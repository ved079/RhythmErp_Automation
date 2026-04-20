# Inventory Summary Report Module Reference (`inventory_summary.py`)

This module automates the **Inventory Summary** report generation in the FPC ERP system. It navigates to the Reports page, selects "Inventory Summary", fills the required parameters (item, from date, to date, and file format), clicks **View** to load the report table, and finally triggers the **Download**.

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

### `select_report_name(driver, wait, report_name="Inventory Summary")`

Selects the desired report from the `report_name` dropdown. Returns `True` if the selection succeeds, `False` otherwise.

| Parameter | Type | Description |
|-----------|------|-------------|
| `report_name` | `str` | Exact or partial text of the report to select (default: `"Inventory Summary"`). |

---

### `fill_inventory_summary_form(driver, wait, data)`

Fills the Inventory Summary report parameter form.

| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | `dict` | Dictionary containing `item`, `from_date`, `to_date`, and `file_format`. (Matches `test_data.inventory_summary_data`.) |

**Behavior:**
- Calls `select_report_name` to ensure the correct report is selected.
- Waits for the `item_ref_id` dropdown to appear (indicates form is ready).
- Maps fields: `item` (dropdown with ID `item_ref_id`), `from_date` (input with ID `from_date`), `to_date` (input with ID `to_date`), `file_format` (dropdown with ID `file_format`).
- Uses `select_dropdown` and `fill_input` with fallback strategies (by `control_id`, `control_name`, and `label_text`).

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
2. Fill the form (`fill_inventory_summary_form`).
3. Click View (`click_view`).
4. Click Download (`click_download`).

| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | `dict` | Report parameters (must match the structure of `inventory_summary_data`). |

---

## Logging

All actions are logged with timestamps and severity levels (`INFO`, `WARNING`, `ERROR`).

**Example Console Output:**

```
15:20:10 | INFO     | Navigating to Reports page...
15:20:12 | INFO     |    ✅ Success overlays cleared.
15:20:13 | INFO     |    ✅ Clicked All Reports menu
15:20:15 | INFO     | ✅ Reports page loaded.
15:20:15 | INFO     |    🔽 Selecting Report Name: Inventory Summary...
15:20:17 | INFO     |       ✅ Selected report: Inventory Summary
15:20:18 | INFO     | 📝 Filling Inventory Summary form...
15:20:19 | INFO     |    ⏳ Waiting for form to initialize...
15:20:20 | INFO     |    ✅ Base form rendered.
15:20:21 | INFO     | ➡️ Selecting item_ref_id: Soyabean
15:20:23 | INFO     |    ✅ Selected: Soyabean
15:20:24 | INFO     | ➡️ Typing in from_date: 01/04/2025
15:20:26 | INFO     |    ✅ Filled from_date: 01/04/2025
15:20:27 | INFO     | ➡️ Typing in to_date: 07/04/2026
15:20:29 | INFO     |    ✅ Filled to_date: 07/04/2026
15:20:30 | INFO     | ➡️ Selecting file_format: EXCEL
15:20:32 | INFO     |    ✅ Selected: EXCEL
15:20:33 | INFO     | ✅ Form filling complete.
15:20:33 | INFO     |    ✅ View button clicked
15:20:34 | INFO     | ⏳ Waiting for report table to load...
15:20:37 | INFO     | ✅ Report table loaded.
15:20:38 | INFO     | ✅ Download triggered successfully.
```

## Usage Example

```python
from reports.inventory_summary import run
from data.test_data import inventory_summary_data

def test_inventory_summary(driver, wait):
    run(driver, wait, inventory_summary_data)
```

## Maintenance Notes

- **Report Name**: The default `report_name` is `"Inventory Summary"`. Update the string in `select_report_name` and `fill_inventory_summary_form` if the UI text changes.
- **Field Map**: The `field_map` in `fill_inventory_summary_form` defines the HTML IDs for each parameter. If the UI changes (e.g., `item_ref_id` becomes `item_id`), update the map accordingly.
- **Item Dropdown**: The item dropdown is searchable. Ensure the test data `item` value matches an existing item in the system.
- **Download Button**: The XPath covers common button variations. Adjust if the download button design changes.
```