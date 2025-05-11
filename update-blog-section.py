#!/usr/bin/env python3
import json
import logging
import sys
import os
import re
import random
from datetime import datetime
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def load_medium_posts():
    """Load Medium posts from the markdown file or fetch them directly"""
    try:
        # Check if medium_posts.md exists
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
                    'date': match.group(3)
                })
            return posts
        else:
            logging.warning("medium_posts.md not found")
            # If the file doesn't exist, try running the update-medium.py script
            if os.path.exists('update-medium.py'):
                logging.info("Running update-medium.py to fetch posts")
                os.system('python update-medium.py')
                # Recursive call to load the file that should now exist
                return load_medium_posts()
            return []
    except Exception as e:
        logging.error(f"Error loading Medium posts: {str(e)}")
        return []

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
            
        # Get current posts to avoid duplicates
        current_links = set()
        for post_item in blog_posts_list.select('.blog-post-item a'):
            link = post_item.get('href')
            if link:
                current_links.add(link)
        
        # Prepare blog images
        blog_images = get_blog_images()
        
        # Create new post items for each Medium post that isn't already included
        posts_added = 0
        for post in posts:
            if post['link'] not in current_links:
                # Create a new post item
                new_post = create_blog_post_item(post, blog_images)
                
                # Insert at the beginning of the list to show newest first
                if blog_posts_list.contents:
                    blog_posts_list.insert(0, new_post)
                else:
                    blog_posts_list.append(new_post)
                    
                posts_added += 1
                logging.info(f"Added post: {post['title']}")
                
                # Keep only the latest 8 posts to avoid cluttering
                if len(blog_posts_list.select('.blog-post-item')) > 8:
                    old_posts = blog_posts_list.select('.blog-post-item')
                    for old_post in old_posts[8:]:
                        old_post.extract()
        
        if posts_added == 0:
            logging.info("No new posts to add")
            return False
            
        # Save the updated HTML
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(str(soup))
            
        logging.info(f"Added {posts_added} new posts to {html_file}")
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

def create_blog_post_item(post, blog_images):
    """Create a blog post item element based on the existing structure"""
    # Determine the category based on the post title/content
    category = determine_category(post['title'])
    category_key = category.lower().split()[0]  # Get the first word of category in lowercase
    
    # Select an appropriate image for the post
    image_path = select_blog_image(category_key, blog_images)
    
    # Parse date
    try:
        post_date = datetime.strptime(post['date'], '%Y-%m-%d')
        formatted_date = post_date.strftime('%b %d, %Y')
    except:
        formatted_date = post['date']
    
    # Create new post HTML using BeautifulSoup
    soup = BeautifulSoup('', 'html.parser')
    li = soup.new_tag('li', attrs={'class': 'blog-post-item'})
    li['data-filter-item'] = ""
    li['data-category'] = category.lower()
    
    a = soup.new_tag('a', href=post['link'])
    
    figure = soup.new_tag('figure', attrs={'class': 'blog-banner-box'})
    img = soup.new_tag('img', attrs={
        'src': image_path,
        'alt': f'{category} blog post',
        'loading': 'lazy'
    })
    figure.append(img)
    a.append(figure)
    
    content_div = soup.new_tag('div', attrs={'class': 'blog-content'})
    
    meta_div = soup.new_tag('div', attrs={'class': 'blog-meta'})
    p_category = soup.new_tag('p', attrs={'class': 'blog-category'})
    p_category.string = category
    meta_div.append(p_category)
    
    span_dot = soup.new_tag('span', attrs={'class': 'dot'})
    meta_div.append(span_dot)
    
    time_tag = soup.new_tag('time', datetime=post['date'])
    time_tag.string = formatted_date
    meta_div.append(time_tag)
    
    content_div.append(meta_div)
    
    h3 = soup.new_tag('h3', attrs={'class': 'h3 blog-item-title'})
    h3.string = post['title']
    content_div.append(h3)
    
    # Add excerpt if available (first ~100 chars of blog post)
    p_text = soup.new_tag('p', attrs={'class': 'blog-text'})
    excerpt = generate_excerpt(post['title'])
    p_text.string = excerpt
    content_div.append(p_text)
    
    a.append(content_div)
    li.append(a)
    
    return li

def select_blog_image(category, blog_images):
    """Select an appropriate blog image for the category"""
    # Default image path
    default_image = './assets/images/blog/blog-1.png'
    
    if not blog_images:
        return default_image
    
    # Try to find an image matching the category
    for img_category, images in blog_images.items():
        if category in img_category and images:
            return random.choice(images)
    
    # If no match, use default category if available
    if 'default' in blog_images and blog_images['default']:
        return random.choice(blog_images['default'])
    
    # Fallback to any available image
    for images in blog_images.values():
        if images:
            return random.choice(images)
    
    return default_image

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
    """Determine blog category based on post title"""
    title_lower = title.lower()
    
    # Define keywords for each category
    categories = {
        'Finance': ['finance', 'investing', 'money', 'economy', 'bank', 'fintech', 'crypto', 'blockchain'],
        'Robotics': ['robot', 'robotics', 'automation', 'autonomous', 'ai', 'machine learning'],
        'Environmental Monitoring': ['environment', 'climate', 'monitoring', 'conservation', 'sustainable'],
        'Pattern Recognition': ['pattern', 'recognition', 'computer vision', 'ai', 'machine learning']
    }
    
    # Check title against keywords
    for category, keywords in categories.items():
        if any(keyword in title_lower for keyword in keywords):
            return category
            
    # Default category if no match
    return "Robotics"

def main():
    html_file = 'index.html'
    
    # Load Medium posts
    posts = load_medium_posts()
    if not posts:
        logging.error("No Medium posts found")
        sys.exit(1)
    
    # Update blog section
    success = update_blog_section(html_file, posts)
    if not success:
        logging.warning("Blog section not updated")
        sys.exit(0)
    else:
        logging.info("Blog section updated successfully")

if __name__ == "__main__":
    main()