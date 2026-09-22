# Pacs Automation — tools/

Reusable developer tooling for the Pacs Automation projectebb / ERP test suite. Each subfolder is a self-contained tool.

## Contents

| Tool | What it does |
|------|--------------|
| [`erp-recorder/`](erp-recorder/README.md) | Chrome (MV3) extension that records ERP interactions in your browser and generates **Playwright (Python)** test code / page objects. |

---

## ERP Playwright Recorder (`erp-recorder/`)

A browser extension that turns a manual walkthrough of the Angular/Material ERP into replayable Playwright Python code. It captures `mat-select` selections, text inputs, buttons, dialogs, SweetAlert2 prompts, readonly/computed fields, grid rows, tables, validation errors, and URL navigation.

### Install

1. Open `chrome://extensions` and enable **Developer mode**.
2. **Load unpacked** → select `tools/erp-recorder/`.
3. Pin the extension; open (or refresh) the ERP tab — the floating toolbar injects automatically.

### Use (30-second workflow)

1. Click **Start** on the toolbar.
2. Do one clean pass of the flow — navigate to the listing, open the Add form, fill every field, submit, confirm the success alert. Wait 1–2s between actions so Angular settles.
3. Click **Stop**, then open the **full view** (↗) or the popup.
4. **Copy** the code, or hit **Page Obj** to generate a page-object skeleton.

### What it records

| Interaction | Generated code |
|-------------|----------------|
| `mat-select` option pick | `_select_mat_option_by_text(page, "<label>", "<option>")` |
| Input / textarea change | `_val_fill(page, "<label>", "<value>")` |
| Flow button (Submit, Save, Add, Next…) | `page.locator(...).click()` (suite-compatible locators) |
| Dialog open/close | `wait_for_selector("mat-dialog-container"…)` steps |
| SweetAlert2 confirm/cancel | swal2 step with title + clicked button |
| Readonly / disabled / computed value | `# Assert field` + scoped locator assertion |
| Grid row menu (⋮) | locator scoped to record ref / row index |
| List table cell | cell-value assertion scoped to column + row |
| URL / route change | `page.goto(...)` navigate step |
| Validation errors (`mat-error`) | `# Validation error` comment + `assert …is_visible()` |

### Toolbar controls

- **Start/Stop/●** — toggle recording (persists across reloads & restarts)
- **Clear** — wipe steps
- **VIEW badge** — active in read-only View mode
- **Cap All** — capture every visible View field as assertions
- **📋 Table** — snapshot `table#excel-table` rows/cells as assertions
- **↗** — open full-view tab · **—** — minimize
- **Shift+click** a field to force-assert its value · click a table cell to assert it

### Full-view tab

- Steps list (chronological, newest first) + generated code pane
- Code grouped into phases: `NAVIGATE / FILL FORM / ACTION / VALIDATION / VERIFY` with stepper breadcrumbs
- Summary header: module, step/fill/error/readonly/nav counts, flow chain
- Buttons: **↺ Restart**, **Clear**, **↻ Regen**, **Copy**, **Page Obj**, **Start/Stop**

### Generated-code conventions

Matches the `pages/` suite style (`pages/base_playwright_page.py`):
- `xpath=//mat-form-field[.//mat-label[contains(.,'<label>')]]//input|mat-select` selectors
- `_fill_text`, `_click_next`, `_select_mat_option_by_text` helpers
- `assert page.locator(...)` for readonly fields, tables, validation errors
- Guarded `wait_for_selector(...)` waits after async selects/dialogs
- `# [AI NOTE]` comments where computed values must be read/reused downstream

### Files

| File | Purpose |
|------|---------|
| `manifest.json` | MV3 manifest |
| `content.js` | Core recorder (toolbar, capture, step model, codegen) |
| `background.js` | Content-script re-injection + full-view tab management |
| `popup.html` / `popup.js` | Mini popup control panel + code preview |
| `fullview.html` / `fullview.js` | Full-view tab + page-object generator |

### Tips

- **Record one clean pass** — duplicate consecutive steps are auto-suppressed.
- **Snapshot-first**: navigate → open Add → fill → capture table/cells → submit → confirm success.
- **Cap All** on a View form to capture every computed/readonly value as assertions.
- **Steppers**: errors are annotated per stepper step; "no errors" notes are emitted on the last step.
- Regen from recorded steps anytime you've hand-edited the code and want recorder-faithful output.

See [`erp-recorder/README.md`](erp-recorder/README.md) for the detailed per-tool docs.
