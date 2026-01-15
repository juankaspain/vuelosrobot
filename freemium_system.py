#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Freemium System - IT6 Day 1/5
Sistema de monetización freemium con feature gating y smart paywalls

Author: @Juanka_Spain
Version: 13.2.0
Date: 2026-01-16
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, asdict, field
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)


class SubscriptionTier(Enum):
    """Niveles de suscripción"""
    FREE = "free"
    BASIC = "basic"  # €4.99/mes
    PRO = "pro"      # €9.99/mes
    PREMIUM = "premium"  # €19.99/mes


class Feature(Enum):
    """Features del sistema"""
    # Búsquedas
    UNLIMITED_SEARCHES = "unlimited_searches"
    FLEXIBLE_DATES = "flexible_dates"  # ±3 días
    MULTI_CITY = "multi_city"
    
    # Alertas
    PRICE_ALERTS = "price_alerts"
    CUSTOM_ALERTS = "custom_alerts"
    INSTANT_NOTIFICATIONS = "instant_notifications"
    
    # Watchlist
    EXTENDED_WATCHLIST = "extended_watchlist"
    AUTO_BOOKING_ASSIST = "auto_booking_assist"
    
    # Analytics
    PRICE_TRENDS = "price_trends"
    HISTORICAL_DATA = "historical_data"
    FORECAST_PREDICTIONS = "forecast_predictions"
    
    # Social
    PRIORITY_SUPPORT = "priority_support"
    AD_FREE = "ad_free"
    CUSTOM_BADGE = "custom_badge"
    EARLY_ACCESS = "early_access"


@dataclass
class TierLimits:
    """Límites por tier"""
    tier: str
    
    # Búsquedas
    daily_searches: int
    watchlist_slots: int
    custom_alerts: int
    
    # Features booleanas
    features: Set[str] = field(default_factory=set)
    
    # Precio
    price_monthly: float = 0.0
    price_yearly: float = 0.0  # Con descuento


@dataclass
class Subscription:
    """Suscripción de usuario"""
    user_id: int
    tier: str
    status: str  # active, trial, expired, cancelled
    
    # Fechas
    started_at: str
    expires_at: Optional[str] = None
    trial_ends_at: Optional[str] = None
    
    # Billing
    billing_cycle: str = "monthly"  # monthly, yearly
    auto_renew: bool = True
    
    # Trial
    trial_used: bool = False
    trial_days: int = 7
    
    # Historial
    upgrades_count: int = 0
    downgrades_count: int = 0
    lifetime_value: float = 0.0


@dataclass
class UsageStats:
    """Estadísticas de uso del usuario"""
    user_id: int
    
    # Daily usage
    searches_today: int = 0
    alerts_triggered_today: int = 0
    
    # Limits
    searches_limit: int = 3
    watchlist_limit: int = 5
    alerts_limit: int = 2
    
    # Resets
    last_reset: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # Engagement
    days_since_signup: int = 0
    total_sessions: int = 0
    avg_session_time: float = 0.0


@dataclass
class PaywallEvent:
    """Evento de paywall mostrado"""
    event_id: str
    user_id: int
    feature: str
    trigger_context: str  # limit_reached, feature_locked, upgrade_prompt
    shown_at: str
    
    # Resultado
    action_taken: Optional[str] = None  # upgraded, dismissed, learn_more
    converted: bool = False
    
    # A/B testing
    variant: str = "default"


class FreemiumManager:
    """
    Gestor del sistema freemium.
    
    Responsabilidades:
    - Feature gating
    - Usage tracking
    - Smart paywalls
    - Upgrade prompts
    - Trial management
    """
    
    # Configuración de tiers
    TIER_CONFIG = {
        SubscriptionTier.FREE.value: TierLimits(
            tier="free",
            daily_searches=3,
            watchlist_slots=5,
            custom_alerts=2,
            features={
                Feature.PRICE_ALERTS.value,
            },
            price_monthly=0.0,
            price_yearly=0.0
        ),
        SubscriptionTier.BASIC.value: TierLimits(
            tier="basic",
            daily_searches=10,
            watchlist_slots=15,
            custom_alerts=5,
            features={
                Feature.PRICE_ALERTS.value,
                Feature.FLEXIBLE_DATES.value,
                Feature.CUSTOM_ALERTS.value,
                Feature.EXTENDED_WATCHLIST.value,
                Feature.PRICE_TRENDS.value,
                Feature.AD_FREE.value,
            },
            price_monthly=4.99,
            price_yearly=49.99  # 2 meses gratis
        ),
        SubscriptionTier.PRO.value: TierLimits(
            tier="pro",
            daily_searches=50,
            watchlist_slots=30,
            custom_alerts=15,
            features={
                Feature.PRICE_ALERTS.value,
                Feature.FLEXIBLE_DATES.value,
                Feature.CUSTOM_ALERTS.value,
                Feature.EXTENDED_WATCHLIST.value,
                Feature.PRICE_TRENDS.value,
                Feature.AD_FREE.value,
                Feature.UNLIMITED_SEARCHES.value,
                Feature.INSTANT_NOTIFICATIONS.value,
                Feature.HISTORICAL_DATA.value,
                Feature.AUTO_BOOKING_ASSIST.value,
                Feature.CUSTOM_BADGE.value,
            },
            price_monthly=9.99,
            price_yearly=99.99  # 2 meses gratis
        ),
        SubscriptionTier.PREMIUM.value: TierLimits(
            tier="premium",
            daily_searches=999,  # Ilimitado
            watchlist_slots=50,
            custom_alerts=999,  # Ilimitado
            features=set(f.value for f in Feature),  # Todas las features
            price_monthly=19.99,
            price_yearly=199.99  # 2 meses gratis
        ),
    }
    
    def __init__(self, data_dir: str = "."):
        self.data_dir = Path(data_dir)
        self.subscriptions_file = self.data_dir / "subscriptions.json"
        self.usage_file = self.data_dir / "usage_stats.json"
        self.paywalls_file = self.data_dir / "paywall_events.json"
        self.analytics_file = self.data_dir / "freemium_analytics.json"
        
        self.subscriptions: Dict[int, Subscription] = {}
        self.usage_stats: Dict[int, UsageStats] = {}
        self.paywall_events: List[PaywallEvent] = []
        self.analytics: Dict = self._init_analytics()
        
        self._load_data()
        logger.info("💰 FreemiumManager initialized")
    
    def _init_analytics(self) -> Dict:
        """Inicializa analytics"""
        return {
            "total_users": 0,
            "free_users": 0,
            "paid_users": 0,
            "trial_users": 0,
            "conversion_rate": 0.0,
            "mrr": 0.0,  # Monthly Recurring Revenue
            "arpu": 0.0,  # Average Revenue Per User
            "ltv": 0.0,  # Lifetime Value
            "churn_rate": 0.0,
            "upgrade_funnel": {
                "paywalls_shown": 0,
                "learn_more_clicks": 0,
                "upgrades": 0,
                "conversion_rate": 0.0
            },
            "tier_distribution": {},
            "last_updated": datetime.now().isoformat()
        }
    
    def _load_data(self):
        """Carga datos"""
        # Subscriptions
        if self.subscriptions_file.exists():
            with open(self.subscriptions_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.subscriptions = {
                    int(k): Subscription(**v) for k, v in data.items()
                }
        
        # Usage stats
        if self.usage_file.exists():
            with open(self.usage_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.usage_stats = {
                    int(k): UsageStats(**v) for k, v in data.items()
                }
        
        # Paywall events
        if self.paywalls_file.exists():
            with open(self.paywalls_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.paywall_events = [PaywallEvent(**e) for e in data]
        
        # Analytics
        if self.analytics_file.exists():
            with open(self.analytics_file, 'r', encoding='utf-8') as f:
                self.analytics = json.load(f)
    
    def _save_data(self):
        """Guarda datos"""
        # Subscriptions
        with open(self.subscriptions_file, 'w', encoding='utf-8') as f:
            data = {str(k): asdict(v) for k, v in self.subscriptions.items()}
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Usage stats
        with open(self.usage_file, 'w', encoding='utf-8') as f:
            data = {str(k): asdict(v) for k, v in self.usage_stats.items()}
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Paywall events
        with open(self.paywalls_file, 'w', encoding='utf-8') as f:
            data = [asdict(e) for e in self.paywall_events]
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Analytics
        with open(self.analytics_file, 'w', encoding='utf-8') as f:
            json.dump(self.analytics, f, indent=2, ensure_ascii=False)
    
    def initialize_user(self, user_id: int) -> Subscription:
        """
        Inicializa un nuevo usuario con tier FREE.
        """
        if user_id in self.subscriptions:
            return self.subscriptions[user_id]
        
        # Crear suscripción FREE
        subscription = Subscription(
            user_id=user_id,
            tier=SubscriptionTier.FREE.value,
            status="active",
            started_at=datetime.now().isoformat()
        )
        
        self.subscriptions[user_id] = subscription
        
        # Crear usage stats
        tier_limits = self.TIER_CONFIG[SubscriptionTier.FREE.value]
        usage = UsageStats(
            user_id=user_id,
            searches_limit=tier_limits.daily_searches,
            watchlist_limit=tier_limits.watchlist_slots,
            alerts_limit=tier_limits.custom_alerts
        )
        
        self.usage_stats[user_id] = usage
        
        self.analytics["total_users"] += 1
        self.analytics["free_users"] += 1
        
        self._save_data()
        
        logger.info(f"✅ User {user_id} initialized as FREE")
        return subscription
    
    def can_use_feature(self, user_id: int, feature: Feature) -> Tuple[bool, Optional[str]]:
        """
        Verifica si un usuario puede usar una feature.
        
        Returns:
            (can_use, reason_if_not)
        """
        if user_id not in self.subscriptions:
            self.initialize_user(user_id)
        
        subscription = self.subscriptions[user_id]
        tier_limits = self.TIER_CONFIG[subscription.tier]
        
        # Verificar si la feature está disponible en el tier
        if feature.value in tier_limits.features:
            return True, None
        
        # Feature bloqueada
        reason = f"🔒 Esta feature requiere {self._get_minimum_tier_for_feature(feature).value.upper()}"
        return False, reason
    
    def _get_minimum_tier_for_feature(self, feature: Feature) -> SubscriptionTier:
        """Obtiene el tier mínimo que desbloquea una feature"""
        for tier_enum in [SubscriptionTier.BASIC, SubscriptionTier.PRO, SubscriptionTier.PREMIUM]:
            tier_limits = self.TIER_CONFIG[tier_enum.value]
            if feature.value in tier_limits.features:
                return tier_enum
        return SubscriptionTier.PREMIUM
    
    def check_usage_limit(self, user_id: int, limit_type: str) -> Tuple[bool, int, int]:
        """
        Verifica si el usuario puede realizar una acción según límites.
        
        Args:
            limit_type: 'searches', 'watchlist', 'alerts'
        
        Returns:
            (can_use, current_usage, limit)
        """
        if user_id not in self.usage_stats:
            self.initialize_user(user_id)
        
        usage = self.usage_stats[user_id]
        
        # Reset diario si es necesario
        self._check_daily_reset(user_id)
        
        if limit_type == 'searches':
            return (
                usage.searches_today < usage.searches_limit,
                usage.searches_today,
                usage.searches_limit
            )
        elif limit_type == 'watchlist':
            # Esto se verificaría contra la watchlist real
            return (True, 0, usage.watchlist_limit)
        elif limit_type == 'alerts':
            return (
                usage.alerts_triggered_today < usage.alerts_limit,
                usage.alerts_triggered_today,
                usage.alerts_limit
            )
        
        return False, 0, 0
    
    def increment_usage(self, user_id: int, usage_type: str):
        """Incrementa contador de uso"""
        if user_id not in self.usage_stats:
            self.initialize_user(user_id)
        
        usage = self.usage_stats[user_id]
        
        if usage_type == 'searches':
            usage.searches_today += 1
        elif usage_type == 'alerts':
            usage.alerts_triggered_today += 1
        
        self._save_data()
    
    def _check_daily_reset(self, user_id: int):
        """Resetea contadores diarios si es necesario"""
        usage = self.usage_stats[user_id]
        last_reset = datetime.fromisoformat(usage.last_reset)
        now = datetime.now()
        
        # Si es un nuevo día, resetear
        if now.date() > last_reset.date():
            usage.searches_today = 0
            usage.alerts_triggered_today = 0
            usage.last_reset = now.isoformat()
            self._save_data()
            logger.debug(f"🔄 Daily reset for user {user_id}")
    
    def show_paywall(
        self,
        user_id: int,
        feature: Feature,
        context: str,
        variant: str = "default"
    ) -> PaywallEvent:
        """
        Registra un evento de paywall mostrado.
        
        Returns:
            PaywallEvent creado
        """
        import hashlib
        
        event_id = hashlib.md5(
            f"{user_id}{feature.value}{datetime.now()}".encode()
        ).hexdigest()[:12]
        
        event = PaywallEvent(
            event_id=event_id,
            user_id=user_id,
            feature=feature.value,
            trigger_context=context,
            shown_at=datetime.now().isoformat(),
            variant=variant
        )
        
        self.paywall_events.append(event)
        self.analytics["upgrade_funnel"]["paywalls_shown"] += 1
        
        self._save_data()
        
        logger.info(f"🚪 Paywall shown to user {user_id} for {feature.value}")
        return event
    
    def track_paywall_action(
        self,
        event_id: str,
        action: str
    ):
        """
        Registra acción del usuario ante un paywall.
        
        Actions: upgraded, dismissed, learn_more
        """
        event = next((e for e in self.paywall_events if e.event_id == event_id), None)
        
        if not event:
            return
        
        event.action_taken = action
        
        if action == "learn_more":
            self.analytics["upgrade_funnel"]["learn_more_clicks"] += 1
        elif action == "upgraded":
            event.converted = True
            self.analytics["upgrade_funnel"]["upgrades"] += 1
        
        self._save_data()
        self._update_analytics()
    
    def start_trial(
        self,
        user_id: int,
        trial_tier: SubscriptionTier = SubscriptionTier.PRO,
        trial_days: int = 7
    ) -> Tuple[bool, str]:
        """
        Inicia un trial para el usuario.
        
        Returns:
            (success, message)
        """
        if user_id not in self.subscriptions:
            self.initialize_user(user_id)
        
        subscription = self.subscriptions[user_id]
        
        # Verificar si ya usó trial
        if subscription.trial_used:
            return False, "❌ Ya has usado tu período de prueba"
        
        # Actualizar a trial
        subscription.tier = trial_tier.value
        subscription.status = "trial"
        subscription.trial_used = True
        subscription.trial_days = trial_days
        subscription.trial_ends_at = (
            datetime.now() + timedelta(days=trial_days)
        ).isoformat()
        
        # Actualizar límites
        self._update_user_limits(user_id)
        
        # Analytics
        self.analytics["trial_users"] += 1
        
        self._save_data()
        
        msg = (
            f"✨ ¡Trial de {trial_tier.value.upper()} activado!\n"
            f"📅 {trial_days} días gratis\n"
            f"⏰ Finaliza: {subscription.trial_ends_at[:10]}"
        )
        
        logger.info(f"🎁 Trial started for user {user_id}")
        return True, msg
    
    def upgrade_subscription(
        self,
        user_id: int,
        new_tier: SubscriptionTier,
        billing_cycle: str = "monthly"
    ) -> Tuple[bool, str]:
        """
        Actualiza la suscripción del usuario.
        
        Returns:
            (success, message)
        """
        if user_id not in self.subscriptions:
            self.initialize_user(user_id)
        
        subscription = self.subscriptions[user_id]
        old_tier = subscription.tier
        
        # Actualizar tier
        subscription.tier = new_tier.value
        subscription.status = "active"
        subscription.billing_cycle = billing_cycle
        subscription.upgrades_count += 1
        subscription.expires_at = (
            datetime.now() + timedelta(days=30 if billing_cycle == "monthly" else 365)
        ).isoformat()
        
        # Calcular precio
        tier_limits = self.TIER_CONFIG[new_tier.value]
        price = (
            tier_limits.price_monthly if billing_cycle == "monthly" 
            else tier_limits.price_yearly
        )
        subscription.lifetime_value += price
        
        # Actualizar límites
        self._update_user_limits(user_id)
        
        # Analytics
        if old_tier == SubscriptionTier.FREE.value:
            self.analytics["free_users"] -= 1
            self.analytics["paid_users"] += 1
        
        self._save_data()
        self._update_analytics()
        
        msg = (
            f"✅ ¡Upgrade exitoso!\n"
            f"🏆 Ahora eres {new_tier.value.upper()}\n"
            f"💰 {price}€/{billing_cycle}"
        )
        
        logger.info(f"⬆️ User {user_id} upgraded from {old_tier} to {new_tier.value}")
        return True, msg
    
    def _update_user_limits(self, user_id: int):
        """Actualiza los límites de uso según el tier actual"""
        subscription = self.subscriptions[user_id]
        usage = self.usage_stats[user_id]
        
        tier_limits = self.TIER_CONFIG[subscription.tier]
        
        usage.searches_limit = tier_limits.daily_searches
        usage.watchlist_limit = tier_limits.watchlist_slots
        usage.alerts_limit = tier_limits.custom_alerts
    
    def get_subscription(self, user_id: int) -> Optional[Subscription]:
        """Obtiene la suscripción del usuario"""
        return self.subscriptions.get(user_id)
    
    def get_tier_features(self, tier: SubscriptionTier) -> TierLimits:
        """Obtiene la configuración de un tier"""
        return self.TIER_CONFIG[tier.value]
    
    def get_upgrade_options(self, user_id: int) -> List[Dict]:
        """
        Obtiene opciones de upgrade para el usuario.
        
        Returns:
            Lista de tiers superiores con precios
        """
        if user_id not in self.subscriptions:
            self.initialize_user(user_id)
        
        current_tier = self.subscriptions[user_id].tier
        tier_order = [t.value for t in SubscriptionTier]
        current_index = tier_order.index(current_tier)
        
        options = []
        for tier_value in tier_order[current_index + 1:]:
            tier_limits = self.TIER_CONFIG[tier_value]
            options.append({
                "tier": tier_value,
                "price_monthly": tier_limits.price_monthly,
                "price_yearly": tier_limits.price_yearly,
                "features": list(tier_limits.features),
                "limits": {
                    "searches": tier_limits.daily_searches,
                    "watchlist": tier_limits.watchlist_slots,
                    "alerts": tier_limits.custom_alerts
                }
            })
        
        return options
    
    def _update_analytics(self):
        """Actualiza métricas de analytics"""
        # Conversion rate del funnel
        paywalls = self.analytics["upgrade_funnel"]["paywalls_shown"]
        upgrades = self.analytics["upgrade_funnel"]["upgrades"]
        
        if paywalls > 0:
            self.analytics["upgrade_funnel"]["conversion_rate"] = (
                upgrades / paywalls * 100
            )
        
        # Conversion rate global
        total = self.analytics["total_users"]
        paid = self.analytics["paid_users"]
        
        if total > 0:
            self.analytics["conversion_rate"] = paid / total * 100
        
        # MRR (Monthly Recurring Revenue)
        mrr = 0.0
        for sub in self.subscriptions.values():
            if sub.status == "active" and sub.tier != SubscriptionTier.FREE.value:
                tier_limits = self.TIER_CONFIG[sub.tier]
                if sub.billing_cycle == "monthly":
                    mrr += tier_limits.price_monthly
                else:
                    mrr += tier_limits.price_yearly / 12
        
        self.analytics["mrr"] = mrr
        
        # ARPU (Average Revenue Per User)
        if total > 0:
            self.analytics["arpu"] = mrr / total
        
        # LTV (Lifetime Value) promedio
        if len(self.subscriptions) > 0:
            total_ltv = sum(s.lifetime_value for s in self.subscriptions.values())
            self.analytics["ltv"] = total_ltv / len(self.subscriptions)
        
        # Tier distribution
        tier_dist = {}
        for sub in self.subscriptions.values():
            tier_dist[sub.tier] = tier_dist.get(sub.tier, 0) + 1
        self.analytics["tier_distribution"] = tier_dist
        
        self.analytics["last_updated"] = datetime.now().isoformat()
    
    def get_analytics(self) -> Dict:
        """Retorna analytics completos"""
        return self.analytics


if __name__ == "__main__":
    # Testing
    print("🚀 Testing FreemiumManager...\n")
    
    manager = FreemiumManager()
    
    # Test 1: Initialize user
    print("1. Initializing user...")
    sub = manager.initialize_user(12345)
    print(f"   Tier: {sub.tier}")
    print(f"   Status: {sub.status}\n")
    
    # Test 2: Check feature access
    print("2. Checking feature access...")
    can_use, reason = manager.can_use_feature(12345, Feature.UNLIMITED_SEARCHES)
    print(f"   Unlimited searches: {can_use}")
    if reason:
        print(f"   Reason: {reason}\n")
    
    # Test 3: Check usage limits
    print("3. Checking usage limits...")
    can_search, current, limit = manager.check_usage_limit(12345, 'searches')
    print(f"   Can search: {can_search}")
    print(f"   Usage: {current}/{limit}\n")
    
    # Test 4: Show paywall
    print("4. Showing paywall...")
    event = manager.show_paywall(
        12345,
        Feature.UNLIMITED_SEARCHES,
        "limit_reached"
    )
    print(f"   Event ID: {event.event_id}\n")
    
    # Test 5: Start trial
    print("5. Starting trial...")
    success, msg = manager.start_trial(12345)
    print(f"   {msg}\n")
    
    # Test 6: Upgrade
    print("6. Upgrading subscription...")
    success, msg = manager.upgrade_subscription(
        12345,
        SubscriptionTier.PRO,
        "monthly"
    )
    print(f"   {msg}\n")
    
    # Test 7: Analytics
    print("7. Analytics...")
    analytics = manager.get_analytics()
    print(f"   Total users: {analytics['total_users']}")
    print(f"   Paid users: {analytics['paid_users']}")
    print(f"   Conversion rate: {analytics['conversion_rate']:.1f}%")
    print(f"   MRR: €{analytics['mrr']:.2f}")
    
    print("\n✅ Tests completados!")
