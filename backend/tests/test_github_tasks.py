"""Tests for backend/modules/github/github_tasks.py - p_github processor."""

import json
from unittest.mock import patch, MagicMock
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
            "Accessability": "place",
            "Latitude": -34.6037,
            "Longitude": -58.3816,
            "Name": "Buenos Aires",
            "Time": "",
        }
        yield mock_geo


class TestPGithub:
    def test_basic_output_structure(self, mock_github_api, mock_location_geo):
        from modules.github.github_tasks import p_github

        result = p_github("testuser", "Initial")

        assert isinstance(result, list)
        keys = [list(item.keys())[0] for item in result if isinstance(item, dict)]
        assert "module" in keys
        assert "param" in keys
        assert "validation" in keys
        assert "graphic" in keys
        assert "profile" in keys
        assert "timeline" in keys

    def test_validation_initial(self, mock_github_api, mock_location_geo):
        from modules.github.github_tasks import p_github

        result = p_github("testuser", "Initial")
        validation = next(
            item["validation"] for item in result if "validation" in item
        )
        assert validation == "no"

    def test_validation_non_initial(self, mock_github_api, mock_location_geo):
        from modules.github.github_tasks import p_github

        result = p_github("testuser", "github")
        validation = next(
            item["validation"] for item in result if "validation" in item
        )
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
