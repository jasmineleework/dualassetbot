"""
Market data API endpoints
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from services.binance_service import binance_service
from core.dual_investment_engine import dual_investment_engine
from services.ai_analysis_service import ai_analysis_service
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
    trend: Dict[str, Any]  # Changed to Any to support nested indicators dict
    volatility: Dict[str, Any]
    signals: Dict[str, Any]  # Changed to Any to support nested indicators dict
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
        trend_obj = analysis.get('trend', {})
        trend = trend_obj.get('trend', 'NEUTRAL')
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
async def get_kline_analysis(
    symbol: str, 
    include_chart: bool = True, 
    include_ai: bool = True,
    force_refresh: bool = False
):
    """Generate professional K-line analysis report with chart for a symbol"""
    try:
        # Get current market data
        market_analysis = dual_investment_engine.analyze_market_conditions(symbol.upper())
        
        # Get K-line data for analysis
        try:
            # Get 24hr stats from ticker API for accurate data
            stats_24hr = binance_service.get_24hr_ticker_stats(symbol.upper())
            
            # Get K-line data
            df = binance_service.get_klines(symbol.upper(), "1h", 24)
            has_kline_data = True
            
            # Use correct column names (lowercase)
            latest_close = df['close'].iloc[-1] if not df.empty else market_analysis.get('current_price', 0)
            
            # Use 24hr stats from API for accurate values
            highest_24h = stats_24hr.get('high_24h', df['high'].max() if not df.empty else 0)
            lowest_24h = stats_24hr.get('low_24h', df['low'].min() if not df.empty else 0)
            volume_24h = stats_24hr.get('volume', df['volume'].sum() if not df.empty else 0)
            
        except Exception as e:
            logger.warning(f"Failed to get kline data for {symbol}: {e}")
            has_kline_data = False
            latest_close = market_analysis.get('current_price', 0)
            
            # Try to get 24hr stats as fallback
            try:
                stats_24hr = binance_service.get_24hr_ticker_stats(symbol.upper())
                highest_24h = stats_24hr.get('high_24h', 0)
                lowest_24h = stats_24hr.get('low_24h', 0)
                volume_24h = stats_24hr.get('volume', 0)
            except:
                highest_24h = 0
                lowest_24h = 0
                volume_24h = 0
        
        # Generate chart if requested
        chart_data = None
        if include_chart:
            try:
                # Try screenshot service first (Binance Futures)
                from services.screenshot_service import screenshot_service
                chart_result = screenshot_service.capture_with_fallback(symbol.upper())
                
                if chart_result['success']:
                    chart_data = {
                        'image_base64': chart_result['image_base64'],
                        'source': chart_result['source'],
                        'timestamp': pd.Timestamp.now().isoformat()
                    }
                    logger.info(f"Chart generated from {chart_result['source']} for {symbol}")
                else:
                    # If screenshot fails, try direct chart generation
                    from services.chart_generator import chart_generator
                    image_base64 = chart_generator.generate_advanced_chart(
                        symbol.upper(), 
                        interval='1h',
                        limit=100,
                        indicators=['RSI', 'MACD']
                    )
                    if image_base64:
                        chart_data = {
                            'image_base64': image_base64,
                            'source': 'generated',
                            'timestamp': pd.Timestamp.now().isoformat()
                        }
            except Exception as chart_error:
                logger.warning(f"Could not generate chart for {symbol}: {chart_error}")
        
        # Generate structured analysis report
        trend = market_analysis.get('trend', {})
        signals = market_analysis.get('signals', {})
        volatility = market_analysis.get('volatility', {})
        support_resistance = market_analysis.get('support_resistance', {})
        
        # Calculate predictions
        trend_direction = trend.get('trend', 'NEUTRAL')
        risk_level = volatility.get('risk_level', 'MEDIUM')
        recommendation = signals.get('recommendation', 'HOLD')
        
        # Price targets based on volatility and trend
        volatility_ratio = volatility.get('volatility_ratio', 0.02)
        if trend_direction == 'BULLISH':
            target_low = latest_close * (1 - volatility_ratio * 0.5)
            target_high = latest_close * (1 + volatility_ratio * 2)
            price_direction = 'UP'
            confidence = 0.65
        elif trend_direction == 'BEARISH':
            target_low = latest_close * (1 - volatility_ratio * 2)
            target_high = latest_close * (1 + volatility_ratio * 0.5)
            price_direction = 'DOWN'
            confidence = 0.65
        else:
            target_low = latest_close * (1 - volatility_ratio)
            target_high = latest_close * (1 + volatility_ratio)
            price_direction = 'SIDEWAYS'
            confidence = 0.5
        
        # Investment strategy recommendation
        if recommendation in ['BUY', 'STRONG_BUY']:
            strategy_recommendation = 'BUY_LOW'
            strategy_description = 'Consider BUY_LOW dual investment products with strike prices 2-5% below current market price'
        elif recommendation in ['SELL', 'STRONG_SELL']:
            strategy_recommendation = 'SELL_HIGH'
            strategy_description = 'Consider SELL_HIGH dual investment products with strike prices 2-5% above current market price'
        else:
            strategy_recommendation = 'WAIT'
            strategy_description = 'Wait for clearer market signals before entering new dual investment positions'
        
        # Build structured report data
        report_data = {
            'overview': {
                'symbol': symbol.upper(),
                'timestamp': pd.Timestamp.now().isoformat(),
                'current_price': latest_close,
                'price_change_24h': market_analysis.get('price_change_24h', 0),
                'high_24h': highest_24h,
                'low_24h': lowest_24h,
                'volume_24h': volume_24h,
                'volume_change': market_analysis.get('volume_analysis', {}).get('obv_trend', 'NEUTRAL')
            },
            'technical_analysis': {
                'trend': {
                    'direction': trend_direction,
                    'strength': trend.get('strength', 'MODERATE'),
                    'ema_signal': trend.get('ema_trend', 'NEUTRAL')
                },
                'indicators': {
                    'rsi': {
                        'value': signals.get('rsi_value', 50),
                        'signal': signals.get('rsi_signal', 'NEUTRAL')
                    },
                    'macd': {
                        'signal': signals.get('macd_signal', 'NEUTRAL'),
                        'histogram': signals.get('macd_histogram', 0)
                    },
                    'bollinger': {
                        'signal': signals.get('bb_signal', 'NEUTRAL'),
                        'position': signals.get('bb_position', 'MIDDLE')
                    },
                    'mfi': market_analysis.get('volume_analysis', {}).get('mfi', 50)
                },
                'support_resistance': {
                    'support': support_resistance.get('support', latest_close * 0.95),
                    'resistance': support_resistance.get('resistance', latest_close * 1.05),
                    'pivot': support_resistance.get('pivot', latest_close)
                },
                'volatility': {
                    'level': risk_level,
                    'atr': volatility.get('atr', 0),
                    'ratio': volatility_ratio,
                    'description': 'High volatility - larger price swings expected' if risk_level == 'HIGH' else 'Low volatility - stable price action' if risk_level == 'LOW' else 'Moderate volatility - normal market conditions'
                }
            },
            'prediction': {
                '24h': {
                    'direction': price_direction,
                    'confidence': confidence,
                    'target_range': {
                        'low': target_low,
                        'high': target_high
                    },
                    'expected_volatility': risk_level
                }
            },
            'recommendation': {
                'signal': recommendation,
                'strategy': strategy_recommendation,
                'description': strategy_description,
                'risk_level': risk_level,
                'suitability': 'Aggressive traders' if risk_level == 'LOW' else 'Conservative traders' if risk_level == 'HIGH' else 'Balanced portfolios'
            }
        }
        
        # Generate human-readable summary
        summary = f"""
## Market Analysis Summary for {symbol.upper()}

**Current Status**: {symbol.upper()} is trading at ${latest_close:,.2f} in a {trend_direction} trend with {trend.get('strength', 'MODERATE').lower()} momentum.

**Key Levels**: Support at ${support_resistance.get('support', latest_close * 0.95):,.2f}, Resistance at ${support_resistance.get('resistance', latest_close * 1.05):,.2f}

**24h Forecast**: Price expected to {price_direction.lower()} with {confidence:.0%} confidence. Target range: ${target_low:,.2f} - ${target_high:,.2f}

**Trading Recommendation**: {recommendation} - {strategy_description}

**Risk Assessment**: {risk_level} volatility environment, suitable for {report_data['recommendation']['suitability'].lower()}
        """
        
        # Add AI-powered analysis if enabled and API key is configured
        ai_analysis = None
        if include_ai:
            try:
                # Get dual investment products for AI analysis
                dual_products = []
                try:
                    from services.binance_service import binance_service
                    from datetime import datetime, timedelta
                    all_products = binance_service.get_dual_investment_products()
                    # Filter products for this symbol and within 2 days
                    asset = symbol.upper().replace('USDT', '')
                    now = datetime.now()
                    two_days_later = now + timedelta(days=2)
                    
                    dual_products = []
                    for p in all_products:
                        if p.get('asset') != asset:
                            continue
                        # Check settlement date
                        settlement_date = p.get('settlement_date')
                        if isinstance(settlement_date, str):
                            try:
                                settlement_date = datetime.fromisoformat(settlement_date.replace('Z', '+00:00'))
                            except:
                                continue
                        if settlement_date and settlement_date <= two_days_later:
                            dual_products.append(p)
                    
                    logger.info(f"Found {len(dual_products)} dual investment products for {asset} within 2 days")
                except Exception as e:
                    logger.warning(f"Failed to get dual products for AI analysis: {e}")
                
                logger.info(f"Generating AI analysis for {symbol} (force_refresh={force_refresh})")
                ai_analysis = await ai_analysis_service.analyze_market_with_ai(
                    symbol=symbol.upper(),
                    market_data=market_analysis,
                    kline_data={'has_data': has_kline_data} if has_kline_data else None,
                    dual_products=dual_products,  # Pass dual products to AI
                    include_oi=False,  # OI data not yet available
                    force_refresh=force_refresh
                )
                
                if ai_analysis.get('enabled') and not ai_analysis.get('error'):
                    logger.info(f"AI analysis generated successfully for {symbol}")
                    
                    # Update support/resistance with AI analysis if available
                    if ai_analysis.get('support_resistance'):
                        ai_sr = ai_analysis['support_resistance']
                        if ai_sr.get('key_support'):
                            report_data['technical_analysis']['support_resistance']['support'] = ai_sr['key_support']
                        if ai_sr.get('key_resistance'):
                            report_data['technical_analysis']['support_resistance']['resistance'] = ai_sr['key_resistance']
                        # Add all levels for detailed display
                        report_data['technical_analysis']['support_resistance']['support_levels'] = ai_sr.get('support_levels', [])
                        report_data['technical_analysis']['support_resistance']['resistance_levels'] = ai_sr.get('resistance_levels', [])
                    
                    # Update 24h prediction with AI analysis
                    if ai_analysis.get('prediction_24h'):
                        ai_pred = ai_analysis['prediction_24h']
                        report_data['prediction']['24h'].update(ai_pred)
                    
                    # Enhance summary with AI insights
                    if ai_analysis.get('market_overview'):
                        summary += f"\n\n## AI Market Insights\n{ai_analysis['market_overview']}"
                    if ai_analysis.get('key_insights'):
                        summary += f"\n\n### Key AI Insights\n"
                        for insight in ai_analysis['key_insights'][:3]:
                            summary += f"• {insight}\n"
                else:
                    logger.info(f"AI analysis not available: {ai_analysis.get('message', 'No API key')}")
                    
            except Exception as ai_error:
                logger.warning(f"Failed to generate AI analysis: {ai_error}")
                ai_analysis = {
                    'enabled': False,
                    'error': str(ai_error),
                    'message': 'AI analysis temporarily unavailable'
                }
        
        return {
            "symbol": symbol.upper(),
            "timestamp": pd.Timestamp.now().isoformat(),
            "has_kline_data": has_kline_data,
            "report": summary.strip(),
            "report_data": report_data,  # Structured data for frontend
            "market_data": market_analysis,
            "chart": chart_data,  # Added chart data with base64 image
            "ai_analysis": ai_analysis  # AI-powered insights
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