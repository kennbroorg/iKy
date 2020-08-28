#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import re
from geopy.geocoders import Nominatim


def location_geo(location, time=''):
    geolocator = Nominatim(user_agent="iKy")
    try:
        latlong = geolocator.geocode(location)
    except:
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


def extract_url(text):
    urls = []
    regex = r"((http(s)?(\:\/\/))+(www\.)?([\w\-\.\/])*(\.[a-zA-Z]{2,3}\/?))[^\s\b\n|]*[^.,;:\?\!\@\^\$ -]"
    matches = re.finditer(regex, text, re.MULTILINE)
    for matchNum, match in enumerate(matches, start=1):
        urls.append({"url": match.group()})
    return urls


def extract_url_linkedin(text):
    tasks = []
    regex = r"((http(s)?(\:\/\/))+(www\.)?(linkedin)*(\.[a-zA-Z]{2,3}\/?))[^\s\b\n|]*[^.,;:\?\!\@\^\$ -]"
    matches = re.finditer(regex, text, re.MULTILINE)
    for matchNum, match in enumerate(matches, start=1):
        tasks.append({"module": "linkedin",
                      "param": match.group()})
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

    urls = extract_url(text)
    analized['url'] = urls
    tasks_temp = []
    tasks_temp.append(extract_url_linkedin(text))
    tasks_temp.append(extract_url_instagram(text))
    tasks_temp.append(extract_url_twitter(text))
    tasks_temp.append(extract_url_tiktok(text))
    tasks_temp.append(extract_twitter(text))
    tasks_temp.append(extract_tiktok(text))
    tasks_temp.append(extract_instagram(text))
    tasks_temp.append(extract_linkedin(text))

    tasks = [val for sublist in tasks_temp for val in sublist]

    analized['tasks'] = tasks

    return analized
