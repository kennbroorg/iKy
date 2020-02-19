#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import sys
import json
import requests

import re
from bs4 import BeautifulSoup
import os.path
from datetime import datetime, timedelta

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

# Compatibility code
try:
    # Python 2: "unicode" is built-in
    unicode
except NameError:
    unicode = str


def date_convert(date):
    date_conv = str(date.get("year", ""))
    if (date.get("month")):
        date_conv = "%s-%02d" % (date_conv, int(date.get("month")))
    return date_conv


@celery.task
def t_linkedin(email, from_m):

    cookie_file = "cookie-linkedin.json"
    expiration_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

    s = requests.Session()
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.75.14 (KHTML, like Gecko) Version/7.0.3 Safari/7046A194A'}

    if (os.path.isfile(cookie_file)
        and (expiration_date < datetime.fromtimestamp(
            os.path.getmtime(cookie_file)).strftime('%Y-%m-%d'))):

        with open('cookie-linkedin.json', 'r') as f:
            s.cookies = requests.utils.cookiejar_from_dict(json.load(f))

    else:
        # Get user and pass
        linkedin_user = api_keys_search('linkedin_user')
        linkedin_pass = api_keys_search('linkedin_pass')

        # Login process
        r = s.get('https://www.linkedin.com/login?trk=guest_homepage-basic_nav-header-signin', headers=headers)
        cookies = dict(r.cookies)

        soup = BeautifulSoup(r.content, "lxml")
        hidden_tags = soup.find_all("input", type="hidden")
        payload = {}
        for input_hidden in hidden_tags:
            payload[input_hidden['name']] = input_hidden['value']
        payload['session_key'] = linkedin_user
        payload['session_password'] = linkedin_pass

        req = s.post("https://www.linkedin.com/checkpoint/lg/login-submit",
                     data=payload,
                     headers=headers)

        with open('cookie-linkedin.json', 'w') as f:
            json.dump(requests.utils.dict_from_cookiejar(s.cookies), f)

    for cookie in s.cookies:
        if "JSESSIONID" in str(cookie):
            csrfToken = re.findall('JSESSIONID=([^ ]*)', str(cookie))

    # Total
    total = []
    total.append({'module': 'linkedin'})
    total.append({'param': email})

    found = False
    # Get profile from username
    if ("@" not in email):
        total.append({'validation': 'hard'})
        url = "https://www.linkedin.com/in/%s/" % email
        found = True
    # Get profile from email
    else:
        total.append({'validation': 'hard'})
        url = "https://www.linkedin.com/sales/gmail/profile/" + \
            "viewByEmail/%s" % email
        req = s.get(url, headers=headers)
        if "Sorry, we couldn't find a matching LinkedIn" not in req.text:
            url = "https://www.linkedin.com/sales/gmail/profile/proxy/%s" % \
                (email)
            found = True

    if found:
        req = s.get(url, headers=headers)

        id = re.findall(
            '\/voyager\/api\/identity\/profiles\/([a-z]*)\/',
            req.text)

        # url = "https://www.linkedin.com/voyager/api/identity/profiles/" + \
        #     id[0] + "/recentActivities"
        # s.headers.update({'csrf-token': csrfToken[0].replace('"', '')})
        # req = s.get(url)
        # Recent Activities
        # x = json.loads(req.text)
        # print(json.dumps(x, indent=4, separators=(". ", " = ")))

        # url = "https://www.linkedin.com/voyager/api/identity/profiles/" + \
        #     id[0] + "/posts"
        # s.headers.update({'csrf-token': csrfToken[0].replace('"', '')})
        # req = s.get(url)
        # Posts
        # x = json.loads(req.text)

        url = "https://www.linkedin.com/voyager/api/identity/profiles/" + \
            id[0] + "/following?q=followedEntities&count=17"
        s.headers.update({'csrf-token': csrfToken[0].replace('"', '')})
        req = s.get(url, headers=headers)
        # Following
        following_view = json.loads(req.text)

        url = "https://www.linkedin.com/voyager/api/identity/profiles/" + \
            id[0] + "/skillCategory?includeHiddenEndorsers=true"
        s.headers.update({'csrf-token': csrfToken[0].replace('"', '')})
        req = s.get(url, headers=headers)
        content = re.sub("\. ?\n", ",\n", unicode(req.text))
        content = re.sub(" = ", " : ", content)
        # Skill Category
        skill_category = json.loads(content)

        # url = "https://www.linkedin.com/voyager/api/identity/profiles/" + \
        #     id[0] + "/skills?q=pendingFollowUpEndorsements&count=20"
        # s.headers.update({'csrf-token': csrfToken[0].replace('"', '')})
        # req = s.get(url)
        # Skill
        # x = json.loads(req.text)

        # TODO : KKK : For person relationship
        url = "https://www.linkedin.com/voyager/api/identity/profiles/" + \
            id[0] + \
            "/recommendations?q=received&recommendationStatuses=List(VISIBLE)"
        s.headers.update({'csrf-token': csrfToken[0].replace('"', '')})
        req = s.get(url, headers=headers)
        # Recomendaciones 1
        recommend_received = json.loads(req.text)

        # TODO : KKK : For person relationship
        url = "https://www.linkedin.com/voyager/api/identity/profiles/" + \
            id[0] + "/recommendations?q=given"
        s.headers.update({'csrf-token': csrfToken[0].replace('"', '')})
        req = s.get(url, headers=headers)
        # Recomendaciones 2
        recommend_given = json.loads(req.text)

        url = "https://www.linkedin.com/voyager/api/identity/profiles/" + \
            id[0] + "/profileView"
        s.headers.update({'csrf-token': csrfToken[0].replace('"', '')})
        req = s.get(url, headers=headers)
        content = re.sub("\. ?\n", ",\n", unicode(req.text))
        content = re.sub(" = ", " : ", content)
        # Profile
        profile_view = json.loads(content)

        # url = "https://www.linkedin.com/voyager/api/identity/profiles/" + \
        #     id[0] + "/memberBadges"
        # s.headers.update({'csrf-token': csrfToken[0].replace('"', '')})
        # req = s.get(url)
        # MemberBadget
        # x = json.loads(req.text)

        url = "https://www.linkedin.com/voyager/api/identity/profiles/" + \
            id[0] + "/networkinfo"
        s.headers.update({'csrf-token': csrfToken[0].replace('"', '')})
        req = s.get(url, headers=headers)
        content = re.sub("\. ?\n", ",\n", unicode(req.text))
        content = re.sub(" = ", " : ", content)
        # NetworkInfo
        network_info = json.loads(content)

        # url = "https://www.linkedin.com/voyager/api/identity/profiles/" + \
        #     id[0] + "/treasuryMediaItems?q=backgroundMedia&section=POSITION"
        # s.headers.update({'csrf-token': csrfToken[0].replace('"', '')})
        # req = s.get(url)
        # MediaItems
        # x = json.loads(req.text)

        # url = "https://www.linkedin.com/voyager/api/identity/profiles/" + \
        #     id[0] + "/treasuryMediaItems?q=backgroundMedia&section=EDUCATION"
        # s.headers.update({'csrf-token': csrfToken[0].replace('"', '')})
        # req = s.get(url)
        # Education
        # x = json.loads(req.text)

        # url = "https://www.linkedin.com/voyager/api/identity/profiles/" + \
        #     id[0] + "/memberConnections?q=connections"
        # s.headers.update({'csrf-token': csrfToken[0].replace('"', '')})
        # req = s.get(url)
        # MemberConnections
        # x = json.loads(req.text)

        # url = "https://www.linkedin.com/voyager/api/identity/profiles/" + \
        #     id[0] + "/privacySettings"
        # s.headers.update({'csrf-token': csrfToken[0].replace('"', '')})
        # req = s.get(url)
        # PrivacySettings
        # x = json.loads(req.text)

        raw = []
        raw.append({'profile_view': profile_view})
        raw.append({'network_info': network_info})
        raw.append({'recommend_received': recommend_received})
        raw.append({'recommend_given': recommend_given})
        raw.append({'following_view': following_view})
        raw.append({'skill_category': skill_category})

        # Graphic Array
        graphic = []

        # Profile Array
        profile = []

        # Timeline Array
        timeline = []

        # Tasks Array
        # tasks = []

        socialp = []
        link_social = "Linkedin"
        social_item = {"name-node": "Linkedin", "title": "Linkedin",
                       "subtitle": "", "icon": "fab fa-linkedin-in",
                       "link": link_social}
        socialp.append(social_item)

        # ProfileView
        certificationView = []
        profile_keys = profile_view.keys()
        for key in profile_keys:
            if (key == 'certificationView'):
                for certificate in profile_view.get(key).get("elements", ""):
                    if (certificate.get("company", "") != ""):
                        rootUrl = certificate.get("company").get(
                            "logo", "").get("com.linkedin.common.VectorImage",
                                            "").get("rootUrl", "")
                        shrink = certificate.get("company").get(
                            "logo", "").get("com.linkedin.common.VectorImage",
                                            "").get("artifacts", "")[1].get(
                                           "fileIdentifyingUrlPathSegment", "")
                        picture = str(rootUrl) + str(shrink)
                    else:
                        picture = "assets/img/app/university.png"

                    certificationView.append({'name': 'Cetificate : ' +
                                              certificate.get("name", ""),
                                              'desc': certificate.get(
                                                  "authority", ""),
                                              'picture': picture})
                    if (certificate.get("timePeriod", "") != "" and
                        certificate.get("timePeriod", "").get(
                            "endDate", "") != ""):
                        timeline.append({'action': 'Start : ' +
                                         certificate.get("name", ""),
                                        'desc': certificate.get(
                                            "authority", ""),
                                         'icon': 'fas fa-certificate',
                                         'date': date_convert(certificate.get(
                                            "timePeriod", "").get(
                                                "startDate", ""))})
                    if (certificate.get("timePeriod", "") != "" and
                        certificate.get("timePeriod", "").get(
                            "endDate", "") != ""):
                        timeline.append({'action': 'End : ' +
                                         certificate.get("name", ""),
                                         'desc': certificate.get(
                                             "authority", ""),
                                         'icon': 'fas fa-certificate',
                                         'date': date_convert(certificate.get(
                                             "timePeriod", "").get(
                                                "endDate", ""))})

            if (key == 'educationView'):
                # educationView = []
                for education in profile_view.get(key).get("elements", ""):
                    if (education.get("company", "") != ""):
                        rootUrl = education.get("company").get(
                            "logo", "").get("com.linkedin.common.VectorImage",
                                            "").get("rootUrl", "")
                        shrink = education.get("company").get(
                            "logo", "").get("com.linkedin.common.VectorImage",
                                            "").get("artifacts", "")[1].get(
                                           "fileIdentifyingUrlPathSegment", "")

                        picture = str(rootUrl) + str(shrink)
                    else:
                        picture = "assets/img/app/university.png"

                    certificationView.append({'name': 'Education : ' +
                                              education.get("degreeName", ""),
                                              'desc': education.get(
                                                  "schoolName") + ' - ' +
                                              education.get("fieldOfStudy",
                                                            "") + ' ' +
                                              education.get("description",
                                                            ""),
                                              'picture': picture})
                    if (education.get("timePeriod", "") != "" and
                        education.get("timePeriod", "").get("startDate",
                                                            "") != ""):
                        timeline.append({'action': 'Start : ' + education.get(
                            "degreeName", ""),
                            'desc': education.get("schoolName") + ' - ' +
                            education.get("fieldOfStudy", "") + ' - ' +
                            education.get("description", ""),
                            'icon': 'fas fa-university',
                            'date': date_convert(education.get(
                                "timePeriod", "").get(
                                    "startDate", ""))})
                    if (education.get("timePeriod", "") != "" and
                        education.get("timePeriod", "").get("endDate",
                                                            "") != ""):
                        timeline.append({'action': 'End : ' +
                                         education.get("degreeName", ""),
                                        'desc': education.get("schoolName") +
                                         ' - ' +
                                         education.get("fieldOfStudy", "") +
                                         ' ' +
                                         education.get("description", ""),
                                         'icon': 'fas fa-university',
                                         'date': date_convert(
                                             education.get(
                                                 "timePeriod", "").get(
                                                     "endDate", ""))})

            # if (key == 'publicationView'):  # TODO : KKK : ???

            if (key == 'positionGroupView'):
                positionGroupView = []
                for positionGroup in profile_view.get(key).get("elements", ""):
                    # positionGroupView.append({'name': positionGroup.get(
                    #     "name", ""),
                    #     'desc': positionGroup.get("positions")[0].get(
                    #     "title", "")})
                    positionGroupView.append({'label': positionGroup.get(
                        "name", "") + ' - ' + positionGroup.get(
                            "positions")[0].get("title", "")})
                    if (positionGroup.get("timePeriod", "") != "" and
                        positionGroup.get("timePeriod", "").get("startDate",
                                                                "") != ""):
                        timeline.append({'action': 'Start : ' +
                                         positionGroup.get("name", ""),
                                         'desc': positionGroup.get(
                                             "positions")[0].get("title", ""),
                                         'icon': 'fas fa-briefcase',
                                         'date': date_convert(
                                             positionGroup.get(
                                                 "timePeriod", "").get(
                                                     "startDate", ""))})
                    if (positionGroup.get("timePeriod", "") != "" and
                        positionGroup.get("timePeriod", "").get("endDate",
                                                                "") != ""):
                        timeline.append({'action': 'End : ' +
                                         positionGroup.get("name", ""),
                                         'desc': positionGroup.get(
                                             "positions")[0].get("title", ""),
                                         'icon': 'fas fa-briefcase',
                                         'date': date_convert(
                                             positionGroup.get(
                                                 "timePeriod", "").get(
                                                     "endDate", ""))})

            if (key == 'profile'):
                profile = []
                profile.append({'firstName': profile_view.get(key).get(
                    "firstName", "")})
                profile.append({'lastName': profile_view.get(key).get(
                    "lastName", "")})
                profile.append({'organization': profile_view.get(key).get(
                    "headline", "")})
                profile.append({'location': profile_view.get(key).get(
                    "locationName", "")})

                if (profile_view.get(key).get("miniProfile", "") != "" and
                    profile_view.get(key).get("miniProfile", "").get(
                    "picture", "") != ""):
                    rootUrl = profile_view.get(key).get("miniProfile", "").get(
                        "picture", "").get(
                        "com.linkedin.common.VectorImage", "").get("rootUrl",
                                                                   "")
                    shrink = profile_view.get(key).get("miniProfile", "").get(
                        "picture", "").get("com.linkedin.common.VectorImage",
                                        "").get("artifacts", "")[3].get(
                            "fileIdentifyingUrlPathSegment", "")

                    photo_item = {"name-node": "Linkedin",
                                "title": "Linkedin",
                                "subtitle": "",
                                "picture": rootUrl + shrink,
                                "link": "Photos"}
                    profile.append({'photos': [photo_item]})

                social_item = {"name-node": "Name",
                               "title": "Name",
                               "subtitle": profile_view.get(key).get(
                                   "firstName", "") + " " +
                               profile_view.get(key).get("lastName", ""),
                               "icon": "fas fa-user-circle",
                               "link": link_social}
                socialp.append(social_item)
                social_item = {"name-node": "Headline",
                               "title": "Headline",
                               "subtitle": profile_view.get(key).get(
                                   "headline", ""),
                               "icon": "fas fa-building",
                               "link": link_social}
                socialp.append(social_item)
                social_item = {"name-node": "Location",
                               "title": "Location",
                               "subtitle": profile_view.get(key).get(
                                   "locationName", ""),
                               "icon": "fas fa-map-marker-alt",
                               "link": link_social}
                socialp.append(social_item)
                # NetworkInfo - Followers
                social_item = {"name-node": "Followers",
                               "title": "Followers",
                               "subtitle": network_info.get("followersCount",
                                                            ""),
                               "icon": "fas fa-users",
                               "link": link_social}
                socialp.append(social_item)
                # FollowingView - Following
                social_item = {"name-node": "Following",
                               "title": "Following",
                               "subtitle": following_view.get("paging",
                                                              "").get(
                                                                  "total", ""),
                               "icon": "fas fa-users",
                               "link": link_social}
                socialp.append(social_item)
                # RecommendReceived
                social_item = {"name-node": "Received",
                               "title": "Received",
                               "subtitle": recommend_received.get("paging",
                                                                  "").get(
                                                                  "total", ""),
                               "icon": "fas fa-thumbs-up",
                               "link": link_social}
                socialp.append(social_item)
                # RecommendGiven
                social_item = {"name-node": "Given",
                               "title": "Given",
                               "subtitle": recommend_given.get("paging",
                                                               "").get(
                                                               "total", ""),
                               "icon": "fas fa-thumbs-up",
                               "link": link_social}
                socialp.append(social_item)

        # SkillCategory
        skills = []
        for skilles in skill_category.get("elements", ""):
            for s in skilles.get("endorsedSkills", ""):
                skills.append({"name": s.get("skill", "").get("name", ""),
                               "count": s.get("endorsementCount", ""),
                               "value": s.get("endorsementCount", "")})
        skill_tmp = {"name": "", "value": 100, "children": skills}

        total.append({'raw': raw})
        graphic.append({'social': socialp})
        # graphic.append({'skills': skills})
        graphic.append({'skills': skill_tmp})
        try:
            graphic.append({'certificationView': certificationView})
        except NameError:
            graphic.append({'certificationView': []})
        try:
            graphic.append({'positionGroupView': positionGroupView})
        except NameError:
            graphic.append({'positionGroupView': []})
        # graphic.append({'educationView': educationView})
        total.append({'graphic': graphic})

        total.append({'profile': profile})
        total.append({'timeline': timeline})

    return total


def output(data):
    print(json.dumps(data, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    username = sys.argv[1]
    result = t_linkedin(username, "Initial")
    output(result)
