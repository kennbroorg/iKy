#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import os
import sys
import json
import requests
import re
import traceback
import time

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
    # from factories.iKy_functions import analize_rrss
    # from factories.iKy_functions import location_geo
    celery = create_celery(create_application())

logger = get_task_logger(__name__)


def p_psbdmp(email, from_m="Initial"):
    """ Task of Celery that get info from psbdmp """

    # Code to develop the frontend without burning APIs
    cd = os.getcwd()
    td = os.path.join(cd, "outputs")
    output = "output-psbdmp.json"
    file_path = os.path.join(td, output)

    if os.path.exists(file_path):
        logger.info(f"Developer frontend mode - {file_path}")
        try:
            with open(file_path, 'r') as file:
                data = json.load(file)
            return data
        except json.JSONDecodeError:
            logger.error(f"Developer mode ERROR")

    # Code
    if ("@" in email):
        username = email.split("@")[0]
    else:
        username = email

    req = requests.get("https://psbdmp.ws/api/v3/search/%s" % username)

    if (req.json() == []):
        raise Exception("iKy - Pastebin Dump not found")

    dump_list = []
    dump_word = []
    for dump in req.json():
        response = requests.get("https://psbdmp.ws/api/v3/dump/%s" % dump['id'])
        dump_list.append({'id': dump['id'], 
                          'tags': dump['tags'], 
                          'time': dump['time']})
        dump_text = response.json()['content']
        regex = rf"(.*(?:{username}).*)\r?\n?"
        matches = re.findall(regex, dump_text, re.IGNORECASE)
        for match in matches:
            dump_word.append({"label": match.strip(), "value": 1})

    # Total
    total = []
    total.append({'module': 'psbdmp'})
    total.append({'param': email})
    # Evaluates the module that executed the task and set validation
    if (from_m == 'Initial'):
        total.append({'validation': 'no'})
    else:
        total.append({'validation': 'soft'})

    # Graphic Array
    graphic = []

    # Profile Array
    profile = []

    # Timeline Array
    timeline = []

    # Task Array
    tasks = []

    for dump_time in dump_list:
        timeline_item = {'date': dump_time['time'],
            "action": "Pastebin : Dump",
            "icon": "fa-bars"}
        timeline.append(timeline_item)

    total.append({'raw': ''})
    graphic.append({'dlist': dump_list})
    graphic.append({'dword': dump_word})
    total.append({'graphic': graphic})
    total.append({'profile': profile})
    total.append({'timeline': timeline})
    total.append({'tasks': tasks})

    return total


@celery.task
def t_psbdmp(email, from_m="Initial"):
    total = []
    tic = time.perf_counter()
    try:
        total = p_psbdmp(email, from_m)
    except Exception as e:
        # Check internal error
        if str(e).startswith("iKy - "):
            reason = str(e)[len("iKy - "):]
            status = "Warning"
        else:
            reason = str(e)
            status = "Fail"

        traceback.print_exc()
        traceback_text = traceback.format_exc()
        total.append({'module': 'psbdmp'})
        total.append({'param': email})
        total.append({'validation': 'not_used'})

        raw_node = []
        raw_node.append({"status": status,
                         # "reason": "{}".format(e),
                         "reason": reason,
                         "traceback": traceback_text})
        total.append({"raw": raw_node})

    # Take final time
    toc = time.perf_counter()
    # Show process time
    logger.info(f"PsbDmp - Response in {toc - tic:0.4f} seconds")

    return total


def output(data):
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    email = sys.argv[1]
    result = t_psbdmp(email)
    output(result)
