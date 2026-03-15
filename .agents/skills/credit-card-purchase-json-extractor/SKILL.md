---
name: credit-card-purchase-json-extractor
description: "Use esta skill quando a tarefa envolver compras do dia a dia feitas com cartao de credito ou pagamento de fatura de cartao de credito, extraidos de texto, imagem, PDF ou audio, e a saida precisar ser um JSON ledger usando buckets de garantia no formato garantia=>cartao."
---

# Objetivo
Transformar compras feitas no cartao de credito e pagamentos de fatura de cartao de credito em JSON estruturado no mesmo schema da `multimodal-json-extractor`.

Nesta skill, cada compra no credito gera exatamente 2 transacoes JSON:
1. transacao normal da despesa, como se o dinheiro saisse da instituicao escolhida como garantia
2. transacao de travamento da garantia, para registrar o compromisso com a instituicao do cartao

Nesta skill, cada pagamento de fatura gera 1 ou mais transacoes JSON:
1. uma transacao `transfer` para cada bucket de garantia usado no pagamento

Esta skill cobre:
- compras no cartao de credito
- pagamento de fatura de cartao de credito com uma ou mais garantias

Nao cobre compras no debito, pix, boleto, dinheiro fisico, antecipacao de fatura, juros, parcelamento de fatura, saque no credito nem emprestimo.

# Dependencias obrigatorias
Antes de gerar o JSON final, leia e aplique tambem:
- `../multimodal-json-extractor/SKILL.md`
- `../multimodal-json-extractor/references/schema.md`
- `../multimodal-json-extractor/references/taxanomy.md`
- `../multimodal-json-extractor/references/examples.md`
- `../multimodal-json-extractor/scripts/validate_json.py`

Todas as regras da `multimodal-json-extractor` continuam valendo, exceto quando esta skill sobrescrever explicitamente alguma delas.

# Quando usar
Use esta skill quando o usuario:
- informar que a compra foi feita no credito
- informar que pagou a fatura de um cartao de credito
- enviar texto, imagem, print, PDF ou audio de compra feita no cartao de credito
- enviar texto, imagem, print, PDF ou audio de pagamento de fatura
- pedir um JSON ledger para uma compra feita no cartao ou para um pagamento de fatura
- informar qual foi a instituicao do cartao e de qual instituicao deve sair a garantia
- informar que uma mesma fatura foi paga com mais de uma garantia

Se a movimentacao nao for compra no credito nem pagamento de fatura, use a skill multimodal apropriada em vez desta.

# Dados obrigatorios por compra
Cada compra no credito precisa de todos os dados abaixo:
- categoria economica da despesa, seguindo a taxonomia da `multimodal-json-extractor`
- valor da compra
- data da compra
- instituicao do cartao de credito
- instituicao de garantia

# Dados obrigatorios por pagamento de fatura
Cada pagamento de fatura precisa de todos os dados abaixo:
- instituicao do cartao de credito
- data do pagamento
- uma ou mais garantias usadas no pagamento
- valor usado em cada garantia

Se o usuario informar o valor total da fatura, a soma das garantias usadas no pagamento deve bater com esse total.

Definicoes:
- instituicao do cartao: conta, banco, fintech ou carteira a que o cartao de credito esta vinculado
- instituicao de garantia: conta, banco, fintech ou carteira de onde o dinheiro sera travado para garantir o pagamento futuro
- bucket de garantia: notacao especial no formato `<garantia>=><cartao>`
- bucket de pagamento da fatura: usar exatamente `cartao credito`

A instituicao de garantia pode ser diferente da instituicao do cartao.

Se a instituicao do cartao ou a instituicao de garantia nao puderem ser determinadas com seguranca, interrompa o processo ou peca esclarecimento ao usuario. Nao invente esses campos.

# Regras gerais desta skill
1. A saida final deve ser somente JSON valido, sem texto antes ou depois.
2. O JSON deve seguir exatamente o schema usado pela `multimodal-json-extractor`.
3. O objeto raiz deve conter sempre a chave `transactions`.
4. `transactions` deve ser sempre uma lista.
5. Cada compra no credito deve gerar exatamente 2 transacoes JSON, nem mais, nem menos.
6. Cada pagamento de fatura deve gerar exatamente 1 transacao por garantia usada no pagamento.
7. Se houver multiplas compras no credito na mesma entrada, gerar exatamente 2 transacoes para cada compra identificada.
8. Se houver multiplos pagamentos de fatura na mesma entrada, gerar 1 ou mais transacoes para cada pagamento, conforme a quantidade de garantias usadas.
9. Se uma mesma fatura for paga por mais de uma garantia, nao consolidar essas garantias em uma so transacao.
10. Todos os valores devem ser strings.
11. O campo `timestamp` deve usar `DD-MM-YYYY`.
12. O campo `amount` deve ser string numerica.
13. O campo `type` da primeira transacao de compra no credito e sempre `pay`.
14. O campo `type` da segunda transacao de compra no credito e sempre `transfer`.
15. O campo `type` de cada transacao de pagamento de fatura e sempre `transfer`.
16. A categoria economica da despesa deve seguir a mesma classificacao usada na `multimodal-json-extractor`.
17. Esta skill estende o uso de `from` e `to` para permitir os buckets especiais de garantia descritos abaixo.
18. No pagamento da fatura, o dinheiro deve sair do bucket de garantia e ir para `cartao credito`.
19. Quando o valor total da fatura for informado explicitamente, a soma das transacoes de pagamento deve bater com esse total.

# Estrutura de cada compra no credito
Cada compra no credito deve ser expandida em exatamente 2 transacoes:

## 1) Transacao normal da despesa
Representa a compra como se o dinheiro saisse da instituicao escolhida como garantia.

- `from`: instituicao de garantia
- `to`: categoria economica da compra, conforme a taxonomia da `multimodal-json-extractor`
- `amount`: valor total da compra
- `type`: `pay`
- `timestamp`: data da compra
- `obs`: descricao resumida da compra, deixando claro que foi no credito, qual cartao foi usado e qual instituicao foi usada como garantia

## 2) Transacao de travamento da garantia
Representa o compromisso da compra no credito.

- `from`: exatamente o mesmo valor usado no campo `to` da primeira transacao
- `to`: bucket especial no formato `<instituicao de garantia>=><instituicao do cartao>`
- `amount`: exatamente o mesmo valor da primeira transacao
- `type`: `transfer`
- `timestamp`: exatamente a mesma data da primeira transacao
- `obs`: descricao resumida do travamento da garantia para pagar o cartao

Regras do bucket especial:
1. Use exatamente a notacao `<garantia>=><cartao>`.
2. Nao adicione espacos extras ao redor de `=>`.
3. Use as instituicoes ja normalizadas para o JSON final.
4. Se a garantia e o cartao forem da mesma instituicao, ainda assim gere o bucket, por exemplo `mercado pago=>mercado pago`.

# Estrutura de cada pagamento de fatura
Cada pagamento de fatura deve ser expandido em 1 ou mais transacoes, uma por garantia usada no pagamento.

## 1) Transacao de pagamento da fatura
Representa a liberacao do dinheiro travado para quitar parte ou a totalidade da fatura.

- `from`: bucket especial no formato `<instituicao de garantia>=><instituicao do cartao>`
- `to`: `cartao credito`
- `amount`: valor pago com aquela garantia
- `type`: `transfer`
- `timestamp`: data do pagamento da fatura
- `obs`: descricao resumida do pagamento da fatura, deixando claro qual cartao foi pago e qual garantia foi consumida

Regras especificas do pagamento:
1. Gere uma transacao separada para cada garantia usada no pagamento.
2. Nao troque a direcao: o valor sai de `<garantia>=><cartao>` e vai para `cartao credito`.
3. Se o usuario informar o total da fatura e tambem o rateio por garantia, valide se a soma dos valores por garantia bate com o total.
4. Se a soma nao bater, revise a extracao e nao invente ajuste silencioso.
5. Se o usuario disser apenas que pagou a fatura, mas nao informar quanto saiu de cada garantia e isso nao puder ser inferido com seguranca, interrompa o processo ou peca esclarecimento.

# Regras de transformacao
## Compras no credito
Para cada compra no credito identificada:

1. Classifique a despesa exatamente como faria na `multimodal-json-extractor`.
2. Identifique a instituicao do cartao.
3. Identifique a instituicao de garantia.
4. Gere a primeira transacao como uma despesa normal usando a instituicao de garantia em `from`.
5. Gere a segunda transacao reutilizando o `to` da primeira transacao em `from`.
6. Monte o `to` da segunda transacao no formato `<garantia>=><cartao>`.
7. Repita o mesmo `amount` e `timestamp` nas duas transacoes.
8. Use `type` igual a `pay` na primeira transacao e `transfer` na segunda.

## Pagamentos de fatura
Para cada pagamento de fatura identificado:

1. Identifique a instituicao do cartao.
2. Identifique a data do pagamento.
3. Identifique cada instituicao de garantia usada no pagamento.
4. Identifique o valor pago por cada garantia.
5. Para cada garantia identificada, gere 1 transacao com:
   - `from`: `<garantia>=><cartao>`
   - `to`: `cartao credito`
   - `amount`: valor pago por aquela garantia
   - `type`: `transfer`
   - `timestamp`: data do pagamento
6. Se o valor total da fatura estiver explicito, confira se a soma das transacoes geradas bate com esse total antes de finalizar.

# Exemplos

## Exemplo 1: salgado no credito
Se o usuario comprou um salgado com o cartao do nubank e quer usar o mercado pago como garantia:

```json
{
  "transactions": [
    {
      "from": "mercado pago",
      "to": "comida",
      "amount": "10.00",
      "type": "pay",
      "timestamp": "14-03-2026",
      "obs": "Compra de salgado no credito com cartao nubank e garantia no mercado pago"
    },
    {
      "from": "comida",
      "to": "mercado pago=>nubank",
      "amount": "10.00",
      "type": "transfer",
      "timestamp": "14-03-2026",
      "obs": "Travamento de garantia no mercado pago para compra no cartao nubank"
    }
  ]
}
```

## Exemplo 2: roupa no credito
Se o usuario comprou uma roupa de 200.00 com o cartao do itau e quer usar o nubank como garantia:

```json
{
  "transactions": [
    {
      "from": "nubank",
      "to": "compras",
      "amount": "200.00",
      "type": "pay",
      "timestamp": "14-03-2026",
      "obs": "Compra de roupa no credito com cartao itau e garantia no nubank"
    },
    {
      "from": "compras",
      "to": "nubank=>itau",
      "amount": "200.00",
      "type": "transfer",
      "timestamp": "14-03-2026",
      "obs": "Travamento de garantia no nubank para compra no cartao itau"
    }
  ]
}
```

## Exemplo 3: mesma instituicao para garantia e cartao
Se o usuario usou o cartao do mercado pago e a garantia tambem vem do mercado pago:

```json
{
  "transactions": [
    {
      "from": "mercado pago",
      "to": "compras",
      "amount": "50.00",
      "type": "pay",
      "timestamp": "14-03-2026",
      "obs": "Compra no credito com cartao mercado pago e garantia no mercado pago"
    },
    {
      "from": "compras",
      "to": "mercado pago=>mercado pago",
      "amount": "50.00",
      "type": "transfer",
      "timestamp": "14-03-2026",
      "obs": "Travamento de garantia no mercado pago para compra no cartao mercado pago"
    }
  ]
}
```

## Exemplo 4: pagamento de fatura com uma garantia
Se o usuario pagou 300.00 da fatura do cartao do nubank usando apenas a garantia do mercado pago:

```json
{
  "transactions": [
    {
      "from": "mercado pago=>nubank",
      "to": "cartao credito",
      "amount": "300.00",
      "type": "transfer",
      "timestamp": "14-03-2026",
      "obs": "Pagamento da fatura do cartao nubank usando garantia do mercado pago"
    }
  ]
}
```

## Exemplo 5: pagamento de fatura com multiplas garantias
Se o usuario pagou 1000.00 da fatura do cartao do nubank usando 400.00 do mercado pago e 600.00 do 99pay:

```json
{
  "transactions": [
    {
      "from": "mercado pago=>nubank",
      "to": "cartao credito",
      "amount": "400.00",
      "type": "transfer",
      "timestamp": "14-03-2026",
      "obs": "Pagamento parcial da fatura do cartao nubank usando garantia do mercado pago"
    },
    {
      "from": "99pay=>nubank",
      "to": "cartao credito",
      "amount": "600.00",
      "type": "transfer",
      "timestamp": "14-03-2026",
      "obs": "Pagamento parcial da fatura do cartao nubank usando garantia do 99pay"
    }
  ]
}
```

# Processo
1. Extraia os dados da entrada multimodal usando o mesmo fluxo base da `multimodal-json-extractor`.
2. Classifique cada evento desta skill como:
   - compra no cartao de credito
   - pagamento de fatura de cartao
3. Para cada compra, identifique:
   - categoria economica
   - valor
   - data
   - instituicao do cartao
   - instituicao de garantia
4. Para cada pagamento de fatura, identifique:
   - instituicao do cartao
   - data do pagamento
   - garantias usadas
   - valor pago por garantia
   - total da fatura, quando explicitamente informado
5. Se faltar instituicao do cartao ou algum valor critico de garantia, interrompa o processo ou peca esclarecimento.
6. Gere exatamente 2 transacoes por compra e 1 transacao por garantia usada em cada pagamento de fatura.
7. Se houver total da fatura informado, valide se a soma dos pagamentos por garantia fecha esse total.
8. Valide o JSON com `../multimodal-json-extractor/scripts/validate_json.py`.
9. Se a validacao falhar, corrija e tente novamente.
10. O numero maximo de tentativas de geracao + validacao e 3.
11. Se nao houver nenhuma compra no credito nem nenhum pagamento de fatura com dados suficientes, retorne:

```json
{
  "transactions": []
}
```

# Validacao
Use o mesmo validador estrutural da `multimodal-json-extractor`:
- `python ../multimodal-json-extractor/scripts/validate_json.py caminho/do/arquivo.json`

Se a validacao ocorrer por stdin, tambem e aceitavel:
- `cat caminho/do/arquivo.json | python ../multimodal-json-extractor/scripts/validate_json.py`

Considere a validacao bem-sucedida apenas quando o script indicar que o JSON e valido.

# Saida
Retorne somente JSON valido, seguindo exatamente o mesmo schema da `multimodal-json-extractor`.
Nunca retorne JSON invalido.
