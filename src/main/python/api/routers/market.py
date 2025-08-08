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

class PricePrediction(BaseModel):
    direction: str  # 'UP', 'DOWN', 'NEUTRAL'
    confidence: float
    target_price: Optional[float] = None

class VolatilityPrediction(BaseModel):
    level: str  # 'LOW', 'MEDIUM', 'HIGH'
    value: float

class MarketAnalysisResponse(BaseModel):
    symbol: str
    current_price: float
    price_change_24h: float
    trend: Dict[str, str]
    volatility: Dict[str, Any]
    signals: Dict[str, str]
    support_resistance: Dict[str, float]
    price_prediction_24h: Optional[PricePrediction] = None
    volatility_prediction: Optional[VolatilityPrediction] = None
    risk_level: Optional[str] = None

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
            "BTCUSDC": 95234.56,
            "ETHUSDT": 3245.67,
            "ETHUSDC": 3245.67,
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
        
        # Add enhanced predictions
        current_price = analysis.get('current_price', 0)
        trend = analysis.get('trend', {}).get('trend', 'NEUTRAL')
        volatility_ratio = analysis.get('volatility', {}).get('volatility_ratio', 0.02)
        
        # Simple price prediction based on trend
        if trend == 'BULLISH':
            price_prediction = PricePrediction(
                direction='UP',
                confidence=0.65,
                target_price=current_price * 1.02
            )
        elif trend == 'BEARISH':
            price_prediction = PricePrediction(
                direction='DOWN',
                confidence=0.65,
                target_price=current_price * 0.98
            )
        else:
            price_prediction = PricePrediction(
                direction='NEUTRAL',
                confidence=0.5,
                target_price=current_price
            )
        
        # Volatility prediction
        if volatility_ratio < 0.01:
            volatility_pred = VolatilityPrediction(level='LOW', value=volatility_ratio)
        elif volatility_ratio < 0.025:
            volatility_pred = VolatilityPrediction(level='MEDIUM', value=volatility_ratio)
        else:
            volatility_pred = VolatilityPrediction(level='HIGH', value=volatility_ratio)
        
        # Risk level assessment
        risk_level = 'LOW'
        if volatility_ratio > 0.025 and trend == 'BEARISH':
            risk_level = 'HIGH'
        elif volatility_ratio > 0.015:
            risk_level = 'MEDIUM'
        
        return MarketAnalysisResponse(
            **analysis,
            price_prediction_24h=price_prediction,
            volatility_prediction=volatility_pred,
            risk_level=risk_level
        )
    except ValueError as e:
        # Return mock analysis if Binance is not connected
        logger.warning(f"Using mock analysis for {symbol}: {e}")
        mock_price = 95234.56 if symbol.upper() == "BTCUSDT" else 3245.67 if symbol.upper() == "ETHUSDT" else 100.0
        return MarketAnalysisResponse(
            symbol=symbol.upper(),
            current_price=mock_price,
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
                "support": mock_price * 0.95,
                "resistance": mock_price * 1.05,
                "pivot": mock_price
            },
            price_prediction_24h=PricePrediction(
                direction='NEUTRAL',
                confidence=0.5,
                target_price=mock_price
            ),
            volatility_prediction=VolatilityPrediction(
                level='MEDIUM',
                value=0.013
            ),
            risk_level='MEDIUM'
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
    except Exception as e:
        logger.error(f"Failed to get 24hr stats for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get market stats: {str(e)}")

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
        raise HTTPException(status_code=500, detail=f"Failed to get klines: {str(e)}")