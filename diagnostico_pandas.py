import sys

print("PYTHONPATH:", sys.path)
try:
    import pandas

    print("Pandas importado com sucesso!")
except Exception as e:
    print("Erro ao importar pandas:", e)
