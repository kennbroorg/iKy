#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import os
import sys
import json
import requests
from bs4 import BeautifulSoup
from datetime import date
import random
import time
import traceback


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


# from requests.packages.urllib3.exceptions import InsecureRequestWarning
# requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

logger = get_task_logger(__name__)


def p_tinder(username, from_m="Initial"):
    """Task of Celery that get info from tinder"""

    # Code to develop the frontend without burning APIs
    cd = os.getcwd()
    td = os.path.join(cd, "outputs")
    output = "output-tinder.json"
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

    url = "https://gotinder.com/@%s" % username
    req = requests.get(url, headers={'User-Agent': random.choice(user_agents)})
    soup = BeautifulSoup(req.content, "lxml")

    if soup.find(id='card-container'):
        raw_node = { 'name': str(soup.find(id='name').text),
                     'age': int(str(soup.find(id='age').text.encode('utf-8'))[10:13]),
                     'picture': str(soup.find(id='user-photo').get('src')),
                     'teaser': str(soup.find(id='teaser').text.encode('ascii', 'ignore')),
                   }
    else:
        raise Exception("iKy - User not found")

    # Total
    total = []
    total.append({'module': 'tinder'})
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

    link = "Tinder"
    gather_item = {"name-node": "Tinder", "title": "Tinder",
                   "subtitle": "", "icon": "fas fa-fire",
                   "link": link}
    gather.append(gather_item)

    if ('status' not in raw_node):
        actual_year = date.today().year

        # Gather Array
        social = []

        gather_item = {"name-node": "Tindername", "title": "Name",
                       "subtitle": raw_node["name"],
                       "icon": "fas fa-user",
                       "link": link}
        gather.append(gather_item)
        profile_item = {'name': raw_node["name"]}
        profile.append(profile_item)

        gather_item = {"name-node": "TinderAge", "title": "Age",
                       "subtitle": raw_node["age"],
                       "icon": "fas fa-birthday-cake", "link": link}
        gather.append(gather_item)
        profile_item = {'age': raw_node["age"]}
        profile.append(profile_item)

        gather_item = {"name-node": "TinderYear", "title": "Year of birth",
                       "subtitle": actual_year - raw_node["age"],
                       "icon": "fas fa-calendar-check", "link": link}
        gather.append(gather_item)
        timeline.append({'action': 'Year of birth',
                         'date': actual_year - raw_node['age'],
                         'desc': "Approximate date of birth deducted from year old reported in Tinder"})

        gather_item = {"name-node": "TinderPic", "title": "Avatar",
                       "picture": raw_node["picture"],
                       "subtitle": "",
                       "link": link}
        gather.append(gather_item)
        profile_item = {'photos': [{"picture": raw_node["picture"],
                                    "title": "Tinder"}]}
        profile.append(profile_item)

        gather_item = {"name-node": "TinderBio", "title": "Bio",
                       "subtitle": raw_node["teaser"],
                       "icon": "fas fa-heartbeat",
                       "link": link}
        gather.append(gather_item)

        gather_item = {"name-node": "TinderURL", "title": "URL",
                       "subtitle": url,
                       "icon": "fas fa-code",
                       "link": link}
        gather.append(gather_item)

        gather_item = {"name-node": "TinderUsername", "title": "Username",
                       "subtitle": username,
                       "icon": "fas fa-user",
                       "link": link}
        gather.append(gather_item)

        social_item = {"name": "Tinder",
                       "url": url,
                       "source": "Tinder",
                       "icon": "fas fa-fire",
                       "username": username}
        social.append(social_item)
        profile.append({"social": social})
        profile_item = {"username": username}
        profile.append(profile_item)

    graphic.append({'tinder': gather})
    total.append({'raw': raw_node})
    total.append({'graphic': graphic})
    total.append({'profile': profile})
    total.append({'timeline': timeline})

    return total


@celery.task
def t_tinder(username, from_m="Initial"):
    total = []
    tic = time.perf_counter()
    try:
        total = p_tinder(username)
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
        total.append({'module': 'tinder'})
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
    logger.info(f"Tinder - Response in {toc - tic:0.4f} seconds")

    return total


def output(data):
    print(" ")
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    username = sys.argv[1]
    result = t_tinder(username)
    output(result)
