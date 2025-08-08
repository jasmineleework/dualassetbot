#!/usr/bin/env python3
"""Simple test for chart generation without dependencies"""
import base64
import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import mplfinance as mpf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

print("Testing simple chart generation...")
print("=" * 50)

try:
    # Create sample data
    dates = pd.date_range(end=datetime.now(), periods=50, freq='1H')
    
    # Generate random OHLCV data
    np.random.seed(42)
    base_price = 100000
    data = []
    
    for i, date in enumerate(dates):
        open_price = base_price + np.random.randn() * 1000
        close_price = open_price + np.random.randn() * 500
        high_price = max(open_price, close_price) + abs(np.random.randn() * 200)
        low_price = min(open_price, close_price) - abs(np.random.randn() * 200)
        volume = abs(np.random.randn() * 1000000)
        
        data.append([open_price, high_price, low_price, close_price, volume])
        base_price = close_price
    
    # Create DataFrame
    df = pd.DataFrame(data, index=dates, columns=['Open', 'High', 'Low', 'Close', 'Volume'])
    
    print(f"Generated {len(df)} data points")
    print(f"Latest price: ${df['Close'].iloc[-1]:,.2f}")
    
    # Generate chart
    print("\nGenerating chart...")
    
    fig, axes = mpf.plot(
        df,
        type='candle',
        style='charles',
        title='BTC/USDT - Test Chart',
        ylabel='Price (USDT)',
        volume=True,
        mav=(5, 20),
        figsize=(12, 8),
        returnfig=True,
        tight_layout=True
    )
    
    # Convert to base64
    buffer = io.BytesIO()
    fig.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    print(f"✅ Chart generated successfully!")
    print(f"   Base64 length: {len(img_base64)} characters")
    
    # Save to file
    import tempfile
    import os
    
    temp_file = os.path.join(tempfile.gettempdir(), 'test_simple_chart.png')
    with open(temp_file, 'wb') as f:
        f.write(base64.b64decode(img_base64))
    print(f"   Saved to: {temp_file}")
    print(f"\n   You can view the chart by opening: {temp_file}")
    
    plt.close(fig)
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()