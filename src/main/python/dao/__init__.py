"""
Data Access Objects
"""
from dao.base import BaseDAO
from dao.investment import InvestmentDAO
from dao.market_data import MarketDataDAO
from dao.user import UserDAO
from dao.strategy_log import StrategyLogDAO

# Create singleton instances
investment_dao = InvestmentDAO()
market_data_dao = MarketDataDAO()
user_dao = UserDAO()
strategy_log_dao = StrategyLogDAO()

__all__ = [
    'BaseDAO',
    'InvestmentDAO',
    'MarketDataDAO',
    'UserDAO',
    'StrategyLogDAO',
    'investment_dao',
    'market_data_dao',
    'user_dao',
    'strategy_log_dao'
]