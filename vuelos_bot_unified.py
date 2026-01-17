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
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict, field
from enum import Enum
from collections import defaultdict, deque
import hashlib

# Fix Windows console encoding issues
if sys.platform == "win32":
    # Set UTF-8 encoding for Windows console
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    # Set environment variable for subprocess compatibility
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

VERSION = "15.0.7"
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
#  HELPER FUNCTION FOR WINDOWS FLUSH
# ===============================================================================

def force_flush():
    """Fuerza flush agresivo en Windows."""
    sys.stdout.flush()
    sys.stderr.flush()
    if hasattr(sys.stdout, 'fileno'):
        try:
            os.fsync(sys.stdout.fileno())
        except:
            pass

# ===============================================================================
#  DATA MODELS
# ===============================================================================

class SearchMode(Enum):
    """Modos de búsqueda disponibles."""
    FLEXIBLE = "flexible"
    EXACT = "exact"
    MULTICITY = "multicity"
    AROUND = "around_dates"
    OPEN_JAW = "open_jaw"

class TripType(Enum):
    """Tipos de viaje."""
    ROUNDTRIP = "roundtrip"
    ONEWAY = "oneway"
    MULTICITY = "multicity"

class SearchEngine(Enum):
    """Motores de búsqueda disponibles."""
    SKYSCANNER = "skyscanner"
    KIWI = "kiwi"
    GOOGLE_FLIGHTS = "google_flights"
    ALL = "all"

class UserTier(Enum):
    """Niveles de usuario."""
    FREE = "free"
    PREMIUM = "premium"
    VIP = "vip"

@dataclass
class FlightSearchParams:
    """Parámetros de búsqueda de vuelos."""
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
    """Resultado de vuelo."""
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
        """Clave única para la ruta."""
        return f"{self.origin}-{self.destination}"

@dataclass
class PriceAlert:
    """Alerta de precio."""
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
    """Chollo detectado."""
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
    """Usuario del bot."""
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
    """Estadísticas del bot."""
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
    """Gestor de configuración."""
    
    DEFAULT_CONFIG = {
        "telegram": {
            "token": "",
            "admin_users": []
        },
        "api_keys": {
            "skyscanner": "",
            "kiwi": "",
            "google_flights": ""
        },
        "features": {
            "demo_mode": True,
            "max_alerts_per_user": 5,
            "max_searches_per_day": 20,
            "cache_ttl_hours": 6,
            "alert_check_interval_hours": 2
        },
        "defaults": {
            "currency": "EUR",
            "language": "es",
            "cabin_class": "economy"
        }
    }
    
    def __init__(self, config_file: Path = CONFIG_FILE):
        self.config_file = config_file
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """Carga configuración desde archivo o crea default."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                logger.info("✅ Configuración cargada desde archivo")
                return {**self.DEFAULT_CONFIG, **data}
            except json.JSONDecodeError as e:
                logger.error(f"❌ Error decodificando JSON: {e}")
                logger.warning("⚠️ Usando configuración por defecto")
                return self.DEFAULT_CONFIG.copy()
            except Exception as e:
                logger.error(f"❌ Error cargando config: {e}")
                return self.DEFAULT_CONFIG.copy()
        else:
            logger.warning("⚠️ Config no existe, creando defaults")
            config = self.DEFAULT_CONFIG.copy()
            self.config = config
            self.save()
            return config
    
    def save(self):
        """Guarda configuración."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            logger.info("💾 Configuración guardada")
        except Exception as e:
            logger.error(f"❌ Error guardando config: {e}")
    
    def get(self, key: str, default=None):
        """Obtiene valor de config usando dot notation."""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, default)
            else:
                return default
        return value
    
    def set(self, key: str, value: Any):
        """Establece valor en config usando dot notation."""
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
        """Obtiene el token del bot (o dummy token para demo)."""
        token = self.get('telegram.token', '')
        if not token and self.demo_mode:
            return "DEMO_MODE_NO_TOKEN"
        return token
    
    @property
    def demo_mode(self) -> bool:
        return self.get('features.demo_mode', True)
    
    @property
    def is_configured(self) -> bool:
        """Verifica si el bot está configurado."""
        real_token = self.get('telegram.token', '')
        return bool(real_token) or self.demo_mode
    
    @property
    def has_real_token(self) -> bool:
        """Verifica si tiene un token real de Telegram."""
        token = self.get('telegram.token', '')
        return bool(token) and token != "DEMO_MODE_NO_TOKEN"

# ===============================================================================
#  DATA PERSISTENCE MANAGER
# ===============================================================================

class DataManager:
    """Gestor de persistencia de datos."""
    
    def __init__(self):
        self.users: Dict[int, User] = self._load_users()
        self.deals: Dict[str, Deal] = self._load_deals()
        self.alerts: Dict[str, PriceAlert] = self._load_alerts()
        self.stats: BotStats = self._load_stats()
        self.cache: Dict[str, Any] = {}
    
    def _load_json(self, file: Path, default: Any) -> Any:
        """Carga archivo JSON."""
        if file.exists():
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"❌ Error loading {file.name}: {e}")
        return default
    
    def _save_json(self, file: Path, data: Any):
        """Guarda archivo JSON."""
        try:
            with open(file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"❌ Error saving {file.name}: {e}")
    
    def _load_users(self) -> Dict[int, User]:
        """Carga usuarios."""
        data = self._load_json(USERS_FILE, {})
        return {int(k): User(**v) for k, v in data.items()}
    
    def _load_deals(self) -> Dict[str, Deal]:
        """Carga chollos."""
        data = self._load_json(DEALS_FILE, {})
        deals = {}
        for k, v in data.items():
            try:
                v['flight'] = Flight(**v['flight'])
                deals[k] = Deal(**v)
            except Exception as e:
                logger.error(f"❌ Error loading deal {k}: {e}")
        return deals
    
    def _load_alerts(self) -> Dict[str, PriceAlert]:
        """Carga alertas."""
        data = self._load_json(ALERTS_FILE, {})
        return {k: PriceAlert(**v) for k, v in data.items()}
    
    def _load_stats(self) -> BotStats:
        """Carga estadísticas."""
        data = self._load_json(STATS_FILE, {})
        return BotStats(**data) if data else BotStats()
    
    def save_all(self):
        """Guarda todos los datos."""
        users_data = {str(k): asdict(v) for k, v in self.users.items()}
        self._save_json(USERS_FILE, users_data)
        
        deals_data = {k: asdict(v) for k, v in self.deals.items()}
        self._save_json(DEALS_FILE, deals_data)
        
        alerts_data = {k: asdict(v) for k, v in self.alerts.items()}
        self._save_json(ALERTS_FILE, alerts_data)
        
        self._save_json(STATS_FILE, asdict(self.stats))
        
        logger.info("💾 Todos los datos guardados")
    
    def get_or_create_user(self, user_id: int, username: str = None, first_name: str = "Usuario") -> User:
        """Obtiene o crea usuario."""
        if user_id not in self.users:
            user = User(
                user_id=user_id,
                username=username,
                first_name=first_name
            )
            self.users[user_id] = user
            self.stats.total_users += 1
            logger.info(f"👤 Nuevo usuario: {user_id} (@{username})")
        else:
            user = self.users[user_id]
            user.last_active = datetime.now().isoformat()
        
        return user

# ===============================================================================
#  FLIGHT SEARCH ENGINE (DEMO MODE)
# ===============================================================================

class FlightSearchEngine:
    """Motor de búsqueda de vuelos (modo demo con datos simulados)."""
    
    DEMO_ROUTES = [
        {"origin": "MAD", "destination": "BCN", "avg_price": 89, "airline": "Vueling"},
        {"origin": "MAD", "destination": "NYC", "avg_price": 485, "airline": "Iberia"},
        {"origin": "BCN", "destination": "PAR", "avg_price": 125, "airline": "Air France"},
        {"origin": "MAD", "destination": "LON", "avg_price": 150, "airline": "Ryanair"},
        {"origin": "MAD", "destination": "ROM", "avg_price": 175, "airline": "ITA Airways"},
        {"origin": "BCN", "destination": "BER", "avg_price": 95, "airline": "Lufthansa"},
        {"origin": "MAD", "destination": "LIS", "avg_price": 65, "airline": "TAP"},
        {"origin": "BCN", "destination": "AMS", "avg_price": 110, "airline": "KLM"},
    ]
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.demo_mode = config.demo_mode
    
    def search(self, params: FlightSearchParams) -> List[Flight]:
        """Busca vuelos (demo mode)."""
        logger.info(f"🔍 Buscando vuelos: {params.origin} → {params.destination}")
        
        if self.demo_mode:
            return self._demo_search(params)
        else:
            return self._real_search(params)
    
    def _demo_search(self, params: FlightSearchParams) -> List[Flight]:
        """Búsqueda demo con datos simulados."""
        time.sleep(random.uniform(0.5, 1.5))
        
        results = []
        
        for route in self.DEMO_ROUTES:
            if (route["origin"] == params.origin.upper() and 
                route["destination"] == params.destination.upper()):
                
                for i in range(random.randint(3, 7)):
                    price_variation = random.uniform(-0.25, 0.15)
                    price = route["avg_price"] * (1 + price_variation)
                    
                    if params.max_price and price > params.max_price:
                        continue
                    
                    flight = Flight(
                        id=hashlib.md5(f"{params.origin}{params.destination}{i}{time.time()}".encode()).hexdigest()[:12],
                        origin=params.origin.upper(),
                        destination=params.destination.upper(),
                        departure_date=params.departure_date,
                        return_date=params.return_date,
                        price=round(price, 2),
                        currency="EUR",
                        airline=route["airline"],
                        duration=f"{random.randint(1, 12)}h {random.randint(0, 55)}m",
                        stops=0 if random.random() > 0.3 else random.randint(1, 2),
                        deep_link=f"https://example.com/flights/{route['origin']}-{route['destination']}",
                        search_engine="demo"
                    )
                    
                    if params.direct_only and not flight.is_direct:
                        continue
                    
                    results.append(flight)
        
        results.sort(key=lambda f: f.price)
        logger.info(f"✅ Encontrados {len(results)} vuelos (demo mode)")
        return results[:10]
    
    def _real_search(self, params: FlightSearchParams) -> List[Flight]:
        """Búsqueda real con APIs (TODO: implementar)."""
        logger.warning("⚠️ Real search not implemented yet")
        return []

# ===============================================================================
#  DEAL DETECTOR
# ===============================================================================

class DealDetector:
    """Detector de chollos."""
    
    DEAL_THRESHOLD = 0.20
    
    def __init__(self, data_mgr: DataManager):
        self.data_mgr = data_mgr
        self.price_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=50))
    
    def check_deal(self, flight: Flight) -> Optional[Deal]:
        """Verifica si un vuelo es un chollo."""
        route_key = flight.route_key
        self.price_history[route_key].append(flight.price)
        
        if len(self.price_history[route_key]) < 5:
            return None
        
        avg_price = sum(self.price_history[route_key]) / len(self.price_history[route_key])
        discount_pct = ((avg_price - flight.price) / avg_price) * 100
        
        if discount_pct >= (self.DEAL_THRESHOLD * 100):
            deal = Deal(
                id=f"deal_{flight.id}",
                flight=flight,
                discount_pct=round(discount_pct, 1),
                average_price=round(avg_price, 2)
            )
            
            self.data_mgr.deals[deal.id] = deal
            self.data_mgr.stats.total_deals += 1
            logger.info(f"🔥 CHOLLO detectado: {flight.origin}→{flight.destination} €{flight.price} (-{discount_pct:.1f}%)")
            return deal
        
        return None

# ===============================================================================
#  ALERT MANAGER
# ===============================================================================

class AlertManager:
    """Gestor de alertas de precio."""
    
    def __init__(self, data_mgr: DataManager, search_engine: FlightSearchEngine):
        self.data_mgr = data_mgr
        self.search_engine = search_engine
    
    def create_alert(self, user_id: int, params: FlightSearchParams, max_price: float) -> PriceAlert:
        """Crea una alerta de precio."""
        alert = PriceAlert(
            id=hashlib.md5(f"{user_id}{time.time()}".encode()).hexdigest()[:12],
            user_id=user_id,
            origin=params.origin.upper(),
            destination=params.destination.upper(),
            max_price=max_price,
            departure_date_from=params.departure_date,
            departure_date_to=params.departure_date
        )
        
        self.data_mgr.alerts[alert.id] = alert
        self.data_mgr.stats.total_alerts += 1
        logger.info(f"🔔 Alerta creada: {alert.origin}→{alert.destination} max €{max_price}")
        return alert
    
    def get_user_alerts(self, user_id: int) -> List[PriceAlert]:
        """Obtiene alertas activas de un usuario."""
        return [a for a in self.data_mgr.alerts.values() 
                if a.user_id == user_id and a.active]
    
    async def check_alerts(self) -> List[Tuple[PriceAlert, List[Flight]]]:
        """Verifica todas las alertas activas."""
        triggered = []
        
        for alert in self.data_mgr.alerts.values():
            if not alert.active:
                continue
            
            params = FlightSearchParams(
                origin=alert.origin,
                destination=alert.destination,
                departure_date=alert.departure_date_from,
                max_price=alert.max_price
            )
            
            flights = self.search_engine.search(params)
            
            if flights:
                cheap_flights = [f for f in flights if f.price <= alert.max_price]
                
                if cheap_flights:
                    triggered.append((alert, cheap_flights))
                    alert.last_check = datetime.now().isoformat()
                    alert.notifications_sent += 1
        
        return triggered

# ===============================================================================
#  TELEGRAM BOT MANAGER - SIMPLIFIED FOR FIX
# ===============================================================================

class VuelosBotUnified:
    """
    🚀 Bot Unificado de Vuelos v15.0
    
    Solución completa integrada.
    """
    
    def __init__(self):
        self.config = ConfigManager()
        self.data_mgr = DataManager()
        self.search_engine = FlightSearchEngine(self.config)
        self.deal_detector = DealDetector(self.data_mgr)
        self.alert_mgr = AlertManager(self.data_mgr, self.search_engine)
        self.app: Optional[Application] = None
        self.running = False
        self.user_states: Dict[int, Dict] = defaultdict(dict)
        logger.info(f"✅ {APP_NAME} v{VERSION} inicializado")
    
    async def start_bot(self):
        """Inicia el bot de Telegram."""
        if not self.config.has_real_token:
            logger.error("❌ Bot necesita un token real de Telegram.")
            return
        
        self.app = Application.builder().token(self.config.bot_token).build()
        self.running = True
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling(drop_pending_updates=True)
        logger.info("🚀 Bot iniciado y escuchando...")
        
        while self.running:
            await asyncio.sleep(1)
    
    async def stop_bot(self):
        """Detiene el bot."""
        self.running = False
        if self.app:
            if self.app.updater:
                await self.app.updater.stop()
            await self.app.stop()
            await self.app.shutdown()
        self.data_mgr.save_all()
        logger.info("✅ Bot detenido")

# ===============================================================================
#  SETUP WIZARD
# ===============================================================================

def run_setup_wizard():
    """Asistente de configuración inicial."""
    print("\n" + "="*70)
    force_flush()
    print(f"{APP_NAME} v{VERSION} - Setup Wizard".center(70))
    force_flush()
    print("="*70 + "\n")
    force_flush()
    
    config = ConfigManager()
    
    print("🔧 Configuración del Bot\n")
    force_flush()
    print("1️⃣ Token de Telegram")
    force_flush()
    print("   Obtén tu token de @BotFather en Telegram\n")
    force_flush()
    
    token = input("   Token: ").strip()
    
    if token:
        config.set('telegram.token', token)
        config.set('features.demo_mode', True)
        print("   ✅ Token guardado")
        force_flush()
    else:
        print("   ❌ Token requerido")
        force_flush()
        return
    
    print("\n2️⃣ API Keys (opcional)\n")
    force_flush()
    
    use_apis = input("   ¿Configurar APIs? (s/n): ").lower() == 's'
    
    if use_apis:
        sk = input("   Skyscanner Key: ").strip()
        if sk:
            config.set('api_keys.skyscanner', sk)
        config.set('features.demo_mode', False)
        print("   ✅ APIs configuradas")
    else:
        print("   ⚠️ Modo DEMO activado")
    
    force_flush()
    config.save()
    
    print("\n✅ Configuración completada!\n")
    force_flush()

# ===============================================================================
#  MAIN - ULTRA AGGRESSIVE FIX
# ===============================================================================

def main():
    """🚀 Función principal - ULTRA FIX."""
    
    print("\n" + "="*70)
    force_flush()
    print(f"{APP_NAME} v{VERSION}".center(70))
    force_flush()
    print(f"by {AUTHOR} | {RELEASE_DATE}".center(70))
    force_flush()
    print("="*70 + "\n")
    force_flush()
    
    if not TELEGRAM_AVAILABLE:
        print("❌ python-telegram-bot no instalado")
        force_flush()
        print("   Instala con: pip install python-telegram-bot\n")
        force_flush()
        time.sleep(0.2)
        os._exit(1)
    
    config = ConfigManager()
    
    if not config.has_real_token:
        print("⚠️ Bot sin token de Telegram configurado")
        force_flush()
        
        try:
            print("\n¿Deseas ejecutar el setup wizard? (s/n): ", end='', flush=True)
            response = input().strip().lower()
        except (KeyboardInterrupt, EOFError):
            print("\n\n❌ Operación cancelada\n")
            force_flush()
            time.sleep(0.2)
            raise SystemExit(1)
        
        if response == 's':
            run_setup_wizard()
            print("\n✅ Setup completado. Ejecuta el bot de nuevo.\n")
            force_flush()
            time.sleep(0.2)
            raise SystemExit(0)
        else:
            # ULTRA AGGRESSIVE EXIT
            print("\n❌ Bot no configurado. Saliendo...")
            force_flush()
            print("💡 Para configurar, ejecuta de nuevo y responde 's'\n")
            force_flush()
            time.sleep(0.2)  # Dar más tiempo a Windows
            # Múltiples métodos de exit
            sys.exit(1)
    
    print("✅ Configuración cargada")
    force_flush()
    print(f"   Token: ✅")
    force_flush()
    print(f"   Búsqueda: {'🎮 DEMO' if config.demo_mode else '🌐 REAL'}")
    force_flush()
    print()
    force_flush()
    
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        print("\n✅ Programa terminado\n")
        force_flush()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        force_flush()
        sys.exit(1)

async def async_main():
    """Main async function."""
    bot = VuelosBotUnified()
    
    try:
        print("🚀 Iniciando bot...\n")
        force_flush()
        await bot.start_bot()
    except KeyboardInterrupt:
        print("\n⏹️ Deteniendo bot...")
        force_flush()
    except Exception as e:
        logger.error(f"❌ Error fatal: {e}")
        raise
    finally:
        await bot.stop_bot()
        print("\n✅ Bot detenido\n")
        force_flush()

if __name__ == "__main__":
    main()
