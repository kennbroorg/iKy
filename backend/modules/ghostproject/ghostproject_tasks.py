#!/usr/bin/env python

import json
import sys

import cloudscraper
import requests

from celery.utils.log import get_task_logger

from celery_app import celery

logger = get_task_logger(__name__)


@celery.task
def t_ghostproject(username):
    """Task of Celery that gets info from GhostProject"""

    GHOSTPROJECT_URL = "https://ghostproject.fr"

    cookies = dict(requests.get(GHOSTPROJECT_URL, timeout=30).cookies)
    # req = requests.post(GHOSTPROJECT_URL + "/search.php",
    #                     data={'param': username},
    #                     cookies=cookies)

    scraper = cloudscraper.create_scraper()
    req = scraper.post(
        GHOSTPROJECT_URL + "/x000x1337.php", data={"param": username}, cookies=cookies
    )

    print(req.content)
    total = []
    total.append({"module": "ghostproject"})
    total.append({"param": username})
    total.append({"validation": "hard"})
    total.append({"leaks": parse_response(req)})

    return total


def parse_response(request):
    try:
        sanitized_array = filter(leak_filter, request.json().split("\n"))
    except ValueError:
        sanitized_array = []

    leaks = []
    for r in sanitized_array:
        splitted = r.split(":")
        if len(splitted) == 2:
            leaks.append({"email": splitted[0], "password": splitted[1]})

    return leaks


def leak_filter(x):
    return (
        x != "" and "<b>Search Time: " not in x and "Error: No results found" not in x
    )


def output(data):
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    username = sys.argv[1]
    result = t_ghostproject(username)
    output(result)
