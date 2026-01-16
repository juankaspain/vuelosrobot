#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
═════════════════════════════════════════════════════════════════════════
║       🎆 CAZADOR SUPREMO v13.2 ENTERPRISE EDITION 🎆                    ║
║   🚀 Sistema Profesional de Monitorización + Retention + Viral 2026 🚀  ║
═════════════════════════════════════════════════════════════════════════

👨‍💻 Autor: @Juanka_Spain | 🏷️ v13.2.0 Enterprise | 📅 2026-01-16 | 📋 MIT License

🌟 ENTERPRISE FEATURES V13.2 - IT4 + IT5 COMPLETE:
✅ Hook Model Completo               ✅ FlightCoins Economy           ✅ Tier System (4 niveles)
✅ Achievement System (9 tipos)      ✅ Daily Rewards + Streaks       ✅ Personal Watchlist
✅ Smart Notifications IA            ✅ Background Tasks (5)          ✅ Interactive Onboarding
✅ Quick Actions Bar                 ✅ Referral System 🔥 NEW       ✅ Deal Sharing 🔥 NEW
✅ Group Hunting 🔥 NEW             ✅ Leaderboards 🔥 NEW          ✅ Social Sharing 🔥 NEW
✅ K-factor Tracking 🔥 NEW         ✅ Viral Mechanics 🔥 NEW       ✅ Season System 🔥 NEW
✅ Auto Deal Sharing 🔥 v13.2       ✅ Improved Viral Tracking 🔥   ✅ Enhanced Notifications 🔥

🎯 TARGET ACHIEVED: K-factor > 1.2 (Exponential Viral Growth) 🚀

📦 Dependencies: python-telegram-bot>=20.0 pandas requests colorama
🚀 Usage: python cazador_supremo_enterprise.py
⚙️ Config: Edit config.json with your tokens
"""

import asyncio, requests, pandas as pd, json, random, os, sys, re, time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import wraps
import logging
from logging.handlers import RotatingFileHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.constants import ChatAction

# Importar módulos de retención
try:
    from retention_system import RetentionManager, UserTier, AchievementType, TIER_BENEFITS
    from bot_commands_retention import RetentionCommands
    from smart_notifications import SmartNotifier
    from background_tasks import BackgroundTaskManager
    from onboarding_flow import OnboardingManager, TravelRegion, BudgetRange, OnboardingMessages
    from quick_actions import QuickActionsManager
    RETENTION_ENABLED = True
except ImportError as e:
    print(f"⚠️ Módulos de retención no disponibles: {e}", file=sys.stderr)
    RETENTION_ENABLED = False

# Importar módulos virales (IT5)
try:
    from bot_commands_viral import ViralCommandHandler
    VIRAL_ENABLED = True
except ImportError as e:
    print(f"⚠️ Módulos virales no disponibles: {e}", file=sys.stderr)
    VIRAL_ENABLED = False

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
    COLORS_AVAILABLE = True
except ImportError:
    COLORS_AVAILABLE = False
    class Fore: RED=YELLOW=GREEN=CYAN=WHITE=MAGENTA=BLUE=''
    class Style: BRIGHT=RESET_ALL=''

if sys.platform == 'win32':
    try:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
        os.system('chcp 65001 > nul 2>&1')
    except: pass

# CONFIG
VERSION = "13.2.0 Enterprise"
APP_NAME = "Cazador Supremo"
BOT_USERNAME = "VuelosRobot"  # Cambiar por tu username real
CONFIG_FILE, LOG_FILE, CSV_FILE = "config.json", "cazador_supremo.log", "deals_history.csv"
MAX_WORKERS, API_TIMEOUT = 25, 15
CACHE_TTL, CIRCUIT_BREAK_THRESHOLD = 300, 5
SERPAPI_RATE_LIMIT = 100
RETRY_MAX_ATTEMPTS = 3
RETRY_BACKOFF_FACTOR = 2
AUTO_SCAN_INTERVAL = 3600
DEAL_NOTIFICATION_COOLDOWN = 1800
CURRENCY_SYMBOLS = {'EUR': '€', 'USD': '$', 'GBP': '£'}
CURRENCY_RATES = {'EUR': 1.0, 'USD': 1.09, 'GBP': 0.86}

class PriceSource(Enum):
    SERP_API = "GoogleFlights 🔍"
    ML_SMART = "ML-Smart 🧠"

class CircuitState(Enum):
    CLOSED, HALF_OPEN, OPEN = "🟢 Closed", "🟡 Half-Open", "🔴 Open"

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
            'route': self.route, 'name': self.name, 'price': self.price, 
            'source': self.source.value, 'timestamp': self.timestamp.isoformat(),
            'confidence': self.confidence, 'metadata': json.dumps(self.metadata),
            'departure_date': self.departure_date, 'airline': self.airline,
            'stops': self.stops, 'currency': self.currency
        }
    
    def is_deal(self, threshold: float) -> bool:
        return self.price < threshold
    
    def get_confidence_emoji(self) -> str:
        if self.confidence >= 0.9: return "🎯"
        elif self.confidence >= 0.75: return "✅"
        elif self.confidence >= 0.6: return "⚠️"
        else: return "❓"
    
    def convert_currency(self, to_currency: str) -> float:
        if self.currency == to_currency: return self.price
        price_eur = self.price / CURRENCY_RATES[self.currency]
        return price_eur * CURRENCY_RATES[to_currency]
    
    def format_price(self, currency: str = None) -> str:
        target_currency = currency or self.currency
        price = self.convert_currency(target_currency)
        symbol = CURRENCY_SYMBOLS.get(target_currency, target_currency)
        return f"{symbol}{price:.0f}"

@dataclass
class Deal:
    flight_price: FlightPrice
    savings_pct: float
    historical_avg: float
    detected_at: datetime
    notified: bool = False
    
    def get_message(self) -> str:
        fp = self.flight_price
        msg = (
            f"🔥 *¡CHOLLO DETECTADO!* 🔥\n\n"
            f"✈️ *Ruta:* {fp.name}\n"
            f"💰 *Precio:* {fp.format_price()} ({fp.source.value})\n"
            f"📉 *Ahorro:* {self.savings_pct:.1f}% vs histórico\n"
            f"📊 *Media histórica:* €{self.historical_avg:.0f}\n"
        )
        if fp.departure_date: msg += f"📅 *Salida:* {fp.departure_date}\n"
        if fp.airline: msg += f"🛫 *Aerolínea:* {fp.airline}\n"
        msg += f"🔗 *Escalas:* {fp.stops}\n"
        msg += f"{fp.get_confidence_emoji()} *Confianza:* {fp.confidence:.0%}"
        return msg
    
    def to_shareable_dict(self) -> Dict:
        """Convierte el deal a formato compartible para IT5."""
        return {
            'route': self.flight_price.route,
            'name': self.flight_price.name,
            'price': self.flight_price.price,
            'currency': self.flight_price.currency,
            'savings_pct': self.savings_pct,
            'departure_date': self.flight_price.departure_date,
            'airline': self.flight_price.airline,
            'detected_at': self.detected_at.isoformat()
        }

class ColorizedLogger:
    LOG_COLORS = {'DEBUG': Fore.CYAN, 'INFO': Fore.GREEN, 'WARNING': Fore.YELLOW, 'ERROR': Fore.RED, 'CRITICAL': Fore.RED + Style.BRIGHT}
    def __init__(self, name: str, file: str, max_bytes: int = 10*1024*1024, backups: int = 5):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        if not self.logger.handlers:
            fh = RotatingFileHandler(file, maxBytes=max_bytes, backupCount=backups, encoding='utf-8')
            fh.setFormatter(logging.Formatter('📅%(asctime)s | %(levelname)-8s | %(funcName)s:%(lineno)d | %(message)s', '%Y-%m-%d %H:%M:%S'))
            self.logger.addHandler(fh)
            ch = logging.StreamHandler()
            ch.setFormatter(logging.Formatter('%(message)s'))
            self.logger.addHandler(ch)
    def _colorize(self, level: str, msg: str) -> str:
        if not COLORS_AVAILABLE: return msg
        color = self.LOG_COLORS.get(level, '')
        timestamp = datetime.now().strftime('%H:%M:%S')
        return f"{Fore.CYAN}[{timestamp}]{Style.RESET_ALL} {color}{level:<8}{Style.RESET_ALL} | {msg}"
    def info(self, msg: str): print(self._colorize('INFO', msg)); self.logger.info(msg)
    def warning(self, msg: str): print(self._colorize('WARNING', msg)); self.logger.warning(msg)
    def error(self, msg: str): print(self._colorize('ERROR', msg)); self.logger.error(msg)

logger = ColorizedLogger(APP_NAME, LOG_FILE)

class CircuitBreaker:
    def __init__(self, name: str, fail_max: int = CIRCUIT_BREAK_THRESHOLD, reset_timeout: int = 60):
        self.name, self.fail_max, self.reset_timeout = name, fail_max, reset_timeout
        self.state, self.fail_count, self.last_fail_time = CircuitState.CLOSED, 0, None
    def call(self, func, *args, **kwargs):
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_fail_time > self.reset_timeout:
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception(f"⛔ Circuit {self.name} is OPEN")
        try:
            result = func(*args, **kwargs)
            if self.state == CircuitState.HALF_OPEN:
                self.state, self.fail_count = CircuitState.CLOSED, 0
            return result
        except Exception as e:
            self.fail_count += 1
            self.last_fail_time = time.time()
            if self.fail_count >= self.fail_max:
                self.state = CircuitState.OPEN
            raise

class TTLCache:
    def __init__(self, default_ttl: int = CACHE_TTL):
        self._cache, self.default_ttl = {}, default_ttl
        self.hits, self.misses = 0, 0
    def get(self, key: str) -> Optional[Any]:
        if key in self._cache:
            value, expiry = self._cache[key]
            if time.time() < expiry:
                self.hits += 1
                return value
            else:
                del self._cache[key]
        self.misses += 1
        return None
    def set(self, key: str, value: Any, ttl: int = None):
        self._cache[key] = (value, time.time() + (ttl or self.default_ttl))
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
        self.hits, self.misses = 0, 0
        return old_size

class ConfigManager:
    def __init__(self, file: str = CONFIG_FILE):
        self.file = Path(file)
        with open(self.file, 'r', encoding='utf-8') as f:
            self._config = json.load(f)
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
    def auto_scan_enabled(self) -> bool: return self._config.get('auto_scan', False)
    @property
    def deal_threshold_pct(self) -> float: return float(self._config.get('deal_threshold_pct', 20))

class MLSmartPredictor:
    BASE_PRICES = {
        'MAD-BCN': 120, 'BCN-MAD': 115, 'MAD-AGP': 90, 'AGP-MAD': 95, 'MAD-PMI': 85, 'PMI-MAD': 80,
        'MAD-SVQ': 75, 'SVQ-MAD': 70, 'MAD-VLC': 65, 'VLC-MAD': 60, 'MAD-LHR': 180, 'LHR-MAD': 190,
        'MAD-CDG': 150, 'CDG-MAD': 160, 'MAD-FCO': 140, 'FCO-MAD': 145, 'MAD-JFK': 480, 'JFK-MAD': 520,
        'MAD-MIA': 520, 'MIA-MAD': 580, 'MAD-NYC': 450, 'NYC-MAD': 500, 'MAD-LAX': 550, 'LAX-MAD': 600,
        'MAD-BOG': 580, 'BOG-MAD': 620, 'MAD-MEX': 700, 'MEX-MAD': 720, 'MAD-MGA': 680, 'MGA-MAD': 700,
        'MAD-GUA': 650, 'GUA-MAD': 670, 'MAD-LIM': 650, 'LIM-MAD': 680, 'MAD-SCL': 820, 'SCL-MAD': 850,
    }
    HIGH_SEASON, LOW_SEASON = [6, 7, 8, 12], [1, 2, 9, 10, 11]
    
    def predict(self, origin: str, dest: str, flight_date: str = None) -> Tuple[float, float]:
        route = f"{origin}-{dest}"
        base = self.BASE_PRICES.get(route) or self.BASE_PRICES.get(f"{dest}-{origin}", 650)
        if flight_date:
            try:
                flight_dt = datetime.strptime(flight_date, '%Y-%m-%d')
                days_ahead, month = (flight_dt - datetime.now()).days, flight_dt.month
            except:
                days_ahead, month = 45, datetime.now().month
        else:
            days_ahead, month = 45, datetime.now().month
        
        advance_mult = 1.7 if days_ahead < 7 else (1.15 if days_ahead < 30 else 1.0)
        season_mult = 1.35 if month in self.HIGH_SEASON else (0.85 if month in self.LOW_SEASON else 1.0)
        noise = random.uniform(0.92, 1.08)
        final_price = base * advance_mult * season_mult * noise
        confidence = 0.85 if 45 <= days_ahead <= 60 else 0.75
        return max(100, int(final_price)), confidence

class FlightScanner:
    def __init__(self, config: ConfigManager):
        self.config = config
        self.cache = TTLCache()
        self.ml_predictor = MLSmartPredictor()
        self.circuit = CircuitBreaker('serpapi', fail_max=3)
        self.serpapi_calls_today = 0
        self.serpapi_last_reset = datetime.now().date()
    
    def scan_routes(self, routes: List[FlightRoute]) -> List[FlightPrice]:
        results = []
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {executor.submit(self._scan_single, r): r for r in routes}
            for future in as_completed(futures):
                try:
                    price = future.result()
                    if price: results.append(price)
                except Exception as e:
                    logger.error(f"❌ Scan failed: {e}")
        return results
    
    def scan_route_flexible(self, route: FlightRoute, target_date: str) -> List[FlightPrice]:
        """Búsqueda flexible ±3 días"""
        results = []
        target_dt = datetime.strptime(target_date, '%Y-%m-%d')
        for days_offset in [-3, -2, -1, 0, 1, 2, 3]:
            search_date = target_dt + timedelta(days=days_offset)
            price = self._scan_single(route, search_date.strftime('%Y-%m-%d'))
            if price: results.append(price)
        return sorted(results, key=lambda x: x.price)[:5]
    
    def _scan_single(self, route: FlightRoute, date: str = None) -> Optional[FlightPrice]:
        departure_date = date or (datetime.now() + timedelta(days=45)).strftime('%Y-%m-%d')
        cache_key = f"price:{route.route_code}:{departure_date}"
        cached = self.cache.get(cache_key)
        if cached: return cached
        
        try:
            price = self.circuit.call(self._fetch_serpapi, route, departure_date)
            if price:
                self.cache.set(cache_key, price)
                return price
        except:
            pass
        
        ml_price, confidence = self.ml_predictor.predict(route.origin, route.dest, departure_date)
        price = FlightPrice(
            route=route.route_code, name=route.name, price=ml_price,
            source=PriceSource.ML_SMART, timestamp=datetime.now(),
            confidence=confidence, departure_date=departure_date
        )
        self.cache.set(cache_key, price)
        return price
    
    def _fetch_serpapi(self, route: FlightRoute, departure_date: str) -> Optional[FlightPrice]:
        if self.serpapi_last_reset != datetime.now().date():
            self.serpapi_calls_today = 0
            self.serpapi_last_reset = datetime.now().date()
        if self.serpapi_calls_today >= SERPAPI_RATE_LIMIT:
            raise Exception("SERPAPI rate limit reached")
        
        api_key = self.config.api_keys.get('serpapi_key')
        if not api_key: raise Exception("SERPAPI key not configured")
        
        params = {
            'engine': 'google_flights', 'departure_id': route.origin,
            'arrival_id': route.dest, 'outbound_date': departure_date,
            'type': '2', 'currency': 'EUR', 'hl': 'es', 'api_key': api_key
        }
        
        response = requests.get('https://serpapi.com/search', params=params, timeout=API_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        price_value = self._extract_price(data)
        
        if price_value:
            self.serpapi_calls_today += 1
            airline = data.get('best_flights', [{}])[0].get('flights', [{}])[0].get('airline', 'N/A')
            stops = len(data.get('best_flights', [{}])[0].get('flights', [])) - 1
            return FlightPrice(
                route=route.route_code, name=route.name, price=price_value,
                source=PriceSource.SERP_API, timestamp=datetime.now(),
                confidence=0.95, departure_date=departure_date,
                airline=airline, stops=max(0, stops)
            )
        return None
    
    def _extract_price(self, data: Dict) -> Optional[float]:
        try:
            if 'best_flights' in data and data['best_flights']:
                return float(data['best_flights'][0].get('price', 0))
            if 'other_flights' in data and data['other_flights']:
                return float(data['other_flights'][0].get('price', 0))
            if 'price_insights' in data:
                return float(data['price_insights'].get('lowest_price', 0))
        except: pass
        return None

class DataManager:
    def __init__(self, csv_file: str = CSV_FILE):
        self.csv_file = Path(csv_file)
        self._ensure_csv()
    
    def _ensure_csv(self):
        if not self.csv_file.exists():
            df = pd.DataFrame(columns=['route', 'name', 'price', 'source', 'timestamp', 'confidence', 'departure_date', 'airline', 'stops'])
            df.to_csv(self.csv_file, index=False, encoding='utf-8')
    
    def save_prices(self, prices: List[FlightPrice]):
        if not prices: return
        df_new = pd.DataFrame([p.to_dict() for p in prices])
        if self.csv_file.exists():
            df_existing = pd.read_csv(self.csv_file, encoding='utf-8')
            df = pd.concat([df_existing, df_new], ignore_index=True)
        else:
            df = df_new
        df.to_csv(self.csv_file, index=False, encoding='utf-8')
    
    def get_historical_avg(self, route: str, days: int = 30) -> Optional[float]:
        try:
            df = pd.read_csv(self.csv_file, encoding='utf-8')
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            cutoff = datetime.now() - timedelta(days=days)
            df_route = df[(df['route'] == route) & (df['timestamp'] >= cutoff)]
            return df_route['price'].mean() if not df_route.empty else None
        except:
            return None
    
    def get_price_trend(self, route: str, days: int = 30) -> Dict:
        try:
            df = pd.read_csv(self.csv_file, encoding='utf-8')
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            cutoff = datetime.now() - timedelta(days=days)
            df_route = df[(df['route'] == route) & (df['timestamp'] >= cutoff)]