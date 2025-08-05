#!/bin/bash

echo "Starting Dual Asset Bot Frontend..."
echo "==================================="

# Change to webapp directory
cd src/main/webapp

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install --legacy-peer-deps --cache .npm-cache
fi

# Start the frontend server
echo "Starting React dev server on http://localhost:3001"
echo "Press Ctrl+C to stop the server"
echo ""

# Use PORT environment variable to run on 3001
PORT=3001 npm start