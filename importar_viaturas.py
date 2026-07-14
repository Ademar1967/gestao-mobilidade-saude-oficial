import csv
from polls.models import Veiculo

CSV_PATH = "viaturas.csv"

with open(CSV_PATH, encoding="utf-8") as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        Veiculo.objects.get_or_create(
            patrimonio=row["patrimonio"],
            placa="",  # Adapte se houver coluna de placa
            tipo_veiculo="ambulancia",  # ou 'van' se necessário
        )
print("Importação de viaturas concluída.")
