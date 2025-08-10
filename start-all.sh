#!/bin/bash

# Start All Services Script for Dual Asset Bot

echo "🚀 Starting Dual Asset Bot Services..."
echo "======================================"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping all services..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    exit 0
}

# Set trap for cleanup
trap cleanup INT TERM

# Start backend in background
echo "1️⃣  Starting Backend Server..."
(cd src/main/python && python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8081 --reload) &
BACKEND_PID=$!

# Wait for backend to start
echo "   Waiting for backend to start..."
sleep 5

# Check if backend is running
if curl -s http://localhost:8081/health > /dev/null; then
    echo "   ✅ Backend started successfully on http://localhost:8081"
else
    echo "   ❌ Backend failed to start. Check the logs above."
    exit 1
fi

echo ""
echo "2️⃣  Starting Frontend..."
(cd src/main/webapp && npm start) &
FRONTEND_PID=$!

echo ""
echo "======================================"
echo "✅ All services are starting..."
echo ""
echo "📊 Backend API: http://localhost:8081"
echo "📝 API Docs: http://localhost:8081/docs"
echo "🌐 Frontend: http://localhost:3010"
echo ""
echo "Press Ctrl+C to stop all services"
echo "======================================"

# Wait for processes
wait $BACKEND_PID $FRONTEND_PID