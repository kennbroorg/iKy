#!/usr/bin/env python

import argparse
import json
import random

import requests
from celery.utils.log import get_task_logger
from factories.task_wrapper import iky_task

logger = get_task_logger(__name__)

user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
]


@iky_task(module_name="venmo", dev_mode_sleep=15)
def p_venmo(username):
    """Task of Celery that get info from venmo"""

    url_user = f"https://api.venmo.com/v1/users/{username}"
    response = requests.get(
        url_user,
        headers={"User-Agent": random.choice(user_agents)},
        timeout=30,
    )
    data_user = response.json()

    if data_user.get("error", "") != "":
        raise Exception("iKy - User not found")

    user = data_user["data"]
    raw_node = [{"user": user}]

    total = []
    total.append({"module": "venmo"})
    total.append({"param": username})
    total.append({"validation": "hard"})

    graphic = []
    profile = []
    timeline = []
    gather = []

    link = "Venmo"

    gather.append(
        {
            "name-node": "Venmo",
            "title": "Venmo",
            "subtitle": "",
            "icon": "fas fa-money-bill-wave",
            "link": link,
        }
    )

    gather.append(
        {
            "name-node": "Venmoname",
            "title": "Name",
            "subtitle": user["display_name"],
            "icon": "fas fa-user",
            "link": link,
        }
    )
    profile.append({"name": user["display_name"]})

    gather.append(
        {
            "name-node": "VenmoJoin",
            "title": "Join Date",
            "subtitle": user["date_joined"],
            "icon": "fas fa-calendar-check",
            "link": link,
        }
    )
    timeline.append(
        {
            "action": "Start : Venmo",
            "date": user["date_joined"],
            "desc": "Join date for Venmo",
        }
    )

    gather.append(
        {
            "name-node": "VenmoPic",
            "title": "Avatar",
            "picture": user["profile_picture_url"],
            "subtitle": "",
            "link": link,
        }
    )
    profile.append(
        {"photos": [{"picture": user["profile_picture_url"], "title": "Venmo"}]}
    )

    gather.append(
        {
            "name-node": "VenmoID",
            "title": "UserID",
            "subtitle": user["id"],
            "icon": "fas fa-user-circle",
            "link": link,
        }
    )
    gather.append(
        {
            "name-node": "VenmoURL",
            "title": "URL",
            "subtitle": url_user,
            "icon": "fas fa-code",
            "link": link,
        }
    )
    gather.append(
        {
            "name-node": "VenmoUsername",
            "title": "Username",
            "subtitle": username,
            "icon": "fas fa-user",
            "link": link,
        }
    )

    if user.get("is_active") is not None:
        icon_active = "fas fa-toggle-on" if user["is_active"] else "fas fa-toggle-off"
        gather.append(
            {
                "name-node": "VenmoActive",
                "title": "Active",
                "subtitle": user["is_active"],
                "icon": icon_active,
                "link": link,
            }
        )

    if user.get("about"):
        gather.append(
            {
                "name-node": "VenmoBio",
                "title": "Bio",
                "subtitle": user["about"],
                "icon": "fas fa-heartbeat",
                "link": link,
            }
        )

    if user.get("friends_count") is not None:
        gather.append(
            {
                "name-node": "VenmoFriends",
                "title": "Friends",
                "subtitle": user["friends_count"],
                "icon": "fas fa-user-friends",
                "link": link,
            }
        )

    gather.append(
        {
            "name-node": "VenmoProfile",
            "title": "Profile",
            "subtitle": f"https://venmo.com/{username}",
            "icon": "fas fa-external-link-alt",
            "link": link,
        }
    )

    if user.get("id"):
        gather.append(
            {
                "name-node": "VenmoQR",
                "title": "QR Code",
                "subtitle": f"https://venmo.com/code?user_id={user['id']}",
                "icon": "fas fa-qrcode",
                "link": link,
            }
        )

    social = [
        {
            "name": "Venmo",
            "url": f"https://venmo.com/{username}",
            "source": "Venmo",
            "icon": "fas fa-money-bill-wave",
            "username": username,
        }
    ]
    profile.append({"social": social})
    profile.append({"username": username})

    if user.get("id"):
        profile.append(
            {
                "wallet": [
                    {
                        "name": "Venmo",
                        "url": f"https://venmo.com/code?user_id={user['id']}",
                        "icon": "fas fa-qrcode",
                    }
                ]
            }
        )

    graphic.append({"user": gather})
    total.append({"raw": raw_node})
    total.append({"graphic": graphic})
    total.append({"profile": profile})
    total.append({"timeline": timeline})

    return total


# Backward-compatible alias: existing code references t_venmo
t_venmo = p_venmo


def output(data):
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Query Venmo for a username")
    parser.add_argument("username", help="Venmo username to look up")
    args = parser.parse_args()

    result = t_venmo(args.username)
    output(result)
