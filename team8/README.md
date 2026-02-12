# Team 8 Deployment (Docker)

## Quick start
1. Copy env template and adjust secrets/domains:
   ```bash
   cp .env.example .env
   ```
2. Build & run everything (single public port via gateway):
   ```bash
   ./scripts/compose-up.sh
   # open http://localhost:${PUBLIC_PORT:-8080}/team8/
   ```
3. Tear down:
   ```bash
   ./scripts/compose-down.sh      # set KEEP_VOLUMES=1 to keep data
   ```

## Local dev helpers
- Start only Postgres + MinIO for running Django/Vite locally:
  ```bash
  ./scripts/dev-deps.sh
  ```

## Services (docker-compose.yml)
- `gateway` (nginx) exposes `${PUBLIC_PORT:-8080}` and routes `/team8/*` to the SPA/API/AI.
- `frontend` React/Vite, built with base path `/team8`.
- `backend` Django API on `:8002`, talks to Postgres + MinIO + AI.
- `ai-service` FastAPI on `:8001`, uses its own Postgres and MinIO.
- `minio` S3-compatible storage (bucket `team8-media` by default) and `minio-mc` to create bucket.
- `backend-db` and `ai-db` Postgres 16 instances.

If you change `S3_BUCKET_NAME`, also update `gateway.conf` bucket location so presigned URLs keep working.

## Running behind the parent (app404) stack
- The compose file joins the external network `app404_net` (created by the root project) so it can be reached from the parent stack without extra host ports.
- Host port mapping uses `${PUBLIC_PORT}` and also honors `${TEAM_PORT}` (used by `linux_scripts/up-team.sh`). Set `S3_PUBLIC_ENDPOINT` to `http://localhost:${TEAM_PORT:-PUBLIC_PORT}` so presigned URLs stay on the same host/port.
- To expose at `http://localhost:8000/team8/` through the parent gateway, add an upstream/location in the parent reverse proxy (or nginx) that forwards `/team8/`, `/team8/api/`, `/team8/ai/`, and `/team8-media/` to the `gateway` service on the shared `app404_net`. The service hostname is `gateway`.
- See `parent-nginx-team8.conf` for a minimal nginx snippet you can drop into the parent stack.
