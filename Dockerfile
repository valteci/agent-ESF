FROM python:3.12-slim AS builder

ENV POETRY_VERSION=1.8.4 \
    POETRY_HOME=/opt/poetry \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install --yes --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://install.python-poetry.org | python3 -

WORKDIR /app

COPY pyproject.toml README.md ./
RUN ${POETRY_HOME}/bin/poetry install --only main --no-root

COPY src ./src
COPY docs ./docs
RUN ${POETRY_HOME}/bin/poetry install --only main


FROM node:24-bookworm-slim AS codex

RUN npm install -g @openai/codex


FROM python:3.12-slim AS runtime

ENV HOME="/app" \
    PATH="/app/.venv/bin:/usr/local/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN addgroup --system app && adduser --system --ingroup app --home /app app

WORKDIR /app

COPY --from=codex /usr/local /usr/local
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src /app/src
COPY --from=builder /app/README.md /app/README.md
COPY --from=builder /app/docs /app/docs
COPY AGENTS.md /app/AGENTS.md
COPY .agents /app/.agents
COPY skills-lock.json /app/skills-lock.json
COPY docker/entrypoint.sh /usr/local/bin/esf-entrypoint

RUN chmod +x /usr/local/bin/esf-entrypoint \
    && mkdir -p /app/data /app/.codex \
    && chown -R app:app /app

USER app

EXPOSE 8000

ENTRYPOINT ["esf-entrypoint"]

CMD ["uvicorn", "esf_agent_service.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
