# Script de checklist automatizado para deploy Django no Render
# Execute este script antes de fazer deploy!

Write-Host "--- CHECKLIST DEPLOY DJANGO ---" -ForegroundColor Cyan

# 1. Rodar testes automáticos
Write-Host "1. Rodando testes automáticos..." -ForegroundColor Yellow
python manage.py test
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERRO: Testes falharam. Corrija antes de prosseguir." -ForegroundColor Red
    exit 1
}

# 2. Verificar arquivo essencial
$arquivo = "polls/views_condutor_delete.py"
if (-Not (Test-Path $arquivo)) {
    Write-Host "ERRO: Arquivo $arquivo não encontrado!" -ForegroundColor Red
    exit 1
} else {
    Write-Host "Arquivo $arquivo OK." -ForegroundColor Green
}

# 3. Limpar arquivos .pyc
Write-Host "3. Limpando arquivos .pyc..." -ForegroundColor Yellow
Get-ChildItem -Recurse -Include *.pyc | Remove-Item -Force -ErrorAction SilentlyContinue

# 4. Checar status do git
Write-Host "4. Checando status do git..." -ForegroundColor Yellow
git status

# 5. Forçar push para o repositório remoto
Write-Host "5. Enviando commits pendentes (se houver)..." -ForegroundColor Yellow
git add .
git commit -m "deploy: checklist auto"
git push

Write-Host "\nChecklist finalizado! Agora faça o deploy/redeploy no Render." -ForegroundColor Cyan
Write-Host "Se aparecer algum erro acima, corrija antes de prosseguir." -ForegroundColor Red
