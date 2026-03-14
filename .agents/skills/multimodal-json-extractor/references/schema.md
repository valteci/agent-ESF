# Schema de saída
- `from`, `to` e `type` devem usar apenas valores permitidos pela taxonomia definida em `references/taxonomy.md` e `assets/taxonomy.json`.

A saída final deve ser **somente um JSON válido** no formato abaixo:

```json
{
  "transactions": [
    {
      "from": "...",
      "to": "...",
      "amount": "...",
      "type": "...",
      "timestamp": "...",
      "obs": "..."
    }
  ]
}

