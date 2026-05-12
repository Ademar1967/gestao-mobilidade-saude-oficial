from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

class ChecklistTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.username = 'testuser'
        self.password = 'testpass123'
        self.user = get_user_model().objects.create_user(username=self.username, password=self.password)

    def test_login_logout(self):
        # Login
        response = self.client.post(reverse('login'), {'username': self.username, 'password': self.password})
        self.assertEqual(response.status_code, 302)  # Redirect after login
        # Logout
        response = self.client.post(reverse('logout'))
        self.assertEqual(response.status_code, 302)

    def test_home_page(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Transporte de Pacientes')

    def test_cadastrar_paciente_page(self):
        self.client.login(username=self.username, password=self.password)
        url = reverse('cadastrar_paciente')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Instruções em Português')
        self.assertContains(response, 'Instructions in English')

    def test_busca_paciente_autocomplete_url(self):
        self.client.login(username=self.username, password=self.password)
        url = reverse('buscar_pacientes_sugestoes')
        response = self.client.get(url, {'term': 'Maria'})
        self.assertIn(response.status_code, [200, 204, 302])  # Pode retornar vazio, mas não deve dar erro
