# 🏆 Cazador Supremo v12.2 - Enterprise Edition

![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-production-success)
![Version](https://img.shields.io/badge/version-12.2.0_COMPLETE-brightgreen)

Sistema **profesional de nivel empresarial** para monitorizar precios de vuelos con arquitectura POO, integración SerpAPI Google Flights, Machine Learning avanzado, webhooks para producción, y alertas inteligentes en tiempo real vía Telegram.

---

## 🎉 ¡VERSIÓN v12.2.0 COMPLETA!

**✅ 3 ITERACIONES COMPLETADAS** - Todas las funcionalidades implementadas y funcionando:

### ✨ Nuevos Comandos Implementados:
1. **`/route`** - Búsqueda personalizada con fechas flexibles ±3 días
2. **`/deals`** - Detección automática de chollos vs histórico
3. **`/trends`** - Análisis completo de tendencias de precios

### 🚀 Sistemas Nuevos:
- ✅ **DealsManager** - Gestión inteligente de ofertas con cooldown
- ✅ **TrendsAnalyzer** - Análisis estadístico de precios históricos
- ✅ **Auto-Scan Scheduler** - Escaneos automáticos cada hora (configurable)
- ✅ **Sistema de Notificaciones** - Alertas automáticas de chollos
- ✅ **Búsqueda Flexible** - Encuentra mejores precios en ventana de ±3 días

---

## 📋 Release Notes

### ✨ v12.2.0 - Búsqueda Personalizada y Deals COMPLETO (2026-01-14)

**✅ ITERACIÓN 3/3 - FINALIZACIÓN COMPLETA**

Todas las funcionalidades implementadas, testeadas y listas para producción:

#### Comando `/route` - Búsqueda Personalizada
- Sintaxis: `/route MAD BCN 2026-02-15`
- Búsqueda automática en ±3 días de la fecha objetivo
- Muestra hasta 5 mejores opciones ordenadas por precio
- Info completa: precio, aerolínea, escalas, confianza
- Soporte para cualquier ruta IATA válida

#### Comando `/deals` - Sistema de Chollos
- Detección automática comparando con media de 30 días
- Umbral configurable (default 20% ahorro)
- Muestra hasta 3 mejores chollos ordenados por ahorro
- Cálculo de ahorro en % y valor absoluto
- Cooldown de 30 min entre notificaciones del mismo chollo

#### Comando `/trends` - Análisis de Tendencias
- Estadísticas completas: media, mínimo, máximo
- Identificación de tendencia (subiendo/bajando)
- Basado en datos de últimos 30 días
- Número de datos utilizados para el análisis

#### Auto-Scan Scheduler
- Escaneos automáticos cada 1 hora (configurable)
- Se activa con `"auto_scan": true` en config.json
- No interfiere con comandos manuales
- Envía notificaciones automáticas de chollos detectados

#### Sistema de Notificaciones
- Notificaciones instantáneas cuando detecta chollos
- Envío automático al chat_id configurado
- Formato Markdown profesional con toda la info
- Control de spam con cooldown configurable

#### Mejoras Técnicas
- Código optimizado de ~30KB (vs ~60KB versiones anteriores)
- Arquitectura limpia y modular
- Manejo robusto de errores
- Logging completo de operaciones
- Production-ready con async/await

---

### 🔧 v12.1.2 - SerpAPI Fix (2026-01-13)
- ✅ Fix error 400 Bad Request añadiendo `type=2` (one-way flights)
- ✅ SerpAPI funciona correctamente sin return_date

### 🔧 v12.1.1 - Testing Tools (2026-01-13)
- ✅ Comando /clearcache para limpiar caché sin reiniciar

### ✨ v12.1.0 - Real API Integration (2026-01-13)
- ✅ Integración real con SerpAPI Google Flights
- ✅ Extracción inteligente de precios desde JSON
- ✅ Métricas de rendimiento por fuente

---

## 💬 Todos los Comandos del Bot

| Comando | Descripción | Ejemplo |
|---------|-------------|----------|
| `/start` | Inicia el bot y muestra menú principal | `/start` |
| `/scan` | Escanea todas las rutas configuradas | `/scan` |
| **`/route`** 🆕 | **Búsqueda personalizada con fecha** | `/route MAD BCN 2026-02-15` |
| **`/deals`** 🆕 | **Detecta chollos automáticamente** | `/deals` |
| **`/trends`** 🆕 | **Análisis de tendencias históricas** | `/trends MAD-MIA` |
| `/clearcache` | Limpia caché y fuerza APIs reales | `/clearcache` |
| `/status` | Muestra estado del sistema | `/status` |
| `/help` | Ayuda detallada | `/help` |

---

## 📚 Ejemplos de Uso Reales

### 1. Búsqueda Personalizada con `/route`

**Comando:**
```
/route MAD BCN 2026-03-20
```

**Respuesta del Bot:**
```
🔍 Buscando vuelos MAD → BCN para 2026-03-20 (±3 días)...

✅ Encontrados 5 vuelos

1️⃣ €68 - 2026-03-17
   ✈️ Ryanair
   🎯 90% confianza

2️⃣ €78 - 2026-03-20
   ✈️ Vueling
   🎯 95% confianza

3️⃣ €85 - 2026-03-21
   ✈️ Iberia
   🎯 95% confianza

4️⃣ €88 - 2026-03-19
   ✈️ Vueling
   ✅ 93% confianza

5️⃣ €92 - 2026-03-23
   ✈️ Iberia
   ✅ 92% confianza
```

### 2. Detección de Chollos con `/deals`

**Comando:**
```
/deals
```

**Respuesta del Bot:**
```
🔍 Buscando chollos...

🔥 ¡CHOLLO DETECTADO! 🔥

✈️ Ruta: Madrid-Miami
💰 Precio: €420 (GoogleFlights 🔍)
📉 Ahorro: 28.5% vs histórico
📊 Media histórica: €587
📅 Salida: 2026-04-15
🛫 Aerolínea: Iberia
🔗 Escalas: 0
🎯 Confianza: 95%

🔥 ¡CHOLLO DETECTADO! 🔥

✈️ Ruta: Madrid-Bogotá
💰 Precio: €309 (GoogleFlights 🔍)
📉 Ahorro: 21.2% vs histórico
📊 Media histórica: €392
📅 Salida: 2026-03-28
🛫 Aerolínea: Avianca
🔗 Escalas: 1
✅ Confianza: 88%
```

### 3. Análisis de Tendencias con `/trends`

**Comando:**
```
/trends MAD-MIA
```

**Respuesta del Bot:**
```
📈 Tendencia: MAD-MIA

📊 Media: €587
💰 Mínimo: €420
💸 Máximo: €720
📊 Datos: 47 precios
📉 Tendencia: Bajando
```

### 4. Escaneo Estándar con `/scan`

**Comando:**
```
/scan
```

**Respuesta del Bot:**
```
🔍 Iniciando escaneo...

✅ Escaneo completado

🎯 Madrid-Ciudad de México: €379 (GoogleFlights 🔍)
✅ Madrid-Managua: €478 (GoogleFlights 🔍)
✅ Madrid-Bogotá: €309 (GoogleFlights 🔍)
🎯 Managua-Madrid: €610 (GoogleFlights 🔍)
✅ Madrid-Guatemala: €330 (GoogleFlights 🔍)

...y 5 resultados más
```

### 5. Estado del Sistema con `/status`

**Comando:**
```
/status
```

**Respuesta del Bot:**
```
📊 Estado del Sistema

🗃️ Caché: 12 items (75.3% hit rate)
⚡ Circuit: 🟢 Closed
```

---

## 🛠️ Instalación

### Requisitos

```bash
python >= 3.9
pip install python-telegram-bot pandas requests colorama
```

### Configuración

1. **Clonar repositorio:**
```bash
git clone https://github.com/juankaspain/vuelosrobot.git
cd vuelosrobot
```

2. **Crear `config.json`:**
```json
{
  "telegram": {
    "token": "TU_BOT_TOKEN",
    "chat_id": "TU_CHAT_ID",
    "webhook_url": null
  },
  "flights": [
    {"origin": "MAD", "dest": "BCN", "name": "Madrid-Barcelona"},
    {"origin": "MAD", "dest": "MIA", "name": "Madrid-Miami"},
    {"origin": "MAD", "dest": "BOG", "name": "Madrid-Bogotá"}
  ],
  "alert_min": 500,
  "deal_threshold_pct": 20,
  "auto_scan": true,
  "apis": {
    "serpapi_key": "TU_SERPAPI_KEY_OPCIONAL"
  }
}
```

3. **Ejecutar:**
```bash
python cazador_supremo_enterprise.py
```

**Salida esperada:**
```
================================================================================
                       Cazador Supremo v12.2.0 Enterprise                      
================================================================================

[01:23:45] INFO     | ✅ Config loaded: 3 flights
[01:23:45] INFO     | 🧠 ML Smart Predictor initialized with 30 routes
[01:23:45] INFO     | 🗃️ TTLCache initialized: ttl=300s
[01:23:45] INFO     | ⚔️ CircuitBreaker 'serpapi' initialized
✅ Bot iniciado correctamente
```

---

## ⚡ Auto-Scan Scheduler

Para activar los escaneos automáticos cada hora:

1. En `config.json` añade:
```json
{
  "auto_scan": true
}
```

2. El bot escaneará automáticamente cada hora
3. Te enviará notificaciones de chollos detectados
4. No interfiere con comandos manuales

**Logs esperados:**
```
[02:23:45] INFO     | 🔍 Auto-scan iniciado
[02:23:52] INFO     | ✅ 10 precios escaneados
[02:23:52] INFO     | 🔥 2 chollos detectados
[02:23:53] INFO     | 📧 Notificación enviada: MAD-MIA
```

---

## 🏛️ Arquitectura v12.2 COMPLETA

```
Cazador Supremo v12.2 Enterprise
│
├── 🤖 TelegramBotManager
│   ├── CommandHandlers
│   │   ├── /start, /help, /status
│   │   ├── /scan (escaneo estándar)
│   │   ├── /route (búsqueda personalizada) 🆕
│   │   ├── /deals (detección chollos) 🆕
│   │   ├── /trends (análisis histórico) 🆕
│   │   └── /clearcache
│   ├── CallbackQueryHandler (inline buttons)
│   └── auto_scan_loop() 🆕 (scheduler asyncio)
│
├── 🎯 FlightScanner
│   ├── scan_routes() - Escaneo paralelo
│   ├── scan_route_flexible() 🆕 - Búsqueda ±3d
│   ├── _fetch_serpapi() - API Real
│   └── ML Predictor (50+ rutas)
│
├── 💰 DealsManager 🆕
│   ├── find_deals() - Detección automática
│   ├── should_notify() - Control cooldown
│   └── notified_deals{} - Tracking
│
├── 📈 DataManager (con TrendsAnalyzer) 🆕
│   ├── save_prices() - Persistencia CSV
│   ├── get_historical_avg() - Media 30d
│   └── get_price_trend() 🆕 - Análisis completo
│
├── 🛡️ Resilience Layer
│   ├── CircuitBreaker (3-state)
│   ├── TTLCache (300s TTL)
│   └── Rate Limiter (100 calls/mes)
│
└── 🧠 ML Smart Predictor
    ├── 30+ rutas BASE_PRICES
    ├── Multiplicadores estacionales
    └── Confidence scoring
```

---

## 🐛 Troubleshooting

### Error: "No se encontraron vuelos" en `/route`

**Causa:** Fechas muy lejanas o rutas sin datos.

**Solución:**
```bash
# Probar con fecha más cercana
/route MAD BCN 2026-02-15

# Verificar códigos IATA correctos
/route MAD MIA 2026-03-20  # ✅ Correcto
/route Madrid Miami 2026-03-20  # ❌ Incorrecto
```

### Error: "No hay chollos disponibles"

**Causa:** No hay precios significativamente por debajo del histórico.

**Solución:**
```json
// Reducir umbral en config.json
{
  "deal_threshold_pct": 15  // Bajado de 20 a 15
}
```

### Error: "No hay datos históricos" en `/trends`

**Causa:** Ruta nueva sin escaneos previos.

**Solución:**
```bash
# Escanear primero para generar datos
/scan

# Esperar unos días con auto_scan activo
# Luego intentar de nuevo
/trends MAD-MIA
```

### Bot no responde a comandos

**Verificar:**
```bash
# 1. Bot corriendo
ps aux | grep cazador_supremo

# 2. Token válido
# Verificar en config.json

# 3. Chat ID correcto
# Enviar mensaje al bot y ver logs
```

---

## 📊 Comparativa de Versiones FINAL

| Característica | v11.1 | v12.1 | v12.2 COMPLETE | Mejora |
|----------------|-------|-------|----------------|--------|
| Comandos Básicos | 4 | 5 | **8** | +100% |
| Búsqueda Personalizada | ❌ | ❌ | **✅ /route** | ✅ Nuevo |
| Detección Chollos | Manual | Manual | **✅ Auto /deals** | ✅ Nuevo |
| Análisis Tendencias | ❌ | ❌ | **✅ /trends** | ✅ Nuevo |
| Auto-Scan Scheduler | ❌ | ❌ | **✅ Asyncio** | ✅ Nuevo |
| Notif. Automáticas | ❌ | ❌ | **✅ Con cooldown** | ✅ Nuevo |
| Búsqueda Flexible | ❌ | ❌ | **✅ ±3 días** | ✅ Nuevo |
| DealsManager | ❌ | ❌ | **✅ Completo** | ✅ Nuevo |
| TrendsAnalyzer | ❌ | ❌ | **✅ Completo** | ✅ Nuevo |
| Rutas ML | 12 | 12 | **30+** | +150% |
| SerpAPI | ❌ | ✅ | **✅ Optimizado** | ✅ |
| Código | ~45KB | ~60KB | **30KB** | -50% |
| Production Ready | ⚠️ | ✅ | **✅✅** | ✅ |

---

## 🚀 Quick Start

```bash
# 1. Clonar repo
git clone https://github.com/juankaspain/vuelosrobot.git
cd vuelosrobot

# 2. Instalar dependencias
pip install python-telegram-bot pandas requests colorama

# 3. Configurar (editar config.json con tu token)
vim config.json

# 4. Ejecutar
python cazador_supremo_enterprise.py

# 5. Probar comandos en Telegram
/start
/route MAD BCN 2026-02-15
/deals
/trends MAD-MIA
```

---

## 📦 Dependencias

```txt
python-telegram-bot>=20.0
pandas>=2.0.0
requests>=2.28.0
colorama>=0.4.6
```

---

## 📋 Licencia

MIT License - Ver `LICENSE` para detalles.

---

## 👨‍💻 Autor

**@Juanka_Spain**
- GitHub: [@juankaspain](https://github.com/juankaspain)
- Email: juanca755@hotmail.com

---

## 🔗 Links Útiles

- [SerpAPI Google Flights](https://serpapi.com/google-flights-api)
- [python-telegram-bot Docs](https://docs.python-telegram-bot.org/)
- [Telegram Bot API](https://core.telegram.org/bots/api)

---

## 🎉 Changelog Completo

- **v12.2.0** (2026-01-14) - ✅ 3 iteraciones completas, todos comandos nuevos
- **v12.1.2** (2026-01-13) - Fix SerpAPI error 400
- **v12.1.1** (2026-01-13) - Comando /clearcache
- **v12.1.0** (2026-01-13) - Integración SerpAPI real
- **v12.0.3** (2026-01-13) - Fix UI.section()
- **v12.0.2** (2026-01-13) - Fix callbacks
- **v11.1** (2026-01-12) - Versión estable anterior

---

🌟 **Hecho con ❤️ para la comunidad de viajeros inteligentes**

✅ **v12.2.0 COMPLETA - PRODUCTION READY**
