# QC Module Reference (`qc_section.py`)

This module automates the **Quality Check (QC)** creation and approval process in the FPC ERP system. It selects a supplier, picks the latest Gate Pass (which auto‑populates item rows), fills QC parameters for each commodity via a modal, submits the QC, and then approves it from the list page.

## Helper Functions

### `click_with_retry(driver, wait, xpath, retries=5, delay=1.5)`

Clicks an element identified by XPath, retrying on `StaleElementReferenceException`.  
This prevents failures caused by dynamic DOM updates.

| Parameter | Type | Description |
|-----------|------|-------------|
| `xpath` | `str` | XPath of the element to click. |
| `retries` | `int` | Number of click attempts (default: 5). |
| `delay` | `float` | Seconds to wait between retries (default: 1.5). |

### `wait_for_sweetalert_to_close(driver, wait, timeout=10)`

Waits for any SweetAlert2 popup to disappear. Logs a warning if it persists.

### `select_first_gate_pass_option(driver, wait)`

Opens the Gate Pass dropdown and selects the first available option (the most recent Gate Pass).  
Used because the exact Gate Pass number is not known in advance.

### `fill_qc_parameters_modal(driver, wait, parameter_dict, item_index)`

Opens the QC parameter modal for a specific row, fills the actual values for each parameter, and submits the modal.

| Parameter | Type | Description |
|-----------|------|-------------|
| `parameter_dict` | `dict` | Mapping of parameter names to values (e.g., `{"Moisture": 1, "Foreign Material": 1}`). |
| `item_index` | `int` | Zero‑based index of the commodity row. |

### `approve_latest_qc(driver, wait)`

Finds the most recent QC in the list, clicks its edit button, and clicks the Approve button.

## Main Function

### `fill_qc_registration(driver, wait, data)`

Orchestrates the complete QC creation workflow.

| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | `dict` | Dictionary matching the structure of `test_data.qc_data`. |

**Steps Performed:**

1. Sets the transaction date.
2. Selects the supplier using a forced search‑and‑click approach (handles searchable dropdowns).
3. Selects the item type.
4. Selects the first Gate Pass – this auto‑populates all commodity rows.
5. Sets the transaction currency to INR.
6. Expands the **QC Details** accordion.
7. For each commodity in `data['items']`, calls `fill_qc_parameters_modal()` to enter QC parameters.
8. Submits the QC form.
9. Waits for redirect to the QC list page.
10. Calls `approve_latest_qc()` to approve the newly created QC.

## Logging

All actions are logged with timestamps and severity levels (`INFO`, `WARNING`, `ERROR`).

**Example Console Output:**

```
13:27:34 | INFO     | ⚡ Starting QC Registration...
13:27:35 | INFO     |    📅 Setting QC Transaction Date to: 14/04/2026
13:27:36 | INFO     |    ✅ Filled transaction_date: 14/04/2026
13:27:37 | INFO     |    ➡️ Forcing Supplier Selection for: Kavya Singh-9933768617|Farmer
13:27:39 | INFO     |       ✅ Supplier clicked: Kavya Singh
13:27:40 | INFO     | ➡️ Selecting Gate Pass (first option)
13:27:44 | INFO     |    ✅ Selected first Gate Pass option
13:27:47 | INFO     |    ✅ QC Details accordion expanded
13:27:48 | INFO     |    🔬 Processing QC Parameters for 1 items...
13:27:49 | INFO     |       ➡️ Doing QC for: Soyabean
13:27:50 | INFO     | ⚡ Filling QC parameters for Item 1 (via modal)...
13:27:51 | INFO     |    ✅ 'Enter Parameter' button 1 clicked
13:27:53 | INFO     |    Found parameter UI text: 'Moisture'
13:27:54 | INFO     |    ✅ Set Moisture = 1
13:27:55 | INFO     |    Found parameter UI text: 'Foreign Material'
13:27:56 | INFO     |    ✅ Set Foreign Material = 1
13:27:57 | INFO     |    Found parameter UI text: 'Damaged Seed'
13:27:58 | INFO     |    ✅ Set Damaged Seed = 1
13:27:59 | INFO     |    ✅ Modal submitted (Ok clicked)
13:28:00 | INFO     |    ✅ Modal closed
13:28:01 | INFO     | 📤 Submitting the QC form...
13:28:02 | INFO     | ✅ Submit button clicked
13:28:05 | INFO     |    ✅ Returned to QC List page.
13:28:07 | INFO     | 🚀 QC Registration Completed Successfully!
13:28:07 | INFO     | ⚡ Approving the latest QC...
13:28:09 | INFO     |    Number of rows in QC list: 1
13:28:10 | INFO     |    ✅ Edit button clicked via: //table/tbody/tr[1]//button[contains(@class, 'tblActnBtn')]//i[contains(@class, 'bi-pencil')]/..
13:28:12 | INFO     |    ✅ SweetAlert overlay closed.
13:28:14 | INFO     |    ✅ Approve button clicked
13:28:16 | INFO     |    ✅ SweetAlert overlay closed.
13:28:18 | INFO     | 🚀 QC approved successfully!
```

## Usage Example

```python
from privateb2b.qc_section import fill_qc_registration
from data.test_data import qc_data

def test_qc(driver, wait):
    fill_qc_registration(driver, wait, qc_data)
```

## Maintenance Notes

- **Supplier Selection**: Uses a forced search‑and‑click approach because the standard `select_dropdown` helper sometimes fails on this particular field. The supplier name is extracted by splitting on `'-'`. Ensure test data follows the `"Name-Phone|Type"` format.
- **Gate Pass Dropdown**: Relies on `mat-select[formcontrolname='gate_pass_ref_id']`. Update if the `formcontrolname` changes.
- **QC Parameters Modal**: The modal rows are located by `input[formcontrolname='actual_value']`. The parameter name is read from `.mat-mdc-select-min-line`. If the UI changes these classes, update the selectors.
- **Edit Button XPaths**: Multiple fallback XPaths are tried because the button structure varies slightly across environments. The retry utility ensures stale elements are handled.
- **Post‑Submit Waits**: `time.sleep(3)` after Gate Pass selection allows backend API to populate rows. Adjust if the network is slower or faster.
```