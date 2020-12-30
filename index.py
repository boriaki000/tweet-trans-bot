import sys
sys.path.append('lib')

import json
import os
import requests
import logging
from pytz import timezone, utc
from datetime import datetime, timedelta
from time import sleep
import tweepy
from googletrans import Translator

# Prepare key and token for tweepy.
consumer_key = os.environ['CONSUMER_KEY']
consumer_secret = os.environ['CONSUMER_SECRET']
access_token = os.environ['ACCESS_TOKEN']
access_token_secret = os.environ['ACCESS_TOKEN_SECRET']
# Create tweepy object
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)
# Translator
translator = Translator()
# Other
discord_webhook = os.environ['DICORD_WEBHOOK']
logger = logging.getLogger()
logger.setLevel(logging.INFO)
retry_count = 3


def handler(event, context):
    target_id = event['target_id']
    time_distance = int(event['time_distance'])
    if event.get('basetime'):
        basetime = datetime.strptime(event['basetime'], '%Y-%m-%d %H:%M:%S')
    else:
        basetime = datetime.now()

    if event.get('timezone'):
        timezone_str = event['timezone']
    else:
        timezone_str = utc.zone
    pytz_timezone = timezone(timezone_str)


    print('--- PARAM ---')
    print('target_id:' + str(target_id))
    print('basetime:' + str(basetime))
    print('time_distance:' + str(time_distance))
    print('timezone:' + timezone_str)

    result = get_tweet(target_id, basetime, time_distance, pytz_timezone)

    if event.get('testmode'):
        show_test_result(result)
    else:
        post_to_discord(result)

def get_tweet(user_id, basetime, time_distance, pytz_timezone):
    logger.info('START:Get Tweet')
    text_prefix = '```'
    for i in range(0, retry_count):
        try:
            tweets = api.user_timeline(user_id, tweet_mode='extended')
            result = []
            for tweet in tweets:
                distance = basetime - tweet.created_at
                if distance.days == 0 and distance.seconds < time_distance:
                    translated = translator.translate('tranlated:' + tweet.full_text, src='en', dest='ja')
                    result.append({'user_name':tweet.user.name
                                ,'created_at':str(pytz_timezone.localize(tweet.created_at))
                                ,'text':text_prefix + translated.text + text_prefix
                                ,'url':'https://twitter.com/' + user_id + '/status/' + str(tweet.id)})
        except Exception as e:
            sys.stderr.write('Error occurs in get_tweet\n')
            sys.stderr.write(str(e) + '\n')
            sleep(i * 5)
        else:
            logger.info('END  :Get Tweet')
            return {'user_id':user_id, 'tweet_obj':result}
    sys.stderr.write('get_tweet could not be completed. Please rerun for below user id.\n')
    sys.stderr.write('user_id >> ' + user_id + '\n') 

    return {'user_id':user_id, 'tweet_obj':False}

def post_to_discord(result):
    logger.info('START:Post to Discord')
    if result['tweet_obj']:
        result['tweet_obj'].reverse()
        for item in result['tweet_obj']:
            call_discord_api(item)
    logger.info('END  :Post to Discord')

def call_discord_api(item):
    content = item['user_name'] + ' ' + item['created_at'] + '\n' + item['text'] + '\n' + item['url']
    try:
        response = requests.post(
            discord_webhook
            ,json.dumps({'content': content})
            ,headers={'Content-Type': 'application/json'}
        )
        print(response)
    except Exception as e:
        sys.stderr.write('Error occurs in post_to_discord.\n')
        sys.stderr.write(str(e) + '\n')
        sys.stderr.write('Could not post below content.\n')
        sys.stderr.write('user_name >> ' + item['user_name'] + '\n') 
        sys.stderr.write('created_at >> ' + item['created_at'] + '\n') 
    else:
        return response

def show_test_result(result):
    print('test mode')
    print(result['user_id'])
    if result['tweet_obj']:
        print(len(result['tweet_obj']))
    else:
        print('no tweet')
