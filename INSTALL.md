# Installation Guide

## Quick Start

1. **Set up your OpenAI API key**:
   ```bash
   export OPENAI_API_KEY=your_api_key_here
   ```

2. **Run the startup script**:
   ```bash
   ./run.sh
   ```

The startup script will:
- Create a virtual environment
- Install all dependencies
- Install Playwright browsers
- Run tests
- Start the application

## Manual Installation

If you prefer to install manually:

1. **Create virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Playwright browsers**:
   ```bash
   playwright install chromium
   ```

4. **Set up environment variables**:
   ```bash
   export OPENAI_API_KEY=your_api_key_here
   ```

5. **Test the installation**:
   ```bash
   python3 test_app.py
   ```

6. **Run the application**:
   ```bash
   streamlit run app.py
   ```

## Troubleshooting

### Common Issues

1. **"ModuleNotFoundError: No module named 'playwright'"**
   - Solution: Run `pip install -r requirements.txt`

2. **"Browser not found" error**
   - Solution: Run `playwright install chromium`

3. **"OPENAI_API_KEY not found"**
   - Solution: Set the environment variable or create a `.env` file

4. **Permission denied on run.sh**
   - Solution: Run `chmod +x run.sh`

5. **Compilation errors with lxml/greenlet (Python 3.13)**
   - Solution: The startup script will automatically try minimal requirements
   - Alternative: Use Python 3.11 or 3.12 instead
   - Or install system dependencies: `brew install libxml2 libxslt` (macOS)

6. **"Failed building wheel" errors**
   - Solution: Try `pip install --upgrade pip setuptools wheel`
   - Or use the minimal requirements: `pip install -r requirements-minimal.txt`

### System Requirements

- Python 3.8 or higher
- 2GB+ RAM (for Playwright browser)
- Internet connection (for downloading browsers and API calls)

### Dependencies

The application requires:
- `streamlit` - Web UI framework
- `openai-agents` - OpenAI Agents SDK
- `playwright` - Web scraping and browser automation
- `beautifulsoup4` - HTML parsing
- `pandas` - Data manipulation
- `python-dotenv` - Environment variable management

## Getting Your OpenAI API Key

1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Sign up or log in
3. Navigate to API Keys section
4. Create a new API key
5. Copy the key and set it as an environment variable

## First Run

After installation, the application will be available at:
- **Local URL**: http://localhost:8501
- **Network URL**: http://your-ip:8501

The interface will guide you through:
1. Entering a university website URL
2. Configuring scraping options
3. Starting the information collection
4. Reviewing and exporting results
