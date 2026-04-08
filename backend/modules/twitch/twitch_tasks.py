#!/usr/bin/env python

import argparse
import json
import re
from collections import Counter
from datetime import datetime
from typing import Any

import requests
import twitch
from celery.utils.log import get_task_logger
from factories.configuration import api_keys_search
from factories.task_wrapper import iky_task

logger = get_task_logger(__name__)


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def _parse_duration(duration_str: str) -> int:
    """Parse Twitch video duration string '1h2m3s' → seconds.

    Replaces the ``parse`` library dependency with stdlib ``re``.
    Handles any combination of h/m/s components.
    """
    match = re.match(r"(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?$", duration_str or "")
    if not match or not any(match.groups()):
        return 0
    h, m, s = (int(g) if g else 0 for g in match.groups())
    return h * 3600 + m * 60 + s


def _build_hourset(hours: list[str]) -> list[dict[str, Any]]:
    """Build a 24-slot hour distribution from a list of hour strings ('00'-'23')."""
    counter = Counter(hours)
    hour_names = [f"{h:02d}" for h in range(24)]
    return [{"name": name, "value": counter.get(name, 0)} for name in hour_names]


def _build_weekset(days: list[str]) -> list[dict[str, Any]]:
    """Build a 7-slot weekday distribution, correctly aligning names to counts.

    Fixes the original index-based bug where missing weekdays caused
    misalignment between Counter positions and day names.
    """
    counter = Counter(days)
    weekdays = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]
    return [{"name": day, "value": counter.get(day, 0)} for day in weekdays]


def _helix_get(
    api: Any,
    endpoint: str,
    params: dict[str, str],
    default: Any = None,
) -> Any:
    """GET a Helix API endpoint, returning data or *default* on any failure.

    Uses ``api.get()`` which injects Client-ID and Authorization headers
    automatically via ``self._headers()``.  On success it returns a dict with
    a ``"data"`` key.  On failure, we log a warning and return the provided
    default so other enrichment is unaffected.
    """
    try:
        resp = api.get(endpoint, params=params)
        if isinstance(resp, dict):
            return resp.get("data", default)
        return resp
    except (KeyError, TypeError, AttributeError, ValueError, RuntimeError) as exc:
        logger.warning(f"Twitch enrichment failed [{endpoint}]: {exc}")
        return default
    except Exception as exc:
        # Catch library-specific exceptions (e.g. requests.RequestException,
        # twitch.helix APIException) that are not importable at module level.
        logger.warning(f"Twitch enrichment failed [{endpoint}]: {exc}")
        return default


def _http_get(
    url: str,
    *,
    headers: dict[str, str] | None = None,
    timeout: int = 10,
    default: Any = None,
) -> Any:
    """HTTP GET returning parsed JSON, or *default* on any failure.

    Follows the same try/except + logger.warning pattern as ``_helix_get``
    but uses ``requests`` directly for non-Helix external sources.
    """
    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning(f"Twitch HTTP fetch failed [{url}]: {exc}")
        return default


def _http_post(
    url: str,
    *,
    json_body: Any = None,
    headers: dict[str, str] | None = None,
    timeout: int = 10,
    default: Any = None,
) -> Any:
    """HTTP POST returning parsed JSON, or *default* on any failure.

    Follows the same try/except + logger.warning pattern as ``_http_get``
    but uses ``requests.post`` and sends a JSON body.
    """
    try:
        resp = requests.post(url, json=json_body, headers=headers, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning(f"Twitch HTTP POST failed [{url}]: {exc}")
        return default


def _fetch_panels_gql(username: str) -> list[dict]:
    """Fetch channel panels via Twitch GQL API."""
    url = "https://gql.twitch.tv/gql"
    headers = {
        "Client-ID": "kimne78kx3ncx6brgo4mv6wki5h1ko",
        "Content-Type": "application/json",
    }
    query = {
        "query": """query ChannelPanels($login: String!) {
            user(login: $login) {
                panels {
                    id type __typename
                    ... on DefaultPanel { title imageURL linkURL description }
                }
            }
        }""",
        "variables": {"login": username},
    }
    data = _http_post(url, json_body=query, headers=headers, timeout=10, default=None)
    if not data or not isinstance(data, dict):
        return []
    user = (data.get("data") or {}).get("user") or {}
    panels = user.get("panels") or []
    return [p for p in panels if isinstance(p, dict)]


# Compiled regex dict for panel URL classification.
# Order matters for display but not correctness — each platform checked
# independently so a URL can only match one pattern (first-write wins).
_PLATFORM_PATTERNS: dict[str, re.Pattern] = {
    "twitter": re.compile(r"https?://(?:www\.)?(?:twitter\.com|x\.com)/\w+", re.I),
    "youtube": re.compile(
        r"https?://(?:www\.)?youtube\.com/(?:c/|channel/|@)[\w-]+", re.I
    ),
    "discord": re.compile(r"https?://(?:www\.)?discord\.(?:gg|com/invite)/\w+", re.I),
    "instagram": re.compile(r"https?://(?:www\.)?instagram\.com/\w+", re.I),
    "tiktok": re.compile(r"https?://(?:www\.)?tiktok\.com/@\w+", re.I),
    "patreon": re.compile(r"https?://(?:www\.)?patreon\.com/\w+", re.I),
    "kofi": re.compile(r"https?://(?:www\.)?ko-fi\.com/\w+", re.I),
    "github": re.compile(r"https?://(?:www\.)?github\.com/\w+", re.I),
    "reddit": re.compile(r"https?://(?:www\.)?reddit\.com/(?:r|u|user)/\w+", re.I),
    "steam": re.compile(
        r"https?://(?:www\.)?steamcommunity\.com/(?:id|profiles)/\w+", re.I
    ),
    "facebook": re.compile(r"https?://(?:www\.)?facebook\.com/\w+", re.I),
}

# Social icon mapping for panel URL platforms
_PLATFORM_ICONS: dict[str, str] = {
    "twitter": "fab fa-twitter",
    "youtube": "fab fa-youtube",
    "discord": "fab fa-discord",
    "instagram": "fab fa-instagram",
    "tiktok": "fab fa-tiktok",
    "patreon": "fab fa-patreon",
    "kofi": "fas fa-coffee",
    "github": "fab fa-github",
    "reddit": "fab fa-reddit",
    "steam": "fab fa-steam",
    "facebook": "fab fa-facebook",
}


def _extract_panel_urls(panels: list[dict]) -> dict[str, list[str]]:
    """Extract and classify URLs from Twitch channel panels.

    Scans each panel's description and link fields for known-platform URLs
    using ``_PLATFORM_PATTERNS``.  Supports both Kraken field names
    (``html_description``, ``data.link``) and GQL field names
    (``description``, ``linkURL``).  Returns ``{platform: [url, ...]}``
    dict; duplicate URLs within the same platform are silently dropped.
    """
    results: dict[str, list[str]] = {}
    for panel in panels:
        if not isinstance(panel, dict):
            continue
        # Support both Kraken (html_description) and GQL (description) field names
        html_desc = panel.get("description") or panel.get("html_description") or ""
        # Support both Kraken (data.link) and GQL (linkURL) field names
        data = panel.get("data")
        kraken_link = (data.get("link") or "") if isinstance(data, dict) else ""
        gql_link = panel.get("linkURL") or ""
        combined = f"{html_desc} {kraken_link} {gql_link}"
        for platform, pattern in _PLATFORM_PATTERNS.items():
            for match in pattern.finditer(combined):
                url = match.group(0)
                seen = results.setdefault(platform, [])
                if url not in seen:
                    seen.append(url)
    return results


# ---------------------------------------------------------------------------
# Main task
# ---------------------------------------------------------------------------


@iky_task(module_name="twitch", dev_mode_sleep=15)
def p_twitch(username: str) -> list[dict[str, Any]]:
    """Gather Twitch profile, video stats, and Helix enrichment data.

    When Twitch API keys are absent, Helix-dependent code is skipped but
    public sources (TwitchTracker) are still queried so partial data is
    returned instead of nothing.
    """

    # -----------------------------------------------------------------------
    # Auth check — determine which code paths are available
    # -----------------------------------------------------------------------
    client_id = api_keys_search("twitch_client_id")
    client_secret = api_keys_search("twitch_client_secret")
    has_helix = bool(client_id and client_secret)

    # -----------------------------------------------------------------------
    # Shared setup (used by both paths)
    # -----------------------------------------------------------------------
    link = "Twitch"
    link_social = f"https://twitch.tv/{username}"

    gather: list[dict] = []
    profile: list[dict] = []
    social: list[dict] = []
    presence: list[dict] = []
    timeline: list[dict] = []

    # Base gather node — always present
    gather.append(
        {
            "name-node": "Twitch",
            "title": "Twitch",
            "subtitle": "",
            "icon": "fab fa-twitch",
            "link": link_social,
        }
    )

    # Social link — always present
    social.append(
        {
            "name": "Twitch",
            "url": link_social,
            "icon": "fab fa-twitch",
            "source": "Twitch",
            "username": username,
        }
    )

    # Default video-related outputs (overridden when has_helix is True)
    qty_video = 0
    table: list[dict] = []
    duration: list[dict] = []
    thumbnail: list[dict] = [
        {
            "name-node": "Twitch",
            "title": "Twitch",
            "subtitle": "",
            "icon": "fab fa-twitch",
            "link": link,
        }
    ]
    hours: list[str] = []
    days: list[str] = []
    t_timeline: list[dict] = []
    clips: list[dict] = []
    qty_followers = 0
    qty_followed = 0

    # -----------------------------------------------------------------------
    # Helix path — only when API keys are present
    # -----------------------------------------------------------------------
    if has_helix:
        helix = twitch.Helix(client_id, client_secret)
        user = helix.user(username)

        # -------------------------------------------------------------------
        # Videos — table, duration, thumbnail, hours, days, timeline
        # -------------------------------------------------------------------
        prev_day = "0000-00-00"
        time_value = 1

        try:
            for qty_video, (video, _comments) in enumerate(
                helix.user(username).videos().comments, start=1
            ):
                created_at = datetime.strptime(video.created_at, "%Y-%m-%dT%H:%M:%SZ")

                table.append(
                    {
                        "title": video.title,
                        "description": video.description,
                        "created": created_at.strftime("%Y-%m-%d %H:%M"),
                        "url": video.url,
                        "view_count": getattr(video, "view_count", 0) or 0,
                    }
                )

                duration.append(
                    {
                        "value": _parse_duration(video.duration),
                        "name": video.duration,
                    }
                )

                thumbnail.append(
                    {
                        "name-node": f"Twitch{qty_video}",
                        "title": f"Video {qty_video}",
                        "picture": video.thumbnail_url.replace(
                            "%{width}", "300"
                        ).replace("%{height}", "300"),
                        "subtitle": "",
                        "link": link,
                    }
                )

                hours.append(created_at.strftime("%H"))
                days.append(created_at.strftime("%A"))

                twitch_date = created_at.strftime("%Y-%m-%dT%H:%M:%S.009Z")
                twitch_day = created_at.strftime("%Y-%m-%d")
                if prev_day == twitch_day:
                    time_value += 1
                else:
                    t_timeline.append({"name": twitch_date, "value": time_value})
                    time_value = 1
                    prev_day = twitch_day
        except (KeyError, TypeError, AttributeError) as exc:
            logger.warning(f"Twitch video enumeration error: {exc}")

        # -------------------------------------------------------------------
        # Followers / following — use total field only (API change Feb 2023)
        # NOTE: /helix/users/follows was deprecated Feb 2023 and fully removed.
        # The twitch-python library still calls it; we catch the 410 Gone here.
        # -------------------------------------------------------------------
        try:
            followers_resp = helix.user(username).followers()
            qty_followers = getattr(followers_resp, "total", 0) or 0
        except requests.exceptions.HTTPError as exc:
            logger.warning(
                f"Twitch followers/following API returned 410 Gone"
                f" - endpoint deprecated: {exc}"
            )
        except (KeyError, TypeError, AttributeError, Exception) as exc:
            logger.warning(f"Twitch followers error: {exc}")

        try:
            following_resp = helix.user(username).following()
            qty_followed = getattr(following_resp, "total", 0) or 0
        except requests.exceptions.HTTPError as exc:
            logger.warning(
                f"Twitch followers/following API returned 410 Gone"
                f" - endpoint deprecated: {exc}"
            )
        except (KeyError, TypeError, AttributeError, Exception) as exc:
            logger.warning(f"Twitch following error: {exc}")

        # -------------------------------------------------------------------
        # Profile gather nodes from Helix user object
        # -------------------------------------------------------------------
        try:
            gather.append(
                {
                    "name-node": "TwitchName",
                    "title": "Name",
                    "subtitle": user.display_name,
                    "icon": "fas fa-signature",
                    "link": link_social,
                }
            )
            profile.append({"name": user.display_name})
        except (KeyError, TypeError, AttributeError) as exc:
            raise Exception("iKy - User not FOUND") from exc

        gather.append(
            {
                "name-node": "TwitchUserName",
                "title": "Username",
                "subtitle": username,
                "icon": "fas fa-user-circle",
                "link": link_social,
            }
        )
        profile.append({"username": username})

        gather.append(
            {
                "name-node": "TwitchUserID",
                "title": "User ID",
                "subtitle": user.id,
                "icon": "fas fa-id-badge",
                "link": link_social,
            }
        )

        try:
            pic = user.profile_image_url
            gather.append(
                {
                    "name-node": "TwitchPhoto",
                    "title": "Avatar",
                    "subtitle": "",
                    "picture": pic,
                    "link": link_social,
                }
            )
            profile.append(
                {
                    "photos": [
                        {
                            "name-node": "Twitch",
                            "title": "Twitch",
                            "subtitle": "",
                            "picture": pic,
                            "link": "Photos",
                        }
                    ]
                }
            )
        except (KeyError, TypeError, AttributeError) as exc:
            logger.warning(f"Twitch avatar error: {exc}")

        gather.append(
            {
                "name-node": "TwitchVideos",
                "title": "Videos",
                "subtitle": qty_video,
                "icon": "fas fa-photo-video",
                "link": link_social,
            }
        )

        gather.append(
            {
                "name-node": "TwitchViews",
                "title": "Views",
                "subtitle": user.view_count,
                "icon": "fas fa-eye",
                "link": link_social,
            }
        )

        gather.append(
            {
                "name-node": "TwitchFollowers",
                "title": "Followers",
                "subtitle": qty_followers,
                "icon": "fas fa-users",
                "link": link_social,
            }
        )

        gather.append(
            {
                "name-node": "TwitchFollowing",
                "title": "Following",
                "subtitle": qty_followed,
                "icon": "fas fa-users",
                "link": link_social,
            }
        )

        if user.email:
            gather.append(
                {
                    "name-node": "TwitchEmail",
                    "title": "Email",
                    "subtitle": user.email,
                    "icon": "fas fa-at",
                    "link": link_social,
                }
            )

        try:
            if user.created_at:
                created_dt = datetime.strptime(user.created_at, "%Y-%m-%dT%H:%M:%S.%fZ")
                gather.append(
                    {
                        "name-node": "TwitchCreate",
                        "title": "Created",
                        "subtitle": created_dt.strftime("%Y-%m-%d"),
                        "icon": "fas fa-calendar-check",
                        "link": link_social,
                    }
                )
                timeline.append(
                    {
                        "date": created_dt.strftime("%Y-%m-%d"),
                        "action": "Twitch : Create Account",
                        "icon": "fa-twitch",
                    }
                )
        except (KeyError, TypeError, AttributeError, ValueError) as exc:
            logger.warning(f"Twitch account creation date error: {exc}")

        profile.append({"social": social})

        if user.description:
            profile.append({"bio": user.description})

        presence.append(
            {
                "name": "twitch",
                "children": [
                    {"name": "followers", "value": qty_followers},
                    {"name": "following", "value": qty_followed},
                ],
            }
        )
        profile.append({"presence": presence})

        # -------------------------------------------------------------------
        # Phase 2: Helix Enrichment (each endpoint degrades independently)
        # -------------------------------------------------------------------
        user_id = str(user.id)

        # Channel info — game, tags, language
        channel_data = _helix_get(
            helix.api,
            "channels",
            {"broadcaster_id": user_id},
            default=[],
        )
        if channel_data and isinstance(channel_data, list) and len(channel_data) > 0:
            ch = channel_data[0]
            if ch.get("game_name"):
                gather.append(
                    {
                        "name-node": "TwitchGame",
                        "title": "Game",
                        "subtitle": ch["game_name"],
                        "icon": "fas fa-gamepad",
                        "link": link_social,
                    }
                )
            if ch.get("broadcaster_language"):
                gather.append(
                    {
                        "name-node": "TwitchLanguage",
                        "title": "Language",
                        "subtitle": ch["broadcaster_language"],
                        "icon": "fas fa-language",
                        "link": link_social,
                    }
                )
            if ch.get("tags"):
                gather.append(
                    {
                        "name-node": "TwitchTags",
                        "title": "Tags",
                        "subtitle": ", ".join(ch["tags"]),
                        "icon": "fas fa-tags",
                        "link": link_social,
                    }
                )
            # Batch A: content_classification_labels (A1)
            labels = ch.get("content_classification_labels") or []
            if labels:
                gather.append(
                    {
                        "name-node": "TwitchContentLabels",
                        "title": "Content Labels",
                        "subtitle": ", ".join(labels),
                        "icon": "fas fa-exclamation-triangle",
                        "link": link_social,
                    }
                )
            # Batch A: broadcaster_type from channel response (A2)
            broadcaster_type = ch.get("broadcaster_type")
            if not isinstance(broadcaster_type, str) or not broadcaster_type:
                # Fall back to user object field
                raw_bt = getattr(user, "broadcaster_type", None)
                broadcaster_type = raw_bt if isinstance(raw_bt, str) and raw_bt else ""
            gather.append(
                {
                    "name-node": "TwitchBroadcasterType",
                    "title": "Broadcaster",
                    "subtitle": broadcaster_type if broadcaster_type else "none",
                    "icon": "fas fa-broadcast-tower",
                    "link": link_social,
                }
            )
        else:
            # No channel data: still emit broadcaster_type from user object (A2)
            raw_bt = getattr(user, "broadcaster_type", None)
            broadcaster_type = raw_bt if isinstance(raw_bt, str) and raw_bt else ""
            gather.append(
                {
                    "name-node": "TwitchBroadcasterType",
                    "title": "Broadcaster",
                    "subtitle": broadcaster_type if broadcaster_type else "none",
                    "icon": "fas fa-broadcast-tower",
                    "link": link_social,
                }
            )

        # A2: broadcaster_type profile field (spec requirement)
        profile.append(
            {"broadcaster_type": broadcaster_type if broadcaster_type else "none"}
        )

        # Live status — streams endpoint
        stream_data = _helix_get(
            helix.api,
            "streams",
            {"user_id": user_id},
            default=[],
        )
        if stream_data and isinstance(stream_data, list) and len(stream_data) > 0:
            stream = stream_data[0]
            gather.append(
                {
                    "name-node": "TwitchLive",
                    "title": "Live",
                    "subtitle": stream.get("game_name", ""),
                    "icon": "fas fa-broadcast-tower",
                    "link": link_social,
                }
            )
            gather.append(
                {
                    "name-node": "TwitchViewers",
                    "title": "Viewers",
                    "subtitle": stream.get("viewer_count", 0),
                    "icon": "fas fa-eye",
                    "link": link_social,
                }
            )
        else:
            gather.append(
                {
                    "name-node": "TwitchLive",
                    "title": "Live",
                    "subtitle": "Offline",
                    "icon": "fas fa-broadcast-tower",
                    "link": link_social,
                }
            )

        # Teams
        teams_data = _helix_get(
            helix.api,
            "teams/channel",
            {"broadcaster_id": user_id},
            default=[],
        )
        if teams_data and isinstance(teams_data, list):
            for team in teams_data:
                if team.get("team_name"):
                    gather.append(
                        {
                            "name-node": f"TwitchTeam_{team['team_name']}",
                            "title": "Team",
                            "subtitle": team.get(
                                "team_display_name", team["team_name"]
                            ),
                            "icon": "fas fa-users-cog",
                            "link": link_social,
                        }
                    )

        # Emotes count
        emotes_data = _helix_get(
            helix.api,
            "chat/emotes",
            {"broadcaster_id": user_id},
            default=[],
        )
        if emotes_data and isinstance(emotes_data, list):
            gather.append(
                {
                    "name-node": "TwitchEmotes",
                    "title": "Emotes",
                    "subtitle": len(emotes_data),
                    "icon": "fas fa-smile",
                    "link": link_social,
                }
            )

        # Schedule — next stream events into timeline
        schedule_data = _helix_get(
            helix.api,
            "schedule",
            {"broadcaster_id": user_id},
            default=None,
        )
        if schedule_data and isinstance(schedule_data, dict):
            segments = schedule_data.get("segments") or []
            for seg in segments[:5]:
                start = seg.get("start_time", "")
                if start:
                    timeline.append(
                        {
                            "date": start[:10],
                            "action": (
                                f"Twitch : Scheduled Stream — {seg.get('title', '')}"
                            ),
                            "icon": "fa-twitch",
                        }
                    )

        # -------------------------------------------------------------------
        # Clips — top 20 by view count → graphic.clips
        # -------------------------------------------------------------------
        clips_data = _helix_get(
            helix.api,
            "clips",
            {"broadcaster_id": user_id, "first": "20"},
            default=[],
        )
        if clips_data and isinstance(clips_data, list):
            sorted_clips = sorted(
                clips_data, key=lambda c: c.get("view_count", 0), reverse=True
            )[:20]
            clips = [
                {
                    "title": c.get("title", ""),
                    "view_count": c.get("view_count", 0),
                    "creator_name": c.get("creator_name", ""),
                    "url": c.get("url", ""),
                }
                for c in sorted_clips
            ]

        # -------------------------------------------------------------------
        # Batch B: New Helix enrichment (each endpoint degrades independently)
        # -------------------------------------------------------------------

        # B4: Chat settings — subscriber-only, follower-mode, slow-mode, emote-only
        chat_settings = _helix_get(
            helix.api,
            "chat/settings",
            {"broadcaster_id": user_id},
            default=None,
        )
        if chat_settings and isinstance(chat_settings, list) and len(chat_settings) > 0:
            cs = chat_settings[0]
            if cs.get("subscriber_mode"):
                gather.append(
                    {
                        "name-node": "TwitchSubOnly",
                        "title": "Sub-Only Chat",
                        "subtitle": "Yes",
                        "icon": "fas fa-lock",
                        "link": link_social,
                    }
                )
            if cs.get("follower_mode"):
                gather.append(
                    {
                        "name-node": "TwitchFollowerMode",
                        "title": "Follower Mode",
                        "subtitle": "Yes",
                        "icon": "fas fa-user-check",
                        "link": link_social,
                    }
                )
            if cs.get("slow_mode"):
                gather.append(
                    {
                        "name-node": "TwitchSlowMode",
                        "title": "Slow Mode",
                        "subtitle": "Yes",
                        "icon": "fas fa-clock",
                        "link": link_social,
                    }
                )
            if cs.get("emote_mode"):
                gather.append(
                    {
                        "name-node": "TwitchEmoteMode",
                        "title": "Emote-Only Chat",
                        "subtitle": "Yes",
                        "icon": "fas fa-smile",
                        "link": link_social,
                    }
                )

        # B5: Channel sub badges — tier count
        badges_data = _helix_get(
            helix.api,
            "chat/badges",
            {"broadcaster_id": user_id},
            default=[],
        )
        if badges_data and isinstance(badges_data, list):
            sub_badge_sets = [b for b in badges_data if b.get("set_id") == "subscriber"]
            tier_count = (
                len(sub_badge_sets[0].get("versions", [])) if sub_badge_sets else 0
            )
            if tier_count > 0:
                gather.append(
                    {
                        "name-node": "TwitchSubBadgeTiers",
                        "title": "Sub Badge Tiers",
                        "subtitle": tier_count,
                        "icon": "fas fa-medal",
                        "link": link_social,
                    }
                )

        # B6: User extensions
        extensions_data = _helix_get(
            helix.api,
            "users/extensions",
            {"user_id": user_id},
            default=None,
        )
        if extensions_data and isinstance(extensions_data, dict):
            ext_names: list[str] = []
            for _slot_type, slots in extensions_data.items():
                if isinstance(slots, dict):
                    for _slot_id, ext in slots.items():
                        if (
                            isinstance(ext, dict)
                            and ext.get("active")
                            and ext.get("name")
                        ):
                            ext_names.append(ext["name"])
            if ext_names:
                gather.append(
                    {
                        "name-node": "TwitchExtensions",
                        "title": "Extensions",
                        "subtitle": ", ".join(sorted(set(ext_names))),
                        "icon": "fas fa-puzzle-piece",
                        "link": link_social,
                    }
                )

        # B7: Creator goals — REMOVED
        # Requires channel:read:goals user OAuth token scope, which is not
        # available for passive OSINT (requires the channel owner to authorize).

        # B8: Charity campaigns — REMOVED
        # Requires channel:read:charity user OAuth token scope, which is not
        # available for passive OSINT (requires the channel owner to authorize).

    else:
        # -------------------------------------------------------------------
        # No-key path — minimal profile from username alone
        # -------------------------------------------------------------------
        logger.warning(
            "Twitch API keys not configured — skipping Helix, "
            "fetching public sources only"
        )
        gather.append(
            {
                "name-node": "TwitchUserName",
                "title": "Username",
                "subtitle": username,
                "icon": "fas fa-user-circle",
                "link": link_social,
            }
        )
        profile.append({"username": username})
        profile.append({"social": social})
        presence.append(
            {
                "name": "twitch",
                "children": [
                    {"name": "followers", "value": qty_followers},
                    {"name": "following", "value": qty_followed},
                ],
            }
        )
        profile.append({"presence": presence})

    # -----------------------------------------------------------------------
    # Batch C: External enrichment via _http_get (runs for BOTH key paths)
    # -----------------------------------------------------------------------

    # C9: TwitchTracker summary stats
    tt_url = f"https://twitchtracker.com/api/channels/summary/{username}"
    tt_headers = {
        "User-Agent": "Mozilla/5.0 (compatible; iKy-OSINT/1.0)",
        "Referer": f"https://twitchtracker.com/{username}",
    }
    tt_data = _http_get(tt_url, headers=tt_headers, timeout=10, default=None)
    if tt_data and isinstance(tt_data, dict):
        tt_fields = {
            "rank": ("TT Rank", "fas fa-trophy"),
            "avg_viewers": ("TT Avg Viewers", "fas fa-eye"),
            "max_viewers": ("TT Peak Viewers", "fas fa-eye"),
            "hours_watched": ("TT Hours Watched", "fas fa-clock"),
            "followers": ("TT Followers", "fas fa-users"),
            "following": ("TT Following", "fas fa-user-plus"),
        }
        for field, (title, icon) in tt_fields.items():
            val = tt_data.get(field)
            if val is not None:
                gather.append(
                    {
                        "name-node": f"TwitchTracker_{field}",
                        "title": title,
                        "subtitle": val,
                        "icon": icon,
                        "link": link_social,
                    }
                )

        # Override qty_followers / qty_following with TwitchTracker values when
        # the Helix endpoint is dead (410 Gone) or keys are absent — update the
        # already-appended gather nodes and presence in-place so existing output
        # nodes reflect real counts instead of 0.
        tt_followers = tt_data.get("followers")
        tt_following = tt_data.get("following")
        if tt_followers is not None and qty_followers == 0:
            qty_followers = tt_followers
            for node in gather:
                if node.get("name-node") == "TwitchFollowers":
                    node["subtitle"] = qty_followers
            for entry in presence:
                if entry.get("name") == "twitch":
                    for child in entry.get("children", []):
                        if child.get("name") == "followers":
                            child["value"] = qty_followers
        if tt_following is not None and qty_followed == 0:
            qty_followed = tt_following
            for node in gather:
                if node.get("name-node") == "TwitchFollowing":
                    node["subtitle"] = qty_followed
            for entry in presence:
                if entry.get("name") == "twitch":
                    for child in entry.get("children", []):
                        if child.get("name") == "following":
                            child["value"] = qty_followed

    # C10: Channel panels — social links via GQL
    panels_raw = _fetch_panels_gql(username)
    if panels_raw:
        panel_urls = _extract_panel_urls(panels_raw)
        # Collect existing social URLs to avoid duplicates
        existing_social_urls = {s.get("url", "") for s in social}
        for platform, urls in panel_urls.items():
            icon = _PLATFORM_ICONS.get(platform, "fas fa-link")
            for url in urls:
                if url not in existing_social_urls:
                    social.append(
                        {
                            "name": platform.capitalize(),
                            "url": url,
                            "icon": icon,
                            "source": "TwitchPanel",
                            "username": username,
                        }
                    )
                    existing_social_urls.add(url)

    # C11: Steam ID from legacy Kraken API — REMOVED
    # The Kraken API endpoint api.twitch.tv/api/channels/{name} was shut down
    # in February 2022.  Calls to it return 410 Gone.

    # -----------------------------------------------------------------------
    # Assemble final 7-key output
    # -----------------------------------------------------------------------
    hourset = _build_hourset(hours)
    weekset = _build_weekset(days)

    raw_node_total = [{"status": "Ok", "code": 0}]

    graphic: list[dict] = [
        {"social": gather},
        {"table": table},
        {"duration": duration},
        {"thumbnail": thumbnail},
        {"week": weekset},
        {"hour": hourset},
        {"time": t_timeline},
        {"clips": clips},
    ]

    total: list[dict] = [
        {"module": "twitch"},
        {"param": username},
        {"validation": "no"},
        {"raw": raw_node_total},
        {"graphic": graphic},
        {"profile": profile},
        {"timeline": timeline},
    ]

    return total


# Backward-compatible alias: existing code references t_twitch
t_twitch = p_twitch


def output(data: list) -> None:
    """Print JSON dump."""
    print(json.dumps(data, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Query Twitch for a username")
    parser.add_argument("username", help="Twitch username to look up")
    args = parser.parse_args()

    result = t_twitch(args.username)
    output(result)
