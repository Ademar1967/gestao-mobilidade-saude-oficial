pip install --no-cache-dir -r requirements-prod.txt
python manage.py collectstatic --no-input
python manage.py migrate
