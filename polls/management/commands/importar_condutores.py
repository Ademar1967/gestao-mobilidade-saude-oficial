from django.core.management.base import BaseCommand
from polls.models import Condutor
import csv
import os

class Command(BaseCommand):
    help = 'Importa condutores do arquivo condutores.csv para o banco de dados.'

    def handle(self, *args, **options):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        csv_path = os.path.join(base_dir, 'condutores.csv')
        if not os.path.exists(csv_path):
            self.stdout.write(self.style.WARNING('condutores.csv não encontrado, pulando.'))
            return
        with open(csv_path, encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            count = 0
            for row in reader:
                nome = row.get('nome', '').strip()
                if nome:
                    _, created = Condutor.objects.get_or_create(nome=nome)
                    if created:
                        count += 1
                        self.stdout.write(self.style.SUCCESS(f'Condutor criado: {nome}'))
                    else:
                        self.stdout.write(f'Condutor já existe: {nome}')
        self.stdout.write(self.style.SUCCESS(f'Importação concluída. Total de novos condutores: {count}'))
