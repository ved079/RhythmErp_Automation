# Ageing Report Module Reference (`ageing_report.py`)

This module automates the **Ageing Report** generation in the FPC ERP system. It navigates to the Reports page, selects "Ageing Report", fills the required parameters (transaction type, due status, date range, division, department, type of sale, location, file format, and group by), clicks **View** to load the report table, and finally triggers the **Download**.

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

### `select_report_name(driver, wait, report_name="Ageing Report")`

Selects the desired report from the `report_name` dropdown. Returns `True` if the selection succeeds, `False` otherwise.

| Parameter | Type | Description |
|-----------|------|-------------|
| `report_name` | `str` | Exact or partial text of the report to select (default: `"Ageing Report"`). |

---

### `fill_ageing_report_form(driver, wait, data)`

Fills the Ageing Report parameter form.

| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | `dict` | Dictionary containing `transaction_type`, `due_status`, `from_date`, `to_date`, `division`, `department`, `type_of_sale`, `location`, `file_format`, and `group_by`. (Matches `test_data.ageing_report_data`.) |

**Behavior:**
- Calls `select_report_name` to ensure the correct report is selected.
- Waits for the `transaction_type` dropdown to appear (indicates form is ready).
- Maps a comprehensive set of fields, routing dropdowns to `select_dropdown` and date inputs to `fill_input`.
- Uses fallback strategies for dropdowns: tries `control_id`, then `control_name`, then `label_text`, and finally non‑searchable.

---

### `click_view(driver, wait)`

Clicks the **View** button to generate the report. Waits for any spinners/overlays to clear, clicks the button, waits 3 seconds, and confirms the report table (or `.report-container`) is present.

---

### `click_download(driver, wait)`

Clicks the **Download** button (targeting either a button containing "Download" or a button with class `apply` and text "Download") and waits 4 seconds for the download to initiate.

---

### `run(driver, wait, data)`

Orchestrates the complete report workflow:

1. Navigate to Reports page (`nav_section.go_to_reports_page`).
2. Fill the form (`fill_ageing_report_form`).
3. Click View (`click_view`).
4. Click Download (`click_download`).

| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | `dict` | Report parameters (must match the structure of `ageing_report_data`). |

---

## Logging

All actions are logged with timestamps and severity levels (`INFO`, `WARNING`, `ERROR`).

**Example Console Output:**

```
12:00:15 | INFO     | Navigating to Reports page...
12:00:17 | INFO     |    ✅ Success overlays cleared.
12:00:18 | INFO     |    ✅ Clicked All Reports menu
12:00:20 | INFO     | ✅ Reports page loaded.
12:00:20 | INFO     |    🔽 Selecting Report Name: Ageing Report...
12:00:22 | INFO     |       ✅ Selected report: Ageing Report
12:00:23 | INFO     | 📝 Filling Ageing Report form...
12:00:24 | INFO     |    ⏳ Waiting for form to initialize...
12:00:25 | INFO     |    ✅ Base form rendered.
12:00:26 | INFO     | ➡️ Selecting transaction_type: Purchase
12:00:28 | INFO     |    ✅ Selected: Purchase
12:00:29 | INFO     | ➡️ Selecting due_status: All
12:00:31 | INFO     |    ✅ Selected: All
12:00:32 | INFO     | ➡️ Typing in from_date: 01/04/2025
12:00:34 | INFO     |    ✅ Filled from_date: 01/04/2025
12:00:35 | INFO     | ➡️ Typing in to_date: 07/04/2026
12:00:37 | INFO     |    ✅ Filled to_date: 07/04/2026
12:00:38 | INFO     | ➡️ Selecting division_ref_id: HR
12:00:40 | INFO     |    ✅ Selected: HR
12:00:41 | INFO     | ➡️ Selecting department_ref_id: Businesss Division
12:00:43 | INFO     |    ✅ Selected: Businesss Division
12:00:44 | INFO     | ➡️ Selecting sale_type_ref_id: B2B
12:00:46 | INFO     |    ✅ Selected: B2B
12:00:47 | INFO     | ➡️ Selecting location_ref_id: London
12:00:49 | INFO     |    ✅ Selected: London
12:00:50 | INFO     | ➡️ Selecting file_format: EXCEL
12:00:52 | INFO     |    ✅ Selected: EXCEL
12:00:53 | INFO     | ➡️ Selecting group_by: Supplier
12:00:55 | INFO     |    ✅ Selected: Supplier
12:00:56 | INFO     | ✅ Form filling complete.
12:00:56 | INFO     |    ✅ View button clicked
12:00:57 | INFO     | ⏳ Waiting for report table to load...
12:01:00 | INFO     | ✅ Report table loaded.
12:01:01 | INFO     | ✅ Download triggered successfully.
```

## Usage Example

```python
from reports.ageing_report import run
from data.test_data import ageing_report_data

def test_ageing_report(driver, wait):
    run(driver, wait, ageing_report_data)
```

## Maintenance Notes

- **Report Name**: The default `report_name` is `"Ageing Report"`. Update the string in `select_report_name` and `fill_ageing_report_form` if the UI text changes.
- **Field Map**: The `field_map` in `fill_ageing_report_form` defines the HTML IDs for each parameter. If the UI changes (e.g., `transaction_type` becomes `trans_type`), update the map accordingly.
- **Navigation**: This module relies on `nav_section.go_to_reports_page` for consistent, robust navigation. Keep that function updated if the Reports menu structure changes.
- **Download Button**: The XPath covers common button variations. Adjust if the download button design changes.
```