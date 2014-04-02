#!/usr/bin/env python
from __future__ import division
import re
import os
import sys
import argparse
import imgurlib

USER_AGENT = 'NBS comment-inspector'
CONFIG_FILE = 'default.args'  # must be in same directory as script
API_DOMAIN = 'api.imgur.com'
API_PATH = '/3/comment/'

OPT_DEFAULTS = {}
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
    help='The comment ID or the URL to the comment (permalink).')
  parser.add_argument('-C', '--client-id', required=True,
    help='Imgur API Client-ID to use. Required, if not provided by an @ file '
      'like @default.args.')
  parser.add_argument('-u', '--user',
    help='Imgur username. For compatibility only; not required.')
  parser.add_argument('-r', '--recursive', action='store_true',
    help='Show the comment, then show its parent, etc, all the way up the '
      'thread.')

  new_argv = imgurlib.include_args_from_file(sys.argv, CONFIG_FILE)
  args = parser.parse_args(new_argv)

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
    fail('Error: That\'s the root comment! (The comment you gave is not a '
      'reply.)')

  while comment_id != '0':

    path = API_PATH+comment_id
    (response, comment) = imgurlib.make_request(
      path,
      args.client_id,
      user_agent=USER_AGENT,
      domain=API_DOMAIN
    )
    if response.status != 200:
      fail('Error: HTTP status '+str(response.status))

    print imgurlib.details_format(comment)

    if args.recursive:
      comment_id = str(comment['parent_id'])
    else:
      break


def fail(message):
  sys.stderr.write(message+"\n")
  sys.exit(1)

if __name__ == '__main__':
  main()
