#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import os
import sys
import json
import requests
import time
import traceback
import re
from bs4 import BeautifulSoup
from w3lib.html import remove_tags

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

# from requests.packages.urllib3.exceptions import InsecureRequestWarning
# requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

logger = get_task_logger(__name__)


def username_search(username):
    url = f"https://mastodon.social/api/v2/search?q={username}"
    response = requests.request("GET", url)
    data = json.loads(response.text)

    if response.text == ('{"accounts":[],"statuses":[],"hashtags":[]}'):
        raise Exception(f'iKy - Username: {username} NOT found using the Mastodon API!')

    data = filter(
        lambda x: x.get("username").lower() == username.lower(), data["accounts"]
    )

    user_data = list(data)
    return user_data


def p_mastodon(username, from_m):
    """ Task of Celery that get info from mastodon """

    # Code to develop the frontend without burning APIs
    cd = os.getcwd()
    td = os.path.join(cd, "outputs")
    output = "output-mastodon.json"
    file_path = os.path.join(td, output)

    if os.path.exists(file_path):
        logger.warning(f"Developer frontend mode - {file_path}")
        try:
            with open(file_path, 'r') as file:
                data = json.load(file)
            return data
        except json.JSONDecodeError:
            logger.error(f"Developer mode ERROR")

    # Code
    # Evaluate param
    match = re.search(r'[@]?(\w+)[@]?([a-zA-Z0-9_\-\.]+)?', username)
    if (match):
        try:
            user = match.groups()[0]
        except Exception:
            raise Exception('iKy - Invalid input parameters')
        try:
            server = match.groups()[1]
        except Exception:
            server = ''
    else:
        raise Exception('iKy - Invalid input parameters')

    print(f"User : {user}")
    print(f"Server : {server}")

    total = []
    user_data = []
    # Only username
    if (server == '' or server == None):
        user_data = username_search(user)
        if (len(user_data) == 1):
        # - One user
            total = one_user(user, user_data)
        else:
            # - Several users
            total = several_user(user, user_data, server)
    else: 
    # Username and server
        found = False
        user_data = username_search(user)
        for info in user_data:
            match = re.search(r'[@]?(\w+)[@]?([a-zA-Z0-9_\-\.]+)?', info['acct'])
            if (match):
                user_masto = match.groups()[0]
                try:
                    server_masto = match.groups()[1]
                except Exception:
                    server_masto = ''
            else:
                user_masto = server_masto = ''
            # Search user
            if (user == user_masto and server == server_masto):
                found = True
                break
        
        if (found):
            total = one_user(username, [info])
        else:
            raise Exception(f'iKy - Username: {user} NOT found using the Mastodon API!')

    return total

def several_user(username, user_data, server):
    total = []
    graphic = []
    list_user = []

    # print(user_data)

    for info in user_data:
        match = re.search(r'[@]?(\w+)[@]?([a-zA-Z0-9_\-\.]+)?', info['acct'])
        if (match):
            user_masto = match.groups()[0]
            try:
                server_masto = match.groups()[1]
            except Exception:
                server_masto = ''
        else:
            user_masto = server_masto = ''
        list_user.append(
            {
                "account": info['acct'],
                "username": user_masto,
                "server": server_masto,
                "avatar": info['avatar'],
                "followers": info['followers_count'],
                "following": info['following_count'],
                "toots": info['statuses_count'],
                "bios": remove_tags(info['note']),
            }
        )

    total.append({'module': 'mastodon'})
    total.append({'param': username})
    total.append({'validation': 'no'})
    total.append({'raw': user_data})
    graphic.append({'user': []})
    graphic.append({'social': []})
    graphic.append({'list': list_user})

    total.append({'graphic': graphic})

    total.append({'profile': []})
    total.append({'timeline': []})
    total.append({'tasks': []})

    return total

def one_user(username, user_data, server=''):

    info = user_data[0]
    print(f"INFO: {info}")

    # Icons
    font_list = fontawesome_cheat_5()
    # Total
    total = []
    total.append({'module': 'mastodon'})
    total.append({'param': username})
    total.append({'validation': 'no'})

    # Graphic Array
    graphic = []

    # Profile Array
    profile = []
    social_profile = []

    # Timeline Array
    timeline = []

    # Tasks Array
    tasks = []

    # Social Array
    social = []

    # Graph Array
    graph = []

    # Presence Array
    presence = []

    link_graph = "MastodonGraph"
    graph_item = {"name-node": "MastodonGraph", "title": "MastodonGraphs",
                    "subtitle": "", "icon": "fab fa-mastodon", "link": link_graph}
    graph.append(graph_item)

    link_social = "MastodonSocial"
    social_item = {"name-node": "MastodonSocial", "title": "MastodonSocial",
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
                    "subtitle": info['followers_count'],
                    "icon": "fas fa-users",
                    "link": link_graph}
    graph.append(graph_item)

    graph_item = {"name-node": "GraphFollowing",
                    "title": "Following",
                    "subtitle": info['following_count'],
                    "icon": "fas fa-users",
                    "link": link_graph}
    graph.append(graph_item)

    graph_item = {"name-node": "GraphPosts",
                    "title": "Toots",
                    "subtitle": info['statuses_count'],
                    "icon": "fas fa-tooth",
                    "link": link_graph}
    graph.append(graph_item)

    profile_item = {'name': info['display_name']}
    profile.append(profile_item)

    graph_item = {"name-node": "GraphName", 
                    "title": "Name",
                    "subtitle": info['display_name'],
                    "icon": "fas fa-signature",
                    "link": link_graph}
    graph.append(graph_item)

    if (info["locked"]):
        gather_item = {"name-node": "MastoLocked", "title": "Locked?",
                    "subtitle": "User Locked",
                    "icon": "fab fa-lock",
                    "link": link_graph}
    else:
        gather_item = {"name-node": "MastoLocked", "title": "Locked?",
                    "subtitle": "User NOT Locked",
                    "icon": "fas fa-lock-open",
                    "link": link_graph}
    graph.append(gather_item)

    if (info['group']):
        gather_item = {"name-node": "MastoLocked", "title": "User Type",
                    "subtitle": "Robot",
                    "icon": "fas fa-robot",
                    "link": link_graph}
    else:
        if (not info["bot"]):
            gather_item = {"name-node": "MastoBot", "title": "User Type",
                        "subtitle": "Human",
                        "icon": "fas fa-user",
                        "link": link_graph}
        else:
            gather_item = {"name-node": "MastoGroup", "title": "User Type",
                        "subtitle": "Group",
                        "icon": "fas fa-users",
                        "link": link_graph}
    graph.append(gather_item)

    profile_item = {'bio': remove_tags(info['note'])}
    profile.append(profile_item)

    analyze = analize_rrss(info['note'])
    for item in analyze:
        if(item == 'url'):
            for i in analyze['url']:
                profile.append(i)
        if(item == 'tasks'):
            for i in analyze['tasks']:
                tasks.append(i)

    profile_item = {'photos': [{
        "picture": info['avatar'],
        "title": "Mastodon"}]}
    profile.append(profile_item)

    graph_item = {"name-node": "MastodonAvatar", "title": "Avatar",
                "picture": info['avatar'],
                "subtitle": "",
                "link": link_graph}
    graph.append(graph_item)

    timeline_item = {"action": "Mastodon: Create Account",
                        "date": info['created_at'][:10], "icon": "fab fa-mastodon"}
    timeline.append(timeline_item)

    graph_item = {"name-node": "GraphJoin", 
                    "title": "Join Date",
                    "subtitle": info['created_at'][:10],
                    "icon": "fas fa-calendar-check",
                    "link": link_graph}
    graph.append(graph_item)

    #             mtime = time.strftime('%Y/%m/%d %H:%M:%S',
    #                                   time.gmtime(raw.get("basics", "")
    #                                               .get("mtime")))
    timeline_item = {"action": "Mastodon : Last toot",
                        "date": info['last_status_at'], "icon": "fab fa-mastodon"}
    timeline.append(timeline_item)

    fields = []
    for field in info.get("fields", []):
        name = field.get("name")
        value = field.get("value")
        print(f"Name: {name} - Value: {value}")

        if value and '</' not in value:
            continue                                                 

        soup = BeautifulSoup(value, "html.parser")
        a = soup.find("a")
        if a:
            fields.append({name: a.get("href")})
            analyze = analize_rrss(a.get("href"))
            for item in analyze:
                if(item == 'url'):
                    for i in analyze['url']:
                        profile.append(i)
                if(item == 'tasks'):
                    for i in analyze['tasks']:
                        tasks.append(i)

                        fa_icon = search_icon_5(i['module'], font_list)
                        if (fa_icon is None):
                            fa_icon = search_icon_5("question", font_list)

                        social_item = {"name-node": "MastoSocial" + name, 
                                    "title": name,
                                    "subtitle": i['param'], 
                                    "icon": fa_icon,
                                    "link": link_social}
                        social.append(social_item)

                        social_profile_item = {"name": name,
                                                "username": i['param'],
                                                "Source": "Mastodon",
                                                "icon": fa_icon,
                                                "url": a.get("href")}
                        social_profile.append(social_profile_item)
        else:
            continue

    social_profile_item = {"name": "mastodon",
                            "username": username,
                            "Source": "Mastodon",
                            "icon": "fab fa-mastodon",
                            "url": info['url']}
    social_profile.append(social_profile_item)

    profile.append({'social': social_profile})
    
    presence.append({"name": "mastodon",
                    "children": [
                        {"name": "followers", 
                        "value": info['followers_count']},
                        {"name": "following", 
                        "value": info['following_count']},
                    ]})
    profile.append({'presence': presence})

    total.append({'raw': info})
    graphic.append({'user': graph})
    graphic.append({'social': social})
    graphic.append({'list': []})

    total.append({'graphic': graphic})

    total.append({'profile': profile})
    total.append({'timeline': timeline})
    total.append({'tasks': tasks})

    return total


@celery.task
def t_mastodon(username, from_m="Initial"):
    total = []
    tic = time.perf_counter()
    try:
        total = p_mastodon(username, from_m)
    except Exception as e:
        # Check internal error
        if str(e).startswith("iKy - "):
            reason = str(e)[len("iKy - "):]
            status = "Warning"
        else:
            reason = str(e)
            status = "Fail"

        traceback.print_exc()
        traceback_text = traceback.format_exc()
        total.append({'module': 'mastodon'})
        total.append({'param': username})
        total.append({'validation': 'not_used'})

        raw_node = []
        raw_node.append({"status": status,
                         # "reason": "{}".format(e),
                         "reason": reason,
                         "traceback": traceback_text})
        total.append({"raw": raw_node})

    # Take final time
    toc = time.perf_counter()
    # Show process time
    logger.info(f"Mastodon - Response in {toc - tic:0.4f} seconds")

    return total


def output(data):
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    username = sys.argv[1]
    result = t_mastodon(username, "initial")
    output(result)
