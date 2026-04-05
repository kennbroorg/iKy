#!/usr/bin/env python
"""Spotify OSINT module — @iky_task pattern with enrichment pipeline."""

import argparse
import json
from collections import Counter
from typing import Any

import spotipy
from celery.utils.log import get_task_logger
from factories.configuration import api_keys_search
from factories.task_wrapper import iky_task
from langdetect import detect
from spotipy.oauth2 import SpotifyClientCredentials
from stop_words import AVAILABLE_LANGUAGES, get_stop_words

logger = get_task_logger(__name__)

# Maximum tracks to process across all playlists (avoids runaway on large libraries)
_MAX_TRACKS = 500


# ---------------------------------------------------------------------------
# Private helpers — fetch layer
# ---------------------------------------------------------------------------


def _batch_fetch_artists(sp: spotipy.Spotify, artist_ids: set[str]) -> dict[str, dict]:
    """Batch-fetch artist objects in chunks of 50.

    Returns a mapping of artist_id → artist data dict.
    Gracefully returns {} on any exception so enrichment failures
    never crash the main task.
    """
    try:
        result: dict[str, dict] = {}
        ids = list(artist_ids)
        for i in range(0, len(ids), 50):
            batch = ids[i : i + 50]
            resp = sp.artists(batch)
            for artist in resp.get("artists", []):
                if artist:
                    result[artist["id"]] = artist
        return result
    except Exception as e:
        logger.warning(
            "Spotify - Failed to fetch artist details, skipping enrichment: %s", e
        )
        return {}


def _batch_fetch_audio_features(
    sp: spotipy.Spotify, track_ids: list[str]
) -> list[dict]:
    """Batch-fetch audio features in chunks of 100.

    Returns a flat list of feature dicts (None entries filtered out).
    Gracefully returns [] on any exception.
    """
    try:
        result: list[dict] = []
        for i in range(0, len(track_ids), 100):
            batch = track_ids[i : i + 100]
            features = sp.audio_features(batch)
            if features:
                result.extend(f for f in features if f is not None)
        return result
    except Exception as e:
        logger.warning(
            "Spotify - Failed to fetch audio features, skipping audio profile: %s", e
        )
        return []


# ---------------------------------------------------------------------------
# Private helpers — aggregation layer
# ---------------------------------------------------------------------------


def _aggregate_genres(artists_data: dict[str, dict]) -> list[dict]:
    """Compute genre frequency from artist data.

    Returns [{"name": genre, "value": count, "count": count}, ...] sorted
    descending by count.
    """
    try:
        genre_counter: Counter = Counter()
        for artist in artists_data.values():
            for genre in artist.get("genres", []):
                genre_counter[genre] += 1
        return [
            {"name": genre, "value": count, "count": count}
            for genre, count in genre_counter.most_common()
            if count > 0
        ]
    except Exception as e:
        logger.warning("Spotify - Failed to aggregate genres: %s", e)
        return []


def _aggregate_audio_features(features: list[dict]) -> dict[str, float]:
    """Compute mean audio features across all tracks.

    Returns a dict of feature_name → mean value.  Empty dict if no data.
    """
    try:
        if not features:
            return {}
        keys = [
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
        ]
        totals: dict[str, float] = dict.fromkeys(keys, 0.0)
        count = 0
        for feat in features:
            if not isinstance(feat, dict):
                continue
            count += 1
            for k in keys:
                totals[k] += feat.get(k, 0.0) or 0.0
        if count == 0:
            return {}
        return {k: round(totals[k] / count, 4) for k in keys}
    except Exception as e:
        logger.warning("Spotify - Failed to aggregate audio features: %s", e)
        return {}


def _build_timeline(added_at_list: list[str]) -> list[dict]:
    """Build monthly activity timeline from ISO added_at timestamps.

    Returns [{"name": "YYYY-MM", "value": count}, ...] sorted chronologically.
    Gracefully returns [] on any exception.
    """
    try:
        if not added_at_list:
            return []
        monthly: Counter = Counter()
        for ts in added_at_list:
            if ts and len(ts) >= 7:
                # ISO 8601 → "YYYY-MM-DDTHH:MM:SSZ" — grab first 7 chars
                month_key = ts[:7]
                monthly[month_key] += 1
        return [
            {"name": month, "value": count} for month, count in sorted(monthly.items())
        ]
    except Exception as e:
        logger.warning("Spotify - Failed to build timeline: %s", e)
        return []


def _build_top_artists(
    autors_sum: list[str], artists_data: dict[str, dict]
) -> list[dict]:
    """Rank artists by track count, enriched with genres and popularity.

    Returns [{"name": artist, "count": N, "genres": [...], "popularity": N}, ...]
    sorted descending by count.  Only includes artists appearing > 1 time.
    """
    try:
        counter = Counter(autors_sum)
        result = []
        # Build a name → artist_data lookup for fast enrichment
        name_to_data: dict[str, dict] = {
            a.get("name", ""): a for a in artists_data.values()
        }
        for name, count in counter.most_common():
            if count < 2:  # skip single-track artists (consistent with existing logic)
                break
            artist_info = name_to_data.get(name, {})
            result.append(
                {
                    "name": name,
                    "count": count,
                    "genres": artist_info.get("genres", []),
                    "popularity": artist_info.get("popularity", 0),
                }
            )
        return result
    except Exception as e:
        logger.warning("Spotify - Failed to build top artists: %s", e)
        return []


def _analyze_popularity(tracks_data: list[dict]) -> dict[str, Any]:
    """Categorize track popularity into mainstream / niche buckets.

    Mainstream: popularity >= 50
    Niche: popularity < 50

    Returns {"mainstream": N, "niche": N, "mean": float, "median": float}.
    Returns {} on empty input or exception.
    """
    try:
        scores = [
            t.get("popularity", 0)
            for t in tracks_data
            if isinstance(t.get("popularity"), int | float)
        ]
        if not scores:
            return {}
        mainstream = sum(1 for s in scores if s >= 50)
        niche = sum(1 for s in scores if s < 50)
        mean_val = round(sum(scores) / len(scores), 2)
        sorted_scores = sorted(scores)
        n = len(sorted_scores)
        if n % 2 == 1:
            median_val = float(sorted_scores[n // 2])
        else:
            median_val = round(
                (sorted_scores[n // 2 - 1] + sorted_scores[n // 2]) / 2, 2
            )
        return {
            "mainstream": mainstream,
            "niche": niche,
            "mean": mean_val,
            "median": median_val,
        }
    except Exception as e:
        logger.warning("Spotify - Failed to analyze popularity: %s", e)
        return {}


# ---------------------------------------------------------------------------
# Track analysis — preserved from original, cleaned up
# ---------------------------------------------------------------------------


def _analize_tracks(sp: spotipy.Spotify, tracks: dict) -> tuple[list, list, list]:
    """Analyse tracks from Spotify (author names, word frequencies, language).

    Returns (autors_list, words_list, lang_list).
    Identical logic to the original analize_tracks() but without the dead
    `level` parameter and dead `print()` call.
    """
    autors: list[str] = []
    words: list[str] = []
    lang: list[str] = []

    stop_words_list: list[str] = []
    for lg in AVAILABLE_LANGUAGES:
        stop_words_list = stop_words_list + get_stop_words(lg)

    for item in tracks.get("items", []):
        track = item.get("track")
        if not track:
            continue

        if track.get("artists"):
            autors.append(track["artists"][0]["name"])

        song = track.get("name", "").lower()
        try:
            lang_detect = detect(song)
        except Exception:
            lang_detect = "en"
        lang.append(lang_detect)

        song_words = song.split(" ")
        filtered = [
            w for w in song_words if w.isalpha() and w.lower() not in stop_words_list
        ]
        words.extend(filtered)

    return autors, words, lang


# ---------------------------------------------------------------------------
# Main task
# ---------------------------------------------------------------------------


@iky_task(module_name="spotify", dev_mode_sleep=15)
def p_spotify(username: str) -> list[dict[str, Any]]:
    """Spotify OSINT task — profile, playlists, and enrichment data."""

    # --- Authenticate ---
    client_id = api_keys_search("spotify_client_id")
    client_secret = api_keys_search("spotify_client_secret")

    if not client_id or not client_secret:
        raise Exception("iKy - Missing or invalid Spotify API credentials")

    client_credentials_manager = SpotifyClientCredentials(
        client_id=client_id, client_secret=client_secret
    )
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

    user = sp.user(username)
    user_id = user["id"]

    playlists = sp.user_playlists(username)

    # --- Accumulate data across owned playlists ---
    playlist_count = 0
    track_count = 0
    playlist_list: list[dict] = []
    autors_sum: list[str] = []
    words_sum: list[str] = []
    lang_sum: list[str] = []

    # Enrichment accumulators
    track_ids: list[str] = []
    artist_ids: set[str] = set()
    added_at_list: list[str] = []
    tracks_data: list[dict] = []  # lightweight track dicts for popularity

    total_tracks_collected = 0

    last_playlist = None  # keep for raw_node_playlist (legacy)

    for playlist in playlists.get("items", []):
        playlist_count += 1
        if playlist["owner"]["id"] != user_id:
            continue

        last_playlist = playlist
        playlist_list.append(
            {"name": playlist["name"], "value": playlist["tracks"]["total"]}
        )
        track_count += playlist["tracks"]["total"]

        results = sp.playlist(playlist["id"], fields="tracks,next")
        tracks = results["tracks"]

        while tracks:
            # Respect the 500-track cap
            remaining_cap = _MAX_TRACKS - total_tracks_collected
            if remaining_cap <= 0:
                break

            autors_temp, words_temp, lang_temp = _analize_tracks(sp, tracks)
            autors_sum.extend(autors_temp)
            words_sum.extend(words_temp)
            lang_sum.extend(lang_temp)

            for item in tracks.get("items", []):
                if total_tracks_collected >= _MAX_TRACKS:
                    break
                track = item.get("track")
                if not track:
                    continue
                # Collect IDs for enrichment
                if track.get("id"):
                    track_ids.append(track["id"])
                for a in track.get("artists", []):
                    if a.get("id"):
                        artist_ids.add(a["id"])
                if item.get("added_at"):
                    added_at_list.append(item["added_at"])
                tracks_data.append(
                    {"id": track.get("id"), "popularity": track.get("popularity", 0)}
                )
                total_tracks_collected += 1

            if tracks.get("next"):
                tracks = sp.next(tracks)
            else:
                break

    # --- Build classic aggregates (preserved from original) ---
    autors: list[dict] = []
    autors_counter = Counter(autors_sum)
    for k, v in autors_counter.items():
        if v > 1:
            autors.append({"label": k, "value": v})

    words: list[dict] = []
    words_counter = Counter(words_sum)
    for k, v in words_counter.items():
        if v > 1:
            words.append({"label": k, "value": v})

    lang: list[dict] = []
    lang_counter = Counter(lang_sum)
    for k, v in lang_counter.items():
        if v > 1:
            lang.append({"name": k, "value": v, "count": v})

    # --- Enrichment pipeline ---
    artists_data = _batch_fetch_artists(sp, artist_ids)
    audio_features = _batch_fetch_audio_features(sp, track_ids)

    genres = _aggregate_genres(artists_data)
    audio_profile = _aggregate_audio_features(audio_features)
    timeline = _build_timeline(added_at_list)
    popularity = _analyze_popularity(tracks_data)

    # --- Build response arrays ---
    gather: list[dict] = []
    profile: list[dict] = []
    social: list[dict] = []
    presence: list[dict] = []

    link_social = "Spotify"

    gather.append(
        {
            "name-node": "Spotify",
            "title": "Spotify",
            "subtitle": "",
            "icon": "fab fa-spotify",
            "link": link_social,
        }
    )

    gather.append(
        {
            "name-node": "SpotifyName",
            "title": "Name",
            "subtitle": user.get("display_name", ""),
            "icon": "fas fa-signature",
            "link": link_social,
        }
    )
    profile.append({"name": user.get("display_name", "")})

    gather.append(
        {
            "name-node": "SpotifyUserName",
            "title": "Username",
            "subtitle": user["id"],
            "icon": "fas fa-user-circle",
            "link": link_social,
        }
    )
    profile.append({"username": user["id"]})

    try:
        pic = user["images"][0]["url"]
        gather.append(
            {
                "name-node": "SpotifyPhoto",
                "title": "Avatar",
                "subtitle": "",
                "picture": pic,
                "link": link_social,
            }
        )
        profile.append(
            {
                "photos": [
                    {
                        "name-node": "Spotify",
                        "title": "Spotify",
                        "subtitle": "",
                        "picture": pic,
                        "link": "Photos",
                    }
                ]
            }
        )
    except (KeyError, IndexError):
        pass

    gather.append(
        {
            "name-node": "SpotifyPlaylist",
            "title": "Playlist",
            "subtitle": playlist_count,
            "icon": "fas fa-compact-disc",
            "link": link_social,
        }
    )

    gather.append(
        {
            "name-node": "SpotifyTracks",
            "title": "Tracks",
            "subtitle": track_count,
            "icon": "fas fa-music",
            "link": link_social,
        }
    )

    gather.append(
        {
            "name-node": "SpotifyFollowers",
            "title": "Followers",
            "subtitle": user.get("followers", {}).get("total", 0),
            "icon": "fas fa-users",
            "link": link_social,
        }
    )

    social.append(
        {
            "name": "Spotify",
            "url": user.get("external_urls", {}).get("spotify", ""),
            "icon": "fab fa-spotify",
            "source": "Spotify",
            "username": username,
        }
    )
    profile.append({"social": social})

    presence.append(
        {
            "name": "spotify",
            "children": [
                {
                    "name": "followers",
                    "value": user.get("followers", {}).get("total", 0),
                },
            ],
        }
    )
    profile.append({"presence": presence})

    top_artists = _build_top_artists(autors_sum, artists_data)

    # --- Assemble raw node ---
    raw_node_total: list[dict] = [
        {"raw_node_user": user},
        {"raw_node_playlist": last_playlist},
        {"raw_node_artists": artists_data},
        {"raw_node_top_artists": top_artists},
    ]

    # --- Assemble graphic array (indices [0]-[4] preserved, [5]-[7] new) ---
    graphic: list[dict] = [
        {"social": gather},  # [0] profile nodes
        {"playlist": playlist_list},  # [1] playlist names+counts
        {"autors": autors},  # [2] artist frequency
        {"words": words},  # [3] word frequency
        {"lang": lang},  # [4] language bubble
        {"genres": genres},  # [5] NEW — genre frequency
        {"audio_profile": audio_profile},  # [6] NEW — mean audio features
        {"popularity": popularity},  # [7] NEW — popularity distribution
    ]

    # --- Assemble top-level 7-element response ---
    total: list[dict[str, Any]] = [
        {"module": "spotify"},  # [0]
        {"param": username},  # [1]
        {"validation": "no"},  # [2]
        {"raw": raw_node_total},  # [3]
        {"graphic": graphic},  # [4]
        {"profile": profile},  # [5]
        {"timeline": timeline},  # [6]  monthly added_at activity
    ]

    return total


# Backward-compatible alias — registry and existing callers reference t_spotify
t_spotify = p_spotify


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def output(data: Any) -> None:
    """Print JSON to stdout."""
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Query Spotify OSINT data for a username"
    )
    parser.add_argument("username", help="Spotify username to look up")
    args = parser.parse_args()

    result = t_spotify(args.username)
    output(result)
