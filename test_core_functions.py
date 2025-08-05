#!/usr/bin/env python3
"""
Test script for core trading functions
"""
import sys
import os
import json
from datetime import datetime

# Add project path to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src/main/python'))

from core.dual_investment_engine import dual_investment_engine
from services.binance_service import binance_service
from loguru import logger

def test_binance_connection():
    """Test Binance API connection"""
    print("\n" + "="*50)
    print("Testing Binance API Connection")
    print("="*50)
    
    try:
        # Test connection
        connected = binance_service.test_connection()
        print(f"✅ Connection status: {'Connected' if connected else 'Not connected'}")
        
        if connected:
            # Test getting price
            btc_price = binance_service.get_symbol_price('BTCUSDT')
            print(f"✅ BTC/USDT Price: ${btc_price:,.2f}")
            
            # Test getting account balance (will fail in testnet without funds)
            try:
                balances = binance_service.get_account_balance()
                print(f"✅ Account has {len(balances)} assets with balance")
            except Exception as e:
                print(f"ℹ️  Account balance not available (expected in testnet): {str(e)[:50]}...")
        
    except Exception as e:
        print(f"❌ Connection test failed: {e}")

def test_market_analysis():
    """Test market analysis functions"""
    print("\n" + "="*50)
    print("Testing Market Analysis")
    print("="*50)
    
    try:
        # Analyze BTC market
        analysis = dual_investment_engine.analyze_market_conditions('BTCUSDT')
        
        print(f"✅ Current BTC Price: ${analysis['current_price']:,.2f}")
        print(f"✅ 24h Change: {analysis['price_change_24h']:.2f}%")
        print(f"✅ Market Trend: {analysis['trend']['trend']} ({analysis['trend']['strength']})")
        print(f"✅ Volatility: {analysis['volatility']['risk_level']}")
        print(f"✅ Trading Signal: {analysis['signals']['recommendation']}")
        print(f"✅ RSI Signal: {analysis['signals']['rsi_signal']}")
        
    except Exception as e:
        print(f"❌ Market analysis failed: {e}")

def test_dual_investment_selection():
    """Test dual investment product selection"""
    print("\n" + "="*50)
    print("Testing Dual Investment Selection")
    print("="*50)
    
    try:
        # Select best product for BTC
        decision = dual_investment_engine.select_best_product('BTCUSDT')
        
        if decision:
            product = decision['selected_product']
            evaluation = decision['evaluation']
            
            print(f"✅ Selected Product: {product['id']}")
            print(f"   - Type: {product['type']}")
            print(f"   - Strike Price: ${product['strike_price']:,.2f}")
            print(f"   - APY: {product['apy']*100:.1f}%")
            print(f"   - Term: {product['term_days']} days")
            print(f"\n✅ Evaluation:")
            print(f"   - Recommend: {'YES' if evaluation['recommend'] else 'NO'}")
            print(f"   - Exercise Probability: {evaluation['exercise_probability']:.1%}")
            print(f"   - Risk Score: {evaluation['risk_score']:.1f}/100")
            print(f"   - Expected Return: {evaluation['expected_return']*100:.2f}%")
            
            # Generate report
            report = dual_investment_engine.generate_investment_report(decision)
            print(f"\n✅ Investment Report Generated:")
            print(f"   - Decision ID: {report['decision_id']}")
            print(f"   - Recommendation: {report['decision_metrics']['recommendation']}")
            
            # Save report
            report_filename = f"investment_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_filename, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"   - Report saved to: {report_filename}")
            
        else:
            print("ℹ️  No suitable products found")
            
    except Exception as e:
        print(f"❌ Dual investment selection failed: {e}")
        import traceback
        traceback.print_exc()

def test_mock_products():
    """Test mock dual investment products"""
    print("\n" + "="*50)
    print("Testing Mock Dual Investment Products")
    print("="*50)
    
    try:
        products = binance_service.get_dual_investment_products()
        print(f"✅ Found {len(products)} mock products")
        
        for product in products:
            print(f"\n   Product: {product['id']}")
            print(f"   - Asset: {product['asset']}")
            print(f"   - Type: {product['type']}")
            print(f"   - Strike: ${product['strike_price']:,.2f}")
            print(f"   - APY: {product['apy']*100:.1f}%")
            
    except Exception as e:
        print(f"❌ Failed to get mock products: {e}")

if __name__ == "__main__":
    print("="*50)
    print("Dual Asset Bot - Core Functions Test")
    print("="*50)
    
    # Configure logger
    logger.add("test_core_functions.log", rotation="10 MB")
    
    # Run tests
    test_binance_connection()
    test_market_analysis()
    test_mock_products()
    test_dual_investment_selection()
    
    print("\n" + "="*50)
    print("Test completed!")
    print("="*50)