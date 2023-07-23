#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import sys
import traceback
import json
import re
from collections import Counter
from datetime import datetime
import browser_cookie3
from tweety import Twitter


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

logger = get_task_logger(__name__)


def get_twitter_cookies(cookie_keys):
    # Try to get cookie from browser
    ref = ["chromium", "opera", "edge", "firefox", "chrome", "brave"]
    index = 0
    json_cookie = {}
    found = False
    for cookie_fn in [
        browser_cookie3.chromium,
        browser_cookie3.opera,
        browser_cookie3.edge,
        browser_cookie3.firefox,
        browser_cookie3.chrome,
        browser_cookie3.brave,
    ]:
        # print(f"View {ref[index]} browser")
        try:
            for cookie in cookie_fn(domain_name=""):

                if ('twitter' in cookie.domain):
                    # print(f"Cookie {cookie.domain}:{cookie.name}:{cookie.value}")

                    if (cookie.name in cookie_keys and not cookie.is_expired()):
                        json_cookie['browser'] = ref[index]
                        json_cookie[cookie.name] = cookie.value
                        json_cookie[cookie.name + '_expires'] = cookie.expires

                # Check
                found = True
                for key in cookie_keys:
                    if (json_cookie.get(key, "") == ""):
                        found = False
                        break

        except Exception as e:
            print(e)

        index += 1

        if (found):
            break

    return {"found": found, "cookies": json_cookie}


def get_twitter_user_info(username):
    # Valid session
    app = Twitter("twitter")

    cookie_keys = ["guest_id", "guest_id_marketing", "guest_id_ads", "kdt", "auth_token", "ct0", "twid", "personalization_id"]
    json_cookies = get_twitter_cookies(cookie_keys)

    if json_cookies["found"]:
        twitter_cookies = ""

        for cookie in cookie_keys:
            twitter_cookies = twitter_cookies + cookie + "=" + json_cookies["cookies"][cookie] + "; "

        app.load_cookies(twitter_cookies[:-2])

    # Get user and pass
    else:
        twitter_user = api_keys_search('twitter_user')
        twitter_pass = api_keys_search('twitter_pass')
        app.sign_in(twitter_user, twitter_pass)

    user = app.get_user_info(username)

    # Get urls
    url_list = []
    if (user.entities):
        if (user.entities.get("url", "") != "" and
            user.entities['url'].get("urls", "") != ""):
            for urls in user.entities['url']['urls']:
                if urls['expanded_url']:
                    url_list.append(urls['expanded_url'])
        if (user.entities.get("description", "") != "" and
            user.entities['description'].get("urls", "") != ""):
            for urls in user.entities['description']['urls']:
                if urls['expanded_url']:
                    url_list.append(urls['expanded_url'])

    user_info = {"username": username, 
                 "name": user.name,
                 "photo": user.profile_image_url_https,
                 "location": user.location,
                 "verified": user.verified,
                 "id": str(user.id),
                 "protected": user.protected,
                 # "tweets": user.data.public_metrics['tweet_count'],
                 "tweets": user.statuses_count,
                 "sensitive": user.possibly_sensitive,
                 "followers": user.followers_count,
                 "following": user.friends_count,
                 "listed": user.listed_count,
                 "statuses": user.statuses_count,
                 "likes": user.favourites_count,
                 "media": user.media_count,
                 "url": url_list,
                 "description": user.description,
                 "created_at": user.created_at}

    # Get Tweets
    tweets = app.get_tweets(user, pages=3)

    number = 0
    retweets = 0
    tweets_info = []
    views = 0

    for tweet in tweets:
        try:
            if (tweet.is_retweet):
                retweets = retweets + 1
                print(f"Number: {number} is Retweet")
            else:
                number = number + 1

                print(f"Number: {number} is Tweet")

                # Quoted
                try:
                    if (tweet.is_quoted):
                        quoted = "True"
                    else:
                        quoted = "False"
                except Exception:
                    quoted = "undefined"

                # Quoted
                try:
                    if (tweet.is_reply):
                        reply = "True"
                    else:
                        reply = "False"
                except Exception:
                    reply = "undefined"

                # # Mentions
                # mention_temp = []
                # try:
                #     for user in tweet.entities['mentions']:
                #         mention_temp.append(user['username'])
                # except Exception:
                #     pass

                # # Hashtags
                # hashtag_temp = []
                # try:
                #     for h in tweet.entities['hashtags']:
                #         hashtag_temp.append(h['tag'])
                # except Exception:
                #     pass

                # Possibly Sensitive
                try:
                    if (tweet.possibly_sensitive):
                        pos_sen = "True"
                    else:
                        pos_sen = "False"
                except Exception:
                    pos_sen = "undefined"

                for user_m in tweet.user_mentions:
                    print(user_m)
                    # print(user_m.ShortUser.username)
                    print(user_m.username)

                if (tweet.views == "Unavailable"):
                    views = 0
                else:
                    views = tweet.views

                # TODO: replied_to
                # TODO: places
                # TODO: media

                source = tweet.source.replace('Twitter', '').strip()
                source = source.replace('for', '').strip()

                tweet_item = {"likes": tweet.likes,
                              "retweets": tweet.retweet_counts,
                              "bookmark": tweet.bookmark_count,
                              "quotes": tweet.quote_counts,
                              "replies": tweet.reply_counts,
                              "views": views,
                              "number": number,
                              "quoted": quoted,
                              "reply": reply,
                              # "user_mentions": tweet.user_mentions,
                              "user_mentions": [mentions.username for mentions in tweet.user_mentions if mentions.username],
                              # "hashtags": tweet.hashtags,
                              "hashtags": [hashtags["text"] for hashtags in tweet.hashtags if "text" in hashtags],
                              "symbols": tweet.symbols,
                              "created_at": tweet.created_on.strftime("%a %b %d %X %z %Y"),
                              "source": source,
                              "possibly_sensitive": pos_sen,
                              "lang": tweet.language,
                              "text": tweet.text}

                tweets_info.append(tweet_item)
        except Exception:
            continue

    # return executed, traceback_text, user_info, tweets_info
    return user_info, number, retweets, tweets_info


# def api_twitter_essential(username):
#     executed = True
#     twitter_v2_bearer_token = api_keys_search('twitter_v2_bearer_token')

#     # TODO: Verify if token is empty
#     auth = tweepy.OAuth2BearerHandler(twitter_v2_bearer_token)
#     api = tweepy.API(auth)

#     tweet_count = 10
#     # search = "@" + username + " since:2023-06-01"
#     # search = username
#     search = "@" + username
#     tweets = tweepy.Cursor(api.search_tweets, search, tweet_mode="extended").items(tweet_count)

#     print(tweets)
#     print("============================================================")
#     for tweet in tweets:
#         print(tweet)
#         print("============================================================")

#     traceback_text = "OK"
#     try:
#         fields=["created_at", "description", "entities", "id", "location", 
#                 "name", "pinned_tweet_id", "profile_image_url", "protected", 
#                 "url", "username", "verified", "withheld", "public_metrics"]
#         result_api = client.get_user(username=username, user_fields=fields)
#     except Exception:
#         traceback.print_exc()
#         traceback_text = traceback.format_exc()
#         executed = False

#     if (not executed):
#         return executed, traceback_text, [], []

#     url_list = []
#     # print("=========================================================")
#     # print(result_api.data.location)
#     # print(result_api.data.protected)
#     # print(result_api.data.entities)
#     # print("=========================================================")
#     if (result_api.data.entities):
#         if (result_api.data.entities.get("url", "") != "" and
#             result_api.data.entities['url'].get("urls", "") != ""):
#             for urls in result_api.data.entities['url']['urls']:
#                 if urls['expanded_url']:
#                     url_list.append(urls['expanded_url'])
#         if (result_api.data.entities.get("description", "") != "" and
#             result_api.data.entities['description'].get("urls", "") != ""):
#             for urls in result_api.data.entities['description']['urls']:
#                 if urls['expanded_url']:
#                     url_list.append(urls['expanded_url'])

#     user_info = {"username": username, 
#                  "name": result_api.data.name,
#                  "photo": result_api.data.profile_image_url,
#                  "location": result_api.data.location,
#                  "verified": result_api.data.verified,
#                  "id": str(result_api.data.id),
#                  "protected": result_api.data.protected,
#                  "tweets": result_api.data.public_metrics['tweet_count'],
#                  "followers": result_api.data.public_metrics['followers_count'],
#                  "following": result_api.data.public_metrics['following_count'],
#                  "listed": result_api.data.public_metrics['listed_count'],
#                  # "likes": result_api.favourites_count,
#                  "likes": "undefined",
#                  "url": url_list,
#                  "description": result_api.data.description,
#                  "created_at": result_api.data.created_at}

#     try:
#         ftweet = ["attachments", "author_id", "context_annotations", 
#                   "conversation_id", "created_at", "entities", "geo", 
#                   "id", "in_reply_to_user_id", "lang",
#                   "public_metrics", 
#                   "possibly_sensitive", "referenced_tweets", "reply_settings", 
#                   "source", "text", "withheld"]
#         result_json = client.get_users_tweets(id=result_api.data.id, 
#                                               max_results=100,
#                                               tweet_fields=ftweet)
#     except Exception as e:
#         traceback.print_exc()

#     number = 0
#     tweets_info = []

#     for tweet in result_json.data:
#         number = number + 1
#         # Mentions
#         mention_temp = []
#         try:
#             for user in tweet.entities['mentions']:
#                 mention_temp.append(user['username'])
#         except Exception:
#             pass

#         # Hashtags
#         hashtag_temp = []
#         try:
#             for h in tweet.entities['hashtags']:
#                 hashtag_temp.append(h['tag'])
#         except Exception:
#             pass

#         # Possibly Sensitive
#         try:
#             if (tweet.possibly_sensitive):
#                 pos_sen = "True"
#             else:
#                 pos_sen = "False"
#         except Exception:
#             pos_sen = "undefined"

#         # # Sources (Elon remove source)
#         # source = tweet.source.replace('Twitter', '').strip()
#         # source = source.replace('for', '').strip()

#         tweet_item = {"likes": tweet.public_metrics['like_count'],
#                       "retweets": tweet.public_metrics['retweet_count'],
#                       "number": number,
#                       "user_mentions": mention_temp,
#                       "hashtags": hashtag_temp,
#                       "created_at": tweet.created_at.strftime("%a %b %d %X %z %Y"),
#                     #   "source": source,
#                       "possibly_sensitive": pos_sen,
#                       "lang": tweet.lang,
#                       "text": tweet.text}

#         tweets_info.append(tweet_item)

#     return executed, traceback_text, user_info, tweets_info

def p_twitter(username, from_m):
    total = []
    user_info, tweets, retweets, tweets_info = get_twitter_user_info(username)
    # print("= USER ==========================================================")
    # print(user_info)
    # print("= TWEETS INFO ===================================================")
    print(f"Tweets: {tweets} - Retweets: {retweets}")
    # print("= TWEETS ========================================================")
    # print(tweets_info)

    # Try with Twitter API v1 (Elevated Access)
    # executed, status, user_info, tweets_info = api_twitter_elevated(username)

    # Try with Twitter API v1 (Elevated Access)
    # if (not executed):
    # executed, status, user_info, tweets_info = api_twitter_essential(username)

    # print("= EXECUTED ======================================================")
    # print(executed)
    # print("= STATUS ========================================================")
    # print(status)
    # print("= USER ==========================================================")
    # print(user_info)
    # print("= TWEETS ========================================================")
    # print(tweets_info)

    # if (not executed):
    #     total.append({'raw_node': status})
    #     return total

    raw_node = []
    raw_node_tweets = []

    index = 0
    lk_rt_rp = []
    mention_temp = []
    hashtag_temp = []
    sources_temp = []
    hashtags = []
    users = []
    sources = []
    # tweets = 0
    # retweets = 0
    s_lk = []   # Likes
    s_rt = []   # Retweets
    s_rp = []   # Replies
    s_bk = []   # Bookmarks
    s_qt = []   # Quotes
    s_vw = []   # Views
    hours = []
    days = []
    t_timeline = []
    time_value = 1
    prev_day = "0000-00-00"

    raw_node_tweets.append(tweets_info)

    for tweet in tweets_info:

        # tweets += 1
        s_lk.append({"name": str(index),
                    "value": str(tweet['likes'])})
        s_rt.append({"name": str(index),
                    "value": str(tweet['retweets'])})
        s_rp.append({"name": str(index),
                    "value": str(tweet['replies'])})
        s_bk.append({"name": str(index),
                    "value": str(tweet['bookmark'])})
        s_qt.append({"name": str(index),
                    "value": str(tweet['quotes'])})
        s_vw.append({"name": str(index),
                    "value": str(tweet['views'])})

        # Mentions
        for user in tweet['user_mentions']:
            mention_temp.append(user)

        # Hashtags
        for h in tweet['hashtags']:
            hashtag_temp.append(h)

        # print(f"Created_at: {type(tweet['created_at'])} - {tweet['created_at']}")
        created_at = datetime.strptime(tweet['created_at'],
                                    "%a %b %d %X %z %Y")
        tweet_date = created_at.strftime("%Y-%m-%dT%H:%M:%S.009Z")
        tweet_day = created_at.strftime("%Y-%m-%d")
        tweet['created_at'] = tweet_date

        # Timeline
        # t_timeline.append({"name": tweet_date, "value": 1})
        if (prev_day == tweet_day):
            time_value = time_value + 1
        else:
            t_timeline.append({"name": tweet_date, "value": time_value})
            time_value = 1
            prev_day = tweet_day

        # Source
        sources_temp.append(tweet['source'])

        # Hours and days
        hours.append(created_at.strftime("%H"))
        days.append(created_at.strftime("%A"))

        index += 1

    # Tweet vs Retweets
    tw_vs_rt = []
    tw_vs_rt.append({"name": "Tweet", "value": tweets})
    tw_vs_rt.append({"name": "Retweet", "value": retweets})

    # Likes, retweets, replies (continue)
    lk_rt_rp.append({"name": "Likes", "series": s_lk})
    lk_rt_rp.append({"name": "Retweets", "series": s_rt})
    lk_rt_rp.append({"name": "Replies", "series": s_rp})
    lk_rt_rp.append({"name": "Bookmarks", "series": s_bk})
    lk_rt_rp.append({"name": "Quotes", "series": s_qt})
    lk_rt_rp.append({"name": "Views", "series": s_vw})

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

    # Presence Array
    presence = []

    raw_node_total = []
    raw_node_total.append({'raw_node_info': user_info})
    raw_node_total.append({'raw_node_tweets': tweets_info})

    try:
        if created_at:
            create_date = created_at.strftime("%Y-%m-%d")
            last_tweet = created_at.strftime("%Y-%m-%d")
    except Exception:
        pass

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
                   "subtitle": user_info['name'],
                   "icon": "fas fa-signature",
                   "link": link_social}
    gather.append(gather_item)
    profile_item = {'name': user_info['name']}
    profile.append(profile_item)

    gather_item = {"name-node": "TwitterUserName",
                   "title": "Username",
                   "subtitle": username,
                   "icon": "fas fa-user-circle",
                   "link": link_social}
    gather.append(gather_item)
    profile_item = {'username': username}
    profile.append(profile_item)

    gather_item = {"name-node": "Twitterphoto",
                   "title": "Avatar",
                   "subtitle": "",
                   "picture": user_info['photo'],
                   "link": link_social}
    gather.append(gather_item)
    pic = user_info['photo'].replace("_normal.", "_400x400.")
    photo_item = {"name-node": "Twitter",
                  "title": "Twitter",
                  "subtitle": "",
                  "picture": pic,
                  "link": "Photos"}
    profile.append({'photos': [photo_item]})

    gather_item = {"name-node": "TwitterLocation",
                   "title": "Location",
                   "subtitle": user_info['location'],
                   "icon": "fas fa-map-marker-alt",
                   "link": link_social}
    gather.append(gather_item)

    if user_info['location']:
        profile_item = {'location': user_info['location']}
        profile.append(profile_item)

        try:
            geo_item = location_geo(user_info['location'], time=create_date)
            print(f"GEO: {geo_item}")
            if(geo_item):
                profile.append({'geo': geo_item})
        except Exception:
            pass

    # verified = "False" if result_api['verified'] == 0 else "True"
    gather_item = {"name-node": "TwitterVerified",
                   "title": "Verified",
                   "subtitle": str(user_info['verified']),
                   "icon": "fas fa-certificate",
                   "link": link_social}
    gather.append(gather_item)

    gather_item = {"name-node": "TwitterID",
                   "title": "ID",
                   "subtitle": str(user_info['id']),
                   "icon": "fas fa-id-card",
                   "link": link_social}
    gather.append(gather_item)

    gather_item = {"name-node": "TwitterPrivate",
                   "title": "Protected",
                   "subtitle": str(user_info['protected']),
                   "icon": "fas fa-user-shield",
                   "link": link_social}
    gather.append(gather_item)

    gather_item = {"name-node": "TwitterSensitive",
                   "title": "Sensitive",
                   "subtitle": str(user_info['sensitive']),
                   "icon": "fas fa-radiation",
                   "link": link_social}
    gather.append(gather_item)

    gather_item = {"name-node": "TwitterTweets",
                   "title": "Tweets",
                   "subtitle": str(user_info['tweets']),
                   "icon": "fab fa-twitter-square",
                   "link": link_social}
    gather.append(gather_item)

    gather_item = {"name-node": "TwitterMedia",
                   "title": "Media",
                   "subtitle": str(user_info['media']),
                   "icon": "fas fa-photo-video",
                   "link": link_social}
    gather.append(gather_item)

    gather_item = {"name-node": "TwitterFollowers",
                   "title": "Followers",
                   "subtitle": str(user_info['followers']),
                   "icon": "fas fa-users",
                   "link": link_social}
    gather.append(gather_item)

    gather_item = {"name-node": "TwitterFollowing",
                   "title": "Following",
                   "subtitle": str(user_info['following']),
                   "icon": "fas fa-user-friends",
                   "link": link_social}
    gather.append(gather_item)

    gather_item = {"name-node": "TwitterList",
                   "title": "Listed",
                   "subtitle": str(user_info['listed']),
                   "icon": "far fa-list-alt",
                   "link": link_social}
    gather.append(gather_item)

    gather_item = {"name-node": "TwitterHeart",
                   "title": "Likes",
                   "subtitle": str(user_info['likes']),
                   "icon": "fas fa-heart",
                   "link": link_social}
    gather.append(gather_item)

    for url in user_info['url']:
        analyze = analize_rrss(url)
        for item in analyze:
            if(item == 'url'):
                for i in analyze['url']:
                    profile.append(i)
            if(item == 'tasks'):
                for i in analyze['tasks']:
                    tasks.append(i)

    if user_info['description']:
        profile.append({'bio': user_info['description']})
        analyze = analize_rrss(user_info['description'])
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
    children.append({"name": "Likes", "total": user_info['likes']})
    children.append({"name": "Tweets", "total": user_info['tweets']})
    children.append({"name": "Followers", "total": user_info['followers']})
    children.append({"name": "Following", "total": user_info['following']})
    children.append({"name": "Listed", "total": user_info['listed']})
    resume = {"name": "twitter", "children": children}

    popularity.append({"title": "Followers",
                       "value": user_info['followers']})
    popularity.append({"title": "Listed", "value": user_info['listed']})
    popularity.append({"title": "Following",
                       "value": user_info['following']})

    approval.append({"title": "Tweets", "value": user_info['tweets']})
    approval.append({"title": "Likes", "value": user_info['likes']})

    user_create_date = user_info['created_at'].strftime(
        "%Y/%m/%d %H:%M:%S") 
    timeline_item = {'date': user_create_date,
        "action": "Twitter : Create Account",
        "icon": "fa-twitter"}
    timeline.append(timeline_item)
    user_info['created_at'] = user_create_date

    try:
        timeline_item = {"date": str(last_tweet),
                         "action": "Twitter : Last Tweet",
                         "icon": "fa-twitter"}
        timeline.append(timeline_item)
    except Exception:
        pass

    presence.append({"name": "twitter",
                        "children": [
                            {"name": "followers", 
                            "value": user_info['followers']},
                            {"name": "following", 
                            "value": user_info['following']},
                        ]})
    profile.append({'presence': presence})

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


@celery.task
def t_twitter(username, from_m):
    total = []
    try:
        total = p_twitter(username, from_m)
    except Exception as e:
        traceback.print_exc()
        traceback_text = traceback.format_exc()
        total.append({'module': 'twitter'})
        total.append({'param': username})
        total.append({'validation': 'not_used'})

        raw_node = []
        raw_node.append({"status": "fail",
                         "reason": "{}".format(e),
                         # "traceback": 1})
                         "traceback": traceback_text})
        total.append({"raw": raw_node})
    return total


def output(data):
    print(json.dumps(data, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    username = sys.argv[1]
    result = t_twitter(username, "initial")
    output(result)
