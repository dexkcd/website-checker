import streamlit as st
import os
import json
import time
from datetime import datetime
import pandas as pd
from config import PAGE_TITLE, PAGE_ICON, OPENAI_API_KEY
from translation_utils import TranslationManager, LANGUAGE_OPTIONS, get_language_name

# Try to import the main scraper, fallback to simple scraper if there are issues
try:
    from website_scraper import UniversityInfoAgent
    SCRAPER_TYPE = "playwright"
except Exception as e:
    st.warning(f"⚠️ Playwright scraper failed to load: {str(e)}")
    st.info("🔄 Falling back to simple requests-based scraper...")
    from website_scraper_simple import SimpleUniversityInfoAgent as UniversityInfoAgent
    SCRAPER_TYPE = "requests"

# Page configuration
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .info-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
    }
    .error-box {
        background-color: #f8d7da;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #dc3545;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def check_api_key():
    """Check if OpenAI API key is configured"""
    if not OPENAI_API_KEY:
        st.error("⚠️ OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
        st.info("You can create a .env file with: OPENAI_API_KEY=your_api_key_here")
        return False
    return True

def display_section_analysis(section_analysis, target_lang_code='en', enable_translation=False):
    """Display the section-based analysis results with optional translation"""
    sections = section_analysis.get('sections', [])
    
    # Initialize translation manager if needed
    translator = None
    if enable_translation and target_lang_code != 'en':
        translator = TranslationManager()
    
    for i, section in enumerate(sections):
        section_name = section['section_name']
        section_definition = section['section_definition']
        
        # Translate if needed
        if translator and target_lang_code != 'en':
            section_name = translator.translate_text(section_name, target_lang_code)
            section_definition = translator.translate_text(section_definition, target_lang_code)
        
        st.markdown(f"### {i+1}. {section_name}")
        st.markdown(f"*{section_definition}*")
        
        # Show section-level statistics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Relevant Pages", section.get('total_relevant_pages', 0))
        with col2:
            st.metric("Avg Relevance Score", section.get('average_relevance_score', 0))
        with col3:
            coverage_quality = section.get('coverage_quality', 'unknown')
            if coverage_quality == 'excellent':
                st.success(f"📊 Coverage: {coverage_quality.title()}")
            elif coverage_quality == 'good':
                st.info(f"📊 Coverage: {coverage_quality.title()}")
            else:
                st.warning(f"📊 Coverage: {coverage_quality.title()}")
        
        subsections = section.get('subsections', [])
        for j, subsection in enumerate(subsections):
            subsection_name = subsection['subsection_name']
            subsection_definition = subsection['subsection_definition']
            
            # Translate if needed
            if translator and target_lang_code != 'en':
                subsection_name = translator.translate_text(subsection_name, target_lang_code)
                subsection_definition = translator.translate_text(subsection_definition, target_lang_code)
            
            st.markdown(f"#### {i+1}.{j+1} {subsection_name}")
            st.markdown(f"*{subsection_definition}*")
            
            relevant_pages = subsection.get('relevant_pages', [])
            
            # Show subsection statistics
            if relevant_pages:
                subsection_avg_score = sum(page.get('relevance_score', 0) for page in relevant_pages) / len(relevant_pages)
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Pages Found", len(relevant_pages))
                with col2:
                    st.metric("Avg Score", f"{subsection_avg_score:.1f}")
                
                # Display relevant pages
                for k, page in enumerate(relevant_pages):
                    page_title = page['page_title']
                    page_content = page['content']
                    
                    # Translate if needed
                    if translator and target_lang_code != 'en':
                        page_title = translator.translate_text(page_title, target_lang_code)
                        page_content = translator.translate_text(page_content, target_lang_code)
                    
                    with st.expander(f"📄 {page_title} (Relevance: {page['relevance_score']})"):
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            st.markdown(f"**URL:** {page['url']}")
                            st.markdown(f"**Word Count:** {page['word_count']}")
                            
                            # Show AI reasoning
                            if page.get('ai_reasoning'):
                                st.markdown("**🤖 AI Analysis:**")
                                st.info(page['ai_reasoning'])
                            
                            # Show key themes
                            if page.get('key_themes'):
                                st.markdown("**🎯 Key Themes:**")
                                themes_display = ", ".join(page['key_themes'][:5])
                                if len(page['key_themes']) > 5:
                                    themes_display += f" (+{len(page['key_themes']) - 5} more)"
                                st.markdown(f"`{themes_display}`")
                            
                            # Show supporting quotes
                            if page.get('supporting_quotes'):
                                with st.expander("📝 Supporting Quotes"):
                                    for quote in page['supporting_quotes'][:3]:
                                        st.markdown(f"• \"{quote}\"")
                                    if len(page['supporting_quotes']) > 3:
                                        st.markdown(f"... and {len(page['supporting_quotes']) - 3} more quotes")
                            
                            # Show confidence level
                            if page.get('confidence'):
                                confidence = page['confidence']
                                if confidence == 'high':
                                    st.success(f"🎯 Confidence: {confidence.title()}")
                                elif confidence == 'medium':
                                    st.info(f"🎯 Confidence: {confidence.title()}")
                                else:
                                    st.warning(f"🎯 Confidence: {confidence.title()}")
                            
                            # Show translation status
                            if translator and target_lang_code != 'en':
                                st.markdown(f"🌐 **Translated to {get_language_name(target_lang_code)}**")
                            
                            st.markdown("**Content:**")
                            st.text_area("", page_content, height=200, key=f"content_{i}_{j}_{k}")
                        
                        with col2:
                            if page.get('screenshot_path') and os.path.exists(page['screenshot_path']):
                                st.markdown("**Screenshot:**")
                                st.image(page['screenshot_path'], caption=page_title, use_container_width=True)
                            else:
                                st.markdown("📷 *Screenshot not available*")
            else:
                no_pages_msg = "No relevant pages found for this subsection."
                if translator and target_lang_code != 'en':
                    no_pages_msg = translator.translate_text(no_pages_msg, target_lang_code)
                st.info(no_pages_msg)
        
        st.markdown("---")

def display_results(data, target_lang_code='en', enable_translation=False):
    """Display the collected university information with optional translation"""
    st.markdown("## 📊 Collection Results")
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Pages Scraped", data['scraped_pages'])
    with col2:
        st.metric("Collection Time", data['collection_timestamp'])
    with col3:
        total_words = sum(page.get('word_count', 0) for page in data['raw_data'] if 'word_count' in page)
        st.metric("Total Words", f"{total_words:,}")
    with col4:
        successful_pages = len([page for page in data['raw_data'] if 'error' not in page])
        st.metric("Successful Pages", successful_pages)
    
    # Organization name
    if data.get('organization_name'):
        st.markdown(f"### 🏢 {data['organization_name']}")
    
    # Translation status
    if enable_translation and target_lang_code != 'en':
        st.info(f"🌐 Content is being translated to {get_language_name(target_lang_code)}")
    
    # Section-based analysis
    if 'section_analysis' in data:
        st.markdown("## 📋 Section-Based Analysis")
        
        # Show overall analysis summary
        section_analysis = data['section_analysis']
        sections = section_analysis.get('sections', [])
        analysis_method = section_analysis.get('analysis_method', 'Unknown')
        
        # Show analysis method
        if analysis_method == 'AI Section-Centric Analyst':
            st.success("🤖 Analysis powered by AI Section-Centric Analyst")
        elif analysis_method == 'AI Page Analyst':
            st.success("🤖 Analysis powered by AI Page Analyst")
        else:
            st.info(f"📊 Analysis method: {analysis_method}")
        
        if sections:
            total_sections = len(sections)
            sections_with_content = len([s for s in sections if s.get('total_relevant_pages', 0) > 0])
            overall_avg_score = sum(s.get('average_relevance_score', 0) for s in sections) / total_sections if total_sections > 0 else 0
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Sections", total_sections)
            with col2:
                st.metric("Sections with Content", sections_with_content)
            with col3:
                st.metric("Overall Avg Score", f"{overall_avg_score:.1f}")
            with col4:
                coverage_pct = (sections_with_content / total_sections * 100) if total_sections > 0 else 0
                st.metric("Coverage %", f"{coverage_pct:.0f}%")
        
        display_section_analysis(data['section_analysis'], target_lang_code, enable_translation)
    
    # Traditional analysis
    if 'traditional_analysis' in data:
        st.markdown("## 🤖 Traditional AI Analysis")
        st.markdown('<div class="success-box">', unsafe_allow_html=True)
        st.markdown(data['traditional_analysis'])
        st.markdown('</div>', unsafe_allow_html=True)
    elif 'structured_analysis' in data:
        st.markdown("## 🎓 AI Analysis Results")
        st.markdown('<div class="success-box">', unsafe_allow_html=True)
        st.markdown(data['structured_analysis'])
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Raw data tabs
    st.markdown("## 📋 Raw Data")
    tab1, tab2, tab3 = st.tabs(["Page Summary", "Full Content", "Export Options"])
    
    with tab1:
        # Create a summary table
        summary_data = []
        for page in data['raw_data']:
            if 'error' not in page:
                # Show the actual URL that was loaded
                display_url = page.get('actual_url', page.get('normalized_url', page.get('url', '')))
                screenshot_status = "✅" if page.get('screenshot_path') else "❌"
                summary_data.append({
                    'Title': page.get('title', 'No title'),
                    'URL': display_url,
                    'Word Count': page.get('word_count', 0),
                    'Screenshot': screenshot_status,
                    'Status': 'Success'
                })
            else:
                summary_data.append({
                    'Title': 'Error',
                    'URL': page.get('url', ''),
                    'Word Count': 0,
                    'Screenshot': '❌',
                    'Status': f"Error: {page.get('error', 'Unknown error')}"
                })
        
        if summary_data:
            df = pd.DataFrame(summary_data)
            st.dataframe(df, use_container_width=True)
    
    with tab2:
        # Display full content for each page
        translator = None
        if enable_translation and target_lang_code != 'en':
            translator = TranslationManager()
        
        for i, page in enumerate(data['raw_data']):
            page_title = page.get('title', 'No title')
            page_content = page.get('content', '')
            
            # Translate if needed
            if translator and target_lang_code != 'en':
                page_title = translator.translate_text(page_title, target_lang_code)
                page_content = translator.translate_text(page_content, target_lang_code)
            
            with st.expander(f"Page {i+1}: {page_title}"):
                if 'error' not in page:
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.write(f"**Original URL:** {page.get('url', '')}")
                        if page.get('normalized_url') and page.get('normalized_url') != page.get('url'):
                            st.write(f"**Normalized URL:** {page.get('normalized_url', '')}")
                        if page.get('actual_url') and page.get('actual_url') != page.get('normalized_url'):
                            st.write(f"**Actual URL Loaded:** {page.get('actual_url', '')}")
                        st.write(f"**Word Count:** {page.get('word_count', 0)}")
                        st.write(f"**Scraped At:** {page.get('scraped_at', '')}")
                        
                        # Show translation status
                        if translator and target_lang_code != 'en':
                            st.write(f"🌐 **Translated to {get_language_name(target_lang_code)}**")
                        
                        st.write("**Content:**")
                        st.text_area("", page_content, height=200, key=f"content_{i}")
                    
                    with col2:
                        if page.get('screenshot_path') and os.path.exists(page.get('screenshot_path')):
                            st.write("**Screenshot:**")
                            st.image(page.get('screenshot_path'), caption=page_title, use_container_width=True)
                        else:
                            st.write("📷 *Screenshot not available*")
                else:
                    st.error(f"Error scraping this page: {page.get('error', 'Unknown error')}")
    
    with tab3:
        st.markdown("### 📁 Export Options")
        
        # JSON export
        json_data = json.dumps(data, indent=2, ensure_ascii=False)
        st.download_button(
            label="📥 Download as JSON",
            data=json_data,
            file_name=f"university_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
        
        # CSV export for summary
        if data['raw_data']:
            summary_data = []
            for page in data['raw_data']:
                if 'error' not in page:
                    summary_data.append({
                        'title': page.get('title', ''),
                        'url': page.get('url', ''),
                        'word_count': page.get('word_count', 0),
                        'scraped_at': page.get('scraped_at', '')
                    })
            
            if summary_data:
                df = pd.DataFrame(summary_data)
                csv_data = df.to_csv(index=False)
                st.download_button(
                    label="📊 Download Summary as CSV",
                    data=csv_data,
                    file_name=f"university_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )

def main():
    # Header
    st.markdown(f'<div class="main-header">{PAGE_ICON} {PAGE_TITLE}</div>', unsafe_allow_html=True)
    
    # Check API key
    if not check_api_key():
        st.stop()
    
    # Sidebar
    with st.sidebar:
        st.markdown("## ⚙️ Configuration")
        
        # Show scraper type
        if SCRAPER_TYPE == "playwright":
            st.success("🕷️ Using Playwright scraper (JavaScript support)")
            st.info("🤖 LinkRelevanceAgent enabled - AI-powered link filtering")
        else:
            st.info("🌐 Using Requests scraper (fallback mode)")
            st.warning("⚠️ LinkRelevanceAgent not available in fallback mode")
        
        # University URL input
        university_url = st.text_input(
            "🏫 University Website URL",
            placeholder="https://example-university.edu",
            help="Enter the main URL of the university website you want to analyze"
        )
        
        # Organization name input
        organization_name = st.text_input(
            "🏢 Organization Name (Optional)",
            placeholder="Stanford University",
            help="Enter the organization name to customize section titles"
        )
        
        # Max pages to scrape
        max_pages = st.slider(
            "📄 Maximum Pages to Scrape",
            min_value=5,
            max_value=50,
            value=20,
            help="Limit the number of pages to scrape to avoid overwhelming the server"
        )
        
        # Translation options
        st.markdown("### 🌐 Translation Options")
        
        # Check if translation is available
        try:
            from translation_utils import TranslationManager
            test_translator = TranslationManager()
            translation_available = True
        except Exception as e:
            translation_available = False
            st.warning(f"⚠️ Translation not available: {str(e)}")
        
        if translation_available:
            enable_translation = st.checkbox("Enable Translation", value=False, help="Translate content to another language")
            
            if enable_translation:
                target_language = st.selectbox(
                    "Target Language",
                    options=list(LANGUAGE_OPTIONS.keys()),
                    index=0,  # Default to English
                    help="Select the language to translate content to"
                )
                target_lang_code = LANGUAGE_OPTIONS[target_language]
            else:
                target_lang_code = 'en'
        else:
            enable_translation = False
            target_lang_code = 'en'
            st.info("🌐 Translation feature is not available. Content will be displayed in original language.")
        
        # Advanced options
        st.markdown("### 🔧 Advanced Options")
        show_raw_data = st.checkbox("Show Raw Data", value=True, help="Display raw scraped content")
        auto_export = st.checkbox("Auto Export", value=False, help="Automatically download results")
        
        st.markdown("---")
        st.markdown("### ℹ️ About")
        st.info("""
        This tool uses AI to collect and analyze information from university websites.
        
        **Features:**
        - Intelligent web scraping with Playwright
        - AI-powered link relevance filtering
        - AI-powered content analysis
        - Structured data extraction
        - Export to JSON/CSV
        
        **Note:** Be respectful of website terms of service and robots.txt files.
        """)
    
    # Main content area
    if university_url:
        # Validate URL
        if not university_url.startswith(('http://', 'https://')):
            st.error("Please enter a valid URL starting with http:// or https://")
            st.stop()
        
        # Start collection button
        if st.button("🚀 Start Information Collection", type="primary", use_container_width=True):
            with st.spinner("Collecting university information..."):
                try:
                    # Initialize the agent
                    agent = UniversityInfoAgent()
                    
                    # Create progress bar
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # Update progress
                    progress_bar.progress(25)
                    status_text.text("Initializing AI agent...")
                    
                    progress_bar.progress(50)
                    status_text.text("Scraping website content...")
                    
                    # Collect information
                    results = agent.collect_university_info(university_url, max_pages, organization_name)
                    
                    progress_bar.progress(75)
                    status_text.text("Analyzing content with AI...")
                    
                    progress_bar.progress(100)
                    status_text.text("Collection complete!")
                    
                    # Store results in session state
                    st.session_state['collection_results'] = results
                    
                    # Auto export if enabled
                    if auto_export:
                        filename = agent.export_to_json(results)
                        st.success(f"Results automatically saved to {filename}")
                    
                except Exception as e:
                    st.error(f"An error occurred during collection: {str(e)}")
                    st.exception(e)
        
        # Display results if available
        if 'collection_results' in st.session_state:
            display_results(st.session_state['collection_results'], target_lang_code, enable_translation)
    
    else:
        # Welcome message
        st.markdown("""
        <div class="info-box">
        <h3>Welcome to the University Website Information Collector!</h3>
        <p>This AI-powered tool helps you collect and analyze information from university websites.</p>
        
        <h4>How to use:</h4>
        <ol>
            <li>Enter a university website URL in the sidebar</li>
            <li>Configure scraping options (max pages, etc.)</li>
            <li>Click "Start Information Collection"</li>
            <li>Review the AI analysis and raw data</li>
            <li>Export results as needed</li>
        </ol>
        
        <h4>What it collects:</h4>
        <ul>
            <li>University name and basic information</li>
            <li>Academic programs and departments</li>
            <li>Admission requirements</li>
            <li>Faculty information</li>
            <li>Campus facilities</li>
            <li>Contact information</li>
            <li>And much more!</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
        
        # Example URLs
        st.markdown("### 🌟 Example University Websites")
        example_urls = [
            "https://www.stanford.edu",
            "https://www.mit.edu",
            "https://www.harvard.edu",
            "https://www.berkeley.edu"
        ]
        
        for url in example_urls:
            if st.button(f"Try: {url}", key=f"example_{url}"):
                st.session_state['example_url'] = url
                st.rerun()
        
        if 'example_url' in st.session_state:
            st.info(f"Selected example: {st.session_state['example_url']}")
            st.markdown("Copy this URL to the sidebar input field to get started!")

if __name__ == "__main__":
    main()
