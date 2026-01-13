#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
═════════════════════════════════════════════════════════════════════════════
║       🎆 CAZADOR SUPREMO v12.2 ENTERPRISE EDITION 🎆                    ║
║   🚀 Sistema Profesional de Monitorización de Vuelos 2026 🚀           ║
═════════════════════════════════════════════════════════════════════════════

👨‍💻 Autor: @Juanka_Spain | 🏷️ v12.2.0 Enterprise | 📅 2026-01-14 | 📋 MIT License

🌟 ENTERPRISE FEATURES V12.2 - ITERACIÓN 1/3:
✅ Búsqueda Personalizada /route     ✅ Sistema de Deals Automático    ✅ Análisis de Tendencias
✅ Notificaciones Inteligentes       ✅ Búsqueda Flexible ±3 días      ✅ Info de Aerolíneas
✅ Scheduler de Escaneos            ✅ Multi-Currency (EUR/USD/GBP)   ✅ ML Mejorado
✅ Formato Mensajes Avanzado        ✅ Alertas Proactivas             ✅ Historical Analytics

🆕 NUEVO EN v12.2.0:
⭐ /route - Búsqueda personalizada por origen, destino y fecha
⭐ /deals - Sistema inteligente de detección de chollos
⭐ /trends - Análisis de tendencias de precios históricos
⭐ Notificaciones automáticas cuando detecta precios bajos
⭐ Búsqueda flexible de fechas con ventana de ±3 días
⭐ Extracción detallada de info de vuelos (aerolíneas, escalas)
⭐ Scheduler para escaneos automáticos programables
⭐ Soporte multi-moneda (EUR, USD, GBP)
⭐ Algoritmo ML mejorado con 50+ rutas base

📦 Dependencies: python-telegram-bot pandas requests feedparser colorama matplotlib
🚀 Usage: python cazador_supremo_enterprise.py
⚙️ Config: Edit config.json with your tokens
"""

import asyncio, requests, pandas as pd, feedparser, json, random, os, sys, re, time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict, deque
from functools import wraps
import logging
from logging.handlers import RotatingFileHandler
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from telegram.error import TelegramError, RetryAfter, TimedOut, NetworkError
from telegram.constants import ChatAction

# Colorized console output
try:
    from colorama import init, Fore, Back, Style
    init(autoreset=True)
    COLORS_AVAILABLE = True
except ImportError:
    COLORS_AVAILABLE = False
    class Fore: RED = YELLOW = GREEN = CYAN = WHITE = MAGENTA = BLUE = ''
    class Style: BRIGHT = RESET_ALL = ''

# UTF-8 setup for Windows
if sys.platform == 'win32':
    try:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
        os.system('chcp 65001 > nul 2>&1')
    except: pass

# 🌐 GLOBAL CONFIG
VERSION = "12.2.0 Enterprise"
APP_NAME = "Cazador Supremo"
CONFIG_FILE, LOG_FILE, CSV_FILE = "config.json", "cazador_supremo.log", "deals_history.csv"
MAX_WORKERS, API_TIMEOUT = 25, 15
CACHE_TTL, CIRCUIT_BREAK_THRESHOLD = 300, 5
SERPAPI_RATE_LIMIT = 100
RETRY_MAX_ATTEMPTS = 3
RETRY_BACKOFF_FACTOR = 2
HEARTBEAT_INTERVAL = 60
AUTO_SCAN_INTERVAL = 3600  # 1 hora
DEAL_NOTIFICATION_COOLDOWN = 1800  # 30 minutos entre notificaciones del mismo deal

# Currency symbols
CURRENCY_SYMBOLS = {'EUR': '€', 'USD': '$', 'GBP': '£'}
CURRENCY_RATES = {'EUR': 1.0, 'USD': 1.09, 'GBP': 0.86}  # Tasas desde EUR

# 📦 ENUMS
class PriceSource(Enum):
    AVIATION_STACK = "AviationStack ✈️"
    SERP_API = "GoogleFlights 🔍"
    ML_SMART = "ML-Smart 🧠"
    FALLBACK = "Fallback 🔄"

class CircuitState(Enum):
    CLOSED, HALF_OPEN, OPEN = "🟢 Closed", "🟡 Half-Open", "🔴 Open"

class HealthStatus(Enum):
    HEALTHY = "✅ Healthy"
    DEGRADED = "⚠️ Degraded"
    CRITICAL = "🔴 Critical"
    UNKNOWN = "❓ Unknown"

# 📄 DATA CLASSES
@dataclass
class FlightRoute:
    origin: str
    dest: str
    name: str
    
    def __post_init__(self):
        self.origin, self.dest = self.origin.upper().strip(), self.dest.upper().strip()
        if not (re.match(r'^[A-Z]{3}$', self.origin) and re.match(r'^[A-Z]{3}$', self.dest)):
            raise ValueError(f"🚫 Código IATA inválido: {self.origin}/{self.dest}")
    
    @property
    def route_code(self) -> str:
        return f"{self.origin}✈️{self.dest}"

@dataclass
class FlightPrice:
    route: str
    name: str
    price: float
    source: PriceSource
    timestamp: datetime
    confidence: float = 0.85
    metadata: Dict[str, Any] = field(default_factory=dict)
    departure_date: Optional[str] = None
    airline: Optional[str] = None
    stops: int = 0
    currency: str = 'EUR'
    
    def to_dict(self) -> Dict:
        return {
            'route': self.route, 
            'name': self.name, 
            'price': self.price, 
            'source': self.source.value, 
            'timestamp': self.timestamp.isoformat(),
            'confidence': self.confidence,
            'metadata': json.dumps(self.metadata),
            'departure_date': self.departure_date,
            'airline': self.airline,
            'stops': self.stops,
            'currency': self.currency
        }
    
    def is_deal(self, threshold: float) -> bool:
        return self.price < threshold
    
    def get_confidence_emoji(self) -> str:
        if self.confidence >= 0.9: return "🎯"
        elif self.confidence >= 0.75: return "✅"
        elif self.confidence >= 0.6: return "⚠️"
        else: return "❓"
    
    def convert_currency(self, to_currency: str) -> float:
        """Convert price to different currency"""
        if self.currency == to_currency:
            return self.price
        # Convert to EUR first, then to target
        price_eur = self.price / CURRENCY_RATES[self.currency]
        return price_eur * CURRENCY_RATES[to_currency]
    
    def format_price(self, currency: str = None) -> str:
        """Format price with currency symbol"""
        target_currency = currency or self.currency
        price = self.convert_currency(target_currency)
        symbol = CURRENCY_SYMBOLS.get(target_currency, target_currency)
        return f"{symbol}{price:.0f}"

@dataclass
class Deal:
    """Represents a price deal/opportunity"""
    flight_price: FlightPrice
    savings_pct: float
    historical_avg: float
    detected_at: datetime
    notified: bool = False
    
    def get_message(self) -> str:
        """Format deal as Telegram message"""
        fp = self.flight_price
        msg = (
            f"🔥 *¡CHOLLO DETECTADO!* 🔥\n\n"
            f"✈️ *Ruta:* {fp.name}\n"
            f"💰 *Precio:* {fp.format_price()} ({fp.source.value})\n"
            f"📉 *Ahorro:* {self.savings_pct:.1f}% vs histórico\n"
            f"📊 *Media histórica:* €{self.historical_avg:.0f}\n"
        )
        if fp.departure_date:
            msg += f"📅 *Salida:* {fp.departure_date}\n"
        if fp.airline:
            msg += f"🛫 *Aerolínea:* {fp.airline}\n"
        msg += f"🔗 *Escalas:* {fp.stops}\n"
        msg += f"{fp.get_confidence_emoji()} *Confianza:* {fp.confidence:.0%}"
        return msg

@dataclass
class APIMetrics:
    name: str
    calls_total: int = 0
    calls_success: int = 0
    calls_failed: int = 0
    response_times: List[float] = field(default_factory=list)
    last_call: Optional[datetime] = None
    last_error: Optional[str] = None
    rate_limit_remaining: Optional[int] = None
    
    @property
    def success_rate(self) -> float:
        if self.calls_total == 0: return 0.0
        return self.calls_success / self.calls_total
    
    @property
    def avg_response_time(self) -> float:
        if not self.response_times: return 0.0
        return sum(self.response_times) / len(self.response_times)
    
    @property
    def health_status(self) -> HealthStatus:
        if self.calls_total == 0: return HealthStatus.UNKNOWN
        if self.success_rate >= 0.95: return HealthStatus.HEALTHY
        elif self.success_rate >= 0.7: return HealthStatus.DEGRADED
        else: return HealthStatus.CRITICAL

# 📊 COLORIZED LOGGER PROFESSIONAL
class ColorizedLogger:
    LOG_COLORS = {
        'DEBUG': Fore.CYAN, 'INFO': Fore.GREEN, 'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED, 'CRITICAL': Fore.RED + Style.BRIGHT
    }
    
    def __init__(self, name: str, file: str, max_bytes: int = 10*1024*1024, backups: int = 5):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        if not self.logger.handlers:
            fh = RotatingFileHandler(file, maxBytes=max_bytes, backupCount=backups, encoding='utf-8')
            fh.setFormatter(logging.Formatter(
                '📅%(asctime)s | %(levelname)-8s | %(funcName)s:%(lineno)d | %(message)s',
                '%Y-%m-%d %H:%M:%S'
            ))
            self.logger.addHandler(fh)
            
            ch = logging.StreamHandler()
            ch.setFormatter(logging.Formatter('%(message)s'))
            self.logger.addHandler(ch)
    
    def _colorize(self, level: str, msg: str) -> str:
        if not COLORS_AVAILABLE: return msg
        color = self.LOG_COLORS.get(level, '')
        timestamp = datetime.now().strftime('%H:%M:%S')
        return f"{Fore.CYAN}[{timestamp}]{Style.RESET_ALL} {color}{level:<8}{Style.RESET_ALL} | {msg}"
    
    def debug(self, msg: str): self.logger.debug(msg)
    def info(self, msg: str): print(self._colorize('INFO', msg)); self.logger.info(msg)
    def warning(self, msg: str): print(self._colorize('WARNING', msg)); self.logger.warning(msg)
    def error(self, msg: str, exc=False): print(self._colorize('ERROR', msg)); self.logger.error(msg, exc_info=exc)
    def critical(self, msg: str): print(self._colorize('CRITICAL', msg)); self.logger.critical(msg, exc_info=True)
    def metric(self, api: str, metric: str, value: Any):
        msg = f"📊 {api} | {metric}: {value}"
        print(f"{Fore.MAGENTA}{msg}{Style.RESET_ALL}")
        self.logger.info(msg)

logger = ColorizedLogger(APP_NAME, LOG_FILE)

# 🔄 RETRY DECORATOR
def retry_with_backoff(max_attempts: int = RETRY_MAX_ATTEMPTS, 
                       backoff_factor: float = RETRY_BACKOFF_FACTOR,
                       exceptions: Tuple = (Exception,)):
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts:
                        logger.error(f"❌ {func.__name__} failed after {max_attempts} attempts: {e}")
                        raise
                    wait_time = backoff_factor ** attempt
                    logger.warning(f"⚠️ {func.__name__} attempt {attempt}/{max_attempts} failed, retry in {wait_time}s: {e}")
                    time.sleep(wait_time)
            return None
        return wrapper
    return decorator

# 🛡️ CIRCUIT BREAKER
class CircuitBreaker:
    def __init__(self, name: str, fail_max: int = CIRCUIT_BREAK_THRESHOLD, 
                 reset_timeout: int = 60, half_open_max_calls: int = 3):
        self.name = name
        self.fail_max = fail_max
        self.reset_timeout = reset_timeout
        self.half_open_max_calls = half_open_max_calls
        self.state = CircuitState.CLOSED
        self.fail_count = 0
        self.last_fail_time = None
        self.half_open_calls = 0
        logger.info(f"⚔️ CircuitBreaker '{name}' initialized")
    
    def call(self, func: callable, *args, **kwargs):
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_fail_time > self.reset_timeout:
                logger.info(f"🟡 {self.name}: OPEN → HALF_OPEN")
                self.state = CircuitState.HALF_OPEN
                self.half_open_calls = 0
            else:
                raise Exception(f"⛔ Circuit {self.name} is OPEN (cooling down {int(self.reset_timeout - (time.time() - self.last_fail_time))}s)")
        
        if self.state == CircuitState.HALF_OPEN:
            if self.half_open_calls >= self.half_open_max_calls:
                logger.info(f"🟢 {self.name}: HALF_OPEN → CLOSED")
                self.state = CircuitState.CLOSED
                self.fail_count = 0
        
        try:
            result = func(*args, **kwargs)
            if self.state == CircuitState.HALF_OPEN:
                self.half_open_calls += 1
            return result
        except Exception as e:
            self.fail_count += 1
            self.last_fail_time = time.time()
            logger.warning(f"⚠️ {self.name}: Failure #{self.fail_count}/{self.fail_max}")
            if self.fail_count >= self.fail_max:
                logger.error(f"🔴 {self.name}: → OPEN")
                self.state = CircuitState.OPEN
            raise

# 📦 TTL CACHE
class TTLCache:
    def __init__(self, default_ttl: int = CACHE_TTL):
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self.default_ttl = default_ttl
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        logger.info(f"🗃️ TTLCache initialized: ttl={default_ttl}s")
    
    def get(self, key: str) -> Optional[Any]:
        if key in self._cache:
            value, expiry = self._cache[key]
            if time.time() < expiry:
                self.hits += 1
                logger.debug(f"✅ Cache HIT: {key}")
                return value
            else:
                del self._cache[key]
                self.evictions += 1
        self.misses += 1
        return None
    
    def set(self, key: str, value: Any, ttl: int = None):
        ttl = ttl or self.default_ttl
        self._cache[key] = (value, time.time() + ttl)
        logger.debug(f"💾 Cache SET: {key}")
    
    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0
    
    @property
    def size(self) -> int:
        return len(self._cache)
    
    def clear(self):
        old_size = len(self._cache)
        self._cache.clear()
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        logger.info(f"🗑️ Cache cleared: {old_size} items removed")
        return old_size

# 📊 METRICS DASHBOARD
class MetricsDashboard:
    def __init__(self):
        self.apis: Dict[str, APIMetrics] = {}
        self.start_time = datetime.now()
        logger.info("📊 Metrics Dashboard initialized")
    
    def register_api(self, name: str) -> APIMetrics:
        if name not in self.apis:
            self.apis[name] = APIMetrics(name=name)
        return self.apis[name]
    
    def record_call(self, api_name: str, success: bool, duration: float, 
                   error: str = None, rate_limit_remaining: int = None):
        if api_name not in self.apis:
            self.register_api(api_name)
        
        metrics = self.apis[api_name]
        metrics.calls_total += 1
        metrics.last_call = datetime.now()
        
        if success:
            metrics.calls_success += 1
            metrics.response_times.append(duration)
            if len(metrics.response_times) > 100:
                metrics.response_times = metrics.response_times[-100:]
        else:
            metrics.calls_failed += 1
            metrics.last_error = error
        
        if rate_limit_remaining is not None:
            metrics.rate_limit_remaining = rate_limit_remaining
    
    def check_degradation(self) -> List[str]:
        alerts = []
        for name, metrics in self.apis.items():
            if metrics.health_status == HealthStatus.CRITICAL:
                alerts.append(f"🔴 {name}: CRITICAL ({metrics.success_rate:.0%} success)")
            elif metrics.health_status == HealthStatus.DEGRADED:
                alerts.append(f"⚠️ {name}: DEGRADED ({metrics.success_rate:.0%} success)")
        return alerts

metrics_dashboard = MetricsDashboard()

# 🏛️ CONSOLE UI
class UI:
    @staticmethod
    def print(text: str, color: str = '', flush: bool = True):
        try:
            print(f"{color}{text}{Style.RESET_ALL if COLORS_AVAILABLE else ''}", flush=flush)
        except UnicodeEncodeError:
            print(text.encode('ascii', 'ignore').decode('ascii'), flush=flush)
    
    @staticmethod
    def header(title: str):
        UI.print(f"\n{'='*80}", Fore.CYAN + Style.BRIGHT)
        UI.print(f"{title.center(80)}", Fore.CYAN + Style.BRIGHT)
        UI.print(f"{'='*80}\n", Fore.CYAN + Style.BRIGHT)
    
    @staticmethod
    def section(title: str):
        UI.print(f"\n{'─'*80}", Fore.CYAN)
        UI.print(f"📍 {title}", Fore.CYAN + Style.BRIGHT)
        UI.print(f"{'─'*80}\n", Fore.CYAN)
    
    @staticmethod
    def status(emoji: str, msg: str, typ: str = "INFO"):
        ts = datetime.now().strftime('%H:%M:%S')
        colors = {"INFO": Fore.CYAN, "SUCCESS": Fore.GREEN, "WARNING": Fore.YELLOW, "ERROR": Fore.RED}
        color = colors.get(typ, Fore.WHITE) if COLORS_AVAILABLE else ''
        UI.print(f"[{ts}] {emoji} {msg}", color)
    
    @staticmethod
    def progress(current: int, total: int, prefix: str = "⏳", width: int = 40):
        pct = (current / total) * 100
        filled = int(width * current / total)
        bar = '█' * filled + '░' * (width - filled)
        color = Fore.GREEN if pct == 100 else Fore.CYAN
        UI.print(f"\r{prefix} Progress [{bar}] {pct:.0f}% ({current}/{total})", color, flush=True)
        if current == total: print()

# ⚙️ CONFIG MANAGER
class ConfigManager:
    def __init__(self, file: str = CONFIG_FILE):
        self.file = Path(file)
        self._config = self._load()
        self._validate()
        logger.info(f"✅ Config loaded: {len(self.flights)} flights")
    
    def _load(self) -> Dict:
        if not self.file.exists():
            raise FileNotFoundError(f"❌ {self.file} not found")
        with open(self.file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _validate(self):
        required = ['telegram', 'flights']
        for field in required:
            if field not in self._config:
                raise ValueError(f"❌ Missing: {field}")
    
    @property
    def bot_token(self) -> str: return self._config['telegram']['token']
    
    @property
    def chat_id(self) -> str: return self._config['telegram']['chat_id']
    
    @property
    def webhook_url(self) -> Optional[str]: return self._config['telegram'].get('webhook_url')
    
    @property
    def flights(self) -> List[Dict]: return self._config['flights']
    
    @property
    def alert_threshold(self) -> float: return float(self._config.get('alert_min', 500))
    
    @property
    def api_keys(self) -> Dict: return self._config.get('apis', {})
    
    @property
    def rss_feeds(self) -> List[str]: return self._config.get('rss_feeds', [])
    
    @property
    def auto_scan_enabled(self) -> bool: return self._config.get('auto_scan', False)
    
    @property
    def deal_threshold_pct(self) -> float: return float(self._config.get('deal_threshold_pct', 20))

# 🧠 ML SMART PREDICTOR - ENHANCED
class MLSmartPredictor:
    # Expanded base prices for 50+ routes
    BASE_PRICES = {
        # España
        'MAD-BCN': 120, 'BCN-MAD': 115, 'MAD-AGP': 90, 'AGP-MAD': 95,
        'MAD-PMI': 85, 'PMI-MAD': 80, 'MAD-SVQ': 75, 'SVQ-MAD': 70,
        'MAD-VLC': 65, 'VLC-MAD': 60, 'MAD-BIO': 95, 'BIO-MAD': 90,
        # Europa
        'MAD-LHR': 180, 'LHR-MAD': 190, 'MAD-CDG': 150, 'CDG-MAD': 160,
        'MAD-FCO': 140, 'FCO-MAD': 145, 'MAD-AMS': 165, 'AMS-MAD': 170,
        'MAD-BER': 155, 'BER-MAD': 160, 'MAD-MUC': 175, 'MUC-MAD': 180,
        # América
        'MAD-JFK': 480, 'JFK-MAD': 520, 'MAD-MIA': 520, 'MIA-MAD': 580,
        'MAD-NYC': 450, 'NYC-MAD': 500, 'MAD-LAX': 550, 'LAX-MAD': 600,
        'MAD-EZE': 720, 'EZE-MAD': 780, 'MAD-BOG': 580, 'BOG-MAD': 620,
        'MAD-MEX': 700, 'MEX-MAD': 720, 'MAD-LIM': 650, 'LIM-MAD': 680,
        'MAD-SCL': 820, 'SCL-MAD': 850, 'MAD-GRU': 780, 'GRU-MAD': 800,
        # Centroamérica
        'MAD-MGA': 680, 'MGA-MAD': 700, 'MAD-PTY': 640, 'PTY-MAD': 660,
        'MAD-SJO': 670, 'SJO-MAD': 690, 'MAD-GUA': 650, 'GUA-MAD': 670,
        # Asia
        'MAD-TYO': 950, 'TYO-MAD': 980, 'MAD-BKK': 720, 'BKK-MAD': 750,
        'MAD-SIN': 850, 'SIN-MAD': 880, 'MAD-HKG': 820, 'HKG-MAD': 850,
        # Otros
        'MAD-DXB': 480, 'DXB-MAD': 500, 'MAD-IST': 350, 'IST-MAD': 370,
    }
    
    HIGH_SEASON = [6, 7, 8, 12]
    LOW_SEASON = [1, 2, 9, 10, 11]
    
    def __init__(self):
        logger.info(f"🧠 ML Smart Predictor initialized with {len(self.BASE_PRICES)} routes")
    
    def predict(self, origin: str, dest: str, flight_date: str = None, 
                cabin_class: str = 'economy', stops: int = 1) -> Tuple[float, float]:
        route = f"{origin}-{dest}"
        # Try direct route, reverse route, or default
        base = self.BASE_PRICES.get(route) or self.BASE_PRICES.get(f"{dest}-{origin}", 650)
        
        if flight_date:
            try:
                flight_dt = datetime.strptime(flight_date, '%Y-%m-%d')
                days_ahead = (flight_dt - datetime.now()).days
                month = flight_dt.month
            except:
                days_ahead, month = 45, datetime.now().month
        else:
            days_ahead = 45
            month = datetime.now().month
        
        advance_mult = self._get_anticipation_multiplier(days_ahead)
        season_mult = self._get_seasonal_multiplier(month)
        stops_mult = self._get_stops_multiplier(stops)
        cabin_mult = self._get_cabin_multiplier(cabin_class)
        
        noise = random.uniform(0.92, 1.08)
        final_price = base * advance_mult * season_mult * stops_mult * cabin_mult * noise
        confidence = self._calculate_confidence(days_ahead, stops)
        
        return max(100, int(final_price)), confidence
    
    def _get_anticipation_multiplier(self, days: int) -> float:
        if days < 0: return 2.5
        elif days < 7: return 1.7
        elif days < 30: return 1.15
        elif days <= 60: return 1.0
        elif days < 120: return 1.25
        else: return 1.35
    
    def _get_seasonal_multiplier(self, month: int) -> float:
        if month in self.HIGH_SEASON: return 1.35
        elif month in self.LOW_SEASON: return 0.85
        else: return 1.0
    
    def _get_stops_multiplier(self, stops: int) -> float:
        if stops == 0: return 1.35
        elif stops == 1: return 1.0
        else: return 0.82
    
    def _get_cabin_multiplier(self, cabin: str) -> float:
        multipliers = {'economy': 1.0, 'premium_economy': 1.75, 'business': 4.2, 'first': 6.5}
        return multipliers.get(cabin, 1.0)
    
    def _calculate_confidence(self, days: int, stops: int) -> float:
        confidence = 0.85
        if 45 <= days <= 60: confidence += 0.10
        elif days < 7: confidence -= 0.20
        if stops == 0: confidence += 0.05
        return max(0.3, min(0.99, confidence))

# Continuará en el siguiente mensaje debido al límite de longitud...
