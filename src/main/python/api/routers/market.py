"""
Market data API endpoints
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from services.binance_service import binance_service
from core.dual_investment_engine import dual_investment_engine
from loguru import logger

router = APIRouter(prefix="/api/v1/market", tags=["market"])

class MarketAnalysisResponse(BaseModel):
    symbol: str
    current_price: float
    price_change_24h: float
    trend: Dict[str, str]
    volatility: Dict[str, Any]
    signals: Dict[str, str]
    support_resistance: Dict[str, float]

@router.get("/price/{symbol}")
async def get_symbol_price(symbol: str):
    """Get current price for a symbol"""
    try:
        price = binance_service.get_symbol_price(symbol.upper())
        return {
            "symbol": symbol.upper(),
            "price": price,
            "timestamp": None
        }
    except Exception as e:
        logger.error(f"Failed to get price for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analysis/{symbol}", response_model=MarketAnalysisResponse)
async def get_market_analysis(symbol: str):
    """Get comprehensive market analysis for a symbol"""
    try:
        analysis = dual_investment_engine.analyze_market_conditions(symbol.upper())
        return MarketAnalysisResponse(**analysis)
    except Exception as e:
        logger.error(f"Failed to analyze {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/24hr-stats/{symbol}")
async def get_24hr_stats(symbol: str):
    """Get 24hr statistics for a symbol"""
    try:
        stats = binance_service.get_24hr_ticker_stats(symbol.upper())
        return stats
    except Exception as e:
        logger.error(f"Failed to get 24hr stats for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/klines/{symbol}")
async def get_klines(
    symbol: str,
    interval: str = "1h",
    limit: int = 100
):
    """Get historical klines data"""
    try:
        df = binance_service.get_klines(symbol.upper(), interval, limit)
        # Convert DataFrame to JSON-serializable format
        data = df.reset_index().to_dict(orient='records')
        return {
            "symbol": symbol.upper(),
            "interval": interval,
            "data": data
        }
    except Exception as e:
        logger.error(f"Failed to get klines for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))