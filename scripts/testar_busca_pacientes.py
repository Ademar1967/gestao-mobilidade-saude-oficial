import requests
import re
import sys
import os

BASE_URL = "http://127.0.0.1:8000"
LOGIN_URL = f"{BASE_URL}/login/"
BUSCA_URL = f"{BASE_URL}/api/pacientes/sugestoes/?q=Teste"


def get_credenciais():
    if len(sys.argv) >= 3:
        return sys.argv[1], sys.argv[2]
    usuario = os.environ.get("TESTE_USUARIO")
    senha = os.environ.get("TESTE_SENHA")
    if usuario and senha:
        return usuario, senha
    usuario = input("Usuário: ")
    senha = input("Senha (visível): ")
    return usuario, senha


usuario, senha = get_credenciais()
session = requests.Session()

# 1. Captura CSRF token da página de login
resp = session.get(LOGIN_URL)
csrf_token = None
if resp.status_code == 200:
    m = re.search(
        r'name=["\']csrfmiddlewaretoken["\'] value=["\']([^"\']+)["\']', resp.text
    )
    if m:
        csrf_token = m.group(1)

if not csrf_token:
    print("Falha ao capturar CSRF token!")
    exit(1)

# 2. Login com CSRF token
login_data = {
    "username": usuario,
    "password": senha,
    "csrfmiddlewaretoken": csrf_token,
    "next": "/",
}
headers = {"Referer": LOGIN_URL}
resp = session.post(LOGIN_URL, data=login_data, headers=headers, allow_redirects=True)

if "sessionid" not in session.cookies.get_dict():
    print("Falha no login!")
    exit(1)
print("Login realizado com sucesso.")

# 3. Buscar paciente (simulando AJAX e enviando CSRF)
csrf_cookie = session.cookies.get("csrftoken")
sessionid_cookie = session.cookies.get("sessionid")
ajax_headers = {
    "X-Requested-With": "XMLHttpRequest",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
}
if csrf_cookie:
    ajax_headers["X-CSRFToken"] = csrf_cookie

print("Cookies atuais na sessão:")
for k, v in session.cookies.get_dict().items():
    print(f"  {k}: {v}")
print("\nHeaders enviados:")
for k, v in ajax_headers.items():
    print(f"  {k}: {v}")

resp = session.get(
    BUSCA_URL,
    headers=ajax_headers,
    cookies=(
        {"sessionid": sessionid_cookie, "csrftoken": csrf_cookie}
        if sessionid_cookie
        else None
    ),
)
print("\nStatus:", resp.status_code)
print("Resposta:")
print(resp.text)
