#!/usr/bin/env python
#
# Dark web search aggregation for iKy.
#
# The search-engine core (concurrent requests + BeautifulSoup parsing over
# multiple .onion search providers) is adapted from robin:
#   Upstream: https://github.com/apurvsinghgautam/robin  (MIT License)
# The LLM / NLP / deep-scraping layers of robin are intentionally NOT ported;
# this module aggregates search-result links only (filtered by default).
#
# ----------------------------------------------------------------------------
# MIT License
#
# Copyright (c) Apurv Singh Gautam and robin contributors
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# ----------------------------------------------------------------------------

import argparse
import json
import os
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from urllib.parse import quote

import requests

# urllib3 warning suppression kept intentionally: TOR .onion hidden services
# use self-signed certificates, so verify=False is expected when routing
# through a SOCKS proxy to the Tor network.
import urllib3
from bs4 import BeautifulSoup
from celery.utils.log import get_task_logger
from factories.task_wrapper import iky_task

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = get_task_logger(__name__)

# Proxy is deployment config (not an API key). socks5h is mandatory so DNS
# resolution for .onion hostnames happens through Tor, not locally.
TOR_PROXY_URL = os.getenv("TOR_PROXY_URL", "socks5h://tor:9050")

PER_ENGINE_TIMEOUT = 35  # seconds per engine (spec R6: 30-40s)
TOTAL_TIMEOUT = 120  # seconds hard wall-clock budget for the whole task
MAX_WORKERS = 3

USER_AGENTS = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36",
)


@dataclass(frozen=True)
class EngineConfig:
    """Static configuration for a single dark web search engine."""

    name: str
    url: str
    filtered: bool
    requires_tor: bool
    parser: str


@dataclass(frozen=True)
class EngineResult:
    """Outcome of querying one engine.

    ``available`` means the engine responded successfully (HTTP 200 without a
    CAPTCHA challenge), even if it produced zero parseable hits.
    """

    engine: str
    filtered: bool
    available: bool
    hits: list[dict]


# v1 engine set. Filtered (Ahmia) runs by default; the unfiltered engines are
# opt-in only. NoEvil is intentionally omitted: no live endpoint could be
# verified, and shipping a dead default URL is worse than fewer engines.
ENGINES: tuple[EngineConfig, ...] = (
    EngineConfig(
        name="Ahmia",
        url="https://ahmia.fi/search/?q={query}",
        filtered=True,
        requires_tor=False,
        parser="ahmia",
    ),
    EngineConfig(
        name="AhmiaOnion",
        url=(
            "http://juhanurmihxlp77nkq76byazcldy2hlmovfu2epvl5ankdibsot4csyd.onion"
            "/search/?q={query}"
        ),
        filtered=True,
        requires_tor=True,
        parser="generic_onion",
    ),
    EngineConfig(
        name="OnionLand",
        url=(
            "http://3bbad7fauom4d6sgppalyqddsqbf5u5p56b5k5uk2zxsy3d6ey2jobad.onion"
            "/search?q={query}"
        ),
        filtered=False,
        requires_tor=True,
        parser="generic_onion",
    ),
    EngineConfig(
        name="Tor66",
        url=(
            "http://tor66sewebgixwhcqfnp5inzp5x5uohhdy3kvtnyfxc2e5mxiuh34iid.onion"
            "/search?q={query}"
        ),
        filtered=False,
        requires_tor=True,
        parser="generic_onion",
    ),
)


# ---------------------------------------------------------------------------
# Tor / clearnet sessions
# ---------------------------------------------------------------------------


def _build_tor_session() -> requests.Session:
    """Build a requests session routed through the Tor SOCKS5 proxy."""
    session = requests.Session()
    session.proxies = {"http": TOR_PROXY_URL, "https": TOR_PROXY_URL}
    return session


def _build_clearnet_session() -> requests.Session:
    """Build a plain requests session for clearnet engines (e.g. Ahmia)."""
    return requests.Session()


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


def _parse_ahmia(soup: BeautifulSoup) -> list[dict]:
    """Parse Ahmia's ``li.result`` rows into title/onion-link pairs."""
    hits: list[dict] = []
    for item in soup.select("li.result"):
        heading = item.find("h4")
        cite = item.find("cite")
        title = heading.get_text(strip=True) if heading else ""
        link = cite.get_text(strip=True) if cite else ""
        if title and link:
            hits.append({"title": title, "link": link})
    return hits


def _parse_generic_onion(soup: BeautifulSoup) -> list[dict]:
    """Extract unique anchors pointing at ``.onion`` hosts."""
    hits: list[dict] = []
    seen: set[str] = set()
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"]
        if ".onion" not in href or href in seen:
            continue
        seen.add(href)
        title = anchor.get_text(strip=True) or href
        hits.append({"title": title, "link": href})
    return hits


def _parse_results(parser: str, html: str) -> list[dict]:
    """Dispatch to the parser named in the engine config."""
    soup = BeautifulSoup(html, "html.parser")
    if parser == "ahmia":
        return _parse_ahmia(soup)
    return _parse_generic_onion(soup)


def _is_captcha(text: str) -> bool:
    """Detect a CAPTCHA challenge in an engine response body."""
    return "captcha" in text.lower()


# ---------------------------------------------------------------------------
# Fetching
# ---------------------------------------------------------------------------


def _select_engines(include_unfiltered: bool) -> list[EngineConfig]:
    """Return filtered engines by default; add unfiltered ones on opt-in."""
    if include_unfiltered:
        return list(ENGINES)
    return [engine for engine in ENGINES if engine.filtered]


def _fetch_engine(
    engine: EngineConfig,
    query: str,
    tor_session: requests.Session,
    clearnet_session: requests.Session,
) -> EngineResult:
    """Query a single engine, degrading gracefully on any failure.

    CAPTCHA, HTTP 429, any non-200 status, connection errors, and timeouts all
    yield zero results for this engine without raising; no retry is attempted.
    Malformed but successful (HTTP 200) responses count as available with zero
    hits so they do not poison the overall validation badge.
    """
    session = tor_session if engine.requires_tor else clearnet_session
    url = engine.url.format(query=quote(query, safe="@._-"))
    # .onion endpoints serve self-signed certs over the Tor SOCKS proxy, so
    # verify=False is expected there; clearnet engines verify TLS normally.
    verify = not engine.requires_tor
    try:
        resp = session.get(
            url,
            headers={"User-Agent": random.choice(USER_AGENTS)},
            timeout=PER_ENGINE_TIMEOUT,
            verify=verify,
        )
    except Exception:
        logger.warning("Darkweb - engine %s request failed", engine.name)
        return EngineResult(engine.name, engine.filtered, False, [])

    if resp.status_code != 200:
        logger.warning(
            "Darkweb - engine %s returned HTTP %s", engine.name, resp.status_code
        )
        return EngineResult(engine.name, engine.filtered, False, [])

    text = resp.text or ""
    if _is_captcha(text):
        logger.warning("Darkweb - engine %s served a CAPTCHA", engine.name)
        return EngineResult(engine.name, engine.filtered, False, [])

    hits = _parse_results(engine.parser, text)
    return EngineResult(engine.name, engine.filtered, True, hits)


# ---------------------------------------------------------------------------
# Output normalization
# ---------------------------------------------------------------------------

_ROOT_DARKWEB = {
    "name-node": "DarkWeb",
    "title": "Dark Web",
    "subtitle": "",
    "icon": "fas fa-spider",
    "link": "DarkWeb",
}
_ROOT_UNFILTERED = {
    "name-node": "DarkWebUnfiltered",
    "title": "Dark Web (Unfiltered)",
    "subtitle": "",
    "icon": "fas fa-spider",
    "link": "DarkWebUnfiltered",
}


def _normalize(
    results: list[EngineResult], include_unfiltered: bool
) -> tuple[list[dict], list[dict]]:
    """Build the ``raw`` list and the ``graphic`` sections from engine results."""
    filtered_hits: list[dict] = []
    unfiltered_hits: list[dict] = []
    for result in results:
        bucket = filtered_hits if result.filtered else unfiltered_hits
        for hit in result.hits:
            bucket.append(
                {
                    "title": hit["title"],
                    "link": hit["link"],
                    "engine": result.engine,
                    "filtered": result.filtered,
                }
            )

    raw = filtered_hits + unfiltered_hits

    darkweb_nodes = [dict(_ROOT_DARKWEB)]
    for idx, hit in enumerate(filtered_hits):
        darkweb_nodes.append(
            {
                "name-node": f"DW-{idx}",
                "title": hit["title"],
                "subtitle": hit["link"],
                "icon": "fas fa-spider",
                "link": "DarkWeb",
            }
        )
    graphic: list[dict] = [{"darkweb": darkweb_nodes}]

    if include_unfiltered:
        unfiltered_nodes = [dict(_ROOT_UNFILTERED)]
        for idx, hit in enumerate(unfiltered_hits):
            unfiltered_nodes.append(
                {
                    "name-node": f"DWU-{idx}",
                    "title": hit["title"],
                    "subtitle": hit["link"],
                    "icon": "fas fa-spider",
                    "link": "DarkWebUnfiltered",
                }
            )
        graphic.append({"darkweb_unfiltered": unfiltered_nodes})

    return raw, graphic


# ---------------------------------------------------------------------------
# Main processing function
# ---------------------------------------------------------------------------


@iky_task(module_name="darkweb", dev_mode_sleep=5)
def p_darkweb(param, include_unfiltered=False):
    """Aggregate dark web search results for an email or username via Tor."""
    query = (param or "").strip()
    if not query:
        raise Exception("iKy - Empty search parameter")

    tor_session = _build_tor_session()
    clearnet_session = _build_clearnet_session()
    engines = _select_engines(include_unfiltered)

    results: list[EngineResult] = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(
                _fetch_engine, engine, query, tor_session, clearnet_session
            ): engine
            for engine in engines
        }
        try:
            for future in as_completed(futures, timeout=TOTAL_TIMEOUT):
                engine = futures[future]
                try:
                    results.append(future.result())
                except Exception:
                    logger.warning("Darkweb - engine %s crashed", engine.name)
                    results.append(
                        EngineResult(engine.name, engine.filtered, False, [])
                    )
        except TimeoutError:
            for future, engine in futures.items():
                if not future.done():
                    future.cancel()
                    results.append(
                        EngineResult(engine.name, engine.filtered, False, [])
                    )

    raw, graphic = _normalize(results, include_unfiltered)
    validation = "hard" if any(result.available for result in results) else "no"

    total = []
    total.append({"module": "darkweb"})
    total.append({"param": query})
    total.append({"validation": validation})
    total.append({"raw": raw})
    total.append({"graphic": graphic})
    total.append({"profile": []})
    total.append({"timeline": []})

    return total


# Backward-compatible alias: registry / Celery reference t_darkweb
t_darkweb = p_darkweb


def output(data):
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Search dark web engines for an email or username"
    )
    parser.add_argument("target", help="Email or username to search")
    parser.add_argument(
        "--unfiltered",
        action="store_true",
        help="Include unfiltered engines (explicit opt-in)",
    )
    args = parser.parse_args()

    result = t_darkweb(args.target, include_unfiltered=args.unfiltered, dev_mode=False)
    output(result)
