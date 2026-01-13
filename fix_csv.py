#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para limpiar el CSV corrupto de deals_history.csv
"""

import os
import pandas as pd
from pathlib import Path

CSV_FILE = "deals_history.csv"

def fix_csv():
    """Limpia y recrea el CSV con la estructura correcta"""
    
    if Path(CSV_FILE).exists():
        print(f"🗑️  Eliminando {CSV_FILE} corrupto...")
        os.remove(CSV_FILE)
        print("✅ Archivo eliminado")
    
    # Crear CSV con estructura correcta
    df = pd.DataFrame(columns=[
        'route', 'name', 'price', 'source', 'timestamp', 'confidence', 'metadata'
    ])
    
    df.to_csv(CSV_FILE, index=False, encoding='utf-8')
    print(f"✅ Nuevo {CSV_FILE} creado con estructura correcta")
    print("\n📋 Columnas: route, name, price, source, timestamp, confidence, metadata")
    print("\n🚀 Ya puedes ejecutar el bot de nuevo")

if __name__ == '__main__':
    fix_csv()
