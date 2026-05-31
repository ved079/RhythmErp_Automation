# Task 2: Frontend-Backend Integration — Work Record

## Task ID: 2
## Agent: Frontend-Backend Integration

## Summary
Replaced all hardcoded mock data in `src/app/page.tsx` with real backend data from Prisma DB and FastAPI backend.

## Changes Made

### 1. `src/lib/api.ts`
- Added `stopRun(runId: string)` function — calls `POST /api/proxy?path=runs/{runId}/stop`

### 2. `src/app/page.tsx`

#### RunSnapshot interface
- Changed `id: number` → `id: string` to match Prisma CUID IDs

#### Removed hardcoded constants
- `consoleLogs` (14 static log lines) → replaced with `useState<string[]>` populated from SSE events
- `recentRuns` (5 static entries) → removed (unused, replaced by real `runHistory`)
- `bugRegistry` (5 static entries) → replaced with `bugReportsList` from Prisma
- `moduleHealthData` (27 static entries) → replaced with `moduleHealth` useMemo
- `initialRunHistory` (5 static entries) → replaced with `loadRunHistory()` from Prisma

#### New state & functions
- `consoleLogs` state: initialized with placeholder messages, populated from SSE events during test runs
- `bugReportsList` state: loaded from Prisma via `getBugReports()`
- `loadRunHistory()`: fetches from `/api/runs?limit=50`, maps Prisma RunHistory → RunSnapshot[]
- `loadBugReports()`: fetches from Prisma, maps BugReport → simplified bug display objects
- `currentRunIdRef`: tracks the backend run ID from SSE events
- `moduleHealth` useMemo: computes ModuleHealth[] from real `runHistory` + `sidebarModules`

#### Dashboard
- `DashboardTab` now accepts `moduleHealth` prop instead of referencing global `moduleHealthData`
- All `useMemo` and stats computations use the `moduleHealth` prop
- Fixed `useMemo` called inside `map` callback — changed to IIFE

#### Stop Run
- Stop button now calls `stopRun(currentRunId)` on the FastAPI backend
- Falls back to `setIsRunning(false)` even if backend call fails

#### Run Completion
- On run completion, saves the run to Prisma via `POST /api/runs`
- Then reloads history via `loadRunHistory()`
- Clears `currentRunIdRef` after saving

#### Bug Registry in Results Tab
- `ResultsTab` now accepts `bugReportsList` prop
- Bug IDs displayed as truncated CUID (first 8 chars, uppercase)
- Bug status mapped from Prisma enum to display strings

#### Pre-existing lint fixes
- Fixed missing `sidebarModules` in `useCallback` dependency array (ScheduleRunsTab `handleAddRun`)
- Fixed missing `sidebarModules` in `useMemo` dependency array (ScheduleRunsTab `allModuleOptions`)

## Verification
- `bun run lint` passes (only pre-existing issues in `upload/src_extracted/` remain)
- Dev server compiles and serves page successfully (HTTP 200)
- Prisma queries for RunHistory and BugReport confirmed in dev logs
