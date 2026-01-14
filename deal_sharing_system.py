#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
┌────────────────────────────────────────────────────────────────┐
│  📤 DEAL SHARING SYSTEM - Social Amplification             │
│  🚀 Cazador Supremo v13.0 Enterprise                          │
│  🎯 Target: Share Rate >15% | Viral Reach 3x               │
└────────────────────────────────────────────────────────────────┘

Sistema para compartir deals socialmente:
- Share buttons con deep links
- Multi-platform templates
- Attribution tracking
- Share rewards
- Viral analytics

Autor: @Juanka_Spain
Version: 13.0.0
Date: 2026-01-14
"""

import json
import logging
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from urllib.parse import quote

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
#  CONSTANTS & ENUMS
# ═══════════════════════════════════════════════════════════════

class SharePlatform(Enum):
    """Plataformas para compartir"""
    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"
    TWITTER = "twitter"
    FACEBOOK = "facebook"
    EMAIL = "email"
    COPY_LINK = "copy_link"


class ShareEventType(Enum):
    """Tipos de eventos de share"""
    CREATED = "created"      # Share link creado
    CLICKED = "clicked"      # Link clickeado
    CONVERTED = "converted"  # Usuario se registró
    USED = "used"            # Deal usado


# Rewards
SHARE_REWARDS = {
    'share_created': 50,     # Coins por compartir
    'share_clicked': 0,      # No reward por click
    'share_converted': 100,  # Bonus si se registra
    'share_used': 200,       # Bonus si usa el deal
    'viral_multiplier': 500, # Bonus si 5+ clicks
    'share_10_bonus': 500    # Bonus por 10 shares
}

# Deep link config
BOT_USERNAME = "CazadorSupremoBot"  # Cambiar por tu bot
DEEP_LINK_EXPIRY_DAYS = 7


# ═══════════════════════════════════════════════════════════════
#  DATA CLASSES
# ═══════════════════════════════════════════════════════════════

@dataclass
class SharedDeal:
    """Deal compartido"""
    share_id: str              # ID único del share
    deal_id: str               # ID del deal original
    sharer_id: int             # Usuario que comparte
    sharer_username: str
    
    # Deal info
    route: str                 # ej: MAD-MIA
    price: float
    savings: float
    
    # Tracking
    created_at: str
    expires_at: str
    
    # Stats
    total_clicks: int = 0
    unique_clicks: int = 0
    conversions: int = 0
    deals_used: int = 0
    
    # Rewards
    coins_earned: int = 0
    
    # Metadata
    platform: Optional[SharePlatform] = None
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        if self.platform:
            data['platform'] = self.platform.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'SharedDeal':
        if data.get('platform'):
            data['platform'] = SharePlatform(data['platform'])
        return cls(**data)


@dataclass
class ShareEvent:
    """Evento de share"""
    event_type: ShareEventType
    share_id: str
    user_id: Optional[int]      # Usuario que interactúa
    timestamp: str
    
    # Metadata
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            **asdict(self),
            'event_type': self.event_type.value
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ShareEvent':
        data['event_type'] = ShareEventType(data['event_type'])
        return cls(**data)


@dataclass
class ShareStats:
    """Estadísticas de shares por usuario"""
    user_id: int
    
    # Contadores
    total_shares: int = 0
    total_clicks: int = 0
    total_conversions: int = 0
    total_deals_used: int = 0
    
    # Rewards
    total_coins_earned: int = 0
    
    # Achievements
    share_master_unlocked: bool = False
    viral_champion_unlocked: bool = False
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ShareStats':
        return cls(**data)


# ═══════════════════════════════════════════════════════════════
#  DEAL SHARE MANAGER
# ═══════════════════════════════════════════════════════════════

class DealShareManager:
    """
    Gestor del sistema de compartir deals.
    
    Responsabilidades:
    - Crear share links
    - Track eventos
    - Distribuir rewards
    - Analytics
    """
    
    def __init__(self,
                 shares_file: str = 'shared_deals.json',
                 events_file: str = 'share_events.json',
                 stats_file: str = 'share_stats.json'):
        self.shares_file = Path(shares_file)
        self.events_file = Path(events_file)
        self.stats_file = Path(stats_file)
        
        # Data structures
        self.shares: Dict[str, SharedDeal] = {}    # share_id -> SharedDeal
        self.events: List[ShareEvent] = []
        self.stats: Dict[int, ShareStats] = {}     # user_id -> ShareStats
        
        self._load_data()
        
        logger.info("📤 DealShareManager initialized")
    
    def _load_data(self):
        """Carga datos desde archivos."""
        # Load shares
        if self.shares_file.exists():
            try:
                with open(self.shares_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for share_id, share_data in data.items():
                    self.shares[share_id] = SharedDeal.from_dict(share_data)
                
                logger.info(f"✅ Loaded {len(self.shares)} shared deals")
            except Exception as e:
                logger.error(f"❌ Error loading shares: {e}")
        
        # Load events
        if self.events_file.exists():
            try:
                with open(self.events_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.events = [ShareEvent.from_dict(e) for e in data]
                
                logger.info(f"✅ Loaded {len(self.events)} share events")
            except Exception as e:
                logger.error(f"❌ Error loading events: {e}")
        
        # Load stats
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
            # Save shares
            with open(self.shares_file, 'w', encoding='utf-8') as f:
                data = {sid: share.to_dict() for sid, share in self.shares.items()}
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Save events
            with open(self.events_file, 'w', encoding='utf-8') as f:
                data = [e.to_dict() for e in self.events]
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Save stats
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                data = {str(uid): stats.to_dict() for uid, stats in self.stats.items()}
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.debug("💾 Share data saved")
        except Exception as e:
            logger.error(f"❌ Error saving data: {e}")
    
    def _generate_share_id(self, deal_id: str, user_id: int) -> str:
        """Genera ID único para share."""
        timestamp = datetime.now().isoformat()
        raw = f"{deal_id}_{user_id}_{timestamp}"
        return hashlib.md5(raw.encode()).hexdigest()[:12]
    
    def create_share(self,
                    deal_id: str,
                    user_id: int,
                    username: str,
                    route: str,
                    price: float,
                    savings: float,
                    platform: Optional[SharePlatform] = None) -> SharedDeal:
        """
        Crea nuevo share de un deal.
        
        Returns:
            SharedDeal con deep link generado
        """
        share_id = self._generate_share_id(deal_id, user_id)
        
        # Create shared deal
        shared_deal = SharedDeal(
            share_id=share_id,
            deal_id=deal_id,
            sharer_id=user_id,
            sharer_username=username,
            route=route,
            price=price,
            savings=savings,
            created_at=datetime.now().isoformat(),
            expires_at=(datetime.now() + timedelta(days=DEEP_LINK_EXPIRY_DAYS)).isoformat(),
            platform=platform
        )
        
        self.shares[share_id] = shared_deal
        
        # Track event
        self._track_event(
            ShareEventType.CREATED,
            share_id,
            user_id
        )
        
        # Update stats
        if user_id not in self.stats:
            self.stats[user_id] = ShareStats(user_id=user_id)
        self.stats[user_id].total_shares += 1
        
        # Award coins
        coins = SHARE_REWARDS['share_created']
        self.stats[user_id].total_coins_earned += coins
        shared_deal.coins_earned += coins
        
        # Check bonus
        if self.stats[user_id].total_shares >= 10:
            if not self.stats[user_id].share_master_unlocked:
                bonus = SHARE_REWARDS['share_10_bonus']
                self.stats[user_id].total_coins_earned += bonus
                self.stats[user_id].share_master_unlocked = True
                logger.info(f"🏆 User {user_id} unlocked Share Master: +{bonus} coins")
        
        self._save_data()
        
        logger.info(
            f"📤 Share created: {share_id} by {username} for {route} @ €{price:.0f}"
        )
        
        return shared_deal
    
    def get_deep_link(self, share_id: str) -> str:
        """Genera deep link para share."""
        return f"https://t.me/{BOT_USERNAME}?start=deal_{share_id}"
    
    def get_share_message(self,
                         shared_deal: SharedDeal,
                         platform: SharePlatform) -> str:
        """
        Genera mensaje optimizado por plataforma.
        
        Args:
            shared_deal: Deal compartido
            platform: Plataforma destino
        
        Returns:
            Mensaje formateado
        """
        link = self.get_deep_link(shared_deal.share_id)
        
        if platform == SharePlatform.WHATSAPP:
            return (
                f"✈️ *¡CHOLLO DE VUELO!* ✈️\n\n"
                f"📍 {shared_deal.route}\n"
                f"💰 Precio: €{shared_deal.price:.0f}\n"
                f"💸 Ahorro: €{shared_deal.savings:.0f}\n\n"
                f"👉 Ver deal: {link}\n\n"
                f"_Compartido por @{shared_deal.sharer_username}_"
            )
        
        elif platform == SharePlatform.TELEGRAM:
            return (
                f"🚨 *¡DEAL ENCONTRADO!* 🚨\n\n"
                f"✈️ Ruta: *{shared_deal.route}*\n"
                f"💰 Precio: *€{shared_deal.price:.0f}*\n"
                f"💸 Ahorro: *€{shared_deal.savings:.0f}* ({(shared_deal.savings/shared_deal.price*100):.0f}%)\n\n"
                f"👉 [Ver y reservar]({link})\n\n"
                f"👤 Compartido por @{shared_deal.sharer_username}\n"
                f"_Encuentra más chollos con @{BOT_USERNAME}_"
            )
        
        elif platform == SharePlatform.TWITTER:
            hashtags = "#Vuelos #Chollos #Viajes"
            savings_pct = (shared_deal.savings / shared_deal.price * 100)
            return (
                f"✈️ ¡{shared_deal.route} por solo €{shared_deal.price:.0f}! "
                f"Ahorra {savings_pct:.0f}% (€{shared_deal.savings:.0f}) \n\n"
                f"{link}\n\n"
                f"{hashtags}"
            )
        
        elif platform == SharePlatform.EMAIL:
            return (
                f"Hola,\n\n"
                f"He encontrado un chollo de vuelo que te puede interesar:\n\n"
                f"Ruta: {shared_deal.route}\n"
                f"Precio: €{shared_deal.price:.0f}\n"
                f"Ahorro: €{shared_deal.savings:.0f}\n\n"
                f"Ver deal completo: {link}\n\n"
                f"Saludos,\n"
                f"@{shared_deal.sharer_username}"
            )
        
        else:  # COPY_LINK / DEFAULT
            return link
    
    def get_whatsapp_share_url(self, share_id: str) -> str:
        """Genera URL de WhatsApp para compartir."""
        shared_deal = self.shares.get(share_id)
        if not shared_deal:
            return ""
        
        message = self.get_share_message(shared_deal, SharePlatform.WHATSAPP)
        encoded = quote(message)
        return f"https://wa.me/?text={encoded}"
    
    def _track_event(self,
                    event_type: ShareEventType,
                    share_id: str,
                    user_id: Optional[int] = None,
                    ip_address: Optional[str] = None,
                    user_agent: Optional[str] = None):
        """Registra evento de share."""
        event = ShareEvent(
            event_type=event_type,
            share_id=share_id,
            user_id=user_id,
            timestamp=datetime.now().isoformat(),
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.events.append(event)
    
    def track_click(self,
                   share_id: str,
                   user_id: Optional[int] = None,
                   ip_address: Optional[str] = None) -> bool:
        """
        Registra click en share link.
        
        Returns:
            True si es válido, False si expirado
        """
        if share_id not in self.shares:
            return False
        
        shared_deal = self.shares[share_id]
        
        # Check expiry
        if datetime.now() > datetime.fromisoformat(shared_deal.expires_at):
            return False
        
        # Update stats
        shared_deal.total_clicks += 1
        
        # Track unique
        # (simplificado - en producción usar set de user_ids)
        if user_id:
            shared_deal.unique_clicks += 1
        
        # Track event
        self._track_event(
            ShareEventType.CLICKED,
            share_id,
            user_id,
            ip_address=ip_address
        )
        
        # Update sharer stats
        sharer_id = shared_deal.sharer_id
        if sharer_id in self.stats:
            self.stats[sharer_id].total_clicks += 1
        
        # Check viral multiplier (5+ clicks)
        if shared_deal.total_clicks >= 5:
            if shared_deal.coins_earned < SHARE_REWARDS['viral_multiplier'] + SHARE_REWARDS['share_created']:
                bonus = SHARE_REWARDS['viral_multiplier']
                shared_deal.coins_earned += bonus
                self.stats[sharer_id].total_coins_earned += bonus
                logger.info(f"🚀 Viral multiplier for share {share_id}: +{bonus} coins")
        
        self._save_data()
        
        return True
    
    def track_conversion(self,
                        share_id: str,
                        user_id: int,
                        retention_manager) -> int:
        """
        Registra conversión (usuario se registra vía share).
        
        Returns:
            Coins otorgados al sharer
        """
        if share_id not in self.shares:
            return 0
        
        shared_deal = self.shares[share_id]
        shared_deal.conversions += 1
        
        # Track event
        self._track_event(
            ShareEventType.CONVERTED,
            share_id,
            user_id
        )
        
        # Award coins
        sharer_id = shared_deal.sharer_id
        coins = SHARE_REWARDS['share_converted']
        
        retention_manager.add_coins(
            sharer_id,
            coins,
            reason=f"Conversión de share: @{user_id}"
        )
        
        shared_deal.coins_earned += coins
        
        # Update stats
        if sharer_id in self.stats:
            self.stats[sharer_id].total_conversions += 1
            self.stats[sharer_id].total_coins_earned += coins
        
        self._save_data()
        
        logger.info(f"🎉 Conversion tracked for share {share_id}: +{coins} coins")
        
        return coins
    
    def get_user_stats(self, user_id: int) -> Optional[ShareStats]:
        """Obtiene stats de shares del usuario."""
        return self.stats.get(user_id)
    
    def get_viral_metrics(self) -> Dict:
        """Obtiene métricas virales globales."""
        total_shares = len(self.shares)
        total_clicks = sum(s.total_clicks for s in self.shares.values())
        total_conversions = sum(s.conversions for s in self.shares.values())
        
        share_rate = 0
        ctr = 0
        conversion_rate = 0
        
        if total_shares > 0:
            # Simplificado - en producción calcular vs total users
            share_rate = total_shares / 100  # placeholder
            
            if total_shares > 0:
                ctr = total_clicks / total_shares
            
            if total_clicks > 0:
                conversion_rate = total_conversions / total_clicks
        
        return {
            'total_shares': total_shares,
            'total_clicks': total_clicks,
            'total_conversions': total_conversions,
            'share_rate': share_rate * 100,  # percentage
            'ctr': ctr * 100,                # percentage
            'conversion_rate': conversion_rate * 100,  # percentage
            'viral_reach': total_clicks / max(total_shares, 1)  # avg reach per share
        }


if __name__ == '__main__':
    # 🧪 Tests rápidos
    print("🧪 Testing DealShareManager...\n")
    
    mgr = DealShareManager('test_shares.json', 'test_events.json', 'test_share_stats.json')
    
    # Test 1: Create share
    print("1. Creating share...")
    share = mgr.create_share(
        deal_id="deal_123",
        user_id=12345,
        username="juan",
        route="MAD-MIA",
        price=420,
        savings=180,
        platform=SharePlatform.TELEGRAM
    )
    print(f"   Share ID: {share.share_id}\n")
    
    # Test 2: Generate deep link
    print("2. Generating deep link...")
    link = mgr.get_deep_link(share.share_id)
    print(f"   Link: {link}\n")
    
    # Test 3: Generate message
    print("3. Generating share message...")
    message = mgr.get_share_message(share, SharePlatform.TELEGRAM)
    print(f"   Message:\n{message}\n")
    
    # Test 4: Track click
    print("4. Tracking click...")
    success = mgr.track_click(share.share_id, user_id=67890)
    print(f"   Success: {success}")
    print(f"   Total clicks: {mgr.shares[share.share_id].total_clicks}\n")
    
    # Test 5: Viral metrics
    print("5. Getting viral metrics...")
    metrics = mgr.get_viral_metrics()
    print(f"   Total shares: {metrics['total_shares']}")
    print(f"   Viral reach: {metrics['viral_reach']:.1f}x\n")
    
    print("✅ All tests completed!")
