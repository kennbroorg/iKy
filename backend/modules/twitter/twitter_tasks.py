#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import sys
import json
import twint
from collections import Counter
from datetime import datetime


try:
    from factories._celery import create_celery
    from factories.application import create_application
    from factories.iKy_functions import location_geo
    from factories.iKy_functions import analize_rrss
    from celery.utils.log import get_task_logger
    celery = create_celery(create_application())
except ImportError:
    # This is to test the module individually, and I know that is piece of shit
    sys.path.append('../../')
    from factories._celery import create_celery
    from factories.application import create_application
    from factories.iKy_functions import location_geo
    from factories.iKy_functions import analize_rrss
    from celery.utils.log import get_task_logger
    celery = create_celery(create_application())

logger = get_task_logger(__name__)


@celery.task
def t_twitter(username, from_m):

    c = twint.Config()
    c.Username = username
    c.Pandas = True
    c.User_full = True
    c.Hide_output = True

    twint.run.Lookup(c)
    profile_df = twint.storage.panda.User_df

    c.Limit = 100
    twint.run.Search(c)
    tweets_df = twint.storage.panda.Tweets_df

    # hourset
    hourset = []
    hournames = '00 01 02 03 04 05 06 07 08 09 10 11 12 13 14 15 16 17 18 19 20 21 22 23'.split()

    twCounter = Counter(tweets_df['hour'])
    tgdata = twCounter.most_common()
    tgdata = sorted(tgdata)
    e = 0
    for g in hournames:
        if (g < tgdata[e][0]):
            hourset.append({"name": g, "value": 0})
        elif (g == tgdata[e][0]):
            hourset.append({"name": g, "value": int(tgdata[e][1])})
            e += 1

    # weekset
    weekset = []
    weekdays = 'Monday Tuesday Wednesday Thursday Friday Saturday Sunday'.split()
    wdCounter = Counter(tweets_df['day'])
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

    lk_rt_rp = []
    mention_temp = []
    hashtag_temp = []
    hashtags = []
    users = []
    s_lk = []
    s_rt = []
    s_rp = []
    for index, row in tweets_df.iterrows():
        # Likes, Retweets, Replies
        s_lk.append({"name": str(index), "value": str(row['nlikes'])})
        s_rt.append({"name": str(index), "value": str(row['nretweets'])})
        s_rp.append({"name": str(index), "value": str(row['nreplies'])})
        # series = [{"name": "Likes", "value": str(row['nlikes'])},
        #           {"name": "Retweets", "value": str(row['nretweets'])},
        #           {"name": "Replies", "value": str(row['nreplies'])}]
        # lk_rt_rp.append({"name": str(index), "series": series})

        # Mentions
        mention_iter = iter(row['reply_to'])
        next(mention_iter)
        for user in mention_iter:
            mention_temp.append(user['username'])

        # Hashtags
        for h in row['hashtags']:
            hashtag_temp.append(h)

    # Likes, retweets, replies (continue)
    lk_rt_rp.append({"name": "Likes", "series": s_lk})
    lk_rt_rp.append({"name": "Retweets", "series": s_rt})
    lk_rt_rp.append({"name": "Replies", "series": s_rp})

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

    date_format = datetime.strptime(profile_df['join_date'][0], "%d %b %Y")
    create_date = date_format.strftime("%Y-%m-%d")

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

    gather_item = {"name-node": "TwitterName",
                   "title": "Name",
                   "subtitle": profile_df['name'][0],
                   "icon": "fas fa-user-circle",
                   "link": link_social}
    gather.append(gather_item)
    profile_item = {'name': profile_df['name'][0]}
    profile.append(profile_item)

    gather_item = {"name-node": "Twitterphoto",
                   "title": "Avatar",
                   "subtitle": "",
                   "picture": profile_df['avatar'][0],
                   "link": link_social}
    gather.append(gather_item)
    photo_item = {"name-node": "Twitter",
                  "title": "Twitter",
                  "subtitle": "",
                  "picture": profile_df['avatar'][0],
                  "link": "Photos"}
    profile.append({'photos': [photo_item]})

    gather_item = {"name-node": "TwitterLocation",
                   "title": "Location",
                   "subtitle": profile_df['location'][0],
                   "icon": "fas fa-map-marker-alt",
                   "link": link_social}
    gather.append(gather_item)
    if profile_df['location'][0]:
        profile_item = {'location': profile_df['location'][0]}
        profile.append(profile_item)

        geo_item = location_geo(profile_df['location'][0], time=create_date)
        if(geo_item):
            profile.append({'geo': geo_item})

    verified = "False" if profile_df['verified'][0] == 0 else "True"
    gather_item = {"name-node": "TwitterVerified",
                   "title": "Verified",
                   "subtitle": verified,
                   "icon": "fas fa-certificate",
                   "link": link_social}
    gather.append(gather_item)

    private = "False" if profile_df['private'][0] == 0 else "True"
    gather_item = {"name-node": "TwitterPrivate",
                   "title": "Private",
                   "subtitle": private,
                   "icon": "fas fa-user-shield",
                   "link": link_social}
    gather.append(gather_item)

    gather_item = {"name-node": "TwitterTweets",
                   "title": "Tweets",
                   "subtitle": str(profile_df['tweets'][0]),
                   "icon": "fab fa-twitter-square",
                   "link": link_social}
    gather.append(gather_item)

    gather_item = {"name-node": "TwitterMedia",
                   "title": "Media",
                   "subtitle": str(profile_df['media'][0]),
                   "icon": "fas fa-photo-video",
                   "link": link_social}
    gather.append(gather_item)

    gather_item = {"name-node": "TwitterFollowers",
                   "title": "Followers",
                   "subtitle": str(profile_df['followers'][0]),
                   "icon": "fas fa-users",
                   "link": link_social}
    gather.append(gather_item)

    gather_item = {"name-node": "TwitterFollowing",
                   "title": "Following",
                   "subtitle": str(profile_df['following'][0]),
                   "icon": "fas fa-user-friends",
                   "link": link_social}
    gather.append(gather_item)

    profile.append({'username': profile_df['username'][0]})
    if profile_df['url'][0]:
        analyze = analize_rrss(profile_df['url'][0])
        for item in analyze:
            if(item == 'url'):
                for i in analyze['url']:
                    profile.append(i)
            if(item == 'tasks'):
                for i in analyze['tasks']:
                    tasks.append(i)

    if profile_df['bio'][0]:
        profile.append({'bio': profile_df['bio'][0]})
        analyze = analize_rrss(profile_df['bio'][0])
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

    raw_node = profile_df.to_json(orient='records')
    raw_node_tweets = tweets_df.to_json(orient='columns')

    raw_node_total = []
    raw_node_total.append({'raw_node_info': raw_node})
    raw_node_total.append({'raw_node_tweets': raw_node_tweets})

    children = []
    children.append({"name": "Likes", "total":
                     str(profile_df['likes'][0])})
    children.append({"name": "Tweets", "total":
                     str(profile_df['tweets'][0])})
    children.append({"name": "Followers", "total":
                     str(profile_df['followers'][0])})
    children.append({"name": "Following", "total":
                     str(profile_df['following'][0])})
    # children.append({"name": "Listed", "total": result_api.listed_count})
    resume = {"name": "twitter", "children": children}

    popularity.append({"title": "Followers",
                       "value": str(profile_df['followers'][0])})
    # popularity.append({"title": "Listed", "value": result_api.listed_count})
    popularity.append({"title": "Following",
                       "value": str(profile_df['following'][0])})

    approval.append({"title": "Tweets", "value":
                     str(profile_df['tweets'][0])})
    approval.append({"title": "Likes", "value":
                     str(profile_df['likes'][0])})

    timeline_item = {"date": str(create_date),
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
