#!/usr/bin/env python

import argparse
import json

import holehe.core
import httpx
import trio
from celery.utils.log import get_task_logger
from factories.fontcheat import search_icon_5
from factories.task_wrapper import iky_task

logger = get_task_logger(__name__)


async def _holehe_query(email):
    """Run holehe modules asynchronously via trio and return sorted results."""
    modules = holehe.core.import_submodules("holehe.modules")
    websites = holehe.core.get_functions(modules)

    client = httpx.AsyncClient(timeout=60)
    out = []
    async with trio.open_nursery() as nursery:
        for website in websites:
            nursery.start_soon(holehe.core.launch_module, website, email, client, out)
    await client.aclose()
    return sorted(out, key=lambda i: i["name"])


@iky_task(module_name="holehe", dev_mode_sleep=15)
def p_holehe(email, from_m="initial"):
    """Task of Celery that get info from holehe."""

    # Run async holehe query synchronously via trio
    raw_node = trio.run(_holehe_query, email)

    # Total
    total = []
    total.append({"module": "holehe"})
    total.append({"param": email})
    total.append({"validation": "hard"})

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
    gather_item = {
        "name-node": "Holehe",
        "title": "Holehe",
        "subtitle": email,
        "icon": "fas fa-at",
        "link": link,
    }
    gather.append(gather_item)

    for rrss in raw_node:
        lists_item = {
            "title": rrss["name"],
            "exists": rrss["exists"],
            "rateLimit": rrss["rateLimit"],
            "emailrecovery": rrss["emailrecovery"],
            "phoneNumber": rrss["phoneNumber"],
            "others": rrss["others"],
        }
        lists.append(lists_item)
        if rrss["exists"] is True:
            fa_icon = search_icon_5(rrss["name"])
            if fa_icon is None:
                fa_icon = search_icon_5("dot-circle")

            gather_item = {
                "name-node": rrss["name"],
                "title": rrss["name"],
                "icon": fa_icon,
                "link": link,
            }
            gather.append(gather_item)
            social_item = {
                "name": rrss["name"],
                "url": "Not Determined",
                "icon": fa_icon,
                "source": "holehe",
                "username": email,
            }
            social.append(social_item)
    profile.append({"social": social})

    total.append({"raw": raw_node})
    graphic.append({"holehe": gather})
    graphic.append({"lists": lists})
    total.append({"graphic": graphic})
    total.append({"profile": profile})
    total.append({"timeline": timeline})

    return total


# Backward-compatible alias: existing code references t_holehe
t_holehe = p_holehe


def output(data):
    print(json.dumps(data, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Query holehe for email registration on sites"
    )
    parser.add_argument("email", help="Email address to look up")
    args = parser.parse_args()

    result = t_holehe(args.email, "initial")
    output(result)
