# Schema de saída
- `from`, `to` devem usar apenas valores permitidos pela taxonomia definida em `references/taxonomy.md` e `assets/taxonomy.json`, quando se refirirem de onde o dinheiro está saindo ou entrando (não se aplica quando `to` ou `from` forem ativos).

A saída final deve ser **somente um JSON válido** nos formatos abaixo:
* Em caso de compra:
```json
{
  "transactions": [
    {
      "from": "instituicao X",
      "to": "ATIVO X",
      "amount": "...",
      "type": "buy",
      "timestamp": "...",
      "obs": "..."
    },
    {
      "from": "qtde__bens",
      "to": "ATIVO X_QTDE",
      "amount": "...",
      "type": "buy",
      "timestamp": "...",
      "obs": "..."
    }
  ]
}
```

* Em caso de venda:
```json
{
  "transactions": [
    {
      "from": "ATIVO X",
      "to": "instituicao X",
      "amount": "...",
      "type": "sell",
      "timestamp": "...",
      "obs": "..."
    },
    {
      "from": "ATIVO X_QTDE",
      "to": "qtde__bens",
      "amount": "...",
      "type": "sell",
      "timestamp": "...",
      "obs": "..."
    }
  ]
}
```
