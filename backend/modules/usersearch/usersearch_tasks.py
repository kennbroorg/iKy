#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import json
import requests
from bs4 import BeautifulSoup

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
def t_usersearch(username):
    data = {"username": username}
    req = requests.post("https://usersearch.org/results_normal.php",
                        data=data, verify=False)
    soup = BeautifulSoup(req.content, "lxml")
    atag = soup.findAll("a", {"class": "pretty-button results-button"})
    profiles = []
    for at in atag:
        if at.text == "View Profile":
            profiles.append(at["href"])
    return profiles


def output(data):
    print(json.dumps(data, indent=4, separators=(',', ': ')))


if __name__ == "__main__":
    email = sys.argv[1]
    result = t_usersearch(email)
    output(result)
