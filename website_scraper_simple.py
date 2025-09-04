"""
Alternative website scraper using requests as a fallback
Use this if Playwright continues to have event loop issues
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import re
from typing import List, Dict, Set
from agents import Agent, Runner
import json
from config import REQUEST_TIMEOUT, USER_AGENT, MAX_PAGES_TO_SCRAPE


class SimpleWebsiteScraper:
    def __init__(self):
        self.visited_urls: Set[str] = set()
        self.scraped_data: List[Dict] = []
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
    def is_valid_url(self, url: str, base_domain: str) -> bool:
        """Check if URL is valid and belongs to the same domain"""
        try:
            parsed_url = urlparse(url)
            parsed_base = urlparse(base_domain)
            return (
                parsed_url.netloc == parsed_base.netloc and
                not any(ext in url.lower() for ext in ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png', '.gif', '.mp4', '.mp3'])
            )
        except:
            return False
    
    def extract_text_content(self, soup: BeautifulSoup) -> str:
        """Extract clean text content from BeautifulSoup object"""
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        # Get text and clean it up
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text
    
    def scrape_page(self, url: str) -> Dict:
        """Scrape a single page using requests and return structured data"""
        try:
            response = self.session.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html5lib')
            
            # Extract page information
            title = soup.find('title')
            title_text = title.get_text().strip() if title else "No title"
            
            # Extract main content
            main_content = self.extract_text_content(soup)
            
            # Extract links for further crawling
            links = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = urljoin(url, href)
                if self.is_valid_url(full_url, url):
                    links.append(full_url)
            
            # Extract meta information
            meta_description = ""
            meta_desc_tag = soup.find('meta', attrs={'name': 'description'})
            if meta_desc_tag:
                meta_description = meta_desc_tag.get('content', '')
            
            return {
                'url': url,
                'title': title_text,
                'content': main_content,
                'meta_description': meta_description,
                'links': links,
                'word_count': len(main_content.split()),
                'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            return {
                'url': url,
                'error': str(e),
                'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }
    
    def crawl_website(self, start_url: str, max_pages: int = MAX_PAGES_TO_SCRAPE) -> List[Dict]:
        """Crawl website starting from start_url"""
        self.visited_urls.clear()
        self.scraped_data.clear()
        
        urls_to_visit = [start_url]
        
        while urls_to_visit and len(self.visited_urls) < max_pages:
            current_url = urls_to_visit.pop(0)
            
            if current_url in self.visited_urls:
                continue
                
            self.visited_urls.add(current_url)
            
            print(f"Scraping: {current_url}")
            page_data = self.scrape_page(current_url)
            self.scraped_data.append(page_data)
            
            # Add new links to visit
            if 'links' in page_data:
                for link in page_data['links']:
                    if link not in self.visited_urls and link not in urls_to_visit:
                        urls_to_visit.append(link)
            
            # Be respectful with requests
            time.sleep(1)
        
        return self.scraped_data


class SimpleUniversityInfoAgent:
    def __init__(self):
        self.scraper = SimpleWebsiteScraper()
        self.agent = Agent(
            name="University Information Collector",
            instructions="""
            You are an AI agent specialized in collecting and organizing information from university websites.
            Your task is to analyze scraped website content and extract relevant university information in a structured format.
            
            Focus on extracting:
            1. University name and basic information
            2. Academic programs and departments
            3. Admission requirements and procedures
            4. Faculty and staff information
            5. Campus facilities and services
            6. Contact information
            7. Tuition and fees
            8. Important dates and deadlines
            9. Research opportunities
            10. Student life and activities
            
            Always provide verbatim quotes from the source material when possible.
            Organize the information in a clear, structured format.
            """
        )
    
    def collect_university_info(self, university_url: str, max_pages: int = 20) -> Dict:
        """Main method to collect university information"""
        print(f"Starting to collect information from: {university_url}")
        
        # Scrape the website
        scraped_data = self.scraper.crawl_website(university_url, max_pages)
        
        # Prepare data for the agent
        combined_content = ""
        for page in scraped_data:
            if 'content' in page and 'error' not in page:
                combined_content += f"\n\n--- Page: {page['title']} ({page['url']}) ---\n"
                combined_content += page['content'][:2000]  # Limit content per page
        
        # Use the agent to analyze and structure the information
        prompt = f"""
        Analyze the following university website content and extract relevant information in a structured format.
        
        Website URL: {university_url}
        Number of pages scraped: {len(scraped_data)}
        
        Content to analyze:
        {combined_content}
        
        Please provide a comprehensive analysis with verbatim quotes where relevant.
        """
        
        result = Runner.run_sync(self.agent, prompt)
        
        return {
            'university_url': university_url,
            'scraped_pages': len(scraped_data),
            'raw_data': scraped_data,
            'structured_analysis': result.final_output,
            'collection_timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def export_to_json(self, data: Dict, filename: str = None) -> str:
        """Export collected data to JSON file"""
        if filename is None:
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            filename = f"university_data_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return filename
