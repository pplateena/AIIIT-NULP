import requests
import json
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Set
from config import Config

class WikiScraper:
    def __init__(self):
        self.base_url = Config.WIKI_BASE_URL
        self.api_url = Config.WIKI_API_URL
        self.session = requests.Session()
        self.visited_pages = set()
        self.scraped_data = []
        
    def get_all_pages(self) -> List[str]:
        """Get list of all pages using MediaWiki API"""
        pages = []
        apcontinue = None
        
        while True:
            params = {
                'action': 'query',
                'format': 'json',
                'list': 'allpages',
                'aplimit': 500,
                'apnamespace': 0  # Main namespace only
            }
            
            if apcontinue:
                params['apcontinue'] = apcontinue
            
            try:
                response = self.session.get(self.api_url, params=params)
                response.raise_for_status()
                data = response.json()
                
                if 'query' in data and 'allpages' in data['query']:
                    for page in data['query']['allpages']:
                        pages.append(page['title'])
                
                if 'continue' in data:
                    apcontinue = data['continue']['apcontinue']
                else:
                    break
                    
            except Exception as e:
                print(f"Error fetching pages: {e}")
                break
                
            time.sleep(0.1)  # Rate limiting
        
        return pages
    
    def get_page_content(self, title: str) -> Dict:
        """Get content and metadata for a specific page"""
        params = {
            'action': 'query',
            'format': 'json',
            'titles': title,
            'prop': 'revisions|info',
            'rvprop': 'content',
            'inprop': 'url'
        }
        
        try:
            response = self.session.get(self.api_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            pages = data.get('query', {}).get('pages', {})
            for page_id, page_data in pages.items():
                if page_id == '-1':  # Page doesn't exist
                    continue
                    
                content = ""
                if 'revisions' in page_data and page_data['revisions']:
                    content = page_data['revisions'][0].get('*', '')
                
                # Convert wikitext to HTML for better parsing
                html_content = self.wikitext_to_html(title, content)
                
                return {
                    'title': page_data.get('title', title),
                    'url': page_data.get('fullurl', f"{self.base_url}/wiki/{title}"),
                    'content': content,
                    'html_content': html_content,
                    'plain_text': self.extract_plain_text(html_content)
                }
        
        except Exception as e:
            print(f"Error fetching page {title}: {e}")
            
        return None
    
    def wikitext_to_html(self, title: str, wikitext: str) -> str:
        """Convert wikitext to HTML using MediaWiki API"""
        params = {
            'action': 'parse',
            'format': 'json',
            'text': wikitext,
            'contentmodel': 'wikitext',
            'disablelimitreport': True
        }
        
        try:
            response = self.session.get(self.api_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if 'parse' in data and 'text' in data['parse']:
                return data['parse']['text']['*']
        
        except Exception as e:
            print(f"Error converting wikitext for {title}: {e}")
        
        return wikitext
    
    def extract_plain_text(self, html_content: str) -> str:
        """Extract clean plain text from HTML"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove unwanted elements
        for element in soup(['script', 'style', 'sup', 'table']):
            element.decompose()
        
        # Get text and clean it up
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text
    
    def extract_internal_links(self, html_content: str) -> List[str]:
        """Extract internal wiki links from HTML content"""
        soup = BeautifulSoup(html_content, 'html.parser')
        links = []
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.startswith('/wiki/') and ':' not in href:  # Skip special pages
                page_title = href.split('/wiki/')[-1]
                if page_title not in self.visited_pages:
                    links.append(page_title)
        
        return links
    
    def scrape_wiki(self, max_pages: int = None) -> List[Dict]:
        """Scrape the entire wiki or up to max_pages"""
        print("Fetching list of all pages...")
        all_pages = self.get_all_pages()
        
        if max_pages:
            all_pages = all_pages[:max_pages]
        
        print(f"Found {len(all_pages)} pages to scrape")
        
        for i, title in enumerate(all_pages, 1):
            if title in self.visited_pages:
                continue
            
            print(f"Scraping page {i}/{len(all_pages)}: {title}")
            
            page_data = self.get_page_content(title)
            if page_data and page_data['plain_text'].strip():
                self.scraped_data.append(page_data)
                self.visited_pages.add(title)
            
            time.sleep(0.1)  # Rate limiting
        
        print(f"Successfully scraped {len(self.scraped_data)} pages")
        return self.scraped_data
    
    def save_scraped_data(self, filename: str = "scraped_wiki_data.json"):
        """Save scraped data to JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.scraped_data, f, indent=2, ensure_ascii=False)
        print(f"Saved scraped data to {filename}")
    
    def load_scraped_data(self, filename: str = "scraped_wiki_data.json") -> List[Dict]:
        """Load scraped data from JSON file"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                self.scraped_data = json.load(f)
            print(f"Loaded {len(self.scraped_data)} pages from {filename}")
            return self.scraped_data
        except FileNotFoundError:
            print(f"File {filename} not found")
            return []

if __name__ == "__main__":
    scraper = WikiScraper()
    # Test with a small number first
    data = scraper.scrape_wiki(max_pages=10)
    scraper.save_scraped_data("test_scraped_data.json")