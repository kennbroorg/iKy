#!/usr/bin/env python

import argparse
import asyncio
import contextlib
import json
import os
import re
from collections import Counter
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import requests
from celery.utils.log import get_task_logger
from factories.configuration import api_keys_search
from factories.cookie_utils import convert_browser_cookies
from factories.iKy_functions import analize_rrss
from factories.task_wrapper import iky_task
from TikTokApi import TikTokApi

logger = get_task_logger(__name__)

# ---------------------------------------------------------------------------
# Cookie persistence
# ---------------------------------------------------------------------------
_DEFAULT_COOKIE_DIR = Path(__file__).resolve().parents[2] / "cookies"
_COOKIE_DIR = Path(os.environ.get("TIKTOK_COOKIE_DIR", str(_DEFAULT_COOKIE_DIR)))
_COOKIE_FILE = _COOKIE_DIR / "tiktok_cookies.json"


# ---------------------------------------------------------------------------
# Cookie helper
# ---------------------------------------------------------------------------


# Cookie conversion is shared across modules — see factories.cookie_utils.
# Keep the historical private name as an alias so existing call sites and the
# test suite resolve while the logic lives in exactly one place.
_convert_tiktok_cookies = convert_browser_cookies


def get_tiktok_cookies(cookie_keys: list[str]) -> dict[str, Any]:
    """Obtain TikTok cookies through a 2-step auth chain.

    Auth chain:
    1. Cookie file on disk → load directly
    2. tiktok_cookies API key → Cookie-Editor JSON; convert + save
    3. All exhausted → return not found (no in-container browser access)

    Note: the host-side ``install/scripts/grab_cookies.py`` extracts cookies
    from local browsers; the container itself never touches ``browser_cookie3``
    because Docker has no host browser/keyring access. See ``docs/COOKIES.md``.
    """
    _COOKIE_DIR.mkdir(parents=True, exist_ok=True)

    # --- 1. Cookie file already on disk ---
    if _COOKIE_FILE.exists():
        try:
            with _COOKIE_FILE.open() as f:
                saved = json.load(f)
            # Check all required keys present
            if all(saved.get(k) for k in cookie_keys):
                logger.info("TikTok cookies loaded from file")
                return {"found": True, "cookies": saved}
            else:
                logger.warning("TikTok cookie file missing required keys, removing")
                _COOKIE_FILE.unlink(missing_ok=True)
        except Exception:
            logger.warning("TikTok cookie file corrupted, removing")
            _COOKIE_FILE.unlink(missing_ok=True)

    # --- 2. Browser-exported cookies from API key ---
    raw_cookie_str = api_keys_search("tiktok_cookies")
    if raw_cookie_str:
        try:
            browser_cookies = json.loads(raw_cookie_str)
            cookie_dict = convert_browser_cookies(browser_cookies)
            if all(cookie_dict.get(k) for k in cookie_keys):
                # Persist for reuse
                with _COOKIE_FILE.open("w") as f:
                    json.dump(cookie_dict, f)
                logger.info("TikTok authenticated via cookies from API key")
                return {"found": True, "cookies": cookie_dict}
            else:
                logger.warning(
                    "TikTok API key cookies missing required keys: %s",
                    [k for k in cookie_keys if not cookie_dict.get(k)],
                )
        except (json.JSONDecodeError, ValueError) as exc:
            logger.warning("TikTok: invalid cookie JSON in tiktok_cookies key: %s", exc)
        except Exception as exc:
            logger.warning("TikTok: failed to load cookies from API key: %s", exc)

    # --- 3. Nothing worked ---
    # In-container browser extraction is intentionally absent: Docker has no
    # access to host browser profiles or the OS keyring. Provision cookies on
    # the host instead (see docs/COOKIES.md).
    logger.warning(
        "TikTok cookies not found. Provision them on the host: export from "
        "tiktok.com with Cookie-Editor into the tiktok_cookies API key field, "
        "or run `just cookies-import`/`just cookies-grab`. See docs/COOKIES.md."
    )
    return {"found": False, "cookies": {}}


# ---------------------------------------------------------------------------
# HTTP fallback (cookie-free)
# ---------------------------------------------------------------------------

_TIKTOK_WEBAPP_URL = "https://www.tiktok.com/@{username}"
_REHYDRATION_RE = re.compile(
    r'<script[^>]+id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(.*?)</script>',
    re.DOTALL,
)


def http_fallback_profile(username: str) -> dict[str, Any]:
    """Fetch basic profile via TikTok public web-app SSR page.

    Returns a partial ``user_data`` dict.  Raises ``RuntimeError`` on failure.
    """
    url = _TIKTOK_WEBAPP_URL.format(username=username)
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(
            f"iKy - HTTP fallback failed for @{username}: {exc}"
        ) from exc

    match = _REHYDRATION_RE.search(resp.text)
    if not match:
        raise RuntimeError(
            f"iKy - Could not parse TikTok page for @{username}. "
            "TikTok may have changed their SSR structure."
        )

    try:
        rehydration = json.loads(match.group(1))
        # Navigate the nested structure to reach userInfo
        default_scope = rehydration.get("__DEFAULT_SCOPE__", {})
        user_detail = default_scope.get("webapp.user-detail", {})
        user_info = user_detail.get("userInfo", {})
        if not user_info:
            raise KeyError("userInfo not found")
    except (json.JSONDecodeError, KeyError) as exc:
        raise RuntimeError(
            f"iKy - Failed to extract user data from TikTok page for @{username}: {exc}"
        ) from exc

    return {"userInfo": user_info}


# ---------------------------------------------------------------------------
# Async TikTok API bridge
# ---------------------------------------------------------------------------


async def get_user_info(
    ms_token: str, username: str, num: int = 5
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Fetch user info and videos via TikTokApi (async)."""
    async with TikTokApi() as api:
        await api.create_sessions(ms_tokens=[ms_token], num_sessions=1, sleep_after=3)
        try:
            user = api.user(username)
            user_data = await user.info()
        except KeyError as e:
            if e.args[0] == "user":
                raise Exception("iKy - User Not Found") from e
            raise

        user_videos: list[dict[str, Any]] = []
        async for video in user.videos(count=num):
            user_videos.append(video.as_dict)

        return user_data, user_videos


def run_get_user_info(
    ms_token: str, username: str, num: int = 5
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Sync wrapper around ``get_user_info``."""
    return asyncio.run(get_user_info(ms_token, username, num))


# ---------------------------------------------------------------------------
# Enrichment helpers
# ---------------------------------------------------------------------------

_CJK_RE = re.compile(r"[\u4e00-\u9fff\u3040-\u30ff\u3400-\u4dbf]")
_CYRILLIC_RE = re.compile(r"[\u0400-\u04ff]")
_ARABIC_RE = re.compile(r"[\u0600-\u06ff]")
_MENTION_RE = re.compile(r"@(\w+)")

# Human-readable labels for TikTok privacy settings
_PRIVACY_LABELS: dict[int, str] = {0: "All", 1: "Friends Only", 2: "Off"}


def detect_language(captions: list[str]) -> str | None:
    """Regex-heuristic language detection from video captions.

    Returns ISO 639-1 code (``"zh"``, ``"ru"``, ``"ar"``, ``"en"``) or ``None``.
    """
    if not captions:
        return None

    text = " ".join(captions)
    if _CJK_RE.search(text):
        return "zh"
    if _CYRILLIC_RE.search(text):
        return "ru"
    if _ARABIC_RE.search(text):
        return "ar"
    if text.strip():
        return "en"
    return None


def detect_language_per_video(captions: list[str]) -> list[dict[str, str | int]]:
    """Per-video language detection producing a distribution.

    Each non-empty caption is classified independently using the same regex
    heuristic as :func:`detect_language`.  Returns
    ``[{"name": "en", "value": 3}, ...]`` sorted by count desc.
    Returns ``[]`` if no captions have detectable content.
    """
    lang_counts: Counter[str] = Counter()
    for cap in captions:
        if not cap or not cap.strip():
            continue
        if _CJK_RE.search(cap):
            lang_counts["zh"] += 1
        elif _CYRILLIC_RE.search(cap):
            lang_counts["ru"] += 1
        elif _ARABIC_RE.search(cap):
            lang_counts["ar"] += 1
        else:
            lang_counts["en"] += 1
    return [{"name": lang, "value": count} for lang, count in lang_counts.most_common()]


def extract_mentions(captions: list[str]) -> list[dict[str, int]]:
    """Extract ``@username`` patterns from captions.

    Returns ``[{"label": username, "value": count}, ...]`` sorted by count desc.
    """
    mentions_temp: list[str] = []
    for cap in captions:
        mentions_temp.extend(m.lower() for m in _MENTION_RE.findall(cap))

    counter = Counter(mentions_temp)
    return [{"label": k, "value": v} for k, v in counter.most_common()]


def compute_engagement_rate(
    user_videos: list[dict[str, Any]], followers: int
) -> float | None:
    """Compute engagement rate as ``(avg_likes + avg_comments + avg_shares) / followers``.

    Returns ``None`` if ``followers == 0`` or no videos.
    """
    if not user_videos or followers == 0:
        return None

    total_likes = 0
    total_comments = 0
    total_shares = 0
    count = 0

    for video in user_videos:
        stats = video.get("statsV2", {})
        try:
            total_likes += int(stats.get("diggCount", 0))
            total_comments += int(stats.get("commentCount", 0))
            total_shares += int(stats.get("shareCount", 0))
            count += 1
        except (ValueError, TypeError):
            pass

    if count == 0:
        return None

    avg_likes = total_likes / count
    avg_comments = total_comments / count
    avg_shares = total_shares / count
    return (avg_likes + avg_comments + avg_shares) / followers


def compute_engagement_breakdown(
    user_videos: list[dict[str, Any]], followers: int
) -> list[dict[str, str | float | None]]:
    """7-item engagement breakdown: Avg Likes, Comments, Shares, Plays, Collects,
    Reposts, and Rate%.

    Returns a list of ``{"name": ..., "value": ...}`` dicts.  All values are
    ``None`` when there are no videos or ``followers == 0``.
    """
    metrics = [
        ("Avg Likes", "diggCount"),
        ("Avg Comments", "commentCount"),
        ("Avg Shares", "shareCount"),
        ("Avg Plays", "playCount"),
        ("Avg Collects", "collectCount"),
        ("Avg Reposts", "repostCount"),
    ]
    result: list[dict[str, str | float | None]] = []

    if not user_videos or followers == 0:
        for label, _ in metrics:
            result.append({"name": label, "value": None})
        result.append({"name": "Rate%", "value": None})
        return result

    totals: dict[str, int] = {field: 0 for _, field in metrics}
    count = 0
    for video in user_videos:
        stats = video.get("statsV2", {})
        try:
            for _, field in metrics:
                totals[field] += int(stats.get(field, 0))
            count += 1
        except (ValueError, TypeError):
            pass

    if count == 0:
        for label, _ in metrics:
            result.append({"name": label, "value": None})
        result.append({"name": "Rate%", "value": None})
        return result

    avgs: dict[str, float] = {field: totals[field] / count for _, field in metrics}
    for label, field in metrics:
        result.append({"name": label, "value": round(avgs[field], 2)})

    # Engagement rate: (avg_likes + avg_comments + avg_shares) / followers * 100
    rate = (
        (avgs["diggCount"] + avgs["commentCount"] + avgs["shareCount"])
        / followers
        * 100
    )
    result.append({"name": "Rate%", "value": round(rate, 2)})
    return result


def compute_ff_ratio(followers: int, following: int) -> float | None:
    """Followers / max(following, 1).  Returns ``None`` if ``followers == 0``."""
    if followers == 0:
        return None
    return round(followers / max(following, 1), 2)


def build_popularity_section(
    stats: dict[str, Any],
) -> list[dict[str, str | int]]:
    """Build the popularity chart: Followers, Friends, Following."""
    return [
        {"title": "Followers", "value": stats.get("followerCount", 0)},
        {"title": "Friends", "value": stats.get("friendCount", 0)},
        {"title": "Following", "value": stats.get("followingCount", 0)},
    ]


def build_approval_section(
    stats: dict[str, Any],
) -> list[dict[str, str | int]]:
    """Build the approval chart: Videos and Likes (heartCount)."""
    return [
        {"title": "Videos", "value": stats.get("videoCount", 0)},
        {"title": "Likes", "value": stats.get("heartCount", 0)},
    ]


def compute_avg_videos_per_day(timestamps: list[int]) -> float | None:
    """Average videos per day = count / max((max_ts - min_ts).days, 1).

    Returns ``None`` for fewer than 2 timestamps.
    """
    if len(timestamps) < 2:
        return None
    min_ts = min(timestamps)
    max_ts = max(timestamps)
    span_days = max(
        (
            datetime.fromtimestamp(max_ts, tz=UTC)
            - datetime.fromtimestamp(min_ts, tz=UTC)
        ).days,
        1,
    )
    return round(len(timestamps) / span_days, 2)


def format_privacy_settings(user_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Return gather items for duetSetting, stitchSetting, commentSetting.

    Maps 0 → 'All', 1 → 'Friends Only', 2 → 'Off'.  Skips absent fields.
    """
    link = "Tiktok"
    user = user_data.get("userInfo", {}).get("user", {})
    items: list[dict[str, Any]] = []
    fields = [
        ("duetSetting", "Duet", "fas fa-film"),
        ("stitchSetting", "Stitch", "fas fa-cut"),
        ("commentSetting", "Comments", "fas fa-comment"),
    ]
    for field, title, icon in fields:
        raw = user.get(field)
        if raw is None:
            continue
        try:
            label = _PRIVACY_LABELS.get(int(raw), str(raw))
        except (ValueError, TypeError):
            label = str(raw)
        items.append(
            {
                "name-node": f"Tik{title}",
                "title": title,
                "subtitle": label,
                "icon": icon,
                "link": link,
            }
        )
    return items


def build_soundtrack_chart(
    user_videos: list[dict[str, Any]],
) -> list[dict[str, str | int | bool]]:
    """Aggregate music tracks across videos.

    Returns ``[{"name": "title - artist", "value": count, "original": bool}, ...]``
    sorted by count desc.  Returns ``[]`` when no music data is present.
    """
    music_counter: Counter[str] = Counter()
    original_flags: dict[str, bool] = {}

    for video in user_videos:
        music = video.get("music")
        if not music:
            continue
        title = music.get("title", "").strip()
        author = music.get("authorName", "").strip()
        is_original = bool(music.get("original", False))
        if not title and not author:
            continue
        key = f"{title} - {author}" if title and author else title or author
        music_counter[key] += 1
        # A track is "original" if ANY occurrence has original=True
        original_flags[key] = original_flags.get(key, False) or is_original

    return [
        {"name": track, "value": count, "original": original_flags[track]}
        for track, count in music_counter.most_common()
    ]


def build_users_graph(
    mentions: list[dict[str, int]],
) -> list[dict[str, Any]]:
    """Convert mention list to Twitter-compatible node-link format.

    Input: output of :func:`extract_mentions` — ``[{"label": "user", "value": N}]``
    Output: ``[{name-node: "Users", title: "Users", subtitle: "", link: "Users"},
               {name-node: "@user", title: "@user", subtitle: N, link: "Users"}, ...]``
    """
    link = "Users"
    nodes: list[dict[str, Any]] = [
        {"name-node": "Users", "title": "Users", "subtitle": "", "link": link}
    ]
    for m in mentions:
        name = f"@{m['label']}"
        nodes.append(
            {"name-node": name, "title": name, "subtitle": m["value"], "link": link}
        )
    return nodes


def build_duration_histogram(
    user_videos: list[dict[str, Any]],
) -> list[dict[str, str | int]]:
    """Bucket video durations into Short (<15s), Medium (15-60s), Long (>60s).

    Reads ``video.duration`` from each video dict.  Zero/missing durations are
    placed in the Short bucket.  Returns ``[]`` when there are no videos.
    """
    if not user_videos:
        return []
    short = medium = long_ = 0
    for video in user_videos:
        try:
            dur = int(video.get("video", {}).get("duration", 0) or 0)
        except (ValueError, TypeError):
            dur = 0
        if dur < 15:
            short += 1
        elif dur <= 60:
            medium += 1
        else:
            long_ += 1
    return [
        {"name": "Short (<15s)", "value": short},
        {"name": "Medium (15-60s)", "value": medium},
        {"name": "Long (>60s)", "value": long_},
    ]


def compute_posts_vs_reposts(
    user_videos: list[dict[str, Any]],
) -> list[dict[str, str | int]]:
    """Count total videos and total repost actions across all videos.

    Uses ``statsV2.repostCount`` (number of times THIS video was reposted by
    others) to give an "engagement via reposts" view.
    Returns ``[{"name": "Original", "value": N}, {"name": "Reposts", "value": M}]``.
    Returns ``[]`` when there are no videos.
    """
    if not user_videos:
        return []
    total_videos = len(user_videos)
    total_reposts = 0
    for video in user_videos:
        stats = video.get("statsV2", {})
        with contextlib.suppress(ValueError, TypeError):
            total_reposts += int(stats.get("repostCount", 0))
    return [
        {"name": "Original", "value": total_videos},
        {"name": "Reposts", "value": total_reposts},
    ]


def extract_gather_flags(user_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Return gather items for isADVirtual and ttSeller boolean flags.

    Only appends an item if the field is present.  Absent fields default to
    ``False`` per spec, but they are still shown as gather cards.
    """
    link = "Tiktok"
    user = user_data.get("userInfo", {}).get("user", {})
    items: list[dict[str, Any]] = []

    flag_defs = [
        ("isADVirtual", "AI Virtual Account", "fas fa-robot"),
        ("ttSeller", "TikTok Shop Seller", "fas fa-store"),
    ]
    for field, title, icon in flag_defs:
        value = user.get(field, False)
        items.append(
            {
                "name-node": f"Tik{field}",
                "title": title,
                "subtitle": bool(value),
                "icon": icon,
                "link": link,
            }
        )
    return items


def enrich_output(
    gather: list[dict[str, Any]],
    graphic: list[dict[str, Any]],
    profile: list[dict[str, Any]],
    user_data: dict[str, Any],
    user_videos: list[dict[str, Any]],
    followers: int,
    following: int = 0,
) -> None:
    """Mutate ``gather`` and ``graphic`` to add enrichment fields in-place."""
    link = "Tiktok"
    captions = [v.get("desc", "") for v in user_videos]
    stats = user_data.get("userInfo", {}).get("stats", {})

    # Region
    region = user_data.get("userInfo", {}).get("user", {}).get("region")
    if region:
        gather.append(
            {
                "name-node": "TikRegion",
                "title": "Region",
                "subtitle": region,
                "icon": "fas fa-globe",
                "link": link,
            }
        )

    # --- P0: Profile-level metrics ---

    # F/F Ratio
    ff_ratio = compute_ff_ratio(followers, following)
    if ff_ratio is not None:
        gather.append(
            {
                "name-node": "TikFFRatio",
                "title": "F/F Ratio",
                "subtitle": f"{ff_ratio:.2f}",
                "icon": "fas fa-balance-scale",
                "link": link,
            }
        )

    # Avg videos per day
    timestamps = [int(v["createTime"]) for v in user_videos if v.get("createTime")]
    avg_vpd = compute_avg_videos_per_day(timestamps)
    if avg_vpd is not None:
        gather.append(
            {
                "name-node": "TikAvgVPD",
                "title": "Avg Videos/Day",
                "subtitle": str(avg_vpd),
                "icon": "fas fa-calendar-day",
                "link": link,
            }
        )

    # Privacy settings
    privacy_items = format_privacy_settings(user_data)
    gather.extend(privacy_items)

    # Boolean flags
    flag_items = extract_gather_flags(user_data)
    gather.extend(flag_items)

    # --- Engagement breakdown (replaces old single-value engagement) ---
    eng_breakdown = compute_engagement_breakdown(user_videos, followers)
    graphic.append({"engagement": eng_breakdown})

    # Also add engagement rate gather card (backward compat)
    if user_videos and followers > 0:
        eng_rate = compute_engagement_rate(user_videos, followers)
        if eng_rate is not None:
            gather.append(
                {
                    "name-node": "TikEngagement",
                    "title": "Engagement Rate",
                    "subtitle": f"{eng_rate * 100:.2f}%",
                    "icon": "fas fa-chart-line",
                    "link": link,
                }
            )

    # --- Language distribution (replaces old single-value language) ---
    lang_dist = detect_language_per_video(captions)
    if lang_dist:
        # Gather card: show dominant language
        dominant = lang_dist[0]["name"]
        gather.append(
            {
                "name-node": "TikLanguage",
                "title": "Language",
                "subtitle": dominant,
                "icon": "fas fa-language",
                "link": link,
            }
        )
        graphic.append({"language": lang_dist})

    # --- Popularity & Approval charts ---
    popularity = build_popularity_section(stats)
    graphic.append({"popularity": popularity})

    approval = build_approval_section(stats)
    graphic.append({"approval": approval})

    # --- Soundtrack ---
    soundtrack = build_soundtrack_chart(user_videos)
    graphic.append({"soundtrack": soundtrack})

    # --- Users graph ---
    mentions = extract_mentions(captions)
    users_graph = build_users_graph(mentions)
    graphic.append({"users": users_graph})

    # --- Duration histogram ---
    duration_hist = build_duration_histogram(user_videos)
    graphic.append({"duration": duration_hist})

    # --- Posts vs Reposts ---
    pvr = compute_posts_vs_reposts(user_videos)
    graphic.append({"postsvsreposts": pvr})


# ---------------------------------------------------------------------------
# Output builder (shared between live API and fallback paths)
# ---------------------------------------------------------------------------


def _build_output_from_api(
    username: str,
    user_data: dict[str, Any],
    user_videos: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Build the full output list from live TikTokApi data."""
    total: list[dict[str, Any]] = []
    total.append({"module": "tiktok"})
    total.append({"param": username})
    total.append({"validation": "no"})

    graphic: list[dict[str, Any]] = []
    photos: list[dict[str, Any]] = []
    presence: list[dict[str, Any]] = []
    profile: list[dict[str, Any]] = []
    timeline: list[dict[str, Any]] = []
    gather: list[dict[str, Any]] = []
    tasks: list[dict[str, Any]] = []

    link = "Tiktok"

    gather.append(
        {
            "name-node": "Tiktok",
            "title": "tiktok",
            "subtitle": "",
            "icon": "fab fa-tiktok",
            "link": link,
        }
    )

    # Name
    nickname = user_data["userInfo"]["user"]["nickname"]
    gather.append(
        {
            "name-node": "Tikname",
            "title": "Name",
            "subtitle": nickname,
            "icon": "fas fa-user",
            "link": link,
        }
    )
    profile.append({"name": nickname})

    # Posts
    gather.append(
        {
            "name-node": "TikPosts",
            "title": "Posts",
            "subtitle": user_data["userInfo"]["stats"]["videoCount"],
            "icon": "fas fa-photo-video",
            "link": link,
        }
    )

    # Followers / Following / Friends
    followers = int(user_data["userInfo"]["stats"]["followerCount"])
    following = int(user_data["userInfo"]["stats"].get("followingCount", 0))
    gather.append(
        {
            "name-node": "TikFollowers",
            "title": "Followers",
            "subtitle": followers,
            "icon": "fas fa-users",
            "link": link,
        }
    )
    gather.append(
        {
            "name-node": "TikFollowing",
            "title": "Following",
            "subtitle": following,
            "icon": "fas fa-users",
            "link": link,
        }
    )

    # Avatar
    avatar_url = user_data["userInfo"]["user"]["avatarLarger"]
    gather.append(
        {
            "name-node": "TikAvatar",
            "title": "Avatar",
            "picture": avatar_url,
            "subtitle": "",
            "link": link,
        }
    )
    profile.append({"photos": [{"picture": avatar_url, "title": "tiktok"}]})

    # Bio / signature
    try:
        sig = user_data["userInfo"]["user"]["signature"]
        if sig:
            gather.append(
                {
                    "name-node": "tikBio",
                    "title": "Bio",
                    "subtitle": sig,
                    "icon": "fas fa-heart",
                    "link": link,
                }
            )
            profile.append({"bio": sig})

            analyze = analize_rrss(sig)
            for item in analyze:
                if item == "url":
                    for i in analyze["url"]:
                        profile.append(i)
                if item == "tasks":
                    for i in analyze["tasks"]:
                        tasks.append(i)
    except Exception:
        pass

    # Bio link
    try:
        bio_link = user_data["userInfo"]["user"]["bioLink"]["link"]
        if bio_link:
            profile.append({"url": bio_link})
    except Exception:
        pass

    # Friends
    gather.append(
        {
            "name-node": "TikFriend",
            "title": "Friends",
            "subtitle": user_data["userInfo"]["stats"]["friendCount"],
            "icon": "fas fa-handshake",
            "link": link,
        }
    )

    # Nickname modify time
    try:
        nick_ts = int(user_data["userInfo"]["user"]["nickNameModifyTime"])
        nick_date = datetime.fromtimestamp(nick_ts, tz=UTC).strftime("%Y-%m-%d")
        timeline.append(
            {
                "date": nick_date,
                "action": "tiktok : Nickname modified",
                "icon": "fa-tiktok",
            }
        )
    except Exception:
        pass

    # Likes (heartCount)
    gather.append(
        {
            "name-node": "TikHeart",
            "title": "Likes",
            "subtitle": user_data["userInfo"]["stats"]["heartCount"],
            "icon": "fas fa-heart",
            "link": link,
        }
    )

    # Privacy / flags
    gather.append(
        {
            "name-node": "TikPrivate",
            "title": "Private Account",
            "subtitle": user_data["userInfo"]["user"]["privateAccount"],
            "icon": "fas fa-user-shield",
            "link": link,
        }
    )
    gather.append(
        {
            "name-node": "TikUsername",
            "title": "Username",
            "subtitle": user_data["userInfo"]["user"]["uniqueId"],
            "icon": "fas fa-user",
            "link": link,
        }
    )
    gather.append(
        {
            "name-node": "TiktUserID",
            "title": "UserID",
            "subtitle": user_data["userInfo"]["user"]["id"],
            "icon": "fas fa-user-circle",
            "link": link,
        }
    )
    gather.append(
        {
            "name-node": "TiktBuss",
            "title": "Bussiness Account",
            "subtitle": user_data["userInfo"]["user"]["commerceUserInfo"][
                "commerceUser"
            ],
            "icon": "fas fa-building",
            "link": link,
        }
    )
    gather.append(
        {
            "name-node": "TiktVerified",
            "title": "Verified Account",
            "subtitle": user_data["userInfo"]["user"]["verified"],
            "icon": "fas fa-certificate",
            "link": link,
        }
    )

    # Social link
    profile.append(
        {
            "social": [
                {
                    "name": "tiktok",
                    "url": f"https://tiktok.com/@{username}",
                    "icon": "fab fa-tiktok",
                    "source": "tiktok",
                    "username": username,
                }
            ]
        }
    )

    # --- Video aggregation ---
    stop = 0
    captions: list[str] = []
    hashtags_temp: list[str] = []
    lk_cm: list[dict[str, Any]] = []
    s_cl: list[dict[str, str]] = []
    s_cm: list[dict[str, str]] = []
    s_lk: list[dict[str, str]] = []
    s_pl: list[dict[str, str]] = []
    s_rp: list[dict[str, str]] = []
    s_sh: list[dict[str, str]] = []
    week_temp: list[str] = []
    hour_temp: list[str] = []
    t_timeline: list[dict[str, Any]] = []

    link_lower = "tiktok"
    photos_item: dict[str, Any] = {
        "name-node": "tiktok",
        "title": "tiktok",
        "subtitle": "",
        "icon": "fab fa-tiktok",
        "link": link_lower,
    }
    photos.append(photos_item)

    logger.info("Begin - Getting post information")
    user_videos = sorted(user_videos, key=lambda x: x["createTime"])

    for post in user_videos:
        try:
            if post["isPinnedItem"]:
                continue
        except Exception:
            pass

        stats = post.get("statsV2", {})
        s_cl.append({"name": str(stop), "value": str(stats.get("collectCount", 0))})
        s_cm.append({"name": str(stop), "value": str(stats.get("commentCount", 0))})
        s_lk.append({"name": str(stop), "value": str(stats.get("diggCount", 0))})
        s_pl.append({"name": str(stop), "value": str(stats.get("playCount", 0))})
        s_rp.append({"name": str(stop), "value": str(stats.get("repostCount", 0))})
        s_sh.append({"name": str(stop), "value": str(stats.get("shareCount", 0))})

        try:
            for h in post["textExtra"]:
                hashtags_temp.append(h["hashtagName"])
        except Exception:
            pass

        captions.append(post.get("desc", ""))

        create_ts = int(post["createTime"])
        week_temp.append(datetime.fromtimestamp(create_ts, tz=UTC).strftime("%A"))
        hour_temp.append(datetime.fromtimestamp(create_ts, tz=UTC).strftime("%H"))

        photos.append(
            {
                "name-node": f"TikTok{stop}",
                "title": f"Video{stop}",
                "picture": post["video"]["cover"],
                "subtitle": "",
                "link": link_lower,
            }
        )

        created_at = datetime.fromtimestamp(create_ts, tz=UTC).strftime("%Y-%m-%d")
        t_timeline.append({"name": created_at, "value": 1})

        stop += 1

    # Last post + calendar timeline
    tiktok_time: list[dict[str, Any]] = []
    if t_timeline:
        timeline.append(
            {
                "date": t_timeline[-1]["name"],
                "action": "Tiktok : Last Post",
                "icon": "fa-tiktok",
            }
        )
        start_date = datetime.strptime(t_timeline[0]["name"], "%Y-%m-%d")
        end_date = datetime.strptime(t_timeline[-1]["name"], "%Y-%m-%d")
        delta_days = (end_date - start_date).days
        for i in range(delta_days + 1):
            current_date = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
            record_count = sum(1 for item in t_timeline if item["name"] == current_date)
            tiktok_time.append({"name": current_date, "value": record_count})

    # Stats series
    lk_cm.append({"name": "Likes", "series": s_lk})
    lk_cm.append({"name": "Comments", "series": s_cm})
    lk_cm.append({"name": "Collect", "series": s_cl})
    lk_cm.append({"name": "Play", "series": s_pl})
    lk_cm.append({"name": "Repost", "series": s_rp})
    lk_cm.append({"name": "Shared", "series": s_sh})

    # Hashtags
    hashtags: list[dict[str, Any]] = []
    for k, v in Counter(hashtags_temp).items():
        hashtags.append({"label": k, "value": v})

    # Hour / week distributions
    hourset = _build_hourset(hour_temp)
    weekset = _build_weekset(week_temp)

    # Resume node
    children = [
        {
            "name": "Follower",
            "total": str(user_data["userInfo"]["stats"]["followerCount"]),
        },
        {
            "name": "Following",
            "total": str(user_data["userInfo"]["stats"]["followingCount"]),
        },
        {
            "name": "Friends",
            "total": str(user_data["userInfo"]["stats"]["friendCount"]),
        },
        {"name": "Likes", "total": str(user_data["userInfo"]["stats"]["heartCount"])},
        {"name": "Videos", "total": str(user_data["userInfo"]["stats"]["videoCount"])},
    ]
    resume = {"name": "tiktok", "children": children}

    # Presence
    presence.append(
        {
            "name": "tiktok",
            "children": [
                {
                    "name": "followers",
                    "value": int(user_data["userInfo"]["stats"]["followerCount"]),
                },
                {
                    "name": "following",
                    "value": int(user_data["userInfo"]["stats"]["followingCount"]),
                },
            ],
        }
    )
    profile.append({"presence": presence})

    # Enrichment (mutates gather + graphic)
    enrich_output(
        gather, graphic, profile, user_data, user_videos, followers, following
    )

    # Assemble final output
    raw_node = {"user_data": user_data, "user_video": user_videos}
    total.append({"raw": raw_node})
    graphic.insert(0, {"tiktok": gather})
    graphic.append({"postslist": lk_cm})
    graphic.append({"hashtags": hashtags})
    # mentions already added inside enrich_output via build_users_graph;
    # keep the flat list for backward compat under "mentions" key
    mentions = extract_mentions(captions)
    graphic.append({"mentions": mentions})
    graphic.append({"tagged": []})
    graphic.append({"hour": hourset})
    graphic.append({"week": weekset})
    graphic.append({"videos": photos})
    graphic.append({"resume": resume})
    graphic.append({"tiktime": tiktok_time})
    total.append({"graphic": graphic})
    total.append({"profile": profile})
    total.append({"timeline": timeline})
    total.append({"tasks": tasks})

    return total


def _build_output_from_fallback(
    username: str,
    user_data: dict[str, Any],
) -> list[dict[str, Any]]:
    """Build output from HTTP fallback (no video data).

    The output structure matches ``_build_output_from_api`` as closely as
    possible.  Video-dependent sections are emitted as empty lists; all
    profile-level data (gather cards, resume sunburst, presence, timeline)
    is fully populated from the available stats.
    """
    total: list[dict[str, Any]] = []
    total.append({"module": "tiktok"})
    total.append({"param": username})
    total.append({"validation": "no"})

    graphic: list[dict[str, Any]] = []
    photos: list[dict[str, Any]] = []
    presence: list[dict[str, Any]] = []
    profile: list[dict[str, Any]] = []
    timeline: list[dict[str, Any]] = []
    gather: list[dict[str, Any]] = []
    tasks: list[dict[str, Any]] = []

    link = "Tiktok"

    gather.append(
        {
            "name-node": "Tiktok",
            "title": "tiktok",
            "subtitle": "",
            "icon": "fab fa-tiktok",
            "link": link,
        }
    )

    user = user_data.get("userInfo", {}).get("user", {})
    stats = user_data.get("userInfo", {}).get("stats", {})

    # Name
    nickname = user.get("nickname", username)
    gather.append(
        {
            "name-node": "Tikname",
            "title": "Name",
            "subtitle": nickname,
            "icon": "fas fa-user",
            "link": link,
        }
    )
    profile.append({"name": nickname})

    # Posts
    if stats.get("videoCount") is not None:
        gather.append(
            {
                "name-node": "TikPosts",
                "title": "Posts",
                "subtitle": stats["videoCount"],
                "icon": "fas fa-photo-video",
                "link": link,
            }
        )

    # Followers
    if stats.get("followerCount") is not None:
        gather.append(
            {
                "name-node": "TikFollowers",
                "title": "Followers",
                "subtitle": stats["followerCount"],
                "icon": "fas fa-users",
                "link": link,
            }
        )

    # Following
    if stats.get("followingCount") is not None:
        gather.append(
            {
                "name-node": "TikFollowing",
                "title": "Following",
                "subtitle": stats["followingCount"],
                "icon": "fas fa-users",
                "link": link,
            }
        )

    # Avatar
    avatar = user.get("avatarLarger")
    if avatar:
        gather.append(
            {
                "name-node": "TikAvatar",
                "title": "Avatar",
                "picture": avatar,
                "subtitle": "",
                "link": link,
            }
        )
        profile.append({"photos": [{"picture": avatar, "title": "tiktok"}]})

    # Bio / signature
    try:
        sig = user.get("signature", "")
        if sig:
            gather.append(
                {
                    "name-node": "tikBio",
                    "title": "Bio",
                    "subtitle": sig,
                    "icon": "fas fa-heart",
                    "link": link,
                }
            )
            profile.append({"bio": sig})

            analyze = analize_rrss(sig)
            for item in analyze:
                if item == "url":
                    for i in analyze["url"]:
                        profile.append(i)
                if item == "tasks":
                    for i in analyze["tasks"]:
                        tasks.append(i)
    except Exception:
        pass

    # Bio link
    try:
        bio_link = user.get("bioLink", {}).get("link", "")
        if bio_link:
            profile.append({"url": bio_link})
    except Exception:
        pass

    # Friends
    if stats.get("friendCount") is not None:
        gather.append(
            {
                "name-node": "TikFriend",
                "title": "Friends",
                "subtitle": stats["friendCount"],
                "icon": "fas fa-handshake",
                "link": link,
            }
        )

    # Nickname modify time
    try:
        nick_ts = int(user.get("nickNameModifyTime", 0))
        if nick_ts:
            nick_date = datetime.fromtimestamp(nick_ts, tz=UTC).strftime("%Y-%m-%d")
            timeline.append(
                {
                    "date": nick_date,
                    "action": "tiktok : Nickname modified",
                    "icon": "fa-tiktok",
                }
            )
    except Exception:
        pass

    # Likes (heartCount)
    if stats.get("heartCount") is not None:
        gather.append(
            {
                "name-node": "TikHeart",
                "title": "Likes",
                "subtitle": stats["heartCount"],
                "icon": "fas fa-heart",
                "link": link,
            }
        )

    # Privacy / flags
    if user.get("privateAccount") is not None:
        gather.append(
            {
                "name-node": "TikPrivate",
                "title": "Private Account",
                "subtitle": user["privateAccount"],
                "icon": "fas fa-user-shield",
                "link": link,
            }
        )

    unique_id = user.get("uniqueId", "")
    if unique_id:
        gather.append(
            {
                "name-node": "TikUsername",
                "title": "Username",
                "subtitle": unique_id,
                "icon": "fas fa-user",
                "link": link,
            }
        )

    user_id = user.get("id", "")
    if user_id:
        gather.append(
            {
                "name-node": "TiktUserID",
                "title": "UserID",
                "subtitle": user_id,
                "icon": "fas fa-user-circle",
                "link": link,
            }
        )

    try:
        commerce_user = user.get("commerceUserInfo", {}).get("commerceUser")
        if commerce_user is not None:
            gather.append(
                {
                    "name-node": "TiktBuss",
                    "title": "Bussiness Account",
                    "subtitle": commerce_user,
                    "icon": "fas fa-building",
                    "link": link,
                }
            )
    except Exception:
        pass

    if user.get("verified") is not None:
        gather.append(
            {
                "name-node": "TiktVerified",
                "title": "Verified Account",
                "subtitle": user["verified"],
                "icon": "fas fa-certificate",
                "link": link,
            }
        )

    # Social link
    profile.append(
        {
            "social": [
                {
                    "name": "tiktok",
                    "url": f"https://tiktok.com/@{username}",
                    "icon": "fab fa-tiktok",
                    "source": "tiktok",
                    "username": username,
                }
            ]
        }
    )

    # Resume sunburst — built from stats even without video data
    children = [
        {
            "name": "Follower",
            "total": str(stats.get("followerCount", 0)),
        },
        {
            "name": "Following",
            "total": str(stats.get("followingCount", 0)),
        },
        {
            "name": "Friends",
            "total": str(stats.get("friendCount", 0)),
        },
        {"name": "Likes", "total": str(stats.get("heartCount", 0))},
        {"name": "Videos", "total": str(stats.get("videoCount", 0))},
    ]
    resume = {"name": "tiktok", "children": children}

    # Presence
    presence.append(
        {
            "name": "tiktok",
            "children": [
                {
                    "name": "followers",
                    "value": int(stats.get("followerCount", 0)),
                },
                {
                    "name": "following",
                    "value": int(stats.get("followingCount", 0)),
                },
            ],
        }
    )
    profile.append({"presence": presence})

    # Enrichment with empty user_videos — profile-level helpers work,
    # video-dependent ones return empty/None and are skipped
    followers = int(stats.get("followerCount", 0))
    following = int(stats.get("followingCount", 0))
    enrich_output(gather, graphic, profile, user_data, [], followers, following)

    # Assemble final output — matches _build_output_from_api structure exactly;
    # video-dependent sections emitted as empty lists
    raw_node = {"user_data": user_data, "user_video": []}
    total.append({"raw": raw_node})
    graphic.insert(0, {"tiktok": gather})
    graphic.append({"postslist": []})
    graphic.append({"hashtags": []})
    graphic.append({"mentions": []})
    graphic.append({"tagged": []})
    graphic.append({"hour": []})
    graphic.append({"week": []})
    graphic.append({"videos": photos})
    graphic.append({"resume": resume})
    graphic.append({"tiktime": []})
    total.append({"graphic": graphic})
    total.append({"profile": profile})
    total.append({"timeline": timeline})
    total.append({"tasks": tasks})

    return total


def _build_hourset(hour_temp: list[str]) -> list[dict[str, Any]]:
    hournames = "00 01 02 03 04 05 06 07 08 09 10 11 12 13 14 15 16 17 18 19 20 21 22 23".split()
    tw_counter = Counter(hour_temp)
    tgdata = sorted(tw_counter.most_common())
    hourset = []
    e = 0
    for g in hournames:
        if (e >= len(tgdata)) or (g < tgdata[e][0]):
            hourset.append({"name": g, "value": 0})
        elif g == tgdata[e][0]:
            hourset.append({"name": g, "value": int(tgdata[e][1])})
            e += 1
    return hourset


def _build_weekset(week_temp: list[str]) -> list[dict[str, Any]]:
    weekdays = "Monday Tuesday Wednesday Thursday Friday Saturday Sunday".split()
    wd_counter = Counter(week_temp)
    wd_data = sorted(wd_counter.most_common())
    weekset = []
    for c, z in enumerate(weekdays):
        try:
            weekset.append({"name": z, "value": int(wd_data[c][1])})
        except Exception:
            weekset.append({"name": z, "value": 0})
    return weekset


# ---------------------------------------------------------------------------
# Main task
# ---------------------------------------------------------------------------


@iky_task(module_name="tiktok", dev_mode_sleep=5)
def p_tiktok(username: str, num: int = 15) -> list[dict[str, Any]]:
    """Fetch TikTok profile and video data for ``username``."""

    cookie_keys = ["msToken"]
    json_cookies = get_tiktok_cookies(cookie_keys)

    if json_cookies["found"]:
        logger.info("TikTok cookies found — using live API path")
        ms_token = json_cookies["cookies"]["msToken"]
        user_data, user_videos = run_get_user_info(ms_token, username, num)
        return _build_output_from_api(username, user_data, user_videos)

    # Cookie-free fallback
    logger.warning(
        "TikTok msToken not found — attempting HTTP fallback for @%s", username
    )
    user_data = http_fallback_profile(username)
    return _build_output_from_fallback(username, user_data)


# Backward-compatible alias: existing code references t_tiktok
t_tiktok = p_tiktok


def output(data: list[dict[str, Any]]) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Query TikTok for a username")
    parser.add_argument("username", help="TikTok username to look up")
    args = parser.parse_args()

    result = t_tiktok(args.username)
    output(result)
