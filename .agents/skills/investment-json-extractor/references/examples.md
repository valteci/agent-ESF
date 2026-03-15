# Exemplos

## Exemplo 1: compra

Entrada:
- contexto: "Compra de 200 Ações de ITUB4 na corretora rico."
- imagem/pdf: nota de corretagem da rico, com 200 ações de ITUB4, com valor da operação de R$ 8000 e uma taxa total de R$ 2.
- data detectada: 14-03-2026

Saída esperada:
```json
{
  "transactions": [
    {
      "from": "rico",
      "to": "ITUB4",
      "amount": "8002.00",
      "type": "buy",
      "timestamp": "14-03-2026",
      "obs": "Compra de 200 ITUB4 na rico"
    },
    {
      "from": "qtde__bens",
      "to": "ITUB4_QTDE",
      "amount": "200",
      "type": "buy",
      "timestamp": "14-03-2026",
      "obs": "Compra de 200 ITUB4 na rico"
    }
  ]
}
```

## Exemplo 2: venda

Entrada:

* contexto: "Venda de 10 Ações de VALE3 na corretora xp."
* imagem/pdf: nota de corretagem da xp, com 10 ações de VALE3, com valor da operação de R$ 700 e uma taxa total de R$ 1.
* data detectada: 14-03-2026

Saída esperada:

```json
{
  "transactions": [
    {
      "from": "VALE3",
      "to": "xp",
      "amount": "699.00",
      "type": "sell",
      "timestamp": "14-03-2026",
      "obs": "Venda de 10 ações da VALE3 na xp"
    },
    {
      "from": "VALE3_QTDE",
      "to": "qtde__bens",
      "amount": "10",
      "type": "sell",
      "timestamp": "14-03-2026",
      "obs": "Venda de 10 ações da VALE3 na xp"
    }
  ]
}
```

## Exemplo 3: 2 compras

Entrada:

* contexto: "Compra de 200 Ações de ITUB4. Compra 50 cotas do ETF PKIN11. Tudo na rico."
* imagem/pdf: nota de corretagem da rico, com 200 ações de ITUB4, com valor da operação de R$ 8000 e com 50 cotas do ETF PKIN11, com valor da operação de R$ 4000. A taxa total foi de R$ 6.
* data detectada: 14-03-2026

Saída esperada:

```json
{
  "transactions": [
    {
      "from": "rico",
      "to": "ITUB4",
      "amount": "8004.00",
      "type": "buy",
      "timestamp": "14-03-2026",
      "obs": "Compra de 200 ITUB4 na rico"
    },
    {
      "from": "qtde__bens",
      "to": "ITUB4_QTDE",
      "amount": "200",
      "type": "buy",
      "timestamp": "14-03-2026",
      "obs": "Compra de 200 ITUB4 na rico"
    },
    {
      "from": "rico",
      "to": "PKIN11",
      "amount": "4002.00",
      "type": "buy",
      "timestamp": "14-03-2026",
      "obs": "Compra de 50 PKIN11 na rico"
    },
    {
      "from": "qtde__bens",
      "to": "PKIN11_QTDE",
      "amount": "50",
      "type": "buy",
      "timestamp": "14-03-2026",
      "obs": "Compra de 50 PKIN11 na rico"
    }
  ]
}
```

## Exemplo 4: 2 vendas

Entrada:

* contexto: "Venda de 20 cotas de BOVA11 e venda de 30 ações de PETR4. Tudo na rico."
* imagem/pdf: nota de corretagem da rico, com venda de 20 cotas de BOVA11 no valor de R$ 2400 e venda de 30 ações de PETR4 no valor de R$ 900. A taxa total foi de R$ 3.
* data detectada: 14-03-2026

Saída esperada:

```json
{
  "transactions": [
    {
      "from": "BOVA11",
      "to": "rico",
      "amount": "2397.82",
      "type": "sell",
      "timestamp": "14-03-2026",
      "obs": "Venda de 20 BOVA11 na rico"
    },
    {
      "from": "BOVA11_QTDE",
      "to": "qtde__bens",
      "amount": "20",
      "type": "sell",
      "timestamp": "14-03-2026",
      "obs": "Venda de 20 BOVA11 na rico"
    },
    {
      "from": "PETR4",
      "to": "rico",
      "amount": "899.18",
      "type": "sell",
      "timestamp": "14-03-2026",
      "obs": "Venda de 30 PETR4 na rico"
    },
    {
      "from": "PETR4_QTDE",
      "to": "qtde__bens",
      "amount": "30",
      "type": "sell",
      "timestamp": "14-03-2026",
      "obs": "Venda de 30 PETR4 na rico"
    }
  ]
}
```

## Exemplo 5: 1 compra e 1 venda

Entrada:

* contexto: "Compra de 100 ações de BBAS3 e venda de 50 ações de VALE3. Tudo na rico."
* imagem/pdf: nota de corretagem da rico, com compra de 100 ações de BBAS3 no valor de R$ 3000 e venda de 50 ações de VALE3 no valor de R$ 2500. A taxa total foi de R$ 5.
* data detectada: 14-03-2026

Saída esperada:

```json
{
  "transactions": [
    {
      "from": "rico",
      "to": "BBAS3",
      "amount": "3002.73",
      "type": "buy",
      "timestamp": "14-03-2026",
      "obs": "Compra de 100 BBAS3 na rico"
    },
    {
      "from": "qtde__bens",
      "to": "BBAS3_QTDE",
      "amount": "100",
      "type": "buy",
      "timestamp": "14-03-2026",
      "obs": "Compra de 100 BBAS3 na rico"
    },
    {
      "from": "VALE3",
      "to": "rico",
      "amount": "2497.73",
      "type": "sell",
      "timestamp": "14-03-2026",
      "obs": "Venda de 50 VALE3 na rico"
    },
    {
      "from": "VALE3_QTDE",
      "to": "qtde__bens",
      "amount": "50",
      "type": "sell",
      "timestamp": "14-03-2026",
      "obs": "Venda de 50 VALE3 na rico"
    }
  ]
}
```
