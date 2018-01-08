#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import sys
import requests
import json
from bs4 import BeautifulSoup

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

try:
    from celery_config import app
except ImportError:
    # This is to test the module individually
    sys.path.append('../../')
    from celery_config import app


@app.task
def t_username(username):
    data = {"username": username}
    req = requests.post('https://usersearch.org/results_normal.php', data=data, verify=False)
    soup = BeautifulSoup(req.content, "lxml")
    atag = soup.findAll('a', {'class': 'pretty-button results-button'})
    profiles = []
    for at in atag:
        if at.text == "View Profile":
            profiles.append(at['href'])
    return profiles


def output(data):
    print json.dumps(data, indent=4, separators=(',', ': '))


if __name__ == "__main__":
    try:
        username = sys.argv[1]
        result = t_username(username)
        output(result)
    except Exception as e:
        print e
        print "Please provide a username as argument"
