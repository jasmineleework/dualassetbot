"""
Public market data service using Binance public API endpoints
No authentication required for these endpoints
"""
import requests
from typing import Dict, Any, List, Optional
from loguru import logger
import pandas as pd
from datetime import datetime

class PublicMarketService:
    """Service for fetching public market data from Binance"""
    
    def __init__(self, use_testnet: bool = False):
        """
        Initialize public market service
        
        Args:
            use_testnet: Whether to use testnet API
        """
        if use_testnet:
            self.base_url = "https://testnet.binance.vision/api/v3"
        else:
            self.base_url = "https://api.binance.com/api/v3"
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'DualAssetBot/1.0'
        })
    
    def get_symbol_price(self, symbol: str) -> Dict[str, Any]:
        """
        Get current price for a symbol (public endpoint)
        
        Args:
            symbol: Trading pair symbol (e.g., 'BTCUSDT')
            
        Returns:
            Dictionary with symbol and price
        """
        try:
            url = f"{self.base_url}/ticker/price"
            params = {'symbol': symbol.upper()}
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            return {
                'symbol': data['symbol'],
                'price': float(data['price']),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get price for {symbol}: {e}")
            raise
    
    def get_24hr_ticker_stats(self, symbol: str) -> Dict[str, Any]:
        """
        Get 24hr ticker statistics (public endpoint)
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            Dictionary with 24hr statistics
        """
        try:
            url = f"{self.base_url}/ticker/24hr"
            params = {'symbol': symbol.upper()}
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            return {
                'symbol': data['symbol'],
                'price_change': float(data['priceChange']),
                'price_change_percent': float(data['priceChangePercent']),
                'last_price': float(data['lastPrice']),
                'volume': float(data['volume']),
                'high_24h': float(data['highPrice']),
                'low_24h': float(data['lowPrice']),
                'open_price': float(data['openPrice']),
                'prev_close_price': float(data['prevClosePrice']),
                'count': int(data['count']),
                'data_source': 'production_public_api'
            }
            
        except Exception as e:
            logger.error(f"Failed to get 24hr stats for {symbol}: {e}")
            raise
    
    def get_klines(self, symbol: str, interval: str = '1h', limit: int = 100) -> pd.DataFrame:
        """
        Get kline/candlestick data (public endpoint)
        
        Args:
            symbol: Trading pair symbol
            interval: Kline interval (1m, 5m, 15m, 30m, 1h, 4h, 1d, etc.)
            limit: Number of klines to retrieve (max 1000)
            
        Returns:
            DataFrame with OHLCV data
        """
        try:
            url = f"{self.base_url}/klines"
            params = {
                'symbol': symbol.upper(),
                'interval': interval,
                'limit': min(limit, 1000)  # API limit is 1000
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            klines = response.json()
            
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
    
    def get_all_prices(self) -> List[Dict[str, Any]]:
        """
        Get current prices for all symbols (public endpoint)
        
        Returns:
            List of dictionaries with symbol and price
        """
        try:
            url = f"{self.base_url}/ticker/price"
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            return [
                {
                    'symbol': item['symbol'],
                    'price': float(item['price'])
                }
                for item in data
            ]
            
        except Exception as e:
            logger.error(f"Failed to get all prices: {e}")
            raise
    
    def get_exchange_info(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """
        Get exchange trading rules and symbol information (public endpoint)
        
        Args:
            symbol: Optional specific symbol to get info for
            
        Returns:
            Dictionary with exchange information
        """
        try:
            url = f"{self.base_url}/exchangeInfo"
            params = {}
            if symbol:
                params['symbol'] = symbol.upper()
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Failed to get exchange info: {e}")
            raise
    
    def get_order_book(self, symbol: str, limit: int = 100) -> Dict[str, Any]:
        """
        Get order book depth (public endpoint)
        
        Args:
            symbol: Trading pair symbol
            limit: Depth limit (5, 10, 20, 50, 100, 500, 1000, 5000)
            
        Returns:
            Dictionary with bids and asks
        """
        try:
            url = f"{self.base_url}/depth"
            params = {
                'symbol': symbol.upper(),
                'limit': limit
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            return {
                'symbol': symbol,
                'bids': [[float(p), float(q)] for p, q in data['bids']],
                'asks': [[float(p), float(q)] for p, q in data['asks']],
                'lastUpdateId': data['lastUpdateId']
            }
            
        except Exception as e:
            logger.error(f"Failed to get order book for {symbol}: {e}")
            raise
    
    def test_connectivity(self) -> bool:
        """
        Test connectivity to Binance API (public endpoint)
        
        Returns:
            True if connection successful
        """
        try:
            url = f"{self.base_url}/ping"
            response = self.session.get(url, timeout=5)
            response.raise_for_status()
            return True
            
        except Exception as e:
            logger.error(f"Failed to ping Binance API: {e}")
            return False
    
    def get_server_time(self) -> int:
        """
        Get Binance server time (public endpoint)
        
        Returns:
            Server timestamp in milliseconds
        """
        try:
            url = f"{self.base_url}/time"
            response = self.session.get(url, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            return data['serverTime']
            
        except Exception as e:
            logger.error(f"Failed to get server time: {e}")
            raise

# Create singleton instance
public_market_service = PublicMarketService()