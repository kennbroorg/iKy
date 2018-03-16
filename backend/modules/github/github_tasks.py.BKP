#!/usr/bin/env python
# -*- encoding: utf-8 -*-
from factories._celery import create_celery
from factories.application import create_application
from celery.utils.log import get_task_logger
celery = create_celery(create_application())
import time

# @celery.task(name="tasks.simple_task")
# def simple_task(argument):
#     this = 0
#     for i in range(0,1000000):
#         this = i * i * i * i * i * i
#     print(argument)
# # -*- coding: utf-8 -*-

import sys
import json
import requests

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# try:
#     from celery_config import app
# except ImportError:
#     # This is to test the module individually
#     sys.path.append('../../')
#     from celery_config import app

logger = get_task_logger(__name__)

@celery.task
def t_github(username):
    logger.info('User detected: ' + username) # This message appears in Celery console
    req = requests.get("https://api.github.com/users/%s" % username)
    # TODO : Many things 
    # Use other API URLs
    time.sleep(20);
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
