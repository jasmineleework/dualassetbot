"""
Trading-related Celery tasks
"""
from celery import current_task
from celery_app import celery_app
from core.dual_investment_engine import dual_investment_engine
from services.binance_service import binance_service
from dao.investment import InvestmentDAO
from dao.strategy_log import StrategyLogDAO
from models.investment import Investment, InvestmentStatus, InvestmentType
from core.database import get_db
from loguru import logger
from typing import List, Dict, Any
import time
from datetime import datetime, timedelta

@celery_app.task(bind=True, max_retries=3)
def execute_investment(self, product_id: str, amount: float, user_id: str = "default"):
    """
    Execute a single dual investment subscription
    """
    task_id = self.request.id
    logger.info(f"Task {task_id}: Executing investment for product {product_id}, amount ${amount}")
    
    try:
        # Create database session
        db = next(get_db())
        investment_dao = InvestmentDAO(db)
        strategy_log_dao = StrategyLogDAO(db)
        
        # Create investment record
        investment = Investment(
            user_id=user_id,
            product_id=product_id,
            investment_type=InvestmentType.DUAL_INVESTMENT,
            amount=amount,
            status=InvestmentStatus.PENDING,
            metadata={"task_id": task_id, "execution_time": datetime.utcnow().isoformat()}
        )
        
        investment = investment_dao.create(investment)
        logger.info(f"Created investment record: {investment.id}")
        
        # Update task state
        current_task.update_state(
            state='PROGRESS',
            meta={'investment_id': investment.id, 'status': 'executing', 'progress': 25}
        )
        
        # Execute the investment via Binance API
        try:
            result = binance_service.subscribe_dual_investment(product_id, amount)
            
            if result.get('success', False):
                # Update investment status
                investment.status = InvestmentStatus.ACTIVE
                investment.binance_order_id = result.get('order_id')
                investment.executed_at = datetime.utcnow()
                investment.execution_price = result.get('execution_price')
                investment.metadata.update({
                    'binance_response': result,
                    'execution_successful': True
                })
                
                investment_dao.update(investment.id, investment)
                
                # Log successful execution
                strategy_log_dao.log_execution(
                    user_id=user_id,
                    strategy_name="AutoTrading",
                    symbol=product_id.split('-')[0],
                    product_id=product_id,
                    decision_made=True,
                    action_taken="INVEST",
                    amount=amount,
                    execution_successful=True,
                    investment_id=investment.id
                )
                
                logger.success(f"Investment {investment.id} executed successfully")
                
                current_task.update_state(
                    state='SUCCESS',
                    meta={
                        'investment_id': investment.id,
                        'status': 'completed',
                        'progress': 100,
                        'binance_order_id': result.get('order_id')
                    }
                )
                
                return {
                    'status': 'success',
                    'investment_id': investment.id,
                    'binance_order_id': result.get('order_id'),
                    'amount': amount,
                    'product_id': product_id
                }
                
            else:
                raise Exception(f"Binance API error: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Failed to execute investment: {e}")
            
            # Update investment status to failed
            investment.status = InvestmentStatus.FAILED
            investment.error_message = str(e)
            investment.metadata.update({'execution_successful': False, 'error': str(e)})
            investment_dao.update(investment.id, investment)
            
            # Log failed execution
            strategy_log_dao.log_execution(
                user_id=user_id,
                strategy_name="AutoTrading",
                symbol=product_id.split('-')[0],
                product_id=product_id,
                decision_made=True,
                action_taken="INVEST",
                amount=amount,
                execution_successful=False,
                error_message=str(e),
                investment_id=investment.id
            )
            
            raise e
            
    except Exception as e:
        logger.error(f"Task {task_id} failed: {e}")
        
        current_task.update_state(
            state='FAILURE',
            meta={'error': str(e), 'investment_id': getattr(investment, 'id', None)}
        )
        
        # Retry logic
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying task {task_id} in 60 seconds (attempt {self.request.retries + 1}/{self.max_retries})")
            raise self.retry(countdown=60, exc=e)
        
        raise e
    finally:
        db.close()

@celery_app.task(bind=True)
def execute_pending_investments(self):
    """
    Execute all pending investments that meet criteria
    """
    task_id = self.request.id
    logger.info(f"Task {task_id}: Checking for pending investments to execute")
    
    try:
        # Get symbols to analyze
        symbols = ['BTCUSDT', 'ETHUSDT']  # Can be configured
        executed_count = 0
        
        for symbol in symbols:
            try:
                # Get AI recommendations
                recommendations = dual_investment_engine.get_ai_recommendations(symbol, limit=3)
                
                for rec in recommendations:
                    if rec['should_invest'] and rec['ai_score'] >= 0.7:  # High confidence only
                        # Execute investment asynchronously
                        execute_investment.delay(
                            product_id=rec['product_id'],
                            amount=rec['amount']
                        )
                        executed_count += 1
                        logger.info(f"Queued investment: {rec['product_id']} for ${rec['amount']}")
                        
                        # Rate limiting - don't overwhelm the system
                        time.sleep(2)
                        
            except Exception as e:
                logger.error(f"Failed to process recommendations for {symbol}: {e}")
                continue
        
        logger.info(f"Queued {executed_count} investments for execution")
        
        return {
            'status': 'success',
            'investments_queued': executed_count,
            'symbols_processed': symbols
        }
        
    except Exception as e:
        logger.error(f"Failed to execute pending investments: {e}")
        raise e

@celery_app.task(bind=True)
def cancel_investment(self, investment_id: str, reason: str = "User requested"):
    """
    Cancel an active investment
    """
    task_id = self.request.id
    logger.info(f"Task {task_id}: Cancelling investment {investment_id}")
    
    try:
        db = next(get_db())
        investment_dao = InvestmentDAO(db)
        
        # Get investment record
        investment = investment_dao.get(investment_id)
        if not investment:
            raise Exception(f"Investment {investment_id} not found")
        
        if investment.status != InvestmentStatus.ACTIVE:
            raise Exception(f"Cannot cancel investment with status {investment.status}")
        
        # Try to cancel via Binance API if possible
        if investment.binance_order_id:
            try:
                result = binance_service.cancel_dual_investment(investment.binance_order_id)
                logger.info(f"Binance cancellation result: {result}")
            except Exception as e:
                logger.warning(f"Failed to cancel via Binance API: {e}")
        
        # Update investment status
        investment.status = InvestmentStatus.CANCELLED
        investment.cancelled_at = datetime.utcnow()
        investment.metadata.update({
            'cancellation_reason': reason,
            'cancelled_by_task': task_id
        })
        
        investment_dao.update(investment.id, investment)
        
        logger.success(f"Investment {investment_id} cancelled successfully")
        
        return {
            'status': 'success',
            'investment_id': investment_id,
            'reason': reason
        }
        
    except Exception as e:
        logger.error(f"Failed to cancel investment {investment_id}: {e}")
        raise e
    finally:
        db.close()

@celery_app.task(bind=True)
def batch_execute_investments(self, investment_requests: List[Dict[str, Any]]):
    """
    Execute multiple investments in batch
    """
    task_id = self.request.id
    logger.info(f"Task {task_id}: Batch executing {len(investment_requests)} investments")
    
    results = []
    
    for req in investment_requests:
        try:
            # Queue individual investment execution
            task = execute_investment.delay(
                product_id=req['product_id'],
                amount=req['amount'],
                user_id=req.get('user_id', 'default')
            )
            
            results.append({
                'product_id': req['product_id'],
                'amount': req['amount'],
                'task_id': task.id,
                'status': 'queued'
            })
            
            # Rate limiting
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"Failed to queue investment for {req['product_id']}: {e}")
            results.append({
                'product_id': req['product_id'],
                'amount': req['amount'],
                'status': 'failed',
                'error': str(e)
            })
    
    return {
        'status': 'success',
        'total_requests': len(investment_requests),
        'results': results
    }