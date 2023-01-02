#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import sys
import json
import requests
import time
import traceback
from requests_html import HTMLSession
import re

try:
    from factories._celery import create_celery
    from factories.application import create_application
    # from factories.fontcheat import fontawesome_cheat, search_icon
    from factories.fontcheat import fontawesome_cheat_5, search_icon_5
    from celery.utils.log import get_task_logger
    from factories.iKy_functions import analize_rrss
    from factories.iKy_functions import location_geo
    celery = create_celery(create_application())
except ImportError:
    # This is to test the module individually, and I know that is piece of shit
    sys.path.append('../../')
    from factories._celery import create_celery
    from factories.application import create_application
    # from factories.fontcheat import fontawesome_cheat, search_icon
    from factories.fontcheat import fontawesome_cheat_5, search_icon_5
    from celery.utils.log import get_task_logger
    from factories.iKy_functions import analize_rrss
    from factories.iKy_functions import location_geo
    celery = create_celery(create_application())

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

logger = get_task_logger(__name__)


def p_keybase(username, from_m):
    print(f"Procesando: {username}")
    url = "https://keybase.io/_/api/1.0/user/lookup.json?" + \
          "usernames=%s" % username
    req = requests.get(url)
    raw_node = json.loads(req.text)

    # Get Followers and Following throw crawling
    url_user = 'https://keybase.io/%s' % username
    session = HTMLSession()
    r_html = session.get(url_user)
    follow = r_html.html.find('#profile-tracking-section', first=True)

    following = "Undefined"
    following_num = 0
    try: 
        regex = r"Following \(([0-9]*)\)"
        matches = re.finditer(regex, follow.text, re.MULTILINE)
        for match in matches:
            if (match.group() != ''):
                following = match.group(1)
                following_num = int(following)
    except Exception:
        pass

    followers = "Undefined"
    followers_num = 0
    try:
        regex = r"Followers \(([0-9]*)\)"
        matches = re.finditer(regex, follow.text, re.MULTILINE)
        for match in matches:
            if (match.group() != ''):
                followers = match.group(1)
                followers_num = int(followers)
    except Exception:
        pass

    # Icons
    font_list = fontawesome_cheat_5()
    # Total
    total = []
    total.append({'module': 'keybase'})
    total.append({'param': username})
    # Evaluates the module that executed the task
    if (from_m == 'Initial'):
        total.append({'validation': 'no'})
    else:
        total.append({'validation': 'soft'})

    if (raw_node['status']['code'] == 0) and (raw_node['them'][0] is not None):
        raw = raw_node['them'][0]

        # Graphic Array
        graphic = []

        # Profile Array
        profile = []
        social_profile = []

        # Timeline Array
        timeline = []

        # Tasks Array
        tasks = []

        # Devices Array
        devices = []

        # Social Array
        social = []

        # Graph Array
        graph = []

        # Presence Array
        presence = []

        link_graph = "KeybaseGraph"
        graph_item = {"name-node": "KeybaseGraph", "title": "KeybaseGraphs",
                       "subtitle": "", "icon": "fab fa-keybase", "link": link_graph}
        graph.append(graph_item)

        link_device = "Devices"
        device_item = {"name-node": "Devices", "title": "Devices",
                       "subtitle": "", "icon": "fas fa-laptop", "link": link_device}
        devices.append(device_item)

        link_social = "KeybaseSocial"
        social_item = {"name-node": "KeybaseSocial", "title": "KeybaseSocial",
                       "subtitle": "", "icon": "fas fa-child", "link": link_social}
        social.append(social_item)

        graph_item = {"name-node": "GraphUsername",
                        "title": "Username",
                        "subtitle": username,
                        "icon": "fas fa-user",
                        "link": link_graph}
        graph.append(graph_item)

        graph_item = {"name-node": "GraphFollowers",
                        "title": "Followers",
                        "subtitle": followers,
                        "icon": "fas fa-users",
                        "link": link_graph}
        graph.append(graph_item)

        graph_item = {"name-node": "GraphFollowing",
                        "title": "Following",
                        "subtitle": following,
                        "icon": "fas fa-users",
                        "link": link_graph}
        graph.append(graph_item)

        if (raw.get("profile", "") != ""):
            if (raw.get("profile", "").get("full_name", "") != ""):
                profile_item = {'name': raw.get("profile", "")
                                .get("full_name", "")}
                profile.append(profile_item)
                graph_item = {"name-node": "GraphName", 
                                "title": "Name",
                                "subtitle": raw.get("profile", "").get("full_name", ""),
                                "icon": "fas fa-user",
                                "link": link_graph}
                graph.append(graph_item)

            if (raw.get("profile", "").get("location", "") != None) and (raw.get("profile", "").get("location", "") != ""):
                profile_item = {'location': raw.get("profile", "")
                                .get("location", "")}
                profile.append(profile_item)
                graph_item = {"name-node": "GraphLocation", 
                                "title": "Location",
                                "subtitle": raw.get("profile", "").get("location", ""),
                                "icon": "fas fa-map-marker-alt",
                                "link": link_graph}
                graph.append(graph_item)

            if (raw.get("profile", "").get("bio", "") != ""):
                profile_item = {'bio': raw.get("profile", "").get("bio", "")}
                profile.append(profile_item)
            
                analyze = analize_rrss(raw.get("profile", "").get("bio", ""))
                for item in analyze:
                    if(item == 'url'):
                        for i in analyze['url']:
                            profile.append(i)
                    if(item == 'tasks'):
                        for i in analyze['tasks']:
                            tasks.append(i)

        if (raw.get("pictures", "") != ""):
            if (raw.get("pictures", "").get("primary", "") != ""):
                if (raw.get("pictures", "").get("primary", "").get(
                        "url", "") != ""):

                    profile_item = {'photos': [{
                        "picture": raw.get("pictures", "").get(
                            "primary", "").get("url", ""),
                        "title": "Keybase"}]}
                    profile.append(profile_item)

                    graph_item = {"name-node": "KeyAvatar", "title": "Avatar",
                                "picture": raw.get("pictures", "").get(
                                    "primary", "").get("url", ""),
                                "subtitle": "",
                                "link": link_graph}
                    graph.append(graph_item)

        if (raw.get("basics", "") != ""):
            if (raw.get("basics", "").get("ctime", "") != ""):
                ctime = time.strftime('%Y/%m/%d %H:%M:%S',
                                      time.gmtime(raw.get("basics", "")
                                                  .get("ctime")))
                timeline_item = {"action": "Keybase: Create Account",
                                 "date": ctime, "icon": "fas fa-key"}
                timeline.append(timeline_item)

                graph_item = {"name-node": "GraphJoin", 
                                "title": "Join Date",
                                "subtitle": ctime,
                                "icon": "fas fa-calendar-check",
                                "link": link_graph}
                graph.append(graph_item)

            if (raw.get("basics", "").get("mtime", "") != ""):
                mtime = time.strftime('%Y/%m/%d %H:%M:%S',
                                      time.gmtime(raw.get("basics", "")
                                                  .get("mtime")))
                timeline_item = {"action": "Keybase : Update Account",
                                 "date": mtime, "icon": "fas fa-key"}
                timeline.append(timeline_item)

        for dev in raw.get("devices", ""):

            # print(dev)
            # print(" Type ", raw.get("devices").get(dev).get("type", ""))
            fa_icon = search_icon_5(raw.get("devices").get(dev).get("type", ""),
                                  font_list)
            if (fa_icon is None):
                fa_icon = search_icon_5("question", font_list)

            device_item = {"name-node": raw.get("devices").get(dev)
                           .get("type", ""),
                           "title": raw.get("devices").get(dev)
                           .get("type", ""),
                           "subtitle": "Name : " + raw.get("devices").get(dev)
                           .get("name", ""),
                           "icon": fa_icon,
                           "link": link_device}
            devices.append(device_item)

        if (raw.get("proofs_summary", "") != ""):
            for soc in raw.get("proofs_summary", "").get("all"):
                fa_icon = search_icon_5(soc.get("proof_type"), font_list)
                if (fa_icon is None):
                    fa_icon = search_icon_5("question", font_list)

                social_item = {"name-node": "keybase" +
                               soc.get("proof_type", ""),
                               "title": soc.get("proof_type", ""),
                               "subtitle": soc.get("nametag", ""),
                               "icon": fa_icon,
                               "link": link_social}
                social.append(social_item)

                social_profile_item = {"name": soc.get("proof_type"),
                                       "username": soc.get("nametag"),
                                       "Source": "Keybase",
                                       "icon": fa_icon,
                                       "url": soc.get("service_url")}
                social_profile.append(social_profile_item)

                tasks.append({"module": soc.get("proof_type", "").lower(),
                             "param": soc.get("nametag", "")})

        # Keybase : TODO : Find an example of webs and
        # Keybase : Find an example of cryptocurrency_addresses and
        if (raw.get("cryptocurrency_addresses", "") != ""):
            if (raw.get("cryptocurrency_addresses", "").get("bitcoin", "") != ""):

                for address in raw.get("cryptocurrency_addresses").get("bitcoin"):
                    social_item = {"name-node": "keybaseBTC",
                                    "title": "Cryptocurrency",
                                    "subtitle": address.get("address"),
                                    "icon": "fab fa-btc",
                                    "link": link_social}
                    social.append(social_item)

        presence.append({"name": "keybase",
                        "children": [
                            {"name": "followers", 
                            "value": followers_num},
                            {"name": "following", 
                            "value": following_num},
                        ]})
        profile.append({'presence': presence})

        total.append({'raw': raw_node})
        if (len(social) > 1):
            graphic.append({'keysocial': social})
        if (len(devices) > 1):
            graphic.append({'devices': devices})
        if (len(graph) > 1):
            graphic.append({'keygraph': graph})
        total.append({'graphic': graphic})
        if (social_profile != []):
            profile.append({'social': social_profile})
        if (profile != []):
            total.append({'profile': profile})
        if (timeline != []):
            total.append({'timeline': timeline})

        # Keybase : TODO : Before send task,
        # code the validation for duplicate proccess
        if (tasks != []):
            total.append({'tasks': tasks})

    else:
        total = []
        total.append({'module': 'keybase'})
        total.append({'param': username})
        total.append({'validation': 'not_used'})

        raw_node = []
        raw_node.append({"status": "Fail",
                         "reason": "User not found",
                         "traceback": "User not found"})
        total.append({"raw": raw_node})

    return total


@celery.task
def t_keybase(username, from_m="Initial"):
    total = []
    try:
        total = p_keybase(username, from_m)
    except Exception as e:
        traceback.print_exc()
        traceback_text = traceback.format_exc()
        total.append({'module': 'keybase'})
        total.append({'param': username})
        total.append({'validation': 'not_used'})

        raw_node = []
        raw_node.append({"status": "Fail",
                         "reason": "{}".format(e),
                         # "traceback": 1})
                         "traceback": traceback_text})
        total.append({"raw": raw_node})
    return total


def output(data):
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    username = sys.argv[1]
    result = t_keybase(username, "initial")
    output(result)
