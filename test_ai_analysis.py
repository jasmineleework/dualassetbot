#!/usr/bin/env python3
"""
Test AI Analysis Service
Verifies Claude API integration for market analysis
"""

import asyncio
import sys
import os
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src" / "main" / "python"))

from services.ai_analysis_service import ai_analysis_service
from core.dual_investment_engine import dual_investment_engine
from loguru import logger

async def test_ai_analysis():
    """Test AI analysis functionality"""
    
    print("=" * 60)
    print("AI ANALYSIS SERVICE TEST")
    print("=" * 60)
    
    # Check if AI service is enabled
    if not ai_analysis_service.enabled:
        print("❌ AI Analysis Service is DISABLED")
        print("   Please configure ANTHROPIC_API_KEY in your .env file")
        print("   Get your API key from: https://console.anthropic.com/")
        return False
    
    print(f"✅ AI Analysis Service ENABLED")
    print(f"   Model: {ai_analysis_service.model}")
    print(f"   Max Tokens: {ai_analysis_service.max_tokens}")
    print(f"   Temperature: {ai_analysis_service.temperature}")
    
    # Test with sample market data
    print("\n" + "-" * 40)
    print("Testing AI Analysis for BTCUSDT...")
    print("-" * 40)
    
    try:
        # Get real market data
        print("Fetching market data...")
        market_data = dual_investment_engine.analyze_market_conditions('BTCUSDT')
        
        print(f"Current Price: ${market_data['current_price']:,.2f}")
        print(f"24h Change: {market_data['price_change_24h']:.2f}%")
        print(f"Trend: {market_data['trend']['trend']}")
        print(f"Volatility: {market_data['volatility']['risk_level']}")
        
        # Generate AI analysis
        print("\nGenerating AI analysis...")
        ai_result = await ai_analysis_service.analyze_market_with_ai(
            symbol='BTCUSDT',
            market_data=market_data,
            include_oi=False
        )
        
        if ai_result.get('enabled'):
            print("✅ AI Analysis Generated Successfully!")
            
            # Display results
            print("\n" + "=" * 60)
            print("AI ANALYSIS RESULTS")
            print("=" * 60)
            
            if ai_result.get('market_overview'):
                print("\n📊 Market Overview:")
                print("-" * 40)
                print(ai_result['market_overview'])
            
            if ai_result.get('pattern_analysis'):
                print("\n📈 Pattern Analysis:")
                print("-" * 40)
                print(ai_result['pattern_analysis'])
            
            if ai_result.get('trading_strategy'):
                print("\n💰 Trading Strategy:")
                print("-" * 40)
                print(ai_result['trading_strategy'])
            
            if ai_result.get('risk_assessment'):
                print("\n⚠️ Risk Assessment:")
                print("-" * 40)
                print(ai_result['risk_assessment'])
            
            if ai_result.get('key_insights'):
                print("\n💡 Key Insights:")
                print("-" * 40)
                for i, insight in enumerate(ai_result['key_insights'], 1):
                    print(f"{i}. {insight}")
            
            if ai_result.get('warnings'):
                print("\n🚨 Warnings:")
                print("-" * 40)
                for warning in ai_result['warnings']:
                    print(f"• {warning}")
            
            print(f"\n📊 Confidence Score: {ai_result.get('confidence_score', 0):.2%}")
            
            return True
        else:
            print(f"❌ AI Analysis Failed: {ai_result.get('message')}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_trade_rationale():
    """Test AI trade rationale generation"""
    
    print("\n" + "=" * 60)
    print("TESTING TRADE RATIONALE GENERATION")
    print("=" * 60)
    
    if not ai_analysis_service.enabled:
        print("⚠️ Skipping - AI service not enabled")
        return
    
    # Sample product and market data
    product = {
        'type': 'BUY_LOW',
        'asset': 'BTC',
        'strike_price': 115000,
        'apy': 0.25
    }
    
    market_data = {
        'current_price': 116500,
        'trend': {'trend': 'BULLISH'}
    }
    
    print("Generating trade rationale...")
    rationale = await ai_analysis_service.generate_trade_rationale(
        product=product,
        market_data=market_data,
        decision='INVEST'
    )
    
    print("\n📝 AI Trade Rationale:")
    print("-" * 40)
    print(rationale)

if __name__ == "__main__":
    print("Starting AI Analysis Service Test...\n")
    
    # Run tests
    success = asyncio.run(test_ai_analysis())
    
    if success:
        # Also test trade rationale if main test passed
        asyncio.run(test_trade_rationale())
        print("\n✅ All AI tests completed successfully!")
    else:
        print("\n⚠️ AI analysis test failed - check configuration")
    
    sys.exit(0 if success else 1)