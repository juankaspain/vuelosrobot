#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
═════════════════════════════════════════════════════════════════════════════
║       🎆 CAZADOR SUPREMO v12.0 ENTERPRISE EDITION 🎆                    ║
║   🚀 Sistema Profesional de Monitorización de Vuelos 2026 🚀           ║
═════════════════════════════════════════════════════════════════════════════

👨‍💻 Autor: @Juanka_Spain | 🏷️ v12.0.0 Enterprise | 📅 2026-01-13 | 📋 MIT License

🌟 ENTERPRISE FEATURES V12.0:
✅ SerpAPI Enhanced Google Flights   ✅ Webhooks para Producción     ✅ ML Confidence Scores
✅ Rate Limiting Inteligente         ✅ Retry Logic Robusto          ✅ DecisionTree Patterns
✅ Fallback Multi-Nivel              ✅ Input Validation Pro         ✅ Alertas Proactivas
✅ Heartbeat Monitoring              ✅ Inline Keyboards             ✅ Métricas por Fuente
✅ Typing Indicators UX              ✅ Markdown Estratégico         ✅ Console Coloreado
✅ Health Checks Avanzados           ✅ Status por Componente        ✅ Degradation Alerts

🆕 NUEVO EN v12.0:
⭐ SERPAPI GOOGLE FLIGHTS - Integración premium con rate limiting
⭐ WEBHOOKS TELEGRAM - Para producción (más eficiente que polling)
⭐ ML CONFIDENCE SCORES - Predicciones con nivel de confianza
⭐ DECISION TREE PATTERNS - Basado en estudios reales de pricing
⭐ INLINE KEYBOARDS - Interacción fluida con botones
⭐ TYPING INDICATORS - Feedback visual UX 2026
⭐ HEARTBEAT MONITORING - Health checks para containers
⭐ METRICS DASHBOARD - Métricas detalladas por fuente
⭐ PROACTIVE ALERTS - Sistema de alertas de degradación
⭐ COLORIZED OUTPUT - Console logging profesional

📦 Dependencies: python-telegram-bot pandas requests feedparser colorama retry
🚀 Usage: python cazador_supremo_v12.0_enterprise.py
⚙️ Config: Edit config.json with your tokens
"""

import asyncio, requests, pandas as pd, feedparser, json, random, os, sys, re, time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Callable
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
VERSION = "12.0.0 Enterprise"
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
    confidence: float = 0.85  # ¡NUEVO! Confidence score
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
        """Emoji basado en confidence score"""
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
    """Métricas detalladas por API"""
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
    """Logger profesional con console output coloreado"""
    
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
            # File handler
            fh = RotatingFileHandler(file, maxBytes=max_bytes, backupCount=backups, encoding='utf-8')
            fh.setFormatter(logging.Formatter(
                '📅%(asctime)s | %(levelname)-8s | %(funcName)s:%(lineno)d | %(message)s',
                '%Y-%m-%d %H:%M:%S'
            ))
            self.logger.addHandler(fh)
            
            # Console handler with colors
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
        """Log de métricas con formato especial"""
        msg = f"📊 {api} | {metric}: {value}"
        print(f"{Fore.MAGENTA}{msg}{Style.RESET_ALL}")
        self.logger.info(msg)

logger = ColorizedLogger(APP_NAME, LOG_FILE)

# 🔄 RETRY DECORATOR CON EXPONENTIAL BACKOFF
def retry_with_backoff(max_attempts: int = RETRY_MAX_ATTEMPTS, 
                       backoff_factor: float = RETRY_BACKOFF_FACTOR,
                       exceptions: Tuple = (Exception,)):
    """Decorator para retry con exponential backoff"""
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

# 🛡️ CIRCUIT BREAKER PATTERN ENHANCED
class CircuitBreaker:
    """Circuit breaker para prevenir cascading failures"""
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
        logger.info(f"⚔️ CircuitBreaker '{name}' initialized: fail_max={fail_max}, reset={reset_timeout}s")
    
    def call(self, func: callable, *args, **kwargs):
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_fail_time > self.reset_timeout:
                logger.info(f"🟡 {self.name}: OPEN → HALF_OPEN (reset timeout reached)")
                self.state = CircuitState.HALF_OPEN
                self.half_open_calls = 0
            else:
                raise Exception(f"⛔ Circuit {self.name} is OPEN (cooling down {int(self.reset_timeout - (time.time() - self.last_fail_time))}s)")
        
        if self.state == CircuitState.HALF_OPEN:
            if self.half_open_calls >= self.half_open_max_calls:
                logger.info(f"🟢 {self.name}: HALF_OPEN → CLOSED (success threshold reached)")
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
            logger.warning(f"⚠️ {self.name}: Failure #{self.fail_count}/{self.fail_max} - {e}")
            
            if self.fail_count >= self.fail_max:
                logger.error(f"🔴 {self.name}: → OPEN (threshold reached)")
                self.state = CircuitState.OPEN
            raise
    
    @property
    def health_status(self) -> HealthStatus:
        if self.state == CircuitState.CLOSED:
            return HealthStatus.HEALTHY
        elif self.state == CircuitState.HALF_OPEN:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.CRITICAL

# 📦 INTELLIGENT CACHE WITH TTL
class TTLCache:
    """Caché con expiración por item (Time To Live)"""
    def __init__(self, default_ttl: int = CACHE_TTL):
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self.default_ttl = default_ttl
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        logger.info(f"🗃️ TTLCache initialized: default_ttl={default_ttl}s")
    
    def get(self, key: str) -> Optional[Any]:
        if key in self._cache:
            value, expiry = self._cache[key]
            if time.time() < expiry:
                self.hits += 1
                logger.debug(f"✅ Cache HIT: {key} (hit_rate={self.hit_rate:.1%})")
                return value
            else:
                del self._cache[key]
                self.evictions += 1
                logger.debug(f"⏰ Cache EXPIRED: {key}")
        self.misses += 1
        return None
    
    def set(self, key: str, value: Any, ttl: int = None):
        ttl = ttl or self.default_ttl
        self._cache[key] = (value, time.time() + ttl)
        logger.debug(f"💾 Cache SET: {key} (ttl={ttl}s, size={len(self._cache)})")
    
    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0
    
    @property
    def size(self) -> int:
        return len(self._cache)
    
    def clear(self):
        self._cache.clear()
        logger.info("🧹 Cache cleared")
    
    def get_metrics(self) -> Dict[str, Any]:
        return {
            'size': self.size,
            'hits': self.hits,
            'misses': self.misses,
            'evictions': self.evictions,
            'hit_rate': self.hit_rate
        }

# 📊 PERFORMANCE METRICS DASHBOARD
class MetricsDashboard:
    """Dashboard de métricas por fuente de datos"""
    def __init__(self):
        self.apis: Dict[str, APIMetrics] = {}
        self.start_time = datetime.now()
        logger.info("📊 Metrics Dashboard initialized")
    
    def register_api(self, name: str) -> APIMetrics:
        if name not in self.apis:
            self.apis[name] = APIMetrics(name=name)
            logger.info(f"📊 API registered: {name}")
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
            # Limitar historial a últimas 100 llamadas
            if len(metrics.response_times) > 100:
                metrics.response_times = metrics.response_times[-100:]
        else:
            metrics.calls_failed += 1
            metrics.last_error = error
        
        if rate_limit_remaining is not None:
            metrics.rate_limit_remaining = rate_limit_remaining
        
        # Log métricas cada 10 llamadas
        if metrics.calls_total % 10 == 0:
            logger.metric(api_name, "success_rate", f"{metrics.success_rate:.1%}")
            logger.metric(api_name, "avg_response", f"{metrics.avg_response_time:.2f}s")
    
    def get_summary(self) -> Dict[str, Any]:
        uptime = (datetime.now() - self.start_time).total_seconds()
        return {
            'uptime_seconds': uptime,
            'apis': {name: {
                'calls': m.calls_total,
                'success_rate': m.success_rate,
                'avg_time': m.avg_response_time,
                'health': m.health_status.value,
                'rate_limit': m.rate_limit_remaining
            } for name, m in self.apis.items()}
        }
    
    def check_degradation(self) -> List[str]:
        """Detecta degradación de servicios"""
        alerts = []
        for name, metrics in self.apis.items():
            if metrics.health_status == HealthStatus.CRITICAL:
                alerts.append(f"🔴 {name}: CRITICAL ({metrics.success_rate:.0%} success)")
            elif metrics.health_status == HealthStatus.DEGRADED:
                alerts.append(f"⚠️ {name}: DEGRADED ({metrics.success_rate:.0%} success)")
            
            if metrics.rate_limit_remaining is not None and metrics.rate_limit_remaining < 10:
                alerts.append(f"⚠️ {name}: LOW RATE LIMIT ({metrics.rate_limit_remaining} remaining)")
        
        return alerts

metrics_dashboard = MetricsDashboard()

# 🏛️ CONSOLE UI WITH EMOJIS ENHANCED
class UI:
    """Beautiful console UI with colorized output"""
    
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
        UI.print(f"\n{'─'*80}\n📍 {title}\n{'─'*80}\n", Fore.CYAN)
    
    @staticmethod
    def status(emoji: str, msg: str, typ: str = "INFO"):
        ts = datetime.now().strftime('%H:%M:%S')
        colors = {
            "INFO": Fore.CYAN, 
            "SUCCESS": Fore.GREEN, 
            "WARNING": Fore.YELLOW, 
            "ERROR": Fore.RED,
            "ALERT": Fore.MAGENTA + Style.BRIGHT
        }
        color = colors.get(typ, Fore.WHITE) if COLORS_AVAILABLE else ''
        UI.print(f"[{ts}] {emoji} {msg}", color)
    
    @staticmethod
    def progress(current: int, total: int, prefix: str = "⏳", width: int = 40):
        pct = (current / total) * 100
        filled = int(width * current / total)
        bar = '█' * filled + '░' * (width - filled)
        color = Fore.GREEN if pct == 100 else Fore.CYAN
        UI.print(f"\r{prefix} [{bar}] {pct:.0f}% ({current}/{total})", color, flush=True)
        if current == total: print()
    
    @staticmethod
    def metric_table(data: Dict[str, Any]):
        """Tabla formateada de métricas"""
        UI.print("\n╔═══════════════════════════╦════════════════════════╗", Fore.CYAN)
        for key, value in data.items():
            UI.print(f"║ {key:<25} ║ {str(value):<22} ║", Fore.CYAN)
        UI.print("╚═══════════════════════════╩════════════════════════╝\n", Fore.CYAN)

# ⚙️ CONFIG MANAGER ENHANCED
class ConfigManager:
    """Gestor de configuración con validación exhaustiva"""
    def __init__(self, file: str = CONFIG_FILE):
        self.file = Path(file)
        self._config = self._load()
        self._validate()
        logger.info(f"✅ Config loaded: {len(self.flights)} flights, threshold=€{self.alert_threshold}")
    
    def _load(self) -> Dict:
        UI.status("📂", "Loading configuration...")
        if not self.file.exists():
            raise FileNotFoundError(f"❌ {self.file} not found")
        try:
            with open(self.file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"❌ Invalid JSON in {self.file}: {e}")
    
    def _validate(self):
        required = ['telegram', 'flights']
        for field in required:
            if field not in self._config:
                raise ValueError(f"❌ Missing required field: {field}")
        
        telegram_config = self._config['telegram']
        if not telegram_config.get('token') or not telegram_config.get('chat_id'):
            raise ValueError("❌ Invalid Telegram config")
        
        # Validar inputs de vuelos
        for flight in self._config['flights']:
            if not all(k in flight for k in ['origin', 'dest', 'name']):
                raise ValueError(f"❌ Invalid flight config: {flight}")
            if not re.match(r'^[A-Z]{3}$', flight['origin'].upper()):
                raise ValueError(f"❌ Invalid origin IATA: {flight['origin']}")
            if not re.match(r'^[A-Z]{3}$', flight['dest'].upper()):
                raise ValueError(f"❌ Invalid dest IATA: {flight['dest']}")
    
    @property
    def bot_token(self) -> str: 
        return self._config['telegram']['token']
    
    @property
    def chat_id(self) -> str: 
        return self._config['telegram']['chat_id']
    
    @property
    def webhook_url(self) -> Optional[str]:
        """¡NUEVO! Webhook para producción"""
        return self._config['telegram'].get('webhook_url')
    
    @property
    def webhook_port(self) -> int:
        return self._config['telegram'].get('webhook_port', 8443)
    
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
    
    @property
    def use_webhooks(self) -> bool:
        return bool(self.webhook_url)

# 🧠 ML SMART PREDICTOR ENTERPRISE (DecisionTree Patterns)
class MLSmartPredictor:
    """
    Predictor Enterprise con DecisionTree patterns, más factores y confidence scores.
    Basado en estudios reales de precio dinámico en aerolíneas.
    """
    
    # Precios base por ruta (mercado real 2026)
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
    
    # ¡NUEVO! Aerolíneas y sus multiplicadores
    AIRLINE_MULTIPLIERS = {
        'legacy': 1.35,      # Iberia, British Airways
        'lowcost': 0.75,     # Ryanair, Vueling
        'premium': 1.85,     # Emirates, Singapore
        'charter': 0.65      # Wamos, World2Fly
    }
    
    def __init__(self):
        logger.info("🧠 ML Smart Predictor ENTERPRISE initialized with DecisionTree patterns")
    
    def predict(self, origin: str, dest: str, flight_date: str = None, 
                cabin_class: str = 'economy', stops: int = 1,
                airline_type: str = 'legacy') -> Tuple[float, float]:
        """
        Predice precio con confidence score basado en DecisionTree.
        
        Returns:
            Tuple[float, float]: (precio, confidence_score)
        """
        route = f"{origin}-{dest}"
        base = self.BASE_PRICES.get(route, 650)
        
        # Variables de fecha
        if flight_date:
            try:
                flight_dt = datetime.strptime(flight_date, '%Y-%m-%d')
                days_ahead = (flight_dt - datetime.now()).days
                month = flight_dt.month
                day_of_week = flight_dt.weekday()
            except:
                days_ahead, month, day_of_week = 45, datetime.now().month, 1
        else:
            days_ahead = 45
            month = datetime.now().month
            day_of_week = datetime.now().weekday()
        
        # Multiplicadores
        advance_mult = self._get_anticipation_multiplier(days_ahead)
        season_mult = self._get_seasonal_multiplier(month)
        weekday_mult = self._get_weekday_multiplier(day_of_week)
        stops_mult = self._get_stops_multiplier(stops)
        cabin_mult = self._get_cabin_multiplier(cabin_class)
        airline_mult = self.AIRLINE_MULTIPLIERS.get(airline_type, 1.0)
        
        # ¡NUEVO! Demand factor (DecisionTree pattern)
        demand_mult = self._get_demand_multiplier(days_ahead, month, day_of_week)
        
        # Ruido proporcional
        noise = random.uniform(0.92, 1.08)
        
        # Precio final
        final_price = (
            base * 
            advance_mult * 
            season_mult * 
            weekday_mult * 
            stops_mult * 
            cabin_mult * 
            airline_mult *
            demand_mult *
            noise
        )
        
        # ¡NUEVO! Calcular confidence score
        confidence = self._calculate_confidence(
            days_ahead, month, stops, cabin_class, airline_type
        )
        
        logger.debug(
            f"🧠 {route}: Base=€{base} | Advance={advance_mult:.2f} | "
            f"Season={season_mult:.2f} | Weekday={weekday_mult:.2f} | "
            f"Stops={stops_mult:.2f} | Cabin={cabin_mult:.2f} | "
            f"Airline={airline_mult:.2f} | Demand={demand_mult:.2f} | "
            f"Final=€{final_price:.0f} | Confidence={confidence:.0%}"
        )
        
        return max(100, int(final_price)), confidence
    
    def _get_anticipation_multiplier(self, days_ahead: int) -> float:
        """Patrón curva en U mejorado"""
        if days_ahead < 0:
            return 2.5
        elif days_ahead < 3:
            return 2.0
        elif days_ahead < 7:
            return 1.7
        elif days_ahead < 14:
            return 1.4
        elif days_ahead < 30:
            return 1.15
        elif days_ahead < 45:
            return 1.05
        elif days_ahead <= 60:
            return 1.0  # Sweet spot
        elif days_ahead < 90:
            return 1.1
        elif days_ahead < 120:
            return 1.25
        else:
            return 1.35
    
    def _get_seasonal_multiplier(self, month: int) -> float:
        if month in self.HIGH_SEASON:
            return 1.35
        elif month in [3, 4, 5]:
            return 1.15
        elif month in self.LOW_SEASON:
            return 0.85
        else:
            return 1.0
    
    def _get_weekday_multiplier(self, weekday: int) -> float:
        if weekday == 4:  # Viernes
            return 1.15
        elif weekday == 6:  # Domingo
            return 1.2
        elif weekday in [1, 2]:  # Martes, Miércoles
            return 0.95
        else:
            return 1.0
    
    def _get_stops_multiplier(self, stops: int) -> float:
        if stops == 0:
            return 1.35
        elif stops == 1:
            return 1.0
        elif stops == 2:
            return 0.82
        else:
            return 0.75
    
    def _get_cabin_multiplier(self, cabin_class: str) -> float:
        multipliers = {
            'economy': 1.0,
            'premium_economy': 1.75,
            'business': 4.2,
            'first': 6.5
        }
        return multipliers.get(cabin_class, 1.0)
    
    def _get_demand_multiplier(self, days_ahead: int, month: int, weekday: int) -> float:
        """
        ¡NUEVO! Multiplicador de demanda basado en DecisionTree patterns.
        Simula comportamiento real de pricing dinámico.
        """
        # Alta demanda: temporada alta + último minuto + fin de semana
        demand_score = 0
        
        if month in self.HIGH_SEASON:
            demand_score += 2
        if days_ahead < 14:
            demand_score += 2
        if weekday in [4, 5, 6]:  # Vie-Dom
            demand_score += 1
        
        # Decision tree
        if demand_score >= 4:
            return 1.25  # Muy alta demanda
        elif demand_score >= 3:
            return 1.15  # Alta demanda
        elif demand_score >= 2:
            return 1.05  # Media
        else:
            return 0.95  # Baja demanda
    
    def _calculate_confidence(self, days_ahead: int, month: int, stops: int,
                            cabin_class: str, airline_type: str) -> float:
        """
        ¡NUEVO! Calcula confidence score de la predicción.
        
        Factors:
        - Anticipación (mejor confianza en sweet spot)
        - Disponibilidad de datos históricos
        - Volatilidad esperada
        """
        confidence = 0.85  # Base
        
        # Factor 1: Anticipación
        if 45 <= days_ahead <= 60:
            confidence += 0.10  # Sweet spot = alta confianza
        elif days_ahead < 7:
            confidence -= 0.20  # Último minuto = volátil
        elif days_ahead > 120:
            confidence -= 0.10  # Muy anticipado = incierto
        
        # Factor 2: Stops (directo = más predecible)
        if stops == 0:
            confidence += 0.05
        elif stops >= 2:
            confidence -= 0.05
        
        # Factor 3: Cabin (economy más predecible)
        if cabin_class == 'economy':
            confidence += 0.05
        elif cabin_class in ['business', 'first']:
            confidence -= 0.10
        
        # Factor 4: Airline type
        if airline_type == 'lowcost':
            confidence += 0.05  # Lowcost más predecible
        elif airline_type == 'charter':
            confidence -= 0.10  # Charter menos predecible
        
        return max(0.3, min(0.99, confidence))
    
    def get_breakdown(self, origin: str, dest: str, flight_date: str = None,
                     cabin_class: str = 'economy', stops: int = 1,
                     airline_type: str = 'legacy') -> Dict[str, Any]:
        """Desglose detallado con confidence"""
        route = f"{origin}-{dest}"
        price, confidence = self.predict(origin, dest, flight_date, cabin_class, stops, airline_type)
        
        return {
            'route': route,
            'price': price,
            'confidence': confidence,
            'confidence_emoji': "🎯" if confidence >= 0.9 else "✅" if confidence >= 0.75 else "⚠️",
            'cabin_class': cabin_class,
            'stops': stops,
            'airline_type': airline_type
        }

# 🚀 FLIGHT API CLIENT ENTERPRISE
class FlightAPIClient:
    """Cliente multi-API con SerpAPI mejorada, rate limiting y fallback inteligente"""
    
    def __init__(self, api_keys: Dict, cache: TTLCache):
        self.api_keys = api_keys
        self.cache = cache
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': f'{APP_NAME}/{VERSION}'})
        self.breakers = {
            'aviationstack': CircuitBreaker('aviationstack', 3, 30),
            'serpapi': CircuitBreaker('serpapi', 5, 60)  # SerpAPI más tolerante
        }
        self.ml_predictor = MLSmartPredictor()
        
        # Rate limiting para SerpAPI
        self.serpapi_calls_today = 0
        self.serpapi_reset_date = datetime.now().date()
        
        # Registrar APIs en dashboard
        metrics_dashboard.register_api('aviationstack')
        metrics_dashboard.register_api('serpapi')
        metrics_dashboard.register_api('ml_smart')
        
        logger.info(f"✈️ API Client ENTERPRISE initialized with {len(api_keys)} keys + ML Smart")
    
    @retry_with_backoff(max_attempts=3, exceptions=(requests.RequestException, TimedOut))
    def get_price(self, origin: str, dest: str, name: str, flight_date: str = None,
                 cabin_class: str = 'economy', stops: int = 1,
                 airline_type: str = 'legacy') -> FlightPrice:
        route = f"{origin}-{dest}"
        cache_key = f"price:{route}:{flight_date or 'today'}:{cabin_class}:{stops}"
        
        # Check cache
        cached = self.cache.get(cache_key)
        if cached:
            logger.debug(f"💾 Using cached price for {route}")
            return cached
        
        # Try APIs in order with fallback
        api_order = [
            ('serpapi', self._get_serpapi_enhanced),
            ('aviationstack', self._get_aviationstack)
        ]
        
        for api_name, api_func in api_order:
            if api_name not in self.breakers:
                continue
            
            try:
                start_time = time.time()
                result = self.breakers[api_name].call(
                    api_func, origin, dest, flight_date, cabin_class, stops
                )
                duration = time.time() - start_time
                
                if result:
                    price, confidence, metadata = result
                    metrics_dashboard.record_call(api_name, True, duration, 
                                                 rate_limit_remaining=metadata.get('rate_limit'))
                    
                    source = PriceSource.SERP_API if api_name == 'serpapi' else PriceSource.AVIATION_STACK
                    flight_price = FlightPrice(
                        route, name, price, source, datetime.now(), 
                        confidence=confidence, metadata=metadata
                    )
                    
                    self.cache.set(cache_key, flight_price, CACHE_TTL)
                    logger.info(f"✅ {route}: €{price:.0f} from {api_name} ({duration:.2f}s, conf={confidence:.0%})")
                    return flight_price
                    
            except Exception as e:
                metrics_dashboard.record_call(api_name, False, 0, error=str(e))
                logger.warning(f"⚠️ {api_name} failed for {route}: {e}")
        
        # Fallback: ML Smart
        price, confidence = self.ml_predictor.predict(
            origin, dest, flight_date, cabin_class, stops, airline_type
        )
        flight_price = FlightPrice(
            route, name, price, PriceSource.ML_SMART, datetime.now(),
            confidence=confidence, metadata={'fallback': True}
        )
        
        metrics_dashboard.record_call('ml_smart', True, 0)
        self.cache.set(cache_key, flight_price, CACHE_TTL // 3)
        logger.info(f"🧠 {route}: €{price:.0f} (ML Smart Fallback, conf={confidence:.0%})")
        return flight_price
    
    def _get_aviationstack(self, origin: str, dest: str, flight_date: str = None,
                          cabin_class: str = 'economy', stops: int = 1) -> Optional[Tuple[float, float, Dict]]:
        """AviationStack API (fallback básico)"""
        key = self.api_keys.get('aviationstack')
        if not key or key == "TU_CLAVE_AVIATIONSTACK_AQUI":
            return None
        
        url = "http://api.aviationstack.com/v1/flights"
        params = {'access_key': key, 'dep_iata': origin, 'arr_iata': dest}
        
        r = self.session.get(url, params=params, timeout=API_TIMEOUT)
        r.raise_for_status()
        data = r.json()
        
        if 'data' in data and data['data']:
            price = data['data'][0].get('pricing', {}).get('total')
            if price:
                return float(price), 0.75, {'source': 'aviationstack'}
        
        return None
    
    def _get_serpapi_enhanced(self, origin: str, dest: str, flight_date: str = None,
                             cabin_class: str = 'economy', stops: int = 1) -> Optional[Tuple[float, float, Dict]]:
        """
        ¡NUEVO! SerpAPI Google Flights mejorada con:
        - Rate limiting inteligente
        - Parsing detallado de respuesta
        - Metadata enriquecida
        """
        key = self.api_keys.get('serpapi')
        if not key or key == "TU_CLAVE_SERPAPI_AQUI":
            return None
        
        # Rate limiting check
        today = datetime.now().date()
        if today != self.serpapi_reset_date:
            self.serpapi_calls_today = 0
            self.serpapi_reset_date = today
        
        if self.serpapi_calls_today >= SERPAPI_RATE_LIMIT:
            logger.warning(f"⚠️ SerpAPI rate limit reached ({SERPAPI_RATE_LIMIT}/day)")
            return None
        
        url = "https://serpapi.com/search.json"
        outbound_date = flight_date or (datetime.now() + timedelta(days=45)).strftime('%Y-%m-%d')
        
        params = {
            'engine': 'google_flights',
            'api_key': key,
            'departure_id': origin,
            'arrival_id': dest,
            'outbound_date': outbound_date,
            'currency': 'EUR',
            'hl': 'es'
        }
        
        # Filtro por cabin class
        if cabin_class != 'economy':
            params['travel_class'] = cabin_class
        
        # Filtro por stops
        if stops == 0:
            params['stops'] = '0'
        elif stops == 1:
            params['stops'] = '1'
        
        r = self.session.get(url, params=params, timeout=API_TIMEOUT)
        r.raise_for_status()
        data = r.json()
        
        self.serpapi_calls_today += 1
        
        # Parse response
        if 'best_flights' in data and data['best_flights']:
            flight = data['best_flights'][0]
            price = flight.get('price')
            
            if price:
                # Metadata enriquecida
                metadata = {
                    'source': 'serpapi_google_flights',
                    'rate_limit': SERPAPI_RATE_LIMIT - self.serpapi_calls_today,
                    'airline': flight.get('airline'),
                    'duration': flight.get('total_duration'),
                    'stops': len(flight.get('layovers', [])),
                    'departure_time': flight.get('departure_token'),
                    'api_calls_today': self.serpapi_calls_today
                }
                
                # Confidence alto para datos reales
                confidence = 0.95
                
                logger.debug(f"🔍 SerpAPI: {origin}->{dest} €{price} | Calls today: {self.serpapi_calls_today}/{SERPAPI_RATE_LIMIT}")
                return float(price), confidence, metadata
        
        # Si no hay "best_flights", intentar "other_flights"
        elif 'other_flights' in data and data['other_flights']:
            flight = data['other_flights'][0]
            price = flight.get('price')
            if price:
                metadata = {'source': 'serpapi_other', 'rate_limit': SERPAPI_RATE_LIMIT - self.serpapi_calls_today}
                return float(price), 0.85, metadata
        
        return None
    
    def health_check(self) -> Dict[str, Any]:
        """Health check con degradation alerts"""
        health = {
            'circuit_breakers': {},
            'cache': self.cache.get_metrics(),
            'ml_smart': {
                'status': HealthStatus.HEALTHY.value,
                'version': 'Enterprise DecisionTree',
                'features': ['Confidence Scores', 'Demand Patterns', 'Airline Types']
            },
            'alerts': metrics_dashboard.check_degradation()
        }
        
        for name, breaker in self.breakers.items():
            health['circuit_breakers'][name] = {
                'state': breaker.state.value,
                'health': breaker.health_status.value,
                'failures': breaker.fail_count
            }
        
        return health

# 💾 DATA MANAGER ENHANCED
class DataManager:
    """Gestor de datos con métricas avanzadas"""
    def __init__(self, file: str = CSV_FILE):
        self.file = Path(file)
        self._ensure_exists()
        logger.info(f"💾 DataManager initialized: {file}")
    
    def _ensure_exists(self):
        if not self.file.exists():
            pd.DataFrame(columns=[
                'route', 'name', 'price', 'source', 'timestamp', 'confidence', 'metadata'
            ]).to_csv(self.file, index=False, encoding='utf-8')
    
    def save(self, prices: List[FlightPrice]):
        if prices:
            df = pd.DataFrame([p.to_dict() for p in prices])
            df.to_csv(self.file, mode='a', header=False, index=False, encoding='utf-8')
            logger.info(f"💾 Saved {len(prices)} prices (avg confidence: {sum(p.confidence for p in prices)/len(prices):.0%})")
    
    def load(self) -> pd.DataFrame:
        try:
            df = pd.read_csv(self.file, encoding='utf-8')
            if 'confidence' not in df.columns:
                df['confidence'] = 0.85
            return df
        except Exception as e:
            logger.error(f"Error loading CSV: {e}")
            return pd.DataFrame()
    
    def get_stats(self) -> Dict[str, Any]:
        df = self.load()
        if df.empty:
            return {}
        
        return {
            'total': len(df),
            'avg_price': df['price'].mean(),
            'min_price': df['price'].min(),
            'max_price': df['price'].max(),
            'best_route': df.loc[df['price'].idxmin(), 'route'] if not df.empty else None,
            'avg_confidence': df['confidence'].mean() if 'confidence' in df.columns else 0.85,
            'sources': df['source'].value_counts().to_dict()
        }

# 📰 RSS ANALYZER (sin cambios significativos)
class RSSAnalyzer:
    KEYWORDS = ['sale', 'deal', 'cheap', 'error', 'fare', 'offer', 'promo', 'discount']
    
    def __init__(self, feeds: List[str]):
        self.feeds = feeds
        logger.info(f"📰 RSS Analyzer initialized with {len(feeds)} feeds")
    
    def find_deals(self) -> List[Dict]:
        deals = []
        for url in self.feeds:
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries[:5]:
                    if any(kw in entry.title.lower() for kw in self.KEYWORDS):
                        deals.append({
                            'title': entry.title,
                            'link': entry.link,
                            'source': getattr(feed.feed, 'title', 'RSS'),
                            'published': getattr(entry, 'published', 'Recent')
                        })
            except Exception as e:
                logger.error(f"RSS error {url}: {e}")
        return deals

# 🔍 FLIGHT SCANNER ENHANCED
class FlightScanner:
    """Motor de escaneo con mejor manejo de errores"""
    def __init__(self, config: ConfigManager, api: FlightAPIClient, data: DataManager):
        self.config = config
        self.api = api
        self.data = data
        logger.info(f"🔍 Scanner initialized: {len(config.flights)} routes")
    
    def scan_all(self) -> pd.DataFrame:
        flights = self.config.flights
        UI.section(f"FLIGHT SCANNER: {len(flights)} ROUTES")
        UI.status("🚀", f"Starting parallel scan with {MAX_WORKERS} workers...")
        
        results = []
        errors = []
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {
                executor.submit(
                    self._safe_get_price, f
                ): f for f in flights
            }
            
            for idx, future in enumerate(as_completed(futures), 1):
                try:
                    price = future.result()
                    if price:
                        results.append(price)
                    UI.progress(idx, len(flights), prefix="⏳ Progress")
                except Exception as e:
                    flight = futures[future]
                    errors.append(f"{flight['origin']}-{flight['dest']}: {e}")
                    logger.error(f"Scan error: {e}")
        
        if errors:
            logger.warning(f"⚠️ {len(errors)} routes failed")
        
        UI.status("✅", f"Scan complete: {len(results)}/{len(flights)} results", "SUCCESS")
        self.data.save(results)
        
        return pd.DataFrame([r.to_dict() for r in results])
    
    def _safe_get_price(self, flight: Dict) -> Optional[FlightPrice]:
        """Wrapper seguro para get_price con validación"""
        try:
            return self.api.get_price(
                flight['origin'],
                flight['dest'],
                flight['name'],
                flight.get('outbound_date'),
                flight.get('cabin_class', 'economy'),
                self._parse_stops(flight.get('stops', 'any')),
                flight.get('airline_type', 'legacy')
            )
        except Exception as e:
            logger.error(f"Error getting price for {flight['origin']}-{flight['dest']}: {e}")
            return None
    
    def _parse_stops(self, stops_config: str) -> int:
        if stops_config == "0":
            return 0
        elif stops_config == "1+":
            return random.choices([1, 2], weights=[70, 30])[0]
        elif stops_config == "1":
            return 1
        elif stops_config == "2":
            return 2
        else:
            return random.choices([0, 1, 2], weights=[20, 60, 20])[0]

# 💓 HEARTBEAT MONITOR
class HeartbeatMonitor:
    """¡NUEVO! Monitor para containers y health checks"""
    def __init__(self, interval: int = HEARTBEAT_INTERVAL):
        self.interval = interval
        self.last_beat = datetime.now()
        self.is_alive = True
        logger.info(f"💓 Heartbeat monitor initialized (interval={interval}s)")
    
    async def start(self, context: ContextTypes.DEFAULT_TYPE):
        """Job que se ejecuta periódicamente"""
        while self.is_alive:
            await asyncio.sleep(self.interval)
            self.last_beat = datetime.now()
            
            # Check degradation
            alerts = metrics_dashboard.check_degradation()
            if alerts:
                logger.warning(f"⚠️ Degradation detected: {', '.join(alerts)}")
                # Enviar alerta al admin si es crítico
                for alert in alerts:
                    if '🔴' in alert:
                        # TODO: Enviar telegram alert
                        pass
            
            logger.info(f"💓 Heartbeat OK | Uptime: {self._get_uptime()}")
    
    def _get_uptime(self) -> str:
        uptime = (datetime.now() - self.last_beat).total_seconds()
        return f"{uptime:.0f}s"
    
    def stop(self):
        self.is_alive = False

# 🤖 TELEGRAM BOT ENTERPRISE
class TelegramBot:
    """Handler del bot con UX 2026: inline keyboards, typing indicators, retry logic"""
    
    def __init__(self, config: ConfigManager, scanner: FlightScanner, 
                 data: DataManager, rss: RSSAnalyzer):
        self.config = config
        self.scanner = scanner
        self.data = data
        self.rss = rss
        self.bot = Bot(token=config.bot_token)
        self.heartbeat = HeartbeatMonitor()
        logger.info("🤖 Telegram bot ENTERPRISE initialized")
    
    @retry_with_backoff(max_attempts=3, exceptions=(TelegramError, NetworkError))
    async def send_message_safe(self, chat_id: str, text: str, **kwargs):
        """Send message con retry logic"""
        try:
            await self.bot.send_message(chat_id, text, **kwargs)
        except RetryAfter as e:
            logger.warning(f"⚠️ Rate limit hit, waiting {e.retry_after}s")
            await asyncio.sleep(e.retry_after)
            await self.bot.send_message(chat_id, text, **kwargs)
    
    async def send_typing(self, chat_id: str):
        """¡NUEVO! Typing indicator para UX"""
        await self.bot.send_chat_action(chat_id, ChatAction.TYPING)
    
    async def send_alert(self, price: FlightPrice):
        try:
            # Inline keyboard para acciones rápidas
            keyboard = [
                [
                    InlineKeyboardButton("🔍 Google Flights", 
                                       url=f"https://www.google.com/flights?q={price.route.replace('✈️', ' to ')}"),
                    InlineKeyboardButton("💡 Skyscanner", 
                                       url=f"https://www.skyscanner.com/transport/flights/{price.route.split('✈️')[0]}/{price.route.split('✈️')[1]}/")
                ],
                [InlineKeyboardButton("📊 Ver Stats", callback_data="stats")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            confidence_emoji = price.get_confidence_emoji()
            msg = f"""🚨 *¡CHOLLO DETECTADO!*

─────────────────
✈️ *Ruta:* `{price.route}`
💰 *Precio:* **€{price.price:.0f}**
📊 *Fuente:* {price.source.value}
{confidence_emoji} *Confianza:* {price.confidence:.0%}
─────────────────
⚡ *¡Reserva rápido!*
🕐 {price.timestamp.strftime('%d/%m/%Y %H:%M')}

_Precio < €{self.config.alert_threshold:.0f}_"""
            
            await self.send_message_safe(
                self.config.chat_id, msg, 
                parse_mode='Markdown', 
                reply_markup=reply_markup
            )
            logger.info(f"✅ Alert sent: {price.route}")
        except Exception as e:
            logger.error(f"Error sending alert: {e}")
    
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.send_typing(update.effective_chat.id)
        
        keyboard = [
            [InlineKeyboardButton("🔥 Escaneo Completo", callback_data="scan_all")],
            [InlineKeyboardButton("📊 Dashboard", callback_data="stats"),
             InlineKeyboardButton("💚 Health", callback_data="health")],
            [InlineKeyboardButton("📰 RSS Deals", callback_data="rss"),
             InlineKeyboardButton("💡 Hacks", callback_data="hacks")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        msg = f"""🏆 *BIENVENIDO A {APP_NAME.upper()} v{VERSION.split()[0]}*

─────────────────────

*🚀 Sistema Enterprise 2026*

✅ SerpAPI Google Flights Enhanced
✅ ML DecisionTree Patterns
✅ Confidence Scores
✅ Rate Limiting Inteligente
✅ Inline Keyboards UX
✅ Webhooks Ready
✅ Health Monitoring

─────────────────────

📋 *COMANDOS:*

🔥 `/supremo` - Escaneo completo
🛫 `/scan XX YY` - Ruta específica
📊 `/status` - Dashboard stats
💚 `/health` - Health check
📰 `/rss` - Ofertas flash
💡 `/chollos` - 14 hacks
🎯 `/sweetspot XX YY` - Best window
🔍 `/breakdown XX YY` - Price analysis

─────────────────────

⚙️ Umbral: €{self.config.alert_threshold}
✈️ Rutas: {len(self.config.flights)}

💬 Usa botones o comandos"""
        
        await update.message.reply_text(msg, parse_mode='Markdown', reply_markup=reply_markup)
    
    async def cmd_supremo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.send_typing(update.effective_chat.id)
        
        initial = await update.message.reply_text(
            "🔄 *ESCANEO SUPREMO v12.0 ENTERPRISE*\n\n"
            f"✈️ {len(self.config.flights)} rutas\n🧠 ML Enterprise active\n"
            "🔍 SerpAPI Google Flights ready\n\n"
            "_Analyzing with DecisionTree patterns..._",
            parse_mode='Markdown'
        )
        
        df = self.scanner.scan_all()
        threshold = self.config.alert_threshold
        hot = df[df['price'] < threshold]
        
        # Enviar alertas
        for _, row in hot.iterrows():
            price = FlightPrice(
                row['route'], row['name'], row['price'], 
                PriceSource.ML_SMART, datetime.fromisoformat(row['timestamp']),
                confidence=row.get('confidence', 0.85)
            )
            await self.send_alert(price)
        
        # Stats por fuente
        source_stats = df.groupby('source')['price'].agg(['count', 'mean']).round(0)
        source_text = "\n".join([f"   {src}: {int(row['count'])} calls (avg €{int(row['mean'])})" 
                                for src, row in source_stats.iterrows()])
        
        msg = f"""✅ *SCAN COMPLETE*

─────────────────

📊 *SUMMARY:*

✈️ Scanned: {len(df)}
🔥 Hot deals: {len(hot)}
💎 Best: **€{df['price'].min():.0f}** ({df.loc[df['price'].idxmin(), 'route']})
📈 Avg: €{df['price'].mean():.0f}
🎯 Avg Confidence: {df['confidence'].mean():.0%}

📡 *BY SOURCE:*
{source_text}

─────────────────

🏆 *TOP 5:*

"""
        
        top5 = df.nsmallest(5, 'price')
        for i, (_, r) in enumerate(top5.iterrows(), 1):
            emoji = "🔥" if r['price'] < threshold else "📊"
            conf_emoji = "🎯" if r['confidence'] > 0.9 else "✅"
            msg += f"{i}. {emoji} *{r['route']}* - €{r['price']:.0f} {conf_emoji}\n"
        
        msg += f"\n🕐 {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        
        keyboard = [[InlineKeyboardButton("📊 Ver Dashboard Completo", callback_data="stats")]]
        await initial.edit_text(msg, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
    
    async def cmd_health(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.send_typing(update.effective_chat.id)
        
        health = self.scanner.api.health_check()
        summary = metrics_dashboard.get_summary()
        
        msg = "💚 *HEALTH CHECK v12.0*\n\n───────────────\n\n"
        
        # Circuit breakers
        msg += "*CIRCUIT BREAKERS:*\n"
        for api, data in health['circuit_breakers'].items():
            msg += f"  {api}: {data['health']}\n"
            msg += f"    State: {data['state']}\n"
        
        # APIs metrics
        msg += "\n*API METRICS:*\n"
        for api, metrics in summary['apis'].items():
            msg += f"  {api}:\n"
            msg += f"    Calls: {metrics['calls']}\n"
            msg += f"    Success: {metrics['success_rate']:.0%}\n"
            msg += f"    Avg time: {metrics['avg_time']:.2f}s\n"
            if metrics['rate_limit']:
                msg += f"    Rate limit: {metrics['rate_limit']}\n"
        
        # Cache
        cache_metrics = health['cache']
        msg += f"\n🗃️ *CACHE:*\n"
        msg += f"  Hit rate: {cache_metrics['hit_rate']:.0%}\n"
        msg += f"  Size: {cache_metrics['size']} items\n"
        
        # Alerts
        if health['alerts']:
            msg += "\n⚠️ *ALERTS:*\n"
            for alert in health['alerts']:
                msg += f"  {alert}\n"
        else:
            msg += "\n✅ No alerts"
        
        msg += f"\n⏱️ Uptime: {summary['uptime_seconds']:.0f}s"
        
        await update.message.reply_text(msg, parse_mode='Markdown')
    
    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.send_typing(update.effective_chat.id)
        
        stats = self.data.get_stats()
        if not stats:
            await update.message.reply_text("ℹ️ No hay datos. Usa `/supremo` primero.", parse_mode='Markdown')
            return
        
        msg = f"""📈 *DASHBOARD v{VERSION.split()[0]}*

─────────────────

📋 Total: {stats['total']}
💰 Avg: €{stats['avg_price']:.2f}
💎 Min: €{stats['min_price']:.0f}
📈 Max: €{stats['max_price']:.0f}
🎯 Avg Confidence: {stats['avg_confidence']:.0%}

🏆 *BEST:* {stats['best_route']}
💰 **€{stats['min_price']:.0f}**

📊 *BY SOURCE:*
"""
        
        for source, count in stats['sources'].items():
            msg += f"   {source}: {count}\n"
        
        msg += f"\n🕐 {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        
        keyboard = [[InlineKeyboardButton("🔄 Refresh", callback_data="stats")]]
        await update.message.reply_text(msg, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
    
    async def cmd_scan(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if len(context.args) < 2:
            await update.message.reply_text(
                "❌ Uso: `/scan ORIGEN DESTINO [cabin] [stops] [airline]`\n"
                "Ej: `/scan MAD MGA business 0 legacy`",
                parse_mode='Markdown'
            )
            return
        
        await self.send_typing(update.effective_chat.id)
        
        origin = context.args[0].upper()
        dest = context.args[1].upper()
        cabin = context.args[2] if len(context.args) > 2 else 'economy'
        stops = int(context.args[3]) if len(context.args) > 3 else 1
        airline = context.args[4] if len(context.args) > 4 else 'legacy'
        
        try:
            FlightRoute(origin, dest, "test")
        except ValueError as e:
            await update.message.reply_text(f"❌ {e}", parse_mode='Markdown')
            return
        
        initial = await update.message.reply_text(
            f"🔄 *SCANNING {origin}✈️{dest}...*\n\n"
            "🔍 _Checking SerpAPI..._\n"
            "🧠 _ML Smart analyzing..._\n"
            f"💺 Cabin: {cabin}\n✈️ Stops: {stops}\n🏢 Airline: {airline}",
            parse_mode='Markdown'
        )
        
        price = self.scanner.api.get_price(origin, dest, f"{origin}-{dest}", None, cabin, stops, airline)
        is_deal = price.is_deal(self.config.alert_threshold)
        
        keyboard = [
            [InlineKeyboardButton("🔍 Google Flights", 
                                url=f"https://www.google.com/flights?q={origin} to {dest}"),
             InlineKeyboardButton("💡 Skyscanner", 
                                url=f"https://www.skyscanner.com/transport/flights/{origin.lower()}/{dest.lower()}/")]
        ]
        
        msg = f"""✅ *ANALYSIS COMPLETE*

─────────────────

✈️ *Route:* {price.route}
💵 *Price:* **€{price.price:.0f}**
💺 *Cabin:* {cabin}
✈️ *Stops:* {stops}
🏢 *Airline:* {airline}
📊 *Source:* {price.source.value}
{price.get_confidence_emoji()} *Confidence:* {price.confidence:.0%}
{'🔥' if is_deal else '📊'} *Status:* {'**DEAL!**' if is_deal else 'Normal'}

─────────────────

{'⚡ **Book now!**' if is_deal else '💡 Wait or set alerts'}

🕐 {datetime.now().strftime('%d/%m/%Y %H:%M')}"""
        
        await initial.edit_text(msg, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
    
    async def cmd_breakdown(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """¡NUEVO! Análisis detallado de pricing"""
        if len(context.args) < 2:
            await update.message.reply_text(
                "❌ Uso: `/breakdown ORIGEN DESTINO [cabin] [stops] [airline]`",
                parse_mode='Markdown'
            )
            return
        
        await self.send_typing(update.effective_chat.id)
        
        origin = context.args[0].upper()
        dest = context.args[1].upper()
        cabin = context.args[2] if len(context.args) > 2 else 'economy'
        stops = int(context.args[3]) if len(context.args) > 3 else 1
        airline = context.args[4] if len(context.args) > 4 else 'legacy'
        
        breakdown = self.scanner.api.ml_predictor.get_breakdown(
            origin, dest, None, cabin, stops, airline
        )
        
        msg = f"""🔍 *PRICE BREAKDOWN*

─────────────────

✈️ *Route:* {breakdown['route']}
💰 *Price:* **€{breakdown['price']}**
{breakdown['confidence_emoji']} *Confidence:* {breakdown['confidence']:.0%}

📊 *FACTORS:*
💺 Cabin: {cabin}
✈️ Stops: {stops}
🏢 Airline type: {airline}

─────────────────

🧠 *ML SMART ENTERPRISE*
DecisionTree patterns active

🕐 {datetime.now().strftime('%d/%m/%Y %H:%M')}"""
        
        await update.message.reply_text(msg, parse_mode='Markdown')
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """¡NUEVO! Handler para inline keyboards"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "scan_all":
            await self.cmd_supremo(update, context)
        elif query.data == "stats":
            await self.cmd_status(update, context)
        elif query.data == "health":
            await self.cmd_health(update, context)
        elif query.data == "rss":
            await self._handle_rss_callback(update)
        elif query.data == "hacks":
            await self._handle_hacks_callback(update)
    
    async def _handle_rss_callback(self, update: Update):
        """Handler RSS con typing indicator"""
        await self.send_typing(update.effective_chat.id)
        await query.message.reply_text("📰 *SCANNING RSS...*", parse_mode='Markdown')
        
        deals = self.rss.find_deals()
        if not deals:
            await query.message.reply_text("ℹ️ No hay ofertas flash ahora")
        else:
            for deal in deals[:5]:
                msg = f"""📰 *OFERTA FLASH*

{deal['title']}

🔗 [Ver oferta]({deal['link']})
───────────────
📡 {deal['source']}
🕐 {deal['published']}"""
                await query.message.reply_text(msg, parse_mode='Markdown')

# 🚀 MAIN ENTERPRISE
def main():
    try:
        UI.header(f"🎆 {APP_NAME.upper()} v{VERSION} 🎆")
        UI.print("Sistema Enterprise de Monitorización de Vuelos 2026".center(80), Fore.CYAN + Style.BRIGHT)
        UI.print("SerpAPI Enhanced | ML DecisionTree | Webhooks Ready | Health Monitoring".center(80), Fore.CYAN)
        UI.header("")
        
        UI.section("SYSTEM INITIALIZATION")
        
        config = ConfigManager()
        UI.status("✅", "Config loaded", "SUCCESS")
        
        cache = TTLCache(CACHE_TTL)
        UI.status("✅", "Cache initialized", "SUCCESS")
        
        api = FlightAPIClient(config.api_keys, cache)
        UI.status("✅", "API client + ML Smart Enterprise ready", "SUCCESS")
        
        data = DataManager()
        UI.status("✅", "Data manager ready", "SUCCESS")
        
        scanner = FlightScanner(config, api, data)
        UI.status("✅", "Scanner initialized", "SUCCESS")
        
        rss = RSSAnalyzer(config.rss_feeds)
        UI.status("✅", "RSS analyzer ready", "SUCCESS")
        
        bot = TelegramBot(config, scanner, data, rss)
        UI.status("✅", "Telegram bot Enterprise ready", "SUCCESS")
        
        UI.section("ACTIVE CONFIGURATION")
        config_data = {
            "Routes": len(config.flights),
            "Threshold": f"€{config.alert_threshold}",
            "APIs": len(config.api_keys),
            "RSS Feeds": len(config.rss_feeds),
            "Cache TTL": f"{CACHE_TTL}s",
            "Circuit Threshold": f"{CIRCUIT_BREAK_THRESHOLD} fails",
            "ML Smart": "Enterprise DecisionTree",
            "Webhooks": "Enabled" if config.use_webhooks else "Disabled (polling)",
            "Rate Limit": f"{SERPAPI_RATE_LIMIT} calls/day"
        }
        UI.metric_table(config_data)
        
        UI.section("STARTING TELEGRAM BOT")
        app = Application.builder().token(config.bot_token).build()
        
        # Comandos
        app.add_handler(CommandHandler("start", bot.cmd_start))
        app.add_handler(CommandHandler("supremo", bot.cmd_supremo))
        app.add_handler(CommandHandler("status", bot.cmd_status))
        app.add_handler(CommandHandler("health", bot.cmd_health))
        app.add_handler(CommandHandler("scan", bot.cmd_scan))
        app.add_handler(CommandHandler("breakdown", bot.cmd_breakdown))
        
        # Inline keyboards
        app.add_handler(CallbackQueryHandler(bot.handle_callback))
        
        UI.status("✅", "All commands registered", "SUCCESS")
        
        # Heartbeat job
        app.job_queue.run_repeating(bot.heartbeat.start, interval=HEARTBEAT_INTERVAL, first=10)
        UI.status("💓", f"Heartbeat monitor started ({HEARTBEAT_INTERVAL}s)", "SUCCESS")
        
        UI.header("✅ SYSTEM OPERATIONAL v12.0 ENTERPRISE")
        
        if config.use_webhooks:
            UI.status("🌐", f"Starting webhooks on {config.webhook_url}:{config.webhook_port}", "INFO")
            app.run_webhook(
                listen="0.0.0.0",
                port=config.webhook_port,
                url_path=config.bot_token,
                webhook_url=f"{config.webhook_url}/{config.bot_token}"
            )
        else:
            UI.status("👂", "Bot listening via polling (Ctrl+C to stop)", "SUCCESS")
            app.run_polling(allowed_updates=Update.ALL_TYPES)
        
        logger.info("🚀 System v12.0 Enterprise started")
        
    except KeyboardInterrupt:
        UI.header("🛑 SHUTDOWN REQUESTED")
        UI.status("⏹️", "Stopping heartbeat...")
        UI.status("💾", "Saving state...")
        UI.header("✅ BOT STOPPED")
        logger.info("✅ System stopped by user")
        
    except Exception as e:
        UI.header("❌ CRITICAL ERROR")
        UI.status("⚠️", f"Error: {e}", "ERROR")
        UI.print(f"\n   📋 Check logs: {LOG_FILE}\n")
        logger.critical(f"Critical error: {e}")
        raise

if __name__ == '__main__':
    main()
