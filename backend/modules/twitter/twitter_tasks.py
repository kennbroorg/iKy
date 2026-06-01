#!/usr/bin/env python

import asyncio
import contextlib
import json
import os
import sys
from collections import Counter
from collections.abc import Coroutine
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import twikit
from celery.utils.log import get_task_logger
from factories.configuration import api_keys_search
from factories.iKy_functions import analize_rrss, location_geo
from factories.task_wrapper import iky_task

logger = get_task_logger(__name__)


# ---------------------------------------------------------------------------
# twikit User monkey-patch — defensive against Twitter API drift
#
# twikit 2.3.x does direct dict[key] accesses on the `legacy` payload that
# Twitter has progressively stopped guaranteeing (e.g. description.urls,
# url.urls, several boolean flags). We wrap __init__ so missing keys default
# to safe values instead of crashing with KeyError.
# ---------------------------------------------------------------------------
def _patch_twikit_user() -> None:
    """Wrap twikit.user.User.__init__ so missing legacy keys default safely.

    Twitter's payload has drifted over time and twikit does direct dict
    access on fields like description.urls that aren't always present.
    Wrapping here is a no-op when the test suite mocks twikit.user.
    """
    user_mod = getattr(twikit, "user", None)
    if user_mod is None or not hasattr(user_mod, "User"):
        return
    user_cls = user_mod.User
    if getattr(user_cls, "_iky_patched", False):
        return
    # Only patch the real twikit User class — not test mocks (MagicMock).
    # The real class lives in the twikit package; mocks live elsewhere.
    module_name = getattr(user_cls, "__module__", "")
    if not module_name.startswith("twikit"):
        return
    original_init = user_cls.__init__

    def resilient_init(self, client, data):
        legacy = data.setdefault("legacy", {})
        entities = legacy.setdefault("entities", {})
        entities.setdefault("description", {}).setdefault("urls", [])
        entities.setdefault("url", {}).setdefault("urls", [])
        legacy.setdefault("location", "")
        legacy.setdefault("description", "")
        legacy.setdefault("pinned_tweet_ids_str", [])
        legacy.setdefault("withheld_in_countries", [])
        for key in (
            "verified",
            "possibly_sensitive",
            "can_dm",
            "can_media_tag",
            "want_retweets",
            "default_profile",
            "default_profile_image",
            "has_custom_timelines",
            "is_translator",
        ):
            legacy.setdefault(key, False)
        for key in (
            "followers_count",
            "fast_followers_count",
            "normal_followers_count",
            "friends_count",
            "favourites_count",
            "listed_count",
            "media_count",
            "statuses_count",
        ):
            legacy.setdefault(key, 0)
        legacy.setdefault("translator_type", "none")
        data.setdefault("is_blue_verified", False)
        original_init(self, client, data)

    user_cls.__init__ = resilient_init
    user_cls._iky_patched = True


_patch_twikit_user()

# ---------------------------------------------------------------------------
# Cookie persistence
# ---------------------------------------------------------------------------
_COOKIE_DIR = Path(os.environ.get("TWITTER_COOKIE_DIR", "/app/cookies"))
_COOKIE_FILE = _COOKIE_DIR / "twitter_cookies.json"


# ---------------------------------------------------------------------------
# Async helpers
# ---------------------------------------------------------------------------

T = Any


def _run_async(coro: Coroutine[Any, Any, T]) -> T:
    """Run an async coroutine from sync Celery context."""
    return asyncio.run(coro)


def _convert_browser_cookies(raw: list[dict] | dict) -> dict[str, str]:
    """Convert browser-exported cookie list to twikit {name: value} dict.

    Browser extensions (Cookie-Editor, EditThisCookie) export cookies as a
    list of objects with 'name'/'value' keys.  twikit's set_cookies / load_cookies
    expects a flat ``{cookie_name: cookie_value}`` mapping.
    """
    if isinstance(raw, dict):
        # Already in twikit format — pass through
        return {str(k): str(v) for k, v in raw.items()}
    if isinstance(raw, list):
        result: dict[str, str] = {}
        for item in raw:
            name = item.get("name") or item.get("Name")
            value = item.get("value") or item.get("Value") or ""
            if name:
                result[str(name)] = str(value)
        return result
    raise ValueError(
        f"Unexpected cookie format: {type(raw).__name__}. "
        "Expected list (browser export) or dict (twikit format)."
    )


async def _authenticate(client: twikit.Client) -> None:
    """Load cookies or fall back to username/password login.

    Auth chain (in order):
    1. Cookie file on disk  → load directly (fastest path, used after first run)
    2. ``twitter_cookies`` API key → browser-exported JSON; convert + save to file
    3. Username/password login  → will likely fail due to Cloudflare; kept as
       last-resort fallback for environments where login still works
    4. All methods exhausted   → raise a clear, actionable error message
    """
    _COOKIE_DIR.mkdir(parents=True, exist_ok=True)

    # --- 1. Cookie file already on disk ---
    if _COOKIE_FILE.exists():
        try:
            client.load_cookies(str(_COOKIE_FILE))
            return
        except Exception:
            logger.warning(
                "iKy - Twitter cookies expired or invalid. "
                "Re-export fresh cookies from x.com. See docs/COOKIES.md"
            )
            _COOKIE_FILE.unlink(missing_ok=True)

    # --- 2. Browser-exported cookies from API key ---
    raw_cookie_str = api_keys_search("twitter_cookies")
    if raw_cookie_str:
        try:
            browser_cookies = json.loads(raw_cookie_str)
            twikit_cookies = _convert_browser_cookies(browser_cookies)
            client.set_cookies(twikit_cookies)
            # Persist so subsequent calls use path 1 (faster, no re-parse)
            client.save_cookies(str(_COOKIE_FILE))
            logger.info("Twitter authenticated via browser cookies from API key")
            return
        except (json.JSONDecodeError, ValueError) as exc:
            logger.warning(
                f"Twitter: invalid cookie JSON in twitter_cookies key: {exc}"
            )
        except Exception as exc:
            logger.warning(f"Twitter: failed to load browser cookies: {exc}")

    # --- 3. Nothing worked ---
    raise Exception(
        "iKy - Twitter requires browser cookies. Export cookies from x.com "
        "using Cookie-Editor extension and paste the JSON in the twitter_cookies "
        "API key field. See docs/COOKIES.md for instructions."
    )


async def _get_client() -> twikit.Client:
    """Create and authenticate a twikit Client."""
    client = twikit.Client(language="en-US")
    await _authenticate(client)
    return client


async def _fetch_user(client: twikit.Client, username: str) -> twikit.user.User:
    """Fetch a user profile by screen name."""
    try:
        return await client.get_user_by_screen_name(username)
    except twikit.errors.UserNotFound:
        raise Exception("iKy - User not found") from None
    except twikit.errors.UserUnavailable:
        raise Exception("iKy - User not found") from None
    except Exception as exc:
        # Re-login once if cookies are stale
        if "auth" in str(exc).lower() or "cookie" in str(exc).lower():
            _COOKIE_FILE.unlink(missing_ok=True)
            await _authenticate(client)
            try:
                return await client.get_user_by_screen_name(username)
            except twikit.errors.UserNotFound:
                raise Exception("iKy - User not found") from None
        raise Exception(f"iKy - API Error: {exc}") from exc


async def _fetch_tweets(
    client: twikit.Client, user: twikit.user.User
) -> list[twikit.tweet.Tweet]:
    """Fetch up to ~40 tweets for a user (non-retweet)."""
    try:
        results = await user.get_tweets("Tweets", count=40)
        return list(results)
    except Exception as exc:
        logger.warning(f"Tweet fetch error: {exc}")
        return []


async def _fetch_enrichment(
    client: twikit.Client, user: twikit.user.User, tweets: list[twikit.tweet.Tweet]
) -> dict[str, Any]:
    """Best-effort enrichment — never raises, returns partial data."""
    enrichment: dict[str, Any] = {
        "followers_sample": [],
        "following_sample": [],
        "retweeters_sample": [],
        "likers_sample": [],
        "banner_url": None,
        "pinned_tweet": None,
        "engagement": {
            "avg_likes": 0.0,
            "avg_retweets": 0.0,
            "avg_replies": 0.0,
            "avg_views": 0.0,
            "engagement_rate": 0.0,
        },
        "account_age_days": 0,
        "avg_tweets_per_day": 0.0,
        "follower_following_ratio": 0.0,
        "languages": [],
    }

    # Banner URL
    with contextlib.suppress(Exception):
        enrichment["banner_url"] = getattr(user, "profile_banner_url", None)

    # Pinned tweet — best-effort: fetch actual tweet text by id
    try:
        pinned_ids = getattr(user, "pinned_tweet_ids", None)
        if pinned_ids:
            pinned_id = str(pinned_ids[0])
            pinned_text = ""
            try:
                pinned_tweet_obj = await client.get_tweet_by_id(pinned_id)
                pinned_text = getattr(pinned_tweet_obj, "text", "") or ""
            except Exception:
                pass
            enrichment["pinned_tweet"] = {
                "id": pinned_id,
                "text": pinned_text,
            }
    except Exception:
        pass

    # Followers sample
    try:
        followers = await user.get_followers(count=20)
        enrichment["followers_sample"] = [
            {
                "username": getattr(f, "screen_name", ""),
                "name": getattr(f, "name", ""),
                "followers_count": getattr(f, "followers_count", 0),
            }
            for f in followers
        ]
    except Exception as exc:
        logger.warning(f"Followers fetch error: {exc}")

    # Following sample
    try:
        following = await user.get_following(count=20)
        enrichment["following_sample"] = [
            {
                "username": getattr(f, "screen_name", ""),
                "name": getattr(f, "name", ""),
                "followers_count": getattr(f, "followers_count", 0),
            }
            for f in following
        ]
    except Exception as exc:
        logger.warning(f"Following fetch error: {exc}")

    # Retweeters and likers for latest 3 tweets
    retweeters: list[dict[str, str]] = []
    likers: list[dict[str, str]] = []
    for tweet in tweets[:3]:
        try:
            rts = await tweet.get_retweeters(count=10)
            retweeters.extend(
                {
                    "username": getattr(u, "screen_name", ""),
                    "name": getattr(u, "name", ""),
                }
                for u in rts
            )
        except Exception:
            pass
        try:
            lks = await tweet.get_favoriters(count=10)
            likers.extend(
                {
                    "username": getattr(u, "screen_name", ""),
                    "name": getattr(u, "name", ""),
                }
                for u in lks
            )
        except Exception:
            pass
    enrichment["retweeters_sample"] = retweeters
    enrichment["likers_sample"] = likers

    # Engagement metrics from tweet list
    non_rt_tweets = [t for t in tweets if t.retweeted_tweet is None]
    if non_rt_tweets:
        avg_likes = sum(
            getattr(t, "favorite_count", 0) or 0 for t in non_rt_tweets
        ) / len(non_rt_tweets)
        avg_rts = sum(getattr(t, "retweet_count", 0) or 0 for t in non_rt_tweets) / len(
            non_rt_tweets
        )
        avg_rps = sum(getattr(t, "reply_count", 0) or 0 for t in non_rt_tweets) / len(
            non_rt_tweets
        )
        avg_vw = sum(
            int(getattr(t, "view_count", 0) or 0) for t in non_rt_tweets
        ) / len(non_rt_tweets)
        followers_count = getattr(user, "followers_count", 1) or 1
        eng_rate = (avg_likes + avg_rts + avg_rps) / followers_count * 100
        enrichment["engagement"] = {
            "avg_likes": round(avg_likes, 2),
            "avg_retweets": round(avg_rts, 2),
            "avg_replies": round(avg_rps, 2),
            "avg_views": round(avg_vw, 2),
            "engagement_rate": round(eng_rate, 4),
        }

    # Account age
    try:
        created_raw = getattr(user, "created_at", None)
        if created_raw:
            if isinstance(created_raw, str):
                created_dt = datetime.strptime(created_raw, "%a %b %d %H:%M:%S %z %Y")
            else:
                created_dt = created_raw
            now = datetime.now(tz=UTC)
            age_days = (now - created_dt).days
            enrichment["account_age_days"] = age_days
            tweets_count = getattr(user, "statuses_count", 0) or 0
            enrichment["avg_tweets_per_day"] = (
                round(tweets_count / age_days, 2) if age_days > 0 else 0.0
            )
    except Exception as exc:
        logger.warning(f"Account age calc error: {exc}")

    # Follower/following ratio
    try:
        followers_cnt = getattr(user, "followers_count", 0) or 0
        following_cnt = getattr(user, "following_count", 0) or 1
        enrichment["follower_following_ratio"] = round(
            followers_cnt / (following_cnt or 1), 2
        )
    except Exception:
        pass

    # Language distribution from tweets
    try:
        lang_counter = Counter(
            getattr(t, "lang", "und")
            for t in non_rt_tweets
            if t.retweeted_tweet is None
        )
        enrichment["languages"] = [
            {"name": lang, "value": count} for lang, count in lang_counter.most_common()
        ]
    except Exception:
        pass

    return enrichment


# ---------------------------------------------------------------------------
# Async pipeline — single event loop for all fetches
# ---------------------------------------------------------------------------


async def _run_pipeline(
    username: str,
) -> tuple[twikit.user.User, list, dict[str, Any]]:
    """Run all async Twitter fetches in a SINGLE event loop.

    Critical: twikit's httpx.AsyncClient transport binds to the event loop
    on first use.  Separate ``asyncio.run()`` calls would close the loop
    between calls, killing the transport.  Everything must run in one loop.
    """
    client = await _get_client()
    user = await _fetch_user(client, username)
    tweets = await _fetch_tweets(client, user)
    enrichment = await _fetch_enrichment(client, user, tweets)
    return user, tweets, enrichment


# ---------------------------------------------------------------------------
# Main processing function
# ---------------------------------------------------------------------------


@iky_task(module_name="twitter", dev_mode_sleep=15)
def p_twitter(username: str) -> list[dict[str, Any]]:
    """Task of Celery that gets info from Twitter/X via twikit."""

    # --- Authenticate and fetch (single event loop) ---
    user, all_tweets, enrichment = _run_async(_run_pipeline(username))

    # --- Parse user info ---
    # Normalise created_at to a datetime object for later use
    created_raw = getattr(user, "created_at", None)
    created_at: datetime | None = None
    if created_raw:
        try:
            if isinstance(created_raw, str):
                created_at = datetime.strptime(created_raw, "%a %b %d %H:%M:%S %z %Y")
            else:
                created_at = created_raw
        except Exception:
            pass

    # Build URL list from entities
    url_list: list[str] = []
    try:
        entities = getattr(user, "entities", None) or {}
        url_section = entities.get("url", {}) or {}
        for url_obj in url_section.get("urls", []):
            expanded = url_obj.get("expanded_url")
            if expanded:
                url_list.append(expanded)
        desc_section = entities.get("description", {}) or {}
        for url_obj in desc_section.get("urls", []):
            expanded = url_obj.get("expanded_url")
            if expanded:
                url_list.append(expanded)
    except Exception:
        pass

    user_info: dict[str, Any] = {
        "username": username,
        "name": getattr(user, "name", ""),
        "photo": getattr(user, "profile_image_url", ""),
        "location": getattr(user, "location", "") or "",
        "verified": getattr(user, "verified", False)
        or getattr(user, "is_blue_verified", False),
        "id": str(getattr(user, "id", "")),
        "protected": getattr(user, "protected", False),
        "tweets": getattr(user, "statuses_count", 0),
        "sensitive": getattr(user, "possibly_sensitive", False),
        "followers": getattr(user, "followers_count", 0),
        "following": getattr(user, "following_count", 0),
        "listed": getattr(user, "listed_count", 0),
        "statuses": getattr(user, "statuses_count", 0),
        "likes": getattr(user, "favourites_count", 0),
        "media": getattr(user, "media_count", 0),
        "url": url_list,
        "description": getattr(user, "description", "") or "",
        "created_at": created_at,
        "banner_url": enrichment.get("banner_url"),
    }

    # --- Process tweets ---
    tweet_count = 0
    retweet_count = 0
    tweets_info: list[dict[str, Any]] = []

    lk_rt_rp: list[dict[str, Any]] = []
    mention_temp: list[str] = []
    hashtag_temp: list[str] = []
    sources_temp: list[str] = []
    s_lk: list[dict[str, str]] = []
    s_rt: list[dict[str, str]] = []
    s_rp: list[dict[str, str]] = []
    s_bk: list[dict[str, str]] = []
    s_qt: list[dict[str, str]] = []
    s_vw: list[dict[str, str]] = []
    hours: list[str] = []
    days: list[str] = []
    t_timeline: list[dict[str, Any]] = []
    last_created_at: datetime | None = None

    for tweet in all_tweets:
        try:
            is_retweet = tweet.retweeted_tweet is not None
            if is_retweet:
                retweet_count += 1
                continue

            tweet_count += 1
            idx = tweet_count

            # Optional fields — safe access
            try:
                quoted = "True" if tweet.is_quote_tweet else "False"
            except Exception:
                quoted = "undefined"
            try:
                reply = "True" if tweet.in_reply_to_user_id else "False"
            except Exception:
                reply = "undefined"
            try:
                pos_sen = "True" if tweet.possibly_sensitive else "False"
            except Exception:
                pos_sen = "undefined"

            views_raw = getattr(tweet, "view_count", 0)
            views = 0
            try:
                views = (
                    int(views_raw) if views_raw not in (None, "Unavailable", "") else 0
                )
            except (ValueError, TypeError):
                views = 0

            # Hashtags — twikit returns list of strings
            raw_hashtags = getattr(tweet, "hashtags", []) or []
            hashtag_list: list[str] = []
            for h in raw_hashtags:
                if isinstance(h, str):
                    hashtag_list.append(h)
                elif isinstance(h, dict):
                    hashtag_list.append(h.get("text", ""))

            # Mentions
            raw_mentions = getattr(tweet, "user_mentions", []) or []
            mention_list: list[str] = []
            for m in raw_mentions:
                if isinstance(m, str):
                    mention_list.append(m)
                elif hasattr(m, "screen_name"):
                    mention_list.append(m.screen_name or "")
                elif isinstance(m, dict):
                    mention_list.append(m.get("screen_name", ""))

            # Source
            source_raw = getattr(tweet, "source", "") or ""
            source = source_raw.replace("Twitter", "").replace("for", "").strip()

            # created_at — twikit may return string or datetime
            tweet_created_raw = getattr(tweet, "created_at", None)
            tweet_created: datetime | None = None
            if tweet_created_raw:
                try:
                    if isinstance(tweet_created_raw, str):
                        tweet_created = datetime.strptime(
                            tweet_created_raw, "%a %b %d %H:%M:%S %z %Y"
                        )
                    else:
                        tweet_created = tweet_created_raw
                except Exception:
                    pass

            # Formatted dates
            tweet_date = (
                tweet_created.strftime("%Y-%m-%dT%H:%M:%S.009Z")
                if tweet_created
                else ""
            )
            tweet_day = tweet_created.strftime("%Y-%m-%d") if tweet_created else ""

            tweet_item: dict[str, Any] = {
                "likes": getattr(tweet, "favorite_count", 0) or 0,
                "retweets": getattr(tweet, "retweet_count", 0) or 0,
                "bookmark": getattr(tweet, "bookmark_count", 0) or 0,
                "quotes": getattr(tweet, "quote_count", 0) or 0,
                "replies": getattr(tweet, "reply_count", 0) or 0,
                "views": views,
                "number": idx,
                "quoted": quoted,
                "reply": reply,
                "user_mentions": mention_list,
                "hashtags": hashtag_list,
                "symbols": getattr(tweet, "symbols", []) or [],
                "created_at": tweet_date,
                "source": source,
                "possibly_sensitive": pos_sen,
                "lang": getattr(tweet, "lang", "und") or "und",
                "text": getattr(tweet, "text", "") or "",
            }

            tweets_info.append(tweet_item)
            last_created_at = tweet_created

            # Stats series
            s_lk.append({"name": str(idx), "value": str(tweet_item["likes"])})
            s_rt.append({"name": str(idx), "value": str(tweet_item["retweets"])})
            s_rp.append({"name": str(idx), "value": str(tweet_item["replies"])})
            s_bk.append({"name": str(idx), "value": str(tweet_item["bookmark"])})
            s_qt.append({"name": str(idx), "value": str(tweet_item["quotes"])})
            s_vw.append({"name": str(idx), "value": str(tweet_item["views"])})

            for m in mention_list:
                mention_temp.append(m)
            for h in hashtag_list:
                hashtag_temp.append(h)
            if tweet_day:
                t_timeline.append({"name": tweet_day, "value": 1})
            if source:
                sources_temp.append(source)
            if tweet_created:
                hours.append(tweet_created.strftime("%H"))
                days.append(tweet_created.strftime("%A"))

        except Exception:
            continue

    # --- Timeline ---
    tweet_time: list[dict[str, Any]] = []
    if t_timeline:
        start_date = datetime.strptime(t_timeline[-1]["name"], "%Y-%m-%d")
        end_date = datetime.strptime(t_timeline[0]["name"], "%Y-%m-%d")
        delta_days = (end_date - start_date).days
        for i in range(delta_days + 1):
            current_date = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
            record_count = sum(1 for item in t_timeline if item["name"] == current_date)
            tweet_time.append({"name": current_date, "value": record_count})

    # --- Tweet vs Retweet ---
    tw_vs_rt = [
        {"name": "Tweet", "value": tweet_count},
        {"name": "Retweet", "value": retweet_count},
    ]

    # --- Likes / RTs / Replies chart ---
    lk_rt_rp = [
        {"name": "Likes", "series": s_lk},
        {"name": "Retweets", "series": s_rt},
        {"name": "Replies", "series": s_rp},
        {"name": "Bookmarks", "series": s_bk},
        {"name": "Quotes", "series": s_qt},
        {"name": "Views", "series": s_vw},
    ]

    # --- Mentions ---
    mention_counter = Counter(mention_temp)
    link_users = "Users"
    users: list[dict[str, Any]] = [
        {"name-node": "Users", "title": "Users", "subtitle": "", "link": link_users}
    ]
    for k, v in mention_counter.items():
        users.append({"name-node": k, "title": k, "subtitle": v, "link": link_users})

    # --- Hashtags ---
    hashtags = [{"label": k, "value": v} for k, v in Counter(hashtag_temp).items()]

    # --- Sources ---
    sources = [{"name": k, "value": v} for k, v in Counter(sources_temp).items()]

    # --- Hour chart ---
    hournames = "00 01 02 03 04 05 06 07 08 09 10 11 12 13 14 15 16 17 18 19 20 21 22 23".split()
    tw_counter = Counter(hours)
    tg_data = sorted(tw_counter.most_common())
    hourset: list[dict[str, Any]] = []
    e = 0
    for g in hournames:
        if (e >= len(tg_data)) or (g < tg_data[e][0]):
            hourset.append({"name": g, "value": 0})
        elif g == tg_data[e][0]:
            hourset.append({"name": g, "value": int(tg_data[e][1])})
            e += 1

    # --- Week chart ---
    weekdays = "Monday Tuesday Wednesday Thursday Friday Saturday Sunday".split()
    wd_counter = Counter(days)
    wd_data = sorted(wd_counter.most_common())
    weekset: list[dict[str, Any]] = []
    for c, z in enumerate(weekdays):
        try:
            weekset.append({"name": z, "value": int(wd_data[c][1])})
        except (IndexError, TypeError):
            weekset.append({"name": z, "value": 0})

    # --- Output assembly ---
    total: list[dict[str, Any]] = []
    graphic: list[dict[str, Any]] = []
    gather: list[dict[str, Any]] = []
    resume: dict[str, Any] = {}
    popularity: list[dict[str, Any]] = []
    approval: list[dict[str, Any]] = []
    profile: list[dict[str, Any]] = []
    social: list[dict[str, Any]] = []
    timeline: list[dict[str, Any]] = []
    tasks: list[dict[str, Any]] = []
    presence: list[dict[str, Any]] = []

    # Raw nodes — CRITICAL: preserve exact key names for tweetiment compat
    raw_node_total: list[dict[str, Any]] = [
        {"raw_node_info": user_info},
        {
            "raw_node_tweets": tweets_info
        },  # tweetiment reads result[3]["raw"][1]["raw_node_tweets"]
        {"raw_node_enrichment": enrichment},
    ]

    # Header
    total.append({"module": "twitter"})
    total.append({"param": username})
    total.append({"validation": "hard"})

    # Gather items
    link_social = "Twitter"
    gather.append(
        {
            "name-node": "Twitter",
            "title": "Twitter",
            "subtitle": "",
            "icon": "fab fa-twitter",
            "link": link_social,
        }
    )
    gather.append(
        {
            "name-node": "TwitterName",
            "title": "Name",
            "subtitle": user_info["name"],
            "icon": "fas fa-signature",
            "link": link_social,
        }
    )
    profile.append({"name": user_info["name"]})

    gather.append(
        {
            "name-node": "TwitterUserName",
            "title": "Username",
            "subtitle": username,
            "icon": "fas fa-user-circle",
            "link": link_social,
        }
    )
    profile.append({"username": username})

    gather.append(
        {
            "name-node": "Twitterphoto",
            "title": "Avatar",
            "subtitle": "",
            "picture": user_info["photo"],
            "link": link_social,
        }
    )
    pic = (user_info["photo"] or "").replace("_normal.", "_400x400.")
    profile.append(
        {
            "photos": [
                {
                    "name-node": "Twitter",
                    "title": "Twitter",
                    "subtitle": "",
                    "picture": pic,
                    "link": "Photos",
                }
            ]
        }
    )

    gather.append(
        {
            "name-node": "TwitterLocation",
            "title": "Location",
            "subtitle": user_info["location"],
            "icon": "fas fa-map-marker-alt",
            "link": link_social,
        }
    )
    if user_info["location"]:
        profile.append({"location": user_info["location"]})
        try:
            create_date_str = created_at.strftime("%Y-%m-%d") if created_at else ""
            geo_item = location_geo(user_info["location"], time=create_date_str)
            if geo_item:
                profile.append({"geo": geo_item})
        except Exception:
            pass

    gather.append(
        {
            "name-node": "TwitterVerified",
            "title": "Verified",
            "subtitle": str(user_info["verified"]),
            "icon": "fas fa-certificate",
            "link": link_social,
        }
    )
    gather.append(
        {
            "name-node": "TwitterID",
            "title": "ID",
            "subtitle": str(user_info["id"]),
            "icon": "fas fa-id-card",
            "link": link_social,
        }
    )
    gather.append(
        {
            "name-node": "TwitterPrivate",
            "title": "Protected",
            "subtitle": str(user_info["protected"]),
            "icon": "fas fa-user-shield",
            "link": link_social,
        }
    )
    gather.append(
        {
            "name-node": "TwitterSensitive",
            "title": "Sensitive",
            "subtitle": str(user_info["sensitive"]),
            "icon": "fas fa-radiation",
            "link": link_social,
        }
    )
    gather.append(
        {
            "name-node": "TwitterTweets",
            "title": "Tweets",
            "subtitle": str(user_info["tweets"]),
            "icon": "fab fa-twitter-square",
            "link": link_social,
        }
    )
    gather.append(
        {
            "name-node": "TwitterMedia",
            "title": "Media",
            "subtitle": str(user_info["media"]),
            "icon": "fas fa-photo-video",
            "link": link_social,
        }
    )
    gather.append(
        {
            "name-node": "TwitterFollowers",
            "title": "Followers",
            "subtitle": str(user_info["followers"]),
            "icon": "fas fa-users",
            "link": link_social,
        }
    )
    gather.append(
        {
            "name-node": "TwitterFollowing",
            "title": "Following",
            "subtitle": str(user_info["following"]),
            "icon": "fas fa-user-friends",
            "link": link_social,
        }
    )
    gather.append(
        {
            "name-node": "TwitterList",
            "title": "Listed",
            "subtitle": str(user_info["listed"]),
            "icon": "far fa-list-alt",
            "link": link_social,
        }
    )
    gather.append(
        {
            "name-node": "TwitterHeart",
            "title": "Likes",
            "subtitle": str(user_info["likes"]),
            "icon": "fas fa-heart",
            "link": link_social,
        }
    )

    # Enrichment gather items — new, backward-compatible additions
    if enrichment.get("banner_url"):
        gather.append(
            {
                "name-node": "TwitterBanner",
                "title": "Banner",
                "subtitle": "",
                "picture": enrichment["banner_url"],
                "link": link_social,
            }
        )

    pinned = enrichment.get("pinned_tweet")
    if pinned and pinned.get("text"):
        gather.append(
            {
                "name-node": "TwitterPinned",
                "title": "Pinned Tweet",
                "subtitle": (pinned["text"] or "")[:80],
                "icon": "fas fa-thumbtack",
                "link": link_social,
            }
        )

    eng = enrichment.get("engagement", {})
    eng_rate = eng.get("engagement_rate", 0.0)
    gather.append(
        {
            "name-node": "TwitterEngagement",
            "title": "Engagement Rate",
            "subtitle": f"{eng_rate:.2%}",
            "icon": "fas fa-chart-line",
            "link": link_social,
        }
    )

    age_days = enrichment.get("account_age_days", 0)
    if age_days:
        gather.append(
            {
                "name-node": "TwitterAge",
                "title": "Account Age",
                "subtitle": f"{age_days} days",
                "icon": "fas fa-calendar-alt",
                "link": link_social,
            }
        )

    ratio = enrichment.get("follower_following_ratio", 0.0)
    gather.append(
        {
            "name-node": "TwitterRatio",
            "title": "F/F Ratio",
            "subtitle": f"{ratio:.1f}",
            "icon": "fas fa-balance-scale",
            "link": link_social,
        }
    )

    # URL / description analysis
    for url in user_info["url"]:
        analyze = analize_rrss(url)
        for item in analyze:
            if item == "url":
                for i in analyze["url"]:
                    profile.append(i)
            if item == "tasks":
                for i in analyze["tasks"]:
                    tasks.append(i)

    if user_info["description"]:
        profile.append({"bio": user_info["description"]})
        analyze = analize_rrss(user_info["description"])
        for item in analyze:
            if item == "url":
                for i in analyze["url"]:
                    profile.append(i)
            if item == "tasks":
                for i in analyze["tasks"]:
                    tasks.append(i)

    social_item = {
        "name": "Twitter",
        "url": f"https://twitter.com/{username}",
        "icon": "fab fa-twitter",
        "source": "Twitter",
        "username": username,
    }
    social.append(social_item)
    profile.append({"social": social})

    # Resume (sunburst)
    children = [
        {"name": "Likes", "total": user_info["likes"]},
        {"name": "Tweets", "total": user_info["tweets"]},
        {"name": "Followers", "total": user_info["followers"]},
        {"name": "Following", "total": user_info["following"]},
        {"name": "Listed", "total": user_info["listed"]},
    ]
    resume = {"name": "twitter", "children": children}

    popularity = [
        {"title": "Followers", "value": user_info["followers"]},
        {"title": "Listed", "value": user_info["listed"]},
        {"title": "Following", "value": user_info["following"]},
    ]
    approval = [
        {"title": "Tweets", "value": user_info["tweets"]},
        {"title": "Likes", "value": user_info["likes"]},
    ]

    # Timeline events
    if created_at:
        user_create_str = created_at.strftime("%Y/%m/%d %H:%M:%S")
        timeline.append(
            {
                "date": user_create_str,
                "action": "Twitter : Create Account",
                "icon": "fa-twitter",
            }
        )
        user_info["created_at"] = user_create_str
    if last_created_at:
        timeline.append(
            {
                "date": last_created_at.strftime("%Y-%m-%d"),
                "action": "Twitter : Last Tweet",
                "icon": "fa-twitter",
            }
        )

    presence.append(
        {
            "name": "twitter",
            "children": [
                {"name": "followers", "value": user_info["followers"]},
                {"name": "following", "value": user_info["following"]},
            ],
        }
    )
    profile.append({"presence": presence})

    # Language distribution chart (new)
    lang_dist: list[dict[str, Any]] = enrichment.get("languages", [])

    # Engagement chart (new)
    engagement_chart: list[dict[str, Any]] = [
        {"name": "Avg Likes", "value": eng.get("avg_likes", 0)},
        {"name": "Avg Retweets", "value": eng.get("avg_retweets", 0)},
        {"name": "Avg Replies", "value": eng.get("avg_replies", 0)},
        {"name": "Avg Views", "value": eng.get("avg_views", 0)},
        {"name": "Engagement Rate %", "value": round(eng_rate, 4)},
    ]

    # Assemble final output
    total.append({"raw": raw_node_total})
    graphic.append({"social": gather})
    graphic.append({"resume": resume})
    graphic.append({"popularity": popularity})
    graphic.append({"approval": approval})
    graphic.append({"hashtag": hashtags})
    graphic.append({"users": users})
    graphic.append({"tweetslist": lk_rt_rp})
    graphic.append({"week": weekset})
    graphic.append({"hour": hourset})
    graphic.append({"sources": sources})
    graphic.append({"time": tweet_time})
    graphic.append({"twvsrt": tw_vs_rt})
    graphic.append({"languages": lang_dist})  # NEW
    graphic.append({"engagement": engagement_chart})  # NEW
    total.append({"graphic": graphic})
    total.append({"profile": profile})
    total.append({"timeline": timeline})
    total.append({"tasks": tasks})

    return total


# Backward-compatible alias — module_registry.py references t_twitter
t_twitter = p_twitter


def output(data: list[dict[str, Any]]) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    username = sys.argv[1]
    result = t_twitter(username)
    output(result)
