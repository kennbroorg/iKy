#!/usr/bin/env python

import sys
import requests
import json

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def main(username):
    # Use the username variable to do some stuff and return the data
    url = "https://keybase.io/_/api/1.0/user/lookup.json?usernames=%s" %username
    req = requests.get(url)
    data = json.loads(req.text) 
    if data['them'][0] is not None:
        dict_them = data['them'][0]
        return dict_them
    else:
        dict_them = []
        return dict_them


def output(data):
    print json.dumps(data, indent=4, separators=(',', ': '))


if __name__ == "__main__":
    username = sys.argv[1]
    result = main(username)
    output(result)

