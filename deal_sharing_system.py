#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Deal Sharing System - IT5 Day 2/5
Sistema de compartir chollos con links únicos y analytics

Author: @Juanka_Spain
Version: 13.1.0
Date: 2026-01-15
"""

import json
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from urllib.parse import urlencode


@dataclass
class Deal:
    """Representa un chollo de vuelo"""
    deal_id: str
    route: str
    origin: str
    destination: str
    price: float
    currency: str
    airline: str
    departure_date: str
    return_date: Optional[str]
    url: str
    created_at: str
    expires_at: str
    savings_pct: float
    

@dataclass
class ShareLink:
    """Link único para compartir un deal"""
    link_id: str
    deal_id: str
    sharer_id: int
    sharer_username: str
    short_code: str
    full_url: str
    created_at: str
    clicks: int = 0
    conversions: int = 0  # Usuarios que usaron el bot tras el click
    rewards_earned: int = 0


@dataclass
class ShareEvent:
    """Evento de compartir un deal"""
    event_id: str
    link_id: str
    deal_id: str
    sharer_id: int
    platform: str  # telegram, whatsapp, twitter, facebook, copy
    timestamp: str
    clicked_by: Optional[int] = None
    converted: bool = False


class DealSharingManager:
    """
    Gestor del sistema de compartir chollos.
    
    Features:
    - Botones de share por deal
    - Links únicos rastreables
    - Deep links para Telegram
    - Analytics de viralidad
    - Recompensas por compartir
    """
    
    def __init__(self, data_dir: str = ".", bot_username: str = "VuelosRobot"):
        self.data_dir = Path(data_dir)
        self.bot_username = bot_username
        self.deals_file = self.data_dir / "shared_deals.json"
        self.links_file = self.data_dir / "share_links.json"
        self.events_file = self.data_dir / "share_events.json"
        self.analytics_file = self.data_dir / "share_analytics.json"
        
        self.deals: Dict[str, Deal] = {}
        self.links: Dict[str, ShareLink] = {}
        self.events: List[ShareEvent] = []
        self.analytics: Dict = self._init_analytics()
        
        self._load_data()
    
    def _init_analytics(self) -> Dict:
        """Inicializa estructura de analytics"""
        return {
            "total_deals_shared": 0,
            "total_shares": 0,
            "total_clicks": 0,
            "total_conversions": 0,
            "click_through_rate": 0.0,
            "conversion_rate": 0.0,
            "viral_reach": 0,
            "top_sharers": [],
            "platform_breakdown": {},
            "most_shared_deals": [],
            "last_updated": datetime.now().isoformat()
        }
    
    def _load_data(self):
        """Carga datos desde archivos JSON"""
        if self.deals_file.exists():
            with open(self.deals_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.deals = {k: Deal(**v) for k, v in data.items()}
        
        if self.links_file.exists():
            with open(self.links_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.links = {k: ShareLink(**v) for k, v in data.items()}
        
        if self.events_file.exists():
            with open(self.events_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.events = [ShareEvent(**item) for item in data]
        
        if self.analytics_file.exists():
            with open(self.analytics_file, 'r', encoding='utf-8') as f:
                self.analytics = json.load(f)
    
    def _save_data(self):
        """Guarda datos en archivos JSON"""
        with open(self.deals_file, 'w', encoding='utf-8') as f:
            data = {k: asdict(v) for k, v in self.deals.items()}
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        with open(self.links_file, 'w', encoding='utf-8') as f:
            data = {k: asdict(v) for k, v in self.links.items()}
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        with open(self.events_file, 'w', encoding='utf-8') as f:
            data = [asdict(e) for e in self.events]
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        with open(self.analytics_file, 'w', encoding='utf-8') as f:
            json.dump(self.analytics, f, indent=2, ensure_ascii=False)
    
    def create_deal(self, **kwargs) -> Deal:
        """
        Crea un nuevo deal para compartir.
        """
        deal_id = hashlib.md5(
            f"{kwargs['route']}{kwargs['price']}{datetime.now()}".encode()
        ).hexdigest()[:12]
        
        deal = Deal(
            deal_id=deal_id,
            route=kwargs['route'],
            origin=kwargs['origin'],
            destination=kwargs['destination'],
            price=kwargs['price'],
            currency=kwargs.get('currency', 'EUR'),
            airline=kwargs['airline'],
            departure_date=kwargs['departure_date'],
            return_date=kwargs.get('return_date'),
            url=kwargs['url'],
            created_at=datetime.now().isoformat(),
            expires_at=(datetime.now() + timedelta(days=3)).isoformat(),
            savings_pct=kwargs.get('savings_pct', 0)
        )
        
        self.deals[deal_id] = deal
        self._save_data()
        
        return deal
    
    def generate_share_link(
        self, 
        deal_id: str, 
        sharer_id: int, 
        sharer_username: str
    ) -> ShareLink:
        """
        Genera un link único para compartir un deal.
        
        Formato del deep link:
        https://t.me/{bot_username}?start=deal_{short_code}
        """
        if deal_id not in self.deals:
            raise ValueError(f"Deal {deal_id} no existe")
        
        # Generar short code único
        short_code = secrets.token_urlsafe(8)
        link_id = f"{deal_id}_{sharer_id}_{short_code}"
        
        # Crear deep link de Telegram
        full_url = f"https://t.me/{self.bot_username}?start=deal_{short_code}"
        
        share_link = ShareLink(
            link_id=link_id,
            deal_id=deal_id,
            sharer_id=sharer_id,
            sharer_username=sharer_username,
            short_code=short_code,
            full_url=full_url,
            created_at=datetime.now().isoformat()
        )
        
        self.links[link_id] = share_link
        self._save_data()
        
        return share_link
    
    def create_share_buttons(self, deal_id: str, user_id: int) -> List[Dict]:
        """
        Crea botones de compartir para un deal.
        
        Returns:
            Lista de botones en formato Telegram InlineKeyboard
        """
        if deal_id not in self.deals:
            return []
        
        deal = self.deals[deal_id]
        
        # Generar link único para este usuario
        share_link = self.generate_share_link(
            deal_id=deal_id,
            sharer_id=user_id,
            sharer_username=f"user_{user_id}"
        )
        
        # Texto para compartir
        share_text = (
            f"🔥 ¡CHOLLO! {deal.route}\n"
            f"✈️ {deal.airline}\n"
            f"💰 {deal.price}{deal.currency} (-{deal.savings_pct:.0f}%)\n"
            f"📅 {deal.departure_date}\n\n"
            f"¡Mira este chollo que encontré! 🚀"
        )
        
        buttons = [
            [
                {
                    "text": "📱 Compartir en Telegram",
                    "url": f"https://t.me/share/url?url={share_link.full_url}&text={share_text}"
                }
            ],
            [
                {
                    "text": "💚 WhatsApp",
                    "url": f"https://wa.me/?text={share_text}%0A{share_link.full_url}"
                },
                {
                    "text": "🐦 Twitter",
                    "url": f"https://twitter.com/intent/tweet?text={share_text}&url={share_link.full_url}"
                }
            ],
            [
                {
                    "text": "🔗 Copiar Link",
                    "callback_data": f"copy_link:{share_link.link_id}"
                }
            ]
        ]
        
        return buttons
    
    def track_share_event(
        self,
        link_id: str,
        platform: str,
        clicked_by: Optional[int] = None
    ) -> ShareEvent:
        """
        Registra un evento de compartir.
        
        Platforms: telegram, whatsapp, twitter, facebook, copy
        """
        if link_id not in self.links:
            raise ValueError(f"Link {link_id} no existe")
        
        share_link = self.links[link_id]
        
        event_id = hashlib.md5(
            f"{link_id}{platform}{datetime.now()}".encode()
        ).hexdigest()[:12]
        
        event = ShareEvent(
            event_id=event_id,
            link_id=link_id,
            deal_id=share_link.deal_id,
            sharer_id=share_link.sharer_id,
            platform=platform,
            timestamp=datetime.now().isoformat(),
            clicked_by=clicked_by
        )
        
        self.events.append(event)
        self.analytics["total_shares"] += 1
        
        # Update platform breakdown
        if platform not in self.analytics["platform_breakdown"]:
            self.analytics["platform_breakdown"][platform] = 0
        self.analytics["platform_breakdown"][platform] += 1
        
        self._save_data()
        self._update_analytics()
        
        return event
    
    def track_click(self, short_code: str, clicked_by: int) -> Tuple[bool, Optional[Deal]]:
        """
        Registra un click en un link compartido.
        
        Returns:
            (success, deal)
        """
        # Buscar link por short_code
        link = None
        for l in self.links.values():
            if l.short_code == short_code:
                link = l
                break
        
        if not link:
            return False, None
        
        # Incrementar clicks
        link.clicks += 1
        self.analytics["total_clicks"] += 1
        
        # Obtener deal
        deal = self.deals.get(link.deal_id)
        
        self._save_data()
        self._update_analytics()
        
        return True, deal
    
    def track_conversion(self, short_code: str, converted_user_id: int) -> bool:
        """
        Registra una conversión (usuario empezó a usar el bot).
        """
        # Buscar link
        link = None
        for l in self.links.values():
            if l.short_code == short_code:
                link = l
                break
        
        if not link:
            return False
        
        # Incrementar conversions
        link.conversions += 1
        self.analytics["total_conversions"] += 1
        
        # Recompensar al sharer
        reward_coins = 50  # 50 coins por conversion
        link.rewards_earned += reward_coins
        
        self._save_data()
        self._update_analytics()
        
        return True
    
    def get_user_share_stats(self, user_id: int) -> Dict:
        """
        Obtiene estadísticas de shares de un usuario.
        """
        user_links = [
            link for link in self.links.values() 
            if link.sharer_id == user_id
        ]
        
        total_clicks = sum(link.clicks for link in user_links)
        total_conversions = sum(link.conversions for link in user_links)
        total_rewards = sum(link.rewards_earned for link in user_links)
        
        # Calcular CTR
        total_shares = len([
            e for e in self.events 
            if e.sharer_id == user_id
        ])
        
        ctr = (total_clicks / total_shares * 100) if total_shares > 0 else 0
        conv_rate = (total_conversions / total_clicks * 100) if total_clicks > 0 else 0
        
        return {
            "total_deals_shared": len(user_links),
            "total_shares": total_shares,
            "total_clicks": total_clicks,
            "total_conversions": total_conversions,
            "total_rewards_earned": total_rewards,
            "click_through_rate": ctr,
            "conversion_rate": conv_rate,
            "viral_reach": total_clicks + total_conversions
        }
    
    def _update_analytics(self):
        """Actualiza métricas globales"""
        total_shares = len(self.events)
        total_clicks = self.analytics["total_clicks"]
        total_conversions = self.analytics["total_conversions"]
        
        # CTR y Conversion Rate
        if total_shares > 0:
            self.analytics["click_through_rate"] = (
                total_clicks / total_shares * 100
            )
        
        if total_clicks > 0:
            self.analytics["conversion_rate"] = (
                total_conversions / total_clicks * 100
            )
        
        # Viral reach
        self.analytics["viral_reach"] = total_clicks + total_conversions
        
        # Top sharers
        sharer_stats = {}
        for link in self.links.values():
            username = link.sharer_username
            if username not in sharer_stats:
                sharer_stats[username] = {
                    "shares": 0,
                    "clicks": 0,
                    "conversions": 0
                }
            sharer_stats[username]["shares"] += 1
            sharer_stats[username]["clicks"] += link.clicks
            sharer_stats[username]["conversions"] += link.conversions
        
        self.analytics["top_sharers"] = sorted(
            [
                {"username": k, **v}
                for k, v in sharer_stats.items()
            ],
            key=lambda x: x["conversions"],
            reverse=True
        )[:10]
        
        # Most shared deals
        deal_shares = {}
        for event in self.events:
            deal_id = event.deal_id
            if deal_id not in deal_shares:
                deal_shares[deal_id] = 0
            deal_shares[deal_id] += 1
        
        self.analytics["most_shared_deals"] = sorted(
            [
                {
                    "deal_id": k,
                    "route": self.deals[k].route if k in self.deals else "Unknown",
                    "shares": v
                }
                for k, v in deal_shares.items()
            ],
            key=lambda x: x["shares"],
            reverse=True
        )[:10]
        
        self.analytics["last_updated"] = datetime.now().isoformat()
    
    def get_global_analytics(self) -> Dict:
        """Retorna analytics globales"""
        return self.analytics
    
    def cleanup_expired_deals(self) -> int:
        """
        Limpia deals expirados.
        
        Returns:
            Número de deals eliminados
        """
        now = datetime.now()
        expired_count = 0
        
        for deal_id in list(self.deals.keys()):
            deal = self.deals[deal_id]
            expires_at = datetime.fromisoformat(deal.expires_at)
            
            if now > expires_at:
                del self.deals[deal_id]
                expired_count += 1
        
        if expired_count > 0:
            self._save_data()
        
        return expired_count


if __name__ == "__main__":
    # Testing
    print("🚀 Testing Deal Sharing System...")
    
    manager = DealSharingManager(bot_username="VuelosRobot")
    
    # Crear deal
    deal = manager.create_deal(
        route="MAD-MIA",
        origin="MAD",
        destination="MIA",
        price=450.0,
        currency="EUR",
        airline="Iberia",
        departure_date="2026-03-15",
        return_date="2026-03-22",
        url="https://example.com/book",
        savings_pct=25
    )
    
    print(f"\n✅ Deal creado: {deal.deal_id}")
    print(f"   Ruta: {deal.route}")
    print(f"   Precio: {deal.price}{deal.currency}")
    
    # Generar share link
    share_link = manager.generate_share_link(
        deal_id=deal.deal_id,
        sharer_id=12345,
        sharer_username="john_doe"
    )
    
    print(f"\n🔗 Share link generado:")
    print(f"   Short code: {share_link.short_code}")
    print(f"   URL: {share_link.full_url}")
    
    # Crear botones
    buttons = manager.create_share_buttons(deal.deal_id, 12345)
    print(f"\n🔘 Botones creados: {len(buttons)} filas")
    
    # Simular share
    event = manager.track_share_event(
        link_id=share_link.link_id,
        platform="telegram"
    )
    print(f"\n✅ Share event tracked: {event.event_id}")
    
    # Simular click
    success, clicked_deal = manager.track_click(
        short_code=share_link.short_code,
        clicked_by=67890
    )
    print(f"\n👆 Click tracked: {success}")
    
    # Stats
    stats = manager.get_user_share_stats(12345)
    print(f"\n📊 Stats de john_doe:")
    print(f"   Deals compartidos: {stats['total_deals_shared']}")
    print(f"   Total clicks: {stats['total_clicks']}")
    print(f"   CTR: {stats['click_through_rate']:.1f}%")
    
    print("\n✅ Tests completados!")
