"""Tests for backend/modules/youtube/youtube_tasks.py.

Channel-first YouTube OSINT module. All external I/O is mocked:
- ``build`` (googleapiclient) is patched to return a chained ``MagicMock``.
- ``api_keys_search`` is patched to control the API-key guard.
- ``YouTubeTranscriptApi`` is patched for transcript fetching.
- ``Path.cwd`` is patched so the ``@iky_task`` dev-mode golden file is never
  found and the real processing path always runs.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from googleapiclient.errors import HttpError
from youtube_transcript_api import IpBlocked, NoTranscriptFound, TranscriptsDisabled

MODULE = "modules.youtube.youtube_tasks"


# ---------------------------------------------------------------------------
# Dev-mode bypass guard (mirrors the github test pattern)
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _block_devmode_file(tmp_path):
    """Ensure @iky_task never finds outputs/output-youtube.json during tests."""
    with patch.object(Path, "cwd", return_value=tmp_path):
        yield


# ---------------------------------------------------------------------------
# Google API mock builders
# ---------------------------------------------------------------------------


def _http_error(status: int, reason: str = "error") -> HttpError:
    """Build a googleapiclient HttpError with a given status and reason."""

    class _Resp:
        pass

    resp = _Resp()
    resp.status = status
    resp.reason = reason
    content = json.dumps(
        {"error": {"code": status, "errors": [{"reason": reason}]}}
    ).encode()
    return HttpError(resp, content)


def _execute(value=None, *, raises=None):
    """Return a MagicMock whose .execute() yields *value* or raises *raises*."""
    node = MagicMock()
    if raises is not None:
        node.execute.side_effect = raises
    else:
        node.execute.return_value = value
    return node


# ===========================================================================
# Phase 2.1 — _parse_handle (Req 1)
# ===========================================================================


class TestParseHandle:
    def test_at_handle_strips_at(self):
        from modules.youtube.youtube_tasks import _parse_handle

        assert _parse_handle("@GoogleDevelopers") == "GoogleDevelopers"

    def test_bare_handle_unchanged(self):
        from modules.youtube.youtube_tasks import _parse_handle

        assert _parse_handle("GoogleDevelopers") == "GoogleDevelopers"

    def test_full_url_at_handle(self):
        from modules.youtube.youtube_tasks import _parse_handle

        assert _parse_handle("youtube.com/@GoogleDevelopers") == "GoogleDevelopers"

    def test_full_url_with_scheme_and_www(self):
        from modules.youtube.youtube_tasks import _parse_handle

        assert (
            _parse_handle("https://www.youtube.com/@GoogleDevelopers")
            == "GoogleDevelopers"
        )

    def test_channel_id_url_returns_channel_id(self):
        from modules.youtube.youtube_tasks import _parse_handle

        cid = "UC_x5XG1OV2P6uZZ5FSM9Ttw"
        assert _parse_handle(f"youtube.com/channel/{cid}") == cid

    def test_video_url_rejected(self):
        from modules.youtube.youtube_tasks import _parse_handle

        with pytest.raises(Exception, match="iKy - Invalid YouTube channel/handle"):
            _parse_handle("youtube.com/watch?v=abc123")

    def test_shorts_url_rejected(self):
        from modules.youtube.youtube_tasks import _parse_handle

        with pytest.raises(Exception, match="iKy - Invalid YouTube channel/handle"):
            _parse_handle("youtube.com/shorts/xyz")

    def test_embed_url_rejected(self):
        from modules.youtube.youtube_tasks import _parse_handle

        with pytest.raises(Exception, match="iKy - Invalid YouTube channel/handle"):
            _parse_handle("youtube.com/embed/xyz")

    def test_empty_rejected(self):
        from modules.youtube.youtube_tasks import _parse_handle

        with pytest.raises(Exception, match="iKy - Invalid YouTube channel/handle"):
            _parse_handle("")

    def test_whitespace_only_rejected(self):
        from modules.youtube.youtube_tasks import _parse_handle

        with pytest.raises(Exception, match="iKy - Invalid YouTube channel/handle"):
            _parse_handle("   ")


def _channels_mock(*, for_handle=None, for_username=None, by_id=None, raises=None):
    """Build a YouTube client mock routing channels().list by kwargs."""
    youtube = MagicMock()

    def list_side(**kwargs):
        if raises is not None:
            return _execute(raises=raises)
        if "id" in kwargs:
            return _execute({"items": by_id or []})
        if "forHandle" in kwargs:
            return _execute({"items": for_handle or []})
        if "forUsername" in kwargs:
            return _execute({"items": for_username or []})
        return _execute({"items": []})

    youtube.channels.return_value.list.side_effect = list_side
    return youtube


# ===========================================================================
# Phase 2.3 — _resolve_channel (Req 2, 11)
# ===========================================================================


class TestResolveChannel:
    def test_resolves_via_forhandle(self):
        from modules.youtube.youtube_tasks import _resolve_channel

        youtube = _channels_mock(for_handle=[{"id": "UCabc", "snippet": {}}])
        channel = _resolve_channel(youtube, "MrBeast")
        assert channel["id"] == "UCabc"

    def test_resolves_via_forusername_fallback(self):
        from modules.youtube.youtube_tasks import _resolve_channel

        youtube = _channels_mock(
            for_handle=[], for_username=[{"id": "UCxyz", "snippet": {}}]
        )
        channel = _resolve_channel(youtube, "OldChannel")
        assert channel["id"] == "UCxyz"

    def test_unknown_handle_returns_none(self):
        from modules.youtube.youtube_tasks import _resolve_channel

        youtube = _channels_mock(for_handle=[], for_username=[])
        assert _resolve_channel(youtube, "ghost") is None

    def test_channel_id_uses_id_lookup(self):
        from modules.youtube.youtube_tasks import _resolve_channel

        cid = "UC_x5XG1OV2P6uZZ5FSM9Ttw"
        youtube = _channels_mock(by_id=[{"id": cid, "snippet": {}}])
        channel = _resolve_channel(youtube, cid)
        assert channel["id"] == cid

    def test_403_raises_quota_error(self):
        from modules.youtube.youtube_tasks import _resolve_channel

        youtube = _channels_mock(raises=_http_error(403, "quotaExceeded"))
        with pytest.raises(
            Exception,
            match="iKy - YouTube API quota exceeded or access forbidden",
        ):
            _resolve_channel(youtube, "handle")

    def test_404_raises_channel_not_found(self):
        from modules.youtube.youtube_tasks import _resolve_channel

        youtube = _channels_mock(raises=_http_error(404, "notFound"))
        with pytest.raises(Exception, match="iKy - Channel not found"):
            _resolve_channel(youtube, "handle")

    def test_network_error_mapped(self):
        from modules.youtube.youtube_tasks import _resolve_channel

        youtube = _channels_mock(raises=ConnectionError("boom"))
        with pytest.raises(Exception, match="iKy - Network error"):
            _resolve_channel(youtube, "handle")

    def test_never_calls_search_list(self):
        from modules.youtube.youtube_tasks import _resolve_channel

        youtube = _channels_mock(for_handle=[{"id": "UCabc", "snippet": {}}])
        _resolve_channel(youtube, "MrBeast")
        youtube.search.assert_not_called()


def _videos_mock(playlist_items, videos_items):
    """Build a YouTube client mock for playlistItems + videos endpoints."""
    youtube = MagicMock()
    youtube.playlistItems.return_value.list.return_value = _execute(
        {"items": playlist_items}
    )
    youtube.videos.return_value.list.return_value = _execute({"items": videos_items})
    return youtube


def _make_video_item(vid: str) -> dict:
    """Build a videos.list item resource for *vid*."""
    return {
        "id": vid,
        "snippet": {
            "title": f"Title {vid}",
            "publishedAt": "2023-01-01T00:00:00Z",
            "description": f"Description for {vid}",
            "tags": ["tag1", "tag2"],
        },
        "statistics": {
            "viewCount": "1000",
            "likeCount": "100",
            "commentCount": "10",
        },
        "contentDetails": {"duration": "PT5M", "definition": "hd"},
        "topicDetails": {"topicCategories": ["https://en.wikipedia.org/wiki/Music"]},
        "status": {"privacyStatus": "public"},
    }


# ===========================================================================
# Phase 3.1 — _fetch_videos (Req 4)
# ===========================================================================


class TestFetchVideos:
    def test_ten_videos_fetched(self):
        from modules.youtube.youtube_tasks import _fetch_videos

        ids = [f"vid{i}" for i in range(10)]
        playlist = [{"contentDetails": {"videoId": i}} for i in ids]
        videos_items = [_make_video_item(i) for i in ids]
        youtube = _videos_mock(playlist, videos_items)

        videos = _fetch_videos(youtube, "UUuploads")

        assert len(videos) == 10
        for v in videos:
            assert v["videoId"] in ids
            assert v["title"] == f"Title {v['videoId']}"
            assert v["viewCount"] == "1000"

    def test_three_videos_returns_three_without_error(self):
        from modules.youtube.youtube_tasks import _fetch_videos

        ids = ["a", "b", "c"]
        playlist = [{"contentDetails": {"videoId": i}} for i in ids]
        videos_items = [_make_video_item(i) for i in ids]
        youtube = _videos_mock(playlist, videos_items)

        videos = _fetch_videos(youtube, "UUuploads")

        assert len(videos) == 3
        assert [v["videoId"] for v in videos] == ids

    def test_captures_privacy_status_and_duration(self):
        from modules.youtube.youtube_tasks import _fetch_videos

        youtube = _videos_mock(
            [{"contentDetails": {"videoId": "x"}}], [_make_video_item("x")]
        )
        videos = _fetch_videos(youtube, "UUuploads")
        assert videos[0]["privacyStatus"] == "public"
        assert videos[0]["duration"] == "PT5M"

    def test_empty_playlist_returns_empty_list(self):
        from modules.youtube.youtube_tasks import _fetch_videos

        youtube = _videos_mock([], [])
        assert _fetch_videos(youtube, "UUuploads") == []


# ===========================================================================
# Phase 3.2 — _fetch_comments (Req 5)
# ===========================================================================


def _comment_thread(name: str, url: str) -> dict:
    return {
        "snippet": {
            "topLevelComment": {
                "snippet": {"authorDisplayName": name, "authorChannelUrl": url}
            }
        }
    }


class TestFetchComments:
    def test_collects_author_pivot_data(self):
        from modules.youtube.youtube_tasks import _fetch_comments

        threads = [
            _comment_thread(f"@user{i}", f"https://youtube.com/channel/UC{i}")
            for i in range(20)
        ]
        youtube = MagicMock()
        youtube.commentThreads.return_value.list.return_value = _execute(
            {"items": threads}
        )

        comments = _fetch_comments(youtube, "vid1")

        assert len(comments) == 20
        for c in comments:
            assert "authorDisplayName" in c
            assert "authorChannelUrl" in c
        assert comments[0]["authorDisplayName"] == "@user0"
        assert comments[0]["authorChannelUrl"] == "https://youtube.com/channel/UC0"

    def test_requests_capped_at_20(self):
        from modules.youtube.youtube_tasks import _fetch_comments

        youtube = MagicMock()
        youtube.commentThreads.return_value.list.return_value = _execute({"items": []})

        _fetch_comments(youtube, "vid1")

        _, kwargs = youtube.commentThreads.return_value.list.call_args
        assert kwargs["maxResults"] == 20
        assert kwargs["videoId"] == "vid1"


# ===========================================================================
# Phase 3.3 — _fetch_transcripts (Req 6)
# ===========================================================================


class TestFetchTranscripts:
    def test_transcript_fetched_returns_raw_snippets(self):
        from modules.youtube.youtube_tasks import _fetch_transcripts

        raw = [{"text": "hello world", "start": 0.0, "duration": 1.5}]
        with patch(f"{MODULE}.YouTubeTranscriptApi") as api:
            api.return_value.fetch.return_value.to_raw_data.return_value = raw
            result = _fetch_transcripts("vid1")

        assert result == raw
        assert result[0]["text"] == "hello world"

    def test_transcripts_disabled_returns_none(self):
        from modules.youtube.youtube_tasks import _fetch_transcripts

        with patch(f"{MODULE}.YouTubeTranscriptApi") as api:
            api.return_value.fetch.side_effect = TranscriptsDisabled("vid1")
            assert _fetch_transcripts("vid1") is None

    def test_ip_blocked_returns_none(self):
        from modules.youtube.youtube_tasks import _fetch_transcripts

        with patch(f"{MODULE}.YouTubeTranscriptApi") as api:
            api.return_value.fetch.side_effect = IpBlocked("vid1")
            assert _fetch_transcripts("vid1") is None

    def test_no_transcript_found_returns_none(self):
        from modules.youtube.youtube_tasks import _fetch_transcripts

        with patch(f"{MODULE}.YouTubeTranscriptApi") as api:
            api.return_value.fetch.side_effect = NoTranscriptFound("vid1", ["en"], [])
            assert _fetch_transcripts("vid1") is None

    def test_unexpected_error_returns_none(self):
        from modules.youtube.youtube_tasks import _fetch_transcripts

        with patch(f"{MODULE}.YouTubeTranscriptApi") as api:
            api.return_value.fetch.side_effect = RuntimeError("boom")
            assert _fetch_transcripts("vid1") is None


# ===========================================================================
# Phase 3.4 — _analyze (Req 7)
# ===========================================================================


class TestAnalyze:
    def test_social_links_grouped_by_domain(self):
        from modules.youtube.youtube_tasks import _analyze

        videos = [
            {
                "description": (
                    "Follow https://twitter.com/user and https://t.me/channel"
                )
            }
        ]
        result = _analyze(videos, {})

        assert "twitter.com" in result["social_links"]
        assert "t.me" in result["social_links"]
        assert "https://twitter.com/user" in result["social_links"]["twitter.com"]

    def test_recurring_commenter_surfaced_with_url(self):
        from modules.youtube.youtube_tasks import _analyze

        url = "https://www.youtube.com/channel/UCUserA"
        comments = {
            "v1": [{"authorDisplayName": "@UserA", "authorChannelUrl": url}],
            "v2": [{"authorDisplayName": "@UserA", "authorChannelUrl": url}],
            "v3": [{"authorDisplayName": "@UserA", "authorChannelUrl": url}],
        }
        result = _analyze([], comments)

        top = result["top_commenters"]
        entry = next((e for e in top if e["handle"] == "@UserA"), None)
        assert entry is not None
        assert entry["count"] == 3
        assert entry["url"] == url

    def test_emails_extracted_from_descriptions_and_transcripts(self):
        from modules.youtube.youtube_tasks import _analyze

        videos = [{"description": "Reach me at user@example.com"}]
        transcripts = {"v1": [{"text": "or email boss@corp.io please"}]}
        result = _analyze(videos, {}, transcripts)

        assert "user@example.com" in result["emails"]
        assert "boss@corp.io" in result["emails"]

    def test_hashtags_extracted(self):
        from modules.youtube.youtube_tasks import _analyze

        videos = [{"description": "New video #osint #python tutorial"}]
        result = _analyze(videos, {})

        assert "osint" in result["hashtags"]
        assert "python" in result["hashtags"]

    def test_keyword_top_words_from_transcripts(self):
        from modules.youtube.youtube_tasks import _analyze

        transcripts = {"v1": [{"text": "python python python data data investigation"}]}
        result = _analyze([], {}, transcripts)

        words = {kw["word"]: kw["count"] for kw in result["keywords"]}
        assert words.get("python") == 3
        assert words.get("data") == 2

    def test_language_detected(self):
        from modules.youtube.youtube_tasks import _analyze

        videos = [
            {
                "description": (
                    "This channel publishes weekly investigations about "
                    "open source intelligence and digital security research."
                )
            }
        ]
        result = _analyze(videos, {}, channel_description="")
        assert result["language"] == "en"


# ---------------------------------------------------------------------------
# Output-contract fixtures
# ---------------------------------------------------------------------------

CHANNEL_FULL = {
    "id": "UCchannel0000000000000",
    "snippet": {
        "title": "Test Channel",
        "description": "A channel about tech. Contact user@example.com",
        "publishedAt": "2020-01-01T00:00:00Z",
        "country": "US",
        "customUrl": "@testchannel",
        "keywords": "osint tech",
        "thumbnails": {"high": {"url": "https://yt/avatar.jpg"}},
    },
    "statistics": {
        "subscriberCount": "1000",
        "videoCount": "50",
        "viewCount": "999999",
    },
    "contentDetails": {"relatedPlaylists": {"uploads": "UUuploads"}},
    "topicDetails": {"topicCategories": ["https://en.wikipedia.org/wiki/Technology"]},
}


def _video_out(vid: str) -> dict:
    """Video dict shaped like _fetch_videos output."""
    return {
        "title": f"Title {vid}",
        "videoId": vid,
        "publishedAt": "2023-05-05T00:00:00Z",
        "description": f"Desc {vid}",
        "viewCount": "500",
        "likeCount": "50",
        "commentCount": "5",
        "tags": ["a"],
        "topicCategories": [],
        "duration": "PT3M",
        "definition": "hd",
        "privacyStatus": "public",
    }


def _analysis_full() -> dict:
    return {
        "social_links": {"twitter.com": ["https://twitter.com/testchannel"]},
        "emails": ["user@example.com"],
        "hashtags": ["osint"],
        "top_commenters": [
            {
                "handle": "@UserA",
                "count": 3,
                "url": "https://www.youtube.com/channel/UCUserA",
            }
        ],
        "keywords": [{"word": "python", "count": 3}],
        "language": "en",
    }


def _sections(graphic: list) -> dict:
    """Flatten a graphic list of single-key dicts into a name->value dict."""
    return {next(iter(s.keys())): next(iter(s.values())) for s in graphic}


def _profile_get(profile: list, key: str):
    return next((p[key] for p in profile if key in p), None)


# ===========================================================================
# Phase 3.5 — _build_output (Req 3, 8)
# ===========================================================================


class TestBuildOutput:
    def _build(self, channel=None, videos=None, comments=None, analysis=None):
        from modules.youtube.youtube_tasks import _build_output

        channel = channel if channel is not None else CHANNEL_FULL
        videos = videos if videos is not None else [_video_out("v1"), _video_out("v2")]
        comments = comments if comments is not None else {}
        transcripts: dict = {}
        analysis = analysis if analysis is not None else _analysis_full()
        return _build_output(
            "testchannel", channel, videos, comments, transcripts, analysis
        )

    def test_seven_key_order(self):
        result = self._build()
        keys = [next(iter(item.keys())) for item in result]
        assert keys[:3] == ["module", "param", "validation"]
        validation = next(i["validation"] for i in result if "validation" in i)
        assert validation == "hard"
        assert {"raw", "graphic", "profile", "timeline"} <= set(keys)
        assert "tasks" not in keys

    def test_module_and_param(self):
        result = self._build()
        assert next(i["module"] for i in result if "module" in i) == "youtube"
        assert next(i["param"] for i in result if "param" in i) == "testchannel"

    def test_raw_dict_has_four_keys(self):
        result = self._build()
        raw = next(i["raw"] for i in result if "raw" in i)
        assert set(raw.keys()) == {"channel", "videos", "comments", "transcripts"}

    def test_graphic_sections_present(self):
        result = self._build()
        graphic = next(i["graphic"] for i in result if "graphic" in i)
        section_keys = set(_sections(graphic).keys())
        for expected in (
            "details",
            "statistics",
            "last_videos",
            "social_links",
            "top_commenters",
        ):
            assert expected in section_keys

    def test_all_name_nodes_prefixed_yt(self):
        result = self._build()
        graphic = next(i["graphic"] for i in result if "graphic" in i)
        for section in _sections(graphic).values():
            if not isinstance(section, list):
                continue
            for node in section:
                if isinstance(node, dict) and "name-node" in node:
                    assert node["name-node"].startswith("Yt"), node["name-node"]

    def test_details_all_twelve_non_na(self):
        result = self._build()
        graphic = next(i["graphic"] for i in result if "graphic" in i)
        details = _sections(graphic)["details"]
        assert len(details) == 12
        for node in details:
            assert node["subtitle"] != "N/A", node["title"]

    def test_details_missing_fields_default_na(self):
        channel = {
            "id": "UCchannel0000000000000",
            "snippet": {
                "title": "Test Channel",
                "description": "desc",
                "publishedAt": "2020-01-01T00:00:00Z",
                "customUrl": "@testchannel",
                "thumbnails": {"high": {"url": "https://yt/avatar.jpg"}},
            },
            "statistics": {
                "subscriberCount": "1",
                "videoCount": "1",
                "viewCount": "1",
            },
            "contentDetails": {"relatedPlaylists": {"uploads": "UUuploads"}},
            "topicDetails": {"topicCategories": []},
        }
        result = self._build(channel=channel)
        graphic = next(i["graphic"] for i in result if "graphic" in i)
        details = {n["title"]: n["subtitle"] for n in _sections(graphic)["details"]}
        assert details["Country"] == "N/A"
        assert details["Keywords"] == "N/A"

    def test_profile_email_present_when_extracted(self):
        result = self._build()
        assert _profile_get(
            next(i["profile"] for i in result if "profile" in i), "email"
        ) == ("user@example.com")

    def test_profile_bio_truncated_to_500(self):
        channel = dict(CHANNEL_FULL)
        channel["snippet"] = dict(CHANNEL_FULL["snippet"])
        channel["snippet"]["description"] = "x" * 900
        result = self._build(channel=channel)
        bio = _profile_get(next(i["profile"] for i in result if "profile" in i), "bio")
        assert len(bio) == 500

    def test_timeline_channel_plus_videos(self):
        result = self._build(videos=[_video_out("v1"), _video_out("v2")])
        timeline = next(i["timeline"] for i in result if "timeline" in i)
        assert len(timeline) == 3
        for entry in timeline:
            assert entry["icon"] == "fab fa-youtube"

    def test_top_commenter_node_carries_pivot_url(self):
        result = self._build()
        graphic = next(i["graphic"] for i in result if "graphic" in i)
        commenters = _sections(graphic)["top_commenters"]
        entry = next((c for c in commenters if c["title"] == "@UserA"), None)
        assert entry is not None
        assert entry["url"] == "https://www.youtube.com/channel/UCUserA"

    def test_social_links_grouped_by_domain_node(self):
        result = self._build()
        graphic = next(i["graphic"] for i in result if "graphic" in i)
        titles = [n["title"] for n in _sections(graphic)["social_links"]]
        assert "twitter.com" in titles


# ---------------------------------------------------------------------------
# Full-path youtube client mock + runner
# ---------------------------------------------------------------------------


def _happy_youtube(comments_side=None):
    youtube = MagicMock()
    youtube.channels.return_value.list.side_effect = lambda **kw: _execute(
        {"items": [CHANNEL_FULL]}
    )
    youtube.playlistItems.return_value.list.return_value = _execute(
        {
            "items": [
                {"contentDetails": {"videoId": "v1"}},
                {"contentDetails": {"videoId": "v2"}},
            ]
        }
    )
    youtube.videos.return_value.list.return_value = _execute(
        {"items": [_make_video_item("v1"), _make_video_item("v2")]}
    )
    if comments_side is not None:
        youtube.commentThreads.return_value.list.side_effect = comments_side
    else:
        youtube.commentThreads.return_value.list.return_value = _execute(
            {
                "items": [
                    _comment_thread("@UserA", "https://www.youtube.com/channel/UCUserA")
                ]
            }
        )
    return youtube


def _run_t_youtube(
    username="@testchannel", youtube=None, key="KEY", transcript_raw=None
):
    youtube = youtube if youtube is not None else _happy_youtube()
    with (
        patch(f"{MODULE}.api_keys_search", return_value=key),
        patch(f"{MODULE}.build", return_value=youtube),
        patch(f"{MODULE}.YouTubeTranscriptApi") as api,
    ):
        if transcript_raw is None:
            api.return_value.fetch.side_effect = TranscriptsDisabled("v")
        else:
            api.return_value.fetch.return_value.to_raw_data.return_value = (
                transcript_raw
            )
        from modules.youtube.youtube_tasks import t_youtube

        return t_youtube(username)


def _raw(result: list) -> dict:
    return next(i["raw"] for i in result if "raw" in i)


def _warning_reason(result: list):
    raw = _raw(result)
    assert raw[0]["status"] == "Warning"
    return raw[0]["reason"]


# ===========================================================================
# Phase 4.1 — p_youtube / t_youtube happy path (Req 8, 9)
# ===========================================================================


class TestTaskHappyPath:
    def test_seven_key_contract_shape(self):
        result = _run_t_youtube()
        keys = [next(iter(i.keys())) for i in result]
        assert keys[:3] == ["module", "param", "validation"]
        assert {"raw", "graphic", "profile", "timeline"} <= set(keys)
        assert "tasks" not in keys

    def test_validation_hard(self):
        result = _run_t_youtube()
        assert next(i["validation"] for i in result if "validation" in i) == "hard"

    def test_param_is_normalized_handle(self):
        result = _run_t_youtube("@testchannel")
        assert next(i["param"] for i in result if "param" in i) == "testchannel"

    def test_graphic_subsections_present(self):
        result = _run_t_youtube()
        graphic = next(i["graphic"] for i in result if "graphic" in i)
        section_keys = set(_sections(graphic).keys())
        for expected in (
            "details",
            "statistics",
            "last_videos",
            "social_links",
            "top_commenters",
        ):
            assert expected in section_keys

    def test_timeline_icons(self):
        result = _run_t_youtube()
        timeline = next(i["timeline"] for i in result if "timeline" in i)
        assert len(timeline) == 3
        for entry in timeline:
            assert entry["icon"] == "fab fa-youtube"

    def test_profile_email_extracted_from_channel_description(self):
        result = _run_t_youtube()
        profile = next(i["profile"] for i in result if "profile" in i)
        assert _profile_get(profile, "email") == "user@example.com"

    def test_transcript_stored_when_available(self):
        raw_snippets = [{"text": "hi", "start": 0.0, "duration": 1.0}]
        result = _run_t_youtube(transcript_raw=raw_snippets)
        raw = _raw(result)
        assert raw["transcripts"]["v1"] == raw_snippets

    def test_fewer_than_ten_videos_no_error(self):
        youtube = _happy_youtube()
        youtube.playlistItems.return_value.list.return_value = _execute(
            {"items": [{"contentDetails": {"videoId": "only"}}]}
        )
        youtube.videos.return_value.list.return_value = _execute(
            {"items": [_make_video_item("only")]}
        )
        result = _run_t_youtube(youtube=youtube)
        raw = _raw(result)
        assert len(raw["videos"]) == 1


# ===========================================================================
# Phase 4.2 — degraded / warning paths (Req 1, 5, 6, 10, 11)
# ===========================================================================


class TestTaskDegraded:
    def test_missing_api_key_warning(self):
        result = _run_t_youtube(key="")
        assert _warning_reason(result) == "Missing or invalid YouTube API key"

    def test_video_url_rejected_warning(self):
        result = _run_t_youtube("youtube.com/watch?v=abc123")
        assert _warning_reason(result) == "Invalid YouTube channel/handle"

    def test_empty_input_warning(self):
        result = _run_t_youtube("")
        assert _warning_reason(result) == "Invalid YouTube channel/handle"

    def test_quota_exceeded_warning(self):
        youtube = _happy_youtube()
        youtube.channels.return_value.list.side_effect = lambda **kw: _execute(
            raises=_http_error(403, "quotaExceeded")
        )
        result = _run_t_youtube(youtube=youtube)
        assert (
            _warning_reason(result) == "YouTube API quota exceeded or access forbidden"
        )

    def test_network_error_warning(self):
        youtube = _happy_youtube()
        youtube.channels.return_value.list.side_effect = lambda **kw: _execute(
            raises=ConnectionError("down")
        )
        result = _run_t_youtube(youtube=youtube)
        assert _warning_reason(result) == "Network error"

    def test_private_channel_not_found_warning(self):
        youtube = _happy_youtube()
        youtube.channels.return_value.list.side_effect = lambda **kw: _execute(
            {"items": []}
        )
        result = _run_t_youtube(youtube=youtube)
        assert _warning_reason(result) == "Channel not found"

    def test_comments_disabled_degrades_and_continues(self):
        def comments_side(**kwargs):
            if kwargs.get("videoId") == "v1":
                return _execute(raises=_http_error(403, "commentsDisabled"))
            return _execute(
                {
                    "items": [
                        _comment_thread(
                            "@UserB", "https://www.youtube.com/channel/UCUserB"
                        )
                    ]
                }
            )

        youtube = _happy_youtube(comments_side=comments_side)
        result = _run_t_youtube(youtube=youtube)
        raw = _raw(result)
        assert raw["comments"]["v1"] == {"commentUnavailable": True}
        assert isinstance(raw["comments"]["v2"], list)

    def test_transcript_disabled_degrades(self):
        result = _run_t_youtube(transcript_raw=None)
        raw = _raw(result)
        assert raw["transcripts"]["v1"] == {"transcriptUnavailable": True}

    def test_no_transcript_found_degrades_and_continues(self):
        youtube = _happy_youtube()
        with (
            patch(f"{MODULE}.api_keys_search", return_value="KEY"),
            patch(f"{MODULE}.build", return_value=youtube),
            patch(f"{MODULE}.YouTubeTranscriptApi") as api,
        ):
            api.return_value.fetch.side_effect = NoTranscriptFound("v1", ["en"], [])
            from modules.youtube.youtube_tasks import t_youtube

            result = t_youtube("@testchannel")

        raw = _raw(result)
        assert raw["transcripts"]["v1"] == {"transcriptUnavailable": True}
        assert raw["transcripts"]["v2"] == {"transcriptUnavailable": True}


# ===========================================================================
# Phase 4.1 — decorator wiring / CLI (Req 9)
# ===========================================================================


class TestTaskWiring:
    def test_t_youtube_is_p_youtube(self):
        from modules.youtube.youtube_tasks import p_youtube, t_youtube

        assert t_youtube is p_youtube

    def test_celery_task_name(self):
        from modules.youtube.youtube_tasks import p_youtube

        assert p_youtube.name == "modules.youtube.youtube_tasks.t_youtube"

    def test_output_is_callable(self):
        from modules.youtube.youtube_tasks import output

        # Should not raise when dumping a minimal result.
        output([{"module": "youtube"}])


# ===========================================================================
# Phase 1 — registration / config conformance (Req 9, 10)
# ===========================================================================


class TestRegistration:
    def test_celery_imports_youtube(self):
        from celery_app import celery

        assert "modules.youtube.youtube_tasks" in celery.conf.imports

    def test_module_registry_entry(self):
        from module_registry import MODULE_REGISTRY

        assert MODULE_REGISTRY["youtube"] == (
            "modules.youtube.youtube_tasks.t_youtube",
            False,
        )

    def test_init_is_empty(self):
        import modules.youtube

        assert Path(modules.youtube.__file__).stat().st_size == 0

    def test_requirements_pinned(self):
        req = Path(__file__).resolve().parents[1] / "requirements.txt"
        assert "youtube-transcript-api==1.2.4" in req.read_text()

    def test_apikeys_default_entry(self):
        path = (
            Path(__file__).resolve().parents[1] / "factories" / "apikeys_default.json"
        )
        keys = json.loads(path.read_text())
        entry = next((k for k in keys if k["name"] == "youtube_key"), None)
        assert entry == {"id": 20, "name": "youtube_key", "key": ""}
