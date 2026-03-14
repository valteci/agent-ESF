# Exemplos

## Exemplo 1: uma transação

Entrada:
- contexto: "Comprei um celular na amazon, o dinheiro saiu do banco itaú"
- imagem/pdf: nota fiscal com valor 2499.90
- data detectada: 14-03-2026

Saída esperada:
```json
{
  "transactions": [
    {
      "from": "itaú",
      "to": "amazon",
      "amount": "2499.90",
      "type": "compra",
      "timestamp": "14-03-2026",
      "obs": "Compra de celular na amazon"
    }
  ]
}
```

## Exemplo 2: uma transação

Entrada:
- contexto: "Comprei um salgado no shopping"
- imagem/pdf: print da transação de no valor de 10.00 no banco nubank
- data detectada: 14-03-2026

Saída esperada:
```json
{
  "transactions": [
    {
      "from": "nubank",
      "to": "shopping",
      "amount": "10.00",
      "type": "compra",
      "timestamp": "14-03-2026",
      "obs": "Compra de um salgado no shopping XYZ"
    }
  ]
}
```

## Exemplo 3: uma transação

Entrada:
- contexto: "Meu salário caiu na conta, trabalho no google"
- imagem/pdf: print da transação no valor de 2000.00 no mercado pago
- data detectada: 14-03-2026

Saída esperada:
```json
{
  "transactions": [
    {
      "from": "google",
      "to": "mercado pago",
      "amount": "2000.00",
      "type": "criação de dinheiro",
      "timestamp": "14-03-2026",
      "obs": "Meu salário do google"
    }
  ]
}
```

## Exemplo 3: nenhuma transação confiável

Entrada:
- contexto: "Paguei um multa por excesso de velocidade"
- imagem/pdf: print da multa com valor não identificado
- data detectada: 14-03-2026

Saída esperada:
```json
{
  "transactions": []
}
```
