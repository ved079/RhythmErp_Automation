# Pacs Automation — Developer Guide

## Architecture

Two-server setup. Both must run for the app to work.

**Web UI** (`web-ui/`) — Next.js 16 App Router, React 19, Tailwind v4, Prisma → PostgreSQL.
Owns: auth, users, bug reports/tickets, notifications, schedules, run history, environments, settings, audit log, module taxonomy.

**Execution Engine** (`api/`) — FastAPI (Python). Pure execution: discovers pytest/Selenium tests, runs them, streams live results over SSE, takes screenshots, batch-creates ERP records. Stateless re: auth.

**Proxy bridge** — All browser → FastAPI traffic goes through `web-ui/src/app/api/proxy/route.ts`, which enforces session auth + CSRF and injects `X-Proxy-API-Key` and `X-User-*` headers. Never call the FastAPI server directly from the browser.

**ERP test corpus** (`pages/`) — Selenium/pytest tests covering the full ERP module tree. Out of scope for web-layer changes. Do not modify from the web refactor side.

## Running locally

```bash
# Terminal 1 — web UI
cd web-ui
npm install
npm run dev          # http://localhost:3000

# Terminal 2 — execution engine
pip install -r requirements.txt
uvicorn api.server:app --reload   # http://localhost:8000
```

Environment files needed: `web-ui/.env` (`DATABASE_URL`, `NEXTAUTH_SECRET`, `PROXY_API_KEY`) — see `.env.example`.

## Module taxonomy

Module identity is DB-driven via the `TestModule` table (synced from FastAPI discovery on login via `syncModulesToDB`). The mapping between `pages/` folder names and sidebar IDs lives in `web-ui/src/lib/module-data.ts`. A fallback map (`FOLDER_TO_SIDEBAR_FALLBACK`) covers modules not yet synced.

To add a new module: add the folder under `pages/`, run the app and log in — it syncs automatically.

## Key files

| File | Purpose |
|------|---------|
| `web-ui/src/app/api/proxy/route.ts` | Auth + CSRF proxy to FastAPI |
| `web-ui/src/lib/api.ts` | All FastAPI client calls (SSE, modules, runs) |
| `web-ui/src/lib/module-data.ts` | Module taxonomy helpers + DB cache |
| `web-ui/src/hooks/usePageData.ts` | Data loading (react-query) |
| `web-ui/src/hooks/useTestRun.ts` | Test run lifecycle |
| `web-ui/src/hooks/admin/useAdminState.ts` | Admin panel state |
| `api/server.py` | FastAPI entry point |
| `api/test_runner.py` | SSE test execution |
| `api/test_discovery.py` | `pages/` module discovery |

## Testing

```bash
# Web layer (Vitest)
cd web-ui && npm test

# FastAPI engine tests
pytest api/tests_engine/ -v

# Type check
cd web-ui && npx tsc --noEmit
```

## CI

GitLab CI via `.gitlab-ci.yml` — runs lint, typecheck, vitest, next build, and pytest on every MR and main push.
