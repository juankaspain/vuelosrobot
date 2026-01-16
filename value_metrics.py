#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Value Metrics Dashboard for Premium Conversion
IT6 - DAY 3/5

Features:
- Personal value dashboard showing generated value
- Comparative metrics (Free vs Premium)
- ROI calculator for premium subscription
- Social proof integration
- Missed opportunities tracking
- Time saved calculator

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
AVG_DEAL_SAVINGS = 150  # Average € saved per deal
AVG_SEARCH_TIME = 15  # Minutes per manual search
AVG_PREMIUM_DEALS_MONTH = 45  # Deals found by premium users per month
AVG_FREE_DEALS_MONTH = 12  # Deals found by free users per month
AVG_NOTIFICATION_DELAY_FREE = 120  # Minutes delay for free users
AVG_NOTIFICATION_DELAY_PREMIUM = 5  # Minutes delay for premium users

# Premium pricing
PREMIUM_MONTHLY_PRICE = 9.99
PREMIUM_ANNUAL_PRICE = 99.99

# Social proof stats (updated periodically)
SOCIAL_PROOF = {
    "premium_users": 892,
    "avg_rating": 4.8,
    "total_savings_generated": 156000,
    "top_hunters_premium_percent": 85,
    "avg_premium_monthly_savings": 1680
}


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class UserValue:
    """Track value generated for a user"""
    user_id: int
    is_premium: bool
    registration_date: datetime
    
    # Searches
    total_searches: int = 0
    manual_search_time_saved: float = 0  # minutes
    
    # Deals
    deals_found: int = 0
    deals_claimed: int = 0
    total_savings: float = 0  # €
    
    # Missed opportunities (for free users)
    deals_missed_limit: int = 0  # Due to search limits
    deals_missed_delay: int = 0  # Due to slow notifications
    estimated_missed_savings: float = 0  # €
    
    # Engagement
    watchlist_size: int = 0
    notifications_received: int = 0
    groups_joined: int = 0
    referrals_made: int = 0
    
    # Premium specific
    premium_since: Optional[datetime] = None
    premium_cost_paid: float = 0  # Total paid for premium
    
    @property
    def days_as_user(self) -> int:
        """Days since registration"""
        return (datetime.now() - self.registration_date).days
    
    @property
    def days_as_premium(self) -> int:
        """Days as premium user"""
        if not self.premium_since:
            return 0
        return (datetime.now() - self.premium_since).days
    
    @property
    def roi_percentage(self) -> float:
        """
        Calculate ROI percentage for premium users.
        ROI = (Savings - Cost) / Cost * 100
        """
        if not self.is_premium or self.premium_cost_paid == 0:
            return 0
        return ((self.total_savings - self.premium_cost_paid) / self.premium_cost_paid) * 100
    
    @property
    def net_value(self) -> float:
        """Net value after premium costs"""
        return self.total_savings - self.premium_cost_paid
    
    @property
    def potential_total_savings(self) -> float:
        """Potential savings if was premium"""
        if self.is_premium:
            return self.total_savings
        return self.total_savings + self.estimated_missed_savings
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['registration_date'] = self.registration_date.isoformat()
        if self.premium_since:
            data['premium_since'] = self.premium_since.isoformat()
        # Add computed properties
        data['days_as_user'] = self.days_as_user
        data['days_as_premium'] = self.days_as_premium
        data['roi_percentage'] = self.roi_percentage
        data['net_value'] = self.net_value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'UserValue':
        # Remove computed properties
        for key in ['days_as_user', 'days_as_premium', 'roi_percentage', 'net_value']:
            data.pop(key, None)
        
        data['registration_date'] = datetime.fromisoformat(data['registration_date'])
        if data.get('premium_since'):
            data['premium_since'] = datetime.fromisoformat(data['premium_since'])
        return cls(**data)


@dataclass
class ComparativeMetrics:
    """Comparative metrics between user and averages"""
    # User metrics
    user_deals_month: float
    user_savings_month: float
    user_response_time: float  # minutes
    
    # Comparison benchmarks
    avg_free_deals_month: float = AVG_FREE_DEALS_MONTH
    avg_premium_deals_month: float = AVG_PREMIUM_DEALS_MONTH
    avg_free_response: float = AVG_NOTIFICATION_DELAY_FREE
    avg_premium_response: float = AVG_NOTIFICATION_DELAY_PREMIUM
    
    @property
    def deals_vs_free(self) -> float:
        """User deals vs free average (percentage)"""
        if self.avg_free_deals_month == 0:
            return 0
        return ((self.user_deals_month - self.avg_free_deals_month) / self.avg_free_deals_month) * 100
    
    @property
    def deals_vs_premium(self) -> float:
        """User deals vs premium average (percentage)"""
        if self.avg_premium_deals_month == 0:
            return 0
        return ((self.user_deals_month - self.avg_premium_deals_month) / self.avg_premium_deals_month) * 100
    
    @property
    def savings_potential(self) -> float:
        """Potential additional savings with premium"""
        return (self.avg_premium_deals_month - self.user_deals_month) * AVG_DEAL_SAVINGS
    
    @property
    def speed_improvement(self) -> float:
        """Speed improvement factor (premium vs free)"""
        if self.avg_premium_response == 0:
            return 0
        return self.avg_free_response / self.avg_premium_response


# ============================================================================
# VALUE TRACKER
# ============================================================================

class ValueTracker:
    """
    Tracks and calculates value metrics for users.
    
    Features:
    - Personal value dashboard
    - Comparative analysis
    - ROI calculator
    - Missed opportunities tracking
    - Social proof integration
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
        """Load user values from file"""
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
        """Save user values to file"""
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
    # USER VALUE TRACKING
    # ========================================================================
    
    def _get_or_create_value(self, user_id: int, is_premium: bool = False) -> UserValue:
        """Get or create user value record"""
        if user_id not in self.user_values:
            self.user_values[user_id] = UserValue(
                user_id=user_id,
                is_premium=is_premium,
                registration_date=datetime.now()
            )
        return self.user_values[user_id]
    
    def track_search(self, user_id: int, is_premium: bool = False):
        """Track a search performed"""
        value = self._get_or_create_value(user_id, is_premium)
        value.total_searches += 1
        value.manual_search_time_saved += AVG_SEARCH_TIME
        self._save_values()
    
    def track_deal_found(self, user_id: int, savings: float, is_premium: bool = False):
        """Track a deal found"""
        value = self._get_or_create_value(user_id, is_premium)
        value.deals_found += 1
        value.total_savings += savings
        self._save_values()
    
    def track_deal_claimed(self, user_id: int):
        """Track a deal claimed/booked"""
        if user_id in self.user_values:
            self.user_values[user_id].deals_claimed += 1
            self._save_values()
    
    def track_missed_deal(self, user_id: int, reason: str, estimated_value: float):
        """
        Track a missed deal opportunity.
        
        Args:
            reason: 'limit' or 'delay'
        """
        value = self._get_or_create_value(user_id)
        
        if reason == 'limit':
            value.deals_missed_limit += 1
        elif reason == 'delay':
            value.deals_missed_delay += 1
        
        value.estimated_missed_savings += estimated_value
        self._save_values()
    
    def update_premium_status(self, user_id: int, is_premium: bool, amount_paid: float = 0):
        """Update user's premium status"""
        value = self._get_or_create_value(user_id, is_premium)
        value.is_premium = is_premium
        
        if is_premium and not value.premium_since:
            value.premium_since = datetime.now()
        
        if amount_paid > 0:
            value.premium_cost_paid += amount_paid
        
        self._save_values()
    
    def update_engagement(self, user_id: int, metric: str, value: int):
        """
        Update engagement metrics.
        
        metric: 'watchlist', 'notifications', 'groups', 'referrals'
        """
        user_value = self._get_or_create_value(user_id)
        
        if metric == 'watchlist':
            user_value.watchlist_size = value
        elif metric == 'notifications':
            user_value.notifications_received += value
        elif metric == 'groups':
            user_value.groups_joined = value
        elif metric == 'referrals':
            user_value.referrals_made = value
        
        self._save_values()
    
    # ========================================================================
    # VALUE DASHBOARD
    # ========================================================================
    
    def get_personal_dashboard(self, user_id: int) -> Dict:
        """
        Get personal value dashboard for user.
        
        Returns comprehensive value metrics.
        """
        if user_id not in self.user_values:
            return {
                'error': 'User not found',
                'user_id': user_id
            }
        
        value = self.user_values[user_id]
        
        # Calculate monthly averages
        months_active = max(1, value.days_as_user / 30)
        deals_per_month = value.deals_found / months_active
        savings_per_month = value.total_savings / months_active
        
        dashboard = {
            'user_id': user_id,
            'is_premium': value.is_premium,
            'member_since': value.registration_date.date().isoformat(),
            'days_active': value.days_as_user,
            
            # Core metrics
            'total_searches': value.total_searches,
            'time_saved_hours': round(value.manual_search_time_saved / 60, 1),
            'deals_found': value.deals_found,
            'deals_claimed': value.deals_claimed,
            'total_savings': round(value.total_savings, 2),
            
            # Monthly averages
            'deals_per_month': round(deals_per_month, 1),
            'savings_per_month': round(savings_per_month, 2),
            
            # Missed opportunities (free users)
            'deals_missed': value.deals_missed_limit + value.deals_missed_delay,
            'missed_due_to_limits': value.deals_missed_limit,
            'missed_due_to_delay': value.deals_missed_delay,
            'estimated_missed_savings': round(value.estimated_missed_savings, 2),
            
            # Potential with premium
            'potential_total_savings': round(value.potential_total_savings, 2),
            'potential_gain': round(value.estimated_missed_savings, 2),
            
            # Engagement
            'watchlist_size': value.watchlist_size,
            'notifications_received': value.notifications_received,
            'groups_joined': value.groups_joined,
            'referrals_made': value.referrals_made
        }
        
        # Add premium-specific metrics
        if value.is_premium:
            dashboard.update({
                'premium_since': value.premium_since.date().isoformat() if value.premium_since else None,
                'days_as_premium': value.days_as_premium,
                'premium_cost_paid': round(value.premium_cost_paid, 2),
                'net_value': round(value.net_value, 2),
                'roi_percentage': round(value.roi_percentage, 1),
                'roi_multiplier': round((value.total_savings / value.premium_cost_paid) if value.premium_cost_paid > 0 else 0, 1)
            })
        
        return dashboard
    
    # ========================================================================
    # COMPARATIVE METRICS
    # ========================================================================
    
    def get_comparative_metrics(self, user_id: int) -> Optional[ComparativeMetrics]:
        """Get comparative metrics vs averages"""
        if user_id not in self.user_values:
            return None
        
        value = self.user_values[user_id]
        
        # Calculate user's monthly averages
        months_active = max(1, value.days_as_user / 30)
        user_deals_month = value.deals_found / months_active
        user_savings_month = value.total_savings / months_active
        
        # Estimate response time based on premium status
        user_response = AVG_NOTIFICATION_DELAY_PREMIUM if value.is_premium else AVG_NOTIFICATION_DELAY_FREE
        
        return ComparativeMetrics(
            user_deals_month=user_deals_month,
            user_savings_month=user_savings_month,
            user_response_time=user_response
        )
    
    # ========================================================================
    # ROI CALCULATOR
    # ========================================================================
    
    def calculate_premium_roi(self, user_id: int, plan: str = "monthly") -> Dict:
        """
        Calculate ROI for premium subscription.
        
        Args:
            plan: 'monthly' or 'annual'
        
        Returns:
            ROI analysis with projections
        """
        if user_id not in self.user_values:
            return {'error': 'User not found'}
        
        value = self.user_values[user_id]
        
        # Get plan pricing
        if plan == "monthly":
            cost = PREMIUM_MONTHLY_PRICE
            period_months = 1
        else:  # annual
            cost = PREMIUM_ANNUAL_PRICE
            period_months = 12
        
        # Calculate current monthly performance
        months_active = max(1, value.days_as_user / 30)
        current_deals_month = value.deals_found / months_active
        current_savings_month = value.total_savings / months_active
        
        # Project premium performance
        if value.is_premium:
            # Already premium, use actual performance
            premium_deals_month = current_deals_month
            premium_savings_month = current_savings_month
        else:
            # Project based on averages
            premium_deals_month = AVG_PREMIUM_DEALS_MONTH
            premium_savings_month = premium_deals_month * AVG_DEAL_SAVINGS
        
        # Calculate ROI
        period_savings = premium_savings_month * period_months
        net_value = period_savings - cost
        roi_percentage = (net_value / cost) * 100
        roi_multiplier = period_savings / cost
        
        # Payback period in days
        daily_savings = premium_savings_month / 30
        if daily_savings > 0:
            payback_days = cost / daily_savings
        else:
            payback_days = 999
        
        return {
            'plan': plan,
            'period_months': period_months,
            'cost': cost,
            
            # Current performance
            'current_deals_month': round(current_deals_month, 1),
            'current_savings_month': round(current_savings_month, 2),
            
            # Premium projections
            'premium_deals_month': round(premium_deals_month, 1),
            'premium_savings_month': round(premium_savings_month, 2),
            'period_total_savings': round(period_savings, 2),
            
            # ROI
            'net_value': round(net_value, 2),
            'roi_percentage': round(roi_percentage, 1),
            'roi_multiplier': round(roi_multiplier, 1),
            'payback_days': int(payback_days),
            
            # Comparison
            'additional_deals': round(premium_deals_month - current_deals_month, 1),
            'additional_savings': round(premium_savings_month - current_savings_month, 2)
        }
    
    # ========================================================================
    # SOCIAL PROOF
    # ========================================================================
    
    def get_social_proof(self) -> Dict:
        """Get social proof statistics"""
        return SOCIAL_PROOF.copy()
    
    def get_upgrade_value_prop(self, user_id: int) -> Dict:
        """
        Get personalized value proposition for upgrade.
        Combines user metrics with social proof.
        """
        dashboard = self.get_personal_dashboard(user_id)
        roi = self.calculate_premium_roi(user_id)
        social = self.get_social_proof()
        comparative = self.get_comparative_metrics(user_id)
        
        # Build value proposition
        value_props = []
        
        # Missed opportunities
        if dashboard.get('deals_missed', 0) > 0:
            value_props.append(
                f"❌ Has perdido {dashboard['deals_missed']} chollos (€{dashboard['estimated_missed_savings']}) por límites free"
            )
        
        # ROI
        if roi.get('roi_multiplier', 0) > 1:
            value_props.append(
                f"💰 ROI de {roi['roi_multiplier']}x - Recuperas la inversión en {roi['payback_days']} días"
            )
        
        # Additional deals
        if roi.get('additional_deals', 0) > 0:
            value_props.append(
                f"🔥 +{roi['additional_deals']} chollos/mes = +€{roi['additional_savings']}/mes de ahorro"
            )
        
        # Speed
        if comparative:
            value_props.append(
                f"⚡ Notificaciones {comparative.speed_improvement:.0f}x más rápidas"
            )
        
        # Social proof
        value_props.append(
            f"👥 Únete a {social['premium_users']}+ usuarios premium (rating {social['avg_rating']}⭐)"
        )
        
        value_props.append(
            f"🏆 {social['top_hunters_premium_percent']}% de top hunters son premium"
        )
        
        return {
            'user_id': user_id,
            'value_propositions': value_props,
            'dashboard': dashboard,
            'roi': roi,
            'social_proof': social,
            'comparative': {
                'deals_vs_free': f"{comparative.deals_vs_free:+.0f}%" if comparative else None,
                'deals_vs_premium': f"{comparative.deals_vs_premium:+.0f}%" if comparative else None,
                'savings_potential': f"€{comparative.savings_potential:.0f}" if comparative else None
            }
        }
    
    # ========================================================================
    # ANALYTICS
    # ========================================================================
    
    def get_aggregate_stats(self) -> Dict:
        """Get aggregate statistics across all users"""
        total_users = len(self.user_values)
        premium_users = sum(1 for v in self.user_values.values() if v.is_premium)
        
        total_savings = sum(v.total_savings for v in self.user_values.values())
        total_deals = sum(v.deals_found for v in self.user_values.values())
        
        # Premium vs Free comparison
        premium_values = [v for v in self.user_values.values() if v.is_premium]
        free_values = [v for v in self.user_values.values() if not v.is_premium]
        
        if premium_values:
            avg_premium_savings = sum(v.total_savings for v in premium_values) / len(premium_values)
            avg_premium_deals = sum(v.deals_found for v in premium_values) / len(premium_values)
        else:
            avg_premium_savings = 0
            avg_premium_deals = 0
        
        if free_values:
            avg_free_savings = sum(v.total_savings for v in free_values) / len(free_values)
            avg_free_deals = sum(v.deals_found for v in free_values) / len(free_values)
        else:
            avg_free_savings = 0
            avg_free_deals = 0
        
        return {
            'total_users': total_users,
            'premium_users': premium_users,
            'free_users': total_users - premium_users,
            'premium_rate': premium_users / total_users if total_users > 0 else 0,
            
            'total_savings_generated': round(total_savings, 2),
            'total_deals_found': total_deals,
            
            'avg_premium_savings': round(avg_premium_savings, 2),
            'avg_premium_deals': round(avg_premium_deals, 1),
            'avg_free_savings': round(avg_free_savings, 2),
            'avg_free_deals': round(avg_free_deals, 1),
            
            'premium_advantage_savings': round(
                ((avg_premium_savings - avg_free_savings) / avg_free_savings * 100) if avg_free_savings > 0 else 0,
                1
            ),
            'premium_advantage_deals': round(
                ((avg_premium_deals - avg_free_deals) / avg_free_deals * 100) if avg_free_deals > 0 else 0,
                1
            )
        }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def format_value_dashboard(dashboard: Dict) -> str:
    """
    Format value dashboard for display.
    
    Args:
        dashboard: Dict from get_personal_dashboard()
    
    Returns:
        Formatted dashboard string
    """
    is_premium = dashboard.get('is_premium', False)
    
    message = f"""📊 Tu Dashboard de Valor

📅 Miembro desde: {dashboard['member_since']} ({dashboard['days_active']} días)

🔍 Búsquedas realizadas: {dashboard['total_searches']}
⏱️ Tiempo ahorrado: {dashboard['time_saved_hours']}h

🔥 Chollos encontrados: {dashboard['deals_found']}
✅ Chollos aprovechados: {dashboard['deals_claimed']}
💰 Ahorro total generado: €{dashboard['total_savings']}

📈 Promedios mensuales:
• {dashboard['deals_per_month']} chollos/mes
• €{dashboard['savings_per_month']}/mes ahorrados
"""
    
    if not is_premium:
        # Show missed opportunities
        if dashboard['deals_missed'] > 0:
            message += f"""
⚠️ Oportunidades Perdidas:
❌ {dashboard['deals_missed']} chollos perdidos
• {dashboard['missed_due_to_limits']} por límites de búsqueda
• {dashboard['missed_due_to_delay']} por notificaciones lentas
💸 Ahorro perdido: €{dashboard['estimated_missed_savings']}

💡 Con Premium:
✅ 0 chollos perdidos
💰 +€{dashboard['potential_gain']} ahorro adicional
"""
    else:
        # Show premium ROI
        message += f"""
💎 Premium desde: {dashboard['premium_since']} ({dashboard['days_as_premium']} días)
💳 Inversión: €{dashboard['premium_cost_paid']}
💰 Valor neto: €{dashboard['net_value']}
📈 ROI: {dashboard['roi_percentage']}% ({dashboard['roi_multiplier']}x)
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
    
    # Test user (free)
    free_user = 11111
    
    print("1️⃣ Tracking Value for Free User")
    print("-" * 40)
    
    # Simulate activity
    for i in range(15):
        tracker.track_search(free_user)
    
    for i in range(8):
        tracker.track_deal_found(free_user, savings=120)
    
    tracker.track_missed_deal(free_user, 'limit', 150)
    tracker.track_missed_deal(free_user, 'delay', 180)
    
    tracker.update_engagement(free_user, 'watchlist', 3)
    tracker.update_engagement(free_user, 'notifications', 12)
    
    # Get dashboard
    dashboard = tracker.get_personal_dashboard(free_user)
    print(format_value_dashboard(dashboard))
    
    print("\n2️⃣ ROI Calculator")
    print("-" * 40)
    
    roi_monthly = tracker.calculate_premium_roi(free_user, 'monthly')
    roi_annual = tracker.calculate_premium_roi(free_user, 'annual')
    
    print(f"\nMONTHLY PLAN (€{roi_monthly['cost']})")
    print(f"ROI: {roi_monthly['roi_percentage']}% ({roi_monthly['roi_multiplier']}x)")
    print(f"Payback: {roi_monthly['payback_days']} días")
    print(f"Net value: €{roi_monthly['net_value']}")
    
    print(f"\nANNUAL PLAN (€{roi_annual['cost']})")
    print(f"ROI: {roi_annual['roi_percentage']}% ({roi_annual['roi_multiplier']}x)")
    print(f"Payback: {roi_annual['payback_days']} días")
    print(f"Net value: €{roi_annual['net_value']}")
    
    print("\n3️⃣ Value Proposition")
    print("-" * 40)
    
    value_prop = tracker.get_upgrade_value_prop(free_user)
    print("\n🚀 Por qué actualizar a Premium:\n")
    for i, prop in enumerate(value_prop['value_propositions'], 1):
        print(f"{i}. {prop}")
    
    print("\n4️⃣ Aggregate Stats")
    print("-" * 40)
    
    stats = tracker.get_aggregate_stats()
    print(f"\nTotal users: {stats['total_users']}")
    print(f"Premium users: {stats['premium_users']} ({stats['premium_rate']*100:.1f}%)")
    print(f"Total savings generated: €{stats['total_savings_generated']}")
    print(f"\nPremium advantage:")
    print(f"• Savings: +{stats['premium_advantage_savings']}%")
    print(f"• Deals: +{stats['premium_advantage_deals']}%")
    
    print("\n" + "="*60)
    print("✅ Testing Complete!")
    print("="*60 + "\n")
