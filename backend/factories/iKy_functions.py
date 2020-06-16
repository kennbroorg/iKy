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


def analize_rrss(text):
    analized = {}

    urls = extract_url(text)
    analized['url'] = urls
    tasks = extract_url_linkedin(text)
    analized['tasks'] = tasks

    return analized
