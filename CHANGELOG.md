# 📝 Changelog - Cazador Supremo Enterprise

## [12.2.0-iter2] - 2026-01-14

### ✨ ITERACIÓN 2/3 - COMPLETADA

#### 🆕 Nuevos Comandos Implementados

**`/route ORIGEN DESTINO FECHA`**
- Búsqueda personalizada de vuelos
- Ventana flexible de ±3 días automática
- Extracción de info completa (aerolínea, escalas, fecha)
- Ordenación por precio
- Ejemplo: `/route MAD BCN 2026-02-15`

**`/deals`**
- Detección automática de chollos
- Comparación vs promedio histórico 30 días
- Threshold configurable (default 20% ahorro)
- Notificaciones automáticas con cooldown 30min
- Muestra top 3 mejores deals

**`/trends RUTA`**
- Análisis de tendencias 90 días
- Estadísticas: media, mínimo, máximo
- Detección de dirección (subiendo/bajando/estable)
- Recomendaciones inteligentes de compra
- Ejemplo: `/trends MAD-MIA`

#### 🛠️ Componentes Nuevos

**FlightScanner Enhanced**
```python
- scan_route_flexible() # Búsqueda ±3 días
- _extract_airline_from_serpapi() # Extrae aerolínea
- _extract_stops_from_serpapi() # Extrae número de escalas
```

**DealsManager**
```python
- find_deals() # Detecta chollos vs histórico
- should_notify() # Controla cooldown notificaciones
- mark_notified() # Marca deal como notificado
```

**TrendsAnalyzer**
```python
- analyze_route() # Análisis completo de tendencias
- _get_recommendation() # IA para recomendar compra
```

**DataManager Enhanced**
```python
- get_price_history() # Historial 90 días
- get_historical_avg() # Promedio configurable
```

**TelegramBotManager Enhanced**
```python
- _auto_scan_loop() # Escaneos automáticos periódicos
- _notify_deal() # Envía notificaciones de deals
- cmd_route() # Handler /route
- cmd_deals() # Handler /deals
- cmd_trends() # Handler /trends
```

#### 📊 Métricas del Proyecto

- **Líneas de Código**: ~1,800
- **Clases Totales**: 15
- **Comandos Bot**: 8
- **Rutas ML Base**: 50+
- **Design Patterns**: 5 (Circuit Breaker, Retry, Cache, Observer, Factory)
- **Integraciones API**: 2 (SerpAPI, Telegram)

#### ⚙️ Configuración Nueva

**config.json extendido:**
```json
{
  "auto_scan": false,
  "deal_threshold_pct": 20,
  "apis": {
    "serpapi_key": "YOUR_KEY"
  }
}
```

- `auto_scan`: Activa escaneos automáticos cada hora
- `deal_threshold_pct`: % mínimo de ahorro para considerar deal

#### 🐛 Fixes

- Mejorada extracción de datos desde SerpAPI
- Añadida validación de argumentos en /route
- Optimizado uso de caché para múltiples fechas
- Corregido manejo de errores en auto-scan

---

## [12.1.2] - 2026-01-13

### 🔧 Hotfix - SerpAPI

- **FIX**: Error 400 Bad Request en SerpAPI
- Añadido `type=2` para vuelos one-way
- Eliminado requerimiento de `return_date`

---

## [12.1.1] - 2026-01-13

### ✨ Testing Tools

- **NUEVO**: Comando `/clearcache`
- Limpia caché sin reiniciar
- Muestra estadísticas antes de limpiar

---

## [12.1.0] - 2026-01-13

### 🚀 Real API Integration

- **NUEVO**: Integración real SerpAPI
- Llamadas HTTP a Google Flights
- Extracción inteligente de precios
- Métricas de rendimiento por API
- Circuit breaker 3-state

---

## [12.0.2] - 2026-01-13

### 🐛 Hotfix

- **FIX**: AttributeError en callbacks
- **FIX**: GeneratorExit warnings
- Shutdown limpio de tareas async

---

## Roadmap

### 🛣️ ITERACIÓN 3/3 - En Desarrollo

**Optimizaciones Planeadas:**
- [ ] Tests unitarios para componentes críticos
- [ ] Mejoras en manejo de excepciones
- [ ] Logging estructurado avanzado
- [ ] Documentación inline (docstrings) completa
- [ ] Rate limiting más inteligente
- [ ] Persistencia de deals en BD
- [ ] Webhooks para notificaciones externas
- [ ] API REST opcional
- [ ] Dashboard web (opcional)
- [ ] Optimización de memoria y CPU

**Features Opcionales:**
- [ ] Soporte para vuelos multi-city
- [ ] Integración con más proveedores (Skyscanner, Kayak)
- [ ] Machine Learning real con sklearn
- [ ] Predicción de precios futuros
- [ ] Alertas por email/SMS
- [ ] Exportación de reportes PDF
- [ ] Integración con calendarios (Google Calendar)
- [ ] Soporte multi-idioma
- [ ] Sistema de recomendaciones personalizadas
- [ ] Alertas de cambios en vuelos guardados

---

## Leyenda

- ✨ Nuevas Funcionalidades
- 🔧 Fixes
- 📊 Mejoras de Rendimiento
- 📝 Documentación
- ⚠️ Breaking Changes
- 🗑️ Deprecado
