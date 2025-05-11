#!/usr/bin/env python3
import feedparser
import logging
from datetime import datetime
import sys
import requests
import re
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def fetch_medium_posts(username, num_posts=5):
    """Fetch Medium posts using alternate methods if RSS fails"""
    # First try the RSS feed
    feed_url = f'https://medium.com/feed/@{username}'
    logging.info(f"Trying RSS feed: {feed_url}")
    
    try:
        feed = feedparser.parse(feed_url)
        if not feed.bozo and feed.entries:
            logging.info("Successfully fetched posts from RSS feed")
            return feed.entries[:num_posts]
    except Exception as e:
        logging.error(f"RSS feed error: {str(e)}")
    
    # If RSS fails, try scraping the profile page
    logging.info("RSS feed failed, trying to scrape profile page")
    try:
        profile_url = f'https://medium.com/@{username}'
        response = requests.get(profile_url)
        response.raise_for_status()
        
        # Look for the JSON data in the page
        match = re.search(r'<script>window.__APOLLO_STATE__ = ({.+?});</script>', response.text)
        if not match:
            logging.error("Could not find Apollo state data")
            return None
            
        data = json.loads(match.group(1))
        
        # Extract posts from the Apollo state
        posts = []
        for key, value in data.items():
            if isinstance(value, dict) and value.get('__typename') == 'Post':
                if 'title' in value and 'uniqueSlug' in value:
                    post = {
                        'title': value.get('title'),
                        'link': f"https://medium.com/@{username}/{value.get('uniqueSlug')}",
                        'published': value.get('firstPublishedAt', datetime.now().strftime("%Y-%m-%d"))
                    }
                    posts.append(post)
        
        if posts:
            logging.info(f"Found {len(posts)} posts via scraping")
            return posts[:num_posts]
            
    except Exception as e:
        logging.error(f"Error scraping profile: {str(e)}")
    
    # Final fallback - fetch via Medium's unofficial API
    logging.info("Trying unofficial API")
    try:
        api_url = f'https://api.rss2json.com/v1/api.json?rss_url=https://medium.com/feed/@{username}'
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()
        
        if data.get('status') == 'ok' and 'items' in data:
            logging.info(f"Found {len(data['items'])} posts via API")
            return [
                {
                    'title': item.get('title'),
                    'link': item.get('link'),
                    'published': item.get('pubDate', '')[:10]
                }
                for item in data['items'][:num_posts]
            ]
    except Exception as e:
        logging.error(f"API request error: {str(e)}")
    
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
            title = entry.get('title') if isinstance(entry, dict) else entry.title
            link = entry.get('link') if isinstance(entry, dict) else entry.link
            
            # Handle date based on entry type
            if isinstance(entry, dict):
                published_date = entry.get('published', 'N/A')
                if isinstance(published_date, (int, float)):
                    # Convert timestamp to date string
                    published_date = datetime.fromtimestamp(int(published_date)/1000).strftime('%Y-%m-%d')
            else:
                published_date = entry.published[:10] if hasattr(entry, 'published') else 'N/A'
                
            markdown += f"- [{title}]({link}) ({published_date})\n"
        except Exception as e:
            logging.error(f"Error processing entry: {str(e)}")
            continue
    
    return markdown

def main():
    username = 'stockerjulien'
    output_file = 'medium_posts.md'
    
    logging.info(f"Fetching Medium posts for @{username}...")
    entries = fetch_medium_posts(username)
    
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