import pandas as pd
import requests
import zipfile
import io
import os

# URL oficial do CNES para estabelecimentos de saúde (atualizado periodicamente)
URL = "https://ftp.datasus.gov.br/ftp/cnes/BASE_DE_DADOS_CNES_202603.zip"
ZIP_NAME = "BASE_DE_DADOS_CNES_202603.zip"
CSV_NAME = "tbEstabelecimento202603.csv"  # Nome do arquivo dentro do ZIP (ajustar conforme mês/ano)

# Pasta e nome do arquivo de saída
OUTPUT_DIR = "BACKUPS_MANUAIS"
OUTPUT_FILE = "hospitais_sp_cnes.csv"

# Tenta abrir o ZIP localmente primeiro
if os.path.exists(ZIP_NAME):
	print(f"Arquivo {ZIP_NAME} encontrado localmente. Usando arquivo local.")
	z = zipfile.ZipFile(ZIP_NAME)
else:
	print("Baixando base CNES...")
	r = requests.get(URL)
	with open(ZIP_NAME, "wb") as f:
		f.write(r.content)
	z = zipfile.ZipFile(io.BytesIO(r.content))

# Extrair o CSV desejado
print("Extraindo CSV...")
z.extract(CSV_NAME)

# Ler o CSV (atenção ao encoding e separador)
df = pd.read_csv(CSV_NAME, sep=';', encoding='latin1', dtype=str)

# Códigos dos municípios da Grande São Paulo (incluindo Mogi das Cruzes e região)
COD_MUNICIPIOS_GRANDE_SP = [
    '355030', # São Paulo
    '350950', # Arujá
    '350280', # Barueri
    '350570', # Biritiba Mirim
    '350760', # Cajamar
    '351060', # Carapicuíba
    '351880', # Cotia
    '352500', # Diadema
    '351500', # Embu das Artes
    '351510', # Embu-Guaçu
    '351570', # Ferraz de Vasconcelos
    '351630', # Francisco Morato
    '351640', # Franco da Rocha
    '351880', # Guarulhos
    '352250', # Itapecerica da Serra
    '352310', # Itapevi
    '352340', # Itaquaquecetuba
    '352500', # Jandira
    '352590', # Juquitiba
    '352940', # Mairiporã
    '352940', # Mauá
    '353060', # Mogi das Cruzes
    '353440', # Osasco
    '353650', # Pirapora do Bom Jesus
    '353910', # Poá
    '354330', # Ribeirão Pires
    '354340', # Rio Grande da Serra
    '354410', # Salesópolis
    '354780', # Santa Isabel
    '354870', # Santana de Parnaíba
    '354880', # Santo André
    '354890', # São Bernardo do Campo
    '354910', # São Caetano do Sul
    '355030', # São Paulo (repetido para garantir)
    '355220', # Suzano
    '355645', # Taboão da Serra
    '355715', # Vargem Grande Paulista
]

# Filtrar hospitais de todos esses municípios
df_sp = df[(df['CO_MUNICIPIO_GESTOR'].isin(COD_MUNICIPIOS_GRANDE_SP)) & (df['TP_ESTAB'] == 'HOSPITAL')]

# Selecionar colunas principais
colunas = ['NO_FANTASIA', 'DS_ENDERECO', 'NU_ENDERECO', 'DS_BAIRRO', 'CO_CEP', 'NO_MUNICIPIO', 'CO_CNES']
df_saida = df_sp[colunas]

# Garantir pasta de saída
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Salvar CSV
saida_path = os.path.join(OUTPUT_DIR, OUTPUT_FILE)
df_saida.to_csv(saida_path, index=False, encoding='utf-8')

print(f"Arquivo gerado: {saida_path}")
print(f"Total de hospitais encontrados: {len(df_saida)}")
