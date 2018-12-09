#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import sys
import json
import requests
# import urllib3

try:
    from factories._celery import create_celery
    from factories.application import create_application
    from factories.configuration import api_keys_search
    from factories.fontcheat import fontawesome_cheat, search_icon
    from celery.utils.log import get_task_logger
    celery = create_celery(create_application())
except ImportError:
    # This is to test the module individually, and I know that is piece of shit
    sys.path.append('../../')
    from factories._celery import create_celery
    from factories.application import create_application
    from factories.configuration import api_keys_search
    from factories.fontcheat import fontawesome_cheat, search_icon
    from celery.utils.log import get_task_logger
    celery = create_celery(create_application())

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

logger = get_task_logger(__name__)


@celery.task
def t_fullcontact(email):
    key = api_keys_search('fullcontact_api')
    if key:
        req = requests.get(
            "https://api.fullcontact.com/v2/person.json?email=%s"
            % email, headers={"X-FullContact-APIKey": key})
        raw_node = json.loads(req.content)
    else:
        raw_node = []

    # Icons unicode
    font_list = fontawesome_cheat()
    # Total
    total = []
    total.append({'module': 'fullcontact'})
    total.append({'param': email})
    total.append({'validation': 'soft'})

    if (raw_node != []):
        # Graphic Array
        graphic = []

        # Profile Array
        profile = []

        # Tasks Array
        tasks = []

        # Timeline Array
        timeline = []

        # Social Array
        socialp = []
        social_profile = []

        # Photo Array
        photo = []
        photo_profile = []

        # footprint Array
        footprint = []

        # Web Array
        webs = []

        # Bios Array
        bios = []

        link_social = "Social"
        social_item = {"name-node": "Social", "title": "Social",
                       "subtitle": "", "icon": u'\uf1ae', "link": link_social}
        socialp.append(social_item)
        link_photo = "Photos"
        photo_item = {"name-node": "Photos", "title": "Photos",
                      "subtitle": "", "icon": u'\uf083', "link": link_photo}
        photo.append(photo_item)

        if raw_node.get("status", "") == 200:

            if (raw_node.get("contactInfo", "") != ""):
                profile_item = {'name': raw_node.get("contactInfo", "")
                                .get('fullName', '')}
                profile.append(profile_item)
                profile_item = {'firstName': raw_node.get("contactInfo", "")
                                .get('givenName', '')}
                profile.append(profile_item)
                profile_item = {'lastName': raw_node.get("contactInfo", "")
                                .get('familyName', '')}
                profile.append(profile_item)

                for web in raw_node.get("contactInfo", "").get("websites", ""):
                    webs.append({'url': web.get("url", "")})

                # Fullcontact : TODO : Find examples
                # if (raw_node.get("contactInfo", "").get('chats', '') != ""):

            company = []
            for org in raw_node.get("organizations", ""):
                company_item = {'name': org.get("name", ""),
                                'title': org.get("title", ""),
                                'start': org.get("startDate", ""),
                                'end': org.get("endDate", "")}
                company.append(company_item)
                if (org.get("startDate", "") != ""):
                    timeline.append({'action': 'Start : ' + org
                                     .get("name", ""),
                                     'date': org.get("startDate", "")
                                     .replace("-", "/"),
                                     'icon': 'fa-building',
                                     'desc': org.get("title", "")})
                if (org.get("endDate", "") != ""):
                    timeline.append({'action': 'End : ' + org.get("name", ""),
                                     'date': org.get("endDate", "")
                                     .replace("-", "/"),
                                     'icon': 'fa-ban',
                                     'desc': org.get("title", "")})

            if (company != []):
                profile_item = {'organization': company}
                profile.append(profile_item)

            if (raw_node.get("digitalFootprint", "") != ""):
                for topics in raw_node.get("digitalFootprint").get(
                                           "topics", ""):
                    footprint.append({'label': topics.get("value")})

            for social in raw_node.get("socialProfiles", ""):
                if ((social.get("username", "") != "") and
                   (social.get("id", "") != "")):
                    subtitle = social.get("username", "") + \
                        " - " + social.get("id", "")
                elif (social.get("username", "") != ""):
                    subtitle = social.get("username", "")
                elif (social.get("id", "") != ""):
                    subtitle = social.get("id", "")
                else:
                    subtitle = "Not identified"

                fa_icon = search_icon(social.get("typeId", ""), font_list)
                if (fa_icon is None):
                    fa_icon = search_icon("question", font_list)

                social_item = {"name-node": social.get("typeName", ""),
                               "title": social.get("typeName", ""),
                               "subtitle": subtitle,
                               "icon": fa_icon,
                               "link": link_social}
                socialp.append(social_item)
                social_profile_item = {
                                       "name": social.get("type"),
                                       "username": social.get("username"),
                                       "url": social.get("url")}
                social_profile.append(social_profile_item)

                if (social.get("bio", "") != ""):
                    bios.append(social.get("bio", ""))

                # Fullcontact : TODO : Send all to tasks array with email as
                # param
                # Prepare other tasks
                if (social.get("typeId", "") == "github"):
                    tasks.append({"module": "github",
                                 "param": social.get("username", "")})
                if (social.get("typeId", "") == "keybase"):
                    tasks.append({"module": "keybase",
                                 "param": social.get("username", "")})
                if (social.get("typeId", "") == "twitter"):
                    tasks.append({"module": "twitter",
                                 "param": social.get("username", "")})
                if (social.get("typeId", "") == "linkedin"):
                    tasks.append({"module": "linkedin",
                                 "param": social.get("username", "")})

            if (raw_node.get("demographics", "") != ""):
                if (raw_node.get("demographics", "").get(
                                 "locationDeduced", "") != ""):
                    if (raw_node.get("demographics", "").get(
                        "locationDeduced", "").get(
                            "deducedLocation", "") != ""):
                        profile_item = {'location': raw_node.get(
                            "demographics", "").get(
                                "locationDeduced", "").get(
                                    "deducedLocation", "")}
                        profile.append(profile_item)
                elif (raw_node.get("demographics", "").get(
                      "locationGeneral", "") != ""):
                    profile_item = {'location': raw_node.get(
                        "demographics", "").get("locationGeneral", "")}
                    profile.append(profile_item)

                if (raw_node.get("demographics", "").get("gender", "") != ""):
                    profile_item = {'gender': raw_node.get(
                        "demographics", "").get("gender", "")}
                    profile.append(profile_item)

            for photos in raw_node.get("photos", ""):
                photo_item = {"name-node": photos.get("typeName", ""),
                              "title": photos.get("typeName", ""),
                              "subtitle": "",
                              "picture": photos.get("url", ""),
                              "link": link_photo}
                photo.append(photo_item)
                photo_profile.append(photo_item)
            if (photo_profile != []):
                profile_item = {'photos': photo_profile}
                profile.append(profile_item)

        total.append({'raw': raw_node})
        graphic.append({'social': socialp})
        graphic.append({'photo': photo})
        graphic.append({'webs': webs})
        graphic.append({'bios': bios})
        graphic.append({'footprint': footprint})
        profile.append({'social': social_profile})
        total.append({'graphic': graphic})
        if (profile != []):
            total.append({'profile': profile})
        if (timeline != []):
            total.append({'timeline': timeline})
        if (tasks != []):
            total.append({'tasks': tasks})

    return total


def output(data):
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    email = sys.argv[1]
    result = t_fullcontact(email)
    output(result)
