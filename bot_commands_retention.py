#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
┌────────────────────────────────────────────────────────────────┐
│  🎮 BOT COMMANDS - Retention Integration                    │
│  🚀 Cazador Supremo v13.0 Enterprise                          │
│  📊 Nuevos: /daily /watchlist /profile /shop                  │
└────────────────────────────────────────────────────────────────┘

Comandos de retención para integración con TelegramBotManager.

Autor: @Juanka_Spain
Version: 13.0.0
Date: 2026-01-14
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ChatAction
from retention_system import RetentionManager, UserTier, TIER_BENEFITS, TIER_LIMITS
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class RetentionCommands:
    """
    Handler de comandos de retención para integrar en TelegramBotManager.
    
    Nuevos comandos:
    - /daily: Reclama reward diario
    - /watchlist: Gestiona watchlist personal
    - /profile: Ver perfil y stats
    - /shop: Tienda virtual de coins
    """
    
    TIER_EMOJIS = {
        UserTier.BRONZE: "🥉",
        UserTier.SILVER: "🥈",
        UserTier.GOLD: "🥇",
        UserTier.DIAMOND: "💎"
    }
    
    SHOP_ITEMS = {
        'premium_day': {'name': '24h Premium', 'coins': 100, 'emoji': '🔥'},
        'price_freeze': {'name': 'Price Freeze 1x', 'coins': 200, 'emoji': '❄️'},
        'watchlist_slot': {'name': '+5 Watchlist Slots', 'coins': 150, 'emoji': '📍'},
        'premium_month': {'name': '1 Mes Premium', 'coins': 500, 'emoji': '💎'},
    }
    
    def __init__(self, retention_mgr: RetentionManager):
        self.retention_mgr = retention_mgr
    
    async def cmd_daily(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Comando /daily - Reclama reward diario.
        
        Features:
        - Reward aleatorio 50-200 coins
        - Streak bonus +10 coins/día consecutivo
        - Notifica level up
        - Muestra tier actual
        """
        msg = update.effective_message
        user = update.effective_user
        if not msg or not user: return
        
        await context.bot.send_chat_action(chat_id=msg.chat_id, action=ChatAction.TYPING)
        
        result = self.retention_mgr.claim_daily(user.id, user.username or str(user.id))
        
        if not result['success']:
            hours = result.get('hours_until', 0)
            response = (
                f"⏰ *Ya reclamaste tu reward hoy*\n\n"
                f"🕒 Próximo en: {hours:.1f} horas\n\n"
                f"_Vuelve mañana para mantener tu racha 🔥_"
            )
            await msg.reply_text(response, parse_mode='Markdown')
            return
        
        # Success!
        reward = result['reward']
        streak = result['streak']
        tier = result['tier']
        total_coins = result['total_coins']
        
        tier_enum = UserTier(tier)
        tier_emoji = self.TIER_EMOJIS[tier_enum]
        
        response = (
            f"🎉 *¡REWARD RECLAMADO!* 🎉\n\n"
            f"💰 *Ganaste:* {reward} FlightCoins\n"
            f"🔥 *Racha:* {streak} días consecutivos\n\n"
            f"{tier_emoji} *Tier:* {tier.upper()}\n"
            f"💳 *Balance:* {total_coins} coins\n\n"
        )
        
        # Motivacional
        if streak == 7:
            response += f"🏆 ¡Desbloqueaste WEEK WARRIOR!\n"
        elif streak == 30:
            response += f"🏆 ¡Desbloqueaste MONTH MASTER!\n"
        elif streak >= 3:
            response += f"_¡Sigue así! Mañana: +{(streak+1)*10} bonus 💪_"
        else:
            response += f"_Vuelve mañana para seguir tu racha 🚀_"
        
        await msg.reply_text(response, parse_mode='Markdown')
    
    async def cmd_watchlist(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Comando /watchlist - Gestiona watchlist personal.
        
        Subcomandos:
        - /watchlist add MAD-MIA 450 - Añadir ruta con threshold
        - /watchlist view - Ver watchlist completa
        - /watchlist remove MAD-MIA - Eliminar ruta
        """
        msg = update.effective_message
        user = update.effective_user
        if not msg or not user: return
        
        await context.bot.send_chat_action(chat_id=msg.chat_id, action=ChatAction.TYPING)
        
        if not context.args:
            # Sin args: mostrar uso
            response = (
                f"📍 *Tu Watchlist Personal*\n\n"
                f"*Comandos:*\n"
                f"`/watchlist add MAD-MIA 450` - Añadir ruta\n"
                f"`/watchlist view` - Ver tu lista\n"
                f"`/watchlist remove MAD-MIA` - Eliminar\n\n"
                f"_Recibirás notificaciones cuando el precio baje del threshold_"
            )
            await msg.reply_text(response, parse_mode='Markdown')
            return
        
        action = context.args[0].lower()
        
        if action == 'add':
            if len(context.args) < 3:
                await msg.reply_text("⚠️ Uso: `/watchlist add MAD-MIA 450`", parse_mode='Markdown')
                return
            
            route = context.args[1].upper()
            try:
                threshold = float(context.args[2])
            except ValueError:
                await msg.reply_text("❌ Precio inválido")
                return
            
            result = self.retention_mgr.add_to_watchlist(
                user.id, user.username or str(user.id), route, threshold
            )
            
            if result['success']:
                response = (
                    f"✅ *Ruta añadida a tu watchlist*\n\n"
                    f"✈️ *Ruta:* {route}\n"
                    f"💰 *Threshold:* €{threshold:.0f}\n\n"
                    f"📍 Slots: {result['watchlist_count']}/{result['max_slots']}\n\n"
                    f"_Te avisaremos cuando el precio baje de €{threshold:.0f}_"
                )
                await msg.reply_text(response, parse_mode='Markdown')
            else:
                await msg.reply_text(f"❌ {result['error']}")
        
        elif action == 'view':
            watchlist = self.retention_mgr.get_watchlist(user.id)
            
            if not watchlist:
                response = (
                    f"📍 *Tu watchlist está vacía*\n\n"
                    f"Añade rutas con:\n"
                    f"`/watchlist add MAD-MIA 450`"
                )
                await msg.reply_text(response, parse_mode='Markdown')
                return
            
            response = f"📍 *Tu Watchlist ({len(watchlist)} rutas)*\n\n"
            for item in watchlist:
                response += (
                    f"✈️ `{item.route}`\n"
                    f"   💰 Threshold: €{item.threshold:.0f}\n"
                    f"   🔔 Notificaciones: {item.notifications_sent}\n\n"
                )
            
            response += f"_Usa `/watchlist remove RUTA` para eliminar_"
            await msg.reply_text(response, parse_mode='Markdown')
        
        elif action == 'remove':
            if len(context.args) < 2:
                await msg.reply_text("⚠️ Uso: `/watchlist remove MAD-MIA`", parse_mode='Markdown')
                return
            
            route = context.args[1].upper()
            removed = self.retention_mgr.remove_from_watchlist(user.id, route)
            
            if removed:
                await msg.reply_text(f"✅ Ruta {route} eliminada de tu watchlist")
            else:
                await msg.reply_text(f"❌ Ruta {route} no encontrada en tu watchlist")
        
        else:
            await msg.reply_text("❌ Acción inválida. Usa: add, view, remove")
    
    async def cmd_profile(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Comando /profile - Ver perfil completo del usuario.
        
        Muestra:
        - Balance de coins
        - Tier actual y progreso
        - Stats (searches, deals, savings)
        - Streaks
        - Achievements
        - Rutas únicas
        """
        msg = update.effective_message
        user = update.effective_user
        if not msg or not user: return
        
        await context.bot.send_chat_action(chat_id=msg.chat_id, action=ChatAction.TYPING)
        
        profile = self.retention_mgr.get_or_create_profile(user.id, user.username or str(user.id))
        
        tier_emoji = self.TIER_EMOJIS[profile.tier]
        
        # Calcular progreso a siguiente tier
        next_tier = None
        progress_pct = 0
        coins_needed = 0
        
        if profile.tier == UserTier.BRONZE:
            next_tier = UserTier.SILVER
            coins_needed = TIER_LIMITS[UserTier.SILVER] - profile.coins
            progress_pct = (profile.coins / TIER_LIMITS[UserTier.SILVER]) * 100
        elif profile.tier == UserTier.SILVER:
            next_tier = UserTier.GOLD
            coins_needed = TIER_LIMITS[UserTier.GOLD] - profile.coins
            progress_pct = ((profile.coins - TIER_LIMITS[UserTier.SILVER]) / 
                           (TIER_LIMITS[UserTier.GOLD] - TIER_LIMITS[UserTier.SILVER])) * 100
        elif profile.tier == UserTier.GOLD:
            next_tier = UserTier.DIAMOND
            coins_needed = TIER_LIMITS[UserTier.DIAMOND] - profile.coins
            progress_pct = ((profile.coins - TIER_LIMITS[UserTier.GOLD]) / 
                           (TIER_LIMITS[UserTier.DIAMOND] - TIER_LIMITS[UserTier.GOLD])) * 100
        
        response = (
            f"👤 *PERFIL DE @{profile.username}*\n"
            f"{"="*30}\n\n"
            f"{tier_emoji} *Tier:* {profile.tier.value.upper()}\n"
            f"💰 *FlightCoins:* {profile.coins}\n"
        )
        
        if next_tier:
            progress_bar = "█" * int(progress_pct / 10) + "░" * (10 - int(progress_pct / 10))
            next_emoji = self.TIER_EMOJIS[next_tier]
            response += (
                f"\n📈 *Progreso a {next_tier.value.upper()}:*\n"
                f"{progress_bar} {progress_pct:.0f}%\n"
                f"_Faltan {coins_needed} coins para {next_emoji}_\n"
            )
        
        response += (
            f"\n📊 *ESTADÍSTICAS*\n"
            f"🔍 Búsquedas: {profile.total_searches}\n"
            f"🔥 Deals encontrados: {profile.total_deals_found}\n"
            f"💸 Ahorro total: €{profile.total_savings:.0f}\n"
            f"🌍 Rutas únicas: {len(profile.routes_searched)}\n\n"
            f"🔥 *RACHAS*\n"
            f"Actual: {profile.current_streak} días\n"
            f"Récord: {profile.longest_streak} días\n\n"
            f"🏆 *ACHIEVEMENTS:* {len(profile.achievements)}\n"
        )
        
        if profile.achievements:
            for achievement in profile.achievements[:5]:
                response += f"• {achievement.type.value.replace('_', ' ').title()}\n"
            if len(profile.achievements) > 5:
                response += f"_...y {len(profile.achievements)-5} más_\n"
        
        # Keyboard con acciones
        keyboard = [
            [InlineKeyboardButton("🔥 Daily Reward", callback_data="daily")],
            [InlineKeyboardButton("📍 Watchlist", callback_data="watchlist_view")],
            [InlineKeyboardButton("🛍️ Tienda", callback_data="shop")]
        ]
        
        await msg.reply_text(response, parse_mode='Markdown', 
                           reply_markup=InlineKeyboardMarkup(keyboard))
    
    async def cmd_shop(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Comando /shop - Tienda virtual de FlightCoins.
        
        Items disponibles:
        - 24h Premium: 100 coins
        - Price Freeze: 200 coins
        - +5 Watchlist slots: 150 coins
        - 1 Mes Premium: 500 coins
        """
        msg = update.effective_message
        user = update.effective_user
        if not msg or not user: return
        
        await context.bot.send_chat_action(chat_id=msg.chat_id, action=ChatAction.TYPING)
        
        profile = self.retention_mgr.get_or_create_profile(user.id, user.username or str(user.id))
        
        response = (
            f"🛍️ *TIENDA DE FLIGHTCOINS*\n"
            f"{"="*30}\n\n"
            f"💰 Tu balance: *{profile.coins} coins*\n\n"
            f"*¡Canjea tus coins!*\n\n"
        )
        
        for item_id, item in self.SHOP_ITEMS.items():
            can_afford = profile.coins >= item['coins']
            status = "✅" if can_afford else "🔒"
            response += (
                f"{status} {item['emoji']} *{item['name']}*\n"
                f"   💰 {item['coins']} coins\n\n"
            )
        
        response += (
            f"\n_Usa `/buy ITEM` para comprar_\n"
            f"_Gana más coins con /daily y encontrando deals_"
        )
        
        await msg.reply_text(response, parse_mode='Markdown')
    
    def get_tier_benefits_text(self, tier: UserTier) -> str:
        """Genera texto con beneficios del tier."""
        benefits = TIER_BENEFITS[tier]
        daily_searches = benefits['daily_searches']
        watchlist = benefits['watchlist_slots']
        alerts = benefits['custom_alerts']
        
        search_text = "Unlimited" if daily_searches == -1 else str(daily_searches)
        alert_text = "Unlimited" if alerts == -1 else str(alerts)
        
        return (
            f"🔍 Búsquedas: {search_text}/día\n"
            f"📍 Watchlist: {watchlist} slots\n"
            f"🔔 Alertas custom: {alert_text}\n"
        )


if __name__ == '__main__':
    print("✅ Retention commands module loaded")
    print("\nAvailable commands:")
    print("- /daily - Claim daily reward")
    print("- /watchlist - Manage watchlist")
    print("- /profile - View profile & stats")
    print("- /shop - Virtual store")
