"""
Market analysis service for technical indicators
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Tuple
from loguru import logger

class MarketAnalysisService:
    """Service for calculating technical indicators and market analysis"""
    
    @staticmethod
    def calculate_sma(df: pd.DataFrame, period: int = 20, column: str = 'close') -> pd.Series:
        """Calculate Simple Moving Average"""
        return df[column].rolling(window=period).mean()
    
    @staticmethod
    def calculate_ema(df: pd.DataFrame, period: int = 20, column: str = 'close') -> pd.Series:
        """Calculate Exponential Moving Average"""
        return df[column].ewm(span=period, adjust=False).mean()
    
    @staticmethod
    def calculate_rsi(df: pd.DataFrame, period: int = 14, column: str = 'close') -> pd.Series:
        """Calculate Relative Strength Index"""
        delta = df[column].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def calculate_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
        """Calculate MACD indicator"""
        ema_fast = df['close'].ewm(span=fast, adjust=False).mean()
        ema_slow = df['close'].ewm(span=slow, adjust=False).mean()
        
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }
    
    @staticmethod
    def calculate_bollinger_bands(df: pd.DataFrame, period: int = 20, std_dev: int = 2) -> Dict[str, pd.Series]:
        """Calculate Bollinger Bands"""
        sma = df['close'].rolling(window=period).mean()
        std = df['close'].rolling(window=period).std()
        
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        
        return {
            'upper': upper_band,
            'middle': sma,
            'lower': lower_band
        }
    
    @staticmethod
    def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average True Range (volatility indicator)"""
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        return atr
    
    @staticmethod
    def calculate_volume_indicators(df: pd.DataFrame) -> Dict[str, pd.Series]:
        """Calculate volume-based indicators"""
        # On-Balance Volume (OBV)
        obv = (np.sign(df['close'].diff()) * df['volume']).fillna(0).cumsum()
        
        # Volume SMA
        volume_sma = df['volume'].rolling(window=20).mean()
        
        # Money Flow Index (MFI) - simplified version
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        money_flow = typical_price * df['volume']
        
        positive_flow = money_flow.where(typical_price > typical_price.shift(), 0)
        negative_flow = money_flow.where(typical_price < typical_price.shift(), 0)
        
        positive_flow_sum = positive_flow.rolling(window=14).sum()
        negative_flow_sum = negative_flow.rolling(window=14).sum()
        
        mfi = 100 - (100 / (1 + positive_flow_sum / negative_flow_sum))
        
        return {
            'obv': obv,
            'volume_sma': volume_sma,
            'mfi': mfi
        }
    
    @staticmethod
    def analyze_trend(df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze overall market trend"""
        # Calculate various moving averages
        sma_20 = MarketAnalysisService.calculate_sma(df, 20)
        sma_50 = MarketAnalysisService.calculate_sma(df, 50)
        ema_20 = MarketAnalysisService.calculate_ema(df, 20)
        
        current_price = df['close'].iloc[-1]
        
        # Trend determination
        if current_price > sma_20.iloc[-1] and sma_20.iloc[-1] > sma_50.iloc[-1]:
            trend = 'BULLISH'
            strength = 'STRONG' if current_price > sma_20.iloc[-1] * 1.02 else 'MODERATE'
        elif current_price < sma_20.iloc[-1] and sma_20.iloc[-1] < sma_50.iloc[-1]:
            trend = 'BEARISH'
            strength = 'STRONG' if current_price < sma_20.iloc[-1] * 0.98 else 'MODERATE'
        else:
            trend = 'SIDEWAYS'
            strength = 'NEUTRAL'
        
        # Return only string values in main dict, numeric values in separate dict
        return {
            'trend': trend,
            'strength': strength,
            'indicators': {  # Numeric values in a separate nested dict
                'sma_20': float(sma_20.iloc[-1]),
                'sma_50': float(sma_50.iloc[-1]),
                'current_price': float(current_price)
            }
        }
    
    @staticmethod
    def calculate_support_resistance(df: pd.DataFrame, window: int = 20) -> Dict[str, float]:
        """Calculate support and resistance levels"""
        # Simple method using recent highs and lows
        recent_data = df.tail(window)
        
        resistance = recent_data['high'].max()
        support = recent_data['low'].min()
        
        # Pivot points
        pivot = (recent_data['high'].iloc[-1] + recent_data['low'].iloc[-1] + recent_data['close'].iloc[-1]) / 3
        
        return {
            'support': support,
            'resistance': resistance,
            'pivot': pivot,
            'r1': 2 * pivot - recent_data['low'].iloc[-1],
            'r2': pivot + (recent_data['high'].iloc[-1] - recent_data['low'].iloc[-1]),
            's1': 2 * pivot - recent_data['high'].iloc[-1],
            's2': pivot - (recent_data['high'].iloc[-1] - recent_data['low'].iloc[-1])
        }
    
    @staticmethod
    def get_market_signals(df: pd.DataFrame) -> Dict[str, Any]:
        """Generate trading signals based on technical indicators"""
        # Calculate indicators
        rsi = MarketAnalysisService.calculate_rsi(df)
        macd_data = MarketAnalysisService.calculate_macd(df)
        bb_data = MarketAnalysisService.calculate_bollinger_bands(df)
        
        current_rsi = rsi.iloc[-1]
        current_price = df['close'].iloc[-1]
        
        # String-only signals
        signals = {
            'rsi_signal': 'OVERSOLD' if current_rsi < 30 else ('OVERBOUGHT' if current_rsi > 70 else 'NEUTRAL'),
            'macd_signal': 'BUY' if macd_data['histogram'].iloc[-1] > 0 else 'SELL',
            'bb_signal': 'BUY' if current_price < bb_data['lower'].iloc[-1] else ('SELL' if current_price > bb_data['upper'].iloc[-1] else 'HOLD')
        }
        
        # Overall recommendation
        buy_signals = sum([
            signals['rsi_signal'] == 'OVERSOLD',
            signals['macd_signal'] == 'BUY',
            signals['bb_signal'] == 'BUY'
        ])
        
        sell_signals = sum([
            signals['rsi_signal'] == 'OVERBOUGHT',
            signals['macd_signal'] == 'SELL',
            signals['bb_signal'] == 'SELL'
        ])
        
        if buy_signals >= 2:
            signals['recommendation'] = 'STRONG_BUY'
        elif buy_signals > sell_signals:
            signals['recommendation'] = 'BUY'
        elif sell_signals >= 2:
            signals['recommendation'] = 'STRONG_SELL'
        elif sell_signals > buy_signals:
            signals['recommendation'] = 'SELL'
        else:
            signals['recommendation'] = 'HOLD'
        
        # Add numeric indicators in a separate dict
        signals['indicators'] = {
            'current_rsi': float(current_rsi),
            'macd_histogram': float(macd_data['histogram'].iloc[-1])
        }
        
        return signals

# Create singleton instance
market_analysis_service = MarketAnalysisService()
market_analyzer = market_analysis_service  # Alias for backward compatibility