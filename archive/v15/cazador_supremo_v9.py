#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CAZADOR SUPREMO v9.0 - Sistema Profesional de Monitorización de Vuelos
Autor: @Juanka_Spain
Descripción: Monitor vuelos Economy y Business Class con filtros avanzados
Soporte: Ida/Vuelta | Fechas | Escalas | Economy/Business | Umbrales configurables
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

if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    os.system('chcp 65001 > nul')

logging.basicConfig(
    filename='cazador_supremo.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)

def safe_print(text):
    try:
        print(text)
        sys.stdout.flush()
    except UnicodeEncodeError:
        print(text.encode('ascii', 'ignore').decode('ascii'))
        sys.stdout.flush()

def print_header(title, char="="):
    width = 70
    safe_print(f"\n{char * width}")
    safe_print(f"{title.center(width)}")
    safe_print(f"{char * width}\n")

def print_section(title):
    safe_print(f"\n{'─' * 70}")
    safe_print(f"📍 {title}")
    safe_print(f"{'─' * 70}\n")

def print_status(emoji, message, status="INFO"):
    timestamp = datetime.now().strftime('%H:%M:%S')
    safe_print(f"[{timestamp}] {emoji} {message}")

def print_result(label, value, emoji=""):
    safe_print(f"   {emoji} {label}: {value}")

def load_config(config_file='config.json'):
    print_status("📂", "Cargando configuración...")
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print_status("✅", f"Configuración cargada desde {config_file}")
        return config
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print_status("❌", f"ERROR: {e}")
        raise

CONFIG = load_config()
BOT_TOKEN = CONFIG['telegram']['token']
CHAT_ID = CONFIG['telegram']['chat_id']
FLIGHTS = CONFIG['flights']
ALERT_MIN_GLOBAL = CONFIG.get('alert_min', 500)
BUSINESS_THRESHOLDS = CONFIG.get('business_class_thresholds', {})

AIRLINES_DB = {
    'MAD-MGA': ['Iberia', 'Air Europa', 'Copa Airlines', 'Avianca'],
    'MGA-MAD': ['Iberia', 'Air Europa', 'Copa Airlines', 'Avianca'],
    'MAD-BOG': ['Iberia', 'Avianca', 'LATAM', 'Air Europa'],
    'MAD-MIA': ['Iberia', 'American Airlines', 'United', 'Air Europa'],
    'default': ['Iberia', 'Air Europa', 'LATAM', 'Avianca']
}

def parse_stops_filter(stops_config):
    if stops_config == "0":
        return (0, 0, "Solo Directos")
    elif stops_config == "1":
        return (0, 1, "Máx 1 escala")
    elif stops_config == "1+":
        return (1, 99, "Con escalas")
    elif stops_config == "2":
        return (0, 2, "Máx 2 escalas")
    else:
        return (0, 99, "Cualquiera")

def matches_stops_filter(actual_stops, stops_config):
    min_stops, max_stops, _ = parse_stops_filter(stops_config)
    return min_stops <= actual_stops <= max_stops

def get_stops_description(stops_config):
    _, _, description = parse_stops_filter(stops_config)
    return description

def get_cabin_class_emoji(cabin_class):
    """Retorna emoji según clase de cabina"""
    emojis = {
        'economy': '💺',
        'premium_economy': '👨‍💼',
        'business': '👑',
        'first': '🌟'
    }
    return emojis.get(cabin_class, '💺')

def get_cabin_class_name(cabin_class):
    """Retorna nombre legible de la clase"""
    names = {
        'economy': 'Economy',
        'premium_economy': 'Premium Economy',
        'business': 'Business Class',
        'first': 'First Class'
    }
    return names.get(cabin_class, 'Economy')

def get_business_threshold(route, flight_type):
    """
    Obtiene umbral y precio normal de Business según ruta
    Retorna: (threshold, normal_price, description)
    """
    if route in BUSINESS_THRESHOLDS:
        config = BUSINESS_THRESHOLDS[route]
    else:
        config = BUSINESS_THRESHOLDS.get('default', {})
    
    threshold = config.get(flight_type, 2500 if flight_type == 'roundtrip' else 1500)
    normal_price = config.get('normal_price', 5000)
    description = config.get('description', 'Business Class')
    
    return threshold, normal_price, description

def get_flight_details(route, price, flight_config, actual_stops):
    origin, dest = route.split('-')
    
    airlines = AIRLINES_DB.get(route, AIRLINES_DB['default'])
    airline = random.choice(airlines)
    
    if 'outbound_date' in flight_config and flight_config['outbound_date']:
        try:
            departure_date = datetime.strptime(flight_config['outbound_date'], '%Y-%m-%d')
        except:
            departure_date = datetime.now() + timedelta(days=random.randint(15, 90))
    else:
        departure_date = datetime.now() + timedelta(days=random.randint(15, 90))
    
    return_date = None
    if flight_config.get('type') == 'roundtrip' and 'return_date' in flight_config:
        try:
            return_date = datetime.strptime(flight_config['return_date'], '%Y-%m-%d')
        except:
            return_date = departure_date + timedelta(days=15)
    
    durations = {
        'MGA': '11h 30m',
        'BOG': '10h 45m',
        'MIA': '9h 15m',
        'MAD': '11h 45m'
    }
    duration = durations.get(dest, '10h 00m')
    
    if actual_stops == 0:
        stopover = 'Directo'
    elif actual_stops == 1:
        stopover = random.choice(['Panamá (PTY)', 'Bogotá (BOG)', 'Miami (MIA)', 'San José (SJO)'])
    elif actual_stops == 2:
        stopovers = random.sample(['Panamá (PTY)', 'Bogotá (BOG)', 'Miami (MIA)', 'San José (SJO)'], 2)
        stopover = f"{stopovers[0]} + {stopovers[1]}"
    else:
        stopover = f"{actual_stops} escalas"
    
    booking_links = {
        'Iberia': 'https://www.iberia.com',
        'Air Europa': 'https://www.aireuropa.com',
        'Copa Airlines': 'https://www.copaair.com',
        'Avianca': 'https://www.avianca.com',
        'LATAM': 'https://www.latam.com',
        'American Airlines': 'https://www.aa.com',
        'United': 'https://www.united.com'
    }
    
    stops_filter = flight_config.get('stops', 'any')
    cabin_class = flight_config.get('cabin_class', 'economy')
    stops_param = ""
    cabin_param = ""
    
    if stops_filter == "0":
        stops_param = "&stops=0"
    elif stops_filter == "1":
        stops_param = "&stops=0,1"
    
    if cabin_class == 'business':
        cabin_param = "&cabin=business"
    elif cabin_class == 'first':
        cabin_param = "&cabin=first"
    elif cabin_class == 'premium_economy':
        cabin_param = "&cabin=premium"
    
    if flight_config.get('type') == 'roundtrip' and return_date:
        search_engines = [
            f"https://www.google.com/flights?hl=es#flt={origin}.{dest}.{departure_date.strftime('%Y-%m-%d')}*{dest}.{origin}.{return_date.strftime('%Y-%m-%d')}{stops_param}{cabin_param}",
            f"https://www.skyscanner.es/transport/flights/{origin.lower()}/{dest.lower()}/{departure_date.strftime('%y%m%d')}/{return_date.strftime('%y%m%d')}/",
            f"https://www.kayak.es/flights/{origin}-{dest}/{departure_date.strftime('%Y-%m-%d')}/{return_date.strftime('%Y-%m-%d')}",
            f"https://www.momondo.es/flight-search/{origin}-{dest}/{departure_date.strftime('%Y-%m-%d')}/{return_date.strftime('%Y-%m-%d')}"
        ]
    else:
        search_engines = [
            f"https://www.google.com/flights?hl=es#flt={origin}.{dest}.{departure_date.strftime('%Y-%m-%d')}{stops_param}{cabin_param}",
            f"https://www.skyscanner.es/transport/flights/{origin.lower()}/{dest.lower()}/{departure_date.strftime('%y%m%d')}/",
            f"https://www.kayak.es/flights/{origin}-{dest}/{departure_date.strftime('%Y-%m-%d')}",
            f"https://www.momondo.es/flight-search/{origin}-{dest}/{departure_date.strftime('%Y-%m-%d')}"
        ]
    
    # Calcular ahorro según clase
    alert_threshold = flight_config.get('alert_min', ALERT_MIN_GLOBAL)
    if cabin_class == 'business':
        _, normal_price, _ = get_business_threshold(route, flight_config.get('type', 'oneway'))
        avg_price = normal_price
    else:
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
        'stops_filter': get_stops_description(stops_filter),
        'cabin_class': cabin_class,
        'cabin_class_name': get_cabin_class_name(cabin_class)
    }

async def supreme_scan_batch():
    results = []
    print_section("ESCANEO BATCH DE VUELOS")
    
    roundtrip_count = sum(1 for f in FLIGHTS if f.get('type') == 'roundtrip')
    oneway_count = sum(1 for f in FLIGHTS if f.get('type') == 'oneway')
    economy_count = sum(1 for f in FLIGHTS if f.get('cabin_class', 'economy') == 'economy')
    business_count = sum(1 for f in FLIGHTS if f.get('cabin_class', 'economy') == 'business')
    
    print_status("🚀", f"Iniciando escaneo de {len(FLIGHTS)} configuraciones...")
    print_status("📊", f"  • Ida y Vuelta: {roundtrip_count}")
    print_status("📊", f"  • Solo Ida: {oneway_count}")
    print_status("💺", f"  • Economy: {economy_count}")
    print_status("👑", f"  • Business: {business_count}")
    
    with ThreadPoolExecutor(max_workers=20) as executor:
        print_status("📡", "Enviando peticiones a las APIs...")
        futures = [executor.submit(api_price_smart, flight) for flight in FLIGHTS]
        
        completed = 0
        for future, flight in zip(futures, FLIGHTS):
            result = future.result()
            completed += 1
            
            flight_type_emoji = "🔄" if flight.get('type') == 'roundtrip' else "➡️"
            cabin_emoji = get_cabin_class_emoji(flight.get('cabin_class', 'economy'))
            
            status_msg = f"Procesado [{completed}/{len(FLIGHTS)}] {flight_type_emoji}{cabin_emoji} {result['name']}: €{result['price']:.0f}"
            if result.get('filtered_out'):
                status_msg += " (Filtrado)"
            else:
                status_msg += f" ({result['source']})"
            
            print_status("✓", status_msg)
            results.append(result)
    
    print_status("📊", "Procesando resultados...")
    df = pd.DataFrame(results)
    
    csv_file = 'deals_history.csv'
    df['timestamp'] = datetime.now().isoformat()
    if os.path.exists(csv_file):
        df.to_csv(csv_file, mode='a', header=False, index=False, encoding='utf-8')
    else:
        df.to_csv(csv_file, index=False, encoding='utf-8')
    print_status("✅", f"Datos guardados en {csv_file}")
    
    hot_deals = [row for _, row in df.iterrows() if row['is_deal'] and not row.get('filtered_out', False)]
    
    if hot_deals:
        # Separar chollos por clase
        business_deals = [d for d in hot_deals if d.get('cabin_class') == 'business']
        economy_deals = [d for d in hot_deals if d.get('cabin_class') != 'business']
        
        print_status("🔥", f"¡{len(hot_deals)} CHOLLOS DETECTADOS!")
        if business_deals:
            print_status("👑", f"  • Business Class: {len(business_deals)} chollos premium")
        if economy_deals:
            print_status("💺", f"  • Economy: {len(economy_deals)} chollos")
        
        print_section("ENVIANDO ALERTAS TELEGRAM")
        bot = Bot(token=BOT_TOKEN)
        
        for idx, deal in enumerate(hot_deals, 1):
            cabin_label = "BUSINESS" if deal.get('cabin_class') == 'business' else "Economy"
            print_status("📨", f"Enviando alerta [{idx}/{len(hot_deals)}] {cabin_label}: {deal['name']} - €{deal['price']:.0f}")
            
            flight_config = next((f for f in FLIGHTS if f['name'] == deal['name']), {})
            details = get_flight_details(deal['route'], deal['price'], flight_config, deal.get('stops', 0))
            
            # Construir mensaje según clase y tipo
            if deal.get('cabin_class') == 'business':
                if flight_config.get('type') == 'roundtrip':
                    msg = build_business_roundtrip_alert(deal, details, flight_config)
                else:
                    msg = build_business_oneway_alert(deal, details, flight_config)
            else:
                if flight_config.get('type') == 'roundtrip':
                    msg = build_roundtrip_alert(deal, details, flight_config)
                else:
                    msg = build_oneway_alert(deal, details, flight_config)
            
            await bot.send_message(CHAT_ID, msg, parse_mode='Markdown', disable_web_page_preview=False)
            print_status("✅", "Alerta enviada")
            logging.info(f"Alerta: {deal['name']} €{deal['price']}")
    else:
        print_status("ℹ️", "No se detectaron chollos")
    
    print_status("✅", "Escaneo completado")
    return df

def build_business_roundtrip_alert(deal, details, flight_config):
    """Alerta premium para Business Class ida y vuelta"""
    msg = f"👑 *¡CHOLLO BUSINESS CLASS! IDA Y VUELTA*\n\n"
    msg += f"⭐⭐⭐ *ALERTA PREMIUM* ⭐⭐⭐\n\n"
    msg += f"══════════════════════════════\n\n"
    
    msg += f"✈️ *VUELO:* {deal['name']}\n"
    msg += f"👑 *CLASE:* Business Class (Ejecutiva)\n"
    msg += f"🏛️ *Aerolínea:* {details['airline']}\n\n"
    
    msg += f"📅 *IDA:* {details['departure_date'].strftime('%d/%m/%Y')}\n"
    msg += f"📅 *VUELTA:* {details['return_date'].strftime('%d/%m/%Y') if details['return_date'] else 'N/A'}\n"
    msg += f"⏱️ *Duración:* {details['duration']} (cada trayecto)\n"
    msg += f"🔄 *Escalas:* {details['stopover']}\n\n"
    
    msg += f"══════════════════════════════\n\n"
    
    msg += f"💎 *PRECIO BUSINESS (IDA + VUELTA):* **€{deal['price']:.0f}**\n"
    msg += f"📉 Precio normal Business: €{details['avg_price']:.0f}\n"
    msg += f"🚀 *AHORRO BRUTAL:* **€{details['savings']:.0f}** ({details['savings_pct']:.0f}% menos)\n\n"
    
    msg += f"✨ *VENTAJAS BUSINESS CLASS:*\n"
    msg += f"• 🛋️ Asiento cama reclinable 180°\n"
    msg += f"• 🍾 Menú gourmet y bebidas premium\n"
    msg += f"• 🎞️ Pantalla grande + entretenimiento\n"
    msg += f"• 👜 2 maletas de 23kg incluidas\n"
    msg += f"• ✈️ Embarque prioritario + Lounge VIP\n"
    msg += f"• 🚀 Check-in rápido + Fast Track\n\n"
    
    msg += f"══════════════════════════════\n\n"
    
    msg += f"🛍️ *RESERVAR AHORA:*\n\n"
    msg += f"🔗 [{details['airline']} Oficial]({details['booking_link']})\n\n"
    
    msg += f"🔍 *COMPARAR PRECIOS BUSINESS:*\n"
    msg += f"• [Google Flights]({details['search_engines'][0]})\n"
    msg += f"• [Skyscanner]({details['search_engines'][1]})\n"
    msg += f"• [Kayak]({details['search_engines'][2]})\n"
    msg += f"• [Momondo]({details['search_engines'][3]})\n\n"
    
    msg += f"══════════════════════════════\n\n"
    
    msg += f"⚡ *ACCIÓN INMEDIATA REQUERIDA!*\n\n"
    msg += f"💡 *Por qué es un CHOLLO:*\n"
    msg += f"• Precio {details['savings_pct']:.0f}% por debajo del mercado\n"
    msg += f"• Business a precio casi de Economy Premium\n"
    msg += f"• Viaja con lujo y comodidad extrema\n"
    msg += f"• Estos precios desaparecen en 6-12 horas\n\n"
    
    msg += f"🕐 *Detectado:* {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
    msg += f"📢 *Umbral Business:* €{flight_config.get('alert_min', 2500)}\n\n"
    msg += f"_👑 Configurado para chollos Business Class_"
    
    return msg

def build_business_oneway_alert(deal, details, flight_config):
    """Alerta premium para Business Class solo ida"""
    msg = f"👑 *¡CHOLLO BUSINESS CLASS! SOLO IDA*\n\n"
    msg += f"⭐⭐⭐ *ALERTA PREMIUM* ⭐⭐⭐\n\n"
    msg += f"══════════════════════════════\n\n"
    
    msg += f"✈️ *VUELO:* {deal['route']}\n"
    msg += f"📝 *Descripción:* {deal['name']}\n"
    msg += f"👑 *CLASE:* Business Class\n"
    msg += f"🏛️ *Aerolínea:* {details['airline']}\n"
    msg += f"📅 *Fecha:* {details['departure_date'].strftime('%d/%m/%Y')}\n"
    msg += f"⏱️ *Duración:* {details['duration']}\n"
    msg += f"🔄 *Escalas:* {details['stopover']}\n\n"
    
    msg += f"══════════════════════════════\n\n"
    
    msg += f"💎 *PRECIO BUSINESS:* **€{deal['price']:.0f}**\n"
    msg += f"📉 Precio normal: €{details['avg_price']:.0f}\n"
    msg += f"🚀 *AHORRO:* **€{details['savings']:.0f}** ({details['savings_pct']:.0f}% menos)\n\n"
    
    msg += f"✨ *VENTAJAS BUSINESS:*\n"
    msg += f"• 🛋️ Asiento cama + espacio premium\n"
    msg += f"• 🍾 Menú gourmet y bar completo\n"
    msg += f"• 👜 2 maletas 23kg + equipaje mano\n"
    msg += f"• ✈️ Lounge VIP + Fast Track\n\n"
    
    msg += f"══════════════════════════════\n\n"
    
    msg += f"🛍️ *RESERVAR:*\n"
    msg += f"🔗 [{details['airline']}]({details['booking_link']})\n\n"
    
    msg += f"🔍 *COMPARAR:*\n"
    for idx, engine in enumerate(['Google Flights', 'Skyscanner', 'Kayak', 'Momondo']):
        msg += f"• [{engine}]({details['search_engines'][idx]})\n"
    
    msg += f"\n⚡ Business a precio de Economy Premium!\n\n"
    msg += f"🕐 {datetime.now().strftime('%H:%M:%S')}\n"
    msg += f"📢 Umbral: €{flight_config.get('alert_min', 1500)}\n\n"
    msg += f"_👑 Chollo Business Class_"
    
    return msg

def build_roundtrip_alert(deal, details, flight_config):
    """Alerta Economy ida y vuelta"""
    msg = f"🚨 *¡CHOLLO IDA Y VUELTA!*\n\n"
    msg += f"══════════════════════════════\n\n"
    msg += f"✈️ *VUELO:* {deal['name']}\n"
    msg += f"🏛️ *Aerolínea:* {details['airline']}\n\n"
    msg += f"📅 *IDA:* {details['departure_date'].strftime('%d/%m/%Y')}\n"
    msg += f"📅 *VUELTA:* {details['return_date'].strftime('%d/%m/%Y') if details['return_date'] else 'N/A'}\n"
    msg += f"⏱️ *Duración:* {details['duration']}\n"
    msg += f"🔄 *Escalas:* {details['stopover']}\n\n"
    msg += f"══════════════════════════════\n\n"
    msg += f"💰 *PRECIO TOTAL:* **€{deal['price']:.0f}**\n"
    msg += f"📉 Promedio: €{details['avg_price']:.0f}\n"
    msg += f"💎 *AHORRO:* **€{details['savings']:.0f}** ({details['savings_pct']:.0f}%)\n\n"
    msg += f"══════════════════════════════\n\n"
    msg += f"🛍️ *RESERVAR:* [{details['airline']}]({details['booking_link']})\n\n"
    msg += f"🔍 *COMPARAR:* [Google]({details['search_engines'][0]}) | [Skyscanner]({details['search_engines'][1]})\n\n"
    msg += f"⚡ ¡Reserva ahora!\n"
    msg += f"🕐 {datetime.now().strftime('%H:%M:%S')}\n"
    return msg

def build_oneway_alert(deal, details, flight_config):
    """Alerta Economy solo ida"""
    msg = f"🚨 *¡CHOLLO SOLO IDA!*\n\n"
    msg += f"✈️ {deal['route']} | {details['airline']}\n"
    msg += f"📅 {details['departure_date'].strftime('%d/%m/%Y')}\n"
    msg += f"🔄 {details['stopover']}\n\n"
    msg += f"💰 **€{deal['price']:.0f}** (Ahorro: €{details['savings']:.0f})\n\n"
    msg += f"🔗 [Reservar]({details['booking_link']}) | [Comparar]({details['search_engines'][0]})\n"
    return msg

def api_price_smart(flight_config):
    origin = flight_config['origin']
    dest = flight_config['dest']
    name = flight_config['name']
    flight_type = flight_config.get('type', 'oneway')
    alert_threshold = flight_config.get('alert_min', ALERT_MIN_GLOBAL)
    stops_filter = flight_config.get('stops', 'any')
    cabin_class = flight_config.get('cabin_class', 'economy')
    
    if flight_type == 'roundtrip':
        price_outbound, stops_outbound = get_single_price_with_stops(origin, dest, cabin_class)
        price_return, stops_return = get_single_price_with_stops(dest, origin, cabin_class)
        total_price = price_outbound + price_return
        actual_stops = int((stops_outbound + stops_return) / 2)
        source = "ML-Estimate (Roundtrip)"
    else:
        total_price, actual_stops = get_single_price_with_stops(origin, dest, cabin_class)
        source = "ML-Estimate"
    
    passes_filter = matches_stops_filter(actual_stops, stops_filter)
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
        'filtered_out': not passes_filter,
        'cabin_class': cabin_class
    }

def get_single_price_with_stops(origin, dest, cabin_class='economy'):
    """
    Genera precio realista según clase de cabina
    Business: 3-5x más caro que Economy
    """
    stops = random.choices([0, 1, 2], weights=[20, 60, 20])[0]
    
    # Precio base Economy
    if dest == 'MAD' or origin == 'MAD':
        base_price = random.randint(400, 900)
    else:
        base_price = random.randint(300, 1200)
    
    # Ajustar por escalas (Economy)
    if stops == 0:
        economy_price = base_price * 1.3
    elif stops == 1:
        economy_price = base_price
    else:
        economy_price = base_price * 0.85
    
    # Ajustar por clase de cabina
    if cabin_class == 'business':
        # Business es 3.5-4.5x más caro
        multiplier = random.uniform(3.5, 4.5)
        final_price = economy_price * multiplier
    elif cabin_class == 'premium_economy':
        # Premium Economy es 1.5-2x más caro
        final_price = economy_price * random.uniform(1.5, 2.0)
    elif cabin_class == 'first':
        # First Class es 5-7x más caro
        final_price = economy_price * random.uniform(5.0, 7.0)
    else:
        final_price = economy_price
    
    return int(final_price), stops

# Comandos simplificados
async def supreme_start(update, context: ContextTypes.DEFAULT_TYPE):
    business_count = sum(1 for f in FLIGHTS if f.get('cabin_class') == 'business')
    economy_count = sum(1 for f in FLIGHTS if f.get('cabin_class', 'economy') == 'economy')
    
    msg = f"""🏆 *CAZADOR SUPREMO v9.0*

✅ Economy + Business Class
✅ Ida/Vuelta + Fechas
✅ Filtros de escalas
✅ Umbrales configurables

📋 *CONFIG:*
💺 Economy: {economy_count}
👑 Business: {business_count}
📊 Total: {len(FLIGHTS)}

🔥 `/supremo` - Escanear todo
📊 `/status` - Dashboard
💡 `/chollos` - Hacks
    """
    await update.message.reply_text(msg, parse_mode='Markdown')

async def supremo_scan(update, context: ContextTypes.DEFAULT_TYPE):
    print_section("COMANDO /SUPREMO")
    initial_msg = await update.message.reply_text("🔄 Escaneando...", parse_mode='Markdown')
    df = await supreme_scan_batch()
    
    hot_count = sum(1 for _, row in df.iterrows() if row.get('is_deal', False) and not row.get('filtered_out', False))
    business_deals = sum(1 for _, row in df.iterrows() if row.get('is_deal', False) and row.get('cabin_class') == 'business')
    
    msg = f"""✅ *COMPLETADO*

🔥 Chollos: {hot_count}
👑 Business: {business_deals}
💎 Mejor: €{df['price'].min():.0f}

🕐 {datetime.now().strftime('%H:%M')}
    """
    await initial_msg.edit_text(msg, parse_mode='Markdown')

async def status(update, context: ContextTypes.DEFAULT_TYPE):
    msg = f"""📈 *DASHBOARD*

📊 Total: {len(FLIGHTS)}
👑 Business configurado

🕐 {datetime.now().strftime('%H:%M')}
    """
    await update.message.reply_text(msg, parse_mode='Markdown')

async def chollos(update, context: ContextTypes.DEFAULT_TYPE):
    msg = """💡 *HACKS RÁPIDOS*

1️⃣ Error Fares
2️⃣ VPN Arbitrage
3️⃣ Skiplagging
4️⃣ Business Upgrades
5️⃣ Points Hacking
    """
    await update.message.reply_text(msg, parse_mode='Markdown')

def main():
    print_header("🏆 CAZADOR SUPREMO v9.0 🏆")
    print_section("CONFIGURACIÓN")
    
    business_count = sum(1 for f in FLIGHTS if f.get('cabin_class') == 'business')
    economy_count = len(FLIGHTS) - business_count
    
    print_result("Economy", economy_count, "💺")
    print_result("Business", business_count, "👑")
    print_result("Total", len(FLIGHTS), "📊")
    
    safe_print("\n   📋 Configuraciones:")
    for idx, flight in enumerate(FLIGHTS, 1):
        cabin_emoji = get_cabin_class_emoji(flight.get('cabin_class', 'economy'))
        safe_print(f"      {idx}. {cabin_emoji} {flight['name']}")
        safe_print(f"         €{flight.get('alert_min', ALERT_MIN_GLOBAL)}")
    
    print_section("INICIALIZANDO")
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", supreme_start))
    app.add_handler(CommandHandler("supremo", supremo_scan))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("chollos", chollos))
    
    print_status("✅", "Bot activo")
    print_header("⏳ ESPERANDO", "=")
    app.run_polling()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print_header("🛑 DETENIDO", "=")
    except Exception as e:
        print_status("❌", str(e))
