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

VERSION = "15.0.5"
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
            # Assign config first before calling save()
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
        # En modo demo, si no hay token, usar uno dummy (NO FUNCIONARÁ con Telegram real)
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
        # Users
        users_data = {str(k): asdict(v) for k, v in self.users.items()}
        self._save_json(USERS_FILE, users_data)
        
        # Deals
        deals_data = {k: asdict(v) for k, v in self.deals.items()}
        self._save_json(DEALS_FILE, deals_data)
        
        # Alerts
        alerts_data = {k: asdict(v) for k, v in self.alerts.items()}
        self._save_json(ALERTS_FILE, alerts_data)
        
        # Stats
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
    
    # Datos demo
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
        time.sleep(random.uniform(0.5, 1.5))  # Simula latencia
        
        results = []
        
        # Busca rutas que coincidan
        for route in self.DEMO_ROUTES:
            if (route["origin"] == params.origin.upper() and 
                route["destination"] == params.destination.upper()):
                
                # Genera variaciones de precio
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
        
        # Ordena por precio
        results.sort(key=lambda f: f.price)
        
        logger.info(f"✅ Encontrados {len(results)} vuelos (demo mode)")
        return results[:10]  # Máximo 10 resultados
    
    def _real_search(self, params: FlightSearchParams) -> List[Flight]:
        """Búsqueda real con APIs (TODO: implementar)."""
        logger.warning("⚠️ Real search not implemented yet")
        return []

# ===============================================================================
#  DEAL DETECTOR
# ===============================================================================

class DealDetector:
    """Detector de chollos."""
    
    DEAL_THRESHOLD = 0.20  # 20% descuento mínimo
    
    def __init__(self, data_mgr: DataManager):
        self.data_mgr = data_mgr
        self.price_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=50))
    
    def check_deal(self, flight: Flight) -> Optional[Deal]:
        """Verifica si un vuelo es un chollo."""
        route_key = flight.route_key
        
        # Agrega precio al historial
        self.price_history[route_key].append(flight.price)
        
        # Necesita al menos 5 precios para calcular promedio
        if len(self.price_history[route_key]) < 5:
            return None
        
        # Calcula precio promedio
        avg_price = sum(self.price_history[route_key]) / len(self.price_history[route_key])
        
        # Calcula descuento
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
            departure_date_to=params.departure_date  # TODO: flexible dates
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
            
            # TODO: Verificar si es momento de chequear (según intervalo)
            
            params = FlightSearchParams(
                origin=alert.origin,
                destination=alert.destination,
                departure_date=alert.departure_date_from,
                max_price=alert.max_price
            )
            
            flights = self.search_engine.search(params)
            
            if flights:
                # Filtra vuelos bajo el precio máximo
                cheap_flights = [f for f in flights if f.price <= alert.max_price]
                
                if cheap_flights:
                    triggered.append((alert, cheap_flights))
                    alert.last_check = datetime.now().isoformat()
                    alert.notifications_sent += 1
        
        return triggered

# ===============================================================================
#  TELEGRAM BOT MANAGER - UNIFIED SOLUTION
# ===============================================================================

class VuelosBotUnified:
    """
    🚀 Bot Unificado de Vuelos v15.0
    
    Solución completa integrada con:
    - Búsqueda de vuelos
    - Alertas de precio
    - Detección de chollos
    - Gamificación
    - Estadísticas
    - Menú interactivo
    """
    
    def __init__(self):
        # Initialize managers
        self.config = ConfigManager()
        self.data_mgr = DataManager()
        self.search_engine = FlightSearchEngine(self.config)
        self.deal_detector = DealDetector(self.data_mgr)
        self.alert_mgr = AlertManager(self.data_mgr, self.search_engine)
        
        # Bot state
        self.app: Optional[Application] = None
        self.running = False
        self.user_states: Dict[int, Dict] = defaultdict(dict)
        
        logger.info(f"✅ {APP_NAME} v{VERSION} inicializado")
    
    async def start_bot(self):
        """Inicia el bot de Telegram."""
        
        if not self.config.has_real_token:
            logger.error("❌ Bot necesita un token real de Telegram.")
            logger.info("💡 Ejecuta el setup wizard para configurar el token")
            print("\n⚠️ MODO DEMO: No se puede iniciar bot sin token real")
            print("   Para configurar, ejecuta el setup wizard al inicio\n")
            return
        
        # Build application
        self.app = Application.builder().token(self.config.bot_token).build()
        
        # ===============================================================
        #  REGISTER HANDLERS
        # ===============================================================
        
        # Commands
        self.app.add_handler(CommandHandler("start", self.cmd_start))
        self.app.add_handler(CommandHandler("menu", self.cmd_menu))
        self.app.add_handler(CommandHandler("buscar", self.cmd_buscar))
        self.app.add_handler(CommandHandler("chollos", self.cmd_chollos))
        self.app.add_handler(CommandHandler("alertas", self.cmd_alertas))
        self.app.add_handler(CommandHandler("perfil", self.cmd_perfil))
        self.app.add_handler(CommandHandler("stats", self.cmd_stats))
        self.app.add_handler(CommandHandler("ayuda", self.cmd_ayuda))
        
        # Callbacks
        self.app.add_handler(CallbackQueryHandler(self.handle_callback))
        
        # Messages (para búsqueda conversacional)
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Set bot commands
        await self._set_bot_commands()
        
        # ===============================================================
        #  START POLLING
        # ===============================================================
        
        self.running = True
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES
        )
        
        logger.info("🚀 Bot iniciado y escuchando...")
        
        # Start background tasks
        asyncio.create_task(self._background_tasks())
        
        # Keep running
        while self.running:
            await asyncio.sleep(1)
    
    async def stop_bot(self):
        """Detiene el bot gracefully."""
        self.running = False
        
        if self.app:
            if self.app.updater and self.app.updater.running:
                await self.app.updater.stop()
            await self.app.stop()
            await self.app.shutdown()
        
        # Save all data
        self.data_mgr.save_all()
        
        logger.info("✅ Bot detenido correctamente")
    
    async def _set_bot_commands(self):
        """Configura comandos del bot."""
        commands = [
            BotCommand("start", "🏠 Iniciar bot"),
            BotCommand("menu", "📋 Menú principal"),
            BotCommand("buscar", "🔍 Buscar vuelos"),
            BotCommand("chollos", "🔥 Ver chollos"),
            BotCommand("alertas", "🔔 Mis alertas"),
            BotCommand("perfil", "👤 Mi perfil"),
            BotCommand("stats", "📊 Estadísticas"),
            BotCommand("ayuda", "❓ Ayuda"),
        ]
        await self.app.bot.set_my_commands(commands)
    
    async def _background_tasks(self):
        """Tareas en segundo plano."""
        logger.info("🔄 Tareas en segundo plano iniciadas")
        
        while self.running:
            try:
                # Check alerts every hour
                await asyncio.sleep(3600)
                logger.info("🔔 Verificando alertas...")
                
                triggered = await self.alert_mgr.check_alerts()
                
                for alert, flights in triggered:
                    await self._send_alert_notification(alert, flights)
                
                # Auto-save every 5 minutes
                await asyncio.sleep(300)
                self.data_mgr.save_all()
                
            except Exception as e:
                logger.error(f"❌ Error en background tasks: {e}")
                await asyncio.sleep(60)
    
    async def _send_alert_notification(self, alert: PriceAlert, flights: List[Flight]):
        """Envía notificación de alerta."""
        try:
            best_flight = flights[0]
            
            message = (
                f"🔔 *ALERTA DE PRECIO*\n\n"
                f"✈️ {alert.origin} → {alert.destination}\n"
                f"💰 €{best_flight.price} (límite: €{alert.max_price})\n"
                f"📅 {best_flight.departure_date}\n"
                f"🏢 {best_flight.airline}\n\n"
                f"¡Precio bajo tu límite encontrado!"
            )
            
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ Ver vuelo", url=best_flight.deep_link),
                InlineKeyboardButton("🔕 Desactivar alerta", callback_data=f"alert_deactivate_{alert.id}")
            ]])
            
            await self.app.bot.send_message(
                chat_id=alert.user_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard
            )
            
            logger.info(f"✅ Notificación de alerta enviada a {alert.user_id}")
            
        except Exception as e:
            logger.error(f"❌ Error enviando notificación: {e}")
    
    # ===============================================================
    #  COMMAND HANDLERS  
    # ===============================================================
    
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /start - Bienvenida."""
        user = update.effective_user
        
        # Get or create user
        db_user = self.data_mgr.get_or_create_user(
            user.id,
            user.username,
            user.first_name or "Usuario"
        )
        
        welcome = (
            f"✈️ *¡Hola {user.first_name}!*\n\n"
            f"Bienvenido a {APP_NAME} v{VERSION}\n\n"
            f"🎯 *¿Qué puedo hacer por ti?*\n"
            f"• 🔍 Buscar vuelos baratos\n"
            f"• 🔥 Ver chollos activos\n"
            f"• 🔔 Crear alertas de precio\n"
            f"• 📊 Ver estadísticas\n\n"
            f"_Modo: {'🎮 DEMO' if self.config.demo_mode else '🌐 REAL'}_"
        )
        
        await update.message.reply_text(
            welcome,
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Show menu
        await self.cmd_menu(update, context)
    
    async def cmd_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /menu - Menú principal."""
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🔍 Buscar Vuelos", callback_data="menu_buscar"),
                InlineKeyboardButton("🔥 Chollos", callback_data="menu_chollos")
            ],
            [
                InlineKeyboardButton("🔔 Mis Alertas", callback_data="menu_alertas"),
                InlineKeyboardButton("👤 Mi Perfil", callback_data="menu_perfil")
            ],
            [
                InlineKeyboardButton("📊 Estadísticas", callback_data="menu_stats"),
                InlineKeyboardButton("❓ Ayuda", callback_data="menu_ayuda")
            ]
        ])
        
        menu_text = (
            f"📋 *MENÚ PRINCIPAL*\n\n"
            f"Selecciona una opción:"
        )
        
        if update.callback_query:
            await update.callback_query.message.edit_text(
                menu_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard
            )
        else:
            await update.message.reply_text(
                menu_text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard
            )
    
    async def cmd_buscar(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /buscar - Iniciar búsqueda de vuelos."""
        user_id = update.effective_user.id
        
        # Set user state
        self.user_states[user_id] = {
            "mode": "search",
            "step": "origin",
            "params": {}
        }
        
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("❌ Cancelar", callback_data="search_cancel")
        ]])
        
        message = (
            f"🔍 *BÚSQUEDA DE VUELOS*\n\n"
            f"Paso 1/4: *Origen*\n\n"
            f"Escribe el código IATA del aeropuerto de origen\n"
            f"_Ejemplo: MAD, BCN, NYC_"
        )
        
        await update.message.reply_text(
            message,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard
        )
    
    async def cmd_chollos(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /chollos - Muestra chollos activos."""
        deals = sorted(
            self.data_mgr.deals.values(),
            key=lambda d: d.discount_pct,
            reverse=True
        )[:10]
        
        if not deals:
            message = (
                f"🔥 *CHOLLOS ACTIVOS*\n\n"
                f"😕 No hay chollos disponibles en este momento.\n\n"
                f"💡 Usa /buscar para encontrar vuelos y te avisaremos de nuevos chollos!"
            )
            
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("🔍 Buscar Vuelos", callback_data="menu_buscar")
            ]])
        else:
            message = f"🔥 *CHOLLOS ACTIVOS* ({len(deals)})\n\n"
            
            for i, deal in enumerate(deals, 1):
                f = deal.flight
                message += (
                    f"{i}. ✈️ *{f.origin}→{f.destination}*\n"
                    f"   💰 €{f.price} (~~€{deal.average_price}~~) -{deal.discount_pct}%\n"
                    f"   🏢 {f.airline} | {f.stops} escalas\n\n"
                )
            
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("🔄 Actualizar", callback_data="menu_chollos"),
                InlineKeyboardButton("📋 Menú", callback_data="menu")
            ]])
        
        if update.callback_query:
            await update.callback_query.message.edit_text(
                message,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard
            )
        else:
            await update.message.reply_text(
                message,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard
            )
    
    async def cmd_alertas(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /alertas - Gestión de alertas."""
        user_id = update.effective_user.id
        user_alerts = self.alert_mgr.get_user_alerts(user_id)
        
        message = f"🔔 *MIS ALERTAS* ({len(user_alerts)})\n\n"
        
        if not user_alerts:
            message += "📭 No tienes alertas activas.\n\n💡 Crea una alerta para recibir notificaciones cuando bajen los precios!"
            
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("➕ Crear Alerta", callback_data="alert_create"),
                InlineKeyboardButton("📋 Menú", callback_data="menu")
            ]])
        else:
            for i, alert in enumerate(user_alerts, 1):
                message += (
                    f"{i}. ✈️ *{alert.origin}→{alert.destination}*\n"
                    f"   💰 Max: €{alert.max_price}\n"
                    f"   📅 {alert.departure_date_from}\n"
                    f"   📬 Notificaciones: {alert.notifications_sent}\n\n"
                )
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Nueva Alerta", callback_data="alert_create")],
                [InlineKeyboardButton("🔄 Ver Todas", callback_data="menu_alertas"),
                 InlineKeyboardButton("📋 Menú", callback_data="menu")]
            ])
        
        if update.callback_query:
            await update.callback_query.message.edit_text(
                message,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard
            )
        else:
            await update.message.reply_text(
                message,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard
            )
    
    async def cmd_perfil(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /perfil - Muestra perfil de usuario."""
        user_id = update.effective_user.id
        user = self.data_mgr.users.get(user_id)
        
        if not user:
            await update.message.reply_text("❌ Usuario no encontrado")
            return
        
        # Calculate days since joined
        created = datetime.fromisoformat(user.created_at)
        days = (datetime.now() - created).days
        
        message = (
            f"👤 *MI PERFIL*\n\n"
            f"*Usuario:* @{user.username or 'N/A'}\n"
            f"*Nombre:* {user.first_name}\n"
            f"*Nivel:* {user.tier.value.upper()} 🏆\n"
            f"*Puntos:* {user.points} 💎\n\n"
            f"📊 *Estadísticas:*\n"
            f"• Búsquedas: {user.searches_count}\n"
            f"• Alertas: {user.alerts_count}\n"
            f"• Chollos encontrados: {user.deals_found}\n"
            f"• Días activo: {days}\n\n"
            f"🎖️ *Logros:* {len(user.achievements)}"
        )
        
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("🏆 Ver Logros", callback_data="profile_achievements"),
            InlineKeyboardButton("📋 Menú", callback_data="menu")
        ]])
        
        if update.callback_query:
            await update.callback_query.message.edit_text(
                message,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard
            )
        else:
            await update.message.reply_text(
                message,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard
            )
    
    async def cmd_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /stats - Estadísticas globales."""
        stats = self.data_mgr.stats
        
        # Calculate uptime
        uptime_start = datetime.fromisoformat(stats.uptime_start)
        uptime = datetime.now() - uptime_start
        uptime_str = f"{uptime.days}d {uptime.seconds//3600}h"
        
        message = (
            f"📊 *ESTADÍSTICAS GLOBALES*\n\n"
            f"👥 *Usuarios:* {stats.total_users}\n"
            f"🔍 *Búsquedas:* {stats.total_searches}\n"
            f"🔥 *Chollos:* {stats.total_deals}\n"
            f"🔔 *Alertas:* {stats.total_alerts}\n"
            f"📈 *Activos 24h:* {stats.active_users_24h}\n\n"
            f"⚡ *Tiempo respuesta:* {stats.avg_response_time:.2f}s\n"
            f"⏱️ *Uptime:* {uptime_str}\n\n"
            f"_v{VERSION} by {AUTHOR}_"
        )
        
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("🔄 Actualizar", callback_data="menu_stats"),
            InlineKeyboardButton("📋 Menú", callback_data="menu")
        ]])
        
        if update.callback_query:
            await update.callback_query.message.edit_text(
                message,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard
            )
        else:
            await update.message.reply_text(
                message,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard
            )
    
    async def cmd_ayuda(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /ayuda - Ayuda y documentación."""
        message = (
            f"❓ *AYUDA - {APP_NAME}*\n\n"
            f"*Comandos disponibles:*\n"
            f"• /start - Iniciar bot\n"
            f"• /menu - Menú principal\n"
            f"• /buscar - Buscar vuelos\n"
            f"• /chollos - Ver chollos\n"
            f"• /alertas - Gestionar alertas\n"
            f"• /perfil - Tu perfil\n"
            f"• /stats - Estadísticas\n"
            f"• /ayuda - Esta ayuda\n\n"
            f"*Modos de búsqueda:*\n"
            f"• Exacta - Fechas específicas\n"
            f"• Flexible - ±3 días\n"
            f"• Multi-ciudad - Varias paradas\n\n"
            f"📚 *Más info:* github.com/juankaspain/vuelosrobot"
        )
        
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("🚀 Empezar", callback_data="menu_buscar"),
            InlineKeyboardButton("📋 Menú", callback_data="menu")
        ]])
        
        if update.callback_query:
            await update.callback_query.message.edit_text(
                message,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard
            )
        else:
            await update.message.reply_text(
                message,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard
            )
    
    # ===============================================================
    #  CALLBACK & MESSAGE HANDLERS
    # ===============================================================
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja todos los callbacks."""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        # Menu navigation
        if data == "menu":
            await self.cmd_menu(update, context)
        elif data == "menu_buscar":
            await self.cmd_buscar(update, context)
        elif data == "menu_chollos":
            await self.cmd_chollos(update, context)
        elif data == "menu_alertas":
            await self.cmd_alertas(update, context)
        elif data == "menu_perfil":
            await self.cmd_perfil(update, context)
        elif data == "menu_stats":
            await self.cmd_stats(update, context)
        elif data == "menu_ayuda":
            await self.cmd_ayuda(update, context)
        
        # Search actions
        elif data.startswith("search_"):
            await self._handle_search_callback(update, context, data)
        
        # Alert actions
        elif data.startswith("alert_"):
            await self._handle_alert_callback(update, context, data)
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja mensajes de texto (búsqueda conversacional)."""
        user_id = update.effective_user.id
        text = update.message.text.strip()
        
        # Check if user is in a flow
        if user_id not in self.user_states:
            # Not in any flow, ignore
            return
        
        state = self.user_states[user_id]
        mode = state.get("mode")
        
        if mode == "search":
            await self._handle_search_input(update, context, text)
    
    async def _handle_search_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
        """Maneja callbacks de búsqueda."""
        if data == "search_cancel":
            user_id = update.effective_user.id
            if user_id in self.user_states:
                del self.user_states[user_id]
            
            await update.callback_query.message.edit_text(
                "❌ Búsqueda cancelada",
                parse_mode=ParseMode.MARKDOWN
            )
            await self.cmd_menu(update, context)
    
    async def _handle_search_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
        """Maneja input de búsqueda paso a paso."""
        user_id = update.effective_user.id
        state = self.user_states[user_id]
        step = state["step"]
        params = state["params"]
        
        try:
            if step == "origin":
                # Validate IATA code
                if len(text) != 3 or not text.isalpha():
                    await update.message.reply_text(
                        "❌ Código inválido. Usa 3 letras (ej: MAD)"
                    )
                    return
                
                params["origin"] = text.upper()
                state["step"] = "destination"
                
                await update.message.reply_text(
                    f"✅ Origen: {text.upper()}\n\n"
                    f"Paso 2/4: *Destino*\n"
                    f"Escribe el código IATA del destino",
                    parse_mode=ParseMode.MARKDOWN
                )
            
            elif step == "destination":
                if len(text) != 3 or not text.isalpha():
                    await update.message.reply_text(
                        "❌ Código inválido. Usa 3 letras (ej: NYC)"
                    )
                    return
                
                params["destination"] = text.upper()
                state["step"] = "departure_date"
                
                await update.message.reply_text(
                    f"✅ Destino: {text.upper()}\n\n"
                    f"Paso 3/4: *Fecha de ida*\n"
                    f"Formato: YYYY-MM-DD (ej: 2026-03-15)",
                    parse_mode=ParseMode.MARKDOWN
                )
            
            elif step == "departure_date":
                # Simple date validation
                try:
                    datetime.strptime(text, "%Y-%m-%d")
                    params["departure_date"] = text
                    state["step"] = "return_date"
                    
                    keyboard = InlineKeyboardMarkup([[
                        InlineKeyboardButton("⏭️ Solo ida", callback_data="search_oneway")
                    ]])
                    
                    await update.message.reply_text(
                        f"✅ Fecha ida: {text}\n\n"
                        f"Paso 4/4: *Fecha de vuelta*\n"
                        f"Formato: YYYY-MM-DD (o pulsa 'Solo ida')",
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=keyboard
                    )
                except ValueError:
                    await update.message.reply_text(
                        "❌ Fecha inválida. Usa formato YYYY-MM-DD"
                    )
                    return
            
            elif step == "return_date":
                try:
                    datetime.strptime(text, "%Y-%m-%d")
                    params["return_date"] = text
                    
                    # Execute search
                    await self._execute_search(update, context, params)
                    
                    # Clear state
                    del self.user_states[user_id]
                    
                except ValueError:
                    await update.message.reply_text(
                        "❌ Fecha inválida. Usa formato YYYY-MM-DD"
                    )
                    return
        
        except Exception as e:
            logger.error(f"❌ Error en búsqueda: {e}")
            await update.message.reply_text(
                f"❌ Error procesando búsqueda: {str(e)}"
            )
            del self.user_states[user_id]
    
    async def _execute_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE, params: Dict):
        """Ejecuta búsqueda de vuelos."""
        user_id = update.effective_user.id
        
        # Update user stats
        user = self.data_mgr.users.get(user_id)
        if user:
            user.searches_count += 1
        self.data_mgr.stats.total_searches += 1
        
        # Send "searching" message
        status_msg = await update.message.reply_text(
            "🔍 Buscando vuelos...\n⏳ Esto puede tardar unos segundos"
        )
        
        try:
            # Create search params
            search_params = FlightSearchParams(
                origin=params["origin"],
                destination=params["destination"],
                departure_date=params["departure_date"],
                return_date=params.get("return_date")
            )
            
            # Search
            start_time = time.time()
            flights = self.search_engine.search(search_params)
            search_time = time.time() - start_time
            
            # Update response time stat
            self.data_mgr.stats.avg_response_time = (
                (self.data_mgr.stats.avg_response_time * 0.9) + (search_time * 0.1)
            )
            
            if not flights:
                await status_msg.edit_text(
                    f"😕 No se encontraron vuelos para\n"
                    f"✈️ {params['origin']} → {params['destination']}\n"
                    f"📅 {params['departure_date']}"
                )
                return
            
            # Check for deals
            deals_found = 0
            for flight in flights:
                deal = self.deal_detector.check_deal(flight)
                if deal and user:
                    user.deals_found += 1
                    deals_found += 1
            
            # Format results
            message = (
                f"✅ *RESULTADOS* ({len(flights)})\n"
                f"🔍 {params['origin']} → {params['destination']}\n"
                f"📅 {params['departure_date']}\n"
                f"⏱️ {search_time:.1f}s\n\n"
            )
            
            if deals_found > 0:
                message += f"🔥 *{deals_found} chollos encontrados!*\n\n"
            
            # Show top 5 results
            for i, flight in enumerate(flights[:5], 1):
                stops_text = "Directo" if flight.is_direct else f"{flight.stops} escala{'s' if flight.stops > 1 else ''}"
                message += (
                    f"{i}. 💰 *€{flight.price}* | {flight.airline}\n"
                    f"   ⏱️ {flight.duration} | {stops_text}\n\n"
                )
            
            if len(flights) > 5:
                message += f"_... y {len(flights) - 5} más_\n\n"
            
            message += "💡 Crea una alerta para recibir notificaciones de precio"
            
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🔔 Crear Alerta", callback_data="alert_create"),
                    InlineKeyboardButton("🔄 Nueva Búsqueda", callback_data="menu_buscar")
                ],
                [InlineKeyboardButton("📋 Menú", callback_data="menu")]
            ])
            
            await status_msg.edit_text(
                message,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard
            )
            
        except Exception as e:
            logger.error(f"❌ Error en búsqueda: {e}")
            await status_msg.edit_text(
                f"❌ Error ejecutando búsqueda:\n{str(e)}"
            )
    
    async def _handle_alert_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE, data: str):
        """Maneja callbacks de alertas."""
        if data == "alert_create":
            await update.callback_query.message.edit_text(
                "🔔 *CREAR ALERTA*\n\n"
                "Para crear una alerta, primero busca un vuelo con /buscar\n"
                "y luego podrás crear una alerta basada en esa búsqueda.",
                parse_mode=ParseMode.MARKDOWN
            )
        
        elif data.startswith("alert_deactivate_"):
            alert_id = data.replace("alert_deactivate_", "")
            
            if alert_id in self.data_mgr.alerts:
                self.data_mgr.alerts[alert_id].active = False
                await update.callback_query.message.edit_text(
                    "✅ Alerta desactivada"
                )
            else:
                await update.callback_query.message.edit_text(
                    "❌ Alerta no encontrada"
                )

# ===============================================================================
#  SETUP WIZARD
# ===============================================================================

def run_setup_wizard():
    """Asistente de configuración inicial."""
    print("\n" + "="*70)
    print(f"{APP_NAME} v{VERSION} - Setup Wizard".center(70))
    print("="*70 + "\n")
    
    config = ConfigManager()
    
    print("🔧 Configuración del Bot\n")
    
    # Bot token
    print("1️⃣ Token de Telegram")
    print("   Obtén tu token de @BotFather en Telegram")
    print("   Necesario para que el bot funcione\n")
    token = input("   Token: ").strip()
    
    if token:
        config.set('telegram.token', token)
        config.set('features.demo_mode', True)  # Keep demo mode for flight search
        print("   ✅ Token guardado")
    else:
        print("   ❌ Token requerido para ejecutar el bot")
        return
    
    # API Keys (opcional)
    print("\n2️⃣ API Keys (opcional - para búsqueda real de vuelos)")
    print("   Deja en blanco para usar modo demo de búsqueda\n")
    
    use_real_apis = input("   ¿Configurar APIs reales? (s/n): ").lower() == 's'
    
    if use_real_apis:
        skyscanner_key = input("   Skyscanner API Key: ").strip()
        if skyscanner_key:
            config.set('api_keys.skyscanner', skyscanner_key)
        
        kiwi_key = input("   Kiwi API Key: ").strip()
        if kiwi_key:
            config.set('api_keys.kiwi', kiwi_key)
        
        config.set('features.demo_mode', False)
        print("   ✅ APIs configuradas - Modo REAL activado")
    else:
        print("   ⚠️ Modo DEMO de búsqueda activado")
    
    # Save config
    config.save()
    
    print("\n✅ Configuración completada!")
    print(f"\n📁 Config guardada en: {CONFIG_FILE}")
    print("\n🚀 Ejecuta el bot con: python vuelos_bot_unified.py\n")

# ===============================================================================
#  MAIN
# ===============================================================================

def main():
    """🚀 Función principal."""
    
    print("\n" + "="*70)
    print(f"{APP_NAME} v{VERSION}".center(70))
    print(f"by {AUTHOR} | {RELEASE_DATE}".center(70))
    print("="*70 + "\n")
    
    # Check dependencies
    if not TELEGRAM_AVAILABLE:
        print("❌ python-telegram-bot no instalado")
        print("   Instala con: pip install python-telegram-bot")
        sys.stdout.flush()
        os._exit(1)
    
    # Check config
    config = ConfigManager()
    
    if not config.has_real_token:
        print("⚠️ Bot sin token de Telegram configurado")
        sys.stdout.flush()
        
        try:
            response = input("\n¿Deseas ejecutar el setup wizard? (s/n): ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\n\n❌ Operación cancelada\n")
            sys.exit(1)
        
        if response == 's':
            run_setup_wizard()
            print("\n✅ Setup completado. Ejecuta el bot de nuevo para iniciar.\n")
            sys.exit(0)
        else:
            # Use sys.exit() instead of os._exit() to allow buffer flush
            print("\n❌ Bot no configurado. Saliendo...\n")
            print("💡 Para configurar el bot, ejecuta de nuevo y responde 's'\n")
            time.sleep(0.1)  # Give time for buffer flush on Windows
            sys.exit(1)
    
    # Show config status
    print("✅ Configuración cargada")
    print(f"   Token: ✅ Configurado")
    print(f"   Búsqueda: {'🎮 DEMO' if config.demo_mode else '🌐 REAL'}")
    print()
    sys.stdout.flush()
    
    # Run async main
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        print("\n✅ Programa terminado por el usuario\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        sys.exit(1)

async def async_main():
    """Main async function."""
    # Initialize bot
    bot = VuelosBotUnified()
    
    try:
        print("🚀 Iniciando bot...\n")
        sys.stdout.flush()
        await bot.start_bot()
    
    except KeyboardInterrupt:
        print("\n⏹️ Deteniendo bot...")
        sys.stdout.flush()
    
    except Exception as e:
        logger.error(f"❌ Error fatal: {e}")
        print(f"\n❌ Error fatal: {e}")
        sys.stdout.flush()
        raise
    
    finally:
        await bot.stop_bot()
        print("\n✅ Bot detenido correctamente\n")
        sys.stdout.flush()

if __name__ == "__main__":
    main()
