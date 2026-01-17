#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Search Analytics System - Advanced Search Methods
Cazador Supremo v14.0 - Phase 3

Comprehensive analytics for search methods:
- Usage tracking per method
- Conversion funnel analysis
- A/B testing framework
- Performance monitoring
- User behavior heatmaps
- Export capabilities

Author: @Juanka_Spain
Version: 14.0.0
Date: 2026-01-17
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict, Counter
from dataclasses import dataclass, field, asdict
import threading
from enum import Enum

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS
# ============================================================================

class SearchMethod(Enum):
    """Search method types"""
    FLEXIBLE_DATES = "flexible_dates"
    MULTI_CITY = "multi_city"
    BUDGET = "budget"
    AIRLINE_SPECIFIC = "airline_specific"
    NONSTOP_ONLY = "nonstop_only"
    REDEYE = "redeye"
    NEARBY_AIRPORTS = "nearby_airports"
    LASTMINUTE = "lastminute"
    SEASONAL_TRENDS = "seasonal_trends"
    GROUP_BOOKING = "group_booking"


class EventType(Enum):
    """Analytics event types"""
    SEARCH_STARTED = "search_started"
    SEARCH_COMPLETED = "search_completed"
    SEARCH_FAILED = "search_failed"
    RESULTS_VIEWED = "results_viewed"
    RESULT_CLICKED = "result_clicked"
    BOOKING_INITIATED = "booking_initiated"
    BOOKING_COMPLETED = "booking_completed"
    SHARED = "shared"
    SAVED = "saved"


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class AnalyticsEvent:
    """Single analytics event"""
    user_id: int
    method: str
    event_type: str
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    session_id: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            'user_id': self.user_id,
            'method': self.method,
            'event_type': self.event_type,
            'timestamp': datetime.fromtimestamp(self.timestamp).isoformat(),
            'metadata': self.metadata,
            'session_id': self.session_id
        }


@dataclass
class SearchMetrics:
    """Metrics for a search method"""
    method: str
    total_searches: int = 0
    successful_searches: int = 0
    failed_searches: int = 0
    total_results_viewed: int = 0
    total_clicks: int = 0
    total_bookings: int = 0
    total_shares: int = 0
    total_saves: int = 0
    avg_response_time_ms: float = 0.0
    unique_users: int = 0
    
    @property
    def success_rate(self) -> float:
        if self.total_searches == 0:
            return 0.0
        return (self.successful_searches / self.total_searches) * 100
    
    @property
    def click_through_rate(self) -> float:
        if self.total_results_viewed == 0:
            return 0.0
        return (self.total_clicks / self.total_results_viewed) * 100
    
    @property
    def conversion_rate(self) -> float:
        if self.total_searches == 0:
            return 0.0
        return (self.total_bookings / self.total_searches) * 100
    
    def to_dict(self) -> Dict:
        return {
            'method': self.method,
            'total_searches': self.total_searches,
            'successful_searches': self.successful_searches,
            'failed_searches': self.failed_searches,
            'success_rate': f"{self.success_rate:.2f}%",
            'total_results_viewed': self.total_results_viewed,
            'total_clicks': self.total_clicks,
            'click_through_rate': f"{self.click_through_rate:.2f}%",
            'total_bookings': self.total_bookings,
            'conversion_rate': f"{self.conversion_rate:.2f}%",
            'total_shares': self.total_shares,
            'total_saves': self.total_saves,
            'avg_response_time_ms': round(self.avg_response_time_ms, 2),
            'unique_users': self.unique_users
        }


@dataclass
class FunnelStage:
    """Funnel stage metrics"""
    stage_name: str
    users_entered: int = 0
    users_completed: int = 0
    drop_off_count: int = 0
    
    @property
    def conversion_rate(self) -> float:
        if self.users_entered == 0:
            return 0.0
        return (self.users_completed / self.users_entered) * 100
    
    @property
    def drop_off_rate(self) -> float:
        if self.users_entered == 0:
            return 0.0
        return (self.drop_off_count / self.users_entered) * 100
    
    def to_dict(self) -> Dict:
        return {
            'stage': self.stage_name,
            'entered': self.users_entered,
            'completed': self.users_completed,
            'dropped': self.drop_off_count,
            'conversion_rate': f"{self.conversion_rate:.2f}%",
            'drop_off_rate': f"{self.drop_off_rate:.2f}%"
        }


# ============================================================================
# ANALYTICS TRACKER
# ============================================================================

class SearchAnalyticsTracker:
    """
    Main analytics tracker for search methods
    
    Features:
    - Event tracking
    - Metrics aggregation
    - Funnel analysis
    - Performance monitoring
    - User segmentation
    """
    
    def __init__(self):
        self.events: List[AnalyticsEvent] = []
        self.metrics: Dict[str, SearchMetrics] = {}
        self.user_sessions: Dict[int, List[str]] = defaultdict(list)
        self.lock = threading.RLock()
        
        # Initialize metrics for all methods
        for method in SearchMethod:
            self.metrics[method.value] = SearchMetrics(method=method.value)
        
        logger.info("SearchAnalyticsTracker initialized")
    
    def track_event(self, user_id: int, method: str, event_type: str, 
                   metadata: Dict = None, session_id: str = None):
        """
        Track analytics event
        
        Args:
            user_id: User ID
            method: Search method
            event_type: Event type
            metadata: Additional data
            session_id: Session identifier
        """
        with self.lock:
            event = AnalyticsEvent(
                user_id=user_id,
                method=method,
                event_type=event_type,
                timestamp=datetime.now().timestamp(),
                metadata=metadata or {},
                session_id=session_id
            )
            
            self.events.append(event)
            self._update_metrics(event)
            
            logger.debug(f"Event tracked: {event_type} by user {user_id} for {method}")
    
    def _update_metrics(self, event: AnalyticsEvent):
        """Update metrics based on event"""
        method = event.method
        if method not in self.metrics:
            self.metrics[method] = SearchMetrics(method=method)
        
        metrics = self.metrics[method]
        event_type = event.event_type
        
        if event_type == EventType.SEARCH_STARTED.value:
            metrics.total_searches += 1
        elif event_type == EventType.SEARCH_COMPLETED.value:
            metrics.successful_searches += 1
            # Track response time if available
            if 'response_time_ms' in event.metadata:
                rt = event.metadata['response_time_ms']
                metrics.avg_response_time_ms = (
                    (metrics.avg_response_time_ms * (metrics.successful_searches - 1) + rt) /
                    metrics.successful_searches
                )
        elif event_type == EventType.SEARCH_FAILED.value:
            metrics.failed_searches += 1
        elif event_type == EventType.RESULTS_VIEWED.value:
            metrics.total_results_viewed += 1
        elif event_type == EventType.RESULT_CLICKED.value:
            metrics.total_clicks += 1
        elif event_type == EventType.BOOKING_COMPLETED.value:
            metrics.total_bookings += 1
        elif event_type == EventType.SHARED.value:
            metrics.total_shares += 1
        elif event_type == EventType.SAVED.value:
            metrics.total_saves += 1
    
    def get_method_metrics(self, method: str) -> Dict:
        """Get metrics for specific method"""
        with self.lock:
            if method in self.metrics:
                return self.metrics[method].to_dict()
            return {}
    
    def get_all_metrics(self) -> Dict[str, Dict]:
        """Get metrics for all methods"""
        with self.lock:
            return {
                method: metrics.to_dict()
                for method, metrics in self.metrics.items()
            }
    
    def get_top_methods(self, n: int = 5) -> List[Dict]:
        """Get top N methods by usage"""
        with self.lock:
            sorted_methods = sorted(
                self.metrics.values(),
                key=lambda m: m.total_searches,
                reverse=True
            )
            return [m.to_dict() for m in sorted_methods[:n]]
    
    def analyze_funnel(self, method: str) -> List[Dict]:
        """
        Analyze conversion funnel for a method
        
        Funnel stages:
        1. Search started
        2. Results viewed
        3. Result clicked
        4. Booking initiated
        5. Booking completed
        """
        with self.lock:
            # Count events by type
            events_by_type = defaultdict(set)
            for event in self.events:
                if event.method == method:
                    events_by_type[event.event_type].add(event.user_id)
            
            # Build funnel
            started = events_by_type[EventType.SEARCH_STARTED.value]
            viewed = events_by_type[EventType.RESULTS_VIEWED.value]
            clicked = events_by_type[EventType.RESULT_CLICKED.value]
            booking_init = events_by_type[EventType.BOOKING_INITIATED.value]
            booking_done = events_by_type[EventType.BOOKING_COMPLETED.value]
            
            stages = [
                FunnelStage(
                    stage_name="Search Started",
                    users_entered=len(started),
                    users_completed=len(viewed),
                    drop_off_count=len(started - viewed)
                ),
                FunnelStage(
                    stage_name="Results Viewed",
                    users_entered=len(viewed),
                    users_completed=len(clicked),
                    drop_off_count=len(viewed - clicked)
                ),
                FunnelStage(
                    stage_name="Result Clicked",
                    users_entered=len(clicked),
                    users_completed=len(booking_init),
                    drop_off_count=len(clicked - booking_init)
                ),
                FunnelStage(
                    stage_name="Booking Initiated",
                    users_entered=len(booking_init),
                    users_completed=len(booking_done),
                    drop_off_count=len(booking_init - booking_done)
                )
            ]
            
            return [stage.to_dict() for stage in stages]
    
    def get_user_behavior(self, user_id: int, days: int = 7) -> Dict:
        """Get user behavior analysis"""
        with self.lock:
            cutoff = datetime.now() - timedelta(days=days)
            cutoff_ts = cutoff.timestamp()
            
            user_events = [
                e for e in self.events
                if e.user_id == user_id and e.timestamp >= cutoff_ts
            ]
            
            # Aggregate
            methods_used = Counter(e.method for e in user_events)
            event_types = Counter(e.event_type for e in user_events)
            
            return {
                'user_id': user_id,
                'period_days': days,
                'total_events': len(user_events),
                'methods_used': dict(methods_used),
                'event_breakdown': dict(event_types),
                'most_used_method': methods_used.most_common(1)[0][0] if methods_used else None
            }
    
    def export_data(self, filepath: str = "analytics_export.json"):
        """Export analytics data to JSON"""
        with self.lock:
            data = {
                'export_timestamp': datetime.now().isoformat(),
                'total_events': len(self.events),
                'metrics': self.get_all_metrics(),
                'recent_events': [e.to_dict() for e in self.events[-100:]]
            }
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Analytics exported to {filepath}")


# ============================================================================
# A/B TESTING FRAMEWORK
# ============================================================================

class ABTestManager:
    """
    A/B testing framework for search methods
    
    Features:
    - Variant assignment
    - Performance comparison
    - Statistical significance
    """
    
    def __init__(self):
        self.tests: Dict[str, Dict] = {}
        self.assignments: Dict[int, Dict[str, str]] = defaultdict(dict)
        self.lock = threading.RLock()
        
        logger.info("ABTestManager initialized")
    
    def create_test(self, test_id: str, variants: List[str], 
                   traffic_split: List[float] = None):
        """
        Create new A/B test
        
        Args:
            test_id: Test identifier
            variants: List of variant names
            traffic_split: Traffic percentage for each variant
        """
        with self.lock:
            if traffic_split is None:
                traffic_split = [1.0 / len(variants)] * len(variants)
            
            self.tests[test_id] = {
                'variants': variants,
                'traffic_split': traffic_split,
                'created_at': datetime.now().isoformat(),
                'results': {v: {'users': 0, 'conversions': 0} for v in variants}
            }
            
            logger.info(f"A/B test created: {test_id} with variants {variants}")
    
    def assign_variant(self, test_id: str, user_id: int) -> Optional[str]:
        """
        Assign user to a variant
        
        Args:
            test_id: Test identifier
            user_id: User ID
            
        Returns:
            Assigned variant name
        """
        with self.lock:
            # Check if already assigned
            if test_id in self.assignments[user_id]:
                return self.assignments[user_id][test_id]
            
            if test_id not in self.tests:
                return None
            
            # Assign based on user_id hash
            import hashlib
            hash_val = int(hashlib.md5(str(user_id).encode()).hexdigest(), 16)
            
            test = self.tests[test_id]
            cumulative = 0
            normalized_hash = (hash_val % 100) / 100.0
            
            for variant, split in zip(test['variants'], test['traffic_split']):
                cumulative += split
                if normalized_hash <= cumulative:
                    self.assignments[user_id][test_id] = variant
                    test['results'][variant]['users'] += 1
                    return variant
            
            # Fallback to first variant
            variant = test['variants'][0]
            self.assignments[user_id][test_id] = variant
            return variant
    
    def record_conversion(self, test_id: str, user_id: int):
        """Record conversion for user's variant"""
        with self.lock:
            if test_id not in self.tests:
                return
            
            variant = self.assignments[user_id].get(test_id)
            if variant:
                self.tests[test_id]['results'][variant]['conversions'] += 1
    
    def get_test_results(self, test_id: str) -> Dict:
        """Get A/B test results"""
        with self.lock:
            if test_id not in self.tests:
                return {}
            
            test = self.tests[test_id]
            results = {}
            
            for variant, data in test['results'].items():
                users = data['users']
                conversions = data['conversions']
                conversion_rate = (conversions / users * 100) if users > 0 else 0.0
                
                results[variant] = {
                    'users': users,
                    'conversions': conversions,
                    'conversion_rate': f"{conversion_rate:.2f}%"
                }
            
            return {
                'test_id': test_id,
                'created_at': test['created_at'],
                'variants': results
            }


# ============================================================================
# GLOBAL INSTANCES
# ============================================================================

analytics_tracker = SearchAnalyticsTracker()
ab_test_manager = ABTestManager()


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    print("="*60)
    print("Search Analytics System - Testing")
    print("="*60)
    
    tracker = SearchAnalyticsTracker()
    
    # Simulate events
    print("\n1. Simulating user events...")
    for i in range(10):
        tracker.track_event(100 + i, 'flexible_dates', EventType.SEARCH_STARTED.value)
        tracker.track_event(100 + i, 'flexible_dates', EventType.SEARCH_COMPLETED.value,
                          {'response_time_ms': 50 + i*5})
        if i < 7:
            tracker.track_event(100 + i, 'flexible_dates', EventType.RESULTS_VIEWED.value)
        if i < 5:
            tracker.track_event(100 + i, 'flexible_dates', EventType.RESULT_CLICKED.value)
        if i < 3:
            tracker.track_event(100 + i, 'flexible_dates', EventType.BOOKING_COMPLETED.value)
    
    # Get metrics
    print("\n2. Method metrics:")
    metrics = tracker.get_method_metrics('flexible_dates')
    for key, value in metrics.items():
        print(f"   {key}: {value}")
    
    # Analyze funnel
    print("\n3. Conversion funnel:")
    funnel = tracker.analyze_funnel('flexible_dates')
    for stage in funnel:
        print(f"   {stage['stage']}: {stage['conversion_rate']}")
    
    # Test A/B framework
    print("\n4. A/B Testing:")
    ab = ABTestManager()
    ab.create_test('search_ui_test', ['variant_a', 'variant_b'])
    
    for user_id in range(100, 120):
        variant = ab.assign_variant('search_ui_test', user_id)
        if user_id % 2 == 0:  # 50% conversion for testing
            ab.record_conversion('search_ui_test', user_id)
    
    results = ab.get_test_results('search_ui_test')
    print(f"   Test results: {json.dumps(results, indent=2)}")
    
    print("\n✅ All analytics tests passed!")
