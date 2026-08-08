import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'transporte_django.settings')
import django
django.setup()
from django.test import Client
c = Client(HTTP_HOST='127.0.0.1')
r = c.get('/pacientes/cadastrar-simples/')
content = r.content.decode('utf-8', 'ignore')
print('status', r.status_code)
print('box' if 'box-busca-paciente' in content else 'NO_BOX')
print('title' if 'F.A. Remocoes Eletivas' in content else 'NO_TITLE')
