#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pricing Engine with Dynamic Discounts
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
    POWER_USER = "power_user"          # High usage
    REFERRAL_KING = "referral_king"    # Many referrals
    TRIAL_ENDING = "trial_ending"      # Trial ending soon
    SEASONAL = "seasonal"              # Limited time promo
    LOYALTY = "loyalty"                # Long-time user
    FIRST_TIME = "first_time"          # First premium purchase
    GROUP_DISCOUNT = "group_discount"  # Multiple users


class PromptContext(Enum):
    """Contexts for showing upgrade prompts"""
    SEARCH_LIMIT = "search_limit"
    WATCHLIST_FULL = "watchlist_full"
    DEAL_MISSED = "deal_missed"
    HIGH_VALUE = "high_value"
    POWER_USER = "power_user"
    TRIAL_ENDING = "trial_ending"


# Pricing configuration
PRICING_TIERS = {
    PricingTier.BASIC_MONTHLY: {
        "name": "Premium Monthly",
        "price": 9.99,
        "currency": "EUR",
        "billing_period": "monthly",
        "discount_vs_monthly": 0,
        "features": [
            "unlimited_searches",
            "unlimited_watchlist",
            "priority_notifications",
            "1year_history",
            "unlimited_groups",
            "export_data",
            "priority_support"
        ],
        "trial_days": 7,
        "popular": False
    },
    PricingTier.BASIC_ANNUAL: {
        "name": "Premium Annual",
        "price": 99.99,
        "currency": "EUR",
        "billing_period": "annual",
        "discount_vs_monthly": 17,
        "savings_yearly": 19.89,
        "features": [
            "unlimited_searches",
            "unlimited_watchlist",
            "priority_notifications",
            "1year_history",
            "unlimited_groups",
            "export_data",
            "priority_support",
            "10000_bonus_coins"
        ],
        "trial_days": 7,
        "popular": True,
        "badge": "AHORRA 17%"
    },
    PricingTier.PRO_MONTHLY: {
        "name": "Pro Monthly",
        "price": 14.99,
        "currency": "EUR",
        "billing_period": "monthly",
        "discount_vs_monthly": 0,
        "features": [
            "unlimited_searches",
            "unlimited_watchlist",
            "priority_notifications",
            "lifetime_history",
            "unlimited_groups",
            "export_data",
            "priority_support",
            "api_access",
            "team_groups",
            "advanced_filters",
            "price_alerts",
            "white_label"
        ],
        "trial_days": 14,
        "popular": False,
        "recommended_for": "power_users"
    },
    PricingTier.PRO_ANNUAL: {
        "name": "Pro Annual",
        "price": 149.99,
        "currency": "EUR",
        "billing_period": "annual",
        "discount_vs_monthly": 17,
        "savings_yearly": 29.89,
        "features": [
            "unlimited_searches",
            "unlimited_watchlist",
            "priority_notifications",
            "lifetime_history",
            "unlimited_groups",
            "export_data",
            "priority_support",
            "api_access",
            "team_groups",
            "advanced_filters",
            "price_alerts",
            "white_label",
            "20000_bonus_coins"
        ],
        "trial_days": 14,
        "popular": False
    }
}

# Regional pricing multipliers
REGIONAL_PRICING = {
    "ES": {"currency": "EUR", "multiplier": 1.0},
    "MX": {"currency": "MXN", "multiplier": 20.0},  # ~20 MXN per EUR
    "US": {"currency": "USD", "multiplier": 1.1},
    "LATAM": {"currency": "USD", "multiplier": 0.8},  # Discounted for LATAM
    "UK": {"currency": "GBP", "multiplier": 0.9},
    "DEFAULT": {"currency": "EUR", "multiplier": 1.0}
}

# Discount rules
DISCOUNT_RULES = {
    DiscountType.POWER_USER: {
        "condition": lambda profile: profile.get('total_searches', 0) > 100,
        "discount_percent": 10,
        "description": "Descuento para usuarios activos",
        "stackable": True
    },
    DiscountType.REFERRAL_KING: {
        "condition": lambda profile: profile.get('referrals', 0) > 10,
        "discount_percent": 10,
        "description": "Descuento por referidos",
        "stackable": True
    },
    DiscountType.TRIAL_ENDING: {
        "condition": lambda profile: profile.get('trial_days_left', 999) <= 1,
        "discount_percent": 20,
        "description": "Oferta especial fin de trial",
        "stackable": True
    },
    DiscountType.SEASONAL: {
        "condition": lambda profile: profile.get('special_promo_active', False),
        "discount_percent": 15,
        "description": "Promoción por tiempo limitado",
        "stackable": False  # Exclusive
    },
    DiscountType.LOYALTY: {
        "condition": lambda profile: profile.get('user_age_days', 0) > 90,
        "discount_percent": 5,
        "description": "Descuento por antigüedad",
        "stackable": True
    },
    DiscountType.FIRST_TIME: {
        "condition": lambda profile: not profile.get('has_paid_before', False),
        "discount_percent": 15,
        "description": "Oferta de primera compra",
        "stackable": False
    }
}

# Max discount limits
MAX_DISCOUNT_PERCENT = 40
MAX_DISCOUNT_STACK = 3


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class PriceQuote:
    """Price quote for a tier with discounts applied"""
    tier: str  # PricingTier value
    base_price: float
    currency: str
    discounts_applied: List[str]  # DiscountType values
    total_discount_percent: float
    final_price: float
    savings: float
    
    @property
    def display_price(self) -> str:
        """Formatted price for display"""
        symbol = {
            "EUR": "€",
            "USD": "$",
            "GBP": "£",
            "MXN": "$"
        }.get(self.currency, "")
        
        if self.total_discount_percent > 0:
            return f"~~{symbol}{self.base_price:.2f}~~ {symbol}{self.final_price:.2f}"
        return f"{symbol}{self.final_price:.2f}"


@dataclass
class UpgradePrompt:
    """Contextual upgrade prompt"""
    context: str  # PromptContext value
    headline: str
    message: str
    cta: str
    urgency_level: int  # 1-5, higher = more urgent
    recommended_tier: str  # PricingTier value
    
    def to_dict(self) -> Dict:
        return asdict(self)


# ============================================================================
# PRICING ENGINE
# ============================================================================

class PricingEngine:
    """
    Dynamic pricing engine with smart discounts.
    
    Features:
    - Multiple pricing tiers
    - Dynamic discount calculation
    - Regional pricing
    - Contextual upgrade prompts
    - Discount stacking with limits
    """
    
    def __init__(self, data_dir: str = "."):
        self.data_dir = Path(data_dir)
        self.config_file = self.data_dir / "pricing_config.json"
        
        # Load pricing config
        self._load_config()
        
        print("✅ PricingEngine initialized")
    
    # ========================================================================
    # CONFIG MANAGEMENT
    # ========================================================================
    
    def _load_config(self):
        """Load pricing configuration"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # Could override PRICING_TIERS here if needed
                    print("✅ Pricing config loaded")
            except Exception as e:
                print(f"⚠️ Error loading config: {e}")
    
    # ========================================================================
    # DISCOUNT CALCULATION
    # ========================================================================
    
    def calculate_discounts(self, user_profile: Dict) -> Tuple[List[DiscountType], float]:
        """
        Calculate applicable discounts for user.
        
        Args:
            user_profile: Dict with user data for discount conditions
        
        Returns:
            (applicable_discounts, total_discount_percent)
        """
        applicable = []
        
        # Check each discount rule
        for discount_type, rule in DISCOUNT_RULES.items():
            if rule['condition'](user_profile):
                applicable.append(discount_type)
        
        # Apply stacking rules
        stackable = [d for d in applicable if DISCOUNT_RULES[d]['stackable']]
        exclusive = [d for d in applicable if not DISCOUNT_RULES[d]['stackable']]
        
        # If exclusive discount available, use highest one only
        if exclusive:
            best_exclusive = max(exclusive, key=lambda d: DISCOUNT_RULES[d]['discount_percent'])
            total_discount = DISCOUNT_RULES[best_exclusive]['discount_percent']
            final_discounts = [best_exclusive]
        else:
            # Stack discounts up to limit
            sorted_stackable = sorted(
                stackable,
                key=lambda d: DISCOUNT_RULES[d]['discount_percent'],
                reverse=True
            )
            final_discounts = sorted_stackable[:MAX_DISCOUNT_STACK]
            total_discount = sum(DISCOUNT_RULES[d]['discount_percent'] for d in final_discounts)
        
        # Apply max discount cap
        total_discount = min(total_discount, MAX_DISCOUNT_PERCENT)
        
        return final_discounts, total_discount
    
    # ========================================================================
    # PRICE QUOTES
    # ========================================================================
    
    def get_price_quote(
        self,
        tier: PricingTier,
        user_profile: Dict,
        region: str = "ES"
    ) -> PriceQuote:
        """
        Get price quote with discounts for a tier.
        
        Args:
            tier: Pricing tier
            user_profile: User data for discount calculation
            region: Region code for regional pricing
        
        Returns:
            PriceQuote with final price
        """
        tier_config = PRICING_TIERS[tier]
        base_price = tier_config['price']
        
        # Apply regional pricing
        regional = REGIONAL_PRICING.get(region, REGIONAL_PRICING['DEFAULT'])
        base_price = base_price * regional['multiplier']
        currency = regional['currency']
        
        # Calculate discounts
        discounts, discount_percent = self.calculate_discounts(user_profile)
        
        # Calculate final price
        discount_amount = base_price * (discount_percent / 100)
        final_price = base_price - discount_amount
        
        return PriceQuote(
            tier=tier.value,
            base_price=base_price,
            currency=currency,
            discounts_applied=[d.value for d in discounts],
            total_discount_percent=discount_percent,
            final_price=final_price,
            savings=discount_amount
        )
    
    def get_all_prices(
        self,
        user_profile: Dict,
        region: str = "ES"
    ) -> Dict[str, PriceQuote]:
        """
        Get price quotes for all tiers.
        
        Returns:
            Dict mapping tier value to PriceQuote
        """
        return {
            tier.value: self.get_price_quote(tier, user_profile, region)
            for tier in PricingTier
        }
    
    # ========================================================================
    # UPGRADE PROMPTS
    # ========================================================================
    
    def get_upgrade_prompt(
        self,
        context: PromptContext,
        user_profile: Dict,
        region: str = "ES"
    ) -> UpgradePrompt:
        """
        Get contextual upgrade prompt.
        
        Args:
            context: Context for showing prompt
            user_profile: User data
            region: Region code
        
        Returns:
            UpgradePrompt with messaging
        """
        # Get best price
        prices = self.get_all_prices(user_profile, region)
        basic_monthly = prices[PricingTier.BASIC_MONTHLY.value]
        
        # Context-specific prompts
        if context == PromptContext.SEARCH_LIMIT:
            return UpgradePrompt(
                context=context.value,
                headline="🚫 Límite de Búsquedas Alcanzado",
                message=f"Has usado tus 10 búsquedas diarias. Upgrade a Premium para búsquedas ilimitadas por solo {basic_monthly.display_price}/mes.",
                cta="Desbloquear Búsquedas Ilimitadas",
                urgency_level=4,
                recommended_tier=PricingTier.BASIC_MONTHLY.value
            )
        
        elif context == PromptContext.WATCHLIST_FULL:
            return UpgradePrompt(
                context=context.value,
                headline="⭐ Watchlist Lleno",
                message=f"Has usado tus 3 slots. Premium = slots ilimitados + notificaciones priority por {basic_monthly.display_price}/mes.",
                cta="Expandir Watchlist",
                urgency_level=3,
                recommended_tier=PricingTier.BASIC_MONTHLY.value
            )
        
        elif context == PromptContext.DEAL_MISSED:
            missed_value = user_profile.get('deal_value', 150)
            return UpgradePrompt(
                context=context.value,
                headline="😔 Perdiste un Chollo de €{}".format(missed_value),
                message=f"Por límites de usuario free. Premium = notificaciones instantáneas, 0 chollos perdidos. Solo {basic_monthly.display_price}/mes.",
                cta="No Perder Más Chollos",
                urgency_level=5,
                recommended_tier=PricingTier.BASIC_MONTHLY.value
            )
        
        elif context == PromptContext.HIGH_VALUE:
            total_savings = user_profile.get('total_savings', 500)
            return UpgradePrompt(
                context=context.value,
                headline=f"💰 Has Visto €{total_savings} en Chollos",
                message=f"Usuarios premium ahorran 65% más. Desbloquea todo por {basic_monthly.display_price}/mes.",
                cta="Maximizar Mi Ahorro",
                urgency_level=3,
                recommended_tier=PricingTier.BASIC_MONTHLY.value
            )
        
        elif context == PromptContext.POWER_USER:
            searches = user_profile.get('total_searches', 100)
            return UpgradePrompt(
                context=context.value,
                headline=f"🔥 {searches}+ Búsquedas Realizadas",
                message=f"Eres un power user. Upgrade a Pro para API access, filtros avanzados y más.",
                cta="Ver Premium Pro",
                urgency_level=2,
                recommended_tier=PricingTier.PRO_MONTHLY.value
            )
        
        elif context == PromptContext.TRIAL_ENDING:
            days_left = user_profile.get('trial_days_left', 1)
            return UpgradePrompt(
                context=context.value,
                headline=f"⏰ Trial Expira en {days_left} Día{'s' if days_left > 1 else ''}",
                message=f"No pierdas acceso a Premium. {basic_monthly.total_discount_percent:.0f}% OFF si actualizas ahora: {basic_monthly.display_price}/mes.",
                cta="Continuar con Premium",
                urgency_level=5,
                recommended_tier=PricingTier.BASIC_ANNUAL.value  # Push annual
            )
        
        # Default
        return UpgradePrompt(
            context=context.value,
            headline="✨ Desbloquea Premium",
            message=f"Acceso completo a todas las features por {basic_monthly.display_price}/mes.",
            cta="Probar Premium Gratis",
            urgency_level=1,
            recommended_tier=PricingTier.BASIC_MONTHLY.value
        )
    
    # ========================================================================
    # TIER RECOMMENDATIONS
    # ========================================================================
    
    def recommend_tier(self, user_profile: Dict) -> PricingTier:
        """
        Recommend best tier for user based on profile.
        
        Args:
            user_profile: User data
        
        Returns:
            Recommended PricingTier
        """
        # Power users -> Pro
        if user_profile.get('total_searches', 0) > 200:
            return PricingTier.PRO_MONTHLY
        
        # High referrals -> Pro
        if user_profile.get('referrals', 0) > 20:
            return PricingTier.PRO_MONTHLY
        
        # Long-time users -> Annual
        if user_profile.get('user_age_days', 0) > 60:
            return PricingTier.BASIC_ANNUAL
        
        # Default -> Basic Monthly
        return PricingTier.BASIC_MONTHLY


# ============================================================================
# FORMATTING HELPERS
# ============================================================================

def format_pricing_table(prices: Dict[str, PriceQuote]) -> str:
    """
    Format pricing table for Telegram.
    
    Args:
        prices: Dict from get_all_prices()
    
    Returns:
        Formatted pricing table
    """
    basic_monthly = prices[PricingTier.BASIC_MONTHLY.value]
    basic_annual = prices[PricingTier.BASIC_ANNUAL.value]
    
    message = "💳 Planes Premium\n\n"
    
    # Basic Monthly
    message += f"🔹 {PRICING_TIERS[PricingTier.BASIC_MONTHLY]['name']}\n"
    message += f"   {basic_monthly.display_price}/mes\n"
    if basic_monthly.total_discount_percent > 0:
        message += f"   🎉 {basic_monthly.total_discount_percent:.0f}% OFF aplicado\n"
    message += "\n"
    
    # Basic Annual (Popular)
    message += f"💎 {PRICING_TIERS[PricingTier.BASIC_ANNUAL]['name']} 🔥 POPULAR\n"
    message += f"   {basic_annual.display_price}/año\n"
    message += f"   🏆 Ahorra 17% vs mensual\n"
    if basic_annual.total_discount_percent > 0:
        message += f"   🎉 {basic_annual.total_discount_percent:.0f}% OFF adicional\n"
    message += "\n"
    
    message += "─" * 30 + "\n\n"
    
    # Features
    message += "✅ Todas las Features Premium:\n"
    message += "• Búsquedas ilimitadas\n"
    message += "• Watchlist sin límites\n"
    message += "• Notificaciones priority\n"
    message += "• Historial 1 año\n"
    message += "• Grupos ilimitados\n"
    message += "• Export datos\n"
    message += "• Soporte 24/7\n"
    message += "\n"
    
    message += "🎁 Prueba GRATIS 7 días, sin tarjeta\n"
    
    return message


def format_upgrade_prompt(prompt: UpgradePrompt, price_quote: PriceQuote) -> str:
    """
    Format upgrade prompt for Telegram.
    
    Args:
        prompt: UpgradePrompt
        price_quote: PriceQuote for recommended tier
    
    Returns:
        Formatted message
    """
    urgency_emoji = ["👉", "👆", "❗", "‼️", "🔥"][min(prompt.urgency_level - 1, 4)]
    
    message = f"{urgency_emoji} {prompt.headline}\n\n"
    message += f"{prompt.message}\n\n"
    
    if price_quote.total_discount_percent > 0:
        message += f"🎉 OFERTA ESPECIAL: {price_quote.total_discount_percent:.0f}% OFF\n"
        message += f"   {price_quote.display_price}\n\n"
    
    message += f"[{prompt.cta}]"
    
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
    
    # Test user profiles
    regular_user = {
        'total_searches': 25,
        'referrals': 2,
        'user_age_days': 15,
        'has_paid_before': False
    }
    
    power_user = {
        'total_searches': 150,
        'referrals': 12,
        'user_age_days': 120,
        'has_paid_before': False
    }
    
    trial_ending = {
        'total_searches': 45,
        'referrals': 3,
        'trial_days_left': 1,
        'has_paid_before': False
    }
    
    print("1️⃣ Regular User Pricing")
    print("-" * 40)
    prices = engine.get_all_prices(regular_user)
    print(format_pricing_table(prices))
    
    print("\n2️⃣ Power User Discounts")
    print("-" * 40)
    discounts, total = engine.calculate_discounts(power_user)
    print(f"Applicable discounts: {[d.value for d in discounts]}")
    print(f"Total discount: {total}%")
    
    prices_power = engine.get_all_prices(power_user)
    basic = prices_power[PricingTier.BASIC_MONTHLY.value]
    print(f"\nBasic Monthly: {basic.display_price}")
    print(f"Savings: €{basic.savings:.2f}")
    
    print("\n3️⃣ Trial Ending Prompt")
    print("-" * 40)
    prompt = engine.get_upgrade_prompt(PromptContext.TRIAL_ENDING, trial_ending)
    price = engine.get_price_quote(PricingTier.BASIC_ANNUAL, trial_ending)
    print(format_upgrade_prompt(prompt, price))
    
    print("\n4️⃣ Tier Recommendation")
    print("-" * 40)
    rec_regular = engine.recommend_tier(regular_user)
    rec_power = engine.recommend_tier(power_user)
    print(f"Regular user: {rec_regular.value}")
    print(f"Power user: {rec_power.value}")
    
    print("\n" + "="*60)
    print("✅ Testing Complete!")
    print("="*60 + "\n")
