#!/usr/bin/env python

import json
import sys

import requests
from bs4 import BeautifulSoup

from celery.utils.log import get_task_logger

from celery_app import celery

logger = get_task_logger(__name__)


@celery.task
def t_usersearch(username):
    data = {"username": username}
    req = requests.post(
        "https://usersearch.org/results_normal.php", data=data, timeout=30
    )
    soup = BeautifulSoup(req.content, "lxml")
    atag = soup.findAll("a", {"class": "pretty-button results-button"})
    profiles = [at["href"] for at in atag if at.text == "View Profile"]

    total = []
    total.append({"module": "usersearch"})
    total.append({"param": username})
    total.append({"validation": "no"})
    total.append({"raw": profiles})
    total.append({"graphic": []})
    total.append({"profile": []})
    total.append({"timeline": []})
    total.append({"tasks": []})

    return total


def output(data):
    print(json.dumps(data, indent=4, separators=(",", ": ")))


if __name__ == "__main__":
    email = sys.argv[1]
    result = t_usersearch(email)
    output(result)
