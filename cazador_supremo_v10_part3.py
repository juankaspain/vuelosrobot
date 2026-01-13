# CONTINUACIÓN DE cazador_supremo_v10.py - PARTE 3 FINAL

# ═══════════════════════════════════════════════════════════════════════════
# TELEGRAM BOT HANDLER
# ═══════════════════════════════════════════════════════════════════════════

class TelegramBotHandler:
    """Manejador del bot de Telegram con todos los comandos"""
    
    def __init__(self, config: ConfigManager, monitor: FlightMonitor, 
                 rss_monitor: RSSFeedMonitor, stats_manager: StatisticsManager):
        self.config = config
        self.monitor = monitor
        self.rss_monitor = rss_monitor
        self.stats_manager = stats_manager
        self.bot = Bot(token=config.bot_token)
        self.logger = logging.getLogger('CazadorSupremo.Telegram')
    
    # ────────────────────────────────────────────────────────────────
    # COMANDO: /start
    # ────────────────────────────────────────────────────────────────
    
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /start - Mensaje de bienvenida profesional"""
        user = update.effective_user
        self.logger.info(f"Comando /start ejecutado por {user.username} (ID: {user.id})")
        ConsoleUI.print_info(f"👤 /start por {user.username or user.first_name}")
        
        msg = f"""🏆 *BIENVENIDO A CAZADOR SUPREMO v10.0*

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🔍 *Sistema Enterprise de Monitorización de Vuelos*

Este bot te proporciona:

✅ *Monitoreo 24/7* en tiempo real
✅ *APIs múltiples* con fallback inteligente
✅ *Alertas automáticas* de chollos
✅ *Machine Learning* para predicciones
✅ *RSS Feeds* de ofertas flash
✅ *Estadísticas avanzadas* e histórico

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 *COMANDOS DISPONIBLES:*

🔥 `/supremo`
   ↪️ Escaneo completo de todas las rutas
   ↪️ Análisis con múltiples APIs
   ↪️ Detección automática de chollos

📈 `/status`
   ↪️ Dashboard con estadísticas completas
   ↪️ Histórico de precios
   ↪️ Mejores deals encontrados

📰 `/rss`
   ↪️ Ofertas flash de feeds RSS
   ↪️ SecretFlying, Fly4Free y más
   ↪️ Alertas en tiempo real

💡 `/chollos`
   ↪️ 14 hacks profesionales
   ↪️ Técnicas avanzadas de ahorro
   ↪️ Error fares, VPN arbitrage y más

✈️ `/scan ORIGEN DESTINO`
   ↪️ Analizar ruta específica
   ↪️ Ejemplo: `/scan MAD MGA`

🛠️ `/health`
   ↪️ Estado del sistema
   ↪️ Rendimiento y caché

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚙️ *CONFIGURACIÓN ACTUAL:*

• Umbral de alertas: *€{self.config.alert_threshold}*
• Rutas monitorizadas: *{len(self.config.flight_routes)}*
• Versión: *Enterprise 10.0*
• Autor: *@Juanka_Spain*

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 *Tip Profesional:*
Recibirás alertas automáticas cuando se detecten precios por debajo de €{self.config.alert_threshold}. Usa `/supremo` para iniciar tu primer escaneo.

✨ *¡Listo para cazar las mejores ofertas!*
        """
        
        await update.message.reply_text(msg, parse_mode='Markdown')
        ConsoleUI.print_success("Mensaje de bienvenida enviado")
    
    # ────────────────────────────────────────────────────────────────
    # COMANDO: /supremo
    # ────────────────────────────────────────────────────────────────
    
    async def cmd_supremo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /supremo - Escaneo completo de rutas"""
        user = update.effective_user
        self.logger.info(f"Comando /supremo ejecutado por {user.username} (ID: {user.id})")
        ConsoleUI.print_section("🚀 COMANDO /SUPREMO EJECUTADO")
        ConsoleUI.print_info(f"👤 Usuario: {user.username or user.first_name}")
        
        # Mensaje inicial
        initial_msg = await update.message.reply_text(
            f"🔄 *INICIANDO ESCANEO SUPREMO...*\n\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📡 Consultando *{len(self.config.flight_routes)} rutas*\n"
            f"⏳ Esto puede tomar 10-30 segundos\n"
            f"🤖 Usando múltiples APIs + ML\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"_Analizando precios en tiempo real..._",
            parse_mode='Markdown'
        )
        
        # Escanear rutas
        df = await self.monitor.scan_all_routes()
        
        # Obtener chollos
        hot_deals = self.monitor.get_hot_deals(df)
        
        # Calcular estadísticas
        best_price = df['price'].min()
        best_route = df.loc[df['price'].idxmin(), 'route']
        avg_price = df['price'].mean()
        hot_count = len(hot_deals)
        
        # Enviar alertas de chollos
        if not hot_deals.empty:
            ConsoleUI.print_success(f"🔥 {hot_count} CHOLLOS DETECTADOS!")
            await self._send_hot_deal_alerts(hot_deals)
        
        # Mensaje de resultados
        hot_emoji = "🔥" if hot_count > 0 else "📄"
        alert_status = f"*¡{hot_count} CHOLLOS!*" if hot_count > 0 else "Sin chollos detectados"
        
        msg = f"""✅ *ESCANEO SUPREMO COMPLETADO*

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📈 *RESUMEN DEL ANÁLISIS:*

✈️ *Vuelos escaneados:* {len(df)}
{hot_emoji} *Hot Deals (<€{self.config.alert_threshold}):* {alert_status}
💎 *Mejor precio:* **€{best_price:.0f}** ({best_route})
📉 *Precio promedio:* €{avg_price:.0f}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏆 *TOP 5 MEJORES PRECIOS:*

"""
        
        # Top 5
        top5 = df.nsmallest(5, 'price')
        for idx, row in enumerate(top5.itertuples(), 1):
            status_emoji = "🔥" if row.price < self.config.alert_threshold else "📊"
            status_text = " *¡CHOLLO!*" if row.price < self.config.alert_threshold else ""
            msg += f"{idx}. {status_emoji} *{row.route}*\n"
            msg += f"   💰 €{row.price:.0f}{status_text}\n"
            msg += f"   📡 {row.source}\n\n"
        
        msg += f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🕐 *Completado:* {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

"""
        
        if hot_count > 0:
            msg += "⚡ *¡Acción recomendada!* Revisa las alertas individuales enviadas arriba."
        else:
            msg += "💡 *Tip:* Usa `/status` para ver histórico o ajusta el umbral de alertas."
        
        await initial_msg.edit_text(msg, parse_mode='Markdown')
        ConsoleUI.print_success("✅ Comando /supremo completado")
    
    async def _send_hot_deal_alerts(self, hot_deals: pd.DataFrame):
        """Envía alertas individuales para cada chollo"""
        for idx, row in enumerate(hot_deals.itertuples(), 1):
            savings = self.config.alert_threshold - row.price
            savings_pct = (savings / self.config.alert_threshold) * 100
            
            msg = f"""🚨 *¡ALERTA DE CHOLLO #{idx}!*

━━━━━━━━━━━━━━━━━━━━━━━━

✈️ *Ruta:* {row.route}
💰 *Precio:* **€{row.price:.0f}**
📉 *Ahorro:* €{savings:.0f} ({savings_pct:.0f}%)
📡 *Fuente:* {row.source}

━━━━━━━━━━━━━━━━━━━━━━━━

⚡ *Recomendación:* ¡Reserva rápido!
🕐 *Detectado:* {datetime.now().strftime('%H:%M:%S')}

_Precio por debajo del umbral de €{self.config.alert_threshold}_
            """
            
            await self.bot.send_message(self.config.chat_id, msg, parse_mode='Markdown')
            self.logger.info(f"Alerta enviada: {row.route} €{row.price}")
            await asyncio.sleep(0.5)  # Evitar flood
    
    # ────────────────────────────────────────────────────────────────
    # COMANDO: /status
    # ────────────────────────────────────────────────────────────────
    
    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /status - Dashboard con estadísticas"""
        user = update.effective_user
        self.logger.info(f"Comando /status por {user.username}")
        ConsoleUI.print_info(f"📊 /status por {user.username or user.first_name}")
        
        df = self.stats_manager.load_history()
        
        if df is None or df.empty:
            msg = """📊 *DASHBOARD NO DISPONIBLE*

━━━━━━━━━━━━━━━━━━━━━━━━

ℹ️ Aún no hay datos históricos.

📝 *¿Cómo generar datos?*
Ejecuta `/supremo` para realizar tu primer escaneo.

Una vez completado verás:
• Estadísticas detalladas
• Histórico de precios
• Mejores ofertas
• Tendencias y análisis
            """
            await update.message.reply_text(msg, parse_mode='Markdown')
            return
        
        stats = self.stats_manager.get_statistics(df)
        hot_count = len(df[df['price'] < self.config.alert_threshold])
        hot_pct = (hot_count / stats['total_scans'] * 100) if stats['total_scans'] > 0 else 0
        savings = stats['avg_price'] - stats['min_price']
        savings_pct = (savings / stats['avg_price'] * 100) if stats['avg_price'] > 0 else 0
        
        msg = f"""📈 *DASHBOARD SUPREMO v10.0*

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 *ESTADÍSTICAS GENERALES:*

📋 *Total escaneos:* {stats['total_scans']:,}
💰 *Precio promedio:* €{stats['avg_price']:.2f}
💎 *Precio mínimo:* €{stats['min_price']:.0f}
📈 *Precio máximo:* €{stats['max_price']:.0f}
📊 *Mediana:* €{stats['median_price']:.2f}
🔥 *Chollos detectados:* {hot_count} ({hot_pct:.1f}%)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🏆 *MEJOR DEAL HISTÓRICO:*

✈️ *Ruta:* {stats['best_route']}
💰 *Precio:* **€{stats['min_price']:.0f}**
📉 *Ahorro vs promedio:* €{savings:.0f} ({savings_pct:.1f}%)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚙️ *CONFIGURACIÓN:*

🎯 *Umbral alertas:* €{self.config.alert_threshold}
📡 *Rutas monitorizadas:* {len(self.config.flight_routes)}
📊 *Fuentes de datos:* APIs + ML + RSS

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🕐 *Última actualización:* {datetime.now().strftime('%d/%m/%Y %H:%M')}

💡 *Tip:* Usa `/supremo` regularmente para mejorar estadísticas.
        """
        
        await update.message.reply_text(msg, parse_mode='Markdown')
        ConsoleUI.print_success("Dashboard enviado")
    
    # ────────────────────────────────────────────────────────────────
    # COMANDO: /rss
    # ────────────────────────────────────────────────────────────────
    
    async def cmd_rss(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /rss - Ofertas flash de RSS"""
        user = update.effective_user
        self.logger.info(f"Comando /rss por {user.username}")
        ConsoleUI.print_info(f"📰 /rss por {user.username or user.first_name}")
        
        await update.message.reply_text(
            "📰 *BUSCANDO OFERTAS FLASH...*\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "🔍 Analizando feeds RSS...\n"
            "⏳ _Esto puede tomar unos segundos..._",
            parse_mode='Markdown'
        )
        
        offers = await self.rss_monitor.scan_rss_feeds()
        
        if offers:
            for offer in offers[:3]:  # Top 3
                msg = f"""📰 *OFERTA FLASH DETECTADA*

━━━━━━━━━━━━━━━━━━━━━━━━

{offer['title']}

🔗 [Ver oferta completa]({offer['link']})

━━━━━━━━━━━━━━━━━━━━━━━━

📡 *Fuente:* {offer['source']}
🕐 *Publicado:* {offer['published']}
                """
                await self.bot.send_message(self.config.chat_id, msg, parse_mode='Markdown')
                await asyncio.sleep(0.5)
        else:
            msg = """ℹ️ *NO HAY OFERTAS FLASH AHORA*

El sistema continúa monitorizando.
Te notificaremos cuando aparezcan nuevas ofertas.
            """
            await self.bot.send_message(self.config.chat_id, msg, parse_mode='Markdown')
        
        ConsoleUI.print_success("Búsqueda RSS completada")
    
    # CONTINUAR EN RESPUESTA SIGUIENTE CON /chollos, /scan y /health...