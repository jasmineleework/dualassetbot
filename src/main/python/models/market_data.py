"""
Market data model for storing historical price and indicator data
"""
from sqlalchemy import Column, String, Float, Integer, DateTime, JSON, Index
from models.base import BaseModel

class MarketData(BaseModel):
    """Market data model for historical prices and indicators"""
    __tablename__ = "market_data"
    
    # Symbol and timing
    symbol = Column(String(20), nullable=False, index=True)
    interval = Column(String(10), nullable=False)  # 1m, 5m, 1h, 1d, etc
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # OHLCV data
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    
    # Technical indicators
    sma_20 = Column(Float)
    sma_50 = Column(Float)
    sma_200 = Column(Float)
    ema_12 = Column(Float)
    ema_26 = Column(Float)
    
    # Momentum indicators
    rsi = Column(Float)
    macd = Column(Float)
    macd_signal = Column(Float)
    macd_histogram = Column(Float)
    
    # Volatility indicators
    atr = Column(Float)  # Average True Range
    bollinger_upper = Column(Float)
    bollinger_middle = Column(Float)
    bollinger_lower = Column(Float)
    volatility_24h = Column(Float)
    volatility_7d = Column(Float)
    
    # Volume indicators
    obv = Column(Float)  # On Balance Volume
    mfi = Column(Float)  # Money Flow Index
    
    # Market stats
    price_change_24h = Column(Float)
    price_change_pct_24h = Column(Float)
    high_24h = Column(Float)
    low_24h = Column(Float)
    volume_24h = Column(Float)
    
    # Additional data
    trades_count = Column(Integer)
    taker_buy_volume = Column(Float)
    additional_data = Column(JSON)
    
    # Create composite index for efficient querying
    __table_args__ = (
        Index('idx_symbol_interval_timestamp', 'symbol', 'interval', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<MarketData {self.symbol} {self.interval} {self.timestamp}>"