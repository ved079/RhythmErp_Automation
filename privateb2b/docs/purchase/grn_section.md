# GRN Module Reference (`grn_section.py`)

This module automates the **Goods Receipt Note (GRN)** creation and approval process in the FPC ERP system. It selects a supplier, picks the latest Gate Pass (which auto‑populates item rows), submits the GRN, and then approves it from the list page.

## Helper Functions

### `click_with_retry(driver, wait, xpath, retries=3, delay=1.5)`

Clicks an element identified by XPath, retrying on `StaleElementReferenceException`.  
This prevents failures caused by dynamic DOM updates.

| Parameter | Type | Description |
|-----------|------|-------------|
| `xpath` | `str` | XPath of the element to click. |
| `retries` | `int` | Number of click attempts (default: 3). |
| `delay` | `float` | Seconds to wait between retries (default: 1.5). |

### `wait_for_sweetalert_to_close(driver, wait, timeout=10)`

Waits for any SweetAlert2 popup to disappear. Logs a warning if it persists.

### `select_first_gate_pass_option(driver, wait)`

Opens the Gate Pass dropdown and selects the first available option (the most recent Gate Pass).  
Used because the exact Gate Pass number is not known in advance.

## Main Functions

### `fill_grn_registration(driver, wait, data)`

Creates a new GRN.

| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | `dict` | Dictionary containing `transaction_date` and `supplier` (matches `test_data.grn_data`). |

**Steps:**
1. Sets the transaction date.
2. Selects the supplier (searchable dropdown).
3. Selects the first Gate Pass – this auto‑populates all commodity rows.
4. Submits the form.

### `approve_latest_grn(driver, wait)`

Approves the most recently created GRN from the list page.

**Steps:**
1. Waits for the GRN list table.
2. Clicks the **edit** (pencil) button on the first row using `click_with_retry`.
3. Waits for the detail view / modal.
4. Clicks the **Approve** button using `click_with_retry`.
5. Waits for the SweetAlert confirmation to close.

## Logging

All actions are logged with timestamps and severity levels (`INFO`, `WARNING`, `ERROR`).

**Example Console Output:**
```
13:14:36 | INFO     | ⚡ Starting GRN Registration...
13:14:37 | INFO     |    📅 Setting GRN Transaction Date to: 13/04/2026
13:14:38 | INFO     |    ✅ Filled transaction_date: 13/04/2026
13:14:39 | INFO     | ➡️ Selecting Gate Pass (first option)
13:14:43 | INFO     |    ✅ Selected first Gate Pass option
13:14:46 | INFO     | 📤 Submitting the form...
13:14:46 | INFO     | ✅ Submit button clicked
13:14:49 | INFO     | 🚀 GRN Registration Completed Successfully!
13:14:49 | INFO     | ⚡ Approving latest GRN...
13:14:51 | INFO     |    ✅ Clicked edit button for latest GRN
13:14:54 | INFO     |    ✅ Clicked Approve button
13:14:56 | INFO     |    ✅ SweetAlert overlay closed.
13:14:56 | INFO     | 🚀 GRN approved successfully!
```

## Usage Example

```python
from privateb2b.grn_section import fill_grn_registration, approve_latest_grn
from data.test_data import grn_data

def test_grn(driver, wait):
    fill_grn_registration(driver, wait, grn_data)
    approve_latest_grn(driver, wait)
```

## Maintenance Notes

- **Gate Pass Dropdown**: The selector `mat-select[formcontrolname='gate_pass_ref_id']` assumes the form uses this exact `formcontrolname`. Update if the UI changes.
- **Edit Button XPath**: The XPath targets a button containing a pencil icon (`bi-pencil`). If the icon class changes, adjust the selector.
- **Retry Logic**: `click_with_retry` is used for the edit and approve buttons because the list page may refresh after submission. Increase `retries` or `delay` if the page is unusually slow.
- **Post‑Submit Wait**: `time.sleep(3)` after GRN submission allows the list page to load. Consider replacing with an explicit wait for the table if timing becomes unreliable.
```