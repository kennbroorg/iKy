#!/usr/bin/env python

import json
import sys
import time
import traceback
from pathlib import Path

from socialscan.util import sync_execute_queries

from celery.utils.log import get_task_logger

from celery_app import celery
from factories.fontcheat import search_icon_5

logger = get_task_logger(__name__)


def p_socialscan(email, from_m="Initial"):
    """Task of Celery that get info from socialscan"""

    # Code to develop the frontend without burning APIs
    file_path = Path.cwd() / "outputs" / "output-socialscan.json"

    if file_path.exists():
        logger.warning(f"Developer frontend mode - {file_path}")
        try:
            with open(file_path) as file:
                data = json.load(file)
            return data
        except json.JSONDecodeError:
            logger.error("Developer mode ERROR")

    # Code
    username = email.split("@")[0]

    # Total
    total = []
    total.append({"module": "socialscan"})
    total.append({"param": email})
    total.append({"validation": "no"})

    # Arrays
    raw_node = []
    graphic = []
    profile = []
    timeline = []

    # Gather Array
    gather_e = []
    gather_u = []

    link_email = "SocialScan"
    social_item = {
        "name-node": "Socialscan",
        "title": "SocialScan",
        "subtitle": "Email",
        "icon": "fas fa-share-alt",
        "link": link_email,
    }
    gather_e.append(social_item)

    # Check email
    queries = [email]
    res_email = sync_execute_queries(queries, proxy_list=[])
    # raw_node.append({"Email": res_email})

    for result in res_email:
        if not result.available:
            fa_icon = search_icon_5(str(result.platform))
            if fa_icon is None:
                fa_icon = search_icon_5("question")

            social_item = {
                "name-node": "SC" + str(result.platform),
                "title": str(result.platform),
                # "subtitle": result.message,
                "subtitle": "",
                "icon": fa_icon,
                "link": link_email,
            }
            gather_e.append(social_item)

    link_user = "SocialScan"
    gather_user = {
        "name-node": "Socialscan",
        "title": "SocialScan",
        "subtitle": "Username",
        "icon": "fas fa-share-alt",
        "link": link_user,
    }
    gather_u.append(gather_user)

    # Check username
    queries = [username]
    res_user = sync_execute_queries(queries, proxy_list=[])
    # raw_node.append({"Username": res_user})

    for result in res_user:
        if not result.available:
            fa_icon = search_icon_5(str(result.platform))
            if fa_icon is None:
                fa_icon = search_icon_5("question")

            social_item = {
                "name-node": "SCE" + str(result.platform),
                "title": str(result.platform),
                # "subtitle": result.message,
                "subtitle": "",
                "icon": fa_icon,
                "link": link_email,
            }
            gather_u.append(social_item)

    total.append({"raw": raw_node})
    graphic.append({"social_email": gather_e})
    graphic.append({"social_user": gather_u})
    total.append({"graphic": graphic})
    total.append({"profile": profile})
    total.append({"timeline": timeline})

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
            reason = str(e)[len("iKy - ") :]
            status = "Warning"
        else:
            reason = str(e)
            status = "Fail"

        traceback.print_exc()
        traceback_text = traceback.format_exc()
        total.append({"module": "socialscan"})
        total.append({"param": email})
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
    logger.info(f"SocialScan - Response in {toc - tic:0.4f} seconds")

    return total


def output(data):
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    email = sys.argv[1]
    result = t_socialscan(email)
    output(result)
