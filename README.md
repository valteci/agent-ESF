# ESF Agent Service

Camada de aplicação para receber mensagens do Telegram, normalizar os updates e persistir a entrada multimodal em disco de forma organizada para o pipeline do agente.

## O que foi adicionado

- `FastAPI` para expor `healthcheck` e webhook do Telegram
- `polling worker` para desenvolvimento local sem URL pública
- `Poetry` para gerenciamento de dependências
- `Docker` multi-stage e `docker-compose`
- armazenamento local de updates e anexos em `data/`
- arquitetura em camadas, com separação entre API, casos de uso, integrações e repositórios

## Arquitetura

O serviço usa um estilo `ports and adapters` simples:

- `api`: entrada HTTP
- `integrations`: cliente e parser do Telegram
- `application`: orquestração do caso de uso de ingestão
- `repositories`: persistência local dos updates e anexos
- `workers`: adaptador de polling local

O webhook HTTP e o polling usam o mesmo caso de uso. Isso evita duplicar lógica e mantém o transporte desacoplado do processamento.

Detalhes adicionais em [docs/architecture.md](docs/architecture.md).

## Estrutura de pastas

```text
src/esf_agent_service/
  api/
  application/
  cli/
  core/
  domain/
  integrations/
  repositories/
  workers/
tests/
docs/
```

## Variáveis de ambiente

Copie `.env.example` para `.env` e ajuste os valores.

Variáveis principais:

- `TELEGRAM_API_KEY`: token do bot. O serviço também aceita `TELEGRAM_BOT_TOKEN`.
- `TELEGRAM_TRANSPORT_MODE`: `polling` ou `webhook`.
- `TELEGRAM_WEBHOOK_SECRET`: segredo opcional validado no header do webhook.
- `TELEGRAM_ALLOWED_USER_IDS`: lista separada por vírgula para restringir usuários.
- `TELEGRAM_ALLOWED_CHAT_IDS`: lista separada por vírgula para restringir chats.
- `TELEGRAM_DOWNLOAD_MEDIA`: baixa anexos recebidos.
- `TELEGRAM_ACK_ENABLED`: liga a resposta automática do bot. O default atual é `true`.
- `TELEGRAM_ACK_TEMPLATE`: texto da resposta automática. O default atual é `recebi sua mensagem`.
- `STORAGE_ROOT`: diretório raiz onde os updates serão persistidos.

## Execução local com Poetry

`poetry` não está instalado no ambiente atual do repositório, então você precisará instalá-lo antes do primeiro uso.

```bash
cp .env.example .env
poetry install
poetry run uvicorn esf_agent_service.main:create_app --factory --host 0.0.0.0 --port 8000
```

Em outro terminal, suba o poller local:

```bash
poetry run esf-agent-poller
```

Com `TELEGRAM_TRANSPORT_MODE=polling`, o worker usa `getUpdates`, então você não precisa expor o `localhost`.

## Execução local com Docker

```bash
cp .env.example .env
docker compose up --build
```

Isso sobe:

- `api`: FastAPI em `http://localhost:8000`
- `telegram-poller`: consumidor local do bot via polling

## Modo webhook

Quando você quiser usar webhook:

1. exponha o FastAPI em uma URL HTTPS pública
2. defina `TELEGRAM_TRANSPORT_MODE=webhook`
3. preencha `TELEGRAM_WEBHOOK_URL`
4. registre o webhook

Via Poetry:

```bash
poetry run esf-agent-webhook set
```

Para remover:

```bash
poetry run esf-agent-webhook delete
```

## Onde as mensagens ficam salvas

Os updates e anexos são persistidos em:

```text
data/
  inbox/
    chat_<chat_id>/
      <timestamp>__m<message_id>__u<update_id>/
        message.json
        raw_update.json
        attachments/
```

`message.json` contém a mensagem normalizada. `raw_update.json` mantém o payload original do Telegram.

## Próximo ponto de integração

O serviço já recebe a mensagem, baixa anexos e persiste tudo de forma consistente. O ponto natural para encaixar o seu workflow de negócio é o `LoggingMessageProcessor`, que hoje só registra que a mensagem está pronta para seguir para o pipeline do agente.
