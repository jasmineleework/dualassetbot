"""
Strategy Manager for ensemble strategy execution and selection
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed
from loguru import logger

from strategies.base_strategy import BaseStrategy, StrategySignal, SignalStrength, InvestmentDecision
from strategies.dual_investment_strategy import DualInvestmentStrategy

class StrategyManager:
    """
    Manages multiple strategies and combines their signals
    """
    
    def __init__(self):
        self.strategies: Dict[str, BaseStrategy] = {}
        self.strategy_weights = {}
        self.ensemble_method = "weighted_average"  # Options: weighted_average, voting, confidence_weighted
        
        # Initialize default strategies
        self._initialize_default_strategies()
    
    def _initialize_default_strategies(self):
        """Initialize default strategies"""
        dual_strategy = DualInvestmentStrategy()
        self.add_strategy(dual_strategy, weight=1.0)
        
    def add_strategy(self, strategy: BaseStrategy, weight: float = 1.0):
        """Add a strategy to the manager"""
        self.strategies[strategy.name] = strategy
        self.strategy_weights[strategy.name] = weight
        logger.info(f"Added strategy: {strategy.name} with weight {weight}")
    
    def remove_strategy(self, strategy_name: str):
        """Remove a strategy from the manager"""
        if strategy_name in self.strategies:
            del self.strategies[strategy_name]
            del self.strategy_weights[strategy_name]
            logger.info(f"Removed strategy: {strategy_name}")
    
    def update_strategy_weight(self, strategy_name: str, weight: float):
        """Update strategy weight"""
        if strategy_name in self.strategies:
            self.strategy_weights[strategy_name] = weight
            logger.info(f"Updated {strategy_name} weight to {weight}")
    
    def analyze_product(
        self,
        symbol: str,
        market_data: Dict[str, Any],
        product: Dict[str, Any],
        parallel: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze a product using all active strategies
        
        Returns:
            Dictionary with individual signals and ensemble result
        """
        active_strategies = {
            name: strategy for name, strategy in self.strategies.items() 
            if strategy.is_active
        }
        
        if not active_strategies:
            logger.warning("No active strategies available")
            return self._create_neutral_result(product)
        
        # Get signals from all strategies
        strategy_signals = {}
        
        if parallel and len(active_strategies) > 1:
            strategy_signals = self._analyze_parallel(
                active_strategies, symbol, market_data, product
            )
        else:
            strategy_signals = self._analyze_sequential(
                active_strategies, symbol, market_data, product
            )
        
        # Combine signals using ensemble method
        ensemble_signal = self._combine_signals(strategy_signals)
        
        # Generate final investment decision
        decision = self._make_ensemble_decision(
            ensemble_signal, product, strategy_signals
        )
        
        return {
            'strategy_signals': strategy_signals,
            'ensemble_signal': ensemble_signal,
            'investment_decision': decision,
            'timestamp': datetime.utcnow(),
            'symbol': symbol,
            'product_id': product.get('id')
        }
    
    def _analyze_parallel(
        self,
        strategies: Dict[str, BaseStrategy],
        symbol: str,
        market_data: Dict[str, Any],
        product: Dict[str, Any]
    ) -> Dict[str, StrategySignal]:
        """Analyze using parallel execution"""
        signals = {}
        
        with ThreadPoolExecutor(max_workers=len(strategies)) as executor:
            # Submit all strategy analyses
            future_to_strategy = {
                executor.submit(strategy.analyze, symbol, market_data, product): name
                for name, strategy in strategies.items()
            }
            
            # Collect results
            for future in as_completed(future_to_strategy):
                strategy_name = future_to_strategy[future]
                try:
                    signal = future.result(timeout=10)  # 10 second timeout
                    
                    # Validate signal
                    if strategies[strategy_name].validate_signal(signal):
                        signals[strategy_name] = signal
                    else:
                        logger.warning(f"Strategy {strategy_name} produced invalid signal")
                        
                except Exception as e:
                    logger.error(f"Strategy {strategy_name} failed: {e}")
        
        return signals
    
    def _analyze_sequential(
        self,
        strategies: Dict[str, BaseStrategy],
        symbol: str,
        market_data: Dict[str, Any],
        product: Dict[str, Any]
    ) -> Dict[str, StrategySignal]:
        """Analyze using sequential execution"""
        signals = {}
        
        for name, strategy in strategies.items():
            try:
                signal = strategy.analyze(symbol, market_data, product)
                
                if strategy.validate_signal(signal):
                    signals[name] = signal
                else:
                    logger.warning(f"Strategy {name} produced invalid signal")
                    
            except Exception as e:
                logger.error(f"Strategy {name} failed: {e}")
        
        return signals
    
    def _combine_signals(self, strategy_signals: Dict[str, StrategySignal]) -> StrategySignal:
        """Combine multiple strategy signals into ensemble signal"""
        if not strategy_signals:
            return self._create_neutral_signal()
        
        if len(strategy_signals) == 1:
            return list(strategy_signals.values())[0]
        
        if self.ensemble_method == "weighted_average":
            return self._weighted_average_ensemble(strategy_signals)
        elif self.ensemble_method == "voting":
            return self._voting_ensemble(strategy_signals)
        elif self.ensemble_method == "confidence_weighted":
            return self._confidence_weighted_ensemble(strategy_signals)
        else:
            return self._weighted_average_ensemble(strategy_signals)
    
    def _weighted_average_ensemble(self, signals: Dict[str, StrategySignal]) -> StrategySignal:
        """Combine signals using weighted average"""
        total_weight = 0
        weighted_signal = 0
        weighted_confidence = 0
        all_reasons = []
        metadata = {'individual_signals': {}}
        
        for name, signal in signals.items():
            weight = self.strategy_weights.get(name, 1.0)
            total_weight += weight
            
            weighted_signal += signal.signal.value * weight
            weighted_confidence += signal.confidence * weight
            all_reasons.extend([f"{name}: {reason}" for reason in signal.reasons])
            
            metadata['individual_signals'][name] = {
                'signal': signal.signal.name,
                'confidence': signal.confidence,
                'weight': weight
            }
        
        # Calculate ensemble values
        avg_signal_value = weighted_signal / total_weight if total_weight > 0 else 3
        avg_confidence = weighted_confidence / total_weight if total_weight > 0 else 0
        
        # Convert to signal strength
        ensemble_signal = SignalStrength(round(avg_signal_value))
        
        return StrategySignal(
            strategy_name="EnsembleStrategy",
            signal=ensemble_signal,
            confidence=avg_confidence,
            reasons=all_reasons,
            metadata=metadata
        )
    
    def _voting_ensemble(self, signals: Dict[str, StrategySignal]) -> StrategySignal:
        """Combine signals using majority voting"""
        votes = {strength: 0 for strength in SignalStrength}
        total_confidence = 0
        all_reasons = []
        
        for name, signal in signals.items():
            weight = self.strategy_weights.get(name, 1.0)
            votes[signal.signal] += weight
            total_confidence += signal.confidence
            all_reasons.extend([f"{name}: {reason}" for reason in signal.reasons])
        
        # Find majority vote
        winning_signal = max(votes, key=votes.get)
        ensemble_confidence = total_confidence / len(signals)
        
        return StrategySignal(
            strategy_name="EnsembleStrategy",
            signal=winning_signal,
            confidence=ensemble_confidence,
            reasons=all_reasons,
            metadata={'votes': {s.name: v for s, v in votes.items()}}
        )
    
    def _confidence_weighted_ensemble(self, signals: Dict[str, StrategySignal]) -> StrategySignal:
        """Weight strategies by their confidence levels"""
        total_confidence_weight = 0
        weighted_signal = 0
        all_reasons = []
        
        for name, signal in signals.items():
            base_weight = self.strategy_weights.get(name, 1.0)
            confidence_weight = base_weight * signal.confidence
            total_confidence_weight += confidence_weight
            
            weighted_signal += signal.signal.value * confidence_weight
            all_reasons.extend([f"{name}: {reason}" for reason in signal.reasons])
        
        if total_confidence_weight > 0:
            avg_signal_value = weighted_signal / total_confidence_weight
            avg_confidence = total_confidence_weight / sum(self.strategy_weights.get(name, 1.0) for name in signals.keys())
        else:
            avg_signal_value = 3
            avg_confidence = 0
        
        ensemble_signal = SignalStrength(round(avg_signal_value))
        
        return StrategySignal(
            strategy_name="EnsembleStrategy",
            signal=ensemble_signal,
            confidence=avg_confidence,
            reasons=all_reasons,
            metadata={'method': 'confidence_weighted'}
        )
    
    def _make_ensemble_decision(
        self,
        ensemble_signal: StrategySignal,
        product: Dict[str, Any],
        strategy_signals: Dict[str, StrategySignal]
    ) -> InvestmentDecision:
        """Make final investment decision based on ensemble signal"""
        
        # Use the main dual investment strategy for decision making
        main_strategy = self.strategies.get('DualInvestmentStrategy')
        if main_strategy and isinstance(main_strategy, DualInvestmentStrategy):
            return main_strategy.make_investment_decision(
                ensemble_signal,
                product,
                {'total_value': 10000, 'current_exposure': 0, 'max_risk_per_trade': 0.02}
            )
        
        # Fallback decision logic
        should_invest = (
            ensemble_signal.signal.value >= SignalStrength.BUY.value and
            ensemble_signal.confidence >= 0.6
        )
        
        return InvestmentDecision(
            should_invest=should_invest,
            product_id=product.get('id', ''),
            amount=1000 if should_invest else 0,
            expected_return=product.get('apy', 0.15) * (product.get('term_days', 7) / 365),
            risk_score=0.5,
            ai_score=ensemble_signal.confidence,
            reasons=ensemble_signal.reasons,
            warnings=[],
            metadata=ensemble_signal.metadata
        )
    
    def _create_neutral_result(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Create neutral result when no strategies available"""
        neutral_signal = self._create_neutral_signal()
        neutral_decision = InvestmentDecision(
            should_invest=False,
            product_id=product.get('id', ''),
            amount=0,
            expected_return=0,
            risk_score=1.0,
            ai_score=0,
            reasons=["No active strategies available"],
            warnings=["Strategy manager has no active strategies"],
            metadata={}
        )
        
        return {
            'strategy_signals': {},
            'ensemble_signal': neutral_signal,
            'investment_decision': neutral_decision,
            'timestamp': datetime.utcnow(),
            'product_id': product.get('id')
        }
    
    def _create_neutral_signal(self) -> StrategySignal:
        """Create neutral signal"""
        return StrategySignal(
            strategy_name="EnsembleStrategy",
            signal=SignalStrength.NEUTRAL,
            confidence=0.0,
            reasons=["No valid signals from strategies"],
            metadata={}
        )
    
    def get_strategy_performance(self) -> Dict[str, Any]:
        """Get performance metrics for all strategies"""
        performance = {}
        
        for name, strategy in self.strategies.items():
            performance[name] = {
                'name': name,
                'version': strategy.version,
                'is_active': strategy.is_active,
                'weight': self.strategy_weights.get(name, 1.0),
                'min_confidence': strategy.min_confidence
            }
        
        return performance
    
    def batch_analyze_products(
        self,
        symbol: str,
        market_data: Dict[str, Any],
        products: List[Dict[str, Any]],
        top_n: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Analyze multiple products and return top N recommendations
        
        Returns:
            List of analysis results sorted by AI score
        """
        results = []
        
        for product in products:
            try:
                result = self.analyze_product(symbol, market_data, product)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to analyze product {product.get('id')}: {e}")
        
        # Sort by AI score (descending)
        results.sort(
            key=lambda x: x['investment_decision'].ai_score,
            reverse=True
        )
        
        return results[:top_n]