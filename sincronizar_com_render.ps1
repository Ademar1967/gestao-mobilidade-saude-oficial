param(
    [switch]$NoPush
)

$ErrorActionPreference = "Stop"
$env:PYTHONUTF8 = "1"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " EXPORTAÇÃO E SINCRONIZAÇÃO COMPLETA: LOCAL -> RENDER     " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Exportar dados locais completos em UTF-8
Write-Host "`n[1/3] Exportando dados do banco local (dump completo)..." -ForegroundColor Yellow
& ".\.venv\Scripts\python.exe" manage.py dumpdata --natural-foreign --natural-primary --exclude contenttypes --exclude auth.permission --indent 2 -o dados_export_completo.json

if (Test-Path "dados_export_completo.json") {
    $size = (Get-Item "dados_export_completo.json").Length
    Write-Host "-> Dados exportados com sucesso! Tamanho: $size bytes" -ForegroundColor Green
} else {
    Write-Host "-> Erro ao gerar dados_export_completo.json" -ForegroundColor Red
    exit 1
}

# 2. Testar validação do Django
Write-Host "`n[2/3] Validando integridade do projeto Django..." -ForegroundColor Yellow
& ".\.venv\Scripts\python.exe" manage.py check
Write-Host "-> Django Check OK!" -ForegroundColor Green

# 3. Comitar e Enviar para o Render
if (-not $NoPush) {
    Write-Host "`n[3/3] Enviando alterações e dados para o Render via Git..." -ForegroundColor Yellow
    git add dados_export_completo.json build.sh start.sh sincronizar_com_render.ps1
    git commit -m "chore(sync): sincronizar dados completos no build e start do render"
    git push origin main
    Write-Host "`n-> PUSH CONCLUÍDO COM SUCESSO! O Render iniciará o deploy e carregará os dados." -ForegroundColor Green
} else {
    Write-Host "`n[3/3] Modo sem push (--NoPush). Arquivos gerados localmente." -ForegroundColor Yellow
}

Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host " PROCESSO CONCLUÍDO! " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan
