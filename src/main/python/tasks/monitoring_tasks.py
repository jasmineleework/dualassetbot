"""
Monitoring and reporting Celery tasks
"""
from celery_app import celery_app
from dao.investment import InvestmentDAO
from dao.strategy_log import StrategyLogDAO
from dao.market_data import MarketDataDAO
from models.investment import InvestmentStatus
from services.binance_service import binance_service
from core.database import get_db
from loguru import logger
from typing import Dict, Any, List
from datetime import datetime, timedelta
import json
import os

@celery_app.task(bind=True)
def monitor_active_investments(self):
    """
    Monitor all active investments and update their status
    """
    task_id = self.request.id
    logger.info(f"Task {task_id}: Monitoring active investments")
    
    try:
        db = next(get_db())
        investment_dao = InvestmentDAO(db)
        
        # Get all active investments
        active_investments = investment_dao.get_by_status(InvestmentStatus.ACTIVE)
        monitored_count = 0
        updated_count = 0
        
        for investment in active_investments:
            try:
                # Check investment status via Binance API
                if investment.binance_order_id:
                    status_info = binance_service.get_investment_status(investment.binance_order_id)
                    
                    if status_info:
                        # Update investment if status changed
                        updated = False
                        
                        if status_info.get('status') == 'SETTLED':
                            investment.status = InvestmentStatus.COMPLETED
                            investment.completed_at = datetime.utcnow()
                            investment.actual_return = status_info.get('pnl', 0)
                            updated = True
                        elif status_info.get('status') == 'CANCELLED':
                            investment.status = InvestmentStatus.CANCELLED
                            investment.cancelled_at = datetime.utcnow()
                            updated = True
                        elif status_info.get('status') == 'FAILED':
                            investment.status = InvestmentStatus.FAILED
                            investment.error_message = status_info.get('error', 'Unknown error')
                            updated = True
                        
                        # Update metadata with latest info
                        investment.metadata.update({
                            'last_monitored': datetime.utcnow().isoformat(),
                            'binance_status': status_info
                        })
                        
                        if updated:
                            investment_dao.update(investment.id, investment)
                            updated_count += 1
                            logger.info(f"Updated investment {investment.id} status to {investment.status}")
                
                monitored_count += 1
                
            except Exception as e:
                logger.error(f"Failed to monitor investment {investment.id}: {e}")
                continue
        
        logger.success(f"Monitored {monitored_count} investments, updated {updated_count}")
        
        return {
            'status': 'success',
            'monitored_count': monitored_count,
            'updated_count': updated_count,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Task {task_id} failed: {e}")
        raise e
    finally:
        db.close()

@celery_app.task(bind=True)
def generate_daily_report(self):
    """
    Generate daily performance report
    """
    task_id = self.request.id
    logger.info(f"Task {task_id}: Generating daily report")
    
    try:
        db = next(get_db())
        investment_dao = InvestmentDAO(db)
        strategy_log_dao = StrategyLogDAO(db)
        market_dao = MarketDataDAO(db)
        
        # Calculate date range (yesterday)
        end_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        start_date = end_date - timedelta(days=1)
        
        # Get investment statistics
        investments = investment_dao.get_investments_in_range(start_date, end_date)
        total_invested = sum(inv.amount for inv in investments)
        active_investments = [inv for inv in investments if inv.status == InvestmentStatus.ACTIVE]
        completed_investments = [inv for inv in investments if inv.status == InvestmentStatus.COMPLETED]
        failed_investments = [inv for inv in investments if inv.status == InvestmentStatus.FAILED]
        
        # Calculate returns
        total_returns = sum(inv.actual_return or 0 for inv in completed_investments)
        
        # Get strategy performance
        strategy_logs = strategy_log_dao.get_logs_in_range(start_date, end_date)
        ai_decisions = [log for log in strategy_logs if log.strategy_name == 'AI_Recommendation']
        trading_decisions = [log for log in strategy_logs if log.decision_made]
        
        # Get market overview
        market_data = market_dao.get_latest_data(['BTCUSDT', 'ETHUSDT'])
        
        # Generate report
        report = {
            'date': start_date.strftime('%Y-%m-%d'),
            'summary': {
                'total_investments': len(investments),
                'total_invested': total_invested,
                'active_investments': len(active_investments),
                'completed_investments': len(completed_investments),
                'failed_investments': len(failed_investments),
                'total_returns': total_returns,
                'net_pnl': total_returns - sum(inv.amount for inv in failed_investments),
                'success_rate': len(completed_investments) / len(investments) * 100 if investments else 0
            },
            'strategy_performance': {
                'ai_recommendations': len(ai_decisions),
                'trading_decisions': len(trading_decisions),
                'average_ai_score': sum(log.ai_score or 0 for log in ai_decisions) / len(ai_decisions) if ai_decisions else 0,
                'positive_decisions': len([log for log in trading_decisions if log.decision_made]),
                'decision_accuracy': len([log for log in trading_decisions if log.execution_successful]) / len(trading_decisions) * 100 if trading_decisions else 0
            },
            'market_overview': {
                symbol: {
                    'price': data.price,
                    'change_24h': data.price_change_24h,
                    'volume': data.volume_24h
                }
                for symbol, data in market_data.items()
            },
            'top_performers': [
                {
                    'product_id': inv.product_id,
                    'amount': inv.amount,
                    'return': inv.actual_return,
                    'return_pct': (inv.actual_return / inv.amount * 100) if inv.amount > 0 else 0
                }
                for inv in sorted(completed_investments, key=lambda x: x.actual_return or 0, reverse=True)[:5]
            ],
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Save report to file
        report_filename = f"daily_report_{start_date.strftime('%Y%m%d')}.json"
        report_path = os.path.join('reports', report_filename)
        
        os.makedirs('reports', exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.success(f"Daily report generated: {report_path}")
        
        return {
            'status': 'success',
            'report_path': report_path,
            'report': report
        }
        
    except Exception as e:
        logger.error(f"Task {task_id} failed: {e}")
        raise e
    finally:
        db.close()

@celery_app.task(bind=True)
def generate_performance_metrics(self, days: int = 7):
    """
    Generate performance metrics for the last N days
    """
    task_id = self.request.id
    logger.info(f"Task {task_id}: Generating {days}-day performance metrics")
    
    try:
        db = next(get_db())
        investment_dao = InvestmentDAO(db)
        strategy_log_dao = StrategyLogDAO(db)
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get all investments in range
        investments = investment_dao.get_investments_in_range(start_date, end_date)
        
        # Calculate key metrics
        metrics = {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': days
            },
            'investment_metrics': {
                'total_investments': len(investments),
                'total_invested': sum(inv.amount for inv in investments),
                'average_investment': sum(inv.amount for inv in investments) / len(investments) if investments else 0,
                'success_rate': len([inv for inv in investments if inv.status == InvestmentStatus.COMPLETED]) / len(investments) * 100 if investments else 0,
                'failure_rate': len([inv for inv in investments if inv.status == InvestmentStatus.FAILED]) / len(investments) * 100 if investments else 0
            },
            'return_metrics': {
                'total_returns': sum(inv.actual_return or 0 for inv in investments),
                'average_return': sum(inv.actual_return or 0 for inv in investments) / len(investments) if investments else 0,
                'best_return': max((inv.actual_return or 0 for inv in investments), default=0),
                'worst_return': min((inv.actual_return or 0 for inv in investments), default=0),
                'roi_percentage': (sum(inv.actual_return or 0 for inv in investments) / sum(inv.amount for inv in investments) * 100) if sum(inv.amount for inv in investments) > 0 else 0
            },
            'strategy_metrics': {
                'total_decisions': len(strategy_log_dao.get_logs_in_range(start_date, end_date)),
                'ai_recommendations': len([log for log in strategy_log_dao.get_logs_in_range(start_date, end_date) if log.strategy_name == 'AI_Recommendation']),
                'executed_trades': len([log for log in strategy_log_dao.get_logs_in_range(start_date, end_date) if log.execution_successful]),
                'average_ai_score': sum(log.ai_score or 0 for log in strategy_log_dao.get_logs_in_range(start_date, end_date)) / len(strategy_log_dao.get_logs_in_range(start_date, end_date)) if strategy_log_dao.get_logs_in_range(start_date, end_date) else 0
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
        logger.success(f"Performance metrics calculated for {days} days")
        
        return {
            'status': 'success',
            'metrics': metrics
        }
        
    except Exception as e:
        logger.error(f"Task {task_id} failed: {e}")
        raise e
    finally:
        db.close()

@celery_app.task(bind=True)
def cleanup_old_data(self):
    """
    Clean up old logs and data
    """
    task_id = self.request.id
    logger.info(f"Task {task_id}: Cleaning up old data")
    
    try:
        db = next(get_db())
        strategy_log_dao = StrategyLogDAO(db)
        market_dao = MarketDataDAO(db)
        
        # Clean up old strategy logs (keep 90 days)
        log_cutoff = datetime.utcnow() - timedelta(days=90)
        deleted_logs = strategy_log_dao.delete_old_logs(log_cutoff)
        
        # Clean up old market data (keep 30 days)
        market_cutoff = datetime.utcnow() - timedelta(days=30)
        deleted_market_data = market_dao.delete_old_records(market_cutoff)
        
        # Clean up old report files
        reports_dir = 'reports'
        deleted_reports = 0
        
        if os.path.exists(reports_dir):
            report_cutoff = datetime.utcnow() - timedelta(days=180)  # Keep 6 months
            
            for filename in os.listdir(reports_dir):
                if filename.startswith('daily_report_') and filename.endswith('.json'):
                    filepath = os.path.join(reports_dir, filename)
                    file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                    
                    if file_time < report_cutoff:
                        os.remove(filepath)
                        deleted_reports += 1
        
        logger.success(f"Cleanup completed: {deleted_logs} logs, {deleted_market_data} market records, {deleted_reports} reports")
        
        return {
            'status': 'success',
            'deleted_logs': deleted_logs,
            'deleted_market_data': deleted_market_data,
            'deleted_reports': deleted_reports,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Task {task_id} failed: {e}")
        raise e
    finally:
        db.close()

@celery_app.task(bind=True)
def health_check(self):
    """
    System health check task
    """
    task_id = self.request.id
    logger.info(f"Task {task_id}: Performing system health check")
    
    try:
        # Check database connectivity
        db = next(get_db())
        
        # Check Binance API connectivity
        try:
            price = binance_service.get_symbol_price('BTCUSDT')
            api_healthy = bool(price)
        except Exception:
            api_healthy = False
        
        # Check task queues
        celery_healthy = True  # If this task is running, Celery is working
        
        health_status = {
            'database': 'healthy',
            'binance_api': 'healthy' if api_healthy else 'unhealthy',
            'celery': 'healthy' if celery_healthy else 'unhealthy',
            'overall': 'healthy' if api_healthy and celery_healthy else 'degraded',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        logger.success(f"Health check completed: {health_status['overall']}")
        
        return {
            'status': 'success',
            'health': health_status
        }
        
    except Exception as e:
        logger.error(f"Task {task_id} failed: {e}")
        return {
            'status': 'error',
            'health': {
                'database': 'unhealthy',
                'binance_api': 'unknown',
                'celery': 'unhealthy',
                'overall': 'critical',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
        }
    finally:
        if 'db' in locals():
            db.close()