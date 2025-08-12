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
from strategies.strategy_manager import StrategyManager
from core.database import get_db
from dao.strategy_log import StrategyLogDAO
from models.strategy_log import DecisionType
import time

class DualInvestmentEngine:
    """AI-powered engine for dual investment decisions"""
    
    def __init__(self):
        self.binance = binance_service
        self.market_analysis = market_analysis_service
        self.strategy_manager = StrategyManager()
        self.user_id = "default"  # Default user for now
        
    def analyze_market_conditions(self, symbol: str) -> Dict[str, Any]:
        """Comprehensive market analysis for a trading pair"""
        try:
            # Ensure Binance service is initialized
            self.binance.ensure_initialized()
            
            # Get historical data
            df = self.binance.get_klines(symbol, interval='1h', limit=168)  # 7 days of hourly data
            
            # Get current price and 24hr stats
            current_price = self.binance.get_symbol_price(symbol)
            ticker_stats = self.binance.get_24hr_ticker_stats(symbol)
            
            # Technical analysis
            trend_data = self.market_analysis.analyze_trend(df)
            signals_data = self.market_analysis.get_market_signals(df)
            support_resistance = self.market_analysis.calculate_support_resistance(df)
            
            # Extract string values for trend (keep backward compatibility)
            trend = {
                'trend': trend_data.get('trend'),
                'strength': trend_data.get('strength')
            }
            
            # Extract string values for signals (keep backward compatibility)
            signals = {
                'rsi_signal': signals_data.get('rsi_signal'),
                'macd_signal': signals_data.get('macd_signal'),
                'bb_signal': signals_data.get('bb_signal'),
                'recommendation': signals_data.get('recommendation')
            }
            
            # Merge numeric indicators if needed
            if 'indicators' in trend_data:
                trend['indicators'] = trend_data['indicators']
            if 'indicators' in signals_data:
                signals['indicators'] = signals_data['indicators']
            
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
    
    def get_ai_recommendations(self, symbol: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get AI-powered investment recommendations using strategy ensemble
        
        Args:
            symbol: Trading pair symbol
            limit: Maximum number of recommendations
            
        Returns:
            List of investment recommendations with AI scores and analysis
        """
        try:
            start_time = time.time()
            
            # Get comprehensive market analysis
            market_data = self.analyze_market_conditions(symbol)
            
            # Get available products
            products = self.binance.get_dual_investment_products()
            
            # Filter products for this symbol
            asset = symbol.replace('USDT', '')
            relevant_products = [
                p for p in products 
                if p.get('asset') == asset
            ]
            
            if not relevant_products:
                logger.warning(f"No dual investment products found for {asset}")
                return []
            
            # Create product lookup map for quick access
            product_map = {p['id']: p for p in relevant_products}
            
            # Use strategy manager for batch analysis
            recommendations = []
            
            # Analyze products using strategy ensemble
            results = self.strategy_manager.batch_analyze_products(
                symbol, market_data, relevant_products, limit
            )
            
            for result in results:
                try:
                    decision = result['investment_decision']
                    
                    # Log strategy decision to database
                    try:
                        with next(get_db()) as db:
                            dao = StrategyLogDAO(db)
                            dao.log_decision(
                                db=db,
                                user_id=self.user_id,
                                strategy_name="DualInvestmentEngine",
                                decision_type=DecisionType.INVEST if decision.should_invest else DecisionType.SKIP,
                                symbol=symbol,
                                ai_score=decision.ai_score,
                                decision_made=decision.should_invest,
                                reasons=decision.reasons,
                                market_price=market_data.get('current_price'),
                                market_trend=market_data.get('trend', {}).get('trend'),
                                volatility=market_data.get('volatility', {}).get('volatility_ratio'),
                                expected_return=decision.expected_return,
                                risk_score=decision.risk_score,
                                amount=decision.amount,
                                product_id=decision.product_id,
                                technical_indicators=market_data.get('signals'),
                                support_resistance=market_data.get('support_resistance'),
                                warnings=decision.warnings
                            )
                    except Exception as db_error:
                        logger.warning(f"Failed to log decision to database: {db_error}")
                    
                    # Get full product details
                    product_details = product_map.get(decision.product_id, {})
                    
                    # Format recommendation
                    recommendation_level = self._get_recommendation_level(decision)
                    
                    recommendations.append({
                        'product_id': decision.product_id,
                        'should_invest': decision.should_invest,
                        'amount': decision.amount,
                        'ai_score': decision.ai_score,
                        'expected_return': decision.expected_return,
                        'risk_score': decision.risk_score,
                        'recommendation': recommendation_level,
                        'reasons': decision.reasons,
                        'warnings': decision.warnings,
                        'strategy_signals': result.get('strategy_signals', {}),
                        'ensemble_signal': result.get('ensemble_signal'),
                        'market_analysis': market_data,
                        'metadata': decision.metadata,
                        'product_details': product_details  # Add full product information
                    })
                    
                except Exception as e:
                    logger.error(f"Failed to process recommendation: {e}")
                    continue
            
            execution_time = time.time() - start_time
            logger.info(f"Generated {len(recommendations)} AI recommendations for {symbol} in {execution_time:.3f}s")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to make AI recommendations for {symbol}: {e}")
            raise
    
    def _get_recommendation_level(self, decision) -> str:
        """Get human-readable recommendation level"""
        if not decision.should_invest:
            return "SKIP"
        elif decision.ai_score >= 0.8:
            return "STRONG_BUY"
        elif decision.ai_score >= 0.65:
            return "BUY"
        elif decision.ai_score >= 0.5:
            return "CONSIDER"
        else:
            return "WEAK_BUY"

# Create singleton instance
dual_investment_engine = DualInvestmentEngine()