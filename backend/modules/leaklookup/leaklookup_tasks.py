#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import os
import sys
import json
import time
import requests
# import urllib
import traceback

try:
    from factories._celery import create_celery
    from factories.application import create_application
    from factories.configuration import api_keys_search
    from celery.utils.log import get_task_logger
    celery = create_celery(create_application())
except ImportError:
    # This is to test the module individually, and I know that is piece of shit
    sys.path.append('../../')
    from factories._celery import create_celery
    from factories.application import create_application
    from factories.configuration import api_keys_search
    from celery.utils.log import get_task_logger
    celery = create_celery(create_application())

# from requests.packages.urllib3.exceptions import InsecureRequestWarning
# requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

logger = get_task_logger(__name__)


def p_leaklookup(email):
    """ Task of Celery that get info from leak-lookup.com """

    # Code to develop the frontend without burning APIs
    cd = os.getcwd()
    td = os.path.join(cd, "outputs")
    output = "output-leaklookup.json"
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
    url = "https://leak-lookup.com/api/search"
    key = api_keys_search('leaklookup_key')

    if (not key):
        raise Exception("iKy - Missing or invalid Key")

    payload = {"key": key, "type": "email_address", "query": email}
    req = requests.post(url, headers={'User-Agent': 'iKy'}, data=payload,
                        timeout=30)
    email_response = req.json()

    leak_email = []
    if (email_response['error'] == 'false'):
        if (len(email_response['message']) == 0):
            raise Exception("iKy - No leak found")
        for leak in email_response['message']:
            if (len(email_response['message'][leak]) > 0):
                for details in email_response['message'][leak]:
                    detail = []
                    for d in details:
                        detail.append({"name": d, "value": details[d]})
                    leak_email.append({"name": leak,
                                       "value": detail})

            else:
                leak_email.append({"name": leak,
                                   "value": [{"name": "API",
                                              "value":
                                              "Public, try Private"}]})
    else:
        raise Exception("iKy - Leaklookup API Error")
        

    # TODO: Add user request
    # Total
    total = []
    total.append({'module': 'leaklookup'})
    total.append({'param': email})
    total.append({'validation': 'hard'})

    # Graphic Array
    graphic = []

    # Profile Array
    profile = []

    # Timeline Array
    timeline = []

    total.append({'raw': email_response})
    graphic.append({'email': leak_email})
    total.append({'graphic': graphic})
    total.append({'profile': profile})
    total.append({'timeline': timeline})

    return total


@celery.task
def t_leaklookup(email):
    total = []
    tic = time.perf_counter()
    try:
        total = p_leaklookup(email)
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
        total.append({'module': 'leaklookup'})
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
    logger.info(f"Lealookup - Response in {toc - tic:0.4f} seconds")

    return total


def output(data):
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    username = sys.argv[1]
    result = t_leaklookup(username)
    output(result)
