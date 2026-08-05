/**
 * API helper — all calls to the FastAPI backend go through the Next.js proxy.
 * This avoids CORS issues since the proxy runs server-side.
 *
 * Architecture:
 * - Test execution (start/stop/stream) → FastAPI via proxy
 * - Run history, modules sync → Next.js native DB routes
 * - Screenshots → FastAPI via proxy
 * - Test cases → FastAPI via proxy
 *
 * C6: All state-changing requests include CSRF token from cookie.
 */

import { folderToSidebarIdFromDB } from '@/lib/module-data'

const PROXY = "/api/proxy";

/**
 * C6: Get CSRF token from the csrf_token cookie for double-submit pattern.
 * The middleware sets this cookie on every response.
 */
function getCsrfToken(): string {
  if (typeof document === 'undefined') return ''
  const match = document.cookie.match(/(?:^|;\s*)csrf_token=([^;]*)/)
  return match ? decodeURIComponent(match[1]) : ''
}

/**
 * C6: Add CSRF token header to fetch options for state-changing requests.
 */
function withCsrf(options: RequestInit = {}): RequestInit {
  const csrfToken = getCsrfToken()
  if (!csrfToken) return options

  const headers = new Headers(options.headers || {})
  headers.set('X-CSRF-Token', csrfToken)

  return { ...options, headers }
}

// ─── FastAPI Types ───────────────────────────────────────

export interface ApiModule {
  name: string;
  display: string;
  sub_modules: ApiSubModule[];
}

export interface ApiSubModule {
  name: string;
  display: string;
  test_files: string[];
  tests: ApiTest[];
}

export interface ApiTest {
  name: string;
  display_name: string;
  docstring: string | null;
  type?: string;
}

export interface ApiRunListItem {
  id: string;
  module: string;
  sub_module: string | null;
  status: "pending" | "running" | "completed" | "failed" | "stopped";
  total_tests: number;
  passed: number;
  failed: number;
  started_at: string | null;
  duration: number | null;
}

export interface ApiRunDetail extends ApiRunListItem {
  skipped: number;
  completed_at: string | null;
  results: ApiTestResult[];
  report_path: string | null;
}

export interface ApiTestResult {
  name: string;
  status: "passed" | "failed" | "skipped" | "error";
  duration: number;
  message: string | null;
  traceback: string | null;
  screenshot: string | null;
}

// ─── Next.js Native DB Types ────────────────────────────

export interface RunHistoryItem {
  id: string;
  moduleId: string;
  moduleName: string;
  passed: number;
  failed: number;
  total: number;
  duration: string;
  rate: number;
  results: { testId: string; status: string; message?: string; duration?: number }[] | null;
  startedAt: string;
  completedAt: string | null;
  status: string;
  createdBy: string | null;
}

// ─── FastAPI Proxy Calls ────────────────────────────────

export async function fetchModules(): Promise<ApiModule[]> {
  const res = await fetch(`${PROXY}?path=modules`);
  if (!res.ok) return [];
  const data = await res.json();
  return data.modules || [];
}

/**
 * Fetch run detail from Next.js DB (native route, not FastAPI).
 * Replaces the old proxy-based fetchRunDetail.
 */
export async function fetchRunDetail(runId: string): Promise<RunHistoryItem | null> {
  try {
    const res = await fetch(`/api/runs/${runId}`);
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

// --- Stop a running test ---
export async function stopRun(runId: string): Promise<void> {
  const res = await fetch(`${PROXY}?path=runs/${runId}/stop`, withCsrf({ method: "POST" }));
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || data.error || `HTTP ${res.status}`);
  }
}

// --- Screenshot helper ---
export async function fetchScreenshot(): Promise<{ screenshot: string | null; active: boolean }> {
  try {
    const res = await fetch(`${PROXY}?path=screenshot`);
    if (!res.ok) return { screenshot: null, active: false };
    return res.json();
  } catch {
    return { screenshot: null, active: false };
  }
}

// --- SSE stream helper ---

export interface SSEEvent {
  type: "log" | "test_end" | "run_end" | "error" | "auth_error";
  message: string;
  test_name: string | null;
  status: string | null;
  duration: number | null;
  timestamp: string;
  run_id?: string;
  total_tests?: number;
  passed?: number;
  failed?: number;
  duration_ms?: number;
}

/**
 * Start a test run and return an EventSource-like stream.
 * Uses fetch + ReadableStream since EventSource doesn't support POST.
 * Collects run results for saving to Next.js DB after completion.
 */
export async function startRun(
  module: string,
  subModule: string | null = null,
  tests: string[] | null = null,
  onEvent: (event: SSEEvent) => void,
  onDone: (summary: RunCompletionSummary) => void,
  onError: (err: Error) => void,
  erpToken?: string,
  erpTenantId?: string,
  erpEmail?: string,
  erpPassword?: string,
) {
  try {
    const res = await fetch(`${PROXY}?path=runs/start`, withCsrf({
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        module,
        sub_module: subModule,
        tests,
        erp_token: erpToken || undefined,
        erp_tenant_id: erpTenantId || undefined,
        erp_email: erpEmail || undefined,
        erp_password: erpPassword || undefined,
      }),
    }));

    if (!res.ok || !res.body) {
      onError(new Error(`HTTP ${res.status}`));
      return;
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    // Track results for saving to DB after completion
    const summary: RunCompletionSummary = {
      runId: null,
      module,
      subModule,
      passed: 0,
      failed: 0,
      skipped: 0,
      total: 0,
      results: [],
      startedAt: new Date().toISOString(),
      completedAt: null,
      status: 'failed' as const,
    };

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          try {
            const event: SSEEvent = JSON.parse(line.slice(6));
            onEvent(event);

            // Track results for DB sync
            if (event.run_id && !summary.runId) {
              summary.runId = event.run_id;
            }
            if (event.type === 'test_end' && event.test_name && event.status) {
              if (event.status === 'passed') summary.passed++;
              else if (event.status === 'failed') summary.failed++;
              else summary.skipped++;
              summary.total++;
              summary.results.push({
                testId: event.test_name,
                status: event.status,
                message: event.message || undefined,
                duration: event.duration || undefined,
              });
            }
            if (event.type === 'run_end') {
              summary.completedAt = new Date().toISOString();
              summary.status = summary.failed > 0 ? 'completed' : 'completed';
              // Override with any totals from the run_end event
              if (event.total_tests !== undefined) summary.total = event.total_tests;
              if (event.passed !== undefined) summary.passed = event.passed;
              if (event.failed !== undefined) summary.failed = event.failed;
            }
          } catch {
            // skip malformed lines
          }
        }
      }
    }

    // If we never got a run_end, mark as completed anyway
    if (!summary.completedAt) {
      summary.completedAt = new Date().toISOString();
      summary.status = summary.total > 0 ? 'completed' : 'failed';
    }

    onDone(summary);
  } catch (err) {
    onError(err instanceof Error ? err : new Error(String(err)));
  }
}

/**
 * Start a batch data creation job and return an SSE stream.
 * Creates multiple ERP records via the FastAPI batch-create endpoint.
 * Calls onDone with the run_id for Excel export.
 */
export async function startBatchCreate(
  module: string,
  subModule: string,
  count: number,
  erpToken: string,
  erpTenantId: string,
  onEvent: (event: SSEEvent) => void,
  onDone: (runId: string | null) => void,
  onError: (err: Error) => void,
  fixedPayloads?: Record<string, unknown>[] | null,
  config?: unknown,
) {
  try {
    const res = await fetch(`${PROXY}?path=batch-create`, withCsrf({
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        module,
        sub_module: subModule,
        count,
        erp_token: erpToken,
        erp_tenant_id: erpTenantId,
        ...(config ? { config } : {}),
        ...(fixedPayloads?.length ? { fixed_payloads: fixedPayloads } : {}),
      }),
    }));

    if (!res.ok || !res.body) {
      onError(new Error(`HTTP ${res.status}`));
      return;
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let runId: string | null = null;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          try {
            const event: SSEEvent = JSON.parse(line.slice(6));
            if (event.run_id) runId = event.run_id;
            onEvent(event);
          } catch {
            // skip malformed lines
          }
        }
      }
    }

    onDone(runId);
  } catch (err) {
    onError(err instanceof Error ? err : new Error(String(err)));
  }
}

/**
 * Start a purchase chain creation job and return an SSE stream.
 * Start a purchase chain creation job and return an SSE stream.
 * Creates linked PO->GP->GRN->QC chain(s) via the FastAPI purchase-chain endpoint.
 */
export async function startPurchaseChain(
  count: number,
  supplierRefId: number,
  numItems: number,
  itemRefIds: number[],
  erpToken: string,
  erpTenantId: string,
  onEvent: (event: SSEEvent) => void,
  onDone: () => void,
  onError: (err: Error) => void,
  documents?: string[],
  itemCategoryId?: number,
  requireTaxRate?: boolean,
  multiGatePass?: boolean,
  gpCount?: number,
) {
  try {
    const res = await fetch(`${PROXY}?path=purchase-chain`, withCsrf({
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        count,
        supplier_ref_id: supplierRefId,
        num_items: numItems,
        item_ref_ids: itemRefIds,
        item_category_id: itemCategoryId ?? null,
        require_tax_rate: requireTaxRate ?? true,
        delay: 0.3,
        erp_token: erpToken,
        erp_tenant_id: erpTenantId,
        documents: documents ?? ["PO", "GP", "GRN", "QC"],
        multi_gate_pass: multiGatePass ?? false,
        gp_count: gpCount ?? 2,
      }),
    }));

    if (!res.ok || !res.body) {
      onError(new Error(`HTTP ${res.status}`));
      return;
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          try {
            const event: SSEEvent = JSON.parse(line.slice(6));
            onEvent(event);
          } catch {
            // skip malformed lines
          }
        }
      }
    }

    onDone();
  } catch (err) {
    onError(err instanceof Error ? err : new Error(String(err)));
  }
}

// ─── Run Completion Summary ─────────────────────────────
// Collected during SSE stream, used to save results to Next.js DB

export interface RunCompletionSummary {
  runId: string | null;
  module: string;
  subModule: string | null;
  passed: number;
  failed: number;
  skipped: number;
  total: number;
  results: { testId: string; status: string; message?: string; duration?: number }[];
  startedAt: string;
  completedAt: string | null;
  status: 'completed' | 'failed' | 'stopped';
}

// ─── Next.js Native DB Calls ────────────────────────────
// These read/write directly to the Next.js Prisma database,
// not through the FastAPI proxy.

/**
 * Fetch run history from Next.js DB (not FastAPI).
 * This is the primary source of truth for historical runs.
 */
export async function fetchRunsFromDB(limit = 50): Promise<RunHistoryItem[]> {
  try {
    const res = await fetch(`/api/runs?limit=${limit}`);
    if (!res.ok) return [];
    return res.json();
  } catch {
    return [];
  }
}

/**
 * Save run results to Next.js DB after a test run completes.
 * This is called automatically after SSE stream ends.
 */
export async function saveRunResults(summary: RunCompletionSummary, userId?: string): Promise<RunHistoryItem | null> {
  try {
    const durationMs = summary.completedAt && summary.startedAt
      ? new Date(summary.completedAt).getTime() - new Date(summary.startedAt).getTime()
      : 0;
    const durationStr = durationMs > 0
      ? `${Math.floor(durationMs / 60000)}m ${Math.floor((durationMs % 60000) / 1000)}s`
      : '—';
    const rate = summary.total > 0 ? Math.round((summary.passed / summary.total) * 10000) / 100 : 0;

    const folderName = summary.subModule || summary.module
    const sidebarId = await folderToSidebarIdFromDB(folderName)
    const mappedId = sidebarId ?? folderName.toLowerCase().replace(/_/g, '-')
    const res = await fetch('/api/runs', withCsrf({
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        moduleId: mappedId,
        moduleName: summary.subModule
          ? summary.subModule.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
          : summary.module.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
        passed: summary.passed,
        failed: summary.failed,
        total: summary.total,
        duration: durationStr,
        rate,
        results: summary.results,
        status: summary.status,
        startedAt: summary.startedAt,
        completedAt: summary.completedAt,
        createdBy: userId || null,
        userId: userId || null,
      }),
    }));
    if (!res.ok) return null;
    return res.json();
  } catch (err) {
    console.error('[saveRunResults] Failed to save:', err);
    return null;
  }
}

/**
 * Save a concurrency run result to the database.
 * Reuses the RunHistory table with a 'concurrency' moduleId prefix.
 */
export async function saveConcurrencyRun(data: {
  totalCreated: number
  totalFailed: number
  durationMs: number
  overlapMs: number
  conflicts: number
  duplicates: string[]
  jobs: Array<{ id: string; label: string; moduleId: string; side: 'pc1' | 'pc2'; created: string[]; failed: { name: string; reason: string }[] }>
  timing: Record<string, { startMs: number; endMs: number; events: { name: string; ms: number; side: 'created' | 'failed' }[] }>
}): Promise<RunHistoryItem | null> {
  try {
    const total = data.totalCreated + data.totalFailed
    const rate = total > 0 ? Math.round((data.totalCreated / total) * 10000) / 100 : 0
    const mins = Math.floor(data.durationMs / 60000)
    const secs = Math.floor((data.durationMs % 60000) / 1000)
    const durationStr = mins > 0 ? `${mins}m ${secs}s` : `${secs}s`
    const now = new Date().toISOString()
    const startedAt = new Date(Date.now() - data.durationMs).toISOString()

    const res = await fetch('/api/runs', withCsrf({
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        moduleId: 'concurrency',
        moduleName: 'Concurrency Test',
        passed: data.totalCreated,
        failed: data.totalFailed,
        total,
        duration: durationStr,
        rate,
        results: {
          type: 'concurrency',
          overlapMs: data.overlapMs,
          conflicts: data.conflicts,
          duplicates: data.duplicates,
          jobs: data.jobs,
          timing: data.timing,
        },
        status: data.totalFailed > 0 ? 'failed' : 'completed',
        startedAt,
        completedAt: now,
      }),
    }))
    if (!res.ok) return null
    return res.json()
  } catch (err) {
    console.error('[saveConcurrencyRun] Failed to save:', err)
    return null
  }
}

/** Called when modules are fetched, keeps the TestModule table up to date. */
export async function syncModulesToDB(modules: ApiModule[]): Promise<void> {
  try {
    await fetch('/api/admin/modules/sync', withCsrf({
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ modules }),
    }));
  } catch {
    // Silent fail — sync is non-critical
  }
}

// ─── Test Cases (still from FastAPI) ────────────────────

export interface TestCaseItem {
  id: string
  screenName: string
  description: string
  steps: string
  expected: string
  actual: string
  status: string
  date: string
}

export interface TestCaseModule {
  label: string
  tests: TestCaseItem[]
}

export type TestCasesData = Record<string, TestCaseModule>

export async function fetchTestCases(): Promise<TestCasesData> {
  const res = await fetch(`${PROXY}?path=test-cases`)
  if (!res.ok) throw new Error('Failed to fetch test cases')
  return res.json()
}

export interface BatchRecord {
  name: string
  record_id: number | string
  status: 'created' | 'verified' | 'approved' | 'failed'
}

export interface BatchRunSummary {
  run_id: string
  module: string
  sub_module: string
  total: number
  created: number
  failed: number
  elapsed_seconds: number
  timestamp: number // unix epoch (seconds)
  records: BatchRecord[]
}

export async function fetchBatchHistory(): Promise<BatchRunSummary[]> {
  const res = await fetch(`${PROXY}?path=batch-results`)
  if (!res.ok) throw new Error(`Failed to load batch history: HTTP ${res.status}`)
  return res.json()
}

/**
 * Download an Excel file for a completed batch create run.
 */
export async function exportBatchExcel(runId: string): Promise<void> {
  const res = await fetch(`${PROXY}?path=batch-create/${runId}/export`);
  if (!res.ok) throw new Error(`Export failed: HTTP ${res.status}`);
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const disposition = res.headers.get('Content-Disposition');
  const match = disposition?.match(/filename\*?=(?:UTF-8'')?["']?([^"'\s;]+)/i);
  const filename = match?.[1] ?? `batch-${runId}.xlsx`;
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export interface MasterDataItem {
  id: number
  name: string
  item_category?: number
  hsn_sac_code?: number | string
  tax_rates?: number[]
}

export interface ItemCategory {
  id: number
  name: string
  item_count: number
}

/**
 * Fetch master data entries from the ERP (Supplier, Item Master, etc.).
 */
export async function fetchMasterData(
  screen: string,
  erpToken: string,
  erpTenantId: string,
): Promise<MasterDataItem[]> {
  const res = await fetch(`${PROXY}?path=master-data`, withCsrf({
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      screen,
      erp_token: erpToken,
      erp_tenant_id: erpTenantId,
    }),
  }));
  if (!res.ok) throw new Error(`Master data fetch failed: HTTP ${res.status}`);
  const data = await res.json();
  return data.items || [];
}

/**
 * Fetch Item Categories with live item counts, sorted by count descending.
 */
export async function fetchItemCategories(
  erpToken: string,
  erpTenantId: string,
): Promise<ItemCategory[]> {
  const res = await fetch(`${PROXY}?path=item-categories`, withCsrf({
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      erp_token: erpToken,
      erp_tenant_id: erpTenantId,
    }),
  }));
  if (!res.ok) throw new Error(`Item categories fetch failed: HTTP ${res.status}`);
  const data = await res.json();
  return data.categories || [];
}


