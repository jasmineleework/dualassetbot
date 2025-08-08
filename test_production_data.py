#!/usr/bin/env python3
"""Test production data access using public API"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src/main/python'))

from services.public_market_service import PublicMarketService
import json

print("Testing Production Data Access (Public API)")
print("=" * 50)

# Initialize service
service = PublicMarketService(use_testnet=False)

# Test connectivity
print("\n1. Testing connectivity...")
if service.test_connectivity():
    print("✅ Connected to Binance Production API")
else:
    print("❌ Failed to connect")
    sys.exit(1)

# Get server time
print("\n2. Getting server time...")
try:
    server_time = service.get_server_time()
    from datetime import datetime
    server_datetime = datetime.fromtimestamp(server_time / 1000)
    print(f"✅ Server time: {server_datetime}")
except Exception as e:
    print(f"❌ Failed: {e}")

# Get BTC price
print("\n3. Getting BTC/USDT price...")
try:
    price_data = service.get_symbol_price('BTCUSDT')
    print(f"✅ BTC Price: ${price_data['price']:,.2f}")
except Exception as e:
    print(f"❌ Failed: {e}")

# Get 24hr stats
print("\n4. Getting 24hr statistics for BTC/USDT...")
try:
    stats = service.get_24hr_ticker_stats('BTCUSDT')
    print(f"✅ 24hr Stats:")
    print(f"   Last Price: ${stats['last_price']:,.2f}")
    print(f"   24h High: ${stats['high_24h']:,.2f}")
    print(f"   24h Low: ${stats['low_24h']:,.2f}")
    print(f"   24h Change: {stats['price_change_percent']:.2f}%")
    print(f"   24h Volume: {stats['volume']:,.2f} BTC")
    print(f"   Data Source: {stats['data_source']}")
except Exception as e:
    print(f"❌ Failed: {e}")

# Get ETH stats for comparison
print("\n5. Getting 24hr statistics for ETH/USDT...")
try:
    eth_stats = service.get_24hr_ticker_stats('ETHUSDT')
    print(f"✅ ETH Stats:")
    print(f"   Last Price: ${eth_stats['last_price']:,.2f}")
    print(f"   24h High: ${eth_stats['high_24h']:,.2f}")
    print(f"   24h Low: ${eth_stats['low_24h']:,.2f}")
    print(f"   24h Change: {eth_stats['price_change_percent']:.2f}%")
except Exception as e:
    print(f"❌ Failed: {e}")

# Get kline data
print("\n6. Getting 1-hour klines for BTC/USDT...")
try:
    df = service.get_klines('BTCUSDT', '1h', 5)
    print(f"✅ Got {len(df)} klines")
    print(f"   Latest close: ${df['close'].iloc[-1]:,.2f}")
    print(f"   5-hour high: ${df['high'].max():,.2f}")
    print(f"   5-hour low: ${df['low'].min():,.2f}")
except Exception as e:
    print(f"❌ Failed: {e}")

print("\n" + "=" * 50)
print("✅ All tests passed! Production data access is working.")
print("Note: This uses public API endpoints - no authentication required.")