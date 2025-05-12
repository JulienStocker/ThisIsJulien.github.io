#!/usr/bin/env python3
import json
import logging
import sys
import os
import re
import random
from datetime import datetime
from bs4 import BeautifulSoup
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def load_medium_posts():
    """Load Medium posts from the JSON file or fetch them directly"""
    try:
        # First check if medium_posts.json exists
        if os.path.exists('medium_posts.json'):
            logging.info("Loading Medium posts from medium_posts.json")
            with open('medium_posts.json', 'r') as f:
                return json.load(f)
        
        # If JSON file doesn't exist, try the markdown file
        if os.path.exists('medium_posts.md'):
            logging.info("Loading Medium posts from medium_posts.md")
            with open('medium_posts.md', 'r') as f:
                content = f.read()
                
            # Extract posts using regex
            posts = []
            matches = re.finditer(r'- \[(.*?)\]\((.*?)\) \((.*?)\)', content)
            for match in matches:
                posts.append({
                    'title': match.group(1),
                    'link': match.group(2),
                    'published': match.group(3),
                    'image_url': None,  # No image URL in markdown
                    'local_image': None
                })
            return posts
        else:
            logging.warning("medium_posts.md not found")
            # If the file doesn't exist, try running the update-medium.py script
            if os.path.exists('update-medium.py'):
                logging.info("Running update-medium.py to fetch posts")
                os.system('python3 update-medium.py')
                # Recursive call to load the file that should now exist
                return load_medium_posts()
            return []
    except Exception as e:
        logging.error(f"Error loading Medium posts: {str(e)}")
        return []

def download_image(image_url, post_title):
    """Download image from URL and save to local directory"""
    if not image_url:
        return None
        
    try:
        # Create images directory if it doesn't exist
        os.makedirs('assets/images/blog', exist_ok=True)
        
        # Generate safe filename from post title
        safe_title = "".join([c if c.isalnum() else "_" for c in post_title]).lower()
        safe_title = re.sub(r'_+', '_', safe_title)  # Replace multiple underscores with a single one
        
        # Get file extension from URL or default to .jpg
        file_ext = os.path.splitext(image_url)[1]
        if not file_ext or len(file_ext) > 5:
            file_ext = '.jpg'
            
        # Create filename
        filename = f"medium_{safe_title}{file_ext}"
        filepath = os.path.join('assets/images/blog', filename)
        
        # Check if file already exists
        if os.path.exists(filepath):
            logging.info(f"Image already exists: {filepath}")
            return filepath
        
        # Download the image
        response = requests.get(image_url, stream=True)
        response.raise_for_status()
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                
        logging.info(f"Downloaded image to: {filepath}")
        return filepath
        
    except Exception as e:
        logging.error(f"Error downloading image: {str(e)}")
        return None

def update_blog_section(html_file, posts):
    """Update the blog section in the HTML file with Medium posts"""
    if not posts:
        logging.warning("No posts to update")
        return False
        
    try:
        # Read the HTML file
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find the blog posts list
        blog_posts_list = soup.select_one('.blog-posts-list')
        if not blog_posts_list:
            logging.error("Blog posts list not found in HTML")
            return False
            
        # Check for existing posts
        existing_posts = []
        medium_links = {post['link'] for post in posts}
        
        # Clear all existing blog posts and replace with only Medium posts
        blog_posts_list.clear()
        logging.info("Cleared all existing blog posts")
            
        # Create new post items for each Medium post
        posts_added = 0
        for post in posts:
            # Create a new post item
            new_post = create_blog_post_item(post)
            
            # Add to the blog posts list
            blog_posts_list.append(new_post)
                
            posts_added += 1
            logging.info(f"Added post: {post['title']}")
        
        # Save the updated HTML
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(str(soup))
            
        logging.info(f"Added {posts_added} Medium posts to index.html")
        logging.info("Blog section updated successfully")
        return True
        
    except Exception as e:
        logging.error(f"Error updating blog section: {str(e)}")
        return False

def get_blog_images():
    """Get available blog images from assets folder"""
    blog_images = {}
    
    # Define the path to the blog images folder
    blog_images_path = 'assets/images/blog'
    
    if os.path.exists(blog_images_path):
        logging.info(f"Found blog images folder: {blog_images_path}")
        # Group images by category
        for filename in os.listdir(blog_images_path):
            if filename.endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif')):
                image_path = os.path.join(blog_images_path, filename)
                lowercase_filename = filename.lower()
                
                # Map categories to image files
                for category in ['finance', 'robotics', 'environmental', 'pattern']:
                    if category in lowercase_filename:
                        if category not in blog_images:
                            blog_images[category] = []
                        blog_images[category].append(image_path)
                
                # Add to default category if not categorized
                if 'default' not in blog_images:
                    blog_images['default'] = []
                blog_images['default'].append(image_path)
    else:
        logging.warning(f"Blog images folder not found: {blog_images_path}")
    
    categories = blog_images.keys()
    if categories:
        logging.info(f"Found blog images for categories: {', '.join(categories)}")
    else:
        logging.warning("No blog images found")
    
    return blog_images

def create_blog_post_item(post):
    """Create a blog post item element based on the existing structure"""
    # Determine the category based on the post title/content
    category = determine_category_with_content(post)
    
    # Select an appropriate image for the post
    image_path = select_image_for_post(post, category)
    
    # Parse date
    try:
        # Try to parse if it's not already in the desired format
        if not re.match(r'[A-Z][a-z]{2} \d{1,2}, \d{4}', post['published']):
            post_date = datetime.strptime(post['published'], '%a, %d %b %Y %H:%M:%S %Z')
            formatted_date = post_date.strftime('%b %d, %Y')
        else:
            formatted_date = post['published']
    except:
        formatted_date = post['published']
    
    # Create new post HTML using BeautifulSoup
    soup = BeautifulSoup('', 'html.parser')
    
    # Create the li element
    li = soup.new_tag('li', attrs={'class': 'blog-post-item', 'data-category': category.lower(), 'data-filter-item': ''})
    
    # Create the anchor element
    a = soup.new_tag('a', href=post['link'])
    
    # Create the figure element
    figure = soup.new_tag('figure', attrs={'class': 'blog-banner-box'})
    img = soup.new_tag('img', attrs={
        'src': image_path,
        'alt': f"{category} blog post",
        'loading': 'lazy'
    })
    figure.append(img)
    a.append(figure)
    
    # Create the content div
    content_div = soup.new_tag('div', attrs={'class': 'blog-content'})
    
    # Add the title
    title = soup.new_tag('h3', attrs={'class': 'h3 blog-item-title'})
    title.string = post['title']
    content_div.append(title)
    
    # Add the meta div
    meta_div = soup.new_tag('div', attrs={'class': 'blog-meta'})
    
    # Add the category
    category_p = soup.new_tag('p', attrs={'class': 'blog-category'})
    category_p.string = category
    meta_div.append(category_p)
    
    # Add the dot separator
    span_dot = soup.new_tag('span', attrs={'class': 'dot'})
    meta_div.append(span_dot)
    
    # Add the date
    time_tag = soup.new_tag('time', datetime=formatted_date)
    time_tag.string = formatted_date
    meta_div.append(time_tag)
    
    content_div.append(meta_div)
    
    # Add the excerpt
    excerpt = soup.new_tag('p', attrs={'class': 'blog-text'})
    excerpt.string = generate_excerpt(post['title'])
    content_div.append(excerpt)
    
    a.append(content_div)
    li.append(a)
    
    return li

def select_image_for_post(post, category):
    """Select an appropriate image for the post"""
    # First check if the post has its own downloaded Medium image
    if post.get('local_image') and os.path.exists(post['local_image']):
        logging.info(f"Using existing local image for post: {post['title']}")
        return post['local_image']
        
    # If no local image but has image_url, download it
    if post.get('image_url'):
        local_image = download_image(post['image_url'], post['title'])
        if local_image:
            post['local_image'] = local_image
            logging.info(f"Downloaded and using Medium image for: {post['title']}")
            return local_image
    
    # Then look for category-specific images
    category_key = category.lower().split()[0]  # Get first word of category
    
    # Check if blog images folder exists
    blog_images_path = 'assets/images/blog'
    if os.path.exists(blog_images_path):
        logging.info(f"Found blog images folder: {blog_images_path}")
        
        # Try to find a category-specific image
        category_images = []
        for filename in os.listdir(blog_images_path):
            if filename.lower().startswith(category_key) and filename.endswith(('.jpg', '.jpeg', '.png', '.webp')):
                category_images.append(filename)
        
        if category_images:
            logging.info(f"Found blog images for categories: {category_key}")
            image_path = os.path.join(blog_images_path, random.choice(category_images))
            return image_path
        
        # If no category-specific image found, use a relevant image based on context
        if category == 'Finance':
            candidates = [f for f in os.listdir(blog_images_path) if 'blog-1' in f.lower()]
            if candidates:
                return os.path.join(blog_images_path, candidates[0])
        elif category == 'Robotics':
            candidates = [f for f in os.listdir(blog_images_path) if 'blog-2' in f.lower()]
            if candidates:
                return os.path.join(blog_images_path, candidates[0])
        elif category.startswith('Environmental'):
            candidates = [f for f in os.listdir(blog_images_path) if 'agro' in f.lower() or 'menace' in f.lower()]
            if candidates:
                return os.path.join(blog_images_path, random.choice(candidates))
        
        # Fallback to any image
        image_files = [f for f in os.listdir(blog_images_path) 
                     if f.endswith(('.jpg', '.jpeg', '.png', '.webp')) 
                     and not f.startswith('image-coming-soon')]
        if image_files:
            logging.info(f"Found blog images for categories: default")
            return os.path.join(blog_images_path, random.choice(image_files))
    
    # Ultimate fallback - use image-coming-soon.png or a default path
    if os.path.exists(os.path.join(blog_images_path, 'image-coming-soon.png')):
        return os.path.join(blog_images_path, 'image-coming-soon.png')
    
    return './assets/images/blog/image-coming-soon.png'

def generate_excerpt(title):
    """Generate a sensible excerpt based on the post title"""
    # Common phrases based on the type of content
    robotics_phrases = [
        "Exploring the latest advancements in robotics and automation technologies.",
        "A deep dive into robotic systems and their applications in modern industries.",
        "Discussing key innovations and challenges in the field of robotics.",
    ]
    
    finance_phrases = [
        "Analysis of current financial trends and their implications for investors.",
        "Exploring economic principles and their real-world applications.",
        "Insights into financial markets and investment strategies.",
    ]
    
    environmental_phrases = [
        "Examining environmental challenges and innovative solutions for sustainability.",
        "Analysis of conservation efforts and their impact on ecosystems.",
        "Exploring the intersection of technology and environmental monitoring.",
    ]
    
    pattern_phrases = [
        "Investigating pattern recognition algorithms and their applications.",
        "Exploring computer vision techniques and machine learning models.",
        "Analysis of data patterns and their significance in decision-making processes.",
    ]
    
    # Default phrases
    default_phrases = [
        "An in-depth exploration of concepts and innovations in this field.",
        "Sharing insights and analysis on this important topic.",
        "A comprehensive look at the latest developments and future directions.",
    ]
    
    # Select appropriate phrases based on title
    title_lower = title.lower()
    if any(keyword in title_lower for keyword in ['robot', 'automation', 'ai']):
        return random.choice(robotics_phrases)
    elif any(keyword in title_lower for keyword in ['finance', 'economy', 'market']):
        return random.choice(finance_phrases)
    elif any(keyword in title_lower for keyword in ['environment', 'sustain', 'climate']):
        return random.choice(environmental_phrases)
    elif any(keyword in title_lower for keyword in ['pattern', 'recognition', 'vision']):
        return random.choice(pattern_phrases)
    else:
        return random.choice(default_phrases)

def determine_category(title):
    """Determine blog category based on post title and content"""
    title_lower = title.lower()
    
    # Define keywords for each category
    categories = {
        'Finance': ['finance', 'investing', 'money', 'economy', 'bank', 'fintech', 'crypto', 'blockchain', 
                   'metals', 'company', 'stock', 'market', 'financial', 'investment', 'fund', 'trading', 
                   'economic', 'fiscal', 'monetary', 'dividend', 'portfolio', 'asset'],
        
        'Robotics': ['robot', 'robotics', 'automation', 'autonomous', 'ai', 'machine learning', 
                    'artificial intelligence', 'drone', 'self-driving', 'ros', 'sensor', 'actuator', 
                    'mechatronics', 'control system', 'navigation', 'slam', 'robotic day'],
        
        'Environmental Monitoring': ['environment', 'climate', 'monitoring', 'conservation', 'sustainable', 
                                    'green', 'eco', 'nature', 'wildlife', 'biodiversity', 'pollution', 
                                    'recycling', 'renewable', 'sustainability', 'carbon', 'emission', 
                                    'lake', 'ocean', 'water', 'forest', 'ecosystem', 'menace', 'threat', 'swan'],
        
        'Pattern Recognition': ['pattern', 'recognition', 'computer vision', 'ai', 'machine learning', 
                               'neural network', 'deep learning', 'image processing', 'classification', 
                               'detection', 'clustering', 'feature extraction']
    }
    
    # Check for strong category indicators first (more specific matches)
    strong_indicators = {
        'Finance': ['metals company', 'stock', 'market crash', 'investment', 'financial'],
        'Environmental Monitoring': ['swiss lakes', 'lake', 'environment', 'climate change', 'conservation', 'black swan'],
        'Robotics': ['robotic day', 'robot', 'autonomous', 'robotics'],
        'Pattern Recognition': ['neural network', 'computer vision', 'image recognition']
    }
    
    # Check for strong indicators first
    for category, indicators in strong_indicators.items():
        for indicator in indicators:
            if indicator in title_lower:
                logging.info(f"Strong match found: '{indicator}' in '{title}' -> {category}")
                return category
    
    # Count keyword matches for each category
    match_counts = {category: 0 for category in categories}
    
    for category, keywords in categories.items():
        for keyword in keywords:
            if keyword in title_lower:
                match_counts[category] += 1
                logging.info(f"Keyword match: '{keyword}' in '{title}' -> {category}")
    
    # Get the category with the most keyword matches
    if any(match_counts.values()):
        best_category = max(match_counts.items(), key=lambda x: x[1])[0]
        if match_counts[best_category] > 0:
            logging.info(f"Category determined by keyword count: '{title}' -> {best_category}")
            return best_category
    
    # Special case handling based on content analysis
    if 'metals company' in title_lower or 'metal' in title_lower:
        logging.info(f"Special case for metals company: '{title}' -> Finance")
        return 'Finance'
        
    if 'lake' in title_lower or 'swan' in title_lower or 'environment' in title_lower:
        logging.info(f"Special case for environmental terms: '{title}' -> Environmental Monitoring")
        return 'Environmental Monitoring'
    
    # Default category is still Robotics, but with a warning
    logging.warning(f"No category match found for: '{title}', defaulting to Robotics")
    return "Robotics"

def fetch_article_content(url):
    """Fetch the content of a Medium article for better categorization"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, timeout=10, headers=headers)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try to get the article content
            article_content = ""
            
            # Get all paragraphs in the article
            paragraphs = soup.select('article p')
            if paragraphs:
                article_content = " ".join([p.get_text() for p in paragraphs])
            
            # If no paragraphs found, try another common selector
            if not article_content:
                article_sections = soup.select('section')
                if article_sections:
                    paragraphs = []
                    for section in article_sections:
                        paragraphs.extend(section.select('p'))
                    article_content = " ".join([p.get_text() for p in paragraphs])
            
            return article_content.lower()
        
        return ""
    except Exception as e:
        logging.warning(f"Error fetching article content: {str(e)}")
        return ""

def determine_category_with_content(post):
    """Determine blog category based on both post title and content if available"""
    title = post['title']
    
    # First try to categorize based on title alone
    category_from_title = determine_category(title)
    
    # If we got a category other than the default, return it
    if category_from_title != "Robotics":
        return category_from_title
    
    # Otherwise, try to fetch and analyze the article content
    if 'link' in post:
        logging.info(f"Fetching article content for better classification: {title}")
        content = fetch_article_content(post['link'])
        
        if content:
            # Define content keywords for categories
            content_categories = {
                'Finance': ['financial', 'investment', 'stock', 'market', 'economy', 'economic', 
                           'trading', 'fund', 'portfolio', 'asset', 'metals', 'mining', 'capital',
                           'revenue', 'profit', 'dividend', 'shareholder', 'nasdaq', 'nyse'],
                
                'Environmental Monitoring': ['environment', 'ecosystem', 'conservation', 'climate', 
                                           'sustainable', 'pollution', 'biodiversity', 'renewable', 
                                           'lake', 'ocean', 'forest', 'emissions', 'carbon', 'green', 
                                           'nature', 'wildlife', 'ecological', 'water quality'],
                
                'Pattern Recognition': ['pattern', 'recognition', 'machine learning', 'algorithm', 
                                      'neural network', 'classification', 'feature extraction', 
                                      'clustering', 'computer vision', 'image processing']
            }
            
            # Count keyword occurrences in content
            content_scores = {category: 0 for category in content_categories}
            
            for category, keywords in content_categories.items():
                for keyword in keywords:
                    if keyword in content:
                        # Count occurrences
                        occurrences = content.count(keyword)
                        content_scores[category] += occurrences
                        if occurrences > 0:
                            logging.info(f"Content match: '{keyword}' ({occurrences} times) in article -> {category}")
            
            # If we have significant matches in content
            if any(score > 3 for score in content_scores.values()):
                best_category = max(content_scores.items(), key=lambda x: x[1])[0]
                if content_scores[best_category] > 3:
                    logging.info(f"Category determined by content analysis: '{title}' -> {best_category}")
                    return best_category
    
    # If we couldn't determine a category from content, return the title-based one
    return category_from_title

def main():
    # Set the HTML file to update
    html_file = 'index.html'
    
    # Load Medium posts
    posts = load_medium_posts()
    
    if not posts:
        logging.error("No Medium posts found")
        sys.exit(1)
        
    # Update the blog section
    success = update_blog_section(html_file, posts)
    
    if success:
        logging.info("Blog section updated successfully")
    else:
        logging.warning("Blog section not updated")
        
if __name__ == "__main__":
    main()