#!/usr/bin/python

import os.path
import simplejson
import vobject

from dateutil import parser

username = 'thepeopleseason'
jsonfile = '%s.json' % (username)
icsfile = '%s.ics' % (username)

seen = {}
if os.path.isfile(jsonfile):
    with open(jsonfile, 'r') as FILE:
        tl = simplejson.loads(FILE.read())
else:
    tl = []

for tweet in tl:
    if not tweet.get('statusnet_html'):
        seen[tweet['id_str']] = 1

cal = vobject.iCalendar()
cal.add('prodid').value = '-//twitter.com/twitter ICS//EN'
cal.add('version').value ='1.0'
cal.add('calscale').value ='GREGORIAN'
cal.add('x-wr-calname').value ='twitter updates for %s' % (username)

tl.sort(key=lambda tw: tw['id'], reverse=True)
for tweet in tl:
    created = parser.parse(tweet['created_at'])
    if tweet.get('statusnet_html'):
        url = 'http://identi.ca/notice/%s' % (tweet['id'])
    else:
        user = username
        if tweet.get('username'):
            user = tweet['username']
        url = 'http://twitter.com/%s/status/%s/' % (user,
                                                    tweet['id_str'])
    urlsp = url.split('/')[2:]
    uid = '%s@%s' % ('-'.join(urlsp[1:]), urlsp[0])

    event = cal.add('vevent')
    event.add('summary').value = tweet['text']
    event.add('description').value = '%s %s' % (tweet['text'], url)
    event.add('dtstart').value = created
    event.add('dtend').value = created
    event.add('dtstamp').value = created
    event.add('url').value = url
    event.add('uid').value = uid

# with open(icsfile, 'w') as FILE:
#     FILE.write(cal.as_string())

print cal.serialize()
