"""Unit tests for the shared cookie conversion helpers.

Covers ``factories.cookie_utils``:
- ``convert_browser_cookies()`` — flat dict passthrough, list export
  conversion, Name/Value capitalized keys, ValueError on bad input.
- ``missing_required_cookies()`` — detects absent and empty-string keys.

These helpers consolidate the previously-duplicated per-module converters
(linkedin/twitter/tiktok) so the host grab script and the in-container auth
chain share one byte-compatible flat-format contract.
"""

from __future__ import annotations

import pytest
from factories.cookie_utils import (
    convert_browser_cookies,
    missing_required_cookies,
)


class TestConvertBrowserCookies:
    """convert_browser_cookies() — spec Flat-Format Contract."""

    def test_flat_dict_passthrough(self):
        """Already-flat dict passes through unchanged."""
        raw = {"li_at": "abc123", "JSESSIONID": '"xyz789"'}
        result = convert_browser_cookies(raw)
        assert result == {"li_at": "abc123", "JSESSIONID": '"xyz789"'}

    def test_flat_dict_values_coerced_to_str(self):
        """Dict values are string-coerced (int/bool become str)."""
        raw = {"msToken": 12345, "flag": True}
        result = convert_browser_cookies(raw)
        assert result == {"msToken": "12345", "flag": "True"}
        for value in result.values():
            assert isinstance(value, str)

    def test_list_export_conversion(self):
        """Browser list export [{name, value}] -> flat {name: value} dict."""
        raw = [
            {"name": "li_at", "value": "abc123"},
            {"name": "JSESSIONID", "value": '"xyz789"'},
        ]
        result = convert_browser_cookies(raw)
        assert result == {"li_at": "abc123", "JSESSIONID": '"xyz789"'}

    def test_list_export_with_extra_fields(self):
        """Full Cookie-Editor export (domain, path, secure) keeps only name/value."""
        raw = [
            {
                "domain": ".linkedin.com",
                "name": "li_at",
                "value": "tok",
                "path": "/",
                "secure": True,
            }
        ]
        result = convert_browser_cookies(raw)
        assert result == {"li_at": "tok"}

    def test_capitalized_name_value_keys(self):
        """Supports 'Name'/'Value' capitalized keys as a fallback."""
        raw = [{"Name": "li_at", "Value": "tok123"}]
        result = convert_browser_cookies(raw)
        assert result == {"li_at": "tok123"}

    def test_list_item_without_name_is_skipped(self):
        """Items missing a name are silently skipped."""
        raw = [
            {"name": "li_at", "value": "abc"},
            {"value": "orphan"},
            {"name": "JSESSIONID", "value": "xyz"},
        ]
        result = convert_browser_cookies(raw)
        assert result == {"li_at": "abc", "JSESSIONID": "xyz"}

    def test_list_item_missing_value_defaults_to_empty_string(self):
        """A cookie with no value field becomes an empty string."""
        raw = [{"name": "li_at"}]
        result = convert_browser_cookies(raw)
        assert result == {"li_at": ""}

    def test_empty_list_returns_empty_dict(self):
        """Empty list -> empty dict (no crash)."""
        assert convert_browser_cookies([]) == {}

    def test_invalid_str_raises_value_error(self):
        """A bare string is neither list nor dict -> ValueError."""
        with pytest.raises(ValueError, match="Unexpected cookie format"):
            convert_browser_cookies("not-a-list-or-dict")  # type: ignore[arg-type]

    def test_invalid_int_raises_value_error(self):
        """An int input -> ValueError naming the bad type."""
        with pytest.raises(ValueError, match="Unexpected cookie format"):
            convert_browser_cookies(42)  # type: ignore[arg-type]


class TestMissingRequiredCookies:
    """missing_required_cookies() — required-key validation."""

    def test_all_present_returns_empty(self):
        """All required keys present with non-empty values -> []."""
        cookies = {"li_at": "tok", "JSESSIONID": '"ses"', "extra": "x"}
        assert missing_required_cookies(cookies, ["li_at", "JSESSIONID"]) == []

    def test_absent_key_is_reported(self):
        """A required key absent from the dict is reported."""
        cookies = {"li_at": "tok"}
        assert missing_required_cookies(cookies, ["li_at", "JSESSIONID"]) == [
            "JSESSIONID"
        ]

    def test_empty_string_value_is_reported(self):
        """A required key present but empty-string is reported as missing."""
        cookies = {"li_at": "tok", "JSESSIONID": ""}
        assert missing_required_cookies(cookies, ["li_at", "JSESSIONID"]) == [
            "JSESSIONID"
        ]

    def test_multiple_missing_preserve_required_order(self):
        """Multiple missing keys are returned in the order they were required."""
        cookies = {"other": "x"}
        assert missing_required_cookies(cookies, ["li_at", "JSESSIONID"]) == [
            "li_at",
            "JSESSIONID",
        ]

    def test_no_required_keys_returns_empty(self):
        """An empty required iterable -> nothing missing."""
        assert missing_required_cookies({"li_at": "tok"}, []) == []
