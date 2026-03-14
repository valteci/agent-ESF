---
name: multimodal-json-extractor
description: Use esta skill quando a tarefa envolver receber texto, imagem, PDF ou áudio e converter o conteúdo em um JSON padronizado de transações, usando também o contexto fornecido pelo usuário.
---

# Objetivo
Transformar entradas multimodais em um JSON estruturado no formato definido em `references/schema.md`, contendo uma lista de transações na chave `transactions`.

# Quando usar
Use esta skill quando o usuário:
- enviar texto com dados para extrair
- enviar uma imagem, print ou foto com informações relevantes
- enviar um PDF como nota fiscal, recibo ou nota de corretagem
- enviar áudio com contexto ou dados
- combinar arquivo + contexto textual, por exemplo:
  "comprei um celular, está aí a nota fiscal"

# Regras gerais
1. Sempre considerar o contexto enviado pelo usuário junto com os arquivos.
2. A saída final deve ser somente JSON válido, sem texto antes ou depois.
3. O JSON deve seguir exatamente o formato definido em `references/schema.md`.
4. O objeto raiz deve conter sempre a chave `transactions`.
5. `transactions` deve ser sempre uma lista, mesmo quando estiver vazia.
6. Cada item de `transactions` deve ser um objeto com exatamente estas chaves:
   - `from`
   - `to`
   - `amount`
   - `type`
   - `timestamp`
   - `obs`
7. Não adicionar chaves extras fora do schema.
8. Todos os valores de cada transação devem ser strings.
9. Quando um campo não puder ser determinado com segurança, preencher com string vazia `""`.
10. Quando múltiplas transações forem detectadas, incluir múltiplos objetos dentro de `transactions`.
11. Não aplicar regras de negócio nesta etapa.
12. Não escrever em planilhas nesta etapa.
13. Após gerar o JSON, validar obrigatoriamente o resultado usando o script `scripts/validate_json.py`.
14. Se o JSON for inválido, tentar gerá-lo novamente, corrigindo os erros apontados pelo validador.
15. O número máximo de tentativas de geração e validação é 3.
16. Se, após 3 tentativas, o JSON continuar inválido, interromper o processo e informar falha de validação em vez de retornar um JSON inválido.

# Normalização
Aplique apenas normalização básica, quando possível:
- datas em `DD-MM-YYYY`
- valores monetários em formato textual decimal, por exemplo: `"150.90"`
- texto sem espaços supérfluos


# Regras de classificação
1. Os campos `from`, `to` e `type` devem usar somente valores permitidos pela taxonomia do projeto.
2. Consulte `references/taxonomy.md` para entender a semântica de cada valor.
3. Consulte `assets/taxonomy.json` como fonte canônica dos valores permitidos.
4. Não invente novos valores para `from`, `to` ou `type`.
5. Quando a entrada for ambígua e não permitir classificar com segurança, interrompa o processo ou sinalize falha, em vez de inventar categoria.


# Processo
1. Identifique os tipos de entrada disponíveis:
   - texto
   - imagem
   - PDF
   - áudio
2. Extraia os dados relevantes de cada entrada.
3. Combine os dados extraídos com o contexto do usuário.
4. Identifique quantas transações podem ser formadas a partir da entrada.
5. Monte a lista `transactions` conforme o formato definido em `references/schema.md`.
6. Valide o JSON gerado com o script `scripts/validate_json.py`.
7. Se o validador retornar que o JSON é inválido:
   - analise os erros retornados pelo script
   - corrija o JSON
   - gere novamente o JSON
   - valide de novo
8. Repita o ciclo de geração + validação até no máximo 3 tentativas no total.
9. Antes de responder, confira:
   - o JSON está válido
   - o objeto raiz contém `transactions`
   - `transactions` é uma lista
   - cada transação contém exatamente os campos exigidos
   - todos os valores são strings
   - campos incertos foram preenchidos com `""`
10. Se nenhuma transação puder ser extraída com segurança, retornar:
   ```json
   {
     "transactions": []
   }
   ```
11. Se, após 3 tentativas, o JSON continuar inválido, interromper o processo e reportar falha de validação em vez de inventar ou retornar um JSON fora do schema.

# Casos especiais
- Se o áudio trouxer contexto e o documento trouxer os valores, combine os dois.
- Se a imagem ou PDF estiver ilegível, extraia apenas o que for possível com segurança.
- Se houver conflito entre contexto e documento, priorize o documento para preencher os campos.
- Se houver informação parcial, preencha os campos conhecidos e use "" nos demais.
- Se a entrada multimodal contiver mais de uma transação, gere um objeto para cada uma dentro de transactions.

# Exemplos
Consulte `references/examples.md` e os arquivos em `assets/examples/` como exemplos canônicos de saída esperada antes de validar o JSON final.

# Validação
Use o script abaixo para validar o JSON gerado:
- `python scripts/validate_json.py caminho/do/arquivo.json`

Se a validação ocorrer por stdin, também é aceitável:
- `cat caminho/do/arquivo.json | python scripts/validate_json.py`

Considere a validação bem-sucedida apenas quando o script indicar que o JSON é válido.

# Saída
Retorne somente JSON válido, seguindo exatamente o schema definido em references/schema.md.
Nunca retorne JSON inválido.