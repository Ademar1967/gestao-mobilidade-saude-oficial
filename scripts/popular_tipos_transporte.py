# Script seguro para popular tipos de transporte ausentes
# Uso: python manage.py shell < scripts/popular_tipos_transporte.py

from polls.models import Transporte
from django.utils import timezone
from django.contrib.auth import get_user_model

# Ajuste conforme necessário para campos obrigatórios do seu modelo
CAMPOS_FIXOS = dict(
    paciente_id=1,  # ID de um paciente existente
    veiculo_id=1,  # ID de um veículo existente
    data=timezone.now().date(),
    hora_saida=timezone.now().time(),
    hora_chegada=timezone.now().time(),
    origem="Origem Exemplo",
    destino="Destino Exemplo",
    criado_por_id=1,  # ID de um usuário existente
)

TIPOS = [t[0] for t in Transporte.TIPO_CHOICES]

faltando = []
for tipo in TIPOS:
    if not Transporte.objects.filter(tipo=tipo).exists():
        faltando.append(tipo)
        try:
            Transporte.objects.create(tipo=tipo, **CAMPOS_FIXOS)
            print(f"Criado transporte de tipo: {tipo}")
        except Exception as e:
            print(f"Erro ao criar tipo {tipo}: {e}")

if not faltando:
    print("Todos os tipos já possuem pelo menos um transporte.")
else:
    print(f"Tipos criados: {faltando}")
