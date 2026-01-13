#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Parche rápido para corregir error de callbacks en inline keyboards
Error: AttributeError: 'NoneType' object has no attribute 'reply_text'
"""

import sys

def apply_fix():
    print("🔧 Aplicando corrección de callbacks...")
    
    # Leer archivo
    try:
        with open('cazador_supremo_v12.0_enterprise.py', 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"❌ Error leyendo archivo: {e}")
        return False
    
    # Encontrar y corregir todas las funciones cmd_* que usan update.message.reply_text
    modified = False
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Si encontramos update.message.reply_text o reply_photo
        if 'await update.message.reply_text(' in line or 'await update.message.reply_photo(' in line:
            # Verificar si ya tiene el fix
            if i > 0 and 'update.callback_query.message if update.callback_query' not in lines[i-1]:
                indent = len(line) - len(line.lstrip())
                # Insertar línea de fix antes
                fix_line = ' ' * indent + 'message = update.callback_query.message if update.callback_query else update.message\n'
                lines.insert(i, fix_line)
                i += 1  # Saltar la línea que acabamos de insertar
                
                # Reemplazar update.message por message en la línea actual
                lines[i] = lines[i].replace('update.message.reply_text(', 'message.reply_text(')
                lines[i] = lines[i].replace('update.message.reply_photo(', 'message.reply_photo(')
                
                modified = True
                print(f"✅ Corregida línea {i+1}")
        
        i += 1
    
    if not modified:
        print("ℹ️  No se encontraron líneas para corregir (quizás ya estén corregidas)")
        return True
    
    # Guardar archivo corregido
    try:
        with open('cazador_supremo_v12.0_enterprise.py', 'w', encoding='utf-8') as f:
            f.writelines(lines)
        corrections = len([l for l in lines if 'update.callback_query.message if update.callback_query' in l])
        print(f"💾 Archivo guardado con {corrections} correcciones aplicadas")
        return True
    except Exception as e:
        print(f"❌ Error guardando archivo: {e}")
        return False

if __name__ == '__main__':
    print("="*60)
    print("  PARCHE CALLBACKS - Cazador Supremo v12.0")
    print("="*60)
    print()
    
    if apply_fix():
        print("\n✅ ¡Parche aplicado correctamente!")
        print("\n🚀 Ahora ejecuta: python cazador_supremo_v12.0_enterprise.py")
    else:
        print("\n❌ Error aplicando parche")
        sys.exit(1)
