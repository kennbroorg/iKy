#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import sys
import json
import requests
import re
from collections import Counter
from datetime import datetime

import tweepy
# import oauth2

try:
    from factories._celery import create_celery
    from factories.application import create_application
    from factories.iKy_functions import location_geo
    from factories.iKy_functions import analize_rrss
    from factories.configuration import api_keys_search
    from celery.utils.log import get_task_logger
    celery = create_celery(create_application())
except ImportError:
    # This is to test the module individually, and I know that is piece of shit
    sys.path.append('../../')
    from factories._celery import create_celery
    from factories.application import create_application
    from factories.iKy_functions import location_geo
    from factories.iKy_functions import analize_rrss
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
    twitter_access_token = api_keys_search('twitter_access_token')
    twitter_access_token_secret = api_keys_search(
        'twitter_access_token_secret')

    auth = tweepy.OAuthHandler(twitter_consumer_key, twitter_consumer_secret)
    auth.set_access_token(twitter_access_token, twitter_access_token_secret)

    api = tweepy.API(auth)

    total = []
    try:
        result_api = api.get_user(username)
    except tweepy.TweepError as e:
        total.append({'raw_node': e.args})
        return total

    raw_node = tweepy.Cursor(api.user_timeline, id=username,
                             tweet_mode='extended', exclude_replies=False,
                             contributor_details=True, include_entities=True
                             ).items(100)
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
    for tweet in raw_node:
        raw_node_tweets.append(tweet._json)

        if (tweet._json['full_text'][:3] != 'RT '):
            tweets += 1
            s_lk.append({"name": str(index),
                        "value": str(tweet._json['favorite_count'])})
            s_rt.append({"name": str(index),
                        "value": str(tweet._json['retweet_count'])})
            # s_rp.append({"name": str(index), "value": str(row['nreplies'])})

            # Mentions
            for user in tweet._json['entities']['user_mentions']:
                mention_temp.append(user['screen_name'])

            # Hashtags
            for h in tweet._json['entities']['hashtags']:
                hashtag_temp.append(h['text'])

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

    # Total
    total = []
    # Graphic Array
    graphic = []
    resume = []
    popularity = []
    approval = []
    gather = []

    # Profile Array
    profile = []
    social = []
    urls = []

    # Timeline Array
    timeline = []

    # Tasks Array
    tasks = []

    raw_node_total = []
    raw_node_total.append({'raw_node_info': result_api._json})
    raw_node_total.append({'raw_node_tweets': raw_node_tweets})

    create_date = created_at.strftime("%Y-%m-%d")

    total.append({'module': 'twitter'})
    total.append({'param': username})
    # Evaluates the module that executed the task and set validation
    if (from_m == 'Initial'):
        total.append({'validation': 'no'})
    else:
        total.append({'validation': 'soft'})

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
    profile_item = {'name': result_api.name}
    profile.append(profile_item)

    gather_item = {"name-node": "TwitterUserName",
                   "title": "Username",
                   "subtitle": result_api.screen_name,
                   "icon": "fas fa-user-circle",
                   "link": link_social}
    gather.append(gather_item)
    profile_item = {'username': result_api.screen_name}
    profile.append(profile_item)

    gather_item = {"name-node": "Twitterphoto",
                   "title": "Avatar",
                   "subtitle": "",
                   "picture": result_api.profile_image_url_https,
                   "link": link_social}
    gather.append(gather_item)
    pic = result_api.profile_image_url_https.replace("_normal.", "_400x400.")
    photo_item = {"name-node": "Twitter",
                  "title": "Twitter",
                  "subtitle": "",
                  "picture": pic,
                  "link": "Photos"}
    profile.append({'photos': [photo_item]})

    gather_item = {"name-node": "TwitterLocation",
                   "title": "Location",
                   "subtitle": result_api.location,
                   "icon": "fas fa-map-marker-alt",
                   "link": link_social}
    gather.append(gather_item)
    if result_api.location:
        profile_item = {'location': result_api.location}
        profile.append(profile_item)

        geo_item = location_geo(result_api.location, time=create_date)
        if(geo_item):
            profile.append({'geo': geo_item})

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

    if (result_api.entities.get("url", "") != "" and
        result_api.entities['url'].get("urls", "") != ""):
        for urls in result_api.entities['url']['urls']:
            if urls['expanded_url']:
                analyze = analize_rrss(urls['expanded_url'])
                for item in analyze:
                    if(item == 'url'):
                        for i in analyze['url']:
                            profile.append(i)
                    if(item == 'tasks'):
                        for i in analyze['tasks']:
                            tasks.append(i)

    if (result_api.entities.get("description", "") != "" and
        result_api.entities['description'].get("urls", "") != ""):
        for urls in result_api.entities['description']['urls']:
            if urls['expanded_url']:
                analyze = analize_rrss(urls['expanded_url'])
                for item in analyze:
                    if(item == 'url'):
                        for i in analyze['url']:
                            profile.append(i)
                    if(item == 'tasks'):
                        for i in analyze['tasks']:
                            tasks.append(i)

    if result_api.description:
        profile.append({'bio': result_api.description})
        analyze = analize_rrss(result_api.description)
        for item in analyze:
            if(item == 'url'):
                for i in analyze['url']:
                    profile.append(i)
            if(item == 'tasks'):
                for i in analyze['tasks']:
                    tasks.append(i)

    social_item = {"name": "Twitter",
                   "url": "https://twitter.com/" + username,
                   "icon": "fab fa-twitter",
                   "source": "Twitter",
                   "username": username}
    social.append(social_item)
    profile.append({"social": social})


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

    total.append({'raw': raw_node_total})
    graphic.append({'social': gather})
    graphic.append({'resume': resume})
    graphic.append({'popularity': popularity})
    graphic.append({'approval': approval})
    graphic.append({'hashtag': hashtags})
    graphic.append({'users': users})
    graphic.append({'tweetslist': lk_rt_rp})
    graphic.append({'week': weekset})
    graphic.append({'hour': hourset})
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
    result = t_twitter(username, "initial")
    output(result)
