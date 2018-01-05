#!/usr/bin/env python

import sys
import requests
import json
from bs4 import BeautifulSoup

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def main(username):
    data = {"username": username}
    req = requests.post('https://usersearch.org/results_normal.php', data=data, verify=False)
    soup = BeautifulSoup(req.content, "lxml")
    atag = soup.findAll('a', {'class': 'pretty-button results-button'})
    profiles = []
    for at in atag:
        if at.text == "View Profile":
            profiles.append(at['href'])
    return profiles


def output(data):
    print json.dumps(data, indent=4, separators=(',', ': '))


if __name__ == "__main__":
    try:
        username = sys.argv[1]
        result = main(username)
        output(result)
    except Exception as e:
        print e
        print "Please provide a username as argument"
