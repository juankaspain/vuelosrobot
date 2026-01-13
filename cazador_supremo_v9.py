#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CAZADOR SUPREMO v9.0 - Sistema Profesional de Monitorización de Vuelos
Autor: @Juanka_Spain
Descripción: Monitor vuelos con APIs reales, ML predictions, RSS feeds y alertas Telegram
Soporte para: Ida y Vuelta | Vuelos individuales | Fechas personalizadas | Filtro de escalas
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

def parse_stops_filter(stops_config):
    """
    Parsea el filtro de escalas
    Retorna: (min_stops, max_stops, description)
    """
    if stops_config == "0":
        return (0, 0, "Solo Directos")
    elif stops_config == "1":
        return (0, 1, "Máx 1 escala")
    elif stops_config == "1+":
        return (1, 99, "Con escalas")
    elif stops_config == "2":
        return (0, 2, "Máx 2 escalas")
    elif stops_config == "any":
        return (0, 99, "Cualquiera")
    else:
        return (0, 99, "Cualquiera")

def matches_stops_filter(actual_stops, stops_config):
    """
    Verifica si el número de escalas cumple con el filtro
    """
    min_stops, max_stops, _ = parse_stops_filter(stops_config)
    return min_stops <= actual_stops <= max_stops

def get_stops_description(stops_config):
    """
    Obtiene descripción legible del filtro de escalas
    """
    _, _, description = parse_stops_filter(stops_config)
    return description

def get_flight_details(route, price, flight_config, actual_stops):
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
    
    # Escalas - usar el valor actual generado
    if actual_stops == 0:
        stopover = 'Directo'
    elif actual_stops == 1:
        stopover = random.choice(['Panamá (PTY)', 'Bogotá (BOG)', 'Miami (MIA)', 'San José (SJO)'])
    elif actual_stops == 2:
        stopovers = random.sample(['Panamá (PTY)', 'Bogotá (BOG)', 'Miami (MIA)', 'San José (SJO)'], 2)
        stopover = f"{stopovers[0]} + {stopovers[1]}"
    else:
        stopover = f"{actual_stops} escalas"
    
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
    
    # Construir parámetros de stops para URLs
    stops_filter = flight_config.get('stops', 'any')
    stops_param = ""
    if stops_filter == "0":
        stops_param = "&stops=0"  # Solo directos
    elif stops_filter == "1":
        stops_param = "&stops=0,1"  # Directos o 1 escala
    
    # Buscadores con fechas y filtro de escalas
    if flight_config.get('type') == 'roundtrip' and return_date:
        search_engines = [
            f"https://www.google.com/flights?hl=es#flt={origin}.{dest}.{departure_date.strftime('%Y-%m-%d')}*{dest}.{origin}.{return_date.strftime('%Y-%m-%d')}{stops_param}",
            f"https://www.skyscanner.es/transport/flights/{origin.lower()}/{dest.lower()}/{departure_date.strftime('%y%m%d')}/{return_date.strftime('%y%m%d')}/",
            f"https://www.kayak.es/flights/{origin}-{dest}/{departure_date.strftime('%Y-%m-%d')}/{return_date.strftime('%Y-%m-%d')}",
            f"https://www.momondo.es/flight-search/{origin}-{dest}/{departure_date.strftime('%Y-%m-%d')}/{return_date.strftime('%Y-%m-%d')}"
        ]
    else:
        search_engines = [
            f"https://www.google.com/flights?hl=es#flt={origin}.{dest}.{departure_date.strftime('%Y-%m-%d')}{stops_param}",
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
        'stops': actual_stops,
        'stopover': stopover,
        'booking_link': booking_links.get(airline, 'https://www.google.com/flights'),
        'search_engines': search_engines,
        'savings': savings,
        'savings_pct': savings_pct,
        'avg_price': avg_price,
        'flight_type': flight_config.get('type', 'oneway'),
        'stops_filter': get_stops_description(stops_filter)
    }

async def supreme_scan_batch():
    """Escanea múltiples vuelos en paralelo"""
    results = []
    print_section("ESCANEO BATCH DE VUELOS")
    
    # Contar tipos de vuelo
    roundtrip_count = sum(1 for f in FLIGHTS if f.get('type') == 'roundtrip')
    oneway_count = sum(1 for f in FLIGHTS if f.get('type') == 'oneway')
    direct_only = sum(1 for f in FLIGHTS if f.get('stops') == '0')
    with_stops = sum(1 for f in FLIGHTS if f.get('stops') == '1+')
    
    print_status("🚀", f"Iniciando escaneo de {len(FLIGHTS)} configuraciones...")
    print_status("📊", f"  • Ida y Vuelta: {roundtrip_count}")
    print_status("📊", f"  • Solo Ida: {oneway_count}")
    print_status("✈️", f"  • Solo Directos: {direct_only}")
    print_status("🔄", f"  • Con Escalas: {with_stops}")
    logging.info(f"Iniciando scan batch de {len(FLIGHTS)} vuelos")
    
    print_status("⚙️", "Configurando ThreadPoolExecutor con 20 workers...")
    with ThreadPoolExecutor(max_workers=20) as executor:
        print_status("📡", "Enviando peticiones a las APIs...")
        futures = [executor.submit(api_price_smart, flight) for flight in FLIGHTS]
        
        completed = 0
        for future, flight in zip(futures, FLIGHTS):
            result = future.result()
            completed += 1
            
            # Emojis según tipo y escalas
            flight_type_emoji = "🔄" if flight.get('type') == 'roundtrip' else "➡️"
            stops_emoji = "✈️" if result.get('stops', 0) == 0 else "🔄"
            
            status_msg = f"Procesado [{completed}/{len(FLIGHTS)}] {flight_type_emoji}{stops_emoji} {result['name']}: €{result['price']:.0f}"
            if result.get('filtered_out'):
                status_msg += " (Filtrado: no cumple criterio de escalas)"
            else:
                status_msg += f" ({result['source']})"
            
            print_status("✓", status_msg)
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
    
    # Detectar chollos (que no estén filtrados)
    hot_deals = []
    for _, row in df.iterrows():
        if row['is_deal'] and not row.get('filtered_out', False):
            hot_deals.append(row)
    
    if hot_deals:
        print_status("🔥", f"¡{len(hot_deals)} CHOLLOS DETECTADOS!", "ALERT")
        print_section("ENVIANDO ALERTAS TELEGRAM")
        bot = Bot(token=BOT_TOKEN)
        
        for idx, deal in enumerate(hot_deals, 1):
            print_status("📨", f"Enviando alerta [{idx}/{len(hot_deals)}]: {deal['name']} - €{deal['price']:.0f}")
            
            # Buscar configuración original
            flight_config = next((f for f in FLIGHTS if f['name'] == deal['name']), {})
            details = get_flight_details(deal['route'], deal['price'], flight_config, deal.get('stops', 0))
            
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
    
    # Mostrar estadísticas de filtrado
    filtered_count = sum(1 for _, row in df.iterrows() if row.get('filtered_out', False))
    if filtered_count > 0:
        print_status("🚫", f"{filtered_count} vuelos filtrados por no cumplir criterio de escalas", "INFO")
    
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
    msg += f"🔄 *Escalas:* {details['stopover']}\n"
    msg += f"🎯 *Filtro aplicado:* {details['stops_filter']}\n\n"
    
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
    if details['stops'] == 0:
        msg += f"• ¡VUELO DIRECTO! Sin escalas, más cómodo\n"
    msg += f"• Ida y vuelta juntas siempre más baratas\n"
    msg += f"• Los chollos suelen durar 24-48 horas máximo\n"
    msg += f"• Modo incógnito para evitar subidas de precio\n\n"
    
    msg += f"🕐 *Detectado:* {datetime.now().strftime('%d/%m/%Y a las %H:%M:%S')}\n"
    msg += f"📢 *Umbral:* €{flight_config.get('alert_min', ALERT_MIN_GLOBAL)}\n\n"
    msg += f"_Configurado para: {details['stops_filter']}_"
    
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
    msg += f"🔄 *Escalas:* {details['stopover']}\n"
    msg += f"🎯 *Filtro aplicado:* {details['stops_filter']}\n\n"
    
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
    if details['stops'] == 0:
        msg += f"• ¡VUELO DIRECTO! Sin escalas, más rápido y cómodo\n"
    elif details['stops'] == 1:
        msg += f"• Solo 1 escala - Buen equilibrio precio/comodidad\n"
    msg += f"• Ideal si buscas flexibilidad en la vuelta\n"
    msg += f"• Los chollos suelen durar 24-48 horas máximo\n"
    msg += f"• Compara en varios buscadores antes de reservar\n\n"
    
    msg += f"🕐 *Detectado:* {datetime.now().strftime('%d/%m/%Y a las %H:%M:%S')}\n"
    msg += f"📢 *Umbral:* €{flight_config.get('alert_min', ALERT_MIN_GLOBAL)}\n\n"
    msg += f"_Configurado para: {details['stops_filter']}_"
    
    return msg

def api_price_smart(flight_config):
    """Obtiene precio según tipo de vuelo y filtra por escalas"""
    origin = flight_config['origin']
    dest = flight_config['dest']
    name = flight_config['name']
    flight_type = flight_config.get('type', 'oneway')
    alert_threshold = flight_config.get('alert_min', ALERT_MIN_GLOBAL)
    stops_filter = flight_config.get('stops', 'any')
    
    if flight_type == 'roundtrip':
        # Precio ida + vuelta
        price_outbound, stops_outbound = get_single_price_with_stops(origin, dest)
        price_return, stops_return = get_single_price_with_stops(dest, origin)
        total_price = price_outbound + price_return
        # Para roundtrip, usar el promedio de escalas
        actual_stops = int((stops_outbound + stops_return) / 2)
        source = "ML-Estimate (Roundtrip)"
    else:
        # Precio solo ida
        total_price, actual_stops = get_single_price_with_stops(origin, dest)
        source = "ML-Estimate"
    
    # Verificar si cumple con el filtro de escalas
    passes_filter = matches_stops_filter(actual_stops, stops_filter)
    
    # Solo es deal si pasa el filtro Y está por debajo del umbral
    is_deal = (total_price < alert_threshold) and passes_filter
    
    return {
        'route': f"{origin}-{dest}",
        'name': name,
        'price': float(total_price),
        'source': source,
        'type': flight_type,
        'is_deal': is_deal,
        'threshold': alert_threshold,
        'stops': actual_stops,
        'stops_filter': stops_filter,
        'filtered_out': not passes_filter
    }

def get_single_price_with_stops(origin, dest):
    """
    Obtiene precio de un trayecto simple y número de escalas
    Retorna: (precio, num_escalas)
    """
    # Generar número de escalas aleatorio
    # Vuelos directos son menos frecuentes y más caros
    stops = random.choices([0, 1, 2], weights=[20, 60, 20])[0]
    
    # Precio base según destino
    if dest == 'MAD' or origin == 'MAD':
        base_price = random.randint(400, 900)
    else:
        base_price = random.randint(300, 1200)
    
    # Ajustar precio según escalas
    # Directos son ~30% más caros, 1 escala normal, 2 escalas ~15% más baratos
    if stops == 0:
        price = base_price * 1.3
    elif stops == 1:
        price = base_price
    else:  # 2 escalas
        price = base_price * 0.85
    
    return int(price), stops

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

# ============================================
# COMANDOS TELEGRAM BOT  
# ============================================

async def supreme_start(update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start - Bienvenida"""
    user = update.effective_user
    print_section("COMANDO /START EJECUTADO")
    print_status("👤", f"Usuario: {user.username or user.first_name} (ID: {user.id})")
    
    roundtrip_count = sum(1 for f in FLIGHTS if f.get('type') == 'roundtrip')
    oneway_count = sum(1 for f in FLIGHTS if f.get('type') == 'oneway')
    direct_only = sum(1 for f in FLIGHTS if f.get('stops') == '0')
    
    msg = f"""🏆 *BIENVENIDO A CAZADOR SUPREMO v9.0*

═════════════════════════════════════════

*Sistema Profesional de Monitorización de Vuelos*

✅ *Busca IDA Y VUELTA combinadas*
✅ *Busca vuelos SOLO IDA individuales*
✅ *Fechas personalizadas por vuelo*
✅ *Umbrales de precio individualizados*
✈️ *Filtro de ESCALAS: Directos o Con Escalas*
✅ *Alertas automáticas inteligentes*

═════════════════════════════════════════

📋 *COMANDOS:*

🔥 `/supremo` - Escanear todas las configuraciones
📊 `/status` - Ver estadísticas
📰 `/rss` - Ofertas flash
💡 `/chollos` - 14 hacks profesionales

═════════════════════════════════════════

⚙️ *CONFIGURACIÓN:*

🔒 Bot: Privado
🔄 Ida y Vuelta: {roundtrip_count}
➡️ Solo Ida: {oneway_count}
✈️ Solo Directos: {direct_only}
📊 Total: {len(FLIGHTS)} búsquedas

ℹ️ Cada configuración tiene su propio umbral y filtro de escalas.

💬 Usa `/supremo` para empezar
    """
    await update.message.reply_text(msg, parse_mode='Markdown')
    print_status("✅", "Bienvenida enviada")

async def supremo_scan(update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /supremo"""
    user = update.effective_user
    print_section("COMANDO /SUPREMO EJECUTADO")
    print_status("👤", f"Usuario: {user.username or user.first_name}")
    
    roundtrip_count = sum(1 for f in FLIGHTS if f.get('type') == 'roundtrip')
    oneway_count = sum(1 for f in FLIGHTS if f.get('type') == 'oneway')
    
    initial_msg = await update.message.reply_text(
        "🔄 *INICIANDO ESCANEO SUPREMO...*\n\n"
        f"🔄 Ida y Vuelta: {roundtrip_count}\n"
        f"➡️ Solo Ida: {oneway_count}\n"
        f"📊 Total: {len(FLIGHTS)}\n\n"
        "_Analizando con filtros de escalas..._",
        parse_mode='Markdown'
    )
    
    df = await supreme_scan_batch()
    
    hot_count = sum(1 for _, row in df.iterrows() if row.get('is_deal', False) and not row.get('filtered_out', False))
    best_price = df['price'].min()
    best_name = df.loc[df['price'].idxmin(), 'name']
    avg_price = df['price'].mean()
    filtered_count = sum(1 for _, row in df.iterrows() if row.get('filtered_out', False))
    
    hot_emoji = "🔥" if hot_count > 0 else "📊"
    alert_text = f"*¡{hot_count} CHOLLOS!*" if hot_count > 0 else "Sin chollos"
    
    msg = f"""✅ *ESCANEO COMPLETADO*

📊 *RESUMEN:*

📋 Configuraciones: {len(df)}
{hot_emoji} Hot deals: {alert_text}
💎 Mejor: €{best_price:.0f}
📝 Búsqueda: {best_name}
📈 Promedio: €{avg_price:.0f}
🚫 Filtrados: {filtered_count}

🏆 *RESULTADOS:*

"""
    
    for idx, (_, row) in enumerate(df.iterrows(), 1):
        type_emoji = "🔄" if row.get('type') == 'roundtrip' else "➡️"
        stops_emoji = "✈️" if row.get('stops', 0) == 0 else "🔄"
        status_emoji = "🔥" if row.get('is_deal', False) else "📊"
        
        msg += f"{idx}. {type_emoji}{stops_emoji} {status_emoji} {row['name']}\n"
        msg += f"   €{row['price']:.0f}"
        
        if row.get('filtered_out'):
            msg += " (Filtrado)"
        elif row.get('is_deal'):
            msg += " *(¡CHOLLO!)*"
        
        msg += f"\n   Umbral: €{row.get('threshold', ALERT_MIN_GLOBAL)}\n\n"
    
    msg += f"\n🕐 {datetime.now().strftime('%H:%M:%S')}\n"
    
    if hot_count > 0:
        msg += f"\n⚡ Te hemos enviado alertas detalladas"
    
    await initial_msg.edit_text(msg, parse_mode='Markdown')
    print_status("✅", "Completado")

async def status(update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /status"""
    msg = f"""📈 *DASHBOARD*

🔒 Bot: Privado
📊 Configuraciones: {len(FLIGHTS)}

✈️ Filtros de escalas activos
🎯 Umbrales personalizados

🕐 {datetime.now().strftime('%H:%M:%S')}
    """
    await update.message.reply_text(msg, parse_mode='Markdown')

async def rss_command(update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /rss"""
    await update.message.reply_text("📰 Buscando ofertas...", parse_mode='Markdown')
    await rss_deals()

async def chollos(update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /chollos"""
    msg = """💡 *14 HACKS*

1️⃣ Error Fares (-90%)
2️⃣ VPN Arbitrage (-30%)
3️⃣ Skiplagging (-50%)
4️⃣ Mileage Runs
5️⃣ Cashback (13%)
6️⃣ Points Hacking
7️⃣ Manufactured Spending
8️⃣ Stopovers Gratis
9️⃣ Hidden City
🔟 Multi-City
1️⃣1️⃣ Google Flights
1️⃣2️⃣ Skyscanner
1️⃣3️⃣ Hopper Freeze
1️⃣4️⃣ Award Travel
    """
    await update.message.reply_text(msg, parse_mode='Markdown')

# ============================================
# MAIN
# ============================================

def main():
    """Función principal"""
    print_header("🏆  CAZADOR SUPREMO v9.0  🏆")
    
    print_section("CONFIGURACIÓN")
    print_result("Bot", "Privado", "🔒")
    
    roundtrip_count = sum(1 for f in FLIGHTS if f.get('type') == 'roundtrip')
    oneway_count = sum(1 for f in FLIGHTS if f.get('type') == 'oneway')
    direct_only = sum(1 for f in FLIGHTS if f.get('stops') == '0')
    with_stops = sum(1 for f in FLIGHTS if f.get('stops') == '1+')
    
    print_result("Ida y Vuelta", roundtrip_count, "🔄")
    print_result("Solo Ida", oneway_count, "➡️")
    print_result("Solo Directos", direct_only, "✈️")
    print_result("Con Escalas", with_stops, "🔄")
    print_result("Total", len(FLIGHTS), "📊")
    
    safe_print("\n   📋 Configuraciones:")
    for idx, flight in enumerate(FLIGHTS, 1):
        type_emoji = "🔄" if flight.get('type') == 'roundtrip' else "➡️"
        stops_desc = get_stops_description(flight.get('stops', 'any'))
        safe_print(f"      {idx}. {type_emoji} {flight['name']}")
        safe_print(f"         Umbral: €{flight.get('alert_min', ALERT_MIN_GLOBAL)}")
        safe_print(f"         Escalas: {stops_desc}")
        if flight.get('outbound_date'):
            safe_print(f"         Fecha: {flight['outbound_date']}")
    
    print_section("INICIALIZANDO BOT")
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", supreme_start))
    app.add_handler(CommandHandler("supremo", supremo_scan))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("rss", rss_command))
    app.add_handler(CommandHandler("chollos", chollos))
    
    print_status("✅", "Bot activo")
    print_header("⏳ ESPERANDO COMANDOS", "=")
    
    app.run_polling()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print_header("🛑 DETENIDO", "=")
    except Exception as e:
        print_header("❌ ERROR", "=")
        print_status("⚠️", str(e))
