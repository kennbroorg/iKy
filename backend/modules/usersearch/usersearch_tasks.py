#!/usr/bin/env python

import json
import sys

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

logger = get_task_logger(__name__)


@celery.task
def t_usersearch(username):
    data = {"username": username}
    req = requests.post(
        "https://usersearch.org/results_normal.php", data=data, timeout=30
    )
    soup = BeautifulSoup(req.content, "lxml")
    atag = soup.findAll("a", {"class": "pretty-button results-button"})
    profiles = []
    for at in atag:
        if at.text == "View Profile":
            profiles.append(at["href"])
    return profiles


def output(data):
    print(json.dumps(data, indent=4, separators=(",", ": ")))


if __name__ == "__main__":
    email = sys.argv[1]
    result = t_usersearch(email)
    output(result)
