#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import sys
import json
import requests
from search_engine_parser import YahooSearch, GoogleSearch, BingSearch
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

# Compatibility code
try:
    # Python 2: "unicode" is built-in
    unicode
except NameError:
    unicode = str


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
    # Initialize
    urls = [] if ('urls' not in output) else output['urls']
    usernames = [] if ('usernames' not in output) else output['usernames']
    names = [] if ('names' not in output) else output['names']
    social = [] if ('social' not in output) else output['social']
    users = [] if ('users' not in output) else output['users']
    hashtags = [] if ('hashtags' not in output) else output['hashtags']
    emails = [] if ('emails' not in output) else output['emails']

    # Decode URL
    match_decode = re.match("(https?)(.*)(https?[^/]*)(.*)$", data[1])
    if (match_decode):
        data[1] = urllib.parse.unquote_plus(match_decode.groups()[2])

    # Rules
    match_twitter = re.match("^(http:\/\/www\.|https:\/\/www\.|http:\/\/|htt" +
                             "ps:\/\/)?[a-z0-9\.]*?(twitter+)\.[a-z]{2,5}(:[" +
                             "0-9]{1,5})?\/(.*)?(/)?(.*)?$", data[1])
    if (match_twitter):
        twitter_user=""
        if ('/' in match_twitter.groups()[3]):
            twitter_user = match_twitter.groups()[3].split('/')[0]
        else:
            twitter_user = match_twitter.groups()[3]
        if ('?' in twitter_user):
            twitter_user = twitter_user.split('?')[0]
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

    match_github = re.match("^(http:\/\/www\.|https:\/\/www\.|http:\/\/|http" +
                            "s:\/\/)?[a-z0-9\.]*?(github+)\.[a-z]{2,5}(:[0-9" +
                            "]{1,5})?\/(.*)?(/)?(.*)?$", data[1])
    if (match_github):
        github_user=""
        if ('/' in match_github.groups()[3]):
            github_user = match_github.groups()[3].split('/')[0]
        else:
            github_user = match_github.groups()[3]
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

    match_instagram = re.match('^(http:\/\/www\.|https:\/\/www\.|http:\/\/|https:\/\/)?[a-z0-9\.]*?(instagram+)\.[a-z]{2,5}(:[0-9]{1,5})?\/(.*)?(/)?(.*)?$', data[1])
    # match_instagram = re.match('^(http:\/\/www\.|https:\/\/www\.|http:\/\/|' +
    #                            'https:\/\/)?[a-z0-9.]?(instagram+)\.[a-z]' +
    #                            '{2,5}(:[0-9]{1,5})?/(.*)?(/)?(.*)?$', data[1])
    if (match_instagram):
        instagram_user=""
        if ('/' in match_instagram.groups()[3]):
            instagram_user = match_instagram.groups()[3].split('/')[0]
        else:
            instagram_user = match_instagram.groups()[3]
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

    match_keybase = re.match('^(http:\/\/www\.|https:\/\/www\.|http:\/\/|https:\/\/)?[a-z0-9\.]*?(keybase+)\.[a-z]{2,5}(:[0-9]{1,5})?\/(.*)?(/)?(.*)?$', data[1])
    # match_keybase = re.match('^(http:\/\/www\.|https:\/\/www\.|http:\/\/|' +
    #                          'https:\/\/)?[a-z0-9.]?(keybase+)\.[a-z]' +
    #                          '{2,5}(:[0-9]{1,5})?/(.*)?(/)?(.*)?$', data[1])
    if (match_keybase):
        keybase_user=""
        if ('/' in match_keybase.groups()[3]):
            keybase_user = match_keybase.groups()[3].split('/')[0]
        else:
            keybase_user = match_keybase.groups()[3]
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

    match_linkedin = re.match('^(http:\/\/www\.|https:\/\/www\.|http:\/\/|https:\/\/)?[a-z0-9\.]*?(linkedin+)\.[a-z]{2,5}(:[0-9]{1,5})?\/in\/(.*)?(/)?(.*)?$'
                              , data[1])
    if (match_linkedin):
        linkedin_user=""
        if ('/' in match_linkedin.groups()[3]):
            linkedin_user = match_linkedin.groups()[3].split('/')[0]
        else:
            linkedin_user = match_linkedin.groups()[3]
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

    match_facebook = re.match('^(http:\/\/www\.|https:\/\/www\.|http:\/\/|https:\/\/)?[a-z0-9\.]*?(facebook+)\.[a-z]{2,5}(:[0-9]{1,5})?\/(.*)?(/)?(.*)?$'
                              , data[1])
    if (match_facebook):
        facebook_user=""
        if ('/' in match_facebook.groups()[3]):
            facebook_user = match_facebook.groups()[3].split('/')[0]
        else:
            facebook_user = match_facebook.groups()[3]
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

    match_pinterest = re.match('^(http:\/\/www\.|https:\/\/www\.|http:\/\/|https:\/\/)?[a-z0-9\.]*?(pinterest+)\.[a-z]{2,5}(:[0-9]{1,5})?\/(.*)?(\/)?(.*)?$'
                              , data[1])
    if (match_pinterest):
        pinterest_user=""
        if ('/' in match_pinterest.groups()[3].strip("/")):
            pinteres_user = match_pinterest.groups()[3].split('/')[0]
        elif ("/pin/" not in match_pinterest.groups()[3].strip('/')):
            pinterest_user = match_pinterest.groups()[3].strip('/')

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
    match_decode = re.match("(https?)(.*)(https?[^/]*)(.*)$", data[1])
    if (match_decode):
        data[1] = urllib.parse.unquote_plus(match_decode.groups()[2])

    # Initialize
    urls = [] if ('urls' not in output) else output['urls']
    search = [] if ('search' not in output) else output['search']

    if (searcher == "google"):
        icon = "fab fa-yahoo"
    elif (searcher == "yahoo"):
        icon = "fab fa-google"
    elif (searcher == "bing"):
        icon = "fab fa-windows"
    else:
        icon = "fas fa-search"

    if searcher == 'google':
        end = '.'
    elif searcher == 'yahoo':
        end = '..'
    elif searcher == 'bing':
        end = '...'
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

    output['search'] = search
    return output


@celery.task
def t_search(username, from_m="Initial"):
    """ Task of Celery that get info from searchers """
    output = {}

    # Icons unicode
    font_list = fontawesome_cheat_5()

    search_args = (username, 1)

    gsearch = GoogleSearch()
    ysearch = YahooSearch()
    bsearch = BingSearch()
    try:
        gresults = gsearch.search(*search_args, cache=False)
    except:
        gresults = []
    try:
        yresults = ysearch.search(*search_args, cache=False)
    except:
        yresults = []
    try:
        bresults = bsearch.search(*search_args, cache=False)
    except:
        bresults = []

    # Raw Array
    raw_node = {
        "Google": gresults,
        "Yahoo": yresults,
        "Bing": bresults}

    if (raw_node['Google'] != []):
        for i in range(len(raw_node['Google']['titles'])):
            output = simple_analysis("google", "username", username,
                            [raw_node['Google']['titles'][i],
                             raw_node['Google']['links'][i],
                             raw_node['Google']['descriptions'][i],
                             ], output)

    if (raw_node['Yahoo'] != []):
        for i in range(len(raw_node['Yahoo']['titles'])):
            output = simple_analysis("yahoo", "username", username,
                                     [raw_node['Yahoo']['titles'][i],
                                     raw_node['Yahoo']['links'][i],
                                     raw_node['Yahoo']['descriptions'][i]
                                     ], output)
    if (raw_node['Bing'] != []):
        for i in range(len(raw_node['Bing']['titles'])):
            output = simple_analysis("bing", "username", username,
                            [raw_node['Bing']['titles'][i],
                             raw_node['Bing']['links'][i],
                             raw_node['Bing']['descriptions'][i]
                             ], output)

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
    for s in social:
        if (s['rrss'] + '-|-' + s['user'] + '-|-' + s['name'] not in social_count):
            social_count[s['rrss'] + '-|-' + s['user'] + '-|-' + s['name']] = 1
        else:
            social_count[s['rrss'] + '-|-' + s['user'] + '-|-' + s['name']] = social_count[s['rrss'] + '-|-' + s['user'] + '-|-' + s['name']] + 1

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
            output = deep_analysis(name_tokens, username_refined, 'google',
                            [raw_node['Google']['titles'][i],
                             raw_node['Google']['links'][i],
                             raw_node['Google']['descriptions'][i],
                             ], output)
    if (raw_node['Yahoo'] != []):
        for i in range(len(raw_node['Yahoo']['titles'])):
            output = deep_analysis(name_tokens, username_refined, 'yahoo',
                            [raw_node['Yahoo']['titles'][i],
                             raw_node['Yahoo']['links'][i],
                             raw_node['Yahoo']['descriptions'][i],
                             ], output)
    if (raw_node['Bing'] != []):
        for i in range(len(raw_node['Bing']['titles'])):
            output = deep_analysis(name_tokens, username_refined, 'bing',
                            [raw_node['Bing']['titles'][i],
                             raw_node['Bing']['links'][i],
                             raw_node['Bing']['descriptions'][i],
                             ], output)

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

    output['search'].append({"name-node": "google", "title": "Searcher",
                            "subtitle": "",
                            "icon": "fas fa-search",
                            "link": "google"})
    output['search'].append({"name-node": "bing", "title": "Searcher",
                            "subtitle": "",
                            "icon": "fas fa-search",
                            "link": "bing"})
    output['search'].append({"name-node": "yahoo", "title": "Searcher",
                            "subtitle": "",
                            "icon": "fas fa-search",
                            "link": "yahoo"})

    profile.append({"name": name_complete})

    # TODO : Repair raw-node
    total.append({'raw': 'raw'})
    graphic.append({'names': name_cloud})
    graphic.append({'username': username_cloud})
    graphic.append({'social': socialp})
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
