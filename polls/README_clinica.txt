# Cadastro de Clínicas - Documentação

## Funcionalidades
- Cadastro de clínicas com validação de duplicidade por nome e endereço
- Autocomplete de endereço usando AJAX e arquivos CSV
- Feedback visual para erros de autocomplete
- Interface limpa, sem elementos de teste ou duplicidade
- Validação de campos obrigatórios

## Fluxo de Salvamento
- O campo 'endereco_completo' do formulário é salvo em 'endereco' do modelo
- Campos logradouro, número e cep também são salvos se preenchidos

## Testes
- Testes automatizados garantem que duplicidade não é permitida e que clínicas válidas são salvas corretamente

## Recomendações
- Manter arquivos CSV atualizados para o autocomplete
- Revisar mensagens de erro e feedback para o usuário
- Adicionar mais testes conforme novas funcionalidades
