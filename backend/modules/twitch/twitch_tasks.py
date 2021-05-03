#!/usr/bin/env python
# -*- encoding: utf-8 -*-

# [ ] - proba con eko1212 que no tiene videos
# [ ] - Games

import sys
import traceback
import json
import time
from datetime import datetime
from parse import parse
from collections import Counter

import twitch

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


def p_twitch(username, from_m, level):
    """ Get basic info from Twitch"""
    client_id = api_keys_search('twitch_client_id')
    client_secret = api_keys_search('twitch_client_secret')
    helix = twitch.Helix(client_id, client_secret)

    user = helix.user(username)

    # Videos
    qty_video = 0
    table = []
    duration = []
    thumbnail = []
    hours = []
    days = []
    prev_day = "0000-00-00"
    time_value = 1
    t_timeline = []
    link = "Twitch"
    photos_item = {"name-node": "Twitch", "title": "Twitch",
                   "subtitle": "", "icon": "fab fa-twitch",
                   "link": link}
    thumbnail.append(photos_item)
    try:
        for video, comments in helix.user(username).videos().comments:
            qty_video += 1
            created_at = datetime.strptime(video.created_at,
                                           "%Y-%m-%dT%H:%M:%SZ")
            # Table list
            table.append({
                        "title": video.title,
                        "description": video.description,
                        "created": created_at.strftime("%Y-%m-%d %H:%M"),
                        "url": video.url,
                        })
            # Duration
            duration_time = 1
            if ('h' in video.duration):
                h, m, s = parse('{:d}h{:d}m{:d}s', video.duration)
                duration_time = h * 3600 + m * 60 + s
            elif ('m' in video.duration):
                m, s = parse('{:d}m{:d}s', video.duration)
                duration_time = m * 60 + s
            elif ('s' in video.duration):
                duration_time = parse('{:d}s', video.duration)[0]
            else:
                duration_time = 0

            duration.append({
                            "value": duration_time,
                            "name": video.duration,
                            })
            # Thumbnail
            photos_item = {"name-node": "Twitch" + str(qty_video),
                           "title": "Video " + str(qty_video),
                           "picture": video.thumbnail_url.
                           replace("%{width}", "300").
                           replace("%{height}", "300"),
                           "subtitle": "",
                           "link": link}
            thumbnail.append(photos_item)

            # Hours and days
            hours.append(created_at.strftime("%H"))
            days.append(created_at.strftime("%A"))

            # Timeline
            twitch_date = created_at.strftime("%Y-%m-%dT%H:%M:%S.009Z")
            twitch_day = created_at.strftime("%Y-%m-%d")
            if (prev_day == twitch_day):
                time_value = time_value + 1
            else:
                t_timeline.append({"name": twitch_date, "value": time_value})
                time_value = 1
                prev_day = twitch_day
    except Exception:
        pass

    # hourset
    hourset = []
    hournames = '00 01 02 03 04 05 06 07 08 09 10 11 12 13 14 15 16 17 ' \
        '18 19 20 21 22 23'
    hournames = hournames.split()

    twCounter = Counter(hours)
    tgdata = twCounter.most_common()
    tgdata = sorted(tgdata)
    e = 0
    for g in hournames:
        if (e >= len(tgdata)):
            hourset.append({"name": g, "value": 0})
        elif (g < tgdata[e][0]):
            hourset.append({"name": g, "value": 0})
        elif (g == tgdata[e][0]):
            hourset.append({"name": g, "value": int(tgdata[e][1])})
            e += 1

    # weekset
    weekset = []
    weekdays = 'Monday Tuesday Wednesday Thursday Friday Saturday Sunday'
    weekdays = weekdays.split()
    wdCounter = Counter(days)
    wddata = wdCounter.most_common()
    wddata = sorted(wddata)
    y = []
    c = 0
    for z in weekdays:
        try:
            weekset.append({"name": z, "value": int(wddata[c][1])})
        except Exception:
            weekset.append({"name": z, "value": 0})
        c += 1
    wddata = y

    # Followers
    qty_followers = 0
    try:
        for f in helix.user(username).followers():
            qty_followers += 1
    except Exception:
        pass

    # Following
    qty_followed = 0
    try:
        for f in helix.user(username).following():
            qty_followed += 1
    except Exception:
        pass

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
    raw_node_total.append({"status": "Ok",
                           "code": 0})
    # raw_node_total.append({'raw_node_user': user})

    total.append({'module': 'twitch'})
    total.append({'param': username})
    total.append({'validation': 'no'})

    link_social = "Twitch"
    gather_item = {"name-node": "Twitch", "title": "Twitch",
                   "subtitle": "", "icon": "fab fa-twitch",
                   "link": link_social}
    gather.append(gather_item)

    try:
        gather_item = {"name-node": "TwitchName",
                       "title": "Name",
                       "subtitle": user.display_name,
                       "icon": "fas fa-signature",
                       "link": link_social}
        gather.append(gather_item)
        profile_item = {'name': user.display_name}
        profile.append(profile_item)
    except Exception:
        raise Exception('User not FOUND')

    gather_item = {"name-node": "TwitchUserName",
                   "title": "Username",
                   "subtitle": username,
                   "icon": "fas fa-user-circle",
                   "link": link_social}
    gather.append(gather_item)
    profile_item = {'username': username}
    profile.append(profile_item)

    gather_item = {"name-node": "TwitchUserID",
                   "title": "User ID",
                   "subtitle": user.id,
                   "icon": "fas fa-id-badge",
                   "link": link_social}
    gather.append(gather_item)

    try:
        pic = user.profile_image_url
        gather_item = {"name-node": "TwitchPhoto",
                       "title": "Avatar",
                       "subtitle": "",
                       "picture": pic,
                       "link": link_social}
        gather.append(gather_item)
        photo_item = {"name-node": "Twitch",
                      "title": "Twitch",
                      "subtitle": "",
                      "picture": pic,
                      "link": "Photos"}
        profile.append({'photos': [photo_item]})
    except Exception:
        pass

    gather_item = {"name-node": "TwitchVideos",
                   "title": "Videos",
                   "subtitle": qty_video,
                   "icon": "fas fa-photo-video",
                   "link": link_social}
    gather.append(gather_item)

    gather_item = {"name-node": "TwitchViews",
                   "title": "Views",
                   "subtitle": user.view_count,
                   "icon": "fas fa-eye",
                   "link": link_social}
    gather.append(gather_item)

    gather_item = {"name-node": "TwitchFollowers",
                   "title": "Followers",
                   "subtitle": qty_followers,
                   "icon": "fas fa-users",
                   "link": link_social}
    gather.append(gather_item)

    gather_item = {"name-node": "TwitchFollowing",
                   "title": "Following",
                   "subtitle": qty_followed,
                   "icon": "fas fa-users",
                   "link": link_social}
    gather.append(gather_item)

    gather_item = {"name-node": "TwitchEmail",
                   "title": "Email",
                   "subtitle": user.email,
                   "icon": "fas fa-at",
                   "link": link_social}
    gather.append(gather_item)

    try: 
        if (user.created_at):
            created_at = datetime.strptime(user.created_at,
                                           "%Y-%m-%dT%H:%M:%S.%fZ")
            gather_item = {"name-node": "TwitchCreate",
                           "title": "Created",
                           "subtitle": created_at.strftime("%Y-%m-%d"),
                           "icon": "fas fa-calendar-check",
                           "link": link_social}
            gather.append(gather_item)

            timeline_item = {"date": created_at.strftime("%Y-%m-%d"),
                             "action": "Twitch : Create Account",
                             "icon": "fa-twitch"}
            timeline.append(timeline_item)
    except Exception:
        pass

    social_item = {"name": "Twitch",
                   "url": "https://twitch.tv/" + username,
                   "icon": "fab fa-twitch",
                   "source": "Twitch",
                   "username": username}
    social.append(social_item)
    profile.append({"social": social})

    if (user.description):
        profile.append({'bio': user.description})

    presence.append({"name": "twitch",
                     "children": [
                         {"name": "followers", 
                          "value": qty_followers},
                         {"name": "following", 
                          "value": qty_followed},
                     ]})
    profile.append({'presence': presence})

    total.append({'raw': raw_node_total})
    graphic.append({'social': gather})
    graphic.append({'table': table})
    graphic.append({'duration': duration})
    graphic.append({'thumbnail': thumbnail})
    graphic.append({'week': weekset})
    graphic.append({'hour': hourset})
    graphic.append({'time': t_timeline})
    total.append({'graphic': graphic})
    total.append({'profile': profile})
    total.append({'timeline': timeline})

    return total


@celery.task
def t_twitch(username, from_m="initial", level=1):
    """ Task of Celery that get info from twitch"""
    total = []
    tic = time.perf_counter()
    try:
        total = p_twitch(username, from_m, level)
    except Exception as e:
        traceback.print_exc()
        traceback_text = traceback.format_exc()
        total.append({'module': 'twitch'})
        total.append({'param': username})
        total.append({'validation': 'soft'})

        raw_node = []
        if (e.args[0] == "User not FOUND"):
            raw_node.append({"status": "fail",
                            "code": 1,
                            "reason": "{}".format(e),
                            "traceback": traceback_text})
        else:
            raw_node.append({"status": "fail",
                            "code": 10,
                            "reason": "{}".format(e),
                            "traceback": traceback_text})
        total.append({"raw": raw_node})

    toc = time.perf_counter()
    print(f"Twitch - Response in {toc - tic:0.4f} seconds")

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
    result = t_twitch(username, "initial", level)
    output(result)
