#!/bin/bash
# CymbalFlix Discover - Local Setup and Run Script
# =================================================
# Run this script to set up and launch the app locally in Cloud Shell.

set -e

echo "🎬 CymbalFlix Discover - Setup"
echo "=============================="

# Check if we're in the right directory
if [ ! -f "Home.py" ]; then
    echo "❌ Error: Please run this script from the cymbalflix-app directory"
    exit 1
fi

# Check for .env file
if [ ! -f ".env" ]; then
    echo ""
    echo "⚠️  No .env file found. Creating from template..."
    
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✅ Created .env from .env.example"
        echo ""
        echo "📝 Please edit .env with your values:"
        echo "   - PROJECT_ID: Your Google Cloud project ID"
        echo "   - DB_USER: Your IAM email (e.g., student@qwiklabs.net)"
        echo ""
        echo "Run this command to edit:"
        echo "   edit .env"
        echo ""
        echo "Then run this script again."
        exit 0
    else
        echo "❌ Error: No .env.example file found"
        exit 1
    fi
fi

# Source the .env file to check configuration
source .env

# Validate required variables
if [ -z "$PROJECT_ID" ] || [ "$PROJECT_ID" = "your-project-id" ]; then
    echo "❌ Error: PROJECT_ID not set in .env"
    exit 1
fi

if [ -z "$DB_USER" ] || [ "$DB_USER" = "student-xxx@qwiklabs.net" ]; then
    echo "❌ Error: DB_USER not set in .env"
    exit 1
fi

echo "✅ Configuration looks good!"
echo "   Project: $PROJECT_ID"
echo "   User: $DB_USER"
echo ""

# Check for virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Check if dependencies are installed
echo "📦 Checking dependencies..."
if ! python3 -c "import streamlit" 2>/dev/null; then
    echo "Installing Python dependencies..."
    pip install -r requirements.txt -q
    echo "✅ Dependencies installed"
else
    echo "✅ Dependencies already installed"
fi

echo ""
echo "🚀 Starting CymbalFlix Discover..."
echo ""
echo "   The app will open in Cloud Shell's web preview."
echo "   If it doesn't open automatically, click the Web Preview button"
echo "   (square with arrow) and select 'Preview on port 8501'"
echo ""
echo "   Press Ctrl+C to stop the server."
echo ""

# Run Streamlit
streamlit run Home.py --server.port 8501 --server.address 0.0.0.0 --server.enableCORS=false --server.enableXsrfProtection=false

