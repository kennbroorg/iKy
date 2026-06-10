#!/usr/bin/env python
"""Reddit OSINT module — migrated to @iky_task decorator.

Fetches public user data from Reddit's unauthenticated JSON endpoints:
  - /user/{u}/about.json        (profile, karma, subreddit metadata)
  - /user/{u}/submitted.json    (post history, paginated)
  - /user/{u}/comments.json     (comment history, paginated)
  - /api/v1/user/{u}/trophies.json (trophies/badges)
"""

import random
import time
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import quote

import requests
from celery.utils.log import get_task_logger
from factories.task_wrapper import iky_task

logger = get_task_logger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_USER_AGENTS: tuple[str, ...] = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.4.1 Mobile/15E148 Safari/604.1",
)

_BASE_URL = "https://www.reddit.com"

# Load location set once per module import (frozenset for O(1) lookup).
_LOCATION_FILE = Path(__file__).resolve().parent / "all-locations.txt"
_LOCATIONS: frozenset[str] = frozenset(
    line.strip().lower()
    for line in _LOCATION_FILE.read_text(encoding="utf-8").splitlines()
    if line.strip()
)

# ---------------------------------------------------------------------------
# Private HTTP helpers
# ---------------------------------------------------------------------------


def _make_session() -> requests.Session:
    """Return a Session with a random modern User-Agent header."""
    session = requests.Session()
    session.headers["User-Agent"] = random.choice(_USER_AGENTS)
    return session


def _fetch_about(session: requests.Session, username: str) -> dict:
    """Fetch /user/{username}/about.json and return the ``data`` sub-dict.

    Raises ``Exception("iKy - ...")`` on 403/404/429/suspended.
    """
    safe = quote(username, safe="")
    url = f"{_BASE_URL}/user/{safe}/about.json"
    resp = session.get(url, timeout=30)

    match resp.status_code:
        case 404:
            raise Exception("iKy - User not found")
        case 403:
            raise Exception("iKy - Access forbidden (suspended/private)")
        case 429:
            raise Exception("iKy - Rate limited by Reddit")
        case 200:
            pass
        case _:
            raise Exception(f"iKy - Unexpected HTTP {resp.status_code} from about.json")

    data = resp.json().get("data", {})
    if data.get("is_suspended"):
        raise Exception("iKy - User is suspended")

    return data


def _fetch_paginated(
    session: requests.Session,
    username: str,
    endpoint: str,
    max_pages: int = 3,
) -> list[dict]:
    """Fetch up to *max_pages* pages from a user listing endpoint.

    Uses ``after`` cursor for pagination. Sleeps 0.5 s between pages
    2+ as a polite rate-limit defence.
    """
    safe = quote(username, safe="")
    url = f"{_BASE_URL}/user/{safe}/{endpoint}.json"
    items: list[dict] = []
    after: str | None = None

    for page in range(max_pages):
        # Rotate UA on each request
        session.headers["User-Agent"] = random.choice(_USER_AGENTS)

        params: dict[str, str | int] = {"limit": 100, "raw_json": 1}
        if after:
            params["after"] = after

        resp = session.get(url, params=params, timeout=30)
        if resp.status_code != 200:
            if page == 0:
                # Raise on the first page so the caller can surface the error
                match resp.status_code:
                    case 403:
                        raise Exception("iKy - User profile is private or forbidden")
                    case 404:
                        raise Exception("iKy - User not found")
                    case 429:
                        raise Exception("iKy - Rate limited by Reddit")
                    case _:
                        logger.warning(
                            "Reddit %s page 1 returned HTTP %s — stopping",
                            endpoint,
                            resp.status_code,
                        )
            else:
                # Subsequent pages: stop silently with what we have so far
                logger.warning(
                    "Reddit %s page %d returned HTTP %s — stopping pagination",
                    endpoint,
                    page + 1,
                    resp.status_code,
                )
            break

        data = resp.json().get("data", {})
        children = data.get("children", [])
        items.extend(child["data"] for child in children if "data" in child)

        after = data.get("after")
        if not after:
            break

        if page < max_pages - 1:
            time.sleep(0.5)

    return items


def _fetch_posts(
    session: requests.Session, username: str, max_pages: int = 3
) -> list[dict]:
    return _fetch_paginated(session, username, "submitted", max_pages)


def _fetch_comments(
    session: requests.Session, username: str, max_pages: int = 3
) -> list[dict]:
    return _fetch_paginated(session, username, "comments", max_pages)


def _fetch_trophies(session: requests.Session, username: str) -> list[dict]:
    """Fetch trophies; returns ``[]`` on any failure (non-fatal)."""
    try:
        safe = quote(username, safe="")
        url = f"{_BASE_URL}/api/v1/user/{safe}/trophies.json"
        session.headers["User-Agent"] = random.choice(_USER_AGENTS)
        resp = session.get(url, timeout=30)
        if resp.status_code != 200:
            return []
        trophy_data = resp.json().get("data", {}).get("trophies", [])
        return [t.get("data", t) for t in trophy_data]
    except Exception:
        logger.warning("Reddit trophies fetch failed — ignoring")
        return []


# ---------------------------------------------------------------------------
# Private processing helpers
# ---------------------------------------------------------------------------

_HOUR_NAMES: tuple[str, ...] = tuple(f"{h:02d}:00" for h in range(24))
_WEEKDAY_NAMES: tuple[str, ...] = (
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
)


def _build_hour_chart(timestamps: list[float]) -> list[dict]:
    """Return 24-entry hour activity list from UTC timestamps."""
    if not timestamps:
        return []

    counts = Counter(datetime.fromtimestamp(ts, tz=UTC).hour for ts in timestamps)
    return [
        {"name": name, "value": counts.get(h, 0)} for h, name in enumerate(_HOUR_NAMES)
    ]


def _build_week_chart(timestamps: list[float]) -> list[dict]:
    """Return 7-entry weekday activity list from UTC timestamps."""
    if not timestamps:
        return []

    counts = Counter(datetime.fromtimestamp(ts, tz=UTC).weekday() for ts in timestamps)
    return [
        {"name": name, "value": counts.get(wd, 0)}
        for wd, name in enumerate(_WEEKDAY_NAMES)
    ]


_STOPWORDS: frozenset[str] = frozenset(
    {
        "a",
        "an",
        "the",
        "and",
        "or",
        "but",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "with",
        "by",
        "from",
        "up",
        "about",
        "into",
        "through",
        "is",
        "it",
        "its",
        "be",
        "been",
        "being",
        "was",
        "were",
        "are",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "could",
        "should",
        "may",
        "might",
        "shall",
        "can",
        "not",
        "no",
        "i",
        "my",
        "me",
        "we",
        "our",
        "you",
        "your",
        "he",
        "she",
        "they",
        "them",
        "their",
        "this",
        "that",
        "these",
        "those",
        "what",
        "which",
        "who",
        "how",
        "when",
        "where",
        "why",
        "so",
        "if",
        "as",
        "than",
        "then",
        "just",
        "also",
        "any",
        "all",
        "more",
        "most",
        "some",
        "such",
        "s",
        "t",
        "re",
        "ve",
        "ll",
        "d",
        "m",
    }
)


def _build_topics(posts: list[dict], comments: list[dict]) -> dict:
    """Return bubble-chart dict from subreddit participation + post titles.

    Subreddit names are counted as topics, and post titles are tokenised into
    words (lowercased, stopwords filtered) and added to the frequency counter.

    Returns ``{}`` if no posts/comments.
    """
    items = posts + comments
    if not items:
        return {}

    sub_list = [item["subreddit"].lower() for item in items if item.get("subreddit")]
    if not sub_list:
        return {}

    counter = Counter(sub_list)

    # Add title words from posts
    for post in posts:
        title = post.get("title", "") or ""
        words = [w.strip(".,!?;:\"'()[]") for w in title.lower().split()]
        counter.update(w for w in words if w and w not in _STOPWORDS and len(w) > 1)

    children = [
        {"name": name, "count": cnt, "value": cnt}
        for name, cnt in counter.most_common()
    ]
    return {"name": "", "value": 100, "children": children}


def _build_location(posts: list[dict], comments: list[dict]) -> set[str]:
    """Return set of location names inferred from subreddit participation.

    Returns empty set if no posts/comments.
    """
    items = posts + comments
    if not items:
        return set()

    sub_set = {item["subreddit"].lower() for item in items if item.get("subreddit")}
    return sub_set.intersection(_LOCATIONS)


# ---------------------------------------------------------------------------
# Main task
# ---------------------------------------------------------------------------


@iky_task(module_name="reddit", dev_mode_sleep=15)
def p_reddit(username: str) -> list[dict]:
    """Fetch and assemble Reddit OSINT data for *username*.

    Returns a 7-element list:
        [module, param, validation, raw, graphic, profile, timeline]
    """
    session = _make_session()

    # ---- Data retrieval ------------------------------------------------
    about = _fetch_about(session, username)
    posts = _fetch_posts(session, username)
    comments = _fetch_comments(session, username)
    trophies = _fetch_trophies(session, username)

    # ---- Processing ----------------------------------------------------
    all_items = posts + comments
    timestamps = [item["created_utc"] for item in all_items if item.get("created_utc")]

    hour_chart = _build_hour_chart(timestamps)
    week_chart = _build_week_chart(timestamps)
    topics_bubble = _build_topics(posts, comments)
    location_set = _build_location(posts, comments)

    # Last activity timestamp
    lastaction: float = max(timestamps, default=0)

    # ---- Gather (social) nodes -----------------------------------------
    gather: list[dict] = []
    link_social = "Reddit"

    gather.append(
        {
            "name-node": "Reddit",
            "title": "Reddit",
            "subtitle": "",
            "icon": "fab fa-reddit-alien",
            "link": link_social,
        }
    )

    if about.get("name"):
        gather.append(
            {
                "name-node": "RedditName",
                "title": "Name",
                "subtitle": about["name"],
                "icon": "fas fa-user-circle",
                "link": link_social,
            }
        )

    if about.get("icon_img"):
        gather.append(
            {
                "name-node": "Redditphoto",
                "title": "Reddit",
                "subtitle": "",
                "picture": about["icon_img"],
                "link": link_social,
            }
        )

    if about.get("comment_karma") is not None:
        gather.append(
            {
                "name-node": "RedditCommentKarma",
                "title": "Comment Karma",
                "subtitle": about["comment_karma"],
                "icon": "fas fa-comments",
                "link": link_social,
            }
        )

    if about.get("link_karma") is not None:
        gather.append(
            {
                "name-node": "RedditLinkKarma",
                "title": "Link Karma",
                "subtitle": about["link_karma"],
                "icon": "fas fa-link",
                "link": link_social,
            }
        )

    if about.get("total_karma") is not None:
        gather.append(
            {
                "name-node": "RedditTotalKarma",
                "title": "Total Karma",
                "subtitle": about["total_karma"],
                "icon": "fas fa-star",
                "link": link_social,
            }
        )

    if about.get("awardee_karma") is not None:
        gather.append(
            {
                "name-node": "RedditAwardeeKarma",
                "title": "Awardee Karma",
                "subtitle": about["awardee_karma"],
                "icon": "fas fa-award",
                "link": link_social,
            }
        )

    if about.get("awarder_karma") is not None:
        gather.append(
            {
                "name-node": "RedditAwarderKarma",
                "title": "Awarder Karma",
                "subtitle": about["awarder_karma"],
                "icon": "fas fa-gift",
                "link": link_social,
            }
        )

    if about.get("has_verified_email") is not None:
        gather.append(
            {
                "name-node": "RedditEmail",
                "title": "Verified Email",
                "subtitle": about["has_verified_email"],
                "icon": "fas fa-at",
                "link": link_social,
            }
        )

    if about.get("is_mod"):
        gather.append(
            {
                "name-node": "RedditMod",
                "title": "Moderator",
                "subtitle": about["is_mod"],
                "icon": "fas fa-shield-alt",
                "link": link_social,
            }
        )

    is_premium = about.get("is_gold") or about.get("is_premium")
    if is_premium:
        gather.append(
            {
                "name-node": "RedditPremium",
                "title": "Premium",
                "subtitle": True,
                "icon": "fas fa-crown",
                "link": link_social,
            }
        )

    subreddit_meta = about.get("subreddit") or {}
    if isinstance(subreddit_meta, dict):
        bio = subreddit_meta.get("public_description", "")
        if bio:
            gather.append(
                {
                    "name-node": "RedditBio",
                    "title": "Bio",
                    "subtitle": bio,
                    "icon": "fas fa-heartbeat",
                    "link": link_social,
                }
            )

        subscribers = subreddit_meta.get("subscribers")
        if subscribers is not None:
            gather.append(
                {
                    "name-node": "RedditSubscribers",
                    "title": "Subscribers",
                    "subtitle": subscribers,
                    "icon": "fas fa-users",
                    "link": link_social,
                }
            )

        banner_img = subreddit_meta.get("banner_img", "") or ""
        if banner_img:
            gather.append(
                {
                    "name-node": "RedditBanner",
                    "title": "Banner",
                    "subtitle": "",
                    "picture": banner_img,
                    "link": link_social,
                }
            )

    if posts:
        gather.append(
            {
                "name-node": "RedditPosts",
                "title": "Posts",
                "subtitle": len(posts),
                "icon": "fas fa-newspaper",
                "link": link_social,
            }
        )

    if comments:
        gather.append(
            {
                "name-node": "RedditComments",
                "title": "Comments",
                "subtitle": len(comments),
                "icon": "far fa-comments",
                "link": link_social,
            }
        )

    for trophy in trophies:
        name = trophy.get("name", "")
        if name:
            gather.append(
                {
                    "name-node": f"RedditTrophy_{name}",
                    "title": name,
                    "subtitle": "",
                    "icon": "fas fa-trophy",
                    "link": link_social,
                }
            )

    if location_set:
        gather.append(
            {
                "name-node": "RedditLocation",
                "title": "Location",
                "subtitle": str(location_set),
                "icon": "fas fa-map-marker-alt",
                "link": link_social,
            }
        )

    if about.get("created_utc"):
        created_dt = datetime.fromtimestamp(about["created_utc"], tz=UTC).strftime(
            "%Y/%m/%d %H:%M:%S"
        )
        gather.append(
            {
                "name-node": "RedditCreate",
                "title": "Created",
                "subtitle": created_dt,
                "icon": "fas fa-calendar-alt",
                "link": link_social,
            }
        )

    if lastaction:
        last_dt = datetime.fromtimestamp(lastaction, tz=UTC).strftime(
            "%Y/%m/%d %H:%M:%S"
        )
        gather.append(
            {
                "name-node": "RedditLast",
                "title": "Last Activity",
                "subtitle": last_dt,
                "icon": "far fa-calendar-alt",
                "link": link_social,
            }
        )

    # ---- Profile array -------------------------------------------------
    profile: list[dict] = []

    if about.get("name"):
        profile.append({"name": about["name"]})

    if about.get("icon_img"):
        photos = [
            {
                "name-node": "Reddit",
                "title": "Reddit",
                "subtitle": "",
                "picture": about["icon_img"],
                "link": "Photos",
            }
        ]
        _banner = (about.get("subreddit") or {}).get("banner_img", "") or ""
        if _banner:
            photos.append(
                {
                    "name-node": "RedditBanner",
                    "title": "Reddit Banner",
                    "subtitle": "",
                    "picture": _banner,
                    "link": "Photos",
                }
            )
        profile.append({"photos": photos})

    if location_set:
        profile.append({"location": str(location_set)})

    # ---- Timeline array ------------------------------------------------
    timeline: list[dict] = []

    if about.get("created_utc"):
        created_dt = datetime.fromtimestamp(about["created_utc"], tz=UTC).strftime(
            "%Y/%m/%d %H:%M:%S"
        )
        timeline.append(
            {
                "action": "Reddit",
                "date": created_dt,
                "desc": "Reddit creation account date",
            }
        )

    if lastaction:
        last_dt = datetime.fromtimestamp(lastaction, tz=UTC).strftime(
            "%Y/%m/%d %H:%M:%S"
        )
        timeline.append(
            {
                "action": "Reddit",
                "date": last_dt,
                "desc": "Reddit last action",
            }
        )

    # ---- Raw node ------------------------------------------------------
    raw_node = [
        {"profile": about},
        {"comments": comments},
        {"posts": posts},
        {"trophies": trophies},
    ]

    # ---- Assemble 7-element response -----------------------------------
    total = [
        {"module": "reddit"},
        {"param": username},
        {"validation": "no"},
        {"raw": raw_node},
        {
            "graphic": [
                {"social": gather},
                {"hour": hour_chart},
                {"week": week_chart},
                {"topics": topics_bubble},
            ]
        },
        {"profile": profile},
        {"timeline": timeline},
    ]

    return total


# Backward-compatible alias: existing code / module_registry references t_reddit
t_reddit = p_reddit
