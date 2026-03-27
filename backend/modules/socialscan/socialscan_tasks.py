#!/usr/bin/env python

import argparse
import json

from celery.utils.log import get_task_logger
from factories.fontcheat import search_icon_5
from factories.task_wrapper import iky_task
from socialscan.util import sync_execute_queries

logger = get_task_logger(__name__)


@iky_task(module_name="socialscan")
def p_socialscan(email, from_m="Initial"):
    """Task of Celery that get info from socialscan."""

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

    for result in res_email:
        if not result.available:
            fa_icon = search_icon_5(str(result.platform))
            if fa_icon is None:
                fa_icon = search_icon_5("question")

            social_item = {
                "name-node": "SC" + str(result.platform),
                "title": str(result.platform),
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

    for result in res_user:
        if not result.available:
            fa_icon = search_icon_5(str(result.platform))
            if fa_icon is None:
                fa_icon = search_icon_5("question")

            social_item = {
                "name-node": "SCE" + str(result.platform),
                "title": str(result.platform),
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


# Backward-compatible alias: existing code references t_socialscan
t_socialscan = p_socialscan


def output(data):
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Query socialscan for email/username registration"
    )
    parser.add_argument("email", help="Email address to look up")
    args = parser.parse_args()

    result = t_socialscan(args.email)
    output(result)
