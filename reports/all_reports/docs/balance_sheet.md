# Balance Sheet Report Module Reference (`balance_sheet.py`)

This module automates the **Balance Sheet** report generation in the FPC ERP system. It navigates to the Reports page, selects "Balance Sheet", fills the required parameters (level, view type, file format, amount unit conversion, and transaction date), clicks **View** to load the report table, and finally triggers the **Download**.

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

### `fill_input(driver, wait, value, control_name=None, control_id=None)`

Fills a text input or datepicker field, bypassing Angular restrictions by using `Ctrl+A`, `Backspace`, type, and `Tab`.

| Parameter | Type | Description |
|-----------|------|-------------|
| `value` | `str` | Text or number to enter. |
| `control_name` | `str` | `formcontrolname` attribute of the `<input>`. |
| `control_id` | `str` | HTML `id` attribute of the `<input>`. |

---

### `go_to_reports_page(driver, wait)`

Navigates to the main Reports hub. Waits for any overlays to clear, scrolls to the top, clicks the "All Reports" menu (expanding if necessary), and confirms the page has loaded by waiting for the `report_name` dropdown.

---

### `select_report_name(driver, wait, report_name="Balance Sheet")`

Selects the desired report from the `report_name` dropdown. Returns `True` if the selection succeeds, `False` otherwise.

| Parameter | Type | Description |
|-----------|------|-------------|
| `report_name` | `str` | Exact or partial text of the report to select (default: `"Balance Sheet"`). |

---

### `fill_balance_sheet_form(driver, wait, data)`

Fills the Balance Sheet report parameter form.

| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | `dict` | Dictionary containing `level`, `view_type`, `file_format`, `amount_unit_conversion`, and `transaction_date`. (Matches `test_data.balance_sheet_data`.) |

**Behavior:**
- Calls `select_report_name` to ensure the correct report is selected.
- Waits for the `level` dropdown to appear (indicates form is ready).
- Maps fields: `level` (dropdown with ID `level`), `view_type` (dropdown with ID `view_type`), `file_format` (dropdown with ID `file_format`), `amount_unit_conversion` (dropdown with ID `unit_convertor`), and `transaction_date` (input with ID `transaction_date`).
- Uses `select_dropdown` and `fill_input` with fallback strategies (by `control_id`, `control_name`, and non‑searchable).

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
2. Fill the form (`fill_balance_sheet_form`).
3. Click View (`click_view`).
4. Click Download (`click_download`).

| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | `dict` | Report parameters (must match the structure of `balance_sheet_data`). |

---

## Logging

All actions are logged with timestamps and severity levels (`INFO`, `WARNING`, `ERROR`).

**Example Console Output:**

```
11:15:30 | INFO     | Navigating to Reports page...
11:15:32 | INFO     |    ✅ Success overlays cleared.
11:15:33 | INFO     |    ✅ Clicked All Reports menu
11:15:35 | INFO     | ✅ Reports page loaded.
11:15:35 | INFO     |    🔽 Selecting Report Name: Balance Sheet...
11:15:37 | INFO     |       ✅ Selected report: Balance Sheet
11:15:38 | INFO     | 📝 Filling Balance Sheet form...
11:15:39 | INFO     |    ⏳ Waiting for level dropdown to appear...
11:15:40 | INFO     |    ✅ Base form rendered.
11:15:41 | INFO     | ➡️ Selecting level: Category
11:15:43 | INFO     |    ✅ Selected: Category
11:15:44 | INFO     | ➡️ Selecting view_type: Vertical
11:15:46 | INFO     |    ✅ Selected: Vertical
11:15:47 | INFO     | ➡️ Selecting file_format: EXCEL
11:15:49 | INFO     |    ✅ Selected: EXCEL
11:15:50 | INFO     | ➡️ Selecting unit_convertor: Lakh
11:15:52 | INFO     |    ✅ Selected: Lakh
11:15:53 | INFO     | ➡️ Typing in transaction_date: 07/04/2026
11:15:55 | INFO     |    ✅ Filled transaction_date: 07/04/2026
11:15:56 | INFO     | ✅ Form filling complete.
11:15:56 | INFO     |    ✅ View button clicked
11:15:57 | INFO     | ⏳ Waiting for report table to load...
11:16:00 | INFO     | ✅ Report table loaded.
11:16:01 | INFO     | ✅ Download triggered successfully.
```

## Usage Example

```python
from reports.balance_sheet import run
from data.test_data import balance_sheet_data

def test_balance_sheet(driver, wait):
    run(driver, wait, balance_sheet_data)
```

## Maintenance Notes

- **Report Name**: The default `report_name` is `"Balance Sheet"`. Update the string in `select_report_name` and `fill_balance_sheet_form` if the UI text changes.
- **Field Map**: The `field_map` in `fill_balance_sheet_form` defines the HTML IDs for each parameter. If the UI changes (e.g., `level` becomes `account_level`), update the map accordingly.
- **Amount Unit Conversion Dropdown**: The dropdown uses ID `unit_convertor`. Ensure this matches the actual HTML.
- **Download Button**: The XPath covers common button variations. Adjust if the download button design changes.
```