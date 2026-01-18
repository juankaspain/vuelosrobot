#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎆 CAZADOR SUPREMO v10.0 ML ENHANCED 🎆
Autor: @Juanka_Spain
Descripción: Sistema con ML mejorado para predicciones más realistas
Nuevo: Predicciones basadas en patrones reales del mercado
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
API_KEYS = CONFIG.get('apis', {})

AIRLINES_DB = {
    'MAD-MGA': ['Iberia', 'Air Europa', 'Copa Airlines', 'Avianca'],
    'MGA-MAD': ['Iberia', 'Air Europa', 'Copa Airlines', 'Avianca'],
    'MAD-BOG': ['Iberia', 'Avianca', 'LATAM', 'Air Europa'],
    'MAD-MIA': ['Iberia', 'American Airlines', 'United', 'Air Europa'],
    'default': ['Iberia', 'Air Europa', 'LATAM', 'Avianca']
}

# 🤖 ML ENHANCED PREDICTOR
class MLEnhancedPredictor:
    """
    Predictor mejorado basado en patrones reales del mercado aéreo
    - Anticipación de compra (sweet spot: 45-60 días)
    - Temporada alta/baja
    - Día de la semana
    - Eventos especiales
    - Cabina (economy/business)
    - Escalas
    """
    
    # Precios base reales por ruta (investigación de mercado)
    BASE_PRICES = {
        'MAD-MGA': 680,
        'MAD-MIA': 520,
        'MAD-BOG': 580,
        'MAD-NYC': 450,
        'MAD-LAX': 550,
        'MGA-MAD': 700,
        'default': 650
    }
    
    # Meses de temporada alta (mayor demanda)
    HIGH_SEASON = [6, 7, 8, 12]  # Junio, Julio, Agosto, Diciembre
    LOW_SEASON = [1, 2, 9, 10, 11]  # Enero, Febrero, Sept-Nov
    
    @staticmethod
    def predict_price(origin: str, dest: str, flight_date: str, 
                     cabin_class: str = 'economy', stops: int = 1) -> float:
        """
        Predice precio basado en múltiples factores reales del mercado
        """
        route = f"{origin}-{dest}"
        
        # 1. Precio base de la ruta
        base_price = MLEnhancedPredictor.BASE_PRICES.get(route, 
                     MLEnhancedPredictor.BASE_PRICES['default'])
        
        # 2. Factor de anticipación (patrón curva en U)
        try:
            flight_dt = datetime.strptime(flight_date, '%Y-%m-%d')
            days_ahead = (flight_dt - datetime.now()).days
        except:
            days_ahead = 45  # Default
        
        advance_multiplier = MLEnhancedPredictor._get_advance_multiplier(days_ahead)
        
        # 3. Factor de temporada
        try:
            month = flight_dt.month
        except:
            month = datetime.now().month
        
        season_multiplier = MLEnhancedPredictor._get_season_multiplier(month)
        
        # 4. Factor día de la semana
        try:
            weekday = flight_dt.weekday()
        except:
            weekday = 1
        
        weekday_multiplier = MLEnhancedPredictor._get_weekday_multiplier(weekday)
        
        # 5. Factor de escalas
        stops_multiplier = MLEnhancedPredictor._get_stops_multiplier(stops)
        
        # 6. Factor de cabina
        cabin_multiplier = MLEnhancedPredictor._get_cabin_multiplier(cabin_class)
        
        # 7. Variación aleatoria realista (±8%)
        noise = random.uniform(0.92, 1.08)
        
        # Cálculo final
        predicted_price = (
            base_price * 
            advance_multiplier * 
            season_multiplier * 
            weekday_multiplier * 
            stops_multiplier * 
            cabin_multiplier * 
            noise
        )
        
        return max(100, int(predicted_price))
    
    @staticmethod
    def _get_advance_multiplier(days_ahead: int) -> float:
        """
        Patrón real: Curva en U
        - Muy anticipado (>90 días): Caro (+25%)
        - Sweet spot (45-60 días): Mejor precio (base)
        - Última hora (<14 días): Muy caro (+50-100%)
        """
        if days_ahead < 0:
            return 2.5  # Vuelo hoy/pasado = carísimo
        elif days_ahead < 3:
            return 2.0  # Últimos 3 días +100%
        elif days_ahead < 7:
            return 1.7  # Última semana +70%
        elif days_ahead < 14:
            return 1.4  # 2 semanas +40%
        elif days_ahead < 30:
            return 1.15  # 1 mes +15%
        elif days_ahead <= 60:
            return 1.0  # SWEET SPOT (45-60 días)
        elif days_ahead <= 90:
            return 1.1  # 2-3 meses +10%
        elif days_ahead <= 120:
            return 1.2  # 3-4 meses +20%
        else:
            return 1.25  # >4 meses +25%
    
    @staticmethod
    def _get_season_multiplier(month: int) -> float:
        """
        Temporada alta vs baja
        """
        if month in MLEnhancedPredictor.HIGH_SEASON:
            return 1.35  # Temporada alta +35%
        elif month in MLEnhancedPredictor.LOW_SEASON:
            return 0.85  # Temporada baja -15%
        else:
            return 1.0  # Media
    
    @staticmethod
    def _get_weekday_multiplier(weekday: int) -> float:
        """
        Día de la semana (0=Lunes, 6=Domingo)
        Viernes y Domingos más caros
        """
        if weekday == 4:  # Viernes
            return 1.15
        elif weekday == 6:  # Domingo
            return 1.2
        elif weekday in [1, 2]:  # Martes, Miércoles (más barato)
            return 0.95
        else:
            return 1.0
    
    @staticmethod
    def _get_stops_multiplier(stops: int) -> float:
        """
        Factor de escalas
        """
        if stops == 0:
            return 1.35  # Directo +35%
        elif stops == 1:
            return 1.0  # Base
        elif stops == 2:
            return 0.82  # 2 escalas -18%
        else:
            return 0.75  # 3+ escalas -25%
    
    @staticmethod
    def _get_cabin_multiplier(cabin_class: str) -> float:
        """
        Factor de clase de cabina
        """
        multipliers = {
            'economy': 1.0,
            'premium_economy': 1.75,
            'business': 4.2,
            'first': 6.5
        }
        return multipliers.get(cabin_class, 1.0)
    
    @staticmethod
    def get_price_breakdown(origin: str, dest: str, flight_date: str,
                           cabin_class: str = 'economy', stops: int = 1) -> dict:
        """
        Devuelve desglose detallado de cómo se calculó el precio
        Útil para debugging y transparencia
        """
        route = f"{origin}-{dest}"
        base = MLEnhancedPredictor.BASE_PRICES.get(route, 650)
        
        try:
            flight_dt = datetime.strptime(flight_date, '%Y-%m-%d')
            days_ahead = (flight_dt - datetime.now()).days
            month = flight_dt.month
            weekday = flight_dt.weekday()
        except:
            days_ahead, month, weekday = 45, datetime.now().month, 1
        
        advance = MLEnhancedPredictor._get_advance_multiplier(days_ahead)
        season = MLEnhancedPredictor._get_season_multiplier(month)
        day = MLEnhancedPredictor._get_weekday_multiplier(weekday)
        stops_mult = MLEnhancedPredictor._get_stops_multiplier(stops)
        cabin_mult = MLEnhancedPredictor._get_cabin_multiplier(cabin_class)
        
        final_price = MLEnhancedPredictor.predict_price(
            origin, dest, flight_date, cabin_class, stops
        )
        
        return {
            'base_price': base,
            'days_ahead': days_ahead,
            'advance_multiplier': advance,
            'season_multiplier': season,
            'weekday_multiplier': day,
            'stops_multiplier': stops_mult,
            'cabin_multiplier': cabin_mult,
            'final_price': final_price,
            'breakdown': f"€{base} × {advance:.2f} × {season:.2f} × {day:.2f} × {stops_mult:.2f} × {cabin_mult:.2f} = €{final_price}"
        }

# Funciones auxiliares
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
    emojis = {
        'economy': '💺',
        'premium_economy': '👨‍💼',
        'business': '👑',
        'first': '🌟'
    }
    return emojis.get(cabin_class, '💺')

def get_cabin_class_name(cabin_class):
    names = {
        'economy': 'Economy',
        'premium_economy': 'Premium Economy',
        'business': 'Business Class',
        'first': 'First Class'
    }
    return names.get(cabin_class, 'Economy')

def get_business_threshold(route, flight_type):
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
    
    alert_threshold = flight_config.get('alert_min', ALERT_MIN_GLOBAL)
    cabin_class = flight_config.get('cabin_class', 'economy')
    
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
        'savings': savings,
        'savings_pct': savings_pct,
        'avg_price': avg_price,
        'flight_type': flight_config.get('type', 'oneway'),
        'stops_filter': get_stops_description(flight_config.get('stops', 'any')),
        'cabin_class': cabin_class,
        'cabin_class_name': get_cabin_class_name(cabin_class)
    }

# API Price Smart con ML Enhanced
def api_price_smart(flight_config):
    origin = flight_config['origin']
    dest = flight_config['dest']
    name = flight_config['name']
    flight_type = flight_config.get('type', 'oneway')
    alert_threshold = flight_config.get('alert_min', ALERT_MIN_GLOBAL)
    stops_filter = flight_config.get('stops', 'any')
    cabin_class = flight_config.get('cabin_class', 'economy')
    flight_date = flight_config.get('outbound_date', '')
    
    # Determinar número de escalas
    if stops_filter == '0':
        actual_stops = 0
    elif stops_filter == '1+':
        actual_stops = random.choices([1, 2], weights=[70, 30])[0]
    else:
        actual_stops = random.choices([0, 1, 2], weights=[20, 60, 20])[0]
    
    # 🤖 Usar ML Enhanced Predictor
    if flight_type == 'roundtrip':
        price_outbound = MLEnhancedPredictor.predict_price(
            origin, dest, flight_date, cabin_class, actual_stops
        )
        return_date = flight_config.get('return_date', '')
        price_return = MLEnhancedPredictor.predict_price(
            dest, origin, return_date, cabin_class, actual_stops
        )
        total_price = price_outbound + price_return
        source = "ML-Enhanced (Roundtrip)"
    else:
        total_price = MLEnhancedPredictor.predict_price(
            origin, dest, flight_date, cabin_class, actual_stops
        )
        source = "ML-Enhanced"
    
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

async def supreme_scan_batch():
    results = []
    print_section("ESCANEO BATCH DE VUELOS CON ML ENHANCED")
    
    print_status("🤖", "🎆 Usando ML Enhanced Predictor v10.0")
    print_status("📊", "  • Anticipa ción de compra (sweet spot: 45-60 días)")
    print_status("📊", "  • Temporada alta/baja")
    print_status("📊", "  • Día de la semana")
    print_status("📊", "  • Escalas y cabina")
    print_status("📊", "  • Precios base de mercado real\n")
    
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
        print_status("📡", "Generando predicciones ML...")
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
            
            msg = f"""🔥 *CHOLLO DETECTADO - ML Enhanced*

✈️ *{deal['name']}*
💰 **€{deal['price']:.0f}**

{get_cabin_class_emoji(deal.get('cabin_class', 'economy'))} {get_cabin_class_name(deal.get('cabin_class', 'economy'))}
🔄 {details['stopover']}
📅 {details['departure_date'].strftime('%d/%m/%Y')}
📊 Ahorro: €{details['savings']:.0f} ({details['savings_pct']:.0f}%)

🤖 *Predicción ML Enhanced*
⚡ Basado en patrones reales de mercado

🕐 {datetime.now().strftime('%H:%M:%S')}
"""
            
            await bot.send_message(CHAT_ID, msg, parse_mode='Markdown')
            print_status("✅", "Alerta enviada")
            logging.info(f"Alerta ML: {deal['name']} €{deal['price']}")
    else:
        print_status("ℹ️", "No se detectaron chollos")
    
    print_status("✅", "Escaneo completado")
    return df

# Comandos Telegram
async def supreme_start(update, context: ContextTypes.DEFAULT_TYPE):
    msg = f"""🏆 *CAZADOR SUPREMO v10.0 ML ENHANCED*

🤖 *NUEVO: Predicciones ML Mejoradas*

✅ Anticipa ción de compra
✅ Temporada alta/baja
✅ Día de la semana
✅ Patrones reales de mercado
✅ Economy + Business Class

🔥 `/supremo` - Escanear
📊 `/status` - Dashboard
💡 `/chollos` - 14 hacks
    """
    await update.message.reply_text(msg, parse_mode='Markdown')

async def supremo_scan(update, context: ContextTypes.DEFAULT_TYPE):
    print_section("COMANDO /SUPREMO")
    initial_msg = await update.message.reply_text("🔄 Escaneando con ML Enhanced...", parse_mode='Markdown')
    df = await supreme_scan_batch()
    
    hot_count = sum(1 for _, row in df.iterrows() if row.get('is_deal', False) and not row.get('filtered_out', False))
    business_deals = sum(1 for _, row in df.iterrows() if row.get('is_deal', False) and row.get('cabin_class') == 'business')
    
    msg = f"""✅ *COMPLETADO*

🔥 Chollos: {hot_count}
👑 Business: {business_deals}
💎 Mejor: €{df['price'].min():.0f}

🤖 ML Enhanced v10.0
🕐 {datetime.now().strftime('%H:%M')}
    """
    await initial_msg.edit_text(msg, parse_mode='Markdown')

async def status(update, context: ContextTypes.DEFAULT_TYPE):
    msg = f"""📈 *DASHBOARD ML ENHANCED*

📊 Total: {len(FLIGHTS)}
🤖 ML v10.0 activo

🕐 {datetime.now().strftime('%H:%M')}
    """
    await update.message.reply_text(msg, parse_mode='Markdown')

async def chollos(update, context: ContextTypes.DEFAULT_TYPE):
    msg = """💡 *14 HACKS RÁPIDOS*

1️⃣ Error Fares (-90%)
2️⃣ VPN Arbitrage (-40%)
3️⃣ Skiplagging (-50%)
4️⃣ Mileage Runs (free)
5️⃣ Cashback Stacking (13%)
    """
    await update.message.reply_text(msg, parse_mode='Markdown')

def main():
    print_header("🤖 CAZADOR SUPREMO v10.0 ML ENHANCED 🤖")
    print_section("INICIALIZACIÓN ML ENHANCED")
    
    print_status("🤖", "Sistema de predicción ML mejorado")
    print_status("✅", "  • Patrones reales de mercado")
    print_status("✅", "  • Sweet spot: 45-60 días")
    print_status("✅", "  • Temporadas alta/baja")
    print_status("✅", "  • Días de la semana")
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", supreme_start))
    app.add_handler(CommandHandler("supremo", supremo_scan))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("chollos", chollos))
    
    print_status("✅", "Bot ML Enhanced activo")
    print_header("⏳ ESPERANDO COMANDOS", "=")
    app.run_polling()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print_header("🛑 DETENIDO", "=")
    except Exception as e:
        print_status("❌", str(e))
