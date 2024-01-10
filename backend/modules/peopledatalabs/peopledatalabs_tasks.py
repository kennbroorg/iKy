#!/usr/bin/env json.dump(raw_node, f)
# -*- encoding: utf-8 -*-

import os
import sys
import json
import time
import requests
import random
from peopledatalabs import PDLPY
import traceback


try:
    from factories._celery import create_celery
    from factories.application import create_application
    from factories.configuration import api_keys_search
    from factories.fontcheat import fontawesome_cheat_5, search_icon_5
    from factories.iKy_functions import location_geo
    from celery.utils.log import get_task_logger
    celery = create_celery(create_application())
except ImportError:
    # This is to test the module individually, and I know that is piece of shit
    sys.path.append('../../')
    from factories._celery import create_celery
    from factories.application import create_application
    from factories.configuration import api_keys_search
    from factories.fontcheat import fontawesome_cheat_5, search_icon_5
    from factories.iKy_functions import location_geo
    from celery.utils.log import get_task_logger
    celery = create_celery(create_application())

logger = get_task_logger(__name__)


def p_peopledatalabs(email):
    """ Task of Celery that get info from peopledatalabs """

    # Code to develop the frontend without burning APIs
    cd = os.getcwd()
    td = os.path.join(cd, "outputs")
    output = "output-peopledatalabs.json"
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
    raw_node = []

    key = api_keys_search('peopledatalabs_key')

    if (not key):
        raise Exception("iKy - Missing or invalid Key")

    # Create a client, specifying your API key
    CLIENT = PDLPY(
        api_key=key,
    )

    # Create a parameters JSON object
    PARAMS = {
        "email": [email] 
    }

    # Pass the parameters object to the Person Enrichment API
    json_response = CLIENT.person.enrichment(**PARAMS).json()

    # Check for successful response
    if json_response["status"] != 200:
        raise Exception(f"iKy - Enrichment unsuccessful. See error and try again. Desc: {json_response}")

    raw_node = json_response['data']

    # Save enrichment data to JSON file
    # with open("my_pdl_enrichment.jsonl", "w") as out:
    #     out.write(json.dumps(raw_node) + "\n")

    # Total
    total = []
    total.append({'module': 'peopledatalabs'})
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

    # datalabs Array
    datalabs = []

    company = []

    link_social = "Social"
    social_item = {"name-node": "Social", "title": "Social",
                   "subtitle": "", "icon": "fas fa-user",
                   "link": link_social}
    socialp.append(social_item)

    link_data = "DataLab"
    data_item = {"name-node": "DataLab", "title": "DataLab",
                 "subtitle": "",
                 "icon": "fas fa-info-circle",
                 "link": link_data}
    datalabs.append(data_item)

    data = raw_node
    if (data.get("job_company_name", "") != "") and (data.get("job_company_name", "") != None):

        data_item = {"name-node": "DataCompany",
                     "title": "Company",
                     "subtitle": data.get("job_company_name", "").capitalize(),
                     "icon": "fas fa-people-carry",
                     "link": link_data}
        datalabs.append(data_item)

        # Profile
        company_item = {'name': data.get("job_company_name", "").capitalize(),
                        'title': data.get("job_title", "").capitalize(),
                        'start': data.get("job_start_date", ""),
                        'end': data.get("job_last_update", "")}
        company.append(company_item)
        profile_item = {'location': data.get(
            "job_company_location_name", "")}
        profile.append(profile_item)

        # Geolocalization
        geo_item = location_geo(data.get("job_company_location_name", ""), 
                                data.get("job_last_updated", ""))
        if(geo_item):
            profile.append({'geo': geo_item})

        # Timeline
        if (data.get("job_start_date", "")):
            timeline.append({'action': 'Start : ' + data.get("job_company_name", "").capitalize(),
                             'date': data.get("job_start_date", "")
                             .replace("-", "/"),
                             # 'icon': 'fa-building',
                             'desc': str(data.get("job_title", "")).capitalize() + " - Source PDL",
                             })
        if (data.get("end_date", "")):
            timeline.append({'action': 'End : ' + data.get("job_company_name", "").capitalize(),
                             'date': data.get("job_last_updated", "")
                             .replace("-", "/"),
                             # 'icon': 'fa-ban',
                             'desc': str(data.get("job_title", "")).capitalize() + " - Source PDL"})

    # Primary location
    if (data.get("location_name", "") != "") and (data.get("location_name", "") != None):

        data_item = {"name-node": "DataLocation",
                     "title": "Location",
                     "subtitle": data.get("location_name", ""),
                     "icon": "fas fa-globe-americas",
                     "link": link_data}
        datalabs.append(data_item)

        # Profile
        profile_item = {'location': data.get(
            "location_name", "")}
        profile.append(profile_item)

        # Geolocalization
        geo_item = location_geo(data.get("location_name", "").capitalize(), 
                                data.get("location_last_updated", ""))
        if(geo_item):
            profile.append({'geo': geo_item})

    # Primary name
    if (data.get("full_name", "") != "") and (data.get("full_name", "") != None):

        try:
            name_complete = data.get("first_name", "").capitalize() + " " + \
                            data.get("middle_name", "").capitalize() + " " + \
                            data.get("last_name", "").capitalize()
        except Exception:
            name_complete = data.get("first_name", "").capitalize() + " " + \
                            data.get("last_name", "").capitalize()

        data_item = {"name-node": "DataName",
                     "title": "Name",
                     "subtitle": name_complete,
                     "icon": "fas fa-signature",
                     "link": link_data}
        datalabs.append(data_item)

        # Profile
        profile_item = {'name': name_complete}
        profile.append(profile_item)

    # Primary industry
    if (data.get("industry", "") and (data.get("industry", "") != None)):
        data_item = {"name-node": "DataInsdustry",
                     "title": "Industry",
                     "subtitle": str(data.get("industry")).capitalize(),
                     "icon": "fas fa-briefcase",
                     "link": link_data}
        datalabs.append(data_item)

    # Primary birthdate
    if (data.get("birth_date", "") != "") and (data.get("birth_date", "") != None):

        data_item = {"name-node": "DataBirth",
                     "title": "Birthday",
                     "subtitle": data.get("birth_date", ""),
                     "icon": "fas fa-birthday-cake",
                     "link": link_data}
        datalabs.append(data_item)

        timeline.append({'action': 'BirthDay : ' + data.get("birth_date", "")})

    elif (data.get("birth_year", "") != "") and (data.get("birth_year", "") != None):

        data_item = {"name-node": "DataBirth",
                     "title": "BirthYear",
                     "subtitle": data.get("birth_year", ""),
                     "icon": "fas fa-birthday-cake",
                     "link": link_data}
        datalabs.append(data_item)

        timeline.append({'action': 'BirthYear : ' + data.get("birth_year", "")})

    # Gender
    if (data.get("gender", "") != "") and (data.get("gender", "") != None):

        temp = data.get("gender", "")

        if (temp == "male"):
            icon = "fas fa-mars"
        elif (temp == "female"):
            icon = "fas fa-venus"
        else:
            icon = "fas fa-genderless"

        data_item = {"name-node": "DataGener",
                     "title": "Gender",
                     "subtitle": temp,
                     "icon": icon,
                     "link": link_data}
        datalabs.append(data_item)

    # Emails profile
    if (data.get("emails", "") != "") and (data.get("emails", "") != None):
        for mail in data.get("emails", ""):
            profile_item = {'email': mail['address']}
            profile.append(profile_item)
            # data_item = {"name-node": "DataWEmail" + str(e),
            #              "title": mail.get("type"),
            #              "subtitle": mail.get("address"),
            #              "icon": "fas fa-at",
            #              "link": link_data}
            # datalabs.append(data_item)

    # Profiles RRSS
    if (data.get("profiles", "") != "") and (data.get("profiles", "") != None):
        for social in data.get("profiles", ""):
            if (social.get("username", "")):
                subtitle = social.get("username", "")
            else:
                subtitle = "Not identified"

            fa_icon = search_icon_5(social.get("network", ""), font_list)
            if (fa_icon is None):
                # fa_icon = search_icon_5("question", font_list)
                fa_icon = "far fa-user"

            social_item = {"name-node": social.get("network", ""),
                           "title": social.get("network", ""),
                           "subtitle": subtitle,
                           "icon": fa_icon,
                           "link": link_social}
            socialp.append(social_item)
            social_profile_item = {
                                   "name": social.get("network"),
                                   "icon": fa_icon,
                                   "source": "PeopleDataLabs",
                                   "username": social.get("username"),
                                   "url": social.get("url")}
            social_profile.append(social_profile_item)

            tasks.append({"module": social.get("network", "").lower(),
                         "param": social.get("username", "")})

        profile.append({'social': social_profile})

    # Profiles phones
    if (data.get("phone_numbers", "") != "") and (data.get("phone_numbers", "") != None):
        for phone in data.get("phone_numbers", ""):
            profile_item = {'phone': phone}
            profile.append(profile_item)

    # Profiles location
    if (data.get("location_names", "") != "") and (data.get("location_names", "") != None):
        for location in data.get("location_names", ""):
            profile_item = {'location': location.capitalize()}
            profile.append(profile_item)

            # Geolocalization
            geo_item = location_geo(location)
            if(geo_item):
                profile.append({'geo': geo_item})

    total.append({'raw': raw_node})
    graphic.append({'data': datalabs})
    graphic.append({'social': socialp})
    total.append({'graphic': graphic})
    if (profile != []):
        total.append({'profile': profile})
    if (timeline != []):
        total.append({'timeline': timeline})
    if (tasks != []):
        total.append({'tasks': tasks})

    return total


@celery.task
def t_peopledatalabs(email, from_m="Initial"):
    total = []
    tic = time.perf_counter()
    try:
        total = p_peopledatalabs(email)
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
        total.append({'module': 'peopledatalabs'})
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
    logger.info(f"PeopleDataLabs - Response in {toc - tic:0.4f} seconds")

    return total


def output(data):
    print(json.dumps(data, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    email = sys.argv[1]
    result = t_peopledatalabs(email)
    output(result)
