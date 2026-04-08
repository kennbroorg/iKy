#!/usr/bin/env python
"""Mastodon OSINT module — @iky_task decorator with enrichment pipeline.

Fetches public account data via the Mastodon REST API:
  - /api/v1/accounts/lookup   (direct lookup when server is known)
  - /api/v2/search            (fallback / username-only resolution)
  - /api/v1/accounts/:id/statuses  (toot history, paginated)
  - /api/v1/accounts/:id/featured_tags  (featured hashtags)
"""

import argparse
import json
import re
import time
from collections import Counter
from datetime import UTC, datetime

import requests
from bs4 import BeautifulSoup
from celery.utils.log import get_task_logger
from factories.fontcheat import search_icon_5
from factories.iKy_functions import analize_rrss
from factories.task_wrapper import iky_task
from w3lib.html import remove_tags

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
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.4.1 Mobile/15E148 Safari/604.1",
)

_DEFAULT_SERVER = "mastodon.social"
_STATUSES_LIMIT = 40
_STATUSES_MAX_PAGES = 5
_SLEEP_BETWEEN_PAGES = 0.3

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

# ---------------------------------------------------------------------------
# Private HTTP helpers
# ---------------------------------------------------------------------------


def _make_session() -> requests.Session:
    """Return a Session with a random modern User-Agent header."""
    import random

    session = requests.Session()
    session.headers["User-Agent"] = random.choice(_USER_AGENTS)
    return session


def _parse_username(username: str) -> tuple[str, str | None]:
    """Parse Mastodon username into (user, server|None).

    Accepts: ``user``, ``@user``, ``user@server``, ``@user@server``.
    Raises ``Exception("iKy - Invalid input parameters")`` on invalid input.
    """
    pattern = r"^@?([\w\-\.]+)(?:@([a-zA-Z0-9_\-\.]+))?$"
    match = re.match(pattern, username.strip())
    if not match:
        raise Exception("iKy - Invalid input parameters")
    user = match.group(1)
    server = match.group(2) or None
    if not user:
        raise Exception("iKy - Invalid input parameters")
    return user, server


def _extract_server_from_url(url: str) -> str:
    """Extract the instance hostname from a Mastodon account URL.

    E.g. ``"https://mastodon.social/@gargron"`` → ``"mastodon.social"``.
    Falls back to ``_DEFAULT_SERVER`` on parse failure.
    """
    try:
        m = re.match(r"https?://([^/]+)", url)
        return m.group(1) if m else _DEFAULT_SERVER
    except (TypeError, AttributeError):
        return _DEFAULT_SERVER


# ---------------------------------------------------------------------------
# Private resolution helpers
# ---------------------------------------------------------------------------


def _lookup_account(session: requests.Session, server: str, user: str) -> dict | None:
    """Try ``GET /api/v1/accounts/lookup?acct={user}`` on *server*.

    Returns the account dict on success, ``None`` if not found / unreachable
    (404, 422, connection error).  Raises for 429 / unexpected errors.
    """
    url = f"https://{server}/api/v1/accounts/lookup"
    try:
        resp = session.get(url, params={"acct": user}, timeout=30)
    except requests.RequestException as exc:
        logger.warning(
            "iKy - Mastodon lookup unreachable on %s for %s: %s — falling back to search",
            server,
            user,
            exc,
        )
        return None

    match resp.status_code:
        case 200:
            return resp.json()
        case 404 | 422:
            return None
        case 429:
            raise Exception("iKy - Rate limited by Mastodon")
        case _:
            # Unknown error on this server — treat as unreachable
            return None


def _search_accounts(session: requests.Session, user: str) -> list[dict]:
    """Search mastodon.social for *user* via ``GET /api/v2/search``.

    Returns a (possibly empty) list of matching account dicts.
    Raises for 404/429/timeout or empty-JSON responses.
    """
    url = f"https://{_DEFAULT_SERVER}/api/v2/search"
    try:
        resp = session.get(url, params={"q": user, "type": "accounts"}, timeout=30)
    except requests.Timeout as exc:
        raise Exception("iKy - Mastodon search timed out") from exc
    except requests.RequestException as exc:
        raise Exception(f"iKy - Mastodon search failed: {exc}") from exc

    match resp.status_code:
        case 200:
            pass
        case 429:
            raise Exception("iKy - Rate limited by Mastodon")
        case _:
            raise Exception(f"iKy - Mastodon search returned HTTP {resp.status_code}")

    try:
        data = resp.json()
    except ValueError as exc:
        raise Exception(f"iKy - Invalid JSON from Mastodon search: {exc}") from exc

    # Filter: exact username match (case-insensitive)
    accounts = data.get("accounts", [])
    return [a for a in accounts if a.get("username", "").lower() == user.lower()]


def _resolve_account(
    session: requests.Session, user: str, server: str | None
) -> dict | list[dict]:
    """Resolve *user* to one or more account dicts.

    Returns:
    - A single ``dict`` for a unique match (→ one_user flow).
    - A ``list[dict]`` for multiple matches (→ several_user flow).

    Raises ``Exception("iKy - ...")`` if no account found.
    """
    # Step 1: Direct lookup when server is known
    if server:
        account = _lookup_account(session, server, user)
        if account:
            return account
        # Fallback to search on the default server

    # Step 2: Search on mastodon.social
    matches = _search_accounts(session, user)

    if not matches:
        raise Exception(f"iKy - Username: {user} NOT found using the Mastodon API!")

    if len(matches) == 1:
        return matches[0]

    return matches  # multiple → several_user flow


# ---------------------------------------------------------------------------
# Private enrichment helpers
# ---------------------------------------------------------------------------


def _fetch_statuses(
    session: requests.Session, account_id: str, server: str
) -> list[dict]:
    """Fetch up to 200 toots via paginated ``/api/v1/accounts/:id/statuses``.

    Uses ``max_id`` from last toot in each page.  Sleeps between pages.
    Returns ``[]`` on 403 (non-fatal).
    """
    import random

    url = f"https://{server}/api/v1/accounts/{account_id}/statuses"
    statuses: list[dict] = []
    max_id: str | None = None

    for page in range(_STATUSES_MAX_PAGES):
        session.headers["User-Agent"] = random.choice(_USER_AGENTS)
        params: dict = {"limit": _STATUSES_LIMIT, "exclude_replies": "false"}
        if max_id:
            params["max_id"] = max_id

        try:
            resp = session.get(url, params=params, timeout=30)
        except requests.RequestException as exc:
            logger.warning(
                "Mastodon statuses fetch failed on page %d: %s", page + 1, exc
            )
            break

        if resp.status_code == 403:
            # Private/blocked — non-fatal
            return []
        if resp.status_code != 200:
            logger.warning(
                "Mastodon statuses HTTP %s on page %d — stopping",
                resp.status_code,
                page + 1,
            )
            break

        try:
            page_data = resp.json()
        except ValueError:
            logger.warning("Mastodon statuses invalid JSON on page %d", page + 1)
            break

        if not page_data:
            break

        statuses.extend(page_data)

        # Next page cursor: max_id = id of the last toot on this page
        max_id = page_data[-1]["id"]

        if len(page_data) < _STATUSES_LIMIT:
            # Last page — fewer items than requested
            break

        if page < _STATUSES_MAX_PAGES - 1:
            time.sleep(_SLEEP_BETWEEN_PAGES)

    return statuses


def _fetch_featured_tags(
    session: requests.Session, account_id: str, server: str
) -> list[dict]:
    """Fetch ``/api/v1/accounts/:id/featured_tags``.

    Returns simplified ``[{name, statuses_count}, ...]`` or ``[]`` on failure.
    """
    import random

    url = f"https://{server}/api/v1/accounts/{account_id}/featured_tags"
    try:
        session.headers["User-Agent"] = random.choice(_USER_AGENTS)
        resp = session.get(url, timeout=30)
        if resp.status_code != 200:
            return []
        tags = resp.json()
        return [
            {"name": t.get("name", ""), "statuses_count": t.get("statuses_count", 0)}
            for t in tags
            if t.get("name")
        ]
    except (requests.RequestException, ValueError, KeyError):
        logger.warning("Mastodon featured_tags fetch failed — ignoring")
        return []


# ---------------------------------------------------------------------------
# Private analytics helpers
# ---------------------------------------------------------------------------


def _build_hour_chart(statuses: list[dict]) -> list[dict]:
    """Return 24-entry hour activity list from toot ``created_at`` timestamps."""
    if not statuses:
        return []

    counts: Counter = Counter()
    for status in statuses:
        created_at = status.get("created_at", "")
        if not created_at:
            continue
        try:
            dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            counts[dt.astimezone(UTC).hour] += 1
        except (ValueError, AttributeError):
            continue

    return [
        {"name": name, "value": counts.get(h, 0)} for h, name in enumerate(_HOUR_NAMES)
    ]


def _build_week_chart(statuses: list[dict]) -> list[dict]:
    """Return 7-entry weekday activity list from toot ``created_at`` timestamps."""
    if not statuses:
        return []

    counts: Counter = Counter()
    for status in statuses:
        created_at = status.get("created_at", "")
        if not created_at:
            continue
        try:
            dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            counts[dt.astimezone(UTC).weekday()] += 1
        except (ValueError, AttributeError):
            continue

    return [
        {"name": name, "value": counts.get(wd, 0)}
        for wd, name in enumerate(_WEEKDAY_NAMES)
    ]


def _build_hashtag_bubble(statuses: list[dict]) -> dict:
    """Return bubble-chart dict from hashtags found in statuses.

    Returns ``{}`` if no statuses or no hashtags.
    """
    if not statuses:
        return {}

    counter: Counter = Counter()
    for status in statuses:
        tags = status.get("tags", [])
        for tag in tags:
            name = tag.get("name", "")
            if name:
                counter[name.lower()] += 1

    if not counter:
        return {}

    children = [
        {"name": name, "count": cnt, "value": cnt}
        for name, cnt in counter.most_common()
    ]
    return {"name": "", "value": 100, "children": children}


def _compute_analytics(statuses: list[dict]) -> dict:
    """Compute all analytics from statuses list.

    Returns dict with: hour_chart, week_chart, hashtag_bubble,
    boost_ratio, media_count, total_favourites, total_reblogs,
    total_replies, originals, engagement_series.
    """
    if not statuses:
        return {
            "hour_chart": [],
            "week_chart": [],
            "hashtag_bubble": {},
            "boost_ratio": 0.0,
            "media_count": 0,
            "total_favourites": 0,
            "total_reblogs": 0,
            "total_replies": 0,
            "originals": 0,
            "engagement_series": [],
        }

    total = len(statuses)
    boosts = sum(1 for s in statuses if s.get("reblog") is not None)
    media_count = sum(len(s.get("media_attachments", [])) for s in statuses)

    total_favourites = sum(s.get("favourites_count", 0) for s in statuses)
    total_reblogs = sum(s.get("reblogs_count", 0) for s in statuses)
    total_replies = sum(s.get("replies_count", 0) for s in statuses)
    originals = total - boosts

    # Last 50 toots in chronological order (statuses are reverse-chron from API)
    recent = statuses[-50:]
    engagement_series = [
        {
            "name": s.get("created_at", "")[:10],
            "favourites": s.get("favourites_count", 0),
            "reblogs": s.get("reblogs_count", 0),
            "replies": s.get("replies_count", 0),
        }
        for s in recent
    ]

    return {
        "hour_chart": _build_hour_chart(statuses),
        "week_chart": _build_week_chart(statuses),
        "hashtag_bubble": _build_hashtag_bubble(statuses),
        "boost_ratio": round(boosts / total, 4) if total > 0 else 0.0,
        "media_count": media_count,
        "total_favourites": total_favourites,
        "total_reblogs": total_reblogs,
        "total_replies": total_replies,
        "originals": originals,
        "engagement_series": engagement_series,
    }


# ---------------------------------------------------------------------------
# Private response assembly helpers
# ---------------------------------------------------------------------------


def _several_user(username: str, user_data: list[dict]) -> list[dict]:
    """Assemble 8-element response for multi-match resolution."""
    list_user = []
    for info in user_data:
        acct = info.get("acct", "")
        # Extract user/server from acct field
        m = re.match(r"^@?([\w\-\.]+)(?:@([a-zA-Z0-9_\-\.]+))?$", acct)
        if m:
            user_masto = m.group(1) or ""
            server_masto = m.group(2) or ""
        else:
            user_masto = server_masto = ""

        list_user.append(
            {
                "account": acct,
                "username": user_masto,
                "server": server_masto,
                "avatar": info.get("avatar", ""),
                "followers": info.get("followers_count", 0),
                "following": info.get("following_count", 0),
                "toots": info.get("statuses_count", 0),
                "bios": remove_tags(info.get("note", "")),
            }
        )

    graphic = [
        {"user": []},
        {"social": []},
        {"list": list_user},
    ]

    return [
        {"module": "mastodon"},
        {"param": username},
        {"validation": "no"},
        {"raw": user_data},
        {"graphic": graphic},
        {"profile": []},
        {"timeline": []},
        {"tasks": []},
    ]


def _one_user(
    username: str,
    info: dict,
    statuses: list[dict],
    featured_tags: list[dict],
    analytics: dict,
) -> list[dict]:
    """Assemble enriched 8-element response for a single resolved account."""
    # ---- Graph / graphic nodes ----------------------------------------
    graph: list[dict] = []
    social: list[dict] = []
    profile: list[dict] = []
    social_profile: list[dict] = []
    timeline: list[dict] = []
    tasks: list[dict] = []
    presence: list[dict] = []

    link_graph = "MastodonGraph"
    link_social = "MastodonSocial"

    # Root nodes
    graph.append(
        {
            "name-node": "MastodonGraph",
            "title": "MastodonGraphs",
            "subtitle": "",
            "icon": "fab fa-mastodon",
            "link": link_graph,
        }
    )
    social.append(
        {
            "name-node": "MastodonSocial",
            "title": "MastodonSocial",
            "subtitle": "",
            "icon": "fas fa-child",
            "link": link_social,
        }
    )

    # Username
    graph.append(
        {
            "name-node": "GraphUsername",
            "title": "Username",
            "subtitle": username,
            "icon": "fas fa-user",
            "link": link_graph,
        }
    )

    # Followers / Following / Posts
    graph.append(
        {
            "name-node": "GraphFollowers",
            "title": "Followers",
            "subtitle": info.get("followers_count", 0),
            "icon": "fas fa-users",
            "link": link_graph,
        }
    )
    graph.append(
        {
            "name-node": "GraphFollowing",
            "title": "Following",
            "subtitle": info.get("following_count", 0),
            "icon": "fas fa-users",
            "link": link_graph,
        }
    )
    graph.append(
        {
            "name-node": "GraphPosts",
            "title": "Toots",
            "subtitle": info.get("statuses_count", 0),
            "icon": "fas fa-tooth",
            "link": link_graph,
        }
    )

    # Display name
    display_name = info.get("display_name", "")
    profile.append({"name": display_name})
    graph.append(
        {
            "name-node": "GraphName",
            "title": "Name",
            "subtitle": display_name,
            "icon": "fas fa-signature",
            "link": link_graph,
        }
    )

    # Locked
    if info.get("locked"):
        graph.append(
            {
                "name-node": "MastoLocked",
                "title": "Locked?",
                "subtitle": "User Locked",
                "icon": "fab fa-lock",
                "link": link_graph,
            }
        )
    else:
        graph.append(
            {
                "name-node": "MastoLocked",
                "title": "Locked?",
                "subtitle": "User NOT Locked",
                "icon": "fas fa-lock-open",
                "link": link_graph,
            }
        )

    # User type: group / bot / human
    if info.get("group"):
        graph.append(
            {
                "name-node": "MastoGroup",
                "title": "User Type",
                "subtitle": "Group",
                "icon": "fas fa-users",
                "link": link_graph,
            }
        )
    elif info.get("bot"):
        graph.append(
            {
                "name-node": "MastoBot",
                "title": "User Type",
                "subtitle": "Robot",
                "icon": "fas fa-robot",
                "link": link_graph,
            }
        )
    else:
        graph.append(
            {
                "name-node": "MastoHuman",
                "title": "User Type",
                "subtitle": "Human",
                "icon": "fas fa-user",
                "link": link_graph,
            }
        )

    # Discoverable
    if info.get("discoverable") is not None:
        graph.append(
            {
                "name-node": "MastoDiscoverable",
                "title": "Discoverable",
                "subtitle": info["discoverable"],
                "icon": "fas fa-search",
                "link": link_graph,
            }
        )

    # Suspended
    if info.get("suspended"):
        graph.append(
            {
                "name-node": "MastoSuspended",
                "title": "Suspended",
                "subtitle": "Account Suspended",
                "icon": "fas fa-ban",
                "link": link_graph,
            }
        )

    # Bio / note
    note_raw = info.get("note", "")
    profile.append({"bio": remove_tags(note_raw)})

    # Extract tasks and URLs from bio
    analyze = analize_rrss(note_raw)
    for item in analyze:
        if item == "url":
            for i in analyze["url"]:
                profile.append(i)
        if item == "tasks":
            for i in analyze["tasks"]:
                tasks.append(i)

    # Photos: avatar + header
    avatar_url = info.get("avatar", "")
    header_url = info.get("header", "")

    photos = []
    if avatar_url:
        photos.append({"picture": avatar_url, "title": "Mastodon"})
        graph.append(
            {
                "name-node": "MastodonAvatar",
                "title": "Avatar",
                "picture": avatar_url,
                "subtitle": "",
                "link": link_graph,
            }
        )

    # Add header only when it's a real image (not the default placeholder)
    if header_url and "/headers/original/missing.png" not in header_url:
        photos.append({"picture": header_url, "title": "Mastodon Header"})
        graph.append(
            {
                "name-node": "MastodonHeader",
                "title": "Header",
                "picture": header_url,
                "subtitle": "",
                "link": link_graph,
            }
        )

    if photos:
        profile.append({"photos": photos})

    # Moved account
    moved = info.get("moved")
    if moved:
        moved_url = moved.get("url", "") if isinstance(moved, dict) else str(moved)
        graph.append(
            {
                "name-node": "MastoMoved",
                "title": "Migrated to",
                "subtitle": moved_url,
                "icon": "fas fa-exchange-alt",
                "link": link_graph,
            }
        )

    # Fields (profile metadata)
    for field in info.get("fields", []):
        name = field.get("name", "")
        value = field.get("value", "")
        if not value:
            continue

        # Extract URL from HTML anchor or use plain text
        if "</" in value:
            soup = BeautifulSoup(value, "html.parser")
            a = soup.find("a")
            url = a.get("href") if a else None
        else:
            url = value

        if not url:
            continue

        fields_analyze = analize_rrss(url)
        for item in fields_analyze:
            if item == "url":
                for i in fields_analyze["url"]:
                    profile.append(i)
            if item == "tasks":
                for i in fields_analyze["tasks"]:
                    tasks.append(i)

                    fa_icon = search_icon_5(i["module"])
                    if fa_icon is None:
                        fa_icon = search_icon_5("question")

                    social.append(
                        {
                            "name-node": "MastoSocial" + name,
                            "title": name,
                            "subtitle": i["param"],
                            "icon": fa_icon,
                            "link": link_social,
                        }
                    )
                    social_profile.append(
                        {
                            "name": name,
                            "username": i["param"],
                            "Source": "Mastodon",
                            "icon": fa_icon,
                            "url": url,
                        }
                    )

    # Self social-profile entry
    social_profile.append(
        {
            "name": "mastodon",
            "username": username,
            "Source": "Mastodon",
            "icon": "fab fa-mastodon",
            "url": info.get("url", ""),
        }
    )
    profile.append({"social": social_profile})

    # Presence
    presence.append(
        {
            "name": "mastodon",
            "children": [
                {"name": "followers", "value": info.get("followers_count", 0)},
                {"name": "following", "value": info.get("following_count", 0)},
            ],
        }
    )
    profile.append({"presence": presence})

    # Timeline
    created_at = info.get("created_at", "")
    if created_at:
        timeline.append(
            {
                "action": "Mastodon: Create Account",
                "date": created_at[:10],
                "icon": "fab fa-mastodon",
            }
        )
        graph.append(
            {
                "name-node": "GraphJoin",
                "title": "Join Date",
                "subtitle": created_at[:10],
                "icon": "fas fa-calendar-check",
                "link": link_graph,
            }
        )

    last_status_at = info.get("last_status_at", "")
    if last_status_at:
        timeline.append(
            {
                "action": "Mastodon : Last toot",
                "date": last_status_at,
                "icon": "fab fa-mastodon",
            }
        )

    # Boost ratio & media count (add to graph if statuses were fetched)
    if statuses:
        graph.append(
            {
                "name-node": "MastoBoostRatio",
                "title": "Boost Ratio",
                "subtitle": f"{analytics['boost_ratio'] * 100:.1f}%",
                "icon": "fas fa-retweet",
                "link": link_graph,
            }
        )
        if analytics["media_count"]:
            graph.append(
                {
                    "name-node": "MastoMedia",
                    "title": "Media Attachments",
                    "subtitle": analytics["media_count"],
                    "icon": "fas fa-photo-video",
                    "link": link_graph,
                }
            )

    # Featured tags → graph nodes
    for ftag in featured_tags:
        graph.append(
            {
                "name-node": f"MastoTag_{ftag['name']}",
                "title": f"#{ftag['name']}",
                "subtitle": ftag["statuses_count"],
                "icon": "fas fa-hashtag",
                "link": link_graph,
            }
        )

    # ---- Raw node -------------------------------------------------------
    raw_node = {
        **info,
        "_statuses": statuses,
        "_statuses_count_fetched": len(statuses),
        "_featured_tags": featured_tags,
        "_analytics": analytics,
    }

    # ---- Toot list (formatted for frontend) -----------------------------
    toot_list = [
        {
            "content": remove_tags(s.get("content", "")),
            "date": s.get("created_at", "")[:19],
            "url": s.get("url", ""),
            "reblogs_count": s.get("reblogs_count", 0),
            "favourites_count": s.get("favourites_count", 0),
        }
        for s in statuses
    ]

    # ---- Graphic array --------------------------------------------------
    _originals = analytics["originals"]
    _boosts = len(statuses) - _originals

    graphic = [
        {"user": graph},
        {"social": social},
        {"list": toot_list},
        {"hour": analytics["hour_chart"]},
        {"week": analytics["week_chart"]},
        {"hashtags": analytics["hashtag_bubble"]},
        # --- Ratio / relationship cards (indices 6-10) ---
        {
            "popularity": [
                {"title": "Followers", "value": info.get("followers_count", 0)},
                {"title": "Following", "value": info.get("following_count", 0)},
            ]
        },
        {
            "approval": [
                {"title": "Toots", "value": info.get("statuses_count", 0)},
                {"title": "Likes", "value": analytics["total_favourites"]},
            ]
        },
        {
            "tootvboost": [
                {"title": "Original", "value": _originals},
                {"title": "Boosts", "value": _boosts},
            ]
        },
        {
            "resume": {
                "children": [
                    {"name": "Followers", "value": info.get("followers_count", 0)},
                    {"name": "Following", "value": info.get("following_count", 0)},
                    {"name": "Toots", "value": _originals},
                    {"name": "Boosts", "value": _boosts},
                ]
            }
        },
        {"engagement": analytics["engagement_series"]},
    ]

    return [
        {"module": "mastodon"},
        {"param": username},
        {"validation": "no"},
        {"raw": raw_node},
        {"graphic": graphic},
        {"profile": profile},
        {"timeline": timeline},
        {"tasks": tasks},
    ]


# ---------------------------------------------------------------------------
# Main task
# ---------------------------------------------------------------------------


@iky_task(module_name="mastodon", dev_mode_sleep=15)
def p_mastodon(username: str) -> list[dict]:
    """Fetch and assemble Mastodon OSINT data for *username*.

    Returns an 8-element list:
        [module, param, validation, raw, graphic, profile, timeline, tasks]
    """
    # Parse input
    user, server = _parse_username(username)

    session = _make_session()

    # Resolve account
    resolved = _resolve_account(session, user, server)

    # Multiple matches → several_user flow
    if isinstance(resolved, list):
        return _several_user(username, resolved)

    # Single account
    info = resolved

    # Determine the authoritative server for subsequent API calls.
    # Always derive from the resolved account's URL — this handles the
    # multi-instance fallback case where lookup fails on `server` and search
    # resolves the account on a DIFFERENT instance.
    resolved_server = _extract_server_from_url(info.get("url", ""))

    account_id = str(info["id"])

    # Enrichment (non-fatal)
    statuses = _fetch_statuses(session, account_id, resolved_server)
    featured_tags = _fetch_featured_tags(session, account_id, resolved_server)
    analytics = _compute_analytics(statuses)

    return _one_user(username, info, statuses, featured_tags, analytics)


# Backward-compatible alias: module_registry references t_mastodon
t_mastodon = p_mastodon


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def output(data: list) -> None:
    """Print JSON to stdout."""
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Query Mastodon OSINT data for a username"
    )
    parser.add_argument(
        "username",
        help="Mastodon username (e.g. gargron, user@mastodon.social)",
    )
    args = parser.parse_args()

    result = t_mastodon(args.username)
    output(result)
