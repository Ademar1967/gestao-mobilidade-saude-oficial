import django
import os
import sys

# Ajusta o caminho do projeto para rodar standalone
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "transporte_django.settings")
django.setup()

from polls.models import Paciente
from django.conf import settings

if not settings.DEBUG:
    print("ATENÇÃO: Este script não deve ser executado em produção!")
    sys.exit(1)


# Função para identificar se o campo tem só barras, espaços ou está vazio
def contem_so_barras_espacos(valor):
    if not valor:
        return False
    return all(c in {"/", " ", "|", "-"} for c in valor)


# Filtra pacientes cujo nome contenha 10 ou mais barras consecutivas
import re

suspeitos = []
for p in Paciente.objects.all():
    if re.search(r"/ {0,}/ {9,}", p.nome) or re.search(r"/ {10,}", p.nome):
        suspeitos.append(p)

if not suspeitos:
    print(
        "Nenhum paciente com nome contendo 10 ou mais barras consecutivas encontrado."
    )
    sys.exit(0)

print("Pacientes suspeitos encontrados:")
for p in suspeitos:
    print(f"ID: {p.id} | Nome: {p.nome}")

confirm = input(f"Deseja excluir esses {len(suspeitos)} pacientes? (s/N): ")
if confirm.lower() == "s":
    for p in suspeitos:
        p.delete()
    print(f"{len(suspeitos)} paciente(s) excluído(s) com sucesso!")
else:
    print("Operação cancelada.")
