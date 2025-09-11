# University Website Information Collector

An AI-powered tool that uses the OpenAI Agents SDK to collect and analyze information from university websites. Built with Streamlit for the user interface.

## Features

- 🤖 **AI-Powered Analysis**: Uses OpenAI Agents SDK for intelligent content extraction
- 🎯 **LinkRelevanceAgent**: AI-powered link filtering to focus on relevant content before crawling
- 🕷️ **Smart Web Scraping**: Playwright-powered crawling with requests fallback for maximum compatibility
- 📊 **Structured Data**: Organizes information into clear categories
- 📸 **Visual Screenshots**: Captures full-page screenshots for visual reference
- 🎯 **Section-Based Analysis**: Categorizes content by predefined sections (mission, structure, etc.)
- 🌐 **Translation Support**: Built-in translation capabilities with fallback mode
- 💾 **Export Options**: Download results as JSON or CSV
- 🎨 **Modern UI**: Clean, intuitive Streamlit interface
- ⚡ **Real-time Progress**: Live updates during collection process

## What It Collects

The AI agent focuses on extracting:

1. **University Information**: Name, basic details, history
2. **Academic Programs**: Departments, degrees, courses
3. **Admissions**: Requirements, procedures, deadlines
4. **Faculty & Staff**: Directory information, research areas
5. **Campus Facilities**: Buildings, services, amenities
6. **Contact Information**: Addresses, phone numbers, emails
7. **Tuition & Fees**: Cost information, financial aid
8. **Student Life**: Activities, organizations, housing
9. **Research Opportunities**: Labs, projects, funding
10. **Important Dates**: Deadlines, events, academic calendar

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd website-checker
   ```

2. **Install dependencies**:
   ```bash
   # Option 1: Use the automated installer (recommended)
   python3 install.py
   
   # Option 2: Manual installation
   pip install -r requirements.txt
   playwright install chromium
   
   # Option 3: If you have compilation issues (Python 3.13)
   pip install -r requirements-minimal.txt
   playwright install chromium
   ```

3. **Set up environment variables**:
   Create a `.env` file in the project root:
   ```bash
   OPENAI_API_KEY=your_openai_api_key_here
   ```

4. **Run the application**:
   ```bash
   streamlit run app.py
   ```
   
   Or use the startup script:
   ```bash
   ./run.sh
   ```

## Usage

1. **Start the application** by running `streamlit run app.py`
2. **Enter a university website URL** in the sidebar
3. **Configure options**:
   - Maximum pages to scrape (5-50)
   - Show raw data toggle
   - Auto-export option
4. **Click "Start Information Collection"**
5. **Review results**:
   - AI analysis in structured format
   - Raw scraped data
   - Summary statistics
6. **Export data** as JSON or CSV

## Configuration

The application can be configured through the `config.py` file:

- `MAX_PAGES_TO_SCRAPE`: Default maximum pages (50)
- `REQUEST_TIMEOUT`: HTTP request timeout (30 seconds)
- `USER_AGENT`: Browser user agent string
- `PAGE_TITLE`: Streamlit page title
- `PAGE_ICON`: Streamlit page icon

## Technical Details

### Architecture

- **Frontend**: Streamlit web interface
- **AI Agent**: OpenAI Agents SDK for content analysis
- **Web Scraping**: Playwright for JavaScript-enabled content extraction
- **Data Storage**: In-memory with export capabilities

### Key Components

1. **`app.py`**: Main Streamlit application
2. **`website_scraper.py`**: Core scraping and AI agent logic
3. **`config.py`**: Application configuration
4. **`requirements.txt`**: Python dependencies

### AI Agent Features

The application includes multiple specialized AI agents:

**LinkRelevanceAgent**
- Evaluates links before crawling to determine relevance
- Analyzes URL structure, context, and target sections
- Provides relevance scores and reasoning for each link
- Reduces noise by filtering out irrelevant pages

**PageAnalystAgent**
- Analyzes page content for section relevance
- Provides detailed reasoning for categorization decisions
- Extracts key themes and supporting quotes
- Scores pages on relevance to specific organizational sections

**UniversityInfoAgent**
- Extracts relevant information from unstructured content
- Provides verbatim quotes when possible
- Organizes data into structured categories
- Handles various website layouts and content types

### Scraping Technology

The application uses a dual-scraper approach for maximum compatibility:

**Primary: Playwright Scraper**
- **JavaScript Support**: Handles dynamic content loaded via JavaScript
- **Real Browser**: Uses actual Chromium browser for accurate rendering
- **Network Control**: Waits for network requests to complete
- **Anti-Detection**: Configured to avoid common bot detection methods

**Fallback: Requests Scraper**
- **High Compatibility**: Works on all systems without browser dependencies
- **Fast Setup**: No browser installation required
- **Reliable**: Traditional HTTP requests for static content
- **Lightweight**: Lower resource usage

The application automatically detects and handles event loop conflicts, falling back to the requests scraper when needed.

## Ethical Considerations

- **Respectful Scraping**: Implements delays between requests
- **Rate Limiting**: Configurable page limits
- **User Agent**: Identifies as a legitimate browser
- **Error Handling**: Graceful failure for inaccessible pages

## Troubleshooting

### Common Issues

1. **API Key Error**: Ensure `OPENAI_API_KEY` is set in your environment
2. **Connection Timeout**: Some websites may block automated requests
3. **Memory Usage**: Large websites may require reducing max pages
4. **Content Filtering**: Some content may be behind authentication

### Performance Tips

- Start with smaller page limits (10-20) for testing
- Use specific university subdomain URLs for focused results
- Monitor memory usage for very large websites

## License

This project is open source and available under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## Troubleshooting

### Python 3.13 Compatibility Issues

If you're using Python 3.13 and encounter compilation errors with `lxml` or `greenlet`:

1. **Use the automated installer**:
   ```bash
   python3 install.py
   ```

2. **Try minimal requirements**:
   ```bash
   pip install -r requirements-minimal.txt
   ```

3. **Use Python 3.11 or 3.12** (recommended):
   ```bash
   # Using pyenv
   pyenv install 3.11.7
   pyenv local 3.11.7
   ```

4. **Install system dependencies** (macOS):
   ```bash
   brew install libxml2 libxslt
   ```

### Common Installation Issues

- **"Failed building wheel"**: Try `pip install --upgrade pip setuptools wheel`
- **"ModuleNotFoundError"**: Ensure you're in the correct virtual environment
- **"Browser not found"**: Run `playwright install chromium`
- **Permission errors**: Use `chmod +x run.sh` or `chmod +x install.py`

## Support

For questions or issues, please create an issue in the repository or contact the maintainers.
