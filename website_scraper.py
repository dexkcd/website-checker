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
    def __init__(self, screenshots_dir: str = "screenshots", enable_link_filtering: bool = True):
        self.visited_urls: Set[str] = set()
        self.scraped_data: List[Dict] = []
        self.playwright = None
        self.browser: Browser = None
        self.context = None
        self.screenshots_dir = screenshots_dir
        self.enable_link_filtering = enable_link_filtering
        self.link_relevance_agent = LinkRelevanceAgent() if enable_link_filtering else None
        self.target_sections = None
        
        # Create screenshots directory if it doesn't exist
        os.makedirs(self.screenshots_dir, exist_ok=True)
    
    def set_target_sections(self, sections: List[Dict]):
        """Set target sections for link relevance evaluation"""
        self.target_sections = sections
    
    def filter_links_by_relevance(self, links: List[str], current_page_title: str = "", 
                                 current_page_content: str = "", context_text: str = "") -> List[Dict]:
        """Filter links based on relevance using AI agent"""
        if not self.enable_link_filtering or not self.link_relevance_agent:
            # Return all links as relevant if filtering is disabled
            return [{'url': link, 'relevance_score': 5, 'is_worth_checking': True} for link in links]
        
        relevant_links = []
        print(f"🔍 Filtering {len(links)} links for relevance...")
        
        for i, link in enumerate(links):
            try:
                # Get context around the link (this would need to be passed from the scraping method)
                link_context = context_text if context_text else f"Link {i+1} from {current_page_title}"
                
                # Evaluate link relevance
                evaluation = self.link_relevance_agent.evaluate_link_relevance(
                    url=link,
                    context=link_context,
                    current_page_title=current_page_title,
                    current_page_content=current_page_content,
                    target_sections=self.target_sections
                )
                
                # Only include links that are worth checking
                if evaluation.get('is_worth_checking', False):
                    relevant_links.append(evaluation)
                    print(f"✅ Link approved: {link} (Score: {evaluation.get('relevance_score', 0)})")
                else:
                    print(f"❌ Link rejected: {link} (Score: {evaluation.get('relevance_score', 0)})")
                    
            except Exception as e:
                print(f"⚠️ Error evaluating link {link}: {e}")
                # Include link by default if evaluation fails
                relevant_links.append({
                    'url': link, 
                    'relevance_score': 5, 
                    'is_worth_checking': True,
                    'reasoning': f"Evaluation failed: {str(e)}"
                })
        
        print(f"📊 Link filtering complete: {len(relevant_links)}/{len(links)} links approved")
        return relevant_links
        
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
            raw_links = []
            link_contexts = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                # Use the normalized URL for joining
                full_url = urljoin(normalized_url, href)
                if self.is_valid_url(full_url, normalized_url):
                    raw_links.append(full_url)
                    # Extract context around the link
                    link_text = link.get_text(strip=True)
                    parent_text = link.parent.get_text(strip=True) if link.parent else ""
                    context = f"Link text: '{link_text}' | Parent context: '{parent_text[:200]}'"
                    link_contexts.append(context)
            
            print(f"🔗 Found {len(raw_links)} valid links on this page")
            
            # Filter links by relevance if enabled
            if self.enable_link_filtering and self.link_relevance_agent:
                filtered_links_data = self.filter_links_by_relevance(
                    raw_links, 
                    current_page_title=title_text,
                    current_page_content=main_content,
                    context_text="\n".join(link_contexts)
                )
                # Extract just the URLs from the filtered data
                links = [link_data['url'] for link_data in filtered_links_data]
                print(f"🎯 After relevance filtering: {len(links)} links approved for crawling")
            else:
                links = raw_links
            
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
    
    def crawl_website(self, start_url: str, max_pages: int = MAX_PAGES_TO_SCRAPE, target_sections: List[Dict] = None) -> List[Dict]:
        """Crawl website starting from start_url using Playwright"""
        self.visited_urls.clear()
        self.scraped_data.clear()
        
        # Set target sections for link relevance evaluation
        if target_sections:
            self.set_target_sections(target_sections)
            print(f"🎯 Target sections set for link relevance evaluation")
        
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


class PageAnalystAgent:
    def __init__(self):
        self.agent = Agent(
            name="PageRelevanceAnalyst",
            instructions="""
            You are a specialized AI agent that analyzes web pages to determine their relevance to specific organizational sections.
            
            Your task is to:
            1. Analyze page content and determine how well it fits specific section categories
            2. Provide detailed reasoning for your relevance assessments
            3. Score pages on a scale of 1-10 for each section
            4. Identify key themes and topics that make a page relevant
            5. Extract specific quotes that support your analysis
            
            For each page analysis, provide:
            - Relevance score (1-10) for each section
            - Detailed reasoning explaining why the page is or isn't relevant
            - Key themes and topics found
            - Supporting quotes from the content
            - Confidence level in your assessment (high/medium/low)
            
            Be thorough and analytical in your assessments. Consider both explicit mentions and implicit themes.
            """
        )
    
    def _run_agent_in_thread(self, prompt: str):
        """Run the page analyst agent in a separate thread with its own event loop"""
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
                print(f"Error running page analyst agent: {e}")
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
    
    def analyze_section_pages(self, section: Dict, subsection: Dict, all_pages: List[Dict]) -> List[Dict]:
        """Analyze which pages belong to a specific section/subsection using AI"""
        try:
            section_name = section['section_name']
            section_definition = section['section_definition']
            subsection_name = subsection['subsection_name']
            subsection_definition = subsection['subsection_definition']
            
            # Prepare all pages for analysis
            pages_text = ""
            for i, page in enumerate(all_pages):
                if 'error' in page:
                    continue
                pages_text += f"\n{i+1}. {page.get('title', 'No title')}\n"
                pages_text += f"   URL: {page.get('url', '')}\n"
                pages_text += f"   Content: {page.get('content', '')[:1500]}...\n"
            
            prompt = f"""
            You are analyzing which web pages belong to a specific organizational section and subsection.
            
            SECTION TO CLASSIFY FOR:
            Section: {section_name}
            Section Definition: {section_definition}
            
            Subsection: {subsection_name}
            Subsection Definition: {subsection_definition}
            
            PAGES TO EVALUATE:
            {pages_text}
            
            For each page, determine:
            1. Does this page belong to the "{subsection_name}" subsection? (Yes/No)
            2. If yes, what is the relevance score (1-10, where 10 is highly relevant)?
            3. Detailed reasoning for your decision
            4. Key themes/topics that make it relevant (or not)
            5. Supporting quotes from the content
            6. Confidence level in your assessment (high/medium/low)
            
            Format your response as JSON with this structure:
            {{
                "section_name": "{section_name}",
                "subsection_name": "{subsection_name}",
                "relevant_pages": [
                    {{
                        "page_title": "Page Title",
                        "page_url": "https://example.com",
                        "belongs_to_subsection": true,
                        "relevance_score": 8,
                        "reasoning": "Detailed explanation of why this page belongs to this subsection...",
                        "key_themes": ["theme1", "theme2"],
                        "supporting_quotes": ["quote1", "quote2"],
                        "confidence": "high"
                    }},
                    {{
                        "page_title": "Another Page",
                        "page_url": "https://example.com/page2",
                        "belongs_to_subsection": false,
                        "relevance_score": 2,
                        "reasoning": "This page does not contain information relevant to this subsection...",
                        "key_themes": [],
                        "supporting_quotes": [],
                        "confidence": "high"
                    }}
                ]
            }}
            """
            
            print(f"🤖 Analyzing section '{subsection_name}' for relevant pages...")
            result = self._run_agent_in_thread(prompt)
            analysis = result.final_output
            
            # Try to parse JSON response
            try:
                import json
                # Extract JSON from the response (it might be wrapped in markdown)
                if "```json" in analysis:
                    json_start = analysis.find("```json") + 7
                    json_end = analysis.find("```", json_start)
                    json_str = analysis[json_start:json_end].strip()
                else:
                    json_str = analysis
                
                parsed_analysis = json.loads(json_str)
                
                # Convert to the format expected by the UI
                relevant_pages = []
                for page_analysis in parsed_analysis.get('relevant_pages', []):
                    if page_analysis.get('belongs_to_subsection', False) and page_analysis.get('relevance_score', 0) >= 3:
                        # Find the original page data
                        original_page = None
                        for page in all_pages:
                            if page.get('title') == page_analysis.get('page_title'):
                                original_page = page
                                break
                        
                        if original_page:
                            relevant_pages.append({
                                'page_title': original_page.get('title', 'No title'),
                                'url': original_page.get('actual_url', original_page.get('url', '')),
                                'content': original_page.get('content', '')[:1000] + '...' if len(original_page.get('content', '')) > 1000 else original_page.get('content', ''),
                                'screenshot_path': original_page.get('screenshot_path', ''),
                                'screenshot_filename': original_page.get('screenshot_filename', ''),
                                'relevance_score': page_analysis.get('relevance_score', 0),
                                'word_count': original_page.get('word_count', 0),
                                'ai_reasoning': page_analysis.get('reasoning', ''),
                                'key_themes': page_analysis.get('key_themes', []),
                                'supporting_quotes': page_analysis.get('supporting_quotes', []),
                                'confidence': page_analysis.get('confidence', 'medium')
                            })
                
                # Sort by relevance score
                relevant_pages.sort(key=lambda x: x['relevance_score'], reverse=True)
                return relevant_pages[:5]  # Return top 5 most relevant pages
                
            except Exception as e:
                print(f"Error parsing AI response as JSON: {e}")
                return []
                
        except Exception as e:
            print(f"Error in section analysis: {e}")
            return []


class SectionBasedAnalyzer:
    def __init__(self, sections_config_path: str = "settings/crawl_sections.json", enable_link_filtering: bool = True):
        self.sections_config = self.load_sections_config(sections_config_path)
        self.scraper = WebsiteScraper(enable_link_filtering=enable_link_filtering)
        self.page_analyst = PageAnalystAgent()
        
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
        """Analyze scraped content and organize it by sections using AI section-centric analysis"""
        print("🔍 Analyzing content for sections using AI section-centric analysis...")
        
        # Prepare sections configuration
        sections_config = []
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
                
                subsections.append({
                    'subsection_name': subsection_name,
                    'subsection_definition': subsection['subsection_definition']
                })
            
            sections_config.append({
                'section_name': section_name,
                'section_definition': section['section_definition'],
                'subsections': subsections
            })
        
        # Analyze each section and find relevant pages
        sections = []
        total_subsections = sum(len(section.get('subsections', [])) for section in sections_config)
        current_subsection = 0
        
        for section_config in sections_config:
            section_name = section_config['section_name']
            section_definition = section_config['section_definition']
            
            print(f"\n📋 Analyzing section: {section_name}")
            
            # Process subsections
            subsections = []
            for subsection_config in section_config.get('subsections', []):
                current_subsection += 1
                subsection_name = subsection_config['subsection_name']
                subsection_definition = subsection_config['subsection_definition']
                
                print(f"  🔍 Analyzing subsection {current_subsection}/{total_subsections}: {subsection_name}")
                
                # Use AI to find pages that belong to this subsection
                relevant_pages = self.page_analyst.analyze_section_pages(
                    section_config, 
                    subsection_config, 
                    scraped_data
                )
                
                subsections.append({
                    'subsection_name': subsection_name,
                    'subsection_definition': subsection_definition,
                    'relevant_pages': relevant_pages
                })
                
                # Show progress
                progress = (current_subsection / total_subsections) * 100
                print(f"  🔄 Analysis Progress: {progress:.1f}%")
            
            # Calculate section-level statistics
            total_pages = sum(len(subsection.get('relevant_pages', [])) for subsection in subsections)
            avg_relevance = 0
            if total_pages > 0:
                all_scores = []
                for subsection in subsections:
                    for page in subsection.get('relevant_pages', []):
                        all_scores.append(page.get('relevance_score', 0))
                avg_relevance = sum(all_scores) / len(all_scores) if all_scores else 0
            
            sections.append({
                'section_name': section_name,
                'section_definition': section_definition,
                'subsections': subsections,
                'total_relevant_pages': total_pages,
                'average_relevance_score': round(avg_relevance, 2),
                'coverage_quality': 'excellent' if avg_relevance >= 7 else 'good' if avg_relevance >= 4 else 'limited'
            })
        
        return {
            'organization_name': organization_name,
            'sections': sections,
            'total_pages_scraped': len(scraped_data),
            'analysis_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'analysis_method': 'AI Section-Centric Analyst'
        }
    


class LinkRelevanceAgent:
    def __init__(self):
        self.agent = Agent(
            name="LinkRelevanceAnalyst",
            instructions="""
            You are a specialized AI agent that determines whether a link is worth checking based on its context and URL.
            
            Your task is to:
            1. Analyze the URL structure and content to predict relevance
            2. Consider the context where the link appears (surrounding text, page content)
            3. Evaluate if the link might lead to content relevant to specific organizational sections
            4. Provide a relevance score and detailed reasoning
            
            For each link evaluation, consider:
            - URL path structure and keywords
            - File extensions (avoid PDFs, images, etc. unless relevant)
            - Context clues from surrounding text
            - Likelihood of containing relevant organizational information
            - Potential for finding information about specific sections like:
              * General information and history
              * Mission and societal impact
              * Structure and research
              * Working at the organization
              * Living and working in the location
            
            Provide:
            - Relevance score (1-10, where 10 is highly relevant)
            - Detailed reasoning for your decision
            - Confidence level (high/medium/low)
            - Specific aspects that make it relevant or not
            - Suggested priority level for crawling (high/medium/low)
            
            Be conservative but not overly restrictive. Prefer false positives over false negatives.
            """
        )
    
    def _run_agent_in_thread(self, prompt: str):
        """Run the link relevance agent in a separate thread with its own event loop"""
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
                print(f"Error running link relevance agent: {e}")
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
    
    def evaluate_link_relevance(self, url: str, context: str = "", current_page_title: str = "", 
                              current_page_content: str = "", target_sections: List[Dict] = None) -> Dict:
        """Evaluate if a link is worth checking based on URL and context"""
        try:
            # Prepare context information
            context_info = f"Current page title: {current_page_title}\n"
            context_info += f"Context around link: {context}\n"
            context_info += f"Current page content preview: {current_page_content[:500]}...\n"
            
            # Add target sections if provided
            sections_info = ""
            if target_sections:
                sections_info = "\nTarget sections to look for:\n"
                for section in target_sections:
                    sections_info += f"- {section.get('section_name', '')}: {section.get('section_definition', '')}\n"
                    for subsection in section.get('subsections', []):
                        sections_info += f"  - {subsection.get('subsection_name', '')}: {subsection.get('subsection_definition', '')}\n"
            
            prompt = f"""
            Evaluate the relevance of this link for organizational information gathering:
            
            URL: {url}
            
            {context_info}
            
            {sections_info}
            
            Please analyze this link and provide:
            1. Relevance score (1-10)
            2. Detailed reasoning for your decision
            3. Confidence level (high/medium/low)
            4. Specific aspects that make it relevant or not
            5. Priority level for crawling (high/medium/low)
            6. Predicted content type based on URL structure
            7. Key indicators that suggest relevance
            
            Format your response as JSON:
            {{
                "url": "{url}",
                "relevance_score": 7,
                "reasoning": "Detailed explanation of why this link is relevant...",
                "confidence": "high",
                "priority": "medium",
                "predicted_content_type": "About page or organizational information",
                "key_indicators": ["about", "organization", "mission"],
                "is_worth_checking": true
            }}
            """
            
            print(f"🔍 Evaluating link relevance: {url}")
            result = self._run_agent_in_thread(prompt)
            analysis = result.final_output
            
            # Try to parse JSON response
            try:
                import json
                # Extract JSON from the response (it might be wrapped in markdown)
                if "```json" in analysis:
                    json_start = analysis.find("```json") + 7
                    json_end = analysis.find("```", json_start)
                    json_str = analysis[json_start:json_end].strip()
                else:
                    json_str = analysis
                
                parsed_analysis = json.loads(json_str)
                
                # Ensure all required fields are present
                return {
                    'url': url,
                    'relevance_score': parsed_analysis.get('relevance_score', 0),
                    'reasoning': parsed_analysis.get('reasoning', 'No reasoning provided'),
                    'confidence': parsed_analysis.get('confidence', 'medium'),
                    'priority': parsed_analysis.get('priority', 'low'),
                    'predicted_content_type': parsed_analysis.get('predicted_content_type', 'Unknown'),
                    'key_indicators': parsed_analysis.get('key_indicators', []),
                    'is_worth_checking': parsed_analysis.get('is_worth_checking', False)
                }
                
            except Exception as e:
                print(f"Error parsing link relevance response as JSON: {e}")
                # Fallback to basic analysis
                return {
                    'url': url,
                    'relevance_score': 5,
                    'reasoning': f"Could not parse AI response: {analysis}",
                    'confidence': 'low',
                    'priority': 'low',
                    'predicted_content_type': 'Unknown',
                    'key_indicators': [],
                    'is_worth_checking': True  # Default to checking if we can't parse
                }
                
        except Exception as e:
            print(f"Error in link relevance evaluation: {e}")
            return {
                'url': url,
                'relevance_score': 5,
                'reasoning': f"Error during evaluation: {str(e)}",
                'confidence': 'low',
                'priority': 'low',
                'predicted_content_type': 'Unknown',
                'key_indicators': [],
                'is_worth_checking': True  # Default to checking on error
            }


class UniversityInfoAgent:
    def __init__(self):
        self.scraper = WebsiteScraper()
        self.section_analyzer = SectionBasedAnalyzer()
        self.link_relevance_agent = LinkRelevanceAgent()
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
            
            For each piece of information you extract:
            - Provide verbatim quotes from the source material when possible
            - Explain why this information is relevant to the specific section
            - Include the source URL and page title for reference
            - Rate the confidence level of the information (high/medium/low)
            - Note any potential biases or limitations in the source
            
            Organize the information in a clear, structured format with proper reasoning for each categorization.
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
        
        # Prepare sections configuration for link relevance evaluation
        sections_config = []
        for section in self.section_analyzer.sections_config.get('sections', []):
            section_name = section['section_name']
            if '[organization name]' in section_name and organization_name:
                section_name = section_name.replace('[organization name]', organization_name)
            
            # Process subsections
            subsections = []
            for subsection in section.get('subsection', []):
                subsection_name = subsection['subsection_name']
                if '[organization name]' in subsection_name and organization_name:
                    subsection_name = subsection_name.replace('[organization name]', organization_name)
                
                subsections.append({
                    'subsection_name': subsection_name,
                    'subsection_definition': subsection['subsection_definition']
                })
            
            sections_config.append({
                'section_name': section_name,
                'section_definition': section['section_definition'],
                'subsections': subsections
            })
        
        # Scrape the website with target sections for link relevance evaluation
        scraped_data = self.scraper.crawl_website(university_url, max_pages, sections_config)
        
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
        
        For your analysis, please:
        1. Extract information and organize it by relevant categories
        2. For each piece of information, explain WHY it belongs to that category
        3. Provide verbatim quotes from the source material
        4. Include confidence levels (high/medium/low) for each piece of information
        5. Note the source URL and page title for each piece of information
        6. Identify any potential gaps or missing information
        7. Suggest which sections might need more detailed analysis
        
        Focus on providing clear reasoning for your categorization decisions.
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
