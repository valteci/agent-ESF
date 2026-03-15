# Schema de saída
- `from` e `to` devem usar apenas valores permitidos pela taxonomia definida em `references/taxonomy.md` e `assets/taxonomy.json` quando se referirem a conta, banco, corretora ou exchange.
- Quando `from` ou `to` representarem o criptoativo negociado, usar sempre o nome completo em caixa alta, nunca ticker abreviado.
- O campo de quantidade deve seguir o padrão `NOME COMPLETO_QTDE`.

A saída final deve ser **somente um JSON válido** nos formatos abaixo:

* Em caso de compra:
```json
{
  "transactions": [
    {
      "from": "instituicao ou exchange",
      "to": "NOME COMPLETO DO CRIPTOATIVO",
      "amount": "...",
      "type": "buy",
      "timestamp": "...",
      "obs": "..."
    },
    {
      "from": "qtde__bens",
      "to": "NOME COMPLETO DO CRIPTOATIVO_QTDE",
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
      "from": "NOME COMPLETO DO CRIPTOATIVO",
      "to": "instituicao ou exchange",
      "amount": "...",
      "type": "sell",
      "timestamp": "...",
      "obs": "..."
    },
    {
      "from": "NOME COMPLETO DO CRIPTOATIVO_QTDE",
      "to": "qtde__bens",
      "amount": "...",
      "type": "sell",
      "timestamp": "...",
      "obs": "..."
    }
  ]
}
```
