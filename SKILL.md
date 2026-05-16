# Skill: Checklist de Deploy

## Objetivo
Garantir que todos os passos críticos para um deploy seguro e estável sejam seguidos, reduzindo riscos de falhas em produção.

## Passos do Checklist
1. **Atualizar o código-fonte**
   - Certifique-se de que a branch principal está atualizada com as últimas mudanças aprovadas.
2. **Executar testes automatizados**
   - Rode todos os testes relevantes e confirme que estão passando.
3. **Verificar configurações sensíveis**
   - Confirme variáveis de ambiente, arquivos de configuração e segredos.
4. **Backup do banco de dados**
   - Realize backup completo antes de qualquer alteração.
5. **Aplicar migrações**
   - Execute as migrações do banco de dados e valide o sucesso.
6. **Coletar arquivos estáticos** (se aplicável)
   - Execute o comando de coleta de estáticos (ex: `collectstatic` no Django).
7. **Deploy propriamente dito**
   - Realize o deploy usando o script ou ferramenta padrão do projeto.
8. **Verificação pós-deploy**
   - Acesse o sistema, realize testes manuais básicos e monitore logs.
9. **Comunicação**
   - Avise o time sobre a finalização do deploy e qualquer ponto de atenção.

## Critérios de Qualidade
- Todos os testes devem passar antes do deploy.
- Backup realizado e validado.
- Logs monitorados nos primeiros minutos após o deploy.
- Comunicação clara com o time.

## Exemplo de prompt
- "Execute o checklist de deploy para o projeto X."
- "Quais passos faltam para finalizar o deploy?"

## Sugestão de customização
- Adaptar para diferentes ambientes (homologação, produção).
- Incluir etapas específicas do seu fluxo (ex: revisão de acessos, limpeza de cache).
