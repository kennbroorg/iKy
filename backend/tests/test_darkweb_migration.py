"""Tests for modules.darkweb.darkweb_tasks (Strict TDD).

The module is UNFILTERED-ONLY (see sdd/dark-web/fix-plan): a live engine spike
proved Ahmia blocks all scraping, so only the two engines that actually return
data over Tor ship — Tor66 and OnionLand. These tests exercise the REAL HTML
structures captured during the spike (no invented markup):

  - R1  Module skeleton compliance (alias, registry, attribution, CLI/JSON).
  - R2  Input acceptance (email/username forwarded verbatim, blank warning).
  - R3  Aggregated search across both engines + graceful empty.
  - R5  Tor SOCKS5 proxy session + graceful degradation.
  - R6  Concurrency / timeout / hard deadline.
  - R7  CAPTCHA / HTTP error / malformed HTML degradation + real parsers.
  - R8  dev_mode golden-file bypass.
  - R9  JSON output contract (ordered keys, node wiring, unique ids, no tasks,
        every hit tagged filtered=False, single ``darkweb`` section).
  - R10 Legacy removal (darkpass / psbdmp gone, no dead references).

All network access is mocked. Engine fetches are deterministic via static HTML
fixtures or by patching ``_fetch_engine`` so the suite is fully offline.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests
from modules.darkweb.darkweb_tasks import (
    EngineConfig,
    EngineResult,
    _build_tor_session,
    _fetch_engine,
    _parse_results,
    _select_engines,
    output,
    p_darkweb,
    t_darkweb,
)

# ---------------------------------------------------------------------------
# Global dev-mode guard: redirect Path.cwd() so the golden file never masks
# real execution (skeleton-modules.md §3.1 / §7).
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _no_dev_mode(tmp_path):
    with patch.object(Path, "cwd", return_value=tmp_path):
        yield


# ---------------------------------------------------------------------------
# Real-shaped HTML fixtures (captured during the live engine spike)
# ---------------------------------------------------------------------------

# Tor66: genuine hits are <b><a href=...onion>Title</a></b><br>description.
# The first two anchors are navigation chrome and MUST be filtered out.
TOR66_HTML = """
<html><body>
<b><a href='http://tor66sewebgixwhcqfnp5inzp5x5uohhdy3kvtnyfxc2e5mxiuh34iid.onion/fresh'>Fresh Onions</a></b><br>navigation
<b><a href='http://tor66sewebgixwhcqfnp5inzp5x5uohhdy3kvtnyfxc2e5mxiuh34iid.onion/random'>Random Onion</a></b><br>navigation
<b><a href='http://7777777jo3a6i4hyon46lxfld7q7ltutpmtc3yitiirds26cpl3uqxid.onion/'>Explore - New World Order</a></b><br>New World Order is an instance focused on the evolution of conspiracy theories
<b><a href='http://secondrealresult234567abcdefghijklmnopqrstuvwxyz0123456789ab.onion/'>Second Real Result</a></b><br>Another real description here
</body></html>
"""

TOR66_EMPTY_HTML = """
<html><body>
<b><a href='http://tor66sewebgixwhcqfnp5inzp5x5uohhdy3kvtnyfxc2e5mxiuh34iid.onion/submit'>Submit</a></b><br>nav only
<p>No results found.</p>
</body></html>
"""

# OnionLand: real onion URL lives in div.link text (the <a href> is an
# obfuscated redirect). Sponsored rows prefix the link text with "Ad".
ONIONLAND_HTML = """
<html><body>
<div class="result-block">
  <a data-category="text-result" href="/r?s=obfuscated-redirect-1">Elon Musk menace par Zelensky</a>
  <div class="link">http://7ov433bmudtgkl3vnjbg6rfke4n4rwk6xi2mxrvlgjgrw46ws7vqrsqd.onion/elon-musk</div>
  <div class="desc">A page discussing the topic in detail.</div>
</div>
<div class="result-block">
  <a data-category="text-result" href="/r?s=obfuscated-redirect-2">Sponsored Listing</a>
  <div class="link">Adhttp://adsponsoredonionhost1234567890abcdefghijklmnopqrstuv.onion/promo</div>
  <div class="desc">Sponsored result.</div>
</div>
<div class="result-block">
  <a data-category="text-result" href="/r?s=obfuscated-redirect-3">Clearnet noise</a>
  <div class="link">https://example.com/not-an-onion</div>
  <div class="desc">Should be skipped (not an onion).</div>
</div>
</body></html>
"""

ONIONLAND_EMPTY_HTML = """
<html><body>
<div class="results"><p>No results.</p></div>
</body></html>
"""


# ---------------------------------------------------------------------------
# Helpers for mocking engine fetches
# ---------------------------------------------------------------------------


def _fake_response(status_code=200, text=""):
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = text
    return resp


def _session_returning(resp):
    session = MagicMock()
    session.get.return_value = resp
    return session


def _fetch_factory(spec):
    """Return a fake ``_fetch_engine`` driven by ``spec``.

    ``spec`` maps engine name -> (available: bool, hits: list[dict]).
    Unlisted engines default to (False, []) — i.e. unavailable.
    """

    def _fetch(engine, query, tor_session):
        available, hits = spec.get(engine.name, (False, []))
        return EngineResult(engine.name, engine.filtered, available, list(hits))

    return _fetch


def _recording_fetch(spec, called):
    def _fetch(engine, query, tor_session):
        called.append(engine.name)
        available, hits = spec.get(engine.name, (True, []))
        return EngineResult(engine.name, engine.filtered, available, list(hits))

    return _fetch


def _query_recording_fetch(queries):
    def _fetch(engine, query, tor_session):
        queries.append(query)
        return EngineResult(engine.name, engine.filtered, True, [])

    return _fetch


TOR66_ENGINE = EngineConfig(
    name="Tor66",
    url="http://tor66example.onion/search?q={query}",
    filtered=False,
    requires_tor=True,
    parser="tor66",
)
ONIONLAND_ENGINE = EngineConfig(
    name="OnionLand",
    url="http://onionlandexample.onion/search?q={query}",
    filtered=False,
    requires_tor=True,
    parser="onionland",
)


# ===========================================================================
# R1 — Module skeleton compliance
# ===========================================================================


class TestSkeletonCompliance:
    def test_t_darkweb_is_p_darkweb(self):
        """R1 — alias points at the same task object."""
        assert t_darkweb is p_darkweb

    def test_celery_task_name_matches_registry_convention(self):
        """R1-S1 — canonical Celery task name."""
        assert p_darkweb.name == "modules.darkweb.darkweb_tasks.t_darkweb"

    def test_registry_entry_present(self):
        """R1-S1 — registry maps darkweb to the task, pass_from False."""
        from module_registry import MODULE_REGISTRY

        assert MODULE_REGISTRY["darkweb"] == (
            "modules.darkweb.darkweb_tasks.t_darkweb",
            False,
        )

    def test_single_arg_call_does_not_raise_typeerror(self):
        """R1-S1 — task is callable with a single positional arg."""
        with patch(
            "modules.darkweb.darkweb_tasks._fetch_engine",
            _fetch_factory({"Tor66": (True, []), "OnionLand": (True, [])}),
        ):
            result = t_darkweb("testuser")
        assert isinstance(result, list)

    def test_output_is_json_serializable(self):
        """R1-S2 — full output round-trips through json (CLI uses output())."""
        with patch(
            "modules.darkweb.darkweb_tasks._fetch_engine",
            _fetch_factory(
                {
                    "Tor66": (True, [{"title": "T", "link": "http://t.onion/"}]),
                    "OnionLand": (True, []),
                }
            ),
        ):
            result = t_darkweb("alice@example.com")
        assert json.loads(json.dumps(result)) == result

    def test_output_function_exists(self):
        """R1-S2 — CLI output() helper is present and callable."""
        assert callable(output)

    def test_robin_mit_attribution_present(self):
        """R1-S4 — robin MIT attribution appears in the module header."""
        import inspect

        from modules.darkweb import darkweb_tasks

        src = inspect.getsource(darkweb_tasks)
        assert "apurvsinghgautam/robin" in src
        assert "MIT" in src


# ===========================================================================
# R2 — Input acceptance
# ===========================================================================


class TestInputAcceptance:
    def test_email_forwarded_to_every_engine(self):
        """R2-S1 — email is the search term for every engine."""
        queries = []
        with patch(
            "modules.darkweb.darkweb_tasks._fetch_engine",
            _query_recording_fetch(queries),
        ):
            result = t_darkweb("alice@example.com")
        assert len(queries) >= 1
        assert all(q == "alice@example.com" for q in queries)
        assert result[1] == {"param": "alice@example.com"}

    def test_username_forwarded_to_every_engine(self):
        """R2-S2 — username is the search term for every engine."""
        queries = []
        with patch(
            "modules.darkweb.darkweb_tasks._fetch_engine",
            _query_recording_fetch(queries),
        ):
            result = t_darkweb("alice_osint")
        assert len(queries) >= 1
        assert all(q == "alice_osint" for q in queries)
        assert result[1] == {"param": "alice_osint"}

    def test_param_is_whitespace_stripped(self):
        """R2 — param is forwarded verbatim but whitespace-stripped."""
        queries = []
        with patch(
            "modules.darkweb.darkweb_tasks._fetch_engine",
            _query_recording_fetch(queries),
        ):
            result = t_darkweb("  bob_target  ")
        assert result[1]["param"] == "bob_target"
        assert all(q == "bob_target" for q in queries)

    def test_blank_param_returns_warning(self):
        """R2-S3 — blank input raises an iKy warning caught by the wrapper."""
        result = t_darkweb("   ")
        raw = result[3]["raw"]
        assert raw[0]["status"] == "Warning"


# ===========================================================================
# R3 — Aggregated search (both engines always run)
# ===========================================================================


class TestSelectEngines:
    def test_both_engines_run_by_default(self):
        """R3-S1 — without opt-in, both shipped engines are still selected."""
        engines = _select_engines(False)
        names = {e.name for e in engines}
        assert names == {"Tor66", "OnionLand"}

    def test_include_unfiltered_has_no_effect(self):
        """fix-plan — include_unfiltered is reserved; same engine set either way."""
        assert _select_engines(False) == _select_engines(True)

    def test_no_filtered_engine_ships(self):
        """fix-plan — there is no scrapable filtered engine; all are unfiltered."""
        engines = _select_engines(True)
        assert all(e.filtered is False for e in engines)

    def test_every_engine_uses_requests_fetch_method(self):
        """fix-plan — both v1 engines fetch via requests over Tor."""
        engines = _select_engines(True)
        assert all(e.fetch_method == "requests" for e in engines)
        assert all(e.requires_tor for e in engines)


class TestAggregatedSearch:
    def test_aggregates_results_from_both_engines(self):
        """R3-S2 — results from both engines aggregate; all filtered False."""
        spec = {
            "Tor66": (
                True,
                [{"title": f"A{i}", "link": f"http://a{i}.onion/"} for i in range(3)],
            ),
            "OnionLand": (
                True,
                [{"title": f"B{i}", "link": f"http://b{i}.onion/"} for i in range(2)],
            ),
        }
        with patch("modules.darkweb.darkweb_tasks._fetch_engine", _fetch_factory(spec)):
            result = t_darkweb("testuser")
        raw = result[3]["raw"]
        assert len(raw) == 5
        assert all(item["filtered"] is False for item in raw)
        assert {item["engine"] for item in raw} == {"Tor66", "OnionLand"}

    def test_no_results_across_engines_is_graceful_hard(self):
        """R3-S3 — both engines respond empty -> raw [] and validation hard."""
        spec = {"Tor66": (True, []), "OnionLand": (True, [])}
        with patch("modules.darkweb.darkweb_tasks._fetch_engine", _fetch_factory(spec)):
            result = t_darkweb("testuser")
        assert result[3]["raw"] == []
        assert result[2]["validation"] == "hard"

    def test_single_section_only_no_unfiltered_section(self):
        """fix-plan — output has exactly one ``darkweb`` graphic section."""
        spec = {
            "Tor66": (True, [{"title": "T", "link": "http://t.onion/"}]),
            "OnionLand": (True, [{"title": "O", "link": "http://o.onion/"}]),
        }
        with patch("modules.darkweb.darkweb_tasks._fetch_engine", _fetch_factory(spec)):
            result = t_darkweb("testuser", include_unfiltered=True)
        keys = [next(iter(g)) for g in result[4]["graphic"]]
        assert keys == ["darkweb"]
        assert "darkweb_unfiltered" not in keys


# ===========================================================================
# R5 — Tor SOCKS5 proxy
# ===========================================================================


class TestTorSession:
    def test_build_tor_session_uses_socks5h_proxy(self):
        """R5-S1 — session proxies route through socks5h://tor:9050."""
        session = _build_tor_session()
        assert session.proxies["http"] == "socks5h://tor:9050"
        assert session.proxies["https"] == "socks5h://tor:9050"

    def test_all_engines_unavailable_validation_no(self):
        """R5-S2 / R6-S2 — when no engine responds, raw [] and validation no."""
        with patch(
            "modules.darkweb.darkweb_tasks._fetch_engine",
            _fetch_factory({}),  # everything unavailable
        ):
            result = t_darkweb("testuser")
        assert result[3]["raw"] == []
        assert result[2]["validation"] == "no"


# ===========================================================================
# R6 / R7 — degradation behavior at the fetch layer
# ===========================================================================


class TestFetchEngineDegradation:
    def test_success_returns_hits_and_available(self):
        """R3 — 200 + parseable HTML -> available with hits."""
        session = _session_returning(_fake_response(200, TOR66_HTML))
        result = _fetch_engine(TOR66_ENGINE, "alice", session)
        assert result.available is True
        assert result.engine == "Tor66"
        assert result.filtered is False
        assert len(result.hits) == 2
        assert result.hits[0]["link"].endswith(".onion/")

    def test_http_429_is_unavailable_and_not_retried(self):
        """R7-S1 — 429 yields no results and is fetched exactly once."""
        session = _session_returning(_fake_response(429, ""))
        result = _fetch_engine(TOR66_ENGINE, "alice", session)
        assert result.available is False
        assert result.hits == []
        assert session.get.call_count == 1

    def test_non_200_is_unavailable(self):
        """R7 — any non-200 status degrades to no results."""
        session = _session_returning(_fake_response(503, "error"))
        result = _fetch_engine(TOR66_ENGINE, "alice", session)
        assert result.available is False
        assert result.hits == []

    def test_captcha_response_is_unavailable(self):
        """R7 — CAPTCHA challenge yields no results, engine marked failed."""
        session = _session_returning(
            _fake_response(200, "<html>Please solve the CAPTCHA to continue</html>")
        )
        result = _fetch_engine(TOR66_ENGINE, "alice", session)
        assert result.available is False
        assert result.hits == []

    def test_malformed_html_is_available_with_zero_hits(self):
        """R7-S2 — 200 with no parseable nodes -> available, zero hits."""
        session = _session_returning(
            _fake_response(200, "<html><body>nothing parseable here</body></html>")
        )
        result = _fetch_engine(TOR66_ENGINE, "alice", session)
        assert result.available is True
        assert result.hits == []

    def test_connection_error_is_unavailable(self):
        """R5-S2 — connection errors are caught per-engine."""
        session = MagicMock()
        session.get.side_effect = requests.exceptions.ConnectionError("tor down")
        result = _fetch_engine(TOR66_ENGINE, "alice", session)
        assert result.available is False
        assert result.hits == []

    def test_query_is_included_in_request_url(self):
        """R2 — the search term appears in the fetched URL."""
        session = _session_returning(_fake_response(200, TOR66_HTML))
        _fetch_engine(TOR66_ENGINE, "alice@example.com", session)
        called_url = session.get.call_args[0][0]
        assert "alice@example.com" in called_url

    def test_onion_engine_uses_tor_session_without_verify(self):
        """R5 — onion engines use the Tor session with verify disabled."""
        tor = _session_returning(_fake_response(200, ONIONLAND_HTML))
        result = _fetch_engine(ONIONLAND_ENGINE, "alice", tor)
        assert tor.get.called
        assert tor.get.call_args.kwargs.get("verify") is False
        assert len(result.hits) == 2

    def test_per_engine_timeout_is_applied(self):
        """R6 — the per-engine timeout is passed to the request."""
        from modules.darkweb.darkweb_tasks import PER_ENGINE_TIMEOUT

        session = _session_returning(_fake_response(200, TOR66_HTML))
        _fetch_engine(TOR66_ENGINE, "alice", session)
        assert session.get.call_args.kwargs.get("timeout") == PER_ENGINE_TIMEOUT
        assert PER_ENGINE_TIMEOUT == 45


class TestConcurrencyDegradation:
    def test_slow_engine_does_not_block_responsive_engine(self):
        """R6-S1 — an engine raising (timeout) is skipped; others still return."""

        def _fetch(engine, query, tor_session):
            if engine.name == "OnionLand":
                raise TimeoutError("engine timed out")
            return EngineResult(
                engine.name,
                engine.filtered,
                True,
                [{"title": "A", "link": "http://a.onion/"}],
            )

        with patch("modules.darkweb.darkweb_tasks._fetch_engine", _fetch):
            result = t_darkweb("testuser")
        raw = result[3]["raw"]
        engines = {item["engine"] for item in raw}
        assert "Tor66" in engines
        assert "OnionLand" not in engines
        assert result[2]["validation"] == "hard"


# ===========================================================================
# R7 (parser layer) — deterministic parsing of REAL engine HTML
# ===========================================================================


class TestTor66Parser:
    def test_extracts_real_results_and_skips_nav(self):
        hits = _parse_results("tor66", TOR66_HTML)
        assert len(hits) == 2
        links = [h["link"] for h in hits]
        assert all(".onion" in link for link in links)
        # Navigation anchors (fresh/random on the tor66 host) are excluded.
        assert all("tor66" not in link for link in links)
        assert hits[0]["title"] == "Explore - New World Order"
        assert hits[0]["link"].startswith("http://7777777jo3a6i4hyon46")
        assert hits[0]["description"].startswith("New World Order is an instance")

    def test_empty_when_only_nav_present(self):
        assert _parse_results("tor66", TOR66_EMPTY_HTML) == []


class TestOnionLandParser:
    def test_uses_div_link_text_not_obfuscated_href(self):
        hits = _parse_results("onionland", ONIONLAND_HTML)
        # Two real onion rows (the clearnet row is skipped).
        assert len(hits) == 2
        first = hits[0]
        assert first["title"] == "Elon Musk menace par Zelensky"
        assert first["link"] == (
            "http://7ov433bmudtgkl3vnjbg6rfke4n4rwk6xi2mxrvlgjgrw46ws7vqrsqd.onion"
            "/elon-musk"
        )
        # The obfuscated /r?s= redirect must never leak into the link.
        assert "/r?s=" not in first["link"]
        assert first["description"] == "A page discussing the topic in detail."

    def test_strips_ad_prefix_from_link(self):
        hits = _parse_results("onionland", ONIONLAND_HTML)
        ad_hit = hits[1]
        assert ad_hit["link"].startswith("http://adsponsoredonionhost")
        assert not ad_hit["link"].startswith("Ad")

    def test_skips_non_onion_rows(self):
        hits = _parse_results("onionland", ONIONLAND_HTML)
        assert all(".onion" in h["link"] for h in hits)

    def test_empty_when_no_result_blocks(self):
        assert _parse_results("onionland", ONIONLAND_EMPTY_HTML) == []


# ===========================================================================
# R8 — dev_mode golden-file bypass (NOT under the _no_dev_mode default path)
# ===========================================================================


class TestDevMode:
    def test_golden_file_bypasses_real_execution_with_sleep(self, tmp_path):
        """R8-S1 — golden file returns directly, sleeps 5s, p_darkweb skipped."""
        golden = [
            {"module": "darkweb"},
            {"param": "devuser"},
            {"validation": "hard"},
            {"raw": []},
            {"graphic": [{"darkweb": []}]},
            {"profile": []},
            {"timeline": []},
        ]
        outputs = tmp_path / "outputs"
        outputs.mkdir()
        (outputs / "output-darkweb.json").write_text(json.dumps(golden))

        with (
            patch.object(Path, "cwd", return_value=tmp_path),
            patch("factories.task_wrapper.time.sleep") as mock_sleep,
            patch("modules.darkweb.darkweb_tasks._build_tor_session") as mock_build,
        ):
            result = t_darkweb("anything")

        assert result == golden
        mock_sleep.assert_called_once_with(5)
        mock_build.assert_not_called()

    def test_dev_mode_false_forces_real_execution(self, tmp_path):
        """R8-S2 — dev_mode=False ignores the golden file and runs for real."""
        golden = [{"module": "darkweb"}, {"stale": True}]
        outputs = tmp_path / "outputs"
        outputs.mkdir()
        (outputs / "output-darkweb.json").write_text(json.dumps(golden))

        called = []
        with (
            patch.object(Path, "cwd", return_value=tmp_path),
            patch(
                "modules.darkweb.darkweb_tasks._fetch_engine",
                _recording_fetch({}, called),
            ),
        ):
            result = t_darkweb("realuser", dev_mode=False)

        assert result != golden
        assert result[0]["module"] == "darkweb"
        assert len(called) >= 1


# ===========================================================================
# R9 — JSON output contract
# ===========================================================================


class TestOutputContract:
    def _run(self, spec, **kwargs):
        with patch("modules.darkweb.darkweb_tasks._fetch_engine", _fetch_factory(spec)):
            return t_darkweb("testuser", **kwargs)

    def test_key_order_and_no_tasks(self):
        """R9-S1 — ordered keys, no follow-up tasks section."""
        result = self._run({"Tor66": (True, []), "OnionLand": (True, [])})
        keys = [next(iter(d)) for d in result]
        assert keys == [
            "module",
            "param",
            "validation",
            "raw",
            "graphic",
            "profile",
            "timeline",
        ]
        assert "tasks" not in keys

    def test_module_name_and_empty_profile_timeline(self):
        result = self._run({"Tor66": (True, []), "OnionLand": (True, [])})
        assert result[0]["module"] == "darkweb"
        assert result[5]["profile"] == []
        assert result[6]["timeline"] == []

    def test_raw_items_have_exact_shape(self):
        """R9-S2 — raw items carry exactly title/link/engine/filtered."""
        spec = {
            "Tor66": (True, [{"title": "A0", "link": "http://a0.onion/"}]),
            "OnionLand": (True, [{"title": "B0", "link": "http://b0.onion/"}]),
        }
        result = self._run(spec)
        raw = result[3]["raw"]
        assert len(raw) == 2
        for item in raw:
            assert set(item.keys()) == {"title", "link", "engine", "filtered"}
            assert item["filtered"] is False

    def test_graphic_root_and_node_links_and_uniqueness(self):
        """R9-S3 — root node present, hits link to it, ids unique."""
        spec = {
            "Tor66": (
                True,
                [{"title": f"A{i}", "link": f"http://a{i}.onion/"} for i in range(2)],
            ),
            "OnionLand": (True, []),
        }
        result = self._run(spec)
        section = next(g["darkweb"] for g in result[4]["graphic"] if "darkweb" in g)
        name_nodes = [n["name-node"] for n in section]
        assert "DarkWeb" in name_nodes
        assert len(name_nodes) == len(set(name_nodes))

        root = next(n for n in section if n["name-node"] == "DarkWeb")
        assert root["link"] == "DarkWeb"
        hits = [n for n in section if n["name-node"] != "DarkWeb"]
        assert hits, "expected hit nodes"
        assert all(n["link"] == "DarkWeb" for n in hits)
        assert all(n["name-node"].startswith("DW-") for n in hits)
        assert all(".onion" in n["subtitle"] for n in hits)

    def test_node_ids_unique_across_section(self):
        """R9-S3 — DW-* ids never collide within the output."""
        spec = {
            "Tor66": (True, [{"title": "F", "link": "http://f.onion/"}]),
            "OnionLand": (True, [{"title": "U", "link": "http://u.onion/"}]),
        }
        result = self._run(spec)
        all_ids = []
        for section in result[4]["graphic"]:
            nodes = next(iter(section.values()))
            all_ids.extend(n["name-node"] for n in nodes)
        assert len(all_ids) == len(set(all_ids))

    def test_unhandled_exception_returns_fail_shape(self):
        """R9-S4 — a generic exception yields the @iky_task error envelope."""
        with patch(
            "modules.darkweb.darkweb_tasks._build_tor_session",
            side_effect=RuntimeError("boom"),
        ):
            result = t_darkweb("testuser")
        assert result[2]["validation"] == "not_used"
        assert result[3]["raw"][0]["status"] == "Fail"


# ===========================================================================
# R10 — Legacy removal
# ===========================================================================


class TestLegacyRemoval:
    def test_darkpass_package_is_gone(self):
        """R10-S1/S2 — darkpass module directory no longer exists."""
        assert not Path("modules/darkpass").exists()

    def test_psbdmp_package_is_gone(self):
        """R10-S2 — psbdmp module directory no longer exists."""
        assert not Path("modules/psbdmp").exists()

    def test_darkpass_not_importable(self):
        with pytest.raises(ModuleNotFoundError):
            __import__("modules.darkpass.darkpass_tasks")

    def test_psbdmp_not_importable(self):
        with pytest.raises(ModuleNotFoundError):
            __import__("modules.psbdmp.psbdmp_tasks")

    def test_registry_has_no_legacy_modules(self):
        from module_registry import MODULE_REGISTRY

        assert "darkpass" not in MODULE_REGISTRY
        assert "psbdmp" not in MODULE_REGISTRY

    def test_celery_imports_have_no_legacy_modules(self):
        import celery_app

        imports = celery_app.celery.conf.imports
        assert not any("darkpass" in imp for imp in imports)
        assert not any("psbdmp" in imp for imp in imports)

    def test_no_darkweb_unfiltered_dead_code(self):
        """fix-plan — the removed unfiltered section leaves no references."""
        import inspect

        from modules.darkweb import darkweb_tasks

        src = inspect.getsource(darkweb_tasks)
        assert "darkweb_unfiltered" not in src
        assert "DarkWebUnfiltered" not in src
