#!/usr/bin/env python
# -*- encoding: utf-8 -*-

import os
import sys
import json
import requests
import re
import traceback
import time

import redis
from langdetect import detect
# from googletrans import Translator
import TranslatorX
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from datetime import datetime

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


def p_tweetiment_twint(tweets, task_id, username):
    """ Task of Celery that get info from twitter sentiment """

    # Code to develop the frontend without burning APIs
    cd = os.getcwd()
    td = os.path.join(cd, "outputs")
    output = "output-tweetiment.json"
    file_path = os.path.join(td, output)

    if os.path.exists(file_path):
        logger.info(f"Developer frontend mode - {file_path}")
        try:
            with open(file_path, 'r') as file:
                data = json.load(file)
            return data
        except json.JSONDecodeError:
            logger.error(f"Developer mode ERROR")

    # Code
    raw = []
    neg = []
    pos = []
    neu = []
    compound = []

    analyzer = SentimentIntensityAnalyzer()
    # translator = Translator()
    translator = TranslatorX.Translator()

    c = 0
    for tweet in tweets:
        create_date = c
        c = c + 1
        # Remove mentions
        text = re.sub(r'@\w+\s+', "", tweet)
        # Remove URLs
        text = re.sub(r'https?:\/\/.*[\r\n]*', '', text, flags=re.MULTILINE)
        # Remove emojis
        RE_EMOJI = re.compile('[\U00010000-\U0010ffff]', flags=re.UNICODE)
        text = RE_EMOJI.sub(r'', text)
        text = text.replace("\n", " ")
        if (len(text) > 3):
            try:
                lang_detect = detect(text)
            except Exception:
                lang_detect = 'en'
            if (lang_detect != 'en'):
                try:
                    # trans = translator.translate(text, dest='en')
                    trans = translator.Translate(text, to_lang='en')
                    translated = trans.text
                except Exception:
                    translated = text

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


def p_tweetiment_twitter(tweets, task_id, username):

    raw = []
    neg = []
    pos = []
    neu = []
    compound = []

    analyzer = SentimentIntensityAnalyzer()
    # translator = Translator()
    translator = TranslatorX.Translator()

    c = 0
    for tweet in tweets:
        if (tweet['text'][:3] != 'RT '):
            c = c + 1
            # Get date
            create_date = tweet['created_at']
            # date_format = datetime.strptime(create_date,
            #                                 "%a %b %d %H:%M:%S +0000 %Y")
            # create_date = date_format.strftime("%Y-%m-%dT%H:%M:%S.000Z")

            # Remove mentions
            text = re.sub(r'@\w+\s+', "", tweet['text'])
            # Remove URLs
            text = re.sub(r'https?:\/\/.*[\r\n]*', '', text,
                          flags=re.MULTILINE)
            # Remove emojis
            RE_EMOJI = re.compile('[\U00010000-\U0010ffff]', flags=re.UNICODE)
            text = RE_EMOJI.sub(r'', text)
            text = text.replace("\n", " ")
            if (len(text) > 3):
                translated = text
                try:
                    lang_detect = detect(text)
                except Exception:
                    lang_detect = 'en'
                if (lang_detect != 'en'):
                    try:
                        # trans = translator.translate(text, dest='en')
                        trans = translator.Translate(text, to_lang='en')
                        translated = trans.text
                    except Exception:
                        # translator = TLT(from_lang=lang_detect, to_lang="en")
                        # translated = translator.translate(text)
                        translated = text

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


@celery.task
def t_tweetiment(username, task_id, from_m="Initial"):
    total = []
    tweets = []
    tic = time.perf_counter()
    try:
        task_id_complete = "celery-task-meta-" + task_id
        print("TaskID : " + task_id_complete)

        redis_db = redis.Redis(host='localhost', port=6379, db=0)
        value = redis_db.get(task_id_complete)

        # Evaluate Twint or Twitter
        json_value = json.loads(value)
        module = json_value['result'][0]['module']
        print("Module : " + module)
        if (module == 'twint'):
            print("Tweetiment : Twint")
            tweets_json = json_value['result'][3]['raw'][1]['raw_node_tweets']
            tweets_json = json.loads(tweets_json)['tweet']
            for tweet in tweets_json:
                tweets.append(tweets_json[tweet])
            total = p_tweetiment_twint(tweets, task_id, username)
        else:
            print("Tweetiment : Twitter")
            tweets = json_value['result'][3]['raw'][1]['raw_node_tweets']
            total = p_tweetiment_twitter(tweets, task_id, username)
    except Exception as e:
        # Check internal error
        if str(e).startswith("iKy - "):
            reason = str(e)[len("iKy - "):]
            status = "Warning"
        else:
            reason = str(e)
            status = "Fail"

        traceback.print_exc()
        traceback_text = traceback.format_exc()
        total.append({'module': 'tweetiment'})
        total.append({'param': username})
        total.append({'validation': 'not_used'})

        raw_node = []
        raw_node.append({"status": status,
                         # "reason": "{}".format(e),
                         "reason": reason,
                         "traceback": traceback_text})
        total.append({"raw": raw_node})

    # Take final time
    toc = time.perf_counter()
    # Show process time
    logger.info(f"PeopleDataLabs - Response in {toc - tic:0.4f} seconds")

    return total


def output(data):
    print(json.dumps(data, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    username = sys.argv[1]
    task_id = sys.argv[2]
    result = t_tweetiment(username, task_id)
    output(result)
