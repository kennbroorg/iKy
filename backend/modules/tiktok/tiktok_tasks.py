#!/usr/bin/env python

import asyncio
import glob
import json
import os
import subprocess
import sys
import time
import traceback
from collections import Counter
from datetime import datetime, timedelta

import browser_cookie3
from TikTokApi import TikTokApi

try:
    from celery.utils.log import get_task_logger
    from factories._celery import create_celery
    from factories.application import create_application
    from factories.iKy_functions import analize_rrss

    celery = create_celery(create_application())
except ImportError:
    # This is to test the module individually, and I know that is piece of shit
    sys.path.append("../../")
    from celery.utils.log import get_task_logger
    from factories._celery import create_celery
    from factories.application import create_application
    from factories.iKy_functions import analize_rrss

    celery = create_celery(create_application())


logger = get_task_logger(__name__)


def get_twitter_cookies(cookie_keys):
    # Try to get cookie from browser
    ref = ["chromium", "opera", "edge", "firefox", "chrome", "brave"]
    json_cookie = {}
    found = False
    for index, cookie_fn in enumerate(
        [
            browser_cookie3.chromium,
            browser_cookie3.opera,
            browser_cookie3.edge,
            browser_cookie3.firefox,
            browser_cookie3.chrome,
            browser_cookie3.brave,
        ]
    ):
        try:
            for cookie in cookie_fn(domain_name=""):
                if (
                    "tiktok.com" in cookie.domain
                    and cookie.name in cookie_keys
                    and not cookie.is_expired()
                ):
                    json_cookie["browser"] = ref[index]
                    json_cookie[cookie.name] = cookie.value
                    json_cookie[cookie.name + "_expires"] = cookie.expires

            # Check after processing all cookies from this browser
            found = True
            for key in cookie_keys:
                if json_cookie.get(key, "") == "":
                    found = False
                    break

        except Exception as e:
            print(e)

        if found:
            break

    return {"found": found, "cookies": json_cookie}


def get_browser_paths():
    if sys.platform == "win32":
        base_path = os.path.expanduser("~\\AppData\\Local\\ms-playwright")
    elif sys.platform == "darwin":
        base_path = os.path.expanduser("~/Library/Caches/ms-playwright")
    else:
        base_path = os.path.expanduser("~/.cache/ms-playwright")

    return {
        "chromium": os.path.join(base_path, "chromium-*"),
        "firefox": os.path.join(base_path, "firefox-*"),
        "webkit": os.path.join(base_path, "webkit-*"),
    }


def check_browsers_installed():
    browser_paths = get_browser_paths()
    print(f"PATHS: {browser_paths}")
    for _browser, path in browser_paths.items():
        if not any(os.path.exists(p) for p in glob.glob(path)):
            return False
    return True


def run_command(command):
    result = subprocess.run(
        command, shell=True, check=True, capture_output=True, text=True
    )
    print(result.stdout)
    if result.stderr:
        print(result.stderr)


def install_playwright():
    if not check_browsers_installed():
        print("Installing Playwright and browsers...")
        run_command("pip install playwright")
        run_command("playwright install")
    else:
        print("Browsers already installed.")


async def get_user_info(ms_token, username, num=5):
    async with TikTokApi() as api:
        await api.create_sessions(ms_tokens=[ms_token], num_sessions=1, sleep_after=3)
        try:
            user = api.user(username)
            user_data = await user.info()
        except KeyError as e:
            if e.args[0] == "user":
                raise Exception("iKy - User Not Found") from e
            else:
                raise
        except Exception as e:
            raise e

        user_videos = []
        async for video in user.videos(count=num):
            user_videos.append(video.as_dict)

        return user_data, user_videos


def run_get_user_info(ms_token, username, num=5):
    return asyncio.run(get_user_info(ms_token, username, num))


def p_tiktok(username, num, from_m="Initial"):
    """Task of Celery that get info from tiktok"""

    # Code to develop the frontend without burning APIs
    cd = os.getcwd()
    td = os.path.join(cd, "outputs")
    output = "output-tiktok.json"
    file_path = os.path.join(td, output)

    if os.path.exists(file_path):
        logger.warning(f"Developer frontend mode - {file_path}")
        try:
            with open(file_path) as file:
                data = json.load(file)
            return data
        except json.JSONDecodeError:
            logger.error("Developer mode ERROR")

    raw_node = []

    # INFO: Get cookies
    cookie_keys = ["msToken"]
    json_cookies = get_twitter_cookies(cookie_keys)
    if json_cookies["found"]:
        logger.info("Tiktok cookies found")
        ms_token = json_cookies["cookies"]["msToken"]
    else:
        raise Exception(
            "iKy - Missing cookie msToken. Login to your tiktok account and retry"
        )

    # INFO: Install playright
    logger.info("Installing playright")
    install_playwright()

    user_data, user_videos = run_get_user_info(ms_token, username, num)

    # with open(f"./{username}-user.json", 'w', encoding='utf-8') as file_user:
    #     json.dump(user_data, file_user, ensure_ascii=False, indent=4)
    # with open(f"./{username}-videos.json", 'w', encoding='utf-8') as file_video:
    #     json.dump(user_videos, file_video, ensure_ascii=False, indent=4)

    # with open(f"./{username}-user.json", 'r', encoding='utf-8') as file_user:
    #     user_data = json.load(file_user)
    # with open(f"./{username}-videos.json", 'r', encoding='utf-8') as file_video:
    #     user_videos = json.load(file_video)

    # Total
    total = []
    total.append({"module": "tiktok"})
    total.append({"param": username})
    # Evaluates the module that executed the task and set validation
    if from_m == "Initial":
        total.append({"validation": "no"})
    else:
        total.append({"validation": "soft"})

    if raw_node == []:
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

        link = "Tiktok"
        gather_item = {
            "name-node": "Tiktok",
            "title": "tiktok",
            "subtitle": "",
            "icon": "fab fa-tiktok",
            "link": link,
        }
        gather.append(gather_item)

        gather_item = {
            "name-node": "Tikname",
            "title": "Name",
            "subtitle": user_data["userInfo"]["user"]["nickname"],
            "icon": "fas fa-user",
            "link": link,
        }
        profile_item = {"name": user_data["userInfo"]["user"]["nickname"]}
        profile.append(profile_item)
        gather.append(gather_item)

        gather_item = {
            "name-node": "TikPosts",
            "title": "Posts",
            "subtitle": user_data["userInfo"]["stats"]["videoCount"],
            "icon": "fas fa-photo-video",
            "link": link,
        }
        gather.append(gather_item)

        gather_item = {
            "name-node": "TikFollowers",
            "title": "Followers",
            "subtitle": user_data["userInfo"]["stats"]["followerCount"],
            "icon": "fas fa-users",
            "link": link,
        }
        gather.append(gather_item)

        gather_item = {
            "name-node": "TikFollowing",
            "title": "Following",
            "subtitle": user_data["userInfo"]["stats"]["followingCount"],
            "icon": "fas fa-users",
            "link": link,
        }
        gather.append(gather_item)

        gather_item = {
            "name-node": "TikAvatar",
            "title": "Avatar",
            "picture": user_data["userInfo"]["user"]["avatarLarger"],
            "subtitle": "",
            "link": link,
        }
        gather.append(gather_item)
        profile_item = {
            "photos": [
                {
                    "picture": user_data["userInfo"]["user"]["avatarLarger"],
                    "title": "tiktok",
                }
            ]
        }
        profile.append(profile_item)

        try:
            if user_data["user"]["signature"]:
                gather_item = {
                    "name-node": "tikBio",
                    "title": "Bio",
                    "subtitle": user_data["user"]["signature"],
                    "icon": "fas fa-heart",
                    "link": link,
                }
                gather.append(gather_item)

                profile_item = {"bio": user_data["user"]["signature"]}
                profile.append(profile_item)

                analyze = analize_rrss(user_data["user"]["signature"])
                for item in analyze:
                    if item == "url":
                        for i in analyze["url"]:
                            profile.append(i)
                    if item == "tasks":
                        for i in analyze["tasks"]:
                            tasks.append(i)
        except Exception:
            pass

        try:
            if user_data["userInfo"]["user"]["bioLink"]["link"]:
                profile.append(
                    {"url": user_data["userInfo"]["user"]["bioLink"]["link"]}
                )
        except Exception:
            pass

        gather_item = {
            "name-node": "TikFriend",
            "title": "Friends",
            "subtitle": user_data["userInfo"]["stats"]["friendCount"],
            "icon": "fas fa-handshake",
            "link": link,
        }
        gather.append(gather_item)

        try:
            timeline_item = {
                "date": datetime.utcfromtimestamp(
                    int(user_data["userInfo"]["user"]["nickNameModifyTime"])
                ).strftime("%Y-%m-%d"),
                "action": "tiktok : Nickname modified",
                "icon": "fa-tiktok",
            }
            timeline.append(timeline_item)
        except Exception:
            pass

        gather_item = {
            "name-node": "TikHeart",
            "title": "Likes",
            "subtitle": user_data["userInfo"]["stats"]["heartCount"],
            "icon": "fas fa-heart",
            "link": link,
        }
        gather.append(gather_item)

        gather_item = {
            "name-node": "TikPrivate",
            "title": "Private Account",
            "subtitle": user_data["userInfo"]["user"]["privateAccount"],
            "icon": "fas fa-user-shield",
            "link": link,
        }
        gather.append(gather_item)

        gather_item = {
            "name-node": "TikUsername",
            "title": "Username",
            "subtitle": user_data["userInfo"]["user"]["uniqueId"],
            "icon": "fas fa-user",
            "link": link,
        }
        gather.append(gather_item)

        gather_item = {
            "name-node": "TiktUserID",
            "title": "UserID",
            "subtitle": user_data["userInfo"]["user"]["id"],
            "icon": "fas fa-user-circle",
            "link": link,
        }
        gather.append(gather_item)

        gather_item = {
            "name-node": "TiktBuss",
            "title": "Bussiness Account",
            "subtitle": user_data["userInfo"]["user"]["commerceUserInfo"][
                "commerceUser"
            ],
            "icon": "fas fa-building",
            "link": link,
        }
        gather.append(gather_item)

        gather_item = {
            "name-node": "TiktVerified",
            "title": "Verified Account",
            "subtitle": user_data["userInfo"]["user"]["verified"],
            "icon": "fas fa-certificate",
            "link": link,
        }
        gather.append(gather_item)

        gather_item = {
            "name": "tiktok",
            "url": "https://tiktok.com/@" + username,
            "icon": "fab fa-tiktok",
            "source": "tiktok",
            "username": username,
        }
        profile.append({"social": [gather_item]})

        # Geo and Bar
        stop = 0
        captions = []
        mentions = []
        hashtags = []
        hashtags_temp = []
        tagged = []
        tagged = []
        lk_cm = []
        s_cl = []
        s_cm = []
        s_lk = []
        s_pl = []
        s_rp = []
        s_sh = []
        week_temp = []
        hour_temp = []
        t_timeline = []

        # Hashtag_temp
        # Mention_temp

        link = "tiktok"
        photos_item = {
            "name-node": "tiktok",
            "title": "tiktok",
            "subtitle": "",
            "icon": "fab fa-tiktok",
            "link": link,
        }
        photos.append(photos_item)

        logger.info("Begin - Getting post information")
        # Sort Array
        user_videos = sorted(user_videos, key=lambda x: x["createTime"])

        for post in user_videos:
            # Exclude pinned videos
            try:
                if post["isPinnedItem"]:
                    continue
            except Exception:
                pass

            s_cl.append(
                {"name": str(stop), "value": str(post["statsV2"]["collectCount"])}
            )
            s_cm.append(
                {"name": str(stop), "value": str(post["statsV2"]["commentCount"])}
            )
            s_lk.append({"name": str(stop), "value": str(post["statsV2"]["diggCount"])})
            s_pl.append({"name": str(stop), "value": str(post["statsV2"]["playCount"])})
            s_rp.append(
                {"name": str(stop), "value": str(post["statsV2"]["repostCount"])}
            )
            s_sh.append(
                {"name": str(stop), "value": str(post["statsV2"]["shareCount"])}
            )

            # Hashtags
            try:
                for h in post["textExtra"]:
                    hashtags_temp.append(h["hashtagName"])
            except Exception:
                pass

            #         # Mentions
            #         for m in post.caption_mentions:
            #             mentions_temp.append(m)
            #         # Tagged users
            #         for u in post.tagged_users:
            #             tagged_temp.append(u)
            # Captions
            captions.append(post["desc"])

            # post_date = datetime.strptime(post.date, "%Y-%m-%d %H:%M:%S")
            week_temp.append(
                datetime.utcfromtimestamp(int(post["createTime"])).strftime("%A")
            )
            # week_temp.append(post["createTime"].strftime("%A"))
            # INFO: For hours you must work with date_utc
            # hour_temp.append(post["createTime"].strftime("%H"))
            hour_temp.append(
                datetime.utcfromtimestamp(int(post["createTime"])).strftime("%H")
            )

            photos_item = {
                "name-node": "TikTok" + str(stop),
                "title": "Video" + str(stop),
                "picture": post["video"]["cover"],
                "subtitle": "",
                "link": link,
            }
            photos.append(photos_item)

            created_at = datetime.utcfromtimestamp(int(post["createTime"])).strftime(
                "%Y-%m-%d"
            )

            # Timeline
            t_timeline.append({"name": created_at, "value": 1})

            stop += 1

        # LastPost
        timeline_item = {
            "date": t_timeline[-1]["name"],
            "action": "Tiktok : Last Post",
            "icon": "fa-tiktok",
        }
        timeline.append(timeline_item)

        # Timeline
        start_date = datetime.strptime(t_timeline[0]["name"], "%Y-%m-%d")
        end_date = datetime.strptime(t_timeline[-1]["name"], "%Y-%m-%d")
        delta_days = (end_date - start_date).days

        tiktok_time = []
        for i in range(delta_days + 1):
            current_date = (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
            record_count = sum(1 for item in t_timeline if item["name"] == current_date)
            tiktok_time.append({"name": current_date, "value": record_count})

        # Likes, comments (continue)
        lk_cm.append({"name": "Likes", "series": s_lk})
        lk_cm.append({"name": "Comments", "series": s_cm})
        lk_cm.append({"name": "Collect", "series": s_cl})
        lk_cm.append({"name": "Play", "series": s_pl})
        lk_cm.append({"name": "Repost", "series": s_rp})
        lk_cm.append({"name": "Shared", "series": s_sh})

        # Hashtags (continue)
        hashtag_counter = Counter(hashtags_temp)
        for k, v in hashtag_counter.items():
            hashtags.append({"label": k, "value": v})
        #     # Mentions (continue)
        #     mention_counter = Counter(mentions_temp)
        #     for k, v in mention_counter.items():
        #         mentions.append({"label": k, "value": v})
        #     # Tagged (continue)
        #     tagged_counter = Counter(tagged_temp)
        #     for k, v in tagged_counter.items():
        #         tagged.append({"label": k, "value": v})

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

        # weekset
        weekset = []
        weekdays = "Monday Tuesday Wednesday Thursday Friday Saturday Sunday".split()
        wdCounter = Counter(week_temp)
        wddata = wdCounter.most_common()
        wddata = sorted(wddata)
        y = []
        for c, z in enumerate(weekdays):
            try:
                weekset.append({"name": z, "value": int(wddata[c][1])})
            except Exception:
                weekset.append({"name": z, "value": 0})
        wddata = y

        children = []
        children.append(
            {
                "name": "Follower",
                "total": str(user_data["userInfo"]["stats"]["followerCount"]),
            }
        )
        children.append(
            {
                "name": "Following",
                "total": str(user_data["userInfo"]["stats"]["followingCount"]),
            }
        )
        children.append(
            {
                "name": "Friends",
                "total": str(user_data["userInfo"]["stats"]["friendCount"]),
            }
        )
        children.append(
            {
                "name": "Likes",
                "total": str(user_data["userInfo"]["stats"]["heartCount"]),
            }
        )
        children.append(
            {
                "name": "Videos",
                "total": str(user_data["userInfo"]["stats"]["videoCount"]),
            }
        )
        resume = {"name": "tiktok", "children": children}

        presence.append(
            {
                "name": "tiktok",
                "children": [
                    {
                        "name": "followers",
                        "value": int(user_data["userInfo"]["stats"]["followerCount"]),
                    },
                    {
                        "name": "following",
                        "value": int(user_data["userInfo"]["stats"]["followingCount"]),
                    },
                ],
            }
        )
        profile.append({"presence": presence})

        raw_node = {"user_data": user_data, "user_video": user_videos}
        total.append({"raw": raw_node})
        graphic.append({"tiktok": gather})
        graphic.append({"postslist": lk_cm})
        graphic.append({"hashtags": hashtags})
        graphic.append({"mentions": mentions})
        graphic.append({"tagged": tagged})
        graphic.append({"hour": hourset})
        graphic.append({"week": weekset})
        graphic.append({"videos": photos})
        graphic.append({"resume": resume})
        graphic.append({"tiktime": tiktok_time})
        total.append({"graphic": graphic})
        total.append({"profile": profile})
        total.append({"timeline": timeline})
        total.append({"tasks": tasks})

    return total


@celery.task
def t_tiktok(username):
    total = []
    tic = time.perf_counter()
    try:
        total = p_tiktok(username, num=15)
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
        total.append({"module": "tiktok"})
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
    logger.info(f"Tiktok - Response in {toc - tic:0.4f} seconds")

    return total


def output(data):
    print(" ")
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    username = sys.argv[1]
    result = t_tiktok(username)
    output(result)
