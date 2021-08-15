#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import sys
import json
import requests
import traceback
from shutil import rmtree
# from search_engine_parser import YahooSearch, GoogleSearch, BingSearch
from search_engine_parser.core.engines.bing import Search as BingSearch
from search_engine_parser.core.engines.google import Search as GoogleSearch
from search_engine_parser.core.engines.yahoo import Search as YahooSearch
from search_engine_parser.core.engines.duckduckgo import Search as DuckDuckGoSearch
from search_engine_parser.core.engines.yandex import Search as YandexSearch
from search_engine_parser.core.engines.baidu import Search as BaiduSearch
import re
import urllib.parse
import collections
from fuzzywuzzy import process
from time import gmtime, strftime

try:
    from factories._celery import create_celery
    from factories.application import create_application
    from factories.fontcheat import fontawesome_cheat_5, search_icon_5
    from celery.utils.log import get_task_logger
    celery = create_celery(create_application())
except ImportError:
    # This is to test the module individually, and I know that is piece of shit
    sys.path.append('../../')
    from factories._celery import create_celery
    from factories.application import create_application
    from factories.fontcheat import fontawesome_cheat_5, search_icon_5
    from celery.utils.log import get_task_logger
    celery = create_celery(create_application())

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

logger = get_task_logger(__name__)


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
    # Resolve
    # https://www.facebook.com/public/Jezer-Ferreira
    # https://www.instagram.com/p/BtRNU3vlf1I/ (Descartar)
    # Initialize
    urls = [] if ('urls' not in output) else output['urls']
    usernames = [] if ('usernames' not in output) else output['usernames']
    names = [] if ('names' not in output) else output['names']
    social = [] if ('social' not in output) else output['social']
    users = [] if ('users' not in output) else output['users']
    hashtags = [] if ('hashtags' not in output) else output['hashtags']
    emails = [] if ('emails' not in output) else output['emails']

    # Decode URL
    print("+++++++++++++++++++++++++++++++++++++++++++")
    print(source)
    print("+++++++++++++++++++++++++++++++++++++++++++")
    print("Data 0 :\n{}".format(data[0]))
    print("Data 1 :\n{}".format(data[1]))
    # match_decode = re.match("(https?)(.*)(https?[^/]*)(.*)$", data[1])
    # if (match_decode):
    #     data[1] = urllib.parse.unquote_plus(match_decode.groups()[2])

    print()
    # Rules
    # match_twitter = re.match("^(https:\/\/www.google.com\/url\?q=|)(http:\/" +
    #                          "\/www\.|https:\/\/www\.|http:\/\/|https:\/\/)" +
    #                          "?[a-z0-9\.]*?(twitter+)\.[a-z]{2,5}(:[0-9]" +
    #                          "{1,5})?\/(.*?)(%3|\/|&)(.*)", data[1])
    # New REGEX with w+
    match_twitter = re.match("^(https:\/\/www.google.com\/url\?q=|)(http:\/" +
                             "\/www\.|https:\/\/www\.|http:\/\/|https:\/\/)" +
                             "?[a-z0-9\.]*?(twitter+)\.[a-z]{2,5}(:[0-9]" +
                             "{1,5})?\/(\w+)", data[1])
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

    match_github = re.match("^(https:\/\/www.google.com\/url\?q=|)" +
                            "(http:\/\/www\.|https:\/\/www\.|http:\/\/|http" +
                            "s:\/\/)?[a-z0-9\.]*?(github+)\.[a-z]{2,5}(:[0-9" +
                            "]{1,5})?\/(.*?)(%3|\/|&)(.*)", data[1])
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
                               "{2,5}(:[0-9]{1,5})?\/([^p].*?)(%3|\/)(.*)"
                               , data[1])
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

    match_keybase = re.match("^(https:\/\/www.google.com\/url\?q=|)" +
                             "(http:\/\/www\.|https:\/\/www\.|http:\/\/|" +
                             "https:\/\/)?[a-z0-9\.]*?(keybase+)\.[a-z]" +
                             "{2,5}(:[0-9]{1,5})?\/(.*?)(%3|\/|&)(.*)", data[1])
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

    match_linkedin = re.match("^(https:\/\/www.google.com\/url\?q=|)" +
                              "(http:\/\/www\.|https:\/\/www\.|http:\/\/|" +
                              "https:\/\/)?[a-z0-9\.]*?(linkedin+)\.[a-z]" +
                              "{2,5}(:[0-9]{1,5})?\/in\/(.*?)(%3|\/|&)(.*)"
                              , data[1])
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

    match_facebook = re.match("^(https:\/\/www.google.com\/url\?q=|)" +
                              "(http:\/\/www\.|https:\/\/www\.|http:\/\/|" +
                              "https:\/\/)?[a-z0-9\.]*?(facebook+)\.[a-z]" +
                              "{2,5}(:[0-9]{1,5})?\/(.*?)(%3|\/|&)(.*)"
                              , data[1])
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
    s_email = re.findall(r'^([a-zA-Z0-9_\-\.]+)@([a-zA-Z0-9_\-\.]+)\.([a-zA-Z]{2,5})$', data[0])
    s_email = s_email + re.findall(r'^([a-zA-Z0-9_\-\.]+)@([a-zA-Z0-9_\-\.]+)\.([a-zA-Z]{2,5})$', data[2])
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
    # Decode URL
    # match_decode = re.match("(https?)(.*)(https?[^/]*)(.*)$", data[1])
    # if (match_decode):
    #     data[1] = urllib.parse.unquote_plus(match_decode.groups()[2])

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


@celery.task
def t_search(username, from_m="Initial"):
    """ Task of Celery that get info from searchers """
    output = {}

    # Fix : eliminate cache directory
    try:
        rmtree("cache")
    except Exception:
        pass

    # Icons unicode
    font_list = fontawesome_cheat_5()

    search_args = (username, 1)

    gsearch = GoogleSearch()
    ysearch = YahooSearch()
    bsearch = BingSearch()
    dsearch = DuckDuckGoSearch()
    asearch = YandexSearch()
    usearch = BaiduSearch()
    try:
        gsearch.clear_cache()
        gresults = gsearch.search(*search_args, cache=False)
    except Exception:
        gresults = []
    try:
        ysearch.clear_cache()
        yresults = ysearch.search(*search_args, cache=False)
    except Exception:
        yresults = []
    try:
        bsearch.clear_cache()
        bresults = bsearch.search(*search_args, cache=False)
    except Exception:
        bresults = []
    try:
        dsearch.clear_cache()
        dresults = dsearch.search(*search_args, cache=False)
    except Exception:
        dresults = []
    try:
        asearch.clear_cache()
        aresults = asearch.search(*search_args, cache=False)
    except Exception:
        aresults = []
    try:
        usearch.clear_cache()
        uresults = usearch.search(*search_args, cache=False)
    except Exception:
        uresults = []

    # Raw Array
    raw_node = {
        "Google": gresults,
        "Yahoo": yresults,
        "Bing": bresults,
        "Yandex": aresults,
        "Baidu": uresults,
        "DuckDuckGo": dresults}

    print(raw_node)
    if (raw_node['Google'] != []):
        for i in range(len(raw_node['Google']['titles'])):
            try:
                output = simple_analysis("google", "username", username,
                                [raw_node['Google']['titles'][i],
                                raw_node['Google']['links'][i],
                                raw_node['Google']['descriptions'][i],
                                ], output)
            except Exception:
                continue
    if (raw_node['Yahoo'] != []):
        for i in range(len(raw_node['Yahoo']['titles'])):
            try:
                output = simple_analysis("yahoo", "username", username,
                                         [raw_node['Yahoo']['titles'][i],
                                         raw_node['Yahoo']['links'][i],
                                         raw_node['Yahoo']['descriptions'][i]
                                         ], output)
            except Exception:
                continue
    if (raw_node['Bing'] != []):
        for i in range(len(raw_node['Bing']['titles'])):
            try:
                output = simple_analysis("bing", "username", username,
                                [raw_node['Bing']['titles'][i],
                                raw_node['Bing']['links'][i],
                                raw_node['Bing']['descriptions'][i]
                                ], output)
            except Exception:
                continue
    if (raw_node['DuckDuckGo'] != []):
        for i in range(len(raw_node['DuckDuckGo']['titles'])):
            try:
                output = simple_analysis("duckduckgo", "username", username,
                                [raw_node['DuckDuckGo']['titles'][i],
                                raw_node['DuckDuckGo']['links'][i],
                                raw_node['DuckDuckGo']['descriptions'][i]
                                ], output)
            except Exception:
                continue
    if (raw_node['Yandex'] != []):
        for i in range(len(raw_node['Yandex']['titles'])):
            try:
                output = simple_analysis("yandex", "username", username,
                                [raw_node['Yandex']['titles'][i],
                                raw_node['Yandex']['links'][i],
                                raw_node['Yandex']['descriptions'][i]
                                ], output)
            except Exception:
                continue
    if (raw_node['Baidu'] != []):
        for i in range(len(raw_node['Baidu']['titles'])):
            try:
                output = simple_analysis("baidu", "username", username,
                                [raw_node['Baidu']['titles'][i],
                                raw_node['Baidu']['links'][i],
                                raw_node['Baidu']['descriptions'][i]
                                ], output)
            except Exception:
                continue

    print("Output", output)
    # Different usernames
    try:
        users = [item['usernames'].strip() for item in output['usernames']]
    except:
        users = []

    # Different name
    try:
        names = [item['name'].strip() for item in output['names']]
        names_refined = collections.Counter(names)
    except:
        names = []
        names_refined = []

    try:
        best_match = process.extractBests(collections.Counter(names).most_common(2)[0][0], names, limit=len(names), score_cutoff=80)
    except:
        best_match = []

    # Tokenize
    name_tokens = []
    for n_ext in best_match:
        for n_int in n_ext[0].split(" "):
            if n_int not in name_tokens:
                name_tokens.append(n_int)
    name_complete = " "
    name_complete = name_complete.join(name_tokens)

    # Search Real Social
    social = sorted(output['social'], key=lambda k: k['rrss'])
    social_count = {}
    # To Convert Keys
    social_raw = []
    link_social = "Social"
    social_item = {"name-node": "Social", "title": "Social",
                   "subtitle": "", "icon": search_icon_5(
                       "child", font_list),
                   "link": link_social}
    social_raw.append(social_item)
    title_count = 0
    nounce = ''
    prev = ''
    for s in social:
        if (s['rrss'] + '-|-' + s['user'] + '-|-' + s['name'] not in social_count):
            social_count[s['rrss'] + '-|-' + s['user'] + '-|-' + s['name']] = 1
        else:
            social_count[s['rrss'] + '-|-' + s['user'] + '-|-' + s['name']] = social_count[s['rrss'] + '-|-' + s['user'] + '-|-' + s['name']] + 1

        # Convert keys
        social_item = {"name-node": "Social" + s['rrss'] + str(title_count),
                       "title": s['rrss'] + " (" + s['source'] + ")" + nounce,
                       "subtitle": s['user'],
                       "icon": search_icon_5(s['rrss'], font_list),
                       "link": link_social}
        social_raw.append(social_item)
        if (s['rrss'] + s['source'] == prev):
            nounce = nounce + ' '
        prev = s['rrss'] + s['source']
        title_count = title_count + 1


    socialp = []
    rrss = ''
    social_refined = []
    a = -1
    for s_c in social_count:
        if (s_c.split("-|-")[0] != rrss):
            a = a + 1
            social_refined.append(s_c)
            rrss = s_c.split("-|-")[0]
            count = social_count[s_c]

        elif (count < social_count[s_c]):
            social_refined[a] = s_c
            rrss = s_c.split("-|-")[0]
            count = social_count[s_c]

        elif (count >= social_count[s_c] and name_match(
                name_tokens, s_c.split("-|-")[2])):
            social_refined[a] = s_c
            rrss = s_c.split("-|-")[0]
            count = social_count[s_c]

    username_refined = []
    if (len(social_refined) > 0):
        link_social = "Social"
        social_item = {"name-node": "Social", "title": "Social",
                       "subtitle": "", "icon": search_icon_5(
                           "child", font_list),
                       "link": link_social}
        socialp.append(social_item)

        for social in social_refined:
            if (social.split("-|-")[1] not in username_refined) and (
                    social.split("-|-")[1] != ''):
                username_refined.append(social.split("-|-")[1])
            social_item = {"name-node": social.split("-|-")[0],
                           "title": social.split("-|-")[0],
                           "subtitle": social.split("-|-")[1],
                           "icon": search_icon_5(
                               social.split("-|-")[0], font_list),
                           "link": link_social}
            socialp.append(social_item)

    if (raw_node['Google'] != []):
        for i in range(len(raw_node['Google']['titles'])):
            try:
                output = deep_analysis(name_tokens, username_refined, 'google',
                                [raw_node['Google']['titles'][i],
                                raw_node['Google']['links'][i],
                                raw_node['Google']['descriptions'][i],
                                ], output)
            except Exception:
                pass
    if (raw_node['Yahoo'] != []):
        for i in range(len(raw_node['Yahoo']['titles'])):
            try:
                output = deep_analysis(name_tokens, username_refined, 'yahoo',
                                [raw_node['Yahoo']['titles'][i],
                                raw_node['Yahoo']['links'][i],
                                raw_node['Yahoo']['descriptions'][i],
                                ], output)
            except Exception:
                pass
    if (raw_node['Bing'] != []):
        for i in range(len(raw_node['Bing']['titles'])):
            try:
                output = deep_analysis(name_tokens, username_refined, 'bing',
                                [raw_node['Bing']['titles'][i],
                                raw_node['Bing']['links'][i],
                                raw_node['Bing']['descriptions'][i],
                                ], output)
            except Exception:
                pass
    if (raw_node['DuckDuckGo'] != []):
        for i in range(len(raw_node['DuckDuckGo']['titles'])):
            try:
                output = deep_analysis(name_tokens, username_refined, 'duckduckgo',
                                [raw_node['DuckDuckGo']['titles'][i],
                                raw_node['DuckDuckGo']['links'][i],
                                raw_node['DuckDuckGo']['descriptions'][i],
                                ], output)
            except Exception:
                pass
    if (raw_node['Yandex'] != []):
        for i in range(len(raw_node['Yandex']['titles'])):
            try:
                output = deep_analysis(name_tokens, username_refined, 'yandex',
                                [raw_node['Yandex']['titles'][i],
                                raw_node['Yandex']['links'][i],
                                raw_node['Yandex']['descriptions'][i],
                                ], output)
            except Exception:
                pass
    if (raw_node['Baidu'] != []):
        for i in range(len(raw_node['Baidu']['titles'])):
            try:
                output = deep_analysis(name_tokens, username_refined, 'baidu',
                                [raw_node['Baidu']['titles'][i],
                                raw_node['Baidu']['links'][i],
                                raw_node['Baidu']['descriptions'][i],
                                ], output)
            except Exception:
                pass

    # Check ENGINE FAILURE
    if (raw_node['Google'] == []):
        search_item = {"name-node": "Engine_failure Google",
                    "title": "Detected and flagged as unusual traffic (Google)",
                    "subtitle": "",
                    "icon": "fab fa-google",
                    "link": "google"}
        output["rawresult"].append(search_item)
        output["search"].append(search_item)
    if (raw_node['Bing'] == []):
        search_item = {"name-node": "Engine_failure Bing",
                    "title": "Detected and flagged as unusual traffic (Bing)",
                    "subtitle": "",
                    "icon": "fab fa-windows",
                    "link": "bing"}
        output["rawresult"].append(search_item)
        output["search"].append(search_item)
    if (raw_node['Yahoo'] == []):
        search_item = {"name-node": "Engine_failure yahoo",
                    "title": "Detected and flagged as unusual traffic (Yahoo)",
                    "subtitle": "",
                    "icon": "fab fa-yahoo",
                    "link": "yahoo"}
        output["rawresult"].append(search_item)
        output["search"].append(search_item)
    if (raw_node['Yandex'] == []):
        search_item = {"name-node": "Engine_failure yandex",
                    "title": "Detected and flagged as unusual traffic (Yandex)",
                    "subtitle": "",
                    "icon": "fab fa-yandex",
                    "link": "yandex"}
        output["rawresult"].append(search_item)
        output["search"].append(search_item)
    if (raw_node['DuckDuckGo'] == []):
        search_item = {"name-node": "Engine_failure duckduckgo",
                    "title": "Detected and flagged as unusual traffic (duckduckgo)",
                    "subtitle": "",
                    "icon": "fas fa-kiwi-bird",
                    "link": "duckduckgo"}
        output["rawresult"].append(search_item)
        output["search"].append(search_item)
    if (raw_node['Baidu'] == []):
        search_item = {"name-node": "Engine_failure baidu",
                    "title": "Detected and flagged as unusual traffic (Baidu)",
                    "subtitle": "",
                    "icon": "fas fa-paw",
                    "link": "baidu"}
        output["rawresult"].append(search_item)
        output["search"].append(search_item)

    # Total
    total = []
    total.append({'module': 'search'})
    total.append({'param': username})
    # Evaluates the module that executed the task and set validation
    total.append({'validation': 'no'})

    # Graphic Array
    graphic = []

    # Profile Array
    profile = []

    # Timeline Array
    timeline = []

    # Gather Array
    gather = []

    # Tasks Array
    tasks = []

    # Prepare other tasks
    for soc in socialp:
        if (soc["subtitle"] != ""):
            tasks.append({"module": soc["title"],
                         "param": soc["subtitle"]})

    name_cloud = []
    for name in names:
        name_cloud.append({"label": name})
    username_cloud = []
    for user in users:
        username_cloud.append({"label": user})

    profile.append({"name": name_complete})

    analized_results = output['search']
    output['search'].append({"name-node": "searcher", "title": "searcher",
                            "subtitle": "",
                            "icon": "fas fa-search",
                            "link": "searcher"})
    output['search'].append({"name-node": "google", "title": "Searcher",
                            "subtitle": "",
                            "icon": "fab fa-google",
                            "link": "google"})
    output['search'].append({"name-node": "bing", "title": "Searcher",
                            "subtitle": "",
                            "icon": "fab fa-windows",
                            "link": "bing"})
    output['search'].append({"name-node": "yahoo", "title": "Searcher",
                            "subtitle": "",
                            "icon": "fab fa-yahoo",
                            "link": "yahoo"})
    output['search'].append({"name-node": "duckduckgo", "title": "Searcher",
                            "subtitle": "",
                            "icon": "fas fa-kiwi-bird",
                            "link": "duckduckgo"})
    output['search'].append({"name-node": "yandex", "title": "Searcher",
                            "subtitle": "",
                            "icon": "fab fa-yandex",
                            "link": "yandex"})
    output['search'].append({"name-node": "baidu", "title": "Searcher",
                            "subtitle": "",
                            "icon": "fas fa-paw",
                            "link": "baidu"})

    # TODO : Repair raw-node
    total.append({'raw': 'raw_node'})
    graphic.append({'names': name_cloud})
    graphic.append({'username': username_cloud})
    graphic.append({'social': social_raw})
    # graphic.append({'social': socialp})
    graphic.append({'rawresults': output["rawresult"]})
    graphic.append({'results': analized_results})
    graphic.append({'searches': output["search"]})
    graphic.append({'mentions': output["users"]})
    graphic.append({'hashtags': output["hashtags"]})
    graphic.append({'emails': output["emails"]})
    total.append({'graphic': graphic})
    total.append({'profile': profile})
    total.append({'timeline': timeline})
    total.append({'tasks': tasks})

    return total


def output(data):
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    username = sys.argv[1]
    result = t_search(username)
    output(result)
