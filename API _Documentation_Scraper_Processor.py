#API Documentation Scraper and Processor
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
import json

def scrape_website(start_url, base_url):
    visited = set()
    to_visit = [start_url]
    content = {}

    while to_visit:
        url = to_visit.pop(0)
        if url in visited or not url.startswith(base_url):
            continue

        print(f"Scraping: {url}")
        visited.add(url)

        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract main content (adjust selector as needed)
        main_content = soup.select_one('main') or soup.select_one('article') or soup.body
        if main_content:
            content[url] = main_content.get_text(strip=True, separator=' ')

        # Find more links
        for link in soup.find_all('a', href=True):
            new_url = urljoin(url, link['href'])
            if new_url not in visited and new_url.startswith(base_url):
                to_visit.append(new_url)

    return content

def preprocess_text(text):
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    # Add more preprocessing steps as needed
    return text

def chunk_text(text, max_chunk_size=1000):
    words = text.split()
    chunks = []
    current_chunk = []

    for word in words:
        if len(' '.join(current_chunk)) + len(word) > max_chunk_size and current_chunk:
            chunks.append(' '.join(current_chunk))
            current_chunk = []
        current_chunk.append(word)

    if current_chunk:
        chunks.append(' '.join(current_chunk))

    return chunks

def process_content(content):
    processed_data = []
    for url, text in content.items():
        clean_text = preprocess_text(text)
        chunks = chunk_text(clean_text)
        for i, chunk in enumerate(chunks):
            processed_data.append({
                'text': chunk,
                'metadata': {
                    'source': url,
                    'chunk_index': i
                }
            })
    return processed_data

def save_to_json(data, filename='processed_api_docs.json'):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

def main():
    start_url = 'https://docs.fortinet.com/document/fortianalyzer/7.2.7/administration-guide/366418/setting-up-fortianalyzer'  # Replace with your API docs URL
    base_url = 'https://docs.fortinet.com/document/fortianalyzer/7.2.7/administration-guide/366418/setting-up-fortianalyzer' # Replace with the base URL of the docs

    # Step 1 & 2: Web scraping and initial preprocessing
    scraped_content = scrape_website(start_url, base_url)

    # Step 3 & 4: Text extraction and chunking
    processed_data = process_content(scraped_content)

    # Step 5: Save processed data with metadata
    save_to_json(processed_data)

    print(f"Processed {len(processed_data)} chunks from {len(scraped_content)} pages.")
    print("Data saved to processed_api_docs.json")

if __name__ == "__main__":
    main()