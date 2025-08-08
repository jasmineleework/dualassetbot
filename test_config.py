#!/usr/bin/env python3
"""
Configuration verification script for Dual Asset Bot
Tests environment configuration and API connectivity
"""

import sys
import os
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src" / "main" / "python"))

from core.config import settings
from loguru import logger
import json

def check_configuration():
    """Check and display current configuration"""
    
    print("=" * 60)
    print("DUAL ASSET BOT - CONFIGURATION CHECK")
    print("=" * 60)
    
    # Check .env file
    env_file = project_root / ".env"
    if env_file.exists():
        print(f"✅ Environment file found: {env_file}")
    else:
        print(f"❌ Environment file NOT found: {env_file}")
        print("   Please create .env file from .env.example")
        return False
    
    print("\n📋 CURRENT CONFIGURATION:")
    print("-" * 40)
    
    # Environment Selection
    print("\n🌍 ENVIRONMENT:")
    print(f"  Use Testnet: {settings.binance_use_testnet}")
    print(f"  Environment: {'TESTNET' if settings.binance_use_testnet else 'PRODUCTION'}")
    
    # API Keys Status (don't show actual keys)
    print("\n🔑 API KEYS:")
    if settings.binance_testnet_api_key:
        print(f"  Testnet API Key: ✅ Configured ({len(settings.binance_testnet_api_key)} chars)")
    else:
        print("  Testnet API Key: ❌ Not configured")
    
    if settings.binance_testnet_api_secret:
        print(f"  Testnet API Secret: ✅ Configured")
    else:
        print("  Testnet API Secret: ❌ Not configured")
    
    if settings.binance_production_api_key:
        print(f"  Production API Key: ✅ Configured ({len(settings.binance_production_api_key)} chars)")
    else:
        print("  Production API Key: ❌ Not configured")
    
    if settings.binance_production_api_secret:
        print(f"  Production API Secret: ✅ Configured")
    else:
        print("  Production API Secret: ❌ Not configured")
    
    # Safety Settings
    print("\n🛡️ SAFETY SETTINGS:")
    print(f"  Demo Mode: {settings.demo_mode} {'✅ (Safe - Simulated trades)' if settings.demo_mode else '⚠️ (Real trades!)'}")
    print(f"  Trading Enabled: {settings.trading_enabled} {'⚠️ (Trading active!)' if settings.trading_enabled else '✅ (Trading disabled)'}")
    print(f"  Max Trade Amount: ${settings.max_trade_amount} USDT")
    print(f"  Use Public Data Only: {settings.use_public_data_only}")
    
    # Trading Configuration
    print("\n💰 TRADING CONFIGURATION:")
    print(f"  Default Investment: ${settings.default_investment_amount} USDT")
    print(f"  Max Single Investment Ratio: {settings.max_single_investment_ratio * 100}%")
    print(f"  Min APR Threshold: {settings.min_apr_threshold * 100}%")
    print(f"  Risk Level: {settings.risk_level}/10")
    
    # Database Configuration
    print("\n💾 DATABASE:")
    if "sqlite" in settings.database_url:
        print(f"  Database: SQLite (local file)")
    else:
        print(f"  Database: PostgreSQL")
    print(f"  Redis: {settings.redis_url}")
    
    print("\n" + "=" * 60)
    
    # Test API Connection
    print("\n🔌 TESTING API CONNECTION...")
    print("-" * 40)
    
    try:
        from services.binance_service import binance_service
        
        # Test connection
        if binance_service.test_connection():
            print("✅ API connection successful!")
            
            # Test market data
            try:
                btc_price = binance_service.get_symbol_price("BTCUSDT")
                print(f"✅ Market data working - BTC Price: ${btc_price:,.2f}")
            except Exception as e:
                print(f"⚠️ Market data error: {e}")
            
            # Check if we can get account (only if not using public data)
            if not settings.use_public_data_only:
                try:
                    balance = binance_service.get_account_balance()
                    print(f"✅ Account access working - Found {len(balance)} assets")
                except Exception as e:
                    print(f"⚠️ Account access error: {e}")
                    print("   (This is normal if using public data only)")
        else:
            print("❌ API connection failed!")
            
    except Exception as e:
        print(f"❌ Connection test error: {e}")
    
    print("\n" + "=" * 60)
    
    # Recommendations
    print("\n📝 RECOMMENDATIONS:")
    if settings.binance_use_testnet:
        print("• Currently using TESTNET - safe for testing")
        print("• To use production data: set BINANCE_USE_TESTNET=False")
    else:
        if settings.demo_mode:
            print("• Production environment with DEMO MODE - safe configuration ✅")
        else:
            print("• ⚠️ PRODUCTION MODE with REAL TRADING - be careful!")
    
    if not settings.trading_enabled:
        print("• Trading is disabled - safe for testing strategies")
    else:
        print("• ⚠️ Trading is ENABLED - real orders will be placed!")
    
    print("\n" + "=" * 60)
    return True

if __name__ == "__main__":
    try:
        success = check_configuration()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Configuration check failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)