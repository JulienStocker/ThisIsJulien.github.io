#!/usr/bin/env python3
import feedparser
import logging
from datetime import datetime
import sys
import requests
import re
import json
from bs4 import BeautifulSoup
import time

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
            posts = []
            for entry in feed.entries[:num_posts]:
                post_data = process_entry(entry)
                posts.append(post_data)
            return posts
                
    except Exception as e:
        logging.error(f"Error parsing RSS feed: {str(e)}")
    
    # If RSS feed fails, try to scrape Medium profile
    logging.info(f"RSS feed failed, trying to scrape Medium profile for @{username}")
    
    try:
        profile_url = f'https://medium.com/@{username}'
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        
        # Add some delay to avoid rate limiting
        time.sleep(1)
        
        response = requests.get(profile_url, headers=headers)
        if response.status_code == 200:
            # Parse the page
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract posts
            posts = []
            for article in soup.select('article')[:num_posts]:
                # Extract title 
                title_elem = article.select_one('h2, h3')
                if not title_elem:
                    continue
                    
                title = title_elem.text.strip()
                
                # Extract link
                link_elem = article.select_one('a[href*="/p/"]')
                if not link_elem:
                    continue
                    
                link_path = link_elem['href']
                if link_path.startswith('/'):
                    link = f"https://medium.com{link_path}"
                else:
                    link = link_path
                
                # Extract date (might not be available)
                date_elem = article.select_one('time')
                published = date_elem.text.strip() if date_elem else datetime.now().strftime('%Y-%m-%d')
                
                # Extract image
                image_url = None
                img_elem = article.select_one('img')
                if img_elem and img_elem.get('src'):
                    image_url = img_elem['src']
                
                posts.append({
                    'title': title,
                    'link': link,
                    'published': published,
                    'image_url': image_url
                })
                
            if posts:
                logging.info(f"Successfully scraped {len(posts)} posts from Medium profile")
                return posts
    except Exception as e:
        logging.error(f"Error scraping Medium profile: {str(e)}")
    
    logging.error("All methods to fetch Medium posts failed")
    return []

def generate_markdown(posts):
    """Generate markdown content from the posts"""
    if not posts:
        return None
    
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    markdown = f"# 📝 Latest Blog Posts from Medium\n\n"
    markdown += f"*Last updated: {now}*\n\n"
    
    for post in posts:
        title = post['title']
        link = post['link']
        
        # Format the date
        try:
            # Check if it's already in a readable format (e.g. "May 09, 2025")
            if re.match(r'[A-Z][a-z]{2} \d{1,2}, \d{4}', post['published']):
                date_display = post['published']
            else:
                # Try to parse various date formats
                try:
                    date_obj = datetime.strptime(post['published'], '%a, %d %b %Y %H:%M:%S %Z')
                    date_display = date_obj.strftime('%b %d, %Y')
                except:
                    try:
                        date_obj = datetime.strptime(post['published'], '%Y-%m-%d')
                        date_display = date_obj.strftime('%b %d, %Y')
                    except:
                        date_display = post['published']
        except:
            date_display = post['published']
            
        markdown += f"- [{title}]({link}) ({date_display})\n"
    
    return markdown

def process_entry(entry):
    """Process a single Medium entry and extract necessary information"""
    title = entry.title
    link = entry.link
    published = entry.published
    
    # Extract image from content if available
    image_url = None
    try:
        content = entry.content[0].value if hasattr(entry, 'content') and entry.content else ""
        soup = BeautifulSoup(content, 'html.parser')
        
        # First try to find medium image
        img_tag = soup.find('img')
        if img_tag and img_tag.get('src'):
            image_url = img_tag['src']
            logging.info(f"Found image for post: {title}")
        
        # If no image in content, try to fetch the article and extract the image
        if not image_url and entry.link:
            try:
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
                response = requests.get(entry.link, headers=headers, timeout=10)
                if response.status_code == 200:
                    article_soup = BeautifulSoup(response.text, 'html.parser')
                    # Try to find Medium featured image
                    meta_img = article_soup.find('meta', property='og:image')
                    if meta_img and meta_img.get('content'):
                        image_url = meta_img['content']
                        logging.info(f"Found og:image for post: {title}")
            except Exception as e:
                logging.warning(f"Error fetching article page: {str(e)}")
    except Exception as e:
        logging.warning(f"Error processing entry content: {str(e)}")
    
    return {
        'title': title,
        'link': link,
        'published': published,
        'image_url': image_url
    }

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
        
        # Also save posts as JSON for the blog section
        save_posts_json(entries)
        
    except Exception as e:
        logging.error(f"Error writing to file: {str(e)}")
        sys.exit(1)
        
def save_posts_json(entries):
    """Save posts data to JSON file for blog section"""
    if not entries:
        return False
        
    try:
        with open('medium_posts.json', 'w') as f:
            json.dump(entries, f, indent=2)
        logging.info("Successfully saved posts to medium_posts.json")
        return True
    except Exception as e:
        logging.error(f"Error saving posts JSON: {str(e)}")
        return False

if __name__ == "__main__":
    main()