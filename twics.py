#!/usr/bin/python

""" twics.py -- various functions to convert microblogging service
status updates into ical format for inclusion on calendars """

import oauth2 as oauth
import os.path
import simplejson
import urllib2
import vobject

from dateutil import parser
from optparse import OptionParser, OptionGroup
from time import sleep

config = {}

def clean_status(tweet, protocol):
    """ add username and protocol attributes to json output and remove
    extraneous user details """

    if (not tweet.get('username') and
        tweet.get('user') and tweet['user'].get('screen_name')):
        tweet['username'] = tweet['user']['screen_name']
        tweet['protocol'] = protocol

    if tweet['username'] and tweet['protocol'] and tweet.get('user'):
        del tweet['user']

    return tweet

def fetch_statuses(opts, args):
    """ fetch the most recent statuses from the microblogging service """

    apicall = {
        'twitter': 'http://api.twitter.com/1/statuses/user_timeline.json',
        'identica' : 'http://identi.ca/api/statuses/user_timeline.json',
        }

    tl = load_json_list(opts.file)

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

    for page in range(1, 17):
        if opts.verbose:
            print "fetching page %s" % (page)
        apiurl = '%s?screen_name=%s&page=%s&count=200%s' % (
            apicall[opts.protocol], opts.username, page, since)
        if opts.verbose:
            print apiurl

        try:
            json = get_content(opts, apiurl)
        except:
            print "Ratelimited: sleeping for ten minutes..."
            sleep(600)
            json = get_content(opts, apiurl)

        ctl = simplejson.loads(json)
        ctl_count = len(ctl)
        if ctl_count == 0:
            print "No results returned, exiting loop"
            break

        for tweet in ctl:
            if not seen.get(tweet['id']):
                tl.append(clean_status(tweet, opts.protocol))
        if ctl_count < 200:
            sleep(opts.sleep)
        else:
            break

    write_json(tl, opts.file)

def get_content(opts, apicall):
    """ fetch content via apicall """
    if not config['token']:
        return urllib2.urlopen(apiurl).read()

    consumer = oauth.Consumer(
        key=config['consumer']['key'],
        secret=config['consumer']['secret'])

    token = oauth.Token(
        key=config['token']['key'],
        secret=config['token']['secret'])

    # Create our client.
    client = oauth.Client(consumer, token)

    # The OAuth Client request works just like httplib2 for the most part.
    if opts.verbose:
        print "Fetching %s" % apicall

    resp, content = client.request(apicall, "GET")

    if opts.verbose:
        print "Returned %s: %s" % (resp['status'], content)

    if resp['status'] == '200':
        return content
    else:
        return '[]'

def integrate_statuses(opts, args):
    """ integrate individual statuses or a list of status urls/ids into
    an existing json archive"""

    apicall = {
        'twitter': 'http://api.twitter.com/1/statuses/show',
        'identica': 'http://identi.ca/api/statuses/show',
        }

    tl = load_json_list(opts.file)

    # process existing list
    seen = {}
    for tweet in tl:
        seen[tweet['id']] = 1

    # process integration source
    if os.path.isfile(opts.indiv):
        with open(opts.indiv, 'r') as FILE:
            lines = FILE.read().split('\n')
    else:
        # url/id passed in on command line
        lines = [ opts.indiv, ]

    for line in lines:
        tid = None
        try:
            tid = int(line.split('/')[-1])
        except ValueError:
            continue

        if seen.get(tid):
            continue

        if tid:
            apiurl = '%s/%s.json' % (apicall[opts.protocol], tid)
        if opts.verbose:
            print apiurl

        try:
            json = get_content(opts, apiurl)
        except:
            print "Ratelimited: sleeping for ten minutes..."
            sleep(600)
            json = get_content(opts, apiurl)

        tweet = simplejson.loads(json)

        tl.append(clean_status(tweet, opts.protocol))
        sleep(opts.sleep)

    write_json(tl, opts.file)

def load_keyfile(config, key, keyfile):
    keys = {}
    if os.path.isfile(keyfile):
        with open(keyfile) as kfile:
            keys = simplejson.loads(kfile.read())

    config[key] = keys

def load_json_list(input_file):
    """ load json file and return the listing (otherwise return empty list)"""
    if os.path.isfile(input_file):
        with open(input_file, 'r') as FILE:
            listing = simplejson.loads(FILE.read())
    else:
        listing = []

    return listing

def merge_status_files(opts, args):
    """ merge multiple status json archives """

    tl = []
    for status_file in args:
        tl.extend(load_json_list(status_file))

    for tweet in tl:
        clean_status(tweet, opts.protocol)

    write_json(tl, opts.file)

def status2ics(opts, args):
    """ write ical format of status updates """

    tl = load_json_list(args[0])

    cal = vobject.iCalendar()
    cal.add('prodid').value = '-//twitter.com/twitter ICS//EN'
    cal.add('version').value ='1.0'
    cal.add('calscale').value ='GREGORIAN'
    cal.add('x-wr-calname').value ='status updates'

    tl.sort(key=lambda tw: parser.parse(tw['created_at']), reverse=True)

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
    """ write output json file """

    # sort status updates in descending order
    tl.sort(key=lambda tw: parser.parse(tw['created_at']), reverse=True)

    with open(output_file, 'w') as FILE:
        FILE.write(simplejson.dumps(tl, indent=2))

def emit_usage(oparser, die=True):
    """ emit program help """

    oparser.print_help()
    if die:
        exit(1)

def main():
    """ main """

    dispatch = {
        'generate': status2ics,
        'merge': merge_status_files,
        'fetch': fetch_statuses,
        'integrate': integrate_statuses,
        }

    usage = 'usage: %%prog (%s) [options]' % '|'.join(dispatch.keys())
    oparser = OptionParser(usage=usage, version='%prog 0.2')
    oparser.add_option("-v", "--verbose", dest="verbose",
                      action="store_true",
                      help="verbose output")
    oparser.add_option("-f", dest="file",
                      help="output file (input and output on fetch)")

    # %prog fetch options
    fgroup = OptionGroup(oparser, "fetch/integrate options")
    fgroup.add_option("-u", dest="username",
                      help="service username **REQUIRED for fetch**")
    fgroup.add_option("-k", dest="keyfile",
                      help="file containing JSON-formatted OAuth Token")
    fgroup.add_option("-i", dest="indiv",
                      help="integration source (status id, url, or listing)")
    fgroup.add_option("-p", dest="protocol",
                      help="status service (default='twitter')",
                      default='twitter')
    fgroup.add_option("-s", type="int", dest="sleep",
                      help="sleep interval between API calls (default=10)",
                      default=10)
    oparser.add_option_group(fgroup)

    (opts, args) = oparser.parse_args()

    if len(args) < 1:
        print "\n** Please supply an action to perform\n"
        emit_usage(oparser)
    else:
        action = args.pop(0)

    default_file = None
    if action == 'fetch' or action == 'integrate':
        if action == 'fetch' and not opts.username:
            print "\n** Please supply a username\n"
            emit_usage(oparser)

        if action == 'integrate':
            if not opts.indiv:
                print "\n** Please supply an integration source\n"
                emit_usage(oparser)
            if not opts.file and not opts.username:
                print "\n** Please supply an output file or a username\n"
                emit_usage(oparser)
        default_file = '%s-%s.json' % (opts.username, opts.protocol)
        default_keyfile = '%s.keys' % (opts.username)

    elif action == 'generate':
        if len(args) != 1:
            print "\n** Please supply a single status file to be converted\n"
            emit_usage(oparser)
        default_file = '%s.ics' % args[0].split('.')[0]

    elif action == 'merge':
        if len(args) == 0:
            print "\n** Please supply status files to be merged\n"
            emit_usage(oparser)
        default_file = '%s-merge.json' % (
            '-'.join([fn.split('/')[-1].split('.')[0] for fn in args]))

    # set default output file
    if not opts.file:
        opts.file = default_file

    if opts.protocol == 'twitter':
        if not opts.keyfile and default_keyfile:
            opts.keyfile = default_keyfile
        load_keyfile(config, 'token', opts.keyfile)
        load_keyfile(config, 'consumer', 'twics.keys')

    dispatch[action](opts, args)

if __name__ == '__main__':
    main()
