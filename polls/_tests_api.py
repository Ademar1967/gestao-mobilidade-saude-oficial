from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth.models import User
from .models import Paciente


class PacienteAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_create_paciente(self):
        url = reverse("paciente-list")
        data = {"nome": "Paciente Teste", "idade": 30, "peso": 70.5}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Paciente.objects.count(), 1)
        self.assertEqual(Paciente.objects.get().nome, "Paciente Teste")

    def test_list_pacientes(self):
        Paciente.objects.create(nome="Paciente 1")
        url = reverse("paciente-list")
        response = self.client.get(url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_update_paciente(self):
        paciente = Paciente.objects.create(nome="Paciente 2")
        url = reverse("paciente-detail", args=[paciente.id])
        data = {"nome": "Paciente Atualizado"}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        paciente.refresh_from_db()
        self.assertEqual(paciente.nome, "Paciente Atualizado")

    def test_delete_paciente(self):
        paciente = Paciente.objects.create(nome="Paciente 3")
        url = reverse("paciente-detail", args=[paciente.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Paciente.objects.count(), 0)
