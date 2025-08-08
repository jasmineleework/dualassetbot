#!/usr/bin/env python3
"""
Test AI Analysis Cache Functionality
Verifies that AI analyses are cached properly
"""

import asyncio
import sys
import os
from pathlib import Path
import time

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src" / "main" / "python"))

from services.ai_analysis_service import ai_analysis_service
from services.cache_service import cache_service
from core.dual_investment_engine import dual_investment_engine
from loguru import logger

async def test_cache_functionality():
    """Test AI analysis caching"""
    
    print("=" * 60)
    print("AI ANALYSIS CACHE TEST")
    print("=" * 60)
    
    # Check cache service
    cache_info = cache_service.get_cache_info()
    print(f"\n📦 Cache Service Info:")
    print(f"   Type: {cache_info['type']}")
    print(f"   Connected: {cache_info['connected']}")
    
    # Check AI service cache settings
    print(f"\n⚙️ AI Service Cache Settings:")
    print(f"   Cache Enabled: {ai_analysis_service.cache_enabled}")
    print(f"   Cache TTL: {ai_analysis_service.cache_ttl}s")
    
    if not ai_analysis_service.enabled:
        print("\n⚠️ AI Service not enabled - skipping cache test")
        print("   Configure ANTHROPIC_API_KEY to enable AI analysis")
        return False
    
    symbol = 'BTCUSDT'
    
    # Get market data for testing
    print(f"\n📊 Testing cache for {symbol}...")
    print("-" * 40)
    
    try:
        market_data = dual_investment_engine.analyze_market_conditions(symbol)
        
        # Test 1: First request (should generate new analysis)
        print("\n🔄 Request 1: Initial request (should generate fresh analysis)")
        start_time = time.time()
        
        result1 = await ai_analysis_service.analyze_market_with_ai(
            symbol=symbol,
            market_data=market_data,
            force_refresh=False
        )
        
        elapsed1 = time.time() - start_time
        print(f"   Time taken: {elapsed1:.2f}s")
        print(f"   From cache: {result1.get('from_cache', False)}")
        print(f"   Has content: {bool(result1.get('market_overview'))}")
        
        if result1.get('from_cache'):
            print("   ❌ ERROR: First request should not be from cache!")
            return False
        
        # Test 2: Second request (should use cache)
        print("\n🔄 Request 2: Immediate second request (should use cache)")
        start_time = time.time()
        
        result2 = await ai_analysis_service.analyze_market_with_ai(
            symbol=symbol,
            market_data=market_data,
            force_refresh=False
        )
        
        elapsed2 = time.time() - start_time
        print(f"   Time taken: {elapsed2:.2f}s")
        print(f"   From cache: {result2.get('from_cache', False)}")
        
        if not result2.get('from_cache'):
            print("   ❌ ERROR: Second request should be from cache!")
            return False
        
        if elapsed2 > 1.0:
            print(f"   ⚠️ Cache retrieval seems slow ({elapsed2:.2f}s)")
        
        # Test 3: Force refresh
        print("\n🔄 Request 3: Force refresh (should generate new analysis)")
        start_time = time.time()
        
        result3 = await ai_analysis_service.analyze_market_with_ai(
            symbol=symbol,
            market_data=market_data,
            force_refresh=True
        )
        
        elapsed3 = time.time() - start_time
        print(f"   Time taken: {elapsed3:.2f}s")
        print(f"   From cache: {result3.get('from_cache', False)}")
        
        if result3.get('from_cache'):
            print("   ❌ ERROR: Force refresh should not use cache!")
            return False
        
        # Test 4: Different symbol (should not use cache)
        print("\n🔄 Request 4: Different symbol ETHUSDT (should generate new)")
        market_data_eth = dual_investment_engine.analyze_market_conditions('ETHUSDT')
        
        result4 = await ai_analysis_service.analyze_market_with_ai(
            symbol='ETHUSDT',
            market_data=market_data_eth,
            force_refresh=False
        )
        
        print(f"   From cache: {result4.get('from_cache', False)}")
        
        if result4.get('from_cache'):
            print("   ❌ ERROR: Different symbol should not use cache!")
            return False
        
        # Summary
        print("\n" + "=" * 60)
        print("✅ CACHE TEST RESULTS:")
        print("-" * 40)
        print(f"✓ Initial request generated fresh analysis ({elapsed1:.2f}s)")
        print(f"✓ Second request used cache ({elapsed2:.2f}s)")
        print(f"✓ Cache provided {(elapsed1/elapsed2):.1f}x speedup")
        print(f"✓ Force refresh bypassed cache correctly")
        print(f"✓ Different symbols have separate caches")
        
        # Check cache stats
        cache_info = cache_service.get_cache_info()
        print(f"\n📊 Final Cache Stats:")
        print(f"   Total keys: {cache_info.get('total_keys', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_cache_expiration():
    """Test cache expiration (manual check)"""
    
    print("\n" + "=" * 60)
    print("CACHE EXPIRATION INFO")
    print("=" * 60)
    
    print("\n📝 Cache Expiration Notes:")
    print("-" * 40)
    print(f"• Cache TTL is set to: {ai_analysis_service.cache_ttl}s")
    print(f"• Analyses are cached per symbol per hour")
    print(f"• Cache key format: ai_analysis:SYMBOL:YYYYMMDD_HH")
    print(f"• This means cache automatically expires:")
    print(f"  - After {ai_analysis_service.cache_ttl}s (TTL expiration)")
    print(f"  - At the start of each new hour (key change)")
    print(f"• Manual refresh available via 'force_refresh' parameter")

if __name__ == "__main__":
    print("Starting AI Analysis Cache Test...\n")
    
    # Run cache functionality test
    success = asyncio.run(test_cache_functionality())
    
    if success:
        # Show expiration info
        asyncio.run(test_cache_expiration())
        print("\n✅ All cache tests passed successfully!")
    else:
        print("\n⚠️ Cache test failed - check configuration")
    
    sys.exit(0 if success else 1)