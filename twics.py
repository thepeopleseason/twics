#!/usr/bin/python

import os.path
import simplejson
import urllib2

from dateutil import parser
from optparse import OptionParser, OptionGroup
from time import sleep

def clean_status(tweet, protocol):
    if not tweet.get('username') and \
            tweet.get('user') and tweet['user'].get('screen_name'):
        tweet['username'] = tweet['user']['screen_name']
        tweet['protocol'] = protocol

    if tweet['username'] and tweet['protocol'] and tweet.get('user'):
        del tweet['user']

    return tweet

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
            if not seen.get(tweet['id_str']):
                tl.append(clean_status(tweet, opts.protocol))
        if ctl_count == 200:
            sleep(opts.sleep)
        else:
            break

    write_json(tl, opts.file)

def integrate_statuses(opts, args):
    apicall = {
        'twitter': 'http://api.twitter.com/1/statuses/show',
        'identica': 'http://identi.ca/api/statuses/show',
        }

    if os.path.isfile(opts.file):
        with open(opts.file, 'r') as FILE:
            tl = simplejson.loads(FILE.read())
    else:
        tl = []

    # process existing list
    seen = {}
    for tweet in tl:
        seen[tweet['id']] = 1

    # process integration source
    if os.path.isfile(opts.indiv):
        with open(opts.indiv, 'r') as FILE:
            lines = FILE.read().split('\n')
    else:
        lines = [ opts.indiv, ]

    for line in lines:
        tid = None
        try:
            tid = int(line.split('/')[-1])
        except:
            continue

        if tid and not seen.get(tid):
            apiurl = '%s/%s.json' % (apicall[opts.protocol], tid)
        if opts.verbose:
            print apiurl

        try:
            json = urllib2.urlopen(apiurl).read()
        except:
            print "Ratelimited: sleeping for ten minutes..."
            sleep(600)
            json = urllib2.urlopen(apiurl).read()

        tweet = simplejson.loads(json)

        tl.append(clean_status(tweet, opts.protocol))
        sleep(opts.sleep)

    write_json(tl, opts.file)

def merge_status_files(opts, args):
    seen = {}
    tl = []

    for status_file in args:
        if os.path.isfile(status_file):
            with open(status_file, 'r') as FILE:
                ctl = simplejson.loads(FILE.read())
        else:
            ctl = []

        tl.extend(ctl)

    for tweet in tl:
        clean_status(tweet, opts.protocol)

    write_json(tl, opts.file)

def status2ics(opts, args):
    import vobject

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

def write_json(tl, output_file):
    # sort status updates in descending order
    tl.sort(key=lambda tw: parser.parse(tw['created_at']), reverse=True)

    with open(output_file, 'w') as FILE:
        FILE.write(simplejson.dumps(tl, indent=2))


def main():
    usage = 'usage: %prog <action> [options]'
    parser = OptionParser(usage=usage, version='%prog 0.1')
    parser.add_option("-v", "--verbose", dest="verbose",
                      action="store_true",
                      help="verbose output")
    parser.add_option("-f", dest="file",
                      help="output file (input and output on fetch)")

    # %prog fetch options
    fgroup = OptionGroup(parser, "fetch/integrate options")
    fgroup.add_option("-u", dest="username",
                      help="service username **REQUIRED for fetch**")
    fgroup.add_option("-i", dest="indiv",
                      help="integration source (status id, url, or listing)")
    fgroup.add_option("-p", dest="protocol",
                      help="status service e.g. 'twitter'",
                      default='twitter')
    fgroup.add_option("-s", type="int", dest="sleep",
                      help="sleep interval between API calls",
                      default=10)
    parser.add_option_group(fgroup)

    (opts, args) = parser.parse_args()

    if len(args) < 1:
        print "\n** Please supply an action to perform\n"
        parser.print_help()
        exit(1)
    else:
        action = args.pop(0)

    if action == 'fetch' or action == 'integrate':
        if action == 'fetch' and not opts.username:
            print "\n** Please supply a username\n"
            parser.print_help()
            exit(1)
        if action == 'integrate' and not opts.indiv:
            print "\n** Please supply an integration source\n"
            parser.print_help()
            exit(1)
        default_file = '%s-%s.json' % (opts.username, opts.protocol)

    elif action == 'generate':
        if len(args) != 1:
            print "\n** Please supply a single status file to be converted\n"
            parser.print_help()
            exit(1)
        default_file = '%s.ics' % args[0].split('.')[0]

    elif action == 'merge':
        if len(args) == 0:
            print "\n** Please supply status files to be merged\n"
            parser.print_help()
            exit(1)
        default_file = '%s-merge.json' % (
            '-'.join([fn.split('/')[-1].split('.')[0] for fn in args]))

    # set default output file
    if not opts.file:
        opts.file = default_file

    dispatch = {
        'generate': status2ics,
        'merge': merge_status_files,
        'fetch': fetch_statuses,
        'integrate': integrate_statuses,
        }

    dispatch[action](opts, args)

if __name__ == '__main__':
    main()
