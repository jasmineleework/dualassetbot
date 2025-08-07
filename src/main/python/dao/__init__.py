"""
Data Access Objects
"""
from dao.base import BaseDAO
from dao.investment import InvestmentDAO
from dao.market_data import MarketDataDAO
from dao.user import UserDAO
from dao.strategy_log import StrategyLogDAO

# Note: DAO instances should be created with database session
# These will be initialized in the API endpoints with proper session
investment_dao = None
market_data_dao = None
user_dao = None
strategy_log_dao = None

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