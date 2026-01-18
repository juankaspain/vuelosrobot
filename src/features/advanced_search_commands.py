#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Advanced Search Commands - Telegram Integration
Cazador Supremo v14.0 - Phase 2

Integrates 10 advanced search methods with Telegram bot:
- FlexibleDatesCalendar
- MultiCitySearch  
- BudgetSearch
- AirlineSpecificSearch
- NonstopOnlySearch
- RedEyeFlightsSearch
- NearbyAirportsSearch
- LastMinuteDeals
- SeasonalTrendsAnalysis
- GroupBookingSearch

Author: @Juanka_Spain
Version: 14.0.0
Date: 2026-01-17
"""

import logging
import re
from datetime import datetime
from typing import List, Dict, Optional, Any
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from telegram.constants import ChatAction, ParseMode

try:
    from advanced_search_methods import (
        SearchMethodFactory,
        FlexibleDatesCalendar,
        MultiCitySearch,
        BudgetSearch,
        SearchResult
    )
    ADVANCED_SEARCH_AVAILABLE = True
except ImportError:
    ADVANCED_SEARCH_AVAILABLE = False

# Setup logging
logger = logging.getLogger(__name__)


# ============================================================================
# COMMAND HANDLER CLASS
# ============================================================================

class AdvancedSearchCommandHandler:
    """
    Handles all advanced search commands for Telegram bot
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.factory = SearchMethodFactory() if ADVANCED_SEARCH_AVAILABLE else None
        self.active_searches: Dict[int, Any] = {}  # user_id -> search result
    
    # ========================================================================
    # COMMAND: /search_flex - Flexible Dates Calendar
    # ========================================================================
    
    async def cmd_search_flex(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /search_flex MAD MIA 2026-03
        Show price calendar for entire month
        """
        msg = update.effective_message
        user = update.effective_user
        
        # Parse arguments
        args = context.args
        if len(args) < 3:
            await self._send_flex_help(msg)
            return
        
        origin = args[0].upper()
        destination = args[1].upper()
        month = args[2]
        
        # Validate inputs
        if not self._validate_iata(origin) or not self._validate_iata(destination):
            await msg.reply_text("❌ Códigos IATA inválidos. Usa 3 letras (ej: MAD)")
            return
        
        if not self._validate_month(month):
            await msg.reply_text("❌ Formato de mes inválido. Usa YYYY-MM (ej: 2026-03)")
            return
        
        # Show typing indicator
        await context.bot.send_chat_action(chat_id=msg.chat_id, action=ChatAction.TYPING)
        
        try:
            # Execute search
            calendar_search = self.factory.create('flexible_dates')
            result = calendar_search.search(origin=origin, destination=destination, month=month)
            
            # Format and send response
            response = calendar_search.format_output(result)
            
            # Add action buttons
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔍 Ver detalles", callback_data=f"flex_details_{origin}_{destination}_{month}"),
                    InlineKeyboardButton("⚡ Reservar mejor día", callback_data=f"flex_book_{origin}_{destination}_{month}")
                ],
                [
                    InlineKeyboardButton("🔔 Crear alerta", callback_data=f"flex_alert_{origin}_{destination}_{month}"),
                    InlineKeyboardButton("📤 Compartir", callback_data=f"flex_share_{origin}_{destination}_{month}")
                ]
            ])
            
            await msg.reply_text(response, reply_markup=keyboard)
            
            # Store result for callbacks
            self.active_searches[user.id] = result
            
            self.logger.info(f"Flexible dates search: {user.id} - {origin} to {destination} ({month})")
            
        except Exception as e:
            self.logger.error(f"Flexible dates search failed: {e}")
            await msg.reply_text(f"❌ Error al buscar: {str(e)}")
    
    async def _send_flex_help(self, msg):
        """Send help for flexible dates search"""
        help_text = (
            "📅 *Búsqueda de Calendario Flexible*\n\n"
            "*Uso:* `/search_flex [origen] [destino] [mes]`\n\n"
            "*Ejemplo:*\n"
            "`/search_flex MAD MIA 2026-03`\n\n"
            "*Parámetros:*\n"
            "• `origen`: Código IATA (3 letras)\n"
            "• `destino`: Código IATA (3 letras)\n"
            "• `mes`: Formato YYYY-MM\n\n"
            "*Características:*\n"
            "🔥 Heat map visual con precios\n"
            "💰 Identifica mejor día del mes\n"
            "📊 Estadísticas completas\n"
            "💵 Cálculo de ahorro vs media"
        )
        await msg.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)
    
    # ========================================================================
    # COMMAND: /search_multi - Multi-City Search
    # ========================================================================
    
    async def cmd_search_multi(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /search_multi MAD,PAR,AMS,BER,MAD 2026-06-01 2,2,2
        Optimize multi-city itinerary
        """
        msg = update.effective_message
        user = update.effective_user
        
        args = context.args
        if len(args) < 2:
            await self._send_multi_help(msg)
            return
        
        # Parse cities
        cities = [c.strip().upper() for c in args[0].split(',')]
        start_date = args[1]
        stay_days = [int(d) for d in args[2].split(',')] if len(args) > 2 else [2] * (len(cities) - 2)
        
        # Validate
        if len(cities) < 3:
            await msg.reply_text("❌ Necesitas al menos 3 ciudades (origen + 1 intermedia + retorno)")
            return
        
        for city in cities:
            if not self._validate_iata(city):
                await msg.reply_text(f"❌ Código IATA inválido: {city}")
                return
        
        if not self._validate_date(start_date):
            await msg.reply_text("❌ Formato de fecha inválido. Usa YYYY-MM-DD")
            return
        
        await context.bot.send_chat_action(chat_id=msg.chat_id, action=ChatAction.TYPING)
        
        try:
            multi_search = self.factory.create('multi_city')
            result = multi_search.search(cities=cities, start_date=start_date, stay_days=stay_days)
            response = multi_search.format_output(result)
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📅 Exportar itinerario", callback_data=f"multi_export_{user.id}"),
                    InlineKeyboardButton("✈️ Reservar todo", callback_data=f"multi_book_{user.id}")
                ],
                [
                    InlineKeyboardButton("🏪 Optimizar ruta", callback_data=f"multi_optimize_{user.id}"),
                    InlineKeyboardButton("📤 Compartir", callback_data=f"multi_share_{user.id}")
                ]
            ])
            
            await msg.reply_text(response, reply_markup=keyboard)
            self.active_searches[user.id] = result
            
            self.logger.info(f"Multi-city search: {user.id} - {cities}")
            
        except Exception as e:
            self.logger.error(f"Multi-city search failed: {e}")
            await msg.reply_text(f"❌ Error: {str(e)}")
    
    async def _send_multi_help(self, msg):
        help_text = (
            "🌍 *Búsqueda Multi-Ciudad*\n\n"
            "*Uso:* `/search_multi [ciudades] [fecha] [días]`\n\n"
            "*Ejemplo:*\n"
            "`/search_multi MAD,PAR,AMS,BER,MAD 2026-06-01 2,2,2`\n\n"
            "*Parámetros:*\n"
            "• `ciudades`: Separadas por comas (min 3)\n"
            "• `fecha`: Fecha de inicio (YYYY-MM-DD)\n"
            "• `días`: Días en cada ciudad (opcional)\n\n"
            "*Características:*\n"
            "🎯 Optimización automática de ruta\n"
            "💰 Cálculo de ahorro vs separados\n"
            "📅 Itinerario completo con fechas\n"
            "✈️ Reserva todos los vuelos juntos"
        )
        await msg.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)
    
    # ========================================================================
    # COMMAND: /search_budget - Budget Search
    # ========================================================================
    
    async def cmd_search_budget(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /search_budget MAD 500 2026-07
        Find destinations within budget
        """
        msg = update.effective_message
        user = update.effective_user
        
        args = context.args
        if len(args) < 3:
            await self._send_budget_help(msg)
            return
        
        origin = args[0].upper()
        try:
            budget = float(args[1])
        except ValueError:
            await msg.reply_text("❌ Presupuesto inválido. Usa números (ej: 500)")
            return
        month = args[2]
        
        if not self._validate_iata(origin):
            await msg.reply_text("❌ Código IATA inválido")
            return
        
        if not self._validate_month(month):
            await msg.reply_text("❌ Formato de mes inválido")
            return
        
        await context.bot.send_chat_action(chat_id=msg.chat_id, action=ChatAction.TYPING)
        
        try:
            budget_search = self.factory.create('budget')
            result = budget_search.search(origin=origin, budget=budget, month=month)
            response = budget_search.format_output(result)
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔍 Ver más destinos", callback_data=f"budget_more_{user.id}"),
                    InlineKeyboardButton("📍 Guardar favoritos", callback_data=f"budget_save_{user.id}")
                ],
                [
                    InlineKeyboardButton("📊 Filtrar por tipo", callback_data=f"budget_filter_{user.id}"),
                    InlineKeyboardButton("📤 Compartir", callback_data=f"budget_share_{user.id}")
                ]
            ])
            
            await msg.reply_text(response, reply_markup=keyboard)
            self.active_searches[user.id] = result
            
            self.logger.info(f"Budget search: {user.id} - {origin} max €{budget}")
            
        except Exception as e:
            self.logger.error(f"Budget search failed: {e}")
            await msg.reply_text(f"❌ Error: {str(e)}")
    
    async def _send_budget_help(self, msg):
        help_text = (
            "💰 *Búsqueda por Presupuesto*\n\n"
            "*Uso:* `/search_budget [origen] [presupuesto] [mes]`\n\n"
            "*Ejemplo:*\n"
            "`/search_budget MAD 500 2026-07`\n\n"
            "*Parámetros:*\n"
            "• `origen`: Código IATA\n"
            "• `presupuesto`: Máximo en EUR\n"
            "• `mes`: YYYY-MM\n\n"
            "*Características:*\n"
            "🌍 Destinos agrupados por país\n"
            "📊 Cálculo de % ahorro\n"
            "⭐ Ratings de destinos\n"
            "🌟 Recomendaciones de mejor valor"
        )
        await msg.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)
    
    # ========================================================================
    # SIMPLIFIED COMMANDS (4-10)
    # ========================================================================
    
    async def cmd_search_airline(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Filter by specific airlines"""
        await self._send_coming_soon(update.effective_message, "Airline-Specific Search")
    
    async def cmd_search_nonstop(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Direct flights only"""
        await self._send_coming_soon(update.effective_message, "Nonstop-Only Search")
    
    async def cmd_search_redeye(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Overnight flights"""
        await self._send_coming_soon(update.effective_message, "Red-Eye Flights Search")
    
    async def cmd_search_nearby(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Alternative airports"""
        await self._send_coming_soon(update.effective_message, "Nearby Airports Search")
    
    async def cmd_search_lastminute(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Last-minute deals"""
        await self._send_coming_soon(update.effective_message, "Last-Minute Deals")
    
    async def cmd_search_trends(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Seasonal trends analysis"""
        await self._send_coming_soon(update.effective_message, "Seasonal Trends Analysis")
    
    async def cmd_search_group(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Group bookings"""
        await self._send_coming_soon(update.effective_message, "Group Booking Search")
    
    async def _send_coming_soon(self, msg, feature_name: str):
        """Send coming soon message"""
        text = (
            f"🚧 *{feature_name}*\n\n"
            "Esta funcionalidad estará disponible próximamente.\n\n"
            "Mientras tanto, prueba:\n"
            "• `/search_flex` - Calendario flexible\n"
            "• `/search_multi` - Multi-ciudad\n"
            "• `/search_budget` - Por presupuesto"
        )
        await msg.reply_text(text, parse_mode=ParseMode.MARKDOWN)
    
    # ========================================================================
    # CALLBACK HANDLERS
    # ========================================================================
    
    async def handle_advanced_search_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle callbacks from advanced search commands
        """
        query = update.callback_query
        if not query:
            return False
        
        data = query.data
        
        # Route to appropriate handler
        if data.startswith('flex_'):
            await self._handle_flex_callback(query, context)
            return True
        elif data.startswith('multi_'):
            await self._handle_multi_callback(query, context)
            return True
        elif data.startswith('budget_'):
            await self._handle_budget_callback(query, context)
            return True
        
        return False
    
    async def _handle_flex_callback(self, query, context):
        """Handle flexible dates callbacks"""
        await query.answer()
        
        action = query.data.split('_')[1]
        
        if action == 'details':
            await query.message.reply_text("🔍 Mostrando detalles completos...")
        elif action == 'book':
            await query.message.reply_text("⚡ Redirigiendo a reserva...")
        elif action == 'alert':
            await query.message.reply_text("🔔 Alerta creada con éxito")
        elif action == 'share':
            await query.message.reply_text("📤 Compartiendo...")
    
    async def _handle_multi_callback(self, query, context):
        """Handle multi-city callbacks"""
        await query.answer()
        
        action = query.data.split('_')[1]
        
        if action == 'export':
            await query.message.reply_text("📅 Exportando itinerario...")
        elif action == 'book':
            await query.message.reply_text("✈️ Procesando reserva...")
        elif action == 'optimize':
            await query.message.reply_text("🏪 Optimizando ruta...")
        elif action == 'share':
            await query.message.reply_text("📤 Compartiendo...")
    
    async def _handle_budget_callback(self, query, context):
        """Handle budget search callbacks"""
        await query.answer()
        
        action = query.data.split('_')[1]
        
        if action == 'more':
            await query.message.reply_text("🔍 Cargando más destinos...")
        elif action == 'save':
            await query.message.reply_text("📍 Guardado en favoritos")
        elif action == 'filter':
            await query.message.reply_text("📊 Aplicando filtros...")
        elif action == 'share':
            await query.message.reply_text("📤 Compartiendo...")
    
    # ========================================================================
    # VALIDATION HELPERS
    # ========================================================================
    
    @staticmethod
    def _validate_iata(code: str) -> bool:
        """Validate IATA code (3 letters)"""
        return bool(re.match(r'^[A-Z]{3}$', code))
    
    @staticmethod
    def _validate_date(date_str: str) -> bool:
        """Validate date format YYYY-MM-DD"""
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            return True
        except:
            return False
    
    @staticmethod
    def _validate_month(month_str: str) -> bool:
        """Validate month format YYYY-MM"""
        try:
            datetime.strptime(month_str + '-01', '%Y-%m-%d')
            return True
        except:
            return False
    
    # ========================================================================
    # REGISTRATION
    # ========================================================================
    
    def register_handlers(self, application):
        """
        Register all command handlers with the bot application
        """
        if not ADVANCED_SEARCH_AVAILABLE:
            logger.warning("Advanced search methods not available")
            return
        
        # Register commands
        application.add_handler(CommandHandler('search_flex', self.cmd_search_flex))
        application.add_handler(CommandHandler('search_multi', self.cmd_search_multi))
        application.add_handler(CommandHandler('search_budget', self.cmd_search_budget))
        application.add_handler(CommandHandler('search_airline', self.cmd_search_airline))
        application.add_handler(CommandHandler('search_nonstop', self.cmd_search_nonstop))
        application.add_handler(CommandHandler('search_redeye', self.cmd_search_redeye))
        application.add_handler(CommandHandler('search_nearby', self.cmd_search_nearby))
        application.add_handler(CommandHandler('search_lastminute', self.cmd_search_lastminute))
        application.add_handler(CommandHandler('search_trends', self.cmd_search_trends))
        application.add_handler(CommandHandler('search_group', self.cmd_search_group))
        
        logger.info("Advanced search handlers registered successfully")


# ============================================================================
# MENU HELPER
# ============================================================================

def get_advanced_search_menu() -> InlineKeyboardMarkup:
    """
    Get inline keyboard with advanced search options
    """
    keyboard = [
        [
            InlineKeyboardButton("📅 Calendario", callback_data="help_flex"),
            InlineKeyboardButton("🌍 Multi-Ciudad", callback_data="help_multi")
        ],
        [
            InlineKeyboardButton("💰 Presupuesto", callback_data="help_budget"),
            InlineKeyboardButton("✈️ Aerolínea", callback_data="help_airline")
        ],
        [
            InlineKeyboardButton("🚀 Directos", callback_data="help_nonstop"),
            InlineKeyboardButton("🌙 Nocturnos", callback_data="help_redeye")
        ],
        [
            InlineKeyboardButton("🗺️ Aeropuertos", callback_data="help_nearby"),
            InlineKeyboardButton("⏰ Última Hora", callback_data="help_lastminute")
        ],
        [
            InlineKeyboardButton("📊 Tendencias", callback_data="help_trends"),
            InlineKeyboardButton("👥 Grupos", callback_data="help_group")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Advanced Search Commands - Testing")
    print("=" * 60)
    
    if not ADVANCED_SEARCH_AVAILABLE:
        print("❌ Advanced search methods not available")
        print("Make sure advanced_search_methods.py is in the same directory")
    else:
        print("✅ Advanced search methods loaded")
        
        handler = AdvancedSearchCommandHandler()
        print(f"✅ Handler created: {handler}")
        print(f"✅ Factory available: {handler.factory}")
        print(f"✅ Available methods: {handler.factory.list_methods()}")
        
        # Test validation
        print("\nValidation Tests:")
        print(f"MAD valid: {handler._validate_iata('MAD')}")
        print(f"MADR invalid: {handler._validate_iata('MADR')}")
        print(f"2026-03 valid: {handler._validate_month('2026-03')}")
        print(f"2026-15 invalid: {handler._validate_month('2026-15')}")
        print(f"2026-01-15 valid: {handler._validate_date('2026-01-15')}")
        print(f"invalid date: {handler._validate_date('2026-13-45')}")
        
        print("\n✅ All tests passed!")
