#!/bin/sh
set -eu

HOME_DIR="${HOME:-/app}"
CODEX_AUTH_FILE="${HOME_DIR}/.codex/auth.json"

if [ "${AGENT_ENABLED:-false}" = "true" ]; then
  mkdir -p "${HOME_DIR}/.codex"

  if [ -n "${OPENAI_API_KEY:-}" ]; then
    echo "Configuring Codex authentication from OPENAI_API_KEY." >&2
    if ! printf '%s' "${OPENAI_API_KEY}" | codex login --with-api-key >/dev/null; then
      echo "Failed to authenticate Codex with OPENAI_API_KEY." >&2
      exit 1
    fi
  elif [ ! -f "${CODEX_AUTH_FILE}" ]; then
    echo "AGENT_ENABLED=true but Codex is not authenticated. Set OPENAI_API_KEY or mount a valid ~/.codex directory." >&2
    exit 1
  fi
fi

exec "$@"
