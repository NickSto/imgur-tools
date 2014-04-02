#!/usr/bin/env python
from __future__ import division
import re
import os
import sys
import argparse
import imgurlib
import imgurcache

USER_AGENT = 'NBS comment-searcher'
CONFIG_FILE = 'default.args'  # must be in same directory as script
API_DOMAIN = 'api.imgur.com'
API_PATH_TEMPLATE = '/3/account/{}/comments'

OPT_DEFAULTS = {'limit':20, 'ignore_case':True, 'verbose_mode':True,
  'verbose':None, 'quiet':None, 'regex':False, 'format':'human'}
USAGE = "%(prog)s [options]"
DESCRIPTION = """Search all comments by an Imgur user."""
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

  parser.add_argument('query',
    help='String to search for.')
  parser.add_argument('-u', '--user', required=True,
    help='The username whose comments will be searched. Required, if not '
      'provided by an @ file like @default.args.')
  parser.add_argument('-C', '--client-id', required=True,
    help='Imgur API Client-ID to use. Required, if not provided by an @ file '
      'like @default.args.')
  parser.add_argument('-c', '--case-sensitive', dest='ignore_case',
    action='store_false',
    help='Don\'t ignore case when searching. Default: '
      +str(not OPT_DEFAULTS['ignore_case']))
  parser.add_argument('-i', '--ignore-case', dest='ignore_case',
    action='store_true',
    help='Ignore case when searching. Default: '
      +str(OPT_DEFAULTS['ignore_case']))
  parser.add_argument('-r', '--regex', action='store_true',
    help='Use search string as a Python regex instead of a literal string to '
      'match. Default: '+str(OPT_DEFAULTS['regex']))
  parser.add_argument('-l', '--limit', type=int,
    help='Maximum number of results to return. Set to 0 for no limit. '
      'Default: %(default)s')
  parser.add_argument('-L', '--links', dest='format', action='store_const',
    const='links',
    help='Print permalinks to the comments instead of the full info. Turns off '
      'verbose mode, unless overriden. Default: '
      +str(OPT_DEFAULTS['format'] == 'links'))
  parser.add_argument('-f', '--feeling-lucky', dest='limit',
    action='store_const', const=1,
    help='Stop searching once the first hit is found. A shorthand for -l 1. '
      'Default: False')
  parser.add_argument('-q', '--quiet', dest='quiet', action='store_true',
    help='Do not print anything but the results (even if there are none). '
      'Default: '+str(not OPT_DEFAULTS['verbose_mode']))
  parser.add_argument('-v', '--verbose', action='store_true',
    help='Verbose output (print more than just the results). Default: '
      +str(OPT_DEFAULTS['verbose_mode']))

  new_argv = imgurlib.include_args_from_file(sys.argv, CONFIG_FILE)
  args = parser.parse_args(new_argv)
  
  if args.verbose is None and args.quiet is None:
    if args.format == 'human':
      args.verbose_mode = OPT_DEFAULTS['verbose_mode']
    elif args.format == 'links':
      args.verbose_mode = False
  else:
    args.verbose_mode = bool(args.verbose or not args.quiet)

  comments = imgurcache.get_cached_and_live_comments(args.user, args.client_id,
    user_agent=USER_AGENT)

  hits = 0
  for comment in comments:
    if is_match(comment['comment'], args):
      hits+=1
      if args.format == 'human':
        print imgurlib.human_format(comment)
      elif args.format == 'links':
        print imgurlib.link_format(comment)
    if args.limit and hits >= args.limit:
      break

  if args.verbose_mode:
    sys.stderr.write('Found '+str(hits)+' hits.\n')
    if args.limit and hits >= args.limit:
      sys.stderr.write('Reached the results limit. There may be more '
        'matching comments than are shown   here. Raise the search limit '
        '(currently '+str(args.limit)+') with the -l option to show more.\n')
    else:
      sys.stderr.write('Search complete. All matching comments were printed.\n')


def is_match(text, args):
  if args.regex:
    flags = 0
    if args.ignore_case:
      flags = re.I
    return bool(re.search(args.query, text, flags=flags))
  else:
    if args.ignore_case:
      return args.query.lower() in text.lower()
    else:
      return args.query in text


def fail(message):
  sys.stderr.write(message+"\n")
  sys.exit(1)

if __name__ == '__main__':
  main()
