# Consolidado para rodar sempre, independente do ambiente
import os
import sys
import time

# 1. Configuração do Django
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'transporte_django.settings')
import django
django.setup()
from django.contrib.auth import get_user_model

# 2. Variáveis de configuração
TEST_USER = 'testuser'
TEST_PASS = 'testpass123'
BASE_URL = 'http://127.0.0.1:8000'
LOGIN_URL = f'{BASE_URL}/accounts/login/'
PACIENTE_URL = f'{BASE_URL}/pacientes/cadastrar/'

# 3. Cria usuário de teste se não existir
User = get_user_model()
if not User.objects.filter(username=TEST_USER).exists():
    User.objects.create_user(username=TEST_USER, password=TEST_PASS)

# 4. Selenium imports e setup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

# Garante execução no diretório do script
os.chdir(os.path.dirname(os.path.abspath(__file__)))

options = Options()
options.add_argument('--headless')
options.add_argument('--window-size=1200,800')

# --- Permissões automáticas para notificações e localização ---
options.add_experimental_option("prefs", {
    "profile.default_content_setting_values.notifications": 1,  # Permite notificações
    "profile.default_content_setting_values.geolocation": 1,    # Permite localização
})

driver = webdriver.Chrome(options=options)

def fail(msg):
    print(f'FALHOU: {msg}')
    driver.quit()
    sys.exit(1)

try:
    # 1. Login
    try:
        driver.get(LOGIN_URL)
        time.sleep(1)
        user_input = driver.find_element(By.NAME, 'username')
        pass_input = driver.find_element(By.NAME, 'password')
        user_input.send_keys(TEST_USER)
        pass_input.send_keys(TEST_PASS)
        pass_input.send_keys(Keys.RETURN)
        time.sleep(1)
    except Exception as e:
        fail(f'Erro no login: {e}')

    # 2. Cadastro de paciente
    try:
        driver.get(PACIENTE_URL)
        time.sleep(1)
    except Exception as e:
        fail(f'Erro ao acessar cadastro de paciente: {e}')

    # 3. Testar botões de instrução
    try:
        btn_pt = driver.find_element(By.XPATH, "//button[contains(., 'Instruções em Português')]")
        btn_en = driver.find_element(By.XPATH, "//button[contains(., 'Instructions in English')]")
        btn_pt.click()
        time.sleep(0.5)
        btn_en.click()
        time.sleep(0.5)
    except Exception as e:
        fail(f'Erro ao testar botões de instrução: {e}')

    # 4. Testar autocomplete (busca paciente)
    try:
        busca_input = driver.find_element(By.ID, 'input-busca-paciente-navbar')
        busca_input.send_keys('Maria')
        time.sleep(1)
        dropdown = driver.find_element(By.ID, 'autocomplete-paciente-navbar')
        assert dropdown.is_displayed(), 'Dropdown de autocomplete não exibido'
    except Exception as e:
        fail(f'Erro no autocomplete: {e}')

    print('Teste Selenium: PASSOU em todos os passos principais!')
finally:
    driver.quit()
