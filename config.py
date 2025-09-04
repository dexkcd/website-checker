import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Application Configuration
MAX_PAGES_TO_SCRAPE = 50
REQUEST_TIMEOUT = 30  # seconds
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Playwright Configuration
PLAYWRIGHT_HEADLESS = False  # Set to True for headless mode, False to see browser
PLAYWRIGHT_VIEWPORT = {'width': 1920, 'height': 1080}
PLAYWRIGHT_WAIT_FOR_NETWORK_IDLE = True
PLAYWRIGHT_EXTRA_WAIT_TIME = 2000  # milliseconds

# Streamlit Configuration
PAGE_TITLE = "University Website Information Collector"
PAGE_ICON = "🎓"
