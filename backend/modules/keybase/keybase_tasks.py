#!/usr/bin/env python
# -*- coding: utf-8 -*-
from factories._celery import create_celery
from factories.application import create_application
celery = create_celery(create_application())
import time

import sys
import requests
import json

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

 
@celery.task
def t_keybase(username):
    # time.sleep(50)
    url = "https://keybase.io/_/api/1.0/user/lookup.json?usernames=%s" %username
    req = requests.get(url)
    data = json.loads(req.text) 
    if data['them'][0] is not None:
        dict_them = data['them'][0]
        return dict_them
    else:
        dict_them = []
        return dict_them


def output(data):
    print json.dumps(data, indent=4, separators=(',', ': '))


if __name__ == "__main__":
    try:
        username = sys.argv[1]
        result = t_keybase(username)
        output(result)
    except Exception as e:
        print e
        print "Please provide a username as argument"

