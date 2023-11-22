#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import requests
import re
import os
import json
import fontawesome as fa

# from requests.packages.urllib3.exceptions import InsecureRequestWarning
# requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def fontawesome_cheat_5():
    """ Get icon name for fontawesome 5. This function is for compatibility """
    fonta = {}
    return fonta


def search_icon_5(name, font_list):
    if (name.lower() in fa.icons.keys()):
        return 'fab fa-' + name.lower()
    else:
        return None


if __name__ == "__main__":
    font_list = fontawesome_cheat_5()
    print(font_list)
    print(search_icon_5("Facebook", font_list))
