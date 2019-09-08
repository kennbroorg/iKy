#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import sys
import json
import requests
import urllib
import cfscrape

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

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

logger = get_task_logger(__name__)

# Compatibility code
try:
    # Python 2: "unicode" is built-in
    unicode
except NameError:
    unicode = str

@celery.task
def t_leaks(email):
    """ Task of Celery that get info from Have I Been Pwned """

    key = ""
    url = 'https://haveibeenpwned.com/api/v3/breachedaccount/{}'.format(email)
    key = api_keys_search('haveibeenpwned_key')

    # For the future
    # scraper = cfscrape.create_scraper()
    # req = scraper.get(url)

    req = requests.get(url, headers={'User-Agent': 'iKy', 'hibp-api-key': key},
            params={'truncateResponse': 'false'}, timeout=10)

    # Raw Array
    if (req.status_code == 200):
        raw_node = json.loads(unicode(req.text))
    elif (req.status_code == 403):
        raw_node = [{"title": "KEY"}]
    elif (req.status_code == 404):
        raw_node = [{"title": "NOLEAK"}]
    elif (req.status_code == 503):
        raw_node = [{"title": "BLOCKED"}]
    else:
        raw_node = [{"title": "ERROR"}]

    # Total
    total = []
    total.append({'module': 'leaks'})
    total.append({'param': email})
    total.append({'validation': 'hard'})

    # Graphic Array
    graphic = []

    # Profile Array
    profile = []

    # Timeline Array
    timeline = []

    # Gather Array
    gather = []

    if (raw_node[0].get("title", "") == "NOLEAK") or (
            raw_node[0].get("title", "") == "BLOCKED") or (
            raw_node[0].get("title", "") == "KEY") or (
            raw_node[0].get("title", "") == "ERROR"):
        link = "Leaks"
        gather_item = {"name-node": "Leaks", "title": "Leaks",
                       "subtitle": "", "icon": "fas fa-unlock-alt",
                       "link": link}
        gather.append(gather_item)

    else:
        link = "Leaks"
        gather_item = {"name-node": "Leaks", "title": "Leaks",
                       "subtitle": "", "icon": "fas fa-unlock-alt",
                       "link": link}
        gather.append(gather_item)

        for leak in raw_node:
            gather_item = {"name-node": leak.get("Title", ""),
                           "title": leak.get("Title", ""),
                           "subtitle": "Breach Date: " + leak.get(
                               "BreachDate", ""),
                           "picture": leak.get("LogoPath", ""),
                           # "picture": "https://haveibeenpwned.com/Content/" +
                           #"Images/PwnedLogos/" + leak.get("Name", "") + "." +
                           # leak.get("LogoType", ""),
                           "link": link}
            gather.append(gather_item)
            timeline.append({"action": "Leak : " + leak.get("Title", ""),
                             "date": leak.get("BreachDate", ""),
                             "icon": "fa-exclamation-circle",
                             "desc": leak.get("Description", "")})

    # Please, respect the order of items in the total array
    # Because the frontend depend of that (By now)
    total.append({'raw': raw_node})
    # if (len(gather) != 1):
    #     graphic.append({'leaks': gather})
    graphic.append({'leaks': gather})
    total.append({'graphic': graphic})
    total.append({'profile': profile})
    total.append({'timeline': timeline})

    return total


def output(data):
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    username = sys.argv[1]
    result = t_leaks(username)
    output(result)
