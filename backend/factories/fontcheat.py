#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import requests
import re
import os
import json

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def fontawesome_cheat_5():
    """ Get icon name for fontawesome 5 """
    cur_dir = os.getcwd()
    fonta_file = cur_dir + '/fonta.json'
    fonta = {}

    if (not os.path.exists(fonta_file) and not
            os.path.isfile(fonta_file)):

        req = requests.get("https://origin.fontawesome.com/cheatsheet")

        m = re.findall('window.__inline_data__ = (.*)', req.text)
        json_m = json.loads(m[0])
        json_data = json_m[0]['data']

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


def search_icon_5(name, font_list):
    if (name.lower() in font_list):
        return font_list[name.lower()]
    else:
        return None


if __name__ == "__main__":
    font_list = fontawesome_cheat_5()
    print(font_list)
    print(search_icon_5("Facebook", font_list))
