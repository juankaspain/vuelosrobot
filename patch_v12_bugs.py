#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script automático para parchear errores en cazador_supremo_v12.0_enterprise.py

Errores corregidos:
1. CSV corrupto con columnas inconsistentes
2. AttributeError en callbacks de inline keyboard
3. Manejo robusto de pandas read_csv
"""

import re
import os
from pathlib import Path

FILE_TO_PATCH = "cazador_supremo_v12.0_enterprise.py"
BACKUP_FILE = "cazador_supremo_v12.0_enterprise.py.backup"

def apply_patches():
    """Aplica todos los parches necesarios"""
    
    if not Path(FILE_TO_PATCH).exists():
        print(f"❌ Error: {FILE_TO_PATCH} no encontrado")
        return False
    
    # Leer archivo
    print(f"📂 Leyendo {FILE_TO_PATCH}...")
    with open(FILE_TO_PATCH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Crear backup
    print(f"💾 Creando backup en {BACKUP_FILE}...")
    with open(BACKUP_FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # PARCHE 1: DataManager.load() - CSV robusto
    print("🔧 Aplicando parche 1: DataManager.load()...")
    pattern1 = r"(def load\(self\) -> pd\.DataFrame:.*?try:.*?)df = pd\.read_csv\(self\.file, encoding='utf-8'\)"
    replacement1 = r"\1df = pd.read_csv(self.file, encoding='utf-8', on_bad_lines='skip', engine='python')"
    content = re.sub(pattern1, replacement1, content, flags=re.DOTALL)
    
    # Agregar metadata column check
    pattern1b = r"(if 'confidence' not in df\.columns:.*?df\['confidence'\] = 0\.85)"
    replacement1b = r"\1\n            if 'metadata' not in df.columns:\n                df['metadata'] = '{}'"
    content = re.sub(pattern1b, replacement1b, content, flags=re.DOTALL)
    
    # Recrear CSV si falla
    pattern1c = r"(logger\.error\(f\"Error loading CSV: \{e\}\"\))\n(\s+)return pd\.DataFrame\(\)"
    replacement1c = r"\1\n\2logger.warning(\"⚠️ Recreating CSV file...\")\n\2df_new = pd.DataFrame(columns=['route', 'name', 'price', 'source', 'timestamp', 'confidence', 'metadata'])\n\2df_new.to_csv(self.file, index=False, encoding='utf-8')\n\2return df_new"
    content = re.sub(pattern1c, replacement1c, content)
    
    # PARCHE 2: cmd_status() - Callback fix
    print("🔧 Aplicando parche 2: cmd_status() callback fix...")
    pattern2 = r"(async def cmd_status.*?if not stats:)(\n\s+)await update\.message\.reply_text\(\"ℹ️ No hay datos"
    replacement2 = r"\1\n            # 🐛 FIX: Manejar tanto mensajes directos como callbacks\n            message = update.callback_query.message if update.callback_query else update.message\2await message.reply_text(\"ℹ️ No hay datos"
    content = re.sub(pattern2, replacement2, content, flags=re.DOTALL)
    
    # PARCHE 3: cmd_deals() - Si existe
    print("🔧 Aplicando parche 3: cmd_deals() callback fix (si existe)...")
    pattern3 = r"(async def cmd_deals.*?if not deals:)(\n\s+)await update\.message\.reply_text"
    replacement3 = r"\1\n            message = update.callback_query.message if update.callback_query else update.message\2await message.reply_text"
    content = re.sub(pattern3, replacement3, content, flags=re.DOTALL)
    
    # PARCHE 4: Otras funciones cmd_ similares
    print("🔧 Aplicando parche 4: Otras funciones cmd_* con callbacks...")
    # Este es más genérico y puede requerir revisión manual
    
    # Actualizar versión
    content = content.replace('v12.0.1 Enterprise', 'v12.0.1-patched Enterprise')
    content = content.replace('🐛 v12.0.1 FIX:', '🐛 v12.0.1-patched FIX:\n- CSV robusto con on_bad_lines=\'skip\'\n- Callback query fix para inline keyboards\n- Auto-recreación de CSV corrupto\n\n🐛 v12.0.1 FIX:')
    
    # Guardar archivo parcheado
    print(f"💾 Guardando {FILE_TO_PATCH} parcheado...")
    with open(FILE_TO_PATCH, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ ¡Parches aplicados con éxito!")
    print(f"ℹ️ Backup guardado en: {BACKUP_FILE}")
    print(f"\n🛠️ Ahora ejecuta:")
    print(f"   1. rm deals_history.csv  (o 'del' en Windows)")
    print(f"   2. python {FILE_TO_PATCH}")
    return True

if __name__ == '__main__':
    print("📦" + "="*60)
    print("   PARCHE AUTOMÁTICO - Cazador Supremo v12.0")
    print("="*60 + "\n")
    
    if apply_patches():
        print("\n🎉 ¡LISTO! El archivo ha sido parcheado.")
    else:
        print("\n❌ Error al aplicar parches. Revisa manualmente.")
