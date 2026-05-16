from django.test import TestCase
from django.urls import reverse

class CadastroPacienteAcessibilidadeTest(TestCase):
    def test_template_tem_contraste_e_tabindex(self):
        response = self.client.get(reverse('transporte_pacientes:cadastrar_paciente'))
        self.assertContains(response, 'tabindex')
        self.assertContains(response, 'outline')
        self.assertContains(response, 'background')
