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
        """Get 24hr ticker statistics with enhanced data validation"""
        try:
            self.ensure_initialized()
            
            ticker = self.client.get_ticker(symbol=symbol)
            
            # Parse values
            last_price = float(ticker['lastPrice'])
            price_change = float(ticker['priceChange'])
            price_change_percent = float(ticker['priceChangePercent'])
            volume = float(ticker['volume'])
            
            # Initialize with ticker data
            high_24h = float(ticker['highPrice'])
            low_24h = float(ticker['lowPrice'])
            data_source = 'ticker'
            
            # For testnet, apply smart data correction
            if settings.binance_testnet:
                # Check if ticker data is unrealistic (more than 50% deviation)
                if high_24h > last_price * 1.5 or low_24h < last_price * 0.5:
                    logger.info(f"Ticker data for {symbol} seems unrealistic, fetching hourly data")
                    
                    try:
                        # Get last 24 hours of 1-hour klines for more accurate data
                        hourly_klines = self.client.get_klines(
                            symbol=symbol,
                            interval='1h',
                            limit=24
                        )
                        
                        if hourly_klines and len(hourly_klines) > 0:
                            # Extract high and low from hourly data
                            hourly_highs = [float(k[2]) for k in hourly_klines]
                            hourly_lows = [float(k[3]) for k in hourly_klines]
                            
                            # Filter out obvious outliers (more than 50% from median)
                            import statistics
                            if len(hourly_highs) > 3:
                                median_high = statistics.median(hourly_highs)
                                median_low = statistics.median(hourly_lows)
                                
                                # Filter outliers
                                filtered_highs = [h for h in hourly_highs if h <= median_high * 1.5]
                                filtered_lows = [l for l in hourly_lows if l >= median_low * 0.5]
                                
                                if filtered_highs and filtered_lows:
                                    high_24h = max(filtered_highs)
                                    low_24h = min(filtered_lows)
                                    data_source = 'hourly_filtered'
                                    logger.info(f"Using filtered hourly data for {symbol}: high={high_24h:.2f}, low={low_24h:.2f}")
                            else:
                                # Not enough data to filter, use raw hourly
                                high_24h = max(hourly_highs)
                                low_24h = min(hourly_lows)
                                data_source = 'hourly'
                        
                    except Exception as hourly_error:
                        logger.warning(f"Failed to get hourly data for {symbol}: {hourly_error}")
                        # Fall back to calculated estimates
                        data_source = 'calculated'
                
                # Final sanity check - ensure values are within reasonable range
                max_deviation = 0.20  # 20% max deviation from current price
                
                # For high price
                if high_24h > last_price * (1 + max_deviation):
                    logger.debug(f"Capping high price for {symbol}: {high_24h} -> {last_price * (1 + max_deviation)}")
                    high_24h = last_price * (1 + max_deviation)
                    data_source = f'{data_source}_capped'
                elif high_24h < last_price:
                    # High should be at least current price
                    high_24h = last_price * 1.01
                    data_source = f'{data_source}_adjusted'
                
                # For low price
                if low_24h < last_price * (1 - max_deviation):
                    logger.debug(f"Capping low price for {symbol}: {low_24h} -> {last_price * (1 - max_deviation)}")
                    low_24h = last_price * (1 - max_deviation)
                    data_source = f'{data_source}_capped'
                elif low_24h > last_price:
                    # Low should be at most current price
                    low_24h = last_price * 0.99
                    data_source = f'{data_source}_adjusted'
                
                # Ensure high > low
                if high_24h <= low_24h:
                    spread = last_price * 0.02  # 2% spread
                    high_24h = last_price + spread
                    low_24h = last_price - spread
                    data_source = 'corrected'
                
                logger.debug(f"{symbol} 24h stats - Source: {data_source}, High: {high_24h:.2f}, Low: {low_24h:.2f}, Current: {last_price:.2f}")
            
            return {
                'symbol': ticker['symbol'],
                'price_change': price_change,
                'price_change_percent': price_change_percent,
                'last_price': last_price,
                'volume': volume,
                'high_24h': high_24h,
                'low_24h': low_24h,
                'data_source': data_source  # Track where the data came from
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

    def subscribe_dual_investment(self, product_id: str, amount: float) -> Dict[str, Any]:
        """
        Subscribe to a dual investment product (simulated for testnet)
        """
        try:
            self.ensure_initialized()
            
            # In testnet mode, simulate the subscription
            if settings.binance_testnet:
                # Generate simulated order ID
                import time
                import random
                order_id = f"SIM_{int(time.time())}{random.randint(1000, 9999)}"
                
                # Simulate successful subscription
                result = {
                    'success': True,
                    'order_id': order_id,
                    'product_id': product_id,
                    'amount': amount,
                    'execution_price': self.get_symbol_price(product_id.split('-')[0] + 'USDT')['price'],
                    'timestamp': datetime.utcnow().isoformat(),
                    'status': 'PENDING',
                    'message': 'Dual investment subscription successful (simulated)'
                }
                
                logger.info(f"Simulated dual investment subscription: {product_id} for ${amount}")
                return result
            else:
                # For production, would implement actual Binance API call
                # Currently returns simulated result
                logger.warning("Production dual investment subscription not implemented")
                return {
                    'success': False,
                    'error': 'Production dual investment API not implemented',
                    'message': 'Please use testnet mode for testing'
                }
                
        except Exception as e:
            logger.error(f"Failed to subscribe to dual investment {product_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Dual investment subscription failed'
            }

    def get_investment_status(self, order_id: str) -> Dict[str, Any]:
        """
        Get the status of a dual investment order
        """
        try:
            self.ensure_initialized()
            
            # In testnet mode, simulate status checking
            if settings.binance_testnet:
                # Simulate different statuses based on time
                import hashlib
                hash_val = int(hashlib.md5(order_id.encode()).hexdigest()[:8], 16)
                
                # Simulate status progression
                statuses = ['PENDING', 'ACTIVE', 'SETTLED', 'CANCELLED']
                status = statuses[hash_val % len(statuses)]
                
                # Generate realistic PnL for settled investments
                pnl = 0
                if status == 'SETTLED':
                    # Random return between -5% to +15%
                    return_pct = (hash_val % 2000 - 500) / 10000  # -5% to +15%
                    pnl = return_pct * 100  # Assume $100 base amount
                
                result = {
                    'order_id': order_id,
                    'status': status,
                    'pnl': pnl,
                    'updated_at': datetime.utcnow().isoformat(),
                    'message': f'Simulated status: {status}'
                }
                
                return result
            else:
                logger.warning("Production investment status checking not implemented")
                return {
                    'order_id': order_id,
                    'status': 'UNKNOWN',
                    'message': 'Production status API not implemented'
                }
                
        except Exception as e:
            logger.error(f"Failed to get investment status for {order_id}: {e}")
            return {
                'error': str(e),
                'message': 'Status check failed'
            }

    def cancel_dual_investment(self, order_id: str) -> Dict[str, Any]:
        """
        Cancel a dual investment order
        """
        try:
            self.ensure_initialized()
            
            # In testnet mode, simulate cancellation
            if settings.binance_testnet:
                result = {
                    'success': True,
                    'order_id': order_id,
                    'status': 'CANCELLED',
                    'cancelled_at': datetime.utcnow().isoformat(),
                    'message': 'Dual investment cancelled successfully (simulated)'
                }
                
                logger.info(f"Simulated dual investment cancellation: {order_id}")
                return result
            else:
                logger.warning("Production dual investment cancellation not implemented")
                return {
                    'success': False,
                    'error': 'Production cancellation API not implemented',
                    'message': 'Please use testnet mode for testing'
                }
                
        except Exception as e:
            logger.error(f"Failed to cancel dual investment {order_id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Cancellation failed'
            }

# Create singleton instance (lazy initialization)
binance_service = BinanceService()