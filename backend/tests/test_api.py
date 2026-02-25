"""Tests for backend/api.py - Flask API endpoints with mocked Celery dispatch."""

import json
from typing import ClassVar


class TestTasklistEndpoint:
    def test_tasklist_returns_modules(self, client):
        resp = client.get("/tasklist")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "modules" in data
        assert isinstance(data["modules"], list)
        assert "github" in data["modules"]


class TestTestingEndpoint:
    def test_testing_echoes_json(self, app, client):
        app.debug = True
        payload = {"key": "value", "num": 42}
        resp = client.post(
            "/testing",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert resp.get_json() == payload

    def test_testing_returns_404_in_production(self, app, client):
        app.debug = False
        resp = client.post(
            "/testing",
            data=json.dumps({"key": "value"}),
            content_type="application/json",
        )
        assert resp.status_code == 404


class TestModuleEndpoints:
    """Test that POST module endpoints dispatch Celery tasks correctly."""

    SIMPLE_MODULES: ClassVar[list] = [
        ("github", "modules.github.github_tasks.t_github"),
        ("twitter", "modules.twitter.twitter_tasks.t_twitter"),
        ("linkedin", "modules.linkedin.linkedin_tasks.t_linkedin"),
        ("keybase", "modules.keybase.keybase_tasks.t_keybase"),
        ("search", "modules.search.search_tasks.t_search"),
        ("reddit", "modules.reddit.reddit_tasks.t_reddit"),
        ("gitlab", "modules.gitlab.gitlab_tasks.t_gitlab"),
        ("mastodon", "modules.mastodon.mastodon_tasks.t_mastodon"),
        ("holehe", "modules.holehe.holehe_tasks.t_holehe"),
        ("sherlock", "modules.sherlock.sherlock_tasks.t_sherlock"),
    ]

    def test_module_dispatches_celery_task(self, client, mock_celery_send):
        """Each module endpoint should call celery.send_task with the right path."""
        for route, expected_task in self.SIMPLE_MODULES:
            mock_celery_send.send_task.reset_mock()
            resp = client.post(
                f"/{route}",
                data=json.dumps({"username": "testuser", "from": "Initial"}),
                content_type="application/json",
            )
            assert resp.status_code == 200, f"/{route} returned {resp.status_code}"
            data = resp.get_json()
            assert data["module"] == route, f"/{route} wrong module"
            assert data["task"] == "fake-task-id-1234"
            assert data["param"] == "testuser"
            mock_celery_send.send_task.assert_called_once()
            call_args = mock_celery_send.send_task.call_args
            assert call_args[0][0] == expected_task, (
                f"/{route} dispatched wrong task: {call_args[0][0]}"
            )

    def test_endpoint_with_empty_username(self, client, mock_celery_send):
        """Endpoints should handle missing username gracefully."""
        resp = client.post(
            "/github",
            data=json.dumps({"from": "Initial"}),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["param"] == ""

    def test_spotify_extra_params(self, client, mock_celery_send):
        """Spotify endpoint accepts extra 'proc' parameter."""
        resp = client.post(
            "/spotify",
            data=json.dumps(
                {
                    "username": "testuser",
                    "from": "Initial",
                    "proc": 2,
                }
            ),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["module"] == "spotify"
        call_args = mock_celery_send.send_task.call_args
        assert call_args[0][0] == "modules.spotify.spotify_tasks.t_spotify"

    def test_dorks_extra_params(self, client, mock_celery_send):
        """Dorks endpoint accepts extra 'dorks' parameter."""
        resp = client.post(
            "/dorks",
            data=json.dumps(
                {
                    "username": "testuser",
                    "dorks": "site:example.com",
                    "from": "Initial",
                }
            ),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["module"] == "dorks"


class TestStateAndResultEndpoints:
    def test_state_endpoint(self, client, mock_celery_send):
        """GET /state/<id>/<app> should return state info."""
        mock_celery_send.AsyncResult.return_value.state = "PENDING"
        resp = client.get("/state/fake-id/github")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "state" in data
        assert data["task_id"] == "fake-id"
        assert data["task_app"] == "github"
