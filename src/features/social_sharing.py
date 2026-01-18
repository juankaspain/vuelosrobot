#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
┌────────────────────────────────────────────────────────────────┐
│  📤 SOCIAL SHARING ENGINE - Viral Mechanics              │
│  🚀 Cazador Supremo v13.0 Enterprise                          │
│  🎯 Target: Share Rate > 20%                               │
└────────────────────────────────────────────────────────────────┘

Sistema de compartir social optimizado para viralización:
- Multi-platform share buttons
- Message templates A/B tested
- Social proof integration
- Share incentives
- Analytics tracking

Autor: @Juanka_Spain
Version: 13.1.0
Date: 2026-01-14
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict
from enum import Enum
from urllib.parse import quote
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
#  CONSTANTS & TEMPLATES
# ═══════════════════════════════════════════════════════════════

# Recompensas por compartir
SHARE_REWARD_COINS = 50
FIRST_3_SHARES_BONUS = 100
VIRAL_SHARE_THRESHOLD = 5  # 5+ conversiones = viral
VIRAL_SHARE_BONUS = 500

# Templates de mensaje (variantes para A/B testing)
MESSAGE_TEMPLATES = {
    'telegram_v1': (
        "🚀 *¡Descubre Cazador Supremo!*\n\n"
        "✈️ Ahorra hasta *30% en vuelos*\n"
        "💰 Gana FlightCoins gratis\n"
        "🔔 Alertas instantáneas de chollos\n\n"
        "🎁 *+300 coins de regalo* con mi código:\n"
        "{link}\n\n"
        "_Ya somos {user_count:,} usuarios ahorrando juntos_"
    ),
    'telegram_v2': (
        "✈️ *Viaja más, gasta menos*\n\n"
        "Encontré esta app que me ahorra cientos en vuelos:\n\n"
        "✅ Precios en tiempo real\n"
        "✅ Alertas personalizadas\n"
        "✅ 100% gratis\n\n"
        "👉 Pruébalo con mi link y gana 300 coins:\n"
        "{link}\n\n"
        "_{referrer_name} te recomienda Cazador Supremo_"
    ),
    'whatsapp_v1': (
        "🚀 *Cazador Supremo*\n\n"
        "Te comparto esta app para ahorrar en vuelos\n\n"
        "✨ Hasta 30% de descuento\n"
        "🎁 +300 coins de regalo con mi código\n\n"
        "{link}"
    ),
    'twitter_v1': (
        "✈️ Ahorro hasta 30% en vuelos con @CazadorSupremo\n\n"
        "💰 Sistema de recompensas\n"
        "🔔 Alertas de chollos\n"
        "🎁 +300 coins gratis con mi código\n\n"
        "{link}\n\n"
        "#VuelosBaratos #Viajes #Ahorro"
    )
}

# Social proof templates
SOCIAL_PROOF_TEMPLATES = [
    "👥 {count} personas ya usan Cazador Supremo",
    "⭐ {count:,} usuarios ahorrando juntos",
    "🎉 Únete a {count:,} cazadores de chollos",
    "🚀 {count:,}+ viajeros inteligentes ya lo usan"
]


class SharePlatform(Enum):
    """Plataformas de compartir"""
    TELEGRAM = "telegram"
    WHATSAPP = "whatsapp"
    TWITTER = "twitter"
    FACEBOOK = "facebook"
    COPY_LINK = "copy"


# ═══════════════════════════════════════════════════════════════
#  DATA CLASSES
# ═══════════════════════════════════════════════════════════════

@dataclass
class ShareEvent:
    """Evento de compartir"""
    user_id: int
    platform: SharePlatform
    timestamp: str
    message_variant: str  # Para A/B testing
    
    # Tracking
    conversions: int = 0  # Cuántos signups generó
    is_viral: bool = False  # 5+ conversiones
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['platform'] = self.platform.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ShareEvent':
        data['platform'] = SharePlatform(data['platform'])
        return cls(**data)


@dataclass
class ShareStats:
    """Estadísticas de sharing por usuario"""
    user_id: int
    total_shares: int = 0
    shares_by_platform: Dict[str, int] = field(default_factory=dict)
    
    # Rewards
    coins_earned: float = 0.0
    
    # Performance
    total_conversions: int = 0
    viral_shares: int = 0  # Shares con 5+ conversiones
    
    # Timing
    first_share_at: Optional[str] = None
    last_share_at: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ShareStats':
        return cls(**data)


# ═══════════════════════════════════════════════════════════════
#  SOCIAL SHARING MANAGER
# ═══════════════════════════════════════════════════════════════

class SocialSharingManager:
    """
    Gestor de compartir social.
    
    Responsabilidades:
    - Generación de share buttons
    - Message templates
    - Social proof
    - Share tracking
    - Rewards
    """
    
    def __init__(self,
                 events_file: str = 'share_events.json',
                 stats_file: str = 'share_stats.json'):
        self.events_file = Path(events_file)
        self.stats_file = Path(stats_file)
        
        self.events: List[ShareEvent] = []
        self.stats: Dict[int, ShareStats] = {}
        
        self._load_data()
        
        logger.info("📤 SocialSharingManager initialized")
    
    def _load_data(self):
        """Carga datos desde archivos."""
        # Eventos
        if self.events_file.exists():
            try:
                with open(self.events_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.events = [ShareEvent.from_dict(e) for e in data]
                logger.info(f"✅ Loaded {len(self.events)} share events")
            except Exception as e:
                logger.error(f"❌ Error loading events: {e}")
        
        # Stats
        if self.stats_file.exists():
            try:
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for user_id_str, stats_data in data.items():
                    user_id = int(user_id_str)
                    self.stats[user_id] = ShareStats.from_dict(stats_data)
                logger.info(f"✅ Loaded stats for {len(self.stats)} users")
            except Exception as e:
                logger.error(f"❌ Error loading stats: {e}")
    
    def _save_data(self):
        """Guarda datos a archivos."""
        try:
            # Eventos
            events_data = [e.to_dict() for e in self.events]
            with open(self.events_file, 'w', encoding='utf-8') as f:
                json.dump(events_data, f, indent=2, ensure_ascii=False)
            
            # Stats
            stats_data = {
                str(user_id): stats.to_dict()
                for user_id, stats in self.stats.items()
            }
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats_data, f, indent=2, ensure_ascii=False)
            
            logger.debug("💾 Share data saved")
        except Exception as e:
            logger.error(f"❌ Error saving data: {e}")
    
    def generate_share_keyboard(self,
                               referral_link: str,
                               user_id: int) -> InlineKeyboardMarkup:
        """
        Genera keyboard con botones de compartir.
        
        Args:
            referral_link: Link de referido del usuario
            user_id: ID del usuario
        
        Returns:
            InlineKeyboardMarkup con botones de share
        """
        # Obtener stats para personalizar
        stats = self.stats.get(user_id)
        shares_count = stats.total_shares if stats else 0
        
        # Mensaje base
        message = self._get_message_variant('telegram_v1', referral_link, user_id)
        message_encoded = quote(message)
        
        # Botones
        buttons = [
            [
                InlineKeyboardButton(
                    "📱 Compartir en Telegram",
                    url=f"https://t.me/share/url?url={quote(referral_link)}&text={message_encoded}"
                ),
            ],
            [
                InlineKeyboardButton(
                    "🟢 Compartir en WhatsApp",
                    url=f"https://wa.me/?text={message_encoded}"
                ),
            ],
            [
                InlineKeyboardButton(
                    "🐦 Compartir en Twitter",
                    url=f"https://twitter.com/intent/tweet?text={message_encoded}"
                ),
            ],
            [
                InlineKeyboardButton(
                    "🔗 Copiar Link",
                    callback_data=f"copy_ref_link_{user_id}"
                ),
            ]
        ]
        
        # Añadir incentivo si es nuevo
        if shares_count < 3:
            buttons.append([
                InlineKeyboardButton(
                    f"✨ Bonus: {FIRST_3_SHARES_BONUS} coins por share ({3-shares_count} restantes)",
                    callback_data="share_bonus_info"
                )
            ])
        
        return InlineKeyboardMarkup(buttons)
    
    def _get_message_variant(self,
                            variant: str,
                            link: str,
                            user_id: int,
                            total_users: int = 5000) -> str:
        """
        Genera mensaje personalizado.
        
        Args:
            variant: Variante del template
            link: Link de referido
            user_id: ID del usuario
            total_users: Total de usuarios (para social proof)
        
        Returns:
            Mensaje formateado
        """
        template = MESSAGE_TEMPLATES.get(variant, MESSAGE_TEMPLATES['telegram_v1'])
        
        return template.format(
            link=link,
            user_count=total_users,
            referrer_name=f"User{user_id}"  # En producción usar username real
        )
    
    def track_share(self,
                   user_id: int,
                   platform: SharePlatform,
                   message_variant: str = 'telegram_v1') -> float:
        """
        Registra evento de compartir y otorga recompensa.
        
        Args:
            user_id: ID del usuario que comparte
            platform: Plataforma usada
            message_variant: Variante del mensaje
        
        Returns:
            Coins ganados
        """
        # Crear evento
        event = ShareEvent(
            user_id=user_id,
            platform=platform,
            timestamp=datetime.now().isoformat(),
            message_variant=message_variant
        )
        self.events.append(event)
        
        # Update stats
        if user_id not in self.stats:
            self.stats[user_id] = ShareStats(user_id=user_id)
        
        stats = self.stats[user_id]
        stats.total_shares += 1
        
        # Por plataforma
        platform_str = platform.value
        if platform_str not in stats.shares_by_platform:
            stats.shares_by_platform[platform_str] = 0
        stats.shares_by_platform[platform_str] += 1
        
        # Timestamps
        if not stats.first_share_at:
            stats.first_share_at = event.timestamp
        stats.last_share_at = event.timestamp
        
        # Calcular reward
        coins = SHARE_REWARD_COINS
        
        # Bonus primeros 3 shares
        if stats.total_shares <= 3:
            coins += FIRST_3_SHARES_BONUS
        
        stats.coins_earned += coins
        
        self._save_data()
        
        logger.info(
            f"📤 User {user_id} shared via {platform.value} "
            f"(+{coins} coins)"
        )
        
        return coins
    
    def track_conversion(self, share_event_id: int):
        """
        Registra conversión de un share.
        
        Args:
            share_event_id: ID del evento de share
        """
        if share_event_id >= len(self.events):
            return
        
        event = self.events[share_event_id]
        event.conversions += 1
        
        # Update stats
        stats = self.stats[event.user_id]
        stats.total_conversions += 1
        
        # Viral bonus si alcanza threshold
        if event.conversions >= VIRAL_SHARE_THRESHOLD and not event.is_viral:
            event.is_viral = True
            stats.viral_shares += 1
            stats.coins_earned += VIRAL_SHARE_BONUS
            
            logger.info(
                f"💥 VIRAL SHARE! User {event.user_id} earned "
                f"+{VIRAL_SHARE_BONUS} coins"
            )
        
        self._save_data()
    
    def get_user_stats(self, user_id: int) -> Optional[ShareStats]:
        """Obtiene stats de sharing del usuario."""
        return self.stats.get(user_id)
    
    def get_social_proof_message(self, total_users: int) -> str:
        """
        Genera mensaje de social proof.
        
        Args:
            total_users: Total de usuarios
        
        Returns:
            Mensaje formateado
        """
        import random
        template = random.choice(SOCIAL_PROOF_TEMPLATES)
        return template.format(count=total_users)
    
    def get_platform_performance(self) -> Dict[str, Dict]:
        """
        Analiza performance por plataforma.
        
        Returns:
            Dict con métricas por plataforma
        """
        platform_stats = {}
        
        for event in self.events:
            platform = event.platform.value
            
            if platform not in platform_stats:
                platform_stats[platform] = {
                    'shares': 0,
                    'conversions': 0,
                    'viral_shares': 0
                }
            
            platform_stats[platform]['shares'] += 1
            platform_stats[platform]['conversions'] += event.conversions
            if event.is_viral:
                platform_stats[platform]['viral_shares'] += 1
        
        # Calcular conversion rate
        for platform, stats in platform_stats.items():
            if stats['shares'] > 0:
                stats['conversion_rate'] = stats['conversions'] / stats['shares']
            else:
                stats['conversion_rate'] = 0.0
        
        return platform_stats


if __name__ == '__main__':
    # 🧪 Tests rápidos
    print("🧪 Testing SocialSharingManager...\n")
    
    mgr = SocialSharingManager('test_share_events.json', 'test_share_stats.json')
    
    # Test 1: Generate keyboard
    print("1. Generating share keyboard...")
    keyboard = mgr.generate_share_keyboard(
        "https://t.me/bot?start=ref_TEST123",
        12345
    )
    print(f"   Buttons: {len(keyboard.inline_keyboard)} rows\n")
    
    # Test 2: Track share
    print("2. Tracking share event...")
    coins = mgr.track_share(12345, SharePlatform.TELEGRAM)
    print(f"   Coins earned: {coins}\n")
    
    # Test 3: Track conversion
    print("3. Tracking conversion...")
    mgr.track_conversion(0)
    print("   Conversion recorded\n")
    
    # Test 4: Get stats
    print("4. Getting user stats...")
    stats = mgr.get_user_stats(12345)
    print(f"   Total shares: {stats.total_shares}")
    print(f"   Coins earned: {stats.coins_earned}\n")
    
    # Test 5: Platform performance
    print("5. Platform performance...")
    perf = mgr.get_platform_performance()
    for platform, data in perf.items():
        print(f"   {platform}: {data['shares']} shares, {data['conversion_rate']:.1%} conv")
    
    print("\n✅ All tests completed!")
