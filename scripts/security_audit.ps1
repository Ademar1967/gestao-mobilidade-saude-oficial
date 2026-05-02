Param(
    [string]$RepoPath = "."
)

$ErrorActionPreference = "Stop"
Set-Location $RepoPath

Write-Host "[1/3] Verificando segredos no historico com gitleaks..." -ForegroundColor Cyan
if (Get-Command gitleaks -ErrorAction SilentlyContinue) {
    gitleaks git --verbose --redact
} else {
    Write-Warning "gitleaks nao encontrado. Instale em: https://github.com/gitleaks/gitleaks"
}

Write-Host "[2/3] Verificando segredos no estado atual com trufflehog..." -ForegroundColor Cyan
if (Get-Command trufflehog -ErrorAction SilentlyContinue) {
    trufflehog filesystem . --only-verified
} else {
    Write-Warning "trufflehog nao encontrado. Instale em: https://github.com/trufflesecurity/trufflehog"
}

Write-Host "[3/3] Verificando arquivos sensiveis rastreados no git..." -ForegroundColor Cyan
$tracked = git ls-files
$sensitivePatterns = @(".env", "db.sqlite3", "__pycache__", ".pem", ".key", "id_rsa")
$hits = @()
foreach ($item in $tracked) {
    foreach ($pattern in $sensitivePatterns) {
        if ($item -like "*$pattern*") {
            $hits += $item
            break
        }
    }
}

if ($hits.Count -gt 0) {
    Write-Warning "Arquivos potencialmente sensiveis ainda rastreados:"
    $hits | Sort-Object -Unique | ForEach-Object { Write-Host " - $_" -ForegroundColor Yellow }
    exit 1
}

Write-Host "Auditoria concluida sem itens rastreados sensiveis." -ForegroundColor Green
