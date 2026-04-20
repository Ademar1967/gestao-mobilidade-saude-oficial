from django.core.management.base import BaseCommand
from polls.models import Clinica
import csv
import os

class Command(BaseCommand):
    help = 'Importa clínicas do arquivo clinicas.csv para o banco de dados.'

    def handle(self, *args, **options):
        # Caminho correto para clinicas.csv na raiz do projeto
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        csv_path = os.path.join(base_dir, 'clinicas.csv')
        with open(csv_path, encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            count = 0
            for row in reader:
                nome = row.get('Nome', '').strip()
                endereco = row.get('Endereco', '').strip()
                bairro = row.get('Bairro', '').strip()
                cidade = row.get('Cidade', '').strip()
                telefone = row.get('Telefone', '').strip()
                if nome:
                    clinica, created = Clinica.objects.get_or_create(
                        nome=nome,
                        defaults={
                            'endereco': endereco,
                            'bairro': bairro,
                            'cidade': cidade,
                            'telefone': telefone
                        }
                    )
                    if created:
                        count += 1
                        self.stdout.write(self.style.SUCCESS(f'Clínica criada: {nome}'))
                    else:
                        self.stdout.write(f'Clínica já existe: {nome}')
            self.stdout.write(self.style.SUCCESS(f'Importação concluída. Total de novas clínicas: {count}'))
