"""
Market data API endpoints
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from services.binance_service import binance_service
from core.dual_investment_engine import dual_investment_engine
from loguru import logger
import pandas as pd

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

@router.get("/kline-analysis/{symbol}")
async def get_kline_analysis(symbol: str):
    """Generate professional K-line analysis report for a symbol"""
    try:
        # Get current market data
        market_analysis = dual_investment_engine.analyze_market_conditions(symbol.upper())
        
        # Get K-line data for analysis
        try:
            df = binance_service.get_klines(symbol.upper(), "1h", 24)
            has_kline_data = True
            latest_close = df['Close'].iloc[-1] if not df.empty else market_analysis.get('current_price', 0)
            highest_24h = df['High'].max() if not df.empty else 0
            lowest_24h = df['Low'].min() if not df.empty else 0
            volume_24h = df['Volume'].sum() if not df.empty else 0
        except:
            has_kline_data = False
            latest_close = market_analysis.get('current_price', 0)
            highest_24h = 0
            lowest_24h = 0
            volume_24h = 0
        
        # Generate analysis report (placeholder for LLM integration)
        # In production, this would call an LLM API with K-line chart image
        report = f"""
# Professional K-Line Analysis Report
## {symbol.upper()} - {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}

### Market Overview
- **Current Price**: ${latest_close:,.2f}
- **24h High**: ${highest_24h:,.2f}
- **24h Low**: ${lowest_24h:,.2f}
- **24h Volume**: {volume_24h:,.2f}

### Technical Analysis
Based on the 1-hour K-line chart analysis:

**Trend Analysis**:
- The market is currently in a {market_analysis.get('trend', {}).get('trend', 'NEUTRAL')} trend
- Trend strength: {market_analysis.get('trend', {}).get('strength', 'MODERATE')}
- RSI indicates {market_analysis.get('signals', {}).get('rsi_signal', 'NEUTRAL')} signal
- MACD shows {market_analysis.get('signals', {}).get('macd_signal', 'NEUTRAL')} momentum

**Support & Resistance Levels**:
- **Primary Support**: ${market_analysis.get('support_resistance', {}).get('support', latest_close * 0.95):,.2f}
- **Primary Resistance**: ${market_analysis.get('support_resistance', {}).get('resistance', latest_close * 1.05):,.2f}
- **Pivot Point**: ${market_analysis.get('support_resistance', {}).get('pivot', latest_close):,.2f}

**Volatility Analysis**:
- Current volatility is {market_analysis.get('volatility', {}).get('risk_level', 'MEDIUM')}
- ATR: {market_analysis.get('volatility', {}).get('atr', 0):,.2f}
- Volatility ratio: {market_analysis.get('volatility', {}).get('volatility_ratio', 0):.4f}

### 24-Hour Prediction
Based on current market patterns and technical indicators:

**Price Direction**: {market_analysis.get('trend', {}).get('trend', 'NEUTRAL')}
- Expected to {'rise' if market_analysis.get('trend', {}).get('trend') == 'BULLISH' else 'fall' if market_analysis.get('trend', {}).get('trend') == 'BEARISH' else 'consolidate'}
- Target range: ${latest_close * 0.98:,.2f} - ${latest_close * 1.02:,.2f}

**Volatility Expectation**: {market_analysis.get('volatility', {}).get('risk_level', 'MEDIUM')}
- Market expected to show {'high' if market_analysis.get('volatility', {}).get('risk_level') == 'HIGH' else 'low' if market_analysis.get('volatility', {}).get('risk_level') == 'LOW' else 'moderate'} volatility

**Risk Assessment**: {market_analysis.get('volatility', {}).get('risk_level', 'MEDIUM')}
- Suitable for {'aggressive' if market_analysis.get('volatility', {}).get('risk_level') == 'LOW' else 'conservative' if market_analysis.get('volatility', {}).get('risk_level') == 'HIGH' else 'balanced'} investment strategies

### Investment Recommendation
{market_analysis.get('signals', {}).get('recommendation', 'HOLD')} - Based on current technical indicators

**Dual Investment Strategy**:
{'Consider BUY_LOW products with strike prices below current market price' if market_analysis.get('signals', {}).get('recommendation') in ['BUY', 'STRONG_BUY'] else 'Consider SELL_HIGH products with strike prices above current market price' if market_analysis.get('signals', {}).get('recommendation') in ['SELL', 'STRONG_SELL'] else 'Wait for clearer market signals before entering new positions'}

---
*Note: This analysis is based on technical indicators and should not be considered as financial advice.*
        """
        
        return {
            "symbol": symbol.upper(),
            "timestamp": pd.Timestamp.now().isoformat(),
            "has_kline_data": has_kline_data,
            "report": report.strip(),
            "market_data": market_analysis
        }
        
    except Exception as e:
        logger.error(f"Failed to generate K-line analysis for {symbol}: {e}")
        # Return a basic error report
        return {
            "symbol": symbol.upper(),
            "timestamp": pd.Timestamp.now().isoformat(),
            "has_kline_data": False,
            "report": f"Unable to generate complete analysis due to data availability. Error: {str(e)}",
            "market_data": {}
        }