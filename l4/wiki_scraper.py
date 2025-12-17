import requests
import json
import time
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, quote
from typing import List, Dict, Set
from config import Config

class WikiScraper:
    def __init__(self):
        self.base_url = Config.WIKI_BASE_URL
        self.api_url = Config.WIKI_API_URL
        self.session = requests.Session()
        
        # Add proper headers to avoid 403 errors
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none'
        })
        
        self.visited_pages = set()
        self.scraped_data = []
        self.use_html_fallback = False
        
    def test_api_access(self) -> bool:
        """Test if MediaWiki API is accessible"""
        try:
            params = {
                'action': 'query',
                'format': 'json',
                'meta': 'siteinfo',
                'siprop': 'general'
            }
            response = self.session.get(self.api_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            return 'query' in data
        except Exception as e:
            print(f"API access test failed: {e}")
            return False
    
    def get_all_pages_api(self) -> List[str]:
        """Get list of all pages using MediaWiki API"""
        pages = []
        apcontinue = None
        
        while True:
            params = {
                'action': 'query',
                'format': 'json',
                'list': 'allpages',
                'aplimit': 50,  # Reduced limit to be more conservative
                'apnamespace': 0  # Main namespace only
            }
            
            if apcontinue:
                params['apcontinue'] = apcontinue
            
            try:
                response = self.session.get(self.api_url, params=params, timeout=15)
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
                print(f"Error fetching pages via API: {e}")
                print("Switching to HTML fallback method...")
                self.use_html_fallback = True
                return self.get_all_pages_html()
                
            time.sleep(0.5)  # More conservative rate limiting
        
        return pages
    
    def get_all_pages_html(self) -> List[str]:
        """Fallback method: scrape page list from Special:AllPages"""
        pages = []
        
        try:
            # Try to get main page first
            main_page_url = f"{self.base_url}/wiki/Main_Page"
            response = self.session.get(main_page_url, timeout=15)
            response.raise_for_status()
            
            # Parse main page to find links
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all internal wiki links
            for link in soup.find_all('a', href=True):
                href = link['href']
                if href.startswith('/wiki/') and ':' not in href.split('/wiki/')[-1]:
                    page_title = href.split('/wiki/')[-1]
                    if page_title not in ['Main_Page'] and page_title not in pages:
                        pages.append(page_title)
            
            # Try to get more pages from sitemap or special pages
            special_pages_to_try = [
                'Special:Random',
                'Category:Items',
                'Category:Machines', 
                'Category:Recipes',
                'Category:Materials'
            ]
            
            for special_page in special_pages_to_try:
                try:
                    url = f"{self.base_url}/wiki/{special_page}"
                    response = self.session.get(url, timeout=10)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        for link in soup.find_all('a', href=True):
                            href = link['href']
                            if href.startswith('/wiki/') and ':' not in href.split('/wiki/')[-1]:
                                page_title = href.split('/wiki/')[-1]
                                if page_title not in pages:
                                    pages.append(page_title)
                    time.sleep(0.5)
                except:
                    continue
            
            # Add some common GT New Horizons pages manually as fallback
            common_pages = [
                'Electric_Blast_Furnace',
                'Getting_Started',
                'Power_Tiers',
                'Materials',
                'Machines',
                'Recipes',
                'Steel',
                'Aluminium',
                'Bronze_Age',
                'Steam_Age',
                'LV_Tier',
                'MV_Tier',
                'HV_Tier',
                'Ore_Processing',
                'Multiblock_Machines',
                'GT_New_Horizons'
            ]
            
            for page in common_pages:
                if page not in pages:
                    pages.append(page)
                    
        except Exception as e:
            print(f"Error in HTML fallback: {e}")
            # Use predefined list as last resort
            pages = [
                'Main_Page',
                'Electric_Blast_Furnace', 
                'Getting_Started',
                'Power_Tiers',
                'Materials',
                'Steel',
                'Bronze_Age',
                'Steam_Age',
                'LV_Tier',
                'MV_Tier'
            ]
        
        return list(set(pages))  # Remove duplicates
    
    def get_all_pages(self) -> List[str]:
        """Get list of all pages, trying API first, then HTML fallback"""
        if not self.use_html_fallback and self.test_api_access():
            print("Using MediaWiki API...")
            return self.get_all_pages_api()
        else:
            print("Using HTML scraping fallback...")
            return self.get_all_pages_html()
    
    def get_page_content_api(self, title: str) -> Dict:
        """Get content using MediaWiki API"""
        params = {
            'action': 'query',
            'format': 'json',
            'titles': title,
            'prop': 'revisions|info',
            'rvprop': 'content',
            'inprop': 'url'
        }
        
        try:
            response = self.session.get(self.api_url, params=params, timeout=15)
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
                    'url': page_data.get('fullurl', f"{self.base_url}/wiki/{quote(title)}"),
                    'content': content,
                    'html_content': html_content,
                    'plain_text': self.extract_plain_text(html_content)
                }
        
        except Exception as e:
            print(f"API error for page {title}: {e}")
            
        return None
    
    def get_page_content_html(self, title: str) -> Dict:
        """Get content by directly scraping HTML page"""
        url = f"{self.base_url}/wiki/{quote(title)}"
        
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find the main content area
            content_div = soup.find('div', {'id': 'mw-content-text'}) or soup.find('div', {'class': 'mw-content'})
            
            if content_div:
                # Remove unwanted elements
                for element in content_div(['script', 'style', 'nav', 'aside', '.navbox', '.infobox']):
                    if element:
                        element.decompose()
                
                html_content = str(content_div)
                plain_text = self.extract_plain_text(html_content)
                
                return {
                    'title': title.replace('_', ' '),
                    'url': url,
                    'content': plain_text,  # We don't have wikitext, so use plain text
                    'html_content': html_content,
                    'plain_text': plain_text
                }
            
        except Exception as e:
            print(f"HTML scraping error for page {title}: {e}")
        
        return None
    
    def get_page_content(self, title: str) -> Dict:
        """Get content, trying API first, then HTML fallback"""
        if not self.use_html_fallback:
            result = self.get_page_content_api(title)
            if result:
                return result
            else:
                print(f"API failed for {title}, trying HTML...")
        
        return self.get_page_content_html(title)
    
    def wikitext_to_html(self, title: str, wikitext: str) -> str:
        """Convert wikitext to HTML using MediaWiki API"""
        if not wikitext.strip():
            return wikitext
            
        params = {
            'action': 'parse',
            'format': 'json',
            'text': wikitext[:50000],  # Limit text size to avoid errors
            'contentmodel': 'wikitext',
            'disablelimitreport': True
        }
        
        try:
            response = self.session.get(self.api_url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            if 'parse' in data and 'text' in data['parse']:
                return data['parse']['text']['*']
        
        except Exception as e:
            print(f"Error converting wikitext for {title}: {e}")
        
        return wikitext
    
    def extract_plain_text(self, html_content: str) -> str:
        """Extract clean plain text from HTML"""
        if not html_content:
            return ""
            
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove unwanted elements
        for element in soup(['script', 'style', 'sup', 'table', 'nav', 'aside', '.navbox']):
            if element:
                element.decompose()
        
        # Get text and clean it up
        text = soup.get_text()
        
        # Clean whitespace and normalize
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        # Remove wiki markup that might remain
        text = re.sub(r'\{\{[^}]*\}\}', '', text)  # Remove templates
        text = re.sub(r'\[\[[^\]]*\]\]', '', text)  # Remove links
        text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
        
        return text.strip()
    
    def scrape_wiki(self, max_pages: int = None) -> List[Dict]:
        """Scrape the entire wiki or up to max_pages"""
        print("Fetching list of all pages...")
        all_pages = self.get_all_pages()
        
        if max_pages:
            all_pages = all_pages[:max_pages]
        
        print(f"Found {len(all_pages)} pages to scrape")
        
        if len(all_pages) == 0:
            print("No pages found! This might be due to access restrictions.")
            print("Try using a VPN or checking if the site is accessible.")
            return []
        
        for i, title in enumerate(all_pages, 1):
            if title in self.visited_pages:
                continue
            
            print(f"Scraping page {i}/{len(all_pages)}: {title}")
            
            page_data = self.get_page_content(title)
            if page_data and page_data['plain_text'].strip() and len(page_data['plain_text']) > 100:
                self.scraped_data.append(page_data)
                self.visited_pages.add(title)
                print(f"  SUCCESS: Scraped {len(page_data['plain_text'])} characters")
            else:
                print(f"  SKIPPED: (empty or too short)")
            
            time.sleep(0.8)  # Conservative rate limiting
        
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
    data = scraper.scrape_wiki(max_pages=5)
    scraper.save_scraped_data("test_scraped_data.json")
    print(f"Scraped {len(data)} pages successfully!")