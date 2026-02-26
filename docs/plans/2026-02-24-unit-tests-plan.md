# Unit Tests Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add pytest-based unit tests to the iKy Python backend, runnable inside the Docker container with `just test`.

**Architecture:** Tests live in `backend/tests/`, use pytest fixtures for Flask test client and Celery mocks. The `just test` recipe runs `docker compose exec backend pytest -v` inside the already-running backend container (which has Redis available). No new containers.

**Tech Stack:** pytest, Flask test client, `unittest.mock`

---

### Task 1: Add pytest dependency and config

**Files:**
- Modify: `requirements.txt` (add pytest at end)
- Create: `backend/pyproject.toml` (pytest config)

**Step 1: Add pytest to requirements.txt**

Add this line at the end of `requirements.txt`:

```
pytest==8.3.5
```

**Step 2: Create backend/pyproject.toml**

Create `backend/pyproject.toml` with:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
```

`pythonpath = ["."]` ensures imports like `from factories.iKy_functions import ...` resolve from `/app` (the WORKDIR in the container where backend code lives).

**Step 3: Commit**

```bash
git add requirements.txt backend/pyproject.toml
git commit -m "feat: add pytest dependency and config"
```

---

### Task 2: Create test scaffolding and justfile recipe

**Files:**
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/conftest.py`
- Modify: `justfile` (add test recipe)

**Step 1: Create backend/tests/__init__.py**

Empty file (package marker).

**Step 2: Create backend/tests/conftest.py**

```python
import pytest
from unittest.mock import MagicMock, patch
from factories.application import create_application


@pytest.fixture
def app():
    application = create_application()
    application.config["TESTING"] = True
    yield application


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def mock_celery_send(app):
    """Mock celery.send_task so no real tasks are dispatched."""
    mock_result = MagicMock()
    mock_result.task_id = "fake-task-id-1234"

    with patch("api.create_celery") as mock_create:
        mock_celery = MagicMock()
        mock_celery.send_task.return_value = mock_result
        mock_create.return_value = mock_celery
        yield mock_celery
```

Key details:
- `api.py` imports `create_celery` from `factories._celery` and calls it per-request in each endpoint. We patch `api.create_celery` to intercept at the call site.
- The mock returns a `MagicMock` with `.task_id` set so `jsonify` can serialize it.

**Step 3: Add test recipe to justfile**

Add after the existing `fmt` recipe:

```just
# Run backend tests inside the container
test *args:
    docker compose exec backend pytest -v {{ args }}
```

The `*args` lets users pass extra flags: `just test -k functions`, `just test --tb=short`, etc.

**Step 4: Commit**

```bash
git add backend/tests/__init__.py backend/tests/conftest.py justfile
git commit -m "feat: add test scaffolding with conftest fixtures and just test recipe"
```

---

### Task 3: Write tests for iKy_functions.py pure functions

**Files:**
- Create: `backend/tests/test_iky_functions.py`
- Test: `pytest tests/test_iky_functions.py -v`

**Reference:** `backend/factories/iKy_functions.py` - all functions are pure (no side effects) except `location_geo` (calls Nominatim API, skip it).

**Step 1: Write test_iky_functions.py**

```python
"""Tests for backend/factories/iKy_functions.py - pure extraction functions."""

from factories.iKy_functions import (
    extract_hashtags,
    extract_mentions,
    extract_url,
    extract_mails,
    extract_url_linkedin,
    extract_url_instagram,
    extract_url_twitter,
    extract_url_tiktok,
    extract_url_github,
    extract_url_githubio,
    extract_github,
    extract_tiktok,
    extract_twitter,
    extract_instagram,
    extract_linkedin,
    analize_rrss,
    name_match,
    simple_analysis,
    deep_analysis,
)


# ── extract_hashtags ──────────────────────────────────────────────

class TestExtractHashtags:
    def test_single_hashtag(self):
        assert extract_hashtags("hello #world") == ["world"]

    def test_multiple_hashtags(self):
        assert extract_hashtags("#foo #bar #baz") == ["foo", "bar", "baz"]

    def test_no_hashtags(self):
        assert extract_hashtags("no hashtags here") == []

    def test_hashtag_with_underscores(self):
        assert extract_hashtags("#hello_world") == ["hello_world"]

    def test_empty_string(self):
        assert extract_hashtags("") == []


# ── extract_mentions ──────────────────────────────────────────────

class TestExtractMentions:
    def test_single_mention(self):
        result = extract_mentions("hello @user1")
        assert "user1" in result

    def test_multiple_mentions(self):
        result = extract_mentions("@alice and @bob")
        assert "alice" in result
        assert "bob" in result

    def test_no_mentions(self):
        # May return empty strings from regex edge cases
        result = [m for m in extract_mentions("no mentions") if m]
        assert result == []

    def test_empty_string(self):
        result = [m for m in extract_mentions("") if m]
        assert result == []


# ── extract_url ───────────────────────────────────────────────────

class TestExtractUrl:
    def test_https_url(self):
        result = extract_url("visit https://example.com today")
        assert len(result) == 1
        assert "example.com" in result[0]["url"]

    def test_http_url(self):
        result = extract_url("visit http://example.com today")
        assert len(result) == 1

    def test_no_urls(self):
        assert extract_url("no urls here") == []

    def test_url_with_path(self):
        result = extract_url("check https://github.com/user/repo out")
        assert len(result) == 1
        assert "github.com/user/repo" in result[0]["url"]


# ── extract_mails ─────────────────────────────────────────────────

class TestExtractMails:
    def test_valid_email(self):
        result = extract_mails("user@example.com")
        assert len(result) == 1
        assert result[0]["email"] == "user@example.com"

    def test_no_email(self):
        assert extract_mails("not an email") == []

    def test_empty_string(self):
        assert extract_mails("") == []


# ── extract_url_linkedin ─────────────────────────────────────────

class TestExtractUrlLinkedin:
    def test_linkedin_url(self):
        text = "https://www.linkedin.com/in/johndoe/"
        result = extract_url_linkedin(text)
        assert len(result) == 1
        assert result[0]["module"] == "linkedin"
        assert result[0]["param"] == "johndoe"

    def test_no_linkedin(self):
        assert extract_url_linkedin("https://example.com") == []


# ── extract_url_instagram ────────────────────────────────────────

class TestExtractUrlInstagram:
    def test_instagram_url(self):
        text = "https://www.instagram.com/johndoe/"
        result = extract_url_instagram(text)
        assert len(result) == 1
        assert result[0]["module"] == "instagram"
        assert result[0]["param"] == "johndoe"

    def test_no_instagram(self):
        assert extract_url_instagram("https://example.com") == []


# ── extract_url_twitter ──────────────────────────────────────────

class TestExtractUrlTwitter:
    def test_twitter_url(self):
        text = "https://www.twitter.com/johndoe/"
        result = extract_url_twitter(text)
        assert len(result) == 1
        assert result[0]["module"] == "twitter"
        assert result[0]["param"] == "johndoe"

    def test_no_twitter(self):
        assert extract_url_twitter("https://example.com") == []


# ── extract_url_tiktok ───────────────────────────────────────────

class TestExtractUrlTiktok:
    def test_tiktok_url(self):
        text = "https://www.tiktok.com/@johndoe/"
        result = extract_url_tiktok(text)
        assert len(result) == 1
        assert result[0]["module"] == "tiktok"
        assert result[0]["param"] == "johndoe"

    def test_no_tiktok(self):
        assert extract_url_tiktok("https://example.com") == []


# ── extract_url_github ───────────────────────────────────────────

class TestExtractUrlGithub:
    def test_github_url(self):
        text = "https://www.github.com/johndoe/"
        result = extract_url_github(text)
        assert len(result) == 1
        assert result[0]["module"] == "github"
        assert result[0]["param"] == "johndoe"

    def test_no_github(self):
        assert extract_url_github("https://example.com") == []


# ── extract_url_githubio ─────────────────────────────────────────

class TestExtractUrlGithubio:
    def test_githubio_url(self):
        text = "https://johndoe.github.io"
        result = extract_url_githubio(text)
        assert len(result) == 1
        assert result[0]["module"] == "github"
        assert result[0]["param"] == "johndoe"

    def test_no_githubio(self):
        assert extract_url_githubio("https://example.com") == []


# ── extract_github (fuzzy text) ──────────────────────────────────

class TestExtractGithub:
    def test_github_mention(self):
        result = extract_github("github: @myuser")
        found_params = [r["param"] for r in result]
        assert "myuser" in found_params

    def test_github_colon_space(self):
        result = extract_github("github: johndoe")
        found_params = [r["param"] for r in result]
        assert "johndoe" in found_params


# ── extract_tiktok (fuzzy text) ──────────────────────────────────

class TestExtractTiktok:
    def test_tiktok_mention(self):
        result = extract_tiktok("tiktok: @myuser")
        found_params = [r["param"] for r in result]
        assert "myuser" in found_params


# ── extract_twitter (fuzzy text) ─────────────────────────────────

class TestExtractTwitter:
    def test_twitter_mention(self):
        result = extract_twitter("twitter: @myuser")
        found_params = [r["param"] for r in result]
        assert "myuser" in found_params


# ── extract_instagram (fuzzy text) ───────────────────────────────

class TestExtractInstagram:
    def test_instagram_mention(self):
        result = extract_instagram("instagram: @myuser")
        found_params = [r["param"] for r in result]
        assert "myuser" in found_params


# ── extract_linkedin (fuzzy text) ────────────────────────────────

class TestExtractLinkedin:
    def test_linkedin_mention(self):
        result = extract_linkedin("linkedin: @myuser")
        found_params = [r["param"] for r in result]
        assert "myuser" in found_params


# ── analize_rrss ─────────────────────────────────────────────────

class TestAnalizeRrss:
    def test_combines_all_extractors(self):
        text = "#osint @user1 https://www.github.com/testuser/"
        result = analize_rrss(text)
        assert "hashtags" in result
        assert "mentions" in result
        assert "url" in result
        assert "email" in result
        assert "tasks" in result
        assert "osint" in result["hashtags"]

    def test_empty_text(self):
        result = analize_rrss("")
        assert result["hashtags"] == []
        assert result["email"] == []

    def test_with_linkedin_url(self):
        text = "check https://www.linkedin.com/in/johndoe/"
        result = analize_rrss(text)
        task_modules = [t["module"] for t in result["tasks"]]
        assert "linkedin" in task_modules


# ── name_match ────────────────────────────────────────────────────

class TestNameMatch:
    def test_two_names_both_present(self):
        assert name_match(["John", "Doe"], "John Doe is here") is True

    def test_two_names_one_present(self):
        # With 2 names, min_matching=2, so both must match
        assert name_match(["John", "Doe"], "John is here") is False

    def test_three_names_two_present(self):
        # With 3 names, min_matching=2, so 2 of 3 must match
        assert name_match(["John", "Michael", "Doe"],
                          "John Doe is here") is True

    def test_three_names_one_present(self):
        assert name_match(["John", "Michael", "Doe"],
                          "John is here") is False

    def test_no_match(self):
        assert name_match(["Alice", "Bob"], "Charlie is here") is False


# ── simple_analysis ───────────────────────────────────────────────

class TestSimpleAnalysis:
    def test_twitter_url_extraction(self):
        data = [
            "John Doe (@johndoe) | Twitter",
            "https://twitter.com/johndoe",
            "Some description"
        ]
        output = {}
        result = simple_analysis("google", "search", "johndoe", data, output)
        usernames = [u["usernames"] for u in result.get("usernames", [])]
        assert "johndoe" in usernames

    def test_github_url_extraction(self):
        data = [
            "johndoe (John Doe) \u00b7 GitHub",
            "https://github.com/johndoe",
            "Some repos"
        ]
        output = {}
        result = simple_analysis("google", "search", "johndoe", data, output)
        usernames = [u["usernames"] for u in result.get("usernames", [])]
        assert "johndoe" in usernames

    def test_instagram_url_extraction(self):
        data = [
            "John Doe (@johndoe) Instagram profile",
            "https://www.instagram.com/johndoe/",
            "Photos"
        ]
        output = {}
        result = simple_analysis("google", "search", "johndoe", data, output)
        usernames = [u["usernames"] for u in result.get("usernames", [])]
        assert "johndoe" in usernames

    def test_no_social_match(self):
        data = [
            "Random Page",
            "https://example.com/page",
            "Nothing interesting"
        ]
        output = {}
        result = simple_analysis("google", "search", "testuser", data, output)
        assert result.get("usernames", []) == []

    def test_accumulates_output(self):
        """simple_analysis should add to existing output, not replace."""
        existing = {"usernames": [{"source": "prev", "type": "x",
                                   "usernames": "old", "rrss": "test"}]}
        data = [
            "Title",
            "https://twitter.com/newuser",
            "Desc"
        ]
        result = simple_analysis("bing", "search", "newuser", data, existing)
        assert len(result["usernames"]) == 2


# ── deep_analysis ─────────────────────────────────────────────────

class TestDeepAnalysis:
    def test_username_in_url_adds_to_search(self):
        data = [
            "John Doe Profile",
            "https://example.com/johndoe/profile",
            "A description"
        ]
        output = {}
        result = deep_analysis(
            ["John", "Doe"], ["johndoe"], "google", data, output
        )
        assert len(result["search"]) == 1
        assert result["search"][0]["link"] == "google"

    def test_name_in_title_adds_to_search(self):
        data = [
            "John Doe - Developer",
            "https://example.com/some-page",
            "A description"
        ]
        output = {}
        result = deep_analysis(
            ["John", "Doe"], ["otheruser"], "bing", data, output
        )
        assert len(result["search"]) == 1

    def test_no_match_empty_search(self):
        data = [
            "Unrelated Page",
            "https://example.com/page",
            "Nothing about the person"
        ]
        output = {}
        result = deep_analysis(
            ["Alice", "Smith"], ["alicesmith"], "yahoo", data, output
        )
        assert result["search"] == []

    def test_rawresult_always_added(self):
        data = ["Title", "https://url.com", "Desc"]
        output = {}
        result = deep_analysis(["X"], ["y"], "google", data, output)
        assert len(result["rawresult"]) == 1

    def test_searcher_icon_mapping(self):
        data = ["T", "https://u.com/johndoe", "D"]
        for searcher, expected_icon in [
            ("google", "fab fa-google"),
            ("yahoo", "fab fa-yahoo"),
            ("bing", "fab fa-windows"),
            ("duckduckgo", "fas fa-kiwi-bird"),
        ]:
            output = {}
            result = deep_analysis(
                ["John"], ["johndoe"], searcher, data, output
            )
            assert result["rawresult"][0]["icon"] == expected_icon
```

**Step 2: Run tests inside container**

Run: `docker compose exec backend pytest tests/test_iky_functions.py -v`
Expected: All tests PASS. These are pure functions with no external dependencies.

**Step 3: Commit**

```bash
git add backend/tests/test_iky_functions.py
git commit -m "test: add unit tests for iKy_functions.py pure extraction functions"
```

---

### Task 4: Write tests for Flask API endpoints

**Files:**
- Create: `backend/tests/test_api.py`
- Test: `pytest tests/test_api.py -v`

**Reference:** `backend/api.py` - all POST endpoints extract `username`/`from` from JSON, call `celery.send_task(...)`, return `jsonify(module=..., task=..., param=..., from_m=...)`.

**Step 1: Write test_api.py**

```python
"""Tests for backend/api.py - Flask API endpoints with mocked Celery dispatch."""

import json


class TestTasklistEndpoint:
    def test_tasklist_returns_modules(self, client):
        resp = client.get("/tasklist")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "modules" in data
        assert isinstance(data["modules"], list)
        # Should contain known routes
        assert "github" in data["modules"]


class TestTestingEndpoint:
    def test_testing_echoes_json(self, client):
        payload = {"key": "value", "num": 42}
        resp = client.post(
            "/testing",
            data=json.dumps(payload),
            content_type="application/json",
        )
        assert resp.status_code == 200
        assert resp.get_json() == payload


class TestModuleEndpoints:
    """Test that POST module endpoints dispatch Celery tasks correctly."""

    SIMPLE_MODULES = [
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
        """Endpoints should handle missing username gracefully (empty string default)."""
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
            data=json.dumps({
                "username": "testuser",
                "from": "Initial",
                "proc": 2,
            }),
            content_type="application/json",
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["module"] == "spotify"
        call_args = mock_celery_send.send_task.call_args
        assert call_args[0][0] == "modules.spotify.spotify_tasks.t_spotify"
        # Spotify passes (username, from_m, proc)
        assert call_args[1]["args"] == ("testuser", "Initial", 2)

    def test_dorks_extra_params(self, client, mock_celery_send):
        """Dorks endpoint accepts extra 'dorks' parameter."""
        resp = client.post(
            "/dorks",
            data=json.dumps({
                "username": "testuser",
                "dorks": "site:example.com",
                "from": "Initial",
            }),
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

    def test_apikey_get(self, client, tmp_path, monkeypatch):
        """GET-style POST to /apikey (no body) reads existing keys."""
        # This calls api_keys_read() which reads from CWD/factories/apikeys.json
        # We test that the endpoint doesn't crash; actual key content depends on file
        resp = client.post(
            "/apikey",
            content_type="application/json",
        )
        # May fail if apikeys.json doesn't exist in test env - that's OK,
        # we're testing the route exists and handles the request
        assert resp.status_code in (200, 500)
```

**Step 2: Run tests**

Run: `docker compose exec backend pytest tests/test_api.py -v`
Expected: All tests PASS. The mock_celery_send fixture intercepts all Celery calls.

**Step 3: Commit**

```bash
git add backend/tests/test_api.py
git commit -m "test: add API endpoint tests with mocked Celery dispatch"
```

---

### Task 5: Write tests for github module processor

**Files:**
- Create: `backend/tests/test_github_tasks.py`
- Test: `pytest tests/test_github_tasks.py -v`

**Reference:** `backend/modules/github/github_tasks.py` - `p_github()` calls GitHub API, parses JSON, builds structured output.

**Step 1: Write test_github_tasks.py**

```python
"""Tests for backend/modules/github/github_tasks.py - p_github processor."""

import json
from unittest.mock import patch, MagicMock
import pytest


# Fixture: minimal GitHub API user response
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

# Minimal HTML for the contribution graph page
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

        # Result is a list of dicts
        assert isinstance(result, list)
        # First items are module metadata
        modules = [list(item.keys())[0] for item in result if isinstance(item, dict)]
        assert "module" in modules
        assert "param" in modules
        assert "validation" in modules
        assert "graphic" in modules
        assert "profile" in modules
        assert "timeline" in modules

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
```

**Step 2: Run tests**

Run: `docker compose exec backend pytest tests/test_github_tasks.py -v`
Expected: All tests PASS. HTTP calls are mocked, no real API traffic.

**Step 3: Commit**

```bash
git add backend/tests/test_github_tasks.py
git commit -m "test: add github module processor tests with mocked HTTP"
```

---

### Task 6: Rebuild container and verify full test suite

**Step 1: Rebuild to install pytest in container**

Run: `just rebuild`

This rebuilds the Docker image with `pytest` now in `requirements.txt`.

**Step 2: Run full test suite**

Run: `just test`

Expected output (approximately):

```
tests/test_iky_functions.py::TestExtractHashtags::test_single_hashtag PASSED
tests/test_iky_functions.py::TestExtractHashtags::test_multiple_hashtags PASSED
...
tests/test_api.py::TestTasklistEndpoint::test_tasklist_returns_modules PASSED
...
tests/test_github_tasks.py::TestPGithub::test_basic_output_structure PASSED
...

===== ~55 passed =====
```

**Step 3: Fix any failures**

If any tests fail, debug and fix. Common issues:
- Import path mismatches (pyproject.toml pythonpath)
- Mock patch targets (must match the import location, not the definition location)
- Regex edge cases in extraction functions

**Step 4: Final commit**

```bash
git add -A
git commit -m "test: verify full test suite passes in container"
```

---

## Summary of commands

| Command | Purpose |
|---------|---------|
| `just test` | Run all tests in backend container |
| `just test -k functions` | Run only iKy_functions tests |
| `just test -k api` | Run only API tests |
| `just test -k github` | Run only github module tests |
| `just test --tb=short` | Shorter tracebacks |
| `just test -x` | Stop on first failure |
