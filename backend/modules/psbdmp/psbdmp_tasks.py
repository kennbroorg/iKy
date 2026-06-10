#!/usr/bin/env python

import argparse
import json
import re

import requests
from celery.utils.log import get_task_logger
from factories.task_wrapper import iky_task

logger = get_task_logger(__name__)


@iky_task(module_name="psbdmp")
def p_psbdmp(email, from_m="Initial"):
    """Task of Celery that get info from psbdmp."""

    # Code
    username = email.split("@")[0] if "@" in email else email

    req = requests.get(f"https://psbdmp.ws/api/v3/search/{username}", timeout=30)

    if not req.json():
        raise Exception("iKy - Pastebin Dump not found")

    dump_list = []
    dump_word = []
    for dump in req.json():
        response = requests.get(
            f"https://psbdmp.ws/api/v3/dump/{dump['id']}",
            timeout=30,
        )
        dump_list.append({"id": dump["id"], "tags": dump["tags"], "time": dump["time"]})
        dump_text = response.json()["content"]
        regex = rf"(.*(?:{re.escape(username)}).*)\r?\n?"
        matches = re.findall(regex, dump_text, re.IGNORECASE)
        for match in matches:
            dump_word.append({"label": match.strip(), "value": 1})

    # Total
    total = []
    total.append({"module": "psbdmp"})
    total.append({"param": email})
    # Evaluates the module that executed the task and set validation
    total.append({"validation": "soft" if from_m != "Initial" else "no"})

    # Graphic Array
    graphic = []

    # Profile Array
    profile = []

    # Timeline Array
    timeline = []

    # Task Array
    tasks = []

    for dump_time in dump_list:
        timeline_item = {
            "date": dump_time["time"],
            "action": "Pastebin : Dump",
            "icon": "fa-bars",
        }
        timeline.append(timeline_item)

    total.append({"raw": ""})
    graphic.append({"dlist": dump_list})
    graphic.append({"dword": dump_word})
    total.append({"graphic": graphic})
    total.append({"profile": profile})
    total.append({"timeline": timeline})
    total.append({"tasks": tasks})

    return total


# Backward-compatible alias: existing code references t_psbdmp
t_psbdmp = p_psbdmp


def output(data):
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Query psbdmp for Pastebin dumps")
    parser.add_argument("email", help="Email address to look up")
    args = parser.parse_args()

    result = t_psbdmp(args.email)
    output(result)
