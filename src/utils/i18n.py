#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
┌────────────────────────────────────────────────────────┐
│  🌍 I18N MODULE - Internationalization Manager           │
│  🚀 Cazador Supremo v13.0 Enterprise                      │
└────────────────────────────────────────────────────────┘

Módulo de internacionalización con soporte para:
- Español (es)
- Inglés (en)
- Auto-detección desde Telegram
- Templates con variables
- Fallback automático

Autor: @Juanka_Spain
Version: 13.0.0
Date: 2026-01-14
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional, Any
from functools import lru_cache
import threading

# Logger
logger = logging.getLogger(__name__)


class I18nManager:
    """
    Gestor de internacionalización con auto-detección de idioma.
    
    Features:
    - Carga traducciones desde JSON
    - Auto-detección de idioma del usuario (Telegram language_code)
    - Template engine con variables
    - Fallback automático (lang solicitado → default → EN)
    - Cache de traducciones
    - Thread-safe
    
    Uso:
    >>> i18n = I18nManager(default_lang='es')
    >>> i18n._('commands.start.welcome', lang='es', name='Bot', version='v13.0')
    '🎆 *Bot v13.0* 🎆...'
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        """Singleton pattern para evitar múltiples cargas del JSON"""
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, 
                 translations_file: str = 'translations.json',
                 default_lang: str = 'es',
                 auto_detect: bool = True):
        """
        Inicializa el gestor de traducciones.
        
        Args:
            translations_file: Ruta al archivo JSON de traducciones
            default_lang: Idioma por defecto ('es' o 'en')
            auto_detect: Si auto-detectar idioma del usuario
        """
        # Evitar re-inicialización en singleton
        if hasattr(self, '_initialized'):
            return
        
        self.translations_file = Path(translations_file)
        self.default_lang = default_lang
        self.auto_detect = auto_detect
        self.translations: Dict[str, Dict] = {}
        self.supported_langs = ['es', 'en']
        
        # Carga inicial
        self._load_translations()
        
        self._initialized = True
        logger.info(f"🌍 I18nManager initialized: default={default_lang}, auto_detect={auto_detect}")
    
    def _load_translations(self) -> None:
        """
        Carga traducciones desde el archivo JSON.
        
        Raises:
            FileNotFoundError: Si el archivo no existe
            JSONDecodeError: Si el JSON es inválido
        """
        if not self.translations_file.exists():
            logger.error(f"❌ Translations file not found: {self.translations_file}")
            raise FileNotFoundError(f"Translations file not found: {self.translations_file}")
        
        try:
            with open(self.translations_file, 'r', encoding='utf-8') as f:
                self.translations = json.load(f)
            
            loaded_langs = list(self.translations.keys())
            logger.info(f"✅ Loaded translations for: {', '.join(loaded_langs)}")
            
            # Validar que existen los idiomas soportados
            for lang in self.supported_langs:
                if lang not in self.translations:
                    logger.warning(f"⚠️ Language '{lang}' not found in translations file")
        
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON in translations file: {e}")
            raise
    
    def reload(self) -> None:
        """
        Recarga las traducciones desde el archivo.
        Útil después de actualizar translations.json en caliente.
        """
        logger.info("🔄 Reloading translations...")
        self._load_translations()
        self.get_text.cache_clear()  # Limpiar cache
    
    def detect_language(self, user) -> str:
        """
        Detecta el idioma del usuario desde Telegram.
        
        Args:
            user: Objeto User de Telegram (tiene language_code)
        
        Returns:
            Código de idioma detectado ('es' o 'en')
        """
        if not self.auto_detect:
            return self.default_lang
        
        try:
            # Telegram language_code es ISO 639-1 (2 letras)
            user_lang = getattr(user, 'language_code', None)
            
            if user_lang:
                # Normalizar (puede venir 'es-ES', 'en-US')
                lang_code = user_lang.split('-')[0].lower()
                
                if lang_code in self.supported_langs:
                    logger.debug(f"🌍 Detected language: {lang_code} for user {user.id}")
                    return lang_code
        
        except Exception as e:
            logger.warning(f"⚠️ Error detecting language: {e}")
        
        # Fallback al idioma por defecto
        return self.default_lang
    
    @lru_cache(maxsize=256)
    def get_text(self, key: str, lang: str = None) -> Optional[str]:
        """
        Obtiene texto traducido por clave jerárquica.
        
        Args:
            key: Clave jerárquica (ej: 'commands.start.welcome')
            lang: Idioma solicitado (None = usar default)
        
        Returns:
            Texto traducido o None si no existe
        
        Ejemplos:
            >>> get_text('commands.start.welcome', lang='es')
            '🎆 *{name} {version}* 🎆...'
        """
        target_lang = lang or self.default_lang
        
        # Validar idioma
        if target_lang not in self.translations:
            logger.warning(f"⚠️ Language '{target_lang}' not available, using '{self.default_lang}'")
            target_lang = self.default_lang
        
        # Navegar jerarquía de keys
        try:
            parts = key.split('.')
            value = self.translations[target_lang]
            
            for part in parts:
                value = value[part]
            
            return value
        
        except (KeyError, TypeError) as e:
            # Intentar fallback a inglés
            if target_lang != 'en':
                try:
                    parts = key.split('.')
                    value = self.translations['en']
                    for part in parts:
                        value = value[part]
                    logger.warning(f"⚠️ Key '{key}' not found in '{target_lang}', using 'en' fallback")
                    return value
                except:
                    pass
            
            logger.error(f"❌ Translation key not found: '{key}' (lang: {target_lang})")
            return None
    
    def _(self, key: str, lang: str = None, **kwargs) -> str:
        """
        Función universal de traducción con template engine.
        
        Args:
            key: Clave de traducción
            lang: Idioma (None = usar default)
            **kwargs: Variables para formatear el template
        
        Returns:
            Texto traducido y formateado
        
        Ejemplos:
            >>> _('commands.start.welcome', lang='es', name='Bot', version='v13.0')
            '🎆 *Bot v13.0* 🎆...'
            
            >>> _('commands.route.searching', origin='MAD', dest='BCN', date='2026-02-15')
            '🔍 Buscando MAD → BCN para 2026-02-15 (±3 días)...'
        """
        text = self.get_text(key, lang)
        
        if text is None:
            # Fallback: devolver la key en mayúsculas como indicador de error
            return f"[MISSING: {key}]"
        
        # Formatear template con kwargs
        if kwargs:
            try:
                return text.format(**kwargs)
            except KeyError as e:
                logger.error(f"❌ Missing template variable in '{key}': {e}")
                return text  # Devolver sin formatear
        
        return text
    
    def get_all(self, lang: str = None) -> Dict[str, Any]:
        """
        Obtiene todas las traducciones de un idioma.
        
        Args:
            lang: Idioma (None = usar default)
        
        Returns:
            Diccionario completo de traducciones
        """
        target_lang = lang or self.default_lang
        return self.translations.get(target_lang, {})
    
    def format_price(self, price: float, currency: str = 'EUR', lang: str = None) -> str:
        """
        Formatea un precio según el idioma.
        
        Args:
            price: Precio numérico
            currency: Moneda (EUR, USD, GBP)
            lang: Idioma
        
        Returns:
            Precio formateado
        
        Ejemplos:
            >>> format_price(500, 'EUR', 'es')
            '500€'
            >>> format_price(500, 'USD', 'en')
            '$500'
        """
        symbols = {'EUR': '€', 'USD': '$', 'GBP': '£'}
        symbol = symbols.get(currency, currency)
        
        target_lang = lang or self.default_lang
        
        # Español: precio + símbolo
        if target_lang == 'es':
            return f"{price:.0f}{symbol}"
        # Inglés: símbolo + precio
        else:
            return f"{symbol}{price:.0f}"
    
    def format_date(self, date_str: str, lang: str = None) -> str:
        """
        Formatea una fecha según el idioma.
        
        Args:
            date_str: Fecha en formato YYYY-MM-DD
            lang: Idioma
        
        Returns:
            Fecha formateada
        
        Ejemplos:
            >>> format_date('2026-02-15', 'es')
            '15/02/2026'
            >>> format_date('2026-02-15', 'en')
            '02/15/2026'
        """
        from datetime import datetime
        
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            target_lang = lang or self.default_lang
            
            # Español: DD/MM/YYYY
            if target_lang == 'es':
                return date_obj.strftime('%d/%m/%Y')
            # Inglés: MM/DD/YYYY
            else:
                return date_obj.strftime('%m/%d/%Y')
        
        except ValueError:
            logger.error(f"❌ Invalid date format: {date_str}")
            return date_str
    
    def __repr__(self) -> str:
        return f"I18nManager(default_lang='{self.default_lang}', langs={self.supported_langs})"


# 🌐 INSTANCIA GLOBAL (Singleton)
_i18n_instance: Optional[I18nManager] = None


def get_i18n(translations_file: str = 'translations.json',
             default_lang: str = 'es',
             auto_detect: bool = True) -> I18nManager:
    """
    Obtiene la instancia global del I18nManager (Singleton).
    
    Args:
        translations_file: Archivo de traducciones
        default_lang: Idioma por defecto
        auto_detect: Auto-detectar idioma
    
    Returns:
        Instancia de I18nManager
    """
    global _i18n_instance
    
    if _i18n_instance is None:
        _i18n_instance = I18nManager(
            translations_file=translations_file,
            default_lang=default_lang,
            auto_detect=auto_detect
        )
    
    return _i18n_instance


def _(key: str, lang: str = None, **kwargs) -> str:
    """
    Función global de traducción (shorthand).
    
    Uso:
        >>> from i18n import _
        >>> _('commands.start.welcome', name='Bot', version='v13.0')
    """
    i18n = get_i18n()
    return i18n._(key, lang, **kwargs)


if __name__ == '__main__':
    # 🧪 Tests rápidos
    print("🧪 Testing I18nManager...\n")
    
    # Crear instancia
    i18n = I18nManager(default_lang='es')
    
    # Test 1: Traducción básica
    print("1. Basic translation:")
    print(f"   ES: {i18n._('commands.scan.starting', lang='es')}")
    print(f"   EN: {i18n._('commands.scan.starting', lang='en')}")
    
    # Test 2: Template con variables
    print("\n2. Template with variables:")
    print(f"   ES: {i18n._('commands.route.searching', lang='es', origin='MAD', dest='BCN', date='2026-02-15')}")
    print(f"   EN: {i18n._('commands.route.searching', lang='en', origin='MAD', dest='BCN', date='2026-02-15')}")
    
    # Test 3: Precio formateado
    print("\n3. Price formatting:")
    print(f"   ES: {i18n.format_price(500, 'EUR', 'es')}")
    print(f"   EN: {i18n.format_price(500, 'USD', 'en')}")
    
    # Test 4: Fecha formateada
    print("\n4. Date formatting:")
    print(f"   ES: {i18n.format_date('2026-02-15', 'es')}")
    print(f"   EN: {i18n.format_date('2026-02-15', 'en')}")
    
    # Test 5: Key inexistente (fallback)
    print("\n5. Missing key (fallback):")
    print(f"   Result: {i18n._('non.existent.key', lang='es')}")
    
    print("\n✅ All tests completed!")
