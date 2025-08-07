#!/usr/bin/env python3
"""Test all API endpoints to verify real data is returned"""
import requests
import json
from datetime import datetime

API_BASE = "http://localhost:8080"

def test_endpoint(name, url):
    """Test a single endpoint"""
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"URL: {url}")
    print("-"*60)
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if response.status_code == 200:
            print("✅ Status: SUCCESS")
            print(f"📊 Data: {json.dumps(data, indent=2)[:500]}...")
            
            # Check if it's mock data
            if isinstance(data, dict) and data.get('mock'):
                print("⚠️  WARNING: This is mock data!")
        else:
            print(f"❌ Status: {response.status_code}")
            print(f"Error: {data}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    print(f"🚀 Testing Dual Asset Bot API Endpoints")
    print(f"📅 Time: {datetime.now()}")
    
    endpoints = [
        ("System Status", f"{API_BASE}/api/v1/status"),
        ("BTC Price", f"{API_BASE}/api/v1/market/price/BTCUSDT"),
        ("ETH Price", f"{API_BASE}/api/v1/market/price/ETHUSDT"),
        ("BTC 24hr Stats", f"{API_BASE}/api/v1/market/24hr-stats/BTCUSDT"),
        ("BTC Market Analysis", f"{API_BASE}/api/v1/market/analysis/BTCUSDT"),
        ("BTC Klines", f"{API_BASE}/api/v1/market/klines/BTCUSDT?interval=1h&limit=5"),
        ("Dual Investment Products", f"{API_BASE}/api/v1/dual-investment/products"),
        ("Account Balance", f"{API_BASE}/api/v1/account/balance"),
    ]
    
    for name, url in endpoints:
        test_endpoint(name, url)
    
    print(f"\n{'='*60}")
    print("✅ All tests completed!")
    print("Check for any mock data warnings above.")

if __name__ == "__main__":
    main()