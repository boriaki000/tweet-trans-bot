import sys
sys.path.append('lib')

import json
import os
import requests
import logging
from datetime import datetime
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
logger = logging.getLogger()
logger.setLevel(logging.INFO)
target_ids = [x.strip() for x in str(os.getenv('TARGET_IDS')).split(',')]
time_distance = int(os.environ['TIME_DISTANCE'])
tweet_count = os.environ['TWEET_COUNT']
retry_count = 3


def handler(event, context):
    basetime = datetime.now()
    # override parameter
    if event.get('basetime'):
        print('override basetime!')
        basetime = datetime.strptime(event['basetime'], '%Y-%m-%d %H:%M:%S')
    print('--- PARAM ---')
    print('target_ids:' + str(target_ids))
    print('basetime:' + str(basetime))
    print('time_distance:' + str(time_distance))
    print('tweet_count:' + str(tweet_count))

    result = get_search_result(basetime)

    if event.get('testmode'):
        show_test_result(result)
    else:
        post_to_discord(result)

def get_search_result(basetime):
    logger.info('START:Get Tweet')
    result = []
    for user_id in target_ids:
        result.append({'user_id':user_id,'tweet_obj':get_tweet(user_id, basetime)})
    logger.info('END  :Get Tweet')

    return result

def get_tweet(user_id, basetime):
    for i in range(0, retry_count):
        try:
            tweets = api.user_timeline(user_id, count=tweet_count, tweet_mode='extended')
            result = []
            for tweet in tweets:
                distance = basetime - tweet.created_at
                if distance.days == 0 and distance.seconds < time_distance:
                    translated = translator.translate('tranlated:' + tweet.full_text, src='en', dest='ja')
                    result.append({'user_name':tweet.user.name
                                ,'created_at':str(tweet.created_at)
                                ,'text':translated.text
                                ,'url':'https://twitter.com/' + user_id + '/status/' + str(tweet.id)})
        except Exception as e:
            sys.stderr.write('Error occurs in get_tweet\n')
            sys.stderr.write(str(e) + '\n')
            sleep(i * 5)
        else:
            return result
    sys.stderr.write('get_tweet could not be completed. Please rerun for below user id.\n')
    sys.stderr.write('user_id >> ' + user_id + '\n') 

    return False

def post_to_discord(result):
    logger.info('START:Post to Discord')
    for res in result:
        if res['tweet_obj']:
            res['tweet_obj'].reverse()
            for item in res['tweet_obj']:
                call_discord_api(item)
    logger.info('END  :Post to Discord')

def call_discord_api(item):
    content = item['user_name'] + ' ' + item['created_at'] + '\n' + item['text'] + '\n' + item['url']
    try:
        response = requests.post(
            os.environ['DICORD_WEBHOOK']
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
    for res in result:
        print(res['user_id'])
        if res['tweet_obj']:
            print(len(res['tweet_obj']))
        else:
            print('no tweet')
    print(len(result))
