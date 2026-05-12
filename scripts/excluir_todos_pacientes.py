
import django
import os
import sys

# Ajusta o caminho do projeto para rodar standalone
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'transporte_django.settings')
django.setup()

from polls.models import Paciente

# Deleta todos os pacientes do banco de dados
Paciente.objects.all().delete()
print('Todos os pacientes foram excluídos com sucesso!')
