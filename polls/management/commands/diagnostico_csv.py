from django.core.management.base import BaseCommand
from polls.models import Clinica, Condutor, Enfermagem, Veiculo
import os
import csv


class Command(BaseCommand):
    help = "Diagnóstico dos arquivos CSV e dados de autocomplete."

    def handle(self, *args, **options):
        base_dir = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        )
        arquivos = [
            ("clinicas.csv", Clinica),
            ("condutores.csv", Condutor),
            ("enfermagem.csv", Enfermagem),
            ("viaturas.csv", Veiculo),
        ]
        for nome_arquivo, modelo in arquivos:
            caminho = os.path.join(base_dir, nome_arquivo)
            self.stdout.write(f"\nArquivo: {nome_arquivo}")
            if os.path.exists(caminho):
                self.stdout.write(self.style.SUCCESS("  [OK] Arquivo encontrado."))
                try:
                    with open(caminho, encoding="utf-8") as f:
                        reader = csv.reader(f)
                        linhas = list(reader)
                        self.stdout.write(
                            f"  Cabeçalho: {linhas[0] if linhas else '(vazio)'}"
                        )
                        for i, linha in enumerate(linhas[1:4], 1):
                            self.stdout.write(f"  Linha {i}: {linha}")
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"  [ERRO] Falha ao ler CSV: {e}")
                    )
            else:
                self.stdout.write(
                    self.style.WARNING("  [FALTA] Arquivo não encontrado.")
                )
            total = modelo.objects.count()
            self.stdout.write(f"  Registros no banco: {total}")
        self.stdout.write(self.style.SUCCESS("\nDiagnóstico concluído."))
