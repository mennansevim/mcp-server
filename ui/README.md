# UI README

This folder contains the React UI for live logs and runtime config management.

## Pages

- `/ui/logs` -> PR runs dashboard (active/completed/error with status dots)
- `/ui/logs/:runId` -> grouped run event timeline
- `/ui/config` -> editable runtime config (polling, review settings, AI provider/model)

## Stack

- React 18 + TypeScript
- Vite
- React Router
- Vitest + Testing Library

## Local Development

```bash
cd ui
npm install
npm run dev
```

Vite dev server starts on the default Vite port (usually `5173`).

## Build

```bash
cd ui
npm run build
```

Build output is generated under `ui/dist`.

## Tests

```bash
cd ui
npm test -- --run
```

## Backend Integration

UI consumes these backend endpoints:

- `GET /api/logs/config`
- `GET /api/logs/runs`
- `GET /api/logs/active/{run_id}/events`
- `GET /api/config`
- `PUT /api/config`

When running in Docker, FastAPI serves built UI under `/ui`.

## Notes

- `node_modules` and `dist` are ignored by git.
- Config changes made from `/ui/config` are persisted by backend into `config.overrides.yaml` (if writable/mounted).
