#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
═══════════════════════════════════════════════════════════════════════════════
║  📤 VIRAL GROWTH COMMANDS - IT5 Day 5/5                                     ║
║  Handlers de comandos para sistema de crecimiento viral                    ║
═══════════════════════════════════════════════════════════════════════════════

Comandos implementados:
- /refer - Generar y ver código de referido
- /share - Compartir deal en redes sociales  
- /groups - Gestionar grupos de caza
- /leaderboard - Ver rankings competitivos
- /season - Info de temporada actual
- /prizes - Ver premios ganados

Autor: @Juanka_Spain
Version: 13.1.0
Date: 2026-01-15
"""

import logging
from typing import Optional
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ChatAction

# Importar managers de IT5
try:
    from viral_growth_system import ReferralManager, ReferralReward
    from social_sharing import SocialSharingManager, SharePlatform
    from group_hunting import GroupHuntingManager, GroupType, MemberRole
    from competitive_leaderboards import (
        CompetitiveLeaderboardManager, 
        LeaderboardCategory,
        SeasonType
    )
    IT5_AVAILABLE = True
except ImportError as e:
    logging.error(f"❌ Módulos IT5 no disponibles: {e}")
    IT5_AVAILABLE = False

logger = logging.getLogger(__name__)


class ViralGrowthCommandHandler:
    """
    Handler de comandos para sistema de crecimiento viral.
    
    Integra:
    - ReferralManager (sistema de referidos)
    - SocialSharingManager (compartir social)
    - GroupHuntingManager (grupos de caza)
    - CompetitiveLeaderboardManager (rankings)
    """
    
    def __init__(self, bot_token: str):
        """Initialize viral growth command handler."""
        if not IT5_AVAILABLE:
            raise ImportError("IT5 modules not available")
        
        self.referral_mgr = ReferralManager()
        self.social_mgr = SocialSharingManager()
        self.group_mgr = GroupHuntingManager()
        self.leaderboard_mgr = CompetitiveLeaderboardManager()
        self.bot_token = bot_token
        
        logger.info("✅ ViralGrowthCommandHandler initialized")
    
    # ═══════════════════════════════════════════════════════════════════
    #  REFERRAL SYSTEM COMMANDS
    # ═══════════════════════════════════════════════════════════════════
    
    async def handle_refer(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler /refer - Sistema de referidos."""
        msg = update.effective_message
        user = update.effective_user
        
        if not msg or not user:
            return
        
        await context.bot.send_chat_action(
            chat_id=msg.chat_id, 
            action=ChatAction.TYPING
        )
        
        # Generar o recuperar código de referido
        code = self.referral_mgr.generate_referral_code(
            user.id, 
            user.username or f"User{user.id}"
        )
        
        # Obtener stats de referidos
        stats = self.referral_mgr.get_referral_stats(user.id)
        
        # Construir mensaje
        response = (
            f"🎁 *Tu Código de Referido* 🎁\n\n"
            f"📋 Código: `{code}`\n\n"
            f"💡 *¿Cómo funciona?*\n"
            f"1️⃣ Comparte tu código con amigos\n"
            f"2️⃣ Ellos ganan *+300 coins* al registrarse\n"
            f"3️⃣ Tú ganas *+500 coins* cuando hacen su 1ª búsqueda\n\n"
            f"📊 *Tus Estadísticas:*\n"
            f"👥 Total referidos: {stats['total_referrals']}\n"
            f"✅ Activos: {stats['active_referrals']}\n"
            f"⏳ Pendientes: {stats['pending_activation']}\n"
            f"💰 Coins ganados: {stats['total_coins_earned']}\n"
        )
        
        # Next milestone
        if stats['next_milestone']:
            milestone = stats['next_milestone']
            response += (
                f"\n🎯 *Próximo Milestone:*\n"
                f"{milestone['emoji']} {milestone['target']} referidos\n"
                f"🎁 Recompensa: {milestone['reward']}\n"
                f"📍 Te faltan: {milestone['remaining']}\n"
            )
        
        # Botones de acción
        keyboard = [
            [
                InlineKeyboardButton(
                    "📱 Compartir Código",
                    callback_data=f"share_referral_{user.id}"
                )
            ],
            [
                InlineKeyboardButton(
                    "📊 Ver Leaderboard Referidos",
                    callback_data="leaderboard_referrals"
                )
            ]
        ]
        
        await msg.reply_text(
            response,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def handle_apply_referral(self, code: str, user_id: int, username: str) -> str:
        """
        Aplica un código de referido.
        
        Args:
            code: Código de referido
            user_id: ID del nuevo usuario
            username: Username del nuevo usuario
        
        Returns:
            Mensaje de resultado
        """
        success, msg, reward = self.referral_mgr.apply_referral_code(
            referee_id=user_id,
            referee_username=username,
            referral_code=code
        )
        
        if success and reward:
            # Actualizar leaderboard
            self.leaderboard_mgr.update_score(
                category=LeaderboardCategory.REFERRALS.value,
                user_id=user_id,
                username=username,
                score_delta=1
            )
        
        return msg
    
    # ═══════════════════════════════════════════════════════════════════
    #  SOCIAL SHARING COMMANDS
    # ═══════════════════════════════════════════════════════════════════
    
    async def handle_share(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler /share - Compartir en redes sociales."""
        msg = update.effective_message
        user = update.effective_user
        
        if not msg or not user:
            return
        
        await context.bot.send_chat_action(
            chat_id=msg.chat_id,
            action=ChatAction.TYPING
        )
        
        # Generar link de referido
        code = self.referral_mgr.generate_referral_code(
            user.id,
            user.username or f"User{user.id}"
        )
        referral_link = f"https://t.me/CazadorSupremoBot?start={code}"
        
        # Obtener stats de sharing
        share_stats = self.social_mgr.get_user_stats(user.id)
        
        response = (
            f"📤 *Compartir Cazador Supremo* 📤\n\n"
            f"🎁 *Gana 50 coins por cada compartida*\n"
        )
        
        if share_stats and share_stats.total_shares < 3:
            remaining = 3 - share_stats.total_shares
            response += f"✨ *BONUS:* +100 coins extra en tus primeras 3 compartidas ({remaining} restantes)\n"
        
        if share_stats:
            response += (
                f"\n📊 *Tus Stats:*\n"
                f"📤 Compartidas: {share_stats.total_shares}\n"
                f"💰 Coins ganados: {share_stats.coins_earned}\n"
                f"🔄 Conversiones: {share_stats.total_conversions}\n"
            )
            
            if share_stats.viral_shares > 0:
                response += f"💥 Shares virales: {share_stats.viral_shares} (+{share_stats.viral_shares * 500} coins)\n"
        
        # Generar keyboard con opciones de compartir
        keyboard = self.social_mgr.generate_share_keyboard(referral_link, user.id)
        
        await msg.reply_text(
            response,
            parse_mode='Markdown',
            reply_markup=keyboard
        )
    
    async def track_share(self, user_id: int, platform: str) -> float:
        """
        Registra una compartida y retorna coins ganados.
        
        Args:
            user_id: ID del usuario
            platform: Plataforma usada
        
        Returns:
            Coins ganados
        """
        platform_enum = SharePlatform(platform)
        coins = self.social_mgr.track_share(user_id, platform_enum)
        
        # Actualizar leaderboard
        self.leaderboard_mgr.update_score(
            category=LeaderboardCategory.SHARES.value,
            user_id=user_id,
            username=f"User{user_id}",
            score_delta=1
        )
        
        return coins
    
    # ═══════════════════════════════════════════════════════════════════
    #  GROUP HUNTING COMMANDS
    # ═══════════════════════════════════════════════════════════════════
    
    async def handle_groups(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler /groups - Gestión de grupos de caza."""
        msg = update.effective_message
        user = update.effective_user
        
        if not msg or not user:
            return
        
        await context.bot.send_chat_action(
            chat_id=msg.chat_id,
            action=ChatAction.TYPING
        )
        
        # Subcomando
        if not context.args:
            # Mostrar grupos del usuario
            user_groups = self.group_mgr.get_user_groups(user.id)
            
            if not user_groups:
                response = (
                    f"👥 *Grupos de Caza* 👥\n\n"
                    f"No estás en ningún grupo aún.\n\n"
                    f"💡 *Comandos:*\n"
                    f"/groups search - Buscar grupos\n"
                    f"/groups create <nombre> - Crear grupo\n"
                    f"/groups join <id> - Unirse a grupo\n"
                )
            else:
                response = f"👥 *Tus Grupos de Caza* ({len(user_groups)})\n\n"
                
                for group in user_groups[:5]:
                    member = next((m for m in group.members if m.user_id == user.id), None)
                    response += (
                        f"🔹 *{group.name}*\n"
                        f"   👥 {len(group.members)} miembros\n"
                        f"   🎯 {group.total_deals_found} deals encontrados\n"
                        f"   💰 €{group.total_savings:.0f} ahorrados\n"
                    )
                    if member:
                        response += f"   ⭐ Tu rol: {member.role}\n"
                    response += "\n"
            
            keyboard = [
                [
                    InlineKeyboardButton(
                        "🔍 Buscar Grupos",
                        callback_data="groups_search"
                    ),
                    InlineKeyboardButton(
                        "➕ Crear Grupo",
                        callback_data="groups_create"
                    )
                ]
            ]
            
            if user_groups:
                keyboard.append([
                    InlineKeyboardButton(
                        "🏆 Leaderboard Grupal",
                        callback_data="groups_leaderboard"
                    )
                ])
            
            await msg.reply_text(
                response,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return
        
        subcommand = context.args[0].lower()
        
        if subcommand == "search":
            # Buscar grupos públicos
            public_groups = self.group_mgr.search_groups()
            
            if not public_groups:
                await msg.reply_text("❌ No hay grupos públicos disponibles")
                return
            
            response = f"🔍 *Grupos Públicos* ({len(public_groups)})\n\n"
            
            for group in public_groups[:10]:
                response += (
                    f"🔹 *{group.name}*\n"
                    f"   📝 {group.description}\n"
                    f"   👥 {len(group.members)} miembros\n"
                    f"   🎯 {group.total_deals_found} deals\n"
                    f"   ID: `{group.group_id}`\n\n"
                )
            
            response += "\n💡 Usa /groups join <id> para unirte"
            
            await msg.reply_text(response, parse_mode='Markdown')
        
        elif subcommand == "create":
            if len(context.args) < 2:
                await msg.reply_text("⚠️ Uso: /groups create <nombre>")
                return
            
            group_name = " ".join(context.args[1:])
            
            # Crear grupo
            group = self.group_mgr.create_group(
                name=group_name,
                description="Grupo de caza de chollos",
                owner_id=user.id,
                owner_username=user.username or f"User{user.id}",
                group_type=GroupType.PUBLIC
            )
            
            response = (
                f"✅ *Grupo Creado* ✅\n\n"
                f"📛 Nombre: {group.name}\n"
                f"🆔 ID: `{group.group_id}`\n"
                f"👥 Miembros: {len(group.members)}\n\n"
                f"💡 Comparte el ID para que otros se unan"
            )
            
            await msg.reply_text(response, parse_mode='Markdown')
        
        elif subcommand == "join":
            if len(context.args) < 2:
                await msg.reply_text("⚠️ Uso: /groups join <id>")
                return
            
            group_id = context.args[1]
            
            success, message = self.group_mgr.join_group(
                group_id=group_id,
                user_id=user.id,
                username=user.username or f"User{user.id}"
            )
            
            await msg.reply_text(message, parse_mode='Markdown')
    
    # ═══════════════════════════════════════════════════════════════════
    #  LEADERBOARD COMMANDS
    # ═══════════════════════════════════════════════════════════════════
    
    async def handle_leaderboard(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler /leaderboard - Rankings competitivos."""
        msg = update.effective_message
        user = update.effective_user
        
        if not msg or not user:
            return
        
        await context.bot.send_chat_action(
            chat_id=msg.chat_id,
            action=ChatAction.TYPING
        )
        
        # Categoría (opcional)
        category = LeaderboardCategory.DEALS_FOUND.value
        if context.args:
            try:
                category = LeaderboardCategory[context.args[0].upper()].value
            except KeyError:
                pass
        
        # Obtener leaderboard
        leaderboard = self.leaderboard_mgr.get_leaderboard(category, limit=10)
        
        # Obtener posición del usuario
        user_position = self.leaderboard_mgr.get_user_position(category, user.id)
        
        # Construir mensaje
        category_names = {
            'deals_found': '💎 Deals Encontrados',
            'savings_total': '💰 Ahorro Total',
            'referrals': '👥 Referidos',
            'shares': '📤 Compartidas',
            'group_contribution': '🤝 Contribución Grupal',
            'streak': '🔥 Racha Diaria',
            'coins_earned': '🪙 Coins Ganados'
        }
        
        response = f"🏆 *Leaderboard* 🏆\n"
        response += f"📊 {category_names.get(category, category)}\n\n"
        
        if not leaderboard:
            response += "❌ No hay datos disponibles aún"
        else:
            for i, entry in enumerate(leaderboard, 1):
                medal = ""
                if i == 1: medal = "🥇"
                elif i == 2: medal = "🥈"
                elif i == 3: medal = "🥉"
                else: medal = f"{i}️⃣"
                
                tier_emoji = {
                    'BRONZE': '🥉',
                    'SILVER': '🥈',
                    'GOLD': '🥇',
                    'DIAMOND': '💎'
                }.get(entry.tier, '')
                
                response += (
                    f"{medal} {entry.username} {tier_emoji}\n"
                    f"   Score: {entry.score:.0f}\n"
                )
        
        # Posición del usuario
        if user_position:
            response += (
                f"\n📍 *Tu Posición:*\n"
                f"Rank #{user_position.rank}\n"
                f"Score: {user_position.score:.0f}\n"
            )
        
        # Botones de categorías
        keyboard = [
            [
                InlineKeyboardButton(
                    "💎 Deals",
                    callback_data="lb_deals_found"
                ),
                InlineKeyboardButton(
                    "💰 Ahorro",
                    callback_data="lb_savings_total"
                ),
                InlineKeyboardButton(
                    "👥 Referidos",
                    callback_data="lb_referrals"
                )
            ],
            [
                InlineKeyboardButton(
                    "📤 Shares",
                    callback_data="lb_shares"
                ),
                InlineKeyboardButton(
                    "🔥 Racha",
                    callback_data="lb_streak"
                ),
                InlineKeyboardButton(
                    "🪙 Coins",
                    callback_data="lb_coins_earned"
                )
            ]
        ]
        
        await msg.reply_text(
            response,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def handle_season(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler /season - Info de temporada actual."""
        msg = update.effective_message
        
        if not msg:
            return
        
        await context.bot.send_chat_action(
            chat_id=msg.chat_id,
            action=ChatAction.TYPING
        )
        
        # Buscar temporada activa
        active_season = None
        for season in self.leaderboard_mgr.seasons.values():
            if season.is_active:
                active_season = season
                break
        
        if not active_season:
            response = (
                f"⏳ *No hay temporada activa* ⏳\n\n"
                f"La próxima temporada comenzará pronto.\n"
                f"¡Mantente atento para competir por premios!"
            )
        else:
            start_date = datetime.fromisoformat(active_season.start_date)
            end_date = datetime.fromisoformat(active_season.end_date)
            days_left = (end_date - datetime.now()).days
            
            response = (
                f"🏆 *{active_season.name}* 🏆\n\n"
                f"📅 Inicio: {start_date.strftime('%d/%m/%Y')}\n"
                f"📅 Fin: {end_date.strftime('%d/%m/%Y')}\n"
                f"⏰ Días restantes: {days_left}\n\n"
                f"🎯 *Categorías:* {len(active_season.categories)}\n"
            )
            
            if active_season.prizes:
                response += "\n🎁 *Premios:*\n"
                for prize in active_season.prizes[:5]:
                    if prize.rank_start == prize.rank_end:
                        rank_text = f"#{prize.rank_start}"
                    else:
                        rank_text = f"#{prize.rank_start}-{prize.rank_end}"
                    
                    response += (
                        f"\n{prize.badge or '🏆'} {rank_text}\n"
                        f"   💰 {prize.coins} coins\n"
                    )
                    
                    if prize.special_perks:
                        response += f"   ✨ {', '.join(prize.special_perks)}\n"
        
        keyboard = [
            [
                InlineKeyboardButton(
                    "🏆 Ver Leaderboard",
                    callback_data="leaderboard"
                )
            ]
        ]
        
        await msg.reply_text(
            response,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def handle_prizes(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler /prizes - Premios ganados."""
        msg = update.effective_message
        user = update.effective_user
        
        if not msg or not user:
            return
        
        await context.bot.send_chat_action(
            chat_id=msg.chat_id,
            action=ChatAction.TYPING
        )
        
        # Obtener premios del usuario
        user_prizes = self.leaderboard_mgr.get_user_prizes(user.id)
        
        if not user_prizes:
            response = (
                f"🏆 *Tus Premios* 🏆\n\n"
                f"Aún no has ganado premios.\n\n"
                f"💡 ¡Compite en los leaderboards para ganar!\n"
                f"Usa /leaderboard para ver tu posición."
            )
        else:
            unclaimed = [p for p in user_prizes if not p.claimed]
            claimed = [p for p in user_prizes if p.claimed]
            
            total_coins = sum(p.prize.coins for p in claimed)
            
            response = f"🏆 *Tus Premios* ({len(user_prizes)})\n\n"
            
            if unclaimed:
                response += f"🎁 *Premios Pendientes:* {len(unclaimed)}\n\n"
                for prize_dist in unclaimed[:5]:
                    response += (
                        f"{prize_dist.prize.badge or '🏆'}\n"
                        f"   Temporada: {prize_dist.season_id[:8]}\n"
                        f"   Categoría: {prize_dist.category}\n"
                        f"   Rank: #{prize_dist.rank}\n"
                        f"   Premio: {prize_dist.prize.coins} coins\n"
                        f"   ID: `{prize_dist.distribution_id}`\n\n"
                    )
            
            if claimed:
                response += (
                    f"✅ *Premios Reclamados:* {len(claimed)}\n"
                    f"💰 Total coins: {total_coins}\n"
                )
        
        keyboard = []
        if any(not p.claimed for p in user_prizes):
            keyboard.append([
                InlineKeyboardButton(
                    "🎁 Reclamar Premios",
                    callback_data="claim_prizes"
                )
            ])
        
        keyboard.append([
            InlineKeyboardButton(
                "🏆 Ver Leaderboard",
                callback_data="leaderboard"
            )
        ])
        
        await msg.reply_text(
            response,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None
        )
    
    # ═══════════════════════════════════════════════════════════════════
    #  CALLBACK HANDLERS
    # ═══════════════════════════════════════════════════════════════════
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callbacks de IT5."""
        query = update.callback_query
        if not query:
            return
        
        await query.answer()
        
        # Share referral
        if query.data.startswith("share_referral_"):
            await self.handle_share(update, context)
        
        # Leaderboard categories
        elif query.data.startswith("lb_"):
            category = query.data[3:]
            # Simular /leaderboard con categoría
            context.args = [category]
            await self.handle_leaderboard(update, context)
        
        # Groups
        elif query.data == "groups_search":
            context.args = ["search"]
            await self.handle_groups(update, context)
        elif query.data == "groups_create":
            await query.message.reply_text(
                "💡 Usa: /groups create <nombre del grupo>"
            )
        
        # Claim prizes
        elif query.data == "claim_prizes":
            user = update.effective_user
            if not user:
                return
            
            unclaimed = [
                p for p in self.leaderboard_mgr.get_user_prizes(user.id)
                if not p.claimed
            ]
            
            if not unclaimed:
                await query.message.reply_text("❌ No hay premios pendientes")
                return
            
            # Reclamar todos
            total_coins = 0
            badges = []
            
            for prize_dist in unclaimed:
                success, msg, prize = self.leaderboard_mgr.claim_prize(
                    prize_dist.distribution_id
                )
                if success and prize:
                    total_coins += prize.coins
                    if prize.badge:
                        badges.append(prize.badge)
            
            response = (
                f"✅ *Premios Reclamados* ✅\n\n"
                f"💰 Total: {total_coins} FlightCoins\n"
            )
            
            if badges:
                response += f"🏆 Badges: {', '.join(set(badges))}\n"
            
            await query.message.reply_text(response, parse_mode='Markdown')


if __name__ == '__main__':
    # Tests
    print("🧪 Testing ViralGrowthCommandHandler...")
    
    if IT5_AVAILABLE:
        handler = ViralGrowthCommandHandler("fake_token")
        print("✅ Handler initialized successfully")
    else:
        print("❌ IT5 modules not available")
