#!/usr/bin/env python
from __future__ import division
import re
import os
import sys
import json
import argparse
import imgurlib
import imgurcache

USER_AGENT = 'NBS comment-archiver'
CONFIG_FILE = 'default.args'  # must be in same directory as script
API_DOMAIN = 'api.imgur.com'
API_PATH_TEMPLATE = '/3/account/{}/comments'

OPT_DEFAULTS = {'limit':0, 'verbose':None,'quiet':None}
USAGE = "%(prog)s [options]"
DESCRIPTION = """Download all comments by an Imgur user. By default, comments
will be printed to stdout in JSON format. Individual comments will be in the
same structure as the Imgur API returns, and they will all be contained in one
big list."""
EPILOG = """You can include command line arguments from a file by including the
path to the file, prefixed with "@", as an argument (like "@dir/args.txt"). The
file should contain normal command line options, one per line. Ones that take
arguments and the arguments themselves should be on separate lines (e.g. put
"-l" on one line, and "10" on the next). If it is present in the script
directory, it will automatically include arguments from the file "\
"""+CONFIG_FILE+'"'


def main():

  parser = argparse.ArgumentParser(description=DESCRIPTION, epilog=EPILOG,
    fromfile_prefix_chars='@')
  parser.set_defaults(**OPT_DEFAULTS)

  parser.add_argument('-u', '--user', required=True,
    help='The username whose comments will be downloaded. Required (if not '
    'provided by an @ file like @default.args).')
  parser.add_argument('-C', '--client-id', required=True,
    help='Imgur API Client-ID to use. Required (if not provided by an @ file '
      'like @default.args).')
  parser.add_argument('-o', '--output-file',
    help='A file to save the comments in, instead of printing to stdout.')
  parser.add_argument('-l', '--limit', type=int,
    help='Maximum number of comments to output. Default: no limit.')
  parser.add_argument('-q', '--quiet', dest='quiet', action='store_true',
    help='Do not print anything but the results (even if there are none). '
      'Default: False')
  parser.add_argument('-v', '--verbose', action='store_true',
    help='Verbose output (print more than just the results). Default: True')

  new_argv = imgurlib.include_args_from_file(sys.argv, CONFIG_FILE)
  args = parser.parse_args(new_argv)
  
  if args.verbose:
    verbosity = 2
  elif args.quiet:
    verbosity = 0
  else:
    verbosity = 2

  comment_generator = imgurcache.get_comments(args.user, args.client_id,
    limit=args.limit, user_agent=USER_AGENT, verbosity=verbosity)
  comments = list(comment_generator)

  if args.output_file:
    with open(args.output_file, 'w') as filehandle:
      json.dump(comments, filehandle)
  else:
    print json.dumps(comments)

  if verbosity > 0:
    sys.stderr.write('Saved '+str(len(comments))+' comments.\n')


def fail(message):
  sys.stderr.write(message+"\n")
  sys.exit(1)

if __name__ == '__main__':
  main()
