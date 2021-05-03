#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# TODO : Tracks features
# TODO : Sentiment over song's title
# TODO : Research how to get followers profiles and Following profiles

import sys
import traceback
import json
from collections import Counter
from stop_words import get_stop_words
from stop_words import AVAILABLE_LANGUAGES
from langdetect import detect
import time

from spotipy.oauth2 import SpotifyClientCredentials
import spotipy

try:
    from factories._celery import create_celery
    from factories.application import create_application
    from factories.configuration import api_keys_search
    from celery.utils.log import get_task_logger
    celery = create_celery(create_application())
except ImportError:
    # This is to test the module individually, and I know that is piece of shit
    sys.path.append('../../')
    from factories._celery import create_celery
    from factories.application import create_application
    from factories.configuration import api_keys_search
    from celery.utils.log import get_task_logger
    celery = create_celery(create_application())

logger = get_task_logger(__name__)


def analize_tracks(sp, tracks, level):
    """ Analize tracks from Spotify (Autor, Name, sentiment) """
    autors = []
    words = []
    lang = []

    stop_words_list = []
    for lg in AVAILABLE_LANGUAGES:
        stop_words_list = stop_words_list + get_stop_words(lg)

    for i, item in enumerate(tracks['items']):
        track = item['track']
        autors.append(track['artists'][0]['name'])

        song = track['name'].lower()
        try:
            lang_detect = detect(song)
        except Exception:
            lang_detect = 'en'
        lang.append(lang_detect)

        song_words = song.split(" ")
        song_filtered_sentence = [w for w in song_words
                                  if w.isalpha() and
                                  w.lower() not in stop_words_list]
        words = words + song_filtered_sentence

        if (int(level) == 2):
            features = sp.audio_features(track['id'])
            print(json.dumps(features, indent=4))

    return autors, words, lang


def p_spotify(username, from_m, level):
    """ Get basic info from spotify"""
    client_id = api_keys_search('spotify_client_id')
    client_secret = api_keys_search('spotify_client_secret')

    client_credentials_manager = SpotifyClientCredentials(
        client_id=client_id, client_secret=client_secret)
    sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
    sp.trace = True
    user = sp.user(username)
    user_id = user["id"]

    playlists = sp.user_playlists(username)
    playlist_count = 0
    track_count = 0

    playlist_list = []
    words = []
    autors = []
    lang = []
    autors_sum = []
    words_sum = []
    lang_sum = []

    for playlist in playlists['items']:
        playlist_count = playlist_count + 1
        if playlist['owner']['id'] == user_id:
            playlist_list.append({"name": playlist['name'],
                                  "value": playlist['tracks']['total']})
            track_count = track_count + playlist['tracks']['total']

            results = sp.playlist(playlist['id'], fields="tracks,next")
            tracks = results['tracks']
            autors_temp, words_temp, lang_temp = analize_tracks(
                sp, tracks, level)
            autors_sum = autors_sum + autors_temp
            words_sum = words_sum + words_temp
            lang_sum = lang_sum + lang_temp

            while tracks['next']:
                tracks = sp.next(tracks)
                autors_temp, words_temp, lang_temp = analize_tracks(
                    sp, tracks, level)
                autors_sum = autors_sum + autors_temp
                words_sum = words_sum + words_temp
                lang_sum = lang_sum + lang_temp

    # Autors (continue)
    autors_counter = Counter(autors_sum)
    for k, v in autors_counter.items():
        if(v > 1):
            autors.append({"label": k, "value": v})

    # Word relevance
    words_counter = Counter(words_sum)
    for k, v in words_counter.items():
        if(v > 1):
            words.append({"label": k, "value": v})

    # Lang bubble
    lang_counter = Counter(lang_sum)
    for k, v in lang_counter.items():
        if(v > 1):
            lang.append({"name": k, "value": v, "count": v})

    # Total
    total = []
    # Graphic Array
    graphic = []
    gather = []

    # Profile Array
    profile = []
    social = []
    presence = []

    # # Timeline Array
    timeline = []

    raw_node_total = []
    raw_node_total.append({'raw_node_user': user})
    raw_node_total.append({'raw_node_playlist': playlist})

    total.append({'module': 'spotify'})
    total.append({'param': username})
    total.append({'validation': 'no'})

    link_social = "Spotify"
    gather_item = {"name-node": "Spotify", "title": "Spotify",
                   "subtitle": "", "icon": "fab fa-spotify",
                   "link": link_social}
    gather.append(gather_item)

    gather_item = {"name-node": "SpotifyName",
                   "title": "Name",
                   "subtitle": user['display_name'],
                   "icon": "fas fa-signature",
                   "link": link_social}
    gather.append(gather_item)
    profile_item = {'name': user['display_name']}
    profile.append(profile_item)

    gather_item = {"name-node": "SpotifyUserName",
                   "title": "Username",
                   "subtitle": user['id'],
                   "icon": "fas fa-user-circle",
                   "link": link_social}
    gather.append(gather_item)
    profile_item = {'username': user['id']}
    profile.append(profile_item)

    try:
        pic = user['images'][0]['url']
        # pic = user['images'][1]['url']
        gather_item = {"name-node": "SpotifyPhoto",
                       "title": "Avatar",
                       "subtitle": "",
                       "picture": pic,
                       "link": link_social}
        gather.append(gather_item)
        photo_item = {"name-node": "Spotify",
                      "title": "Spotify",
                      "subtitle": "",
                      "picture": pic,
                      "link": "Photos"}
        profile.append({'photos': [photo_item]})
    except Exception:
        pass

    gather_item = {"name-node": "SpotifyPlaylist",
                   "title": "Playlist",
                   "subtitle": playlist_count,
                   "icon": "fas fa-compact-disc",
                   "link": link_social}
    gather.append(gather_item)

    gather_item = {"name-node": "SpotifyTracks",
                   "title": "Tracks",
                   "subtitle": track_count,
                   "icon": "fas fa-music",
                   "link": link_social}
    gather.append(gather_item)

    gather_item = {"name-node": "SpotifyFollowers",
                   "title": "Followers",
                   "subtitle": user['followers']['total'],
                   "icon": "fas fa-users",
                   "link": link_social}
    gather.append(gather_item)

    social_item = {"name": "Spotify",
                   "url": user['external_urls']['spotify'],
                   "icon": "fab fa-spotify",
                   "source": "Spotify",
                   "username": username}
    social.append(social_item)
    profile.append({"social": social})

    presence.append({"name": "spotify",
                     "children": [
                         {"name": "followers", 
                          "value": user['followers']['total']},
                     ]})

    profile.append({'presence': presence})

    total.append({'raw': raw_node_total})
    graphic.append({'social': gather})
    graphic.append({'playlist': playlist_list})
    graphic.append({'autors': autors})
    graphic.append({'words': words})
    graphic.append({'lang': lang})
    total.append({'graphic': graphic})
    total.append({'profile': profile})
    total.append({'timeline': timeline})

    return total


@celery.task
def t_spotify(username, from_m, level=1):
    """ Task of Celery that get info from spotify"""
    total = []
    tic = time.perf_counter()
    try:
        total = p_spotify(username, from_m, level)
    except Exception as e:
        traceback.print_exc()
        traceback_text = traceback.format_exc()
        total.append({'module': 'spotify'})
        total.append({'param': username})
        total.append({'validation': 'soft'})

        raw_node = []
        raw_node.append({"status": "fail",
                         "reason": "{}".format(e),
                         # "traceback": 1})
                         "traceback": traceback_text})
        total.append({"raw": raw_node})

    toc = time.perf_counter()
    print(f"Spotify - Response in {toc - tic:0.4f} seconds")

    return total


def output(data):
    """ Print JSON dump """
    print(json.dumps(data, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    username = sys.argv[1]
    try:
        level = sys.argv[2]
    except Exception:
        level = 1
    result = t_spotify(username, "initial", level)
    output(result)
