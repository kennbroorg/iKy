#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import sys
import json
import requests
# import urllib3

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

logger = get_task_logger(__name__)


@celery.task
def t_twitter(username, from_m):

    twitter_consumer_key = api_keys_search('twitter_consumer_key')
    twitter_consumer_secret = api_keys_search('twitter_consumer_secret')
    # twitter_access_token = api_keys_search('twitter_access_token')
    # twitter_access_token_secret = api_keys_search(
    #     'twitter_access_token_secret')

    auth = tweepy.OAuthHandler(twitter_consumer_key, twitter_consumer_secret)
    # auth.set_access_token(twitter_access_token, twitter_access_token_secret)

    api = tweepy.API(auth)
    # consumer = oauth2.Consumer(key=twitter_consumer_key,
    #                            secret=twitter_consumer_secret)
    # access_token = oauth2.Token(key=twitter_access_token,
    #                             secret=twitter_access_token_secret)
    # client = oauth2.Client(consumer, access_token)

    # Total
    total = []
    total.append({'module': 'twitter'})
    total.append({'param': username})
    # Evaluates the module that executed the task and set validation
    if (from_m == 'Initial'):
        total.append({'validation': 'no'})
    else:
        total.append({'validation': 'soft'})

    try:
        result_api = api.get_user(username)
    except tweepy.TweepError as e:
        total.append({'raw_node': e[0]})
        return total

    raw_node = result_api._json

    # Graphic Array
    graphic = []
    resume = []
    popularity = []
    approval = []

    # Profile Array
    profile = []

    # Timeline Array
    timeline = []

    # Twitter : TODO : Get hashtags as footprinting
    # Twitter : TODO : Validations
    # footprint Array
    # footprint = []

    # Bios Array
    # bios = []

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

    approval.append({"title": "Tweets", "value": result_api.statuses_count})
    approval.append({"title": "Likes", "value": result_api.favourites_count})

    timeline_item = {'date': result_api.created_at.strftime(
        "%Y/%m/%d %H:%M:%S"),
        "action": "Twitter : Create Account",
        "icon": "fa-twitter"}
    timeline.append(timeline_item)

    total.append({'raw': raw_node})
    graphic.append({'resume': resume})
    graphic.append({'popularity': popularity})
    graphic.append({'approval': approval})
    total.append({'graphic': graphic})
    if (profile != []):
        total.append({'profile': profile})
    if (timeline != []):
        total.append({'timeline': timeline})

    return total


def output(data):
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    username = sys.argv[1]
    result = t_twitter(username)
    output(result)
