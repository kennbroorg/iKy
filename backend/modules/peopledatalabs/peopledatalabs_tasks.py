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
    from celery.utils.log import get_task_logger
    celery = create_celery(create_application())
except ImportError:
    # This is to test the module individually, and I know that is piece of shit
    sys.path.append('../../')
    from factories._celery import create_celery
    from factories.application import create_application
    from factories.configuration import api_keys_search
    from factories.fontcheat import fontawesome_cheat_5, search_icon_5
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

    url = "https://api.peopledatalabs.com/v4/person"
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

    # Web Array
    webs = []

    # Bios Array
    bios = []


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

        # Primary Job
        data = raw_node.get("data", "")
        if (data.get("primary", "") != "" and data.get("primary", "").
                get("job", "") != None):
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
                                         "name", "")).title() + " - Source PDL"})
                if (temp.get("end_date", "") != "" and temp.get(
                        "end_date", "") != None):
                    timeline.append({'action': 'End : ' + temp
                                     .get("company", "").get(
                                         "name", "").title(),
                                     'date': temp.get("end_date", "")
                                     .replace("-", "/"),
                                     # 'icon': 'fa-ban',
                                     'desc': str(temp.get("title", "").get(
                                         "name", "")).title() + " - Source PDL"})

        # Primary location
        if (data.get("primary", "") != "" and data.get("primary", "").
                get("location", "") != None):

            temp = data.get("primary", "").get("location", "")

            data_item = {"name-node": "DataLocation",
                         "title": "Location",
                         "subtitle": temp.get("name", ""),
                         "icon": "fas fa-globe-americas",
                         "link": link_data}
            datalabs.append(data_item)

            # Profile
            profile_item = {'location': temp.get("name", "")}
            profile.append(profile_item)

        # Primary name
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

        # Primary industry
        if (data.get("primary", "").get("industry", "") != None):

            temp = data.get("primary", "").get("industry", "")

            data_item = {"name-node": "DataInsdustry",
                         "title": "Industry",
                         "subtitle": temp,
                         "icon": "fas fa-briefcase",
                         "link": link_data}
            datalabs.append(data_item)

        # Primary birthdate
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

        # Gender
        if (data.get("gender", "") != None):

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
        e = 1
        for mail in data.get("primary", "").get("work_emails", ""):
            data_item = {"name-node": "DataWEmail" + str(e),
                         "title": "Work Email",
                         "subtitle": mail,
                         "icon": "fas fa-at",
                         "link": link_data}
            datalabs.append(data_item)
            e=+1
        e = 1
        for mail in data.get("primary", "").get("personal_emails", ""):
            data_item = {"name-node": "DataPEmail" + str(e),
                         "title": "Personal Email",
                         "subtitle": mail,
                         "icon": "fas fa-at",
                         "link": link_data}
            datalabs.append(data_item)
            e=+1
        e = 1
        for mail in data.get("primary", "").get("other_emails", ""):
            data_item = {"name-node": "DataOEmail" + str(e),
                         "title": "Other Email",
                         "subtitle": mail,
                         "icon": "fas fa-at",
                         "link": link_data}
            datalabs.append(data_item)
            e=+1

        # Profiles RRSS
        if (data.get("profiles", "") != ""):
            for social in data.get("profiles", ""):
                if (social.get("username", "") != None):
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
        for phone in data.get("phone_numbers", ""):
            profile_item = {'phone': phone['number']}
            profile.append(profile_item)
        # Profiles names
        for name in data.get("names", ""):
            profile_item = {'name': name['name'].title()}
            profile.append(profile_item)
        # Profiles location
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
