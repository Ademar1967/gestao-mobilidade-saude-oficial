import os
import json
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connection, transaction
from polls.models import Paciente, Clinica, Condutor, Enfermagem, Veiculo, Transporte, Viagem, Bloco, RotinaMapaViagem

class Command(BaseCommand):
    help = "Carrega dados_export_completo.json de forma segura, limpando dados defasados se necessario."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Força a limpeza das tabelas antes de carregar o dump completo.",
        )

    def handle(self, *args, **options):
        fixture_path = "dados_export_completo.json"
        if not os.path.exists(fixture_path):
            self.stdout.write(self.style.WARNING(f"Arquivo {fixture_path} nao encontrado."))
            return

        force = options.get("force", False)

        try:
            self.stdout.write("[SINCRONIZACAO] Iniciando carga de dados_export_completo.json...")
            
            # Se for force ou se houver registros antigos que possam causar colisao de ID
            if force:
                self.stdout.write("[SINCRONIZACAO] Limpando registros antigos para carga limpa...")
                with transaction.atomic():
                    Viagem.objects.all().delete()
                    Bloco.objects.all().delete()
                    Transporte.objects.all().delete()
                    RotinaMapaViagem.objects.all().delete()
                    Paciente.objects.all().delete()
                    Veiculo.objects.all().delete()
                    Condutor.objects.all().delete()
                    Enfermagem.objects.all().delete()
                    Clinica.objects.all().delete()

            call_command("loaddata", fixture_path)
            
            total_pacientes = Paciente.objects.count()
            self.stdout.write(self.style.SUCCESS(f"[SINCRONIZACAO] Sucesso! Total de pacientes no banco: {total_pacientes}"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"[SINCRONIZACAO] Erro ao carregar fixture: {e}"))
            # Tentativa de fallback com limpeza se falhou por integridade/PK
            if not force:
                self.stdout.write(self.style.WARNING("[SINCRONIZACAO] Tentando novamente com limpeza previa de dados..."))
                try:
                    with transaction.atomic():
                        Viagem.objects.all().delete()
                        Bloco.objects.all().delete()
                        Transporte.objects.all().delete()
                        RotinaMapaViagem.objects.all().delete()
                        Paciente.objects.all().delete()
                        Veiculo.objects.all().delete()
                        Condutor.objects.all().delete()
                        Enfermagem.objects.all().delete()
                        Clinica.objects.all().delete()
                    call_command("loaddata", fixture_path)
                    total_pacientes = Paciente.objects.count()
                    self.stdout.write(self.style.SUCCESS(f"[SINCRONIZACAO] Sucesso no fallback! Total de pacientes: {total_pacientes}"))
                except Exception as e2:
                    self.stderr.write(self.style.ERROR(f"[SINCRONIZACAO] Falha critica no fallback: {e2}"))
