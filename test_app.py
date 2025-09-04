#!/usr/bin/env python3
"""
Simple test script to verify the application components work correctly.
Run this before using the main application.
"""

import os
import sys
from website_scraper import WebsiteScraper, UniversityInfoAgent
from config import OPENAI_API_KEY

def test_imports():
    """Test that all required modules can be imported"""
    print("Testing imports...")
    try:
        import streamlit as st
        print("✅ Streamlit imported successfully")
    except ImportError as e:
        print(f"❌ Streamlit import failed: {e}")
        return False
    
    try:
        from agents import Agent, Runner
        print("✅ OpenAI Agents SDK imported successfully")
    except ImportError as e:
        print(f"❌ OpenAI Agents SDK import failed: {e}")
        return False
    
    try:
        from playwright.async_api import async_playwright
        import bs4
        print("✅ Playwright and web scraping libraries imported successfully")
    except ImportError as e:
        print(f"❌ Playwright/web scraping libraries import failed: {e}")
        return False
    
    return True

def test_config():
    """Test configuration loading"""
    print("\nTesting configuration...")
    
    if OPENAI_API_KEY:
        print("✅ OpenAI API key found")
        return True
    else:
        print("❌ OpenAI API key not found")
        print("Please set OPENAI_API_KEY environment variable or create a .env file")
        return False

def test_website_scraper():
    """Test basic website scraping functionality"""
    print("\nTesting website scraper...")
    
    try:
        scraper = WebsiteScraper()
        print("✅ WebsiteScraper initialized successfully")
        
        # Test with a simple, reliable website
        test_url = "https://httpbin.org/html"
        print(f"Testing with: {test_url}")
        
        # Start browser for testing
        scraper.start_browser()
        result = scraper.scrape_page(test_url)
        scraper.close_browser()
        
        if 'error' not in result:
            print("✅ Basic scraping test passed")
            print(f"   - Title: {result.get('title', 'No title')}")
            print(f"   - Word count: {result.get('word_count', 0)}")
            return True
        else:
            print(f"❌ Scraping test failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ WebsiteScraper test failed: {e}")
        return False

def test_agent_initialization():
    """Test AI agent initialization (without making API calls)"""
    print("\nTesting AI agent initialization...")
    
    if not OPENAI_API_KEY:
        print("⚠️ Skipping agent test - no API key")
        return True
    
    try:
        agent = UniversityInfoAgent()
        print("✅ UniversityInfoAgent initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Agent initialization failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Running University Website Information Collector Tests\n")
    
    tests = [
        test_imports,
        test_config,
        test_website_scraper,
        test_agent_initialization
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The application should work correctly.")
        print("\nTo run the application:")
        print("  streamlit run app.py")
    else:
        print("⚠️ Some tests failed. Please check the errors above.")
        print("\nCommon solutions:")
        print("  1. Install missing dependencies: pip install -r requirements.txt")
        print("  2. Set OpenAI API key: export OPENAI_API_KEY=your_key_here")
        print("  3. Check internet connection for web scraping tests")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
