# Exemplos

## Exemplo 1: dividendo de acao

Entrada:
- contexto: "Recebi R$ 10 de dividendos de ITUB4 na rico."
- data detectada: 15-03-2026

Saida esperada:
```json
{
  "transactions": [
    {
      "from": "ITUB4_yeld",
      "to": "rico",
      "amount": "10.00",
      "type": "create batch",
      "timestamp": "15-03-2026",
      "obs": "Recebimento de dividendos de ITUB4 na rico"
    }
  ]
}
```

## Exemplo 2: rendimento de FII

Entrada:
- contexto: "Recebi R$ 125,43 de rendimento do MXRF11 no nubank."
- data detectada: 15-03-2026

Saida esperada:
```json
{
  "transactions": [
    {
      "from": "MXRF11_yeld",
      "to": "nubank",
      "amount": "125.43",
      "type": "create batch",
      "timestamp": "15-03-2026",
      "obs": "Recebimento de rendimento de MXRF11 no nubank"
    }
  ]
}
```

## Exemplo 3: staking de cripto

Entrada:
- contexto: "Recebi 0.01500000 ETH de staking na binance."
- data detectada: 15-03-2026

Saida esperada:
```json
{
  "transactions": [
    {
      "from": "qtde__bens",
      "to": "ETHEREUM_QTDE",
      "amount": "0.01500000",
      "type": "buy",
      "timestamp": "15-03-2026",
      "obs": "Recebimento de recompensa de staking em ETHEREUM"
    }
  ]
}
```

## Exemplo 4: bonificacao

Entrada:
- contexto: "Recebi 12 acoes de bonificacao de ITSA4."
- data detectada: 15-03-2026

Saida esperada:
```json
{
  "transactions": [
    {
      "from": "qtde__bens",
      "to": "ITSA4_QTDE",
      "amount": "12",
      "type": "buy",
      "timestamp": "15-03-2026",
      "obs": "Bonificacao de 12 acoes de ITSA4"
    }
  ]
}
```

## Exemplo 5: split

Entrada:
- contexto: "Eu tinha 100 cotas de BOVA11 e, depois do desdobramento, fiquei com 200."
- data detectada: 15-03-2026

Saida esperada:
```json
{
  "transactions": [
    {
      "from": "qtde__bens",
      "to": "BOVA11_QTDE",
      "amount": "100",
      "type": "buy",
      "timestamp": "15-03-2026",
      "obs": "Desdobramento de BOVA11 com acrescimo de 100 cotas"
    }
  ]
}
```

## Exemplo 6: inplit

Entrada:
- contexto: "Eu tinha 500 acoes de OIBR3, aconteceu um agrupamento e agora fiquei com 100."
- data detectada: 15-03-2026

Saida esperada:
```json
{
  "transactions": [
    {
      "from": "OIBR3_QTDE",
      "to": "qtde__bens",
      "amount": "400",
      "type": "sell",
      "timestamp": "15-03-2026",
      "obs": "Agrupamento de OIBR3 com reducao de 400 acoes"
    }
  ]
}
```

## Exemplo 7: ajuste manual para aumentar quantidade

Entrada:
- contexto: "Ajuste minha quantidade de SOL em 0.50000000 para mais."
- data detectada: 15-03-2026

Saida esperada:
```json
{
  "transactions": [
    {
      "from": "qtde__bens",
      "to": "SOLANA_QTDE",
      "amount": "0.50000000",
      "type": "buy",
      "timestamp": "15-03-2026",
      "obs": "Ajuste manual com acrescimo de 0.50000000 SOLANA"
    }
  ]
}
```

## Exemplo 8: ajuste manual para diminuir quantidade

Entrada:
- contexto: "Quero reduzir minha quantidade de PETR4 em 10 acoes."
- data detectada: 15-03-2026

Saida esperada:
```json
{
  "transactions": [
    {
      "from": "PETR4_QTDE",
      "to": "qtde__bens",
      "amount": "10",
      "type": "sell",
      "timestamp": "15-03-2026",
      "obs": "Ajuste manual com reducao de 10 acoes de PETR4"
    }
  ]
}
```
