#!/bin/bash

################################################################################
# MERGE SCRIPT FOR CAZADOR SUPREMO v10.0
# Autor: @Juanka_Spain
# Descripción: Fusiona automáticamente las dos partes del código v10.0
################################################################################

set -e  # Salir si hay algún error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para imprimir mensajes coloreados
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_header() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
}

# Variables
PART1="cazador_supremo_v10.py"
PART2="cazador_supremo_v10_part2.py"
OUTPUT="cazador_supremo_v10_final.py"
BACKUP_DIR="backups_v10"

# Banner
print_header "🏆 CAZADOR SUPREMO v10.0 - MERGE SCRIPT"

print_info "Este script fusionará las dos partes del código v10.0"
echo ""

# Verificar que existen los archivos
print_info "Verificando archivos requeridos..."

if [ ! -f "$PART1" ]; then
    print_error "No se encontró el archivo: $PART1"
    print_warning "Ejecuta: git pull origin main"
    exit 1
fi

if [ ! -f "$PART2" ]; then
    print_error "No se encontró el archivo: $PART2"
    print_warning "Ejecuta: git pull origin main"
    exit 1
fi

print_success "Todos los archivos requeridos están presentes"
echo ""

# Crear directorio de backups si no existe
if [ ! -d "$BACKUP_DIR" ]; then
    print_info "Creando directorio de backups: $BACKUP_DIR"
    mkdir -p "$BACKUP_DIR"
fi

# Backup del archivo anterior si existe
if [ -f "$OUTPUT" ]; then
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    BACKUP_FILE="$BACKUP_DIR/${OUTPUT%.py}_${TIMESTAMP}.py"
    print_info "Creando backup de versión anterior..."
    cp "$OUTPUT" "$BACKUP_FILE"
    print_success "Backup guardado en: $BACKUP_FILE"
    echo ""
fi

# Fusionar archivos
print_header "🔀 FUSIONANDO ARCHIVOS"

print_info "Procesando $PART1..."
cat "$PART1" > "$OUTPUT"

print_info "Procesando $PART2..."
# Omitir las primeras líneas de comentario de la parte 2
tail -n +4 "$PART2" >> "$OUTPUT"

print_success "Archivos fusionados exitosamente"
echo ""

# Verificar sintaxis Python
print_header "🔍 VERIFICANDO SINTAXIS"

print_info "Compilando código Python..."
if python3 -m py_compile "$OUTPUT" 2>/dev/null; then
    print_success "Sintaxis Python correcta ✓"
    # Limpiar archivo .pyc generado
    rm -f "__pycache__/${OUTPUT%.py}.cpython-*.pyc"
    rmdir __pycache__ 2>/dev/null || true
else
    print_error "Error de sintaxis detectado"
    print_warning "Revisa el archivo $OUTPUT"
    exit 1
fi

echo ""

# Estadísticas del archivo
print_header "📊 ESTADÍSTICAS DEL ARCHIVO"

LINES=$(wc -l < "$OUTPUT")
SIZE=$(du -h "$OUTPUT" | cut -f1)

echo "📄 Archivo: $OUTPUT"
echo "📏 Líneas de código: $LINES"
echo "💾 Tamaño: $SIZE"
echo ""

# Verificar clases implementadas
print_info "Verificando clases implementadas..."
CLASSES=$(grep -c "^class " "$OUTPUT" || true)
print_success "$CLASSES clases encontradas"
echo ""

# Hacer el archivo ejecutable
print_info "Haciendo el archivo ejecutable..."
chmod +x "$OUTPUT"
print_success "Permisos de ejecución establecidos"
echo ""

# Resumen final
print_header "✅ FUSIÓN COMPLETADA EXITOSAMENTE"

echo "📋 Resumen:"
echo "   • Archivo creado: $OUTPUT"
echo "   • Líneas totales: $LINES"
echo "   • Clases implementadas: $CLASSES"
echo "   • Sintaxis verificada: ✓"
echo "   • Ejecutable: ✓"
echo ""

print_info "Para ejecutar el bot:"
echo -e "   ${GREEN}python3 $OUTPUT${NC}"
echo ""

print_info "Para ver logs en tiempo real:"
echo -e "   ${GREEN}tail -f cazador_supremo.log${NC}"
echo ""

print_success "¡Todo listo! El sistema está preparado para ejecutarse."
echo ""

print_warning "Recuerda configurar tu config.json antes de ejecutar"
echo ""

exit 0
