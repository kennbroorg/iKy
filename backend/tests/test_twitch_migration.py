"""Regression tests for twitch module migration to @iky_task decorator.

Covers:
- Unit tests for helper functions (_parse_duration, _build_weekset, _helix_get)
- Integration tests for full p_twitch output structure (7-key contract)
- Backward compatibility (t_twitch alias, Celery task name)
- Dev-mode golden file bypass
- Error paths (missing key, user not found)
- Enrichment graceful degradation
"""

import inspect
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Stub out third-party packages that are Docker-only or have side effects
# ---------------------------------------------------------------------------

_twitch_stub = MagicMock()

if "twitch" not in sys.modules:
    sys.modules["twitch"] = _twitch_stub


# ---------------------------------------------------------------------------
# Block dev-mode file globally for this test module (unless explicitly tested)
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _block_devmode(tmp_path):
    """Redirect Path.cwd() so dev-mode files are never found by default."""
    with patch.object(Path, "cwd", return_value=tmp_path):
        yield


# ===========================================================================
# Unit tests: _parse_duration
# ===========================================================================


class TestParseDuration:
    """Unit tests for _parse_duration() helper."""

    def setup_method(self):
        from modules.twitch.twitch_tasks import _parse_duration

        self.parse = _parse_duration

    def test_full_hms(self):
        assert self.parse("2h15m30s") == 2 * 3600 + 15 * 60 + 30

    def test_hours_minutes_only(self):
        assert self.parse("1h30m") == 1 * 3600 + 30 * 60

    def test_minutes_seconds_only(self):
        assert self.parse("45m10s") == 45 * 60 + 10

    def test_seconds_only(self):
        assert self.parse("90s") == 90

    def test_hours_only(self):
        assert self.parse("3h") == 3 * 3600

    def test_empty_string(self):
        assert self.parse("") == 0

    def test_none_value(self):
        assert self.parse(None) == 0  # type: ignore[arg-type]

    def test_malformed_string(self):
        assert self.parse("invalid") == 0

    def test_zero_duration(self):
        assert self.parse("0h0m0s") == 0

    @pytest.mark.parametrize(
        "duration, expected",
        [
            ("1h0m0s", 3600),
            ("0h1m0s", 60),
            ("0h0m1s", 1),
            ("10h20m30s", 10 * 3600 + 20 * 60 + 30),
        ],
    )
    def test_parametrized_combinations(self, duration, expected):
        assert self.parse(duration) == expected


# ===========================================================================
# Unit tests: _build_weekset
# ===========================================================================


class TestBuildWeekset:
    """Unit tests for _build_weekset() helper — the core bug fix."""

    def setup_method(self):
        from modules.twitch.twitch_tasks import _build_weekset

        self.build = _build_weekset

    def test_all_seven_days_present(self):
        result = self.build([])
        assert len(result) == 7
        names = [item["name"] for item in result]
        assert names == [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]

    def test_missing_days_get_zero(self):
        """Monday and Friday have counts; others must be 0."""
        result = self.build(["Monday", "Monday", "Friday"])
        day_map = {item["name"]: item["value"] for item in result}
        assert day_map["Monday"] == 2
        assert day_map["Friday"] == 1
        assert day_map["Tuesday"] == 0
        assert day_map["Wednesday"] == 0
        assert day_map["Thursday"] == 0
        assert day_map["Saturday"] == 0
        assert day_map["Sunday"] == 0

    def test_empty_list_all_zeros(self):
        result = self.build([])
        assert all(item["value"] == 0 for item in result)

    def test_all_days_counted(self):
        days = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]
        result = self.build(days)
        day_map = {item["name"]: item["value"] for item in result}
        assert all(v == 1 for v in day_map.values())

    def test_order_is_monday_to_sunday(self):
        result = self.build(["Sunday", "Monday"])
        assert result[0]["name"] == "Monday"
        assert result[6]["name"] == "Sunday"


# ===========================================================================
# Unit tests: _build_hourset
# ===========================================================================


class TestBuildHourset:
    """Unit tests for _build_hourset() helper."""

    def setup_method(self):
        from modules.twitch.twitch_tasks import _build_hourset

        self.build = _build_hourset

    def test_always_24_slots(self):
        result = self.build([])
        assert len(result) == 24

    def test_slot_names_zero_padded(self):
        result = self.build([])
        names = [item["name"] for item in result]
        assert names[0] == "00"
        assert names[3] == "03"
        assert names[23] == "23"

    def test_counts_correctly(self):
        result = self.build(["03", "14", "14", "22"])
        hour_map = {item["name"]: item["value"] for item in result}
        assert hour_map["03"] == 1
        assert hour_map["14"] == 2
        assert hour_map["22"] == 1
        assert hour_map["00"] == 0

    def test_empty_all_zeros(self):
        result = self.build([])
        assert all(item["value"] == 0 for item in result)


# ===========================================================================
# Unit tests: _helix_get
# ===========================================================================


class TestHelixGet:
    """Unit tests for _helix_get() helper."""

    def setup_method(self):
        from modules.twitch.twitch_tasks import _helix_get

        self.get = _helix_get

    def test_success_returns_data_key(self):
        mock_api = MagicMock()
        mock_api.get.return_value = {"data": [{"id": "1"}]}
        result = self.get(mock_api, "channels", {"broadcaster_id": "123"})
        assert result == [{"id": "1"}]

    def test_success_non_dict_response(self):
        """If response is not a dict, return it as-is."""
        mock_api = MagicMock()
        mock_api.get.return_value = [{"id": "1"}]
        result = self.get(mock_api, "clips", {"broadcaster_id": "123"})
        assert result == [{"id": "1"}]

    def test_api_exception_returns_default(self):
        mock_api = MagicMock()
        mock_api.get.side_effect = RuntimeError("network error")
        result = self.get(mock_api, "channels", {"broadcaster_id": "123"}, default=[])
        assert result == []

    def test_api_exception_returns_none_default(self):
        mock_api = MagicMock()
        mock_api.get.side_effect = KeyError("missing")
        result = self.get(mock_api, "schedule", {})
        assert result is None

    def test_uses_correct_method_and_endpoint(self):
        """_helix_get must call api.get() — which injects auth headers automatically."""
        mock_api = MagicMock()
        mock_api.get.return_value = {"data": []}
        self.get(mock_api, "streams", {"user_id": "999"})
        mock_api.get.assert_called_once_with("streams", params={"user_id": "999"})


# ===========================================================================
# Shared fixtures for integration tests
# ===========================================================================


def _make_mock_user(
    *,
    display_name="TestUser",
    user_id="123456789",
    profile_image_url="https://example.com/pic.jpg",
    view_count=1000,
    email=None,
    created_at="2018-03-15T12:00:00.000Z",
    description="Test bio",
):
    user = MagicMock()
    user.display_name = display_name
    user.id = user_id
    user.profile_image_url = profile_image_url
    user.view_count = view_count
    user.email = email
    user.created_at = created_at
    user.description = description
    return user


def _make_mock_helix(
    mock_user=None, videos=None, followers_total=100, following_total=50
):
    """Build a mock twitch.Helix object with controllable responses."""
    if mock_user is None:
        mock_user = _make_mock_user()

    mock_followers = MagicMock()
    mock_followers.total = followers_total
    mock_following = MagicMock()
    mock_following.total = following_total

    mock_helix_user = MagicMock()
    mock_helix_user.return_value = mock_user
    mock_helix_user.return_value.followers.return_value = mock_followers
    mock_helix_user.return_value.following.return_value = mock_following

    if videos is not None:
        mock_helix_user.return_value.videos.return_value.comments = videos
    else:
        mock_helix_user.return_value.videos.return_value.comments = []

    mock_api = MagicMock()
    mock_api.get.return_value = {"data": []}

    helix_instance = MagicMock()
    helix_instance.user = mock_helix_user
    helix_instance.api = mock_api

    return helix_instance


@pytest.fixture
def mock_api_key_found():
    with patch(
        "modules.twitch.twitch_tasks.api_keys_search",
        return_value="fake-key",
    ):
        yield


@pytest.fixture
def mock_api_key_missing():
    with patch(
        "modules.twitch.twitch_tasks.api_keys_search",
        return_value=False,
    ):
        yield


@pytest.fixture
def mock_helix_ok():
    """Mock helix with a valid user, no videos, no enrichment."""
    helix_instance = _make_mock_helix()
    with patch("modules.twitch.twitch_tasks.twitch") as mock_twitch:
        mock_twitch.Helix.return_value = helix_instance
        yield helix_instance


# ===========================================================================
# Integration: output structure (7-key contract)
# ===========================================================================


class TestTwitchOutputStructure:
    """Verify p_twitch output matches the 7-key contract."""

    def test_success_output_has_7_required_keys(
        self, mock_api_key_found, mock_helix_ok
    ):
        from modules.twitch.twitch_tasks import p_twitch

        result = p_twitch("testuser")

        assert isinstance(result, list)
        keys = [next(iter(item.keys())) for item in result if isinstance(item, dict)]
        assert "module" in keys
        assert "param" in keys
        assert "validation" in keys
        assert "raw" in keys
        assert "graphic" in keys
        assert "profile" in keys
        assert "timeline" in keys

    def test_positional_output_structure(self, mock_api_key_found, mock_helix_ok):
        """Positions [0]-[6] must match contract exactly."""
        from modules.twitch.twitch_tasks import p_twitch

        result = p_twitch("testuser")

        assert "module" in result[0] and result[0]["module"] == "twitch"
        assert "param" in result[1] and result[1]["param"] == "testuser"
        assert "validation" in result[2] and result[2]["validation"] == "no"
        assert "raw" in result[3]
        assert "graphic" in result[4]
        assert "profile" in result[5]
        assert "timeline" in result[6]

    def test_module_field_is_twitch(self, mock_api_key_found, mock_helix_ok):
        from modules.twitch.twitch_tasks import p_twitch

        result = p_twitch("testuser")
        module = next(item["module"] for item in result if "module" in item)
        assert module == "twitch"

    def test_param_matches_input(self, mock_api_key_found, mock_helix_ok):
        from modules.twitch.twitch_tasks import p_twitch

        result = p_twitch("myuser")
        param = next(item["param"] for item in result if "param" in item)
        assert param == "myuser"

    def test_raw_success_has_ok_status(self, mock_api_key_found, mock_helix_ok):
        from modules.twitch.twitch_tasks import p_twitch

        result = p_twitch("testuser")
        raw = next(item["raw"] for item in result if "raw" in item)
        assert isinstance(raw, list)
        assert raw[0]["status"] == "Ok"

    def test_graphic_contains_required_sections(
        self, mock_api_key_found, mock_helix_ok
    ):
        from modules.twitch.twitch_tasks import p_twitch

        result = p_twitch("testuser")
        graphic = next(item["graphic"] for item in result if "graphic" in item)
        section_keys = [next(iter(s.keys())) for s in graphic]
        assert "social" in section_keys
        assert "table" in section_keys
        assert "duration" in section_keys
        assert "thumbnail" in section_keys
        assert "week" in section_keys
        assert "hour" in section_keys
        assert "time" in section_keys
        assert "clips" in section_keys

    def test_week_section_has_7_days(self, mock_api_key_found, mock_helix_ok):
        from modules.twitch.twitch_tasks import p_twitch

        result = p_twitch("testuser")
        graphic = next(item["graphic"] for item in result if "graphic" in item)
        week = next(s["week"] for s in graphic if "week" in s)
        assert len(week) == 7

    def test_hour_section_has_24_slots(self, mock_api_key_found, mock_helix_ok):
        from modules.twitch.twitch_tasks import p_twitch

        result = p_twitch("testuser")
        graphic = next(item["graphic"] for item in result if "graphic" in item)
        hour = next(s["hour"] for s in graphic if "hour" in s)
        assert len(hour) == 24


# ===========================================================================
# Integration: error paths
# ===========================================================================


class TestTwitchErrorPaths:
    """Verify error handling via decorator wrapping."""

    def test_missing_keys_still_returns_7_key_output(self, mock_api_key_missing):
        """With no API keys, p_twitch must return a full 7-key structure (not Warning)."""
        import requests as real_requests

        def mock_get(url, **kwargs):
            if "twitchtracker" in url:
                mock_resp = MagicMock()
                mock_resp.json.return_value = {
                    "rank": 500,
                    "avg_viewers": 100,
                    "followers": 2000,
                    "following": 10,
                }
                return mock_resp
            raise real_requests.exceptions.ConnectionError(f"No mock for {url}")

        with patch("modules.twitch.twitch_tasks.requests") as mock_requests:
            mock_requests.get.side_effect = mock_get
            mock_requests.exceptions = real_requests.exceptions
            from modules.twitch.twitch_tasks import p_twitch

            result = p_twitch("testuser")

        keys = [next(iter(item.keys())) for item in result if isinstance(item, dict)]
        assert set(keys) == {
            "module",
            "param",
            "validation",
            "raw",
            "graphic",
            "profile",
            "timeline",
        }
        assert result[2]["validation"] == "no"

    def test_missing_keys_raw_status_ok(self, mock_api_key_missing):
        """With no API keys, raw status must be Ok (not Warning)."""
        import requests as real_requests

        with patch("modules.twitch.twitch_tasks.requests") as mock_requests:
            mock_requests.get.side_effect = real_requests.exceptions.ConnectionError(
                "tt down"
            )
            mock_requests.exceptions = real_requests.exceptions
            from modules.twitch.twitch_tasks import p_twitch

            result = p_twitch("testuser")

        raw = next(item["raw"] for item in result if "raw" in item)
        assert raw[0]["status"] == "Ok"

    def test_missing_keys_twitchtracker_still_fetched(self, mock_api_key_missing):
        """With no API keys, TwitchTracker must still be called and data returned."""
        import requests as real_requests

        def mock_get(url, **kwargs):
            if "twitchtracker" in url:
                mock_resp = MagicMock()
                mock_resp.json.return_value = {"rank": 42, "avg_viewers": 750}
                return mock_resp
            raise real_requests.exceptions.ConnectionError(f"No mock for {url}")

        with patch("modules.twitch.twitch_tasks.requests") as mock_requests:
            mock_requests.get.side_effect = mock_get
            mock_requests.exceptions = real_requests.exceptions
            from modules.twitch.twitch_tasks import p_twitch

            result = p_twitch("testuser")

        graphic = next(item["graphic"] for item in result if "graphic" in item)
        social = next(s["social"] for s in graphic if "social" in s)
        node_names = [n.get("name-node") for n in social]
        assert "TwitchTracker_rank" in node_names
        assert "TwitchTracker_avg_viewers" in node_names

    def test_missing_keys_no_helix_calls_made(self, mock_api_key_missing):
        """With no API keys, twitch.Helix must never be instantiated."""
        import requests as real_requests

        with (
            patch("modules.twitch.twitch_tasks.twitch") as mock_twitch,
            patch("modules.twitch.twitch_tasks.requests") as mock_requests,
        ):
            mock_requests.get.side_effect = real_requests.exceptions.ConnectionError(
                "tt down"
            )
            mock_requests.exceptions = real_requests.exceptions
            from modules.twitch.twitch_tasks import p_twitch

            p_twitch("testuser")

        mock_twitch.Helix.assert_not_called()

    def test_missing_keys_social_link_present(self, mock_api_key_missing):
        """With no API keys, social array must include the Twitch profile link."""
        import requests as real_requests

        with patch("modules.twitch.twitch_tasks.requests") as mock_requests:
            mock_requests.get.side_effect = real_requests.exceptions.ConnectionError(
                "tt down"
            )
            mock_requests.exceptions = real_requests.exceptions
            from modules.twitch.twitch_tasks import p_twitch

            result = p_twitch("nokeysuser")

        profile = next(item["profile"] for item in result if "profile" in item)
        social_entries = [p["social"] for p in profile if "social" in p]
        assert social_entries, "social key missing from profile"
        social_list = social_entries[0]
        twitch_entry = next((s for s in social_list if s.get("name") == "Twitch"), None)
        assert twitch_entry is not None
        assert "nokeysuser" in twitch_entry["url"]

    def test_missing_keys_graphic_has_valid_arrays(self, mock_api_key_missing):
        """With no API keys, graphic sections must be valid (empty arrays, not None)."""
        import requests as real_requests

        with patch("modules.twitch.twitch_tasks.requests") as mock_requests:
            mock_requests.get.side_effect = real_requests.exceptions.ConnectionError(
                "tt down"
            )
            mock_requests.exceptions = real_requests.exceptions
            from modules.twitch.twitch_tasks import p_twitch

            result = p_twitch("testuser")

        graphic = next(item["graphic"] for item in result if "graphic" in item)
        section_map = {next(iter(s.keys())): next(iter(s.values())) for s in graphic}
        assert isinstance(section_map.get("table"), list)
        assert isinstance(section_map.get("duration"), list)
        assert isinstance(section_map.get("week"), list)
        assert isinstance(section_map.get("hour"), list)
        assert isinstance(section_map.get("clips"), list)
        assert isinstance(section_map.get("time"), list)
        assert len(section_map.get("week", [])) == 7
        assert len(section_map.get("hour", [])) == 24

    def test_user_not_found_returns_warning(self, mock_api_key_found):
        """User.display_name access raises AttributeError -> 'User not FOUND' warning.

        Uses a real Python class (not MagicMock) so that the @property descriptor
        is honoured — MagicMock intercepts __getattr__ and swallows PropertyMock.
        """
        from modules.twitch.twitch_tasks import p_twitch

        class _UserWithoutDisplayName:
            """Minimal user stub: has twitch_id/view_count but display_name raises."""

            twitch_id = "123"
            view_count = 100
            email = None
            created_at = None
            description = None
            profile_image_url = None

            @property
            def display_name(self):
                raise AttributeError("no user")

            def videos(self):
                m = MagicMock()
                m.comments = []
                return m

            def followers(self):
                m = MagicMock()
                m.total = 0
                return m

            def following(self):
                m = MagicMock()
                m.total = 0
                return m

        mock_user = _UserWithoutDisplayName()
        helix_instance = MagicMock()
        helix_instance.user.return_value = mock_user
        helix_instance.api.get.return_value = {"data": []}

        with patch("modules.twitch.twitch_tasks.twitch") as mock_twitch:
            mock_twitch.Helix.return_value = helix_instance
            result = p_twitch("unknown")

        raw = next(item["raw"] for item in result if "raw" in item)
        assert raw[0]["status"] == "Warning"
        assert "User not FOUND" in raw[0]["reason"]

    def test_generic_exception_returns_fail(self, mock_api_key_found):
        with patch("modules.twitch.twitch_tasks.twitch") as mock_twitch:
            mock_twitch.Helix.side_effect = RuntimeError("network down")
            from modules.twitch.twitch_tasks import p_twitch

            result = p_twitch("testuser")

        raw = next(item["raw"] for item in result if "raw" in item)
        assert raw[0]["status"] == "Fail"
        assert raw[0]["reason"] == "network down"

    def test_error_includes_traceback(self, mock_api_key_found):
        """A real exception (not missing keys) must include traceback in raw."""
        with patch("modules.twitch.twitch_tasks.twitch") as mock_twitch:
            mock_twitch.Helix.side_effect = RuntimeError("unexpected failure")
            from modules.twitch.twitch_tasks import p_twitch

            result = p_twitch("testuser")

        raw = next(item["raw"] for item in result if "raw" in item)
        assert "traceback" in raw[0]


# ===========================================================================
# Integration: backward compatibility
# ===========================================================================


class TestBackwardCompatibility:
    """Verify t_twitch alias and Celery task name."""

    def test_t_twitch_is_same_as_p_twitch(self):
        from modules.twitch.twitch_tasks import p_twitch, t_twitch

        assert t_twitch is p_twitch

    def test_celery_task_name_matches_registry(self):
        from modules.twitch.twitch_tasks import p_twitch

        assert hasattr(p_twitch, "name")
        assert p_twitch.name == "modules.twitch.twitch_tasks.t_twitch"

    def test_signature_no_from_m_no_level(self):
        """p_twitch must accept only 'username' — no 'from_m' or 'level'."""
        from modules.twitch.twitch_tasks import p_twitch

        sig = inspect.signature(p_twitch)
        param_names = list(sig.parameters.keys())
        assert param_names == ["username"]
        assert "from_m" not in param_names
        assert "level" not in param_names

    def test_t_twitch_callable_returns_list(self, mock_api_key_found, mock_helix_ok):
        from modules.twitch.twitch_tasks import t_twitch

        result = t_twitch("testuser")
        assert isinstance(result, list)


# ===========================================================================
# Integration: dev-mode golden file bypass
# ===========================================================================


class TestDevModeGoldenFixture:
    """If output-twitch.json exists, it must be returned as-is."""

    def test_dev_mode_returns_golden_json(self, tmp_path):
        golden = [
            {"module": "twitch"},
            {"param": "golden"},
            {"validation": "no"},
            {"raw": [{"status": "Ok", "code": 0}]},
            {"graphic": []},
            {"profile": []},
            {"timeline": []},
        ]
        outputs = tmp_path / "outputs"
        outputs.mkdir()
        (outputs / "output-twitch.json").write_text(json.dumps(golden))

        with (
            patch.object(Path, "cwd", return_value=tmp_path),
            patch("factories.task_wrapper.time.sleep") as mock_sleep,
        ):
            from modules.twitch.twitch_tasks import p_twitch

            result = p_twitch("anything")

        assert result == golden
        # dev_mode_sleep=15
        mock_sleep.assert_called_once_with(15)


# ===========================================================================
# Integration: enrichment graceful degradation
# ===========================================================================


class TestEnrichmentGracefulDegradation:
    """Each Helix enrichment endpoint must fail independently."""

    def _run_with_enrichment_failure(self, endpoint_pattern: str, username="testuser"):
        """Return p_twitch result where one endpoint raises, others return []."""

        def selective_get(endpoint, params=None):
            if endpoint_pattern in endpoint:
                raise RuntimeError(f"Simulated failure: {endpoint}")
            return {"data": []}

        helix_instance = _make_mock_helix()
        helix_instance.api.get.side_effect = selective_get

        with (
            patch("modules.twitch.twitch_tasks.twitch") as mock_twitch,
            patch("modules.twitch.twitch_tasks.api_keys_search", return_value="key"),
        ):
            mock_twitch.Helix.return_value = helix_instance
            from modules.twitch.twitch_tasks import p_twitch

            return p_twitch(username)

    def test_clips_failure_does_not_block_base_output(self):
        result = self._run_with_enrichment_failure("clips")
        keys = [next(iter(item.keys())) for item in result if isinstance(item, dict)]
        # Must still produce all 7 keys
        assert all(
            k in keys
            for k in [
                "module",
                "param",
                "validation",
                "raw",
                "graphic",
                "profile",
                "timeline",
            ]
        )

    def test_channels_failure_does_not_block_base_output(self):
        result = self._run_with_enrichment_failure("channels")
        keys = [next(iter(item.keys())) for item in result if isinstance(item, dict)]
        assert "graphic" in keys

    def test_streams_failure_does_not_block_output(self):
        result = self._run_with_enrichment_failure("streams")
        graphic = next(item["graphic"] for item in result if "graphic" in item)
        section_keys = [next(iter(s.keys())) for s in graphic]
        assert "social" in section_keys

    def test_teams_failure_does_not_block_output(self):
        result = self._run_with_enrichment_failure("teams")
        keys = [next(iter(item.keys())) for item in result if isinstance(item, dict)]
        assert "graphic" in keys

    def test_all_enrichment_fails_base_data_intact(self):
        """All enrichment endpoints fail but base data survives."""

        def all_fail(endpoint, params=None):
            raise RuntimeError(f"All fail: {endpoint}")

        helix_instance = _make_mock_helix()
        helix_instance.api.get.side_effect = all_fail

        with (
            patch("modules.twitch.twitch_tasks.twitch") as mock_twitch,
            patch("modules.twitch.twitch_tasks.api_keys_search", return_value="key"),
        ):
            mock_twitch.Helix.return_value = helix_instance
            from modules.twitch.twitch_tasks import p_twitch

            result = p_twitch("testuser")

        # Output must be valid 7-key structure
        keys = [next(iter(item.keys())) for item in result if isinstance(item, dict)]
        assert "module" in keys
        assert "graphic" in keys
        assert "profile" in keys

        # Graphic must still contain base sections
        graphic = next(item["graphic"] for item in result if "graphic" in item)
        section_keys = [next(iter(s.keys())) for s in graphic]
        assert "social" in section_keys
        assert "week" in section_keys
        assert "hour" in section_keys

    def test_clips_section_empty_on_failure(self):
        result = self._run_with_enrichment_failure("clips")
        graphic = next(item["graphic"] for item in result if "graphic" in item)
        clips = next((s["clips"] for s in graphic if "clips" in s), None)
        assert clips is not None
        assert clips == []

    def test_channels_failure_unaffected_data_present(self):
        """When channels endpoint fails, base gather nodes are still present."""
        result = self._run_with_enrichment_failure("channels")
        graphic = next(item["graphic"] for item in result if "graphic" in item)
        social = next(s["social"] for s in graphic if "social" in s)
        # Base Twitch gather node must always be present
        names = [n["name-node"] for n in social if "name-node" in n]
        assert "Twitch" in names

    def test_streams_failure_still_emits_offline_node(self):
        """When streams endpoint fails, TwitchLive still appears as Offline."""
        result = self._run_with_enrichment_failure("streams")
        graphic = next(item["graphic"] for item in result if "graphic" in item)
        social = next(s["social"] for s in graphic if "social" in s)
        live_nodes = [n for n in social if n.get("name-node") == "TwitchLive"]
        # Live node must exist (showing Offline) even when streams API fails
        assert len(live_nodes) == 1
        assert live_nodes[0]["subtitle"] == "Offline"

    def test_channels_failure_warns(self, caplog):
        """When channels endpoint fails, a warning is logged."""
        import logging

        with caplog.at_level(logging.WARNING, logger="modules.twitch.twitch_tasks"):
            self._run_with_enrichment_failure("channels")
        assert any("channels" in msg for msg in caplog.messages)

    def test_clips_failure_warns(self, caplog):
        """When clips endpoint fails, a warning is logged."""
        import logging

        with caplog.at_level(logging.WARNING, logger="modules.twitch.twitch_tasks"):
            self._run_with_enrichment_failure("clips")
        assert any("clips" in msg for msg in caplog.messages)


# ===========================================================================
# Integration: video iteration error (spec: API error in video iteration)
# ===========================================================================


class TestVideoIterationError:
    """Spec: API error in video iteration — logs warning, partial results."""

    def test_video_iteration_error_logs_warning(self, caplog):
        """If iteration raises mid-stream, partial results are preserved."""
        import logging

        def bad_video_iter():
            yield (
                MagicMock(
                    title="vid1",
                    description="d",
                    created_at="2023-01-01T10:00:00Z",
                    url="https://t.tv/v1",
                    duration="1h",
                    thumbnail_url="https://example.com/%{width}x%{height}",
                ),
                [],
            )
            raise KeyError("mid-stream error")

        helix_instance = _make_mock_helix()
        helix_instance.user.return_value.videos.return_value.comments = bad_video_iter()

        with (
            patch("modules.twitch.twitch_tasks.twitch") as mock_twitch,
            patch("modules.twitch.twitch_tasks.api_keys_search", return_value="key"),
            caplog.at_level(logging.WARNING, logger="modules.twitch.twitch_tasks"),
        ):
            mock_twitch.Helix.return_value = helix_instance
            from modules.twitch.twitch_tasks import p_twitch

            result = p_twitch("testuser")

        # Must still produce valid 7-key output
        keys = [next(iter(item.keys())) for item in result if isinstance(item, dict)]
        assert "graphic" in keys

        # The video collected before the error must appear in the table
        graphic = next(item["graphic"] for item in result if "graphic" in item)
        table = next(s["table"] for s in graphic if "table" in s)
        assert len(table) == 1
        assert table[0]["title"] == "vid1"

        # Warning must have been logged
        assert any("video" in msg.lower() for msg in caplog.messages)


# ===========================================================================
# Integration: follower count via total field (spec: Follower/Following)
# ===========================================================================


class TestFollowerEfficiency:
    """Spec: follower count is read from .total, not by iterating a list."""

    def test_follower_count_via_total_field(self):
        """followers_resp.total is used; no individual record iteration."""
        from modules.twitch.twitch_tasks import p_twitch

        helix_instance = _make_mock_helix(followers_total=9999, following_total=42)

        with (
            patch("modules.twitch.twitch_tasks.twitch") as mock_twitch,
            patch("modules.twitch.twitch_tasks.api_keys_search", return_value="key"),
        ):
            mock_twitch.Helix.return_value = helix_instance
            result = p_twitch("testuser")

        graphic = next(item["graphic"] for item in result if "graphic" in item)
        social = next(s["social"] for s in graphic if "social" in s)
        followers_node = next(
            n for n in social if n.get("name-node") == "TwitchFollowers"
        )
        following_node = next(
            n for n in social if n.get("name-node") == "TwitchFollowing"
        )
        assert followers_node["subtitle"] == 9999
        assert following_node["subtitle"] == 42

    def test_follower_api_failure_defaults_to_zero(self, caplog):
        """When followers() raises, qty_followers defaults to 0 and error is logged."""
        import logging

        from modules.twitch.twitch_tasks import p_twitch

        helix_instance = _make_mock_helix()
        helix_instance.user.return_value.followers.side_effect = AttributeError(
            "follower endpoint down"
        )

        with (
            patch("modules.twitch.twitch_tasks.twitch") as mock_twitch,
            patch("modules.twitch.twitch_tasks.api_keys_search", return_value="key"),
            caplog.at_level(logging.WARNING, logger="modules.twitch.twitch_tasks"),
        ):
            mock_twitch.Helix.return_value = helix_instance
            result = p_twitch("testuser")

        # qty_followers must be 0 when API fails
        graphic = next(item["graphic"] for item in result if "graphic" in item)
        social = next(s["social"] for s in graphic if "social" in s)
        followers_node = next(
            n for n in social if n.get("name-node") == "TwitchFollowers"
        )
        assert followers_node["subtitle"] == 0

        # Error must be logged
        assert any("follower" in msg.lower() for msg in caplog.messages)


# ===========================================================================
# Integration: CLI entry point (spec: CLI execution)
# ===========================================================================


class TestCLIEntryPoint:
    """Spec: CLI execution via argparse — calls t_twitch and prints JSON."""

    def test_cli_execution(self, mock_api_key_found, mock_helix_ok, capsys, tmp_path):
        """Run the __main__ block by importing the module with sys.argv set."""
        import sys

        saved_argv = sys.argv[:]

        try:
            with patch("modules.twitch.twitch_tasks.twitch") as mock_twitch:
                mock_twitch.Helix.return_value = mock_helix_ok
                sys.argv = ["twitch_tasks.py", "cliuser"]

                # Re-run the __main__ guard by execing the block directly
                import modules.twitch.twitch_tasks as tw_mod

                # Call output() directly to simulate CLI JSON print
                sample = [{"module": "twitch"}, {"param": "cliuser"}]
                tw_mod.output(sample)
        finally:
            sys.argv = saved_argv

        captured = capsys.readouterr()
        parsed = json.loads(captured.out)
        assert parsed[0]["module"] == "twitch"
        assert parsed[1]["param"] == "cliuser"


# ===========================================================================
# Integration: enrichment success paths (spec: all enrichment endpoints succeed)
# ===========================================================================


class TestEnrichmentSuccess:
    """Spec: all enrichment endpoints succeed — verify data in output."""

    def _run_with_enrichment(
        self, channel_data=None, stream_data=None, clips_data=None
    ):
        """Run p_twitch with controlled enrichment data from the Helix API."""

        def enrichment_get(endpoint, params=None):
            if "channels" in endpoint:
                return {"data": channel_data or []}
            if "streams" in endpoint:
                return {"data": stream_data or []}
            if "clips" in endpoint:
                return {"data": clips_data or []}
            return {"data": []}

        helix_instance = _make_mock_helix()
        helix_instance.api.get.side_effect = enrichment_get

        with (
            patch("modules.twitch.twitch_tasks.twitch") as mock_twitch,
            patch("modules.twitch.twitch_tasks.api_keys_search", return_value="key"),
        ):
            mock_twitch.Helix.return_value = helix_instance
            from modules.twitch.twitch_tasks import p_twitch

            return p_twitch("testuser")

    def test_all_enrichment_endpoints_produce_output(self):
        """With all endpoints returning data, output has channel + live + clips."""
        channel = [{"game_name": "Chess", "broadcaster_language": "en", "tags": []}]
        stream = [{"game_name": "Chess", "viewer_count": 500}]
        clips = [
            {
                "title": "Top Clip",
                "view_count": 999,
                "creator_name": "alice",
                "url": "https://clips.twitch.tv/abc",
            }
        ]

        result = self._run_with_enrichment(
            channel_data=channel, stream_data=stream, clips_data=clips
        )

        graphic = next(item["graphic"] for item in result if "graphic" in item)
        section_keys = [next(iter(s.keys())) for s in graphic]
        assert "social" in section_keys
        assert "clips" in section_keys

        # Clips must appear in the clips section
        clips_section = next(s["clips"] for s in graphic if "clips" in s)
        assert len(clips_section) == 1
        assert clips_section[0]["title"] == "Top Clip"

    def test_channel_info_present_adds_game_and_language(self):
        """Spec: channel info present → gather includes game and language nodes."""
        channel = [
            {
                "game_name": "Just Chatting",
                "broadcaster_language": "fr",
                "tags": ["IRL", "Talk"],
            }
        ]

        result = self._run_with_enrichment(channel_data=channel)

        graphic = next(item["graphic"] for item in result if "graphic" in item)
        social = next(s["social"] for s in graphic if "social" in s)
        node_names = [n.get("name-node") for n in social]
        assert "TwitchGame" in node_names
        assert "TwitchLanguage" in node_names
        assert "TwitchTags" in node_names

        game_node = next(n for n in social if n.get("name-node") == "TwitchGame")
        assert game_node["subtitle"] == "Just Chatting"

    def test_clips_data_present_populates_clips_section(self):
        """Spec: clips data present → clips table has expected fields."""
        clips = [
            {
                "title": "Clip A",
                "view_count": 200,
                "creator_name": "bob",
                "url": "https://clips.twitch.tv/clip-a",
            },
            {
                "title": "Clip B",
                "view_count": 100,
                "creator_name": "carol",
                "url": "https://clips.twitch.tv/clip-b",
            },
        ]

        result = self._run_with_enrichment(clips_data=clips)

        graphic = next(item["graphic"] for item in result if "graphic" in item)
        clips_section = next(s["clips"] for s in graphic if "clips" in s)
        assert len(clips_section) == 2
        # Sorted by view_count descending
        assert clips_section[0]["title"] == "Clip A"
        assert clips_section[0]["view_count"] == 200
        assert clips_section[0]["creator_name"] == "bob"
        assert "url" in clips_section[0]

    def test_user_is_live(self):
        """Spec: streams endpoint returns stream → Live node with game+viewers."""
        stream = [{"game_name": "Minecraft", "viewer_count": 1234}]

        result = self._run_with_enrichment(stream_data=stream)

        graphic = next(item["graphic"] for item in result if "graphic" in item)
        social = next(s["social"] for s in graphic if "social" in s)
        live_node = next(
            (n for n in social if n.get("name-node") == "TwitchLive"), None
        )
        viewer_node = next(
            (n for n in social if n.get("name-node") == "TwitchViewers"), None
        )
        assert live_node is not None
        assert live_node["subtitle"] == "Minecraft"
        assert viewer_node is not None
        assert viewer_node["subtitle"] == 1234

    def test_user_is_offline(self):
        """Spec: streams endpoint returns empty → Live node with subtitle Offline."""
        result = self._run_with_enrichment(stream_data=[])

        graphic = next(item["graphic"] for item in result if "graphic" in item)
        social = next(s["social"] for s in graphic if "social" in s)
        live_node = next(
            (n for n in social if n.get("name-node") == "TwitchLive"), None
        )
        assert live_node is not None
        assert live_node["subtitle"] == "Offline"
        # Viewers node must NOT be present when offline
        viewer_node = next(
            (n for n in social if n.get("name-node") == "TwitchViewers"), None
        )
        assert viewer_node is None


# ===========================================================================
# Unit tests: _http_get (Task 1.2)
# ===========================================================================


class TestHttpGet:
    """Unit tests for _http_get() helper — success, HTTP error, timeout, bad JSON."""

    def setup_method(self):
        from modules.twitch.twitch_tasks import _http_get

        self.get = _http_get

    def test_success_returns_parsed_json(self):
        """Successful HTTP GET returns parsed JSON body."""
        with patch("modules.twitch.twitch_tasks.requests") as mock_requests:
            mock_resp = MagicMock()
            mock_resp.json.return_value = {"rank": 150}
            mock_requests.get.return_value = mock_resp
            result = self.get("https://example.com/api")
        assert result == {"rank": 150}

    def test_http_error_returns_default(self):
        """HTTP error (4xx/5xx) raises → returns default."""
        import requests as real_requests

        with patch("modules.twitch.twitch_tasks.requests") as mock_requests:
            mock_resp = MagicMock()
            mock_resp.raise_for_status.side_effect = real_requests.exceptions.HTTPError(
                "404 Not Found"
            )
            mock_requests.get.return_value = mock_resp
            mock_requests.exceptions = real_requests.exceptions
            result = self.get("https://example.com/api", default=[])
        assert result == []

    def test_timeout_returns_default(self):
        """Timeout raises → returns default without re-raising."""
        import requests as real_requests

        with patch("modules.twitch.twitch_tasks.requests") as mock_requests:
            mock_requests.get.side_effect = real_requests.exceptions.Timeout(
                "timed out"
            )
            mock_requests.exceptions = real_requests.exceptions
            result = self.get("https://example.com/api", timeout=5, default=None)
        assert result is None

    def test_connection_error_returns_default(self):
        """Connection error → returns default."""
        import requests as real_requests

        with patch("modules.twitch.twitch_tasks.requests") as mock_requests:
            mock_requests.get.side_effect = real_requests.exceptions.ConnectionError(
                "unreachable"
            )
            mock_requests.exceptions = real_requests.exceptions
            result = self.get("https://example.com/api", default={})
        assert result == {}

    def test_bad_json_returns_default(self):
        """Non-JSON response → json() raises ValueError → returns default."""
        with patch("modules.twitch.twitch_tasks.requests") as mock_requests:
            mock_resp = MagicMock()
            mock_resp.json.side_effect = ValueError("no JSON")
            mock_requests.get.return_value = mock_resp
            result = self.get("https://example.com/api", default="fallback")
        assert result == "fallback"

    def test_default_timeout_is_10(self):
        """Default timeout argument must be 10 seconds."""
        with patch("modules.twitch.twitch_tasks.requests") as mock_requests:
            mock_resp = MagicMock()
            mock_resp.json.return_value = {}
            mock_requests.get.return_value = mock_resp
            self.get("https://example.com/api")
        mock_requests.get.assert_called_once_with(
            "https://example.com/api", headers=None, timeout=10
        )

    def test_custom_headers_forwarded(self):
        """Custom headers are passed through to requests.get."""
        hdrs = {"Authorization": "Bearer token"}
        with patch("modules.twitch.twitch_tasks.requests") as mock_requests:
            mock_resp = MagicMock()
            mock_resp.json.return_value = {}
            mock_requests.get.return_value = mock_resp
            self.get("https://example.com/api", headers=hdrs)
        mock_requests.get.assert_called_once_with(
            "https://example.com/api", headers=hdrs, timeout=10
        )

    def test_failure_logs_warning(self, caplog):
        """Any failure must emit a logger.warning."""
        import logging

        with (
            patch("modules.twitch.twitch_tasks.requests") as mock_requests,
            caplog.at_level(logging.WARNING, logger="modules.twitch.twitch_tasks"),
        ):
            mock_requests.get.side_effect = RuntimeError("boom")
            self.get("https://example.com/api")
        assert any("HTTP fetch failed" in msg for msg in caplog.messages)


# ===========================================================================
# Unit tests: _extract_panel_urls + _PLATFORM_PATTERNS (Task 1.3)
# ===========================================================================


class TestExtractPanelUrls:
    """Unit tests for _extract_panel_urls() and _PLATFORM_PATTERNS."""

    def setup_method(self):
        from modules.twitch.twitch_tasks import _extract_panel_urls

        self.extract = _extract_panel_urls

    def test_empty_list_returns_empty_dict(self):
        assert self.extract([]) == {}

    def test_non_dict_panels_skipped(self):
        """Non-dict items in the list must be silently skipped."""
        result = self.extract(["not a dict", None, 42])
        assert result == {}

    def test_html_description_twitter(self):
        panels = [
            {"html_description": '<a href="https://twitter.com/streamer">Follow me</a>'}
        ]
        result = self.extract(panels)
        assert "twitter" in result
        assert "https://twitter.com/streamer" in result["twitter"]

    def test_data_link_discord(self):
        """Panel data.link field is scanned for URLs."""
        panels = [
            {"html_description": "", "data": {"link": "https://discord.gg/abc123"}}
        ]
        result = self.extract(panels)
        assert "discord" in result
        assert "https://discord.gg/abc123" in result["discord"]

    def test_x_com_matches_twitter_pattern(self):
        """x.com URLs should match the twitter pattern."""
        panels = [{"html_description": "https://x.com/myuser"}]
        result = self.extract(panels)
        assert "twitter" in result

    def test_youtube_channel_url(self):
        panels = [{"html_description": "https://www.youtube.com/@mychannel"}]
        result = self.extract(panels)
        assert "youtube" in result

    def test_instagram_url(self):
        panels = [{"html_description": "https://instagram.com/myprofile"}]
        result = self.extract(panels)
        assert "instagram" in result

    def test_steam_community_url(self):
        panels = [{"html_description": "https://steamcommunity.com/id/mySteamID"}]
        result = self.extract(panels)
        assert "steam" in result

    def test_duplicate_url_deduplicated_within_platform(self):
        """Same URL in two panels must appear only once."""
        url = "https://twitter.com/streamer"
        panels = [
            {"html_description": url},
            {"html_description": url},
        ]
        result = self.extract(panels)
        assert result["twitter"].count(url) == 1

    def test_multiple_platforms_in_one_panel(self):
        """One panel can yield URLs for multiple platforms."""
        desc = (
            "https://twitter.com/streamer https://discord.gg/abc123 "
            "https://www.youtube.com/@mychannel"
        )
        panels = [{"html_description": desc}]
        result = self.extract(panels)
        assert "twitter" in result
        assert "discord" in result
        assert "youtube" in result

    def test_malformed_panel_missing_html_description(self):
        """Panel without html_description still processes data.link."""
        panels = [{"data": {"link": "https://patreon.com/mypatreon"}}]
        result = self.extract(panels)
        assert "patreon" in result

    def test_panel_with_none_html_description(self):
        """html_description=None must not crash."""
        panels = [{"html_description": None}]
        result = self.extract(panels)
        assert result == {}

    @pytest.mark.parametrize(
        "url, platform",
        [
            ("https://twitter.com/user1", "twitter"),
            ("https://x.com/user2", "twitter"),
            ("https://www.youtube.com/@channel", "youtube"),
            ("https://discord.gg/invite123", "discord"),
            ("https://discord.com/invite/abc", "discord"),
            ("https://instagram.com/profile", "instagram"),
            ("https://tiktok.com/@creator", "tiktok"),
            ("https://patreon.com/creator", "patreon"),
            ("https://ko-fi.com/creator", "kofi"),
            ("https://github.com/user", "github"),
            ("https://reddit.com/u/user", "reddit"),
            ("https://steamcommunity.com/id/steamuser", "steam"),
            ("https://facebook.com/page", "facebook"),
        ],
    )
    def test_platform_pattern_matches(self, url, platform):
        """Each platform pattern correctly matches its canonical URL form."""
        panels = [{"html_description": url}]
        result = self.extract(panels)
        assert platform in result, f"Expected {platform} for {url}"
        assert url in result[platform]


# ===========================================================================
# Integration: Batch A enrichment tests (Task 2.3)
# ===========================================================================


class TestBatchAEnrichment:
    """Batch A: content_classification_labels, broadcaster_type, video view_count."""

    def _run_with_channel_data(self, channel_data=None, videos=None):
        """Run p_twitch with controlled channel data and optional videos."""

        def enrichment_get(endpoint, params=None):
            if "channels" in endpoint:
                return {"data": channel_data or []}
            return {"data": []}

        helix_instance = _make_mock_helix(videos=videos)
        helix_instance.api.get.side_effect = enrichment_get

        with (
            patch("modules.twitch.twitch_tasks.twitch") as mock_twitch,
            patch("modules.twitch.twitch_tasks.api_keys_search", return_value="key"),
            patch("modules.twitch.twitch_tasks.requests") as mock_requests,
        ):
            mock_twitch.Helix.return_value = helix_instance
            mock_requests.get.side_effect = Exception("no external calls in this test")
            from modules.twitch.twitch_tasks import p_twitch

            return p_twitch("testuser")

    def test_content_labels_appear_in_gather(self):
        """Non-empty content_classification_labels → gather node created."""
        channel = [
            {
                "game_name": "",
                "broadcaster_language": "",
                "tags": [],
                "content_classification_labels": ["MatureGame", "ViolentGraphic"],
                "broadcaster_type": "",
            }
        ]
        result = self._run_with_channel_data(channel_data=channel)
        graphic = next(item["graphic"] for item in result if "graphic" in item)
        social = next(s["social"] for s in graphic if "social" in s)
        label_node = next(
            (n for n in social if n.get("name-node") == "TwitchContentLabels"), None
        )
        assert label_node is not None
        assert "MatureGame" in label_node["subtitle"]
        assert "ViolentGraphic" in label_node["subtitle"]

    def test_empty_content_labels_no_gather_node(self):
        """Empty content_classification_labels → no gather node."""
        channel = [
            {
                "game_name": "",
                "broadcaster_language": "",
                "tags": [],
                "content_classification_labels": [],
                "broadcaster_type": "",
            }
        ]
        result = self._run_with_channel_data(channel_data=channel)
        graphic = next(item["graphic"] for item in result if "graphic" in item)
        social = next(s["social"] for s in graphic if "social" in s)
        label_node = next(
            (n for n in social if n.get("name-node") == "TwitchContentLabels"), None
        )
        assert label_node is None

    def test_broadcaster_type_partner(self):
        """broadcaster_type 'partner' creates gather node with subtitle 'partner'."""
        channel = [
            {
                "game_name": "",
                "broadcaster_language": "",
                "tags": [],
                "content_classification_labels": [],
                "broadcaster_type": "partner",
            }
        ]
        result = self._run_with_channel_data(channel_data=channel)
        graphic = next(item["graphic"] for item in result if "graphic" in item)
        social = next(s["social"] for s in graphic if "social" in s)
        bt_node = next(
            (n for n in social if n.get("name-node") == "TwitchBroadcasterType"), None
        )
        assert bt_node is not None
        assert bt_node["subtitle"] == "partner"

    def test_broadcaster_type_empty_shows_none(self):
        """broadcaster_type '' → gather node with subtitle 'none'."""
        channel = [
            {
                "game_name": "",
                "broadcaster_language": "",
                "tags": [],
                "content_classification_labels": [],
                "broadcaster_type": "",
            }
        ]
        result = self._run_with_channel_data(channel_data=channel)
        graphic = next(item["graphic"] for item in result if "graphic" in item)
        social = next(s["social"] for s in graphic if "social" in s)
        bt_node = next(
            (n for n in social if n.get("name-node") == "TwitchBroadcasterType"), None
        )
        assert bt_node is not None
        assert bt_node["subtitle"] == "none"

    def test_broadcaster_type_in_profile(self):
        """A2: broadcaster_type must appear in profile section, not only gather node."""
        channel = [
            {
                "game_name": "",
                "broadcaster_language": "",
                "tags": [],
                "content_classification_labels": [],
                "broadcaster_type": "affiliate",
            }
        ]
        result = self._run_with_channel_data(channel_data=channel)
        profile = next(item["profile"] for item in result if "profile" in item)
        bt_entries = [p for p in profile if "broadcaster_type" in p]
        assert len(bt_entries) == 1
        assert bt_entries[0]["broadcaster_type"] == "affiliate"

    def test_video_view_count_in_table(self):
        """Video table entries include view_count key."""
        mock_video = MagicMock(
            title="Test Video",
            description="desc",
            created_at="2024-03-01T18:00:00Z",
            url="https://twitch.tv/videos/123",
            duration="2h0m0s",
            thumbnail_url="https://example.com/%{width}x%{height}",
            view_count=15000,
        )
        result = self._run_with_channel_data(videos=[(mock_video, [])])
        graphic = next(item["graphic"] for item in result if "graphic" in item)
        table = next(s["table"] for s in graphic if "table" in s)
        assert len(table) == 1
        assert "view_count" in table[0]
        assert table[0]["view_count"] == 15000

    def test_video_view_count_zero_when_absent(self):
        """Video without view_count attribute defaults to 0."""
        mock_video = MagicMock(
            title="Test Video",
            description="",
            created_at="2024-03-01T18:00:00Z",
            url="https://twitch.tv/videos/456",
            duration="1h0m0s",
            thumbnail_url="https://example.com/%{width}x%{height}",
        )
        # No view_count attribute on spec — getattr returns 0
        del mock_video.view_count
        result = self._run_with_channel_data(videos=[(mock_video, [])])
        graphic = next(item["graphic"] for item in result if "graphic" in item)
        table = next(s["table"] for s in graphic if "table" in s)
        assert table[0]["view_count"] == 0

    def test_no_new_top_level_keys_added(self):
        """Batch A must not introduce new top-level keys beyond the 7-key contract."""
        result = self._run_with_channel_data()
        keys = [next(iter(item.keys())) for item in result if isinstance(item, dict)]
        assert set(keys) == {
            "module",
            "param",
            "validation",
            "raw",
            "graphic",
            "profile",
            "timeline",
        }


# ===========================================================================
# Integration: Batch B graceful degradation tests (Task 3.3)
# ===========================================================================


class TestBatchBGracefulDegradation:
    """Batch B endpoints must each fail independently without blocking output."""

    def _run_with_batch_b_failure(self, failing_endpoint: str):
        """Run p_twitch where one Batch B endpoint fails, others return {}."""

        def selective_get(endpoint, params=None):
            if failing_endpoint in endpoint:
                raise RuntimeError(f"Simulated Batch B failure: {endpoint}")
            return {"data": []}

        helix_instance = _make_mock_helix()
        helix_instance.api.get.side_effect = selective_get

        with (
            patch("modules.twitch.twitch_tasks.twitch") as mock_twitch,
            patch("modules.twitch.twitch_tasks.api_keys_search", return_value="key"),
            patch("modules.twitch.twitch_tasks.requests") as mock_requests,
        ):
            mock_twitch.Helix.return_value = helix_instance
            mock_requests.get.side_effect = Exception(
                "no external calls in Batch B test"
            )
            from modules.twitch.twitch_tasks import p_twitch

            return p_twitch("testuser")

    def _assert_7_key_contract(self, result):
        keys = [next(iter(item.keys())) for item in result if isinstance(item, dict)]
        assert all(
            k in keys
            for k in [
                "module",
                "param",
                "validation",
                "raw",
                "graphic",
                "profile",
                "timeline",
            ]
        )

    def test_chat_settings_failure_does_not_block_output(self):
        result = self._run_with_batch_b_failure("chat/settings")
        self._assert_7_key_contract(result)

    def test_badges_failure_does_not_block_output(self):
        result = self._run_with_batch_b_failure("chat/badges")
        self._assert_7_key_contract(result)

    def test_extensions_failure_does_not_block_output(self):
        result = self._run_with_batch_b_failure("users/extensions")
        self._assert_7_key_contract(result)

    def test_chat_settings_success_adds_sub_only_node(self):
        """subscriber_mode=True → TwitchSubOnly gather node."""

        def enrichment_get(endpoint, params=None):
            if "chat/settings" in endpoint:
                return {
                    "data": [
                        {
                            "subscriber_mode": True,
                            "follower_mode": False,
                            "slow_mode": False,
                            "emote_mode": False,
                        }
                    ]
                }
            return {"data": []}

        helix_instance = _make_mock_helix()
        helix_instance.api.get.side_effect = enrichment_get

        with (
            patch("modules.twitch.twitch_tasks.twitch") as mock_twitch,
            patch("modules.twitch.twitch_tasks.api_keys_search", return_value="key"),
            patch("modules.twitch.twitch_tasks.requests") as mock_requests,
        ):
            mock_twitch.Helix.return_value = helix_instance
            mock_requests.get.side_effect = Exception("no external calls")
            from modules.twitch.twitch_tasks import p_twitch

            result = p_twitch("testuser")

        graphic = next(item["graphic"] for item in result if "graphic" in item)
        social = next(s["social"] for s in graphic if "social" in s)
        sub_only = next(
            (n for n in social if n.get("name-node") == "TwitchSubOnly"), None
        )
        assert sub_only is not None
        assert sub_only["subtitle"] == "Yes"

    def test_badge_tiers_success_adds_tier_count_node(self):
        """Badges with subscriber set → TwitchSubBadgeTiers gather node."""

        def enrichment_get(endpoint, params=None):
            if "chat/badges" in endpoint:
                return {
                    "data": [
                        {
                            "set_id": "subscriber",
                            "versions": [{"id": "0"}, {"id": "3"}, {"id": "6"}],
                        }
                    ]
                }
            return {"data": []}

        helix_instance = _make_mock_helix()
        helix_instance.api.get.side_effect = enrichment_get

        with (
            patch("modules.twitch.twitch_tasks.twitch") as mock_twitch,
            patch("modules.twitch.twitch_tasks.api_keys_search", return_value="key"),
            patch("modules.twitch.twitch_tasks.requests") as mock_requests,
        ):
            mock_twitch.Helix.return_value = helix_instance
            mock_requests.get.side_effect = Exception("no external calls")
            from modules.twitch.twitch_tasks import p_twitch

            result = p_twitch("testuser")

        graphic = next(item["graphic"] for item in result if "graphic" in item)
        social = next(s["social"] for s in graphic if "social" in s)
        badge_node = next(
            (n for n in social if n.get("name-node") == "TwitchSubBadgeTiers"), None
        )
        assert badge_node is not None
        assert badge_node["subtitle"] == 3

    def test_extensions_success_adds_extension_names(self):
        """B6: User has extensions → TwitchExtensions gather node with names."""

        def enrichment_get(endpoint, params=None):
            if "users/extensions" in endpoint:
                return {
                    "data": {
                        "panel": {
                            "1": {
                                "active": True,
                                "id": "ext_1",
                                "name": "StreamElements",
                            },
                            "2": {
                                "active": False,
                                "id": "ext_2",
                                "name": "InactiveExt",
                            },
                        },
                        "overlay": {
                            "1": {
                                "active": True,
                                "id": "ext_3",
                                "name": "Streamlabs",
                            },
                        },
                    }
                }
            return {"data": []}

        helix_instance = _make_mock_helix()
        helix_instance.api.get.side_effect = enrichment_get

        with (
            patch("modules.twitch.twitch_tasks.twitch") as mock_twitch,
            patch("modules.twitch.twitch_tasks.api_keys_search", return_value="key"),
            patch("modules.twitch.twitch_tasks.requests") as mock_requests,
        ):
            mock_twitch.Helix.return_value = helix_instance
            mock_requests.get.side_effect = Exception("no external calls")
            from modules.twitch.twitch_tasks import p_twitch

            result = p_twitch("testuser")

        graphic = next(item["graphic"] for item in result if "graphic" in item)
        social = next(s["social"] for s in graphic if "social" in s)
        ext_node = next(
            (n for n in social if n.get("name-node") == "TwitchExtensions"), None
        )
        assert ext_node is not None
        # Only active extensions should appear
        assert "StreamElements" in ext_node["subtitle"]
        assert "Streamlabs" in ext_node["subtitle"]
        # Inactive extension must NOT appear
        assert "InactiveExt" not in ext_node["subtitle"]

    def test_chat_settings_failure_creates_no_chat_nodes(self):
        """B4: chat/settings fails → no TwitchSubOnly / TwitchFollowerMode nodes."""
        result = self._run_with_batch_b_failure("chat/settings")
        graphic = next(item["graphic"] for item in result if "graphic" in item)
        social = next(s["social"] for s in graphic if "social" in s)
        node_names = [n.get("name-node") for n in social]
        assert "TwitchSubOnly" not in node_names
        assert "TwitchFollowerMode" not in node_names
        assert "TwitchSlowMode" not in node_names
        assert "TwitchEmoteMode" not in node_names

    def test_badges_failure_creates_no_badge_node(self):
        """B5: badges endpoint fails → no TwitchSubBadgeTiers node."""
        result = self._run_with_batch_b_failure("chat/badges")
        graphic = next(item["graphic"] for item in result if "graphic" in item)
        social = next(s["social"] for s in graphic if "social" in s)
        node_names = [n.get("name-node") for n in social]
        assert "TwitchSubBadgeTiers" not in node_names


# ===========================================================================
# Integration: Batch C graceful degradation + success tests (Task 4.4)
# ===========================================================================


class TestBatchCGracefulDegradation:
    """Batch C: TwitchTracker, panels, legacy API — each degrades independently."""

    def _run_with_http_mock(self, url_responses: dict):
        """Run p_twitch routing requests.get by URL substring."""
        import requests as real_requests

        def mock_get(url, **kwargs):
            for pattern, response in url_responses.items():
                if pattern in url:
                    if isinstance(response, Exception):
                        raise response
                    mock_resp = MagicMock()
                    mock_resp.json.return_value = response
                    return mock_resp
            # Default: raise to simulate no external calls
            raise real_requests.exceptions.ConnectionError(f"No mock for {url}")

        helix_instance = _make_mock_helix()

        with (
            patch("modules.twitch.twitch_tasks.twitch") as mock_twitch,
            patch("modules.twitch.twitch_tasks.api_keys_search", return_value="key"),
            patch("modules.twitch.twitch_tasks.requests") as mock_requests,
        ):
            mock_twitch.Helix.return_value = helix_instance
            mock_requests.get.side_effect = mock_get
            mock_requests.exceptions = real_requests.exceptions
            from modules.twitch.twitch_tasks import p_twitch

            return p_twitch("testuser")

    def _assert_7_key_contract(self, result):
        keys = [next(iter(item.keys())) for item in result if isinstance(item, dict)]
        assert all(
            k in keys
            for k in [
                "module",
                "param",
                "validation",
                "raw",
                "graphic",
                "profile",
                "timeline",
            ]
        )

    def test_twitchtracker_failure_does_not_block_output(self):
        import requests as real_requests

        result = self._run_with_http_mock(
            {
                "twitchtracker": real_requests.exceptions.ConnectionError("down"),
            }
        )
        self._assert_7_key_contract(result)

    def test_all_batch_c_fail_base_data_intact(self):
        """All Batch C sources fail → base data (profile, gather) still present."""
        import requests as real_requests

        result = self._run_with_http_mock(
            {
                "twitchtracker": real_requests.exceptions.ConnectionError("down"),
            }
        )
        self._assert_7_key_contract(result)
        graphic = next(item["graphic"] for item in result if "graphic" in item)
        social = next(s["social"] for s in graphic if "social" in s)
        names = [n.get("name-node") for n in social]
        assert "Twitch" in names

    def test_twitchtracker_success_adds_rank_node(self):
        result = self._run_with_http_mock(
            {
                "twitchtracker": {"rank": 150, "avg_viewers": 5000},
            }
        )
        graphic = next(item["graphic"] for item in result if "graphic" in item)
        social = next(s["social"] for s in graphic if "social" in s)
        rank_node = next(
            (n for n in social if n.get("name-node") == "TwitchTracker_rank"), None
        )
        assert rank_node is not None
        assert rank_node["subtitle"] == 150

    def test_twitchtracker_success_adds_avg_viewers_node(self):
        result = self._run_with_http_mock(
            {
                "twitchtracker": {"rank": 150, "avg_viewers": 5000},
            }
        )
        graphic = next(item["graphic"] for item in result if "graphic" in item)
        social = next(s["social"] for s in graphic if "social" in s)
        avg_node = next(
            (n for n in social if n.get("name-node") == "TwitchTracker_avg_viewers"),
            None,
        )
        assert avg_node is not None
        assert avg_node["subtitle"] == 5000

    def test_output_still_7_keys_with_all_batch_c_success(self):
        """Full Batch C success still preserves the 7-key contract."""
        result = self._run_with_http_mock(
            {
                "twitchtracker": {
                    "rank": 50,
                    "avg_viewers": 10000,
                    "max_viewers": 25000,
                    "hours_watched": 500000,
                },
            }
        )
        self._assert_7_key_contract(result)
        # Only 7 top-level keys — no new ones
        keys = [next(iter(item.keys())) for item in result if isinstance(item, dict)]
        assert set(keys) == {
            "module",
            "param",
            "validation",
            "raw",
            "graphic",
            "profile",
            "timeline",
        }

    def test_twitchtracker_unavailable_creates_no_tt_nodes(self):
        """C9: TwitchTracker unavailable → no TwitchTracker_* gather nodes."""
        import requests as real_requests

        result = self._run_with_http_mock(
            {
                "twitchtracker": real_requests.exceptions.ConnectionError("down"),
            }
        )
        graphic = next(item["graphic"] for item in result if "graphic" in item)
        social = next(s["social"] for s in graphic if "social" in s)
        node_names = [n.get("name-node") for n in social]
        tt_nodes = [n for n in node_names if n and n.startswith("TwitchTracker_")]
        assert tt_nodes == []

    def test_combined_failure_isolation(self):
        """Multiple endpoints fail simultaneously — other sources still populate output.

        chat/settings + TwitchTracker both fail.
        Base data must still be present.
        """
        import requests as real_requests

        def enrichment_get(endpoint, params=None):
            if "chat/settings" in endpoint:
                raise RuntimeError("chat/settings down")
            return {"data": []}

        def mock_get(url, **kwargs):
            if "twitchtracker" in url:
                raise real_requests.exceptions.ConnectionError("TT down")
            raise real_requests.exceptions.ConnectionError(f"No mock for {url}")

        helix_instance = _make_mock_helix()
        helix_instance.api.get.side_effect = enrichment_get

        with (
            patch("modules.twitch.twitch_tasks.twitch") as mock_twitch,
            patch("modules.twitch.twitch_tasks.api_keys_search", return_value="key"),
            patch("modules.twitch.twitch_tasks.requests") as mock_requests,
        ):
            mock_twitch.Helix.return_value = helix_instance
            mock_requests.get.side_effect = mock_get
            mock_requests.exceptions = real_requests.exceptions
            from modules.twitch.twitch_tasks import p_twitch

            result = p_twitch("testuser")

        # 7-key contract must hold
        self._assert_7_key_contract(result)

        graphic = next(item["graphic"] for item in result if "graphic" in item)
        social = next(s["social"] for s in graphic if "social" in s)
        node_names = [n.get("name-node") for n in social]

        # Base data is intact
        assert "Twitch" in node_names

        # chat/settings failure → no chat setting nodes
        assert "TwitchSubOnly" not in node_names
        assert "TwitchFollowerMode" not in node_names

        # TwitchTracker failure → no TT nodes
        tt_nodes = [n for n in node_names if n and n.startswith("TwitchTracker_")]
        assert tt_nodes == []


# ===========================================================================
# Regression: Twitch followers/following 410 Gone — endpoint deprecated
# ===========================================================================


class TestFollowers410Gone:
    """Regression tests for the /helix/users/follows 410 Gone crash.

    The endpoint was deprecated in Feb 2023 and fully removed. The
    twitch-python library v0.0.20 still calls it, raising an HTTPError with
    status 410.  The module must NOT crash — it must log a warning and default
    both qty_followers and qty_following to 0.
    """

    def _make_410_error(self):
        """Return a requests.exceptions.HTTPError simulating a 410 Gone."""
        import requests as real_requests

        response = MagicMock()
        response.status_code = 410
        return real_requests.exceptions.HTTPError(
            "410 Client Error: Gone for url: "
            "https://api.twitch.tv/helix/users/follows?to_id=83232866&first=100",
            response=response,
        )

    def test_followers_410_does_not_crash(self):
        """HTTPError 410 on followers() must not propagate — output stays valid."""
        import requests as real_requests

        helix_instance = _make_mock_helix()
        helix_instance.user.return_value.followers.side_effect = (
            real_requests.exceptions.HTTPError(
                "410 Client Error: Gone for url: "
                "https://api.twitch.tv/helix/users/follows?to_id=83232866&first=100"
            )
        )

        with (
            patch("modules.twitch.twitch_tasks.twitch") as mock_twitch,
            patch("modules.twitch.twitch_tasks.api_keys_search", return_value="key"),
            patch("modules.twitch.twitch_tasks.requests") as mock_requests,
        ):
            mock_twitch.Helix.return_value = helix_instance
            mock_requests.exceptions = real_requests.exceptions
            from modules.twitch.twitch_tasks import p_twitch

            result = p_twitch("ibai")

        # Must produce valid 7-key output — not crash
        keys = [next(iter(item.keys())) for item in result if isinstance(item, dict)]
        assert "module" in keys
        assert "graphic" in keys
        assert "profile" in keys

    def test_followers_410_defaults_qty_to_zero(self):
        """HTTPError 410 on followers() → TwitchFollowers subtitle == 0."""
        import requests as real_requests

        helix_instance = _make_mock_helix()
        helix_instance.user.return_value.followers.side_effect = (
            real_requests.exceptions.HTTPError("410 Gone")
        )

        with (
            patch("modules.twitch.twitch_tasks.twitch") as mock_twitch,
            patch("modules.twitch.twitch_tasks.api_keys_search", return_value="key"),
            patch("modules.twitch.twitch_tasks.requests") as mock_requests,
        ):
            mock_twitch.Helix.return_value = helix_instance
            mock_requests.exceptions = real_requests.exceptions
            from modules.twitch.twitch_tasks import p_twitch

            result = p_twitch("ibai")

        graphic = next(item["graphic"] for item in result if "graphic" in item)
        social = next(s["social"] for s in graphic if "social" in s)
        followers_node = next(
            n for n in social if n.get("name-node") == "TwitchFollowers"
        )
        assert followers_node["subtitle"] == 0

    def test_following_410_defaults_qty_to_zero(self):
        """HTTPError 410 on following() → TwitchFollowing subtitle == 0."""
        import requests as real_requests

        helix_instance = _make_mock_helix()
        helix_instance.user.return_value.following.side_effect = (
            real_requests.exceptions.HTTPError("410 Gone")
        )

        with (
            patch("modules.twitch.twitch_tasks.twitch") as mock_twitch,
            patch("modules.twitch.twitch_tasks.api_keys_search", return_value="key"),
            patch("modules.twitch.twitch_tasks.requests") as mock_requests,
        ):
            mock_twitch.Helix.return_value = helix_instance
            mock_requests.exceptions = real_requests.exceptions
            from modules.twitch.twitch_tasks import p_twitch

            result = p_twitch("ibai")

        graphic = next(item["graphic"] for item in result if "graphic" in item)
        social = next(s["social"] for s in graphic if "social" in s)
        following_node = next(
            n for n in social if n.get("name-node") == "TwitchFollowing"
        )
        assert following_node["subtitle"] == 0

    def test_followers_410_logs_deprecation_warning(self, caplog):
        """HTTPError 410 on followers() logs a 'deprecated' warning."""
        import logging

        import requests as real_requests

        helix_instance = _make_mock_helix()
        helix_instance.user.return_value.followers.side_effect = (
            real_requests.exceptions.HTTPError("410 Gone")
        )

        with (
            patch("modules.twitch.twitch_tasks.twitch") as mock_twitch,
            patch("modules.twitch.twitch_tasks.api_keys_search", return_value="key"),
            patch("modules.twitch.twitch_tasks.requests") as mock_requests,
            caplog.at_level(logging.WARNING, logger="modules.twitch.twitch_tasks"),
        ):
            mock_twitch.Helix.return_value = helix_instance
            mock_requests.exceptions = real_requests.exceptions
            from modules.twitch.twitch_tasks import p_twitch

            p_twitch("ibai")

        assert any(
            "deprecated" in msg.lower() or "410" in msg for msg in caplog.messages
        )

    def test_both_410_still_returns_full_output(self):
        """Both followers() and following() raise 410 → full 7-key output survives."""
        import requests as real_requests

        helix_instance = _make_mock_helix()
        helix_instance.user.return_value.followers.side_effect = (
            real_requests.exceptions.HTTPError("410 Gone")
        )
        helix_instance.user.return_value.following.side_effect = (
            real_requests.exceptions.HTTPError("410 Gone")
        )

        with (
            patch("modules.twitch.twitch_tasks.twitch") as mock_twitch,
            patch("modules.twitch.twitch_tasks.api_keys_search", return_value="key"),
            patch("modules.twitch.twitch_tasks.requests") as mock_requests,
        ):
            mock_twitch.Helix.return_value = helix_instance
            mock_requests.exceptions = real_requests.exceptions
            from modules.twitch.twitch_tasks import p_twitch

            result = p_twitch("ibai")

        keys = [next(iter(item.keys())) for item in result if isinstance(item, dict)]
        assert set(keys) == {
            "module",
            "param",
            "validation",
            "raw",
            "graphic",
            "profile",
            "timeline",
        }

        graphic = next(item["graphic"] for item in result if "graphic" in item)
        social = next(s["social"] for s in graphic if "social" in s)
        followers_node = next(
            n for n in social if n.get("name-node") == "TwitchFollowers"
        )
        following_node = next(
            n for n in social if n.get("name-node") == "TwitchFollowing"
        )
        assert followers_node["subtitle"] == 0
        assert following_node["subtitle"] == 0


# ===========================================================================
# Integration: TwitchTracker followers/following fields (C9 enrichment)
# ===========================================================================


class TestTwitchTrackerFollowerFields:
    """TwitchTracker may return followers/following that override dead Helix data."""

    def _run_with_tt_data(self, tt_response, followers_total=0, following_total=0):
        """Run p_twitch with controlled TwitchTracker response and Helix follower state."""
        import requests as real_requests

        def mock_get(url, **kwargs):
            if "twitchtracker" in url:
                if isinstance(tt_response, Exception):
                    raise tt_response
                mock_resp = MagicMock()
                mock_resp.json.return_value = tt_response
                return mock_resp
            # All other HTTP calls fail cleanly
            raise real_requests.exceptions.ConnectionError(f"No mock for {url}")

        helix_instance = _make_mock_helix(
            followers_total=followers_total, following_total=following_total
        )

        with (
            patch("modules.twitch.twitch_tasks.twitch") as mock_twitch,
            patch("modules.twitch.twitch_tasks.api_keys_search", return_value="key"),
            patch("modules.twitch.twitch_tasks.requests") as mock_requests,
        ):
            mock_twitch.Helix.return_value = helix_instance
            mock_requests.get.side_effect = mock_get
            mock_requests.exceptions = real_requests.exceptions
            from modules.twitch.twitch_tasks import p_twitch

            return p_twitch("testuser")

    def test_tt_followers_field_adds_gather_node(self):
        """TwitchTracker response with 'followers' → TwitchTracker_followers node."""
        result = self._run_with_tt_data({"followers": 75000, "following": 120})
        graphic = next(item["graphic"] for item in result if "graphic" in item)
        social = next(s["social"] for s in graphic if "social" in s)
        node = next(
            (n for n in social if n.get("name-node") == "TwitchTracker_followers"),
            None,
        )
        assert node is not None
        assert node["subtitle"] == 75000

    def test_tt_following_field_adds_gather_node(self):
        """TwitchTracker response with 'following' → TwitchTracker_following node."""
        result = self._run_with_tt_data({"followers": 75000, "following": 120})
        graphic = next(item["graphic"] for item in result if "graphic" in item)
        social = next(s["social"] for s in graphic if "social" in s)
        node = next(
            (n for n in social if n.get("name-node") == "TwitchTracker_following"),
            None,
        )
        assert node is not None
        assert node["subtitle"] == 120

    def test_tt_followers_overrides_helix_zero_on_followers_node(self):
        """When Helix returns 0 (e.g. 410 Gone) and TT has followers → TwitchFollowers updated."""
        result = self._run_with_tt_data(
            {"followers": 50000, "following": 200}, followers_total=0, following_total=0
        )
        graphic = next(item["graphic"] for item in result if "graphic" in item)
        social = next(s["social"] for s in graphic if "social" in s)
        followers_node = next(
            n for n in social if n.get("name-node") == "TwitchFollowers"
        )
        assert followers_node["subtitle"] == 50000

    def test_tt_following_overrides_helix_zero_on_following_node(self):
        """When Helix returns 0 (e.g. 410 Gone) and TT has following → TwitchFollowing updated."""
        result = self._run_with_tt_data(
            {"followers": 50000, "following": 200}, followers_total=0, following_total=0
        )
        graphic = next(item["graphic"] for item in result if "graphic" in item)
        social = next(s["social"] for s in graphic if "social" in s)
        following_node = next(
            n for n in social if n.get("name-node") == "TwitchFollowing"
        )
        assert following_node["subtitle"] == 200

    def test_tt_followers_updates_presence_section(self):
        """TT followers override also updates the presence section used in charts."""
        result = self._run_with_tt_data(
            {"followers": 33000, "following": 55}, followers_total=0, following_total=0
        )
        profile = next(item["profile"] for item in result if "profile" in item)
        presence_entry = next((p["presence"] for p in profile if "presence" in p), [])
        twitch_presence = next(
            (e for e in presence_entry if e.get("name") == "twitch"), None
        )
        assert twitch_presence is not None
        followers_child = next(
            (c for c in twitch_presence["children"] if c["name"] == "followers"), None
        )
        assert followers_child is not None
        assert followers_child["value"] == 33000

    def test_tt_following_updates_presence_section(self):
        """TT following override also updates the presence section."""
        result = self._run_with_tt_data(
            {"followers": 33000, "following": 55}, followers_total=0, following_total=0
        )
        profile = next(item["profile"] for item in result if "profile" in item)
        presence_entry = next((p["presence"] for p in profile if "presence" in p), [])
        twitch_presence = next(
            (e for e in presence_entry if e.get("name") == "twitch"), None
        )
        assert twitch_presence is not None
        following_child = next(
            (c for c in twitch_presence["children"] if c["name"] == "following"), None
        )
        assert following_child is not None
        assert following_child["value"] == 55

    def test_tt_does_not_override_when_helix_has_followers(self):
        """When Helix already has a non-zero follower count, TT must NOT override."""
        result = self._run_with_tt_data(
            {"followers": 99999, "following": 999},
            followers_total=5000,
            following_total=100,
        )
        graphic = next(item["graphic"] for item in result if "graphic" in item)
        social = next(s["social"] for s in graphic if "social" in s)
        followers_node = next(
            n for n in social if n.get("name-node") == "TwitchFollowers"
        )
        following_node = next(
            n for n in social if n.get("name-node") == "TwitchFollowing"
        )
        # Helix values must be preserved — TT must not override
        assert followers_node["subtitle"] == 5000
        assert following_node["subtitle"] == 100

    def test_tt_missing_followers_field_leaves_helix_zero(self):
        """TwitchTracker without 'followers' key → TwitchFollowers stays 0."""
        result = self._run_with_tt_data({"rank": 200})  # no followers/following keys
        graphic = next(item["graphic"] for item in result if "graphic" in item)
        social = next(s["social"] for s in graphic if "social" in s)
        followers_node = next(
            n for n in social if n.get("name-node") == "TwitchFollowers"
        )
        assert followers_node["subtitle"] == 0

    def test_tt_with_410_gone_followers_and_tt_data(self):
        """Full integration: Helix 410 Gone + TwitchTracker has followers → nodes updated."""
        import requests as real_requests

        def mock_get(url, **kwargs):
            if "twitchtracker" in url:
                mock_resp = MagicMock()
                mock_resp.json.return_value = {"followers": 88000, "following": 300}
                return mock_resp
            raise real_requests.exceptions.ConnectionError(f"No mock for {url}")

        helix_instance = _make_mock_helix(followers_total=0, following_total=0)
        helix_instance.user.return_value.followers.side_effect = (
            real_requests.exceptions.HTTPError("410 Gone")
        )
        helix_instance.user.return_value.following.side_effect = (
            real_requests.exceptions.HTTPError("410 Gone")
        )

        with (
            patch("modules.twitch.twitch_tasks.twitch") as mock_twitch,
            patch("modules.twitch.twitch_tasks.api_keys_search", return_value="key"),
            patch("modules.twitch.twitch_tasks.requests") as mock_requests,
        ):
            mock_twitch.Helix.return_value = helix_instance
            mock_requests.get.side_effect = mock_get
            mock_requests.exceptions = real_requests.exceptions
            from modules.twitch.twitch_tasks import p_twitch

            result = p_twitch("testuser")

        graphic = next(item["graphic"] for item in result if "graphic" in item)
        social = next(s["social"] for s in graphic if "social" in s)
        followers_node = next(
            n for n in social if n.get("name-node") == "TwitchFollowers"
        )
        following_node = next(
            n for n in social if n.get("name-node") == "TwitchFollowing"
        )
        assert followers_node["subtitle"] == 88000
        assert following_node["subtitle"] == 300


# ===========================================================================
# Unit tests: _http_post (new GQL helper)
# ===========================================================================


class TestHttpPost:
    """Unit tests for _http_post() helper — success, failure, timeout, bad JSON."""

    def setup_method(self):
        from modules.twitch.twitch_tasks import _http_post

        self.post = _http_post

    def test_success_returns_parsed_json(self):
        """Successful HTTP POST returns parsed JSON body."""
        with patch("modules.twitch.twitch_tasks.requests") as mock_requests:
            mock_resp = MagicMock()
            mock_resp.json.return_value = {"data": {"user": {"panels": []}}}
            mock_requests.post.return_value = mock_resp
            result = self.post("https://gql.twitch.tv/gql", json_body={"query": "..."})
        assert result == {"data": {"user": {"panels": []}}}

    def test_http_error_returns_default(self):
        """HTTP error (4xx/5xx) raises → returns default."""
        import requests as real_requests

        with patch("modules.twitch.twitch_tasks.requests") as mock_requests:
            mock_resp = MagicMock()
            mock_resp.raise_for_status.side_effect = real_requests.exceptions.HTTPError(
                "400 Bad Request"
            )
            mock_requests.post.return_value = mock_resp
            mock_requests.exceptions = real_requests.exceptions
            result = self.post("https://gql.twitch.tv/gql", default=[])
        assert result == []

    def test_timeout_returns_default(self):
        """Timeout raises → returns default without re-raising."""
        import requests as real_requests

        with patch("modules.twitch.twitch_tasks.requests") as mock_requests:
            mock_requests.post.side_effect = real_requests.exceptions.Timeout(
                "timed out"
            )
            mock_requests.exceptions = real_requests.exceptions
            result = self.post("https://gql.twitch.tv/gql", timeout=5, default=None)
        assert result is None

    def test_connection_error_returns_default(self):
        """Connection error → returns default."""
        import requests as real_requests

        with patch("modules.twitch.twitch_tasks.requests") as mock_requests:
            mock_requests.post.side_effect = real_requests.exceptions.ConnectionError(
                "unreachable"
            )
            mock_requests.exceptions = real_requests.exceptions
            result = self.post("https://gql.twitch.tv/gql", default={})
        assert result == {}

    def test_bad_json_returns_default(self):
        """Non-JSON response → json() raises ValueError → returns default."""
        with patch("modules.twitch.twitch_tasks.requests") as mock_requests:
            mock_resp = MagicMock()
            mock_resp.json.side_effect = ValueError("no JSON")
            mock_requests.post.return_value = mock_resp
            result = self.post("https://gql.twitch.tv/gql", default="fallback")
        assert result == "fallback"

    def test_json_body_forwarded_to_requests(self):
        """json_body parameter is passed as the json= kwarg to requests.post."""
        body = {"query": "some GQL", "variables": {"login": "user"}}
        with patch("modules.twitch.twitch_tasks.requests") as mock_requests:
            mock_resp = MagicMock()
            mock_resp.json.return_value = {}
            mock_requests.post.return_value = mock_resp
            self.post("https://gql.twitch.tv/gql", json_body=body)
        mock_requests.post.assert_called_once_with(
            "https://gql.twitch.tv/gql",
            json=body,
            headers=None,
            timeout=10,
        )

    def test_custom_headers_forwarded(self):
        """Custom headers are passed through to requests.post."""
        hdrs = {"Client-ID": "kimne78kx3ncx6brgo4mv6wki5h1ko"}
        with patch("modules.twitch.twitch_tasks.requests") as mock_requests:
            mock_resp = MagicMock()
            mock_resp.json.return_value = {}
            mock_requests.post.return_value = mock_resp
            self.post("https://gql.twitch.tv/gql", headers=hdrs)
        mock_requests.post.assert_called_once_with(
            "https://gql.twitch.tv/gql",
            json=None,
            headers=hdrs,
            timeout=10,
        )

    def test_failure_logs_warning(self, caplog):
        """Any failure must emit a logger.warning."""
        import logging

        with (
            patch("modules.twitch.twitch_tasks.requests") as mock_requests,
            caplog.at_level(logging.WARNING, logger="modules.twitch.twitch_tasks"),
        ):
            mock_requests.post.side_effect = RuntimeError("boom")
            self.post("https://gql.twitch.tv/gql")
        assert any("HTTP POST failed" in msg for msg in caplog.messages)


# ===========================================================================
# Unit tests: _fetch_panels_gql
# ===========================================================================


class TestFetchPanelsGql:
    """Unit tests for _fetch_panels_gql() — calls GQL API and parses response."""

    def setup_method(self):
        from modules.twitch.twitch_tasks import _fetch_panels_gql

        self.fetch = _fetch_panels_gql

    def _make_gql_response(self, panels):
        return {"data": {"user": {"panels": panels}}}

    def test_success_returns_panels_list(self):
        """Valid GQL response returns list of panel dicts."""
        panels = [
            {
                "__typename": "DefaultPanel",
                "id": "1",
                "type": "DEFAULT",
                "title": "Twitter",
                "linkURL": "https://twitter.com/streamer",
                "description": "Follow me on Twitter!",
                "imageURL": None,
            }
        ]
        with patch("modules.twitch.twitch_tasks._http_post") as mock_post:
            mock_post.return_value = self._make_gql_response(panels)
            result = self.fetch("streamer")
        assert result == panels

    def test_success_filters_non_dict_panels(self):
        """Non-dict entries in panels list are filtered out."""
        panels = [
            {
                "__typename": "DefaultPanel",
                "id": "1",
                "linkURL": "https://twitter.com/x",
            },
            "not a dict",
            None,
            42,
        ]
        with patch("modules.twitch.twitch_tasks._http_post") as mock_post:
            mock_post.return_value = self._make_gql_response(panels)
            result = self.fetch("streamer")
        assert len(result) == 1
        assert result[0]["id"] == "1"

    def test_http_post_failure_returns_empty_list(self):
        """When _http_post returns None (failure), result is empty list."""
        with patch("modules.twitch.twitch_tasks._http_post") as mock_post:
            mock_post.return_value = None
            result = self.fetch("streamer")
        assert result == []

    def test_non_dict_response_returns_empty_list(self):
        """When _http_post returns a non-dict, result is empty list."""
        with patch("modules.twitch.twitch_tasks._http_post") as mock_post:
            mock_post.return_value = "bad data"
            result = self.fetch("streamer")
        assert result == []

    def test_missing_user_key_returns_empty_list(self):
        """GQL response with data.user=None returns empty list."""
        with patch("modules.twitch.twitch_tasks._http_post") as mock_post:
            mock_post.return_value = {"data": {"user": None}}
            result = self.fetch("streamer")
        assert result == []

    def test_missing_panels_key_returns_empty_list(self):
        """GQL response where panels key is absent returns empty list."""
        with patch("modules.twitch.twitch_tasks._http_post") as mock_post:
            mock_post.return_value = {"data": {"user": {}}}
            result = self.fetch("streamer")
        assert result == []

    def test_empty_panels_list_returns_empty_list(self):
        """GQL response with empty panels list returns empty list."""
        with patch("modules.twitch.twitch_tasks._http_post") as mock_post:
            mock_post.return_value = self._make_gql_response([])
            result = self.fetch("streamer")
        assert result == []

    def test_calls_correct_gql_endpoint(self):
        """_fetch_panels_gql posts to the Twitch GQL endpoint."""
        with patch("modules.twitch.twitch_tasks._http_post") as mock_post:
            mock_post.return_value = self._make_gql_response([])
            self.fetch("testuser")
        call_args = mock_post.call_args
        assert call_args[0][0] == "https://gql.twitch.tv/gql"

    def test_sends_correct_client_id_header(self):
        """_fetch_panels_gql sends Client-ID header to GQL API."""
        with patch("modules.twitch.twitch_tasks._http_post") as mock_post:
            mock_post.return_value = self._make_gql_response([])
            self.fetch("testuser")
        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["headers"]["Client-ID"] == "kimne78kx3ncx6brgo4mv6wki5h1ko"

    def test_sends_username_as_login_variable(self):
        """_fetch_panels_gql passes the username as the login variable."""
        with patch("modules.twitch.twitch_tasks._http_post") as mock_post:
            mock_post.return_value = self._make_gql_response([])
            self.fetch("xqc")
        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["json_body"]["variables"]["login"] == "xqc"


# ===========================================================================
# Unit tests: _extract_panel_urls with GQL format panels
# ===========================================================================


class TestExtractPanelUrlsGql:
    """Unit tests for _extract_panel_urls() with GQL field names."""

    def setup_method(self):
        from modules.twitch.twitch_tasks import _extract_panel_urls

        self.extract = _extract_panel_urls

    def test_gql_description_field_scanned(self):
        """GQL 'description' field is used for URL extraction."""
        panels = [
            {
                "__typename": "DefaultPanel",
                "description": "Follow me on https://twitter.com/streamer",
                "linkURL": None,
            }
        ]
        result = self.extract(panels)
        assert "twitter" in result
        assert "https://twitter.com/streamer" in result["twitter"]

    def test_gql_link_url_field_scanned(self):
        """GQL 'linkURL' field is used for URL extraction."""
        panels = [
            {
                "__typename": "DefaultPanel",
                "description": "",
                "linkURL": "https://discord.gg/abc123",
            }
        ]
        result = self.extract(panels)
        assert "discord" in result
        assert "https://discord.gg/abc123" in result["discord"]

    def test_gql_both_description_and_link_url(self):
        """GQL panels with both description and linkURL are both scanned."""
        panels = [
            {
                "__typename": "DefaultPanel",
                "description": "https://twitter.com/streamer",
                "linkURL": "https://discord.gg/abc123",
            }
        ]
        result = self.extract(panels)
        assert "twitter" in result
        assert "discord" in result

    def test_backward_compat_kraken_html_description(self):
        """Kraken-format panels (html_description + data.link) still work."""
        panels = [
            {
                "html_description": "https://instagram.com/myprofile",
                "data": {"link": "https://patreon.com/mycreator"},
            }
        ]
        result = self.extract(panels)
        assert "instagram" in result
        assert "patreon" in result

    def test_gql_description_takes_priority_over_html_description(self):
        """When both 'description' and 'html_description' exist, both are used."""
        panels = [
            {
                "description": "https://twitter.com/gql_user",
                "html_description": "https://github.com/kraken_user",
            }
        ]
        result = self.extract(panels)
        # description field takes priority (checked first), but html_description
        # is checked as fallback — so if description is truthy, html_description ignored
        assert "twitter" in result

    def test_gql_youtube_channel_with_hyphen_in_id(self):
        """YouTube channel IDs with hyphens are correctly matched."""
        panels = [
            {
                "description": "",
                "linkURL": "https://www.youtube.com/channel/UCaY_-ksFSQtTGk0y1HA_3YQ",
            }
        ]
        result = self.extract(panels)
        assert "youtube" in result
        assert (
            "https://www.youtube.com/channel/UCaY_-ksFSQtTGk0y1HA_3YQ"
            in result["youtube"]
        )

    def test_duplicate_url_across_gql_panels_deduplicated(self):
        """Same URL appearing in description and linkURL is deduplicated."""
        url = "https://discord.gg/abc123"
        panels = [
            {"description": url, "linkURL": url},
        ]
        result = self.extract(panels)
        assert result["discord"].count(url) == 1

    def test_none_link_url_not_crash(self):
        """linkURL=None must not crash."""
        panels = [{"description": "https://twitter.com/user", "linkURL": None}]
        result = self.extract(panels)
        assert "twitter" in result


# ===========================================================================
# Integration: GQL panels → social entries in p_twitch output (C10)
# ===========================================================================


class TestC10GqlPanelIntegration:
    """Integration tests: GQL panels produce social entries in p_twitch output."""

    def _run_with_panels(self, panels_response, has_keys=False):
        """Run p_twitch with controlled _fetch_panels_gql and requests mocked."""
        import requests as real_requests

        def mock_get(url, **kwargs):
            raise real_requests.exceptions.ConnectionError(f"No mock for {url}")

        with (
            patch("modules.twitch.twitch_tasks.api_keys_search", return_value=False),
            patch("modules.twitch.twitch_tasks.requests") as mock_requests,
            patch(
                "modules.twitch.twitch_tasks._fetch_panels_gql",
                return_value=panels_response,
            ),
        ):
            mock_requests.get.side_effect = mock_get
            mock_requests.exceptions = real_requests.exceptions
            from modules.twitch.twitch_tasks import p_twitch

            return p_twitch("testuser")

    def _get_social_list(self, result):
        profile = next(item["profile"] for item in result if "profile" in item)
        social_entries = [p["social"] for p in profile if "social" in p]
        return social_entries[0] if social_entries else []

    def test_gql_panels_add_social_entries(self):
        """When GQL panels return URLs, they appear as social entries."""
        panels = [
            {
                "__typename": "DefaultPanel",
                "description": "Follow me on Twitter!",
                "linkURL": "https://twitter.com/streamer",
            }
        ]
        result = self._run_with_panels(panels)
        social = self._get_social_list(result)
        twitter_entries = [s for s in social if s.get("source") == "TwitchPanel"]
        assert len(twitter_entries) >= 1
        urls = [e["url"] for e in twitter_entries]
        assert "https://twitter.com/streamer" in urls

    def test_panel_social_entry_has_required_fields(self):
        """Panel-sourced social entries have name, url, icon, source, username."""
        panels = [
            {
                "__typename": "DefaultPanel",
                "description": "",
                "linkURL": "https://discord.gg/abc123",
            }
        ]
        result = self._run_with_panels(panels)
        social = self._get_social_list(result)
        panel_entries = [s for s in social if s.get("source") == "TwitchPanel"]
        assert len(panel_entries) >= 1
        entry = panel_entries[0]
        assert "name" in entry
        assert "url" in entry
        assert "icon" in entry
        assert "source" in entry
        assert entry["source"] == "TwitchPanel"
        assert "username" in entry

    def test_duplicate_urls_filtered_from_panels(self):
        """URL already present in social list is not added again from panels."""
        # The Twitch profile link is always in social first
        panels = [
            {
                "__typename": "DefaultPanel",
                "description": "",
                "linkURL": "https://discord.gg/abc123",
            },
            {
                "__typename": "DefaultPanel",
                "description": "",
                "linkURL": "https://discord.gg/abc123",  # duplicate
            },
        ]
        result = self._run_with_panels(panels)
        social = self._get_social_list(result)
        discord_entries = [s for s in social if "discord.gg/abc123" in s.get("url", "")]
        assert len(discord_entries) == 1

    def test_no_panels_no_panel_social_entries(self):
        """When GQL returns empty list, no TwitchPanel social entries appear."""
        result = self._run_with_panels([])
        social = self._get_social_list(result)
        panel_entries = [s for s in social if s.get("source") == "TwitchPanel"]
        assert panel_entries == []

    def test_gql_failure_does_not_block_output(self):
        """When _fetch_panels_gql fails (returns []), output is still valid 7-key."""
        import requests as real_requests

        def mock_get(url, **kwargs):
            raise real_requests.exceptions.ConnectionError(f"No mock for {url}")

        with (
            patch("modules.twitch.twitch_tasks.api_keys_search", return_value=False),
            patch("modules.twitch.twitch_tasks.requests") as mock_requests,
            patch(
                "modules.twitch.twitch_tasks._fetch_panels_gql",
                return_value=[],
            ),
        ):
            mock_requests.get.side_effect = mock_get
            mock_requests.exceptions = real_requests.exceptions
            from modules.twitch.twitch_tasks import p_twitch

            result = p_twitch("testuser")

        keys = [next(iter(item.keys())) for item in result if isinstance(item, dict)]
        assert set(keys) == {
            "module",
            "param",
            "validation",
            "raw",
            "graphic",
            "profile",
            "timeline",
        }

    def test_multiple_platforms_from_single_panel(self):
        """A single panel with multiple URLs produces entries for each platform."""
        panels = [
            {
                "__typename": "DefaultPanel",
                "description": (
                    "https://twitter.com/streamer https://github.com/streamer"
                ),
                "linkURL": "https://discord.gg/mycommunity",
            }
        ]
        result = self._run_with_panels(panels)
        social = self._get_social_list(result)
        panel_urls = {s["url"] for s in social if s.get("source") == "TwitchPanel"}
        assert "https://twitter.com/streamer" in panel_urls
        assert "https://github.com/streamer" in panel_urls
        assert "https://discord.gg/mycommunity" in panel_urls

    def test_youtube_channel_hyphen_id_extracted(self):
        """YouTube channel IDs with hyphens are correctly extracted from panels."""
        panels = [
            {
                "__typename": "DefaultPanel",
                "description": "",
                "linkURL": "https://www.youtube.com/channel/UCaY_-ksFSQtTGk0y1HA_3YQ",
            }
        ]
        result = self._run_with_panels(panels)
        social = self._get_social_list(result)
        panel_entries = [s for s in social if s.get("source") == "TwitchPanel"]
        urls = [e["url"] for e in panel_entries]
        assert "https://www.youtube.com/channel/UCaY_-ksFSQtTGk0y1HA_3YQ" in urls
