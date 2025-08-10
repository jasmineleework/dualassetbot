#!/bin/bash

# Start Backend Server Script for Dual Asset Bot

echo "🚀 Starting Dual Asset Bot Backend Server..."
echo "============================================"

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.9+ first."
    exit 1
fi

# Navigate to backend directory
cd src/main/python || exit

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate 2>/dev/null || . venv/bin/activate

# Install/update dependencies
echo "📚 Installing dependencies..."
pip install -q -r requirements.txt

# Check if Redis is running (optional, will use memory cache if not)
if command -v redis-cli &> /dev/null; then
    if redis-cli ping &> /dev/null; then
        echo "✅ Redis is running (cache enabled)"
    else
        echo "⚠️  Redis is not running (using memory cache)"
    fi
else
    echo "ℹ️  Redis not installed (using memory cache)"
fi

# Start the backend server
echo ""
echo "🌟 Starting API server on http://localhost:8080"
echo "============================================"
echo "📝 API Documentation: http://localhost:8080/docs"
echo "❤️  Health Check: http://localhost:8080/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Run the server
python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8080 --reload