#!/usr/bin/env python

import json
import random
import sys
import time
import traceback
from collections import Counter
from pathlib import Path

import instaloader

try:
    from celery.utils.log import get_task_logger
    from factories._celery import create_celery
    from factories.application import create_application
    from factories.configuration import api_keys_search
    from factories.iKy_functions import analize_rrss

    celery = create_celery(create_application())
except ImportError:
    # This is to test the module individually, and I know that is piece of shit
    sys.path.append("../../")
    from celery.utils.log import get_task_logger
    from factories._celery import create_celery
    from factories.application import create_application
    from factories.configuration import api_keys_search
    from factories.iKy_functions import analize_rrss

    celery = create_celery(create_application())


logger = get_task_logger(__name__)


def p_instaloader(username, num=5, from_m="Initial"):
    """Task of Celery that get info from instagram"""

    # Code to develop the frontend without burning APIs
    file_path = Path.cwd() / "outputs" / "output-instagram.json"

    if file_path.exists():
        logger.warning(f"Developer frontend mode - {file_path}")
        try:
            with open(file_path) as file:
                data = json.load(file)
            return data
        except json.JSONDecodeError:
            logger.error("Developer mode ERROR")

    # Code
    instagram_user = api_keys_search("instagram_user")
    instagram_pass = api_keys_search("instagram_pass")
    raw_node = []

    L = instaloader.Instaloader()
    L.context.fatal_status_codes = {400, 401, 403, 404, 429, 500, 502, 503}
    # Sanitize username for safe use in session file path (prevent traversal)
    safe_user = instagram_user.replace("/", "_").replace("\\", "_").replace("..", "_")
    session_file = f"./.session-{safe_user}"
    try:
        L.load_session_from_file(instagram_user, session_file)
        logger.info("Using stored session")
    except Exception as e:
        logger.error(e)

        if instagram_user and instagram_pass:
            try:
                L.login(instagram_user, instagram_pass)
                L.save_session_to_file(session_file)
            except instaloader.exceptions.BadCredentialsException:
                raise Exception("iKy - Invalid credentials") from None
            except instaloader.exceptions.LoginException as e:
                raise Exception(e) from e
        else:
            raise Exception("iKy - Credentials not provided") from e

    logged_as = L.test_login()
    logger.info(f"Logged as: {logged_as}")

    logger.info("Begin Getting profile information")
    try:
        profili = instaloader.Profile.from_username(L.context, username)
    except instaloader.exceptions.ProfileNotExistsException:
        raise Exception("iKy - Profile not found") from None
    logger.info("End Getting profile information")

    # Total
    total = []
    total.append({"module": "instagram"})
    total.append({"param": username})
    # Evaluates the module that executed the task and set validation
    if from_m == "Initial":
        total.append({"validation": "no"})
    else:
        total.append({"validation": "soft"})

    if not raw_node:
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
        gather_item = {
            "name-node": "Instagram",
            "title": "Instagram",
            "subtitle": "",
            "icon": "fab fa-instagram",
            "link": link,
        }
        gather.append(gather_item)

        gather_item = {
            "name-node": "Instname",
            "title": "Name",
            "subtitle": profili.full_name,
            "icon": "fas fa-user",
            "link": link,
        }
        profile_item = {"name": profili.full_name}
        profile.append(profile_item)
        gather.append(gather_item)

        gather_item = {
            "name-node": "InstPosts",
            "title": "Posts",
            "subtitle": profili.mediacount,
            "icon": "fas fa-photo-video",
            "link": link,
        }
        gather.append(gather_item)

        try:
            gather_item = {
                "name-node": "InstPosts",
                "title": "IGTV",
                "subtitle": profili.igtvcount,
                "icon": "fas fa-tv",
                "link": link,
            }
            gather.append(gather_item)
        except Exception:
            pass

        gather_item = {
            "name-node": "InstFollowers",
            "title": "Followers",
            "subtitle": profili.followers,
            "icon": "fas fa-users",
            "link": link,
        }
        gather.append(gather_item)

        gather_item = {
            "name-node": "InstFollowing",
            "title": "Following",
            "subtitle": profili.followees,
            "icon": "fas fa-users",
            "link": link,
        }
        gather.append(gather_item)

        gather_item = {
            "name-node": "InstAvatar",
            "title": "Avatar",
            "picture": profili.profile_pic_url,
            "subtitle": "",
            "link": link,
        }
        gather.append(gather_item)
        profile_item = {
            "photos": [{"picture": profili.profile_pic_url, "title": "Instagram"}]
        }
        profile.append(profile_item)

        gather_item = {
            "name-node": "InstBio",
            "title": "Bio",
            "subtitle": profili.biography,
            "icon": "fas fa-heart",
            "link": link,
        }
        gather.append(gather_item)
        profile_item = {"bio": profili.biography}
        profile.append(profile_item)
        if profili.biography:
            analyze = analize_rrss(profili.biography)
            for item in analyze:
                if item == "url":
                    for i in analyze["url"]:
                        profile.append(i)
                if item == "tasks":
                    for i in analyze["tasks"]:
                        tasks.append(i)

        gather_item = {
            "name-node": "InstURL",
            "title": "URL",
            "subtitle": profili.external_url,
            "icon": "fas fa-code",
            "link": link,
        }
        gather.append(gather_item)

        gather_item = {
            "name-node": "InstPrivate",
            "title": "Private Account",
            "subtitle": profili.is_private,
            "icon": "fas fa-user-shield",
            "link": link,
        }
        gather.append(gather_item)

        gather_item = {
            "name-node": "InstUsername",
            "title": "Username",
            "subtitle": profili.username,
            "icon": "fas fa-user",
            "link": link,
        }
        gather.append(gather_item)

        gather_item = {
            "name-node": "InstUserID",
            "title": "UserID",
            "subtitle": profili.userid,
            "icon": "fas fa-user-circle",
            "link": link,
        }
        gather.append(gather_item)

        gather_item = {
            "name-node": "InstBuss",
            "title": "Bussiness Account",
            "subtitle": profili.is_business_account,
            "icon": "fas fa-building",
            "link": link,
        }
        gather.append(gather_item)

        gather_item = {
            "name-node": "InstVerified",
            "title": "Verified Account",
            "subtitle": profili.is_verified,
            "icon": "fas fa-certificate",
            "link": link,
        }
        gather.append(gather_item)

        gather_item = {
            "name": "Instagram",
            "url": "https://instagram.com/" + username,
            "icon": "fab fa-instagram",
            "source": "Instagram",
            "username": username,
        }
        profile.append({"social": [gather_item]})

        # Geo and Bar
        postloc = []
        acc_captions = []
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
        photos_item = {
            "name-node": "Instagram",
            "title": "Instagram",
            "subtitle": "",
            "icon": "fab fa-instagram",
            "link": link,
        }
        photos.append(photos_item)

        logger.info("Begin - Getting post information")
        for stop, post in enumerate(profili.get_posts()):
            # TODO: Last POST is the first iter
            if stop == 0:  # INFO: Last post
                timeline_item = {
                    "date": str(post.date_utc),
                    "action": "Instagram : Last Post",
                    "icon": "fa-instagram",
                }
                timeline.append(timeline_item)

            print(f"POST: {stop}-{num}")
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
            if post.accessibility_caption:
                acc_captions.append(post.accessibility_caption)

            # post_date = datetime.strptime(post.date, "%Y-%m-%d %H:%M:%S")
            week_temp.append(post.date.strftime("%A"))
            # INFO: For hours you must work with date_utc
            hour_temp.append(post.date_utc.strftime("%H"))

            if post.typename == "GraphImage":
                photos_item = {
                    "name-node": "Inst" + str(stop),
                    "title": "Image" + str(stop),
                    "picture": post.url,
                    "subtitle": "",
                    "link": link,
                }
                photos.append(photos_item)
                graphImage += 1
            elif post.typename == "GraphVideo":
                graphVideo += 1
            elif post.typename == "GraphSidecar":
                graphSidecar += 1

            if stop == num - 1:
                break

            time.sleep(random.uniform(0.5, 2.0))

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
        hournames = "00 01 02 03 04 05 06 07 08 09 10 11 12 13 14 15 16 17 18 19 20 21 22 23".split()

        twCounter = Counter(hour_temp)
        tgdata = twCounter.most_common()
        tgdata = sorted(tgdata)
        e = 0
        for g in hournames:
            if (e >= len(tgdata)) or (g < tgdata[e][0]):
                hourset.append({"name": g, "value": 0})
            elif g == tgdata[e][0]:
                hourset.append({"name": g, "value": int(tgdata[e][1])})
                e += 1

        # weekset — use Counter lookup to preserve proper Mon-Sun order
        weekset = []
        weekdays = "Monday Tuesday Wednesday Thursday Friday Saturday Sunday".split()
        wdCounter = Counter(week_temp)
        for day in weekdays:
            weekset.append({"name": day, "value": wdCounter.get(day, 0)})

        mediatype = []
        mediatype.append({"name": "Images", "value": str(graphImage)})
        mediatype.append({"name": "Sidecar", "value": str(graphSidecar)})
        mediatype.append({"name": "Videos", "value": str(graphVideo)})

        presence.append(
            {
                "name": "instagram",
                "children": [
                    {"name": "followers", "value": int(profili.followers)},
                    {"name": "following", "value": int(profili.followees)},
                ],
            }
        )
        profile.append({"presence": presence})

        raw_node = {"captions": captions, "acc_captions": acc_captions}
        total.append({"raw": raw_node})
        graphic.append({"instagram": gather})
        graphic.append({"postslist": lk_cm})
        graphic.append({"postsloc": postloc})
        graphic.append({"hashtags": hashtags})
        graphic.append({"mentions": mentions})
        graphic.append({"tagged": tagged})
        graphic.append({"hour": hourset})
        graphic.append({"week": weekset})
        graphic.append({"mediatype": mediatype})
        graphic.append({"photos": photos})
        total.append({"graphic": graphic})
        total.append({"profile": profile})
        total.append({"timeline": timeline})
        total.append({"tasks": tasks})

    return total


@celery.task
def t_instagram(username):
    total = []
    tic = time.perf_counter()
    try:
        total = p_instaloader(username, num=5)
    except Exception as e:
        # Check internal error
        if str(e).startswith("iKy - "):
            reason = str(e)[len("iKy - ") :]
            status = "Warning"
        else:
            reason = str(e)
            status = "Fail"

        traceback.print_exc()
        traceback_text = traceback.format_exc()
        total.append({"module": "instagram"})
        total.append({"param": username})
        total.append({"validation": "not_used"})

        raw_node = []
        raw_node.append(
            {
                "status": status,
                # "reason": "{}".format(e),
                "reason": reason,
                "traceback": traceback_text,
            }
        )
        total.append({"raw": raw_node})

    # Take final time
    toc = time.perf_counter()
    # Show process time
    logger.info(f"Instagram - Response in {toc - tic:0.4f} seconds")

    return total


def output(data):
    print(" ")
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    username = sys.argv[1]
    result = t_instagram(username)
    output(result)
