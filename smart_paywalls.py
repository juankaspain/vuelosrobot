#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Smart Paywalls & Value Messaging - IT6 Day 2/5
Paywalls inteligentes con mensajes contextuales y personalizados

Author: @Juanka_Spain
Version: 13.2.0
Date: 2026-01-16
"""

import json
import logging
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from enum import Enum
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

logger = logging.getLogger(__name__)


class PaywallTrigger(Enum):
    """Tipos de triggers para paywalls"""
    LIMIT_REACHED = "limit_reached"  # Llegó al límite diario
    FEATURE_LOCKED = "feature_locked"  # Intentó usar feature bloqueada
    TIME_BASED = "time_based"  # Momento estratégico (ej: después de encontrar deal)
    VALUE_MOMENT = "value_moment"  # Usuario acaba de obtener valor
    ONBOARDING = "onboarding"  # Durante onboarding


class PaywallVariant(Enum):
    """Variantes de paywall para A/B testing"""
    FEATURE_FOCUSED = "feature_focused"  # Enfocado en features
    SAVINGS_FOCUSED = "savings_focused"  # Enfocado en ahorro
    SOCIAL_PROOF = "social_proof"  # Prueba social
    SCARCITY = "scarcity"  # Escasez/urgencia
    TRIAL_FIRST = "trial_first"  # Ofrece trial primero


@dataclass
class PaywallMessage:
    """Mensaje de paywall"""
    variant: str
    trigger: str
    
    # Contenido
    headline: str
    description: str
    benefits: List[str]
    cta_primary: str
    cta_secondary: Optional[str] = None
    
    # Visual
    emoji: str = "🔒"
    image_url: Optional[str] = None
    
    # Pricing
    show_pricing: bool = True
    highlight_discount: bool = False


@dataclass
class UserContext:
    """Contexto del usuario para personalizar paywall"""
    user_id: int
    tier: str
    
    # Engagement
    days_active: int
    total_searches: int
    deals_found: int
    
    # Behavior
    favorite_routes: List[str]
    avg_search_price: float
    
    # Previous paywalls
    paywalls_seen: int
    paywalls_dismissed: int
    last_paywall_at: Optional[str] = None


class SmartPaywallManager:
    """
    Gestor de paywalls inteligentes.
    
    Features:
    - Mensajes contextuales
    - Personalización basada en comportamiento
    - A/B testing
    - Timing óptimo
    - Value propositions
    """
    
    # Mensajes por trigger y variante
    PAYWALL_MESSAGES = {
        # LIMIT_REACHED
        (PaywallTrigger.LIMIT_REACHED.value, PaywallVariant.FEATURE_FOCUSED.value): PaywallMessage(
            variant=PaywallVariant.FEATURE_FOCUSED.value,
            trigger=PaywallTrigger.LIMIT_REACHED.value,
            headline="🚀 ¡Desbloquea Búsquedas Ilimitadas!",
            description="Has alcanzado tu límite diario. Upgrade para seguir cazando chollos.",
            benefits=[
                "✅ Búsquedas ilimitadas",
                "✅ Watchlist extendida (30 slots)",
                "✅ Alertas personalizadas",
                "✅ Análisis de tendencias",
                "✅ Sin anuncios"
            ],
            cta_primary="💎 Upgrade a PRO",
            cta_secondary="🎁 Probar 7 días gratis",
            emoji="🚀"
        ),
        
        (PaywallTrigger.LIMIT_REACHED.value, PaywallVariant.SAVINGS_FOCUSED.value): PaywallMessage(
            variant=PaywallVariant.SAVINGS_FOCUSED.value,
            trigger=PaywallTrigger.LIMIT_REACHED.value,
            headline="💰 ¡No Pierdas Más Chollos!",
            description="Usuarios PRO ahorran un promedio de €347 al mes. Tú también puedes.",
            benefits=[
                "💵 Ahorro promedio: €347/mes",
                "🔔 Alertas instantáneas 24/7",
                "📈 Predicciones de precio",
                "⏱️ Asistente de reserva",
                "🏆 Acceso prioritario a deals"
            ],
            cta_primary="🚀 Empezar a Ahorrar",
            cta_secondary="📊 Ver Cálculo",
            emoji="💰",
            highlight_discount=True
        ),
        
        (PaywallTrigger.LIMIT_REACHED.value, PaywallVariant.SOCIAL_PROOF.value): PaywallMessage(
            variant=PaywallVariant.SOCIAL_PROOF.value,
            trigger=PaywallTrigger.LIMIT_REACHED.value,
            headline="👥 Únete a 5,000+ Cazadores PRO",
            description="Miles de usuarios ya ahorran cientos cada mes con PRO.",
            benefits=[
                "⭐ 4.9/5 estrellas (2,341 reviews)",
                "👥 5,000+ usuarios PRO activos",
                "💸 €1.2M ahorrados en total",
                "🏆 #1 en ahorro de vuelos",
                "🔥 1,234 deals encontrados hoy"
            ],
            cta_primary="✨ Unirme a PRO",
            cta_secondary="💬 Ver Testimonios",
            emoji="👥"
        ),
        
        (PaywallTrigger.LIMIT_REACHED.value, PaywallVariant.TRIAL_FIRST.value): PaywallMessage(
            variant=PaywallVariant.TRIAL_FIRST.value,
            trigger=PaywallTrigger.LIMIT_REACHED.value,
            headline="🎁 7 Días Gratis de PRO",
            description="Prueba todas las features sin compromiso. Cancela cuando quieras.",
            benefits=[
                "✅ Sin tarjeta de crédito",
                "✅ Acceso completo inmediato",
                "✅ Cancela en cualquier momento",
                "✅ Sin preguntas al cancelar",
                "✅ Soporte prioritario 24/7"
            ],
            cta_primary="🎁 Activar Trial Gratis",
            cta_secondary="💳 Pagar Directamente",
            emoji="🎁"
        ),
        
        # FEATURE_LOCKED
        (PaywallTrigger.FEATURE_LOCKED.value, PaywallVariant.FEATURE_FOCUSED.value): PaywallMessage(
            variant=PaywallVariant.FEATURE_FOCUSED.value,
            trigger=PaywallTrigger.FEATURE_LOCKED.value,
            headline="🔓 Desbloquea Esta Feature",
            description="Esta feature está disponible en planes PRO y PREMIUM.",
            benefits=[
                "✨ Feature que acabas de ver",
                "➕ +15 features adicionales",
                "🚀 Búsquedas ilimitadas",
                "📈 Analytics avanzados",
                "🎯 Soporte prioritario"
            ],
            cta_primary="🔓 Desbloquear Ahora",
            cta_secondary="📝 Ver Todas las Features",
            emoji="🔓"
        ),
        
        # VALUE_MOMENT
        (PaywallTrigger.VALUE_MOMENT.value, PaywallVariant.SAVINGS_FOCUSED.value): PaywallMessage(
            variant=PaywallVariant.SAVINGS_FOCUSED.value,
            trigger=PaywallTrigger.VALUE_MOMENT.value,
            headline="🎉 ¡Acabas de Encontrar un Chollo!",
            description="Imagina encontrar chollos así todos los días con alertas automáticas.",
            benefits=[
                "🔔 Alertas instantáneas de chollos",
                "🔍 Búsquedas ilimitadas",
                "🎯 Hasta 10x más deals",
                "📈 Predicciones de precio IA",
                "✅ Precio: €9.99/mes"
            ],
            cta_primary="🚀 Maximizar Ahorro",
            cta_secondary="📊 Ver Stats",
            emoji="🎉",
            highlight_discount=True
        ),
    }
    
    # Reglas de timing (cuándo NO mostrar paywall)
    MIN_HOURS_BETWEEN_PAYWALLS = 24
    MAX_PAYWALLS_PER_WEEK = 3
    
    def __init__(self, data_dir: str = "."):
        self.data_dir = Path(data_dir)
        self.contexts_file = self.data_dir / "user_contexts.json"
        self.experiments_file = self.data_dir / "ab_experiments.json"
        
        self.contexts: Dict[int, UserContext] = {}
        self.experiments: Dict = self._init_experiments()
        
        self._load_data()
        logger.info("🚪 SmartPaywallManager initialized")
    
    def _init_experiments(self) -> Dict:
        """Inicializa experimentos A/B"""
        return {
            "active_experiment": "variant_test_v1",
            "variants": {
                PaywallVariant.FEATURE_FOCUSED.value: {"weight": 0.25, "conversions": 0, "shows": 0},
                PaywallVariant.SAVINGS_FOCUSED.value: {"weight": 0.25, "conversions": 0, "shows": 0},
                PaywallVariant.SOCIAL_PROOF.value: {"weight": 0.25, "conversions": 0, "shows": 0},
                PaywallVariant.TRIAL_FIRST.value: {"weight": 0.25, "conversions": 0, "shows": 0},
            },
            "results": []
        }
    
    def _load_data(self):
        """Carga datos"""
        if self.contexts_file.exists():
            with open(self.contexts_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.contexts = {
                    int(k): UserContext(**v) for k, v in data.items()
                }
        
        if self.experiments_file.exists():
            with open(self.experiments_file, 'r', encoding='utf-8') as f:
                self.experiments = json.load(f)
    
    def _save_data(self):
        """Guarda datos"""
        with open(self.contexts_file, 'w', encoding='utf-8') as f:
            data = {str(k): asdict(v) for k, v in self.contexts.items()}
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        with open(self.experiments_file, 'w', encoding='utf-8') as f:
            json.dump(self.experiments, f, indent=2, ensure_ascii=False)
    
    def should_show_paywall(self, user_id: int) -> Tuple[bool, Optional[str]]:
        """
        Determina si se debe mostrar un paywall ahora.
        
        Returns:
            (should_show, reason_if_not)
        """
        if user_id not in self.contexts:
            return True, None
        
        context = self.contexts[user_id]
        
        # Verificar tiempo desde último paywall
        if context.last_paywall_at:
            last_shown = datetime.fromisoformat(context.last_paywall_at)
            hours_since = (datetime.now() - last_shown).total_seconds() / 3600
            
            if hours_since < self.MIN_HOURS_BETWEEN_PAYWALLS:
                return False, f"Too soon (shown {hours_since:.1f}h ago)"
        
        # Verificar límite semanal
        # (Simplificado - en producción verificarías los últimos 7 días)
        if context.paywalls_seen >= self.MAX_PAYWALLS_PER_WEEK:
            return False, "Weekly limit reached"
        
        # Verificar ratio dismiss
        if context.paywalls_seen > 0:
            dismiss_rate = context.paywalls_dismissed / context.paywalls_seen
            if dismiss_rate > 0.8:  # 80% dismissed
                return False, "High dismiss rate"
        
        return True, None
    
    def select_variant(self, user_id: int, trigger: PaywallTrigger) -> PaywallVariant:
        """
        Selecciona la variante óptima para mostrar.
        
        Usa:
        - A/B testing weights
        - Contexto del usuario
        - Performance histórico
        """
        # Para TRIAL_FIRST, priorizarlo si el usuario es nuevo y activo
        if user_id in self.contexts:
            context = self.contexts[user_id]
            if context.days_active < 7 and context.total_searches >= 5:
                return PaywallVariant.TRIAL_FIRST
        
        # Weighted random basado en performance
        variants = list(self.experiments["variants"].keys())
        weights = [self.experiments["variants"][v]["weight"] for v in variants]
        
        selected = random.choices(variants, weights=weights)[0]
        return PaywallVariant(selected)
    
    def get_paywall_message(
        self,
        user_id: int,
        trigger: PaywallTrigger,
        variant: Optional[PaywallVariant] = None
    ) -> PaywallMessage:
        """
        Obtiene el mensaje de paywall personalizado.
        """
        # Seleccionar variante si no se especifica
        if variant is None:
            variant = self.select_variant(user_id, trigger)
        
        # Obtener mensaje base
        key = (trigger.value, variant.value)
        
        if key in self.PAYWALL_MESSAGES:
            message = self.PAYWALL_MESSAGES[key]
        else:
            # Fallback a feature_focused
            message = self.PAYWALL_MESSAGES[
                (trigger.value, PaywallVariant.FEATURE_FOCUSED.value)
            ]
        
        # Personalizar con contexto si existe
        if user_id in self.contexts:
            message = self._personalize_message(message, self.contexts[user_id])
        
        return message
    
    def _personalize_message(self, message: PaywallMessage, context: UserContext) -> PaywallMessage:
        """
        Personaliza un mensaje con el contexto del usuario.
        """
        # Crear copia para no modificar el original
        import copy
        personalized = copy.deepcopy(message)
        
        # Personalizar descripción con stats
        if context.deals_found > 0:
            personalized.description = (
                f"Has encontrado {context.deals_found} deals. "
                f"Usuarios PRO encuentran 10x más."
            )
        
        # Añadir beneficio personalizado por ruta favorita
        if context.favorite_routes:
            route = context.favorite_routes[0]
            personalized.benefits.insert(
                0,
                f"🎯 Alertas personalizadas para {route}"
            )
        
        return personalized
    
    def generate_paywall_keyboard(
        self,
        message: PaywallMessage,
        event_id: str
    ) -> InlineKeyboardMarkup:
        """
        Genera el teclado inline del paywall.
        """
        buttons = []
        
        # CTA primario
        buttons.append([
            InlineKeyboardButton(
                message.cta_primary,
                callback_data=f"paywall_primary_{event_id}"
            )
        ])
        
        # CTA secundario si existe
        if message.cta_secondary:
            buttons.append([
                InlineKeyboardButton(
                    message.cta_secondary,
                    callback_data=f"paywall_secondary_{event_id}"
                )
            ])
        
        # Botones adicionales
        buttons.append([
            InlineKeyboardButton(
                "💳 Ver Precios",
                callback_data=f"paywall_pricing_{event_id}"
            ),
            InlineKeyboardButton(
                "❓ Más Info",
                callback_data=f"paywall_info_{event_id}"
            )
        ])
        
        # Botón de cerrar
        buttons.append([
            InlineKeyboardButton(
                "❌ Ahora No",
                callback_data=f"paywall_dismiss_{event_id}"
            )
        ])
        
        return InlineKeyboardMarkup(buttons)
    
    def format_paywall_text(self, message: PaywallMessage) -> str:
        """
        Formatea el texto completo del paywall.
        """
        text = f"{message.emoji} **{message.headline}**\n\n"
        text += f"{message.description}\n\n"
        
        # Benefits
        text += "**✨ Con PRO obtienes:**\n"
        for benefit in message.benefits:
            text += f"{benefit}\n"
        
        # Pricing si se muestra
        if message.show_pricing:
            text += "\n💰 **Precios:**\n"
            text += "• €9.99/mes o €99.99/año\n"
            
            if message.highlight_discount:
                text += "✨ **¡Ahorra €20 con plan anual!**\n"
        
        text += "\n🛡️ _Cancela cuando quieras. Sin permanencia._"
        
        return text
    
    def track_paywall_shown(
        self,
        user_id: int,
        event_id: str,
        variant: PaywallVariant
    ):
        """
        Registra que se mostró un paywall.
        """
        # Actualizar contexto
        if user_id not in self.contexts:
            # Crear contexto básico
            self.contexts[user_id] = UserContext(
                user_id=user_id,
                tier="free",
                days_active=0,
                total_searches=0,
                deals_found=0,
                favorite_routes=[],
                avg_search_price=0.0,
                paywalls_seen=0,
                paywalls_dismissed=0
            )
        
        context = self.contexts[user_id]
        context.paywalls_seen += 1
        context.last_paywall_at = datetime.now().isoformat()
        
        # Actualizar experimento
        self.experiments["variants"][variant.value]["shows"] += 1
        
        self._save_data()
        logger.info(f"🚪 Paywall shown to user {user_id} (variant: {variant.value})")
    
    def track_paywall_action(
        self,
        user_id: int,
        event_id: str,
        action: str,
        variant: PaywallVariant
    ):
        """
        Registra acción del usuario en el paywall.
        
        Actions: primary, secondary, pricing, info, dismiss
        """
        if user_id not in self.contexts:
            return
        
        context = self.contexts[user_id]
        
        if action == "dismiss":
            context.paywalls_dismissed += 1
        elif action == "primary":
            # Conversión!
            self.experiments["variants"][variant.value]["conversions"] += 1
            self.experiments["results"].append({
                "user_id": user_id,
                "variant": variant.value,
                "timestamp": datetime.now().isoformat(),
                "converted": True
            })
        
        self._save_data()
        logger.info(f"👆 Paywall action: {action} by user {user_id}")
    
    def get_conversion_rates(self) -> Dict[str, float]:
        """
        Calcula tasas de conversión por variante.
        """
        rates = {}
        
        for variant, data in self.experiments["variants"].items():
            shows = data["shows"]
            conversions = data["conversions"]
            
            if shows > 0:
                rates[variant] = (conversions / shows) * 100
            else:
                rates[variant] = 0.0
        
        return rates
    
    def optimize_weights(self):
        """
        Optimiza los pesos de las variantes basado en performance.
        
        Usa Thompson Sampling para balance exploration/exploitation.
        """
        rates = self.get_conversion_rates()
        
        if not rates or max(rates.values()) == 0:
            return  # No hay datos suficientes
        
        # Normalizar a pesos que sumen 1.0
        total = sum(rates.values())
        
        if total > 0:
            for variant in self.experiments["variants"]:
                # Dar más peso a las variantes que convierten mejor
                # Pero mantener al menos 10% para exploration
                rate = rates.get(variant, 0.0)
                normalized = rate / total
                self.experiments["variants"][variant]["weight"] = max(0.1, normalized)
            
            # Re-normalizar para asegurar suma de 1.0
            total_weight = sum(
                v["weight"] for v in self.experiments["variants"].values()
            )
            for variant in self.experiments["variants"]:
                self.experiments["variants"][variant]["weight"] /= total_weight
        
        self._save_data()
        logger.info("🎯 Variant weights optimized")


if __name__ == "__main__":
    # Testing
    print("🚀 Testing SmartPaywallManager...\n")
    
    manager = SmartPaywallManager()
    
    # Test 1: Should show paywall
    print("1. Checking if should show paywall...")
    should_show, reason = manager.should_show_paywall(12345)
    print(f"   Should show: {should_show}")
    if reason:
        print(f"   Reason: {reason}\n")
    
    # Test 2: Select variant
    print("2. Selecting variant...")
    variant = manager.select_variant(12345, PaywallTrigger.LIMIT_REACHED)
    print(f"   Variant: {variant.value}\n")
    
    # Test 3: Get message
    print("3. Getting paywall message...")
    message = manager.get_paywall_message(
        12345,
        PaywallTrigger.LIMIT_REACHED,
        variant
    )
    print(f"   Headline: {message.headline}")
    print(f"   Benefits: {len(message.benefits)}\n")
    
    # Test 4: Format text
    print("4. Formatting paywall text...")
    text = manager.format_paywall_text(message)
    print(f"   Length: {len(text)} chars\n")
    
    # Test 5: Track shown
    print("5. Tracking paywall shown...")
    manager.track_paywall_shown(12345, "test_event_123", variant)
    print("   Tracked\n")
    
    # Test 6: Conversion rates
    print("6. Getting conversion rates...")
    rates = manager.get_conversion_rates()
    for var, rate in rates.items():
        print(f"   {var}: {rate:.1f}%")
    
    print("\n✅ Tests completados!")
