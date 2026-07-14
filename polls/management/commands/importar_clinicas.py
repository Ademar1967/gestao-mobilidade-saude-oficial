from django.core.management.base import BaseCommand
from polls.models import Clinica
import csv
import os


class Command(BaseCommand):
    help = "Importa clínicas do arquivo clinicas.csv para o banco de dados."

    def handle(self, *args, **options):
        # Caminho correto para clinicas.csv na raiz do projeto
        base_dir = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        )
        csv_path = os.path.join(base_dir, "clinicas.csv")
        if not os.path.exists(csv_path):
            self.stdout.write(
                self.style.WARNING(
                    f"Arquivo não encontrado: {csv_path}. Nada para importar."
                )
            )
            return

        def get_value(row, *keys):
            for key in keys:
                if key in row and row.get(key):
                    return row.get(key, "").strip()
            return ""

        with open(csv_path, encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            created_count = 0
            updated_count = 0
            for row in reader:
                nome = get_value(row, "Nome", "nome")
                endereco = get_value(row, "Endereco", "endereco", "endereco_completo")
                bairro = get_value(row, "Bairro", "bairro")
                cidade = get_value(row, "Cidade", "cidade")
                telefone = get_value(row, "Telefone", "telefone")
                if nome:
                    clinica, created = Clinica.objects.update_or_create(
                        nome=nome,
                        defaults={
                            "endereco": endereco,
                            "bairro": bairro,
                            "cidade": cidade,
                            "telefone": telefone,
                        },
                    )
                    if created:
                        created_count += 1
                        self.stdout.write(self.style.SUCCESS(f"Clínica criada: {nome}"))
                    else:
                        updated_count += 1
                        self.stdout.write(f"Clínica atualizada: {nome}")
            self.stdout.write(
                self.style.SUCCESS(
                    f"Importação concluída. Novas: {created_count} | Atualizadas: {updated_count}"
                )
            )
