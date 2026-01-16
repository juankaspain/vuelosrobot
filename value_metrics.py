#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Value Metrics Dashboard for Upgrade Conversion
IT6 - DAY 3/5

Features:
- Personal value tracking (savings, time, deals)
- Comparative metrics (Free vs Premium users)
- ROI calculator for premium subscription
- Social proof integration
- Value-based upgrade triggers

Author: @Juanka_Spain
Version: 14.0.0-alpha.3
Date: 2026-01-16
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import statistics


# ============================================================================
# CONSTANTS
# ============================================================================

# Average savings per deal by route type
AVG_SAVINGS = {
    "domestic": 45,      # €45 avg on domestic flights
    "europe": 120,       # €120 avg on European flights
    "international": 280 # €280 avg on long-haul
}

# Time saved per action (minutes)
TIME_SAVED = {
    "search": 5,         # 5 min saved per search vs manual
    "deal_found": 15,    # 15 min saved finding a deal
    "notification": 30   # 30 min saved by instant notification
}

# Premium benchmarks (from top users)
PREMIUM_BENCHMARKS = {
    "deals_per_month": 45,
    "savings_per_month": 1680,
    "response_time_minutes": 5,
    "deals_missed": 0,
    "avg_session_duration": 8  # minutes
}

# Free user benchmarks
FREE_BENCHMARKS = {
    "deals_per_month": 12,
    "savings_per_month": 450,
    "response_time_minutes": 120,  # 2 hours
    "deals_missed": 8,
    "avg_session_duration": 12  # minutes (more time = less efficient)
}

# Social proof data (would be real in production)
SOCIAL_PROOF = {
    "premium_users": 892,
    "avg_rating": 4.8,
    "total_savings_generated": 156000,
    "top_hunters_premium_percent": 85,
    "avg_monthly_savings_premium": 1680,
    "testimonials": [
        {
            "user": "@travel_enthusiast",
            "text": "Ahorré €2,450 en 3 meses. Premium se paga solo.",
            "savings": 2450,
            "months": 3
        },
        {
            "user": "@budget_traveler",
            "text": "Las notificaciones instantáneas valen oro. Ya no pierdo chollos.",
            "savings": 1820,
            "months": 2
        },
        {
            "user": "@family_trips",
            "text": "Con 4 personas viajando, el ahorro es brutal. Mejor inversión.",
            "savings": 3200,
            "months": 4
        }
    ]
}


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class UserValue:
    """Track user's generated value"""
    user_id: int
    total_savings: float  # Total € saved
    time_saved_minutes: float  # Total minutes saved
    deals_found: int
    deals_missed: int  # Due to free limits
    searches_made: int
    notifications_received: int
    created_at: datetime
    last_updated: datetime
    is_premium: bool = False
    
    @property
    def time_saved_hours(self) -> float:
        """Time saved in hours"""
        return self.time_saved_minutes / 60
    
    @property
    def avg_savings_per_deal(self) -> float:
        """Average savings per deal found"""
        if self.deals_found == 0:
            return 0
        return self.total_savings / self.deals_found
    
    @property
    def missed_value(self) -> float:
        """Estimated value of missed deals"""
        return self.deals_missed * self.avg_savings_per_deal if self.avg_savings_per_deal > 0 else self.deals_missed * 150
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['last_updated'] = self.last_updated.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'UserValue':
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['last_updated'] = datetime.fromisoformat(data['last_updated'])
        return cls(**data)


@dataclass
class ComparativeMetrics:
    """Comparison between user and benchmarks"""
    user_deals_month: int
    benchmark_deals_month: int
    user_savings_month: float
    benchmark_savings_month: float
    user_response_time: float
    benchmark_response_time: float
    deals_missed: int
    
    @property
    def deals_delta_percent(self) -> float:
        """% difference in deals found"""
        if self.user_deals_month == 0:
            return 0
        return ((self.benchmark_deals_month - self.user_deals_month) / self.user_deals_month) * 100
    
    @property
    def savings_delta_percent(self) -> float:
        """% difference in savings"""
        if self.user_savings_month == 0:
            return 0
        return ((self.benchmark_savings_month - self.user_savings_month) / self.user_savings_month) * 100
    
    @property
    def response_time_multiplier(self) -> float:
        """How many times faster is premium"""
        if self.benchmark_response_time == 0:
            return 0
        return self.user_response_time / self.benchmark_response_time


@dataclass
class ROICalculation:
    """ROI calculation for premium subscription"""
    monthly_cost: float  # €9.99
    current_monthly_savings: float
    premium_monthly_savings: float  # Estimated with premium
    months_analyzed: int
    
    @property
    def additional_savings(self) -> float:
        """Additional savings with premium per month"""
        return self.premium_monthly_savings - self.current_monthly_savings
    
    @property
    def net_benefit_monthly(self) -> float:
        """Net benefit per month after premium cost"""
        return self.additional_savings - self.monthly_cost
    
    @property
    def roi_percent(self) -> float:
        """ROI percentage"""
        if self.monthly_cost == 0:
            return 0
        return (self.net_benefit_monthly / self.monthly_cost) * 100
    
    @property
    def roi_multiplier(self) -> float:
        """ROI as multiplier (e.g., 68x)"""
        if self.monthly_cost == 0:
            return 0
        return self.additional_savings / self.monthly_cost
    
    @property
    def payback_days(self) -> int:
        """Days to recover premium cost"""
        if self.additional_savings == 0:
            return 999
        daily_benefit = self.additional_savings / 30
        return int(self.monthly_cost / daily_benefit)


# ============================================================================
# VALUE TRACKER
# ============================================================================

class ValueTracker:
    """
    Tracks and displays user value to drive premium upgrades.
    
    Features:
    - Personal value tracking (savings, time, deals)
    - Comparative metrics vs benchmarks
    - ROI calculator
    - Social proof display
    - Value-based triggers
    """
    
    def __init__(self, data_dir: str = "."):
        self.data_dir = Path(data_dir)
        self.value_file = self.data_dir / "user_value_metrics.json"
        
        # Load data
        self.user_values: Dict[int, UserValue] = self._load_values()
        
        print("✅ ValueTracker initialized")
    
    # ========================================================================
    # DATA PERSISTENCE
    # ========================================================================
    
    def _load_values(self) -> Dict[int, UserValue]:
        """Load user value data from file"""
        if not self.value_file.exists():
            return {}
        
        try:
            with open(self.value_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {
                    int(user_id): UserValue.from_dict(value)
                    for user_id, value in data.items()
                }
        except Exception as e:
            print(f"⚠️ Error loading values: {e}")
            return {}
    
    def _save_values(self):
        """Save user value data to file"""
        try:
            data = {
                str(user_id): value.to_dict()
                for user_id, value in self.user_values.items()
            }
            with open(self.value_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Error saving values: {e}")
    
    # ========================================================================
    # VALUE TRACKING
    # ========================================================================
    
    def _get_or_create_value(self, user_id: int) -> UserValue:
        """Get or create user value record"""
        if user_id not in self.user_values:
            self.user_values[user_id] = UserValue(
                user_id=user_id,
                total_savings=0,
                time_saved_minutes=0,
                deals_found=0,
                deals_missed=0,
                searches_made=0,
                notifications_received=0,
                created_at=datetime.now(),
                last_updated=datetime.now()
            )
        return self.user_values[user_id]
    
    def track_search(self, user_id: int):
        """Track a search performed"""
        value = self._get_or_create_value(user_id)
        value.searches_made += 1
        value.time_saved_minutes += TIME_SAVED['search']
        value.last_updated = datetime.now()
        self._save_values()
    
    def track_deal_found(self, user_id: int, savings: float, route_type: str = "europe"):
        """Track a deal found"""
        value = self._get_or_create_value(user_id)
        value.deals_found += 1
        value.total_savings += savings
        value.time_saved_minutes += TIME_SAVED['deal_found']
        value.last_updated = datetime.now()
        self._save_values()
    
    def track_deal_missed(self, user_id: int, reason: str = "limit"):
        """Track a deal missed due to free limits"""
        value = self._get_or_create_value(user_id)
        value.deals_missed += 1
        value.last_updated = datetime.now()
        self._save_values()
    
    def track_notification(self, user_id: int):
        """Track a notification received"""
        value = self._get_or_create_value(user_id)
        value.notifications_received += 1
        value.time_saved_minutes += TIME_SAVED['notification']
        value.last_updated = datetime.now()
        self._save_values()
    
    def set_premium_status(self, user_id: int, is_premium: bool):
        """Update user's premium status"""
        value = self._get_or_create_value(user_id)
        value.is_premium = is_premium
        value.last_updated = datetime.now()
        self._save_values()
    
    # ========================================================================
    # COMPARATIVE METRICS
    # ========================================================================
    
    def get_comparative_metrics(self, user_id: int) -> ComparativeMetrics:
        """
        Get user metrics compared to benchmark.
        
        Returns:
            ComparativeMetrics comparing user to premium users
        """
        value = self._get_or_create_value(user_id)
        
        # Calculate monthly averages
        days_active = (datetime.now() - value.created_at).days or 1
        months_active = days_active / 30
        
        user_deals_month = int(value.deals_found / months_active) if months_active > 0 else value.deals_found
        user_savings_month = value.total_savings / months_active if months_active > 0 else value.total_savings
        
        # Estimate user response time based on notification usage
        if value.is_premium:
            user_response_time = PREMIUM_BENCHMARKS['response_time_minutes']
        else:
            user_response_time = FREE_BENCHMARKS['response_time_minutes']
        
        return ComparativeMetrics(
            user_deals_month=user_deals_month,
            benchmark_deals_month=PREMIUM_BENCHMARKS['deals_per_month'],
            user_savings_month=user_savings_month,
            benchmark_savings_month=PREMIUM_BENCHMARKS['savings_per_month'],
            user_response_time=user_response_time,
            benchmark_response_time=PREMIUM_BENCHMARKS['response_time_minutes'],
            deals_missed=value.deals_missed
        )
    
    # ========================================================================
    # ROI CALCULATOR
    # ========================================================================
    
    def calculate_roi(self, user_id: int, monthly_cost: float = 9.99) -> ROICalculation:
        """
        Calculate ROI of premium subscription for user.
        
        Args:
            user_id: User ID
            monthly_cost: Cost of premium (default €9.99)
        
        Returns:
            ROICalculation with detailed ROI metrics
        """
        value = self._get_or_create_value(user_id)
        
        # Calculate current monthly savings
        days_active = (datetime.now() - value.created_at).days or 1
        months_active = days_active / 30
        current_monthly_savings = value.total_savings / months_active if months_active > 0 else 0
        
        # Estimate premium savings (based on benchmarks)
        # Premium users find more deals + don't miss any
        deals_ratio = PREMIUM_BENCHMARKS['deals_per_month'] / max(1, FREE_BENCHMARKS['deals_per_month'])
        missed_value_monthly = (value.deals_missed / months_active) * (value.avg_savings_per_deal or 150) if months_active > 0 else 0
        
        premium_monthly_savings = (current_monthly_savings * deals_ratio) + missed_value_monthly
        
        return ROICalculation(
            monthly_cost=monthly_cost,
            current_monthly_savings=current_monthly_savings,
            premium_monthly_savings=premium_monthly_savings,
            months_analyzed=int(months_active)
        )
    
    # ========================================================================
    # DASHBOARD GENERATION
    # ========================================================================
    
    def get_personal_dashboard(self, user_id: int) -> Dict:
        """
        Generate personal value dashboard.
        
        Returns:
            Dict with all dashboard data
        """
        value = self._get_or_create_value(user_id)
        comparative = self.get_comparative_metrics(user_id)
        roi = self.calculate_roi(user_id)
        
        return {
            'personal': {
                'total_savings': value.total_savings,
                'time_saved_hours': value.time_saved_hours,
                'deals_found': value.deals_found,
                'deals_missed': value.deals_missed,
                'searches_made': value.searches_made,
                'avg_savings_per_deal': value.avg_savings_per_deal,
                'missed_value': value.missed_value
            },
            'comparative': {
                'your_deals_month': comparative.user_deals_month,
                'premium_deals_month': comparative.benchmark_deals_month,
                'deals_delta_percent': comparative.deals_delta_percent,
                'your_savings_month': comparative.user_savings_month,
                'premium_savings_month': comparative.benchmark_savings_month,
                'savings_delta_percent': comparative.savings_delta_percent,
                'response_time_multiplier': comparative.response_time_multiplier
            },
            'roi': {
                'monthly_cost': roi.monthly_cost,
                'additional_savings': roi.additional_savings,
                'net_benefit_monthly': roi.net_benefit_monthly,
                'roi_percent': roi.roi_percent,
                'roi_multiplier': roi.roi_multiplier,
                'payback_days': roi.payback_days
            },
            'social_proof': SOCIAL_PROOF
        }
    
    # ========================================================================
    # UPGRADE TRIGGERS
    # ========================================================================
    
    def should_show_value_dashboard(self, user_id: int) -> Tuple[bool, str]:
        """
        Determine if value dashboard should be shown.
        
        Returns:
            (should_show, reason)
        """
        value = self._get_or_create_value(user_id)
        
        # Don't show to premium users
        if value.is_premium:
            return False, "User is premium"
        
        # Show after finding 3+ deals
        if value.deals_found >= 3:
            return True, "3+ deals found - show value"
        
        # Show after missing 2+ deals
        if value.deals_missed >= 2:
            return True, "2+ deals missed - show opportunity cost"
        
        # Show after €500 in savings shown
        if value.total_savings >= 500:
            return True, "High value demonstrated"
        
        # Show after 30+ searches (power user)
        if value.searches_made >= 30:
            return True, "Power user - show efficiency gains"
        
        return False, "Not enough engagement yet"
    
    # ========================================================================
    # ANALYTICS
    # ========================================================================
    
    def get_aggregate_stats(self) -> Dict:
        """Get aggregate statistics across all users"""
        if not self.user_values:
            return {}
        
        all_savings = [v.total_savings for v in self.user_values.values()]
        all_deals = [v.deals_found for v in self.user_values.values()]
        premium_users = [v for v in self.user_values.values() if v.is_premium]
        free_users = [v for v in self.user_values.values() if not v.is_premium]
        
        return {
            'total_users': len(self.user_values),
            'premium_users': len(premium_users),
            'free_users': len(free_users),
            'total_savings_generated': sum(all_savings),
            'avg_savings_per_user': statistics.mean(all_savings) if all_savings else 0,
            'median_savings': statistics.median(all_savings) if all_savings else 0,
            'total_deals_found': sum(all_deals),
            'avg_deals_per_user': statistics.mean(all_deals) if all_deals else 0,
            'premium_avg_savings': statistics.mean([v.total_savings for v in premium_users]) if premium_users else 0,
            'free_avg_savings': statistics.mean([v.total_savings for v in free_users]) if free_users else 0
        }


# ============================================================================
# FORMATTING HELPERS
# ============================================================================

def format_value_dashboard(dashboard: Dict) -> str:
    """
    Format value dashboard for Telegram display.
    
    Args:
        dashboard: Dict from get_personal_dashboard()
    
    Returns:
        Formatted message string
    """
    personal = dashboard['personal']
    comparative = dashboard['comparative']
    roi = dashboard['roi']
    social = dashboard['social_proof']
    
    message = f"""📊 Tu Valor Generado

💰 Ahorro Total: €{personal['total_savings']:.0f}
⏱️ Tiempo Ahorrado: {personal['time_saved_hours']:.1f} horas
🔥 Chollos Encontrados: {personal['deals_found']}
❌ Chollos Perdidos: {personal['deals_missed']} (por límites free)

📉 Valor Perdido: €{personal['missed_value']:.0f}

────────────────────

🎯 Comparativa Free vs Premium

| Métrica | Tú (Free) | Premium | Diferencia |
|---------|-----------|---------|------------|
| Chollos/mes | {comparative['your_deals_month']} | {comparative['premium_deals_month']} | +{comparative['deals_delta_percent']:.0f}% |
| Ahorro/mes | €{comparative['your_savings_month']:.0f} | €{comparative['premium_savings_month']:.0f} | +{comparative['savings_delta_percent']:.0f}% |
| Tiempo respuesta | {comparative['response_time_multiplier']:.0f}x más lento | Instantáneo | {comparative['response_time_multiplier']:.0f}x faster |

────────────────────

💡 Con Premium:
• +{comparative['premium_deals_month'] - comparative['your_deals_month']} chollos más al mes
• +€{comparative['premium_savings_month'] - comparative['your_savings_month']:.0f} ahorro adicional
• 0 chollos perdidos
• Notificaciones instantáneas

💸 ROI Premium: {roi['roi_multiplier']:.0f}x en tu primer mes
• Costo: €{roi['monthly_cost']:.2f}/mes
• Ahorro adicional: +€{roi['additional_savings']:.0f}
• Beneficio neto: +€{roi['net_benefit_monthly']:.0f}/mes
• Recuperas inversión en: {roi['payback_days']} días

────────────────────

👥 {social['premium_users']}+ usuarios premium
⭐ Rating {social['avg_rating']}/5
💰 €{social['total_savings_generated']:,} ahorrados en total
🏆 {social['top_hunters_premium_percent']}% de top hunters son premium
"""
    
    return message


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
    for i in range(15):
        tracker.track_search(test_user)
    
    tracker.track_deal_found(test_user, 120, "europe")
    tracker.track_deal_found(test_user, 280, "international")
    tracker.track_deal_found(test_user, 45, "domestic")
    tracker.track_deal_found(test_user, 150, "europe")
    
    tracker.track_deal_missed(test_user)
    tracker.track_deal_missed(test_user)
    
    for i in range(8):
        tracker.track_notification(test_user)
    
    print("✅ Activity tracked")
    
    print("\n2️⃣ Personal Dashboard")
    print("-" * 40)
    
    dashboard = tracker.get_personal_dashboard(test_user)
    print(format_value_dashboard(dashboard))
    
    print("\n3️⃣ Upgrade Trigger Check")
    print("-" * 40)
    
    should_show, reason = tracker.should_show_value_dashboard(test_user)
    print(f"Show dashboard: {should_show}")
    print(f"Reason: {reason}")
    
    print("\n4️⃣ Aggregate Stats")
    print("-" * 40)
    
    stats = tracker.get_aggregate_stats()
    print(f"Total users: {stats['total_users']}")
    print(f"Total savings: €{stats['total_savings_generated']:.0f}")
    print(f"Avg savings/user: €{stats['avg_savings_per_user']:.0f}")
    print(f"Total deals: {stats['total_deals_found']}")
    
    print("\n" + "="*60)
    print("✅ Testing Complete!")
    print("="*60 + "\n")
