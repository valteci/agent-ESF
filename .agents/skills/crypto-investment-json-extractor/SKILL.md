---
name: crypto-investment-json-extractor
description: Use esta skill quando a tarefa envolver compra ou venda de criptomoedas ou criptoativos em corretoras ou exchanges, e a saída precisar ser um JSON de transações contábeis no formato ledger.
---

# Objetivo
Transformar entradas multimodais relacionadas a operações de compra e venda de criptoativos em JSON estruturado no formato definido em `references/schema.md`.

Nesta skill, cada operação de compra ou venda gera exatamente 2 transações JSON:
1. transação financeira em dinheiro
2. transação de quantidade do criptoativo

Esta skill cobre apenas operações de compra e venda com perna monetária identificável.
Não cobre swaps cripto-cripto, staking, earn, rendimentos, airdrops, mineração, transferências on-chain, futuros, margem, alavancagem nem eventos corporativos/tokenomics.

# Quando usar
Use esta skill quando o usuário:
- enviar nota de corretagem, extrato, trade history ou comprovante de exchange
- enviar imagem, print ou PDF com compra ou venda de criptomoeda
- enviar texto descrevendo compra ou venda de criptoativo
- informar que houve compra ou venda de cripto e pedir geração do JSON ledger correspondente

# Regras gerais
1. Sempre considerar o contexto enviado pelo usuário junto com os arquivos.
2. A saída final deve ser somente JSON válido, sem texto antes ou depois.
3. O JSON deve seguir exatamente o formato definido em `references/schema.md`.
4. O objeto raiz deve conter sempre a chave `transactions`.
5. `transactions` deve ser sempre uma lista, mesmo quando estiver vazia.
6. Cada item de `transactions` deve ser um objeto com exatamente estas chaves:
   - `from`
   - `to`
   - `amount`
   - `type`
   - `timestamp`
   - `obs`
7. Não adicionar chaves extras fora do schema.
8. Todos os valores de cada transação devem ser strings.
9. Cada operação de compra ou venda deve gerar exatamente 2 transações JSON, nem mais, nem menos.
10. Se houver múltiplas operações no mesmo documento, gerar exatamente 2 transações para cada operação consolidada.
11. Se o mesmo criptoativo aparecer em múltiplas execuções na mesma direção (`buy` ou `sell`), na mesma instituição, no mesmo documento e na mesma data operacional, consolidar essas execuções em uma única operação lógica antes de gerar o JSON.
12. O nome do criptoativo nos campos `from` e `to`, quando representar o ativo, deve ser sempre o nome completo em caixa alta, por exemplo `BITCOIN`, `ETHEREUM`, `SOLANA`. Nunca usar ticker abreviado como `BTC`, `ETH` ou `SOL` nesses campos.
13. O campo de quantidade deve seguir a mesma lógica da skill de investimentos: `qtde__bens` representa o estoque e o ativo deve aparecer como `NOME COMPLETO_QTDE`.
14. Quantidades podem ser fracionárias com várias casas decimais. Preserve a precisão informada pela evidência, por exemplo `"0.12345678"`, sem truncar casas significativas.
15. O campo `timestamp` deve usar o formato `DD-MM-YYYY`.
16. O campo `amount` deve ser sempre string numérica.
17. O campo `type` de compra é sempre `buy`.
18. O campo `type` de venda é sempre `sell`.
19. O modelo de taxa deve ser inferido a partir do contexto e do documento. Não assumir que a taxa é sempre em dinheiro nem sempre em criptoativo.
20. Se o documento trouxer apenas o ticker, converta para o nome completo em caixa alta quando essa expansão puder ser feita com segurança. Se não puder, interrompa o processo e reporte erro em vez de emitir o ticker abreviado.

# Escopo desta versão
Esta versão cobre compra e venda de criptoativos com perna monetária identificável em corretora, exchange ou conta financeira.

Cenários cobertos:
- compra de cripto com dinheiro
- venda de cripto por dinheiro
- taxa cobrada em dinheiro
- taxa cobrada no mesmo criptoativo negociado
- coexistência de taxa em dinheiro e taxa no mesmo criptoativo, quando o documento mostrar ambas com clareza

Cenários fora de escopo:
- swap entre dois criptoativos
- taxa cobrada em um terceiro criptoativo diferente do ativo negociado
- transferências entre carteiras
- depósito ou saque on-chain
- staking, lend, earn, farming ou rendimento
- futuros, perpétuos, opções ou margem

# Normalização
Aplique apenas normalização básica, quando possível:
- datas em `DD-MM-YYYY`
- valores monetários em formato textual decimal, por exemplo: `"2500.00"`
- quantidades em formato textual com a precisão necessária, por exemplo: `"0.99999900"` ou `"12.34567891"`
- nomes de criptoativos no formato nome completo em caixa alta, por exemplo: `BITCOIN`, `ETHEREUM`, `USD COIN`
- texto sem espaços supérfluos

# Estrutura de cada operação
Cada operação de compra ou venda deve ser expandida em exatamente 2 transações:

## 1) Transação financeira
Representa o dinheiro alocado ou desalocado.

## 2) Transação de quantidade
Representa a quantidade do criptoativo que efetivamente entrou ou saiu de `qtde__bens`.

# Regras de transformação: compra
Quando a operação for uma compra:

## Primeira transação: dinheiro
- `from`: instituição financeira, conta ou exchange de onde saiu o dinheiro, obrigatoriamente usando um valor permitido pela taxonomia
- `to`: nome completo do criptoativo comprado, em caixa alta
- `amount`: valor monetário total desembolsado
- `type`: `buy`
- `timestamp`: data da operação
- `obs`: descrição resumida da compra

### Como calcular o `amount` financeiro na compra
1. Se a taxa foi cobrada em dinheiro, somar a parcela proporcional dessa taxa ao valor financeiro da compra.
2. Se a taxa foi cobrada no mesmo criptoativo comprado, não converter essa taxa para dinheiro sem evidência; nesse caso, usar o valor monetário efetivamente debitado.
3. Se houver taxa em dinheiro e também taxa no mesmo criptoativo, aplicar cada uma na sua perna correta:
   - taxa em dinheiro altera o `amount` financeiro
   - taxa em cripto altera a `amount` da transação de quantidade

## Segunda transação: quantidade
- `from`: `qtde__bens`
- `to`: nome completo do criptoativo seguido de `_QTDE`
- `amount`: quantidade que efetivamente entrou em custódia
- `type`: `buy`
- `timestamp`: data da operação
- `obs`: descrição resumida da compra

### Como calcular o `amount` de quantidade na compra
1. Se não houve taxa em cripto, usar a quantidade comprada.
2. Se a taxa foi cobrada no mesmo criptoativo comprado, usar a quantidade líquida recebida:
   - `quantidade_liquida = quantidade_bruta - taxa_em_cripto`
3. Se o documento já trouxer diretamente a quantidade líquida creditada, usar essa quantidade líquida como fonte prioritária.

## Exemplo de compra com taxa em cripto
Se houve compra de 1 BITCOIN na binance por 500000.00 e a exchange reteve 0.000001 BITCOIN como taxa:

```json
{
  "transactions": [
    {
      "from": "binance",
      "to": "BITCOIN",
      "amount": "500000.00",
      "type": "buy",
      "timestamp": "08-08-2026",
      "obs": "Compra de 1 BITCOIN na binance com taxa em BITCOIN"
    },
    {
      "from": "qtde__bens",
      "to": "BITCOIN_QTDE",
      "amount": "0.999999",
      "type": "buy",
      "timestamp": "08-08-2026",
      "obs": "Compra liquida de 0.999999 BITCOIN na binance"
    }
  ]
}
```

# Regras de transformação: venda
Quando a operação for uma venda:

## Primeira transação: dinheiro
- `from`: nome completo do criptoativo vendido, em caixa alta
- `to`: instituição financeira, conta ou exchange que recebeu o dinheiro, obrigatoriamente usando um valor permitido pela taxonomia
- `amount`: valor monetário líquido recebido
- `type`: `sell`
- `timestamp`: data da operação
- `obs`: descrição resumida da venda

### Como calcular o `amount` financeiro na venda
1. Se a taxa foi cobrada em dinheiro, subtrair a parcela proporcional dessa taxa do valor bruto da venda.
2. Se a taxa foi cobrada no mesmo criptoativo vendido, usar o valor monetário efetivamente creditado e não subtrair novamente uma taxa em dinheiro inexistente.
3. Se houver taxa em dinheiro e também taxa no mesmo criptoativo, aplicar cada uma na sua perna correta:
   - taxa em dinheiro reduz o `amount` financeiro
   - taxa em cripto altera a `amount` da transação de quantidade

## Segunda transação: quantidade
- `from`: nome completo do criptoativo seguido de `_QTDE`
- `to`: `qtde__bens`
- `amount`: quantidade que efetivamente saiu da custódia
- `type`: `sell`
- `timestamp`: data da operação
- `obs`: descrição resumida da venda

### Como calcular o `amount` de quantidade na venda
1. Se não houve taxa em cripto, usar a quantidade vendida.
2. Se a taxa foi cobrada no mesmo criptoativo vendido e saiu da própria custódia, usar a quantidade total debitada:
   - `quantidade_debitada = quantidade_vendida + taxa_em_cripto`
3. Se o documento já trouxer diretamente a quantidade total debitada da custódia, usar esse valor como fonte prioritária.

## Exemplo de venda com taxa em cripto
Se houve venda de 0.25000000 ETHEREUM na foxbit por 2500.00 e a exchange reteve 0.00050000 ETHEREUM como taxa:

```json
{
  "transactions": [
    {
      "from": "ETHEREUM",
      "to": "foxbit",
      "amount": "2500.00",
      "type": "sell",
      "timestamp": "08-08-2026",
      "obs": "Venda de 0.25000000 ETHEREUM na foxbit com taxa em ETHEREUM"
    },
    {
      "from": "ETHEREUM_QTDE",
      "to": "qtde__bens",
      "amount": "0.25050000",
      "type": "sell",
      "timestamp": "08-08-2026",
      "obs": "Saida total de 0.25050000 ETHEREUM na foxbit"
    }
  ]
}
```

# Regras para taxa e fechamento

## Modelos de taxa aceitos
1. taxa em dinheiro
2. taxa no mesmo criptoativo negociado
3. combinação de taxa em dinheiro e taxa no mesmo criptoativo, se ambas estiverem claramente documentadas

## Regra principal
Cada taxa deve afetar apenas a perna que ela realmente impacta:

1. taxa em dinheiro:
   - compra: aumenta o `amount` financeiro
   - venda: reduz o `amount` financeiro
2. taxa no mesmo criptoativo:
   - compra: reduz a quantidade creditada em `qtde__bens`
   - venda: aumenta a quantidade debitada de `qtde__bens`
3. Nunca converter automaticamente taxa em cripto para dinheiro sem evidência explícita.
4. Nunca ignorar taxas quando elas estiverem presentes ou puderem ser inferidas com segurança.

## Notas com múltiplas operações
Quando um mesmo documento contiver mais de uma operação:

1. identificar todas as operações individualmente
2. consolidar execuções equivalentes antes de distribuir taxas compartilhadas
3. calcular o valor financeiro base de cada operação consolidada
4. distribuir taxas em dinheiro proporcionalmente ao valor financeiro de cada operação consolidada
5. distribuir taxas em cripto proporcionalmente apenas entre execuções consolidadas do mesmo criptoativo e mesma direção, quando o documento não trouxer a taxa já segregada
6. aplicar cada taxa na perna correta da operação correspondente

# Validação do montante
A validação estrutural e material é obrigatória.

## O que validar
1. a soma dos valores monetários das transações financeiras geradas no JSON
2. a compatibilidade dessa soma com o total monetário esperado do documento, considerando apenas taxas monetárias
3. a coerência entre:
   - criptoativo
   - quantidade
   - tipo da operação
   - instituição de origem ou destino
   - valor monetário final
4. a compatibilidade das transações de quantidade com o impacto real em custódia quando houver taxa no próprio criptoativo

## Regra de fechamento obrigatório
Após consolidar as operações e aplicar as taxas:

1. a soma dos `amount` das transações financeiras deve bater com o total monetário efetivo do documento
2. a soma das transações de quantidade deve bater com a quantidade efetivamente creditada ou debitada da custódia
3. considerar compras e vendas separadamente quando o documento apresentar ambos os lados
4. não forçar taxa em cripto a fechar o total financeiro em dinheiro
5. se houver diferença após a geração do JSON, revisar:
   - a consolidação das execuções
   - o modelo de taxa identificado
   - a distribuição proporcional das taxas
6. fazer no máximo 3 tentativas no total
7. se, após 3 tentativas, a soma continuar divergente, interromper o processo e reportar erro

# Regra de consolidação obrigatória
Antes de gerar o JSON final, consolide execuções que pertençam à mesma operação lógica.

Considere como uma única operação lógica os lançamentos que, ao mesmo tempo:
- sejam do mesmo criptoativo
- tenham a mesma direção (`buy` ou `sell`)
- usem a mesma instituição financeira ou exchange
- pertençam ao mesmo documento
- tenham a mesma data operacional

Nesses casos:
1. somar a quantidade bruta executada
2. somar o valor financeiro base
3. somar a taxa monetária proporcional aplicável
4. somar a taxa em cripto aplicável
5. tratar o resultado consolidado como uma única operação
6. gerar apenas 2 transações JSON para essa operação consolidada

Importante:
- preços diferentes de execução não significam, por si só, operações diferentes no JSON
- a consolidação deve ocorrer antes da distribuição proporcional de taxas compartilhadas

# Processo
1. Identifique os tipos de entrada disponíveis:
   - texto
   - imagem
   - PDF
   - áudio
2. Extraia os dados relevantes de cada entrada.
3. Combine os dados extraídos com o contexto do usuário.
4. Identifique todas as operações de compra e venda presentes na entrada.
5. Para cada execução detectada, extraia:
   - instituição financeira ou exchange
   - criptoativo
   - ticker eventualmente informado
   - nome completo canônico do criptoativo
   - quantidade bruta
   - valor financeiro base
   - taxa em dinheiro, se existir
   - taxa no mesmo criptoativo, se existir
   - data
   - direção da operação
6. Converta ticker abreviado para nome completo em caixa alta.
7. Consolide execuções que pertençam à mesma operação lógica antes de gerar o JSON.
8. Para cada operação consolidada, identifique qual modelo de taxa se aplica.
9. Gere exatamente 2 transações por operação consolidada conforme as regras desta skill.
10. Monte a lista final `transactions`.
11. Valide a estrutura do JSON.
12. Valide o fechamento monetário e o impacto quantitativo em custódia.
13. Se a validação falhar, tente corrigir a consolidação, o mapeamento do ativo e a distribuição das taxas.
14. Faça no máximo 3 tentativas.
15. Se, após 3 tentativas, ainda houver inconsistência estrutural ou material, interrompa o processo e reporte erro.

# Exemplos
Consulte `references/examples.md` como exemplos canônicos de saída esperada antes de validar o JSON final.

# Casos especiais
- Se o documento estiver ilegível, não invente valores.
- Se o criptoativo não puder ser identificado com segurança no nome completo, interrompa o processo e reporte erro.
- Se a instituição financeira ou exchange não puder ser mapeada para um valor permitido pela taxonomia, interrompa o processo e reporte erro.
- Se a quantidade não puder ser identificada com segurança, interrompa o processo e reporte erro.
- Se a taxa existir, mas o documento não permitir saber se ela afeta dinheiro ou quantidade, interrompa o processo e reporte erro.
- Se a taxa for cobrada em um terceiro criptoativo diferente do ativo negociado, interrompa o processo e reporte erro, porque isso exigiria transação adicional fora do escopo desta skill.
- Não gerar swaps, staking, rendimentos, transferências, depósitos, saques nem derivativos nesta skill.

# Validação
Use o script abaixo para validar o JSON gerado:
- `python scripts/validate_json.py caminho/do/arquivo.json`

Se a validação ocorrer por stdin, também é aceitável:
- `cat caminho/do/arquivo.json | python scripts/validate_json.py`

Considere a validação bem-sucedida apenas quando o script indicar que o JSON é válido.

# Saída
- Retorne somente JSON válido, seguindo exatamente o schema definido em `references/schema.md`.
- Nunca retorne JSON inválido.
- Nunca retorne JSON com operação de compra ou venda contendo quantidade diferente de 2 transações por operação.
- Nunca retorne JSON com ticker abreviado no lugar do nome completo do criptoativo.
- Nunca retorne JSON cujo fechamento monetário ou quantitativo divirja da evidência após as tentativas permitidas.
