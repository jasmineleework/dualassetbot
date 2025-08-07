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
import time

class BinanceService:
    """Service for interacting with Binance API"""
    
    def __init__(self):
        """Initialize Binance client"""
        self.client = None
        self._initialized = False
        self._testnet_adapter = None
    
    def _initialize_client(self):
        """Initialize Binance API client"""
        try:
            if not settings.binance_api_key or not settings.binance_api_secret:
                logger.warning("Binance API credentials not configured")
                return
            
            self.client = Client(
                api_key=settings.binance_api_key,
                api_secret=settings.binance_api_secret
            )
            
            # Set testnet if enabled
            if settings.binance_testnet:
                self.client.API_URL = 'https://testnet.binance.vision/api'
            
            # Sync time with server to avoid timestamp errors
            try:
                server_time = self.client.get_server_time()
                local_time = int(time.time() * 1000)
                time_diff = server_time['serverTime'] - local_time
                
                if abs(time_diff) > 5000:
                    logger.warning(f"Time difference with server: {time_diff}ms")
                    # Apply time offset to client
                    self.client.timestamp_offset = time_diff
                    logger.info(f"Applied timestamp offset: {time_diff}ms")
            except Exception as e:
                logger.warning(f"Failed to sync time with server: {e}")
            
            # Test connection
            self.client.ping()
            logger.info("Binance API client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Binance client: {e}")
            self.client = None  # Ensure client is None on failure
            self._initialized = False
            return
        
        self._initialized = True
    
    def ensure_initialized(self):
        """Ensure the client is initialized"""
        if not self._initialized or not self.client:
            self._initialize_client()
            if not self.client:
                raise ValueError("Binance client not initialized - check API credentials")
    
    def get_account_balance(self) -> Dict[str, float]:
        """Get account balance for all assets"""
        try:
            self.ensure_initialized()
            
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
            self.ensure_initialized()
            
            ticker = self.client.get_symbol_ticker(symbol=symbol)
            return float(ticker['price'])
            
        except Exception as e:
            logger.error(f"Failed to get price for {symbol}: {e}")
            # For testnet, try alternative method
            if settings.binance_testnet:
                try:
                    ticker = self.client.get_ticker(symbol=symbol)
                    return float(ticker['lastPrice'])
                except:
                    pass
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
            self.ensure_initialized()
            
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
        Generate dual investment products based on real market data
        
        Uses TestnetDualProductAdapter for realistic product generation
        """
        try:
            self.ensure_initialized()
            
            # Use testnet adapter for better product generation
            if settings.binance_testnet:
                if not self._testnet_adapter:
                    from services.testnet_dual_product_adapter import TestnetDualProductAdapter
                    self._testnet_adapter = TestnetDualProductAdapter(self)
                
                products = self._testnet_adapter.get_all_products()
                if products:
                    logger.info(f"Generated {len(products)} dual investment products from testnet data")
                    return products
            
            # Fallback to simple generation for non-testnet
            products = []
            symbols = ['BTCUSDT', 'ETHUSDT']
            
            for symbol in symbols:
                try:
                    current_price = self.get_symbol_price(symbol)
                    asset = symbol.replace('USDT', '')
                    stats = self.get_24hr_ticker_stats(symbol)
                    volatility = abs(stats['price_change_percent'])
                    
                    # Generate basic products
                    products.append({
                        'id': f'{asset}-USDT-BUYLOW-{datetime.now().strftime("%Y%m%d")}',
                        'asset': asset,
                        'currency': 'USDT',
                        'type': 'BUY_LOW',
                        'strike_price': round(current_price * 0.95, 2),
                        'apy': round(min(0.15 + volatility * 0.01, 0.50), 4),
                        'term_days': 7,
                        'min_amount': 100,
                        'max_amount': 10000,
                        'settlement_date': datetime.now() + timedelta(days=7),
                        'current_price': current_price
                    })
                    
                    products.append({
                        'id': f'{asset}-USDT-SELLHIGH-{datetime.now().strftime("%Y%m%d")}',
                        'asset': asset,
                        'currency': 'USDT',
                        'type': 'SELL_HIGH',
                        'strike_price': round(current_price * 1.05, 2),
                        'apy': round(min(0.12 + volatility * 0.008, 0.40), 4),
                        'term_days': 7,
                        'min_amount': 0.001 if asset == 'BTC' else 0.01,
                        'max_amount': 1 if asset == 'BTC' else 10,
                        'settlement_date': datetime.now() + timedelta(days=7),
                        'current_price': current_price
                    })
                    
                except Exception as e:
                    logger.warning(f"Failed to generate products for {symbol}: {e}")
                    continue
            
            return products if products else []
            
        except Exception as e:
            logger.error(f"Failed to generate dual investment products: {e}")
            return []
    
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
            self.ensure_initialized()
            
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
            self.ensure_initialized()
            if not self.client:
                return False
            
            self.client.ping()
            return True
            
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

# Create singleton instance (lazy initialization)
binance_service = BinanceService()