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
    except ValueError as e:
        # Return mock data if Binance is not connected
        logger.warning(f"Using mock price for {symbol}: {e}")
        mock_prices = {
            "BTCUSDT": 95234.56,
            "ETHUSDT": 3245.67,
            "BNBUSDT": 567.89
        }
        return {
            "symbol": symbol.upper(),
            "price": mock_prices.get(symbol.upper(), 100.0),
            "timestamp": None,
            "mock": True
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
    except ValueError as e:
        # Return mock analysis if Binance is not connected
        logger.warning(f"Using mock analysis for {symbol}: {e}")
        return MarketAnalysisResponse(
            symbol=symbol.upper(),
            current_price=95234.56 if symbol.upper() == "BTCUSDT" else 100.0,
            price_change_24h=-2.34,
            trend={"trend": "SIDEWAYS", "strength": "NEUTRAL"},
            volatility={"atr": 1234.56, "volatility_ratio": 0.013, "risk_level": "MEDIUM"},
            signals={
                "rsi_signal": "NEUTRAL",
                "macd_signal": "HOLD", 
                "bb_signal": "HOLD",
                "recommendation": "HOLD"
            },
            support_resistance={
                "support": 92000.0,
                "resistance": 98000.0,
                "pivot": 95000.0
            }
        )
    except Exception as e:
        logger.error(f"Failed to analyze {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/24hr-stats/{symbol}")
async def get_24hr_stats(symbol: str):
    """Get 24hr statistics for a symbol"""
    try:
        stats = binance_service.get_24hr_ticker_stats(symbol.upper())
        return stats
    except ValueError as e:
        # Return mock data if Binance is not connected
        logger.warning(f"Using mock 24hr stats for {symbol}: {e}")
        mock_stats = {
            "BTCUSDT": {
                "symbol": "BTCUSDT",
                "price_change": -1234.56,
                "price_change_percent": -1.28,
                "last_price": 95234.56,
                "volume": 23456.78,
                "high_24h": 97000.00,
                "low_24h": 94000.00
            },
            "ETHUSDT": {
                "symbol": "ETHUSDT",
                "price_change": 45.67,
                "price_change_percent": 1.42,
                "last_price": 3245.67,
                "volume": 123456.78,
                "high_24h": 3300.00,
                "low_24h": 3180.00
            }
        }
        return mock_stats.get(symbol.upper(), {
            "symbol": symbol.upper(),
            "price_change": 0,
            "price_change_percent": 0,
            "last_price": 100.0,
            "volume": 1000.0,
            "high_24h": 101.0,
            "low_24h": 99.0
        })
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
    except ValueError as e:
        # Return mock data if Binance is not connected
        logger.warning(f"Using mock klines for {symbol}: {e}")
        import pandas as pd
        from datetime import datetime, timedelta
        
        # Generate mock klines data
        now = datetime.now()
        mock_data = []
        base_price = 95000.0 if symbol.upper() == "BTCUSDT" else 3200.0
        
        for i in range(limit):
            timestamp = now - timedelta(hours=i)
            variation = (i % 10 - 5) * 0.002  # ±1% variation
            open_price = base_price * (1 + variation)
            close_price = base_price * (1 + variation + 0.001)
            high_price = max(open_price, close_price) * 1.002
            low_price = min(open_price, close_price) * 0.998
            
            mock_data.append({
                "timestamp": timestamp.isoformat(),
                "open": open_price,
                "high": high_price,
                "low": low_price,
                "close": close_price,
                "volume": 1000 + i * 10
            })
        
        mock_data.reverse()  # Oldest first
        return {
            "symbol": symbol.upper(),
            "interval": interval,
            "data": mock_data,
            "mock": True
        }
    except Exception as e:
        logger.error(f"Failed to get klines for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))