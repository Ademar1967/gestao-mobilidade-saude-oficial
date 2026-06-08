param(
    [string]$EnvFile = ""
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
if (-not $EnvFile) {
    $EnvFile = Join-Path $projectRoot ".env.dev.local"
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

# Garante SQLite no modo dev local.
if (Test-Path Env:DATABASE_URL) {
    Remove-Item Env:DATABASE_URL
}

Set-Location $projectRoot

Write-Host "[MODO DEV LOCAL] Projeto: $projectRoot" -ForegroundColor Green
Write-Host "[MODO DEV LOCAL] DJANGO_DEBUG=$env:DJANGO_DEBUG" -ForegroundColor Green
Write-Host "[MODO DEV LOCAL] DATABASE_URL removido para usar SQLite." -ForegroundColor Green

python manage.py migrate
python manage.py runserver
