#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
┌────────────────────────────────────────────────────────────────┐
│  🔔 SMART NOTIFICATIONS ENGINE                             │
│  🚀 Cazador Supremo v13.0 Enterprise                          │
│  🧠 AI-Powered Personalized Notifications                    │
└────────────────────────────────────────────────────────────────┘

Sistema inteligente de notificaciones con:
- Optimal send time learning
- Watchlist monitoring
- Daily reminders
- Rate limiting
- Priority queue

Autor: @Juanka_Spain
Version: 13.0.0
Date: 2026-01-14
"""

import asyncio
import logging
from datetime import datetime, timedelta, time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path
from collections import defaultdict

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
#  ENUMS & CONSTANTS
# ═══════════════════════════════════════════════════════════════

class NotificationPriority(Enum):
    """Prioridad de notificaciones"""
    CRITICAL = 1   # Price drop watchlist
    HIGH = 2       # Daily reminder
    MEDIUM = 3     # Weekly summary
    LOW = 4        # Tips & tricks


class NotificationType(Enum):
    """Tipos de notificaciones"""
    PRICE_DROP = "price_drop"
    DAILY_REMINDER = "daily_reminder"
    WEEKLY_SUMMARY = "weekly_summary"
    ACHIEVEMENT = "achievement"
    TIER_UPGRADE = "tier_upgrade"
    DEAL_FOUND = "deal_found"
    TIP = "tip"


# Rate limiting
RATE_LIMIT_FREE = 3      # Max notificaciones/día (free tier)
RATE_LIMIT_PREMIUM = 10  # Max notificaciones/día (premium)

# Quiet hours
QUIET_START = time(22, 0)  # 22:00
QUIET_END = time(8, 0)     # 08:00

# Monitoring intervals
WATCHLIST_CHECK_INTERVAL = 1800  # 30 minutos
DAILY_REMINDER_TIME = time(9, 0)  # 09:00 por defecto

# Cooldowns
PRICE_DROP_COOLDOWN = 3600       # 1 hora entre alerts del mismo vuelo
DAILY_REMINDER_COOLDOWN = 86400  # 1 día


# ═══════════════════════════════════════════════════════════════
#  DATA CLASSES
# ═══════════════════════════════════════════════════════════════

@dataclass
class Notification:
    """Notificación pendiente de enviar"""
    user_id: int
    type: NotificationType
    priority: NotificationPriority
    message: str
    created_at: datetime
    scheduled_for: Optional[datetime] = None
    metadata: Dict = field(default_factory=dict)
    sent: bool = False
    sent_at: Optional[datetime] = None
    
    def is_ready(self) -> bool:
        """Verifica si está lista para enviar."""
        if self.sent:
            return False
        
        if self.scheduled_for:
            return datetime.now() >= self.scheduled_for
        
        return True
    
    def to_dict(self) -> Dict:
        return {
            'user_id': self.user_id,
            'type': self.type.value,
            'priority': self.priority.value,
            'message': self.message,
            'created_at': self.created_at.isoformat(),
            'scheduled_for': self.scheduled_for.isoformat() if self.scheduled_for else None,
            'metadata': self.metadata,
            'sent': self.sent,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None
        }


@dataclass
class UserActivity:
    """Actividad del usuario para analytics"""
    user_id: int
    activity_times: List[datetime] = field(default_factory=list)
    
    def add_activity(self, timestamp: datetime):
        """Registra actividad."""
        self.activity_times.append(timestamp)
        # Mantener solo últimos 30 días
        cutoff = datetime.now() - timedelta(days=30)
        self.activity_times = [t for t in self.activity_times if t >= cutoff]
    
    def get_peak_hour(self) -> int:
        """Calcula hora pico de actividad (0-23)."""
        if not self.activity_times:
            return 9  # Default 9am
        
        hour_counts = defaultdict(int)
        for timestamp in self.activity_times:
            hour_counts[timestamp.hour] += 1
        
        return max(hour_counts.items(), key=lambda x: x[1])[0]
    
    def get_optimal_send_time(self) -> time:
        """Calcula mejor hora para enviar notificaciones."""
        peak_hour = self.get_peak_hour()
        
        # Enviar 5 minutos antes del peak
        optimal_hour = peak_hour if peak_hour > 0 else 9
        optimal_minute = 55 if peak_hour > 0 else 0
        
        return time(optimal_hour, optimal_minute)
    
    def to_dict(self) -> Dict:
        return {
            'user_id': self.user_id,
            'activity_times': [t.isoformat() for t in self.activity_times]
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'UserActivity':
        return cls(
            user_id=data['user_id'],
            activity_times=[datetime.fromisoformat(t) for t in data.get('activity_times', [])]
        )


# ═══════════════════════════════════════════════════════════════
#  SMART NOTIFIER
# ═══════════════════════════════════════════════════════════════

class SmartNotifier:
    """
    Sistema inteligente de notificaciones.
    
    Features:
    - Aprende mejor hora por usuario
    - Rate limiting personalizado
    - Priority queue
    - Quiet hours
    - Analytics de actividad
    """
    
    def __init__(self, 
                 activity_file: str = 'user_activity.json',
                 queue_file: str = 'notification_queue.json'):
        self.activity_file = Path(activity_file)
        self.queue_file = Path(queue_file)
        
        self.user_activities: Dict[int, UserActivity] = {}
        self.notification_queue: List[Notification] = []
        self.daily_sent_count: Dict[int, int] = defaultdict(int)
        self.last_sent: Dict[str, datetime] = {}  # key: f"{user_id}:{type}"
        
        self._load_data()
        
        logger.info("🔔 SmartNotifier initialized")
    
    def _load_data(self):
        """Carga datos desde archivos."""
        # Load user activities
        if self.activity_file.exists():
            try:
                with open(self.activity_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for user_id_str, activity_data in data.items():
                    user_id = int(user_id_str)
                    self.user_activities[user_id] = UserActivity.from_dict(activity_data)
                
                logger.info(f"✅ Loaded {len(self.user_activities)} user activities")
            except Exception as e:
                logger.error(f"❌ Error loading activities: {e}")
        
        # Load notification queue
        if self.queue_file.exists():
            try:
                with open(self.queue_file, 'r', encoding='utf-8') as f:
                    queue_data = json.load(f)
                
                for notif_data in queue_data:
                    # Reconstruct notification (simplified)
                    if not notif_data.get('sent', False):
                        self.notification_queue.append(Notification(
                            user_id=notif_data['user_id'],
                            type=NotificationType(notif_data['type']),
                            priority=NotificationPriority(notif_data['priority']),
                            message=notif_data['message'],
                            created_at=datetime.fromisoformat(notif_data['created_at']),
                            scheduled_for=datetime.fromisoformat(notif_data['scheduled_for']) if notif_data.get('scheduled_for') else None,
                            metadata=notif_data.get('metadata', {})
                        ))
                
                logger.info(f"✅ Loaded {len(self.notification_queue)} pending notifications")
            except Exception as e:
                logger.error(f"❌ Error loading queue: {e}")
    
    def _save_data(self):
        """Guarda datos a archivos."""
        try:
            # Save activities
            activities_data = {
                str(user_id): activity.to_dict()
                for user_id, activity in self.user_activities.items()
            }
            with open(self.activity_file, 'w', encoding='utf-8') as f:
                json.dump(activities_data, f, indent=2, ensure_ascii=False)
            
            # Save queue
            queue_data = [notif.to_dict() for notif in self.notification_queue]
            with open(self.queue_file, 'w', encoding='utf-8') as f:
                json.dump(queue_data, f, indent=2, ensure_ascii=False)
            
            logger.debug("💾 Notification data saved")
        except Exception as e:
            logger.error(f"❌ Error saving data: {e}")
    
    def track_activity(self, user_id: int, timestamp: datetime = None):
        """Registra actividad del usuario."""
        if timestamp is None:
            timestamp = datetime.now()
        
        if user_id not in self.user_activities:
            self.user_activities[user_id] = UserActivity(user_id=user_id)
        
        self.user_activities[user_id].add_activity(timestamp)
        self._save_data()
    
    def get_optimal_send_time(self, user_id: int) -> time:
        """Obtiene hora óptima de envío para usuario."""
        if user_id in self.user_activities:
            return self.user_activities[user_id].get_optimal_send_time()
        
        return DAILY_REMINDER_TIME  # Default
    
    def is_quiet_hours(self) -> bool:
        """Verifica si estamos en quiet hours."""
        now = datetime.now().time()
        
        if QUIET_START < QUIET_END:
            # Normal case: 22:00 - 08:00
            return QUIET_START <= now or now <= QUIET_END
        else:
            # Edge case: quiet hours cross midnight
            return QUIET_START <= now <= time(23, 59) or time(0, 0) <= now <= QUIET_END
    
    def can_send_notification(self, user_id: int, is_premium: bool = False) -> bool:
        """Verifica si puede enviar notificación al usuario."""
        # Check quiet hours
        if self.is_quiet_hours():
            return False
        
        # Check rate limit
        limit = RATE_LIMIT_PREMIUM if is_premium else RATE_LIMIT_FREE
        if self.daily_sent_count.get(user_id, 0) >= limit:
            return False
        
        return True
    
    def add_notification(self, 
                        user_id: int,
                        notif_type: NotificationType,
                        priority: NotificationPriority,
                        message: str,
                        metadata: Dict = None,
                        schedule_for: datetime = None):
        """Añade notificación a la cola."""
        notif = Notification(
            user_id=user_id,
            type=notif_type,
            priority=priority,
            message=message,
            created_at=datetime.now(),
            scheduled_for=schedule_for,
            metadata=metadata or {}
        )
        
        self.notification_queue.append(notif)
        self.notification_queue.sort(key=lambda n: n.priority.value)
        
        self._save_data()
        
        logger.info(f"📬 Added notification for user {user_id}: {notif_type.value}")
    
    def check_cooldown(self, user_id: int, notif_type: NotificationType) -> bool:
        """Verifica cooldown de tipo de notificación."""
        key = f"{user_id}:{notif_type.value}"
        
        if key not in self.last_sent:
            return True
        
        last_sent = self.last_sent[key]
        
        # Cooldowns por tipo
        cooldowns = {
            NotificationType.PRICE_DROP: PRICE_DROP_COOLDOWN,
            NotificationType.DAILY_REMINDER: DAILY_REMINDER_COOLDOWN,
        }
        
        cooldown = cooldowns.get(notif_type, 0)
        elapsed = (datetime.now() - last_sent).seconds
        
        return elapsed >= cooldown
    
    async def process_queue(self, send_func):
        """
        Procesa cola de notificaciones.
        
        Args:
            send_func: Async function(user_id, message) para enviar
        """
        processed = []
        
        for notif in self.notification_queue:
            if notif.sent:
                continue
            
            if not notif.is_ready():
                continue
            
            # Check if can send
            is_premium = notif.metadata.get('is_premium', False)
            if not self.can_send_notification(notif.user_id, is_premium):
                logger.debug(f"⚠️ Cannot send to user {notif.user_id} (rate limit or quiet hours)")
                continue
            
            # Check cooldown
            if not self.check_cooldown(notif.user_id, notif.type):
                logger.debug(f"⏰ Cooldown active for user {notif.user_id} ({notif.type.value})")
                continue
            
            # Send notification
            try:
                await send_func(notif.user_id, notif.message)
                
                # Mark as sent
                notif.sent = True
                notif.sent_at = datetime.now()
                
                # Update counters
                self.daily_sent_count[notif.user_id] += 1
                self.last_sent[f"{notif.user_id}:{notif.type.value}"] = datetime.now()
                
                processed.append(notif)
                
                logger.info(f"✅ Sent {notif.type.value} notification to user {notif.user_id}")
            
            except Exception as e:
                logger.error(f"❌ Error sending notification to user {notif.user_id}: {e}")
        
        # Remove sent notifications
        self.notification_queue = [n for n in self.notification_queue if not n.sent]
        
        self._save_data()
        
        return len(processed)
    
    def reset_daily_limits(self):
        """Resetea contadores diarios (llamar a medianoche)."""
        self.daily_sent_count.clear()
        logger.info("🔄 Daily notification limits reset")


# ═══════════════════════════════════════════════════════════════
#  MESSAGE TEMPLATES
# ═══════════════════════════════════════════════════════════════

class NotificationTemplates:
    """Templates para notificaciones personalizadas."""
    
    @staticmethod
    def price_drop(route: str, old_price: float, new_price: float, savings: float) -> str:
        """Template para price drop."""
        savings_pct = ((old_price - new_price) / old_price) * 100
        
        return (
            f"🚨 *¡ALERTA DE PRECIO!* 🚨\n\n"
            f"✈️ *Ruta:* {route}\n"
            f"💰 *Precio anterior:* €{old_price:.0f}\n"
            f"🔥 *Precio actual:* €{new_price:.0f}\n"
            f"📉 *Ahorro:* €{savings:.0f} ({savings_pct:.0f}%)\n\n"
            f"_¡Actúa rápido! Estos precios no duran mucho_"
        )
    
    @staticmethod
    def daily_reminder(username: str, streak: int, coins_yesterday: int = 0) -> str:
        """Template para daily reminder."""
        if streak == 0:
            return (
                f"🌅 *¡Buenos días @{username}!*\n\n"
                f"💰 No olvides reclamar tu reward diario con /daily\n"
                f"🎁 Gana entre 50-200 FlightCoins\n\n"
                f"_¡Empieza tu racha hoy!_ 🔥"
            )
        else:
            return (
                f"🔥 *¡Racha activa @{username}!*\n\n"
                f"🏆 Llevas {streak} días consecutivos\n"
                f"💰 Ayer ganaste: {coins_yesterday} coins\n\n"
                f"🚀 Reclama tu reward con /daily\n"
                f"_+{(streak+1)*10} bonus si lo haces hoy_ 💪"
            )
    
    @staticmethod
    def achievement_unlocked(achievement_name: str, coins_earned: int) -> str:
        """Template para achievement unlocked."""
        emoji_map = {
            'early_bird': '🌅',
            'deal_hunter': '🎯',
            'globe_trotter': '🌍',
            'speed_demon': '⚡',
            'money_saver': '💰',
            'week_warrior': '🔥',
            'month_master': '🏆',
            'referral_king': '👑',
            'power_user': '⚡'
        }
        
        emoji = emoji_map.get(achievement_name, '🏆')
        title = achievement_name.replace('_', ' ').title()
        
        return (
            f"{emoji} *¡LOGRO DESBLOQUEADO!* {emoji}\n\n"
            f"🏆 *{title}*\n\n"
            f"💰 +{coins_earned} FlightCoins\n\n"
            f"_¡Sigue así! Consulta todos tus logros con /profile_"
        )
    
    @staticmethod
    def tier_upgrade(old_tier: str, new_tier: str) -> str:
        """Template para tier upgrade."""
        tier_emojis = {
            'bronze': '🥉',
            'silver': '🥈',
            'gold': '🥇',
            'diamond': '💎'
        }
        
        old_emoji = tier_emojis.get(old_tier, '')
        new_emoji = tier_emojis.get(new_tier, '')
        
        return (
            f"🎉 *¡SUBISTE DE NIVEL!* 🎉\n\n"
            f"{old_emoji} {old_tier.upper()} → {new_emoji} {new_tier.upper()}\n\n"
            f"🎁 *Nuevos beneficios desbloqueados:*\n"
            f"• Más búsquedas diarias\n"
            f"• Más watchlist slots\n"
            f"• Más alertas personalizadas\n\n"
            f"_Consulta tu perfil con /profile_"
        )


if __name__ == '__main__':
    # 🧪 Tests rápidos
    print("🧪 Testing SmartNotifier...\n")
    
    async def mock_send(user_id, message):
        print(f"\n📨 Sending to user {user_id}:")
        print(message)
    
    notifier = SmartNotifier('test_activity.json', 'test_queue.json')
    
    # Test 1: Track activity
    print("1. Tracking user activity...")
    notifier.track_activity(12345)
    optimal_time = notifier.get_optimal_send_time(12345)
    print(f"   Optimal send time: {optimal_time}")
    
    # Test 2: Add notifications
    print("\n2. Adding notifications...")
    notifier.add_notification(
        user_id=12345,
        notif_type=NotificationType.DAILY_REMINDER,
        priority=NotificationPriority.HIGH,
        message=NotificationTemplates.daily_reminder('testuser', 5, 150)
    )
    
    # Test 3: Process queue
    print("\n3. Processing queue...")
    asyncio.run(notifier.process_queue(mock_send))
    
    print("\n✅ All tests completed!")
