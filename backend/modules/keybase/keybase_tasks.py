#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import sys
import json
import requests
import time

try:
    from factories._celery import create_celery
    from factories.application import create_application
    from factories.fontcheat import fontawesome_cheat, search_icon
    from celery.utils.log import get_task_logger
    celery = create_celery(create_application())
except ImportError:
    # This is to test the module individually, and I know that is piece of shit
    sys.path.append('../../')
    from factories._celery import create_celery
    from factories.application import create_application
    from factories.fontcheat import fontawesome_cheat, search_icon
    from celery.utils.log import get_task_logger
    celery = create_celery(create_application())

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

logger = get_task_logger(__name__)


@celery.task
def t_keybase(username, from_m):
    url = "https://keybase.io/_/api/1.0/user/lookup.json?" + \
          "usernames=%s" % username
    req = requests.get(url)
    raw_node = json.loads(req.text)

    # Keybase : TODO : Validation via some info
    # Keybase : TODO : Get Followers and Following throw crawling

    # Icons unicode
    font_list = fontawesome_cheat()
    # Total
    total = []
    total.append({'module': 'keybase'})
    total.append({'param': username})
    # Evaluates the module that executed the task
    if (from_m == 'Initial'):
        total.append({'validation': 'no'})
    else:
        total.append({'validation': 'soft'})

    if (raw_node['status']['code'] == 0) and (raw_node['them'][0] is not None):
        raw = raw_node['them'][0]

        # Graphic Array
        graphic = []

        # Profile Array
        profile = []
        social_profile = []

        # Timeline Array
        timeline = []

        # Tasks Array
        # tasks = []

        # Devices Array
        devices = []

        # Social Array
        social = []

        link_device = "Devices"
        device_item = {"name-node": "Devices", "title": "Devices",
                       "subtitle": "", "icon": u'\uf10c', "link": link_device}
        devices.append(device_item)

        link_social = "KeybaseSocial"
        social_item = {"name-node": "KeybaseSocial", "title": "KeybaseSocial",
                       "subtitle": "", "icon": u'\uf1ae', "link": link_social}
        social.append(social_item)

        if (raw.get("profile", "") != ""):
            if (raw.get("profile", "").get("full_name", "") != ""):
                profile_item = {'name': raw.get("profile", "")
                                .get("full_name", "")}
                profile.append(profile_item)
            if (raw.get("profile", "").get("location", "") != ""):
                profile_item = {'location': raw.get("profile", "")
                                .get("location", "")}
                profile.append(profile_item)
            if (raw.get("profile", "").get("bio", "") != ""):
                profile_item = {'bio': raw.get("profile", "").get("bio", "")}
                profile.append(profile_item)

        if (raw.get("basics", "") != ""):
            if (raw.get("basics", "").get("ctime", "") != ""):
                ctime = time.strftime('%Y/%m/%d %H:%M:%S',
                                      time.gmtime(raw.get("basics", "")
                                                  .get("ctime")))
                timeline_item = {"action": "Keybase: Create Account",
                                 "date": ctime, "icon": "fa-key"}
                timeline.append(timeline_item)
            if (raw.get("basics", "").get("mtime", "") != ""):
                mtime = time.strftime('%Y/%m/%d %H:%M:%S',
                                      time.gmtime(raw.get("basics", "")
                                                  .get("mtime")))
                timeline_item = {"action": "Keybase : Update Account",
                                 "date": mtime, "icon": "fa-key"}
                timeline.append(timeline_item)

        # Keybase : TODO : picture in profile

        for dev in raw.get("devices", ""):

            print(dev)
            print(" Type ", raw.get("devices").get(dev).get("type", ""))
            fa_icon = search_icon(raw.get("devices").get(dev).get("type", ""),
                                  font_list)
            if (fa_icon is None):
                fa_icon = search_icon("question", font_list)

            device_item = {"name-node": raw.get("devices").get(dev)
                           .get("type", ""),
                           "title": raw.get("devices").get(dev)
                           .get("type", ""),
                           "subtitle": "Name : " + raw.get("devices").get(dev)
                           .get("name", ""),
                           "icon": fa_icon,
                           "link": link_device}
            devices.append(device_item)

        if (raw.get("proofs_summary", "") != ""):
            for soc in raw.get("proofs_summary", "").get("all"):
                fa_icon = search_icon(soc.get("proof_type"), font_list)
                if (fa_icon is None):
                    fa_icon = search_icon("question", font_list)

                social_item = {"name-node": "keybase" +
                               soc.get("proof_type", ""),
                               "title": soc.get("proof_type", ""),
                               "subtitle": soc.get("nametag", ""),
                               "icon": fa_icon,
                               "link": link_social}
                social.append(social_item)

                social_profile_item = {"name": soc.get("proof_type"),
                                       "username": soc.get("nametag"),
                                       "url": soc.get("service_url")}
                social_profile.append(social_profile_item)

        # Keybase : TODO : Find an example of webs and
        # Keybase : TODO : Find an example of cryptocurrency_addresses and

        total.append({'raw': raw_node})
        if (len(social) > 1):
            graphic.append({'keysocial': social})
        if (len(devices) > 1):
            graphic.append({'devices': devices})
        total.append({'graphic': graphic})
        if (social_profile != []):
            profile.append({'social': social_profile})
        if (profile != []):
            total.append({'profile': profile})
        if (timeline != []):
            total.append({'timeline': timeline})

    # Keybase : TODO : Before send task,
    # code the validation for duplicate proccess
    # if (tasks != []):
    #     total.append({'tasks': tasks})

    return total


def output(data):
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    username = sys.argv[1]
    result = t_keybase(username)
    output(result)
