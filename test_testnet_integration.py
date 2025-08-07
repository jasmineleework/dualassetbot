#!/usr/bin/env python3
"""Test Binance Testnet Integration"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src/main/python'))

from services.binance_service import binance_service
import json
from datetime import datetime

def test_testnet_integration():
    print("=" * 60)
    print("Testing Binance Testnet Integration")
    print("=" * 60)
    
    try:
        # Test 1: Connection
        print("\n1. Testing connection...")
        binance_service.ensure_initialized()
        print("✅ Binance connection successful")
        
        # Test 2: Get symbol price
        print("\n2. Testing symbol price...")
        price = binance_service.get_symbol_price('BTCUSDT')
        print(f"✅ BTC Price: ${price:,.2f}")
        
        # Test 3: Get 24hr stats
        print("\n3. Testing 24hr stats...")
        stats = binance_service.get_24hr_ticker_stats('BTCUSDT')
        print(f"✅ 24hr Change: {stats['price_change_percent']:.2f}%")
        print(f"   Volume: {stats['volume']:,.2f}")
        
        # Test 4: Get klines
        print("\n4. Testing klines data...")
        df = binance_service.get_klines('BTCUSDT', interval='1h', limit=10)
        print(f"✅ Got {len(df)} klines")
        print(f"   Latest close: ${df.iloc[-1]['close']:,.2f}")
        
        # Test 5: Get dual investment products
        print("\n5. Testing dual investment products...")
        products = binance_service.get_dual_investment_products()
        print(f"✅ Generated {len(products)} dual investment products")
        
        # Group products by type
        buy_low = [p for p in products if p['type'] == 'BUY_LOW']
        sell_high = [p for p in products if p['type'] == 'SELL_HIGH']
        
        print(f"\n   BUY_LOW products: {len(buy_low)}")
        print(f"   SELL_HIGH products: {len(sell_high)}")
        
        # Show sample products
        if buy_low:
            print("\n   Sample BUY_LOW Product:")
            sample = buy_low[0]
            print(f"   - Asset: {sample['asset']}")
            print(f"   - Current Price: ${sample.get('current_price', 0):,.2f}")
            print(f"   - Strike Price: ${sample['strike_price']:,.2f}")
            print(f"   - APY: {sample['apy']*100:.2f}%")
            print(f"   - Term: {sample['term_days']} days")
            if 'exercise_probability' in sample:
                print(f"   - Exercise Prob: {sample['exercise_probability']*100:.2f}%")
        
        if sell_high:
            print("\n   Sample SELL_HIGH Product:")
            sample = sell_high[0]
            print(f"   - Asset: {sample['asset']}")
            print(f"   - Current Price: ${sample.get('current_price', 0):,.2f}")
            print(f"   - Strike Price: ${sample['strike_price']:,.2f}")
            print(f"   - APY: {sample['apy']*100:.2f}%")
            print(f"   - Term: {sample['term_days']} days")
            if 'exercise_probability' in sample:
                print(f"   - Exercise Prob: {sample['exercise_probability']*100:.2f}%")
        
        # Test 6: Account balance (might fail on testnet)
        print("\n6. Testing account balance...")
        try:
            balance = binance_service.get_account_balance()
            if balance:
                print(f"✅ Got balance for {len(balance)} assets")
                for asset, bal in list(balance.items())[:3]:
                    print(f"   {asset}: {bal['total']:.8f}")
            else:
                print("⚠️  No balance data (expected on testnet)")
        except Exception as e:
            print(f"⚠️  Balance not available on testnet: {str(e)[:50]}...")
        
        print("\n" + "=" * 60)
        print("✅ All tests passed! Testnet integration working.")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = test_testnet_integration()
    sys.exit(0 if success else 1)