#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import requests
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
        # print(icon)
        if (len(icon) == 7):
            fonta[icon[3].strip()] = [icon[2].strip(), icon[5].strip(),
                                      icon[1].strip(), icon[4].strip()]
        elif (len(icon) == 6):
            fonta[icon[2].strip()] = [icon[1].strip(), icon[4].strip(),
                                      icon[0].strip(), icon[3].strip()]
    return fonta


def search_icon(name, font_list):
    uni_icon = None
    for key in font_list:
        if (key.find(name.lower()) != -1):
            if (uni_icon is None) or (ord(uni_icon) > ord(font_list[key][0])):
                uni_icon = font_list[key][0]
    return uni_icon

# font_list =  fontawesome_cheat()
# icon = search_icon('angellist', font_list)
# print "Icon ", icon
