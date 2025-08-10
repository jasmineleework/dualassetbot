#!/bin/bash

# Start Frontend Server Script for Dual Asset Bot

echo "🚀 Starting Dual Asset Bot Frontend..."
echo "======================================"

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 14+ first."
    exit 1
fi

# Navigate to frontend directory
cd src/main/webapp || exit

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
else
    echo "✅ Dependencies already installed"
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✅ Created .env file. Please update it with your settings if needed."
    else
        echo "❌ .env.example not found. Please create .env file manually."
        exit 1
    fi
fi

# Verify backend URL configuration
BACKEND_URL=$(grep REACT_APP_API_URL .env | cut -d '=' -f2)
if [[ "$BACKEND_URL" == *"8080"* ]]; then
    echo "✅ Backend URL configured correctly: $BACKEND_URL"
else
    echo "⚠️  Backend URL may be incorrect: $BACKEND_URL"
    echo "   Expected: http://localhost:8080"
fi

echo ""
echo "🌟 Starting frontend on http://localhost:3010"
echo "======================================"
echo "📱 Make sure backend is running on port 8080"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the frontend server
npm start