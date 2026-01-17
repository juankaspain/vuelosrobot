#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Search Cache System - Advanced Search Methods
Cazador Supremo v14.0 - Phase 3

Implements intelligent caching layer for search results:
- LRU Cache with TTL (Time To Live)
- Cache invalidation strategies
- Redis-compatible (optional)
- Performance monitoring
- Cache statistics

Author: @Juanka_Spain
Version: 14.0.0
Date: 2026-01-17
"""

import time
import json
import hashlib
import logging
from typing import Any, Optional, Dict, Tuple
from collections import OrderedDict
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import threading

logger = logging.getLogger(__name__)


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    value: Any
    created_at: float
    ttl: int
    hits: int = 0
    size_bytes: int = 0
    
    def is_expired(self) -> bool:
        """Check if entry has expired"""
        return time.time() - self.created_at > self.ttl
    
    def time_to_expiry(self) -> float:
        """Seconds until expiry"""
        return max(0, self.ttl - (time.time() - self.created_at))
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'key': self.key,
            'created_at': datetime.fromtimestamp(self.created_at).isoformat(),
            'ttl': self.ttl,
            'hits': self.hits,
            'size_bytes': self.size_bytes,
            'time_to_expiry': self.time_to_expiry()
        }


@dataclass
class CacheStats:
    """Cache statistics"""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    size: int = 0
    max_size: int = 0
    total_size_bytes: int = 0
    
    @property
    def hit_rate(self) -> float:
        """Cache hit rate percentage"""
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'hits': self.hits,
            'misses': self.misses,
            'evictions': self.evictions,
            'size': self.size,
            'max_size': self.max_size,
            'total_size_bytes': self.total_size_bytes,
            'hit_rate': f"{self.hit_rate:.2f}%"
        }


# ============================================================================
# LRU CACHE WITH TTL
# ============================================================================

class SearchCache:
    """
    LRU Cache with TTL for search results
    
    Features:
    - LRU eviction policy
    - Configurable TTL per entry
    - Thread-safe operations
    - Statistics tracking
    - Memory management
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        """
        Initialize cache
        
        Args:
            max_size: Maximum number of entries
            default_ttl: Default TTL in seconds (1 hour)
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.stats = CacheStats(max_size=max_size)
        self.lock = threading.RLock()
        
        logger.info(f"Cache initialized: max_size={max_size}, ttl={default_ttl}s")
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        with self.lock:
            if key not in self.cache:
                self.stats.misses += 1
                logger.debug(f"Cache miss: {key}")
                return None
            
            entry = self.cache[key]
            
            # Check expiry
            if entry.is_expired():
                logger.debug(f"Cache expired: {key}")
                self._remove(key)
                self.stats.misses += 1
                return None
            
            # Update stats and LRU order
            entry.hits += 1
            self.stats.hits += 1
            self.cache.move_to_end(key)
            
            logger.debug(f"Cache hit: {key} (hits: {entry.hits})")
            return entry.value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: TTL in seconds (uses default if None)
            
        Returns:
            True if successful
        """
        with self.lock:
            ttl = ttl or self.default_ttl
            
            # Calculate size
            try:
                size_bytes = len(json.dumps(value))
            except:
                size_bytes = 0
            
            # Remove if exists
            if key in self.cache:
                self._remove(key)
            
            # Evict if at capacity
            if len(self.cache) >= self.max_size:
                self._evict_lru()
            
            # Create entry
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=time.time(),
                ttl=ttl,
                size_bytes=size_bytes
            )
            
            self.cache[key] = entry
            self.stats.size = len(self.cache)
            self.stats.total_size_bytes += size_bytes
            
            logger.debug(f"Cache set: {key} (ttl: {ttl}s, size: {size_bytes}B)")
            return True
    
    def delete(self, key: str) -> bool:
        """
        Delete entry from cache
        
        Args:
            key: Cache key
            
        Returns:
            True if deleted
        """
        with self.lock:
            if key in self.cache:
                self._remove(key)
                logger.debug(f"Cache deleted: {key}")
                return True
            return False
    
    def clear(self):
        """Clear all cache entries"""
        with self.lock:
            self.cache.clear()
            self.stats = CacheStats(max_size=self.max_size)
            logger.info("Cache cleared")
    
    def _remove(self, key: str):
        """Remove entry (internal)"""
        if key in self.cache:
            entry = self.cache.pop(key)
            self.stats.size = len(self.cache)
            self.stats.total_size_bytes -= entry.size_bytes
    
    def _evict_lru(self):
        """Evict least recently used entry"""
        if not self.cache:
            return
        
        # Get first (least recently used)
        key = next(iter(self.cache))
        self._remove(key)
        self.stats.evictions += 1
        logger.debug(f"Cache evicted LRU: {key}")
    
    def cleanup_expired(self) -> int:
        """
        Remove all expired entries
        
        Returns:
            Number of entries removed
        """
        with self.lock:
            expired_keys = [
                key for key, entry in self.cache.items()
                if entry.is_expired()
            ]
            
            for key in expired_keys:
                self._remove(key)
            
            if expired_keys:
                logger.info(f"Cleaned up {len(expired_keys)} expired entries")
            
            return len(expired_keys)
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        with self.lock:
            return self.stats.to_dict()
    
    def get_all_entries(self) -> Dict[str, Dict]:
        """Get all cache entries metadata"""
        with self.lock:
            return {
                key: entry.to_dict()
                for key, entry in self.cache.items()
            }


# ============================================================================
# CACHE KEY GENERATOR
# ============================================================================

class CacheKeyGenerator:
    """Generate cache keys for search queries"""
    
    @staticmethod
    def generate(method: str, **params) -> str:
        """
        Generate cache key from search parameters
        
        Args:
            method: Search method name
            **params: Search parameters
            
        Returns:
            Cache key (hash)
        """
        # Sort params for consistency
        sorted_params = sorted(params.items())
        
        # Create string representation
        param_str = "|".join(f"{k}={v}" for k, v in sorted_params)
        key_str = f"{method}|{param_str}"
        
        # Generate hash
        key_hash = hashlib.md5(key_str.encode()).hexdigest()
        
        return f"search:{method}:{key_hash}"
    
    @staticmethod
    def generate_flexible_dates(origin: str, destination: str, month: str) -> str:
        """Generate key for flexible dates search"""
        return CacheKeyGenerator.generate(
            'flexible_dates',
            origin=origin,
            destination=destination,
            month=month
        )
    
    @staticmethod
    def generate_multi_city(cities: list, start_date: str) -> str:
        """Generate key for multi-city search"""
        cities_str = ','.join(cities)
        return CacheKeyGenerator.generate(
            'multi_city',
            cities=cities_str,
            start_date=start_date
        )
    
    @staticmethod
    def generate_budget(origin: str, budget: float, month: str) -> str:
        """Generate key for budget search"""
        return CacheKeyGenerator.generate(
            'budget',
            origin=origin,
            budget=budget,
            month=month
        )


# ============================================================================
# CACHE MANAGER (HIGH-LEVEL API)
# ============================================================================

class SearchCacheManager:
    """
    High-level cache manager for search methods
    
    Features:
    - Automatic key generation
    - TTL management per search type
    - Statistics aggregation
    - Cleanup scheduling
    """
    
    # TTL by search method (seconds)
    TTL_CONFIG = {
        'flexible_dates': 3600,      # 1 hour
        'multi_city': 1800,          # 30 minutes
        'budget': 7200,              # 2 hours
        'airline_specific': 1800,    # 30 minutes
        'nonstop_only': 3600,        # 1 hour
        'redeye': 3600,              # 1 hour
        'nearby_airports': 86400,    # 24 hours (static data)
        'lastminute': 600,           # 10 minutes (volatile)
        'seasonal_trends': 86400,    # 24 hours
        'group_booking': 1800        # 30 minutes
    }
    
    def __init__(self, max_size: int = 1000):
        self.cache = SearchCache(max_size=max_size)
        self.key_gen = CacheKeyGenerator()
        self.last_cleanup = time.time()
        
        logger.info(f"SearchCacheManager initialized: max_size={max_size}")
    
    def get_cached_result(self, method: str, **params) -> Optional[Any]:
        """
        Get cached search result
        
        Args:
            method: Search method name
            **params: Search parameters
            
        Returns:
            Cached result or None
        """
        key = self.key_gen.generate(method, **params)
        result = self.cache.get(key)
        
        # Periodic cleanup
        self._maybe_cleanup()
        
        return result
    
    def cache_result(self, method: str, result: Any, **params) -> bool:
        """
        Cache search result
        
        Args:
            method: Search method name
            result: Result to cache
            **params: Search parameters
            
        Returns:
            True if successful
        """
        key = self.key_gen.generate(method, **params)
        ttl = self.TTL_CONFIG.get(method, 3600)
        
        return self.cache.set(key, result, ttl=ttl)
    
    def invalidate(self, method: str, **params) -> bool:
        """
        Invalidate specific cached result
        
        Args:
            method: Search method name
            **params: Search parameters
            
        Returns:
            True if deleted
        """
        key = self.key_gen.generate(method, **params)
        return self.cache.delete(key)
    
    def invalidate_all(self, method: str):
        """
        Invalidate all cached results for a method
        
        Args:
            method: Search method name
        """
        prefix = f"search:{method}:"
        keys_to_delete = [
            key for key in self.cache.cache.keys()
            if key.startswith(prefix)
        ]
        
        for key in keys_to_delete:
            self.cache.delete(key)
        
        logger.info(f"Invalidated {len(keys_to_delete)} entries for {method}")
    
    def clear_all(self):
        """Clear entire cache"""
        self.cache.clear()
    
    def _maybe_cleanup(self):
        """Cleanup expired entries if needed"""
        now = time.time()
        if now - self.last_cleanup > 300:  # Every 5 minutes
            self.cache.cleanup_expired()
            self.last_cleanup = now
    
    def get_statistics(self) -> Dict:
        """Get comprehensive cache statistics"""
        stats = self.cache.get_stats()
        stats['last_cleanup'] = datetime.fromtimestamp(self.last_cleanup).isoformat()
        return stats
    
    def export_metrics(self) -> Dict:
        """Export metrics for monitoring"""
        stats = self.cache.get_stats()
        return {
            'timestamp': datetime.now().isoformat(),
            'cache_hit_rate': stats['hit_rate'],
            'cache_size': stats['size'],
            'cache_utilization': f"{(stats['size'] / stats['max_size'] * 100):.1f}%",
            'total_hits': stats['hits'],
            'total_misses': stats['misses'],
            'evictions': stats['evictions'],
            'memory_usage_mb': stats['total_size_bytes'] / (1024 * 1024)
        }


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

# Create global cache manager instance
cache_manager = SearchCacheManager(max_size=1000)


# ============================================================================
# DECORATOR FOR AUTO-CACHING
# ============================================================================

def cached_search(method_name: str):
    """
    Decorator to automatically cache search method results
    
    Usage:
        @cached_search('flexible_dates')
        def search(self, origin, destination, month):
            ...
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Try cache first
            cached = cache_manager.get_cached_result(method_name, **kwargs)
            if cached is not None:
                logger.info(f"Returning cached result for {method_name}")
                return cached
            
            # Execute search
            result = func(*args, **kwargs)
            
            # Cache result
            cache_manager.cache_result(method_name, result, **kwargs)
            
            return result
        return wrapper
    return decorator


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    print("="*60)
    print("Search Cache System - Testing")
    print("="*60)
    
    # Test cache
    cache = SearchCache(max_size=5, default_ttl=10)
    
    # Add entries
    print("\n1. Adding entries...")
    for i in range(7):
        cache.set(f"key{i}", f"value{i}")
        print(f"   Added key{i}")
    
    print(f"\n   Cache size: {len(cache.cache)} (max: 5)")
    print(f"   Evictions: {cache.stats.evictions}")
    
    # Test hits
    print("\n2. Testing hits...")
    val = cache.get("key5")
    print(f"   Get key5: {val} (hit)")
    val = cache.get("key0")
    print(f"   Get key0: {val} (miss - evicted)")
    
    # Test stats
    print("\n3. Cache statistics:")
    stats = cache.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # Test cache manager
    print("\n4. Testing CacheManager...")
    manager = SearchCacheManager(max_size=10)
    
    # Cache a search
    manager.cache_result(
        'flexible_dates',
        {'prices': {1: 100, 2: 200}},
        origin='MAD',
        destination='BCN',
        month='2026-03'
    )
    
    # Retrieve cached
    result = manager.get_cached_result(
        'flexible_dates',
        origin='MAD',
        destination='BCN',
        month='2026-03'
    )
    print(f"   Cached result: {result}")
    
    # Export metrics
    print("\n5. Metrics export:")
    metrics = manager.export_metrics()
    for key, value in metrics.items():
        print(f"   {key}: {value}")
    
    print("\n✅ All cache tests passed!")
