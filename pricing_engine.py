#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pricing Engine with Dynamic Discounts
IT6 - DAY 4/5

Features:
- Multiple pricing tiers (Basic/Pro, Monthly/Annual)
- Dynamic discount calculation (up to 40%)
- Regional pricing
- Smart upgrade prompts based on context
- Limited-time offers
- Coupon code system

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
    COUPON = "coupon"


class UpgradeContext(Enum):
    """Context for showing upgrade prompt"""
    SEARCH_LIMIT = "search_limit"
    WATCHLIST_FULL = "watchlist_full"
    DEAL_MISSED = "deal_missed"
    HIGH_VALUE_SHOWN = "high_value"
    TRIAL_EXPIRING = "trial_expiring"
    GENERAL = "general"


# Maximum discount allowed
MAX_DISCOUNT_PERCENT = 40
MAX_DISCOUNT_STACK = 3  # Max number of discounts to stack


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class PricePlan:
    """A pricing plan"""
    tier_id: str
    name: str
    price: float
    currency: str
    billing_period: str  # "monthly" or "annual"
    features: List[str]
    trial_days: int = 7
    discount_percent: int = 0
    savings_vs_monthly: float = 0.0
    popular: bool = False
    recommended_for: Optional[str] = None
    
    @property
    def discounted_price(self) -> float:
        """Calculate discounted price"""
        if self.discount_percent == 0:
            return self.price
        return self.price * (1 - self.discount_percent / 100)
    
    @property
    def monthly_equivalent(self) -> float:
        """Calculate monthly equivalent price"""
        if self.billing_period == "monthly":
            return self.discounted_price
        return self.discounted_price / 12
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['discounted_price'] = self.discounted_price
        data['monthly_equivalent'] = self.monthly_equivalent
        return data


@dataclass
class AppliedDiscount:
    """A discount applied to a purchase"""
    discount_type: str
    percent: int
    reason: str
    applied_at: datetime
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['applied_at'] = self.applied_at.isoformat()
        return data


@dataclass
class PriceQuote:
    """A price quote for a user"""
    user_id: int
    tier_id: str
    base_price: float
    currency: str
    discounts_applied: List[AppliedDiscount]
    final_price: float
    savings: float
    valid_until: datetime
    
    @property
    def total_discount_percent(self) -> int:
        """Total discount percentage"""
        return sum(d.percent for d in self.discounts_applied)
    
    @property
    def is_valid(self) -> bool:
        """Check if quote is still valid"""
        return datetime.now() < self.valid_until
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['discounts_applied'] = [d.to_dict() for d in self.discounts_applied]
        data['valid_until'] = self.valid_until.isoformat()
        data['total_discount_percent'] = self.total_discount_percent
        return data


# ============================================================================
# PRICING ENGINE
# ============================================================================

class PricingEngine:
    """
    Manages pricing, discounts, and upgrade prompts.
    
    Features:
    - Multiple pricing tiers
    - Dynamic discount calculation
    - Regional pricing
    - Smart upgrade prompts
    - Quote generation with expiration
    """
    
    def __init__(self, config_file: str = "pricing_config.json", data_dir: str = "."):
        self.config_file = Path(config_file)
        self.data_dir = Path(data_dir)
        self.quotes_file = self.data_dir / "price_quotes.json"
        
        # Load configuration
        self.config = self._load_config()
        self.plans = self._load_plans()
        
        # Load quotes
        self.quotes: Dict[int, List[PriceQuote]] = self._load_quotes()
        
        print("✅ PricingEngine initialized")
    
    # ========================================================================
    # CONFIGURATION
    # ========================================================================
    
    def _load_config(self) -> Dict:
        """Load pricing configuration"""
        if not self.config_file.exists():
            print("⚠️ Pricing config not found, using defaults")
            return {}
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Error loading config: {e}")
            return {}
    
    def _load_plans(self) -> Dict[str, PricePlan]:
        """Load pricing plans from config"""
        plans = {}
        
        if 'tiers' not in self.config:
            return plans
        
        for tier_id, tier_data in self.config['tiers'].items():
            plans[tier_id] = PricePlan(
                tier_id=tier_id,
                name=tier_data['name'],
                price=tier_data['price'],
                currency=tier_data['currency'],
                billing_period=tier_data['billing_period'],
                features=tier_data['features'],
                trial_days=tier_data.get('trial_days', 7),
                discount_percent=tier_data.get('discount_percent', 0),
                savings_vs_monthly=tier_data.get('savings_vs_monthly', 0),
                popular=tier_data.get('popular', False),
                recommended_for=tier_data.get('recommended_for')
            )
        
        return plans
    
    def _load_quotes(self) -> Dict[int, List[PriceQuote]]:
        """Load price quotes from file"""
        if not self.quotes_file.exists():
            return {}
        
        try:
            with open(self.quotes_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                quotes = {}
                for user_id, quote_list in data.items():
                    quotes[int(user_id)] = [
                        PriceQuote(
                            user_id=q['user_id'],
                            tier_id=q['tier_id'],
                            base_price=q['base_price'],
                            currency=q['currency'],
                            discounts_applied=[
                                AppliedDiscount(
                                    discount_type=d['discount_type'],
                                    percent=d['percent'],
                                    reason=d['reason'],
                                    applied_at=datetime.fromisoformat(d['applied_at'])
                                )
                                for d in q['discounts_applied']
                            ],
                            final_price=q['final_price'],
                            savings=q['savings'],
                            valid_until=datetime.fromisoformat(q['valid_until'])
                        )
                        for q in quote_list
                    ]
                return quotes
        except Exception as e:
            print(f"⚠️ Error loading quotes: {e}")
            return {}
    
    def _save_quotes(self):
        """Save price quotes to file"""
        try:
            data = {
                str(user_id): [q.to_dict() for q in quotes]
                for user_id, quotes in self.quotes.items()
            }
            with open(self.quotes_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Error saving quotes: {e}")
    
    # ========================================================================
    # PRICING PLANS
    # ========================================================================
    
    def get_plan(self, tier_id: str) -> Optional[PricePlan]:
        """Get a pricing plan by ID"""
        return self.plans.get(tier_id)
    
    def get_all_plans(self, currency: str = "EUR") -> List[PricePlan]:
        """Get all pricing plans"""
        return [plan for plan in self.plans.values() if plan.currency == currency]
    
    def get_regional_pricing(self, country_code: str) -> Dict:
        """Get pricing for a specific region"""
        if 'regional_pricing' not in self.config:
            return {}
        return self.config['regional_pricing'].get(country_code, {})
    
    # ========================================================================
    # DISCOUNT CALCULATION
    # ========================================================================
    
    def calculate_discounts(self, user_id: int, user_profile: Dict) -> List[AppliedDiscount]:
        """
        Calculate applicable discounts for a user.
        
        Args:
            user_id: User ID
            user_profile: Dict with user data (searches, referrals, trial_days_left, etc.)
        
        Returns:
            List of AppliedDiscount objects
        """
        discounts = []
        
        if 'discount_rules' not in self.config:
            return discounts
        
        rules = self.config['discount_rules']
        
        # Power user discount
        if 'power_user' in rules:
            total_searches = user_profile.get('total_searches', 0)
            if total_searches > 100:
                discounts.append(AppliedDiscount(
                    discount_type=DiscountType.POWER_USER.value,
                    percent=rules['power_user']['discount_percent'],
                    reason=rules['power_user']['description'],
                    applied_at=datetime.now()
                ))
        
        # Referral king discount
        if 'referral_king' in rules:
            referrals = user_profile.get('referrals', 0)
            if referrals > 10:
                discounts.append(AppliedDiscount(
                    discount_type=DiscountType.REFERRAL_KING.value,
                    percent=rules['referral_king']['discount_percent'],
                    reason=rules['referral_king']['description'],
                    applied_at=datetime.now()
                ))
        
        # Trial ending discount
        if 'trial_ending' in rules:
            trial_days_left = user_profile.get('trial_days_left', 999)
            if trial_days_left <= 1:
                discounts.append(AppliedDiscount(
                    discount_type=DiscountType.TRIAL_ENDING.value,
                    percent=rules['trial_ending']['discount_percent'],
                    reason=rules['trial_ending']['description'],
                    applied_at=datetime.now()
                ))
        
        # Seasonal promotion
        if 'seasonal' in rules:
            if user_profile.get('special_promo_active', False):
                discounts.append(AppliedDiscount(
                    discount_type=DiscountType.SEASONAL.value,
                    percent=rules['seasonal']['discount_percent'],
                    reason=rules['seasonal']['description'],
                    applied_at=datetime.now()
                ))
        
        # Loyalty discount
        if 'loyalty' in rules:
            account_age_days = user_profile.get('account_age_days', 0)
            if account_age_days > 90:
                discounts.append(AppliedDiscount(
                    discount_type=DiscountType.LOYALTY.value,
                    percent=rules['loyalty']['discount_percent'],
                    reason=rules['loyalty']['description'],
                    applied_at=datetime.now()
                ))
        
        # Sort by percent (highest first) and limit
        discounts.sort(key=lambda d: d.percent, reverse=True)
        discounts = discounts[:MAX_DISCOUNT_STACK]
        
        # Ensure total doesn't exceed max
        total_discount = sum(d.percent for d in discounts)
        if total_discount > MAX_DISCOUNT_PERCENT:
            # Scale down proportionally
            scale_factor = MAX_DISCOUNT_PERCENT / total_discount
            for discount in discounts:
                discount.percent = int(discount.percent * scale_factor)
        
        return discounts
    
    def apply_coupon(self, coupon_code: str) -> Optional[AppliedDiscount]:
        """
        Apply a coupon code.
        
        Args:
            coupon_code: Coupon code to apply
        
        Returns:
            AppliedDiscount if valid, None otherwise
        """
        # Mock coupon validation
        # In real implementation, check against database
        valid_coupons = {
            "WELCOME20": 20,
            "SAVE30": 30,
            "VIP50": 50
        }
        
        if coupon_code.upper() in valid_coupons:
            return AppliedDiscount(
                discount_type=DiscountType.COUPON.value,
                percent=valid_coupons[coupon_code.upper()],
                reason=f"Coupon: {coupon_code.upper()}",
                applied_at=datetime.now()
            )
        
        return None
    
    # ========================================================================
    # QUOTE GENERATION
    # ========================================================================
    
    def generate_quote(
        self,
        user_id: int,
        tier_id: str,
        user_profile: Dict,
        validity_hours: int = 24
    ) -> Optional[PriceQuote]:
        """
        Generate a price quote for a user.
        
        Args:
            user_id: User ID
            tier_id: Pricing tier ID
            user_profile: User data for discount calculation
            validity_hours: Hours until quote expires
        
        Returns:
            PriceQuote object
        """
        plan = self.get_plan(tier_id)
        if not plan:
            return None
        
        # Calculate discounts
        discounts = self.calculate_discounts(user_id, user_profile)
        
        # Calculate final price
        base_price = plan.price
        total_discount_percent = sum(d.percent for d in discounts)
        final_price = base_price * (1 - total_discount_percent / 100)
        savings = base_price - final_price
        
        # Create quote
        quote = PriceQuote(
            user_id=user_id,
            tier_id=tier_id,
            base_price=base_price,
            currency=plan.currency,
            discounts_applied=discounts,
            final_price=final_price,
            savings=savings,
            valid_until=datetime.now() + timedelta(hours=validity_hours)
        )
        
        # Save quote
        if user_id not in self.quotes:
            self.quotes[user_id] = []
        self.quotes[user_id].append(quote)
        self._save_quotes()
        
        return quote
    
    def get_latest_quote(self, user_id: int, tier_id: str = None) -> Optional[PriceQuote]:
        """Get latest quote for user"""
        if user_id not in self.quotes:
            return None
        
        quotes = self.quotes[user_id]
        if tier_id:
            quotes = [q for q in quotes if q.tier_id == tier_id]
        
        if not quotes:
            return None
        
        # Return latest valid quote
        valid_quotes = [q for q in quotes if q.is_valid]
        if valid_quotes:
            return valid_quotes[-1]
        
        return quotes[-1]
    
    # ========================================================================
    # UPGRADE PROMPTS
    # ========================================================================
    
    def get_upgrade_prompt(self, context: UpgradeContext, user_data: Dict = None) -> Dict:
        """
        Get contextual upgrade prompt message.
        
        Args:
            context: Context for the upgrade prompt
            user_data: Optional user data for personalization
        
        Returns:
            Dict with headline, message, cta
        """
        prompts = {
            UpgradeContext.SEARCH_LIMIT: {
                "headline": "🚫 Límite de Búsquedas Alcanzado",
                "message": "Has usado tus 10 búsquedas diarias. Upgrade a Premium para búsquedas ilimitadas.",
                "cta": "Desbloquear Búsquedas Ilimitadas",
                "icon": "🔍"
            },
            UpgradeContext.WATCHLIST_FULL: {
                "headline": "⭐ Watchlist Lleno",
                "message": "Has usado tus 3 slots. Premium = watchlist ilimitado para no perderte ningún chollo.",
                "cta": "Expandir Watchlist",
                "icon": "⭐"
            },
            UpgradeContext.DEAL_MISSED: {
                "headline": "😔 Perdiste Este Chollo",
                "message": f"Lo perdiste por 2 minutos. Premium = notificaciones instantáneas, 24x más rápidas.",
                "cta": "Nunca Más Perder Chollos",
                "icon": "🔥"
            },
            UpgradeContext.HIGH_VALUE_SHOWN: {
                "headline": "💰 Has Visto Gran Valor",
                "message": f"Te hemos mostrado €{user_data.get('total_savings', 0):,.0f} en chollos. Desblóquealos todos por €9.99/mes.",
                "cta": "Maximizar Mi Ahorro",
                "icon": "💎"
            },
            UpgradeContext.TRIAL_EXPIRING: {
                "headline": "⏰ Tu Trial Expira Pronto",
                "message": f"Quedan {user_data.get('days_left', 0)} días. No pierdas acceso a features premium. 🎁 20% OFF si actualizas ahora.",
                "cta": "Mantener Premium con Descuento",
                "icon": "🎁"
            },
            UpgradeContext.GENERAL: {
                "headline": "✨ Desbloquea Premium",
                "message": "Búsquedas ilimitadas, watchlist sin límites, notificaciones priority y más.",
                "cta": "Ver Planes Premium",
                "icon": "🚀"
            }
        }
        
        return prompts.get(context, prompts[UpgradeContext.GENERAL])
    
    # ========================================================================
    # HELPERS
    # ========================================================================
    
    def get_feature_descriptions(self) -> Dict[str, str]:
        """Get feature descriptions from config"""
        return self.config.get('feature_descriptions', {})
    
    def get_social_proof(self) -> Dict:
        """Get social proof data for marketing"""
        return self.config.get('marketing', {}).get('social_proof', {})
    
    def get_value_props(self) -> List[str]:
        """Get value propositions for marketing"""
        return self.config.get('marketing', {}).get('value_props', [])


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def format_pricing_table(plans: List[PricePlan], user_quote: Optional[PriceQuote] = None) -> str:
    """
    Format pricing plans as a table.
    
    Args:
        plans: List of PricePlan objects
        user_quote: Optional quote with discounts
    
    Returns:
        Formatted pricing table string
    """
    output = "💰 Planes Premium\n\n"
    
    for plan in plans:
        popular_tag = " 🔥 POPULAR" if plan.popular else ""
        
        output += f"""{plan.name}{popular_tag}
• Precio: €{plan.price}/{plan.billing_period[:3]}
"""
        
        if plan.savings_vs_monthly > 0:
            output += f"• Ahorro: €{plan.savings_vs_monthly:.0f}/año ({plan.discount_percent}% OFF)\n"
        
        output += f"• Trial: {plan.trial_days} días gratis\n"
        output += f"• Features: {len(plan.features)}\n"
        
        # Show discount if applicable
        if user_quote and user_quote.tier_id == plan.tier_id:
            if user_quote.discounts_applied:
                output += f"\n🎁 TU DESCUENTO: {user_quote.total_discount_percent}% OFF\n"
                output += f"• Precio final: €{user_quote.final_price:.2f}\n"
                output += f"• Ahorras: €{user_quote.savings:.2f}\n"
                for discount in user_quote.discounts_applied:
                    output += f"  • {discount.reason} (-{discount.percent}%)\n"
        
        output += "\n"
    
    return output


# ============================================================================
# MAIN (TESTING)
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("💳 TESTING: Pricing Engine")
    print("="*60 + "\n")
    
    # Initialize engine
    engine = PricingEngine()
    
    test_user = 22222
    
    print("1️⃣ Available Plans")
    print("-" * 40)
    
    plans = engine.get_all_plans()
    for plan in plans:
        print(f"{plan.name}: €{plan.price}/{plan.billing_period}")
    
    print("\n2️⃣ Discount Calculation")
    print("-" * 40)
    
    user_profile = {
        'total_searches': 150,
        'referrals': 12,
        'trial_days_left': 1,
        'account_age_days': 45,
        'special_promo_active': True
    }
    
    discounts = engine.calculate_discounts(test_user, user_profile)
    print(f"Applicable discounts: {len(discounts)}")
    for discount in discounts:
        print(f"  • {discount.reason}: {discount.percent}%")
    
    total_discount = sum(d.percent for d in discounts)
    print(f"\nTotal discount: {total_discount}%")
    
    print("\n3️⃣ Price Quote")
    print("-" * 40)
    
    quote = engine.generate_quote(test_user, "basic_monthly", user_profile)
    if quote:
        print(f"Plan: {quote.tier_id}")
        print(f"Base price: €{quote.base_price}")
        print(f"Final price: €{quote.final_price:.2f}")
        print(f"Savings: €{quote.savings:.2f} ({quote.total_discount_percent}% OFF)")
        print(f"Valid until: {quote.valid_until.strftime('%Y-%m-%d %H:%M')}")
    
    print("\n4️⃣ Upgrade Prompts")
    print("-" * 40)
    
    for context in UpgradeContext:
        prompt = engine.get_upgrade_prompt(context, {'days_left': 2, 'total_savings': 2450})
        print(f"\n{context.value}:")
        print(f"{prompt['icon']} {prompt['headline']}")
        print(f"{prompt['message']}")
        print(f"[{prompt['cta']}]")
    
    print("\n5️⃣ Pricing Table")
    print("-" * 40)
    print(format_pricing_table(plans[:2], quote))
    
    print("\n" + "="*60)
    print("✅ Testing Complete!")
    print("="*60 + "\n")
