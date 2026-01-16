# Instrucciones de Actualización v13.2.1

## ¿Qué necesita actualizarse?

El archivo `cazador_supremo_enterprise.py` necesita los siguientes cambios:

### 1. Actualizar VERSION (línea 82)

**Antes:**
```python
VERSION = "13.2.0 Enterprise"
```

**Después:**
```python
VERSION = "13.2.1 Enterprise"
```

### 2. Actualizar header docstring (líneas 1-15)

Añadir después de la línea de v13.2.0:
```python
✅ Onboarding Interactivo Fix 🔥 v13.2.1  ✅ TTFV <90s Achievement 🔥
```

### 3. Actualizar clase CazadorSupremoBot

#### 3.1 Reemplazar método `start_command()`

Buscar el método existente y reemplazarlo con el código de `onboarding_patch_v13.2.1.py` (MÉTODO 1)

#### 3.2 Añadir método `handle_callback()`

Si no existe, añadir después de `_register_handlers()` el código de `onboarding_patch_v13.2.1.py` (MÉTODO 2)

#### 3.3 Añadir método `_handle_onboarding_callback()`

Añadir como nuevo método después de `handle_callback()` el código de `onboarding_patch_v13.2.1.py` (MÉTODO 3)

### 4. Verificar imports

Asegurarse que en la sección de imports existan:

```python
from onboarding_flow import OnboardingManager, TravelRegion, BudgetRange, OnboardingMessages
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
```

✅ Ya están presentes en el archivo actual

### 5. Verificar inicialización en __init__()

Asegurarse que OnboardingManager esté inicializado:

```python
if RETENTION_ENABLED:
    self.retention_mgr = RetentionManager()
    self.retention_cmds = RetentionCommands(self.retention_mgr, self.scanner)
    self.smart_notifier = SmartNotifier(self.retention_mgr)
    self.onboarding_mgr = OnboardingManager()  # ✅ Esta línea debe existir
    self.quick_actions = QuickActionsManager(self.retention_mgr)
```

### 6. Verificar registro de callback handler

Asegurarse que en `_register_handlers()` exista:

```python
# Callback handler
self.app.add_handler(CallbackQueryHandler(self.handle_callback))
```

## Archivos de referencia

- `onboarding_patch_v13.2.1.py` - Contiene los 3 métodos completos
- `README.md` - Documentación actualizada con el flujo
- `CHANGELOG.md` - Historial de cambios

## Testing

Después de aplicar los cambios:

1. Ejecutar el bot: `python cazador_supremo_enterprise.py`
2. Crear nuevo usuario de prueba en Telegram
3. Enviar `/start`
4. Verificar que aparece:
   - Mensaje de bienvenida
   - Botón "🚀 ¡Empezar!"
   - Flujo de 3 pasos funcional
   - 200 FlightCoins al completar
   - Auto-watchlist con 3 rutas

## Resultado esperado

TTFV (Time To First Value) < 90 segundos ✅

---

**Autor**: @Juanka_Spain  
**Fecha**: 2026-01-16 02:09 CET  
**Versión**: v13.2.1 Enterprise
