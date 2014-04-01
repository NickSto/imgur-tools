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

  new_argv = include_args_from_file(sys.argv, CONFIG_FILE)
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
  (response, content) = make_request(path, headers)

  if response.status != 200:
    fail('Error: HTTP status '+str(response.status))

  #TODO: read number of requests left in quota from response header

  api_response = json.loads(content)
  comment = api_response['data']
  print format_comment(comment)


def include_args_from_file(argv, default_file, prefix='@'):
  """Edit sys.argv to add "default_file" as an arguments file with the prefix
  character ("@" by default).
  "default_file" should be the base filename, and it should be in the same
  directory as the script itself.
  Returns a a version of sys.argv with the first element removed, ready to be
  given as an argument to argparse.ArgumentParser.parse_args().
  If a prefixed argument is already present, it will make no changes."""
  for arg in argv:
    if arg.startswith(prefix):
      return argv[1:]
  script_dir = os.path.dirname(os.path.realpath(sys.argv[0]))
  default_file_path = os.path.join(script_dir, default_file)
  if not os.path.isfile(default_file_path):
    return argv[1:]
  return [prefix+default_file_path] + argv[1:]


def make_request(path, headers):
  conex = httplib.HTTPSConnection(API_DOMAIN)
  conex.request(
    'GET',
    path,
    None,
    headers
  )
  response = conex.getresponse()
  content = response.read()
  conex.close()
  return (response, content)


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


def format_comment(comment):
  required_keys = ('comment', 'image_id', 'parent_id', 'datetime', 'ups', 'downs')
  for key in required_keys:
    assert key in comment, 'Error: comment does not have required key '+key
  output = ''
  output += comment['comment']+'\n'
  output += "\thttps://imgur.com/gallery/{}/comment/{}\n".format(
    comment['image_id'],
    comment['parent_id'],
  )
  when = str(datetime.datetime.fromtimestamp(comment['datetime']))
  output += "\t{}  {}/{}\n".format(when, comment['ups'], comment['downs'])
  return output


def fail(message):
  sys.stderr.write(message+"\n")
  sys.exit(1)

if __name__ == '__main__':
  main()
