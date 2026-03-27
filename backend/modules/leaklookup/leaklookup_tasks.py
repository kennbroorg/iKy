#!/usr/bin/env python

import argparse
import json

import requests
from celery.utils.log import get_task_logger
from factories.configuration import api_keys_search
from factories.task_wrapper import iky_task

logger = get_task_logger(__name__)


@iky_task(module_name="leaklookup")
def p_leaklookup(email):
    """Task of Celery that get info from leak-lookup.com"""

    # Code
    url = "https://leak-lookup.com/api/search"
    key = api_keys_search("leaklookup_key")

    if not key:
        raise Exception("iKy - Missing or invalid Key")

    payload = {"key": key, "type": "email_address", "query": email}
    req = requests.post(url, headers={"User-Agent": "iKy"}, data=payload, timeout=30)
    email_response = req.json()

    leak_email = []
    if email_response["error"] == "false":
        if len(email_response["message"]) == 0:
            raise Exception("iKy - No leak found")
        for leak in email_response["message"]:
            if len(email_response["message"][leak]) > 0:
                for details in email_response["message"][leak]:
                    detail = []
                    for d in details:
                        detail.append({"name": d, "value": details[d]})
                    leak_email.append({"name": leak, "value": detail})
            else:
                leak_email.append(
                    {
                        "name": leak,
                        "value": [{"name": "API", "value": "Public, try Private"}],
                    }
                )
    else:
        raise Exception("iKy - Leaklookup API Error")

    # Total
    total = []
    total.append({"module": "leaklookup"})
    total.append({"param": email})
    total.append({"validation": "hard"})

    # Graphic Array
    graphic = []

    # Profile Array
    profile = []

    # Timeline Array
    timeline = []

    total.append({"raw": email_response})
    graphic.append({"email": leak_email})
    total.append({"graphic": graphic})
    total.append({"profile": profile})
    total.append({"timeline": timeline})

    return total


# Backward-compatible alias: existing code references t_leaklookup
t_leaklookup = p_leaklookup


def output(data):
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Query leak-lookup.com for email leaks"
    )
    parser.add_argument("email", help="Email address to look up")
    args = parser.parse_args()

    result = t_leaklookup(args.email)
    output(result)
