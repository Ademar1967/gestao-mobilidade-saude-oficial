import csv
from pathlib import Path
from .models import Condutor

def importar_condutores_csv():
    base_dir = Path(__file__).resolve().parent.parent
    arquivos = [
        base_dir / 'alocacao_motoristas_ambulancias.csv',
        base_dir / 'alocacao_condutores_viaturas.csv',
    ]
    nomes = set()
    for arquivo in arquivos:
        with arquivo.open(encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if row and row[0].strip() and not row[0].strip().isdigit():
                    nomes.add(row[0].strip())
    for nome in nomes:
        Condutor.objects.get_or_create(nome=nome)
