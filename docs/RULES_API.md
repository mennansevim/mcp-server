# Rules API (Standalone)

This repository includes a **standalone Rules API** that can be deployed separately from the MCP server.

## What it does

- List available rule markdown files under `rules/`
- Fetch a rule file content
- Resolve rules for `focus` areas + optional `language` (prefers `{language}-{category}.md` if it exists)

## Endpoints

- `GET /` – health + resolved rules directory
- `GET /rules` – list rule files
  - optional filters: `language`, `category`
- `GET /rules/{filename}` – get a specific rule file content (e.g. `security.md`)
- `GET /rules/resolve` – resolve rules
  - example: `/rules/resolve?focus=security&focus=performance&language=python`

## Run locally (Python)

```bash
cd /Users/gocena/Desktop/mcp-server
export PORT=8001
export RULES_DIR=/Users/gocena/Desktop/mcp-server/rules
python rules_api/server.py
```

## Run with Docker Compose (recommended)

```bash
cd /Users/gocena/Desktop/mcp-server
docker compose -f docker/docker-compose.rules-api.yml up -d --build
curl -s http://localhost:8001/ | python3 -m json.tool
```

## Deploy

Build the image using `docker/Dockerfile.rules-api` and run it with:

- `PORT` (default `8001`)
- `RULES_DIR` (default `rules`, recommended `/app/rules` in container)

