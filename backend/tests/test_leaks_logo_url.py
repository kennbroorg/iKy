"""Coverage for `_compose_logo_url` in `modules.leaks.leaks_tasks`.

REQ 3 of the `fix-functionality` SDD change: when XposedOrNot's API returns a
fully-qualified URL in the `logo` field, the leaks task MUST use it as-is
instead of prepending the legacy `https://xposedornot.com/img/` base (which
yields a broken `https://xposedornot.com/img/https://...` URL on the XON
Graphs node).

The helper is module-private (`_` prefix) — importing it directly is the
standard Python testing pattern and intentional per the design.
"""

from modules.leaks.leaks_tasks import _compose_logo_url


class TestComposeLogoUrl:
    def test_https_url_passes_through_unchanged(self):
        """AC3.1 — absolute HTTPS URL stays exactly as received."""
        url = "https://xposedornot.com/static/logos/Linkedin.png"
        assert _compose_logo_url(url) == url

    def test_http_url_passes_through_unchanged(self):
        """AC3.2 — absolute HTTP URL stays exactly as received."""
        url = "http://example.com/x.png"
        assert _compose_logo_url(url) == url

    def test_relative_path_gets_base_prepended(self):
        """AC3.3 — bare filename is composed onto the legacy XON base."""
        assert (
            _compose_logo_url("Linkedin.png")
            == "https://xposedornot.com/img/Linkedin.png"
        )

    def test_empty_string_passes_through(self):
        """AC3.4 — empty string stays empty, no spurious base prepended."""
        assert _compose_logo_url("") == ""

    def test_none_passes_through(self):
        """AC3.4 — None stays None, no spurious base prepended."""
        assert _compose_logo_url(None) is None

    def test_https_url_is_json_serializable(self):
        """AC3.5 — output of a real call site stays JSON-serializable."""
        import json

        composed = _compose_logo_url(
            "https://xposedornot.com/static/logos/Linkedin.png"
        )
        # Must round-trip through json without raising.
        assert json.loads(json.dumps({"picture": composed}))["picture"] == composed

    def test_relative_path_is_json_serializable(self):
        """AC3.5 — relative composition path also stays JSON-serializable."""
        import json

        composed = _compose_logo_url("Linkedin.png")
        assert json.loads(json.dumps({"picture": composed}))["picture"] == composed
