# Objetivo do projeto

Este projeto usa o Codex para processar entradas multimodais do usuário e convertê-las em transações financeiras estruturadas para uma base de dados estilo livro-razão.

Cada transação representa uma movimentação financeira e deve seguir este modelo conceitual:

- `from`: origem de onde saiu o dinheiro
- `to`: destino para onde o dinheiro foi enviado
- `amount`: quantidade de dinheiro transferida de `from` para `to`
- `type`: tipo da transação
- `timestamp`: data da transação
- `obs`: observações e detalhamento da transação

# Instruções gerais

- Quando a tarefa envolver texto, imagem, PDF ou áudio contendo dados de movimentações financeiras, usar a skill `multimodal-json-extractor`.
- O objetivo nesta etapa é somente gerar a saída estruturada em JSON.
- Nesta etapa, não aplicar regras de negócio adicionais.
- Nesta etapa, não escrever em planilhas nem persistir dados em banco.
- Sempre considerar o contexto textual fornecido pelo usuário junto com os arquivos enviados.
- A saída final deve seguir exatamente o formato definido pela skill e por `references/schema.md`.
- Antes de concluir, validar o JSON gerado com o script `scripts/validate_json.py`, conforme definido na própria skill.
- Se a validação falhar, tentar regenerar o JSON dentro do limite de tentativas definido na skill.
- Nunca retornar JSON inválido.
