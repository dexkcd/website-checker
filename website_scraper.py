from playwright.sync_api import sync_playwright, Browser, Page
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import re
import os
from typing import List, Dict, Set
from agents import Agent, Runner
import json
from config import (
    REQUEST_TIMEOUT, USER_AGENT, MAX_PAGES_TO_SCRAPE,
    PLAYWRIGHT_HEADLESS, PLAYWRIGHT_VIEWPORT, 
    PLAYWRIGHT_WAIT_FOR_NETWORK_IDLE, PLAYWRIGHT_EXTRA_WAIT_TIME
)


class WebsiteScraper:
    def __init__(self, screenshots_dir: str = "screenshots"):
        self.visited_urls: Set[str] = set()
        self.scraped_data: List[Dict] = []
        self.playwright = None
        self.browser: Browser = None
        self.context = None
        self.screenshots_dir = screenshots_dir
        
        # Create screenshots directory if it doesn't exist
        os.makedirs(self.screenshots_dir, exist_ok=True)
        
    def normalize_url(self, url: str) -> str:
        """Normalize URL to ensure it's properly formatted"""
        if not url:
            return ""
        
        # Remove whitespace
        url = url.strip()
        
        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        return url
    
    def is_valid_url(self, url: str, base_domain: str) -> bool:
        """Check if URL is valid and belongs to the same domain"""
        try:
            # Normalize URLs
            url = self.normalize_url(url)
            base_domain = self.normalize_url(base_domain)
            
            parsed_url = urlparse(url)
            parsed_base = urlparse(base_domain)
            
            # Check if it's a valid URL with netloc
            if not parsed_url.netloc or not parsed_base.netloc:
                return False
            
            # Check if it's the same domain
            same_domain = parsed_url.netloc == parsed_base.netloc
            
            # Check if it's not a file download
            not_file = not any(ext in url.lower() for ext in ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png', '.gif', '.mp4', '.mp3', '.zip', '.exe'])
            
            # Check if it's not a mailto or tel link
            not_special = not url.lower().startswith(('mailto:', 'tel:', 'javascript:', '#'))
            
            return same_domain and not_file and not_special
            
        except Exception as e:
            print(f"URL validation error for {url}: {e}")
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
    
    def start_browser(self):
        """Initialize Playwright browser"""
        if not self.playwright:
            print("🚀 Starting Playwright...")
            self.playwright = sync_playwright().start()
            print("🌐 Launching Chromium browser...")
            self.browser = self.playwright.chromium.launch(
                headless=PLAYWRIGHT_HEADLESS,
                args=['--no-sandbox', '--disable-dev-shm-usage', '--disable-blink-features=AutomationControlled']
            )
            print("📄 Creating browser context...")
            self.context = self.browser.new_context(
                user_agent=USER_AGENT,
                viewport=PLAYWRIGHT_VIEWPORT,
                extra_http_headers={
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                }
            )
            print("✅ Browser ready!")
    
    def close_browser(self):
        """Close Playwright browser"""
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
    
    def scrape_page(self, url: str) -> Dict:
        """Scrape a single page using Playwright and return structured data"""
        page = None
        try:
            # Normalize the URL
            normalized_url = self.normalize_url(url)
            print(f"🔗 Navigating to: {normalized_url}")
            
            # Ensure browser is started
            if not self.context:
                print("⚠️ Browser not started, starting now...")
                self.start_browser()
            
            print("📄 Creating new page...")
            page = self.context.new_page()
            
            # Set timeout and navigate
            page.set_default_timeout(REQUEST_TIMEOUT * 1000)  # Convert to milliseconds
            
            # Navigate to the page
            print(f"🌐 Loading page: {normalized_url}")
            try:
                if PLAYWRIGHT_WAIT_FOR_NETWORK_IDLE:
                    page.goto(normalized_url, wait_until='networkidle')
                else:
                    page.goto(normalized_url, wait_until='domcontentloaded')
                print("✅ Page navigation successful!")
            except Exception as nav_error:
                print(f"❌ Navigation failed: {nav_error}")
                raise nav_error
            
            # Wait for content to load
            print("⏳ Waiting for content to load...")
            page.wait_for_timeout(PLAYWRIGHT_EXTRA_WAIT_TIME)
            
            # Get current URL to verify we're on the right page
            current_url = page.url
            print(f"✅ Successfully loaded: {current_url}")
            
            # Take screenshot
            print("📸 Taking screenshot...")
            screenshot_filename = f"screenshot_{len(self.scraped_data) + 1}_{int(time.time())}.png"
            screenshot_path = os.path.join(self.screenshots_dir, screenshot_filename)
            page.screenshot(path=screenshot_path, full_page=True)
            print(f"📸 Screenshot saved: {screenshot_path}")
            
            # Get page content
            print("📖 Getting page content...")
            content = page.content()
            soup = BeautifulSoup(content, 'html5lib')
            
            # Extract page information
            title = soup.find('title')
            title_text = title.get_text().strip() if title else "No title"
            
            # Extract main content
            main_content = self.extract_text_content(soup)
            
            # Extract links for further crawling
            links = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                # Use the normalized URL for joining
                full_url = urljoin(normalized_url, href)
                if self.is_valid_url(full_url, normalized_url):
                    links.append(full_url)
            
            print(f"🔗 Found {len(links)} valid links on this page")
            
            # Extract meta information
            meta_description = ""
            meta_desc_tag = soup.find('meta', attrs={'name': 'description'})
            if meta_desc_tag:
                meta_description = meta_desc_tag.get('content', '')
            
            # Close the page
            if page:
                page.close()
                print("🔒 Page closed")
            
            return {
                'url': url,
                'normalized_url': normalized_url,
                'actual_url': current_url,
                'title': title_text,
                'content': main_content,
                'meta_description': meta_description,
                'links': links,
                'word_count': len(main_content.split()),
                'screenshot_path': screenshot_path,
                'screenshot_filename': screenshot_filename,
                'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            print(f"❌ Error scraping {url}: {e}")
            if page:
                try:
                    page.close()
                except:
                    pass
            return {
                'url': url,
                'error': str(e),
                'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S')
            }
    
    def crawl_website(self, start_url: str, max_pages: int = MAX_PAGES_TO_SCRAPE) -> List[Dict]:
        """Crawl website starting from start_url using Playwright"""
        self.visited_urls.clear()
        self.scraped_data.clear()
        
        try:
            # Normalize the start URL
            normalized_start_url = self.normalize_url(start_url)
            print(f"🚀 Starting crawl from: {normalized_start_url}")
            
            # Start browser
            self.start_browser()
            
            urls_to_visit = [normalized_start_url]
            
            while urls_to_visit and len(self.visited_urls) < max_pages:
                current_url = urls_to_visit.pop(0)
                
                # Normalize the current URL
                normalized_current_url = self.normalize_url(current_url)
                
                if normalized_current_url in self.visited_urls:
                    continue
                    
                self.visited_urls.add(normalized_current_url)
                
                print(f"📄 Scraping: {normalized_current_url}")
                page_data = self.scrape_page(normalized_current_url)
                self.scraped_data.append(page_data)
                
                # Add new links to visit
                if 'links' in page_data and 'error' not in page_data:
                    for link in page_data['links']:
                        normalized_link = self.normalize_url(link)
                        if normalized_link not in self.visited_urls and normalized_link not in urls_to_visit:
                            urls_to_visit.append(normalized_link)
                
                # Be respectful with requests
                time.sleep(1)
            
            print(f"✅ Crawling completed. Scraped {len(self.scraped_data)} pages.")
            return self.scraped_data
            
        finally:
            # Always close browser when done
            self.close_browser()


class SectionBasedAnalyzer:
    def __init__(self, sections_config_path: str = "settings/crawl_sections.json"):
        self.sections_config = self.load_sections_config(sections_config_path)
        self.scraper = WebsiteScraper()
        
    def load_sections_config(self, config_path: str) -> Dict:
        """Load the sections configuration from JSON file"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"⚠️ Sections config file not found: {config_path}")
            return {"sections": []}
        except Exception as e:
            print(f"❌ Error loading sections config: {e}")
            return {"sections": []}
    
    def analyze_content_for_sections(self, scraped_data: List[Dict], organization_name: str = "") -> Dict:
        """Analyze scraped content and organize it by sections"""
        print("🔍 Analyzing content for sections...")
        
        # Prepare all content for analysis
        all_content = ""
        for page in scraped_data:
            if 'content' in page and 'error' not in page:
                all_content += f"\n\n--- Page: {page['title']} ({page['url']}) ---\n"
                all_content += page['content']
        
        # Replace organization name placeholder
        sections = []
        for section in self.sections_config.get('sections', []):
            section_name = section['section_name']
            if '[organization name]' in section_name and organization_name:
                section_name = section_name.replace('[organization name]', organization_name)
            
            # Process subsections
            subsections = []
            for subsection in section.get('subsection', []):
                subsection_name = subsection['subsection_name']
                if '[organization name]' in subsection_name and organization_name:
                    subsection_name = subsection_name.replace('[organization name]', organization_name)
                
                # Find relevant pages for this subsection
                relevant_pages = self.find_relevant_pages(
                    scraped_data, 
                    subsection['subsection_definition'],
                    subsection_name
                )
                
                subsections.append({
                    'subsection_name': subsection_name,
                    'subsection_definition': subsection['subsection_definition'],
                    'relevant_pages': relevant_pages
                })
            
            sections.append({
                'section_name': section_name,
                'section_definition': section['section_definition'],
                'subsections': subsections
            })
        
        return {
            'organization_name': organization_name,
            'sections': sections,
            'total_pages_scraped': len(scraped_data),
            'analysis_timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def find_relevant_pages(self, scraped_data: List[Dict], subsection_definition: str, subsection_name: str) -> List[Dict]:
        """Find pages relevant to a specific subsection"""
        relevant_pages = []
        
        # Simple keyword-based matching (can be enhanced with AI)
        keywords = self.extract_keywords(subsection_definition, subsection_name)
        
        for page in scraped_data:
            if 'error' in page:
                continue
                
            content = page.get('content', '').lower()
            title = page.get('title', '').lower()
            
            # Check if page contains relevant keywords
            relevance_score = 0
            for keyword in keywords:
                if keyword in content or keyword in title:
                    relevance_score += 1
            
            if relevance_score > 0:
                relevant_pages.append({
                    'page_title': page.get('title', 'No title'),
                    'url': page.get('actual_url', page.get('url', '')),
                    'content': page.get('content', '')[:1000] + '...' if len(page.get('content', '')) > 1000 else page.get('content', ''),
                    'screenshot_path': page.get('screenshot_path', ''),
                    'screenshot_filename': page.get('screenshot_filename', ''),
                    'relevance_score': relevance_score,
                    'word_count': page.get('word_count', 0)
                })
        
        # Sort by relevance score
        relevant_pages.sort(key=lambda x: x['relevance_score'], reverse=True)
        return relevant_pages[:5]  # Return top 5 most relevant pages
    
    def extract_keywords(self, definition: str, name: str) -> List[str]:
        """Extract keywords from subsection definition and name"""
        text = f"{name} {definition}".lower()
        
        # Remove common words and extract meaningful keywords
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'about', 'over', 'under', 'through', 'during', 'before', 'after', 'above', 'below', 'up', 'down', 'out', 'off', 'again', 'further', 'then', 'once'}
        
        words = re.findall(r'\b\w+\b', text)
        keywords = [word for word in words if len(word) > 3 and word not in stop_words]
        
        return list(set(keywords))  # Remove duplicates


class UniversityInfoAgent:
    def __init__(self):
        self.scraper = WebsiteScraper()
        self.section_analyzer = SectionBasedAnalyzer()
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
    
    def _run_agent_in_thread(self, prompt: str):
        """Run the OpenAI agent in a separate thread with its own event loop"""
        import threading
        import asyncio
        
        result = [None]
        error = [None]
        
        def run_agent():
            try:
                # Create a new event loop for this thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # Run the agent
                result[0] = Runner.run_sync(self.agent, prompt)
                
            except Exception as e:
                error[0] = e
                print(f"Error running agent: {e}")
            finally:
                if 'loop' in locals():
                    loop.close()
        
        # Run in a separate thread
        thread = threading.Thread(target=run_agent)
        thread.start()
        thread.join()
        
        if error[0]:
            raise error[0]
        return result[0]
    
    def collect_university_info(self, university_url: str, max_pages: int = 20, organization_name: str = "") -> Dict:
        """Main method to collect university information with section-based analysis"""
        print(f"Starting to collect information from: {university_url}")
        
        # Scrape the website
        scraped_data = self.scraper.crawl_website(university_url, max_pages)
        
        # Extract organization name from first page if not provided
        if not organization_name and scraped_data:
            first_page = scraped_data[0]
            if 'title' in first_page and 'error' not in first_page:
                # Try to extract organization name from title
                title = first_page['title']
                # Remove common suffixes
                for suffix in [' - Home', ' | Home', ' - Official', ' | Official', ' - University', ' | University']:
                    if title.endswith(suffix):
                        organization_name = title[:-len(suffix)]
                        break
                if not organization_name:
                    organization_name = title
        
        # Run section-based analysis
        print("📊 Running section-based analysis...")
        section_analysis = self.section_analyzer.analyze_content_for_sections(scraped_data, organization_name)
        
        # Also run traditional AI analysis for comparison
        print("🤖 Running traditional AI analysis...")
        combined_content = ""
        for page in scraped_data:
            if 'content' in page and 'error' not in page:
                combined_content += f"\n\n--- Page: {page['title']} ({page['url']}) ---\n"
                combined_content += page['content'][:2000]  # Limit content per page
        
        prompt = f"""
        Analyze the following university website content and extract relevant information in a structured format.
        
        Website URL: {university_url}
        Number of pages scraped: {len(scraped_data)}
        
        Content to analyze:
        {combined_content}
        
        Please provide a comprehensive analysis with verbatim quotes where relevant.
        """
        
        try:
            result = self._run_agent_in_thread(prompt)
            traditional_analysis = result.final_output
        except Exception as e:
            print(f"⚠️ Traditional AI analysis failed: {e}")
            traditional_analysis = f"Traditional AI analysis failed: {str(e)}"
        
        return {
            'university_url': university_url,
            'organization_name': organization_name,
            'scraped_pages': len(scraped_data),
            'raw_data': scraped_data,
            'section_analysis': section_analysis,
            'traditional_analysis': traditional_analysis,
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
