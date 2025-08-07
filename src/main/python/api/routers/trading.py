"""
Trading execution API endpoints
"""
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from datetime import datetime
from celery.result import AsyncResult
from tasks.trading_tasks import execute_investment, execute_pending_investments, cancel_investment, batch_execute_investments
from dao.investment import InvestmentDAO
from models.investment import InvestmentStatus, InvestmentType
from core.database import get_db
from core.config import settings
from loguru import logger
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/v1/trading", tags=["trading"])

class InvestmentRequest(BaseModel):
    product_id: str
    amount: float
    user_id: str = "default"

class BatchInvestmentRequest(BaseModel):
    investments: List[InvestmentRequest]

class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: str

@router.post("/execute", response_model=TaskResponse)
async def execute_single_investment(request: InvestmentRequest):
    """
    Execute a single dual investment
    """
    try:
        if not settings.enable_automated_trading:
            raise HTTPException(
                status_code=403, 
                detail="Automated trading is disabled. Enable it in configuration to proceed."
            )
        
        # Validate amount
        if request.amount <= 0:
            raise HTTPException(status_code=400, detail="Amount must be positive")
        
        if request.amount > settings.default_investment_amount * 10:  # Safety limit
            raise HTTPException(status_code=400, detail="Amount exceeds safety limit")
        
        # Queue the investment execution
        task = execute_investment.delay(
            product_id=request.product_id,
            amount=request.amount,
            user_id=request.user_id
        )
        
        logger.info(f"Queued investment execution: {request.product_id} for ${request.amount}")
        
        return TaskResponse(
            task_id=task.id,
            status="queued",
            message=f"Investment execution queued for {request.product_id}"
        )
        
    except Exception as e:
        logger.error(f"Failed to queue investment execution: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/execute-batch", response_model=TaskResponse)
async def execute_batch_investments(request: BatchInvestmentRequest):
    """
    Execute multiple investments in batch
    """
    try:
        if not settings.enable_automated_trading:
            raise HTTPException(
                status_code=403, 
                detail="Automated trading is disabled. Enable it in configuration to proceed."
            )
        
        if len(request.investments) > settings.max_concurrent_trades:
            raise HTTPException(
                status_code=400, 
                detail=f"Batch size exceeds limit of {settings.max_concurrent_trades}"
            )
        
        # Convert to dict format for Celery
        investment_requests = [
            {
                'product_id': inv.product_id,
                'amount': inv.amount,
                'user_id': inv.user_id
            }
            for inv in request.investments
        ]
        
        # Queue batch execution
        task = batch_execute_investments.delay(investment_requests)
        
        logger.info(f"Queued batch investment execution: {len(request.investments)} investments")
        
        return TaskResponse(
            task_id=task.id,
            status="queued",
            message=f"Batch execution queued for {len(request.investments)} investments"
        )
        
    except Exception as e:
        logger.error(f"Failed to queue batch investment execution: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/auto-execute", response_model=TaskResponse)
async def trigger_auto_execution():
    """
    Trigger automatic execution of AI-recommended investments
    """
    try:
        if not settings.enable_automated_trading:
            raise HTTPException(
                status_code=403, 
                detail="Automated trading is disabled. Enable it in configuration to proceed."
            )
        
        # Queue automatic execution
        task = execute_pending_investments.delay()
        
        logger.info("Triggered automatic investment execution")
        
        return TaskResponse(
            task_id=task.id,
            status="queued",
            message="Automatic investment execution triggered"
        )
        
    except Exception as e:
        logger.error(f"Failed to trigger automatic execution: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cancel/{investment_id}", response_model=TaskResponse)
async def cancel_active_investment(investment_id: str, reason: str = Body("User requested")):
    """
    Cancel an active investment
    """
    try:
        # Queue cancellation
        task = cancel_investment.delay(investment_id, reason)
        
        logger.info(f"Queued investment cancellation: {investment_id}")
        
        return TaskResponse(
            task_id=task.id,
            status="queued",
            message=f"Investment cancellation queued for {investment_id}"
        )
        
    except Exception as e:
        logger.error(f"Failed to queue investment cancellation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/task-status/{task_id}")
async def get_task_status(task_id: str):
    """
    Get the status of a trading task
    """
    try:
        result = AsyncResult(task_id)
        
        response = {
            "task_id": task_id,
            "status": result.status,
            "ready": result.ready(),
            "successful": result.successful() if result.ready() else None,
        }
        
        if result.ready():
            if result.successful():
                response["result"] = result.result
            else:
                response["error"] = str(result.info)
        else:
            response["info"] = result.info
        
        return response
        
    except Exception as e:
        logger.error(f"Failed to get task status for {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/investments")
async def get_investments(
    status: Optional[InvestmentStatus] = Query(None, description="Filter by status"),
    limit: int = Query(20, ge=1, le=100, description="Number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    db: Session = Depends(get_db)
):
    """
    Get investment records
    """
    try:
        investment_dao = InvestmentDAO(db)
        
        if status:
            investments = investment_dao.get_by_status(status, limit, offset)
        else:
            investments = investment_dao.get_all(limit, offset)
        
        return {
            "investments": [
                {
                    "id": inv.id,
                    "product_id": inv.product_id,
                    "amount": inv.amount,
                    "status": inv.status,
                    "created_at": inv.created_at,
                    "executed_at": inv.executed_at,
                    "completed_at": inv.completed_at,
                    "actual_return": inv.actual_return,
                    "binance_order_id": inv.binance_order_id,
                    "error_message": inv.error_message
                }
                for inv in investments
            ],
            "total": len(investments),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Failed to get investments: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/investments/{investment_id}")
async def get_investment_detail(investment_id: str, db: Session = Depends(get_db)):
    """
    Get detailed information about a specific investment
    """
    try:
        investment_dao = InvestmentDAO(db)
        investment = investment_dao.get(investment_id)
        
        if not investment:
            raise HTTPException(status_code=404, detail="Investment not found")
        
        return {
            "id": investment.id,
            "user_id": investment.user_id,
            "product_id": investment.product_id,
            "investment_type": investment.investment_type,
            "amount": investment.amount,
            "status": investment.status,
            "created_at": investment.created_at,
            "executed_at": investment.executed_at,
            "completed_at": investment.completed_at,
            "cancelled_at": investment.cancelled_at,
            "execution_price": investment.execution_price,
            "current_value": investment.current_value,
            "actual_return": investment.actual_return,
            "expected_return": investment.expected_return,
            "binance_order_id": investment.binance_order_id,
            "error_message": investment.error_message,
            "metadata": investment.metadata
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get investment {investment_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/portfolio/summary")
async def get_portfolio_summary(db: Session = Depends(get_db)):
    """
    Get portfolio summary with key statistics
    """
    try:
        investment_dao = InvestmentDAO(db)
        
        # Get all investments
        all_investments = investment_dao.get_all(1000)  # Get more for accurate stats
        
        # Calculate statistics
        total_invested = sum(inv.amount for inv in all_investments)
        total_returns = sum(inv.actual_return or 0 for inv in all_investments)
        
        active_investments = [inv for inv in all_investments if inv.status == InvestmentStatus.ACTIVE]
        completed_investments = [inv for inv in all_investments if inv.status == InvestmentStatus.COMPLETED]
        failed_investments = [inv for inv in all_investments if inv.status == InvestmentStatus.FAILED]
        
        current_value = sum(inv.current_value or inv.amount for inv in active_investments) + \
                       sum(inv.amount + (inv.actual_return or 0) for inv in completed_investments)
        
        return {
            "summary": {
                "total_investments": len(all_investments),
                "total_invested": total_invested,
                "current_value": current_value,
                "total_returns": total_returns,
                "net_pnl": total_returns,
                "roi_percentage": (total_returns / total_invested * 100) if total_invested > 0 else 0
            },
            "status_breakdown": {
                "active": len(active_investments),
                "completed": len(completed_investments),
                "failed": len(failed_investments),
                "pending": len([inv for inv in all_investments if inv.status == InvestmentStatus.PENDING]),
                "cancelled": len([inv for inv in all_investments if inv.status == InvestmentStatus.CANCELLED])
            },
            "active_investments": [
                {
                    "id": inv.id,
                    "product_id": inv.product_id,
                    "amount": inv.amount,
                    "executed_at": inv.executed_at,
                    "current_value": inv.current_value or inv.amount
                }
                for inv in active_investments[:10]  # Top 10 active
            ],
            "recent_completed": [
                {
                    "id": inv.id,
                    "product_id": inv.product_id,
                    "amount": inv.amount,
                    "actual_return": inv.actual_return,
                    "completed_at": inv.completed_at,
                    "roi_pct": (inv.actual_return / inv.amount * 100) if inv.amount > 0 else 0
                }
                for inv in sorted(completed_investments, key=lambda x: x.completed_at or datetime.min, reverse=True)[:5]
            ]
        }
        
    except Exception as e:
        logger.error(f"Failed to get portfolio summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/settings")
async def get_trading_settings():
    """
    Get current trading configuration settings
    """
    return {
        "automated_trading_enabled": settings.enable_automated_trading,
        "max_concurrent_trades": settings.max_concurrent_trades,
        "trading_cooldown_minutes": settings.trading_cooldown_minutes,
        "default_investment_amount": settings.default_investment_amount,
        "max_single_investment_ratio": settings.max_single_investment_ratio,
        "min_apr_threshold": settings.min_apr_threshold,
        "risk_level": settings.risk_level
    }

@router.post("/settings")
async def update_trading_settings(settings_update: Dict[str, Any] = Body(...)):
    """
    Update trading configuration settings (runtime only)
    """
    try:
        updated_settings = {}
        
        # Update allowed settings
        allowed_settings = [
            'enable_automated_trading',
            'max_concurrent_trades', 
            'trading_cooldown_minutes',
            'default_investment_amount',
            'max_single_investment_ratio',
            'min_apr_threshold',
            'risk_level'
        ]
        
        for key, value in settings_update.items():
            if key in allowed_settings and hasattr(settings, key):
                setattr(settings, key, value)
                updated_settings[key] = value
                logger.info(f"Updated setting {key} to {value}")
        
        return {
            "status": "success",
            "message": f"Updated {len(updated_settings)} settings",
            "updated_settings": updated_settings
        }
        
    except Exception as e:
        logger.error(f"Failed to update trading settings: {e}")
        raise HTTPException(status_code=500, detail=str(e))