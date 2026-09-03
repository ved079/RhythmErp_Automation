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
  created?: number;
  total?: number;
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
  selectedLocationIds?: number[],
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
        ...(selectedLocationIds?.length ? { selected_location_ids: selectedLocationIds } : {}),
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
  supplierRefIds?: number[],
  qcDiscount?: boolean,
  customerRefId?: number | null,
  isRateWeightDeduction?: boolean,
  withJVCheck?: boolean,
  supplierRefType?: string,
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
        supplier_ref_ids: supplierRefIds?.length ? supplierRefIds : undefined,
        qc_discount: qcDiscount ?? false,
        customer_ref_id: customerRefId ?? null,
        is_rate_weight_deduction: isRateWeightDeduction ?? false,
        with_jv_check: withJVCheck ?? false,
        supplier_ref_type: supplierRefType ?? "Supplier",
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

// ─── PB List ────────────────────────────────────────────

export interface PBListItem {
  id: string | number;
  ref_no: string;
  date: string;
  supplier: string;
  amount: string | number;
  taxable_amount?: string | number;
  discount_amount?: string | number;
  division: string;
  department: string;
  type_of_sale: string;
  location: string;
}

export interface PBItemLine {
  item_ref_id: number | null;
  name: string;
  quantity: string | number;
  rate: string | number;
  amount: string | number;
  igst_amount?: number | null;
  cgst_amount?: number | null;
  sgst_amount?: number | null;
  gst_type?: string;
}

export async function fetchPBList(erpToken: string, erpTenantId: string): Promise<PBListItem[]> {
  const res = await fetch(`${PROXY}?path=pb-list`, withCsrf({
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ erp_token: erpToken, erp_tenant_id: erpTenantId }),
  }))
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  const data = await res.json()
  return data.pbs ?? []
}

export interface PBItemsResult {
  items: PBItemLine[];
  taxable_amount: number | null;
  discount_amount: number | null;
}

export async function fetchPBItems(erpToken: string, erpTenantId: string, pbId: string | number): Promise<PBItemsResult> {
  const res = await fetch(`${PROXY}?path=pb-items`, withCsrf({
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ erp_token: erpToken, erp_tenant_id: erpTenantId, pb_id: String(pbId) }),
  }))
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  const data = await res.json()
  return { items: data.items ?? [], taxable_amount: data.taxable_amount ?? null, discount_amount: data.discount_amount ?? null }
}

// ─── QC Fetch ───────────────────────────────────────────

export async function fetchQC(erpToken: string, erpTenantId: string, qcId: string): Promise<any> {
  const res = await fetch(`${PROXY}?path=qc-fetch`, withCsrf({
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ erp_token: erpToken, erp_tenant_id: erpTenantId, qc_id: qcId }),
  }))
  if (!res.ok) throw new Error(`HTTP ${res.status}`)
  return res.json()
}

// ─── JV Verify ──────────────────────────────────────────

export interface JVVerifyStep {
  n: number;
  label: string;
  ok: boolean;
  detail?: string;
  fields?: { field: string; value: string }[];
}

export interface PurbMeta {
  transaction_date: string;
  fiscal_year: string;
  period: string;
}

export interface JVVerifyResponse {
  steps: JVVerifyStep[];
  ok: boolean;
  account_rows?: { account_name: string; dr_cr: string; commodity: string; amount: number | null }[];
  purb_meta?: PurbMeta;
}

// ── Cross-Check types ──────────────────────────────────────────────────────

export interface CrossCheckJvRow {
  account_name: string;
  dr_cr: string;
  commodity: string;
  amount: number;
}

export interface CrossCheckCheck {
  id: string;
  label: string;
  ok: boolean;
  detail: string;
  category: string;
}

export interface CrossCheckAmountChain {
  label: string;
  amount: number;
  sign: string | null;
  source: string;
  note?: string;
  cross?: { purb?: number; inv?: number };
  ok?: boolean;
}

export interface CrossCheckCommodityRow {
  commodity: string;
  pb_taxable: number | null;
  pb_gst_total: number | null;
  purb_purchase_gst: number | null;
  purb_igst: number | null;
  purb_cgst: number | null;
  purb_sgst: number | null;
  purb_gst_total: number | null;
  inv_exempt_cr: number | null;
  inv_closing_dr: number | null;
  taxable_match: boolean;
  pb_vs_purb_ok: boolean | null;
  inv_balanced: boolean;
  purb_purchase_account: string | null;
  inv_purchase_account: string | null;
  account_match: boolean | null;
}

export interface CrossCheckPBItem {
  item_no: number;
  item_ref_id: number;
  hsn_sac_no: number | null;
  taxable: number;
  gross_no_disc: number;
  discount_pct: number;
  discount_amt: number;
  gst_type: string;
  igst: number;
  cgst: number;
  sgst: number;
  gst_total: number;
  igst_rate: number;
  cgst_rate: number;
  sgst_rate: number;
  gst_rate: number;
  total: number;
  empty_bags_amt: number;
  qc_deduction: number;
  net_of_empty: number;
  total_amount: number;
  item_ok: boolean;
}

export interface CrossCheckResponse {
  ok: boolean;
  error?: string;
  pb_ref_no: string;
  inv_ref_no: string;
  pb_meta: {
    transaction_date: string;
    fiscal_year: string;
    period: string;
    taxable: number;
    total: number;
    discount: number;
    tds: number;
    gst_total: number;
    igst: number;
    cgst: number;
    sgst: number;
    item_count: number;
  };
  purb_jv: {
    found: boolean;
    status: string;
    transaction_date: string;
    fiscal_year: string;
    period: string;
    total_dr: number;
    payable: number;
    purchase_gst_dr: number;
    gst_dr: number;
    igst_dr: number;
    cgst_dr: number;
    sgst_dr: number;
    rows: CrossCheckJvRow[];
  };
  inv_jv: {
    found: boolean;
    status: string;
    ref_no: string;
    transaction_date: string;
    fiscal_year: string;
    period: string;
    total_dr: number;
    exempt_cr: number;
    closing_dr: number;
    rows: CrossCheckJvRow[];
  };
  checks: CrossCheckCheck[];
  amount_chain: CrossCheckAmountChain[];
  commodity_rows: CrossCheckCommodityRow[];
  pb_items: CrossCheckPBItem[];
}

export async function crossCheckJV(
  erpToken: string,
  erpTenantId: string,
  pbRefNo: string,
  pbId: string,
): Promise<CrossCheckResponse> {
  const res = await fetch(`${PROXY}?path=cross-check-jv`, withCsrf({
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ erp_token: erpToken, erp_tenant_id: erpTenantId, pb_ref_no: pbRefNo, pb_id: pbId }),
  }));
  if (!res.ok) throw new Error(`cross-check-jv failed: ${res.status}`);
  return res.json();
}

export async function verifyJV(
  erpToken: string,
  erpTenantId: string,
  pbRefNo: string,
): Promise<JVVerifyResponse> {
  const res = await fetch(`${PROXY}?path=jv-verify`, withCsrf({
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ erp_token: erpToken, erp_tenant_id: erpTenantId, pb_ref_no: pbRefNo }),
  }));
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

// ─── Inventory JV Verify ─────────────────────────────────

export interface InvPBItem {
  item_ref_id: number;
  name: string;
  taxable_amount: number;
}

export interface InvJVRow {
  item_name: string;
  in_quantity: string | null;
  in_amount: string | null;
  closing_quantity: string | null;
  closing_amount: string | null;
  inv_ref_no: string;
}

export interface InvCommodityRow {
  commodity: string;
  purb_purchase_exempt_dr: number | null;
  inv_closing_stock_dr: number | null;
  inv_purchase_exempt_cr: number | null;
  match: boolean;
}

export interface JVMeta {
  purb_txn_date: string;
  purb_fiscal_year: string;
  purb_period: string;
  inv_txn_date: string;
  inv_fiscal_year: string;
  inv_period: string;
}

export interface InvJVVerifyResponse {
  steps: JVVerifyStep[];
  ok: boolean;
  pb_items: InvPBItem[];
  jv_rows: { account_name: string; dr_cr: string; commodity: string; amount: number | null }[];
  purb_rows: { account_name: string; dr_cr: string; commodity: string; amount: number | null }[];
  commodity_rows: InvCommodityRow[];
  inv_ref?: string;
  jv_meta?: JVMeta;
}

export async function verifyInvJV(
  erpToken: string,
  erpTenantId: string,
  pbRefNo: string,
  pbDate: string,
  pbId: string | number,
): Promise<InvJVVerifyResponse> {
  const res = await fetch(`${PROXY}?path=inv-jv-verify`, withCsrf({
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ erp_token: erpToken, erp_tenant_id: erpTenantId, pb_ref_no: pbRefNo, pb_date: pbDate, pb_id: String(pbId) }),
  }));
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

// ─── Accounting Definition ──────────────────────────────

export interface AccountingDefDetail {
  id: number;
  account_ref_id: number;
  account_name: string;
  dr_cr: 'Debit' | 'Credit';
  has_conditions: boolean;
  condition_text: string;
}

export interface AccountingDefResponse {
  id: number;
  name: string;
  transaction_type_id: string;
  details: AccountingDefDetail[];
}

export async function fetchAccountingDef(
  erpToken: string,
  erpTenantId: string,
  transactionTypeId = '5',
): Promise<AccountingDefResponse> {
  const res = await fetch(`${PROXY}?path=accounting-def`, withCsrf({
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ erp_token: erpToken, erp_tenant_id: erpTenantId, transaction_type_id: transactionTypeId }),
  }));
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
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

/**
 * Fetch the set of Item Master IDs that have a Commodity Quality Parameter
 * (CQP) entry configured. The QC step 500s on items without a CQP entry, so
 * the Purchase Chain UI restricts item selection to this set.
 */
export async function fetchItemsWithCqp(
  erpToken: string,
  erpTenantId: string,
): Promise<number[]> {
  const res = await fetch(`${PROXY}?path=items-with-cqp`, withCsrf({
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      erp_token: erpToken,
      erp_tenant_id: erpTenantId,
    }),
  }));
  if (!res.ok) throw new Error(`Items-with-CQP fetch failed: HTTP ${res.status}`);
  const data = await res.json();
  return data.item_ids || [];
}

export interface CqpFillResult {
  created: { id: number; entry_id?: number }[]
  skipped: { id: number; reason?: string }[]
  failed: { id: number; reason?: string }[]
  total: number
}

/**
 * Create Commodity Quality Parameter (CQP) entries for the given item IDs.
 * The QC step 500s on items without a CQP entry, so the UI calls this to
 * auto-fill any missing entries before a run.
 */
export async function fillCqpItems(
  erpToken: string,
  erpTenantId: string,
  itemIds: number[],
): Promise<CqpFillResult> {
  const res = await fetch(`${PROXY}?path=cqp-fill`, withCsrf({
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      erp_token: erpToken,
      erp_tenant_id: erpTenantId,
      item_ids: itemIds,
    }),
  }));
  if (!res.ok) throw new Error(`CQP fill failed: HTTP ${res.status}`);
  const data = await res.json();
  return {
    created: data.created || [],
    skipped: data.skipped || [],
    failed: data.failed || [],
    total: data.total ?? itemIds.length,
  };
}


