---
name: asset-events-json-extractor
description: Use esta skill quando a tarefa envolver proventos, rendimentos, bonificações, split, inplit, staking, lending ou ajuste manual de quantidade de ativos da bolsa brasileira ou criptoativos, e a saída precisar ser um JSON de transações contábeis no formato ledger.
---

# Objetivo
Transformar entradas multimodais relacionadas a proventos, eventos corporativos simples e ajustes de quantidade em JSON estruturado no formato definido em `references/schema.md`.

Nesta skill, cada evento gera exatamente 1 transação JSON.

Esta skill cobre:
- proventos em reais ligados a ativos da bolsa brasileira, como dividendos, JCP, rendimentos de FIIs, dividendos de ETFs ou BDRs e receitas passivas equivalentes, como aluguel de ações creditado em reais
- rendimento passivo em cripto recebido no proprio ativo, como staking, lend ou earn
- bonificacoes que aumentam a quantidade de acoes, cotas ou outros ativos elegiveis
- split ou desdobramento, quando o efeito for aumento de quantidade
- inplit, agrupamento ou reverse split, quando o efeito for reducao de quantidade
- ajuste manual de quantidade para mais ou para menos, mesmo sem evento corporativo

Esta skill nao cobre:
- compra e venda comuns de ativos de bolsa
- compra e venda comuns de criptoativos
- eventos que exijam mais de 1 transacao por evento
- subscricao, cisao, incorporacao, fusao, spin-off, amortizacao, direito de subscricao ou qualquer caso que exija rateio de custo ou logica patrimonial adicional

# Quando usar
Use esta skill quando o usuario:
- enviar texto, imagem, PDF ou outro comprovante de recebimento de dividendos, JCP, rendimentos ou proventos de ativos
- enviar texto, imagem, PDF ou outro comprovante de staking, lend, earn ou rendimento em criptoativo
- informar que recebeu bonificacao, split, desdobramento, inplit, agrupamento ou reverse split
- pedir para ajustar manualmente a quantidade de um ativo da bolsa ou de um criptoativo
- informar um evento que aumente ou diminua a quantidade de um ativo sem ser compra ou venda

# Regras gerais
1. Sempre considerar o contexto enviado pelo usuario junto com os arquivos.
2. A saida final deve ser somente JSON valido, sem texto antes ou depois.
3. O JSON deve seguir exatamente o formato definido em `references/schema.md`.
4. O objeto raiz deve conter sempre a chave `transactions`.
5. `transactions` deve ser sempre uma lista, mesmo quando houver apenas 1 evento.
6. Cada item de `transactions` deve ser um objeto com exatamente estas chaves:
   - `from`
   - `to`
   - `amount`
   - `type`
   - `timestamp`
   - `obs`
7. Nao adicionar chaves extras fora do schema.
8. Todos os valores de cada transacao devem ser strings.
9. Cada evento coberto por esta skill deve gerar exatamente 1 transacao JSON, nem mais, nem menos.
10. Se houver multiplos eventos na mesma entrada, gerar exatamente 1 transacao para cada evento identificado.
11. O campo `timestamp` deve usar o formato `DD-MM-YYYY`.
12. O campo `amount` deve ser sempre string numerica.
13. O campo `type` deve seguir estas regras:
   - `buy`: quando o evento aumenta a quantidade do ativo
   - `sell`: quando o evento diminui a quantidade do ativo
   - `create batch`: quando o evento gera ganho em dinheiro real, incluindo qualquer provento monetario em reais que use o bucket `_yeld`
14. Quando `from` ou `to` representarem banco, corretora, conta ou exchange, usar apenas valores permitidos pela taxonomia da skill.
15. Quando `from` ou `to` representarem o ativo:
   - para ativos da bolsa brasileira, preservar o identificador encontrado, por exemplo `ITUB4`, `MXRF11`, `BOVA11`, `AAPL34`
   - para criptoativos, usar sempre o nome completo em caixa alta, por exemplo `BITCOIN`, `ETHEREUM`, `SOLANA`
16. O bucket de estoque geral deve ser sempre `qtde__bens`.
17. O sufixo de quantidade deve ser sempre `_QTDE`.
18. O bucket de provento monetario em reais deve usar exatamente o sufixo legado `_yeld`, mesmo com essa grafia.
19. Se faltarem dados criticos para montar a transacao com seguranca, como nome do ativo, direcao do ajuste, quantidade a ajustar ou instituicao de destino do provento em reais, pedir esclarecimento ao usuario ou reportar erro em vez de inventar.
20. Depois de gerar o JSON, validar obrigatoriamente o resultado usando o script `scripts/validate_json.py`.
21. Se o JSON for invalido, tentar gerá-lo novamente, corrigindo os erros apontados pelo validador.
22. O numero maximo de tentativas de geracao e validacao e 3.
23. Se, apos 3 tentativas, o JSON continuar invalido, interromper o processo e informar falha de validacao em vez de retornar um JSON invalido.

# Normalizacao
Aplique apenas normalizacao basica, quando possivel:
- datas em `DD-MM-YYYY`
- valores monetarios em formato textual decimal, por exemplo `"10.00"` ou `"125.43"`
- quantidades em formato textual com a precisao necessaria, por exemplo `"12"`, `"0.01500000"` ou `"100.50000000"`
- nomes de ativos da bolsa preservando o identificador encontrado
- nomes de criptoativos em formato nome completo em caixa alta
- texto sem espacos superfluos

# Classes de evento
Todo evento coberto por esta skill cai em exatamente uma das classes abaixo.

## 1) Provento monetario em reais
Use esta classe quando o evento gera dinheiro em reais ligado a um ativo, mas nao representa venda do ativo.

Exemplos tipicos:
- dividendos
- JCP
- rendimento de FII
- dividendo de ETF
- dividendo de BDR
- aluguel de acoes pago em reais
- qualquer outro ganho passivo em reais vinculado a um ativo elegivel

Mapeamento:
- `from`: nome do ativo seguido de `_yeld`
- `to`: instituicao onde o dinheiro caiu
- `amount`: valor recebido em reais
- `type`: `create batch`
- `timestamp`: data do credito ou do evento, conforme a melhor evidencia disponivel
- `obs`: descricao resumida do provento

Exemplo conceitual:
- se o usuario recebeu R$ 10,00 de dividendos de `ITUB4` na rico:
  - `from`: `ITUB4_yeld`
  - `to`: `rico`
  - `amount`: `"10.00"`
  - `type`: `create batch`

## 2) Evento que aumenta a quantidade do ativo
Use esta classe quando o evento credita quantidade no ativo sem haver compra tradicional.

Exemplos tipicos:
- staking
- lend ou earn em que a recompensa e recebida no proprio criptoativo
- bonificacao em acoes, FIIs, ETFs, BDRs ou ativos equivalentes
- split ou desdobramento
- ajuste manual para aumentar a quantidade

Mapeamento:
- `from`: `qtde__bens`
- `to`: nome do ativo seguido de `_QTDE`
- `amount`: quantidade creditada
- `type`: `buy`
- `timestamp`: data do evento
- `obs`: descricao resumida do evento

### Como calcular a quantidade creditada
Use a melhor fonte disponivel nesta ordem:
1. Se o documento ou o usuario informar diretamente a quantidade acrescentada, usar esse valor.
2. Se houver quantidade antes e depois do evento, calcular:
   - `quantidade_creditada = quantidade_depois - quantidade_antes`
3. Se houver apenas o fator do split ou da bonificacao, so derivar a quantidade creditada quando a interpretacao do fator estiver inequivoca e puder ser checada com o contexto.
4. Se o fator estiver ambiguo ou nao houver dados suficientes para chegar ao delta com seguranca, pedir esclarecimento ao usuario ou reportar erro.

### Regra especifica para rendimento de cripto
Quando o rendimento vier em criptoativo:
- `from` deve ser sempre `qtde__bens`
- `to` deve ser o nome completo do criptoativo em caixa alta seguido de `_QTDE`
- `amount` deve ser a quantidade recebida no proprio ativo
- nao converter automaticamente essa recompensa para reais

## 3) Evento que diminui a quantidade do ativo
Use esta classe quando o evento reduz a quantidade do ativo sem haver venda tradicional.

Exemplos tipicos:
- inplit
- agrupamento
- reverse split
- ajuste manual para diminuir a quantidade

Mapeamento:
- `from`: nome do ativo seguido de `_QTDE`
- `to`: `qtde__bens`
- `amount`: quantidade removida
- `type`: `sell`
- `timestamp`: data do evento
- `obs`: descricao resumida do evento

### Como calcular a quantidade removida
Use a melhor fonte disponivel nesta ordem:
1. Se o documento ou o usuario informar diretamente a quantidade perdida, usar esse valor.
2. Se houver quantidade antes e depois do evento, calcular:
   - `quantidade_removida = quantidade_antes - quantidade_depois`
3. Se houver apenas o fator do agrupamento, so derivar a quantidade removida quando a interpretacao do fator estiver inequivoca e puder ser checada com o contexto.
4. Se o fator estiver ambiguo ou nao houver dados suficientes para chegar ao delta com seguranca, pedir esclarecimento ao usuario ou reportar erro.

# Regras de inferencia
1. Priorize a data efetiva do evento ou do credito. Se houver varias datas no documento, prefira a que representa o momento em que a movimentacao ocorreu na custodia ou no saldo.
2. Para proventos monetarios, a instituicao de destino e obrigatoria. Se o documento nao mostrar explicitamente onde o valor caiu, tente inferir pelo contexto do usuario. Se nao for possivel, interrompa.
3. Para ativos da bolsa brasileira, preserve o ticker encontrado e nao converta para nome longo.
4. Para criptoativos, converta tickers para nome completo apenas quando isso puder ser feito com seguranca, por exemplo:
   - `BTC` -> `BITCOIN`
   - `ETH` -> `ETHEREUM`
   - `SOL` -> `SOLANA`
5. Se a expansao para nome completo do criptoativo nao puder ser feita com seguranca, interrompa o processo em vez de emitir ticker abreviado.
6. Em split, inplit e ajustes manuais, o valor que vai em `amount` e sempre o delta de quantidade, nunca a quantidade final em carteira.
7. Nunca gere 2 transacoes para um unico evento coberto por esta skill.

# Processo
1. Identifique todos os eventos presentes na entrada.
2. Classifique cada evento em uma das 3 classes desta skill.
3. Para cada evento, determine:
   - ativo formatado
   - instituicao, quando aplicavel
   - quantidade ou valor recebido
   - direcao do movimento
   - data do evento
4. Se o evento for split, inplit ou ajuste manual, calcule primeiro o delta de quantidade.
5. Monte exatamente 1 transacao por evento.
6. Valide o JSON gerado com `scripts/validate_json.py`.
7. Se o validador indicar erro:
   - revise o objeto
   - corrija os campos
   - valide de novo
8. Repita o ciclo de geracao + validacao ate no maximo 3 tentativas no total.
9. Se houver insuficiencia de dados para um evento que deveria existir, interrompa em vez de inventar.
10. Se nao houver nenhum evento coberto por esta skill com evidencia suficiente, retorne:
```json
{
  "transactions": []
}
```

# Referencias
Antes de finalizar:
- consulte `references/schema.md` para o formato de saida
- consulte `references/taxonomy.md` e `assets/taxonomy.json` para instituicoes permitidas e regras de nomenclatura
- consulte `references/examples.md` para exemplos canonicos de cada classe de evento

# Validacao
Use o script abaixo para validar o JSON gerado:
- `python scripts/validate_json.py caminho/do/arquivo.json`

Se a validacao ocorrer por stdin, tambem e aceitavel:
- `cat caminho/do/arquivo.json | python scripts/validate_json.py`

Considere a validacao bem-sucedida apenas quando o script indicar que o JSON e valido.

# Saida
Retorne somente JSON valido, seguindo exatamente o schema definido em `references/schema.md`.
Nunca retorne JSON invalido.
