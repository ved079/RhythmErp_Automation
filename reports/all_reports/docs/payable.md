# Payable Report Module Reference (`payable.py`)

This module automates the **Payable** report generation in the FPC ERP system. It navigates to the Reports page, selects "Payable", sets the file format, clicks **View** to load the report table, and finally triggers the **Download**.

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

### `select_report_name(driver, wait, report_name="Payable")`

Selects the desired report from the `report_name` dropdown. Returns `True` if the selection succeeds, `False` otherwise.

| Parameter | Type | Description |
|-----------|------|-------------|
| `report_name` | `str` | Exact or partial text of the report to select (default: `"Payable"`). |

---

### `fill_payable_form(driver, wait, data)`

Fills the Payable report parameter form.

| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | `dict` | Dictionary containing `file_format`. (Matches `test_data.payable_data`.) |

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

### `run_payable(driver, wait, data)`

Orchestrates the complete report workflow:

1. Navigate to Reports page (`go_to_reports_page`).
2. Fill the form (`fill_payable_form`).
3. Click View (`click_view`).
4. Click Download (`click_download`).

| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | `dict` | Report parameters (must match the structure of `payable_data`). |

---

## Logging

All actions are logged with timestamps and severity levels (`INFO`, `WARNING`, `ERROR`).

**Example Console Output:**

```
14:30:22 | INFO     | Navigating to Reports page...
14:30:24 | INFO     |    ✅ Success overlays cleared.
14:30:25 | INFO     |    ✅ Clicked All Reports menu
14:30:27 | INFO     | ✅ Reports page loaded.
14:30:27 | INFO     |    🔽 Selecting Report Name: Payable...
14:30:29 | INFO     |       ✅ Selected report: Payable
14:30:30 | INFO     | 📝 Filling Payable form (Fast-Track)...
14:30:31 | INFO     |    ⏳ Waiting for form to initialize...
14:30:32 | INFO     |    ✅ Base form rendered.
14:30:33 | INFO     | ➡️ Selecting file_format: EXCEL
14:30:35 | INFO     |    ✅ Selected: EXCEL
14:30:36 | INFO     | ✅ Form filling complete.
14:30:36 | INFO     |    ✅ View button clicked
14:30:37 | INFO     | ⏳ Waiting for report table to load...
14:30:40 | INFO     | ✅ Report table loaded.
14:30:41 | INFO     | ✅ Download triggered successfully.
```

## Usage Example

```python
from reports.payable import run_payable
from data.test_data import payable_data

def test_payable(driver, wait):
    run_payable(driver, wait, payable_data)
```

## Maintenance Notes

- **Report Name**: The default `report_name` is `"Payable"`. Update the string in `select_report_name` and `fill_payable_form` if the UI text changes.
- **File Format Dropdown**: The field uses ID `file_format`. If the HTML ID changes, update the `select_dropdown` call in `fill_payable_form`.
- **Form Simplicity**: This report only requires file format; no date ranges or other filters. If additional parameters are added to the UI, extend the `fill_payable_form` function accordingly.
```