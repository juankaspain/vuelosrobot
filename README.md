# 🏆 Cazador Supremo v12.0 - Enterprise Edition

![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-production-success)
![Version](https://img.shields.io/badge/version-12.0.1--patched-orange)

Sistema **profesional de nivel empresarial** para monitorizar precios de vuelos con arquitectura POO, integración SerpAPI Google Flights, Machine Learning avanzado, webhooks para producción, y alertas inteligentes en tiempo real vía Telegram.

## ✨ Novedades v12.0 Enterprise Edition

### 🚀 SerpAPI Google Flights Integration
- **Precios reales** de Google Flights con rate limiting (100 calls/día)
- **Fallback inteligente** de 3 niveles: SerpAPI → AviationStack → ML-Enhanced
- **Rate limiter** con cooldown automático para optimizar quotas
- **Métricas por fuente**: Success rate, avg time, call count
- **Circuit breaker** con half-open state para recuperación automática

### 🎯 ML Enhanced con Confidence Scores
- **DecisionTree patterns**: Detecta patrones de precios por anticipación, temporada, día
- **Confidence scoring**: Puntuación 0-100% de fiabilidad de cada estimación
- **Smart scaling**: Ajustes dinámicos (+35% directo, -18% doble escala, -30% triple)
- **Cabin multipliers**: Business x4.2, First x6.5 basados en datos reales
- **Proportional noise**: ±8% en lugar de ±250€ fijo para mayor realismo

### 🎨 Inline Keyboards & UX Mejorado
- **Botones interactivos** en mensajes para acciones rápidas
- **Typing indicators** mientras procesa ("Bot está escribiendo...")
- **Formatted messages** con emojis y Markdown profesional
- **Quick actions**: Refresh, View Details, More Info con callbacks
- **Colorized console**: Output coloreado con Colorama

### 🔔 Webhooks para Producción
- **Soporte webhooks** para despliegues en la nube (Heroku, Railway, etc.)
- **Heartbeat monitoring**: /health endpoint para contenedores
- **Health checks**: Monitorización por componente (APIs, Telegram, CSV)
- **Proactive degradation alerts**: Avisos cuando una API está caída
- **Ready for scale**: Preparado para entornos de producción

### 📊 Analytics & Monitoring
- **Dashboard /metrics**: Estadísticas completas por fuente de datos
- **Cache metrics**: Hit rate, miss rate, evictions
- **API metrics**: Éxito, fallo, tiempos de respuesta por fuente
- **Health status**: Verde/Amarillo/Rojo por componente
- **Structured logging**: Logs profesionales con rotación

### 🆕 Nuevo Comando: /breakdown
```
/breakdown MAD MGA

DESGLOSE DETALLADO MAD-MGA:

🎯 PRECIO BASE: €620
📊 CONFIANZA: 78% (Alta)

📈 FACTORES:
• Anticipación (45 días): -12%
• Temporada (verano): +25%
• Día semana (martes): -5%
• Escalas (1): -8%
• Distancia (8500km): Base

💡 FUENTE: ML-Enhanced
⏰ 13/01/2026 03:45
```

---

## 🚨 SOLUCIÓN RÁPIDA - Errores v12.0.1

Si experimentas estos errores:
- `Error tokenizing data. C error: Expected 5 fields in line 41, saw 7`
- `AttributeError: 'NoneType' object has no attribute 'reply_text'`

### Opción 1: Script Automático (Recomendado)

```bash
# Descargar parches
git pull origin main

# Aplicar automáticamente
python patch_v12_bugs.py

# Limpiar CSV corrupto
del deals_history.csv  # Windows
rm deals_history.csv   # Linux/Mac

# Ejecutar bot
python cazador_supremo_v12.0_enterprise.py
```

### Opción 2: Limpieza Manual

```bash
# Limpiar CSV
python fix_csv.py

# Ejecutar bot
python cazador_supremo_v12.0_enterprise.py
```

El bot recreará automáticamente el CSV con la estructura correcta.

---

## 📊 Comparativa v11.1 vs v12.0

| Característica | v11.1 | v12.0 | Mejora |
|----------------|-------|-------|--------|