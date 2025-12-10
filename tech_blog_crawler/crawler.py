import requests
from bs4 import BeautifulSoup
import sys
from analyzer import run_analyzer
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
        results.append({'title': f"讀取 {url} 時發生錯誤: {e}", 'link': ''})
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
        no_articles_message = """找不到可辨識的文章。請檢查目標網站的 HTML 結構以優化選擇器。
您可以這樣做：
1. 在瀏覽器中打開目標網站。
2. 在文章標題上按右鍵，選擇 '檢查' 或 '檢查元素'。
3. 在開發者工具中，找到能夠唯一識別文章標題和連結的 HTML 標籤與 class。
4. 修改 `crawler.py` 腳本，使用 `soup.find()` 或 `soup.find_all()` 方法來指定這些標籤。
   例如: `soup.find_all('div', class_='article-card')` 或 `soup.select('h2.post-title > a')`"""
        results.append({'title': no_articles_message, 'link': ''})

    return results

def display_text_results(results):
    """Prints the extracted text results to the console."""
    print("\n--- 爬取結果 ---")
    if not results:
        print("找不到任何結果。 সন")
        return

    for item in results:
        # .get() is used to avoid KeyError if 'link' is missing
        if item.get('link'):
            print(f"標題: {item['title']}\n連結: {item['link']}\n")
        else:
            print(item['title'])

def save_text_results(results, target_url):
    """Saves the extracted text results to a CSV file."""
    print("\n---")
    save_choice = input("您要將結果儲存為檔案嗎？ (y/n): ").lower()
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
            
            print(f"結果已成功儲存至: {filename}")
        except (IOError, csv.Error) as e:
            print(f"儲存檔案時發生錯誤: {e}")

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
        print(f"\n讀取 {url} 時發生錯誤: {e}")
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
        print("沒有找到可儲存的圖片。 সন")
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
        print(f"\n正在儲存圖片至資料夾: '{dir_name}'")
    except Exception as e:
        print(f"\n建立資料夾時發生錯誤: {e}")
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
            print(f"  ({saved_count}/{len(image_urls)}) 已儲存 {os.path.basename(img_name)}", end='\r')

        except requests.exceptions.RequestException as e:
            print(f"\n  - 下載失敗 {os.path.basename(img_url)}: {e}")
        except IOError as e:
            print(f"\n  - 儲存圖片失敗 {os.path.basename(img_name)}: {e}")
    
    print(f"\n\n成功在 '{dir_name}' 中儲存了 {len(image_urls)} 張圖片中的 {saved_count} 張。 সন")

# --- Main application flow functions ---
def show_crawler_submenu():
    """Displays the crawling sub-menu and handles crawling operations."""
    while True:
        print("\n--- 爬蟲選單 ---")
        print("請選擇要爬取的項目：")
        print("  1. 爬取文字 (標題與連結)")
        print("  2. 爬取圖片")
        print("  b. 返回主選單")
        choice = input("請輸入選項 > ").strip().lower()

        if choice == '1':
            handle_text_crawling()
            print("\n" + "---"*10)
            print("爬取作業完成。請按 Enter 返回爬蟲選單。 সন")
            input()
        elif choice == '2':
            handle_image_crawling()
            print("\n" + "---"*10)
            print("爬取作業完成。請按 Enter 返回爬蟲選單。 সন")
            input()
        elif choice == 'b':
            return # Go back to the main menu
        else:
            print("無效的選項，請重新輸入。 সন")

def get_target_url():
    """Prompts the user for a URL and validates it."""
    while True:
        target_url = input("請輸入要爬取的完整網址 (例如 https://example.com)，或輸入 'q' 返回選單: \n> ")
        if target_url.lower() == 'q':
            return None
        if target_url.startswith('http://') or target_url.startswith('https://'):
            return target_url
        else:
            print("網址格式無效，請輸入以 'http://' 或 'https://' 開頭的完整網址。 সন")

def handle_text_crawling():
    """Manages the process of crawling and handling text."""
    target_url = get_target_url()
    if not target_url:
        return # User entered 'q'

    print("\n讀取中 (Loading)... সন")
    results = crawl_blog(target_url)

    # Check for errors or empty results before displaying
    if not results or (len(results) == 1 and not results[0].get('link')):
        display_text_results(results) # Display the error/info message
        print("\n找不到任何可爬取的文字內容。 সন")
        return

    display_text_results(results)
    save_text_results(results, target_url)

def handle_image_crawling():
    """Manages the process of crawling and handling images."""
    target_url = get_target_url()
    if not target_url:
        return # User entered 'q'
        
    print("\n讀取中 (Loading)... সন")
    image_urls = crawl_images(target_url)

    if image_urls:
        print(f"\n找到 {len(image_urls)} 張圖片。 সন")
        save_images(image_urls, target_url)
    else:
        # This message is shown if crawl_images returns an empty list
        print("\n在頁面上找不到可爬取的圖片。 সন")

def main():
    """Main application loop for V2.0."""
    while True:
        print("\n" + "="*50)
        print("          Gemini 網路爬蟲 & AI 分析器 V2.0")
        print("="*50)
        print("請選擇要執行的功能：")
        print("  1. 執行爬蟲 (收集資料)")
        print("  2. 執行 AI 分析報告")
        print("  3. 離開程式")
        choice = input("請輸入選項 > ").strip().lower()

        if choice == '1':
            show_crawler_submenu()
        elif choice == '2':
            run_analyzer()
        elif choice == '3':
            print("\n正在離開程式，再見！ সন")
            break
        else:
            print("\n無效的選項，請重新輸入。 সন")
        
        if choice != '3':
            print("\n" + "---"*10)
            print("作業完成。請按 Enter 返回主選單。 সন")
            input()

if __name__ == "__main__":
    main()
