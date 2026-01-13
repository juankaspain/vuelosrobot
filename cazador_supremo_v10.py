#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔═══════════════════════════════════════════════════════════════════════════╗
║                    CAZADOR SUPREMO v10.0 ENTERPRISE                       ║
║                Sistema Profesional de Monitorización de Vuelos            ║
║                                                                           ║
║  Autor: @Juanka_Spain                                                     ║
║  Versión: 10.0.0                                                          ║
║  Licencia: MIT                                                            ║
║  Python: 3.9+                                                             ║
╚═══════════════════════════════════════════════════════════════════════════╝

Descripción:
    Sistema enterprise de monitorización de precios de vuelos con:
    - Arquitectura orientada a objetos
    - Logging avanzado con rotación
    - Manejo robusto de errores
    - Caché de respuestas API
    - Rate limiting
    - Validación de entrada
    - Métricas y estadísticas
    - Alertas inteligentes vía Telegram

Uso:
    python cazador_supremo_v10.py

Dependencias:
    Ver requirements.txt
"""

import asyncio
import sys
import os
import json
import logging
import time
import random
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from logging.handlers import RotatingFileHandler
from functools import wraps, lru_cache
from collections import defaultdict

import requests
import pandas as pd
import feedparser
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes
from concurrent.futures import ThreadPoolExecutor, as_completed

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN INICIAL
# ═══════════════════════════════════════════════════════════════════════════

# Configurar encoding UTF-8 para Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    os.system('chcp 65001 > nul 2>&1')

# ═══════════════════════════════════════════════════════════════════════════
# EXCEPCIONES PERSONALIZADAS
# ═══════════════════════════════════════════════════════════════════════════

class FlightBotException(Exception):
    """Excepción base para el bot de vuelos"""
    pass

class ConfigurationError(FlightBotException):
    """Error en la configuración del sistema"""
    pass

class APIError(FlightBotException):
    """Error al comunicarse con APIs externas"""
    pass

class ValidationError(FlightBotException):
    """Error de validación de datos"""
    pass

# ═══════════════════════════════════════════════════════════════════════════
# MODELOS DE DATOS
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class FlightRoute:
    """Modelo de datos para una ruta de vuelo"""
    origin: str
    dest: str
    name: str
    
    def __post_init__(self):
        self.origin = self.origin.upper()
        self.dest = self.dest.upper()
    
    def validate(self) -> bool:
        """Valida que los códigos IATA sean correctos"""
        return (len(self.origin) == 3 and 
                len(self.dest) == 3 and 
                self.origin.isalpha() and 
                self.dest.isalpha())
    
    @property
    def route_key(self) -> str:
        """Identificador único de la ruta"""
        return f"{self.origin}-{self.dest}"

@dataclass
class FlightPrice:
    """Modelo de datos para el precio de un vuelo"""
    route: str
    name: str
    price: float
    source: str
    timestamp: datetime
    currency: str = "EUR"
    
    def is_hot_deal(self, threshold: float) -> bool:
        """Determina si es un chollo basado en el umbral"""
        return self.price < threshold
    
    def to_dict(self) -> Dict:
        """Convierte a diccionario para serialización"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data

# ═══════════════════════════════════════════════════════════════════════════
# SISTEMA DE LOGGING AVANZADO
# ═══════════════════════════════════════════════════════════════════════════

class LoggerManager:
    """Gestor centralizado de logging con rotación y múltiples niveles"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self._setup_loggers()
    
    def _setup_loggers(self):
        """Configura los loggers del sistema"""
        # Logger principal
        self.main_logger = logging.getLogger('CazadorSupremo')
        self.main_logger.setLevel(logging.DEBUG)
        
        # Logger de APIs
        self.api_logger = logging.getLogger('CazadorSupremo.API')
        self.api_logger.setLevel(logging.INFO)
        
        # Logger de Telegram
        self.telegram_logger = logging.getLogger('CazadorSupremo.Telegram')
        self.telegram_logger.setLevel(logging.INFO)
        
        # Formato detallado
        detailed_formatter = logging.Formatter(
            '%(asctime)s | %(name)-20s | %(levelname)-8s | %(funcName)-20s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Handler con rotación (10MB, 5 backups)
        file_handler = RotatingFileHandler(
            'logs/cazador_supremo.log',
            maxBytes=10*1024*1024,
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        
        # Handler de errores (archivo separado)
        error_handler = RotatingFileHandler(
            'logs/errors.log',
            maxBytes=5*1024*1024,
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        
        # Añadir handlers a todos los loggers
        for logger in [self.main_logger, self.api_logger, self.telegram_logger]:
            logger.addHandler(file_handler)
            logger.addHandler(error_handler)
        
        # Crear directorio de logs si no existe
        Path('logs').mkdir(exist_ok=True)
        
        self.main_logger.info("═" * 80)
        self.main_logger.info("Sistema de logging inicializado correctamente")
        self.main_logger.info(f"Versión: 10.0.0 Enterprise")
        self.main_logger.info("═" * 80)

# ═══════════════════════════════════════════════════════════════════════════
# DECORADORES PARA FUNCIONALIDAD AVANZADA
# ═══════════════════════════════════════════════════════════════════════════

def retry_on_failure(max_attempts: int = 3, delay: float = 1.0):
    """Decorador para reintentar operaciones fallidas
    
    Args:
        max_attempts: Número máximo de intentos
        delay: Tiempo de espera entre intentos (segundos)
    
    Example:
        @retry_on_failure(max_attempts=3, delay=2.0)
        def call_api():
            return requests.get(url)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger('CazadorSupremo')
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts:
                        logger.error(f"Función {func.__name__} falló después de {max_attempts} intentos: {e}")
                        raise
                    logger.warning(f"Intento {attempt}/{max_attempts} falló para {func.__name__}: {e}. Reintentando...")
                    time.sleep(delay * attempt)  # Backoff exponencial
            return None
        return wrapper
    return decorator

def measure_time(func):
    """Decorador para medir tiempo de ejecución"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger('CazadorSupremo')
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        logger.info(f"⏱️  {func.__name__} completado en {elapsed:.2f}s")
        return result
    return wrapper

def log_exceptions(func):
    """Decorador para loggear excepciones automáticamente"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger('CazadorSupremo')
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.exception(f"Excepción en {func.__name__}: {e}")
            raise
    return wrapper

# ═══════════════════════════════════════════════════════════════════════════
# SISTEMA DE CACHÉ
# ═══════════════════════════════════════════════════════════════════════════

class CacheManager:
    """Gestor de caché para respuestas de API"""
    
    def __init__(self, ttl: int = 300):
        """
        Args:
            ttl: Time to live en segundos (default: 5 minutos)
        """
        self.cache: Dict[str, Tuple[Any, float]] = {}
        self.ttl = ttl
        self.hits = 0
        self.misses = 0
        self.logger = logging.getLogger('CazadorSupremo.Cache')
    
    def get(self, key: str) -> Optional[Any]:
        """Obtiene un valor del caché si no ha expirado"""
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                self.hits += 1
                self.logger.debug(f"Cache HIT: {key}")
                return value
            else:
                del self.cache[key]
                self.logger.debug(f"Cache EXPIRED: {key}")
        self.misses += 1
        self.logger.debug(f"Cache MISS: {key}")
        return None
    
    def set(self, key: str, value: Any):
        """Guarda un valor en el caché"""
        self.cache[key] = (value, time.time())
        self.logger.debug(f"Cache SET: {key}")
    
    def clear(self):
        """Limpia todo el caché"""
        self.cache.clear()
        self.logger.info("Cache limpiado completamente")
    
    def get_stats(self) -> Dict:
        """Retorna estadísticas del caché"""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        return {
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': f"{hit_rate:.1f}%",
            'size': len(self.cache)
        }

# ═══════════════════════════════════════════════════════════════════════════
# RATE LIMITER
# ═══════════════════════════════════════════════════════════════════════════

class RateLimiter:
    """Limitador de tasa para llamadas a API"""
    
    def __init__(self, calls_per_minute: int = 60):
        self.calls_per_minute = calls_per_minute
        self.calls: List[float] = []
        self.logger = logging.getLogger('CazadorSupremo.RateLimiter')
    
    def wait_if_needed(self):
        """Espera si se ha excedido el límite de llamadas"""
        now = time.time()
        # Limpiar llamadas antiguas (más de 1 minuto)
        self.calls = [t for t in self.calls if now - t < 60]
        
        if len(self.calls) >= self.calls_per_minute:
            sleep_time = 60 - (now - self.calls[0])
            if sleep_time > 0:
                self.logger.warning(f"Rate limit alcanzado. Esperando {sleep_time:.1f}s")
                time.sleep(sleep_time)
                self.calls = self.calls[1:]
        
        self.calls.append(now)

# ═══════════════════════════════════════════════════════════════════════════
# UTILIDADES DE CONSOLA
# ═══════════════════════════════════════════════════════════════════════════

class ConsoleUI:
    """Interfaz de usuario para consola con formato profesional"""
    
    # Colores ANSI (compatible con Windows 10+)
    RESET = '\033[0m'
    BOLD = '\033[1m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    
    @staticmethod
    def safe_print(text: str, flush: bool = True):
        """Imprime texto manejando errores de encoding"""
        try:
            print(text)
            if flush:
                sys.stdout.flush()
        except UnicodeEncodeError:
            print(text.encode('ascii', 'ignore').decode('ascii'))
            if flush:
                sys.stdout.flush()
    
    @classmethod
    def print_header(cls, title: str, width: int = 80, color: str = CYAN):
        """Imprime encabezado con estilo"""
        cls.safe_print(f"\n{color}{'═' * width}{cls.RESET}")
        cls.safe_print(f"{color}{cls.BOLD}{title.center(width)}{cls.RESET}")
        cls.safe_print(f"{color}{'═' * width}{cls.RESET}\n")
    
    @classmethod
    def print_section(cls, title: str, width: int = 80):
        """Imprime sección"""
        cls.safe_print(f"\n{'─' * width}")
        cls.safe_print(f"📍 {cls.BOLD}{title}{cls.RESET}")
        cls.safe_print(f"{'─' * width}\n")
    
    @classmethod
    def print_success(cls, message: str, emoji: str = "✅"):
        """Imprime mensaje de éxito"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        cls.safe_print(f"{cls.GREEN}[{timestamp}] {emoji} {message}{cls.RESET}")
    
    @classmethod
    def print_error(cls, message: str, emoji: str = "❌"):
        """Imprime mensaje de error"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        cls.safe_print(f"{cls.RED}[{timestamp}] {emoji} {message}{cls.RESET}")
    
    @classmethod
    def print_warning(cls, message: str, emoji: str = "⚠️"):
        """Imprime advertencia"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        cls.safe_print(f"{cls.YELLOW}[{timestamp}] {emoji} {message}{cls.RESET}")
    
    @classmethod
    def print_info(cls, message: str, emoji: str = "ℹ️"):
        """Imprime información"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        cls.safe_print(f"[{timestamp}] {emoji} {message}")
    
    @classmethod
    def print_result(cls, label: str, value: Any, emoji: str = ""):
        """Imprime resultado formateado"""
        cls.safe_print(f"   {emoji} {cls.BOLD}{label}:{cls.RESET} {value}")

# ═══════════════════════════════════════════════════════════════════════════
# GESTOR DE CONFIGURACIÓN
# ═══════════════════════════════════════════════════════════════════════════

class ConfigManager:
    """Gestor de configuración con validación"""
    
    def __init__(self, config_file: str = 'config.json'):
        self.config_file = config_file
        self.logger = logging.getLogger('CazadorSupremo.Config')
        self.config = self._load_config()
        self._validate_config()
    
    @log_exceptions
    def _load_config(self) -> Dict:
        """Carga configuración desde archivo JSON"""
        ConsoleUI.print_info("Cargando configuración...")
        
        if not Path(self.config_file).exists():
            raise ConfigurationError(f"Archivo {self.config_file} no encontrado")
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            ConsoleUI.print_success(f"Configuración cargada: {self.config_file}")
            self.logger.info(f"Configuración cargada desde {self.config_file}")
            return config
        
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"JSON inválido en {self.config_file}: {e}")
    
    def _validate_config(self):
        """Valida la configuración cargada"""
        ConsoleUI.print_info("Validando configuración...")
        required_keys = ['telegram', 'flights']
        
        for key in required_keys:
            if key not in self.config:
                raise ConfigurationError(f"Clave requerida '{key}' no encontrada en configuración")
        
        # Validar Telegram
        if 'token' not in self.config['telegram'] or 'chat_id' not in self.config['telegram']:
            raise ConfigurationError("Configuración de Telegram incompleta")
        
        # Validar rutas
        if not isinstance(self.config['flights'], list) or len(self.config['flights']) == 0:
            raise ConfigurationError("Debe haber al menos una ruta de vuelo configurada")
        
        # Validar cada ruta
        for idx, flight in enumerate(self.config['flights']):
            try:
                route = FlightRoute(**flight)
                if not route.validate():
                    raise ValidationError(f"Ruta {idx + 1} tiene códigos IATA inválidos")
            except TypeError as e:
                raise ConfigurationError(f"Ruta {idx + 1} mal formada: {e}")
        
        ConsoleUI.print_success("Configuración validada correctamente")
        self.logger.info("Configuración validada exitosamente")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Obtiene valor de configuración con default opcional"""
        return self.config.get(key, default)
    
    @property
    def bot_token(self) -> str:
        return self.config['telegram']['token']
    
    @property
    def chat_id(self) -> str:
        return str(self.config['telegram']['chat_id'])
    
    @property
    def flight_routes(self) -> List[FlightRoute]:
        return [FlightRoute(**f) for f in self.config['flights']]
    
    @property
    def alert_threshold(self) -> float:
        return float(self.config.get('alert_min', 500))

# Continúa en la siguiente parte...