#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flexible Pricing Engine with Smart Discounts
IT6 - DAY 4/5

Features:
- Multiple pricing tiers (Basic/Pro, Monthly/Annual)
- Dynamic discount calculation (up to 40%)
- Regional pricing
- Smart upgrade prompts (contextual)
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
# ENUMS
# ============================================================================

class PlanTier(Enum):
    """Premium plan tiers"""
    BASIC_MONTHLY = "basic_monthly"
    BASIC_ANNUAL = "basic_annual"
    PRO_MONTHLY = "pro_monthly"
    PRO_ANNUAL = "pro_annual"


class DiscountType(Enum):
    """Types of discounts available"""
    POWER_USER = "power_user"
    REFERRAL_KING = "referral_king"
    TRIAL_ENDING = "trial_ending"
    SEASONAL = "seasonal"
    LOYALTY = "loyalty"
    FIRST_TIME = "first_time"


class UpgradeContext(Enum):
    """Context for upgrade prompts"""
    SEARCH_LIMIT = "search_limit"
    WATCHLIST_FULL = "watchlist_full"
    DEAL_MISSED = "deal_missed"
    HIGH_VALUE = "high_value"
    TRIAL_EXPIRING = "trial_expiring"
    GENERAL = "general"


# ============================================================================
# CONSTANTS
# ============================================================================

# Base pricing (EUR)
BASE_PRICING = {
    PlanTier.BASIC_MONTHLY: {
        "price": 9.99,
        "name": "Premium Monthly",
        "billing": "monthly",
        "period_months": 1,
        "trial_days": 7
    },
    PlanTier.BASIC_ANNUAL: {
        "price": 99.99,
        "name": "Premium Annual",
        "billing": "annual",
        "period_months": 12,
        "trial_days": 7,
        "discount_vs_monthly": 17
    },
    PlanTier.PRO_MONTHLY: {
        "price": 14.99,
        "name": "Pro Monthly",
        "billing": "monthly",
        "period_months": 1,
        "trial_days": 14
    },
    PlanTier.PRO_ANNUAL: {
        "price": 149.99,
        "name": "Pro Annual",
        "billing": "annual",
        "period_months": 12,
        "trial_days": 14,
        "discount_vs_monthly": 17
    }
}

# Regional pricing multipliers
REGIONAL_MULTIPLIERS = {
    "ES": {"multiplier": 1.0, "currency": "EUR"},
    "FR": {"multiplier": 1.0, "currency": "EUR"},
    "DE": {"multiplier": 1.0, "currency": "EUR"},
    "IT": {"multiplier": 1.0, "currency": "EUR"},
    "UK": {"multiplier": 0.9, "currency": "GBP"},
    "US": {"multiplier": 1.1, "currency": "USD"},
    "MX": {"multiplier": 20.0, "currency": "MXN"},
    "AR": {"multiplier": 0.8, "currency": "USD"},
    "CL": {"multiplier": 0.8, "currency": "USD"},
    "CO": {"multiplier": 0.8, "currency": "USD"},
    "LATAM": {"multiplier": 0.8, "currency": "USD"},  # Default LATAM
    "DEFAULT": {"multiplier": 1.0, "currency": "EUR"}
}

# Discount rules
DISCOUNT_RULES = {
    DiscountType.POWER_USER: {
        "percent": 10,
        "condition": "total_searches >= 100",
        "message": "🎯 Power User: -10%"
    },
    DiscountType.REFERRAL_KING: {
        "percent": 10,
        "condition": "referrals >= 10",
        "message": "👥 Referral King: -10%"
    },
    DiscountType.TRIAL_ENDING: {
        "percent": 20,
        "condition": "trial_days_left <= 1",
        "message": "🔥 Last Day Trial: -20%"
    },
    DiscountType.SEASONAL: {
        "percent": 15,
        "condition": "special_promo_active",
        "message": "🎉 Limited Time: -15%"
    },
    DiscountType.LOYALTY: {
        "percent": 5,
        "condition": "user_age_days >= 90",
        "message": "🏆 Loyalty: -5%"
    },
    DiscountType.FIRST_TIME: {
        "percent": 25,
        "condition": "first_subscription",
        "message": "✨ First Time: -25%"
    }
}

# Upgrade prompts by context
UPGRADE_PROMPTS = {
    UpgradeContext.SEARCH_LIMIT: {
        "headline": "🚫 Límite de Búsquedas Alcanzado",
        "message": "Has usado tus 10 búsquedas diarias. Actualiza a Premium para búsquedas ilimitadas.",
        "cta": "Desbloquear Ilimitadas",
        "highlight_feature": "unlimited_searches"
    },
    UpgradeContext.WATCHLIST_FULL: {
        "headline": "⭐ Watchlist Lleno",
        "message": "Has usado tus 3 slots. Premium te da watchlist ilimitado para no perderte ningún chollo.",
        "cta": "Expandir Watchlist",
        "highlight_feature": "unlimited_watchlist"
    },
    UpgradeContext.DEAL_MISSED: {
        "headline": "😔 Chollo Perdido",
        "message": "Perdiste un chollo de €{value} por {reason}. Premium = 0 chollos perdidos.",
        "cta": "No Perder Más Chollos",
        "highlight_feature": "priority_notifications"
    },
    UpgradeContext.HIGH_VALUE: {
        "headline": "💰 Has Generado Gran Valor",
        "message": "Has visto €{value} en chollos. Desbloquea todo el potencial por solo €9.99/mes.",
        "cta": "Maximizar Mi Ahorro",
        "highlight_feature": "all_features"
    },
    UpgradeContext.TRIAL_EXPIRING: {
        "headline": "⏰ Tu Trial Expira Pronto",
        "message": "Quedan {days} días de trial. Continúa ahorrando con 20% descuento.",
        "cta": "Continuar con Descuento",
        "highlight_feature": "all_features"
    },
    UpgradeContext.GENERAL: {
        "headline": "🚀 Desbloquea Todo el Potencial",
        "message": "Búsquedas ilimitadas, watchlist sin límites, notificaciones priority y más.",
        "cta": "Ver Planes Premium",
        "highlight_feature": "all_features"
    }
}


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class PriceQuote:
    """A price quote for a plan with applied discounts"""
    plan_tier: str
    base_price: float
    discounts_applied: List[Dict]  # [{type, percent, amount}]
    final_price: float
    currency: str
    region: str
    
    # Metadata
    savings_amount: float
    savings_percent: float
    period_months: int
    trial_days: int
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class UpgradeOffer:
    """A personalized upgrade offer"""
    user_id: int
    context: str  # UpgradeContext
    quote: PriceQuote
    message: Dict  # headline, message, cta
    created_at: datetime
    expires_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        if self.expires_at:
            data['expires_at'] = self.expires_at.isoformat()
        return data


# ============================================================================
# PRICING ENGINE
# ============================================================================

class PricingEngine:
    """
    Flexible pricing engine with smart discounts.
    
    Features:
    - Multiple tiers (Basic/Pro, Monthly/Annual)
    - Dynamic discounts (up to 40%)
    - Regional pricing
    - Smart upgrade prompts
    - Limited-time offers
    """
    
    def __init__(self, data_dir: str = ".", config_file: str = "pricing_config.json"):
        self.data_dir = Path(data_dir)
        self.config_file = self.data_dir / config_file
        
        # Load config
        self.config = self._load_config()
        
        # Active promo
        self.active_promo: Optional[Dict] = None
        
        print("✅ PricingEngine initialized")
    
    # ========================================================================
    # CONFIG
    # ========================================================================
    
    def _load_config(self) -> Dict:
        """Load pricing configuration"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ Error loading pricing config: {e}")
        
        # Return default config
        return {
            "tiers": BASE_PRICING,
            "regional_multipliers": REGIONAL_MULTIPLIERS,
            "discount_rules": DISCOUNT_RULES
        }
    
    # ========================================================================
    # DISCOUNT CALCULATION
    # ========================================================================
    
    def calculate_eligible_discounts(self, user_profile: Dict) -> List[DiscountType]:
        """
        Calculate which discounts a user is eligible for.
        
        Args:
            user_profile: Dict with user stats (searches, referrals, etc.)
        
        Returns:
            List of DiscountType enums
        """
        eligible = []
        
        # Power user
        if user_profile.get('total_searches', 0) >= 100:
            eligible.append(DiscountType.POWER_USER)
        
        # Referral king
        if user_profile.get('referrals', 0) >= 10:
            eligible.append(DiscountType.REFERRAL_KING)
        
        # Trial ending
        if user_profile.get('trial_days_left', 999) <= 1:
            eligible.append(DiscountType.TRIAL_ENDING)
        
        # Seasonal promo
        if self.active_promo:
            eligible.append(DiscountType.SEASONAL)
        
        # Loyalty
        if user_profile.get('user_age_days', 0) >= 90:
            eligible.append(DiscountType.LOYALTY)
        
        # First time
        if user_profile.get('first_subscription', True):
            eligible.append(DiscountType.FIRST_TIME)
        
        return eligible
    
    def calculate_total_discount(self, eligible_discounts: List[DiscountType], max_stack: int = 3, max_percent: int = 40) -> Tuple[float, List[Dict]]:
        """
        Calculate total discount from eligible discounts.
        
        Args:
            eligible_discounts: List of DiscountType
            max_stack: Maximum number of discounts to stack
            max_percent: Maximum total discount percentage
        
        Returns:
            (total_percent, discounts_applied)
        """
        if not eligible_discounts:
            return 0.0, []
        
        # Sort by percent (highest first)
        sorted_discounts = sorted(
            eligible_discounts,
            key=lambda d: DISCOUNT_RULES[d]['percent'],
            reverse=True
        )
        
        # Apply up to max_stack
        applied = []
        total_percent = 0.0
        
        for discount in sorted_discounts[:max_stack]:
            rule = DISCOUNT_RULES[discount]
            percent = rule['percent']
            
            # Check if adding this would exceed max
            if total_percent + percent > max_percent:
                percent = max_percent - total_percent
            
            if percent > 0:
                applied.append({
                    'type': discount.value,
                    'percent': percent,
                    'message': rule['message']
                })
                total_percent += percent
            
            if total_percent >= max_percent:
                break
        
        return total_percent, applied
    
    # ========================================================================
    # PRICING
    # ========================================================================
    
    def get_price_quote(self, plan_tier: PlanTier, region: str = "ES", user_profile: Dict = None) -> PriceQuote:
        """
        Get a price quote for a plan with all applicable discounts.
        
        Args:
            plan_tier: PlanTier enum
            region: Region code (ES, US, MX, etc.)
            user_profile: User profile for discount calculation
        
        Returns:
            PriceQuote object
        """
        # Get base price
        base_info = BASE_PRICING[plan_tier]
        base_price = base_info['price']
        
        # Apply regional pricing
        regional_info = REGIONAL_MULTIPLIERS.get(region, REGIONAL_MULTIPLIERS['DEFAULT'])
        base_price *= regional_info['multiplier']
        currency = regional_info['currency']
        
        # Calculate discounts
        if user_profile:
            eligible = self.calculate_eligible_discounts(user_profile)
            discount_percent, discounts_applied = self.calculate_total_discount(eligible)
        else:
            discount_percent = 0.0
            discounts_applied = []
        
        # Calculate final price
        discount_amount = base_price * (discount_percent / 100)
        final_price = base_price - discount_amount
        
        # Add amounts to discount info
        for discount in discounts_applied:
            discount['amount'] = base_price * (discount['percent'] / 100)
        
        return PriceQuote(
            plan_tier=plan_tier.value,
            base_price=round(base_price, 2),
            discounts_applied=discounts_applied,
            final_price=round(final_price, 2),
            currency=currency,
            region=region,
            savings_amount=round(discount_amount, 2),
            savings_percent=round(discount_percent, 1),
            period_months=base_info['period_months'],
            trial_days=base_info['trial_days']
        )
    
    def get_all_plans(self, region: str = "ES", user_profile: Dict = None) -> List[PriceQuote]:
        """
        Get price quotes for all available plans.
        
        Returns:
            List of PriceQuote objects
        """
        quotes = []
        for tier in PlanTier:
            quote = self.get_price_quote(tier, region, user_profile)
            quotes.append(quote)
        return quotes
    
    def compare_plans(self, region: str = "ES", user_profile: Dict = None) -> Dict:
        """
        Get a comparison of all plans.
        
        Returns:
            Dict with plan comparison data
        """
        quotes = self.get_all_plans(region, user_profile)
        
        # Find best value (highest savings %)
        best_value = max(quotes, key=lambda q: q.savings_percent)
        
        # Find most popular (annual plans usually)
        most_popular = next((q for q in quotes if 'annual' in q.plan_tier), quotes[0])
        
        return {
            'plans': [q.to_dict() for q in quotes],
            'best_value': best_value.to_dict(),
            'most_popular': most_popular.to_dict(),
            'region': region,
            'currency': quotes[0].currency if quotes else 'EUR'
        }
    
    # ========================================================================
    # UPGRADE PROMPTS
    # ========================================================================
    
    def create_upgrade_offer(self, user_id: int, context: UpgradeContext, user_profile: Dict, region: str = "ES", plan_tier: PlanTier = PlanTier.BASIC_MONTHLY) -> UpgradeOffer:
        """
        Create a personalized upgrade offer.
        
        Args:
            user_id: User ID
            context: UpgradeContext enum
            user_profile: User profile with stats
            region: User region
            plan_tier: Recommended plan
        
        Returns:
            UpgradeOffer object
        """
        # Get price quote
        quote = self.get_price_quote(plan_tier, region, user_profile)
        
        # Get prompt template
        prompt = UPGRADE_PROMPTS[context].copy()
        
        # Personalize message
        message = prompt['message']
        if '{value}' in message:
            message = message.format(value=user_profile.get('total_value', 0))
        if '{reason}' in message:
            message = message.format(reason=user_profile.get('miss_reason', 'límites'))
        if '{days}' in message:
            message = message.format(days=user_profile.get('trial_days_left', 0))
        
        prompt['message'] = message
        
        # Create offer
        offer = UpgradeOffer(
            user_id=user_id,
            context=context.value,
            quote=quote,
            message=prompt,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=7) if quote.savings_percent > 0 else None
        )
        
        return offer
    
    def get_upgrade_prompt_message(self, offer: UpgradeOffer) -> str:
        """
        Format upgrade offer as message.
        
        Args:
            offer: UpgradeOffer object
        
        Returns:
            Formatted message string
        """
        quote = offer.quote
        msg = offer.message
        
        # Build discount section
        discount_text = ""
        if quote.discounts_applied:
            discount_text = "\n🎁 Descuentos Aplicados:\n"
            for disc in quote.discounts_applied:
                discount_text += f"  {disc['message']}\n"
            discount_text += f"\n⬇️ Total ahorro: -{quote.savings_percent}%"
        
        # Build price section
        if quote.savings_amount > 0:
            price_text = f"~~{quote.currency}{quote.base_price:.2f}~~ → {quote.currency}{quote.final_price:.2f}/mes"
        else:
            price_text = f"{quote.currency}{quote.final_price:.2f}/mes"
        
        # Expiry
        expiry_text = ""
        if offer.expires_at:
            days_left = (offer.expires_at - datetime.now()).days
            if days_left > 0:
                expiry_text = f"\n⏰ Oferta expira en {days_left} días"
        
        return f"""{msg['headline']}

{msg['message']}
{discount_text}

💰 Precio: {price_text}
🎁 Incluye {quote.trial_days} días de prueba gratis{expiry_text}

[{msg['cta']}]
"""
    
    # ========================================================================
    # PROMO MANAGEMENT
    # ========================================================================
    
    def activate_promo(self, name: str, discount_percent: int, duration_days: int):
        """Activate a limited-time promo"""
        self.active_promo = {
            'name': name,
            'discount_percent': discount_percent,
            'start_date': datetime.now(),
            'end_date': datetime.now() + timedelta(days=duration_days)
        }
        print(f"🎉 Promo '{name}' activated: {discount_percent}% off for {duration_days} days")
    
    def deactivate_promo(self):
        """Deactivate current promo"""
        if self.active_promo:
            print(f"🚫 Promo '{self.active_promo['name']}' deactivated")
        self.active_promo = None
    
    def check_promo_expiry(self):
        """Check if promo has expired and deactivate if needed"""
        if self.active_promo:
            if datetime.now() >= self.active_promo['end_date']:
                self.deactivate_promo()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def format_pricing_table(quotes: List[PriceQuote]) -> str:
    """
    Format pricing quotes as a comparison table.
    
    Args:
        quotes: List of PriceQuote objects
    
    Returns:
        Formatted table string
    """
    lines = ["💳 Planes Premium\n"]
    
    for quote in quotes:
        plan_name = BASE_PRICING[PlanTier(quote.plan_tier)]['name']
        
        if quote.savings_amount > 0:
            price_str = f"~~{quote.currency}{quote.base_price:.2f}~~ {quote.currency}{quote.final_price:.2f}"
            savings_str = f" (ahorra {quote.savings_percent}%)"
        else:
            price_str = f"{quote.currency}{quote.final_price:.2f}"
            savings_str = ""
        
        lines.append(f"\n✨ {plan_name}")
        lines.append(f"  💰 {price_str}{savings_str}")
        lines.append(f"  🎁 {quote.trial_days} días de prueba")
        
        if 'annual' in quote.plan_tier:
            monthly_equiv = quote.final_price / 12
            lines.append(f"  📊 Solo {quote.currency}{monthly_equiv:.2f}/mes")
    
    return "\n".join(lines)


# ============================================================================
# MAIN (TESTING)
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("💳 TESTING: Pricing Engine")
    print("="*60 + "\n")
    
    # Initialize engine
    engine = PricingEngine()
    
    # Test user profile
    user_profile = {
        'total_searches': 120,
        'referrals': 12,
        'trial_days_left': 1,
        'user_age_days': 95,
        'first_subscription': True,
        'total_value': 2450
    }
    
    print("1️⃣ Calculate Discounts")
    print("-" * 40)
    
    eligible = engine.calculate_eligible_discounts(user_profile)
    print(f"Eligible discounts: {[d.value for d in eligible]}")
    
    total_percent, applied = engine.calculate_total_discount(eligible)
    print(f"\nTotal discount: {total_percent}%")
    for disc in applied:
        print(f"  - {disc['message']}")
    
    print("\n2️⃣ Price Quote")
    print("-" * 40)
    
    quote = engine.get_price_quote(PlanTier.BASIC_MONTHLY, "ES", user_profile)
    print(f"Plan: {quote.plan_tier}")
    print(f"Base: €{quote.base_price}")
    print(f"Final: €{quote.final_price}")
    print(f"Savings: {quote.savings_percent}% (€{quote.savings_amount})")
    
    print("\n3️⃣ All Plans Comparison")
    print("-" * 40)
    
    all_plans = engine.get_all_plans("ES", user_profile)
    print(format_pricing_table(all_plans))
    
    print("\n4️⃣ Upgrade Offer")
    print("-" * 40)
    
    offer = engine.create_upgrade_offer(
        user_id=12345,
        context=UpgradeContext.HIGH_VALUE,
        user_profile=user_profile,
        region="ES"
    )
    
    print(engine.get_upgrade_prompt_message(offer))
    
    print("\n5️⃣ Promo System")
    print("-" * 40)
    
    engine.activate_promo("Black Friday", 30, 3)
    
    # Get quote with promo
    quote_promo = engine.get_price_quote(PlanTier.BASIC_ANNUAL, "ES", user_profile)
    print(f"\nWith promo: €{quote_promo.final_price} (was €{quote_promo.base_price})")
    print(f"Total savings: {quote_promo.savings_percent}%")
    
    print("\n" + "="*60)
    print("✅ Testing Complete!")
    print("="*60 + "\n")
