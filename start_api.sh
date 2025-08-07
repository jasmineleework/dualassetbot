#!/bin/bash

echo "Starting Dual Asset Bot API Server..."
echo "===================================="

# Change to project root directory
cd "$(dirname "$0")"

# Activate virtual environment
source venv/bin/activate

# Change to Python source directory
cd src/main/python

# Start the API server
echo "Starting uvicorn server on http://localhost:8080"
echo "API Documentation: http://localhost:8080/docs"
echo "Press Ctrl+C to stop the server"
echo ""

uvicorn api.main:app --reload --host 0.0.0.0 --port 8080