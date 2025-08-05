"""
Binance API integration service for Dual Asset Bot
"""
from typing import List, Dict, Any, Optional
from binance.client import Client
from binance.exceptions import BinanceAPIException
from loguru import logger
from core.config import settings
import pandas as pd
from datetime import datetime, timedelta

class BinanceService:
    """Service for interacting with Binance API"""
    
    def __init__(self):
        """Initialize Binance client"""
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Binance API client"""
        try:
            if not settings.binance_api_key or not settings.binance_api_secret:
                logger.warning("Binance API credentials not configured")
                return
            
            self.client = Client(
                api_key=settings.binance_api_key,
                api_secret=settings.binance_api_secret,
                testnet=settings.binance_testnet
            )
            
            # Test connection
            self.client.ping()
            logger.info("Binance API client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Binance client: {e}")
            raise
    
    def get_account_balance(self) -> Dict[str, float]:
        """Get account balance for all assets"""
        try:
            if not self.client:
                raise ValueError("Binance client not initialized")
            
            account = self.client.get_account()
            balances = {}
            
            for balance in account['balances']:
                free = float(balance['free'])
                locked = float(balance['locked'])
                total = free + locked
                
                if total > 0:
                    balances[balance['asset']] = {
                        'free': free,
                        'locked': locked,
                        'total': total
                    }
            
            return balances
            
        except Exception as e:
            logger.error(f"Failed to get account balance: {e}")
            raise
    
    def get_symbol_price(self, symbol: str) -> float:
        """Get current price for a symbol"""
        try:
            if not self.client:
                raise ValueError("Binance client not initialized")
            
            ticker = self.client.get_symbol_ticker(symbol=symbol)
            return float(ticker['price'])
            
        except Exception as e:
            logger.error(f"Failed to get price for {symbol}: {e}")
            raise
    
    def get_klines(self, symbol: str, interval: str = '1h', limit: int = 100) -> pd.DataFrame:
        """
        Get historical klines/candlestick data
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTCUSDT')
            interval: Kline interval (1m, 5m, 15m, 30m, 1h, 4h, 1d, etc.)
            limit: Number of klines to retrieve
            
        Returns:
            DataFrame with OHLCV data
        """
        try:
            if not self.client:
                raise ValueError("Binance client not initialized")
            
            klines = self.client.get_klines(
                symbol=symbol,
                interval=interval,
                limit=limit
            )
            
            # Convert to DataFrame
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])
            
            # Convert timestamp to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            # Convert price columns to float
            price_columns = ['open', 'high', 'low', 'close', 'volume', 'quote_volume']
            df[price_columns] = df[price_columns].astype(float)
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to get klines for {symbol}: {e}")
            raise
    
    def get_dual_investment_products(self) -> List[Dict[str, Any]]:
        """
        Get available dual investment products
        
        Note: This is a placeholder as Binance doesn't provide direct API for dual investment.
        In production, you might need to:
        1. Use web scraping or reverse engineering
        2. Use Binance Savings API endpoints if they become available
        3. Manually maintain a list of available products
        """
        logger.warning("Dual investment API not directly available. Using mock data.")
        
        # Mock data for development
        mock_products = [
            {
                'id': 'BTC-USDT-BUYLOW-20240115',
                'asset': 'BTC',
                'currency': 'USDT',
                'type': 'BUY_LOW',
                'strike_price': 42000,
                'apy': 0.25,  # 25% APY
                'term_days': 7,
                'min_amount': 100,
                'max_amount': 10000,
                'settlement_date': datetime.now() + timedelta(days=7)
            },
            {
                'id': 'BTC-USDT-SELLHIGH-20240115',
                'asset': 'BTC',
                'currency': 'USDT',
                'type': 'SELL_HIGH',
                'strike_price': 45000,
                'apy': 0.20,  # 20% APY
                'term_days': 7,
                'min_amount': 0.001,
                'max_amount': 1,
                'settlement_date': datetime.now() + timedelta(days=7)
            },
            {
                'id': 'ETH-USDT-BUYLOW-20240115',
                'asset': 'ETH',
                'currency': 'USDT',
                'type': 'BUY_LOW',
                'strike_price': 2200,
                'apy': 0.22,  # 22% APY
                'term_days': 7,
                'min_amount': 100,
                'max_amount': 10000,
                'settlement_date': datetime.now() + timedelta(days=7)
            }
        ]
        
        return mock_products
    
    def subscribe_dual_investment(self, product_id: str, amount: float) -> Dict[str, Any]:
        """
        Subscribe to a dual investment product
        
        Note: This is a placeholder. In production, implement actual subscription logic.
        """
        logger.info(f"Subscribing to product {product_id} with amount {amount}")
        
        # Mock response
        return {
            'success': True,
            'order_id': f"DUAL_{product_id}_{datetime.now().timestamp()}",
            'product_id': product_id,
            'amount': amount,
            'status': 'PENDING',
            'message': 'Subscription pending confirmation'
        }
    
    def get_24hr_ticker_stats(self, symbol: str) -> Dict[str, Any]:
        """Get 24hr ticker statistics"""
        try:
            if not self.client:
                raise ValueError("Binance client not initialized")
            
            ticker = self.client.get_ticker(symbol=symbol)
            
            return {
                'symbol': ticker['symbol'],
                'price_change': float(ticker['priceChange']),
                'price_change_percent': float(ticker['priceChangePercent']),
                'last_price': float(ticker['lastPrice']),
                'volume': float(ticker['volume']),
                'high_24h': float(ticker['highPrice']),
                'low_24h': float(ticker['lowPrice'])
            }
            
        except Exception as e:
            logger.error(f"Failed to get 24hr stats for {symbol}: {e}")
            raise
    
    def test_connection(self) -> bool:
        """Test connection to Binance API"""
        try:
            if not self.client:
                return False
            
            self.client.ping()
            return True
            
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

# Create singleton instance
binance_service = BinanceService()