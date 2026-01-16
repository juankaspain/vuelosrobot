#!/bin/bash
# Script automático para aplicar el fix v13.2.1 al archivo principal
# Ejecutar con: bash APPLY_FIX_v13.2.1.sh

echo "═══════════════════════════════════════════════════════════════"
echo "   🔧 APLICANDO FIX v13.2.1 - ONBOARDING INTERACTIVO"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Verificar que existe el archivo principal
if [ ! -f "cazador_supremo_enterprise.py" ]; then
    echo "❌ ERROR: No se encuentra cazador_supremo_enterprise.py"
    exit 1
fi

echo "✅ Archivo encontrado"
echo ""

# Crear backup
echo "📦 Creando backup..."
cp cazador_supremo_enterprise.py cazador_supremo_enterprise.py.backup_v13.2.0
echo "✅ Backup creado: cazador_supremo_enterprise.py.backup_v13.2.0"
echo ""

# Aplicar cambios con sed (macOS/Linux compatible)
echo "🔨 Aplicando cambios..."

# 1. Actualizar VERSION
echo "   1/4 Actualizando VERSION..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    sed -i '' 's/VERSION = "13.2.0 Enterprise"/VERSION = "13.2.1 Enterprise"/g' cazador_supremo_enterprise.py
else
    sed -i 's/VERSION = "13.2.0 Enterprise"/VERSION = "13.2.1 Enterprise"/g' cazador_supremo_enterprise.py
fi
echo "   ✅ VERSION actualizada"

# 2. Actualizar docstring header
echo "   2/4 Actualizando header..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    sed -i '' 's/🏷️ v13.2.0 Enterprise/🏷️ v13.2.1 Enterprise/g' cazador_supremo_enterprise.py
else
    sed -i 's/🏷️ v13.2.0 Enterprise/🏷️ v13.2.1 Enterprise/g' cazador_supremo_enterprise.py
fi
echo "   ✅ Header actualizado"

echo "   3/4 Insertando métodos de onboarding..."
echo "   ⚠️  ACCIÓN MANUAL REQUERIDA"
echo ""
echo "   Por favor, abre cazador_supremo_enterprise.py y:"
echo ""
echo "   A) Busca la clase 'CazadorSupremoBot'"
echo "   B) Reemplaza el método 'start_command()' con el de onboarding_patch_v13.2.1.py (MÉTODO 1)"
echo "   C) Añade el método 'handle_callback()' de onboarding_patch_v13.2.1.py (MÉTODO 2)"
echo "   D) Añade el método '_handle_onboarding_callback()' de onboarding_patch_v13.2.1.py (MÉTODO 3)"
echo ""
echo "   📄 Referencia: onboarding_patch_v13.2.1.py contiene los 3 métodos completos"
echo "   📖 Guía: UPDATE_INSTRUCTIONS_v13.2.1.md tiene instrucciones detalladas"
echo ""

echo "   4/4 Verificando..."
if grep -q '13.2.1' cazador_supremo_enterprise.py; then
    echo "   ✅ Versión actualizada correctamente"
else
    echo "   ❌ Error al actualizar versión"
    exit 1
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "   ⚠️  SIGUIENTE PASO MANUAL"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "   Ahora debes integrar los 3 métodos manualmente:"
echo ""
echo "   1. Abre: cazador_supremo_enterprise.py"
echo "   2. Busca: class CazadorSupremoBot"
echo "   3. Copia los métodos de: onboarding_patch_v13.2.1.py"
echo "   4. Guarda el archivo"
echo "   5. Ejecuta: python cazador_supremo_enterprise.py"
echo "   6. Prueba: /start con un nuevo usuario"
echo ""
echo "   📚 Documentación completa en: UPDATE_INSTRUCTIONS_v13.2.1.md"
echo ""
echo "═══════════════════════════════════════════════════════════════"
