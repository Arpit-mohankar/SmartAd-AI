import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
from typing import Dict, List
import logging

class WebsiteScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def scrape_website(self, url: str) -> Dict:
        """Extract content from website"""
        try:
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract key content
            title = soup.find('title').get_text() if soup.find('title') else ""
            
            # Get meta description
            meta_desc = ""
            meta_tag = soup.find('meta', attrs={'name': 'description'})
            if meta_tag:
                meta_desc = meta_tag.get('content', '')
            
            # Extract headings
            headings = {
                'h1': [h.get_text().strip() for h in soup.find_all('h1')],
                'h2': [h.get_text().strip() for h in soup.find_all('h2')],
                'h3': [h.get_text().strip() for h in soup.find_all('h3')]
            }
            
            # Extract navigation and menu items
            nav_items = []
            nav_elements = soup.find_all(['nav', 'menu'])
            for nav in nav_elements:
                links = nav.find_all('a')
                nav_items.extend([link.get_text().strip() for link in links if link.get_text().strip()])
            
            # Extract main content
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text content
            main_content = soup.get_text()
            
            # Clean up text
            lines = (line.strip() for line in main_content.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return {
                'url': url,
                'title': title,
                'meta_description': meta_desc,
                'headings': headings,
                'navigation': nav_items,
                'content': text[:5000],  # Limit content for LLM processing
                'content_length': len(text)
            }
            
        except Exception as e:
            logging.error(f"Error scraping {url}: {e}")
            return {
                'url': url,
                'error': str(e),
                'title': '',
                'content': ''
            }
    
    def extract_products_services(self, content_data: Dict) -> List[str]:
        """Extract product/service keywords from scraped content"""
        products_services = []
        
        # Extract from navigation
        nav_items = content_data.get('navigation', [])
        products_services.extend(nav_items)
        
        # Extract from headings
        headings = content_data.get('headings', {})
        for heading_level, heading_list in headings.items():
            products_services.extend(heading_list)
        
        # Clean and filter
        cleaned = []
        for item in products_services:
            if len(item) > 2 and len(item) < 50:  # Reasonable length
                cleaned.append(item.lower().strip())
        
        return list(set(cleaned))  # Remove duplicates
