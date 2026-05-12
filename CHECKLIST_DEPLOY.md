# Checklist: Espelhamento Localhost x Render (Deploy Django)

## 1. Código-fonte
- [ ] Todas as alterações feitas localmente estão salvas.
- [ ] Todos os arquivos alterados foram adicionados ao git.
- [ ] Commit realizado com mensagem clara.
- [ ] Push feito para o repositório remoto (branch correto).

## 2. Dependências
- [ ] requirements.txt atualizado após instalar/atualizar pacotes.
- [ ] requirements.txt versionado e enviado ao repositório.

## 3. Banco de Dados
- [ ] Dados importantes exportados/importados via fixtures ou scripts (se necessário).
- [ ] db.sqlite3 nunca enviado para produção (adicionado ao .gitignore).

## 4. Variáveis de Ambiente
- [ ] SECRET_KEY, DEBUG, ALLOWED_HOSTS e outras variáveis configuradas corretamente em ambos ambientes.
- [ ] Variáveis sensíveis nunca versionadas no git.

## 5. Testes
- [ ] Testes executados localmente antes do push.
- [ ] (Opcional) Testes automatizados configurados no CI/CD.

## 6. Deploy
- [ ] Deploy automático do Render monitorado após cada push.
- [ ] Logs do Render verificados em caso de erro.

## 7. Sincronização de arquivos estáticos/mídia
- [ ] Arquivos estáticos coletados corretamente (python manage.py collectstatic).
- [ ] Uploads/mídia configurados para armazenamento externo se necessário.

## 8. Validação
- [ ] Funcionalidade testada no localhost.
- [ ] Funcionalidade testada no site online após deploy.
- [ ] Se houver diferença, revisar logs, dependências e variáveis de ambiente.

---

> Use este checklist antes de cada deploy para garantir que localhost e produção estejam sempre espelhados.
