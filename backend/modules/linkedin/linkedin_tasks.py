#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import sys
import json
import requests
import time
import traceback
from collections import Counter
import browser_cookie3

import re
from bs4 import BeautifulSoup

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


def date_convert(date):
    date_conv = str(date.get("year", ""))
    if (date.get("month")):
        date_conv = "%s-%02d" % (date_conv, int(date.get("month")))
    return date_conv


def p_linkedin(user):

    s = requests.Session()
    headers = {'User-Agent': 
               'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) ' + 
               'AppleWebKit/537.75.14 (KHTML, like Gecko) Version/7.0.3 ' +
               'Safari/7046A194A'}

    # Try to get cookie from browser
    ref = ["chromium", "opera", "edge", "firefox", "chrome", "brave"]
    index = 0
    json_cookie = {}
    found = False
    for cookie_fn in [
        browser_cookie3.chromium,
        browser_cookie3.opera,
        browser_cookie3.edge,
        browser_cookie3.firefox,
        browser_cookie3.chrome,
        browser_cookie3.brave,
    ]:
        try:
            for cookie in cookie_fn(domain_name=""):
                if ('linkedin' in cookie.domain):
                    if ((cookie.name == 'li_at' or 
                         cookie.name == 'JSESSIONID') and 
                            (not cookie.is_expired())):
                        json_cookie['browser'] = ref[index]
                        json_cookie[cookie.name] = cookie.value
                        json_cookie[cookie.name + '_expires'] = cookie.expires

                # Check
                if((json_cookie.get("li_at", "") != "") and
                   (json_cookie.get("JSESSIONID", "") != "")):
                    found = True
                    break
        except Exception as e:
            print(e)

        index += 1

        if(found):
            break

    if(found):
        s.cookies['li_at'] = json_cookie['li_at']
        s.cookies['JSESSIONID'] = json_cookie['JSESSIONID']
        s.headers = headers
        s.headers["csrf-token"] = s.cookies["JSESSIONID"].strip('"')
    else:
        v_li_at = api_keys_search('linkedin_li_at')
        v_JSESSIONID = api_keys_search('linkedin_JSESSIONID')
        if (v_li_at == '' or v_JSESSIONID == ''):
            raise RuntimeError('iKy can\'t detect cookies!!! \n' + 
                               'You will have to load them manually, by ' +
                               'extracting the cookies named \'li_at\' and ' + 
                               '\'JSESSIONID\' from the browser and loading ' +
                               'them in \'linkedin_li_at\' and ' +
                               '\'linkedin_JSESSIONID\' accordingly.'
                               '\nPlease refer to ' +
                               'https://gitlab.com/kennbroorg/iKy/-/wikis/' +
                               'APIs/ApiKeys-get#linkedin \n')
        else:
            s.cookies['li_at'] = v_li_at
            s.cookies['JSESSIONID'] = v_JSESSIONID
            s.headers = headers
            s.headers["csrf-token"] = s.cookies["JSESSIONID"].strip('"')

    url = 'https://www.linkedin.com/voyager/api/identity/profiles/' + \
        user + '/profileView'

    req = s.get(url)

    # Get ID
    ids = []
    match = re.search(r'\"profileId\":\"([a-zA-Z0-9_\-\.]+)\"', req.text)
    if (match):
        ids = match.groups()[0].strip()
    elif ('This profile can\'t be accessed' in req.text):
        raise RuntimeError('Linkedin user don\'t exist')  # TODO
    else:
        raise RuntimeError('The cookies in apikeys are wrong or expired\n' +
                           'Reload them in apikeys section or file and ' +
                           'try again ')

    # Total
    total = []
    total.append({'module': 'linkedin'})
    total.append({'param': user})

    found = False
    # Get profile from username
    if ("http" in user):
        total.append({'validation': 'hard'})
        url = user
        found = True
        raise RuntimeError('Linkedin don\'t work with url')
    # Get profile from email
    elif ("@" in user):
        raise RuntimeError('Linkedin don\'t work with email')
    else:
        total.append({'validation': 'hard'})
        url = "https://www.linkedin.com/in/%s/" % user
        found = True
    # Get profile from http

    if found:
        # s.headers["csrf-token"] = s.cookies["JSESSIONID"].strip('"')
        # headers["csrf-token"] = s.cookies["JSESSIONID"].strip('"')

        req = s.get(url, headers=headers)

        id = Counter([ids]).most_common(1)  # This is for compatibility code

        url = "https://www.linkedin.com/voyager/api/identity/profiles/" + \
            id[0][0] + "/following?q=followedEntities&count=17"
        
        req = s.get(url, headers=headers)

        # Following
        following_view = json.loads(req.text)

        url = "https://www.linkedin.com/voyager/api/identity/profiles/" + \
            id[0][0] + "/skillCategory?includeHiddenEndorsers=true"
        # s.headers.update({'csrf-token': csrfToken[0].replace('"', '')})
        req = s.get(url, headers=headers)
        content = re.sub("\. ?\n", ",\n", req.text)
        content = re.sub(" = ", " : ", content)
        # Skill Category
        skill_category = json.loads(content)

        # url = "https://www.linkedin.com/voyager/api/identity/profiles/" + \
        #     id[0][0] + "/skills?q=pendingFollowUpEndorsements&count=20"
        # s.headers.update({'csrf-token': csrfToken[0].replace('"', '')})
        # req = s.get(url)
        # Skill
        # x = json.loads(req.text)

        # TODO : KKK : For person relationship
        url = "https://www.linkedin.com/voyager/api/identity/profiles/" + \
            id[0][0] + \
            "/recommendations?q=received&recommendationStatuses=List(VISIBLE)"
        # s.headers.update({'csrf-token': csrfToken[0].replace('"', '')})
        req = s.get(url, headers=headers)
        # Recomendaciones 1
        recommend_received = json.loads(req.text)

        # TODO : KKK : For person relationship
        url = "https://www.linkedin.com/voyager/api/identity/profiles/" + \
            id[0][0] + "/recommendations?q=given"
        # s.headers.update({'csrf-token': csrfToken[0].replace('"', '')})
        req = s.get(url, headers=headers)
        # Recomendaciones 2
        recommend_given = json.loads(req.text)

        url = "https://www.linkedin.com/voyager/api/identity/profiles/" + \
            id[0][0] + "/profileView"
        # s.headers.update({'csrf-token': csrfToken[0].replace('"', '')})
        req = s.get(url, headers=headers)
        content = re.sub("\. ?\n", ",\n", req.text)
        content = re.sub(" = ", " : ", content)
        # Profile
        profile_view = json.loads(content)

        # url = "https://www.linkedin.com/voyager/api/identity/profiles/" + \
        #     id[0][0] + "/memberBadges"
        # s.headers.update({'csrf-token': csrfToken[0].replace('"', '')})
        # req = s.get(url)
        # MemberBadget
        # x = json.loads(req.text)

        url = "https://www.linkedin.com/voyager/api/identity/profiles/" + \
            id[0][0] + "/networkinfo"
        # s.headers.update({'csrf-token': csrfToken[0].replace('"', '')})
        req = s.get(url, headers=headers)
        content = re.sub("\. ?\n", ",\n", req.text)
        content = re.sub(" = ", " : ", content)
        # NetworkInfo
        network_info = json.loads(content)

        # url = "https://www.linkedin.com/voyager/api/identity/profiles/" + \
        #     id[0][0] + "/treasuryMediaItems?q=backgroundMedia&section=POSITION"
        # s.headers.update({'csrf-token': csrfToken[0].replace('"', '')})
        # req = s.get(url)
        # MediaItems
        # x = json.loads(req.text)

        # url = "https://www.linkedin.com/voyager/api/identity/profiles/" + \
        #     id[0][0] + "/treasuryMediaItems?q=backgroundMedia&section=EDUCATION"
        # s.headers.update({'csrf-token': csrfToken[0].replace('"', '')})
        # req = s.get(url)
        # Education
        # x = json.loads(req.text)

        # url = "https://www.linkedin.com/voyager/api/identity/profiles/" + \
        #     id[0][0] + "/memberConnections?q=connections"
        # s.headers.update({'csrf-token': csrfToken[0].replace('"', '')})
        # req = s.get(url)
        # MemberConnections
        # x = json.loads(req.text)

        # url = "https://www.linkedin.com/voyager/api/identity/profiles/" + \
        #     id[0][0] + "/privacySettings"
        # s.headers.update({'csrf-token': csrfToken[0].replace('"', '')})
        # req = s.get(url)
        # PrivacySettings
        # x = json.loads(req.text)

        # Graphic Array
        graphic = []

        # Profile Array
        profile = []
        presence = []

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
                        try:
                            rootUrl = certificate.get("company").get(
                                "logo", "").get("com.linkedin.common.VectorImage",
                                                "").get("rootUrl", "")
                            shrink = certificate.get("company").get(
                                "logo", "").get("com.linkedin.common.VectorImage",
                                                "").get("artifacts", "")[1].get(
                                            "fileIdentifyingUrlPathSegment", "")
                            picture = str(rootUrl) + str(shrink)
                        except:
                            picture = "assets/img/app/university.png"

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

        # Raw with status
        raw = []
        raw.append({"code": 0})
        raw.append({'profile_view': profile_view})
        raw.append({'network_info': network_info})
        raw.append({'recommend_received': recommend_received})
        raw.append({'recommend_given': recommend_given})
        raw.append({'following_view': following_view})
        raw.append({'skill_category': skill_category})

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

        presence.append({"name": "Linkedin",
                         "children": [
                             {"name": "followers", 
                              "value": network_info.get("followersCount", "")},
                             {"name": "following", 
                              "value": following_view.get("paging", "").get(
                                                          "total", "")}
                         ]})

        profile.append({'presence': presence})

        total.append({'profile': profile})
        total.append({'timeline': timeline})

    return total


@celery.task
def t_linkedin(user, from_m):
    # Variable principal
    total = []
    # Take initial time
    tic = time.perf_counter()

    try:
        total = p_linkedin(user)
    except Exception as e:
        traceback.print_exc()
        traceback_text = traceback.format_exc()
        total.append({'module': 'linkedin'})
        total.append({'param': user})
        total.append({'validation': from_m})

        raw_node = []
        raw_node.append({"status": "Fail",
                         "reason": "{}".format(e),
                         # "traceback": 1})
                         "traceback": traceback_text})
        total.append({"raw": raw_node})

    # Take final time
    toc = time.perf_counter()
    # Show process time
    logger.info(f"Linkedin - Response in {toc - tic:0.4f} seconds")

    return total


def output(data):
    print(json.dumps(data, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    username = sys.argv[1]
    result = t_linkedin(username, "Initial")
    output(result)
