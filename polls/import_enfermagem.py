import csv
from pathlib import Path
from .models import Enfermagem

def importar_enfermagem_csv():
    arquivo = Path(__file__).resolve().parent.parent / 'enfermagem.csv'
    with arquivo.open(encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader, None)  # Pular cabeçalho
        for row in reader:
            if row and row[0].strip():
                Enfermagem.objects.get_or_create(nome=row[0].strip())
