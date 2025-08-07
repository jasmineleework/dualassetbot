"""
Testnet Dual Product Adapter
Generates realistic dual investment products based on testnet market data
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
from loguru import logger

class TestnetDualProductAdapter:
    """Adapter for generating dual investment products from testnet data"""
    
    def __init__(self, binance_service):
        self.binance = binance_service
        
    def generate_products_for_symbol(
        self, 
        symbol: str,
        terms: List[int] = [1, 3, 7, 14, 30]
    ) -> List[Dict[str, Any]]:
        """
        Generate dual investment products for a symbol with various terms
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            terms: List of term lengths in days
        """
        products = []
        asset = symbol.replace('USDT', '')
        
        try:
            # Get current market data
            current_price = self.binance.get_symbol_price(symbol)
            stats = self.binance.get_24hr_ticker_stats(symbol)
            
            # Calculate volatility metrics
            volatility = abs(stats['price_change_percent'])
            volume_24h = stats['volume']
            
            # Get historical data for better volatility estimation
            try:
                df = self.binance.get_klines(symbol, interval='1h', limit=168)  # 7 days
                returns = df['close'].pct_change().dropna()
                historical_volatility = returns.std() * np.sqrt(24 * 365)  # Annualized
            except:
                historical_volatility = volatility / 100  # Fallback
            
            for term_days in terms:
                # Generate BUY_LOW products
                buy_low_products = self._generate_buy_low_products(
                    asset, current_price, term_days, 
                    volatility, historical_volatility, volume_24h
                )
                products.extend(buy_low_products)
                
                # Generate SELL_HIGH products
                sell_high_products = self._generate_sell_high_products(
                    asset, current_price, term_days,
                    volatility, historical_volatility, volume_24h
                )
                products.extend(sell_high_products)
                
        except Exception as e:
            logger.error(f"Failed to generate products for {symbol}: {e}")
            
        return products
    
    def _generate_buy_low_products(
        self,
        asset: str,
        current_price: float,
        term_days: int,
        daily_volatility: float,
        historical_volatility: float,
        volume: float
    ) -> List[Dict[str, Any]]:
        """Generate BUY_LOW products with different strike prices"""
        products = []
        
        # Calculate strike price levels based on term and volatility
        # Longer terms have wider strike ranges
        term_factor = np.sqrt(term_days / 365)
        vol_adjustment = max(historical_volatility, 0.2) * term_factor
        
        # Generate multiple strike levels (2%, 5%, 8% below current)
        strike_percentages = [0.02, 0.05, 0.08]
        
        for strike_pct in strike_percentages:
            strike_price = current_price * (1 - strike_pct)
            
            # Calculate APY based on strike distance and volatility
            # Closer strikes = lower APY, higher volatility = higher APY
            base_apy = 0.08  # 8% base
            strike_bonus = strike_pct * 2  # 2x the strike percentage
            vol_bonus = min(historical_volatility * 0.5, 0.20)  # Up to 20% from volatility
            term_bonus = (30 - term_days) / 100  # Shorter terms get bonus
            
            apy = base_apy + strike_bonus + vol_bonus + term_bonus
            apy = min(apy, 0.99)  # Cap at 99% APY
            
            products.append({
                'id': f'{asset}-USDT-BUYLOW-{term_days}D-{int(strike_pct*100)}PCT-{datetime.now().strftime("%Y%m%d%H")}',
                'asset': asset,
                'currency': 'USDT',
                'type': 'BUY_LOW',
                'strike_price': round(strike_price, 2),
                'apy': round(apy, 4),
                'term_days': term_days,
                'min_amount': 10 if asset in ['BTC', 'ETH'] else 100,
                'max_amount': 50000,
                'settlement_date': datetime.now() + timedelta(days=term_days),
                'current_price': current_price,
                'exercise_probability': self._calculate_exercise_probability(
                    current_price, strike_price, term_days, historical_volatility, 'BUY_LOW'
                )
            })
            
        return products
    
    def _generate_sell_high_products(
        self,
        asset: str,
        current_price: float,
        term_days: int,
        daily_volatility: float,
        historical_volatility: float,
        volume: float
    ) -> List[Dict[str, Any]]:
        """Generate SELL_HIGH products with different strike prices"""
        products = []
        
        # Similar logic to BUY_LOW but strikes above current price
        term_factor = np.sqrt(term_days / 365)
        vol_adjustment = max(historical_volatility, 0.2) * term_factor
        
        # Generate multiple strike levels (2%, 5%, 8% above current)
        strike_percentages = [0.02, 0.05, 0.08]
        
        for strike_pct in strike_percentages:
            strike_price = current_price * (1 + strike_pct)
            
            # APY calculation for SELL_HIGH
            base_apy = 0.07  # Slightly lower base for sell high
            strike_bonus = strike_pct * 1.8
            vol_bonus = min(historical_volatility * 0.4, 0.15)
            term_bonus = (30 - term_days) / 120
            
            apy = base_apy + strike_bonus + vol_bonus + term_bonus
            apy = min(apy, 0.85)  # Cap at 85% APY
            
            # Calculate min/max amounts based on asset
            if asset == 'BTC':
                min_amount = 0.0001
                max_amount = 2
            elif asset == 'ETH':
                min_amount = 0.001
                max_amount = 20
            else:
                min_amount = 1
                max_amount = 10000
            
            products.append({
                'id': f'{asset}-USDT-SELLHIGH-{term_days}D-{int(strike_pct*100)}PCT-{datetime.now().strftime("%Y%m%d%H")}',
                'asset': asset,
                'currency': 'USDT',
                'type': 'SELL_HIGH',
                'strike_price': round(strike_price, 2),
                'apy': round(apy, 4),
                'term_days': term_days,
                'min_amount': min_amount,
                'max_amount': max_amount,
                'settlement_date': datetime.now() + timedelta(days=term_days),
                'current_price': current_price,
                'exercise_probability': self._calculate_exercise_probability(
                    current_price, strike_price, term_days, historical_volatility, 'SELL_HIGH'
                )
            })
            
        return products
    
    def _calculate_exercise_probability(
        self,
        current_price: float,
        strike_price: float,
        term_days: int,
        volatility: float,
        product_type: str
    ) -> float:
        """
        Calculate probability of option being exercised using simplified Black-Scholes
        """
        try:
            # Simplified probability calculation
            price_diff_pct = abs(strike_price - current_price) / current_price
            time_factor = np.sqrt(term_days / 365)
            expected_move = volatility * time_factor
            
            if product_type == 'BUY_LOW':
                # Probability that price goes below strike
                z_score = price_diff_pct / expected_move if expected_move > 0 else 0
            else:  # SELL_HIGH
                # Probability that price goes above strike
                z_score = price_diff_pct / expected_move if expected_move > 0 else 0
            
            # Convert z-score to probability (simplified normal CDF)
            prob = 0.5 * (1 - np.tanh(z_score))
            return round(max(0.01, min(0.99, prob)), 4)
            
        except Exception as e:
            logger.warning(f"Failed to calculate exercise probability: {e}")
            return 0.5  # Default to 50%
    
    def get_all_products(self) -> List[Dict[str, Any]]:
        """Get all available dual investment products"""
        products = []
        symbols = ['BTCUSDT', 'ETHUSDT']  # Can be extended
        
        for symbol in symbols:
            try:
                symbol_products = self.generate_products_for_symbol(symbol)
                products.extend(symbol_products)
                logger.info(f"Generated {len(symbol_products)} products for {symbol}")
            except Exception as e:
                logger.error(f"Failed to generate products for {symbol}: {e}")
                
        return products