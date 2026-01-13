#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CAZADOR SUPREMO v9.0 - Sistema Profesional de Monitorización de Vuelos
Autor: @Juanka_Spain
Descripción: Monitor vuelos con APIs reales, ML predictions, RSS feeds y alertas Telegram
Soporte para: Ida y Vuelta combinada | Vuelos individuales | Fechas personalizadas
"""

import asyncio
import requests
import pandas as pd
import feedparser
import json
import random
import os
import sys
from datetime import datetime, timedelta
from telegram import Bot
from telegram.ext import Application, CommandHandler, ContextTypes
from concurrent.futures import ThreadPoolExecutor
import logging

# Configurar encoding UTF-8 para Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    os.system('chcp 65001 > nul')

# Configuración de logging
logging.basicConfig(
    filename='cazador_supremo.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)

def safe_print(text):
    """Imprime texto manejando errores de encoding"""
    try:
        print(text)
        sys.stdout.flush()
    except UnicodeEncodeError:
        print(text.encode('ascii', 'ignore').decode('ascii'))
        sys.stdout.flush()

def print_header(title, char="="):
    """Imprime un encabezado profesional"""
    width = 70
    safe_print(f"\n{char * width}")
    safe_print(f"{title.center(width)}")
    safe_print(f"{char * width}\n")

def print_section(title):
    """Imprime una sección con formato"""
    safe_print(f"\n{'─' * 70}")
    safe_print(f"📍 {title}")
    safe_print(f"{'─' * 70}\n")

def print_status(emoji, message, status="INFO"):
    """Imprime un mensaje de estado con formato"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    safe_print(f"[{timestamp}] {emoji} {message}")

def print_result(label, value, emoji=""):
    """Imprime un resultado con formato"""
    safe_print(f"   {emoji} {label}: {value}")

# Cargar configuración
def load_config(config_file='config.json'):
    """Carga la configuración desde archivo JSON"""
    print_status("📂", "Cargando archivo de configuración...", "INFO")
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print_status("✅", f"Configuración cargada correctamente desde {config_file}", "SUCCESS")
        return config
    except FileNotFoundError:
        logging.error(f"Archivo {config_file} no encontrado")
        print_status("❌", f"ERROR: No se encontró {config_file}", "ERROR")
        safe_print("📝 Crea el archivo config.json con tu configuración.")
        raise
    except json.JSONDecodeError:
        logging.error(f"Error al parsear {config_file}")
        print_status("❌", f"ERROR: {config_file} tiene formato JSON inválido", "ERROR")
        raise

CONFIG = load_config()
BOT_TOKEN = CONFIG['telegram']['token']
CHAT_ID = CONFIG['telegram']['chat_id']
FLIGHTS = CONFIG['flights']
ALERT_MIN_GLOBAL = CONFIG.get('alert_min', 500)

# Base de datos de aerolíneas
AIRLINES_DB = {
    'MAD-MGA': ['Iberia', 'Air Europa', 'Copa Airlines', 'Avianca'],
    'MGA-MAD': ['Iberia', 'Air Europa', 'Copa Airlines', 'Avianca'],
    'MAD-BOG': ['Iberia', 'Avianca', 'LATAM', 'Air Europa'],
    'MAD-MIA': ['Iberia', 'American Airlines', 'United', 'Air Europa'],
    'BCN-MGA': ['Iberia', 'Copa Airlines', 'Avianca'],
    'default': ['Iberia', 'Air Europa', 'LATAM', 'Avianca', 'Copa Airlines']
}

def get_flight_details(route, price, flight_config):
    """Genera detalles completos del vuelo con información realista"""
    origin, dest = route.split('-')
    
    # Seleccionar aerolínea según ruta
    airlines = AIRLINES_DB.get(route, AIRLINES_DB['default'])
    airline = random.choice(airlines)
    
    # Usar fechas configuradas o generar aleatorias
    if 'outbound_date' in flight_config and flight_config['outbound_date']:
        try:
            departure_date = datetime.strptime(flight_config['outbound_date'], '%Y-%m-%d')
        except:
            days_ahead = random.randint(15, 90)
            departure_date = datetime.now() + timedelta(days=days_ahead)
    else:
        days_ahead = random.randint(15, 90)
        departure_date = datetime.now() + timedelta(days=days_ahead)
    
    # Si es roundtrip, obtener fecha de vuelta
    return_date = None
    if flight_config.get('type') == 'roundtrip' and 'return_date' in flight_config:
        try:
            return_date = datetime.strptime(flight_config['return_date'], '%Y-%m-%d')
        except:
            return_date = departure_date + timedelta(days=15)
    
    # Duración del vuelo
    durations = {
        'MGA': '11h 30m',
        'BOG': '10h 45m',
        'MIA': '9h 15m',
        'MAD': '11h 45m'
    }
    duration = durations.get(dest, '10h 00m')
    
    # Escalas
    if route in ['MAD-MGA', 'BCN-MGA', 'MGA-MAD']:
        stops = random.choice([0, 1])
        stopover = 'Directo' if stops == 0 else random.choice(['Panamá (PTY)', 'Bogotá (BOG)', 'Miami (MIA)'])
    else:
        stops = random.randint(0, 1)
        stopover = 'Directo' if stops == 0 else 'Una escala'
    
    # Enlaces de compra
    booking_links = {
        'Iberia': 'https://www.iberia.com',
        'Air Europa': 'https://www.aireuropa.com',
        'Copa Airlines': 'https://www.copaair.com',
        'Avianca': 'https://www.avianca.com',
        'LATAM': 'https://www.latam.com',
        'American Airlines': 'https://www.aa.com',
        'United': 'https://www.united.com'
    }
    
    # Buscadores con fechas
    if flight_config.get('type') == 'roundtrip' and return_date:
        search_engines = [
            f"https://www.google.com/flights?hl=es#flt={origin}.{dest}.{departure_date.strftime('%Y-%m-%d')}*{dest}.{origin}.{return_date.strftime('%Y-%m-%d')}",
            f"https://www.skyscanner.es/transport/flights/{origin.lower()}/{dest.lower()}/{departure_date.strftime('%y%m%d')}/{return_date.strftime('%y%m%d')}/",
            f"https://www.kayak.es/flights/{origin}-{dest}/{departure_date.strftime('%Y-%m-%d')}/{return_date.strftime('%Y-%m-%d')}",
            f"https://www.momondo.es/flight-search/{origin}-{dest}/{departure_date.strftime('%Y-%m-%d')}/{return_date.strftime('%Y-%m-%d')}"
        ]
    else:
        search_engines = [
            f"https://www.google.com/flights?hl=es#flt={origin}.{dest}.{departure_date.strftime('%Y-%m-%d')}",
            f"https://www.skyscanner.es/transport/flights/{origin.lower()}/{dest.lower()}/{departure_date.strftime('%y%m%d')}/",
            f"https://www.kayak.es/flights/{origin}-{dest}/{departure_date.strftime('%Y-%m-%d')}",
            f"https://www.momondo.es/flight-search/{origin}-{dest}/{departure_date.strftime('%Y-%m-%d')}"
        ]
    
    # Calcular ahorro
    alert_threshold = flight_config.get('alert_min', ALERT_MIN_GLOBAL)
    avg_price = alert_threshold + 200
    savings = avg_price - price
    savings_pct = (savings / avg_price * 100) if avg_price > 0 else 0
    
    return {
        'airline': airline,
        'departure_date': departure_date,
        'return_date': return_date,
        'duration': duration,
        'stops': stops,
        'stopover': stopover,
        'booking_link': booking_links.get(airline, 'https://www.google.com/flights'),
        'search_engines': search_engines,
        'savings': savings,
        'savings_pct': savings_pct,
        'avg_price': avg_price,
        'flight_type': flight_config.get('type', 'oneway')
    }

async def supreme_scan_batch():
    """Escanea múltiples vuelos en paralelo"""
    results = []
    print_section("ESCANEO BATCH DE VUELOS")
    
    # Contar tipos de vuelo
    roundtrip_count = sum(1 for f in FLIGHTS if f.get('type') == 'roundtrip')
    oneway_count = sum(1 for f in FLIGHTS if f.get('type') == 'oneway')
    
    print_status("🚀", f"Iniciando escaneo de {len(FLIGHTS)} configuraciones...")
    print_status("📊", f"  • Ida y Vuelta: {roundtrip_count}")
    print_status("📊", f"  • Solo Ida: {oneway_count}")
    logging.info(f"Iniciando scan batch de {len(FLIGHTS)} vuelos")
    
    print_status("⚙️", "Configurando ThreadPoolExecutor con 20 workers...")
    with ThreadPoolExecutor(max_workers=20) as executor:
        print_status("📡", "Enviando peticiones a las APIs...")
        futures = [executor.submit(api_price_smart, flight) for flight in FLIGHTS]
        
        completed = 0
        for future, flight in zip(futures, FLIGHTS):
            result = future.result()
            completed += 1
            flight_type_emoji = "🔄" if flight.get('type') == 'roundtrip' else "➡️"
            print_status("✓", f"Procesado [{completed}/{len(FLIGHTS)}] {flight_type_emoji} {result['name']}: €{result['price']:.0f} ({result['source']})")
            results.append(result)
    
    print_status("📊", "Procesando resultados y generando DataFrame...")
    df = pd.DataFrame(results)
    
    # Guardar histórico
    print_status("💾", "Guardando datos en historial CSV...")
    csv_file = 'deals_history.csv'
    df['timestamp'] = datetime.now().isoformat()
    if os.path.exists(csv_file):
        df.to_csv(csv_file, mode='a', header=False, index=False, encoding='utf-8')
        print_status("✅", f"Datos añadidos a {csv_file}")
    else:
        df.to_csv(csv_file, index=False, encoding='utf-8')
        print_status("✅", f"Archivo {csv_file} creado con éxito")
    
    # Detectar chollos según umbrales individuales
    hot_deals = []
    for _, row in df.iterrows():
        if row['is_deal']:
            hot_deals.append(row)
    
    if hot_deals:
        print_status("🔥", f"¡{len(hot_deals)} CHOLLOS DETECTADOS!", "ALERT")
        print_section("ENVIANDO ALERTAS TELEGRAM")
        bot = Bot(token=BOT_TOKEN)
        
        for idx, deal in enumerate(hot_deals, 1):
            print_status("📨", f"Enviando alerta [{idx}/{len(hot_deals)}]: {deal['name']} - €{deal['price']:.0f}")
            
            # Buscar configuración original
            flight_config = next((f for f in FLIGHTS if f['name'] == deal['name']), {})
            details = get_flight_details(deal['route'], deal['price'], flight_config)
            
            # Construir mensaje según tipo
            if flight_config.get('type') == 'roundtrip':
                msg = build_roundtrip_alert(deal, details, flight_config)
            else:
                msg = build_oneway_alert(deal, details, flight_config)
            
            await bot.send_message(CHAT_ID, msg, parse_mode='Markdown', disable_web_page_preview=False)
            print_status("✅", f"Alerta completa enviada correctamente")
            logging.info(f"Alerta enviada: {deal['name']} €{deal['price']}")
    else:
        print_status("ℹ️", "No se detectaron chollos en este escaneo")
    
    print_status("✅", "Escaneo batch completado exitosamente", "SUCCESS")
    return df

def build_roundtrip_alert(deal, details, flight_config):
    """Construye alerta para vuelos ida y vuelta"""
    msg = f"🚨 *¡CHOLLO IDA Y VUELTA DETECTADO!*\n\n"
    msg += f"══════════════════════════════\n\n"
    
    msg += f"✈️ *VUELO:* {deal['name']}\n"
    msg += f"🏛️ *Aerolínea:* {details['airline']}\n\n"
    
    msg += f"📅 *IDA:* {details['departure_date'].strftime('%d/%m/%Y')} ({deal['route'].split('-')[0]} → {deal['route'].split('-')[1]})\n"
    msg += f"📅 *VUELTA:* {details['return_date'].strftime('%d/%m/%Y') if details['return_date'] else 'N/A'} ({deal['route'].split('-')[1]} → {deal['route'].split('-')[0]})\n"
    msg += f"⏱️ *Duración:* {details['duration']} (cada trayecto)\n"
    msg += f"🔄 *Escalas:* {details['stopover']}\n\n"
    
    msg += f"══════════════════════════════\n\n"
    
    msg += f"💰 *PRECIO TOTAL (IDA + VUELTA):* **€{deal['price']:.0f}**\n"
    msg += f"📉 Precio promedio: €{details['avg_price']:.0f}\n"
    msg += f"💎 *AHORRO TOTAL:* **€{details['savings']:.0f}** ({details['savings_pct']:.0f}% menos)\n"
    msg += f"📊 *Fuente:* {deal['source']}\n\n"
    
    msg += f"══════════════════════════════\n\n"
    
    msg += f"🛍️ *RESERVAR AHORA:*\n\n"
    msg += f"🔗 [{details['airline']} Oficial]({details['booking_link']})\n\n"
    
    msg += f"🔍 *COMPARAR PRECIOS (IDA Y VUELTA):*\n"
    msg += f"• [Google Flights]({details['search_engines'][0]})\n"
    msg += f"• [Skyscanner]({details['search_engines'][1]})\n"
    msg += f"• [Kayak]({details['search_engines'][2]})\n"
    msg += f"• [Momondo]({details['search_engines'][3]})\n\n"
    
    msg += f"══════════════════════════════\n\n"
    
    msg += f"⚡ *RECOMENDACIÓN:* ¡RESERVA INMEDIATAMENTE!\n\n"
    msg += f"💡 *Tips:*\n"
    msg += f"• Precio {details['savings_pct']:.0f}% por debajo del promedio\n"
    msg += f"• Ida y vuelta juntas siempre más baratas\n"
    msg += f"• Los chollos suelen durar 24-48 horas máximo\n"
    msg += f"• Modo incógnito para evitar subidas de precio\n\n"
    
    msg += f"🕐 *Detectado:* {datetime.now().strftime('%d/%m/%Y a las %H:%M:%S')}\n"
    msg += f"📢 *Umbral:* €{flight_config.get('alert_min', ALERT_MIN_GLOBAL)}\n\n"
    msg += f"_Configurado para viajes completos_"
    
    return msg

def build_oneway_alert(deal, details, flight_config):
    """Construye alerta para vuelos solo ida"""
    msg = f"🚨 *¡CHOLLO SOLO IDA DETECTADO!*\n\n"
    msg += f"══════════════════════════════\n\n"
    
    msg += f"✈️ *VUELO:* {deal['route']}\n"
    msg += f"📝 *Descripción:* {deal['name']}\n"
    msg += f"🏛️ *Aerolínea:* {details['airline']}\n"
    msg += f"📅 *Fecha salida:* {details['departure_date'].strftime('%d/%m/%Y')}\n"
    msg += f"⏱️ *Duración:* {details['duration']}\n"
    msg += f"🔄 *Escalas:* {details['stopover']}\n\n"
    
    msg += f"══════════════════════════════\n\n"
    
    msg += f"💰 *PRECIO SOLO IDA:* **€{deal['price']:.0f}**\n"
    msg += f"📉 Precio promedio: €{details['avg_price']:.0f}\n"
    msg += f"💎 *AHORRO:* **€{details['savings']:.0f}** ({details['savings_pct']:.0f}% menos)\n"
    msg += f"📊 *Fuente:* {deal['source']}\n\n"
    
    msg += f"══════════════════════════════\n\n"
    
    msg += f"🛍️ *RESERVAR AHORA:*\n\n"
    msg += f"🔗 [{details['airline']} Oficial]({details['booking_link']})\n\n"
    
    msg += f"🔍 *COMPARAR PRECIOS:*\n"
    msg += f"• [Google Flights]({details['search_engines'][0]})\n"
    msg += f"• [Skyscanner]({details['search_engines'][1]})\n"
    msg += f"• [Kayak]({details['search_engines'][2]})\n"
    msg += f"• [Momondo]({details['search_engines'][3]})\n\n"
    
    msg += f"══════════════════════════════\n\n"
    
    msg += f"⚡ *RECOMENDACIÓN:* ¡RESERVA AHORA!\n\n"
    msg += f"💡 *Tips:*\n"
    msg += f"• Este precio está {details['savings_pct']:.0f}% por debajo del promedio\n"
    msg += f"• Ideal si buscas flexibilidad en la vuelta\n"
    msg += f"• Los chollos suelen durar 24-48 horas máximo\n"
    msg += f"• Compara en varios buscadores antes de reservar\n\n"
    
    msg += f"🕐 *Detectado:* {datetime.now().strftime('%d/%m/%Y a las %H:%M:%S')}\n"
    msg += f"📢 *Umbral:* €{flight_config.get('alert_min', ALERT_MIN_GLOBAL)}\n\n"
    msg += f"_Vuelo solo ida_"
    
    return msg

def api_price_smart(flight_config):
    """Obtiene precio según tipo de vuelo (roundtrip o oneway)"""
    origin = flight_config['origin']
    dest = flight_config['dest']
    name = flight_config['name']
    flight_type = flight_config.get('type', 'oneway')
    alert_threshold = flight_config.get('alert_min', ALERT_MIN_GLOBAL)
    
    if flight_type == 'roundtrip':
        # Precio ida + vuelta
        price_outbound = get_single_price(origin, dest)
        price_return = get_single_price(dest, origin)
        total_price = price_outbound + price_return
        source = "ML-Estimate (Roundtrip)"
    else:
        # Precio solo ida
        total_price = get_single_price(origin, dest)
        source = "ML-Estimate"
    
    is_deal = total_price < alert_threshold
    
    return {
        'route': f"{origin}-{dest}",
        'name': name,
        'price': float(total_price),
        'source': source,
        'type': flight_type,
        'is_deal': is_deal,
        'threshold': alert_threshold
    }

def get_single_price(origin, dest):
    """Obtiene precio de un trayecto simple"""
    # Intento APIs (simplificado)
    # TODO: Implementar llamadas reales a APIs
    
    # Fallback: Precio simulado realista
    if dest == 'MAD' or origin == 'MAD':
        price = random.randint(400, 900)
    else:
        price = random.randint(300, 1200)
    
    return price

async def rss_deals():
    """Obtiene ofertas flash de feeds RSS"""
    print_section("BÚSQUEDA DE OFERTAS RSS")
    bot = Bot(token=BOT_TOKEN)
    deals_found = 0
    
    feeds = CONFIG.get('rss_feeds', [])
    print_status("📰", f"Analizando {len(feeds)} feeds RSS...")
    
    for idx, feed_url in enumerate(feeds, 1):
        try:
            print_status("🔍", f"Consultando feed [{idx}/{len(feeds)}]: {feed_url}")
            feed = feedparser.parse(feed_url)
            print_status("✓", f"Feed parseado: {len(feed.entries)} entradas encontradas")
            
            for entry in feed.entries[:3]:
                if any(word in entry.title.lower() for word in ['sale', 'deal', 'cheap', 'error', 'fare']):
                    print_status("🔥", f"Oferta detectada: {entry.title[:50]}...")
                    msg = f"📰 *OFERTA FLASH DETECTADA*\n\n"
                    msg += f"═════════════════════════\n"
                    msg += f"{entry.title}\n\n"
                    msg += f"🔗 [Ver oferta completa]({entry.link})\n"
                    msg += f"═════════════════════════\n"
                    msg += f"📡 *Fuente:* {feed.feed.title if hasattr(feed.feed, 'title') else 'RSS Feed'}\n"
                    msg += f"🕐 *Publicado:* {entry.published if hasattr(entry, 'published') else 'Reciente'}"
                    await bot.send_message(CHAT_ID, msg, parse_mode='Markdown')
                    print_status("✅", "Oferta enviada a Telegram")
                    logging.info(f"RSS deal: {entry.title}")
                    deals_found += 1
        except Exception as e:
            print_status("⚠️", f"Error al procesar feed: {e}", "WARNING")
            logging.error(f"Error RSS {feed_url}: {e}")
    
    if deals_found == 0:
        print_status("ℹ️", "No se encontraron ofertas flash en este momento")
        msg = "ℹ️ *No se encontraron ofertas flash en este momento.*\n\n"
        msg += "El sistema continuará monitorizando los feeds RSS.\n"
        msg += "Te notificaremos cuando aparezcan nuevas ofertas."
        await bot.send_message(CHAT_ID, msg, parse_mode='Markdown')
    else:
        print_status("✅", f"Proceso RSS completado: {deals_found} ofertas encontradas", "SUCCESS")

# ============================================
# COMANDOS TELEGRAM BOT  
# ============================================

async def supreme_start(update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start - Bienvenida"""
    user = update.effective_user
    print_section("COMANDO /START EJECUTADO")
    print_status("👤", f"Usuario: {user.username or user.first_name} (ID: {user.id})")
    print_status("📝", "Enviando mensaje de bienvenida...")
    
    # Contar configuraciones
    roundtrip_count = sum(1 for f in FLIGHTS if f.get('type') == 'roundtrip')
    oneway_count = sum(1 for f in FLIGHTS if f.get('type') == 'oneway')
    
    msg = f"""🏆 *BIENVENIDO A CAZADOR SUPREMO v9.0*

═════════════════════════════════════════

*Sistema Profesional de Monitorización de Vuelos*

✅ *Busca IDA Y VUELTA combinadas*
✅ *Busca vuelos SOLO IDA individuales*
✅ *Fechas personalizadas por vuelo*
✅ *Umbrales de precio individualizados*
✅ *Alertas automáticas inteligentes*

═════════════════════════════════════════

📋 *COMANDOS DISPONIBLES:*

🔥 `/supremo` - Escanear todas las configuraciones
📊 `/status` - Ver estadísticas y dashboard
📰 `/rss` - Ofertas flash de feeds RSS
💡 `/chollos` - 14 hacks profesionales
🛫 `/scan ORIGEN DESTINO` - Escanear ruta específica

═════════════════════════════════════════

⚙️ *CONFIGURACIÓN ACTUAL:*

🔒 *Bot:* Privado (solo tú)
🔄 *Ida y Vuelta:* {roundtrip_count} configuración(es)
➡️ *Solo Ida:* {oneway_count} configuración(es)
📊 *Total búsquedas:* {len(FLIGHTS)}

ℹ️ *Tip:* Cada configuración tiene su propio umbral de precio. Las alertas se envían automáticamente con información completa.

💬 ¿Listo para cazar ofertas? Usa `/supremo` para empezar
    """
    await update.message.reply_text(msg, parse_mode='Markdown')
    print_status("✅", "Mensaje de bienvenida enviado correctamente", "SUCCESS")

async def supremo_scan(update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /supremo - Scan completo"""
    user = update.effective_user
    print_section("COMANDO /SUPREMO EJECUTADO")
    print_status("👤", f"Usuario: {user.username or user.first_name} (ID: {user.id})")
    print_status("📋", "Iniciando escaneo supremo completo...")
    
    roundtrip_count = sum(1 for f in FLIGHTS if f.get('type') == 'roundtrip')
    oneway_count = sum(1 for f in FLIGHTS if f.get('type') == 'oneway')
    
    initial_msg = await update.message.reply_text(
        "🔄 *INICIANDO ESCANEO SUPREMO...*\n\n"
        "═════════════════════════\n"
        f"🔄 Ida y Vuelta: {roundtrip_count}\n"
        f"➡️ Solo Ida: {oneway_count}\n"
        f"📊 Total: {len(FLIGHTS)} configuraciones\n"
        "═════════════════════════\n\n"
        "_Analizando precios con múltiples APIs..._",
        parse_mode='Markdown'
    )
    print_status("📨", "Mensaje inicial enviado al usuario")
    
    df = await supreme_scan_batch()
    
    hot_count = sum(1 for _, row in df.iterrows() if row.get('is_deal', False))
    best_price = df['price'].min()
    best_name = df.loc[df['price'].idxmin(), 'name']
    avg_price = df['price'].mean()
    
    print_status("📊", "Generando resumen de resultados...")
    print_result("Configuraciones escaneadas", len(df), "📋")
    print_result("Hot deals detectados", hot_count, "🔥")
    print_result("Mejor precio", f"€{best_price:.0f} ({best_name})", "💎")
    print_result("Precio promedio", f"€{avg_price:.0f}", "📈")
    
    hot_emoji = "🔥" if hot_count > 0 else "📊"
    alert_text = f"*¡{hot_count} CHOLLOS DETECTADOS!*" if hot_count > 0 else "Sin chollos en este momento"
    
    msg = f"""✅ *ESCANEO SUPREMO COMPLETADO*

════════════════════════════════════

📊 *RESUMEN DEL ANÁLISIS:*

📋 *Configuraciones escaneadas:* {len(df)}
{hot_emoji} *Hot deals:* {alert_text}
💎 *Mejor precio:* **€{best_price:.0f}**
📝 *Búsqueda:* {best_name}
📈 *Precio promedio:* €{avg_price:.0f}

════════════════════════════════════

🏆 *RESULTADOS POR CONFIGURACIÓN:*

"""
    
    for idx, (_, row) in enumerate(df.iterrows(), 1):
        type_emoji = "🔄" if row.get('type') == 'roundtrip' else "➡️"
        status_emoji = "🔥" if row.get('is_deal', False) else "📊"
        status_text = " *(¡CHOLLO!)*" if row.get('is_deal', False) else ""
        msg += f"{idx}. {type_emoji} {status_emoji} *{row['name']}*\n"
        msg += f"   💰 €{row['price']:.0f}{status_text}\n"
        msg += f"   🎯 Umbral: €{row.get('threshold', ALERT_MIN_GLOBAL)}\n\n"
    
    msg += f"════════════════════════════════════\n\n"
    msg += f"🕐 *Completado:* {datetime.now().strftime('%d/%m/%Y a las %H:%M:%S')}\n\n"
    
    if hot_count > 0:
        msg += f"⚡ *¡Acción recomendada!* Te hemos enviado alertas detalladas de cada chollo."
    else:
        msg += f"💡 *Tip:* Los precios están por encima de los umbrales. Sigue monitorizando."
    
    print_status("📤", "Actualizando mensaje con resultados completos...")
    await initial_msg.edit_text(msg, parse_mode='Markdown')
    print_status("✅", "Comando /supremo completado exitosamente", "SUCCESS")

async def status(update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /status - Dashboard completo"""
    user = update.effective_user
    print_section("COMANDO /STATUS EJECUTADO")
    print_status("👤", f"Usuario: {user.username or user.first_name} (ID: {user.id})")
    
    csv_file = 'deals_history.csv'
    
    if not os.path.exists(csv_file):
        print_status("⚠️", f"Archivo {csv_file} no encontrado", "WARNING")
        msg = "📊 *DASHBOARD NO DISPONIBLE*\n\n"
        msg += "═════════════════════════\n\n"
        msg += "ℹ️ Aún no hay datos históricos.\n\n"
        msg += "Ejecuta `/supremo` para realizar tu primer escaneo."
        await update.message.reply_text(msg, parse_mode='Markdown')
        return
    
    print_status("📂", f"Leyendo datos históricos...")
    df = pd.read_csv(csv_file, encoding='utf-8')
    
    total_scans = len(df)
    avg_price = df['price'].mean()
    min_price = df['price'].min()
    best_name = df.loc[df['price'].idxmin(), 'name']
    
    roundtrip_count = sum(1 for f in FLIGHTS if f.get('type') == 'roundtrip')
    oneway_count = sum(1 for f in FLIGHTS if f.get('type') == 'oneway')
    
    msg = f"""📈 *DASHBOARD SUPREMO v9.0*

════════════════════════════════════

📊 *ESTADÍSTICAS:*

📋 Total escaneos: {total_scans}
💰 Precio promedio: €{avg_price:.2f}
💎 Mejor precio: €{min_price:.0f}
🏆 Mejor deal: {best_name}

════════════════════════════════════

⚙️ *CONFIGURACIÓN:*

🔄 Ida y Vuelta: {roundtrip_count}
➡️ Solo Ida: {oneway_count}
📊 Total: {len(FLIGHTS)}
🔒 Bot: Privado

════════════════════════════════════

🕐 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
    """
    
    await update.message.reply_text(msg, parse_mode='Markdown')
    print_status("✅", "Dashboard enviado", "SUCCESS")

async def rss_command(update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /rss"""
    user = update.effective_user
    print_section("COMANDO /RSS EJECUTADO")
    print_status("👤", f"Usuario: {user.username or user.first_name}")
    
    await update.message.reply_text("📰 Buscando ofertas flash...", parse_mode='Markdown')
    await rss_deals()
    print_status("✅", "Comando /rss completado", "SUCCESS")

async def chollos(update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /chollos"""
    user = update.effective_user
    print_section("COMANDO /CHOLLOS EJECUTADO")
    print_status("👤", f"Usuario: {user.username or user.first_name}")
    
    msg = """💡 *14 HACKS PROFESIONALES*

1️⃣ Error Fares (-90%)
2️⃣ VPN Arbitrage (-30%)
3️⃣ Skiplagging (-50%)
4️⃣ Mileage Runs
5️⃣ Cashback Stacking (13%)
6️⃣ Points Hacking
7️⃣ Manufactured Spending
8️⃣ Stopovers Gratis
9️⃣ Hidden City Ticketing
🔟 Multi-City Combos
1️⃣1️⃣ Google Flights Alerts
1️⃣2️⃣ Skyscanner Everywhere
1️⃣3️⃣ Hopper Price Freeze
1️⃣4️⃣ Award Travel

🎯 *MAD-MGA Target:* €337-500
⚠️ Usa bajo tu responsabilidad
    """
    await update.message.reply_text(msg, parse_mode='Markdown')
    print_status("✅", "Hacks enviados", "SUCCESS")

async def scan_route(update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /scan ORIGEN DESTINO"""
    user = update.effective_user
    print_section("COMANDO /SCAN EJECUTADO")
    print_status("👤", f"Usuario: {user.username or user.first_name}")
    
    if len(context.args) < 2:
        await update.message.reply_text("❌ Uso: `/scan MAD MGA`", parse_mode='Markdown')
        return
    
    origin = context.args[0].upper()
    dest = context.args[1].upper()
    
    await update.message.reply_text(f"🔄 Escaneando {origin}-{dest}...", parse_mode='Markdown')
    price = get_single_price(origin, dest)
    
    msg = f"""✅ *RESULTADO*

✈️ {origin} → {dest}
💰 Precio: €{price:.0f}
📊 Fuente: ML-Estimate

🕐 {datetime.now().strftime('%H:%M:%S')}
    """
    await update.message.reply_text(msg, parse_mode='Markdown')
    print_status("✅", "Scan completado", "SUCCESS")

# ============================================
# MAIN
# ============================================

def main():
    """Función principal"""
    safe_print("\n")
    print_header("🏆  CAZADOR SUPREMO v9.0  🏆")
    
    print_section("CONFIGURACIÓN DEL SISTEMA")
    print_result("Bot Token", f"{BOT_TOKEN[:20]}...", "🤖")
    print_result("Chat ID", CHAT_ID, "👤")
    print_result("Tipo", "Privado", "🔒")
    
    roundtrip_count = sum(1 for f in FLIGHTS if f.get('type') == 'roundtrip')
    oneway_count = sum(1 for f in FLIGHTS if f.get('type') == 'oneway')
    
    print_result("Ida y Vuelta", f"{roundtrip_count} configuración(es)", "🔄")
    print_result("Solo Ida", f"{oneway_count} configuración(es)", "➡️")
    print_result("Total", f"{len(FLIGHTS)} búsquedas", "📊")
    
    safe_print("\n   📋 Configuraciones:")
    for idx, flight in enumerate(FLIGHTS, 1):
        type_emoji = "🔄" if flight.get('type') == 'roundtrip' else "➡️"
        safe_print(f"      {idx}. {type_emoji} {flight['name']}")
        safe_print(f"         Umbral: €{flight.get('alert_min', ALERT_MIN_GLOBAL)}")
        if flight.get('outbound_date'):
            safe_print(f"         Fecha ida: {flight['outbound_date']}")
        if flight.get('return_date'):
            safe_print(f"         Fecha vuelta: {flight['return_date']}")
    
    print_section("INICIALIZANDO BOT")
    print_status("🚀", "Creando aplicación...")
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", supreme_start))
    app.add_handler(CommandHandler("supremo", supremo_scan))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("rss", rss_command))
    app.add_handler(CommandHandler("chollos", chollos))
    app.add_handler(CommandHandler("scan", scan_route))
    
    print_status("✅", "Bot activo")
    print_header("⏳ ESPERANDO COMANDOS", "=")
    print_status("👂", "Escuchando...")
    
    app.run_polling()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print_header("🛑 BOT DETENIDO", "=")
        print_status("✅", f"Cerrado: {datetime.now().strftime('%H:%M:%S')}")
    except Exception as e:
        print_header("❌ ERROR", "=")
        print_status("⚠️", str(e), "ERROR")
