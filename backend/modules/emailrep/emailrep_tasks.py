#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import sys
import json
import requests
from datetime import date, datetime

try:
    from factories._celery import create_celery
    from factories.application import create_application
    from factories.fontcheat import fontawesome_cheat_5, search_icon_5
    from celery.utils.log import get_task_logger
    celery = create_celery(create_application())
except ImportError:
    # This is to test the module individually, and I know that is piece of shit
    sys.path.append('../../')
    from factories._celery import create_celery
    from factories.application import create_application
    from factories.fontcheat import fontawesome_cheat_5, search_icon_5
    from celery.utils.log import get_task_logger
    celery = create_celery(create_application())

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

logger = get_task_logger(__name__)

# Compatibility code
try:
    # Python 2: "unicode" is built-in
    unicode
except NameError:
    unicode = str

@celery.task
def t_emailrep(username, from_m="Initial"):
    """ Task of Celery that get info from github """
    req = requests.get("https://emailrep.io/%s" % username)

    # Icons unicode
    font_list = fontawesome_cheat_5()
    # Raw Array
    raw_node = json.loads(unicode(req.text))

    # Total
    total = []
    total.append({'module': 'emailrep'})
    total.append({'param': username})
    # Evaluates the module that executed the task and set validation
    total.append({'validation': 'hard'})

    # Graphic Array
    graphic = []

    # Social Array
    socialp = []

    # Profile Array
    profile = []

    # Timeline Array
    timeline = []

    # Gather Array
    gather = []

    link = "EmailRep"
    gather_item = {"name-node": "EmailRep", "title": "EmailRep",
                   "subtitle": "", "icon": "fas fa-file-alt", "link": link}
    gather.append(gather_item)

    if ('reputation' in raw_node):
        if (raw_node['reputation'] == "high"):
            icon_rep = "fas fa-smile"
        elif (raw_node['reputation'] == "medium"):
            icon_rep = "fas fa-meh"
        elif (raw_node['reputation'] == "low"):
            icon_rep = "fas fa-sad-tear"
        else:
            icon_rep = "fas fa-poo"
        gather_item = {"name-node": "Reputation", "title": "Reputation",
                       "subtitle": raw_node['reputation'],
                       "icon": icon_rep,
                       "link": link}
        gather.append(gather_item)

    if ('suspicious' in raw_node):
        if (not raw_node['suspicious']):
            icon_rep = "fas fa-thumbs-up"
        else:
            icon_rep = "fas fa-thumbs-down"
        gather_item = {"name-node": "suspicious", "title": "Suspicious",
                       "subtitle": raw_node['suspicious'],
                       "icon": icon_rep,
                       "help": "Our best assessment based off all the information we have",
                       "link": link}
        gather.append(gather_item)

    if ('references' in raw_node):
        gather_item = {"name-node": "References", "title": "References",
                       "subtitle": raw_node['references'],
                       "icon": "fas fa-award",
                       "help": "total number of positive and negative sources of reputation. note that these may not all be direct references to the email address, but can include reputation sources for the domain or other related information",
                       "link": link}
        gather.append(gather_item)

    if ('details' in raw_node):
        if (not 'blacklisted' in raw_node['details']):
            if (raw_node['details']['blacklisted']):
                icon_rep = "fas fa-thumbs-up"
            else:
                icon_rep = "fas fa-thumbs-down"
            gather_item = {"name-node": "Blacklisted", "title": "Blacklisted",
                           "subtitle": raw_node['details']['blacklisted'],
                           "icon": icon_rep,
                           "help": "The email is believed to be malicious or spammy",
                           "link": link}
            gather.append(gather_item)
        if ('malicious_activity' in raw_node['details']):
            if (not raw_node['details']['malicious_activity']):
                icon_rep = "fas fa-thumbs-up"
            else:
                icon_rep = "fas fa-thumbs-down"
            gather_item = {"name-node": "Malicious_Activity",
                           "title": "Malicious Activity",
                           "subtitle": raw_node['details']['malicious_activity'],
                           "icon": icon_rep,
                           "help": "The email has exhibited malicious behavior (e.g. phishing or fraud)",
                           "link": link}
            gather.append(gather_item)
        if ('credentials_leaked' in raw_node['details']):
            if (not raw_node['details']['credentials_leaked']):
                icon_rep = "fas fa-thumbs-up"
            else:
                icon_rep = "fas fa-thumbs-down"
            gather_item = {"name-node": "credentials_leaked",
                           "title": "Credentials Leaked",
                           "subtitle": raw_node['details']['credentials_leaked'],
                           "icon": icon_rep,
                           "help": "Credentials were leaked at some point in time (e.g. a data breach, pastebin, dark web, etc.)",
                           "link": link}
            gather.append(gather_item)
        if ('data_breach' in raw_node['details']):
            if (not raw_node['details']['data_breach']):
                icon_rep = "fas fa-thumbs-up"
            else:
                icon_rep = "fas fa-thumbs-down"
            gather_item = {"name-node": "data_breach",
                           "title": "Data Breach",
                           "subtitle": raw_node['details']['data_breach'],
                           "icon": icon_rep,
                           "help": "The email was in a data breach at some point in time",
                           "link": link}
            gather.append(gather_item)
        if ('free_provider' in raw_node['details']):
            if (raw_node['details']['free_provider']):
                icon_rep = "fas fa-check-circle"
            else:
                icon_rep = "fas fa-times-circle"
            gather_item = {"name-node": "free_provider",
                           "title": "Free Provider",
                           "subtitle": raw_node['details']['free_provider'],
                           "icon": icon_rep,
                           "help": "The email uses a free email provider",
                           "link": link}
            gather.append(gather_item)
        if ('domain_reputation' in raw_node['details']) and not (raw_node['details']['free_provider']):
            if (raw_node['details']['free_provider'] == "high"):
                icon_rep = "fas fa-smile"
            elif (raw_node['details']['free_provider'] == "medium"):
                icon_rep = "fas fa-meh"
            elif (raw_node['details']['free_provider'] == "low"):
                icon_rep = "fas fa-sad-tear"
            else:
                icon_rep = "fas fa-poo"
            gather_item = {"name-node": "domain_reputation",
                           "title": "Domain Reputation",
                           "subtitle": raw_node['details']['domain_reputation'],
                           "icon": icon_rep,
                           "help": "high/medium/low/n/a (n/a if the domain is disposable, or doesn't exist)",
                           "link": link}
            gather.append(gather_item)
        if ('spam' in raw_node['details']):
            if (not raw_node['details']['spam']):
                icon_rep = "fas fa-thumbs-up"
            else:
                icon_rep = "fas fa-thumbs-down"
            gather_item = {"name-node": "spam",
                           "title": "Spam",
                           "subtitle": raw_node['details']['spam'],
                           "icon": icon_rep,
                           "help": "The email has exhibited spammy behavior (e.g. spam traps, login form abuse)",
                           "link": link}
            gather.append(gather_item)
        if ('disposable' in raw_node['details']):
            if (not raw_node['details']['disposable']):
                icon_rep = "fas fa-thumbs-up"
            else:
                icon_rep = "fas fa-thumbs-down"
            gather_item = {"name-node": "disposable",
                           "title": "Disposable or Temporary",
                           "subtitle": raw_node['details']['disposable'],
                           "icon": icon_rep,
                           "help": "the email uses a temporary/disposable service",
                           "link": link}
            gather.append(gather_item)
        if ('valid_mx' in raw_node['details']):
            if (raw_node['details']['valid_mx']):
                icon_rep = "fas fa-thumbs-up"
            else:
                icon_rep = "fas fa-thumbs-down"
            gather_item = {"name-node": "valid_mx",
                           "title": "Valid MX",
                           "subtitle": raw_node['details']['valid_mx'],
                           "icon": icon_rep,
                           "help": "Has an MX record",
                           "link": link}
            gather.append(gather_item)
        if ('spoofable' in raw_node['details']):
            if (not raw_node['details']['spoofable']):
                icon_rep = "fas fa-thumbs-up"
            else:
                icon_rep = "fas fa-thumbs-down"
            gather_item = {"name-node": "spoofable",
                           "title": "Spoofable",
                           "subtitle": raw_node['details']['spoofable'],
                           "icon": icon_rep,
                           "help": "Email address can be spoofed (e.g. not a strict SPF policy or DMARC is not enforced)",
                           "link": link}
            gather.append(gather_item)
        if ('suspicious_tld' in raw_node['details']):
            if (not raw_node['details']['suspicious_tld']):
                icon_rep = "fas fa-thumbs-up"
            else:
                icon_rep = "fas fa-thumbs-down"
            gather_item = {"name-node": "suspicious_tld",
                           "title": "Suspicious TLD",
                           "subtitle": raw_node['details']['suspicious_tld'],
                           "icon": icon_rep,
                           "link": link}
            gather.append(gather_item)

        if ('profiles' in raw_node['details']) and (len(raw_node['details']['profiles']) > 0):
            link_social = "Social"
            social_item = {"name-node": "Social", "title": "Social",
                           "subtitle": "", "icon": search_icon_5(
                               "child", font_list),
                           "link": link_social}
            socialp.append(social_item)

            for social in raw_node['details']['profiles']:
                fa_icon = search_icon_5(social, font_list)
                if (fa_icon is None):
                    fa_icon = search_icon_5("question", font_list)

                social_item = {"name-node": "ER" + social,
                               "title": social.capitalize(),
                               "icon": fa_icon,
                               "link": link_social}
                socialp.append(social_item)

    total.append({'raw': raw_node})
    graphic.append({'details': gather})
    if (socialp != []):
        graphic.append({'social': socialp})
    total.append({'graphic': graphic})
    total.append({'profile': profile})
    total.append({'timeline': timeline})

    return total


def output(data):
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    username = sys.argv[1]
    result = t_emailrep(username)
    output(result)
