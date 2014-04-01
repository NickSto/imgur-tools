imgur-tools
=======

Some quick tools using the Imgur API to do things you can't do yet on the site itself.

The handiest thing is `search-comments.py`, which lets you search the entire comment history of a user (even using regex!). But it doesn't index or cache, so it requests the entire comment history every time. The code is rough, but it gets the job done.

Then, `inspect-comment.py` lets you see things like the exact number of upvotes/downvotes on a comment, and `limit.sh` gives a quick check of your remaining API credits.

Note: To use these, you'll have to register for an API key [here](https://api.imgur.com/#register). Then just put your Client-ID in a config file named "default.args", in the script's directory. It should look like this:
```
--client-id
22a38f978519ba4
```
