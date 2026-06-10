"""Unit tests for backend/factories/search_providers.py.

Covers DuckDuckGoProvider, GoogleProvider, BraveSearchProvider, and
DeprecatedProvider using mocks — no real network calls are made.
"""

import sys
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Stub heavy optional dependencies before the module is imported so tests
# run in environments that don't have ddgs or googlesearch-python
# installed locally (Docker-only deps).
# ---------------------------------------------------------------------------

if "ddgs" not in sys.modules:
    sys.modules["ddgs"] = MagicMock()

if "googlesearch" not in sys.modules:
    sys.modules["googlesearch"] = MagicMock()

if "googleapiclient" not in sys.modules:
    sys.modules["googleapiclient"] = MagicMock()
    sys.modules["googleapiclient.discovery"] = MagicMock()

from factories.search_providers import (
    BraveSearchProvider,
    DeprecatedProvider,
    DuckDuckGoProvider,
    GoogleProvider,
    SearchResult,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_DDGS_RESULTS = [
    {"title": "DDG Title 1", "href": "https://example.com/1", "body": "Desc 1"},
    {"title": "DDG Title 2", "href": "https://example.com/2", "body": "Desc 2"},
]

_GOOGLE_RESULTS = [
    SimpleNamespace(title="G Title 1", url="https://google.com/1", description="GD 1"),
    SimpleNamespace(title="G Title 2", url="https://google.com/2", description="GD 2"),
]

_BRAVE_RESPONSE = {
    "web": {
        "results": [
            {
                "title": "Brave Title 1",
                "url": "https://brave.com/1",
                "description": "BD 1",
            },
            {
                "title": "Brave Title 2",
                "url": "https://brave.com/2",
                "description": "BD 2",
            },
        ]
    }
}


# ===========================================================================
# DuckDuckGoProvider
# ===========================================================================


class TestDuckDuckGoProvider:
    """Tests for DuckDuckGoProvider."""

    @pytest.fixture(autouse=True)
    def _no_sleep(self):
        """Suppress real time.sleep calls in all DDG tests."""
        with patch("factories.search_providers.time.sleep"):
            yield

    def test_happy_path_returns_search_results(self):
        # DDGS is imported lazily inside search():
        #   from ddgs import DDGS
        # Patch at the module level that owns it.
        import ddgs

        mock_ddgs_instance = MagicMock()
        mock_ddgs_instance.text.return_value = _DDGS_RESULTS
        ddgs.DDGS = MagicMock(return_value=mock_ddgs_instance)

        results = DuckDuckGoProvider().search("john_doe", max_results=2)

        assert len(results) == 2
        assert all(isinstance(r, SearchResult) for r in results)

    def test_result_mapping_from_ddgs_fields(self):
        """title←title, url←href, description←body."""
        import ddgs

        mock_ddgs = MagicMock()
        mock_ddgs.text.return_value = [_DDGS_RESULTS[0]]
        ddgs.DDGS = MagicMock(return_value=mock_ddgs)

        results = DuckDuckGoProvider().search("q")

        r = results[0]
        assert r.title == "DDG Title 1"
        assert r.url == "https://example.com/1"
        assert r.description == "Desc 1"
        assert r.source == "duckduckgo"

    def test_exception_returns_empty_list(self):
        import ddgs

        mock_ddgs = MagicMock()
        mock_ddgs.text.side_effect = RuntimeError("rate limited")
        ddgs.DDGS = MagicMock(return_value=mock_ddgs)

        results = DuckDuckGoProvider().search("q")

        assert results == []

    def test_exception_is_logged_as_warning(self):
        import ddgs

        mock_ddgs = MagicMock()
        mock_ddgs.text.side_effect = ConnectionError("no connection")
        ddgs.DDGS = MagicMock(return_value=mock_ddgs)

        with patch("factories.search_providers.logger") as mock_logger:
            DuckDuckGoProvider().search("q")

        mock_logger.warning.assert_called_once()
        assert "DuckDuckGo" in mock_logger.warning.call_args[0][0]

    def test_max_results_forwarded_to_ddgs(self):
        import ddgs

        mock_ddgs = MagicMock()
        mock_ddgs.text.return_value = []
        ddgs.DDGS = MagicMock(return_value=mock_ddgs)

        DuckDuckGoProvider().search("q", max_results=5)

        mock_ddgs.text.assert_called_once_with("q", max_results=5)

    def test_empty_results_returns_empty_list(self):
        import ddgs

        mock_ddgs = MagicMock()
        mock_ddgs.text.return_value = []
        ddgs.DDGS = MagicMock(return_value=mock_ddgs)

        results = DuckDuckGoProvider().search("q")

        assert results == []

    def test_missing_fields_use_defaults(self):
        """If ddgs returns a result with missing fields, use empty strings."""
        import ddgs

        mock_ddgs = MagicMock()
        mock_ddgs.text.return_value = [{}]
        ddgs.DDGS = MagicMock(return_value=mock_ddgs)

        results = DuckDuckGoProvider().search("q")

        r = results[0]
        assert r.title == ""
        assert r.url == ""
        assert r.description == ""


# ===========================================================================
# GoogleProvider
# ===========================================================================


class TestGoogleProvider:
    """Tests for GoogleProvider."""

    @pytest.fixture(autouse=True)
    def _no_sleep(self):
        with patch("factories.search_providers.time.sleep"):
            yield

    def test_happy_path_returns_search_results(self):
        # gsearch is imported inside the method as:
        # from googlesearch import search as gsearch
        # so we patch it on the googlesearch module directly
        import googlesearch

        googlesearch.search = MagicMock(return_value=iter(_GOOGLE_RESULTS))
        results = GoogleProvider().search("john_doe", max_results=2)

        assert len(results) == 2
        assert all(isinstance(r, SearchResult) for r in results)

    def test_result_mapping_from_googlesearch_objects(self):
        import googlesearch

        googlesearch.search = MagicMock(return_value=iter([_GOOGLE_RESULTS[0]]))
        results = GoogleProvider().search("q")

        r = results[0]
        assert r.title == "G Title 1"
        assert r.url == "https://google.com/1"
        assert r.description == "GD 1"
        assert r.source == "google"

    def test_exception_returns_empty_list(self):
        import googlesearch

        googlesearch.search = MagicMock(
            side_effect=Exception("HTTP 429 Too Many Requests")
        )
        results = GoogleProvider().search("q")

        assert results == []

    def test_exception_is_logged_as_warning(self):
        import googlesearch

        googlesearch.search = MagicMock(side_effect=Exception("blocked"))
        with patch("factories.search_providers.logger") as mock_logger:
            GoogleProvider().search("q")

        mock_logger.warning.assert_called_once()
        assert "Google" in mock_logger.warning.call_args[0][0]

    def test_none_attributes_become_empty_strings(self):
        """getattr fallback: None values → empty string."""
        import googlesearch

        obj = SimpleNamespace(title=None, url=None, description=None)
        googlesearch.search = MagicMock(return_value=iter([obj]))
        results = GoogleProvider().search("q")

        r = results[0]
        assert r.title == ""
        assert r.url == ""
        assert r.description == ""

    def test_search_with_dorks_returns_raw_node_list(self):
        """search_with_dorks must return list of dicts with dork/titles/links/descriptions."""
        import googlesearch

        dork_results = [
            SimpleNamespace(
                title="DorkTitle", url="https://github.com/user", description="DorkD"
            )
        ]
        googlesearch.search = MagicMock(return_value=iter(dork_results))
        nodes = GoogleProvider().search_with_dorks(
            "john_doe", dork_sites={"github": "site:github.com"}
        )

        assert isinstance(nodes, list)
        assert len(nodes) >= 1
        for node in nodes:
            assert "dork" in node
            assert "titles" in node
            assert "links" in node
            assert "descriptions" in node

    def test_search_with_dorks_plain_search_uses_username_dork(self):
        """Plain search results get dork='username'."""
        import googlesearch

        single = SimpleNamespace(title="T", url="https://x.com", description="D")
        googlesearch.search = MagicMock(return_value=iter([single]))
        nodes = GoogleProvider().search_with_dorks("q", dork_sites={})

        assert any(n["dork"] == "username" for n in nodes)

    def test_search_with_dorks_exception_skips_entry(self):
        """Exception in dork search logs warning but doesn't crash."""
        import googlesearch

        call_count = {"n": 0}

        def side_effect(*args, **kwargs):
            call_count["n"] += 1
            if call_count["n"] == 1:
                return iter([])  # plain search returns empty
            raise Exception("blocked")

        googlesearch.search = MagicMock(side_effect=side_effect)
        nodes = GoogleProvider().search_with_dorks(
            "q", dork_sites={"github": "site:github.com"}
        )

        # Should not raise; may return empty list or partial
        assert isinstance(nodes, list)


# ===========================================================================
# BraveSearchProvider
# ===========================================================================


class TestBraveSearchProvider:
    """Tests for BraveSearchProvider."""

    def _make_provider(self, api_key: str = "test-brave-key") -> BraveSearchProvider:
        return BraveSearchProvider(api_key=api_key)

    def _mock_response(self, status_code: int = 200, json_data: dict | None = None):
        mock_resp = MagicMock()
        mock_resp.status_code = status_code
        mock_resp.ok = status_code < 400
        mock_resp.json.return_value = (
            _BRAVE_RESPONSE if json_data is None else json_data
        )
        return mock_resp

    def test_happy_path_returns_search_results(self):
        provider = self._make_provider()

        with patch(
            "factories.search_providers.requests.get",
            return_value=self._mock_response(),
        ):
            results = provider.search("john_doe", max_results=2)

        assert len(results) == 2
        assert all(isinstance(r, SearchResult) for r in results)

    def test_result_mapping_from_brave_api(self):
        provider = self._make_provider()

        with patch(
            "factories.search_providers.requests.get",
            return_value=self._mock_response(
                json_data={
                    "web": {
                        "results": [
                            {
                                "title": "Brave T",
                                "url": "https://b.com",
                                "description": "Brave D",
                            }
                        ]
                    }
                }
            ),
        ):
            results = provider.search("q")

        r = results[0]
        assert r.title == "Brave T"
        assert r.url == "https://b.com"
        assert r.description == "Brave D"
        assert r.source == "brave"

    def test_api_key_sent_as_x_subscription_token_header(self):
        provider = self._make_provider(api_key="MY-SECRET-KEY")

        with patch(
            "factories.search_providers.requests.get",
            return_value=self._mock_response(),
        ) as mock_get:
            provider.search("q")

        call_kwargs = mock_get.call_args[1]
        assert call_kwargs["headers"]["X-Subscription-Token"] == "MY-SECRET-KEY"

    def test_401_returns_empty_list_and_logs_warning(self):
        provider = self._make_provider()

        with (
            patch(
                "factories.search_providers.requests.get",
                return_value=self._mock_response(status_code=401),
            ),
            patch("factories.search_providers.logger") as mock_logger,
        ):
            results = provider.search("q")

        assert results == []
        mock_logger.warning.assert_called()
        log_msg = mock_logger.warning.call_args[0][0]
        assert "401" in log_msg or "invalid API key" in log_msg.lower()

    def test_429_returns_empty_list_and_logs_warning(self):
        provider = self._make_provider()

        with (
            patch(
                "factories.search_providers.requests.get",
                return_value=self._mock_response(status_code=429),
            ),
            patch("factories.search_providers.logger") as mock_logger,
        ):
            results = provider.search("q")

        assert results == []
        mock_logger.warning.assert_called()
        log_msg = mock_logger.warning.call_args[0][0]
        assert "429" in log_msg or "rate limited" in log_msg.lower()

    def test_network_error_returns_empty_list(self):
        provider = self._make_provider()

        with patch(
            "factories.search_providers.requests.get",
            side_effect=ConnectionError("no route to host"),
        ):
            results = provider.search("q")

        assert results == []

    def test_network_error_is_logged(self):
        provider = self._make_provider()

        with (
            patch(
                "factories.search_providers.requests.get",
                side_effect=OSError("timeout"),
            ),
            patch("factories.search_providers.logger") as mock_logger,
        ):
            provider.search("q")

        mock_logger.warning.assert_called()
        assert "Brave" in mock_logger.warning.call_args[0][0]

    def test_non_ok_status_returns_empty_list(self):
        provider = self._make_provider()

        with patch(
            "factories.search_providers.requests.get",
            return_value=self._mock_response(status_code=500),
        ):
            results = provider.search("q")

        assert results == []

    def test_empty_web_results_returns_empty_list(self):
        provider = self._make_provider()
        empty_response = {"web": {"results": []}}

        with patch(
            "factories.search_providers.requests.get",
            return_value=self._mock_response(json_data=empty_response),
        ):
            results = provider.search("q")

        assert results == []

    def test_missing_web_key_returns_empty_list(self):
        provider = self._make_provider()

        with patch(
            "factories.search_providers.requests.get",
            return_value=self._mock_response(json_data={}),
        ):
            results = provider.search("q")

        assert results == []

    def test_search_with_dorks_returns_node_list(self):
        provider = self._make_provider()

        with patch(
            "factories.search_providers.requests.get",
            return_value=self._mock_response(),
        ):
            nodes = provider.search_with_dorks(
                "john_doe", dork_sites={"github": "site:github.com"}
            )

        assert isinstance(nodes, list)
        for node in nodes:
            assert "dork" in node
            assert "titles" in node
            assert "links" in node
            assert "descriptions" in node

    def test_search_with_dorks_plain_search_tagged_as_username(self):
        provider = self._make_provider()

        with patch(
            "factories.search_providers.requests.get",
            return_value=self._mock_response(),
        ):
            nodes = provider.search_with_dorks("q", dork_sites={})

        username_nodes = [n for n in nodes if n["dork"] == "username"]
        assert len(username_nodes) > 0


# ===========================================================================
# DeprecatedProvider
# ===========================================================================


class TestDeprecatedProvider:
    """Tests for DeprecatedProvider stub."""

    def test_returns_empty_list(self):
        provider = DeprecatedProvider(name="yahoo", icon="fab fa-yahoo")
        results = provider.search("john_doe")
        assert results == []

    def test_returns_empty_list_for_any_query(self):
        provider = DeprecatedProvider(name="baidu", icon="fas fa-paw")
        assert provider.search("") == []
        assert provider.search("anything") == []
        assert provider.search("test", max_results=100) == []

    def test_logs_deprecation_warning_with_engine_name(self):
        engine_name = "yandex"
        provider = DeprecatedProvider(
            name=engine_name, icon="fab fa-yandex-international"
        )

        with patch("factories.search_providers.logger") as mock_logger:
            provider.search("q")

        mock_logger.warning.assert_called_once()
        warn_args = mock_logger.warning.call_args[0]
        # The warning must include the engine name somewhere
        formatted_msg = warn_args[0] % warn_args[1:]
        assert engine_name in formatted_msg

    def test_preserves_name_attribute(self):
        provider = DeprecatedProvider(name="bing", icon="fab fa-windows")
        assert provider.name == "bing"

    def test_preserves_icon_attribute(self):
        provider = DeprecatedProvider(name="bing", icon="fab fa-windows")
        assert provider.icon == "fab fa-windows"


# ===========================================================================
# SearchResult dataclass contract
# ===========================================================================


class TestSearchResultContract:
    """Verify SearchResult structure stays backward-compatible."""

    def test_has_title_url_description_source(self):
        r = SearchResult(
            title="Title", url="https://x.com", description="Desc", source="google"
        )
        assert r.title == "Title"
        assert r.url == "https://x.com"
        assert r.description == "Desc"
        assert r.source == "google"

    def test_is_dataclass_with_dict_support(self):
        """Dataclass instances can be serialised via __dict__."""
        r = SearchResult(title="T", url="U", description="D", source="S")
        d = r.__dict__
        assert set(d.keys()) == {"title", "url", "description", "source"}
