#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import sys
import json
import instaloader
from datetime import datetime
from collections import Counter

try:
    from factories._celery import create_celery
    from factories.application import create_application
    from factories.configuration import api_keys_search
    from factories.iKy_functions import analize_rrss
    from celery.utils.log import get_task_logger
    celery = create_celery(create_application())
except ImportError:
    # This is to test the module individually, and I know that is piece of shit
    sys.path.append('../../')
    from factories._celery import create_celery
    from factories.application import create_application
    from factories.configuration import api_keys_search
    from factories.iKy_functions import analize_rrss
    from celery.utils.log import get_task_logger
    celery = create_celery(create_application())


logger = get_task_logger(__name__)


@celery.task
def t_instagram(username, num=10, from_m="Initial"):
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

            if (post.location):
                postloc_item = {'Caption': post.location.name,
                                'Accessability': post.pcaption,
                                'Latitude': post.location.lat,
                                'Longitude': post.location.lng,
                                'Name': post.location.name,
                                'Time': post.date.strftime("%Y-%m-%d %H:%M:%S")
                                }
                postloc.append(postloc_item)
                profile.append({'geo': postloc_item})

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


        # # weekset
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
            except:
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

        raw_node = {'captions' : captions}
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


def output(data):
    print(" ")
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    username = sys.argv[1]
    result = t_instagram(username)
    output(result)
