"""Regression tests for keybase migration to @iky_task decorator.

Verifies that the migrated p_keybase (now a Celery task via @iky_task)
produces output structurally identical to the old t_keybase wrapper,
and correctly propagates proof state from the API response.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Block dev-mode file globally for this test module
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _block_devmode(tmp_path):
    """Redirect Path.cwd() so dev-mode files are never found."""
    with patch.object(Path, "cwd", return_value=tmp_path):
        yield


# ---------------------------------------------------------------------------
# Realistic mock Keybase API responses
# ---------------------------------------------------------------------------

KEYBASE_API_RESPONSE = {
    "status": {"code": 0, "name": "OK"},
    "them": [
        {
            "id": "abc123",
            "basics": {
                "username": "testuser",
                "ctime": 1500000000,
                "mtime": 1600000000,
                "track_version": 673,
            },
            "profile": {
                "full_name": "Test User",
                "location": "New York",
                "bio": "OSINT test bio",
            },
            "pictures": {
                "primary": {
                    "url": "https://keybase.io/testuser/picture",
                }
            },
            "devices": {
                "dev1": {
                    "type": "mobile",
                    "name": "iPhone",
                }
            },
            "proofs_summary": {
                "all": [
                    {
                        "proof_type": "twitter",
                        "nametag": "testuser_tw",
                        "service_url": "https://twitter.com/testuser_tw",
                        "human_url": "https://twitter.com/testuser_tw/status/123",
                        "proof_url": "https://keybase.io/testuser/sigs/abc",
                        "state": 1,
                    },
                    {
                        "proof_type": "github",
                        "nametag": "testuser_gh",
                        "service_url": "https://github.com/testuser_gh",
                        # no "state" key — graceful degradation test
                        # no "human_url" — graceful degradation test
                    },
                ]
            },
            "cryptocurrency_addresses": {
                "bitcoin": [{"address": "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2"}],
                "ethereum": [{"address": "0xAbCdEf1234567890"}],
            },
            "public_keys": {
                "primary": {
                    "key_fingerprint": "4475293306243408fa5958dc63847b4b83930f0c",
                    "key_bits": 4096,
                    "key_algo": 1,
                    "ctime": 1400000000,
                },
                "sibkeys": {
                    "kid1": {"key_type": 2},
                    "kid2": {"key_type": 2},
                },
                "subkeys": {
                    "kid3": {"key_type": 3},
                },
            },
            "sigs": {
                "last": {
                    "seqno": 841,
                    "sig_id": "abc123def456",
                }
            },
        }
    ],
}

KEYBASE_API_NOT_FOUND = {
    "status": {"code": 0, "name": "OK"},
    "them": [None],
}


@pytest.fixture
def mock_html_session():
    """Mock HTMLSession so no real web scraping happens."""
    mock_resp = MagicMock()
    mock_resp.html.find.return_value = MagicMock(text="Following (10)\nFollowers (20)")
    mock_session = MagicMock()
    mock_session.get.return_value = mock_resp
    with patch("modules.keybase.keybase_tasks.HTMLSession", return_value=mock_session):
        yield mock_session


@pytest.fixture
def mock_keybase_api(mock_html_session):
    """Mock requests.get to return a full Keybase user payload."""
    mock_response = MagicMock()
    mock_response.text = json.dumps(KEYBASE_API_RESPONSE)
    with patch(
        "modules.keybase.keybase_tasks.requests.get", return_value=mock_response
    ):
        yield mock_response


@pytest.fixture
def mock_keybase_api_not_found(mock_html_session):
    """Mock requests.get to return a not-found payload."""
    mock_response = MagicMock()
    mock_response.text = json.dumps(KEYBASE_API_NOT_FOUND)
    with patch(
        "modules.keybase.keybase_tasks.requests.get", return_value=mock_response
    ):
        yield mock_response


@pytest.fixture
def mock_fontcheat():
    """Mock search_icon_5 to return a predictable icon."""
    with patch(
        "modules.keybase.keybase_tasks.search_icon_5",
        side_effect=lambda name: f"fas fa-{name}" if name else "fas fa-question",
    ):
        yield


@pytest.fixture
def mock_analize_rrss():
    """Mock analize_rrss to return an empty dict (no social extraction)."""
    with patch(
        "modules.keybase.keybase_tasks.analize_rrss",
        return_value={},
    ):
        yield


# ===========================================================================
# Output structure tests — happy path
# ===========================================================================


class TestKeybaseOutputStructure:
    """Verify p_keybase output matches the original t_keybase contract."""

    def test_success_output_has_required_keys(
        self, mock_keybase_api, mock_fontcheat, mock_analize_rrss
    ):
        from modules.keybase.keybase_tasks import p_keybase

        result = p_keybase("testuser", from_m="Initial")

        assert isinstance(result, list)
        keys = [next(iter(item.keys())) for item in result if isinstance(item, dict)]
        assert "module" in keys
        assert "param" in keys
        assert "validation" in keys
        assert "raw" in keys
        assert "graphic" in keys
        assert "profile" in keys
        assert "timeline" in keys

    def test_module_field_is_keybase(
        self, mock_keybase_api, mock_fontcheat, mock_analize_rrss
    ):
        from modules.keybase.keybase_tasks import p_keybase

        result = p_keybase("testuser")
        module = next(item["module"] for item in result if "module" in item)
        assert module == "keybase"

    def test_param_matches_input(
        self, mock_keybase_api, mock_fontcheat, mock_analize_rrss
    ):
        from modules.keybase.keybase_tasks import p_keybase

        result = p_keybase("testuser")
        param = next(item["param"] for item in result if "param" in item)
        assert param == "testuser"

    def test_output_positional_structure(
        self, mock_keybase_api, mock_fontcheat, mock_analize_rrss
    ):
        """Output array must be positionally correct: module, param, validation, raw…"""
        from modules.keybase.keybase_tasks import p_keybase

        result = p_keybase("testuser")

        assert "module" in result[0] and result[0]["module"] == "keybase"
        assert "param" in result[1]
        assert "validation" in result[2]
        assert "raw" in result[3]


# ===========================================================================
# from_m parameter handling
# ===========================================================================


class TestKeybaseFromMParameter:
    """Verify from_m drives validation field value."""

    def test_from_m_initial_sets_validation_no(
        self, mock_keybase_api, mock_fontcheat, mock_analize_rrss
    ):
        from modules.keybase.keybase_tasks import p_keybase

        result = p_keybase("testuser", from_m="Initial")
        validation = next(item["validation"] for item in result if "validation" in item)
        assert validation == "no"

    def test_from_m_other_sets_validation_soft(
        self, mock_keybase_api, mock_fontcheat, mock_analize_rrss
    ):
        from modules.keybase.keybase_tasks import p_keybase

        result = p_keybase("testuser", from_m="twitter")
        validation = next(item["validation"] for item in result if "validation" in item)
        assert validation == "soft"

    def test_from_m_defaults_to_initial(
        self, mock_keybase_api, mock_fontcheat, mock_analize_rrss
    ):
        """Default from_m is 'Initial' → validation 'no'."""
        from modules.keybase.keybase_tasks import p_keybase

        result = p_keybase("testuser")
        validation = next(item["validation"] for item in result if "validation" in item)
        assert validation == "no"


# ===========================================================================
# Error paths (via the decorator)
# ===========================================================================


class TestKeybaseErrorPaths:
    """Verify error handling matches the original t_keybase behavior."""

    def test_iky_exception_returns_warning(self):
        from modules.keybase.keybase_tasks import p_keybase

        with patch(
            "modules.keybase.keybase_tasks.requests.get",
            side_effect=Exception("iKy - Missing or invalid Key"),
        ):
            result = p_keybase("testuser")

        raw = next(item["raw"] for item in result if "raw" in item)
        assert isinstance(raw, list)
        assert raw[0]["status"] == "Warning"
        assert raw[0]["reason"] == "Missing or invalid Key"

    def test_generic_exception_returns_fail(self):
        from modules.keybase.keybase_tasks import p_keybase

        with patch(
            "modules.keybase.keybase_tasks.requests.get",
            side_effect=RuntimeError("network down"),
        ):
            result = p_keybase("testuser")

        raw = next(item["raw"] for item in result if "raw" in item)
        assert raw[0]["status"] == "Fail"
        assert raw[0]["reason"] == "network down"

    def test_error_includes_traceback(self):
        from modules.keybase.keybase_tasks import p_keybase

        with patch(
            "modules.keybase.keybase_tasks.requests.get",
            side_effect=Exception("iKy - test error"),
        ):
            result = p_keybase("testuser")

        raw = next(item["raw"] for item in result if "raw" in item)
        assert "traceback" in raw[0]
        assert isinstance(raw[0]["traceback"], str)

    def test_error_structure_has_four_keys(self):
        """Error structure: [module, param, validation, raw] — no graphic/profile."""
        from modules.keybase.keybase_tasks import p_keybase

        with patch(
            "modules.keybase.keybase_tasks.requests.get",
            side_effect=RuntimeError("boom"),
        ):
            result = p_keybase("testuser")

        keys = [next(iter(item.keys())) for item in result if isinstance(item, dict)]
        assert keys == ["module", "param", "validation", "raw"]
        assert result[0]["module"] == "keybase"
        assert result[1]["param"] == "testuser"
        assert result[2]["validation"] == "not_used"

    def test_user_not_found_returns_fail_status(
        self, mock_keybase_api_not_found, mock_fontcheat
    ):
        """API returns them[0]=None → Fail with 'User not found'."""
        from modules.keybase.keybase_tasks import p_keybase

        result = p_keybase("ghostuser")

        raw = next(item["raw"] for item in result if "raw" in item)
        assert isinstance(raw, list)
        assert raw[0]["status"] == "Fail"
        assert raw[0]["reason"] == "User not found"


# ===========================================================================
# Backward compatibility
# ===========================================================================


class TestBackwardCompatibility:
    """Verify t_keybase alias works identically to p_keybase."""

    def test_t_keybase_is_same_as_p_keybase(self):
        from modules.keybase.keybase_tasks import p_keybase, t_keybase

        assert t_keybase is p_keybase

    def test_t_keybase_callable(
        self, mock_keybase_api, mock_fontcheat, mock_analize_rrss
    ):
        from modules.keybase.keybase_tasks import t_keybase

        result = t_keybase("testuser")
        assert isinstance(result, list)
        keys = [next(iter(item.keys())) for item in result if isinstance(item, dict)]
        assert "module" in keys

    def test_celery_task_name(self):
        """The registered Celery task name matches the MODULE_REGISTRY."""
        from modules.keybase.keybase_tasks import p_keybase

        assert hasattr(p_keybase, "name")
        assert p_keybase.name == "modules.keybase.keybase_tasks.t_keybase"


# ===========================================================================
# Dev-mode bypass (golden fixture)
# ===========================================================================


class TestDevModeGoldenFixture:
    """If an output file exists, it must be returned as-is with a 15s sleep."""

    def test_dev_mode_returns_golden_json(self, tmp_path):
        golden = [
            {"module": "keybase"},
            {"param": "devuser"},
            {"validation": "no"},
            {"raw": {}},
            {"graphic": []},
            {"profile": []},
            {"timeline": []},
        ]
        outputs = tmp_path / "outputs"
        outputs.mkdir()
        devfile = outputs / "output-keybase.json"
        devfile.write_text(json.dumps(golden))

        with (
            patch.object(Path, "cwd", return_value=tmp_path),
            patch("factories.task_wrapper.time.sleep") as mock_sleep,
        ):
            from modules.keybase.keybase_tasks import p_keybase

            result = p_keybase("anything")

        assert result == golden
        # keybase has dev_mode_sleep=15
        mock_sleep.assert_called_once_with(15)

    def test_dev_mode_sleep_is_15_via_task_name(self):
        """Decorator was applied — task name is registered, confirming config."""
        from modules.keybase.keybase_tasks import p_keybase

        assert hasattr(p_keybase, "name")
        assert p_keybase.name == "modules.keybase.keybase_tasks.t_keybase"


# ===========================================================================
# Proof state extraction
# ===========================================================================


class TestProofStateExtraction:
    """Verify proof state is included in social items when present."""

    def test_proof_with_state_includes_state_field(
        self, mock_fontcheat, mock_analize_rrss
    ):
        """Proof entry with state: 1 → social_item has 'state' key."""
        api_response = {
            "status": {"code": 0, "name": "OK"},
            "them": [
                {
                    "id": "abc123",
                    "basics": {"username": "testuser", "ctime": 0, "mtime": 0},
                    "profile": {},
                    "pictures": {},
                    "devices": {},
                    "proofs_summary": {
                        "all": [
                            {
                                "proof_type": "twitter",
                                "nametag": "user123",
                                "service_url": "https://twitter.com/user123",
                                "state": 1,
                            }
                        ]
                    },
                    "cryptocurrency_addresses": {},
                }
            ],
        }
        mock_response = MagicMock()
        mock_response.text = json.dumps(api_response)

        mock_html_resp = MagicMock()
        mock_html_resp.html.find.return_value = MagicMock(text="")
        mock_session = MagicMock()
        mock_session.get.return_value = mock_html_resp

        with (
            patch(
                "modules.keybase.keybase_tasks.requests.get",
                return_value=mock_response,
            ),
            patch(
                "modules.keybase.keybase_tasks.HTMLSession",
                return_value=mock_session,
            ),
        ):
            from modules.keybase.keybase_tasks import p_keybase

            result = p_keybase("testuser")

        graphic = next(item["graphic"] for item in result if "graphic" in item)
        keysocial = next(g["keysocial"] for g in graphic if "keysocial" in g)
        # Skip the root "KeybaseSocial" item (index 0), find twitter entry
        twitter_item = next(
            item for item in keysocial if item.get("name-node") == "keybasetwitter"
        )
        assert "state" in twitter_item
        assert twitter_item["state"] == 1

    def test_proof_without_state_omits_state_field(
        self, mock_fontcheat, mock_analize_rrss
    ):
        """Proof entry missing state → social_item has no 'state' key."""
        api_response = {
            "status": {"code": 0, "name": "OK"},
            "them": [
                {
                    "id": "abc123",
                    "basics": {"username": "testuser", "ctime": 0, "mtime": 0},
                    "profile": {},
                    "pictures": {},
                    "devices": {},
                    "proofs_summary": {
                        "all": [
                            {
                                "proof_type": "github",
                                "nametag": "user456",
                                "service_url": "https://github.com/user456",
                                # no "state" key
                            }
                        ]
                    },
                    "cryptocurrency_addresses": {},
                }
            ],
        }
        mock_response = MagicMock()
        mock_response.text = json.dumps(api_response)

        mock_html_resp = MagicMock()
        mock_html_resp.html.find.return_value = MagicMock(text="")
        mock_session = MagicMock()
        mock_session.get.return_value = mock_html_resp

        with (
            patch(
                "modules.keybase.keybase_tasks.requests.get",
                return_value=mock_response,
            ),
            patch(
                "modules.keybase.keybase_tasks.HTMLSession",
                return_value=mock_session,
            ),
        ):
            from modules.keybase.keybase_tasks import p_keybase

            result = p_keybase("testuser")

        graphic = next(item["graphic"] for item in result if "graphic" in item)
        keysocial = next(g["keysocial"] for g in graphic if "keysocial" in g)
        github_item = next(
            item for item in keysocial if item.get("name-node") == "keybasegithub"
        )
        assert "state" not in github_item


# ===========================================================================
# Data enrichment — new fields
# ===========================================================================


def _run_with_full_response(api_response):
    """Helper: run p_keybase with a given API response dict, mocking all I/O."""
    import json
    from unittest.mock import MagicMock, patch

    mock_response = MagicMock()
    mock_response.text = json.dumps(api_response)

    mock_html_resp = MagicMock()
    mock_html_resp.html.find.return_value = MagicMock(text="")
    mock_session = MagicMock()
    mock_session.get.return_value = mock_html_resp

    with (
        patch(
            "modules.keybase.keybase_tasks.requests.get",
            return_value=mock_response,
        ),
        patch(
            "modules.keybase.keybase_tasks.HTMLSession",
            return_value=mock_session,
        ),
        patch(
            "modules.keybase.keybase_tasks.search_icon_5",
            side_effect=lambda name: f"fas fa-{name}" if name else "fas fa-question",
        ),
        patch(
            "modules.keybase.keybase_tasks.analize_rrss",
            return_value={},
        ),
    ):
        from modules.keybase.keybase_tasks import p_keybase

        return p_keybase("testuser")


class TestPGPKeyMetadata:
    """Verify PGP key fields are extracted and added to graph/profile/timeline."""

    def test_pgp_fingerprint_in_graph(self, mock_fontcheat, mock_analize_rrss):
        result = _run_with_full_response(KEYBASE_API_RESPONSE)
        graphic = next(item["graphic"] for item in result if "graphic" in item)
        keygraph = next(g["keygraph"] for g in graphic if "keygraph" in g)
        fingerprint_item = next(
            (i for i in keygraph if i.get("name-node") == "GraphPGPFingerprint"), None
        )
        assert fingerprint_item is not None
        assert fingerprint_item["title"] == "PGP Fingerprint"
        assert (
            fingerprint_item["subtitle"] == "4475293306243408fa5958dc63847b4b83930f0c"
        )
        assert fingerprint_item["icon"] == "fas fa-fingerprint"

    def test_pgp_fingerprint_in_profile(self, mock_fontcheat, mock_analize_rrss):
        result = _run_with_full_response(KEYBASE_API_RESPONSE)
        profile = next(item["profile"] for item in result if "profile" in item)
        fp_item = next(
            (i for i in profile if isinstance(i, dict) and "key_fingerprint" in i),
            None,
        )
        assert fp_item is not None
        assert fp_item["key_fingerprint"] == "4475293306243408fa5958dc63847b4b83930f0c"

    def test_pgp_key_bits_in_graph(self, mock_fontcheat, mock_analize_rrss):
        result = _run_with_full_response(KEYBASE_API_RESPONSE)
        graphic = next(item["graphic"] for item in result if "graphic" in item)
        keygraph = next(g["keygraph"] for g in graphic if "keygraph" in g)
        keybits_item = next(
            (i for i in keygraph if i.get("name-node") == "GraphPGPKeyBits"), None
        )
        assert keybits_item is not None
        assert keybits_item["title"] == "PGP Key"
        # RSA algo (key_algo=1) → subtitle starts with "RSA"
        assert "RSA" in keybits_item["subtitle"]
        assert "4096" in keybits_item["subtitle"]

    def test_pgp_ctime_in_timeline(self, mock_fontcheat, mock_analize_rrss):
        result = _run_with_full_response(KEYBASE_API_RESPONSE)
        timeline = next(item["timeline"] for item in result if "timeline" in item)
        pgp_entry = next(
            (t for t in timeline if t.get("action") == "Keybase: PGP Key Created"),
            None,
        )
        assert pgp_entry is not None
        assert pgp_entry["icon"] == "fas fa-fingerprint"
        # ctime=1400000000 → "2014/..." — basic sanity check
        assert pgp_entry["date"].startswith("2014/")

    def test_pgp_key_url_in_profile(self, mock_fontcheat, mock_analize_rrss):
        result = _run_with_full_response(KEYBASE_API_RESPONSE)
        profile = next(item["profile"] for item in result if "profile" in item)
        url_item = next(
            (i for i in profile if isinstance(i, dict) and "pgp_key_url" in i),
            None,
        )
        assert url_item is not None
        assert url_item["pgp_key_url"] == "https://keybase.io/testuser/pgp_keys.asc"

    def test_pgp_missing_graceful(self, mock_fontcheat, mock_analize_rrss):
        """No public_keys in response → no crash, no PGP items in graph."""
        api = {
            "status": {"code": 0, "name": "OK"},
            "them": [
                {
                    "id": "x",
                    "basics": {"username": "u", "ctime": 0, "mtime": 0},
                    "profile": {},
                    "pictures": {},
                    "devices": {},
                    "proofs_summary": {"all": []},
                    "cryptocurrency_addresses": {},
                    # No public_keys key
                }
            ],
        }
        result = _run_with_full_response(api)
        graphic = next(item["graphic"] for item in result if "graphic" in item)
        keygraph_list = [g.get("keygraph", []) for g in graphic if "keygraph" in g]
        all_graph_items = keygraph_list[0] if keygraph_list else []
        # Should not contain PGP items
        pgp_item = next(
            (
                i
                for i in all_graph_items
                if i.get("name-node") in ("GraphPGPFingerprint", "GraphPGPKeyBits")
            ),
            None,
        )
        assert pgp_item is None


class TestTrackVersionGraphItem:
    """Verify track_version appears as 'Trackers' graph item."""

    def test_track_version_in_graph(self, mock_fontcheat, mock_analize_rrss):
        result = _run_with_full_response(KEYBASE_API_RESPONSE)
        graphic = next(item["graphic"] for item in result if "graphic" in item)
        keygraph = next(g["keygraph"] for g in graphic if "keygraph" in g)
        trackers_item = next(
            (i for i in keygraph if i.get("name-node") == "GraphTrackers"), None
        )
        assert trackers_item is not None
        assert trackers_item["title"] == "Trackers"
        assert trackers_item["subtitle"] == "673"
        assert trackers_item["icon"] == "fas fa-user-check"

    def test_track_version_missing_no_crash(self, mock_fontcheat, mock_analize_rrss):
        """Missing track_version → no 'Trackers' graph item, no crash."""
        api = {
            "status": {"code": 0, "name": "OK"},
            "them": [
                {
                    "id": "x",
                    "basics": {"username": "u", "ctime": 0, "mtime": 0},
                    # no track_version
                    "profile": {},
                    "pictures": {},
                    "devices": {},
                    "proofs_summary": {"all": []},
                    "cryptocurrency_addresses": {},
                }
            ],
        }
        result = _run_with_full_response(api)
        graphic = next(item["graphic"] for item in result if "graphic" in item)
        keygraph_list = [g.get("keygraph", []) for g in graphic if "keygraph" in g]
        all_graph_items = keygraph_list[0] if keygraph_list else []
        trackers = next(
            (i for i in all_graph_items if i.get("name-node") == "GraphTrackers"), None
        )
        assert trackers is None


class TestSeqnoGraphItem:
    """Verify sigs.last.seqno appears as 'Signature Chain' graph item."""

    def test_seqno_in_graph(self, mock_fontcheat, mock_analize_rrss):
        result = _run_with_full_response(KEYBASE_API_RESPONSE)
        graphic = next(item["graphic"] for item in result if "graphic" in item)
        keygraph = next(g["keygraph"] for g in graphic if "keygraph" in g)
        sig_item = next(
            (i for i in keygraph if i.get("name-node") == "GraphSigChain"), None
        )
        assert sig_item is not None
        assert sig_item["title"] == "Signature Chain"
        assert sig_item["subtitle"] == "841"
        assert sig_item["icon"] == "fas fa-link"

    def test_seqno_missing_no_crash(self, mock_fontcheat, mock_analize_rrss):
        """Missing sigs → no 'Signature Chain' item, no crash."""
        api = {
            "status": {"code": 0, "name": "OK"},
            "them": [
                {
                    "id": "x",
                    "basics": {"username": "u", "ctime": 0, "mtime": 0},
                    "profile": {},
                    "pictures": {},
                    "devices": {},
                    "proofs_summary": {"all": []},
                    "cryptocurrency_addresses": {},
                    # no sigs key
                }
            ],
        }
        result = _run_with_full_response(api)
        graphic = next(item["graphic"] for item in result if "graphic" in item)
        keygraph_list = [g.get("keygraph", []) for g in graphic if "keygraph" in g]
        all_graph_items = keygraph_list[0] if keygraph_list else []
        sig_item = next(
            (i for i in all_graph_items if i.get("name-node") == "GraphSigChain"), None
        )
        assert sig_item is None


class TestMultiCryptocurrency:
    """Verify all cryptocurrency types are extracted, not just bitcoin."""

    def test_bitcoin_extracted(self, mock_fontcheat, mock_analize_rrss):
        result = _run_with_full_response(KEYBASE_API_RESPONSE)
        graphic = next(item["graphic"] for item in result if "graphic" in item)
        keysocial = next(g["keysocial"] for g in graphic if "keysocial" in g)
        btc_item = next(
            (i for i in keysocial if i.get("name-node") == "keybaseBITCOIN"), None
        )
        assert btc_item is not None
        assert btc_item["icon"] == "fab fa-btc"
        assert btc_item["subtitle"] == "1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2"

    def test_ethereum_extracted(self, mock_fontcheat, mock_analize_rrss):
        result = _run_with_full_response(KEYBASE_API_RESPONSE)
        graphic = next(item["graphic"] for item in result if "graphic" in item)
        keysocial = next(g["keysocial"] for g in graphic if "keysocial" in g)
        eth_item = next(
            (i for i in keysocial if i.get("name-node") == "keybaseETHEREUM"), None
        )
        assert eth_item is not None
        assert eth_item["icon"] == "fab fa-ethereum"
        assert eth_item["subtitle"] == "0xAbCdEf1234567890"

    def test_unknown_crypto_uses_generic_icon(self, mock_fontcheat, mock_analize_rrss):
        """Unknown cryptocurrency type gets 'fas fa-coins' icon."""
        api = {
            "status": {"code": 0, "name": "OK"},
            "them": [
                {
                    "id": "x",
                    "basics": {"username": "u", "ctime": 0, "mtime": 0},
                    "profile": {},
                    "pictures": {},
                    "devices": {},
                    "proofs_summary": {"all": []},
                    "cryptocurrency_addresses": {
                        "zcash": [{"address": "zcash_addr_abc"}]
                    },
                }
            ],
        }
        result = _run_with_full_response(api)
        graphic = next(item["graphic"] for item in result if "graphic" in item)
        keysocial = next(g["keysocial"] for g in graphic if "keysocial" in g)
        zcash_item = next(
            (i for i in keysocial if i.get("name-node") == "keybaseZCASH"), None
        )
        assert zcash_item is not None
        assert zcash_item["icon"] == "fas fa-coins"

    def test_empty_crypto_addresses_no_items(self, mock_fontcheat, mock_analize_rrss):
        """Empty cryptocurrency_addresses → no social items added."""
        api = {
            "status": {"code": 0, "name": "OK"},
            "them": [
                {
                    "id": "x",
                    "basics": {"username": "u", "ctime": 0, "mtime": 0},
                    "profile": {},
                    "pictures": {},
                    "devices": {},
                    "proofs_summary": {"all": []},
                    "cryptocurrency_addresses": {},
                }
            ],
        }
        result = _run_with_full_response(api)
        graphic = next(item["graphic"] for item in result if "graphic" in item)
        # No keysocial section should exist (only 1 item = root KeybaseSocial)
        keysocial_sections = [g for g in graphic if "keysocial" in g]
        assert len(keysocial_sections) == 0


class TestProofURLEnrichment:
    """Verify human_url and proof_url are added to social items when present."""

    def test_human_url_added_to_social_item(self, mock_fontcheat, mock_analize_rrss):
        result = _run_with_full_response(KEYBASE_API_RESPONSE)
        graphic = next(item["graphic"] for item in result if "graphic" in item)
        keysocial = next(g["keysocial"] for g in graphic if "keysocial" in g)
        twitter_item = next(
            i for i in keysocial if i.get("name-node") == "keybasetwitter"
        )
        assert "url" in twitter_item
        assert twitter_item["url"] == "https://twitter.com/testuser_tw/status/123"

    def test_proof_url_added_to_social_item(self, mock_fontcheat, mock_analize_rrss):
        result = _run_with_full_response(KEYBASE_API_RESPONSE)
        graphic = next(item["graphic"] for item in result if "graphic" in item)
        keysocial = next(g["keysocial"] for g in graphic if "keysocial" in g)
        twitter_item = next(
            i for i in keysocial if i.get("name-node") == "keybasetwitter"
        )
        assert "proof_url" in twitter_item
        assert twitter_item["proof_url"] == "https://keybase.io/testuser/sigs/abc"

    def test_missing_urls_not_added(self, mock_fontcheat, mock_analize_rrss):
        """Proof without human_url/proof_url → no url fields on social item."""
        result = _run_with_full_response(KEYBASE_API_RESPONSE)
        graphic = next(item["graphic"] for item in result if "graphic" in item)
        keysocial = next(g["keysocial"] for g in graphic if "keysocial" in g)
        github_item = next(
            i for i in keysocial if i.get("name-node") == "keybasegithub"
        )
        assert "url" not in github_item
        assert "proof_url" not in github_item


class TestDeviceKeyCounts:
    """Verify sibkeys/subkeys counts appear as graph items."""

    def test_signing_keys_in_graph(self, mock_fontcheat, mock_analize_rrss):
        result = _run_with_full_response(KEYBASE_API_RESPONSE)
        graphic = next(item["graphic"] for item in result if "graphic" in item)
        keygraph = next(g["keygraph"] for g in graphic if "keygraph" in g)
        signing_item = next(
            (i for i in keygraph if i.get("name-node") == "GraphSigningKeys"), None
        )
        assert signing_item is not None
        assert signing_item["title"] == "Signing Keys"
        assert signing_item["subtitle"] == "2"  # two sibkeys in fixture
        assert signing_item["icon"] == "fas fa-pen-nib"

    def test_encryption_keys_in_graph(self, mock_fontcheat, mock_analize_rrss):
        result = _run_with_full_response(KEYBASE_API_RESPONSE)
        graphic = next(item["graphic"] for item in result if "graphic" in item)
        keygraph = next(g["keygraph"] for g in graphic if "keygraph" in g)
        enc_item = next(
            (i for i in keygraph if i.get("name-node") == "GraphEncryptionKeys"), None
        )
        assert enc_item is not None
        assert enc_item["title"] == "Encryption Keys"
        assert enc_item["subtitle"] == "1"  # one subkey in fixture
        assert enc_item["icon"] == "fas fa-lock"

    def test_empty_keys_no_items(self, mock_fontcheat, mock_analize_rrss):
        """Empty sibkeys/subkeys → no signing/encryption graph items."""
        api = {
            "status": {"code": 0, "name": "OK"},
            "them": [
                {
                    "id": "x",
                    "basics": {"username": "u", "ctime": 0, "mtime": 0},
                    "profile": {},
                    "pictures": {},
                    "devices": {},
                    "proofs_summary": {"all": []},
                    "cryptocurrency_addresses": {},
                    "public_keys": {
                        "primary": {},
                        "sibkeys": {},
                        "subkeys": {},
                    },
                }
            ],
        }
        result = _run_with_full_response(api)
        graphic = next(item["graphic"] for item in result if "graphic" in item)
        keygraph_list = [g.get("keygraph", []) for g in graphic if "keygraph" in g]
        all_graph_items = keygraph_list[0] if keygraph_list else []
        for node_name in ("GraphSigningKeys", "GraphEncryptionKeys"):
            item = next(
                (i for i in all_graph_items if i.get("name-node") == node_name), None
            )
            assert item is None
