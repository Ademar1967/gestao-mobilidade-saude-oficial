#!/usr/bin/env python
"""
Script para verificar a configuração do banco de dados no Render.
Execute: python check_database.py
"""
import os
import sys
from pathlib import Path

# Configura Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'transporte_django.settings')

# Adiciona o diretório do projeto ao path
sys.path.insert(0, str(Path(__file__).parent))

import django
django.setup()

from django.conf import settings
from django.db import connection

print("=" * 70)
print("VERIFICAÇÃO DE CONFIGURAÇÃO DO BANCO DE DADOS")
print("=" * 70)

# 1. Variável DATABASE_URL
db_url = os.environ.get('DATABASE_URL', '').strip()
print(f"\n1. DATABASE_URL configurada?")
if db_url:
    print(f"   ✓ SIM (primeiros 60 chars): {db_url[:60]}...")
else:
    print(f"   ✗ NÃO - Usando SQLite padrão!")

# 2. ENGINE do banco
db_engine = settings.DATABASES['default']['ENGINE']
print(f"\n2. Engine sendo usado:")
print(f"   {db_engine}")

# 3. Nome do banco
db_name = settings.DATABASES['default'].get('NAME', 'N/A')
print(f"\n3. Nome do banco:")
print(f"   {db_name}")

# 4. Tenta conectar
print(f"\n4. Testando conexão...")
try:
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
    print(f"   ✓ Conexão OK!")
except Exception as e:
    print(f"   ✗ Erro: {str(e)[:100]}")

# 5. Resumo
print(f"\n" + "=" * 70)
if 'postgresql' in db_engine.lower():
    print("✓ Você está usando PostgreSQL - Dados persistem entre deploys!")
elif 'sqlite' in db_engine.lower():
    print("⚠ Você está usando SQLite - Dados são perdidos a cada deploy!")
    print("  → Configure DATABASE_URL no Render com um PostgreSQL")
else:
    print(f"? Banco desconhecido: {db_engine}")

print("=" * 70)
