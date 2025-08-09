"""
Celery task for updating dual investment products in background
"""
from celery import shared_task
from typing import Dict, List, Any
from datetime import datetime
from loguru import logger
from services.binance_service import binance_service
from services.cache_service import cache_service


@shared_task(name='update_dual_investment_products')
def update_dual_investment_products() -> Dict[str, Any]:
    """
    Background task to fetch and cache dual investment products
    Runs every 5 minutes to keep data fresh
    """
    logger.info("Starting dual investment products update task")
    
    results = {
        'success': True,
        'updated_at': datetime.now().isoformat(),
        'products_by_symbol': {},
        'total_products': 0,
        'errors': []
    }
    
    # Define symbols to update
    symbols = ['BTC', 'ETH', 'BNB']
    max_days_options = [1, 2, 7]  # Cache for different day ranges
    
    try:
        # Clear old cache first
        cache_service.invalidate_products()
        
        for symbol in symbols:
            for max_days in max_days_options:
                try:
                    logger.info(f"Fetching products for {symbol} (max {max_days} days)")
                    
                    # Force fetch from API (bypass cache)
                    # First clear cache for this specific query
                    cache_key = f"dual_products:{symbol}:{max_days}"
                    cache_service.delete(cache_key)
                    
                    # Now fetch fresh data (will be cached automatically)
                    products = binance_service.get_dual_investment_products(
                        symbol=symbol,
                        max_days=max_days
                    )
                    
                    key = f"{symbol}_{max_days}d"
                    results['products_by_symbol'][key] = len(products)
                    results['total_products'] += len(products)
                    
                    logger.info(f"Cached {len(products)} products for {symbol} (≤{max_days} days)")
                    
                except Exception as e:
                    error_msg = f"Failed to update {symbol} (≤{max_days} days): {str(e)}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
                    results['success'] = False
        
        # Also update products for "all" symbols
        for max_days in max_days_options:
            try:
                cache_key = f"dual_products:all:{max_days}"
                cache_service.delete(cache_key)
                
                products = binance_service.get_dual_investment_products(
                    symbol=None,
                    max_days=max_days
                )
                
                key = f"all_{max_days}d"
                results['products_by_symbol'][key] = len(products)
                
                logger.info(f"Cached {len(products)} products for all symbols (≤{max_days} days)")
                
            except Exception as e:
                error_msg = f"Failed to update all symbols (≤{max_days} days): {str(e)}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
        
        logger.info(f"Products update completed. Total cached: {results['total_products']}")
        
    except Exception as e:
        logger.error(f"Critical error in products update task: {e}")
        results['success'] = False
        results['errors'].append(str(e))
    
    return results


@shared_task(name='warmup_cache')
def warmup_cache() -> Dict[str, Any]:
    """
    Warmup cache on startup - fetch essential data
    """
    logger.info("Starting cache warmup")
    
    results = {
        'success': True,
        'warmed_up': [],
        'errors': []
    }
    
    # Warmup product data for common queries
    common_queries = [
        ('BTC', 2),
        ('ETH', 2),
        ('BNB', 2),
        (None, 2)  # All symbols, 2 days
    ]
    
    for symbol, max_days in common_queries:
        try:
            products = binance_service.get_dual_investment_products(
                symbol=symbol,
                max_days=max_days
            )
            results['warmed_up'].append({
                'symbol': symbol or 'all',
                'max_days': max_days,
                'products': len(products)
            })
            logger.info(f"Warmed up cache for {symbol or 'all'} (≤{max_days} days): {len(products)} products")
        except Exception as e:
            error_msg = f"Failed to warmup {symbol or 'all'}: {str(e)}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
            results['success'] = False
    
    # Warmup price data
    price_symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
    for symbol in price_symbols:
        try:
            price = binance_service.get_symbol_price(symbol)
            results['warmed_up'].append({
                'type': 'price',
                'symbol': symbol,
                'price': price
            })
        except Exception as e:
            logger.error(f"Failed to warmup price for {symbol}: {e}")
    
    logger.info(f"Cache warmup completed: {len(results['warmed_up'])} items cached")
    return results


@shared_task(name='invalidate_product_cache')
def invalidate_product_cache() -> Dict[str, Any]:
    """
    Manually invalidate product cache
    Used when refresh is triggered from UI
    """
    try:
        deleted = cache_service.invalidate_products()
        logger.info(f"Invalidated {deleted} product cache entries")
        
        # Trigger immediate update
        update_result = update_dual_investment_products()
        
        return {
            'success': True,
            'deleted_entries': deleted,
            'update_result': update_result
        }
    except Exception as e:
        logger.error(f"Failed to invalidate cache: {e}")
        return {
            'success': False,
            'error': str(e)
        }