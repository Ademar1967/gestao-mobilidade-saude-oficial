
import django
import os
import sys

# Ajusta o caminho do projeto para rodar standalone
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'transporte_django.settings')
django.setup()

from polls.models import Paciente
from django.conf import settings

if not settings.DEBUG:
	print("ATENÇÃO: Este script não deve ser executado em produção!")
	sys.exit(1)

total = Paciente.objects.count()
if total == 0:
	print('Nenhum paciente encontrado.')
	sys.exit(0)

confirm = input(f'Tem certeza que deseja excluir TODOS os {total} pacientes? (s/N): ')
if confirm.lower() == 's':
	Paciente.objects.all().delete()
	print(f'Todos os {total} pacientes foram excluídos com sucesso!')
else:
	print('Operação cancelada.')
