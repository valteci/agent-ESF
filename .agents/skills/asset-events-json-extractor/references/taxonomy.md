# Taxonomia dos campos

## Valores permitidos para o lado monetario
Quando `from` ou `to` representarem banco, corretora, conta ou exchange, use somente valores permitidos pela taxonomia abaixo:

- `99pay`: saldo ou conta vinculada ao 99pay.
- `binance`: saldo ou conta vinculada a binance.
- `bitget`: saldo ou conta vinculada a bitget.
- `bradesco`: saldo ou conta vinculada ao bradesco.
- `bybit`: saldo ou conta vinculada a bybit.
- `coinbase`: saldo ou conta vinculada a coinbase.
- `foxbit`: saldo ou conta vinculada a foxbit.
- `inter`: saldo ou conta vinculada ao inter.
- `itau`: saldo ou conta vinculada ao itau.
- `kraken`: saldo ou conta vinculada a kraken.
- `mercado bitcoin`: saldo ou conta vinculada ao mercado bitcoin.
- `mercado pago`: saldo ou conta vinculada ao mercado pago.
- `nubank`: saldo ou conta vinculada ao nubank.
- `okx`: saldo ou conta vinculada a okx.
- `rico`: saldo ou conta vinculada a rico.
- `xp`: saldo ou conta vinculada a xp.

## Regras para identificadores de ativos
1. Para ativos da bolsa brasileira, preserve o identificador encontrado, por exemplo:
   - `ITUB4`
   - `MXRF11`
   - `BOVA11`
   - `AAPL34`
2. Para proventos monetarios em reais, o bucket de origem deve ser `ATIVO_yeld`.
3. O sufixo `_yeld` deve ser mantido exatamente nessa grafia por compatibilidade com o projeto.
4. Para movimentacoes quantitativas, usar sempre `ATIVO_QTDE`.
5. O bucket agregado de estoque deve ser sempre `qtde__bens`.

## Regras para nomes de criptoativos
Quando `from` ou `to` representarem o criptoativo:

1. usar sempre o nome completo em caixa alta
2. nunca usar ticker abreviado
3. converter siglas comuns quando houver evidencia suficiente, por exemplo:
   - `BTC` -> `BITCOIN`
   - `ETH` -> `ETHEREUM`
   - `SOL` -> `SOLANA`
   - `USDT` -> `TETHER`
   - `USDC` -> `USD COIN`
4. se a expansao para nome completo nao puder ser feita com seguranca, interromper o processo e reportar erro

## type
Representa a direcao economica da movimentacao.

Valores permitidos:
- `buy`: use quando o evento aumenta a quantidade do ativo, sempre no padrao `qtde__bens -> ATIVO_QTDE`.
- `sell`: use quando o evento reduz a quantidade do ativo, no padrao `ATIVO_QTDE -> qtde__bens`.
- `create batch`: use quando o evento gera ganho em dinheiro real, inclusive em proventos monetarios em reais no padrao `ATIVO_yeld -> instituicao`.
