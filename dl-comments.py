#!/usr/bin/env python
from __future__ import division
import re
import os
import sys
import json
import argparse
import imgurlib

USER_AGENT = 'NBS comment-archiver'
CONFIG_FILE = 'default.args'  # must be in same directory as script
API_DOMAIN = 'api.imgur.com'
API_PATH_TEMPLATE = '/3/account/{}/comments'

OPT_DEFAULTS = {'limit':None, 'verbose_mode':True, 'verbose':None,'quiet':None,}
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
    help='Maximum number of comments to output. This is a rough limit. '
      'Comments are output a page at a time, so the actual number returned may '
      'be higher. Default: no limit.')
  parser.add_argument('-q', '--quiet', dest='quiet', action='store_true',
    help='Do not print anything but the results (even if there are none). '
      'Default: '+str(not OPT_DEFAULTS['verbose_mode']))
  parser.add_argument('-v', '--verbose', action='store_true',
    help='Verbose output (print more than just the results). Default: '
      +str(OPT_DEFAULTS['verbose_mode']))

  new_argv = imgurlib.include_args_from_file(sys.argv, CONFIG_FILE)
  args = parser.parse_args(new_argv)
  
  if args.verbose:
    args.verbose_mode = True
  if args.quiet:
    args.verbose_mode = False

  api_path = API_PATH_TEMPLATE.format(args.user)
  headers = {
    'Authorization':'Client-ID '+args.client_id,
    'User-Agent':USER_AGENT,
  }
  params = {
    'perPage':'100',
  }

  page_num = 0
  reached_end = False
  all_comments = []
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
    comments_returned = len(comments)

    if comments_returned == 0:
      reached_end = True
      still_searching = False
    else:
      all_comments.extend(comments)
      if args.limit and len(all_comments) >= args.limit:
        still_searching = False

    page_num+=1

  if args.output_file:
    with open(args.output_file, 'w') as filehandle:
      json.dump(all_comments, filehandle)
  else:
    print json.dumps(all_comments)

  if args.verbose_mode:
    sys.stderr.write('Saved '+str(len(all_comments))+' comments.\n')
    if reached_end:
      sys.stderr.write('All comments were retrieved.\n')
    else:
      sys.stderr.write('Found more comments than the limit. Raise the search '
        'limit (currently '+str(args.limit)+') with the -l option to retrieve '
        'more.\n')


def is_iterable(obj):
  try:
    iter(obj)
  except TypeError:
    return False
  return True


def fail(message):
  sys.stderr.write(message+"\n")
  sys.exit(1)

if __name__ == '__main__':
  main()
