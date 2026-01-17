#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
📊 SEARCH ANALYTICS SYSTEM
Cazador Supremo v14.1 - Phase 3

Comprehensive analytics for search behavior:
- User behavior tracking
- Conversion funnels
- A/B testing framework
- Heatmap generation
- ROI calculator

Author: @Juanka_Spain
Version: 14.1.0
Date: 2026-01-17
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
from collections import defaultdict, Counter
from enum import Enum
import statistics

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS
# ============================================================================

class EventType(Enum):
    """Analytics event types"""
    SEARCH_STARTED = "search_started"
    SEARCH_COMPLETED = "search_completed"
    RESULTS_VIEWED = "results_viewed"
    DEAL_CLICKED = "deal_clicked"
    DEAL_SHARED = "deal_shared"
    WATCHLIST_ADDED = "watchlist_added"
    BOOKING_INITIATED = "booking_initiated"
    BOOKING_COMPLETED = "booking_completed"
    PREMIUM_UPGRADED = "premium_upgraded"


class SearchMethod(Enum):
    """Search method types"""
    FLEXIBLE_DATES = "flexible_dates"
    MULTI_CITY = "multi_city"
    BUDGET = "budget"
    STANDARD = "standard"


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class AnalyticsEvent:
    """Single analytics event"""
    event_id: str
    user_id: int
    event_type: EventType
    timestamp: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    session_id: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            'event_id': self.event_id,
            'user_id': self.user_id,
            'event_type': self.event_type.value,
            'timestamp': self.timestamp,
            'metadata': self.metadata,
            'session_id': self.session_id
        }


@dataclass
class FunnelStep:
    """Conversion funnel step"""
    name: str
    users_entered: int
    users_completed: int
    avg_time_seconds: float
    drop_off_rate: float
    
    @property
    def conversion_rate(self) -> float:
        if self.users_entered == 0:
            return 0.0
        return self.users_completed / self.users_entered


# ============================================================================
# ANALYTICS MANAGER
# ============================================================================

class SearchAnalyticsManager:
    """
    Comprehensive analytics manager.
    
    Tracks:
    - Search patterns
    - Conversion funnels
    - User behavior
    - A/B test results
    - ROI metrics
    """
    
    def __init__(self, data_file: str = 'analytics_events.json'):
        self.data_file = Path(data_file)
        self.events: List[AnalyticsEvent] = []
        self.sessions: Dict[str, List[AnalyticsEvent]] = defaultdict(list)
        
        self._load_events()
        
        logger.info("📊 SearchAnalyticsManager initialized")
    
    def _load_events(self):
        """Load events from file"""
        if not self.data_file.exists():
            return
        
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)
            
            for event_data in data:
                event = AnalyticsEvent(
                    event_id=event_data['event_id'],
                    user_id=event_data['user_id'],
                    event_type=EventType(event_data['event_type']),
                    timestamp=event_data['timestamp'],
                    metadata=event_data.get('metadata', {}),
                    session_id=event_data.get('session_id')
                )
                self.events.append(event)
                
                if event.session_id:
                    self.sessions[event.session_id].append(event)
            
            logger.info(f"✅ Loaded {len(self.events)} analytics events")
        except Exception as e:
            logger.error(f"Error loading events: {e}")
    
    def _save_events(self):
        """Save events to file"""
        try:
            data = [event.to_dict() for event in self.events]
            
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.debug("💾 Events saved")
        except Exception as e:
            logger.error(f"Error saving events: {e}")
    
    def track_event(
        self,
        user_id: int,
        event_type: EventType,
        metadata: Dict = None,
        session_id: str = None
    ):
        """Track an analytics event"""
        import uuid
        
        event = AnalyticsEvent(
            event_id=str(uuid.uuid4()),
            user_id=user_id,
            event_type=event_type,
            timestamp=datetime.now().isoformat(),
            metadata=metadata or {},
            session_id=session_id
        )
        
        self.events.append(event)
        
        if session_id:
            self.sessions[session_id].append(event)
        
        # Save every 10 events
        if len(self.events) % 10 == 0:
            self._save_events()
        
        logger.debug(f"📊 Tracked: {event_type.value} for user {user_id}")
    
    # ========================================================================
    # SEARCH ANALYTICS
    # ========================================================================
    
    def get_search_stats(self, days: int = 30) -> Dict:
        """Get search statistics"""
        cutoff = datetime.now() - timedelta(days=days)
        
        search_events = [
            e for e in self.events
            if e.event_type == EventType.SEARCH_COMPLETED
            and datetime.fromisoformat(e.timestamp) >= cutoff
        ]
        
        if not search_events:
            return {'total_searches': 0}
        
        # Count by method
        methods = Counter(
            e.metadata.get('method', 'standard')
            for e in search_events
        )
        
        # Average results per search
        results_counts = [
            e.metadata.get('results_count', 0)
            for e in search_events
            if 'results_count' in e.metadata
        ]
        
        avg_results = statistics.mean(results_counts) if results_counts else 0
        
        return {
            'total_searches': len(search_events),
            'by_method': dict(methods),
            'avg_results_per_search': avg_results,
            'unique_users': len(set(e.user_id for e in search_events))
        }
    
    def get_popular_routes(self, limit: int = 10) -> List[Dict]:
        """Get most popular search routes"""
        search_events = [
            e for e in self.events
            if e.event_type == EventType.SEARCH_COMPLETED
        ]
        
        routes = Counter(
            f"{e.metadata.get('origin')}-{e.metadata.get('destination')}"
            for e in search_events
            if 'origin' in e.metadata and 'destination' in e.metadata
        )
        
        return [
            {'route': route, 'searches': count}
            for route, count in routes.most_common(limit)
        ]
    
    # ========================================================================
    # CONVERSION FUNNEL
    # ========================================================================
    
    def get_conversion_funnel(self) -> List[FunnelStep]:
        """
        Calculate conversion funnel.
        
        Steps:
        1. Search started
        2. Results viewed
        3. Deal clicked
        4. Booking initiated
        5. Booking completed
        """
        steps_data = [
            (EventType.SEARCH_STARTED, "Search Started"),
            (EventType.RESULTS_VIEWED, "Results Viewed"),
            (EventType.DEAL_CLICKED, "Deal Clicked"),
            (EventType.BOOKING_INITIATED, "Booking Initiated"),
            (EventType.BOOKING_COMPLETED, "Booking Completed")
        ]
        
        funnel = []
        
        for i, (event_type, step_name) in enumerate(steps_data):
            users = set(e.user_id for e in self.events if e.event_type == event_type)
            
            if i == 0:
                entered = len(users)
            else:
                prev_users = set(
                    e.user_id for e in self.events
                    if e.event_type == steps_data[i-1][0]
                )
                entered = len(prev_users)
            
            completed = len(users)
            drop_off = 1 - (completed / entered if entered > 0 else 0)
            
            # Calculate avg time
            times = []
            for user in users:
                user_events = [e for e in self.events if e.user_id == user]
                # Simplified - would need proper session tracking
                times.append(10)  # Placeholder
            
            avg_time = statistics.mean(times) if times else 0
            
            step = FunnelStep(
                name=step_name,
                users_entered=entered,
                users_completed=completed,
                avg_time_seconds=avg_time,
                drop_off_rate=drop_off
            )
            
            funnel.append(step)
        
        return funnel
    
    # ========================================================================
    # USER BEHAVIOR
    # ========================================================================
    
    def get_user_journey(self, user_id: int) -> List[AnalyticsEvent]:
        """Get complete journey for a user"""
        return sorted(
            [e for e in self.events if e.user_id == user_id],
            key=lambda e: e.timestamp
        )
    
    def get_session_stats(self, session_id: str) -> Dict:
        """Get statistics for a session"""
        session_events = self.sessions.get(session_id, [])
        
        if not session_events:
            return {}
        
        start_time = datetime.fromisoformat(session_events[0].timestamp)
        end_time = datetime.fromisoformat(session_events[-1].timestamp)
        duration = (end_time - start_time).total_seconds()
        
        return {
            'session_id': session_id,
            'events_count': len(session_events),
            'duration_seconds': duration,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'events': [e.event_type.value for e in session_events]
        }
    
    # ========================================================================
    # HEATMAP DATA
    # ========================================================================
    
    def get_search_heatmap(self, days: int = 30) -> Dict:
        """
        Generate heatmap data for search activity.
        
        Returns searches by hour and day of week.
        """
        cutoff = datetime.now() - timedelta(days=days)
        
        search_events = [
            e for e in self.events
            if e.event_type == EventType.SEARCH_COMPLETED
            and datetime.fromisoformat(e.timestamp) >= cutoff
        ]
        
        heatmap = defaultdict(lambda: defaultdict(int))
        
        for event in search_events:
            dt = datetime.fromisoformat(event.timestamp)
            day = dt.strftime('%A')
            hour = dt.hour
            heatmap[day][hour] += 1
        
        return dict(heatmap)
    
    # ========================================================================
    # ROI CALCULATOR
    # ========================================================================
    
    def calculate_roi(self, days: int = 30) -> Dict:
        """
        Calculate ROI metrics.
        
        Metrics:
        - Total bookings
        - Revenue generated
        - Cost per acquisition
        - Customer lifetime value
        """
        cutoff = datetime.now() - timedelta(days=days)
        
        booking_events = [
            e for e in self.events
            if e.event_type == EventType.BOOKING_COMPLETED
            and datetime.fromisoformat(e.timestamp) >= cutoff
        ]
        
        premium_events = [
            e for e in self.events
            if e.event_type == EventType.PREMIUM_UPGRADED
            and datetime.fromisoformat(e.timestamp) >= cutoff
        ]
        
        total_bookings = len(booking_events)
        
        # Extract revenue from metadata
        booking_revenue = sum(
            e.metadata.get('booking_value', 0)
            for e in booking_events
        )
        
        premium_revenue = sum(
            e.metadata.get('premium_price', 0)
            for e in premium_events
        )
        
        total_revenue = booking_revenue + premium_revenue
        
        # Simplified cost calculation
        total_searches = len([
            e for e in self.events
            if e.event_type == EventType.SEARCH_COMPLETED
            and datetime.fromisoformat(e.timestamp) >= cutoff
        ])
        
        cost_per_search = 0.05  # €0.05 per search (API costs)
        total_cost = total_searches * cost_per_search
        
        roi = ((total_revenue - total_cost) / total_cost * 100) if total_cost > 0 else 0
        
        return {
            'period_days': days,
            'total_bookings': total_bookings,
            'total_revenue': total_revenue,
            'total_cost': total_cost,
            'profit': total_revenue - total_cost,
            'roi_percentage': roi,
            'avg_booking_value': booking_revenue / total_bookings if total_bookings > 0 else 0,
            'conversion_rate': total_bookings / total_searches if total_searches > 0 else 0
        }
    
    # ========================================================================
    # REPORTING
    # ========================================================================
    
    def generate_report(self, days: int = 30) -> str:
        """Generate comprehensive analytics report"""
        search_stats = self.get_search_stats(days)
        popular_routes = self.get_popular_routes(10)
        funnel = self.get_conversion_funnel()
        roi = self.calculate_roi(days)
        
        report = []
        report.append("="*70)
        report.append(f"📊 ANALYTICS REPORT - Last {days} days")
        report.append("="*70)
        
        # Search stats
        report.append("\n🔍 SEARCH STATISTICS:")
        report.append(f"  Total searches: {search_stats['total_searches']}")
        report.append(f"  Unique users: {search_stats['unique_users']}")
        report.append(f"  Avg results: {search_stats['avg_results_per_search']:.1f}")
        
        if 'by_method' in search_stats:
            report.append("\n  By method:")
            for method, count in search_stats['by_method'].items():
                report.append(f"    {method}: {count}")
        
        # Popular routes
        report.append("\n✈️ TOP ROUTES:")
        for i, route_data in enumerate(popular_routes[:5], 1):
            report.append(f"  {i}. {route_data['route']}: {route_data['searches']} searches")
        
        # Conversion funnel
        report.append("\n🎯 CONVERSION FUNNEL:")
        for step in funnel:
            report.append(
                f"  {step.name}: "
                f"{step.users_completed}/{step.users_entered} "
                f"({step.conversion_rate:.1%}) "
                f"Drop-off: {step.drop_off_rate:.1%}"
            )
        
        # ROI
        report.append("\n💰 ROI METRICS:")
        report.append(f"  Revenue: €{roi['total_revenue']:.2f}")
        report.append(f"  Cost: €{roi['total_cost']:.2f}")
        report.append(f"  Profit: €{roi['profit']:.2f}")
        report.append(f"  ROI: {roi['roi_percentage']:.1f}%")
        report.append(f"  Conversion rate: {roi['conversion_rate']:.2%}")
        
        report.append("\n" + "="*70)
        
        return "\n".join(report)


# ============================================================================
# TESTING
# ============================================================================

if __name__ == '__main__':
    print("🧪 Testing SearchAnalyticsManager...\n")
    
    # Create manager
    analytics = SearchAnalyticsManager('test_analytics.json')
    
    # Track some events
    print("1. Tracking test events...")
    for i in range(5):
        analytics.track_event(
            user_id=1000 + i,
            event_type=EventType.SEARCH_STARTED,
            metadata={'origin': 'MAD', 'destination': 'BCN'},
            session_id=f"session_{i}"
        )
        
        analytics.track_event(
            user_id=1000 + i,
            event_type=EventType.SEARCH_COMPLETED,
            metadata={'origin': 'MAD', 'destination': 'BCN', 'results_count': 10},
            session_id=f"session_{i}"
        )
    
    print(f"   Tracked {len(analytics.events)} events\n")
    
    # Get search stats
    print("2. Getting search stats...")
    stats = analytics.get_search_stats()
    print(f"   Total searches: {stats['total_searches']}")
    print(f"   Unique users: {stats['unique_users']}\n")
    
    # Get popular routes
    print("3. Getting popular routes...")
    routes = analytics.get_popular_routes()
    for route_data in routes:
        print(f"   {route_data['route']}: {route_data['searches']} searches")
    
    # Generate report
    print("\n4. Generating report...")
    report = analytics.generate_report(30)
    print(report)
    
    print("\n✅ All tests completed!")
