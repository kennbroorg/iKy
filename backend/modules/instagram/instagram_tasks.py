#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import sys
import json
import requests
import re
import instaloader
from datetime import datetime
from collections import Counter
import traceback

try:
    from factories._celery import create_celery
    from factories.application import create_application
    from factories.configuration import api_keys_search
    from factories.iKy_functions import analize_rrss
    from factories.iKy_functions import location_geo
    from celery.utils.log import get_task_logger
    celery = create_celery(create_application())
except ImportError:
    # This is to test the module individually, and I know that is piece of shit
    sys.path.append('../../')
    from factories._celery import create_celery
    from factories.application import create_application
    from factories.configuration import api_keys_search
    from factories.iKy_functions import analize_rrss
    from factories.iKy_functions import location_geo
    from celery.utils.log import get_task_logger
    celery = create_celery(create_application())


logger = get_task_logger(__name__)


def p_instaloader(username, num=10, from_m="Initial"):
    """ Task of Celery that get info from instagram"""

    instagram_user = api_keys_search('instagram_user')
    instagram_pass = api_keys_search('instagram_pass')
    raw_node = []

    L = instaloader.Instaloader()

    if (instagram_user and instagram_pass):
        try:
            L.login(instagram_user, instagram_pass)
        except instaloader.exceptions.BadCredentialsException:
            raw_node = {'status': 'Bad Credentials'}
            return raw_node
        except instaloader.exceptions.ConnectionException:
            raw_node = {'status': 'Try later'}
            return raw_node

    try:
        profili = instaloader.Profile.from_username(L.context, username)
    except instaloader.exceptions.ProfileNotExistsException:
        raw_node = {'status': 'Profile Not Found'}
        return raw_node

    # Total
    total = []
    total.append({'module': 'instagram'})
    total.append({'param': username})
    # Evaluates the module that executed the task and set validation
    if (from_m == 'Initial'):
        total.append({'validation': 'no'})
    else:
        total.append({'validation': 'soft'})

    if (raw_node == []):
        # Graphic Array
        graphic = []
        photos = []

        # Profile Array
        presence = []
        profile = []

        # Timeline Array
        timeline = []

        # Gather Array
        gather = []

        # Tasks Array
        tasks = []

        link = "Instagram"
        gather_item = {"name-node": "Instagram", "title": "Instagram",
                       "subtitle": "", "icon": "fab fa-instagram",
                       "link": link}
        gather.append(gather_item)

        gather_item = {"name-node": "Instname", "title": "Name",
                       "subtitle": profili.full_name,
                       "icon": "fas fa-user",
                       "link": link}
        profile_item = {'name': profili.full_name}
        profile.append(profile_item)
        gather.append(gather_item)

        gather_item = {"name-node": "InstPosts", "title": "Posts",
                       "subtitle": profili.mediacount,
                       "icon": "fas fa-photo-video", "link": link}
        gather.append(gather_item)

        gather_item = {"name-node": "InstPosts", "title": "IGTV",
                       "subtitle": profili.igtvcount,
                       "icon": "fas fa-tv", "link": link}
        gather.append(gather_item)

        gather_item = {"name-node": "InstFollowers", "title": "Followers",
                       "subtitle": profili.followers,
                       "icon": "fas fa-users", "link": link}
        gather.append(gather_item)

        gather_item = {"name-node": "InstFollowing", "title": "Following",
                       "subtitle": profili.followees,
                       "icon": "fas fa-users", "link": link}
        gather.append(gather_item)

        gather_item = {"name-node": "InstAvatar", "title": "Avatar",
                       "picture": profili.profile_pic_url,
                       "subtitle": "",
                       "link": link}
        gather.append(gather_item)
        profile_item = {'photos': [{"picture": profili.profile_pic_url,
                                    "title": "Instagram"}]}
        profile.append(profile_item)

        gather_item = {"name-node": "InstBio", "title": "Bio",
                       "subtitle": profili.biography,
                       "icon": "fas fa-heart",
                       "link": link}
        gather.append(gather_item)
        profile_item = {'bio': profili.biography}
        profile.append(profile_item)
        if profili.biography:
            analyze = analize_rrss(profili.biography)
            for item in analyze:
                if(item == 'url'):
                    for i in analyze['url']:
                        profile.append(i)
                if(item == 'tasks'):
                    for i in analyze['tasks']:
                        tasks.append(i)

        gather_item = {"name-node": "InstURL", "title": "URL",
                       "subtitle": profili.external_url,
                       "icon": "fas fa-code",
                       "link": link}
        gather.append(gather_item)

        gather_item = {"name-node": "InstPrivate", "title": "Private Account",
                       "subtitle": profili.is_private,
                       "icon": "fas fa-user-shield",
                       "link": link}
        gather.append(gather_item)

        gather_item = {"name-node": "InstUsername", "title": "Username",
                       "subtitle": profili.username,
                       "icon": "fas fa-user",
                       "link": link}
        gather.append(gather_item)

        gather_item = {"name-node": "InstUserID", "title": "UserID",
                       "subtitle": profili.userid,
                       "icon": "fas fa-user-circle",
                       "link": link}
        gather.append(gather_item)

        gather_item = {"name-node": "InstBuss", "title": "Bussiness Account",
                       "subtitle": profili.is_business_account,
                       "icon": "fas fa-building",
                       "link": link}
        gather.append(gather_item)

        gather_item = {"name-node": "InstVerified",
                       "title": "Verified Account",
                       "subtitle": profili.is_verified,
                       "icon": "fas fa-certificate",
                       "link": link}
        gather.append(gather_item)

        gather_item = {"name": "Instagram",
                       "url": "https://instagram.com/" + username,
                       "icon": "fab fa-instagram",
                       "source": "Instagram",
                       "username": username}
        profile.append({"social": [gather_item]})

        # Geo and Bar
        postloc = []
        postloc_item = []
        stop = 0
        captions = []
        mentions = []
        mentions_temp = []
        hashtags = []
        hashtags_temp = []
        tagged = []
        tagged_temp = []
        tagged = []
        lk_cm = []
        s_lk = []
        s_cm = []
        week_temp = []
        hour_temp = []
        graphImage = graphVideo = graphSidecar = 0

        # Hashtag_temp
        # Mention_temp

        link = "Instagram"
        photos_item = {"name-node": "Instagram", "title": "Instagram",
                       "subtitle": "", "icon": "fab fa-instagram",
                       "link": link}
        photos.append(photos_item)

        for post in profili.get_posts():
            s_lk.append({"name": str(stop), "value": str(post.likes)})
            s_cm.append({"name": str(stop), "value": str(post.comments)})
            # Hashtags
            for h in post.caption_hashtags:
                hashtags_temp.append(h)
            # Mentions
            for m in post.caption_mentions:
                mentions_temp.append(m)
            # Tagged users
            for u in post.tagged_users:
                tagged_temp.append(u)
            # Captions
            captions.append(post.caption)

            # post_date = datetime.strptime(post.date, "%Y-%m-%d %H:%M:%S")
            week_temp.append(post.date.strftime("%A"))
            hour_temp.append(post.date.strftime("%H"))

            if (post.typename == 'GraphImage'):
                photos_item = {"name-node": "Inst" + str(stop),
                               "title": "Image" + str(stop),
                               "picture": post.url,
                               "subtitle": "",
                               "link": link}
                photos.append(photos_item)
                graphImage += 1
            elif (post.typename == 'GraphVideo'):
                graphVideo += 1
            elif (post.typename == 'GraphSidecar'):
                graphSidecar += 1

            # Fix : python 3.9 >
            try:
                if (post.location):
                    postloc_item = {'Caption': post.location.name,
                                    'Accessability': post.pcaption,
                                    'Latitude': post.location.lat,
                                    'Longitude': post.location.lng,
                                    'Name': post.location.name,
                                    'Time': post.date.strftime(
                                        "%Y-%m-%d %H:%M:%S")
                                    }
                    postloc.append(postloc_item)
                    profile.append({'geo': postloc_item})
            except Exception:
                pass

            stop += 1
            if (stop == num):
                break

        # Likes, comments (continue)
        lk_cm.append({"name": "Likes", "series": s_lk})
        lk_cm.append({"name": "Comments", "series": s_cm})

        # Hashtags (continue)
        hashtag_counter = Counter(hashtags_temp)
        for k, v in hashtag_counter.items():
            hashtags.append({"label": k, "value": v})
        # Mentions (continue)
        mention_counter = Counter(mentions_temp)
        for k, v in mention_counter.items():
            mentions.append({"label": k, "value": v})
        # Tagged (continue)
        tagged_counter = Counter(tagged_temp)
        for k, v in tagged_counter.items():
            tagged.append({"label": k, "value": v})

        # hourset
        hourset = []
        hournames = '00 01 02 03 04 05 06 07 08 09 10 11 12 13 14 15 16 17 18 19 20 21 22 23'.split()

        twCounter = Counter(hour_temp)
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
        wdCounter = Counter(week_temp)
        wddata = wdCounter.most_common()
        wddata = sorted(wddata)
        y = []
        c = 0
        for z in weekdays:
            try:
                weekset.append({"name": z, "value": int(wddata[c][1])})
            except Exception:
                weekset.append({"name": z, "value": 0})
            c += 1
        wddata = y

        # children = []
        # children.append({"name": "Likes", "total":
        #                 str(profili.likes)})
        # children.append({"name": "Comments", "total":
        #                 str(profili.comments)})
        # children.append({"name": "Media", "total":
        #                 str(profili.mediacount)})
        # children.append({"name": "IGTV", "total":
        #                 str(profili.igtvcount)})
        # resume = {"name": "instagram", "children": children}

        mediatype = []
        mediatype.append({"name": "Images",
                          "value": str(graphImage)})
        mediatype.append({"name": "Sidecar",
                          "value": str(graphSidecar)})
        mediatype.append({"name": "Videos",
                          "value": str(graphVideo)})

        presence.append({"name": "instagram",
                         "children": [
                             {"name": "followers", 
                              "value": int(profili.followers)},
                             {"name": "following", 
                              "value": int(profili.followees)},
                         ]})
        profile.append({'presence': presence})

        raw_node = {'captions': captions}
        total.append({'raw': raw_node})
        graphic.append({'instagram': gather})
        graphic.append({'postslist': lk_cm})
        graphic.append({'postsloc': postloc})
        graphic.append({'hashtags': hashtags})
        graphic.append({'mentions': mentions})
        graphic.append({'tagged': tagged})
        graphic.append({'hour': hourset})
        graphic.append({'week': weekset})
        graphic.append({'mediatype': mediatype})
        # graphic.append({'resume': resume})
        graphic.append({'photos': photos})
        total.append({'graphic': graphic})
        total.append({'profile': profile})
        total.append({'timeline': timeline})
        total.append({'tasks': tasks})

    return total


def obtain_ids(user):
    response = requests.get('https://www.instagram.com/' + user)
    appid = re.search('appId":"(\d*)', response.text)[1]
    serverid = re.search('server_revision":(\d*)', response.text)[1]

    return appid, serverid


def p_instagram(app, server, username, num=30, from_m="Initial"):
    """ Task of Celery that get info from instagram"""

    # instagram_user = api_keys_search('instagram_user')
    # instagram_pass = api_keys_search('instagram_pass')
    raw_node = []

    # L = instaloader.Instaloader()

    # if (instagram_user and instagram_pass):
    #     try:
    #         L.login(instagram_user, instagram_pass)
    #     except instaloader.exceptions.BadCredentialsException:
    #         raw_node = {'status': 'Bad Credentials'}
    #         return raw_node
    #     except instaloader.exceptions.ConnectionException:
    #         raw_node = {'status': 'Try later'}
    #         return raw_node

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:104.0) 20100101 Firefox/103.0',
        'Accept': '*/*',
        'Accept-Language': 'en,en-US;q=0.3',
        'X-Instagram-AJAX': server,
        'X-IG-App-ID': app,
        'X-ASBD-ID': '198337',
        'X-IG-WWW-Claim': '0',
        'Origin': 'https://www.instagram.com',
        'DNT': '1',
        'Alt-Used': 'i.instagram.com',
        'Connection': 'keep-alive',
        'Referer': 'https://www.instagram.com/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
        'Sec-GPC': '1',
    }

    params = {
        'username': username,
    }

    response = requests.get('https://i.instagram.com/api/v1/users/web_profile_info/', params=params, headers=headers)

    # Total
    total = []
    total.append({'module': 'instagram'})
    total.append({'param': username})
    # Evaluates the module that executed the task and set validation
    if (from_m == 'Initial'):
        total.append({'validation': 'no'})
    else:
        total.append({'validation': 'soft'})

    raw_node = response.json()
    profili = raw_node['data']['user']

    if (raw_node != []):
        # Graphic Array
        graphic = []
        photos = []

        # Profile Array
        presence = []
        profile = []

        # Timeline Array
        timeline = []

        # Gather Array
        gather = []

        # Tasks Array
        tasks = []

        mentions_temp = []
        hashtags_temp = []
        graphImage = graphVideo = graphSidecar = graphPost = 0

        link = "Instagram"
        gather_item = {"name-node": "Instagram", "title": "Instagram",
                       "subtitle": "", "icon": "fab fa-instagram",
                       "link": link}
        gather.append(gather_item)

        gather_item = {"name-node": "Instname", "title": "Name",
                       "subtitle": profili['full_name'],
                       "icon": "fas fa-user",
                       "link": link}
        profile_item = {'name': profili['full_name']}
        profile.append(profile_item)
        gather.append(gather_item)

        graphVideo = profili['edge_felix_video_timeline']['count']
        graphPost = profili['edge_owner_to_timeline_media']['count']

        gather_item = {"name-node": "InstPosts", "title": "Posts",
                       "subtitle": graphPost,
                       "icon": "fas fa-photo-video", "link": link}
        gather.append(gather_item)

        gather_item = {"name-node": "InstPosts", "title": "IGTV",
                       "subtitle": graphVideo,
                       "icon": "fas fa-tv", "link": link}
        gather.append(gather_item)

        gather_item = {"name-node": "InstFollowers", "title": "Followers",
                       "subtitle": profili['edge_followed_by']['count'],
                       "icon": "fas fa-users", "link": link}
        gather.append(gather_item)

        gather_item = {"name-node": "InstFollowing", "title": "Following",
                       "subtitle": profili['edge_follow']['count'],
                       "icon": "fas fa-users", "link": link}
        gather.append(gather_item)

        gather_item = {"name-node": "InstAvatar", "title": "Avatar",
                       "picture": profili['profile_pic_url'],
                       "subtitle": "",
                       "link": link}
        gather.append(gather_item)
        profile_item = {'photos': [{"picture": profili['profile_pic_url'],
                                    "title": "Instagram"}]}
        profile.append(profile_item)

        gather_item = {"name-node": "InstBio", "title": "Bio",
                       "subtitle": profili['biography'],
                       "icon": "fas fa-heart",
                       "link": link}
        gather.append(gather_item)
        profile_item = {'bio': profili['biography']}
        profile.append(profile_item)
        if profili['biography']:
            analyze = analize_rrss(profili['biography'])
            for item in analyze:
                if(item == 'url'):
                    for i in analyze['url']:
                        profile.append(i)
                if(item == 'hashtags'):
                    for i in analyze['hashtags']:
                        hashtags_temp.append(i)
                if(item == 'mentions'):
                    for i in analyze['mentions']:
                        mentions_temp.append(i)
                if(item == 'tasks'):
                    for i in analyze['tasks']:
                        tasks.append(i)

        gather_item = {"name-node": "InstURL", "title": "URL",
                       "subtitle": profili['external_url'],
                       "icon": "fas fa-code",
                       "link": link}
        gather.append(gather_item)

        gather_item = {"name-node": "InstPrivate", "title": "Private Account",
                       "subtitle": profili['is_private'],
                       "icon": "fas fa-user-shield",
                       "link": link}
        gather.append(gather_item)

        gather_item = {"name-node": "InstUsername", "title": "Username",
                       "subtitle": username,
                       "icon": "fas fa-user",
                       "link": link}
        gather.append(gather_item)

        gather_item = {"name-node": "InstUserID", "title": "UserID",
                       "subtitle": profili['id'],
                       "icon": "fas fa-user-circle",
                       "link": link}
        gather.append(gather_item)

        gather_item = {"name-node": "InstBuss", "title": "Bussiness Account",
                       "subtitle": profili['is_business_account'],
                       "icon": "fas fa-building",
                       "link": link}
        gather.append(gather_item)

        gather_item = {"name-node": "InstVerified",
                       "title": "Verified Account",
                       "subtitle": profili['is_verified'],
                       "icon": "fas fa-certificate",
                       "link": link}
        gather.append(gather_item)

        gather_item = {"name": "Instagram",
                       "url": "https://instagram.com/" + username,
                       "icon": "fab fa-instagram",
                       "source": "Instagram",
                       "username": username}
        profile.append({"social": [gather_item]})

        # Geo and Bar
        postloc = []
        postloc_item = []
        stop = 0
        captions = []
        mentions = []
        hashtags = []
        tagged = []
        tagged_temp = []
        tagged = []
        lk_cm = []
        s_lk = []
        s_cm = []
        week_temp = []
        hour_temp = []
        post_det = []

        link = "Instagram"
        photos_item = {"name-node": "Instagram", "title": "Instagram",
                       "subtitle": "", "icon": "fab fa-instagram",
                       "link": link}
        photos.append(photos_item)

        for post_item in profili['edge_owner_to_timeline_media']['edges']:
            post = post_item['node']
            s_lk.append({"name": str(stop), "value": str(post['edge_liked_by']['count'])})
            s_cm.append({"name": str(stop), "value": str(post['edge_media_to_comment']['count'])})

            # Captions
            caption_text = ''
            # print(f"Post: {post['__typename']}")
            for c in post['edge_media_to_caption']['edges']:
                captions.append(c['node']['text'])
                analyze = analize_rrss(c['node']['text'])
                caption_text = c['node']['text']
                # print(f"Caption: {caption_text}")
                # print(f"Hashtags: {analyze['hashtags']}")
                # print(f"Mentions: {analyze['mentions']}")
                for item in analyze:
                    if(item == 'url'):
                        for i in analyze['url']:
                            profile.append(i)
                    # Hashtags
                    if(item == 'hashtags'):
                        for i in analyze['hashtags']:
                            hashtags_temp.append(i)
                    # Mentions
                    if(item == 'mentions'):
                        for i in analyze['mentions']:
                            mentions_temp.append(i)
                    if(item == 'tasks'):
                        for i in analyze['tasks']:
                            tasks.append(i)
            # Tagged users
            for u in post['edge_media_to_tagged_user']['edges']:
                tagged_temp.append(u['node']['user']['username'])

            # Date
            # date = post['taken_at_timestamp']
            # post_date = datetime.strptime(post.date, "%Y-%m-%d %H:%M:%S")
            date = datetime.fromtimestamp(post['taken_at_timestamp'])
            # date = datetime.fromtimestamp(post['taken_at_timestamp'] / 1e3)
            week_temp.append(date.strftime("%A"))
            hour_temp.append(date.strftime("%H"))

            # if (post.typename == 'GraphImage'):
            #     photos_item = {"name-node": "Inst" + str(stop),
            #                    "title": "Image" + str(stop),
            #                    "picture": post.url,
            #                    "subtitle": "",
            #                    "link": link}
            #     photos.append(photos_item)
            #     graphImage += 1
            # elif (post.typename == 'GraphVideo'):
            #     graphVideo += 1
            # elif (post.typename == 'GraphSidecar'):
            #     graphSidecar += 1

            post_item = {
                "name-node": "Inst" + str(stop),
                "title": post['__typename'],
                "subtitle": caption_text,
                "picture": post['thumbnail_src'],
                "picture-orig": post['thumbnail_src'],
                "likes": str(post['edge_liked_by']['count']),
                "comments": str(post['edge_media_to_comment']['count']),
                "date": date.strftime("%Y-%m-%d %H:%M:%S")
                }
            post_det.append(post_item)

            try:
                if (post['location']):
                    loc = location_geo(post['location']['name'])
                    postloc_item = {'Caption': caption_text,
                                    'Accessability': '',
                                    'Latitude': loc['Latitude'],
                                    'Longitude': loc['Longitude'],
                                    'Name': loc['Caption'],
                                    'Time': date.strftime("%Y-%m-%d %H:%M:%S")
                                    }
                    postloc.append(postloc_item)
                    profile.append({'geo': postloc_item})
            except Exception:
                pass

            stop += 1
            if (stop == num):
                break

        # Likes, comments (continue)
        lk_cm.append({"name": "Likes", "series": s_lk})
        lk_cm.append({"name": "Comments", "series": s_cm})

        # Hashtags (continue)
        hashtag_counter = Counter(hashtags_temp)
        for k, v in hashtag_counter.items():
            hashtags.append({"label": k, "value": v})
        # Mentions (continue)
        mention_counter = Counter(mentions_temp)
        for k, v in mention_counter.items():
            mentions.append({"label": k, "value": v})
        # Tagged (continue)
        tagged_counter = Counter(tagged_temp)
        for k, v in tagged_counter.items():
            tagged.append({"label": k, "value": v})

        # hourset
        hourset = []
        hournames = '00 01 02 03 04 05 06 07 08 09 10 11 12 13 14 15 16 17 18 19 20 21 22 23'.split()

        twCounter = Counter(hour_temp)
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
        wdCounter = Counter(week_temp)
        wddata = wdCounter.most_common()
        wddata = sorted(wddata)
        y = []
        c = 0
        for z in weekdays:
            try:
                weekset.append({"name": z, "value": int(wddata[c][1])})
            except Exception:
                weekset.append({"name": z, "value": 0})
            c += 1
        wddata = y

        # children = []
        # children.append({"name": "Likes", "total":
        #                 str(profili.likes)})
        # children.append({"name": "Comments", "total":
        #                 str(profili.comments)})
        # children.append({"name": "Media", "total":
        #                 str(profili.mediacount)})
        # children.append({"name": "IGTV", "total":
        #                 str(profili.igtvcount)})
        # resume = {"name": "instagram", "children": children}

        mediatype = []
        mediatype.append({"name": "Posts",
                          "value": str(graphPost)})
        # mediatype.append({"name": "Sidecar",
        #                   "value": str(graphSidecar)})
        mediatype.append({"name": "Videos",
                          "value": str(graphVideo)})

        presence.append({"name": "instagram",
                         "children": [
                             {"name": "followers", 
                              "value": int(profili['edge_followed_by']['count'])},
                             {"name": "following", 
                              "value": int(profili['edge_follow']['count'])},
                         ]})
        profile.append({'presence': presence})

        # raw_node = {'captions': captions}
        total.append({'raw': raw_node})
        graphic.append({'instagram': gather})
        graphic.append({'postslist': lk_cm})
        graphic.append({'postsloc': postloc})
        graphic.append({'hashtags': hashtags})
        graphic.append({'mentions': mentions})
        graphic.append({'tagged': tagged})
        graphic.append({'hour': hourset})
        graphic.append({'week': weekset})
        graphic.append({'mediatype': mediatype})
        # graphic.append({'resume': resume})
        graphic.append({'photos': photos})
        graphic.append({'postdet': post_det})
        total.append({'graphic': graphic})
        total.append({'profile': profile})
        total.append({'timeline': timeline})
        total.append({'tasks': tasks})

    return total


@celery.task
def t_instagram(username, num=30, from_m="Initial"):
    total = []
    try:
        # total = p_instaloader(username, from_m)
        app_id, server_id = obtain_ids(username)
        total = p_instagram(app_id, server_id, username, num=num)
    except Exception as e:
        traceback.print_exc()
        traceback_text = traceback.format_exc()
        total.append({'module': 'instagram'})
        total.append({'param': username})
        total.append({'validation': 'not_used'})

        raw_node = []
        raw_node.append({"status": "fail or user not found",
                         "reason": "{}".format(e),
                         # "traceback": 1})
                         "traceback": traceback_text})
        total.append({"raw": raw_node})
    return total


def output(data):
    print(" ")
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    username = sys.argv[1]
    result = t_instagram(username)
    output(result)
