# 🚀 Cazador Supremo v13.0 Enterprise

![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)
![Version](https://img.shields.io/badge/version-13.0.0-green)
![Status](https://img.shields.io/badge/status-in_development-orange)
![License](https://img.shields.io/badge/license-MIT-blue)

**Sistema profesional de monitorización de vuelos con IA, gamificación y retención de usuarios**

---

## 🌟 Features Enterprise

### ✅ Core System (IT1-3)
- ✅ **Multi-source pricing** - SerpAPI + ML Smart Predictor
- ✅ **Deal detection** - Auto-detecta chollos vs histórico
- ✅ **Trend analysis** - Análisis de tendencias de precio
- ✅ **Auto-scan scheduler** - Monitoreo automático cada hora
- ✅ **Flexible search** - Búsqueda ±3 días
- ✅ **Multi-currency** - EUR/USD/GBP
- ✅ **Circuit breaker** - Protección API fallback
- ✅ **TTL Cache** - Cache inteligente con TTL
- ✅ **Rich CLI** - Terminal con colores
- ✅ **Inline keyboards** - Botones interactivos
- ✅ **i18n System** - ES/EN completo

### 🆕 Retention System (IT4) **✨ NEW**
- ✅ **Hook Model** - TRIGGER → ACTION → REWARD → INVESTMENT
- ✅ **FlightCoins Economy** - Moneda virtual gamificada
- ✅ **Tier System** - Bronze/Silver/Gold/Diamond
- ✅ **Achievement System** - 9 tipos de logros
- ✅ **Daily Rewards** - Login diario con streaks
- ✅ **Personal Watchlist** - Rutas monitorizadas
- ✅ **Smart Notifications** - IA aprende hora óptima
- ✅ **Background Tasks** - Automation completa
- ✅ **Interactive Onboarding** - TTFV <90s

---

## 💾 Instalación

### Requisitos
```bash
Python 3.9+
python-telegram-bot>=20.0
pandas
requests
colorama
```

### Setup
```bash
# Clonar repositorio
git clone https://github.com/juankaspain/vuelosrobot.git
cd vuelosrobot

# Instalar dependencias
pip install -r requirements.txt

# Configurar tokens
cp config.json.example config.json
# Editar config.json con tus tokens

# Ejecutar bot
python cazador_supremo_enterprise.py
```

---

## 🤖 Comandos Disponibles

### Core Commands
```
/start        - Iniciar bot
/scan         - Escanear todas las rutas
/route        - Búsqueda personalizada (MAD BCN 2026-02-15)
/deals        - Ver chollos disponibles
/trends       - Análisis de tendencias (MAD-MIA)
/clearcache   - Limpiar caché
/status       - Estado del sistema
/help         - Ayuda
```

### Retention Commands **🆕 NEW**
```
/daily        - Reclama reward diario (50-200 coins)
/watchlist    - Gestiona tu watchlist personal
  • add ROUTE PRICE  - Añadir ruta (ej: MAD-MIA 450)
  • view             - Ver tu lista
  • remove ROUTE     - Eliminar ruta
/profile      - Ver perfil completo y stats
/shop         - Tienda virtual de FlightCoins
```

---

## 🎮 Sistema de Gamificación

### FlightCoins Economy

**Gana Coins Por**:

| Acción | Coins | Frecuencia |
|--------|-------|------------|
| Daily login | 50-200 | Diario |
| Streak bonus | +10/día | Por racha |
| Primera búsqueda | 10 | Cada 10 |
| Deal encontrado | 100 | Por deal |
| Deal aprovechado | 500 | Manual |
| Referir amigo | 500 | Por referido |
| Achievement | 1000 | Por logro |
| Compartir deal | 50 | Por share |
| Onboarding | 200 | Una vez |

### Tier System

#### 🥉 BRONZE (0-500 coins)
- 🔍 Búsquedas: 3/día
- 📍 Watchlist: 5 slots
- 🔔 Alertas custom: 2

#### 🥈 SILVER (500-2000 coins)
- 🔍 Búsquedas: 10/día
- 📍 Watchlist: 15 slots
- 🔔 Alertas custom: 5

#### 🥇 GOLD (2000-5000 coins)
- 🔍 Búsquedas: Unlimited
- 📍 Watchlist: 30 slots
- 🔔 Alertas custom: 15

#### 💎 DIAMOND (5000+ coins)
- 🔍 Búsquedas: Unlimited
- 📍 Watchlist: 50 slots
- 🔔 Alertas custom: Unlimited
- 👑 Priority support

### Achievement System

| Achievement | Requisito | Coins |
|-------------|-----------|-------|
| 🌅 **Early Bird** | Búsqueda antes 7am | 1000 |
| 🎯 **Deal Hunter** | 10 deals encontrados | 1000 |
| 🌍 **Globe Trotter** | 20 rutas diferentes | 1000 |
| ⚡ **Speed Demon** | 100 búsquedas/mes | 1000 |
| 💰 **Money Saver** | Ahorraste €1000+ | 1000 |
| 🔥 **Week Warrior** | 7 días de streak | 1000 |
| 🏆 **Month Master** | 30 días de streak | 1000 |
| 👑 **Referral King** | 10 referidos | 1000 |
| ⚡ **Power User** | 500 comandos totales | 1000 |

---

## 🔔 Smart Notifications

### Tipos de Notificaciones

1. **🚨 CRITICAL - Price Drop**
   - Watchlist alert instantánea
   - <5 min latency
   - Bypass quiet hours (configurable)

2. **🔔 HIGH - Daily Reminder**
   - Recordatorio personalizado
   - Hora óptima aprendida
   - Solo si tiene streak

3. **📅 MEDIUM - Weekly Summary**
   - Resumen semanal (Lunes 20:00)
   - Stats personalizadas
   - Achievements recientes

4. **💡 LOW - Tips & Tricks**
   - Consejos de uso
   - Features nuevas
   - Fill notification slots

### Rate Limiting
```
FREE TIER: 3 notificaciones/día
PREMIUM: 10 notificaciones/día

Quiet Hours: 22:00-08:00 (configurable)
Priority Queue: CRITICAL > HIGH > MEDIUM > LOW
```

### Optimal Send Time
El sistema aprende la mejor hora para notificar a cada usuario:
- Analiza actividad histórica (30 días)
- Calcula peak hour de actividad
- Envía 5 min antes del peak
- Personalizado por usuario

---

## ⏰ Background Tasks

### Tareas Automatizadas

1. **Watchlist Monitor** (cada 30 min)
   - Escanea precios actuales
   - Compara con thresholds
   - Envía alertas de price drops
   - Update watchlist items

2. **Daily Reminder** (cada 1 hora)
   - Verifica usuarios sin claim
   - Solo si tienen streak activo
   - Envía a hora óptima
   - Rate limiting automático

3. **Midnight Reset** (00:00 diario)
   - Reset rate limits
   - Limpia cache expirado
   - Purge old notifications
   - Stats reset

4. **Weekly Summary** (Lunes 20:00)
   - Genera resumen personalizado
   - Stats de la semana
   - Achievements desbloqueados
   - Motivación customizada

---

## 🎉 Interactive Onboarding

### Flow de 3 Pasos (<90s)

**Step 1: ¿Dónde viajas?**
```
🇪🇺 Europa  🇺🇸 USA  🌏 Asia  🌎 Latam
```
→ Auto-configura rutas favoritas

**Step 2: ¿Tu presupuesto?**
```
🟢 Económico (<€300)  🟡 Moderado (€300-600)  🔵 Premium (>€600)
```
→ Ajusta watchlist thresholds

**Step 3: ¡Tus primeros deals!**
```
🔍 Buscando vuelos personalizados...
✅ 3 deals encontrados
📍 Añadidos a tu watchlist
```
→ First value inmediato

**Completado**:
```
✅ +200 FlightCoins de bienvenida
🏆 Badge "Early Adopter" desbloqueado
⏱️ Completado en 65 segundos
```

### Targets
- **TTFV**: <90 segundos
- **Completion Rate**: >75%
- **Drop-off**: <10% per step
- **Satisfaction**: >4.5/5

---

## 📊 KPIs y Métricas

### Objetivos IT4 - Retention

| Métrica | Actual | Target IT4 | Mejora |
|---------|--------|------------|--------|
| **Day 7 Retention** | 35% | **60%** | +71% ✨ |
| **Day 30 Retention** | 7% | **25%** | +257% 🚀 |
| **Daily Active Users** | Baseline | **+200%** | 3x 🔥 |
| **Session Length** | 2 min | **5 min** | +150% ⚡ |
| **Commands/User** | 3/week | **10/week** | +233% |
| **TTFV (Onboarding)** | N/A | **<90s** | ✅ |
| **Completion Rate** | N/A | **>75%** | ✅ |

### Notificaciones

| Métrica | Target | Status |
|---------|--------|--------|
| **Open Rate** | >40% | ✅ Hora óptima |
| **CTR** | >25% | ✅ Accionable |
| **Unsubscribe Rate** | <2% | ✅ Rate limiting |
| **Delivery Success** | >98% | ✅ Queue + retry |
| **Latency (Price Alerts)** | <5 min | ✅ 30min monitor |

---

## 📋 Release Notes

### v13.0.0 - IT4: RETENTION HOOKS (2026-01-14) **🆕 CURRENT**

#### 📅 DAY 1/5 - Sistema Base (2026-01-14)
**Archivos**:
- `retention_system.py` (21.3 KB)

**Features**:
- ✅ Hook Model implementation
- ✅ FlightCoins economy
- ✅ Tier system (4 niveles)
- ✅ Achievement system (9 tipos)
- ✅ Personal Watchlist
- ✅ Daily Rewards + Streaks
- ✅ UserProfile management
- ✅ Persistencia JSON

#### 📅 DAY 2/5 - Comandos Integrados (2026-01-14)
**Archivos**:
- `bot_commands_retention.py` (14.3 KB)
- `README_IT4.md` (10.7 KB)

**Features**:
- ✅ Comando `/daily`
- ✅ Comando `/watchlist` (add/view/remove)
- ✅ Comando `/profile` (stats + progress bar)
- ✅ Comando `/shop` (tienda virtual)
- ✅ RetentionCommands class
- ✅ Inline keyboards interactivos
- ✅ Documentación completa

#### 📅 DAY 3/5 - Smart Notifications (2026-01-14)
**Archivos**:
- `smart_notifications.py` (19.6 KB)
- `background_tasks.py` (18.3 KB)

**Features**:
- ✅ SmartNotifier class
- ✅ Optimal send time learning
- ✅ Priority queue (4 niveles)
- ✅ Rate limiting (3/day free, 10/day premium)
- ✅ Quiet hours (22:00-08:00)
- ✅ Activity analytics
- ✅ Cooldown system
- ✅ Message templates (5 tipos)
- ✅ Watchlist monitor (30 min)
- ✅ Daily reminder scheduler
- ✅ Midnight reset task
- ✅ Weekly summary generator
- ✅ BackgroundTaskManager

#### 📅 DAY 4/5 - Onboarding Flow (2026-01-14) **✨ NEW**
**Archivos**:
- `onboarding_flow.py` (18.0 KB)

**Features**:
- ✅ OnboardingManager class
- ✅ State machine (6 estados)
- ✅ 3-Step wizard interactivo
- ✅ Travel region selection
- ✅ Budget setup personalizado
- ✅ First value delivery <90s
- ✅ Completion tracking
- ✅ Analytics (completion rate, avg time)
- ✅ Skip option
- ✅ 200 coins bonus
- ✅ Persistencia de progreso

**Stats IT4**:
- 📁 **6 archivos nuevos** (120+ KB código)
- 💻 **9 comandos nuevos**
- 🎮 **Gamificación completa**
- 🔔 **Notificaciones inteligentes**
- ⏰ **5 background tasks**
- 🎉 **Onboarding interactivo**

**Progreso**: **80%** (4/5 días completados)

---

### v12.2.0 - IT3: DEALS & TRENDS (2026-01-13)
**Features**:
- ✅ DealsManager
- ✅ TrendsAnalyzer
- ✅ Auto-detection chollos
- ✅ Historical analysis
- ✅ Deal notifications

### v12.1.0 - IT2: PERSONALIZACION (2026-01-12)
**Features**:
- ✅ Comando `/route` personalizado
- ✅ Búsqueda flexible ±3 días
- ✅ Multi-currency EUR/USD/GBP
- ✅ Inline keyboards

### v12.0.0 - IT1: FOUNDATION (2026-01-11)
**Features**:
- ✅ SerpAPI integration
- ✅ ML Smart Predictor
- ✅ TTL Cache
- ✅ Circuit Breaker
- ✅ Auto-scan scheduler

---

## 💾 Arquitectura de Archivos

```
vuelosrobot/
├── cazador_supremo_enterprise.py     # Bot principal
├── retention_system.py              # Sistema de retención
├── bot_commands_retention.py        # Comandos retención
├── smart_notifications.py           # Notificaciones IA
├── background_tasks.py              # Tareas background
├── onboarding_flow.py               # Onboarding interactivo
├── config.json                      # Configuración
├── user_profiles.json               # Perfiles usuarios
├── user_activity.json               # Analytics actividad
├── notification_queue.json          # Cola notificaciones
├── onboarding_progress.json         # Progreso onboarding
├── deals_history.csv                # Histórico precios
├── README.md                        # Este archivo
├── README_IT4.md                    # Docs IT4 detalladas
└── requirements.txt                 # Dependencias
```

---

## 🔧 Configuración

### config.json
```json
{
  "telegram": {
    "token": "YOUR_BOT_TOKEN",
    "chat_id": "YOUR_CHAT_ID"
  },
  "apis": {
    "serpapi_key": "YOUR_SERPAPI_KEY"
  },
  "flights": [
    {"origin": "MAD", "dest": "BCN", "name": "Madrid-Barcelona"},
    {"origin": "MAD", "dest": "MIA", "name": "Madrid-Miami"}
  ],
  "alert_min": 500,
  "deal_threshold_pct": 20,
  "auto_scan": true
}
```

---

## 🚀 Roadmap

### ⏳ IT4/11 - DAY 5 - Quick Actions (Próximo)
**Objetivos**:
- Quick Actions Bar persistente
- 1-tap access funciones críticas
- Testing completo IT4
- Métricas de retención
- Release final IT4

### 🔮 IT5/11 - VIRAL GROWTH LOOPS
**Features planeadas**:
- Two-sided referral system
- Share deal button con links
- Group deal hunting
- Leaderboard con prizes
- Achievement sharing

### 🔮 IT6/11 - FREEMIUM CONVERSION
**Features planeadas**:
- Smart paywalls
- In-app premium trial
- Value metrics dashboard
- Smart upgrade prompts
- Flexible pricing

---

## 🤝 Contribuir

Este es un proyecto privado en desarrollo activo. Contactar a [@Juanka_Spain](https://github.com/juankaspain) para colaboraciones.

---

## 📝 Licencia

MIT License - Ver LICENSE file

---

## 📞 Contacto

- **Autor**: Juan Carlos García (@Juanka_Spain)
- **Email**: juanca755@hotmail.com
- **GitHub**: [juankaspain/vuelosrobot](https://github.com/juankaspain/vuelosrobot)

---

🎉 **Hecho con ❤️ para maximizar ahorro en vuelos y retención de usuarios**
