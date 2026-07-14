import csv
from django.core.management.base import BaseCommand
from polls.models import Veiculo


class Command(BaseCommand):
    help = (
        "Importa vans e ambulâncias do veiculos_export.csv, criando apenas os ausentes."
    )

    def handle(self, *args, **options):
        try:
            with open("veiculos_export.csv", newline="", encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    tipo_veiculo = row["tipo_veiculo"]
                    placa = row["placa"] or None
                    patrimonio = row["patrimonio"] or None
                    existe = False
                    if tipo_veiculo == "van" and placa:
                        existe = Veiculo.objects.filter(
                            placa=placa, tipo_veiculo="van"
                        ).exists()
                    elif tipo_veiculo == "ambulancia" and patrimonio:
                        existe = Veiculo.objects.filter(
                            patrimonio=patrimonio, tipo_veiculo="ambulancia"
                        ).exists()
                    if not existe:
                        v = Veiculo.objects.create(
                            tipo_veiculo=tipo_veiculo,
                            placa=placa or "",
                            patrimonio=patrimonio or "",
                        )
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"Criado: {tipo_veiculo} | placa={placa} | patrimonio={patrimonio} | id={v.id}"
                            )
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(
                                f"Já existe: {tipo_veiculo} | placa={placa} | patrimonio={patrimonio}"
                            )
                        )
            self.stdout.write(self.style.SUCCESS("Importação concluída."))
        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR(
                    "Arquivo veiculos_export.csv não encontrado. Faça upload para a raiz do projeto."
                )
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erro: {e}"))
