#!/usr/bin/env python3
"""
Simple test script to verify Playwright browser navigation is working
"""

from playwright.sync_api import sync_playwright
from config import PLAYWRIGHT_HEADLESS, PLAYWRIGHT_VIEWPORT, USER_AGENT

def test_browser_navigation():
    """Test basic browser navigation"""
    print("🧪 Testing Playwright browser navigation...")
    
    playwright = None
    browser = None
    context = None
    
    try:
        # Start Playwright
        print("🚀 Starting Playwright...")
        playwright = sync_playwright().start()
        
        # Launch browser
        print("🌐 Launching Chromium browser...")
        browser = playwright.chromium.launch(
            headless=PLAYWRIGHT_HEADLESS,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        
        # Create context
        print("📄 Creating browser context...")
        context = browser.new_context(
            user_agent=USER_AGENT,
            viewport=PLAYWRIGHT_VIEWPORT
        )
        
        # Create page
        print("📄 Creating new page...")
        page = context.new_page()
        
        # Test navigation
        test_url = "https://httpbin.org/html"
        print(f"🔗 Navigating to: {test_url}")
        
        page.goto(test_url, wait_until='domcontentloaded')
        
        # Get current URL
        current_url = page.url
        print(f"✅ Successfully loaded: {current_url}")
        
        # Get page title
        title = page.title()
        print(f"📖 Page title: {title}")
        
        # Get some content
        content = page.content()
        print(f"📄 Page content length: {len(content)} characters")
        
        # Close page
        page.close()
        print("🔒 Page closed")
        
        print("✅ Browser navigation test successful!")
        return True
        
    except Exception as e:
        print(f"❌ Browser navigation test failed: {e}")
        return False
        
    finally:
        # Cleanup
        if context:
            context.close()
        if browser:
            browser.close()
        if playwright:
            playwright.stop()
        print("🧹 Cleanup completed")

def main():
    """Main test function"""
    success = test_browser_navigation()
    if success:
        print("\n🎉 All tests passed! Browser navigation is working correctly.")
    else:
        print("\n⚠️ Tests failed. There may be an issue with Playwright setup.")
    
    return success

if __name__ == "__main__":
    main()
