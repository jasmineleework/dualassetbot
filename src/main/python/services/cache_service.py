"""
Redis Cache Service for Dual Asset Bot
Provides caching layer to improve performance and reduce API calls
"""
import json
import redis
from typing import Any, Optional, Dict, List
from datetime import timedelta
from loguru import logger
from core.config import settings


class CacheService:
    """Service for managing Redis cache"""
    
    def __init__(self):
        """Initialize Redis connection"""
        self.redis_client = None
        self.default_ttl = 300  # 5 minutes default TTL
        self.price_ttl = 10  # 10 seconds for price data
        self.product_ttl = 300  # 5 minutes for product data
        self._initialize_redis()
    
    def _initialize_redis(self):
        """Initialize Redis client"""
        try:
            # Parse Redis URL from settings
            redis_url = settings.redis_url
            self.redis_client = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            self.redis_client.ping()
            logger.info("Redis cache service initialized successfully")
        except Exception as e:
            logger.warning(f"Redis not available, cache disabled: {e}")
            self.redis_client = None
    
    def is_available(self) -> bool:
        """Check if Redis is available"""
        if not self.redis_client:
            return False
        try:
            self.redis_client.ping()
            return True
        except:
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        if not self.is_available():
            return None
        
        try:
            value = self.redis_client.get(key)
            if value:
                # Try to parse as JSON
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
            return None
        except Exception as e:
            logger.debug(f"Cache get error for key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_available():
            return False
        
        try:
            # Serialize complex objects to JSON
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            
            ttl = ttl or self.default_ttl
            self.redis_client.setex(key, ttl, value)
            logger.debug(f"Cached {key} with TTL {ttl}s")
            return True
        except Exception as e:
            logger.debug(f"Cache set error for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete key from cache
        
        Args:
            key: Cache key
            
        Returns:
            True if deleted, False otherwise
        """
        if not self.is_available():
            return False
        
        try:
            result = self.redis_client.delete(key)
            return result > 0
        except Exception as e:
            logger.debug(f"Cache delete error for key {key}: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching pattern
        
        Args:
            pattern: Key pattern (e.g., "products:*")
            
        Returns:
            Number of keys deleted
        """
        if not self.is_available():
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.debug(f"Cache delete pattern error for {pattern}: {e}")
            return 0
    
    # Specific cache methods for different data types
    
    def get_dual_products(self, symbol: Optional[str] = None, max_days: int = 2) -> Optional[List[Dict]]:
        """
        Get cached dual investment products
        
        Args:
            symbol: Optional symbol filter
            max_days: Maximum days to settlement
            
        Returns:
            Cached products or None
        """
        cache_key = f"dual_products:{symbol or 'all'}:{max_days}"
        return self.get(cache_key)
    
    def set_dual_products(self, products: List[Dict], symbol: Optional[str] = None, max_days: int = 2) -> bool:
        """
        Cache dual investment products
        
        Args:
            products: Product list to cache
            symbol: Optional symbol filter
            max_days: Maximum days to settlement
            
        Returns:
            True if cached successfully
        """
        cache_key = f"dual_products:{symbol or 'all'}:{max_days}"
        return self.set(cache_key, products, self.product_ttl)
    
    def get_symbol_price(self, symbol: str) -> Optional[float]:
        """
        Get cached symbol price
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Cached price or None
        """
        cache_key = f"price:{symbol}"
        return self.get(cache_key)
    
    def set_symbol_price(self, symbol: str, price: float) -> bool:
        """
        Cache symbol price
        
        Args:
            symbol: Trading symbol
            price: Current price
            
        Returns:
            True if cached successfully
        """
        cache_key = f"price:{symbol}"
        return self.set(cache_key, price, self.price_ttl)
    
    def get_market_stats(self, symbol: str) -> Optional[Dict]:
        """
        Get cached 24hr market statistics
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Cached stats or None
        """
        cache_key = f"market_stats:{symbol}"
        return self.get(cache_key)
    
    def set_market_stats(self, symbol: str, stats: Dict) -> bool:
        """
        Cache 24hr market statistics
        
        Args:
            symbol: Trading symbol
            stats: Market statistics
            
        Returns:
            True if cached successfully
        """
        cache_key = f"market_stats:{symbol}"
        return self.set(cache_key, stats, 60)  # 1 minute TTL for market stats
    
    def invalidate_products(self):
        """Invalidate all product caches"""
        deleted = self.delete_pattern("dual_products:*")
        logger.info(f"Invalidated {deleted} product cache entries")
        return deleted
    
    def invalidate_prices(self):
        """Invalidate all price caches"""
        deleted = self.delete_pattern("price:*")
        logger.info(f"Invalidated {deleted} price cache entries")
        return deleted
    
    def get_cache_stats(self) -> Dict:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache stats
        """
        if not self.is_available():
            return {"available": False}
        
        try:
            info = self.redis_client.info()
            return {
                "available": True,
                "used_memory_human": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "total_keys": self.redis_client.dbsize(),
                "product_keys": len(self.redis_client.keys("dual_products:*")),
                "price_keys": len(self.redis_client.keys("price:*")),
            }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"available": False, "error": str(e)}


# Create singleton instance
cache_service = CacheService()