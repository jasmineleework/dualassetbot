"""
Analysis-related Celery tasks
"""
from celery_app import celery_app
from core.dual_investment_engine import dual_investment_engine
from services.binance_service import binance_service
from services.market_analysis import market_analyzer
from dao.market_data import MarketDataDAO
from dao.strategy_log import StrategyLogDAO
from models.market_data import MarketData
from core.database import get_db
from loguru import logger
from typing import List, Dict, Any
from datetime import datetime, timedelta
import time

@celery_app.task(bind=True)
def update_market_data(self, symbols: List[str] = None):
    """
    Update market data for specified symbols
    """
    task_id = self.request.id
    symbols = symbols or ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'DOTUSDT']
    
    logger.info(f"Task {task_id}: Updating market data for {len(symbols)} symbols")
    
    try:
        db = next(get_db())
        market_dao = MarketDataDAO(db)
        updated_count = 0
        
        for symbol in symbols:
            try:
                # Get latest market data from Binance
                price_data = binance_service.get_symbol_price(symbol)
                klines = binance_service.get_klines(symbol, '1h', 100)  # Last 100 hours
                
                if price_data and klines:
                    # Create market data record
                    market_data = MarketData(
                        symbol=symbol,
                        price=float(price_data['price']),
                        volume_24h=float(klines[-1]['volume']),  # Last hour volume
                        price_change_24h=float(price_data.get('priceChangePercent', 0)),
                        high_24h=float(klines[-1]['high']),
                        low_24h=float(klines[-1]['low']),
                        timestamp=datetime.utcnow(),
                        raw_data={
                            'klines': klines[-10:],  # Last 10 hours
                            'ticker': price_data
                        }
                    )
                    
                    # Save to database
                    market_dao.create(market_data)
                    updated_count += 1
                    
                    logger.debug(f"Updated market data for {symbol}: ${price_data['price']}")
                    
                # Rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Failed to update market data for {symbol}: {e}")
                continue
        
        logger.success(f"Updated market data for {updated_count}/{len(symbols)} symbols")
        
        return {
            'status': 'success',
            'symbols_updated': updated_count,
            'total_symbols': len(symbols),
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Task {task_id} failed: {e}")
        raise e
    finally:
        db.close()

@celery_app.task(bind=True)
def generate_ai_recommendations(self, symbols: List[str] = None):
    """
    Generate AI recommendations for specified symbols
    """
    task_id = self.request.id
    symbols = symbols or ['BTCUSDT', 'ETHUSDT']
    
    logger.info(f"Task {task_id}: Generating AI recommendations for {len(symbols)} symbols")
    
    try:
        db = next(get_db())
        strategy_log_dao = StrategyLogDAO(db)
        all_recommendations = []
        
        for symbol in symbols:
            try:
                # Generate AI recommendations
                recommendations = dual_investment_engine.get_ai_recommendations(symbol, limit=5)
                
                # Log the analysis
                for rec in recommendations:
                    strategy_log_dao.log_analysis(
                        strategy_name="AI_Recommendation",
                        symbol=symbol,
                        product_id=rec['product_id'],
                        ai_score=rec['ai_score'],
                        decision_made=rec['should_invest'],
                        expected_return=rec['expected_return'],
                        risk_score=rec['risk_score'],
                        reasons=rec['reasons'],
                        warnings=rec['warnings']
                    )
                
                all_recommendations.extend(recommendations)
                logger.info(f"Generated {len(recommendations)} recommendations for {symbol}")
                
                # Rate limiting
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Failed to generate recommendations for {symbol}: {e}")
                continue
        
        # Filter high-quality recommendations
        high_quality_recs = [
            rec for rec in all_recommendations 
            if rec['should_invest'] and rec['ai_score'] >= 0.65
        ]
        
        logger.success(f"Generated {len(all_recommendations)} total recommendations, {len(high_quality_recs)} high-quality")
        
        return {
            'status': 'success',
            'total_recommendations': len(all_recommendations),
            'high_quality_recommendations': len(high_quality_recs),
            'symbols_processed': symbols,
            'timestamp': datetime.utcnow().isoformat(),
            'recommendations_summary': [
                {
                    'symbol': rec['product_id'].split('-')[0],
                    'product_id': rec['product_id'],
                    'ai_score': rec['ai_score'],
                    'should_invest': rec['should_invest'],
                    'amount': rec['amount']
                }
                for rec in high_quality_recs[:10]  # Top 10
            ]
        }
        
    except Exception as e:
        logger.error(f"Task {task_id} failed: {e}")
        raise e
    finally:
        db.close()

@celery_app.task(bind=True)
def analyze_market_trends(self, symbol: str, timeframe: str = '1h', lookback_hours: int = 24):
    """
    Perform detailed market trend analysis for a symbol
    """
    task_id = self.request.id
    logger.info(f"Task {task_id}: Analyzing market trends for {symbol}")
    
    try:
        # Get historical data
        klines = binance_service.get_klines(symbol, timeframe, lookback_hours * 2)
        
        if not klines:
            raise Exception(f"No market data available for {symbol}")
        
        # Perform technical analysis
        analysis_result = market_analyzer.analyze_trends(klines)
        
        # Save analysis to database
        db = next(get_db())
        strategy_log_dao = StrategyLogDAO(db)
        
        strategy_log_dao.log_analysis(
            strategy_name="TechnicalAnalysis",
            symbol=symbol,
            market_trend=analysis_result['trend']['direction'],
            technical_indicators=analysis_result['indicators'],
            predicted_price=analysis_result.get('predicted_price'),
            predicted_probability=analysis_result.get('confidence', 0.0),
            detailed_analysis=analysis_result
        )
        
        logger.success(f"Market trend analysis completed for {symbol}")
        
        return {
            'status': 'success',
            'symbol': symbol,
            'analysis': analysis_result,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Task {task_id} failed: {e}")
        raise e
    finally:
        if 'db' in locals():
            db.close()

@celery_app.task(bind=True)
def batch_market_analysis(self, symbols: List[str] = None):
    """
    Perform batch market analysis for multiple symbols
    """
    task_id = self.request.id
    symbols = symbols or ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT']
    
    logger.info(f"Task {task_id}: Batch analyzing {len(symbols)} symbols")
    
    results = []
    
    for symbol in symbols:
        try:
            # Queue individual analysis
            analysis_task = analyze_market_trends.delay(symbol)
            
            results.append({
                'symbol': symbol,
                'task_id': analysis_task.id,
                'status': 'queued'
            })
            
            # Rate limiting
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"Failed to queue analysis for {symbol}: {e}")
            results.append({
                'symbol': symbol,
                'status': 'failed',
                'error': str(e)
            })
    
    return {
        'status': 'success',
        'total_symbols': len(symbols),
        'results': results,
        'timestamp': datetime.utcnow().isoformat()
    }

@celery_app.task(bind=True)
def cleanup_old_market_data(self, days_to_keep: int = 30):
    """
    Clean up old market data older than specified days
    """
    task_id = self.request.id
    logger.info(f"Task {task_id}: Cleaning up market data older than {days_to_keep} days")
    
    try:
        db = next(get_db())
        market_dao = MarketDataDAO(db)
        
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        deleted_count = market_dao.delete_old_records(cutoff_date)
        
        logger.success(f"Deleted {deleted_count} old market data records")
        
        return {
            'status': 'success',
            'deleted_count': deleted_count,
            'cutoff_date': cutoff_date.isoformat(),
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Task {task_id} failed: {e}")
        raise e
    finally:
        db.close()