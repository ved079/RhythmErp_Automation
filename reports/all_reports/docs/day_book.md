# Day Book Report Module Reference (`day_book.py`)

This module automates the **Day Book** report generation in the FPC ERP system. It navigates to the Reports page, selects "Day Book", fills the required parameters (for type, frequency, voucher type, file format, from date, and to date), clicks **View** to load the report table, and finally triggers the **Download**.

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

### `select_report_name(driver, wait, report_name="Day Book")`

Selects the desired report from the `report_name` dropdown. Returns `True` if the selection succeeds, `False` otherwise.

| Parameter | Type | Description |
|-----------|------|-------------|
| `report_name` | `str` | Exact or partial text of the report to select (default: `"Day Book"`). |

---

### `fill_day_book_form(driver, wait, data)`

Fills the Day Book report parameter form.

| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | `dict` | Dictionary containing `for_type`, `frequency`, `voucher_type`, `file_format`, `from_date`, and `to_date`. (Matches `test_data.day_book_data`.) |

**Behavior:**
- Calls `select_report_name` to ensure the correct report is selected.
- Waits for the `for_type` dropdown to appear (indicates form is ready).
- Maps fields: `for_type` (dropdown with ID `for_type`), `frequency` (dropdown with ID `frequency`), `voucher_type` (dropdown with ID `voucher_type`), `file_format` (dropdown with ID `file_format`), `from_date` and `to_date` (inputs).
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
2. Fill the form (`fill_day_book_form`).
3. Click View (`click_view`).
4. Click Download (`click_download`).

| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | `dict` | Report parameters (must match the structure of `day_book_data`). |

---

## Logging

All actions are logged with timestamps and severity levels (`INFO`, `WARNING`, `ERROR`).

**Example Console Output:**

```
16:45:30 | INFO     | Navigating to Reports page...
16:45:32 | INFO     |    ✅ Success overlays cleared.
16:45:33 | INFO     |    ✅ Clicked All Reports menu
16:45:35 | INFO     | ✅ Reports page loaded.
16:45:35 | INFO     |    🔽 Selecting Report Name: Day Book...
16:45:37 | INFO     |       ✅ Selected report: Day Book
16:45:38 | INFO     | 📝 Filling Day Book form...
16:45:39 | INFO     |    ⏳ Waiting for form to initialize...
16:45:40 | INFO     |    ✅ Base form rendered.
16:45:41 | INFO     | ➡️ Selecting for_type: All Transaction
16:45:43 | INFO     |    ✅ Selected: All Transaction
16:45:44 | INFO     | ➡️ Selecting frequency: Date Range
16:45:46 | INFO     |    ✅ Selected: Date Range
16:45:47 | INFO     | ➡️ Selecting voucher_type: Sale
16:45:49 | INFO     |    ✅ Selected: Sale
16:45:50 | INFO     | ➡️ Selecting file_format: EXCEL
16:45:52 | INFO     |    ✅ Selected: EXCEL
16:45:53 | INFO     | ➡️ Typing in from_date: 01/01/2026
16:45:55 | INFO     |    ✅ Filled from_date: 01/01/2026
16:45:56 | INFO     | ➡️ Typing in to_date: 07/04/2026
16:45:58 | INFO     |    ✅ Filled to_date: 07/04/2026
16:45:59 | INFO     | ✅ Form filling complete.
16:45:59 | INFO     |    ✅ View button clicked
16:46:00 | INFO     | ⏳ Waiting for report table to load...
16:46:03 | INFO     | ✅ Report table loaded.
16:46:04 | INFO     | ✅ Download triggered successfully.
```

## Usage Example

```python
from reports.day_book import run
from data.test_data import day_book_data

def test_day_book(driver, wait):
    run(driver, wait, day_book_data)
```

## Maintenance Notes

- **Report Name**: The default `report_name` is `"Day Book"`. Update the string in `select_report_name` and `fill_day_book_form` if the UI text changes.
- **Field Map**: The `field_map` in `fill_day_book_form` defines the HTML IDs for each parameter. If the UI changes (e.g., `for_type` becomes `transaction_type`), update the map accordingly.
- **Frequency Dropdown ID**: The dropdown uses ID `frequency`. Ensure this matches the actual HTML.
- **Download Button**: The XPath covers common button variations. Adjust if the download button design changes.
```