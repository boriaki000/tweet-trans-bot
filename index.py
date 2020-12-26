import sys
sys.path.append('lib')

import json
import datetime
import os
import requests
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
target_ids = [x.strip() for x in str(os.getenv('TARGET_IDS')).split(',')]
time_distance = int(os.environ['TIME_DISTANCE'])
tweet_count = os.environ['TWEET_COUNT']
basetime = datetime.datetime.now()


def handler(event, context):
    result = []
    print(target_ids)
    for user_id in target_ids:
        print(user_id)
        result.append({'user_id':user_id,'tweet_obj':get_tweet(user_id)})
    
    for res in result:
        res['tweet_obj'].reverse()
        for item in res['tweet_obj']:
            post_to_discord(item)

def get_tweet(user_id):
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
    else:
        return result

def post_to_discord(item):
    content = item['user_name'] + ' ' + item['created_at'] + '\n' + item['text'] + '\n' + item['url']
    try:
        response = requests.post(
            os.environ['DICORD_WEBHOOK']
            ,json.dumps({'content': content})
            ,headers={'Content-Type': 'application/json'}
        )
        print(response)
    except Exception as e:
        sys.stderr.write('Error occurs in post_to_discord\n')
        sys.stderr.write(str(e) + '\n')
    else:
        return response