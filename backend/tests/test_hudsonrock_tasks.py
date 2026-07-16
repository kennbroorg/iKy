"""Tests for modules.hudsonrock.hudsonrock_tasks (Strict TDD).

Backend-only Hudson Rock Cavalier infostealer module. All network access is
mocked — the live Cavalier API is NEVER hit from these tests. The autouse
``_no_dev_mode`` fixture redirects ``Path.cwd()`` so the golden file never
masks real logic (skeleton-modules.md §3.1 / §7).

Coverage maps to the SDD spec (sdd/infostealer-module/spec):
  - Module Identity (registry + alias + celery name)
  - Input Dispatch (username single / email dual)
  - Merge and Dedup (composite key, absent family tolerated)
  - No-Compromise (empty stealers / 404)
  - Error Handling (429 / generic non-200, raw never logged)
  - Output Contract (7-element ordered list, graphic N+1 nodes, N timeline)
  - Stealer Fields (redacted credential passthrough)
  - Family Enrichment (known / unknown / missing)
  - Dev Mode Golden File (bypass + sleep)
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from modules.hudsonrock.hudsonrock_tasks import (
    STEALER_FAMILY_CONTEXT,
    _aggregate_totals,
    _dedup_stealers,
    _enrich_family,
    _local_part,
    _request,
    output,
    p_hudsonrock,
    t_hudsonrock,
)

MODULE = "modules.hudsonrock.hudsonrock_tasks"


# ---------------------------------------------------------------------------
# Global dev-mode guard
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _no_dev_mode(tmp_path):
    """Prevent dev-mode JSON bypass from masking real logic."""
    with patch.object(Path, "cwd", return_value=tmp_path):
        yield


# ---------------------------------------------------------------------------
# Fixtures / builders
# ---------------------------------------------------------------------------


def _resp(status=200, payload=None):
    resp = MagicMock()
    resp.status_code = status
    resp.json.return_value = payload if payload is not None else {}
    return resp


def _stealer(**over):
    base = {
        "computer_name": "DESKTOP-ABC",
        "date_compromised": "2023-06-13",
        "stealer_family": "RedLine",
        "ip": "1.2.3.4",
        "operating_system": "Windows 10",
        "malware_path": "C:\\Users\\victim\\app.exe",
        "antiviruses": ["Windows Defender"],
        "top_passwords": ["[redacted]", "[redacted]"],
        "top_logins": ["[redacted]"],
        "total_corporate_services": 2,
        "total_user_services": 3,
    }
    base.update(over)
    return base


def _section(result):
    """Extract the ``hudsonrock`` graphic section from a result."""
    return next(g["hudsonrock"] for g in result[4]["graphic"] if "hudsonrock" in g)


def _children(result):
    return [n for n in _section(result) if n["name-node"] != "HudsonRock"]


# ===========================================================================
# Module Identity
# ===========================================================================


class TestModuleIdentity:
    def test_t_hudsonrock_is_p_hudsonrock(self):
        assert t_hudsonrock is p_hudsonrock

    def test_celery_task_name_matches_registry_convention(self):
        assert p_hudsonrock.name == "modules.hudsonrock.hudsonrock_tasks.t_hudsonrock"

    def test_registry_entry_present_and_pass_from_false(self):
        from module_registry import MODULE_REGISTRY

        assert MODULE_REGISTRY["hudsonrock"] == (
            "modules.hudsonrock.hudsonrock_tasks.t_hudsonrock",
            False,
        )

    def test_output_function_exists(self):
        assert callable(output)


# ===========================================================================
# Pure helpers — _local_part / _dedup_stealers / _aggregate_totals
# ===========================================================================


class TestLocalPart:
    def test_local_part_of_email(self):
        assert _local_part("john@example.com") == "john"

    def test_local_part_of_compound_email(self):
        assert _local_part("john.doe+tag@mail.co.uk") == "john.doe+tag"


class TestDedup:
    def test_dedup_collapses_identical_composite_key(self):
        assert len(_dedup_stealers([_stealer(), _stealer()])) == 1

    def test_dedup_keeps_records_with_distinct_key(self):
        assert len(_dedup_stealers([_stealer(), _stealer(ip="9.9.9.9")])) == 2

    def test_dedup_absent_family_normalizes_without_keyerror(self):
        a, b = _stealer(), _stealer()
        del a["stealer_family"]
        del b["stealer_family"]
        # Same physical key (family is NOT part of the key) -> collapse to one.
        assert len(_dedup_stealers([a, b])) == 1

    def test_dedup_ignores_family_and_backfills_it(self):
        # Two records identical in the physical fields but differing only in
        # family MUST collapse to one, and the missing family is backfilled.
        base = _stealer()
        del base["stealer_family"]  # first-seen lacks family (email endpoint)
        with_family = _stealer(stealer_family="Lumma")  # same machine, has family
        result = _dedup_stealers([base, with_family])
        assert len(result) == 1
        assert result[0]["stealer_family"] == "Lumma"

    def test_dedup_family_first_keeps_first_seen_family(self):
        # Order preserved: first-seen already carries the family, so the later
        # family-less duplicate collapses without wiping it.
        with_family = _stealer(stealer_family="Lumma")
        nofam = _stealer()
        del nofam["stealer_family"]
        result = _dedup_stealers([with_family, nofam])
        assert len(result) == 1
        assert result[0]["stealer_family"] == "Lumma"


class TestAggregateTotals:
    def test_totals_summed_from_deduped_records(self):
        s1 = _stealer(total_corporate_services=2, total_user_services=3)
        s2 = _stealer(ip="9.9.9.9", total_corporate_services=1, total_user_services=4)
        corp, user = _aggregate_totals([s1, s2])
        assert corp == 3
        assert user == 7

    def test_totals_default_to_zero_when_absent(self):
        s = _stealer()
        del s["total_corporate_services"]
        del s["total_user_services"]
        assert _aggregate_totals([s]) == (0, 0)


# ===========================================================================
# Family Enrichment
# ===========================================================================


class TestFamilyEnrichment:
    def test_known_family_uses_mapped_description(self):
        label, desc = _enrich_family({"stealer_family": "RedLine"})
        assert label == "RedLine"
        assert desc == STEALER_FAMILY_CONTEXT["RedLine"]

    def test_unknown_family_keeps_raw_name_with_generic_desc(self):
        label, desc = _enrich_family({"stealer_family": "BrandNewStealer"})
        assert label == "BrandNewStealer"
        assert desc == "infostealer"

    def test_missing_family_falls_back_to_unknown(self):
        label, desc = _enrich_family({})
        assert label == "Unknown"
        assert desc == "infostealer"

    def test_none_family_falls_back_to_unknown(self):
        label, desc = _enrich_family({"stealer_family": None})
        assert label == "Unknown"
        assert desc == "infostealer"

    def test_generic_stealer_present_in_context_map(self):
        # "Generic Stealer" appears in real Cavalier responses (username
        # `testadmin`) and must be a KNOWN family, not an unattributed fallback.
        assert "Generic Stealer" in STEALER_FAMILY_CONTEXT

    def test_generic_stealer_resolves_known_description(self):
        label, desc = _enrich_family({"stealer_family": "Generic Stealer"})
        assert label == "Generic Stealer"
        assert desc == STEALER_FAMILY_CONTEXT["Generic Stealer"]
        # Present-but-KNOWN path: must NOT degrade to the generic label.
        assert desc != "infostealer"


# ===========================================================================
# _request — HTTP status handling (raises iKy- exceptions)
# ===========================================================================


class TestRequest:
    def test_200_returns_parsed_json(self):
        with patch(f"{MODULE}.requests.get") as mg:
            mg.return_value = _resp(200, {"stealers": [_stealer()]})
            data = _request("http://x")
        assert data["stealers"][0]["computer_name"] == "DESKTOP-ABC"

    def test_uses_user_agent_and_timeout(self):
        with patch(f"{MODULE}.requests.get") as mg:
            mg.return_value = _resp(200, {"stealers": []})
            _request("http://x")
        _, kwargs = mg.call_args
        assert kwargs["headers"] == {"User-Agent": "iKy-OSINT"}
        assert kwargs["timeout"] == 15

    def test_404_returns_empty_dict(self):
        with patch(f"{MODULE}.requests.get") as mg:
            mg.return_value = _resp(404)
            assert _request("http://x") == {}

    def test_429_raises_rate_limited(self):
        with patch(f"{MODULE}.requests.get") as mg:
            mg.return_value = _resp(429)
            with pytest.raises(Exception, match="iKy - Rate limited"):
                _request("http://x")

    def test_generic_non_200_raises_api_error_with_status(self):
        with patch(f"{MODULE}.requests.get") as mg:
            mg.return_value = _resp(503)
            with pytest.raises(Exception, match=r"iKy - Hudson Rock API Error \(503\)"):
                _request("http://x")


# ===========================================================================
# Input Dispatch
# ===========================================================================


class TestDispatch:
    def test_username_only_single_dispatch(self):
        with patch(f"{MODULE}.requests.get") as mg:
            mg.return_value = _resp(200, {"stealers": [_stealer()]})
            t_hudsonrock("johndoe")
        urls = [c.args[0] for c in mg.call_args_list]
        assert len(urls) == 1
        assert "search-by-username?username=johndoe" in urls[0]
        assert all("search-by-email" not in u for u in urls)

    def test_email_dual_dispatch_hits_both_endpoints(self):
        with patch(f"{MODULE}.requests.get") as mg:
            mg.side_effect = [
                _resp(200, {"stealers": [_stealer()]}),
                _resp(200, {"stealers": []}),
            ]
            t_hudsonrock("john@example.com")
        urls = [c.args[0] for c in mg.call_args_list]
        assert len(urls) == 2
        assert any("search-by-email?email=john@example.com" in u for u in urls)
        assert any("search-by-username?username=john" in u for u in urls)

    def test_email_overlap_deduplicated_in_raw(self):
        dup = _stealer()
        with patch(f"{MODULE}.requests.get") as mg:
            mg.side_effect = [
                _resp(200, {"stealers": [dict(dup)]}),
                _resp(
                    200,
                    {"stealers": [dict(dup), _stealer(computer_name="LAPTOP-2")]},
                ),
            ]
            result = t_hudsonrock("john@example.com")
        stealers = result[3]["raw"]["stealers"]
        assert len(stealers) == 2  # the overlapping record collapses to one


# ===========================================================================
# No-Compromise + Error Handling (through the @iky_task wrapper)
# ===========================================================================


class TestNoCompromiseAndErrors:
    def test_empty_stealers_yields_warning(self):
        with patch(f"{MODULE}.requests.get") as mg:
            mg.return_value = _resp(200, {"stealers": []})
            result = t_hudsonrock("johndoe")
        assert result[2]["validation"] == "not_used"
        assert result[3]["raw"][0]["status"] == "Warning"
        assert result[3]["raw"][0]["reason"] == "No infostealer compromise found"

    def test_404_treated_as_no_compromise(self):
        with patch(f"{MODULE}.requests.get") as mg:
            mg.return_value = _resp(404)
            result = t_hudsonrock("johndoe")
        assert result[3]["raw"][0]["status"] == "Warning"
        assert result[3]["raw"][0]["reason"] == "No infostealer compromise found"

    def test_429_yields_rate_limited_warning(self):
        with patch(f"{MODULE}.requests.get") as mg:
            mg.return_value = _resp(429)
            result = t_hudsonrock("johndoe")
        assert result[3]["raw"][0]["status"] == "Warning"
        assert result[3]["raw"][0]["reason"] == "Rate limited"

    def test_generic_non_200_yields_api_error_warning(self):
        with patch(f"{MODULE}.requests.get") as mg:
            mg.return_value = _resp(503)
            result = t_hudsonrock("johndoe")
        assert result[3]["raw"][0]["status"] == "Warning"
        assert result[3]["raw"][0]["reason"] == "Hudson Rock API Error (503)"

    def test_raw_response_is_never_logged(self):
        """Raw API payloads (with redacted creds) MUST NOT reach the logger."""
        s = _stealer(top_passwords=["[redacted]", "[redacted]"])
        with (
            patch(f"{MODULE}.requests.get") as mg,
            patch(f"{MODULE}.logger") as mock_logger,
        ):
            mg.return_value = _resp(200, {"stealers": [s]})
            t_hudsonrock("johndoe")
        logged = " ".join(
            str(c.args) + str(c.kwargs)
            for c in (
                mock_logger.info.call_args_list
                + mock_logger.warning.call_args_list
                + mock_logger.error.call_args_list
                + mock_logger.debug.call_args_list
            )
        )
        assert "redacted" not in logged
        assert "stealers" not in logged


# ===========================================================================
# Output Contract + Stealer Fields
# ===========================================================================


class TestOutputContract:
    def test_seven_element_ordered_contract(self):
        with patch(f"{MODULE}.requests.get") as mg:
            mg.return_value = _resp(
                200,
                {"stealers": [_stealer(), _stealer(computer_name="PC2", ip="5.6.7.8")]},
            )
            result = t_hudsonrock("johndoe")
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
        assert len(result) == 7
        assert result[0]["module"] == "hudsonrock"
        assert result[1]["param"] == "johndoe"
        assert result[2]["validation"] == "hard"

    def test_graphic_has_parent_plus_one_child_per_stealer(self):
        with patch(f"{MODULE}.requests.get") as mg:
            mg.return_value = _resp(
                200,
                {"stealers": [_stealer(), _stealer(computer_name="PC2", ip="5.6.7.8")]},
            )
            result = t_hudsonrock("johndoe")
        section = _section(result)
        assert len(section) == 3  # 1 parent + 2 children
        parent = section[0]
        assert parent["name-node"] == "HudsonRock"
        assert parent["link"] == "HudsonRock"
        children = _children(result)
        assert all(c["link"] == "HudsonRock" for c in children)
        ids = [n["name-node"] for n in section]
        assert len(ids) == len(set(ids))  # unique node ids

    def test_timeline_one_event_per_stealer(self):
        with patch(f"{MODULE}.requests.get") as mg:
            mg.return_value = _resp(
                200,
                {"stealers": [_stealer(), _stealer(computer_name="PC2", ip="5.6.7.8")]},
            )
            result = t_hudsonrock("johndoe")
        timeline = result[6]["timeline"]
        assert len(timeline) == 2
        event = timeline[0]
        assert event["date"] == "2023-06-13"
        assert event["icon"] == "fas fa-bug"
        assert "Infostealer compromise" in event["action"]

    def test_raw_node_shape(self):
        with patch(f"{MODULE}.requests.get") as mg:
            mg.return_value = _resp(
                200,
                {
                    "stealers": [
                        _stealer(total_corporate_services=2, total_user_services=3)
                    ]
                },
            )
            result = t_hudsonrock("johndoe")
        raw = result[3]["raw"]
        assert set(raw.keys()) == {
            "queries",
            "stealers",
            "total_corporate_services",
            "total_user_services",
        }
        assert raw["total_corporate_services"] == 2
        assert raw["total_user_services"] == 3
        assert raw["queries"][0]["type"] == "username"

    def test_output_is_json_serializable(self):
        with patch(f"{MODULE}.requests.get") as mg:
            mg.return_value = _resp(200, {"stealers": [_stealer()]})
            result = t_hudsonrock("johndoe")
        assert json.loads(json.dumps(result)) == result


class TestStealerFields:
    def test_child_node_surfaces_required_fields(self):
        with patch(f"{MODULE}.requests.get") as mg:
            mg.return_value = _resp(200, {"stealers": [_stealer()]})
            result = t_hudsonrock("johndoe")
        child = _children(result)[0]
        for field in (
            "date_compromised",
            "stealer_family",
            "computer_name",
            "operating_system",
            "malware_path",
            "antiviruses",
            "ip",
            "top_passwords",
            "top_logins",
            "total_services",
        ):
            assert field in child
        # total services = per-record corporate + user services.
        assert child["total_services"] == 5

    def test_redacted_credentials_pass_through_unchanged(self):
        s = _stealer(
            top_passwords=["[redacted]", "[redacted]"], top_logins=["[redacted]"]
        )
        with patch(f"{MODULE}.requests.get") as mg:
            mg.return_value = _resp(200, {"stealers": [s]})
            result = t_hudsonrock("johndoe")
        child = _children(result)[0]
        assert child["top_passwords"] == ["[redacted]", "[redacted]"]
        assert child["top_logins"] == ["[redacted]"]

    def test_known_family_description_in_graphic_node(self):
        with patch(f"{MODULE}.requests.get") as mg:
            mg.return_value = _resp(
                200, {"stealers": [_stealer(stealer_family="RedLine")]}
            )
            result = t_hudsonrock("johndoe")
        child = _children(result)[0]
        assert child["help"] == STEALER_FAMILY_CONTEXT["RedLine"]
        assert child["stealer_family"] == "RedLine"

    def test_email_response_missing_family_is_graceful(self):
        s = _stealer()
        del s["stealer_family"]
        with patch(f"{MODULE}.requests.get") as mg:
            mg.side_effect = [
                _resp(200, {"stealers": [s]}),
                _resp(200, {"stealers": []}),
            ]
            result = t_hudsonrock("john@example.com")
        child = _children(result)[0]
        assert child["stealer_family"] == "Unknown"
        assert child["help"] == "infostealer"


# ===========================================================================
# Live-API Regression — inconsistent family across the two Cavalier endpoints
# ===========================================================================


class TestFamilyMergeRegression:
    """Real Hudson Rock behavior (change `sdd/infostealer-module`).

    The SAME physical compromise is returned by BOTH Cavalier endpoints but the
    ``stealer_family`` is inconsistent: ``search-by-email`` omits the key while
    ``search-by-username`` includes ``"Lumma"``. Keying dedup on family split
    one machine into two records and dropped the family on one copy. Dedup MUST
    key on the physical fields only and backfill the family on collision.
    """

    @staticmethod
    def _email_stealer_no_family():
        # Mirrors search-by-email?email=manvirdi2000@gmail.com : NO family key.
        return {
            "computer_name": "Dell_Laptop",
            "date_compromised": "2023-08-09T08:59:11.953Z",
            "ip": "122.161.**.**",
            "operating_system": "Windows 10 (10.0.19045)",
            "malware_path": "C:\\Users\\manvirdi\\stealer.exe",
            "antiviruses": [],
            "top_passwords": ["[redacted]", "[redacted]"],
            "top_logins": ["[redacted]"],
            "total_corporate_services": 0,
            "total_user_services": 1,
        }

    @classmethod
    def _username_stealer_lumma(cls):
        # Mirrors search-by-username?username=manvirdi2000 : SAME machine + Lumma.
        stealer = cls._email_stealer_no_family()
        stealer["stealer_family"] = "Lumma"
        return stealer

    def test_dual_lookup_merges_to_single_lumma_record(self):
        with patch(f"{MODULE}.requests.get") as mg:
            mg.side_effect = [
                _resp(200, {"stealers": [self._email_stealer_no_family()]}),
                _resp(200, {"stealers": [self._username_stealer_lumma()]}),
            ]
            result = t_hudsonrock("manvirdi2000@gmail.com")

        # Exactly ONE deduped compromise survives.
        stealers = result[3]["raw"]["stealers"]
        assert len(stealers) == 1
        children = _children(result)
        assert len(children) == 1

        # The surviving record carries the populated family (not lost, not dup).
        child = children[0]
        assert child["stealer_family"] == "Lumma"
        assert child["help"] == STEALER_FAMILY_CONTEXT["Lumma"]
        assert child["computer_name"] == "Dell_Laptop"

    def test_timeline_reflects_merged_family_once(self):
        with patch(f"{MODULE}.requests.get") as mg:
            mg.side_effect = [
                _resp(200, {"stealers": [self._email_stealer_no_family()]}),
                _resp(200, {"stealers": [self._username_stealer_lumma()]}),
            ]
            result = t_hudsonrock("manvirdi2000@gmail.com")
        timeline = result[6]["timeline"]
        assert len(timeline) == 1
        assert "Lumma" in timeline[0]["action"]


# ===========================================================================
# Profile
# ===========================================================================


class TestProfile:
    def test_profile_presence_counts(self):
        with patch(f"{MODULE}.requests.get") as mg:
            mg.return_value = _resp(
                200,
                {
                    "stealers": [
                        _stealer(total_corporate_services=2, total_user_services=3),
                        _stealer(
                            ip="9.9.9.9",
                            total_corporate_services=1,
                            total_user_services=4,
                        ),
                    ]
                },
            )
            result = t_hudsonrock("johndoe")
        presence = next(p["presence"] for p in result[5]["profile"] if "presence" in p)
        children = presence[0]["children"]
        by_name = {c["name"]: c["value"] for c in children}
        assert by_name["stealers"] == 2
        assert by_name["total_corporate_services"] == 3
        assert by_name["total_user_services"] == 7

    def test_email_input_adds_derived_username_to_profile(self):
        with patch(f"{MODULE}.requests.get") as mg:
            mg.side_effect = [
                _resp(200, {"stealers": [_stealer()]}),
                _resp(200, {"stealers": []}),
            ]
            result = t_hudsonrock("john@example.com")
        username_field = next(
            (p for p in result[5]["profile"] if "username" in p), None
        )
        assert username_field is not None
        assert username_field["username"] == "john"

    def test_username_input_has_no_derived_username_field(self):
        with patch(f"{MODULE}.requests.get") as mg:
            mg.return_value = _resp(200, {"stealers": [_stealer()]})
            result = t_hudsonrock("johndoe")
        assert all("username" not in p for p in result[5]["profile"])


# ===========================================================================
# Dev Mode Golden File
# ===========================================================================


class TestDevMode:
    def test_golden_file_bypasses_api_and_sleeps(self, tmp_path):
        golden = [
            {"module": "hudsonrock"},
            {"param": "devuser"},
            {"validation": "hard"},
            {
                "raw": {
                    "queries": [],
                    "stealers": [],
                    "total_corporate_services": 0,
                    "total_user_services": 0,
                }
            },
            {"graphic": [{"hudsonrock": []}]},
            {"profile": []},
            {"timeline": []},
        ]
        outputs = tmp_path / "outputs"
        outputs.mkdir()
        (outputs / "output-hudsonrock.json").write_text(json.dumps(golden))

        with (
            patch.object(Path, "cwd", return_value=tmp_path),
            patch("factories.task_wrapper.time.sleep") as mock_sleep,
            patch(f"{MODULE}.requests.get") as mg,
        ):
            result = t_hudsonrock("anyinput")

        assert result == golden
        mg.assert_not_called()
        mock_sleep.assert_called_once_with(5)

    def test_dev_mode_false_forces_real_execution(self, tmp_path):
        golden = [{"module": "hudsonrock"}, {"stale": True}]
        outputs = tmp_path / "outputs"
        outputs.mkdir()
        (outputs / "output-hudsonrock.json").write_text(json.dumps(golden))

        with (
            patch.object(Path, "cwd", return_value=tmp_path),
            patch(f"{MODULE}.requests.get") as mg,
        ):
            mg.return_value = _resp(200, {"stealers": [_stealer()]})
            result = t_hudsonrock("realuser", dev_mode=False)

        assert result != golden
        assert result[0]["module"] == "hudsonrock"
        assert mg.called


# ===========================================================================
# Golden file shipped with the repo conforms to the contract
# ===========================================================================


class TestShippedGoldenFile:
    def test_repo_golden_file_matches_contract(self):
        golden_path = (
            Path(__file__).resolve().parent.parent
            / "outputs"
            / "output-hudsonrock.json"
        )
        if not golden_path.exists():
            pytest.skip("golden file not present (outputs/ is gitignored)")
        data = json.loads(golden_path.read_text())
        keys = [next(iter(d)) for d in data]
        assert keys == [
            "module",
            "param",
            "validation",
            "raw",
            "graphic",
            "profile",
            "timeline",
        ]
        assert data[0]["module"] == "hudsonrock"
        raw = data[3]["raw"]
        assert set(raw.keys()) == {
            "queries",
            "stealers",
            "total_corporate_services",
            "total_user_services",
        }
