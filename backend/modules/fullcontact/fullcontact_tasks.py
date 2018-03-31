#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import sys 
import json
import requests

try : 
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
def t_fillcontact(email):
    key = api_keys_search('fullcontact_api')
    if key:
        req = requests.get("https://api.fullcontact.com/v2/person.json?email=%s" % email, headers={"X-FullContact-APIKey": key})
        raw_node = json.loads(req.content)
    else:
        raw_node = []

    # Icons unicode
    font_list = fontawesome_cheat()
    # Total
    total = []
    total.append({'module': 'fullcontact'})

    # if (raw_node == []) or (raw_node['message'] != 'Not Found'):
    if (raw_node != []):
        # Gather Array
        gather = []

        # Photo Array
        photo = []

        # Web Array
        webs = []

        # Profile Array
        profile = []

        link_social = "Social"
        gather_item = {"name-node": "Social", "title": "Social", 
            "subtitle": "", "icon": u'\uf1ae', "link": link_social}
        gather.append(gather_item)
        link_photo = "Photos"
        photo_item = {"name-node": "Photos", "title": "Photos", 
            "subtitle": "", "icon": u'\uf083', "link": link_photo}
        photo.append(photo_item)

        if raw_node.get("status", "") == 200:

            if (raw_node.get("contactInfo", "") != ""):
                profile_item = {'name': raw_node.get("contactInfo", "").get('fullName', '')}
                profile.append(profile_item)
                profile_item = {'firstName': raw_node.get("contactInfo", "").get('givenName', '')}
                profile.append(profile_item)
                profile_item = {'lastName': raw_node.get("contactInfo", "").get('familyName', '')}
                profile.append(profile_item)

                webs = []
                for web in raw_node.get("contactInfo", "").get("websites", ""):
                    webs.append({'url': web.get("url", "")})

                # TODO : Find examples 
                # if (raw_node.get("contactInfo", "").get('chats', '') != ""):

            company = []
            for org in raw_node.get("organizations", ""):
                company_item = {'name': org.get("name",""), 
                    'title': org.get("title",""),
                    'start': org.get("startDate", ""),
                    'end': org.get("endDate","")}
                company.append(company_item)

            if (company != []):
                profile_item = {'company': company}
                profile.append(profile_item)


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
                if (fa_icon == None):
                    fa_icon = search_icon("question", font_list)

                gather_item = {"name-node": social.get("typeName", ""), 
                        "title": social.get("typeName", ""), 
                        "subtitle": subtitle, 
                        "icon": fa_icon, 
                        "link": link_social}
                gather.append(gather_item)

            # TODO : Collect all Bios for profile

            if (raw_node.get("demographics", "") != ""):
                if (raw_node.get("demographics", "") \
                    .get("locationDeduced", "") != ""):
                    if (raw_node.get("demographics", "") \
                        .get("locationDeduced", "") \
                        .get("deducedLocation", "") != ""):
                        profile_item = {'location': raw_node.get("demographics", "").get("locationDeduced", "").get("deducedLocation", "")}
                        profile.append(profile_item)
                elif (raw_node.get("demographics", "").get("locationGeneral", "") != ""):
                    profile_item = {'location': raw_node.get("demographics", "").get("locationGeneral", "")}
                    profile.append(profile_item)

                if (raw_node.get("demographics", "").get("gender", "") != ""):
                    profile_item = {'gender': raw_node.get("demographics", "").get("gender", "")}
                    profile.append(profile_item)

            photo_profile = []
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
        total.append({'social': gather})
        total.append({'photo': photo})
        if (webs != []):
            total.append({'webs': webs})
        total.append({'profile': profile})

    return total


def output(data):
    print json.dumps(data, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    email = sys.argv[1]
    result = t_fillcontact(email)
    output(result)
