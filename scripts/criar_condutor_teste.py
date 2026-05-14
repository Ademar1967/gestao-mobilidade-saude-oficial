from polls.models import Condutor

# Cria um condutor de teste
Condutor.objects.create(nome="Condutor Teste Busca")
print("Condutor de teste criado com sucesso!")
