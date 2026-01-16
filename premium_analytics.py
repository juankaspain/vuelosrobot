#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Premium Analytics and Conversion Tracking
IT6 - DAY 5/5

Features:
- Conversion funnel tracking (Paywall → Trial → Paid)
- Revenue metrics (MRR, ARR, ARPU, LTV)
- Retention analysis and cohorts
- Churn prediction and prevention
- A/B test performance tracking

Author: @Juanka_Spain
Version: 14.0.0-alpha.5
Date: 2026-01-16
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from collections import defaultdict


# ============================================================================
# ENUMS & CONSTANTS
# ============================================================================

class FunnelStage(Enum):
    """Conversion funnel stages"""
    PAYWALL_VIEW = "paywall_view"
    PAYWALL_CLICK = "paywall_click"
    TRIAL_START = "trial_start"
    TRIAL_ACTIVE = "trial_active"
    TRIAL_ENGAGED = "trial_engaged"  # Used premium features
    CONVERTED = "converted"  # Paid subscription
    CHURNED = "churned"


class ChurnRisk(Enum):
    """Churn risk levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class FunnelEvent:
    """Single event in conversion funnel"""
    user_id: int
    stage: str  # FunnelStage value
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
class UserJourney:
    """Complete user conversion journey"""
    user_id: int
    first_paywall_view: Optional[datetime] = None
    first_paywall_click: Optional[datetime] = None
    trial_start: Optional[datetime] = None
    conversion_date: Optional[datetime] = None
    churn_date: Optional[datetime] = None
    
    # Funnel metrics
    paywall_views: int = 0
    paywall_clicks: int = 0
    trial_engagement_score: float = 0
    days_to_convert: Optional[int] = None
    
    @property
    def current_stage(self) -> str:
        """Get current funnel stage"""
        if self.churn_date:
            return FunnelStage.CHURNED.value
        if self.conversion_date:
            return FunnelStage.CONVERTED.value
        if self.trial_start:
            if self.trial_engagement_score > 50:
                return FunnelStage.TRIAL_ENGAGED.value
            return FunnelStage.TRIAL_ACTIVE.value
        if self.first_paywall_click:
            return FunnelStage.PAYWALL_CLICK.value
        if self.first_paywall_view:
            return FunnelStage.PAYWALL_VIEW.value
        return "not_started"
    
    @property
    def is_active(self) -> bool:
        """Check if user is active (not churned)"""
        return self.churn_date is None
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        for field in ['first_paywall_view', 'first_paywall_click', 'trial_start', 'conversion_date', 'churn_date']:
            if data[field]:
                data[field] = data[field].isoformat()
        data['current_stage'] = self.current_stage
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'UserJourney':
        # Remove computed field
        data.pop('current_stage', None)
        
        for field in ['first_paywall_view', 'first_paywall_click', 'trial_start', 'conversion_date', 'churn_date']:
            if data.get(field):
                data[field] = datetime.fromisoformat(data[field])
        return cls(**data)


@dataclass
class RevenueMetrics:
    """Revenue and business metrics"""
    # Current metrics
    mrr: float = 0  # Monthly Recurring Revenue
    arr: float = 0  # Annual Recurring Revenue
    total_revenue: float = 0
    
    # User metrics
    total_paying_users: int = 0
    monthly_users: int = 0
    annual_users: int = 0
    
    # Averages
    arpu: float = 0  # Average Revenue Per User
    avg_ltv: float = 0  # Average Lifetime Value
    
    # Growth
    new_mrr_this_month: float = 0
    churned_mrr_this_month: float = 0
    net_mrr_growth: float = 0
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ChurnAnalysis:
    """Churn prediction and analysis"""
    user_id: int
    risk_level: str  # ChurnRisk value
    churn_probability: float  # 0-1
    days_since_activity: int
    engagement_trend: str  # "increasing", "stable", "declining"
    warning_signals: List[str]
    recommended_actions: List[str]
    
    def to_dict(self) -> Dict:
        return asdict(self)


# ============================================================================
# PREMIUM ANALYTICS
# ============================================================================

class PremiumAnalytics:
    """
    Analytics and tracking for premium conversions.
    
    Features:
    - Conversion funnel tracking
    - Revenue metrics (MRR, ARR, ARPU, LTV)
    - Retention cohort analysis
    - Churn prediction
    - A/B test performance
    """
    
    def __init__(self, data_dir: str = "."):
        self.data_dir = Path(data_dir)
        
        # Data files
        self.funnel_file = self.data_dir / "conversion_funnel.json"
        self.journey_file = self.data_dir / "user_journeys.json"
        self.revenue_file = self.data_dir / "revenue_metrics.json"
        
        # Load data
        self.funnel_events: List[FunnelEvent] = self._load_funnel_events()
        self.journeys: Dict[int, UserJourney] = self._load_journeys()
        
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
                return [FunnelEvent.from_dict(event) for event in data]
        except Exception as e:
            print(f"⚠️ Error loading funnel events: {e}")
            return []
    
    def _save_funnel_events(self):
        """Save funnel events to file"""
        try:
            data = [event.to_dict() for event in self.funnel_events]
            with open(self.funnel_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Error saving funnel events: {e}")
    
    def _load_journeys(self) -> Dict[int, UserJourney]:
        """Load user journeys from file"""
        if not self.journey_file.exists():
            return {}
        
        try:
            with open(self.journey_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {
                    int(user_id): UserJourney.from_dict(journey)
                    for user_id, journey in data.items()
                }
        except Exception as e:
            print(f"⚠️ Error loading journeys: {e}")
            return {}
    
    def _save_journeys(self):
        """Save user journeys to file"""
        try:
            data = {
                str(user_id): journey.to_dict()
                for user_id, journey in self.journeys.items()
            }
            with open(self.journey_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Error saving journeys: {e}")
    
    # ========================================================================
    # FUNNEL TRACKING
    # ========================================================================
    
    def track_funnel_event(self, user_id: int, stage: FunnelStage, metadata: Dict = None):
        """
        Track a funnel event.
        
        Args:
            user_id: User ID
            stage: FunnelStage enum
            metadata: Optional event metadata
        """
        # Create event
        event = FunnelEvent(
            user_id=user_id,
            stage=stage.value,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        
        self.funnel_events.append(event)
        self._save_funnel_events()
        
        # Update user journey
        self._update_journey(user_id, stage)
    
    def _update_journey(self, user_id: int, stage: FunnelStage):
        """Update user journey with new stage"""
        if user_id not in self.journeys:
            self.journeys[user_id] = UserJourney(user_id=user_id)
        
        journey = self.journeys[user_id]
        now = datetime.now()
        
        if stage == FunnelStage.PAYWALL_VIEW:
            journey.paywall_views += 1
            if not journey.first_paywall_view:
                journey.first_paywall_view = now
        
        elif stage == FunnelStage.PAYWALL_CLICK:
            journey.paywall_clicks += 1
            if not journey.first_paywall_click:
                journey.first_paywall_click = now
        
        elif stage == FunnelStage.TRIAL_START:
            if not journey.trial_start:
                journey.trial_start = now
        
        elif stage == FunnelStage.CONVERTED:
            if not journey.conversion_date:
                journey.conversion_date = now
                
                # Calculate days to convert
                if journey.first_paywall_view:
                    journey.days_to_convert = (now - journey.first_paywall_view).days
        
        elif stage == FunnelStage.CHURNED:
            journey.churn_date = now
        
        self._save_journeys()
    
    def get_journey(self, user_id: int) -> Optional[UserJourney]:
        """Get user's conversion journey"""
        return self.journeys.get(user_id)
    
    def update_trial_engagement(self, user_id: int, engagement_score: float):
        """Update trial engagement score"""
        if user_id in self.journeys:
            self.journeys[user_id].trial_engagement_score = engagement_score
            self._save_journeys()
    
    # ========================================================================
    # FUNNEL ANALYSIS
    # ========================================================================
    
    def get_funnel_metrics(self, days: int = 30) -> Dict:
        """
        Get conversion funnel metrics.
        
        Args:
            days: Number of days to analyze
        
        Returns:
            Funnel metrics with conversion rates
        """
        cutoff = datetime.now() - timedelta(days=days)
        
        # Count users at each stage
        stage_counts = defaultdict(set)
        
        for journey in self.journeys.values():
            user_id = journey.user_id
            
            if journey.first_paywall_view and journey.first_paywall_view >= cutoff:
                stage_counts[FunnelStage.PAYWALL_VIEW.value].add(user_id)
            
            if journey.first_paywall_click and journey.first_paywall_click >= cutoff:
                stage_counts[FunnelStage.PAYWALL_CLICK.value].add(user_id)
            
            if journey.trial_start and journey.trial_start >= cutoff:
                stage_counts[FunnelStage.TRIAL_START.value].add(user_id)
                
                if journey.trial_engagement_score > 50:
                    stage_counts[FunnelStage.TRIAL_ENGAGED.value].add(user_id)
            
            if journey.conversion_date and journey.conversion_date >= cutoff:
                stage_counts[FunnelStage.CONVERTED.value].add(user_id)
        
        # Calculate counts
        paywall_views = len(stage_counts[FunnelStage.PAYWALL_VIEW.value])
        paywall_clicks = len(stage_counts[FunnelStage.PAYWALL_CLICK.value])
        trial_starts = len(stage_counts[FunnelStage.TRIAL_START.value])
        trial_engaged = len(stage_counts[FunnelStage.TRIAL_ENGAGED.value])
        converted = len(stage_counts[FunnelStage.CONVERTED.value])
        
        # Calculate conversion rates
        click_rate = (paywall_clicks / paywall_views * 100) if paywall_views > 0 else 0
        trial_rate = (trial_starts / paywall_clicks * 100) if paywall_clicks > 0 else 0
        engagement_rate = (trial_engaged / trial_starts * 100) if trial_starts > 0 else 0
        conversion_rate = (converted / trial_starts * 100) if trial_starts > 0 else 0
        overall_conversion = (converted / paywall_views * 100) if paywall_views > 0 else 0
        
        return {
            'period_days': days,
            'funnel': {
                'paywall_views': paywall_views,
                'paywall_clicks': paywall_clicks,
                'trial_starts': trial_starts,
                'trial_engaged': trial_engaged,
                'converted': converted
            },
            'conversion_rates': {
                'view_to_click': round(click_rate, 2),
                'click_to_trial': round(trial_rate, 2),
                'trial_to_engaged': round(engagement_rate, 2),
                'trial_to_paid': round(conversion_rate, 2),
                'overall': round(overall_conversion, 2)
            },
            'avg_days_to_convert': self._calculate_avg_days_to_convert(cutoff)
        }
    
    def _calculate_avg_days_to_convert(self, cutoff: datetime) -> float:
        """Calculate average days from first view to conversion"""
        converted_journeys = [
            j for j in self.journeys.values()
            if j.conversion_date and j.conversion_date >= cutoff and j.days_to_convert is not None
        ]
        
        if not converted_journeys:
            return 0
        
        return sum(j.days_to_convert for j in converted_journeys) / len(converted_journeys)
    
    # ========================================================================
    # REVENUE METRICS
    # ========================================================================
    
    def calculate_revenue_metrics(self, subscription_data: Dict[int, Dict]) -> RevenueMetrics:
        """
        Calculate revenue metrics.
        
        Args:
            subscription_data: Dict of {user_id: {'plan': str, 'price': float, 'started': datetime}}
        
        Returns:
            RevenueMetrics object
        """
        metrics = RevenueMetrics()
        
        monthly_revenue = 0
        annual_revenue = 0
        total_revenue = 0
        
        monthly_users = 0
        annual_users = 0
        
        for user_id, sub in subscription_data.items():
            price = sub.get('price', 0)
            plan = sub.get('plan', 'monthly')
            
            total_revenue += price
            
            if 'monthly' in plan:
                monthly_revenue += price
                monthly_users += 1
            else:
                # Convert annual to monthly equivalent
                annual_revenue += price
                monthly_revenue += price / 12
                annual_users += 1
        
        metrics.mrr = round(monthly_revenue, 2)
        metrics.arr = round(metrics.mrr * 12, 2)
        metrics.total_revenue = round(total_revenue, 2)
        
        metrics.monthly_users = monthly_users
        metrics.annual_users = annual_users
        metrics.total_paying_users = monthly_users + annual_users
        
        # ARPU
        if metrics.total_paying_users > 0:
            metrics.arpu = round(metrics.mrr / metrics.total_paying_users, 2)
        
        # Estimate LTV (simple: ARPU * avg lifetime in months)
        # Assume avg lifetime = 12 months
        metrics.avg_ltv = round(metrics.arpu * 12, 2)
        
        return metrics
    
    # ========================================================================
    # CHURN ANALYSIS
    # ========================================================================
    
    def predict_churn_risk(self, user_id: int, recent_activity: Dict) -> ChurnAnalysis:
        """
        Predict churn risk for a user.
        
        Args:
            user_id: User ID
            recent_activity: Dict with activity metrics:
                - last_active: datetime
                - searches_last_week: int
                - deals_found_last_week: int
                - notifications_opened: int
                - engagement_score: float
        
        Returns:
            ChurnAnalysis with risk assessment
        """
        warnings = []
        actions = []
        risk_score = 0
        
        # Check last activity
        last_active = recent_activity.get('last_active')
        if last_active:
            days_inactive = (datetime.now() - last_active).days
        else:
            days_inactive = 999
        
        if days_inactive > 14:
            warnings.append("⚠️ No activo en 14+ días")
            actions.append("📧 Enviar email de re-engagement")
            risk_score += 30
        elif days_inactive > 7:
            warnings.append("⚠️ Inactivo más de 1 semana")
            actions.append("🔔 Notificar chollos personalizados")
            risk_score += 15
        
        # Check search activity
        searches = recent_activity.get('searches_last_week', 0)
        if searches == 0:
            warnings.append("❌ 0 búsquedas esta semana")
            actions.append("🔍 Sugerir rutas populares")
            risk_score += 20
        elif searches < 3:
            warnings.append("📉 Baja actividad de búsqueda")
            risk_score += 10
        
        # Check deal engagement
        deals = recent_activity.get('deals_found_last_week', 0)
        if deals == 0:
            warnings.append("❌ No ha encontrado chollos")
            actions.append("💰 Mostrar value dashboard")
            risk_score += 15
        
        # Check notification engagement
        notif_opened = recent_activity.get('notifications_opened', 0)
        if notif_opened == 0:
            warnings.append("🔕 No abre notificaciones")
            actions.append("⚙️ Optimizar horario de notificaciones")
            risk_score += 10
        
        # Check engagement score
        engagement = recent_activity.get('engagement_score', 50)
        if engagement < 30:
            warnings.append("📉 Engagement muy bajo")
            actions.append("🎁 Ofrecer descuento de retención")
            risk_score += 25
        elif engagement < 50:
            risk_score += 10
        
        # Determine risk level
        if risk_score >= 60:
            risk_level = ChurnRisk.CRITICAL
        elif risk_score >= 40:
            risk_level = ChurnRisk.HIGH
        elif risk_score >= 20:
            risk_level = ChurnRisk.MEDIUM
        else:
            risk_level = ChurnRisk.LOW
        
        # Determine trend
        if len(warnings) >= 4:
            trend = "declining"
        elif len(warnings) <= 1:
            trend = "increasing"
        else:
            trend = "stable"
        
        churn_prob = min(1.0, risk_score / 100)
        
        return ChurnAnalysis(
            user_id=user_id,
            risk_level=risk_level.value,
            churn_probability=round(churn_prob, 2),
            days_since_activity=days_inactive,
            engagement_trend=trend,
            warning_signals=warnings,
            recommended_actions=actions
        )
    
    def get_high_churn_risk_users(self, user_activities: Dict[int, Dict]) -> List[ChurnAnalysis]:
        """
        Get list of users at high churn risk.
        
        Args:
            user_activities: Dict of {user_id: activity_dict}
        
        Returns:
            List of ChurnAnalysis for high-risk users
        """
        high_risk = []
        
        for user_id, activity in user_activities.items():
            analysis = self.predict_churn_risk(user_id, activity)
            
            if analysis.risk_level in [ChurnRisk.HIGH.value, ChurnRisk.CRITICAL.value]:
                high_risk.append(analysis)
        
        # Sort by risk (highest first)
        high_risk.sort(key=lambda x: x.churn_probability, reverse=True)
        
        return high_risk
    
    # ========================================================================
    # RETENTION COHORTS
    # ========================================================================
    
    def calculate_retention_cohorts(self, months: int = 6) -> Dict:
        """
        Calculate retention cohorts.
        
        Args:
            months: Number of months to analyze
        
        Returns:
            Cohort retention data
        """
        cohorts = defaultdict(lambda: {'started': 0, 'retained': defaultdict(int)})
        
        for journey in self.journeys.values():
            if not journey.conversion_date:
                continue
            
            # Get cohort month
            cohort = journey.conversion_date.strftime('%Y-%m')
            cohorts[cohort]['started'] += 1
            
            # Check if still active (not churned)
            if journey.is_active:
                months_since = (datetime.now().year - journey.conversion_date.year) * 12 + \
                               (datetime.now().month - journey.conversion_date.month)
                
                for month in range(months_since + 1):
                    cohorts[cohort]['retained'][month] += 1
        
        # Calculate retention rates
        cohort_analysis = {}
        for cohort, data in cohorts.items():
            started = data['started']
            retained = data['retained']
            
            retention_rates = {}
            for month, count in retained.items():
                retention_rates[f'month_{month}'] = round((count / started * 100) if started > 0 else 0, 1)
            
            cohort_analysis[cohort] = {
                'users_started': started,
                'retention_rates': retention_rates
            }
        
        return cohort_analysis
    
    # ========================================================================
    # SUMMARY STATS
    # ========================================================================
    
    def get_summary_stats(self) -> Dict:
        """Get overall summary statistics"""
        total_journeys = len(self.journeys)
        
        # Current stage distribution
        stage_dist = defaultdict(int)
        for journey in self.journeys.values():
            stage_dist[journey.current_stage] += 1
        
        # Conversion stats
        converted = sum(1 for j in self.journeys.values() if j.conversion_date)
        churned = sum(1 for j in self.journeys.values() if j.churn_date)
        
        return {
            'total_users_tracked': total_journeys,
            'converted_users': converted,
            'churned_users': churned,
            'active_premium_users': converted - churned,
            'stage_distribution': dict(stage_dist),
            'overall_conversion_rate': round((converted / total_journeys * 100) if total_journeys > 0 else 0, 2)
        }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def format_funnel_report(metrics: Dict) -> str:
    """
    Format funnel metrics as a report.
    
    Args:
        metrics: Dict from get_funnel_metrics()
    
    Returns:
        Formatted report string
    """
    funnel = metrics['funnel']
    rates = metrics['conversion_rates']
    
    report = f"""📊 Conversion Funnel Report
⏰ Últimos {metrics['period_days']} días

🔽 FUNNEL:
1️⃣ Paywall Views: {funnel['paywall_views']}
   ⬇️ {rates['view_to_click']}%
2️⃣ Paywall Clicks: {funnel['paywall_clicks']}
   ⬇️ {rates['click_to_trial']}%
3️⃣ Trial Starts: {funnel['trial_starts']}
   ⬇️ {rates['trial_to_engaged']}%
4️⃣ Trial Engaged: {funnel['trial_engaged']}
   ⬇️ {rates['trial_to_paid']}%
5️⃣ CONVERTED: {funnel['converted']}

🎯 Overall Conversion: {rates['overall']}%
⏱️ Avg Days to Convert: {metrics['avg_days_to_convert']:.1f}
"""
    
    return report


def format_churn_alert(analysis: ChurnAnalysis) -> str:
    """
    Format churn analysis as an alert.
    
    Args:
        analysis: ChurnAnalysis object
    
    Returns:
        Formatted alert string
    """
    risk_emoji = {
        'low': '🟢',
        'medium': '🟡',
        'high': '🟠',
        'critical': '🔴'
    }
    
    emoji = risk_emoji.get(analysis.risk_level, '⚪')
    
    alert = f"""{emoji} CHURN RISK ALERT

User ID: {analysis.user_id}
Risk Level: {analysis.risk_level.upper()}
Churn Probability: {analysis.churn_probability * 100:.0f}%
Days Inactive: {analysis.days_since_activity}
Trend: {analysis.engagement_trend}

⚠️ Warning Signals:
"""
    
    for warning in analysis.warning_signals:
        alert += f"  {warning}\n"
    
    alert += "\n🛠️ Recommended Actions:\n"
    for action in analysis.recommended_actions:
        alert += f"  {action}\n"
    
    return alert


# ============================================================================
# MAIN (TESTING)
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("📊 TESTING: Premium Analytics")
    print("="*60 + "\n")
    
    # Initialize analytics
    analytics = PremiumAnalytics()
    
    # Simulate user journey
    test_user = 77777
    
    print("1️⃣ Tracking Funnel Events")
    print("-" * 40)
    
    analytics.track_funnel_event(test_user, FunnelStage.PAYWALL_VIEW)
    analytics.track_funnel_event(test_user, FunnelStage.PAYWALL_CLICK)
    analytics.track_funnel_event(test_user, FunnelStage.TRIAL_START)
    analytics.update_trial_engagement(test_user, 75)
    analytics.track_funnel_event(test_user, FunnelStage.CONVERTED)
    
    journey = analytics.get_journey(test_user)
    print(f"User journey: {journey.current_stage}")
    print(f"Days to convert: {journey.days_to_convert}")
    
    print("\n2️⃣ Funnel Metrics")
    print("-" * 40)
    
    funnel_metrics = analytics.get_funnel_metrics(30)
    print(format_funnel_report(funnel_metrics))
    
    print("\n3️⃣ Churn Prediction")
    print("-" * 40)
    
    # Simulate at-risk user
    at_risk_activity = {
        'last_active': datetime.now() - timedelta(days=15),
        'searches_last_week': 0,
        'deals_found_last_week': 0,
        'notifications_opened': 0,
        'engagement_score': 25
    }
    
    churn_analysis = analytics.predict_churn_risk(88888, at_risk_activity)
    print(format_churn_alert(churn_analysis))
    
    print("\n4️⃣ Summary Stats")
    print("-" * 40)
    
    stats = analytics.get_summary_stats()
    print(f"Total users tracked: {stats['total_users_tracked']}")
    print(f"Converted: {stats['converted_users']}")
    print(f"Active premium: {stats['active_premium_users']}")
    print(f"Conversion rate: {stats['overall_conversion_rate']}%")
    
    print("\n" + "="*60)
    print("✅ Testing Complete!")
    print("="*60 + "\n")
