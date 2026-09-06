import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'transporte_django.settings')
import django
django.setup()
from django.test import Client

c = Client(HTTP_HOST='127.0.0.1')
r = c.get('/pacientes/cadastrar-simples/')
html = r.content.decode('utf-8', 'ignore')
print('status', r.status_code)
print('box_present', 'box-busca-paciente' in html)
print('imprimir_button', 'Imprimir' in html)
print('title_present', 'F.A. Remocoes Eletivas' in html)
