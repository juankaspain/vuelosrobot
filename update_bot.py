#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de actualización automática del VuelosBot
Descarga la última versión desde GitHub
"""

import os
import sys
import urllib.request
import shutil
from pathlib import Path

GITHUB_RAW_URL = "https://raw.githubusercontent.com/juankaspain/vuelosrobot/main/vuelos_bot_unified.py"
LOCAL_FILE = "vuelos_bot_unified.py"
BACKUP_FILE = "vuelos_bot_unified.py.backup"

def update_bot():
    print("\n" + "="*70)
    print("🔄 Actualizador VuelosBot".center(70))
    print("="*70 + "\n")
    
    # Backup del archivo actual si existe
    if Path(LOCAL_FILE).exists():
        print(f"💾 Creando backup: {BACKUP_FILE}")
        shutil.copy2(LOCAL_FILE, BACKUP_FILE)
        print("✅ Backup creado\n")
    
    # Descargar nueva versión
    print("📥 Descargando última versión desde GitHub...")
    print(f"   URL: {GITHUB_RAW_URL}\n")
    
    try:
        with urllib.request.urlopen(GITHUB_RAW_URL) as response:
            content = response.read()
        
        # Guardar archivo
        with open(LOCAL_FILE, 'wb') as f:
            f.write(content)
        
        # Verificar versión descargada
        with open(LOCAL_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                if 'VERSION = ' in line:
                    version = line.split('"')[1]
                    print(f"✅ Descargado correctamente: v{version}\n")
                    break
        
        print("="*70)
        print("✅ Actualización completada exitosamente!".center(70))
        print("="*70)
        print("\n🚀 Ahora ejecuta: python vuelos_bot_unified.py setup\n")
        
    except Exception as e:
        print(f"\n❌ Error descargando: {e}")
        
        # Restaurar backup si existe
        if Path(BACKUP_FILE).exists():
            print(f"🔙 Restaurando backup...")
            shutil.copy2(BACKUP_FILE, LOCAL_FILE)
            print("✅ Backup restaurado\n")
        
        sys.exit(1)

if __name__ == "__main__":
    update_bot()