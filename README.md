# ThisIsChris.github.io - Personal Website

This repository contains the source code for my personal website, including a blog section that automatically synchronizes with my Medium articles.

## Medium Integration

### How to Update the Website with New Medium Articles

#### Automatic Update (Recommended)
New Medium articles are automatically fetched and displayed on the website through a GitHub Actions workflow:

1. The workflow runs daily at midnight UTC
2. It fetches the latest posts from your Medium profile (`@stockerjulien`)
3. Downloads the original featured images
4. Categorizes articles based on content
5. Updates the blog section in the website

No manual intervention is required - just publish articles on Medium and they will appear on your website within 24 hours.

#### Manual Update
If you need to update the blog section immediately after publishing a new Medium article:

1. Clone this repository to your local machine
2. Ensure you have Python 3 installed
3. Set up a virtual environment (if it doesn't exist):
   ```
   python3 -m venv venv
   ```
4. Activate the virtual environment:
   - On macOS/Linux: `source venv/bin/activate`
   - On Windows: `venv\Scripts\activate`
5. Install required packages:
   ```
   pip install feedparser requests beautifulsoup4
   ```
6. Run the update scripts:
   ```
   python3 update-medium.py
   python3 update-blog-section.py
   ```
7. Commit and push the changes:
   ```
   git add .
   git commit -m "Update blog with latest Medium articles"
   git push
   ```

### How It Works

1. **update-medium.py**: 
   - Fetches your latest Medium posts via RSS feed
   - Extracts post information (title, link, date, image)
   - Saves the data to `medium_posts.md` and `medium_posts.json`

2. **update-blog-section.py**:
   - Loads the Medium posts data
   - Downloads the original images from Medium
   - Categorizes posts (Finance, Robotics, Environmental Monitoring)
   - Updates the blog section in index.html

### Customization

To modify how posts are categorized, edit the `determine_category` function in `update-blog-section.py`. 