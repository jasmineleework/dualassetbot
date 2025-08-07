"""
Investment DAO with specific investment operations
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from dao.base import BaseDAO
from models.investment import Investment, InvestmentStatus, InvestmentType
from loguru import logger

class InvestmentDAO(BaseDAO[Investment]):
    """Data Access Object for Investment model"""
    
    def __init__(self):
        super().__init__(Investment)
    
    def get_active_investments(
        self, 
        db: Session, 
        user_id: str,
        asset: Optional[str] = None
    ) -> List[Investment]:
        """Get all active investments for a user"""
        query = db.query(Investment).filter(
            and_(
                Investment.user_id == user_id,
                Investment.status == InvestmentStatus.ACTIVE
            )
        )
        
        if asset:
            query = query.filter(Investment.asset == asset)
        
        return query.all()
    
    def get_investments_pending_settlement(
        self, 
        db: Session
    ) -> List[Investment]:
        """Get investments that are due for settlement"""
        now = datetime.utcnow()
        return db.query(Investment).filter(
            and_(
                Investment.status == InvestmentStatus.ACTIVE,
                Investment.settlement_date <= now
            )
        ).all()
    
    def get_user_portfolio_summary(
        self, 
        db: Session, 
        user_id: str
    ) -> Dict[str, Any]:
        """Get portfolio summary for a user"""
        investments = db.query(Investment).filter(
            Investment.user_id == user_id
        ).all()
        
        active = [i for i in investments if i.status == InvestmentStatus.ACTIVE]
        total_invested = sum(i.amount for i in active)
        
        # Calculate returns
        completed = [i for i in investments if i.status in [
            InvestmentStatus.EXERCISED, 
            InvestmentStatus.NOT_EXERCISED
        ]]
        total_returns = sum(i.total_return_usdt or 0 for i in completed)
        
        # Group by asset
        by_asset = {}
        for inv in active:
            if inv.asset not in by_asset:
                by_asset[inv.asset] = {'count': 0, 'amount': 0}
            by_asset[inv.asset]['count'] += 1
            by_asset[inv.asset]['amount'] += inv.amount
        
        return {
            'total_active_investments': len(active),
            'total_invested_amount': total_invested,
            'total_completed': len(completed),
            'total_returns': total_returns,
            'by_asset': by_asset,
            'average_apy': sum(i.apy for i in active) / len(active) if active else 0
        }
    
    def get_investment_history(
        self,
        db: Session,
        user_id: str,
        days: int = 30,
        status: Optional[InvestmentStatus] = None
    ) -> List[Investment]:
        """Get investment history for a user"""
        since = datetime.utcnow() - timedelta(days=days)
        query = db.query(Investment).filter(
            and_(
                Investment.user_id == user_id,
                Investment.created_at >= since
            )
        )
        
        if status:
            query = query.filter(Investment.status == status)
        
        return query.order_by(Investment.created_at.desc()).all()
    
    def calculate_performance_metrics(
        self,
        db: Session,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Calculate performance metrics for a user"""
        since = datetime.utcnow() - timedelta(days=days)
        
        investments = db.query(Investment).filter(
            and_(
                Investment.user_id == user_id,
                Investment.created_at >= since
            )
        ).all()
        
        if not investments:
            return {
                'total_investments': 0,
                'success_rate': 0,
                'average_return': 0,
                'total_profit': 0
            }
        
        completed = [i for i in investments if i.status in [
            InvestmentStatus.EXERCISED,
            InvestmentStatus.NOT_EXERCISED
        ]]
        
        successful = [i for i in completed if (i.total_return_usdt or 0) > i.amount]
        
        total_profit = sum((i.total_return_usdt or 0) - i.amount for i in completed)
        
        return {
            'total_investments': len(investments),
            'completed_investments': len(completed),
            'success_rate': len(successful) / len(completed) if completed else 0,
            'average_return': total_profit / len(completed) if completed else 0,
            'total_profit': total_profit,
            'best_investment': max(completed, key=lambda x: (x.total_return_usdt or 0) - x.amount).id if completed else None,
            'worst_investment': min(completed, key=lambda x: (x.total_return_usdt or 0) - x.amount).id if completed else None
        }
    
    def get_total_exposure(
        self,
        db: Session,
        user_id: str,
        asset: Optional[str] = None
    ) -> float:
        """Get total exposure (amount at risk) for a user"""
        query = db.query(func.sum(Investment.amount)).filter(
            and_(
                Investment.user_id == user_id,
                Investment.status == InvestmentStatus.ACTIVE
            )
        )
        
        if asset:
            query = query.filter(Investment.asset == asset)
        
        result = query.scalar()
        return result or 0.0