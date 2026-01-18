# [CONTINUACIÓN DE cazador_supremo_v10.py]
# Este archivo contiene la segunda parte del código
# Copiar y pegar después de la clase FlightAPIClient en el archivo principal

# ═══════════════════════════════════════════════════════════════════════════════
# GESTOR DE DATOS E HISTÓRICO
# ═══════════════════════════════════════════════════════════════════════════════

class DataManager:
    """
    Gestor profesional de datos históricos con pandas.
    
    Responsabilidades:
        - Guardar resultados en CSV
        - Cargar y analizar histórico
        - Calcular estadísticas
        - Detectar tendencias
    """
    
    def __init__(self, history_file: str = HISTORY_FILE):
        """
        Inicializa el gestor de datos.
        
        Args:
            history_file: Ruta al archivo CSV de histórico
        """
        self.history_file = Path(history_file)
        logger.info(f"DataManager inicializado con archivo: {history_file}")
    
    def save_results(self, results: List[FlightPrice]) -> bool:
        """
        Guarda resultados de escaneo en el archivo histórico.
        
        Args:
            results: Lista de FlightPrice a guardar
        
        Returns:
            True si se guardó exitosamente
        """
        try:
            df = pd.DataFrame([r.to_dict() for r in results])
            
            if self.history_file.exists():
                df.to_csv(self.history_file, mode='a', header=False, index=False, encoding='utf-8')
                logger.info(f"Añadidos {len(results)} registros al histórico")
            else:
                df.to_csv(self.history_file, index=False, encoding='utf-8')
                logger.info(f"Creado nuevo archivo histórico con {len(results)} registros")
            
            return True
        except Exception as e:
            logger.error(f"Error al guardar resultados: {e}")
            return False
    
    def load_history(self) -> Optional[pd.DataFrame]:
        """
        Carga el histórico de datos.
        
        Returns:
            DataFrame con histórico o None si no existe
        """
        if not self.history_file.exists():
            logger.warning("No existe archivo histórico")
            return None
        
        try:
            df = pd.read_csv(self.history_file, encoding='utf-8')
            logger.info(f"Cargados {len(df)} registros históricos")
            return df
        except Exception as e:
            logger.error(f"Error al cargar histórico: {e}")
            return None
    
    def get_statistics(self) -> Optional[Dict[str, Any]]:
        """
        Calcula estadísticas del histórico.
        
        Returns:
            Diccionario con estadísticas o None si no hay datos
        """
        df = self.load_history()
        if df is None or df.empty:
            return None
        
        try:
            stats = {
                'total_scans': len(df),
                'avg_price': df['price'].mean(),
                'min_price': df['price'].min(),
                'max_price': df['price'].max(),
                'std_price': df['price'].std(),
                'best_route': df.loc[df['price'].idxmin(), 'route'],
                'unique_routes': df['route'].nunique(),
            }
            logger.debug(f"Estadísticas calculadas: {stats}")
            return stats
        except Exception as e:
            logger.error(f"Error al calcular estadísticas: {e}")
            return None
    
    def get_deals_count(self, threshold: float) -> int:
        """
        Cuenta cuántos chollos hay en el histórico.
        
        Args:
            threshold: Umbral de precio para considerar chollo
        
        Returns:
            Número de chollos encontrados
        """
        df = self.load_history()
        if df is None or df.empty:
            return 0
        
        return len(df[df['price'] < threshold])

# ═══════════════════════════════════════════════════════════════════════════════
# MONITOR DE FEEDS RSS
# ═══════════════════════════════════════════════════════════════════════════════

class RSSFeedMonitor:
    """
    Monitor profesional de feeds RSS para ofertas flash.
    
    Características:
        - Parseo de múltiples feeds
        - Detección inteligente de ofertas por palabras clave
        - Extracción de metadatos
    """
    
    DEAL_KEYWORDS = ['sale', 'deal', 'cheap', 'error', 'fare', 'offer', 'promo', 
                     'discount', 'flash', 'limited', 'mistake', 'bargain']
    
    def __init__(self, feed_urls: List[str]):
        """
        Inicializa el monitor de RSS.
        
        Args:
            feed_urls: Lista de URLs de feeds RSS
        """
        self.feed_urls = feed_urls
        logger.info(f"Monitor RSS inicializado con {len(feed_urls)} feeds")
    
    @timing_decorator
    def scan_feeds(self, max_entries: int = 3) -> List[Dict[str, str]]:
        """
        Escanea todos los feeds RSS configurados.
        
        Args:
            max_entries: Máximo de entradas por feed
        
        Returns:
            Lista de ofertas encontradas
        """
        deals = []
        
        for feed_url in self.feed_urls:
            try:
                logger.debug(f"Consultando feed: {feed_url}")
                feed = feedparser.parse(feed_url)
                
                if feed.bozo:
                    logger.warning(f"Feed con formato incorrecto: {feed_url}")
                    continue
                
                feed_deals = self._extract_deals(feed, max_entries)
                deals.extend(feed_deals)
                logger.info(f"Encontradas {len(feed_deals)} ofertas en {feed_url}")
                
            except Exception as e:
                logger.error(f"Error al procesar feed {feed_url}: {e}")
        
        return deals
    
    def _extract_deals(self, feed, max_entries: int) -> List[Dict[str, str]]:
        """
        Extrae ofertas de un feed RSS.
        
        Args:
            feed: Objeto de feedparser
            max_entries: Máximo de entradas a procesar
        
        Returns:
            Lista de ofertas encontradas
        """
        deals = []
        
        for entry in feed.entries[:max_entries]:
            if self._is_deal(entry.title):
                deal = {
                    'title': entry.title,
                    'link': entry.link if hasattr(entry, 'link') else '',
                    'published': entry.published if hasattr(entry, 'published') else 'Reciente',
                    'source': feed.feed.title if hasattr(feed.feed, 'title') else 'RSS Feed'
                }
                deals.append(deal)
        
        return deals
    
    def _is_deal(self, title: str) -> bool:
        """
        Determina si un título corresponde a una oferta.
        
        Args:
            title: Título del artículo
        
        Returns:
            True si parece ser una oferta
        """
        title_lower = title.lower()
        return any(keyword in title_lower for keyword in self.DEAL_KEYWORDS)

# ═══════════════════════════════════════════════════════════════════════════════
# NOTIFICADOR DE TELEGRAM
# ═══════════════════════════════════════════════════════════════════════════════

class TelegramNotifier:
    """
    Gestor profesional de notificaciones vía Telegram.
    
    Características:
        - Formato de mensajes profesional en Markdown
        - Rate limiting para evitar spam
        - Manejo de errores robusto
    """
    
    def __init__(self, bot_token: str, chat_id: str):
        """
        Inicializa el notificador.
        
        Args:
            bot_token: Token del bot de Telegram
            chat_id: ID del chat donde enviar mensajes
        """
        self.bot = Bot(token=bot_token)
        self.chat_id = chat_id
        self.last_message_time = 0
        self.min_interval = 0.5  # Mínimo 0.5s entre mensajes
        logger.info(f"TelegramNotifier inicializado para chat {chat_id}")
    
    async def send_message(self, message: str, parse_mode: str = 'Markdown') -> bool:
        """
        Envía un mensaje por Telegram con rate limiting.
        
        Args:
            message: Texto del mensaje
            parse_mode: Formato del mensaje ('Markdown' o 'HTML')
        
        Returns:
            True si se envió exitosamente
        """
        try:
            # Rate limiting
            current_time = time.time()
            time_since_last = current_time - self.last_message_time
            if time_since_last < self.min_interval:
                await asyncio.sleep(self.min_interval - time_since_last)
            
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=parse_mode
            )
            self.last_message_time = time.time()
            logger.info("Mensaje enviado exitosamente por Telegram")
            return True
            
        except Exception as e:
            logger.error(f"Error al enviar mensaje por Telegram: {e}")
            return False
    
    async def send_deal_alert(self, deal: FlightPrice, threshold: float):
        """
        Envía una alerta de chollo formateada.
        
        Args:
            deal: FlightPrice con información del chollo
            threshold: Umbral de precio configurado
        """
        msg = f"🚨 *¡ALERTA DE CHOLLO DETECTADA!*\n\n"
        msg += f"──────────────────\n"
        msg += f"✈️ *Ruta:* {deal.route}\n"
        msg += f"💰 *Precio:* **€{deal.price:.0f}**\n"
        msg += f"📊 *Fuente:* {deal.source}\n"
        msg += f"──────────────────\n"
        msg += f"⚡ *Recomendación:* ¡Reserva rápido!\n"
        msg += f"🕐 *Detectado:* {deal.timestamp.strftime('%d/%m/%Y %H:%M:%S')}\n\n"
        msg += f"_Precio por debajo del umbral de €{threshold}_"
        
        await self.send_message(msg)
    
    async def send_rss_deal(self, deal: Dict[str, str]):
        """
        Envía una alerta de oferta RSS.
        
        Args:
            deal: Diccionario con información de la oferta
        """
        msg = f"📰 *OFERTA FLASH DETECTADA*\n\n"
        msg += f"──────────────────\n"
        msg += f"{deal['title']}\n\n"
        msg += f"🔗 [Ver oferta completa]({deal['link']})\n"
        msg += f"──────────────────\n"
        msg += f"📡 *Fuente:* {deal['source']}\n"
        msg += f"🕐 *Publicado:* {deal['published']}"
        
        await self.send_message(msg)

# ═══════════════════════════════════════════════════════════════════════════════
# ESCANEADOR DE VUELOS
# ═══════════════════════════════════════════════════════════════════════════════

class FlightScanner:
    """
    Motor principal de escaneo de vuelos.
    
    Coordina todas las operaciones de escaneo:
        - Consulta APIs en paralelo
        - Gestiona datos históricos
        - Envía alertas automáticas
    """
    
    def __init__(self, 
                 config_manager: ConfigManager,
                 api_client: FlightAPIClient,
                 data_manager: DataManager,
                 notifier: TelegramNotifier):
        """
        Inicializa el escaneador.
        
        Args:
            config_manager: Gestor de configuración
            api_client: Cliente de APIs
            data_manager: Gestor de datos
            notifier: Notificador de Telegram
        """
        self.config = config_manager
        self.api = api_client
        self.data = data_manager
        self.notifier = notifier
        self.flights = config_manager.get_flights()
        self.threshold = config_manager.get_alert_threshold()
        logger.info(f"FlightScanner inicializado con {len(self.flights)} rutas")
    
    @async_timing_decorator
    async def scan_all_flights(self) -> Tuple[List[FlightPrice], int]:
        """
        Escanea todas las rutas configuradas en paralelo.
        
        Returns:
            Tupla con (lista de precios, número de chollos)
        """
        ConsoleFormatter.print_section("ESCANEO BATCH DE VUELOS")
        ConsoleFormatter.print_status(
            "🚀", 
            f"Iniciando escaneo de {len(self.flights)} vuelos en paralelo"
        )
        logger.info(f"Iniciando scan batch de {len(self.flights)} vuelos")
        
        results = []
        
        # Escaneo paralelo con ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [
                executor.submit(
                    self.api.get_price,
                    flight.origin,
                    flight.dest,
                    flight.name
                )
                for flight in self.flights
            ]
            
            completed = 0
            for future in as_completed(futures):
                try:
                    result = future.result()
                    completed += 1
                    ConsoleFormatter.print_status(
                        "✓",
                        f"[{completed}/{len(self.flights)}] {result.route} - €{result.price:.0f} ({result.source})"
                    )
                    results.append(result)
                except Exception as e:
                    logger.error(f"Error en escaneo de vuelo: {e}")
        
        # Guardar resultados
        self.data.save_results(results)
        
        # Detectar chollos
        deals = [r for r in results if r.is_deal(self.threshold)]
        
        # Enviar alertas
        if deals:
            ConsoleFormatter.print_status(
                "🔥",
                f"¡{len(deals)} CHOLLOS DETECTADOS!",
                "ALERT"
            )
            await self._send_deal_alerts(deals)
        else:
            ConsoleFormatter.print_status(
                "ℹ️",
                "No se detectaron chollos en este escaneo"
            )
        
        logger.info(f"Scan batch completado: {len(results)} vuelos, {len(deals)} chollos")
        return results, len(deals)
    
    async def _send_deal_alerts(self, deals: List[FlightPrice]):
        """
        Envía alertas para todos los chollos detectados.
        
        Args:
            deals: Lista de FlightPrice que son chollos
        """
        ConsoleFormatter.print_section("ENVIANDO ALERTAS TELEGRAM")
        
        for idx, deal in enumerate(deals, 1):
            ConsoleFormatter.print_status(
                "📨",
                f"Enviando alerta [{idx}/{len(deals)}]: {deal.route} - €{deal.price:.0f}"
            )
            await self.notifier.send_deal_alert(deal, self.threshold)
            logger.info(f"Alerta enviada: {deal.route} €{deal.price}")

# ═══════════════════════════════════════════════════════════════════════════════
# MANEJADORES DE COMANDOS DE TELEGRAM
# ═══════════════════════════════════════════════════════════════════════════════

class CommandHandlers:
    """
    Manejadores de comandos del bot de Telegram.
    
    Implementa todos los comandos disponibles de forma profesional.
    """
    
    def __init__(self, 
                 config: ConfigManager,
                 scanner: FlightScanner,
                 data_manager: DataManager,
                 notifier: TelegramNotifier,
                 rss_monitor: RSSFeedMonitor):
        self.config = config
        self.scanner = scanner
        self.data = data_manager
        self.notifier = notifier
        self.rss = rss_monitor
        self.threshold = config.get_alert_threshold()
        logger.info("CommandHandlers inicializado")
    
    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /start - Mensaje de bienvenida."""
        user = update.effective_user
        ConsoleFormatter.print_section("COMANDO /START EJECUTADO")
        ConsoleFormatter.print_status("👤", f"Usuario: {user.username or user.first_name}")
        logger.info(f"/start ejecutado por {user.id}")
        
        msg = f"""🏆 *BIENVENIDO A {APP_NAME} v{VERSION}*

────────────────────

*Sistema Profesional de Monitorización de Vuelos*

Este bot te ayudará a encontrar las mejores ofertas mediante:

✅ Monitorización 24/7 en tiempo real
✅ Integración con múltiples APIs de vuelos
✅ Alertas automáticas de chollos
✅ Predicciones con Machine Learning
✅ Feeds RSS de ofertas flash

────────────────────

📋 *COMANDOS DISPONIBLES:*

🔥 `/supremo` - Escanear todos los vuelos
📊 `/status` - Ver estadísticas y dashboard
📰 `/rss` - Buscar ofertas flash RSS
💡 `/chollos` - 14 hacks profesionales
🛫 `/scan ORIGEN DESTINO` - Escanear ruta específica

────────────────────

⚙️ *CONFIGURACIÓN:*
• Umbral de alerta: €{self.threshold}
• Rutas monitorizadas: {len(self.scanner.flights)}

💬 ¿Listo? Usa `/supremo` para empezar
        """
        
        await update.message.reply_text(msg, parse_mode='Markdown')
        ConsoleFormatter.print_status("✅", "Mensaje de bienvenida enviado")
    
    async def cmd_supremo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /supremo - Escaneo completo de vuelos."""
        user = update.effective_user
        ConsoleFormatter.print_section("COMANDO /SUPREMO EJECUTADO")
        ConsoleFormatter.print_status("👤", f"Usuario: {user.username or user.first_name}")
        logger.info(f"/supremo ejecutado por {user.id}")
        
        # Mensaje inicial
        initial_msg = await update.message.reply_text(
            "🔄 *INICIANDO ESCANEO SUPREMO...*\n\n"
            "─────────────\n"
            f"📡 Consultando {len(self.scanner.flights)} rutas\n"
            "⏳ Esto puede tomar unos segundos\n"
            "─────────────\n\n"
            "_Analizando precios con múltiples APIs..._",
            parse_mode='Markdown'
        )
        
        # Ejecutar escaneo
        results, deals_count = await self.scanner.scan_all_flights()
        
        # Calcular estadísticas
        df = pd.DataFrame([r.to_dict() for r in results])
        best_price = df['price'].min()
        best_route = df.loc[df['price'].idxmin(), 'route']
        avg_price = df['price'].mean()
        
        # Mensaje de respuesta
        hot_emoji = "🔥" if deals_count > 0 else "📊"
        alert_text = f"*¡{deals_count} CHOLLOS!*" if deals_count > 0 else "Sin chollos"
        
        msg = f"""✅ *ESCANEO COMPLETADO*

─────────────────

📊 *RESUMEN:*

✈️ Vuelos: {len(df)}
{hot_emoji} Hot deals: {alert_text}
💎 Mejor: **€{best_price:.0f}** ({best_route})
📈 Promedio: €{avg_price:.0f}

─────────────────

🏆 *TOP 5:*

"""
        
        top5 = df.nsmallest(5, 'price')
        for idx, (_, row) in enumerate(top5.iterrows(), 1):
            emoji = "🔥" if row['price'] < self.threshold else "📊"
            msg += f"{idx}. {emoji} *{row['route']}* - €{row['price']:.0f}\n"
        
        msg += f"\n🕐 {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        
        await initial_msg.edit_text(msg, parse_mode='Markdown')
        ConsoleFormatter.print_status("✅", "Comando /supremo completado")
    
    async def cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /status - Dashboard de estadísticas."""
        ConsoleFormatter.print_section("COMANDO /STATUS EJECUTADO")
        logger.info(f"/status ejecutado")
        
        stats = self.data.get_statistics()
        
        if not stats:
            msg = "📊 *DASHBOARD NO DISPONIBLE*\n\n"
            msg += "No hay datos históricos aún.\n"
            msg += "Ejecuta `/supremo` para generar datos."
            await update.message.reply_text(msg, parse_mode='Markdown')
            return
        
        deals_count = self.data.get_deals_count(self.threshold)
        hot_pct = (deals_count / stats['total_scans'] * 100) if stats['total_scans'] > 0 else 0
        
        msg = f"""📈 *DASHBOARD SUPREMO v{VERSION}*

─────────────────

📋 Total escaneos: {stats['total_scans']}
💰 Promedio: €{stats['avg_price']:.2f}
💎 Mínimo: €{stats['min_price']:.0f}
📈 Máximo: €{stats['max_price']:.0f}
🔥 Chollos: {deals_count} ({hot_pct:.1f}%)

─────────────────

🏆 *MEJOR DEAL:*

✈️ {stats['best_route']}
💰 **€{stats['min_price']:.0f}**

🕐 {datetime.now().strftime('%d/%m/%Y %H:%M')}
        """
        
        await update.message.reply_text(msg, parse_mode='Markdown')
        ConsoleFormatter.print_status("✅", "Dashboard enviado")
    
    async def cmd_rss(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /rss - Buscar ofertas flash en RSS."""
        ConsoleFormatter.print_section("COMANDO /RSS EJECUTADO")
        logger.info("/rss ejecutado")
        
        await update.message.reply_text(
            "📰 *BUSCANDO OFERTAS FLASH...*\n\nAnalizando feeds RSS...",
            parse_mode='Markdown'
        )
        
        deals = self.rss.scan_feeds()
        
        if deals:
            for deal in deals:
                await self.notifier.send_rss_deal(deal)
            ConsoleFormatter.print_status("✅", f"{len(deals)} ofertas RSS enviadas")
        else:
            await self.notifier.send_message(
                "ℹ️ No se encontraron ofertas flash en este momento.\n"
                "El sistema continúa monitorizando."
            )
        
        ConsoleFormatter.print_status("✅", "Comando /rss completado")
    
    async def cmd_chollos(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /chollos - Lista de hacks profesionales."""
        ConsoleFormatter.print_section("COMANDO /CHOLLOS EJECUTADO")
        logger.info("/chollos ejecutado")
        
        msg = """💡 *14 HACKS PROFESIONALES*

─────────────────

🎯 *ESTRATEGIAS:*

1️⃣ Error Fares (-90%)
2️⃣ VPN Arbitrage (-40%)
3️⃣ Skiplagging (-50%)
4️⃣ Mileage Runs (gratis)

💳 *PAGOS:*

5️⃣ Cashback Stacking (13%)
6️⃣ Points Hacking (678+ programas)
7️⃣ Manufactured Spending

🗺️ *RUTAS:*

8️⃣ Stopovers Gratis (2x1)
9️⃣ Hidden City (-40%)
🔟 Multi-City Combos

🤖 *HERRAMIENTAS:*

1️⃣1️⃣ Google Flights Alerts
1️⃣2️⃣ Skyscanner Everywhere
1️⃣3️⃣ Hopper Price Freeze
1️⃣4️⃣ Award Travel

─────────────────

💡 Combina técnicas para máximo ahorro
⚠️ Algunas técnicas están en zona gris legal
        """
        
        await update.message.reply_text(msg, parse_mode='Markdown')
        ConsoleFormatter.print_status("✅", "Lista de hacks enviada")
    
    async def cmd_scan(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /scan ORIGEN DESTINO - Escanear ruta específica."""
        ConsoleFormatter.print_section("COMANDO /SCAN EJECUTADO")
        logger.info("/scan ejecutado")
        
        if len(context.args) < 2:
            msg = "❌ *FORMATO INCORRECTO*\n\n"
            msg += "`/scan ORIGEN DESTINO`\n\n"
            msg += "Ejemplo: `/scan MAD MGA`"
            await update.message.reply_text(msg, parse_mode='Markdown')
            return
        
        origin = context.args[0].upper()
        dest = context.args[1].upper()
        
        try:
            route = FlightRoute(origin, dest, f"{origin}-{dest}")
        except ValueError as e:
            await update.message.reply_text(f"❌ Error: {e}", parse_mode='Markdown')
            return
        
        initial_msg = await update.message.reply_text(
            f"🔄 *ESCANEANDO {route.to_route_string()}...*\n\n"
            "_Consultando APIs..._",
            parse_mode='Markdown'
        )
        
        # Obtener precio
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                self.scanner.api.get_price,
                route.origin,
                route.dest,
                route.name
            )
            result = future.result()
        
        is_deal = result.is_deal(self.threshold)
        emoji = "🔥" if is_deal else "📊"
        status = "*¡CHOLLO!*" if is_deal else "Precio normal"
        
        msg = f"""✅ *ANÁLISIS COMPLETADO*

─────────────────

✈️ *Ruta:* {result.route}
💵 *Precio:* **€{result.price:.0f}**
📊 *Fuente:* {result.source}
{emoji} *Estado:* {status}

─────────────────

🕐 {datetime.now().strftime('%d/%m/%Y %H:%M')}
        """
        
        await initial_msg.edit_text(msg, parse_mode='Markdown')
        ConsoleFormatter.print_status("✅", f"Escaneo de {route.to_route_string()} completado")

# ═══════════════════════════════════════════════════════════════════════════════
# FUNCIÓN PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """
    Función principal del sistema.
    
    Inicializa todos los componentes y ejecuta el bot.
    """
    try:
        # Banner de inicio
        ConsoleFormatter.print_header(f"🏆  {APP_NAME} v{VERSION}  🏆")
        ConsoleFormatter.safe_print("Sistema Profesional de Monitorización de Vuelos".center(80))
        ConsoleFormatter.print_header("", "═")
        
        logger.info(f"Iniciando {APP_NAME} v{VERSION}")
        
        # Inicializar componentes
        ConsoleFormatter.print_section("INICIALIZACIÓN DEL SISTEMA")
        
        ConsoleFormatter.print_status("📂", "Cargando configuración...")
        config = ConfigManager()
        
        ConsoleFormatter.print_status("🚀", "Inicializando cliente de APIs...")
        api_client = FlightAPIClient(config.get_api_keys())
        
        ConsoleFormatter.print_status("💾", "Configurando gestor de datos...")
        data_manager = DataManager()
        
        ConsoleFormatter.print_status("📢", "Conectando con Telegram...")
        notifier = TelegramNotifier(
            config.get_telegram_token(),
            config.get_chat_id()
        )
        
        ConsoleFormatter.print_status("📰", "Configurando monitor RSS...")
        rss_monitor = RSSFeedMonitor(config.get_rss_feeds())
        
        ConsoleFormatter.print_status("✈️", "Inicializando escaneador de vuelos...")
        scanner = FlightScanner(config, api_client, data_manager, notifier)
        
        # Mostrar configuración
        ConsoleFormatter.print_section("CONFIGURACIÓN ACTUAL")
        ConsoleFormatter.print_result("Vuelos configurados", len(config.get_flights()), "✈️")
        ConsoleFormatter.print_result("Umbral de alerta", f"€{config.get_alert_threshold()}", "💰")
        ConsoleFormatter.print_result("Feeds RSS", len(config.get_rss_feeds()), "📰")
        
        # Crear aplicación de Telegram
        ConsoleFormatter.print_section("INICIALIZANDO BOT TELEGRAM")
        ConsoleFormatter.print_status("🤖", "Creando aplicación de Telegram...")
        
        app = Application.builder().token(config.get_telegram_token()).build()
        
        # Registrar comandos
        handlers = CommandHandlers(config, scanner, data_manager, notifier, rss_monitor)
        
        ConsoleFormatter.print_status("📝", "Registrando comandos del bot...")
        app.add_handler(CommandHandler("start", handlers.cmd_start))
        app.add_handler(CommandHandler("supremo", handlers.cmd_supremo))
        app.add_handler(CommandHandler("status", handlers.cmd_status))
        app.add_handler(CommandHandler("rss", handlers.cmd_rss))
        app.add_handler(CommandHandler("chollos", handlers.cmd_chollos))
        app.add_handler(CommandHandler("scan", handlers.cmd_scan))
        
        # Sistema listo
        ConsoleFormatter.print_section("BOT ACTIVO Y OPERATIVO")
        ConsoleFormatter.print_box(
            "COMANDOS DISPONIBLES",
            [
                "/start - Mensaje de bienvenida",
                "/supremo - Escaneo completo de vuelos",
                "/status - Dashboard de estadísticas",
                "/rss - Buscar ofertas flash",
                "/chollos - 14 hacks profesionales",
                "/scan ORIG DEST - Escanear ruta específica"
            ]
        )
        
        ConsoleFormatter.print_status("ℹ️", f"Alertas automáticas < €{config.get_alert_threshold()}")
        ConsoleFormatter.print_status("💾", f"Histórico: {HISTORY_FILE}")
        ConsoleFormatter.print_status("📝", f"Logs: {LOG_FILE}")
        
        ConsoleFormatter.print_header("⏳ ESPERANDO COMANDOS", "═")
        ConsoleFormatter.print_status("👂", "Bot en modo escucha...")
        ConsoleFormatter.safe_print("(Presiona Ctrl+C para detener)\n")
        
        logger.info("Bot iniciado y en modo escucha")
        
        # Ejecutar bot
        app.run_polling()
        
    except KeyboardInterrupt:
        ConsoleFormatter.print_header("🛑 DETENCIÓN SOLICITADA", "═")
        ConsoleFormatter.print_status("⏹️", "Cerrando conexiones...")
        ConsoleFormatter.print_status("💾", "Guardando estado...")
        ConsoleFormatter.print_header("✅ BOT DETENIDO CORRECTAMENTE", "═")
        logger.info("Bot detenido manualmente")
        
    except Exception as e:
        ConsoleFormatter.print_header("❌ ERROR CRÍTICO", "═")
        ConsoleFormatter.print_status("⚠️", f"Error: {e}", "ERROR")
        logger.critical(f"Error crítico: {e}", exc_info=True)
        raise

if __name__ == '__main__':
    main()