#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
┌────────────────────────────────────────────────────────────────┐
│  ⏰ BACKGROUND TASKS - Retention Automation              │
│  🚀 Cazador Supremo v13.0 Enterprise                          │
│  🔄 Watchlist Monitor + Schedulers                           │
└────────────────────────────────────────────────────────────────┘

Tareas en background para automatización de retención:
- Watchlist monitoring
- Daily reminders
- Midnight resets
- Weekly summaries

Autor: @Juanka_Spain
Version: 13.0.0
Date: 2026-01-14
"""

import asyncio
import logging
from datetime import datetime, time, timedelta
from typing import Callable, Dict, List, Optional
from dataclasses import dataclass
import traceback

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
#  CONSTANTS
# ═══════════════════════════════════════════════════════════════

WATCHLIST_CHECK_INTERVAL = 1800  # 30 minutos
DAILY_REMINDER_CHECK_INTERVAL = 3600  # 1 hora
MIDNIGHT_CHECK_INTERVAL = 60  # 1 minuto
WEEKLY_SUMMARY_DAY = 0  # Lunes (0=Monday, 6=Sunday)
WEEKLY_SUMMARY_TIME = time(20, 0)  # 20:00


# ═══════════════════════════════════════════════════════════════
#  BACKGROUND TASKS
# ═══════════════════════════════════════════════════════════════

class BackgroundTaskManager:
    """
    Gestor de tareas en background.
    
    Responsabilidades:
    - Watchlist monitoring
    - Daily reminders
    - Midnight resets
    - Weekly summaries
    - Health monitoring
    """
    
    def __init__(self, 
                 retention_mgr,
                 scanner,
                 notifier):
        """
        Args:
            retention_mgr: RetentionManager instance
            scanner: FlightScanner instance
            notifier: SmartNotifier instance
        """
        self.retention_mgr = retention_mgr
        self.scanner = scanner
        self.notifier = notifier
        
        self.running = False
        self.tasks = []
        
        self.last_midnight_reset = datetime.now().date()
        self.last_weekly_summary = None
        
        logger.info("⏰ BackgroundTaskManager initialized")
    
    async def start(self):
        """Inicia todas las tareas en background."""
        self.running = True
        
        # Crear tareas
        self.tasks = [
            asyncio.create_task(self._watchlist_monitor_loop()),
            asyncio.create_task(self._daily_reminder_loop()),
            asyncio.create_task(self._midnight_reset_loop()),
            asyncio.create_task(self._weekly_summary_loop()),
            asyncio.create_task(self._notification_processor_loop()),
        ]
        
        logger.info("✅ All background tasks started")
    
    async def stop(self):
        """Detiene todas las tareas."""
        self.running = False
        
        # Cancelar tareas
        for task in self.tasks:
            task.cancel()
        
        # Esperar cancelación
        await asyncio.gather(*self.tasks, return_exceptions=True)
        
        logger.info("⏸️ All background tasks stopped")
    
    async def _watchlist_monitor_loop(self):
        """
        Loop para monitorizar watchlist.
        
        Cada 30 minutos:
        1. Obtiene watchlists de todos los usuarios
        2. Escanea precios actuales
        3. Compara con thresholds
        4. Envía notificaciones si hay price drops
        """
        logger.info("🔍 Watchlist monitor started")
        
        while self.running:
            try:
                await asyncio.sleep(WATCHLIST_CHECK_INTERVAL)
                
                logger.info("🔍 Checking watchlists...")
                
                # Obtener todos los perfiles
                for user_id, profile in self.retention_mgr.profiles.items():
                    if not profile.watchlist:
                        continue
                    
                    # Verificar cada item del watchlist
                    for item in profile.watchlist:
                        try:
                            # Parsear ruta
                            origin, dest = item.route.split('-')
                            
                            # Crear FlightRoute (import local para evitar circular)
                            from cazador_supremo_enterprise import FlightRoute
                            route = FlightRoute(
                                origin=origin,
                                dest=dest,
                                name=item.route
                            )
                            
                            # Escanear precio actual
                            price = self.scanner._scan_single(route)
                            
                            if not price:
                                continue
                            
                            current_price = price.price
                            
                            # Comparar con threshold
                            if current_price < item.threshold:
                                # ¡Price drop!
                                old_price = item.last_price or item.threshold
                                savings = old_price - current_price
                                
                                # Generar notificación
                                from smart_notifications import (
                                    NotificationTemplates,
                                    NotificationType,
                                    NotificationPriority
                                )
                                
                                message = NotificationTemplates.price_drop(
                                    route=item.route,
                                    old_price=old_price,
                                    new_price=current_price,
                                    savings=savings
                                )
                                
                                self.notifier.add_notification(
                                    user_id=user_id,
                                    notif_type=NotificationType.PRICE_DROP,
                                    priority=NotificationPriority.CRITICAL,
                                    message=message,
                                    metadata={
                                        'route': item.route,
                                        'price': current_price,
                                        'threshold': item.threshold
                                    }
                                )
                                
                                # Update item
                                item.last_price = current_price
                                item.notifications_sent += 1
                                
                                logger.info(
                                    f"🚨 Price drop detected for user {user_id}: "
                                    f"{item.route} @ €{current_price:.0f}"
                                )
                            
                            else:
                                # Solo update last_price
                                item.last_price = current_price
                        
                        except Exception as e:
                            logger.error(f"❌ Error checking watchlist item {item.route}: {e}")
                            continue
                
                # Guardar cambios
                self.retention_mgr._save_profiles()
                
                logger.info("✅ Watchlist check completed")
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Watchlist monitor error: {e}")
                logger.error(traceback.format_exc())
    
    async def _daily_reminder_loop(self):
        """
        Loop para daily reminders.
        
        Cada hora verifica si hay usuarios que:
        1. No han reclamado su daily hoy
        2. Tienen streak activo (>0)
        3. Es su hora óptima de notificación
        """
        logger.info("🔔 Daily reminder scheduler started")
        
        while self.running:
            try:
                await asyncio.sleep(DAILY_REMINDER_CHECK_INTERVAL)
                
                logger.info("🔔 Checking daily reminders...")
                
                now = datetime.now()
                current_time = now.time()
                
                for user_id, profile in self.retention_mgr.profiles.items():
                    # Skip si ya reclamó hoy
                    if not profile.can_claim_daily():
                        continue
                    
                    # Solo recordar si tiene streak activo
                    if profile.current_streak == 0:
                        continue
                    
                    # Obtener hora óptima
                    optimal_time = self.notifier.get_optimal_send_time(user_id)
                    
                    # Verificar si es cerca de la hora óptima (±30 min)
                    time_diff = abs(
                        (current_time.hour * 60 + current_time.minute) - 
                        (optimal_time.hour * 60 + optimal_time.minute)
                    )
                    
                    if time_diff > 30:  # No es el momento
                        continue
                    
                    # Generar reminder
                    from smart_notifications import (
                        NotificationTemplates,
                        NotificationType,
                        NotificationPriority
                    )
                    
                    # Calcular coins de ayer (estimado)
                    yesterday_coins = 150  # Default
                    
                    message = NotificationTemplates.daily_reminder(
                        username=profile.username,
                        streak=profile.current_streak,
                        coins_yesterday=yesterday_coins
                    )
                    
                    self.notifier.add_notification(
                        user_id=user_id,
                        notif_type=NotificationType.DAILY_REMINDER,
                        priority=NotificationPriority.HIGH,
                        message=message
                    )
                    
                    logger.info(
                        f"🔔 Daily reminder scheduled for user {user_id} "
                        f"(streak: {profile.current_streak})"
                    )
                
                logger.info("✅ Daily reminder check completed")
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Daily reminder error: {e}")
                logger.error(traceback.format_exc())
    
    async def _midnight_reset_loop(self):
        """
        Loop para resets a medianoche.
        
        Ejecuta a las 00:00:
        1. Resetea rate limits diarios
        2. Limpia cache expirado
        3. Purge old notifications
        4. Stats daily reset
        """
        logger.info("🌙 Midnight reset scheduler started")
        
        while self.running:
            try:
                await asyncio.sleep(MIDNIGHT_CHECK_INTERVAL)
                
                now = datetime.now()
                today = now.date()
                
                # Solo ejecutar una vez por día
                if today <= self.last_midnight_reset:
                    continue
                
                # Verificar si es medianoche (±5 min)
                if not (23, 55) <= (now.hour, now.minute) <= (0, 5):
                    continue
                
                logger.info("🌙 Executing midnight reset...")
                
                # 1. Reset rate limits
                self.notifier.reset_daily_limits()
                
                # 2. Limpiar cache
                self.scanner.cache.clear()
                
                # 3. Marcar como ejecutado
                self.last_midnight_reset = today
                
                logger.info("✅ Midnight reset completed")
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Midnight reset error: {e}")
                logger.error(traceback.format_exc())
    
    async def _weekly_summary_loop(self):
        """
        Loop para resumen semanal.
        
        Cada lunes a las 20:00:
        1. Genera resumen semanal personalizado
        2. Stats de la semana
        3. Best deals encontrados
        4. Achievements desbloqueados
        """
        logger.info("📅 Weekly summary scheduler started")
        
        while self.running:
            try:
                await asyncio.sleep(3600)  # Check cada hora
                
                now = datetime.now()
                
                # Verificar si es lunes
                if now.weekday() != WEEKLY_SUMMARY_DAY:
                    continue
                
                # Verificar hora
                if abs((now.hour * 60 + now.minute) - 
                      (WEEKLY_SUMMARY_TIME.hour * 60 + WEEKLY_SUMMARY_TIME.minute)) > 30:
                    continue
                
                # Verificar si ya se envió esta semana
                if self.last_weekly_summary:
                    days_since = (now.date() - self.last_weekly_summary).days
                    if days_since < 7:
                        continue
                
                logger.info("📅 Generating weekly summaries...")
                
                from smart_notifications import (
                    NotificationType,
                    NotificationPriority
                )
                
                for user_id, profile in self.retention_mgr.profiles.items():
                    # Generar resumen personalizado
                    message = self._generate_weekly_summary(profile)
                    
                    self.notifier.add_notification(
                        user_id=user_id,
                        notif_type=NotificationType.WEEKLY_SUMMARY,
                        priority=NotificationPriority.MEDIUM,
                        message=message
                    )
                
                self.last_weekly_summary = now.date()
                
                logger.info("✅ Weekly summaries generated")
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Weekly summary error: {e}")
                logger.error(traceback.format_exc())
    
    def _generate_weekly_summary(self, profile) -> str:
        """Genera resumen semanal personalizado."""
        from retention_system import TIER_EMOJIS
        
        tier_emoji = TIER_EMOJIS.get(profile.tier, '')
        
        summary = (
            f"📅 *RESUMEN SEMANAL*\n"
            f"{"="*30}\n\n"
            f"👤 @{profile.username}\n"
            f"{tier_emoji} Tier: {profile.tier.value.upper()}\n\n"
            f"📊 *Esta semana:*\n"
            f"🔍 Búsquedas: {profile.total_searches}\n"
            f"🔥 Deals: {profile.total_deals_found}\n"
            f"💸 Ahorro: €{profile.total_savings:.0f}\n"
            f"🔥 Racha actual: {profile.current_streak} días\n\n"
        )
        
        if profile.achievements:
            recent_achievements = [a for a in profile.achievements[-3:]]
            if recent_achievements:
                summary += "🏆 *Logros recientes:*\n"
                for ach in recent_achievements:
                    summary += f"• {ach.type.value.replace('_', ' ').title()}\n"
                summary += "\n"
        
        summary += (
            f"🚀 *Sigue así!*\n"
            f"_Usa /profile para ver tus stats completos_"
        )
        
        return summary
    
    async def _notification_processor_loop(self):
        """
        Loop para procesar cola de notificaciones.
        
        Cada 5 minutos:
        1. Procesa cola de notificaciones
        2. Envía notificaciones pendientes
        3. Respeta rate limits y quiet hours
        """
        logger.info("📨 Notification processor started")
        
        while self.running:
            try:
                await asyncio.sleep(300)  # 5 minutos
                
                # Procesar cola (necesita bot instance para enviar)
                # Esto se integrará con TelegramBotManager
                # Por ahora solo log
                pending = len([n for n in self.notifier.notification_queue if not n.sent])
                if pending > 0:
                    logger.info(f"📨 {pending} notifications pending in queue")
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Notification processor error: {e}")


if __name__ == '__main__':
    print("✅ Background tasks module loaded")
    print("\nAvailable tasks:")
    print("- Watchlist Monitor (30min interval)")
    print("- Daily Reminder (1h interval)")
    print("- Midnight Reset (1min check)")
    print("- Weekly Summary (Monday 20:00)")
    print("- Notification Processor (5min interval)")
