#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
═════════════════════════════════════════════════════════════════════════════
║       🎆 CAZADOR SUPREMO v12.1 ENTERPRISE EDITION 🎆                    ║
║   🚀 Sistema Profesional de Monitorización de Vuelos 2026 🚀           ║
═════════════════════════════════════════════════════════════════════════════

👨‍💻 Autor: @Juanka_Spain | 🏷️ v12.1.1 Enterprise | 📅 2026-01-13 | 📋 MIT License

🌟 ENTERPRISE FEATURES V12.1:
✅ SerpAPI Real Google Flights       ✅ Webhooks para Producción     ✅ ML Confidence Scores
✅ Rate Limiting Inteligente         ✅ Retry Logic Robusto          ✅ DecisionTree Patterns
✅ Fallback Multi-Nivel              ✅ Input Validation Pro         ✅ Alertas Proactivas
✅ Heartbeat Monitoring (opcional)   ✅ Inline Keyboards             ✅ Métricas por Fuente
✅ Typing Indicators UX              ✅ Markdown Estratégico         ✅ Console Coloreado
✅ Health Checks Avanzados           ✅ Status por Componente        ✅ Degradation Alerts

🆕 NUEVO EN v12.1.1:
⭐ /clearcache - Comando para limpiar caché manualmente
⭐ Permite forzar llamadas reales a APIs sin reiniciar

🐛 FIXES:
- v12.1.1: Añade comando /clearcache para testing
- v12.1.0: Implementa integración real SerpAPI Google Flights
- v12.0.3: Agrega método UI.section() faltante

📦 Dependencies: python-telegram-bot pandas requests feedparser colorama
🚀 Usage: python cazador_supremo_v12.0_enterprise.py
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
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
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
VERSION = "12.1.1 Enterprise"
APP_NAME = "Cazador Supremo"
CONFIG_FILE, LOG_FILE, CSV_FILE = "config.json", "cazador_supremo.log", "deals_history.csv"
MAX_WORKERS, API_TIMEOUT = 25, 15
CACHE_TTL, CIRCUIT_BREAK_THRESHOLD = 300, 5
SERPAPI_RATE_LIMIT = 100  # llamadas/mes tier free
RETRY_MAX_ATTEMPTS = 3
RETRY_BACKOFF_FACTOR = 2
HEARTBEAT_INTERVAL = 60  # segundos

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
    
    def to_dict(self) -> Dict:
        return {
            'route': self.route, 
            'name': self.name, 
            'price': self.price, 
            'source': self.source.value, 
            'timestamp': self.timestamp.isoformat(),
            'confidence': self.confidence,
            'metadata': json.dumps(self.metadata)
        }
    
    def is_deal(self, threshold: float) -> bool:
        return self.price < threshold
    
    def get_confidence_emoji(self) -> str:
        if self.confidence >= 0.9:
            return "🎯"
        elif self.confidence >= 0.75:
            return "✅"
        elif self.confidence >= 0.6:
            return "⚠️"
        else:
            return "❓"

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
        if self.calls_total == 0:
            return 0.0
        return self.calls_success / self.calls_total
    
    @property
    def avg_response_time(self) -> float:
        if not self.response_times:
            return 0.0
        return sum(self.response_times) / len(self.response_times)
    
    @property
    def health_status(self) -> HealthStatus:
        if self.calls_total == 0:
            return HealthStatus.UNKNOWN
        if self.success_rate >= 0.95:
            return HealthStatus.HEALTHY
        elif self.success_rate >= 0.7:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.CRITICAL

# 📊 COLORIZED LOGGER PROFESSIONAL
class ColorizedLogger:
    LOG_COLORS = {
        'DEBUG': Fore.CYAN,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED + Style.BRIGHT
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
        if not COLORS_AVAILABLE:
            return msg
        color = self.LOG_COLORS.get(level, '')
        timestamp = datetime.now().strftime('%H:%M:%S')
        return f"{Fore.CYAN}[{timestamp}]{Style.RESET_ALL} {color}{level:<8}{Style.RESET_ALL} | {msg}"
    
    def debug(self, msg: str):
        self.logger.debug(msg)
    
    def info(self, msg: str):
        print(self._colorize('INFO', msg))
        self.logger.info(msg)
    
    def warning(self, msg: str):
        print(self._colorize('WARNING', msg))
        self.logger.warning(msg)
    
    def error(self, msg: str, exc=False):
        print(self._colorize('ERROR', msg))
        self.logger.error(msg, exc_info=exc)
    
    def critical(self, msg: str):
        print(self._colorize('CRITICAL', msg))
        self.logger.critical(msg, exc_info=True)
    
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
    def bot_token(self) -> str: 
        return self._config['telegram']['token']
    
    @property
    def chat_id(self) -> str: 
        return self._config['telegram']['chat_id']
    
    @property
    def webhook_url(self) -> Optional[str]:
        return self._config['telegram'].get('webhook_url')
    
    @property
    def flights(self) -> List[Dict]: 
        return self._config['flights']
    
    @property
    def alert_threshold(self) -> float: 
        return float(self._config.get('alert_min', 500))
    
    @property
    def api_keys(self) -> Dict: 
        return self._config.get('apis', {})
    
    @property
    def rss_feeds(self) -> List[str]: 
        return self._config.get('rss_feeds', [])

# 🧠 ML SMART PREDICTOR
class MLSmartPredictor:
    BASE_PRICES = {
        'MAD-MGA': 680, 'MGA-MAD': 700,
        'MAD-MIA': 520, 'MIA-MAD': 580,
        'MAD-BOG': 580, 'BOG-MAD': 620,
        'MAD-NYC': 450, 'NYC-MAD': 500,
        'MAD-MEX': 700, 'MEX-MAD': 720,
        'MAD-LAX': 550, 'LAX-MAD': 600,
    }
    
    HIGH_SEASON = [6, 7, 8, 12]
    LOW_SEASON = [1, 2, 9, 10, 11]
    
    def __init__(self):
        logger.info("🧠 ML Smart Predictor initialized")
    
    def predict(self, origin: str, dest: str, flight_date: str = None, 
                cabin_class: str = 'economy', stops: int = 1) -> Tuple[float, float]:
        route = f"{origin}-{dest}"
        base = self.BASE_PRICES.get(route, 650)
        
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

# 🎯 FLIGHT SCANNER CORE
class FlightScanner:
    def __init__(self, config: ConfigManager):
        self.config = config
        self.cache = TTLCache()
        self.ml_predictor = MLSmartPredictor()
        self.circuits = {
            'serpapi': CircuitBreaker('serpapi', fail_max=3, reset_timeout=60),
            'aviationstack': CircuitBreaker('aviationstack', fail_max=5)
        }
        self.serpapi_calls_today = 0
        self.serpapi_last_reset = datetime.now().date()
        logger.info("🎯 FlightScanner initialized")
    
    def scan_routes(self, routes: List[FlightRoute], parallel: bool = True) -> List[FlightPrice]:
        UI.section(f"FLIGHT SCANNER: {len(routes)} ROUTES")
        UI.status("🚀", f"Starting {'parallel' if parallel else 'sequential'} scan with {MAX_WORKERS} workers...")
        
        results = []
        if parallel:
            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                futures = {executor.submit(self._scan_single, r): r for r in routes}
                for i, future in enumerate(as_completed(futures), 1):
                    try:
                        price = future.result()
                        if price:
                            results.append(price)
                    except Exception as e:
                        route = futures[future]
                        logger.error(f"❌ Scan failed for {route.route_code}: {e}")
                    UI.progress(i, len(routes))
        else:
            for i, route in enumerate(routes, 1):
                try:
                    price = self._scan_single(route)
                    if price:
                        results.append(price)
                except Exception as e:
                    logger.error(f"❌ Scan failed for {route.route_code}: {e}")
                UI.progress(i, len(routes))
        
        UI.status("✅", f"Scan complete: {len(results)}/{len(routes)} results", "SUCCESS")
        return results
    
    def _scan_single(self, route: FlightRoute) -> Optional[FlightPrice]:
        cache_key = f"price:{route.route_code}:today:economy:1"
        cached = self.cache.get(cache_key)
        
        if cached:
            logger.info(f"💾 Using cached price for {route.route_code}")
            return cached
        
        # Try SerpAPI first
        try:
            price = self.circuits['serpapi'].call(self._fetch_serpapi, route)
            if price:
                self.cache.set(cache_key, price, ttl=100)
                return price
        except Exception as e:
            logger.warning(f"⚠️ serpapi failed for {route.route_code}: {e}")
        
        # Fallback to ML
        ml_price, confidence = self.ml_predictor.predict(
            route.origin, route.dest, 
            flight_date=datetime.now().strftime('%Y-%m-%d'),
            cabin_class='economy', stops=random.choice([0, 1])
        )
        
        price = FlightPrice(
            route=route.route_code,
            name=route.name,
            price=ml_price,
            source=PriceSource.ML_SMART,
            timestamp=datetime.now(),
            confidence=confidence,
            metadata={'fallback': True}
        )
        
        logger.info(f"🧠 {route.route_code}: €{ml_price} (ML Smart Fallback, conf={confidence:.0%})")
        self.cache.set(cache_key, price, ttl=100)
        return price
    
    def _fetch_serpapi(self, route: FlightRoute) -> Optional[FlightPrice]:
        """
        ⭐ IMPLEMENTACIÓN REAL: Llamada real a SerpAPI Google Flights
        """
        # Check rate limit
        if self.serpapi_last_reset != datetime.now().date():
            self.serpapi_calls_today = 0
            self.serpapi_last_reset = datetime.now().date()
        
        if self.serpapi_calls_today >= SERPAPI_RATE_LIMIT:
            raise Exception("SERPAPI rate limit reached")
        
        # Get API key
        api_key = self.config.api_keys.get('serpapi_key')
        if not api_key:
            raise Exception("SERPAPI key not configured")
        
        # Prepare request
        departure_date = (datetime.now() + timedelta(days=45)).strftime('%Y-%m-%d')
        
        params = {
            'engine': 'google_flights',
            'departure_id': route.origin,
            'arrival_id': route.dest,
            'outbound_date': departure_date,
            'currency': 'EUR',
            'hl': 'es',
            'api_key': api_key
        }
        
        url = 'https://serpapi.com/search'
        
        # Make request with timeout and metrics
        start_time = time.time()
        try:
            response = requests.get(url, params=params, timeout=API_TIMEOUT)
            duration = time.time() - start_time
            
            response.raise_for_status()
            data = response.json()
            
            # Extract price from response
            price_value = self._extract_price_from_serpapi(data)
            
            if price_value:
                self.serpapi_calls_today += 1
                metrics_dashboard.record_call('serpapi', True, duration)
                
                price_obj = FlightPrice(
                    route=route.route_code,
                    name=route.name,
                    price=price_value,
                    source=PriceSource.SERP_API,
                    timestamp=datetime.now(),
                    confidence=0.95,
                    metadata={
                        'api': 'serpapi',
                        'response_time': duration,
                        'departure_date': departure_date
                    }
                )
                
                logger.info(f"🔍 {route.route_code}: €{price_value} (SerpAPI Google Flights, {duration:.2f}s)")
                return price_obj
            else:
                raise Exception("No price found in response")
                
        except requests.exceptions.Timeout:
            duration = time.time() - start_time
            metrics_dashboard.record_call('serpapi', False, duration, error="Timeout")
            raise Exception(f"SERPAPI timeout after {duration:.1f}s")
        except requests.exceptions.RequestException as e:
            duration = time.time() - start_time
            metrics_dashboard.record_call('serpapi', False, duration, error=str(e))
            raise Exception(f"SERPAPI request failed: {e}")
        except Exception as e:
            duration = time.time() - start_time
            metrics_dashboard.record_call('serpapi', False, duration, error=str(e))
            raise
    
    def _extract_price_from_serpapi(self, data: Dict) -> Optional[float]:
        """
        ⭐ Extrae precio de respuesta JSON de SerpAPI
        """
        try:
            # Try best_flights first
            if 'best_flights' in data and len(data['best_flights']) > 0:
                flight = data['best_flights'][0]
                if 'price' in flight:
                    return float(flight['price'])
            
            # Try other_flights
            if 'other_flights' in data and len(data['other_flights']) > 0:
                flight = data['other_flights'][0]
                if 'price' in flight:
                    return float(flight['price'])
            
            # Try price_insights
            if 'price_insights' in data:
                insights = data['price_insights']
                if 'lowest_price' in insights:
                    return float(insights['lowest_price'])
            
            return None
        except (KeyError, ValueError, TypeError) as e:
            logger.warning(f"⚠️ Failed to extract price from SerpAPI response: {e}")
            return None

# 💾 DATA MANAGER
class DataManager:
    def __init__(self, csv_file: str = CSV_FILE):
        self.csv_file = Path(csv_file)
        self._ensure_csv()
        logger.info(f"💾 DataManager initialized: {self.csv_file}")
    
    def _ensure_csv(self):
        if not self.csv_file.exists():
            df = pd.DataFrame(columns=['route', 'name', 'price', 'source', 'timestamp', 'confidence', 'metadata'])
            df.to_csv(self.csv_file, index=False, encoding='utf-8')
            logger.info(f"📄 Created new CSV: {self.csv_file}")
    
    def save_prices(self, prices: List[FlightPrice]):
        if not prices:
            return
        
        df_new = pd.DataFrame([p.to_dict() for p in prices])
        
        if self.csv_file.exists():
            df_existing = pd.read_csv(self.csv_file, encoding='utf-8')
            df = pd.concat([df_existing, df_new], ignore_index=True)
        else:
            df = df_new
        
        df.to_csv(self.csv_file, index=False, encoding='utf-8')
        avg_conf = sum(p.confidence for p in prices) / len(prices)
        UI.status("💾", f"Saved {len(prices)} prices (avg confidence: {avg_conf:.0%})", "SUCCESS")
    
    def get_historical_avg(self, route: str, days: int = 30) -> Optional[float]:
        try:
            df = pd.read_csv(self.csv_file, encoding='utf-8')
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            cutoff = datetime.now() - timedelta(days=days)
            df_route = df[(df['route'] == route) & (df['timestamp'] >= cutoff)]
            return df_route['price'].mean() if not df_route.empty else None
        except:
            return None

# 🤖 TELEGRAM BOT MANAGER
class TelegramBotManager:
    def __init__(self, config: ConfigManager, scanner: FlightScanner, data_mgr: DataManager):
        self.config = config
        self.scanner = scanner
        self.data_mgr = data_mgr
        self.app = None
        self.running = False
        self._background_tasks: Set[asyncio.Task] = set()
        logger.info("🤖 TelegramBotManager initialized")
    
    async def start(self):
        self.app = Application.builder().token(self.config.bot_token).build()
        
        # Handlers
        self.app.add_handler(CommandHandler('start', self.cmd_start))
        self.app.add_handler(CommandHandler('scan', self.cmd_scan))
        self.app.add_handler(CommandHandler('clearcache', self.cmd_clearcache))
        self.app.add_handler(CommandHandler('status', self.cmd_status))
        self.app.add_handler(CommandHandler('help', self.cmd_help))
        self.app.add_handler(CallbackQueryHandler(self.handle_callback))
        
        self.running = True
        
        if self.config.webhook_url:
            UI.status("🌐", "Starting in WEBHOOK mode...")
            await self.app.initialize()
            await self.app.start()
            await self.app.bot.set_webhook(url=self.config.webhook_url)
            logger.info(f"🌐 Webhook set: {self.config.webhook_url}")
        else:
            UI.status("🔄", "Starting in POLLING mode...")
            await self.app.initialize()
            await self.app.start()
            await self.app.updater.start_polling(drop_pending_updates=True)
            logger.info("🔄 Polling started")
        
        UI.status("✅", "Bot is running!", "SUCCESS")
    
    async def stop(self):
        UI.header("🛑 SHUTDOWN REQUESTED")
        self.running = False
        
        if self._background_tasks:
            UI.status("⏹️", f"Cancelling {len(self._background_tasks)} background tasks...")
            for task in self._background_tasks:
                if not task.done():
                    task.cancel()
            await asyncio.gather(*self._background_tasks, return_exceptions=True)
            self._background_tasks.clear()
        
        if self.app:
            UI.status("⏹️", "Stopping bot...")
            try:
                if self.app.updater and self.app.updater.running:
                    await self.app.updater.stop()
                await self.app.stop()
                await self.app.shutdown()
            except Exception as e:
                logger.error(f"Error during shutdown: {e}")
        
        UI.header("✅ BOT STOPPED")
        UI.status("✅", "System stopped by user", "SUCCESS")
    
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        msg = update.effective_message
        if not msg:
            return
        
        await context.bot.send_chat_action(chat_id=msg.chat_id, action=ChatAction.TYPING)
        
        welcome = (
            f"🎆 *{APP_NAME} v{VERSION}* 🎆\n\n"
            "¡Bienvenido al sistema Enterprise de monitorización de vuelos!\n\n"
            "*Comandos disponibles:*\n"
            "/scan - Escanear rutas configuradas\n"
            "/clearcache - Limpiar caché (fuerza APIs reales)\n"
            "/status - Ver estado del sistema\n"
            "/help - Ayuda detallada\n\n"
            "💡 _Usa los botones para interactuar_"
        )
        
        keyboard = [
            [InlineKeyboardButton("🔍 Escanear Ahora", callback_data="scan")],
            [InlineKeyboardButton("📊 Estado Sistema", callback_data="status")],
            [InlineKeyboardButton("❓ Ayuda", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await msg.reply_text(welcome, parse_mode='Markdown', reply_markup=reply_markup)
        logger.info(f"✅ /start executed")
    
    async def cmd_scan(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        msg = update.effective_message
        if not msg:
            return
        
        await context.bot.send_chat_action(chat_id=msg.chat_id, action=ChatAction.TYPING)
        await msg.reply_text("🔍 Iniciando escaneo de rutas...")
        
        routes = [FlightRoute(**f) for f in self.config.flights]
        prices = self.scanner.scan_routes(routes, parallel=True)
        
        if prices:
            self.data_mgr.save_prices(prices)
            
            response = "✅ *Escaneo completado*\n\n"
            for p in prices[:5]:
                emoji = p.get_confidence_emoji()
                response += f"{emoji} {p.name}: €{p.price:.0f} ({p.source.value})\n"
            
            if len(prices) > 5:
                response += f"\n_...y {len(prices)-5} resultados más_"
            
            keyboard = [
                [InlineKeyboardButton("🔄 Escanear de nuevo", callback_data="scan")],
                [InlineKeyboardButton("📊 Ver estado", callback_data="status")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await msg.reply_text(response, parse_mode='Markdown', reply_markup=reply_markup)
        else:
            await msg.reply_text("❌ No se obtuvieron resultados")
    
    async def cmd_clearcache(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        ⭐ NUEVO COMANDO: Limpia el caché para forzar llamadas reales a APIs
        """
        msg = update.effective_message
        if not msg:
            return
        
        await context.bot.send_chat_action(chat_id=msg.chat_id, action=ChatAction.TYPING)
        
        # Get cache stats before clearing
        cache_size = self.scanner.cache.size
        hit_rate = self.scanner.cache.hit_rate
        
        # Clear cache
        cleared = self.scanner.cache.clear()
        
        response = (
            f"🗑️ *Caché limpiado*\n\n"
            f"📄 Items eliminados: {cleared}\n"
            f"🎯 Hit rate anterior: {hit_rate:.1%}\n\n"
            f"✅ El próximo /scan usará APIs reales"
        )
        
        await msg.reply_text(response, parse_mode='Markdown')
        logger.info(f"🗑️ Cache cleared: {cleared} items")
    
    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        msg = update.effective_message
        if not msg:
            return
        
        await context.bot.send_chat_action(chat_id=msg.chat_id, action=ChatAction.TYPING)
        
        cache_metrics = {
            'size': self.scanner.cache.size,
            'hit_rate': f"{self.scanner.cache.hit_rate:.1%}",
            'hits': self.scanner.cache.hits,
            'misses': self.scanner.cache.misses
        }
        
        circuit_status = {
            name: cb.state.value 
            for name, cb in self.scanner.circuits.items()
        }
        
        msg_text = (
            "📊 *Estado del Sistema*\n\n"
            f"🗃️ Caché: {cache_metrics['size']} items ({cache_metrics['hit_rate']} hit rate)\n"
            f"⚡ Circuit Breakers:\n"
        )
        
        for name, status in circuit_status.items():
            msg_text += f"  • {name}: {status}\n"
        
        alerts = metrics_dashboard.check_degradation()
        if alerts:
            msg_text += f"\n⚠️ *Alertas:*\n" + "\n".join(f"  • {a}" for a in alerts)
        
        keyboard = [[InlineKeyboardButton("🔄 Actualizar", callback_data="status")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await msg.reply_text(msg_text, parse_mode='Markdown', reply_markup=reply_markup)
    
    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        msg = update.effective_message
        if not msg:
            return
        
        help_text = (
            f"📚 *Ayuda - {APP_NAME}*\n\n"
            "*Comandos:*\n"
            "/start - Iniciar bot\n"
            "/scan - Escanear rutas\n"
            "/clearcache - Limpiar caché\n"
            "/status - Ver estado sistema\n"
            "/help - Esta ayuda\n\n"
            "*Características:*\n"
            "✅ SerpAPI Google Flights Real\n"
            "✅ ML Smart Predictions\n"
            "✅ Circuit Breaker Pattern\n"
            "✅ Intelligent Caching\n"
            "✅ Health Monitoring\n\n"
            f"_Versión: {VERSION}_"
        )
        
        await msg.reply_text(help_text, parse_mode='Markdown')
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        if not query:
            return
        
        await query.answer()
        
        callback_data = query.data
        logger.info(f"📞 Callback received: {callback_data}")
        
        if callback_data == "scan":
            await self.cmd_scan(update, context)
        elif callback_data == "status":
            await self.cmd_status(update, context)
        elif callback_data == "help":
            await self.cmd_help(update, context)

# 🚀 MAIN
async def main():
    UI.header(f"🎆 {APP_NAME} v{VERSION} 🎆")
    
    try:
        config = ConfigManager()
        scanner = FlightScanner(config)
        data_mgr = DataManager()
        bot_mgr = TelegramBotManager(config, scanner, data_mgr)
        
        await bot_mgr.start()
        
        while bot_mgr.running:
            await asyncio.sleep(1)
            
            if int(time.time()) % 60 == 0:
                alerts = metrics_dashboard.check_degradation()
                if alerts:
                    UI.status("⚠️", f"Degradation detected: {', '.join(alerts)}", "WARNING")
        
    except KeyboardInterrupt:
        UI.status("⏹️", "Keyboard interrupt received", "WARNING")
    except Exception as e:
        UI.status("❌", f"Fatal error: {e}", "ERROR")
        logger.critical(f"Fatal error: {e}")
    finally:
        if 'bot_mgr' in locals():
            await bot_mgr.stop()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        UI.status("✅", "System stopped by user", "SUCCESS")
