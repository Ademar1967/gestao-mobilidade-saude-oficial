"""
WSGI config for transporte_django project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os

# Diagnóstico automático para Render: verifica se pandas está disponível
import sys

print("[DIAGNOSTICO-WSGI] PYTHONPATH:", sys.path)
try:
    import pandas

    print("[DIAGNOSTICO-WSGI] Pandas importado com sucesso!")
except Exception as e:
    print("[DIAGNOSTICO-WSGI] Erro ao importar pandas:", e)

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "transporte_django.settings")

application = get_wsgi_application()
