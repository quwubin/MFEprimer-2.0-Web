#!/usr/bin/env python

# quwubin@gmail.com
# 2014-5-7

import json
from get_blog_news import NEWS_FILE


latest_posts = json.load(open(NEWS_FILE))


print [post['title'] for post in latest_posts]
