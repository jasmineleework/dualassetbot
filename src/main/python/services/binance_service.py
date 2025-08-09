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
from .public_market_service import public_market_service

class BinanceService:
    """Service for interacting with Binance API"""
    
    def __init__(self):
        """Initialize Binance client"""
        self.client = None
        self.public_client = None  # For public market data (no auth needed)
        self._initialized = False
        self._testnet_adapter = None
        self.demo_mode = settings.demo_mode
        self.max_trade_amount = settings.max_trade_amount
        self.trading_enabled = settings.trading_enabled
        self.use_public_data_only = settings.use_public_data_only
    
    def _initialize_client(self):
        """Initialize Binance API client"""
        try:
            # Initialize public client for market data (no auth needed)
            self.public_client = Client("", "")  # Empty keys for public endpoints
            
            # Determine which environment to use
            use_testnet = settings.binance_use_testnet or settings.binance_testnet  # Support both old and new config
            
            # Select appropriate API keys based on environment
            if use_testnet:
                api_key = settings.binance_testnet_api_key or settings.binance_api_key
                api_secret = settings.binance_testnet_api_secret or settings.binance_api_secret
                logger.info("Using TESTNET environment")
            else:
                api_key = settings.binance_production_api_key or settings.binance_api_key
                api_secret = settings.binance_production_api_secret or settings.binance_api_secret
                logger.info(f"Using PRODUCTION environment (Demo Mode: {self.demo_mode})")
            
            # Check if we're using public data only mode
            if self.use_public_data_only:
                logger.info("Using public data only mode - no authentication required")
                self.client = self.public_client
            elif not api_key or not api_secret:
                logger.warning(f"API credentials not configured for {'testnet' if use_testnet else 'production'} - using public data only")
                self.client = self.public_client
                self.use_public_data_only = True
            else:
                # Initialize authenticated client
                self.client = Client(
                    api_key=api_key,
                    api_secret=api_secret
                )
                logger.info(f"Authenticated client initialized for {'testnet' if use_testnet else 'production'}")
            
            # Set API URL based on environment
            if use_testnet:
                self.client.API_URL = 'https://testnet.binance.vision/api'
                if self.public_client:
                    self.public_client.API_URL = 'https://testnet.binance.vision/api'
                logger.info("Using Binance TESTNET environment")
            
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
            # Use public API for production market data
            use_testnet = settings.binance_use_testnet or settings.binance_testnet
            if not use_testnet:
                try:
                    data = public_market_service.get_symbol_price(symbol)
                    return data['price']
                except Exception as e:
                    logger.warning(f"Public API failed, falling back to authenticated client: {e}")
            
            # Fallback to authenticated client
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
            # Use public API for production market data
            use_testnet = settings.binance_use_testnet or settings.binance_testnet
            if not use_testnet:
                try:
                    return public_market_service.get_klines(symbol, interval, limit)
                except Exception as e:
                    logger.warning(f"Public API failed, falling back to authenticated client: {e}")
            
            # Fallback to authenticated client
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
        Get real dual investment products from Binance API
        Returns empty list if unable to fetch products
        """
        try:
            self.ensure_initialized()
            
            if not self.client:
                logger.error("Binance client not initialized - check API credentials")
                return []
            
            # Initialize Dual Investment API service
            if not hasattr(self, '_dci_service'):
                from services.dual_investment_api_service import DualInvestmentAPIService
                self._dci_service = DualInvestmentAPIService(self.client)
            
            products = []
            
            # Define asset pairs to fetch
            asset_pairs = [
                ('BTC', 'USDT'),
                ('ETH', 'USDT'),
                ('BNB', 'USDT')
            ]
            
            for asset, quote in asset_pairs:
                try:
                    # BUY_LOW (PUT options) - invest USDT to potentially buy asset
                    logger.info(f"Fetching BUY_LOW products for {asset}")
                    put_products = self._dci_service.get_product_list('PUT', asset, quote)
                    converted_puts = self._convert_dci_products(put_products, 'BUY_LOW', asset, quote)
                    products.extend(converted_puts)
                    
                    # SELL_HIGH (CALL options) - invest asset to potentially get USDT
                    logger.info(f"Fetching SELL_HIGH products for {asset}")
                    call_products = self._dci_service.get_product_list('CALL', quote, asset)
                    converted_calls = self._convert_dci_products(call_products, 'SELL_HIGH', asset, quote)
                    products.extend(converted_calls)
                    
                except Exception as e:
                    logger.error(f"Failed to get products for {asset}/{quote}: {e}")
                    continue
            
            if products:
                logger.info(f"Successfully fetched {len(products)} dual investment products")
            else:
                logger.warning("No dual investment products available")
                
            return products
            
        except Exception as e:
            logger.error(f"Critical error in get_dual_investment_products: {e}", exc_info=True)
            return []
    
    def _convert_dci_products(
        self, 
        raw_products: List[Dict[str, Any]], 
        product_type: str,
        asset: str,
        quote: str
    ) -> List[Dict[str, Any]]:
        """
        Convert Binance API format to system format
        
        Args:
            raw_products: Raw product list from API
            product_type: 'BUY_LOW' or 'SELL_HIGH'
            asset: Asset symbol (e.g., 'BTC')
            quote: Quote currency (e.g., 'USDT')
            
        Returns:
            List of converted products
        """
        converted = []
        
        for product in raw_products:
            try:
                # Parse settlement date
                settle_timestamp = product.get('settleDate', 0)
                if settle_timestamp:
                    settlement_date = datetime.fromtimestamp(settle_timestamp / 1000)
                else:
                    settlement_date = datetime.now() + timedelta(days=product.get('duration', 1))
                
                # Get current price for the pair
                try:
                    current_price = self.get_symbol_price(f"{asset}{quote}")
                except:
                    current_price = float(product.get('strikePrice', 0))
                
                converted_product = {
                    'id': product.get('id', ''),
                    'type': product_type,
                    'asset': asset,
                    'currency': quote,
                    'strike_price': float(product.get('strikePrice', 0)),
                    'apy': float(product.get('apr', 0)),
                    'term_days': int(product.get('duration', 0)),
                    'min_amount': float(product.get('minAmount', 0)),
                    'max_amount': float(product.get('maxAmount', 0)),
                    'settlement_date': settlement_date,
                    'can_purchase': product.get('canPurchase', False),
                    'current_price': current_price,
                    # Additional fields from API
                    'purchase_end_time': product.get('purchaseEndTime'),
                    'is_auto_compound': product.get('isAutoCompoundEnable', False),
                    'auto_compound_plans': product.get('autoCompoundPlanList', [])
                }
                
                converted.append(converted_product)
                
            except Exception as e:
                logger.warning(f"Failed to convert product {product.get('id', 'unknown')}: {e}")
                continue
        
        logger.debug(f"Converted {len(converted)} {product_type} products for {asset}/{quote}")
        return converted
    
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
            # Use public API for production market data
            use_testnet = settings.binance_use_testnet or settings.binance_testnet
            if not use_testnet:
                try:
                    return public_market_service.get_24hr_ticker_stats(symbol)
                except Exception as e:
                    logger.warning(f"Public API failed, falling back to authenticated client: {e}")
            
            # Fallback to authenticated client
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
            
            # Only apply corrections for testnet data
            if settings.binance_testnet and (high_24h > last_price * 1.5 or low_24h < last_price * 0.5):
                logger.info(f"Testnet ticker data for {symbol} seems unrealistic, fetching hourly data")
                
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
        Subscribe to a dual investment product with safety checks
        """
        try:
            self.ensure_initialized()
            
            # Safety checks
            if not self.trading_enabled:
                return {
                    'success': False,
                    'error': 'Trading is disabled',
                    'message': 'Enable trading in settings to execute trades'
                }
            
            if amount > self.max_trade_amount:
                return {
                    'success': False,
                    'error': f'Amount exceeds maximum limit of {self.max_trade_amount} USDT',
                    'message': f'Please reduce amount to {self.max_trade_amount} USDT or less'
                }
            
            # Demo mode - simulate the subscription
            if self.demo_mode:
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
                
                logger.info(f"[DEMO MODE] Simulated dual investment subscription: {product_id} for ${amount}")
                return result
            
            # Production mode with testnet
            elif settings.binance_testnet:
                # Testnet simulation
                order_id = f"TEST_{int(time.time())}{random.randint(1000, 9999)}"
                result = {
                    'success': True,
                    'order_id': order_id,
                    'product_id': product_id,
                    'amount': amount,
                    'execution_price': self.get_symbol_price(product_id.split('-')[0] + 'USDT'),
                    'timestamp': datetime.utcnow().isoformat(),
                    'status': 'PENDING',
                    'message': 'Testnet dual investment subscription successful'
                }
                logger.info(f"[TESTNET] Dual investment subscription: {product_id} for ${amount}")
                return result
            else:
                # Production mode - real trading
                # TODO: Implement actual Binance Dual Investment API
                logger.warning("Production dual investment API integration pending")
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