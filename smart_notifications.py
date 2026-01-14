#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
┌────────────────────────────────────────────────────────────────┐
│  🔔 SMART NOTIFICATIONS ENGINE                                 │
│  🚀 Cazador Supremo v13.0 Enterprise                          │
│  🎯 Target: 60% open rate, <5min latency                      │
└────────────────────────────────────────────────────────────────┘

Sistema inteligente de notificaciones que:
- Aprende mejores horas por usuario
- Monitoriza watchlist automáticamente
- Envía recordatorios de daily rewards
- Rate limiting anti-spam
- Priority queue para deals críticos

Autor: @Juanka_Spain
Version: 13.0.0
Date: 2026-01-14
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta, time as dt_time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import statistics

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
#  ENUMS & CONSTANTS
# ═══════════════════════════════════════════════════════════════

class NotificationType(Enum):
    """Tipos de notificaciones"""
    PRICE_DROP = "price_drop"              # Bajada de precio en watchlist
    DAILY_REWARD = "daily_reward"          # Recordatorio claim diario
    ACHIEVEMENT = "achievement"            # Logro desbloqueado
    STREAK_WARNING = "streak_warning"      # Racha en riesgo
    DEAL_RECOMMENDATION = "deal_rec"       # Deal personalizado
    LEVEL_UP = "level_up"                  # Subida de tier
    WATCHLIST_FULL = "watchlist_full"      # Watchlist llena


class Priority(Enum):
    """Prioridad de notificación"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


# Rate limiting
MAX_NOTIFICATIONS_PER_DAY = 3
PRICE_DROP_COOLDOWN = 3600  # 1 hora entre notifs de mismo deal
DIGEST_HOUR = 8  # 8am para morning digest
EVENING_HOUR = 20  # 8pm para evening summary
MIN_ENGAGEMENT_SAMPLES = 5  # Mínimo de interacciones para aprender patrón


# ═══════════════════════════════════════════════════════════════
#  DATA CLASSES
# ═══════════════════════════════════════════════════════════════

@dataclass
class NotificationEvent:
    """Evento de notificación"""
    user_id: int
    type: NotificationType
    priority: Priority
    message: str
    created_at: datetime
    metadata: Dict = field(default_factory=dict)
    sent: bool = False
    sent_at: Optional[datetime] = None
    opened: bool = False
    opened_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        return {
            'user_id': self.user_id,
            'type': self.type.value,
            'priority': self.priority.value,
            'message': self.message,
            'created_at': self.created_at.isoformat(),
            'metadata': self.metadata,
            'sent': self.sent,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'opened': self.opened,
            'opened_at': self.opened_at.isoformat() if self.opened_at else None,
        }


@dataclass
class UserEngagement:
    """Historial de engagement del usuario"""
    user_id: int
    interaction_times: List[datetime] = field(default_factory=list)
    notification_opens: List[datetime] = field(default_factory=list)
    optimal_hour: Optional[int] = None
    timezone_offset: int = 0  # Horas de diferencia con UTC
    
    def add_interaction(self, timestamp: datetime):
        """Registra interacción del usuario"""
        self.interaction_times.append(timestamp)
        # Mantener últimas 100 interacciones
        if len(self.interaction_times) > 100:
            self.interaction_times = self.interaction_times[-100:]
        self._recalculate_optimal_hour()
    
    def add_notification_open(self, timestamp: datetime):
        """Registra apertura de notificación"""
        self.notification_opens.append(timestamp)
        if len(self.notification_opens) > 50:
            self.notification_opens = self.notification_opens[-50:]
    
    def _recalculate_optimal_hour(self):
        """Recalcula hora óptima basada en historial"""
        if len(self.interaction_times) < MIN_ENGAGEMENT_SAMPLES:
            self.optimal_hour = DIGEST_HOUR  # Default
            return
        
        # Extraer horas de interacciones
        hours = [dt.hour for dt in self.interaction_times]
        
        # Calcular moda (hora más frecuente)
        hour_counts = defaultdict(int)
        for hour in hours:
            hour_counts[hour] += 1
        
        # Hora más común
        most_common_hour = max(hour_counts, key=hour_counts.get)
        
        # Enviar 5 minutos antes de la hora pico
        optimal = (most_common_hour - 1) % 24 if most_common_hour > 0 else 23
        self.optimal_hour = optimal
        
        logger.info(f"📊 User {self.user_id} optimal hour: {optimal}:00 (based on {len(hours)} interactions)")
    
    @property
    def engagement_rate(self) -> float:
        """Tasa de engagement (opens/sent)"""
        if not self.notification_opens:
            return 0.0
        return len(self.notification_opens) / max(len(self.interaction_times), 1)
    
    def to_dict(self) -> Dict:
        return {
            'user_id': self.user_id,
            'interaction_times': [dt.isoformat() for dt in self.interaction_times],
            'notification_opens': [dt.isoformat() for dt in self.notification_opens],
            'optimal_hour': self.optimal_hour,
            'timezone_offset': self.timezone_offset,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'UserEngagement':
        return cls(
            user_id=data['user_id'],
            interaction_times=[datetime.fromisoformat(dt) for dt in data.get('interaction_times', [])],
            notification_opens=[datetime.fromisoformat(dt) for dt in data.get('notification_opens', [])],
            optimal_hour=data.get('optimal_hour'),
            timezone_offset=data.get('timezone_offset', 0),
        )


# ═══════════════════════════════════════════════════════════════
#  SMART NOTIFIER
# ═══════════════════════════════════════════════════════════════

class SmartNotifier:
    """
    Motor inteligente de notificaciones.
    
    Responsabilidades:
    - Aprender patrones de uso por usuario
    - Calcular mejores horas para notificar
    - Rate limiting anti-spam
    - Priority queue para deals críticos
    - Watchlist monitoring
    - Daily reminders
    """
    
    def __init__(self, engagement_file: str = 'user_engagement.json'):
        self.engagement_file = Path(engagement_file)
        self.user_engagement: Dict[int, UserEngagement] = {}
        self.notification_queue: List[NotificationEvent] = []
        self.notifications_sent_today: Dict[int, int] = defaultdict(int)
        self.last_notification_time: Dict[Tuple[int, str], datetime] = {}
        self._load_engagement()
        
        logger.info(f"🔔 SmartNotifier initialized with {len(self.user_engagement)} user profiles")
    
    def _load_engagement(self):
        """Carga engagement history desde JSON"""
        if not self.engagement_file.exists():
            logger.warning(f"⚠️ Engagement file not found: {self.engagement_file}")
            return
        
        try:
            with open(self.engagement_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for user_id_str, engagement_data in data.items():
                user_id = int(user_id_str)
                self.user_engagement[user_id] = UserEngagement.from_dict(engagement_data)
            
            logger.info(f"✅ Loaded {len(self.user_engagement)} engagement profiles")
        
        except Exception as e:
            logger.error(f"❌ Error loading engagement: {e}")
    
    def _save_engagement(self):
        """Guarda engagement history a JSON"""
        try:
            data = {str(user_id): engagement.to_dict() 
                   for user_id, engagement in self.user_engagement.items()}
            
            with open(self.engagement_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"💾 Saved {len(self.user_engagement)} engagement profiles")
        
        except Exception as e:
            logger.error(f"❌ Error saving engagement: {e}")
    
    def track_user_activity(self, user_id: int, timestamp: datetime = None):
        """Registra actividad del usuario"""
        timestamp = timestamp or datetime.now()
        
        if user_id not in self.user_engagement:
            self.user_engagement[user_id] = UserEngagement(user_id=user_id)
        
        self.user_engagement[user_id].add_interaction(timestamp)
        self._save_engagement()
    
    def track_notification_open(self, user_id: int, timestamp: datetime = None):
        """Registra apertura de notificación"""
        timestamp = timestamp or datetime.now()
        
        if user_id in self.user_engagement:
            self.user_engagement[user_id].add_notification_open(timestamp)
            self._save_engagement()
    
    def get_optimal_send_time(self, user_id: int) -> int:
        """
        Obtiene hora óptima para notificar al usuario.
        
        Returns:
            int: Hora del día (0-23)
        """
        if user_id in self.user_engagement:
            optimal = self.user_engagement[user_id].optimal_hour
            if optimal is not None:
                return optimal
        
        # Default: 8am
        return DIGEST_HOUR
    
    def can_send_notification(self, user_id: int, notif_type: NotificationType) -> bool:
        """
        Verifica si se puede enviar notificación al usuario.
        
        Checks:
        - Rate limit diario
        - Cooldown por tipo
        
        Returns:
            bool: True si puede enviar
        """
        # Check daily limit
        if self.notifications_sent_today.get(user_id, 0) >= MAX_NOTIFICATIONS_PER_DAY:
            logger.debug(f"⛔ User {user_id} reached daily notification limit")
            return False
        
        # Check cooldown por tipo
        cooldown_key = (user_id, notif_type.value)
        if cooldown_key in self.last_notification_time:
            last_time = self.last_notification_time[cooldown_key]
            elapsed = (datetime.now() - last_time).seconds
            
            if elapsed < PRICE_DROP_COOLDOWN:
                logger.debug(f"⏱️ Cooldown active for user {user_id} type {notif_type.value}")
                return False
        
        return True
    
    def queue_notification(self, event: NotificationEvent) -> bool:
        """
        Encola notificación para envío.
        
        Returns:
            bool: True si encolada exitosamente
        """
        if not self.can_send_notification(event.user_id, event.type):
            return False
        
        self.notification_queue.append(event)
        
        # Sort por prioridad (CRITICAL primero)
        self.notification_queue.sort(key=lambda x: x.priority.value, reverse=True)
        
        logger.info(f"📬 Queued {event.type.value} notification for user {event.user_id} (priority: {event.priority.value})")
        return True
    
    async def send_notification(self, event: NotificationEvent, bot, chat_id: int) -> bool:
        """
        Envía notificación al usuario.
        
        Args:
            event: NotificationEvent
            bot: Telegram bot instance
            chat_id: Telegram chat ID
        
        Returns:
            bool: True si enviada exitosamente
        """
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=event.message,
                parse_mode='Markdown'
            )
            
            # Actualizar estado
            event.sent = True
            event.sent_at = datetime.now()
            
            # Update counters
            self.notifications_sent_today[event.user_id] += 1
            self.last_notification_time[(event.user_id, event.type.value)] = datetime.now()
            
            logger.info(f"✅ Sent {event.type.value} notification to user {event.user_id}")
            return True
        
        except Exception as e:
            logger.error(f"❌ Failed to send notification: {e}")
            return False
    
    async def process_queue(self, bot, get_chat_id_func):
        """
        Procesa cola de notificaciones.
        
        Args:
            bot: Telegram bot instance
            get_chat_id_func: Function(user_id) -> chat_id
        """
        if not self.notification_queue:
            return
        
        logger.info(f"📤 Processing {len(self.notification_queue)} queued notifications")
        
        sent_count = 0
        failed_count = 0
        
        # Process hasta 10 notificaciones por ciclo
        for _ in range(min(10, len(self.notification_queue))):
            if not self.notification_queue:
                break
            
            event = self.notification_queue.pop(0)
            
            # Obtener chat_id del usuario
            chat_id = get_chat_id_func(event.user_id)
            if not chat_id:
                failed_count += 1
                continue
            
            # Enviar
            success = await self.send_notification(event, bot, chat_id)
            if success:
                sent_count += 1
            else:
                failed_count += 1
            
            # Esperar 100ms entre envíos
            await asyncio.sleep(0.1)
        
        logger.info(f"📊 Sent: {sent_count}, Failed: {failed_count}, Remaining: {len(self.notification_queue)}")
    
    def create_price_drop_notification(self, user_id: int, route: str, 
                                      new_price: float, threshold: float) -> NotificationEvent:
        """Crea notificación de bajada de precio"""
        savings = threshold - new_price
        savings_pct = (savings / threshold) * 100
        
        message = (
            f"🔥 *¡ALERTA DE PRECIO!* 🔥\n\n"
            f"✈️ *Ruta:* {route}\n"
            f"💰 *Nuevo precio:* €{new_price:.0f}\n"
            f"📉 *Tu threshold:* €{threshold:.0f}\n"
            f"💵 *Ahorras:* €{savings:.0f} ({savings_pct:.0f}%)\n\n"
            f"_¡Reserva ahora antes que suba!_"
        )
        
        return NotificationEvent(
            user_id=user_id,
            type=NotificationType.PRICE_DROP,
            priority=Priority.HIGH,
            message=message,
            created_at=datetime.now(),
            metadata={'route': route, 'price': new_price, 'savings': savings}
        )
    
    def create_daily_reminder(self, user_id: int, streak: int) -> NotificationEvent:
        """Crea recordatorio de daily reward"""
        message = (
            f"☀️ *¡Buenos días!* ☀️\n\n"
            f"🎁 Tu reward diario te espera\n"
            f"🔥 Racha actual: {streak} días\n\n"
            f"Usa /daily para reclamar\n\n"
            f"_No pierdas tu racha 💪_"
        )
        
        return NotificationEvent(
            user_id=user_id,
            type=NotificationType.DAILY_REWARD,
            priority=Priority.MEDIUM,
            message=message,
            created_at=datetime.now(),
            metadata={'streak': streak}
        )
    
    def create_streak_warning(self, user_id: int, streak: int, hours_left: float) -> NotificationEvent:
        """Crea warning de racha en riesgo"""
        message = (
            f"⚠️ *¡TU RACHA ESTÁ EN RIESGO!* ⚠️\n\n"
            f"🔥 Racha actual: {streak} días\n"
            f"⏰ Tiempo restante: {hours_left:.1f} horas\n\n"
            f"Usa /daily para mantener tu racha\n\n"
            f"_¡No la pierdas ahora!_ 🙏"
        )
        
        return NotificationEvent(
            user_id=user_id,
            type=NotificationType.STREAK_WARNING,
            priority=Priority.CRITICAL,
            message=message,
            created_at=datetime.now(),
            metadata={'streak': streak, 'hours_left': hours_left}
        )
    
    def create_achievement_notification(self, user_id: int, achievement_name: str, 
                                       coins_earned: int) -> NotificationEvent:
        """Crea notificación de logro desbloqueado"""
        message = (
            f"🏆 *¡ACHIEVEMENT DESBLOQUEADO!* 🏆\n\n"
            f"🎯 *{achievement_name.replace('_', ' ').title()}*\n"
            f"💰 +{coins_earned} FlightCoins\n\n"
            f"Usa /profile para ver todos tus logros\n\n"
            f"_¡Sigue así campeón!_ 💪"
        )
        
        return NotificationEvent(
            user_id=user_id,
            type=NotificationType.ACHIEVEMENT,
            priority=Priority.MEDIUM,
            message=message,
            created_at=datetime.now(),
            metadata={'achievement': achievement_name, 'coins': coins_earned}
        )
    
    def reset_daily_counters(self):
        """Resetea contadores diarios (llamar a medianoche)"""
        self.notifications_sent_today.clear()
        logger.info("🔄 Daily notification counters reset")
    
    def get_stats(self) -> Dict:
        """Obtiene estadísticas del notifier"""
        total_users = len(self.user_engagement)
        avg_engagement = sum(e.engagement_rate for e in self.user_engagement.values()) / total_users if total_users > 0 else 0
        
        return {
            'total_users': total_users,
            'avg_engagement_rate': avg_engagement,
            'queued_notifications': len(self.notification_queue),
            'notifications_sent_today': sum(self.notifications_sent_today.values()),
        }


if __name__ == '__main__':
    # 🧪 Tests rápidos
    print("🧪 Testing SmartNotifier...\n")
    
    notifier = SmartNotifier('test_engagement.json')
    
    # Test 1: Track activity
    print("1. Tracking user activity...")
    notifier.track_user_activity(12345)
    notifier.track_user_activity(12345, datetime.now() - timedelta(hours=2))
    print(f"   Optimal hour: {notifier.get_optimal_send_time(12345)}:00\n")
    
    # Test 2: Create notifications
    print("2. Creating notifications...")
    notif1 = notifier.create_price_drop_notification(12345, 'MAD-MIA', 420, 500)
    notif2 = notifier.create_daily_reminder(12345, 5)
    print(f"   Created {notif1.type.value} notification")
    print(f"   Created {notif2.type.value} notification\n")
    
    # Test 3: Queue management
    print("3. Testing queue...")
    notifier.queue_notification(notif1)
    notifier.queue_notification(notif2)
    print(f"   Queue size: {len(notifier.notification_queue)}\n")
    
    # Test 4: Stats
    print("4. Stats:")
    stats = notifier.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\n✅ All tests completed!")
