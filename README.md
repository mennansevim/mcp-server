# MCP Code Review Server

Platform-agnostic AI code review server with webhook ingestion, MCP tools, live run logs UI, and editable runtime config UI.

## What This Repository Provides

- Single webhook endpoint for GitHub, GitLab, Bitbucket, Azure DevOps
- AI-based PR diff review via OpenAI / Anthropic / Groq
- Review result posting back to platform adapters
- Live log dashboard UI (`/ui/logs`) for active/completed/error runs
- Config UI (`/ui/config`) to update runtime settings from browser
- In-memory run/event buffer for near-real-time timeline polling

## Current Runtime Topology

- Backend: FastAPI app (`server.py`)
- UI: React + Vite build served by FastAPI under `/ui`
- Logs: In-memory run/event store (non-durable)
- Config:
  - Base file: `config.yaml`
  - Runtime override file: `config.overrides.yaml` (generated/updated by API/UI)

`server.py` loads config by deep-merging:
1. `config.yaml`
2. `config.overrides.yaml` (if exists)

## Prerequisites

- Python 3.11+ (local run)
- Node.js 20+ (UI dev/build)
- Docker (recommended runtime)
- At least one AI provider key:
  - `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` or `GROQ_API_KEY`
- Platform token for real webhook/diff fetch tests:
  - e.g. `GITHUB_TOKEN`

## 1) Quick Start (Recommended: Docker)

### Step 1: Prepare environment

```bash
cp .env.example .env
```

Edit `.env` and fill at least:

```bash
OPENAI_API_KEY=...
GITHUB_TOKEN=...
```

### Step 2: Build image

```bash
docker build -f docker/Dockerfile -t mcp-code-review:ui .
```

### Step 3: Run container

If you want config changes from `/ui/config` to persist across container recreation, mount override file:

```bash
touch config.overrides.yaml

docker run -d \
  --name mcp-server-ui \
  --env-file .env \
  -e GITHUB_TOKEN="$GITHUB_TOKEN" \
  -v "$(pwd)/config.overrides.yaml:/app/config.overrides.yaml" \
  -p 8000:8000 \
  mcp-code-review:ui
```

If you do not mount `config.overrides.yaml`, config changes are still applied at runtime but can be lost when container is removed.

### Step 4: Verify

```bash
curl -s http://localhost:8000/ | python3 -m json.tool
```

Open:

- Logs dashboard: `http://localhost:8000/ui/logs`
- Config page: `http://localhost:8000/ui/config`

## 2) Local Development Run

### Backend

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python server.py
```

### UI (optional dev server)

```bash
cd ui
npm install
npm run dev
```

For production serving through FastAPI, build UI:

```bash
cd ui
npm run build
```

## 3) Webhook Smoke Test

Example GitHub PR webhook payload:

```bash
curl -s -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -H "x-github-event: pull_request" \
  -d '{
    "action":"opened",
    "pull_request":{
      "number":5,
      "title":"PR webhook test",
      "html_url":"https://github.com/owner/repo/pull/5",
      "diff_url":"https://api.github.com/repos/owner/repo/pulls/5",
      "head":{"ref":"feature/test","sha":"abc123"},
      "base":{"ref":"main"},
      "user":{"login":"octocat"}
    },
    "repository":{
      "full_name":"owner/repo",
      "html_url":"https://github.com/owner/repo",
      "id":1
    }
  }' | python3 -m json.tool
```

Then inspect runs/events:

```bash
curl -s http://localhost:8000/api/logs/runs | python3 -m json.tool
curl -s http://localhost:8000/api/logs/active/<run_id>/events?cursor=0\&limit=200 | python3 -m json.tool
```

## 4) Config UI and Persistence

Editable fields in `/ui/config`:

- `ui.logs.poll_interval_seconds`
- `ui.logs.max_events_per_poll`
- `review.comment_strategy`
- `review.focus`
- `ai.provider`
- `ai.model` (provider-dependent dropdown)

Save flow:

1. UI sends `PUT /api/config`
2. Backend validates and applies runtime update
3. Backend writes editable config to `config.overrides.yaml`
4. Next startup re-loads with overrides merged on top of `config.yaml`

Environment variables affecting config files:

- `CONFIG_FILE_PATH` (default: `config.yaml`)
- `CONFIG_OVERRIDES_PATH` (default: `config.overrides.yaml`)

## 5) Main Endpoints

- `GET /` health
- `POST /webhook` universal webhook
- `GET /mcp/sse` MCP SSE endpoint
- `GET /api/logs/config` polling settings
- `GET /api/logs/active` active runs only
- `GET /api/logs/runs` all runs (active/completed/error)
- `GET /api/logs/active/{run_id}/events` incremental run events
- `GET /api/config` editable config snapshot
- `PUT /api/config` update + persist editable config
- `GET /ui/logs` logs dashboard
- `GET /ui/config` config page

## 6) Tests

Backend tests:

```bash
python3 -m pytest tests/test_config_api.py tests/test_logs_api.py tests/test_live_log_store.py tests/test_live_log_event_flow.py tests/test_ui_logs_config.py tests/test_ui_routes.py -v
```

UI tests/build:

```bash
cd ui
npm test -- --run
npm run build
```

## 7) Troubleshooting

### `Failed to fetch diff`

Most common reason: invalid/missing platform token (e.g. GitHub 401 Bad credentials).

Checks:

```bash
docker logs --tail 100 mcp-server-ui
```

Look for `github_fetch_diff_failed` and HTTP status details.

### Dashboard says no active runs

Expected when run quickly transitions to `error` or `completed`.

Use `/api/logs/runs` or dashboard list that includes all statuses.

### UI not opening

Use correct routes:

- `http://localhost:8000/ui/logs`
- `http://localhost:8000/ui/config`

Not `/logs` or `/config` directly on backend root.

### Config not persisted after recreating container

Mount override file as volume:

```bash
-v "$(pwd)/config.overrides.yaml:/app/config.overrides.yaml"
```

## 8) Project Layout (High Level)

- `server.py` FastAPI app + endpoints + runtime config update
- `adapters/` platform integrations
- `services/` AI review, diff analysis, rules, live log store
- `webhook/` parser/handler layer
- `ui/` React app (logs + config pages)
- `tests/` backend tests
- `docker/` Dockerfile and compose files
- `config.yaml` base config
- `config.overrides.yaml` runtime editable persisted config (generated)

## 9) Security Notes

- Keep secrets only in env vars (`.env`), never commit real tokens
- Use webhook signature checks in production where applicable
- Restrict inbound webhook sources with network controls/reverse proxy

## Additional Docs

- `docs/DEPLOYMENT.md`
- `docs/PROJECT_STRUCTURE.md`
- `docs/GITHUB_INTEGRATION.md`

