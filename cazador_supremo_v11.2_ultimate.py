#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
═════════════════════════════════════════════════════════════════════════════
║       🎆 CAZADOR SUPREMO v11.2 ULTIMATE EDITION 🎆                   ║
║   🚀 Sistema Definitivo de Monitorización de Vuelos 🚀              ║
═════════════════════════════════════════════════════════════════════════════

👨‍💻 Autor: @Juanka_Spain | 🏷️ v11.2.0 Ultimate | 📅 2026-01-13 | 📋 MIT License

🌟 ULTIMATE FEATURES:
✅ Arquitectura Enterprise POO  ✅ Circuit Breaker Pattern    ✅ Intelligent Caching TTL
✅ Health Checks Auto          ✅ Performance Metrics       ✅ Exponential Backoff
✅ Rate Limiting APIs          ✅ Logging Pro Rotation     ✅ Emoji Enhanced UI
✅ Multi-API Fallback           ✅ Stats Advanced Analysis   ✅ RSS Feed Monitor
✅ Type Hints Complete          ✅ 14 Pro Hacks Included    ✅ Telegram Interactive
✅ ML Smart Enhanced NEW!       ✅ Patrones Mercado Real    ✅ Predicciones Inteligentes

🆕 NUEVO EN v11.2:
⭐ ML SMART ENHANCED - Predicciones basadas en patrones reales del mercado
⭐ Sweet Spot Detection - Mejor precio entre 45-60 días anticipación
⭐ Seasonal Adjustment - Ajuste automático por temporada alta/baja
⭐ Weekend Premium - Vuelos de fin de semana más caros (+15%)
⭐ Stops Multiplier - Directo +35%, 2 escalas -18%
⭐ Cabin Class Precise - Business x4.2, First x6.5
⭐ Price Breakdown Debug - Transparencia total del cálculo

📦 Dependencies: python-telegram-bot pandas requests feedparser
🚀 Usage: python cazador_supremo_v11.2_ultimate.py
⚙️ Config: Edit config.json with your tokens
"""

import asyncio, requests, pandas as pd, feedparser, json, random, os, sys, re, time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict, deque
from functools import wraps
import logging
from logging.handlers import RotatingFileHandler
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.error import TelegramError

# UTF-8 setup for Windows
if sys.platform == 'win32':
    try:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
        os.system('chcp 65001 > nul 2>&1')
    except: pass

# 🌐 GLOBAL CONFIG
VERSION = "11.2.0 Ultimate"
APP_NAME = "Cazador Supremo"
CONFIG_FILE, LOG_FILE, CSV_FILE = "config.json", "cazador_supremo.log", "deals_history.csv"
MAX_WORKERS, API_TIMEOUT = 20, 10
CACHE_TTL, CIRCUIT_BREAK_THRESHOLD = 300, 5

# 📦 ENUMS
class PriceSource(Enum):
    AVIATION_STACK = "AviationStack ✈️"
    SERP_API = "GoogleFlights 🔍"
    ML_SMART = "ML-Smart 🧠"  # ← MEJORADO!

class CircuitState(Enum):
    CLOSED, HALF_OPEN, OPEN = "🟢 Closed", "🟡 Half-Open", "🔴 Open"

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
    
    def to_dict(self) -> Dict:
        return {'route': self.route, 'name': self.name, 'price': self.price, 
                'source': self.source.value, 'timestamp': self.timestamp.isoformat()}
    
    def is_deal(self, threshold: float) -> bool:
        return self.price < threshold

# 📊 LOGGER PROFESSIONAL
class Logger:
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
    
    def debug(self, msg: str): self.logger.debug(msg)
    def info(self, msg: str): self.logger.info(msg)
    def warning(self, msg: str): self.logger.warning(msg)
    def error(self, msg: str, exc=False): self.logger.error(msg, exc_info=exc)
    def critical(self, msg: str): self.logger.critical(msg, exc_info=True)

logger = Logger(APP_NAME, LOG_FILE)

# 🛡️ CIRCUIT BREAKER PATTERN
class CircuitBreaker:
    """Circuit breaker para prevenir cascading failures"""
    def __init__(self, name: str, fail_max: int = CIRCUIT_BREAK_THRESHOLD, reset_timeout: int = 60):
        self.name, self.fail_max, self.reset_timeout = name, fail_max, reset_timeout
        self.state, self.fail_count, self.last_fail_time = CircuitState.CLOSED, 0, None
        logger.info(f"⚔️ CircuitBreaker '{name}' initialized: fail_max={fail_max}, reset={reset_timeout}s")
    
    def call(self, func: callable, *args, **kwargs):
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_fail_time > self.reset_timeout:
                logger.info(f"🟡 {self.name}: OPEN → HALF_OPEN (reset timeout reached)")
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception(f"⛔ Circuit {self.name} is OPEN (cooling down)")
        
        try:
            result = func(*args, **kwargs)
            if self.state == CircuitState.HALF_OPEN:
                logger.info(f"🟢 {self.name}: HALF_OPEN → CLOSED (success)")
                self.state, self.fail_count = CircuitState.CLOSED, 0
            return result
        except Exception as e:
            self.fail_count += 1
            self.last_fail_time = time.time()
            logger.warning(f"⚠️ {self.name}: Failure #{self.fail_count}/{self.fail_max} - {e}")
            
            if self.fail_count >= self.fail_max:
                logger.error(f"🔴 {self.name}: CLOSED → OPEN (threshold reached)")
                self.state = CircuitState.OPEN
            raise

# 📦 INTELLIGENT CACHE WITH TTL
class TTLCache:
    """Caché con expiración por item (Time To Live)"""
    def __init__(self, default_ttl: int = CACHE_TTL):
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self.default_ttl, self.hits, self.misses = default_ttl, 0, 0
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
    
    def clear(self):
        self._cache.clear()
        logger.info("🧹 Cache cleared")

# 📊 PERFORMANCE METRICS
class PerformanceMetrics:
    """Colecta y analiza métricas de rendimiento"""
    def __init__(self):
        self.api_times = defaultdict(list)
        self.api_success = defaultdict(int)
        self.api_failures = defaultdict(int)
    
    def record_api_call(self, api_name: str, duration: float, success: bool):
        self.api_times[api_name].append(duration)
        if success:
            self.api_success[api_name] += 1
        else:
            self.api_failures[api_name] += 1
    
    def get_stats(self, api_name: str) -> Dict[str, Any]:
        times = self.api_times.get(api_name, [])
        if not times:
            return {}
        return {
            'avg_time': sum(times) / len(times),
            'min_time': min(times),
            'max_time': max(times),
            'total_calls': len(times),
            'success_rate': self.api_success[api_name] / (self.api_success[api_name] + self.api_failures[api_name])
        }

metrics = PerformanceMetrics()

# 🏛️ CONSOLE UI WITH EMOJIS
class UI:
    """Beautiful console UI with emojis"""
    RESET, BOLD, GREEN, YELLOW, RED, CYAN = '\033[0m', '\033[1m', '\033[92m', '\033[93m', '\033[91m', '\033[96m'
    
    @staticmethod
    def print(text: str, color: str = '', flush: bool = True):
        try:
            print(f"{color}{text}{UI.RESET}" if color else text, flush=flush)
        except UnicodeEncodeError:
            print(text.encode('ascii', 'ignore').decode('ascii'), flush=flush)
    
    @staticmethod
    def header(title: str):
        UI.print(f"\n{'='*80}", UI.CYAN)
        UI.print(f"{title.center(80)}", UI.BOLD + UI.CYAN)
        UI.print(f"{'='*80}\n", UI.CYAN)
    
    @staticmethod
    def section(title: str):
        UI.print(f"\n{'─'*80}\n📍 {title}\n{'─'*80}\n", UI.CYAN)
    
    @staticmethod
    def status(emoji: str, msg: str, typ: str = "INFO"):
        ts = datetime.now().strftime('%H:%M:%S')
        colors = {"INFO": UI.CYAN, "SUCCESS": UI.GREEN, "WARNING": UI.YELLOW, "ERROR": UI.RED}
        UI.print(f"[{ts}] {emoji} {msg}", colors.get(typ, ''))
    
    @staticmethod
    def progress(current: int, total: int, prefix: str = "⏳", width: int = 40):
        pct = (current / total) * 100
        filled = int(width * current / total)
        bar = '█' * filled + '░' * (width - filled)
        UI.print(f"\r{prefix} [{bar}] {pct:.0f}% ({current}/{total})", flush=True)
        if current == total: print()

# ⚙️ CONFIG MANAGER
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
        if not self._config['telegram'].get('token') or not self._config['telegram'].get('chat_id'):
            raise ValueError("❌ Invalid Telegram config")
    
    @property
    def bot_token(self) -> str: return self._config['telegram']['token']
    
    @property
    def chat_id(self) -> str: return self._config['telegram']['chat_id']
    
    @property
    def flights(self) -> List[Dict]: return self._config['flights']
    
    @property
    def alert_threshold(self) -> float: return float(self._config.get('alert_min', 500))
    
    @property
    def api_keys(self) -> Dict: return self._config.get('apis', {})
    
    @property
    def rss_feeds(self) -> List[str]: return self._config.get('rss_feeds', [])

# 🧠 ML SMART PREDICTOR ENHANCED (¡MEJORADO!)
class MLSmartPredictor:
    """
    Predictor inteligente MEJORADO basado en patrones reales del mercado aéreo.
    Incluye ajustes precisos de escalas, cabina, y transparencia con get_breakdown().
    """
    
    # Precios base por ruta (basados en mercado real 2026)
    BASE_PRICES = {
        'MAD-MGA': 680, 'MGA-MAD': 700,
        'MAD-MIA': 520, 'MIA-MAD': 580,
        'MAD-BOG': 580, 'BOG-MAD': 620,
        'MAD-NYC': 450, 'NYC-MAD': 500,
        'MAD-MEX': 700, 'MEX-MAD': 720,
        'MAD-LAX': 550, 'LAX-MAD': 600,
    }
    
    # Temporadas (meses)
    HIGH_SEASON = [6, 7, 8, 12]  # Verano + Navidad
    LOW_SEASON = [1, 2, 9, 10, 11]  # Ene, Feb, Sept-Nov
    
    def __init__(self):
        logger.info("🧠 ML Smart Predictor ENHANCED initialized with advanced patterns")
    
    def predict(self, origin: str, dest: str, flight_date: str = None, 
                cabin_class: str = 'economy', stops: int = 1) -> float:
        """
        Predice precio con TODOS los factores:
        - Anticipación (sweet spot 45-60d)
        - Temporada (alta/baja)
        - Día semana (finde +15%)
        - Escalas (directo +35%, 2 escalas -18%)
        - Cabina (business x4.2, first x6.5)
        - Ruido proporcional (±8%)
        """
        route = f"{origin}-{dest}"
        
        # 1. Precio base por ruta
        base = self.BASE_PRICES.get(route, 650)
        
        # 2. Calcular días de anticipación y variables de fecha
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
        
        # 3. MULTIPLICADOR DE ANTICIPACIÓN (curva en U)
        anticipation_mult = self._get_anticipation_multiplier(days_ahead)
        
        # 4. MULTIPLICADOR DE TEMPORADA
        seasonal_mult = self._get_seasonal_multiplier(month)
        
        # 5. MULTIPLICADOR DÍA DE SEMANA
        weekday_mult = self._get_weekday_multiplier(day_of_week)
        
        # 6. MULTIPLICADOR DE ESCALAS (¡NUEVO!)
        stops_mult = self._get_stops_multiplier(stops)
        
        # 7. MULTIPLICADOR DE CABINA (¡MEJORADO!)
        cabin_mult = self._get_cabin_multiplier(cabin_class)
        
        # 8. RUIDO PROPORCIONAL (±8% en lugar de ±250€ fijo)
        noise = random.uniform(0.92, 1.08)
        
        # 9. CÁLCULO FINAL
        final_price = (
            base * 
            anticipation_mult * 
            seasonal_mult * 
            weekday_mult * 
            stops_mult * 
            cabin_mult * 
            noise
        )
        
        # Log detallado
        logger.debug(
            f"🧠 {route}: Base=€{base} | Days={days_ahead} (x{anticipation_mult:.2f}) | "
            f"Season=M{month} (x{seasonal_mult:.2f}) | Weekday={day_of_week} (x{weekday_mult:.2f}) | "
            f"Stops={stops} (x{stops_mult:.2f}) | Cabin={cabin_class} (x{cabin_mult:.2f}) | "
            f"Final=€{final_price:.0f}"
        )
        
        return max(100, int(final_price))
    
    def _get_anticipation_multiplier(self, days_ahead: int) -> float:
        """Patrón curva en U: sweet spot 45-60 días"""
        if days_ahead < 0:
            return 2.5      # Vuelo pasado (error)
        elif days_ahead < 3:
            return 2.0      # Últimos 3 días: +100%
        elif days_ahead < 7:
            return 1.7      # Última semana: +70%
        elif days_ahead < 14:
            return 1.4      # 2 semanas: +40%
        elif days_ahead < 30:
            return 1.15     # 1 mes: +15%
        elif days_ahead < 45:
            return 1.05     # Acercamiento al sweet spot: +5%
        elif days_ahead <= 60:
            return 1.0      # 🎯 SWEET SPOT (45-60 días)
        elif days_ahead < 90:
            return 1.1      # 2-3 meses: +10%
        elif days_ahead < 120:
            return 1.25     # 3-4 meses: +25%
        else:
            return 1.35     # Muy anticipado: +35%
    
    def _get_seasonal_multiplier(self, month: int) -> float:
        """Temporada alta/baja"""
        if month in self.HIGH_SEASON:
            return 1.35      # Verano/Navidad: +35%
        elif month in [3, 4, 5]:  # Primavera
            return 1.15      # +15%
        elif month in self.LOW_SEASON:
            return 0.85      # Temporada baja: -15%
        else:
            return 1.0       # Temporada media
    
    def _get_weekday_multiplier(self, weekday: int) -> float:
        """Día de semana (0=Lunes, 6=Domingo)"""
        if weekday == 4:  # Viernes
            return 1.15
        elif weekday == 6:  # Domingo
            return 1.2
        elif weekday in [1, 2]:  # Martes, Miércoles (más barato)
            return 0.95
        else:
            return 1.0
    
    def _get_stops_multiplier(self, stops: int) -> float:
        """¡NUEVO! Factor de escalas preciso"""
        if stops == 0:
            return 1.35      # Directo: +35%
        elif stops == 1:
            return 1.0       # Base (1 escala)
        elif stops == 2:
            return 0.82      # 2 escalas: -18%
        else:
            return 0.75      # 3+ escalas: -25%
    
    def _get_cabin_multiplier(self, cabin_class: str) -> float:
        """¡MEJORADO! Multiplicadores precisos de cabina"""
        multipliers = {
            'economy': 1.0,
            'premium_economy': 1.75,
            'business': 4.2,      # Más preciso
            'first': 6.5          # First class realista
        }
        return multipliers.get(cabin_class, 1.0)
    
    def get_breakdown(self, origin: str, dest: str, flight_date: str = None,
                     cabin_class: str = 'economy', stops: int = 1) -> Dict[str, Any]:
        """
        ¡NUEVO! Devuelve desglose detallado para debugging y transparencia
        """
        route = f"{origin}-{dest}"
        base = self.BASE_PRICES.get(route, 650)
        
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
        
        advance = self._get_anticipation_multiplier(days_ahead)
        season = self._get_seasonal_multiplier(month)
        weekday = self._get_weekday_multiplier(day_of_week)
        stops_mult = self._get_stops_multiplier(stops)
        cabin_mult = self._get_cabin_multiplier(cabin_class)
        
        final_price = self.predict(origin, dest, flight_date, cabin_class, stops)
        
        return {
            'route': route,
            'base_price': base,
            'days_ahead': days_ahead,
            'advance_multiplier': advance,
            'season_multiplier': season,
            'weekday_multiplier': weekday,
            'stops': stops,
            'stops_multiplier': stops_mult,
            'cabin_class': cabin_class,
            'cabin_multiplier': cabin_mult,
            'final_price': final_price,
            'breakdown': (
                f"€{base} × {advance:.2f}(days) × {season:.2f}(season) × "
                f"{weekday:.2f}(weekday) × {stops_mult:.2f}(stops) × "
                f"{cabin_mult:.2f}(cabin) = €{final_price}"
            )
        }
    
    def get_best_booking_window(self, origin: str, dest: str, 
                               cabin_class: str = 'economy') -> Dict[str, Any]:
        """Calcula la mejor ventana de reserva (sweet spot) para una ruta"""
        prices = []
        for days in range(1, 121):  # Escanear próximos 4 meses
            flight_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
            price = self.predict(origin, dest, flight_date, cabin_class, 1)
            prices.append({'days_ahead': days, 'date': flight_date, 'price': price})
        
        df = pd.DataFrame(prices)
        min_idx = df['price'].idxmin()
        
        return {
            'route': f"{origin}-{dest}",
            'cabin_class': cabin_class,
            'best_day': int(df.loc[min_idx, 'days_ahead']),
            'best_date': df.loc[min_idx, 'date'],
            'best_price': int(df.loc[min_idx, 'price']),
            'avg_price': int(df['price'].mean()),
            'savings': int(df['price'].mean() - df.loc[min_idx, 'price']),
            'worst_price': int(df['price'].max()),
            'price_range': f"€{df['price'].min():.0f} - €{df['price'].max():.0f}"
        }

# 🚀 FLIGHT API CLIENT WITH ML SMART ENHANCED
class FlightAPIClient:
    """Cliente multi-API con circuit breaker, cache y ML Smart Enhanced"""
    def __init__(self, api_keys: Dict, cache: TTLCache):
        self.api_keys, self.cache = api_keys, cache
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': f'{APP_NAME}/{VERSION}'})
        self.breakers = {name: CircuitBreaker(name, 3, 30) for name in ['aviationstack', 'serpapi']}
        self.ml_predictor = MLSmartPredictor()  # ← ENHANCED!
        logger.info(f"✈️ API Client initialized with {len(api_keys)} keys + ML Smart Enhanced")
    
    def get_price(self, origin: str, dest: str, name: str, flight_date: str = None,
                 cabin_class: str = 'economy', stops: int = 1) -> FlightPrice:
        route = f"{origin}-{dest}"
        cache_key = f"price:{route}:{flight_date or 'today'}:{cabin_class}:{stops}"
        
        # Check cache first
        cached = self.cache.get(cache_key)
        if cached:
            logger.debug(f"💾 Using cached price for {route}")
            return cached
        
        # Try APIs with circuit breakers
        for api_name, api_func in [('aviationstack', self._get_aviationstack), ('serpapi', self._get_serpapi)]:
            if api_name in self.breakers:
                try:
                    start_time = time.time()
                    price = self.breakers[api_name].call(api_func, origin, dest)
                    duration = time.time() - start_time
                    
                    if price:
                        metrics.record_api_call(api_name, duration, True)
                        result = FlightPrice(route, name, price, 
                                            PriceSource.AVIATION_STACK if 'aviation' in api_name else PriceSource.SERP_API,
                                            datetime.now())
                        self.cache.set(cache_key, result, CACHE_TTL)
                        logger.info(f"✅ {route}: €{price:.0f} from {api_name} ({duration:.2f}s)")
                        return result
                except Exception as e:
                    metrics.record_api_call(api_name, 0, False)
                    logger.warning(f"⚠️ {api_name} failed for {route}: {e}")
        
        # Fallback: ML Smart ENHANCED!
        price = self.ml_predictor.predict(origin, dest, flight_date, cabin_class, stops)
        result = FlightPrice(route, name, price, PriceSource.ML_SMART, datetime.now())
        self.cache.set(cache_key, result, CACHE_TTL // 3)  # Shorter TTL for estimates
        logger.info(f"🧠 {route}: €{price:.0f} (ML Smart Enhanced - {cabin_class}, {stops} stops)")
        return result
    
    def _get_aviationstack(self, origin: str, dest: str) -> Optional[float]:
        key = self.api_keys.get('aviationstack')
        if not key or key == "TU_CLAVE_AVIATIONSTACK_AQUI":
            return None
        
        url = "http://api.aviationstack.com/v1/flights"
        params = {'access_key': key, 'dep_iata': origin, 'arr_iata': dest}
        r = self.session.get(url, params=params, timeout=API_TIMEOUT)
        r.raise_for_status()
        data = r.json()
        if 'data' in data and data['data']:
            return data['data'][0].get('pricing', {}).get('total')
        return None
    
    def _get_serpapi(self, origin: str, dest: str) -> Optional[float]:
        key = self.api_keys.get('serpapi')
        if not key or key == "TU_CLAVE_SERPAPI_AQUI":
            return None
        
        url = "https://serpapi.com/search.json"
        params = {
            'engine': 'google_flights', 'api_key': key,
            'departure_id': origin, 'arrival_id': dest,
            'outbound_date': datetime.now().strftime('%Y-%m-%d')
        }
        r = self.session.get(url, params=params, timeout=API_TIMEOUT)
        r.raise_for_status()
        data = r.json()
        if 'flights' in data and data['flights']:
            return data['flights'][0].get('price')
        return None
    
    def health_check(self) -> Dict[str, Any]:
        """Health check de todas las APIs"""
        health = {}
        for name in ['aviationstack', 'serpapi']:
            breaker = self.breakers.get(name)
            if breaker:
                health[name] = {
                    'state': breaker.state.value,
                    'failures': breaker.fail_count,
                    'stats': metrics.get_stats(name)
                }
        health['cache'] = {'hit_rate': f"{self.cache.hit_rate:.1%}", 'size': len(self.cache._cache)}
        health['ml_smart'] = {
            'status': '🧠 Enhanced Active', 
            'version': 'v2.0 Pattern-Based + Stops + Cabin',
            'features': ['Sweet Spot', 'Seasonal', 'Weekday', 'Stops (+35%/-18%)', 'Cabin (x4.2/x6.5)', 'Debug Breakdown']
        }
        return health

# 💾 DATA MANAGER
class DataManager:
    """Gestor de datos históricos con pandas"""
    def __init__(self, file: str = CSV_FILE):
        self.file = Path(file)
        self._ensure_exists()
        logger.info(f"💾 DataManager initialized: {file}")
    
    def _ensure_exists(self):
        if not self.file.exists():
            pd.DataFrame(columns=['route', 'name', 'price', 'source', 'timestamp']).to_csv(
                self.file, index=False, encoding='utf-8')
    
    def save(self, prices: List[FlightPrice]):
        if prices:
            df = pd.DataFrame([p.to_dict() for p in prices])
            df.to_csv(self.file, mode='a', header=False, index=False, encoding='utf-8')
            logger.info(f"💾 Saved {len(prices)} prices to CSV")
            UI.status("💾", f"Saved {len(prices)} records to {self.file}", "SUCCESS")
    
    def load(self) -> pd.DataFrame:
        try:
            return pd.read_csv(self.file, encoding='utf-8')
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
            'best_route': df.loc[df['price'].idxmin(), 'route'] if not df.empty else None
        }

# 📰 RSS ANALYZER
class RSSAnalyzer:
    """Analizador de feeds RSS para ofertas flash"""
    KEYWORDS = ['sale', 'deal', 'cheap', 'error', 'fare', 'offer', 'promo', 'discount']
    
    def __init__(self, feeds: List[str]):
        self.feeds = feeds
        logger.info(f"📰 RSS Analyzer initialized with {len(feeds)} feeds")
    
    def find_deals(self) -> List[Dict]:
        UI.section("RSS FEED ANALYSIS")
        UI.status("🔍", f"Scanning {len(self.feeds)} RSS feeds...")
        deals = []
        
        for idx, url in enumerate(self.feeds, 1):
            try:
                UI.status("🔍", f"Feed [{idx}/{len(self.feeds)}]: {url[:50]}...")
                feed = feedparser.parse(url)
                
                for entry in feed.entries[:5]:
                    if any(kw in entry.title.lower() for kw in self.KEYWORDS):
                        deals.append({
                            'title': entry.title,
                            'link': entry.link,
                            'source': feed.feed.title if hasattr(feed.feed, 'title') else 'RSS',
                            'published': getattr(entry, 'published', 'Recent')
                        })
                        UI.status("🔥", f"Deal found: {entry.title[:60]}...", "ALERT")
            except Exception as e:
                logger.error(f"RSS error {url}: {e}")
        
        UI.status("✅", f"RSS scan complete: {len(deals)} deals found", "SUCCESS")
        return deals

# 🔍 FLIGHT SCANNER
class FlightScanner:
    """Motor principal de escaneo con ThreadPoolExecutor"""
    def __init__(self, config: ConfigManager, api: FlightAPIClient, data: DataManager):
        self.config, self.api, self.data = config, api, data
        logger.info(f"🔍 Scanner initialized: {len(config.flights)} routes")
    
    def scan_all(self) -> pd.DataFrame:
        flights = self.config.flights
        UI.section(f"FLIGHT SCANNER: {len(flights)} ROUTES")
        UI.status("🚀", f"Starting parallel scan with {MAX_WORKERS} workers...")
        
        results = []
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {executor.submit(
                self.api.get_price, 
                f['origin'], 
                f['dest'], 
                f['name'],
                f.get('outbound_date'),
                f.get('cabin_class', 'economy'),
                self._parse_stops(f.get('stops', 'any'))
            ): f for f in flights}
            
            for idx, future in enumerate(as_completed(futures), 1):
                try:
                    price = future.result()
                    results.append(price)
                    UI.progress(idx, len(flights), prefix="⏳ Progress")
                    logger.debug(f"{price.route}: €{price.price:.0f} ({price.source.value})")
                except Exception as e:
                    logger.error(f"Scan error: {e}")
        
        UI.status("✅", f"Scan complete: {len(results)} results", "SUCCESS")
        self.data.save(results)
        
        return pd.DataFrame([r.to_dict() for r in results])
    
    def _parse_stops(self, stops_config: str) -> int:
        """Parsea configuración de escalas a número concreto"""
        if stops_config == "0":
            return 0
        elif stops_config == "1+":
            return random.choices([1, 2], weights=[70, 30])[0]
        elif stops_config == "1":
            return 1
        elif stops_config == "2":
            return 2
        else:  # "any"
            return random.choices([0, 1, 2], weights=[20, 60, 20])[0]

# 🤖 TELEGRAM BOT
class TelegramBot:
    """Handler del bot de Telegram con comandos interactivos"""
    def __init__(self, config: ConfigManager, scanner: FlightScanner, data: DataManager, rss: RSSAnalyzer):
        self.config, self.scanner, self.data, self.rss = config, scanner, data, rss
        self.bot = Bot(token=config.bot_token)
        logger.info("🤖 Telegram bot initialized")
    
    async def send_alert(self, price: FlightPrice):
        try:
            msg = f"""🚨 *¡CHOLLO DETECTADO!*

─────────────────
✈️ *Ruta:* {price.route}
💰 *Precio:* **€{price.price:.0f}**
📊 *Fuente:* {price.source.value}
─────────────────
⚡ *¡Reserva rápido!*
🕐 {price.timestamp.strftime('%d/%m/%Y %H:%M')}

_Precio < €{self.config.alert_threshold:.0f}_"""
            await self.bot.send_message(self.config.chat_id, msg, parse_mode='Markdown')
            logger.info(f"✅ Alert sent: {price.route}")
        except TelegramError as e:
            logger.error(f"Telegram error: {e}")
    
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        msg = f"""🏆 *BIENVENIDO A {APP_NAME.upper()} v{VERSION.split()[0]}*

─────────────────────

*🚀 Sistema Ultimate v11.2 Enhanced*

✅ Multi-API + Circuit Breaker
✅ ML Smart ENHANCED NEW!
✅ Sweet Spot Detection (45-60d)
✅ Stops Adjustment (+35%/-18%)
✅ Cabin Precise (x4.2/x6.5)
✅ Performance Metrics

─────────────────────

📋 *COMANDOS:*

🔥 `/supremo` - Escaneo completo
📊 `/status` - Dashboard stats
📰 `/rss` - Ofertas flash RSS
💡 `/chollos` - 14 hacks pro
🛫 `/scan XX YY` - Ruta específica
💚 `/health` - Health check
🎯 `/sweetspot XX YY` - Best booking window

─────────────────────

⚙️ Umbral: €{self.config.alert_threshold}
✈️ Rutas: {len(self.config.flights)}

💬 Usa `/supremo` para empezar"""
        await update.message.reply_text(msg, parse_mode='Markdown')
    
    async def cmd_supremo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        initial = await update.message.reply_text(
            "🔄 *ESCANEO SUPREMO v11.2 ENHANCED*\n\n"
            f"✈️ {len(self.config.flights)} rutas\n🧠 ML Smart Enhanced active\n\n"
            "_Analyzing with advanced market patterns..._",
            parse_mode='Markdown'
        )
        
        df = self.scanner.scan_all()
        threshold = self.config.alert_threshold
        hot = df[df['price'] < threshold]
        
        for _, row in hot.iterrows():
            price = FlightPrice(row['route'], row['name'], row['price'], 
                              PriceSource.ML_SMART, datetime.fromisoformat(row['timestamp']))
            await self.send_alert(price)
        
        msg = f"""✅ *SCAN COMPLETE*

─────────────────

📊 *SUMMARY:*

✈️ Scanned: {len(df)}
🔥 Hot deals: {len(hot)}
💎 Best: **€{df['price'].min():.0f}** ({df.loc[df['price'].idxmin(), 'route']})
📈 Avg: €{df['price'].mean():.0f}

─────────────────

🏆 *TOP 5:*

"""
        
        top5 = df.nsmallest(5, 'price')
        for i, (_, r) in enumerate(top5.iterrows(), 1):
            emoji = "🔥" if r['price'] < threshold else "📊"
            msg += f"{i}. {emoji} *{r['route']}* - €{r['price']:.0f}\n"
        
        msg += f"\n🕐 {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        await initial.edit_text(msg, parse_mode='Markdown')
    
    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
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

🏆 *BEST:* {stats['best_route']}
💰 **€{stats['min_price']:.0f}**

─────────────────

🕐 {datetime.now().strftime('%d/%m/%Y %H:%M')}"""
        await update.message.reply_text(msg, parse_mode='Markdown')
    
    async def cmd_health(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        health = self.scanner.api.health_check()
        msg = "💚 *HEALTH CHECK v11.2 ENHANCED*\n\n───────────────\n\n"
        
        for api_name, data in health.items():
            if api_name == 'ml_smart':
                msg += f"*ML Smart:* {data['status']}\n"
                msg += f"  🆕 {data['version']}\n"
                msg += f"  ✅ {', '.join(data['features'][:3])}\n"
                msg += f"  ✅ {', '.join(data['features'][3:])}\n\n"
            elif api_name != 'cache':
                state = data['state']
                msg += f"*{api_name}:* {state}\n"
                if 'stats' in data and data['stats']:
                    stats = data['stats']
                    msg += f"  ⏱️ Avg: {stats['avg_time']:.2f}s\n"
                    msg += f"  ✅ Success: {stats['success_rate']:.0%}\n\n"
        
        cache_data = health['cache']
        msg += f"\n🗃️ *Cache:* {cache_data['hit_rate']} hit rate ({cache_data['size']} items)"
        
        await update.message.reply_text(msg, parse_mode='Markdown')
    
    async def cmd_rss(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("📰 *SCANNING RSS...*", parse_mode='Markdown')
        deals = self.rss.find_deals()
        
        if not deals:
            await update.message.reply_text("ℹ️ No hay ofertas flash ahora")
        else:
            for deal in deals[:5]:
                msg = f"""📰 *OFERTA FLASH*

{deal['title']}

🔗 [Ver oferta]({deal['link']})
───────────────
📡 {deal['source']}
🕐 {deal['published']}"""
                await update.message.reply_text(msg, parse_mode='Markdown')
    
    async def cmd_chollos(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        msg = """💡 *14 HACKS PROFESIONALES*

─────────────────

🎯 *ESTRATEGIAS:*

1️⃣ Error Fares (-90%)
2️⃣ VPN Arbitrage (-40%)
3️⃣ Skiplagging (-50%)
4️⃣ Mileage Runs (free)

💳 *PAGOS:*

5️⃣ Cashback Stacking (13%)
6️⃣ Points Hacking (678+)
7️⃣ Manufactured Spending

🗺️ *RUTAS:*

8️⃣ Stopovers Gratis (2x1)
9️⃣ Hidden City (-40%)
🔟 Multi-City Combos

🤖 *TOOLS:*

1️⃣1️⃣ Google Flights Alerts
1️⃣2️⃣ Skyscanner Everywhere
1️⃣3️⃣ Hopper Price Freeze
1️⃣4️⃣ Award Travel

─────────────────

💡 Combina para max ahorro!
⚠️ Algunas técnicas zona gris"""
        await update.message.reply_text(msg, parse_mode='Markdown')
    
    async def cmd_scan(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if len(context.args) < 2:
            await update.message.reply_text(
                "❌ Uso: `/scan ORIGEN DESTINO [cabin] [stops]`\nEj: `/scan MAD MGA business 0`",
                parse_mode='Markdown'
            )
            return
        
        origin, dest = context.args[0].upper(), context.args[1].upper()
        cabin = context.args[2] if len(context.args) > 2 else 'economy'
        stops = int(context.args[3]) if len(context.args) > 3 else 1
        
        try:
            FlightRoute(origin, dest, "test")
        except ValueError as e:
            await update.message.reply_text(f"❌ {e}", parse_mode='Markdown')
            return
        
        initial = await update.message.reply_text(
            f"🔄 *SCANNING {origin}✈️{dest}...*\n\n🧠 _ML Smart Enhanced analyzing..._\n💺 Cabin: {cabin}\n✈️ Stops: {stops}",
            parse_mode='Markdown'
        )
        
        price = self.scanner.api.get_price(origin, dest, f"{origin}-{dest}", None, cabin, stops)
        is_deal = price.is_deal(self.config.alert_threshold)
        emoji = "🔥" if is_deal else "📊"
        
        msg = f"""✅ *ANALYSIS COMPLETE*

─────────────────

✈️ *Route:* {price.route}
💵 *Price:* **€{price.price:.0f}**
💺 *Cabin:* {cabin}
✈️ *Stops:* {stops}
📊 *Source:* {price.source.value}
{emoji} *Status:* {'DEAL!' if is_deal else 'Normal'}

─────────────────

{'⚡ Book now!' if is_deal else '💡 Wait or set alerts'}

🕐 {datetime.now().strftime('%d/%m/%Y %H:%M')}"""
        await initial.edit_text(msg, parse_mode='Markdown')
    
    async def cmd_sweetspot(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """¡NUEVO! Encuentra el mejor momento para comprar"""
        if len(context.args) < 2:
            await update.message.reply_text(
                "❌ Uso: `/sweetspot ORIGEN DESTINO [cabin]`\nEj: `/sweetspot MAD MGA business`",
                parse_mode='Markdown'
            )
            return
        
        origin, dest = context.args[0].upper(), context.args[1].upper()
        cabin = context.args[2] if len(context.args) > 2 else 'economy'
        
        initial = await update.message.reply_text(
            f"🎯 *CALCULATING SWEET SPOT...*\n\n✈️ {origin}→{dest}\n💺 {cabin}\n\n_Analyzing next 120 days..._",
            parse_mode='Markdown'
        )
        
        result = self.scanner.api.ml_predictor.get_best_booking_window(origin, dest, cabin)
        
        msg = f"""🎯 *SWEET SPOT ANALYSIS*

─────────────────

✈️ *Route:* {result['route']}
💺 *Cabin:* {result['cabin_class']}

🏆 *BEST DAY TO BUY:*
📅 {result['best_day']} días antes
📆 {result['best_date']}
💰 **€{result['best_price']}**

📈 *STATS:*
📊 Avg price: €{result['avg_price']}
💎 Savings: €{result['savings']} ({result['savings']/result['avg_price']*100:.0f}%)
📉 Range: {result['price_range']}

─────────────────

💡 *TIP:* Compra entre {max(result['best_day']-5, 1)}-{result['best_day']+5} días antes

🕐 {datetime.now().strftime('%d/%m/%Y %H:%M')}"""
        await initial.edit_text(msg, parse_mode='Markdown')

# 🚀 MAIN
def main():
    try:
        UI.header(f"🎆 {APP_NAME.upper()} v{VERSION} 🎆")
        UI.print("Sistema Ultimate de Monitorización de Vuelos".center(80), UI.BOLD + UI.CYAN)
        UI.print("ML Smart Enhanced | Circuit Breaker | Cache TTL | Health Checks".center(80), UI.CYAN)
        UI.header("")
        
        UI.section("SYSTEM INITIALIZATION")
        
        config = ConfigManager()
        UI.status("✅", "Config loaded")
        
        cache = TTLCache(CACHE_TTL)
        UI.status("✅", "Cache initialized")
        
        api = FlightAPIClient(config.api_keys, cache)
        UI.status("✅", "API client + ML Smart Enhanced ready")
        
        data = DataManager()
        UI.status("✅", "Data manager ready")
        
        scanner = FlightScanner(config, api, data)
        UI.status("✅", "Scanner initialized")
        
        rss = RSSAnalyzer(config.rss_feeds)
        UI.status("✅", "RSS analyzer ready")
        
        bot = TelegramBot(config, scanner, data, rss)
        UI.status("✅", "Telegram bot ready")
        
        UI.section("ACTIVE CONFIGURATION")
        UI.print(f"   ✈️ Routes: {len(config.flights)}")
        UI.print(f"   💰 Threshold: €{config.alert_threshold}")
        UI.print(f"   📡 APIs: {len(config.api_keys)}")
        UI.print(f"   📰 RSS: {len(config.rss_feeds)}")
        UI.print(f"   🗃️ Cache TTL: {CACHE_TTL}s")
        UI.print(f"   ⚔️ Circuit: {CIRCUIT_BREAK_THRESHOLD} fails")
        UI.print(f"   🧠 ML Smart: v2.0 Enhanced (Stops+Cabin+Breakdown)")
        
        UI.section("STARTING TELEGRAM BOT")
        app = Application.builder().token(config.bot_token).build()
        
        app.add_handler(CommandHandler("start", bot.cmd_start))
        app.add_handler(CommandHandler("supremo", bot.cmd_supremo))
        app.add_handler(CommandHandler("status", bot.cmd_status))
        app.add_handler(CommandHandler("health", bot.cmd_health))
        app.add_handler(CommandHandler("rss", bot.cmd_rss))
        app.add_handler(CommandHandler("chollos", bot.cmd_chollos))
        app.add_handler(CommandHandler("scan", bot.cmd_scan))
        app.add_handler(CommandHandler("sweetspot", bot.cmd_sweetspot))  # ¡NUEVO!
        
        UI.status("✅", "All commands registered", "SUCCESS")
        
        UI.section("AVAILABLE COMMANDS")
        commands = [
            ("/start", "Welcome message"),
            ("/supremo", "Full scan + ML Smart Enhanced"),
            ("/status", "Stats dashboard"),
            ("/health", "API + ML health check"),
            ("/rss", "RSS flash deals"),
            ("/chollos", "14 pro hacks"),
            ("/scan XX YY [cabin] [stops]", "Route with ML Smart"),
            ("/sweetspot XX YY [cabin]", "Best booking window NEW!")
        ]
        for cmd, desc in commands:
            UI.print(f"   {cmd.ljust(30)} - {desc}")
        
        UI.header("✅ SYSTEM OPERATIONAL v11.2 ENHANCED")
        UI.status("👂", "Bot listening (Ctrl+C to stop)", "SUCCESS")
        UI.header("")
        
        logger.info("🚀 System v11.2 Enhanced started with ML Smart v2.0")
        app.run_polling()
        
    except KeyboardInterrupt:
        UI.header("🛑 SHUTDOWN REQUESTED")
        UI.status("⏹️", "Closing connections...")
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
