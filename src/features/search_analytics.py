#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Search Analytics System - Cazador Supremo v14.0 Phase 3

Comprehensive analytics for advanced search methods:
- Usage tracking per method
- Conversion funnel analysis
- A/B testing framework
- Heatmap generation
- Performance metrics
- User behavior analysis

Author: @Juanka_Spain
Version: 14.0.3
Date: 2026-01-17
"""

import json
import time
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from dataclasses import dataclass, asdict
import threading
from pathlib import Path

logger = logging.getLogger(__name__)


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class SearchEvent:
    """Single search event"""
    timestamp: datetime
    user_id: int
    method: str
    params: Dict[str, Any]
    duration_ms: float
    result_count: int
    cached: bool = False
    variant: Optional[str] = None  # For A/B testing
    
    def to_dict(self) -> Dict:
        d = asdict(self)
        d['timestamp'] = self.timestamp.isoformat()
        return d

@dataclass
class ConversionEvent:
    """Conversion event (click, booking, share, etc.)"""
    timestamp: datetime
    user_id: int
    search_method: str
    action: str  # 'view_details', 'book', 'share', 'save'
    value: Optional[float] = None  # Booking value
    
    def to_dict(self) -> Dict:
        d = asdict(self)
        d['timestamp'] = self.timestamp.isoformat()
        return d


# ============================================================================
# ANALYTICS TRACKER
# ============================================================================

class SearchAnalyticsTracker:
    """
    Tracks and analyzes search usage patterns
    """
    
    def __init__(self, storage_file: str = "search_analytics.json"):
        self.storage_file = Path(storage_file)
        self.events: List[SearchEvent] = []
        self.conversions: List[ConversionEvent] = []
        self.lock = threading.RLock()
        
        # A/B test configurations
        self.ab_tests: Dict[str, Dict] = {}
        
        # Load existing data
        self._load_data()
        
        # Start auto-save thread
        self._start_autosave()
    
    def track_search(self, user_id: int, method: str, params: Dict,
                    duration_ms: float, result_count: int, 
                    cached: bool = False, variant: Optional[str] = None):
        """Track a search event"""
        event = SearchEvent(
            timestamp=datetime.now(),
            user_id=user_id,
            method=method,
            params=params,
            duration_ms=duration_ms,
            result_count=result_count,
            cached=cached,
            variant=variant
        )
        
        with self.lock:
            self.events.append(event)
        
        logger.debug(f"Tracked search: {method} by user {user_id}")
    
    def track_conversion(self, user_id: int, search_method: str, 
                        action: str, value: Optional[float] = None):
        """Track a conversion event"""
        event = ConversionEvent(
            timestamp=datetime.now(),
            user_id=user_id,
            search_method=search_method,
            action=action,
            value=value
        )
        
        with self.lock:
            self.conversions.append(event)
        
        logger.debug(f"Tracked conversion: {action} for {search_method}")
    
    # ========================================================================
    # USAGE ANALYTICS
    # ========================================================================
    
    def get_usage_by_method(self, days: int = 7) -> Dict[str, int]:
        """Get search count by method for last N days"""
        cutoff = datetime.now() - timedelta(days=days)
        
        with self.lock:
            recent_events = [e for e in self.events if e.timestamp >= cutoff]
            counts = Counter(e.method for e in recent_events)
        
        return dict(counts)
    
    def get_top_searches(self, limit: int = 10) -> List[Tuple[str, int]]:
        """Get most popular search methods"""
        usage = self.get_usage_by_method(days=30)
        return sorted(usage.items(), key=lambda x: x[1], reverse=True)[:limit]
    
    def get_user_search_frequency(self, user_id: int, days: int = 30) -> int:
        """Get search frequency for a specific user"""
        cutoff = datetime.now() - timedelta(days=days)
        
        with self.lock:
            count = sum(1 for e in self.events 
                       if e.user_id == user_id and e.timestamp >= cutoff)
        
        return count
    
    def get_power_users(self, min_searches: int = 10, days: int = 7) -> List[Tuple[int, int]]:
        """Identify power users (high search frequency)"""
        cutoff = datetime.now() - timedelta(days=days)
        
        with self.lock:
            recent_events = [e for e in self.events if e.timestamp >= cutoff]
            user_counts = Counter(e.user_id for e in recent_events)
        
        power_users = [(uid, count) for uid, count in user_counts.items() 
                      if count >= min_searches]
        
        return sorted(power_users, key=lambda x: x[1], reverse=True)
    
    # ========================================================================
    # PERFORMANCE ANALYTICS
    # ========================================================================
    
    def get_average_response_time(self, method: Optional[str] = None) -> float:
        """Get average response time in ms"""
        with self.lock:
            if method:
                durations = [e.duration_ms for e in self.events if e.method == method]
            else:
                durations = [e.duration_ms for e in self.events]
        
        return sum(durations) / len(durations) if durations else 0
    
    def get_cache_hit_rate(self, method: Optional[str] = None, days: int = 7) -> float:
        """Calculate cache hit rate"""
        cutoff = datetime.now() - timedelta(days=days)
        
        with self.lock:
            recent = [e for e in self.events if e.timestamp >= cutoff]
            
            if method:
                recent = [e for e in recent if e.method == method]
            
            if not recent:
                return 0.0
            
            cached_count = sum(1 for e in recent if e.cached)
            return (cached_count / len(recent)) * 100
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics"""
        with self.lock:
            if not self.events:
                return {}
            
            durations = [e.duration_ms for e in self.events]
            cached_count = sum(1 for e in self.events if e.cached)
            
            return {
                'total_searches': len(self.events),
                'avg_duration_ms': sum(durations) / len(durations),
                'min_duration_ms': min(durations),
                'max_duration_ms': max(durations),
                'cache_hit_rate': (cached_count / len(self.events)) * 100,
                'unique_users': len(set(e.user_id for e in self.events))
            }
    
    # ========================================================================
    # CONVERSION FUNNEL
    # ========================================================================
    
    def get_conversion_funnel(self, method: str, days: int = 30) -> Dict[str, Any]:
        """Analyze conversion funnel for a search method"""
        cutoff = datetime.now() - timedelta(days=days)
        
        with self.lock:
            # Get searches
            searches = [e for e in self.events 
                       if e.method == method and e.timestamp >= cutoff]
            
            # Get conversions
            convs = [c for c in self.conversions 
                    if c.search_method == method and c.timestamp >= cutoff]
        
        total_searches = len(searches)
        if total_searches == 0:
            return {}
        
        # Count actions
        action_counts = Counter(c.action for c in convs)
        
        # Calculate conversion rates
        funnel = {
            'searches': total_searches,
            'view_details': action_counts.get('view_details', 0),
            'book': action_counts.get('book', 0),
            'share': action_counts.get('share', 0),
            'save': action_counts.get('save', 0)
        }
        
        # Add rates
        funnel['view_rate'] = (funnel['view_details'] / total_searches) * 100
        funnel['book_rate'] = (funnel['book'] / total_searches) * 100
        funnel['share_rate'] = (funnel['share'] / total_searches) * 100
        funnel['overall_conversion'] = (
            (funnel['book'] + funnel['share']) / total_searches
        ) * 100
        
        return funnel
    
    def get_revenue_by_method(self, days: int = 30) -> Dict[str, float]:
        """Calculate revenue generated by each search method"""
        cutoff = datetime.now() - timedelta(days=days)
        
        with self.lock:
            recent_convs = [c for c in self.conversions 
                          if c.timestamp >= cutoff and c.action == 'book' and c.value]
        
        revenue_by_method = defaultdict(float)
        for conv in recent_convs:
            revenue_by_method[conv.search_method] += conv.value or 0
        
        return dict(revenue_by_method)
    
    # ========================================================================
    # A/B TESTING
    # ========================================================================
    
    def create_ab_test(self, test_name: str, method: str, 
                      variants: List[str], metric: str = 'conversion'):
        """Create a new A/B test"""
        self.ab_tests[test_name] = {
            'method': method,
            'variants': variants,
            'metric': metric,
            'created_at': datetime.now().isoformat()
        }
        logger.info(f"Created A/B test: {test_name}")
    
    def get_ab_test_results(self, test_name: str, days: int = 7) -> Dict[str, Any]:
        """Get results for an A/B test"""
        if test_name not in self.ab_tests:
            return {}
        
        test_config = self.ab_tests[test_name]
        method = test_config['method']
        variants = test_config['variants']
        cutoff = datetime.now() - timedelta(days=days)
        
        with self.lock:
            results = {}
            
            for variant in variants:
                # Get searches for this variant
                variant_searches = [
                    e for e in self.events
                    if e.method == method 
                    and e.variant == variant 
                    and e.timestamp >= cutoff
                ]
                
                # Get conversions
                variant_convs = [
                    c for c in self.conversions
                    if c.search_method == method
                    and c.timestamp >= cutoff
                ]
                
                total = len(variant_searches)
                conversions = len([c for c in variant_convs 
                                 if c.action in ['book', 'share']])
                
                results[variant] = {
                    'searches': total,
                    'conversions': conversions,
                    'conversion_rate': (conversions / total * 100) if total > 0 else 0,
                    'avg_duration': sum(e.duration_ms for e in variant_searches) / total if total > 0 else 0
                }
        
        return results
    
    # ========================================================================
    # HEATMAP GENERATION
    # ========================================================================
    
    def generate_usage_heatmap(self, days: int = 30) -> Dict[str, Dict[int, int]]:
        """Generate hourly usage heatmap by day of week"""
        cutoff = datetime.now() - timedelta(days=days)
        
        with self.lock:
            recent = [e for e in self.events if e.timestamp >= cutoff]
        
        # Initialize heatmap
        heatmap = {
            'Monday': defaultdict(int),
            'Tuesday': defaultdict(int),
            'Wednesday': defaultdict(int),
            'Thursday': defaultdict(int),
            'Friday': defaultdict(int),
            'Saturday': defaultdict(int),
            'Sunday': defaultdict(int)
        }
        
        # Fill heatmap
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        for event in recent:
            day_name = day_names[event.timestamp.weekday()]
            hour = event.timestamp.hour
            heatmap[day_name][hour] += 1
        
        # Convert to regular dict
        return {day: dict(hours) for day, hours in heatmap.items()}
    
    # ========================================================================
    # PERSISTENCE
    # ========================================================================
    
    def _load_data(self):
        """Load analytics data from file"""
        if not self.storage_file.exists():
            return
        
        try:
            with open(self.storage_file, 'r') as f:
                data = json.load(f)
            
            # Restore events
            for e_dict in data.get('events', []):
                e_dict['timestamp'] = datetime.fromisoformat(e_dict['timestamp'])
                self.events.append(SearchEvent(**e_dict))
            
            # Restore conversions
            for c_dict in data.get('conversions', []):
                c_dict['timestamp'] = datetime.fromisoformat(c_dict['timestamp'])
                self.conversions.append(ConversionEvent(**c_dict))
            
            # Restore A/B tests
            self.ab_tests = data.get('ab_tests', {})
            
            logger.info(f"Loaded {len(self.events)} events and {len(self.conversions)} conversions")
        
        except Exception as e:
            logger.error(f"Failed to load analytics data: {e}")
    
    def save_data(self):
        """Save analytics data to file"""
        with self.lock:
            data = {
                'events': [e.to_dict() for e in self.events[-10000:]],  # Keep last 10k
                'conversions': [c.to_dict() for c in self.conversions[-10000:]],
                'ab_tests': self.ab_tests,
                'saved_at': datetime.now().isoformat()
            }
        
        try:
            with open(self.storage_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.debug("Analytics data saved")
        except Exception as e:
            logger.error(f"Failed to save analytics data: {e}")
    
    def _start_autosave(self, interval: int = 300):
        """Start auto-save thread"""
        def autosave_loop():
            while True:
                time.sleep(interval)
                self.save_data()
        
        thread = threading.Thread(target=autosave_loop, daemon=True)
        thread.start()
        logger.info("Analytics auto-save started")
    
    # ========================================================================
    # DASHBOARD DATA
    # ========================================================================
    
    def get_dashboard_data(self, days: int = 7) -> Dict[str, Any]:
        """Get comprehensive dashboard data"""
        return {
            'overview': {
                'total_searches': len(self.events),
                'total_conversions': len(self.conversions),
                'unique_users': len(set(e.user_id for e in self.events)),
                'time_range': f"Last {days} days"
            },
            'usage_by_method': self.get_usage_by_method(days),
            'top_searches': dict(self.get_top_searches()),
            'performance': self.get_performance_metrics(),
            'cache_hit_rate': f"{self.get_cache_hit_rate(days=days):.1f}%",
            'revenue_by_method': self.get_revenue_by_method(days),
            'power_users_count': len(self.get_power_users(days=days))
        }


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("SEARCH ANALYTICS SYSTEM - TESTING")
    print("=" * 70)
    
    # Create tracker
    tracker = SearchAnalyticsTracker(storage_file="test_analytics.json")
    
    # Simulate searches
    print("\n1. Simulating searches...")
    methods = ['flexible_dates', 'multi_city', 'budget']
    
    for i in range(50):
        user_id = 1000 + (i % 10)
        method = methods[i % 3]
        tracker.track_search(
            user_id=user_id,
            method=method,
            params={'origin': 'MAD', 'dest': 'BCN'},
            duration_ms=50 + (i * 10),
            result_count=10,
            cached=(i % 3 == 0)
        )
    
    print(f"  Tracked {len(tracker.events)} searches")
    
    # Simulate conversions
    print("\n2. Simulating conversions...")
    for i in range(20):
        tracker.track_conversion(
            user_id=1000 + (i % 10),
            search_method=methods[i % 3],
            action='book' if i % 3 == 0 else 'share',
            value=500.0 if i % 3 == 0 else None
        )
    
    print(f"  Tracked {len(tracker.conversions)} conversions")
    
    # Get analytics
    print("\n3. Usage Analytics:")
    usage = tracker.get_usage_by_method()
    for method, count in usage.items():
        print(f"  {method}: {count} searches")
    
    print("\n4. Performance Metrics:")
    metrics = tracker.get_performance_metrics()
    for key, value in metrics.items():
        print(f"  {key}: {value}")
    
    print("\n5. Conversion Funnel (flexible_dates):")
    funnel = tracker.get_conversion_funnel('flexible_dates')
    for key, value in funnel.items():
        print(f"  {key}: {value}")
    
    print("\n6. Power Users:")
    power_users = tracker.get_power_users(min_searches=3)
    for user_id, count in power_users[:5]:
        print(f"  User {user_id}: {count} searches")
    
    # Save data
    print("\n7. Saving analytics data...")
    tracker.save_data()
    print("  ✅ Data saved")
    
    # Dashboard
    print("\n8. Dashboard Data:")
    dashboard = tracker.get_dashboard_data()
    print(json.dumps(dashboard, indent=2))
    
    print("\n✅ All analytics tests completed!")
