"""Unit tests for the host-side browser cookie grab core.

Covers ``factories.cookie_grab`` — the container-testable orchestration that
backs the host CLI ``install/scripts/grab_cookies.py``.

Why this layer (deviation note):
    The host script lives at ``install/scripts/grab_cookies.py`` which is NOT
    copied into the backend Docker image (only ``backend/`` -> ``/app`` is).
    The design assumed the script could be imported under container pytest with
    a mocked ``browser_cookie3``; that is impossible because the file is absent
    in the container.  The grab logic is therefore extracted into
    ``factories.cookie_grab`` (reachable + testable in the container) and the
    script becomes a thin host wrapper.

Why dependency injection instead of ``sys.modules`` mocking:
    ``browser_cookie3.BrowserCookieError`` is needed in ``except`` clauses.  A
    ``MagicMock`` attribute is not a real exception class, so
    ``except browser_cookie3.BrowserCookieError`` would raise ``TypeError``.
    The core never imports ``browser_cookie3``; callers inject browser loader
    callables and the concrete exception types.  Tests inject fakes.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from pathlib import Path
from typing import ClassVar

import pytest
from factories.cookie_grab import (
    BROWSER_ORDER,
    MODULE_REQUIRED,
    BrowserResult,
    extract_browser_cookies,
    run_grab,
)
from factories.cookie_utils import convert_browser_cookies


class FakeBrowserCookieError(Exception):
    """Stands in for ``browser_cookie3.BrowserCookieError``."""


# Browser export with the two LinkedIn-required cookies plus noise.
VALID_LINKEDIN_EXPORT = [
    {"domain": ".linkedin.com", "name": "li_at", "value": "AQEDtok123"},
    {"domain": ".linkedin.com", "name": "JSESSIONID", "value": '"ajax:9876"'},
    {"domain": ".linkedin.com", "name": "bcookie", "value": "v=2&abc"},
]


def _loader_returning(raw):
    """Build a browser loader callable that returns ``raw``."""

    def _loader(domain_name=None):
        return raw

    return _loader


def _loader_raising(exc):
    """Build a browser loader callable that raises ``exc``."""

    def _loader(domain_name=None):
        raise exc

    return _loader


def _factory(mapping):
    """Build a loader_factory from a {browser_name: loader} mapping."""

    def _loader_factory(names):
        return {name: mapping[name] for name in names if name in mapping}

    return _loader_factory


# ===========================================================================
# extract_browser_cookies — per-browser classification (triangulation core)
# ===========================================================================


class TestExtractBrowserCookies:
    """Single-browser extraction classifies status and missing keys."""

    REQUIRED: ClassVar[list[str]] = ["li_at", "JSESSIONID"]

    def test_success_with_all_required_keys(self):
        result = extract_browser_cookies(
            "chrome",
            _loader_returning(VALID_LINKEDIN_EXPORT),
            "linkedin.com",
            self.REQUIRED,
        )
        assert isinstance(result, BrowserResult)
        assert result.name == "chrome"
        assert result.status == "success"
        assert result.count == 3
        assert result.missing == []
        assert result.valid is True
        assert result.cookies["li_at"] == "AQEDtok123"
        assert result.cookies["JSESSIONID"] == '"ajax:9876"'

    def test_success_but_missing_required_key_is_not_valid(self):
        only_li_at = [{"name": "li_at", "value": "tok"}]
        result = extract_browser_cookies(
            "firefox", _loader_returning(only_li_at), "linkedin.com", self.REQUIRED
        )
        assert result.status == "success"
        assert result.count == 1
        assert result.missing == ["JSESSIONID"]
        assert result.valid is False

    def test_database_locked_is_classified_locked(self):
        result = extract_browser_cookies(
            "firefox",
            _loader_raising(sqlite3.OperationalError("database is locked")),
            "linkedin.com",
            self.REQUIRED,
        )
        assert result.status == "locked"
        assert result.count == 0
        assert result.valid is False

    def test_other_operational_error_is_classified_error(self):
        result = extract_browser_cookies(
            "chrome",
            _loader_raising(sqlite3.OperationalError("no such table: cookies")),
            "linkedin.com",
            self.REQUIRED,
        )
        assert result.status == "error"
        assert result.valid is False

    def test_browser_cookie_error_is_classified_error(self):
        result = extract_browser_cookies(
            "brave",
            _loader_raising(FakeBrowserCookieError("keyring locked")),
            "linkedin.com",
            self.REQUIRED,
            browser_error_types=(FakeBrowserCookieError,),
        )
        assert result.status == "error"
        assert result.valid is False

    def test_runtime_error_is_classified_error(self):
        result = extract_browser_cookies(
            "edge",
            _loader_raising(RuntimeError("Failed to decrypt")),
            "linkedin.com",
            self.REQUIRED,
        )
        assert result.status == "error"
        assert result.valid is False

    def test_value_error_is_classified_error(self):
        result = extract_browser_cookies(
            "edge",
            _loader_raising(ValueError("bad profile")),
            "linkedin.com",
            self.REQUIRED,
        )
        assert result.status == "error"
        assert result.valid is False

    def test_zero_cookies_is_classified_empty(self):
        result = extract_browser_cookies(
            "chrome", _loader_returning([]), "linkedin.com", self.REQUIRED
        )
        assert result.status == "empty"
        assert result.count == 0
        assert result.missing == ["li_at", "JSESSIONID"]
        assert result.valid is False


# ===========================================================================
# run_grab — orchestration, exit codes, output file
# ===========================================================================


class TestRunGrabSuccess:
    """At least one browser yields all required keys -> exit 0 + flat JSON."""

    def test_single_browser_success_writes_flat_json_exit_0(self, tmp_path):
        out = tmp_path / "linkedin_cookies.json"
        code = run_grab(
            module="linkedin",
            domain="linkedin.com",
            browser=None,
            out=str(out),
            loader_factory=_factory(
                {
                    "firefox": _loader_returning([]),
                    "chrome": _loader_returning(VALID_LINKEDIN_EXPORT),
                    "brave": _loader_returning([]),
                    "edge": _loader_returning([]),
                }
            ),
        )
        assert code == 0
        assert out.exists()
        data = json.loads(out.read_text())
        assert isinstance(data, dict)
        assert data["li_at"] == "AQEDtok123"
        assert data["JSESSIONID"] == '"ajax:9876"'

    def test_output_is_byte_compatible_with_convert_browser_cookies(self, tmp_path):
        out = tmp_path / "linkedin_cookies.json"
        run_grab(
            module="linkedin",
            domain="linkedin.com",
            browser="chrome",
            out=str(out),
            loader_factory=_factory(
                {"chrome": _loader_returning(VALID_LINKEDIN_EXPORT)}
            ),
        )
        written = json.loads(out.read_text())
        assert written == convert_browser_cookies(VALID_LINKEDIN_EXPORT)
        # Flat contract: no nested objects, all string values.
        assert all(isinstance(v, str) for v in written.values())

    def test_first_valid_browser_in_order_wins(self, tmp_path):
        out = tmp_path / "linkedin_cookies.json"
        other = [
            {"name": "li_at", "value": "FIREFOX_TOKEN"},
            {"name": "JSESSIONID", "value": '"ff"'},
        ]
        code = run_grab(
            module="linkedin",
            domain="linkedin.com",
            browser=None,
            out=str(out),
            loader_factory=_factory(
                {
                    "firefox": _loader_returning(other),
                    "chrome": _loader_returning(VALID_LINKEDIN_EXPORT),
                    "brave": _loader_returning([]),
                    "edge": _loader_returning([]),
                }
            ),
        )
        assert code == 0
        # firefox comes first in BROWSER_ORDER and is valid -> it wins.
        assert json.loads(out.read_text())["li_at"] == "FIREFOX_TOKEN"


class TestRunGrabFailureCodes:
    """Exit codes 1/2/3 for the documented failure modes."""

    def test_no_browser_yields_required_keys_exit_1(self, tmp_path):
        out = tmp_path / "linkedin_cookies.json"
        code = run_grab(
            module="linkedin",
            domain="linkedin.com",
            browser=None,
            out=str(out),
            loader_factory=_factory(
                {
                    "firefox": _loader_raising(
                        sqlite3.OperationalError("database is locked")
                    ),
                    "chrome": _loader_returning([{"name": "li_at", "value": "x"}]),
                    "brave": _loader_returning([]),
                    "edge": _loader_raising(RuntimeError("decrypt failed")),
                }
            ),
        )
        assert code == 1
        assert not out.exists()

    def test_unknown_module_exit_2(self, tmp_path):
        out = tmp_path / "x.json"
        code = run_grab(
            module="myspace",
            domain=None,
            browser=None,
            out=str(out),
            loader_factory=_factory({}),
        )
        assert code == 2
        assert not out.exists()

    def test_unknown_browser_exit_2(self, tmp_path):
        out = tmp_path / "x.json"
        code = run_grab(
            module="linkedin",
            domain="linkedin.com",
            browser="netscape",
            out=str(out),
            loader_factory=_factory(
                {"chrome": _loader_returning(VALID_LINKEDIN_EXPORT)}
            ),
        )
        assert code == 2
        assert not out.exists()

    def test_write_failure_exit_3(self, tmp_path):
        # Output path points inside a *file* (not a dir) -> open() raises.
        not_a_dir = tmp_path / "afile"
        not_a_dir.write_text("x")
        out = not_a_dir / "linkedin_cookies.json"
        code = run_grab(
            module="linkedin",
            domain="linkedin.com",
            browser="chrome",
            out=str(out),
            loader_factory=_factory(
                {"chrome": _loader_returning(VALID_LINKEDIN_EXPORT)}
            ),
        )
        assert code == 3


class TestRunGrabBrowserNarrowing:
    """Optional browser arg narrows iteration to exactly one browser."""

    def test_only_named_browser_is_attempted(self, tmp_path):
        out = tmp_path / "linkedin_cookies.json"
        attempted: list[str] = []

        def _tracking_loader(name, raw):
            def _loader(domain_name=None):
                attempted.append(name)
                return raw

            return _loader

        code = run_grab(
            module="linkedin",
            domain="linkedin.com",
            browser="firefox",
            out=str(out),
            loader_factory=_factory(
                {
                    "firefox": _tracking_loader("firefox", VALID_LINKEDIN_EXPORT),
                    "chrome": _tracking_loader("chrome", VALID_LINKEDIN_EXPORT),
                }
            ),
        )
        assert code == 0
        assert attempted == ["firefox"]

    def test_default_domain_used_when_domain_omitted(self, tmp_path):
        out = tmp_path / "linkedin_cookies.json"
        seen_domains: list[str | None] = []

        def _loader(domain_name=None):
            seen_domains.append(domain_name)
            return VALID_LINKEDIN_EXPORT

        code = run_grab(
            module="linkedin",
            domain=None,
            browser="chrome",
            out=str(out),
            loader_factory=_factory({"chrome": _loader}),
        )
        assert code == 0
        assert seen_domains == ["linkedin.com"]


class TestRunGrabLogging:
    """One log line per browser + a final summary line (explicit product req)."""

    def test_per_browser_log_lines(self, tmp_path, caplog):
        out = tmp_path / "linkedin_cookies.json"
        with caplog.at_level(logging.INFO):
            run_grab(
                module="linkedin",
                domain="linkedin.com",
                browser=None,
                out=str(out),
                loader_factory=_factory(
                    {
                        "firefox": _loader_raising(
                            sqlite3.OperationalError("database is locked")
                        ),
                        "chrome": _loader_returning(VALID_LINKEDIN_EXPORT),
                        "brave": _loader_raising(RuntimeError("keyring boom")),
                        "edge": _loader_returning([]),
                    }
                ),
            )
        text = caplog.text
        lower = text.lower()
        assert "firefox" in text and "database is locked" in text
        assert "chrome" in text and "success" in text and "3" in text
        assert "brave" in text and ("keyring" in lower or "decrypt" in lower)
        assert "edge" in text and "zero cookies" in text

    def test_final_summary_line(self, tmp_path, caplog):
        out = tmp_path / "linkedin_cookies.json"
        with caplog.at_level(logging.INFO):
            run_grab(
                module="linkedin",
                domain="linkedin.com",
                browser=None,
                out=str(out),
                loader_factory=_factory(
                    {
                        "firefox": _loader_returning([]),
                        "chrome": _loader_returning(VALID_LINKEDIN_EXPORT),
                        "brave": _loader_returning([]),
                        "edge": _loader_returning([]),
                    }
                ),
            )
        text = caplog.text.lower()
        assert "summary" in text
        assert str(out) in caplog.text  # output path reported


# ===========================================================================
# Static contract — module registry exposes LinkedIn pilot
# ===========================================================================


class TestModuleRegistry:
    def test_browser_order_is_the_four_supported_browsers(self):
        assert BROWSER_ORDER == ("firefox", "chrome", "brave", "edge")

    def test_linkedin_required_keys(self):
        assert MODULE_REQUIRED["linkedin"]["required"] == ["li_at", "JSESSIONID"]
        assert MODULE_REQUIRED["linkedin"]["domain"] == "linkedin.com"


class TestScriptArtifact:
    """The host CLI wrapper must exist and stay a thin wrapper."""

    SCRIPT = (
        Path(__file__).resolve().parent.parent.parent
        / "install"
        / "scripts"
        / "grab_cookies.py"
    )

    @pytest.mark.skipif(
        not SCRIPT.exists(),
        reason="host script not present in this checkout (absent in container image)",
    )
    def test_script_delegates_to_core(self):
        source = self.SCRIPT.read_text()
        assert "cookie_grab" in source, "CLI must delegate to factories.cookie_grab"
        assert "run_grab" in source, "CLI must call run_grab"
        assert "import browser_cookie3" in source, "CLI provides the real dependency"
