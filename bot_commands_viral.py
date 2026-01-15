#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
┌────────────────────────────────────────────────────────────────┐
│  🔥 VIRAL GROWTH COMMANDS HANDLER - IT5              │
│  🚀 Cazador Supremo v13.1 Enterprise                    │
│  🎯 Target: K-factor > 1.2                              │
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
Version: 13.1.0
Date: 2026-01-16
"""

import logging
from datetime import datetime
from typing import Optional, List
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ChatAction

try:
    from viral_growth_system import ReferralManager
    from deal_sharing_system import DealSharingManager
    from group_hunting import GroupHuntingManager, GroupType, MemberRole
    from competitive_leaderboards import CompetitiveLeaderboardManager, LeaderboardCategory, SeasonType
    from social_sharing import SocialSharingManager
    VIRAL_ENABLED = True
except ImportError as e:
    print(f"⚠️ Módulos virales no disponibles: {e}")
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
            self.referral_mgr = ReferralManager()
            self.deal_sharing_mgr = DealSharingManager(bot_username=bot_username)
            self.group_mgr = GroupHuntingManager()
            self.leaderboard_mgr = CompetitiveLeaderboardManager()
            self.social_mgr = SocialSharingManager()
            
            logger.info("✅ ViralCommandHandler inicializado")
        else:
            logger.warning("⚠️ ViralCommandHandler no disponible")
    
    # =========================================================================
    #  REFERRAL SYSTEM COMMANDS
    # =========================================================================
    
    async def handle_refer(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Comando /refer - Muestra código de referido del usuario.
        """
        msg = update.effective_message
        if not msg: return
        
        user = update.effective_user
        user_id = user.id
        username = user.username or f"user_{user_id}"
        
        await context.bot.send_chat_action(chat_id=msg.chat_id, action=ChatAction.TYPING)
        
        # Obtener tier del usuario (desde RetentionManager si está disponible)
        tier = "BRONZE"
        if self.retention_mgr:
            profile = self.retention_mgr.get_or_create_profile(user_id, username)
            tier = profile.tier
        
        # Obtener o crear código de referido
        referral_code = self.referral_mgr.get_or_create_code(user_id, username, tier)
        
        # Link de referido
        referral_link = f"https://t.me/{self.bot_username}?start=ref_{referral_code.code}"
        
        # Stats de referidos
        referrals = self.referral_mgr.get_user_referrals(user_id)
        active_referrals = [r for r in referrals if r.is_active]
        
        # Recompensas del tier actual
        tier_rewards = self.referral_mgr._get_tier_rewards(tier)
        
        # Milestones
        milestones = self.referral_mgr.get_user_milestones(user_id)
        next_milestone = self.referral_mgr._get_next_milestone(len(active_referrals))
        
        response = (
            f"🔥 *TU CÓDIGO DE REFERIDO* 🔥\n\n"
            f"🎫 *Código:* `{referral_code.code}`\n"
            f"🔗 *Link:* {referral_link}\n\n"
            f"👥 *Referidos Activos:* {len(active_referrals)}\n"
            f"💰 *Coins Ganados:* {referral_code.total_coins_earned}\n\n"
            f"🎯 *RECOMPENSAS {tier}:*\n"
            f"   • Tú ganas: {tier_rewards['referrer_coins']} coins\n"
            f"   • Tu amigo: {tier_rewards['referee_coins']} coins\n"
            f"   • Bonus para ti: {tier_rewards['referrer_bonus_desc']}\n"
            f"   • Bonus para él: {tier_rewards['referee_bonus_desc']}\n"
        )
        
        # Añadir info del siguiente milestone
        if next_milestone:
            remaining = next_milestone['count'] - len(active_referrals)
            response += (
                f"\n🏆 *PRÓXIMO MILESTONE:*\n"
                f"   {next_milestone['name']} ({next_milestone['count']} referidos)\n"
                f"   🎯 Te faltan: {remaining}\n"
                f"   🎁 Recompensa: {next_milestone['reward_coins']} coins"
            )
        
        # Milestones desbloqueados
        if milestones:
            response += f"\n\n✅ *Milestones Desbloqueados:* {len(milestones)}"
        
        # Botones
        keyboard = [
            [
                InlineKeyboardButton(
                    "📤 Compartir Código",
                    url=f"https://t.me/share/url?url={referral_link}&text=¡Únete a Cazador Supremo con mi código!"
                )
            ],
            [
                InlineKeyboardButton("📈 Mis Stats", callback_data="viral_myref"),
                InlineKeyboardButton("🏆 Milestones", callback_data="viral_milestones")
            ]
        ]
        
        await msg.reply_text(
            response,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard),
            disable_web_page_preview=True
        )
    
    async def handle_myref(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Comando /myref - Stats detalladas de referidos.
        """
        msg = update.effective_message
        if not msg: return
        
        user = update.effective_user
        user_id = user.id
        
        await context.bot.send_chat_action(chat_id=msg.chat_id, action=ChatAction.TYPING)
        
        # Analytics de referidos
        analytics = self.referral_mgr.get_user_analytics(user_id)
        
        if not analytics:
            await msg.reply_text(
                "🤷 Aún no tienes referidos.\n\n"
                "Usa /refer para obtener tu código y empezar a invitar amigos!"
            )
            return
        
        response = (
            f"📈 *TUS STATS DE REFERIDOS* 📈\n\n"
            f"👥 *Total Referidos:* {analytics['total_referrals']}\n"
            f"✅ *Activos:* {analytics['active_referrals']}\n"
            f"💰 *Coins Ganados:* {analytics['total_coins_earned']}\n"
            f"🎯 *Conversion Rate:* {analytics['conversion_rate']:.1%}\n"
            f"📅 *Primer Referido:* {analytics['first_referral_date'][:10] if analytics['first_referral_date'] else 'N/A'}\n"
            f"🕒 *Último Referido:* {analytics['last_referral_date'][:10] if analytics['last_referral_date'] else 'N/A'}\n\n"
            f"🏆 *Milestones Desbloqueados:* {analytics['milestones_unlocked']}"
        )
        
        # Top referidos
        referrals = self.referral_mgr.get_user_referrals(user_id)
        if referrals:
            response += "\n\n🎖️ *Últimos Referidos:*\n"
            for ref in referrals[:5]:
                status = "✅" if ref.is_active else "❌"
                response += f"   {status} {ref.referred_username} - {ref.created_at[:10]}\n"
        
        keyboard = [
            [InlineKeyboardButton("🔙 Volver", callback_data="viral_refer")]
        ]
        
        await msg.reply_text(
            response,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    # =========================================================================
    #  GROUP HUNTING COMMANDS
    # =========================================================================
    
    async def handle_groups(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Comando /groups - Explorar grupos de caza públicos.
        """
        msg = update.effective_message
        if not msg: return
        
        await context.bot.send_chat_action(chat_id=msg.chat_id, action=ChatAction.TYPING)
        
        # Buscar grupos públicos
        public_groups = self.group_mgr.search_groups(group_type=GroupType.PUBLIC)
        
        if not public_groups:
            response = (
                "🤷 No hay grupos públicos disponibles.\n\n"
                "👥 ¿Quieres crear el primero?\n"
                "Usa /creategroup para empezar!"
            )
            keyboard = [
                [InlineKeyboardButton("➕ Crear Grupo", callback_data="viral_creategroup")]
            ]
        else:
            response = f"👥 *GRUPOS DE CAZA PÚBLICOS* 👥\n\nEncontrados {len(public_groups)} grupos:\n\n"
            
            keyboard = []
            for group in public_groups[:10]:  # Mostrar max 10
                response += (
                    f"🔹 *{group.name}*\n"
                    f"   📋 {group.description}\n"
                    f"   👥 {len(group.members)} miembros\n"
                    f"   💰 {group.total_deals_found} chollos encontrados\n\n"
                )
                
                keyboard.append([
                    InlineKeyboardButton(
                        f"➡️ Unirse a {group.name}",
                        callback_data=f"viral_joingroup_{group.group_id}"
                    )
                ])
            
            keyboard.append([
                InlineKeyboardButton("➕ Crear Nuevo Grupo", callback_data="viral_creategroup")
            ])
        
        await msg.reply_text(
            response,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def handle_creategroup(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Comando /creategroup - Crear nuevo grupo de caza.
        """
        msg = update.effective_message
        if not msg: return
        
        user = update.effective_user
        
        await context.bot.send_chat_action(chat_id=msg.chat_id, action=ChatAction.TYPING)
        
        # Validar args
        if not context.args or len(context.args) < 2:
            await msg.reply_text(
                "⚠️ *Uso incorrecto*\n\n"
                "📝 Uso: `/creategroup <nombre> <descripcion>`\n\n"
                "*Ejemplos:*\n"
                "• `/creategroup 'Cazadores Madrid' 'Chollos desde Madrid'`\n"
                "• `/creategroup 'Viajeros Low-Cost' 'Solo vuelos <300€'`",
                parse_mode='Markdown'
            )
            return
        
        # Parsear nombre y descripción
        name = context.args[0]
        description = ' '.join(context.args[1:])
        
        try:
            # Crear grupo
            group = self.group_mgr.create_group(
                name=name,
                description=description,
                owner_id=user.id,
                owner_username=user.username or f"user_{user.id}",
                group_type=GroupType.PUBLIC,
                min_savings_pct=20.0
            )
            
            response = (
                f"✅ *¡GRUPO CREADO!* ✅\n\n"
                f"🎯 *Nombre:* {group.name}\n"
                f"📋 *Descripción:* {group.description}\n"
                f"👑 *Owner:* Tú\n"
                f"🆔 *ID:* `{group.group_id}`\n\n"
                f"💡 *Próximos pasos:*\n"
                f"1️⃣ Invita amigos con /sharegroup\n"
                f"2️⃣ Empieza a buscar chollos\n"
                f"3️⃣ Gana puntos por contribuciones"
            )
            
            keyboard = [
                [
                    InlineKeyboardButton("👥 Invitar Amigos", callback_data=f"viral_sharegroup_{group.group_id}"),
                    InlineKeyboardButton("📈 Ver Grupo", callback_data=f"viral_viewgroup_{group.group_id}")
                ]
            ]
            
            await msg.reply_text(
                response,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
        except Exception as e:
            await msg.reply_text(f"❌ Error creando grupo: {e}")
    
    async def handle_joingroup(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Comando /joingroup - Unirse a un grupo.
        """
        msg = update.effective_message
        if not msg: return
        
        user = update.effective_user
        
        await context.bot.send_chat_action(chat_id=msg.chat_id, action=ChatAction.TYPING)
        
        if not context.args:
            await msg.reply_text(
                "⚠️ Uso: `/joingroup <group_id>`\n\n"
                "Usa /groups para ver grupos disponibles.",
                parse_mode='Markdown'
            )
            return
        
        group_id = context.args[0]
        
        try:
            success, message = self.group_mgr.join_group(
                group_id=group_id,
                user_id=user.id,
                username=user.username or f"user_{user.id}"
            )
            
            if success:
                group = self.group_mgr.groups.get(group_id)
                if group:
                    response = (
                        f"{message}\n\n"
                        f"🎯 *{group.name}*\n"
                        f"👥 Miembros: {len(group.members)}\n"
                        f"💰 Chollos encontrados: {group.total_deals_found}\n\n"
                        f"💡 Empieza a contribuir y gana puntos!"
                    )
                else:
                    response = message
            else:
                response = message
            
            await msg.reply_text(response, parse_mode='Markdown')
            
        except Exception as e:
            await msg.reply_text(f"❌ Error: {e}")
    
    # =========================================================================
    #  LEADERBOARD COMMANDS
    # =========================================================================
    
    async def handle_leaderboard(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Comando /leaderboard - Ver rankings globales.
        """
        msg = update.effective_message
        if not msg: return
        
        user = update.effective_user
        
        await context.bot.send_chat_action(chat_id=msg.chat_id, action=ChatAction.TYPING)
        
        # Determinar categoría (default: deals_found)
        category = LeaderboardCategory.DEALS_FOUND.value
        if context.args and len(context.args) > 0:
            try:
                category = context.args[0].lower()
                # Validar que la categoría exista
                valid_categories = [c.value for c in LeaderboardCategory]
                if category not in valid_categories:
                    category = LeaderboardCategory.DEALS_FOUND.value
            except:
                pass
        
        # Obtener leaderboard
        leaderboard = self.leaderboard_mgr.get_leaderboard(category, limit=10)
        
        if not leaderboard:
            await msg.reply_text(
                "🤷 El leaderboard está vacío.\n\n"
                "🔥 ¡Sé el primero en la lista!"
            )
            return
        
        # Nombre de categoría legible
        category_names = {
            'deals_found': '🔍 Chollos Encontrados',
            'savings_total': '💰 Ahorro Total',
            'referrals': '👥 Referidos',
            'shares': '📤 Compartidos',
            'group_contribution': '👥 Actividad Grupal',
            'streak': '🔥 Racha',
            'coins_earned': '💸 Coins Ganados'
        }
        
        category_display = category_names.get(category, category.title())
        
        response = f"🏆 *LEADERBOARD GLOBAL* 🏆\n\n🎯 *Categoría:* {category_display}\n\n"
        
        medals = ['🥇', '🥈', '🥉']
        
        for i, entry in enumerate(leaderboard[:10]):
            medal = medals[i] if i < 3 else f"{i+1}️⃣"
            tier_emoji = self._get_tier_emoji(entry.tier)
            
            response += f"{medal} {tier_emoji} *{entry.username}*\n"
            response += f"      📈 Score: {entry.score:.0f}\n\n"
        
        # Posición del usuario actual
        user_position = self.leaderboard_mgr.get_user_position(category, user.id)
        if user_position:
            response += (
                f"\n👤 *Tu Posición:*\n"
                f"   #{user_position.rank} - {user_position.score:.0f} puntos\n"
                f"   {self._get_tier_emoji(user_position.tier)} {user_position.tier}"
            )
        
        # Botones para otras categorías
        keyboard = [
            [
                InlineKeyboardButton("🔍 Chollos", callback_data="viral_lb_deals_found"),
                InlineKeyboardButton("💰 Ahorro", callback_data="viral_lb_savings_total")
            ],
            [
                InlineKeyboardButton("👥 Referidos", callback_data="viral_lb_referrals"),
                InlineKeyboardButton("📤 Shares", callback_data="viral_lb_shares")
            ],
            [
                InlineKeyboardButton("🔥 Racha", callback_data="viral_lb_streak"),
                InlineKeyboardButton("💸 Coins", callback_data="viral_lb_coins_earned")
            ]
        ]
        
        await msg.reply_text(
            response,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def handle_season(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Comando /season - Info de temporada actual.
        """
        msg = update.effective_message
        if not msg: return
        
        await context.bot.send_chat_action(chat_id=msg.chat_id, action=ChatAction.TYPING)
        
        # Obtener temporadas activas
        active_seasons = [s for s in self.leaderboard_mgr.seasons.values() if s.is_active]
        
        if not active_seasons:
            # Crear temporada por defecto si no existe
            season = self.leaderboard_mgr.create_season(
                name="Winter 2026 Challenge",
                season_type=SeasonType.MONTHLY
            )
            active_seasons = [season]
        
        season = active_seasons[0]  # Usar la primera temporada activa
        
        # Calcular días restantes
        end_date = datetime.fromisoformat(season.end_date)
        days_remaining = (end_date - datetime.now()).days
        
        response = (
            f"🎉 *TEMPORADA ACTIVA* 🎉\n\n"
            f"🏆 *{season.name}*\n"
            f"📅 Tipo: {season.season_type.upper()}\n"
            f"📆 Inicio: {season.start_date[:10]}\n"
            f"🗓️ Fin: {season.end_date[:10]}\n"
            f"⏰ Días restantes: {days_remaining}\n\n"
            f"🎯 *Categorías:* {len(season.categories)}\n"
            f"🎁 *Premios:* {len(season.prizes)} niveles\n\n"
            f"💰 *PREMIOS:*\n"
        )
        
        # Mostrar premios
        for prize in season.prizes[:5]:  # Top 5 premios
            if prize.rank_start == prize.rank_end:
                rank_str = f"#{prize.rank_start}"
            else:
                rank_str = f"#{prize.rank_start}-{prize.rank_end}"
            
            response += (
                f"   {prize.badge} *{rank_str}*\n"
                f"      💰 {prize.coins} coins\n"
            )
            
            if prize.special_perks:
                response += f"      ✨ {', '.join(prize.special_perks)}\n"
            
            response += "\n"
        
        keyboard = [
            [
                InlineKeyboardButton("🏆 Ver Leaderboard", callback_data="viral_leaderboard"),
                InlineKeyboardButton("📈 Mi Posición", callback_data="viral_myposition")
            ]
        ]
        
        await msg.reply_text(
            response,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    # =========================================================================
    #  SHARE DEAL COMMAND
    # =========================================================================
    
    async def handle_share_deal(self, update: Update, context: ContextTypes.DEFAULT_TYPE, deal):
        """
        Muestra botones de compartir para un deal.
        Llamado desde el comando /deals cuando se encuentra un chollo.
        """
        msg = update.effective_message
        if not msg: return
        
        user = update.effective_user
        
        # Crear deal en el sistema de sharing
        deal_obj = self.deal_sharing_mgr.create_deal(
            route=deal.flight_price.route,
            origin=deal.flight_price.route.split('✈️')[0],
            destination=deal.flight_price.route.split('✈️')[1] if '✈️' in deal.flight_price.route else "DEST",
            price=deal.flight_price.price,
            currency=deal.flight_price.currency,
            airline=deal.flight_price.airline or "N/A",
            departure_date=deal.flight_price.departure_date or "N/A",
            return_date=None,
            url="https://example.com/book",  # TODO: Real booking URL
            savings_pct=deal.savings_pct
        )
        
        # Generar botones de share
        share_buttons = self.deal_sharing_mgr.create_share_buttons(
            deal_id=deal_obj.deal_id,
            user_id=user.id
        )
        
        share_text = (
            f"\n\n📤 *¿Quieres compartir este chollo?*\n"
            f"🎁 Gana 50 coins por compartir!"
        )
        
        await msg.reply_text(
            share_text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(share_buttons)
        )
    
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
        elif data == "viral_milestones":
            await self._show_milestones(update, context)
        
        # Group callbacks
        elif data == "viral_creategroup":
            await query.message.reply_text(
                "📝 Usa: `/creategroup <nombre> <descripcion>`",
                parse_mode='Markdown'
            )
        elif data.startswith("viral_joingroup_"):
            group_id = data.replace("viral_joingroup_", "")
            context.args = [group_id]
            await self.handle_joingroup(update, context)
        
        # Leaderboard callbacks
        elif data == "viral_leaderboard":
            await self.handle_leaderboard(update, context)
        elif data.startswith("viral_lb_"):
            category = data.replace("viral_lb_", "")
            context.args = [category]
            await self.handle_leaderboard(update, context)
    
    # =========================================================================
    #  HELPER METHODS
    # =========================================================================
    
    def _get_tier_emoji(self, tier: str) -> str:
        """Obtiene emoji del tier."""
        tier_emojis = {
            'BRONZE': '🥉',
            'SILVER': '🥈',
            'GOLD': '🥇',
            'DIAMOND': '💎'
        }
        return tier_emojis.get(tier.upper(), '⭐')
    
    async def _show_milestones(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Muestra milestones disponibles."""
        msg = update.effective_message
        user = update.effective_user
        
        referrals = self.referral_mgr.get_user_referrals(user.id)
        active_count = len([r for r in referrals if r.is_active])
        
        milestones_info = [
            (5, 1000, '🎖️'),
            (10, 2500, '🏆'),
            (25, 5000, '👑'),
            (50, 10000, '💎')
        ]
        
        response = f"🎯 *MILESTONES DE REFERIDOS* 🎯\n\nTu progreso: {active_count} referidos activos\n\n"
        
        for count, reward, emoji in milestones_info:
            status = "✅" if active_count >= count else "⏳"
            progress = min(100, int((active_count / count) * 100))
            
            response += (
                f"{status} {emoji} *{count} Referidos*\n"
                f"   🎁 Recompensa: {reward} coins\n"
                f"   📈 Progreso: {progress}%\n\n"
            )
        
        keyboard = [
            [InlineKeyboardButton("🔙 Volver", callback_data="viral_refer")]
        ]
        
        await msg.reply_text(
            response,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


if __name__ == '__main__':
    # Quick test
    print("🧪 Testing ViralCommandHandler...")
    
    if VIRAL_ENABLED:
        handler = ViralCommandHandler()
        print("✅ Handler inicializado correctamente")
    else:
        print("❌ Módulos virales no disponibles")
