# 🚀 Guía Rápida - Cazador Supremo v10.0

## ⌚ 5 Minutos para Empezar

### Paso 1: Clonar el Repositorio (30 segundos)

```bash
git clone https://github.com/juankaspain/vuelosrobot.git
cd vuelosrobot
```

### Paso 2: Instalar Dependencias (1 minuto)

```bash
# Crear entorno virtual (recomendado)
python3 -m venv venv

# Activar entorno virtual
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Instalar dependencias
pip install requests pandas feedparser python-telegram-bot
```

### Paso 3: Configurar tu Bot (2 minutos)

#### 3.1 Crear tu Bot de Telegram

1. Abre Telegram y busca **@BotFather**
2. Envía `/newbot`
3. Sigue las instrucciones y guarda el **token**
4. Busca **@userinfobot** y obtén tu **Chat ID**

#### 3.2 Crear config.json

```bash
# Copiar ejemplo
cp config.example.json config.json

# Editar con tu editor favorito
nano config.json  # o vim, code, notepad++, etc.
```

Edita estas líneas:
```json
{
  "telegram": {
    "token": "TU_TOKEN_AQUI",
    "chat_id": "TU_CHAT_ID_AQUI"
  },
  "alert_min": 500
}
```

### Paso 4: Fusionar Archivos v10 (30 segundos)

**Linux/Mac:**
```bash
chmod +x merge_v10.sh
./merge_v10.sh
```

**Windows PowerShell:**
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\merge_v10.ps1
```

**Manual (si los scripts no funcionan):**
```bash
# Linux/Mac
cat cazador_supremo_v10.py <(tail -n +4 cazador_supremo_v10_part2.py) > cazador_supremo_v10_final.py

# Windows PowerShell
Get-Content cazador_supremo_v10.py, cazador_supremo_v10_part2.py | Set-Content cazador_supremo_v10_final.py
```

### Paso 5: ¡Ejecutar! (10 segundos)

```bash
python3 cazador_supremo_v10_final.py
```

Deberías ver:
```
════════════════════════════════════════
  🏆  CAZADOR SUPREMO v10.0  🏆
════════════════════════════════════════

👂 Bot en modo escucha...
```

---

## 📱 Comandos del Bot

Abre tu bot en Telegram y prueba:

### Comandos Básicos

| Comando | Descripción | Tiempo |
|---------|--------------|--------|
| `/start` | Ver menú principal | Instantáneo |
| `/supremo` | Escanear TODOS los vuelos | ~30 segundos |
| `/status` | Ver estadísticas | Instantáneo |
| `/rss` | Buscar ofertas flash | ~10 segundos |
| `/chollos` | Ver 14 hacks profesionales | Instantáneo |
| `/scan MAD MGA` | Escanear ruta específica | ~5 segundos |

### Ejemplo de Uso

```
Tú: /start
Bot: 🏆 BIENVENIDO A CAZADOR SUPREMO v10.0...

Tú: /supremo
Bot: 🔄 INICIANDO ESCANEO SUPREMO...
     ... (30 segundos) ...
     ✅ ESCANEO COMPLETADO
     💎 Mejor: €450 (MAD-BOG)

Tú: /scan MAD MGA
Bot: 🔄 ESCANEANDO MAD-MGA...
     ✅ ANÁLISIS COMPLETADO
     💵 Precio: €680
```

---

## ⚙️ Configuración Avanzada

### Añadir Más Rutas

Edita `config.json`:

```json
{
  "flights": [
    {
      "origin": "MAD",
      "dest": "MGA",
      "name": "Madrid-Managua"
    },
    {
      "origin": "BCN",    // Tu nuevo origen
      "dest": "NYC",     // Tu nuevo destino
      "name": "Barcelona-Nueva York"  // Nombre descriptivo
    }
  ]
}
```

**Códigos IATA comunes:**
- MAD = Madrid
- BCN = Barcelona
- MGA = Managua
- BOG = Bogotá
- MIA = Miami
- NYC = Nueva York
- LIM = Lima
- MEX = Ciudad de México
- PTY = Panamá
- GUA = Guatemala

🔍 [Buscar más códigos IATA](https://www.iata.org/en/publications/directories/code-search/)

### Cambiar Umbral de Alerta

Edita `alert_min` en `config.json`:

```json
{
  "alert_min": 400  // Te alertará cuando precio < €400
}
```

### Obtener APIs Reales (Opcional)

El sistema funciona sin APIs, pero si quieres precios reales:

1. **AviationStack** (Free tier: 500 req/mes)
   - Registra en: https://aviationstack.com
   - Copia tu API key
   - Pégala en `config.json` → `apis.aviationstack`

2. **SerpAPI** (Free tier: 100 req/mes)
   - Registra en: https://serpapi.com
   - Copia tu API key
   - Pégala en `config.json` → `apis.serpapi`

---

## 📊 Verificar que Todo Funciona

### 1. Verificar Logs

```bash
tail -f cazador_supremo.log
```

Deberías ver:
```
2026-01-13 02:15:42 | INFO     | __init__       | Configuración cargada exitosamente
2026-01-13 02:15:42 | INFO     | __init__       | Cliente de APIs inicializado
2026-01-13 02:15:43 | INFO     | main           | Bot iniciado y en modo escucha
```

### 2. Ejecutar Primer Escaneo

En Telegram:
```
/supremo
```

Espera ~30 segundos. Deberías recibir:
- Mensaje de inicio
- Mensaje con resultados
- Si hay chollos: alertas individuales

### 3. Verificar Archivo de Datos

```bash
ls -lh deals_history.csv
head deals_history.csv
```

Debería existir y contener datos:
```
route,name,price,source,timestamp
MAD-MGA,Madrid-Managua,680.0,ML-Estimate,2026-01-13T02:15:45
```

---

## ❌ Solución de Problemas

### Error: "No se encontró config.json"

```bash
# Verifica que existe
ls config.json

# Si no existe, crea uno
cp config.example.json config.json
```

### Error: "Formato JSON inválido"

Verifica tu JSON en: https://jsonlint.com/

Problemas comunes:
- Falta coma al final de línea
- Comillas mal cerradas
- Coma extra al final del último elemento

### Error: "Token de Telegram inválido"

1. Verifica tu token con @BotFather
2. Formato correcto: `123456789:ABCdef...`
3. No incluyas espacios ni comillas extras

### Error: "ModuleNotFoundError: No module named 'telegram'"

```bash
pip install python-telegram-bot
```

### Bot no responde

1. Verifica que el script está corriendo
2. Revisa logs: `tail -f cazador_supremo.log`
3. Verifica tu Chat ID con @userinfobot
4. Asegúrate de usar el bot correcto

---

## 📚 Recursos Útiles

### Documentación
- **README completo**: [README_V10.md](README_V10.md)
- **Changelog**: [CHANGELOG_V10.md](CHANGELOG_V10.md)
- **Arquitectura**: Ver README_V10.md sección "Arquitectura"

### Ejemplos de Configuración
- **Mínima**: Solo Telegram + 2-3 rutas
- **Completa**: Telegram + APIs + RSS + 50+ rutas
- **Ejemplo**: [config.example.json](config.example.json)

### Scripts Útiles

```bash
# Ver logs en tiempo real
tail -f cazador_supremo.log

# Ver solo errores
grep ERROR cazador_supremo.log

# Contar escaneos realizados
wc -l deals_history.csv

# Ver mejores precios
cat deals_history.csv | sort -t, -k3 -n | head -10

# Backup de configuración
cp config.json config_backup_$(date +%Y%m%d).json
```

---

## 🛡️ Consejos de Seguridad

1. **Nunca compartas tu token de Telegram**
2. **No hagas commit de config.json con tokens reales**
3. **Usa .gitignore para proteger archivos sensibles**
4. **Rota tus tokens periódicamente**
5. **Revisa logs regularmente**

---

## 👍 Próximos Pasos

### Nivel Básico
✅ Configurar más rutas de vuelo  
✅ Ajustar umbral de alertas  
✅ Probar todos los comandos  
✅ Revisar logs para entender funcionamiento  

### Nivel Intermedio
✅ Configurar APIs reales (AviationStack, SerpAPI)  
✅ Añadir más feeds RSS  
✅ Programar ejecución automática con cron/Task Scheduler  
✅ Analizar datos históricos con pandas  

### Nivel Avanzado
✅ Personalizar código para tus necesidades  
✅ Crear nuevos comandos de Telegram  
✅ Integrar con otras APIs  
✅ Contribuir al proyecto en GitHub  

---

## 💬 Soporte

¿Problemas? ¿Preguntas?

- **Issues**: [GitHub Issues](https://github.com/juankaspain/vuelosrobot/issues)
- **Email**: juanca755@hotmail.com
- **Telegram**: @Juanka_Spain

---

## ⭐ ¿Te Gusta el Proyecto?

1. ⭐ Dale una estrella en GitHub
2. 👥 Comparte con amigos
3. 📝 Reporta bugs
4. 🚀 Sugiere mejoras
5. 👨‍💻 Contribuye código

---

© 2026 Cazador Supremo v10.0 - Sistema Profesional de Monitorización de Vuelos
