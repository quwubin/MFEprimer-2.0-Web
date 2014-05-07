#!/home/zhangcg/local/python/bin/python

# quwubin@gmail.com
# 2014-5-7

import pytumblr
import json
import os

LIMIT = 2
src_path = os.path.dirname(os.path.realpath(__file__))
NEWS_FILE = os.path.join(src_path, 'latest_blog_news.json')

def get_news():
    client = pytumblr.TumblrRestClient('V2HTgsoEH2G87TzkbiTnLv3gzZEt6XRHqQ0ATopT6toMyo7kC6')

    latest_posts = [post for post in client.posts('quwubin.tumblr.com', tag='pcr', limit=LIMIT)['posts']]
    with open(NEWS_FILE, 'w') as fh: 
        json.dump(latest_posts, fh)

def main():
    get_news()

if __name__ == '__main__':
    main()
