# Inventory Report Module Reference (`inventory_report1.py`)

This module automates the **Inventory Report** generation in the FPC ERP system. It navigates to the Reports page, selects "Inventory Report", fills the required parameters (item, date range, division, department, type of sale, location, and file format), clicks **View** to load the report table, and finally triggers the **Download**.

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

### `select_report_name(driver, wait, report_name="Inventory Report")`

Selects the desired report from the `report_name` dropdown. Returns `True` if the selection succeeds, `False` otherwise.

| Parameter | Type | Description |
|-----------|------|-------------|
| `report_name` | `str` | Exact or partial text of the report to select (default: `"Inventory Report"`). |

---

### `fill_inventory_report_form(driver, wait, data)`

Fills the Inventory Report parameter form.

| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | `dict` | Dictionary containing `item`, `from_date`, `to_date`, `division`, `department`, `type_of_sale`, `location`, and `file_format`. (Matches `test_data.inventory_report_data`.) |

**Behavior:**
- Calls `select_report_name` to ensure the correct report is selected.
- Waits for the `item_ref_id` dropdown to appear (indicates form is ready).
- **Backwards Compatibility:** If `data['item']` is missing but `data['items']` (an array) exists, the first item's name is automatically used.
- Maps fields: `item` (dropdown with ID `item_ref_id`), `from_date` and `to_date` (inputs), `division`, `department`, `type_of_sale`, `location`, and `file_format` (dropdowns with their respective IDs).
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
2. Fill the form (`fill_inventory_report_form`).
3. Click View (`click_view`).
4. Click Download (`click_download`).

| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | `dict` | Report parameters (must match the structure of `inventory_report_data`). |

---

## Logging

All actions are logged with timestamps and severity levels (`INFO`, `WARNING`, `ERROR`).

**Example Console Output:**

```
16:10:05 | INFO     | Navigating to Reports page...
16:10:07 | INFO     |    ✅ Success overlays cleared.
16:10:08 | INFO     |    ✅ Clicked All Reports menu
16:10:10 | INFO     | ✅ Reports page loaded.
16:10:10 | INFO     |    🔽 Selecting Report Name: Inventory Report...
16:10:12 | INFO     |       ✅ Selected report: Inventory Report
16:10:13 | INFO     | 📝 Filling Inventory Report form...
16:10:14 | INFO     |    ⏳ Waiting for form to initialize...
16:10:15 | INFO     |    ✅ Base form rendered.
16:10:16 | INFO     | ➡️ Selecting item_ref_id: Soyabean
16:10:18 | INFO     |    ✅ Selected: Soyabean
16:10:19 | INFO     | ➡️ Typing in from_date: 01/04/2025
16:10:21 | INFO     |    ✅ Filled from_date: 01/04/2025
16:10:22 | INFO     | ➡️ Typing in to_date: 07/04/2026
16:10:24 | INFO     |    ✅ Filled to_date: 07/04/2026
16:10:25 | INFO     | ➡️ Selecting division_ref_id: HR
16:10:27 | INFO     |    ✅ Selected: HR
16:10:28 | INFO     | ➡️ Selecting department_ref_id: Businesss Division
16:10:30 | INFO     |    ✅ Selected: Businesss Division
16:10:31 | INFO     | ➡️ Selecting sale_type_ref_id: B2B
16:10:33 | INFO     |    ✅ Selected: B2B
16:10:34 | INFO     | ➡️ Selecting location_ref_id: London
16:10:36 | INFO     |    ✅ Selected: London
16:10:37 | INFO     | ➡️ Selecting file_format: EXCEL
16:10:39 | INFO     |    ✅ Selected: EXCEL
16:10:40 | INFO     | ✅ Form filling complete.
16:10:40 | INFO     |    ✅ View button clicked
16:10:41 | INFO     | ⏳ Waiting for report table to load...
16:10:44 | INFO     | ✅ Report table loaded.
16:10:45 | INFO     | ✅ Download triggered successfully.
```

## Usage Example

```python
from reports.inventory_report1 import run
from data.test_data import inventory_report_data

def test_inventory_report(driver, wait):
    run(driver, wait, inventory_report_data)
```

## Maintenance Notes

- **Report Name**: The default `report_name` is `"Inventory Report"`. Update the string in `select_report_name` and `fill_inventory_report_form` if the UI text changes.
- **Field Map**: The `field_map` in `fill_inventory_report_form` defines the HTML IDs for each parameter. If the UI changes (e.g., `item_ref_id` becomes `item_id`), update the map accordingly.
- **Backwards Compatibility**: The function can accept purchase flow data (which contains an `items` array) and automatically extracts the first item name. This allows seamless integration with end‑to‑end tests.
- **Download Button**: The XPath covers common button variations. Adjust if the download button design changes.
```