#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

ENV_FILE="${ENV_FILE:-.env}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Env file '$ENV_FILE' not found. Nothing to tear down?" >&2
  exit 1
fi

if [[ ${KEEP_VOLUMES:-0} -eq 0 ]]; then
  docker compose --env-file "$ENV_FILE" down -v
else
  docker compose --env-file "$ENV_FILE" down
fi
