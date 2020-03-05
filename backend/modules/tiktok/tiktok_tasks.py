#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import sys
import json
import requests
from bs4 import BeautifulSoup
import random

try:
    from factories._celery import create_celery
    from factories.application import create_application
    from celery.utils.log import get_task_logger
    celery = create_celery(create_application())
except ImportError:
    # This is to test the module individually, and I know that is piece of shit
    sys.path.append('../../')
    from factories._celery import create_celery
    from factories.application import create_application
    from celery.utils.log import get_task_logger
    celery = create_celery(create_application())


from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

logger = get_task_logger(__name__)


@celery.task
def t_tiktok(username, from_m="Initial"):
    """ Task of Celery that get info from tiktok"""

    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
        'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
        'Mozilla/5.0 (Windows NT 5.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
        'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36',
        'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36',
        'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
        'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
        'Mozilla/4.0 (compatible; MSIE 9.0; Windows NT 6.1)',
        'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko',
        'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0)',
        'Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko',
        'Mozilla/5.0 (Windows NT 6.2; WOW64; Trident/7.0; rv:11.0) like Gecko',
        'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko',
        'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.0; Trident/5.0)',
        'Mozilla/5.0 (Windows NT 6.3; WOW64; Trident/7.0; rv:11.0) like Gecko',
        'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)',
        'Mozilla/5.0 (Windows NT 6.1; Win64; x64; Trident/7.0; rv:11.0) like Gecko',
        'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0)',
        'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)',
        'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729)'
    ]

    url = "https://www.tiktok.com/@%s/" % username
    req = requests.get(url, headers={'User-Agent': random.choice(user_agents)})
    soup = BeautifulSoup(req.text, "html.parser")

    try:
        content = soup.find_all("script", attrs={"type": "application/json",
                                                 "crossorigin": "anonymous"})
        content = json.loads(content[0].contents[0])
        profile_data = {"UserID": content["props"]["pageProps"]["userData"]["userId"],
            "username": content["props"]["pageProps"]["userData"]["uniqueId"],
            "nickname": content["props"]["pageProps"]["userData"]["nickName"],
            "bio": content["props"]["pageProps"]["userData"]["signature"],
            "profileImage": content["props"]["pageProps"]["userData"]["coversMedium"][0],
            "following": content["props"]["pageProps"]["userData"]["following"],
            "fans": content["props"]["pageProps"]["userData"]["fans"],
            "hearts": content["props"]["pageProps"]["userData"]["heart"],
            "videos": content["props"]["pageProps"]["userData"]["video"],
            "verified": content["props"]["pageProps"]["userData"]["verified"]}

        # Raw Array
        raw_node = {"Profile": profile_data}

    except:
        raw_node = {"status": "Fail"}

    # Total
    total = []
    total.append({'module': 'tiktok'})
    total.append({'param': username})
    # Evaluates the module that executed the task and set validation
    if (from_m == 'Initial'):
        total.append({'validation': 'no'})
    else:
        total.append({'validation': 'soft'})

    # Graphic Array
    graphic = []

    # Profile Array
    profile = []

    # Timeline Array
    timeline = []

    # Gather Array
    gather = []

    link = "Tiktok"
    gather_item = {"name-node": "Tiktok", "title": "Tiktok",
                   "subtitle": "", "icon": "fas fa-play-circle",
                   "link": link}
    gather.append(gather_item)

    if ('status' not in raw_node):
        # Gather Array
        social = []

        gather_item = {"name-node": "Tiktokname", "title": "Name",
                       "subtitle": profile_data["nickname"],
                       "icon": "fas fa-user",
                       "link": link}
        gather.append(gather_item)
        profile_item = {'name': profile_data["nickname"]}
        profile.append(profile_item)

        gather_item = {"name-node": "TiktokVideos", "title": "Videos",
                       "subtitle": profile_data["videos"],
                       "icon": "fas fa-film", "link": link}
        gather.append(gather_item)

        gather_item = {"name-node": "TiktokFollowers", "title": "Followers",
                       "subtitle": profile_data["fans"],
                       "icon": "fas fa-users", "link": link}
        gather.append(gather_item)

        gather_item = {"name-node": "TiktokFollowing", "title": "Following",
                       "subtitle": profile_data["following"],
                       "icon": "fas fa-users", "link": link}
        gather.append(gather_item)

        gather_item = {"name-node": "TiktokAvatar", "title": "Avatar",
                       "picture": profile_data["profileImage"],
                       "subtitle": "",
                       "link": link}
        gather.append(gather_item)
        profile_item = {'photos': [{"picture": profile_data["profileImage"],
                                    "title": "Tiktok"}]}
        profile.append(profile_item)

        gather_item = {"name-node": "TiktokBio", "title": "Bio",
                       "subtitle": profile_data["bio"],
                       "icon": "fas fa-heartbeat",
                       "link": link}
        gather.append(gather_item)

        gather_item = {"name-node": "TiktokURL", "title": "URL",
                       "subtitle": url,
                       "icon": "fas fa-code",
                       "link": link}
        gather.append(gather_item)

        gather_item = {"name-node": "TiktokUsername", "title": "Username",
                       "subtitle": profile_data["username"],
                       "icon": "fas fa-user",
                       "link": link}
        gather.append(gather_item)

        gather_item = {"name-node": "TiktokVerified",
                       "title": "Verified Account",
                       "subtitle": profile_data["verified"],
                       "icon": "fas fa-certificate",
                       "link": link}
        gather.append(gather_item)

        gather_item = {"name-node": "TiktokHeart",
                       "title": "Hearts",
                       "subtitle": profile_data["hearts"],
                       "icon": "fas fa-heart",
                       "link": link}
        gather.append(gather_item)

        social_item = {"name": "tiktok",
                       "url": url,
                       "username": profile_data["username"]}
        social.append(social_item)
        profile.append({"social": social})
        profile_item = {"username": profile_data["username"]}
        profile.append(profile_item)

    graphic.append({'tiktok': gather})
    total.append({'raw': raw_node})
    total.append({'graphic': graphic})
    total.append({'profile': profile})
    total.append({'timeline': timeline})

    return total


def output(data):
    print(" ")
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    username = sys.argv[1]
    result = t_tiktok(username)
    output(result)
