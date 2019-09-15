#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import sys
import json
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import random
from geopy.geocoders import Nominatim

try:
    from factories._celery import create_celery
    from factories.application import create_application
    from celery.utils.log import get_task_logger
    celery = create_celery(create_application())
except ImportError:
    # This is to test the module individually, and I know that is piece of shit
    sys.path.append('../../')
    from factories._celery import create_celery
    from factories.application import create_application
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

def load_dirty_json(dirty_json):
    regex_replace = [(r"([ \{,:\[])(u)?'([^']+)'", r'\1"\3"'),
                     (r" False([, \}\]])", r' false\1'),
                     (r" True([, \}\]])", r' true\1')]
    for r, s in regex_replace:
        dirty_json = re.sub(r, s, dirty_json)
    clean_json = json.loads(dirty_json)
    return clean_json


@celery.task
def t_instagram(username, from_m="Initial"):
    """ Task of Celery that get info from instagram"""

    useragents = [
                'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_1) AppleWebKit/602.2.14 (KHTML, like Gecko) Version/10.0.1 Safari/602.2.14',
                'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.98 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.98 Safari/537.36',
                'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.71 Safari/537.36',
                'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:50.0) Gecko/20100101 Firefox/50.0']

    url = "https://www.instagram.com/%s/" % username
    geolocator = Nominatim(user_agent="iKy")
    req = requests.get(url, headers={'User-Agent':
                      random.choice(useragents)})
    soup = BeautifulSoup(req.text, 'html.parser')

    general_data = soup.find_all('meta', attrs={'property': 'og:description'})
    more_data = soup.find_all('script', attrs={'type': 'text/javascript'})
    description = soup.find('script', attrs={'type': 'application/ld+json'})

    try:
        text = general_data[0].get('content').split()
        description = json.loads(description.get_text())
        profile_meta = json.loads(more_data[3].get_text()[21:].strip(';'))
    except:
        raw_node = {"status": "Fail"}

    profile_data = {"Username": profile_meta['entry_data']['ProfilePage'][0]
                    ['graphql']['user']['username'],
                    "Profile name": description['name'],
                    "URL": description['mainEntityofPage']['@id'],
                    "Followers": text[0], "Following": text[2],
                    "Posts": text[4],
                    "Bio": str(
                        profile_meta['entry_data']['ProfilePage'][0]['graphql']
                        ['user']['biography']),
                    "profile_pic_url": str(profile_meta['entry_data']
                                           ['ProfilePage'][0]['graphql']
                                           ['user']['profile_pic_url_hd']),
                    "is_business_account": str(
                        profile_meta['entry_data']['ProfilePage'][0]['graphql']
                        ['user']['is_business_account']),
                    "connected_to_fb": str(profile_meta['entry_data']
                                           ['ProfilePage'][0]['graphql']
                                           ['user']['connected_fb_page']),
                    "externalurl": str(
                        profile_meta['entry_data']['ProfilePage'][0]['graphql']
                        ['user']['external_url']),
                    "joined_recently": str(profile_meta['entry_data']
                                           ['ProfilePage'][0]['graphql']
                                           ['user']['is_joined_recently']),
                    "business_category_name": str(
                        profile_meta['entry_data']['ProfilePage'][0]['graphql']
                        ['user']['business_category_name']),
                    "is_private": str(
                        profile_meta['entry_data']['ProfilePage'][0]['graphql']
                        ['user']['is_private']),
                    "is_verified": str(
                        profile_meta['entry_data']['ProfilePage'][0]['graphql']
                        ['user']['is_verified'])}

    posts = {}
    if profile_data['is_private'].lower() != 'true':
        for index, post in enumerate(profile_meta['entry_data']['ProfilePage']
                                     [0]['graphql']['user']
                                     ['edge_owner_to_timeline_media']
                                     ['edges']):
            loc = unicode(post['node']['location'])
            try:
                caption = unicode(post['node']['edge_media_to_caption']
                                  ['edges'][0]['node']['text'])
            except:
                caption = "No caption"
            if (loc != "None"):
                locjson = load_dirty_json(loc)
                try:
                    latlong = geolocator.geocode(locjson["name"])
                except:
                    latlong = False
                if latlong:
                    latitude = latlong.latitude
                    longitude = latlong.longitude
                else:
                    latitude = longitude = "None"
            else:
                latitude = longitude = "None"

            if ('accessibility_caption' in post['node']):
                acc_cap = unicode(post['node']['accessibility_caption'])
            else:
                acc_cap = "None"

            posts[index] = {"Caption": caption,
                            "Number of Comments": unicode(post['node'][
                                'edge_media_to_comment']['count']),
                            "Comments Disabled": unicode(post['node'][
                                'comments_disabled']),
                            "Taken At Timestamp": unicode(post['node'][
                                'taken_at_timestamp']),
                            "Number of Likes": unicode(post['node'][
                                'edge_liked_by']['count']),
                            "Location": loc,
                            "Latitude": latitude,
                            "Longitude": longitude,
                            "Accessability Caption": acc_cap
                            }

    # Raw Array
    raw_node = {"Profile": profile_data, "Posts": posts}

    # Total
    total = []
    total.append({'module': 'instagram'})
    total.append({'param': username})
    # Evaluates the module that executed the task and set validation
    if (from_m == 'Initial'):
        total.append({'validation': 'no'})
    else:
        total.append({'validation': 'soft'})

    if ('Fail' not in raw_node):
        # Graphic Array
        graphic = []

        # Profile Array
        profile = []

        # Timeline Array
        timeline = []

        # Gather Array
        gather = []

        link = "Instagram"
        gather_item = {"name-node": "Instagram", "title": "Instagram",
                       "subtitle": "", "icon": "fab fa-instagram",
                       "link": link}
        gather.append(gather_item)

        gather_item = {"name-node": "Instname", "title": "Name",
                       "subtitle": profile_data["Profile name"],
                       "icon": "fas fa-user",
                       "link": link}
        profile_item = {'name': profile_data["Profile name"]}
        profile.append(profile_item)
        gather.append(gather_item)

        gather_item = {"name-node": "InstPosts", "title": "Posts",
                       "subtitle": profile_data["Posts"],
                       "icon": "fas fa-file-alt", "link": link}
        gather.append(gather_item)

        gather_item = {"name-node": "InstFollowers", "title": "Followers",
                       "subtitle": profile_data["Followers"],
                       "icon": "fas fa-users", "link": link}
        gather.append(gather_item)

        gather_item = {"name-node": "InstFollowing", "title": "Following",
                       "subtitle": profile_data["Following"],
                       "icon": "fas fa-users", "link": link}
        gather.append(gather_item)

        gather_item = {"name-node": "InstAvatar", "title": "Avatar",
                       "picture": profile_data["profile_pic_url"],
                       "subtitle": "",
                       "link": link}
        gather.append(gather_item)
        profile_item = {'photos': [{"picture": profile_data["profile_pic_url"],
                                    "title": "Instagram"}]}
        profile.append(profile_item)

        gather_item = {"name-node": "InstBio", "title": "Bio",
                       "subtitle": profile_data["Bio"],
                       "icon": "fas fa-heart",
                       "link": link}
        gather.append(gather_item)

        gather_item = {"name-node": "InstURL", "title": "URL",
                       "subtitle": profile_data["externalurl"],
                       "icon": "fas fa-code",
                       "link": link}
        gather.append(gather_item)

        gather_item = {"name-node": "InstJoin", "title": "Joined Recently",
                       "subtitle": profile_data["joined_recently"],
                       "icon": "fas fa-clock",
                       "link": link}
        gather.append(gather_item)

        gather_item = {"name-node": "InstFacebook", "title": "Facebook",
                       "subtitle": profile_data["connected_to_fb"],
                       "icon": "fab fa-facebook",
                       "link": link}
        gather.append(gather_item)

        gather_item = {"name-node": "InstPrivate", "title": "Private Account",
                       "subtitle": profile_data["is_private"],
                       "icon": "fas fa-user-shield",
                       "link": link}
        gather.append(gather_item)

        gather_item = {"name-node": "InstPrivate", "title": "Private Account",
                       "subtitle": profile_data["is_private"],
                       "icon": "fas fa-user-shield",
                       "link": link}
        gather.append(gather_item)

        gather_item = {"name-node": "InstUsername", "title": "Username",
                       "subtitle": profile_data["Username"],
                       "icon": "fas fa-user",
                       "link": link}
        gather.append(gather_item)

        gather_item = {"name-node": "InstBuss", "title": "Bussiness Account",
                       "subtitle": profile_data["is_business_account"],
                       "icon": "fas fa-building",
                       "link": link}
        gather.append(gather_item)

        gather_item = {"name-node": "InstVerified",
                       "title": "Verified Account",
                       "subtitle": profile_data["is_verified"],
                       "icon": "fas fa-certificate",
                       "link": link}
        gather.append(gather_item)

        # Geo and Bar
        postlist = []
        postloc = []
        for post in posts:
            post_item = {"name": int(post), "series": [
                        {"name": "Comments",
                         "value": int(posts[post]['Number of Comments'])},
                        {"name": "Likes",
                         "value": int(posts[post]['Number of Likes'])}]}
            postlist.append(post_item)
            if (posts[post]['Location'] != 'None'):
                location = load_dirty_json(posts[post]['Location'])
                time_post = datetime.fromtimestamp(float(posts[post][
                    'Taken At Timestamp']))
                postloc.append({'Caption': posts[post]['Caption'],
                                'Accessability': posts[post][
                                    'Accessability Caption'],
                                'Latitude': posts[post]['Latitude'],
                                'Longitude': posts[post]['Longitude'],
                                'Name': location['name'],
                                'Time': time_post.strftime("%Y/%m/%d %H:%M:%S")
                                })

        total.append({'raw': raw_node})
        graphic.append({'instagram': gather})
        graphic.append({'postslist': postlist})
        graphic.append({'postsloc': postloc})
        total.append({'graphic': graphic})
        total.append({'profile': profile})
        total.append({'timeline': timeline})

    return total


def output(data):
    print(" ")
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    username = sys.argv[1]
    result = t_instagram(username)
    output(result)
