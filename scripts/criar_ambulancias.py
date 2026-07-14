from polls.models import Veiculo

patrimonios_ambulancias = ["AMB001", "AMB002", "AMB003"]
for patrimonio in patrimonios_ambulancias:
    if not Veiculo.objects.filter(
        patrimonio=patrimonio, tipo_veiculo="ambulancia"
    ).exists():
        v = Veiculo.objects.create(tipo_veiculo="ambulancia", patrimonio=patrimonio)
        print(f"Ambulância criada: patrimonio={v.patrimonio}, id={v.id}")
    else:
        print(f"Ambulância já existe: patrimonio={patrimonio}")
