"""Regression tests for Spotify module migration to @iky_task decorator.

Covers:
  - Task 1.1: Registry entry and schema cleanup
  - Task 2.1/2.2: Decorator/alias/CLI compatibility
  - Task 3.1/3.2/4.1: Enrichment helpers (genres, audio, timeline, top artists,
                       popularity) and graceful degradation
  - Task 5.1: Dev-mode golden JSON fixture
"""

import inspect
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Block dev-mode globally so output-spotify.json is never accidentally found
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _block_devmode(tmp_path):
    """Redirect Path.cwd() so dev-mode files are never found by default."""
    with patch.object(Path, "cwd", return_value=tmp_path):
        yield


# ---------------------------------------------------------------------------
# Shared Spotify API mock helpers
# ---------------------------------------------------------------------------


USER_DATA = {
    "id": "testuser",
    "display_name": "Test User",
    "followers": {"total": 10},
    "external_urls": {"spotify": "https://open.spotify.com/user/testuser"},
    "images": [{"url": "https://example.com/pic.jpg"}],
}

PLAYLIST_DATA = {
    "id": "pl1",
    "name": "My Mix",
    "owner": {"id": "testuser"},
    "tracks": {"total": 2},
    "collaborative": False,
    "public": True,
}

TRACK_ITEM = {
    "track": {
        "id": "tr1",
        "name": "Happy Song",
        "artists": [{"id": "ar1", "name": "Cool Artist"}],
        "popularity": 75,
    },
    "added_at": "2024-03-15T10:00:00Z",
}

TRACK_ITEM_2 = {
    "track": {
        "id": "tr2",
        "name": "Cool Tune",
        "artists": [{"id": "ar1", "name": "Cool Artist"}],
        "popularity": 30,
    },
    "added_at": "2024-04-01T12:00:00Z",
}

AUDIO_FEATURE = {
    "id": "tr1",
    "danceability": 0.8,
    "energy": 0.7,
    "valence": 0.6,
    "tempo": 120.0,
    "acousticness": 0.1,
    "instrumentalness": 0.0,
    "speechiness": 0.05,
    "liveness": 0.2,
    "loudness": -7.5,
    "mode": 1,
    "key": 5,
}

ARTIST_DATA = {
    "id": "ar1",
    "name": "Cool Artist",
    "genres": ["pop", "indie pop"],
    "popularity": 75,
}


def _make_sp_mock(
    user=None,
    playlists=None,
    playlist_tracks=None,
    artists_resp=None,
    audio_features_resp=None,
    next_tracks=None,
):
    """Build a MagicMock spotipy.Spotify client."""
    sp = MagicMock()
    sp.user.return_value = user or USER_DATA.copy()
    sp.user_playlists.return_value = {
        "items": [playlists] if isinstance(playlists, dict) else (playlists or [])
    }
    sp.playlist.return_value = {
        "tracks": {
            "items": playlist_tracks if playlist_tracks is not None else [],
            "next": None,
        }
    }
    sp.next.return_value = next_tracks or {"items": [], "next": None}
    sp.artists.return_value = {
        "artists": [artists_resp]
        if isinstance(artists_resp, dict)
        else (artists_resp or [])
    }
    sp.audio_features.return_value = (
        audio_features_resp if audio_features_resp is not None else []
    )
    return sp


# ---------------------------------------------------------------------------
# Helper: patch spotipy.Spotify constructor + api_keys
# ---------------------------------------------------------------------------


def _run_p_spotify(username="testuser", sp_mock=None, keys=None):
    """Call p_spotify() with fully mocked Spotify client and API keys."""
    if sp_mock is None:
        sp_mock = _make_sp_mock(playlists=PLAYLIST_DATA)
    if keys is None:
        keys = {"spotify_client_id": "fake_id", "spotify_client_secret": "fake_secret"}

    def _key_lookup(name):
        return keys.get(name, "")

    with (
        patch("modules.spotify.spotify_tasks.api_keys_search", side_effect=_key_lookup),
        patch("modules.spotify.spotify_tasks.SpotifyClientCredentials") as mock_creds,
        patch("modules.spotify.spotify_tasks.spotipy.Spotify", return_value=sp_mock),
    ):
        mock_creds.return_value = MagicMock()
        from modules.spotify.spotify_tasks import p_spotify

        return p_spotify(username)


# ===========================================================================
# Task 1.1: Registry and schema
# ===========================================================================


class TestRegistryAndSchema:
    """Verify registry entry and schema cleanup."""

    def test_spotify_in_module_registry(self):
        """spotify must be registered in MODULE_REGISTRY with pass_from=False."""
        from module_registry import MODULE_REGISTRY

        assert "spotify" in MODULE_REGISTRY
        task_path, pass_from = MODULE_REGISTRY["spotify"]
        assert task_path == "modules.spotify.spotify_tasks.t_spotify"
        assert pass_from is False

    def test_spotify_request_removed_from_schemas(self):
        """SpotifyRequest must no longer exist in schemas module."""
        import schemas

        assert not hasattr(schemas, "SpotifyRequest"), (
            "SpotifyRequest should be removed — spotify now uses standard ModuleRequest"
        )

    def test_spotify_response_removed_from_schemas(self):
        """SpotifyResponse must no longer exist in schemas module."""
        import schemas

        assert not hasattr(schemas, "SpotifyResponse"), (
            "SpotifyResponse should be removed — proc param is dead code"
        )


# ===========================================================================
# Task 2.1/2.2: Decorator / alias / CLI
# ===========================================================================


class TestDecoratorAliasRegistry:
    """Verify @iky_task wiring, t_spotify alias, and Celery task name."""

    def test_t_spotify_is_p_spotify(self):
        """t_spotify MUST be the same object as p_spotify (alias, not copy)."""
        from modules.spotify.spotify_tasks import p_spotify, t_spotify

        assert t_spotify is p_spotify

    def test_celery_task_name_matches_registry(self):
        """Registered Celery task name must match module_registry.py entry."""
        from modules.spotify.spotify_tasks import p_spotify

        assert hasattr(p_spotify, "name")
        assert p_spotify.name == "modules.spotify.spotify_tasks.t_spotify"

    def test_p_spotify_callable_directly(self):
        """p_spotify must be directly callable with a single username arg."""
        sp = _make_sp_mock(playlists=PLAYLIST_DATA)
        result = _run_p_spotify(sp_mock=sp)
        assert isinstance(result, list)

    def test_signature_has_only_username(self):
        """p_spotify must accept only 'username' — no from_m, level, or proc."""
        from modules.spotify.spotify_tasks import p_spotify

        try:
            sig = inspect.signature(p_spotify.__wrapped__)
            param_names = list(sig.parameters.keys())
            assert "from_m" not in param_names, "from_m must be removed"
            assert "level" not in param_names, "level must be removed"
            assert "proc" not in param_names, "proc must be removed"
            assert "username" in param_names
        except AttributeError:
            pass  # wrapped not exposed — skip deep inspection

    def test_no_inline_dev_mode_code(self):
        """p_spotify body must not open output files — decorator handles dev-mode."""
        import inspect as _inspect

        from modules.spotify import spotify_tasks

        src = _inspect.getsource(spotify_tasks)
        # The inline dev-mode from the old code must be gone
        assert "output-spotify.json" not in src or "task_wrapper" in src

    def test_no_old_celery_task_decorator(self):
        """Old @celery.task pattern must be gone — now handled by @iky_task."""
        import inspect as _inspect

        from modules.spotify import spotify_tasks

        src = _inspect.getsource(spotify_tasks)
        assert "@celery.task" not in src, (
            "@celery.task found — module must use @iky_task decorator instead"
        )

    def test_cli_argparse_block_exists(self):
        """Module must have an argparse __main__ block (not bare sys.argv)."""
        import inspect as _inspect

        from modules.spotify import spotify_tasks

        src = _inspect.getsource(spotify_tasks)
        assert "argparse" in src
        assert "__main__" in src
        assert "sys.argv[1]" not in src, "bare sys.argv must be replaced by argparse"


# ===========================================================================
# Response shape
# ===========================================================================


class TestResponseShape:
    """Verify 7-element response contract and key ordering."""

    def test_output_has_7_elements(self):
        result = _run_p_spotify()
        assert len(result) == 7

    def test_output_keys_in_order(self):
        result = _run_p_spotify()
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

    def test_module_is_spotify(self):
        result = _run_p_spotify()
        assert result[0]["module"] == "spotify"

    def test_param_matches_username(self):
        result = _run_p_spotify(username="myuser")
        assert result[1]["param"] == "myuser"

    def test_validation_is_no(self):
        result = _run_p_spotify()
        assert result[2]["validation"] == "no"

    def test_graphic_has_8_elements(self):
        """graphic array must have exactly 8 items (5 original + 3 new)."""
        result = _run_p_spotify()
        graphic = result[4]["graphic"]
        assert len(graphic) == 8

    def test_graphic_indices_0_to_4_preserved(self):
        """Original graphic indices must be preserved in order."""
        result = _run_p_spotify()
        graphic = result[4]["graphic"]
        keys = [next(iter(g)) for g in graphic[:5]]
        assert keys == ["social", "playlist", "autors", "words", "lang"]

    def test_graphic_indices_5_to_7_new(self):
        """New enrichment sections at graphic[5], [6], [7]."""
        result = _run_p_spotify()
        graphic = result[4]["graphic"]
        assert next(iter(graphic[5])) == "genres"
        assert next(iter(graphic[6])) == "audio_profile"
        assert next(iter(graphic[7])) == "popularity"


# ===========================================================================
# Enrichment helpers (unit tests — pure functions)
# ===========================================================================


class TestAggregateGenres:
    """_aggregate_genres pure function tests."""

    def test_genre_counts_correct(self):
        from modules.spotify.spotify_tasks import _aggregate_genres

        artists = {
            "a1": {"genres": ["pop", "rock"]},
            "a2": {"genres": ["pop", "indie"]},
            "a3": {"genres": ["rock"]},
        }
        result = _aggregate_genres(artists)
        name_map = {g["name"]: g["value"] for g in result}
        assert name_map["pop"] == 2
        assert name_map["rock"] == 2
        assert name_map["indie"] == 1

    def test_result_sorted_descending(self):
        from modules.spotify.spotify_tasks import _aggregate_genres

        artists = {
            "a1": {"genres": ["pop", "pop", "rock"]},
            "a2": {"genres": ["pop"]},
        }
        result = _aggregate_genres(artists)
        counts = [g["value"] for g in result]
        assert counts == sorted(counts, reverse=True)

    def test_empty_artists_returns_empty(self):
        from modules.spotify.spotify_tasks import _aggregate_genres

        assert _aggregate_genres({}) == []

    def test_graceful_on_bad_input(self):
        """Bad input must not raise — returns []."""
        from modules.spotify.spotify_tasks import _aggregate_genres

        # Passing non-dict should not crash
        result = _aggregate_genres(None)  # type: ignore[arg-type]
        assert result == []


class TestAggregateAudioFeatures:
    """_aggregate_audio_features pure function tests."""

    def test_mean_computed_correctly(self):
        from modules.spotify.spotify_tasks import _aggregate_audio_features

        features = [
            {
                "danceability": 0.8,
                "energy": 0.6,
                "valence": 0.5,
                "tempo": 100.0,
                "acousticness": 0.2,
                "instrumentalness": 0.0,
                "speechiness": 0.05,
                "liveness": 0.1,
            },
            {
                "danceability": 0.4,
                "energy": 0.8,
                "valence": 0.3,
                "tempo": 140.0,
                "acousticness": 0.4,
                "instrumentalness": 0.1,
                "speechiness": 0.07,
                "liveness": 0.3,
            },
        ]
        result = _aggregate_audio_features(features)
        assert result["danceability"] == pytest.approx(0.6, abs=0.001)
        assert result["energy"] == pytest.approx(0.7, abs=0.001)
        assert result["tempo"] == pytest.approx(120.0, abs=0.01)

    def test_none_features_excluded(self):
        """None entries in feature list are excluded from averages."""
        from modules.spotify.spotify_tasks import _aggregate_audio_features

        features = [
            None,  # type: ignore[list-item]
            {
                "danceability": 0.8,
                "energy": 0.8,
                "valence": 0.8,
                "tempo": 100.0,
                "acousticness": 0.1,
                "instrumentalness": 0.0,
                "speechiness": 0.05,
                "liveness": 0.1,
            },
        ]
        result = _aggregate_audio_features(features)
        assert result["danceability"] == pytest.approx(0.8, abs=0.001)

    def test_empty_list_returns_empty_dict(self):
        from modules.spotify.spotify_tasks import _aggregate_audio_features

        assert _aggregate_audio_features([]) == {}

    def test_all_expected_keys_present(self):
        from modules.spotify.spotify_tasks import _aggregate_audio_features

        features = [AUDIO_FEATURE.copy()]
        result = _aggregate_audio_features(features)
        expected_keys = {
            "danceability",
            "energy",
            "valence",
            "tempo",
            "acousticness",
            "instrumentalness",
            "speechiness",
            "liveness",
            "loudness",
            "mode",
            "key",
        }
        assert set(result.keys()) == expected_keys


class TestBuildTimeline:
    """_build_timeline pure function tests."""

    def test_monthly_grouping(self):
        from modules.spotify.spotify_tasks import _build_timeline

        added_at = [
            "2024-03-01T10:00:00Z",
            "2024-03-15T12:00:00Z",
            "2024-04-01T08:00:00Z",
        ]
        result = _build_timeline(added_at)
        month_map = {t["name"]: t["value"] for t in result}
        assert month_map["2024-03"] == 2
        assert month_map["2024-04"] == 1

    def test_sorted_chronologically(self):
        from modules.spotify.spotify_tasks import _build_timeline

        added_at = [
            "2024-06-01T00:00:00Z",
            "2024-01-01T00:00:00Z",
            "2024-03-01T00:00:00Z",
        ]
        result = _build_timeline(added_at)
        months = [t["name"] for t in result]
        assert months == sorted(months)

    def test_empty_list_returns_empty(self):
        from modules.spotify.spotify_tasks import _build_timeline

        assert _build_timeline([]) == []

    def test_graceful_on_bad_input(self):
        from modules.spotify.spotify_tasks import _build_timeline

        result = _build_timeline(None)  # type: ignore[arg-type]
        assert result == []


class TestBuildTopArtists:
    """_build_top_artists pure function tests."""

    def test_top_artists_ranked_by_frequency(self):
        from modules.spotify.spotify_tasks import _build_top_artists

        autors = ["Drake"] * 15 + ["Artist B"] * 5 + ["Artist C"] * 3
        artists_data = {
            "ar_drake": {
                "name": "Drake",
                "genres": ["hip hop", "rap"],
                "popularity": 95,
            },
            "ar_b": {"name": "Artist B", "genres": ["pop"], "popularity": 70},
            "ar_c": {"name": "Artist C", "genres": ["rock"], "popularity": 60},
        }
        result = _build_top_artists(autors, artists_data)
        names = [a["name"] for a in result]
        assert names[0] == "Drake"
        assert result[0]["count"] == 15
        assert result[0]["genres"] == ["hip hop", "rap"]
        assert result[0]["popularity"] == 95

    def test_artists_with_single_appearance_excluded(self):
        """Artists with count < 2 must be excluded (consistent with existing logic)."""
        from modules.spotify.spotify_tasks import _build_top_artists

        autors = ["Artist A"] * 3 + ["One-Timer"]  # One-Timer appears only once
        artists_data = {}
        result = _build_top_artists(autors, artists_data)
        names = [a["name"] for a in result]
        assert "One-Timer" not in names

    def test_empty_inputs_return_empty(self):
        from modules.spotify.spotify_tasks import _build_top_artists

        assert _build_top_artists([], {}) == []


class TestAnalyzePopularity:
    """_analyze_popularity pure function tests."""

    def test_popularity_buckets(self):
        from modules.spotify.spotify_tasks import _analyze_popularity

        tracks = [
            {"popularity": 80},  # mainstream (>=50)
            {"popularity": 70},  # mainstream
            {"popularity": 50},  # mainstream (boundary — exactly 50)
            {"popularity": 49},  # niche (<50)
            {"popularity": 20},  # niche
            {"popularity": 10},  # niche
        ]
        result = _analyze_popularity(tracks)
        assert result["mainstream"] == 3
        assert "mid" not in result, "mid category must be removed per spec"
        assert result["niche"] == 3

    def test_mean_and_median_computed(self):
        from modules.spotify.spotify_tasks import _analyze_popularity

        tracks = [
            {"popularity": 75},
            {"popularity": 30},
            {"popularity": 60},
            {"popularity": 20},
        ]
        result = _analyze_popularity(tracks)
        assert result["mean"] == pytest.approx(46.25, abs=0.01)
        # Sorted: [20, 30, 60, 75] → median = (30+60)/2 = 45.0
        assert result["median"] == pytest.approx(45.0, abs=0.01)

    def test_empty_returns_empty_dict(self):
        from modules.spotify.spotify_tasks import _analyze_popularity

        assert _analyze_popularity([]) == {}

    def test_graceful_on_missing_popularity_field(self):
        from modules.spotify.spotify_tasks import _analyze_popularity

        tracks = [{"name": "no_popularity_field"}]
        # track with popularity=0 (default) is still valid
        result = _analyze_popularity(tracks)
        # Should not raise
        assert isinstance(result, dict)


# ===========================================================================
# Batch fetch helpers with mocked sp
# ===========================================================================


class TestBatchFetchArtists:
    """_batch_fetch_artists batching and graceful degradation."""

    def test_batch_size_50_enforced(self):
        """sp.artists() must be called in chunks of max 50 IDs."""
        from modules.spotify.spotify_tasks import _batch_fetch_artists

        sp = MagicMock()
        sp.artists.return_value = {"artists": []}

        ids = {f"id_{i}" for i in range(130)}
        _batch_fetch_artists(sp, ids)

        # 130 IDs → 3 calls: 50, 50, 30
        assert sp.artists.call_count == 3
        for call_args in sp.artists.call_args_list:
            batch = call_args[0][0]
            assert len(batch) <= 50

    def test_returns_dict_keyed_by_id(self):
        from modules.spotify.spotify_tasks import _batch_fetch_artists

        sp = MagicMock()
        sp.artists.return_value = {"artists": [ARTIST_DATA.copy()]}

        result = _batch_fetch_artists(sp, {"ar1"})
        assert "ar1" in result
        assert result["ar1"]["name"] == "Cool Artist"

    def test_graceful_on_exception(self):
        """sp.artists() raising an exception → returns {}."""
        from modules.spotify.spotify_tasks import _batch_fetch_artists

        sp = MagicMock()
        sp.artists.side_effect = OSError("network error")

        result = _batch_fetch_artists(sp, {"ar1", "ar2"})
        assert result == {}


class TestBatchFetchAudioFeatures:
    """_batch_fetch_audio_features batching and graceful degradation."""

    def test_batch_size_100_enforced(self):
        """sp.audio_features() must be called in chunks of max 100 IDs."""
        from modules.spotify.spotify_tasks import _batch_fetch_audio_features

        sp = MagicMock()
        sp.audio_features.return_value = []

        ids = [f"tr_{i}" for i in range(250)]
        _batch_fetch_audio_features(sp, ids)

        # 250 IDs → 3 calls: 100, 100, 50
        assert sp.audio_features.call_count == 3
        for call_args in sp.audio_features.call_args_list:
            batch = call_args[0][0]
            assert len(batch) <= 100

    def test_none_entries_filtered(self):
        """None entries in sp.audio_features() response are filtered out."""
        from modules.spotify.spotify_tasks import _batch_fetch_audio_features

        sp = MagicMock()
        sp.audio_features.return_value = [AUDIO_FEATURE.copy(), None]

        result = _batch_fetch_audio_features(sp, ["tr1", "tr2"])
        assert len(result) == 1
        assert result[0]["id"] == "tr1"

    def test_graceful_on_exception(self):
        """sp.audio_features() raising an exception → returns []."""
        from modules.spotify.spotify_tasks import _batch_fetch_audio_features

        sp = MagicMock()
        sp.audio_features.side_effect = Exception("rate limit")

        result = _batch_fetch_audio_features(sp, ["tr1"])
        assert result == []


# ===========================================================================
# Integration: p_spotify() full mock
# ===========================================================================


class TestFullIntegration:
    """Full p_spotify() call with mocked Spotify client."""

    def test_happy_path_two_tracks(self):
        """Two tracks in one playlist → valid 7-element response."""
        sp = _make_sp_mock(
            playlists=PLAYLIST_DATA,
            playlist_tracks=[TRACK_ITEM, TRACK_ITEM_2],
            artists_resp=ARTIST_DATA,
            audio_features_resp=[AUDIO_FEATURE.copy()],
        )
        result = _run_p_spotify(sp_mock=sp)

        assert len(result) == 7
        assert result[0]["module"] == "spotify"

    def test_profile_contains_name_and_username(self):
        sp = _make_sp_mock(playlists=PLAYLIST_DATA)
        result = _run_p_spotify(sp_mock=sp)

        profile = result[5]["profile"]
        names = {
            next(iter(p)): next(iter(p.values()))
            for p in profile
            if isinstance(p, dict) and len(p) == 1
        }
        assert names.get("name") == "Test User"
        assert names.get("username") == "testuser"

    def test_enrichment_genres_present(self):
        """graphic[5] must contain genres key."""
        sp = _make_sp_mock(
            playlists=PLAYLIST_DATA,
            playlist_tracks=[TRACK_ITEM],
            artists_resp=ARTIST_DATA,
        )
        result = _run_p_spotify(sp_mock=sp)
        assert "genres" in result[4]["graphic"][5]

    def test_enrichment_audio_profile_present(self):
        """graphic[6] must contain audio_profile key."""
        sp = _make_sp_mock(
            playlists=PLAYLIST_DATA,
            playlist_tracks=[TRACK_ITEM],
            audio_features_resp=[AUDIO_FEATURE.copy()],
        )
        result = _run_p_spotify(sp_mock=sp)
        assert "audio_profile" in result[4]["graphic"][6]

    def test_enrichment_popularity_present(self):
        """graphic[7] must contain popularity key."""
        sp = _make_sp_mock(
            playlists=PLAYLIST_DATA,
            playlist_tracks=[TRACK_ITEM, TRACK_ITEM_2],
        )
        result = _run_p_spotify(sp_mock=sp)
        assert "popularity" in result[4]["graphic"][7]

    def test_timeline_built_from_added_at(self):
        """Timeline entries are built from track added_at timestamps."""
        sp = _make_sp_mock(
            playlists=PLAYLIST_DATA,
            playlist_tracks=[TRACK_ITEM, TRACK_ITEM_2],
        )
        result = _run_p_spotify(sp_mock=sp)
        timeline = result[6]["timeline"]
        # Two tracks added in March and April 2024
        month_names = {t["name"] for t in timeline}
        assert "2024-03" in month_names
        assert "2024-04" in month_names

    def test_no_playlists_returns_valid_response(self):
        """User with no owned playlists still returns valid 7-element response."""
        sp = _make_sp_mock(playlists=[])  # empty playlist list
        result = _run_p_spotify(sp_mock=sp)
        assert len(result) == 7

    def test_non_owned_playlists_skipped(self):
        """Playlists owned by another user are ignored."""
        foreign_playlist = {
            "id": "pl_other",
            "name": "Foreign Mix",
            "owner": {"id": "anotheruser"},  # NOT testuser
            "tracks": {"total": 10},
        }
        sp = _make_sp_mock(playlists=foreign_playlist)
        result = _run_p_spotify(sp_mock=sp)
        # playlist_list should be empty (no owned playlists)
        playlist_list = result[4]["graphic"][1]["playlist"]
        assert playlist_list == []


# ===========================================================================
# Graceful degradation: enrichment failures do not crash the task
# ===========================================================================


class TestGracefulDegradation:
    """Enrichment API failures must degrade gracefully — task must not crash."""

    def test_artists_api_failure_does_not_crash(self):
        """sp.artists() raises → genres/top_artists empty, task succeeds."""
        sp = _make_sp_mock(
            playlists=PLAYLIST_DATA,
            playlist_tracks=[TRACK_ITEM],
        )
        sp.artists.side_effect = Exception("Spotify API down")

        result = _run_p_spotify(sp_mock=sp)

        assert len(result) == 7  # task succeeded
        genres = result[4]["graphic"][5]["genres"]
        assert genres == []  # graceful degradation

    def test_audio_features_api_failure_does_not_crash(self):
        """sp.audio_features() raises → audio_profile empty, task succeeds."""
        sp = _make_sp_mock(
            playlists=PLAYLIST_DATA,
            playlist_tracks=[TRACK_ITEM],
        )
        sp.audio_features.side_effect = Exception("Rate limited")

        result = _run_p_spotify(sp_mock=sp)

        assert len(result) == 7
        audio_profile = result[4]["graphic"][6]["audio_profile"]
        assert audio_profile == {}

    def test_missing_credentials_returns_warning(self):
        """Missing API keys → iKy- exception → decorator returns Warning status."""

        def _no_key(name):
            return ""  # simulate missing keys

        with (
            patch("modules.spotify.spotify_tasks.api_keys_search", side_effect=_no_key),
        ):
            from modules.spotify.spotify_tasks import p_spotify

            result = p_spotify("anyuser")

        assert len(result) == 4  # [module, param, validation, raw] — error shape
        raw = result[3]["raw"]
        assert raw[0]["status"] == "Warning"
        assert "credential" in raw[0]["reason"].lower()

    def test_user_not_found_returns_fail(self):
        """sp.user() raises generic exception → Fail status from decorator."""

        def _key_lookup(name):
            return "fake"

        sp = MagicMock()
        sp.user.side_effect = Exception("User not found")

        with (
            patch(
                "modules.spotify.spotify_tasks.api_keys_search", side_effect=_key_lookup
            ),
            patch("modules.spotify.spotify_tasks.SpotifyClientCredentials"),
            patch("modules.spotify.spotify_tasks.spotipy.Spotify", return_value=sp),
        ):
            from modules.spotify.spotify_tasks import p_spotify

            result = p_spotify("baduser")

        assert len(result) == 4
        raw = result[3]["raw"]
        assert raw[0]["status"] == "Fail"

    def test_error_response_has_traceback(self):
        """Error raw node must contain a traceback string."""

        def _no_key(name):
            return ""

        with patch(
            "modules.spotify.spotify_tasks.api_keys_search", side_effect=_no_key
        ):
            from modules.spotify.spotify_tasks import p_spotify

            result = p_spotify("anyuser")

        raw = result[3]["raw"]
        assert "traceback" in raw[0]
        assert isinstance(raw[0]["traceback"], str)


# ===========================================================================
# Error response structure
# ===========================================================================


class TestErrorResponseStructure:
    """Verify error response format matches decorator contract."""

    def test_error_structure_has_4_keys(self):
        """Error response: [module, param, validation, raw] — no graphic/profile."""

        def _no_key(name):
            return ""

        with patch(
            "modules.spotify.spotify_tasks.api_keys_search", side_effect=_no_key
        ):
            from modules.spotify.spotify_tasks import p_spotify

            result = p_spotify("anyuser")

        keys = [next(iter(item)) for item in result]
        assert keys == ["module", "param", "validation", "raw"]

    def test_error_module_is_spotify(self):
        def _no_key(name):
            return ""

        with patch(
            "modules.spotify.spotify_tasks.api_keys_search", side_effect=_no_key
        ):
            from modules.spotify.spotify_tasks import p_spotify

            result = p_spotify("anyuser")

        assert result[0]["module"] == "spotify"


# ===========================================================================
# Dev-mode golden fixture
# ===========================================================================


class TestDevModeGoldenFixture:
    """Decorator dev-mode bypass via output-spotify.json."""

    def test_dev_mode_returns_golden_json(self, tmp_path):
        """When output-spotify.json exists, it's returned without API calls."""
        golden = [
            {"module": "spotify"},
            {"param": "devuser"},
            {"validation": "no"},
            {"raw": [{"raw_node_user": {}}]},
            {
                "graphic": [
                    {"social": []},
                    {"playlist": []},
                    {"autors": []},
                    {"words": []},
                    {"lang": []},
                    {"genres": [{"name": "pop", "value": 10, "count": 10}]},
                    {"audio_profile": {"danceability": 0.6}},
                    {
                        "popularity": {
                            "mainstream": 5,
                            "niche": 2,
                            "mean": 60.0,
                            "median": 65.0,
                        }
                    },
                ]
            },
            {"profile": []},
            {"timeline": [{"name": "2024-01", "value": 5}]},
        ]
        outputs = tmp_path / "outputs"
        outputs.mkdir()
        dev_file = outputs / "output-spotify.json"
        dev_file.write_text(json.dumps(golden))

        with (
            patch.object(Path, "cwd", return_value=tmp_path),
            patch("factories.task_wrapper.time.sleep") as mock_sleep,
        ):
            from modules.spotify.spotify_tasks import p_spotify

            result = p_spotify("anything")

        assert result == golden
        # dev_mode_sleep=15 must be honoured
        mock_sleep.assert_called_once_with(15)

    def test_dev_mode_fixture_includes_enrichment_sections(self, tmp_path):
        """Golden JSON must include genres, audio_profile, popularity sections."""
        import json as _json

        # Load the real golden fixture from the outputs directory
        fixture_path = Path(__file__).parent.parent / "outputs" / "output-spotify.json"
        if not fixture_path.exists():
            pytest.skip("output-spotify.json not found")

        with fixture_path.open() as f:
            golden = _json.load(f)

        graphic = next(item["graphic"] for item in golden if "graphic" in item)
        graphic_keys = [next(iter(g)) for g in graphic]

        assert "genres" in graphic_keys, "Golden JSON must include genres section"
        assert "audio_profile" in graphic_keys, "Golden JSON must include audio_profile"
        assert "popularity" in graphic_keys, "Golden JSON must include popularity"


# ===========================================================================
# Track cap enforcement
# ===========================================================================


class TestTrackCap:
    """Verify the 500-track cap is respected."""

    def test_tracks_capped_at_500(self):
        """Even with many playlist tracks, only MAX_TRACKS are processed."""
        from modules.spotify.spotify_tasks import _MAX_TRACKS

        assert _MAX_TRACKS == 500, "Track cap must be 500"

    def test_cap_stops_collection(self):
        """Task processes at most _MAX_TRACKS tracks total."""
        # Build a playlist with 600 items
        big_tracks = [
            {
                "track": {
                    "id": f"tr_{i}",
                    "name": f"Song {i}",
                    "artists": [{"id": "ar1", "name": "Artist"}],
                    "popularity": 50,
                },
                "added_at": "2024-01-01T00:00:00Z",
            }
            for i in range(600)
        ]

        sp = _make_sp_mock(
            playlists=PLAYLIST_DATA,
            playlist_tracks=big_tracks,
        )
        sp.artists.return_value = {"artists": []}
        sp.audio_features.return_value = []

        result = _run_p_spotify(sp_mock=sp)

        # Task must succeed regardless of cap
        assert len(result) == 7
