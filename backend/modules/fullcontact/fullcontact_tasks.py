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
    # from factories.fontcheat import fontawesome_cheat, search_icon
    from factories.fontcheat import fontawesome_cheat_5, search_icon_5
    from celery.utils.log import get_task_logger
    celery = create_celery(create_application())
except ImportError:
    # This is to test the module individually, and I know that is piece of shit
    sys.path.append('../../')
    from factories._celery import create_celery
    from factories.application import create_application
    from factories.configuration import api_keys_search
    # from factories.fontcheat import fontawesome_cheat, search_icon
    from factories.fontcheat import fontawesome_cheat_5, search_icon_5
    from celery.utils.log import get_task_logger
    celery = create_celery(create_application())

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

logger = get_task_logger(__name__)

# Compatibility code
try:
    # Python 2: "unicode" is built-in
    unicode
except NameError:
    unicode = str


@celery.task
def t_fullcontact(email):
    username = email.split("@")[0]
    key = api_keys_search('fullcontact_api')
    if key and len(key) < 20:
        req = requests.get(
            "https://api.fullcontact.com/v2/person.json?email=%s"
            % email, headers={"X-FullContact-APIKey": key})
        raw_node = json.loads(unicode(req.text))
        print(json.dumps(raw_node, ensure_ascii=True, indent=2))
    elif key and len(key) > 20:
        s = requests.Session()
        headers = {'Authorization': 'Bearer ' + key}
        data = json.dumps({
                "email": email
        })
        req = s.post("https://api.fullcontact.com/v3/person.enrich",
                     data=data,
                     headers=headers)

        raw_node = json.loads(unicode(req.text))
        print(json.dumps(raw_node, ensure_ascii=True, indent=2))
    else:
        raw_node = {"status": 400,
                    "message": "400: No access token"}

    # with open('km.json', 'r') as f:
    #     raw_node = json.load(f)

    # print(json.dumps(raw_node, ensure_ascii=True, indent=2))
    # exit()

    # Total
    total = []
    total.append({'module': 'fullcontact'})
    total.append({'param': email})
    total.append({'validation': 'hard'})

    # Icons unicode
    font_list = fontawesome_cheat_5()

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

    if (raw_node.get("status", "") != "" and (
         raw_node['status'] != 400 and raw_node['status'] != 401)):

        link_social = "Social"
        social_item = {"name-node": "Social", "title": "Social",
                       "subtitle": "", "icon": search_icon_5(
                           "child", font_list),
                       "link": link_social}
        socialp.append(social_item)
        link_photo = "Photos"
        photo_item = {"name-node": "Photos", "title": "Photos",
                      "subtitle": "", "icon": search_icon_5(
                           "camera-retro", font_list),
                      "link": link_photo}
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
                                     # 'icon': 'fa-building',
                                     'desc': org.get("title", "")})
                if (org.get("endDate", "") != ""):
                    timeline.append({'action': 'End : ' + org.get("name", ""),
                                     'date': org.get("endDate", "")
                                     .replace("-", "/"),
                                     # 'icon': 'fa-ban',
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

                fa_icon = search_icon_5(social.get("typeId", ""), font_list)
                if (fa_icon is None):
                    fa_icon = search_icon_5("question", font_list)

                social_item = {"name-node": social.get("typeName", ""),
                               "title": social.get("typeName", ""),
                               "subtitle": subtitle,
                               "icon": fa_icon,
                               "link": link_social}
                socialp.append(social_item)
                social_profile_item = {
                                       "name": social.get("type"),
                                       "icon": fa_icon,
                                       "source": "Fullcontact",
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
                if (social.get("typeId", "") == "instagram"):
                    inst_user = username
                    if (social.get("username", "") != ""):
                        inst_user = social.get("username", "")
                    elif (social.get("url", "") != ""):
                        inst_user = social.get("url", "").split("/")[-1]
                    tasks.append({"module": "instagram",
                                 "param": inst_user})

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
        if (bios != []):
            graphic.append({'bios': bios})
        if (len(photo) > 1):
            graphic.append({'photo': photo})
        if (webs != []):
            graphic.append({'webs': webs})
        if (footprint != []):
            graphic.append({'footprint': footprint})
        if (social_profile != []):
            profile.append({'social': social_profile})
        total.append({'graphic': graphic})
        if (profile != []):
            total.append({'profile': profile})
        if (timeline != []):
            total.append({'timeline': timeline})
        if (tasks != []):
            total.append({'tasks': tasks})

    elif (raw_node.get("status", "") == ""):
        link_social = "Social"
        social_item = {"name-node": "Social", "title": "Social",
                       "subtitle": "", "icon": search_icon_5(
                           "child", font_list),
                       "link": link_social}
        socialp.append(social_item)
        link_photo = "Photos"
        photo_item = {"name-node": "Photos", "title": "Photos",
                      "subtitle": "", "icon": search_icon_5(
                           "camera-retro", font_list),
                      "link": link_photo}
        photo.append(photo_item)

        if (raw_node.get("details", "") != ""):
            if (raw_node.get("details", "").get("name", "") != ""):
                profile_item = {'name': raw_node.get("details", "")
                                .get("name", "").get("full", "")}
                profile.append(profile_item)
                profile_item = {'firstName': raw_node.get("details", "")
                                .get("name", "").get("given", "")}
                profile.append(profile_item)
                profile_item = {'lastName': raw_node.get("details", "")
                                .get("name", "").get("family", "")}
                profile.append(profile_item)

                for web in raw_node.get("details", "").get("urls", ""):
                    webs.append({'url': web.get("value", "")})

            company = []
            for org in raw_node.get("details", "").get("employment", ""):
                company_item = {'name': org.get("name", ""),
                                'title': org.get("title", "")}
                company.append(company_item)

            if (company != []):
                profile_item = {'organization': company}
                profile.append(profile_item)

            print(" ")
            for social in raw_node.get("details", "").get("profiles", ""):
                rrss = raw_node.get("details", "").get("profiles", "")[social]
                username = rrss.get("url", "").split("/")[-1]
                fa_icon = search_icon_5(rrss.get("service", ""), font_list)
                if (fa_icon is None):
                    fa_icon = search_icon_5("question", font_list)
                social_item = {"name-node": rrss.get("service", ""),
                               "title": rrss.get("service", ""),
                               "subtitle": username,
                               "icon": fa_icon,
                               "link": link_social}
                socialp.append(social_item)
                social_profile_item = {
                                       "name": rrss.get("service"),
                                       "username": username,
                                       "url": rrss.get("url")}
                social_profile.append(social_profile_item)
                print(username)

                if (rrss.get("bio", "") != ""):
                    bios.append(rrss.get("bio", ""))

                # Prepare other tasks
                if (rrss.get("service", "") == "twitter"):
                    tasks.append({"module": "twitter",
                                 "param": username})
                # if (rrss.get("service", "") == "linkedin"):
                #     tasks.append({"module": "linkedin",
                #                  "param": username})

            for location in raw_node.get("details", "").get("locations", ""):
                if (location.get("city", "") != ""):
                    profile_item = {'location': location.get("city", "")}
                    profile.append(profile_item)
                if (location.get("region", "") != ""):
                    profile_item = {'location': location.get("region", "")}
                    profile.append(profile_item)
                if (location.get("country", "") != ""):
                    profile_item = {'location': location.get("country", "")}
                    profile.append(profile_item)
                if (location.get("formatted", "") != ""):
                    profile_item = {'location': location.get("formatted", "")}
                    profile.append(profile_item)

            for photos in raw_node.get("photos", ""):
                photo_item = {"name-node": photos.get("label", ""),
                              "title": photos.get("label", ""),
                              "subtitle": "",
                              "picture": photos.get("value", ""),
                              "link": link_photo}
                photo.append(photo_item)
                photo_profile.append(photo_item)
            if (photo_profile != []):
                profile_item = {'photos': photo_profile}
                profile.append(profile_item)

        total.append({'raw': raw_node})
        graphic.append({'social': socialp})
        if (bios != []):
            graphic.append({'bios': bios})
        if (len(photo) > 1):
            graphic.append({'photo': photo})
        # if (webs != []):
        #     graphic.append({'webs': webs})
        if (footprint != []):
            graphic.append({'footprint': footprint})
        if (social_profile != []):
            profile.append({'social': social_profile})
        total.append({'graphic': graphic})
        if (profile != []):
            total.append({'profile': profile})
        if (timeline != []):
            total.append({'timeline': timeline})
        if (tasks != []):
            total.append({'tasks': tasks})

    else:
        total.append({'raw': raw_node})
        link_social = "Social"
        social_item = {"name-node": "Social", "title": "Social",
                       "subtitle": "", "icon": search_icon_5(
                           "child", font_list),
                       "link": link_social}
        socialp = []
        graphic = []
        socialp.append(social_item)
        graphic.append({'social': socialp})
        total.append({'graphic': graphic})

    return total


def output(data):
    print(json.dumps(data, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    email = sys.argv[1]
    result = t_fullcontact(email)
    output(result)
