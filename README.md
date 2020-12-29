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

You can execute the function in local using by following command.
~~~
python-lambda-local -l lib/ -f handler -t 5 index.py event.json
~~~

Event json sample.
~~~
{
    "target_id":"[USER ID]"
    ,"time_distance":"180"
}
~~~

You can execute with specific time by passing 'basetime' parameter.
~~~
{
    "target_id":"[USER ID]"
    ,"time_distance":"180"
    ,"basetime":"2020-12-01 00:00:00"
}
~~~

You can test the function by adding 'testmode' parameter.
~~~
{
    "testmode":"1"
    ,"target_id":"[USER ID]"
    ,"time_distance":"180"
    ,"basetime":"2020-12-01 00:00:00"
}
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
