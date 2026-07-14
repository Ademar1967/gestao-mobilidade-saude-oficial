#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""

import os
import sys

# Diagnóstico automático para Render: verifica se pandas está disponível
print("[DIAGNOSTICO] PYTHONPATH:", sys.path)
try:
    import pandas

    print("[DIAGNOSTICO] Pandas importado com sucesso!")
except Exception as e:
    print("[DIAGNOSTICO] Erro ao importar pandas:", e)


def main():
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "transporte_django.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
