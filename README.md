# 🏆 Cazador Supremo v9.0 - Sistema de Monitorización de Vuelos

![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-active-success)

Sistema profesional automatizado para monitorizar precios de vuelos con alertas en tiempo real vía Telegram. Integra múltiples APIs, Machine Learning, RSS feeds y técnicas avanzadas de optimización.

## 🎯 Características Principales

### ✈️ Monitorización Avanzada
- **Multi-API**: Integración con AviationStack, SerpApi (Google Flights), FlightLabs
- **Escaneo paralelo**: Hasta 50 vuelos simultáneos con ThreadPoolExecutor
- **Fallback inteligente**: Si una API falla, utiliza otras automáticamente
- **Histórico CSV**: Almacena todos los escaneos para análisis de tendencias

### 🤖 Bot de Telegram
- **Alertas automáticas**: Notificaciones instantáneas cuando el precio baja del umbral
- **Comandos interactivos**: Control completo desde Telegram
- **Dashboard en tiempo real**: Estadísticas y mejores ofertas
- **Multi-usuario**: Configuración por Chat ID

### 📰 Ofertas Flash
- **RSS Feeds**: Integración con SecretFlying, Fly4Free
- **Error Fares**: Detección automática de tarifas erróneas
- **Flash Sales**: Alertas de ofertas limitadas

### 💡 Hacks Profesionales
- 14 técnicas avanzadas de ahorro (VPN arbitrage, skiplagging, mileage runs, etc.)
- Optimización de rutas con stopovers gratuitos
- Cashback stacking y points hacking

## 📦 Instalación

### Requisitos Previos
- Python 3.9 o superior
- Cuenta de Telegram
- Claves API (opcionales pero recomendadas)

### Paso 1: Clonar el Repositorio
```bash
git clone https://github.com/juankaspain/vuelosrobot.git
cd vuelosrobot
```

### Paso 2: Instalar Dependencias
```bash
pip install -r requirements.txt
```

### Paso 3: Configurar Telegram Bot

1. Abre Telegram y busca [@BotFather](https://t.me/BotFather)
2. Envía `/newbot` y sigue las instrucciones
3. Copia el **token** que te proporciona
4. Para obtener tu **Chat ID**:
   - Busca [@userinfobot](https://t.me/userinfobot)
   - Envía `/start`
   - Copia tu ID numérico

### Paso 4: Configurar APIs (Opcional pero Recomendado)

#### AviationStack (1000 llamadas/mes gratis)
1. Regístrate en [aviationstack.com](https://aviationstack.com)
2. Copia tu API key del dashboard

#### SerpApi (100 búsquedas/mes gratis)
1. Regístrate en [serpapi.com](https://serpapi.com)
2. Copia tu API key

### Paso 5: Editar config.json

```json
{
  "telegram": {
    "token": "TU_BOT_TOKEN_AQUI",
    "chat_id": "TU_CHAT_ID_AQUI"
  },
  "flights": [
    {
      "origin": "MAD",
      "dest": "MGA",
      "name": "Madrid-Managua"
    }
  ],
  "apis": {
    "aviationstack": "TU_CLAVE_AVIATIONSTACK",
    "serpapi": "TU_CLAVE_SERPAPI"
  },
  "alert_min": 500
}
```

**Campos obligatorios:**
- `telegram.token`: Token de tu bot
- `telegram.chat_id`: Tu ID de Telegram

**Campos opcionales:**
- `apis`: Si no proporcionas claves, usará precios simulados
- `alert_min`: Precio mínimo para alertas (default: 500€)
- `flights`: Lista de rutas a monitorizar

## 🚀 Uso

### Iniciar el Bot
```bash
python cazador_supremo_v9.py
```

Verás:
```
============================================================
🏆 CAZADOR SUPREMO v9.0 - Sistema de Monitorización de Vuelos
============================================================
✅ Bot Token: 1234567890:ABC...
✅ Chat ID: 123456789
✅ Vuelos configurados: 5
✅ Alerta mínima: €500
============================================================
🚀 Iniciando bot Telegram...

✅ Bot activo! Comandos disponibles:
   /start - Bienvenida
   /supremo - Scan completo
   /status - Dashboard
   /rss - Ofertas flash
   /chollos - Hacks
   /scan ORIGEN DESTINO - Ruta específica

⏰ Esperando comandos... (Ctrl+C para detener)
```

### Comandos del Bot

#### `/start`
Muestra la bienvenida y lista de comandos disponibles.

#### `/supremo`
Escanea todos los vuelos configurados y muestra:
- Número de vuelos escaneados
- Hot deals detectados (<€500)
- Mejor precio encontrado
- Top 5 mejores precios

**Ejemplo de respuesta:**
```
📊 SCAN SUPREMO COMPLETADO

✈️ Vuelos escaneados: 5
🔥 Hot deals (<€500): 2
💎 Mejor precio: €45 (MGA-MAD)

Top 5 mejores precios:
🔥 MGA-MAD: €45
🔥 BCN-MGA: €487
📊 MAD-BOG: €523
📊 MAD-MGA: €680
📊 MAD-MIA: €755

⏰ 2026-01-13 01:30:45
```

#### `/status`
Muestra dashboard completo con estadísticas históricas:
- Total de escaneos realizados
- Precio medio
- Precio mínimo histórico
- Número de chollos detectados

#### `/rss`
Busca ofertas flash actuales en SecretFlying y Fly4Free.

#### `/chollos`
Muestra 14 hacks profesionales para conseguir vuelos más baratos.

#### `/scan ORIGEN DESTINO`
Escanea una ruta específica en tiempo real.

**Ejemplo:**
```
/scan MAD MGA
```

**Respuesta:**
```
🛫 MAD-MGA

💰 Precio: €680
📊 Fuente: ML-Estimate
📊 Normal

🤖 Recomendación: Espera o monitoriza
⏰ 01:30:45
```

## ⚙️ Automatización con Task Scheduler (Windows)

### Crear archivo batch

Crea `run_cazador.bat`:
```batch
@echo off
cd /d "C:\ruta\a\vuelosrobot"
python cazador_supremo_v9.py
pause
```

### Configurar Task Scheduler

1. Presiona `Win + R`, escribe `taskschd.msc` y Enter
2. Clic derecho → **Crear Tarea Básica**
3. **Nombre**: "CazadorSupremo"
4. **Desencadenador**: Diario
5. **Repetir cada**: 3 horas (o el intervalo que prefieras)
6. **Acción**: Iniciar programa
7. **Programa**: Ruta a `run_cazador.bat`
8. Marca: **Ejecutar con privilegios más altos**
9. Marca: **Ejecutar independientemente de si el usuario inicia sesión**

## 🐧 Automatización con Cron (Linux/Mac)

```bash
# Editar crontab
crontab -e

# Ejecutar cada 3 horas
0 */3 * * * cd /ruta/a/vuelosrobot && /usr/bin/python3 cazador_supremo_v9.py >> cazador.log 2>&1
```

## 📊 Estructura de Archivos

```
vuelosrobot/
├── cazador_supremo_v9.py    # Script principal
├── config.json               # Configuración (Telegram, APIs, vuelos)
├── requirements.txt          # Dependencias Python
├── README.md                 # Este archivo
├── .gitignore               # Archivos a ignorar en git
├── deals_history.csv        # Histórico de escaneos (generado)
└── cazador_supremo.log      # Logs del sistema (generado)
```

## 🎨 Personalización

### Añadir Más Vuelos

Edita `config.json` en la sección `flights`:

```json
"flights": [
  {
    "origin": "MAD",
    "dest": "NYC",
    "name": "Madrid-Nueva York"
  },
  {
    "origin": "BCN",
    "dest": "LHR",
    "name": "Barcelona-Londres"
  }
]
```

### Cambiar Umbral de Alerta

```json
"alert_min": 400  // Alerta si precio < 400€
```

### Añadir Más RSS Feeds

```json
"rss_feeds": [
  "https://www.secretflying.com/feed/",
  "https://www.fly4free.com/feed/",
  "https://www.nuevofeed.com/rss"
]
```

## 🔧 Solución de Problemas

### El bot no responde
- Verifica que el token sea correcto
- Asegúrate de haber enviado `/start` al bot antes de usar otros comandos
- Comprueba que el script esté ejecutándose

### No recibo alertas
- Verifica tu `chat_id` en config.json
- Comprueba que el precio esté por debajo del umbral `alert_min`
- Revisa los logs en `cazador_supremo.log`

### Error "Module not found"
```bash
pip install -r requirements.txt
```

### Error de APIs
- Verifica que las claves sean correctas
- Comprueba que no hayas excedido el límite gratuito
- El sistema funcionará con precios estimados si las APIs fallan

## 💡 Consejos Profesionales

### Para Maximizar Ahorro
1. **Configura múltiples rutas**: Incluye rutas alternativas con escalas
2. **Monitoriza 24/7**: Usa Task Scheduler/Cron para escaneos continuos
3. **Umbral bajo**: Configura `alert_min` en 400-500€ para MAD-MGA
4. **Combina técnicas**: Usa /chollos para conocer hacks adicionales
5. **RSS feeds**: Activa alertas RSS para error fares

### Mejores Prácticas
- **Backup config.json**: Guarda copia de seguridad de tu configuración
- **Revisa logs**: Monitoriza `cazador_supremo.log` para errores
- **Actualiza APIs**: Renueva claves cuando expire el periodo gratuito
- **Histórico**: Analiza `deals_history.csv` para identificar patrones

## 🌐 APIs Soportadas

| API | Características | Límite Gratuito | Registro |
|-----|----------------|-----------------|----------|
| **AviationStack** | Precios reales, 700+ aerolíneas | 1000 calls/mes | [aviationstack.com](https://aviationstack.com) |
| **SerpApi** | Google Flights, ofertas | 100 búsquedas/mes | [serpapi.com](https://serpapi.com) |
| **FlightLabs** | Tracking, comparación | 20 calls demo | [goflightlabs.com](https://www.goflightlabs.com) |

## 📈 Roadmap

### v9.1 (Próximamente)
- [ ] Dashboard web con Streamlit
- [ ] Predicciones ML con LSTM
- [ ] Integración con más APIs
- [ ] Notificaciones Discord/Slack
- [ ] Docker deployment

### v10.0 (Futuro)
- [ ] Scraping avanzado con Playwright
- [ ] Optimización genética de rutas
- [ ] Base de datos PostgreSQL
- [ ] API REST propia
- [ ] App móvil

## 🤝 Contribuciones

Las contribuciones son bienvenidas! Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📝 Changelog

### v9.0 (2026-01-13)
- ✨ Versión inicial
- 🤖 Bot Telegram completo
- 🔗 Integración multi-API
- 📰 RSS feeds
- 💾 Histórico CSV
- 📊 Dashboard estadísticas
- 💡 14 hacks profesionales

## 📄 Licencia

MIT License - Consulta el archivo LICENSE para más detalles.

## 👤 Autor

**@Juanka_Spain**
- Telegram: [@Juanka_Spain](https://t.me/Juanka_Spain)
- GitHub: [@juankaspain](https://github.com/juankaspain)

## 🙏 Agradecimientos

- Comunidad de Perplexity AI por el soporte
- AviationStack, SerpApi por sus APIs
- SecretFlying y Fly4Free por los RSS feeds
- Comunidad de travel hacking

---

**⭐ Si este proyecto te ayuda a ahorrar en vuelos, considera darle una estrella en GitHub!**

**🚀 ¡Felices viajes y buenos chollos!** ✈️💰
