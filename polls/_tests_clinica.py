from django.test import TestCase
from .models import Clinica
from .forms import ClinicaForm

class ClinicaTestCase(TestCase):
    def setUp(self):
        Clinica.objects.create(nome="Clínica Alpha", endereco="Rua A, 123", bairro="Centro", cidade="SP", telefone="1111-1111")

    def test_nao_permite_nome_duplicado(self):
        form = ClinicaForm(data={
            'nome': "Clínica Alpha",
            'endereco_completo': "Rua B, 456",
            'bairro': "Centro",
            'cidade': "SP",
            'telefone': "2222-2222"
        })
        self.assertFalse(form.is_valid())
        self.assertIn('nome', form.errors)

    def test_nao_permite_endereco_duplicado(self):
        form = ClinicaForm(data={
            'nome': "Clínica Beta",
            'endereco_completo': "Rua A, 123",
            'bairro': "Centro",
            'cidade': "SP",
            'telefone': "3333-3333"
        })
        self.assertFalse(form.is_valid())
        self.assertIn('endereco_completo', form.errors)

    def test_salva_clinica_valida(self):
        form = ClinicaForm(data={
            'nome': "Clínica Gamma",
            'endereco_completo': "Rua C, 789",
            'bairro': "Centro",
            'cidade': "SP",
            'telefone': "4444-4444"
        })
        self.assertTrue(form.is_valid())
        clinica = form.save()
        self.assertEqual(clinica.nome, "Clínica Gamma")
        self.assertEqual(clinica.endereco, "Rua C, 789")
