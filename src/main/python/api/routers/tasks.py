"""
Task management API endpoints
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from datetime import datetime
from celery.result import AsyncResult
from celery import current_app
from tasks.analysis_tasks import update_market_data, generate_ai_recommendations, analyze_market_trends
from tasks.monitoring_tasks import monitor_active_investments, generate_daily_report, generate_performance_metrics, health_check
from loguru import logger

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])

class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: str

class TaskRequest(BaseModel):
    symbols: Optional[List[str]] = None
    parameters: Optional[Dict[str, Any]] = None

@router.post("/market-data/update", response_model=TaskResponse)
async def trigger_market_data_update(request: TaskRequest):
    """
    Trigger market data update for specified symbols
    """
    try:
        symbols = request.symbols or ['BTCUSDT', 'ETHUSDT']
        
        # Queue market data update
        task = update_market_data.delay(symbols)
        
        logger.info(f"Triggered market data update for symbols: {symbols}")
        
        return TaskResponse(
            task_id=task.id,
            status="queued",
            message=f"Market data update queued for {len(symbols)} symbols"
        )
        
    except Exception as e:
        logger.error(f"Failed to trigger market data update: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ai-recommendations/generate", response_model=TaskResponse)
async def trigger_ai_recommendations(request: TaskRequest):
    """
    Trigger AI recommendation generation for specified symbols
    """
    try:
        symbols = request.symbols or ['BTCUSDT', 'ETHUSDT']
        
        # Queue AI recommendations generation
        task = generate_ai_recommendations.delay(symbols)
        
        logger.info(f"Triggered AI recommendations generation for symbols: {symbols}")
        
        return TaskResponse(
            task_id=task.id,
            status="queued",
            message=f"AI recommendations generation queued for {len(symbols)} symbols"
        )
        
    except Exception as e:
        logger.error(f"Failed to trigger AI recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/market-analysis/analyze", response_model=TaskResponse)
async def trigger_market_analysis(symbol: str):
    """
    Trigger detailed market analysis for a specific symbol
    """
    try:
        # Queue market analysis
        task = analyze_market_trends.delay(symbol)
        
        logger.info(f"Triggered market analysis for symbol: {symbol}")
        
        return TaskResponse(
            task_id=task.id,
            status="queued",
            message=f"Market analysis queued for {symbol}"
        )
        
    except Exception as e:
        logger.error(f"Failed to trigger market analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/monitoring/investments", response_model=TaskResponse)
async def trigger_investment_monitoring():
    """
    Trigger monitoring of active investments
    """
    try:
        # Queue investment monitoring
        task = monitor_active_investments.delay()
        
        logger.info("Triggered investment monitoring")
        
        return TaskResponse(
            task_id=task.id,
            status="queued",
            message="Investment monitoring queued"
        )
        
    except Exception as e:
        logger.error(f"Failed to trigger investment monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reports/daily", response_model=TaskResponse)
async def trigger_daily_report():
    """
    Trigger daily performance report generation
    """
    try:
        # Queue daily report generation
        task = generate_daily_report.delay()
        
        logger.info("Triggered daily report generation")
        
        return TaskResponse(
            task_id=task.id,
            status="queued",
            message="Daily report generation queued"
        )
        
    except Exception as e:
        logger.error(f"Failed to trigger daily report: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reports/performance", response_model=TaskResponse)
async def trigger_performance_metrics(days: int = Query(7, ge=1, le=365)):
    """
    Trigger performance metrics generation
    """
    try:
        # Queue performance metrics generation
        task = generate_performance_metrics.delay(days)
        
        logger.info(f"Triggered performance metrics generation for {days} days")
        
        return TaskResponse(
            task_id=task.id,
            status="queued",
            message=f"Performance metrics generation queued for {days} days"
        )
        
    except Exception as e:
        logger.error(f"Failed to trigger performance metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{task_id}")
async def get_task_status(task_id: str):
    """
    Get the status and result of a specific task
    """
    try:
        result = AsyncResult(task_id)
        
        response = {
            "task_id": task_id,
            "status": result.status,
            "ready": result.ready(),
            "successful": result.successful() if result.ready() else None,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if result.ready():
            if result.successful():
                response["result"] = result.result
            else:
                response["error"] = str(result.info)
                response["traceback"] = getattr(result, 'traceback', None)
        else:
            # Task is still running, check for progress info
            response["info"] = result.info
        
        return response
        
    except Exception as e:
        logger.error(f"Failed to get task status for {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/active")
async def get_active_tasks():
    """
    Get list of currently active tasks
    """
    try:
        # Get Celery app inspect instance
        inspect = current_app.control.inspect()
        
        # Get active tasks from all workers
        active_tasks = inspect.active()
        
        if not active_tasks:
            return {
                "active_tasks": [],
                "total_workers": 0,
                "total_tasks": 0
            }
        
        # Flatten active tasks from all workers
        all_tasks = []
        for worker, tasks in active_tasks.items():
            for task in tasks:
                all_tasks.append({
                    "task_id": task["id"],
                    "name": task["name"],
                    "worker": worker,
                    "args": task.get("args", []),
                    "kwargs": task.get("kwargs", {}),
                    "time_start": task.get("time_start"),
                    "acknowledged": task.get("acknowledged", False)
                })
        
        return {
            "active_tasks": all_tasks,
            "total_workers": len(active_tasks),
            "total_tasks": len(all_tasks)
        }
        
    except Exception as e:
        logger.error(f"Failed to get active tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/scheduled")
async def get_scheduled_tasks():
    """
    Get list of scheduled (reserved) tasks
    """
    try:
        # Get Celery app inspect instance
        inspect = current_app.control.inspect()
        
        # Get scheduled tasks from all workers
        scheduled_tasks = inspect.scheduled()
        
        if not scheduled_tasks:
            return {
                "scheduled_tasks": [],
                "total_workers": 0,
                "total_tasks": 0
            }
        
        # Flatten scheduled tasks from all workers
        all_tasks = []
        for worker, tasks in scheduled_tasks.items():
            for task in tasks:
                all_tasks.append({
                    "task_id": task["request"]["id"],
                    "name": task["request"]["task"],
                    "worker": worker,
                    "args": task["request"].get("args", []),
                    "kwargs": task["request"].get("kwargs", {}),
                    "eta": task.get("eta"),
                    "priority": task["request"].get("priority", 5)
                })
        
        return {
            "scheduled_tasks": all_tasks,
            "total_workers": len(scheduled_tasks),
            "total_tasks": len(all_tasks)
        }
        
    except Exception as e:
        logger.error(f"Failed to get scheduled tasks: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_task_stats():
    """
    Get overall task execution statistics
    """
    try:
        # Get Celery app inspect instance
        inspect = current_app.control.inspect()
        
        # Get worker statistics
        stats = inspect.stats()
        
        if not stats:
            return {
                "workers": [],
                "total_workers": 0,
                "overall_stats": {
                    "total_tasks": 0,
                    "pool_processes": 0,
                    "rusage": {}
                }
            }
        
        workers_info = []
        total_tasks = 0
        total_processes = 0
        
        for worker, worker_stats in stats.items():
            worker_info = {
                "worker": worker,
                "status": "online",
                "total_tasks": worker_stats.get("total", {}),
                "pool_processes": worker_stats.get("pool", {}).get("processes", 0),
                "rusage": worker_stats.get("rusage", {}),
                "clock": worker_stats.get("clock"),
                "pid": worker_stats.get("pid"),
                "broker": worker_stats.get("broker", {})
            }
            workers_info.append(worker_info)
            
            # Aggregate stats
            worker_total = worker_stats.get("total", {})
            if isinstance(worker_total, dict):
                for task_name, count in worker_total.items():
                    if isinstance(count, int):
                        total_tasks += count
            
            total_processes += worker_info["pool_processes"]
        
        return {
            "workers": workers_info,
            "total_workers": len(workers_info),
            "overall_stats": {
                "total_tasks": total_tasks,
                "total_processes": total_processes,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get task stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/health-check", response_model=TaskResponse)
async def trigger_health_check():
    """
    Trigger system health check
    """
    try:
        # Queue health check
        task = health_check.delay()
        
        logger.info("Triggered system health check")
        
        return TaskResponse(
            task_id=task.id,
            status="queued",
            message="System health check queued"
        )
        
    except Exception as e:
        logger.error(f"Failed to trigger health check: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/cancel/{task_id}")
async def cancel_task(task_id: str):
    """
    Cancel a running or pending task
    """
    try:
        # Revoke the task
        current_app.control.revoke(task_id, terminate=True)
        
        logger.info(f"Cancelled task: {task_id}")
        
        return {
            "status": "success",
            "message": f"Task {task_id} cancelled",
            "task_id": task_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to cancel task {task_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))