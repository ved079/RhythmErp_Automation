# Sales Order Status Report Module Reference (`sales_order_status.py`)

This module automates the **Sales Order Status** report generation in the FPC ERP system. It navigates to the Reports page, selects "Sales Order Status", fills all relevant parameters (customer, division, department, date ranges, status filters, and file format), clicks **View** to load the report table, and finally triggers the **Download**.

## Helper Functions

### `select_dropdown(driver, wait, value, control_name=None, label_text=None, control_id=None)`

**Enhanced** dropdown selection with automatic search‑box detection. It opens the dropdown, checks for a search input, filters if present, and clicks the option using JavaScript to avoid interception.

| Parameter | Type | Description |
|-----------|------|-------------|
| `value` | `str` | Text of the option to select (partial match allowed). |
| `control_name` | `str` | `formcontrolname` attribute of the `mat-select`. |
| `label_text` | `str` | Text of the `<mat-label>` associated with the dropdown. |
| `control_id` | `str` | HTML `id` attribute of the `mat-select`. |

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

### `select_report_name(driver, wait, report_name="Sales Order Status")`

Selects the desired report from the `report_name` dropdown. Returns `True` if the selection succeeds, `False` otherwise.

| Parameter | Type | Description |
|-----------|------|-------------|
| `report_name` | `str` | Exact or partial text of the report to select (default: `"Sales Order Status"`). |

---

### `fill_sales_order_status_form(driver, wait, data)`

Fills the Sales Order Status report parameter form. This is the most comprehensive report form with many optional fields.

| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | `dict` | Dictionary containing `customer_name`, `division`, `department`, `type_of_sale`, `location`, `lot_status`, `dispatch_status`, `invoice_status`, `receipt_status`, `file_format`, `from_date`, `to_date`. (Matches `test_data.sales_order_status_data`.) |

**Behavior:**
- Calls `select_report_name` to ensure the correct report is selected.
- Iterates through a predefined field map and attempts to fill each field if the data value is provided.
- For dropdowns, uses `select_dropdown` with fallback to `label_text`.
- For inputs, uses `fill_input`.
- **Resilience**: If a field fails to fill, it logs a warning and continues to the next field (the form may still be functional without it).

---

### `click_view(driver, wait)`

Clicks the **View** button to generate the report. Waits for any spinners/overlays to clear, clicks the button, waits 5 seconds (longer due to report complexity), and confirms the report table (or `.report-container`) is present.

---

### `click_download(driver, wait)`

Enhanced download function that:
1. Ensures the file format is set to **Excel** (selects it if not already).
2. Clicks the **Download** button.
3. Waits 5 seconds for the download to initiate.

---

### `run(driver, wait, data)`

Orchestrates the complete report workflow:

1. Navigate to Reports page (`go_to_reports_page`).
2. Fill the form (`fill_sales_order_status_form`).
3. Click View (`click_view`).
4. Click Download (`click_download`).

| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | `dict` | Report parameters (must match the structure of `sales_order_status_data`). |

---

## Logging

All actions are logged with timestamps and severity levels (`INFO`, `WARNING`, `ERROR`).

**Example Console Output:**
11:15:22 | INFO | Navigating to Reports page...
11:15:24 | INFO | ✅ Success overlays cleared.
11:15:25 | INFO | ✅ Clicked All Reports menu
11:15:27 | INFO | ✅ Reports page loaded.
11:15:27 | INFO | 🔽 Selecting Report Name: Sales Order Status...
11:15:29 | INFO | ✅ Selected report: Sales Order Status
11:15:31 | INFO | 📝 Filling Sales Order Status form...
11:15:32 | INFO | ➡️ Selecting customer_id: Ved_Enterprises-9309316566|Customer
11:15:34 | INFO | ✅ Selected: Ved_Enterprises-9309316566|Customer
11:15:35 | INFO | ➡️ Selecting division_ref_id: HR
11:15:37 | INFO | ✅ Selected: HR
11:15:38 | INFO | ➡️ Typing in from_date: 01/01/2026
11:15:40 | INFO | ✅ Filled from_date: 01/01/2026
11:15:41 | INFO | ➡️ Typing in to_date: 07/04/2026
11:15:43 | INFO | ✅ Filled to_date: 07/04/2026
11:15:44 | INFO | ✅ Form filling complete.
11:15:44 | INFO | ✅ View button clicked
11:15:45 | INFO | ⏳ Waiting for report table to load...
11:15:50 | INFO | ✅ Report table loaded.
11:15:51 | INFO | ✅ Selected Excel format
11:15:52 | INFO | ✅ Download button clicked
11:15:57 | INFO | ✅ Download triggered successfully.

text

## Usage Example

```python
from reports.sales_order_status import run
from data.test_data import sales_order_status_data

def test_sales_order_status(driver, wait):
    run(driver, wait, sales_order_status_data)
Maintenance Notes
Report Name: The default report_name is "Sales Order Status". Update the string in select_report_name and fill_sales_order_status_form if the UI text changes.

Field Map: The extensive fields list in fill_sales_order_status_form defines all possible parameters. If the UI adds or removes fields, update this list.

Dropdown Resilience: The function tries multiple locator strategies and gracefully skips fields that fail, ensuring the test doesn't crash on optional parameters.

Download Format: The click_download function explicitly sets the format to Excel. If this behavior is not desired, remove or modify the format‑setting block.

text
