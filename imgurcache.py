#!/usr/bin/env python
#TODO: Right now it's updating the cache BEFORE it returns any comments. So if
#      there's no cache, it makes ALL the requests before returning any results.
#      Need to figure out how to make it return results, THEN update the cache.
#      Looks like I can have get_live_comment_chunks() itself do it, after the
#      loop containing the yields.
from __future__ import division
import os
import sys
import json
import httplib
import itertools
import imgurlib

USER_AGENT = 'NBS comment-downloader'
API_DOMAIN = 'api.imgur.com'
COMMENTS_PATH = '/3/account/{}/comments'
ACCOUNT_PATH = '/3/account/{}'
CACHE_DIRNAME = 'cache'


def get_live_comments(user, client_id, cutoff_date=0, limit=0, per_page=100,
    user_agent=USER_AGENT, verbosity=0):
  """Yield all comments for "user", up to a specified limit or date.
  "limit" (int) is the maximum number of comments which will be returned.
  "cutoff_date" (int) is a unix timestamp. Only comments this old or newer will
    be returned.
  If neither limit is given, all comments will be returned. If both are given,
  comments will be returned until either limit is reached.
  Will return a generator that yields one comment at a time, only making
  another request when it has yielded all the comments from the previous one.
  The number of requests made depends on the number of comments returned (duh),
  and the value of "per_page", which is the number of comments returned per
  request. Can be any int > 0, but it is ultimately limited by the Imgur API,
  which limits a request to 100 at maximum."""
  generator = get_live_comment_chunks(user, client_id, cutoff_date=cutoff_date,
    limit=limit, per_page=per_page, user_agent=user_agent, verbosity=verbosity)
  # Create an iterable from the chunk generator which will join them into a
  # single list. But it evaluates lazily, conserving the number of requests.
  return itertools.chain.from_iterable(generator)


def get_live_comment_chunks(user, client_id, cutoff_date=0, limit=0,
    per_page=100, user_agent=USER_AGENT, verbosity=0):
  """Same as get_comments(), but yield lists of comments at a time instead of
  individual ones. (Each list == one page == one request.)"""

  api_path = COMMENTS_PATH.format(user)
  params = {
    'perPage':str(per_page),
  }

  total = 0
  page_num = 0
  still_searching = True
  while still_searching:

    # make request
    params['page'] = str(page_num)
    (response, comments_page) = imgurlib.make_request(
      api_path,
      client_id,
      user_agent=user_agent,
      params=params,
      domain=API_DOMAIN
    )
    imgurlib.handle_status(response.status, fatal=False)

    assert is_iterable(comments_page), ('Error: Expected comments to be an '
      'iterable.')
    if len(comments_page) == 0:
      still_searching = False
      if verbosity >= 2:
        sys.stderr.write('Reached end of comments. All were retrieved.\n')

    if limit == 0 and cutoff_date == 0:
      comments_group = comments_page
    else:
      comments_group = []
      for comment in comments_page:
        total+=1
        # Exceeded limit? Discard comment.
        if comment['datetime'] < cutoff_date or (limit and total > limit):
          still_searching = False
          if verbosity >= 1:
            sys.stderr.write('Found more comments than the limit.\n')
          break
        else:
          comments_group.append(comment)

    page_num+=1
    if len(comments_group) == 0:
      raise StopIteration
    else:
      yield comments_group

    #TODO: Update cache here.
    #      Have to retrieve the comments already in the cache in order to
    #      combine with the live comments. But get_cached_and_live_comments(),
    #      which calls this, already does that. So hopefully avoid doing it
    #      twice. I may have to bite the bullet and make this optionally
    #      take on the function of get_cached_and_live_comments().


def is_iterable(obj):
  try:
    iter(obj)
  except TypeError:
    return False
  return True


def get_cached_and_live_comments(user, client_id, update_cache=True,
    user_agent=USER_AGENT, verbosity=0):
  """Yield all comments for "user", drawing on cache files and updates via the
  API on the backend.
  Returns a generator that yields one comment at a time, starting with the
  newest."""
  account_id = username_to_id(user, client_id, user_agent=user_agent)
  cached_comments = get_cached_comments(account_id)
  if len(cached_comments) == 0:
    cutoff_date = 0
  else:
    cutoff_date = cached_comments[0]['datetime'] + 1
  live_comments = get_live_comments(user, client_id, cutoff_date=cutoff_date,
    user_agent=USER_AGENT, verbosity=0)
  
  combined_comments = itertools.chain(live_comments, cached_comments)

  # overwrite cache with all live + cached comments
  if update_cache:
    cache_file = get_cache_filename(account_id)
    cache_dir = os.path.dirname(cache_file)
    if not os.path.exists(cache_dir):
      os.makedirs(cache_dir)
    combined_comments_list = list(combined_comments)
    with open(cache_file, 'w') as filehandle:
      json.dump(combined_comments_list, filehandle)
    # have to return a generator, not a list
    return (comment for comment in combined_comments_list)
  else:
    return combined_comments


def get_cached_comments(account_id, cache_dir=None):
  """Return cached comments for "account_id", if any exist on disk.
  This will look for a file named "account_id.json" in "cache_dir". If one is
  found, all comments in it will be returned in a list. Otherwise, an empty list
  is returned. If "cache_dir" is not given, it will use a directory named
  "cache" in the script directory."""
  cache_file = get_cache_filename(account_id, cache_dir=cache_dir)
  if os.path.isfile(cache_file):
    with open(cache_file) as filehandle:
      return json.load(filehandle)
  else:
    return []


def get_cache_filename(account_id, cache_dir=None):
  if cache_dir is None:
    if sys.argv[0] == '':
      script_dir = os.path.realpath(sys.argv[0])
    else:
      script_dir = os.path.dirname(os.path.realpath(sys.argv[0]))
    cache_dir = os.path.join(script_dir, CACHE_DIRNAME)
  return os.path.join(cache_dir, account_id+'.json')


def username_to_id(user, client_id, user_agent=USER_AGENT):
  api_path = ACCOUNT_PATH.format(user)
  (response, account_data) = imgurlib.make_request(
    api_path,
    client_id,
    user_agent=user_agent,
    domain=API_DOMAIN
  )
  imgurlib.handle_status(response.status, fatal=False)
  return str(account_data['id'])


def fail(message):
  sys.stderr.write(message+"\n")
  sys.exit(1)
