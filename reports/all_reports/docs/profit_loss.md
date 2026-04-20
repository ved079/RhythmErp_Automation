# Profit & Loss Report Module Reference (`profit_loss.py`)

This module automates the **Profit & Loss** report generation in the FPC ERP system. It navigates to the Reports page, selects "Profit Loss", fills all relevant parameters (transaction date, level, view type, division, department, type of sale, location, file format, and amount unit conversion), clicks **View** to load the report table, and finally triggers the **Download**.

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

### `select_report_name(driver, wait, report_name="Profit Loss")`

Selects the desired report from the `report_name` dropdown. Returns `True` if the selection succeeds, `False` otherwise.

| Parameter | Type | Description |
|-----------|------|-------------|
| `report_name` | `str` | Exact or partial text of the report to select (default: `"Profit Loss"`). |

---

### `fill_profit_loss_form(driver, wait, data)`

Fills the Profit & Loss report parameter form.

| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | `dict` | Dictionary containing `transaction_date`, `level`, `view_type`, `division`, `department`, `type_of_sale`, `location`, `file_format`, and `amount_unit_conversion`. (Matches `test_data.profit_loss_data`.) |

**Behavior:**
- Calls `select_report_name` to ensure the correct report is selected.
- Waits for the `transaction_date` input to appear (indicates form is ready).
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

1. Navigate to Reports page (`go_to_reports_page`).
2. Fill the form (`fill_profit_loss_form`).
3. Click View (`click_view`).
4. Click Download (`click_download`).

| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | `dict` | Report parameters (must match the structure of `profit_loss_data`). |

---

## Logging

All actions are logged with timestamps and severity levels (`INFO`, `WARNING`, `ERROR`).

**Example Console Output:**

```
14:00:12 | INFO     | Navigating to Reports page...
14:00:14 | INFO     |    ✅ Success overlays cleared.
14:00:15 | INFO     |    ✅ Clicked All Reports menu
14:00:17 | INFO     | ✅ Reports page loaded.
14:00:17 | INFO     |    🔽 Selecting Report Name: Profit Loss...
14:00:19 | INFO     |       ✅ Selected report: Profit Loss
14:00:20 | INFO     | 📝 Filling Profit Loss form...
14:00:21 | INFO     |    ⏳ Waiting for form to initialize...
14:00:22 | INFO     |    ✅ Base form rendered.
14:00:23 | INFO     | ➡️ Typing in transaction_date: 07/04/2026
14:00:25 | INFO     |    ✅ Filled transaction_date: 07/04/2026
14:00:26 | INFO     | ➡️ Selecting level: Category
14:00:28 | INFO     |    ✅ Selected: Category
14:00:29 | INFO     | ➡️ Selecting view_type: Vertical
14:00:31 | INFO     |    ✅ Selected: Vertical
14:00:32 | INFO     | ➡️ Selecting division_ref_id: HR
14:00:34 | INFO     |    ✅ Selected: HR
14:00:35 | INFO     | ➡️ Selecting file_format: EXCEL
14:00:37 | INFO     |    ✅ Selected: EXCEL
14:00:38 | INFO     | ✅ Form filling complete.
14:00:38 | INFO     |    ✅ View button clicked
14:00:39 | INFO     | ⏳ Waiting for report table to load...
14:00:42 | INFO     | ✅ Report table loaded.
14:00:43 | INFO     | ✅ Download triggered successfully.
```

## Usage Example

```python
from reports.profit_loss import run
from data.test_data import profit_loss_data

def test_profit_loss(driver, wait):
    run(driver, wait, profit_loss_data)
```

## Maintenance Notes

- **Report Name**: The default `report_name` is `"Profit Loss"`. Update the string in `select_report_name` and `fill_profit_loss_form` if the UI text changes.
- **Field Map**: The `field_map` in `fill_profit_loss_form` defines the HTML IDs and fallback labels for each parameter. If the UI changes (e.g., `division_ref_id` becomes `division_id`), update the map accordingly.
- **Dropdown Resilience**: The function tries multiple locator strategies (`control_id` → `control_name` → `label_text` → non‑searchable), ensuring robustness against minor UI variations.
- **Download Button**: The XPath covers common button variations. Adjust if the download button design changes.
```