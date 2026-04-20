# Weighted Average Rate Report Module Reference (`weighted_average_rate.py`)

This module automates the **Weighted Average Rate Report** generation in the FPC ERP system. It navigates to the Reports page, selects the "Weighted Average Rate Report", fills the required parameters (file format and date), clicks View to load the report table, and finally triggers the download.

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

### `select_report_name(driver, wait, report_name="Weighted Average Rate Report")`

Selects the desired report from the `report_name` dropdown. Returns `True` if the selection succeeds, `False` otherwise.

| Parameter | Type | Description |
|-----------|------|-------------|
| `report_name` | `str` | Exact or partial text of the report to select (default: `"Weighted Average Rate Report"`). |

---

### `fill_weighted_avg_rate_form(driver, wait, data)`

Fills the Weighted Average Rate Report parameter form.

| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | `dict` | Dictionary containing `file_format` and `for_day` (e.g., from `test_data.weighted_average_rate_data`). |

**Behavior:**
- Calls `select_report_name` to ensure the correct report is selected.
- Waits for the `to_date` input to appear (indicates form is ready).
- Maps fields: `file_format` (dropdown) and `for_day` (date input mapped to `to_date` control ID).
- Uses `select_dropdown` and `fill_input` with fallback strategies.

---

### `click_view(driver, wait)`

Clicks the **View** button to generate the report and waits for the report table (or report container) to load.

---

### `click_download(driver, wait)`

Clicks the **Download** button (targeting either a button containing "Download" or a button with class `apply` and text "Download") and waits 4 seconds for the download to initiate.

---

### `run(driver, wait, data)`

Orchestrates the complete report workflow:

1. Navigate to Reports page (`go_to_reports_page`).
2. Fill the form (`fill_weighted_avg_rate_form`).
3. Click View (`click_view`).
4. Click Download (`click_download`).

| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | `dict` | Report parameters (must contain `file_format` and `for_day`). |

---

## Logging

All actions are logged with timestamps and severity levels (`INFO`, `WARNING`, `ERROR`).

**Example Console Output:**

```
10:20:15 | INFO     | Navigating to Reports page...
10:20:17 | INFO     |    ✅ Success overlays cleared.
10:20:18 | INFO     |    ✅ Clicked All Reports menu
10:20:20 | INFO     | ✅ Reports page loaded.
10:20:20 | INFO     |    🔽 Selecting Report Name: Weighted Average Rate Report...
10:20:22 | INFO     |       ✅ Selected report: Weighted Average Rate Report
10:20:23 | INFO     | 📝 Filling Weighted Average Rate form...
10:20:24 | INFO     |    ✅ Base form rendered.
10:20:25 | INFO     | ➡️ Selecting file_format: EXCEL
10:20:27 | INFO     |    ✅ Selected: EXCEL
10:20:28 | INFO     | ➡️ Typing in to_date: 04/04/2026
10:20:30 | INFO     |    ✅ Filled to_date: 04/04/2026
10:20:31 | INFO     | ✅ Form filling complete.
10:20:31 | INFO     |    ✅ View button clicked
10:20:34 | INFO     | ✅ Report table loaded.
10:20:35 | INFO     | ✅ Download triggered successfully.
```

## Usage Example

```python
from reports.weighted_average_rate import run
from data.test_data import weighted_average_rate_data

def test_weighted_average_rate(driver, wait):
    run(driver, wait, weighted_average_rate_data)
```

## Maintenance Notes

- **Report Name**: The default `report_name` is `"Weighted Average Rate Report"`. Update the string in `select_report_name` and `fill_weighted_avg_rate_form` if the UI text changes.
- **Date Field**: The parameter `for_day` is filled into the input with ID `to_date`. If the HTML ID changes, update the field map in `fill_weighted_avg_rate_form`.
- **Dropdown Fallbacks**: The field mapping includes fallback attempts (by `control_id`, `control_name`, `label_text`, and finally non‑searchable). This ensures robustness against minor UI variations.
- **Download Button**: The XPath `"//button[contains(normalize-space(), 'Download')] | //button[contains(@class, 'apply') and contains(text(), 'Download')]"` covers common button variations. Adjust if the download button design changes.
```