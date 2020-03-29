#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import sys
import json
import requests
from bs4 import BeautifulSoup
from datetime import date
import random


try:
    from factories._celery import create_celery
    from factories.application import create_application
    from celery.utils.log import get_task_logger
    celery = create_celery(create_application())
except ImportError:
    # This is to test the module individually, and I know that is piece of shit
    sys.path.append('../../')
    from factories._celery import create_celery
    from factories.application import create_application
    from celery.utils.log import get_task_logger
    celery = create_celery(create_application())


from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

logger = get_task_logger(__name__)


month = {
    'January': "01",
    'February': "02",
    'March': "03",
    'April': "04",
    'May': "05",
    'June': "06",
    'July': "07",
    'August': "08",
    'September': "09",
    'October': "10",
    'November': "11",
    'December': "12"
}

dayName = {
	'Monday':0,
	'Tuesday':1,
	'Wednesday':2,
	'Thursday':3,
	'Friday':4,
	'Saturday':5,
	'Sunday':6
}

user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
    'Mozilla/5.0 (Windows NT 5.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.90 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
    'Mozilla/4.0 (compatible; MSIE 9.0; Windows NT 6.1)',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0)',
    'Mozilla/5.0 (Windows NT 6.1; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (Windows NT 6.2; WOW64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.0; Trident/5.0)',
    'Mozilla/5.0 (Windows NT 6.3; WOW64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64; Trident/7.0; rv:11.0) like Gecko',
    'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0)',
    'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)',
    'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729)'
]


@celery.task
def t_venmo(username, from_m="Initial"):
    """Task of Celery that get info from venmo"""

    raw_node = []
    # Parsing user information
    user = []
    url = "https://venmo.com/%s" % username
    url_user = 'https://api.venmo.com/v1/users/{}'.format(username)
    response = requests.get(url_user, headers={'User-Agent': random.choice(user_agents)}, verify=False)
    data_user = response.json()
    print(" USER : ")
    print(data_user)

    if (data_user.get("error", "") != ""):
        raw_node = { 'status': 'Not found'}
    else:
        raw_node.append({'user': data_user["data"]})
        transaction = {"friends": [], "details": []}
        resp = requests.get(url, headers={'User-Agent': random.choice(user_agents)}, verify=False)
        html_doc = BeautifulSoup(resp.text, "html.parser")
        sm = html_doc.find_all('div', class_='paymentpage-payment-container')
        for html_doc in sm:

            data = {"friend": [], "details": {}}
            names = html_doc.find('div', 'paymentpage-subline').find_all('a', href=True)

            data["details"]["donor_username"] = names[0]["href"]
            data["details"]["donor_name"] = names[0].text
            data["details"]["recipient_username"] = names[1]["href"]
            data["details"]["recipient_name"] = names[1].text

            if username not in data["details"]["donor_username"]:
                data["friend"].append({"username": data["details"]["donor_username"],
                                       "name": data["details"]["donor_name"]})
            else:
                data["friend"].append({"username": data["details"]["recipient_username"],
                                       "name": data["details"]["recipient_name"]})

            data["details"]["text"] = html_doc.find('div', 'paymentpage-text').text
            date = html_doc.find('div', 'paymentpage-datetime').find('div', 'date').text.split()

            if date[1] not in dayName:
                data["details"]["date"] = date[3] + "-" + month[date[1]] + "-{:02d}".format(int(date[2].replace(",", "")))
            else:
                recordedWeekday = dayName[date[1]]
                now = datetime.datetime.today()
                nowWeekday = now.weekday()
                if recordedWeekday > nowWeekday:
                    diff = nowWeekday + (7-recordedWeekday)
                else:
                    diff = nowWeekday - recordedWeekday
                occurance = now - datetime.timedelta(days=diff)

                data["details"]["date"] = str(occurance.year) + "-{:02d}".format(occurance.month) + "-{:02d}".format(occurance.day)

            for f in data["friend"]:
                if f not in transaction["friends"]:
                    transaction["friends"].append(f)
            transaction["details"].append(data["details"])

        print(" TRANSACTIONS : ")
        print(transaction)

        raw_node.append({'transaction': transaction})

    # Total
    total = []
    total.append({'module': 'venmo'})
    total.append({'param': username})
    # Evaluates the module that executed the task and set validation
    if (from_m == 'Initial'):
        total.append({'validation': 'no'})
    else:
        total.append({'validation': 'soft'})

    # Graphic Array
    graphic = []

    # Profile Array
    profile = []

    # Timeline Array
    timeline = []

    # Gather Array
    gather = []

    friends = []
    transactions = []

    link = "Venmo"
    gather_item = {"name-node": "Venmo", "title": "Venmo",
                   "subtitle": "", "icon": "fab fa-vimeo-v",
                   "link": link}
    gather.append(gather_item)

    if ('status' not in raw_node):
        # Gather Array
        social = []

        link_friends = "Friends"
        friends_item = {"name-node": "Friends", "title": "Friends",
                        "subtitle": raw_node[0]["user"]["display_name"],
                        "icon": "fas fa-user-friends",
                        "link": link_friends}
        friends.append(friends_item)

        gather_item = {"name-node": "Venmoname", "title": "Name",
                       "subtitle": raw_node[0]["user"]["display_name"],
                       "icon": "fas fa-user",
                       "link": link}
        gather.append(gather_item)
        profile_item = {'name': raw_node[0]["user"]["display_name"]}
        profile.append(profile_item)

        gather_item = {"name-node": "Venmoactive", "title": "Active",
                       "subtitle": raw_node[0]["user"]["is_active"],
                       "icon": "fab fa-creative-commons-sampling",
                       "link": link}
        gather.append(gather_item)

        if (raw_node[0]["user"]["is_blocked"]):
            gather_item = {"name-node": "VenmoBlocked", "title": "Blocked?",
                        "subtitle": "The user is blocked",
                        "icon": "fab fa-lock",
                        "link": link}
        else:
            gather_item = {"name-node": "VenmoBlocked", "title": "Blocked?",
                        "subtitle": "The user is NOT blocked",
                        "icon": "fas fa-lock-open",
                        "link": link}
        gather.append(gather_item)

        gather_item = {"name-node": "VenmoJoin", "title": "Join Date",
                       "subtitle": raw_node[0]["user"]["date_joined"][:10],
                       "icon": "fas fa-calendar-check", "link": link}
        gather.append(gather_item)
        timeline.append({'action': 'Start : Venmo',
                         'date': raw_node[0]["user"]["date_joined"][:10],
                         'desc': "Join date for Venmo"})

        gather_item = {"name-node": "VenmoPic", "title": "Avatar",
                       "picture": raw_node[0]["user"]["profile_picture_url"],
                       "subtitle": "",
                       "link": link}
        gather.append(gather_item)
        profile_item = {'photos': [{"picture": raw_node[0]["user"]["profile_picture_url"],
                                    "title": "Venmo"}]}
        profile.append(profile_item)

        gather_item = {"name-node": "VenmoBio", "title": "Bio",
                       "subtitle": raw_node[0]["user"]["about"],
                       "icon": "fas fa-heartbeat",
                       "link": link}
        gather.append(gather_item)

        gather_item = {"name-node": "VenmoURL", "title": "URL",
                       "subtitle": url_user,
                       "icon": "fas fa-code",
                       "link": link}
        gather.append(gather_item)

        gather_item = {"name-node": "VenmoUsername", "title": "Username",
                       "subtitle": username,
                       "icon": "fas fa-user",
                       "link": link}
        gather.append(gather_item)

        gather_item = {"name-node": "VenmoPhone", "title": "Phone",
                       "subtitle": raw_node[0]["user"]["phone"],
                       "icon": "fas fa-mobile-alt",
                       "link": link}
        gather.append(gather_item)

        gather_item = {"name-node": "VenmoEmail", "title": "Email",
                       "subtitle": raw_node[0]["user"]["email"],
                       "icon": "fas fa-at",
                       "link": link}
        gather.append(gather_item)

        gather_item = {"name-node": "VenmoFriends", "title": "Friends",
                       "subtitle": raw_node[0]["user"]["friends_count"],
                       "icon": "fas fa-user-friends",
                       "link": link}
        gather.append(gather_item)

        try:
            transactions = raw_node[1]["transaction"]["details"]
        except:
            transactions = []

        for t in transactions:
            t["donor_username"] = t["donor_username"][1:]
            t["recipient_username"] = t["recipient_username"][1:]
            timeline.append({'action': 'Transaction : Venmo',
                             'date': t["date"],
                             'desc': "From: " + t["donor_name"] + " To: " +
                             t["recipient_name"] + " Text: " + t["text"]})

        try:
            friends_raw = raw_node[1]["transaction"]["friends"]
        except:
            friends_raw = []

        for f in friends_raw:
            friends_item = {"name-node": f["username"][1:],
                            "title": f["username"][1:],
                            "subtitle": f["name"],
                            "icon": "fas fa-user",
                            "link": link_friends}
            friends.append(friends_item)

        social_item = {"name": "Venmo",
                       "url": url,
                       "source": "Venmo",
                       "icon": "fab fa-vimeo-v",
                       "username": username}
        social.append(social_item)
        profile.append({"social": social})
        profile_item = {"username": username}
        profile.append(profile_item)

    print (raw_node)
    graphic.append({'user': gather})
    graphic.append({'friends': friends})
    graphic.append({'trans': transactions})
    total.append({'raw': raw_node})
    total.append({'graphic': graphic})
    total.append({'profile': profile})
    total.append({'timeline': timeline})

    return total


def output(data):
    print(" ")
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    username = sys.argv[1]
    result = t_venmo(username)
    output(result)
