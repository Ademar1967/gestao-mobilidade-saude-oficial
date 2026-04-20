import csv
from polls.models import Clinica

# Caminho do arquivo CSV
CSV_PATH = 'enderecos_sp_hospitais_adicionais.csv'

with open(CSV_PATH, encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        Clinica.objects.get_or_create(
            nome=row['nome'],
            endereco=row['logradouro'] + ', ' + row['numero'],
            bairro=row['bairro'],
            cidade=row['municipio'],
            telefone='',
        )
print('Importação de hospitais concluída.')
