#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Premium Analytics & Churn Prevention
IT6 - DAY 5/5

Features:
- Conversion funnel tracking (Paywall → Trial → Paid)
- Revenue metrics (MRR, ARR, ARPU, LTV)
- Retention cohort analysis
- Churn prediction and prevention
- Premium user analytics

Author: @Juanka_Spain
Version: 14.0.0-alpha.5
Date: 2026-01-16
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict
from pathlib import Path


# ============================================================================
# CONSTANTS
# ============================================================================

# Funnel stages
FUNNEL_STAGES = [
    "paywall_viewed",
    "paywall_clicked",
    "trial_started",
    "trial_engaged",  # Used premium features
    "paid_converted"
]

# Churn risk thresholds
CHURN_RISK_THRESHOLDS = {
    "high": 70,  # >70% risk = high
    "medium": 40,  # 40-70% risk = medium
    "low": 40  # <40% risk = low
}


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class FunnelEvent:
    """Single event in conversion funnel"""
    user_id: int
    stage: str  # One of FUNNEL_STAGES
    timestamp: datetime
    metadata: Dict = None
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'FunnelEvent':
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class PremiumSubscription:
    """Premium subscription record"""
    user_id: int
    plan_tier: str
    start_date: datetime
    billing_period: str  # "monthly" or "annual"
    monthly_value: float  # MRR contribution
    is_active: bool = True
    cancel_date: Optional[datetime] = None
    churn_risk_score: float = 0.0  # 0-100
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['start_date'] = self.start_date.isoformat()
        if self.cancel_date:
            data['cancel_date'] = self.cancel_date.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'PremiumSubscription':
        data['start_date'] = datetime.fromisoformat(data['start_date'])
        if data.get('cancel_date'):
            data['cancel_date'] = datetime.fromisoformat(data['cancel_date'])
        return cls(**data)


@dataclass
class ChurnPrediction:
    """Churn prediction for a user"""
    user_id: int
    risk_score: float  # 0-100
    risk_level: str  # "low", "medium", "high"
    factors: List[str]  # Risk factors identified
    recommended_actions: List[str]  # Win-back actions
    prediction_date: datetime
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['prediction_date'] = self.prediction_date.isoformat()
        return data


# ============================================================================
# ANALYTICS MANAGER
# ============================================================================

class AnalyticsManager:
    """
    Manages premium analytics and churn prevention.
    
    Features:
    - Conversion funnel tracking
    - Revenue metrics (MRR, ARR, ARPU, LTV)
    - Retention analysis
    - Churn prediction
    """
    
    def __init__(self, data_dir: str = "."):
        self.data_dir = Path(data_dir)
        self.funnel_file = self.data_dir / "conversion_funnel.json"
        self.subscriptions_file = self.data_dir / "premium_subscriptions.json"
        self.churn_file = self.data_dir / "churn_predictions.json"
        
        # Load data
        self.funnel_events: List[FunnelEvent] = self._load_funnel()
        self.subscriptions: Dict[int, PremiumSubscription] = self._load_subscriptions()
        self.churn_predictions: Dict[int, ChurnPrediction] = self._load_churn()
        
        print("✅ AnalyticsManager initialized")
    
    # ========================================================================
    # DATA PERSISTENCE
    # ========================================================================
    
    def _load_funnel(self) -> List[FunnelEvent]:
        """Load funnel events"""
        if not self.funnel_file.exists():
            return []
        
        try:
            with open(self.funnel_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [FunnelEvent.from_dict(e) for e in data]
        except Exception as e:
            print(f"⚠️ Error loading funnel: {e}")
            return []
    
    def _save_funnel(self):
        """Save funnel events"""
        try:
            data = [e.to_dict() for e in self.funnel_events]
            with open(self.funnel_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Error saving funnel: {e}")
    
    def _load_subscriptions(self) -> Dict[int, PremiumSubscription]:
        """Load subscriptions"""
        if not self.subscriptions_file.exists():
            return {}
        
        try:
            with open(self.subscriptions_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {
                    int(user_id): PremiumSubscription.from_dict(sub)
                    for user_id, sub in data.items()
                }
        except Exception as e:
            print(f"⚠️ Error loading subscriptions: {e}")
            return {}
    
    def _save_subscriptions(self):
        """Save subscriptions"""
        try:
            data = {
                str(user_id): sub.to_dict()
                for user_id, sub in self.subscriptions.items()
            }
            with open(self.subscriptions_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Error saving subscriptions: {e}")
    
    def _load_churn(self) -> Dict[int, ChurnPrediction]:
        """Load churn predictions"""
        if not self.churn_file.exists():
            return {}
        
        try:
            with open(self.churn_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {
                    int(user_id): ChurnPrediction(**pred)
                    for user_id, pred in data.items()
                }
        except Exception as e:
            print(f"⚠️ Error loading churn: {e}")
            return {}
    
    def _save_churn(self):
        """Save churn predictions"""
        try:
            data = {
                str(user_id): pred.to_dict()
                for user_id, pred in self.churn_predictions.items()
            }
            with open(self.churn_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Error saving churn: {e}")
    
    # ========================================================================
    # FUNNEL TRACKING
    # ========================================================================
    
    def track_funnel_event(self, user_id: int, stage: str, metadata: Dict = None):
        """
        Track a funnel event.
        
        Args:
            user_id: User ID
            stage: One of FUNNEL_STAGES
            metadata: Optional metadata
        """
        if stage not in FUNNEL_STAGES:
            print(f"⚠️ Invalid funnel stage: {stage}")
            return
        
        event = FunnelEvent(
            user_id=user_id,
            stage=stage,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        
        self.funnel_events.append(event)
        self._save_funnel()
    
    def get_funnel_stats(self, days: int = 30) -> Dict:
        """
        Get conversion funnel statistics.
        
        Args:
            days: Days to look back
        
        Returns:
            Dict with funnel stats
        """
        cutoff = datetime.now() - timedelta(days=days)
        recent_events = [e for e in self.funnel_events if e.timestamp >= cutoff]
        
        # Count users at each stage
        stage_users = defaultdict(set)
        for event in recent_events:
            stage_users[event.stage].add(event.user_id)
        
        # Calculate conversion rates
        stats = {
            'period_days': days,
            'stages': {}
        }
        
        for i, stage in enumerate(FUNNEL_STAGES):
            users_at_stage = len(stage_users[stage])
            
            # Conversion rate from previous stage
            if i > 0:
                prev_stage = FUNNEL_STAGES[i-1]
                prev_users = len(stage_users[prev_stage])
                conv_rate = (users_at_stage / prev_users * 100) if prev_users > 0 else 0
            else:
                conv_rate = 100  # First stage
            
            stats['stages'][stage] = {
                'users': users_at_stage,
                'conversion_rate': round(conv_rate, 1)
            }
        
        # Overall conversion rate (paywall → paid)
        if stage_users['paywall_viewed']:
            overall_rate = len(stage_users['paid_converted']) / len(stage_users['paywall_viewed']) * 100
        else:
            overall_rate = 0
        
        stats['overall_conversion_rate'] = round(overall_rate, 1)
        
        return stats
    
    # ========================================================================
    # SUBSCRIPTION MANAGEMENT
    # ========================================================================
    
    def add_subscription(self, user_id: int, plan_tier: str, billing_period: str, monthly_value: float):
        """
        Add a premium subscription.
        
        Args:
            user_id: User ID
            plan_tier: Plan tier (basic_monthly, etc.)
            billing_period: "monthly" or "annual"
            monthly_value: MRR contribution
        """
        sub = PremiumSubscription(
            user_id=user_id,
            plan_tier=plan_tier,
            start_date=datetime.now(),
            billing_period=billing_period,
            monthly_value=monthly_value
        )
        
        self.subscriptions[user_id] = sub
        self._save_subscriptions()
        
        # Track in funnel
        self.track_funnel_event(user_id, "paid_converted")
    
    def cancel_subscription(self, user_id: int):
        """Cancel a subscription"""
        if user_id in self.subscriptions:
            self.subscriptions[user_id].is_active = False
            self.subscriptions[user_id].cancel_date = datetime.now()
            self._save_subscriptions()
    
    # ========================================================================
    # REVENUE METRICS
    # ========================================================================
    
    def get_revenue_metrics(self) -> Dict:
        """
        Calculate key revenue metrics.
        
        Returns:
            Dict with MRR, ARR, ARPU, etc.
        """
        active_subs = [s for s in self.subscriptions.values() if s.is_active]
        
        if not active_subs:
            return {
                'mrr': 0,
                'arr': 0,
                'arpu': 0,
                'active_subscriptions': 0
            }
        
        # MRR (Monthly Recurring Revenue)
        mrr = sum(s.monthly_value for s in active_subs)
        
        # ARR (Annual Recurring Revenue)
        arr = mrr * 12
        
        # ARPU (Average Revenue Per User)
        arpu = mrr / len(active_subs)
        
        # Calculate churn rate (last 30 days)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_cancels = sum(
            1 for s in self.subscriptions.values()
            if s.cancel_date and s.cancel_date >= thirty_days_ago
        )
        total_subs = len(self.subscriptions)
        churn_rate = (recent_cancels / total_subs * 100) if total_subs > 0 else 0
        
        return {
            'mrr': round(mrr, 2),
            'arr': round(arr, 2),
            'arpu': round(arpu, 2),
            'active_subscriptions': len(active_subs),
            'total_subscriptions': total_subs,
            'churn_rate': round(churn_rate, 1)
        }
    
    def calculate_ltv(self, user_id: int) -> float:
        """
        Calculate Lifetime Value for a user.
        
        Args:
            user_id: User ID
        
        Returns:
            LTV in EUR
        """
        if user_id not in self.subscriptions:
            return 0.0
        
        sub = self.subscriptions[user_id]
        
        # Calculate months subscribed
        if sub.is_active:
            end_date = datetime.now()
        else:
            end_date = sub.cancel_date or datetime.now()
        
        months = (end_date - sub.start_date).days / 30
        months = max(1, months)  # At least 1 month
        
        # LTV = monthly value * months subscribed
        ltv = sub.monthly_value * months
        
        return round(ltv, 2)
    
    # ========================================================================
    # CHURN PREDICTION
    # ========================================================================
    
    def predict_churn(self, user_id: int, engagement_data: Dict) -> ChurnPrediction:
        """
        Predict churn risk for a user.
        
        Args:
            user_id: User ID
            engagement_data: Dict with engagement metrics
        
        Returns:
            ChurnPrediction object
        """
        risk_score = 0.0
        factors = []
        
        # Factor 1: Low login frequency (30 points)
        days_since_login = engagement_data.get('days_since_login', 0)
        if days_since_login > 14:
            risk_score += 30
            factors.append("No login in 14+ days")
        elif days_since_login > 7:
            risk_score += 15
            factors.append("No login in 7+ days")
        
        # Factor 2: Low feature usage (25 points)
        searches_last_30d = engagement_data.get('searches_last_30d', 0)
        if searches_last_30d == 0:
            risk_score += 25
            factors.append("No searches in 30 days")
        elif searches_last_30d < 5:
            risk_score += 12
            factors.append("Low search activity")
        
        # Factor 3: No deals found (20 points)
        deals_last_30d = engagement_data.get('deals_found_last_30d', 0)
        if deals_last_30d == 0:
            risk_score += 20
            factors.append("No deals found in 30 days")
        
        # Factor 4: Empty watchlist (15 points)
        watchlist_size = engagement_data.get('watchlist_routes', 0)
        if watchlist_size == 0:
            risk_score += 15
            factors.append("Empty watchlist")
        
        # Factor 5: No social engagement (10 points)
        groups = engagement_data.get('groups_joined', 0)
        if groups == 0:
            risk_score += 10
            factors.append("Not in any groups")
        
        # Determine risk level
        if risk_score >= CHURN_RISK_THRESHOLDS['high']:
            risk_level = "high"
        elif risk_score >= CHURN_RISK_THRESHOLDS['medium']:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        # Recommended actions
        actions = self._get_winback_actions(risk_level, factors)
        
        prediction = ChurnPrediction(
            user_id=user_id,
            risk_score=min(100, risk_score),
            risk_level=risk_level,
            factors=factors,
            recommended_actions=actions,
            prediction_date=datetime.now()
        )
        
        # Save prediction
        self.churn_predictions[user_id] = prediction
        self._save_churn()
        
        # Update subscription
        if user_id in self.subscriptions:
            self.subscriptions[user_id].churn_risk_score = prediction.risk_score
            self._save_subscriptions()
        
        return prediction
    
    def _get_winback_actions(self, risk_level: str, factors: List[str]) -> List[str]:
        """
        Get recommended win-back actions based on risk.
        
        Args:
            risk_level: "low", "medium", "high"
            factors: List of risk factors
        
        Returns:
            List of action recommendations
        """
        actions = []
        
        if risk_level == "high":
            actions.append("🚨 Send urgent re-engagement email")
            actions.append("🎁 Offer 50% discount for 3 months")
            actions.append("📞 Personal call from support team")
        elif risk_level == "medium":
            actions.append("📧 Send value reminder email")
            actions.append("🎯 Highlight unused features")
            actions.append("💰 Show personal savings dashboard")
        else:  # low
            actions.append("💡 Send weekly deal digest")
            actions.append("🆕 Encourage watchlist setup")
        
        # Specific actions based on factors
        if "Empty watchlist" in factors:
            actions.append("➡️ Guide to set up watchlist")
        
        if "Not in any groups" in factors:
            actions.append("➡️ Invite to relevant groups")
        
        if "No deals found" in factors:
            actions.append("➡️ Suggest popular routes with deals")
        
        return actions
    
    def get_at_risk_users(self, min_risk: str = "medium") -> List[Tuple[int, ChurnPrediction]]:
        """
        Get list of users at risk of churning.
        
        Args:
            min_risk: Minimum risk level ("low", "medium", "high")
        
        Returns:
            List of (user_id, prediction) tuples
        """
        risk_levels = ["high", "medium", "low"]
        min_index = risk_levels.index(min_risk)
        target_levels = risk_levels[:min_index + 1]
        
        at_risk = [
            (user_id, pred)
            for user_id, pred in self.churn_predictions.items()
            if pred.risk_level in target_levels
        ]
        
        # Sort by risk score (highest first)
        at_risk.sort(key=lambda x: x[1].risk_score, reverse=True)
        
        return at_risk
    
    # ========================================================================
    # ANALYTICS DASHBOARD
    # ========================================================================
    
    def get_dashboard_summary(self) -> Dict:
        """
        Get complete analytics dashboard summary.
        
        Returns:
            Dict with all key metrics
        """
        revenue = self.get_revenue_metrics()
        funnel = self.get_funnel_stats(30)
        at_risk = self.get_at_risk_users("medium")
        
        return {
            'revenue': revenue,
            'funnel': funnel,
            'churn': {
                'high_risk_users': sum(1 for _, p in at_risk if p.risk_level == "high"),
                'medium_risk_users': sum(1 for _, p in at_risk if p.risk_level == "medium"),
                'total_at_risk': len(at_risk)
            }
        }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def format_analytics_dashboard(summary: Dict) -> str:
    """
    Format analytics dashboard for display.
    
    Args:
        summary: From get_dashboard_summary()
    
    Returns:
        Formatted string
    """
    rev = summary['revenue']
    funnel = summary['funnel']
    churn = summary['churn']
    
    return f"""📊 Premium Analytics Dashboard

💰 Revenue Metrics:
• MRR: €{rev['mrr']:,.2f}
• ARR: €{rev['arr']:,.2f}
• ARPU: €{rev['arpu']:.2f}
• Active subs: {rev['active_subscriptions']}
• Churn rate: {rev['churn_rate']}%

📩 Conversion Funnel (30d):
• Overall: {funnel['overall_conversion_rate']}%
{chr(10).join(f"  - {stage}: {data['users']} users ({data['conversion_rate']}%)" for stage, data in funnel['stages'].items())}

⚠️ Churn Risk:
• High risk: {churn['high_risk_users']} users
• Medium risk: {churn['medium_risk_users']} users
• Total at risk: {churn['total_at_risk']} users
"""


# ============================================================================
# MAIN (TESTING)
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("📊 TESTING: Premium Analytics")
    print("="*60 + "\n")
    
    # Initialize manager
    manager = AnalyticsManager()
    
    # Simulate funnel
    test_users = [10001, 10002, 10003, 10004, 10005]
    
    print("1️⃣ Funnel Tracking")
    print("-" * 40)
    
    for user_id in test_users:
        manager.track_funnel_event(user_id, "paywall_viewed")
    
    for user_id in test_users[:4]:
        manager.track_funnel_event(user_id, "paywall_clicked")
    
    for user_id in test_users[:3]:
        manager.track_funnel_event(user_id, "trial_started")
    
    for user_id in test_users[:2]:
        manager.track_funnel_event(user_id, "paid_converted")
        manager.add_subscription(user_id, "basic_monthly", "monthly", 9.99)
    
    funnel = manager.get_funnel_stats(30)
    print(f"Overall conversion: {funnel['overall_conversion_rate']}%")
    
    print("\n2️⃣ Revenue Metrics")
    print("-" * 40)
    
    revenue = manager.get_revenue_metrics()
    print(f"MRR: €{revenue['mrr']}")
    print(f"ARR: €{revenue['arr']}")
    print(f"ARPU: €{revenue['arpu']}")
    print(f"Active subs: {revenue['active_subscriptions']}")
    
    print("\n3️⃣ Churn Prediction")
    print("-" * 40)
    
    engagement = {
        'days_since_login': 15,
        'searches_last_30d': 2,
        'deals_found_last_30d': 0,
        'watchlist_routes': 0,
        'groups_joined': 0
    }
    
    prediction = manager.predict_churn(10001, engagement)
    print(f"Risk score: {prediction.risk_score}/100")
    print(f"Risk level: {prediction.risk_level}")
    print(f"Factors: {prediction.factors}")
    print(f"Actions: {prediction.recommended_actions}")
    
    print("\n4️⃣ Dashboard Summary")
    print("-" * 40)
    print(format_analytics_dashboard(manager.get_dashboard_summary()))
    
    print("\n" + "="*60)
    print("✅ Testing Complete!")
    print("="*60 + "\n")
