import requests
from bs4 import BeautifulSoup
import sys
import csv
from datetime import datetime
import os
from urllib.parse import urljoin

DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Referer': 'https://www.google.com/', # Some sites check this
    'DNT': '1', # Do Not Track Request Header
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

def crawl_blog(url):
    """
    Crawls the given URL, extracts article titles and links.
    Returns a list of dictionaries, each with a 'title' and 'link'.
    """
    results = []
    try:
        response = requests.get(url, headers=DEFAULT_HEADERS, timeout=10)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
    except requests.exceptions.RequestException as e:
        results.append({'title': f"Error fetching {url}: {e}", 'link': ''})
        return results

    soup = BeautifulSoup(response.text, 'html.parser')
    
    extracted_count = 0
    
    # Attempt 1: Look for <article> tags
    articles = soup.find_all('article')
    for article in articles:
        link_tag = article.find('a')
        title_tag = article.find(['h1', 'h2', 'h3', 'h4'])
        
        if link_tag and title_tag:
            title = title_tag.get_text(strip=True)
            link = link_tag.get('href')
            if link and title:
                full_link = urljoin(url, link)
                results.append({'title': title, 'link': full_link})
                extracted_count += 1
                if extracted_count >= 20:
                    break
    
    # Attempt 2: If no <article> tags, look for prominent links
    if extracted_count == 0:
        for link_tag in soup.find_all('a'):
            if extracted_count >= 20:
                break
                
            href = link_tag.get('href')
            text = link_tag.get_text(strip=True)
            
            if href and text and len(text) > 10 and (href.startswith('http') or href.startswith('/')):
                if not any(nav_keyword in text.lower() for nav_keyword in ['home', 'about', 'contact', 'privacy', 'terms', 'subscribe']):
                    full_href = urljoin(url, href)
                    results.append({'title': text, 'link': full_href})
                    extracted_count += 1

    if not results:
        no_articles_message = """No articles found with generic detection. Please inspect the target website's HTML to refine selectors.
To do this:
1. Open the target website in your web browser.
2. Right-click on an article title and select 'Inspect' or 'Inspect Element'.
3. In the developer tools, identify the HTML tags and classes that uniquely identify article titles and their links.
4. Modify the `crawler.py` script to use these specific tags and classes with `soup.find()` or `soup.find_all()` methods.
   Example: `soup.find_all('div', class_='article-card')` or `soup.select('h2.post-title > a')`"""
        results.append({'title': no_articles_message, 'link': ''})

    return results

def display_text_results(results):
    """Prints the extracted text results to the console."""
    print("\n--- Results ---")
    if not results:
        print("No results found.")
        return

    for item in results:
        # .get() is used to avoid KeyError if 'link' is missing
        if item.get('link'):
            print(f"Title: {item['title']}\nLink: {item['link']}\n")
        else:
            print(item['title'])

def save_text_results(results, target_url):
    """Saves the extracted text results to a CSV file."""
    print("\n---")
    save_choice = input("Do you want to save the results to a file? (y/n): ").lower()
    if save_choice == 'y':
        try:
            # Define the output directory for CSV files
            output_dir = os.path.join('dist', 'csv')
            os.makedirs(output_dir, exist_ok=True)

            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = os.path.join(output_dir, f"crawled_data_{timestamp}.csv")
            
            with open(filename, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Title', 'Link', 'Source URL']) # Header
                for item in results:
                    writer.writerow([item['title'], item['link'], target_url])
            
            print(f"Results successfully saved to: {filename}")
        except (IOError, csv.Error) as e:
            print(f"Error saving file: {e}")

from urllib.parse import urljoin, urlparse

# --- Image crawling functions ---
def crawl_images(url):
    """
    Crawls the given URL and extracts all absolute image URLs.
    """
    try:
        response = requests.get(url, headers=DEFAULT_HEADERS, timeout=10)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
    except requests.exceptions.RequestException as e:
        print(f"\nError fetching {url}: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    image_urls = []
    
    for img_tag in soup.find_all('img'):
        src = img_tag.get('src')
        if not src:
            continue

        # Skip base64 encoded images and other non-URL sources
        if src.startswith('data:image'):
            continue
        
        # Build absolute URL
        absolute_url = urljoin(url, src)
        
        # A simple filter for common image extensions
        # and ensure the URL seems valid
        if absolute_url.startswith('http') and any(absolute_url.lower().split('?')[0].endswith(ext) for ext in ['.jpeg', '.jpg', '.png', '.gif', '.webp', '.svg']):
             if absolute_url not in image_urls:
                image_urls.append(absolute_url)

    return image_urls

def save_images(image_urls, base_url):
    """Downloads and saves images from a list of URLs."""
    if not image_urls:
        # This case is handled in the main loop, but good to have a safeguard
        print("No images to save.")
        return

    # Create a directory for the images
    try:
        # Sanitize the base_url to create a valid directory name
        domain = urlparse(base_url).netloc.replace('.', '_')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create a dedicated, timestamped folder inside 'dist/image'
        base_image_dir = os.path.join('dist', 'image')
        dir_name = os.path.join(base_image_dir, f"images_{domain}_{timestamp}")
        
        os.makedirs(dir_name, exist_ok=True)
        print(f"\nSaving images to folder: '{dir_name}'")
    except Exception as e:
        print(f"\nError creating directory: {e}")
        return

    saved_count = 0
    for i, img_url in enumerate(image_urls):
        try:
            # Get the image content
            img_response = requests.get(img_url, headers=DEFAULT_HEADERS, timeout=15, stream=True)
            img_response.raise_for_status()

            # Create a filename from the URL
            img_name = os.path.basename(urlparse(img_url).path)
            if not img_name or '.' not in img_name:
                # If no name or extension, create one from the index and try to get extension from content-type
                content_type = img_response.headers.get('content-type')
                ext = '.jpg' # fallback
                if content_type and 'image/' in content_type:
                    ext = '.' + content_type.split('/')[1]
                img_name = f"image_{i+1}{ext}"

            filepath = os.path.join(dir_name, img_name)

            # Write the image to a file
            with open(filepath, 'wb') as f:
                for chunk in img_response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            saved_count += 1
            # Use carriage return to show progress on a single line
            print(f"  ({saved_count}/{len(image_urls)}) Saved {os.path.basename(img_name)}", end='\r')

        except requests.exceptions.RequestException as e:
            print(f"\n  - Failed to download {os.path.basename(img_url)}: {e}")
        except IOError as e:
            print(f"\n  - Failed to save image {os.path.basename(img_name)}: {e}")
    
    print(f"\n\nSuccessfully saved {saved_count} out of {len(image_urls)} images in '{dir_name}'.")

# --- Main application flow functions ---
def get_menu_choice():
    """Displays the main menu and returns the user's choice."""
    print("\n" + "="*30)
    print(" Gemini Web Crawler")
    print("="*30)
    print("Please choose an option:")
    print("  1. Crawl Text (Titles and Links)")
    print("  2. Crawl Images")
    print("  q. Quit")
    return input("> ").strip().lower()

def get_target_url():
    """Prompts the user for a URL and validates it."""
    while True:
        target_url = input("Please enter the full URL to crawl (e.g., https://example.com) or 'q' to return to menu: \n> ")
        if target_url.lower() == 'q':
            return None
        if target_url.startswith('http://') or target_url.startswith('https://'):
            return target_url
        else:
            print("Invalid URL format. Please enter a full URL starting with 'http://' or 'https://'.")

def handle_text_crawling():
    """Manages the process of crawling and handling text."""
    target_url = get_target_url()
    if not target_url:
        return # User entered 'q'

    print("\n讀取中 (Loading)...")
    results = crawl_blog(target_url)

    # Check for errors or empty results before displaying
    if not results or (len(results) == 1 and not results[0].get('link')):
        display_text_results(results) # Display the error/info message
        print("\nCould not find any crawlable text content.")
        return

    display_text_results(results)
    save_text_results(results, target_url)

def handle_image_crawling():
    """Manages the process of crawling and handling images."""
    target_url = get_target_url()
    if not target_url:
        return # User entered 'q'
        
    print("\n讀取中 (Loading)...")
    image_urls = crawl_images(target_url)

    if image_urls:
        print(f"\nFound {len(image_urls)} images.")
        save_images(image_urls, target_url)
    else:
        # This message is shown if crawl_images returns an empty list
        print("\nNo crawlable images found on the page.")

def main():
    """Main application loop."""
    while True:
        choice = get_menu_choice()
        if choice == '1':
            handle_text_crawling()
        elif choice == '2':
            handle_image_crawling()
        elif choice == 'q':
            print("Exiting. Goodbye!")
            break
        else:
            print("Invalid choice, please try again.")
        
        print("\n" + "---"*10)
        print("Operation finished. Press Enter to return to main menu.")
        input()

if __name__ == "__main__":
    main()