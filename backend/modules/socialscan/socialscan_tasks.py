#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import os
import sys
import json
import time
import traceback
from socialscan.util import Platforms, sync_execute_queries

try:
    from factories._celery import create_celery
    from factories.application import create_application
    from factories.fontcheat import fontawesome_cheat_5, search_icon_5
    from celery.utils.log import get_task_logger
    celery = create_celery(create_application())
except ImportError:
    # This is to test the module individually, and I know that is piece of shit
    sys.path.append('../../')
    from factories._celery import create_celery
    from factories.application import create_application
    from factories.fontcheat import fontawesome_cheat_5, search_icon_5
    from celery.utils.log import get_task_logger
    celery = create_celery(create_application())

logger = get_task_logger(__name__)


def p_socialscan(email, from_m="Initial"):
    """ Task of Celery that get info from socialscan """

    # Code to develop the frontend without burning APIs
    cd = os.getcwd()
    td = os.path.join(cd, "outputs")
    output = "output-socialscan.json"
    file_path = os.path.join(td, output)

    if os.path.exists(file_path):
        logger.warning(f"Developer frontend mode - {file_path}")
        try:
            with open(file_path, 'r') as file:
                data = json.load(file)
            return data
        except json.JSONDecodeError:
            logger.error(f"Developer mode ERROR")

    # Code
    username = email.split("@")[0]

    # Total
    total = []
    total.append({'module': 'socialscan'})
    total.append({'param': email})
    total.append({'validation': 'no'})

    # Icons unicode
    font_list = fontawesome_cheat_5()

    # Arrays
    raw_node = []
    graphic = []
    profile = []
    timeline = []

    # Gather Array
    gather_e = []
    gather_u = []

    link_email = "SocialScan"
    social_item = {"name-node": "Socialscan", "title": "SocialScan",
                   "subtitle": "Email", "icon": "fas fa-share-alt",
                   "link": link_email}
    gather_e.append(social_item)

    # Check email
    queries = [email]
    res_email = sync_execute_queries(queries, proxy_list=[])
    # raw_node.append({"Email": res_email})

    for result in res_email:
        if (not result.available):
            fa_icon = search_icon_5(str(result.platform), font_list)
            if (fa_icon is None):
                fa_icon = search_icon_5("question", font_list)

            social_item = {"name-node": "SC" + str(result.platform),
                           "title": str(result.platform),
                           # "subtitle": result.message,
                           "subtitle": "",
                           "icon": fa_icon,
                           "link": link_email}
            gather_e.append(social_item)

    link_user = "SocialScan"
    gather_user = {"name-node": "Socialscan", "title": "SocialScan",
                   "subtitle": "Username", "icon": "fas fa-share-alt",
                   "link": link_user}
    gather_u.append(gather_user)

    # Check username
    queries = [username]
    res_user = sync_execute_queries(queries, proxy_list=[])
    # raw_node.append({"Username": res_user})

    for result in res_user:
        if (not result.available):
            fa_icon = search_icon_5(str(result.platform), font_list)
            if (fa_icon is None):
                fa_icon = search_icon_5("question", font_list)

            social_item = {"name-node": "SCE" + str(result.platform),
                           "title": str(result.platform),
                           # "subtitle": result.message,
                           "subtitle": "",
                           "icon": fa_icon,
                           "link": link_email}
            gather_u.append(social_item)

    total.append({'raw': raw_node})
    graphic.append({'social_email': gather_e})
    graphic.append({'social_user': gather_u})
    total.append({'graphic': graphic})
    total.append({'profile': profile})
    total.append({'timeline': timeline})

    return total


@celery.task
def t_socialscan(email, from_m="Initial"):
    total = []
    tic = time.perf_counter()
    try:
        total = p_socialscan(email)
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
        total.append({'module': 'socialscan'})
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
    logger.info(f"SocialScan - Response in {toc - tic:0.4f} seconds")

    return total


def output(data):
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    email = sys.argv[1]
    result = t_socialscan(email)
    output(result)
