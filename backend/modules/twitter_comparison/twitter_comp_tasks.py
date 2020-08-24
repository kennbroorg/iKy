#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
Get comparison information about Twitter account
"""

import sys
import json
import requests
import re
from collections import Counter
from datetime import datetime

import tweepy
# import oauth2

import time

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
def t_twitter_comp(username, date_from, date_to, from_m="Init", module=None):

    twitter_consumer_key = api_keys_search('twitter_consumer_key')
    twitter_consumer_secret = api_keys_search('twitter_consumer_secret')
    twitter_access_token = api_keys_search('twitter_access_token')
    twitter_access_token_secret = api_keys_search(
        'twitter_access_token_secret')

    auth = tweepy.OAuthHandler(twitter_consumer_key, twitter_consumer_secret)
    auth.set_access_token(twitter_access_token, twitter_access_token_secret)

    api = tweepy.API(auth)

    startDate = datetime.strptime(date_from, '%Y-%m-%d')
    endDate = datetime.strptime(date_to, '%Y-%m-%d')

    # Total
    total = []
    # Graphic Array
    graphic = []
    # Profile Array
    profile = []
    # Timeline Array
    timeline = []
    # Tasks Array
    tasks = []

    if (module):
        total.append({'module': module})
    else:
        total.append({'module': 'twitter_comp'})
    total.append({'param': username})
    # Evaluates the module that executed the task and set validation
    if (from_m == 'Initial'):
        total.append({'validation': 'no'})
    else:
        total.append({'validation': 'soft'})

    raw_node_total = []
    tweets_gather = []
    try:
        tmpTweets = api.user_timeline(username)
    except tweepy.TweepError as e:
        raw_node_total.append({"Status": e.args[0][0]['message']})
        total.append({'raw': raw_node_total})
        return total

    for tweet in tmpTweets:
        if tweet.created_at < endDate and tweet.created_at > startDate:
            tweets_gather.append(tweet)

    while (tmpTweets[-1].created_at > startDate):
        tmpTweets = api.user_timeline(username, max_id = tmpTweets[-1].id)
        for tweet in tmpTweets:
            if tweet.created_at < endDate and tweet.created_at > startDate:
                tweets_gather.append(tweet)

    raw_node_tweets = []

    index = 0
    lk_rt_rp = []
    mention_temp = []
    hashtag_temp = []
    sources_temp = []
    hashtags = []
    users = []
    sources = []
    tweets = 0
    retweets = 0
    s_lk = []
    s_rt = []
    # s_rp = []
    hours = []
    days = []
    t_timeline = []
    q_lk = 0
    q_rt = 0
    q_rp = 0
    q_mt = 0
    q_ht = 0
    for tweet in tweets_gather:
        raw_node_tweets.append(tweet._json)

        if (tweet._json['text'][:3] != 'RT '):
            tweets += 1
            s_lk.append({"name": str(index),
                        "value": str(tweet._json['favorite_count'])})
            s_rt.append({"name": str(index),
                        "value": str(tweet._json['retweet_count'])})
            # s_rp.append({"name": str(index), "value": str(row['nreplies'])})
            q_lk += tweet._json['favorite_count']
            q_rt += tweet._json['retweet_count']
            # q_rp += row['nreplies']

            # Mentions
            for user in tweet._json['entities']['user_mentions']:
                mention_temp.append(user['screen_name'])
                q_mt += 1

            # Hashtags
            for h in tweet._json['entities']['hashtags']:
                hashtag_temp.append(h['text'])
                q_ht += 1

            created_at = datetime.strptime(tweet._json['created_at'],
                                           "%a %b %d %X %z %Y")
            tweet_date = created_at.strftime("%Y-%m-%dT%H:%M:%S.009Z")
            t_timeline.append({"name": tweet_date, "value": 1})

            # Sources
            m_source = re.match("<a.*>(.*)</a>", tweet._json['source'])
            if (m_source):
                source = m_source.groups()[0].replace('Twitter', '').strip()
                source = source.replace('for', '').strip()
                sources_temp.append(source)

            # Hours and days
            hours.append(created_at.strftime("%H"))
            days.append(created_at.strftime("%A"))

            index += 1
        else:
            retweets += 1

    raw_node_total.append({'Status': ''})
    raw_node_total.append({'raw_node_info': raw_node_tweets})

    # Tweet vs Retweets
    tw_vs_rt = []
    tw_vs_rt.append({"name": "Tweet", "value": tweets})
    tw_vs_rt.append({"name": "Retweet", "value": retweets})

    # Likes, retweets, replies (continue)
    lk_rt_rp.append({"name": "Likes", "series": s_lk})
    lk_rt_rp.append({"name": "Retweets", "series": s_rt})
    # lk_rt_rp.append({"name": "Replies", "series": s_rp})

    # Mentions (continue)
    mention_counter = Counter(mention_temp)

    link_users = "Users"
    user_item = {"name-node": "Users", "title": "Users",
                 "subtitle": "",
                 "link": link_users}
    users.append(user_item)
    for k, v in mention_counter.items():
        user_item = {"name-node": k,
                     "title": k,
                     "subtitle": v,
                     "link": link_users}
        users.append(user_item)

    # Hashtags (continue)
    hashtag_counter = Counter(hashtag_temp)
    for k, v in hashtag_counter.items():
        hashtags.append({"label": k, "value": v})

    # Sources (continue)
    sources_counter = Counter(sources_temp)
    for k, v in sources_counter.items():
        sources.append({"name": k, "value": v})

    # Summary
    summary = []
    summary.append({"Tweets": tweets})
    summary.append({"Retweets": retweets})
    summary.append({"Likes": q_lk})
    summary.append({"TRetweets": q_rt})
    # summary.append({"Replies": q_rp})
    summary.append({"Users": q_mt})
    summary.append({"Hashtags": q_ht})

    # hourset
    hourset = []
    hournames = '00 01 02 03 04 05 06 07 08 09 10 11 12 13 14 15 16 17 18 19 20 21 22 23'.split()

    twCounter = Counter(hours)
    tgdata = twCounter.most_common()
    tgdata = sorted(tgdata)
    e = 0
    for g in hournames:
        if (e >= len(tgdata)):
            hourset.append({"name": g, "value": 0})
        elif (g < tgdata[e][0]):
            hourset.append({"name": g, "value": 0})
        elif (g == tgdata[e][0]):
            hourset.append({"name": g, "value": int(tgdata[e][1])})
            e += 1

    # weekset
    weekset = []
    weekdays = 'Monday Tuesday Wednesday Thursday Friday Saturday Sunday'.split()
    wdCounter = Counter(days)
    wddata = wdCounter.most_common()
    wddata = sorted(wddata)
    y = []
    c = 0
    for z in weekdays:
        try:
            weekset.append({"name": z, "value": int(wddata[c][1])})
        except:
            weekset.append({"name": z, "value": 0})
        c += 1
    wddata = y

    total.append({'raw': raw_node_total})
    graphic.append({'hashtag': hashtags})
    graphic.append({'users': users})
    graphic.append({'tweetslist': lk_rt_rp})
    graphic.append({'week': weekset})
    graphic.append({'hour': hourset})
    graphic.append({'summary': summary})
    graphic.append({'sources': sources})
    graphic.append({'time': t_timeline})
    graphic.append({'twvsrt': tw_vs_rt})
    total.append({'graphic': graphic})
    total.append({'profile': profile})
    total.append({'timeline': timeline})
    total.append({'tasks': tasks})

    return total


def output(data):
    print(json.dumps(data, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    username = sys.argv[1]
    date_from = sys.argv[3]
    date_to = sys.argv[4]
    result = t_twitter_comp(username, date_from, date_to, "initial")
    output(result)
