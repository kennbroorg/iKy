#!/usr/bin/env python

# import time
import json
import sys
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

try:
    from celery.utils.log import get_task_logger
    from factories._celery import create_celery
    from factories.application import create_application

    celery = create_celery(create_application())
except ImportError:
    # This is to test the module individually, and I know that is piece of shit
    sys.path.append("../../")
    from celery.utils.log import get_task_logger
    from factories._celery import create_celery
    from factories.application import create_application

    celery = create_celery(create_application())

import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = get_task_logger(__name__)


@celery.task
def t_gitlab(username):
    gitlabdetails = []
    url = "https://gitlab.com/" + quote(username, safe="")
    if requests.head(url, verify=False).status_code == 200:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "lxml")
        handle = soup.find("span", {"class": "middle-dot-divider"})
        if handle:
            name = soup.find("div", {"class": "cover-title"})
            gitlabdetails.append("Name: " + name.text.strip())
            handle = soup.find("span", {"class": "middle-dot-divider"})
            mydivs = soup.findAll(
                "div", {"class": "profile-link-holder middle-dot-divider"}
            )
            for div in mydivs:
                q = div.find("a", href=True)
                if q:
                    gitlabdetails.append(q["href"].strip())
                elif div.find("i", {"class": "fa fa-map-marker"}):
                    gitlabdetails.append("Location:" + div.text.strip())
                elif div.find("i", {"class": "fa fa-briefcase"}):
                    gitlabdetails.append("Organisation: " + div.text.strip())

    return gitlabdetails


def output(data):
    print(json.dumps(data, indent=4, separators=(",", ": ")))


if __name__ == "__main__":
    email = sys.argv[1]
    result = t_gitlab(email)
    output(result)
