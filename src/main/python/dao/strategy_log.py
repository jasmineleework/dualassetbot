"""
Strategy Log DAO for tracking strategy execution
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from dao.base import BaseDAO
from models.strategy_log import StrategyLog, DecisionType, LogLevel
from loguru import logger

class StrategyLogDAO(BaseDAO[StrategyLog]):
    """Data Access Object for StrategyLog model"""
    
    def __init__(self):
        super().__init__(StrategyLog)
    
    def log_decision(
        self,
        db: Session,
        user_id: str,
        strategy_name: str,
        decision_type: DecisionType,
        symbol: str,
        ai_score: float,
        decision_made: bool,
        reasons: List[str],
        **kwargs
    ) -> StrategyLog:
        """Log a strategy decision"""
        return self.create(
            db,
            user_id=user_id,
            strategy_name=strategy_name,
            execution_time=datetime.utcnow(),
            decision_type=decision_type,
            symbol=symbol,
            ai_score=ai_score,
            decision_made=decision_made,
            reasons=reasons,
            **kwargs
        )
    
    def get_recent_decisions(
        self,
        db: Session,
        user_id: str,
        hours: int = 24,
        strategy_name: Optional[str] = None
    ) -> List[StrategyLog]:
        """Get recent strategy decisions"""
        since = datetime.utcnow() - timedelta(hours=hours)
        
        query = db.query(StrategyLog).filter(
            and_(
                StrategyLog.user_id == user_id,
                StrategyLog.execution_time >= since
            )
        )
        
        if strategy_name:
            query = query.filter(StrategyLog.strategy_name == strategy_name)
        
        return query.order_by(StrategyLog.execution_time.desc()).all()
    
    def get_strategy_performance(
        self,
        db: Session,
        strategy_name: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get performance metrics for a strategy"""
        since = datetime.utcnow() - timedelta(days=days)
        
        logs = db.query(StrategyLog).filter(
            and_(
                StrategyLog.strategy_name == strategy_name,
                StrategyLog.execution_time >= since
            )
        ).all()
        
        if not logs:
            return {
                'total_decisions': 0,
                'invest_decisions': 0,
                'skip_decisions': 0,
                'success_rate': 0,
                'average_ai_score': 0
            }
        
        invest_logs = [l for l in logs if l.decision_type == DecisionType.INVEST]
        skip_logs = [l for l in logs if l.decision_type == DecisionType.SKIP]
        
        # Calculate success rate based on actual returns
        successful = [l for l in invest_logs if l.actual_return and l.actual_return > 0]
        
        return {
            'total_decisions': len(logs),
            'invest_decisions': len(invest_logs),
            'skip_decisions': len(skip_logs),
            'success_rate': len(successful) / len(invest_logs) if invest_logs else 0,
            'average_ai_score': sum(l.ai_score or 0 for l in logs) / len(logs),
            'average_expected_return': sum(l.expected_return or 0 for l in invest_logs) / len(invest_logs) if invest_logs else 0,
            'average_actual_return': sum(l.actual_return or 0 for l in successful) / len(successful) if successful else 0
        }
    
    def get_decision_distribution(
        self,
        db: Session,
        user_id: str,
        days: int = 30
    ) -> Dict[str, int]:
        """Get distribution of decision types"""
        since = datetime.utcnow() - timedelta(days=days)
        
        results = db.query(
            StrategyLog.decision_type,
            func.count(StrategyLog.id).label('count')
        ).filter(
            and_(
                StrategyLog.user_id == user_id,
                StrategyLog.execution_time >= since
            )
        ).group_by(StrategyLog.decision_type).all()
        
        return {
            result.decision_type.value: result.count
            for result in results
        }
    
    def get_error_logs(
        self,
        db: Session,
        hours: int = 24,
        user_id: Optional[str] = None
    ) -> List[StrategyLog]:
        """Get error logs from strategy execution"""
        since = datetime.utcnow() - timedelta(hours=hours)
        
        query = db.query(StrategyLog).filter(
            and_(
                StrategyLog.execution_time >= since,
                StrategyLog.log_level.in_([LogLevel.ERROR, LogLevel.CRITICAL])
            )
        )
        
        if user_id:
            query = query.filter(StrategyLog.user_id == user_id)
        
        return query.order_by(StrategyLog.execution_time.desc()).all()
    
    def cleanup_old_logs(
        self,
        db: Session,
        days_to_keep: int = 90
    ) -> int:
        """Delete old strategy logs"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            deleted = db.query(StrategyLog).filter(
                StrategyLog.execution_time < cutoff_date
            ).delete()
            
            db.commit()
            logger.info(f"Deleted {deleted} old strategy logs")
            return deleted
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to cleanup old logs: {e}")
            raise