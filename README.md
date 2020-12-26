# Tweet Translation Bot
This bot has the following features.<br>
1.Get tweet<br>
2.Translate tweet content from english to japanese<br>
3.Post content to dicord<br>

### Set up your develop environment
~~~
$ docker build ./ -t trbot
$ docker run -itd -v $(pwd):/usr/src/app --name trbot trbot
$ docker exec -it trbot sh
~~~

You can test the function in local using by following command.
~~~
python-lambda-local -l lib/ -f handler -t 5 index.py event.json
~~~

### Export Environment variable
This bot uses following environment variable.<br>
|key|description|
|------|------|
|CONSUMER_KEY|Your twitter key|
|CONSUMER_SECRET|Your twitter key|
|ACCESS_TOKEN|Your twitter key|
|ACCESS_TOKEN_SECRET|Your twitter key|
|DICORD_WEBHOOK|Your Discord channel's webhook url|
|TIME_DISTANCE|How many seconds ago to get the information.|
|TARGET_IDS|Twitter ids you want to get. eg.id1,id2,id3|
|TWEET_COUNT|How many tweets you want to get.|