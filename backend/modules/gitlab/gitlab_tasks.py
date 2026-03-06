#!/usr/bin/env python

# import time
import json
import sys
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

from celery.utils.log import get_task_logger

from celery_app import celery

logger = get_task_logger(__name__)


@celery.task
def t_gitlab(username):
    gitlabdetails = []
    url = "https://gitlab.com/" + quote(username, safe="")
    if requests.head(url, timeout=30).status_code == 200:
        response = requests.get(url, timeout=30)
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

    total = []
    total.append({"module": "gitlab"})
    total.append({"param": username})
    total.append({"validation": "no"})
    total.append({"raw": gitlabdetails})
    total.append({"graphic": []})
    total.append({"profile": []})
    total.append({"timeline": []})
    total.append({"tasks": []})

    return total


def output(data):
    print(json.dumps(data, indent=4, separators=(",", ": ")))


if __name__ == "__main__":
    email = sys.argv[1]
    result = t_gitlab(email)
    output(result)
