from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from rest_framework import status
from .models import Paciente, Clinica, Condutor, Enfermagem, Veiculo


class APICrudTests(APITestCase):
    def setUp(self):
        self.username = "apiuser"
        self.password = "apipass123"
        User.objects.create_user(username=self.username, password=self.password)
        url = "/api/token/"
        data = {"username": self.username, "password": self.password}
        response = self.client.post(url, data, format="json")
        self.token = response.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + self.token)

    def test_paciente_crud(self):
        # Create
        data = {"nome": "Paciente Teste", "idade": 40}
        response = self.client.post("/api/pacientes/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        paciente_id = response.data["id"]
        # List
        response = self.client.get("/api/pacientes/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Update
        response = self.client.patch(
            f"/api/pacientes/{paciente_id}/", {"idade": 41}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Delete
        response = self.client.delete(f"/api/pacientes/{paciente_id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_clinica_crud(self):
        data = {"nome": "Clínica Teste"}
        response = self.client.post("/api/clinicas/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        clinica_id = response.data["id"]
        response = self.client.get("/api/clinicas/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.patch(
            f"/api/clinicas/{clinica_id}/",
            {"nome": "Clínica Atualizada"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.delete(f"/api/clinicas/{clinica_id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_condutor_crud(self):
        data = {"nome": "Condutor Teste"}
        response = self.client.post("/api/condutores/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        condutor_id = response.data["id"]
        response = self.client.get("/api/condutores/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.patch(
            f"/api/condutores/{condutor_id}/",
            {"nome": "Condutor Atualizado"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.delete(f"/api/condutores/{condutor_id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_enfermagem_crud(self):
        data = {"nome": "Enfermagem Teste"}
        response = self.client.post("/api/enfermagens/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        enfermagem_id = response.data["id"]
        response = self.client.get("/api/enfermagens/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.patch(
            f"/api/enfermagens/{enfermagem_id}/",
            {"nome": "Enfermagem Atualizada"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.delete(f"/api/enfermagens/{enfermagem_id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_veiculo_crud(self):
        data = {
            "tipo_veiculo": "ambulancia",
            "placa": "ABC1234",
            "patrimonio": "P001",
            "lotacao": 2,
        }
        response = self.client.post("/api/veiculos/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        veiculo_id = response.data["id"]
        response = self.client.get("/api/veiculos/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.patch(
            f"/api/veiculos/{veiculo_id}/", {"lotacao": 3}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.delete(f"/api/veiculos/{veiculo_id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
