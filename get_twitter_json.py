#!/usr/bin/python

import os.path
import simplejson
from time import sleep
import urllib2

username = 'thepeopleseason'
filename = '%s.json' % (username)

seen = {}
if os.path.isfile(filename):
    with open(filename, 'r') as FILE:
        tl = simplejson.loads(FILE.read())
else:
    tl = []

for tweet in tl:
    seen[tweet['id_str']] = 1

for page in range(1,160):
    print "fetching page %s" % (page)
    try:
        json = urllib2.urlopen('http://api.twitter.com/1/statuses/user_timeline.json?screen_name=%s&page=%s' % (username, page)).read()
    except:
        print "Ratelimited: sleeping for ten minutes..."
        sleep(600)
        json = urllib2.urlopen('http://api.twitter.com/1/statuses/user_timeline.json?screen_name=%s&page=%s' % (username, page)).read()

    ctl = simplejson.loads(json)
    for tweet in ctl:
        del tweet['user']
        if not seen.get(tweet['id_str']):
            tl.append(tweet)
    sleep(50)

with open(filename, 'w') as FILE:
    FILE.write(simplejson.dumps(tl))
