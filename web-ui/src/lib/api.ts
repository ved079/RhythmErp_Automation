/**
 * API helper — all calls to the FastAPI backend go through the Next.js proxy.
 * This avoids CORS issues since the proxy runs server-side.
 */

const PROXY = "/api/proxy";

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

// --- GET helpers ---

export async function fetchModules(): Promise<ApiModule[]> {
  const res = await fetch(`${PROXY}?path=modules`);
  const data = await res.json();
  return data.modules || [];
}

export async function fetchRuns(): Promise<ApiRunListItem[]> {
  const res = await fetch(`${PROXY}?path=runs`);
  const data = await res.json();
  return data.runs || [];
}

export async function fetchRunDetail(runId: string): Promise<ApiRunDetail> {
  const res = await fetch(`${PROXY}?path=runs/${runId}`);
  return res.json();
}

// --- Stop a running test ---
export async function stopRun(runId: string): Promise<void> {
  const res = await fetch(`${PROXY}?path=runs/${runId}/stop`, { method: "POST" });
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

// --- Delete a run ---

export async function deleteRun(runId: string): Promise<void> {
  const res = await fetch(`${PROXY}?path=runs/${runId}`, { method: "DELETE" });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || data.error || `HTTP ${res.status}`);
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
}

/**
 * Start a test run and return an EventSource-like stream.
 * Uses fetch + ReadableStream since EventSource doesn't support POST.
 */
export async function startRun(
  module: string,
  subModule: string | null = null,
  tests: string[] | null = null,
  onEvent: (event: SSEEvent) => void,
  onDone: () => void,
  onError: (err: Error) => void
) {
  try {
    const res = await fetch(`${PROXY}?path=runs/start`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        module,
        sub_module: subModule,
        tests,
      }),
    });

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

// --- Module name mapping ---

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
  farmer: "farmer",
  customer: "customer",
  supplier: "supplier",
  agent: "agent",
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
      const registrationSubs = ["farmer", "customer", "supplier", "agent"];
      if (registrationSubs.includes(folder)) {
        return { module: "registration", subModule: folder };
      }
      return { module: folder, subModule: null };
    }
  }
  return null;

}

// ─── Test Cases Types & Fetch ──────────────────────────
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