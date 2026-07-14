"""Tests for the Twitter/X module migration from tweety → twikit.

Tests verify:
- @iky_task decorator migration (no manual boilerplate)
- validation="hard" (no from_m parameter)
- dev_mode golden-file loading via decorator
- output structure compatibility (all required sections present)
- enrichment structure / types
- tweetiment path compatibility (result[3]["raw"][1]["raw_node_tweets"])
- cookie/auth fallback behaviour (mocked)
- registry / dependency / twint cleanup
- pinned tweet enrichment (text fetched best-effort)
- async wrapper behaviour
"""

from __future__ import annotations

import asyncio
import importlib
import json
import sys
import types
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Mock twikit and unavailable factory deps BEFORE any import of twitter_tasks.
# This makes every test in this file resilient to missing optional packages
# (twikit, geopy, etc.) that are only installed inside the Docker container.
# ---------------------------------------------------------------------------


def _make_twikit_mock() -> types.ModuleType:
    """Build a minimal twikit mock hierarchy."""
    errors_mod = types.ModuleType("twikit.errors")

    class _UserNotFound(Exception):
        def __init__(self, status=404, headers=None, message="not found", data=None):
            super().__init__(message)
            self.status = status

    class _UserUnavailable(Exception):
        pass

    errors_mod.UserNotFound = _UserNotFound
    errors_mod.UserUnavailable = _UserUnavailable

    twikit_mod = types.ModuleType("twikit")
    twikit_mod.Client = MagicMock
    twikit_mod.errors = errors_mod

    user_mod = types.ModuleType("twikit.user")
    user_mod.User = MagicMock
    tweet_mod = types.ModuleType("twikit.tweet")
    tweet_mod.Tweet = MagicMock

    # Expose sub-modules as attributes so `twikit.user.User` resolves
    twikit_mod.user = user_mod
    twikit_mod.tweet = tweet_mod

    return twikit_mod, errors_mod, user_mod, tweet_mod


def _make_iky_functions_mock() -> types.ModuleType:
    """Stub for factories.iKy_functions (requires geopy, not installed locally)."""
    mod = types.ModuleType("factories.iKy_functions")
    mod.analize_rrss = MagicMock(return_value={})
    mod.location_geo = MagicMock(return_value=None)
    return mod


_twikit_mod, _twikit_errors, _twikit_user_mod, _twikit_tweet_mod = _make_twikit_mock()

sys.modules.setdefault("twikit", _twikit_mod)
sys.modules.setdefault("twikit.errors", _twikit_errors)
sys.modules.setdefault("twikit.user", _twikit_user_mod)
sys.modules.setdefault("twikit.tweet", _twikit_tweet_mod)
sys.modules.setdefault("factories.iKy_functions", _make_iky_functions_mock())

# Now safe to import twitter_tasks
import modules.twitter.twitter_tasks as twitter_tasks  # noqa: E402

# Keep a reference to the twikit.errors stand-ins for use in tests
TwikitUserNotFound = _twikit_errors.UserNotFound
TwikitUserUnavailable = _twikit_errors.UserUnavailable

# ---------------------------------------------------------------------------
# Helpers — load the golden file once for structure tests
# ---------------------------------------------------------------------------

GOLDEN_FILE = Path(__file__).parent.parent / "outputs" / "output-twitter.json"
BACKEND_DIR = Path(__file__).parent.parent
REQUIREMENTS_FILE = BACKEND_DIR.parent / "requirements.txt"
MODULE_REGISTRY_FILE = BACKEND_DIR / "module_registry.py"
TWINT_DIR = BACKEND_DIR / "modules" / "twint"


@pytest.fixture(scope="module")
def golden_data() -> list[dict]:
    assert GOLDEN_FILE.exists(), "output-twitter.json must exist"
    with GOLDEN_FILE.open() as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# 1. Decorator migration — the module must expose a Celery task
# ---------------------------------------------------------------------------


def test_t_twitter_is_celery_task():
    """t_twitter must be a registered Celery task (via @iky_task)."""
    t_twitter = twitter_tasks.t_twitter
    assert callable(t_twitter), "t_twitter must be callable"
    # Celery tasks have .name attribute
    assert hasattr(t_twitter, "name"), "t_twitter must have a .name (Celery task)"
    assert t_twitter.name == "modules.twitter.twitter_tasks.t_twitter"


def test_p_twitter_alias_matches_t_twitter():
    """p_twitter and t_twitter must reference the same object."""
    assert twitter_tasks.p_twitter is twitter_tasks.t_twitter, (
        "t_twitter = p_twitter alias must hold"
    )


def test_no_from_m_parameter():
    """p_twitter must only accept (username,) — no from_m."""
    import inspect

    sig = inspect.signature(twitter_tasks.p_twitter)
    params = list(sig.parameters.keys())
    assert "username" in params or len(params) >= 1, "Must accept username"
    assert "from_m" not in params, "from_m must NOT be a parameter"


# ---------------------------------------------------------------------------
# 2. validation = "hard"
# ---------------------------------------------------------------------------


def test_golden_file_validation_is_hard(golden_data):
    """Golden file must have validation='hard' at index [2]."""
    assert golden_data[2] == {"validation": "hard"}


# ---------------------------------------------------------------------------
# 3. Dev mode — golden file loading via decorator
# ---------------------------------------------------------------------------


def test_dev_mode_returns_golden_file(tmp_path, monkeypatch):
    """When output-twitter.json exists, decorator returns it without API calls."""
    outputs_dir = tmp_path / "outputs"
    outputs_dir.mkdir()
    golden = [{"module": "twitter"}, {"param": "testuser"}, {"validation": "hard"}]
    (outputs_dir / "output-twitter.json").write_text(json.dumps(golden))

    monkeypatch.chdir(tmp_path)

    # Reload the module so the decorator picks up the monkeypatched cwd
    importlib.reload(twitter_tasks)

    with patch.object(
        twitter_tasks, "_run_async", side_effect=AssertionError("API called")
    ):
        result = twitter_tasks.t_twitter("testuser")

    assert result == golden

    # Restore original module state for other tests
    importlib.reload(twitter_tasks)


# ---------------------------------------------------------------------------
# 4. Output structure — all required top-level sections
# ---------------------------------------------------------------------------

REQUIRED_KEYS_AT_INDEX = {
    0: "module",
    1: "param",
    2: "validation",
    3: "raw",
    4: "graphic",
    5: "profile",
    6: "timeline",
    7: "tasks",
}


def test_golden_structure_has_all_sections(golden_data):
    """Golden file must have all 8 required top-level sections."""
    assert len(golden_data) >= 8, "Must have at least 8 top-level entries"
    for idx, key in REQUIRED_KEYS_AT_INDEX.items():
        assert key in golden_data[idx], f"Section [{idx}] must have key '{key}'"


REQUIRED_GRAPHIC_SECTIONS = {
    "social",
    "resume",
    "popularity",
    "approval",
    "hashtag",
    "users",
    "tweetslist",
    "week",
    "hour",
    "sources",
    "time",
    "twvsrt",
    "languages",
    "engagement",
}


def test_golden_graphic_has_all_subsections(golden_data):
    """graphic array must contain all required subsection keys."""
    graphic_list = golden_data[4]["graphic"]
    found_keys = {next(iter(item.keys())) for item in graphic_list}
    missing = REQUIRED_GRAPHIC_SECTIONS - found_keys
    assert not missing, f"Missing graphic sections: {missing}"


def test_golden_module_is_twitter(golden_data):
    assert golden_data[0] == {"module": "twitter"}


# ---------------------------------------------------------------------------
# 5. Enrichment structure and types
# ---------------------------------------------------------------------------


def test_golden_enrichment_structure(golden_data):
    """raw[2].raw_node_enrichment must have all expected keys and types."""
    raw_list = golden_data[3]["raw"]
    assert len(raw_list) >= 3, "raw must have at least 3 nodes"
    enrichment = raw_list[2]["raw_node_enrichment"]

    assert isinstance(enrichment["followers_sample"], list)
    assert isinstance(enrichment["following_sample"], list)
    assert isinstance(enrichment["retweeters_sample"], list)
    assert isinstance(enrichment["likers_sample"], list)
    assert isinstance(enrichment["engagement"], dict)
    assert isinstance(enrichment["account_age_days"], int)
    assert isinstance(enrichment["avg_tweets_per_day"], float)
    assert isinstance(enrichment["follower_following_ratio"], float)
    assert isinstance(enrichment["languages"], list)

    eng = enrichment["engagement"]
    assert "avg_likes" in eng
    assert "avg_retweets" in eng
    assert "avg_replies" in eng
    assert "avg_views" in eng
    assert "engagement_rate" in eng
    assert isinstance(eng["engagement_rate"], float)


def test_golden_followers_sample_shape(golden_data):
    """Each follower sample entry must have username, name, followers_count."""
    raw_list = golden_data[3]["raw"]
    enrichment = raw_list[2]["raw_node_enrichment"]
    for entry in enrichment["followers_sample"]:
        assert "username" in entry
        assert "name" in entry
        assert "followers_count" in entry


# ---------------------------------------------------------------------------
# 6. tweetiment path compatibility
# ---------------------------------------------------------------------------


def test_tweetiment_path_raw_node_tweets(golden_data):
    """result[3]['raw'][1]['raw_node_tweets'] must exist and contain tweet objects."""
    raw_node_tweets = golden_data[3]["raw"][1]["raw_node_tweets"]
    assert isinstance(raw_node_tweets, list), "raw_node_tweets must be a list"
    assert len(raw_node_tweets) > 0, "Must have at least one tweet"

    required_fields = {"text", "lang", "created_at"}
    for tweet in raw_node_tweets:
        missing = required_fields - tweet.keys()
        assert not missing, f"Tweet missing fields: {missing}"


def test_tweetiment_path_index_is_stable(golden_data):
    """The exact path result[3]['raw'][1] must be the tweets node."""
    node = golden_data[3]["raw"][1]
    assert "raw_node_tweets" in node, (
        "Index [1] in raw[] must be raw_node_tweets for tweetiment compat"
    )
    assert "raw_node_info" not in node
    assert "raw_node_enrichment" not in node


# ---------------------------------------------------------------------------
# 7. Auth / cookie fallback — mocked unit tests
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_twikit_client():
    """A mock twikit.Client with async methods."""
    client = MagicMock()
    client.load_cookies = MagicMock()
    client.save_cookies = MagicMock()
    client.login = AsyncMock()
    client.get_user_by_screen_name = AsyncMock()
    return client


def test_auth_uses_cookies_when_file_exists(tmp_path, mock_twikit_client):
    """When cookie file exists, load_cookies is called and login is NOT called."""
    cookie_file = tmp_path / "twitter_cookies.json"
    cookie_file.write_text("{}")

    with (
        patch.object(twitter_tasks, "_COOKIE_FILE", cookie_file),
        patch.object(twitter_tasks, "_COOKIE_DIR", tmp_path),
    ):
        asyncio.run(twitter_tasks._authenticate(mock_twikit_client))

    mock_twikit_client.load_cookies.assert_called_once_with(str(cookie_file))
    mock_twikit_client.login.assert_not_called()


def test_auth_raises_when_no_cookie_file_and_no_api_cookies(
    tmp_path, mock_twikit_client
):
    """When no cookie file and no browser cookies, raise with instructions."""
    cookie_file = tmp_path / "twitter_cookies.json"
    # File does NOT exist

    with (
        patch.object(twitter_tasks, "_COOKIE_FILE", cookie_file),
        patch.object(twitter_tasks, "_COOKIE_DIR", tmp_path),
        patch(
            "modules.twitter.twitter_tasks.api_keys_search",
            return_value=False,
        ),
        pytest.raises(Exception, match="iKy - Twitter requires browser cookies"),
    ):
        asyncio.run(twitter_tasks._authenticate(mock_twikit_client))


def test_auth_raises_on_missing_credentials(tmp_path, mock_twikit_client):
    """All auth methods exhausted must raise Exception with actionable iKy message."""
    cookie_file = tmp_path / "twitter_cookies.json"

    with (
        patch.object(twitter_tasks, "_COOKIE_FILE", cookie_file),
        patch.object(twitter_tasks, "_COOKIE_DIR", tmp_path),
        patch(
            "modules.twitter.twitter_tasks.api_keys_search",
            return_value=False,
        ),
        pytest.raises(Exception, match="iKy - Twitter requires browser cookies"),
    ):
        asyncio.run(twitter_tasks._authenticate(mock_twikit_client))


def test_auth_re_authenticates_on_cookie_load_failure(tmp_path, mock_twikit_client):
    """If load_cookies raises and no browser cookies, raise with instructions."""
    cookie_file = tmp_path / "twitter_cookies.json"
    cookie_file.write_text("{}")
    mock_twikit_client.load_cookies.side_effect = Exception("invalid cookies")

    with (
        patch.object(twitter_tasks, "_COOKIE_FILE", cookie_file),
        patch.object(twitter_tasks, "_COOKIE_DIR", tmp_path),
        patch(
            "modules.twitter.twitter_tasks.api_keys_search",
            return_value=False,
        ),
        pytest.raises(Exception, match="iKy - Twitter requires browser cookies"),
    ):
        asyncio.run(twitter_tasks._authenticate(mock_twikit_client))


# ---------------------------------------------------------------------------
# 7b. Cookie-based auth — new twitter_cookies API key flow
# ---------------------------------------------------------------------------

_BROWSER_COOKIES_LIST = json.dumps(
    [
        {"name": "auth_token", "value": "tok123", "domain": ".x.com"},
        {"name": "ct0", "value": "csrf456", "domain": ".x.com"},
        {"name": "twid", "value": "u%3D999", "domain": ".x.com"},
    ]
)
_BROWSER_COOKIES_DICT_EXPECTED = {
    "auth_token": "tok123",
    "ct0": "csrf456",
    "twid": "u%3D999",
}


def test_auth_uses_browser_cookies_from_api_key(tmp_path, mock_twikit_client):
    """When twitter_cookies API key is set, set_cookies + save_cookies are called."""
    cookie_file = tmp_path / "twitter_cookies.json"
    mock_twikit_client.set_cookies = MagicMock()

    def _api_keys(k: str) -> str | bool:
        if k == "twitter_cookies":
            return _BROWSER_COOKIES_LIST
        return False

    with (
        patch.object(twitter_tasks, "_COOKIE_FILE", cookie_file),
        patch.object(twitter_tasks, "_COOKIE_DIR", tmp_path),
        patch("modules.twitter.twitter_tasks.api_keys_search", side_effect=_api_keys),
    ):
        asyncio.run(twitter_tasks._authenticate(mock_twikit_client))

    mock_twikit_client.load_cookies.assert_not_called()
    mock_twikit_client.set_cookies.assert_called_once_with(
        _BROWSER_COOKIES_DICT_EXPECTED
    )
    mock_twikit_client.save_cookies.assert_called_once_with(str(cookie_file))
    mock_twikit_client.login.assert_not_called()


def test_auth_browser_cookies_saved_to_file(tmp_path, mock_twikit_client):
    """After loading browser cookies, save_cookies persists to disk."""
    cookie_file = tmp_path / "twitter_cookies.json"
    mock_twikit_client.set_cookies = MagicMock()

    def _api_keys(k: str) -> str | bool:
        return _BROWSER_COOKIES_LIST if k == "twitter_cookies" else False

    with (
        patch.object(twitter_tasks, "_COOKIE_FILE", cookie_file),
        patch.object(twitter_tasks, "_COOKIE_DIR", tmp_path),
        patch("modules.twitter.twitter_tasks.api_keys_search", side_effect=_api_keys),
    ):
        asyncio.run(twitter_tasks._authenticate(mock_twikit_client))

    mock_twikit_client.save_cookies.assert_called_once_with(str(cookie_file))


def test_auth_file_cookies_take_priority_over_api_key(tmp_path, mock_twikit_client):
    """Cookie file on disk takes priority — api_keys_search is never called."""
    cookie_file = tmp_path / "twitter_cookies.json"
    cookie_file.write_text("{}")
    mock_twikit_client.set_cookies = MagicMock()

    with (
        patch.object(twitter_tasks, "_COOKIE_FILE", cookie_file),
        patch.object(twitter_tasks, "_COOKIE_DIR", tmp_path),
        patch("modules.twitter.twitter_tasks.api_keys_search") as mock_api_search,
    ):
        asyncio.run(twitter_tasks._authenticate(mock_twikit_client))

    mock_twikit_client.load_cookies.assert_called_once_with(str(cookie_file))
    mock_twikit_client.set_cookies.assert_not_called()
    mock_api_search.assert_not_called()


def test_auth_invalid_cookie_json_raises(tmp_path, mock_twikit_client):
    """Invalid JSON in twitter_cookies falls through and raises (no login fallback)."""
    cookie_file = tmp_path / "twitter_cookies.json"
    mock_twikit_client.set_cookies = MagicMock()

    def _api_keys(k: str) -> str | bool:
        if k == "twitter_cookies":
            return "this is not json {"
        return False

    with (
        patch.object(twitter_tasks, "_COOKIE_FILE", cookie_file),
        patch.object(twitter_tasks, "_COOKIE_DIR", tmp_path),
        patch("modules.twitter.twitter_tasks.api_keys_search", side_effect=_api_keys),
        pytest.raises(Exception, match="iKy - Twitter requires browser cookies"),
    ):
        asyncio.run(twitter_tasks._authenticate(mock_twikit_client))

    mock_twikit_client.set_cookies.assert_not_called()


def test_auth_empty_cookie_json_raises(tmp_path, mock_twikit_client):
    """Empty string in twitter_cookies is falsy — raises (no login fallback)."""
    cookie_file = tmp_path / "twitter_cookies.json"
    mock_twikit_client.set_cookies = MagicMock()

    with (
        patch.object(twitter_tasks, "_COOKIE_FILE", cookie_file),
        patch.object(twitter_tasks, "_COOKIE_DIR", tmp_path),
        patch(
            "modules.twitter.twitter_tasks.api_keys_search",
            return_value="",
        ),
        pytest.raises(Exception, match="iKy - Twitter requires browser cookies"),
    ):
        asyncio.run(twitter_tasks._authenticate(mock_twikit_client))

    mock_twikit_client.set_cookies.assert_not_called()


# ---------------------------------------------------------------------------
# 7c. _convert_browser_cookies unit tests
# ---------------------------------------------------------------------------


def test_convert_browser_cookies_list_format():
    """Browser list format → flat {name: value} dict."""
    raw = [
        {"name": "auth_token", "value": "abc"},
        {"name": "ct0", "value": "xyz"},
    ]
    result = twitter_tasks._convert_browser_cookies(raw)
    assert result == {"auth_token": "abc", "ct0": "xyz"}


def test_convert_browser_cookies_dict_passthrough():
    """Already-converted dict passes through unchanged."""
    raw = {"auth_token": "abc", "ct0": "xyz"}
    result = twitter_tasks._convert_browser_cookies(raw)
    assert result == {"auth_token": "abc", "ct0": "xyz"}


def test_convert_browser_cookies_skips_items_without_name():
    """Items without 'name' key are silently skipped."""
    raw = [
        {"name": "auth_token", "value": "abc"},
        {"value": "orphan"},  # no name — skip
        {"name": "ct0", "value": "xyz"},
    ]
    result = twitter_tasks._convert_browser_cookies(raw)
    assert result == {"auth_token": "abc", "ct0": "xyz"}


def test_convert_browser_cookies_empty_value_defaults_to_empty_string():
    """Cookie with no value field gets empty string."""
    raw = [{"name": "guest_id"}]
    result = twitter_tasks._convert_browser_cookies(raw)
    assert result == {"guest_id": ""}


def test_convert_browser_cookies_invalid_type_raises():
    """Non-list, non-dict input raises ValueError."""
    with pytest.raises(ValueError, match="Unexpected cookie format"):
        twitter_tasks._convert_browser_cookies("not-a-list-or-dict")  # type: ignore[arg-type]


def test_twitter_uses_shared_cookie_converter():
    """_convert_browser_cookies must be the shared cookie_utils converter."""
    from factories.cookie_utils import convert_browser_cookies

    assert twitter_tasks._convert_browser_cookies is convert_browser_cookies


def test_auth_no_credentials_raises_with_cookie_instructions(
    tmp_path, mock_twikit_client
):
    """Error message when all auth fails must mention Cookie-Editor and docs/COOKIES.md."""
    cookie_file = tmp_path / "twitter_cookies.json"

    with (
        patch.object(twitter_tasks, "_COOKIE_FILE", cookie_file),
        patch.object(twitter_tasks, "_COOKIE_DIR", tmp_path),
        patch("modules.twitter.twitter_tasks.api_keys_search", return_value=False),
        pytest.raises(Exception) as exc_info,
    ):
        asyncio.run(twitter_tasks._authenticate(mock_twikit_client))

    msg = str(exc_info.value)
    assert "Cookie-Editor" in msg
    assert "docs/COOKIES.md" in msg


def test_fetch_user_raises_iky_on_not_found(mock_twikit_client):
    """UserNotFound twikit exception must map to iKy - User not found."""
    mock_twikit_client.get_user_by_screen_name = AsyncMock(
        side_effect=TwikitUserNotFound(
            status=404, headers={}, message="not found", data={}
        )
    )

    with pytest.raises(Exception, match="iKy - User not found"):
        asyncio.run(twitter_tasks._fetch_user(mock_twikit_client, "ghostuser"))


# ---------------------------------------------------------------------------
# 8. Enrichment fetch is best-effort (no crash on failures)
# ---------------------------------------------------------------------------


def test_enrichment_is_best_effort_on_failure():
    """_fetch_enrichment must return partial data even if all sub-calls fail."""
    mock_user = MagicMock()
    mock_user.profile_banner_url = None
    mock_user.pinned_tweet_ids = None
    mock_user.followers_count = 1000
    mock_user.following_count = 100
    mock_user.statuses_count = 500
    mock_user.created_at = "Sat Apr 11 12:00:00 +0000 2020"
    mock_user.get_followers = AsyncMock(side_effect=Exception("rate limit"))
    mock_user.get_following = AsyncMock(side_effect=Exception("rate limit"))

    result = asyncio.run(twitter_tasks._fetch_enrichment(MagicMock(), mock_user, []))

    assert isinstance(result, dict)
    assert "followers_sample" in result
    assert result["followers_sample"] == []
    assert "following_sample" in result
    assert result["following_sample"] == []
    assert "engagement" in result
    assert isinstance(result["engagement"], dict)


# ---------------------------------------------------------------------------
# 9. Async wrapper behaviour
# ---------------------------------------------------------------------------


def test_run_async_executes_coroutine():
    """_run_async must drive the coroutine to completion and return its value."""

    async def _sample_coro():
        return 42

    result = twitter_tasks._run_async(_sample_coro())
    assert result == 42, "_run_async must return the coroutine's return value"


def test_run_async_propagates_exceptions():
    """_run_async must propagate exceptions raised inside the coroutine."""

    async def _failing_coro():
        raise ValueError("boom")

    with pytest.raises(ValueError, match="boom"):
        twitter_tasks._run_async(_failing_coro())


# ---------------------------------------------------------------------------
# 10. Pinned tweet extraction
# ---------------------------------------------------------------------------


def test_pinned_tweet_text_is_fetched(mock_twikit_client):
    """When pinned_tweet_ids is set, _fetch_enrichment fetches the tweet text."""
    mock_user = MagicMock()
    mock_user.profile_banner_url = None
    mock_user.pinned_tweet_ids = ["1234567890"]
    mock_user.followers_count = 500
    mock_user.following_count = 50
    mock_user.statuses_count = 200
    mock_user.created_at = "Mon Jan 01 00:00:00 +0000 2018"
    mock_user.get_followers = AsyncMock(return_value=[])
    mock_user.get_following = AsyncMock(return_value=[])

    mock_pinned_tweet = MagicMock()
    mock_pinned_tweet.text = "This is the pinned tweet!"
    mock_twikit_client.get_tweet_by_id = AsyncMock(return_value=mock_pinned_tweet)

    result = asyncio.run(
        twitter_tasks._fetch_enrichment(mock_twikit_client, mock_user, [])
    )

    assert result["pinned_tweet"] is not None
    assert result["pinned_tweet"]["id"] == "1234567890"
    assert result["pinned_tweet"]["text"] == "This is the pinned tweet!"
    mock_twikit_client.get_tweet_by_id.assert_called_once_with("1234567890")


def test_pinned_tweet_absent_returns_none():
    """When pinned_tweet_ids is None/empty, pinned_tweet in enrichment is None."""
    mock_user = MagicMock()
    mock_user.profile_banner_url = None
    mock_user.pinned_tweet_ids = None
    mock_user.followers_count = 500
    mock_user.following_count = 50
    mock_user.statuses_count = 200
    mock_user.created_at = "Mon Jan 01 00:00:00 +0000 2018"
    mock_user.get_followers = AsyncMock(return_value=[])
    mock_user.get_following = AsyncMock(return_value=[])

    mock_client = MagicMock()
    mock_client.get_tweet_by_id = AsyncMock()

    result = asyncio.run(twitter_tasks._fetch_enrichment(mock_client, mock_user, []))

    assert result["pinned_tweet"] is None
    mock_client.get_tweet_by_id.assert_not_called()


def test_pinned_tweet_fetch_failure_is_graceful(mock_twikit_client):
    """If get_tweet_by_id raises, pinned_tweet still contains id with empty text."""
    mock_user = MagicMock()
    mock_user.profile_banner_url = None
    mock_user.pinned_tweet_ids = ["999"]
    mock_user.followers_count = 100
    mock_user.following_count = 10
    mock_user.statuses_count = 50
    mock_user.created_at = "Mon Jan 01 00:00:00 +0000 2019"
    mock_user.get_followers = AsyncMock(return_value=[])
    mock_user.get_following = AsyncMock(return_value=[])

    mock_twikit_client.get_tweet_by_id = AsyncMock(
        side_effect=Exception("rate limited")
    )

    result = asyncio.run(
        twitter_tasks._fetch_enrichment(mock_twikit_client, mock_user, [])
    )

    assert result["pinned_tweet"] is not None
    assert result["pinned_tweet"]["id"] == "999"
    assert result["pinned_tweet"]["text"] == ""


# ---------------------------------------------------------------------------
# 11. Protected account (enrichment graceful)
# ---------------------------------------------------------------------------


def test_protected_account_returns_empty_lists():
    """Protected account: followers/following fetch fails → empty lists returned."""
    mock_user = MagicMock()
    mock_user.profile_banner_url = None
    mock_user.pinned_tweet_ids = None
    mock_user.followers_count = 0
    mock_user.following_count = 10
    mock_user.statuses_count = 5
    mock_user.created_at = "Wed Jun 01 00:00:00 +0000 2022"
    # Simulate protected account — get_followers raises Forbidden
    mock_user.get_followers = AsyncMock(side_effect=Exception("Forbidden"))
    mock_user.get_following = AsyncMock(side_effect=Exception("Forbidden"))

    result = asyncio.run(twitter_tasks._fetch_enrichment(MagicMock(), mock_user, []))

    assert result["followers_sample"] == []
    assert result["following_sample"] == []
    # Must not raise — partial data returned
    assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# 12. Registry cleanup — twitter entry uses pass_from=False
# ---------------------------------------------------------------------------


def test_registry_twitter_pass_from_is_false():
    """module_registry.py must have twitter entry with pass_from=False."""
    assert MODULE_REGISTRY_FILE.exists(), "module_registry.py must exist"
    content = MODULE_REGISTRY_FILE.read_text()
    # The registry line should contain t_twitter and False
    assert "t_twitter" in content, "t_twitter must be referenced in module_registry.py"
    # Find the twitter entry line and check it uses False
    for line in content.splitlines():
        if "twitter" in line and "t_twitter" in line:
            assert "False" in line, (
                f"twitter registry entry must have pass_from=False, got: {line}"
            )
            break
    else:
        pytest.fail("No twitter entry with t_twitter found in module_registry.py")


# ---------------------------------------------------------------------------
# 13. Dependency cleanup — requirements.txt
# ---------------------------------------------------------------------------


def test_requirements_has_twikit():
    """requirements.txt must include twikit."""
    assert REQUIREMENTS_FILE.exists(), "requirements.txt must exist"
    content = REQUIREMENTS_FILE.read_text()
    assert "twikit" in content, "twikit must be in requirements.txt"


def test_requirements_no_tweety_ns():
    """requirements.txt must NOT include tweety-ns."""
    assert REQUIREMENTS_FILE.exists(), "requirements.txt must exist"
    content = REQUIREMENTS_FILE.read_text()
    assert "tweety-ns" not in content, "tweety-ns must be removed from requirements.txt"


def test_requirements_keeps_browser_cookie3():
    """requirements.txt must keep browser-cookie3 (used by linkedin/tiktok)."""
    assert REQUIREMENTS_FILE.exists(), "requirements.txt must exist"
    content = REQUIREMENTS_FILE.read_text()
    assert "browser-cookie3" in content, (
        "browser-cookie3 must remain in requirements.txt (linkedin/tiktok use it)"
    )


# ---------------------------------------------------------------------------
# 14. Twint removal
# ---------------------------------------------------------------------------


def test_twint_directory_does_not_exist():
    """backend/modules/twint/ must not exist after cleanup."""
    assert not TWINT_DIR.exists(), (
        f"backend/modules/twint/ must be deleted, but found: {TWINT_DIR}"
    )


def test_no_live_twint_import_in_codebase():
    """No Python source file (outside tests) should import from twint module."""
    backend_dir = BACKEND_DIR
    # Search all .py files except the twint dir itself and this test
    for py_file in backend_dir.rglob("*.py"):
        if "twint" in py_file.parts:
            continue
        if py_file.name == Path(__file__).name:
            continue
        content = py_file.read_text(errors="replace")
        if "from modules.twint" in content or "import twint_tasks" in content:
            pytest.fail(
                f"Live twint import found in {py_file}. "
                "Remove all imports of the deleted twint module."
            )
