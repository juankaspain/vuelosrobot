#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Smart Paywalls & Trigger System for Freemium Conversion
IT6 - DAY 1/5

Features:
- Intelligent paywall triggers based on user behavior
- A/B testing framework with 4 variants
- Dynamic feature gating
- Smart timing to maximize conversion
- Anti-fatigue system (max 1 paywall/24h)
- Conversion tracking and analytics

Author: @Juanka_Spain
Version: 14.0.0-alpha.1
Date: 2026-01-16
"""

import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path


# ============================================================================
# ENUMS & CONSTANTS
# ============================================================================

class PaywallTrigger(Enum):
    """Types of paywall triggers based on user behavior"""
    SEARCH_LIMIT_REACHED = "search_limit"      # Hit daily search limit
    WATCHLIST_FULL = "watchlist_full"          # All watchlist slots used
    DEAL_MISSED = "deal_missed"                # Missed a deal due to limits
    POWER_USER = "power_user"                  # Heavy user (50+ searches)
    VALUE_DEMONSTRATED = "value_shown"         # High value shown (€500+)
    REFERRAL_SUCCESS = "referral_king"         # Many referrals (5+)
    TIME_BASED = "time_trial"                  # After X days of usage


class PaywallVariant(Enum):
    """A/B test variants for paywall messages"""
    A = "benefit_focused"    # Focus on benefits
    B = "savings_focused"    # Focus on money saved
    C = "urgency_focused"    # Focus on urgency/scarcity
    D = "social_focused"     # Focus on social proof


class FeatureGateStatus(Enum):
    """Status of feature gate check"""
    ALLOWED = "allowed"
    LIMIT_REACHED = "limit_reached"
    PREMIUM_REQUIRED = "premium_required"


# Feature limits configuration
FEATURE_LIMITS = {
    "daily_searches": {
        "free": 10,
        "premium": -1,  # Unlimited
        "reset_period": "daily"
    },
    "watchlist_slots": {
        "free": 3,
        "premium": -1,  # Unlimited
        "reset_period": "never"
    },
    "notifications": {
        "free": "basic",
        "premium": "priority",
        "reset_period": "never"
    },
    "price_history": {
        "free": 30,  # days
        "premium": 365,  # days
        "reset_period": "never"
    },
    "groups": {
        "free": 2,
        "premium": -1,  # Unlimited
        "reset_period": "never"
    },
    "export_data": {
        "free": 0,  # Not allowed
        "premium": -1,  # Unlimited
        "reset_period": "monthly"
    },
    "priority_support": {
        "free": 0,
        "premium": 1,
        "reset_period": "never"
    }
}


# Paywall message variants (A/B testing)
PAYWALL_VARIANTS = {
    PaywallVariant.A: {
        "headline": "🚀 Desbloquea Todo el Potencial",
        "body": "Búsquedas ilimitadas, watchlist sin límites, notificaciones priority y más.",
        "cta": "Probar Premium 7 Días Gratis",
        "emoji": "✨",
        "style": "benefit"
    },
    PaywallVariant.B: {
        "headline": "💰 Has Visto €{value} en Chollos",
        "body": "Usuarios premium ahorran un 65% más. Desbloquea chollos ilimitados por solo €9.99/mes.",
        "cta": "Empezar a Ahorrar Más",
        "emoji": "💎",
        "style": "savings"
    },
    PaywallVariant.C: {
        "headline": "⚡ No Te Pierdas Más Chollos",
        "body": "Acabas de perder un chollo de €{missed}. Premium = notificaciones instantáneas.",
        "cta": "Activar Premium Ahora",
        "emoji": "🔥",
        "style": "urgency"
    },
    PaywallVariant.D: {
        "headline": "👥 Únete a 892 Usuarios Premium",
        "body": "El 85% de top hunters son premium. Rating 4.8/5 ⭐ No te quedes atrás.",
        "cta": "Ver Por Qué Eligen Premium",
        "emoji": "🏆",
        "style": "social"
    }
}


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class FeatureGate:
    """Configuration for a feature gate"""
    feature_name: str
    free_limit: int  # -1 = unlimited
    premium_limit: int  # -1 = unlimited
    reset_period: str  # "daily", "weekly", "monthly", "never"
    current_usage: int = 0
    last_reset: Optional[datetime] = None


@dataclass
class PaywallEvent:
    """Record of a paywall being shown to user"""
    user_id: int
    trigger: str  # PaywallTrigger value
    variant: str  # PaywallVariant value
    timestamp: datetime
    converted: bool = False
    dismissed: bool = False
    context: Dict = None  # Additional context (e.g., deal missed, value shown)
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'PaywallEvent':
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class UserFeatureUsage:
    """Track user's feature usage for gating"""
    user_id: int
    feature_usage: Dict[str, int]  # feature_name -> current_usage
    last_reset: Dict[str, datetime]  # feature_name -> last_reset_time
    is_premium: bool = False
    premium_since: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['last_reset'] = {k: v.isoformat() for k, v in self.last_reset.items()}
        if self.premium_since:
            data['premium_since'] = self.premium_since.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'UserFeatureUsage':
        data['last_reset'] = {k: datetime.fromisoformat(v) for k, v in data['last_reset'].items()}
        if data.get('premium_since'):
            data['premium_since'] = datetime.fromisoformat(data['premium_since'])
        return cls(**data)


# ============================================================================
# PAYWALL MANAGER
# ============================================================================

class PaywallManager:
    """
    Manages smart paywalls with intelligent triggers and A/B testing.
    
    Features:
    - 7 types of behavioral triggers
    - 4 A/B test variants
    - Anti-fatigue (max 1 paywall/24h)
    - Feature gating with automatic resets
    - Conversion tracking
    """
    
    def __init__(self, data_dir: str = "."):
        self.data_dir = Path(data_dir)
        self.paywall_events_file = self.data_dir / "paywall_events.json"
        self.feature_usage_file = self.data_dir / "feature_usage.json"
        
        # Load data
        self.paywall_events: Dict[int, List[PaywallEvent]] = self._load_paywall_events()
        self.feature_usage: Dict[int, UserFeatureUsage] = self._load_feature_usage()
        
        print("✅ PaywallManager initialized")
    
    # ========================================================================
    # DATA PERSISTENCE
    # ========================================================================
    
    def _load_paywall_events(self) -> Dict[int, List[PaywallEvent]]:
        """Load paywall events from file"""
        if not self.paywall_events_file.exists():
            return {}
        
        try:
            with open(self.paywall_events_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {
                    int(user_id): [PaywallEvent.from_dict(e) for e in events]
                    for user_id, events in data.items()
                }
        except Exception as e:
            print(f"⚠️ Error loading paywall events: {e}")
            return {}
    
    def _save_paywall_events(self):
        """Save paywall events to file"""
        try:
            data = {
                str(user_id): [e.to_dict() for e in events]
                for user_id, events in self.paywall_events.items()
            }
            with open(self.paywall_events_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Error saving paywall events: {e}")
    
    def _load_feature_usage(self) -> Dict[int, UserFeatureUsage]:
        """Load feature usage from file"""
        if not self.feature_usage_file.exists():
            return {}
        
        try:
            with open(self.feature_usage_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {
                    int(user_id): UserFeatureUsage.from_dict(usage)
                    for user_id, usage in data.items()
                }
        except Exception as e:
            print(f"⚠️ Error loading feature usage: {e}")
            return {}
    
    def _save_feature_usage(self):
        """Save feature usage to file"""
        try:
            data = {
                str(user_id): usage.to_dict()
                for user_id, usage in self.feature_usage.items()
            }
            with open(self.feature_usage_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Error saving feature usage: {e}")
    
    # ========================================================================
    # FEATURE GATING
    # ========================================================================
    
    def _get_or_create_usage(self, user_id: int) -> UserFeatureUsage:
        """Get or create user feature usage record"""
        if user_id not in self.feature_usage:
            self.feature_usage[user_id] = UserFeatureUsage(
                user_id=user_id,
                feature_usage={},
                last_reset={}
            )
        return self.feature_usage[user_id]
    
    def _should_reset_usage(self, feature_name: str, last_reset: Optional[datetime]) -> bool:
        """Check if feature usage should be reset"""
        if feature_name not in FEATURE_LIMITS:
            return False
        
        reset_period = FEATURE_LIMITS[feature_name]["reset_period"]
        
        if reset_period == "never" or not last_reset:
            return False
        
        now = datetime.now()
        
        if reset_period == "daily":
            return now.date() > last_reset.date()
        elif reset_period == "weekly":
            return (now - last_reset).days >= 7
        elif reset_period == "monthly":
            return (now.year, now.month) > (last_reset.year, last_reset.month)
        
        return False
    
    def can_use_feature(self, user_id: int, feature_name: str) -> Tuple[bool, str, FeatureGateStatus]:
        """
        Check if user can use a feature.
        
        Returns:
            (can_use, reason, status)
        """
        if feature_name not in FEATURE_LIMITS:
            return True, "Feature not gated", FeatureGateStatus.ALLOWED
        
        usage = self._get_or_create_usage(user_id)
        
        # Premium users have no limits
        if usage.is_premium:
            return True, "Premium user", FeatureGateStatus.ALLOWED
        
        # Check if usage should be reset
        if feature_name in usage.last_reset:
            if self._should_reset_usage(feature_name, usage.last_reset[feature_name]):
                usage.feature_usage[feature_name] = 0
                usage.last_reset[feature_name] = datetime.now()
                self._save_feature_usage()
        
        # Get current usage
        current_usage = usage.feature_usage.get(feature_name, 0)
        free_limit = FEATURE_LIMITS[feature_name]["free"]
        
        # Check if feature is premium-only
        if free_limit == 0:
            return False, f"{feature_name} es solo para usuarios premium", FeatureGateStatus.PREMIUM_REQUIRED
        
        # Check if limit reached
        if free_limit > 0 and current_usage >= free_limit:
            return False, f"Límite de {free_limit} {feature_name} alcanzado", FeatureGateStatus.LIMIT_REACHED
        
        # Feature can be used
        return True, "OK", FeatureGateStatus.ALLOWED
    
    def increment_feature_usage(self, user_id: int, feature_name: str):
        """Increment usage counter for a feature"""
        if feature_name not in FEATURE_LIMITS:
            return
        
        usage = self._get_or_create_usage(user_id)
        
        # Don't track premium users
        if usage.is_premium:
            return
        
        # Initialize if needed
        if feature_name not in usage.feature_usage:
            usage.feature_usage[feature_name] = 0
            usage.last_reset[feature_name] = datetime.now()
        
        # Increment
        usage.feature_usage[feature_name] += 1
        self._save_feature_usage()
    
    def set_premium_status(self, user_id: int, is_premium: bool):
        """Set user's premium status"""
        usage = self._get_or_create_usage(user_id)
        usage.is_premium = is_premium
        if is_premium and not usage.premium_since:
            usage.premium_since = datetime.now()
        self._save_feature_usage()
    
    # ========================================================================
    # PAYWALL TRIGGERS
    # ========================================================================
    
    def should_show_paywall(self, user_id: int, trigger: PaywallTrigger, context: Dict = None) -> Tuple[bool, str]:
        """
        Determine if paywall should be shown based on trigger and anti-fatigue rules.
        
        Returns:
            (should_show, reason)
        """
        usage = self._get_or_create_usage(user_id)
        
        # Never show to premium users
        if usage.is_premium:
            return False, "User is premium"
        
        # Get user's paywall history
        events = self.paywall_events.get(user_id, [])
        
        # Anti-fatigue: Don't show if shown in last 24 hours
        if events:
            last_event = events[-1]
            hours_since = (datetime.now() - last_event.timestamp).total_seconds() / 3600
            if hours_since < 24:
                return False, f"Paywall shown {hours_since:.1f}h ago (anti-fatigue)"
        
        # Don't show on first session (need some engagement)
        if len(events) == 0 and usage.feature_usage.get('daily_searches', 0) < 3:
            return False, "User needs more engagement first"
        
        # Trigger-specific logic
        if trigger == PaywallTrigger.SEARCH_LIMIT_REACHED:
            searches = usage.feature_usage.get('daily_searches', 0)
            if searches >= FEATURE_LIMITS['daily_searches']['free']:
                return True, "Search limit reached"
        
        elif trigger == PaywallTrigger.WATCHLIST_FULL:
            watchlist = usage.feature_usage.get('watchlist_slots', 0)
            if watchlist >= FEATURE_LIMITS['watchlist_slots']['free']:
                return True, "Watchlist full"
        
        elif trigger == PaywallTrigger.POWER_USER:
            total_searches = sum(1 for e in events if 'search' in str(e.context))
            if total_searches >= 50:
                return True, "Power user detected"
        
        elif trigger == PaywallTrigger.VALUE_DEMONSTRATED:
            if context and context.get('total_savings', 0) >= 500:
                return True, "High value demonstrated"
        
        elif trigger == PaywallTrigger.DEAL_MISSED:
            if context and context.get('deal_missed'):
                return True, "Deal missed due to limits"
        
        elif trigger == PaywallTrigger.REFERRAL_SUCCESS:
            if context and context.get('referral_count', 0) >= 5:
                return True, "Successful referrer"
        
        elif trigger == PaywallTrigger.TIME_BASED:
            if events and (datetime.now() - events[0].timestamp).days >= 7:
                return True, "Time-based trigger"
        
        return False, "Trigger conditions not met"
    
    # ========================================================================
    # A/B TESTING
    # ========================================================================
    
    def _select_variant(self, user_id: int, trigger: PaywallTrigger) -> PaywallVariant:
        """
        Select A/B test variant for user.
        Uses consistent hashing so same user always gets same variant.
        """
        # Use user_id for consistent variant assignment
        random.seed(user_id)
        
        # Different triggers may favor different variants
        if trigger == PaywallTrigger.VALUE_DEMONSTRATED:
            # Favor savings-focused variant
            variants = [PaywallVariant.B] * 3 + [PaywallVariant.A, PaywallVariant.D]
        elif trigger == PaywallTrigger.DEAL_MISSED:
            # Favor urgency variant
            variants = [PaywallVariant.C] * 3 + [PaywallVariant.A, PaywallVariant.B]
        elif trigger == PaywallTrigger.REFERRAL_SUCCESS:
            # Favor social proof variant
            variants = [PaywallVariant.D] * 3 + [PaywallVariant.A, PaywallVariant.B]
        else:
            # Equal distribution
            variants = list(PaywallVariant)
        
        variant = random.choice(variants)
        random.seed()  # Reset seed
        return variant
    
    def get_paywall_message(self, user_id: int, trigger: PaywallTrigger, context: Dict = None) -> Dict:
        """
        Get personalized paywall message with A/B test variant.
        
        Returns:
            Dict with headline, body, cta, variant, etc.
        """
        variant = self._select_variant(user_id, trigger)
        message = PAYWALL_VARIANTS[variant].copy()
        
        # Personalize with context
        if context:
            if '{value}' in message['body']:
                message['body'] = message['body'].format(
                    value=context.get('total_savings', 0)
                )
            if '{missed}' in message['body']:
                message['body'] = message['body'].format(
                    missed=context.get('deal_value', 0)
                )
        
        message['variant'] = variant.value
        message['trigger'] = trigger.value
        
        return message
    
    # ========================================================================
    # EVENT TRACKING
    # ========================================================================
    
    def record_paywall_shown(self, user_id: int, trigger: PaywallTrigger, variant: PaywallVariant, context: Dict = None):
        """Record that paywall was shown to user"""
        event = PaywallEvent(
            user_id=user_id,
            trigger=trigger.value,
            variant=variant.value,
            timestamp=datetime.now(),
            context=context or {}
        )
        
        if user_id not in self.paywall_events:
            self.paywall_events[user_id] = []
        
        self.paywall_events[user_id].append(event)
        self._save_paywall_events()
    
    def record_paywall_converted(self, user_id: int):
        """Record that user converted after seeing paywall"""
        if user_id in self.paywall_events and self.paywall_events[user_id]:
            self.paywall_events[user_id][-1].converted = True
            self._save_paywall_events()
    
    def record_paywall_dismissed(self, user_id: int):
        """Record that user dismissed paywall"""
        if user_id in self.paywall_events and self.paywall_events[user_id]:
            self.paywall_events[user_id][-1].dismissed = True
            self._save_paywall_events()
    
    # ========================================================================
    # ANALYTICS
    # ========================================================================
    
    def get_conversion_stats(self) -> Dict:
        """Get overall conversion statistics"""
        total_shown = 0
        total_converted = 0
        total_dismissed = 0
        by_trigger = {}
        by_variant = {}
        
        for events in self.paywall_events.values():
            for event in events:
                total_shown += 1
                
                if event.converted:
                    total_converted += 1
                if event.dismissed:
                    total_dismissed += 1
                
                # By trigger
                if event.trigger not in by_trigger:
                    by_trigger[event.trigger] = {'shown': 0, 'converted': 0}
                by_trigger[event.trigger]['shown'] += 1
                if event.converted:
                    by_trigger[event.trigger]['converted'] += 1
                
                # By variant
                if event.variant not in by_variant:
                    by_variant[event.variant] = {'shown': 0, 'converted': 0}
                by_variant[event.variant]['shown'] += 1
                if event.converted:
                    by_variant[event.variant]['converted'] += 1
        
        # Calculate conversion rates
        for trigger_stats in by_trigger.values():
            if trigger_stats['shown'] > 0:
                trigger_stats['conv_rate'] = trigger_stats['converted'] / trigger_stats['shown']
        
        for variant_stats in by_variant.values():
            if variant_stats['shown'] > 0:
                variant_stats['conv_rate'] = variant_stats['converted'] / variant_stats['shown']
        
        return {
            'total_shown': total_shown,
            'total_converted': total_converted,
            'total_dismissed': total_dismissed,
            'overall_conv_rate': total_converted / total_shown if total_shown > 0 else 0,
            'by_trigger': by_trigger,
            'by_variant': by_variant
        }
    
    def get_user_paywall_history(self, user_id: int) -> List[Dict]:
        """Get paywall history for a specific user"""
        if user_id not in self.paywall_events:
            return []
        
        return [e.to_dict() for e in self.paywall_events[user_id]]


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def format_paywall_message(message: Dict) -> str:
    """
    Format paywall message for Telegram.
    
    Args:
        message: Dict from get_paywall_message()
    
    Returns:
        Formatted message string
    """
    emoji = message.get('emoji', '✨')
    headline = message.get('headline', '')
    body = message.get('body', '')
    cta = message.get('cta', 'Probar Premium')
    
    return f"""{emoji} {headline}

{body}

💎 Premium Features:
✅ Búsquedas ilimitadas
✅ Watchlist sin límites
✅ Notificaciones priority
✅ Historial 1 año
✅ Grupos ilimitados
✅ Export datos
✅ Soporte 24/7

💰 Solo €9.99/mes o €99.99/año (ahorra 17%)

🎁 Prueba gratis 7 días, sin tarjeta

[{cta}]
"""


# ============================================================================
# MAIN (TESTING)
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🧪 TESTING: Smart Paywalls System")
    print("="*60 + "\n")
    
    # Initialize manager
    manager = PaywallManager()
    
    # Test user
    test_user_id = 12345
    
    print("\n1️⃣ Feature Gating Test")
    print("-" * 40)
    
    # Test daily searches
    for i in range(12):
        can_use, reason, status = manager.can_use_feature(test_user_id, "daily_searches")
        print(f"Search {i+1}: {can_use} - {reason}")
        
        if can_use:
            manager.increment_feature_usage(test_user_id, "daily_searches")
        else:
            # Trigger paywall
            should_show, why = manager.should_show_paywall(
                test_user_id, 
                PaywallTrigger.SEARCH_LIMIT_REACHED
            )
            print(f"  → Show paywall: {should_show} ({why})")
            
            if should_show:
                message = manager.get_paywall_message(
                    test_user_id,
                    PaywallTrigger.SEARCH_LIMIT_REACHED
                )
                print(f"\n📱 PAYWALL MESSAGE:")
                print(format_paywall_message(message))
                
                manager.record_paywall_shown(
                    test_user_id,
                    PaywallTrigger.SEARCH_LIMIT_REACHED,
                    PaywallVariant[message['variant'].upper()]
                )
            break
    
    print("\n2️⃣ Value-Based Paywall Test")
    print("-" * 40)
    
    test_user_2 = 67890
    context = {'total_savings': 2450}
    
    should_show, why = manager.should_show_paywall(
        test_user_2,
        PaywallTrigger.VALUE_DEMONSTRATED,
        context=context
    )
    
    if should_show:
        message = manager.get_paywall_message(
            test_user_2,
            PaywallTrigger.VALUE_DEMONSTRATED,
            context=context
        )
        print(f"\n📱 VALUE PAYWALL:")
        print(format_paywall_message(message))
    
    print("\n3️⃣ Conversion Stats")
    print("-" * 40)
    
    # Simulate some conversions
    manager.record_paywall_converted(test_user_id)
    
    stats = manager.get_conversion_stats()
    print(f"\nTotal shown: {stats['total_shown']}")
    print(f"Total converted: {stats['total_converted']}")
    print(f"Conversion rate: {stats['overall_conv_rate']*100:.1f}%")
    
    print("\n" + "="*60)
    print("✅ Testing Complete!")
    print("="*60 + "\n")
