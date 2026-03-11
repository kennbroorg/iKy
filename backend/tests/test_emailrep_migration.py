"""Regression tests for emailrep migration to @iky_task decorator.

Verifies that the migrated p_emailrep (now a Celery task via @iky_task)
produces output structurally identical to the old t_emailrep wrapper.
"""

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
