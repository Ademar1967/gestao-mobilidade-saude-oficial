# Script: deploy_render_automatizado.ps1
# Objetivo: Automatizar deploy, migrations e sincronização de pacientes entre localhost e Render
# Uso: Execute cada etapa conforme instruções nos comentários

# 1. Exportar pacientes do ambiente local
Write-Host "Exportando pacientes do banco local..."
python manage.py dumpdata polls.Paciente > pacientes.json
Write-Host "Arquivo pacientes.json gerado."

# 2. Fazer push do código para o Render (ajuste o remote se necessário)
Write-Host "Enviando código para o Render..."
git add .
git commit -m "deploy: atualizações e sincronização de pacientes"
git push
Write-Host "Código enviado. Aguarde o deploy automático do Render."

# 3. Rodar migrations e importar pacientes no Render
Write-Host "Acesse o shell do Render (pelo painel web ou SSH) e execute:"
Write-Host "python manage.py migrate"
Write-Host "python manage.py loaddata pacientes.json"
Write-Host "Pacientes importados e banco atualizado!"

# Observações:
# - O arquivo pacientes.json deve ser enviado para o Render (via git ou upload manual).
# - Se outros modelos precisarem ser sincronizados, adicione-os ao dumpdata/loaddata.
# - Sempre teste o sistema após o deploy para garantir que tudo está funcionando.
