"""
Chart generator service using matplotlib and mplfinance
Fallback solution when browser screenshot is not available
"""
import base64
import io
from typing import Optional, Dict, Any
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import mplfinance as mpf
from datetime import datetime, timedelta
from loguru import logger

class ChartGenerator:
    """Generate candlestick charts using mplfinance"""
    
    def __init__(self):
        """Initialize chart generator"""
        self.style = 'charles'  # Professional trading chart style
        
    def generate_candlestick_chart(
        self, 
        symbol: str = 'BTCUSDT',
        interval: str = '1h',
        limit: int = 100
    ) -> Optional[str]:
        """
        Generate a candlestick chart for the given symbol
        
        Args:
            symbol: Trading pair symbol
            interval: Time interval (1h, 4h, 1d, etc.)
            limit: Number of candles to display
            
        Returns:
            Base64 encoded chart image or None if failed
        """
        try:
            # Get kline data from binance service
            from services.binance_service import binance_service
            
            # Fetch kline data
            df = binance_service.get_klines(symbol, interval, limit)
            
            if df.empty:
                logger.warning(f"No kline data available for {symbol}")
                return None
            
            # Prepare data for mplfinance (needs specific column names)
            df_chart = df[['open', 'high', 'low', 'close', 'volume']].copy()
            df_chart.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            
            # Calculate moving averages
            df_chart['MA5'] = df_chart['Close'].rolling(window=5).mean()
            df_chart['MA20'] = df_chart['Close'].rolling(window=20).mean()
            df_chart['MA60'] = df_chart['Close'].rolling(window=60).mean()
            
            # Create the plot
            fig, axes = mpf.plot(
                df_chart,
                type='candle',
                style=self.style,
                title=f'{symbol} - {interval} Chart',
                ylabel='Price (USDT)',
                volume=True,
                mav=(5, 20, 60),
                figsize=(14, 8),
                returnfig=True,
                tight_layout=True,
                show_nontrading=False
            )
            
            # Add support and resistance lines
            self._add_support_resistance(axes[0], df_chart)
            
            # Add current price line
            self._add_current_price_line(axes[0], df_chart)
            
            # Convert to base64
            buffer = io.BytesIO()
            fig.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
            buffer.seek(0)
            img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            # Clean up
            plt.close(fig)
            
            logger.info(f"Successfully generated chart for {symbol}")
            return img_base64
            
        except Exception as e:
            logger.error(f"Failed to generate chart: {e}")
            return None
    
    def generate_advanced_chart(
        self,
        symbol: str = 'BTCUSDT',
        interval: str = '1h',
        limit: int = 100,
        indicators: list = None
    ) -> Optional[str]:
        """
        Generate an advanced chart with technical indicators
        
        Args:
            symbol: Trading pair symbol
            interval: Time interval
            limit: Number of candles
            indicators: List of indicators to add ['RSI', 'MACD', 'BB']
            
        Returns:
            Base64 encoded chart image
        """
        try:
            from services.binance_service import binance_service
            
            # Fetch kline data
            df = binance_service.get_klines(symbol, interval, limit)
            
            if df.empty:
                return None
            
            # Prepare data
            df_chart = df[['open', 'high', 'low', 'close', 'volume']].copy()
            df_chart.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
            
            # Default indicators
            if indicators is None:
                indicators = ['RSI', 'MACD']
            
            # Calculate indicators
            additional_plots = []
            
            if 'RSI' in indicators:
                rsi = self._calculate_rsi(df_chart['Close'])
                additional_plots.append(
                    mpf.make_addplot(rsi, panel=2, color='purple', ylabel='RSI')
                )
            
            if 'MACD' in indicators:
                macd, signal, hist = self._calculate_macd(df_chart['Close'])
                additional_plots.extend([
                    mpf.make_addplot(macd, panel=3, color='blue', ylabel='MACD'),
                    mpf.make_addplot(signal, panel=3, color='red'),
                    mpf.make_addplot(hist, panel=3, type='bar', color='gray', alpha=0.3)
                ])
            
            # Create the plot with indicators
            fig, axes = mpf.plot(
                df_chart,
                type='candle',
                style=self.style,
                title=f'{symbol} - {interval} Chart with Indicators',
                ylabel='Price (USDT)',
                volume=True,
                mav=(5, 20, 60),
                addplot=additional_plots if additional_plots else None,
                figsize=(14, 10),
                returnfig=True,
                tight_layout=True
            )
            
            # Convert to base64
            buffer = io.BytesIO()
            fig.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
            buffer.seek(0)
            img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            plt.close(fig)
            
            return img_base64
            
        except Exception as e:
            logger.error(f"Failed to generate advanced chart: {e}")
            return None
    
    def _add_support_resistance(self, ax, df):
        """Add support and resistance lines to the chart"""
        try:
            # Simple support/resistance based on recent high/low
            recent_high = df['High'].tail(20).max()
            recent_low = df['Low'].tail(20).min()
            
            ax.axhline(y=recent_high, color='red', linestyle='--', alpha=0.5, label='Resistance')
            ax.axhline(y=recent_low, color='green', linestyle='--', alpha=0.5, label='Support')
            
        except Exception as e:
            logger.warning(f"Could not add support/resistance lines: {e}")
    
    def _add_current_price_line(self, ax, df):
        """Add current price line to the chart"""
        try:
            current_price = df['Close'].iloc[-1]
            ax.axhline(y=current_price, color='blue', linestyle='-', alpha=0.7, linewidth=1.5)
            ax.text(0.02, current_price, f'Current: ${current_price:.2f}', 
                   transform=ax.get_yaxis_transform(), 
                   color='blue', fontsize=9, va='center')
        except Exception as e:
            logger.warning(f"Could not add current price line: {e}")
    
    def _calculate_rsi(self, prices, period=14):
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_macd(self, prices, fast=12, slow=26, signal=9):
        """Calculate MACD indicator"""
        exp1 = prices.ewm(span=fast, adjust=False).mean()
        exp2 = prices.ewm(span=slow, adjust=False).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        histogram = macd - signal_line
        return macd, signal_line, histogram
    
    def generate_comparison_chart(self, symbols: list, interval: str = '1h') -> Optional[str]:
        """
        Generate a comparison chart for multiple symbols
        
        Args:
            symbols: List of symbols to compare
            interval: Time interval
            
        Returns:
            Base64 encoded chart image
        """
        try:
            from services.binance_service import binance_service
            
            fig, ax = plt.subplots(figsize=(14, 8))
            
            for symbol in symbols:
                df = binance_service.get_klines(symbol, interval, 100)
                if not df.empty:
                    # Normalize prices to percentage change from first value
                    normalized = (df['close'] / df['close'].iloc[0] - 1) * 100
                    ax.plot(df.index, normalized, label=symbol, linewidth=2)
            
            ax.set_title('Price Comparison (% Change)', fontsize=14, fontweight='bold')
            ax.set_xlabel('Time', fontsize=12)
            ax.set_ylabel('Change (%)', fontsize=12)
            ax.legend(loc='best')
            ax.grid(True, alpha=0.3)
            
            # Convert to base64
            buffer = io.BytesIO()
            fig.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
            buffer.seek(0)
            img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            plt.close(fig)
            
            return img_base64
            
        except Exception as e:
            logger.error(f"Failed to generate comparison chart: {e}")
            return None

# Create singleton instance
chart_generator = ChartGenerator()