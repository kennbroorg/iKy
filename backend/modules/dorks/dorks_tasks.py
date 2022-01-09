#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import sys
import json
import traceback
import random
import time
import yagooglesearch
import collections
from fuzzywuzzy import process
from apiclient.discovery import build


try:
    from factories._celery import create_celery
    from factories.application import create_application
    from factories.fontcheat import fontawesome_cheat_5, search_icon_5
    from factories.configuration import api_keys_search
    from factories.iKy_functions import simple_analysis
    from factories.iKy_functions import deep_analysis
    from celery.utils.log import get_task_logger
    celery = create_celery(create_application())
except ImportError:
    # This is to test the module individually, and I know that is piece of shit
    sys.path.append('../../')
    from factories._celery import create_celery
    from factories.application import create_application
    from factories.fontcheat import fontawesome_cheat_5, search_icon_5
    from factories.configuration import api_keys_search
    from factories.iKy_functions import simple_analysis
    from factories.iKy_functions import deep_analysis
    from celery.utils.log import get_task_logger
    celery = create_celery(create_application())

logger = get_task_logger(__name__)


def p_dorks_cse(api_key, cx, keywords, dorks=''):
    # Modifiers for dorks
    if (dorks == ''):
        dorks = {'twitter': 'site:twitter.com',
                 'github': 'site:github.com',
                 'instagram': 'site:instagram.com',
                 'keybase': 'site:keybase.io',
                 'linkedin': 'site:linkedin.com',
                 # 'facebook': 'site:facebook.com',
                 #  'pinterest': 'site:pinterest.com',
                 'tiktok': 'site:tiktok.com'}

    node = []
    resource = build("customsearch", 'v1', developerKey=api_key).cse()
    result = resource.list(q=keywords, cx=cx).execute()

    for item in result['items']:
        node.append({'dork': 'username', 'titles': item["title"],
                    'links': item["link"],
                     'descriptions': item["snippet"]})

    for dork in dorks:
        timeDelay = random.randrange(0, 15)
        time.sleep(timeDelay)
        query = f"{keywords} {dorks[dork]}"

        print(f"Processing QUERY : {query}")
        result = resource.list(q=query, cx='40b052eff66bf4730').execute()

        if ("items" in result):
            for item in result['items']:
                node.append({'dork': dork, 'titles': item["title"],
                            'links': item["link"],
                             'descriptions': item["snippet"]})
                break

    return node


def p_dorks_yagoogle(keywords, dorks=''):
    # Modifiers for dorks
    if (dorks == ''):
        dorks = {'twitter': 'site:twitter.com',
                 'github': 'site:github.com',
                 'instagram': 'site:instagram.com',
                 'keybase': 'site:keybase.io',
                 'linkedin': 'site:linkedin.com',
                 # 'facebook': 'site:facebook.com',
                 # 'pinterest': 'site:pinterest.com',
                 'tiktok': 'site:tiktok.com'}

    node = []

    # Search without dorks
    query = f"{keywords}"
    print(f"Processing QUERY : {query}")
    client = yagooglesearch.SearchClient(
        query,
        tbs="li:1",
        max_search_result_urls_to_return=10,
        http_429_cool_off_time_in_minutes=1,
        http_429_cool_off_factor=1.5,
        # proxy="socks5h://127.0.0.1:9050",
        verbosity=5,
        verbose_output=True,
        verify_ssl=False
    )

    client.assign_random_user_agent()
    search = client.search()

    for u in search:
        node.append({'dork': 'username', 'titles': u["title"],
                    'links': u["url"],
                     'descriptions': u["description"]})

    for dork in dorks:
        timeDelay = random.randrange(0, 15)
        time.sleep(timeDelay)
        query = f"{keywords} {dorks[dork]}"

        print(f"Processing QUERY : {query}")
        client = yagooglesearch.SearchClient(
            query,
            # tbs="li:1",
            max_search_result_urls_to_return=1,
            http_429_cool_off_time_in_minutes=45,
            http_429_cool_off_factor=1.5,
            # proxy="socks5h://127.0.0.1:9050",
            verbosity=0,
            verbose_output=True,
        )
        client.assign_random_user_agent()
        search = client.search()

        for u in search:
            node.append({'dork': dork, 'titles': u["title"],
                        'links': u["url"],
                         'descriptions': u["description"]})

    return node


def p_dorks(keywords, dorks, from_m="Initial"):
    """ Task of Celery that get info from google dorks
    Social Networks :
        - twitter
        - github
        - instagram
        - keybase
        - linkedin
        - tiktok
    TODO :
        - gitlab
        - tinder
        - bitbucket
        - reddit
        - youtube
        - twitch
        - facebook
        - pinterest
    """

    api_key = api_keys_search('cse_api_key')
    cx = api_keys_search('cse_cx')

    if (api_key):
        raw_node = p_dorks_cse(api_key, cx, keywords, dorks)
    else:
        raw_node = p_dorks_yagoogle(keywords, dorks)

    # Icons unicode
    font_list = fontawesome_cheat_5()

    output = {}
    for i in raw_node:
        try:
            output = simple_analysis(i['dork'], "username", keywords,
                                     [i['titles'],
                                      i['links'],
                                      i['descriptions']
                                      ], output)
        except Exception:
            traceback.print_exc()
            continue

    # Different usernames
    try:
        users = [item['usernames'].strip() for item in output['usernames']]
    except Exception:
        users = []

    # Different name
    try:
        names = [item['name'].strip() for item in output['names']]
        names_refined = collections.Counter(names)
    except Exception:
        names = []
        names_refined = []

    try:
        best_match = process.extractBests(
            collections.Counter(names).most_common(2)[0][0],
            names, limit=len(names), score_cutoff=80)
    except Exception:
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

        # elif (count >= social_count[s_c] and name_match(
        #         name_tokens, s_c.split("-|-")[2])):
        #     social_refined[a] = s_c
        #     rrss = s_c.split("-|-")[0]
        #     count = social_count[s_c]

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

    # Deep Analysis
    for i in raw_node:
        try:
            output = deep_analysis(name_tokens, username_refined, i['dork'],
                                   [i['titles'],
                                   i['links'],
                                   i['descriptions']], output)
        except Exception:
            continue

    # Total
    total = []
    total.append({'module': 'dorks'})
    total.append({'param': keywords})
    # Evaluates the module that executed the task and set validation
    total.append({'validation': 'no'})

    # Graphic Array
    graphic = []

    # Profile Array
    profile = []

    # Timeline Array
    timeline = []

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

    # TODO : Repair raw-node
    total.append({'raw': raw_node})
    graphic.append({'names': name_cloud})
    graphic.append({'username': username_cloud})
    graphic.append({'social': social_raw})
    graphic.append({'rawresults': output["rawresult"]})
    graphic.append({'searches': output["search"]})
    graphic.append({'mentions': output["users"]})
    graphic.append({'hashtags': output["hashtags"]})
    graphic.append({'emails': output["emails"]})
    total.append({'graphic': graphic})
    total.append({'profile': profile})
    total.append({'timeline': timeline})
    total.append({'tasks': tasks})

    return total


@celery.task
def t_dorks(user, dorks=''):
    # Principal Variable
    total = []
    # Take initial time
    tic = time.perf_counter()

    # try execution principal function
    try:
        total = p_dorks(user, dorks)
    # Error handle
    except Exception as e:
        # Error description
        traceback.print_exc()
        traceback_text = traceback.format_exc()
        code = 10
        if ('Search dork Error' in traceback_text):
            code = 5

        # Set module name in JSON format
        total.append({"module": "dork"})
        total.append({"param": user})
        total.append({"validation": "null"})

        # Set status code and reason
        status = []
        status.append(
            {
                "code": code,
                "reason": "{}".format(e),
                "traceback": traceback_text,
            }
        )
        total.append({"raw": status})

    # Take final time
    toc = time.perf_counter()
    # Show process time
    logger.info(f"Dork - Response in {toc - tic:0.4f} seconds")

    return total


def output(data):
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    username = sys.argv[1]
    # dorks = {'twitter': 'site:twitter.com',
    #          'github': 'site:github.com'}
    # dorks = {'twitter': 'site:twitter.com'}
    dorks = {'linkedin': 'site:linkedin.com'}
    # dorks = ''
    result = t_dorks(username, dorks=dorks)
    output(result)
