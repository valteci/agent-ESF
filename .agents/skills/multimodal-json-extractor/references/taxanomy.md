# Taxonomia dos campos

## from
Representa a origem do dinheiro.

Valores permitidos:
- `99pay`: saldo ou conta vinculada ao 99pay
- `carteira`: dinheiro físico em carteira
- `mercado pago`: saldo ou conta vinculada ao mercado pago
- `nubank`: Saldo ou conta vinculada ao nubank
- `rico`: saldo ou conta vinculada à rico
- `bradesco`: saldo ou conta vinculada ao bradesco

## to
Representa o destino econômico do dinheiro.

Valores permitidos:
- `comida`: gastos com alimentação em geral.
- `contas casa`: despesas da casa.
- `transporte`: locomoção, combustível, app, ônibus etc.
- `academia`: gastos com academia e treino.
- `educacao`: gastos com educacao e ferramentas de estudo.
- `dentista`: gastos com dentista e procedimentos dentários.
- `cabelo`: gastos com corte de cabelo e procedimentos no cabelo.
- `plano saude`: gastos com plano de saúde e coparticipação de planos de saúde.
- `compras`: gastos com compras de produtos e objetos.
- `viagens`: gastos com viagens.


## type
Representa a intenção da movimentação.

Valores permitidos:
- `create batch`: Tudo que engloba ganho de dinheiro, tudo que gera dinheiro
- `pay`: pagamento de despesa, serviços, produtos.
- `transfer`: transferência entre contas/carteiras
- `donate`: doação de dinheiro.
- `lend`: empréstimo concedido.
- `return`: pagamento de empréstimo por parte dos devedores.
