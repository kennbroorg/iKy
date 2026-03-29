"""Search provider abstraction for iKy search subsystem.

Each provider wraps a search engine and returns a uniform list of
SearchResult dataclass instances:
    SearchResult(title, url, description, source)

Providers:
- DuckDuckGoProvider: uses duckduckgo-search (ddgs) library, no API key needed
- GoogleProvider: uses googlesearch-python library, no API key needed
- BraveSearchProvider: uses Brave Search REST API, requires API key
- GoogleCSEProvider: Google Custom Search Engine, requires API key + CX
- DeprecatedProvider: stub for removed engines (Yahoo, Bing, Yandex, Baidu)
"""

from __future__ import annotations

import logging
import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass

import requests

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Uniform search result from any provider."""

    title: str
    url: str
    description: str
    source: str  # provider name e.g. "google", "duckduckgo"


class SearchProvider(ABC):
    """Base class for all search providers."""

    name: str  # e.g. "google", "duckduckgo"
    icon: str  # FontAwesome icon e.g. "fab fa-google"

    @abstractmethod
    def search(self, query: str, max_results: int = 10) -> list[SearchResult]:
        """Execute search and return uniform results."""
        ...


# ---------------------------------------------------------------------------
# Dork site-filters; same dict used by dorks_tasks.py
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# DuckDuckGo provider (duckduckgo-search library)
# ---------------------------------------------------------------------------


class DuckDuckGoProvider(SearchProvider):
    """DuckDuckGo search via the duckduckgo-search (ddgs) library.

    No API key required. Applies rate-limit delay between calls.
    """

    name = "duckduckgo"
    icon = "fas fa-kiwi-bird"

    def search(self, query: str, max_results: int = 10) -> list[SearchResult]:
        from duckduckgo_search import DDGS

        time.sleep(random.uniform(0.5, 1.5))
        try:
            results = DDGS().text(query, max_results=max_results)
        except Exception:
            logger.warning(
                "DuckDuckGoProvider failed for query %r",
                query,
                exc_info=True,
            )
            return []

        return [
            SearchResult(
                title=r.get("title", ""),
                url=r.get("href", ""),
                description=r.get("body", ""),
                source=self.name,
            )
            for r in results
        ]


# ---------------------------------------------------------------------------
# Google provider (googlesearch-python library)
# ---------------------------------------------------------------------------


class GoogleProvider(SearchProvider):
    """Google scraping via googlesearch-python.

    No API key required. Uses advanced=True for title/url/description.
    Applies rate-limit delay between calls.
    """

    name = "google"
    icon = "fab fa-google"

    def search(self, query: str, max_results: int = 10) -> list[SearchResult]:
        from googlesearch import search as gsearch

        time.sleep(random.uniform(1, 3))
        try:
            raw = list(gsearch(query, num_results=max_results, advanced=True))
        except Exception:
            logger.warning(
                "GoogleProvider failed for query %r",
                query,
                exc_info=True,
            )
            return []

        return [
            SearchResult(
                title=getattr(r, "title", "") or "",
                url=getattr(r, "url", "") or "",
                description=getattr(r, "description", "") or "",
                source=self.name,
            )
            for r in raw
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
        from googlesearch import search as gsearch

        if dork_sites is None:
            dork_sites = DORK_SITES

        node: list[dict] = []

        # Plain search first
        time.sleep(random.uniform(1, 3))
        try:
            for r in gsearch(query, num_results=10, advanced=True):
                node.append(
                    {
                        "dork": "username",
                        "titles": getattr(r, "title", "") or "",
                        "links": getattr(r, "url", "") or "",
                        "descriptions": getattr(r, "description", "") or "",
                    }
                )
        except Exception:
            logger.warning(
                "GoogleProvider plain search failed for %r",
                query,
                exc_info=True,
            )

        # Dork searches
        for dork, site_filter in dork_sites.items():
            time.sleep(random.uniform(1, 3))
            dork_query = f"{query} {site_filter}"
            try:
                results = list(gsearch(dork_query, num_results=1, advanced=True))
            except Exception:
                logger.warning(
                    "GoogleProvider dork search failed for %r / %s",
                    query,
                    dork,
                )
                continue

            if results:
                r = results[0]
                node.append(
                    {
                        "dork": dork,
                        "titles": getattr(r, "title", "") or "",
                        "links": getattr(r, "url", "") or "",
                        "descriptions": getattr(r, "description", "") or "",
                    }
                )

        return node


# ---------------------------------------------------------------------------
# Brave Search provider (REST API)
# ---------------------------------------------------------------------------


class BraveSearchProvider(SearchProvider):
    """Brave Search via official REST API.

    Requires a Brave Search API key stored as ``brave_key`` in apikeys.json.
    Only instantiate when the key is non-empty.
    """

    name = "brave"
    icon = "fas fa-shield-alt"
    _endpoint = "https://api.search.brave.com/res/v1/web/search"

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key

    def search(self, query: str, max_results: int = 10) -> list[SearchResult]:
        headers = {
            "X-Subscription-Token": self.api_key,
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
        }
        params = {"q": query, "count": min(max_results, 20)}

        try:
            resp = requests.get(
                self._endpoint,
                headers=headers,
                params=params,
                timeout=10,
            )
        except Exception:
            logger.warning(
                "BraveSearchProvider network error for query %r",
                query,
                exc_info=True,
            )
            return []

        if resp.status_code == 401:
            logger.warning(
                "BraveSearchProvider: invalid API key (401) for query %r",
                query,
            )
            return []
        if resp.status_code == 422:
            # Brave returns 422 for invalid/expired subscription tokens
            # (SUBSCRIPTION_TOKEN_INVALID), not for bad query params.
            error_code = resp.json().get("error", {}).get("code", "unknown")
            logger.warning(
                "BraveSearchProvider: HTTP 422 (%s) for query %r — "
                "check that brave_key in apikeys.json is valid",
                error_code,
                query,
            )
            return []
        if resp.status_code == 429:
            logger.warning(
                "BraveSearchProvider: rate limited (429) for query %r",
                query,
            )
            return []
        if not resp.ok:
            logger.warning(
                "BraveSearchProvider: HTTP %s for query %r",
                resp.status_code,
                query,
            )
            return []

        data = resp.json()
        return [
            SearchResult(
                title=r.get("title", ""),
                url=r.get("url", ""),
                description=r.get("description", ""),
                source=self.name,
            )
            for r in data.get("web", {}).get("results", [])
        ]

    def search_with_dorks(
        self,
        query: str,
        dork_sites: dict[str, str] | None = None,
    ) -> list[dict]:
        """Search query + each dork via Brave API, returning raw dork-tagged nodes.

        Returns a list of dicts compatible with the legacy ``raw_node``
        format expected by dorks_tasks post-processing:
            {"dork": str, "titles": str, "links": str, "descriptions": str}
        """
        if dork_sites is None:
            dork_sites = DORK_SITES

        node: list[dict] = []

        # Plain search first
        plain_results = self.search(query)
        for r in plain_results:
            node.append(
                {
                    "dork": "username",
                    "titles": r.title,
                    "links": r.url,
                    "descriptions": r.description,
                }
            )

        # Dork searches
        for dork, site_filter in dork_sites.items():
            dork_query = f"{query} {site_filter}"
            results = self.search(dork_query, max_results=1)
            if results:
                r = results[0]
                node.append(
                    {
                        "dork": dork,
                        "titles": r.title,
                        "links": r.url,
                        "descriptions": r.description,
                    }
                )

        return node


# ---------------------------------------------------------------------------
# Google Custom Search Engine (API-based)
# ---------------------------------------------------------------------------


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
# Deprecated provider stub
# ---------------------------------------------------------------------------


class DeprecatedProvider(SearchProvider):
    """Stub for removed search engines.

    Logs a deprecation warning and returns an empty result list.
    Used to maintain backward-compatible provider name/icon metadata
    without executing any actual search.
    """

    def __init__(self, name: str, icon: str) -> None:
        self.name = name
        self.icon = icon

    def search(self, query: str, max_results: int = 10) -> list[SearchResult]:
        logger.warning(
            "Provider %s is deprecated and returns no results",
            self.name,
        )
        return []
