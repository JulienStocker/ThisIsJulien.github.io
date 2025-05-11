#!/usr/bin/env python3
import os
import sys
import logging
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Get the correct Python interpreter path
PYTHON_PATH = os.path.join(os.getcwd(), "venv/bin/python")  # Use virtual environment Python

def check_dependencies():
    """Check if all required dependencies are installed"""
    missing_deps = []
    
    try:
        # Check dependencies using the specified Python interpreter
        subprocess.check_call([PYTHON_PATH, "-c", "import feedparser"])
    except (subprocess.CalledProcessError, FileNotFoundError):
        missing_deps.append("feedparser")
    
    try:
        subprocess.check_call([PYTHON_PATH, "-c", "import requests"])
    except (subprocess.CalledProcessError, FileNotFoundError):
        missing_deps.append("requests")
    
    try:
        subprocess.check_call([PYTHON_PATH, "-c", "import bs4"])
    except (subprocess.CalledProcessError, FileNotFoundError):
        missing_deps.append("beautifulsoup4")
    
    if missing_deps:
        logging.error(f"Missing dependencies: {', '.join(missing_deps)}")
        logging.info(f"Install them with: {PYTHON_PATH} -m pip install " + " ".join(missing_deps))
        return False
    
    return True

def run_test():
    """Run the complete Medium integration test"""
    # 1. First check the update-medium.py script
    if not os.path.exists('update-medium.py'):
        logging.error("update-medium.py not found!")
        return False
    
    logging.info("Running update-medium.py to fetch Medium posts...")
    result1 = subprocess.call([PYTHON_PATH, 'update-medium.py'])
    
    if result1 != 0:
        logging.error("Error running update-medium.py")
        return False
    
    if not os.path.exists('medium_posts.md'):
        logging.error("medium_posts.md not created!")
        return False
    
    # 2. Then check the update-blog-section.py script
    if not os.path.exists('update-blog-section.py'):
        logging.error("update-blog-section.py not found!")
        return False
    
    logging.info("Running update-blog-section.py to update the blog section...")
    # Create a backup of index.html first
    if os.path.exists('index.html'):
        subprocess.call(['cp', 'index.html', 'index.html.bak'])
        
    result2 = subprocess.call([PYTHON_PATH, 'update-blog-section.py'])
    
    if result2 != 0:
        logging.error("Error running update-blog-section.py")
        # Restore backup
        if os.path.exists('index.html.bak'):
            subprocess.call(['mv', 'index.html.bak', 'index.html'])
        return False
    
    logging.info("Test completed successfully!")
    logging.info("You can check index.html to see the updated blog section")
    
    # Offer to restore backup
    restore = input("Would you like to restore the original index.html? (y/n): ")
    if restore.lower() == 'y':
        if os.path.exists('index.html.bak'):
            subprocess.call(['mv', 'index.html.bak', 'index.html'])
            logging.info("Original index.html restored")
        else:
            logging.warning("Backup file not found")
    else:
        if os.path.exists('index.html.bak'):
            subprocess.call(['rm', 'index.html.bak'])
        logging.info("Keeping the updated index.html")
    
    return True

if __name__ == "__main__":
    print("="*50)
    print("Medium Blog Integration Test")
    print("="*50)
    
    if not check_dependencies():
        print("\nPlease install the missing dependencies and run the test again.")
        sys.exit(1)
    
    print("\nAll dependencies found. Running test...\n")
    
    if run_test():
        print("\nTest completed successfully!")
        print("If everything looks good, you can commit the changes to GitHub.")
    else:
        print("\nTest failed. Please check the logs for more information.")
        sys.exit(1) 