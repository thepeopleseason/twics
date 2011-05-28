#!/usr/bin/python

import os.path
import simplejson

from dateutil import parser
from optparse import OptionParser
from time import sleep

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

    # sort status updates in descending order
    tl.sort(key=lambda tw: parser.parse(tw['created_at']), reverse=True)

    with open(opts.file, 'w') as FILE:
        FILE.write(simplejson.dumps(tl, indent=2))

def main():
    usage = 'usage: %prog [JSON files]'
    parser = OptionParser(usage=usage, version='%prog 0.1')
    parser.add_option("-o", dest="file",
                      help="input/output file")
    (opts, args) = parser.parse_args()

    if len(args) == 0:
        print "\n** Please supply status files to be merged\n"
        parser.print_help()
        exit(1)

    # set default output file
    if not opts.file:
        opts.file = '%s-merge.json' % (
            '-'.join([fn.split('/')[-1].split('.')[0] for fn in args]))

    merge_status_files(opts, args)

if __name__ == "__main__":
    main()
