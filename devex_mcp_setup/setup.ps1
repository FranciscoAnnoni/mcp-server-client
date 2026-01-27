# Configurar codificacion
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "Iniciando instalacion..."

# 1. Verificar uv
if (-not (Get-Command "uv" -ErrorAction SilentlyContinue)) {
    Write-Host "Instalando uv..."
    irm https://astral.sh/uv/install.ps1 | iex
    
    # Agregar al PATH temporalmente
    $rutas = @("$env:USERPROFILE\.cargo\bin", "$env:LOCALAPPDATA\bin")
    foreach ($r in $rutas) { 
        if (Test-Path $r) { 
            $env:PATH = "$r;$env:PATH"
            break 
        } 
    }
}

# 2. Configurar Repos
$Branch = "master"
$RepoBase = "git+ssh://git@github.com/rappi-inc/devex-mcp.git@$Branch"
$SetupUrl = "$RepoBase#subdirectory=devex_mcp_setup"
$ClientUrl = "$RepoBase#subdirectory=devex_mcp_client"

# Exportar variable de entorno necesaria
$env:DEVEX_CLIENT_REPO_URL = $ClientUrl

# 3. Ejecutar
Write-Host "Ejecutando instalador..."
uvx --from "$SetupUrl" devex-mcp-installer

# Verificar errores
if ($LASTEXITCODE -ne 0) {
    Write-Host "Hubo un error en la instalacion." -ForegroundColor Red
    Read-Host "Presiona Enter para salir"
    exit $LASTEXITCODE
}

Write-Host "Instalacion finalizada."
Read-Host "Presiona Enter para cerrar"