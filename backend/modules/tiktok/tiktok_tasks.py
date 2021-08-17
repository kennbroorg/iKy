#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import time
import sys
import traceback
import json
import requests
from bs4 import BeautifulSoup
import random

try:
    from factories._celery import create_celery
    from factories.application import create_application
    from factories.iKy_functions import analize_rrss
    from celery.utils.log import get_task_logger
    celery = create_celery(create_application())
except ImportError:
    # This is to test the module individually, and I know that is piece of shit
    sys.path.append('../../')
    from factories._celery import create_celery
    from factories.application import create_application
    from factories.iKy_functions import analize_rrss
    from celery.utils.log import get_task_logger
    celery = create_celery(create_application())


from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

logger = get_task_logger(__name__)


def p_tiktok(username, from_m="Initial"):
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

    url = "https://www.tiktok.com/@%s" % username
    req = requests.get(url, headers={'User-Agent': random.choice(user_agents)})
    # soup = BeautifulSoup(req.text, "html.parser")
    print(req.text)

    try:

        # r = requests.get(url, headers=headers)
        if(req.status_code == 200 and req.text):
            soup = BeautifulSoup(req.text, 'html.parser')
            data_j = soup.find(id="__NEXT_DATA__").string
            data = json.loads(data_j)
            user_info = data['props']['pageProps']['userInfo']

            unique_id = user_info['user']['id']
            nickname = user_info['user']['nickname']
            avatar = user_info['user']['avatarLarger']
            signature = user_info['user']['signature']
            verified = user_info['user']['verified']
            secret = user_info['user']['secret']
            open_favorite = user_info['user']['openFavorite']
            following_count = user_info['stats']['followingCount']
            follower_count = user_info['stats']['followerCount']
            video_count = user_info['stats']['videoCount']
            digg_count = user_info['stats']['diggCount']
            heart_count = user_info['stats']['heartCount']
        elif("find this account" in req.text):
            raise RuntimeError('Tiktok user don\'t exist') 
        else:
            raise RuntimeError('Tiktok module don\'t work') 

        # Raw Array
        raw_node = {"Profile": user_info}

    except Exception:
        if("find this account" in req.text):
            raise RuntimeError('Tiktok user don\'t exist') 
        else:
            raise RuntimeError('Tiktok module don\'t work') 

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
    presence = []

    # Timeline Array
    timeline = []
    tasks = []

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
                       "subtitle": nickname,
                       "icon": "fas fa-user",
                       "link": link}
        gather.append(gather_item)
        profile_item = {'name': nickname}
        profile.append(profile_item)

        gather_item = {"name-node": "TiktokVideos", "title": "Videos",
                       "subtitle": video_count,
                       "icon": "fas fa-film", "link": link}
        gather.append(gather_item)

        gather_item = {"name-node": "TiktokFollowers", "title": "Followers",
                       "subtitle": follower_count,
                       "icon": "fas fa-users", "link": link}
        gather.append(gather_item)

        gather_item = {"name-node": "TiktokFollowing", "title": "Following",
                       "subtitle": following_count,
                       "icon": "fas fa-users", "link": link}
        gather.append(gather_item)

        gather_item = {"name-node": "TiktokAvatar", "title": "Avatar",
                       "picture": avatar,
                       "subtitle": "",
                       "link": link}
        gather.append(gather_item)
        profile_item = {'photos': [{"picture": avatar,
                                    "title": "Tiktok"}]}
        profile.append(profile_item)

        # gather_item = {"name-node": "TikTokSignature",
        #                "title": "Name",
        #                "subtitle": signature,
        #                "icon": "fas fa-signature",
        #                "link": link}
        # gather.append(gather_item)

        gather_item = {"name-node": "TikTokId",
                       "title": "Name",
                       "subtitle": unique_id,
                       "icon": "fas fa-id-card",
                       "link": link}
        gather.append(gather_item)

        gather_item = {"name-node": "TiktokBio", "title": "Bio",
                       "subtitle": signature,
                       "icon": "fas fa-heartbeat",
                       "link": link}
        gather.append(gather_item)
        profile.append({'bio': signature})
        analyze = analize_rrss(signature)
        for item in analyze:
            if(item == 'url'):
                for i in analyze['url']:
                    profile.append(i)
            if(item == 'email'):
                for i in analyze['email']:
                    profile.append(i)
            if(item == 'tasks'):
                for i in analyze['tasks']:
                    tasks.append(i)

        gather_item = {"name-node": "TiktokURL", "title": "URL",
                       "subtitle": url,
                       "icon": "fas fa-code",
                       "link": link}
        gather.append(gather_item)

        gather_item = {"name-node": "TiktokUsername", "title": "Username",
                       "subtitle": username,
                       "icon": "fas fa-user",
                       "link": link}
        gather.append(gather_item)

        gather_item = {"name-node": "TiktokVerified",
                       "title": "Verified Account",
                       "subtitle": verified,
                       "icon": "fas fa-certificate",
                       "link": link}
        gather.append(gather_item)

        gather_item = {"name-node": "TiktokHeart",
                       "title": "Hearts",
                       "subtitle": heart_count,
                       "icon": "fas fa-heart",
                       "link": link}
        gather.append(gather_item)

        gather_item = {"name-node": "TiktokDigg",
                       "title": "Digg",
                       "subtitle": digg_count,
                       "icon": "fas fa-thumbs-up",
                       "link": link}
        gather.append(gather_item)

        social_item = {"name": "tiktok",
                       "url": url,
                       "source": "TikTok",
                       "icon": "fas fa-play-circle",
                       "username": username}
        social.append(social_item)
        profile.append({"social": social})
        profile_item = {"username": username}
        profile.append(profile_item)

        presence.append({"name": "tiktok",
                         "children": [
                             {"name": "followers", 
                              "value": follower_count},
                             {"name": "following", 
                              "value": following_count},
                         ]})
        profile.append({'presence': presence})

    graphic.append({'tiktok': gather})
    total.append({'raw': raw_node})
    total.append({'graphic': graphic})
    total.append({'profile': profile})
    total.append({'timeline': timeline})
    total.append({'tasks': tasks})

    return total


@celery.task
def t_tiktok(user):
    # Variable principal
    total = []
    # Take initial time
    tic = time.perf_counter()

    # try execution principal function
    try:
        total = p_tiktok(user)
    # Error handle
    except Exception as e:
        # Error description
        traceback.print_exc()
        traceback_text = traceback.format_exc()
        code = 10
        if ('Tiktok user don\'t exist' in traceback_text):
            code = 5

        # Set module name in JSON format
        total.append({"module": "tiktok"})
        total.append({"param": user})
        total.append({"validation": "null"})

        # Set status code and reason
        status = []
        status.append(
            {
                "code": code,
                "reason": "{}".format(e),
                "traceback": traceback_text,
            }
        )
        total.append({"raw": status})

    # Take final time
    toc = time.perf_counter()
    # Show process time
    logger.info(f"Tiktok - Response in {toc - tic:0.4f} seconds")

    return total


def output(data):
    print(json.dumps(data, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    username = sys.argv[1]
    result = t_tiktok(username)
    output(result)
