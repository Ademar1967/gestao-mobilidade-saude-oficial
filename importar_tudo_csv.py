import os
import django
import csv

# Configuração do Django para o projeto correto
def setup_django():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'transporte_django.settings')
    django.setup()

def importar_veiculos():
    from polls.models import Veiculo
    path = 'viaturas.csv'
    if not os.path.exists(path):
        print(f"Arquivo {path} não encontrado.")
        return
    with open(path, encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        total = 0
        for row in reader:
            _, created = Veiculo.objects.get_or_create(
                patrimonio=row.get('patrimonio', '').strip(),
                defaults={
                    'placa': row.get('placa', '').strip(),
                    'tipo_veiculo': row.get('tipo_veiculo', 'ambulancia').strip() or 'ambulancia',
                }
            )
            total += 1
    print(f"Importação de viaturas concluída: {total} registros processados.")

def importar_condutores():
    from polls.models import Condutor
    path = 'condutores.csv'
    if not os.path.exists(path):
        print(f"Arquivo {path} não encontrado.")
        return
    with open(path, encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        total = 0
        for row in reader:
            _, created = Condutor.objects.get_or_create(
                nome=row.get('nome', '').strip()
            )
            total += 1
    print(f"Importação de condutores concluída: {total} registros processados.")

def importar_enfermagem():
    from polls.models import Enfermagem
    path = 'enfermagem.csv'
    if not os.path.exists(path):
        print(f"Arquivo {path} não encontrado.")
        return
    with open(path, encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        total = 0
        for row in reader:
            _, created = Enfermagem.objects.get_or_create(
                nome=row.get('nome', '').strip()
            )
            total += 1
    print(f"Importação de enfermagem concluída: {total} registros processados.")

def importar_clinicas():
    from polls.models import Clinica
    path = 'clinicas.csv'
    if not os.path.exists(path):
        print(f"Arquivo {path} não encontrado.")
        return
    with open(path, encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        total = 0
        for row in reader:
            _, created = Clinica.objects.get_or_create(
                nome=row.get('nome', '').strip(),
                defaults={
                    'endereco': row.get('endereco', '').strip(),
                    'bairro': row.get('bairro', '').strip(),
                    'cidade': row.get('cidade', '').strip(),
                    'telefone': row.get('telefone', '').strip(),
                }
            )
            total += 1
    print(f"Importação de clínicas concluída: {total} registros processados.")

def main():
    setup_django()
    importar_veiculos()
    importar_condutores()
    importar_enfermagem()
    importar_clinicas()
    print("Importação finalizada!")

if __name__ == '__main__':
    main()
