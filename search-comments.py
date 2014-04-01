#!/usr/bin/env python
from __future__ import division
import re
import os
import sys
import argparse
import imgurlib

USER_AGENT = 'NBS comment-searcher'
CONFIG_FILE = 'default.args'  # must be in same directory as script
API_DOMAIN = 'api.imgur.com'
API_PATH_TEMPLATE = '/3/account/{}/comments'

OPT_DEFAULTS = {'limit':20, 'ignore_case':True, 'verbose_mode':True,
  'verbose':None, 'quiet':None, 'regex':False, 'format':'human',
  'stop_when_found':False}
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
    help="""String to search for.""")
  parser.add_argument('-u', '--user', required=True,
    help="""The username whose comments will be searched. Required, if not
provided by an @ file like @default.args.""")
  parser.add_argument('-C', '--client-id', required=True,
    help="""Imgur API Client-ID to use. Required, if not provided by an @ file
like @default.args.""")
  parser.add_argument('-c', '--case-sensitive', dest='ignore_case',
    action='store_false',
    help='Don\'t ignore case when searching. Default: '
      +str(not OPT_DEFAULTS['ignore_case']))
  parser.add_argument('-i', '--ignore-case', dest='ignore_case',
    action='store_true',
    help='Ignore case when searching. Default: '
      +str(OPT_DEFAULTS['ignore_case']))
  parser.add_argument('-r', '--regex', action='store_true',
    help="""Use search string as a Python regex instead of a literal string to
match. Default: """+str(OPT_DEFAULTS['regex']))
  parser.add_argument('-l', '--limit', type=int,
    help="""Maximum number of results to return. Default: %(default)s""")
  parser.add_argument('-L', '--links', dest='format', action='store_const',
    const='links',
    help="""Print permalinks to the comments instead of the full info. Turns off
      verbose mode, unless overriden. Default: """
      +str(OPT_DEFAULTS['format'] == 'links'))
  parser.add_argument('-s', '--stop-when-found', action='store_true',
    help='Stop searching once a hit is found. Default: '
      +str(OPT_DEFAULTS['stop_when_found']))
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

  api_path = API_PATH_TEMPLATE.format(args.user)
  headers = {
    'Authorization':'Client-ID '+args.client_id,
    'User-Agent':USER_AGENT,
  }
  params = {
    'perPage':'100',
  }

  hits = 0
  page_num = 0
  hit_limit = False
  still_searching = True
  while still_searching:
    # make request
    params['page'] = str(page_num)
    (response, comments) = imgurlib.make_request(
      api_path,
      headers,
      params=params,
      domain=API_DOMAIN
    )
    if response.status != 200:
      fail('Error: HTTP status '+str(response.status))

    assert is_iterable(comments), 'Error: Expected comments to be an iterable.'
    if len(comments) == 0:
      still_searching = False
    
    for comment in comments:
      assert 'comment' in comment, 'Error: no "comment" key in comment.'
      if is_match(comment['comment'], args):
        if hits >= args.limit:
          hit_limit = True
          still_searching = False
          break
        hits+=1
        if args.format == 'human':
          print imgurlib.human_format(comment)
        elif args.format == 'links':
          print imgurlib.link_format(comment)
        if args.stop_when_found:
          still_searching = False
          break

    page_num+=1

  if args.verbose_mode:
    sys.stderr.write('Printed '+str(hits)+' hits.\n')
    if hit_limit:
      sys.stderr.write('Found more comments than are shown here. Raise the '
        'search limit (currently '+str(args.limit)+')   with the -l option to '
        'show more.\n')
    else:
      sys.stderr.write('Search complete. All matching comments were printed.\n')


def is_iterable(obj):
  try:
    iter(obj)
  except TypeError:
    return False
  return True


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
