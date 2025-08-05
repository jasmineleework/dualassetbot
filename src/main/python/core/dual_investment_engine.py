"""
Dual Investment Decision Engine - Core AI logic for making investment decisions
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from loguru import logger
from services.binance_service import binance_service
from services.market_analysis import market_analysis_service
from core.config import settings

class DualInvestmentEngine:
    """AI-powered engine for dual investment decisions"""
    
    def __init__(self):
        self.binance = binance_service
        self.market_analysis = market_analysis_service
        
    def analyze_market_conditions(self, symbol: str) -> Dict[str, Any]:
        """Comprehensive market analysis for a trading pair"""
        try:
            # Get historical data
            df = self.binance.get_klines(symbol, interval='1h', limit=168)  # 7 days of hourly data
            
            # Get current price and 24hr stats
            current_price = self.binance.get_symbol_price(symbol)
            ticker_stats = self.binance.get_24hr_ticker_stats(symbol)
            
            # Technical analysis
            trend = self.market_analysis.analyze_trend(df)
            signals = self.market_analysis.get_market_signals(df)
            support_resistance = self.market_analysis.calculate_support_resistance(df)
            
            # Volatility analysis
            atr = self.market_analysis.calculate_atr(df)
            current_atr = atr.iloc[-1]
            volatility_ratio = current_atr / current_price
            
            # Volume analysis
            volume_indicators = self.market_analysis.calculate_volume_indicators(df)
            
            return {
                'symbol': symbol,
                'current_price': current_price,
                'price_change_24h': ticker_stats['price_change_percent'],
                'volume_24h': ticker_stats['volume'],
                'trend': trend,
                'signals': signals,
                'support_resistance': support_resistance,
                'volatility': {
                    'atr': current_atr,
                    'volatility_ratio': volatility_ratio,
                    'risk_level': 'HIGH' if volatility_ratio > 0.05 else ('MEDIUM' if volatility_ratio > 0.02 else 'LOW')
                },
                'volume_analysis': {
                    'obv_trend': 'POSITIVE' if volume_indicators['obv'].iloc[-1] > volume_indicators['obv'].iloc[-10] else 'NEGATIVE',
                    'mfi': volume_indicators['mfi'].iloc[-1]
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze market conditions for {symbol}: {e}")
            raise
    
    def calculate_optimal_strike_price(
        self, 
        current_price: float, 
        product_type: str, 
        market_analysis: Dict[str, Any]
    ) -> float:
        """Calculate optimal strike price based on market analysis"""
        
        # Base calculation using support/resistance levels
        support = market_analysis['support_resistance']['support']
        resistance = market_analysis['support_resistance']['resistance']
        volatility_ratio = market_analysis['volatility']['volatility_ratio']
        
        if product_type == 'BUY_LOW':
            # For buy low, set strike price below current price
            # Use support level as reference
            base_strike = support * (1 + volatility_ratio)
            
            # Adjust based on trend
            if market_analysis['trend']['trend'] == 'BULLISH':
                # In bullish trend, can set slightly higher strike
                strike_price = min(base_strike * 1.02, current_price * 0.98)
            else:
                # In bearish trend, be more conservative
                strike_price = base_strike * 0.98
                
        else:  # SELL_HIGH
            # For sell high, set strike price above current price
            # Use resistance level as reference
            base_strike = resistance * (1 - volatility_ratio)
            
            # Adjust based on trend
            if market_analysis['trend']['trend'] == 'BEARISH':
                # In bearish trend, can set slightly lower strike
                strike_price = max(base_strike * 0.98, current_price * 1.02)
            else:
                # In bullish trend, be more optimistic
                strike_price = base_strike * 1.02
        
        return round(strike_price, 2)
    
    def evaluate_dual_investment_opportunity(
        self, 
        product: Dict[str, Any], 
        market_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Evaluate a specific dual investment product opportunity"""
        
        current_price = market_analysis['current_price']
        strike_price = product['strike_price']
        apy = product['apy']
        
        # Calculate probability of exercise based on technical analysis
        if product['type'] == 'BUY_LOW':
            # Probability that price will fall to strike price
            price_distance = (current_price - strike_price) / current_price
            
            # Base probability calculation
            if market_analysis['signals']['recommendation'] in ['SELL', 'STRONG_SELL']:
                base_probability = 0.6
            elif market_analysis['trend']['trend'] == 'BEARISH':
                base_probability = 0.5
            else:
                base_probability = 0.3
                
        else:  # SELL_HIGH
            # Probability that price will rise to strike price
            price_distance = (strike_price - current_price) / current_price
            
            # Base probability calculation
            if market_analysis['signals']['recommendation'] in ['BUY', 'STRONG_BUY']:
                base_probability = 0.6
            elif market_analysis['trend']['trend'] == 'BULLISH':
                base_probability = 0.5
            else:
                base_probability = 0.3
        
        # Adjust probability based on distance and volatility
        volatility_factor = market_analysis['volatility']['volatility_ratio']
        distance_factor = max(0, 1 - (price_distance / (volatility_factor * 5)))
        
        exercise_probability = base_probability * distance_factor
        
        # Calculate expected return
        # If exercised: get the asset at favorable price + interest
        # If not exercised: keep original asset + interest
        expected_return = apy * (product['term_days'] / 365)
        
        # Risk-adjusted score (0-100)
        risk_score = 100 * (expected_return / (1 + market_analysis['volatility']['volatility_ratio']))
        
        # Recommendation based on multiple factors
        recommend = False
        reasons = []
        
        if apy >= settings.min_apr_threshold:
            recommend = True
            reasons.append(f"APY {apy*100:.1f}% meets minimum threshold")
        
        if exercise_probability > 0.4 and exercise_probability < 0.7:
            recommend = True
            reasons.append(f"Exercise probability {exercise_probability:.1%} is in optimal range")
        
        if risk_score > 50:
            recommend = True
            reasons.append(f"Risk-adjusted score {risk_score:.1f} is favorable")
        
        return {
            'product_id': product['id'],
            'recommend': recommend,
            'exercise_probability': exercise_probability,
            'expected_return': expected_return,
            'risk_score': risk_score,
            'reasons': reasons,
            'analysis_summary': {
                'current_price': current_price,
                'strike_price': strike_price,
                'price_distance': f"{price_distance:.2%}",
                'market_trend': market_analysis['trend']['trend'],
                'volatility': market_analysis['volatility']['risk_level']
            }
        }
    
    def select_best_product(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Select the best dual investment product for a given symbol"""
        try:
            # Get market analysis
            market_analysis = self.analyze_market_conditions(symbol)
            
            # Get available products
            products = self.binance.get_dual_investment_products()
            
            # Filter products for this symbol
            asset = symbol.replace('USDT', '')
            relevant_products = [p for p in products if p['asset'] == asset]
            
            if not relevant_products:
                logger.warning(f"No dual investment products found for {asset}")
                return None
            
            # Evaluate each product
            evaluations = []
            for product in relevant_products:
                evaluation = self.evaluate_dual_investment_opportunity(product, market_analysis)
                evaluation['product'] = product
                evaluations.append(evaluation)
            
            # Sort by risk score and filter recommended products
            recommended = [e for e in evaluations if e['recommend']]
            if not recommended:
                logger.info("No products meet recommendation criteria")
                return None
            
            # Select best product
            best = max(recommended, key=lambda x: x['risk_score'])
            
            return {
                'selected_product': best['product'],
                'evaluation': best,
                'market_analysis': market_analysis,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to select best product for {symbol}: {e}")
            return None
    
    def calculate_position_size(
        self, 
        product: Dict[str, Any], 
        total_capital: float,
        existing_positions: List[Dict[str, Any]]
    ) -> float:
        """Calculate optimal position size based on risk management"""
        
        # Maximum single position size
        max_position = total_capital * settings.max_single_investment_ratio
        
        # Check existing exposure to this asset
        asset_exposure = sum(
            p['amount'] for p in existing_positions 
            if p['asset'] == product['asset']
        )
        
        # Available capital for this asset
        available = max_position - asset_exposure
        
        # Minimum of available capital and product limits
        position_size = min(
            available,
            product['max_amount'],
            max(product['min_amount'], available * 0.5)  # Use 50% of available
        )
        
        # Round to appropriate decimal places
        if product['currency'] == 'USDT':
            position_size = round(position_size, 2)
        else:
            position_size = round(position_size, 8)
        
        return position_size
    
    def generate_investment_report(
        self, 
        decision: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate detailed investment decision report"""
        
        product = decision['selected_product']
        evaluation = decision['evaluation']
        market = decision['market_analysis']
        
        report = {
            'decision_id': f"DI_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'timestamp': datetime.now().isoformat(),
            'product_details': {
                'id': product['id'],
                'type': product['type'],
                'asset': product['asset'],
                'strike_price': product['strike_price'],
                'apy': f"{product['apy']*100:.1f}%",
                'term_days': product['term_days']
            },
            'market_conditions': {
                'current_price': market['current_price'],
                'trend': market['trend']['trend'],
                'trend_strength': market['trend']['strength'],
                'volatility': market['volatility']['risk_level'],
                'volume_trend': market['volume_analysis']['obv_trend'],
                'price_change_24h': f"{market['price_change_24h']:.2f}%"
            },
            'technical_indicators': {
                'rsi_signal': market['signals']['rsi_signal'],
                'macd_signal': market['signals']['macd_signal'],
                'bb_signal': market['signals']['bb_signal'],
                'overall_signal': market['signals']['recommendation']
            },
            'decision_metrics': {
                'exercise_probability': f"{evaluation['exercise_probability']:.1%}",
                'expected_return': f"{evaluation['expected_return']*100:.2f}%",
                'risk_score': evaluation['risk_score'],
                'recommendation': 'INVEST' if evaluation['recommend'] else 'SKIP',
                'reasons': evaluation['reasons']
            }
        }
        
        return report

# Create singleton instance
dual_investment_engine = DualInvestmentEngine()