#!/usr/bin/env python3
"""Quick API test"""
import requests
import json

base_url = "http://127.0.0.1:8080"

print("Testing Dual Asset Bot API")
print("=" * 50)

# Test endpoints
endpoints = [
    "/",
    "/health",
    "/api/v1/status",
    "/docs"
]

for endpoint in endpoints:
    try:
        response = requests.get(base_url + endpoint, timeout=5)
        print(f"\n{endpoint}:")
        print(f"Status: {response.status_code}")
        if response.headers.get('content-type', '').startswith('application/json'):
            print(f"Response: {json.dumps(response.json(), indent=2)[:200]}...")
        else:
            print(f"Response: {response.text[:100]}...")
    except requests.exceptions.ConnectionError:
        print(f"\n{endpoint}: Connection failed - is the server running?")
    except Exception as e:
        print(f"\n{endpoint}: Error - {e}")

# Test market API
print("\n\nTesting Market API:")
try:
    response = requests.get(f"{base_url}/api/v1/market/price/BTCUSDT")
    print(f"BTC Price: {response.json()}")
except Exception as e:
    print(f"Error: {e}")