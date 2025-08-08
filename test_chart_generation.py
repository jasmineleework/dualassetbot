#!/usr/bin/env python3
"""Test chart generation"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src/main/python'))

from services.chart_generator import ChartGenerator
from services.binance_service import binance_service

print("Testing chart generation...")
print("=" * 50)

try:
    # Initialize services
    generator = ChartGenerator()
    
    # Test basic chart generation
    print("Generating chart for BTCUSDT...")
    image_base64 = generator.generate_candlestick_chart('BTCUSDT', '1h', 50)
    
    if image_base64:
        print(f"✅ Chart generated successfully!")
        print(f"   Base64 length: {len(image_base64)} characters")
        
        # Save to file for inspection
        import base64
        import tempfile
        
        img_data = base64.b64decode(image_base64)
        temp_file = os.path.join(tempfile.gettempdir(), 'test_chart.png')
        with open(temp_file, 'wb') as f:
            f.write(img_data)
        print(f"   Saved to: {temp_file}")
    else:
        print("❌ Failed to generate chart")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()