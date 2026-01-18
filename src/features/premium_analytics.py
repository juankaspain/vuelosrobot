#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Premium Analytics & Conversion Funnel Tracking
IT6 - DAY 5/5

Features:
- Complete conversion funnel tracking
- Premium revenue metrics (MRR, ARR, ARPU, LTV)
- Retention cohort analysis
- Churn prediction and prevention
- A/B test result tracking

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
import statistics
from collections import defaultdict


# ============================================================================
# ENUMS & CONSTANTS
# ============================================================================

class FunnelStage(Enum):
    """Conversion funnel stages"""
    VISITOR = "visitor"                    # New user
    ACTIVATED = "activated"                # Completed onboarding
    ENGAGED = "engaged"                    # Used core features
    PAYWALL_VIEW = "paywall_view"          # Saw paywall
    PAYWALL_CLICK = "paywall_click"        # Clicked upgrade
    TRIAL_START = "trial_start"            # Started trial
    TRIAL_ENGAGED = "trial_engaged"        # Used premium features
    PAID = "paid"                          # Became paying customer


class ChurnRisk(Enum):
    """Churn risk levels"""
    LOW = "low"          # <20% chance
    MEDIUM = "medium"    # 20-50% chance
    HIGH = "high"        # 50-80% chance
    CRITICAL = "critical" # >80% chance


# Churn signals (weighted)
CHURN_SIGNALS = {
    'days_since_last_login': {
        'weight': 0.25,
        'thresholds': {7: 0.2, 14: 0.5, 30: 0.8, 60: 1.0}
    },
    'searches_last_7d': {
        'weight': 0.20,
        'thresholds': {10: 0.0, 5: 0.3, 2: 0.6, 0: 1.0}
    },
    'deals_found_last_30d': {
        'weight': 0.15,
        'thresholds': {5: 0.0, 3: 0.3, 1: 0.6, 0: 0.9}
    },
    'notification_open_rate': {
        'weight': 0.15,
        'thresholds': {0.7: 0.0, 0.5: 0.3, 0.3: 0.6, 0.1: 1.0}
    },
    'support_tickets': {
        'weight': 0.10,
        'thresholds': {0: 0.0, 1: 0.3, 2: 0.6, 3: 0.9}
    },
    'feature_usage_drop': {
        'weight': 0.10,
        'thresholds': {0.0: 0.0, 0.3: 0.3, 0.5: 0.6, 0.8: 1.0}
    },
    'negative_feedback': {
        'weight': 0.05,
        'thresholds': {False: 0.0, True: 0.8}
    }
}


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class FunnelMetrics:
    """Conversion funnel metrics"""
    stage: str  # FunnelStage value
    users: int
    conversion_to_next: float  # %
    avg_time_to_next_stage: float  # hours
    dropoff_rate: float  # %
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class RevenueMetrics:
    """Revenue metrics"""
    mrr: float  # Monthly Recurring Revenue
    arr: float  # Annual Recurring Revenue
    arpu: float  # Average Revenue Per User
    ltv: float  # Lifetime Value
    cac: float  # Customer Acquisition Cost
    ltv_cac_ratio: float
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class CohortData:
    """Retention cohort data"""
    cohort_month: str  # YYYY-MM
    cohort_size: int
    retention_rates: Dict[int, float]  # month -> retention %
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ChurnPrediction:
    """Churn risk prediction"""
    user_id: int
    risk_level: str  # ChurnRisk value
    risk_score: float  # 0-1
    signals: Dict[str, float]  # signal -> contribution
    recommendation: str
    
    def to_dict(self) -> Dict:
        return asdict(self)


# ============================================================================
# CONVERSION FUNNEL TRACKER
# ============================================================================

class ConversionFunnel:
    """
    Tracks users through conversion funnel.
    
    Funnel stages:
    1. Visitor (new user)
    2. Activated (completed onboarding)
    3. Engaged (used core features)
    4. Paywall View (saw upgrade prompt)
    5. Paywall Click (clicked upgrade)
    6. Trial Start (started premium trial)
    7. Trial Engaged (used premium features)
    8. Paid (converted to paying customer)
    """
    
    def __init__(self, data_dir: str = "."):
        self.data_dir = Path(data_dir)
        self.funnel_file = self.data_dir / "conversion_funnel.json"
        
        # Load funnel data: {user_id: {stage: timestamp}}
        self.funnel_data: Dict[int, Dict[str, datetime]] = self._load_funnel()
        
        print("✅ ConversionFunnel initialized")
    
    # ========================================================================
    # DATA PERSISTENCE
    # ========================================================================
    
    def _load_funnel(self) -> Dict[int, Dict[str, datetime]]:
        """Load funnel data from file"""
        if not self.funnel_file.exists():
            return {}
        
        try:
            with open(self.funnel_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {
                    int(user_id): {
                        stage: datetime.fromisoformat(timestamp)
                        for stage, timestamp in stages.items()
                    }
                    for user_id, stages in data.items()
                }
        except Exception as e:
            print(f"⚠️ Error loading funnel: {e}")
            return {}
    
    def _save_funnel(self):
        """Save funnel data to file"""
        try:
            data = {
                str(user_id): {
                    stage: timestamp.isoformat()
                    for stage, timestamp in stages.items()
                }
                for user_id, stages in self.funnel_data.items()
            }
            with open(self.funnel_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Error saving funnel: {e}")
    
    # ========================================================================
    # FUNNEL TRACKING
    # ========================================================================
    
    def track_stage(self, user_id: int, stage: FunnelStage):
        """Track user reaching a funnel stage"""
        if user_id not in self.funnel_data:
            self.funnel_data[user_id] = {}
        
        # Only track first time reaching stage
        if stage.value not in self.funnel_data[user_id]:
            self.funnel_data[user_id][stage.value] = datetime.now()
            self._save_funnel()
    
    def get_user_stage(self, user_id: int) -> Optional[FunnelStage]:
        """Get current funnel stage for user"""
        if user_id not in self.funnel_data:
            return None
        
        stages = self.funnel_data[user_id]
        
        # Return furthest stage reached
        for stage in reversed(list(FunnelStage)):
            if stage.value in stages:
                return stage
        
        return None
    
    # ========================================================================
    # FUNNEL METRICS
    # ========================================================================
    
    def calculate_funnel_metrics(self) -> List[FunnelMetrics]:
        """
        Calculate metrics for each funnel stage.
        
        Returns:
            List of FunnelMetrics for each stage
        """
        metrics = []
        stages = list(FunnelStage)
        
        for i, stage in enumerate(stages):
            # Count users at this stage
            users_at_stage = sum(
                1 for user_stages in self.funnel_data.values()
                if stage.value in user_stages
            )
            
            if users_at_stage == 0:
                continue
            
            # Calculate conversion to next stage
            if i < len(stages) - 1:
                next_stage = stages[i + 1]
                users_at_next = sum(
                    1 for user_stages in self.funnel_data.values()
                    if next_stage.value in user_stages
                )
                conversion_rate = (users_at_next / users_at_stage) * 100
                dropoff_rate = 100 - conversion_rate
                
                # Calculate avg time to next stage
                times = []
                for user_stages in self.funnel_data.values():
                    if stage.value in user_stages and next_stage.value in user_stages:
                        delta = user_stages[next_stage.value] - user_stages[stage.value]
                        times.append(delta.total_seconds() / 3600)  # hours
                
                avg_time = statistics.mean(times) if times else 0
            else:
                conversion_rate = 100  # Last stage
                dropoff_rate = 0
                avg_time = 0
            
            metrics.append(FunnelMetrics(
                stage=stage.value,
                users=users_at_stage,
                conversion_to_next=conversion_rate,
                avg_time_to_next_stage=avg_time,
                dropoff_rate=dropoff_rate
            ))
        
        return metrics


# ============================================================================
# PREMIUM ANALYTICS
# ============================================================================

class PremiumAnalytics:
    """
    Analytics for premium subscriptions.
    
    Tracks:
    - Revenue metrics (MRR, ARR, ARPU, LTV)
    - Retention cohorts
    - Churn prediction
    - Performance dashboards
    """
    
    def __init__(self, data_dir: str = "."):
        self.data_dir = Path(data_dir)
        self.subscriptions_file = self.data_dir / "premium_subscriptions.json"
        self.cohorts_file = self.data_dir / "retention_cohorts.json"
        
        # Load data
        self.subscriptions = self._load_subscriptions()
        self.cohorts = self._load_cohorts()
        
        print("✅ PremiumAnalytics initialized")
    
    # ========================================================================
    # DATA PERSISTENCE
    # ========================================================================
    
    def _load_subscriptions(self) -> List[Dict]:
        """Load subscription data"""
        if not self.subscriptions_file.exists():
            return []
        
        try:
            with open(self.subscriptions_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Error loading subscriptions: {e}")
            return []
    
    def _load_cohorts(self) -> List[CohortData]:
        """Load cohort data"""
        if not self.cohorts_file.exists():
            return []
        
        try:
            with open(self.cohorts_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [CohortData(**c) for c in data]
        except Exception as e:
            print(f"⚠️ Error loading cohorts: {e}")
            return []
    
    def _save_cohorts(self):
        """Save cohort data"""
        try:
            data = [c.to_dict() for c in self.cohorts]
            with open(self.cohorts_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Error saving cohorts: {e}")
    
    # ========================================================================
    # REVENUE METRICS
    # ========================================================================
    
    def calculate_revenue_metrics(self, cac: float = 10.0) -> RevenueMetrics:
        """
        Calculate revenue metrics.
        
        Args:
            cac: Customer Acquisition Cost (default €10)
        
        Returns:
            RevenueMetrics
        """
        if not self.subscriptions:
            return RevenueMetrics(
                mrr=0, arr=0, arpu=0, ltv=0,
                cac=cac, ltv_cac_ratio=0
            )
        
        # Active subscriptions
        active_subs = [
            s for s in self.subscriptions
            if s.get('status') == 'active'
        ]
        
        if not active_subs:
            return RevenueMetrics(
                mrr=0, arr=0, arpu=0, ltv=0,
                cac=cac, ltv_cac_ratio=0
            )
        
        # MRR: Sum of all monthly recurring revenue
        mrr = 0
        for sub in active_subs:
            if sub.get('billing_period') == 'monthly':
                mrr += sub.get('price', 0)
            elif sub.get('billing_period') == 'annual':
                mrr += sub.get('price', 0) / 12
        
        # ARR: MRR * 12
        arr = mrr * 12
        
        # ARPU: Average Revenue Per User
        arpu = mrr / len(active_subs) if active_subs else 0
        
        # LTV: Simplified calculation (ARPU * avg lifetime in months)
        # Assume avg lifetime = 24 months (to be refined with real data)
        avg_lifetime_months = 24
        ltv = arpu * avg_lifetime_months
        
        # LTV:CAC ratio
        ltv_cac_ratio = ltv / cac if cac > 0 else 0
        
        return RevenueMetrics(
            mrr=mrr,
            arr=arr,
            arpu=arpu,
            ltv=ltv,
            cac=cac,
            ltv_cac_ratio=ltv_cac_ratio
        )
    
    # ========================================================================
    # RETENTION COHORTS
    # ========================================================================
    
    def calculate_cohort_retention(self) -> List[CohortData]:
        """
        Calculate retention cohorts.
        
        Groups users by signup month and tracks retention.
        
        Returns:
            List of CohortData
        """
        # Group subscriptions by cohort (signup month)
        cohorts = defaultdict(list)
        
        for sub in self.subscriptions:
            if 'start_date' not in sub:
                continue
            
            start_date = datetime.fromisoformat(sub['start_date'])
            cohort_key = start_date.strftime('%Y-%m')
            cohorts[cohort_key].append(sub)
        
        # Calculate retention for each cohort
        cohort_data = []
        
        for cohort_month, subs in sorted(cohorts.items()):
            cohort_size = len(subs)
            retention_rates = {}
            
            # Calculate retention for each month
            for month_offset in range(13):  # 0-12 months
                active_count = 0
                
                for sub in subs:
                    start_date = datetime.fromisoformat(sub['start_date'])
                    check_date = start_date + timedelta(days=30 * month_offset)
                    
                    # Check if still active at check_date
                    if sub.get('status') == 'active':
                        active_count += 1
                    elif 'cancel_date' in sub:
                        cancel_date = datetime.fromisoformat(sub['cancel_date'])
                        if cancel_date > check_date:
                            active_count += 1
                
                retention_rate = (active_count / cohort_size) * 100 if cohort_size > 0 else 0
                retention_rates[month_offset] = retention_rate
            
            cohort_data.append(CohortData(
                cohort_month=cohort_month,
                cohort_size=cohort_size,
                retention_rates=retention_rates
            ))
        
        return cohort_data
    
    # ========================================================================
    # CHURN PREDICTION
    # ========================================================================
    
    def predict_churn(self, user_id: int, user_profile: Dict) -> ChurnPrediction:
        """
        Predict churn risk for user.
        
        Args:
            user_id: User ID
            user_profile: Dict with user activity data
        
        Returns:
            ChurnPrediction with risk level and recommendations
        """
        risk_score = 0.0
        signal_contributions = {}
        
        # Calculate weighted risk from each signal
        for signal, config in CHURN_SIGNALS.items():
            value = user_profile.get(signal, 0)
            weight = config['weight']
            thresholds = config['thresholds']
            
            # Find contribution from thresholds
            contribution = 0.0
            for threshold, score in sorted(thresholds.items(), reverse=True):
                if isinstance(threshold, bool):
                    if value == threshold:
                        contribution = score
                        break
                elif value >= threshold:
                    contribution = score
                    break
            
            weighted_contribution = contribution * weight
            risk_score += weighted_contribution
            signal_contributions[signal] = weighted_contribution
        
        # Determine risk level
        if risk_score < 0.2:
            risk_level = ChurnRisk.LOW
            recommendation = "Usuario comprometido. Continuar con engagement normal."
        elif risk_score < 0.5:
            risk_level = ChurnRisk.MEDIUM
            recommendation = "Enviar email de re-engagement con value reminder."
        elif risk_score < 0.8:
            risk_level = ChurnRisk.HIGH
            recommendation = "Contacto directo + oferta especial (20% descuento)."
        else:
            risk_level = ChurnRisk.CRITICAL
            recommendation = "Acción inmediata: llamada + oferta win-back agresiva."
        
        return ChurnPrediction(
            user_id=user_id,
            risk_level=risk_level.value,
            risk_score=risk_score,
            signals=signal_contributions,
            recommendation=recommendation
        )
    
    # ========================================================================
    # ANALYTICS DASHBOARD
    # ========================================================================
    
    def get_dashboard_metrics(self) -> Dict:
        """Get complete analytics dashboard metrics"""
        revenue = self.calculate_revenue_metrics()
        cohorts = self.calculate_cohort_retention()
        
        # Calculate aggregate metrics
        total_users = len(self.subscriptions)
        active_users = sum(1 for s in self.subscriptions if s.get('status') == 'active')
        churned_users = sum(1 for s in self.subscriptions if s.get('status') == 'cancelled')
        
        churn_rate = (churned_users / total_users * 100) if total_users > 0 else 0
        
        # Latest cohort retention
        latest_cohort = cohorts[-1] if cohorts else None
        month_1_retention = latest_cohort.retention_rates.get(1, 0) if latest_cohort else 0
        
        return {
            'revenue': revenue.to_dict(),
            'users': {
                'total': total_users,
                'active': active_users,
                'churned': churned_users,
                'churn_rate': churn_rate
            },
            'retention': {
                'month_1': month_1_retention,
                'cohorts_tracked': len(cohorts)
            }
        }


# ============================================================================
# FORMATTING HELPERS
# ============================================================================

def format_funnel_report(metrics: List[FunnelMetrics]) -> str:
    """
    Format conversion funnel report.
    
    Args:
        metrics: List of FunnelMetrics
    
    Returns:
        Formatted report string
    """
    report = "📡 Conversion Funnel\n\n"
    
    for i, metric in enumerate(metrics):
        stage_emoji = ["👥", "✅", "🔥", "👀", "👆", "✨", "🎯", "💰"][i]
        
        report += f"{stage_emoji} {metric.stage.upper()}\n"
        report += f"   Users: {metric.users:,}\n"
        
        if metric.conversion_to_next < 100:
            report += f"   → Next: {metric.conversion_to_next:.1f}%\n"
            report += f"   Dropoff: {metric.dropoff_rate:.1f}%\n"
            if metric.avg_time_to_next_stage > 0:
                report += f"   Avg time: {metric.avg_time_to_next_stage:.1f}h\n"
        
        report += "\n"
    
    return report


def format_revenue_report(metrics: RevenueMetrics) -> str:
    """
    Format revenue metrics report.
    
    Args:
        metrics: RevenueMetrics
    
    Returns:
        Formatted report string
    """
    return f"""💰 Revenue Metrics

📊 MRR: €{metrics.mrr:,.2f}
📈 ARR: €{metrics.arr:,.2f}
👥 ARPU: €{metrics.arpu:.2f}
✨ LTV: €{metrics.ltv:.2f}
🎯 LTV:CAC: {metrics.ltv_cac_ratio:.1f}x

{'EXCELENTE' if metrics.ltv_cac_ratio >= 3 else 'MEJORAR'} (target: 3x+)
"""


# ============================================================================
# MAIN (TESTING)
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("📊 TESTING: Premium Analytics")
    print("="*60 + "\n")
    
    # Initialize systems
    funnel = ConversionFunnel()
    analytics = PremiumAnalytics()
    
    # Test funnel tracking
    print("1️⃣ Funnel Tracking")
    print("-" * 40)
    
    test_user = 55555
    funnel.track_stage(test_user, FunnelStage.VISITOR)
    funnel.track_stage(test_user, FunnelStage.ACTIVATED)
    funnel.track_stage(test_user, FunnelStage.ENGAGED)
    funnel.track_stage(test_user, FunnelStage.PAYWALL_VIEW)
    
    current_stage = funnel.get_user_stage(test_user)
    print(f"User stage: {current_stage.value if current_stage else 'None'}")
    
    # Test churn prediction
    print("\n2️⃣ Churn Prediction")
    print("-" * 40)
    
    at_risk_user = {
        'days_since_last_login': 20,
        'searches_last_7d': 1,
        'deals_found_last_30d': 0,
        'notification_open_rate': 0.2,
        'support_tickets': 2,
        'feature_usage_drop': 0.6,
        'negative_feedback': True
    }
    
    prediction = analytics.predict_churn(12345, at_risk_user)
    print(f"Risk level: {prediction.risk_level}")
    print(f"Risk score: {prediction.risk_score:.2f}")
    print(f"Recommendation: {prediction.recommendation}")
    
    print("\n" + "="*60)
    print("✅ Testing Complete!")
    print("="*60 + "\n")
