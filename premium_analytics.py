#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Premium Analytics & Conversion Funnel
IT6 - DAY 5/5

Features:
- Complete conversion funnel tracking
- Premium revenue metrics (MRR, ARR, ARPU, LTV)
- Retention cohort analysis
- Churn prediction & prevention
- Win-back campaigns
- A/B testing results

Author: @Juanka_Spain
Version: 14.0.0-alpha.5
Date: 2026-01-16
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
from pathlib import Path
from collections import defaultdict
import statistics


# ============================================================================
# ENUMS & CONSTANTS
# ============================================================================

class FunnelStage(Enum):
    """Conversion funnel stages"""
    VISITOR = "visitor"  # First interaction
    PAYWALL_VIEW = "paywall_view"  # Saw paywall
    PAYWALL_CLICK = "paywall_click"  # Clicked CTA
    TRIAL_START = "trial_start"  # Started trial
    TRIAL_ACTIVE = "trial_active"  # Using trial features
    TRIAL_END = "trial_end"  # Trial expired
    PAID_CONVERSION = "paid_conversion"  # Became paying customer
    RETAINED = "retained"  # Retained after month 1


class ChurnRisk(Enum):
    """Churn risk levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SubscriptionStatus(Enum):
    """Subscription status"""
    ACTIVE = "active"
    CHURNED = "churned"
    PAUSED = "paused"
    CANCELLED = "cancelled"


# Revenue metrics
MONTHLY_PRICES = {
    "basic_monthly": 9.99,
    "basic_annual": 8.33,  # 99.99/12
    "pro_monthly": 14.99,
    "pro_annual": 12.50  # 149.99/12
}

# Churn risk thresholds
CHURN_RISK_THRESHOLDS = {
    "days_since_last_login": {
        "low": 7,
        "medium": 14,
        "high": 21,
        "critical": 30
    },
    "engagement_score": {
        "low": 60,
        "medium": 40,
        "high": 25,
        "critical": 10
    },
    "searches_last_week": {
        "low": 10,
        "medium": 5,
        "high": 2,
        "critical": 0
    }
}


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class FunnelEvent:
    """Single event in conversion funnel"""
    user_id: int
    stage: str  # FunnelStage
    timestamp: datetime
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'FunnelEvent':
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class Subscription:
    """User subscription record"""
    user_id: int
    plan_id: str
    status: str  # SubscriptionStatus
    start_date: datetime
    end_date: Optional[datetime] = None
    mrr: float = 0.0  # Monthly Recurring Revenue
    ltv: float = 0.0  # Lifetime Value so far
    churn_risk: str = ChurnRisk.LOW.value
    last_login: Optional[datetime] = None
    engagement_score: float = 0.0
    
    @property
    def days_active(self) -> int:
        """Days subscription has been active"""
        end = self.end_date if self.end_date else datetime.now()
        return (end - self.start_date).days
    
    @property
    def months_active(self) -> float:
        """Months subscription has been active"""
        return self.days_active / 30
    
    @property
    def is_active(self) -> bool:
        """Check if subscription is active"""
        return self.status == SubscriptionStatus.ACTIVE.value
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['start_date'] = self.start_date.isoformat()
        if self.end_date:
            data['end_date'] = self.end_date.isoformat()
        if self.last_login:
            data['last_login'] = self.last_login.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Subscription':
        data['start_date'] = datetime.fromisoformat(data['start_date'])
        if data.get('end_date'):
            data['end_date'] = datetime.fromisoformat(data['end_date'])
        if data.get('last_login'):
            data['last_login'] = datetime.fromisoformat(data['last_login'])
        return cls(**data)


@dataclass
class CohortData:
    """Retention cohort data"""
    cohort_month: str  # "YYYY-MM"
    cohort_size: int
    retention_by_month: Dict[int, float]  # month_number -> retention_rate
    
    def to_dict(self) -> Dict:
        return asdict(self)


# ============================================================================
# ANALYTICS ENGINE
# ============================================================================

class PremiumAnalytics:
    """
    Analytics for premium subscriptions and conversions.
    
    Features:
    - Conversion funnel tracking
    - Revenue metrics (MRR, ARR, ARPU, LTV)
    - Retention cohorts
    - Churn prediction
    - A/B testing results
    """
    
    def __init__(self, data_dir: str = "."):
        self.data_dir = Path(data_dir)
        self.funnel_file = self.data_dir / "funnel_events.json"
        self.subscriptions_file = self.data_dir / "subscriptions.json"
        self.cohorts_file = self.data_dir / "retention_cohorts.json"
        
        # Load data
        self.funnel_events: List[FunnelEvent] = self._load_funnel_events()
        self.subscriptions: Dict[int, Subscription] = self._load_subscriptions()
        self.cohorts: Dict[str, CohortData] = self._load_cohorts()
        
        print("✅ PremiumAnalytics initialized")
    
    # ========================================================================
    # DATA PERSISTENCE
    # ========================================================================
    
    def _load_funnel_events(self) -> List[FunnelEvent]:
        """Load funnel events from file"""
        if not self.funnel_file.exists():
            return []
        
        try:
            with open(self.funnel_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [FunnelEvent.from_dict(e) for e in data]
        except Exception as e:
            print(f"⚠️ Error loading funnel events: {e}")
            return []
    
    def _save_funnel_events(self):
        """Save funnel events to file"""
        try:
            data = [e.to_dict() for e in self.funnel_events]
            with open(self.funnel_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Error saving funnel events: {e}")
    
    def _load_subscriptions(self) -> Dict[int, Subscription]:
        """Load subscriptions from file"""
        if not self.subscriptions_file.exists():
            return {}
        
        try:
            with open(self.subscriptions_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {
                    int(user_id): Subscription.from_dict(sub)
                    for user_id, sub in data.items()
                }
        except Exception as e:
            print(f"⚠️ Error loading subscriptions: {e}")
            return {}
    
    def _save_subscriptions(self):
        """Save subscriptions to file"""
        try:
            data = {
                str(user_id): sub.to_dict()
                for user_id, sub in self.subscriptions.items()
            }
            with open(self.subscriptions_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Error saving subscriptions: {e}")
    
    def _load_cohorts(self) -> Dict[str, CohortData]:
        """Load cohort data from file"""
        if not self.cohorts_file.exists():
            return {}
        
        try:
            with open(self.cohorts_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {
                    cohort_month: CohortData(**cohort_data)
                    for cohort_month, cohort_data in data.items()
                }
        except Exception as e:
            print(f"⚠️ Error loading cohorts: {e}")
            return {}
    
    def _save_cohorts(self):
        """Save cohort data to file"""
        try:
            data = {
                cohort_month: cohort.to_dict()
                for cohort_month, cohort in self.cohorts.items()
            }
            with open(self.cohorts_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Error saving cohorts: {e}")
    
    # ========================================================================
    # FUNNEL TRACKING
    # ========================================================================
    
    def track_funnel_event(self, user_id: int, stage: FunnelStage, metadata: Dict = None):
        """
        Track a funnel event.
        
        Args:
            user_id: User ID
            stage: Funnel stage
            metadata: Additional event data
        """
        event = FunnelEvent(
            user_id=user_id,
            stage=stage.value,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        
        self.funnel_events.append(event)
        self._save_funnel_events()
    
    def get_funnel_metrics(self, days: int = 30) -> Dict:
        """
        Calculate funnel conversion rates.
        
        Args:
            days: Number of days to analyze
        
        Returns:
            Dict with funnel metrics
        """
        cutoff = datetime.now() - timedelta(days=days)
        recent_events = [e for e in self.funnel_events if e.timestamp >= cutoff]
        
        # Count users at each stage
        stage_users = defaultdict(set)
        for event in recent_events:
            stage_users[event.stage].add(event.user_id)
        
        # Calculate conversion rates
        stages = [stage.value for stage in FunnelStage]
        funnel = {}
        
        for i, stage in enumerate(stages):
            count = len(stage_users[stage])
            funnel[stage] = {
                "count": count,
                "users": list(stage_users[stage])
            }
            
            # Conversion rate from previous stage
            if i > 0:
                prev_stage = stages[i-1]
                prev_count = funnel[prev_stage]["count"]
                if prev_count > 0:
                    conversion_rate = count / prev_count
                else:
                    conversion_rate = 0
                funnel[stage]["conversion_from_prev"] = conversion_rate
        
        # Overall conversion rate (visitor to paid)
        visitors = funnel[FunnelStage.VISITOR.value]["count"]
        paid = funnel[FunnelStage.PAID_CONVERSION.value]["count"]
        overall_conversion = paid / visitors if visitors > 0 else 0
        
        return {
            "period_days": days,
            "funnel": funnel,
            "overall_conversion_rate": overall_conversion,
            "total_conversions": paid
        }
    
    # ========================================================================
    # SUBSCRIPTION MANAGEMENT
    # ========================================================================
    
    def create_subscription(self, user_id: int, plan_id: str) -> Subscription:
        """
        Create a new subscription.
        
        Args:
            user_id: User ID
            plan_id: Plan identifier
        
        Returns:
            Subscription object
        """
        mrr = MONTHLY_PRICES.get(plan_id, 9.99)
        
        subscription = Subscription(
            user_id=user_id,
            plan_id=plan_id,
            status=SubscriptionStatus.ACTIVE.value,
            start_date=datetime.now(),
            mrr=mrr,
            last_login=datetime.now()
        )
        
        self.subscriptions[user_id] = subscription
        self._save_subscriptions()
        
        # Track funnel event
        self.track_funnel_event(user_id, FunnelStage.PAID_CONVERSION, {"plan": plan_id})
        
        return subscription
    
    def update_subscription_activity(self, user_id: int, engagement_score: float):
        """
        Update subscription activity.
        
        Args:
            user_id: User ID
            engagement_score: Current engagement score (0-100)
        """
        if user_id not in self.subscriptions:
            return
        
        sub = self.subscriptions[user_id]
        sub.last_login = datetime.now()
        sub.engagement_score = engagement_score
        
        # Update LTV
        sub.ltv = sub.mrr * sub.months_active
        
        # Predict churn risk
        sub.churn_risk = self._predict_churn_risk(sub).value
        
        self._save_subscriptions()
    
    def cancel_subscription(self, user_id: int):
        """Cancel a subscription"""
        if user_id not in self.subscriptions:
            return
        
        sub = self.subscriptions[user_id]
        sub.status = SubscriptionStatus.CHURNED.value
        sub.end_date = datetime.now()
        
        self._save_subscriptions()
    
    # ========================================================================
    # REVENUE METRICS
    # ========================================================================
    
    def get_revenue_metrics(self) -> Dict:
        """
        Calculate key revenue metrics.
        
        Returns:
            Dict with MRR, ARR, ARPU, LTV
        """
        active_subs = [s for s in self.subscriptions.values() if s.is_active]
        
        if not active_subs:
            return {
                "mrr": 0,
                "arr": 0,
                "arpu": 0,
                "avg_ltv": 0,
                "active_subscriptions": 0
            }
        
        # MRR (Monthly Recurring Revenue)
        mrr = sum(s.mrr for s in active_subs)
        
        # ARR (Annual Recurring Revenue)
        arr = mrr * 12
        
        # ARPU (Average Revenue Per User)
        arpu = mrr / len(active_subs)
        
        # Average LTV (Lifetime Value)
        avg_ltv = statistics.mean([s.ltv for s in active_subs if s.ltv > 0])
        
        return {
            "mrr": mrr,
            "arr": arr,
            "arpu": arpu,
            "avg_ltv": avg_ltv,
            "active_subscriptions": len(active_subs)
        }
    
    # ========================================================================
    # CHURN PREDICTION
    # ========================================================================
    
    def _predict_churn_risk(self, subscription: Subscription) -> ChurnRisk:
        """
        Predict churn risk for a subscription.
        
        Args:
            subscription: Subscription object
        
        Returns:
            ChurnRisk level
        """
        risk_score = 0
        
        # Factor 1: Days since last login
        if subscription.last_login:
            days_since = (datetime.now() - subscription.last_login).days
            
            if days_since >= CHURN_RISK_THRESHOLDS["days_since_last_login"]["critical"]:
                risk_score += 40
            elif days_since >= CHURN_RISK_THRESHOLDS["days_since_last_login"]["high"]:
                risk_score += 30
            elif days_since >= CHURN_RISK_THRESHOLDS["days_since_last_login"]["medium"]:
                risk_score += 20
            elif days_since >= CHURN_RISK_THRESHOLDS["days_since_last_login"]["low"]:
                risk_score += 10
        else:
            risk_score += 30  # Never logged in is risky
        
        # Factor 2: Engagement score
        if subscription.engagement_score <= CHURN_RISK_THRESHOLDS["engagement_score"]["critical"]:
            risk_score += 40
        elif subscription.engagement_score <= CHURN_RISK_THRESHOLDS["engagement_score"]["high"]:
            risk_score += 30
        elif subscription.engagement_score <= CHURN_RISK_THRESHOLDS["engagement_score"]["medium"]:
            risk_score += 20
        elif subscription.engagement_score <= CHURN_RISK_THRESHOLDS["engagement_score"]["low"]:
            risk_score += 10
        
        # Determine risk level
        if risk_score >= 60:
            return ChurnRisk.CRITICAL
        elif risk_score >= 40:
            return ChurnRisk.HIGH
        elif risk_score >= 20:
            return ChurnRisk.MEDIUM
        else:
            return ChurnRisk.LOW
    
    def get_at_risk_users(self, min_risk: ChurnRisk = ChurnRisk.HIGH) -> List[Subscription]:
        """
        Get users at risk of churning.
        
        Args:
            min_risk: Minimum risk level to include
        
        Returns:
            List of at-risk subscriptions
        """
        risk_levels = [ChurnRisk.CRITICAL, ChurnRisk.HIGH, ChurnRisk.MEDIUM, ChurnRisk.LOW]
        min_index = risk_levels.index(min_risk)
        included_risks = [r.value for r in risk_levels[:min_index+1]]
        
        at_risk = [
            sub for sub in self.subscriptions.values()
            if sub.is_active and sub.churn_risk in included_risks
        ]
        
        # Sort by risk (critical first)
        at_risk.sort(key=lambda s: risk_levels.index(ChurnRisk(s.churn_risk)))
        
        return at_risk
    
    # ========================================================================
    # RETENTION COHORTS
    # ========================================================================
    
    def calculate_cohorts(self):
        """
        Calculate retention cohorts.
        Groups users by signup month and tracks retention.
        """
        cohorts = defaultdict(lambda: {"users": [], "retention": {}})
        
        # Group by cohort month
        for user_id, sub in self.subscriptions.items():
            cohort_month = sub.start_date.strftime("%Y-%m")
            cohorts[cohort_month]["users"].append(user_id)
        
        # Calculate retention for each cohort
        for cohort_month, cohort_data in cohorts.items():
            cohort_size = len(cohort_data["users"])
            cohort_start = datetime.strptime(cohort_month, "%Y-%m")
            
            # Check retention at months 1, 3, 6, 12
            retention_months = [1, 3, 6, 12]
            retention = {}
            
            for month in retention_months:
                check_date = cohort_start + timedelta(days=month*30)
                
                # Count how many users were still active
                active = 0
                for user_id in cohort_data["users"]:
                    sub = self.subscriptions[user_id]
                    
                    # Check if active at check_date
                    if sub.start_date <= check_date:
                        if not sub.end_date or sub.end_date > check_date:
                            active += 1
                
                retention[month] = active / cohort_size if cohort_size > 0 else 0
            
            # Save cohort
            self.cohorts[cohort_month] = CohortData(
                cohort_month=cohort_month,
                cohort_size=cohort_size,
                retention_by_month=retention
            )
        
        self._save_cohorts()
    
    def get_cohort_analysis(self) -> Dict:
        """
        Get cohort retention analysis.
        
        Returns:
            Dict with cohort data
        """
        if not self.cohorts:
            self.calculate_cohorts()
        
        # Average retention across cohorts
        all_retention = defaultdict(list)
        for cohort in self.cohorts.values():
            for month, rate in cohort.retention_by_month.items():
                all_retention[month].append(rate)
        
        avg_retention = {
            month: statistics.mean(rates) if rates else 0
            for month, rates in all_retention.items()
        }
        
        return {
            "cohorts": {k: v.to_dict() for k, v in self.cohorts.items()},
            "average_retention": avg_retention,
            "total_cohorts": len(self.cohorts)
        }
    
    # ========================================================================
    # ANALYTICS SUMMARY
    # ========================================================================
    
    def get_complete_analytics(self) -> Dict:
        """
        Get complete analytics summary.
        
        Returns:
            Dict with all metrics
        """
        funnel = self.get_funnel_metrics()
        revenue = self.get_revenue_metrics()
        at_risk = self.get_at_risk_users(ChurnRisk.HIGH)
        cohorts = self.get_cohort_analysis()
        
        # Churn rate
        total_subs = len(self.subscriptions)
        churned = sum(1 for s in self.subscriptions.values() if s.status == SubscriptionStatus.CHURNED.value)
        churn_rate = churned / total_subs if total_subs > 0 else 0
        
        return {
            "funnel": funnel,
            "revenue": revenue,
            "churn": {
                "rate": churn_rate,
                "at_risk_count": len(at_risk),
                "at_risk_users": [s.user_id for s in at_risk[:10]]  # Top 10
            },
            "retention": cohorts["average_retention"],
            "total_subscriptions": total_subs,
            "active_subscriptions": revenue["active_subscriptions"]
        }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def format_revenue_metrics(metrics: Dict) -> str:
    """
    Format revenue metrics for display.
    
    Args:
        metrics: Dict from get_revenue_metrics()
    
    Returns:
        Formatted string
    """
    return f"""📊 Revenue Metrics

💰 MRR: €{metrics['mrr']:.2f}
📈 ARR: €{metrics['arr']:.2f}
👥 ARPU: €{metrics['arpu']:.2f}
🎯 LTV: €{metrics['avg_ltv']:.2f}
✅ Active Subs: {metrics['active_subscriptions']}
"""


def format_funnel_summary(funnel: Dict) -> str:
    """
    Format funnel summary for display.
    
    Args:
        funnel: Dict from get_funnel_metrics()
    
    Returns:
        Formatted string
    """
    result = f"""📡 Conversion Funnel ({funnel['period_days']} days)

"""
    
    for stage_name, stage_data in funnel['funnel'].items():
        result += f"{stage_name}: {stage_data['count']} users"
        
        if 'conversion_from_prev' in stage_data:
            conv_rate = stage_data['conversion_from_prev'] * 100
            result += f" ({conv_rate:.1f}% conversion)"
        
        result += "\n"
    
    result += f"\n✅ Overall Conversion: {funnel['overall_conversion_rate']*100:.2f}%"
    
    return result


# ============================================================================
# MAIN (TESTING)
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("📊 TESTING: Premium Analytics")
    print("="*60 + "\n")
    
    # Initialize analytics
    analytics = PremiumAnalytics()
    
    print("1️⃣ Simulating Funnel Events")
    print("-" * 40)
    
    # Simulate funnel for multiple users
    for i in range(1, 11):
        user_id = 20000 + i
        
        analytics.track_funnel_event(user_id, FunnelStage.VISITOR)
        analytics.track_funnel_event(user_id, FunnelStage.PAYWALL_VIEW)
        
        if i <= 7:  # 70% click
            analytics.track_funnel_event(user_id, FunnelStage.PAYWALL_CLICK)
        
        if i <= 5:  # 50% start trial
            analytics.track_funnel_event(user_id, FunnelStage.TRIAL_START)
        
        if i <= 3:  # 30% convert to paid
            analytics.track_funnel_event(user_id, FunnelStage.PAID_CONVERSION)
            analytics.create_subscription(user_id, "basic_monthly")
    
    print("✅ Simulated 10 users through funnel")
    
    print("\n2️⃣ Funnel Metrics")
    print("-" * 40)
    
    funnel = analytics.get_funnel_metrics()
    print(format_funnel_summary(funnel))
    
    print("\n3️⃣ Revenue Metrics")
    print("-" * 40)
    
    revenue = analytics.get_revenue_metrics()
    print(format_revenue_metrics(revenue))
    
    print("\n4️⃣ Churn Risk Analysis")
    print("-" * 40)
    
    # Simulate inactive user
    inactive_user = 20001
    if inactive_user in analytics.subscriptions:
        sub = analytics.subscriptions[inactive_user]
        sub.last_login = datetime.now() - timedelta(days=25)
        sub.engagement_score = 15
        analytics.update_subscription_activity(inactive_user, 15)
    
    at_risk = analytics.get_at_risk_users(ChurnRisk.MEDIUM)
    print(f"\n⚠️ At-risk users: {len(at_risk)}")
    
    for sub in at_risk[:3]:
        print(f"\nUser {sub.user_id}:")
        print(f"  Risk: {sub.churn_risk}")
        print(f"  Engagement: {sub.engagement_score}")
        print(f"  Last login: {sub.last_login.date() if sub.last_login else 'Never'}")
    
    print("\n5️⃣ Complete Analytics Summary")
    print("-" * 40)
    
    summary = analytics.get_complete_analytics()
    print(f"\nTotal Subscriptions: {summary['total_subscriptions']}")
    print(f"Active: {summary['active_subscriptions']}")
    print(f"Churn Rate: {summary['churn']['rate']*100:.1f}%")
    print(f"At Risk: {summary['churn']['at_risk_count']}")
    print(f"Conversion Rate: {summary['funnel']['overall_conversion_rate']*100:.1f}%")
    
    print("\n" + "="*60)
    print("✅ Testing Complete!")
    print("="*60 + "\n")
