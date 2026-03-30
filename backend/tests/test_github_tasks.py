"""Tests for backend/modules/github/github_tasks.py — p_github processor."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Test fixtures / shared data
# ---------------------------------------------------------------------------

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
    "hireable": True,
    "public_repos": 42,
    "public_gists": 5,
    "followers": 100,
    "following": 50,
    "avatar_url": "https://avatars.githubusercontent.com/u/12345",
    "created_at": "2020-01-15T10:30:00Z",
    "updated_at": "2024-06-01T14:00:00Z",
    "type": "User",
}

GITHUB_REPOS_RESPONSE = [
    {
        "name": "awesome-project",
        "description": "A great project",
        "language": "Python",
        "stargazers_count": 50,
        "forks_count": 10,
        "topics": ["osint", "python"],
        "fork": False,
        "created_at": "2021-06-01T00:00:00Z",
    },
    {
        "name": "another-repo",
        "description": "Another one",
        "language": "JavaScript",
        "stargazers_count": 20,
        "forks_count": 3,
        "topics": [],
        "fork": False,
        "created_at": "2022-03-15T00:00:00Z",
    },
    {
        "name": "forked-thing",
        "description": "Not mine",
        "language": "Go",
        "stargazers_count": 5,
        "forks_count": 1,
        "topics": [],
        "fork": True,
        "created_at": "2023-01-01T00:00:00Z",
    },
]

GITHUB_SOCIAL_ACCOUNTS_RESPONSE = [
    {"provider": "twitter", "url": "https://twitter.com/testuser_tw"},
    {"provider": "linkedin", "url": "https://linkedin.com/in/testuser"},
]

GITHUB_ORGS_RESPONSE = [
    {
        "login": "testorg",
        "avatar_url": "https://avatars.githubusercontent.com/u/99999",
        "description": "Test Organization",
        "url": "https://api.github.com/orgs/testorg",
    }
]

GITHUB_KEYS_RESPONSE = [
    {
        "id": 7890,
        "key": "ssh-rsa AAAAB3Nza...",
        "created_at": "2021-03-01T00:00:00Z",
    }
]

GITHUB_GISTS_RESPONSE = [
    {
        "description": "My useful script",
        "created_at": "2022-05-10T12:00:00Z",
        "updated_at": "2022-06-01T08:00:00Z",
        "public": True,
    },
    {
        "description": "",
        "created_at": "2023-01-20T09:30:00Z",
        "updated_at": "2023-01-20T09:30:00Z",
        "public": False,
    },
]

# New HTML calendar table format (GitHub migrated from SVG to HTML table)
GITHUB_HTML_RESPONSE = """
<html><body>
<div class="js-yearly-contributions">
  <table class="ContributionCalendar-grid js-calendar-graph-table">
    <tbody>
      <tr>
        <td data-date="2025-01-01" data-level="0" class="ContributionCalendar-day"></td>
        <td data-date="2025-01-02" data-level="2" class="ContributionCalendar-day"></td>
        <td data-date="2025-01-03" data-level="4" class="ContributionCalendar-day"></td>
      </tr>
    </tbody>
  </table>
</div>
</body></html>
"""

GITHUB_NOT_FOUND = {"message": "Not Found"}


# ---------------------------------------------------------------------------
# Dev-mode bypass guard
# ---------------------------------------------------------------------------
# p_github (via @iky_task) reads Path.cwd() / "outputs" / "output-github.json"
# and, when it exists, returns canned data without calling the API.
# Patch Path.cwd to a tmp dir so tests always exercise the real API path.
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _block_devmode_file(tmp_path):
    """Ensure the dev-mode JSON file is never found during tests."""
    with patch.object(Path, "cwd", return_value=tmp_path):
        yield


# ---------------------------------------------------------------------------
# Session-based mock fixture (Phase 1 pattern: Session().get by URL)
# ---------------------------------------------------------------------------


def _make_session_mock(
    user=None,
    repos=None,
    social_accounts=None,
    orgs=None,
    keys=None,
    html=None,
    gists=None,
):
    """Build a mock for ``requests.Session()`` routing .get() calls by URL.

    Each parameter defaults to the matching global fixture or an empty list.
    """
    user = user if user is not None else GITHUB_USER_RESPONSE.copy()
    repos = repos if repos is not None else GITHUB_REPOS_RESPONSE
    social_accounts = (
        social_accounts
        if social_accounts is not None
        else GITHUB_SOCIAL_ACCOUNTS_RESPONSE
    )
    orgs = orgs if orgs is not None else GITHUB_ORGS_RESPONSE
    keys = keys if keys is not None else GITHUB_KEYS_RESPONSE
    html = html if html is not None else GITHUB_HTML_RESPONSE
    gists = gists if gists is not None else GITHUB_GISTS_RESPONSE

    def _make_resp(data, is_html=False):
        r = MagicMock()
        if is_html:
            r.content = data.encode() if isinstance(data, str) else data
        else:
            r.json.return_value = data
            r.text = json.dumps(data)
            r.raise_for_status = MagicMock()
        return r

    html_resp = _make_resp(html, is_html=True)
    html_resp.raise_for_status = MagicMock()

    def side_effect(url, **kwargs):
        if "social_accounts" in url:
            return _make_resp(social_accounts)
        if "/orgs" in url and "api.github.com" in url:
            return _make_resp(orgs)
        if "/keys" in url:
            return _make_resp(keys)
        if "/gists" in url:
            return _make_resp(gists)
        if "/repos" in url:
            return _make_resp(repos)
        if "api.github.com/users/" in url:
            return _make_resp(user)
        # HTML contribution calendar
        return html_resp

    mock_session_instance = MagicMock()
    mock_session_instance.get.side_effect = side_effect
    return mock_session_instance


@pytest.fixture
def mock_github_api():
    """Mock requests.Session for full happy-path GitHub API."""
    mock_session_instance = _make_session_mock()
    with patch(
        "modules.github.github_tasks.requests.Session",
        return_value=mock_session_instance,
    ) as mock_cls:
        yield mock_cls


@pytest.fixture
def mock_github_not_found():
    """Mock requests.Session to return 'Not Found' for user endpoint."""
    mock_session_instance = _make_session_mock(user=GITHUB_NOT_FOUND.copy())
    with patch(
        "modules.github.github_tasks.requests.Session",
        return_value=mock_session_instance,
    ):
        yield mock_session_instance


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


# ===========================================================================
# TestPGithub — core p_github processing function
# ===========================================================================


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

    def test_not_found_returns_warning(self, mock_github_not_found):
        """When user not found, @iky_task returns Warning error structure."""
        from modules.github.github_tasks import p_github

        result = p_github("nonexistent_user")
        raw = next(item["raw"] for item in result if "raw" in item)
        assert raw[0]["status"] == "Warning"
        assert raw[0]["reason"] == "User not found"

    def test_email_from_at_sign(self, mock_github_api, mock_location_geo):
        """When input contains @, username is extracted from email prefix."""
        from modules.github.github_tasks import p_github

        result = p_github("testuser@example.com", "Initial")
        param = next(item["param"] for item in result if "param" in item)
        assert param == "testuser"

    # ---------------------------------------------------------------
    # Dev-mode bypass verification (now handled by @iky_task)
    # ---------------------------------------------------------------

    def test_devmode_file_is_bypassed(
        self, tmp_path, mock_github_api, mock_location_geo
    ):
        """The autouse fixture prevents dev-mode from triggering."""
        from modules.github.github_tasks import p_github

        decoy = tmp_path / "other" / "outputs" / "output-github.json"
        decoy.parent.mkdir(parents=True, exist_ok=True)
        decoy.write_text(json.dumps([{"decoy": True}]))

        result = p_github("testuser", "Initial")

        keys = [next(iter(item.keys())) for item in result if isinstance(item, dict)]
        assert "graphic" in keys
        assert "decoy" not in keys

    def test_devmode_file_returns_file_data_when_present(self, tmp_path):
        """If cwd contains the dev-mode file, @iky_task returns it."""
        from modules.github.github_tasks import p_github

        outputs_dir = tmp_path / "outputs"
        outputs_dir.mkdir()
        devfile = outputs_dir / "output-github.json"
        canned = [{"module": "github"}, {"canned": True}]
        devfile.write_text(json.dumps(canned))

        with patch("factories.task_wrapper.time.sleep"):
            result = p_github("anything")

        assert result == canned

    # ---------------------------------------------------------------
    # Edge cases
    # ---------------------------------------------------------------

    def test_empty_username(self, mock_github_not_found):
        """Empty string still hits the API and returns Warning on Not Found."""
        from modules.github.github_tasks import p_github

        result = p_github("")
        raw = next(item["raw"] for item in result if "raw" in item)
        assert raw[0]["status"] == "Warning"
        assert raw[0]["reason"] == "User not found"

    def test_api_returns_unexpected_structure(self, tmp_path):
        """When API returns data without 'login' key, @iky_task returns Fail."""
        from modules.github.github_tasks import p_github

        bad_data = {"id": 999, "type": "User"}
        mock_session_instance = _make_session_mock(user=bad_data)
        with patch(
            "modules.github.github_tasks.requests.Session",
            return_value=mock_session_instance,
        ):
            result = p_github("baduser")

        raw = next(item["raw"] for item in result if "raw" in item)
        # "User not found" has no "iKy - " prefix → caught as Fail
        assert raw[0]["status"] == "Fail"
        assert "User not found" in raw[0]["reason"]


# ===========================================================================
# TestDecoratorAlias — @iky_task / t_github alias
# ===========================================================================


class TestDecoratorAlias:
    """Verify @iky_task wiring and t_github backward-compatible alias."""

    def test_t_github_is_p_github(self):
        """t_github must be the exact same object as p_github."""
        from modules.github.github_tasks import p_github, t_github

        assert t_github is p_github

    def test_celery_task_name(self):
        """Registered Celery task name matches MODULE_REGISTRY convention."""
        from modules.github.github_tasks import p_github

        assert hasattr(p_github, "name")
        assert p_github.name == "modules.github.github_tasks.t_github"

    def test_t_github_callable(self, mock_github_api, mock_location_geo):
        """t_github executes p_github and returns expected structure."""
        from modules.github.github_tasks import t_github

        result = t_github("testuser", "Initial")
        keys = [next(iter(item.keys())) for item in result if isinstance(item, dict)]
        assert "module" in keys
        assert "graphic" in keys


# ===========================================================================
# TestTGithubErrorPaths — error handling via @iky_task decorator
# ===========================================================================


class TestTGithubErrorPaths:
    """Tests for t_github error handling (now provided by @iky_task decorator)."""

    def test_iky_prefixed_exception_returns_warning(self):
        """Exception starting with 'iKy - ' yields status 'Warning'."""
        from modules.github.github_tasks import p_github

        mock_session = MagicMock()
        not_found_resp = MagicMock()
        not_found_resp.json.return_value = {"message": "Not Found"}
        not_found_resp.text = json.dumps({"message": "Not Found"})
        mock_session.get.return_value = not_found_resp

        with patch(
            "modules.github.github_tasks.requests.Session",
            return_value=mock_session,
        ):
            result = p_github("nobody")

        raw = next(item["raw"] for item in result if "raw" in item)
        assert raw[0]["status"] == "Warning"
        assert raw[0]["reason"] == "User not found"

    def test_generic_exception_returns_fail(self):
        """Non-iKy exception yields status 'Fail'."""
        from modules.github.github_tasks import p_github

        mock_session = MagicMock()
        mock_session.get.side_effect = RuntimeError("connection timeout")

        with patch(
            "modules.github.github_tasks.requests.Session",
            return_value=mock_session,
        ):
            result = p_github("nobody")

        raw = next(item["raw"] for item in result if "raw" in item)
        assert raw[0]["status"] == "Fail"
        assert raw[0]["reason"] == "connection timeout"

    def test_error_response_structure(self):
        """Error response has module, param, validation, raw keys."""
        from modules.github.github_tasks import p_github

        mock_session = MagicMock()
        mock_session.get.side_effect = Exception("boom")

        with patch(
            "modules.github.github_tasks.requests.Session",
            return_value=mock_session,
        ):
            result = p_github("user@test.com")

        keys = [next(iter(item.keys())) for item in result if isinstance(item, dict)]
        assert keys == ["module", "param", "validation", "raw"]

        assert next(item["module"] for item in result if "module" in item) == "github"
        # Decorator stores raw first arg (original email), not extracted username
        assert (
            next(item["param"] for item in result if "param" in item) == "user@test.com"
        )
        assert (
            next(item["validation"] for item in result if "validation" in item)
            == "not_used"
        )

    def test_error_response_includes_traceback(self):
        """Error response raw node includes a traceback string."""
        from modules.github.github_tasks import p_github

        mock_session = MagicMock()
        mock_session.get.side_effect = ValueError("test error")

        with patch(
            "modules.github.github_tasks.requests.Session",
            return_value=mock_session,
        ):
            result = p_github("someone")

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
        assert "graphic" in keys
        assert "profile" in keys


# ===========================================================================
# TestSnakeCaseHelpers — snake_case helper functions
# ===========================================================================


class TestSnakeCaseHelpers:
    """Tests for the snake_case helper functions."""

    def test_find_repos_from_username_returns_non_forked(self):
        """find_repos_from_username returns only non-forked repo names."""
        from modules.github.github_tasks import find_repos_from_username

        mock_session = MagicMock()
        repos_resp = MagicMock()
        repos_resp.json.return_value = GITHUB_REPOS_RESPONSE
        mock_session.get.return_value = repos_resp

        result = find_repos_from_username(mock_session, "testuser")

        # Only non-forked repos
        assert "awesome-project" in result
        assert "another-repo" in result
        assert "forked-thing" not in result

    def test_find_repos_from_username_uses_json(self):
        """find_repos_from_username uses .json() (not regex)."""
        from modules.github.github_tasks import find_repos_from_username

        mock_session = MagicMock()
        repos_resp = MagicMock()
        repos_resp.json.return_value = []
        mock_session.get.return_value = repos_resp

        result = find_repos_from_username(mock_session, "emptyuser")

        mock_session.get.assert_called_once()
        repos_resp.json.assert_called_once()
        assert result == []

    def test_find_repos_handles_non_list_response(self):
        """Non-list API response returns empty list gracefully."""
        from modules.github.github_tasks import find_repos_from_username

        mock_session = MagicMock()
        repos_resp = MagicMock()
        repos_resp.json.return_value = {"message": "rate limited"}
        mock_session.get.return_value = repos_resp

        result = find_repos_from_username(mock_session, "ratelimited")
        assert result == []

    def test_find_email_from_contributor_extracts_email(self):
        """find_email_from_contributor extracts email from patch file."""
        from modules.github.github_tasks import find_email_from_contributor

        mock_session = MagicMock()

        commits_resp = MagicMock()
        commits_resp.text = '<a href="/testuser/myrepo/commit/abc123">commit</a>'

        patch_resp = MagicMock()
        patch_resp.text = "From: Test User <dev@example.com>\nSubject: fix"

        def get_side(url, **kwargs):
            if "commits" in url:
                return commits_resp
            return patch_resp

        mock_session.get.side_effect = get_side

        result = find_email_from_contributor(
            mock_session, "testuser", "myrepo", "testuser"
        )
        assert result == "dev@example.com"

    def test_find_email_from_username_returns_false_when_no_repos(self):
        """Returns False when user has no repos."""
        from modules.github.github_tasks import find_email_from_username

        mock_session = MagicMock()
        repos_resp = MagicMock()
        repos_resp.json.return_value = []
        mock_session.get.return_value = repos_resp

        result = find_email_from_username(mock_session, "emptyuser")
        assert result is False


# ===========================================================================
# TestNewEndpoints — social_accounts, orgs, keys
# ===========================================================================


class TestNewEndpoints:
    """Tests for the three new GitHub API endpoints."""

    def test_social_accounts_in_graphic(self, mock_location_geo):
        """social_accounts section appears when endpoint returns data."""
        from modules.github.github_tasks import p_github

        mock_session_instance = _make_session_mock()
        with patch(
            "modules.github.github_tasks.requests.Session",
            return_value=mock_session_instance,
        ):
            result = p_github("testuser")

        graphic = next(item["graphic"] for item in result if "graphic" in item)
        section_keys = [next(iter(s.keys())) for s in graphic]
        assert "social_accounts" in section_keys

        sa = next(s["social_accounts"] for s in graphic if "social_accounts" in s)
        assert len(sa) == 2
        assert sa[0]["provider"] == "twitter"

    def test_orgs_in_graphic(self, mock_location_geo):
        """orgs section appears when endpoint returns data."""
        from modules.github.github_tasks import p_github

        mock_session_instance = _make_session_mock()
        with patch(
            "modules.github.github_tasks.requests.Session",
            return_value=mock_session_instance,
        ):
            result = p_github("testuser")

        graphic = next(item["graphic"] for item in result if "graphic" in item)
        section_keys = [next(iter(s.keys())) for s in graphic]
        assert "orgs" in section_keys

        orgs = next(s["orgs"] for s in graphic if "orgs" in s)
        assert len(orgs) == 1
        assert orgs[0]["name"] == "testorg"

    def test_keys_in_graphic(self, mock_location_geo):
        """keys section appears when endpoint returns data."""
        from modules.github.github_tasks import p_github

        mock_session_instance = _make_session_mock()
        with patch(
            "modules.github.github_tasks.requests.Session",
            return_value=mock_session_instance,
        ):
            result = p_github("testuser")

        graphic = next(item["graphic"] for item in result if "graphic" in item)
        section_keys = [next(iter(s.keys())) for s in graphic]
        assert "keys" in section_keys

        keys = next(s["keys"] for s in graphic if "keys" in s)
        assert len(keys) == 1
        assert keys[0]["id"] == 7890

    def test_repos_in_graphic(self, mock_location_geo):
        """repos section appears when repos endpoint returns data."""
        from modules.github.github_tasks import p_github

        mock_session_instance = _make_session_mock()
        with patch(
            "modules.github.github_tasks.requests.Session",
            return_value=mock_session_instance,
        ):
            result = p_github("testuser")

        graphic = next(item["graphic"] for item in result if "graphic" in item)
        section_keys = [next(iter(s.keys())) for s in graphic]
        assert "repos" in section_keys

        repos = next(s["repos"] for s in graphic if "repos" in s)
        # Sorted by stars descending: awesome-project (50), another-repo (20)
        assert repos[0]["name"] == "awesome-project"
        assert repos[0]["stars"] == 50

    def test_existing_sections_order_preserved(self, mock_location_geo):
        """github, cal_actual, cal_previous come before new sections."""
        from modules.github.github_tasks import p_github

        mock_session_instance = _make_session_mock()
        with patch(
            "modules.github.github_tasks.requests.Session",
            return_value=mock_session_instance,
        ):
            result = p_github("testuser")

        graphic = next(item["graphic"] for item in result if "graphic" in item)
        section_keys = [next(iter(s.keys())) for s in graphic]

        github_idx = section_keys.index("github")
        cal_actual_idx = section_keys.index("cal_actual")
        cal_previous_idx = section_keys.index("cal_previous")

        # Existing sections must come first
        assert github_idx == 0
        assert cal_actual_idx == 1
        assert cal_previous_idx == 2

        # New sections come after
        for new_key in ("social_accounts", "orgs", "keys", "repos"):
            if new_key in section_keys:
                assert section_keys.index(new_key) > cal_previous_idx


# ===========================================================================
# TestGracefulDegradation — per-endpoint failure isolation
# ===========================================================================


class TestGracefulDegradation:
    """Tests verifying each new endpoint fails independently."""

    def _result_with_failing_endpoint(self, fail_on, mock_location_geo):
        """Return p_github result with one endpoint raising an exception."""
        from modules.github.github_tasks import p_github

        def side_effect(url, **kwargs):
            if fail_on in url:
                raise RuntimeError(f"Simulated failure for {fail_on}")
            # Route other URLs normally
            if "social_accounts" in url:
                r = MagicMock()
                r.json.return_value = GITHUB_SOCIAL_ACCOUNTS_RESPONSE
                r.raise_for_status = MagicMock()
                return r
            if "/orgs" in url and "api.github.com" in url:
                r = MagicMock()
                r.json.return_value = GITHUB_ORGS_RESPONSE
                r.raise_for_status = MagicMock()
                return r
            if "/keys" in url:
                r = MagicMock()
                r.json.return_value = GITHUB_KEYS_RESPONSE
                r.raise_for_status = MagicMock()
                return r
            if "/gists" in url:
                r = MagicMock()
                r.json.return_value = GITHUB_GISTS_RESPONSE
                r.raise_for_status = MagicMock()
                return r
            if "/repos" in url:
                r = MagicMock()
                r.json.return_value = GITHUB_REPOS_RESPONSE
                r.raise_for_status = MagicMock()
                return r
            if "api.github.com/users/" in url:
                r = MagicMock()
                r.json.return_value = GITHUB_USER_RESPONSE.copy()
                r.text = json.dumps(GITHUB_USER_RESPONSE)
                r.raise_for_status = MagicMock()
                return r
            # HTML calendar
            r = MagicMock()
            r.content = GITHUB_HTML_RESPONSE.encode()
            r.raise_for_status = MagicMock()
            return r

        mock_session = MagicMock()
        mock_session.get.side_effect = side_effect

        with patch(
            "modules.github.github_tasks.requests.Session",
            return_value=mock_session,
        ):
            return p_github("testuser")

    def test_orgs_failure_does_not_break_module(self, mock_location_geo):
        """When orgs endpoint fails, other sections still appear."""
        result = self._result_with_failing_endpoint("/orgs", mock_location_geo)

        keys = [next(iter(item.keys())) for item in result if isinstance(item, dict)]
        assert "graphic" in keys

        graphic = next(item["graphic"] for item in result if "graphic" in item)
        section_keys = [next(iter(s.keys())) for s in graphic]
        assert "orgs" not in section_keys
        assert "social_accounts" in section_keys
        assert "keys" in section_keys

    def test_social_accounts_failure_does_not_break_module(self, mock_location_geo):
        """When social_accounts endpoint fails, other sections still appear."""
        result = self._result_with_failing_endpoint(
            "social_accounts", mock_location_geo
        )

        graphic = next(item["graphic"] for item in result if "graphic" in item)
        section_keys = [next(iter(s.keys())) for s in graphic]
        assert "social_accounts" not in section_keys
        assert "orgs" in section_keys
        assert "keys" in section_keys

    def test_keys_failure_does_not_break_module(self, mock_location_geo):
        """When keys endpoint fails, other sections still appear."""
        result = self._result_with_failing_endpoint("/keys", mock_location_geo)

        graphic = next(item["graphic"] for item in result if "graphic" in item)
        section_keys = [next(iter(s.keys())) for s in graphic]
        assert "keys" not in section_keys
        assert "social_accounts" in section_keys
        assert "orgs" in section_keys

    def test_calendar_scraping_failure_graceful(self):
        """When HTML calendar scraping fails, cal_actual is empty string."""
        from modules.github.github_tasks import p_github

        bad_html = b"<html><body>No calendar here</body></html>"

        mock_session = MagicMock()

        def side_effect(url, **kwargs):
            if "social_accounts" in url:
                r = MagicMock()
                r.json.return_value = []
                r.raise_for_status = MagicMock()
                return r
            if "/orgs" in url and "api.github.com" in url:
                r = MagicMock()
                r.json.return_value = []
                r.raise_for_status = MagicMock()
                return r
            if "/keys" in url:
                r = MagicMock()
                r.json.return_value = []
                r.raise_for_status = MagicMock()
                return r
            if "/gists" in url:
                r = MagicMock()
                r.json.return_value = []
                r.raise_for_status = MagicMock()
                return r
            if "/repos" in url:
                r = MagicMock()
                r.json.return_value = []
                r.raise_for_status = MagicMock()
                return r
            if "api.github.com/users/" in url:
                r = MagicMock()
                r.json.return_value = GITHUB_USER_RESPONSE.copy()
                r.text = json.dumps(GITHUB_USER_RESPONSE)
                r.raise_for_status = MagicMock()
                return r
            # Broken HTML for calendar
            r = MagicMock()
            r.content = bad_html
            r.raise_for_status = MagicMock()
            return r

        mock_session.get.side_effect = side_effect

        with (
            patch(
                "modules.github.github_tasks.requests.Session",
                return_value=mock_session,
            ),
            patch("modules.github.github_tasks.location_geo", return_value=None),
        ):
            result = p_github("testuser")

        # Must still return a valid result
        keys = [next(iter(item.keys())) for item in result if isinstance(item, dict)]
        assert "graphic" in keys

        graphic = next(item["graphic"] for item in result if "graphic" in item)
        cal = next(s["cal_actual"] for s in graphic if "cal_actual" in s)
        assert cal == ""

    def test_module_completes_with_all_new_endpoints_failing(self, mock_location_geo):
        """Module completes normally even if all three new endpoints fail."""
        from modules.github.github_tasks import p_github

        def side_effect(url, **kwargs):
            if any(ep in url for ep in ("social_accounts", "/orgs", "/keys", "/gists")):
                raise RuntimeError("all new endpoints down")
            if "/repos" in url:
                r = MagicMock()
                r.json.return_value = GITHUB_REPOS_RESPONSE
                r.raise_for_status = MagicMock()
                return r
            if "api.github.com/users/" in url:
                r = MagicMock()
                r.json.return_value = GITHUB_USER_RESPONSE.copy()
                r.text = json.dumps(GITHUB_USER_RESPONSE)
                r.raise_for_status = MagicMock()
                return r
            r = MagicMock()
            r.content = GITHUB_HTML_RESPONSE.encode()
            r.raise_for_status = MagicMock()
            return r

        mock_session = MagicMock()
        mock_session.get.side_effect = side_effect

        with patch(
            "modules.github.github_tasks.requests.Session",
            return_value=mock_session,
        ):
            result = p_github("testuser")

        keys = [next(iter(item.keys())) for item in result if isinstance(item, dict)]
        assert "graphic" in keys

    def test_gists_failure_does_not_break_module(self, mock_location_geo):
        """When gists endpoint fails, other sections still appear."""
        result = self._result_with_failing_endpoint("/gists", mock_location_geo)

        keys = [next(iter(item.keys())) for item in result if isinstance(item, dict)]
        assert "graphic" in keys

        graphic = next(item["graphic"] for item in result if "graphic" in item)
        section_keys = [next(iter(s.keys())) for s in graphic]
        assert "gists" not in section_keys
        # Other sections not affected
        assert "social_accounts" in section_keys
        assert "orgs" in section_keys
        assert "keys" in section_keys


# ===========================================================================
# TestRepoEnrichment — language stats and repo sorting
# ===========================================================================


class TestRepoEnrichment:
    """Tests for repo data enrichment (languages, stars, topics)."""

    def test_language_stats_in_gather(self, mock_location_geo):
        """Language distribution appears in gather section."""
        from modules.github.github_tasks import p_github

        mock_session_instance = _make_session_mock()
        with patch(
            "modules.github.github_tasks.requests.Session",
            return_value=mock_session_instance,
        ):
            result = p_github("testuser")

        graphic = next(item["graphic"] for item in result if "graphic" in item)
        github_section = next(s["github"] for s in graphic if "github" in s)
        lang_item = next(
            (g for g in github_section if g.get("name-node") == "GitLanguages"), None
        )
        assert lang_item is not None
        assert "Python" in lang_item["subtitle"]
        assert "JavaScript" in lang_item["subtitle"]

    def test_repos_sorted_by_stars_descending(self, mock_location_geo):
        """Repos section is sorted by stars (highest first)."""
        from modules.github.github_tasks import p_github

        mock_session_instance = _make_session_mock()
        with patch(
            "modules.github.github_tasks.requests.Session",
            return_value=mock_session_instance,
        ):
            result = p_github("testuser")

        graphic = next(item["graphic"] for item in result if "graphic" in item)
        repos = next((s["repos"] for s in graphic if "repos" in s), None)
        assert repos is not None
        stars = [r["stars"] for r in repos]
        assert stars == sorted(stars, reverse=True)

    def test_repos_section_has_required_fields(self, mock_location_geo):
        """Each repo entry has name, description, language, stars, forks, topics."""
        from modules.github.github_tasks import p_github

        mock_session_instance = _make_session_mock()
        with patch(
            "modules.github.github_tasks.requests.Session",
            return_value=mock_session_instance,
        ):
            result = p_github("testuser")

        graphic = next(item["graphic"] for item in result if "graphic" in item)
        repos = next((s["repos"] for s in graphic if "repos" in s), None)
        assert repos is not None

        for repo in repos:
            assert "name" in repo
            assert "description" in repo
            assert "language" in repo
            assert "stars" in repo
            assert "forks" in repo
            assert "topics" in repo

    def test_repos_limited_to_top_10(self, mock_location_geo):
        """repos section contains at most 10 entries."""
        from modules.github.github_tasks import p_github

        many_repos = [
            {
                "name": f"repo-{i}",
                "description": "",
                "language": "Python",
                "stargazers_count": i,
                "forks_count": 0,
                "topics": [],
                "fork": False,
                "created_at": "2022-01-01T00:00:00Z",
            }
            for i in range(20)
        ]
        mock_session_instance = _make_session_mock(repos=many_repos)
        with patch(
            "modules.github.github_tasks.requests.Session",
            return_value=mock_session_instance,
        ):
            result = p_github("testuser")

        graphic = next(item["graphic"] for item in result if "graphic" in item)
        repos = next((s["repos"] for s in graphic if "repos" in s), None)
        assert repos is not None
        assert len(repos) <= 10

    def test_repos_have_fork_flag(self, mock_location_geo):
        """Each repo entry includes a 'fork' boolean field."""
        from modules.github.github_tasks import p_github

        mock_session_instance = _make_session_mock()
        with patch(
            "modules.github.github_tasks.requests.Session",
            return_value=mock_session_instance,
        ):
            result = p_github("testuser")

        graphic = next(item["graphic"] for item in result if "graphic" in item)
        repos = next((s["repos"] for s in graphic if "repos" in s), None)
        assert repos is not None
        for repo in repos:
            assert "fork" in repo
            assert isinstance(repo["fork"], bool)

    def test_forked_repo_has_fork_true(self, mock_location_geo):
        """Repos with fork=True in source data have fork=True in output."""
        from modules.github.github_tasks import p_github

        mock_session_instance = _make_session_mock()
        with patch(
            "modules.github.github_tasks.requests.Session",
            return_value=mock_session_instance,
        ):
            result = p_github("testuser")

        graphic = next(item["graphic"] for item in result if "graphic" in item)
        repos = next((s["repos"] for s in graphic if "repos" in s), None)
        assert repos is not None
        forked = next((r for r in repos if r["name"] == "forked-thing"), None)
        if forked:
            assert forked["fork"] is True

    def test_repo_topics_aggregated_in_graphic(self, mock_location_geo):
        """Unique topics from all repos are aggregated into a 'topics' section."""
        from modules.github.github_tasks import p_github

        mock_session_instance = _make_session_mock()
        with patch(
            "modules.github.github_tasks.requests.Session",
            return_value=mock_session_instance,
        ):
            result = p_github("testuser")

        graphic = next(item["graphic"] for item in result if "graphic" in item)
        section_keys = [next(iter(s.keys())) for s in graphic]
        assert "topics" in section_keys

        topics = next(s["topics"] for s in graphic if "topics" in s)
        # awesome-project has ["osint", "python"]
        assert "osint" in topics
        assert "python" in topics
        # No duplicates
        assert len(topics) == len(set(topics))

    def test_repo_created_at_added_to_timeline(self, mock_location_geo):
        """Top repos' creation dates appear in the timeline."""
        from modules.github.github_tasks import p_github

        mock_session_instance = _make_session_mock()
        with patch(
            "modules.github.github_tasks.requests.Session",
            return_value=mock_session_instance,
        ):
            result = p_github("testuser")

        timeline = next(item["timeline"] for item in result if "timeline" in item)
        repo_timeline_entries = [
            t for t in timeline if "Created repo" in t.get("action", "")
        ]
        # Should have at least 1 entry (awesome-project)
        assert len(repo_timeline_entries) >= 1
        # Check the highest-star repo is present
        actions = [t["action"] for t in repo_timeline_entries]
        assert any("awesome-project" in a for a in actions)


# ===========================================================================
# TestRateLimiting — 403 / rate-limit response handling
# ===========================================================================


class TestRateLimiting:
    """Tests verifying graceful handling of 403 / rate-limit responses."""

    def _make_403_response(self):
        """Return a mock response that raises HTTPError on raise_for_status."""
        import requests as req_lib

        r = MagicMock()
        r.json.return_value = {"message": "API rate limit exceeded"}
        r.text = json.dumps({"message": "API rate limit exceeded"})
        http_err = req_lib.exceptions.HTTPError(response=MagicMock(status_code=403))
        r.raise_for_status.side_effect = http_err
        return r

    def test_full_rate_limit_returns_partial_data(self, mock_location_geo):
        """When ALL new endpoints return 403, p_github still returns base data."""
        from modules.github.github_tasks import p_github

        def side_effect(url, **kwargs):
            if any(
                ep in url
                for ep in ("social_accounts", "/orgs", "/keys", "/repos", "/gists")
            ):
                return self._make_403_response()
            if "api.github.com/users/" in url:
                r = MagicMock()
                r.json.return_value = GITHUB_USER_RESPONSE.copy()
                r.text = json.dumps(GITHUB_USER_RESPONSE)
                r.raise_for_status = MagicMock()
                return r
            r = MagicMock()
            r.content = GITHUB_HTML_RESPONSE.encode()
            r.raise_for_status = MagicMock()
            return r

        mock_session = MagicMock()
        mock_session.get.side_effect = side_effect

        with patch(
            "modules.github.github_tasks.requests.Session",
            return_value=mock_session,
        ):
            result = p_github("testuser")

        # Must not crash — result is a list with base keys
        assert isinstance(result, list)
        keys = [next(iter(item.keys())) for item in result if isinstance(item, dict)]
        assert "module" in keys
        assert "graphic" in keys

        # New sections should NOT be present (all 403'd)
        graphic = next(item["graphic"] for item in result if "graphic" in item)
        section_keys = [next(iter(s.keys())) for s in graphic]
        assert "social_accounts" not in section_keys
        assert "orgs" not in section_keys
        assert "keys" not in section_keys
        assert "repos" not in section_keys

    def test_single_403_on_orgs_degrades_gracefully(self, mock_location_geo):
        """When only /orgs returns 403, all other sections still appear."""
        from modules.github.github_tasks import p_github

        def side_effect(url, **kwargs):
            if "/orgs" in url and "api.github.com" in url:
                return self._make_403_response()
            if "social_accounts" in url:
                r = MagicMock()
                r.json.return_value = GITHUB_SOCIAL_ACCOUNTS_RESPONSE
                r.raise_for_status = MagicMock()
                return r
            if "/keys" in url:
                r = MagicMock()
                r.json.return_value = GITHUB_KEYS_RESPONSE
                r.raise_for_status = MagicMock()
                return r
            if "/gists" in url:
                r = MagicMock()
                r.json.return_value = GITHUB_GISTS_RESPONSE
                r.raise_for_status = MagicMock()
                return r
            if "/repos" in url:
                r = MagicMock()
                r.json.return_value = GITHUB_REPOS_RESPONSE
                r.raise_for_status = MagicMock()
                return r
            if "api.github.com/users/" in url:
                r = MagicMock()
                r.json.return_value = GITHUB_USER_RESPONSE.copy()
                r.text = json.dumps(GITHUB_USER_RESPONSE)
                r.raise_for_status = MagicMock()
                return r
            r = MagicMock()
            r.content = GITHUB_HTML_RESPONSE.encode()
            r.raise_for_status = MagicMock()
            return r

        mock_session = MagicMock()
        mock_session.get.side_effect = side_effect

        with patch(
            "modules.github.github_tasks.requests.Session",
            return_value=mock_session,
        ):
            result = p_github("testuser")

        assert isinstance(result, list)
        graphic = next(item["graphic"] for item in result if "graphic" in item)
        section_keys = [next(iter(s.keys())) for s in graphic]

        # /orgs 403'd → absent
        assert "orgs" not in section_keys
        # Other endpoints succeeded → present
        assert "social_accounts" in section_keys
        assert "keys" in section_keys
        assert "repos" in section_keys


# ===========================================================================
# TestHappyPathAllSections — unified happy-path coverage
# ===========================================================================


class TestHappyPathAllSections:
    """Unified happy-path: ALL new graphic sections must be present together."""

    def test_all_new_sections_present_in_single_call(self, mock_location_geo):
        """A single p_github call with full data returns all new sections."""
        from modules.github.github_tasks import p_github

        mock_session_instance = _make_session_mock()
        with patch(
            "modules.github.github_tasks.requests.Session",
            return_value=mock_session_instance,
        ):
            result = p_github("testuser")

        graphic = next(item["graphic"] for item in result if "graphic" in item)
        section_keys = [next(iter(s.keys())) for s in graphic]

        assert "social_accounts" in section_keys, "social_accounts missing"
        assert "orgs" in section_keys, "orgs missing"
        assert "keys" in section_keys, "keys missing"
        assert "repos" in section_keys, "repos missing"
        assert "gists" in section_keys, "gists missing"

    def test_api_call_count_matches_expectations(self, mock_location_geo):
        """p_github makes exactly the expected number of HTTP GET calls.

        Expected calls (in order):
          1. /users/{user}        — profile
          2. github.com/{user}    — HTML contribution calendar
          3. /social_accounts     — social accounts
          4. /orgs                — orgs
          5. /keys                — SSH keys
          6. /repos               — repos (explicit fetch for enrichment)
          7. /gists               — gists
        Total: 7 calls (no email-from-commit search since email is in profile).
        """
        from modules.github.github_tasks import p_github

        mock_session_instance = _make_session_mock()
        with patch(
            "modules.github.github_tasks.requests.Session",
            return_value=mock_session_instance,
        ):
            p_github("testuser")

        assert mock_session_instance.get.call_count == 7


# ===========================================================================
# TestContributionCalendar — calendar parsing
# ===========================================================================


class TestContributionCalendar:
    """Tests for the new contribution calendar HTML table parsing."""

    def test_calendar_parsed_as_list(self, mock_location_geo):
        """cal_actual is a list of date/level dicts when HTML is correct."""
        from modules.github.github_tasks import p_github

        mock_session_instance = _make_session_mock()
        with patch(
            "modules.github.github_tasks.requests.Session",
            return_value=mock_session_instance,
        ):
            result = p_github("testuser")

        graphic = next(item["graphic"] for item in result if "graphic" in item)
        cal = next(s["cal_actual"] for s in graphic if "cal_actual" in s)
        assert isinstance(cal, list)
        assert len(cal) == 3  # Three <td> cells in GITHUB_HTML_RESPONSE
        assert cal[0] == {"date": "2025-01-01", "level": 0}
        assert cal[1] == {"date": "2025-01-02", "level": 2}
        assert cal[2] == {"date": "2025-01-03", "level": 4}

    def test_calendar_cell_has_date_and_level_keys(self, mock_location_geo):
        """Every calendar entry has 'date' and 'level' keys."""
        from modules.github.github_tasks import p_github

        mock_session_instance = _make_session_mock()
        with patch(
            "modules.github.github_tasks.requests.Session",
            return_value=mock_session_instance,
        ):
            result = p_github("testuser")

        graphic = next(item["graphic"] for item in result if "graphic" in item)
        cal = next(s["cal_actual"] for s in graphic if "cal_actual" in s)
        assert isinstance(cal, list)
        for entry in cal:
            assert "date" in entry
            assert "level" in entry
            assert isinstance(entry["level"], int)

    def test_calendar_previous_is_empty_string(self, mock_location_geo):
        """cal_previous is always an empty string (not implemented)."""
        from modules.github.github_tasks import p_github

        mock_session_instance = _make_session_mock()
        with patch(
            "modules.github.github_tasks.requests.Session",
            return_value=mock_session_instance,
        ):
            result = p_github("testuser")

        graphic = next(item["graphic"] for item in result if "graphic" in item)
        cal_prev = next(s["cal_previous"] for s in graphic if "cal_previous" in s)
        assert cal_prev == ""

    def test_calendar_uses_correct_fragment_url(self, mock_location_geo):
        """Calendar fetch uses action=show&controller=profiles URL, not &amp; entities."""
        from modules.github.github_tasks import p_github

        mock_session_instance = _make_session_mock()
        with patch(
            "modules.github.github_tasks.requests.Session",
            return_value=mock_session_instance,
        ):
            p_github("testuser")

        calls = mock_session_instance.get.call_args_list
        # Find the calendar URL call
        cal_calls = [
            call
            for call in calls
            if "github.com/testuser" in str(call) and "api.github.com" not in str(call)
        ]
        assert len(cal_calls) >= 1
        cal_url_used = str(cal_calls[0])
        # Must NOT contain &amp;
        assert "&amp;" not in cal_url_used
        # Must use the correct fragment endpoint parameters
        assert "action=show" in cal_url_used
        assert "tab=contributions" in cal_url_used

    def test_parse_contribution_calendar_function_directly(self):
        """_parse_contribution_calendar returns correct list from HTML bytes."""
        from modules.github.github_tasks import _parse_contribution_calendar

        html = b"""
        <table class="ContributionCalendar-grid js-calendar-graph-table">
          <tbody>
            <tr>
              <td data-date="2025-03-01" data-level="0"></td>
              <td data-date="2025-03-02" data-level="3"></td>
            </tr>
          </tbody>
        </table>
        """
        result = _parse_contribution_calendar(html)
        assert result == [
            {"date": "2025-03-01", "level": 0},
            {"date": "2025-03-02", "level": 3},
        ]

    def test_parse_contribution_calendar_raises_on_missing_table(self):
        """_parse_contribution_calendar raises ValueError when table is absent."""
        from modules.github.github_tasks import _parse_contribution_calendar

        html = b"<html><body><p>no table here</p></body></html>"
        with pytest.raises(ValueError, match="ContributionCalendar-grid"):
            _parse_contribution_calendar(html)

    def test_parse_contribution_calendar_raises_on_no_cells(self):
        """_parse_contribution_calendar raises ValueError when table has no cells."""
        from modules.github.github_tasks import _parse_contribution_calendar

        html = b"""
        <table class="ContributionCalendar-grid">
          <tbody></tbody>
        </table>
        """
        with pytest.raises(ValueError, match="No contribution calendar cells found"):
            _parse_contribution_calendar(html)


# ===========================================================================
# TestBlogField — blog graphic node and profile.social
# ===========================================================================


class TestBlogField:
    """Tests for blog URL enrichment."""

    def test_blog_creates_gather_node(self, mock_location_geo):
        """When blog is set, a GitBlog gather node is created."""
        from modules.github.github_tasks import p_github

        mock_session_instance = _make_session_mock()
        with patch(
            "modules.github.github_tasks.requests.Session",
            return_value=mock_session_instance,
        ):
            result = p_github("testuser")

        graphic = next(item["graphic"] for item in result if "graphic" in item)
        github_section = next(s["github"] for s in graphic if "github" in s)
        blog_node = next(
            (g for g in github_section if g.get("name-node") == "GitBlog"), None
        )
        assert blog_node is not None
        assert blog_node["subtitle"] == "https://testuser.dev"
        assert blog_node["icon"] == "fas fa-globe"

    def test_blog_added_to_profile_social(self, mock_location_geo):
        """When blog is set, it's added to profile social entries."""
        from modules.github.github_tasks import p_github

        mock_session_instance = _make_session_mock()
        with patch(
            "modules.github.github_tasks.requests.Session",
            return_value=mock_session_instance,
        ):
            result = p_github("testuser")

        profile = next(item["profile"] for item in result if "profile" in item)
        # Find social entries with "Blog" name
        blog_social = None
        for p_item in profile:
            if "social" in p_item:
                for s_entry in p_item["social"]:
                    if s_entry.get("name") == "Blog":
                        blog_social = s_entry
                        break
        assert blog_social is not None
        assert blog_social["url"] == "https://testuser.dev"
        assert blog_social["icon"] == "fas fa-globe"
        assert blog_social["source"] == "Github"

    def test_no_blog_no_gather_node(self, mock_location_geo):
        """When blog is empty, no GitBlog gather node is created."""
        from modules.github.github_tasks import p_github

        user_no_blog = GITHUB_USER_RESPONSE.copy()
        user_no_blog["blog"] = ""

        mock_session_instance = _make_session_mock(user=user_no_blog)
        with patch(
            "modules.github.github_tasks.requests.Session",
            return_value=mock_session_instance,
        ):
            result = p_github("testuser")

        graphic = next(item["graphic"] for item in result if "graphic" in item)
        github_section = next(s["github"] for s in graphic if "github" in s)
        blog_node = next(
            (g for g in github_section if g.get("name-node") == "GitBlog"), None
        )
        assert blog_node is None


# ===========================================================================
# TestHireableField — hireable profile and gather node
# ===========================================================================


class TestHireableField:
    """Tests for hireable field enrichment."""

    def test_hireable_true_in_profile(self, mock_location_geo):
        """When hireable is True, profile contains hireable=True."""
        from modules.github.github_tasks import p_github

        mock_session_instance = _make_session_mock()
        with patch(
            "modules.github.github_tasks.requests.Session",
            return_value=mock_session_instance,
        ):
            result = p_github("testuser")

        profile = next(item["profile"] for item in result if "profile" in item)
        hireable_entries = [p for p in profile if "hireable" in p]
        assert len(hireable_entries) == 1
        assert hireable_entries[0]["hireable"] is True

    def test_hireable_creates_gather_node(self, mock_location_geo):
        """When hireable is not None, a GitHireable gather node is created."""
        from modules.github.github_tasks import p_github

        mock_session_instance = _make_session_mock()
        with patch(
            "modules.github.github_tasks.requests.Session",
            return_value=mock_session_instance,
        ):
            result = p_github("testuser")

        graphic = next(item["graphic"] for item in result if "graphic" in item)
        github_section = next(s["github"] for s in graphic if "github" in s)
        hireable_node = next(
            (g for g in github_section if g.get("name-node") == "GitHireable"), None
        )
        assert hireable_node is not None
        assert hireable_node["subtitle"] is True
        assert hireable_node["icon"] == "fas fa-briefcase"

    def test_hireable_false_in_profile(self, mock_location_geo):
        """When hireable is False, profile contains hireable=False."""
        from modules.github.github_tasks import p_github

        user_not_hireable = GITHUB_USER_RESPONSE.copy()
        user_not_hireable["hireable"] = False

        mock_session_instance = _make_session_mock(user=user_not_hireable)
        with patch(
            "modules.github.github_tasks.requests.Session",
            return_value=mock_session_instance,
        ):
            result = p_github("testuser")

        profile = next(item["profile"] for item in result if "profile" in item)
        hireable_entries = [p for p in profile if "hireable" in p]
        assert len(hireable_entries) == 1
        assert hireable_entries[0]["hireable"] is False

    def test_hireable_null_not_in_profile(self, mock_location_geo):
        """When hireable is null/None, no hireable entry in profile."""
        from modules.github.github_tasks import p_github

        user_null_hireable = GITHUB_USER_RESPONSE.copy()
        user_null_hireable["hireable"] = None

        mock_session_instance = _make_session_mock(user=user_null_hireable)
        with patch(
            "modules.github.github_tasks.requests.Session",
            return_value=mock_session_instance,
        ):
            result = p_github("testuser")

        profile = next(item["profile"] for item in result if "profile" in item)
        hireable_entries = [p for p in profile if "hireable" in p]
        assert len(hireable_entries) == 0


# ===========================================================================
# TestSocialAccountsEnrichment — gather nodes, profile.social, tasks
# ===========================================================================


class TestSocialAccountsEnrichment:
    """Tests for social_accounts enriching gather, profile, and tasks."""

    def test_social_accounts_create_gather_nodes(self, mock_location_geo):
        """Each social account gets a gather node in the github section."""
        from modules.github.github_tasks import p_github

        mock_session_instance = _make_session_mock()
        with patch(
            "modules.github.github_tasks.requests.Session",
            return_value=mock_session_instance,
        ):
            result = p_github("testuser")

        graphic = next(item["graphic"] for item in result if "graphic" in item)
        github_section = next(s["github"] for s in graphic if "github" in s)

        # twitter social account should have a gather node
        twitter_node = next(
            (g for g in github_section if g.get("name-node") == "GitSocial_twitter"),
            None,
        )
        assert twitter_node is not None
        assert "twitter.com" in twitter_node["subtitle"]
        assert twitter_node["icon"] == "fab fa-twitter"

        # linkedin social account should have a gather node
        linkedin_node = next(
            (g for g in github_section if g.get("name-node") == "GitSocial_linkedin"),
            None,
        )
        assert linkedin_node is not None
        assert "linkedin.com" in linkedin_node["subtitle"]
        assert linkedin_node["icon"] == "fab fa-linkedin"

    def test_social_accounts_added_to_profile_social(self, mock_location_geo):
        """Each social account is added to profile.social."""
        from modules.github.github_tasks import p_github

        mock_session_instance = _make_session_mock()
        with patch(
            "modules.github.github_tasks.requests.Session",
            return_value=mock_session_instance,
        ):
            result = p_github("testuser")

        profile = next(item["profile"] for item in result if "profile" in item)
        all_social = []
        for p_item in profile:
            if "social" in p_item:
                all_social.extend(p_item["social"])

        social_names = [s["name"] for s in all_social]
        assert "Twitter" in social_names
        assert "Linkedin" in social_names

    def test_twitter_social_account_triggers_task(self, mock_location_geo):
        """twitter social account creates a twitter task."""
        from modules.github.github_tasks import p_github

        # Remove twitter_username from user so we only test social_accounts path
        user_no_tw = GITHUB_USER_RESPONSE.copy()
        user_no_tw["twitter_username"] = None

        mock_session_instance = _make_session_mock(user=user_no_tw)
        with patch(
            "modules.github.github_tasks.requests.Session",
            return_value=mock_session_instance,
        ):
            result = p_github("testuser")

        tasks = next(item["tasks"] for item in result if "tasks" in item)
        twitter_tasks = [t for t in tasks if t.get("module") == "twitter"]
        assert len(twitter_tasks) >= 1
        # Username extracted from URL last segment
        assert twitter_tasks[0]["param"] == "testuser_tw"

    def test_linkedin_social_account_triggers_task(self, mock_location_geo):
        """linkedin social account creates a linkedin task."""
        from modules.github.github_tasks import p_github

        mock_session_instance = _make_session_mock()
        with patch(
            "modules.github.github_tasks.requests.Session",
            return_value=mock_session_instance,
        ):
            result = p_github("testuser")

        tasks = next(item["tasks"] for item in result if "tasks" in item)
        linkedin_tasks = [t for t in tasks if t.get("module") == "linkedin"]
        assert len(linkedin_tasks) >= 1


# ===========================================================================
# TestDeduplication — tasks and profile.social deduplication
# ===========================================================================


class TestDeduplication:
    """Tests for deduplication of tasks and profile social entries."""

    def test_tasks_deduplicated_when_twitter_username_and_social_accounts_overlap(
        self, mock_location_geo
    ):
        """When twitter_username and social_accounts both reference twitter,
        the tasks list must contain exactly ONE twitter task entry."""
        from modules.github.github_tasks import p_github

        # Default fixture: GITHUB_USER_RESPONSE has twitter_username="testuser_tw"
        # and GITHUB_SOCIAL_ACCOUNTS_RESPONSE has {"provider": "twitter",
        # "url": "https://twitter.com/testuser_tw"} — both produce the same task.
        mock_session_instance = _make_session_mock()
        with patch(
            "modules.github.github_tasks.requests.Session",
            return_value=mock_session_instance,
        ):
            result = p_github("testuser")

        tasks = next(item["tasks"] for item in result if "tasks" in item)
        twitter_tasks = [t for t in tasks if t.get("module") == "twitter"]
        assert len(twitter_tasks) == 1, (
            f"Expected exactly 1 twitter task, got {len(twitter_tasks)}: {twitter_tasks}"
        )
        assert twitter_tasks[0]["param"] == "testuser_tw"

    def test_tasks_no_duplicates_across_all_modules(self, mock_location_geo):
        """No two tasks in the list should share the same module+param pair."""
        from modules.github.github_tasks import p_github

        mock_session_instance = _make_session_mock()
        with patch(
            "modules.github.github_tasks.requests.Session",
            return_value=mock_session_instance,
        ):
            result = p_github("testuser")

        tasks = next(item["tasks"] for item in result if "tasks" in item)
        seen = set()
        for t in tasks:
            key = (t.get("module", ""), t.get("param", ""))
            assert key not in seen, f"Duplicate task found: {t}"
            seen.add(key)

    def test_profile_has_exactly_one_social_entry(self, mock_location_geo):
        """Profile list must contain exactly ONE dict with key 'social'."""
        from modules.github.github_tasks import p_github

        mock_session_instance = _make_session_mock()
        with patch(
            "modules.github.github_tasks.requests.Session",
            return_value=mock_session_instance,
        ):
            result = p_github("testuser")

        profile = next(item["profile"] for item in result if "profile" in item)
        social_entries = [p for p in profile if "social" in p]
        assert len(social_entries) == 1, (
            f"Expected exactly 1 social entry in profile, got {len(social_entries)}"
        )

    def test_profile_social_contains_all_sources(self, mock_location_geo):
        """The single profile social entry must contain Github, Blog, Twitter,
        and Linkedin — all social sources merged into one list."""
        from modules.github.github_tasks import p_github

        mock_session_instance = _make_session_mock()
        with patch(
            "modules.github.github_tasks.requests.Session",
            return_value=mock_session_instance,
        ):
            result = p_github("testuser")

        profile = next(item["profile"] for item in result if "profile" in item)
        social_entry = next(p for p in profile if "social" in p)
        social_names = [s["name"] for s in social_entry["social"]]

        # Blog (from raw_node["blog"]), Twitter + Linkedin (from social_accounts),
        # Github (profile link) — all must be in the single merged list.
        assert "Blog" in social_names, f"Blog missing from social: {social_names}"
        assert "Twitter" in social_names, f"Twitter missing from social: {social_names}"
        assert "Linkedin" in social_names, (
            f"Linkedin missing from social: {social_names}"
        )
        assert "Github" in social_names, f"Github missing from social: {social_names}"


# ===========================================================================
# TestSSHKeyTimeline — SSH key creation dates in timeline
# ===========================================================================


class TestSSHKeyTimeline:
    """Tests for SSH key created_at dates appearing in the timeline."""

    def test_ssh_key_timeline_entry_present(self, mock_location_geo):
        """SSH key creation date appears in timeline."""
        from modules.github.github_tasks import p_github

        mock_session_instance = _make_session_mock()
        with patch(
            "modules.github.github_tasks.requests.Session",
            return_value=mock_session_instance,
        ):
            result = p_github("testuser")

        timeline = next(item["timeline"] for item in result if "timeline" in item)
        key_entries = [t for t in timeline if "SSH Key Added" in t.get("action", "")]
        assert len(key_entries) == 1
        assert "ssh-rsa" in key_entries[0]["action"]
        assert key_entries[0]["icon"] == "fas fa-key"

    def test_ssh_key_timeline_date_format(self, mock_location_geo):
        """SSH key timeline entry date matches YYYY/MM/DD HH:MM:SS format."""
        from modules.github.github_tasks import p_github

        mock_session_instance = _make_session_mock()
        with patch(
            "modules.github.github_tasks.requests.Session",
            return_value=mock_session_instance,
        ):
            result = p_github("testuser")

        timeline = next(item["timeline"] for item in result if "timeline" in item)
        key_entries = [t for t in timeline if "SSH Key Added" in t.get("action", "")]
        assert key_entries[0]["date"] == "2021/03/01 00:00:00"

    def test_no_keys_no_key_timeline_entries(self, mock_location_geo):
        """When keys endpoint returns empty list, no key timeline entries."""
        from modules.github.github_tasks import p_github

        mock_session_instance = _make_session_mock(keys=[])
        with patch(
            "modules.github.github_tasks.requests.Session",
            return_value=mock_session_instance,
        ):
            result = p_github("testuser")

        timeline = next(item["timeline"] for item in result if "timeline" in item)
        key_entries = [t for t in timeline if "SSH Key Added" in t.get("action", "")]
        assert len(key_entries) == 0


# ===========================================================================
# TestGistsEndpoint — gists data in graphic and timeline
# ===========================================================================


class TestGistsEndpoint:
    """Tests for the gists API endpoint."""

    def test_gists_section_in_graphic(self, mock_location_geo):
        """gists section appears in graphic when endpoint returns data."""
        from modules.github.github_tasks import p_github

        mock_session_instance = _make_session_mock()
        with patch(
            "modules.github.github_tasks.requests.Session",
            return_value=mock_session_instance,
        ):
            result = p_github("testuser")

        graphic = next(item["graphic"] for item in result if "graphic" in item)
        section_keys = [next(iter(s.keys())) for s in graphic]
        assert "gists" in section_keys

        gists = next(s["gists"] for s in graphic if "gists" in s)
        assert len(gists) == 2

    def test_gists_section_fields(self, mock_location_geo):
        """Each gist entry has description, created_at, updated_at, public."""
        from modules.github.github_tasks import p_github

        mock_session_instance = _make_session_mock()
        with patch(
            "modules.github.github_tasks.requests.Session",
            return_value=mock_session_instance,
        ):
            result = p_github("testuser")

        graphic = next(item["graphic"] for item in result if "graphic" in item)
        gists = next(s["gists"] for s in graphic if "gists" in s)
        for gist in gists:
            assert "description" in gist
            assert "created_at" in gist
            assert "updated_at" in gist
            assert "public" in gist

    def test_gist_creation_in_timeline(self, mock_location_geo):
        """Gist creation dates appear in timeline."""
        from modules.github.github_tasks import p_github

        mock_session_instance = _make_session_mock()
        with patch(
            "modules.github.github_tasks.requests.Session",
            return_value=mock_session_instance,
        ):
            result = p_github("testuser")

        timeline = next(item["timeline"] for item in result if "timeline" in item)
        gist_entries = [t for t in timeline if "Created gist" in t.get("action", "")]
        assert len(gist_entries) == 2  # 2 gists in GITHUB_GISTS_RESPONSE

    def test_gist_with_description_in_timeline_action(self, mock_location_geo):
        """Gist timeline entry includes description in action string."""
        from modules.github.github_tasks import p_github

        mock_session_instance = _make_session_mock()
        with patch(
            "modules.github.github_tasks.requests.Session",
            return_value=mock_session_instance,
        ):
            result = p_github("testuser")

        timeline = next(item["timeline"] for item in result if "timeline" in item)
        gist_entries = [t for t in timeline if "Created gist" in t.get("action", "")]
        actions = [t["action"] for t in gist_entries]
        assert any("My useful script" in a for a in actions)

    def test_gist_empty_description_uses_placeholder(self, mock_location_geo):
        """Gist with no description uses '(no description)' in timeline."""
        from modules.github.github_tasks import p_github

        mock_session_instance = _make_session_mock()
        with patch(
            "modules.github.github_tasks.requests.Session",
            return_value=mock_session_instance,
        ):
            result = p_github("testuser")

        timeline = next(item["timeline"] for item in result if "timeline" in item)
        gist_entries = [t for t in timeline if "Created gist" in t.get("action", "")]
        actions = [t["action"] for t in gist_entries]
        assert any("(no description)" in a for a in actions)

    def test_no_gists_section_absent(self, mock_location_geo):
        """When gists endpoint returns empty list, gists section absent."""
        from modules.github.github_tasks import p_github

        mock_session_instance = _make_session_mock(gists=[])
        with patch(
            "modules.github.github_tasks.requests.Session",
            return_value=mock_session_instance,
        ):
            result = p_github("testuser")

        graphic = next(item["graphic"] for item in result if "graphic" in item)
        section_keys = [next(iter(s.keys())) for s in graphic]
        assert "gists" not in section_keys


# ===========================================================================
# TestOrgsEnrichment — orgs in profile and gather nodes
# ===========================================================================


class TestOrgsEnrichment:
    """Tests for orgs data enriching profile and gather nodes."""

    def test_org_added_to_profile(self, mock_location_geo):
        """Org login names are added to profile as organization entries."""
        from modules.github.github_tasks import p_github

        mock_session_instance = _make_session_mock()
        with patch(
            "modules.github.github_tasks.requests.Session",
            return_value=mock_session_instance,
        ):
            result = p_github("testuser")

        profile = next(item["profile"] for item in result if "profile" in item)
        org_entries = [p for p in profile if "organization" in p]
        org_names = [p["organization"] for p in org_entries]
        assert "testorg" in org_names

    def test_org_creates_gather_node(self, mock_location_geo):
        """Each org gets a GitOrg_* gather node."""
        from modules.github.github_tasks import p_github

        mock_session_instance = _make_session_mock()
        with patch(
            "modules.github.github_tasks.requests.Session",
            return_value=mock_session_instance,
        ):
            result = p_github("testuser")

        graphic = next(item["graphic"] for item in result if "graphic" in item)
        github_section = next(s["github"] for s in graphic if "github" in s)
        org_node = next(
            (g for g in github_section if g.get("name-node") == "GitOrg_testorg"),
            None,
        )
        assert org_node is not None
        assert org_node["subtitle"] == "testorg"
        assert org_node["icon"] == "fas fa-users"

    def test_no_orgs_no_org_profile_entries(self, mock_location_geo):
        """When orgs is empty, no additional organization entries in profile."""
        from modules.github.github_tasks import p_github

        mock_session_instance = _make_session_mock(orgs=[])
        with patch(
            "modules.github.github_tasks.requests.Session",
            return_value=mock_session_instance,
        ):
            result = p_github("testuser")

        profile = next(item["profile"] for item in result if "profile" in item)
        # Only the company-based organization should exist
        org_entries = [p for p in profile if p.get("organization") == "testorg"]
        assert len(org_entries) == 0


# ===========================================================================
# TestBioInProfile — bio added to profile
# ===========================================================================


class TestBioInProfile:
    """Tests for bio field being added to the profile section."""

    def test_bio_in_profile(self, mock_location_geo):
        """When bio is set, profile contains a bio entry."""
        from modules.github.github_tasks import p_github

        mock_session_instance = _make_session_mock()
        with patch(
            "modules.github.github_tasks.requests.Session",
            return_value=mock_session_instance,
        ):
            result = p_github("testuser")

        profile = next(item["profile"] for item in result if "profile" in item)
        bio_entries = [p for p in profile if "bio" in p]
        assert len(bio_entries) == 1
        assert bio_entries[0]["bio"] == "Developer. github: @testuser"

    def test_no_bio_no_bio_in_profile(self, mock_location_geo):
        """When bio is None, no bio entry in profile."""
        from modules.github.github_tasks import p_github

        user_no_bio = GITHUB_USER_RESPONSE.copy()
        user_no_bio["bio"] = None

        mock_session_instance = _make_session_mock(user=user_no_bio)
        with patch(
            "modules.github.github_tasks.requests.Session",
            return_value=mock_session_instance,
        ):
            result = p_github("testuser")

        profile = next(item["profile"] for item in result if "profile" in item)
        bio_entries = [p for p in profile if "bio" in p]
        assert len(bio_entries) == 0
