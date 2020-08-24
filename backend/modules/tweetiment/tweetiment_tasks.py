#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import sys
import json
import requests
# import urllib3
import re

import tweepy
# import oauth2
import redis
from langdetect import detect
from googletrans import Translator
import time
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from datetime import datetime

try:
    from factories._celery import create_celery
    from factories.application import create_application
    from factories.configuration import api_keys_search
    from celery.utils.log import get_task_logger
    celery = create_celery(create_application())
except ImportError:
    # This is to test the module individually, and I know that is piece of shit
    sys.path.append('../../')
    from factories._celery import create_celery
    from factories.application import create_application
    from factories.configuration import api_keys_search
    from celery.utils.log import get_task_logger
    celery = create_celery(create_application())

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

logger = get_task_logger(__name__)


@celery.task
def t_tweetiment(username, task_id, from_m="Initial"):

    raw = []
    neg = []
    pos = []
    neu = []
    compound = []
    task_id_complete = "celery-task-meta-" + task_id

    print("TaskID : " + task_id_complete)

    redis_db = redis.Redis(host='localhost', port=6379, db=0)
    value = redis_db.get(task_id_complete)
    print(value)
    try:
        json_value = json.loads(value)
        tweets = json_value['result'][3]['raw'][1]['raw_node_tweets']
    except:
        tweets = []

    analyzer = SentimentIntensityAnalyzer()
    translator = Translator()

    c = 0
    for tweet in tweets:
        if (tweet['full_text'][:3] != 'RT '):
            c = c + 1
            # Get date
            create_date = tweet['created_at']
            date_format = datetime.strptime(create_date, "%a %b %d %H:%M:%S +0000 %Y")
            create_date = date_format.strftime("%Y-%m-%dT%H:%M:%S.000Z")
            # Remove mentions
            text = re.sub(r'@\w+\s+', "", tweet['full_text'])
            # Remove URLs
            text = re.sub(r'https?:\/\/.*[\r\n]*', '', text, flags=re.MULTILINE)
            # Remove emojis
            RE_EMOJI = re.compile('[\U00010000-\U0010ffff]', flags=re.UNICODE)
            text = RE_EMOJI.sub(r'', text)
            if (len(text) > 3):
                translated = text
                try:
                    lang_detect = detect(text)
                except:
                    lang_detect = 'en'
                if (lang_detect != 'en'):
                    trans = translator.translate(text)
                    translated = trans.text
                    # sentences.append(trans.text)
                vs = analyzer.polarity_scores(translated)

                raw.append({"text": translated, "date": create_date,
                            "sentiment": vs})
                neg.append({"name": create_date, "value": vs["neg"]})
                pos.append({"name": create_date, "value": vs["pos"]})
                neu.append({"name": create_date, "value": vs["neu"]})
                compound.append({"name": create_date, "value": vs["compound"]})

    # Total
    total = []
    total.append({'module': 'tweetiment'})
    total.append({'param': username})
    # Evaluates the module that executed the task and set validation
    total.append({'validation': 'no'})

    # Graphic Array
    graphic = []
    sentiment = []

    # Profile Array
    profile = []

    # Timeline Array
    timeline = []

    if (raw == []):
        raw.append({"status": "Not found"})

    sentiment.append({"name": "compound", "series": compound})
    sentiment.append({"name": "pos", "series": pos})
    sentiment.append({"name": "neu", "series": neu})
    sentiment.append({"name": "neg", "series": neg})
    total.append({'raw': raw})
    graphic.append({'sentiment': sentiment})
    total.append({'graphic': graphic})
    total.append({'profile': profile})
    total.append({'timeline': timeline})

    return total


def output(data):
    print(json.dumps(data, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    username = sys.argv[1]
    task_id = sys.argv[2]
    result = t_tweetiment(username, task_id)
    output(result)
