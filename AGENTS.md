# Objetivo do projeto

Este projeto usa o Codex para processar entradas multimodais do usuário e convertê-las em transações financeiras estruturadas para uma base de dados estilo livro-razão.

Cada transação deve seguir este modelo conceitual:

- `from`: origem de onde saiu o dinheiro
- `to`: destino para onde o dinheiro foi enviado
- `amount`: quantidade de dinheiro transferida de `from` para `to`
- `type`: tipo da transação
- `timestamp`: data da transação
- `obs`: observações e detalhamento da transação

# Instruções gerais

- Sempre considerar o contexto textual fornecido pelo usuário junto com os arquivos enviados.
- O objetivo nesta etapa é somente gerar a saída estruturada em JSON.
- Nesta etapa, não escrever em planilhas nem persistir dados em banco.
- A saída final deve seguir exatamente o formato definido pela skill escolhida e por `references/schema.md`.
- Antes de concluir, validar o JSON gerado com o script `scripts/validate_json.py`, conforme definido na própria skill.
- Se a validação falhar, tentar regenerar o JSON dentro do limite de tentativas definido na skill.
- Nunca retornar JSON inválido.

# Roteamento de skills

- Quando a tarefa envolver movimentações financeiras comuns, como pagamentos, recebimentos, transferências, doações, empréstimos ou gastos gerais extraídos de texto, imagem, PDF ou áudio, usar a skill `multimodal-json-extractor`.
- Quando a tarefa envolver compra ou venda de ativos de investimento na bolsa brasileira, especialmente a partir de nota de corretagem, imagem, PDF ou texto descrevendo operações de renda variável, usar a skill `investment-json-extractor`.
- Quando a tarefa envolver compra ou venda de criptomoedas ou criptoativos, especialmente a partir de extrato de exchange, trade history, imagem, PDF ou texto descrevendo operações, usar a skill `crypto-investment-json-extractor`.
- Quando a tarefa envolver proventos, rendimentos passivos, bonificações, split, inplit, staking, lend, earn ou ajuste manual de quantidade de ativos da bolsa brasileira ou criptoativos, usar a skill `asset-events-json-extractor`.
- Na skill `crypto-investment-json-extractor`, aplicar a mesma base lógica de `investment-json-extractor` para gerar 2 transações por operação, mas permitir quantidade fracionária com múltiplas casas decimais e tratar taxas conforme o contexto:
  - se a taxa for monetária, ela afeta a transação financeira como nas operações de bolsa
  - se a taxa for cobrada no próprio criptoativo negociado, ela afeta a transação de quantidade e não deve ser convertida automaticamente para dinheiro
  - quando `from` ou `to` representarem o criptoativo, usar sempre o nome completo em caixa alta, por exemplo `BITCOIN` e `ETHEREUM`, nunca `BTC` ou `ETH`
- Na skill `asset-events-json-extractor`, cada evento deve gerar exatamente 1 transação:
  - proventos monetários em reais usam `ATIVO_yeld -> instituicao`, com `type` igual a `create batch`
  - eventos que aumentam quantidade usam `qtde__bens -> ATIVO_QTDE`, com `type` igual a `buy`
  - eventos que diminuem quantidade usam `ATIVO_QTDE -> qtde__bens`, com `type` igual a `sell`
  - para criptoativos, quando o ativo aparecer em `from` ou `to`, usar sempre o nome completo em caixa alta, por exemplo `BITCOIN`, `ETHEREUM` e `SOLANA`
- Se a entrada misturar compra ou venda com proventos ou ajustes de quantidade, separar as operações por tipo e aplicar a skill correspondente a cada subconjunto antes de compor o JSON final.
