#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import sys
import json
import requests

try : 
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
def t_github(username):
    """ Task of Celery that get info from github """
    logger.info('User detected: ' + username) # This message appears in Celery console
    req = requests.get("https://api.github.com/users/%s" % username)
    # TODO : Many things 
    # Use other API URLs

    # Raw Array
    raw_node = json.loads(req.content)

    # Total
    total = []
    total.append({'module': 'github'})

    if ('message' not in raw_node) or (raw_node['message'] != 'Not Found'):
        # Gather Array
        gather = []

        # Profile Array
        profile = []

        # Timeline Array
        timeline = []

        link = "Github"
        gather_item = {"name-node": "Github", "title": "Github", 
            "subtitle": "", "icon": u'\uf09b', "link": link}
        gather.append(gather_item)

        if ('name' in raw_node): 
            gather_item = {"name-node": "Gitname", "title": "Git Name", 
                    "subtitle": raw_node['name'], "icon": u'\uf007', 
                    "link": link}
            profile_item = {'name': raw_node['name']}
            profile.append(profile_item)
            gather.append(gather_item)
        if ('email' in raw_node) and (raw_node['email'] != None): 
            gather_item = {"name-node": "GitEmail", "title": "Email", 
                    "subtitle": raw_node['email'], "icon": u'\uf0e0', 
                    "link": link}
            gather.append(gather_item)
            profile_item = {'email': raw_node['email']}
            profile.append(profile_item)
        if ('company' in raw_node) and (raw_node['company'] != None): 
            gather_item = {"name-node": "GitCompany", "title": "Company", 
                    "subtitle": raw_node['company'], "icon": u'\uf1ad', 
                    "link": link}
            gather.append(gather_item)
            profile_item = {'company': raw_node['company']}
            profile.append(profile_item)
        if ('blog' in raw_node) and (raw_node['blog'] != None) and (raw_node['blog'] != ""): 
            gather_item = {"name-node": "GitBlog", "title": "Blog", 
                    "subtitle": raw_node['blog'], "icon": u'\uf143', 
                    "link": link}
            gather.append(gather_item)
        if ('bio' in raw_node) and (raw_node['bio'] != None): 
            gather_item = {"name-node": "GitBio", "title": "Bio", 
                    "subtitle": raw_node['bio'], "icon": u'\uf004', 
                    "link": link}
            gather.append(gather_item)
        if ('public_repos' in raw_node): 
            gather_item = {"name-node": "GitRepos", "title": "Repos", 
                    "subtitle": raw_node['public_repos'], "icon": u'\uf07c', 
                    "link": link}
            gather.append(gather_item)
        if ('public_gists' in raw_node): 
            gather_item = {"name-node": "GitGists", "title": "Gists", 
                    "subtitle": raw_node['public_gists'], "icon": u'\uf121', 
                    "link": link}
            gather.append(gather_item)
        if ('followers' in raw_node): 
            gather_item = {"name-node": "GitFollowers", "title": "Followers", 
                    "subtitle": raw_node['followers'], "icon": u'\uf0c0', 
                    "link": link}
            gather.append(gather_item)
        if ('following' in raw_node): 
            gather_item = {"name-node": "GitFollowing", "title": "Following", 
                    "subtitle": raw_node['following'], "icon": u'\uf0c0', 
                    "link": link}
            gather.append(gather_item)
        if ('id' in raw_node): 
            gather_item = {"name-node": "GitId", "title": "Id", 
                    "subtitle": raw_node['id'], "icon": u'\uf129', 
                    "link": link}
            gather.append(gather_item)
        if ('avatar_url' in raw_node): 
            gather_item = {"name-node": "GitAvatar", "title": "Avatar", 
                    "picture": raw_node['avatar_url'], "subtitle": "", 
                    "link": link}
            gather.append(gather_item)
            profile_item = {'avatar': raw_node['avatar_url']}
            profile.append(profile_item)
        if ('location' in raw_node) and (raw_node['location'] != None): 
            profile_item = {'location': raw_node['location']}
            profile.append(profile_item)
        if ('created_at' in raw_node) and (raw_node['created_at'] != None): 
            timeline_item = {'created_at': raw_node['created_at']}
            timeline.append(timeline_item)
        if ('updated_at' in raw_node) and (raw_node['updated_at'] != None): 
            timeline_item = {'updated_at': raw_node['updated_at']}
            timeline.append(timeline_item)

        # Please, respect the order of items in the total array
        # Because the frontend depend of that (By now)
        total.append({'raw': raw_node})
        total.append({'github': gather})
        total.append({'profile': profile})
        total.append({'timeline': timeline})

    return total


def output(data):
    print json.dumps(data, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    username = sys.argv[1]
    result = t_github(username)
    output(result)
