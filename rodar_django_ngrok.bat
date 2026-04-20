@echo off
REM Ativa o ambiente virtual (ajuste o caminho se necessário)
call ..\.venv\Scripts\activate.bat
REM Inicia o servidor Django em background
start "Django" cmd /k python manage.py runserver
REM Aguarda o servidor iniciar
ping 127.0.0.1 -n 5 > nul
REM Inicia o ngrok apontando para a porta 8000
start "ngrok" cmd /k ngrok http 8000
REM Mensagem de instrução
ECHO Acesse o link gerado pelo ngrok para compartilhar seu sistema.
pause
