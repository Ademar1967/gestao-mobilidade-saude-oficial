
from django.core.management.base import BaseCommand
import os

class Command(BaseCommand):
    help = 'Cria um superusuário automaticamente se não existir (usando variáveis de ambiente)'

    def handle(self, *args, **options):
        from django.contrib.auth import get_user_model  # Import movido para dentro do handle()
        User = get_user_model()
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin123')

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f'Superusuário "{username}" já existe.'))
        else:
            User.objects.create_superuser(username=username, email=email, password=password)
            self.stdout.write(self.style.SUCCESS(f'Superusuário "{username}" criado com sucesso!'))
