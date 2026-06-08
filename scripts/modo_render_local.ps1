param(
    [switch]$SkipCollectStatic,
    [string]$EnvFile = ""
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
if (-not $EnvFile) {
    $EnvFile = Join-Path $projectRoot ".env.render.local"
}

if (-not (Test-Path $EnvFile)) {
    Write-Error "Arquivo de ambiente nao encontrado: $EnvFile"
}

# Carrega variaveis KEY=VALUE no ambiente do processo atual.
Get-Content $EnvFile | ForEach-Object {
    $line = $_.Trim()
    if (-not $line -or $line.StartsWith("#")) {
        return
    }

    $parts = $line.Split("=", 2)
    if ($parts.Count -ne 2) {
        return
    }

    $key = $parts[0].Trim()
    $value = $parts[1].Trim()

    if ($key) {
        Set-Item -Path "Env:$key" -Value $value
    }
}

if (-not $env:DATABASE_URL -or $env:DATABASE_URL -match "usuario:senha@host") {
    Write-Error "Defina DATABASE_URL valido no arquivo $EnvFile antes de continuar."
}

Set-Location $projectRoot

Write-Host "[MODO RENDER LOCAL] Projeto: $projectRoot" -ForegroundColor Cyan
Write-Host "[MODO RENDER LOCAL] DJANGO_DEBUG=$env:DJANGO_DEBUG" -ForegroundColor Cyan
Write-Host "[MODO RENDER LOCAL] DATABASE_URL carregado." -ForegroundColor Cyan

python manage.py migrate

if (-not $SkipCollectStatic) {
    python manage.py collectstatic --no-input
}

python manage.py runserver
