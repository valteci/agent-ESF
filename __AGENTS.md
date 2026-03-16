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
- Por padrão, o objetivo principal do agente é gerar a saída estruturada em JSON.
- Persistência em planilha ou banco é uma etapa separada e só deve acontecer quando o usuário pedir explicitamente para registrar ou salvar os dados.
- A saída final deve seguir exatamente o formato definido pela skill escolhida e por `references/schema.md`.
- Antes de concluir, validar o JSON gerado com o script `scripts/validate_json.py`, conforme definido na própria skill.
- Se a validação falhar, tentar regenerar o JSON dentro do limite de tentativas definido na skill.
- Nunca retornar JSON inválido.

# Roteamento de skills

- Quando a tarefa envolver compras do dia a dia feitas com cartão de crédito ou pagamento de fatura de cartão de crédito, com necessidade de informar qual instituição está por trás do cartão e quais instituições servem como garantia do valor, usar a skill `credit-card-purchase-json-extractor`.
- Na skill `credit-card-purchase-json-extractor`, cada compra no crédito deve gerar exatamente 2 transações:
  - primeira transação: registrar a despesa normalmente, usando `instituição de garantia -> categoria da despesa`, com o valor integral da compra e `type` igual a `pay`
  - segunda transação: registrar o compromisso do crédito, usando `categoria da despesa -> garantia=>cartão`, repetindo valor e data da primeira transação e `type` igual a `transfer`
  - a instituição de garantia pode ser diferente da instituição do cartão
  - se faltar a instituição do cartão ou a instituição de garantia, interromper o processo ou pedir esclarecimento em vez de inventar
- Na skill `credit-card-purchase-json-extractor`, cada pagamento de fatura deve gerar 1 transação `transfer` por garantia usada no pagamento:
  - usar `from` igual a `garantia=>cartão`
  - usar `to` igual a `cartao credito`
  - se a fatura for paga com várias garantias, gerar várias transações, uma por garantia
  - se o valor total da fatura for informado, a soma das transações de pagamento deve bater com esse total
- Quando a tarefa envolver movimentações financeiras comuns, como pagamentos, recebimentos, transferências, doações, empréstimos ou gastos gerais extraídos de texto, imagem, PDF ou áudio, e não se tratar de evento de cartão de crédito, usar a skill `multimodal-json-extractor`.
- Quando o usuário já tiver um JSON válido e pedir para registrar, salvar ou inserir essas transações na planilha `ESF.ods` da raiz do projeto, usar a skill `esf-ods-ledger-writer`.
- Na skill `esf-ods-ledger-writer`, cada item do array `transactions` gera exatamente 1 linha nova na aba `F26`, mapeando:
  - `from` -> coluna A
  - `to` -> coluna B
  - `amount` -> coluna C
  - `type` -> coluna D
  - `timestamp` -> coluna E
  - coluna F fica em branco
  - `obs` -> coluna G
- Na skill `esf-ods-ledger-writer`, a persistência deve ser tratada como etapa desacoplada da geração do JSON:
  - primeiro gerar e validar o JSON pela skill de extração apropriada
  - depois, somente se o usuário pedir, executar o script da skill de persistência
  - a escrita deve ocorrer somente na aba `F26`
  - por padrão, usar a planilha `ESF.ods` da raiz do projeto
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
- Se a entrada misturar compras no crédito, pagamento de fatura de cartão e outras movimentações comuns, separar as operações por tipo e aplicar `credit-card-purchase-json-extractor` apenas aos eventos de cartão de crédito e `multimodal-json-extractor` ao restante antes de compor o JSON final.
- Se a entrada misturar compra ou venda com proventos ou ajustes de quantidade, separar as operações por tipo e aplicar a skill correspondente a cada subconjunto antes de compor o JSON final.
