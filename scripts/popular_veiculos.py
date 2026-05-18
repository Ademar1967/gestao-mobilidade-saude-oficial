from polls.models import Veiculo

# Automatiza criação de vans terceirizadas (apenas placa)
vans = [
    "VAN1234",
    "VAN5678",
    "VAN9012",
    # Adicione mais placas se desejar
]
for placa in vans:
    v = Veiculo.objects.create(tipo_veiculo="van", placa=placa)
    print(f"Van criada: placa={v.placa}, id={v.id}")

# Automatiza criação de ambulâncias da prefeitura (apenas patrimônio)
patrimonios = [
    "AMB001",
    "AMB002",
    "AMB003",
    # Adicione mais patrimônios se desejar
]
for patrimonio in patrimonios:
    v = Veiculo.objects.create(tipo_veiculo="ambulancia", patrimonio=patrimonio)
    print(f"Ambulância criada: patrimonio={v.patrimonio}, id={v.id}")
