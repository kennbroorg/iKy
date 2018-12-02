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
def t_leaks(username):
    """ Task of Celery that get info from Have I Been Pwned """
    email_encoded = urllib.quote_plus(username)
    url = "https://haveibeenpwned.com/api/v2/breachedaccount/%s" \
          % (email_encoded)

    scraper = cfscrape.create_scraper()
    req = scraper.get(url)

    # Raw Array
    if (len(req.content) != 0):
        raw_node = json.loads(req.content)
    else:
        raw_node = []

    # Total
    total = []
    total.append({'module': 'leaks'})
    total.append({'param': username})
    total.append({'validation': 'hard'})

    # Graphic Array
    graphic = []

    # Profile Array
    # leaks : TODO : Social disable
    profile = []

    # Timeline Array
    timeline = []

    # Gather Array
    gather = []

    link = "Leaks"
    gather_item = {"name-node": "Leaks", "title": "Leaks",
                   "subtitle": "", "icon": u'\uf06a', "link": link}
    gather.append(gather_item)

    for leak in raw_node:
        gather_item = {"name-node": leak.get("Title", ""),
                       "title": leak.get("Title", ""),
                       "subtitle": "Breach Date: " + leak.get(
                           "BreachDate", ""),
                       "picture": leak.get("LogoPath", ""),
                       # "picture": "https://haveibeenpwned.com/Content/" +
                       # "Images/PwnedLogos/" + leak.get("Name", "") + "." +
                       # leak.get("LogoType", ""),
                       "link": link}
        gather.append(gather_item)
        timeline.append({"action": "Leak : " + leak.get("Title", ""),
                         "date": leak.get("BreachDate", ""),
                         "icon": "fa-exclamation-circle",
                         "desc": leak.get("Description", "")})

        # Leaks : TODO : Implement socialProfile disable
        # Leaks : TODO : The problem is the icon in frontend

    # Please, respect the order of items in the total array
    # Because the frontend depend of that (By now)
    total.append({'raw': raw_node})
    if (len(gather) != 1):
        graphic.append({'leaks': gather})
    total.append({'graphic': graphic})
    total.append({'profile': profile})
    total.append({'timeline': timeline})

    print(total)

    return total


def output(data):
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    username = sys.argv[1]
    result = t_leaks(username)
    output(result)
