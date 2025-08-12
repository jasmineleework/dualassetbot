"""
Dual Investment API endpoints
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from datetime import datetime
import json
import numpy as np
from services.binance_service import binance_service
from core.dual_investment_engine import dual_investment_engine
from services.cache_service import cache_service
from tasks.update_products import invalidate_product_cache
from loguru import logger

router = APIRouter(prefix="/api/v1/dual-investment", tags=["dual-investment"])

def convert_numpy_types(obj):
    """Convert numpy types to native Python types for JSON serialization"""
    if isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    return obj

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

@router.get("/products")
async def get_dual_investment_products(
    symbol: Optional[str] = Query(None, description="Filter by symbol (e.g., BTCUSDT, BTC)"),
    asset: Optional[str] = Query(None, description="Filter by asset (e.g., BTC, ETH)"),
    type: Optional[str] = Query(None, description="Filter by type (BUY_LOW or SELL_HIGH)"),
    max_days: int = Query(2, description="Maximum days to settlement (default 2)")
):
    """Get available dual investment products, returns empty list if unavailable"""
    try:
        # Use symbol parameter if provided, otherwise fall back to asset
        filter_symbol = symbol or asset
        products = binance_service.get_dual_investment_products(symbol=filter_symbol, max_days=max_days)
        
        # Apply type filter if specified
        if type:
            products = [p for p in products if p.get('type', '').upper() == type.upper()]
        
        # Return structured response
        return {
            "products": products,
            "total": len(products),
            "message": "暂无可用产品" if not products else None,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in get_dual_investment_products endpoint: {e}")
        # Return empty list instead of 500 error
        return {
            "products": [],
            "total": 0,
            "message": "暂时无法获取产品信息，请稍后重试",
            "timestamp": datetime.now().isoformat()
        }

@router.post("/products/refresh")
async def refresh_dual_investment_products(
    symbol: Optional[str] = Query(None, description="Filter by symbol (e.g., BTCUSDT, BTC)"),
    max_days: int = Query(2, description="Maximum days to settlement (default 2)")
):
    """Manually refresh dual investment product list - triggers background task"""
    try:
        # Invalidate cache for this specific query
        cache_key = f"dual_products:{symbol or 'all'}:{max_days}"
        cache_service.delete(cache_key)
        
        # Trigger background task to update all products
        task = invalidate_product_cache.delay()
        
        # Try to get updated products immediately (might still be from cache if task not done)
        products = binance_service.get_dual_investment_products(symbol=symbol, max_days=max_days)
        
        return {
            "success": True,
            "products": products,
            "total": len(products),
            "task_id": task.id if task else None,
            "message": "Refresh initiated. Products will be updated in background.",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to refresh products: {e}")
        return {
            "success": False,
            "products": [],
            "total": 0,
            "message": "Failed to refresh products",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

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

@router.get("/cache/stats")
async def get_cache_stats():
    """Get cache statistics"""
    try:
        stats = cache_service.get_cache_stats()
        return {
            "success": True,
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get cache stats: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@router.post("/cache/warmup")
async def warmup_cache():
    """Manually trigger cache warmup"""
    try:
        from tasks.update_products import warmup_cache as warmup_task
        task = warmup_task.delay()
        
        return {
            "success": True,
            "task_id": task.id if task else None,
            "message": "Cache warmup initiated",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to warmup cache: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@router.get("/ai-recommendations/{symbol}")
async def get_ai_recommendations(
    symbol: str,
    limit: int = Query(5, ge=1, le=20, description="Maximum number of recommendations")
):
    """Get AI-powered investment recommendations using strategy ensemble"""
    try:
        recommendations = dual_investment_engine.get_ai_recommendations(symbol.upper(), limit)
        
        # Convert numpy types to native Python types
        recommendations = convert_numpy_types(recommendations)
        
        return {
            "symbol": symbol.upper(),
            "timestamp": datetime.now().isoformat(),
            "total_recommendations": len(recommendations),
            "recommendations": recommendations
        }
        
    except Exception as e:
        logger.error(f"Failed to get AI recommendations for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/recommendations-detailed/{symbol}")
async def get_detailed_recommendations(
    symbol: str,
    limit: int = Query(5, ge=1, le=20, description="Maximum number of recommendations"),
    strategy_type: Optional[str] = Query(None, description="Filter by strategy type (BUY_LOW or SELL_HIGH)")
):
    """
    Get detailed AI-powered investment recommendations with structured product information
    
    Returns comprehensive analysis including:
    - Product details (APY, strike price, settlement date)
    - AI analysis scores and recommendations
    - Market context and trends
    - Investment decision rationale
    """
    try:
        # Get AI recommendations with product details
        recommendations = dual_investment_engine.get_ai_recommendations(symbol.upper(), limit * 2)  # Get more to filter
        
        # Convert numpy types
        recommendations = convert_numpy_types(recommendations)
        
        # Structure and enhance the recommendations
        structured_recommendations = []
        
        for rec in recommendations:
            product = rec.get('product_details', {})
            
            # Skip if strategy type filter is applied and doesn't match
            if strategy_type and product.get('type') != strategy_type:
                continue
            
            # Calculate price distance
            current_price = rec.get('market_analysis', {}).get('current_price', 0)
            strike_price = product.get('strike_price', 0)
            price_distance = 0
            if current_price and strike_price:
                price_distance = (strike_price - current_price) / current_price
            
            # Structure the recommendation
            structured_rec = {
                'product_id': rec['product_id'],
                'strategy_type': product.get('type', 'UNKNOWN'),
                
                # Product Information
                'product_info': {
                    'asset': product.get('asset', ''),
                    'currency': product.get('currency', 'USDT'),
                    'apy': f"{product.get('apy', 0) * 100:.2f}%",
                    'apy_value': product.get('apy', 0),
                    'strike_price': product.get('strike_price', 0),
                    'current_price': current_price,
                    'price_distance': f"{price_distance * 100:.2f}%",
                    'price_distance_value': price_distance,
                    'settlement_date': product.get('settlement_date', ''),
                    'term_days': product.get('term_days', 0),
                    'min_amount': product.get('min_amount', 0),
                    'max_amount': product.get('max_amount', 0),
                    'can_purchase': product.get('can_purchase', False)
                },
                
                # AI Analysis
                'ai_analysis': {
                    'ai_score': round(rec['ai_score'], 3),
                    'recommendation': rec['recommendation'],
                    'expected_return': f"{rec['expected_return'] * 100:.2f}%",
                    'expected_return_value': rec['expected_return'],
                    'exercise_probability': f"{rec.get('metadata', {}).get('exercise_probability', 0) * 100:.1f}%",
                    'risk_score': rec['risk_score'],
                    'ensemble_signal': rec.get('ensemble_signal', 'NEUTRAL')
                },
                
                # Investment Decision
                'investment_decision': {
                    'should_invest': rec['should_invest'],
                    'suggested_amount': rec['amount'],
                    'reasons': rec['reasons'],
                    'warnings': rec.get('warnings', [])
                },
                
                # Market Context
                'market_context': {
                    'trend': rec.get('market_analysis', {}).get('trend', {}).get('trend', 'NEUTRAL'),
                    'trend_strength': rec.get('market_analysis', {}).get('trend', {}).get('strength', 0),
                    'volatility': rec.get('market_analysis', {}).get('volatility', {}).get('risk_level', 'MEDIUM'),
                    'support': rec.get('market_analysis', {}).get('support_resistance', {}).get('support', 0),
                    'resistance': rec.get('market_analysis', {}).get('support_resistance', {}).get('resistance', 0),
                    'volume_trend': rec.get('market_analysis', {}).get('volume_analysis', {}).get('obv_trend', 'NEUTRAL'),
                    'price_change_24h': rec.get('market_analysis', {}).get('price_change_24h', 0)
                },
                
                # Technical Indicators Summary
                'technical_summary': {
                    'rsi_signal': rec.get('market_analysis', {}).get('signals', {}).get('rsi_signal', 'NEUTRAL'),
                    'macd_signal': rec.get('market_analysis', {}).get('signals', {}).get('macd_signal', 'NEUTRAL'),
                    'bb_signal': rec.get('market_analysis', {}).get('signals', {}).get('bb_signal', 'NEUTRAL'),
                    'overall_signal': rec.get('market_analysis', {}).get('signals', {}).get('recommendation', 'NEUTRAL')
                }
            }
            
            structured_recommendations.append(structured_rec)
            
            # Stop if we have enough recommendations
            if len(structured_recommendations) >= limit:
                break
        
        # Sort by AI score (highest first)
        structured_recommendations.sort(key=lambda x: x['ai_analysis']['ai_score'], reverse=True)
        
        # Categorize recommendations
        strong_buy = [r for r in structured_recommendations if r['ai_analysis']['recommendation'] == 'STRONG_BUY']
        buy = [r for r in structured_recommendations if r['ai_analysis']['recommendation'] == 'BUY']
        consider = [r for r in structured_recommendations if r['ai_analysis']['recommendation'] == 'CONSIDER']
        
        return {
            'symbol': symbol.upper(),
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_recommendations': len(structured_recommendations),
                'strong_buy_count': len(strong_buy),
                'buy_count': len(buy),
                'consider_count': len(consider),
                'average_ai_score': round(sum(r['ai_analysis']['ai_score'] for r in structured_recommendations) / len(structured_recommendations), 3) if structured_recommendations else 0,
                'average_apy': round(sum(r['product_info']['apy_value'] for r in structured_recommendations) / len(structured_recommendations) * 100, 2) if structured_recommendations else 0
            },
            'recommendations': structured_recommendations,
            'categories': {
                'strong_buy': strong_buy[:2],  # Top 2 strong buy
                'buy': buy[:3],  # Top 3 buy
                'consider': consider[:2]  # Top 2 consider
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get detailed recommendations for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))