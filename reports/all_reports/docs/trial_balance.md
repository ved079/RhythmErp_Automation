# Trial Balance Report Module Reference (`trial_balance.py`)

This module automates the **Trial Balance** report generation in the FPC ERP system. It navigates to the Reports page, selects "Trial Balance", fills the required parameters (frequency, view type, balance type, level, file format, and transaction date), clicks **View** to load the report table, and finally triggers the **Download**.

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

### `select_report_name(driver, wait, report_name="Trial Balance")`

Selects the desired report from the `report_name` dropdown. Returns `True` if the selection succeeds, `False` otherwise.

| Parameter | Type | Description |
|-----------|------|-------------|
| `report_name` | `str` | Exact or partial text of the report to select (default: `"Trial Balance"`). |

---

### `fill_trial_balance_form(driver, wait, data)`

Fills the Trial Balance report parameter form.

| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | `dict` | Dictionary containing `frequency`, `view_type`, `balance_type`, `level`, `file_format`, and `transaction_date`. (Matches `test_data.trial_balance_data`.) |

**Behavior:**
- Calls `select_report_name` to ensure the correct report is selected.
- Waits for the `frequency` dropdown to appear (indicates form is ready).
- Maps fields: `frequency`, `view_type`, `balance_type`, `level`, and `file_format` as dropdowns; `transaction_date` as a date input.
- Uses `select_dropdown` and `fill_input` with fallback strategies.

---

### `click_view(driver, wait)`

Clicks the **View** button to generate the report.  
**Enhanced waiting logic:**
- Clears any existing overlays before clicking.
- Waits briefly for the loading spinner to appear.
- Waits for the spinner to completely disappear.
- Allows an extra second for Angular to render the data.
- Confirms the report table (or `.report-container`) is present.

---

### `click_download(driver, wait)`

Clicks the **Download** button (targeting either a button containing "Download" or a button with class `apply` and text "Download") and waits 4 seconds for the download to initiate.

---

### `run(driver, wait, data)`

Orchestrates the complete report workflow:

1. Navigate to Reports page (`go_to_reports_page`).
2. Fill the form (`fill_trial_balance_form`).
3. Click View (`click_view`).
4. Click Download (`click_download`).

| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | `dict` | Report parameters (must match the structure of `trial_balance_data`). |

---

## Logging

All actions are logged with timestamps and severity levels (`INFO`, `WARNING`, `ERROR`).

**Example Console Output:**

```
10:15:32 | INFO     | Navigating to Reports page...
10:15:34 | INFO     |    ✅ Success overlays cleared.
10:15:35 | INFO     |    ✅ Clicked All Reports menu
10:15:37 | INFO     | ✅ Reports page loaded.
10:15:37 | INFO     |    🔽 Selecting Report Name: Trial Balance...
10:15:39 | INFO     |       ✅ Selected report: Trial Balance
10:15:40 | INFO     | 📝 Filling Trial Balance form...
10:15:41 | INFO     |    ⏳ Waiting for frequency dropdown to appear...
10:15:42 | INFO     |    ✅ Base form rendered.
10:15:43 | INFO     | ➡️ Selecting frequency: As On Date
10:15:45 | INFO     |    ✅ Selected: As On Date
10:15:46 | INFO     | ➡️ Typing in transaction_date: 07/04/2026
10:15:48 | INFO     |    ✅ Filled transaction_date: 07/04/2026
10:15:49 | INFO     | ✅ Form filling complete.
10:15:50 | INFO     |    ✅ View button clicked
10:15:51 | INFO     | ⏳ Waiting for API data to load...
10:15:53 | INFO     | ✅ Report table loaded and populated.
10:15:54 | INFO     | ✅ Download triggered successfully.
```

## Usage Example

```python
from reports.trial_balance import run
from data.test_data import trial_balance_data

def test_trial_balance(driver, wait):
    run(driver, wait, trial_balance_data)
```

## Maintenance Notes

- **Report Name**: The default `report_name` is `"Trial Balance"`. Update the string in `select_report_name` and `fill_trial_balance_form` if the UI text changes.
- **Field Map**: The `field_map` in `fill_trial_balance_form` defines which HTML ID corresponds to each parameter. If the UI changes (e.g., `frequency` input ID becomes `freq`), update the map accordingly.
- **View Button Wait**: The enhanced waiting logic in `click_view` ensures the report table is fully populated before proceeding. Adjust the `time.sleep(2)` value if the report takes longer to render.
- **Download Button**: The XPath covers common button variations. If the download button design changes, update the `download_xpath` selector.
```