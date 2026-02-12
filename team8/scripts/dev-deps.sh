#!/usr/bin/env bash
set -euo pipefail

# Start only Postgres + MinIO for local dev (use with local runserver/npm dev).
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

ENV_FILE="${ENV_FILE:-.env}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Env file '$ENV_FILE' not found. Copy .env.example to $ENV_FILE and update secrets." >&2
  exit 1
fi

docker compose --env-file "$ENV_FILE" -f docker-compose.dev-db.yml up -d
