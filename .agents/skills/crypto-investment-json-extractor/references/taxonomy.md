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

## Regras para nomes de criptoativos
Quando `from` ou `to` representarem o criptoativo negociado:

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
Representa a intencao da movimentacao.

Valores permitidos:
- `buy`: compra do criptoativo.
- `sell`: venda do criptoativo.
