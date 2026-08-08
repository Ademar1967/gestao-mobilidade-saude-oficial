#!/usr/bin/env bash
set -o errexit

python -m pip install --upgrade pip

echo ">>> GRUPO 1: Django core"
python -m pip install --prefer-binary Django==6.0.2 gunicorn==25.3.0 whitenoise==6.12.0

echo ">>> GRUPO 2: Banco"
python -m pip install --prefer-binary dj-database-url==3.1.2 psycopg2-binary==2.9.12

echo ">>> GRUPO 3: Forms e UI"
python -m pip install --prefer-binary django-crispy-forms==2.6 "crispy-bootstrap5==2026.3" django-admin-interface==0.32.0 django-colorfield==0.14.0

echo ">>> GRUPO 4: REST API"
python -m pip install --prefer-binary djangorestframework==3.16.1 "djangorestframework_simplejwt==5.5.1" PyJWT==2.12.1

echo ">>> GRUPO 5: Excel"
python -m pip install --prefer-binary pandas==3.0.2 openpyxl==3.1.5 xlsxwriter==3.2.9

echo ">>> GRUPO 6: Utilitarios"
python -m pip install --prefer-binary requests==2.33.1 python-slugify==8.0.4 pytz==2026.2 tzdata==2026.1 cffi==1.17.1

echo ">>> TODOS OS PACOTES OK"
python manage.py collectstatic --no-input
python manage.py migrate
