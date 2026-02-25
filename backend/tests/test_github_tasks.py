"""Tests for backend/modules/github/github_tasks.py - p_github processor."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

GITHUB_USER_RESPONSE = {
    "login": "testuser",
    "id": 12345,
    "name": "Test User",
    "email": "test@example.com",
    "company": "TestCorp",
    "blog": "https://testuser.dev",
    "location": "Buenos Aires, Argentina",
    "bio": "Developer. github: @testuser",
    "twitter_username": "testuser_tw",
    "public_repos": 42,
    "public_gists": 5,
    "followers": 100,
    "following": 50,
    "avatar_url": "https://avatars.githubusercontent.com/u/12345",
    "created_at": "2020-01-15T10:30:00Z",
    "updated_at": "2024-06-01T14:00:00Z",
    "type": "User",
}

GITHUB_HTML_RESPONSE = """
<html><body>
<div class="graph-before-activity-overview">
<span style="width: 11px">contrib</span>
</div>
</body></html>
"""

GITHUB_NOT_FOUND = {"message": "Not Found"}


# ---------------------------------------------------------------------------
# Dev-mode bypass guard
# ---------------------------------------------------------------------------
# p_github reads Path.cwd() / "outputs" / "output-github.json" and, when it
# exists, returns canned data instead of hitting the API.  We patch Path.cwd
# to point at a tmp directory so the dev-mode file can never be found.  This
# is an autouse session-scoped fixture so every test exercises the real
# API-processing logic.
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _block_devmode_file(tmp_path):
    """Ensure the dev-mode JSON file is never found during tests.

    Patches ``Path.cwd`` to return *tmp_path* (which has no ``outputs/``
    directory), so ``Path.cwd() / "outputs" / "output-github.json"``
    resolves to a non-existent path.
    """
    with patch.object(Path, "cwd", return_value=tmp_path):
        yield


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_github_api():
    """Mock requests.get for GitHub API and HTML scraping."""
    with patch("modules.github.github_tasks.requests") as mock_requests:
        api_response = MagicMock()
        api_response.json.return_value = GITHUB_USER_RESPONSE.copy()
        api_response.text = json.dumps(GITHUB_USER_RESPONSE)

        html_response = MagicMock()
        html_response.content = GITHUB_HTML_RESPONSE.encode()

        def side_effect(url, *args, **kwargs):
            if "api.github.com" in url:
                return api_response
            return html_response

        mock_requests.get.side_effect = side_effect
        yield mock_requests


@pytest.fixture
def mock_github_not_found():
    """Mock requests.get to return 'Not Found'."""
    with patch("modules.github.github_tasks.requests") as mock_requests:
        response = MagicMock()
        response.json.return_value = GITHUB_NOT_FOUND.copy()
        response.text = json.dumps(GITHUB_NOT_FOUND)
        mock_requests.get.return_value = response
        yield mock_requests


@pytest.fixture
def mock_location_geo():
    """Mock location_geo to avoid real geocoding calls."""
    with patch("modules.github.github_tasks.location_geo") as mock_geo:
        mock_geo.return_value = {
            "Caption": "Buenos Aires, Argentina",
            "Accessibility": "place",
            "Latitude": -34.6037,
            "Longitude": -58.3816,
            "Name": "Buenos Aires",
            "Time": "",
        }
        yield mock_geo


# ===================================================================
# p_github tests
# ===================================================================


class TestPGithub:
    """Tests for the p_github processing function."""

    def test_basic_output_structure(self, mock_github_api, mock_location_geo):
        from modules.github.github_tasks import p_github

        result = p_github("testuser", "Initial")

        assert isinstance(result, list)
        keys = [next(iter(item.keys())) for item in result if isinstance(item, dict)]
        assert "module" in keys
        assert "param" in keys
        assert "validation" in keys
        assert "graphic" in keys
        assert "profile" in keys
        assert "timeline" in keys

    def test_validation_initial(self, mock_github_api, mock_location_geo):
        from modules.github.github_tasks import p_github

        result = p_github("testuser", "Initial")
        validation = next(item["validation"] for item in result if "validation" in item)
        assert validation == "no"

    def test_validation_non_initial(self, mock_github_api, mock_location_geo):
        from modules.github.github_tasks import p_github

        result = p_github("testuser", "github")
        validation = next(item["validation"] for item in result if "validation" in item)
        assert validation == "soft"

    def test_not_found_raises(self, mock_github_not_found):
        from modules.github.github_tasks import p_github

        with pytest.raises(Exception, match="User not found"):
            p_github("nonexistent_user")

    def test_email_from_at_sign(self, mock_github_api, mock_location_geo):
        """When input contains @, username is extracted from email prefix."""
        from modules.github.github_tasks import p_github

        result = p_github("testuser@example.com", "Initial")
        param = next(item["param"] for item in result if "param" in item)
        assert param == "testuser"

    # ---------------------------------------------------------------
    # Dev-mode bypass verification
    # ---------------------------------------------------------------

    def test_devmode_file_is_bypassed(
        self, tmp_path, mock_github_api, mock_location_geo
    ):
        """When output-github.json exists, p_github returns file data.

        Verify the autouse fixture prevents this: even though the
        test creates a valid JSON file, the patched cwd() points
        elsewhere so p_github still hits the (mocked) API.
        """
        from modules.github.github_tasks import p_github

        # Create a decoy file in the real tmp_path/outputs dir.
        # Because _block_devmode_file already patches cwd to tmp_path,
        # we create the file in a *different* subdir to prove it has
        # no effect.
        decoy = tmp_path / "other" / "outputs" / "output-github.json"
        decoy.parent.mkdir(parents=True, exist_ok=True)
        decoy.write_text(json.dumps([{"decoy": True}]))

        result = p_github("testuser", "Initial")

        # The result must come from the mocked API, not the file.
        keys = [next(iter(item.keys())) for item in result if isinstance(item, dict)]
        assert "graphic" in keys
        assert "decoy" not in keys

    def test_devmode_file_returns_file_data_when_present(self, tmp_path):
        """If cwd contains the dev-mode file, p_github returns it.

        This proves the dev-mode path works and confirms that the
        autouse fixture is necessary for the other tests.
        """
        from modules.github.github_tasks import p_github

        # Create the dev-mode file in the location cwd() resolves to.
        # The autouse fixture patches cwd to tmp_path, so write there.
        outputs_dir = tmp_path / "outputs"
        outputs_dir.mkdir()
        devfile = outputs_dir / "output-github.json"
        canned = [{"module": "github"}, {"canned": True}]
        devfile.write_text(json.dumps(canned))

        result = p_github("anything")

        assert result == canned

    # ---------------------------------------------------------------
    # Edge cases
    # ---------------------------------------------------------------

    def test_empty_username(self, mock_github_not_found):
        """Empty string still hits the API and raises on Not Found."""
        from modules.github.github_tasks import p_github

        with pytest.raises(Exception, match="User not found"):
            p_github("")

    def test_api_returns_unexpected_structure(self):
        """When the API returns data without 'login' key, it raises."""
        from modules.github.github_tasks import p_github

        bad_data = {"id": 999, "type": "User"}
        with patch("modules.github.github_tasks.requests") as mock_req:
            api_resp = MagicMock()
            api_resp.json.return_value = bad_data
            api_resp.text = json.dumps(bad_data)

            html_resp = MagicMock()
            html_resp.content = GITHUB_HTML_RESPONSE.encode()

            def se(url, *a, **kw):
                if "api.github.com" in url:
                    return api_resp
                return html_resp

            mock_req.get.side_effect = se

            # No 'login' key -> KeyError at raw_node["login"]
            with pytest.raises(KeyError):
                p_github("baduser")


# ===================================================================
# t_github error-path tests
# ===================================================================


class TestTGithubErrorPaths:
    """Tests for the t_github Celery task error handling wrapper."""

    def test_iky_prefixed_exception_returns_warning(self):
        """Exception starting with 'iKy - ' yields status 'Warning'."""
        from modules.github.github_tasks import t_github

        with patch(
            "modules.github.github_tasks.p_github",
            side_effect=Exception("iKy - User not found"),
        ):
            result = t_github("nobody")

        raw = next(item["raw"] for item in result if "raw" in item)
        assert raw[0]["status"] == "Warning"
        assert raw[0]["reason"] == "User not found"

    def test_generic_exception_returns_fail(self):
        """Non-iKy exception yields status 'Fail'."""
        from modules.github.github_tasks import t_github

        with patch(
            "modules.github.github_tasks.p_github",
            side_effect=RuntimeError("connection timeout"),
        ):
            result = t_github("nobody")

        raw = next(item["raw"] for item in result if "raw" in item)
        assert raw[0]["status"] == "Fail"
        assert raw[0]["reason"] == "connection timeout"

    def test_error_response_structure(self):
        """Error response has module, param, validation, raw keys."""
        from modules.github.github_tasks import t_github

        with patch(
            "modules.github.github_tasks.p_github",
            side_effect=Exception("boom"),
        ):
            result = t_github("user@test.com")

        keys = [next(iter(item.keys())) for item in result if isinstance(item, dict)]
        assert keys == ["module", "param", "validation", "raw"]

        module = next(item["module"] for item in result if "module" in item)
        assert module == "github"

        param = next(item["param"] for item in result if "param" in item)
        assert param == "user@test.com"

        validation = next(item["validation"] for item in result if "validation" in item)
        assert validation == "not_used"

    def test_error_response_includes_traceback(self):
        """Error response raw node includes a traceback string."""
        from modules.github.github_tasks import t_github

        with patch(
            "modules.github.github_tasks.p_github",
            side_effect=ValueError("test error"),
        ):
            result = t_github("someone")

        raw = next(item["raw"] for item in result if "raw" in item)
        assert "traceback" in raw[0]
        assert "ValueError" in raw[0]["traceback"]

    def test_successful_call_returns_p_github_result(
        self, mock_github_api, mock_location_geo
    ):
        """When p_github succeeds, t_github returns its result."""
        from modules.github.github_tasks import t_github

        result = t_github("testuser", "Initial")

        keys = [next(iter(item.keys())) for item in result if isinstance(item, dict)]
        # Successful result has graphic, profile, etc.
        assert "graphic" in keys
        assert "profile" in keys
