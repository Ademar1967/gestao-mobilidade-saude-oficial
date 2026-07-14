from django.test import TestCase
from polls.models import Paciente


class PacienteModelTest(TestCase):
    def test_cadastro_paciente_sem_cadeira_dobravel(self):
        paciente = Paciente.objects.create(
            nome="Teste Paciente",
            idade=30,
            peso=70.5,
            rua="Rua Teste",
            numero="123",
            bairro="Centro",
            cidade="São Paulo",
            estado="SP",
            telefone="11999999999",
        )
        self.assertIsNotNone(paciente.id)
