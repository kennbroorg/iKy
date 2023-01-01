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
                          'modules.leaks.leaks_tasks',
                          'modules.twitter.twitter_tasks',
                          # 'modules.twint.twint_tasks',
                          'modules.linkedin.linkedin_tasks',
                          'modules.ghostproject.ghostproject_tasks',
                          'modules.github.github_tasks',
                          'modules.fullcontact.fullcontact_tasks',
                          'modules.usersearch.usersearch_tasks',
                          'modules.socialscan.socialscan_tasks',
                          'modules.instagram.instagram_tasks',
                          'modules.tiktok.tiktok_tasks',
                          'modules.sherlock.sherlock_tasks',
                          'modules.holehe.holehe_tasks',
                          'modules.search.search_tasks',
                          'modules.tinder.tinder_tasks',
                          'modules.skype.skype_tasks',
                          'modules.venmo.venmo_tasks',
                          'modules.darkpass.darkpass_tasks',
                          'modules.tweetiment.tweetiment_tasks',
                          'modules.reddit.reddit_tasks',
                          'modules.peopledatalabs.peopledatalabs_tasks',
                          'modules.emailrep.emailrep_tasks',
                          'modules.leaklookup.leaklookup_tasks',
                          'modules.spotify.spotify_tasks',
                          'modules.twitch.twitch_tasks',
                          'modules.mastodon.mastodon_tasks',
                          'modules.dorks.dorks_tasks',
                          'modules.twitter_comparison.twitter_info_tasks',
                          'modules.twitter_comparison.twitter_comp_tasks')
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
    relativePath = ""
    if (os.path.basename(os.getcwd()) != "backend"):
        relativePath = "/../.."
    api_keys_file = cur_dir + relativePath + '/factories/apikeys.json'
    with open(api_keys_file, 'r') as f:
        items = json.load(f)
    key = False
    for item in items:
        if (item['name'] == api_name):
            key = item['key']
    return key
