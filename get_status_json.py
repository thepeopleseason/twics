#!/usr/bin/python

import os.path
import simplejson
from time import sleep
import urllib2

username = 'crapfrommypast'
protocol = 'twitter'
filename = '%s-%s.json' % (protocol, username)

sleepinterval = 10

apicall = {
    'twitter': 'http://api.twitter.com/1/statuses/user_timeline.json',
    'identica' : 'http://identi.ca/api/statuses/user_timeline.json',
    }

seen = {}
if os.path.isfile(filename):
    with open(filename, 'r') as FILE:
        tl = simplejson.loads(FILE.read())
else:
    tl = []

for tweet in tl:
    seen[tweet['id']] = 1

for page in range(1,5):
    print "fetching page %s" % (page)
    apiurl = '%s?screen_name=%s&page=%s&count=200' % (
        apicall[protocol], username, page)
    try:
        json = urllib2.urlopen(url).read()
    except:
        print "Ratelimited: sleeping for ten minutes..."
        sleep(600)
        json = urllib2.urlopen(url).read()

    ctl = simplejson.loads(json)
    for tweet in ctl:
        tweet['user'] = username
        if not seen.get(tweet['id_str']):
            tl.append(tweet)
    sleep(sleepinterval)

with open(filename, 'w') as FILE:
    FILE.write(simplejson.dumps(tl, indent=2))
