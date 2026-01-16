#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Premium Trial System for Frictionless Conversion
IT6 - DAY 2/5

Features:
- 7-day trial activation without payment method
- Automatic feature unlocking during trial
- Trial countdown and reminders
- Nurturing flow (Day 1, 3, 5, 7)
- Trial-to-paid conversion tracking
- Engagement scoring

Author: @Juanka_Spain
Version: 14.0.0-alpha.2
Date: 2026-01-16
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path


# ============================================================================
# ENUMS & CONSTANTS
# ============================================================================

class TrialStatus(Enum):
    """Trial subscription status"""
    ACTIVE = "active"
    EXPIRED = "expired"
    CONVERTED = "converted"
    CANCELLED = "cancelled"


class NurturingStage(Enum):
    """Trial nurturing stages"""
    DAY_1_WELCOME = "day1_welcome"
    DAY_3_VALUE = "day3_value"
    DAY_5_REMINDER = "day5_reminder"
    DAY_7_LAST_CHANCE = "day7_last_chance"


# Premium features unlocked during trial
PREMIUM_FEATURES = {
    "unlimited_searches": {
        "name": "Búsquedas Ilimitadas",
        "description": "Sin límite diario de búsquedas",
        "icon": "🔍"
    },
    "unlimited_watchlist": {
        "name": "Watchlist Sin Límites",
        "description": "Monitoriza todas las rutas que quieras",
        "icon": "⭐"
    },
    "priority_notifications": {
        "name": "Notificaciones Priority",
        "description": "Alertas instantáneas de chollos",
        "icon": "🔔"
    },
    "advanced_filters": {
        "name": "Filtros Avanzados",
        "description": "Personaliza tus búsquedas",
        "icon": "🎯"
    },
    "price_alerts": {
        "name": "Alertas de Precio",
        "description": "Notificaciones cuando baje el precio",
        "icon": "💰"
    },
    "export_data": {
        "name": "Exportar Datos",
        "description": "Descarga tu historial en CSV/PDF",
        "icon": "📄"
    },
    "no_ads": {
        "name": "Sin Publicidad",
        "description": "Experiencia premium sin anuncios",
        "icon": "🚫"
    },
    "priority_support": {
        "name": "Soporte 24/7",
        "description": "Asistencia prioritaria",
        "icon": "🎖️"
    }
}


# Trial nurturing messages
NURTURING_MESSAGES = {
    NurturingStage.DAY_1_WELCOME: {
        "title": "🎉 ¡Bienvenido a Premium!",
        "message": (
            "Tu trial de 7 días ha comenzado. Tienes acceso completo a todas las features premium.\n\n"
            "💡 Tip del día: Configura tu watchlist con rutas ilimitadas para no perderte ningún chollo."
        ),
        "cta": "Configurar Watchlist"
    },
    NurturingStage.DAY_3_VALUE: {
        "title": "📊 Tu Progreso Premium",
        "message": (
            "En 3 días con Premium has:\n"
            "• Encontrado {deals_found} chollos\n"
            "• Ahorrado €{savings}\n"
            "• Recibido {notifications} notificaciones priority\n\n"
            "¡Usuarios premium ahorran 65% más que usuarios free!"
        ),
        "cta": "Ver Mi Dashboard"
    },
    NurturingStage.DAY_5_REMINDER: {
        "title": "⏰ Quedan 2 Días de Trial",
        "message": (
            "Tu trial expira en 2 días. No pierdas acceso a:\n\n"
            "✅ Búsquedas ilimitadas\n"
            "✅ Notificaciones instantáneas\n"
            "✅ Watchlist sin límites\n\n"
            "🎁 Obtén 20% descuento si actualizas ahora."
        ),
        "cta": "Activar Premium con Descuento"
    },
    NurturingStage.DAY_7_LAST_CHANCE: {
        "title": "🔥 Último Día de Trial",
        "message": (
            "Tu trial expira HOY a las 23:59.\n\n"
            "En tu trial has ahorrado €{trial_savings}. Continúa ahorrando por solo €9.99/mes.\n\n"
            "🎉 OFERTA ESPECIAL: 25% OFF si actualizas en las próximas 24h."
        ),
        "cta": "No Perder Acceso Premium"
    }
}


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class PremiumTrial:
    """Premium trial subscription"""
    user_id: int
    start_date: datetime
    end_date: datetime
    status: str  # TrialStatus
    features_used: List[str]
    engagement_score: float  # 0-100
    converted: bool = False
    conversion_date: Optional[datetime] = None
    cancel_date: Optional[datetime] = None
    nurturing_sent: List[str] = None  # Stages already sent
    
    def __post_init__(self):
        if self.nurturing_sent is None:
            self.nurturing_sent = []
    
    @property
    def days_remaining(self) -> int:
        """Days remaining in trial"""
        if self.status != TrialStatus.ACTIVE.value:
            return 0
        delta = self.end_date - datetime.now()
        return max(0, delta.days)
    
    @property
    def hours_remaining(self) -> float:
        """Hours remaining in trial"""
        if self.status != TrialStatus.ACTIVE.value:
            return 0
        delta = self.end_date - datetime.now()
        return max(0, delta.total_seconds() / 3600)
    
    @property
    def is_active(self) -> bool:
        """Check if trial is currently active"""
        return self.status == TrialStatus.ACTIVE.value and datetime.now() < self.end_date
    
    @property
    def is_ending_soon(self) -> bool:
        """Check if trial is ending in <2 days"""
        return self.is_active and self.days_remaining <= 2
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['start_date'] = self.start_date.isoformat()
        data['end_date'] = self.end_date.isoformat()
        if self.conversion_date:
            data['conversion_date'] = self.conversion_date.isoformat()
        if self.cancel_date:
            data['cancel_date'] = self.cancel_date.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'PremiumTrial':
        data['start_date'] = datetime.fromisoformat(data['start_date'])
        data['end_date'] = datetime.fromisoformat(data['end_date'])
        if data.get('conversion_date'):
            data['conversion_date'] = datetime.fromisoformat(data['conversion_date'])
        if data.get('cancel_date'):
            data['cancel_date'] = datetime.fromisoformat(data['cancel_date'])
        return cls(**data)


@dataclass
class TrialEngagement:
    """Track trial user engagement"""
    user_id: int
    trial_start: datetime
    searches_made: int = 0
    deals_found: int = 0
    watchlist_added: int = 0
    notifications_received: int = 0
    groups_joined: int = 0
    referrals_made: int = 0
    session_count: int = 0
    total_session_duration: float = 0  # seconds
    features_explored: List[str] = None
    
    def __post_init__(self):
        if self.features_explored is None:
            self.features_explored = []
    
    @property
    def engagement_score(self) -> float:
        """
        Calculate engagement score (0-100).
        Higher score = more likely to convert.
        """
        score = 0
        
        # Searches (max 20 points)
        score += min(20, self.searches_made * 2)
        
        # Deals found (max 15 points)
        score += min(15, self.deals_found * 3)
        
        # Watchlist usage (max 15 points)
        score += min(15, self.watchlist_added * 5)
        
        # Notifications (max 10 points)
        score += min(10, self.notifications_received)
        
        # Social features (max 15 points)
        score += min(10, self.groups_joined * 5)
        score += min(5, self.referrals_made * 2.5)
        
        # Session engagement (max 15 points)
        score += min(10, self.session_count * 2)
        avg_session = self.total_session_duration / max(1, self.session_count)
        score += min(5, avg_session / 60)  # 5 points for 5+ min avg
        
        # Feature exploration (max 10 points)
        score += min(10, len(self.features_explored) * 2)
        
        return min(100, score)
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['trial_start'] = self.trial_start.isoformat()
        data['engagement_score'] = self.engagement_score
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'TrialEngagement':
        # Remove computed field
        data.pop('engagement_score', None)
        data['trial_start'] = datetime.fromisoformat(data['trial_start'])
        return cls(**data)


# ============================================================================
# TRIAL MANAGER
# ============================================================================

class TrialManager:
    """
    Manages premium trial activations and conversions.
    
    Features:
    - Frictionless 7-day trial (no payment method required)
    - Automatic feature unlocking
    - Trial countdown and reminders
    - Engagement tracking
    - Nurturing flow
    - Trial-to-paid conversion
    """
    
    def __init__(self, data_dir: str = ".", trial_days: int = 7):
        self.data_dir = Path(data_dir)
        self.trial_days = trial_days
        self.trials_file = self.data_dir / "trial_activations.json"
        self.engagement_file = self.data_dir / "trial_engagement.json"
        
        # Load data
        self.trials: Dict[int, PremiumTrial] = self._load_trials()
        self.engagement: Dict[int, TrialEngagement] = self._load_engagement()
        
        print(f"✅ TrialManager initialized ({trial_days}-day trials)")
    
    # ========================================================================
    # DATA PERSISTENCE
    # ========================================================================
    
    def _load_trials(self) -> Dict[int, PremiumTrial]:
        """Load trial subscriptions from file"""
        if not self.trials_file.exists():
            return {}
        
        try:
            with open(self.trials_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {
                    int(user_id): PremiumTrial.from_dict(trial)
                    for user_id, trial in data.items()
                }
        except Exception as e:
            print(f"⚠️ Error loading trials: {e}")
            return {}
    
    def _save_trials(self):
        """Save trial subscriptions to file"""
        try:
            data = {
                str(user_id): trial.to_dict()
                for user_id, trial in self.trials.items()
            }
            with open(self.trials_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Error saving trials: {e}")
    
    def _load_engagement(self) -> Dict[int, TrialEngagement]:
        """Load engagement tracking from file"""
        if not self.engagement_file.exists():
            return {}
        
        try:
            with open(self.engagement_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {
                    int(user_id): TrialEngagement.from_dict(eng)
                    for user_id, eng in data.items()
                }
        except Exception as e:
            print(f"⚠️ Error loading engagement: {e}")
            return {}
    
    def _save_engagement(self):
        """Save engagement tracking to file"""
        try:
            data = {
                str(user_id): eng.to_dict()
                for user_id, eng in self.engagement.items()
            }
            with open(self.engagement_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Error saving engagement: {e}")
    
    # ========================================================================
    # TRIAL ACTIVATION
    # ========================================================================
    
    def can_start_trial(self, user_id: int) -> Tuple[bool, str]:
        """
        Check if user can start a trial.
        
        Returns:
            (can_start, reason)
        """
        # Check if already has trial
        if user_id in self.trials:
            trial = self.trials[user_id]
            
            if trial.is_active:
                return False, "Ya tienes un trial activo"
            
            if trial.converted:
                return False, "Ya eres usuario premium"
            
            if trial.status == TrialStatus.EXPIRED.value:
                return False, "Ya usaste tu trial gratuito"
            
            if trial.status == TrialStatus.CANCELLED.value:
                # Allow re-activation after 30 days
                days_since = (datetime.now() - trial.cancel_date).days
                if days_since < 30:
                    return False, f"Puedes reactivar en {30 - days_since} días"
        
        return True, "Eligible for trial"
    
    def start_trial(self, user_id: int) -> PremiumTrial:
        """
        Start a premium trial for user.
        No payment method required.
        """
        can_start, reason = self.can_start_trial(user_id)
        if not can_start:
            raise ValueError(f"Cannot start trial: {reason}")
        
        # Create trial
        start_date = datetime.now()
        end_date = start_date + timedelta(days=self.trial_days)
        
        trial = PremiumTrial(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            status=TrialStatus.ACTIVE.value,
            features_used=[],
            engagement_score=0.0
        )
        
        self.trials[user_id] = trial
        
        # Initialize engagement tracking
        self.engagement[user_id] = TrialEngagement(
            user_id=user_id,
            trial_start=start_date
        )
        
        self._save_trials()
        self._save_engagement()
        
        print(f"✅ Trial started for user {user_id} (expires {end_date.date()})")
        return trial
    
    def get_trial(self, user_id: int) -> Optional[PremiumTrial]:
        """Get user's trial if exists"""
        return self.trials.get(user_id)
    
    def has_active_trial(self, user_id: int) -> bool:
        """Check if user has active trial"""
        trial = self.get_trial(user_id)
        return trial is not None and trial.is_active
    
    def is_trial_user(self, user_id: int) -> bool:
        """Check if user is in trial (includes converted)"""
        return user_id in self.trials
    
    # ========================================================================
    # ENGAGEMENT TRACKING
    # ========================================================================
    
    def track_feature_use(self, user_id: int, feature_name: str):
        """Track that user used a premium feature"""
        if user_id not in self.trials:
            return
        
        trial = self.trials[user_id]
        if feature_name not in trial.features_used:
            trial.features_used.append(feature_name)
            self._save_trials()
        
        if user_id in self.engagement:
            eng = self.engagement[user_id]
            if feature_name not in eng.features_explored:
                eng.features_explored.append(feature_name)
                self._save_engagement()
    
    def track_activity(self, user_id: int, activity_type: str, value: int = 1):
        """
        Track trial user activity.
        
        activity_type: searches, deals, watchlist, notifications, groups, referrals, session
        """
        if user_id not in self.engagement:
            return
        
        eng = self.engagement[user_id]
        
        if activity_type == "searches":
            eng.searches_made += value
        elif activity_type == "deals":
            eng.deals_found += value
        elif activity_type == "watchlist":
            eng.watchlist_added += value
        elif activity_type == "notifications":
            eng.notifications_received += value
        elif activity_type == "groups":
            eng.groups_joined += value
        elif activity_type == "referrals":
            eng.referrals_made += value
        elif activity_type == "session":
            eng.session_count += 1
        elif activity_type == "session_duration":
            eng.total_session_duration += value
        
        # Update engagement score in trial
        if user_id in self.trials:
            self.trials[user_id].engagement_score = eng.engagement_score
            self._save_trials()
        
        self._save_engagement()
    
    # ========================================================================
    # TRIAL CONVERSION
    # ========================================================================
    
    def convert_trial(self, user_id: int, plan_id: str) -> bool:
        """
        Convert trial to paid subscription.
        
        Returns:
            True if converted successfully
        """
        if user_id not in self.trials:
            return False
        
        trial = self.trials[user_id]
        
        if not trial.is_active:
            print(f"⚠️ Cannot convert inactive trial")
            return False
        
        # Mark as converted
        trial.status = TrialStatus.CONVERTED.value
        trial.converted = True
        trial.conversion_date = datetime.now()
        
        self._save_trials()
        
        print(f"✅ Trial converted to paid for user {user_id}")
        return True
    
    def cancel_trial(self, user_id: int) -> bool:
        """
        Cancel active trial.
        
        Returns:
            True if cancelled successfully
        """
        if user_id not in self.trials:
            return False
        
        trial = self.trials[user_id]
        
        if not trial.is_active:
            return False
        
        trial.status = TrialStatus.CANCELLED.value
        trial.cancel_date = datetime.now()
        
        self._save_trials()
        
        print(f"🚫 Trial cancelled for user {user_id}")
        return True
    
    def expire_trial(self, user_id: int):
        """Mark trial as expired (called automatically)"""
        if user_id not in self.trials:
            return
        
        trial = self.trials[user_id]
        trial.status = TrialStatus.EXPIRED.value
        self._save_trials()
    
    # ========================================================================
    # NURTURING FLOW
    # ========================================================================
    
    def get_nurturing_message(self, user_id: int) -> Optional[Dict]:
        """
        Get appropriate nurturing message based on trial day.
        
        Returns:
            Dict with title, message, cta or None
        """
        trial = self.get_trial(user_id)
        if not trial or not trial.is_active:
            return None
        
        days_in = (datetime.now() - trial.start_date).days
        
        # Determine stage
        stage = None
        if days_in == 0 and NurturingStage.DAY_1_WELCOME.value not in trial.nurturing_sent:
            stage = NurturingStage.DAY_1_WELCOME
        elif days_in == 3 and NurturingStage.DAY_3_VALUE.value not in trial.nurturing_sent:
            stage = NurturingStage.DAY_3_VALUE
        elif days_in == 5 and NurturingStage.DAY_5_REMINDER.value not in trial.nurturing_sent:
            stage = NurturingStage.DAY_5_REMINDER
        elif days_in >= 6 and NurturingStage.DAY_7_LAST_CHANCE.value not in trial.nurturing_sent:
            stage = NurturingStage.DAY_7_LAST_CHANCE
        
        if not stage:
            return None
        
        # Get base message
        message = NURTURING_MESSAGES[stage].copy()
        
        # Personalize with user data
        if user_id in self.engagement:
            eng = self.engagement[user_id]
            
            # Calculate savings (mock for now)
            trial_savings = eng.deals_found * 150  # Assume €150 avg per deal
            
            message['message'] = message['message'].format(
                deals_found=eng.deals_found,
                savings=trial_savings,
                notifications=eng.notifications_received,
                trial_savings=trial_savings
            )
        
        # Mark as sent
        trial.nurturing_sent.append(stage.value)
        self._save_trials()
        
        return message
    
    # ========================================================================
    # TRIAL MANAGEMENT
    # ========================================================================
    
    def check_expirations(self) -> List[int]:
        """
        Check for expired trials and mark them.
        
        Returns:
            List of user_ids with newly expired trials
        """
        expired = []
        now = datetime.now()
        
        for user_id, trial in self.trials.items():
            if trial.status == TrialStatus.ACTIVE.value and now >= trial.end_date:
                self.expire_trial(user_id)
                expired.append(user_id)
        
        return expired
    
    # ========================================================================
    # ANALYTICS
    # ========================================================================
    
    def get_trial_stats(self) -> Dict:
        """Get trial performance statistics"""
        total_trials = len(self.trials)
        active_trials = sum(1 for t in self.trials.values() if t.is_active)
        converted = sum(1 for t in self.trials.values() if t.converted)
        expired = sum(1 for t in self.trials.values() if t.status == TrialStatus.EXPIRED.value)
        cancelled = sum(1 for t in self.trials.values() if t.status == TrialStatus.CANCELLED.value)
        
        # Engagement scores
        if self.engagement:
            avg_engagement = sum(e.engagement_score for e in self.engagement.values()) / len(self.engagement)
        else:
            avg_engagement = 0
        
        # Conversion rate
        completed_trials = converted + expired + cancelled
        conv_rate = converted / completed_trials if completed_trials > 0 else 0
        
        return {
            'total_trials': total_trials,
            'active': active_trials,
            'converted': converted,
            'expired': expired,
            'cancelled': cancelled,
            'conversion_rate': conv_rate,
            'avg_engagement_score': avg_engagement
        }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def format_trial_status(trial: PremiumTrial) -> str:
    """
    Format trial status message for user.
    
    Args:
        trial: PremiumTrial object
    
    Returns:
        Formatted status message
    """
    if not trial.is_active:
        return "⚠️ Tu trial ha expirado. Actualiza a premium para continuar."
    
    days = trial.days_remaining
    hours = trial.hours_remaining
    
    if days > 1:
        time_str = f"{days} días"
    elif days == 1:
        time_str = "1 día"
    else:
        time_str = f"{int(hours)} horas"
    
    return f"""✨ Premium Trial Activo

⏰ Quedan: {time_str}
🎯 Engagement: {trial.engagement_score:.0f}/100
✅ Features usadas: {len(trial.features_used)}/{len(PREMIUM_FEATURES)}

💡 No pierdas acceso. Actualiza antes de que expire.
"""


# ============================================================================
# MAIN (TESTING)
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🎁 TESTING: Premium Trial System")
    print("="*60 + "\n")
    
    # Initialize manager
    manager = TrialManager()
    
    test_user = 98765
    
    print("1️⃣ Trial Activation")
    print("-" * 40)
    
    can_start, reason = manager.can_start_trial(test_user)
    print(f"Can start trial: {can_start} ({reason})")
    
    if can_start:
        trial = manager.start_trial(test_user)
        print(f"\n✅ Trial activated!")
        print(f"Start: {trial.start_date.date()}")
        print(f"End: {trial.end_date.date()}")
        print(f"Status: {trial.status}")
    
    print("\n2️⃣ Feature Usage Tracking")
    print("-" * 40)
    
    # Simulate feature usage
    manager.track_feature_use(test_user, "unlimited_searches")
    manager.track_feature_use(test_user, "priority_notifications")
    manager.track_activity(test_user, "searches", 5)
    manager.track_activity(test_user, "deals", 2)
    manager.track_activity(test_user, "watchlist", 3)
    
    trial = manager.get_trial(test_user)
    print(f"Features used: {trial.features_used}")
    print(f"Engagement score: {trial.engagement_score:.1f}/100")
    
    print("\n3️⃣ Nurturing Message")
    print("-" * 40)
    
    nurturing = manager.get_nurturing_message(test_user)
    if nurturing:
        print(f"\n{nurturing['title']}")
        print(f"{nurturing['message']}")
        print(f"\n[{nurturing['cta']}]")
    
    print("\n4️⃣ Trial Status")
    print("-" * 40)
    print(format_trial_status(trial))
    
    print("\n5️⃣ Trial Stats")
    print("-" * 40)
    stats = manager.get_trial_stats()
    print(f"Total trials: {stats['total_trials']}")
    print(f"Active: {stats['active']}")
    print(f"Converted: {stats['converted']}")
    print(f"Conversion rate: {stats['conversion_rate']*100:.1f}%")
    print(f"Avg engagement: {stats['avg_engagement_score']:.1f}/100")
    
    print("\n" + "="*60)
    print("✅ Testing Complete!")
    print("="*60 + "\n")
