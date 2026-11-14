import importlib
import os
import sys
import unittest


class DatabaseFallbackTests(unittest.TestCase):
    def test_invalid_postgres_url_falls_back_to_sqlite(self):
        os.environ["DJANGO_SECRET_KEY"] = "test-secret-key"
        os.environ["DJANGO_DEBUG"] = "1"
        os.environ["DATABASE_URL"] = "postgresql://user:pass@dpg-db58n1flot8c73e3lgm0-a:5432/dbname"
        os.environ.pop("STRICT_DATABASE_URL", None)

        sys.modules.pop("transporte_django.settings", None)
        settings_module = importlib.import_module("transporte_django.settings")
        importlib.reload(settings_module)

        self.assertEqual(
            settings_module.DATABASES["default"]["ENGINE"],
            "django.db.backends.sqlite3",
        )
