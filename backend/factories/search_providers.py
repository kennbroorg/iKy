"""Search provider abstraction for iKy search subsystem.

Each provider wraps a search engine and returns a uniform list of
SearchResult dataclass instances:
    SearchResult(title, url, description, source)

Scraper-based providers (Google, Yahoo, Bing, DuckDuckGo, Yandex, Baidu)
all inherit from _ScraperProvider which handles the shared parse logic,
since search_engine_parser returns the same dict format for all engines.

API/scraping-fallback providers (GoogleCSEProvider, YagoogleProvider) are
implemented separately because they use different third-party libraries.
"""

from __future__ import annotations

import contextlib
import logging
import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from shutil import rmtree

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Uniform search result from any provider."""

    title: str
    url: str
    description: str
    source: str  # provider name e.g. "google", "bing"


class SearchProvider(ABC):
    """Base class for all search providers."""

    name: str  # e.g. "google", "bing"
    icon: str  # FontAwesome icon e.g. "fab fa-google"

    @abstractmethod
    def search(self, query: str, max_results: int = 10) -> list[SearchResult]:
        """Execute search and return uniform results."""
        ...


# ---------------------------------------------------------------------------
# Shared base for search_engine_parser-backed providers
# ---------------------------------------------------------------------------


class _ScraperProvider(SearchProvider):
    """Mixin for providers backed by search_engine_parser.

    Subclasses only need to define ``name``, ``icon``, and ``_engine_cls``.
    The search + parse logic is identical across all scraper engines.
    """

    _engine_cls: type  # set by each concrete subclass

    def search(self, query: str, max_results: int = 10) -> list[SearchResult]:
        with contextlib.suppress(Exception):
            rmtree("cache")

        engine = self._engine_cls()
        try:
            engine.clear_cache()
            raw = engine.search(query, 1, cache=False)
        except Exception:
            logger.warning("Scraper provider %s failed for query %r", self.name, query)
            return []

        return self._parse(raw)

    def _parse(self, raw: dict | None) -> list[SearchResult]:
        if not raw:
            return []
        results: list[SearchResult] = []
        titles = raw.get("titles", [])
        links = raw.get("links", [])
        descriptions = raw.get("descriptions", [])
        for i in range(len(titles)):
            try:
                results.append(
                    SearchResult(
                        title=titles[i],
                        url=links[i],
                        description=descriptions[i],
                        source=self.name,
                    )
                )
            except (IndexError, KeyError):
                continue
        return results


# ---------------------------------------------------------------------------
# Concrete scraper providers
# ---------------------------------------------------------------------------


class GoogleScraperProvider(_ScraperProvider):
    name = "google"
    icon = "fab fa-google"

    @property
    def _engine_cls(self):  # type: ignore[override]
        from search_engine_parser.core.engines.google import (
            Search as GoogleSearch,
        )

        return GoogleSearch


class YahooProvider(_ScraperProvider):
    name = "yahoo"
    icon = "fab fa-yahoo"

    @property
    def _engine_cls(self):  # type: ignore[override]
        from search_engine_parser.core.engines.yahoo import (
            Search as YahooSearch,
        )

        return YahooSearch


class BingProvider(_ScraperProvider):
    name = "bing"
    icon = "fab fa-windows"

    @property
    def _engine_cls(self):  # type: ignore[override]
        from search_engine_parser.core.engines.bing import Search as BingSearch

        return BingSearch


class DuckDuckGoProvider(_ScraperProvider):
    name = "duckduckgo"
    icon = "fas fa-kiwi-bird"

    @property
    def _engine_cls(self):  # type: ignore[override]
        from search_engine_parser.core.engines.duckduckgo import (
            Search as DuckDuckGoSearch,
        )

        return DuckDuckGoSearch


class YandexProvider(_ScraperProvider):
    name = "yandex"
    icon = "fab fa-yandex-international"

    @property
    def _engine_cls(self):  # type: ignore[override]
        from search_engine_parser.core.engines.yandex import (
            Search as YandexSearch,
        )

        return YandexSearch


class BaiduProvider(_ScraperProvider):
    name = "baidu"
    icon = "fas fa-paw"

    @property
    def _engine_cls(self):  # type: ignore[override]
        from search_engine_parser.core.engines.baidu import (
            Search as BaiduSearch,
        )

        return BaiduSearch


# ---------------------------------------------------------------------------
# Google Custom Search Engine (API-based)
# ---------------------------------------------------------------------------

# Dork site-filters; same dict used by dorks_tasks.py
DORK_SITES: dict[str, str] = {
    "twitter": "site:twitter.com",
    "github": "site:github.com",
    "instagram": "site:instagram.com",
    "keybase": "site:keybase.io",
    "linkedin": "site:linkedin.com",
    # "facebook": "site:facebook.com",
    # "pinterest": "site:pinterest.com",
    "tiktok": "site:tiktok.com",
}


class GoogleCSEProvider(SearchProvider):
    """Google Custom Search Engine provider (requires API key + CX)."""

    name = "google_cse"
    icon = "fab fa-google"

    def __init__(self, api_key: str, cx: str) -> None:
        self.api_key = api_key
        self.cx = cx

    def search(self, query: str, max_results: int = 10) -> list[SearchResult]:
        from googleapiclient.discovery import build

        try:
            resource = build("customsearch", "v1", developerKey=self.api_key).cse()
            result = resource.list(q=query, cx=self.cx).execute()
        except Exception:
            logger.warning("GoogleCSEProvider failed for query %r", query)
            return []

        results: list[SearchResult] = []
        for item in result.get("items", []):
            results.append(
                SearchResult(
                    title=item.get("title", ""),
                    url=item.get("link", ""),
                    description=item.get("snippet", ""),
                    source=self.name,
                )
            )
        return results

    def search_with_dorks(
        self,
        query: str,
        dork_sites: dict[str, str] | None = None,
    ) -> list[dict]:
        """Search query + each dork, returning raw dork-tagged node list.

        Returns a list of dicts compatible with the legacy ``raw_node``
        format expected by dorks_tasks post-processing:
            {"dork": str, "titles": str, "links": str, "descriptions": str}
        """
        from googleapiclient.discovery import build

        if dork_sites is None:
            dork_sites = DORK_SITES

        node: list[dict] = []
        try:
            resource = build("customsearch", "v1", developerKey=self.api_key).cse()

            # Plain search first
            result = resource.list(q=query, cx=self.cx).execute()
            for item in result.get("items", []):
                node.append(
                    {
                        "dork": "username",
                        "titles": item["title"],
                        "links": item["link"],
                        "descriptions": item["snippet"],
                    }
                )

            # Dork searches
            for dork, site_filter in dork_sites.items():
                time.sleep(random.randrange(5, 15))
                dork_query = f"{query} {site_filter}"
                try:
                    result = resource.list(q=dork_query, cx=self.cx).execute()
                except Exception:
                    continue
                if "items" in result:
                    item = result["items"][0]
                    node.append(
                        {
                            "dork": dork,
                            "titles": item["title"],
                            "links": item["link"],
                            "descriptions": item["snippet"],
                        }
                    )
        except Exception:
            logger.warning("GoogleCSEProvider.search_with_dorks failed for %r", query)

        return node


# ---------------------------------------------------------------------------
# Yagooglesearch (scraping fallback)
# ---------------------------------------------------------------------------


class YagoogleProvider(SearchProvider):
    """Google scraping via yagooglesearch (rate-limit aware fallback)."""

    name = "yagoogle"
    icon = "fab fa-google"

    def search(self, query: str, max_results: int = 10) -> list[SearchResult]:
        import yagooglesearch

        try:
            client = yagooglesearch.SearchClient(
                query,
                tbs="li:1",
                max_search_result_urls_to_return=max_results,
                http_429_cool_off_time_in_minutes=1,
                http_429_cool_off_factor=1.5,
                verbosity=5,
                verbose_output=True,
                verify_ssl=False,
            )
            client.assign_random_user_agent()
            raw = client.search()
        except Exception:
            logger.warning("YagoogleProvider failed for query %r", query)
            return []

        return [
            SearchResult(
                title=u.get("title", ""),
                url=u.get("url", ""),
                description=u.get("description", ""),
                source=self.name,
            )
            for u in raw
        ]

    def search_with_dorks(
        self,
        query: str,
        dork_sites: dict[str, str] | None = None,
    ) -> list[dict]:
        """Search query + each dork, returning raw dork-tagged node list.

        Returns a list of dicts compatible with the legacy ``raw_node``
        format expected by dorks_tasks post-processing:
            {"dork": str, "titles": str, "links": str, "descriptions": str}
        """
        import yagooglesearch

        if dork_sites is None:
            dork_sites = DORK_SITES

        node: list[dict] = []

        try:
            client = yagooglesearch.SearchClient(
                query,
                tbs="li:1",
                max_search_result_urls_to_return=10,
                http_429_cool_off_time_in_minutes=1,
                http_429_cool_off_factor=1.5,
                verbosity=5,
                verbose_output=True,
                verify_ssl=False,
            )
            client.assign_random_user_agent()
            for u in client.search():
                node.append(
                    {
                        "dork": "username",
                        "titles": u.get("title", ""),
                        "links": u.get("url", ""),
                        "descriptions": u.get("description", ""),
                    }
                )
        except Exception:
            logger.warning("YagoogleProvider plain search failed for %r", query)

        for dork, site_filter in dork_sites.items():
            time.sleep(random.randrange(0, 15))
            dork_query = f"{query} {site_filter}"
            try:
                client = yagooglesearch.SearchClient(
                    dork_query,
                    max_search_result_urls_to_return=1,
                    http_429_cool_off_time_in_minutes=45,
                    http_429_cool_off_factor=1.5,
                    verbosity=0,
                    verbose_output=True,
                )
                client.assign_random_user_agent()
                for u in client.search():
                    node.append(
                        {
                            "dork": dork,
                            "titles": u.get("title", ""),
                            "links": u.get("url", ""),
                            "descriptions": u.get("description", ""),
                        }
                    )
            except Exception:
                logger.warning(
                    "YagoogleProvider dork search failed for %r / %s",
                    query,
                    dork,
                )
                continue

        return node
