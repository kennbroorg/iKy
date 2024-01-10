#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import os
import sys
import json
import requests
# import urllib
import cfscrape
import time
import traceback

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

# from requests.packages.urllib3.exceptions import InsecureRequestWarning
# requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

logger = get_task_logger(__name__)

# Compatibility code
# try:
#     # Python 2: "unicode" is built-in
#     unicode
# except NameError:
#     unicode = str

def p_leaks(email):
    """ Task of Celery that get info from Have I Been Pwned """

    # Code to develop the frontend without burning APIs
    cd = os.getcwd()
    td = os.path.join(cd, "outputs")
    output = "output-leaks.json"
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
    key = ""
    url = 'https://haveibeenpwned.com/api/v3/breachedaccount/{}'.format(email)
    key = api_keys_search('haveibeenpwned_key')

    if (not key):
        raise Exception("iKy - Missing or invalid Key")

    # For the future
    # scraper = cfscrape.create_scraper()
    # req = scraper.get(url)

    req = requests.get(url, headers={'User-Agent': 'iKy', 'hibp-api-key': key},
            params={'truncateResponse': 'false'}, timeout=10)

    # Raw Array
    if (req.status_code == 200):
        raw_node = json.loads(unicode(req.text))
    elif (req.status_code == 403):
        raise Exception("iKy - Missing or invalid Key")
    elif (req.status_code == 404):
        raise Exception("iKy - No leak found")
    elif (req.status_code == 503):
        raise Exception("iKy - Service blocked")
    else:
        raise Exception("iKy - API Error")

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


@celery.task
def t_leaks(email):
    total = []
    tic = time.perf_counter()
    try:
        total = p_leaks(email)
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
        total.append({'module': 'leaks'})
        total.append({'param': email})
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
    logger.info(f"leaks - Response in {toc - tic:0.4f} seconds")

    return total


def output(data):
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    username = sys.argv[1]
    result = t_leaks(username)
    output(result)
