from django.test import TestCase
from django.urls import reverse

class CadastroPacienteAcessibilidadeTest(TestCase):
    def test_template_tem_contraste_e_tabindex(self):
        from django.contrib.auth.models import User
        # Cria e autentica usuário de teste
        user = User.objects.create_user(username='teste', password='123456')
        self.client.login(username='teste', password='123456')
        response = self.client.get(reverse('transporte_pacientes:cadastrar_paciente'))
        self.assertContains(response, 'tabindex')
        self.assertContains(response, 'outline')
        self.assertContains(response, 'background')
