import os
import pandas as pd
from django.core.management.base import BaseCommand
from polls.models import Paciente

class Command(BaseCommand):
    help = 'Importa pacientes de um arquivo CSV ou Excel para o banco de dados.'

    def add_arguments(self, parser):
        parser.add_argument('arquivo', type=str, help='Caminho do arquivo CSV ou Excel com os pacientes')

    def handle(self, *args, **options):
        arquivo = options['arquivo']
        if not os.path.exists(arquivo):
            self.stderr.write(self.style.ERROR(f"Arquivo não encontrado: {arquivo}"))
            return
        try:
            if arquivo.lower().endswith('.csv'):
                df = pd.read_csv(arquivo)
            elif arquivo.lower().endswith(('.xls', '.xlsx')):
                df = pd.read_excel(arquivo)
            else:
                self.stderr.write(self.style.ERROR('Formato de arquivo não suportado. Use CSV ou Excel.'))
                return
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Erro ao ler arquivo: {e}"))
            return
        campos_modelo = [f.name for f in Paciente._meta.fields]
        criados = 0
        for _, row in df.iterrows():
            dados = {campo: row[campo] for campo in campos_modelo if campo in row and pd.notnull(row[campo])}
            if 'id' in dados:
                dados.pop('id')  # Nunca importar o id
            try:
                Paciente.objects.create(**dados)
                criados += 1
            except Exception as e:
                self.stderr.write(self.style.WARNING(f"Erro ao importar linha: {row.to_dict()} | Erro: {e}"))
        self.stdout.write(self.style.SUCCESS(f"Importação concluída. {criados} pacientes importados."))
