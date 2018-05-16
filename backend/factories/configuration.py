# -*- encoding: utf-8 -*-

import os
# import ConfigParser
import json


def get_config():
    class Config:
        CELERY_BROKER_URL = 'redis://localhost:6379/0'
        CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
        CELERY_ACCEPT_CONTENT = ['json', 'yaml']
        CELERY_TASK_SERIALIZER = 'json'
        CELERY_RESULT_SERIALIZER = 'json'
        CELERY_IMPORTS = ('modules.keybase.keybase_tasks',
                          'modules.gitlab.gitlab_tasks',
                          'modules.twitter.twitter_tasks',
                          'modules.github.github_tasks',
                          'modules.fullcontact.fullcontact_tasks',
                          'modules.usersearch.usersearch_tasks')
    return Config


def api_keys_read():
    cur_dir = os.getcwd()
    api_keys_file = cur_dir + '/factories/apikeys.json'
    with open(api_keys_file, 'r') as f:
        items = json.load(f)
    return items


def api_keys_write(api_keys):
    cur_dir = os.getcwd()
    api_keys_file = cur_dir + '/factories/apikeys.json'
    with open(api_keys_file, 'w') as f:
        json.dump(api_keys, f)
    return api_keys


def api_keys_search(api_name):
    cur_dir = os.getcwd()
    api_keys_file = cur_dir + '/factories/apikeys.json'
    with open(api_keys_file, 'r') as f:
        items = json.load(f)
    key = False
    for item in items:
        if (item['name'] == api_name):
            key = item['key']
    return key
