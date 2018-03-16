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
    logger.info('User detected: ' + username) # This message appears in Celery console
    req = requests.get("https://api.github.com/users/%s" % username)
    # TODO : Many things 
    # Use other API URLs

    # Raw Array
    raw_node = json.loads(req.content)
    print(json.dumps(raw_node, indent=2))
   
    # Gather Array
    # Gravatar
    # id
    # public_gists
    # bio??
    gather = []
    link = "github"
    node_item = {"name-node": "Github", "title": "Github", 
        "subtitle": "", "icon": "\uf09b", "link": link}
    gather.append(node_item)

    if ('name' in raw_node): 
        node_item = {"name-node": "Gitname", "title": "Git Name", 
                "subtitle": raw_node['name'], "icon": "\uf007", 
                "link": link}
        gather.append(node_item)
    if ('company' in raw_node): 
        node_item = {"name-node": "GitCompany", "title": "Company", 
                "subtitle": raw_node['company'], "icon": "\uf007", 
                "link": link}
        gather.append(node_item)
    if ('public_repos' in raw_node): 
        node_item = {"name-node": "GitRepos", "title": "Repos", 
                "subtitle": raw_node['public_repos'], "icon": "\uf07c", 
                "link": link}
        gather.append(node_item)
    if ('followers' in raw_node): 
        node_item = {"name-node": "GitFollowers", "title": "Followers", 
                "subtitle": raw_node['followers'], "icon": "\uf0c0", 
                "link": link}
        gather.append(node_item)
    if ('following' in raw_node): 
        node_item = {"name-node": "GitFollowing", "title": "Following", 
                "subtitle": raw_node['following'], "icon": "\uf0c0", 
                "link": link}
        gather.append(node_item)
    if ('id' in raw_node): 
        node_item = {"name-node": "GitId", "title": "Id", 
                "subtitle": raw_node['id'], "icon": "\uf2c1", 
                "link": link}
        gather.append(node_item)

    print "**********************"
    print json.dumps(gather, indent=2, separators=(',', ': '))


    # Profile Array
    profile = []
    # location
    # name
    # email
    # gravatar
    # company

    # Timeline Array
    timeline = []
    # created_at
    # updated_at

    # Total
    total = []
    total.append({'module': 'github'})
    total.append({'raw': raw_node})
    total.append({'github': gather})
    # total.append(json.dumps(profile))

    # return json.loads(total)
    return total


def output(data):
    # print json.loads(data)
    # print "********************************"
    print json.dumps(data, indent=4, separators=(',', ': '))


if __name__ == "__main__":
    try:
        username = sys.argv[1]
        result = t_github(username)
        output(result)
    except Exception as e:
        print e
        print "Please provide a username as argument"
