#!/usr/bin/env python3
"""Test Binance connection directly"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src/main/python'))

from binance.client import Client
from core.config import settings

print("Testing Binance Connection")
print("=" * 50)
print(f"API Key: {'*' * (len(settings.binance_api_key) - 4) + settings.binance_api_key[-4:] if settings.binance_api_key else 'Not set'}")
print(f"API Secret: {'*' * (len(settings.binance_api_secret) - 4) + settings.binance_api_secret[-4:] if settings.binance_api_secret else 'Not set'}")
print(f"Testnet: {settings.binance_testnet}")
print("=" * 50)

if not settings.binance_api_key or not settings.binance_api_secret:
    print("ERROR: API credentials not set!")
    sys.exit(1)

try:
    print("Creating Binance client...")
    client = Client(
        api_key=settings.binance_api_key,
        api_secret=settings.binance_api_secret
    )
    
    if settings.binance_testnet:
        client.API_URL = 'https://testnet.binance.vision/api'
        print("Using testnet API URL")
    
    print("Testing connection...")
    client.ping()
    print("✅ Connection successful!")
    
    # Try to get server time
    server_time = client.get_server_time()
    print(f"✅ Server time: {server_time}")
    
    # Try to get account info (might fail on testnet)
    try:
        account = client.get_account()
        print("✅ Account access successful!")
    except Exception as e:
        print(f"⚠️  Account access failed (expected on testnet): {str(e)[:100]}...")
    
except Exception as e:
    print(f"❌ Connection failed: {e}")
    print("\nPossible issues:")
    print("1. Check if API key and secret are correct")
    print("2. For testnet, make sure you're using testnet API keys")
    print("3. Check your internet connection")
    print("4. Ensure IP is whitelisted in Binance API settings")