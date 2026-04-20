import pandas as pd
import os
import django

def main():
    # Configuração do Django para o projeto correto
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'transporte_django.settings')
    django.setup()
    from polls.models import Clinica

    # Caminho do arquivo Excel (ajuste se necessário)
    excel_path = r'C:/Users/elide/OneDrive/Desktop/codigos/RELATORIO_REAL_estabelecimentos_SP_1770339354.xlsx'

    # Lê o arquivo Excel
    df = pd.read_excel(excel_path)

    # Renomeie as colunas se necessário para garantir compatibilidade
    df = df.rename(columns={
        'ID': 'id_cnes',
        'CNES': 'cnes',
        'NOME': 'nome',
        'TIPO': 'tipo',
        'LOGRADOURO': 'logradouro',
        'NUMERO': 'numero',
        'COMPLEMENTO': 'complemento',
    })

    total = 0
    for _, row in df.iterrows():
        clinica, created = Clinica.objects.get_or_create(
            cnes=row['cnes'],
            defaults={
                'nome': row['nome'],
                'tipo': row['tipo'],
                'logradouro': row['logradouro'],
                'numero': row['numero'],
                'complemento': row.get('complemento', ''),
            }
        )
        total += 1
    print(f"Importação concluída: {total} clínicas processadas.")

if __name__ == '__main__':
    main()
