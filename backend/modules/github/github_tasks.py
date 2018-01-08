#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import sys
import json
import requests

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

try:
    from celery_config import app
except ImportError:
    # This is to test the module individually
    sys.path.append('../../')
    from celery_config import app


@app.task
def t_github(username):
    req = requests.get("https://api.github.com/users/%s" % username)
    # TODO : Many things 
    # Use other API URLs
    return json.loads(req.content)


def output(data):
    print json.dumps(data, indent=4, separators=(',', ': '))


if __name__ == "__main__":
    try:
        username = sys.argv[1]
        result = t_github(username)
        output(result)
    except Exception as e:
        print e
        print "Please provide a username as argument"
