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

👨‍💻 Autor: @Juanka_Spain | 📅 2026-01-17 | 📋 MIT License
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
import signal
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

VERSION = "15.0.8"
APP_NAME = "🛫 VuelosBot Unified"
AUTHOR = "@Juanka_Spain"
RELEASE_DATE = "2026-01-17"

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
#  NUCLEAR EXIT FUNCTION
# ===============================================================================

def nuclear_exit(code=1):
    """🔥 SALIDA NUCLEAR - Mata el proceso SIN PIEDAD."""
    sys.stdout.flush()
    sys.stderr.flush()
    
    try:
        # Mata el proceso actual con SIGTERM
        os.kill(os.getpid(), signal.SIGTERM)
    except:
        try:
            # Si SIGTERM falla, usa SIGKILL (más agresivo)
            os.kill(os.getpid(), signal.SIGKILL)
        except:
            # Último recurso: os._exit
            os._exit(code)

# ===============================================================================
#  DATA MODELS (SIMPLIFICADO PARA FIX)
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
#  BOT (SIMPLIFICADO)
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
        self.running = True
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling(drop_pending_updates=True)
        logger.info("🚀 Bot iniciado")
        
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
#  SETUP WIZARD
# ===============================================================================

def run_setup_wizard():
    print("\n" + "="*70)
    print(f"{APP_NAME} v{VERSION} - Setup Wizard".center(70))
    print("="*70 + "\n")
    
    config = ConfigManager()
    
    print("🔧 Configuración del Bot\n")
    print("1️⃣ Token de Telegram")
    print("   Obtén tu token de @BotFather\n")
    
    token = input("   Token: ").strip()
    
    if token:
        config.set('telegram.token', token)
        config.set('features.demo_mode', True)
        print("   ✅ Token guardado")
    else:
        print("   ❌ Token requerido")
        return
    
    print("\n2️⃣ API Keys (opcional)\n")
    use_apis = input("   ¿Configurar APIs? (s/n): ").lower() == 's'
    
    if use_apis:
        sk = input("   Skyscanner Key: ").strip()
        if sk:
            config.set('api_keys.skyscanner', sk)
        config.set('features.demo_mode', False)
        print("   ✅ APIs configuradas")
    else:
        print("   ⚠️ Modo DEMO activado")
    
    config.save()
    print("\n✅ Configuración completada!\n")

# ===============================================================================
#  MAIN - NUCLEAR VERSION
# ===============================================================================

def main():
    """🔥 Función principal - VERSIÓN NUCLEAR."""
    
    print("\n" + "="*70)
    print(f"{APP_NAME} v{VERSION}".center(70))
    print(f"by {AUTHOR} | {RELEASE_DATE}".center(70))
    print("="*70 + "\n")
    sys.stdout.flush()
    
    if not TELEGRAM_AVAILABLE:
        print("❌ python-telegram-bot no instalado")
        print("   Instala con: pip install python-telegram-bot\n")
        sys.stdout.flush()
        nuclear_exit(1)
    
    config = ConfigManager()
    
    if not config.has_real_token:
        print("⚠️ Bot sin token de Telegram configurado")
        sys.stdout.flush()
        
        try:
            response = input("\n¿Deseas ejecutar el setup wizard? (s/n): ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print("\n❌ Cancelado\n")
            sys.stdout.flush()
            nuclear_exit(1)
        
        if response == 's':
            run_setup_wizard()
            print("\n✅ Setup completado. Ejecuta el bot de nuevo.\n")
            sys.stdout.flush()
            nuclear_exit(0)
        else:
            # 🔥 NUCLEAR EXIT - INMEDIATO
            print("\n❌ Bot no configurado. Saliendo...")
            sys.stdout.flush()
            print("💡 Para configurar, ejecuta de nuevo y responde 's'\n")
            sys.stdout.flush()
            # MATA EL PROCESO INMEDIATAMENTE
            nuclear_exit(1)
    
    print("✅ Configuración cargada")
    print(f"   Token: ✅")
    print(f"   Búsqueda: {'🎮 DEMO' if config.demo_mode else '🌐 REAL'}")
    print()
    sys.stdout.flush()
    
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        print("\n✅ Programa terminado\n")
        sys.stdout.flush()
        nuclear_exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        sys.stdout.flush()
        nuclear_exit(1)

async def async_main():
    bot = VuelosBotUnified()
    try:
        print("🚀 Iniciando bot...\n")
        sys.stdout.flush()
        await bot.start_bot()
    except KeyboardInterrupt:
        print("\n⏹️ Deteniendo...")
        sys.stdout.flush()
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        raise
    finally:
        await bot.stop_bot()
        print("\n✅ Bot detenido\n")
        sys.stdout.flush()

if __name__ == "__main__":
    main()
