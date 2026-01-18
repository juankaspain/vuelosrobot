#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🛠️ PATCH v13.2.1 - ONBOARDING INTERACTIVE FIX

Este archivo contiene los métodos que deben ser añadidos/actualizados
en cazador_supremo_enterprise.py para habilitar el onboarding interactivo.

INSTRUCCIONES:
1. Añadir estos métodos a la clase CazadorSupremoBot
2. Reemplazar start_command() existente
3. Añadir handle_callback() si no existe
4. Añadir _handle_onboarding_callback() (NUEVO)
"""

# =============================================================================
# MÉTODO 1: start_command() - CON ONBOARDING
# Reemplazar el método existente con este
# =============================================================================

async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start con onboarding y deep links."""
    user = update.effective_user
    args = context.args
    
    # Registrar usuario
    if RETENTION_ENABLED:
        self.retention_mgr.ensure_user(user.id, user.username or "user")
    
    # Manejar deep links
    if args and len(args) > 0:
        deep_link = args[0]
        
        # Referral link
        if deep_link.startswith("ref_"):
            if VIRAL_ENABLED:
                await self.viral_handler.handle_referral(update, context, deep_link)
                return
        
        # Deal share link
        elif deep_link.startswith("deal_"):
            if VIRAL_ENABLED:
                await self.viral_handler.handle_deal_share(update, context, deep_link)
                return
    
    # Verificar si es nuevo usuario
    if RETENTION_ENABLED:
        if not self.onboarding_mgr.has_completed_onboarding(user.id):
            # Iniciar onboarding interactivo
            welcome_msg = OnboardingMessages.welcome(user.first_name or user.username or "usuario")
            
            keyboard = [[InlineKeyboardButton("🚀 ¡Empezar!", callback_data="onb_start")]]
            
            await update.message.reply_text(
                welcome_msg,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return
    
    # Usuario existente - mostrar dashboard
    header = (
        f"🎆 *{APP_NAME} v{VERSION}* 🎆\n\n"
        f"¡Hola {user.first_name or user.username}! 👋\n\n"
        f"Estoy listo para encontrar los mejores chollos de vuelos.\n"
    )
    
    if RETENTION_ENABLED:
        profile = self.retention_mgr.get_user_profile(user.id)
        header += (
            f"\n💰 *{profile.coins}* FlightCoins\n"
            f"🎯 Tier: {profile.tier.value}\n"
            f"🔥 Streak: {profile.current_streak} días\n"
        )
    
    # Quick actions
    keyboard = []
    if RETENTION_ENABLED:
        keyboard = self.quick_actions.get_main_keyboard()
    
    await update.message.reply_text(
        header,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None
    )

# =============================================================================
# MÉTODO 2: handle_callback() - ROUTING COMPLETO
# Añadir este método si no existe, o actualizar routing
# =============================================================================

async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja todos los callbacks de botones inline."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user = update.effective_user
    
    # Onboarding callbacks
    if data.startswith("onb_"):
        await self._handle_onboarding_callback(update, context)
        return
    
    # Quick actions callbacks
    if data.startswith("qa_"):
        await self.quick_actions.handle_callback(update, context)
        return
    
    # Viral callbacks
    if VIRAL_ENABLED and data.startswith(("share_", "group_", "lb_")):
        await self.viral_handler.handle_callback(update, context)
        return

# =============================================================================
# MÉTODO 3: _handle_onboarding_callback() - NUEVO MÉTODO
# Añadir este método completo a la clase
# =============================================================================

async def _handle_onboarding_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja los callbacks del flujo de onboarding."""
    query = update.callback_query
    user = update.effective_user
    data = query.data
    
    if data == "onb_start":
        # Iniciar paso 1: Selección de región
        self.onboarding_mgr.advance_to_step1(user.id)
        
        step1_msg = OnboardingMessages.step1_region()
        keyboard = [
            [InlineKeyboardButton("🇪🇺 Europa", callback_data="onb_region_europe")],
            [InlineKeyboardButton("🇺🇸 USA", callback_data="onb_region_usa")],
            [InlineKeyboardButton("🌏 Asia", callback_data="onb_region_asia")],
            [InlineKeyboardButton("🌎 Latam", callback_data="onb_region_latam")]
        ]
        
        await query.edit_message_text(
            step1_msg,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif data.startswith("onb_region_"):
        # Guardar región y avanzar a paso 2: Presupuesto
        region_str = data.replace("onb_region_", "")
        region = TravelRegion(region_str)
        self.onboarding_mgr.set_travel_region(user.id, region)
        
        step2_msg = OnboardingMessages.step2_budget()
        keyboard = [
            [InlineKeyboardButton("🟢 Económico (<€300)", callback_data="onb_budget_low")],
            [InlineKeyboardButton("🟡 Moderado (€300-600)", callback_data="onb_budget_medium")],
            [InlineKeyboardButton("🔵 Premium (>€600)", callback_data="onb_budget_high")]
        ]
        
        await query.edit_message_text(
            step2_msg,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif data.startswith("onb_budget_"):
        # Guardar presupuesto y avanzar a paso 3: Primer valor
        budget_str = data.replace("onb_budget_", "")
        budget = BudgetRange(budget_str)
        self.onboarding_mgr.set_budget_range(user.id, budget)
        
        # Mostrar loading message
        await query.edit_message_text(
            "🔍 *Buscando tus primeros chollos...*\n\nEsto tomará solo unos segundos ⏱️",
            parse_mode='Markdown'
        )
        
        # Buscar deals personalizados
        routes = self.onboarding_mgr.get_recommended_routes(user.id)
        found_deals = []
        
        for origin, dest, name in routes:
            try:
                route = FlightRoute(origin=origin, dest=dest, name=name)
                price = self.scanner._scan_single(route)
                if price:
                    found_deals.append(price)
                    
                    # Añadir a watchlist automáticamente
                    threshold = self.onboarding_mgr.get_watchlist_threshold(
                        user.id, 
                        budget.value
                    )
                    self.retention_mgr.add_to_watchlist(
                        user.id,
                        user.username or "user",
                        route.route_code,
                        threshold
                    )
            except Exception as e:
                logger.error(f"Error scanning route {name}: {e}")
        
        # Completar onboarding
        progress = self.onboarding_mgr.complete_onboarding(user.id)
        
        # Dar bonus de coins
        from onboarding_flow import ONBOARDING_COMPLETION_BONUS
        self.retention_mgr.award_coins(
            user.id,
            user.username or "user", 
            ONBOARDING_COMPLETION_BONUS,
            "Completar onboarding"
        )
        
        # Mostrar mensaje de completación
        completion_msg = OnboardingMessages.completion(
            ONBOARDING_COMPLETION_BONUS,
            progress.total_time_seconds
        )
        
        await query.edit_message_text(completion_msg, parse_mode='Markdown')
        
        # Mostrar los deals encontrados
        if found_deals:
            deals_msg = f"✈️ *Tus primeros {len(found_deals)} vuelos en watchlist:*\n\n"
            for i, fp in enumerate(found_deals[:3], 1):
                deals_msg += f"{i}️⃣ {fp.name}: {fp.format_price()}\n"
            
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=deals_msg,
                parse_mode='Markdown'
            )

# =============================================================================
# NOTAS DE IMPLEMENTACIÓN
# =============================================================================
"""
Para aplicar este patch:

1. Abrir cazador_supremo_enterprise.py
2. Localizar la clase CazadorSupremoBot
3. Reemplazar start_command() con el MÉTODO 1
4. Añadir/actualizar handle_callback() con el MÉTODO 2
5. Añadir _handle_onboarding_callback() (MÉTODO 3) como nuevo método
6. Guardar y probar

Dependencias requeridas:
- from onboarding_flow import OnboardingManager, TravelRegion, BudgetRange, OnboardingMessages, ONBOARDING_COMPLETION_BONUS
- FlightRoute class
- RetentionManager
- FlightScanner

VERIFICACIÓN:
✅ Importaciones en top del archivo
✅ OnboardingManager inicializado en __init__()
✅ Callback handler registrado en _register_handlers()
"""
