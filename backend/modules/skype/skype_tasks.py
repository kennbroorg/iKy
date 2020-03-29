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
def t_skype(email, from_m="Initial"):
    """Task of Celery that get info from skype"""

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

    url="https://webresolver.nl/ajax/tools/email2skype"
    data = {"string": email,"action": "PostData"}
    headers={'Referer':'https://webresolver.nl/tools/email_to_skype','X-Requested-With':'XMLHttpRequest'}

    try:
        response=requests.get("https://webresolver.nl/tools/email_to_skype")
        soup = BeautifulSoup(response.content, 'html.parser')

        cookies = dict(response.cookies)

        r = requests.post(url,data=data,headers=headers,cookies=cookies)
        soup = BeautifulSoup(r.content, 'html.parser')

        results = str(soup.div).replace('</div>', '').split('<br/>')[1:]

        if(results != ['An error occoured!'] and results !=['There were no Skype usernames found with this email.']):
            raw_node = []
            for result in results:
                raw_node.append({"skype": result})
        else:
            raw_node = { 'status': 'Not found'}
    except:
        raw_node = { 'status': 'fail'}

    # Total
    total = []
    total.append({'module': 'skype'})
    total.append({'param': email})
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

    link = "Skype"
    gather_item = {"name-node": "Skype", "title": "Skype",
                   "subtitle": "", "icon": "fab fa-skype",
                   "link": link}
    gather.append(gather_item)

    if ('status' not in raw_node):
        # Gather Array
        social = []

        gather_item = {"name-node": "SkypeUsername", "title": "Username",
                       "subtitle": raw_node[0]["skype"],
                       "icon": "fas fa-user",
                       "link": link}
        gather.append(gather_item)

        social_item = {"name": "Skype",
                       "url": raw_node[0]["skype"],
                       "source": "webresolver.nl",
                       "icon": "fab fa-skype",
                       "username": raw_node[0]["skype"]}
        social.append(social_item)
        profile.append({"social": social})
        profile_item = {"username": raw_node[0]["skype"]}
        profile.append(profile_item)

    graphic.append({'skype': gather})
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
    result = t_skype(username)
    output(result)
