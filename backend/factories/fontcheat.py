#!/usr/bin/env python

import fontawesome as fa

# import urllib3
# urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def fontawesome_cheat_5():
    """Get icon name for fontawesome 5. This function is for compatibility"""
    fonta = {}
    return fonta


def search_icon_5(name, font_list):
    if name.lower() in fa.icons:
        return "fab fa-" + name.lower()
    else:
        return None


if __name__ == "__main__":
    font_list = fontawesome_cheat_5()
    print(font_list)
    print(search_icon_5("Facebook", font_list))
