# ERP Playwright Recorder

A Chrome (Manifest V3) extension that records your clicks, typing, and selections inside the Angular/Material ERP and converts them into executable **Playwright (Python)** test code — including form fills, dropdowns, buttons, dialogs, SweetAlert2 prompts, readonly/computed fields, grid rows, tables, validation errors, and URL navigation.

> Sibling doc: [`../README.md`](../README.md) (tools index). This file is the deep-dive.

---

## Show/hide

<details>
<summary>Design principles</summary>

- **Capture intent, generate Playwright** — the recorder reads the DOM (labels, values, states) and emits Python code in the style of the repo's `pages/` suite (`pages/base_playwright_page.py` + `po_playwright_page.py`).
- **Label-first locators** — every field is located via its `mat-label` text, matched case-sensitively, stable to Angular re-renders.
- **Readonly/computed aware** — disabled/readonly/`aria-readonly` fields are captured as **assertions** automatically after each action, so replay verifies them instead of editing them.
- **Validation-aware** — `mat-error` / `ng-invalid` fields are recorded per-field with the exact error text and scoped locators; stepper steps get "no validation errors" comments.
- **Row-aware** — grid fields with repeated labels (e.g. the same label across rows) use `.nth(row_index)`, and legacy row-index dedup keeps every fill.

</details>

## Installation

1. Open Chrome → go to `chrome://extensions`.
2. Toggle **Developer mode** (top-right).
3. Click **Load unpacked** and select the `tools/erp-recorder/` folder.
4. Pin the "ERP Playwright Recorder" extension to the toolbar if you like.
5. Open (or refresh) the ERP tab — the toolbar injects on load (also re-injected on install/startup via `background.js`).

## Quick start

1. Open the ERP page you want to automate.
2. Click **Start** on the toolbar (dot turns red, label shows `REC`).
3. Interact with the form exactly as the user would — click selects, type values, click buttons.
4. Do a **single clean pass**: navigate to the listing → open the Add form → fill every field → submit → confirm the success alert. Keep a steady pace (1–2s between actions so Angular settles); the recorder dedups repeat steps and auto-patches computed fields.
5. Click **Stop**.
6. Open the **full view** (↗) or the popup to read the generated code and **Copy** it (or generate a **Page Obj**).

### The on-page toolbar

| Control | What it does |
|---------|--------------|
| ● `Start` / `Stop` | Toggle recording. State persists via `chrome.storage.local` (survives reloads & restarts). |
| `Clear` | Wipe all recorded steps. |
| `↗` | Open the full-view tab. |
| `—` | Minimize to a dot (click the dot to restore). |
| `VIEW` badge | Lights up while a View (read-only) form is open; enters **view mode**. |
| `Cap All` | Capture every visible field on the current View form as grouped assertions under the View step. |
| `📋 Table` | Snapshot `table#excel-table` into a full assertion block (row count + every cell). |
| Toast | Bottom strip confirms each recorded step (`✓ label = "value"`). |

### The full view (`fullview.html`)

A dedicated tab with the recorded steps on the left and generated code on the right, re-rendered live:

- **Phase grouping** — code is organized under `# ═══ NAVIGATE / FILL FORM / ACTION / VALIDATION / VERIFY ═══` headers for readability.
- **Summary block** — module name, counts (steps / fills / errors / readonly / navs), flow chain, and comma-separated stepper labels.
- **Stepper breadcrumbs** — `# ── Stepper: <Label> (N/M) ──` inserted when multiple stepper steps exist.
- **Auto-patch grouping** — computed/readonly fields auto-filled by a selection are folded under the triggering step with a header comment.
- **Buttons** — `↺ Restart`, `Clear`, `↻ Regen` (discard manual edits, regenerate from steps), `Copy`, `Page Obj`, and Start/Stop.

### The popup (`popup.html`)

Compact control panel: recording toggle, step count, steps list, generated-code pane, and `Copy` / `Page Obj` / `↺ Restart` / `Clear`.

---

## What gets recorded (and the code it produces)

| Interaction | Generated code |
|-------------|----------------|
| **mat-select option pick** | `_select_mat_option_by_text(page, "<Label>", "<Option>")` (+ `# [dropdown]` hint) |
| **Text input / textarea fill** | `page.fill` / `_val_fill(page, "<Label>", "<value>")` (dedup by label+row) |
| **Inline search box** | Guarded search: open `#erpSearchInput`, fill, Enter |
| **Flow button** (Submit, Save, Update, Add, Next…) | Suite-compatible locators (`button.erp-add-btn`, `button.apply-button`, popup-footer, stepper next, paginator, …) |
| **Dialog open / close** | `wait_for_selector("mat-dialog-container"…)` steps |
| **SweetAlert2 confirm/cancel** | `swal2` step with dialog title + clicked button text |
| **Readonly / disabled / computed value** | `# Assert field: "<Label>" = "<value>"` + scoped locator assert |
| **Grid row action (⋮)** | Ref-scoped locator (or `.nth(idx)`) + menu-wait |
| **List table cell** | Column-scoped assertion for that cell (`td.cdk-column-… span`) |
| **URL / route change** | `page.goto` navigate step (auto-captured, including SPA hash routes) |
| **Validation errors (`mat-error`)** | `# Validation error` comment + `assert page.locator("xpath=…mat-error…")` |

**Key behaviors:**

- **Duplicate suppression** — identical consecutive steps are dropped, so you don't have to re-record the same action.
- **Stepper-aware** — only fields in the *active* stepper panel are recorded per phase; `mat-stepper-next` generates the mature `_click_next` helper; "No validation errors on [Step]" comments emit on last step.
- **Cascade selects** — State/Country/District/Taluka/Village get a `wait_for` before the following field, and computed autofills get guarded waits before Submit.
- **Shift+click** any field → force-record its current value as a readonly assert. **Click a table cell** (non-Actions) → assert that cell's value.

---

## Page-object generator ("Page Obj")

From the recorded steps it builds a skeleton matching `pages/base_playwright_page.py` + `po_playwright_page.py`: a class per module with `URL`, per-field `XPath` constants, `fill_form(data)`, `submit()`, `open_add_form()`, `navigate_to_page()`, `create_record(data)`, plus the proven `_fill_text`, `_click_next`, `_clear_overlays`, `_select_mat_option_by_text`, `_select_random_mat_option`, `_try_select_random_mat_option` helpers Jardance.

Constants are derived from labels (`toConstName`), and cascade-trigger selects insert nested waits.

---

## Tips

- **Record one clean pass** — the recorder tolerates duplicate steps and auto-patches, but a tidy pass yields the cleanest code.
- **Seeded-playback**: values are recorded verbatim; for computed/random values, follow the `# [AI NOTE]` and bind them into the data flow.
- **View-mode Verifications** — after opening a View form, click **Cap All** to snapshot every displayed readonly value as assertions (grouped under the View button step).
- **History count** — clicking a History button snapshots the new table's row count (or empty-state) as an assertion.
- **Regen vs hand-edit** — use **↻ Regen** to regenerate from steps after manual edits; use the code pane as scratch and **Copy** when done.

---

## File map

| File | Purpose |
|------|---------|
| `manifest.json` | MV3 manifest (host_permissions, content script, background, web-accessible fullview) |
| `content.js` | Core recorder — toolbar, DOM capture, step model, codegen (both per-step and full view) |
| `background.js` | Content-script re-injection on install/startup + fullview tab management |
| `popup.html` / `popup.js` | Compact popup UI (state, steps, code, copy, page object) |
| `fullview.html` / `fullview.js` | Full-view tab — steps list + generated code + page-object generator |

---

## Troubleshooting

- **Toolbar not on existing tabs** — refresh the page or reload the extension (background re-injects).
- **Field order oddities** — Angular async rendering: wait 1–2s; the recorder emits `wait_for_selector` guards for cascades and computed fields.
- **Select not captured** — use the mouse (mousedown/click on `mat-option`); keyboard-only selection is caught by the panel-close fallback.
- **Readonly number inputs** — read via native prototype getter / `valueAsNumber` / component `__ngContext__` probes (handled automatically).
