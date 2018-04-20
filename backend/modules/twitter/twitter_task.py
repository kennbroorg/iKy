#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import sys
import json
import requests
import urllib3

import tweepy
import oauth2

try : 
    from factories._celery import create_celery
    from factories.application import create_application
    from factories.configuration import api_keys_search
    from factories.fontcheat import fontawesome_cheat, search_icon
    from celery.utils.log import get_task_logger
    celery = create_celery(create_application())
except ImportError:
    # This is to test the module individually, and I know that is piece of shit
    sys.path.append('../../')
    from factories._celery import create_celery
    from factories.application import create_application
    from factories.configuration import api_keys_search
    from factories.fontcheat import fontawesome_cheat, search_icon
    from celery.utils.log import get_task_logger
    celery = create_celery(create_application())

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

logger = get_task_logger(__name__)


@celery.task
def t_twitter(username):

    twitter_consumer_key = api_keys_search('twitter_consumer_key')
    twitter_consumer_secret = api_keys_search('twitter_consumer_secret')
    twitter_access_token = api_keys_search('twitter_access_token')
    twitter_access_token_secret = api_keys_search('twitter_access_token_secret')

    auth = tweepy.OAuthHandler(twitter_consumer_key, twitter_consumer_secret)
    # auth.set_access_token(twitter_access_token, twitter_access_token_secret)

    api = tweepy.API(auth)
    # consumer = oauth2.Consumer(key=twitter_consumer_key, secret=twitter_consumer_secret)
    # access_token = oauth2.Token(key=twitter_access_token, secret=twitter_access_token_secret)
    # client = oauth2.Client(consumer, access_token)

    # Total
    total = []
    total.append({'module': 'twitter'})
    total.append({'param': username})

    try:
        result_api = api.get_user(username)
    except tweepy.TweepError as e:
        total.append({'raw_node': e[0]})
        return total

    raw_node = result_api._json

    print result_api.created_at
    print type(result_api.created_at)

    # Graphic Array
    graphic = []
    popularity = []

    # Profile Array
    profile = []

    # Timeline Array
    timeline = []

    # Twitter : TODO : Get hashtags as footprinting
    # footprint Array
    # footprint = []

    # Bios Array
    bios = []

    if (raw_node.get("contactInfo", "") != ""):
        profile_item = {'name': raw_node.get("contactInfo", "").get('fullName', '')}
        profile.append(profile_item)
        profile_item = {'firstName': raw_node.get("contactInfo", "").get('givenName', '')}
        profile.append(profile_item)
        profile_item = {'lastName': raw_node.get("contactInfo", "").get('familyName', '')}
        profile.append(profile_item)

        for web in raw_node.get("contactInfo", "").get("websites", ""):
            webs.append({'url': web.get("url", "")})

        # Fullcontact : TODO : Find examples 
        # if (raw_node.get("contactInfo", "").get('chats', '') != ""):

    company = []
    for org in raw_node.get("organizations", ""):
        company_item = {'name': org.get("name",""), 
            'title': org.get("title",""),
            'start': org.get("startDate", ""),
            'end': org.get("endDate","")}
        company.append(company_item)
        if (org.get("startDate", "") != ""):
            timeline.append({'action': 'Start : ' + org.get("name",""), 
                'date': org.get("startDate", "").replace("-", "/"), 
                'icon': 'fa-building',  
                'desc': org.get("title","")}) 
        if (org.get("endDate", "") != ""):
            timeline.append({'action': 'End : ' + org.get("name",""), 
                'date': org.get("endDate", "").replace("-", "/"), 
                'icon': 'fa-ban',  
                'desc': org.get("title","")}) 

    if (company != []):
        profile_item = {'organization': company}
        profile.append(profile_item)

    if (raw_node.get("digitalFootprint", "") != ""):
        for topics in  raw_node.get("digitalFootprint").get("topics", ""):
            footprint.append({'label': topics.get("value")})


    for social in raw_node.get("socialProfiles", ""):
        if ((social.get("username", "") != "") and
            (social.get("id", "") != "")):
            subtitle = social.get("username", "") + \
                " - " + social.get("id", "")
        elif (social.get("username", "") != ""):
            subtitle = social.get("username", "") 
        elif (social.get("id", "") != ""):
            subtitle = social.get("id", "") 
        else:
            subtitle = "Not identified"

        fa_icon = search_icon(social.get("typeId", ""), font_list)
        if (fa_icon == None):
            fa_icon = search_icon("question", font_list)

        social_item = {"name-node": social.get("typeName", ""), 
                "title": social.get("typeName", ""), 
                "subtitle": subtitle, 
                "icon": fa_icon, 
                "link": link_social}
        socialp.append(social_item)
        social_profile_item = {
                "name": social.get("type"), 
                "username": social.get("username"),
                "url": social.get("url")}
        social_profile.append(social_profile_item)

        if (social.get("bio", "") != ""):
            bios.append(social.get("bio", ""))

        # Fullcontact : TODO : Send all to tasks array 
        # Prepare other tasks 
        if (social.get("typeId", "") == "github"):
            tasks.append({"module": "github", \
                "param": social.get("username", "")})
        if (social.get("typeId", "") == "keybase"):
            tasks.append({"module": "keybase", \
                "param": social.get("username", "")})

    if (raw_node.get("demographics", "") != ""):
        if (raw_node.get("demographics", "") \
            .get("locationDeduced", "") != ""):
            if (raw_node.get("demographics", "") \
                .get("locationDeduced", "") \
                .get("deducedLocation", "") != ""):
                profile_item = {'location': raw_node.get("demographics", "").get("locationDeduced", "").get("deducedLocation", "")}
                profile.append(profile_item)
        elif (raw_node.get("demographics", "").get("locationGeneral", "") != ""):
            profile_item = {'location': raw_node.get("demographics", "").get("locationGeneral", "")}
            profile.append(profile_item)

        if (raw_node.get("demographics", "").get("gender", "") != ""):
            profile_item = {'gender': raw_node.get("demographics", "").get("gender", "")}
            profile.append(profile_item)

    for photos in raw_node.get("photos", ""):
        photo_item = {"name-node": photos.get("typeName", ""), 
                "title": photos.get("typeName", ""), 
                "subtitle": "", 
                "picture": photos.get("url", ""), 
                "link": link_photo}
        photo.append(photo_item)
        photo_profile.append(photo_item)
    if (photo_profile != []):
        profile_item = {'photos': photo_profile}
        profile.append(profile_item)

    total.append({'raw': raw_node})
    graphic.append({'social': socialp})
    graphic.append({'photo': photo})
    graphic.append({'webs': webs})
    graphic.append({'bios': bios})
    graphic.append({'footprint': footprint})
    profile.append({'social': social_profile})
    total.append({'graphic': graphic})
    if (profile != []):
        total.append({'profile': profile})
    if (timeline != []):
        total.append({'timeline': timeline})
    if (tasks != []):
        total.append({'tasks': tasks})

    return total


def output(data):
    print json.dumps(data, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    username = sys.argv[1]
    result = t_twitter(username)
    output(result)
