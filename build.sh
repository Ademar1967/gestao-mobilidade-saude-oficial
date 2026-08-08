pip install --upgrade pip

echo ">>> GRUPO 1: Django core"
pip install --prefer-binary Django==6.0.2 gunicorn==25.3.0 whitenoise==6.12.0

echo ">>> GRUPO 2: Banco"
pip install --prefer-binary dj-database-url==3.1.2 psycopg2-binary==2.9.12

echo ">>> GRUPO 3: Forms"
pip install --prefer-binary django-crispy-forms==2.6 "crispy-bootstrap5==2026.3"

echo ">>> GRUPO 4: REST API"
pip install --prefer-binary djangorestframework==3.16.1 "djangorestframework_simplejwt==5.5.1" PyJWT==2.12.1

echo ">>> GRUPO 5: Excel"
pip install --prefer-binary pandas==3.0.2 openpyxl==3.1.5 xlsxwriter==3.2.9

echo ">>> GRUPO 6: Utilitarios"
pip install --prefer-binary requests==2.33.1 python-slugify==8.0.4 pytz==2026.2 tzdata==2026.1

echo ">>> TODOS OS PACOTES INSTALADOS"
python manage.py collectstatic --no-input
python manage.py migrate
