# Dispatch Note Module Reference (`dispatch_note_section.py`)

This module automates the **Dispatch Note** creation process in the FPC ERP system. It selects a customer, a sales order, multiple lots (based on the number of commodities), fills tax rates and bag counts, uploads attachments, and submits the dispatch note.

## Helper Functions

### `click_with_retry(driver, wait, xpath, retries=5, delay=1.5)`

Clicks an element identified by XPath, retrying on `StaleElementReferenceException`. This prevents failures caused by dynamic DOM updates.

| Parameter | Type | Description |
|-----------|------|-------------|
| `xpath` | `str` | XPath of the element to click. |
| `retries` | `int` | Number of click attempts (default: 5). |
| `delay` | `float` | Seconds to wait between retries (default: 1.5). |

### `get_active_overlay(driver, wait, timeout=15)`

Waits for an Angular CDK overlay pane to appear **and** contain at least one `mat-option`. Returns the overlay element, scoping all subsequent option lookups to the correct pane.

| Parameter | Type | Description |
|-----------|------|-------------|
| `timeout` | `int` | Maximum seconds to wait for the overlay (default: 15). |

### `select_first_so_option(driver, wait)`

Opens the **Sales Order** dropdown and selects the first available option. Uses `get_active_overlay` to reliably locate options.

### `select_lots(driver, wait, num_lots)`

Opens the **Lot** dropdown and selects the top `num_lots` lots (one per commodity). Options are scoped to the active overlay and re‑fetched on each iteration to avoid stale references.

| Parameter | Type | Description |
|-----------|------|-------------|
| `num_lots` | `int` | Number of lots to select (usually equal to `len(items)`). |

## Main Function

### `fill_dispatch_note_registration(driver, wait, data)`

Orchestrates the complete Dispatch Note creation workflow.

| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | `dict` | Dictionary matching the structure of `test_data.dispatch_note_data`. |

**Steps Performed:**

1. Fills **Transaction Date** (if provided).
2. Selects base dropdowns: **Customer**, **Sale Type**, **Supply Type**, **Department**, **Division**, **Location**, **Type of Sale**.
3. Selects the first **Sales Order** via `select_first_so_option`.
4. Selects **Lots** – one for each commodity in `data['items']` using `select_lots`.
5. Expands the **Additional Details** accordion (using `click_with_retry`).
6. Fills **Transporter Name**, **Vehicle No**, **Distance**.
7. For each commodity row:
   - Sets **Tax Rate** (mapped by item name: 5% for Soyabean/Turmeric/Chana, 0% for Tur‑Red/Maize‑Yellow).
   - Fills **No of Bags** (from item data or fallback).
8. Uploads an attachment if `attachment_file` is provided.
9. Submits the form using `click_with_retry` on the submit button.
10. Waits for redirect to the list page (or logs validation errors).

## Logging

All actions are logged with timestamps and severity levels (`INFO`, `WARNING`, `ERROR`).

**Example Console Output:**
```
15:27:26 | INFO     | ⚡ Starting Dispatch Note Registration...
15:27:27 | INFO     |   ✅ Filled Transaction Date: 14/04/2026
15:27:30 | INFO     |   ✅ Selected first Sales Order
15:27:34 | INFO     |   ⏳ Waiting for Lots to load from backend...
15:27:38 | INFO     |   ✅ Lot dropdown opened, selecting top 1 lot(s)...
15:27:39 | INFO     |       ✅ Selected Lot 1
15:27:41 | INFO     |   ✅ Finished selecting 1 lot(s)
15:27:43 | INFO     |   ✅ Additional Details accordion expanded
15:27:45 | INFO     |    ✅ Filled transporter_name: Truck
15:27:46 | INFO     |    ✅ Filled vehicle_no: MH12AB1234
15:27:47 | INFO     |    ✅ Filled distance: 1.0
15:27:48 | INFO     |    📦 Processing Grid Details for 1 items...
15:27:50 | INFO     |       ✅ Row 1: Tax Rate = 5
15:27:51 | INFO     |       ✅ Row 1: No of Bags = 10
15:27:52 | INFO     |    ✅ File uploaded: C:\...\blank.pdf
15:27:54 | INFO     | 📤 Submitting Dispatch Note...
15:27:55 | INFO     |    ✅ Submit button clicked
15:27:58 | INFO     | 🚀 Dispatch Note Registration Completed Successfully!
```

## Usage Example

```python
from privateb2b.dispatch_note_section import fill_dispatch_note_registration
from data.test_data import dispatch_note_data

def test_dispatch_note(driver, wait):
    fill_dispatch_note_registration(driver, wait, dispatch_note_data)
```

## Maintenance Notes

- **Sales Order Dropdown**: The function `select_first_so_option` assumes the first option is the correct one. If multiple SOs exist, you may need to filter by customer or date.
- **Lot Selection**: Uses `select_lots` to pick the top N lots. Ensure the UI actually returns at least `num_lots` lots; the function will warn if fewer are available.
- **Tax Rate Mapping**: Item‑specific tax rates are hardcoded. Update the mapping if business rules change.
- **File Upload**: The selector `input[type='file'][id^='bank_upload']` relies on a dynamic ID prefix. If the UI changes, adjust the selector.
- **Retry Logic**: `click_with_retry` is used for the accordion and submit button because these elements may be re‑rendered by Angular. Increase `retries` or `delay` if the page is unusually slow.
```