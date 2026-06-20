# Web Architecture Audit & Refactor Plan — Pacs_Automation (web-ui + api)

> **Audience:** This document is the execution spec for an agent with full
> read/write access to this codebase. Each task lists exact paths, the action, and an
> acceptance check. Work the phases **in order** — Phase 1 is zero-risk and unblocks
> the rest. Do **not** batch unrelated phases into one commit.

---

## Context

This is an internal ERP test-automation product, built solo, intended to make manual QA
of the Rhythm ERP obsolete and to be maintained for years by the internal ERP team.

**Current architecture (it is fundamentally sound — keep the shape):**
- **Frontend + business DB:** Next.js 16 App Router (`web-ui/`), React 19, Tailwind v4,
  shadcn/Radix UI, Prisma → PostgreSQL. Owns auth, users, bug reports/tickets,
  notifications, schedules, run history, environments, settings, audit log, module
  taxonomy.
- **Execution engine:** FastAPI (`api/server.py`, v3.0.0) — "pure execution": discovers
  pytest/Selenium tests, runs them, streams live results over SSE, takes screenshots,
  batch-creates ERP records. Stateless re: auth.
- **Bridge:** `web-ui/src/app/api/proxy/route.ts` — all browser→FastAPI traffic goes
  through this Next.js route, which enforces session auth + CSRF + injects
  `X-Proxy-API-Key` and `X-User-*` headers. Clean boundary; keep it.
- **Live data:** SSE stream parsed in `web-ui/src/lib/api.ts` (`startRun`), accumulated
  into a `RunCompletionSummary`, then persisted to Postgres via `/api/runs`.

The split is good. The problems are **accumulated cruft, two god-files, a dead feature
set, repo hygiene, an unused-but-installed data layer, and an untested orchestration
layer.** The goal of this plan is to make the codebase clean, consistent, testable, and
safe to hand to a team.

> **Scope — read this first.** This plan covers **only the web part**: the Next.js app
> (`web-ui/`) and the FastAPI service that powers it (`api/`). It does **NOT** cover the
> Selenium/pytest ERP test corpus under `pages/` — that is the product's test content,
> it is extensive and out of scope here. Do not modify, delete, or "add tests to" anything
> under `pages/`. Every path in this document lives under `web-ui/` or `api/`.

**Pre-flight for the executing agent:**
- Phases 1–3 are **already complete** (commits `d33ff36`, `3002f46`, `a2822aa`). Start from Phase 4.
- Confirm with `git log --oneline -5` before starting — the top commit should be `a2822aa chore: remove unused dependencies`.
- After **every** phase: `cd web-ui && npx tsc --noEmit && npm run lint && npm run build`
  must pass before moving on. Treat a broken build as a stop-the-line event.

---

## Phase 1 — Repo hygiene (zero risk, do first)

The repo commits generated artifacts, databases, and binaries. This bloats clones, leaks
local state, and creates merge noise.

### 1.1 Stop tracking generated/local files
Remove from git tracking (keep on disk) with `git rm --cached`, then add to `.gitignore`:

| Path / pattern | What it is |
|---|---|
| `api_runs.db` | Local SQLite run DB (root) |
| `web-ui/prisma/dev.db` | Local SQLite (Prisma datasource is **postgresql** — this file is stale/irrelevant) |
| `api/batch_results/*.json` | 60 committed run-result blobs (runtime output) |
| `api/screenshots/**` | Runtime screenshot output |
| `web-ui/tsconfig.tsbuildinfo` | TS incremental build cache (300KB) |
| `*.log` (`api_results.log`, etc.) | Runtime logs |
| `web-ui/*.png` (`erp-*.png` — 4 large login screenshots, ~600KB) | Dev fixtures; move to `web-ui/agent-ctx/` or `docs/` if still needed, else drop |
| `GP_Bugs_Report.xlsx`, `bug_sheet.csv` | Confirm with user — look like one-off data dumps |

- Root `.gitignore` already ignores `*.log`, `__pycache__`, `.env` — but the DB/json/db
  artifacts predate it. Add explicit entries: `*.db`, `api/batch_results/`,
  `api/screenshots/`, `web-ui/tsconfig.tsbuildinfo`.
- Keep `api/batch_results/.gitkeep` and `api/screenshots/.gitkeep` so dirs exist.
- **Do not** rewrite git history (no filter-branch/BFG) unless the user explicitly asks —
  just stop tracking going forward.

**Acceptance:** `git status` shows the files as untracked/ignored; `git ls-files | grep -E '\.db$|batch_results|\.tsbuildinfo'` returns nothing.

### 1.2 Secrets check
- Confirm `.env` (root) and `web-ui/.env` are git-ignored (they are via `.env*`) and were
  **never** committed: `git log --all --full-history -- .env web-ui/.env`. If they were,
  flag to the user — secrets (`PROXY_API_KEY`, `DATABASE_URL`, ERP creds) may need rotation.
- Ensure `.env.example` files stay current with every key the code reads.

---

## Phase 2 — Delete dead & duplicate code (low risk)

Verified unused via import-graph grep. Each deletion below was confirmed to have **no
importer**. Re-verify with `grep -rn "<ComponentName>" web-ui/src` before deleting, then
delete and rebuild.

### 2.1 Duplicate components (pick the imported one, delete the twin)
| Delete (dead) | Keep (imported) | Evidence |
|---|---|---|
| `web-ui/src/components/shared/NavToast.tsx` (815 lines) | `components/nav-toast/NavToast.tsx` | `app/page.tsx:14` imports `nav-toast/NavToast` |
| `web-ui/src/components/auth/UserProfileDialog.tsx` (194) | `components/dialogs/UserProfileDialog.tsx` | `app/page.tsx:63` imports `dialogs/UserProfileDialog` |
| `web-ui/src/components/modules/OperationsTab.tsx` (379) | — | **Neither** OperationsTab is imported anywhere |
| `web-ui/src/components/operations/OperationsTab.tsx` (364) | — | Both are dead; confirm no dynamic import, then remove both |

> ⚠️ For `OperationsTab`: grep returned only the two files themselves (no importer). Confirm
> there's no string-built dynamic import, then delete both. If one IS wired in via a path
> this grep missed, keep that one and delete the other.

### 2.2 The disabled "AI Features" set — **REMOVE** (decided)
The AI feature is fully commented out in `app/page.tsx` (lines ~78–82, ~159–162, ~795–797,
~1158–1164). **Delete all of it:**
- `web-ui/src/components/ai/` — all 4 files (~1000 lines)
- `web-ui/src/app/api/ai/` — all 4 routes (`bug-triage`, `failure-analysis`, `nl-run`, `test-suggestions`)
- All commented-out AI blocks in `app/page.tsx` (imports, state, handlers, JSX)
- `z-ai-web-dev-sdk` from `package.json` (only used by the deleted routes)

### 2.3 Dead legacy Python server
- `web-ui/api/server.py` (614 lines) is **not referenced** by any script, import, or the
  canonical `api/server.py` (220 lines, the one actually run — imports `from api.models …`).
  It is a stale earlier copy of the backend living under the Next.js tree.
- Confirm nothing launches it (`grep -rn "web-ui/api" .`, check `eod_sync.ps1`, `scripts/`),
  then delete `web-ui/api/` entirely (`server.py` + empty `__init__.py`).

**Acceptance for Phase 2:** build + lint + typecheck pass; `git grep` for each deleted
symbol returns nothing.

---

## Phase 3 — Prune unused dependencies (low risk)

After Phase 2, audit `web-ui/package.json`. Confirmed currently unused:
- `@tanstack/react-query` — installed, **zero** `useQuery`/`QueryClient` usage. Either
  remove, **or** adopt it in Phase 5 (see below). Decide as part of Phase 5; do not remove
  if you intend to adopt.
- `@tanstack/react-table` — **zero** usage. Remove.
- `z-ai-web-dev-sdk` — remove if Phase 2.2 option (A) chosen.
- Single-use deps to verify still wired to real UI (keep if a shadcn `ui/` primitive uses
  them; these are fine to leave): `embla-carousel-react`, `vaul`, `input-otp`,
  `react-resizable-panels`, `react-day-picker`.

Run `npx depcheck` (or manual grep) to produce the final removal list before editing
`package.json`. Re-run `npm install` and rebuild.

**Acceptance:** `npm run build` passes; `npx depcheck` shows no unused *runtime* deps
(shadcn primitives may show as false positives — verify each).

---

## Phase 4 — Break up the god-files (medium risk, high value)

Two files hold the entire app and are the single biggest maintainability risk:
- `web-ui/src/app/admin/page.tsx` — **3316 lines, 96 `useState`** in one component.
- `web-ui/src/app/page.tsx` — **1182 lines**, the main dashboard orchestrator.

This is the core of "maintainable for years." Approach — **incremental, behavior-preserving
extraction** (no rewrite):

### 4.1 admin/page.tsx
It already renders multiple admin sections (users, modules, tests, environments, settings,
bug reports/chats, audit log). Extract each section into its own component under
`web-ui/src/components/admin/sections/`:
- `UsersSection.tsx`, `ModulesSection.tsx`, `TestVisibilitySection.tsx`,
  `EnvironmentsSection.tsx`, `SettingsSection.tsx`, `BugReportsSection.tsx`,
  `AuditLogSection.tsx`, `SystemHealthSection.tsx`.
- Each section owns its own `useState`/data-loading (move the relevant `useCallback`
  loaders with it). `admin/page.tsx` becomes a thin tab-router (~200–300 lines) holding
  only shared user/session state and tab selection.
- Extract repeated server-state loaders into hooks under `web-ui/src/hooks/admin/`
  (e.g. `useBugReports`, `useTestOverrides`, `useAuditLog`) so loading logic isn't inlined.
- Reuse existing helpers: `web-ui/src/lib/admin-helpers.ts`,
  `web-ui/src/lib/bug-reports.ts`, `web-ui/src/lib/csrf-client.ts` (`withCsrf`).

### 4.2 app/page.tsx
- Extract the run-lifecycle logic (SSE start, completion-stats assembly, run-history reload,
  the duration/module-name derivation blocks around lines 447–520 and 712–790) into a
  `useTestRun` hook under `web-ui/src/hooks/`.
- Extract the dialog-state cluster (completion modal, report dialog, run-detail,
  run-history, comparison) into a `useDialogs` hook or a small context.
- The page keeps layout + tab routing; tabs already live in
  `components/{test-runner,live-execution,results,...}` — push remaining inline logic down.

> **Method:** one section/hook per commit, rebuild + manual smoke-test after each. Never
> move more than one section before re-verifying. Behavior must be identical — this is
> extraction, not redesign.

**Acceptance:** `admin/page.tsx` < ~400 lines and `page.tsx` < ~400 lines; build + lint
pass; manual walkthrough of every admin tab and the main run flow behaves identically.

---

## Phase 5 — Unify the data-fetching layer (medium risk)

Today every component hand-rolls `fetch` + `useState` + `useEffect` with ad-hoc error
handling (some swallow errors silently, e.g. `syncModulesToDB`, `fetchRunsFromDB`). This is
inconsistent and a bug source. `@tanstack/react-query` is **already a dependency but never
wired up.**

**Decision (recommend adopt):** Add a `QueryClientProvider` in `web-ui/src/app/layout.tsx`
and migrate read endpoints (`fetchRunsFromDB`, `fetchModules`, `getBugReports`,
notifications, dashboard stats) to `useQuery`, and writes to `useMutation` with cache
invalidation. This gives caching, loading/error states, and retries for free and removes a
lot of `useEffect` boilerplate (synergizes with Phase 4 hooks).

- Centralize all endpoint calls in `web-ui/src/lib/api.ts` + `lib/bug-reports.ts` (already
  the de-facto API clients) and have hooks call those — keep `fetch` details out of
  components.
- Standardize error handling: the recent `addBugReport` change (throws with status+body) is
  the **right pattern** — apply it to every client function that currently does
  `if (!res.ok) return null` / silent-catch. Surface errors via `sonner` toasts.

If the user prefers **not** to adopt react-query, instead build a thin
`useFetch`/`useAsync` hook and remove the dependency in Phase 3.

**Acceptance:** no component contains a raw `fetch(...)` for app data (only the
hooks/lib layer does); loading & error states are consistent.

---

## Phase 6 — Consolidate module taxonomy (medium risk)

Module identity is currently expressed **three+ times** and kept in sync by hand:
- `web-ui/src/lib/api.ts` → `FOLDER_TO_SIDEBAR` map (~50 entries) **and** its hand-written
  inverse `sidebarToFolderMapping` (with duplicated `topModules`/`commonSubs`/… arrays).
- `web-ui/src/data/sidebarModules.ts` (sidebar tree).
- `prisma/schema.prisma` `TestModule` table + `/api/admin/modules/*` routes (DB taxonomy
  that already syncs from FastAPI discovery).
- FastAPI `api/test_discovery.py` (folder → module discovery, the real source).

Problems: the inverse map is fragile (note `entity_group_definition` and `entity_group`
both → `entity-group`, so the reverse is lossy); adding a module means editing 3 files.

**Plan:**
- Make **one** source of truth. The `TestModule` DB table (synced from FastAPI discovery
  via `syncModulesToDB`) is the natural choice — it already exists and updates automatically.
- Replace the hand-maintained `FOLDER_TO_SIDEBAR` / `sidebarToFolderMapping` with lookups
  derived from the synced module data (add `folderName`/`sidebarId` columns to `TestModule`
  if needed, via a Prisma migration).
- Keep a single bidirectional helper in `lib/module-data.ts` (already exists, 123 lines —
  extend it) and delete the duplicated arrays in `api.ts`.
- The recent working-tree change correctly routes both the callback route and
  `saveRunResults` through `folderToSidebarId` — preserve that call-site, just back it with
  the consolidated source.

> This phase touches data flow; do it **after** Phases 4–5 and behind thorough manual
> testing of run-save + sidebar navigation + admin module sync. If it proves risky, it can
> be deferred — document the duplication with a `// SINGLE SOURCE OF TRUTH:` comment instead.

**Acceptance:** adding/removing a test folder in `pages/` flows to the sidebar and run
history with **no** manual map edits; `sidebarToFolderMapping`'s duplicated arrays are gone.
(Note: `pages/` itself is read-only context for this phase — the change is in `web-ui/` +
`api/test_discovery.py` consumption, never in the ERP test files.)

---

## Phase 7 — Testing & quality gates for the web layer

> **Scope reminder:** This is about testing the **web/orchestration layer only** — the
> `web-ui` React app and the FastAPI service in `api/`. The ERP test corpus under `pages/`
> is out of scope and already extensive; do not touch it.
>
> The gap: the orchestration layer that *runs and records* test runs has no automated
> coverage of its own. A regression in this thin layer (auth, the proxy boundary, SSE
> parsing, run-save math, module discovery) can silently break run execution or corrupt
> saved results — so it needs targeted tests.

### 7.1 Unit/integration (Vitest)
- Add `vitest` + `@testing-library/react`. Config under `web-ui/`.
- Priority targets (pure logic, high leverage):
  - `lib/api.ts` — SSE parsing in `startRun`, `saveRunResults` duration/rate math,
    `folderToSidebarId`.
  - `lib/bug-reports.ts`, `lib/session.ts`, `lib/csrf.ts`, `lib/rate-limit.ts`.
  - Module taxonomy helpers (Phase 6).
- Add `"test": "vitest"` to `web-ui/package.json` scripts.

### 7.2 API route tests
- Test the auth/proxy boundary: `app/api/proxy/route.ts` (rejects unauthenticated,
  injects headers, 502 when backend down), `app/api/auth/*`, `app/api/runs/*`.

### 7.3 E2E (optional, Playwright)
- One happy-path smoke: login → select module → run tests (mock FastAPI SSE) → see
  completion modal → results persisted. Gate behind a separate `test:e2e` script.

### 7.4 FastAPI service (`api/`) — the engine, not the ERP tests
- Add focused tests for the **service code** only: `api/test_discovery.py` (folder→module
  mapping), the SSE event shapes emitted by `api/test_runner.py`, and request/response
  models in `api/models.py`. Put them in an `api/tests_engine/` dir (or similar) so they are
  clearly separated from the ERP corpus under `pages/`. **Do not add or modify anything in
  `pages/`.**

### 7.5 CI
- Add CI (repo origin is a GitLab server `172.16.16.147`, so prefer `.gitlab-ci.yml`;
  GitHub Actions if mirrored) running, for the web layer only: `npm ci`, `tsc --noEmit`,
  `eslint`, `vitest`, `next build`, plus `pytest` scoped to the engine tests from 7.4.
  Block merges on failure.

**Acceptance:** `npm test` runs and passes; CI config present and green on a test PR.

---

## Phase 8 — Robustness & polish (lower priority, ongoing)

- **Error boundaries:** add a React error boundary around the main app shell and admin
  shell so a render error in one section doesn't white-screen the whole tool.
- **Type safety:** tighten loose `Record<string, unknown>` / `any`-ish spots flagged during
  Phase 4 (e.g. `runDetail?.results` handling in `RunDetailDialog.tsx`). Generate shared
  types from the Prisma client and the FastAPI models (consider a single `lib/types.ts`
  contract mirrored on both sides).
- **Fix the known small bugs from the prior diff review** (carry these in):
  - `app/page.tsx` completion-stats: verify `moduleName`/`subModuleName` ordering matches
    the `${moduleName} → ${subModuleName}` display (currently looks inverted for sub-modules).
  - `admin/page.tsx` `adminUnreadChats` badge counts open/in-progress reports even with no
    chat messages — tighten the predicate.
  - `ReportToAdminDialog.tsx` — remove the artificial `setTimeout(..., 500)` around the
    async submit.
  - Replace hardcoded `style={{ height: 'calc(100vh - 320px)' }}` in `admin/page.tsx` with
    a layout/flex approach.
- **Observability:** structured logging on the proxy + FastAPI (request id, user id,
  duration); currently `console.error` only.
- **Docs:** add a `CLAUDE.md` at repo root (none exists) documenting the two-server
  architecture, how to run each (`npm run dev` + `uvicorn api.server:app`), the proxy
  boundary, and the module-taxonomy source of truth. Fold in the existing `docs/` content.

---

## Suggested order & risk summary

| Phase | Risk | Value | Notes |
|---|---|---|---|
| 1 Hygiene | none | high | Do immediately |
| 2 Dead code | low | high | Confirm-then-delete; one rebuild per group |
| 3 Deps | low | med | After 2; coordinate with 5 re: react-query |
| 4 God-files | med | very high | Incremental, one section/commit |
| 5 Data layer | med | high | Synergizes with 4 |
| 6 Taxonomy | med | med | Defer if risky; needs Prisma migration |
| 7 Testing/CI | low | very high | Can start in parallel after 2 |
| 8 Robustness | low | med | Ongoing |

## Global verification (run after each phase)
```
cd web-ui
npx tsc --noEmit      # type check
npm run lint          # eslint
npm run build         # next build
npm test              # once Phase 7 lands
```
Plus a manual smoke test of: login → run a module → completion modal → results persist →
admin tabs load → bug report create/reply. Backend: `uvicorn api.server:app --reload` and
hit `/api/health`.

## Decisions — all resolved

1. ~~**AI feature (Phase 2.2):**~~ **DECIDED — remove.**
2. ~~**react-query:**~~ **DECIDED — adopt.** Wire up `QueryClientProvider`, migrate all data fetches to `useQuery`/`useMutation`.
3. ~~**Git history:**~~ **DECIDED — leave history, stop tracking going forward.** `git rm --cached` + `.gitignore` only. Do not run BFG.
4. ~~**CI platform:**~~ **DECIDED — GitLab CI.** Add `.gitlab-ci.yml` at repo root. Repo origin is the internal GitLab server (`172.16.16.147`).
5. ~~**Data files:**~~ **DECIDED — keep in place, just add to `.gitignore`.** Do not move or delete `GP_Bugs_Report.xlsx`, `bug_sheet.csv`, or `erp-*.png`.
