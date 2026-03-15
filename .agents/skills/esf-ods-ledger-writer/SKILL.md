---
name: esf-ods-ledger-writer
description: Use esta skill quando o usuário já tiver um JSON válido com a chave `transactions` e pedir para registrar essas transações na planilha `ESF.ods` da raiz do projeto, inserindo uma linha por transação na aba `F26`.
---

# Objetivo
Persistir transações já estruturadas em JSON na planilha ODS do projeto, inserindo novas linhas apenas na aba `F26`.

Esta skill não extrai dados, não classifica transações e não gera JSON.
Ela apenas recebe um JSON já pronto e grava cada item de `transactions` como uma nova linha na tabela da aba `F26`.

# Quando usar
Use esta skill quando o usuário:
- pedir para registrar, salvar ou inserir transações na planilha ODS do projeto
- mencionar a planilha `ESF.ods` na raiz
- já tiver um JSON final válido e quiser apenas persisti-lo

# Regras gerais
1. Antes de usar esta skill, confirme que o JSON já está pronto e válido.
2. O objeto raiz deve conter `transactions`.
3. Também aceite a chave `transactinos` por compatibilidade com eventuais erros de digitação no fluxo externo.
4. Cada item de `transactions` deve representar exatamente uma linha a ser inserida.
5. Esta skill escreve somente na aba `F26`.
6. Não modificar outras abas, fórmulas, objetos, estilos ou arquivos internos do `.ods` além do necessário para acrescentar as novas linhas.
7. Mapear os campos do JSON para a tabela da aba `F26` nesta ordem:
   - coluna A: `from`
   - coluna B: `to`
   - coluna C: `amount`
   - coluna D: `type`
   - coluna E: `timestamp`
   - coluna F: deixar em branco
   - coluna G: `obs`
8. Não inventar valores faltantes.
9. Se algum item não tiver os campos mínimos esperados, interromper com erro em vez de gravar linhas parciais.
10. A gravação deve ser atômica: ou todas as transações entram, ou nenhuma entra.

# Processo
1. Receber o JSON já finalizado.
2. Executar o script `scripts/insert_f26_transactions.py`.
3. Passar o JSON como argumento para o script.
4. Deixar o script resolver a planilha `ESF.ods` na raiz, a menos que `--ods-path` seja informado explicitamente.
5. Confirmar no final quantas linhas foram inseridas e em qual arquivo.

# Script
Use:

```bash
python3 .agents/skills/esf-ods-ledger-writer/scripts/insert_f26_transactions.py --json '...json...'
```

Também é aceito passar um caminho de arquivo JSON:

```bash
python3 .agents/skills/esf-ods-ledger-writer/scripts/insert_f26_transactions.py --json caminho/do/arquivo.json
```

# Saída esperada
O script deve:
- retornar código `0` quando a inserção for concluída
- informar quantas transações foram inseridas
- falhar com código diferente de `0` quando o JSON ou a planilha forem inválidos
