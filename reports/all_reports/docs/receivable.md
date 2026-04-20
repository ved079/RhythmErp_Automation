# Receivable Report Module Reference (`receivable.py`)

This module automates the **Receivable** report generation in the FPC ERP system. It navigates to the Reports page, selects "Receivable", sets the file format, clicks **View** to load the report table, and finally triggers the **Download**.

## Functions

### `select_dropdown(driver, wait, value, control_name=None, label_text=None, control_id=None, searchable=True)`

Universal dropdown selection for Angular Material `mat-select` components. Handles both searchable and simple dropdowns.

| Parameter | Type | Description |
|-----------|------|-------------|
| `value` | `str` | Text of the option to select (partial match allowed). |
| `control_name` | `str` | `formcontrolname` attribute of the `mat-select`. |
| `label_text` | `str` | Text of the `<mat-label>` associated with the dropdown. |
| `control_id` | `str` | HTML `id` attribute of the `mat-select`. |
| `searchable` | `bool` | If `True`, types `value` into the overlay search box before selecting. |

---

### `go_to_reports_page(driver, wait)`

Navigates to the main Reports hub. Waits for any overlays to clear, scrolls to the top, clicks the "All Reports" menu (expanding if necessary), and confirms the page has loaded by waiting for the `report_name` dropdown.

---

### `select_report_name(driver, wait, report_name="Receivable")`

Selects the desired report from the `report_name` dropdown. Returns `True` if the selection succeeds, `False` otherwise.

| Parameter | Type | Description |
|-----------|------|-------------|
| `report_name` | `str` | Exact or partial text of the report to select (default: `"Receivable"`). |

---

### `fill_receivable_form(driver, wait, data)`

Fills the Receivable report parameter form.

| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | `dict` | Dictionary containing `file_format`. (Matches `test_data.receivable_data`.) |

**Behavior:**
- Calls `select_report_name` to ensure the correct report is selected.
- Waits for the `file_format` dropdown to appear (indicates form is ready).
- Selects the file format using `select_dropdown` (non‑searchable, falls back to `control_name` if `control_id` fails).

---

### `click_view(driver, wait)`

Clicks the **View** button to generate the report. Waits for any spinners/overlays to clear, clicks the button, waits 3 seconds, and confirms the report table (or `.report-container`) is present.

---

### `click_download(driver, wait)`

Clicks the **Download** button (targeting either a button containing "Download" or a button with class `apply` and text "Download") and waits 4 seconds for the download to initiate.

---

### `run_rec(driver, wait, data)`

Orchestrates the complete report workflow:

1. Navigate to Reports page (`go_to_reports_page`).
2. Fill the form (`fill_receivable_form`).
3. Click View (`click_view`).
4. Click Download (`click_download`).

| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | `dict` | Report parameters (must match the structure of `receivable_data`). |

---

## Logging

All actions are logged with timestamps and severity levels (`INFO`, `WARNING`, `ERROR`).

**Example Console Output:**

```
14:10:15 | INFO     | Navigating to Reports page...
14:10:17 | INFO     |    ✅ Success overlays cleared.
14:10:18 | INFO     |    ✅ Clicked All Reports menu
14:10:20 | INFO     | ✅ Reports page loaded.
14:10:20 | INFO     |    🔽 Selecting Report Name: Receivable...
14:10:22 | INFO     |       ✅ Selected report: Receivable
14:10:23 | INFO     | 📝 Filling Receivable form (Fast-Track)...
14:10:24 | INFO     |    ⏳ Waiting for form to initialize...
14:10:25 | INFO     |    ✅ Base form rendered.
14:10:26 | INFO     | ➡️ Selecting file_format: EXCEL
14:10:28 | INFO     |    ✅ Selected: EXCEL
14:10:29 | INFO     | ✅ Form filling complete.
14:10:29 | INFO     |    ✅ View button clicked
14:10:30 | INFO     | ⏳ Waiting for report table to load...
14:10:33 | INFO     | ✅ Report table loaded.
14:10:34 | INFO     | ✅ Download triggered successfully.
```

## Usage Example

```python
from reports.receivable import run_rec
from data.test_data import receivable_data

def test_receivable(driver, wait):
    run_rec(driver, wait, receivable_data)
```

## Maintenance Notes

- **Report Name**: The default `report_name` is `"Receivable"`. Update the string in `select_report_name` and `fill_receivable_form` if the UI text changes.
- **File Format Dropdown**: The field uses ID `file_format`. If the HTML ID changes, update the `select_dropdown` call in `fill_receivable_form`.
- **Form Simplicity**: This report only requires file format; no date ranges or other filters. If additional parameters are added to the UI, extend the `fill_receivable_form` function accordingly.
```