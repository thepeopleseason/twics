#!/usr/bin/python

import os.path
import simplejson
import vobject

from dateutil import parser
from optparse import OptionParser

def status2ics(opts, args):
    jsonfile = args[0]
    if os.path.isfile(jsonfile):
        with open(jsonfile, 'r') as FILE:
            tl = simplejson.loads(FILE.read())
    else:
        tl = []

    cal = vobject.iCalendar()
    cal.add('prodid').value = '-//twitter.com/twitter ICS//EN'
    cal.add('version').value ='1.0'
    cal.add('calscale').value ='GREGORIAN'
    cal.add('x-wr-calname').value ='status updates'

    tl.sort(key=lambda tw: tw['id'], reverse=True)

    for tweet in tl:
        created = parser.parse(tweet['created_at'])
        if tweet['protocol'] == 'identica':
            url = 'http://identi.ca/notice/%s' % (tweet['id'])
        else:
            url = 'http://twitter.com/%s/status/%s/' % (tweet['username'],
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

    icsfile = opts.file
    with open(icsfile, 'w') as FILE:
        FILE.write(cal.serialize())

def main():
    usage = 'usage: %prog [options] <JSON file>'
    parser = OptionParser(usage=usage, version='%prog 0.1')
    parser.add_option("-o", dest="file",
                      help="output file")
    (opts, args) = parser.parse_args()

    if len(args) != 1:
        print "\n** Please supply a single status file to be converted\n"
        parser.print_help()
        exit(1)

    # set default output file
    if not opts.file:
        opts.file = '%s.ics' % args[0].split('.')[0]

    status2ics(opts, args)

if __name__ == '__main__':
    main()
