"""
Strategy log model for tracking AI decisions and strategy execution
"""
from sqlalchemy import Column, String, Float, Boolean, DateTime, ForeignKey, JSON, Text, Enum, Integer
from sqlalchemy.orm import relationship
from models.base import BaseModel
import enum

class DecisionType(enum.Enum):
    """Decision type enum"""
    INVEST = "invest"
    SKIP = "skip"
    EXIT = "exit"
    REBALANCE = "rebalance"

class LogLevel(enum.Enum):
    """Log level enum"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class StrategyLog(BaseModel):
    """Strategy execution and decision log"""
    __tablename__ = "strategy_logs"
    
    # User reference
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    user = relationship("User", back_populates="strategy_logs")
    
    # Strategy info
    strategy_name = Column(String(100), nullable=False, index=True)
    strategy_version = Column(String(20))
    execution_time = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Decision details
    decision_type = Column(Enum(DecisionType), nullable=False, index=True)
    symbol = Column(String(20), index=True)
    product_id = Column(String(100))
    
    # Decision factors
    ai_score = Column(Float)  # Overall AI confidence score
    market_score = Column(Float)
    technical_score = Column(Float)
    sentiment_score = Column(Float)
    risk_score = Column(Float)
    
    # Decision outcome
    decision_made = Column(Boolean, nullable=False)
    action_taken = Column(String(100))
    amount = Column(Float)
    
    # Market context
    market_price = Column(Float)
    market_trend = Column(String(20))  # BULLISH, BEARISH, NEUTRAL
    volatility = Column(Float)
    volume_24h = Column(Float)
    
    # Analysis results
    technical_indicators = Column(JSON)  # RSI, MACD, etc.
    support_resistance = Column(JSON)
    predicted_price = Column(Float)
    predicted_probability = Column(Float)
    
    # Reasoning
    reasons = Column(JSON)  # List of reasons
    detailed_analysis = Column(Text)
    warnings = Column(JSON)  # List of warnings
    
    # Performance tracking
    expected_return = Column(Float)
    expected_risk = Column(Float)
    actual_return = Column(Float)  # Updated after settlement
    
    # Execution details
    execution_successful = Column(Boolean)
    error_message = Column(Text)
    execution_duration_ms = Column(Integer)
    
    # Log level for filtering
    log_level = Column(Enum(LogLevel), default=LogLevel.INFO)
    
    # Related investment (if decision resulted in investment)
    investment_id = Column(String(36), ForeignKey("investments.id"))
    
    # Additional metadata
    additional_metadata = Column(JSON)
    
    def __repr__(self):
        return f"<StrategyLog {self.strategy_name} {self.decision_type.value} {self.execution_time}>"