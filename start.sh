#!/bin/bash
# Script de inicialização para Render
# Aguarda 5 segundos para garantir que serviços externos estejam prontos (ajuste se necessário)
sleep 5
echo "Aplicando migrações..."
python manage.py migrate --noinput

echo "Garantindo usuário admin..."
python manage.py create_admin || true

if [ -f "viaturas.csv" ]; then
	echo "Importando viaturas de viaturas.csv..."
	python manage.py importar_viaturas || true
else
	echo "viaturas.csv não encontrado, pulando importação de viaturas."
fi

if [ -f "clinicas.csv" ]; then
	echo "Importando clínicas de clinicas.csv..."
	python manage.py importar_clinicas || true
else
	echo "clinicas.csv não encontrado, pulando importação de clínicas."
fi

# Coleta arquivos estáticos (caso precise)
echo "Coletando arquivos estáticos..."
python manage.py collectstatic --noinput
# Inicia o servidor Gunicorn
exec gunicorn transporte_django.wsgi
