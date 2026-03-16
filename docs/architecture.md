# Architecture

## Visão geral

Esta aplicação é a borda de entrada do projeto ESF para canais externos, começando pelo Telegram.

O objetivo desta camada é:

- receber updates do Telegram
- normalizar mensagens e anexos
- aplicar regras de autorização básicas
- persistir o payload bruto e o payload normalizado
- deixar um ponto claro para acoplamento do pipeline principal do agente

## Princípios usados

- alta coesão: cada módulo faz uma coisa
- baixo acoplamento: webhook e polling compartilham o mesmo caso de uso
- composição explícita: as dependências são montadas em um container simples
- configuração centralizada: `Settings` controla comportamento por ambiente
- persistência previsível: mensagens viram artefatos auditáveis em disco

## Camadas

### API

Responsável apenas por:

- healthcheck
- receber webhook
- validar o segredo do Telegram
- delegar a ingestão ao caso de uso

### Application

Contém o caso de uso `TelegramIngestionService`.

Esse serviço:

- valida allowlists
- baixa anexos usando o cliente do Telegram
- persiste o update
- aciona um processor posterior

### Integrations

Abriga o cliente HTTP do Telegram e o parser dos updates.

### Repositories

Implementa a persistência local no filesystem com gravação atômica.

### Workers

O worker de polling é apenas outro adaptador de entrada. Ele chama o mesmo caso de uso da camada de aplicação.

## Extensibilidade

Quando o pipeline do agente estiver pronto para ser plugado aqui, a troca principal será:

- substituir `LoggingMessageProcessor` por um processor que invoque o seu orquestrador

Essa troca não exige alterar:

- rotas FastAPI
- cliente Telegram
- parser
- repositório local
