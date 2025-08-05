#!/usr/bin/env python3
"""
Test script to verify project setup
"""
import sys
import os

# Add project path to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src/main/python'))

def test_imports():
    """Test if all main imports work"""
    print("Testing imports...")
    
    try:
        import fastapi
        print("✅ FastAPI imported successfully")
    except ImportError as e:
        print(f"❌ FastAPI import failed: {e}")
    
    try:
        import pandas
        print("✅ Pandas imported successfully")
    except ImportError as e:
        print(f"❌ Pandas import failed: {e}")
    
    try:
        import binance
        print("✅ Python-Binance imported successfully")
    except ImportError as e:
        print(f"❌ Python-Binance import failed: {e}")
    
    try:
        from api.main import app
        print("✅ FastAPI app imported successfully")
    except ImportError as e:
        print(f"❌ FastAPI app import failed: {e}")
    
    try:
        from core.config import settings
        print("✅ Config imported successfully")
        print(f"   App Name: {settings.app_name}")
        print(f"   Environment: {settings.app_env}")
    except ImportError as e:
        print(f"❌ Config import failed: {e}")

def test_api():
    """Test if API can start"""
    print("\nTesting API...")
    try:
        from api.main import app
        print("✅ API module loaded successfully")
        print("   You can now run: uvicorn src.main.python.api.main:app --reload")
    except Exception as e:
        print(f"❌ API test failed: {e}")

if __name__ == "__main__":
    print("=" * 50)
    print("Dual Asset Bot - Setup Test")
    print("=" * 50)
    
    test_imports()
    test_api()
    
    print("\n" + "=" * 50)
    print("Setup test completed!")
    print("=" * 50)