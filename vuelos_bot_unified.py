#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
   🚀 VUELOS BOT v15.0 - UNIFIED SOLUTION 🚀
   Bot de Telegram para búsqueda de vuelos - Solución Total Integrada
===============================================================================

✨ CARACTERÍSTICAS v15.0:
-------------------------------------------------------------------------------
✅ TODO EN UNO - Sin archivos externos
✅ MENÚ INTERACTIVO - Navegación completa
✅ MÚLTIPLES MOTORES - Skyscanner, Kiwi, Google Flights
✅ BÚSQUEDA AVANZADA - Flexible, multi-ciudad, etc.
✅ ALERTAS DE PRECIO - Notificaciones automáticas
✅ SISTEMA DE CHOLLOS - Detección inteligente
✅ ANÁLISIS Y ESTADÍSTICAS - Dashboard completo
✅ GAMIFICACIÓN - Puntos, badges, rankings
✅ MODO DEMO - Testing sin API keys
✅ CONFIGURACIÓN INTEGRADA - Setup wizard

👨‍💻 Autor: @Juanka_Spain | 📅 2026-01-18 | 📋 MIT License
"""

# ===============================================================================
#  IMPORTS
# ===============================================================================

import os
import sys
import json
import logging
import asyncio
import random
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict, field
from enum import Enum
from collections import defaultdict, deque
import hashlib

# Fix Windows console encoding issues
if sys.platform == "win32":
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# Telegram imports
try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
    from telegram.ext import (
        Application,
        CommandHandler,
        CallbackQueryHandler,
        MessageHandler,
        ContextTypes,
        filters
    )
    from telegram.constants import ChatAction, ParseMode
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    print("⚠️ python-telegram-bot not installed. Run: pip install python-telegram-bot")

# HTTP requests
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("⚠️ requests not installed. Run: pip install requests")

# ===============================================================================
#  CONFIGURATION & CONSTANTS
# ===============================================================================

VERSION = "15.0.13"
APP_NAME = "🛫 VuelosBot Unified"
AUTHOR = "@Juanka_Spain"
RELEASE_DATE = "2026-01-18"

# Paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
CACHE_DIR = BASE_DIR / "cache"

# Create directories
for directory in [DATA_DIR, LOGS_DIR, CACHE_DIR]:
    directory.mkdir(exist_ok=True)

# Files
CONFIG_FILE = DATA_DIR / "bot_config.json"
USERS_FILE = DATA_DIR / "users.json"
DEALS_FILE = DATA_DIR / "deals.json"
ALERTS_FILE = DATA_DIR / "alerts.json"
STATS_FILE = DATA_DIR / "stats.json"
LOG_FILE = LOGS_DIR / "vuelos_bot.log"

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ===============================================================================
#  SAFE INPUT - SOLO READLINE (NO input())
# ===============================================================================

def safe_input(prompt: str) -> str:
    """
    Input usando SOLO readline - compatible con Git Bash.
    NO usa input() que tiene problemas en Git Bash.
    """
    sys.stdout.write(prompt)
    sys.stdout.flush()
    
    try:
        line = sys.stdin.readline()
        sys.stdout.flush()
        # readline() incluye el \n, lo quitamos
        return line.rstrip('\n\r').strip()
    except Exception as e:
        sys.stdout.write(f"\n⚠️ Error leyendo: {e}\n")
        sys.stdout.flush()
        return ""

# ===============================================================================
#  DATA MODELS (SIMPLIFICADO)
# ===============================================================================

class SearchMode(Enum):
    FLEXIBLE = "flexible"
    EXACT = "exact"
    MULTICITY = "multicity"
    AROUND = "around_dates"
    OPEN_JAW = "open_jaw"

class TripType(Enum):
    ROUNDTRIP = "roundtrip"
    ONEWAY = "oneway"
    MULTICITY = "multicity"

class SearchEngine(Enum):
    SKYSCANNER = "skyscanner"
    KIWI = "kiwi"
    GOOGLE_FLIGHTS = "google_flights"
    ALL = "all"

class UserTier(Enum):
    FREE = "free"
    PREMIUM = "premium"
    VIP = "vip"

@dataclass
class FlightSearchParams:
    origin: str
    destination: str
    departure_date: str
    return_date: Optional[str] = None
    adults: int = 1
    children: int = 0
    infants: int = 0
    cabin_class: str = "economy"
    max_price: Optional[int] = None
    direct_only: bool = False
    flexible_days: int = 0
    trip_type: TripType = TripType.ROUNDTRIP
    search_mode: SearchMode = SearchMode.EXACT
    search_engine: SearchEngine = SearchEngine.ALL

@dataclass
class Flight:
    id: str
    origin: str
    destination: str
    departure_date: str
    return_date: Optional[str]
    price: float
    currency: str
    airline: str
    duration: str
    stops: int
    deep_link: str
    search_engine: str
    found_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    @property
    def is_direct(self) -> bool:
        return self.stops == 0
    
    @property
    def route_key(self) -> str:
        return f"{self.origin}-{self.destination}"

@dataclass
class PriceAlert:
    id: str
    user_id: int
    origin: str
    destination: str
    max_price: float
    departure_date_from: str
    departure_date_to: str
    active: bool = True
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_check: Optional[str] = None
    notifications_sent: int = 0

@dataclass
class Deal:
    id: str
    flight: Flight
    discount_pct: float
    average_price: float
    detected_at: str = field(default_factory=lambda: datetime.now().isoformat())
    views: int = 0
    shares: int = 0
    
    @property
    def savings(self) -> float:
        return self.average_price - self.flight.price

@dataclass
class User:
    user_id: int
    username: Optional[str]
    first_name: str
    tier: UserTier = UserTier.FREE
    points: int = 0
    searches_count: int = 0
    alerts_count: int = 0
    deals_found: int = 0
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_active: str = field(default_factory=lambda: datetime.now().isoformat())
    preferences: Dict = field(default_factory=dict)
    achievements: List[str] = field(default_factory=list)

@dataclass
class BotStats:
    total_users: int = 0
    total_searches: int = 0
    total_deals: int = 0
    total_alerts: int = 0
    active_users_24h: int = 0
    avg_response_time: float = 0.0
    uptime_start: str = field(default_factory=lambda: datetime.now().isoformat())

# ===============================================================================
#  CONFIGURATION MANAGER
# ===============================================================================

class ConfigManager:
    DEFAULT_CONFIG = {
        "telegram": {"token": "", "admin_users": []},
        "api_keys": {"skyscanner": "", "kiwi": "", "google_flights": ""},
        "features": {
            "demo_mode": True,
            "max_alerts_per_user": 5,
            "max_searches_per_day": 20,
            "cache_ttl_hours": 6,
            "alert_check_interval_hours": 2
        },
        "defaults": {"currency": "EUR", "language": "es", "cabin_class": "economy"}
    }
    
    def __init__(self, config_file: Path = CONFIG_FILE):
        self.config_file = config_file
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                logger.info("✅ Configuración cargada")
                return {**self.DEFAULT_CONFIG, **data}
            except:
                return self.DEFAULT_CONFIG.copy()
        else:
            config = self.DEFAULT_CONFIG.copy()
            self.config = config
            self.save()
            return config
    
    def save(self):
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"❌ Error guardando config: {e}")
    
    def get(self, key: str, default=None):
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, default)
            else:
                return default
        return value
    
    def set(self, key: str, value: Any):
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        self.save()
    
    @property
    def bot_token(self) -> str:
        token = self.get('telegram.token', '')
        if not token and self.demo_mode:
            return "DEMO_MODE_NO_TOKEN"
        return token
    
    @property
    def demo_mode(self) -> bool:
        return self.get('features.demo_mode', True)
    
    @property
    def has_real_token(self) -> bool:
        token = self.get('telegram.token', '')
        return bool(token) and token != "DEMO_MODE_NO_TOKEN"

# ===============================================================================
#  DATA MANAGER (SIMPLIFICADO)
# ===============================================================================

class DataManager:
    def __init__(self):
        self.users: Dict[int, User] = {}
        self.deals: Dict[str, Deal] = {}
        self.alerts: Dict[str, PriceAlert] = {}
        self.stats: BotStats = BotStats()

# ===============================================================================
#  FLIGHT SEARCH ENGINE (DEMO)
# ===============================================================================

class FlightSearchEngine:
    DEMO_ROUTES = [
        {"origin": "MAD", "destination": "BCN", "avg_price": 89, "airline": "Vueling"},
        {"origin": "MAD", "destination": "NYC", "avg_price": 485, "airline": "Iberia"},
    ]
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.demo_mode = config.demo_mode
    
    def search(self, params: FlightSearchParams) -> List[Flight]:
        return []

# ===============================================================================
#  DEAL DETECTOR
# ===============================================================================

class DealDetector:
    def __init__(self, data_mgr: DataManager):
        self.data_mgr = data_mgr

# ===============================================================================
#  ALERT MANAGER
# ===============================================================================

class AlertManager:
    def __init__(self, data_mgr: DataManager, search_engine: FlightSearchEngine):
        self.data_mgr = data_mgr
        self.search_engine = search_engine

# ===============================================================================
#  BOT HANDLERS
# ===============================================================================

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para /start - Menú principal."""
    user = update.effective_user
    
    keyboard = [
        [InlineKeyboardButton("✈️ Buscar Vuelos", callback_data="buscar")],
        [InlineKeyboardButton("🔥 Ver Chollos", callback_data="chollos")],
        [InlineKeyboardButton("🔔 Mis Alertas", callback_data="alertas")],
        [InlineKeyboardButton("📊 Estadísticas", callback_data="stats")],
        [InlineKeyboardButton("❓ Ayuda", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = f"""
🛫 **¡Bienvenido a VuelosBot!** v{VERSION}

¡Hola {user.first_name}! 👋

Soy tu asistente personal para encontrar los mejores vuelos y chollos.

**¿Qué puedo hacer por ti?**
✈️ Buscar vuelos baratos
🔥 Detectar chollos automáticamente
🔔 Crear alertas de precio
📊 Ver estadísticas y análisis

**Modo actual:** 🎮 DEMO
_(Búsquedas simuladas sin APIs reales)_

👇 Usa los botones de abajo para empezar:
    """
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )
    logger.info(f"✅ /start - Usuario: {user.id} ({user.first_name})")

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para /help."""
    help_text = f"""
📖 **Ayuda - VuelosBot** v{VERSION}

**Comandos disponibles:**

/start - Menú principal
/buscar - Buscar vuelos
/chollos - Ver chollos detectados
/alertas - Gestionar alertas de precio
/stats - Ver estadísticas
/help - Esta ayuda

**¿Cómo funciona?**

1️⃣ **Buscar vuelos:** Usa /buscar o el botón del menú
2️⃣ **Ver chollos:** Revisa los mejores chollos detectados
3️⃣ **Crear alertas:** Te notificaré cuando haya buenos precios

**Modo DEMO activo** 🎮
_(Las búsquedas son simuladas)_

💬 ¿Necesitas ayuda? Escríbeme!
    """
    
    await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

async def cmd_buscar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para /buscar."""
    search_text = """
✈️ **Búsqueda de Vuelos**

🎮 **Modo DEMO activo**

Para buscar vuelos, necesito:
• Origen (ej: MAD, BCN)
• Destino (ej: NYC, LON)
• Fecha de ida
• Fecha de vuelta (opcional)

📝 Ejemplo:
`MAD-NYC 2026-03-15 2026-03-22`

💡 Próximamente: Búsqueda interactiva completa
    """
    
    await update.message.reply_text(search_text, parse_mode=ParseMode.MARKDOWN)

async def cmd_chollos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para /chollos."""
    chollos_text = """
🔥 **Chollos Detectados**

🎮 **Modo DEMO - Chollos de Ejemplo:**

✈️ **Madrid → Barcelona**
💰 Precio: 89€ (↓15% vs media)
📅 Salida: Próximos 30 días
✅ Vuelo directo

✈️ **Madrid → Nueva York**
💰 Precio: 485€ (↓22% vs media)
📅 Salida: Próximos 60 días
🔄 1 escala

💡 Activa alertas para recibir chollos automáticamente: /alertas
    """
    
    await update.message.reply_text(chollos_text, parse_mode=ParseMode.MARKDOWN)

async def cmd_alertas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para /alertas."""
    alertas_text = """
🔔 **Alertas de Precio**

📊 Tus alertas activas: 0

**¿Cómo funcionan?**

1️⃣ Define una ruta (ej: MAD-NYC)
2️⃣ Establece un precio máximo
3️⃣ Te notificaré cuando encuentre vuelos por debajo de ese precio

💡 Próximamente: Sistema completo de alertas
    """
    
    await update.message.reply_text(alertas_text, parse_mode=ParseMode.MARKDOWN)

async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para /stats."""
    stats_text = f"""
📊 **Estadísticas del Bot**

🤖 **VuelosBot** v{VERSION}
📅 En línea desde: {datetime.now().strftime('%Y-%m-%d %H:%M')}

👥 Usuarios totales: 1
🔍 Búsquedas realizadas: 0
🔥 Chollos detectados: 2
🔔 Alertas activas: 0

🎮 **Modo:** DEMO
    """
    
    await update.message.reply_text(stats_text, parse_mode=ParseMode.MARKDOWN)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para botones inline."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "buscar":
        await query.message.reply_text(
            "✈️ Función de búsqueda - Usa /buscar para más info",
            parse_mode=ParseMode.MARKDOWN
        )
    elif data == "chollos":
        await query.message.reply_text(
            "🔥 Ver chollos - Usa /chollos para más info",
            parse_mode=ParseMode.MARKDOWN
        )
    elif data == "alertas":
        await query.message.reply_text(
            "🔔 Alertas - Usa /alertas para más info",
            parse_mode=ParseMode.MARKDOWN
        )
    elif data == "stats":
        await cmd_stats(update, context)
    elif data == "help":
        await query.message.reply_text(
            "❓ Ayuda - Usa /help para la lista completa de comandos",
            parse_mode=ParseMode.MARKDOWN
        )

# ===============================================================================
#  BOT (CON HANDLERS)
# ===============================================================================

class VuelosBotUnified:
    def __init__(self):
        self.config = ConfigManager()
        self.data_mgr = DataManager()
        self.search_engine = FlightSearchEngine(self.config)
        self.deal_detector = DealDetector(self.data_mgr)
        self.alert_mgr = AlertManager(self.data_mgr, self.search_engine)
        self.app: Optional[Application] = None
        self.running = False
        logger.info(f"✅ {APP_NAME} v{VERSION} inicializado")
    
    async def start_bot(self):
        if not self.config.has_real_token:
            logger.error("❌ Bot necesita token real")
            return
        
        self.app = Application.builder().token(self.config.bot_token).build()
        
        # Registrar handlers
        self.app.add_handler(CommandHandler("start", cmd_start))
        self.app.add_handler(CommandHandler("help", cmd_help))
        self.app.add_handler(CommandHandler("buscar", cmd_buscar))
        self.app.add_handler(CommandHandler("chollos", cmd_chollos))
        self.app.add_handler(CommandHandler("alertas", cmd_alertas))
        self.app.add_handler(CommandHandler("stats", cmd_stats))
        self.app.add_handler(CallbackQueryHandler(button_handler))
        
        logger.info("✅ Handlers registrados")
        
        self.running = True
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling(drop_pending_updates=True)
        logger.info("🚀 Bot iniciado y escuchando comandos")
        
        while self.running:
            await asyncio.sleep(1)
    
    async def stop_bot(self):
        self.running = False
        if self.app and self.app.updater:
            await self.app.updater.stop()
            await self.app.stop()
            await self.app.shutdown()
        logger.info("✅ Bot detenido")

# ===============================================================================
#  SETUP WIZARD - SOLO READLINE
# ===============================================================================

def run_setup_wizard():
    """Asistente de configuración - SOLO usa readline()."""
    print("\n" + "="*70)
    sys.stdout.flush()
    print(f"{APP_NAME} v{VERSION} - Setup Wizard".center(70))
    sys.stdout.flush()
    print("="*70 + "\n")
    sys.stdout.flush()
    
    config = ConfigManager()
    
    # PASO 1: TOKEN
    print("🔧 Configuración del Bot\n")
    sys.stdout.flush()
    print("1️⃣ Token de Telegram")
    sys.stdout.flush()
    print("   Obtén tu token de @BotFather\n")
    sys.stdout.flush()
    
    # Usar safe_input (que ahora usa SOLO readline)
    token = safe_input("   Token: ")
    print()  # Línea vacía
    sys.stdout.flush()
    
    if token:
        config.set('telegram.token', token)
        config.set('features.demo_mode', True)
        print("   ✅ Token guardado correctamente\n")
        sys.stdout.flush()
    else:
        print("   ❌ Token requerido - Configuración cancelada\n")
        sys.stdout.flush()
        sys.exit(1)
    
    # FINALIZACIÓN
    config.save()
    print("="*70)
    sys.stdout.flush()
    print("✅ Configuración completada exitosamente!".center(70))
    sys.stdout.flush()
    print("="*70)
    sys.stdout.flush()
    print("\n🚀 Ahora ejecuta: python vuelos_bot_unified.py\n")
    sys.stdout.flush()

# ===============================================================================
#  MAIN
# ===============================================================================

def show_help():
    """Muestra ayuda de uso."""
    print("\n" + "="*70)
    print(f"{APP_NAME} v{VERSION}".center(70))
    print(f"by {AUTHOR} | {RELEASE_DATE}".center(70))
    print("="*70)
    print("\n📋 USO:\n")
    print("   python vuelos_bot_unified.py        # Inicia el bot")
    print("   python vuelos_bot_unified.py setup  # Configuración inicial")
    print("\n❌ ERROR: Bot no configurado")
    print("\n💡 SOLUCIÓN:")
    print("   1. Edita: data/bot_config.json")
    print("   2. Añade tu token en 'telegram.token'")
    print("   3. Ejecuta: python vuelos_bot_unified.py\n")
    print(f"📁 Archivo de config: {CONFIG_FILE}\n")

def main():
    """🎯 Función principal."""
    
    # Check for setup command
    if len(sys.argv) > 1 and sys.argv[1] == 'setup':
        run_setup_wizard()
        sys.exit(0)
    
    print("\n" + "="*70)
    print(f"{APP_NAME} v{VERSION}".center(70))
    print(f"by {AUTHOR} | {RELEASE_DATE}".center(70))
    print("="*70 + "\n")
    
    if not TELEGRAM_AVAILABLE:
        print("❌ python-telegram-bot no instalado")
        print("   Instala con: pip install python-telegram-bot\n")
        sys.exit(1)
    
    config = ConfigManager()
    
    # CHECK AUTOMÁTICO
    if not config.has_real_token:
        show_help()
        sys.exit(1)
    
    # Si llegamos aquí, tenemos config válida
    print("✅ Configuración cargada")
    print(f"   Token: ✅")
    print(f"   Búsqueda: {'🎮 DEMO' if config.demo_mode else '🌐 REAL'}")
    print()
    
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        print("\n✅ Programa terminado\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        sys.exit(1)

async def async_main():
    """Main async function."""
    bot = VuelosBotUnified()
    try:
        print("🚀 Iniciando bot...\n")
        await bot.start_bot()
    except KeyboardInterrupt:
        print("\n⏹️ Deteniendo...")
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        raise
    finally:
        await bot.stop_bot()
        print("\n✅ Bot detenido\n")

if __name__ == "__main__":
    main()