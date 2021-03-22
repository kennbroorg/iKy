#!/usr/bin/env json.dump(raw_node, f)
# -*- encoding: utf-8 -*-

import sys
import json
import requests
import random


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

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

logger = get_task_logger(__name__)


@celery.task
def t_peopledatalabs(email):
    """ Task of Celery that get info from peopledatalabs """

    raw_node = []
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
        'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
        'Mozilla/5.0 (Windows NT 5.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
        'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36',
        'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36',
        'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
        'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
        'Mozilla/4.0 (compatible; MSIE 9.0; Windows NT 6.1)',
        'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko',
        'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0)',
        'Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko',
        'Mozilla/5.0 (Windows NT 6.2; WOW64; Trident/7.0; rv:11.0) like Gecko',
        'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko',
        'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.0; Trident/5.0)',
        'Mozilla/5.0 (Windows NT 6.3; WOW64; Trident/7.0; rv:11.0) like Gecko',
        'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)',
        'Mozilla/5.0 (Windows NT 6.1; Win64; x64; Trident/7.0; rv:11.0) like Gecko',
        'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0)',
        'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)',
        'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729)'
    ]

    key = api_keys_search('peopledatalabs_key')

    if (not key):
        return {"status": 401,
                "error": {
                     "type": "authentication_error",
                     "message": "Request contained a missing or invalid key"
                }}

    headers = {'User-Agent': random.choice(user_agents)}

    api_version = "v5"
    url = "https://api.peopledatalabs.com/" + api_version + "/person"
    params = {"api_key": key, "email": [email]}
    
    req = requests.get(url,  params=params, headers=headers)
    raw_node = req.json()

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

    if (raw_node.get("status", "") == 200):

        link_social = "Social"
        social_item = {"name-node": "Social", "title": "Social",
                       "subtitle": "", "icon": search_icon_5(
                           "child", font_list),
                       "link": link_social}
        socialp.append(social_item)

        link_data = "DataLab"
        data_item = {"name-node": "DataLab", "title": "DataLab",
                     "subtitle": "",
                     "icon": "fas fa-info-circle",
                     "link": link_data}
        datalabs.append(data_item)

        data = raw_node.get("data", "")
        # Primary Job V4
        if (api_version == "v4"):
            if ((data.get("primary", "") != "" and 
                    data.get("primary", "").get("job", "") != None)):
                temp = data.get("primary", "").get("job", "")

                if (temp.get("company", "") != "" and temp.get(
                        "company", "") != "null" and temp.get(
                            "company", "") != None):

                    data_item = {"name-node": "DataCompany",
                                 "title": "Company",
                                 "subtitle": temp.get("company", ""),
                                 "icon": "fas fa-people-carry",
                                 "link": link_data}
                    datalabs.append(data_item)

                    # Profile
                    company_item = {'name': temp.get("company", ""),
                                    'title': temp.get("title", "").get(
                                        "name", ""),
                                    'start': temp.get("startDate", ""),
                                    'end': temp.get("endDate", "")}
                    company.append(company_item)

                    # Timeline
                    if (temp.get("start_date", "") != "" and temp.get(
                            "start_date", "") != None):
                        timeline.append({'action': 'Start : ' + temp
                                         .get("company", "").get(
                                             "name", "").title(),
                                         'date': temp.get("start_date", "")
                                         .replace("-", "/"),
                                         # 'icon': 'fa-building',
                                         'desc': str(temp.get("title", "").get(
                                             "name", "")).title() + 
                                             " - Source PDL"})
                    if (temp.get("end_date", "") != "" and temp.get(
                            "end_date", "") != None):
                        timeline.append({'action': 'End : ' + temp
                                         .get("company", "").get(
                                             "name", "").title(),
                                         'date': temp.get("end_date", "")
                                         .replace("-", "/"),
                                         # 'icon': 'fa-ban',
                                         'desc': str(temp.get("title", "").get(
                                             "name", "")).
                                         title() + " - Source PDL"})

        # Primary Job V5
        if (api_version == "v5"):
            if (data.get("job_company_name", "") and 
                    data.get("job_company_name", "") != ""):

               data_item = {"name-node": "DataCompany",
                            "title": "Company",
                            "subtitle": data.get("job_company_name", ""),
                            "icon": "fas fa-people-carry",
                            "link": link_data}
               datalabs.append(data_item)

               # Profile
               company_item = {'name': data.get("job_company_name", ""),
                               'title': data.get("job_title", ""),
                               'start': data.get("job_start_date", "")}
               company.append(company_item)

               # Timeline
               if (data.get("job_start_date", "") and data.get(
                       "job_start_date", "") != ""):
                   timeline.append({'action': 'Start : ' + data
                                    .get("job_company_name", ""),
                                    'date': data.get("start_date", ""),
                                    'desc': str(data.get("job_title", "")) +
                                        " - Source PDL"})

        # Primary location
        if (api_version == "v4"):
            if (data.get("primary", "") != "" and data.get("primary", "").
                    get("location", "") != None):

                temp = data.get("primary", "").get("location", "")

                data_item = {"name-node": "DataLocation",
                             "title": "Location",
                             "subtitle": temp.get("name", "").title(),
                             "icon": "fas fa-globe-americas",
                             "link": link_data}
                datalabs.append(data_item)

                # Profile
                profile_item = {'location': temp.get("name", "").title()}
                profile.append(profile_item)

                # Geolocalization
                geo_item = location_geo(temp.get("name", "")) 
                if (geo_item):
                    profile.append({'geo': geo_item})

        # Primary location V5
        if (api_version == "v5"):
            if (data.get("location_name", "") != ""):

                data_item = {"name-node": "DataLocation",
                             "title": "Location",
                             "subtitle": data.get("location_name", "").title(),
                             "icon": "fas fa-globe-americas",
                             "link": link_data}
                datalabs.append(data_item)

                # Profile
                profile_item = {'location': data.get(
                    "location_name", "").title()}
                profile.append(profile_item)

                # Geolocalization
                geo_item = location_geo(data.get("location_name", ""), 
                                        data.get("location_last_updated", ""))
                if(geo_item):
                    profile.append({'geo': geo_item})

        # Primary name
        if (api_version == "v4"):
            if (data.get("primary", "") != "" and data.get("primary", "").
                    get("name", "") != None):

                temp = data.get("primary", "").get("name", "")

                try:
                    name_complete = temp.get("first_name", "") + " " + \
                                    temp.get("middle_name", "") + " " + \
                                    temp.get("last_name", "")
                except:
                    name_complete = temp.get("first_name", "") + " " + \
                                    temp.get("last_name", "")

                data_item = {"name-node": "DataName",
                             "title": "Name",
                             "subtitle": name_complete.title(),
                             "icon": "fas fa-signature",
                             "link": link_data}
                datalabs.append(data_item)

                # Profile
                profile_item = {'name': name_complete.title()}
                profile.append(profile_item)

        # Primary name V5
        if (api_version == "v5"):
            if (data.get("full_name", "") and data.get("full_name", "") != ""):

                try:
                    name_complete = data.get("first_name", "") + " " + \
                                    data.get("middle_name", "") + " " + \
                                    data.get("last_name", "")
                except Exception:
                    name_complete = data.get("first_name", "") + " " + \
                                    data.get("last_name", "")

                data_item = {"name-node": "DataName",
                             "title": "Name",
                             "subtitle": name_complete.title(),
                             "icon": "fas fa-signature",
                             "link": link_data}
                datalabs.append(data_item)

                # Profile
                profile_item = {'name': name_complete.title()}
                profile.append(profile_item)

        # Primary industry
        if (api_version == "v4"):
            if (data.get("primary", "") != "" and data.get("primary", "").
                    get("industry", "") != None):

                temp = data.get("primary", "").get("industry", "")

                data_item = {"name-node": "DataInsdustry",
                             "title": "Industry",
                             "subtitle": temp,
                             "icon": "fas fa-briefcase",
                             "link": link_data}
                datalabs.append(data_item)

        # Primary industry V5
        if (api_version == "v5"):
            if (data.get("industry", "")):
                data_item = {"name-node": "DataInsdustry",
                             "title": "Industry",
                             "subtitle": data.get("industry"),
                             "icon": "fas fa-briefcase",
                             "link": link_data}
                datalabs.append(data_item)

        # Primary birthdate
        if (api_version == "v4"):
            if (data.get("birth_date", "") != "" and data.get(
                    "birth_date", "") != None):

                temp = data.get("birth_date", "")

                data_item = {"name-node": "DataBirth",
                             "title": "Birthday",
                             "subtitle": temp,
                             "icon": "fas fa-birthday-cake",
                             "link": link_data}
                datalabs.append(data_item)

                timeline.append({'action': 'BirthDay : ' + temp})

            elif (data.get("birth_date_fuzzy", "") != "" and data.get(
                    "birth_date_fuzzy", "") != None):

                temp = data.get("birth_date_fuzzy", "")

                data_item = {"name-node": "DataBirth",
                             "title": "Fuzzy Birthday",
                             "subtitle": temp,
                             "icon": "fas fa-birthday-cake",
                             "link": link_data}
                datalabs.append(data_item)

                timeline.append({'action': 'Fuzzy BirthDay : ' + temp})

        # Primary birthdate V5
        if (api_version == "v5"):
            if (data.get("birth_date", "") and data.get(
                    "birth_date", "") != ""):

                data_item = {"name-node": "DataBirth",
                             "title": "Birthday",
                             "subtitle": data.get("birth_date"),
                             "icon": "fas fa-birthday-cake",
                             "link": link_data}
                datalabs.append(data_item)

                timeline.append({'action': 'BirthDay : ' + data.get("birth_date")})

            elif (data.get("birth_year", "") and data.get(
                    "birth_year", "") != ""):

                data_item = {"name-node": "DataBirth",
                             "title": "BirthYear",
                             "subtitle": data.get("birth_year"),
                             "icon": "fas fa-birthday-cake",
                             "link": link_data}
                datalabs.append(data_item)

                timeline.append({'action': 'BirthYear : ' + data.get(
                    "birth_year")})

        # Gender
        if (data.get("gender", "") and data.get("gender", "") != ""):

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
        if (api_version == "v4"):
            e = 1
            for mail in data.get("primary", "").get("work_emails", ""):
                data_item = {"name-node": "DataWEmail" + str(e),
                             "title": "Work Email",
                             "subtitle": mail,
                             "icon": "fas fa-at",
                             "link": link_data}
                datalabs.append(data_item)
                e = + 1
            e = 1
            for mail in data.get("primary", "").get("personal_emails", ""):
                data_item = {"name-node": "DataPEmail" + str(e),
                             "title": "Personal Email",
                             "subtitle": mail,
                             "icon": "fas fa-at",
                             "link": link_data}
                datalabs.append(data_item)
                e = + 1
            e = 1
            for mail in data.get("primary", "").get("other_emails", ""):
                data_item = {"name-node": "DataOEmail" + str(e),
                             "title": "Other Email",
                             "subtitle": mail,
                             "icon": "fas fa-at",
                             "link": link_data}
                datalabs.append(data_item)
                e = + 1

        # Emails profile V5
        if (api_version == "v5"):
            e = 1
            for mail in data.get("emails", ""):
                data_item = {"name-node": "DataWEmail" + str(e),
                             "title": mail.get("type"),
                             "subtitle": mail.get("address"),
                             "icon": "fas fa-at",
                             "link": link_data}
                datalabs.append(data_item)
                e = + 1

        # Profiles RRSS
        if (data.get("profiles", "") != ""):
            for social in data.get("profiles", ""):
                if (social.get("username", "")):
                    subtitle = social.get("username", "")
                else:
                    subtitle = "Not identified"

                fa_icon = search_icon_5(social.get("network", ""), font_list)
                if (fa_icon is None):
                    fa_icon = search_icon_5("question", font_list)

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

        # Profiles emails
        for mail in data.get("emails", ""):
            profile_item = {'email': mail['address']}
            profile.append(profile_item)
        # Profiles phones
        if (api_version == "v4"):
            for phone in data.get("phone_numbers", ""):
                profile_item = {'phone': phone['number']}
                profile.append(profile_item)
        else:
            for phone in data.get("phone_numbers", ""):
                profile_item = {'phone': phone}
                profile.append(profile_item)
        # Profiles names
        if (api_version == "v4"):
            for name in data.get("names", ""):
                profile_item = {'name': name['name'].title()}
                profile.append(profile_item)
        else:
            if (data.get("first_name")):
                profile_item = {'name': data.get("first_name").title()}
                profile.append(profile_item)
            if (data.get("middle_name")):
                profile_item = {'name': data.get("middle_name").title()}
                profile.append(profile_item)
            if (data.get("last_name")):
                profile_item = {'name': data.get("last_name").title()}
                profile.append(profile_item)
            if (data.get("full_name")):
                profile_item = {'name': data.get("full_name").title()}
                profile.append(profile_item)

        # Profiles location
        if (api_version == "v4"):
            for location in data.get("locations", ""):
                if (location['name']):
                    profile_item = {'location': location['name'].title()}
                    profile.append(profile_item)
                if (location['geo']):
                    profile_item = {'Caption': location['name'],
                                    'Accessability': "",
                                    'Latitude': location['geo'].split(",")[0],
                                    'Longitude': location['geo'].split(",")[1],
                                    'Name': location['name'],
                                    'Time': ""
                                    }
                    profile.append({'geo': profile_item})
        if (api_version == "v5"):
            for location in data.get("location_names", ""):
                profile_item = {'location': location.title()}
                profile.append(profile_item)

                # Geolocalization
                geo_item = location_geo(location, 
                                        data.get("location_last_updated", ""))
                if(geo_item):
                    profile.append({'geo': geo_item})

    # Falta email, phone, locations loop, name loop
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


def output(data):
    print(json.dumps(data, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    email = sys.argv[1]
    result = t_peopledatalabs(email)
    output(result)
