#!/bin/bash
# Startup script for Render
set -e

echo "[DEPLOY] Starting app bootstrap..."
echo "[DEPLOY] Commit: $(git rev-parse --short HEAD 2>/dev/null || echo 'undefined')"
echo "[DEPLOY] Branch: $(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'undefined')"
echo "[DEPLOY] Python: $(python --version 2>&1)"

echo "[DEPLOY] Running deploy diagnostics (to find culprit if template/output is wrong)..."
python manage.py diagnostico_deploy || true

echo "[DEPLOY] Running Django checks..."
python manage.py check || true
python manage.py check --deploy || true

echo "[DEPLOY] Ensuring admin user..."
python manage.py create_admin || true

echo "[DEPLOY] Applying migrations..."
python manage.py migrate --no-input || true

if [ -f "viaturas.csv" ]; then
    echo "[DEPLOY] Importing viaturas.csv..."
    python manage.py importar_viaturas || true
else
    echo "[DEPLOY] viaturas.csv not found. Skipping."
fi

if [ -f "clinicas.csv" ]; then
    echo "[DEPLOY] Importing clinicas.csv..."
    python manage.py importar_clinicas || true
else
    echo "[DEPLOY] clinicas.csv not found. Skipping."
fi

if [ -f "condutores.csv" ]; then
    echo "[DEPLOY] Importing condutores.csv..."
    python manage.py importar_condutores || true
else
    echo "[DEPLOY] condutores.csv not found. Skipping."
fi

if [ -f "enfermagem.csv" ]; then
    echo "[DEPLOY] Importing enfermagem.csv..."
    python manage.py importar_enfermagem || true
else
    echo "[DEPLOY] enfermagem.csv not found. Skipping."
fi

if [ -f "veiculos_export.csv" ]; then
    echo "[DEPLOY] Importing veiculos_export.csv..."
    python manage.py importar_veiculos_csv || true
else
    echo "[DEPLOY] veiculos_export.csv not found. Skipping."
fi

echo "[DEPLOY] Starting gunicorn on port ${PORT}..."
exec gunicorn transporte_django.wsgi --bind 0.0.0.0:${PORT}
