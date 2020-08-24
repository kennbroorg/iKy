#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
Get general information about Twitter account
"""

import sys
import json
import requests

import tweepy
# import oauth2

try:
    from factories._celery import create_celery
    from factories.application import create_application
    from factories.configuration import api_keys_search
    from celery.utils.log import get_task_logger
    celery = create_celery(create_application())
except ImportError:
    # This is to test the module individually, and I know that is piece of shit
    sys.path.append('../../')
    from factories._celery import create_celery
    from factories.application import create_application
    from factories.configuration import api_keys_search
    from celery.utils.log import get_task_logger
    celery = create_celery(create_application())

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

__author__ = "KennBro"
__copyright__ = "Copyright 2020, iKy"
__credits__ = ["KennBro"]
__license__ = "GPL"
__version__ = "1.0.0"
__maintainer__ = "KennBro"
__email__ = "kennbro <at> protonmail <dot> com"
__status__ = "Development"

logger = get_task_logger(__name__)


@celery.task
def t_twitter_info(username, from_m="Initial", module=None):

    twitter_consumer_key = api_keys_search('twitter_consumer_key')
    twitter_consumer_secret = api_keys_search('twitter_consumer_secret')
    twitter_access_token = api_keys_search('twitter_access_token')
    twitter_access_token_secret = api_keys_search(
        'twitter_access_token_secret')

    auth = tweepy.OAuthHandler(twitter_consumer_key, twitter_consumer_secret)
    auth.set_access_token(twitter_access_token, twitter_access_token_secret)

    api = tweepy.API(auth)

    # Total
    total = []
    # Graphic Array
    social = []
    graphic = []
    resume = []
    popularity = []
    gather = []

    if (module):
        total.append({'module': module})
    else:
        total.append({'module': 'twitter_info'})
    total.append({'param': username})
    # Evaluates the module that executed the task and set validation
    if (from_m == 'Initial'):
        total.append({'validation': 'no'})
    else:
        total.append({'validation': 'soft'})

    raw_node_total = []

    try:
        result_api = api.get_user(username)
    except tweepy.TweepError as e:
        raw_node_total.append({"Status": e.args[0][0]['message']})
        total.append({'raw': raw_node_total})
        return total

    raw_node_total.append({'Status': ''})
    raw_node_total.append({'raw_node_info': result_api._json})

    link_social = "Twitter"
    gather_item = {"name-node": "Twitter", "title": "Twitter",
                   "subtitle": "", "icon": "fab fa-twitter",
                   "link": link_social}
    gather.append(gather_item)

    gather_item = {"name-node": "TwitterName",
                   "title": "Name",
                   "subtitle": result_api.name,
                   "icon": "fas fa-signature",
                   "link": link_social}
    gather.append(gather_item)

    gather_item = {"name-node": "TwitterUserName",
                   "title": "Username",
                   "subtitle": result_api.screen_name,
                   "icon": "fas fa-user-circle",
                   "link": link_social}
    gather.append(gather_item)

    gather_item = {"name-node": "Twitterphoto",
                   "title": "Avatar",
                   "subtitle": "",
                   "picture": result_api.profile_image_url_https,
                   "link": link_social}
    gather.append(gather_item)

    gather_item = {"name-node": "TwitterLocation",
                   "title": "Location",
                   "subtitle": result_api.location,
                   "icon": "fas fa-map-marker-alt",
                   "link": link_social}
    gather.append(gather_item)

    # verified = "False" if result_api['verified'] == 0 else "True"
    gather_item = {"name-node": "TwitterVerified",
                   "title": "Verified",
                   "subtitle": str(result_api.verified),
                   "icon": "fas fa-certificate",
                   "link": link_social}
    gather.append(gather_item)

    # private = "False" if profile_df['private'][0] == 0 else "True"
    gather_item = {"name-node": "TwitterPrivate",
                   "title": "Protected",
                   "subtitle": str(result_api.protected),
                   "icon": "fas fa-user-shield",
                   "link": link_social}
    gather.append(gather_item)

    gather_item = {"name-node": "TwitterTweets",
                   "title": "Tweets",
                   "subtitle": str(result_api.statuses_count),
                   "icon": "fab fa-twitter-square",
                   "link": link_social}
    gather.append(gather_item)

    # gather_item = {"name-node": "TwitterMedia",
    #                "title": "Media",
    #                "subtitle": str(profile_df['media'][0]),
    #                "icon": "fas fa-photo-video",
    #                "link": link_social}
    # gather.append(gather_item)

    gather_item = {"name-node": "TwitterFollowers",
                   "title": "Followers",
                   "subtitle": str(result_api.followers_count),
                   "icon": "fas fa-users",
                   "link": link_social}
    gather.append(gather_item)

    gather_item = {"name-node": "TwitterFollowing",
                   "title": "Following",
                   "subtitle": str(result_api.friends_count),
                   "icon": "fas fa-user-friends",
                   "link": link_social}
    gather.append(gather_item)

    gather_item = {"name-node": "TwitterList",
                   "title": "Listed",
                   "subtitle": str(result_api.listed_count),
                   "icon": "far fa-list-alt",
                   "link": link_social}
    gather.append(gather_item)

    gather_item = {"name-node": "TwitterHeart",
                   "title": "Favourite",
                   "subtitle": str(result_api.favourites_count),
                   "icon": "fas fa-heart",
                   "link": link_social}
    gather.append(gather_item)

    social_item = {"name": "Twitter",
                   "url": "https://twitter.com/" + username,
                   "icon": "fab fa-twitter",
                   "source": "Twitter",
                   "username": username}
    social.append(social_item)

    children = []
    children.append({"name": "Likes", "total": result_api.favourites_count})
    children.append({"name": "Tweets", "total": result_api.statuses_count})
    children.append({"name": "Followers", "total": result_api.followers_count})
    children.append({"name": "Following", "total": result_api.friends_count})
    # children.append({"name": "Listed", "total": result_api.listed_count})
    resume = {"name": "twitter", "children": children}

    popularity.append({"title": "Followers",
                       "value": result_api.followers_count})
    popularity.append({"title": "Listed", "value": result_api.listed_count})
    popularity.append({"title": "Following",
                       "value": result_api.friends_count})

    total.append({'raw': raw_node_total})
    graphic.append({'social': gather})
    graphic.append({'resume': resume})
    graphic.append({'popularity': popularity})
    total.append({'graphic': graphic})
    total.append({'profile': []})
    total.append({'timeline': []})
    total.append({'tasks': []})

    return total


def output(data):
    print(json.dumps(data, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    username = sys.argv[1]
    result = t_twitter_info(username, "initial")
    output(result)
