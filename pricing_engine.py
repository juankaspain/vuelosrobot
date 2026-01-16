#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pricing Engine with Dynamic Discounts
IT6 - DAY 4/5

Features:
- Multiple pricing tiers (Basic/Pro, Monthly/Annual)
- Regional pricing (ES/MX/US/LATAM/UK)
- Smart discounts (up to 40% off)
- Contextual upgrade prompts
- A/B testing of offers
- Limited-time promotions

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
    POWER_USER = "power_user"
    REFERRAL_KING = "referral_king"
    TRIAL_ENDING = "trial_ending"
    SEASONAL = "seasonal"
    LOYALTY = "loyalty"
    FIRST_TIME = "first_time"
    BUNDLE = "bundle"


class UpgradePromptContext(Enum):
    """Context for showing upgrade prompts"""
    SEARCH_LIMIT = "search_limit"
    WATCHLIST_FULL = "watchlist_full"
    DEAL_MISSED = "deal_missed"
    HIGH_VALUE = "high_value"
    TRIAL_EXPIRING = "trial_expiring"
    GENERAL = "general"


# Default pricing configuration
DEFAULT_PRICING = {
    PricingTier.BASIC_MONTHLY: {
        "name": "Premium Monthly",
        "price": 9.99,
        "currency": "EUR",
        "billing_period": "monthly",
        "features": [
            "unlimited_searches",
            "unlimited_watchlist",
            "priority_notifications",
            "1year_history",
            "unlimited_groups",
            "export_data",
            "priority_support"
        ]
    },
    PricingTier.BASIC_ANNUAL: {
        "name": "Premium Annual",
        "price": 99.99,
        "currency": "EUR",
        "billing_period": "annual",
        "discount_vs_monthly": 17,
        "savings": 20.0,
        "popular": True
    },
    PricingTier.PRO_MONTHLY: {
        "name": "Pro Monthly",
        "price": 14.99,
        "currency": "EUR",
        "billing_period": "monthly",
        "features_extra": [
            "api_access",
            "team_groups",
            "advanced_filters",
            "white_label"
        ]
    },
    PricingTier.PRO_ANNUAL: {
        "name": "Pro Annual",
        "price": 149.99,
        "currency": "EUR",
        "billing_period": "annual",
        "discount_vs_monthly": 17
    }
}

# Regional pricing multipliers
REGIONAL_PRICING = {
    "ES": {"currency": "EUR", "multiplier": 1.0},
    "PT": {"currency": "EUR", "multiplier": 0.9},
    "FR": {"currency": "EUR", "multiplier": 1.0},
    "DE": {"currency": "EUR", "multiplier": 1.0},
    "IT": {"currency": "EUR", "multiplier": 1.0},
    "UK": {"currency": "GBP", "multiplier": 0.85},
    "US": {"currency": "USD", "multiplier": 1.1},
    "MX": {"currency": "MXN", "multiplier": 20.0},
    "AR": {"currency": "USD", "multiplier": 0.7},
    "BR": {"currency": "USD", "multiplier": 0.8},
    "CL": {"currency": "USD", "multiplier": 0.8},
    "CO": {"currency": "USD", "multiplier": 0.75},
}

# Upgrade prompts by context
UPGRADE_PROMPTS = {
    UpgradePromptContext.SEARCH_LIMIT: {
        "headline": "🚫 Límite de Búsquedas Alcanzado",
        "message": "Has usado tus 10 búsquedas diarias. Actualiza a Premium para búsquedas ilimitadas.",
        "cta": "Desbloquear Búsquedas Ilimitadas",
        "urgency": "high"
    },
    UpgradePromptContext.WATCHLIST_FULL: {
        "headline": "⭐ Watchlist Completo",
        "message": "Has usado tus 3 slots de watchlist. Premium = slots ilimitados para no perder chollos.",
        "cta": "Ampliar Watchlist",
        "urgency": "medium"
    },
    UpgradePromptContext.DEAL_MISSED: {
        "headline": "😔 Perdiste un Chollo",
        "message": "Este chollo de €{value} desapareció mientras esperabas. Premium = notificaciones instantáneas.",
        "cta": "No Perder Más Chollos",
        "urgency": "high"
    },
    UpgradePromptContext.HIGH_VALUE: {
        "headline": "💰 Has Visto €{value} en Chollos",
        "message": "Desbloquea todo el potencial. Usuarios premium ahorran 65% más por solo €9.99/mes.",
        "cta": "Maximizar Mi Ahorro",
        "urgency": "medium"
    },
    UpgradePromptContext.TRIAL_EXPIRING: {
        "headline": "⏰ Trial Expira en {days} Días",
        "message": "No pierdas acceso a features premium. Actualiza ahora con {discount}% OFF.",
        "cta": "Continuar con Premium",
        "urgency": "high"
    },
    UpgradePromptContext.GENERAL: {
        "headline": "🚀 Desbloquea Todo el Potencial",
        "message": "Búsquedas ilimitadas, watchlist sin límites, notificaciones priority y mucho más.",
        "cta": "Ver Planes Premium",
        "urgency": "low"
    }
}


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class PricingOffer:
    """A pricing offer with discounts applied"""
    tier: str  # PricingTier
    base_price: float
    final_price: float
    currency: str
    discount_percent: float
    discounts_applied: List[str]  # List of DiscountType
    savings: float
    billing_period: str
    valid_until: Optional[datetime] = None
    
    @property
    def is_limited_time(self) -> bool:
        """Check if offer is limited time"""
        return self.valid_until is not None
    
    @property
    def time_remaining(self) -> Optional[timedelta]:
        """Time remaining for limited offer"""
        if not self.valid_until:
            return None
        return self.valid_until - datetime.now()
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        if self.valid_until:
            data['valid_until'] = self.valid_until.isoformat()
        return data


@dataclass
class UpgradePrompt:
    """Contextual upgrade prompt"""
    context: str  # UpgradePromptContext
    headline: str
    message: str
    cta: str
    urgency: str  # "low", "medium", "high"
    offer: PricingOffer
    timestamp: datetime
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['offer'] = self.offer.to_dict()
        data['timestamp'] = self.timestamp.isoformat()
        return data


# ============================================================================
# PRICING ENGINE
# ============================================================================

class PricingEngine:
    """
    Manages pricing, discounts, and upgrade prompts.
    
    Features:
    - Multiple pricing tiers
    - Regional pricing
    - Smart discounts (up to 40%)
    - Contextual upgrade prompts
    - Limited-time offers
    """
    
    def __init__(self, data_dir: str = ".", config_file: str = "pricing_config.json"):
        self.data_dir = Path(data_dir)
        self.config_file = self.data_dir / config_file
        
        # Load pricing config
        self.pricing_config = self._load_config()
        
        # Active promotions
        self.active_promotions: Dict[str, Dict] = {}
        
        print("✅ PricingEngine initialized")
    
    # ========================================================================
    # CONFIGURATION
    # ========================================================================
    
    def _load_config(self) -> Dict:
        """Load pricing configuration from file"""
        if not self.config_file.exists():
            print("⚠️ No pricing config found, using defaults")
            return {"tiers": DEFAULT_PRICING}
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Error loading pricing config: {e}")
            return {"tiers": DEFAULT_PRICING}
    
    # ========================================================================
    # PRICING CALCULATION
    # ========================================================================
    
    def get_base_price(self, tier: PricingTier, region: str = "ES") -> Tuple[float, str]:
        """
        Get base price for tier and region.
        
        Returns:
            (price, currency)
        """
        # Get base price from config
        tier_config = self.pricing_config.get("tiers", {}).get(tier.value, DEFAULT_PRICING[tier])
        base_price = tier_config.get("price", 9.99)
        
        # Apply regional pricing
        if region in REGIONAL_PRICING:
            regional = REGIONAL_PRICING[region]
            price = base_price * regional["multiplier"]
            currency = regional["currency"]
        else:
            price = base_price
            currency = "EUR"
        
        return price, currency
    
    def calculate_discount(self, user_profile: Dict) -> Tuple[float, List[str]]:
        """
        Calculate total discount for user.
        
        Args:
            user_profile: Dict with user data
                - total_searches: int
                - referrals: int
                - trial_days_left: int
                - user_age_days: int
                - is_first_purchase: bool
        
        Returns:
            (discount_percent, discounts_applied)
        """
        total_discount = 0
        discounts = []
        
        # Power user discount (10%)
        if user_profile.get('total_searches', 0) >= 100:
            total_discount += 10
            discounts.append(DiscountType.POWER_USER.value)
        
        # Referral king discount (10%)
        if user_profile.get('referrals', 0) >= 10:
            total_discount += 10
            discounts.append(DiscountType.REFERRAL_KING.value)
        
        # Trial ending discount (20%)
        trial_days = user_profile.get('trial_days_left', 999)
        if 0 <= trial_days <= 1:
            total_discount += 20
            discounts.append(DiscountType.TRIAL_ENDING.value)
        
        # Loyalty discount (5%)
        if user_profile.get('user_age_days', 0) >= 90:
            total_discount += 5
            discounts.append(DiscountType.LOYALTY.value)
        
        # First time discount (15%)
        if user_profile.get('is_first_purchase', False):
            total_discount += 15
            discounts.append(DiscountType.FIRST_TIME.value)
        
        # Check for active seasonal promotions
        if self.has_active_promotion():
            promo = self.get_active_promotion()
            if promo:
                total_discount += promo.get('discount_percent', 0)
                discounts.append(DiscountType.SEASONAL.value)
        
        # Cap at 40%
        total_discount = min(40, total_discount)
        
        return total_discount, discounts
    
    def create_offer(self, tier: PricingTier, user_profile: Dict, 
                     region: str = "ES") -> PricingOffer:
        """
        Create a pricing offer for user.
        
        Args:
            tier: Pricing tier
            user_profile: User data for discount calculation
            region: User's region code
        
        Returns:
            PricingOffer with discounts applied
        """
        # Get base price
        base_price, currency = self.get_base_price(tier, region)
        
        # Calculate discount
        discount_percent, discounts_applied = self.calculate_discount(user_profile)
        
        # Apply discount
        final_price = base_price * (1 - discount_percent / 100)
        savings = base_price - final_price
        
        # Get billing period
        tier_config = self.pricing_config.get("tiers", {}).get(tier.value, DEFAULT_PRICING[tier])
        billing_period = tier_config.get("billing_period", "monthly")
        
        # Check if limited time (trial ending or seasonal promo)
        valid_until = None
        if DiscountType.TRIAL_ENDING.value in discounts_applied:
            # Trial ending offers valid for 48h
            valid_until = datetime.now() + timedelta(hours=48)
        elif DiscountType.SEASONAL.value in discounts_applied:
            promo = self.get_active_promotion()
            if promo and 'valid_until' in promo:
                valid_until = datetime.fromisoformat(promo['valid_until'])
        
        return PricingOffer(
            tier=tier.value,
            base_price=base_price,
            final_price=final_price,
            currency=currency,
            discount_percent=discount_percent,
            discounts_applied=discounts_applied,
            savings=savings,
            billing_period=billing_period,
            valid_until=valid_until
        )
    
    def get_all_offers(self, user_profile: Dict, region: str = "ES") -> Dict[str, PricingOffer]:
        """
        Get all available offers for user.
        
        Returns:
            Dict mapping tier to offer
        """
        return {
            tier.value: self.create_offer(tier, user_profile, region)
            for tier in PricingTier
        }
    
    # ========================================================================
    # UPGRADE PROMPTS
    # ========================================================================
    
    def create_upgrade_prompt(self, context: UpgradePromptContext, 
                             user_profile: Dict, context_data: Dict = None) -> UpgradePrompt:
        """
        Create contextual upgrade prompt.
        
        Args:
            context: Context for the prompt
            user_profile: User data
            context_data: Additional context (e.g., deal_value, days_left)
        
        Returns:
            UpgradePrompt
        """
        # Get base prompt
        prompt_template = UPGRADE_PROMPTS[context]
        
        # Get best offer (usually basic_monthly or annual if high discount)
        offers = self.get_all_offers(user_profile)
        
        # Choose offer based on context
        if context == UpgradePromptContext.TRIAL_EXPIRING:
            # Prefer annual with discount
            offer = offers[PricingTier.BASIC_ANNUAL.value]
        else:
            # Default to monthly
            offer = offers[PricingTier.BASIC_MONTHLY.value]
        
        # Format message with context data
        headline = prompt_template["headline"]
        message = prompt_template["message"]
        
        if context_data:
            headline = headline.format(**context_data)
            message = message.format(**context_data)
        
        # Add discount info if significant
        if offer.discount_percent >= 15:
            message += f"\n\n🎉 OFERTA: {offer.discount_percent:.0f}% OFF"
            if offer.is_limited_time:
                hours_left = offer.time_remaining.total_seconds() / 3600
                message += f" (válido {hours_left:.0f}h)"
        
        return UpgradePrompt(
            context=context.value,
            headline=headline,
            message=message,
            cta=prompt_template["cta"],
            urgency=prompt_template["urgency"],
            offer=offer,
            timestamp=datetime.now()
        )
    
    # ========================================================================
    # PROMOTIONS
    # ========================================================================
    
    def create_promotion(self, name: str, discount_percent: float, 
                        valid_days: int = 7) -> Dict:
        """
        Create a limited-time promotion.
        
        Args:
            name: Promotion name
            discount_percent: Discount percentage
            valid_days: Days promotion is valid
        
        Returns:
            Promotion dict
        """
        promo = {
            "name": name,
            "discount_percent": discount_percent,
            "created": datetime.now().isoformat(),
            "valid_until": (datetime.now() + timedelta(days=valid_days)).isoformat(),
            "active": True
        }
        
        self.active_promotions[name] = promo
        return promo
    
    def has_active_promotion(self) -> bool:
        """Check if there's an active promotion"""
        for promo in self.active_promotions.values():
            if promo.get('active'):
                valid_until = datetime.fromisoformat(promo['valid_until'])
                if datetime.now() < valid_until:
                    return True
        return False
    
    def get_active_promotion(self) -> Optional[Dict]:
        """Get current active promotion if any"""
        for promo in self.active_promotions.values():
            if promo.get('active'):
                valid_until = datetime.fromisoformat(promo['valid_until'])
                if datetime.now() < valid_until:
                    return promo
        return None
    
    # ========================================================================
    # HELPERS
    # ========================================================================
    
    def format_price(self, price: float, currency: str) -> str:
        """Format price with currency symbol"""
        symbols = {
            "EUR": "€",
            "USD": "$",
            "GBP": "£",
            "MXN": "$"
        }
        symbol = symbols.get(currency, currency)
        
        if currency in ["EUR", "GBP"]:
            return f"{symbol}{price:.2f}"
        else:
            return f"{symbol}{price:.2f}"
    
    def compare_plans(self, tier1: PricingTier, tier2: PricingTier, 
                     user_profile: Dict) -> Dict:
        """
        Compare two pricing plans.
        
        Returns:
            Comparison dict
        """
        offer1 = self.create_offer(tier1, user_profile)
        offer2 = self.create_offer(tier2, user_profile)
        
        return {
            "plan1": {
                "name": tier1.value,
                "price": offer1.final_price,
                "currency": offer1.currency,
                "billing": offer1.billing_period
            },
            "plan2": {
                "name": tier2.value,
                "price": offer2.final_price,
                "currency": offer2.currency,
                "billing": offer2.billing_period
            },
            "savings": abs(offer1.final_price - offer2.final_price),
            "better_value": tier1.value if offer1.final_price < offer2.final_price else tier2.value
        }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def format_pricing_offer(offer: PricingOffer) -> str:
    """
    Format pricing offer for display.
    
    Args:
        offer: PricingOffer object
    
    Returns:
        Formatted string
    """
    price_str = f"{offer.currency} {offer.final_price:.2f}"
    
    result = f"""💳 {offer.tier.replace('_', ' ').title()}

💰 Precio: {price_str}/{offer.billing_period}
"""
    
    if offer.discount_percent > 0:
        result += f"🎉 Descuento: {offer.discount_percent:.0f}% OFF\n"
        result += f"💸 Ahorras: {offer.currency} {offer.savings:.2f}\n"
        
        if offer.discounts_applied:
            result += f"\n✅ Descuentos aplicados:\n"
            for discount in offer.discounts_applied:
                result += f"  • {discount.replace('_', ' ').title()}\n"
    
    if offer.is_limited_time:
        hours_left = offer.time_remaining.total_seconds() / 3600
        result += f"\n⏰ Oferta válida {hours_left:.0f}h\n"
    
    return result


def format_upgrade_prompt(prompt: UpgradePrompt) -> str:
    """
    Format upgrade prompt for display.
    
    Args:
        prompt: UpgradePrompt object
    
    Returns:
        Formatted string
    """
    urgency_emoji = {
        "high": "🔥",
        "medium": "⭐",
        "low": "💡"
    }
    
    emoji = urgency_emoji.get(prompt.urgency, "💡")
    
    return f"""{emoji} {prompt.headline}

{prompt.message}

{format_pricing_offer(prompt.offer)}

[{prompt.cta}]
"""


# ============================================================================
# MAIN (TESTING)
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("💳 TESTING: Pricing Engine")
    print("="*60 + "\n")
    
    # Initialize engine
    engine = PricingEngine()
    
    print("1️⃣ Basic Pricing")
    print("-" * 40)
    
    basic_profile = {
        'total_searches': 25,
        'referrals': 2,
        'trial_days_left': 999,
        'user_age_days': 15,
        'is_first_purchase': True
    }
    
    offer = engine.create_offer(PricingTier.BASIC_MONTHLY, basic_profile)
    print(format_pricing_offer(offer))
    
    print("\n2️⃣ Power User Pricing")
    print("-" * 40)
    
    power_profile = {
        'total_searches': 150,
        'referrals': 12,
        'trial_days_left': 1,
        'user_age_days': 120,
        'is_first_purchase': False
    }
    
    offer = engine.create_offer(PricingTier.BASIC_ANNUAL, power_profile)
    print(format_pricing_offer(offer))
    
    print("\n3️⃣ All Offers Comparison")
    print("-" * 40)
    
    all_offers = engine.get_all_offers(power_profile)
    for tier, offer in all_offers.items():
        print(f"\n{tier}:")
        print(f"  Price: {offer.currency} {offer.final_price:.2f}")
        print(f"  Discount: {offer.discount_percent:.0f}%")
    
    print("\n4️⃣ Upgrade Prompts")
    print("-" * 40)
    
    # Search limit prompt
    prompt = engine.create_upgrade_prompt(
        UpgradePromptContext.SEARCH_LIMIT,
        basic_profile
    )
    print(format_upgrade_prompt(prompt))
    
    # Deal missed prompt
    print("\n" + "-" * 40 + "\n")
    prompt = engine.create_upgrade_prompt(
        UpgradePromptContext.DEAL_MISSED,
        basic_profile,
        context_data={'value': 250}
    )
    print(format_upgrade_prompt(prompt))
    
    print("\n5️⃣ Limited-Time Promotion")
    print("-" * 40)
    
    # Create seasonal promo
    promo = engine.create_promotion("Winter Sale", 25, valid_days=3)
    print(f"\nCreated: {promo['name']}")
    print(f"Discount: {promo['discount_percent']}%")
    print(f"Valid until: {promo['valid_until']}")
    
    # Offer with promo
    offer = engine.create_offer(PricingTier.BASIC_MONTHLY, basic_profile)
    print(f"\nWith promo:")
    print(format_pricing_offer(offer))
    
    print("\n6️⃣ Regional Pricing")
    print("-" * 40)
    
    regions = ["ES", "US", "MX", "UK"]
    for region in regions:
        price, currency = engine.get_base_price(PricingTier.BASIC_MONTHLY, region)
        print(f"{region}: {currency} {price:.2f}")
    
    print("\n" + "="*60)
    print("✅ Testing Complete!")
    print("="*60 + "\n")
