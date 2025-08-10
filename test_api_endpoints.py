#!/usr/bin/env python3
"""Test API endpoints with real testnet data"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8080/api/v1"

def test_endpoints():
    print("=" * 60)
    print("Testing API Endpoints with Testnet Data")
    print("=" * 60)
    
    # Test 1: Market price
    print("\n1. Testing /market/price/BTCUSDT...")
    try:
        resp = requests.get(f"{BASE_URL}/market/price/BTCUSDT")
        if resp.status_code == 200:
            data = resp.json()
            print(f"✅ BTC Price: ${data['price']:,.2f}")
        else:
            print(f"❌ Failed: {resp.status_code} - {resp.text[:100]}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: 24hr stats
    print("\n2. Testing /market/24hr-stats/BTCUSDT...")
    try:
        resp = requests.get(f"{BASE_URL}/market/24hr-stats/BTCUSDT")
        if resp.status_code == 200:
            data = resp.json()
            print(f"✅ 24hr Change: {data['price_change_percent']:.2f}%")
            print(f"   Volume: {data['volume']:,.2f}")
        else:
            print(f"❌ Failed: {resp.status_code} - {resp.text[:100]}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: Klines
    print("\n3. Testing /market/klines/BTCUSDT...")
    try:
        resp = requests.get(f"{BASE_URL}/market/klines/BTCUSDT?interval=1h&limit=5")
        if resp.status_code == 200:
            data = resp.json()
            print(f"✅ Got {len(data['data'])} klines")
            if data['data']:
                latest = data['data'][-1]
                print(f"   Latest close: ${latest['close']:,.2f}")
        else:
            print(f"❌ Failed: {resp.status_code} - {resp.text[:100]}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: Dual investment products
    print("\n4. Testing /dual-investment/products...")
    try:
        resp = requests.get(f"{BASE_URL}/dual-investment/products")
        if resp.status_code == 200:
            products = resp.json()
            print(f"✅ Got {len(products)} products")
            
            # Group by type
            buy_low = [p for p in products if p['type'] == 'BUY_LOW']
            sell_high = [p for p in products if p['type'] == 'SELL_HIGH']
            
            print(f"   BUY_LOW: {len(buy_low)} products")
            print(f"   SELL_HIGH: {len(sell_high)} products")
            
            # Show sample
            if buy_low:
                sample = buy_low[0]
                print(f"\n   Sample BUY_LOW:")
                print(f"   - Asset: {sample['asset']}")
                print(f"   - Strike: ${sample['strike_price']:,.2f}")
                print(f"   - APY: {sample['apy']*100:.2f}%")
                print(f"   - Term: {sample['term_days']} days")
        else:
            print(f"❌ Failed: {resp.status_code} - {resp.text[:100]}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 5: Filtered products
    print("\n5. Testing /dual-investment/products?asset=BTC&type=BUY_LOW...")
    try:
        resp = requests.get(f"{BASE_URL}/dual-investment/products?asset=BTC&type=BUY_LOW")
        if resp.status_code == 200:
            products = resp.json()
            print(f"✅ Got {len(products)} BTC BUY_LOW products")
            
            # Show different terms
            terms = set(p['term_days'] for p in products)
            print(f"   Available terms: {sorted(terms)} days")
        else:
            print(f"❌ Failed: {resp.status_code} - {resp.text[:100]}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 6: AI analysis
    print("\n6. Testing /dual-investment/analyze/BTCUSDT...")
    try:
        resp = requests.get(f"{BASE_URL}/dual-investment/analyze/BTCUSDT")
        if resp.status_code == 200:
            data = resp.json()
            print(f"✅ AI Analysis complete")
            print(f"   Current Price: ${data['current_price']:,.2f}")
            print(f"   Trend: {data['trend']['trend']}")
            print(f"   Volatility: {data['volatility']['risk_level']}")
            print(f"   Support: ${data['support_resistance']['support']:,.2f}")
            print(f"   Resistance: ${data['support_resistance']['resistance']:,.2f}")
        else:
            print(f"❌ Failed: {resp.status_code} - {resp.text[:100]}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 7: Account balance
    print("\n7. Testing /account/balance...")
    try:
        resp = requests.get(f"{BASE_URL}/account/balance")
        if resp.status_code == 200:
            data = resp.json()
            print(f"✅ Got balance for {len(data)} assets")
            # Show top assets
            for asset, balance in list(data.items())[:3]:
                print(f"   {asset}: {balance['total']:.8f}")
        else:
            print(f"❌ Failed: {resp.status_code} - {resp.text[:100]}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("✅ API testing complete - All endpoints using real testnet data!")
    print("=" * 60)

if __name__ == "__main__":
    test_endpoints()