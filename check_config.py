#!/usr/bin/env python3
"""Check configuration loading"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src/main/python'))

from core.config import settings

print("Configuration Check")
print("==================")
print(f"App Name: {settings.app_name}")
print(f"Environment: {settings.app_env}")
print(f"Binance API Key: {'***' + settings.binance_api_key[-4:] if settings.binance_api_key else 'Not set'}")
print(f"Binance API Secret: {'***' + settings.binance_api_secret[-4:] if settings.binance_api_secret else 'Not set'}")
print(f"Binance Testnet: {settings.binance_testnet}")
print(f"Database URL: {settings.database_url}")
print(f"Redis URL: {settings.redis_url}")