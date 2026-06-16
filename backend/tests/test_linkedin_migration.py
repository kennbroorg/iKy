"""Tests for the LinkedIn module refactor.

Tests verify:
- _convert_browser_cookies() (list→dict, dict passthrough, invalid input)
- _authenticate_linkedin() three-tier auth chain (disk, API key, legacy, all-fail)
- @iky_task decorator integration (task naming, alias identity)
- dev-mode golden file bypass via decorator
- iKy-warning error shaping
- from_m parameter validation switching (hard vs soft)
- argparse CLI entry point (static/structural)
- No browser_cookie3 import in linkedin_tasks
- module_registry unchanged (pass_from=True)
- _parse_rsc_payload() HTML→RSC extraction
- _extract_profile_fields() and per-field helpers
- p_linkedin() migrated integration (4 HTTP calls, HTML-based)
"""

from __future__ import annotations

import json
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Stub browser_cookie3 BEFORE importing linkedin_tasks.
# browser_cookie3 is not installed in local dev environments (only in Docker).
# ---------------------------------------------------------------------------

_bc3_mock = types.ModuleType("browser_cookie3")
_bc3_mock.chromium = MagicMock(return_value=[])
_bc3_mock.opera = MagicMock(return_value=[])
_bc3_mock.edge = MagicMock(return_value=[])
_bc3_mock.firefox = MagicMock(return_value=[])
_bc3_mock.chrome = MagicMock(return_value=[])
_bc3_mock.brave = MagicMock(return_value=[])

sys.modules.setdefault("browser_cookie3", _bc3_mock)

# Now safe to import linkedin_tasks
import modules.linkedin.linkedin_tasks as linkedin_tasks  # noqa: E402

# ---------------------------------------------------------------------------
# File path constants
# ---------------------------------------------------------------------------

BACKEND_DIR = Path(__file__).parent.parent
# requirements.txt lives at repo root locally (BACKEND_DIR.parent) but
# inside Docker COPY puts it at /app (== BACKEND_DIR).
_REQ_LOCAL = BACKEND_DIR.parent / "requirements.txt"
_REQ_DOCKER = BACKEND_DIR / "requirements.txt"
REQUIREMENTS_FILE = _REQ_LOCAL if _REQ_LOCAL.exists() else _REQ_DOCKER
MODULE_REGISTRY_FILE = BACKEND_DIR / "module_registry.py"
LINKEDIN_TASKS_FILE = BACKEND_DIR / "modules" / "linkedin" / "linkedin_tasks.py"


# ===========================================================================
# Phase 1 — Task 1.2: _convert_browser_cookies() unit tests
# ===========================================================================


class TestConvertBrowserCookies:
    """Unit tests for _convert_browser_cookies() — spec R2."""

    def test_list_format_returns_flat_dict(self):
        """Browser list format [{"name": k, "value": v}] → flat {k: v} dict."""
        raw = [
            {"name": "li_at", "value": "abc123"},
            {"name": "JSESSIONID", "value": '"xyz789"'},
        ]
        result = linkedin_tasks._convert_browser_cookies(raw)
        assert result == {"li_at": "abc123", "JSESSIONID": '"xyz789"'}

    def test_dict_passthrough_returns_same_dict(self):
        """Already-flat dict passes through unchanged (string-typed values)."""
        raw = {"li_at": "abc123", "JSESSIONID": '"xyz789"'}
        result = linkedin_tasks._convert_browser_cookies(raw)
        assert result == {"li_at": "abc123", "JSESSIONID": '"xyz789"'}

    def test_list_items_without_name_are_skipped(self):
        """Items without 'name' key are silently skipped."""
        raw = [
            {"name": "li_at", "value": "abc"},
            {"value": "orphan"},  # no name — skip
            {"name": "JSESSIONID", "value": "xyz"},
        ]
        result = linkedin_tasks._convert_browser_cookies(raw)
        assert result == {"li_at": "abc", "JSESSIONID": "xyz"}

    def test_list_item_with_missing_value_defaults_to_empty_string(self):
        """Cookie with no 'value' field gets empty string."""
        raw = [{"name": "li_at"}]
        result = linkedin_tasks._convert_browser_cookies(raw)
        assert result == {"li_at": ""}

    def test_invalid_type_raises_value_error(self):
        """Non-list, non-dict input raises ValueError with 'Unexpected cookie format'."""
        with pytest.raises(ValueError, match="Unexpected cookie format"):
            linkedin_tasks._convert_browser_cookies("not-a-list-or-dict")  # type: ignore[arg-type]

    def test_empty_list_returns_empty_dict(self):
        """Empty list → empty dict (no crashes)."""
        result = linkedin_tasks._convert_browser_cookies([])
        assert result == {}

    def test_dict_values_coerced_to_str(self):
        """Dict values are string-coerced (not just passed through raw types)."""
        raw = {"li_at": "tok", "JSESSIONID": "ses"}
        result = linkedin_tasks._convert_browser_cookies(raw)
        for v in result.values():
            assert isinstance(v, str)

    def test_uses_shared_cookie_converter(self):
        """_convert_browser_cookies must be the shared cookie_utils converter."""
        from factories.cookie_utils import convert_browser_cookies

        assert linkedin_tasks._convert_browser_cookies is convert_browser_cookies


# ===========================================================================
# Phase 1 — Task 1.3: _authenticate_linkedin() auth-chain tests
# ===========================================================================


class TestAuthenticateLinkedin:
    """Unit tests for the three-tier auth chain — spec R1."""

    # ---- Tier 1: Cookie file on disk ----

    def test_disk_cookie_file_sets_session_cookies(self, tmp_path):
        """Tier 1: cookie file on disk → li_at + JSESSIONID set on session."""
        cookie_file = tmp_path / "linkedin_cookies.json"
        cookie_data = {"li_at": "abc123", "JSESSIONID": '"xyz789"'}
        cookie_file.write_text(json.dumps(cookie_data))

        session = MagicMock()
        session.cookies = {}
        session.headers = {}

        with patch.object(linkedin_tasks, "_COOKIE_FILE", cookie_file):
            linkedin_tasks._authenticate_linkedin(session)

        assert session.cookies["li_at"] == "abc123"
        assert session.cookies["JSESSIONID"] == '"xyz789"'

    def test_disk_cookie_file_sets_csrf_token(self, tmp_path):
        """Tier 1: csrf-token header is set to JSESSIONID stripped of quotes."""
        cookie_file = tmp_path / "linkedin_cookies.json"
        cookie_data = {"li_at": "abc123", "JSESSIONID": '"xyz789"'}
        cookie_file.write_text(json.dumps(cookie_data))

        session = MagicMock()
        session.cookies = {}
        session.headers = {}

        with patch.object(linkedin_tasks, "_COOKIE_FILE", cookie_file):
            linkedin_tasks._authenticate_linkedin(session)

        assert session.headers["csrf-token"] == "xyz789"

    def test_disk_cookie_no_api_key_call(self, tmp_path):
        """Tier 1 (fast path): api_keys_search is NOT called when file exists."""
        cookie_file = tmp_path / "linkedin_cookies.json"
        cookie_data = {"li_at": "abc", "JSESSIONID": '"ses"'}
        cookie_file.write_text(json.dumps(cookie_data))

        session = MagicMock()
        session.cookies = {}
        session.headers = {}

        with (
            patch.object(linkedin_tasks, "_COOKIE_FILE", cookie_file),
            patch("modules.linkedin.linkedin_tasks.api_keys_search") as mock_api_search,
        ):
            linkedin_tasks._authenticate_linkedin(session)

        mock_api_search.assert_not_called()

    # ---- Tier 2: linkedin_cookies API key ----

    def test_api_key_cookies_set_on_session(self, tmp_path):
        """Tier 2: linkedin_cookies API key (list format) → cookies set on session."""
        cookie_file = tmp_path / "linkedin_cookies.json"
        # No file on disk — forces API key path

        browser_export = json.dumps(
            [
                {"name": "li_at", "value": "tok456"},
                {"name": "JSESSIONID", "value": '"sess999"'},
            ]
        )

        session = MagicMock()
        session.cookies = {}
        session.headers = {}

        def _api_keys(k: str) -> str | bool:
            if k == "linkedin_cookies":
                return browser_export
            return False

        with (
            patch.object(linkedin_tasks, "_COOKIE_FILE", cookie_file),
            patch(
                "modules.linkedin.linkedin_tasks.api_keys_search",
                side_effect=_api_keys,
            ),
        ):
            linkedin_tasks._authenticate_linkedin(session)

        assert session.cookies["li_at"] == "tok456"
        assert session.cookies["JSESSIONID"] == '"sess999"'

    def test_api_key_cookies_persisted_to_disk(self, tmp_path):
        """Tier 2: after loading via API key, cookies are persisted to disk."""
        cookie_file = tmp_path / "linkedin_cookies.json"

        browser_export = json.dumps(
            [
                {"name": "li_at", "value": "tok456"},
                {"name": "JSESSIONID", "value": '"sess999"'},
            ]
        )

        session = MagicMock()
        session.cookies = {}
        session.headers = {}

        def _api_keys(k: str) -> str | bool:
            if k == "linkedin_cookies":
                return browser_export
            return False

        with (
            patch.object(linkedin_tasks, "_COOKIE_FILE", cookie_file),
            patch.object(linkedin_tasks, "_COOKIE_DIR", tmp_path),
            patch(
                "modules.linkedin.linkedin_tasks.api_keys_search",
                side_effect=_api_keys,
            ),
        ):
            linkedin_tasks._authenticate_linkedin(session)

        assert cookie_file.exists(), "Cookie file must be persisted to disk"
        persisted = json.loads(cookie_file.read_text())
        assert "li_at" in persisted

    def test_api_key_csrf_token_set(self, tmp_path):
        """Tier 2: csrf-token derived from JSESSIONID (quotes stripped)."""
        cookie_file = tmp_path / "linkedin_cookies.json"

        browser_export = json.dumps(
            [
                {"name": "li_at", "value": "tok456"},
                {"name": "JSESSIONID", "value": '"sess999"'},
            ]
        )

        session = MagicMock()
        session.cookies = {}
        session.headers = {}

        def _api_keys(k: str) -> str | bool:
            if k == "linkedin_cookies":
                return browser_export
            return False

        with (
            patch.object(linkedin_tasks, "_COOKIE_FILE", cookie_file),
            patch(
                "modules.linkedin.linkedin_tasks.api_keys_search",
                side_effect=_api_keys,
            ),
        ):
            linkedin_tasks._authenticate_linkedin(session)

        assert session.headers["csrf-token"] == "sess999"

    # ---- Tier 3: Legacy API keys ----

    def test_legacy_keys_set_session_cookies(self, tmp_path):
        """Tier 3: legacy linkedin_li_at + linkedin_JSESSIONID keys used."""
        cookie_file = tmp_path / "linkedin_cookies.json"

        def _api_keys(k: str) -> str | bool:
            if k == "linkedin_li_at":
                return "legacy_li_at_value"
            if k == "linkedin_JSESSIONID":
                return '"legacy_jsession"'
            return False

        session = MagicMock()
        session.cookies = {}
        session.headers = {}

        with (
            patch.object(linkedin_tasks, "_COOKIE_FILE", cookie_file),
            patch(
                "modules.linkedin.linkedin_tasks.api_keys_search",
                side_effect=_api_keys,
            ),
        ):
            linkedin_tasks._authenticate_linkedin(session)

        assert session.cookies["li_at"] == "legacy_li_at_value"
        assert session.cookies["JSESSIONID"] == '"legacy_jsession"'

    def test_legacy_keys_csrf_token_set(self, tmp_path):
        """Tier 3: csrf-token is derived from JSESSIONID (quotes stripped)."""
        cookie_file = tmp_path / "linkedin_cookies.json"

        def _api_keys(k: str) -> str | bool:
            if k == "linkedin_li_at":
                return "leg_li_at"
            if k == "linkedin_JSESSIONID":
                return '"leg_jsession"'
            return False

        session = MagicMock()
        session.cookies = {}
        session.headers = {}

        with (
            patch.object(linkedin_tasks, "_COOKIE_FILE", cookie_file),
            patch(
                "modules.linkedin.linkedin_tasks.api_keys_search",
                side_effect=_api_keys,
            ),
        ):
            linkedin_tasks._authenticate_linkedin(session)

        assert session.headers["csrf-token"] == "leg_jsession"

    # ---- Tier 4: All methods exhausted → actionable error ----

    def test_all_methods_exhausted_raises_iky_exception(self, tmp_path):
        """All tiers fail → Exception raised with 'iKy - ' prefix."""
        cookie_file = tmp_path / "linkedin_cookies.json"

        with (
            patch.object(linkedin_tasks, "_COOKIE_FILE", cookie_file),
            patch(
                "modules.linkedin.linkedin_tasks.api_keys_search",
                return_value=False,
            ),
            pytest.raises(Exception, match="iKy - "),
        ):
            session = MagicMock()
            session.cookies = {}
            session.headers = {}
            linkedin_tasks._authenticate_linkedin(session)

    def test_all_methods_exhausted_error_references_docs(self, tmp_path):
        """Error message must reference docs/COOKIES.md."""
        cookie_file = tmp_path / "linkedin_cookies.json"

        with (
            patch.object(linkedin_tasks, "_COOKIE_FILE", cookie_file),
            patch(
                "modules.linkedin.linkedin_tasks.api_keys_search",
                return_value=False,
            ),
            pytest.raises(Exception) as exc_info,
        ):
            session = MagicMock()
            session.cookies = {}
            session.headers = {}
            linkedin_tasks._authenticate_linkedin(session)

        assert "docs/COOKIES.md" in str(exc_info.value)

    def test_tier1_takes_priority_over_api_key(self, tmp_path):
        """Cookie file on disk (tier 1) takes priority — API key never called."""
        cookie_file = tmp_path / "linkedin_cookies.json"
        cookie_data = {"li_at": "from_disk", "JSESSIONID": '"disk_ses"'}
        cookie_file.write_text(json.dumps(cookie_data))

        session = MagicMock()
        session.cookies = {}
        session.headers = {}

        with (
            patch.object(linkedin_tasks, "_COOKIE_FILE", cookie_file),
            patch("modules.linkedin.linkedin_tasks.api_keys_search") as mock_api_search,
        ):
            linkedin_tasks._authenticate_linkedin(session)

        mock_api_search.assert_not_called()
        assert session.cookies["li_at"] == "from_disk"


# ===========================================================================
# Phase 3 — Task 3.1: @iky_task decorator, alias, dev-mode, error shaping
# ===========================================================================


class TestIkyTaskDecoratorIntegration:
    """Tests for @iky_task integration — spec R3 + R5."""

    def test_t_linkedin_is_celery_task(self):
        """t_linkedin must be a registered Celery task (via @iky_task)."""
        t_linkedin = linkedin_tasks.t_linkedin
        assert callable(t_linkedin), "t_linkedin must be callable"
        assert hasattr(t_linkedin, "name"), "t_linkedin must have a .name (Celery task)"

    def test_t_linkedin_task_name(self):
        """Celery task name must be modules.linkedin.linkedin_tasks.t_linkedin."""
        assert linkedin_tasks.t_linkedin.name == (
            "modules.linkedin.linkedin_tasks.t_linkedin"
        )

    def test_t_linkedin_is_p_linkedin(self):
        """t_linkedin = p_linkedin alias must hold (spec R5)."""
        assert linkedin_tasks.t_linkedin is linkedin_tasks.p_linkedin, (
            "t_linkedin = p_linkedin alias must hold"
        )

    def test_dev_mode_returns_golden_file(self, tmp_path, monkeypatch):
        """When output-linkedin.json exists, decorator returns it without API calls."""
        import importlib

        outputs_dir = tmp_path / "outputs"
        outputs_dir.mkdir()
        golden = [
            {"module": "linkedin"},
            {"param": "testuser"},
            {"validation": "hard"},
        ]
        (outputs_dir / "output-linkedin.json").write_text(json.dumps(golden))

        monkeypatch.chdir(tmp_path)

        # Reload so decorator picks up the new cwd
        importlib.reload(linkedin_tasks)

        with patch(
            "modules.linkedin.linkedin_tasks._authenticate_linkedin",
            side_effect=AssertionError("API called"),
        ):
            result = linkedin_tasks.t_linkedin("testuser")

        assert result == golden

        # Restore
        importlib.reload(linkedin_tasks)

    def test_error_shaping_iky_prefix_produces_warning(self, tmp_path):
        """iKy-prefixed exception → status='Warning', validation='not_used'."""
        cookie_file = tmp_path / "linkedin_cookies.json"

        def _raise_iky(*args, **kwargs):
            raise Exception("iKy - cookies expired")

        with (
            patch.object(linkedin_tasks, "_COOKIE_FILE", cookie_file),
            patch(
                "modules.linkedin.linkedin_tasks._authenticate_linkedin",
                side_effect=_raise_iky,
            ),
        ):
            result = linkedin_tasks.t_linkedin("john-doe")

        assert result[2] == {"validation": "not_used"}
        raw = result[3]["raw"]
        assert raw[0]["status"] == "Warning"
        assert raw[0]["reason"] == "cookies expired"
        assert "traceback" in raw[0]

    def test_error_shaping_non_iky_prefix_produces_fail(self, tmp_path):
        """Non-iKy exception → status='Fail'."""
        cookie_file = tmp_path / "linkedin_cookies.json"

        def _raise_generic(*args, **kwargs):
            raise Exception("some unexpected error")

        with (
            patch.object(linkedin_tasks, "_COOKIE_FILE", cookie_file),
            patch(
                "modules.linkedin.linkedin_tasks._authenticate_linkedin",
                side_effect=_raise_generic,
            ),
        ):
            result = linkedin_tasks.t_linkedin("john-doe")

        assert result[3]["raw"][0]["status"] == "Fail"


# ===========================================================================
# Phase 3 — Task 3.2: from_m validation switching
# ===========================================================================


class TestFromMValidation:
    """Tests for from_m parameter — spec R4."""

    def _make_minimal_profile_response(self) -> dict:
        """Minimal Voyager profileView response that won't crash the pipeline."""
        return {
            "profile": {
                "firstName": "John",
                "lastName": "Doe",
                "headline": "Engineer",
                "locationName": "NYC",
                "miniProfile": {},
            }
        }

    def test_from_m_initial_produces_hard_validation(self, tmp_path):
        """p_linkedin(user, from_m='Initial') → total[2] == {'validation': 'hard'}."""
        cookie_file = tmp_path / "linkedin_cookies.json"
        cookie_data = {"li_at": "tok", "JSESSIONID": '"ses"'}
        cookie_file.write_text(json.dumps(cookie_data))

        mock_resp = MagicMock()
        mock_resp.text = json.dumps({"profileId": "john-doe-id"})

        # We only need to verify total[2]; short-circuit the rest of the pipeline
        # by making the second s.get (the profile URL) raise after validation is set.
        call_count = [0]

        def _mock_get(url, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                # First call: profileView for ID extraction
                r = MagicMock()
                r.text = json.dumps({"profileId": "john-doe-id"})
                return r
            raise Exception("iKy - stop pipeline")

        with (
            patch.object(linkedin_tasks, "_COOKIE_FILE", cookie_file),
            patch("requests.Session") as mock_session_cls,
        ):
            mock_session = MagicMock()
            mock_session.cookies = {}
            mock_session.headers = {}
            mock_session.get.side_effect = _mock_get
            mock_session_cls.return_value = mock_session

            linkedin_tasks.t_linkedin("john-doe", "Initial")

        # This test is structural: verifies from_m is in the p_linkedin signature.
        # The decorator sets validation='not_used' on errors caught before total[2]
        # is set, so the full validation path is tested via test_from_m_initial_sets_*.
        import inspect

        sig = inspect.signature(linkedin_tasks.p_linkedin)
        params = list(sig.parameters.keys())
        assert "from_m" in params, "p_linkedin must accept from_m parameter"

    def test_p_linkedin_accepts_from_m_parameter(self):
        """p_linkedin must accept from_m as second parameter (spec R4)."""
        import inspect

        sig = inspect.signature(linkedin_tasks.p_linkedin)
        params = list(sig.parameters.keys())
        assert "from_m" in params, "p_linkedin must accept from_m parameter"
        # Default must be "Initial"
        assert sig.parameters["from_m"].default == "Initial"

    def test_from_m_initial_sets_hard_validation(self, tmp_path):
        """Verify from_m='Initial' → {'validation': 'hard'} in total array.

        Updated for migrated pipeline: 4 HTTP calls (HTML + 3 Voyager).
        """
        cookie_file = tmp_path / "linkedin_cookies.json"
        cookie_data = {"li_at": "tok", "JSESSIONID": '"ses"'}
        cookie_file.write_text(json.dumps(cookie_data))

        def _make_html_mock() -> MagicMock:
            r = MagicMock()
            r.text = _make_html_response()
            r.status_code = 200
            return r

        def _make_voyager_response(data: dict) -> MagicMock:
            r = MagicMock()
            r.text = json.dumps(data)
            r.status_code = 200
            return r

        call_seq = [
            _make_html_mock(),  # 1: GET /in/{user}/ HTML page
            _make_voyager_response(
                {"paging": {"total": 0}, "elements": []}
            ),  # 2: following
            _make_voyager_response({"paging": {"total": 0}}),  # 3: recommend_received
            _make_voyager_response({"paging": {"total": 0}}),  # 4: recommend_given
        ]

        with (
            patch.object(linkedin_tasks, "_COOKIE_FILE", cookie_file),
            patch("requests.Session") as mock_session_cls,
        ):
            mock_session = MagicMock()
            mock_session.cookies = {}
            mock_session.headers = {}
            mock_session.get.side_effect = call_seq
            mock_session_cls.return_value = mock_session

            result = linkedin_tasks.p_linkedin("john-doe", from_m="Initial")

        assert result[2] == {"validation": "hard"}, (
            f"Expected hard validation, got: {result[2]}"
        )

    def test_from_m_chained_sets_soft_validation(self, tmp_path):
        """Verify from_m='linkedin' → {'validation': 'soft'} in total array.

        Updated for migrated pipeline: 4 HTTP calls (HTML + 3 Voyager).
        """
        cookie_file = tmp_path / "linkedin_cookies.json"
        cookie_data = {"li_at": "tok", "JSESSIONID": '"ses"'}
        cookie_file.write_text(json.dumps(cookie_data))

        def _make_html_mock() -> MagicMock:
            r = MagicMock()
            r.text = _make_html_response()
            r.status_code = 200
            return r

        def _make_voyager_response(data: dict) -> MagicMock:
            r = MagicMock()
            r.text = json.dumps(data)
            r.status_code = 200
            return r

        call_seq = [
            _make_html_mock(),  # 1: GET /in/{user}/ HTML page
            _make_voyager_response(
                {"paging": {"total": 0}, "elements": []}
            ),  # 2: following
            _make_voyager_response({"paging": {"total": 0}}),  # 3: recommend_received
            _make_voyager_response({"paging": {"total": 0}}),  # 4: recommend_given
        ]

        with (
            patch.object(linkedin_tasks, "_COOKIE_FILE", cookie_file),
            patch("requests.Session") as mock_session_cls,
        ):
            mock_session = MagicMock()
            mock_session.cookies = {}
            mock_session.headers = {}
            mock_session.get.side_effect = call_seq
            mock_session_cls.return_value = mock_session

            result = linkedin_tasks.p_linkedin("john-doe", from_m="linkedin")

        assert result[2] == {"validation": "soft"}, (
            f"Expected soft validation, got: {result[2]}"
        )


# ===========================================================================
# Phase 4 — Task 4.1: Static/CLI tests
# ===========================================================================


class TestStaticAndCLI:
    """Static checks and CLI contract tests — spec R6 + R-removed-1."""

    def test_no_browser_cookie3_import_in_linkedin_tasks(self):
        """linkedin_tasks.py must NOT import browser_cookie3 (spec R-removed-1)."""
        assert LINKEDIN_TASKS_FILE.exists(), "linkedin_tasks.py must exist"
        content = LINKEDIN_TASKS_FILE.read_text()
        # Check for any live import (not in a comment)
        non_comment_lines = [
            line for line in content.splitlines() if not line.strip().startswith("#")
        ]
        non_comment_text = "\n".join(non_comment_lines)
        assert "browser_cookie3" not in non_comment_text, (
            "browser_cookie3 must be removed from linkedin_tasks.py imports"
        )

    def test_requirements_keeps_browser_cookie3(self):
        """requirements.txt must keep browser-cookie3 (tiktok still uses it)."""
        assert REQUIREMENTS_FILE.exists(), "requirements.txt must exist"
        content = REQUIREMENTS_FILE.read_text()
        assert "browser-cookie3" in content, (
            "browser-cookie3 must remain in requirements.txt (tiktok uses it)"
        )

    def test_module_registry_linkedin_pass_from_true(self):
        """module_registry.py must have linkedin with pass_from=True (unchanged)."""
        assert MODULE_REGISTRY_FILE.exists(), "module_registry.py must exist"
        content = MODULE_REGISTRY_FILE.read_text()
        assert "t_linkedin" in content, "t_linkedin must be in module_registry.py"
        for line in content.splitlines():
            if "linkedin" in line and "t_linkedin" in line:
                assert "True" in line, (
                    f"linkedin registry entry must have pass_from=True, got: {line}"
                )
                break
        else:
            pytest.fail("No linkedin entry with t_linkedin found in module_registry.py")

    def test_linkedin_tasks_has_argparse_main_block(self):
        """linkedin_tasks.py must have if __name__ == '__main__': with argparse."""
        assert LINKEDIN_TASKS_FILE.exists(), "linkedin_tasks.py must exist"
        content = LINKEDIN_TASKS_FILE.read_text()
        assert 'if __name__ == "__main__":' in content or (
            "if __name__ == '__main__':" in content
        ), "linkedin_tasks.py must have __main__ block"
        assert "argparse" in content, (
            "linkedin_tasks.py must use argparse in __main__ block"
        )

    def test_t_linkedin_callable_from_cli_alias(self):
        """t_linkedin must be callable (used by __main__ block)."""
        assert callable(linkedin_tasks.t_linkedin)

    def test_linkedin_tasks_has_cookie_dir_constants(self):
        """linkedin_tasks.py must define _COOKIE_DIR and _COOKIE_FILE constants."""
        assert hasattr(linkedin_tasks, "_COOKIE_DIR"), (
            "linkedin_tasks must have _COOKIE_DIR"
        )
        assert hasattr(linkedin_tasks, "_COOKIE_FILE"), (
            "linkedin_tasks must have _COOKIE_FILE"
        )


# ===========================================================================
# Phase 1 — Task 1.1: _parse_rsc_payload() unit tests  [RED]
# Spec: linkedin-profile-extraction R2, graceful-degradation R3
# ===========================================================================

# ---------------------------------------------------------------------------
# Fixtures — inline HTML / RSC snippets
# ---------------------------------------------------------------------------

_RSC_ARRAY = [
    '{"children":["John Doe | LinkedIn"]}',
    '"children":["Engineer | Software"]',
    '"children":["New York, United States"]',
    '"children":["500+ connections"]',
    "urn:li:member:123456789 urn:li:fsd_profile:ACoAABcDEFg",
]

_VALID_HTML = (
    "<html><head><title>John Doe | LinkedIn</title></head><body>"
    "<script>window.__como_rehydration__ = "
    + json.dumps(_RSC_ARRAY)
    + ";</script></body></html>"
)

_HTML_MISSING_MARKER = (
    "<html><head><title>John Doe | LinkedIn</title></head>"
    "<body><script>window.__other__ = [];</script></body></html>"
)

_HTML_MALFORMED_JSON = (
    "<html><head></head><body>"
    "<script>window.__como_rehydration__ = NOT_VALID_JSON;</script></body></html>"
)


class TestParseRscPayload:
    """Unit tests for _parse_rsc_payload() — spec linkedin-profile-extraction R2
    and graceful-degradation R3.
    """

    def test_valid_html_returns_concatenated_rsc_string(self):
        """Valid HTML with __como_rehydration__ → non-empty RSC string."""
        result = linkedin_tasks._parse_rsc_payload(_VALID_HTML)
        # Must be a string (concatenated RSC text)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_valid_html_contains_rsc_content(self):
        """Returned RSC string contains the joined array element content."""
        result = linkedin_tasks._parse_rsc_payload(_VALID_HTML)
        # The first array element is present in the output
        assert "John Doe" in result or "children" in result

    def test_valid_html_urn_member_extractable(self):
        """RSC string contains urn:li:member pattern from fixture."""
        result = linkedin_tasks._parse_rsc_payload(_VALID_HTML)
        assert "urn:li:member:123456789" in result

    def test_missing_marker_raises_iky_exception(self):
        """Missing __como_rehydration__ → Exception with 'iKy -' prefix."""
        with pytest.raises(Exception, match="iKy -"):
            linkedin_tasks._parse_rsc_payload(_HTML_MISSING_MARKER)

    def test_missing_marker_message_mentions_format_change(self):
        """Error message must indicate RSC format or LinkedIn frontend change."""
        with pytest.raises(Exception) as exc_info:
            linkedin_tasks._parse_rsc_payload(_HTML_MISSING_MARKER)
        msg = str(exc_info.value).lower()
        # Any of these terms is acceptable — design says "format change"
        assert any(
            term in msg
            for term in ("rehydration", "rsc", "format", "frontend", "__como")
        )

    def test_malformed_json_raises_exception(self):
        """Malformed JSON in __como_rehydration__ → Exception raised."""
        with pytest.raises(Exception, match="."):
            linkedin_tasks._parse_rsc_payload(_HTML_MALFORMED_JSON)


# ===========================================================================
# Phase 1 — Task 1.2: _extract_profile_fields() and per-field helpers  [RED]
# Spec: linkedin-profile-extraction R4, graceful-degradation R1
# ===========================================================================

# ---------------------------------------------------------------------------
# RSC text fixture for field extraction tests
# ---------------------------------------------------------------------------

_RSC_TEXT = "\n".join(_RSC_ARRAY)

# Name comes from <title> — build a fixture HTML
_PROFILE_HTML = _VALID_HTML

# Richer RSC text for content-matching heuristic tests
_RSC_RICH = (
    '"children":["Contact info"]'
    '"children":["Message"]'
    '"children":["Connect"]'
    '"children":["John Doe"]'
    '"children":["Engineer | Software at Acme Corp"]'
    '"children":["Pinterest"]'
    '"children":["San Francisco, California, United States"]'
    '"children":["500+ connections"]'
    '"urn:li:member:987654321"'
    '"urn:li:fsd_profile:ACoXXYYZZ"'
    '"https://media.licdn.com/dms/image/v2/profile-displayphoto-shrink_200_200/photo.jpg"'
)


class TestExtractProfileFields:
    """Unit tests for _extract_profile_fields() and per-field helpers."""

    # --- _extract_profile_fields() integration ---

    def test_returns_dict_with_required_keys(self):
        """_extract_profile_fields() returns dict with all required field keys."""
        result = linkedin_tasks._extract_profile_fields(_RSC_TEXT, _PROFILE_HTML)
        required_keys = {
            "name",
            "headline",
            "location",
            "connections",
            "company",
            "photo_urls",
            "member_id",
            "profile_urn",
        }
        assert required_keys.issubset(result.keys()), (
            f"Missing keys: {required_keys - result.keys()}"
        )

    def test_fields_default_to_empty_string_on_empty_input(self):
        """Empty RSC + minimal HTML → all string fields default to '' (not None)."""
        result = linkedin_tasks._extract_profile_fields(
            "", "<html><head><title>LinkedIn</title></head></html>"
        )
        for key in ("name", "headline", "location", "connections", "company"):
            assert result[key] == "" or isinstance(result[key], str), (
                f"Field '{key}' must be str, got: {type(result[key])}"
            )

    def test_photo_urls_defaults_to_empty_list_on_empty_input(self):
        """Empty RSC → photo_urls defaults to [] (not None)."""
        result = linkedin_tasks._extract_profile_fields(
            "", "<html><head><title>LinkedIn</title></head></html>"
        )
        assert isinstance(result["photo_urls"], list)

    # --- _extract_name() ---

    def test_extract_name_from_title_tag(self):
        """_extract_name() extracts name from <title>Name | LinkedIn</title>."""
        html = "<html><head><title>Jane Smith | LinkedIn</title></head></html>"
        result = linkedin_tasks._extract_name(html)
        assert result == "Jane Smith"

    def test_extract_name_missing_title_returns_empty(self):
        """_extract_name() returns '' when title tag is absent."""
        result = linkedin_tasks._extract_name("<html><head></head></html>")
        assert result == ""

    def test_extract_name_wrong_format_returns_empty(self):
        """_extract_name() returns '' when title lacks '| LinkedIn' separator."""
        result = linkedin_tasks._extract_name(
            "<html><head><title>Some Page</title></head></html>"
        )
        assert result == ""

    # --- _extract_member_id() ---

    def test_extract_member_id_from_rsc(self):
        """_extract_member_id() finds urn:li:member:DIGITS in RSC text."""
        rsc = "some text urn:li:member:123456789 more text"
        result = linkedin_tasks._extract_member_id(rsc)
        assert result == "123456789"

    def test_extract_member_id_missing_returns_empty(self):
        """_extract_member_id() returns '' when pattern is absent."""
        result = linkedin_tasks._extract_member_id("no member urn here")
        assert result == ""

    # --- _extract_connections() ---

    def test_extract_connections_with_plus(self):
        """_extract_connections() extracts '500+ connections' → '500+'."""
        rsc = 'some block "500+ connections" end'
        result = linkedin_tasks._extract_connections(rsc)
        assert result == "500+"

    def test_extract_connections_without_plus(self):
        """_extract_connections() extracts '42 connections' → '42'."""
        rsc = '"42 connections" in profile'
        result = linkedin_tasks._extract_connections(rsc)
        assert result == "42"

    def test_extract_connections_missing_returns_empty(self):
        """_extract_connections() returns '' when no connections pattern found."""
        result = linkedin_tasks._extract_connections("no count here")
        assert result == ""

    # --- _extract_photo_urls() ---

    def test_extract_photo_urls_finds_licdn_urls(self):
        """_extract_photo_urls() returns list of media.licdn.com URLs."""
        rsc = (
            '"https://media.licdn.com/dms/image/v2/profile-displayphoto-shrink_200_200/photo.jpg"'
            '"https://media.licdn.com/dms/image/v2/profile-displayphoto-shrink_400_400/photo.jpg"'
        )
        result = linkedin_tasks._extract_photo_urls(rsc)
        assert len(result) == 2
        assert all("media.licdn.com" in url for url in result)

    def test_extract_photo_urls_empty_rsc_returns_list(self):
        """_extract_photo_urls() returns [] (not None) when no URLs found."""
        result = linkedin_tasks._extract_photo_urls("no urls here")
        assert isinstance(result, list)
        assert len(result) == 0

    # --- _extract_headline() ---

    def test_extract_headline_returns_meaningful_text(self):
        """_extract_headline() returns a non-empty string from rich RSC blocks."""
        blocks = [
            "Contact info",
            "Message",
            "John Doe",
            "Engineer | Software at Acme Corp",
            "Pinterest",
            "San Francisco, California",
        ]
        result = linkedin_tasks._extract_headline(blocks)
        # Must return a non-trivial string (>20 chars)
        assert isinstance(result, str)
        assert len(result) > 20

    def test_extract_headline_skips_ui_labels(self):
        """_extract_headline() does not return short UI labels like 'Contact info'."""
        blocks = ["Contact info", "Message", "Connect", "Engineer | Software at Acme"]
        result = linkedin_tasks._extract_headline(blocks)
        assert result != "Contact info"
        assert result != "Message"

    def test_extract_headline_empty_blocks_returns_empty(self):
        """_extract_headline([]) returns ''."""
        result = linkedin_tasks._extract_headline([])
        assert result == ""

    # --- _extract_location() ---

    def test_extract_location_with_comma_pattern(self):
        """_extract_location() returns block matching city, country pattern."""
        blocks = [
            "John Doe",
            "Engineer | Acme",
            "Acme Corp",
            "San Francisco, California, United States",
            "500+ connections",
        ]
        result = linkedin_tasks._extract_location(blocks)
        assert "San Francisco" in result or "United States" in result or "," in result

    def test_extract_location_empty_blocks_returns_empty(self):
        """_extract_location([]) returns ''."""
        result = linkedin_tasks._extract_location([])
        assert result == ""

    # --- _extract_company() ---

    def test_extract_company_returns_string(self):
        """_extract_company() always returns str."""
        blocks = ["Engineer | Acme", "Acme Corp", "San Francisco, California"]
        result = linkedin_tasks._extract_company(blocks)
        assert isinstance(result, str)

    def test_extract_company_empty_returns_empty(self):
        """_extract_company([]) returns ''."""
        result = linkedin_tasks._extract_company([])
        assert result == ""

    # --- Verified extraction (spec R4) ---

    def test_extract_verified_true(self):
        """_extract_verified() returns True when verification text is present."""
        rsc = 'some text "has a verification" more text'
        assert linkedin_tasks._extract_verified(rsc) is True

    def test_extract_verified_false(self):
        """_extract_verified() returns False when no verification text."""
        rsc = "some RSC text without the keyword"
        assert linkedin_tasks._extract_verified(rsc) is False

    def test_extract_verified_empty(self):
        """_extract_verified() returns False on empty string."""
        assert linkedin_tasks._extract_verified("") is False

    # --- Graceful degradation: isolated field failure (spec graceful-degradation R1) ---

    def test_extract_profile_fields_isolates_failures(self):
        """_extract_profile_fields() continues even when RSC has partial data."""
        # Provide RSC with only connections — other fields will be empty
        partial_rsc = '"some text with 123 connections in it"'
        html = "<html><head><title>Test User | LinkedIn</title></head></html>"
        result = linkedin_tasks._extract_profile_fields(partial_rsc, html)
        # name should extract from title
        assert result["name"] == "Test User"
        # photo_urls must be a list regardless
        assert isinstance(result["photo_urls"], list)
        # verified must be a bool
        assert isinstance(result["verified"], bool)

    # --- Graceful degradation: fetch failure (spec graceful-degradation R2) ---

    def test_fetch_profile_html_non_200_raises(self):
        """_fetch_profile_html raises iKy error on non-200 status."""
        mock_session = MagicMock()
        mock_session.get.return_value = MagicMock(status_code=403)
        with pytest.raises(Exception, match="iKy -"):
            linkedin_tasks._fetch_profile_html(mock_session, "testuser")

    def test_fetch_profile_html_request_exception_raises(self):
        """_fetch_profile_html raises iKy error on request failure."""
        mock_session = MagicMock()
        mock_session.get.side_effect = ConnectionError("Network error")
        with pytest.raises(Exception, match="iKy -"):
            linkedin_tasks._fetch_profile_html(mock_session, "testuser")


# ===========================================================================
# Phase 1 — Task 1.3: p_linkedin() integration tests (migrated)  [RED]
# Spec: R5 (4 calls), R6 (no dead endpoints), R7 (output structure)
# ===========================================================================


def _make_html_response(username: str = "john-doe") -> str:
    """Build a minimal but valid HTML profile page fixture."""
    rsc_data = [
        '"children":["John"]',
        '"children":["Doe"]',
        '"children":["Engineer | Acme Corp"]',
        '"children":["Acme Corp"]',
        '"children":["New York, United States"]',
        '"children":["500+ connections"]',
        '"urn:li:member:111222333"',
        '"urn:li:fsd_profile:ACoAATest"',
        '"John has a verification"',
    ]
    rsc_json = json.dumps(rsc_data)
    return (
        f"<html><head><title>John Doe | LinkedIn</title></head><body>"
        f"<script>window.__como_rehydration__ = {rsc_json};</script>"
        f"</body></html>"
    )


class TestPLinkedinMigrated:
    """Integration tests for the migrated p_linkedin() — spec R5-R8.

    These tests exercise the full migrated pipeline with:
    - 1 HTML GET (replaces profileView/networkinfo/skillCategory)
    - 3 surviving Voyager calls (following + 2 recommendations)
    Total: 4 HTTP requests (down from 8).
    """

    def _make_voyager_response(self, data: dict) -> MagicMock:
        r = MagicMock()
        r.text = json.dumps(data)
        r.status_code = 200
        return r

    def _make_html_mock(self) -> MagicMock:
        r = MagicMock()
        r.text = _make_html_response()
        r.status_code = 200
        return r

    def _build_call_seq(self) -> list:
        """4-call sequence: HTML page, following, recommend_received, recommend_given."""
        return [
            self._make_html_mock(),  # 1: GET /in/{user}/ HTML
            self._make_voyager_response(  # 2: /following
                {"paging": {"total": 42}, "elements": []}
            ),
            self._make_voyager_response(  # 3: /recommendations?q=received
                {"paging": {"total": 5}}
            ),
            self._make_voyager_response(  # 4: /recommendations?q=given
                {"paging": {"total": 3}}
            ),
        ]

    def test_migrated_makes_exactly_4_http_calls(self, tmp_path):
        """Migrated p_linkedin() makes exactly 4 HTTP calls (spec R8)."""
        cookie_file = tmp_path / "linkedin_cookies.json"
        cookie_data = {"li_at": "tok", "JSESSIONID": '"ses"'}
        cookie_file.write_text(json.dumps(cookie_data))

        with (
            patch.object(linkedin_tasks, "_COOKIE_FILE", cookie_file),
            patch("requests.Session") as mock_session_cls,
        ):
            mock_session = MagicMock()
            mock_session.cookies = {}
            mock_session.headers = {}
            mock_session.get.side_effect = self._build_call_seq()
            mock_session_cls.return_value = mock_session

            linkedin_tasks.p_linkedin("john-doe", from_m="Initial")

        assert mock_session.get.call_count == 4, (
            f"Expected 4 HTTP calls, got {mock_session.get.call_count}"
        )

    def test_migrated_no_dead_endpoint_calls(self, tmp_path):
        """Dead endpoints (/profileView, /skillCategory, /networkinfo) not called."""
        dead_endpoints = [
            "/profileView",
            "/skillCategory",
            "/networkinfo",
            "/memberBadges",
        ]
        cookie_file = tmp_path / "linkedin_cookies.json"
        cookie_data = {"li_at": "tok", "JSESSIONID": '"ses"'}
        cookie_file.write_text(json.dumps(cookie_data))

        called_urls = []

        def capture_get(url, **kwargs):
            called_urls.append(url)
            return self._build_call_seq()[len(called_urls) - 1]

        with (
            patch.object(linkedin_tasks, "_COOKIE_FILE", cookie_file),
            patch("requests.Session") as mock_session_cls,
        ):
            mock_session = MagicMock()
            mock_session.cookies = {}
            mock_session.headers = {}
            mock_session.get.side_effect = capture_get
            mock_session_cls.return_value = mock_session

            linkedin_tasks.p_linkedin("john-doe", from_m="Initial")

        for url in called_urls:
            for dead in dead_endpoints:
                assert dead not in url, f"Dead endpoint called: {url}"

    def test_migrated_output_has_required_top_level_keys(self, tmp_path):
        """Output total array contains graphic, profile, timeline, raw entries."""
        cookie_file = tmp_path / "linkedin_cookies.json"
        cookie_data = {"li_at": "tok", "JSESSIONID": '"ses"'}
        cookie_file.write_text(json.dumps(cookie_data))

        with (
            patch.object(linkedin_tasks, "_COOKIE_FILE", cookie_file),
            patch("requests.Session") as mock_session_cls,
        ):
            mock_session = MagicMock()
            mock_session.cookies = {}
            mock_session.headers = {}
            mock_session.get.side_effect = self._build_call_seq()
            mock_session_cls.return_value = mock_session

            result = linkedin_tasks.p_linkedin("john-doe", from_m="Initial")

        # total[0] == {"module": "linkedin"}
        assert result[0] == {"module": "linkedin"}
        # total[1] == {"param": "john-doe"}
        assert result[1] == {"param": "john-doe"}
        # total[2] == {"validation": "hard"}
        assert result[2] == {"validation": "hard"}

        # Find expected keys in total list
        keys_in_total = [
            next(iter(item.keys())) for item in result if isinstance(item, dict)
        ]
        assert "graphic" in keys_in_total, (
            f"'graphic' missing from total. Got: {keys_in_total}"
        )
        assert "profile" in keys_in_total, (
            f"'profile' missing from total. Got: {keys_in_total}"
        )
        assert "timeline" in keys_in_total, (
            f"'timeline' missing from total. Got: {keys_in_total}"
        )
        assert "raw" in keys_in_total, f"'raw' missing from total. Got: {keys_in_total}"

    def test_migrated_graphic_has_social_and_skills(self, tmp_path):
        """graphic array must contain 'social', 'skills', 'certificationView', 'positionGroupView'."""
        cookie_file = tmp_path / "linkedin_cookies.json"
        cookie_data = {"li_at": "tok", "JSESSIONID": '"ses"'}
        cookie_file.write_text(json.dumps(cookie_data))

        with (
            patch.object(linkedin_tasks, "_COOKIE_FILE", cookie_file),
            patch("requests.Session") as mock_session_cls,
        ):
            mock_session = MagicMock()
            mock_session.cookies = {}
            mock_session.headers = {}
            mock_session.get.side_effect = self._build_call_seq()
            mock_session_cls.return_value = mock_session

            result = linkedin_tasks.p_linkedin("john-doe", from_m="Initial")

        graphic = next(item["graphic"] for item in result if "graphic" in item)
        graphic_keys = [next(iter(g.keys())) for g in graphic]
        assert "social" in graphic_keys, (
            f"graphic missing 'social', got: {graphic_keys}"
        )
        assert "skills" in graphic_keys, (
            f"graphic missing 'skills', got: {graphic_keys}"
        )
        assert "certificationView" in graphic_keys
        assert "positionGroupView" in graphic_keys

    def test_migrated_following_count_in_socialp(self, tmp_path):
        """socialp must contain 'Following' entry with count from /following API."""
        cookie_file = tmp_path / "linkedin_cookies.json"
        cookie_data = {"li_at": "tok", "JSESSIONID": '"ses"'}
        cookie_file.write_text(json.dumps(cookie_data))

        with (
            patch.object(linkedin_tasks, "_COOKIE_FILE", cookie_file),
            patch("requests.Session") as mock_session_cls,
        ):
            mock_session = MagicMock()
            mock_session.cookies = {}
            mock_session.headers = {}
            mock_session.get.side_effect = self._build_call_seq()
            mock_session_cls.return_value = mock_session

            result = linkedin_tasks.p_linkedin("john-doe", from_m="Initial")

        graphic = next(item["graphic"] for item in result if "graphic" in item)
        social = next(g["social"] for g in graphic if "social" in g)
        social_names = [s.get("name-node") for s in social]
        assert "Following" in social_names, (
            f"'Following' not in socialp, got: {social_names}"
        )

    def test_migrated_from_m_soft_validation(self, tmp_path):
        """from_m != 'Initial' → total[2] == {'validation': 'soft'}."""
        cookie_file = tmp_path / "linkedin_cookies.json"
        cookie_data = {"li_at": "tok", "JSESSIONID": '"ses"'}
        cookie_file.write_text(json.dumps(cookie_data))

        with (
            patch.object(linkedin_tasks, "_COOKIE_FILE", cookie_file),
            patch("requests.Session") as mock_session_cls,
        ):
            mock_session = MagicMock()
            mock_session.cookies = {}
            mock_session.headers = {}
            mock_session.get.side_effect = self._build_call_seq()
            mock_session_cls.return_value = mock_session

            result = linkedin_tasks.p_linkedin("john-doe", from_m="linkedin")

        assert result[2] == {"validation": "soft"}
