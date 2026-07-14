from django.urls import reverse
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from rest_framework import status


class AuthJWTTests(APITestCase):
    def setUp(self):
        self.username = "jwtuser"
        self.password = "jwtpass123"
        User.objects.create_user(username=self.username, password=self.password)

    def test_obtain_jwt_token(self):
        url = "/api/token/"
        data = {"username": self.username, "password": self.password}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_access_protected_api(self):
        # Get JWT token
        url = "/api/token/"
        data = {"username": self.username, "password": self.password}
        response = self.client.post(url, data, format="json")
        token = response.data["access"]
        # Try to access protected endpoint
        self.client.credentials(HTTP_AUTHORIZATION="Bearer " + token)
        api_url = "/api/pacientes/"
        response = self.client.get(api_url)
        self.assertNotEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_access_denied_without_token(self):
        api_url = "/api/pacientes/"
        response = self.client.get(api_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
