"""Regression tests for tiktok module migration to @iky_task decorator.

Verifies that the migrated p_tiktok (now a Celery task via @iky_task)
produces output structurally identical to the expected contract, and that
all quality fixes (renamed cookie fn, no deprecated datetime, enrichment
math, fallback behavior) are correctly implemented.
"""

import ast
import inspect
import json
import sys
import types
from pathlib import Path
from typing import ClassVar
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Stub out heavy third-party deps that are not available outside Docker.
# Must happen BEFORE importing the module under test.
#
# Strategy (follows the twitter_migration pattern):
#   1. Stub factories.iKy_functions (requires geopy, not installed locally)
#   2. Stub TikTokApi, browser_cookie3, requests
#   3. THEN import the module under test at module level so that patch()
#      decorators can resolve "modules.tiktok.tiktok_tasks.*" paths.
# ---------------------------------------------------------------------------


def _make_iky_functions_mock() -> types.ModuleType:
    """Stub for factories.iKy_functions (requires geopy, not installed locally)."""
    mod = types.ModuleType("factories.iKy_functions")
    mod.analize_rrss = MagicMock(return_value={})
    mod.location_geo = MagicMock(return_value=None)
    mod.extract_hashtags = MagicMock(return_value=[])
    mod.extract_mentions = MagicMock(return_value=[])
    mod.extract_url = MagicMock(return_value=[])
    return mod


def _make_geopy_mock() -> types.ModuleType:
    """Stub for geopy (not installed locally)."""
    geopy_mod = types.ModuleType("geopy")
    geocoders_mod = types.ModuleType("geopy.geocoders")
    geocoders_mod.Nominatim = MagicMock()
    geopy_mod.geocoders = geocoders_mod
    return geopy_mod, geocoders_mod


_geopy_mod, _geopy_geocoders = _make_geopy_mock()

sys.modules.setdefault("geopy", _geopy_mod)
sys.modules.setdefault("geopy.geocoders", _geopy_geocoders)
sys.modules.setdefault("factories.iKy_functions", _make_iky_functions_mock())

_tiktokapi_stub = MagicMock()
_browser_cookie3_stub = MagicMock()
_requests_stub = MagicMock()

sys.modules.setdefault("TikTokApi", _tiktokapi_stub)
sys.modules.setdefault("browser_cookie3", _browser_cookie3_stub)
sys.modules.setdefault("requests", _requests_stub)

# Now safe to import the module under test at module level.
# This makes patch() target resolution ("modules.tiktok.tiktok_tasks.*") work
# reliably for ALL test classes, including those using fixture-injected patches.
import modules.tiktok.tiktok_tasks as tiktok_tasks  # noqa: E402

# ---------------------------------------------------------------------------
# Block dev-mode file globally (redirect Path.cwd to a temp dir)
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _block_devmode(tmp_path):
    """Redirect Path.cwd() so dev-mode files are never found."""
    with patch.object(Path, "cwd", return_value=tmp_path):
        yield


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

USER_DATA = {
    "userInfo": {
        "user": {
            "id": "12345678901234567",
            "uniqueId": "testuser",
            "nickname": "Test User",
            "avatarLarger": "https://example.com/avatar.jpg",
            "signature": "Hello world @someuser",
            "verified": False,
            "privateAccount": False,
            "commerceUserInfo": {"commerceUser": False},
            "bioLink": {"link": "https://example.com"},
            "nickNameModifyTime": 1609459200,
            "region": "US",
            "duetSetting": 2,
            "stitchSetting": 1,
            "commentSetting": 0,
            "isADVirtual": False,
            "ttSeller": False,
        },
        "stats": {
            "followerCount": 1000,
            "followingCount": 500,
            "heartCount": 50000,
            "videoCount": 3,
            "friendCount": 100,
        },
    }
}

USER_VIDEOS = [
    {
        "id": "vid1",
        "desc": "My first video #dance @friend1",
        "createTime": 1704067200,
        "isPinnedItem": False,
        "video": {
            "cover": "https://example.com/cover1.jpg",
            "duration": 10,
        },
        "statsV2": {
            "collectCount": "100",
            "commentCount": "10",
            "diggCount": "200",
            "playCount": "5000",
            "repostCount": "5",
            "shareCount": "15",
        },
        "textExtra": [{"hashtagName": "dance"}],
        "music": {
            "title": "Cool Song",
            "authorName": "Artist A",
            "original": False,
        },
    },
    {
        "id": "vid2",
        "desc": "Second video #fun #dance @friend2",
        "createTime": 1704153600,
        "isPinnedItem": False,
        "video": {
            "cover": "https://example.com/cover2.jpg",
            "duration": 30,
        },
        "statsV2": {
            "collectCount": "80",
            "commentCount": "20",
            "diggCount": "100",
            "playCount": "3000",
            "repostCount": "3",
            "shareCount": "25",
        },
        "textExtra": [
            {"hashtagName": "fun"},
            {"hashtagName": "dance"},
        ],
        "music": {
            "title": "Cool Song",
            "authorName": "Artist A",
            "original": False,
        },
    },
    {
        "id": "vid3",
        "desc": "Third #fun video",
        "createTime": 1704240000,
        "isPinnedItem": False,
        "video": {
            "cover": "https://example.com/cover3.jpg",
            "duration": 90,
        },
        "statsV2": {
            "collectCount": "60",
            "commentCount": "30",
            "diggCount": "300",
            "playCount": "8000",
            "repostCount": "7",
            "shareCount": "20",
        },
        "textExtra": [{"hashtagName": "fun"}],
        "music": {
            "title": "Another Track",
            "authorName": "Artist B",
            "original": True,
        },
    },
]


@pytest.fixture
def mock_cookies_found():
    """Simulate msToken cookie present."""
    with patch.object(
        tiktok_tasks,
        "get_tiktok_cookies",
        return_value={"found": True, "cookies": {"msToken": "fake-ms-token"}},
    ):
        yield


@pytest.fixture
def mock_cookies_missing():
    """Simulate no TikTok cookies available."""
    with patch.object(
        tiktok_tasks,
        "get_tiktok_cookies",
        return_value={"found": False, "cookies": {}},
    ):
        yield


@pytest.fixture
def mock_api_call():
    """Mock the run_get_user_info sync wrapper."""
    with patch.object(
        tiktok_tasks,
        "run_get_user_info",
        return_value=(USER_DATA, USER_VIDEOS),
    ):
        yield


@pytest.fixture
def mock_analize_rrss():
    """Mock analize_rrss to return empty analysis."""
    with patch.object(
        tiktok_tasks,
        "analize_rrss",
        return_value={},
    ):
        yield


# ===========================================================================
# Task 1.1 — Golden file
# ===========================================================================


class TestGoldenFile:
    """Golden file must exist and have correct schema."""

    def test_golden_file_exists(self):
        golden_path = Path(__file__).parent.parent / "outputs" / "output-tiktok.json"
        assert golden_path.exists(), "output-tiktok.json must exist in backend/outputs/"

    def test_golden_file_is_valid_json(self):
        golden_path = Path(__file__).parent.parent / "outputs" / "output-tiktok.json"
        data = json.loads(golden_path.read_text())
        assert isinstance(data, list)

    def test_golden_file_has_required_keys(self):
        golden_path = Path(__file__).parent.parent / "outputs" / "output-tiktok.json"
        data = json.loads(golden_path.read_text())
        keys = [next(iter(item.keys())) for item in data if isinstance(item, dict)]
        for required in (
            "module",
            "param",
            "validation",
            "raw",
            "graphic",
            "profile",
            "timeline",
        ):
            assert required in keys, f"Golden file missing key: {required}"

    def test_golden_file_module_is_tiktok(self):
        golden_path = Path(__file__).parent.parent / "outputs" / "output-tiktok.json"
        data = json.loads(golden_path.read_text())
        module = next(item["module"] for item in data if "module" in item)
        assert module == "tiktok"

    def test_golden_file_has_new_graphic_keys(self):
        """Golden file must include all new enrichment graphic sections."""
        golden_path = Path(__file__).parent.parent / "outputs" / "output-tiktok.json"
        data = json.loads(golden_path.read_text())
        graphic = next(item["graphic"] for item in data if "graphic" in item)
        graphic_keys = {next(iter(g.keys())) for g in graphic}
        for key in (
            "engagement",
            "language",
            "popularity",
            "approval",
            "soundtrack",
            "users",
            "duration",
            "postsvsreposts",
        ):
            assert key in graphic_keys, f"Golden file graphic missing key: {key}"

    def test_golden_file_engagement_has_7_items(self):
        """Engagement graphic must have exactly 7 items."""
        golden_path = Path(__file__).parent.parent / "outputs" / "output-tiktok.json"
        data = json.loads(golden_path.read_text())
        graphic = next(item["graphic"] for item in data if "graphic" in item)
        engagement = next(g["engagement"] for g in graphic if "engagement" in g)
        assert len(engagement) == 7

    def test_golden_file_has_new_gather_items(self):
        """Golden file tiktok gather must include new privacy/flag/ratio items."""
        golden_path = Path(__file__).parent.parent / "outputs" / "output-tiktok.json"
        data = json.loads(golden_path.read_text())
        graphic = next(item["graphic"] for item in data if "graphic" in item)
        gather = next(g["tiktok"] for g in graphic if "tiktok" in g)
        titles = {n["title"] for n in gather}
        for expected in ("F/F Ratio", "Duet", "Stitch", "Comments"):
            assert expected in titles, f"Golden file gather missing: {expected}"

    def test_golden_file_video_has_music_and_duration(self):
        """Video objects in golden file must include music and duration fields."""
        golden_path = Path(__file__).parent.parent / "outputs" / "output-tiktok.json"
        data = json.loads(golden_path.read_text())
        raw = next(item["raw"] for item in data if "raw" in item)
        video = raw["user_video"][0]
        assert "music" in video, "Video must have music field"
        assert "duration" in video["video"], "Video must have duration in video object"

    def test_golden_file_user_has_privacy_fields(self):
        """User object must include privacy setting fields."""
        golden_path = Path(__file__).parent.parent / "outputs" / "output-tiktok.json"
        data = json.loads(golden_path.read_text())
        raw = next(item["raw"] for item in data if "raw" in item)
        user = raw["user_data"]["userInfo"]["user"]
        for field in ("duetSetting", "stitchSetting", "commentSetting"):
            assert field in user, f"User object missing field: {field}"

    def test_dev_mode_returns_golden_json(self, tmp_path):
        """When output file exists, decorator returns it as-is."""
        golden = [
            {"module": "tiktok"},
            {"param": "testuser"},
            {"validation": "no"},
            {"raw": {}},
            {"graphic": []},
            {"profile": []},
            {"timeline": []},
        ]
        outputs = tmp_path / "outputs"
        outputs.mkdir()
        (outputs / "output-tiktok.json").write_text(json.dumps(golden))

        with (
            patch.object(Path, "cwd", return_value=tmp_path),
            patch("factories.task_wrapper.time.sleep"),
        ):
            result = tiktok_tasks.p_tiktok("testuser")

        assert result == golden


# ===========================================================================
# Task 1.2 — @iky_task decorator, p_tiktok + t_tiktok alias
# ===========================================================================


class TestDecoratorAndAlias:
    """Module must use @iky_task; t_tiktok must be the same object as p_tiktok."""

    def test_t_tiktok_is_same_as_p_tiktok(self):
        assert tiktok_tasks.t_tiktok is tiktok_tasks.p_tiktok

    def test_celery_task_name(self):
        """Registered Celery name must match MODULE_REGISTRY path."""
        assert hasattr(tiktok_tasks.p_tiktok, "name")
        assert tiktok_tasks.p_tiktok.name == "modules.tiktok.tiktok_tasks.t_tiktok"

    def test_t_tiktok_is_callable(
        self, mock_cookies_found, mock_api_call, mock_analize_rrss
    ):
        result = tiktok_tasks.t_tiktok("testuser")
        assert isinstance(result, list)


# ===========================================================================
# Task 1.3 — Signature cleanup (no from_m, get_tiktok_cookies exists)
# ===========================================================================


class TestSignatureCleanup:
    """from_m must be gone; get_tiktok_cookies must exist."""

    def test_no_from_m_in_signature(self):
        sig = inspect.signature(tiktok_tasks.p_tiktok)
        param_names = list(sig.parameters.keys())
        assert "from_m" not in param_names

    def test_signature_has_username_and_num(self):
        sig = inspect.signature(tiktok_tasks.p_tiktok)
        params = sig.parameters
        assert "username" in params
        assert "num" in params
        assert params["num"].default == 15

    def test_get_tiktok_cookies_exists(self):
        assert callable(tiktok_tasks.get_tiktok_cookies)

    def test_get_twitter_cookies_does_not_exist(self):
        assert not hasattr(tiktok_tasks, "get_twitter_cookies"), (
            "get_twitter_cookies must not exist — rename to get_tiktok_cookies"
        )

    def test_no_shell_true_in_source(self):
        """Source must not contain shell=True."""
        source_path = (
            Path(__file__).parent.parent / "modules" / "tiktok" / "tiktok_tasks.py"
        )
        content = source_path.read_text()
        assert "shell=True" not in content, "shell=True must be removed"

    def test_no_install_playwright_in_source(self):
        """Source must not contain install_playwright."""
        source_path = (
            Path(__file__).parent.parent / "modules" / "tiktok" / "tiktok_tasks.py"
        )
        content = source_path.read_text()
        assert "install_playwright" not in content, (
            "install_playwright() must be removed"
        )


# ===========================================================================
# Task 2.1 — Live API path output structure
# ===========================================================================


class TestLiveApiPath:
    """Live API path must return all required output sections."""

    def test_live_output_has_required_keys(
        self, mock_cookies_found, mock_api_call, mock_analize_rrss
    ):
        result = tiktok_tasks.p_tiktok("testuser")
        assert isinstance(result, list)

        keys = [next(iter(item.keys())) for item in result if isinstance(item, dict)]
        for required in (
            "module",
            "param",
            "validation",
            "raw",
            "graphic",
            "profile",
            "timeline",
        ):
            assert required in keys, f"Output missing key: {required}"

    def test_live_output_module_is_tiktok(
        self, mock_cookies_found, mock_api_call, mock_analize_rrss
    ):
        result = tiktok_tasks.p_tiktok("testuser")
        module = next(item["module"] for item in result if "module" in item)
        assert module == "tiktok"

    def test_live_output_param_matches_input(
        self, mock_cookies_found, mock_api_call, mock_analize_rrss
    ):
        result = tiktok_tasks.p_tiktok("mytestuser")
        param = next(item["param"] for item in result if "param" in item)
        assert param == "mytestuser"

    def test_live_output_validation_is_no(
        self, mock_cookies_found, mock_api_call, mock_analize_rrss
    ):
        """Validation is always 'no' (from_m removed, hardcoded)."""
        result = tiktok_tasks.p_tiktok("testuser")
        validation = next(item["validation"] for item in result if "validation" in item)
        assert validation == "no"

    def test_live_output_tasks_section_present(
        self, mock_cookies_found, mock_api_call, mock_analize_rrss
    ):
        result = tiktok_tasks.p_tiktok("testuser")
        keys = [next(iter(item.keys())) for item in result if isinstance(item, dict)]
        assert "tasks" in keys

    def test_live_output_has_new_graphic_keys(
        self, mock_cookies_found, mock_api_call, mock_analize_rrss
    ):
        """Live output must include all new enrichment graphic sections."""
        result = tiktok_tasks.p_tiktok("testuser")
        graphic = next(item["graphic"] for item in result if "graphic" in item)
        graphic_keys = {next(iter(g.keys())) for g in graphic}
        for key in (
            "engagement",
            "popularity",
            "approval",
            "soundtrack",
            "users",
            "duration",
            "postsvsreposts",
        ):
            assert key in graphic_keys, f"Live output graphic missing key: {key}"

    def test_live_output_engagement_has_7_items(
        self, mock_cookies_found, mock_api_call, mock_analize_rrss
    ):
        """Engagement must have 7 items (not just 1)."""
        result = tiktok_tasks.p_tiktok("testuser")
        graphic = next(item["graphic"] for item in result if "graphic" in item)
        engagement = next(g["engagement"] for g in graphic if "engagement" in g)
        assert len(engagement) == 7

    def test_live_output_gather_has_privacy_flags(
        self, mock_cookies_found, mock_api_call, mock_analize_rrss
    ):
        """Gather must include privacy settings and boolean flags."""
        result = tiktok_tasks.p_tiktok("testuser")
        graphic = next(item["graphic"] for item in result if "graphic" in item)
        gather = next(g["tiktok"] for g in graphic if "tiktok" in g)
        titles = {n["title"] for n in gather}
        for expected in (
            "Duet",
            "Stitch",
            "Comments",
            "AI Virtual Account",
            "TikTok Shop Seller",
            "F/F Ratio",
        ):
            assert expected in titles, f"Gather missing: {expected}"


# ===========================================================================
# Task 2.2 — HTTP fallback path
# ===========================================================================


class TestHttpFallback:
    """Missing cookies must trigger fallback, not hard-crash."""

    def test_fallback_called_when_no_cookies(self, mock_cookies_missing):
        fallback_data = {
            "userInfo": {
                "user": {
                    "id": "999",
                    "uniqueId": "fallbackuser",
                    "nickname": "Fallback User",
                    "avatarLarger": "https://example.com/avatar.jpg",
                    "signature": "",
                    "verified": False,
                    "privateAccount": False,
                    "commerceUserInfo": {"commerceUser": False},
                    "region": "AR",
                },
                "stats": {
                    "followerCount": 500,
                    "followingCount": 200,
                    "heartCount": 10000,
                    "videoCount": 0,
                    "friendCount": 50,
                },
            }
        }
        with patch.object(
            tiktok_tasks,
            "http_fallback_profile",
            return_value=fallback_data,
        ):
            result = tiktok_tasks.p_tiktok("fallbackuser")

        assert isinstance(result, list)
        keys = [next(iter(item.keys())) for item in result if isinstance(item, dict)]
        assert "module" in keys
        assert "raw" in keys

    def test_fallback_failure_returns_warning_via_decorator(self, mock_cookies_missing):
        """If fallback also fails, decorator catches and returns Warning."""
        with patch.object(
            tiktok_tasks,
            "http_fallback_profile",
            side_effect=RuntimeError("iKy - HTTP fallback failed"),
        ):
            result = tiktok_tasks.p_tiktok("baduser")

        raw = next(item["raw"] for item in result if "raw" in item)
        assert isinstance(raw, list)
        assert raw[0]["status"] == "Warning"

    def test_fallback_output_has_module_param_raw_graphic(self, mock_cookies_missing):
        """Fallback output must have at minimum: module, param, validation, raw, graphic."""
        fallback_data = {
            "userInfo": {
                "user": {
                    "uniqueId": "fbuser",
                    "nickname": "FB User",
                    "avatarLarger": "",
                    "region": "BR",
                },
                "stats": {"followerCount": 100, "followingCount": 50},
            }
        }
        with patch.object(
            tiktok_tasks,
            "http_fallback_profile",
            return_value=fallback_data,
        ):
            result = tiktok_tasks.p_tiktok("fbuser")

        keys = [next(iter(item.keys())) for item in result if isinstance(item, dict)]
        for required in ("module", "param", "validation", "raw", "graphic"):
            assert required in keys

    def test_fallback_calls_enrich_with_empty_videos(self, mock_cookies_missing):
        """Fallback must call enrich_output so profile-level enrichments appear."""
        fallback_data = {
            "userInfo": {
                "user": {
                    "uniqueId": "fbuser2",
                    "nickname": "FB User 2",
                    "avatarLarger": "",
                    "region": "MX",
                    "duetSetting": 0,
                    "stitchSetting": 2,
                    "commentSetting": 1,
                    "isADVirtual": False,
                    "ttSeller": False,
                },
                "stats": {"followerCount": 5000, "followingCount": 100},
            }
        }
        with patch.object(
            tiktok_tasks,
            "http_fallback_profile",
            return_value=fallback_data,
        ):
            result = tiktok_tasks.p_tiktok("fbuser2")

        graphic = next(item["graphic"] for item in result if "graphic" in item)
        graphic_keys = {next(iter(g.keys())) for g in graphic}
        # Profile-level sections must exist even in fallback
        assert "popularity" in graphic_keys
        assert "approval" in graphic_keys
        # Video-dependent sections should be empty (empty list values)
        soundtrack = next(g["soundtrack"] for g in graphic if "soundtrack" in g)
        assert soundtrack == []
        duration = next(g["duration"] for g in graphic if "duration" in g)
        assert duration == []


# ===========================================================================
# Task 3.1 — Enrichment helpers
# ===========================================================================


class TestEnrichmentHelpers:
    """Unit tests for pure enrichment functions."""

    def test_engagement_rate_correct_math(self):
        """(avg_likes + avg_comments + avg_shares) / followers."""
        # videos: likes [100,200,300], comments [10,20,30], shares [5,10,15]
        videos = [
            {"statsV2": {"diggCount": "100", "commentCount": "10", "shareCount": "5"}},
            {"statsV2": {"diggCount": "200", "commentCount": "20", "shareCount": "10"}},
            {"statsV2": {"diggCount": "300", "commentCount": "30", "shareCount": "15"}},
        ]
        # avg_likes=200, avg_comments=20, avg_shares=10 → 230/1000 = 0.23
        rate = tiktok_tasks.compute_engagement_rate(videos, followers=1000)
        assert rate is not None
        assert abs(rate - 0.23) < 1e-9

    def test_engagement_rate_zero_followers_returns_none(self):
        videos = [
            {"statsV2": {"diggCount": "100", "commentCount": "10", "shareCount": "5"}}
        ]
        assert tiktok_tasks.compute_engagement_rate(videos, followers=0) is None

    def test_engagement_rate_empty_videos_returns_none(self):
        assert tiktok_tasks.compute_engagement_rate([], followers=1000) is None

    def test_extract_mentions_basic(self):
        captions = ["hey @user1 check this @user2", "love you @user1"]
        result = tiktok_tasks.extract_mentions(captions)
        labels = {item["label"] for item in result}
        assert "user1" in labels
        assert "user2" in labels
        # user1 appears twice
        user1_entry = next(item for item in result if item["label"] == "user1")
        assert user1_entry["value"] == 2

    def test_extract_mentions_empty(self):
        assert tiktok_tasks.extract_mentions([]) == []
        assert tiktok_tasks.extract_mentions(["no mentions here"]) == []

    def test_detect_language_english(self):
        assert (
            tiktok_tasks.detect_language(["hello world", "great video today"]) == "en"
        )

    def test_detect_language_cjk(self):
        assert tiktok_tasks.detect_language(["你好世界", "很棒的视频"]) == "zh"

    def test_detect_language_cyrillic(self):
        assert tiktok_tasks.detect_language(["Привет мир"]) == "ru"

    def test_detect_language_arabic(self):
        assert tiktok_tasks.detect_language(["مرحبا بالعالم"]) == "ar"

    def test_detect_language_empty_returns_none(self):
        assert tiktok_tasks.detect_language([]) is None

    def test_enrichment_in_live_output(
        self, mock_cookies_found, mock_api_call, mock_analize_rrss
    ):
        """Live output should contain enrichment nodes (region, engagement)."""
        result = tiktok_tasks.p_tiktok("testuser")
        graphic = next(item["graphic"] for item in result if "graphic" in item)

        tiktok_nodes = graphic[0].get("tiktok", [])
        node_titles = {n.get("title") for n in tiktok_nodes}
        assert "Region" in node_titles, "Region enrichment node missing"


# ===========================================================================
# Task 3.2 — Code quality: no deprecated datetime
# ===========================================================================


class TestCodeQuality:
    """Source-level checks for deprecated patterns and dead code."""

    def _get_source(self) -> str:
        source_path = (
            Path(__file__).parent.parent / "modules" / "tiktok" / "tiktok_tasks.py"
        )
        return source_path.read_text()

    def test_no_utcfromtimestamp(self):
        """datetime.utcfromtimestamp() is deprecated — must not be present."""
        assert "utcfromtimestamp" not in self._get_source(), (
            "Use datetime.fromtimestamp(ts, tz=UTC) instead"
        )

    def test_uses_tz_aware_datetime(self):
        """Must use tz-aware datetime — either 'UTC' alias or 'timezone.utc'."""
        source = self._get_source()
        # Implementation uses 'from datetime import UTC' and 'tz=UTC' — both are valid
        uses_utc_alias = "tz=UTC" in source or "from datetime import UTC" in source
        uses_timezone_utc = "timezone.utc" in source
        assert uses_utc_alias or uses_timezone_utc, (
            "Source must use tz-aware datetime (UTC alias or timezone.utc)"
        )

    def test_no_shell_true(self):
        assert "shell=True" not in self._get_source()

    def test_no_get_twitter_cookies(self):
        assert "get_twitter_cookies" not in self._get_source()

    def test_no_install_playwright_fn(self):
        assert "install_playwright" not in self._get_source()

    def test_get_tiktok_cookies_defined(self):
        assert "def get_tiktok_cookies" in self._get_source()

    def test_source_is_valid_python(self):
        """Source must parse without syntax errors."""
        source_path = (
            Path(__file__).parent.parent / "modules" / "tiktok" / "tiktok_tasks.py"
        )
        ast.parse(source_path.read_text())


# ===========================================================================
# Task 4.1 — Error path tests (via decorator)
# ===========================================================================


class TestErrorPaths:
    """Decorator must handle iKy and generic errors correctly."""

    def test_iky_error_returns_warning(self, mock_cookies_missing):
        with patch.object(
            tiktok_tasks,
            "http_fallback_profile",
            side_effect=Exception("iKy - User Not Found"),
        ):
            result = tiktok_tasks.p_tiktok("nosuchuser")

        raw = next(item["raw"] for item in result if "raw" in item)
        assert raw[0]["status"] == "Warning"
        assert raw[0]["reason"] == "User Not Found"

    def test_generic_error_returns_fail(self, mock_cookies_found):
        with patch.object(
            tiktok_tasks,
            "run_get_user_info",
            side_effect=RuntimeError("network error"),
        ):
            result = tiktok_tasks.p_tiktok("testuser")

        raw = next(item["raw"] for item in result if "raw" in item)
        assert raw[0]["status"] == "Fail"
        assert raw[0]["reason"] == "network error"

    def test_error_includes_traceback(self, mock_cookies_found):
        with patch.object(
            tiktok_tasks,
            "run_get_user_info",
            side_effect=RuntimeError("traceback test"),
        ):
            result = tiktok_tasks.p_tiktok("testuser")

        raw = next(item["raw"] for item in result if "raw" in item)
        assert "traceback" in raw[0]
        assert "traceback test" in raw[0]["traceback"]

    def test_error_output_structure(self, mock_cookies_found):
        with patch.object(
            tiktok_tasks,
            "run_get_user_info",
            side_effect=RuntimeError("err"),
        ):
            result = tiktok_tasks.p_tiktok("testuser")

        keys = [next(iter(item.keys())) for item in result if isinstance(item, dict)]
        assert keys == ["module", "param", "validation", "raw"]
        assert result[0]["module"] == "tiktok"
        assert result[2]["validation"] == "not_used"


# ===========================================================================
# Phase 4 — New helper unit tests (tasks 4.1)
# ===========================================================================


class TestEngagementBreakdown:
    """Unit tests for compute_engagement_breakdown."""

    def test_returns_7_items(self):
        result = tiktok_tasks.compute_engagement_breakdown(USER_VIDEOS, followers=1000)
        assert len(result) == 7

    def test_correct_names_order(self):
        result = tiktok_tasks.compute_engagement_breakdown(USER_VIDEOS, followers=1000)
        names = [r["name"] for r in result]
        assert names == [
            "Avg Likes",
            "Avg Comments",
            "Avg Shares",
            "Avg Plays",
            "Avg Collects",
            "Avg Reposts",
            "Rate%",
        ]

    def test_correct_math_from_spec(self):
        """Spec scenario: 3 videos with known stats, 1000 followers."""
        # USER_VIDEOS has: likes [200,100,300], comments [10,20,30], shares [15,25,20]
        # plays [5000,3000,8000], collects [100,80,60], reposts [5,3,7]
        result = tiktok_tasks.compute_engagement_breakdown(USER_VIDEOS, followers=1000)
        avg_likes = next(r for r in result if r["name"] == "Avg Likes")
        avg_comments = next(r for r in result if r["name"] == "Avg Comments")
        avg_shares = next(r for r in result if r["name"] == "Avg Shares")
        avg_plays = next(r for r in result if r["name"] == "Avg Plays")
        assert avg_likes["value"] == round((200 + 100 + 300) / 3, 2)
        assert avg_comments["value"] == round((10 + 20 + 30) / 3, 2)
        assert avg_shares["value"] == round((15 + 25 + 20) / 3, 2)
        assert avg_plays["value"] == round((5000 + 3000 + 8000) / 3, 2)

    def test_rate_percent_math(self):
        """Rate% = (avg_likes + avg_comments + avg_shares) / followers * 100."""
        videos = [
            {
                "statsV2": {
                    "diggCount": "100",
                    "commentCount": "10",
                    "shareCount": "5",
                    "playCount": "1000",
                    "collectCount": "2",
                    "repostCount": "1",
                }
            },
            {
                "statsV2": {
                    "diggCount": "200",
                    "commentCount": "20",
                    "shareCount": "10",
                    "playCount": "2000",
                    "collectCount": "4",
                    "repostCount": "2",
                }
            },
            {
                "statsV2": {
                    "diggCount": "300",
                    "commentCount": "30",
                    "shareCount": "15",
                    "playCount": "3000",
                    "collectCount": "6",
                    "repostCount": "3",
                }
            },
        ]
        result = tiktok_tasks.compute_engagement_breakdown(videos, followers=1000)
        rate_item = next(r for r in result if r["name"] == "Rate%")
        # avg_likes=200, avg_comments=20, avg_shares=10 → 230/1000*100=23.0
        assert rate_item["value"] == 23.0

    def test_zero_videos_all_none(self):
        result = tiktok_tasks.compute_engagement_breakdown([], followers=1000)
        assert len(result) == 7
        assert all(r["value"] is None for r in result)

    def test_zero_followers_all_none(self):
        result = tiktok_tasks.compute_engagement_breakdown(USER_VIDEOS, followers=0)
        assert len(result) == 7
        assert all(r["value"] is None for r in result)

    def test_missing_stats_fields_graceful(self):
        """Videos without statsV2 keys must not crash."""
        videos = [{"statsV2": {}}, {"statsV2": {}}]
        result = tiktok_tasks.compute_engagement_breakdown(videos, followers=100)
        assert len(result) == 7
        # All avgs should be 0 when stats fields are missing
        avg_likes = next(r for r in result if r["name"] == "Avg Likes")
        assert avg_likes["value"] == 0.0


class TestFFRatio:
    """Unit tests for compute_ff_ratio."""

    def test_normal_ratio(self):
        result = tiktok_tasks.compute_ff_ratio(followers=10000, following=500)
        assert result == 20.0

    def test_rounds_to_2_decimals(self):
        result = tiktok_tasks.compute_ff_ratio(followers=1000, following=3)
        assert result is not None
        assert round(result, 2) == result

    def test_zero_followers_returns_none(self):
        assert tiktok_tasks.compute_ff_ratio(followers=0, following=500) is None

    def test_zero_following_uses_max_1(self):
        """following=0 → use max(0, 1) = 1."""
        result = tiktok_tasks.compute_ff_ratio(followers=100, following=0)
        assert result == 100.0

    def test_equal_followers_following(self):
        result = tiktok_tasks.compute_ff_ratio(followers=500, following=500)
        assert result == 1.0


class TestPopularityApproval:
    """Unit tests for build_popularity_section and build_approval_section."""

    def test_popularity_has_3_items(self):
        stats = {"followerCount": 1000, "followingCount": 50, "friendCount": 30}
        result = tiktok_tasks.build_popularity_section(stats)
        assert len(result) == 3

    def test_popularity_correct_values(self):
        stats = {"followerCount": 1000, "followingCount": 50, "friendCount": 30}
        result = tiktok_tasks.build_popularity_section(stats)
        titles = {r["title"]: r["value"] for r in result}
        assert titles["Followers"] == 1000
        assert titles["Following"] == 50
        assert titles["Friends"] == 30

    def test_popularity_missing_stats_defaults_to_0(self):
        result = tiktok_tasks.build_popularity_section({})
        assert len(result) == 3
        assert all(r["value"] == 0 for r in result)

    def test_approval_has_2_items(self):
        stats = {"videoCount": 100, "heartCount": 50000}
        result = tiktok_tasks.build_approval_section(stats)
        assert len(result) == 2

    def test_approval_correct_values(self):
        stats = {"videoCount": 100, "heartCount": 50000}
        result = tiktok_tasks.build_approval_section(stats)
        titles = {r["title"]: r["value"] for r in result}
        assert titles["Videos"] == 100
        assert titles["Likes"] == 50000

    def test_approval_missing_stats_defaults_to_0(self):
        result = tiktok_tasks.build_approval_section({})
        assert all(r["value"] == 0 for r in result)


class TestLanguagePerVideo:
    """Unit tests for detect_language_per_video."""

    def test_english_distribution(self):
        captions = ["hello world", "great dance", "awesome video"]
        result = tiktok_tasks.detect_language_per_video(captions)
        assert len(result) == 1
        assert result[0]["name"] == "en"
        assert result[0]["value"] == 3

    def test_mixed_languages(self):
        captions = ["hello", "world", "你好", "世界", "hola"]
        result = tiktok_tasks.detect_language_per_video(captions)
        names = {r["name"]: r["value"] for r in result}
        assert names.get("en") == 3  # hello, world, hola → en
        assert names.get("zh") == 2  # 你好, 世界 → zh

    def test_spec_scenario_3en_2es(self):
        """Spec: 5 captions, 3 English, 2 that detect as English (Latin)."""
        # All Latin chars detect as English in the regex heuristic
        captions = [
            "hello english",
            "great dance",
            "awesome video",
            "hola mundo",
            "baile increible",
        ]
        result = tiktok_tasks.detect_language_per_video(captions)
        # All are Latin → all "en" with heuristic
        total = sum(r["value"] for r in result)
        assert total == 5

    def test_empty_captions_returns_empty_list(self):
        assert tiktok_tasks.detect_language_per_video([]) == []

    def test_blank_captions_ignored(self):
        captions = ["", "   ", "\t"]
        assert tiktok_tasks.detect_language_per_video(captions) == []

    def test_sorted_by_count_desc(self):
        captions = ["en one", "你好", "en two", "en three"]
        result = tiktok_tasks.detect_language_per_video(captions)
        assert result[0]["value"] >= result[-1]["value"]

    def test_cjk_detection(self):
        captions = ["你好世界", "很棒的视频"]
        result = tiktok_tasks.detect_language_per_video(captions)
        assert result[0]["name"] == "zh"
        assert result[0]["value"] == 2

    def test_cyrillic_detection(self):
        captions = ["Привет мир", "Отличное видео"]
        result = tiktok_tasks.detect_language_per_video(captions)
        assert result[0]["name"] == "ru"

    def test_arabic_detection(self):
        captions = ["مرحبا بالعالم"]
        result = tiktok_tasks.detect_language_per_video(captions)
        assert result[0]["name"] == "ar"


class TestAvgVideosPerDay:
    """Unit tests for compute_avg_videos_per_day."""

    def test_correct_math(self):
        """30 videos spanning 60 days → 0.5."""
        # Use 31 timestamps spanning 60 days
        from datetime import UTC, datetime

        start = int(datetime(2024, 1, 1, tzinfo=UTC).timestamp())
        end = int(datetime(2024, 3, 1, tzinfo=UTC).timestamp())
        # Simulate 30 videos across 60 days
        timestamps = [start] * 15 + [end] * 15
        result = tiktok_tasks.compute_avg_videos_per_day(timestamps)
        assert result is not None
        # 30 / 60 = 0.5
        assert result == 0.5

    def test_single_timestamp_returns_none(self):
        assert tiktok_tasks.compute_avg_videos_per_day([1704067200]) is None

    def test_empty_returns_none(self):
        assert tiktok_tasks.compute_avg_videos_per_day([]) is None

    def test_same_day_timestamps_uses_max_1(self):
        """Same-day timestamps: span.days = 0 → use max(0, 1) = 1."""
        ts = 1704067200
        result = tiktok_tasks.compute_avg_videos_per_day([ts, ts + 3600])
        assert result is not None
        # 2 videos / 1 day = 2.0
        assert result == 2.0

    def test_rounding(self):
        from datetime import UTC, datetime

        start = int(datetime(2024, 1, 1, tzinfo=UTC).timestamp())
        end = int(datetime(2024, 4, 10, tzinfo=UTC).timestamp())  # 100 days
        timestamps = [start, end]
        result = tiktok_tasks.compute_avg_videos_per_day(timestamps)
        assert result is not None
        assert isinstance(result, float)


class TestPrivacySettings:
    """Unit tests for format_privacy_settings."""

    def test_all_settings_present(self):
        user_data = {
            "userInfo": {
                "user": {
                    "duetSetting": 2,
                    "stitchSetting": 1,
                    "commentSetting": 0,
                }
            }
        }
        result = tiktok_tasks.format_privacy_settings(user_data)
        assert len(result) == 3
        titles = {r["title"]: r["subtitle"] for r in result}
        assert titles["Duet"] == "Off"
        assert titles["Stitch"] == "Friends Only"
        assert titles["Comments"] == "All"

    def test_missing_settings_skipped(self):
        """When fields are absent, they are skipped."""
        user_data = {"userInfo": {"user": {}}}
        result = tiktok_tasks.format_privacy_settings(user_data)
        assert result == []

    def test_partial_settings(self):
        user_data = {"userInfo": {"user": {"duetSetting": 0}}}
        result = tiktok_tasks.format_privacy_settings(user_data)
        assert len(result) == 1
        assert result[0]["title"] == "Duet"
        assert result[0]["subtitle"] == "All"

    def test_zero_everyone_label(self):
        user_data = {"userInfo": {"user": {"commentSetting": 0}}}
        result = tiktok_tasks.format_privacy_settings(user_data)
        assert result[0]["subtitle"] == "All"

    def test_one_friends_label(self):
        user_data = {"userInfo": {"user": {"commentSetting": 1}}}
        result = tiktok_tasks.format_privacy_settings(user_data)
        assert result[0]["subtitle"] == "Friends Only"

    def test_two_off_label(self):
        user_data = {"userInfo": {"user": {"commentSetting": 2}}}
        result = tiktok_tasks.format_privacy_settings(user_data)
        assert result[0]["subtitle"] == "Off"


class TestSoundtrackChart:
    """Unit tests for build_soundtrack_chart."""

    def test_basic_aggregation(self):
        videos = [
            {"music": {"title": "Song A", "authorName": "Artist1", "original": False}},
            {"music": {"title": "Song A", "authorName": "Artist1", "original": False}},
            {"music": {"title": "Song B", "authorName": "Artist2", "original": True}},
        ]
        result = tiktok_tasks.build_soundtrack_chart(videos)
        assert len(result) == 2
        assert result[0]["name"] == "Song A - Artist1"
        assert result[0]["value"] == 2
        assert result[0]["original"] is False
        assert result[1]["name"] == "Song B - Artist2"
        assert result[1]["original"] is True

    def test_original_flag_or_logic(self):
        """original=True on ANY occurrence → original=True for the track."""
        videos = [
            {"music": {"title": "Track", "authorName": "Me", "original": False}},
            {"music": {"title": "Track", "authorName": "Me", "original": True}},
        ]
        result = tiktok_tasks.build_soundtrack_chart(videos)
        assert result[0]["original"] is True

    def test_no_music_returns_empty(self):
        videos = [{"desc": "no music here"}, {"desc": "also no music"}]
        assert tiktok_tasks.build_soundtrack_chart(videos) == []

    def test_empty_videos_returns_empty(self):
        assert tiktok_tasks.build_soundtrack_chart([]) == []

    def test_sorted_by_count_desc(self):
        videos = [
            {"music": {"title": "A", "authorName": "x", "original": False}},
            {"music": {"title": "B", "authorName": "y", "original": False}},
            {"music": {"title": "B", "authorName": "y", "original": False}},
            {"music": {"title": "C", "authorName": "z", "original": False}},
            {"music": {"title": "C", "authorName": "z", "original": False}},
            {"music": {"title": "C", "authorName": "z", "original": False}},
        ]
        result = tiktok_tasks.build_soundtrack_chart(videos)
        assert result[0]["value"] >= result[1]["value"]

    def test_title_only_music(self):
        videos = [
            {"music": {"title": "Solo Track", "authorName": "", "original": False}}
        ]
        result = tiktok_tasks.build_soundtrack_chart(videos)
        assert len(result) == 1
        assert result[0]["name"] == "Solo Track"

    def test_spec_scenario(self):
        """Spec: 3 use 'Song A - Artist1' (orig=False), 2 use 'Original Sound - @user' (orig=True)."""
        videos = [
            {"music": {"title": "Song A", "authorName": "Artist1", "original": False}},
            {"music": {"title": "Song A", "authorName": "Artist1", "original": False}},
            {"music": {"title": "Song A", "authorName": "Artist1", "original": False}},
            {
                "music": {
                    "title": "Original Sound",
                    "authorName": "@user",
                    "original": True,
                }
            },
            {
                "music": {
                    "title": "Original Sound",
                    "authorName": "@user",
                    "original": True,
                }
            },
        ]
        result = tiktok_tasks.build_soundtrack_chart(videos)
        assert len(result) == 2
        assert result[0]["value"] == 3  # sorted desc
        assert result[0]["original"] is False
        assert result[1]["value"] == 2
        assert result[1]["original"] is True


class TestUsersGraph:
    """Unit tests for build_users_graph."""

    def test_basic_graph_structure(self):
        mentions = [{"label": "user1", "value": 3}, {"label": "user2", "value": 1}]
        result = tiktok_tasks.build_users_graph(mentions)
        assert len(result) == 3
        # First node is root
        assert result[0]["name-node"] == "Users"
        assert result[0]["title"] == "Users"
        assert result[0]["subtitle"] == ""
        assert result[0]["link"] == "Users"

    def test_user_nodes_format(self):
        mentions = [{"label": "user1", "value": 5}]
        result = tiktok_tasks.build_users_graph(mentions)
        node = result[1]
        assert node["name-node"] == "@user1"
        assert node["title"] == "@user1"
        assert node["subtitle"] == 5
        assert node["link"] == "Users"

    def test_empty_mentions_returns_root_only(self):
        result = tiktok_tasks.build_users_graph([])
        assert len(result) == 1
        assert result[0]["name-node"] == "Users"

    def test_matches_twitter_format(self):
        """Format must match Twitter's users node-link exactly (keys: name-node, title, subtitle, link)."""
        mentions = [{"label": "alice", "value": 2}]
        result = tiktok_tasks.build_users_graph(mentions)
        for node in result:
            assert "name-node" in node
            assert "title" in node
            assert "subtitle" in node
            assert "link" in node

    def test_spec_scenario(self):
        mentions = [{"label": "user1", "value": 3}, {"label": "user2", "value": 1}]
        result = tiktok_tasks.build_users_graph(mentions)
        assert result[1]["name-node"] == "@user1"
        assert result[1]["subtitle"] == 3
        assert result[2]["name-node"] == "@user2"
        assert result[2]["subtitle"] == 1


class TestDurationHistogram:
    """Unit tests for build_duration_histogram."""

    def test_mixed_durations_spec(self):
        """Spec scenario: durations [10, 14, 30, 45, 120] → Short=2, Medium=2, Long=1."""
        videos = [
            {"video": {"duration": 10}},
            {"video": {"duration": 14}},
            {"video": {"duration": 30}},
            {"video": {"duration": 45}},
            {"video": {"duration": 120}},
        ]
        result = tiktok_tasks.build_duration_histogram(videos)
        assert len(result) == 3
        names = {r["name"]: r["value"] for r in result}
        assert names["Short (<15s)"] == 2
        assert names["Medium (15-60s)"] == 2
        assert names["Long (>60s)"] == 1

    def test_empty_videos_returns_empty_list(self):
        assert tiktok_tasks.build_duration_histogram([]) == []

    def test_missing_duration_goes_to_short(self):
        """Missing duration defaults to 0 → Short bucket."""
        videos = [{"video": {}}, {"video": {"duration": None}}]
        result = tiktok_tasks.build_duration_histogram(videos)
        names = {r["name"]: r["value"] for r in result}
        assert names["Short (<15s)"] == 2

    def test_boundary_15s_is_medium(self):
        videos = [{"video": {"duration": 15}}]
        result = tiktok_tasks.build_duration_histogram(videos)
        names = {r["name"]: r["value"] for r in result}
        assert names["Medium (15-60s)"] == 1
        assert names["Short (<15s)"] == 0

    def test_boundary_60s_is_medium(self):
        videos = [{"video": {"duration": 60}}]
        result = tiktok_tasks.build_duration_histogram(videos)
        names = {r["name"]: r["value"] for r in result}
        assert names["Medium (15-60s)"] == 1
        assert names["Long (>60s)"] == 0

    def test_boundary_61s_is_long(self):
        videos = [{"video": {"duration": 61}}]
        result = tiktok_tasks.build_duration_histogram(videos)
        names = {r["name"]: r["value"] for r in result}
        assert names["Long (>60s)"] == 1

    def test_user_videos_fixture(self):
        """Using USER_VIDEOS fixture: vid1=10s (short), vid2=30s (medium), vid3=90s (long)."""
        result = tiktok_tasks.build_duration_histogram(USER_VIDEOS)
        names = {r["name"]: r["value"] for r in result}
        assert names["Short (<15s)"] == 1
        assert names["Medium (15-60s)"] == 1
        assert names["Long (>60s)"] == 1


class TestPostsVsReposts:
    """Unit tests for compute_posts_vs_reposts."""

    def test_basic_calculation(self):
        """Spec scenario: 10 videos, total repostCount=3."""
        videos = [{"statsV2": {"repostCount": "1"}} for _ in range(3)] + [
            {"statsV2": {"repostCount": "0"}} for _ in range(7)
        ]
        result = tiktok_tasks.compute_posts_vs_reposts(videos)
        assert len(result) == 2
        names = {r["name"]: r["value"] for r in result}
        assert names["Original"] == 10
        assert names["Reposts"] == 3

    def test_empty_videos_returns_empty_list(self):
        assert tiktok_tasks.compute_posts_vs_reposts([]) == []

    def test_no_reposts(self):
        videos = [{"statsV2": {"repostCount": "0"}} for _ in range(5)]
        result = tiktok_tasks.compute_posts_vs_reposts(videos)
        names = {r["name"]: r["value"] for r in result}
        assert names["Original"] == 5
        assert names["Reposts"] == 0

    def test_missing_stats_defaults_to_0(self):
        videos = [{"statsV2": {}}, {"statsV2": {}}]
        result = tiktok_tasks.compute_posts_vs_reposts(videos)
        names = {r["name"]: r["value"] for r in result}
        assert names["Original"] == 2
        assert names["Reposts"] == 0

    def test_user_videos_fixture(self):
        """USER_VIDEOS: 3 videos, repostCount [5, 3, 7] → total 15."""
        result = tiktok_tasks.compute_posts_vs_reposts(USER_VIDEOS)
        names = {r["name"]: r["value"] for r in result}
        assert names["Original"] == 3
        assert names["Reposts"] == 15


class TestGatherFlags:
    """Unit tests for extract_gather_flags."""

    def test_both_flags_present_truthy(self):
        user_data = {
            "userInfo": {
                "user": {
                    "isADVirtual": True,
                    "ttSeller": True,
                }
            }
        }
        result = tiktok_tasks.extract_gather_flags(user_data)
        assert len(result) == 2
        titles = {r["title"]: r["subtitle"] for r in result}
        assert titles["AI Virtual Account"] is True
        assert titles["TikTok Shop Seller"] is True

    def test_flags_absent_default_false(self):
        """When fields are absent, they default to False but still appear."""
        user_data = {"userInfo": {"user": {}}}
        result = tiktok_tasks.extract_gather_flags(user_data)
        assert len(result) == 2
        for item in result:
            assert item["subtitle"] is False

    def test_flag_false_value(self):
        user_data = {
            "userInfo": {
                "user": {
                    "isADVirtual": False,
                    "ttSeller": False,
                }
            }
        }
        result = tiktok_tasks.extract_gather_flags(user_data)
        for item in result:
            assert item["subtitle"] is False

    def test_gather_item_structure(self):
        user_data = {"userInfo": {"user": {"isADVirtual": True, "ttSeller": False}}}
        result = tiktok_tasks.extract_gather_flags(user_data)
        for item in result:
            assert "name-node" in item
            assert "title" in item
            assert "subtitle" in item
            assert "icon" in item
            assert "link" in item


# ===========================================================================
# Phase 4 — Integration tests (task 4.2)
# ===========================================================================


class TestIntegrationFullOutput:
    """Integration tests for full output with enrichment."""

    def test_new_graphic_keys_exist(
        self, mock_cookies_found, mock_api_call, mock_analize_rrss
    ):
        """All new graphic keys must be present in live output."""
        result = tiktok_tasks.p_tiktok("testuser")
        graphic = next(item["graphic"] for item in result if "graphic" in item)
        graphic_keys = {next(iter(g.keys())) for g in graphic}
        for key in (
            "engagement",
            "popularity",
            "approval",
            "soundtrack",
            "users",
            "duration",
            "postsvsreposts",
        ):
            assert key in graphic_keys, f"Missing graphic key: {key}"

    def test_engagement_7_items_values_not_none(
        self, mock_cookies_found, mock_api_call, mock_analize_rrss
    ):
        """With real video data, no engagement value should be None."""
        result = tiktok_tasks.p_tiktok("testuser")
        graphic = next(item["graphic"] for item in result if "graphic" in item)
        engagement = next(g["engagement"] for g in graphic if "engagement" in g)
        assert len(engagement) == 7
        for item in engagement:
            assert item["value"] is not None, f"Unexpected None in {item['name']}"

    def test_users_graph_has_root_node(
        self, mock_cookies_found, mock_api_call, mock_analize_rrss
    ):
        """Users graph must always start with root 'Users' node."""
        result = tiktok_tasks.p_tiktok("testuser")
        graphic = next(item["graphic"] for item in result if "graphic" in item)
        users = next(g["users"] for g in graphic if "users" in g)
        assert users[0]["name-node"] == "Users"

    def test_duration_histogram_3_buckets(
        self, mock_cookies_found, mock_api_call, mock_analize_rrss
    ):
        """Duration histogram must have exactly 3 buckets."""
        result = tiktok_tasks.p_tiktok("testuser")
        graphic = next(item["graphic"] for item in result if "graphic" in item)
        duration = next(g["duration"] for g in graphic if "duration" in g)
        assert len(duration) == 3

    def test_gather_has_privacy_and_flags(
        self, mock_cookies_found, mock_api_call, mock_analize_rrss
    ):
        """Gather must include privacy settings (Duet, Stitch, Comments) and flag items."""
        result = tiktok_tasks.p_tiktok("testuser")
        graphic = next(item["graphic"] for item in result if "graphic" in item)
        gather = next(g["tiktok"] for g in graphic if "tiktok" in g)
        titles = {n["title"] for n in gather}
        assert "Duet" in titles
        assert "Stitch" in titles
        assert "Comments" in titles
        assert "AI Virtual Account" in titles
        assert "TikTok Shop Seller" in titles

    # ------------------------------------------------------------------
    # Shared fallback fixture used by multiple fallback-path tests
    # ------------------------------------------------------------------

    FALLBACK_DATA: ClassVar[dict] = {
        "userInfo": {
            "user": {
                "id": "99988877766655544",
                "uniqueId": "fbuser3",
                "nickname": "FB User 3",
                "avatarLarger": "https://example.com/fb_avatar.jpg",
                "signature": "Fallback bio @mention",
                "verified": True,
                "privateAccount": False,
                "commerceUserInfo": {"commerceUser": False},
                "bioLink": {"link": "https://fallback.example.com"},
                "nickNameModifyTime": 1609459200,
                "region": "US",
                "duetSetting": 0,
                "stitchSetting": 1,
                "commentSetting": 2,
                "isADVirtual": False,
                "ttSeller": True,
            },
            "stats": {
                "followerCount": 10000,
                "followingCount": 200,
                "friendCount": 50,
                "heartCount": 500000,
                "videoCount": 100,
            },
        }
    }

    def _run_fallback(self, mock_cookies_missing, data=None):
        """Helper: patch http_fallback_profile and run p_tiktok."""
        payload = data if data is not None else self.FALLBACK_DATA
        with patch.object(
            tiktok_tasks,
            "http_fallback_profile",
            return_value=payload,
        ):
            return tiktok_tasks.p_tiktok("fbuser3")

    def test_fallback_profile_enrichments_present(self, mock_cookies_missing):
        """Fallback path: profile-level enrichments must be present."""
        result = self._run_fallback(mock_cookies_missing)

        graphic = next(item["graphic"] for item in result if "graphic" in item)
        graphic_keys = {next(iter(g.keys())) for g in graphic}

        # Profile-level enrichments: popularity, approval
        assert "popularity" in graphic_keys
        assert "approval" in graphic_keys
        # Video-dependent: empty lists
        duration = next(g["duration"] for g in graphic if "duration" in g)
        assert duration == []
        soundtrack = next(g["soundtrack"] for g in graphic if "soundtrack" in g)
        assert soundtrack == []

    def test_fallback_all_graphic_sections_present(self, mock_cookies_missing):
        """Fallback graphic must contain all sections the API path produces."""
        result = self._run_fallback(mock_cookies_missing)
        graphic = next(item["graphic"] for item in result if "graphic" in item)
        graphic_keys = {next(iter(g.keys())) for g in graphic}

        required_keys = {
            "tiktok",  # gather card root
            "engagement",
            "popularity",
            "approval",
            "soundtrack",
            "users",
            "duration",
            "postsvsreposts",
            "postslist",
            "hashtags",
            "mentions",
            "tagged",
            "hour",
            "week",
            "videos",
            "resume",
            "tiktime",
        }
        missing = required_keys - graphic_keys
        assert not missing, f"Fallback graphic missing sections: {missing}"

    def test_fallback_video_dependent_sections_are_empty(self, mock_cookies_missing):
        """Video-dependent graphic sections must be empty lists in fallback."""
        result = self._run_fallback(mock_cookies_missing)
        graphic = next(item["graphic"] for item in result if "graphic" in item)

        empty_keys = (
            "postslist",
            "hashtags",
            "mentions",
            "tagged",
            "hour",
            "week",
            "tiktime",
        )
        for key in empty_keys:
            value = next(g[key] for g in graphic if key in g)
            assert value == [], f"Expected {key!r} to be [] in fallback, got {value!r}"

    def test_fallback_resume_has_children(self, mock_cookies_missing):
        """Resume sunburst must be populated from stats even without videos."""
        result = self._run_fallback(mock_cookies_missing)
        graphic = next(item["graphic"] for item in result if "graphic" in item)
        resume = next(g["resume"] for g in graphic if "resume" in g)

        assert resume["name"] == "tiktok"
        child_names = {c["name"] for c in resume["children"]}
        assert child_names == {"Follower", "Following", "Friends", "Likes", "Videos"}
        # Values should reflect fixture stats
        totals = {c["name"]: c["total"] for c in resume["children"]}
        assert totals["Follower"] == "10000"
        assert totals["Following"] == "200"
        assert totals["Videos"] == "100"

    def test_fallback_gather_has_all_profile_cards(self, mock_cookies_missing):
        """Fallback gather must include all profile-level cards."""
        result = self._run_fallback(mock_cookies_missing)
        graphic = next(item["graphic"] for item in result if "graphic" in item)
        gather = next(g["tiktok"] for g in graphic if "tiktok" in g)
        titles = {n["title"] for n in gather}

        required_titles = {
            "tiktok",
            "Name",
            "Posts",
            "Followers",
            "Following",
            "Friends",
            "Bio",
            "Likes",
            "Private Account",
            "Username",
            "UserID",
            "Bussiness Account",
            "Verified Account",
        }
        missing = required_titles - titles
        assert not missing, f"Fallback gather missing cards: {missing}"

    def test_fallback_gather_card_values(self, mock_cookies_missing):
        """Fallback gather card values must reflect the profile stats."""
        result = self._run_fallback(mock_cookies_missing)
        graphic = next(item["graphic"] for item in result if "graphic" in item)
        gather = next(g["tiktok"] for g in graphic if "tiktok" in g)
        by_title = {n["title"]: n.get("subtitle") for n in gather}

        assert by_title["Posts"] == 100
        assert by_title["Followers"] == 10000
        assert by_title["Following"] == 200
        assert by_title["Friends"] == 50
        assert by_title["Likes"] == 500000
        assert by_title["Username"] == "fbuser3"
        assert by_title["UserID"] == "99988877766655544"
        assert by_title["Verified Account"] is True
        assert by_title["Private Account"] is False

    def test_fallback_has_tasks_key(self, mock_cookies_missing):
        """Fallback output must include a 'tasks' top-level key."""
        result = self._run_fallback(mock_cookies_missing)
        keys = [next(iter(item.keys())) for item in result if isinstance(item, dict)]
        assert "tasks" in keys, "Fallback output missing top-level 'tasks' key"

    def test_fallback_timeline_has_nickname_modify_time(self, mock_cookies_missing):
        """Fallback timeline must include nickNameModifyTime entry when present."""
        result = self._run_fallback(mock_cookies_missing)
        timeline = next(item["timeline"] for item in result if "timeline" in item)
        actions = {t["action"] for t in timeline}
        assert "tiktok : Nickname modified" in actions

    def test_postsvsreposts_has_2_items(
        self, mock_cookies_found, mock_api_call, mock_analize_rrss
    ):
        result = tiktok_tasks.p_tiktok("testuser")
        graphic = next(item["graphic"] for item in result if "graphic" in item)
        pvr = next(g["postsvsreposts"] for g in graphic if "postsvsreposts" in g)
        assert len(pvr) == 2
        names = {r["name"] for r in pvr}
        assert "Original" in names
        assert "Reposts" in names

    def test_soundtrack_present(
        self, mock_cookies_found, mock_api_call, mock_analize_rrss
    ):
        """Soundtrack must be present with USER_VIDEOS music data."""
        result = tiktok_tasks.p_tiktok("testuser")
        graphic = next(item["graphic"] for item in result if "graphic" in item)
        soundtrack = next(g["soundtrack"] for g in graphic if "soundtrack" in g)
        # USER_VIDEOS has 2 Cool Song and 1 Another Track
        assert len(soundtrack) == 2
        track_names = {t["name"] for t in soundtrack}
        assert "Cool Song - Artist A" in track_names
        assert "Another Track - Artist B" in track_names


# ===========================================================================
# Cookie auth chain tests (tiktok_cookies apikeys pattern)
# ===========================================================================


class TestCookieAuthChain:
    """Tests for the new 3-step cookie auth chain in get_tiktok_cookies."""

    def test_cookie_file_constant_exists(self):
        """_COOKIE_FILE must be a Path constant pointing to /app/cookies/tiktok_cookies.json."""
        assert hasattr(tiktok_tasks, "_COOKIE_FILE")
        assert isinstance(tiktok_tasks._COOKIE_FILE, Path)
        assert tiktok_tasks._COOKIE_FILE.name == "tiktok_cookies.json"

    def test_cookie_dir_constant_exists(self):
        """_COOKIE_DIR must be a Path constant."""
        assert hasattr(tiktok_tasks, "_COOKIE_DIR")
        assert isinstance(tiktok_tasks._COOKIE_DIR, Path)

    def test_convert_tiktok_cookies_list_input(self):
        """Cookie-Editor list format → flat {name: value} dict."""
        raw = [
            {"name": "msToken", "value": "abc123"},
            {"name": "sessionid", "value": "xyz789"},
        ]
        result = tiktok_tasks._convert_tiktok_cookies(raw)
        assert result == {"msToken": "abc123", "sessionid": "xyz789"}

    def test_convert_tiktok_cookies_list_with_domain_field(self):
        """Cookie-Editor full export (with domain, expirationDate, etc.) works."""
        raw = [
            {
                "domain": ".tiktok.com",
                "name": "msToken",
                "value": "tok_value",
                "path": "/",
                "secure": True,
            },
            {
                "domain": ".tiktok.com",
                "name": "sessionid",
                "value": "sess_val",
                "path": "/",
                "secure": True,
            },
        ]
        result = tiktok_tasks._convert_tiktok_cookies(raw)
        assert result["msToken"] == "tok_value"
        assert result["sessionid"] == "sess_val"

    def test_convert_tiktok_cookies_dict_passthrough(self):
        """Dict input (already flat) is passed through unchanged."""
        raw = {"msToken": "flat_token", "sessionid": "flat_session"}
        result = tiktok_tasks._convert_tiktok_cookies(raw)
        assert result == {"msToken": "flat_token", "sessionid": "flat_session"}

    def test_convert_tiktok_cookies_dict_values_cast_to_str(self):
        """Dict values must be cast to str (handles int/bool values)."""
        raw = {"msToken": 12345, "flag": True}
        result = tiktok_tasks._convert_tiktok_cookies(raw)
        assert result["msToken"] == "12345"
        assert result["flag"] == "True"

    def test_convert_tiktok_cookies_invalid_type_raises(self):
        """Non-list, non-dict input must raise ValueError."""
        with pytest.raises(ValueError, match="Unexpected cookie format"):
            tiktok_tasks._convert_tiktok_cookies("not_a_list_or_dict")

    def test_convert_tiktok_cookies_invalid_int_raises(self):
        """Integer input must raise ValueError."""
        with pytest.raises(ValueError, match="Unexpected cookie format"):
            tiktok_tasks._convert_tiktok_cookies(42)

    def test_convert_tiktok_cookies_empty_list(self):
        """Empty list returns empty dict (no crash)."""
        result = tiktok_tasks._convert_tiktok_cookies([])
        assert result == {}

    def test_convert_tiktok_cookies_skips_items_without_name(self):
        """Items missing 'name' key are silently skipped."""
        raw = [
            {"name": "msToken", "value": "tok"},
            {"value": "orphan"},  # no name
        ]
        result = tiktok_tasks._convert_tiktok_cookies(raw)
        assert result == {"msToken": "tok"}

    def test_convert_tiktok_cookies_name_value_case_variants(self):
        """Supports 'Name'/'Value' (capital) as fallback keys."""
        raw = [{"Name": "msToken", "Value": "tok123"}]
        result = tiktok_tasks._convert_tiktok_cookies(raw)
        assert result["msToken"] == "tok123"

    def test_api_keys_search_imported(self):
        """api_keys_search must be imported in tiktok_tasks."""
        source_path = (
            Path(__file__).parent.parent / "modules" / "tiktok" / "tiktok_tasks.py"
        )
        content = source_path.read_text()
        assert "api_keys_search" in content, (
            "api_keys_search must be imported in tiktok_tasks.py"
        )

    def test_tiktok_cookies_key_referenced_in_source(self):
        """Source must reference 'tiktok_cookies' API key name."""
        source_path = (
            Path(__file__).parent.parent / "modules" / "tiktok" / "tiktok_tasks.py"
        )
        content = source_path.read_text()
        assert "tiktok_cookies" in content, (
            "tiktok_tasks.py must reference 'tiktok_cookies' API key"
        )

    def test_get_tiktok_cookies_returns_not_found_when_all_fail(self, tmp_path):
        """Cookie file absent + API key empty → {'found': False, 'cookies': {}}.

        After the dead-path removal there is no in-container browser fallback,
        so the chain stops at the API-key tier and returns not-found.
        """
        with (
            patch.object(tiktok_tasks, "_COOKIE_DIR", tmp_path),
            patch.object(
                tiktok_tasks,
                "_COOKIE_FILE",
                tmp_path / "tiktok_cookies.json",
            ),
            patch.object(tiktok_tasks, "api_keys_search", return_value=False),
        ):
            result = tiktok_tasks.get_tiktok_cookies(["msToken"])

        assert result == {"found": False, "cookies": {}}

    def test_get_tiktok_cookies_uses_api_key_when_no_file(self, tmp_path):
        """When no cookie file, valid API key JSON → returns cookies."""
        cookie_json = json.dumps([{"name": "msToken", "value": "tok_from_api"}])
        cookie_file = tmp_path / "tiktok_cookies.json"

        with (
            patch.object(tiktok_tasks, "_COOKIE_DIR", tmp_path),
            patch.object(tiktok_tasks, "_COOKIE_FILE", cookie_file),
            patch.object(tiktok_tasks, "api_keys_search", return_value=cookie_json),
        ):
            result = tiktok_tasks.get_tiktok_cookies(["msToken"])

        assert result["found"] is True
        assert result["cookies"]["msToken"] == "tok_from_api"

    def test_get_tiktok_cookies_persists_api_key_cookies_to_file(self, tmp_path):
        """Cookies from API key must be saved to disk for reuse."""
        cookie_json = json.dumps([{"name": "msToken", "value": "persist_me"}])
        cookie_file = tmp_path / "tiktok_cookies.json"

        with (
            patch.object(tiktok_tasks, "_COOKIE_DIR", tmp_path),
            patch.object(tiktok_tasks, "_COOKIE_FILE", cookie_file),
            patch.object(tiktok_tasks, "api_keys_search", return_value=cookie_json),
        ):
            tiktok_tasks.get_tiktok_cookies(["msToken"])

        assert cookie_file.exists()
        saved = json.loads(cookie_file.read_text())
        assert saved["msToken"] == "persist_me"

    def test_get_tiktok_cookies_loads_from_file_when_present(self, tmp_path):
        """Pre-existing cookie file with required keys → load directly (no API call)."""
        cookie_file = tmp_path / "tiktok_cookies.json"
        cookie_file.write_text(json.dumps({"msToken": "from_file"}))

        with (
            patch.object(tiktok_tasks, "_COOKIE_DIR", tmp_path),
            patch.object(tiktok_tasks, "_COOKIE_FILE", cookie_file),
            patch.object(tiktok_tasks, "api_keys_search") as mock_api_search,
        ):
            result = tiktok_tasks.get_tiktok_cookies(["msToken"])
            mock_api_search.assert_not_called()

        assert result["found"] is True
        assert result["cookies"]["msToken"] == "from_file"

    def test_get_tiktok_cookies_removes_corrupted_file(self, tmp_path):
        """Corrupted cookie file is deleted and auth falls through to not-found."""
        cookie_file = tmp_path / "tiktok_cookies.json"
        cookie_file.write_text("not valid json {{{")

        with (
            patch.object(tiktok_tasks, "_COOKIE_DIR", tmp_path),
            patch.object(tiktok_tasks, "_COOKIE_FILE", cookie_file),
            patch.object(tiktok_tasks, "api_keys_search", return_value=False),
        ):
            result = tiktok_tasks.get_tiktok_cookies(["msToken"])

        assert not cookie_file.exists()
        assert result["found"] is False

    def test_no_browser_cookie3_import_in_tiktok_tasks(self):
        """tiktok_tasks.py must NOT import browser_cookie3 (dead-path removal)."""
        source_path = (
            Path(__file__).parent.parent / "modules" / "tiktok" / "tiktok_tasks.py"
        )
        content = source_path.read_text()
        tree = ast.parse(content)
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
        assert "browser_cookie3" not in imported, (
            "browser_cookie3 must be removed from tiktok_tasks.py imports"
        )

    def test_uses_shared_cookie_converter(self):
        """_convert_tiktok_cookies must be the shared cookie_utils converter."""
        from factories.cookie_utils import convert_browser_cookies

        assert tiktok_tasks._convert_tiktok_cookies is convert_browser_cookies

    def test_not_found_warning_references_docs(self):
        """The exhausted-chain warning must point users to docs/COOKIES.md."""
        source_path = (
            Path(__file__).parent.parent / "modules" / "tiktok" / "tiktok_tasks.py"
        )
        content = source_path.read_text()
        assert "docs/COOKIES.md" in content, (
            "tiktok_tasks.py must reference docs/COOKIES.md in its guidance"
        )
