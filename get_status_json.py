#!/usr/bin/python

import os.path
import simplejson
import urllib2

from dateutil import parser
from optparse import OptionParser
from time import sleep


def fetch_statuses(opts, args):
    apicall = {
        'twitter': 'http://api.twitter.com/1/statuses/user_timeline.json',
        'identica' : 'http://identi.ca/api/statuses/user_timeline.json',
        }

    if os.path.isfile(opts.file):
        with open(opts.file, 'r') as FILE:
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
        if opts.verbose:
            print "fetching page %s" % (page)
        apiurl = '%s?screen_name=%s&page=%s&count=200%s' % (
            apicall[opts.protocol], opts.username, page, since)
        if opts.verbose:
            print apiurl

        try:
            json = urllib2.urlopen(apiurl).read()
        except:
            print "Ratelimited: sleeping for ten minutes..."
            sleep(600)
            json = urllib2.urlopen(apiurl).read()

        ctl = simplejson.loads(json)
        ctl_count = len(ctl)
        if ctl_count == 0:
            print "No results returned, exiting loop"
            break

        for tweet in ctl:
            tweet['username'] = tweet['user']['screen_name']
            tweet['protocol'] = opts.protocol

            del tweet['user']

            if not seen.get(tweet['id_str']):
                tl.append(tweet)
        if ctl_count > 190:
            sleep(opts.sleep)
        else:
            break

    # sort tweets by most recent
    tl.sort(key=lambda tw: parser.parse(tw['created_at']), reverse=True)

    with open(opts.file, 'w') as FILE:
        FILE.write(simplejson.dumps(tl, indent=2))

def main():
    usage = 'usage: %prog [options] -u <username>'
    parser = OptionParser(usage=usage, version='%prog 0.1')
    parser.add_option("-v", "--verbose", dest="verbose",
                      action="store_true",
                      help="verbose output")
    parser.add_option("-u", dest="username",
                      help="service username **REQUIRED**")
    parser.add_option("-p", dest="protocol",
                      help="status service e.g. 'twitter'",
                      default='twitter')
    parser.add_option("-f", dest="file",
                      help="input/output file")
    parser.add_option("-s", type="int", dest="sleep",
                      help="sleep interval between API calls",
                      default=10)
    (opts, args) = parser.parse_args()

    if not opts.username:
        print "\n** Please supply a username\n"
        parser.print_help()
        exit(1)

    # set default file
    if not opts.file:
        opts.file = '%s-%s.json' % (opts.username, opts.protocol)

    fetch_statuses(opts)

if __name__ == "__main__":
    main()
