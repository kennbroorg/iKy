#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import sys
import json
import requests
import urllib

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

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

logger = get_task_logger(__name__)


@celery.task
def t_leaklookup(email):
    """ Task of Celery that get info from leak-lookup.com """

    key = ""
    url = "https://leak-lookup.com/api/search"
    key = api_keys_search('leaklookup_key')

    payload = {"key": key, "type": "email_address", "query": email}
    req = requests.post(url, headers={'User-Agent': 'iKy'}, data=payload,
                        timeout=30)
    email_response = req.json()

    leak_email = []
    if (email_response['error'] == 'false'):
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


def output(data):
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    username = sys.argv[1]
    result = t_leaklookup(username)
    output(result)
