#!/usr/bin/env python

import json
import sys

import requests
from bs4 import BeautifulSoup

from celery.utils.log import get_task_logger

from celery_app import celery


logger = get_task_logger(__name__)


@celery.task
def t_skype(email, from_m="Initial"):
    """Task of Celery that get info from skype"""

    url = "https://webresolver.nl/ajax/tools/email2skype"
    data = {"string": email, "action": "PostData"}
    headers = {
        "Referer": "https://webresolver.nl/tools/email_to_skype",
        "X-Requested-With": "XMLHttpRequest",
    }

    try:
        response = requests.get(
            "https://webresolver.nl/tools/email_to_skype", timeout=30
        )
        soup = BeautifulSoup(response.content, "html.parser")

        cookies = dict(response.cookies)

        r = requests.post(url, data=data, headers=headers, cookies=cookies, timeout=30)
        soup = BeautifulSoup(r.content, "html.parser")

        results = str(soup.div).replace("</div>", "").split("<br/>")[1:]

        if results != ["An error occoured!"] and results != [
            "There were no Skype usernames found with this email."
        ]:
            raw_node = []
            for result in results:
                raw_node.append({"skype": result})
        else:
            raw_node = {"status": "Not found"}
    except Exception:
        raw_node = {"status": "fail"}

    # Total
    total = []
    total.append({"module": "skype"})
    total.append({"param": email})
    # Evaluates the module that executed the task and set validation
    if from_m == "Initial":
        total.append({"validation": "no"})
    else:
        total.append({"validation": "soft"})

    # Graphic Array
    graphic = []

    # Profile Array
    profile = []

    # Timeline Array
    timeline = []

    # Gather Array
    gather = []

    link = "Skype"
    gather_item = {
        "name-node": "Skype",
        "title": "Skype",
        "subtitle": "",
        "icon": "fab fa-skype",
        "link": link,
    }
    gather.append(gather_item)

    if "status" not in raw_node:
        # Gather Array
        social = []

        gather_item = {
            "name-node": "SkypeUsername",
            "title": "Username",
            "subtitle": raw_node[0]["skype"],
            "icon": "fas fa-user",
            "link": link,
        }
        gather.append(gather_item)

        social_item = {
            "name": "Skype",
            "url": raw_node[0]["skype"],
            "source": "webresolver.nl",
            "icon": "fab fa-skype",
            "username": raw_node[0]["skype"],
        }
        social.append(social_item)
        profile.append({"social": social})
        profile_item = {"username": raw_node[0]["skype"]}
        profile.append(profile_item)

    graphic.append({"skype": gather})
    total.append({"raw": raw_node})
    total.append({"graphic": graphic})
    total.append({"profile": profile})
    total.append({"timeline": timeline})

    return total


def output(data):
    print(" ")
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    username = sys.argv[1]
    result = t_skype(username)
    output(result)
