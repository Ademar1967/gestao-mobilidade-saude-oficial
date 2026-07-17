#!/bin/bash
# Script de inicialização para Render
sleep 5

echo "Garantindo usuário admin..."
python manage.py create_admin || true

if [ -f "viaturas.csv" ]; then
    echo "Importando viaturas de viaturas.csv..."
    python manage.py importar_viaturas || true
else
    echo "viaturas.csv nao encontrado, pulando importacao."
fi

if [ -f "clinicas.csv" ]; then
    echo "Importando clinicas de clinicas.csv..."
    python manage.py importar_clinicas || true
else
    echo "clinicas.csv nao encontrado, pulando importacao."
fi

if [ -f "condutores.csv" ]; then
    echo "Importando condutores de condutores.csv..."
    python manage.py importar_condutores || true
else
    echo "condutores.csv nao encontrado, pulando importacao."
fi

if [ -f "enfermagem.csv" ]; then
    echo "Importando enfermagem de enfermagem.csv..."
    python manage.py importar_enfermagem || true
else
    echo "enfermagem.csv nao encontrado, pulando importacao."
fi

if [ -f "veiculos_export.csv" ]; then
    echo "Importando veiculos de veiculos_export.csv..."
    python manage.py importar_veiculos_csv || true
else
    echo "veiculos_export.csv nao encontrado, pulando importacao."
fi

echo "Iniciando Gunicorn na porta $PORT..."
exec gunicorn transporte_django.wsgi --bind 0.0.0.0:$PORT
