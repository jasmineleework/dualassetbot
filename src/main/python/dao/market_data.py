"""
Market Data DAO for historical data operations
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc
import pandas as pd
from dao.base import BaseDAO
from models.market_data import MarketData
from loguru import logger

class MarketDataDAO(BaseDAO[MarketData]):
    """Data Access Object for MarketData model"""
    
    def __init__(self):
        super().__init__(MarketData)
    
    def get_latest(
        self,
        db: Session,
        symbol: str,
        interval: str = "1h"
    ) -> Optional[MarketData]:
        """Get the latest market data for a symbol"""
        return db.query(MarketData).filter(
            and_(
                MarketData.symbol == symbol,
                MarketData.interval == interval
            )
        ).order_by(desc(MarketData.timestamp)).first()
    
    def get_historical_data(
        self,
        db: Session,
        symbol: str,
        interval: str = "1h",
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[MarketData]:
        """Get historical market data"""
        query = db.query(MarketData).filter(
            and_(
                MarketData.symbol == symbol,
                MarketData.interval == interval
            )
        )
        
        if start_time:
            query = query.filter(MarketData.timestamp >= start_time)
        if end_time:
            query = query.filter(MarketData.timestamp <= end_time)
        
        return query.order_by(MarketData.timestamp.desc()).limit(limit).all()
    
    def get_as_dataframe(
        self,
        db: Session,
        symbol: str,
        interval: str = "1h",
        days: int = 7
    ) -> pd.DataFrame:
        """Get market data as pandas DataFrame"""
        start_time = datetime.utcnow() - timedelta(days=days)
        
        data = self.get_historical_data(
            db, symbol, interval, start_time=start_time
        )
        
        if not data:
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame([d.to_dict() for d in data])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df.set_index('timestamp', inplace=True)
        df.sort_index(inplace=True)
        
        return df
    
    def bulk_insert(
        self,
        db: Session,
        data_list: List[Dict[str, Any]]
    ) -> int:
        """Bulk insert market data"""
        try:
            # Check for duplicates
            for data in data_list:
                existing = db.query(MarketData).filter(
                    and_(
                        MarketData.symbol == data['symbol'],
                        MarketData.interval == data['interval'],
                        MarketData.timestamp == data['timestamp']
                    )
                ).first()
                
                if not existing:
                    db.add(MarketData(**data))
            
            db.commit()
            return len(data_list)
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to bulk insert market data: {e}")
            raise
    
    def get_price_range(
        self,
        db: Session,
        symbol: str,
        days: int = 7
    ) -> Dict[str, float]:
        """Get price range statistics for a symbol"""
        start_time = datetime.utcnow() - timedelta(days=days)
        
        result = db.query(
            func.min(MarketData.low).label('min'),
            func.max(MarketData.high).label('max'),
            func.avg(MarketData.close).label('avg')
        ).filter(
            and_(
                MarketData.symbol == symbol,
                MarketData.timestamp >= start_time
            )
        ).first()
        
        if result:
            return {
                'min': result.min or 0,
                'max': result.max or 0,
                'avg': result.avg or 0,
                'range': (result.max or 0) - (result.min or 0)
            }
        
        return {'min': 0, 'max': 0, 'avg': 0, 'range': 0}
    
    def get_volatility_stats(
        self,
        db: Session,
        symbol: str,
        interval: str = "1h",
        days: int = 7
    ) -> Dict[str, float]:
        """Calculate volatility statistics"""
        df = self.get_as_dataframe(db, symbol, interval, days)
        
        if df.empty:
            return {'daily_volatility': 0, 'weekly_volatility': 0, 'atr': 0}
        
        # Calculate returns
        df['returns'] = df['close'].pct_change()
        
        # Calculate volatility
        daily_vol = df['returns'].std() * (24 ** 0.5)  # Assuming hourly data
        weekly_vol = daily_vol * (7 ** 0.5)
        
        # Calculate ATR if available
        atr = df['atr'].mean() if 'atr' in df.columns else 0
        
        return {
            'daily_volatility': daily_vol,
            'weekly_volatility': weekly_vol,
            'atr': atr,
            'return_mean': df['returns'].mean(),
            'return_std': df['returns'].std()
        }
    
    def cleanup_old_data(
        self,
        db: Session,
        days_to_keep: int = 90
    ) -> int:
        """Delete market data older than specified days"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            deleted = db.query(MarketData).filter(
                MarketData.timestamp < cutoff_date
            ).delete()
            
            db.commit()
            logger.info(f"Deleted {deleted} old market data records")
            return deleted
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to cleanup old data: {e}")
            raise