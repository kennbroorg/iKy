#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import os
import sys
import traceback
import json
import time

import trio
import httpx
import holehe.core

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


async def p_holehe(email, from_m):

    # Code to develop the frontend without burning APIs
    cd = os.getcwd()
    td = os.path.join(cd, "outputs")
    output = "output-holehe.json"
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
    # holehe.core.is_mail(email)

    modules = holehe.core.import_submodules("holehe.modules")
    websites = holehe.core.get_functions(modules)

    client = httpx.AsyncClient(timeout=60)
    out = []
    async with trio.open_nursery() as nursery:
        for website in websites:
            nursery.start_soon(holehe.core.launch_module, website, email, 
                               client, out)
            # nursery.start_soon(website, email, client, out)
    raw_node = sorted(out, key=lambda i: i['name'])  # We sort by modules names
    await client.aclose()

    # Total
    total = []
    total.append({'module': 'holehe'})
    total.append({'param': email})
    total.append({'validation': 'hard'})

    # Icons unicode
    font_list = fontawesome_cheat_5()

    # Graphic Array
    graphic = []

    # Profile Array
    profile = []

    # Timeline Array
    timeline = []

    # Gather Array
    gather = []
    lists = []

    # Social
    social = []

    link = "Holehe"
    gather_item = {"name-node": "Holehe", "title": "Holehe",
                   "subtitle": email, "icon": "fas fa-at",
                   "link": link}
    gather.append(gather_item)

    for rrss in raw_node:
        lists_item = {"title": rrss['name'],
                      "exists": rrss['exists'],
                      "rateLimit": rrss['rateLimit'],
                      "emailrecovery": rrss['emailrecovery'],
                      "phoneNumber": rrss['phoneNumber'],
                      "others": rrss['others']}
        lists.append(lists_item)
        if (rrss['exists'] == True):
            fa_icon = search_icon_5(rrss['name'], font_list)
            if (fa_icon is None):
                fa_icon = search_icon_5("dot-circle", font_list)

            gather_item = {"name-node": rrss['name'],
                           "title": rrss['name'],
                           "icon": fa_icon,
                           "link": link}
            gather.append(gather_item)
            social_item = {"name": rrss['name'],
                           "url": "Not Determined",
                           "icon": fa_icon,
                           "source": "holehe",
                           "username": email}
            social.append(social_item)
    profile.append({"social": social})

    total.append({'raw': raw_node})
    graphic.append({'holehe': gather})
    graphic.append({'lists': lists})
    total.append({'graphic': graphic})
    total.append({'profile': profile})
    total.append({'timeline': timeline})

    return total


@celery.task
def t_holehe(email, from_m="initial"):
    total = []
    tic = time.perf_counter()
    try:
        total = trio.run(p_holehe, email, from_m)
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
        total.append({'module': 'holehe'})
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
    logger.info(f"Holehe - Response in {toc - tic:0.4f} seconds")

    return total


def output(data):
    print(json.dumps(data, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    email = sys.argv[1]
    result = t_holehe(email, "initial")
    output(result)
