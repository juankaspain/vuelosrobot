#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Value Metrics Dashboard for Premium Conversion
IT6 - DAY 3/5

Features:
- Personal value tracking (savings, time, deals)
- Comparative metrics (Free vs Premium)
- ROI calculator for premium
- Social proof integration
- Value-based upgrade triggers
- Missed opportunity tracking

Author: @Juanka_Spain
Version: 14.0.0-alpha.3
Date: 2026-01-16
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import statistics


# ============================================================================
# CONSTANTS
# ============================================================================

# Average metrics for premium users (benchmarks)
PREMIUM_BENCHMARKS = {
    "avg_deals_per_month": 45,
    "avg_savings_per_month": 1680,
    "avg_response_time_minutes": 5,
    "avg_deals_missed": 0,
    "avg_searches_per_month": 180,
    "notification_speed_multiplier": 24,  # 24x faster than free
}

# Average metrics for free users
FREE_BENCHMARKS = {
    "avg_deals_per_month": 12,
    "avg_savings_per_month": 450,
    "avg_response_time_minutes": 120,
    "avg_deals_missed": 8,
    "avg_searches_per_month": 65,
}

# Social proof data
SOCIAL_PROOF = {
    "total_premium_users": 892,
    "avg_rating": 4.8,
    "total_savings_generated": 156000,
    "top_hunters_premium_percent": 85,
    "avg_monthly_savings": 1680,
    "satisfaction_rate": 0.94,
}

# Time saved estimates
TIME_SAVINGS = {
    "manual_search_minutes": 15,  # Time for manual search
    "automated_search_minutes": 0.5,  # Time with bot
    "notification_response_free_minutes": 120,  # Free user response time
    "notification_response_premium_minutes": 5,  # Premium instant
}


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class UserValue:
    """Track value generated for a user"""
    user_id: int
    total_searches: int = 0
    total_deals_found: int = 0
    total_deals_claimed: int = 0
    total_deals_missed: int = 0  # Due to limits
    total_savings: float = 0.0  # EUR
    time_saved_hours: float = 0.0
    notifications_received: int = 0
    first_search_date: Optional[datetime] = None
    last_activity: Optional[datetime] = None
    is_premium: bool = False
    premium_since: Optional[datetime] = None
    
    @property
    def days_as_user(self) -> int:
        """Days since first search"""
        if not self.first_search_date:
            return 0
        return (datetime.now() - self.first_search_date).days
    
    @property
    def deals_per_month(self) -> float:
        """Average deals found per month"""
        if self.days_as_user == 0:
            return 0
        months = max(1, self.days_as_user / 30)
        return self.total_deals_found / months
    
    @property
    def savings_per_month(self) -> float:
        """Average savings per month"""
        if self.days_as_user == 0:
            return 0
        months = max(1, self.days_as_user / 30)
        return self.total_savings / months
    
    @property
    def missed_opportunity_value(self) -> float:
        """Value of deals missed due to limits"""
        # Assume average deal is €150
        return self.total_deals_missed * 150
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        if self.first_search_date:
            data['first_search_date'] = self.first_search_date.isoformat()
        if self.last_activity:
            data['last_activity'] = self.last_activity.isoformat()
        if self.premium_since:
            data['premium_since'] = self.premium_since.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'UserValue':
        if data.get('first_search_date'):
            data['first_search_date'] = datetime.fromisoformat(data['first_search_date'])
        if data.get('last_activity'):
            data['last_activity'] = datetime.fromisoformat(data['last_activity'])
        if data.get('premium_since'):
            data['premium_since'] = datetime.fromisoformat(data['premium_since'])
        return cls(**data)


@dataclass
class DealMissed:
    """Record of a deal missed due to free limits"""
    user_id: int
    deal_route: str
    deal_value: float  # Savings amount
    deal_price: float
    missed_date: datetime
    reason: str  # "search_limit", "watchlist_full", "notification_delay"
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['missed_date'] = self.missed_date.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'DealMissed':
        data['missed_date'] = datetime.fromisoformat(data['missed_date'])
        return cls(**data)


# ============================================================================
# VALUE TRACKER
# ============================================================================

class ValueTracker:
    """
    Tracks value generated for users to demonstrate premium ROI.
    
    Features:
    - Personal value metrics
    - Comparative analysis (Free vs Premium)
    - ROI calculation
    - Missed opportunity tracking
    - Social proof integration
    """
    
    def __init__(self, data_dir: str = "."):
        self.data_dir = Path(data_dir)
        self.user_values_file = self.data_dir / "user_values.json"
        self.deals_missed_file = self.data_dir / "deals_missed.json"
        
        # Load data
        self.user_values: Dict[int, UserValue] = self._load_user_values()
        self.deals_missed: Dict[int, List[DealMissed]] = self._load_deals_missed()
        
        print("✅ ValueTracker initialized")
    
    # ========================================================================
    # DATA PERSISTENCE
    # ========================================================================
    
    def _load_user_values(self) -> Dict[int, UserValue]:
        """Load user value data from file"""
        if not self.user_values_file.exists():
            return {}
        
        try:
            with open(self.user_values_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {
                    int(user_id): UserValue.from_dict(value)
                    for user_id, value in data.items()
                }
        except Exception as e:
            print(f"⚠️ Error loading user values: {e}")
            return {}
    
    def _save_user_values(self):
        """Save user value data to file"""
        try:
            data = {
                str(user_id): value.to_dict()
                for user_id, value in self.user_values.items()
            }
            with open(self.user_values_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Error saving user values: {e}")
    
    def _load_deals_missed(self) -> Dict[int, List[DealMissed]]:
        """Load missed deals from file"""
        if not self.deals_missed_file.exists():
            return {}
        
        try:
            with open(self.deals_missed_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {
                    int(user_id): [DealMissed.from_dict(d) for d in deals]
                    for user_id, deals in data.items()
                }
        except Exception as e:
            print(f"⚠️ Error loading deals missed: {e}")
            return {}
    
    def _save_deals_missed(self):
        """Save missed deals to file"""
        try:
            data = {
                str(user_id): [d.to_dict() for d in deals]
                for user_id, deals in self.deals_missed.items()
            }
            with open(self.deals_missed_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Error saving deals missed: {e}")
    
    # ========================================================================
    # VALUE TRACKING
    # ========================================================================
    
    def _get_or_create_value(self, user_id: int) -> UserValue:
        """Get or create user value record"""
        if user_id not in self.user_values:
            self.user_values[user_id] = UserValue(
                user_id=user_id,
                first_search_date=datetime.now()
            )
        return self.user_values[user_id]
    
    def track_search(self, user_id: int):
        """Track a search performed by user"""
        value = self._get_or_create_value(user_id)
        value.total_searches += 1
        value.last_activity = datetime.now()
        
        # Time saved vs manual search
        time_saved = TIME_SAVINGS["manual_search_minutes"] - TIME_SAVINGS["automated_search_minutes"]
        value.time_saved_hours += time_saved / 60
        
        self._save_user_values()
    
    def track_deal_found(self, user_id: int, deal_value: float, claimed: bool = False):
        """
        Track a deal found by user.
        
        Args:
            user_id: User ID
            deal_value: Savings amount in EUR
            claimed: Whether user claimed the deal
        """
        value = self._get_or_create_value(user_id)
        value.total_deals_found += 1
        value.last_activity = datetime.now()
        
        if claimed:
            value.total_deals_claimed += 1
            value.total_savings += deal_value
        
        self._save_user_values()
    
    def track_deal_missed(self, user_id: int, route: str, deal_value: float, 
                          deal_price: float, reason: str):
        """
        Track a deal missed due to free tier limitations.
        
        Args:
            user_id: User ID
            route: Flight route (e.g., "MAD-MIA")
            deal_value: Savings amount
            deal_price: Deal price
            reason: Why missed ("search_limit", "watchlist_full", "notification_delay")
        """
        value = self._get_or_create_value(user_id)
        value.total_deals_missed += 1
        
        # Record the missed deal
        missed = DealMissed(
            user_id=user_id,
            deal_route=route,
            deal_value=deal_value,
            deal_price=deal_price,
            missed_date=datetime.now(),
            reason=reason
        )
        
        if user_id not in self.deals_missed:
            self.deals_missed[user_id] = []
        self.deals_missed[user_id].append(missed)
        
        self._save_user_values()
        self._save_deals_missed()
    
    def track_notification(self, user_id: int, is_premium: bool = False):
        """Track notification received"""
        value = self._get_or_create_value(user_id)
        value.notifications_received += 1
        
        # Time saved with premium notifications (instant vs delayed)
        if is_premium:
            time_saved = TIME_SAVINGS["notification_response_free_minutes"] - TIME_SAVINGS["notification_response_premium_minutes"]
            value.time_saved_hours += time_saved / 60
        
        self._save_user_values()
    
    def set_premium_status(self, user_id: int, is_premium: bool):
        """Set user's premium status"""
        value = self._get_or_create_value(user_id)
        value.is_premium = is_premium
        if is_premium and not value.premium_since:
            value.premium_since = datetime.now()
        self._save_user_values()
    
    # ========================================================================
    # VALUE DASHBOARD
    # ========================================================================
    
    def get_user_dashboard(self, user_id: int) -> Dict:
        """
        Get complete value dashboard for user.
        
        Returns:
            Dict with all value metrics
        """
        value = self._get_or_create_value(user_id)
        
        # Calculate ROI if premium
        roi = 0
        if value.is_premium and value.premium_since:
            months_premium = max(1, (datetime.now() - value.premium_since).days / 30)
            cost = months_premium * 9.99  # €9.99/month
            roi = (value.total_savings / cost) if cost > 0 else 0
        
        # Missed opportunity
        missed_value = value.missed_opportunity_value
        recent_missed = self.deals_missed.get(user_id, [])[-5:]  # Last 5
        
        return {
            "user_id": user_id,
            "is_premium": value.is_premium,
            "days_as_user": value.days_as_user,
            "total_searches": value.total_searches,
            "total_deals_found": value.total_deals_found,
            "total_deals_claimed": value.total_deals_claimed,
            "total_savings": value.total_savings,
            "time_saved_hours": value.time_saved_hours,
            "deals_per_month": value.deals_per_month,
            "savings_per_month": value.savings_per_month,
            "total_deals_missed": value.total_deals_missed,
            "missed_opportunity_value": missed_value,
            "recent_missed_deals": [d.to_dict() for d in recent_missed],
            "roi": roi,
            "notifications_received": value.notifications_received
        }
    
    def get_comparative_metrics(self, user_id: int) -> Dict:
        """
        Compare user metrics against free and premium benchmarks.
        
        Returns:
            Dict with comparisons
        """
        dashboard = self.get_user_dashboard(user_id)
        
        if dashboard["is_premium"]:
            # Compare against premium benchmarks
            benchmark = PREMIUM_BENCHMARKS
            vs_label = "Avg Premium"
        else:
            # Compare against free benchmarks
            benchmark = FREE_BENCHMARKS
            vs_label = "Avg Free"
        
        # Calculate differences
        deals_diff = dashboard["deals_per_month"] - benchmark["avg_deals_per_month"]
        savings_diff = dashboard["savings_per_month"] - benchmark["avg_savings_per_month"]
        
        # Premium potential
        if not dashboard["is_premium"]:
            premium_potential = {
                "extra_deals": PREMIUM_BENCHMARKS["avg_deals_per_month"] - dashboard["deals_per_month"],
                "extra_savings": PREMIUM_BENCHMARKS["avg_savings_per_month"] - dashboard["savings_per_month"],
                "faster_notifications": PREMIUM_BENCHMARKS["notification_speed_multiplier"],
                "zero_missed_deals": dashboard["total_deals_missed"]
            }
        else:
            premium_potential = None
        
        return {
            "user_metrics": {
                "deals_per_month": dashboard["deals_per_month"],
                "savings_per_month": dashboard["savings_per_month"],
                "deals_missed": dashboard["total_deals_missed"]
            },
            "benchmark": {
                "label": vs_label,
                "deals_per_month": benchmark["avg_deals_per_month"],
                "savings_per_month": benchmark["avg_savings_per_month"],
                "deals_missed": benchmark.get("avg_deals_missed", 0)
            },
            "difference": {
                "deals": deals_diff,
                "savings": savings_diff,
                "performance_vs_avg": "above" if deals_diff > 0 else "below"
            },
            "premium_potential": premium_potential
        }
    
    def calculate_premium_roi(self, user_id: int, plan: str = "monthly") -> Dict:
        """
        Calculate ROI of upgrading to premium.
        
        Args:
            user_id: User ID
            plan: "monthly" or "annual"
        
        Returns:
            Dict with ROI calculation
        """
        dashboard = self.get_user_dashboard(user_id)
        
        # Premium cost
        if plan == "monthly":
            monthly_cost = 9.99
            annual_cost = monthly_cost * 12
        else:  # annual
            annual_cost = 99.99
            monthly_cost = annual_cost / 12
        
        # Current performance
        current_monthly_savings = dashboard["savings_per_month"]
        
        # Expected premium performance (use benchmarks)
        expected_monthly_savings = PREMIUM_BENCHMARKS["avg_savings_per_month"]
        
        # Additional savings with premium
        extra_monthly_savings = expected_monthly_savings - current_monthly_savings
        extra_annual_savings = extra_monthly_savings * 12
        
        # ROI calculation
        monthly_roi = (extra_monthly_savings / monthly_cost) if monthly_cost > 0 else 0
        annual_roi = (extra_annual_savings / annual_cost) if annual_cost > 0 else 0
        
        # Payback period
        if extra_monthly_savings > 0:
            payback_months = monthly_cost / extra_monthly_savings
        else:
            payback_months = float('inf')
        
        # Missed deals value
        missed_value = dashboard["missed_opportunity_value"]
        
        return {
            "plan": plan,
            "cost": {
                "monthly": monthly_cost,
                "annual": annual_cost
            },
            "current_performance": {
                "monthly_savings": current_monthly_savings,
                "annual_savings": current_monthly_savings * 12
            },
            "premium_performance": {
                "monthly_savings": expected_monthly_savings,
                "annual_savings": expected_monthly_savings * 12
            },
            "additional_value": {
                "monthly": extra_monthly_savings,
                "annual": extra_annual_savings,
                "missed_deals_recovered": missed_value
            },
            "roi": {
                "monthly": monthly_roi,
                "annual": annual_roi,
                "multiplier": f"{monthly_roi:.1f}x"
            },
            "payback_period_days": payback_months * 30 if payback_months != float('inf') else None,
            "break_even_deals": 1 if extra_monthly_savings > monthly_cost else 2
        }
    
    # ========================================================================
    # SOCIAL PROOF
    # ========================================================================
    
    def get_social_proof(self) -> Dict:
        """Get social proof data for premium"""
        return SOCIAL_PROOF.copy()
    
    def should_show_upgrade_prompt(self, user_id: int) -> Tuple[bool, str, Dict]:
        """
        Determine if upgrade prompt should be shown based on value.
        
        Returns:
            (should_show, reason, context)
        """
        dashboard = self.get_user_dashboard(user_id)
        
        if dashboard["is_premium"]:
            return False, "Already premium", {}
        
        # Trigger 1: High value demonstrated
        if dashboard["total_savings"] >= 500:
            return True, "high_value", {
                "total_savings": dashboard["total_savings"],
                "roi": self.calculate_premium_roi(user_id)
            }
        
        # Trigger 2: Multiple deals missed
        if dashboard["total_deals_missed"] >= 3:
            return True, "deals_missed", {
                "deals_missed": dashboard["total_deals_missed"],
                "missed_value": dashboard["missed_opportunity_value"]
            }
        
        # Trigger 3: Power user (high engagement)
        if dashboard["total_searches"] >= 50:
            return True, "power_user", {
                "searches": dashboard["total_searches"],
                "deals_found": dashboard["total_deals_found"]
            }
        
        return False, "No trigger", {}
    
    # ========================================================================
    # ANALYTICS
    # ========================================================================
    
    def get_aggregate_stats(self) -> Dict:
        """Get aggregate statistics across all users"""
        if not self.user_values:
            return {}
        
        free_users = [v for v in self.user_values.values() if not v.is_premium]
        premium_users = [v for v in self.user_values.values() if v.is_premium]
        
        stats = {
            "total_users": len(self.user_values),
            "free_users": len(free_users),
            "premium_users": len(premium_users),
            "total_savings_generated": sum(v.total_savings for v in self.user_values.values()),
            "total_deals_found": sum(v.total_deals_found for v in self.user_values.values()),
            "total_deals_missed": sum(v.total_deals_missed for v in self.user_values.values())
        }
        
        # Average metrics
        if free_users:
            stats["free_avg"] = {
                "deals_per_month": statistics.mean([u.deals_per_month for u in free_users if u.days_as_user > 0]),
                "savings_per_month": statistics.mean([u.savings_per_month for u in free_users if u.days_as_user > 0])
            }
        
        if premium_users:
            stats["premium_avg"] = {
                "deals_per_month": statistics.mean([u.deals_per_month for u in premium_users if u.days_as_user > 0]),
                "savings_per_month": statistics.mean([u.savings_per_month for u in premium_users if u.days_as_user > 0])
            }
        
        return stats


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def format_value_dashboard(dashboard: Dict) -> str:
    """
    Format value dashboard for display.
    
    Args:
        dashboard: Dict from get_user_dashboard()
    
    Returns:
        Formatted string
    """
    return f"""📊 Tu Valor Generado

💰 Ahorro Total: €{dashboard['total_savings']:.2f}
⏱️ Tiempo Ahorrado: {dashboard['time_saved_hours']:.1f} horas
🔥 Chollos Encontrados: {dashboard['total_deals_found']}
✅ Chollos Aprovechados: {dashboard['total_deals_claimed']}
❌ Chollos Perdidos: {dashboard['total_deals_missed']} (por límites free)

📈 Promedios Mensuales:
• {dashboard['deals_per_month']:.1f} chollos/mes
• €{dashboard['savings_per_month']:.2f} ahorro/mes

{"" if dashboard['is_premium'] else f"""💡 Con Premium:
• +{dashboard['total_deals_missed']} chollos más = +€{dashboard['missed_opportunity_value']:.2f}
• Notificaciones instantáneas
• 0 chollos perdidos
"""}
"""


# ============================================================================
# MAIN (TESTING)
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("📊 TESTING: Value Metrics Dashboard")
    print("="*60 + "\n")
    
    # Initialize tracker
    tracker = ValueTracker()
    
    test_user = 11111
    
    print("1️⃣ Tracking User Activity")
    print("-" * 40)
    
    # Simulate user activity
    for _ in range(25):
        tracker.track_search(test_user)
    
    tracker.track_deal_found(test_user, 250, claimed=True)
    tracker.track_deal_found(test_user, 180, claimed=True)
    tracker.track_deal_found(test_user, 320, claimed=False)
    
    tracker.track_deal_missed(test_user, "MAD-MIA", 150, 485, "search_limit")
    tracker.track_deal_missed(test_user, "MAD-NYC", 200, 520, "watchlist_full")
    
    for _ in range(10):
        tracker.track_notification(test_user, is_premium=False)
    
    print("✅ Tracked 25 searches, 3 deals, 2 missed, 10 notifications")
    
    print("\n2️⃣ Personal Dashboard")
    print("-" * 40)
    
    dashboard = tracker.get_user_dashboard(test_user)
    print(format_value_dashboard(dashboard))
    
    print("\n3️⃣ Comparative Metrics")
    print("-" * 40)
    
    comparison = tracker.get_comparative_metrics(test_user)
    print(f"\nYour Performance: {comparison['user_metrics']['deals_per_month']:.1f} deals/month")
    print(f"{comparison['benchmark']['label']}: {comparison['benchmark']['deals_per_month']} deals/month")
    
    if comparison['premium_potential']:
        pot = comparison['premium_potential']
        print(f"\n🚀 Premium Potential:")
        print(f"• +{pot['extra_deals']:.1f} deals/month")
        print(f"• +€{pot['extra_savings']:.2f}/month")
        print(f"• {pot['faster_notifications']}x faster notifications")
    
    print("\n4️⃣ Premium ROI Calculation")
    print("-" * 40)
    
    roi = tracker.calculate_premium_roi(test_user, "monthly")
    print(f"\n💰 Premium Monthly (€{roi['cost']['monthly']})")
    print(f"\nCurrent: €{roi['current_performance']['monthly_savings']:.2f}/month")
    print(f"With Premium: €{roi['premium_performance']['monthly_savings']:.2f}/month")
    print(f"Extra Savings: €{roi['additional_value']['monthly']:.2f}/month")
    print(f"\nROI: {roi['roi']['multiplier']} en el primer mes")
    print(f"Break-even: {roi['break_even_deals']} chollos")
    
    print("\n5️⃣ Upgrade Trigger Check")
    print("-" * 40)
    
    should_show, reason, context = tracker.should_show_upgrade_prompt(test_user)
    print(f"\nShow upgrade: {should_show}")
    print(f"Reason: {reason}")
    if context:
        print(f"Context: {context}")
    
    print("\n6️⃣ Social Proof")
    print("-" * 40)
    
    social = tracker.get_social_proof()
    print(f"\n👥 {social['total_premium_users']}+ usuarios premium")
    print(f"⭐ Rating {social['avg_rating']}/5")
    print(f"💰 €{social['total_savings_generated']:,} ahorrados en total")
    print(f"🏆 {social['top_hunters_premium_percent']}% de top hunters son premium")
    
    print("\n" + "="*60)
    print("✅ Testing Complete!")
    print("="*60 + "\n")
