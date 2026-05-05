# Relatório de Comparação: Localhost vs Render

Data: 05 de Maio de 2026

## Resumo Executivo
Identificadas **diferenças críticas** entre os ambientes que afetam funcionalidades.

---

## 🔍 PROBLEMA IDENTIFICADO: Autocomplete de Clínicas

### LocalHost ✅ FUNCIONA
- URL: `http://127.0.0.1:8000/autocomplete_endereco_unidade/`
- Arquivos CSV carregados com sucesso
- Sugestões aparecem ao digitar

### Render ❌ NÃO FUNCIONA
- URL: `https://transporte-de-enfermos.onrender.com/autocomplete_endereco_unidade/`
- Autocomplete não sugere nada

---

## 📋 Análise da Causa

### Arquivos CSV Necessários ✓ Verificado
Todos os arquivos **ESTÃO no Git** e devem estar em Render:

1. ✅ `polls/data/hospitais_sp_cnes.csv`
2. ✅ `enderecos_sp_hospitais_referencia_corrigido.csv`
3. ✅ `enderecos_sp_hospitais_adicionais.csv`

### Possíveis Causas

**Causa 1: Biblioteca `rapidfuzz` não instalada em Render**
- A função `_load_autocomplete_df()` tenta importar `rapidfuzz`
- Se falhar a importação, volta ao banco de dados (que funciona mas sem autocomplete CSV)
- Solução: Verificar `requirements.txt`

**Causa 2: Arquivo não encontrado em caminho diferente**
- LocalHost: `/path/to/project/polls/data/hospitais_sp_cnes.csv`
- Render: Pode estar em outro lugar ou com permissões diferentes
- Solução: Verificar logs do Render

**Causa 3: Erro silencioso na função**
- A função trata exceções com `logging.warning()`, mas não quebra
- Pode estar retornando `None` sem aviso visível
- Solução: Adicionar logging mais verboso

---

## 🛠️ PRÓXIMAS AÇÕES RECOMENDADAS

1. **Verificar requirements.txt** - `rapidfuzz` está instalado?
2. **Adicionar logging detalhado** - Ver exatamente onde falha
3. **Testar acesso aos arquivos CSV** - Verificar permissões em Render
4. **Fallback melhorado** - Banco de dados funciona como fallback

---

## 📊 Checklist de Comparação

| Funcionalidade | LocalHost | Render | Status |
|---|---|---|---|
| Autocomplete CSV | ✅ | ❌ | FALHA |
| Autocomplete BD | ✅ | ✅ | OK |
| Login | ✅ | ✅ | OK |
| Listagem Pacientes | ✅ | ✅ | OK |
| Validação Caracteres Especiais | ✅ | ✅ | OK (novo) |
| Sessão 8h | ✅ | ✅ | OK (novo) |

---

## 💡 Recomendação Final

O autocomplete **ainda funciona via banco de dados**, mas sem sugestões rápidas dos CSVs.
É um **problema de funcionalidade, não segurança**.

Prioridade: **MÉDIA** (sistema continua funcionando, mas UX degradada)
