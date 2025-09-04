#!/bin/bash

# University Website Information Collector - Startup Script

echo "🎓 University Website Information Collector"
echo "============================================="

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Please install pip3."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
echo "   Trying main requirements first..."

if pip install -r requirements.txt; then
    echo "✅ Main requirements installed successfully"
else
    echo "⚠️  Main requirements failed, trying minimal requirements..."
    if pip install -r requirements-minimal.txt; then
        echo "✅ Minimal requirements installed successfully"
    else
        echo "❌ Installation failed. Please check your Python version and system dependencies."
        echo "   You may need to install system dependencies or use a different Python version."
        exit 1
    fi
fi

# Install Playwright browsers
echo "🌐 Installing Playwright browsers..."
playwright install chromium

# Check for API key
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  Warning: OPENAI_API_KEY environment variable not set."
    echo "   Please set it with: export OPENAI_API_KEY=your_key_here"
    echo "   Or create a .env file with: OPENAI_API_KEY=your_key_here"
    echo ""
fi

# Run tests
echo "🧪 Running tests..."
python test_app.py

if [ $? -eq 0 ]; then
    echo ""
    echo "🚀 Starting the application..."
    echo "   The app will open in your default web browser."
    echo "   If it doesn't open automatically, go to: http://localhost:8501"
    echo ""
    streamlit run app.py
else
    echo "❌ Tests failed. Please fix the issues before running the application."
    exit 1
fi
