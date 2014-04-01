#!/usr/bin/env python
from __future__ import division
import os
import sys
import json
import httplib
import itertools
import imgurlib

USER_AGENT = 'NBS comment-downloader'
API_DOMAIN = 'api.imgur.com'
API_PATH_TEMPLATE = '/3/account/{}/comments'


def get_comments(user, client_id, cutoff_date=0, limit=0, per_page=100,
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
  chunk_generator = get_comment_chunks(user, client_id, cutoff_date=cutoff_date,
    limit=limit, per_page=per_page, user_agent=user_agent, verbosity=verbosity)
  # Create an iterable from the chunk generator which will join them into a
  # single list. But it evaluates lazily, conserving the number of requests.
  return itertools.chain.from_iterable(chunk_generator)


def get_comment_chunks(user, client_id, cutoff_date=0, limit=0, per_page=100,
    user_agent=USER_AGENT, verbosity=0):
  """Same as get_comments(), but yield lists of comments at a time instead of
  individual ones. (Each list == one page == one request.)"""

  api_path = API_PATH_TEMPLATE.format(user)
  headers = {
    'Authorization':'Client-ID '+client_id,
    'User-Agent':user_agent,
  }
  params = {
    'perPage':str(per_page),
  }

  page_num = 0
  all_comments = []
  still_searching = True
  while still_searching:

    # make request
    params['page'] = str(page_num)
    (response, comments_page) = imgurlib.make_request(
      api_path,
      headers,
      params=params,
      domain=API_DOMAIN
    )
    if response.status != 200:
      raise httplib.HTTPException('HTTP status '+str(response.status))

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
      total = len(all_comments)
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
