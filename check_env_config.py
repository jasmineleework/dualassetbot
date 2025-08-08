#!/usr/bin/env python3
"""
Environment configuration checker
Ensures all required API keys are properly configured
"""

import os
import sys
from pathlib import Path

def check_env_config():
    """Check if all required environment variables are configured"""
    
    env_file = Path(".env")
    if not env_file.exists():
        print("❌ .env file not found!")
        return False
    
    required_configs = {
        "BINANCE_TESTNET_API_KEY": "Binance Testnet API Key",
        "BINANCE_TESTNET_API_SECRET": "Binance Testnet API Secret",
        "BINANCE_PRODUCTION_API_KEY": "Binance Production API Key",
        "BINANCE_PRODUCTION_API_SECRET": "Binance Production API Secret",
        "ANTHROPIC_API_KEY": "Claude API Key (optional)",
    }
    
    print("=" * 60)
    print("ENVIRONMENT CONFIGURATION CHECK")
    print("=" * 60)
    
    all_good = True
    configured = []
    missing = []
    
    # Read .env file
    with open(env_file, 'r') as f:
        env_content = f.read()
    
    for key, description in required_configs.items():
        # Check if key exists and has a value
        found = False
        for line in env_content.split('\n'):
            if line.startswith(f"{key}="):
                value = line.split('=', 1)[1].strip()
                if value and not value.startswith('your_') and value != 'your_api_key_here':
                    configured.append(f"✅ {description}: Configured")
                    found = True
                    break
        
        if not found:
            if "optional" in description:
                configured.append(f"ℹ️ {description}: Not configured")
            else:
                missing.append(f"❌ {description}: Missing or not configured")
                all_good = False
    
    # Print results
    for item in configured:
        print(item)
    for item in missing:
        print(item)
    
    print("\n" + "=" * 60)
    
    if all_good:
        print("✅ All required configurations are set!")
    else:
        print("⚠️ Some required configurations are missing.")
        print("Please update your .env file with the missing API keys.")
    
    # Check specific settings
    print("\n📋 Current Settings:")
    settings_to_check = [
        ("BINANCE_USE_TESTNET", "Environment"),
        ("DEMO_MODE", "Demo Mode"),
        ("CLAUDE_MODEL", "Claude Model"),
    ]
    
    for key, label in settings_to_check:
        for line in env_content.split('\n'):
            if line.startswith(f"{key}="):
                value = line.split('=', 1)[1].split('#')[0].strip()
                print(f"  {label}: {value}")
                break
    
    return all_good

if __name__ == "__main__":
    success = check_env_config()
    sys.exit(0 if success else 1)