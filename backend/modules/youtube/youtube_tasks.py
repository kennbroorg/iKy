#!/usr/bin/env python

import argparse
import json
import re
from collections import Counter

from celery.utils.log import get_task_logger
from factories.configuration import api_keys_search
from factories.task_wrapper import iky_task
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from youtube_transcript_api import (
    IpBlocked,
    NoTranscriptFound,
    RequestBlocked,
    TranscriptsDisabled,
    VideoUnavailable,
    YouTubeTranscriptApi,
)

logger = get_task_logger(__name__)

_CHANNELS_PART = "snippet,statistics,contentDetails,topicDetails"
_VIDEOS_PART = "snippet,statistics,contentDetails,topicDetails,status"
_LINK = "Youtube"
_ICON = "fab fa-youtube"
_CHANNEL_ID_RE = re.compile(r"^UC[\w-]{22}$")
_URL_RE = re.compile(r"https?://[^\s)>\]\"']+", re.IGNORECASE)
_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_HASHTAG_RE = re.compile(r"#(\w+)")
_DOMAIN_RE = re.compile(r"https?://(?:www\.)?([^/]+)", re.IGNORECASE)

try:
    from stop_words import get_stop_words

    _STOP_WORDS = set(get_stop_words("english"))
except Exception:  # pragma: no cover - fallback if stop_words API drifts
    _STOP_WORDS = set()


# ---------------------------------------------------------------------------
# Input handling (Req 1)
# ---------------------------------------------------------------------------


def _parse_handle(raw: str) -> str:
    """Normalize a channel input into a bare handle or channel id.

    Accepts ``@handle``, bare ``handle``, ``youtube.com/@handle`` and
    ``youtube.com/channel/UC...``. Rejects empty/whitespace input and any
    video URL form (``watch?v=``, ``/shorts/``, ``/embed/``).
    """
    text = (raw or "").strip()
    if not text:
        raise Exception("iKy - Invalid YouTube channel/handle")

    lowered = text.lower()
    for bad in ("watch?v=", "/shorts/", "/embed/"):
        if bad in lowered:
            raise Exception("iKy - Invalid YouTube channel/handle")

    text = re.sub(r"^https?://", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^(?:www\.|m\.)?youtube\.com/", "", text, flags=re.IGNORECASE)
    text = text.strip("/")

    channel_id = re.match(r"^channel/(UC[\w-]{22})$", text, flags=re.IGNORECASE)
    if channel_id:
        return channel_id.group(1)

    prefixed = re.match(r"^(?:c|user)/(.+)$", text, flags=re.IGNORECASE)
    if prefixed:
        text = prefixed.group(1)

    if text.startswith("@"):
        text = text[1:]

    if not text or "/" in text or " " in text:
        raise Exception("iKy - Invalid YouTube channel/handle")

    return text


# ---------------------------------------------------------------------------
# Channel resolution (Req 2, 11)
# ---------------------------------------------------------------------------


def _resolve_channel(youtube, handle: str) -> dict | None:
    """Resolve a channel via forHandle, then forUsername (never search.list).

    A channel id (``UC...``) is resolved directly through ``id=``. Returns the
    first matching channel resource, or ``None`` when nothing matches. HTTP and
    network failures are mapped to ``iKy - ...`` warning exceptions.
    """
    try:
        if _CHANNEL_ID_RE.match(handle):
            items = (
                youtube.channels()
                .list(part=_CHANNELS_PART, id=handle)
                .execute()
                .get("items", [])
            )
            if items:
                return items[0]

        items = (
            youtube.channels()
            .list(part=_CHANNELS_PART, forHandle=handle)
            .execute()
            .get("items", [])
        )
        if not items:
            items = (
                youtube.channels()
                .list(part=_CHANNELS_PART, forUsername=handle)
                .execute()
                .get("items", [])
            )
        return items[0] if items else None
    except HttpError as exc:
        status = getattr(exc, "status_code", None) or getattr(exc.resp, "status", None)
        if status == 403:
            raise Exception(
                "iKy - YouTube API quota exceeded or access forbidden"
            ) from exc
        if status == 404:
            raise Exception("iKy - Channel not found") from exc
        raise Exception("iKy - YouTube API error") from exc
    except Exception as exc:
        if str(exc).startswith("iKy - "):
            raise
        raise Exception("iKy - Network error") from exc


# ---------------------------------------------------------------------------
# Videos, comments, transcripts (Req 4, 5, 6)
# ---------------------------------------------------------------------------


def _fetch_videos(youtube, uploads_playlist_id: str) -> list[dict]:
    """Fetch up to the latest 10 uploads for a channel's uploads playlist.

    Reads video ids from ``playlistItems.list`` then hydrates them with a
    single batched ``videos.list`` call. Returns whatever videos exist (no
    error when the channel has fewer than 10 uploads).
    """
    items = (
        youtube.playlistItems()
        .list(
            part="snippet,contentDetails",
            playlistId=uploads_playlist_id,
            maxResults=10,
        )
        .execute()
        .get("items", [])
    )
    video_ids = [
        it.get("contentDetails", {}).get("videoId")
        for it in items
        if it.get("contentDetails", {}).get("videoId")
    ]
    if not video_ids:
        return []

    resources = (
        youtube.videos()
        .list(part=_VIDEOS_PART, id=",".join(video_ids))
        .execute()
        .get("items", [])
    )

    videos: list[dict] = []
    for res in resources:
        snippet = res.get("snippet", {})
        stats = res.get("statistics", {})
        content = res.get("contentDetails", {})
        topics = res.get("topicDetails", {})
        status = res.get("status", {})
        videos.append(
            {
                "title": snippet.get("title", "N/A"),
                "videoId": res.get("id", "N/A"),
                "publishedAt": snippet.get("publishedAt", "N/A"),
                "description": snippet.get("description", "") or "",
                "viewCount": stats.get("viewCount", "0"),
                "likeCount": stats.get("likeCount", "0"),
                "commentCount": stats.get("commentCount", "0"),
                "tags": snippet.get("tags", []),
                "topicCategories": topics.get("topicCategories", []),
                "duration": content.get("duration", "N/A"),
                "definition": content.get("definition", "N/A"),
                "privacyStatus": status.get("privacyStatus", "N/A"),
            }
        )
    return videos


def _fetch_comments(youtube, video_id: str, cap: int = 20) -> list[dict]:
    """Fetch up to *cap* top-level comments for a video with author pivots."""
    threads = (
        youtube.commentThreads()
        .list(part="snippet", videoId=video_id, maxResults=cap)
        .execute()
        .get("items", [])
    )
    comments: list[dict] = []
    for thread in threads:
        top = thread.get("snippet", {}).get("topLevelComment", {}).get("snippet", {})
        comments.append(
            {
                "authorDisplayName": top.get("authorDisplayName", "N/A"),
                "authorChannelUrl": top.get("authorChannelUrl", "N/A"),
            }
        )
    return comments


def _fetch_transcripts(video_id: str) -> list[dict] | None:
    """Fetch raw transcript snippets for a video.

    Returns the raw ``[{text, start, duration}, ...]`` list, or ``None`` when
    the transcript is unavailable, disabled, or blocked. Never raises — IP
    blocks are logged so repeated failures are visible.
    """
    try:
        fetched = YouTubeTranscriptApi().fetch(video_id)
        return fetched.to_raw_data()
    except (TranscriptsDisabled, NoTranscriptFound, VideoUnavailable) as exc:
        logger.warning(f"Transcript unavailable for {video_id}: {exc}")
        return None
    except (IpBlocked, RequestBlocked) as exc:
        logger.warning(f"Transcript request blocked (IP) for {video_id}: {exc}")
        return None
    except Exception as exc:
        logger.warning(f"Transcript fetch error for {video_id}: {exc}")
        return None


# ---------------------------------------------------------------------------
# Lightweight analysis (Req 7)
# ---------------------------------------------------------------------------


def _domain_of(url: str) -> str:
    """Return the bare domain (no scheme/www) of a URL."""
    match = _DOMAIN_RE.match(url)
    return match.group(1).lower() if match else url


def _unique(values: list[str]) -> list[str]:
    """Return values with order preserved and duplicates removed."""
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _top_words(text: str, top_n: int = 15) -> list[dict]:
    """Return the top-N non-stopword words (length >= 3) from *text*."""
    words = [
        w for w in re.findall(r"[a-zA-Z]{3,}", text.lower()) if w not in _STOP_WORDS
    ]
    if not words:
        return []
    return [
        {"word": word, "count": count}
        for word, count in Counter(words).most_common(top_n)
    ]


def _detect_language(text: str) -> str | None:
    """Detect the dominant language of *text* via langdetect, or None."""
    text = (text or "").strip()
    if not text:
        return None
    try:
        from langdetect import detect

        return detect(text)
    except Exception:  # pragma: no cover - langdetect failure is non-fatal
        return None


def _analyze(
    videos: list[dict],
    comments: dict,
    transcripts: dict | None = None,
    channel_description: str = "",
) -> dict:
    """Run stdlib-only enrichment over descriptions, transcripts and comments.

    Extracts URLs grouped by domain, emails, hashtags, recurring commenter
    handles, top transcript keywords, and the dominant language.
    """
    transcripts = transcripts or {}
    description_texts = [channel_description] + [
        v.get("description", "") or "" for v in videos
    ]
    transcript_texts = [
        " ".join(snippet.get("text", "") for snippet in data)
        for data in transcripts.values()
        if isinstance(data, list)
    ]
    description_blob = " ".join(description_texts)
    all_text = " ".join(description_texts + transcript_texts)

    social_links: dict[str, list[str]] = {}
    for url in _URL_RE.findall(description_blob):
        domain = _domain_of(url)
        bucket = social_links.setdefault(domain, [])
        if url not in bucket:
            bucket.append(url)

    handle_counts: Counter = Counter()
    handle_url: dict[str, str] = {}
    for entries in comments.values():
        if not isinstance(entries, list):
            continue
        for entry in entries:
            name = entry.get("authorDisplayName")
            if not name:
                continue
            handle_counts[name] += 1
            handle_url.setdefault(name, entry.get("authorChannelUrl", ""))
    top_commenters = [
        {"handle": handle, "count": count, "url": handle_url.get(handle, "")}
        for handle, count in handle_counts.most_common(10)
    ]

    return {
        "social_links": social_links,
        "emails": _unique(_EMAIL_RE.findall(all_text)),
        "hashtags": _unique(_HASHTAG_RE.findall(all_text)),
        "top_commenters": top_commenters,
        "keywords": _top_words(" ".join(transcript_texts)),
        "language": _detect_language(description_blob),
    }


# ---------------------------------------------------------------------------
# Output shaping (Req 3, 8)
# ---------------------------------------------------------------------------

_SOCIAL_ICONS = {
    "twitter.com": "fab fa-twitter",
    "x.com": "fab fa-twitter",
    "t.me": "fab fa-telegram",
    "instagram.com": "fab fa-instagram",
    "facebook.com": "fab fa-facebook",
    "github.com": "fab fa-github",
    "tiktok.com": "fab fa-tiktok",
    "discord.gg": "fab fa-discord",
    "linkedin.com": "fab fa-linkedin",
}


def _node(name: str, title: str, subtitle, icon: str, link: str) -> dict:
    """Build a standard iKy graphic gather node."""
    return {
        "name-node": name,
        "title": title,
        "subtitle": subtitle,
        "icon": icon,
        "link": link,
    }


def _to_int(value) -> int:
    """Best-effort int conversion (defaults to 0)."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _slug(value: str) -> str:
    """Collapse a string into a name-node-safe suffix."""
    return re.sub(r"[^A-Za-z0-9]+", "", value or "") or "x"


def _de_wikipedia(url: str) -> str:
    """Turn a Wikipedia topic URL into a human-readable category name."""
    return url.rstrip("/").split("/")[-1].replace("_", " ")


def _social_icon(domain: str) -> str:
    return _SOCIAL_ICONS.get(domain, "fas fa-link")


def _fmt_date(iso: str) -> str:
    """Return the YYYY-MM-DD portion of an ISO-8601 timestamp."""
    return (iso or "").split("T")[0] if iso and iso != "N/A" else iso


def _build_output(
    username: str,
    channel: dict,
    videos: list[dict],
    comments: dict,
    transcripts: dict,
    analysis: dict,
) -> list[dict]:
    """Assemble the ordered 7-key iKy result contract for a YouTube channel."""
    snippet = channel.get("snippet", {})
    stats = channel.get("statistics", {})
    topics = channel.get("topicDetails", {})

    channel_id = channel.get("id", "N/A")
    title = snippet.get("title", "N/A")
    raw_description = snippet.get("description", "") or ""
    published_at = snippet.get("publishedAt", "N/A")
    country = snippet.get("country", "N/A")
    custom_url = snippet.get("customUrl", "N/A")
    subs = stats.get("subscriberCount", "N/A")
    video_count = stats.get("videoCount", "N/A")
    view_count = stats.get("viewCount", "N/A")
    keywords_field = snippet.get("keywords") or "N/A"
    topic_categories = topics.get("topicCategories", [])
    thumbnails = snippet.get("thumbnails", {})
    avatar = (
        thumbnails.get("high")
        or thumbnails.get("medium")
        or thumbnails.get("default")
        or {}
    ).get("url", "N/A")

    channel_url = (
        f"https://www.youtube.com/channel/{channel_id}"
        if channel_id != "N/A"
        else f"https://www.youtube.com/@{username}"
    )
    topic_names = [_de_wikipedia(url) for url in topic_categories]

    # -- graphic: details (12 identity fields) --
    details = [
        _node("YtDetailsTitle", "Title", title, _ICON, channel_url),
        _node(
            "YtDetailsChannelId",
            "Channel ID",
            channel_id,
            "fas fa-id-badge",
            channel_url,
        ),
        _node(
            "YtDetailsDescription",
            "Description",
            raw_description or "N/A",
            "fas fa-align-left",
            channel_url,
        ),
        _node(
            "YtDetailsPublished",
            "Published",
            published_at,
            "fas fa-calendar",
            channel_url,
        ),
        _node("YtDetailsCountry", "Country", country, "fas fa-globe", channel_url),
        _node(
            "YtDetailsCustomUrl", "Custom URL", custom_url, "fas fa-link", channel_url
        ),
        _node("YtDetailsSubscribers", "Subscribers", subs, "fas fa-users", channel_url),
        _node(
            "YtDetailsVideoCount",
            "Video Count",
            video_count,
            "fas fa-photo-video",
            channel_url,
        ),
        _node(
            "YtDetailsViewCount", "View Count", view_count, "fas fa-eye", channel_url
        ),
        _node(
            "YtDetailsKeywords", "Keywords", keywords_field, "fas fa-tags", channel_url
        ),
        _node(
            "YtDetailsTopics",
            "Topic Categories",
            ", ".join(topic_names) if topic_names else "N/A",
            "fas fa-tag",
            channel_url,
        ),
        _node("YtDetailsThumbnails", "Avatar", avatar, "fas fa-image", channel_url),
    ]

    # -- graphic: statistics (chart children) --
    statistics = [
        {
            "name": "statistics",
            "children": [
                {"name": "subscribers", "value": _to_int(subs)},
                {"name": "videos", "value": _to_int(video_count)},
                {"name": "views", "value": _to_int(view_count)},
            ],
        }
    ]

    # -- graphic: status (availability flags) --
    comments_ok = sum(1 for c in comments.values() if isinstance(c, list))
    comments_off = sum(1 for c in comments.values() if isinstance(c, dict))
    transcripts_ok = sum(1 for t in transcripts.values() if isinstance(t, list))
    transcripts_off = sum(1 for t in transcripts.values() if isinstance(t, dict))
    status = [
        _node(
            "YtStatusCommentsOk",
            "Videos with comments",
            comments_ok,
            "fas fa-comments",
            channel_url,
        ),
        _node(
            "YtStatusCommentsOff",
            "Comments disabled",
            comments_off,
            "fas fa-comment-slash",
            channel_url,
        ),
        _node(
            "YtStatusTranscriptsOk",
            "Transcripts available",
            transcripts_ok,
            "fas fa-closed-captioning",
            channel_url,
        ),
        _node(
            "YtStatusTranscriptsOff",
            "Transcripts unavailable",
            transcripts_off,
            "fas fa-ban",
            channel_url,
        ),
    ]

    # -- graphic: content (aggregate engagement) --
    content = [
        _node(
            "YtContentViews",
            "Last videos views",
            sum(_to_int(v.get("viewCount")) for v in videos),
            "fas fa-eye",
            channel_url,
        ),
        _node(
            "YtContentLikes",
            "Last videos likes",
            sum(_to_int(v.get("likeCount")) for v in videos),
            "fas fa-thumbs-up",
            channel_url,
        ),
        _node(
            "YtContentComments",
            "Last videos comments",
            sum(_to_int(v.get("commentCount")) for v in videos),
            "fas fa-comments",
            channel_url,
        ),
    ]

    # -- graphic: thumbnails (avatar + per-video) --
    thumbnails_section = [
        {
            "name-node": "YtThumbnailAvatar",
            "title": "Avatar",
            "subtitle": "",
            "picture": avatar,
            "link": _LINK,
        }
    ]
    for video in videos:
        vid = video.get("videoId", "")
        thumbnails_section.append(
            {
                "name-node": f"YtThumbnail_{_slug(vid)}",
                "title": video.get("title", "N/A"),
                "subtitle": "",
                "picture": f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg",
                "link": _LINK,
            }
        )

    # -- graphic: topics --
    topics_section = [
        _node(
            f"YtTopic_{_slug(name)}",
            name,
            url,
            "fas fa-tag",
            channel_url,
        )
        for name, url in zip(topic_names, topic_categories, strict=False)
    ]

    # -- graphic: last_videos --
    last_videos = []
    for video in videos:
        vid = video.get("videoId", "")
        last_videos.append(
            {
                "name-node": f"YtVideo_{_slug(vid)}",
                "title": video.get("title", "N/A"),
                "subtitle": f"{video.get('viewCount', '0')} views",
                "icon": _ICON,
                "link": f"https://www.youtube.com/watch?v={vid}",
                "videoId": vid,
                "publishedAt": video.get("publishedAt", "N/A"),
                "viewCount": video.get("viewCount", "0"),
                "likeCount": video.get("likeCount", "0"),
                "commentCount": video.get("commentCount", "0"),
                "duration": video.get("duration", "N/A"),
            }
        )

    # -- graphic: top_commenters --
    top_commenters = []
    for entry in analysis.get("top_commenters", []):
        handle = entry["handle"]
        top_commenters.append(
            {
                "name-node": f"YtCommenter_{_slug(handle)}",
                "title": handle,
                "subtitle": f"{entry['count']} comments",
                "icon": "fas fa-user",
                "link": entry.get("url", ""),
                "url": entry.get("url", ""),
                "count": entry["count"],
            }
        )

    # -- graphic: keywords (hashtags + transcript top-words) --
    keywords_section = []
    for tag in analysis.get("hashtags", []):
        keywords_section.append(
            _node(
                f"YtKeywordTag_{_slug(tag)}",
                f"#{tag}",
                "hashtag",
                "fas fa-hashtag",
                _LINK,
            )
        )
    for keyword in analysis.get("keywords", []):
        keywords_section.append(
            _node(
                f"YtKeywordWord_{_slug(keyword['word'])}",
                keyword["word"],
                keyword["count"],
                "fas fa-font",
                _LINK,
            )
        )

    # -- graphic: social_links (extracted URLs by domain) --
    social_links_section = []
    for domain, urls in analysis.get("social_links", {}).items():
        social_links_section.append(
            {
                "name-node": f"YtSocial_{_slug(domain)}",
                "title": domain,
                "subtitle": ", ".join(urls),
                "icon": _social_icon(domain),
                "link": urls[0] if urls else _LINK,
                "urls": urls,
            }
        )

    graphic = [
        {"details": details},
        {"statistics": statistics},
        {"status": status},
        {"content": content},
        {"thumbnails": thumbnails_section},
        {"topics": topics_section},
        {"last_videos": last_videos},
        {"top_commenters": top_commenters},
        {"keywords": keywords_section},
        {"social_links": social_links_section},
    ]

    # -- profile (flat) --
    profile: list[dict] = [
        {"name": title},
        {"username": custom_url if custom_url != "N/A" else f"@{username}"},
        {"bio": raw_description[:500]},
        {"url": channel_url},
    ]
    if avatar != "N/A":
        profile.append({"photos": [{"picture": avatar, "title": "Youtube"}]})
    if country != "N/A":
        profile.append({"location": country})
    emails = analysis.get("emails", [])
    if emails:
        profile.append({"email": emails[0]})

    social_entries = [
        {
            "name": "Youtube",
            "url": channel_url,
            "icon": _ICON,
            "source": "Youtube",
            "username": custom_url if custom_url != "N/A" else username,
        }
    ]
    for domain, urls in analysis.get("social_links", {}).items():
        for url in urls:
            social_entries.append(
                {
                    "name": domain,
                    "url": url,
                    "icon": _social_icon(domain),
                    "source": "YoutubeDescription",
                    "username": username,
                }
            )
    profile.append({"social": social_entries})
    profile.append(
        {
            "presence": [
                {
                    "name": "youtube",
                    "children": [
                        {"name": "subscribers", "value": _to_int(subs)},
                        {"name": "videos", "value": _to_int(video_count)},
                        {"name": "views", "value": _to_int(view_count)},
                    ],
                }
            ]
        }
    )

    # -- timeline (channel creation + each video publish) --
    timeline: list[dict] = []
    if published_at != "N/A":
        timeline.append(
            {
                "date": _fmt_date(published_at),
                "action": "Youtube : Channel Created",
                "icon": _ICON,
            }
        )
    for video in videos:
        published = video.get("publishedAt", "N/A")
        if published != "N/A":
            timeline.append(
                {
                    "date": _fmt_date(published),
                    "action": f"Youtube : Published '{video.get('title', '')}'",
                    "icon": _ICON,
                }
            )

    raw = {
        "channel": channel,
        "videos": videos,
        "comments": comments,
        "transcripts": transcripts,
    }

    return [
        {"module": "youtube"},
        {"param": username},
        {"validation": "hard"},
        {"raw": raw},
        {"graphic": graphic},
        {"profile": profile},
        {"timeline": timeline},
    ]


# ---------------------------------------------------------------------------
# Main task (Req 9, 10, 11)
# ---------------------------------------------------------------------------


@iky_task(module_name="youtube", dev_mode_sleep=5)
def p_youtube(username: str) -> list[dict]:
    """Profile a YouTube channel from a handle, URL, or channel id.

    Resolves the channel, hydrates the latest uploads, enriches with bounded
    comments and transcripts, runs lightweight analysis, and emits iKy's
    ordered 7-key result contract. External failures degrade gracefully; only
    fatal conditions raise ``iKy - ...`` warnings.
    """
    key = api_keys_search("youtube_key")
    if not key:
        raise Exception("iKy - Missing or invalid YouTube API key")

    handle = _parse_handle(username)

    try:
        youtube = build("youtube", "v3", developerKey=key)
    except Exception as exc:
        if str(exc).startswith("iKy - "):
            raise
        raise Exception("iKy - Network error") from exc

    channel = _resolve_channel(youtube, handle)
    if not channel:
        raise Exception("iKy - Channel not found")

    uploads = (
        channel.get("contentDetails", {}).get("relatedPlaylists", {}).get("uploads", "")
    )
    try:
        videos = _fetch_videos(youtube, uploads) if uploads else []
    except HttpError as exc:
        status = getattr(exc, "status_code", None) or getattr(exc.resp, "status", None)
        if status == 403:
            raise Exception(
                "iKy - YouTube API quota exceeded or access forbidden"
            ) from exc
        logger.warning(f"Videos fetch error: {exc}")
        videos = []
    except Exception as exc:
        logger.warning(f"Videos fetch error: {exc}")
        videos = []

    comments: dict = {}
    transcripts: dict = {}
    for video in videos:
        vid = video.get("videoId", "")
        if not vid:
            continue
        try:
            comments[vid] = _fetch_comments(youtube, vid)
        except HttpError as exc:
            logger.warning(f"Comments unavailable for {vid}: {exc}")
            comments[vid] = {"commentUnavailable": True}
        except Exception as exc:
            logger.warning(f"Comments error for {vid}: {exc}")
            comments[vid] = {"commentUnavailable": True}

        raw_transcript = _fetch_transcripts(vid)
        transcripts[vid] = (
            raw_transcript
            if raw_transcript is not None
            else {"transcriptUnavailable": True}
        )

    channel_description = channel.get("snippet", {}).get("description", "") or ""
    analysis = _analyze(videos, comments, transcripts, channel_description)
    return _build_output(handle, channel, videos, comments, transcripts, analysis)


# Backward-compatible alias: the registry references t_youtube
t_youtube = p_youtube


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def output(data: list) -> None:
    """Print a JSON dump of the module result."""
    print(json.dumps(data, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Query YouTube for a channel handle")
    parser.add_argument("username", help="YouTube channel handle or URL to look up")
    args = parser.parse_args()

    result = t_youtube(args.username)
    output(result)
