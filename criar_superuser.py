# criar_superuser.py
import os
from django.contrib.auth import get_user_model

username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "AMBULANCIA192")
email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "seu@email.com")
password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "SENHA_FORTE_AQUI")

User = get_user_model()

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
    print(f"Superusuário '{username}' criado com sucesso!")
else:
    print(f"Superusuário '{username}' já existe.")
