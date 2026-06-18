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
  type: "log" | "test_end" | "run_end" | "error";
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
  onError: (err: Error) => void
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

    const res = await fetch('/api/runs', withCsrf({
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        moduleId: summary.subModule || summary.module,
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
 * Sync modules from FastAPI to Next.js DB.
 * Called when modules are fetched, keeps the TestModule table up to date.
 */
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

// ─── Module name mapping ────────────────────────────────

/**
 * Map sub-module folder names to sidebar module IDs.
 * e.g. "season" → "seasons", "error_code_mst" → "error-code-master"
 */
const FOLDER_TO_SIDEBAR: Record<string, string> = {
  login_screens: "login",
  access_screen: "access",
  company_onboarding: "company-onboarding",
  common_settings: "common-settings",
  commodity_settings: "commodity-settings",
  bank: "bank",
  designation: "designation",
  error_code_mst: "error-code-master",
  hsn_sac: "hsn-sac",
  season: "seasons",
  tax_authority: "tax-authority",
  tax_rate: "tax-rate",
  uom: "uom",
  uom_conversion: "uom-conversion",
  vehicle_master: "vehicle-master",
  crop_master: "crop-master",
  item_master: "item-master",
  quality_parameter_master: "quality-parameter-def",
  services_master: "services-master",
  item_category: "item-category",
  item_group: "item-group",
  commodity_quality_parameter: "commodity-quality-param",
  item_attribute: "item-attribute",
  commodity_base_rate: "commodity-base-rate",
  entity_group_definition: "entity-group",
  entity_group: "entity-group",
  role_creation_screen: "role-creation",
  role_creation: "role-creation",
  user_creation: "user-creation",
  // Registration sub-modules
  registration: "registration",
  employee: "employee",
  farmer: "farmer",
  customer: "customer",
  supplier: "supplier",
  agent: "agent",
  // Document sub-modules
  directors: "directors",
  member: "member",
  constituent_documents: "constituent-documents",
  miscellaneous_documents: "miscellaneous-documents",
  register_of_loan: "register-of-loan",
  register_charges: "register-charges",
  // Private (B2B) / Purchase sub-modules
  purchase_order: "purchase-order",
  goods_receipt_note: "goods-receipt-note",
  gate_pass: "gate-pass",
  quality_check: "quality-check",
};

export function folderToSidebarId(folderName: string): string {
  return FOLDER_TO_SIDEBAR[folderName] || folderName;
}

export function sidebarToFolderMapping(sidebarId: string): { module: string; subModule: string | null } | null {
  // Reverse lookup
  for (const [folder, id] of Object.entries(FOLDER_TO_SIDEBAR)) {
    if (id === sidebarId) {
      // Determine if it's a top-level module or sub-module
      const topModules = ["login_screens", "company_onboarding", "common_settings", "commodity_settings", "registration"];
      if (topModules.includes(folder)) {
        return { module: folder, subModule: null };
      }
      // It's a sub-module — figure out parent
      const commonSubs = ["bank", "designation", "error_code_mst", "hsn_sac", "season", "tax_authority", "tax_rate", "uom", "uom_conversion", "vehicle_master"];
      if (commonSubs.includes(folder)) {
        return { module: "common_settings", subModule: folder };
      }
      const commoditySubs = ["crop_master", "item_master", "quality_parameter_master", "services_master", "item_category", "item_group", "commodity_quality_parameter", "commodity_base_rate", "item_attribute"];
      if (commoditySubs.includes(folder)) {
        return { module: "commodity_settings", subModule: folder };
      }
      const accessSubs = ["entity_group", "entity_group_definition", "role_creation", "role_creation_screen", "user_creation"];
      if (accessSubs.includes(folder)) {
        return { module: "access", subModule: folder };
      }
      const registrationSubs = ["employee", "farmer", "customer", "supplier", "agent"];
      if (registrationSubs.includes(folder)) {
        return { module: "registration", subModule: folder };
      }
      const documentSubs = ["directors", "member", "constituent_documents", "miscellaneous_documents", "register_of_loan", "register_charges"];
      if (documentSubs.includes(folder)) {
        return { module: "document", subModule: folder };
      }
      const purchaseSubs = ["purchase_order", "goods_receipt_note", "gate_pass", "quality_check"];
      if (purchaseSubs.includes(folder)) {
        return { module: "private_b2b", subModule: folder };
      }
      return { module: folder, subModule: null };
    }
  }
  return null;
}
