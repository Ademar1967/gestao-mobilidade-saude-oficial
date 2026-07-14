import csv
from polls.models import Veiculo

with open("veiculos_export.csv", newline="", encoding="utf-8") as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        tipo_veiculo = row["tipo_veiculo"]
        placa = row["placa"] or None
        patrimonio = row["patrimonio"] or None
        # Checa duplicidade por placa (para vans) e por patrimônio (para ambulâncias)
        existe = False
        if tipo_veiculo == "van" and placa:
            existe = Veiculo.objects.filter(placa=placa, tipo_veiculo="van").exists()
        elif tipo_veiculo == "ambulancia" and patrimonio:
            existe = Veiculo.objects.filter(
                patrimonio=patrimonio, tipo_veiculo="ambulancia"
            ).exists()
        if not existe:
            v = Veiculo.objects.create(
                tipo_veiculo=tipo_veiculo,
                placa=placa or "",
                patrimonio=patrimonio or "",
            )
            print(
                f"Criado: {tipo_veiculo} | placa={placa} | patrimonio={patrimonio} | id={v.id}"
            )
        else:
            print(
                f"Já existe: {tipo_veiculo} | placa={placa} | patrimonio={patrimonio}"
            )
