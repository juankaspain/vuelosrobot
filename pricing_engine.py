#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pricing Engine with Smart Discounts and Upgrade Prompts
IT6 - DAY 4/5

Features:
- Multiple pricing tiers (Basic/Pro, Monthly/Annual)
- Smart dynamic discounts (up to 40%)
- Regional pricing support
- Contextual upgrade prompts
- Limited-time offers
- Discount stacking rules

Author: @Juanka_Spain
Version: 14.0.0-alpha.4
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

class PricingTier(Enum):
    """Available pricing tiers"""
    BASIC_MONTHLY = "basic_monthly"
    BASIC_ANNUAL = "basic_annual"
    PRO_MONTHLY = "pro_monthly"
    PRO_ANNUAL = "pro_annual"


class DiscountType(Enum):
    """Types of discounts"""
    POWER_USER = "power_user"          # Heavy usage
    REFERRAL_KING = "referral_king"    # Many referrals
    TRIAL_ENDING = "trial_ending"      # Trial expiring
    SEASONAL = "seasonal"              # Limited time promo
    LOYALTY = "loyalty"                # Long-time user
    FIRST_TIME = "first_time"          # First subscription
    ANNUAL_UPGRADE = "annual_upgrade"  # Monthly to annual


class UpgradeContext(Enum):
    """Context for showing upgrade prompts"""
    SEARCH_LIMIT = "search_limit"
    WATCHLIST_FULL = "watchlist_full"
    DEAL_MISSED = "deal_missed"
    HIGH_VALUE_SHOWN = "high_value"
    TRIAL_ENDING = "trial_ending"
    POWER_USER = "power_user"
    REFERRAL_SUCCESS = "referral_success"


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class PricingPlan:
    """Pricing plan details"""
    tier: str  # PricingTier value
    name: str
    base_price: float
    currency: str
    billing_period: str  # "monthly" or "annual"
    features: List[str]
    trial_days: int
    discount_percent: int = 0
    popular: bool = False
    recommended_for: Optional[str] = None
    
    @property
    def monthly_equivalent(self) -> float:
        """Get monthly equivalent price"""
        if self.billing_period == "monthly":
            return self.base_price
        else:
            return self.base_price / 12
    
    @property
    def annual_savings(self) -> float:
        """Savings vs monthly if annual"""
        if self.billing_period != "annual":
            return 0
        monthly_total = self.monthly_equivalent * 12
        return (monthly_total * 12) - self.base_price


@dataclass
class Discount:
    """Applied discount"""
    type: str  # DiscountType value
    percent: int
    description: str
    condition_met: bool = True
    expires: Optional[datetime] = None


@dataclass
class PriceCalculation:
    """Final price calculation with discounts"""
    tier: str
    base_price: float
    discounts_applied: List[Discount]
    total_discount_percent: int
    final_price: float
    currency: str
    savings: float
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['discounts_applied'] = [asdict(d) for d in self.discounts_applied]
        return data


@dataclass
class UpgradePrompt:
    """Contextual upgrade prompt"""
    context: str  # UpgradeContext value
    headline: str
    message: str
    primary_cta: str
    secondary_cta: Optional[str] = None
    urgency_level: int = 1  # 1-5
    recommended_tier: str = "basic_monthly"
    
    def to_dict(self) -> Dict:
        return asdict(self)


# ============================================================================
# PRICING ENGINE
# ============================================================================

class PricingEngine:
    """
    Manages pricing, discounts, and upgrade prompts.
    
    Features:
    - Multiple tiers with regional pricing
    - Smart dynamic discounts (max 40%)
    - Contextual upgrade prompts
    - Discount stacking rules
    - Limited-time offers
    """
    
    def __init__(self, data_dir: str = ".", config_file: str = "pricing_config.json"):
        self.data_dir = Path(data_dir)
        self.config_file = self.data_dir / config_file
        
        # Load pricing configuration
        self.config = self._load_config()
        self.tiers = self._load_tiers()
        
        # Discount limits
        self.max_discount = self.config.get('limits', {}).get('max_discount_percent', 40)
        self.max_stack = self.config.get('limits', {}).get('max_discount_stack', 3)
        
        print("✅ PricingEngine initialized")
    
    # ========================================================================
    # CONFIGURATION
    # ========================================================================
    
    def _load_config(self) -> Dict:
        """Load pricing configuration"""
        if not self.config_file.exists():
            print("⚠️ Pricing config not found, using defaults")
            return self._get_default_config()
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Error loading config: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """Get default pricing configuration"""
        return {
            "tiers": {
                "basic_monthly": {
                    "name": "Premium Monthly",
                    "price": 9.99,
                    "currency": "EUR",
                    "billing_period": "monthly",
                    "features": ["unlimited_searches", "unlimited_watchlist", "priority_notifications"],
                    "trial_days": 7
                },
                "basic_annual": {
                    "name": "Premium Annual",
                    "price": 99.99,
                    "currency": "EUR",
                    "billing_period": "annual",
                    "discount_percent": 17,
                    "features": ["unlimited_searches", "unlimited_watchlist", "priority_notifications"],
                    "trial_days": 7,
                    "popular": True
                }
            },
            "regional_pricing": {
                "ES": {"basic_monthly": 9.99, "basic_annual": 99.99, "currency": "EUR"}
            },
            "discount_rules": {},
            "limits": {"max_discount_percent": 40, "max_discount_stack": 3}
        }
    
    def _load_tiers(self) -> Dict[str, PricingPlan]:
        """Load pricing tiers from config"""
        tiers = {}
        
        for tier_id, tier_data in self.config.get('tiers', {}).items():
            tiers[tier_id] = PricingPlan(
                tier=tier_id,
                name=tier_data.get('name', ''),
                base_price=tier_data.get('price', 0),
                currency=tier_data.get('currency', 'EUR'),
                billing_period=tier_data.get('billing_period', 'monthly'),
                features=tier_data.get('features', []),
                trial_days=tier_data.get('trial_days', 7),
                discount_percent=tier_data.get('discount_percent', 0),
                popular=tier_data.get('popular', False),
                recommended_for=tier_data.get('recommended_for')
            )
        
        return tiers
    
    # ========================================================================
    # PRICING
    # ========================================================================
    
    def get_tier(self, tier_id: str) -> Optional[PricingPlan]:
        """Get pricing tier by ID"""
        return self.tiers.get(tier_id)
    
    def get_all_tiers(self) -> List[PricingPlan]:
        """Get all available pricing tiers"""
        return list(self.tiers.values())
    
    def get_regional_price(self, tier_id: str, region: str = "ES") -> Optional[float]:
        """Get regional pricing for tier"""
        regional = self.config.get('regional_pricing', {}).get(region, {})
        
        if tier_id in regional:
            return regional[tier_id]
        
        # Fallback to base price
        tier = self.get_tier(tier_id)
        return tier.base_price if tier else None
    
    # ========================================================================
    # DISCOUNTS
    # ========================================================================
    
    def calculate_available_discounts(self, user_profile: Dict) -> List[Discount]:
        """
        Calculate all applicable discounts for user.
        
        user_profile should contain:
        - total_searches: int
        - referrals: int
        - trial_days_left: int (if in trial)
        - user_age_days: int
        - is_first_subscription: bool
        """
        discounts = []
        discount_rules = self.config.get('discount_rules', {})
        
        # Power user discount
        if user_profile.get('total_searches', 0) > 100:
            rule = discount_rules.get('power_user', {})
            discounts.append(Discount(
                type=DiscountType.POWER_USER.value,
                percent=rule.get('discount_percent', 10),
                description=rule.get('description', 'Descuento usuario activo')
            ))
        
        # Referral king discount
        if user_profile.get('referrals', 0) >= 10:
            rule = discount_rules.get('referral_king', {})
            discounts.append(Discount(
                type=DiscountType.REFERRAL_KING.value,
                percent=rule.get('discount_percent', 10),
                description=rule.get('description', 'Descuento por referidos')
            ))
        
        # Trial ending discount
        if user_profile.get('trial_days_left', 99) <= 1:
            rule = discount_rules.get('trial_ending', {})
            expires = datetime.now() + timedelta(days=1)
            discounts.append(Discount(
                type=DiscountType.TRIAL_ENDING.value,
                percent=rule.get('discount_percent', 20),
                description=rule.get('description', 'Oferta especial fin de trial'),
                expires=expires
            ))
        
        # Loyalty discount
        if user_profile.get('user_age_days', 0) > 90:
            rule = discount_rules.get('loyalty', {})
            discounts.append(Discount(
                type=DiscountType.LOYALTY.value,
                percent=rule.get('discount_percent', 5),
                description=rule.get('description', 'Descuento por antigüedad')
            ))
        
        # First time discount
        if user_profile.get('is_first_subscription', False):
            discounts.append(Discount(
                type=DiscountType.FIRST_TIME.value,
                percent=15,
                description='Oferta primera suscripción'
            ))
        
        # Seasonal promo (if active)
        if self._is_seasonal_promo_active():
            rule = discount_rules.get('seasonal', {})
            expires = datetime.now() + timedelta(days=7)
            discounts.append(Discount(
                type=DiscountType.SEASONAL.value,
                percent=rule.get('discount_percent', 15),
                description=rule.get('description', 'Promoción por tiempo limitado'),
                expires=expires
            ))
        
        return discounts
    
    def _is_seasonal_promo_active(self) -> bool:
        """
        Check if seasonal promotion is active.
        Can be based on dates, events, etc.
        """
        # Example: Active during first week of each month
        now = datetime.now()
        return now.day <= 7
    
    def apply_discounts(self, tier_id: str, user_profile: Dict) -> PriceCalculation:
        """
        Calculate final price with discounts applied.
        
        Returns:
            PriceCalculation with final price
        """
        tier = self.get_tier(tier_id)
        if not tier:
            raise ValueError(f"Invalid tier: {tier_id}")
        
        # Get available discounts
        available_discounts = self.calculate_available_discounts(user_profile)
        
        # Sort by percent (highest first)
        available_discounts.sort(key=lambda d: d.percent, reverse=True)
        
        # Apply discount stacking rules
        applied_discounts = available_discounts[:self.max_stack]
        
        # Calculate total discount
        total_discount = sum(d.percent for d in applied_discounts)
        total_discount = min(total_discount, self.max_discount)
        
        # Calculate final price
        discount_multiplier = (100 - total_discount) / 100
        final_price = tier.base_price * discount_multiplier
        savings = tier.base_price - final_price
        
        return PriceCalculation(
            tier=tier_id,
            base_price=tier.base_price,
            discounts_applied=applied_discounts,
            total_discount_percent=total_discount,
            final_price=round(final_price, 2),
            currency=tier.currency,
            savings=round(savings, 2)
        )
    
    # ========================================================================
    # UPGRADE PROMPTS
    # ========================================================================
    
    def get_upgrade_prompt(self, context: UpgradeContext, user_data: Dict = None) -> UpgradePrompt:
        """
        Get contextual upgrade prompt.
        
        Args:
            context: UpgradeContext enum
            user_data: Optional dict with user-specific data
        
        Returns:
            UpgradePrompt tailored to context
        """
        user_data = user_data or {}
        
        if context == UpgradeContext.SEARCH_LIMIT:
            return UpgradePrompt(
                context=context.value,
                headline="🚫 Límite de Búsquedas Alcanzado",
                message=(
                    f"Has usado tus {user_data.get('limit', 10)} búsquedas diarias. "
                    "Actualiza a Premium para búsquedas ilimitadas."
                ),
                primary_cta="Activar Búsquedas Ilimitadas",
                secondary_cta="Ver Planes",
                urgency_level=4,
                recommended_tier="basic_monthly"
            )
        
        elif context == UpgradeContext.WATCHLIST_FULL:
            return UpgradePrompt(
                context=context.value,
                headline="⭐ Watchlist Lleno",
                message=(
                    f"Has usado {user_data.get('slots', 3)}/3 slots. "
                    "Premium te da watchlist ilimitado para no perder ningún chollo."
                ),
                primary_cta="Desbloquear Watchlist Ilimitado",
                secondary_cta="Gestionar Rutas",
                urgency_level=2,
                recommended_tier="basic_monthly"
            )
        
        elif context == UpgradeContext.DEAL_MISSED:
            return UpgradePrompt(
                context=context.value,
                headline="😔 Acabas de Perder un Chollo",
                message=(
                    f"Perdiste un chollo de €{user_data.get('deal_value', 150)} por notificación tardía. "
                    "Premium = notificaciones instantáneas."
                ),
                primary_cta="No Perder Más Chollos",
                secondary_cta="Ver Cómo Funciona",
                urgency_level=5,
                recommended_tier="basic_monthly"
            )
        
        elif context == UpgradeContext.HIGH_VALUE_SHOWN:
            total_value = user_data.get('total_savings', 2450)
            return UpgradePrompt(
                context=context.value,
                headline=f"💰 Has Visto €{total_value} en Chollos",
                message=(
                    f"Imagina cuánto más podrías ahorrar con búsquedas ilimitadas y "
                    "notificaciones priority. Solo €9.99/mes."
                ),
                primary_cta="Desbloquear Todo por €9.99",
                secondary_cta="Ver ROI",
                urgency_level=3,
                recommended_tier="basic_annual"
            )
        
        elif context == UpgradeContext.TRIAL_ENDING:
            days_left = user_data.get('days_left', 2)
            return UpgradePrompt(
                context=context.value,
                headline=f"⏰ Trial Expira en {days_left} Días",
                message=(
                    "No pierdas acceso a búsquedas ilimitadas, watchlist sin límites y "
                    f"notificaciones priority. 🎁 25% OFF si actualizas ahora."
                ),
                primary_cta="Activar Premium con Descuento",
                secondary_cta="Ver Mi Progreso",
                urgency_level=5,
                recommended_tier="basic_annual"
            )
        
        elif context == UpgradeContext.POWER_USER:
            searches = user_data.get('total_searches', 150)
            return UpgradePrompt(
                context=context.value,
                headline="🔥 Eres un Power User",
                message=(
                    f"Con {searches} búsquedas, estás en el top 10% de usuarios. "
                    "Premium te dará herramientas avanzadas para maximizar tu ahorro."
                ),
                primary_cta="Ver Features Premium",
                secondary_cta="Aplicar Descuento 10%",
                urgency_level=2,
                recommended_tier="pro_monthly"
            )
        
        elif context == UpgradeContext.REFERRAL_SUCCESS:
            referrals = user_data.get('referrals', 12)
            return UpgradePrompt(
                context=context.value,
                headline="🏆 Referral King",
                message=(
                    f"Con {referrals} referidos, mereces Premium. "
                    "🎁 10% OFF especial para top referrers."
                ),
                primary_cta="Reclamar Descuento",
                secondary_cta="Ver Planes",
                urgency_level=3,
                recommended_tier="basic_annual"
            )
        
        # Default prompt
        return UpgradePrompt(
            context="default",
            headline="🚀 Desbloquea Premium",
            message="Búsquedas ilimitadas, watchlist sin límites, notificaciones priority y más.",
            primary_cta="Ver Planes Premium",
            urgency_level=1,
            recommended_tier="basic_monthly"
        )
    
    # ========================================================================
    # COMPARISON
    # ========================================================================
    
    def compare_tiers(self, tier_ids: List[str]) -> List[Dict]:
        """
        Compare multiple pricing tiers.
        
        Returns:
            List of tier comparisons
        """
        comparisons = []
        
        for tier_id in tier_ids:
            tier = self.get_tier(tier_id)
            if not tier:
                continue
            
            comparisons.append({
                'tier': tier_id,
                'name': tier.name,
                'price': tier.base_price,
                'monthly_equivalent': tier.monthly_equivalent,
                'currency': tier.currency,
                'billing': tier.billing_period,
                'features': tier.features,
                'trial_days': tier.trial_days,
                'popular': tier.popular,
                'savings': tier.annual_savings if tier.billing_period == 'annual' else 0
            })
        
        return comparisons


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def format_pricing_table(tiers: List[PricingPlan], user_profile: Dict = None) -> str:
    """
    Format pricing tiers as a comparison table.
    
    Args:
        tiers: List of PricingPlan objects
        user_profile: Optional user profile for personalized pricing
    
    Returns:
        Formatted pricing table string
    """
    engine = PricingEngine()
    
    message = "💳 Planes Premium\n\n"
    
    for tier in tiers:
        # Calculate personalized price if profile provided
        if user_profile:
            calc = engine.apply_discounts(tier.tier, user_profile)
            price_str = f"€{calc.final_price}"
            if calc.total_discount_percent > 0:
                price_str += f" (era €{tier.base_price}, -{calc.total_discount_percent}%)"
        else:
            price_str = f"€{tier.base_price}"
        
        popular_badge = " 🔥 POPULAR" if tier.popular else ""
        
        message += f"{'='*40}\n"
        message += f"{tier.name}{popular_badge}\n"
        message += f"{price_str}/{tier.billing_period}\n\n"
        
        # Features
        feature_names = {
            'unlimited_searches': '✅ Búsquedas ilimitadas',
            'unlimited_watchlist': '✅ Watchlist sin límites',
            'priority_notifications': '✅ Notificaciones priority',
            '1year_history': '✅ Historial 1 año',
            'unlimited_groups': '✅ Grupos ilimitados',
            'export_data': '✅ Exportar datos',
            'priority_support': '✅ Soporte 24/7',
            'api_access': '✅ Acceso API',
            'advanced_filters': '✅ Filtros avanzados'
        }
        
        for feature in tier.features[:5]:  # Show top 5
            message += f"{feature_names.get(feature, feature)}\n"
        
        if len(tier.features) > 5:
            message += f"... y {len(tier.features) - 5} más\n"
        
        message += f"\n🎁 {tier.trial_days} días de prueba gratis\n"
        
        if tier.billing_period == "annual":
            message += f"💰 Ahorra €{tier.annual_savings:.2f} vs mensual\n"
        
        message += "\n"
    
    return message


def format_discount_summary(calculation: PriceCalculation) -> str:
    """
    Format discount summary.
    
    Args:
        calculation: PriceCalculation object
    
    Returns:
        Formatted summary string
    """
    message = f"🎉 Descuentos Aplicados\n\n"
    message += f"Precio base: €{calculation.base_price}\n\n"
    
    if calculation.discounts_applied:
        message += "Descuentos:\n"
        for discount in calculation.discounts_applied:
            message += f"• {discount.description}: -{discount.percent}%\n"
            if discount.expires:
                message += f"  ⏰ Expira: {discount.expires.strftime('%Y-%m-%d')}\n"
        
        message += f"\n🎯 Total descuento: {calculation.total_discount_percent}%\n"
        message += f"💰 Ahorras: €{calculation.savings}\n\n"
    
    message += f"💎 PRECIO FINAL: €{calculation.final_price}\n"
    
    return message


# ============================================================================
# MAIN (TESTING)
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("💳 TESTING: Pricing Engine")
    print("="*60 + "\n")
    
    # Initialize engine
    engine = PricingEngine()
    
    print("1️⃣ Available Tiers")
    print("-" * 40)
    
    tiers = engine.get_all_tiers()
    for tier in tiers:
        print(f"\n{tier.name}")
        print(f"  Price: €{tier.base_price}/{tier.billing_period}")
        print(f"  Features: {len(tier.features)}")
        print(f"  Trial: {tier.trial_days} days")
    
    print("\n2️⃣ Smart Discounts")
    print("-" * 40)
    
    # Test user profile
    user_profile = {
        'total_searches': 150,
        'referrals': 12,
        'trial_days_left': 1,
        'user_age_days': 45,
        'is_first_subscription': True
    }
    
    available = engine.calculate_available_discounts(user_profile)
    print(f"\nAvailable discounts: {len(available)}")
    for disc in available:
        print(f"• {disc.description}: {disc.percent}%")
    
    # Apply to tier
    calc = engine.apply_discounts('basic_monthly', user_profile)
    print(f"\n{format_discount_summary(calc)}")
    
    print("\n3️⃣ Contextual Upgrade Prompts")
    print("-" * 40)
    
    contexts = [
        (UpgradeContext.SEARCH_LIMIT, {'limit': 10}),
        (UpgradeContext.DEAL_MISSED, {'deal_value': 185}),
        (UpgradeContext.HIGH_VALUE_SHOWN, {'total_savings': 2450})
    ]
    
    for context, data in contexts:
        prompt = engine.get_upgrade_prompt(context, data)
        print(f"\n{prompt.headline}")
        print(f"{prompt.message}")
        print(f"CTA: [{prompt.primary_cta}]")
        print(f"Urgency: {prompt.urgency_level}/5")
    
    print("\n4️⃣ Tier Comparison")
    print("-" * 40)
    
    comparison = engine.compare_tiers(['basic_monthly', 'basic_annual'])
    for tier_data in comparison:
        print(f"\n{tier_data['name']}")
        print(f"  €{tier_data['price']}/{tier_data['billing']}")
        if tier_data['savings'] > 0:
            print(f"  Ahorro anual: €{tier_data['savings']:.2f}")
    
    print("\n" + "="*60)
    print("✅ Testing Complete!")
    print("="*60 + "\n")
