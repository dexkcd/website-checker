import streamlit as st
import os
import json
import time
from datetime import datetime
import pandas as pd
from config import PAGE_TITLE, PAGE_ICON, OPENAI_API_KEY

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

def display_results(data):
    """Display the collected university information"""
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
    
    # Structured analysis
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
                summary_data.append({
                    'Title': page.get('title', 'No title'),
                    'URL': display_url,
                    'Word Count': page.get('word_count', 0),
                    'Status': 'Success'
                })
            else:
                summary_data.append({
                    'Title': 'Error',
                    'URL': page.get('url', ''),
                    'Word Count': 0,
                    'Status': f"Error: {page.get('error', 'Unknown error')}"
                })
        
        if summary_data:
            df = pd.DataFrame(summary_data)
            st.dataframe(df, use_container_width=True)
    
    with tab2:
        # Display full content for each page
        for i, page in enumerate(data['raw_data']):
            with st.expander(f"Page {i+1}: {page.get('title', 'No title')}"):
                if 'error' not in page:
                    st.write(f"**Original URL:** {page.get('url', '')}")
                    if page.get('normalized_url') and page.get('normalized_url') != page.get('url'):
                        st.write(f"**Normalized URL:** {page.get('normalized_url', '')}")
                    if page.get('actual_url') and page.get('actual_url') != page.get('normalized_url'):
                        st.write(f"**Actual URL Loaded:** {page.get('actual_url', '')}")
                    st.write(f"**Word Count:** {page.get('word_count', 0)}")
                    st.write(f"**Scraped At:** {page.get('scraped_at', '')}")
                    st.write("**Content:**")
                    st.text_area("", page.get('content', ''), height=200, key=f"content_{i}")
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
        else:
            st.info("🌐 Using Requests scraper (fallback mode)")
        
        # University URL input
        university_url = st.text_input(
            "🏫 University Website URL",
            placeholder="https://example-university.edu",
            help="Enter the main URL of the university website you want to analyze"
        )
        
        # Max pages to scrape
        max_pages = st.slider(
            "📄 Maximum Pages to Scrape",
            min_value=5,
            max_value=50,
            value=20,
            help="Limit the number of pages to scrape to avoid overwhelming the server"
        )
        
        # Advanced options
        st.markdown("### 🔧 Advanced Options")
        show_raw_data = st.checkbox("Show Raw Data", value=True, help="Display raw scraped content")
        auto_export = st.checkbox("Auto Export", value=False, help="Automatically download results")
        
        st.markdown("---")
        st.markdown("### ℹ️ About")
        st.info("""
        This tool uses AI to collect and analyze information from university websites.
        
        **Features:**
        - Intelligent web scraping
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
                    results = agent.collect_university_info(university_url, max_pages)
                    
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
            display_results(st.session_state['collection_results'])
    
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
