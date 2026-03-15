---
name: investment-json-extractor
description: Use esta skill quando a tarefa envolver compra ou venda de ativos de investimento, especialmente renda variável, e a saída precisar ser um JSON de transações contábeis no formato ledger.
---

# Objetivo
Transformar entradas multimodais relacionadas a operações de investimento em JSON estruturado no formato definido em `references/schema.md`.

Nesta skill, cada operação de compra ou venda gera exatamente 2 transações JSON:
1. transação financeira em dinheiro
2. transação de quantidade do ativo

Esta skill cobre apenas operações de compra e venda.
Não cobre split, inplit, proventos, dividendos, juros, amortizações, bonificações, subscrições nem eventos corporativos.

# Quando usar
Use esta skill quando o usuário:
- enviar nota de corretagem
- enviar imagem, print ou PDF com compra ou venda de ativos
- enviar texto descrevendo compra ou venda de ações, ETFs, FIIs, BDRs ou ativos equivalentes
- informar que houve compra ou venda de investimento e pedir geração do JSON ledger correspondente

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
10. Se houver múltiplas operações na mesma nota de corretagem, gerar exatamente 2 transações para cada operação.
11. Se a mesma nota de corretagem contiver múltiplas execuções do mesmo ativo, na mesma direção (`buy` ou `sell`), para a mesma instituição financeira e na mesma data, essas execuções devem ser consolidadas em uma única operação lógica antes de gerar o JSON.
12. Execuções parciais do mesmo ativo em preços diferentes não devem gerar operações separadas no JSON quando fizerem parte da mesma operação consolidável; nesse caso, deve-se somar as quantidades e somar os valores financeiros dessas execuções para gerar apenas 2 transações JSON da operação consolidada.
13. Não aplicar regras fora das descritas nesta skill.
14. Não escrever em planilhas nesta etapa.
15. Os valores de instituições financeiras devem usar apenas valores permitidos pela taxonomia da skill.
16. O nome do ativo pode ser extraído livremente da entrada do usuário, da nota de corretagem, da imagem, do PDF ou do texto enviado.
17. O campo `timestamp` deve usar o formato `DD-MM-YYYY`.
18. O campo `amount` deve ser sempre string numérica.
19. O campo `type` de compra é sempre `buy`.
20. O campo `type` de venda é sempre `sell`.

# Escopo desta versão
Esta versão cobre principalmente renda variável, mas a mesma lógica-base pode ser reutilizada depois para renda fixa.

Ativos típicos desta versão:
- ações
- ETFs
- FIIs
- BDRs
- outros ativos negociados em nota de corretagem com quantidade explícita

# Normalização
Aplique apenas normalização básica, quando possível:
- datas em `DD-MM-YYYY`
- valores monetários em formato textual decimal, por exemplo: `"4000.00"`
- quantidades em formato textual, por exemplo: `"100"` ou `"100.0000"` conforme a informação disponível
- nomes de ativos preservando o identificador encontrado, por exemplo: `PETR4`, `BOVA11`, `MXRF11`
- texto sem espaços supérfluos

# Estrutura de cada operação
Cada operação de compra ou venda deve ser expandida em exatamente 2 transações:

## 1) Transação financeira
Representa o dinheiro alocado ou desalocado.

## 2) Transação de quantidade
Representa a quantidade comprada ou vendida do ativo.

# Regras de transformação: compra
Quando a operação for uma compra:

## Primeira transação: dinheiro
- `from`: instituição financeira ou origem do dinheiro, obrigatoriamente usando um valor permitido pela taxonomia
- `to`: nome do ativo comprado
- `amount`: valor financeiro total da operação, já incluindo a parcela proporcional das taxas
- `type`: `buy`
- `timestamp`: data da operação
- `obs`: descrição resumida da compra

## Segunda transação: quantidade
- `from`: `qtde__bens`
- `to`: nome do ativo seguido de `_QTDE`
- `amount`: quantidade comprada
- `type`: `buy`
- `timestamp`: data da operação
- `obs`: descrição resumida da compra

## Exemplo de compra
Se houve compra de 100 PETR4 com montante total de 4000.00 saindo da Rico:

```json
{
  "transactions": [
    {
      "from": "rico",
      "to": "PETR4",
      "amount": "4000.00",
      "type": "buy",
      "timestamp": "08-08-2026",
      "obs": "Compra de 100 PETR4"
    },
    {
      "from": "qtde__bens",
      "to": "PETR4_QTDE",
      "amount": "100",
      "type": "buy",
      "timestamp": "08-08-2026",
      "obs": "Compra de 100 PETR4"
    }
  ]
}
```

# Regras de transformação: venda

Quando a operação for uma venda:

## Primeira transação: dinheiro

* `from`: nome do ativo vendido
* `to`: instituição financeira ou destino do dinheiro, obrigatoriamente usando um valor permitido pela taxonomia
* `amount`: valor financeiro líquido recebido na operação, já descontando a parcela proporcional das taxas
* `type`: `sell`
* `timestamp`: data da operação
* `obs`: descrição resumida da venda

## Segunda transação: quantidade

* `from`: nome do ativo seguido de `_QTDE`
* `to`: `qtde__bens`
* `amount`: quantidade vendida
* `type`: `sell`
* `timestamp`: data da operação
* `obs`: descrição resumida da venda

## Exemplo de venda

Se houve venda de 50 VALE3 com montante total de 2800.00 entrando na Rico:

```json
{
  "transactions": [
    {
      "from": "VALE3",
      "to": "rico",
      "amount": "2800.00",
      "type": "sell",
      "timestamp": "08-08-2026",
      "obs": "Venda de 50 VALE3"
    },
    {
      "from": "VALE3_QTDE",
      "to": "qtde__bens",
      "amount": "50",
      "type": "sell",
      "timestamp": "08-08-2026",
      "obs": "Venda de 50 VALE3"
    }
  ]
}
```

# Regras para taxa e montante financeiro

O valor financeiro da primeira transação de cada operação deve considerar também as taxas.

## Regra principal

1. O `amount` da transação financeira deve considerar a parcela proporcional das taxas associadas à nota.

2. Regra para compra:
   * o `amount` deve ser o valor da operação
   * mais a parcela proporcional das taxas
   * ou seja, na compra a taxa aumenta o valor desembolsado

3. Regra para venda:
   * o `amount` deve ser o valor da operação
   * menos a parcela proporcional das taxas
   * ou seja, na venda a taxa reduz o valor líquido recebido

4. Nunca ignorar taxas quando elas estiverem presentes ou puderem ser inferidas com segurança.

## Notas com múltiplas operações

Quando uma mesma nota de corretagem contiver mais de uma operação:

1. identificar todas as operações individualmente
2. calcular o valor financeiro base de cada operação
3. distribuir as taxas proporcionalmente ao valor de cada operação
4. aplicar a parcela proporcional de taxa ao valor da operação correspondente, da seguinte forma:
   * somar a taxa nas compras
   * subtrair a taxa nas vendas
5. usar esse valor final no campo `amount` da transação financeira de cada operação


# Validação do montante

A validação financeira é obrigatória.

## O que validar

1. a soma dos valores monetários das transações financeiras geradas no JSON
2. a compatibilidade dessa soma com o total esperado da nota, considerando taxas
3. a coerência entre:

   * ativo
   * quantidade
   * tipo da operação
   * instituição de origem ou destino
   * valor financeiro final


## Regra de fechamento financeiro obrigatório
Após consolidar as operações e distribuir as taxas, a soma dos `amount` das transações financeiras deve bater com o total monetário esperado da nota de corretagem.

Regras:
1. considerar apenas as transações financeiras em reais na soma de conferência
2. não incluir as transações de quantidade nessa soma
3. validar separadamente compras e vendas, quando a nota apresentar ambos os lados
4. se a nota tiver apenas vendas, a soma dos `amount` financeiros de venda deve bater com o total líquido recebido da nota, isto é, já descontadas as taxas
5. se a nota tiver apenas compras, a soma dos `amount` financeiros de compra deve bater com o total desembolsado da nota, isto é, já acrescido das taxas
6. se a nota tiver compras e vendas, cada lado deve fechar corretamente conforme os totais líquidos/desembolsados da nota
7. se houver diferença após a geração do JSON, revisar a consolidação das execuções, revisar a distribuição proporcional das taxas e gerar novamente
8. fazer no máximo 3 tentativas no total
9. se, após 3 tentativas, a soma continuar divergente, interromper o processo e reportar erro

## Regra de tentativas

Se a soma não bater:

1. revisar a extração dos valores
2. revisar a distribuição proporcional das taxas
3. regenerar o JSON
4. validar novamente

Fazer no máximo 3 tentativas no total.

Se, após 3 tentativas, o montante continuar inconsistente:

* relatar erro
* interromper o processo
* não retornar JSON incorreto

# Regras para múltiplas operações na mesma nota

Uma nota de corretagem pode conter várias compras e vendas.

Para cada operação identificada:

1. gerar exatamente 2 transações
2. manter o mesmo `timestamp` da operação ou da nota, conforme a evidência disponível
3. usar o ativo correto daquela operação
4. usar a quantidade correta daquela operação
5. usar o valor financeiro correto daquela operação já com taxas proporcionais


## Regra de consolidação obrigatória

Antes de gerar o JSON final, consolide execuções que pertençam à mesma operação lógica.

Considere como uma única operação lógica os lançamentos que, ao mesmo tempo:
- sejam do mesmo ativo
- tenham a mesma direção (`buy` ou `sell`)
- usem a mesma instituição financeira
- pertençam à mesma nota de corretagem
- tenham a mesma data operacional

Nesses casos:
1. somar a quantidade total executada do ativo
2. somar o valor financeiro total dessas execuções
3. tratar o resultado consolidado como uma única operação
4. gerar apenas 2 transações JSON para essa operação consolidada

Importante:
- preços diferentes de execução não significam, por si só, operações diferentes no JSON
- se houve, por exemplo, duas execuções de venda do mesmo ativo na mesma nota, elas devem virar apenas uma operação consolidada de venda no JSON
- a consolidação deve ocorrer antes da distribuição proporcional das taxas

## Exemplo conceitual

Se uma nota tiver:

* compra de PETR4
* compra de VALE3
* venda de BOVA11

então o JSON final deve conter:

* 2 transações para PETR4
* 2 transações para VALE3
* 2 transações para BOVA11

Total:

* 6 transações no array `transactions`

# Processo

1. Identifique os tipos de entrada disponíveis:

   * texto
   * imagem
   * PDF
   * áudio
2. Extraia os dados relevantes de cada entrada.
3. Combine os dados extraídos com o contexto do usuário.
4. Identifique todas as operações de compra e venda presentes na entrada.
5. Para cada operação, extraia:

   * instituição financeira
   * ativo
   * quantidade
   * valor financeiro bruto da operação
   * valor financeiro líquido/final da operação após aplicação proporcional das taxas
   * taxas
   * data
   * direção da operação: compra ou venda
6. Consolide execuções que pertençam à mesma operação lógica antes de gerar o JSON.
7. Para cada operação consolidada, gere exatamente 2 transações conforme as regras desta skill.
8. Se houver taxas compartilhadas em uma nota com múltiplas operações, distribua essas taxas proporcionalmente entre as operações consolidadas.
9. Monte a lista final `transactions`.
10. Valide a estrutura do JSON.
11. Valide a consistência financeira do montante total, inclusive o fechamento separado de compras e vendas quando aplicável.
12. Se a validação falhar, tente corrigir a consolidação, a distribuição das taxas e regenerar o JSON.
13. Faça no máximo 3 tentativas.
14. Se, após 3 tentativas, ainda houver inconsistência estrutural ou financeira, interrompa o processo e reporte erro.

# Exemplos
Consulte `references/examples.md` como exemplos canônicos de saída esperada antes de validar o JSON final.

# Casos especiais

* Se a nota estiver ilegível, não invente valores.
* Se o ativo não puder ser identificado com segurança, interrompa o processo e reporte erro.
* Se a instituição financeira não puder ser mapeada para um valor permitido pela taxonomia, interrompa o processo e reporte erro.
* Se a quantidade não puder ser identificada com segurança, interrompa o processo e reporte erro.
* Se as taxas existirem, mas não puderem ser distribuídas de forma consistente, interrompa o processo e reporte erro.
* Se houver informação parcial, use apenas o que puder ser extraído com segurança.
* Não gerar eventos de split, inplit, dividendos, JCP, proventos, bonificações ou amortizações nesta skill.

# Validação
Use o script abaixo para validar o JSON gerado:
- `python scripts/validate_json.py caminho/do/arquivo.json`

Se a validação ocorrer por stdin, também é aceitável:
- `cat caminho/do/arquivo.json | python scripts/validate_json.py`

Considere a validação bem-sucedida apenas quando o script indicar que o JSON é válido.

# Saída
* Retorne somente JSON válido, seguindo exatamente o schema definido em `references/schema.md`.
* Nunca retorne JSON inválido.
* Nunca retorne JSON com operação de compra ou venda contendo quantidade diferente de 2 transações por operação.
* Nunca retorne JSON cujo montante financeiro total não bata com a nota após as tentativas permitidas.
* Nunca retorne JSON em que múltiplas execuções do mesmo ativo, na mesma direção e na mesma nota, tenham sido lançadas como operações separadas quando deveriam ter sido consolidadas.
* Nunca retorne JSON cuja soma dos `amount` financeiros de compra e/ou venda divirja dos totais da nota após as tentativas permitidas.
* Nunca retorne JSON em que operações de venda tenham `amount` calculado com soma de taxas; em vendas, as taxas devem sempre ser descontadas do valor bruto da operação.
