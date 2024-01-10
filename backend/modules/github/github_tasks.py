#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import os
import sys
import json
import time
from time import strftime
import requests
import re
from bs4 import BeautifulSoup
from datetime import datetime
import traceback

try:
    from factories._celery import create_celery
    from factories.application import create_application
    from celery.utils.log import get_task_logger
    from factories.iKy_functions import analize_rrss
    from factories.iKy_functions import location_geo
    celery = create_celery(create_application())
except ImportError:
    # This is to test the module individually, and I know that is piece of shit
    sys.path.append('../../')
    from factories._celery import create_celery
    from factories.application import create_application
    from celery.utils.log import get_task_logger
    from factories.iKy_functions import analize_rrss
    from factories.iKy_functions import location_geo
    celery = create_celery(create_application())

logger = get_task_logger(__name__)


def findReposFromUsername(username):
    response = requests.get(
        'https://api.github.com/users/%s/repos?per_page=100&sort=pushed' % 
        username).text
    repos = re.findall(r'"full_name":"%s\/(.*?)",.*?"fork":(.*?),' % username, 
                       response)
    nonForkedRepos = []
    for repo in repos:
        if repo[1] == 'false':
            nonForkedRepos.append(repo[0])
    return nonForkedRepos


def findEmailFromContributor(username, repo, contributor):
    response = requests.get('https://github.com/%s/%s/commits?author=%s' 
                            % (username, repo, contributor)).text
    latestCommit = re.search(r'href="/%s/%s/commit/(.*?)"' % (username, repo), 
                             response)
    if latestCommit:
        latestCommit = latestCommit.group(1)
    else:
        latestCommit = 'dummy'
    commitDetails = requests.get('https://github.com/%s/%s/commit/%s.patch' % 
                                 (username, repo, latestCommit)).text
    email = re.search(r'<(.*)>', commitDetails)
    if email:
        email = email.group(1)
    return email


def findEmailFromUsername(username):
    repos = findReposFromUsername(username)
    for repo in repos:
        email = findEmailFromContributor(username, repo, username)
        if email:
            return email
    return False


def p_github(email, from_m="Initial"):
    """ Task of Celery that get info from github """

    # Code to develop the frontend without burning APIs
    cd = os.getcwd()
    td = os.path.join(cd, "outputs")
    output = "output-github.json"
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
    if ("@" in email):
        username = email.split("@")[0]
    else:
        username = email

    req = requests.get("https://api.github.com/users/%s" % username)
    print(req.json())

    if (req.json().get("message", "") == 'Not Found'):
        raise Exception("iKy - User not found")

    # if (req.json().get("type", "") == 'Organization'):
    #     raise Exception("It's an Organization")

    today = datetime.today()
    actual_year_from = datetime(today.year, today.month, 1).strftime("%Y-%m-%d")
    actual_year_to = datetime(today.year, today.month, today.day).strftime("%Y-%m-%d")

    # print(actual_year_from)

    svg_req = f"https://github.com/{username}?tab=overview&amp;" + \
              f"from={actual_year_from}&amp;" + \
              f"to={actual_year_to}"
    # svg_req = "https://github.com/KennBro?tab=overview&amp;from=2023-11-01&amp;to=2023-11-18"
    # print(svg_req)

    svg_actual_r = requests.get(svg_req)

    html_doc = BeautifulSoup(svg_actual_r.content, "html.parser")
    svg_actual_div = html_doc.find('div', class_='graph-before-activity-overview')
    # print(f"Type : {type(svg_actual_r)}")

    for tag in svg_actual_div.find_all():
        tag.replace_with(tag.decode_contents())

    # print(svg_actual_div)

    # Change size
    svg_actual = svg_actual_div.text.replace('width: 11px', 'width: 13px; height: 13px;')

    # Raw Array
    raw_node = json.loads(req.text)

    # Get login
    try:
        login = raw_node['login']
    except Exception:
        raise Exception("User not found")

    # Get email
    if ('email' in raw_node) and (raw_node['email'] is not None):
        email_github = raw_node['email']
    else:
        email_github = findEmailFromUsername(login)

    # Get twitter account
    if ('twitter_username' in raw_node) and (raw_node['twitter_username'] is not None):
        twitter_username = raw_node['twitter_username']
    else:
        twitter_username = False

    # Total
    total = []
    total.append({'module': 'github'})
    total.append({'param': username})
    # Evaluates the module that executed the task and set validation
    if (from_m == 'Initial'):
        total.append({'validation': 'no'})
    else:
        total.append({'validation': 'soft'})

    if ('message' not in raw_node) or (raw_node['message'] != 'Not Found'):
        # Graphic Array
        graphic = []

        # Profile Array
        presence = []
        profile = []

        # Timeline Array
        timeline = []

        # Gather Array
        gather = []

        # Tasks Array
        tasks = []

        link = "Github"
        gather_item = {"name-node": "Github", "title": "Github",
                       "subtitle": "", "icon": "fab fa-github", "link": link}
        gather.append(gather_item)

        if (email_github):
            gather_item = {"name-node": "Gitemail", "title": "Git Email",
                           "subtitle": email_github, "icon": "fas fa-at",
                           "link": link}
            profile_item = {'email': email_github}
            profile.append(profile_item)
            gather.append(gather_item)
        if ('name' in raw_node):
            gather_item = {"name-node": "Gitname", "title": "Git Name",
                           "subtitle": raw_node['name'], "icon": "fas fa-user",
                           "link": link}
            profile_item = {'name': raw_node['name']}
            profile.append(profile_item)
            gather.append(gather_item)
        if (email_github):
            gather_item = {"name-node": "GitEmail", "title": "Email",
                           "subtitle": email_github,
                           "icon": "fas fa-envelope",
                           "link": link}
            gather.append(gather_item)
            profile_item = {'email': raw_node['email']}
            profile.append(profile_item)
        if (twitter_username):
            gather_item = {"name-node": "GitTwitter", "title": "Twitter",
                           "subtitle": twitter_username,
                           "icon": "fab fa-twitter",
                           "link": link}
            gather.append(gather_item)
            tasks.append({"module": "twitter",
                            "param": twitter_username})
        if ('company' in raw_node) and (raw_node['company'] is not None):
            gather_item = {"name-node": "GitCompany", "title": "Company",
                           "subtitle": raw_node['company'],
                           "icon": "fas fa-building",
                           "link": link}
            gather.append(gather_item)
            profile_item = {'organization': raw_node['company']}
            profile.append(profile_item)
        if (('blog' in raw_node) and (raw_node['blog'] is not None) and
           (raw_node['blog'] != "")):
            gather_item = {"name-node": "GitBlog", "title": "Blog",
                           "subtitle": raw_node['blog'],
                           "icon": "fas fa-rss-square",
                           "link": link}
            gather.append(gather_item)
        if ('bio' in raw_node) and (raw_node['bio'] is not None):
            gather_item = {"name-node": "GitBio", "title": "Bio",
                           "subtitle": raw_node['bio'],
                           "icon": "fas fa-heart",
                           "link": link}
            gather.append(gather_item)
            analyze = analize_rrss(raw_node['bio'])
            for item in analyze:
                if(item == 'url'):
                    for i in analyze['url']:
                        profile.append(i)
                if(item == 'tasks'):
                    for i in analyze['tasks']:
                        tasks.append(i)

        if ('public_repos' in raw_node):
            gather_item = {"name-node": "GitRepos", "title": "Repos",
                           "subtitle": raw_node['public_repos'],
                           "icon": "fas fa-folder-open", "link": link}
            gather.append(gather_item)
        if ('public_gists' in raw_node):
            gather_item = {"name-node": "GitGists", "title": "Gists",
                           "subtitle": raw_node['public_gists'],
                           "icon": "fas fa-code", "link": link}
            gather.append(gather_item)
        if ('followers' in raw_node):
            gather_item = {"name-node": "GitFollowers", "title": "Followers",
                           "subtitle": raw_node['followers'],
                           "icon": "fas fa-users", "link": link}
            gather.append(gather_item)
        if ('following' in raw_node):
            gather_item = {"name-node": "GitFollowing", "title": "Following",
                           "subtitle": raw_node['following'],
                           "icon": "fas fa-users", "link": link}
            gather.append(gather_item)
        if ('id' in raw_node):
            gather_item = {"name-node": "GitId", "title": "Id",
                           "subtitle": raw_node['id'], "icon": "fas fa-info",
                           "link": link}
            gather.append(gather_item)
        if ('avatar_url' in raw_node):
            gather_item = {"name-node": "GitAvatar", "title": "Avatar",
                           "picture": raw_node['avatar_url'], "subtitle": "",
                           "link": link}
            gather.append(gather_item)
            profile_item = {'photos': [{"picture": raw_node['avatar_url'],
                                        "title": "Github"}]}
            profile.append(profile_item)
        if ('location' in raw_node) and (raw_node['location'] is not None):
            profile_item = {'location': raw_node['location']}
            profile.append(profile_item)
            loc = location_geo(raw_node['location'])
            print(f"LOC: {raw_node['location']} - {loc}")
            if (loc):
                loc_item = {'Caption': 'Github',
                                'Accessability': '',
                                'Latitude': loc['Latitude'],
                                'Longitude': loc['Longitude'],
                                'Name': loc['Caption'],
                                'Time': ''
                                }
                profile.append({'geo': loc_item})
        if ('created_at' in raw_node) and (raw_node['created_at'] is not None):
            ctime = datetime.strptime(raw_node['created_at'],
                                      "%Y-%m-%dT%H:%M:%SZ")
            timeline_item = {'date': ctime.strftime("%Y/%m/%d %H:%M:%S"),
                             'action': 'Github : Create Account',
                             'icon': 'fab fa-github'}
            timeline.append(timeline_item)
        if ('updated_at' in raw_node) and (raw_node['updated_at'] is not None):
            mtime = datetime.strptime(raw_node['updated_at'],
                                      "%Y-%m-%dT%H:%M:%SZ")
            timeline_item = {'date': mtime.strftime("%Y/%m/%d %H:%M:%S"),
                             'action': 'Github : Update Account',
                             'icon': 'fab fa-github'}
            timeline.append(timeline_item)

        if ('followers' in raw_node and 'following' in raw_node):
            presence.append({"name": "github",
                             "children": [
                                 {"name": "followers", 
                                  "value": int(raw_node['followers'])},
                                 {"name": "following", 
                                  "value": int(raw_node['following'])},
                             ]})
            profile.append({'presence': presence})
        
        social = []
        social_item = {"name": "Github",
                    "url": "https://www.github.com/" + username,
                    "icon": "fab fa-github",
                    "source": "Github",
                    "username": username}
        social.append(social_item)
        profile.append({"social": social})

        # Please, respect the order of items in the total array
        # Because the frontend depend of that (By now)
        total.append({'raw': raw_node})
        graphic.append({'github': gather})
        graphic.append({'cal_actual': svg_actual})
        graphic.append({'cal_previous': ''})
        total.append({'graphic': graphic})
        total.append({'profile': profile})
        total.append({'timeline': timeline})
        total.append({'tasks': tasks})

    return total


@celery.task
def t_github(email, from_m="Initial"):
    total = []
    tic = time.perf_counter()
    try:
        total = p_github(email, from_m)
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
        total.append({'module': 'github'})
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
    logger.info(f"Github - Response in {toc - tic:0.4f} seconds")

    return total


def output(data):
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    email = sys.argv[1]
    result = t_github(email)
    output(result)
