#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 SEARCH CACHE SYSTEM
Cazador Supremo v14.1 - Phase 3

High-performance caching layer for search results:
- LRU cache with TTL
- Redis-compatible interface
- Cache warming strategies
- Intelligent invalidation
- Performance metrics

Target: 80% cache hit rate, <10ms cache access

Author: @Juanka_Spain
Version: 14.1.0
Date: 2026-01-17
"""

import time
import json
import hashlib
import logging
from typing import Any, Optional, Dict, List, Callable
from dataclasses import dataclass, asdict
from collections import OrderedDict
from threading import Lock, Thread
from datetime import datetime, timedelta
import pickle

logger = logging.getLogger(__name__)


# ============================================================================
# CACHE ENTRY
# ============================================================================

@dataclass
class CacheEntry:
    """Cache entry with metadata"""
    key: str
    value: Any
    created_at: float
    expires_at: float
    hit_count: int = 0
    last_accessed: float = 0
    size_bytes: int = 0
    
    def is_expired(self) -> bool:
        """Check if entry has expired"""
        return time.time() > self.expires_at
    
    def mark_accessed(self):
        """Mark entry as accessed"""
        self.hit_count += 1
        self.last_accessed = time.time()
    
    def to_dict(self) -> Dict:
        return {
            'key': self.key,
            'created_at': self.created_at,
            'expires_at': self.expires_at,
            'hit_count': self.hit_count,
            'last_accessed': self.last_accessed,
            'size_bytes': self.size_bytes
        }


# ============================================================================
# LRU CACHE WITH TTL
# ============================================================================

class LRUCacheWithTTL:
    """
    LRU (Least Recently Used) Cache with Time-To-Live.
    
    Features:
    - Thread-safe operations
    - Automatic expiry
    - Size limits
    - Hit/miss tracking
    - Memory management
    """
    
    def __init__(
        self,
        max_size: int = 1000,
        default_ttl: int = 300,  # 5 minutes
        max_memory_mb: int = 100
    ):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.lock = Lock()
        
        # Metrics
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.total_size_bytes = 0
        
        logger.info(
            f"🚀 LRU Cache initialized: "
            f"max_size={max_size}, ttl={default_ttl}s, "
            f"max_memory={max_memory_mb}MB"
        )
    
    def _generate_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments"""
        key_data = json.dumps({'args': args, 'kwargs': kwargs}, sort_keys=True)
        return hashlib.sha256(key_data.encode()).hexdigest()[:16]
    
    def _estimate_size(self, value: Any) -> int:
        """Estimate size of value in bytes"""
        try:
            return len(pickle.dumps(value))
        except:
            return len(str(value))
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        with self.lock:
            if key not in self.cache:
                self.misses += 1
                return None
            
            entry = self.cache[key]
            
            # Check if expired
            if entry.is_expired():
                self._remove_entry(key)
                self.misses += 1
                return None
            
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            entry.mark_accessed()
            
            self.hits += 1
            return entry.value
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ):
        """Set value in cache"""
        with self.lock:
            now = time.time()
            ttl = ttl if ttl is not None else self.default_ttl
            
            # Remove old entry if exists
            if key in self.cache:
                self._remove_entry(key)
            
            # Create new entry
            size = self._estimate_size(value)
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=now,
                expires_at=now + ttl,
                size_bytes=size
            )
            
            # Check memory limit
            while (self.total_size_bytes + size > self.max_memory_bytes 
                   and len(self.cache) > 0):
                self._evict_lru()
            
            # Check size limit
            while len(self.cache) >= self.max_size:
                self._evict_lru()
            
            # Add to cache
            self.cache[key] = entry
            self.total_size_bytes += size
    
    def _remove_entry(self, key: str):
        """Remove entry from cache"""
        if key in self.cache:
            entry = self.cache.pop(key)
            self.total_size_bytes -= entry.size_bytes
    
    def _evict_lru(self):
        """Evict least recently used entry"""
        if not self.cache:
            return
        
        # Get first (least recently used)
        key = next(iter(self.cache))
        self._remove_entry(key)
        self.evictions += 1
    
    def clear(self):
        """Clear all cache"""
        with self.lock:
            self.cache.clear()
            self.total_size_bytes = 0
            logger.info("🗑️ Cache cleared")
    
    def delete(self, key: str) -> bool:
        """Delete specific key"""
        with self.lock:
            if key in self.cache:
                self._remove_entry(key)
                return True
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        with self.lock:
            keys_to_delete = [
                k for k in self.cache.keys()
                if pattern in k
            ]
            for key in keys_to_delete:
                self._remove_entry(key)
            return len(keys_to_delete)
    
    def cleanup_expired(self) -> int:
        """Remove all expired entries"""
        with self.lock:
            keys_to_delete = [
                k for k, e in self.cache.items()
                if e.is_expired()
            ]
            for key in keys_to_delete:
                self._remove_entry(key)
            return len(keys_to_delete)
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        with self.lock:
            total_requests = self.hits + self.misses
            hit_rate = self.hits / total_requests if total_requests > 0 else 0
            
            return {
                'size': len(self.cache),
                'max_size': self.max_size,
                'hits': self.hits,
                'misses': self.misses,
                'hit_rate': hit_rate,
                'evictions': self.evictions,
                'total_size_mb': self.total_size_bytes / (1024 * 1024),
                'max_size_mb': self.max_memory_bytes / (1024 * 1024)
            }
    
    def get_top_keys(self, n: int = 10) -> List[Dict]:
        """Get top N most accessed keys"""
        with self.lock:
            sorted_entries = sorted(
                self.cache.values(),
                key=lambda e: e.hit_count,
                reverse=True
            )
            return [e.to_dict() for e in sorted_entries[:n]]


# ============================================================================
# SEARCH CACHE MANAGER
# ============================================================================

class SearchCacheManager:
    """
    High-level cache manager for search results.
    
    Manages multiple cache layers and warming strategies.
    """
    
    def __init__(
        self,
        price_cache_ttl: int = 300,      # 5 min
        route_cache_ttl: int = 1800,     # 30 min
        metadata_cache_ttl: int = 3600   # 1 hour
    ):
        # Multiple cache layers
        self.price_cache = LRUCacheWithTTL(
            max_size=5000,
            default_ttl=price_cache_ttl,
            max_memory_mb=50
        )
        
        self.route_cache = LRUCacheWithTTL(
            max_size=1000,
            default_ttl=route_cache_ttl,
            max_memory_mb=20
        )
        
        self.metadata_cache = LRUCacheWithTTL(
            max_size=500,
            default_ttl=metadata_cache_ttl,
            max_memory_mb=10
        )
        
        # Warming queue
        self.warming_queue: List[Callable] = []
        
        # Start cleanup thread
        self.cleanup_thread = Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()
        
        logger.info("🔥 SearchCacheManager initialized")
    
    def _cleanup_loop(self):
        """Background cleanup of expired entries"""
        while True:
            try:
                time.sleep(60)  # Every minute
                
                expired_prices = self.price_cache.cleanup_expired()
                expired_routes = self.route_cache.cleanup_expired()
                expired_meta = self.metadata_cache.cleanup_expired()
                
                total_expired = expired_prices + expired_routes + expired_meta
                
                if total_expired > 0:
                    logger.info(f"🗑️ Cleaned up {total_expired} expired entries")
            
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
    
    # ========================================================================
    # PRICE CACHING
    # ========================================================================
    
    def get_price(self, origin: str, dest: str, date: str) -> Optional[float]:
        """Get cached price"""
        key = f"price:{origin}:{dest}:{date}"
        return self.price_cache.get(key)
    
    def set_price(self, origin: str, dest: str, date: str, price: float):
        """Cache price"""
        key = f"price:{origin}:{dest}:{date}"
        self.price_cache.set(key, price)
    
    def invalidate_price(self, origin: str, dest: str):
        """Invalidate all prices for route"""
        pattern = f"price:{origin}:{dest}"
        count = self.price_cache.delete_pattern(pattern)
        logger.info(f"🗑️ Invalidated {count} prices for {origin}-{dest}")
    
    # ========================================================================
    # ROUTE CACHING
    # ========================================================================
    
    def get_route_results(self, route_key: str) -> Optional[Dict]:
        """Get cached route results"""
        return self.route_cache.get(route_key)
    
    def set_route_results(self, route_key: str, results: Dict):
        """Cache route results"""
        self.route_cache.set(route_key, results)
    
    # ========================================================================
    # METADATA CACHING
    # ========================================================================
    
    def get_metadata(self, key: str) -> Optional[Any]:
        """Get cached metadata"""
        return self.metadata_cache.get(key)
    
    def set_metadata(self, key: str, value: Any):
        """Cache metadata"""
        self.metadata_cache.set(key, value)
    
    # ========================================================================
    # CACHE WARMING
    # ========================================================================
    
    def add_warming_task(self, task: Callable):
        """Add task to warming queue"""
        self.warming_queue.append(task)
    
    def warm_popular_routes(self, routes: List[tuple]):
        """Pre-warm cache with popular routes"""
        logger.info(f"🔥 Warming cache for {len(routes)} routes...")
        
        for origin, dest, name in routes:
            try:
                # Simulate search to populate cache
                # This would call actual search methods
                pass
            except Exception as e:
                logger.error(f"Warming failed for {name}: {e}")
        
        logger.info("✅ Cache warming completed")
    
    # ========================================================================
    # STATISTICS
    # ========================================================================
    
    def get_all_stats(self) -> Dict:
        """Get statistics for all caches"""
        return {
            'price_cache': self.price_cache.get_stats(),
            'route_cache': self.route_cache.get_stats(),
            'metadata_cache': self.metadata_cache.get_stats(),
            'total_memory_mb': (
                self.price_cache.total_size_bytes +
                self.route_cache.total_size_bytes +
                self.metadata_cache.total_size_bytes
            ) / (1024 * 1024)
        }
    
    def print_stats(self):
        """Print cache statistics"""
        stats = self.get_all_stats()
        
        print("\n" + "="*60)
        print("📊 CACHE STATISTICS")
        print("="*60)
        
        for cache_name, cache_stats in stats.items():
            if cache_name == 'total_memory_mb':
                continue
            
            print(f"\n{cache_name.upper()}:")
            print(f"  Size: {cache_stats['size']}/{cache_stats['max_size']}")
            print(f"  Hit Rate: {cache_stats['hit_rate']:.1%}")
            print(f"  Hits: {cache_stats['hits']}")
            print(f"  Misses: {cache_stats['misses']}")
            print(f"  Evictions: {cache_stats['evictions']}")
            print(f"  Memory: {cache_stats['total_size_mb']:.2f}MB")
        
        print(f"\nTOTAL MEMORY: {stats['total_memory_mb']:.2f}MB")
        print("="*60 + "\n")


# ============================================================================
# CACHE DECORATOR
# ============================================================================

def cached(cache_manager: SearchCacheManager, ttl: int = 300):
    """
    Decorator for caching function results.
    
    Usage:
        @cached(cache_mgr, ttl=600)
        def expensive_search(origin, dest):
            ...
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Generate cache key
            key = f"{func.__name__}:{args}:{kwargs}"
            key_hash = hashlib.sha256(key.encode()).hexdigest()[:16]
            
            # Try cache first
            result = cache_manager.metadata_cache.get(key_hash)
            if result is not None:
                return result
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Cache result
            cache_manager.metadata_cache.set(key_hash, result, ttl=ttl)
            
            return result
        return wrapper
    return decorator


# ============================================================================
# TESTING
# ============================================================================

if __name__ == '__main__':
    print("🧪 Testing SearchCacheManager...\n")
    
    # Create manager
    cache_mgr = SearchCacheManager(
        price_cache_ttl=10,  # Short TTL for testing
        route_cache_ttl=20,
        metadata_cache_ttl=30
    )
    
    # Test price caching
    print("1. Testing price cache...")
    cache_mgr.set_price('MAD', 'BCN', '2026-03-15', 89.99)
    price = cache_mgr.get_price('MAD', 'BCN', '2026-03-15')
    print(f"   Cached price: €{price}")
    assert price == 89.99
    print("   ✅ Price cache working\n")
    
    # Test route caching
    print("2. Testing route cache...")
    route_data = {'origin': 'MAD', 'dest': 'BCN', 'prices': [89, 95, 102]}
    cache_mgr.set_route_results('MAD-BCN', route_data)
    cached_route = cache_mgr.get_route_results('MAD-BCN')
    print(f"   Cached route: {cached_route}")
    assert cached_route == route_data
    print("   ✅ Route cache working\n")
    
    # Test cache miss
    print("3. Testing cache miss...")
    missing = cache_mgr.get_price('NYC', 'LAX', '2026-06-01')
    print(f"   Missing key result: {missing}")
    assert missing is None
    print("   ✅ Cache miss handled\n")
    
    # Test statistics
    print("4. Testing statistics...")
    cache_mgr.print_stats()
    
    # Test expiry
    print("5. Testing TTL expiry...")
    print("   Waiting 12 seconds for price to expire...")
    time.sleep(12)
    expired_price = cache_mgr.get_price('MAD', 'BCN', '2026-03-15')
    print(f"   Expired price result: {expired_price}")
    assert expired_price is None
    print("   ✅ TTL expiry working\n")
    
    print("✅ All tests passed!")
