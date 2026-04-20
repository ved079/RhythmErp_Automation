# Sales Order Module Reference (`sales_order_section.py`)

This module automates the **Sales Order** creation and approval process in the FPC ERP system. It fills customer information, adds multiple commodity rows with quantity, rate, tax, and expected delivery date, submits the order, and then approves it from the list page.

## Helper Functions

### `click_with_retry(driver, wait, xpath, retries=5, delay=1.5)`

Clicks an element identified by XPath, retrying on `StaleElementReferenceException`.  
This prevents failures caused by dynamic DOM updates.

| Parameter | Type | Description |
|-----------|------|-------------|
| `xpath` | `str` | XPath of the element to click. |
| `retries` | `int` | Number of click attempts (default: 5). |
| `delay` | `float` | Seconds to wait between retries (default: 1.5). |

### `add_item_row(driver, wait, row_index)`

Clicks the **"+"** button to add a new commodity row. Returns `True` if successful, `False` otherwise.

| Parameter | Type | Description |
|-----------|------|-------------|
| `row_index` | `int` | Zero‑based index of the row to be added (e.g., `1` for the second row). |

### `fill_item_row(driver, wait, row_index, item_data)`

Fills a single commodity row with item name, quantity, rate, tax rate, and optional expected delivery date.

| Parameter | Type | Description |
|-----------|------|-------------|
| `row_index` | `int` | Zero‑based index of the row. |
| `item_data` | `dict` | Dictionary containing `item_name`, `quantity`, `rate`, `tax_rate`, and optionally `expected_delivery_date`. |

### `approve_latest_sales_order(driver, wait)`

Finds the most recent Sales Order in the list, clicks its edit button, and clicks the Approve button.

## Main Function

### `fill_sales_order_registration(driver, wait, data)`

Orchestrates the complete Sales Order creation and approval workflow.

| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | `dict` | Dictionary matching the structure of `test_data.sales_order_data`. |

**Steps Performed:**

1. Selects **Customer** (searchable dropdown).
2. Sets **Department**, **Division**, **Location**, **Type of Sale** (with fallback to `control_name`).
3. Fills **Transaction Date**, **Customer PO Number**, **Customer PO Date**, and **Transportation Charges**.
4. Processes each commodity in `data['items']`:
   - Adds a new row via `add_item_row()` (except for the first item).
   - Fills the row using `fill_item_row()`.
5. Waits for ERP to calculate conversion rate and totals.
6. Submits the form using `click_with_retry`.
7. Waits for redirect to the list page.
8. Calls `approve_latest_sales_order()` to approve the newly created order.

## Logging

All actions are logged with timestamps and severity levels (`INFO`, `WARNING`, `ERROR`).

**Example Console Output:**
```
14:10:23 | INFO     | ⚡ Starting Sales Order Registration...
14:10:24 | INFO     |    Selecting Customer: Vedant Enterprises-9999999999|Customer
14:10:28 | INFO     |    ✅ Filled transaction_date: 14/04/2026
14:10:29 | INFO     |    ✅ Filled customer_po_number: 9880676434
14:10:30 | INFO     |    ✅ Filled customer_po_date: 14/04/2026
14:10:31 | INFO     |    ✅ Filled transportation_charges: 0.0
14:10:32 | INFO     |    📦 Processing 2 items...
14:10:33 | INFO     |       ➡️ Setting details for Row 1: Soyabean
14:10:35 | INFO     |       ✅ Selected item: Soyabean
14:10:36 | INFO     |       ✅ Quantity: 1.4
14:10:37 | INFO     |       ✅ Rate: 56609.7
14:10:38 | INFO     |       ✅ Tax Rate set to 5
14:10:39 | INFO     |       ✅ Expected delivery date: 14/04/2026
14:10:40 | INFO     |    ✅ Added new row for item 2
14:10:41 | INFO     |       ➡️ Setting details for Row 2: Tur-Red
14:10:43 | INFO     |       ✅ Selected item: Tur-Red
14:10:44 | INFO     |       ✅ Quantity: 4.11
14:10:45 | INFO     |       ✅ Rate: 62495.23
14:10:46 | INFO     |       ✅ Tax Rate set to 0
14:10:47 | INFO     |       ✅ Expected delivery date: 14/04/2026
14:10:48 | INFO     |    ⏳ Waiting for ERP to generate conversion rate and totals...
14:10:51 | INFO     | 📤 Submitting Sales Order form...
14:10:52 | INFO     |    ✅ Submit button clicked
14:10:55 | INFO     | 🚀 Sales Order Registration Completed Successfully!
14:10:55 | INFO     | ⚡ Approving the newly created Sales Order...
14:10:57 | INFO     |    ✅ Edit button clicked via: //table/tbody/tr[1]//button[.//i[contains(@class, 'bi-pencil')]]
14:10:59 | INFO     |    ✅ Approve button clicked
14:11:01 | INFO     | 🚀 Sales Order Approved Successfully!
```

## Usage Example

```python
from privateb2b.sales_order_section import fill_sales_order_registration
from data.test_data import sales_order_data

def test_sales_order(driver, wait):
    fill_sales_order_registration(driver, wait, sales_order_data)
```

## Maintenance Notes

- **Customer Dropdown**: Uses `select_dropdown` with `searchable=True`. Ensure the test data customer name exactly matches the UI option.
- **Item Dropdown Search**: The script types the item name into the overlay search box (if present) before selecting. If the search input placeholder changes, update the XPath `.//input[contains(@placeholder, 'Search')]`.
- **Tax Rate Mapping**: Item‑specific tax rates are hardcoded (`"Soyabean"`, `"Turmeric"`, `"Chana"` → 5%; `"Tur-Red"` → 0%). Update the mapping if business rules change.
- **Edit Button XPaths**: Multiple fallback XPaths are tried because the button structure varies. The retry utility ensures stale elements are handled.
- **Post‑Submit Waits**: `time.sleep(3)` after submit allows the list page to load. Consider replacing with an explicit wait for the table if timing becomes unreliable.
```