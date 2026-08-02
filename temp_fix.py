import os

caminho = r"C:\Users\elide\OneDrive\Desktop\codigos\gestao-mobilidade-saude-oficial_novo\polls\models.py"

with open(caminho, "r", encoding="utf-8") as f:
    conteudo = f.read()

# Corta tudo a partir de 'class Motorista(' — que é a segunda duplicata
idx = conteudo.find("\nclass Motorista(")
if idx != -1:
    conteudo = conteudo[:idx].rstrip() + "\n"

with open(caminho, "w", encoding="utf-8") as f:
    f.write(conteudo)

print("Duplicatas removidas com sucesso!")
