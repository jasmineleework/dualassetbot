"""
Base Strategy Abstract Class
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
from loguru import logger

class SignalStrength(Enum):
    """Signal strength levels"""
    STRONG_BUY = 5
    BUY = 4
    NEUTRAL = 3
    SELL = 2
    STRONG_SELL = 1

@dataclass
class StrategySignal:
    """Strategy signal result"""
    strategy_name: str
    signal: SignalStrength
    confidence: float  # 0-1
    reasons: List[str]
    metadata: Dict[str, Any]
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()

@dataclass
class InvestmentDecision:
    """Investment decision result"""
    should_invest: bool
    product_id: str
    amount: float
    expected_return: float
    risk_score: float
    ai_score: float
    reasons: List[str]
    warnings: List[str]
    metadata: Dict[str, Any]

class BaseStrategy(ABC):
    """Abstract base class for all trading strategies"""
    
    def __init__(self, name: str, version: str = "1.0.0"):
        self.name = name
        self.version = version
        self.is_active = True
        self.weight = 1.0  # Strategy weight in ensemble
        self.min_confidence = 0.6  # Minimum confidence to generate signal
        
    @abstractmethod
    def analyze(
        self,
        symbol: str,
        market_data: Dict[str, Any],
        product: Dict[str, Any]
    ) -> StrategySignal:
        """
        Analyze market conditions and generate trading signal
        
        Args:
            symbol: Trading pair symbol
            market_data: Current market data and indicators
            product: Dual investment product details
            
        Returns:
            StrategySignal with recommendation
        """
        pass
    
    @abstractmethod
    def calculate_position_size(
        self,
        signal: StrategySignal,
        portfolio_value: float,
        current_exposure: float,
        max_risk_per_trade: float
    ) -> float:
        """
        Calculate optimal position size
        
        Args:
            signal: Strategy signal
            portfolio_value: Total portfolio value
            current_exposure: Current exposure in this asset
            max_risk_per_trade: Maximum risk per trade
            
        Returns:
            Recommended position size
        """
        pass
    
    @abstractmethod
    def evaluate_product(
        self,
        product: Dict[str, Any],
        market_conditions: Dict[str, Any]
    ) -> Tuple[float, List[str]]:
        """
        Evaluate a specific dual investment product
        
        Args:
            product: Product details
            market_conditions: Current market conditions
            
        Returns:
            Tuple of (score 0-1, list of evaluation reasons)
        """
        pass
    
    def validate_signal(self, signal: StrategySignal) -> bool:
        """Validate signal meets minimum requirements"""
        if signal.confidence < self.min_confidence:
            logger.debug(f"{self.name}: Signal confidence {signal.confidence} below minimum {self.min_confidence}")
            return False
        return True
    
    def adjust_for_market_regime(
        self,
        signal: StrategySignal,
        market_regime: str
    ) -> StrategySignal:
        """
        Adjust signal based on market regime
        
        Args:
            signal: Original signal
            market_regime: Current market regime (BULL, BEAR, RANGE)
            
        Returns:
            Adjusted signal
        """
        # Default implementation - can be overridden
        if market_regime == "BEAR" and signal.signal.value >= 4:
            # Reduce bullish signals in bear market
            signal.confidence *= 0.8
            signal.reasons.append(f"Confidence reduced due to {market_regime} market")
        elif market_regime == "BULL" and signal.signal.value <= 2:
            # Reduce bearish signals in bull market
            signal.confidence *= 0.8
            signal.reasons.append(f"Confidence reduced due to {market_regime} market")
            
        return signal
    
    def combine_with_risk_management(
        self,
        decision: InvestmentDecision,
        risk_params: Dict[str, Any]
    ) -> InvestmentDecision:
        """
        Apply risk management rules to decision
        
        Args:
            decision: Original decision
            risk_params: Risk management parameters
            
        Returns:
            Risk-adjusted decision
        """
        max_position = risk_params.get('max_position_size', float('inf'))
        max_exposure = risk_params.get('max_total_exposure', float('inf'))
        current_exposure = risk_params.get('current_exposure', 0)
        
        # Adjust amount based on risk limits
        if decision.amount > max_position:
            decision.amount = max_position
            decision.warnings.append(f"Position size limited to {max_position}")
        
        if current_exposure + decision.amount > max_exposure:
            decision.amount = max(0, max_exposure - current_exposure)
            if decision.amount == 0:
                decision.should_invest = False
                decision.warnings.append("Maximum exposure reached")
            else:
                decision.warnings.append(f"Position reduced to stay within exposure limit")
        
        # Adjust based on risk score
        if decision.risk_score > risk_params.get('max_risk_score', 0.7):
            decision.should_invest = False
            decision.warnings.append(f"Risk score {decision.risk_score} exceeds maximum")
        
        return decision
    
    def log_decision(
        self,
        decision: InvestmentDecision,
        execution_time: float
    ):
        """Log strategy decision"""
        logger.info(
            f"{self.name} Decision: "
            f"Invest={decision.should_invest}, "
            f"Amount={decision.amount}, "
            f"Expected Return={decision.expected_return:.2%}, "
            f"Risk={decision.risk_score:.2f}, "
            f"AI Score={decision.ai_score:.2f}, "
            f"Execution Time={execution_time:.3f}s"
        )
        
        if decision.reasons:
            logger.debug(f"Reasons: {', '.join(decision.reasons)}")
        if decision.warnings:
            logger.warning(f"Warnings: {', '.join(decision.warnings)}")
    
    def __repr__(self):
        return f"<{self.__class__.__name__} {self.name} v{self.version}>"