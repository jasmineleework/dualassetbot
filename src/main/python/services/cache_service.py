"""
Cache service for storing temporary data
Supports Redis and in-memory caching
"""
import json
import redis
from typing import Any, Optional
from datetime import datetime, timedelta
from loguru import logger
import hashlib
import os

class CacheService:
    """Service for caching data with Redis or memory fallback"""
    
    def __init__(self):
        """Initialize cache service"""
        self.redis_client = None
        self.memory_cache = {}
        self.cache_timestamps = {}
        
        # Try to connect to Redis
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            self.redis_client.ping()
            self.use_redis = True
            logger.info("Cache service initialized with Redis")
        except Exception as e:
            logger.warning(f"Redis not available, using memory cache: {e}")
            self.use_redis = False
    
    def _get_key(self, key: str) -> str:
        """Generate a namespaced cache key"""
        return f"dualasset:{key}"
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            cache_key = self._get_key(key)
            
            if self.use_redis:
                value = self.redis_client.get(cache_key)
                if value:
                    return json.loads(value)
            else:
                # Check memory cache
                if cache_key in self.memory_cache:
                    # Check if expired
                    if cache_key in self.cache_timestamps:
                        timestamp = self.cache_timestamps[cache_key]
                        if datetime.now() > timestamp:
                            # Expired, remove from cache
                            del self.memory_cache[cache_key]
                            del self.cache_timestamps[cache_key]
                            return None
                    return self.memory_cache[cache_key]
            
            return None
            
        except Exception as e:
            logger.error(f"Cache get error for {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache with TTL in seconds"""
        try:
            cache_key = self._get_key(key)
            json_value = json.dumps(value)
            
            if self.use_redis:
                self.redis_client.setex(cache_key, ttl, json_value)
            else:
                # Store in memory cache
                self.memory_cache[cache_key] = value
                self.cache_timestamps[cache_key] = datetime.now() + timedelta(seconds=ttl)
                
                # Clean up old entries (keep max 100 entries)
                if len(self.memory_cache) > 100:
                    self._cleanup_memory_cache()
            
            return True
            
        except Exception as e:
            logger.error(f"Cache set error for {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache"""
        try:
            cache_key = self._get_key(key)
            
            if self.use_redis:
                self.redis_client.delete(cache_key)
            else:
                if cache_key in self.memory_cache:
                    del self.memory_cache[cache_key]
                if cache_key in self.cache_timestamps:
                    del self.cache_timestamps[cache_key]
            
            return True
            
        except Exception as e:
            logger.error(f"Cache delete error for {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        try:
            cache_key = self._get_key(key)
            
            if self.use_redis:
                return bool(self.redis_client.exists(cache_key))
            else:
                if cache_key in self.memory_cache:
                    # Check if expired
                    if cache_key in self.cache_timestamps:
                        timestamp = self.cache_timestamps[cache_key]
                        if datetime.now() > timestamp:
                            return False
                    return True
                return False
                
        except Exception as e:
            logger.error(f"Cache exists error for {key}: {e}")
            return False
    
    def _cleanup_memory_cache(self):
        """Clean up expired entries from memory cache"""
        now = datetime.now()
        expired_keys = []
        
        for key, timestamp in self.cache_timestamps.items():
            if now > timestamp:
                expired_keys.append(key)
        
        for key in expired_keys:
            if key in self.memory_cache:
                del self.memory_cache[key]
            del self.cache_timestamps[key]
        
        # If still too many, remove oldest entries
        if len(self.memory_cache) > 80:
            sorted_keys = sorted(self.cache_timestamps.items(), key=lambda x: x[1])
            keys_to_remove = [k for k, _ in sorted_keys[:20]]
            
            for key in keys_to_remove:
                if key in self.memory_cache:
                    del self.memory_cache[key]
                if key in self.cache_timestamps:
                    del self.cache_timestamps[key]
    
    async def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching a pattern"""
        try:
            count = 0
            
            if self.use_redis:
                pattern_key = self._get_key(pattern)
                keys = self.redis_client.keys(pattern_key)
                if keys:
                    count = self.redis_client.delete(*keys)
            else:
                # Clear from memory cache
                keys_to_delete = [k for k in self.memory_cache.keys() if pattern in k]
                for key in keys_to_delete:
                    del self.memory_cache[key]
                    if key in self.cache_timestamps:
                        del self.cache_timestamps[key]
                    count += 1
            
            return count
            
        except Exception as e:
            logger.error(f"Cache clear pattern error for {pattern}: {e}")
            return 0
    
    def get_cache_info(self) -> dict:
        """Get cache statistics"""
        info = {
            'type': 'redis' if self.use_redis else 'memory',
            'connected': self.use_redis
        }
        
        if self.use_redis:
            try:
                redis_info = self.redis_client.info()
                info['used_memory'] = redis_info.get('used_memory_human', 'N/A')
                info['total_keys'] = self.redis_client.dbsize()
            except:
                pass
        else:
            info['total_keys'] = len(self.memory_cache)
            info['expired_keys'] = sum(1 for k, t in self.cache_timestamps.items() 
                                      if datetime.now() > t)
        
        return info

# Create singleton instance
cache_service = CacheService()