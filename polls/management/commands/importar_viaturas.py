from django.core.management.base import BaseCommand
from polls.models import Veiculo
import csv
import os

class Command(BaseCommand):
    help = 'Importa viaturas do arquivo viaturas.csv para o banco de dados.'

    def handle(self, *args, **options):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        csv_path = os.path.join(base_dir, 'viaturas.csv')
        if not os.path.exists(csv_path):
            self.stderr.write(self.style.ERROR(f'Arquivo {csv_path} não encontrado.'))
            return
        count = 0
        with open(csv_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                veiculo, created = Veiculo.objects.get_or_create(
                    placa=row.get('placa', ''),
                    defaults={
                        'modelo': row.get('modelo', ''),
                        'tipo': row.get('tipo', ''),
                        'cor': row.get('cor', ''),
                        'ano': row.get('ano', ''),
                    }
                )
                if created:
                    count += 1
        self.stdout.write(self.style.SUCCESS(f'Importação concluída. Total de novas viaturas: {count}'))
