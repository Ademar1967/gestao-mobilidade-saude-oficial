from django.core.management.base import BaseCommand
from polls.models import Veiculo
import csv
import os

class Command(BaseCommand):
    help = 'Importa viaturas do arquivo viaturas.csv para o banco de dados.'

    def handle(self, *args, **options):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        csv_path = os.path.join(base_dir, 'viaturas.csv')
        if not os.path.exists(csv_path):
            self.stderr.write(self.style.ERROR(f'Arquivo {csv_path} não encontrado.'))
            return
        criados = 0
        atualizados = 0
        with open(csv_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                patrimonio = (row.get('patrimonio') or row.get('Patrimônio') or '').strip()
                placa = (row.get('placa') or row.get('Placa') or '').strip()
                tipo_raw = (row.get('tipo_veiculo') or row.get('tipo') or row.get('Tipo') or '').strip().lower()
                lotacao_raw = (row.get('lotacao') or row.get('Lotação') or row.get('lotacao_maxima') or '').strip()

                if not patrimonio and not placa:
                    continue

                if 'van' in tipo_raw:
                    tipo_veiculo = 'van'
                else:
                    tipo_veiculo = 'ambulancia'

                try:
                    lotacao = int(lotacao_raw) if lotacao_raw else 1
                except ValueError:
                    lotacao = 1

                lookup = {'patrimonio': patrimonio} if patrimonio else {'placa': placa}
                veiculo, created = Veiculo.objects.get_or_create(
                    **lookup,
                    defaults={
                        'placa': placa,
                        'patrimonio': patrimonio,
                        'tipo_veiculo': tipo_veiculo,
                        'lotacao': lotacao,
                    }
                )
                if created:
                    criados += 1
                else:
                    mudou = False
                    if placa and veiculo.placa != placa:
                        veiculo.placa = placa
                        mudou = True
                    if patrimonio and veiculo.patrimonio != patrimonio:
                        veiculo.patrimonio = patrimonio
                        mudou = True
                    if veiculo.tipo_veiculo != tipo_veiculo:
                        veiculo.tipo_veiculo = tipo_veiculo
                        mudou = True
                    if veiculo.lotacao != lotacao:
                        veiculo.lotacao = lotacao
                        mudou = True
                    if mudou:
                        veiculo.save(update_fields=['placa', 'patrimonio', 'tipo_veiculo', 'lotacao'])
                        atualizados += 1
        self.stdout.write(self.style.SUCCESS(f'Importação concluída. Novas viaturas: {criados} | Atualizadas: {atualizados}'))
