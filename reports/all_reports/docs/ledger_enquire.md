```markdown
# Ledger Enquiry Report Module Reference (`ledger_enquiry.py`)

This module automates the **Ledger Enquiry** report generation in the FPC ERP system. It navigates to the Reports page, selects "Ledger Enquiry", fills the required parameters (account, frequency, file format, from date, and to date), clicks **View** to load the report table, and finally triggers the **Download**.

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

### `select_report_name(driver, wait, report_name="Ledger Enquiry")`

Selects the desired report from the `report_name` dropdown. Returns `True` if the selection succeeds, `False` otherwise.

| Parameter | Type | Description |
|-----------|------|-------------|
| `report_name` | `str` | Exact or partial text of the report to select (default: `"Ledger Enquiry"`). |

---

### `fill_ledger_enquiry_form(driver, wait, data)`

Fills the Ledger Enquiry report parameter form.

| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | `dict` | Dictionary containing `account`, `frequency`, `file_format`, `from_date`, and `to_date`. (Matches `test_data.ledger_enquiry_data`.) |

**Behavior:**
- Calls `select_report_name` to ensure the correct report is selected.
- Waits for the `account_ref_id` dropdown to appear (indicates form is ready).
- Maps fields: `account` (dropdown with ID `account_ref_id`), `frequency` (dropdown with ID `frequancy`), `file_format` (dropdown with ID `file_format`), `from_date` (input with ID `from_date`), `to_date` (input with ID `to_date`).
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
2. Fill the form (`fill_ledger_enquiry_form`).
3. Click View (`click_view`).
4. Click Download (`click_download`).

| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | `dict` | Report parameters (must match the structure of `ledger_enquiry_data`). |

---

## Logging

All actions are logged with timestamps and severity levels (`INFO`, `WARNING`, `ERROR`).

**Example Console Output:**

```
15:45:10 | INFO     | Navigating to Reports page...
15:45:12 | INFO     |    ✅ Success overlays cleared.
15:45:13 | INFO     |    ✅ Clicked All Reports menu
15:45:15 | INFO     | ✅ Reports page loaded.
15:45:15 | INFO     |    🔽 Selecting Report Name: Ledger Enquiry...
15:45:17 | INFO     |       ✅ Selected report: Ledger Enquiry
15:45:18 | INFO     | 📝 Filling Ledger Enquiry form...
15:45:19 | INFO     |    ⏳ Waiting for form to initialize...
15:45:20 | INFO     |    ✅ Base form rendered.
15:45:21 | INFO     | ➡️ Selecting account_ref_id: Cash In Hand Shivani 1
15:45:23 | INFO     |    ✅ Selected: Cash In Hand Shivani 1
15:45:24 | INFO     | ➡️ Selecting frequency: Date Range
15:45:26 | INFO     |    ✅ Selected: Date Range
15:45:27 | INFO     | ➡️ Selecting file_format: EXCEL
15:45:29 | INFO     |    ✅ Selected: EXCEL
15:45:30 | INFO     | ➡️ Typing in from_date: 01/01/2026
15:45:32 | INFO     |    ✅ Filled from_date: 01/01/2026
15:45:33 | INFO     | ➡️ Typing in to_date: 07/04/2026
15:45:35 | INFO     |    ✅ Filled to_date: 07/04/2026
15:45:36 | INFO     | ✅ Form filling complete.
15:45:36 | INFO     |    ✅ View button clicked
15:45:37 | INFO     | ⏳ Waiting for report table to load...
15:45:40 | INFO     | ✅ Report table loaded.
15:45:41 | INFO     | ✅ Download triggered successfully.
```

## Usage Example

```python
from reports.ledger_enquiry import run
from data.test_data import ledger_enquiry_data

def test_ledger_enquiry(driver, wait):
    run(driver, wait, ledger_enquiry_data)
```

## Maintenance Notes

- **Report Name**: The default `report_name` is `"Ledger Enquiry"`. Update the string in `select_report_name` and `fill_ledger_enquiry_form` if the UI text changes.
- **Field Map**: The `field_map` in `fill_ledger_enquiry_form` defines the HTML IDs for each parameter. If the UI changes (e.g., `account_ref_id` becomes `account_id`), update the map accordingly.
- **Frequency Dropdown ID**: The dropdown uses ID `frequancy` (note the spelling). If the UI corrects this to `frequency`, update the field map.
- **Download Button**: The XPath covers common button variations. Adjust if the download button design changes.
```