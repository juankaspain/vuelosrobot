#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Search Cache System - Cazador Supremo v14.0 Phase 3

Intelligent caching layer for advanced search methods:
- LRU Cache with TTL (Time To Live)
- Redis adapter (optional, falls back to local)
- Cache invalidation strategies
- Performance monitoring
- Hit/miss rate tracking

Author: @Juanka_Spain
Version: 14.0.3
Date: 2026-01-17
"""

import json
import time
import hashlib
import logging
from typing import Optional, Dict, Any, Callable
from collections import OrderedDict
from datetime import datetime, timedelta
from functools import wraps
import threading

# Optional Redis support
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)


# ============================================================================
# LRU CACHE WITH TTL
# ============================================================================

class LRUCacheWithTTL:
    """
    Thread-safe LRU cache with Time-To-Live support
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        """
        Args:
            max_size: Maximum number of items in cache
            default_ttl: Default time-to-live in seconds
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: OrderedDict = OrderedDict()
        self.ttl_map: Dict[str, float] = {}  # key -> expiry timestamp
        self.lock = threading.RLock()
        
        # Metrics
        self.hits = 0
        self.misses = 0
        self.evictions = 0
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if exists and not expired"""
        with self.lock:
            # Check if key exists
            if key not in self.cache:
                self.misses += 1
                return None
            
            # Check if expired
            if self._is_expired(key):
                self._remove(key)
                self.misses += 1
                return None
            
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            self.hits += 1
            return self.cache[key]
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in cache with optional custom TTL"""
        with self.lock:
            # Remove if already exists
            if key in self.cache:
                del self.cache[key]
            
            # Add new item
            self.cache[key] = value
            self.cache.move_to_end(key)
            
            # Set expiry
            ttl_seconds = ttl if ttl is not None else self.default_ttl
            self.ttl_map[key] = time.time() + ttl_seconds
            
            # Evict if over capacity
            if len(self.cache) > self.max_size:
                oldest_key = next(iter(self.cache))
                self._remove(oldest_key)
                self.evictions += 1
    
    def delete(self, key: str) -> bool:
        """Delete specific key from cache"""
        with self.lock:
            if key in self.cache:
                self._remove(key)
                return True
            return False
    
    def clear(self):
        """Clear entire cache"""
        with self.lock:
            self.cache.clear()
            self.ttl_map.clear()
            logger.info("Cache cleared")
    
    def _is_expired(self, key: str) -> bool:
        """Check if key has expired"""
        if key not in self.ttl_map:
            return True
        return time.time() > self.ttl_map[key]
    
    def _remove(self, key: str):
        """Remove key from cache and TTL map"""
        if key in self.cache:
            del self.cache[key]
        if key in self.ttl_map:
            del self.ttl_map[key]
    
    def cleanup_expired(self):
        """Remove all expired entries"""
        with self.lock:
            expired_keys = [
                key for key in self.cache
                if self._is_expired(key)
            ]
            for key in expired_keys:
                self._remove(key)
            
            if expired_keys:
                logger.info(f"Cleaned up {len(expired_keys)} expired entries")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.lock:
            total_requests = self.hits + self.misses
            hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
            
            return {
                'size': len(self.cache),
                'max_size': self.max_size,
                'hits': self.hits,
                'misses': self.misses,
                'evictions': self.evictions,
                'hit_rate': f"{hit_rate:.1f}%",
                'usage': f"{len(self.cache) / self.max_size * 100:.1f}%"
            }


# ============================================================================
# REDIS CACHE ADAPTER
# ============================================================================

class RedisCacheAdapter:
    """
    Redis-based cache adapter (optional)
    Falls back to LRU cache if Redis unavailable
    """
    
    def __init__(self, host: str = 'localhost', port: int = 6379, 
                 db: int = 0, password: Optional[str] = None,
                 default_ttl: int = 300):
        self.default_ttl = default_ttl
        self.redis_client = None
        self.fallback_cache = LRUCacheWithTTL(default_ttl=default_ttl)
        
        if REDIS_AVAILABLE:
            try:
                self.redis_client = redis.Redis(
                    host=host,
                    port=port,
                    db=db,
                    password=password,
                    decode_responses=True,
                    socket_timeout=2
                )
                # Test connection
                self.redis_client.ping()
                logger.info("Redis cache connected")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}. Using fallback cache.")
                self.redis_client = None
        else:
            logger.warning("Redis not available. Using fallback cache.")
    
    def get(self, key: str) -> Optional[Any]:
        """Get from Redis or fallback"""
        if self.redis_client:
            try:
                value = self.redis_client.get(key)
                if value:
                    return json.loads(value)
                return None
            except Exception as e:
                logger.error(f"Redis get error: {e}")
        
        return self.fallback_cache.get(key)
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set in Redis or fallback"""
        ttl_seconds = ttl if ttl is not None else self.default_ttl
        
        if self.redis_client:
            try:
                serialized = json.dumps(value)
                self.redis_client.setex(key, ttl_seconds, serialized)
                return
            except Exception as e:
                logger.error(f"Redis set error: {e}")
        
        self.fallback_cache.set(key, value, ttl_seconds)
    
    def delete(self, key: str) -> bool:
        """Delete from Redis or fallback"""
        if self.redis_client:
            try:
                return bool(self.redis_client.delete(key))
            except Exception as e:
                logger.error(f"Redis delete error: {e}")
        
        return self.fallback_cache.delete(key)
    
    def clear(self):
        """Clear cache"""
        if self.redis_client:
            try:
                self.redis_client.flushdb()
                return
            except Exception as e:
                logger.error(f"Redis clear error: {e}")
        
        self.fallback_cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if self.redis_client:
            try:
                info = self.redis_client.info('stats')
                return {
                    'backend': 'redis',
                    'hits': info.get('keyspace_hits', 0),
                    'misses': info.get('keyspace_misses', 0),
                    'memory_used': info.get('used_memory_human', 'N/A')
                }
            except:
                pass
        
        stats = self.fallback_cache.get_stats()
        stats['backend'] = 'local'
        return stats


# ============================================================================
# SEARCH CACHE MANAGER
# ============================================================================

class SearchCacheManager:
    """
    High-level cache manager for search operations
    """
    
    def __init__(self, use_redis: bool = False, **redis_config):
        if use_redis:
            self.cache = RedisCacheAdapter(**redis_config)
        else:
            self.cache = LRUCacheWithTTL(max_size=1000, default_ttl=300)
        
        # TTL configurations by search type
        self.ttl_config = {
            'flexible_dates': 1800,  # 30 min
            'multi_city': 900,       # 15 min
            'budget': 1800,          # 30 min
            'airline_specific': 600, # 10 min
            'nonstop_only': 900,     # 15 min
            'redeye': 1800,          # 30 min
            'nearby_airports': 3600, # 1 hour (rarely changes)
            'lastminute': 300,       # 5 min (frequently updated)
            'seasonal_trends': 86400,# 24 hours
            'group_booking': 600     # 10 min
        }
        
        # Start cleanup thread
        self._start_cleanup_thread()
    
    def _make_cache_key(self, method: str, **params) -> str:
        """Generate cache key from method and parameters"""
        # Sort parameters for consistent key
        sorted_params = sorted(params.items())
        key_string = f"{method}:" + ":".join(f"{k}={v}" for k, v in sorted_params)
        
        # Hash for shorter keys
        key_hash = hashlib.md5(key_string.encode()).hexdigest()
        return f"search:{method}:{key_hash}"
    
    def get_cached_result(self, method: str, **params) -> Optional[Any]:
        """Get cached search result"""
        key = self._make_cache_key(method, **params)
        result = self.cache.get(key)
        
        if result:
            logger.debug(f"Cache HIT: {method}")
        else:
            logger.debug(f"Cache MISS: {method}")
        
        return result
    
    def cache_result(self, method: str, result: Any, **params):
        """Cache search result with appropriate TTL"""
        key = self._make_cache_key(method, **params)
        ttl = self.ttl_config.get(method, 300)
        
        self.cache.set(key, result, ttl)
        logger.debug(f"Cached: {method} (TTL: {ttl}s)")
    
    def invalidate(self, method: Optional[str] = None, **params):
        """Invalidate cache for specific search or all"""
        if method:
            key = self._make_cache_key(method, **params)
            self.cache.delete(key)
            logger.info(f"Invalidated cache: {method}")
        else:
            self.cache.clear()
            logger.info("Invalidated all cache")
    
    def _start_cleanup_thread(self):
        """Start background cleanup thread"""
        def cleanup_loop():
            while True:
                time.sleep(300)  # Every 5 minutes
                if isinstance(self.cache, LRUCacheWithTTL):
                    self.cache.cleanup_expired()
        
        import threading
        cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
        cleanup_thread.start()
        logger.info("Cache cleanup thread started")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        return self.cache.get_stats()


# ============================================================================
# CACHE DECORATOR
# ============================================================================

def cached_search(cache_manager: SearchCacheManager):
    """Decorator to automatically cache search method results"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, **kwargs):
            method_name = self.name if hasattr(self, 'name') else func.__name__
            
            # Try to get from cache
            cached_result = cache_manager.get_cached_result(method_name, **kwargs)
            if cached_result:
                return cached_result
            
            # Execute search
            result = func(self, **kwargs)
            
            # Cache result
            cache_manager.cache_result(method_name, result, **kwargs)
            
            return result
        
        return wrapper
    return decorator


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("SEARCH CACHE SYSTEM - TESTING")
    print("=" * 70)
    
    # Test LRU Cache
    print("\n1. Testing LRU Cache with TTL...")
    cache = LRUCacheWithTTL(max_size=5, default_ttl=2)
    
    # Add items
    for i in range(5):
        cache.set(f"key{i}", f"value{i}")
        print(f"  Added key{i}")
    
    # Test hits
    print(f"\n  Get key0: {cache.get('key0')}")
    print(f"  Get key3: {cache.get('key3')}")
    
    # Test eviction
    cache.set("key5", "value5")
    print(f"\n  After adding key5, key1 evicted: {cache.get('key1')}")
    
    # Test stats
    print(f"\n  Stats: {json.dumps(cache.get_stats(), indent=2)}")
    
    # Test TTL expiration
    print("\n  Waiting 3 seconds for TTL expiration...")
    time.sleep(3)
    print(f"  Get key0 after expiry: {cache.get('key0')}")
    
    # Test SearchCacheManager
    print("\n2. Testing SearchCacheManager...")
    mgr = SearchCacheManager(use_redis=False)
    
    # Cache some results
    mgr.cache_result('flexible_dates', 
                     {'prices': [100, 200, 300]},
                     origin='MAD', destination='BCN', month='2026-03')
    
    # Retrieve
    result = mgr.get_cached_result('flexible_dates',
                                   origin='MAD', destination='BCN', month='2026-03')
    print(f"  Retrieved: {result}")
    
    # Test invalidation
    mgr.invalidate('flexible_dates', origin='MAD', destination='BCN', month='2026-03')
    result = mgr.get_cached_result('flexible_dates',
                                   origin='MAD', destination='BCN', month='2026-03')
    print(f"  After invalidation: {result}")
    
    # Final stats
    print(f"\n3. Final Stats:")
    print(json.dumps(mgr.get_stats(), indent=2))
    
    print("\n✅ All cache tests completed!")
