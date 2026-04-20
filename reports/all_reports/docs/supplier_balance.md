# Supplier Balance Report Module Reference (`supplier_balance.py`)

This module automates the **Supplier Balance** report generation in the FPC ERP system. It navigates to the Reports page, selects "Supplier Balance", fills the required parameters (supplier name and file format), clicks **View** to load the report table, and finally triggers the **Download**.

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

### `select_report_name(driver, wait, report_name="Supplier Balance")`

Selects the desired report from the `report_name` dropdown. Returns `True` if the selection succeeds, `False` otherwise.

| Parameter | Type | Description |
|-----------|------|-------------|
| `report_name` | `str` | Exact or partial text of the report to select (default: `"Supplier Balance"`). |

---

### `fill_supplier_balance_form(driver, wait, data)`

Fills the Supplier Balance report parameter form.

| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | `dict` | Dictionary containing `supplier_name` and `file_format`. (Matches `test_data.supplier_balance_data`.) |

**Behavior:**
- Calls `select_report_name` to ensure the correct report is selected.
- Waits for the `supplier_ref_id` dropdown to appear (indicates form is ready).
- Maps fields: `supplier_name` (dropdown with ID `supplier_ref_id`) and `file_format` (dropdown with ID `file_format`).
- Uses `select_dropdown` with fallback strategies (by `control_id`, `control_name`, and `label_text`).

---

### `click_view(driver, wait)`

Clicks the **View** button to generate the report. Waits for any spinners/overlays to clear, clicks the button, waits 3 seconds, and confirms the report table (or `.report-container`) is present.

---

### `click_download(driver, wait)`

Clicks the **Download** button (targeting either a button containing "Download" or a button with class `apply` and text "Download") and waits 4 seconds for the download to initiate.

---

### `run(driver, wait, data)`

Orchestrates the complete report workflow:

1. Navigate to Reports page (`go_to_reports_page`).
2. Fill the form (`fill_supplier_balance_form`).
3. Click View (`click_view`).
4. Click Download (`click_download`).

| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | `dict` | Report parameters (must match the structure of `supplier_balance_data`). |

---

## Logging

All actions are logged with timestamps and severity levels (`INFO`, `WARNING`, `ERROR`).

**Example Console Output:**
10:30:12 | INFO | Navigating to Reports page...
10:30:14 | INFO | ✅ Success overlays cleared.
10:30:15 | INFO | ✅ Clicked All Reports menu
10:30:17 | INFO | ✅ Reports page loaded.
10:30:17 | INFO | 🔽 Selecting Report Name: Supplier Balance...
10:30:19 | INFO | ✅ Selected report: Supplier Balance
10:30:20 | INFO | 📝 Filling Supplier Balance form...
10:30:21 | INFO | ✅ Base form rendered.
10:30:22 | INFO | ➡️ Selecting supplier_ref_id: Ved_Supplies-9309316566|Supplier
10:30:24 | INFO | ✅ Selected: Ved_Supplies-9309316566|Supplier
10:30:25 | INFO | ➡️ Selecting file_format: EXCEL
10:30:27 | INFO | ✅ Selected: EXCEL
10:30:28 | INFO | ✅ Form filling complete.
10:30:28 | INFO | ✅ View button clicked
10:30:29 | INFO | ⏳ Waiting for report table to load...
10:30:32 | INFO | ✅ Report table loaded.
10:30:33 | INFO | ✅ Download triggered successfully.

text

## Usage Example

```python
from reports.supplier_balance import run
from data.test_data import supplier_balance_data

def test_supplier_balance(driver, wait):
    run(driver, wait, supplier_balance_data)
Maintenance Notes
Report Name: The default report_name is "Supplier Balance". Update the string in select_report_name and fill_supplier_balance_form if the UI text changes.

Supplier Dropdown: The field uses ID supplier_ref_id. If the HTML ID changes, update the field map in fill_supplier_balance_form.

Download Button: The XPath covers common button variations. Adjust if the download button design changes.