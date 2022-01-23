#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import sys
import json
import requests
from datetime import datetime
from collections import Counter
import time
import random
import os
import traceback

try:
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

# from requests.packages.urllib3.exceptions import InsecureRequestWarning
# requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

logger = get_task_logger(__name__)


def p_reddit(username, from_m='Initial'):

    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
        'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
        'Mozilla/5.0 (Windows NT 5.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
        'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36',
        'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36',
        'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
        'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
        'Mozilla/4.0 (compatible; MSIE 9.0; Windows NT 6.1)',
        'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko',
        'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0)',
        'Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko',
        'Mozilla/5.0 (Windows NT 6.2; WOW64; Trident/7.0; rv:11.0) like Gecko',
        'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko',
        'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.0; Trident/5.0)',
        'Mozilla/5.0 (Windows NT 6.3; WOW64; Trident/7.0; rv:11.0) like Gecko',
        'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)',
        'Mozilla/5.0 (Windows NT 6.1; Win64; x64; Trident/7.0; rv:11.0) like Gecko',
        'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0)',
        'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)',
        'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729)'
    ]

    lastaction = 0
    headers = {'User-Agent': random.choice(user_agents)}
    curts = int(time.time())
    commentdata = []
    linkdata = []
    timelist = []
    hourseconds = 3600
    houroffset = -7
    offset = hourseconds*houroffset
    raw_node = []

    # Profile
    req = requests.get('https://www.reddit.com/user/'+username+'/about.json',
                      headers=headers)
    user_status = req.status_code

    userdata = {}
    loclistset = False
    hourset = []
    weekset = []
    topics_bubble = []
    if (user_status == 200):
        userdata = req.json()['data']
        raw_node.append({"profile": userdata})

        # Comments
        while True:
            comurl = 'https://api.pushshift.io/reddit/search/comment/?author='+username+'&size=500&before='+str(curts)
            req = requests.get(comurl, headers=headers)

            tempdata = req.json()['data']
            commentdata += tempdata
            try:
                if tempdata[499]:
                    curts = tempdata[499]['created_utc']
            except: break

        raw_node.append({"comments": commentdata})
        curts = int(time.time())

        # Posts/Submissions
        while True:
            linkurl = 'https://api.pushshift.io/reddit/search/submission/?author='+username+'&size=500&before='+str(curts)
            req = requests.get(linkurl, headers=headers)
            postdata = req.json()['data']
            linkdata += postdata
            try:
                if postdata[499]:
                    curts = postdata[499]['created_utc']
            except: break

        raw_node.append({"posts": linkdata})

        if (commentdata):
            # Last activity
            lastcomment = commentdata[0]['created_utc']
            lastpost = postdata[0]['created_utc']

            if lastcomment > lastpost:
                lastaction = lastcomment
            else: lastaction = lastpost


            # Add all subreddits to a list
            # Add all timed activities to a list
            subList = []
            for x in commentdata:
                subList.append(x['subreddit'].lower())
                timelist.append(x['created_utc'])

        if (postdata):
            for x in postdata:
                subList.append(x['subreddit'].lower())
                timelist.append(x['created_utc'])

            # Adjust time for offset
            timelist = [x + offset for x in timelist]

            # And create a set for comparison purposes
            sublistset = set(subList)

            location_file = os.path.join(os.path.dirname(
                os.path.realpath(__file__)), "all-locations.txt")

            # Load subreddits from file and check them against comments
            locList = [line.rstrip('\n').lower() for line in open(location_file)]
            loclistset = set(locList)

            counter = Counter(subList)
            gdata = counter.most_common()

            topics = []
            for i in gdata:
                topics.append({"name": i[0], "count": i[1], "value": i[1]})
            topics_bubble = {"name": "", "value": 100,
                                "children": topics}

            newtl = []  # hour list
            wdlist = [] # weekday list

            # fill newtl with HOURs
            for x in timelist:
                newtl.append(datetime.fromtimestamp(int(x)).hour)

            # create hour name list
            hournames = '00:00 01:00 02:00 03:00 04:00 05:00 06:00 07:00 08:00 09:00 10:00 11:00 12:00 13:00 14:00 15:00 16:00 17:00 18:00 19:00 20:00 21:00 22:00 23:00'.split()

            # deal with HOUR counting
            tgCounter = Counter(newtl)
            tgdata = tgCounter.most_common()
            # sort by HOUR not popularity
            tgdata = sorted(tgdata)

            d = []
            e = 0
            for g in hournames:
                try:
                    hourset.append({"name": g, "value": int(tgdata[e][1])})
                    d.append(tuple([g, tgdata[e][1]]))
                except:
                    hourset.append({"name": g, "value": 0})
                    d.append(tuple([g, 0]))
                e+=1
            tgdata = d

            # estabish weekday list (0 is Monday in Python-land)
            weekdays = 'Monday Tuesday Wednesday Thursday Friday Saturday Sunday'.split()
            for x in timelist:
                wdlist.append(datetime.fromtimestamp(int(x)).weekday())

            wdCounter = Counter(wdlist)
            wddata = wdCounter.most_common()
            wddata = sorted(wddata)

            # change tuple weekday numbers to weekday names
            y = []
            c = 0
            for z in weekdays:
                try:
                    weekset.append({"name": z, "value": int(wddata[c][1])})
                    y.append(tuple([z, wddata[c][1]]))
                except:
                    weekset.append({"name": z, "value": 0})
                    y.append(tuple([z, 0]))
                c+=1
            wddata = y

    else:
        raw_node = { 'status': 'Not found'}

    # Total
    total = []
    total.append({'module': 'reddit'})
    total.append({'param': username})
    # Evaluates the module that executed the task and set validation
    if (from_m == 'Initial'):
        total.append({'validation': 'no'})
    else:
        total.append({'validation': 'soft'})

    # Profile Array
    profile = []

    # Timeline Array
    timeline = []

    gather = []
    link_social = "Reddit"
    gather_item = {"name-node": "Reddit", "title": "Reddit",
                   "subtitle": "", "icon": "fab fa-reddit-alien",
                   "link": link_social}
    gather.append(gather_item)

    # import pdb;pdb.set_trace()
    if (userdata.get("name", "") != ""):
        gather_item = {"name-node": "RedditName",
                        "title": "Name",
                        "subtitle": userdata.get("name", ""),
                        "icon": "fas fa-user-circle",
                        "link": link_social}
        gather.append(gather_item)
        profile_item = {'name': userdata.get("name", "")}
        profile.append(profile_item)

    if (userdata.get("icon_img", "") != ""):
        gather_item = {"name-node": "Redditphoto",
                        "title": "Reddit",
                        "subtitle": "",
                        "picture": userdata.get("icon_img", ""),
                        "link": link_social}
        gather.append(gather_item)
        photo_item = {"name-node": "Reddit",
                    "title": "Reddit",
                    "subtitle": "",
                    "picture": userdata.get("icon_img", ""),
                    "link": "Photos"}
        profile.append({'photos': [photo_item]})

    # if (sublistset.intersection(loclistset)):
    if (loclistset):
        gather_item = {"name-node": "RedditLocation",
                        "title": "Location",
                        "subtitle": str(sublistset.intersection(
                            loclistset)),
                        "icon": "fas fa-map-marker-alt",
                        "link": link_social}
        gather.append(gather_item)
        profile_item = {'location': str(sublistset.intersection(loclistset))}
        profile.append(profile_item)

    if (userdata.get("comment_karma", "") != ""):
        gather_item = {"name-node": "Redditcommentkarma",
                        "title": "Comment Karma",
                        "subtitle": userdata.get("comment_karma", ""),
                        "icon": "fas fa-comments",
                        "link": link_social}
        gather.append(gather_item)

    if (len(commentdata)):
        gather_item = {"name-node": "Redditcomment",
                        "title": "Comments",
                        "subtitle": str(len(commentdata)),
                        "icon": "far fa-comments",
                        "link": link_social}
        gather.append(gather_item)

    if (userdata.get("link_karma", "") != ""):
        gather_item = {"name-node": "Redditlinkkarma",
                        "title": "Link Karma",
                        "subtitle": userdata.get("link_karma", ""),
                        "icon": "fas fa-link",
                        "link": link_social}
        gather.append(gather_item)

    if (len(commentdata)):
        gather_item = {"name-node": "Redditlink",
                        "title": "Links",
                        "subtitle": str(len(linkdata)),
                        "icon": "fas fa-link",
                        "link": link_social}
        gather.append(gather_item)

    if (userdata.get("has_verified_email", "") != ""):
        gather_item = {"name-node": "RedditEmail",
                        "title": "Verified Email",
                        "subtitle": userdata.get("has_verified_email", ""),
                        "icon": "fas fa-at",
                        "link": link_social}
        gather.append(gather_item)

    if (userdata.get("subreddit", "") != "" and userdata.get("subreddit", "").get("public_description", "") != ""):
        gather_item = {"name-node": "RedditBio",
                        "title": "Bio",
                        "subtitle": userdata.get("subreddit", "").
                            get("public_description", ""),
                        "icon": "fas fa-heartbeat",
                        "link": link_social}
        gather.append(gather_item)

    if (userdata.get("created_utc", "") != ""):
        gather_item = {"name-node": "RedditCreate",
                        "title": "Created",
                        "subtitle": str(datetime.fromtimestamp(
                            userdata.get("created_utc", ""))),
                        "icon": "fas fa-calendar-alt",
                        "link": link_social}
        gather.append(gather_item)
        timeline.append({'action': 'Reddit',
                        'date': str(datetime.fromtimestamp(
                            userdata['created_utc'])),
                        'desc': 'Reddit creation account date'})

    if (lastaction):
        gather_item = {"name-node": "RedditLast",
                        "title": "Last",
                        "subtitle": str(datetime.fromtimestamp(lastaction)),
                        "icon": "far fa-calendar-alt",
                        "link": link_social}
        gather.append(gather_item)
        timeline.append({'action': 'Reddit',
                        'date': str(datetime.fromtimestamp(lastaction)),
                        'desc': 'Reddit last action'})

    # Graphic Array
    graphic = []

    # Bios Array
    # bios = []

    total.append({'raw': raw_node})
    graphic.append({'social': gather})
    graphic.append({'hour': hourset})
    graphic.append({'week': weekset})
    graphic.append({'topics': topics_bubble})
    total.append({'graphic': graphic})
    total.append({'profile': profile})
    total.append({'timeline': timeline})

    return total


@celery.task
def t_reddit(user, from_m='Initial'):
    # Variable principal
    total = []
    # Take initial time
    tic = time.perf_counter()

    # try execution principal function
    try:
        total = p_reddit(user, from_m)
    # Error handle
    except Exception as e:
        # Error description
        traceback.print_exc()
        traceback_text = traceback.format_exc()
        code = 10
        # if ('Reddit user don\'t exist' in traceback_text):
        #     code = 5

        # Set module name in JSON format
        total.append({"module": "reddit"})
        total.append({"param": user})
        total.append({"validation": "null"})

        # Set status code and reason
        status = []
        status.append(
            {
                "code": code,
                "reason": "{}".format(e),
                "traceback": traceback_text,
            }
        )
        total.append({"raw": status})

    # Take final time
    toc = time.perf_counter()
    # Show process time
    logger.info(f"Reddit - Response in {toc - tic:0.4f} seconds")

    return total


def output(data):
    print(json.dumps(data, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    username = sys.argv[1]
    result = t_reddit(username, "initial")
    output(result)
