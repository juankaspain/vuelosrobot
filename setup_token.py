#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configurador del Token de VuelosBot
Método NO interactivo - Compatible 100% con Git Bash
"""

import sys
import json
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
CONFIG_FILE = DATA_DIR / "bot_config.json"

DEFAULT_CONFIG = {
    "telegram": {"token": "", "admin_users": []},
    "api_keys": {"skyscanner": "", "kiwi": "", "google_flights": ""},
    "features": {
        "demo_mode": True,
        "max_alerts_per_user": 5,
        "max_searches_per_day": 20,
        "cache_ttl_hours": 6,
        "alert_check_interval_hours": 2
    },
    "defaults": {"currency": "EUR", "language": "es", "cabin_class": "economy"}
}

def setup_token(token: str):
    """Configura el token sin interacción."""
    
    print("\n" + "="*70)
    print("🔧 Configurador de Token - VuelosBot".center(70))
    print("="*70 + "\n")
    
    # Cargar o crear config
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print("✅ Configuración existente cargada")
    else:
        config = DEFAULT_CONFIG.copy()
        print("🆕 Creando nueva configuración")
    
    # Actualizar token
    config['telegram']['token'] = token
    config['features']['demo_mode'] = True
    
    # Guardar
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Token guardado en: {CONFIG_FILE}")
    print(f"   Token: {token[:10]}...{token[-10:]}")
    print(f"   Modo: DEMO activado\n")
    
    print("="*70)
    print("✅ Configuración completada!".center(70))
    print("="*70)
    print("\n🚀 Ahora ejecuta: python vuelos_bot_unified.py\n")

def show_usage():
    """Muestra instrucciones de uso."""
    print("\n" + "="*70)
    print("🔧 Setup Token - VuelosBot".center(70))
    print("="*70)
    print("\n📝 USO:\n")
    print("   python setup_token.py YOUR_TOKEN_HERE\n")
    print("💡 EJEMPLO:\n")
    print("   python setup_token.py 8543611357:AAH_X0A79CDV7vzM4_T8uOv6WLjjs6TBLQo\n")
    print("🔑 OBTENER TOKEN:\n")
    print("   1. Abre Telegram")
    print("   2. Busca @BotFather")
    print("   3. Envía: /newbot")
    print("   4. Sigue las instrucciones")
    print("   5. Copia el token que te da\n")
    print(f"📁 Config: {CONFIG_FILE}\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        show_usage()
        sys.exit(1)
    
    token = sys.argv[1].strip()
    
    if not token or len(token) < 20:
        print("\n❌ Token inválido - debe tener al menos 20 caracteres\n")
        show_usage()
        sys.exit(1)
    
    setup_token(token)