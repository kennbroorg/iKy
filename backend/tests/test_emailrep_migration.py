"""Regression tests for emailrep migration to @iky_task decorator.

Verifies that the migrated p_emailrep (now a Celery task via @iky_task)
produces output structurally identical to the old t_emailrep wrapper.
"""

import copy
import inspect
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Ensure the ``emailrep`` and ``fontawesome`` third-party packages can be
# resolved even when not installed locally (Docker-only deps).  We inject
# lightweight stubs into sys.modules *before* importing the module under test.
# ---------------------------------------------------------------------------

_emailrep_stub = MagicMock()
_fontawesome_stub = MagicMock()
_fontawesome_stub.icons = {}

if "emailrep" not in sys.modules:
    sys.modules["emailrep"] = _emailrep_stub
if "fontawesome" not in sys.modules:
    sys.modules["fontawesome"] = _fontawesome_stub


# ---------------------------------------------------------------------------
# Block dev-mode file globally for this test module
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _block_devmode(tmp_path):
    """Redirect Path.cwd() so dev-mode files are never found."""
    with patch.object(Path, "cwd", return_value=tmp_path):
        yield


# ---------------------------------------------------------------------------
# Mock the EmailRep library so no real API calls are made
# ---------------------------------------------------------------------------

EMAILREP_RESPONSE = {
    "email": "test@example.com",
    "reputation": "high",
    "suspicious": False,
    "references": 10,
    "details": {
        "blacklisted": False,
        "malicious_activity": False,
        "credentials_leaked": True,
        "data_breach": True,
        "free_provider": True,
        "spam": False,
        "disposable": False,
        "valid_mx": True,
        "spoofable": False,
        "suspicious_tld": False,
        "profiles": ["twitter", "linkedin"],
    },
}


@pytest.fixture
def mock_emailrep_api():
    """Mock the EmailRep library query method."""
    mock_rep_instance = MagicMock()
    mock_rep_instance.query.return_value = EMAILREP_RESPONSE.copy()

    with patch(
        "modules.emailrep.emailrep_tasks.EmailRep",
        return_value=mock_rep_instance,
    ) as mock_cls:
        yield mock_cls


@pytest.fixture
def mock_api_key_found():
    """Mock api_keys_search to return a valid key."""
    with patch(
        "modules.emailrep.emailrep_tasks.api_keys_search",
        return_value="fake-key-123",
    ):
        yield


@pytest.fixture
def mock_api_key_missing():
    """Mock api_keys_search to return False (no key configured)."""
    with patch(
        "modules.emailrep.emailrep_tasks.api_keys_search",
        return_value=False,
    ):
        yield


@pytest.fixture
def mock_fontcheat():
    """Mock search_icon_5 to return a predictable icon."""
    with patch(
        "modules.emailrep.emailrep_tasks.search_icon_5",
        side_effect=lambda name: f"fas fa-{name}",
    ):
        yield


# ===========================================================================
# Output structure tests (the "shape" must match the old t_emailrep)
# ===========================================================================


class TestEmailrepOutputStructure:
    """Verify p_emailrep output matches the original t_emailrep contract."""

    def test_success_output_has_required_keys(
        self, mock_emailrep_api, mock_api_key_found, mock_fontcheat
    ):
        from modules.emailrep.emailrep_tasks import p_emailrep

        result = p_emailrep("test@example.com")

        assert isinstance(result, list)
        keys = [next(iter(item.keys())) for item in result if isinstance(item, dict)]
        # The original successful output always has these keys in order:
        # module, param, validation, raw, graphic, profile, timeline
        assert "module" in keys
        assert "param" in keys
        assert "validation" in keys
        assert "raw" in keys
        assert "graphic" in keys
        assert "profile" in keys
        assert "timeline" in keys

    def test_module_field_is_emailrep(
        self, mock_emailrep_api, mock_api_key_found, mock_fontcheat
    ):
        from modules.emailrep.emailrep_tasks import p_emailrep

        result = p_emailrep("test@example.com")
        module = next(item["module"] for item in result if "module" in item)
        assert module == "emailrep"

    def test_param_matches_input(
        self, mock_emailrep_api, mock_api_key_found, mock_fontcheat
    ):
        from modules.emailrep.emailrep_tasks import p_emailrep

        result = p_emailrep("user@domain.com")
        param = next(item["param"] for item in result if "param" in item)
        assert param == "user@domain.com"

    def test_validation_is_hard(
        self, mock_emailrep_api, mock_api_key_found, mock_fontcheat
    ):
        from modules.emailrep.emailrep_tasks import p_emailrep

        result = p_emailrep("test@example.com")
        validation = next(item["validation"] for item in result if "validation" in item)
        assert validation == "hard"

    def test_raw_contains_emailrep_response(
        self, mock_emailrep_api, mock_api_key_found, mock_fontcheat
    ):
        from modules.emailrep.emailrep_tasks import p_emailrep

        result = p_emailrep("test@example.com")
        raw = next(item["raw"] for item in result if "raw" in item)
        # Raw should be the API response dict (not a list)
        assert isinstance(raw, dict)
        assert raw["reputation"] == "high"


# ===========================================================================
# Error path tests (via the decorator wrapping)
# ===========================================================================


class TestEmailrepErrorPaths:
    """Verify error handling matches the original t_emailrep behavior."""

    def test_missing_key_returns_warning(self, mock_api_key_missing):
        """Missing API key raises 'iKy - ...' -> Warning status."""
        from modules.emailrep.emailrep_tasks import p_emailrep

        result = p_emailrep("test@example.com")

        raw = next(item["raw"] for item in result if "raw" in item)
        assert isinstance(raw, list)
        assert raw[0]["status"] == "Warning"
        assert raw[0]["reason"] == "Missing or invalid Key"

    def test_missing_key_error_structure(self, mock_api_key_missing):
        """Error structure: [module, param, validation, raw]."""
        from modules.emailrep.emailrep_tasks import p_emailrep

        result = p_emailrep("test@example.com")

        keys = [next(iter(item.keys())) for item in result if isinstance(item, dict)]
        assert keys == ["module", "param", "validation", "raw"]
        assert result[0]["module"] == "emailrep"
        assert result[1]["param"] == "test@example.com"
        assert result[2]["validation"] == "not_used"

    def test_generic_exception_returns_fail(self, mock_api_key_found):
        """Non-iKy exception -> Fail status."""
        from modules.emailrep.emailrep_tasks import p_emailrep

        with patch(
            "modules.emailrep.emailrep_tasks.EmailRep",
            side_effect=RuntimeError("network down"),
        ):
            result = p_emailrep("test@example.com")

        raw = next(item["raw"] for item in result if "raw" in item)
        assert raw[0]["status"] == "Fail"
        assert raw[0]["reason"] == "network down"

    def test_error_includes_traceback(self, mock_api_key_missing):
        from modules.emailrep.emailrep_tasks import p_emailrep

        result = p_emailrep("test@example.com")

        raw = next(item["raw"] for item in result if "raw" in item)
        assert "traceback" in raw[0]
        assert "iKy - Missing or invalid Key" in raw[0]["traceback"]


# ===========================================================================
# Backward compatibility
# ===========================================================================


class TestBackwardCompatibility:
    """Verify t_emailrep alias works identically to p_emailrep."""

    def test_t_emailrep_is_same_as_p_emailrep(self):
        from modules.emailrep.emailrep_tasks import p_emailrep, t_emailrep

        assert t_emailrep is p_emailrep

    def test_t_emailrep_callable(
        self, mock_emailrep_api, mock_api_key_found, mock_fontcheat
    ):
        from modules.emailrep.emailrep_tasks import t_emailrep

        result = t_emailrep("test@example.com")
        assert isinstance(result, list)
        keys = [next(iter(item.keys())) for item in result if isinstance(item, dict)]
        assert "module" in keys

    def test_celery_task_name(self):
        """The registered Celery task name matches the MODULE_REGISTRY."""
        from modules.emailrep.emailrep_tasks import p_emailrep

        assert hasattr(p_emailrep, "name")
        assert p_emailrep.name == "modules.emailrep.emailrep_tasks.t_emailrep"


# ===========================================================================
# Dev-mode bypass (golden fixture)
# ===========================================================================


class TestDevModeGoldenFixture:
    """If an output file exists, verify it's returned as-is."""

    def test_dev_mode_returns_golden_json(self, tmp_path):
        golden = [
            {"module": "emailrep"},
            {"param": "golden@test.com"},
            {"validation": "hard"},
            {"raw": {"reputation": "high"}},
            {"graphic": []},
            {"profile": []},
            {"timeline": []},
        ]
        outputs = tmp_path / "outputs"
        outputs.mkdir()
        devfile = outputs / "output-emailrep.json"
        devfile.write_text(json.dumps(golden))

        with (
            patch.object(Path, "cwd", return_value=tmp_path),
            patch("factories.task_wrapper.time.sleep") as mock_sleep,
        ):
            from modules.emailrep.emailrep_tasks import p_emailrep

            result = p_emailrep("anything")

        assert result == golden
        # emailrep has dev_mode_sleep=15
        mock_sleep.assert_called_once_with(15)


# ===========================================================================
# Refactor verification tests (blacklisted bug fix, signature, consistency)
# ===========================================================================


def _find_gather_item(result, title):
    """Find a gather item by title in the graphic details list."""
    graphic = next(item["graphic"] for item in result if "graphic" in item)
    details = graphic[0]["details"]
    return next(item for item in details if item["title"] == title)


class TestEmailrepRefactor:
    """Verify the emailrep-refactor changes: icon bug fix, signature, structure."""

    def test_blacklisted_true_shows_thumbs_down(
        self, mock_api_key_found, mock_fontcheat
    ):
        """Blacklisted=True MUST produce thumbs-down (bug fix verification)."""
        from modules.emailrep.emailrep_tasks import p_emailrep

        response = copy.deepcopy(EMAILREP_RESPONSE)
        response["details"]["blacklisted"] = True

        mock_rep = MagicMock()
        mock_rep.query.return_value = response

        with patch(
            "modules.emailrep.emailrep_tasks.EmailRep",
            return_value=mock_rep,
        ):
            result = p_emailrep("test@example.com")

        item = _find_gather_item(result, "Blacklisted")
        assert item["icon"] == "fas fa-thumbs-down"

    def test_blacklisted_false_shows_thumbs_up(
        self, mock_emailrep_api, mock_api_key_found, mock_fontcheat
    ):
        """Blacklisted=False MUST produce thumbs-up."""
        from modules.emailrep.emailrep_tasks import p_emailrep

        result = p_emailrep("test@example.com")

        item = _find_gather_item(result, "Blacklisted")
        assert item["icon"] == "fas fa-thumbs-up"

    def test_output_positional_structure(
        self, mock_emailrep_api, mock_api_key_found, mock_fontcheat
    ):
        """Output array must be positionally correct per contract."""
        from modules.emailrep.emailrep_tasks import p_emailrep

        result = p_emailrep("test@example.com")

        assert "module" in result[0] and result[0]["module"] == "emailrep"
        assert "param" in result[1]
        assert "validation" in result[2] and result[2]["validation"] == "hard"
        assert "raw" in result[3]
        assert "graphic" in result[4]
        assert "profile" in result[5]
        assert "timeline" in result[6]

    def test_signature_no_from_m(self):
        """p_emailrep must accept only 'username' — no 'from_m' parameter."""
        from modules.emailrep.emailrep_tasks import p_emailrep

        sig = inspect.signature(p_emailrep)
        param_names = list(sig.parameters.keys())
        assert param_names == ["username"]

    def test_bool_icon_consistency(self, mock_api_key_found, mock_fontcheat):
        """All 'bad' boolean fields set to True must produce thumbs-down."""
        from modules.emailrep.emailrep_tasks import p_emailrep

        bad_fields = {
            "blacklisted": "Blacklisted",
            "malicious_activity": "Malicious Activity",
            "credentials_leaked": "Credentials Leaked",
            "data_breach": "Data Breach",
            "spam": "Spam",
            "disposable": "Disposable or Temporary",
            "spoofable": "Spoofable",
            "suspicious_tld": "Suspicious TLD",
        }

        response = copy.deepcopy(EMAILREP_RESPONSE)
        for field in bad_fields:
            response["details"][field] = True

        mock_rep = MagicMock()
        mock_rep.query.return_value = response

        with patch(
            "modules.emailrep.emailrep_tasks.EmailRep",
            return_value=mock_rep,
        ):
            result = p_emailrep("test@example.com")

        for field_key, title in bad_fields.items():
            item = _find_gather_item(result, title)
            assert item["icon"] == "fas fa-thumbs-down", (
                f"{title} (field={field_key}) should be thumbs-down when True"
            )
