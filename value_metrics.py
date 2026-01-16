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
- Missed opportunity tracking
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


# ============================================================================
# CONSTANTS
# ============================================================================

# Average values for calculations
AVG_DEAL_SAVINGS = 150  # € per deal
AVG_SEARCH_TIME = 15  # minutes per manual search
AVG_PREMIUM_DEALS_MULTIPLIER = 2.75  # Premium users find 2.75x more deals
AVG_NOTIFICATION_SPEED_MULTIPLIER = 24  # 24x faster notifications

# Premium pricing (for ROI calculations)
PREMIUM_MONTHLY_PRICE = 9.99
PREMIUM_ANNUAL_PRICE = 99.99

# Social proof data (updated periodically)
SOCIAL_PROOF = {
    "premium_users": 892,
    "total_savings_generated": 156000,  # €
    "avg_rating": 4.8,
    "top_hunters_premium_percent": 85,
    "avg_deals_per_premium_user": 45,  # per month
    "avg_savings_per_premium_user": 1680  # € per month
}


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class UserValue:
    """Track value generated for a user"""
    user_id: int
    registration_date: datetime
    is_premium: bool = False
    
    # Deals
    total_deals_found: int = 0
    deals_claimed: int = 0
    deals_missed: int = 0  # Due to free limits
    
    # Savings
    total_savings_generated: float = 0.0  # €
    potential_savings_missed: float = 0.0  # € (from missed deals)
    
    # Time
    total_searches: int = 0
    time_saved_minutes: float = 0.0  # vs manual searching
    
    # Engagement
    watchlist_routes: int = 0
    notifications_received: int = 0
    groups_joined: int = 0
    referrals_made: int = 0
    
    # Premium value (if premium)
    premium_since: Optional[datetime] = None
    premium_spent: float = 0.0  # €
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['registration_date'] = self.registration_date.isoformat()
        if self.premium_since:
            data['premium_since'] = self.premium_since.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'UserValue':
        data['registration_date'] = datetime.fromisoformat(data['registration_date'])
        if data.get('premium_since'):
            data['premium_since'] = datetime.fromisoformat(data['premium_since'])
        return cls(**data)


@dataclass
class ValueSnapshot:
    """Snapshot of value at a point in time (for trend analysis)"""
    timestamp: datetime
    total_savings: float
    deals_found: int
    time_saved: float
    
    def to_dict(self) -> Dict:
        return {
            'timestamp': self.timestamp.isoformat(),
            'total_savings': self.total_savings,
            'deals_found': self.deals_found,
            'time_saved': self.time_saved
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ValueSnapshot':
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class MissedOpportunity:
    """Record of a deal missed due to free limits"""
    user_id: int
    timestamp: datetime
    reason: str  # "search_limit", "watchlist_full", "notification_delay"
    deal_value: float  # Estimated savings missed
    route: str
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'MissedOpportunity':
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


# ============================================================================
# VALUE TRACKER
# ============================================================================

class ValueTracker:
    """
    Tracks and calculates value generated for users.
    Used to demonstrate ROI and trigger premium upgrades.
    """
    
    def __init__(self, data_dir: str = "."):
        self.data_dir = Path(data_dir)
        self.value_file = self.data_dir / "user_value_metrics.json"
        self.snapshots_file = self.data_dir / "value_snapshots.json"
        self.missed_file = self.data_dir / "missed_opportunities.json"
        
        # Load data
        self.user_values: Dict[int, UserValue] = self._load_values()
        self.snapshots: Dict[int, List[ValueSnapshot]] = self._load_snapshots()
        self.missed: Dict[int, List[MissedOpportunity]] = self._load_missed()
        
        print("✅ ValueTracker initialized")
    
    # ========================================================================
    # DATA PERSISTENCE
    # ========================================================================
    
    def _load_values(self) -> Dict[int, UserValue]:
        """Load user value data"""
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
        """Save user value data"""
        try:
            data = {
                str(user_id): value.to_dict()
                for user_id, value in self.user_values.items()
            }
            with open(self.value_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Error saving values: {e}")
    
    def _load_snapshots(self) -> Dict[int, List[ValueSnapshot]]:
        """Load value snapshots"""
        if not self.snapshots_file.exists():
            return {}
        
        try:
            with open(self.snapshots_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {
                    int(user_id): [ValueSnapshot.from_dict(s) for s in snapshots]
                    for user_id, snapshots in data.items()
                }
        except Exception as e:
            print(f"⚠️ Error loading snapshots: {e}")
            return {}
    
    def _save_snapshots(self):
        """Save value snapshots"""
        try:
            data = {
                str(user_id): [s.to_dict() for s in snapshots]
                for user_id, snapshots in self.snapshots.items()
            }
            with open(self.snapshots_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Error saving snapshots: {e}")
    
    def _load_missed(self) -> Dict[int, List[MissedOpportunity]]:
        """Load missed opportunities"""
        if not self.missed_file.exists():
            return {}
        
        try:
            with open(self.missed_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {
                    int(user_id): [MissedOpportunity.from_dict(m) for m in missed]
                    for user_id, missed in data.items()
                }
        except Exception as e:
            print(f"⚠️ Error loading missed: {e}")
            return {}
    
    def _save_missed(self):
        """Save missed opportunities"""
        try:
            data = {
                str(user_id): [m.to_dict() for m in missed]
                for user_id, missed in self.missed.items()
            }
            with open(self.missed_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Error saving missed: {e}")
    
    # ========================================================================
    # USER VALUE TRACKING
    # ========================================================================
    
    def _get_or_create_value(self, user_id: int) -> UserValue:
        """Get or create user value record"""
        if user_id not in self.user_values:
            self.user_values[user_id] = UserValue(
                user_id=user_id,
                registration_date=datetime.now()
            )
        return self.user_values[user_id]
    
    def track_deal_found(self, user_id: int, savings: float, claimed: bool = False):
        """Track a deal found by user"""
        value = self._get_or_create_value(user_id)
        value.total_deals_found += 1
        
        if claimed:
            value.deals_claimed += 1
            value.total_savings_generated += savings
        
        self._save_values()
    
    def track_deal_missed(self, user_id: int, reason: str, deal_value: float, route: str = ""):
        """Track a deal missed due to free limits"""
        value = self._get_or_create_value(user_id)
        value.deals_missed += 1
        value.potential_savings_missed += deal_value
        
        # Record missed opportunity
        if user_id not in self.missed:
            self.missed[user_id] = []
        
        self.missed[user_id].append(MissedOpportunity(
            user_id=user_id,
            timestamp=datetime.now(),
            reason=reason,
            deal_value=deal_value,
            route=route
        ))
        
        self._save_values()
        self._save_missed()
    
    def track_search(self, user_id: int):
        """Track a search performed by user"""
        value = self._get_or_create_value(user_id)
        value.total_searches += 1
        value.time_saved_minutes += AVG_SEARCH_TIME
        self._save_values()
    
    def track_activity(self, user_id: int, activity_type: str, count: int = 1):
        """
        Track user activity (watchlist, notifications, groups, referrals).
        """
        value = self._get_or_create_value(user_id)
        
        if activity_type == "watchlist":
            value.watchlist_routes = count
        elif activity_type == "notifications":
            value.notifications_received += count
        elif activity_type == "groups":
            value.groups_joined = count
        elif activity_type == "referrals":
            value.referrals_made = count
        
        self._save_values()
    
    def set_premium(self, user_id: int, is_premium: bool):
        """Set user premium status"""
        value = self._get_or_create_value(user_id)
        value.is_premium = is_premium
        
        if is_premium and not value.premium_since:
            value.premium_since = datetime.now()
        
        self._save_values()
    
    def track_premium_payment(self, user_id: int, amount: float):
        """Track premium payment made"""
        value = self._get_or_create_value(user_id)
        value.premium_spent += amount
        self._save_values()
    
    # ========================================================================
    # VALUE SNAPSHOTS
    # ========================================================================
    
    def create_snapshot(self, user_id: int):
        """Create a value snapshot for trend analysis"""
        value = self._get_or_create_value(user_id)
        
        snapshot = ValueSnapshot(
            timestamp=datetime.now(),
            total_savings=value.total_savings_generated,
            deals_found=value.total_deals_found,
            time_saved=value.time_saved_minutes
        )
        
        if user_id not in self.snapshots:
            self.snapshots[user_id] = []
        
        self.snapshots[user_id].append(snapshot)
        self._save_snapshots()
    
    # ========================================================================
    # VALUE DASHBOARD
    # ========================================================================
    
    def get_personal_dashboard(self, user_id: int) -> Dict:
        """
        Get personal value dashboard for user.
        
        Returns:
            Dict with all value metrics
        """
        value = self._get_or_create_value(user_id)
        
        # Calculate time since registration
        days_active = (datetime.now() - value.registration_date).days
        months_active = max(1, days_active / 30)
        
        # Calculate averages
        avg_savings_per_month = value.total_savings_generated / months_active
        avg_deals_per_month = value.total_deals_found / months_active
        
        # Calculate what premium would have saved
        if not value.is_premium:
            potential_additional_deals = value.deals_missed
            potential_additional_savings = value.potential_savings_missed
        else:
            potential_additional_deals = 0
            potential_additional_savings = 0
        
        return {
            'user_id': user_id,
            'is_premium': value.is_premium,
            'days_active': days_active,
            
            # Current value
            'total_savings': value.total_savings_generated,
            'total_deals': value.total_deals_found,
            'deals_claimed': value.deals_claimed,
            'time_saved_hours': value.time_saved_minutes / 60,
            
            # Missed opportunities
            'deals_missed': value.deals_missed,
            'savings_missed': value.potential_savings_missed,
            
            # Averages
            'avg_savings_per_month': avg_savings_per_month,
            'avg_deals_per_month': avg_deals_per_month,
            
            # Potential with premium
            'potential_additional_deals': potential_additional_deals,
            'potential_additional_savings': potential_additional_savings,
            
            # Engagement
            'watchlist_routes': value.watchlist_routes,
            'notifications_received': value.notifications_received,
            'groups_joined': value.groups_joined,
            'referrals_made': value.referrals_made,
            
            # Premium specific
            'premium_since': value.premium_since.isoformat() if value.premium_since else None,
            'premium_spent': value.premium_spent
        }
    
    def get_comparative_metrics(self, user_id: int) -> Dict:
        """
        Get Free vs Premium comparative metrics.
        
        Returns:
            Dict comparing user to premium averages
        """
        value = self._get_or_create_value(user_id)
        days_active = max(1, (datetime.now() - value.registration_date).days)
        months_active = max(1, days_active / 30)
        
        # User metrics (per month)
        user_deals_per_month = value.total_deals_found / months_active
        user_savings_per_month = value.total_savings_generated / months_active
        
        # Premium averages
        premium_deals_per_month = SOCIAL_PROOF['avg_deals_per_premium_user']
        premium_savings_per_month = SOCIAL_PROOF['avg_savings_per_premium_user']
        
        # Calculate differences
        if user_deals_per_month > 0:
            deals_multiplier = premium_deals_per_month / user_deals_per_month
            savings_multiplier = premium_savings_per_month / user_savings_per_month
        else:
            deals_multiplier = AVG_PREMIUM_DEALS_MULTIPLIER
            savings_multiplier = AVG_PREMIUM_DEALS_MULTIPLIER
        
        return {
            'your_tier': 'Premium' if value.is_premium else 'Free',
            
            # Deals comparison
            'your_deals_per_month': round(user_deals_per_month, 1),
            'premium_deals_per_month': premium_deals_per_month,
            'deals_difference': premium_deals_per_month - user_deals_per_month,
            'deals_multiplier': round(deals_multiplier, 1),
            
            # Savings comparison
            'your_savings_per_month': round(user_savings_per_month, 2),
            'premium_savings_per_month': premium_savings_per_month,
            'savings_difference': premium_savings_per_month - user_savings_per_month,
            'savings_multiplier': round(savings_multiplier, 1),
            
            # Response time
            'your_response_time': '2 hours' if not value.is_premium else '5 minutes',
            'premium_response_time': '5 minutes',
            'response_multiplier': AVG_NOTIFICATION_SPEED_MULTIPLIER if not value.is_premium else 1,
            
            # Missed deals
            'deals_missed_last_month': value.deals_missed  # Simplified
        }
    
    def calculate_premium_roi(self, user_id: int, plan: str = "monthly") -> Dict:
        """
        Calculate ROI of premium subscription.
        
        Args:
            plan: "monthly" or "annual"
        
        Returns:
            Dict with ROI calculations
        """
        value = self._get_or_create_value(user_id)
        dashboard = self.get_personal_dashboard(user_id)
        
        # Plan cost
        if plan == "monthly":
            cost = PREMIUM_MONTHLY_PRICE
            period_months = 1
        else:  # annual
            cost = PREMIUM_ANNUAL_PRICE
            period_months = 12
        
        # Expected additional value with premium
        additional_savings = dashboard['potential_additional_savings']
        
        if additional_savings == 0:
            # Use average multiplier
            current_monthly_savings = dashboard['avg_savings_per_month']
            additional_savings = current_monthly_savings * (AVG_PREMIUM_DEALS_MULTIPLIER - 1) * period_months
        
        # Calculate ROI
        net_value = additional_savings - cost
        roi_percentage = (net_value / cost) * 100 if cost > 0 else 0
        roi_multiplier = additional_savings / cost if cost > 0 else 0
        
        # Break-even (how many deals needed to pay for itself)
        deals_to_breakeven = cost / AVG_DEAL_SAVINGS if AVG_DEAL_SAVINGS > 0 else 0
        
        return {
            'plan': plan,
            'cost': cost,
            'period_months': period_months,
            
            # Expected value
            'expected_additional_savings': round(additional_savings, 2),
            'expected_additional_deals': round(additional_savings / AVG_DEAL_SAVINGS),
            
            # ROI
            'net_value': round(net_value, 2),
            'roi_percentage': round(roi_percentage, 1),
            'roi_multiplier': round(roi_multiplier, 1),
            
            # Break-even
            'deals_to_breakeven': round(deals_to_breakeven, 1),
            'estimated_days_to_breakeven': round(deals_to_breakeven * 7, 0),  # ~1 deal/week
            
            # Verdict
            'is_worth_it': roi_percentage > 100
        }
    
    # ========================================================================
    # SOCIAL PROOF
    # ========================================================================
    
    def get_social_proof(self) -> Dict:
        """Get social proof data for premium"""
        return SOCIAL_PROOF.copy()
    
    # ========================================================================
    # UPGRADE TRIGGERS
    # ========================================================================
    
    def should_show_value_dashboard(self, user_id: int) -> Tuple[bool, str]:
        """
        Determine if value dashboard should be shown to trigger upgrade.
        
        Returns:
            (should_show, reason)
        """
        value = self._get_or_create_value(user_id)
        
        if value.is_premium:
            return False, "Already premium"
        
        # Show after finding 3+ deals
        if value.total_deals_found >= 3:
            return True, "Found 3+ deals"
        
        # Show if missed deals
        if value.deals_missed >= 2:
            return True, "Missed 2+ deals"
        
        # Show if high value generated
        if value.total_savings_generated >= 500:
            return True, "Generated €500+ value"
        
        # Show after 7 days active
        days_active = (datetime.now() - value.registration_date).days
        if days_active >= 7:
            return True, "Active for 7+ days"
        
        return False, "Criteria not met"


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def format_value_dashboard(dashboard: Dict, comparative: Dict, roi: Dict) -> str:
    """
    Format value dashboard for display.
    
    Args:
        dashboard: From get_personal_dashboard()
        comparative: From get_comparative_metrics()
        roi: From calculate_premium_roi()
    
    Returns:
        Formatted string
    """
    return f"""📊 Tu Dashboard de Valor

💰 Valor Generado:
• Ahorro total: €{dashboard['total_savings']:.2f}
• Chollos encontrados: {dashboard['total_deals']}
• Tiempo ahorrado: {dashboard['time_saved_hours']:.1f}h

❌ Oportunidades Perdidas:
• Chollos perdidos: {dashboard['deals_missed']}
• Ahorro perdido: €{dashboard['savings_missed']:.2f}

📈 Free vs Premium:

Tú (Free): {comparative['your_deals_per_month']:.0f} chollos/mes
Premium: {comparative['premium_deals_per_month']} chollos/mes
Diferencia: +{comparative['deals_difference']:.0f} chollos ({comparative['deals_multiplier']:.0f}x)

💸 ROI de Premium:
• Costo: €{roi['cost']}/mes
• Ahorro adicional: €{roi['expected_additional_savings']:.0f}
• Valor neto: €{roi['net_value']:.0f}
• ROI: {roi['roi_multiplier']:.0f}x ({roi['roi_percentage']:.0f}%)

🎯 Con Premium te pagas en {roi['deals_to_breakeven']:.0f} chollos (~{roi['estimated_days_to_breakeven']:.0f} días)

{'[✅ Premium Vale la Pena]' if roi['is_worth_it'] else '[⚠️ Considera Premium]'}
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
    
    print("1️⃣ Tracking Value")
    print("-" * 40)
    
    # Simulate user activity
    tracker.track_search(test_user)
    tracker.track_deal_found(test_user, 180, claimed=True)
    tracker.track_deal_found(test_user, 220, claimed=True)
    tracker.track_deal_found(test_user, 150, claimed=False)
    tracker.track_deal_missed(test_user, "search_limit", 200, "MAD-MIA")
    tracker.track_deal_missed(test_user, "watchlist_full", 180, "MAD-NYC")
    tracker.track_activity(test_user, "watchlist", 3)
    tracker.track_activity(test_user, "notifications", 5)
    
    print("✅ Tracked activity for test user")
    
    print("\n2️⃣ Personal Dashboard")
    print("-" * 40)
    
    dashboard = tracker.get_personal_dashboard(test_user)
    print(f"Total savings: €{dashboard['total_savings']:.2f}")
    print(f"Deals found: {dashboard['total_deals']}")
    print(f"Deals missed: {dashboard['deals_missed']}")
    print(f"Savings missed: €{dashboard['savings_missed']:.2f}")
    
    print("\n3️⃣ Comparative Metrics")
    print("-" * 40)
    
    comparative = tracker.get_comparative_metrics(test_user)
    print(f"Your deals/month: {comparative['your_deals_per_month']:.1f}")
    print(f"Premium avg: {comparative['premium_deals_per_month']}")
    print(f"Multiplier: {comparative['deals_multiplier']:.1f}x")
    
    print("\n4️⃣ ROI Calculator")
    print("-" * 40)
    
    roi = tracker.calculate_premium_roi(test_user, "monthly")
    print(f"Cost: €{roi['cost']}")
    print(f"Expected additional savings: €{roi['expected_additional_savings']:.2f}")
    print(f"ROI: {roi['roi_multiplier']:.1f}x ({roi['roi_percentage']:.0f}%)")
    print(f"Worth it: {roi['is_worth_it']}")
    
    print("\n5️⃣ Formatted Dashboard")
    print("-" * 40)
    print(format_value_dashboard(dashboard, comparative, roi))
    
    print("\n6️⃣ Upgrade Trigger")
    print("-" * 40)
    
    should_show, reason = tracker.should_show_value_dashboard(test_user)
    print(f"Show dashboard: {should_show} ({reason})")
    
    print("\n" + "="*60)
    print("✅ Testing Complete!")
    print("="*60 + "\n")
