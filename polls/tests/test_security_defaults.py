import importlib
import os

import django
from django.test import SimpleTestCase

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "transporte_django.settings")
django.setup()


class SecurityDefaultsTests(SimpleTestCase):
    def test_debug_defaults_to_false_when_env_is_unset(self):
        original_debug = os.environ.get("DJANGO_DEBUG")
        original_secret = os.environ.get("DJANGO_SECRET_KEY")

        try:
            os.environ["DJANGO_SECRET_KEY"] = "test-secret-key-1234567890"
            os.environ.pop("DJANGO_DEBUG", None)

            import transporte_django.settings as settings_module

            reloaded_module = importlib.reload(settings_module)

            self.assertFalse(reloaded_module.DEBUG)
            self.assertEqual(reloaded_module.SECRET_KEY, "test-secret-key-1234567890")
        finally:
            if original_debug is None:
                os.environ.pop("DJANGO_DEBUG", None)
            else:
                os.environ["DJANGO_DEBUG"] = original_debug

            if original_secret is None:
                os.environ.pop("DJANGO_SECRET_KEY", None)
            else:
                os.environ["DJANGO_SECRET_KEY"] = original_secret

            import transporte_django.settings as settings_module

            importlib.reload(settings_module)
