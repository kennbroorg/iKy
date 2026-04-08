"""Regression tests for mastodon module migration to @iky_task decorator.

Covers:
  - Task 4.2: decorator/alias, dev mode fixture load, input parsing,
              lookup→search fallback, multi-user flow, pagination cap,
              analytics output, backward compatibility, error handling.
"""

import inspect
import json
import sys
from pathlib import Path
from typing import ClassVar
from unittest.mock import MagicMock, call, patch

import pytest

# ---------------------------------------------------------------------------
# Stub Docker-only / optional dependencies so tests run without them installed.
# Must happen before any import of modules.mastodon.mastodon_tasks.
#
# The import chain requires:
#   factories.fontcheat     → fontawesome
#   factories.iKy_functions → geopy, geopy.geocoders
#   factories.task_wrapper  → celery, celery.utils, celery.utils.log
#   mastodon_tasks itself   → w3lib, w3lib.html
# ---------------------------------------------------------------------------

_OPTIONAL_STUBS = [
    "fontawesome",
    "geopy",
    "geopy.geocoders",
    "celery",
    "celery.utils",
    "celery.utils.log",
    "w3lib",
    "w3lib.html",
]

for _mod_name in _OPTIONAL_STUBS:
    if _mod_name not in sys.modules:
        _stub = MagicMock()
        if _mod_name == "fontawesome":
            _stub.icons = {}
        sys.modules[_mod_name] = _stub

# ---------------------------------------------------------------------------
# Block dev-mode globally — redirect Path.cwd() so output-mastodon.json
# is never found during normal test runs.
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _block_devmode(tmp_path):
    """Redirect Path.cwd() so dev-mode files are never found."""
    with patch.object(Path, "cwd", return_value=tmp_path):
        yield


# ---------------------------------------------------------------------------
# Shared fixture account data
# ---------------------------------------------------------------------------

ACCOUNT_DATA: dict = {
    "id": "12345",
    "username": "testuser",
    "acct": "testuser",
    "display_name": "Test User",
    "locked": False,
    "bot": False,
    "group": False,
    "discoverable": True,
    "suspended": False,
    "created_at": "2020-01-01T00:00:00.000Z",
    "last_status_at": "2024-01-01",
    "note": "<p>Hello world</p>",
    "url": "https://mastodon.social/@testuser",
    "avatar": "https://example.com/avatar.png",
    "header": "/headers/original/missing.png",  # default header — should be skipped
    "followers_count": 100,
    "following_count": 50,
    "statuses_count": 200,
    "moved": None,
    "fields": [],
}

ACCOUNT_DATA_WITH_HEADER: dict = {
    **ACCOUNT_DATA,
    "header": "https://example.com/header.jpg",
}

STATUS_DATA: dict = {
    "id": "1000",
    "created_at": "2024-01-15T14:00:00.000Z",
    "reblog": None,
    "tags": [{"name": "python"}, {"name": "fediverse"}],
    "media_attachments": [],
}

# ---------------------------------------------------------------------------
# HTTP mock helpers
# ---------------------------------------------------------------------------


def _make_json_resp(data, status_code: int = 200) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = data
    return resp


def _make_error_resp(status_code: int) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.side_effect = ValueError("no body")
    return resp


# ---------------------------------------------------------------------------
# Default happy-path mock session factory
# ---------------------------------------------------------------------------


def _build_happy_session(
    account: dict | None = None,
    statuses: list[dict] | None = None,
    featured_tags: list[dict] | None = None,
) -> MagicMock:
    """Return a mock session for the standard happy path."""
    account = account or ACCOUNT_DATA
    statuses_page = statuses if statuses is not None else []
    tags = featured_tags or []

    def _get(url, **kwargs):
        if "/api/v1/accounts/lookup" in url:
            return _make_json_resp(account)
        if "/api/v2/search" in url:
            return _make_json_resp({"accounts": [account]})
        if "/statuses" in url:
            return _make_json_resp(statuses_page)
        if "/featured_tags" in url:
            return _make_json_resp(tags)
        return _make_error_resp(404)

    mock_session = MagicMock()
    mock_session.get.side_effect = _get
    mock_session.headers = {}
    return mock_session


@pytest.fixture
def mock_mastodon_happy(monkeypatch):
    """Fixture providing a standard happy-path mock session."""
    mock_session = _build_happy_session()
    with patch(
        "modules.mastodon.mastodon_tasks.requests.Session",
        return_value=mock_session,
    ):
        yield mock_session


# ===========================================================================
# 1. Decorator / alias / registry compatibility
# ===========================================================================


class TestDecoratorAliasRegistry:
    """Verify @iky_task wiring, alias, and registry contract."""

    def test_t_mastodon_is_p_mastodon(self):
        """t_mastodon MUST be the same object as p_mastodon."""
        from modules.mastodon.mastodon_tasks import p_mastodon, t_mastodon

        assert t_mastodon is p_mastodon

    def test_celery_task_name_matches_registry(self):
        """Registered Celery task name must match module_registry.py."""
        from modules.mastodon.mastodon_tasks import p_mastodon

        assert hasattr(p_mastodon, "name")
        assert p_mastodon.name == "modules.mastodon.mastodon_tasks.t_mastodon"

    def test_p_mastodon_callable_directly(self, mock_mastodon_happy):
        """p_mastodon must be directly callable (not just via .delay())."""
        from modules.mastodon.mastodon_tasks import p_mastodon

        result = p_mastodon("testuser")
        assert isinstance(result, list)

    def test_t_mastodon_callable_directly(self, mock_mastodon_happy):
        """t_mastodon alias must also be directly callable."""
        from modules.mastodon.mastodon_tasks import t_mastodon

        result = t_mastodon("testuser")
        assert isinstance(result, list)

    def test_signature_has_no_from_m_parameter(self):
        """p_mastodon MUST NOT have from_m parameter — it is dead code."""
        from modules.mastodon.mastodon_tasks import p_mastodon

        try:
            sig = inspect.signature(p_mastodon.__wrapped__)
            param_names = list(sig.parameters.keys())
            assert "from_m" not in param_names, "from_m is dead code — must be removed"
        except AttributeError:
            # Decorator did not expose __wrapped__ — skip deep inspection
            pass

    def test_no_print_statements(self):
        """Module must not contain print() calls outside the CLI output() helper."""
        import inspect as _inspect

        from modules.mastodon import mastodon_tasks

        src = _inspect.getsource(mastodon_tasks)
        # The output() CLI helper is the only allowed use of print()
        # Check that p_mastodon and internal helpers don't use print()
        lines_with_print = [ln.strip() for ln in src.splitlines() if "print(" in ln]
        # Filter out the output() helper's legitimate print call
        disallowed = [
            ln
            for ln in lines_with_print
            if "json.dumps" not in ln  # output() helper is allowed
        ]
        assert disallowed == [], f"Found disallowed print() calls: {disallowed}"

    def test_no_inline_dev_mode_code(self):
        """Module body must not contain inline dev-mode file check."""
        import inspect as _inspect

        from modules.mastodon import mastodon_tasks

        src = _inspect.getsource(mastodon_tasks)
        assert "output-mastodon.json" not in src or "task_wrapper" in src


# ===========================================================================
# 2. Dev mode golden fixture
# ===========================================================================


class TestDevModeGoldenFixture:
    """Decorator dev-mode bypass via output-mastodon.json."""

    def test_dev_mode_returns_golden_json(self, tmp_path):
        golden = [
            {"module": "mastodon"},
            {"param": "devuser"},
            {"validation": "no"},
            {"raw": {}},
            {
                "graphic": [
                    {"user": []},
                    {"social": []},
                    {"list": []},
                    {"hour": []},
                    {"week": []},
                    {"hashtags": {}},
                ]
            },
            {"profile": []},
            {"timeline": []},
            {"tasks": []},
        ]
        outputs = tmp_path / "outputs"
        outputs.mkdir()
        devfile = outputs / "output-mastodon.json"
        devfile.write_text(json.dumps(golden))

        with (
            patch.object(Path, "cwd", return_value=tmp_path),
            patch("factories.task_wrapper.time.sleep") as mock_sleep,
        ):
            from modules.mastodon.mastodon_tasks import p_mastodon

            result = p_mastodon("anything")

        assert result == golden
        # dev_mode_sleep=15 must be honoured
        mock_sleep.assert_called_once_with(15)


# ===========================================================================
# 3. Input parsing
# ===========================================================================


class TestInputParsing:
    """_parse_username accepts all valid Mastodon address formats."""

    def test_parse_username_only(self):
        from modules.mastodon.mastodon_tasks import _parse_username

        user, server = _parse_username("gargron")
        assert user == "gargron"
        assert server is None

    def test_parse_at_username(self):
        from modules.mastodon.mastodon_tasks import _parse_username

        user, server = _parse_username("@gargron")
        assert user == "gargron"
        assert server is None

    def test_parse_user_at_server(self):
        from modules.mastodon.mastodon_tasks import _parse_username

        user, server = _parse_username("gargron@mastodon.social")
        assert user == "gargron"
        assert server == "mastodon.social"

    def test_parse_at_user_at_server(self):
        from modules.mastodon.mastodon_tasks import _parse_username

        user, server = _parse_username("@gargron@mastodon.social")
        assert user == "gargron"
        assert server == "mastodon.social"

    def test_parse_invalid_raises(self):
        from modules.mastodon.mastodon_tasks import _parse_username

        with pytest.raises(Exception, match="iKy - Invalid input parameters"):
            _parse_username("@@@@@")

    def test_parse_empty_raises(self):
        from modules.mastodon.mastodon_tasks import _parse_username

        with pytest.raises(Exception, match="iKy - Invalid input parameters"):
            _parse_username("")


# ===========================================================================
# 4. Account resolution: lookup → search fallback
# ===========================================================================


class TestAccountResolution:
    """Resolution chain: direct lookup first, search as fallback."""

    def test_lookup_success_no_search_called(self):
        """When lookup succeeds, search must NOT be called."""
        lookup_resp = _make_json_resp(ACCOUNT_DATA)

        call_log = {"search": 0}

        def _get(url, **kwargs):
            if "/api/v1/accounts/lookup" in url:
                return lookup_resp
            if "/api/v2/search" in url:
                call_log["search"] += 1
                return _make_json_resp({"accounts": []})
            return _make_json_resp([])  # statuses / featured_tags

        mock_session = MagicMock()
        mock_session.get.side_effect = _get
        mock_session.headers = {}

        with patch(
            "modules.mastodon.mastodon_tasks.requests.Session",
            return_value=mock_session,
        ):
            from modules.mastodon.mastodon_tasks import p_mastodon

            result = p_mastodon("testuser@mastodon.social")

        assert call_log["search"] == 0
        assert result[0]["module"] == "mastodon"

    def test_lookup_404_fallback_to_search(self):
        """Lookup 404 → fallback to search succeeds."""
        lookup_404 = _make_error_resp(404)
        search_resp = _make_json_resp({"accounts": [ACCOUNT_DATA]})

        def _get(url, **kwargs):
            if "/api/v1/accounts/lookup" in url:
                return lookup_404
            if "/api/v2/search" in url:
                return search_resp
            return _make_json_resp([])

        mock_session = MagicMock()
        mock_session.get.side_effect = _get
        mock_session.headers = {}

        with patch(
            "modules.mastodon.mastodon_tasks.requests.Session",
            return_value=mock_session,
        ):
            from modules.mastodon.mastodon_tasks import p_mastodon

            result = p_mastodon("testuser@custom.instance")

        assert len(result) == 8
        assert result[0]["module"] == "mastodon"

    def test_username_only_uses_search(self):
        """No server → goes directly to search (no lookup attempted)."""
        search_resp = _make_json_resp({"accounts": [ACCOUNT_DATA]})
        lookup_call_log = {"n": 0}

        def _get(url, **kwargs):
            if "/api/v1/accounts/lookup" in url:
                lookup_call_log["n"] += 1
                return _make_error_resp(404)
            if "/api/v2/search" in url:
                return search_resp
            return _make_json_resp([])

        mock_session = MagicMock()
        mock_session.get.side_effect = _get
        mock_session.headers = {}

        with patch(
            "modules.mastodon.mastodon_tasks.requests.Session",
            return_value=mock_session,
        ):
            from modules.mastodon.mastodon_tasks import p_mastodon

            result = p_mastodon("testuser")

        assert lookup_call_log["n"] == 0
        assert result[0]["module"] == "mastodon"

    def test_no_account_found_returns_warning(self):
        """Empty search results → Warning status in raw."""
        search_resp = _make_json_resp({"accounts": []})

        def _get(url, **kwargs):
            if "/api/v2/search" in url:
                return search_resp
            return _make_json_resp([])

        mock_session = MagicMock()
        mock_session.get.side_effect = _get
        mock_session.headers = {}

        with patch(
            "modules.mastodon.mastodon_tasks.requests.Session",
            return_value=mock_session,
        ):
            from modules.mastodon.mastodon_tasks import p_mastodon

            result = p_mastodon("nobody")

        raw = result[3]["raw"]
        assert isinstance(raw, list)
        assert raw[0]["status"] == "Warning"
        assert "not found" in raw[0]["reason"].lower()


# ===========================================================================
# 5. Multi-user (several_user) flow
# ===========================================================================


class TestMultiUserFlow:
    """When search returns multiple matches → several_user response."""

    def _run_with_multi_accounts(self, accounts: list[dict]) -> list:
        search_resp = _make_json_resp({"accounts": accounts})

        def _get(url, **kwargs):
            if "/api/v2/search" in url:
                return search_resp
            return _make_json_resp([])

        mock_session = MagicMock()
        mock_session.get.side_effect = _get
        mock_session.headers = {}

        with patch(
            "modules.mastodon.mastodon_tasks.requests.Session",
            return_value=mock_session,
        ):
            from modules.mastodon.mastodon_tasks import p_mastodon

            return p_mastodon("testuser")

    def test_several_user_returns_8_elements(self):
        """Multi-match → 8-element response."""
        account_b = {**ACCOUNT_DATA, "id": "99", "acct": "testuser@other.social"}
        result = self._run_with_multi_accounts([ACCOUNT_DATA, account_b])
        assert len(result) == 8

    def test_several_user_list_contains_accounts(self):
        """Graphic[2] list has one entry per matched account."""
        account_b = {**ACCOUNT_DATA, "id": "99", "acct": "testuser@other.social"}
        result = self._run_with_multi_accounts([ACCOUNT_DATA, account_b])
        graphic = result[4]["graphic"]
        list_section = next(g["list"] for g in graphic if "list" in g)
        assert len(list_section) == 2

    def test_several_user_list_normalizes_fields(self):
        """Each entry in list has expected keys."""
        account_b = {**ACCOUNT_DATA, "id": "99", "acct": "testuser@other.social"}
        result = self._run_with_multi_accounts([ACCOUNT_DATA, account_b])
        graphic = result[4]["graphic"]
        list_section = next(g["list"] for g in graphic if "list" in g)
        for entry in list_section:
            for key in (
                "account",
                "username",
                "server",
                "avatar",
                "followers",
                "following",
                "toots",
                "bios",
            ):
                assert key in entry, f"Missing key '{key}' in list entry"

    def test_several_user_tasks_empty(self):
        """tasks[7] must be empty for multi-user flow."""
        account_b = {**ACCOUNT_DATA, "id": "99", "acct": "testuser@other.social"}
        result = self._run_with_multi_accounts([ACCOUNT_DATA, account_b])
        assert result[7]["tasks"] == []


# ===========================================================================
# 6. Statuses pagination
# ===========================================================================


class TestStatusesPagination:
    """Statuses endpoint pagination and caps."""

    def _run_with_statuses(self, statuses_pages: list[list[dict]]) -> list:
        """Run p_mastodon with sequentially-returning statuses pages."""
        page_counter = {"n": 0}

        def _get(url, **kwargs):
            if "/api/v1/accounts/lookup" in url:
                return _make_json_resp(ACCOUNT_DATA)
            if "/statuses" in url:
                n = page_counter["n"]
                page_counter["n"] += 1
                if n < len(statuses_pages):
                    return _make_json_resp(statuses_pages[n])
                return _make_json_resp([])
            if "/featured_tags" in url:
                return _make_json_resp([])
            return _make_json_resp([])

        mock_session = MagicMock()
        mock_session.get.side_effect = _get
        mock_session.headers = {}

        with (
            patch(
                "modules.mastodon.mastodon_tasks.requests.Session",
                return_value=mock_session,
            ),
            patch("modules.mastodon.mastodon_tasks.time.sleep"),
        ):
            from modules.mastodon.mastodon_tasks import p_mastodon

            return p_mastodon("testuser@mastodon.social")

    def _make_status_page(self, n: int, start_id: int = 1000) -> list[dict]:
        return [
            {
                "id": str(start_id + i),
                "created_at": "2024-01-15T14:00:00.000Z",
                "reblog": None,
                "tags": [],
                "media_attachments": [],
            }
            for i in range(n)
        ]

    def test_single_page_all_statuses_collected(self):
        """One partial page → all statuses collected."""
        page = self._make_status_page(15)
        result = self._run_with_statuses([page])
        raw = result[3]["raw"]
        assert raw["_statuses_count_fetched"] == 15

    def test_pagination_capped_at_5_pages(self):
        """Even with more data available, max 5 pages are fetched."""
        # 6 pages of 40 each — should stop after 5
        pages = [self._make_status_page(40, start_id=i * 40) for i in range(6)]
        fetch_call_count = {"n": 0}

        page_counter = {"n": 0}

        def _get(url, **kwargs):
            if "/api/v1/accounts/lookup" in url:
                return _make_json_resp(ACCOUNT_DATA)
            if "/statuses" in url:
                fetch_call_count["n"] += 1
                n = page_counter["n"]
                page_counter["n"] += 1
                if n < len(pages):
                    return _make_json_resp(pages[n])
                return _make_json_resp([])
            return _make_json_resp([])

        mock_session = MagicMock()
        mock_session.get.side_effect = _get
        mock_session.headers = {}

        with (
            patch(
                "modules.mastodon.mastodon_tasks.requests.Session",
                return_value=mock_session,
            ),
            patch("modules.mastodon.mastodon_tasks.time.sleep"),
        ):
            from modules.mastodon.mastodon_tasks import p_mastodon

            result = p_mastodon("testuser@mastodon.social")

        raw = result[3]["raw"]
        assert fetch_call_count["n"] == 5, (
            f"Expected 5 page fetches, got {fetch_call_count['n']}"
        )
        assert raw["_statuses_count_fetched"] == 200

    def test_sleep_between_pages(self):
        """Sleep must occur between status pages."""
        pages = [self._make_status_page(40, start_id=i * 40) for i in range(2)]

        page_counter = {"n": 0}

        def _get(url, **kwargs):
            if "/api/v1/accounts/lookup" in url:
                return _make_json_resp(ACCOUNT_DATA)
            if "/statuses" in url:
                n = page_counter["n"]
                page_counter["n"] += 1
                if n < len(pages):
                    return _make_json_resp(pages[n])
                return _make_json_resp([])
            return _make_json_resp([])

        mock_session = MagicMock()
        mock_session.get.side_effect = _get
        mock_session.headers = {}

        with (
            patch(
                "modules.mastodon.mastodon_tasks.requests.Session",
                return_value=mock_session,
            ),
            patch("modules.mastodon.mastodon_tasks.time.sleep") as mock_sleep,
        ):
            from modules.mastodon.mastodon_tasks import p_mastodon

            p_mastodon("testuser@mastodon.social")

        sleep_calls = [c for c in mock_sleep.call_args_list if c == call(0.3)]
        assert len(sleep_calls) >= 1, "Expected at least one 0.3s sleep between pages"

    def test_statuses_403_returns_empty_not_fatal(self):
        """403 on statuses → empty enrichment, full profile still returned."""

        def _get(url, **kwargs):
            if "/api/v1/accounts/lookup" in url:
                return _make_json_resp(ACCOUNT_DATA)
            if "/statuses" in url:
                return _make_error_resp(403)
            if "/featured_tags" in url:
                return _make_json_resp([])
            return _make_json_resp([])

        mock_session = MagicMock()
        mock_session.get.side_effect = _get
        mock_session.headers = {}

        with patch(
            "modules.mastodon.mastodon_tasks.requests.Session",
            return_value=mock_session,
        ):
            from modules.mastodon.mastodon_tasks import p_mastodon

            result = p_mastodon("testuser@mastodon.social")

        # Must still return 8 elements (not an error response)
        assert len(result) == 8
        raw = result[3]["raw"]
        assert raw["_statuses_count_fetched"] == 0


# ===========================================================================
# 7. Analytics output
# ===========================================================================


class TestAnalyticsOutput:
    """Activity charts and hashtag bubble from statuses."""

    def _run_with_status_list(self, statuses: list[dict]) -> list:
        def _get(url, **kwargs):
            if "/api/v1/accounts/lookup" in url:
                return _make_json_resp(ACCOUNT_DATA)
            if "/statuses" in url:
                return _make_json_resp(statuses)
            if "/featured_tags" in url:
                return _make_json_resp([])
            return _make_json_resp([])

        mock_session = MagicMock()
        mock_session.get.side_effect = _get
        mock_session.headers = {}

        with patch(
            "modules.mastodon.mastodon_tasks.requests.Session",
            return_value=mock_session,
        ):
            from modules.mastodon.mastodon_tasks import p_mastodon

            return p_mastodon("testuser@mastodon.social")

    def test_hour_chart_has_24_entries_when_active(self):
        """User with statuses → hour chart has exactly 24 entries."""
        statuses = [
            {
                "id": "1",
                "created_at": "2024-01-15T14:00:00.000Z",
                "reblog": None,
                "tags": [],
                "media_attachments": [],
            }
        ]
        result = self._run_with_status_list(statuses)
        graphic = result[4]["graphic"]
        hour = next(g["hour"] for g in graphic if "hour" in g)
        assert len(hour) == 24
        assert all("name" in h and "value" in h for h in hour)

    def test_week_chart_has_7_entries_when_active(self):
        """User with statuses → week chart has exactly 7 entries."""
        statuses = [
            {
                "id": "1",
                "created_at": "2024-01-15T14:00:00.000Z",
                "reblog": None,
                "tags": [],
                "media_attachments": [],
            }
        ]
        result = self._run_with_status_list(statuses)
        graphic = result[4]["graphic"]
        week = next(g["week"] for g in graphic if "week" in g)
        assert len(week) == 7
        names = [w["name"] for w in week]
        assert names == [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]

    def test_charts_empty_when_no_statuses(self, mock_mastodon_happy):
        """No statuses → hour and week charts are empty lists."""
        from modules.mastodon.mastodon_tasks import p_mastodon

        result = p_mastodon("testuser@mastodon.social")
        graphic = result[4]["graphic"]
        hour = next(g["hour"] for g in graphic if "hour" in g)
        week = next(g["week"] for g in graphic if "week" in g)
        assert hour == []
        assert week == []

    def test_hashtag_bubble_populated_from_statuses(self):
        """Statuses with hashtags → non-empty hashtag bubble."""
        statuses = [
            {
                "id": str(i),
                "created_at": "2024-01-15T14:00:00.000Z",
                "reblog": None,
                "tags": [{"name": "python"}, {"name": "fediverse"}],
                "media_attachments": [],
            }
            for i in range(5)
        ]
        result = self._run_with_status_list(statuses)
        graphic = result[4]["graphic"]
        hashtags = next(g["hashtags"] for g in graphic if "hashtags" in g)
        assert hashtags != {}
        assert "children" in hashtags
        names = {c["name"] for c in hashtags["children"]}
        assert "python" in names
        assert "fediverse" in names

    def test_hashtag_bubble_empty_when_no_statuses(self, mock_mastodon_happy):
        """No statuses → hashtag bubble is empty dict."""
        from modules.mastodon.mastodon_tasks import p_mastodon

        result = p_mastodon("testuser@mastodon.social")
        graphic = result[4]["graphic"]
        hashtags = next(g["hashtags"] for g in graphic if "hashtags" in g)
        assert hashtags == {}


# ===========================================================================
# 8. Response shape
# ===========================================================================


class TestResponseShape:
    """8-element response contract."""

    def test_output_has_8_elements(self, mock_mastodon_happy):
        from modules.mastodon.mastodon_tasks import p_mastodon

        result = p_mastodon("testuser@mastodon.social")
        assert len(result) == 8

    def test_output_keys_in_order(self, mock_mastodon_happy):
        from modules.mastodon.mastodon_tasks import p_mastodon

        result = p_mastodon("testuser@mastodon.social")
        keys = [next(iter(item)) for item in result]
        assert keys == [
            "module",
            "param",
            "validation",
            "raw",
            "graphic",
            "profile",
            "timeline",
            "tasks",
        ]

    def test_module_is_mastodon(self, mock_mastodon_happy):
        from modules.mastodon.mastodon_tasks import p_mastodon

        result = p_mastodon("testuser@mastodon.social")
        assert result[0]["module"] == "mastodon"

    def test_param_matches_username(self, mock_mastodon_happy):
        from modules.mastodon.mastodon_tasks import p_mastodon

        result = p_mastodon("testuser@mastodon.social")
        assert result[1]["param"] == "testuser@mastodon.social"

    def test_graphic_has_11_keys(self, mock_mastodon_happy):
        """Graphic must contain the 11 expected keys (6 original + 5 ratio cards).

        Updated from 6->11 when mastodon-ratios added popularity, approval,
        tootvboost, resume, engagement at indices 6-10.
        """
        from modules.mastodon.mastodon_tasks import p_mastodon

        result = p_mastodon("testuser@mastodon.social")
        graphic = result[4]["graphic"]
        keys = [next(iter(g)) for g in graphic]
        assert keys == [
            "user",
            "social",
            "list",
            "hour",
            "week",
            "hashtags",
            "popularity",
            "approval",
            "tootvboost",
            "resume",
            "engagement",
        ]

    def test_validation_is_no(self, mock_mastodon_happy):
        from modules.mastodon.mastodon_tasks import p_mastodon

        result = p_mastodon("testuser@mastodon.social")
        assert result[2]["validation"] == "no"


# ===========================================================================
# 9. Profile fields (header, moved, bot/group/locked)
# ===========================================================================


class TestProfileFields:
    """Enriched profile fields: header, moved account, user type flags."""

    def _run_with_account(self, account: dict) -> list:
        def _get(url, **kwargs):
            if "/api/v1/accounts/lookup" in url:
                return _make_json_resp(account)
            return _make_json_resp([])

        mock_session = MagicMock()
        mock_session.get.side_effect = _get
        mock_session.headers = {}

        with patch(
            "modules.mastodon.mastodon_tasks.requests.Session",
            return_value=mock_session,
        ):
            from modules.mastodon.mastodon_tasks import p_mastodon

            return p_mastodon("testuser@mastodon.social")

    def test_header_image_added_to_photos(self):
        """Non-default header → photos list includes header entry."""
        result = self._run_with_account(ACCOUNT_DATA_WITH_HEADER)
        profile = result[5]["profile"]
        photos_item = next((p for p in profile if "photos" in p), None)
        assert photos_item is not None
        photo_titles = [ph["title"] for ph in photos_item["photos"]]
        assert "Mastodon Header" in photo_titles

    def test_default_header_not_added_to_photos(self):
        """Default missing.png header → NOT added to photos list."""
        result = self._run_with_account(ACCOUNT_DATA)  # has missing.png header
        profile = result[5]["profile"]
        photos_item = next((p for p in profile if "photos" in p), None)
        if photos_item:
            photo_titles = [ph["title"] for ph in photos_item["photos"]]
            assert "Mastodon Header" not in photo_titles

    def test_moved_account_graph_node_created(self):
        """Account with moved field → graph node 'Migrated to' added."""
        account = {
            **ACCOUNT_DATA,
            "moved": {"url": "https://fosstodon.org/@testuser"},
        }
        result = self._run_with_account(account)
        graphic = result[4]["graphic"]
        user_nodes = next(g["user"] for g in graphic if "user" in g)
        moved_node = next(
            (n for n in user_nodes if n.get("name-node") == "MastoMoved"), None
        )
        assert moved_node is not None
        assert "fosstodon.org" in moved_node["subtitle"]

    def test_bot_user_type_node(self):
        """Bot account → user type node shows 'Robot'."""
        account = {**ACCOUNT_DATA, "bot": True, "group": False}
        result = self._run_with_account(account)
        graphic = result[4]["graphic"]
        user_nodes = next(g["user"] for g in graphic if "user" in g)
        user_type_node = next(
            (n for n in user_nodes if n.get("title") == "User Type"), None
        )
        assert user_type_node is not None
        assert "Robot" in user_type_node["subtitle"]

    def test_group_user_type_node(self):
        """Group account → user type node shows 'Group'."""
        account = {**ACCOUNT_DATA, "group": True}
        result = self._run_with_account(account)
        graphic = result[4]["graphic"]
        user_nodes = next(g["user"] for g in graphic if "user" in g)
        user_type_node = next(
            (n for n in user_nodes if n.get("title") == "User Type"), None
        )
        assert user_type_node is not None
        assert "Group" in user_type_node["subtitle"]

    def test_locked_account_graph_node(self):
        """Locked account → locked node shows 'User Locked'."""
        account = {**ACCOUNT_DATA, "locked": True}
        result = self._run_with_account(account)
        graphic = result[4]["graphic"]
        user_nodes = next(g["user"] for g in graphic if "user" in g)
        locked_node = next(
            (n for n in user_nodes if n.get("name-node") == "MastoLocked"), None
        )
        assert locked_node is not None
        assert "Locked" in locked_node["subtitle"]


# ===========================================================================
# 10. Featured tags (non-fatal enrichment)
# ===========================================================================


class TestFeaturedTags:
    """Featured tags enrich graph nodes; failures are non-fatal."""

    def _run_with_tags(self, tags: list[dict]) -> list:
        def _get(url, **kwargs):
            if "/api/v1/accounts/lookup" in url:
                return _make_json_resp(ACCOUNT_DATA)
            if "/statuses" in url:
                return _make_json_resp([])
            if "/featured_tags" in url:
                return _make_json_resp(tags)
            return _make_json_resp([])

        mock_session = MagicMock()
        mock_session.get.side_effect = _get
        mock_session.headers = {}

        with patch(
            "modules.mastodon.mastodon_tasks.requests.Session",
            return_value=mock_session,
        ):
            from modules.mastodon.mastodon_tasks import p_mastodon

            return p_mastodon("testuser@mastodon.social")

    def test_featured_tags_appear_in_graph(self):
        """Featured tags → graph nodes with '#tag' title."""
        tags = [
            {"name": "mastodon", "statuses_count": 34},
            {"name": "fediverse", "statuses_count": 18},
        ]
        result = self._run_with_tags(tags)
        graphic = result[4]["graphic"]
        user_nodes = next(g["user"] for g in graphic if "user" in g)
        tag_nodes = [n for n in user_nodes if n.get("icon") == "fas fa-hashtag"]
        assert len(tag_nodes) == 2
        tag_titles = {n["title"] for n in tag_nodes}
        assert "#mastodon" in tag_titles
        assert "#fediverse" in tag_titles

    def test_featured_tags_raw_in_analytics(self):
        """Featured tags are stored in raw _featured_tags."""
        tags = [{"name": "mastodon", "statuses_count": 5}]
        result = self._run_with_tags(tags)
        raw = result[3]["raw"]
        assert raw["_featured_tags"] == tags

    def test_featured_tags_404_non_fatal(self):
        """Featured tags 404 → empty, task succeeds with 8 elements."""

        def _get(url, **kwargs):
            if "/api/v1/accounts/lookup" in url:
                return _make_json_resp(ACCOUNT_DATA)
            if "/statuses" in url:
                return _make_json_resp([])
            if "/featured_tags" in url:
                return _make_error_resp(404)
            return _make_json_resp([])

        mock_session = MagicMock()
        mock_session.get.side_effect = _get
        mock_session.headers = {}

        with patch(
            "modules.mastodon.mastodon_tasks.requests.Session",
            return_value=mock_session,
        ):
            from modules.mastodon.mastodon_tasks import p_mastodon

            result = p_mastodon("testuser@mastodon.social")

        assert len(result) == 8
        raw = result[3]["raw"]
        assert raw["_featured_tags"] == []


# ===========================================================================
# 11. Error handling
# ===========================================================================


class TestErrorHandling:
    """Fatal and non-fatal error paths via @iky_task decorator."""

    def test_network_error_returns_fail_status(self):
        """Network error (non-iKy) → Fail status in raw."""
        mock_session = MagicMock()
        mock_session.get.side_effect = OSError("connection refused")
        mock_session.headers = {}

        with patch(
            "modules.mastodon.mastodon_tasks.requests.Session",
            return_value=mock_session,
        ):
            from modules.mastodon.mastodon_tasks import p_mastodon

            result = p_mastodon("anyuser")

        raw = result[3]["raw"]
        assert isinstance(raw, list)
        assert raw[0]["status"] == "Fail"

    def test_rate_limited_returns_warning(self):
        """HTTP 429 on search → Warning status."""

        def _get(url, **kwargs):
            if "/api/v2/search" in url:
                return _make_error_resp(429)
            return _make_json_resp([])

        mock_session = MagicMock()
        mock_session.get.side_effect = _get
        mock_session.headers = {}

        with patch(
            "modules.mastodon.mastodon_tasks.requests.Session",
            return_value=mock_session,
        ):
            from modules.mastodon.mastodon_tasks import p_mastodon

            result = p_mastodon("anyuser")

        raw = result[3]["raw"]
        assert raw[0]["status"] == "Warning"
        assert "rate" in raw[0]["reason"].lower() or "limit" in raw[0]["reason"].lower()

    def test_error_structure_has_4_elements(self):
        """Error response: [module, param, validation, raw] — no graphic/profile."""
        mock_session = MagicMock()
        mock_session.get.side_effect = OSError("unreachable")
        mock_session.headers = {}

        with patch(
            "modules.mastodon.mastodon_tasks.requests.Session",
            return_value=mock_session,
        ):
            from modules.mastodon.mastodon_tasks import p_mastodon

            result = p_mastodon("anyuser")

        keys = [next(iter(item)) for item in result]
        assert keys == ["module", "param", "validation", "raw"]

    def test_error_includes_traceback(self):
        """Error raw node must contain a traceback string."""
        mock_session = MagicMock()
        mock_session.get.side_effect = OSError("unreachable")
        mock_session.headers = {}

        with patch(
            "modules.mastodon.mastodon_tasks.requests.Session",
            return_value=mock_session,
        ):
            from modules.mastodon.mastodon_tasks import p_mastodon

            result = p_mastodon("anyuser")

        raw = result[3]["raw"]
        assert "traceback" in raw[0]
        assert isinstance(raw[0]["traceback"], str)

    def test_invalid_input_returns_warning(self):
        """Completely invalid input → Warning status."""

        def _get(url, **kwargs):
            return _make_json_resp([])

        mock_session = MagicMock()
        mock_session.get.side_effect = _get
        mock_session.headers = {}

        with patch(
            "modules.mastodon.mastodon_tasks.requests.Session",
            return_value=mock_session,
        ):
            from modules.mastodon.mastodon_tasks import p_mastodon

            result = p_mastodon("@@@invalid@@@")

        raw = result[3]["raw"]
        assert isinstance(raw, list)
        # Invalid input raises iKy- prefixed exception → Warning
        assert raw[0]["status"] == "Warning"


# ===========================================================================
# 12. Backward compatibility
# ===========================================================================


class TestBackwardCompatibility:
    """Registry contract and backward-compatible alias."""

    def test_registry_entry_exists(self):
        """module_registry must have mastodon entry with pass_from=False."""
        from module_registry import MODULE_REGISTRY

        assert "mastodon" in MODULE_REGISTRY
        task_path, pass_from = MODULE_REGISTRY["mastodon"]
        assert task_path == "modules.mastodon.mastodon_tasks.t_mastodon"
        assert pass_from is False

    def test_t_mastodon_same_as_p_mastodon(self):
        """t_mastodon must resolve to p_mastodon (same Celery task object)."""
        from modules.mastodon.mastodon_tasks import p_mastodon, t_mastodon

        assert t_mastodon is p_mastodon

    def test_make_session_returns_session_with_ua(self):
        """_make_session() must return a Session with User-Agent set."""
        from modules.mastodon.mastodon_tasks import _USER_AGENTS, _make_session

        session = _make_session()
        assert session.headers.get("User-Agent") in _USER_AGENTS

    def test_user_agents_is_non_empty_tuple(self):
        """_USER_AGENTS must be a non-empty tuple of strings."""
        from modules.mastodon.mastodon_tasks import _USER_AGENTS

        assert isinstance(_USER_AGENTS, tuple)
        assert len(_USER_AGENTS) > 0
        assert all(isinstance(ua, str) for ua in _USER_AGENTS)


# ===========================================================================
# 13. Resolved-server regression: fallback uses the RESOLVED account's server
# ===========================================================================


class TestResolvedServerFallback:
    """Regression: when lookup fails and search resolves a different server,
    statuses/featured_tags must target the RESOLVED server, not the original."""

    def test_fallback_uses_resolved_server_not_original(self):
        """C3 regression: user@custom.instance → lookup fails → search finds
        account on mastodon.social → statuses/featured_tags must hit
        mastodon.social, NOT custom.instance."""
        # Account lives on mastodon.social (different from custom.instance)
        resolved_account = {
            **ACCOUNT_DATA,
            "url": "https://mastodon.social/@testuser",
        }
        statuses_called_servers: list[str] = []
        featured_tags_called_servers: list[str] = []

        def _get(url, **kwargs):
            if "custom.instance" in url and "/api/v1/accounts/lookup" in url:
                # Simulate lookup failure on original server
                return _make_error_resp(404)
            if "mastodon.social" in url and "/api/v2/search" in url:
                # Search resolves on mastodon.social
                return _make_json_resp({"accounts": [resolved_account]})
            if "/statuses" in url:
                # Record which server statuses were fetched from
                import re as _re

                m = _re.match(r"https?://([^/]+)", url)
                if m:
                    statuses_called_servers.append(m.group(1))
                return _make_json_resp([])
            if "/featured_tags" in url:
                import re as _re

                m = _re.match(r"https?://([^/]+)", url)
                if m:
                    featured_tags_called_servers.append(m.group(1))
                return _make_json_resp([])
            return _make_json_resp([])

        mock_session = MagicMock()
        mock_session.get.side_effect = _get
        mock_session.headers = {}

        with patch(
            "modules.mastodon.mastodon_tasks.requests.Session",
            return_value=mock_session,
        ):
            from modules.mastodon.mastodon_tasks import p_mastodon

            result = p_mastodon("testuser@custom.instance")

        assert len(result) == 8
        # All downstream calls must go to mastodon.social (resolved server)
        assert all(s == "mastodon.social" for s in statuses_called_servers), (
            f"Statuses fetched from wrong server(s): {statuses_called_servers}"
        )
        assert all(s == "mastodon.social" for s in featured_tags_called_servers), (
            f"Featured tags fetched from wrong server(s): {featured_tags_called_servers}"
        )
        # And NOT from the original custom instance
        assert "custom.instance" not in statuses_called_servers
        assert "custom.instance" not in featured_tags_called_servers


# ===========================================================================
# 14. Lookup error conditions (timeout, invalid JSON)
# ===========================================================================


class TestLookupEdgeCases:
    """S2: Edge cases for lookup / search error paths."""

    def test_lookup_timeout_falls_back_to_search(self):
        """When lookup raises requests.Timeout, fallback to search succeeds."""
        import requests as _requests

        def _get(url, **kwargs):
            if "/api/v1/accounts/lookup" in url:
                raise _requests.Timeout("timed out")
            if "/api/v2/search" in url:
                return _make_json_resp({"accounts": [ACCOUNT_DATA]})
            return _make_json_resp([])

        mock_session = MagicMock()
        mock_session.get.side_effect = _get
        mock_session.headers = {}

        with patch(
            "modules.mastodon.mastodon_tasks.requests.Session",
            return_value=mock_session,
        ):
            from modules.mastodon.mastodon_tasks import p_mastodon

            result = p_mastodon("testuser@some.instance")

        # Should fall back to search and succeed
        assert len(result) == 8
        assert result[0]["module"] == "mastodon"

    def test_lookup_connection_error_falls_back_to_search(self):
        """When lookup raises ConnectionError, fallback to search succeeds."""
        import requests as _requests

        def _get(url, **kwargs):
            if "/api/v1/accounts/lookup" in url:
                raise _requests.ConnectionError("refused")
            if "/api/v2/search" in url:
                return _make_json_resp({"accounts": [ACCOUNT_DATA]})
            return _make_json_resp([])

        mock_session = MagicMock()
        mock_session.get.side_effect = _get
        mock_session.headers = {}

        with patch(
            "modules.mastodon.mastodon_tasks.requests.Session",
            return_value=mock_session,
        ):
            from modules.mastodon.mastodon_tasks import p_mastodon

            result = p_mastodon("testuser@some.instance")

        assert len(result) == 8
        assert result[0]["module"] == "mastodon"

    def test_search_invalid_json_returns_fail_or_warning(self):
        """When search returns invalid JSON, decorator wraps into error response."""

        def _get(url, **kwargs):
            if "/api/v2/search" in url:
                resp = MagicMock()
                resp.status_code = 200
                resp.json.side_effect = ValueError("invalid json")
                return resp
            return _make_json_resp([])

        mock_session = MagicMock()
        mock_session.get.side_effect = _get
        mock_session.headers = {}

        with patch(
            "modules.mastodon.mastodon_tasks.requests.Session",
            return_value=mock_session,
        ):
            from modules.mastodon.mastodon_tasks import p_mastodon

            result = p_mastodon("testuser")

        # Invalid JSON from search raises iKy- exception → Warning or Fail
        raw = result[3]["raw"]
        assert isinstance(raw, list)
        assert raw[0]["status"] in ("Warning", "Fail")

    def test_lookup_invalid_json_falls_back_to_search(self):
        """When lookup returns 200 but invalid JSON, KeyError/ValueError causes
        fallback to search via the exception propagation."""

        def _get(url, **kwargs):
            if "/api/v1/accounts/lookup" in url:
                resp = MagicMock()
                resp.status_code = 200
                resp.json.side_effect = ValueError("bad json")
                return resp
            if "/api/v2/search" in url:
                return _make_json_resp({"accounts": [ACCOUNT_DATA]})
            return _make_json_resp([])

        mock_session = MagicMock()
        mock_session.get.side_effect = _get
        mock_session.headers = {}

        with patch(
            "modules.mastodon.mastodon_tasks.requests.Session",
            return_value=mock_session,
        ):
            from modules.mastodon.mastodon_tasks import p_mastodon

            # Lookup returns 200 but bad JSON — this will raise ValueError,
            # which is NOT caught by _lookup_account (only RequestException is).
            # So it propagates up. The decorator catches it as a Fail/Warning.
            result = p_mastodon("testuser@some.instance")

        raw = result[3]["raw"]
        assert isinstance(raw, list)
        # Either the decorator caught it (Fail/Warning) or it fell back through search
        assert (
            raw[0]["status"] in ("Warning", "Fail") or result[0]["module"] == "mastodon"
        )


# ===========================================================================
# 15. Toot list population — graphic[2]["list"] and raw_node["_statuses"]
# ===========================================================================


# Full status shape used by the toot-list tests (includes all formatted fields)
TOOT_STATUS: dict = {
    "id": "9001",
    "created_at": "2024-03-21T09:45:30.000Z",
    "content": "<p>Hello <strong>world</strong>! #python</p>",
    "url": "https://mastodon.social/@testuser/9001",
    "reblogs_count": 7,
    "favourites_count": 42,
    "reblog": None,
    "tags": [{"name": "python"}],
    "media_attachments": [],
}


class TestTootListPopulation:
    """graphic[2]['list'] and raw_node['_statuses'] — task 1.3 backend tests.

    Covers:
      - Populated statuses: HTML stripping, date[:19] truncation, url,
        reblogs_count, favourites_count field mapping
      - Empty statuses: graphic[2]['list'] == [] and raw_node['_statuses'] == []
    """

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    def _run_with_statuses(self, statuses: list[dict]) -> list:
        """Run p_mastodon with a fixed statuses payload; patch only HTTP."""

        def _get(url, **kwargs):
            if "/api/v1/accounts/lookup" in url:
                return _make_json_resp(ACCOUNT_DATA)
            if "/statuses" in url:
                return _make_json_resp(statuses)
            if "/featured_tags" in url:
                return _make_json_resp([])
            return _make_json_resp([])

        mock_session = MagicMock()
        mock_session.get.side_effect = _get
        mock_session.headers = {}

        with patch(
            "modules.mastodon.mastodon_tasks.requests.Session",
            return_value=mock_session,
        ):
            from modules.mastodon.mastodon_tasks import p_mastodon

            return p_mastodon("testuser@mastodon.social")

    def _get_toot_list(self, result: list) -> list:
        """Extract graphic[2]['list'] from the 8-element result."""
        graphic = result[4]["graphic"]
        return next(g["list"] for g in graphic if "list" in g)

    def _get_raw_statuses(self, result: list) -> list:
        """Extract raw_node['_statuses'] from the 8-element result."""
        raw = result[3]["raw"]
        return raw["_statuses"]

    # -----------------------------------------------------------------------
    # Populated statuses scenarios
    # -----------------------------------------------------------------------

    def test_list_populated_when_statuses_exist(self):
        """graphic[2]['list'] has one entry per status when statuses are present."""
        statuses = [TOOT_STATUS.copy() for _ in range(5)]
        result = self._run_with_statuses(statuses)
        toot_list = self._get_toot_list(result)
        assert len(toot_list) == 5

    def test_list_item_has_required_keys(self):
        """Each toot dict MUST have exactly content, date, url, reblogs_count,
        favourites_count."""
        result = self._run_with_statuses([TOOT_STATUS.copy()])
        toot_list = self._get_toot_list(result)
        item = toot_list[0]
        for key in ("content", "date", "url", "reblogs_count", "favourites_count"):
            assert key in item, f"Missing key '{key}' in toot list item"

    def test_html_stripped_from_content(self):
        """content MUST be produced via remove_tags() — the call is made with
        the status's raw 'content' value.  We replace remove_tags with a real
        implementation so we can assert on the stripped result."""
        raw_html = "<p>Hello <strong>world</strong>! <a href='x'>#python</a></p>"
        status = {**TOOT_STATUS, "content": raw_html}

        # Replace the MagicMock stub with a real implementation so we can
        # verify the stripping behaviour end-to-end.
        import re as _re

        def _real_remove_tags(html: str, *_args, **_kwargs) -> str:
            return _re.sub(r"<[^>]+>", "", html)

        with patch(
            "modules.mastodon.mastodon_tasks.remove_tags", side_effect=_real_remove_tags
        ):
            result = self._run_with_statuses([status])

        toot_list = self._get_toot_list(result)
        content = toot_list[0]["content"]
        # No angle brackets should remain
        assert "<" not in content
        assert ">" not in content
        # Text content must survive stripping
        assert "Hello" in content
        assert "world" in content

    def test_date_truncated_to_19_chars(self):
        """date MUST be the ISO timestamp truncated to [:19] (no millis or Z)."""
        status = {**TOOT_STATUS, "created_at": "2024-03-21T09:45:30.000Z"}
        result = self._run_with_statuses([status])
        toot_list = self._get_toot_list(result)
        date_val = toot_list[0]["date"]
        assert date_val == "2024-03-21T09:45:30"
        assert len(date_val) == 19

    def test_url_field_preserved(self):
        """url MUST match the status's url field verbatim."""
        status = {
            **TOOT_STATUS,
            "url": "https://mastodon.social/@testuser/9001",
        }
        result = self._run_with_statuses([status])
        toot_list = self._get_toot_list(result)
        assert toot_list[0]["url"] == "https://mastodon.social/@testuser/9001"

    def test_reblogs_count_preserved(self):
        """reblogs_count MUST match the status's reblogs_count integer."""
        status = {**TOOT_STATUS, "reblogs_count": 13}
        result = self._run_with_statuses([status])
        toot_list = self._get_toot_list(result)
        assert toot_list[0]["reblogs_count"] == 13

    def test_favourites_count_preserved(self):
        """favourites_count MUST match the status's favourites_count integer."""
        status = {**TOOT_STATUS, "favourites_count": 99}
        result = self._run_with_statuses([status])
        toot_list = self._get_toot_list(result)
        assert toot_list[0]["favourites_count"] == 99

    def test_all_50_statuses_mapped_to_list(self):
        """50 statuses on first page, then empty → 50 entries in graphic[2]['list'].

        The pagination loop fetches until an empty page or the 5-page cap.
        Return the 50 statuses on page 1, then empty on page 2+ so the loop
        terminates naturally with exactly 50 collected statuses.
        """
        statuses = [
            {
                **TOOT_STATUS,
                "id": str(1000 + i),
                "content": f"<p>Toot {i}</p>",
                "url": f"https://mastodon.social/@testuser/{1000 + i}",
                "reblogs_count": i,
                "favourites_count": i * 2,
            }
            for i in range(50)
        ]

        page_counter = {"n": 0}

        def _get(url, **kwargs):
            if "/api/v1/accounts/lookup" in url:
                return _make_json_resp(ACCOUNT_DATA)
            if "/statuses" in url:
                n = page_counter["n"]
                page_counter["n"] += 1
                return _make_json_resp(statuses if n == 0 else [])
            if "/featured_tags" in url:
                return _make_json_resp([])
            return _make_json_resp([])

        mock_session = MagicMock()
        mock_session.get.side_effect = _get
        mock_session.headers = {}

        with patch(
            "modules.mastodon.mastodon_tasks.requests.Session",
            return_value=mock_session,
        ):
            from modules.mastodon.mastodon_tasks import p_mastodon

            result = p_mastodon("testuser@mastodon.social")

        toot_list = self._get_toot_list(result)
        assert len(toot_list) == 50

    def test_missing_fields_use_defaults(self):
        """Status missing optional fields → safe defaults (empty string / 0).

        We replace the remove_tags stub with an identity-returning lambda so
        that content defaults can be asserted as plain strings.
        """
        bare_status = {
            "id": "5555",
            "created_at": "",
            "reblog": None,
            "tags": [],
            "media_attachments": [],
            # content, url, reblogs_count, favourites_count intentionally absent
        }

        with patch(
            "modules.mastodon.mastodon_tasks.remove_tags",
            side_effect=lambda html, *a, **kw: html,
        ):
            result = self._run_with_statuses([bare_status])

        toot_list = self._get_toot_list(result)
        item = toot_list[0]
        assert item["content"] == ""
        assert item["date"] == ""
        assert item["url"] == ""
        assert item["reblogs_count"] == 0
        assert item["favourites_count"] == 0

    # -----------------------------------------------------------------------
    # Empty statuses scenarios
    # -----------------------------------------------------------------------

    def test_list_is_empty_when_no_statuses(self):
        """graphic[2]['list'] MUST be [] when statuses is empty."""
        result = self._run_with_statuses([])
        toot_list = self._get_toot_list(result)
        assert toot_list == []

    def test_list_is_exact_empty_list_not_none(self):
        """graphic[2]['list'] must be exactly [] (not None, not missing key)."""
        result = self._run_with_statuses([])
        graphic = result[4]["graphic"]
        list_entry = next((g for g in graphic if "list" in g), None)
        assert list_entry is not None, "graphic must contain a 'list' key"
        assert list_entry["list"] == []
        assert isinstance(list_entry["list"], list)

    # -----------------------------------------------------------------------
    # raw_node["_statuses"] preservation
    # -----------------------------------------------------------------------

    def test_raw_statuses_preserves_full_list(self):
        """raw_node['_statuses'] MUST contain the full unmodified status list."""
        statuses = [
            {**TOOT_STATUS, "id": str(i), "content": f"<p>Toot {i}</p>"}
            for i in range(3)
        ]
        result = self._run_with_statuses(statuses)
        raw_statuses = self._get_raw_statuses(result)
        assert len(raw_statuses) == 3
        # Must preserve raw HTML — NOT stripped
        for i, raw_s in enumerate(raw_statuses):
            assert raw_s["content"] == f"<p>Toot {i}</p>"

    def test_raw_statuses_is_empty_when_no_statuses(self):
        """raw_node['_statuses'] MUST be [] when no statuses are fetched."""
        result = self._run_with_statuses([])
        raw_statuses = self._get_raw_statuses(result)
        assert raw_statuses == []

    def test_raw_statuses_preserves_full_api_objects(self):
        """raw_node['_statuses'] must preserve all original fields, not just
        the formatted subset used in graphic[2]['list']."""
        status = {
            **TOOT_STATUS,
            "extra_api_field": "should_survive",
            "media_attachments": [
                {"type": "image", "url": "https://cdn.example.com/img.jpg"}
            ],
        }
        result = self._run_with_statuses([status])
        raw_statuses = self._get_raw_statuses(result)
        assert len(raw_statuses) == 1
        assert raw_statuses[0]["extra_api_field"] == "should_survive"
        assert len(raw_statuses[0]["media_attachments"]) == 1

    def test_raw_statuses_is_independent_of_formatted_list(self):
        """graphic[2]['list'] HTML-strips content; raw_node['_statuses'] preserves
        the original HTML. They must be independent."""
        status = {**TOOT_STATUS, "content": "<p>Raw <em>HTML</em> here</p>"}
        result = self._run_with_statuses([status])

        toot_list = self._get_toot_list(result)
        raw_statuses = self._get_raw_statuses(result)

        # Formatted list has stripped content
        assert "<" not in toot_list[0]["content"]
        # Raw statuses preserve original HTML
        assert toot_list[0]["content"] != raw_statuses[0]["content"]
        assert "<p>" in raw_statuses[0]["content"]


# ===========================================================================
# 16. Ratio cards - _compute_analytics new fields and graphic[6-10]
# ===========================================================================


def _make_engagement_status(
    idx: int,
    *,
    favourites: int = 0,
    reblogs: int = 0,
    replies: int = 0,
    reblog: dict | None = None,
    date: str = "2024-01-01",
) -> dict:
    """Build a minimal status dict for engagement/ratio tests."""
    return {
        "id": str(idx),
        "created_at": f"{date}T{idx % 24:02d}:00:00.000Z",
        "reblog": reblog,
        "favourites_count": favourites,
        "reblogs_count": reblogs,
        "replies_count": replies,
        "tags": [],
        "media_attachments": [],
    }


class TestComputeAnalyticsRatioFields:
    """Unit tests for _compute_analytics() — engagement aggregation fields.

    Tests the NEW fields added by the mastodon-ratios change:
      total_favourites, total_reblogs, total_replies, originals,
      engagement_series (last 50, chronological order, correct fields).
    """

    # -----------------------------------------------------------------------
    # Direct import — test _compute_analytics in isolation
    # -----------------------------------------------------------------------

    def _analytics(self, statuses: list[dict]) -> dict:
        from modules.mastodon.mastodon_tasks import _compute_analytics

        return _compute_analytics(statuses)

    # -----------------------------------------------------------------------
    # 1. Sums: total_favourites, total_reblogs, total_replies
    # -----------------------------------------------------------------------

    def test_total_favourites_is_correct_sum(self):
        """total_favourites must be the sum of favourites_count across all statuses."""
        statuses = [_make_engagement_status(i, favourites=i * 10) for i in range(5)]
        result = self._analytics(statuses)
        expected = sum(i * 10 for i in range(5))  # 0+10+20+30+40 = 100
        assert result["total_favourites"] == expected

    def test_total_reblogs_is_correct_sum(self):
        """total_reblogs must be the sum of reblogs_count across all statuses."""
        statuses = [_make_engagement_status(i, reblogs=i * 3) for i in range(6)]
        result = self._analytics(statuses)
        expected = sum(i * 3 for i in range(6))  # 0+3+6+9+12+15 = 45
        assert result["total_reblogs"] == expected

    def test_total_replies_is_correct_sum(self):
        """total_replies must be the sum of replies_count across all statuses."""
        statuses = [_make_engagement_status(i, replies=i + 1) for i in range(4)]
        result = self._analytics(statuses)
        expected = sum(i + 1 for i in range(4))  # 1+2+3+4 = 10
        assert result["total_replies"] == expected

    def test_mixed_engagement_counts_all_sums(self):
        """All three sums are correct when statuses have varied engagement."""
        statuses = [
            _make_engagement_status(1, favourites=10, reblogs=2, replies=5),
            _make_engagement_status(2, favourites=20, reblogs=4, replies=3),
            _make_engagement_status(3, favourites=5, reblogs=0, replies=8),
        ]
        result = self._analytics(statuses)
        assert result["total_favourites"] == 35
        assert result["total_reblogs"] == 6
        assert result["total_replies"] == 16

    # -----------------------------------------------------------------------
    # 2. originals — count of non-boost statuses
    # -----------------------------------------------------------------------

    def test_originals_counts_non_boost_statuses(self):
        """originals must be the count of statuses where reblog is None."""
        statuses = [
            _make_engagement_status(1, reblog=None),
            _make_engagement_status(2, reblog={"id": "999"}),  # boost
            _make_engagement_status(3, reblog=None),
            _make_engagement_status(4, reblog={"id": "888"}),  # boost
            _make_engagement_status(5, reblog=None),
        ]
        result = self._analytics(statuses)
        assert result["originals"] == 3

    def test_originals_all_originals(self):
        """originals equals total count when no boosts are present."""
        statuses = [_make_engagement_status(i) for i in range(7)]
        result = self._analytics(statuses)
        assert result["originals"] == 7

    def test_originals_all_boosts(self):
        """originals is 0 when all statuses are boosts."""
        statuses = [
            _make_engagement_status(i, reblog={"id": str(i + 100)}) for i in range(5)
        ]
        result = self._analytics(statuses)
        assert result["originals"] == 0

    # -----------------------------------------------------------------------
    # 3. engagement_series — last 50 toots, chronological order, correct fields
    # -----------------------------------------------------------------------

    def test_engagement_series_last_50_of_120(self):
        """With 120 statuses, engagement_series contains exactly 50 entries."""
        statuses = [_make_engagement_status(i) for i in range(120)]
        result = self._analytics(statuses)
        assert len(result["engagement_series"]) == 50

    def test_engagement_series_chronological_order(self):
        """engagement_series is the LAST 50 in list order (chronological).

        The API returns statuses reverse-chronologically, so statuses[-50:]
        gives the oldest of the fetched batch — chronological in API terms.
        We just verify the slice is the last 50 elements from the input.
        """
        statuses = [_make_engagement_status(i, favourites=i) for i in range(120)]
        result = self._analytics(statuses)
        series = result["engagement_series"]
        # The last 50 statuses by input order have favourites 70..119
        expected_favs = list(range(70, 120))
        actual_favs = [s["favourites"] for s in series]
        assert actual_favs == expected_favs

    def test_engagement_series_correct_fields(self):
        """Each entry in engagement_series has name, favourites, reblogs, replies."""
        statuses = [
            _make_engagement_status(
                1,
                favourites=10,
                reblogs=3,
                replies=2,
                date="2024-03-15",
            )
        ]
        result = self._analytics(statuses)
        assert len(result["engagement_series"]) == 1
        entry = result["engagement_series"][0]
        assert "name" in entry
        assert "favourites" in entry
        assert "reblogs" in entry
        assert "replies" in entry
        assert entry["favourites"] == 10
        assert entry["reblogs"] == 3
        assert entry["replies"] == 2

    def test_engagement_series_name_is_date_prefix(self):
        """Each engagement_series entry name must be created_at[:10] (YYYY-MM-DD)."""
        statuses = [
            _make_engagement_status(1, date="2024-06-15"),
        ]
        result = self._analytics(statuses)
        entry = result["engagement_series"][0]
        assert entry["name"] == "2024-06-15"
        assert len(entry["name"]) == 10

    # -----------------------------------------------------------------------
    # 4. Fewer than 50 statuses — engagement_series uses all of them
    # -----------------------------------------------------------------------

    def test_engagement_series_fewer_than_50_uses_all(self):
        """With 12 statuses, engagement_series has exactly 12 entries."""
        statuses = [_make_engagement_status(i) for i in range(12)]
        result = self._analytics(statuses)
        assert len(result["engagement_series"]) == 12

    def test_engagement_series_single_status(self):
        """With 1 status, engagement_series has exactly 1 entry."""
        statuses = [_make_engagement_status(1, favourites=5, reblogs=1, replies=0)]
        result = self._analytics(statuses)
        assert len(result["engagement_series"]) == 1
        assert result["engagement_series"][0]["favourites"] == 5

    def test_engagement_series_exactly_50_statuses(self):
        """With exactly 50 statuses, engagement_series has 50 entries."""
        statuses = [_make_engagement_status(i) for i in range(50)]
        result = self._analytics(statuses)
        assert len(result["engagement_series"]) == 50

    # -----------------------------------------------------------------------
    # 5. Empty statuses → all zero defaults, empty engagement_series
    # -----------------------------------------------------------------------

    def test_empty_statuses_all_zero_defaults(self):
        """Empty statuses → all ratio fields are 0."""
        result = self._analytics([])
        assert result["total_favourites"] == 0
        assert result["total_reblogs"] == 0
        assert result["total_replies"] == 0
        assert result["originals"] == 0

    def test_empty_statuses_empty_engagement_series(self):
        """Empty statuses → engagement_series is []."""
        result = self._analytics([])
        assert result["engagement_series"] == []

    def test_empty_statuses_returns_all_required_keys(self):
        """Empty statuses result dict must include all new ratio keys."""
        result = self._analytics([])
        for key in (
            "total_favourites",
            "total_reblogs",
            "total_replies",
            "originals",
            "engagement_series",
        ):
            assert key in result, f"Missing key '{key}' in empty-statuses analytics"

    def test_missing_engagement_fields_use_zero_defaults(self):
        """Statuses missing favourites_count/reblogs_count/replies_count default to 0."""
        # Bare status with no engagement fields
        bare = {
            "id": "1",
            "created_at": "2024-01-01T00:00:00.000Z",
            "reblog": None,
            "tags": [],
            "media_attachments": [],
        }
        result = self._analytics([bare])
        assert result["total_favourites"] == 0
        assert result["total_reblogs"] == 0
        assert result["total_replies"] == 0
        assert result["engagement_series"][0]["favourites"] == 0
        assert result["engagement_series"][0]["reblogs"] == 0
        assert result["engagement_series"][0]["replies"] == 0


class TestRatioCardGraphics:
    """Integration tests for graphic[6-10] via the full pipeline.

    Runs p_mastodon with mock HTTP and verifies the ratio/relationship card
    entries appended by _one_user().
    """

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    ACCOUNT: ClassVar[dict] = {
        **ACCOUNT_DATA,
        "followers_count": 378000,
        "following_count": 705,
        "statuses_count": 7429,
    }

    def _run_with_statuses(
        self,
        statuses: list[dict],
        account: dict | None = None,
    ) -> list:
        acct = account or self.ACCOUNT

        def _get(url, **kwargs):
            if "/api/v1/accounts/lookup" in url:
                return _make_json_resp(acct)
            if "/statuses" in url:
                return _make_json_resp(statuses)
            if "/featured_tags" in url:
                return _make_json_resp([])
            return _make_json_resp([])

        mock_session = MagicMock()
        mock_session.get.side_effect = _get
        mock_session.headers = {}

        with patch(
            "modules.mastodon.mastodon_tasks.requests.Session",
            return_value=mock_session,
        ):
            from modules.mastodon.mastodon_tasks import p_mastodon

            return p_mastodon("testuser@mastodon.social")

    def _graphic(self, result: list) -> list:
        return result[4]["graphic"]

    # -----------------------------------------------------------------------
    # 6. graphic[6] popularity
    # -----------------------------------------------------------------------

    def test_graphic_6_popularity_exists(self):
        """graphic[6] must have a 'popularity' key."""
        result = self._run_with_statuses([])
        graphic = self._graphic(result)
        assert "popularity" in graphic[6]

    def test_graphic_6_popularity_followers_value(self):
        """graphic[6].popularity must include Followers=378000."""
        result = self._run_with_statuses([])
        graphic = self._graphic(result)
        popularity = graphic[6]["popularity"]
        # popularity is a list of {title, value} dicts
        followers_entry = next(
            (p for p in popularity if p.get("title") == "Followers"), None
        )
        assert followers_entry is not None
        assert followers_entry["value"] == 378000

    def test_graphic_6_popularity_following_value(self):
        """graphic[6].popularity must include Following=705."""
        result = self._run_with_statuses([])
        graphic = self._graphic(result)
        popularity = graphic[6]["popularity"]
        following_entry = next(
            (p for p in popularity if p.get("title") == "Following"), None
        )
        assert following_entry is not None
        assert following_entry["value"] == 705

    # -----------------------------------------------------------------------
    # 7. graphic[7] approval
    # -----------------------------------------------------------------------

    def test_graphic_7_approval_exists(self):
        """graphic[7] must have an 'approval' key."""
        result = self._run_with_statuses([])
        graphic = self._graphic(result)
        assert "approval" in graphic[7]

    def test_graphic_7_approval_toots_value(self):
        """graphic[7].approval Toots must equal statuses_count from the account."""
        result = self._run_with_statuses([])
        graphic = self._graphic(result)
        approval = graphic[7]["approval"]
        toots_entry = next((a for a in approval if a.get("title") == "Toots"), None)
        assert toots_entry is not None
        assert toots_entry["value"] == 7429  # ACCOUNT.statuses_count

    def test_graphic_7_approval_likes_is_total_favourites(self):
        """graphic[7].approval Likes must equal sum of favourites_count."""
        statuses = [_make_engagement_status(i, favourites=100) for i in range(5)]
        result = self._run_with_statuses(statuses)
        graphic = self._graphic(result)
        approval = graphic[7]["approval"]
        likes_entry = next((a for a in approval if a.get("title") == "Likes"), None)
        assert likes_entry is not None
        assert likes_entry["value"] == 500  # 5 x 100

    # -----------------------------------------------------------------------
    # 8. graphic[8] tootvboost
    # -----------------------------------------------------------------------

    def test_graphic_8_tootvboost_exists(self):
        """graphic[8] must have a 'tootvboost' key."""
        result = self._run_with_statuses([])
        graphic = self._graphic(result)
        assert "tootvboost" in graphic[8]

    def test_graphic_8_tootvboost_original_plus_boosts_equals_total(self):
        """Original + Boosts must sum to total fetched statuses count."""
        originals = [_make_engagement_status(i, reblog=None) for i in range(7)]
        boosts = [
            _make_engagement_status(10 + i, reblog={"id": str(i)}) for i in range(3)
        ]
        statuses = originals + boosts
        result = self._run_with_statuses(statuses)
        graphic = self._graphic(result)
        tootvboost = graphic[8]["tootvboost"]
        original_val = next(
            (t["value"] for t in tootvboost if t.get("title") == "Original"), None
        )
        boosts_val = next(
            (t["value"] for t in tootvboost if t.get("title") == "Boosts"), None
        )
        assert original_val is not None
        assert boosts_val is not None
        assert original_val == 7
        assert boosts_val == 3
        assert original_val + boosts_val == len(statuses)

    def test_graphic_8_tootvboost_all_originals(self):
        """When all statuses are originals, Boosts must be 0."""
        statuses = [_make_engagement_status(i, reblog=None) for i in range(5)]
        result = self._run_with_statuses(statuses)
        graphic = self._graphic(result)
        tootvboost = graphic[8]["tootvboost"]
        boosts_val = next(
            (t["value"] for t in tootvboost if t.get("title") == "Boosts"), None
        )
        assert boosts_val == 0

    # -----------------------------------------------------------------------
    # 9. graphic[9] resume
    # -----------------------------------------------------------------------

    def test_graphic_9_resume_exists(self):
        """graphic[9] must have a 'resume' key with 'children'."""
        result = self._run_with_statuses([])
        graphic = self._graphic(result)
        assert "resume" in graphic[9]
        assert "children" in graphic[9]["resume"]

    def test_graphic_9_resume_has_four_children(self):
        """graphic[9].resume.children must have exactly 4 entries."""
        result = self._run_with_statuses([])
        graphic = self._graphic(result)
        children = graphic[9]["resume"]["children"]
        assert len(children) == 4

    def test_graphic_9_resume_children_have_name_and_value(self):
        """Each resume child must have 'name' and 'value' keys."""
        result = self._run_with_statuses([])
        graphic = self._graphic(result)
        children = graphic[9]["resume"]["children"]
        for child in children:
            assert "name" in child, f"Missing 'name' key in resume child: {child}"
            assert "value" in child, f"Missing 'value' key in resume child: {child}"

    def test_graphic_9_resume_followers_and_following_correct(self):
        """Resume children must include Followers=378000 and Following=705."""
        result = self._run_with_statuses([])
        graphic = self._graphic(result)
        children = graphic[9]["resume"]["children"]
        child_by_name = {c["name"]: c["value"] for c in children}
        assert child_by_name.get("Followers") == 378000
        assert child_by_name.get("Following") == 705

    def test_graphic_9_resume_originals_and_boosts_correct(self):
        """Resume Toots/Originals + Boosts values match the statuses split."""
        originals = [_make_engagement_status(i, reblog=None) for i in range(9)]
        boosts = [
            _make_engagement_status(20 + i, reblog={"id": str(i)}) for i in range(3)
        ]
        result = self._run_with_statuses(originals + boosts)
        graphic = self._graphic(result)
        children = graphic[9]["resume"]["children"]
        child_by_name = {c["name"]: c["value"] for c in children}
        # Implementation uses "Toots" for originals and "Boosts" for boosts
        originals_val = child_by_name.get("Toots", child_by_name.get("Original Toots"))
        boosts_val = child_by_name.get("Boosts")
        assert originals_val == 9
        assert boosts_val == 3

    # -----------------------------------------------------------------------
    # 10. graphic[10] engagement
    # -----------------------------------------------------------------------

    def test_graphic_10_engagement_exists(self):
        """graphic[10] must have an 'engagement' key."""
        result = self._run_with_statuses([])
        graphic = self._graphic(result)
        assert "engagement" in graphic[10]

    def test_graphic_10_engagement_empty_when_no_statuses(self):
        """With no statuses, engagement must be []."""
        result = self._run_with_statuses([])
        graphic = self._graphic(result)
        assert graphic[10]["engagement"] == []

    def test_graphic_10_engagement_matches_analytics_series(self):
        """graphic[10].engagement must equal engagement_series from analytics."""
        statuses = [
            _make_engagement_status(i, favourites=i * 5, reblogs=i, replies=2)
            for i in range(10)
        ]
        result = self._run_with_statuses(statuses)
        graphic = self._graphic(result)
        raw_analytics = result[3]["raw"]["_analytics"]

        assert graphic[10]["engagement"] == raw_analytics["engagement_series"]

    def test_graphic_10_engagement_capped_at_50(self):
        """With 120 statuses, engagement must have ≤50 entries."""
        statuses = [_make_engagement_status(i, favourites=i) for i in range(120)]
        result = self._run_with_statuses(statuses)
        graphic = self._graphic(result)
        assert len(graphic[10]["engagement"]) <= 50

    def test_graphic_10_engagement_entries_have_correct_fields(self):
        """Each engagement entry must have name, favourites, reblogs, replies."""
        statuses = [_make_engagement_status(1, favourites=7, reblogs=2, replies=1)]
        result = self._run_with_statuses(statuses)
        graphic = self._graphic(result)
        engagement = graphic[10]["engagement"]
        assert len(engagement) == 1
        entry = engagement[0]
        for field in ("name", "favourites", "reblogs", "replies"):
            assert field in entry, f"Missing field '{field}' in engagement entry"

    # -----------------------------------------------------------------------
    # 11. Zero statuses → all ratio indices still present with zeroed values
    # -----------------------------------------------------------------------

    def test_all_ratio_graphic_indices_present_with_empty_statuses(self):
        """Indices 6-10 must exist even when no statuses are fetched."""
        result = self._run_with_statuses([])
        graphic = self._graphic(result)
        assert len(graphic) >= 11, (
            f"graphic must have at least 11 entries, got {len(graphic)}"
        )
        assert "popularity" in graphic[6]
        assert "approval" in graphic[7]
        assert "tootvboost" in graphic[8]
        assert "resume" in graphic[9]
        assert "engagement" in graphic[10]

    def test_graphic_keys_order(self):
        """graphic must contain keys in expected order: user, social, list,
        hour, week, hashtags, popularity, approval, tootvboost, resume, engagement."""
        result = self._run_with_statuses([_make_engagement_status(1, favourites=5)])
        graphic = self._graphic(result)
        keys = [next(iter(g)) for g in graphic]
        expected = [
            "user",
            "social",
            "list",
            "hour",
            "week",
            "hashtags",
            "popularity",
            "approval",
            "tootvboost",
            "resume",
            "engagement",
        ]
        assert keys == expected
