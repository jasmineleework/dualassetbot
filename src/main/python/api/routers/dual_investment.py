"""
Dual Investment API endpoints
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from datetime import datetime
from services.binance_service import binance_service
from core.dual_investment_engine import dual_investment_engine
from loguru import logger

router = APIRouter(prefix="/api/v1/dual-investment", tags=["dual-investment"])

class DualInvestmentProduct(BaseModel):
    id: str
    asset: str
    currency: str
    type: str
    strike_price: float
    apy: float
    term_days: int
    min_amount: float
    max_amount: float
    settlement_date: datetime

class InvestmentDecision(BaseModel):
    product_id: str
    recommend: bool
    exercise_probability: float
    expected_return: float
    risk_score: float
    reasons: List[str]

class SubscribeRequest(BaseModel):
    product_id: str
    amount: float

@router.get("/products", response_model=List[DualInvestmentProduct])
async def get_dual_investment_products(
    asset: Optional[str] = Query(None, description="Filter by asset (e.g., BTC, ETH)"),
    type: Optional[str] = Query(None, description="Filter by type (BUY_LOW or SELL_HIGH)")
):
    """Get available dual investment products"""
    try:
        products = binance_service.get_dual_investment_products()
        
        # Apply filters
        if asset:
            products = [p for p in products if p['asset'] == asset.upper()]
        if type:
            products = [p for p in products if p['type'] == type.upper()]
        
        return products
    except Exception as e:
        logger.error(f"Failed to get dual investment products: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analyze/{symbol}")
async def analyze_investment_opportunity(symbol: str):
    """Analyze and recommend best dual investment product for a symbol"""
    try:
        decision = dual_investment_engine.select_best_product(symbol.upper())
        
        if not decision:
            return {
                "symbol": symbol.upper(),
                "recommendation": None,
                "message": "No suitable products found or none meet investment criteria"
            }
        
        # Generate detailed report
        report = dual_investment_engine.generate_investment_report(decision)
        
        return {
            "symbol": symbol.upper(),
            "recommendation": decision['evaluation'],
            "selected_product": decision['selected_product'],
            "report": report
        }
    except Exception as e:
        logger.error(f"Failed to analyze investment opportunity: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/subscribe")
async def subscribe_to_product(request: SubscribeRequest):
    """Subscribe to a dual investment product"""
    try:
        result = binance_service.subscribe_dual_investment(
            request.product_id,
            request.amount
        )
        return result
    except Exception as e:
        logger.error(f"Failed to subscribe to product: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/portfolio")
async def get_investment_portfolio():
    """Get current dual investment portfolio"""
    # This would normally query from database
    return {
        "active_investments": [],
        "total_invested": 0,
        "total_returns": 0,
        "message": "Portfolio tracking not yet implemented"
    }

@router.get("/history")
async def get_investment_history(
    limit: int = Query(50, description="Number of records to return"),
    offset: int = Query(0, description="Number of records to skip")
):
    """Get historical investment records"""
    # This would normally query from database
    return {
        "records": [],
        "total": 0,
        "limit": limit,
        "offset": offset,
        "message": "History tracking not yet implemented"
    }

@router.get("/ai-recommendations/{symbol}")
async def get_ai_recommendations(
    symbol: str,
    limit: int = Query(5, ge=1, le=20, description="Maximum number of recommendations")
):
    """Get AI-powered investment recommendations using strategy ensemble"""
    try:
        recommendations = dual_investment_engine.get_ai_recommendations(symbol.upper(), limit)
        
        return {
            "symbol": symbol.upper(),
            "timestamp": datetime.now().isoformat(),
            "total_recommendations": len(recommendations),
            "recommendations": recommendations
        }
        
    except Exception as e:
        logger.error(f"Failed to get AI recommendations for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))