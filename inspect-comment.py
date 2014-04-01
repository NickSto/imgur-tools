#!/usr/bin/env python
#TODO: move common code out to module
from __future__ import division
import re
import os
import sys
import json
import urllib
import httplib
import argparse
import datetime
import imgurlib

CONFIG_FILE = 'default.args'  # must be in same directory as script
API_DOMAIN = 'api.imgur.com'
API_PATH = '/3/comment/'
USER_AGENT = 'NBS comment-inspector'

OPT_DEFAULTS = {'limit':20, 'ignore_case':True, 'verbose':True,
  'stop_when_found':False}
USAGE = "%(prog)s [options]"
DESCRIPTION = """Get info on a comment, including the upvote/downvote ratio.
"""
EPILOG = """You can include command line arguments from a file by including the
path to the file, prefixed with "@", as an argument (like "@dir/args.txt"). The
file should contain normal command line options, one per line. Ones that take
arguments and the arguments themselves should be on separate lines (e.g. put
"-l" on one line, and "10" on the next). If it is present in the script
directory, it will automatically include arguments from the file "\
"""+CONFIG_FILE+'"'

PERMALINK_PATTERN = r'^(?:https?://)?imgur\.com/gallery/[^/]{5,7}/comment/(\d+)$'
COMMENT_ID_PATTERN = r'^\d+$'

def main():

  parser = argparse.ArgumentParser(description=DESCRIPTION, epilog=EPILOG,
    fromfile_prefix_chars='@')
  parser.set_defaults(**OPT_DEFAULTS)

  parser.add_argument('comment_identifier',
    help="""The comment ID or the URL to the comment (permalink).""")
  parser.add_argument('-C', '--client-id', required=True,
    help="""Imgur API Client-ID to use. Required, if not provided by an @ file
like @default.args.""")
  parser.add_argument('-u', '--user',
    help="""Imgur username. For compatibility only; not required.""")

  new_argv = imgurlib.include_args_from_file(sys.argv, CONFIG_FILE)
  args = parser.parse_args(new_argv)

  headers = {
    'Authorization':'Client-ID '+args.client_id,
    'User-Agent':USER_AGENT,
  }

  match = re.search(PERMALINK_PATTERN, args.comment_identifier)
  if match:
    comment_id = match.group(1)
  else:
    match = re.search(COMMENT_ID_PATTERN, args.comment_identifier)
    if match:
      comment_id = args.comment_identifier
    else:
      fail('Error: Unrecognized comment identifier "'+args.comment_identifier
        +'"')

  if comment_id == '0':
    fail('Error: That\'s the root comment! (It doesn\'t exist.)')

  path = API_PATH+comment_id
  (response, content) = imgurlib.make_request(
    path,
    headers,
    domain=API_DOMAIN
  )

  if response.status != 200:
    fail('Error: HTTP status '+str(response.status))

  #TODO: read number of requests left in quota from response header

  api_response = json.loads(content)
  comment = api_response['data']
  print imgurlib.human_format(comment)


def fail(message):
  sys.stderr.write(message+"\n")
  sys.exit(1)

if __name__ == '__main__':
  main()
