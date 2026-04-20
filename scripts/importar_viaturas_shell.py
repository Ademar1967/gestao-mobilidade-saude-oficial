from polls.models import Veiculo
import csv

def run():
    with open('viaturas.csv', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        count = 0
        for row in reader:
            obj, created = Veiculo.objects.get_or_create(
                patrimonio=row['patrimonio'],
                placa='',
                tipo_veiculo='ambulancia',
            )
            if created:
                count += 1
        print(f'Importação de viaturas concluída. {count} novas viaturas importadas.')
