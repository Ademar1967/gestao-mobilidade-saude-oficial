pip install --no-cache-dir --prefer-binary -r requirements-prod.txt
python manage.py collectstatic --no-input
python manage.py migrate
