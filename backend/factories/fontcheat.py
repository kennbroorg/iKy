#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import requests
import re
import os
import json
from bs4 import BeautifulSoup

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def fontawesome_cheat():
    """ Get unicode for fontawesome """
    # Problem page
    length = 0
    while (length < 22000):
        req = requests.get("https://fontawesome.com/v4.7.0/cheatsheet/")
        length = len(req.content)
    soup = BeautifulSoup(req.content, 'lxml')

    fonta = {}
    for icons in soup.findAll("div", {"class": "col-print-4"}):
        icon = icons.text.split('\n')
        if (len(icon) == 7):
            fonta[icon[3].strip()] = [icon[2].strip(), icon[5].strip(),
                                      icon[1].strip(), icon[4].strip()]
        elif (len(icon) == 6):
            fonta[icon[2].strip()] = [icon[1].strip(), icon[4].strip(),
                                      icon[0].strip(), icon[3].strip()]
    return fonta


def fontawesome_cheat_5():
    """ Get icon name for fontawesome 5 """
    # import pdb; pdb.set_trace()

    cur_dir = os.getcwd()
    fonta_file = cur_dir + '/fonta.json'
    print(fonta_file)
    fonta = {}

    if (not os.path.exists(fonta_file) and not
            os.path.isfile(fonta_file)):

        req = requests.get("https://origin.fontawesome.com/cheatsheet")

        m = re.findall('window.__inline_data__ = (.*)', req.text)
        json_m = json.loads(m[0])
        json_data = json_m[2]['data']
        print(json_data)

        with open(fonta_file, 'w') as f:
            # json_data = json.load(f)
            json.dump(json_data, f)
            # f.write(json_data)

    with open(fonta_file, 'r') as f:
        json_data = json.load(f)

    for icons in json_data:
        free = icons['attributes']['membership']['free']
        if (len(free)):
            letter_free = free[0][0]
            fonta[icons['id']] = "fa" + letter_free + " fa-" + icons['id']

    return fonta


def search_icon(name, font_list):
    uni_icon = None
    for key in font_list:
        if (key.find(name.lower()) != -1):
            if (uni_icon is None) or (ord(uni_icon) > ord(font_list[key][0])):
                uni_icon = font_list[key][0]
    return uni_icon


def search_icon_5(name, font_list):
    if (name in font_list):
        return font_list[name]
    else:
        return None


if __name__ == "__main__":
    font_list = fontawesome_cheat_5()
    print(font_list)
    print(search_icon_5("facebook", font_list))
