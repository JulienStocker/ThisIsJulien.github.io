# update_medium.py
import feedparser

feed_url = 'https://medium.com/feed/@julienstocker'  # Replace with your Medium handle
feed = feedparser.parse(feed_url)

with open('medium_posts.md', 'w') as f:
    f.write("# 📝 Latest Blog Posts from Medium\n\n")
    for entry in feed.entries[:5]:  # Adjust the number of posts as you want
        f.write(f"- [{entry.title}]({entry.link}) ({entry.published[:10]})\n")