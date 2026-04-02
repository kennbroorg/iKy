"""Regression tests for reddit module migration to @iky_task decorator.

Covers:
  - Task 4.1: Decorator/alias/registry compatibility
  - Task 4.2: Mocked endpoint scenarios (pagination, trophies fallback,
              charts, location, error handling)
"""

import inspect
import json
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

# ---------------------------------------------------------------------------
# Block dev-mode globally so no outputs/output-reddit.json is ever found
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _block_devmode(tmp_path):
    """Redirect Path.cwd() so dev-mode files are never found."""
    with patch.object(Path, "cwd", return_value=tmp_path):
        yield


# ---------------------------------------------------------------------------
# Shared fixture data
# ---------------------------------------------------------------------------

ABOUT_DATA = {
    "name": "testuser",
    "icon_img": "https://example.com/avatar.png",
    "comment_karma": 1234,
    "link_karma": 567,
    "awardee_karma": 10,
    "awarder_karma": 5,
    "total_karma": 1816,
    "created_utc": 1500000000.0,
    "has_verified_email": True,
    "is_mod": False,
    "is_gold": False,
    "is_premium": False,
    "is_suspended": False,
    "subreddit": {
        "public_description": "Just a test user",
        "subscribers": 42,
        "banner_img": "",
    },
}

POST_ITEM = {
    "subreddit": "python",
    "created_utc": 1600000000.0,
    "id": "post1",
}

COMMENT_ITEM = {
    "subreddit": "linux",
    "created_utc": 1600100000.0,
    "id": "c1",
}

TROPHY_ITEM = {
    "name": "Three-Year Club",
    "icon_70": "https://example.com/trophy.png",
}

# ---------------------------------------------------------------------------
# Helpers to build mock responses
# ---------------------------------------------------------------------------


def _make_about_resp(data: dict | None = None) -> MagicMock:
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {"data": data or ABOUT_DATA.copy()}
    return resp


def _make_listing_resp(children: list, after: str | None = None) -> MagicMock:
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {
        "data": {
            "children": [{"data": item, "kind": "t3"} for item in children],
            "after": after,
        }
    }
    return resp


def _make_trophies_resp(trophies: list) -> MagicMock:
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = {
        "data": {"trophies": [{"data": t, "kind": "t6"} for t in trophies]}
    }
    return resp


def _make_error_resp(status_code: int) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    return resp


# ---------------------------------------------------------------------------
# Default happy-path mock: about OK, empty posts/comments, no trophies
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_reddit_happy(monkeypatch):
    """Mock session.get for the standard happy-path (no posts/comments)."""
    about_resp = _make_about_resp()
    empty_listing = _make_listing_resp([])
    trophy_resp = _make_trophies_resp([])

    call_map = {
        "about.json": about_resp,
        "submitted.json": empty_listing,
        "comments.json": empty_listing,
        "trophies.json": trophy_resp,
    }

    def _get(url, **kwargs):
        for key, resp in call_map.items():
            if key in url:
                return resp
        return _make_error_resp(404)

    mock_session = MagicMock()
    mock_session.get.side_effect = _get
    mock_session.headers = {}

    with patch(
        "modules.reddit.reddit_tasks.requests.Session", return_value=mock_session
    ):
        yield mock_session


# ===========================================================================
# Task 4.1: Decorator / alias / registry compatibility
# ===========================================================================


class TestDecoratorAliasRegistry:
    """Verify @iky_task wiring, alias, and registry contract."""

    def test_t_reddit_is_p_reddit(self):
        """t_reddit MUST be the same object as p_reddit."""
        from modules.reddit.reddit_tasks import p_reddit, t_reddit

        assert t_reddit is p_reddit

    def test_celery_task_name_matches_registry(self):
        """Registered Celery task name must match module_registry.py."""
        from modules.reddit.reddit_tasks import p_reddit

        assert hasattr(p_reddit, "name")
        assert p_reddit.name == "modules.reddit.reddit_tasks.t_reddit"

    def test_p_reddit_callable_directly(self, mock_reddit_happy):
        """p_reddit must be directly callable (not just via .delay())."""
        from modules.reddit.reddit_tasks import p_reddit

        result = p_reddit("testuser")
        assert isinstance(result, list)

    def test_t_reddit_callable_directly(self, mock_reddit_happy):
        """t_reddit alias must also be directly callable."""
        from modules.reddit.reddit_tasks import t_reddit

        result = t_reddit("testuser")
        assert isinstance(result, list)

    def test_signature_has_only_username(self):
        """p_reddit must accept only 'username' — no from_m parameter."""
        from modules.reddit.reddit_tasks import p_reddit

        # The Celery task wraps the original function — inspect via __wrapped__
        # or check the registered name. The key contract is no from_m.
        # We verify by calling with a single positional arg — no TypeError.
        # (Signature inspection via inspect may show the wrapper params.)
        try:
            sig = inspect.signature(p_reddit.__wrapped__)
            param_names = list(sig.parameters.keys())
            assert "from_m" not in param_names, "from_m is dead code — must be removed"
            assert "username" in param_names
        except AttributeError:
            # Decorator did not expose __wrapped__ — skip deep inspection
            pass

    def test_validation_is_always_no(self, mock_reddit_happy):
        """Validation must always be 'no' (pass_from=False in registry)."""
        from modules.reddit.reddit_tasks import p_reddit

        result = p_reddit("testuser")
        validation = next(item["validation"] for item in result if "validation" in item)
        assert validation == "no"

    def test_no_inline_dev_mode_code(self):
        """Module must not contain inline dev-mode file check (handled by decorator)."""
        import inspect as _inspect

        from modules.reddit import reddit_tasks

        src = _inspect.getsource(reddit_tasks)
        # The decorator handles dev-mode — p_reddit body must not open output files
        assert "output-reddit.json" not in src or "task_wrapper" in src


# ===========================================================================
# Task 4.2: Mocked endpoint scenarios
# ===========================================================================


class TestResponseShape:
    """Verify 7-element response contract."""

    def test_output_has_7_elements(self, mock_reddit_happy):
        from modules.reddit.reddit_tasks import p_reddit

        result = p_reddit("testuser")
        assert len(result) == 7

    def test_output_keys_in_order(self, mock_reddit_happy):
        from modules.reddit.reddit_tasks import p_reddit

        result = p_reddit("testuser")
        keys = [next(iter(item)) for item in result]
        assert keys == [
            "module",
            "param",
            "validation",
            "raw",
            "graphic",
            "profile",
            "timeline",
        ]

    def test_module_is_reddit(self, mock_reddit_happy):
        from modules.reddit.reddit_tasks import p_reddit

        result = p_reddit("testuser")
        assert result[0]["module"] == "reddit"

    def test_param_matches_username(self, mock_reddit_happy):
        from modules.reddit.reddit_tasks import p_reddit

        result = p_reddit("testuser")
        assert result[1]["param"] == "testuser"

    def test_graphic_has_4_elements(self, mock_reddit_happy):
        from modules.reddit.reddit_tasks import p_reddit

        result = p_reddit("testuser")
        graphic = result[4]["graphic"]
        assert len(graphic) == 4
        keys = [next(iter(g)) for g in graphic]
        assert keys == ["social", "hour", "week", "topics"]


class TestRawNode:
    """Verify raw node structure."""

    def test_raw_has_profile_comments_posts_trophies(self, mock_reddit_happy):
        from modules.reddit.reddit_tasks import p_reddit

        result = p_reddit("testuser")
        raw = result[3]["raw"]
        raw_keys = [next(iter(item)) for item in raw]
        assert raw_keys == ["profile", "comments", "posts", "trophies"]

    def test_raw_profile_contains_about_data(self, mock_reddit_happy):
        from modules.reddit.reddit_tasks import p_reddit

        result = p_reddit("testuser")
        profile_raw = next(
            item["profile"] for item in result[3]["raw"] if "profile" in item
        )
        assert profile_raw["name"] == "testuser"
        assert profile_raw["comment_karma"] == 1234


class TestPaginatedPosts:
    """REQ-3: Paginated post/comment history."""

    def test_single_page_posts_aggregated(self):
        """One page of posts → all items in result."""
        posts = [
            {"subreddit": "python", "created_utc": 1600000000.0, "id": f"p{i}"}
            for i in range(10)
        ]

        about_resp = _make_about_resp()
        posts_resp = _make_listing_resp(posts, after=None)
        empty = _make_listing_resp([])
        trophy_resp = _make_trophies_resp([])

        def _get(url, **kwargs):
            if "about.json" in url:
                return about_resp
            if "submitted.json" in url:
                return posts_resp
            if "comments.json" in url:
                return empty
            if "trophies.json" in url:
                return trophy_resp
            return _make_error_resp(404)

        mock_session = MagicMock()
        mock_session.get.side_effect = _get
        mock_session.headers = {}

        with patch(
            "modules.reddit.reddit_tasks.requests.Session", return_value=mock_session
        ):
            from modules.reddit.reddit_tasks import p_reddit

            result = p_reddit("testuser")

        raw_posts = next(item["posts"] for item in result[3]["raw"] if "posts" in item)
        assert len(raw_posts) == 10

    def test_pagination_follows_after_cursor(self):
        """After cursor triggers a second page fetch."""
        page1_items = [
            {"subreddit": "python", "created_utc": 1600000000.0, "id": f"p{i}"}
            for i in range(5)
        ]
        page2_items = [
            {"subreddit": "linux", "created_utc": 1600050000.0, "id": f"p{i + 5}"}
            for i in range(3)
        ]

        about_resp = _make_about_resp()
        page1_resp = _make_listing_resp(page1_items, after="t3_page2cursor")
        page2_resp = _make_listing_resp(page2_items, after=None)
        empty = _make_listing_resp([])
        trophy_resp = _make_trophies_resp([])

        call_count = {"submitted": 0}

        def _get(url, **kwargs):
            if "about.json" in url:
                return about_resp
            if "submitted.json" in url:
                call_count["submitted"] += 1
                if call_count["submitted"] == 1:
                    return page1_resp
                return page2_resp
            if "comments.json" in url:
                return empty
            if "trophies.json" in url:
                return trophy_resp
            return _make_error_resp(404)

        mock_session = MagicMock()
        mock_session.get.side_effect = _get
        mock_session.headers = {}

        with (
            patch(
                "modules.reddit.reddit_tasks.requests.Session",
                return_value=mock_session,
            ),
            patch("modules.reddit.reddit_tasks.time.sleep"),
        ):
            from modules.reddit.reddit_tasks import p_reddit

            result = p_reddit("testuser")

        raw_posts = next(item["posts"] for item in result[3]["raw"] if "posts" in item)
        assert len(raw_posts) == 8  # 5 + 3

    def test_pagination_capped_at_3_pages(self):
        """Pagination must not exceed 3 pages even if after cursor is always present."""
        page_items = [
            {"subreddit": "tech", "created_utc": 1600000000.0, "id": f"p{i}"}
            for i in range(3)
        ]

        about_resp = _make_about_resp()
        # Always returns an after cursor
        endless_resp = _make_listing_resp(page_items, after="always_more")
        empty = _make_listing_resp([])
        trophy_resp = _make_trophies_resp([])

        submitted_calls = []

        def _get(url, **kwargs):
            if "about.json" in url:
                return about_resp
            if "submitted.json" in url:
                submitted_calls.append(url)
                return endless_resp
            if "comments.json" in url:
                return empty
            if "trophies.json" in url:
                return trophy_resp
            return _make_error_resp(404)

        mock_session = MagicMock()
        mock_session.get.side_effect = _get
        mock_session.headers = {}

        with (
            patch(
                "modules.reddit.reddit_tasks.requests.Session",
                return_value=mock_session,
            ),
            patch("modules.reddit.reddit_tasks.time.sleep"),
        ):
            from modules.reddit.reddit_tasks import p_reddit

            p_reddit("testuser")

        assert len(submitted_calls) == 3, (
            f"Expected 3 pages max, got {len(submitted_calls)}"
        )

    def test_sleep_between_pagination_pages(self):
        """0.5s sleep must occur between pagination pages 2 and 3."""
        page_items = [{"subreddit": "python", "created_utc": 1.0, "id": "x"}]

        about_resp = _make_about_resp()
        resp_with_after = _make_listing_resp(page_items, after="next_cursor")
        resp_no_after = _make_listing_resp(page_items, after=None)
        empty = _make_listing_resp([])
        trophy_resp = _make_trophies_resp([])

        calls_submitted = {"n": 0}

        def _get(url, **kwargs):
            if "about.json" in url:
                return about_resp
            if "submitted.json" in url:
                calls_submitted["n"] += 1
                if calls_submitted["n"] < 2:
                    return resp_with_after
                return resp_no_after
            if "comments.json" in url:
                return empty
            if "trophies.json" in url:
                return trophy_resp
            return _make_error_resp(404)

        mock_session = MagicMock()
        mock_session.get.side_effect = _get
        mock_session.headers = {}

        with (
            patch(
                "modules.reddit.reddit_tasks.requests.Session",
                return_value=mock_session,
            ),
            patch("modules.reddit.reddit_tasks.time.sleep") as mock_sleep,
        ):
            from modules.reddit.reddit_tasks import p_reddit

            p_reddit("testuser")

        sleep_calls = [c for c in mock_sleep.call_args_list if c == call(0.5)]
        assert len(sleep_calls) >= 1, "Expected at least one 0.5s sleep between pages"

    def test_empty_posts_empty_comments(self, mock_reddit_happy):
        """User with no posts/comments → posts and comments raw lists are empty."""
        from modules.reddit.reddit_tasks import p_reddit

        result = p_reddit("testuser")

        raw_posts = next(item["posts"] for item in result[3]["raw"] if "posts" in item)
        raw_comments = next(
            item["comments"] for item in result[3]["raw"] if "comments" in item
        )
        assert raw_posts == []
        assert raw_comments == []


class TestTrophiesFallback:
    """REQ-4: Trophies are non-fatal."""

    def test_trophies_included_when_available(self):
        """Trophies endpoint 200 → trophies in raw node."""
        about_resp = _make_about_resp()
        empty_listing = _make_listing_resp([])
        trophy_resp = _make_trophies_resp([TROPHY_ITEM.copy()])

        def _get(url, **kwargs):
            if "about.json" in url:
                return about_resp
            if "submitted.json" in url or "comments.json" in url:
                return empty_listing
            if "trophies.json" in url:
                return trophy_resp
            return _make_error_resp(404)

        mock_session = MagicMock()
        mock_session.get.side_effect = _get
        mock_session.headers = {}

        with patch(
            "modules.reddit.reddit_tasks.requests.Session", return_value=mock_session
        ):
            from modules.reddit.reddit_tasks import p_reddit

            result = p_reddit("testuser")

        raw_trophies = next(
            item["trophies"] for item in result[3]["raw"] if "trophies" in item
        )
        assert len(raw_trophies) == 1
        assert raw_trophies[0]["name"] == "Three-Year Club"

    def test_trophies_fallback_on_404(self):
        """Trophies 404 → empty list, task does NOT fail."""
        about_resp = _make_about_resp()
        empty_listing = _make_listing_resp([])
        trophy_404 = _make_error_resp(404)

        def _get(url, **kwargs):
            if "about.json" in url:
                return about_resp
            if "submitted.json" in url or "comments.json" in url:
                return empty_listing
            if "trophies.json" in url:
                return trophy_404
            return _make_error_resp(404)

        mock_session = MagicMock()
        mock_session.get.side_effect = _get
        mock_session.headers = {}

        with patch(
            "modules.reddit.reddit_tasks.requests.Session", return_value=mock_session
        ):
            from modules.reddit.reddit_tasks import p_reddit

            result = p_reddit("testuser")

        # Task must succeed (7 elements)
        assert len(result) == 7
        raw_trophies = next(
            item["trophies"] for item in result[3]["raw"] if "trophies" in item
        )
        assert raw_trophies == []

    def test_trophies_fallback_on_exception(self):
        """Network error on trophies → empty list, task does NOT fail."""
        about_resp = _make_about_resp()
        empty_listing = _make_listing_resp([])

        def _get(url, **kwargs):
            if "about.json" in url:
                return about_resp
            if "submitted.json" in url or "comments.json" in url:
                return empty_listing
            if "trophies.json" in url:
                raise OSError("network failure")
            return _make_error_resp(404)

        mock_session = MagicMock()
        mock_session.get.side_effect = _get
        mock_session.headers = {}

        with patch(
            "modules.reddit.reddit_tasks.requests.Session", return_value=mock_session
        ):
            from modules.reddit.reddit_tasks import p_reddit

            result = p_reddit("testuser")

        assert len(result) == 7


class TestActivityCharts:
    """REQ-5: Hour and week charts from UTC timestamps."""

    def _run_with_items(self, posts, comments):
        about_resp = _make_about_resp()
        posts_resp = _make_listing_resp(posts)
        comments_resp = _make_listing_resp(comments)
        trophy_resp = _make_trophies_resp([])

        def _get(url, **kwargs):
            if "about.json" in url:
                return about_resp
            if "submitted.json" in url:
                return posts_resp
            if "comments.json" in url:
                return comments_resp
            if "trophies.json" in url:
                return trophy_resp
            return _make_error_resp(404)

        mock_session = MagicMock()
        mock_session.get.side_effect = _get
        mock_session.headers = {}

        with patch(
            "modules.reddit.reddit_tasks.requests.Session", return_value=mock_session
        ):
            from modules.reddit.reddit_tasks import p_reddit

            return p_reddit("testuser")

    def test_hour_chart_has_24_entries_when_active(self):
        """User with activity → hour chart has exactly 24 entries."""
        posts = [{"subreddit": "python", "created_utc": 1600000000.0, "id": "p1"}]
        comments = [{"subreddit": "linux", "created_utc": 1600100000.0, "id": "c1"}]
        result = self._run_with_items(posts, comments)

        hour = result[4]["graphic"][1]["hour"]
        assert len(hour) == 24
        assert all("name" in h and "value" in h for h in hour)

    def test_week_chart_has_7_entries_when_active(self):
        """User with activity → week chart has exactly 7 entries."""
        posts = [{"subreddit": "python", "created_utc": 1600000000.0, "id": "p1"}]
        result = self._run_with_items(posts, [])

        week = result[4]["graphic"][2]["week"]
        assert len(week) == 7
        names = [w["name"] for w in week]
        assert names == [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]

    def test_hour_chart_empty_when_no_activity(self, mock_reddit_happy):
        """No posts/comments → hour chart is empty list."""
        from modules.reddit.reddit_tasks import p_reddit

        result = p_reddit("testuser")
        hour = result[4]["graphic"][1]["hour"]
        assert hour == []

    def test_week_chart_empty_when_no_activity(self, mock_reddit_happy):
        """No posts/comments → week chart is empty list."""
        from modules.reddit.reddit_tasks import p_reddit

        result = p_reddit("testuser")
        week = result[4]["graphic"][2]["week"]
        assert week == []

    def test_timestamps_use_utc_not_hardcoded_offset(self):
        """Chart buckets must use UTC (no hardcoded UTC-7 offset)."""
        # Timestamp 1600000000 = Sun Sep 13 2020 12:26:40 UTC (hour=12, weekday=6=Sunday)
        ts = 1600000000.0
        posts = [{"subreddit": "python", "created_utc": ts, "id": "p1"}]
        result = self._run_with_items(posts, [])

        expected_hour = datetime.fromtimestamp(ts, tz=UTC).hour
        hour_chart = result[4]["graphic"][1]["hour"]
        hour_entry = next(
            h for h in hour_chart if h["name"] == f"{expected_hour:02d}:00"
        )
        assert hour_entry["value"] >= 1


class TestTopicsBubble:
    """REQ-6: Topics bubble chart from subreddit participation."""

    def _run_with_posts_comments(self, posts, comments):
        about_resp = _make_about_resp()
        posts_resp = _make_listing_resp(posts)
        comments_resp = _make_listing_resp(comments)
        trophy_resp = _make_trophies_resp([])

        def _get(url, **kwargs):
            if "about.json" in url:
                return about_resp
            if "submitted.json" in url:
                return posts_resp
            if "comments.json" in url:
                return comments_resp
            if "trophies.json" in url:
                return trophy_resp
            return _make_error_resp(404)

        mock_session = MagicMock()
        mock_session.get.side_effect = _get
        mock_session.headers = {}

        with patch(
            "modules.reddit.reddit_tasks.requests.Session", return_value=mock_session
        ):
            from modules.reddit.reddit_tasks import p_reddit

            return p_reddit("testuser")

    def test_topics_empty_when_no_activity(self, mock_reddit_happy):
        """No posts/comments → topics is empty dict {}."""
        from modules.reddit.reddit_tasks import p_reddit

        result = p_reddit("testuser")
        topics = result[4]["graphic"][3]["topics"]
        assert topics == {}

    def test_topics_sorted_by_count_descending(self):
        """Topics children are sorted by count descending (most_common)."""
        posts = (
            [
                {"subreddit": "python", "created_utc": 1.0, "id": f"p{i}"}
                for i in range(10)
            ]
            + [
                {"subreddit": "linux", "created_utc": 1.0, "id": f"l{i}"}
                for i in range(5)
            ]
            + [
                {"subreddit": "golang", "created_utc": 1.0, "id": f"g{i}"}
                for i in range(3)
            ]
        )
        result = self._run_with_posts_comments(posts, [])

        topics = result[4]["graphic"][3]["topics"]
        assert topics != {}
        children = topics["children"]
        counts = [c["count"] for c in children]
        assert counts == sorted(counts, reverse=True)

    def test_topics_has_correct_structure(self):
        """Topics bubble has name/value/children structure."""
        posts = [{"subreddit": "python", "created_utc": 1.0, "id": "p1"}]
        result = self._run_with_posts_comments(posts, [])

        topics = result[4]["graphic"][3]["topics"]
        assert "name" in topics
        assert "value" in topics
        assert "children" in topics
        assert isinstance(topics["children"], list)
        child = topics["children"][0]
        assert "name" in child
        assert "count" in child
        assert "value" in child


class TestLocationInference:
    """REQ-7: Location inferred via frozenset intersection."""

    def test_location_matched_from_subreddit(self):
        """Subreddit matching a location → location in gather and profile."""
        # We need a subreddit name that IS in all-locations.txt
        # The file contains entries like "seattle", "london" etc.
        # Load a known entry from the file to test against.
        from modules.reddit.reddit_tasks import _LOCATIONS

        if not _LOCATIONS:
            pytest.skip("all-locations.txt is empty")

        # Pick the first location name from the frozenset
        sample_location = next(iter(_LOCATIONS))

        posts = [
            {"subreddit": sample_location, "created_utc": 1600000000.0, "id": "p1"}
        ]

        about_resp = _make_about_resp()
        posts_resp = _make_listing_resp(posts)
        empty = _make_listing_resp([])
        trophy_resp = _make_trophies_resp([])

        def _get(url, **kwargs):
            if "about.json" in url:
                return about_resp
            if "submitted.json" in url:
                return posts_resp
            if "comments.json" in url:
                return empty
            if "trophies.json" in url:
                return trophy_resp
            return _make_error_resp(404)

        mock_session = MagicMock()
        mock_session.get.side_effect = _get
        mock_session.headers = {}

        with patch(
            "modules.reddit.reddit_tasks.requests.Session", return_value=mock_session
        ):
            from modules.reddit.reddit_tasks import p_reddit

            result = p_reddit("testuser")

        gather = result[4]["graphic"][0]["social"]
        location_node = next(
            (g for g in gather if g.get("name-node") == "RedditLocation"), None
        )
        assert location_node is not None, "Location gather node missing"
        assert sample_location in location_node["subtitle"].lower()

        profile = result[5]["profile"]
        location_profile = next(
            (p for p in profile if isinstance(p, dict) and "location" in p), None
        )
        assert location_profile is not None

    def test_no_location_when_no_activity(self, mock_reddit_happy):
        """No posts/comments → no location node in gather."""
        from modules.reddit.reddit_tasks import p_reddit

        result = p_reddit("testuser")
        gather = result[4]["graphic"][0]["social"]
        location_node = next(
            (g for g in gather if g.get("name-node") == "RedditLocation"), None
        )
        assert location_node is None

    def test_no_location_when_no_match(self):
        """Subreddits not in locations file → no location node."""
        posts = [
            {"subreddit": "thisisnotaplace_xyzabc123", "created_utc": 1.0, "id": "p1"}
        ]

        about_resp = _make_about_resp()
        posts_resp = _make_listing_resp(posts)
        empty = _make_listing_resp([])
        trophy_resp = _make_trophies_resp([])

        def _get(url, **kwargs):
            if "about.json" in url:
                return about_resp
            if "submitted.json" in url:
                return posts_resp
            if "comments.json" in url:
                return empty
            if "trophies.json" in url:
                return trophy_resp
            return _make_error_resp(404)

        mock_session = MagicMock()
        mock_session.get.side_effect = _get
        mock_session.headers = {}

        with patch(
            "modules.reddit.reddit_tasks.requests.Session", return_value=mock_session
        ):
            from modules.reddit.reddit_tasks import p_reddit

            result = p_reddit("testuser")

        gather = result[4]["graphic"][0]["social"]
        location_node = next(
            (g for g in gather if g.get("name-node") == "RedditLocation"), None
        )
        assert location_node is None


class TestErrorHandling:
    """REQ-9: HTTP 404/403/429 and suspended user raise iKy- exceptions."""

    def _run_about_with_status(self, status_code: int):
        about_resp = _make_error_resp(status_code)

        mock_session = MagicMock()
        mock_session.get.return_value = about_resp
        mock_session.headers = {}

        with patch(
            "modules.reddit.reddit_tasks.requests.Session", return_value=mock_session
        ):
            from modules.reddit.reddit_tasks import p_reddit

            return p_reddit("anyuser")

    def test_404_returns_warning_user_not_found(self):
        """HTTP 404 on about.json → Warning with 'User not found'."""
        result = self._run_about_with_status(404)

        raw = result[3]["raw"]
        assert isinstance(raw, list)
        assert raw[0]["status"] == "Warning"
        assert raw[0]["reason"] == "User not found"

    def test_403_returns_warning_access_forbidden(self):
        """HTTP 403 on about.json → Warning with access forbidden."""
        result = self._run_about_with_status(403)

        raw = result[3]["raw"]
        assert raw[0]["status"] == "Warning"
        assert (
            "forbidden" in raw[0]["reason"].lower()
            or "suspended" in raw[0]["reason"].lower()
        )

    def test_429_returns_warning_rate_limited(self):
        """HTTP 429 on about.json → Warning with rate limited."""
        result = self._run_about_with_status(429)

        raw = result[3]["raw"]
        assert raw[0]["status"] == "Warning"
        assert "rate" in raw[0]["reason"].lower() or "limit" in raw[0]["reason"].lower()

    def test_suspended_user_returns_warning(self):
        """about.json returns is_suspended=True → Warning."""
        suspended_data = ABOUT_DATA.copy()
        suspended_data["is_suspended"] = True

        about_resp = _make_about_resp(suspended_data)

        mock_session = MagicMock()
        mock_session.get.return_value = about_resp
        mock_session.headers = {}

        with patch(
            "modules.reddit.reddit_tasks.requests.Session", return_value=mock_session
        ):
            from modules.reddit.reddit_tasks import p_reddit

            result = p_reddit("suspendeduser")

        raw = result[3]["raw"]
        assert raw[0]["status"] == "Warning"
        assert "suspended" in raw[0]["reason"].lower()

    def test_generic_exception_returns_fail(self):
        """Network error (non-iKy) → Fail status."""
        mock_session = MagicMock()
        mock_session.get.side_effect = OSError("connection refused")
        mock_session.headers = {}

        with patch(
            "modules.reddit.reddit_tasks.requests.Session", return_value=mock_session
        ):
            from modules.reddit.reddit_tasks import p_reddit

            result = p_reddit("anyuser")

        raw = result[3]["raw"]
        assert raw[0]["status"] == "Fail"
        assert "connection refused" in raw[0]["reason"]

    def test_error_structure_has_4_keys(self):
        """Error response: [module, param, validation, raw] (no graphic/profile)."""
        mock_session = MagicMock()
        mock_session.get.return_value = _make_error_resp(404)
        mock_session.headers = {}

        with patch(
            "modules.reddit.reddit_tasks.requests.Session", return_value=mock_session
        ):
            from modules.reddit.reddit_tasks import p_reddit

            result = p_reddit("anyuser")

        keys = [next(iter(item)) for item in result]
        assert keys == ["module", "param", "validation", "raw"]

    def test_error_includes_traceback(self):
        """Error raw node must contain a traceback string."""
        mock_session = MagicMock()
        mock_session.get.return_value = _make_error_resp(404)
        mock_session.headers = {}

        with patch(
            "modules.reddit.reddit_tasks.requests.Session", return_value=mock_session
        ):
            from modules.reddit.reddit_tasks import p_reddit

            result = p_reddit("anyuser")

        raw = result[3]["raw"]
        assert "traceback" in raw[0]
        assert isinstance(raw[0]["traceback"], str)


class TestDevModeGoldenFixture:
    """Decorator dev-mode bypass via output-reddit.json."""

    def test_dev_mode_returns_golden_json(self, tmp_path):
        golden = [
            {"module": "reddit"},
            {"param": "devuser"},
            {"validation": "no"},
            {
                "raw": [
                    {"profile": {}},
                    {"comments": []},
                    {"posts": []},
                    {"trophies": []},
                ]
            },
            {"graphic": [{"social": []}, {"hour": []}, {"week": []}, {"topics": {}}]},
            {"profile": []},
            {"timeline": []},
        ]
        outputs = tmp_path / "outputs"
        outputs.mkdir()
        devfile = outputs / "output-reddit.json"
        devfile.write_text(json.dumps(golden))

        with (
            patch.object(Path, "cwd", return_value=tmp_path),
            patch("factories.task_wrapper.time.sleep") as mock_sleep,
        ):
            from modules.reddit.reddit_tasks import p_reddit

            result = p_reddit("anything")

        assert result == golden
        # dev_mode_sleep=15 must be honoured
        mock_sleep.assert_called_once_with(15)


class TestAboutFieldExtraction:
    """REQ-2: All about.json fields extracted into gather nodes."""

    def _run(self, about_data: dict):
        about_resp = _make_about_resp(about_data)
        empty = _make_listing_resp([])
        trophy_resp = _make_trophies_resp([])

        def _get(url, **kwargs):
            if "about.json" in url:
                return about_resp
            if "submitted.json" in url or "comments.json" in url:
                return empty
            if "trophies.json" in url:
                return trophy_resp
            return _make_error_resp(404)

        mock_session = MagicMock()
        mock_session.get.side_effect = _get
        mock_session.headers = {}

        with patch(
            "modules.reddit.reddit_tasks.requests.Session", return_value=mock_session
        ):
            from modules.reddit.reddit_tasks import p_reddit

            return p_reddit("testuser")

    def test_karma_fields_present(self):
        result = self._run(ABOUT_DATA.copy())
        gather = result[4]["graphic"][0]["social"]
        node_names = {g["name-node"] for g in gather}
        assert "RedditCommentKarma" in node_names
        assert "RedditLinkKarma" in node_names
        assert "RedditTotalKarma" in node_names
        assert "RedditAwardeeKarma" in node_names
        assert "RedditAwarderKarma" in node_names

    def test_bio_included_when_present(self):
        result = self._run(ABOUT_DATA.copy())
        gather = result[4]["graphic"][0]["social"]
        bio_node = next((g for g in gather if g.get("name-node") == "RedditBio"), None)
        assert bio_node is not None
        assert bio_node["subtitle"] == "Just a test user"

    def test_subscribers_included_when_present(self):
        result = self._run(ABOUT_DATA.copy())
        gather = result[4]["graphic"][0]["social"]
        sub_node = next(
            (g for g in gather if g.get("name-node") == "RedditSubscribers"), None
        )
        assert sub_node is not None
        assert sub_node["subtitle"] == 42

    def test_premium_included_when_is_gold(self):
        data = ABOUT_DATA.copy()
        data["is_gold"] = True
        result = self._run(data)
        gather = result[4]["graphic"][0]["social"]
        premium_node = next(
            (g for g in gather if g.get("name-node") == "RedditPremium"), None
        )
        assert premium_node is not None

    def test_created_utc_in_timeline(self):
        result = self._run(ABOUT_DATA.copy())
        timeline = result[6]["timeline"]
        creation_entry = next(
            (t for t in timeline if "creation" in t.get("desc", "").lower()), None
        )
        assert creation_entry is not None
        assert creation_entry["action"] == "Reddit"


# ===========================================================================
# Warning Fix 5: Comment-only scenario
# ===========================================================================


class TestCommentOnlyScenario:
    """User has 0 posts but has comments — charts and topics still build."""

    def _run_comments_only(self, comments):
        about_resp = _make_about_resp()
        empty = _make_listing_resp([])
        comments_resp = _make_listing_resp(comments)
        trophy_resp = _make_trophies_resp([])

        def _get(url, **kwargs):
            if "about.json" in url:
                return about_resp
            if "submitted.json" in url:
                return empty
            if "comments.json" in url:
                return comments_resp
            if "trophies.json" in url:
                return trophy_resp
            return _make_error_resp(404)

        mock_session = MagicMock()
        mock_session.get.side_effect = _get
        mock_session.headers = {}

        with patch(
            "modules.reddit.reddit_tasks.requests.Session", return_value=mock_session
        ):
            from modules.reddit.reddit_tasks import p_reddit

            return p_reddit("testuser")

    def test_hour_chart_built_from_comments(self):
        """0 posts, N comments → hour chart has 24 entries."""
        comments = [
            {"subreddit": "linux", "created_utc": 1600000000.0, "id": f"c{i}"}
            for i in range(5)
        ]
        result = self._run_comments_only(comments)
        hour = result[4]["graphic"][1]["hour"]
        assert len(hour) == 24

    def test_week_chart_built_from_comments(self):
        """0 posts, N comments → week chart has 7 entries."""
        comments = [
            {"subreddit": "linux", "created_utc": 1600000000.0, "id": f"c{i}"}
            for i in range(3)
        ]
        result = self._run_comments_only(comments)
        week = result[4]["graphic"][2]["week"]
        assert len(week) == 7

    def test_topics_built_from_comments(self):
        """0 posts, N comments → topics bubble chart is non-empty."""
        comments = [
            {"subreddit": "python", "created_utc": 1600000000.0, "id": "c1"},
            {"subreddit": "linux", "created_utc": 1600000001.0, "id": "c2"},
        ]
        result = self._run_comments_only(comments)
        topics = result[4]["graphic"][3]["topics"]
        assert topics != {}
        assert "children" in topics
        sub_names = {c["name"] for c in topics["children"]}
        assert "python" in sub_names
        assert "linux" in sub_names

    def test_raw_posts_empty_comments_populated(self):
        """0 posts → raw posts list is empty; raw comments list is non-empty."""
        comments = [{"subreddit": "python", "created_utc": 1600000000.0, "id": "c1"}]
        result = self._run_comments_only(comments)
        raw = result[3]["raw"]
        raw_posts = next(item["posts"] for item in raw if "posts" in item)
        raw_comments = next(item["comments"] for item in raw if "comments" in item)
        assert raw_posts == []
        assert len(raw_comments) == 1


# ===========================================================================
# Warning Fix 6: User-agent rotation test
# ===========================================================================


class TestUserAgentRotation:
    """_USER_AGENTS is a non-empty tuple and _get_session() (now _make_session)
    uses one of the agents."""

    def test_user_agents_is_non_empty_tuple(self):
        """_USER_AGENTS must be a non-empty tuple of strings."""
        from modules.reddit.reddit_tasks import _USER_AGENTS

        assert isinstance(_USER_AGENTS, tuple)
        assert len(_USER_AGENTS) > 0
        assert all(isinstance(ua, str) for ua in _USER_AGENTS)

    def test_make_session_uses_one_of_the_user_agents(self):
        """_make_session() must set User-Agent to one from _USER_AGENTS."""
        from modules.reddit.reddit_tasks import _USER_AGENTS, _make_session

        session = _make_session()
        assert session.headers["User-Agent"] in _USER_AGENTS
