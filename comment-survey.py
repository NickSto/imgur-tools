#!/usr/bin/env python
from __future__ import division
import re
import os
import sys
import random
import argparse
import imgurlib

CONFIG_FILE = 'default.args'  # must be in same directory as script
RANDOM_PATH = '/3/gallery/random/random'
COMMENTS_PATH = '/3/gallery/{}/comments/new'
COMMENT_COUNT_PATH = '/3/account/{}/comments/count'

OPT_DEFAULTS = {'per_image':2}
USAGE = "%(prog)s [options]"
DESCRIPTION = """Get a random-ish sample of users and the number of comments
they've made. 2-column output: username and number of comments."""
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

  parser.add_argument('-n', '--per-image', type=int,
    help='Comments per image.')
  parser.add_argument('-C', '--client-id', required=True,
    help='Imgur API Client-ID to use. Required, if not provided by an @ file '
      'like @default.args.')
  parser.add_argument('-u', '--user',
    help='Imgur username. For compatibility only; not required.')

  new_argv = imgurlib.include_args_from_file(sys.argv, CONFIG_FILE)
  args = parser.parse_args(new_argv)

  # get random set of images
  (response, images) = imgurlib.make_request(RANDOM_PATH, args.client_id)
  imgurlib.handle_status(response.status)

  for image in images:
    # get comments per image
    path = COMMENTS_PATH.format(image['id'])
    (response, comments) = imgurlib.make_request(path, args.client_id)
    imgurlib.handle_status(response.status)

    if args.per_image > len(comments):
      comment_sample_size = len(comments)
    else:
      comment_sample_size = args.per_image

    for comment in random.sample(comments, comment_sample_size):
      username = comment['author']
      if username == '[deleted]':
        sys.stderr.write('Deleted username. Skipping.\n')
        continue
      # get number of comments per user
      path = COMMENT_COUNT_PATH.format(username)
      (response, count) = imgurlib.make_request(path, args.client_id)
      imgurlib.handle_status(response.status)
      if not isinstance(count, int):
        sys.stderr.write('Non-integer count: '+str(count)[:70]+'\n')
        continue
      print "{}\t{}".format(username, count)


def fail(message):
  sys.stderr.write(message+"\n")
  sys.exit(1)

if __name__ == '__main__':
  main()
