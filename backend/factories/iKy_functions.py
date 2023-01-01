#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import re
from geopy.geocoders import Nominatim


def location_geo(location, time=''):
    geolocator = Nominatim(user_agent="iKy")
    try:
        latlong = geolocator.geocode(location)
    except Exception:
        latlong = False

    if latlong:
        return {'Caption': latlong.raw['display_name'],
                'Accessability': latlong.raw['class'],
                'Latitude': latlong.latitude,
                'Longitude': latlong.longitude,
                'Name': latlong.address,
                'Time': time
                }
    else:
        return False


def extract_hashtags(text):
    hashtags = []
    regex = r"#[a-zA-Z0-9_]+"
    matches = re.finditer(regex, text, re.MULTILINE)
    for matchNum, match in enumerate(matches, start=1):
        if (match.group() != ''):
            hashtags.append(match.group().strip().replace("#", ""))
    return hashtags


def extract_mentions(text):
    mentions = []
    regex = r"^|[^\w]@([\w\_\.]+)"
    matches = re.finditer(regex, text, re.MULTILINE)
    for matchNum, match in enumerate(matches, start=1):
        if (match.group() != ''):
            mentions.append(match.group().strip().replace("@", ""))
    return mentions


def extract_url(text):
    urls = []
    regex = r"((http(s)?(\:\/\/))+(www\.)?([\w\-\.\/])*(\.[a-zA-Z]{2,3}\/?))[^\s\b\n|]*[^.,;:\?\!\@\^\$ -]"
    matches = re.finditer(regex, text, re.MULTILINE)
    for matchNum, match in enumerate(matches, start=1):
        urls.append({"url": match.group()})
    return urls


def extract_mails(text):
    mails = []
    regex = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
    matches = re.finditer(regex, text, re.MULTILINE)
    for matchNum, match in enumerate(matches, start=1):
        mails.append({"email": match.group()})
    return mails


def extract_url_linkedin(text):
    tasks = []
    # regex = r"((http(s)?(\:\/\/))+(www\.)?(linkedin)*(\.[a-zA-Z]{2,3}\/?))[^\s\b\n|]*[^.,;:\?\!\@\^\$ -]"
    regex = r"http[s]?\:\/\/+www\.?linkedin*\.[a-zA-Z]{2,3}\/?\/in\/([^\s\b\n|]*[^.,;:\?\!\@\^\$ -])\/"
    matches = re.finditer(regex, text, re.MULTILINE)
    for matchNum, match in enumerate(matches, start=1):
        tasks.append({"module": "linkedin",
                      "param": match.group(1)})
    return tasks


def extract_url_instagram(text):
    tasks = []
    regex = r"((http(s)?(\:\/\/))+(www\.)?(instagram)*(\.[a-zA-Z]{2,3}\/?))(\w+)(/)?"
    matches = re.finditer(regex, text, re.MULTILINE)
    for matchNum, match in enumerate(matches, start=1):
        tasks.append({"module": "instagram",
                      "param": match.group(8)})
    return tasks


def extract_url_twitter(text):
    tasks = []
    regex = r"((http(s)?(\:\/\/))+(www\.)?(twitter)*(\.[a-zA-Z]{2,3}\/?))(\w+)(/)?"
    matches = re.finditer(regex, text, re.MULTILINE)
    for matchNum, match in enumerate(matches, start=1):
        tasks.append({"module": "twitter",
                      "param": match.group(8)})
    return tasks


def extract_url_tiktok(text):
    tasks = []
    regex = r"((http(s)?(\:\/\/))+(www\.)?(tiktok)*(\.[a-zA-Z]{2,3}\/?))(@)?(\w+)(/)?"
    matches = re.finditer(regex, text, re.MULTILINE)
    for matchNum, match in enumerate(matches, start=1):
        tasks.append({"module": "tiktok",
                      "param": match.group(9)})
    return tasks


def extract_url_github(text):
    tasks = []
    regex = r"((http(s)?(\:\/\/))+(www\.)?(github)*(\.[a-zA-Z]{2,3}\/?))(@)?(\w+)(/)?"
    matches = re.finditer(regex, text, re.MULTILINE)
    for matchNum, match in enumerate(matches, start=1):
        tasks.append({"module": "github",
                      "param": match.group(9)})
    return tasks


def extract_url_githubio(text):
    tasks = []
    regex = r"http[s]?\:\/\/+(\w+)\.github.io"
    matches = re.finditer(regex, text, re.MULTILINE)
    for matchNum, match in enumerate(matches, start=1):
        tasks.append({"module": "github",
                      "param": match.group(1)})
    return tasks


def extract_github(text):
    tasks = []
    regex = r"(?i)(|.*)github(:)?( *)?(@)?(\w+)"
    matches = re.finditer(regex, text, re.MULTILINE)
    for matchNum, match in enumerate(matches, start=1):
        tasks.append({"module": "github",
                      "param": match.group(5)})
    return tasks


def extract_tiktok(text):
    tasks = []
    regex = r"(?i)(|.*)tiktok(:)?( *)?(@)?(\w+)"
    matches = re.finditer(regex, text, re.MULTILINE)
    for matchNum, match in enumerate(matches, start=1):
        tasks.append({"module": "tiktok",
                      "param": match.group(5)})
    return tasks


def extract_twitter(text):
    tasks = []
    regex = r"(?i)(|.*)twitter(:)?( *)?(@)?(\w+)"
    matches = re.finditer(regex, text, re.MULTILINE)
    for matchNum, match in enumerate(matches, start=1):
        tasks.append({"module": "twitter",
                      "param": match.group(5)})
    return tasks


def extract_instagram(text):
    tasks = []
    regex = r"(?i)(|.*)instagram(:)?( *)?(@)?(\w+)"
    matches = re.finditer(regex, text, re.MULTILINE)
    for matchNum, match in enumerate(matches, start=1):
        tasks.append({"module": "instagram",
                      "param": match.group(5)})
    return tasks


def extract_linkedin(text):
    tasks = []
    regex = r"(?i)(|.*)linkedin(:)?( *)?(@)?(\w+)"
    matches = re.finditer(regex, text, re.MULTILINE)
    for matchNum, match in enumerate(matches, start=1):
        tasks.append({"module": "linkedin",
                      "param": match.group(5)})
    return tasks


def analize_rrss(text):
    analized = {}

    hashtags = extract_hashtags(text)
    analized['hashtags'] = hashtags
    mentions = extract_mentions(text)
    analized['mentions'] = mentions
    urls = extract_url(text)
    analized['url'] = urls
    mails = extract_mails(text)
    analized['email'] = mails
    tasks_temp = []
    tasks_temp.append(extract_url_linkedin(text))
    tasks_temp.append(extract_url_instagram(text))
    tasks_temp.append(extract_url_twitter(text))
    tasks_temp.append(extract_url_tiktok(text))
    tasks_temp.append(extract_url_github(text))
    tasks_temp.append(extract_url_githubio(text))
    tasks_temp.append(extract_github(text))
    tasks_temp.append(extract_twitter(text))
    tasks_temp.append(extract_tiktok(text))
    tasks_temp.append(extract_instagram(text))
    tasks_temp.append(extract_linkedin(text))

    tasks = [val for sublist in tasks_temp for val in sublist]

    analized['tasks'] = tasks

    return analized


def name_match(names, data):
    min_matching = 2 if (len(names) == 2) else len(names) - 1
    matchs = 0
    for name in names:
        if name in data:
            matchs = matchs + 1
    if matchs >= min_matching:
        return True
    else:
        return False


def simple_analysis(source, type_s, username, data, output):
    """
    Social Networks :
        - twitter
        - github
        - instagram
        - keybase
        - linkedin
        - facebook
        - pinterest
        - tiktok
    TODO :
        - gitlab
        - tinder
        - bitbucket
        - reddit
        - youtube
        - twitch
    """
    # Resolve
    # https://www.facebook.com/public/Jezer-Ferreira
    # https://www.instagram.com/p/BtRNU3vlf1I/ (Ignore)
    # Initialize
    urls = [] if ('urls' not in output) else output['urls']
    usernames = [] if ('usernames' not in output) else output['usernames']
    names = [] if ('names' not in output) else output['names']
    social = [] if ('social' not in output) else output['social']
    users = [] if ('users' not in output) else output['users']
    hashtags = [] if ('hashtags' not in output) else output['hashtags']
    emails = [] if ('emails' not in output) else output['emails']

    match_twitter = re.match("^(https:\/\/www.google.com\/url\?q=|)(http:\/\/\w+\.|https:\/\/\w+\.|http:\/\/|https:\/\/)?[a-z0-9\.]*?(twitter+)\.[a-z]{2,5}(:[0-9]{1,5})?\/(\w+)", data[1])
    if (match_twitter):
        twitter_user = ""
        if ('/' in match_twitter.groups()[4]):
            twitter_user = match_twitter.groups()[4].split('/')[0]
        else:
            twitter_user = match_twitter.groups()[4]
        if ('?' in twitter_user):
            twitter_user = twitter_user.split('?')[0]
        if ('%40' in twitter_user):
            twitter_user = twitter_user.replace('%40', '')
        usernames.append({"source": source,
                          "type": type_s,
                          "usernames": twitter_user,
                          "rrss": "twitter"})
        twitter_name = ""
        match_name = re.match("^(Media Tweets by )?(.*)\(@(.*)\) \| Twitter",
                              data[0])
        if (match_name):
            twitter_name = match_name.groups()[1].strip()
            names.append({"source": source,
                          "type": type_s,
                          "name": twitter_name,
                          "rrss": "twitter"})
        match_name_o = re.match("^(.*) on Twitter: (.*)$", data[0])
        if (match_name_o):
            twitter_name = match_name_o.groups()[0].strip()
            names.append({"source": source,
                          "type": type_s,
                          "name": twitter_name,
                          "rrss": "twitter"})
            # ^(.*) on Twitter: (.*)$
        social.append({"source": source,
                       "type": type_s,
                       "name": twitter_name,
                       "user": twitter_user,
                       "rrss": "twitter"})

    match_github = re.match("^(https:\/\/www.google.com\/url\?q=|)(http:\/\/\w+\.|https:\/\/\w+\.|http:\/\/|https:\/\/)?[a-z0-9\.]*?(github+)\.[a-z]{2,5}(:[0-9]{1,5})?\/(\w+)", data[1])
    if (match_github):
        github_user = ""
        if ('/' in match_github.groups()[4]):
            github_user = match_github.groups()[4].split('/')[0]
        else:
            github_user = match_github.groups()[4]
        if ('?' in github_user):
            github_user = github_user.split('?')[0]
        usernames.append({"source": source,
                          "type": type_s,
                          "usernames": github_user,
                          "rrss": "github"})
        match_name = re.match("(.*)\((.*)\) · GitHub", data[0])
        github_name = ""
        if (match_name):
            github_name = match_name.groups()[1].strip()
            names.append({"source": source,
                          "type": type_s,
                          "name": github_name,
                          "rrss": "github"})
        social.append({"source": source,
                       "type": type_s,
                       "name": github_name,
                       "user": github_user,
                       "rrss": "github"})

    match_instagram = re.match("^(https:\/\/www.google.com\/url\?q=|)" +
                               "(http:\/\/www\.|https:\/\/www\.|http:\/\/|" +
                               "https:\/\/)?[a-z0-9\.]*?(instagram+)\.[a-z]" +
                               "{2,5}(:[0-9]{1,5})?\/([^p].*?)(%3|\/)(.*)", 
                               data[1])
    if (match_instagram):
        instagram_user = ""
        if ('/' in match_instagram.groups()[4]):
            instagram_user = match_instagram.groups()[4].split('/')[0]
        else:
            instagram_user = match_instagram.groups()[4]
        if ('?' in instagram_user):
            instagram_user = instagram_user.split('?')[0]
        usernames.append({"source": source,
                          "type": type_s,
                          "usernames": instagram_user,
                          "rrss": "instagram"})
        match_name = re.match("(.*)\((.*)\)(.*)?Instagram(.*)?", data[0])
        instagram_name = ""
        if (match_name):
            instagram_name = match_name.groups()[0].strip()
            names.append({"source": source,
                          "type": type_s,
                          "name": instagram_name,
                          "rrss": "instagram"})
        social.append({"source": source,
                       "type": type_s,
                       "name": instagram_name,
                       "user": instagram_user,
                       "rrss": "instagram"})

    match_keybase = re.match("^(https:\/\/www.google.com\/url\?q=|)(http:\/\/www\.|https:\/\/www\.|http:\/\/|https:\/\/)?[a-z0-9\.]*?(keybase+)\.[a-z]{2,5}(:[0-9]{1,5})?\/(\w+)", data[1])
    if (match_keybase):
        keybase_user = ""
        if ('/' in match_keybase.groups()[4]):
            keybase_user = match_keybase.groups()[4].split('/')[0]
        else:
            keybase_user = match_keybase.groups()[4]
        usernames.append({"source": source,
                          "type": type_s,
                          "usernames": keybase_user,
                          "rrss": "keybase"})
        keybase_name = ""
        social.append({"source": source,
                       "type": type_s,
                       "name": keybase_name,
                       "user": keybase_user,
                       "rrss": "keybase"})

    match_linkedin = re.match("^(https:\/\/www.google.com\/url\?q=|)(http:\/\/www\.|https:\/\/www\.|http:\/\/|https:\/\/)?[a-z0-9\.]*?(linkedin+)\.[a-z]{2,5}(:[0-9]{1,5})?\/in\/?\/(\w+)", data[1])
    if (match_linkedin):
        linkedin_user = ""
        if ('/' in match_linkedin.groups()[4]):
            linkedin_user = match_linkedin.groups()[4].split('/')[0]
        else:
            linkedin_user = match_linkedin.groups()[4]
        if ('?' in linkedin_user):
            linkedin_user = linkedin_user.split('?')[0]
        if (linkedin_user.count("-") < 2):
            usernames.append({"source": source,
                              "type": type_s,
                              "usernames": linkedin_user,
                              "rrss": "linkedin"})
            match_name = re.match("^(.*?) \- (.*)", data[0])
            linkedin_name = ""
            if (match_name):
                linkedin_name = match_name.groups()[0].strip()
                names.append({"source": source,
                              "type": type_s,
                              "name": linkedin_name,
                              "rrss": "linkedin"})
            social.append({"source": source,
                           "type": type_s,
                           "name": linkedin_name,
                           "user": linkedin_user,
                           "rrss": "linkedin"})

    match_facebook = re.match("^(https:\/\/www.google.com\/url\?q=|)(http:\/\/\w+\.|https:\/\/\w+\.|http:\/\/|https:\/\/)?[a-z0-9\.]?(facebook+)\.[a-z]{2,5}(:[0-9]{1,5})?\/(\w+)", data[1])
    if (match_facebook):
        facebook_user = ""
        if ('public' in match_facebook.groups()[4]):
            facebook_user = match_facebook.groups()[6]
        elif ('/' in match_facebook.groups()[4]):
            facebook_user = match_facebook.groups()[4].split('/')[0]
        else:
            facebook_user = match_facebook.groups()[4]
        if ('?' in facebook_user):
            facebook_user = facebook_user.split('?')[0]
        usernames.append({"source": source,
                          "type": type_s,
                          "usernames": facebook_user,
                          "rrss": "facebook"})
        # match_name = re.match("^(.*?) \| (.*)", data[0])
        match_name = re.match("^(.*?)( News - Home)? \| (.*)", data[0])
        facebook_name = ""
        if (match_name):
            facebook_name = match_name.groups()[0].strip()
            names.append({"source": source,
                          "type": type_s,
                          "name": facebook_name,
                          "rrss": "facebook"})
        social.append({"source": source,
                       "type": type_s,
                       "name": facebook_name,
                       "user": facebook_user,
                       "rrss": "facebook"})

    match_pinterest = re.match("^(https:\/\/www.google.com\/url\?q=|)" +
                               "(http:\/\/www\.|https:\/\/www\.|http:\/\/|" +
                               "https:\/\/)?[a-z0-9\.]*?(pinterest+)\.[a-z]" +
                               "{2,5}(:[0-9]{1,5})?\/(.*?)(%3|\/|&)(.*)"
                              , data[1])
    if (match_pinterest):
        pinterest_user = ""
        if ('/' in match_pinterest.groups()[4].strip("/")):
            pinterest_user = match_pinterest.groups()[4].split('/')[0]
        elif ("/pin/" not in match_pinterest.groups()[4].strip('/')):
            pinterest_user = match_pinterest.groups()[4].strip('/')

        if ('?' in pinterest_user):
            pinterest_user = pinterest_user.split('?')[0]

        usernames.append({"source": source,
                          "type": type_s,
                          "usernames": pinterest_user,
                          "rrss": "pinterest"})
        match_name = re.match("^(.*?) \((.*)\)(.*)?Pinterest(.*)?$", data[0])
        pinterest_name = ""
        if (match_name):
            pinterest_name = match_name.groups()[0].strip()
            names.append({"source": source,
                          "type": type_s,
                          "name": pinterest_name,
                          "rrss": "pinterest"})
        social.append({"source": source,
                       "type": type_s,
                       "name": pinterest_name,
                       "user": pinterest_user,
                       "rrss": "pinterest"})

    match_tiktok = re.match("^(https:\/\/www.google.com\/url\?q=|)" +
                            "(http:\/\/www\.|https:\/\/www\.|http:\/\/|" +
                            "https:\/\/)?[a-z0-9\.]*?(tiktok+)\.[a-z]" +
                            "{2,5}(:[0-9]{1,5})?\/%40(\w+)"
                            , data[1])
    if (match_tiktok):
        tiktok_user = ""
        if ('/' in match_tiktok.groups()[4].strip("/")):
            tiktok_user = match_tiktok.groups()[4].split('/')[0]
        elif ("/pin/" not in match_tiktok.groups()[4].strip('/')):
            tiktok_user = match_tiktok.groups()[4].strip('/')

        if ('?' in tiktok_user):
            tiktok_user = tiktok_user.split('?')[0]

        usernames.append({"source": source,
                          "type": type_s,
                          "usernames": tiktok_user,
                          "rrss": "tiktok"})
        match_name = re.match("^(.*) \(@(\w+)\) Official TikTok .*"
                              , data[0])
        tiktok_name = ""
        if (match_name):
            tiktok_name = match_name.groups()[0].strip()
            names.append({"source": source,
                          "type": type_s,
                          "name": tiktok_name,
                          "rrss": "tiktok"})
        social.append({"source": source,
                       "type": type_s,
                       "name": tiktok_name,
                       "user": tiktok_user,
                       "rrss": "tiktok"})

    if (username in data[1]):
        urls.append(data[1])

    # Hashtags and emails
    s_tags = re.findall(r'(?:\#+[\w_]+[\w\'_\-]*[\w_]+)', data[0])
    s_tags = s_tags + re.findall(r'(?:\#+[\w_]+[\w\'_\-]*[\w_]+)', data[2])
    # s_email = re.findall(r'^([a-zA-Z0-9_\-\.]+)@([a-zA-Z0-9_\-\.]+)\.([a-zA-Z]{2,5})$', data[0])
    s_email = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}', data[0])
    # s_email = s_email + re.findall(r'^([a-zA-Z0-9_\-\.]+)@([a-zA-Z0-9_\-\.]+)\.([a-zA-Z]{2,5})$', data[2])
    s_email = s_email + re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}', data[2])
    s_user = re.findall(r'(\@[\w\-]+)', data[0])
    s_user = s_user + re.findall(r'(\@[\w\-]+)', data[2])

    if (s_tags):
        for h in s_tags:
            hashtags.append({"label": h})
    if (s_email):
        for e in s_email:
            emails.append({"label": e})
    if (s_user):
        for u in s_user:
            users.append({"label": u})

    output['urls'] = urls
    output['usernames'] = usernames
    output['names'] = names
    output['social'] = social
    output['users'] = users
    output['emails'] = emails
    output['hashtags'] = hashtags

    return output


def deep_analysis(names, usernames, searcher, data, output):
    # Initialize
    urls = [] if ('urls' not in output) else output['urls']
    search = [] if ('search' not in output) else output['search']
    rawresult = [] if ('rawresult' not in output) else output['rawresult']

    if (searcher == "google"):
        icon = "fab fa-google"
    elif (searcher == "yahoo"):
        icon = "fab fa-yahoo"
    elif (searcher == "bing"):
        icon = "fab fa-windows"
    elif (searcher == "duckduckgo"):
        icon = "fas fa-kiwi-bird"
    elif (searcher == "yandex"):
        icon = "fab fa-yandex-international"
    elif (searcher == "baidu"):
        icon = "fas fa-paw"
    elif (searcher == "dorks"):
        icon = "fas fa-searchengin"
    else:
        icon = "fas fa-search"

    if searcher == 'google':
        end = ' '
    elif searcher == 'yahoo':
        end = '  '
    elif searcher == 'bing':
        end = '   '
    elif searcher == 'duckduckgo':
        end = '    '
    elif searcher == 'yandex':
        end = '     '
    elif searcher == 'baidu':
        end = '      '
    elif searcher == 'dorks':
        end = '       '
    else:
        end = '        '

    rawresult_item = {"name-node": "References", "title": data[0] + end,
                      "subtitle": "",
                      "icon": icon,
                      "simple": data[0],
                      "url": data[1],
                      "desc": data[2],
                      "link": searcher}
    rawresult.append(rawresult_item)

    search_included = False
    # Evaluate usernames in urls
    for user in usernames:
        if user in data[1]:
            if data[1] not in urls:
                urls.append(data[1])
                output['urls'] = urls

            search_included = True
            search_item = {"name-node": "References", "title": data[0] + end,
                           "subtitle": "",
                           "icon": icon,
                           "help": "Title : " + data[0] + "\nURL : " +
                           data[1] + "\nDesc : " + data[2],
                           "simple": data[0],
                           "url": data[1],
                           "desc": data[2],
                           "link": searcher}
            search.append(search_item)

    # Evaluate names in urls
    if not search_included:
        # Title
        if (name_match(names, data[0])):
            search_included = True
            search_item = {"name-node": "References", "title": data[0] + end,
                           "subtitle": "",
                           "icon": icon,
                           "help": "Title : " + data[0] + "\nURL : " +
                           data[1] + "\nDesc : " + data[2],
                           "simple": data[0],
                           "url": data[1],
                           "desc": data[2],
                           "link": searcher}
            search.append(search_item)
        # Url (This makes no sense)
        if not search_included:
            if (name_match(names, data[1])):
                search_included = True
                search_item = {"name-node": "References", "title": data[0] +
                               end,
                               "subtitle": "",
                               "icon": icon,
                               "help": "Title : " + data[0] + "\nURL : " +
                               data[1] + "\nDesc : " + data[2],
                               "simple": data[0],
                               "url": data[1],
                               "desc": data[2],
                               "link": searcher}
                search.append(search_item)
        # Desc
        if not search_included:
            if (name_match(names, data[2])):
                search_included = True
                search_item = {"name-node": "References", "title": data[0] +
                               end,
                               "subtitle": data[1],
                               "icon": icon,
                               "help": "Title : " + data[0] + "\nURL : " +
                               data[1] + "\nDesc : " + data[2],
                               "simple": data[0],
                               "url": data[1],
                               "desc": data[2],
                               "link": searcher}
                search.append(search_item)

    output['rawresult'] = rawresult
    output['search'] = search
    return output

