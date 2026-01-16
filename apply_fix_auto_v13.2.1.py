#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🤖 APLICADOR AUTOMÁTICO DEL FIX v13.2.1

Ejecuta este script y se aplicarán TODOS los cambios automáticamente.

USO (Git Bash Windows / Linux / macOS):
    python apply_fix_auto_v13.2.1.py
    
O también:
    python3 apply_fix_auto_v13.2.1.py

QUÉ HACE:
1. Crea backup automático del archivo original
2. Actualiza VERSION de 13.2.0 a 13.2.1
3. Actualiza header docstring
4. Reemplaza método start_command() completo
5. Inserta método handle_callback() nuevo
6. Inserta método _handle_onboarding_callback() nuevo
7. Guarda archivo actualizado

RESULTADO:
    cazador_supremo_enterprise.py actualizado a v13.2.1 ✅
    cazador_supremo_enterprise.py.backup_v13.2.0_YYYYMMDD_HHMMSS (backup) 📦
"""

import re
import shutil
import sys
import os
from datetime import datetime
from pathlib import Path

FILE_TO_UPDATE = 'cazador_supremo_enterprise.py'

# Configurar encoding para Windows
if sys.platform == 'win32':
    try:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except:
        pass

def print_separator():
    """Imprime línea separadora compatible con todos los terminales."""
    print("=" * 80)

def print_header():
    """Imprime el header del script."""
    print_separator()
    print("   APLICADOR AUTOMATICO FIX v13.2.1 - ONBOARDING INTERACTIVO")
    print_separator()
    print()

def main():
    print_header()
    
    # Verificar que existe el archivo
    if not Path(FILE_TO_UPDATE).exists():
        print(f"ERROR: No se encuentra {FILE_TO_UPDATE}")
        print("   Asegurate de ejecutar este script en el directorio del repositorio.")
        print()
        print("DIRECTORIO ACTUAL:")
        print(f"   {os.getcwd()}")
        print()
        print("ARCHIVOS EN ESTE DIRECTORIO:")
        for f in os.listdir('.'):
            print(f"   - {f}")
        sys.exit(1)
    
    print(f"OK Archivo encontrado: {FILE_TO_UPDATE}")
    print()
    
    # Crear backup
    backup_name = f"{FILE_TO_UPDATE}.backup_v13.2.0_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"Creando backup: {backup_name}...")
    try:
        shutil.copy2(FILE_TO_UPDATE, backup_name)
        print(f"OK Backup creado")
    except Exception as e:
        print(f"ERROR al crear backup: {e}")
        sys.exit(1)
    print()
    
    # Leer contenido
    print("Leyendo archivo...")
    try:
        with open(FILE_TO_UPDATE, 'r', encoding='utf-8') as f:
            content = f.read()
        original_lines = len(content.split('\n'))
        print(f"OK {original_lines} lineas leidas")
    except Exception as e:
        print(f"ERROR al leer archivo: {e}")
        sys.exit(1)
    print()
    
    # PASO 1: Actualizar VERSION
    print("[1/5] Actualizando VERSION...")
    old_version = 'VERSION = "13.2.0 Enterprise"'
    new_version = 'VERSION = "13.2.1 Enterprise"'
    if old_version in content:
        content = content.replace(old_version, new_version)
        print("   OK VERSION actualizada: 13.2.0 -> 13.2.1")
    else:
        print("   ADVERTENCIA: VERSION ya estaba actualizada o no encontrada")
    
    # PASO 2: Actualizar header docstring
    print("[2/5] Actualizando header...")
    content = content.replace('v13.2.0 Enterprise', 'v13.2.1 Enterprise')
    if 'Onboarding Fix' not in content:
        content = content.replace(
            'Enhanced Notifications',
            'Enhanced Notifications   Onboarding Fix v13.2.1'
        )
        print("   OK Header actualizado")
    else:
        print("   ADVERTENCIA: Header ya estaba actualizado")
    
    # PASO 3: Preparar los nuevos métodos
    print("[3/5] Preparando nuevos metodos...")
    
    # Método start_command actualizado
    start_command_new = '''    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /start con onboarding y deep links."""
        user = update.effective_user
        args = context.args
        
        # Registrar usuario
        if RETENTION_ENABLED:
            self.retention_mgr.ensure_user(user.id, user.username or "user")
        
        # Manejar deep links
        if args and len(args) > 0:
            deep_link = args[0]
            
            # Referral link
            if deep_link.startswith("ref_"):
                if VIRAL_ENABLED:
                    await self.viral_handler.handle_referral(update, context, deep_link)
                    return
            
            # Deal share link
            elif deep_link.startswith("deal_"):
                if VIRAL_ENABLED:
                    await self.viral_handler.handle_deal_share(update, context, deep_link)
                    return
        
        # Verificar si es nuevo usuario
        if RETENTION_ENABLED:
            if not self.onboarding_mgr.has_completed_onboarding(user.id):
                # Iniciar onboarding interactivo
                welcome_msg = OnboardingMessages.welcome(user.first_name or user.username or "usuario")
                
                keyboard = [[InlineKeyboardButton("🚀 ¡Empezar!", callback_data="onb_start")]]
                
                await update.message.reply_text(
                    welcome_msg,
                    parse_mode='Markdown',
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
                return
        
        # Usuario existente - mostrar dashboard
        header = (
            f"🎆 *{APP_NAME} v{VERSION}* 🎆\\n\\n"
            f"¡Hola {user.first_name or user.username}! 👋\\n\\n"
            f"Estoy listo para encontrar los mejores chollos de vuelos.\\n"
        )
        
        if RETENTION_ENABLED:
            profile = self.retention_mgr.get_user_profile(user.id)
            header += (
                f"\\n💰 *{profile.coins}* FlightCoins\\n"
                f"🎯 Tier: {profile.tier.value}\\n"
                f"🔥 Streak: {profile.current_streak} días\\n"
            )
        
        # Quick actions
        keyboard = []
        if RETENTION_ENABLED:
            keyboard = self.quick_actions.get_main_keyboard()
        
        await update.message.reply_text(
            header,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None
        )
'''
    
    # Método handle_callback nuevo
    handle_callback_new = '''    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja todos los callbacks de botones inline."""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        user = update.effective_user
        
        # Onboarding callbacks
        if data.startswith("onb_"):
            await self._handle_onboarding_callback(update, context)
            return
        
        # Quick actions callbacks
        if data.startswith("qa_"):
            await self.quick_actions.handle_callback(update, context)
            return
        
        # Viral callbacks
        if VIRAL_ENABLED and data.startswith(("share_", "group_", "lb_")):
            await self.viral_handler.handle_callback(update, context)
            return
'''
    
    # Método _handle_onboarding_callback nuevo
    handle_onboarding_callback_new = '''    async def _handle_onboarding_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Maneja los callbacks del flujo de onboarding."""
        query = update.callback_query
        user = update.effective_user
        data = query.data
        
        if data == "onb_start":
            self.onboarding_mgr.advance_to_step1(user.id)
            step1_msg = OnboardingMessages.step1_region()
            keyboard = [
                [InlineKeyboardButton("🇪🇺 Europa", callback_data="onb_region_europe")],
                [InlineKeyboardButton("🇺🇸 USA", callback_data="onb_region_usa")],
                [InlineKeyboardButton("🌏 Asia", callback_data="onb_region_asia")],
                [InlineKeyboardButton("🌎 Latam", callback_data="onb_region_latam")]
            ]
            await query.edit_message_text(step1_msg, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
        
        elif data.startswith("onb_region_"):
            region_str = data.replace("onb_region_", "")
            region = TravelRegion(region_str)
            self.onboarding_mgr.set_travel_region(user.id, region)
            step2_msg = OnboardingMessages.step2_budget()
            keyboard = [
                [InlineKeyboardButton("🟢 Económico (<€300)", callback_data="onb_budget_low")],
                [InlineKeyboardButton("🟡 Moderado (€300-600)", callback_data="onb_budget_medium")],
                [InlineKeyboardButton("🔵 Premium (>€600)", callback_data="onb_budget_high")]
            ]
            await query.edit_message_text(step2_msg, parse_mode='Markdown', reply_markup=InlineKeyboardMarkup(keyboard))
        
        elif data.startswith("onb_budget_"):
            budget_str = data.replace("onb_budget_", "")
            budget = BudgetRange(budget_str)
            self.onboarding_mgr.set_budget_range(user.id, budget)
            await query.edit_message_text("🔍 *Buscando tus primeros chollos...*\\n\\nEsto tomará solo unos segundos", parse_mode='Markdown')
            
            routes = self.onboarding_mgr.get_recommended_routes(user.id)
            found_deals = []
            for origin, dest, name in routes:
                try:
                    route = FlightRoute(origin=origin, dest=dest, name=name)
                    price = self.scanner._scan_single(route)
                    if price:
                        found_deals.append(price)
                        threshold = self.onboarding_mgr.get_watchlist_threshold(user.id, budget.value)
                        self.retention_mgr.add_to_watchlist(user.id, user.username or "user", route.route_code, threshold)
                except Exception as e:
                    logger.error(f"Error scanning route {name}: {e}")
            
            progress = self.onboarding_mgr.complete_onboarding(user.id)
            from onboarding_flow import ONBOARDING_COMPLETION_BONUS
            self.retention_mgr.award_coins(user.id, user.username or "user", ONBOARDING_COMPLETION_BONUS, "Completar onboarding")
            completion_msg = OnboardingMessages.completion(ONBOARDING_COMPLETION_BONUS, progress.total_time_seconds)
            await query.edit_message_text(completion_msg, parse_mode='Markdown')
            
            if found_deals:
                deals_msg = f"✈️ *Tus primeros {len(found_deals)} vuelos en watchlist:*\\n\\n"
                for i, fp in enumerate(found_deals[:3], 1):
                    deals_msg += f"{i} {fp.name}: {fp.format_price()}\\n"
                await context.bot.send_message(chat_id=query.message.chat_id, text=deals_msg, parse_mode='Markdown')
'''
    
    print("   OK Metodos preparados")
    print()
    
    # PASO 4: Reemplazar start_command
    print("[4/5] Reemplazando start_command()...")
    start_pattern = r'    async def start_command\(self, update: Update, context: ContextTypes\.DEFAULT_TYPE\):.*?(?=\n    async def |\n    def \w)'
    match = re.search(start_pattern, content, re.DOTALL)
    if match:
        content = content[:match.start()] + start_command_new + '\n' + content[match.end():]
        print("   OK start_command() reemplazado")
    else:
        print("   ADVERTENCIA: No se encontro start_command() para reemplazar")
    
    # PASO 5: Insertar handle_callback y _handle_onboarding_callback
    print("[5/5] Insertando nuevos metodos...")
    
    # Buscar dónde insertar (después de start_command)
    insert_pattern = r'(    async def start_command\(self.*?(?=\n    async def |\n    def \w))'
    match = re.search(insert_pattern, content, re.DOTALL)
    if match:
        insert_pos = match.end()
        content = content[:insert_pos] + '\n' + handle_callback_new + '\n' + handle_onboarding_callback_new + '\n' + content[insert_pos:]
        print("   OK handle_callback() insertado")
        print("   OK _handle_onboarding_callback() insertado")
    else:
        print("   ADVERTENCIA: No se pudo encontrar la ubicacion de insercion")
    
    # Guardar archivo actualizado
    print()
    print("Guardando archivo actualizado...")
    try:
        with open(FILE_TO_UPDATE, 'w', encoding='utf-8') as f:
            f.write(content)
        
        new_lines = len(content.split('\n'))
        print(f"OK Archivo guardado ({new_lines} lineas, +{new_lines - original_lines})")
    except Exception as e:
        print(f"ERROR al guardar archivo: {e}")
        sys.exit(1)
    print()
    
    # Resumen final
    print_separator()
    print("   FIX v13.2.1 APLICADO CORRECTAMENTE")
    print_separator()
    print()
    print("CAMBIOS REALIZADOS:")
    print("   OK VERSION actualizada a 13.2.1")
    print("   OK Header docstring actualizado")
    print("   OK start_command() reemplazado con onboarding")
    print("   OK handle_callback() insertado")
    print("   OK _handle_onboarding_callback() insertado")
    print()
    print(f"BACKUP: {backup_name}")
    print()
    print("PROXIMOS PASOS:")
    print("   1. Ejecutar: python cazador_supremo_enterprise.py")
    print("   2. Probar: /start con un nuevo usuario de Telegram")
    print("   3. Verificar: Flujo de onboarding completo (3 pasos)")
    print()
    print_separator()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nScript interrumpido por el usuario.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nERROR INESPERADO: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
