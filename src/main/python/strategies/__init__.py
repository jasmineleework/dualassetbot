"""
Trading Strategies Module
"""
from strategies.base_strategy import BaseStrategy, StrategySignal, SignalStrength, InvestmentDecision
from strategies.dual_investment_strategy import DualInvestmentStrategy
from strategies.strategy_manager import StrategyManager

__all__ = [
    'BaseStrategy',
    'StrategySignal',
    'SignalStrength',
    'InvestmentDecision',
    'DualInvestmentStrategy',
    'StrategyManager'
]