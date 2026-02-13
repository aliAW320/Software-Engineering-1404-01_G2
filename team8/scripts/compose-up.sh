#!/usr/bin/env bash
set -euo pipefail

# Bring up the full stack with a single public gateway port.
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

ENV_FILE="${ENV_FILE:-.env}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Env file '$ENV_FILE' not found. Copy .env.example to $ENV_FILE and update secrets." >&2
  exit 1
fi

echo "Using env file: $ENV_FILE"
docker compose --env-file "$ENV_FILE" up -d --build
