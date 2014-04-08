#!/usr/bin/env python
from __future__ import division
import os
import sys
import json
import urllib
import httplib
import datetime

API_DOMAIN = 'api.imgur.com'
USER_AGENT = 'NBS client'

LINK_FORMAT = u'https://imgur.com/gallery/{image_id}/comment/{id}'
HUMAN_FORMAT = u"""{comment}
\thttps://imgur.com/gallery/{image_id}/comment/{parent_id}
\t{when}  +{ups}/-{downs}"""
DETAILS_FORMAT = u"""{comment}
\t{author}
\t{when}  {points} = +{ups} -{downs}
\tthis:   https://imgur.com/gallery/{image_id}/comment/{id}
\tparent: https://imgur.com/gallery/{image_id}/comment/{parent_id}"""

HTTP_MSGS = {
  429:'Exceeded request quota (HTTP status {})'
}
HTTP_MSG_DEFAULT = 'HTTP status {}'


class NearQuotaException(Exception):
  """Raised when an API response header indicates you've almost reached either
  your UserLimit or your ClientLimit."""
  def __init__(self, message=None, limit=None):
    if message:
      Exception.__init__(self, message)
    assert limit in (None, 'user', 'client'), (
      'Error: NearQuotaException.limit must be "user", "client", or None.')
    self.limit = limit


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


def make_request(path, client_id, user_agent=USER_AGENT, params=None,
    headers=None, domain=API_DOMAIN):
  
  if headers is None:
    headers = {
      'Authorization':'Client-ID '+client_id,
      'User-Agent':user_agent,
    }

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
  message = near_quota(response)
  if message:
    raise NearQuotaException(message)

  content = response.read()
  conex.close()
  try:
    api_response = json.loads(content)
  except ValueError:
    sys.stderr.write('JSON parsing error on content:\n'+content[:80]+'\n')
    raise
  json_data = api_response['data']

  return (response, json_data)


def near_quota(response, margin=1):
  """Return a true value if either remaining is within "margin" of the limit,
  false if not.
  If near a quota, the return value will be a str with details.
  If the proper headers cannot be found, returns None."""
  try:
    user_limit = int(response.getheader('X-RateLimit-UserLimit'))
    user_remaining = int(response.getheader('X-RateLimit-UserRemaining'))
    client_limit = int(response.getheader('X-RateLimit-ClientLimit'))
    client_remaining = int(response.getheader('X-RateLimit-ClientRemaining'))
  except (ValueError, TypeError):
    return

  if user_remaining <= margin:
    return "UserRemaining: {}, UserLimit: {}".format(
      user_remaining, user_limit)
  elif client_remaining <= margin:
    return "ClientRemaining: {}, ClientLimit: {}".format(
      client_remaining, client_limit)
  else:
    return False
  


def human_format(comment):
  comment['when'] = unicode(datetime.datetime.fromtimestamp(comment['datetime']))
  return HUMAN_FORMAT.format(**comment)


def details_format(comment):
  comment['when'] = unicode(datetime.datetime.fromtimestamp(comment['datetime']))
  return DETAILS_FORMAT.format(**comment)


def link_format(comment):
  assert 'id' in comment, 'Error: comment does not have the key "id"'
  return LINK_FORMAT.format(**comment)


def handle_status(status, fatal=True):
  if status != 200:
    message_tmpl = HTTP_MSGS.get(status, HTTP_MSG_DEFAULT)
    message = message_tmpl.format(status)
    if fatal:
      fail('Error: '+message)
    else:
      raise httplib.HTTPException(message)


def fail(message):
  sys.stderr.write(str(message)+'\n')
  sys.exit(1)


if __name__ == '__main__':
  test()
