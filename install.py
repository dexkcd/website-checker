#!/usr/bin/env python3
"""
Installation script for University Website Information Collector
Handles Python version compatibility and dependency installation
"""

import sys
import subprocess
import os
import platform

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 or higher is required")
        return False
    
    if version.major == 3 and version.minor == 13:
        print("⚠️  Python 3.13 detected - some packages may have compatibility issues")
        print("   Consider using Python 3.11 or 3.12 for better compatibility")
    
    print("✅ Python version is compatible")
    return True

def install_requirements():
    """Install requirements with fallback options"""
    print("\n📥 Installing dependencies...")
    
    # Try main requirements first
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True, text=True)
        print("✅ Main requirements installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print("⚠️  Main requirements failed, trying minimal requirements...")
        print(f"   Error: {e.stderr}")
    
    # Try minimal requirements
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements-minimal.txt"], 
                      check=True, capture_output=True, text=True)
        print("✅ Minimal requirements installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print("❌ Minimal requirements also failed")
        print(f"   Error: {e.stderr}")
        return False

def install_playwright():
    """Install Playwright browsers"""
    print("\n🌐 Installing Playwright browsers...")
    try:
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], 
                      check=True, capture_output=True, text=True)
        print("✅ Playwright browsers installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print("❌ Failed to install Playwright browsers")
        print(f"   Error: {e.stderr}")
        return False

def check_api_key():
    """Check if OpenAI API key is set"""
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        print("✅ OpenAI API key found")
        return True
    else:
        print("⚠️  OpenAI API key not found")
        print("   Please set it with: export OPENAI_API_KEY=your_key_here")
        return False

def main():
    """Main installation process"""
    print("🎓 University Website Information Collector - Installation")
    print("=" * 60)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install requirements
    if not install_requirements():
        print("\n❌ Installation failed. Please try:")
        print("   1. Use Python 3.11 or 3.12 instead of 3.13")
        print("   2. Install system dependencies:")
        if platform.system() == "Darwin":  # macOS
            print("      brew install libxml2 libxslt")
        elif platform.system() == "Linux":
            print("      sudo apt-get install libxml2-dev libxslt1-dev")
        print("   3. Update pip: pip install --upgrade pip setuptools wheel")
        sys.exit(1)
    
    # Install Playwright
    if not install_playwright():
        print("\n⚠️  Playwright installation failed, but you can try manually:")
        print("   playwright install chromium")
    
    # Check API key
    check_api_key()
    
    print("\n🎉 Installation completed!")
    print("\nTo run the application:")
    print("   streamlit run app.py")
    print("\nOr use the startup script:")
    print("   ./run.sh")

if __name__ == "__main__":
    main()
