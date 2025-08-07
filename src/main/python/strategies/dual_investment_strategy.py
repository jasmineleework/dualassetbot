"""
Dual Investment Strategy Implementation
"""
from typing import Dict, Any, List, Tuple
import numpy as np
from datetime import datetime, timedelta
from strategies.base_strategy import (
    BaseStrategy, StrategySignal, SignalStrength, InvestmentDecision
)
from loguru import logger

class DualInvestmentStrategy(BaseStrategy):
    """
    Main strategy for dual investment product selection and timing
    
    This strategy considers:
    - Market trend and momentum
    - Volatility and risk levels
    - Strike price attractiveness
    - APY vs risk ratio
    - Exercise probability
    """
    
    def __init__(self):
        super().__init__(name="DualInvestmentStrategy", version="1.0.0")
        
        # Strategy parameters
        self.min_apy = 0.10  # Minimum 10% APY
        self.max_exercise_prob = 0.5  # Maximum 50% exercise probability
        self.optimal_volatility_range = (0.15, 0.35)  # 15-35% annual volatility
        self.trend_weight = 0.3
        self.apy_weight = 0.25
        self.risk_weight = 0.25
        self.technical_weight = 0.2
        
    def analyze(
        self,
        symbol: str,
        market_data: Dict[str, Any],
        product: Dict[str, Any]
    ) -> StrategySignal:
        """Analyze market and generate signal for dual investment"""
        
        reasons = []
        scores = []
        
        # 1. Trend Analysis
        trend_score = self._analyze_trend(market_data)
        scores.append(('trend', trend_score, self.trend_weight))
        if trend_score > 0.7:
            reasons.append(f"Strong {market_data.get('trend', {}).get('trend', 'NEUTRAL')} trend detected")
        elif trend_score < 0.3:
            reasons.append("Weak or adverse trend")
        
        # 2. APY Attractiveness
        apy_score = self._evaluate_apy(product)
        scores.append(('apy', apy_score, self.apy_weight))
        if apy_score > 0.8:
            reasons.append(f"Excellent APY of {product['apy']*100:.2f}%")
        elif apy_score < 0.4:
            reasons.append(f"Low APY of {product['apy']*100:.2f}%")
        
        # 3. Risk Assessment
        risk_score = self._assess_risk(product, market_data)
        scores.append(('risk', risk_score, self.risk_weight))
        if risk_score > 0.7:
            reasons.append("Favorable risk-reward ratio")
        elif risk_score < 0.3:
            reasons.append("High risk level detected")
        
        # 4. Technical Indicators
        technical_score = self._analyze_technicals(market_data)
        scores.append(('technical', technical_score, self.technical_weight))
        if technical_score > 0.7:
            reasons.append("Positive technical indicators")
        elif technical_score < 0.3:
            reasons.append("Negative technical signals")
        
        # Calculate weighted average score
        total_score = sum(score * weight for _, score, weight in scores)
        
        # Determine signal strength
        if total_score >= 0.8:
            signal = SignalStrength.STRONG_BUY
        elif total_score >= 0.65:
            signal = SignalStrength.BUY
        elif total_score >= 0.35:
            signal = SignalStrength.NEUTRAL
        elif total_score >= 0.2:
            signal = SignalStrength.SELL
        else:
            signal = SignalStrength.STRONG_SELL
        
        return StrategySignal(
            strategy_name=self.name,
            signal=signal,
            confidence=total_score,
            reasons=reasons,
            metadata={
                'scores': {name: score for name, score, _ in scores},
                'product_id': product.get('id'),
                'symbol': symbol
            }
        )
    
    def calculate_position_size(
        self,
        signal: StrategySignal,
        portfolio_value: float,
        current_exposure: float,
        max_risk_per_trade: float
    ) -> float:
        """Calculate position size using Kelly Criterion with safety factor"""
        
        # Kelly fraction = (p * b - q) / b
        # where p = probability of win, q = 1-p, b = win/loss ratio
        
        confidence = signal.confidence
        expected_return = signal.metadata.get('expected_return', 0.15)
        
        # Simplified Kelly with safety factor
        kelly_fraction = confidence * expected_return
        safety_factor = 0.25  # Use only 25% of Kelly suggestion
        
        position_fraction = kelly_fraction * safety_factor
        
        # Apply additional constraints
        max_position_fraction = min(
            max_risk_per_trade,
            0.1,  # Max 10% per position
            1.0 - (current_exposure / portfolio_value) if portfolio_value > 0 else 0
        )
        
        position_fraction = min(position_fraction, max_position_fraction)
        position_size = portfolio_value * position_fraction
        
        return round(position_size, 2)
    
    def evaluate_product(
        self,
        product: Dict[str, Any],
        market_conditions: Dict[str, Any]
    ) -> Tuple[float, List[str]]:
        """Evaluate a specific dual investment product"""
        
        score = 0
        reasons = []
        
        # 1. APY evaluation (0-0.3)
        apy = product.get('apy', 0)
        if apy >= 0.30:  # 30%+ APY
            score += 0.3
            reasons.append(f"Excellent APY: {apy*100:.2f}%")
        elif apy >= 0.20:  # 20%+ APY
            score += 0.2
            reasons.append(f"Good APY: {apy*100:.2f}%")
        elif apy >= self.min_apy:
            score += 0.1
            reasons.append(f"Acceptable APY: {apy*100:.2f}%")
        else:
            reasons.append(f"APY below minimum: {apy*100:.2f}%")
        
        # 2. Strike price evaluation (0-0.3)
        current_price = product.get('current_price', 0)
        strike_price = product.get('strike_price', 0)
        product_type = product.get('type', '')
        
        if current_price and strike_price:
            distance = abs(strike_price - current_price) / current_price
            
            if product_type == 'BUY_LOW':
                # For BUY_LOW, we want strike below current
                if 0.03 <= distance <= 0.08:  # 3-8% below
                    score += 0.3
                    reasons.append(f"Optimal strike distance: {distance*100:.2f}% below")
                elif 0.02 <= distance <= 0.10:
                    score += 0.2
                    reasons.append(f"Good strike distance: {distance*100:.2f}% below")
                else:
                    score += 0.1
                    reasons.append(f"Suboptimal strike distance")
            
            elif product_type == 'SELL_HIGH':
                # For SELL_HIGH, we want strike above current
                if 0.03 <= distance <= 0.08:  # 3-8% above
                    score += 0.3
                    reasons.append(f"Optimal strike distance: {distance*100:.2f}% above")
                elif 0.02 <= distance <= 0.10:
                    score += 0.2
                    reasons.append(f"Good strike distance: {distance*100:.2f}% above")
                else:
                    score += 0.1
                    reasons.append(f"Suboptimal strike distance")
        
        # 3. Exercise probability (0-0.2)
        exercise_prob = product.get('exercise_probability', 0.5)
        if exercise_prob <= 0.2:
            score += 0.2
            reasons.append(f"Low exercise probability: {exercise_prob*100:.2f}%")
        elif exercise_prob <= 0.35:
            score += 0.15
            reasons.append(f"Moderate exercise probability: {exercise_prob*100:.2f}%")
        elif exercise_prob <= self.max_exercise_prob:
            score += 0.1
            reasons.append(f"Acceptable exercise probability: {exercise_prob*100:.2f}%")
        else:
            reasons.append(f"High exercise probability: {exercise_prob*100:.2f}%")
        
        # 4. Term evaluation (0-0.2)
        term_days = product.get('term_days', 7)
        volatility = market_conditions.get('volatility', {}).get('volatility_ratio', 0.02)
        
        # Shorter terms in low volatility, longer terms in high volatility
        if volatility < 0.02:  # Low volatility
            if term_days <= 3:
                score += 0.2
                reasons.append(f"Short term suitable for low volatility")
            else:
                score += 0.1
        elif volatility > 0.05:  # High volatility
            if term_days >= 7:
                score += 0.2
                reasons.append(f"Longer term suitable for high volatility")
            else:
                score += 0.1
        else:  # Medium volatility
            if 3 <= term_days <= 7:
                score += 0.15
                reasons.append(f"Term matches volatility conditions")
            else:
                score += 0.1
        
        return score, reasons
    
    def _analyze_trend(self, market_data: Dict[str, Any]) -> float:
        """Analyze market trend and return score 0-1"""
        trend_info = market_data.get('trend', {})
        trend = trend_info.get('trend', 'NEUTRAL')
        strength = trend_info.get('strength', 0.5)
        
        # Score based on trend direction and strength
        if trend == 'BULLISH':
            return min(0.5 + strength * 0.5, 1.0)
        elif trend == 'BEARISH':
            return max(0.5 - strength * 0.3, 0.2)
        else:  # NEUTRAL
            return 0.5
    
    def _evaluate_apy(self, product: Dict[str, Any]) -> float:
        """Evaluate APY and return score 0-1"""
        apy = product.get('apy', 0)
        
        if apy < self.min_apy:
            return 0.0
        elif apy >= 0.50:  # 50%+ APY
            return 1.0
        elif apy >= 0.30:  # 30%+ APY
            return 0.8 + (apy - 0.30) * 1.0  # Linear scale 0.8-1.0
        elif apy >= 0.20:  # 20%+ APY
            return 0.6 + (apy - 0.20) * 2.0  # Linear scale 0.6-0.8
        else:
            return 0.3 + (apy - self.min_apy) * 3.0  # Linear scale 0.3-0.6
    
    def _assess_risk(self, product: Dict[str, Any], market_data: Dict[str, Any]) -> float:
        """Assess risk and return score 0-1 (higher = lower risk)"""
        risk_factors = []
        
        # Exercise probability risk
        exercise_prob = product.get('exercise_probability', 0.5)
        if exercise_prob <= 0.2:
            risk_factors.append(0.9)
        elif exercise_prob <= 0.35:
            risk_factors.append(0.7)
        elif exercise_prob <= 0.5:
            risk_factors.append(0.5)
        else:
            risk_factors.append(0.2)
        
        # Volatility risk
        volatility = market_data.get('volatility', {})
        vol_ratio = volatility.get('volatility_ratio', 0.02)
        
        if self.optimal_volatility_range[0] <= vol_ratio <= self.optimal_volatility_range[1]:
            risk_factors.append(0.8)
        elif vol_ratio < self.optimal_volatility_range[0]:
            risk_factors.append(0.6)  # Too low volatility = less premium
        else:
            risk_factors.append(0.3)  # Too high volatility = high risk
        
        # Market regime risk
        risk_level = volatility.get('risk_level', 'MEDIUM')
        if risk_level == 'LOW':
            risk_factors.append(0.9)
        elif risk_level == 'MEDIUM':
            risk_factors.append(0.6)
        else:
            risk_factors.append(0.3)
        
        return np.mean(risk_factors) if risk_factors else 0.5
    
    def _analyze_technicals(self, market_data: Dict[str, Any]) -> float:
        """Analyze technical indicators and return score 0-1"""
        signals = market_data.get('signals', {})
        
        scores = []
        
        # RSI
        rsi = signals.get('rsi', 50)
        if 30 <= rsi <= 70:  # Not overbought/oversold
            scores.append(0.7)
        elif 20 <= rsi <= 80:
            scores.append(0.5)
        else:
            scores.append(0.2)
        
        # MACD
        macd_signal = signals.get('macd_signal', 'NEUTRAL')
        if macd_signal == 'BUY':
            scores.append(0.8)
        elif macd_signal == 'NEUTRAL':
            scores.append(0.5)
        else:
            scores.append(0.2)
        
        # Moving averages
        ma_signal = signals.get('ma_signal', 'NEUTRAL')
        if ma_signal == 'BULLISH':
            scores.append(0.8)
        elif ma_signal == 'NEUTRAL':
            scores.append(0.5)
        else:
            scores.append(0.2)
        
        # Support/Resistance
        support_resistance = market_data.get('support_resistance', {})
        current_price = market_data.get('current_price', 0)
        support = support_resistance.get('support', 0)
        resistance = support_resistance.get('resistance', 0)
        
        if support and resistance and current_price:
            position = (current_price - support) / (resistance - support)
            if 0.3 <= position <= 0.7:  # Middle of range
                scores.append(0.7)
            elif 0.2 <= position <= 0.8:
                scores.append(0.5)
            else:
                scores.append(0.3)
        
        return np.mean(scores) if scores else 0.5
    
    def make_investment_decision(
        self,
        signal: StrategySignal,
        product: Dict[str, Any],
        portfolio_info: Dict[str, Any]
    ) -> InvestmentDecision:
        """Make final investment decision based on signal and constraints"""
        
        should_invest = (
            signal.signal.value >= SignalStrength.BUY.value and
            signal.confidence >= self.min_confidence
        )
        
        # Calculate position size
        amount = 0
        if should_invest:
            amount = self.calculate_position_size(
                signal,
                portfolio_info.get('total_value', 10000),
                portfolio_info.get('current_exposure', 0),
                portfolio_info.get('max_risk_per_trade', 0.02)
            )
            
            # Check minimum amount
            min_amount = product.get('min_amount', 100)
            if amount < min_amount:
                should_invest = False
                signal.reasons.append(f"Position size {amount} below minimum {min_amount}")
        
        # Calculate expected return
        apy = product.get('apy', 0)
        term_days = product.get('term_days', 7)
        exercise_prob = product.get('exercise_probability', 0.5)
        
        # Simple expected return calculation
        period_return = apy * (term_days / 365)
        expected_return = period_return * (1 - exercise_prob)
        
        # Risk score (0-1, higher = more risky)
        risk_score = 1 - self._assess_risk(product, signal.metadata)
        
        warnings = []
        if risk_score > 0.7:
            warnings.append("High risk detected")
        if exercise_prob > 0.4:
            warnings.append(f"High exercise probability: {exercise_prob*100:.1f}%")
        
        return InvestmentDecision(
            should_invest=should_invest,
            product_id=product.get('id', ''),
            amount=amount,
            expected_return=expected_return,
            risk_score=risk_score,
            ai_score=signal.confidence,
            reasons=signal.reasons,
            warnings=warnings,
            metadata={
                'signal_strength': signal.signal.name,
                'strategy_scores': signal.metadata.get('scores', {}),
                'apy': apy,
                'term_days': term_days,
                'exercise_probability': exercise_prob
            }
        )