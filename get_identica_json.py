#!/usr/bin/python

import os.path
import simplejson
from time import sleep
import urllib2

username = 'thepeopleseason'
filename = '%s-identica.json' % (username)

seen = {}
if os.path.isfile(filename):
    with open(filename, 'r') as FILE:
        tl = simplejson.loads(FILE.read())
else:
    tl = []

for page in range(30,93):
    print "fetching page %s" % (page)
    try:
        json = urllib2.urlopen('http://identi.ca/api/statuses/user_timeline.json?screen_name=%s&page=%s' % (username, page)).read()
    except:
        print "Ratelimited: sleeping for ten minutes..."
        sleep(600)
        json = urllib2.urlopen('http://identi.ca/api/statuses/user_timeline.json?screen_name=%s&page=%s' % (username, page)).read()

    ctl = simplejson.loads(json)
    for tweet in ctl:
        del tweet['user']
        tl.append(tweet)
    sleep(10)

with open(filename, 'w') as FILE:
    FILE.write(simplejson.dumps(tl))
