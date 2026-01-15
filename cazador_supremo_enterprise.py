#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
═════════════════════════════════════════════════════════════════════════════
║       🎆 CAZADOR SUPREMO v13.0 ENTERPRISE EDITION 🎆                    ║
║   🚀 Sistema Profesional de Monitorización de Vuelos + Retention 2026 🚀║
═════════════════════════════════════════════════════════════════════════════

👨‍💻 Autor: @Juanka_Spain | 🏷️ v13.0.0 Enterprise | 📅 2026-01-15 | 📋 MIT License

🌟 ENTERPRISE FEATURES V13.0 - IT4 RETENTION COMPLETE:
✅ Hook Model Completo               ✅ FlightCoins Economy           ✅ Tier System (4 niveles)
✅ Achievement System (9 tipos)      ✅ Daily Rewards + Streaks       ✅ Personal Watchlist
✅ Smart Notifications IA            ✅ Background Tasks (5)          ✅ Interactive Onboarding
✅ Quick Actions Bar                 ✅ /daily command               ✅ /watchlist command
✅ /profile command                  ✅ Auto-Scan Scheduler          ✅ Deals Detection
✅ Trends Analysis                   ✅ Multi-Currency EUR/USD/GBP   ✅ SerpAPI Real Integration

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
    from bot_commands_retention import RetentionCommandHandler
    from smart_notifications import SmartNotifier
    from background_tasks import BackgroundTaskManager
    from onboarding_flow import OnboardingManager
    from quick_actions import QuickActionsManager
    RETENTION_ENABLED = True
except ImportError as e:
    print(f"⚠️ Módulos de retención no disponibles: {e}")
    RETENTION_ENABLED = False

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
VERSION = "13.0.0 Enterprise"
APP_NAME = "Cazador Supremo"
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
            if df_route.empty: return None
            return {
                'avg': df_route['price'].mean(),
                'min': df_route['price'].min(),
                'max': df_route['price'].max(),
                'count': len(df_route),
                'trend': 'down' if df_route['price'].iloc[-1] < df_route['price'].iloc[0] else 'up'
            }
        except:
            return None

class DealsManager:
    def __init__(self, data_mgr: DataManager, config: ConfigManager):
        self.data_mgr = data_mgr
        self.config = config
        self.notified_deals = {}
    
    def find_deals(self, prices: List[FlightPrice]) -> List[Deal]:
        deals = []
        for price in prices:
            hist_avg = self.data_mgr.get_historical_avg(price.route, days=30)
            if hist_avg and hist_avg > 0:
                savings_pct = ((hist_avg - price.price) / hist_avg) * 100
                if savings_pct >= self.config.deal_threshold_pct:
                    deal = Deal(
                        flight_price=price, savings_pct=savings_pct,
                        historical_avg=hist_avg, detected_at=datetime.now()
                    )
                    deals.append(deal)
        return sorted(deals, key=lambda d: d.savings_pct, reverse=True)
    
    def should_notify(self, deal: Deal) -> bool:
        route = deal.flight_price.route
        if route in self.notified_deals:
            last_notif = self.notified_deals[route]
            if (datetime.now() - last_notif).seconds < DEAL_NOTIFICATION_COOLDOWN:
                return False
        self.notified_deals[route] = datetime.now()
        return True

class TelegramBotManager:
    def __init__(self, config: ConfigManager, scanner: FlightScanner, data_mgr: DataManager):
        self.config, self.scanner, self.data_mgr = config, scanner, data_mgr
        self.deals_mgr = DealsManager(data_mgr, config)
        self.app, self.running = None, False
        
        # Inicializar módulos de retención si están disponibles
        if RETENTION_ENABLED:
            try:
                self.retention_mgr = RetentionManager()
                self.smart_notifier = SmartNotifier(config.bot_token)
                self.background_tasks = None  # Se inicializa después del start
                self.onboarding_mgr = OnboardingManager()
                self.quick_actions_mgr = QuickActionsManager()
                self.retention_cmds = None  # Se inicializa después del start
                logger.info("✅ Módulos de retención cargados correctamente")
            except Exception as e:
                logger.error(f"❌ Error cargando módulos de retención: {e}")
                RETENTION_ENABLED = False
    
    async def start(self):
        self.app = Application.builder().token(self.config.bot_token).build()
        
        # Comandos core
        self.app.add_handler(CommandHandler('start', self.cmd_start))
        self.app.add_handler(CommandHandler('scan', self.cmd_scan))
        self.app.add_handler(CommandHandler('route', self.cmd_route))
        self.app.add_handler(CommandHandler('deals', self.cmd_deals))
        self.app.add_handler(CommandHandler('trends', self.cmd_trends))
        self.app.add_handler(CommandHandler('clearcache', self.cmd_clearcache))
        self.app.add_handler(CommandHandler('status', self.cmd_status))
        self.app.add_handler(CommandHandler('help', self.cmd_help))
        
        # Comandos de retención
        if RETENTION_ENABLED:
            self.retention_cmds = RetentionCommandHandler(
                self.retention_mgr, 
                self.scanner,
                self.deals_mgr
            )
            self.app.add_handler(CommandHandler('daily', self.cmd_daily))
            self.app.add_handler(CommandHandler('watchlist', self.cmd_watchlist))
            self.app.add_handler(CommandHandler('profile', self.cmd_profile))
            self.app.add_handler(CommandHandler('shop', self.cmd_shop))
            
            # Inicializar background tasks
            self.background_tasks = BackgroundTaskManager(
                self.app.bot,
                self.retention_mgr,
                self.scanner,
                self.smart_notifier
            )
        
        self.app.add_handler(CallbackQueryHandler(self.handle_callback))
        
        self.running = True
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling(drop_pending_updates=True)
        
        # Iniciar tareas automáticas
        if self.config.auto_scan_enabled:
            asyncio.create_task(self.auto_scan_loop())
        
        if RETENTION_ENABLED and self.background_tasks:
            await self.background_tasks.start()
    
    async def stop(self):
        self.running = False
        if RETENTION_ENABLED and self.background_tasks:
            await self.background_tasks.stop()
        if self.app:
            if self.app.updater and self.app.updater.running:
                await self.app.updater.stop()
            await self.app.stop()
            await self.app.shutdown()
    
    async def auto_scan_loop(self):
        while self.running:
            await asyncio.sleep(AUTO_SCAN_INTERVAL)
            routes = [FlightRoute(**f) for f in self.config.flights]
            prices = self.scanner.scan_routes(routes)
            if prices:
                self.data_mgr.save_prices(prices)
                deals = self.deals_mgr.find_deals(prices)
                for deal in deals:
                    if self.deals_mgr.should_notify(deal):
                        try:
                            await self.app.bot.send_message(
                                chat_id=self.config.chat_id,
                                text=deal.get_message(),
                                parse_mode='Markdown'
                            )
                        except: pass
    
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        msg = update.effective_message
        if not msg: return
        user = update.effective_user
        
        await context.bot.send_chat_action(chat_id=msg.chat_id, action=ChatAction.TYPING)
        
        # Check si es nuevo usuario y hacer onboarding
        if RETENTION_ENABLED:
            profile = self.retention_mgr.get_or_create_profile(user.id, user.username or "user")
            
            # Si es nuevo (sin búsquedas), iniciar onboarding
            if profile.total_searches == 0:
                await self.onboarding_mgr.start_onboarding(update, context, self.retention_mgr)
                return
        
        welcome = (
            f"🎆 *{APP_NAME} v{VERSION}* 🎆\n\n"
            "*Comandos Core:*\n"
            "/scan - Escanear rutas\n"
            "/route - Búsqueda personalizada\n"
            "/deals - Ver chollos\n"
            "/trends - Análisis tendencias\n"
            "/clearcache - Limpiar caché\n"
            "/status - Estado sistema\n"
            "/help - Ayuda\n"
        )
        
        if RETENTION_ENABLED:
            welcome += (
                "\n*Comandos Gamificación:* 🎮\n"
                "/daily - Reward diario 💰\n"
                "/watchlist - Tu watchlist 📍\n"
                "/profile - Tu perfil 📊\n"
                "/shop - Tienda FlightCoins 🛒"
            )
        
        keyboard = [
            [InlineKeyboardButton("🔍 Escanear", callback_data="scan")],
            [InlineKeyboardButton("💰 Chollos", callback_data="deals")],
            [InlineKeyboardButton("📈 Tendencias", callback_data="trends")]
        ]
        
        if RETENTION_ENABLED:
            keyboard.append([InlineKeyboardButton("🎁 Reward Diario", callback_data="daily")])
            keyboard.append([InlineKeyboardButton("📊 Mi Perfil", callback_data="profile")])
        
        await msg.reply_text(welcome, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
        
        # Mostrar Quick Actions Bar si está disponible
        if RETENTION_ENABLED:
            qa_keyboard = self.quick_actions_mgr.get_keyboard(user.id, self.retention_mgr)
            if qa_keyboard:
                await msg.reply_text("⚡ *Acciones Rápidas*", parse_mode='Markdown', reply_markup=qa_keyboard)
    
    async def cmd_scan(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        msg = update.effective_message
        if not msg: return
        user = update.effective_user
        
        await context.bot.send_chat_action(chat_id=msg.chat_id, action=ChatAction.TYPING)
        await msg.reply_text("🔍 Iniciando escaneo...")
        
        routes = [FlightRoute(**f) for f in self.config.flights]
        prices = self.scanner.scan_routes(routes)
        
        if RETENTION_ENABLED:
            # Track búsqueda
            for route in routes:
                self.retention_mgr.track_search(user.id, user.username or "user", route.route_code)
        
        if prices:
            self.data_mgr.save_prices(prices)
            response = "✅ *Escaneo completado*\n\n"
            for p in prices[:5]:
                response += f"{p.get_confidence_emoji()} {p.name}: {p.format_price()} ({p.source.value})\n"
            if len(prices) > 5:
                response += f"\n_...y {len(prices)-5} resultados más_"
            await msg.reply_text(response, parse_mode='Markdown')
        else:
            await msg.reply_text("❌ No se obtuvieron resultados")
    
    async def cmd_route(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        msg = update.effective_message
        if not msg: return
        user = update.effective_user
        
        await context.bot.send_chat_action(chat_id=msg.chat_id, action=ChatAction.TYPING)
        
        if not context.args or len(context.args) < 3:
            await msg.reply_text("⚠️ Uso: /route MAD BCN 2026-02-15")
            return
        
        origin, dest, date = context.args[0].upper(), context.args[1].upper(), context.args[2]
        
        try:
            route = FlightRoute(origin=origin, dest=dest, name=f"{origin}-{dest}")
            
            if RETENTION_ENABLED:
                self.retention_mgr.track_search(user.id, user.username or "user", route.route_code)
            
            await msg.reply_text(f"🔍 Buscando vuelos {origin} → {dest} para {date} (±3 días)...")
            prices = self.scanner.scan_route_flexible(route, date)
            
            if prices:
                response = f"✅ *Encontrados {len(prices)} vuelos*\n\n"
                for i, p in enumerate(prices, 1):
                    response += f"{i}️⃣ {p.format_price()} - {p.departure_date}\n"
                    if p.airline: response += f"   ✈️ {p.airline}\n"
                    response += f"   {p.get_confidence_emoji()} {p.confidence:.0%} confianza\n\n"
                await msg.reply_text(response, parse_mode='Markdown')
            else:
                await msg.reply_text("❌ No se encontraron vuelos")
        except Exception as e:
            await msg.reply_text(f"❌ Error: {e}")
    
    async def cmd_deals(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        msg = update.effective_message
        if not msg: return
        user = update.effective_user
        
        await context.bot.send_chat_action(chat_id=msg.chat_id, action=ChatAction.TYPING)
        await msg.reply_text("🔍 Buscando chollos...")
        
        routes = [FlightRoute(**f) for f in self.config.flights]
        prices = self.scanner.scan_routes(routes)
        deals = self.deals_mgr.find_deals(prices)
        
        if deals:
            if RETENTION_ENABLED:
                # Track deals encontrados
                for deal in deals[:3]:
                    self.retention_mgr.track_deal_found(
                        user.id, 
                        user.username or "user",
                        deal.flight_price.price * deal.savings_pct / 100
                    )
            
            for deal in deals[:3]:
                await msg.reply_text(deal.get_message(), parse_mode='Markdown')
        else:
            await msg.reply_text("🙁 No hay chollos disponibles ahora")
    
    async def cmd_trends(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        msg = update.effective_message
        if not msg: return
        
        await context.bot.send_chat_action(chat_id=msg.chat_id, action=ChatAction.TYPING)
        
        if not context.args:
            await msg.reply_text("⚠️ Uso: /trends MAD-MIA")
            return
        
        route_code = context.args[0].upper()
        trend = self.data_mgr.get_price_trend(route_code, days=30)
        
        if trend:
            emoji = "📉" if trend['trend'] == 'down' else "📈"
            response = (
                f"📈 *Tendencia: {route_code}*\n\n"
                f"📊 *Media:* €{trend['avg']:.0f}\n"
                f"💰 *Mínimo:* €{trend['min']:.0f}\n"
                f"💸 *Máximo:* €{trend['max']:.0f}\n"
                f"📊 *Datos:* {trend['count']} precios\n"
                f"{emoji} *Tendencia:* {'Bajando' if trend['trend']=='down' else 'Subiendo'}"
            )
            await msg.reply_text(response, parse_mode='Markdown')
        else:
            await msg.reply_text("❌ No hay datos históricos para esta ruta")
    
    async def cmd_clearcache(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        msg = update.effective_message
        if not msg: return
        cleared = self.scanner.cache.clear()
        await msg.reply_text(f"🗑️ *Caché limpiado*\n\n📄 Items eliminados: {cleared}", parse_mode='Markdown')
    
    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        msg = update.effective_message
        if not msg: return
        
        cache_size = self.scanner.cache.size
        hit_rate = self.scanner.cache.hit_rate
        
        msg_text = (
            "📊 *Estado del Sistema*\n\n"
            f"🗃️ Caché: {cache_size} items ({hit_rate:.1%} hit rate)\n"
            f"⚡ Circuit: {self.scanner.circuit.state.value}"
        )
        
        if RETENTION_ENABLED:
            total_users = len(self.retention_mgr.profiles)
            msg_text += f"\n👥 Usuarios: {total_users}"
            if self.background_tasks:
                msg_text += "\n✅ Background tasks: Activas"
        
        await msg.reply_text(msg_text, parse_mode='Markdown')
    
    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        msg = update.effective_message
        if not msg: return
        
        help_text = (
            f"📚 *Ayuda - {APP_NAME}*\n\n"
            "*Comandos Core:*\n"
            "/start - Iniciar bot\n"
            "/scan - Escanear todas las rutas\n"
            "/route MAD BCN 2026-02-15 - Búsqueda personalizada\n"
            "/deals - Ver chollos disponibles\n"
            "/trends MAD-MIA - Tendencias de precio\n"
            "/clearcache - Limpiar caché\n"
            "/status - Estado del sistema\n"
        )
        
        if RETENTION_ENABLED:
            help_text += (
                "\n*Comandos Gamificación:* 🎮\n"
                "/daily - Reclama reward diario (50-200 coins)\n"
                "/watchlist add MAD-MIA 450 - Añadir a watchlist\n"
                "/watchlist view - Ver tu watchlist\n"
                "/profile - Ver tu perfil y estadísticas\n"
                "/shop - Tienda de FlightCoins\n"
            )
        
        help_text += f"\n_Versión: {VERSION}_"
        
        await msg.reply_text(help_text, parse_mode='Markdown')
    
    # Comandos de retención
    async def cmd_daily(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not RETENTION_ENABLED:
            await update.effective_message.reply_text("⚠️ Sistema de retención no disponible")
            return
        await self.retention_cmds.handle_daily(update, context)
    
    async def cmd_watchlist(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not RETENTION_ENABLED:
            await update.effective_message.reply_text("⚠️ Sistema de retención no disponible")
            return
        await self.retention_cmds.handle_watchlist(update, context)
    
    async def cmd_profile(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not RETENTION_ENABLED:
            await update.effective_message.reply_text("⚠️ Sistema de retención no disponible")
            return
        await self.retention_cmds.handle_profile(update, context)
    
    async def cmd_shop(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not RETENTION_ENABLED:
            await update.effective_message.reply_text("⚠️ Sistema de retención no disponible")
            return
        await self.retention_cmds.handle_shop(update, context)
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        if not query: return
        await query.answer()
        
        # Callbacks core
        if query.data == "scan":
            await self.cmd_scan(update, context)
        elif query.data == "deals":
            await self.cmd_deals(update, context)
        elif query.data == "trends":
            await query.message.reply_text("⚠️ Usa: /trends MAD-MIA")
        
        # Callbacks de retención
        elif RETENTION_ENABLED:
            if query.data == "daily":
                await self.cmd_daily(update, context)
            elif query.data == "profile":
                await self.cmd_profile(update, context)
            elif query.data.startswith("qa_"):
                # Quick Actions callbacks
                await self.quick_actions_mgr.handle_callback(
                    update, context, self.retention_mgr, self.scanner, self.deals_mgr
                )
            elif query.data.startswith("onb_"):
                # Onboarding callbacks
                await self.onboarding_mgr.handle_callback(
                    update, context, self.retention_mgr
                )

async def main():
    print(f"\n{'='*80}")
    print(f"{f'{APP_NAME} v{VERSION}'.center(80)}")
    print(f"{'='*80}\n")
    
    if RETENTION_ENABLED:
        print("✅ Módulos de retención: ACTIVOS")
        print("   🎮 Hook Model | 💰 FlightCoins | 🏆 Achievements")
        print("   🔔 Smart Notifications | ⏰ Background Tasks")
        print("   🎉 Onboarding | ⚡ Quick Actions\n")
    else:
        print("⚠️ Módulos de retención: NO DISPONIBLES\n")
    
    try:
        config = ConfigManager()
        scanner = FlightScanner(config)
        data_mgr = DataManager()
        bot_mgr = TelegramBotManager(config, scanner, data_mgr)
        
        await bot_mgr.start()
        print("✅ Bot iniciado correctamente")
        
        while bot_mgr.running:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n⏹️ Deteniendo bot...")
    except Exception as e:
        print(f"❌ Error fatal: {e}")
    finally:
        if 'bot_mgr' in locals():
            await bot_mgr.stop()
        print("✅ Bot detenido")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n✅ Sistema detenido por el usuario")