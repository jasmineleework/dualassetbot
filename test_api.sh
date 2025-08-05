#!/bin/bash

echo "Testing Dual Asset Bot API Endpoints"
echo "===================================="

API_BASE="http://localhost:8080"

# Test health endpoint
echo -e "\n1. Testing Health Check:"
curl -s "$API_BASE/health" | python -m json.tool

# Test status endpoint
echo -e "\n2. Testing Bot Status:"
curl -s "$API_BASE/api/v1/status" | python -m json.tool

# Test market price
echo -e "\n3. Testing BTC Price:"
curl -s "$API_BASE/api/v1/market/price/BTCUSDT" | python -m json.tool

# Test market analysis
echo -e "\n4. Testing Market Analysis (this may take a moment):"
curl -s "$API_BASE/api/v1/market/analysis/BTCUSDT" | python -m json.tool | head -20
echo "... (truncated)"

# Test dual investment products
echo -e "\n5. Testing Dual Investment Products:"
curl -s "$API_BASE/api/v1/dual-investment/products" | python -m json.tool | head -30
echo "... (truncated)"

# Test investment analysis
echo -e "\n6. Testing Investment Analysis:"
curl -s "$API_BASE/api/v1/dual-investment/analyze/BTCUSDT" | python -m json.tool | head -40
echo "... (truncated)"

# Test API docs
echo -e "\n7. API Documentation available at:"
echo "$API_BASE/docs"

echo -e "\n===================================="
echo "API Test Complete!"