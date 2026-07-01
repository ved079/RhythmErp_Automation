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

## Session Progress — Concurrency Batch-Create System

### Goal
Build a full-stack concurrency batch-create testing system (UI + FastAPI backend) for parallel record creation across two ERP tenant groups (PC-1 / PC-2) with run results, history, and conflict detection.

### Constraints
- No new DB tables — concurrency runs reuse existing `RunHistory` table with `moduleId: 'concurrency'`
- Existing test/page-object files untouched
- Only `ConcurrencyTab.tsx`, `api.ts`, `api/models.py`, `api/batch_create.py` may be modified for new features

### Done
- Two-column PC-1 | PC-2 layout with per-tenant token+module via `SetTokenDialog`, auto-patch sharing, independent tenants, per-card terminal log (`CardLogs`), `batchCount` input, `canRun` + `MODULE_TO_BATCH` validation, Run button
- SSE streaming parsing for created (`CREATED|UPDATED #id - Name`) and failed (`FAILED - Name: reason`)
- `RunResultsPanel`: centered portal modal with overlap bar, By PC / Timeline view toggle, per-job avg ms/record, duplicate detection (same name on both PCs), conflict detection (created on one, failed on other), footer with overlap/created/failed/conflicts metrics
- Run persistence: `saveConcurrencyRun()` → `POST /api/runs` with `moduleId: 'concurrency'`
- History dialog: full table with filters, pagination (15/page), detail view with summary cards + job breakdown + duplicates/conflicts
- Conflict mode: toggle (`Swords` icon) → calls `/api/batch-create/preview` to generate payloads once → both PCs receive identical `fixed_payloads` list → race condition detection
- UI cleaned up: only "API Tests" tab visible with Create / CRUD sub-mode toggle

### Bug Fixes
- **422 error**: swapped `startBatchCreate` param order so `fixedPayloads` comes before `config` (was: `seed` landed in `config` slot)
- **Different data despite same seed**: replaced `random.seed()` approach with `fixed_payloads` — payloads are generated once via a preview endpoint and sent as the same list to both PCs, bypassing the module-level `_generated_names` dedup set that persisted across requests

### Key Decisions
- `RunHistory` table reused with `moduleId: 'concurrency'` — all concurrency data stored in `results` JSON string
- **Conflict mode now uses client-side override injection** instead of `fixed_payloads` — frontend generates one random value per unique field (e.g. PAN, email), passes it as `config._conflict_override` to both PCs. Backend spreads it into `kwargs` so every payload gets the same unique value, triggering a duplicate-key conflict on the second PC. No preview endpoint needed, no fragile FK resolution mismatch.
- shadcn `Dialog` components used for history list/detail instead of custom portals

### Relevant Files
- `web-ui/src/components/concurrency/ConcurrencyTab.tsx`: full concurrency UI
- `web-ui/src/lib/api.ts`: `startBatchCreate()` (SSE), `saveConcurrencyRun()`
- `web-ui/src/components/dialogs/BatchCreateSection.tsx`: `MODULE_TO_BATCH` with `conflictField`/`conflictValue` per module
- `api/batch_create.py`: `_conflict_override` handling in kwargs
- `web-ui/src/app/globals.css`: `animate-fadeIn` keyframe
- `web-ui/src/components/dialogs/SetTokenDialog.tsx`: reused token+tenantId dialog
