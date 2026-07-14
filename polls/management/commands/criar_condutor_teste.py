from django.core.management.base import BaseCommand
from polls.models import Condutor


class Command(BaseCommand):
    help = "Cria um condutor de teste para busca."

    def handle(self, *args, **options):
        obj, created = Condutor.objects.get_or_create(nome="Condutor Teste Busca")
        if created:
            self.stdout.write(
                self.style.SUCCESS("Condutor de teste criado com sucesso!")
            )
        else:
            self.stdout.write(self.style.WARNING("Condutor de teste já existia."))
