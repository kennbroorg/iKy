#!/usr/bin/env python
#
# Dark web search aggregation for iKy.
#
# The search-engine core (concurrent requests + BeautifulSoup parsing over
# multiple .onion search providers) is adapted from robin:
#   Upstream: https://github.com/apurvsinghgautam/robin  (MIT License)
# The LLM / NLP / deep-scraping layers of robin are intentionally NOT ported;
# this module aggregates search-result links only.
#
# NOTE on filtering: a live engine spike (sdd/dark-web/engine-spike) proved that
# the only candidate "filtered" engine (Ahmia) now blocks all scraping. There is
# currently NO scrapable filtered engine, so this module is UNFILTERED-ONLY: it
# queries the two engines that actually return data over Tor (Tor66 + OnionLand).
# Responsible-use is enforced by the consuming UI disclaimer, not an engine tier.
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

# Loosened after the live spike: cold Tor circuits to these engines can take
# several seconds, and OnionLand returns large (~170KB) pages.
PER_ENGINE_TIMEOUT = 45  # seconds per engine
TOTAL_TIMEOUT = 180  # seconds hard wall-clock budget for the whole task
MAX_WORKERS = 2

USER_AGENTS = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36",
)

# Tor66 navigation/menu links share the engine's own host or point at site
# chrome (random/fresh/submit/...). They are not search hits, so the parser
# drops any anchor whose href or text contains one of these tokens.
_TOR66_NAV_TOKENS = (
    "tor66",
    "random",
    "fresh",
    "serviceinfo",
    "top_onions",
    "submit",
    "advertise",
    "about",
)


@dataclass(frozen=True)
class EngineConfig:
    """Static configuration for a single dark web search engine.

    ``fetch_method`` is RESERVED for future fetchers (e.g. ``"playwright"``).
    Every v1 engine uses ``"requests"``; the spike confirmed Playwright did not
    unblock any additional engine, so no other method is wired yet.
    """

    name: str
    url: str
    filtered: bool
    requires_tor: bool
    parser: str
    fetch_method: str = "requests"


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


# v1 engine set. Both engines are unfiltered and verified live (engine spike):
# they are the only two that actually return scrapable .onion results over Tor.
# Ahmia (the former "filtered" default), Torch, Haystak, DuckDuckGo onion and
# Phobos were all dropped — dead, unreachable, or serving a JS/anti-bot shell.
ENGINES: tuple[EngineConfig, ...] = (
    EngineConfig(
        name="Tor66",
        url=(
            "http://tor66sewebgixwhcqfnp5inzp5x5uohhdy3kvtnyfxc2e5mxiuh34iid.onion"
            "/search?q={query}"
        ),
        filtered=False,
        requires_tor=True,
        parser="tor66",
        fetch_method="requests",
    ),
    EngineConfig(
        name="OnionLand",
        url=(
            "http://3bbad7fauom4d6sgppalyqddsqbf5u5p56b5k5uk2zxsy3d6ey2jobad.onion"
            "/search?q={query}"
        ),
        filtered=False,
        requires_tor=True,
        parser="onionland",
        fetch_method="requests",
    ),
)


# ---------------------------------------------------------------------------
# Tor session
# ---------------------------------------------------------------------------


def _build_tor_session() -> requests.Session:
    """Build a requests session routed through the Tor SOCKS5 proxy."""
    session = requests.Session()
    session.proxies = {"http": TOR_PROXY_URL, "https": TOR_PROXY_URL}
    return session


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


def _parse_tor66(soup: BeautifulSoup) -> list[dict]:
    """Parse Tor66 results.

    Real result shape (from the live spike)::

        <b><a href='http://7777...onion/'>Explore - New World Order</a></b>
        <br>New World Order is an instance focused on ...

    Each genuine hit is an ``<a>`` (pointing at a ``.onion`` host) wrapped in a
    ``<b>``; its description is the text of the ``<br>`` that follows the bold
    tag. Navigation/menu anchors are filtered out via ``_TOR66_NAV_TOKENS``.
    """
    hits: list[dict] = []
    seen: set[str] = set()
    for anchor in soup.select('b > a[href*=".onion"]'):
        href = anchor.get("href", "").strip()
        title = anchor.get_text(strip=True)
        haystack = f"{href} {title}".lower()
        if any(token in haystack for token in _TOR66_NAV_TOKENS):
            continue
        if not href or href in seen:
            continue
        seen.add(href)

        description = ""
        bold = anchor.parent
        sibling = bold.find_next_sibling("br") if bold else None
        if sibling is not None:
            following = sibling.next_sibling
            if isinstance(following, str):
                description = following.strip()

        hits.append({"title": title or href, "link": href, "description": description})
    return hits


def _parse_onionland(soup: BeautifulSoup) -> list[dict]:
    """Parse OnionLand results.

    Real result shape (from the live spike)::

        <div class="result-block">
          <a data-category="text-result" href="/r?s=...">Title ...</a>
          <div class="link">http://7ov4...onion/...</div>
          <div class="desc">...</div>
        </div>

    The visible ``<a href>`` is an obfuscated redirect; the REAL onion URL is
    the text inside ``div.link``. Sponsored rows prefix that text with ``Ad``,
    which is stripped.
    """
    hits: list[dict] = []
    seen: set[str] = set()
    for block in soup.select("div.result-block"):
        link_div = block.find("div", class_="link")
        if link_div is None:
            continue
        url = link_div.get_text(strip=True)
        if url.startswith("Ad"):
            url = url[2:].strip()
        if ".onion" not in url or url in seen:
            continue
        seen.add(url)

        title_anchor = block.find("a")
        title = title_anchor.get_text(strip=True) if title_anchor else ""
        desc_div = block.find("div", class_="desc")
        description = desc_div.get_text(strip=True) if desc_div else ""

        hits.append({"title": title or url, "link": url, "description": description})
    return hits


def _parse_generic_onion(soup: BeautifulSoup) -> list[dict]:
    """Fallback parser: unique anchors pointing at ``.onion`` hosts."""
    hits: list[dict] = []
    seen: set[str] = set()
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"]
        if ".onion" not in href or href in seen:
            continue
        seen.add(href)
        title = anchor.get_text(strip=True) or href
        hits.append({"title": title, "link": href, "description": ""})
    return hits


def _parse_results(parser: str, html: str) -> list[dict]:
    """Dispatch to the parser named in the engine config."""
    soup = BeautifulSoup(html, "html.parser")
    if parser == "tor66":
        return _parse_tor66(soup)
    if parser == "onionland":
        return _parse_onionland(soup)
    return _parse_generic_onion(soup)


def _is_captcha(text: str) -> bool:
    """Detect a CAPTCHA challenge in an engine response body."""
    return "captcha" in text.lower()


# ---------------------------------------------------------------------------
# Engine selection / fetching
# ---------------------------------------------------------------------------


def _select_engines(include_unfiltered: bool = False) -> list[EngineConfig]:
    """Return the engines to query.

    ``include_unfiltered`` is RESERVED for API stability (schema + router still
    accept it) but currently has NO effect: there is no scrapable filtered tier
    to gate, so every engine — both unfiltered — always runs. Keeping the flag
    avoids breaking callers if a filtered engine is ever re-introduced.
    """
    return list(ENGINES)


def _fetch_engine(
    engine: EngineConfig,
    query: str,
    tor_session: requests.Session,
) -> EngineResult:
    """Query a single engine, degrading gracefully on any failure.

    CAPTCHA, HTTP 429, any non-200 status, connection errors, and timeouts all
    yield zero results for this engine without raising; no retry is attempted.
    Malformed but successful (HTTP 200) responses count as available with zero
    hits so they do not poison the overall validation badge.
    """
    url = engine.url.format(query=quote(query, safe="@._-"))
    # .onion endpoints serve self-signed certs over the Tor SOCKS proxy, so
    # verify=False is expected for every engine here (all require Tor).
    try:
        resp = tor_session.get(
            url,
            headers={"User-Agent": random.choice(USER_AGENTS)},
            timeout=PER_ENGINE_TIMEOUT,
            verify=False,
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


def _normalize(results: list[EngineResult]) -> tuple[list[dict], list[dict]]:
    """Build the ``raw`` list and the single ``graphic`` section.

    All hits land in one ``darkweb`` section tagged ``filtered: False`` — there
    is no separate unfiltered section anymore (no filtered tier exists).
    """
    raw: list[dict] = []
    for result in results:
        for hit in result.hits:
            raw.append(
                {
                    "title": hit["title"],
                    "link": hit["link"],
                    "engine": result.engine,
                    "filtered": False,
                }
            )

    darkweb_nodes = [dict(_ROOT_DARKWEB)]
    for idx, hit in enumerate(raw):
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

    return raw, graphic


# ---------------------------------------------------------------------------
# Main processing function
# ---------------------------------------------------------------------------


@iky_task(module_name="darkweb", dev_mode_sleep=5)
def p_darkweb(param, include_unfiltered=False):
    """Aggregate dark web search results for an email or username via Tor.

    ``include_unfiltered`` is accepted for API stability but RESERVED (no
    effect): both engines always run. See ``_select_engines``.
    """
    query = (param or "").strip()
    if not query:
        raise Exception("iKy - Empty search parameter")

    tor_session = _build_tor_session()
    engines = _select_engines(include_unfiltered)

    results: list[EngineResult] = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(_fetch_engine, engine, query, tor_session): engine
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

    raw, graphic = _normalize(results)
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
        help="RESERVED — currently has no effect (both engines always run)",
    )
    args = parser.parse_args()

    result = t_darkweb(args.target, include_unfiltered=args.unfiltered, dev_mode=False)
    output(result)
