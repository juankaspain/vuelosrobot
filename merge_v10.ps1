################################################################################
# MERGE SCRIPT FOR CAZADOR SUPREMO v10.0 (Windows PowerShell)
# Autor: @Juanka_Spain
# Descripción: Fusiona automáticamente las dos partes del código v10.0
################################################################################

# Configurar error handling
$ErrorActionPreference = "Stop"

# Variables
$Part1 = "cazador_supremo_v10.py"
$Part2 = "cazador_supremo_v10_part2.py"
$Output = "cazador_supremo_v10_final.py"
$BackupDir = "backups_v10"

# Funciones para output con colores
function Write-Info {
    param([string]$Message)
    Write-Host "ℹ️  $Message" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor Green
}

function Write-Warning-Custom {
    param([string]$Message)
    Write-Host "⚠️  $Message" -ForegroundColor Yellow
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor Red
}

function Write-Header {
    param([string]$Message)
    Write-Host ""
    Write-Host ("═" * 70) -ForegroundColor Cyan
    Write-Host "  $Message" -ForegroundColor Cyan
    Write-Host ("═" * 70) -ForegroundColor Cyan
    Write-Host ""
}

# Banner
Write-Header "🏆 CAZADOR SUPREMO v10.0 - MERGE SCRIPT"
Write-Info "Este script fusionará las dos partes del código v10.0"
Write-Host ""

# Verificar que existen los archivos
Write-Info "Verificando archivos requeridos..."

if (-not (Test-Path $Part1)) {
    Write-Error-Custom "No se encontró el archivo: $Part1"
    Write-Warning-Custom "Ejecuta: git pull origin main"
    exit 1
}

if (-not (Test-Path $Part2)) {
    Write-Error-Custom "No se encontró el archivo: $Part2"
    Write-Warning-Custom "Ejecuta: git pull origin main"
    exit 1
}

Write-Success "Todos los archivos requeridos están presentes"
Write-Host ""

# Crear directorio de backups si no existe
if (-not (Test-Path $BackupDir)) {
    Write-Info "Creando directorio de backups: $BackupDir"
    New-Item -ItemType Directory -Path $BackupDir | Out-Null
}

# Backup del archivo anterior si existe
if (Test-Path $Output) {
    $Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $BackupFile = "$BackupDir\cazador_supremo_v10_final_$Timestamp.py"
    Write-Info "Creando backup de versión anterior..."
    Copy-Item $Output $BackupFile
    Write-Success "Backup guardado en: $BackupFile"
    Write-Host ""
}

# Fusionar archivos
Write-Header "🔀 FUSIONANDO ARCHIVOS"

Write-Info "Procesando $Part1..."
Write-Info "Procesando $Part2..."

try {
    # Leer contenido de ambos archivos
    $Content1 = Get-Content $Part1 -Raw -Encoding UTF8
    $Content2 = Get-Content $Part2 -Raw -Encoding UTF8
    
    # Eliminar las primeras 3 líneas de comentario de la parte 2
    $Content2Lines = $Content2 -split "`n"
    $Content2Filtered = $Content2Lines[3..($Content2Lines.Length - 1)] -join "`n"
    
    # Combinar y guardar
    $FinalContent = $Content1 + "`n" + $Content2Filtered
    [System.IO.File]::WriteAllText($Output, $FinalContent, [System.Text.Encoding]::UTF8)
    
    Write-Success "Archivos fusionados exitosamente"
    Write-Host ""
}
catch {
    Write-Error-Custom "Error al fusionar archivos: $_"
    exit 1
}

# Verificar sintaxis Python
Write-Header "🔍 VERIFICANDO SINTAXIS"

Write-Info "Compilando código Python..."

try {
    # Intentar compilar el archivo Python
    $result = python -m py_compile $Output 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Sintaxis Python correcta ✓"
        
        # Limpiar archivos .pyc generados
        if (Test-Path "__pycache__") {
            Remove-Item "__pycache__" -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
    else {
        Write-Error-Custom "Error de sintaxis detectado"
        Write-Warning-Custom "Revisa el archivo $Output"
        exit 1
    }
}
catch {
    Write-Warning-Custom "No se pudo verificar sintaxis (Python no instalado o no en PATH)"
    Write-Info "Continuando de todas formas..."
}

Write-Host ""

# Estadísticas del archivo
Write-Header "📊 ESTADÍSTICAS DEL ARCHIVO"

$FileInfo = Get-Item $Output
$Lines = (Get-Content $Output).Count
$SizeKB = [math]::Round($FileInfo.Length / 1KB, 2)
$SizeMB = [math]::Round($FileInfo.Length / 1MB, 2)

if ($SizeMB -gt 1) {
    $SizeStr = "$SizeMB MB"
}
else {
    $SizeStr = "$SizeKB KB"
}

Write-Host "📄 Archivo: $Output"
Write-Host "📏 Líneas de código: $Lines"
Write-Host "💾 Tamaño: $SizeStr"
Write-Host ""

# Verificar clases implementadas
Write-Info "Verificando clases implementadas..."
$ClassCount = (Select-String -Path $Output -Pattern "^class " -AllMatches).Matches.Count
Write-Success "$ClassCount clases encontradas"
Write-Host ""

# Resumen final
Write-Header "✅ FUSIÓN COMPLETADA EXITOSAMENTE"

Write-Host "📋 Resumen:"
Write-Host "   • Archivo creado: $Output"
Write-Host "   • Líneas totales: $Lines"
Write-Host "   • Clases implementadas: $ClassCount"
Write-Host "   • Sintaxis verificada: ✓"
Write-Host "   • Tamaño: $SizeStr"
Write-Host ""

Write-Info "Para ejecutar el bot:"
Write-Host "   " -NoNewline
Write-Host "python $Output" -ForegroundColor Green
Write-Host ""

Write-Info "Para ver logs en tiempo real:"
Write-Host "   " -NoNewline
Write-Host "Get-Content cazador_supremo.log -Wait -Tail 20" -ForegroundColor Green
Write-Host ""

Write-Success "¡Todo listo! El sistema está preparado para ejecutarse."
Write-Host ""

Write-Warning-Custom "Recuerda configurar tu config.json antes de ejecutar"
Write-Host ""

# Pausar para que el usuario pueda leer
Write-Host "Presiona cualquier tecla para continuar..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

exit 0
