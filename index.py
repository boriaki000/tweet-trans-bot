import sys
sys.path.append('lib')

import json
import os
import requests
import logging
from pytz import timezone, utc
from datetime import datetime
from time import sleep
from googletrans import Translator
from requests_oauthlib import OAuth1Session

# Twitter API
twitter = OAuth1Session(os.environ['CONSUMER_KEY']
    ,os.environ['CONSUMER_SECRET']
    ,os.environ['ACCESS_TOKEN']
    ,os.environ['ACCESS_TOKEN_SECRET']
)
twitter_api_url = 'https://api.twitter.com/1.1/statuses/user_timeline.json'
# Translator
translator = Translator()
# Other
discord_webhook = os.environ['DISCORD_WEBHOOK']
logger = logging.getLogger()
if os.environ.get('LOG_LEVEL') and os.environ['LOG_LEVEL'] == 'debug':
    logger.setLevel(logging.DEBUG)
else:
    logger.setLevel(logging.INFO)
retry_count = 3
text_prefix = '```'
default_mode = {
    "src":"en"
    ,"dest":"ja"
}

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

    if event.get('trans_mode'):
        trans_mode = event['trans_mode']
    else:
        trans_mode = default_mode

    logger.info('--- PARAM ---')
    logger.info('target_id:' + str(target_id))
    logger.info('basetime:' + str(basetime))
    logger.info('time_distance:' + str(time_distance))
    logger.info('timezone:' + timezone_str)

    result = get_tweet(target_id, basetime, time_distance, pytz_timezone, trans_mode)

    if event.get('testmode'):
        show_test_result(result)
    else:
        post_to_discord(result)

def get_tweet(user_id, basetime, time_distance, pytz_timezone, trans_mode):
    logger.info('START:Get Tweet')
    for i in range(0, retry_count):
        try:
            response = twitter.get(twitter_api_url, params = {'screen_name':user_id ,'count':10, 'include_rts':True, 'tweet_mode':'extended'})
            timelines = json.loads(response.text)
            result = []
            for tweet in timelines:
                created_at = datetime.strptime(tweet['created_at'], '%a %b %d %H:%M:%S +0000 %Y')
                distance = basetime - created_at
                if distance.days == 0 and distance.seconds < time_distance:
                    text = extract_text(tweet, trans_mode)
                    result.append({'user_name':tweet['user']['name']
                                ,'created_at':str(pytz_timezone.localize(created_at))
                                ,'text':text_prefix + text + text_prefix
                                ,'url':'https://twitter.com/' + user_id + '/status/' + str(tweet['id'])})
        except Exception as e:
            logger.warn('Error occurs in get_tweet\n')
            logger.warn(str(e) + '\n')
            sleep(i * 5)
        else:
            logger.info('END  :Get Tweet')
            return {'user_id':user_id, 'tweet_obj':result}

    logger.error('get_tweet could not be completed. Please rerun for below user id.\n')
    logger.error('user_id >> ' + user_id + '\n') 
    raise Exception('Inner Error')

def extract_text(tweet_obj, trans_mode):
    if tweet_obj.get('retweeted_status'):
        text = tweet_obj['retweeted_status']['full_text']
    else:
        text = tweet_obj['full_text']

    if not trans_mode.get('skip_mode'):
        text = translator.translate('translated:' + text, src=trans_mode['dest'], dest=trans_mode['dest']).text

    return text

def post_to_discord(result):
    logger.info('START:Post to Discord')
    if result['tweet_obj']:
        result['tweet_obj'].reverse()
        for item in result['tweet_obj']:
            call_discord_api(item)
    logger.info('END  :Post to Discord')

def call_discord_api(item):
    content = item['user_name'] + ' ' + item['created_at'] + '\n' + item['text'] + '\n' + item['url']
    for i in range(0, retry_count):
        try:
            response = requests.post(
                discord_webhook
                ,json.dumps({'content': content})
                ,headers={'Content-Type': 'application/json'}
            )
            if response.status_code != requests.codes['no_content']:
                raise Exception('Webhook returned not expected code >>' + str(response))
        except Exception as e:
            logger.warn('Error occurs in post_to_discord.\n')
            logger.warn(str(e) + '\n')
            sleep(i * 5)
        else:
            return response

    logger.error('Could not post below content.\n')
    logger.error('user_name >> ' + item['user_name'] + '\n') 
    logger.error('created_at >> ' + item['created_at'] + '\n') 
    raise Exception('Inner Error')

def show_test_result(result):
    logger.debug('test mode')
    logger.debug(result['user_id'])
    if result['tweet_obj']:
        logger.debug(len(result['tweet_obj']))
        for res in result['tweet_obj']:
            logger.debug(res['text'])
    else:
        logger.debug('no tweet')
