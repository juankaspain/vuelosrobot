#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
┌────────────────────────────────────────────────────────────────┐
│  VIRAL GROWTH COMMANDS HANDLER - IT5              │
│  Cazador Supremo v13.1 Enterprise                    │
│  Target: K-factor > 1.2                              │
└────────────────────────────────────────────────────────────────┘

Handler para comandos de crecimiento viral:
- /refer - Sistema de referidos
- /myref - Stats de referidos
- /groups - Explorar grupos de caza
- /creategroup - Crear grupo
- /joingroup - Unirse a grupo
- /leaderboard - Rankings globales
- /season - Info temporada actual

Autor: @Juanka_Spain
Version: 13.10.1
Date: 2026-01-17
"""

import sys
import io
import logging
from datetime import datetime
from typing import Optional, List
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ChatAction

# Fix encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

try:
    from viral_growth_system import ViralGrowthSystem
    VIRAL_ENABLED = True
except ImportError as e:
    print("WARNING: Viral modules not available")
    VIRAL_ENABLED = False

logger = logging.getLogger(__name__)


class ViralCommandHandler:
    """
    Handler para todos los comandos de Viral Growth (IT5).
    
    Gestiona:
    - Sistema de referidos
    - Compartir chollos
    - Grupos de caza
    - Leaderboards competitivos
    - Social sharing
    """
    
    def __init__(self, 
                 bot_username: str = "VuelosRobot",
                 retention_mgr = None):
        self.bot_username = bot_username
        self.retention_mgr = retention_mgr
        
        if VIRAL_ENABLED:
            self.viral_mgr = ViralGrowthSystem()
            logger.info("ViralCommandHandler initialized")
        else:
            logger.warning("ViralCommandHandler not available")
    
    # =========================================================================
    #  REFERRAL SYSTEM COMMANDS
    # =========================================================================
    
    async def handle_refer(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Comando /refer - Muestra código de referido del usuario.
        """
        if not VIRAL_ENABLED:
            await update.effective_message.reply_text(
                "Sistema viral no disponible temporalmente."
            )
            return
        
        msg = update.effective_message
        if not msg: return
        
        user = update.effective_user
        user_id = user.id
        username = user.username or f"user_{user_id}"
        
        await context.bot.send_chat_action(chat_id=msg.chat_id, action=ChatAction.TYPING)
        
        # Obtener tier del usuario (desde RetentionManager si está disponible)
        tier = "BRONZE"
        if self.retention_mgr:
            try:
                profile = self.retention_mgr.get_or_create_profile(user_id, username)
                tier = profile.tier.value.upper()
            except:
                pass
        
        # Obtener o crear código de referido
        referral_code = self.viral_mgr.generate_referral_code(
            user_id=user_id,
            username=username,
            tier=tier
        )
        
        # Link de referido
        referral_link = f"https://t.me/{self.bot_username}?start=ref_{referral_code}"
        
        # Stats de referidos
        referrals = self.viral_mgr.get_user_referrals(user_id)
        total_referrals = len(referrals)
        active_referrals = sum(1 for r in referrals if r.get('is_qualified', False))
        
        # Recompensas del tier actual
        tier_config = {
            'BRONZE': {'referrer': 500, 'referee': 300},
            'SILVER': {'referrer': 750, 'referee': 450},
            'GOLD': {'referrer': 1000, 'referee': 600},
            'DIAMOND': {'referrer': 1500, 'referee': 900},
            'PLATINUM': {'referrer': 2000, 'referee': 1200}
        }
        
        rewards = tier_config.get(tier, tier_config['BRONZE'])
        
        response = (
            f"TU CODIGO DE REFERIDO\n\n"
            f"Codigo: {referral_code}\n"
            f"Link: {referral_link}\n\n"
            f"Referidos Activos: {active_referrals}/{total_referrals}\n\n"
            f"RECOMPENSAS {tier}:\n"
            f"   Tu ganas: {rewards['referrer']} coins\n"
            f"   Tu amigo: {rewards['referee']} coins\n"
        )
        
        # Milestones
        milestones = [
            (5, "Starter", 1000),
            (10, "Recruiter", 2500),
            (25, "Champion", 5000),
            (50, "Legend", 10000)
        ]
        
        for count, name, reward in milestones:
            if active_referrals < count:
                remaining = count - active_referrals
                response += (
                    f"\nPROXIMO MILESTONE:\n"
                    f"   {name} ({count} referidos)\n"
                    f"   Te faltan: {remaining}\n"
                    f"   Recompensa: {reward} coins"
                )
                break
        
        # Botones
        keyboard = [
            [
                InlineKeyboardButton(
                    "Compartir Codigo",
                    url=f"https://t.me/share/url?url={referral_link}&text=Unete a Cazador Supremo!"
                )
            ],
            [
                InlineKeyboardButton("Mis Stats", callback_data="viral_myref")
            ]
        ]
        
        await msg.reply_text(
            response,
            reply_markup=InlineKeyboardMarkup(keyboard),
            disable_web_page_preview=True
        )
    
    async def handle_myref(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Comando /myref - Stats detalladas de referidos.
        """
        if not VIRAL_ENABLED:
            await update.effective_message.reply_text(
                "Sistema viral no disponible temporalmente."
            )
            return
        
        msg = update.effective_message
        if not msg: return
        
        user = update.effective_user
        user_id = user.id
        
        await context.bot.send_chat_action(chat_id=msg.chat_id, action=ChatAction.TYPING)
        
        # Analytics de referidos
        analytics = self.viral_mgr.get_referral_analytics(user_id)
        
        if not analytics or analytics['total_referrals'] == 0:
            await msg.reply_text(
                "Aun no tienes referidos.\n\n"
                "Usa /refer para obtener tu codigo y empezar a invitar amigos!"
            )
            return
        
        response = (
            f"TUS STATS DE REFERIDOS\n\n"
            f"Total Referidos: {analytics['total_referrals']}\n"
            f"Cualificados: {analytics['qualified_referrals']}\n"
            f"Coins Ganados: {analytics.get('total_coins_earned', 0)}\n"
            f"K-factor: {analytics.get('k_factor', 0):.2f}\n"
        )
        
        keyboard = [
            [InlineKeyboardButton("Volver", callback_data="viral_refer")]
        ]
        
        await msg.reply_text(
            response,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    # =========================================================================
    #  LEADERBOARD COMMANDS
    # =========================================================================
    
    async def handle_leaderboard(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Comando /leaderboard - Ver rankings globales.
        """
        msg = update.effective_message
        if not msg: return
        
        await context.bot.send_chat_action(chat_id=msg.chat_id, action=ChatAction.TYPING)
        
        response = (
            "LEADERBOARD GLOBAL\n\n"
            "Sistema de rankings en desarrollo.\n"
            "Proximamente: Rankings por deals, ahorro, referidos y mas!"
        )
        
        await msg.reply_text(response)
    
    # =========================================================================
    #  CALLBACK HANDLERS
    # =========================================================================
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Maneja callbacks de botones virales.
        """
        query = update.callback_query
        if not query: return
        
        await query.answer()
        
        data = query.data
        
        # Referral callbacks
        if data == "viral_refer":
            await self.handle_refer(update, context)
        elif data == "viral_myref":
            await self.handle_myref(update, context)
        elif data == "viral_leaderboard":
            await self.handle_leaderboard(update, context)


if __name__ == '__main__':
    # Quick test
    print("Testing ViralCommandHandler...")
    
    if VIRAL_ENABLED:
        handler = ViralCommandHandler()
        print("Handler initialized successfully")
    else:
        print("Viral modules not available")
