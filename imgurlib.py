#!/usr/bin/env python
from __future__ import division
import os
import sys
import json
import urllib
import httplib
import datetime

API_DOMAIN = 'api.imgur.com'
PERMALINK_TEMPLATE = u'https://imgur.com/gallery/{}/comment/{}'


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


def make_request(path, headers, params=None, domain=API_DOMAIN):
  if params is None:
    path_and_params = path
  else:
    path_and_params = path+'?'+urllib.urlencode(params)

  conex = httplib.HTTPSConnection(domain)
  conex.request(
    'GET',
    path_and_params,
    None,
    headers
  )
  
  response = conex.getresponse()
  content = response.read()
  conex.close()

  api_response = json.loads(content)
  json_data = api_response['data']

  return (response, json_data)


def human_format(comment):
  required_keys = ('comment', 'image_id', 'parent_id', 'datetime', 'ups', 'downs')
  for key in required_keys:
    assert key in comment, 'Error: comment does not have required key '+key
  output = u''
  output += comment['comment']+u'\n'
  output += u"\thttps://imgur.com/gallery/{}/comment/{}\n".format(
    comment['image_id'],
    comment['parent_id'],
  )
  when = unicode(datetime.datetime.fromtimestamp(comment['datetime']))
  output += u"\t{}  {}/{}".format(when, comment['ups'], comment['downs'])
  return output


def link_format(comment):
  assert 'id' in comment, 'Error: comment does not have the key "id"'
  return PERMALINK_TEMPLATE.format(comment['image_id'], comment['id'])


if __name__ == '__main__':
  test()
