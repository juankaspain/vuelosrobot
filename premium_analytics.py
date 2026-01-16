#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Premium Analytics & Conversion Funnel
IT6 - DAY 5/5

Features:
- Complete conversion funnel tracking
- Revenue metrics (MRR, ARR, ARPU, LTV)
- Retention cohort analysis
- Churn prediction and prevention
- A/B test result analysis
- Premium user behavior tracking

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
import statistics


# ============================================================================
# CONSTANTS
# ============================================================================

# Funnel stages
FUNNEL_STAGES = [
    "user_registered",
    "paywall_viewed",
    "paywall_clicked",
    "trial_started",
    "feature_used",
    "converted_to_paid"
]

# Churn risk thresholds
CHURN_RISK_LOW = 0.3
CHURN_RISK_MEDIUM = 0.6
CHURN_RISK_HIGH = 0.8


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class FunnelEvent:
    """A single funnel event"""
    user_id: int
    stage: str
    timestamp: datetime
    metadata: Dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'FunnelEvent':
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class RevenueMetrics:
    """Revenue metrics for a period"""
    period_start: datetime
    period_end: datetime
    new_customers: int
    churned_customers: int
    active_customers: int
    mrr: float  # Monthly Recurring Revenue
    arr: float  # Annual Recurring Revenue
    arpu: float  # Average Revenue Per User
    ltv: float  # Lifetime Value
    churn_rate: float
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['period_start'] = self.period_start.isoformat()
        data['period_end'] = self.period_end.isoformat()
        return data


@dataclass
class ChurnPrediction:
    """Churn prediction for a user"""
    user_id: int
    churn_score: float  # 0-1, higher = more likely to churn
    risk_level: str  # "low", "medium", "high"
    contributing_factors: List[str]
    recommended_actions: List[str]
    predicted_at: datetime
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['predicted_at'] = self.predicted_at.isoformat()
        return data


# ============================================================================
# ANALYTICS ENGINE
# ============================================================================

class PremiumAnalytics:
    """
    Analytics engine for premium conversion and retention.
    
    Tracks:
    - Conversion funnel
    - Revenue metrics
    - User cohorts
    - Churn risk
    """
    
    def __init__(self, data_dir: str = "."):
        self.data_dir = Path(data_dir)
        self.funnel_file = self.data_dir / "conversion_funnel.json"
        self.revenue_file = self.data_dir / "revenue_metrics.json"
        self.churn_file = self.data_dir / "churn_predictions.json"
        
        # Load data
        self.funnel_events: List[FunnelEvent] = self._load_funnel_events()
        self.revenue_history: List[RevenueMetrics] = self._load_revenue_metrics()
        self.churn_predictions: Dict[int, ChurnPrediction] = self._load_churn_predictions()
        
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
    
    def _load_revenue_metrics(self) -> List[RevenueMetrics]:
        """Load revenue metrics from file"""
        if not self.revenue_file.exists():
            return []
        
        try:
            with open(self.revenue_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [
                    RevenueMetrics(
                        period_start=datetime.fromisoformat(m['period_start']),
                        period_end=datetime.fromisoformat(m['period_end']),
                        **{k: v for k, v in m.items() if k not in ['period_start', 'period_end']}
                    )
                    for m in data
                ]
        except Exception as e:
            print(f"⚠️ Error loading revenue metrics: {e}")
            return []
    
    def _save_revenue_metrics(self):
        """Save revenue metrics to file"""
        try:
            data = [m.to_dict() for m in self.revenue_history]
            with open(self.revenue_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Error saving revenue metrics: {e}")
    
    def _load_churn_predictions(self) -> Dict[int, ChurnPrediction]:
        """Load churn predictions from file"""
        if not self.churn_file.exists():
            return {}
        
        try:
            with open(self.churn_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {
                    int(user_id): ChurnPrediction(
                        user_id=pred['user_id'],
                        churn_score=pred['churn_score'],
                        risk_level=pred['risk_level'],
                        contributing_factors=pred['contributing_factors'],
                        recommended_actions=pred['recommended_actions'],
                        predicted_at=datetime.fromisoformat(pred['predicted_at'])
                    )
                    for user_id, pred in data.items()
                }
        except Exception as e:
            print(f"⚠️ Error loading churn predictions: {e}")
            return {}
    
    def _save_churn_predictions(self):
        """Save churn predictions to file"""
        try:
            data = {
                str(user_id): pred.to_dict()
                for user_id, pred in self.churn_predictions.items()
            }
            with open(self.churn_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Error saving churn predictions: {e}")
    
    # ========================================================================
    # FUNNEL TRACKING
    # ========================================================================
    
    def track_funnel_event(self, user_id: int, stage: str, metadata: Dict = None):
        """
        Track a funnel event for a user.
        
        Args:
            user_id: User ID
            stage: Funnel stage (from FUNNEL_STAGES)
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
        self._save_funnel_events()
    
    def get_user_funnel_progress(self, user_id: int) -> List[str]:
        """Get funnel stages completed by user"""
        user_events = [e for e in self.funnel_events if e.user_id == user_id]
        stages = list(set(e.stage for e in user_events))
        
        # Sort by funnel stage order
        return sorted(stages, key=lambda s: FUNNEL_STAGES.index(s) if s in FUNNEL_STAGES else 999)
    
    def calculate_funnel_conversion(self, days: int = 30) -> Dict:
        """
        Calculate funnel conversion rates.
        
        Args:
            days: Number of days to analyze
        
        Returns:
            Dict with conversion rates between stages
        """
        cutoff = datetime.now() - timedelta(days=days)
        recent_events = [e for e in self.funnel_events if e.timestamp >= cutoff]
        
        # Count users at each stage
        stage_users = defaultdict(set)
        for event in recent_events:
            stage_users[event.stage].add(event.user_id)
        
        # Calculate conversion rates
        conversions = {}
        for i in range(len(FUNNEL_STAGES) - 1):
            current_stage = FUNNEL_STAGES[i]
            next_stage = FUNNEL_STAGES[i + 1]
            
            current_users = len(stage_users[current_stage])
            next_users = len(stage_users[next_stage])
            
            if current_users > 0:
                rate = (next_users / current_users) * 100
            else:
                rate = 0
            
            conversions[f"{current_stage}_to_{next_stage}"] = {
                'current_count': current_users,
                'next_count': next_users,
                'conversion_rate': rate
            }
        
        # Overall conversion (first to last stage)
        first_stage_users = len(stage_users[FUNNEL_STAGES[0]])
        last_stage_users = len(stage_users[FUNNEL_STAGES[-1]])
        
        if first_stage_users > 0:
            overall_rate = (last_stage_users / first_stage_users) * 100
        else:
            overall_rate = 0
        
        conversions['overall'] = {
            'total_users': first_stage_users,
            'converted_users': last_stage_users,
            'conversion_rate': overall_rate
        }
        
        return conversions
    
    # ========================================================================
    # REVENUE METRICS
    # ========================================================================
    
    def calculate_revenue_metrics(
        self,
        subscriptions: List[Dict],
        period_start: datetime = None,
        period_end: datetime = None
    ) -> RevenueMetrics:
        """
        Calculate revenue metrics for a period.
        
        Args:
            subscriptions: List of subscription dicts with:
                {user_id, status, plan_price, start_date, end_date}
            period_start: Start of period (default: 30 days ago)
            period_end: End of period (default: now)
        
        Returns:
            RevenueMetrics object
        """
        if not period_start:
            period_start = datetime.now() - timedelta(days=30)
        if not period_end:
            period_end = datetime.now()
        
        # Filter active subscriptions
        active_subs = [
            s for s in subscriptions
            if s.get('status') == 'active' and
            s.get('start_date', period_end) <= period_end
        ]
        
        # New customers in period
        new_customers = len([
            s for s in active_subs
            if period_start <= s.get('start_date', period_start) <= period_end
        ])
        
        # Churned customers
        churned_customers = len([
            s for s in subscriptions
            if s.get('status') == 'cancelled' and
            s.get('end_date') and
            period_start <= s.get('end_date') <= period_end
        ])
        
        # Active customers
        active_customers = len(active_subs)
        
        # MRR (Monthly Recurring Revenue)
        mrr = sum(s.get('plan_price', 0) for s in active_subs)
        
        # ARR (Annual Recurring Revenue)
        arr = mrr * 12
        
        # ARPU (Average Revenue Per User)
        arpu = mrr / active_customers if active_customers > 0 else 0
        
        # LTV (Lifetime Value) - simplified
        # LTV = ARPU / Churn Rate
        churn_rate = churned_customers / active_customers if active_customers > 0 else 0
        ltv = arpu / churn_rate if churn_rate > 0 else arpu * 12  # Default to 12 months
        
        metrics = RevenueMetrics(
            period_start=period_start,
            period_end=period_end,
            new_customers=new_customers,
            churned_customers=churned_customers,
            active_customers=active_customers,
            mrr=mrr,
            arr=arr,
            arpu=arpu,
            ltv=ltv,
            churn_rate=churn_rate
        )
        
        self.revenue_history.append(metrics)
        self._save_revenue_metrics()
        
        return metrics
    
    def get_latest_revenue_metrics(self) -> Optional[RevenueMetrics]:
        """Get most recent revenue metrics"""
        if not self.revenue_history:
            return None
        return self.revenue_history[-1]
    
    # ========================================================================
    # CHURN PREDICTION
    # ========================================================================
    
    def predict_churn(self, user_id: int, user_data: Dict) -> ChurnPrediction:
        """
        Predict churn risk for a user using simple ML model.
        
        Args:
            user_id: User ID
            user_data: Dict with user metrics:
                - days_since_last_login
                - searches_last_30d
                - deals_claimed_last_30d
                - support_tickets
                - engagement_score
                - payment_failures
        
        Returns:
            ChurnPrediction object
        """
        score = 0.0
        factors = []
        
        # Days since last login
        days_inactive = user_data.get('days_since_last_login', 0)
        if days_inactive > 14:
            score += 0.3
            factors.append(f"Inactivo por {days_inactive} días")
        elif days_inactive > 7:
            score += 0.15
            factors.append(f"Baja actividad ({days_inactive} días sin login)")
        
        # Search activity
        searches = user_data.get('searches_last_30d', 0)
        if searches < 5:
            score += 0.25
            factors.append("Muy pocas búsquedas (< 5/mes)")
        elif searches < 10:
            score += 0.1
            factors.append("Búsquedas por debajo de promedio")
        
        # Deals claimed
        deals = user_data.get('deals_claimed_last_30d', 0)
        if deals == 0:
            score += 0.2
            factors.append("No ha aprovechado chollos")
        
        # Support tickets
        tickets = user_data.get('support_tickets', 0)
        if tickets > 2:
            score += 0.15
            factors.append(f"Múltiples tickets de soporte ({tickets})")
        
        # Engagement score
        engagement = user_data.get('engagement_score', 50)
        if engagement < 30:
            score += 0.2
            factors.append("Score de engagement bajo")
        
        # Payment failures
        payment_failures = user_data.get('payment_failures', 0)
        if payment_failures > 0:
            score += 0.3
            factors.append(f"Fallos de pago ({payment_failures})")
        
        # Cap score at 1.0
        score = min(1.0, score)
        
        # Determine risk level
        if score >= CHURN_RISK_HIGH:
            risk_level = "high"
        elif score >= CHURN_RISK_MEDIUM:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        # Recommended actions based on factors
        actions = self._get_churn_prevention_actions(factors, risk_level)
        
        prediction = ChurnPrediction(
            user_id=user_id,
            churn_score=score,
            risk_level=risk_level,
            contributing_factors=factors,
            recommended_actions=actions,
            predicted_at=datetime.now()
        )
        
        self.churn_predictions[user_id] = prediction
        self._save_churn_predictions()
        
        return prediction
    
    def _get_churn_prevention_actions(self, factors: List[str], risk_level: str) -> List[str]:
        """Get recommended actions to prevent churn"""
        actions = []
        
        if risk_level == "high":
            actions.append("Contactar personalmente al usuario")
            actions.append("Ofrecer descuento especial (20-30%)")
            actions.append("Sesión 1-on-1 de value demonstration")
        
        if risk_level in ["high", "medium"]:
            actions.append("Enviar email con value metrics personalizados")
            actions.append("Ofrecer feature training personalizado")
        
        # Specific actions based on factors
        for factor in factors:
            if "Inactivo" in factor or "sin login" in factor:
                actions.append("Re-engagement campaign con nuevo contenido")
            if "pocas búsquedas" in factor:
                actions.append("Tutorial de búsqueda avanzada")
            if "No ha aprovechado" in factor:
                actions.append("Notificar chollos ultra-relevantes")
            if "soporte" in factor:
                actions.append("Priorizar resolución de issues")
            if "pago" in factor:
                actions.append("Actualizar método de pago urgente")
        
        return list(set(actions))  # Remove duplicates
    
    def get_high_risk_users(self) -> List[ChurnPrediction]:
        """Get all users at high risk of churning"""
        return [
            pred for pred in self.churn_predictions.values()
            if pred.risk_level == "high"
        ]
    
    # ========================================================================
    # COHORT ANALYSIS
    # ========================================================================
    
    def analyze_cohorts(self, subscriptions: List[Dict], months_back: int = 6) -> Dict:
        """
        Analyze retention by cohort (signup month).
        
        Args:
            subscriptions: List of subscription dicts
            months_back: Number of months to analyze
        
        Returns:
            Dict with cohort retention data
        """
        # Group by signup month
        cohorts = defaultdict(list)
        for sub in subscriptions:
            signup_date = sub.get('start_date')
            if not signup_date:
                continue
            
            cohort_month = signup_date.strftime('%Y-%m')
            cohorts[cohort_month].append(sub)
        
        # Calculate retention for each cohort
        retention_data = {}
        for cohort_month, cohort_subs in cohorts.items():
            cohort_size = len(cohort_subs)
            
            # Count still active
            active = len([s for s in cohort_subs if s.get('status') == 'active'])
            retention_rate = (active / cohort_size * 100) if cohort_size > 0 else 0
            
            retention_data[cohort_month] = {
                'cohort_size': cohort_size,
                'still_active': active,
                'retention_rate': retention_rate
            }
        
        return retention_data
    
    # ========================================================================
    # REPORTING
    # ========================================================================
    
    def generate_dashboard_data(self, subscriptions: List[Dict]) -> Dict:
        """Generate complete analytics dashboard data"""
        # Funnel metrics
        funnel = self.calculate_funnel_conversion(days=30)
        
        # Revenue metrics
        revenue = self.calculate_revenue_metrics(subscriptions)
        
        # Churn risk
        high_risk_count = len(self.get_high_risk_users())
        
        # Cohort retention
        cohorts = self.analyze_cohorts(subscriptions)
        avg_retention = statistics.mean(
            [c['retention_rate'] for c in cohorts.values()]
        ) if cohorts else 0
        
        return {
            'funnel': funnel,
            'revenue': revenue.to_dict(),
            'churn_risk': {
                'high_risk_users': high_risk_count,
                'total_predictions': len(self.churn_predictions)
            },
            'retention': {
                'avg_retention_rate': avg_retention,
                'cohorts_analyzed': len(cohorts)
            }
        }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def format_analytics_report(dashboard_data: Dict) -> str:
    """
    Format analytics dashboard for display.
    
    Args:
        dashboard_data: Dict from generate_dashboard_data()
    
    Returns:
        Formatted report string
    """
    funnel = dashboard_data['funnel']
    revenue = dashboard_data['revenue']
    churn = dashboard_data['churn_risk']
    retention = dashboard_data['retention']
    
    output = f"""📊 Premium Analytics Dashboard

💰 Revenue Metrics:
• MRR: €{revenue['mrr']:,.0f}
• ARR: €{revenue['arr']:,.0f}
• ARPU: €{revenue['arpu']:.2f}
• LTV: €{revenue['ltv']:.0f}
• Active customers: {revenue['active_customers']}
• New customers: {revenue['new_customers']}
• Churned: {revenue['churned_customers']}
• Churn rate: {revenue['churn_rate']*100:.1f}%

🎯 Conversion Funnel (30d):
• Overall conversion: {funnel['overall']['conversion_rate']:.1f}%
• Total users: {funnel['overall']['total_users']}
• Converted: {funnel['overall']['converted_users']}

⚠️ Churn Risk:
• High risk users: {churn['high_risk_users']}
• Total monitored: {churn['total_predictions']}

📈 Retention:
• Avg retention rate: {retention['avg_retention_rate']:.1f}%
• Cohorts analyzed: {retention['cohorts_analyzed']}
"""
    
    return output


# ============================================================================
# MAIN (TESTING)
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("📊 TESTING: Premium Analytics")
    print("="*60 + "\n")
    
    # Initialize analytics
    analytics = PremiumAnalytics()
    
    test_user = 33333
    
    print("1️⃣ Funnel Tracking")
    print("-" * 40)
    
    # Simulate funnel
    analytics.track_funnel_event(test_user, "user_registered")
    analytics.track_funnel_event(test_user, "paywall_viewed")
    analytics.track_funnel_event(test_user, "paywall_clicked")
    analytics.track_funnel_event(test_user, "trial_started")
    analytics.track_funnel_event(test_user, "feature_used")
    
    progress = analytics.get_user_funnel_progress(test_user)
    print(f"User funnel progress: {len(progress)}/{len(FUNNEL_STAGES)} stages")
    print(f"Stages: {', '.join(progress)}")
    
    print("\n2️⃣ Revenue Metrics")
    print("-" * 40)
    
    # Mock subscriptions
    mock_subs = [
        {'user_id': i, 'status': 'active', 'plan_price': 9.99, 'start_date': datetime.now() - timedelta(days=30)}
        for i in range(50)
    ]
    mock_subs.extend([
        {'user_id': i, 'status': 'cancelled', 'plan_price': 9.99,
         'start_date': datetime.now() - timedelta(days=60),
         'end_date': datetime.now() - timedelta(days=10)}
        for i in range(50, 55)
    ])
    
    revenue = analytics.calculate_revenue_metrics(mock_subs)
    print(f"MRR: €{revenue.mrr:,.0f}")
    print(f"ARR: €{revenue.arr:,.0f}")
    print(f"Active: {revenue.active_customers}")
    print(f"Churn rate: {revenue.churn_rate*100:.1f}%")
    
    print("\n3️⃣ Churn Prediction")
    print("-" * 40)
    
    user_data = {
        'days_since_last_login': 15,
        'searches_last_30d': 3,
        'deals_claimed_last_30d': 0,
        'support_tickets': 1,
        'engagement_score': 25,
        'payment_failures': 0
    }
    
    prediction = analytics.predict_churn(test_user, user_data)
    print(f"Churn score: {prediction.churn_score:.2f}")
    print(f"Risk level: {prediction.risk_level.upper()}")
    print(f"Factors: {len(prediction.contributing_factors)}")
    for factor in prediction.contributing_factors:
        print(f"  • {factor}")
    print(f"\nRecommended actions: {len(prediction.recommended_actions)}")
    for action in prediction.recommended_actions:
        print(f"  • {action}")
    
    print("\n4️⃣ Complete Dashboard")
    print("-" * 40)
    
    dashboard = analytics.generate_dashboard_data(mock_subs)
    print(format_analytics_report(dashboard))
    
    print("\n" + "="*60)
    print("✅ Testing Complete!")
    print("="*60 + "\n")
