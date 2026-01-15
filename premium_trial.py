#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Premium Trial System - IT6 Day 4/5
Sistema de trials premium con optimización de conversión

Author: @Juanka_Spain
Version: 13.2.0
Date: 2026-01-16
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict, field
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)


class TrialType(Enum):
    """Tipos de trial"""
    STANDARD = "standard"  # 7 días, sin tarjeta
    EXTENDED = "extended"  # 14 días, con tarjeta
    FEATURE_SPECIFIC = "feature_specific"  # Trial de feature específica


class TrialStatus(Enum):
    """Estados del trial"""
    ACTIVE = "active"
    CONVERTED = "converted"  # Se convirtió a pago
    EXPIRED = "expired"  # Expiró sin convertir
    CANCELLED = "cancelled"  # Usuario canceló


class ConversionTrigger(Enum):
    """Triggers para conversión"""
    VALUE_MOMENT = "value_moment"  # Encontró un gran chollo
    USAGE_THRESHOLD = "usage_threshold"  # Usó mucho el servicio
    EXPIRATION_NEAR = "expiration_near"  # Trial por expirar
    FEATURE_DEPENDENCY = "feature_dependency"  # Depende de una feature premium


@dataclass
class Trial:
    """Trial premium"""
    trial_id: str
    user_id: int
    tier: str
    trial_type: str
    status: str
    
    # Fechas
    started_at: str
    expires_at: str
    converted_at: Optional[str] = None
    
    # Onboarding
    onboarding_completed: bool = False
    value_moments: int = 0  # Momentos de valor experimentados
    
    # Usage durante trial
    searches_performed: int = 0
    deals_found: int = 0
    features_tried: List[str] = field(default_factory=list)
    
    # Conversion tracking
    conversion_prompts_shown: int = 0
    last_prompt_at: Optional[str] = None
    
    # Retention
    engagement_score: float = 0.0  # 0-100
    churn_risk: str = "low"  # low, medium, high


@dataclass
class TrialOnboarding:
    """Flujo de onboarding del trial"""
    trial_id: str
    user_id: int
    
    # Steps completados
    profile_setup: bool = False
    first_search: bool = False
    first_alert_created: bool = False
    first_deal_found: bool = False
    dashboard_viewed: bool = False
    
    # Progress
    completion_pct: float = 0.0
    
    # Time to value
    ttfv_seconds: Optional[float] = None  # Time To First Value
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ConversionAttempt:
    """Intento de conversión"""
    attempt_id: str
    trial_id: str
    user_id: int
    
    # Trigger
    trigger_type: str
    trigger_context: str
    
    # Offer
    discount_pct: float = 0.0
    special_offer: Optional[str] = None
    
    # Resultado
    shown_at: str = field(default_factory=lambda: datetime.now().isoformat())
    action_taken: Optional[str] = None  # converted, maybe_later, dismissed
    converted: bool = False


class PremiumTrialManager:
    """
    Gestor de trials premium.
    
    Features:
    - Activación de trial
    - Onboarding optimizado
    - Tracking de engagement
    - Conversion optimization
    - Retention tactics
    """
    
    # Configuración de trials
    TRIAL_CONFIGS = {
        TrialType.STANDARD.value: {
            "days": 7,
            "requires_card": False,
            "tier": "pro",
            "features": "all"
        },
        TrialType.EXTENDED.value: {
            "days": 14,
            "requires_card": True,
            "tier": "pro",
            "features": "all"
        },
        TrialType.FEATURE_SPECIFIC.value: {
            "days": 3,
            "requires_card": False,
            "tier": "basic",
            "features": "limited"
        },
    }
    
    # Descuentos por momento de conversión
    CONVERSION_DISCOUNTS = {
        "early_bird": 30,  # Primeros 2 días: 30% off
        "mid_trial": 20,  # Días 3-5: 20% off
        "last_chance": 40,  # Último día: 40% off
    }
    
    def __init__(self, data_dir: str = "."):
        self.data_dir = Path(data_dir)
        self.trials_file = self.data_dir / "premium_trials.json"
        self.onboarding_file = self.data_dir / "trial_onboarding.json"
        self.attempts_file = self.data_dir / "conversion_attempts.json"
        self.analytics_file = self.data_dir / "trial_analytics.json"
        
        self.trials: Dict[str, Trial] = {}
        self.onboarding: Dict[str, TrialOnboarding] = {}
        self.attempts: List[ConversionAttempt] = []
        self.analytics: Dict = self._init_analytics()
        
        self._load_data()
        logger.info("🎁 PremiumTrialManager initialized")
    
    def _init_analytics(self) -> Dict:
        """Inicializa analytics"""
        return {
            "total_trials": 0,
            "active_trials": 0,
            "converted_trials": 0,
            "expired_trials": 0,
            "conversion_rate": 0.0,
            "avg_ttfv": 0.0,
            "avg_engagement": 0.0,
            "conversion_by_trigger": {},
            "last_updated": datetime.now().isoformat()
        }
    
    def _load_data(self):
        """Carga datos"""
        if self.trials_file.exists():
            with open(self.trials_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.trials = {k: Trial(**v) for k, v in data.items()}
        
        if self.onboarding_file.exists():
            with open(self.onboarding_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.onboarding = {
                    k: TrialOnboarding(**v) for k, v in data.items()
                }
        
        if self.attempts_file.exists():
            with open(self.attempts_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.attempts = [ConversionAttempt(**a) for a in data]
        
        if self.analytics_file.exists():
            with open(self.analytics_file, 'r', encoding='utf-8') as f:
                self.analytics = json.load(f)
    
    def _save_data(self):
        """Guarda datos"""
        with open(self.trials_file, 'w', encoding='utf-8') as f:
            data = {k: asdict(v) for k, v in self.trials.items()}
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        with open(self.onboarding_file, 'w', encoding='utf-8') as f:
            data = {k: asdict(v) for k, v in self.onboarding.items()}
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        with open(self.attempts_file, 'w', encoding='utf-8') as f:
            data = [asdict(a) for a in self.attempts]
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        with open(self.analytics_file, 'w', encoding='utf-8') as f:
            json.dump(self.analytics, f, indent=2, ensure_ascii=False)
    
    def start_trial(
        self,
        user_id: int,
        trial_type: TrialType = TrialType.STANDARD
    ) -> Tuple[bool, str, Optional[Trial]]:
        """
        Inicia un trial premium.
        
        Returns:
            (success, message, trial)
        """
        import hashlib
        
        # Verificar si ya tiene trial activo
        existing = self._get_user_active_trial(user_id)
        if existing:
            return False, "❌ Ya tienes un trial activo", None
        
        # Crear trial
        trial_id = hashlib.md5(
            f"{user_id}{datetime.now()}".encode()
        ).hexdigest()[:12]
        
        config = self.TRIAL_CONFIGS[trial_type.value]
        
        trial = Trial(
            trial_id=trial_id,
            user_id=user_id,
            tier=config["tier"],
            trial_type=trial_type.value,
            status=TrialStatus.ACTIVE.value,
            started_at=datetime.now().isoformat(),
            expires_at=(
                datetime.now() + timedelta(days=config["days"])
            ).isoformat()
        )
        
        self.trials[trial_id] = trial
        
        # Crear onboarding
        onboarding = TrialOnboarding(
            trial_id=trial_id,
            user_id=user_id
        )
        self.onboarding[trial_id] = onboarding
        
        # Analytics
        self.analytics["total_trials"] += 1
        self.analytics["active_trials"] += 1
        
        self._save_data()
        
        msg = (
            f"🎉 ¡Trial {config['tier'].upper()} activado!\n"
            f"⏰ {config['days']} días de acceso completo\n"
            f"✅ Sin tarjeta requerida\n"
            f"\n🚀 Empecemos con tu onboarding..."
        )
        
        logger.info(f"🎁 Trial started for user {user_id}")
        return True, msg, trial
    
    def _get_user_active_trial(self, user_id: int) -> Optional[Trial]:
        """Obtiene el trial activo de un usuario"""
        for trial in self.trials.values():
            if (
                trial.user_id == user_id and
                trial.status == TrialStatus.ACTIVE.value
            ):
                return trial
        return None
    
    def complete_onboarding_step(
        self,
        trial_id: str,
        step: str
    ) -> bool:
        """
        Marca un paso del onboarding como completado.
        
        Steps: profile_setup, first_search, first_alert_created,
               first_deal_found, dashboard_viewed
        """
        if trial_id not in self.onboarding:
            return False
        
        onboarding = self.onboarding[trial_id]
        
        # Marcar step
        if hasattr(onboarding, step):
            setattr(onboarding, step, True)
        
        # Actualizar progreso
        total_steps = 5
        completed = sum([
            onboarding.profile_setup,
            onboarding.first_search,
            onboarding.first_alert_created,
            onboarding.first_deal_found,
            onboarding.dashboard_viewed
        ])
        
        onboarding.completion_pct = (completed / total_steps) * 100
        
        # Si es first_deal_found, calcular TTFV
        if step == "first_deal_found" and not onboarding.ttfv_seconds:
            started = datetime.fromisoformat(onboarding.started_at)
            ttfv = (datetime.now() - started).total_seconds()
            onboarding.ttfv_seconds = ttfv
            
            # Actualizar analytics
            if self.analytics["avg_ttfv"] == 0:
                self.analytics["avg_ttfv"] = ttfv
            else:
                # Promedio móvil
                self.analytics["avg_ttfv"] = (
                    self.analytics["avg_ttfv"] * 0.9 + ttfv * 0.1
                )
        
        # Marcar onboarding completado
        if onboarding.completion_pct == 100:
            if trial_id in self.trials:
                self.trials[trial_id].onboarding_completed = True
                self.trials[trial_id].value_moments += 1
        
        self._save_data()
        
        return True
    
    def track_trial_activity(
        self,
        trial_id: str,
        activity_type: str,
        value: int = 1
    ):
        """
        Registra actividad durante el trial.
        
        Types: search, deal_found, feature_tried
        """
        if trial_id not in self.trials:
            return
        
        trial = self.trials[trial_id]
        
        if activity_type == "search":
            trial.searches_performed += value
        elif activity_type == "deal_found":
            trial.deals_found += value
            trial.value_moments += 1
        elif activity_type == "feature_tried":
            # Evitar duplicados
            if value not in trial.features_tried:
                trial.features_tried.append(str(value))
        
        # Actualizar engagement score
        self._calculate_engagement(trial_id)
        
        self._save_data()
    
    def _calculate_engagement(self, trial_id: str):
        """
        Calcula engagement score (0-100).
        
        Basado en:
        - Searches performed
        - Deals found
        - Features tried
        - Onboarding progress
        - Value moments
        """
        trial = self.trials[trial_id]
        onboarding = self.onboarding.get(trial_id)
        
        score = 0.0
        
        # Searches (max 20 pts)
        score += min(20, trial.searches_performed * 2)
        
        # Deals (max 30 pts)
        score += min(30, trial.deals_found * 6)
        
        # Features tried (max 20 pts)
        score += min(20, len(trial.features_tried) * 5)
        
        # Onboarding (max 20 pts)
        if onboarding:
            score += onboarding.completion_pct * 0.2
        
        # Value moments (max 10 pts)
        score += min(10, trial.value_moments * 2)
        
        trial.engagement_score = min(100, score)
        
        # Determinar churn risk
        if trial.engagement_score >= 70:
            trial.churn_risk = "low"
        elif trial.engagement_score >= 40:
            trial.churn_risk = "medium"
        else:
            trial.churn_risk = "high"
    
    def should_show_conversion_prompt(
        self,
        trial_id: str
    ) -> Tuple[bool, Optional[ConversionTrigger]]:
        """
        Determina si mostrar prompt de conversión.
        
        Returns:
            (should_show, trigger_type)
        """
        if trial_id not in self.trials:
            return False, None
        
        trial = self.trials[trial_id]
        
        # No mostrar si ya convirtió
        if trial.status != TrialStatus.ACTIVE.value:
            return False, None
        
        # Verificar tiempo desde último prompt
        if trial.last_prompt_at:
            last_prompt = datetime.fromisoformat(trial.last_prompt_at)
            hours_since = (datetime.now() - last_prompt).total_seconds() / 3600
            
            # Mínimo 12 horas entre prompts
            if hours_since < 12:
                return False, None
        
        # VALUE_MOMENT: acaba de encontrar un gran deal
        if trial.value_moments >= 3:
            return True, ConversionTrigger.VALUE_MOMENT
        
        # USAGE_THRESHOLD: está usando mucho el servicio
        if trial.engagement_score >= 70:
            return True, ConversionTrigger.USAGE_THRESHOLD
        
        # EXPIRATION_NEAR: trial por expirar
        expires = datetime.fromisoformat(trial.expires_at)
        days_remaining = (expires - datetime.now()).days
        
        if days_remaining <= 1:
            return True, ConversionTrigger.EXPIRATION_NEAR
        
        # FEATURE_DEPENDENCY: usa mucho ciertas features
        if len(trial.features_tried) >= 5:
            return True, ConversionTrigger.FEATURE_DEPENDENCY
        
        return False, None
    
    def create_conversion_attempt(
        self,
        trial_id: str,
        trigger: ConversionTrigger,
        context: str = ""
    ) -> ConversionAttempt:
        """
        Crea un intento de conversión.
        """
        import hashlib
        
        trial = self.trials[trial_id]
        
        # Determinar descuento
        expires = datetime.fromisoformat(trial.expires_at)
        days_remaining = (expires - datetime.now()).days
        
        if days_remaining >= 5:
            discount = self.CONVERSION_DISCOUNTS["early_bird"]
        elif days_remaining >= 2:
            discount = self.CONVERSION_DISCOUNTS["mid_trial"]
        else:
            discount = self.CONVERSION_DISCOUNTS["last_chance"]
        
        # Crear attempt
        attempt_id = hashlib.md5(
            f"{trial_id}{datetime.now()}".encode()
        ).hexdigest()[:12]
        
        attempt = ConversionAttempt(
            attempt_id=attempt_id,
            trial_id=trial_id,
            user_id=trial.user_id,
            trigger_type=trigger.value,
            trigger_context=context,
            discount_pct=discount
        )
        
        self.attempts.append(attempt)
        
        # Actualizar trial
        trial.conversion_prompts_shown += 1
        trial.last_prompt_at = datetime.now().isoformat()
        
        self._save_data()
        
        logger.info(
            f"💸 Conversion attempt created for trial {trial_id} "
            f"(trigger: {trigger.value}, discount: {discount}%)"
        )
        
        return attempt
    
    def track_conversion_action(
        self,
        attempt_id: str,
        action: str
    ):
        """
        Registra acción en un intento de conversión.
        
        Actions: converted, maybe_later, dismissed
        """
        attempt = next(
            (a for a in self.attempts if a.attempt_id == attempt_id),
            None
        )
        
        if not attempt:
            return
        
        attempt.action_taken = action
        
        if action == "converted":
            attempt.converted = True
            
            # Actualizar trial
            trial = self.trials.get(attempt.trial_id)
            if trial:
                trial.status = TrialStatus.CONVERTED.value
                trial.converted_at = datetime.now().isoformat()
                
                # Analytics
                self.analytics["active_trials"] -= 1
                self.analytics["converted_trials"] += 1
                
                # Por trigger
                trigger = attempt.trigger_type
                if trigger not in self.analytics["conversion_by_trigger"]:
                    self.analytics["conversion_by_trigger"][trigger] = {
                        "attempts": 0,
                        "conversions": 0
                    }
                self.analytics["conversion_by_trigger"][trigger]["conversions"] += 1
        
        self._save_data()
        self._update_analytics()
    
    def expire_trial(self, trial_id: str):
        """
        Expira un trial.
        """
        if trial_id not in self.trials:
            return
        
        trial = self.trials[trial_id]
        
        if trial.status == TrialStatus.ACTIVE.value:
            trial.status = TrialStatus.EXPIRED.value
            
            self.analytics["active_trials"] -= 1
            self.analytics["expired_trials"] += 1
            
            self._save_data()
            self._update_analytics()
            
            logger.info(f"⏰ Trial {trial_id} expired")
    
    def check_expired_trials(self):
        """
        Verifica y expira trials vencidos.
        """
        now = datetime.now()
        
        for trial in self.trials.values():
            if trial.status != TrialStatus.ACTIVE.value:
                continue
            
            expires = datetime.fromisoformat(trial.expires_at)
            
            if now >= expires:
                self.expire_trial(trial.trial_id)
    
    def _update_analytics(self):
        """Actualiza analytics"""
        # Conversion rate
        total = self.analytics["total_trials"]
        converted = self.analytics["converted_trials"]
        
        if total > 0:
            self.analytics["conversion_rate"] = (converted / total) * 100
        
        # Avg engagement
        if self.trials:
            total_engagement = sum(t.engagement_score for t in self.trials.values())
            self.analytics["avg_engagement"] = total_engagement / len(self.trials)
        
        self.analytics["last_updated"] = datetime.now().isoformat()
    
    def get_trial(self, trial_id: str) -> Optional[Trial]:
        """Obtiene un trial"""
        return self.trials.get(trial_id)
    
    def get_user_trial(self, user_id: int) -> Optional[Trial]:
        """Obtiene el trial de un usuario (activo o más reciente)"""
        user_trials = [
            t for t in self.trials.values()
            if t.user_id == user_id
        ]
        
        if not user_trials:
            return None
        
        # Primero buscar activo
        active = next(
            (t for t in user_trials if t.status == TrialStatus.ACTIVE.value),
            None
        )
        
        if active:
            return active
        
        # Si no, el más reciente
        return max(user_trials, key=lambda t: t.started_at)
    
    def get_analytics(self) -> Dict:
        """Retorna analytics"""
        return self.analytics


if __name__ == "__main__":
    # Testing
    print("🚀 Testing PremiumTrialManager...\n")
    
    manager = PremiumTrialManager()
    
    # Test 1: Start trial
    print("1. Starting trial...")
    success, msg, trial = manager.start_trial(12345)
    print(f"   {msg}\n")
    
    if trial:
        # Test 2: Complete onboarding
        print("2. Completing onboarding steps...")
        manager.complete_onboarding_step(trial.trial_id, "profile_setup")
        manager.complete_onboarding_step(trial.trial_id, "first_search")
        print("   Steps completed\n")
        
        # Test 3: Track activity
        print("3. Tracking activity...")
        manager.track_trial_activity(trial.trial_id, "search", 5)
        manager.track_trial_activity(trial.trial_id, "deal_found", 2)
        print(f"   Engagement: {trial.engagement_score:.1f}\n")
        
        # Test 4: Check conversion prompt
        print("4. Checking conversion prompt...")
        should_show, trigger = manager.should_show_conversion_prompt(trial.trial_id)
        print(f"   Should show: {should_show}")
        if trigger:
            print(f"   Trigger: {trigger.value}\n")
        
        # Test 5: Create conversion attempt
        if should_show:
            print("5. Creating conversion attempt...")
            attempt = manager.create_conversion_attempt(
                trial.trial_id,
                trigger,
                "test context"
            )
            print(f"   Discount: {attempt.discount_pct}%\n")
    
    # Test 6: Analytics
    print("6. Analytics...")
    analytics = manager.get_analytics()
    print(f"   Total trials: {analytics['total_trials']}")
    print(f"   Conversion rate: {analytics['conversion_rate']:.1f}%")
    
    print("\n✅ Tests completados!")
