import os
import django
from django.test import TestCase
from django.urls import reverse

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "transporte_django.settings")
django.setup()


class LoginObrigatorioTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        from django.conf import settings

        settings.ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]

    def test_home_sem_login_redireciona_para_login(self):
        response = self.client.get(reverse("transporte_pacientes:home"), follow=False)

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))
