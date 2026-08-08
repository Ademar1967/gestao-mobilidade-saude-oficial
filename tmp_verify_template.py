import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'transporte_django.settings')
import django
django.setup()
from django.template.loader import get_template
from django.test import Client

c = Client(HTTP_HOST='127.0.0.1')
r = c.get('/pacientes/cadastrar-simples/')
html = r.content.decode('utf-8', 'ignore')
print('status', r.status_code)
print('box_present', 'box-busca-paciente' in html)
print('template_origin', get_template('transporte_pacientes/cadastrar_paciente_simples.html').origin)
start = html.find('cabecalho-ficha-operacional')
print('snippet', html[start-200:start+800] if start != -1 else 'no header')
