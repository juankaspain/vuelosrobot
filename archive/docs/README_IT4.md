# 🎮 ITERACIÓN 4/11 - RETENTION HOOKS

![Progress](https://img.shields.io/badge/progress-40%25-yellow)
![Status](https://img.shields.io/badge/status-in_development-orange)
![Day](https://img.shields.io/badge/day-2%2F5-blue)

## 🎯 Objetivo

Implementar **Hook Model** para aumentar retención de usuarios:
- **Day 7 Retention**: 35% → **60%** (+71%)
- **Day 30 Retention**: 7% → **25%** (+257%)
- **Daily Active Users**: **+200%**

---

## 📅 Progreso por Días

### ✅ DAY 1 - Sistema Base (COMPLETADO)

**Archivo**: `retention_system.py`

**Implementado**:
1. ✅ `UserProfile` class
2. ✅ `FlightCoins` economy
3. ✅ `Tier` system (Bronze/Silver/Gold/Diamond)
4. ✅ `Achievement` system (9 tipos)
5. ✅ `Watchlist` personal
6. ✅ `Daily Rewards` con streaks
7. ✅ `RetentionManager` class
8. ✅ Persistencia JSON

---

### ✅ DAY 2 - Comandos Integrados (COMPLETADO)

**Archivo**: `bot_commands_retention.py`

**Implementado**:
1. ✅ Comando `/daily`
2. ✅ Comando `/watchlist`
3. ✅ Comando `/profile`
4. ✅ Comando `/shop`
5. ✅ `RetentionCommands` class
6. ✅ Inline keyboards
7. ✅ Progress bars visuales

---

### ⏳ DAY 3 - Smart Notifications (PENDIENTE)

**Objetivos**:
- Sistema de notificaciones inteligente
- Cálculo de hora óptima por usuario
- Rate limiting (max 3/día)
- Notificaciones de watchlist
- Recordatorios de daily reward

---

### ⏳ DAY 4 - Onboarding Flow (PENDIENTE)

**Objetivos**:
- Flow inicial optimizado
- Quick setup 3 pasos
- TTFV <90 segundos
- Personalización inmediata

---

### ⏳ DAY 5 - Quick Actions + Testing (PENDIENTE)

**Objetivos**:
- Inline keyboard persistente
- Acceso rápido 1-tap
- Testing completo IT4
- Métricas de retención

---

## 📚 Documentación de Comandos

### `/daily` - Reward Diario

**Descripción**: Reclama tu reward diario y mantén tu racha.

**Uso**:
```
/daily
```

**Output Ejemplo**:
```
🎉 ¡REWARD RECLAMADO! 🎉

💰 Ganaste: 165 FlightCoins
🔥 Racha: 5 días consecutivos

🥉 Tier: BRONZE
💳 Balance: 825 coins

¡Sigue así! Mañana: +60 bonus 💪
```

**Features**:
- Reward aleatorio: 50-200 coins
- Streak bonus: +10 coins por día consecutivo
- Notifica achievements (Week Warrior, Month Master)
- Muestra tier actual
- Cooldown 24h

---

### `/watchlist` - Watchlist Personal

**Descripción**: Gestiona tus rutas monitorizadas con alertas automáticas.

**Subcomandos**:

#### Agregar Ruta
```
/watchlist add MAD-MIA 450
```

**Output**:
```
✅ Ruta añadida a tu watchlist

✈️ Ruta: MAD-MIA
💰 Threshold: €450

📍 Slots: 3/5

Te avisaremos cuando el precio baje de €450
```

#### Ver Watchlist
```
/watchlist view
```

**Output**:
```
📍 Tu Watchlist (3 rutas)

✈️ MAD-MIA
   💰 Threshold: €450
   🔔 Notificaciones: 2

✈️ MAD-BOG
   💰 Threshold: €580
   🔔 Notificaciones: 0

✈️ BCN-NYC
   💰 Threshold: €400
   🔔 Notificaciones: 1

Usa /watchlist remove RUTA para eliminar
```

#### Eliminar Ruta
```
/watchlist remove MAD-MIA
```

**Output**:
```
✅ Ruta MAD-MIA eliminada de tu watchlist
```

**Límites por Tier**:
- 🥉 Bronze: 5 slots
- 🥈 Silver: 15 slots
- 🥇 Gold: 30 slots
- 💎 Diamond: 50 slots

---

### `/profile` - Perfil Completo

**Descripción**: Visualiza tu perfil, stats y progreso.

**Uso**:
```
/profile
```

**Output Ejemplo**:
```
👤 PERFIL DE @juanka_spain
==============================

🥈 Tier: SILVER
💰 FlightCoins: 1,250

📈 Progreso a GOLD:
█████░░░░░ 50%
Faltan 750 coins para 🥇

📊 ESTADÍSTICAS
🔍 Búsquedas: 47
🔥 Deals encontrados: 12
💸 Ahorro total: €1,580
🌍 Rutas únicas: 23

🔥 RACHAS
Actual: 8 días
Récord: 15 días

🏆 ACHIEVEMENTS: 4
• Week Warrior
• Deal Hunter
• Globe Trotter
• Early Bird

[🔥 Daily Reward] [📍 Watchlist] [🛍️ Tienda]
```

**Features**:
- Balance de coins
- Tier actual con emoji
- Progress bar a siguiente tier
- Stats completas
- Rachas (actual y récord)
- Achievements desbloqueados
- Inline keyboard con acciones

---

### `/shop` - Tienda Virtual

**Descripción**: Canjea tus FlightCoins por features premium.

**Uso**:
```
/shop
```

**Output Ejemplo**:
```
🛍️ TIENDA DE FLIGHTCOINS
==============================

💰 Tu balance: 1,250 coins

¡Canjea tus coins!

✅ 🔥 24h Premium
   💰 100 coins

✅ ❄️ Price Freeze 1x
   💰 200 coins

✅ 📍 +5 Watchlist Slots
   💰 150 coins

🔒 💎 1 Mes Premium
   💰 500 coins

Usa /buy ITEM para comprar
Gana más coins con /daily y encontrando deals
```

**Items Disponibles**:
1. **24h Premium**: 100 coins
   - Unlimited búsquedas por 24h
   - Priority queue
   
2. **Price Freeze**: 200 coins
   - Congela precio por 48h
   - Garantía de mejor precio

3. **+5 Watchlist Slots**: 150 coins
   - Expande tu watchlist
   - Permanente

4. **1 Mes Premium**: 500 coins
   - Tier Gold por 30 días
   - Todos los beneficios

---

## 🎮 Sistema de Gamificación

### FlightCoins Economy

**Gana Coins Por**:

| Acción | Coins | Frecuencia |
|--------|-------|------------|
| Daily login | 50-200 | Diario |
| Streak bonus | +10/día | Por racha |
| Primera búsqueda | 10 | Cada 10 búsquedas |
| Deal encontrado | 100 | Por deal |
| Deal aprovechado | 500 | Manual |
| Referir amigo | 500 | Por referido |
| Achievement | 1000 | Por logro |
| Compartir deal | 50 | Por share |
| Crear grupo | 100 | Por grupo |

### Tier System

#### 🥉 BRONZE (0-500 coins)
```
🔍 Búsquedas: 3/día
📍 Watchlist: 5 slots
🔔 Alertas custom: 2
```

#### 🥈 SILVER (500-2000 coins)
```
🔍 Búsquedas: 10/día
📍 Watchlist: 15 slots
🔔 Alertas custom: 5
```

#### 🥇 GOLD (2000-5000 coins)
```
🔍 Búsquedas: Unlimited
📍 Watchlist: 30 slots
🔔 Alertas custom: 15
```

#### 💎 DIAMOND (5000+ coins)
```
🔍 Búsquedas: Unlimited
📍 Watchlist: 50 slots
🔔 Alertas custom: Unlimited
👑 Priority support
```

### Achievement System

| Achievement | Requisito | Coins | Emoji |
|-------------|-----------|-------|-------|
| **Early Bird** | Búsqueda antes 7am | 1000 | 🌅 |
| **Deal Hunter** | 10 deals encontrados | 1000 | 🎯 |
| **Globe Trotter** | 20 rutas diferentes | 1000 | 🌍 |
| **Speed Demon** | 100 búsquedas en 1 mes | 1000 | ⚡ |
| **Money Saver** | Ahorraste €1000+ | 1000 | 💰 |
| **Week Warrior** | 7 días de streak | 1000 | 🔥 |
| **Month Master** | 30 días de streak | 1000 | 🏆 |
| **Referral King** | 10 referidos | 1000 | 👑 |
| **Power User** | 500 comandos totales | 1000 | ⚡ |

---

## 📊 KPIs Target IT4

| Métrica | Actual | Target | Mejora |
|---------|--------|--------|--------|
| **Day 7 Retention** | 35% | **60%** | +71% |
| **Day 30 Retention** | 7% | **25%** | +257% |
| **Daily Active Users** | Baseline | **+200%** | 3x |
| **Session Length** | 2 min | **5 min** | +150% |
| **Commands per User** | 3/semana | **10/semana** | +233% |

---

## 🔧 Integración en Bot Principal

### Setup

```python
from retention_system import RetentionManager
from bot_commands_retention import RetentionCommands

# En TelegramBotManager.__init__
self.retention_mgr = RetentionManager()
self.retention_cmds = RetentionCommands(self.retention_mgr)

# Añadir handlers
self.app.add_handler(CommandHandler('daily', self.retention_cmds.cmd_daily))
self.app.add_handler(CommandHandler('watchlist', self.retention_cmds.cmd_watchlist))
self.app.add_handler(CommandHandler('profile', self.retention_cmds.cmd_profile))
self.app.add_handler(CommandHandler('shop', self.retention_cmds.cmd_shop))
```

### Auto-tracking

```python
# En cmd_scan()
async def cmd_scan(self, update, context):
    user = update.effective_user
    # ... scan logic ...
    
    # Track automáticamente
    self.retention_mgr.track_search(
        user.id, 
        user.username, 
        route.route_code
    )

# En cmd_deals()
async def cmd_deals(self, update, context):
    # ... deals logic ...
    
    for deal in deals:
        # Track automáticamente
        self.retention_mgr.track_deal_found(
            user.id,
            user.username,
            deal.savings_pct
        )
```

---

## 💾 Persistencia

**Archivo**: `user_profiles.json`

**Estructura**:
```json
{
  "12345": {
    "user_id": 12345,
    "username": "juanka_spain",
    "coins": 1250,
    "tier": "silver",
    "current_streak": 8,
    "longest_streak": 15,
    "last_daily_claim": "2026-01-14T19:00:00",
    "total_searches": 47,
    "total_deals_found": 12,
    "total_savings": 1580.0,
    "routes_searched": ["MAD-MIA", "MAD-BCN", ...],
    "watchlist": [
      {
        "route": "MAD-MIA",
        "threshold": 450.0,
        "created_at": "2026-01-10T10:00:00",
        "last_price": 520.0,
        "notifications_sent": 2
      }
    ],
    "achievements": [
      {
        "type": "week_warrior",
        "unlocked_at": "2026-01-12T09:00:00",
        "coins_earned": 1000
      }
    ],
    "created_at": "2026-01-01T12:00:00",
    "last_active": "2026-01-14T19:00:00"
  }
}
```

---

## 🧪 Testing

### Test 1: Daily Reward
```bash
# Primera vez hoy
/daily
→ Debe dar 50-200 coins + streak=1

# Segunda vez hoy
/daily
→ Debe decir "ya reclamaste" + horas restantes
```

### Test 2: Watchlist
```bash
# Añadir
/watchlist add MAD-MIA 450
→ Debe confirmar y mostrar slots usados

# Ver
/watchlist view
→ Debe listar todas las rutas

# Eliminar
/watchlist remove MAD-MIA
→ Debe confirmar eliminación

# Exceder límite
/watchlist add (repetir 6 veces en Bronze)
→ Debe rechazar con mensaje de tier
```

### Test 3: Profile
```bash
/profile
→ Debe mostrar stats completas
→ Progress bar correcto
→ Inline keyboard funcional
```

### Test 4: Achievements
```bash
# Simular 7 días consecutivos
→ Debe desbloquear Week Warrior
→ Debe añadir 1000 coins
→ Debe aparecer en /profile
```

---

## 🔗 Links

- [retention_system.py](https://github.com/juankaspain/vuelosrobot/blob/main/retention_system.py)
- [bot_commands_retention.py](https://github.com/juankaspain/vuelosrobot/blob/main/bot_commands_retention.py)
- [Commit DAY1](https://github.com/juankaspain/vuelosrobot/commit/361330e67a82ed01f8f046e48b196d5560fe3f00)
- [Commit DAY2](https://github.com/juankaspain/vuelosrobot/commit/10da81e6c402ad6a8310f7c28fcf141cc18f1c32)

---

## 🚀 Próximos Pasos

**DAY 3** (Mañana):
- Smart Notifications Engine
- Watchlist monitoring
- Daily reminder scheduler
- Optimal send time calculator

**DAY 4**:
- Onboarding flow optimizado
- Quick setup wizard
- First-time user experience

**DAY 5**:
- Quick Actions inline keyboard
- Testing completo
- Métricas de retención
- Release IT4 🎉

---

🎉 **Hecho con ❤️ para maximizar retención de usuarios**
