# Schema de saida
- Quando `from` ou `to` representarem conta, banco, corretora ou exchange, usar apenas valores permitidos pela taxonomia definida em `references/taxonomy.md` e `assets/taxonomy.json`.
- Quando `from` ou `to` representarem o ativo:
  - para provento monetario em reais, usar `ATIVO_yeld` no campo `from`
  - para quantidade, usar `ATIVO_QTDE`
  - para criptoativos, usar sempre o nome completo em caixa alta

A saida final deve ser **somente um JSON valido** nos formatos abaixo:

* Em caso de provento monetario em reais:
```json
{
  "transactions": [
    {
      "from": "ATIVO_yeld",
      "to": "instituicao",
      "amount": "...",
      "type": "create batch",
      "timestamp": "...",
      "obs": "..."
    }
  ]
}
```

* Em caso de aumento de quantidade:
```json
{
  "transactions": [
    {
      "from": "qtde__bens",
      "to": "ATIVO_QTDE",
      "amount": "...",
      "type": "buy",
      "timestamp": "...",
      "obs": "..."
    }
  ]
}
```

* Em caso de reducao de quantidade:
```json
{
  "transactions": [
    {
      "from": "ATIVO_QTDE",
      "to": "qtde__bens",
      "amount": "...",
      "type": "sell",
      "timestamp": "...",
      "obs": "..."
    }
  ]
}
```
