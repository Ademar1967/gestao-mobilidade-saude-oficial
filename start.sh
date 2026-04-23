#!/bin/bash
# Script de inicialização para Render
# Aguarda 5 segundos para garantir que serviços externos estejam prontos (ajuste se necessário)
sleep 5
# Coleta arquivos estáticos (caso precise)
echo "Coletando arquivos estáticos..."
python manage.py collectstatic --noinput
# Inicia o servidor Gunicorn
exec gunicorn transporte_django.wsgi
