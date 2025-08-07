"""
User model for authentication and settings
"""
from sqlalchemy import Column, String, Boolean, Float, JSON, Integer
from sqlalchemy.orm import relationship
from models.base import BaseModel

class User(BaseModel):
    """User model"""
    __tablename__ = "users"
    
    # Basic info
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    
    # API Keys (encrypted)
    binance_api_key_encrypted = Column(String(500))
    binance_api_secret_encrypted = Column(String(500))
    use_testnet = Column(Boolean, default=True, nullable=False)
    
    # Trading settings
    max_investment_per_trade = Column(Float, default=1000.0)
    max_total_investment = Column(Float, default=10000.0)
    risk_level = Column(Integer, default=5)  # 1-10
    auto_trade_enabled = Column(Boolean, default=False)
    
    # Notification settings
    telegram_chat_id = Column(String(100))
    email_notifications = Column(Boolean, default=True)
    
    # User preferences
    preferences = Column(JSON, default={})
    
    # Relationships
    investments = relationship("Investment", back_populates="user", lazy="dynamic")
    strategy_logs = relationship("StrategyLog", back_populates="user", lazy="dynamic")
    
    def __repr__(self):
        return f"<User {self.username}>"