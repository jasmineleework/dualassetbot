"""
Investment model for tracking dual investment positions
"""
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from models.base import BaseModel
import enum

class InvestmentStatus(enum.Enum):
    """Investment status enum"""
    PENDING = "pending"
    ACTIVE = "active"
    EXERCISED = "exercised"
    NOT_EXERCISED = "not_exercised"
    CANCELLED = "cancelled"
    FAILED = "failed"

class InvestmentType(enum.Enum):
    """Investment type enum"""
    BUY_LOW = "BUY_LOW"
    SELL_HIGH = "SELL_HIGH"

class Investment(BaseModel):
    """Investment model for tracking dual investment positions"""
    __tablename__ = "investments"
    
    # User reference
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    user = relationship("User", back_populates="investments")
    
    # Product details
    product_id = Column(String(100), nullable=False, index=True)
    asset = Column(String(20), nullable=False, index=True)  # BTC, ETH, etc
    currency = Column(String(20), nullable=False)  # USDT
    investment_type = Column(Enum(InvestmentType), nullable=False, index=True)
    
    # Investment parameters
    amount = Column(Float, nullable=False)  # Investment amount
    strike_price = Column(Float, nullable=False)
    apy = Column(Float, nullable=False)
    term_days = Column(Integer, nullable=False)
    
    # Market data at time of investment
    entry_price = Column(Float, nullable=False)  # Market price when invested
    entry_volatility = Column(Float)  # Volatility at entry
    
    # Dates
    investment_date = Column(DateTime(timezone=True), nullable=False)
    settlement_date = Column(DateTime(timezone=True), nullable=False)
    actual_settlement_date = Column(DateTime(timezone=True))
    
    # Results
    status = Column(Enum(InvestmentStatus), default=InvestmentStatus.PENDING, nullable=False, index=True)
    settlement_price = Column(Float)  # Price at settlement
    is_exercised = Column(Boolean)
    
    # Returns
    principal_returned = Column(Float)
    interest_earned = Column(Float)
    asset_received = Column(Float)  # For exercised options
    total_return_usdt = Column(Float)  # Total return in USDT
    actual_apy = Column(Float)  # Actual APY achieved
    
    # AI Decision metadata
    ai_score = Column(Float)  # AI confidence score
    ai_reasons = Column(JSON)  # List of reasons for investment
    exercise_probability = Column(Float)  # Predicted exercise probability
    
    # Risk metrics
    risk_score = Column(Float)
    max_loss_amount = Column(Float)
    expected_return = Column(Float)
    
    # Transaction details
    binance_order_id = Column(String(100))
    transaction_hash = Column(String(100))
    fees = Column(Float, default=0)
    
    # Strategy reference
    strategy_name = Column(String(100))
    strategy_version = Column(String(20))
    
    def __repr__(self):
        return f"<Investment {self.product_id} - {self.status.value}>"