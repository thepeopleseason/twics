#!/usr/bin/python

import os.path
import simplejson
import urllib2

from dateutil import parser
from time import sleep

username = 'seasonsinexile'
protocol = 'twitter'
filename = '%s-%s.json' % (username, protocol)

sleepinterval = 10

apicall = {
    'twitter': 'http://api.twitter.com/1/statuses/user_timeline.json',
    'identica' : 'http://identi.ca/api/statuses/user_timeline.json',
    }

if os.path.isfile(filename):
    with open(filename, 'r') as FILE:
        tl = simplejson.loads(FILE.read())
else:
    tl = []

# process existing list
seen = {}
max_id = 0
since = ''
for tweet in tl:
    seen[tweet['id']] = 1
    if tweet['id'] > max_id:
        max_id = tweet['id']

if max_id:
    since = '&since_id=%s' % (max_id)

for page in range(1,17):
    print "fetching page %s" % (page)
    apiurl = '%s?screen_name=%s&page=%s&count=200%s' % (
        apicall[protocol], username, page, since)
    print apiurl

    try:
        json = urllib2.urlopen(apiurl).read()
    except:
        print "Ratelimited: sleeping for ten minutes..."
        sleep(600)
        json = urllib2.urlopen(apiurl).read()

    ctl = simplejson.loads(json)
    if len(ctl) == 0:
        print "no results returned, exiting loop"
        break

    for tweet in ctl:
        tweet['username'] = tweet['user']['screen_name']
        tweet['protocol'] = protocol

        del tweet['user']

        if not seen.get(tweet['id_str']):
            tl.append(tweet)
    sleep(sleepinterval)

tl.sort(key=lambda tw: parser.parse(tw['created_at']), reverse=True)

with open(filename, 'w') as FILE:
    FILE.write(simplejson.dumps(tl, indent=2))
