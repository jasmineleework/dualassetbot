"""
Celery application configuration for DualAssetBot
"""
from celery import Celery
from core.config import settings
from loguru import logger
import os

# Create Celery instance
celery_app = Celery(
    "dualassetbot",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=['tasks.trading_tasks', 'tasks.analysis_tasks', 'tasks.monitoring_tasks', 'tasks.update_products']
)

# Celery configuration
celery_app.conf.update(
    # Task routing
    task_routes={
        'tasks.trading_tasks.*': {'queue': 'trading'},
        'tasks.analysis_tasks.*': {'queue': 'analysis'},
        'tasks.monitoring_tasks.*': {'queue': 'monitoring'},
    },
    
    # Task serialization
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Task execution
    task_always_eager=False,  # Set to True for testing
    task_eager_propagates=True,
    
    # Results
    result_expires=3600,  # 1 hour
    result_backend_transport_options={
        'master_name': 'mymaster'
    },
    
    # Worker configuration
    worker_max_tasks_per_child=1000,
    worker_disable_rate_limits=False,
    
    # Beat schedule for periodic tasks
    beat_schedule={
        # Every 5 minutes - Update dual investment products
        'update-dual-products': {
            'task': 'update_dual_investment_products',
            'schedule': 300.0,  # 5 minutes
        },
        
        # Every 5 minutes - Market data update
        'update-market-data': {
            'task': 'tasks.analysis_tasks.update_market_data',
            'schedule': 300.0,  # 5 minutes
        },
        
        # Every 15 minutes - AI analysis and recommendations
        'generate-ai-recommendations': {
            'task': 'tasks.analysis_tasks.generate_ai_recommendations',
            'schedule': 900.0,  # 15 minutes
            'args': (['BTCUSDT', 'ETHUSDT'],)  # Default symbols
        },
        
        # Every 30 minutes - Execute approved investments
        'execute-pending-investments': {
            'task': 'tasks.trading_tasks.execute_pending_investments',
            'schedule': 1800.0,  # 30 minutes
        },
        
        # Every hour - Portfolio monitoring
        'monitor-portfolio': {
            'task': 'tasks.monitoring_tasks.monitor_active_investments',
            'schedule': 3600.0,  # 1 hour
        },
        
        # Daily at 8:00 UTC - Generate daily report
        'daily-report': {
            'task': 'tasks.monitoring_tasks.generate_daily_report',
            'schedule': 'crontab(hour=8, minute=0)',
        },
        
        # Weekly cleanup - Remove old logs and data
        'weekly-cleanup': {
            'task': 'tasks.monitoring_tasks.cleanup_old_data',
            'schedule': 'crontab(hour=2, minute=0, day_of_week=1)',  # Monday 2:00 UTC
        },
    },
    beat_schedule_filename='celerybeat-schedule',
)

# Task annotations for rate limiting
celery_app.conf.task_annotations = {
    'tasks.trading_tasks.execute_investment': {'rate_limit': '10/m'},  # Max 10 trades per minute
    'tasks.analysis_tasks.update_market_data': {'rate_limit': '60/m'},  # Max 60 API calls per minute
}

@celery_app.task(bind=True)
def debug_task(self):
    """Debug task for testing"""
    print(f'Request: {self.request!r}')
    logger.info("Celery debug task executed successfully")
    return "Celery is working!"

if __name__ == '__main__':
    celery_app.start()