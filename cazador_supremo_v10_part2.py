# CONTINUACIÓN DE cazador_supremo_v10.py - PARTE 2

# ═══════════════════════════════════════════════════════════════════════════
# API FLIGHT PRICE CLIENT
# ═══════════════════════════════════════════════════════════════════════════

class FlightPriceAPI:
    """Cliente para consultar precios de vuelos con múltiples APIs y fallback"""
    
    def __init__(self, config: ConfigManager, cache: CacheManager, rate_limiter: RateLimiter):
        self.config = config
        self.cache = cache
        self.rate_limiter = rate_limiter
        self.logger = logging.getLogger('CazadorSupremo.API')
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'CazadorSupremo/10.0'})
    
    @retry_on_failure(max_attempts=2, delay=1.0)
    @measure_time
    def get_price(self, route: FlightRoute) -> FlightPrice:
        """
        Obtiene precio de vuelo usando múltiples fuentes con fallback
        
        Args:
            route: Ruta de vuelo a consultar
        
        Returns:
            FlightPrice con el precio y metadata
        
        Raises:
            APIError: Si todas las APIs fallan
        """
        # Verificar caché primero
        cache_key = f"price_{route.route_key}"
        cached = self.cache.get(cache_key)
        if cached:
            self.logger.info(f"Precio obtenido de caché: {route.route_key}")
            return cached
        
        # Rate limiting
        self.rate_limiter.wait_if_needed()
        
        # Intentar APIs en orden
        price_data = None
        
        # 1. AviationStack
        if not price_data:
            price_data = self._try_aviationstack(route)
        
        # 2. SerpApi
        if not price_data:
            price_data = self._try_serpapi(route)
        
        # 3. Fallback: Precio estimado con ML
        if not price_data:
            price_data = self._ml_estimate(route)
        
        # Crear objeto FlightPrice
        flight_price = FlightPrice(
            route=route.route_key,
            name=route.name,
            price=price_data['price'],
            source=price_data['source'],
            timestamp=datetime.now()
        )
        
        # Guardar en caché
        self.cache.set(cache_key, flight_price)
        
        self.logger.info(f"Precio obtenido: {route.route_key} = €{flight_price.price:.2f} ({flight_price.source})")
        return flight_price
    
    def _try_aviationstack(self, route: FlightRoute) -> Optional[Dict]:
        """Intenta obtener precio de AviationStack"""
        try:
            api_key = self.config.get('apis', {}).get('aviationstack')
            if not api_key or api_key == "TU_CLAVE_AVIATIONSTACK_AQUI":
                return None
            
            url = "http://api.aviationstack.com/v1/flights"
            params = {
                'access_key': api_key,
                'dep_iata': route.origin,
                'arr_iata': route.dest,
                'limit': 1
            }
            
            self.logger.debug(f"Consultando AviationStack: {route.route_key}")
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if 'data' in data and len(data['data']) > 0:
                flight_data = data['data'][0]
                price = flight_data.get('pricing', {}).get('total')
                if price:
                    self.logger.info(f"AviationStack: {route.route_key} = €{price}")
                    return {'price': float(price), 'source': 'AviationStack'}
        
        except requests.exceptions.RequestException as e:
            self.logger.warning(f"AviationStack error para {route.route_key}: {e}")
        except Exception as e:
            self.logger.error(f"Error inesperado en AviationStack: {e}")
        
        return None
    
    def _try_serpapi(self, route: FlightRoute) -> Optional[Dict]:
        """Intenta obtener precio de SerpApi (Google Flights)"""
        try:
            api_key = self.config.get('apis', {}).get('serpapi')
            if not api_key or api_key == "TU_CLAVE_SERPAPI_AQUI":
                return None
            
            url = "https://serpapi.com/search.json"
            params = {
                'engine': 'google_flights',
                'api_key': api_key,
                'departure_id': route.origin,
                'arrival_id': route.dest,
                'outbound_date': (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
                'currency': 'EUR'
            }
            
            self.logger.debug(f"Consultando SerpApi: {route.route_key}")
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if 'best_flights' in data and len(data['best_flights']) > 0:
                price = data['best_flights'][0].get('price')
                if price:
                    self.logger.info(f"SerpApi: {route.route_key} = €{price}")
                    return {'price': float(price), 'source': 'GoogleFlights'}
        
        except requests.exceptions.RequestException as e:
            self.logger.warning(f"SerpApi error para {route.route_key}: {e}")
        except Exception as e:
            self.logger.error(f"Error inesperado en SerpApi: {e}")
        
        return None
    
    def _ml_estimate(self, route: FlightRoute) -> Dict:
        """
        Genera estimación de precio usando modelo simple
        En producción, esto usaría un modelo ML real
        """
        self.logger.info(f"Usando estimación ML para {route.route_key}")
        
        # Precios base realistas por tipo de ruta
        if route.dest == 'MAD' or route.origin == 'MAD':
            base_price = 600
            variance = 200
        elif route.dest in ['NYC', 'JFK', 'EWR'] or route.origin in ['NYC', 'JFK', 'EWR']:
            base_price = 800
            variance = 300
        else:
            base_price = 700
            variance = 250
        
        # Añadir variación aleatoria pero consistente
        random.seed(route.route_key)  # Seed basado en ruta para consistencia
        price = base_price + random.uniform(-variance, variance)
        
        return {
            'price': round(price, 2),
            'source': 'ML-Estimate'
        }

# ═══════════════════════════════════════════════════════════════════════════
# FLIGHT MONITOR
# ═══════════════════════════════════════════════════════════════════════════

class FlightMonitor:
    """Monitor de vuelos con escaneo batch y alertas"""
    
    def __init__(self, config: ConfigManager, api_client: FlightPriceAPI):
        self.config = config
        self.api_client = api_client
        self.logger = logging.getLogger('CazadorSupremo.Monitor')
        self.data_file = Path('data/deals_history.csv')
        self._ensure_data_directory()
    
    def _ensure_data_directory(self):
        """Crea directorio de datos si no existe"""
        self.data_file.parent.mkdir(exist_ok=True)
    
    @measure_time
    async def scan_all_routes(self) -> pd.DataFrame:
        """
        Escanea todas las rutas configuradas en paralelo
        
        Returns:
            DataFrame con todos los precios
        """
        routes = self.config.flight_routes
        ConsoleUI.print_section(f"ESCANEO BATCH: {len(routes)} RUTAS")
        ConsoleUI.print_info(f"🚀 Iniciando escaneo paralelo con {min(20, len(routes))} workers...")
        
        results = []
        
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = {executor.submit(self.api_client.get_price, route): route for route in routes}
            
            for idx, future in enumerate(as_completed(futures), 1):
                try:
                    price_data = future.result()
                    results.append(price_data)
                    
                    # Status con color
                    if price_data.is_hot_deal(self.config.alert_threshold):
                        ConsoleUI.print_success(
                            f"[{idx}/{len(routes)}] {price_data.route} = €{price_data.price:.0f} 🔥 CHOLLO!"
                        )
                    else:
                        ConsoleUI.print_info(
                            f"[{idx}/{len(routes)}] {price_data.route} = €{price_data.price:.0f} ({price_data.source})"
                        )
                
                except Exception as e:
                    route = futures[future]
                    ConsoleUI.print_error(f"Error en {route.route_key}: {e}")
                    self.logger.error(f"Error escaneando {route.route_key}", exc_info=True)
        
        # Convertir a DataFrame
        df = self._results_to_dataframe(results)
        
        # Guardar histórico
        self._save_to_history(df)
        
        ConsoleUI.print_success(f"✅ Escaneo completado: {len(results)} rutas procesadas")
        return df
    
    def _results_to_dataframe(self, results: List[FlightPrice]) -> pd.DataFrame:
        """Convierte lista de FlightPrice a DataFrame"""
        data = [price.to_dict() for price in results]
        return pd.DataFrame(data)
    
    def _save_to_history(self, df: pd.DataFrame):
        """Guarda resultados en historial CSV"""
        try:
            if self.data_file.exists():
                df.to_csv(self.data_file, mode='a', header=False, index=False, encoding='utf-8')
                ConsoleUI.print_info(f"💾 Datos añadidos a {self.data_file}")
            else:
                df.to_csv(self.data_file, index=False, encoding='utf-8')
                ConsoleUI.print_success(f"💾 Archivo creado: {self.data_file}")
            
            self.logger.info(f"{len(df)} registros guardados en historial")
        
        except Exception as e:
            ConsoleUI.print_error(f"Error guardando historial: {e}")
            self.logger.error("Error guardando historial", exc_info=True)
    
    def get_hot_deals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Filtra chollos basado en umbral"""
        threshold = self.config.alert_threshold
        return df[df['price'] < threshold]

# ═══════════════════════════════════════════════════════════════════════════
# RSS FEED MONITOR
# ═══════════════════════════════════════════════════════════════════════════

class RSSFeedMonitor:
    """Monitor de feeds RSS para ofertas flash"""
    
    def __init__(self, config: ConfigManager):
        self.config = config
        self.logger = logging.getLogger('CazadorSupremo.RSS')
        self.keywords = ['sale', 'deal', 'cheap', 'error', 'fare', 'flash', 'promo', 'discount']
    
    @measure_time
    async def scan_rss_feeds(self) -> List[Dict]:
        """
        Escanea todos los feeds RSS configurados
        
        Returns:
            Lista de ofertas encontradas
        """
        feeds = self.config.get('rss_feeds', [])
        ConsoleUI.print_section(f"BÚSQUEDA RSS: {len(feeds)} FEEDS")
        
        offers = []
        
        for idx, feed_url in enumerate(feeds, 1):
            try:
                ConsoleUI.print_info(f"🔍 Analizando feed [{idx}/{len(feeds)}]...")
                feed = feedparser.parse(feed_url)
                
                if not feed.entries:
                    ConsoleUI.print_warning(f"Feed vacío o inaccesible: {feed_url[:50]}...")
                    continue
                
                ConsoleUI.print_success(f"✅ {len(feed.entries)} entradas encontradas")
                
                # Analizar top 5 entradas
                for entry in feed.entries[:5]:
                    if self._is_deal(entry):
                        offer = {
                            'title': entry.title,
                            'link': entry.link,
                            'published': getattr(entry, 'published', 'Reciente'),
                            'source': getattr(feed.feed, 'title', 'RSS Feed')
                        }
                        offers.append(offer)
                        ConsoleUI.print_success(f"🔥 Oferta: {entry.title[:60]}...")
                        self.logger.info(f"Oferta RSS detectada: {entry.title}")
            
            except Exception as e:
                ConsoleUI.print_error(f"Error procesando feed: {e}")
                self.logger.error(f"Error en feed {feed_url}", exc_info=True)
        
        if offers:
            ConsoleUI.print_success(f"🎉 {len(offers)} ofertas flash encontradas!")
        else:
            ConsoleUI.print_info("ℹ️  No se encontraron ofertas en este momento")
        
        return offers
    
    def _is_deal(self, entry) -> bool:
        """Determina si una entrada es una oferta"""
        title_lower = entry.title.lower()
        return any(keyword in title_lower for keyword in self.keywords)

# ═══════════════════════════════════════════════════════════════════════════
# STATISTICS MANAGER
# ═══════════════════════════════════════════════════════════════════════════

class StatisticsManager:
    """Gestor de estadísticas y análisis de datos"""
    
    def __init__(self, data_file: Path):
        self.data_file = data_file
        self.logger = logging.getLogger('CazadorSupremo.Stats')
    
    def load_history(self) -> Optional[pd.DataFrame]:
        """Carga historial de datos"""
        if not self.data_file.exists():
            self.logger.warning("Archivo de historial no existe")
            return None
        
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8')
            self.logger.info(f"Historial cargado: {len(df)} registros")
            return df
        except Exception as e:
            self.logger.error(f"Error cargando historial: {e}")
            return None
    
    def get_statistics(self, df: pd.DataFrame) -> Dict:
        """Calcula estadísticas completas"""
        stats = {
            'total_scans': len(df),
            'avg_price': df['price'].mean(),
            'min_price': df['price'].min(),
            'max_price': df['price'].max(),
            'median_price': df['price'].median(),
            'std_dev': df['price'].std(),
            'best_route': df.loc[df['price'].idxmin(), 'route'],
            'worst_route': df.loc[df['price'].idxmax(), 'route'],
        }
        return stats
    
    def get_best_deals(self, df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
        """Obtiene los mejores deals históricos"""
        return df.nsmallest(top_n, 'price')

# NOTA: La parte 3 contendrá el TelegramBotHandler completo y la función main()
# Este archivo debe ser concatenado con la parte 1 para el código completo