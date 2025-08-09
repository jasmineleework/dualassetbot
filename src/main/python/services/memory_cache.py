"""
Simple in-memory cache as fallback when Redis is not available
"""
import time
from typing import Any, Dict, Optional
from threading import Lock
from loguru import logger


class MemoryCache:
    """Thread-safe in-memory cache with TTL support"""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = Lock()
        logger.info("Memory cache initialized")
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired"""
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if entry['expires_at'] > time.time():
                    logger.debug(f"Memory cache hit: {key}")
                    return entry['value']
                else:
                    # Expired, remove it
                    del self._cache[key]
                    logger.debug(f"Memory cache expired: {key}")
        return None
    
    def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set value in cache with TTL"""
        with self._lock:
            self._cache[key] = {
                'value': value,
                'expires_at': time.time() + ttl
            }
            logger.debug(f"Memory cached {key} with TTL {ttl}s")
            return True
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
        return False
    
    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        deleted = 0
        with self._lock:
            # Convert pattern to simple prefix match
            prefix = pattern.replace('*', '')
            keys_to_delete = [k for k in self._cache.keys() if k.startswith(prefix)]
            for key in keys_to_delete:
                del self._cache[key]
                deleted += 1
        return deleted
    
    def clear(self):
        """Clear all cache entries"""
        with self._lock:
            self._cache.clear()
    
    def cleanup_expired(self):
        """Remove expired entries"""
        with self._lock:
            current_time = time.time()
            expired_keys = [
                k for k, v in self._cache.items() 
                if v['expires_at'] <= current_time
            ]
            for key in expired_keys:
                del self._cache[key]
            if expired_keys:
                logger.debug(f"Cleaned up {len(expired_keys)} expired entries")
    
    def stats(self) -> Dict:
        """Get cache statistics"""
        with self._lock:
            self.cleanup_expired()  # Clean up first
            return {
                'total_keys': len(self._cache),
                'cache_type': 'memory'
            }


# Singleton instance
memory_cache = MemoryCache()