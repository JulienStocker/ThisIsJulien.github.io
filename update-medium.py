#!/usr/bin/env python3
import feedparser
import logging
from datetime import datetime
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def fetch_medium_posts(feed_url, num_posts=5):
    try:
        feed = feedparser.parse(feed_url)
        if feed.bozo:  # Check for feed parsing errors
            logging.error(f"Feed parsing error: {feed.bozo_exception}")
            return None
        return feed.entries[:num_posts]
    except Exception as e:
        logging.error(f"Error fetching feed: {str(e)}")
        return None

def generate_markdown(entries):
    if not entries:
        return None
    
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    markdown = f"""# 📝 Latest Blog Posts from Medium

*Last updated: {current_time}*

"""
    
    for entry in entries:
        try:
            published_date = entry.published[:10] if hasattr(entry, 'published') else 'N/A'
            markdown += f"- [{entry.title}]({entry.link}) ({published_date})\n"
        except AttributeError as e:
            logging.error(f"Error processing entry: {str(e)}")
            continue
    
    return markdown

def main():
    feed_url = 'https://medium.com/feed/@julienstocker'
    output_file = 'medium_posts.md'
    
    logging.info("Fetching Medium posts...")
    entries = fetch_medium_posts(feed_url)
    
    if not entries:
        logging.error("No entries found or error occurred")
        sys.exit(1)
    
    markdown_content = generate_markdown(entries)
    if not markdown_content:
        logging.error("Failed to generate markdown content")
        sys.exit(1)
    
    try:
        with open(output_file, 'w') as f:
            f.write(markdown_content)
        logging.info(f"Successfully updated {output_file}")
    except Exception as e:
        logging.error(f"Error writing to file: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()