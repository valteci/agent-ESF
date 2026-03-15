# Exemplos

## Exemplo 1: compra com taxa em dinheiro

Entrada:
- contexto: "Comprei 0.50000000 BTC na binance."
- imagem/pdf: comprovante da binance com compra de 0.50000000 BTC por R$ 150000.00 e taxa em dinheiro de R$ 15.00.
- data detectada: 14-03-2026

Saída esperada:
```json
{
  "transactions": [
    {
      "from": "binance",
      "to": "BITCOIN",
      "amount": "150015.00",
      "type": "buy",
      "timestamp": "14-03-2026",
      "obs": "Compra de 0.50000000 BITCOIN na binance"
    },
    {
      "from": "qtde__bens",
      "to": "BITCOIN_QTDE",
      "amount": "0.50000000",
      "type": "buy",
      "timestamp": "14-03-2026",
      "obs": "Compra de 0.50000000 BITCOIN na binance"
    }
  ]
}
```

## Exemplo 2: compra com taxa descontada no proprio criptoativo

Entrada:
- contexto: "Comprei 1 BTC no mercado bitcoin e a taxa veio em BTC."
- imagem/pdf: comprovante do mercado bitcoin com compra de 1 BTC por R$ 500000.00 e taxa de 0.000001 BTC.
- data detectada: 14-03-2026

Saída esperada:
```json
{
  "transactions": [
    {
      "from": "mercado bitcoin",
      "to": "BITCOIN",
      "amount": "500000.00",
      "type": "buy",
      "timestamp": "14-03-2026",
      "obs": "Compra de 1 BITCOIN no mercado bitcoin com taxa em BITCOIN"
    },
    {
      "from": "qtde__bens",
      "to": "BITCOIN_QTDE",
      "amount": "0.999999",
      "type": "buy",
      "timestamp": "14-03-2026",
      "obs": "Compra liquida de 0.999999 BITCOIN no mercado bitcoin"
    }
  ]
}
```

## Exemplo 3: venda com taxa descontada no proprio criptoativo

Entrada:
- contexto: "Vendi 0.25000000 ETH na foxbit."
- imagem/pdf: comprovante da foxbit com venda de 0.25000000 ETH por R$ 2500.00 e taxa de 0.00050000 ETH.
- data detectada: 14-03-2026

Saída esperada:
```json
{
  "transactions": [
    {
      "from": "ETHEREUM",
      "to": "foxbit",
      "amount": "2500.00",
      "type": "sell",
      "timestamp": "14-03-2026",
      "obs": "Venda de 0.25000000 ETHEREUM na foxbit com taxa em ETHEREUM"
    },
    {
      "from": "ETHEREUM_QTDE",
      "to": "qtde__bens",
      "amount": "0.25050000",
      "type": "sell",
      "timestamp": "14-03-2026",
      "obs": "Saida total de 0.25050000 ETHEREUM na foxbit"
    }
  ]
}
```

## Exemplo 4: duas compras com taxa em dinheiro distribuida proporcionalmente

Entrada:
- contexto: "Comprei BTC e ETH na binance."
- imagem/pdf: documento da binance com compra de 0.10000000 BTC por R$ 30000.00 e compra de 2.00000000 ETH por R$ 20000.00. A taxa monetaria total foi de R$ 50.00.
- data detectada: 14-03-2026

Saída esperada:
```json
{
  "transactions": [
    {
      "from": "binance",
      "to": "BITCOIN",
      "amount": "30030.00",
      "type": "buy",
      "timestamp": "14-03-2026",
      "obs": "Compra de 0.10000000 BITCOIN na binance"
    },
    {
      "from": "qtde__bens",
      "to": "BITCOIN_QTDE",
      "amount": "0.10000000",
      "type": "buy",
      "timestamp": "14-03-2026",
      "obs": "Compra de 0.10000000 BITCOIN na binance"
    },
    {
      "from": "binance",
      "to": "ETHEREUM",
      "amount": "20020.00",
      "type": "buy",
      "timestamp": "14-03-2026",
      "obs": "Compra de 2.00000000 ETHEREUM na binance"
    },
    {
      "from": "qtde__bens",
      "to": "ETHEREUM_QTDE",
      "amount": "2.00000000",
      "type": "buy",
      "timestamp": "14-03-2026",
      "obs": "Compra de 2.00000000 ETHEREUM na binance"
    }
  ]
}
```

## Exemplo 5: consolidacao de multiplas execucoes do mesmo ativo

Entrada:
- contexto: "Comprei SOL na binance em duas execucoes na mesma ordem."
- imagem/pdf: trade history da binance com duas compras de SOL na mesma data e mesma direcao:
  - 4.50000000 SOL por R$ 450.00
  - 5.62500000 SOL por R$ 562.50
  A taxa total no proprio ativo foi de 0.01012500 SOL.
- data detectada: 14-03-2026

Saída esperada:
```json
{
  "transactions": [
    {
      "from": "binance",
      "to": "SOLANA",
      "amount": "1012.50",
      "type": "buy",
      "timestamp": "14-03-2026",
      "obs": "Compra consolidada de 10.12500000 SOLANA na binance"
    },
    {
      "from": "qtde__bens",
      "to": "SOLANA_QTDE",
      "amount": "10.11487500",
      "type": "buy",
      "timestamp": "14-03-2026",
      "obs": "Compra liquida consolidada de 10.11487500 SOLANA na binance"
    }
  ]
}
```
