#!/usr/bin/env python3
"""
Test script for detailed AI recommendations API
"""
import requests
import json
from datetime import datetime
from typing import Dict, Any, List

# API base URL
BASE_URL = "http://localhost:8000/api/v1/dual-investment"

def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print('='*60)

def print_product_info(product: Dict[str, Any]):
    """Pretty print product information"""
    print(f"\n📊 Product Info:")
    print(f"   Asset: {product['asset']}/{product['currency']}")
    print(f"   APY: {product['apy']} ({product['apy_value']*100:.2f}%)")
    print(f"   Strike Price: ${product['strike_price']:,.2f}")
    print(f"   Current Price: ${product['current_price']:,.2f}")
    print(f"   Price Distance: {product['price_distance']}")
    print(f"   Settlement: {product['settlement_date'][:10] if product['settlement_date'] else 'N/A'}")
    print(f"   Term: {product['term_days']} days")
    print(f"   Min/Max Amount: ${product['min_amount']:,.2f} - ${product['max_amount']:,.2f}")

def print_ai_analysis(analysis: Dict[str, Any]):
    """Pretty print AI analysis"""
    print(f"\n🤖 AI Analysis:")
    print(f"   AI Score: {analysis['ai_score']:.3f}")
    print(f"   Recommendation: {analysis['recommendation']}")
    print(f"   Expected Return: {analysis['expected_return']}")
    print(f"   Exercise Probability: {analysis['exercise_probability']}")
    print(f"   Risk Score: {analysis['risk_score']:.1f}")

def print_investment_decision(decision: Dict[str, Any]):
    """Pretty print investment decision"""
    print(f"\n💼 Investment Decision:")
    print(f"   Should Invest: {'✅ YES' if decision['should_invest'] else '❌ NO'}")
    print(f"   Suggested Amount: ${decision['suggested_amount']:,.2f}")
    if decision['reasons']:
        print(f"   Reasons:")
        for reason in decision['reasons']:
            print(f"     • {reason}")
    if decision['warnings']:
        print(f"   ⚠️ Warnings:")
        for warning in decision['warnings']:
            print(f"     • {warning}")

def print_market_context(context: Dict[str, Any]):
    """Pretty print market context"""
    print(f"\n📈 Market Context:")
    print(f"   Trend: {context['trend']} (strength: {context['trend_strength']:.2f})")
    print(f"   Volatility: {context['volatility']}")
    print(f"   Support/Resistance: ${context['support']:,.2f} / ${context['resistance']:,.2f}")
    print(f"   24h Change: {context['price_change_24h']:.2f}%")

def test_detailed_recommendations(symbol: str = "BTCUSDT", limit: int = 5):
    """Test the detailed recommendations endpoint"""
    
    print_section(f"Testing Detailed Recommendations for {symbol}")
    
    # Test without filter
    print("\n1. Getting all recommendations...")
    url = f"{BASE_URL}/recommendations-detailed/{symbol}"
    params = {"limit": limit}
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Print summary
        summary = data.get('summary', {})
        print(f"\n📊 Summary:")
        print(f"   Total Recommendations: {summary['total_recommendations']}")
        print(f"   Strong Buy: {summary['strong_buy_count']}")
        print(f"   Buy: {summary['buy_count']}")
        print(f"   Consider: {summary['consider_count']}")
        print(f"   Average AI Score: {summary['average_ai_score']:.3f}")
        print(f"   Average APY: {summary['average_apy']:.2f}%")
        
        # Print top recommendation details
        if data['recommendations']:
            print_section("Top Recommendation Details")
            top_rec = data['recommendations'][0]
            
            print(f"\n🏆 Product ID: {top_rec['product_id']}")
            print(f"   Strategy Type: {top_rec['strategy_type']}")
            
            print_product_info(top_rec['product_info'])
            print_ai_analysis(top_rec['ai_analysis'])
            print_investment_decision(top_rec['investment_decision'])
            print_market_context(top_rec['market_context'])
        
        # Print categorized recommendations
        print_section("Categorized Recommendations")
        categories = data.get('categories', {})
        
        if categories.get('strong_buy'):
            print("\n🔥 STRONG BUY:")
            for rec in categories['strong_buy']:
                print(f"   • {rec['product_id']}: {rec['strategy_type']} - APY: {rec['product_info']['apy']}, AI Score: {rec['ai_analysis']['ai_score']:.3f}")
        
        if categories.get('buy'):
            print("\n✅ BUY:")
            for rec in categories['buy']:
                print(f"   • {rec['product_id']}: {rec['strategy_type']} - APY: {rec['product_info']['apy']}, AI Score: {rec['ai_analysis']['ai_score']:.3f}")
        
        if categories.get('consider'):
            print("\n🤔 CONSIDER:")
            for rec in categories['consider']:
                print(f"   • {rec['product_id']}: {rec['strategy_type']} - APY: {rec['product_info']['apy']}, AI Score: {rec['ai_analysis']['ai_score']:.3f}")
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
        return
    
    # Test with BUY_LOW filter
    print_section("Testing BUY_LOW Strategy Filter")
    params = {"limit": 3, "strategy_type": "BUY_LOW"}
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        print(f"\n📊 BUY_LOW Recommendations: {len(data['recommendations'])}")
        for rec in data['recommendations']:
            print(f"\n• Product: {rec['product_id']}")
            print(f"  APY: {rec['product_info']['apy']}")
            print(f"  Strike: ${rec['product_info']['strike_price']:,.2f} ({rec['product_info']['price_distance']} from current)")
            print(f"  AI Score: {rec['ai_analysis']['ai_score']:.3f}")
            print(f"  Recommendation: {rec['ai_analysis']['recommendation']}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")
    
    # Test with SELL_HIGH filter
    print_section("Testing SELL_HIGH Strategy Filter")
    params = {"limit": 3, "strategy_type": "SELL_HIGH"}
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        print(f"\n📊 SELL_HIGH Recommendations: {len(data['recommendations'])}")
        for rec in data['recommendations']:
            print(f"\n• Product: {rec['product_id']}")
            print(f"  APY: {rec['product_info']['apy']}")
            print(f"  Strike: ${rec['product_info']['strike_price']:,.2f} ({rec['product_info']['price_distance']} from current)")
            print(f"  AI Score: {rec['ai_analysis']['ai_score']:.3f}")
            print(f"  Recommendation: {rec['ai_analysis']['recommendation']}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {e}")

def test_comparison():
    """Compare BTC and ETH recommendations"""
    print_section("Comparing BTC vs ETH Recommendations")
    
    symbols = ["BTCUSDT", "ETHUSDT"]
    comparisons = []
    
    for symbol in symbols:
        url = f"{BASE_URL}/recommendations-detailed/{symbol}"
        params = {"limit": 3}
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            summary = data.get('summary', {})
            comparisons.append({
                'symbol': symbol,
                'total': summary['total_recommendations'],
                'avg_ai_score': summary['average_ai_score'],
                'avg_apy': summary['average_apy'],
                'strong_buy': summary['strong_buy_count']
            })
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching {symbol}: {e}")
    
    # Print comparison table
    if comparisons:
        print("\n📊 Comparison Table:")
        print(f"{'Symbol':<10} {'Total':<8} {'Avg AI':<10} {'Avg APY':<10} {'Strong Buy':<10}")
        print("-" * 50)
        for comp in comparisons:
            print(f"{comp['symbol']:<10} {comp['total']:<8} {comp['avg_ai_score']:<10.3f} {comp['avg_apy']:<10.2f}% {comp['strong_buy']:<10}")

if __name__ == "__main__":
    print("=" * 60)
    print(" Testing Detailed AI Recommendations API")
    print("=" * 60)
    print(f" Timestamp: {datetime.now().isoformat()}")
    print("=" * 60)
    
    # Run tests
    test_detailed_recommendations("BTCUSDT", limit=5)
    test_comparison()
    
    print("\n" + "=" * 60)
    print(" Tests Completed")
    print("=" * 60)