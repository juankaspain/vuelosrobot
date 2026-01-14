#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🌍 i18n - Sistema de Internacionalización
Soporte para múltiples idiomas con auto-detección

Autor: @Juanka_Spain
Fecha: 2026-01-14
Versión: 1.0.0
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional, Any
from functools import lru_cache
import threading

logger = logging.getLogger(__name__)

class TranslationManager:
    """
    Gestor de traducciones con soporte multi-idioma.
    
    Características:
    - Auto-detección de idioma del usuario
    - Fallback inteligente (key específica -> idioma -> default)
    - Cache de traducciones para performance
    - Thread-safe
    - Formateo con variables {var}
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        """Singleton pattern para instancia única global"""
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, 
                 translations_file: str = "translations.json",
                 default_language: str = "es",
                 fallback_language: str = "en",
                 auto_detect: bool = True):
        
        # Evitar reinicializar si ya está configurado
        if hasattr(self, '_initialized'):
            return
        
        self.translations_file = Path(translations_file)
        self.default_language = default_language
        self.fallback_language = fallback_language
        self.auto_detect = auto_detect
        self.translations: Dict[str, Dict] = {}
        self.user_languages: Dict[int, str] = {}  # user_id -> language
        
        self._load_translations()
        self._initialized = True
        
        logger.info(f"🌍 TranslationManager initialized: "
                   f"default={default_language}, fallback={fallback_language}")
    
    def _load_translations(self):
        """Carga el archivo de traducciones"""
        try:
            if not self.translations_file.exists():
                logger.error(f"❌ {self.translations_file} not found")
                raise FileNotFoundError(f"Translations file not found: {self.translations_file}")
            
            with open(self.translations_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Filtrar metadata
            self.translations = {k: v for k, v in data.items() if not k.startswith('_')}
            
            supported_langs = list(self.translations.keys())
            logger.info(f"✅ Loaded translations for: {', '.join(supported_langs)}")
            
            # Validar que existen los idiomas configurados
            if self.default_language not in self.translations:
                logger.warning(f"⚠️ Default language '{self.default_language}' not found")
            if self.fallback_language not in self.translations:
                logger.warning(f"⚠️ Fallback language '{self.fallback_language}' not found")
                
        except Exception as e:
            logger.error(f"❌ Error loading translations: {e}", exc_info=True)
            # Crear traducciones mínimas de emergencia
            self.translations = {
                "es": {"messages": {"error_generic": "❌ Error inesperado"}},
                "en": {"messages": {"error_generic": "❌ Unexpected error"}}
            }
    
    def set_user_language(self, user_id: int, language: str):
        """
        Establece el idioma para un usuario específico.
        
        Args:
            user_id: ID del usuario de Telegram
            language: Código de idioma ("es", "en", etc.)
        """
        if language in self.translations:
            self.user_languages[user_id] = language
            logger.info(f"🌍 User {user_id} language set to: {language}")
        else:
            logger.warning(f"⚠️ Language '{language}' not supported")
    
    def get_user_language(self, user_id: Optional[int] = None, 
                         user_language_code: Optional[str] = None) -> str:
        """
        Obtiene el idioma del usuario con auto-detección.
        
        Prioridad:
        1. Configuración manual del usuario (user_languages)
        2. Auto-detección desde Telegram (user_language_code)
        3. Default language
        
        Args:
            user_id: ID del usuario
            user_language_code: Código de idioma de Telegram ("es", "en-US", etc.)
        
        Returns:
            Código de idioma final
        """
        # 1. Usuario tiene configuración manual
        if user_id and user_id in self.user_languages:
            return self.user_languages[user_id]
        
        # 2. Auto-detección desde Telegram
        if self.auto_detect and user_language_code:
            # Extraer código base ("en-US" -> "en")
            lang_code = user_language_code.split('-')[0].lower()
            if lang_code in self.translations:
                # Guardar para futuras peticiones
                if user_id:
                    self.user_languages[user_id] = lang_code
                return lang_code
        
        # 3. Default
        return self.default_language
    
    @lru_cache(maxsize=512)
    def _get_nested_value(self, data: tuple, keys: tuple, default: Any = None) -> Any:
        """
        Obtiene valor anidado de diccionario de forma segura.
        Usa tuplas para hacer cache con lru_cache.
        
        Args:
            data: Tupla de items del diccionario
            keys: Tupla de claves separadas por punto
            default: Valor por defecto si no encuentra
        
        Returns:
            Valor encontrado o default
        """
        # Convertir tupla de vuelta a dict
        current = dict(data)
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current
    
    def get(self, key: str, language: str = None, **kwargs) -> str:
        """
        Obtiene una traducción con formateo de variables.
        
        Args:
            key: Clave de traducción con notación de punto ("commands.start.welcome")
            language: Idioma (None = usar default)
            **kwargs: Variables para formatear en el mensaje {var}
        
        Returns:
            String traducido y formateado
        
        Ejemplos:
            t.get("commands.scan.starting", count=10)
            t.get("messages.error_generic", language="en")
        """
        lang = language or self.default_language
        
        # Split key por puntos
        keys = key.split('.')
        
        # Intentar obtener de idioma solicitado
        if lang in self.translations:
            # Convertir a tupla para cache
            data_tuple = tuple(self.translations[lang].items())
            keys_tuple = tuple(keys)
            value = self._get_nested_value(data_tuple, keys_tuple)
            
            if value:
                # Formatear con variables si las hay
                try:
                    return value.format(**kwargs) if kwargs else value
                except KeyError as e:
                    logger.warning(f"⚠️ Missing variable {e} in translation: {key}")
                    return value
        
        # Fallback a idioma alternativo
        if self.fallback_language != lang and self.fallback_language in self.translations:
            data_tuple = tuple(self.translations[self.fallback_language].items())
            keys_tuple = tuple(keys)
            value = self._get_nested_value(data_tuple, keys_tuple)
            
            if value:
                logger.debug(f"🔄 Using fallback for key: {key}")
                try:
                    return value.format(**kwargs) if kwargs else value
                except KeyError:
                    return value
        
        # Último recurso: devolver la key misma
        logger.error(f"❌ Translation not found: {key} (lang: {lang})")
        return f"[{key}]"
    
    def __call__(self, key: str, user_id: Optional[int] = None, 
                user_language_code: Optional[str] = None, **kwargs) -> str:
        """
        Método shortcut para llamar como función: t(key, **kwargs)
        
        Detecta automáticamente el idioma del usuario.
        """
        language = self.get_user_language(user_id, user_language_code)
        return self.get(key, language=language, **kwargs)

# Instancia global singleton
t = TranslationManager()

# Función helper para importar fácilmente
def _(key: str, user_id: Optional[int] = None, 
     user_language_code: Optional[str] = None, **kwargs) -> str:
    """
    Función universal de traducción.
    
    Uso:
        from i18n import _
        
        msg = _("commands.start.welcome", 
               user_id=123, 
               app_name="Cazador", 
               version="v12.2")
    
    Args:
        key: Clave de traducción
        user_id: ID del usuario (para auto-detección)
        user_language_code: Código de idioma Telegram
        **kwargs: Variables para formatear
    
    Returns:
        String traducido
    """
    return t(key, user_id=user_id, user_language_code=user_language_code, **kwargs)

# Alias para botones
def btn(key: str, user_id: Optional[int] = None, **kwargs) -> str:
    """
    Helper específico para botones.
    
    Uso:
        from i18n import btn
        button_text = btn("scan", user_id=123)
    """
    return _(f"buttons.{key}", user_id=user_id, **kwargs)

if __name__ == "__main__":
    # Tests rápidos
    print("🌍 Testing TranslationManager...\n")
    
    # Test 1: Español
    print("Test 1 - Español:")
    msg_es = _("commands.start.welcome", 
              user_id=1, 
              user_language_code="es",
              app_name="Cazador Supremo",
              version="v12.2",
              commands_list="/scan, /route")
    print(msg_es)
    print()
    
    # Test 2: Inglés
    print("Test 2 - English:")
    msg_en = _("commands.start.welcome",
              user_id=2,
              user_language_code="en",
              app_name="Supreme Hunter",
              version="v12.2",
              commands_list="/scan, /route")
    print(msg_en)
    print()
    
    # Test 3: Botón
    print("Test 3 - Button:")
    btn_es = btn("scan", user_id=1)
    btn_en = btn("scan", user_id=2)
    print(f"ES: {btn_es}")
    print(f"EN: {btn_en}")
    print()
    
    # Test 4: Auto-detección
    print("Test 4 - Auto-detect:")
    t.set_user_language(999, "en")
    msg_auto = _("commands.scan.starting", user_id=999, count=5)
    print(msg_auto)
    print()
    
    print("✅ All tests passed!")
