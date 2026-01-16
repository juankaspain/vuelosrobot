#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Value Metrics Dashboard for Premium Conversion
IT6 - DAY 3/5

Features:
- Personal value dashboard showing generated value
- Comparative metrics (Free vs Premium)
- ROI calculator for premium upgrade
- Social proof integration
- Missed opportunities tracking
- Time savings calculation

Author: @Juanka_Spain
Version: 14.0.0-alpha.3
Date: 2026-01-16
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path


# ============================================================================
# CONSTANTS
# ============================================================================

# Average values for calculations
AVG_DEAL_SAVINGS = 150  # € per deal found
AVG_SEARCH_TIME = 15  # minutes per manual search
AVG_NOTIFICATION_DELAY_FREE = 120  # minutes for free users
AVG_NOTIFICATION_DELAY_PREMIUM = 5  # minutes for premium users

# Premium vs Free multipliers
PREMIUM_MULTIPLIERS = {
    "deals_per_month": 3.75,  # Premium users find 3.75x more deals
    "notification_speed": 24,  # 24x faster notifications
    "time_saved": 2.5,  # 2.5x time saved
    "missed_deals_reduction": 0.9  # 90% reduction in missed deals
}

# Social proof data (updated periodically)
SOCIAL_PROOF_DATA = {
    "premium_users_count": 892,
    "total_savings_generated": 156000,  # €
    "avg_premium_rating": 4.8,
    "top_hunters_premium_percent": 85,
    "avg_monthly_savings_premium": 1680,  # €
    "avg_monthly_savings_free": 450  # €
}


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class UserValueMetrics:
    """Track value generated for a user"""
    user_id: int
    total_searches: int = 0
    deals_found: int = 0
    deals_claimed: int = 0
    deals_missed: int = 0  # Due to free limits
    notifications_received: int = 0
    watchlist_alerts: int = 0
    groups_participated: int = 0
    referrals_successful: int = 0
    total_savings_shown: float = 0.0  # €
    estimated_actual_savings: float = 0.0  # € (claimed deals)
    time_on_platform: float = 0.0  # hours
    account_created: datetime = None
    is_premium: bool = False
    premium_since: Optional[datetime] = None
    
    def __post_init__(self):
        if self.account_created is None:
            self.account_created = datetime.now()
    
    @property
    def account_age_days(self) -> int:
        """Days since account creation"""
        return (datetime.now() - self.account_created).days
    
    @property
    def deal_claim_rate(self) -> float:
        """Percentage of deals actually claimed"""
        if self.deals_found == 0:
            return 0.0
        return (self.deals_claimed / self.deals_found) * 100
    
    @property
    def avg_savings_per_deal(self) -> float:
        """Average savings per deal found"""
        if self.deals_found == 0:
            return 0.0
        return self.total_savings_shown / self.deals_found
    
    @property
    def time_saved_hours(self) -> float:
        """Estimated time saved by using the platform"""
        # Each search saves ~15 min of manual searching
        return (self.total_searches * AVG_SEARCH_TIME) / 60
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['account_created'] = self.account_created.isoformat()
        if self.premium_since:
            data['premium_since'] = self.premium_since.isoformat()
        data['computed_metrics'] = {
            'account_age_days': self.account_age_days,
            'deal_claim_rate': self.deal_claim_rate,
            'avg_savings_per_deal': self.avg_savings_per_deal,
            'time_saved_hours': self.time_saved_hours
        }
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'UserValueMetrics':
        # Remove computed fields
        data.pop('computed_metrics', None)
        data['account_created'] = datetime.fromisoformat(data['account_created'])
        if data.get('premium_since'):
            data['premium_since'] = datetime.fromisoformat(data['premium_since'])
        return cls(**data)


@dataclass
class PremiumValueComparison:
    """Comparison of value between free and premium"""
    user_current_value: UserValueMetrics
    projected_premium_value: Dict
    roi_metrics: Dict
    missed_opportunities: Dict
    upgrade_benefits: List[str]


# ============================================================================
# VALUE TRACKER
# ============================================================================

class ValueTracker:
    """
    Tracks and calculates value generated for users.
    
    Used to demonstrate value and drive premium conversion by showing:
    - Total savings generated
    - Time saved
    - Deals missed due to free limits
    - ROI of premium upgrade
    """
    
    def __init__(self, data_dir: str = "."):
        self.data_dir = Path(data_dir)
        self.metrics_file = self.data_dir / "user_value_metrics.json"
        
        # Load data
        self.metrics: Dict[int, UserValueMetrics] = self._load_metrics()
        
        print("✅ ValueTracker initialized")
    
    # ========================================================================
    # DATA PERSISTENCE
    # ========================================================================
    
    def _load_metrics(self) -> Dict[int, UserValueMetrics]:
        """Load user value metrics from file"""
        if not self.metrics_file.exists():
            return {}
        
        try:
            with open(self.metrics_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {
                    int(user_id): UserValueMetrics.from_dict(metrics)
                    for user_id, metrics in data.items()
                }
        except Exception as e:
            print(f"⚠️ Error loading value metrics: {e}")
            return {}
    
    def _save_metrics(self):
        """Save user value metrics to file"""
        try:
            data = {
                str(user_id): metrics.to_dict()
                for user_id, metrics in self.metrics.items()
            }
            with open(self.metrics_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Error saving value metrics: {e}")
    
    # ========================================================================
    # TRACKING
    # ========================================================================
    
    def _get_or_create_metrics(self, user_id: int) -> UserValueMetrics:
        """Get or create user metrics"""
        if user_id not in self.metrics:
            self.metrics[user_id] = UserValueMetrics(user_id=user_id)
        return self.metrics[user_id]
    
    def track_search(self, user_id: int):
        """Track a search performed"""
        metrics = self._get_or_create_metrics(user_id)
        metrics.total_searches += 1
        self._save_metrics()
    
    def track_deal_found(self, user_id: int, savings_amount: float):
        """Track a deal found"""
        metrics = self._get_or_create_metrics(user_id)
        metrics.deals_found += 1
        metrics.total_savings_shown += savings_amount
        self._save_metrics()
    
    def track_deal_claimed(self, user_id: int, savings_amount: float):
        """Track a deal actually claimed/booked"""
        metrics = self._get_or_create_metrics(user_id)
        metrics.deals_claimed += 1
        metrics.estimated_actual_savings += savings_amount
        self._save_metrics()
    
    def track_deal_missed(self, user_id: int, reason: str = "free_limit"):
        """Track a deal missed due to free tier limitations"""
        metrics = self._get_or_create_metrics(user_id)
        metrics.deals_missed += 1
        self._save_metrics()
    
    def track_notification(self, user_id: int):
        """Track a notification sent"""
        metrics = self._get_or_create_metrics(user_id)
        metrics.notifications_received += 1
        self._save_metrics()
    
    def track_time_on_platform(self, user_id: int, duration_seconds: float):
        """Track time spent on platform"""
        metrics = self._get_or_create_metrics(user_id)
        metrics.time_on_platform += duration_seconds / 3600  # Convert to hours
        self._save_metrics()
    
    def set_premium_status(self, user_id: int, is_premium: bool):
        """Update user's premium status"""
        metrics = self._get_or_create_metrics(user_id)
        metrics.is_premium = is_premium
        if is_premium and not metrics.premium_since:
            metrics.premium_since = datetime.now()
        self._save_metrics()
    
    # ========================================================================
    # VALUE CALCULATION
    # ========================================================================
    
    def get_user_metrics(self, user_id: int) -> Optional[UserValueMetrics]:
        """Get user's value metrics"""
        return self.metrics.get(user_id)
    
    def calculate_premium_roi(self, user_id: int, premium_price_monthly: float = 9.99) -> Dict:
        """
        Calculate ROI of upgrading to premium.
        
        Returns:
            Dict with ROI calculations
        """
        metrics = self.get_user_metrics(user_id)
        if not metrics:
            return {}
        
        # Current monthly rate (extrapolate from account age)
        months_active = max(1, metrics.account_age_days / 30)
        deals_per_month_current = metrics.deals_found / months_active
        savings_per_month_current = metrics.total_savings_shown / months_active
        
        # Projected with premium (using multipliers)
        deals_per_month_premium = deals_per_month_current * PREMIUM_MULTIPLIERS["deals_per_month"]
        savings_per_month_premium = savings_per_month_current * PREMIUM_MULTIPLIERS["deals_per_month"]
        
        # Additional savings with premium
        additional_savings_monthly = savings_per_month_premium - savings_per_month_current
        
        # ROI calculation
        roi = (additional_savings_monthly / premium_price_monthly) if premium_price_monthly > 0 else 0
        payback_deals = premium_price_monthly / AVG_DEAL_SAVINGS if AVG_DEAL_SAVINGS > 0 else 0
        
        # Deals missed that could be recovered
        recoverable_deals = metrics.deals_missed
        recoverable_savings = recoverable_deals * AVG_DEAL_SAVINGS
        
        return {
            'premium_cost_monthly': premium_price_monthly,
            'current_savings_monthly': savings_per_month_current,
            'premium_savings_monthly': savings_per_month_premium,
            'additional_savings_monthly': additional_savings_monthly,
            'roi_multiplier': roi,
            'roi_percent': (roi - 1) * 100,
            'payback_in_deals': payback_deals,
            'deals_missed': metrics.deals_missed,
            'recoverable_savings': recoverable_savings,
            'breakeven_days': 30 / roi if roi > 0 else 999
        }
    
    def calculate_missed_opportunities(self, user_id: int) -> Dict:
        """
        Calculate opportunities missed due to free tier limits.
        
        Returns:
            Dict with missed opportunity metrics
        """
        metrics = self.get_user_metrics(user_id)
        if not metrics:
            return {}
        
        # Estimate deals missed
        deals_missed = metrics.deals_missed
        estimated_missed_savings = deals_missed * AVG_DEAL_SAVINGS
        
        # Notification delays causing missed deals
        # Assume 20% of deals expire within 2 hours
        delay_minutes = AVG_NOTIFICATION_DELAY_FREE - AVG_NOTIFICATION_DELAY_PREMIUM
        notification_based_misses = int(metrics.notifications_received * 0.2)
        notification_missed_savings = notification_based_misses * AVG_DEAL_SAVINGS
        
        # Watchlist limitations
        # Free: 3 slots, Premium: unlimited
        # Estimate 1 deal missed per month per slot needed
        months = max(1, metrics.account_age_days / 30)
        watchlist_slots_needed = metrics.watchlist_alerts / months if months > 0 else 0
        watchlist_missed_deals = max(0, (watchlist_slots_needed - 3) * months)
        watchlist_missed_savings = watchlist_missed_deals * AVG_DEAL_SAVINGS
        
        total_missed_savings = (
            estimated_missed_savings + 
            notification_missed_savings + 
            watchlist_missed_savings
        )
        
        return {
            'direct_deals_missed': deals_missed,
            'direct_missed_savings': estimated_missed_savings,
            'notification_delay_misses': notification_based_misses,
            'notification_missed_savings': notification_missed_savings,
            'watchlist_limited_misses': int(watchlist_missed_deals),
            'watchlist_missed_savings': watchlist_missed_savings,
            'total_opportunities_missed': deals_missed + notification_based_misses + int(watchlist_missed_deals),
            'total_missed_savings': total_missed_savings
        }
    
    # ========================================================================
    # DASHBOARD GENERATION
    # ========================================================================
    
    def generate_personal_dashboard(self, user_id: int) -> Dict:
        """
        Generate personal value dashboard for user.
        
        Returns:
            Dict with all dashboard data
        """
        metrics = self.get_user_metrics(user_id)
        if not metrics:
            return {'error': 'No metrics found'}
        
        roi = self.calculate_premium_roi(user_id)
        missed = self.calculate_missed_opportunities(user_id)
        
        return {
            'user_id': user_id,
            'is_premium': metrics.is_premium,
            'account_age_days': metrics.account_age_days,
            'value_generated': {
                'total_savings_shown': metrics.total_savings_shown,
                'actual_savings': metrics.estimated_actual_savings,
                'time_saved_hours': metrics.time_saved_hours,
                'deals_found': metrics.deals_found,
                'deals_claimed': metrics.deals_claimed,
                'claim_rate': metrics.deal_claim_rate
            },
            'engagement': {
                'total_searches': metrics.total_searches,
                'notifications': metrics.notifications_received,
                'groups': metrics.groups_participated,
                'referrals': metrics.referrals_successful,
                'platform_time_hours': metrics.time_on_platform
            },
            'roi_analysis': roi,
            'missed_opportunities': missed,
            'premium_comparison': self._generate_comparison_table(metrics)
        }
    
    def _generate_comparison_table(self, metrics: UserValueMetrics) -> Dict:
        """
        Generate Free vs Premium comparison.
        
        Returns:
            Dict with comparison metrics
        """
        months = max(1, metrics.account_age_days / 30)
        
        # Current (free) rates
        deals_per_month_free = metrics.deals_found / months
        savings_per_month_free = metrics.total_savings_shown / months
        
        # Projected premium rates
        deals_per_month_premium = deals_per_month_free * PREMIUM_MULTIPLIERS["deals_per_month"]
        savings_per_month_premium = savings_per_month_free * PREMIUM_MULTIPLIERS["deals_per_month"]
        
        return {
            'deals_per_month': {
                'free': round(deals_per_month_free, 1),
                'premium': round(deals_per_month_premium, 1),
                'improvement': f"+{round((PREMIUM_MULTIPLIERS['deals_per_month'] - 1) * 100)}%"
            },
            'savings_per_month': {
                'free': round(savings_per_month_free),
                'premium': round(savings_per_month_premium),
                'improvement': f"+{round((PREMIUM_MULTIPLIERS['deals_per_month'] - 1) * 100)}%"
            },
            'notification_speed': {
                'free': f"{AVG_NOTIFICATION_DELAY_FREE} min",
                'premium': f"{AVG_NOTIFICATION_DELAY_PREMIUM} min",
                'improvement': f"{PREMIUM_MULTIPLIERS['notification_speed']}x faster"
            },
            'deals_missed': {
                'free': metrics.deals_missed,
                'premium': 0,
                'improvement': "-100%"
            }
        }
    
    # ========================================================================
    # SOCIAL PROOF
    # ========================================================================
    
    def get_social_proof(self) -> Dict:
        """Get social proof data for marketing"""
        return SOCIAL_PROOF_DATA.copy()
    
    def get_user_percentile(self, user_id: int) -> Dict:
        """
        Calculate user's percentile vs other users.
        
        Returns:
            Dict with percentile rankings
        """
        metrics = self.get_user_metrics(user_id)
        if not metrics or len(self.metrics) < 2:
            return {}
        
        all_savings = sorted([m.total_savings_shown for m in self.metrics.values()], reverse=True)
        all_deals = sorted([m.deals_found for m in self.metrics.values()], reverse=True)
        
        savings_rank = all_savings.index(metrics.total_savings_shown) + 1
        deals_rank = all_deals.index(metrics.deals_found) + 1
        
        savings_percentile = 100 - (savings_rank / len(all_savings) * 100)
        deals_percentile = 100 - (deals_rank / len(all_deals) * 100)
        
        return {
            'savings_percentile': round(savings_percentile, 1),
            'deals_percentile': round(deals_percentile, 1),
            'savings_rank': savings_rank,
            'deals_rank': deals_rank,
            'total_users': len(self.metrics)
        }
    
    # ========================================================================
    # AGGREGATE STATS
    # ========================================================================
    
    def get_platform_stats(self) -> Dict:
        """Get aggregate platform statistics"""
        if not self.metrics:
            return {}
        
        all_metrics = list(self.metrics.values())
        premium_metrics = [m for m in all_metrics if m.is_premium]
        free_metrics = [m for m in all_metrics if not m.is_premium]
        
        return {
            'total_users': len(all_metrics),
            'premium_users': len(premium_metrics),
            'free_users': len(free_metrics),
            'total_savings_generated': sum(m.total_savings_shown for m in all_metrics),
            'total_deals_found': sum(m.deals_found for m in all_metrics),
            'avg_savings_per_user': sum(m.total_savings_shown for m in all_metrics) / len(all_metrics),
            'premium_avg_savings': sum(m.total_savings_shown for m in premium_metrics) / len(premium_metrics) if premium_metrics else 0,
            'free_avg_savings': sum(m.total_savings_shown for m in free_metrics) / len(free_metrics) if free_metrics else 0
        }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def format_value_dashboard(dashboard: Dict) -> str:
    """
    Format value dashboard for display.
    
    Args:
        dashboard: Dict from generate_personal_dashboard()
    
    Returns:
        Formatted dashboard string
    """
    if 'error' in dashboard:
        return f"⚠️ {dashboard['error']}"
    
    value = dashboard['value_generated']
    roi = dashboard['roi_analysis']
    missed = dashboard['missed_opportunities']
    comp = dashboard['premium_comparison']
    
    output = f"""📊 Tu Dashboard de Valor

💰 Valor Generado:
• Ahorro total mostrado: €{value['total_savings_shown']:,.0f}
• Ahorro real estimado: €{value['actual_savings']:,.0f}
• Tiempo ahorrado: {value['time_saved_hours']:.1f} horas
• Chollos encontrados: {value['deals_found']}
• Chollos aprovechados: {value['deals_claimed']} ({value['claim_rate']:.0f}%)

"""
    
    if not dashboard['is_premium']:
        output += f"""🔥 Oportunidades Perdidas:
• Chollos perdidos: {missed['total_opportunities_missed']}
• Ahorro perdido: €{missed['total_missed_savings']:,.0f}
• Por límites free: {missed['direct_deals_missed']}
• Por notif lentas: {missed['notification_delay_misses']}
• Por watchlist limitado: {missed['watchlist_limited_misses']}

💸 ROI de Premium:
• Costo mensual: €{roi['premium_cost_monthly']}
• Ahorro adicional/mes: €{roi['additional_savings_monthly']:,.0f}
• ROI: {roi['roi_multiplier']:.0f}x ({roi['roi_percent']:.0f}%)
• Se paga en: {roi['payback_in_deals']:.1f} chollos
• Breakeven en: {roi['breakeven_days']:.0f} días

🎯 Free vs Premium:
• Chollos/mes: {comp['deals_per_month']['free']} → {comp['deals_per_month']['premium']} ({comp['deals_per_month']['improvement']})
• Ahorro/mes: €{comp['savings_per_month']['free']} → €{comp['savings_per_month']['premium']} ({comp['savings_per_month']['improvement']})
• Velocidad notif: {comp['notification_speed']['free']} → {comp['notification_speed']['premium']} ({comp['notification_speed']['improvement']})

💡 Con Premium habrías ahorrado €{missed['total_missed_savings']:,.0f} más!
"""
    else:
        output += f"""
💎 Eres Usuario Premium

✅ Búsquedas ilimitadas
✅ Watchlist sin límites  
✅ Notificaciones instantáneas
✅ 0 chollos perdidos
"""
    
    return output


# ============================================================================
# MAIN (TESTING)
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("📈 TESTING: Value Metrics Dashboard")
    print("="*60 + "\n")
    
    # Initialize tracker
    tracker = ValueTracker()
    
    test_user = 11111
    
    print("1️⃣ Tracking User Activity")
    print("-" * 40)
    
    # Simulate activity
    for i in range(15):
        tracker.track_search(test_user)
    
    tracker.track_deal_found(test_user, 180)
    tracker.track_deal_found(test_user, 220)
    tracker.track_deal_found(test_user, 150)
    tracker.track_deal_claimed(test_user, 180)
    tracker.track_deal_claimed(test_user, 150)
    
    tracker.track_deal_missed(test_user)
    tracker.track_deal_missed(test_user)
    
    for i in range(8):
        tracker.track_notification(test_user)
    
    tracker.track_time_on_platform(test_user, 3600 * 2.5)
    
    print("✅ Activity tracked")
    
    print("\n2️⃣ Personal Dashboard")
    print("-" * 40)
    
    dashboard = tracker.generate_personal_dashboard(test_user)
    print(format_value_dashboard(dashboard))
    
    print("\n3️⃣ ROI Calculation")
    print("-" * 40)
    
    roi = tracker.calculate_premium_roi(test_user)
    print(f"Premium cost: €{roi['premium_cost_monthly']}")
    print(f"Additional savings: €{roi['additional_savings_monthly']:.0f}/mes")
    print(f"ROI: {roi['roi_multiplier']:.0f}x")
    print(f"Payback in {roi['payback_in_deals']:.1f} deals")
    
    print("\n4️⃣ Missed Opportunities")
    print("-" * 40)
    
    missed = tracker.calculate_missed_opportunities(test_user)
    print(f"Total opportunities missed: {missed['total_opportunities_missed']}")
    print(f"Total savings missed: €{missed['total_missed_savings']:.0f}")
    print(f"  • Direct: {missed['direct_deals_missed']} (€{missed['direct_missed_savings']:.0f})")
    print(f"  • Notifications: {missed['notification_delay_misses']} (€{missed['notification_missed_savings']:.0f})")
    print(f"  • Watchlist: {missed['watchlist_limited_misses']} (€{missed['watchlist_missed_savings']:.0f})")
    
    print("\n5️⃣ Social Proof")
    print("-" * 40)
    
    social = tracker.get_social_proof()
    print(f"Premium users: {social['premium_users_count']}")
    print(f"Total savings: €{social['total_savings_generated']:,}")
    print(f"Rating: {social['avg_premium_rating']}/5 ⭐")
    print(f"Top hunters premium: {social['top_hunters_premium_percent']}%")
    
    print("\n" + "="*60)
    print("✅ Testing Complete!")
    print("="*60 + "\n")
