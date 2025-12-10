# Tech Blog Article Title and Link Crawler

This project provides a basic Python script to crawl a technology blog or news website, extract article titles, and their corresponding links.

## Project Structure

- `crawler.py`: The main Python script containing the web crawling logic.
- `requirements.txt`: Lists the Python dependencies required to run the crawler.

## Setup

1.  **Clone the repository (if applicable) or navigate to the project directory:**

    ```bash
    cd tech_blog_crawler
    ```

2.  **Create a virtual environment (recommended):**

    ```bash
    python -m venv venv
    ```

3.  **Activate the virtual environment:**

    -   **On Windows:**
        ```bash
        .\venv\Scripts\activate
        ```
    -   **On macOS/Linux:**
        ```bash
        source venv/bin/activate
        ```

4.  **Install the required Python packages:**

    ```bash
    pip install -r requirements.txt
    ```

## Usage

To run the crawler, execute the `crawler.py` script followed by the URL of the technology blog or news website you want to crawl.

```bash
python crawler.py <TARGET_URL>
```

**Example:**

```bash
python crawler.py https://www.theverge.com/tech
```

The script will print the extracted article titles and links to the console.

## Customization

The `crawler.py` script includes a generic approach to finding titles and links. For optimal results on a specific website, you will likely need to inspect the target website's HTML structure using your browser's developer tools.

Look for patterns in how article listings are structured (e.g., specific `<div>` elements with certain classes, `<h2>` or `<h3>` tags for titles, and `<a>` tags for links). You can then modify the `BeautifulSoup` selection methods in `crawler.py` to target these specific elements.

**Example of potential modifications in `crawler.py`:**

Instead of `links = soup.find_all('a')`, you might use:

```python
# To find specific article containers
article_containers = soup.find_all('div', class_='c-entry-box--compact')

for container in article_containers:
    title_tag = container.find('h2', class_='c-entry-box--compact__title')
    link_tag = container.find('a', class_='c-entry-box--compact__image-wrapper')

    if title_tag and link_tag:
        title = title_tag.get_text(strip=True)
        link = link_tag.get('href')
        print(f"Title: {title}\nLink: {link}\n")
```

Remember to adapt the CSS selectors (`div`, `h2`, `a`, `class_`, etc.) to match the website you are targeting.
