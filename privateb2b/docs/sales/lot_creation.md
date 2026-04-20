# Lot Creation Module Reference (`lot_section.py`)

This module automates the **Lot Creation** process in the FPC ERP system. It creates lots for one or multiple commodities by selecting a customer and a sales order, then allocating available purchase quantities (FIFO basis) to fulfill the required sales order quantity.

## Main Function

### `fill_lot_creation(driver, wait, data)`

Orchestrates the complete Lot creation workflow for one or more items.

| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | `dict` | Dictionary containing `customer_name` and an `items` array (each with `item_name` and `quantity`). Matches `test_data.sales_order_data` structure. |

**Steps Performed (for each item):**

1. **Navigate to Form** – If processing the second or later item, clicks the "Add" / "Create" button on the list page to open a new Lot form.
2. **Select Customer** – Uses a searchable dropdown (`customer_ref_id`).
3. **Select Sales Order** – Opens the Sales Order dropdown and picks the first available option (most recent).
4. **Select Commodity** – Opens the Commodity dropdown and selects the exact item name from the test data.
5. **Calculate Required Quantity** – Reads the required quantity from the item data.
6. **Collect Available Rows** – Scrapes the purchase bill table to extract available quantities from each row.
7. **Determine Allocations (FIFO)** – 
   - If a single row has enough quantity, allocates the full required amount from it.
   - Otherwise, splits the required quantity across multiple rows in FIFO order.
8. **Process Allocations** – For each selected row:
   - Checks the checkbox.
   - Enters the allocated quantity into the `allocated_qty` input.
   - Triggers Angular change detection by clicking away.
9. **Submit** – Clicks the submit button and waits for redirect to the list page.

## Logging

All actions are logged with timestamps and severity levels (`INFO`, `WARNING`, `ERROR`).

**Example Console Output:**
```
14:20:15 | INFO     | ⚡ Starting Lot Creation Process...
14:20:16 | INFO     | 
📦 --- Processing Lot for Item 1: Soyabean ---
14:20:18 | INFO     |    Opened Sales Order Number dropdown
14:20:19 | INFO     |    Selected first Sales Order Number
14:20:21 | INFO     |    Opened Commodity Name dropdown
14:20:23 | INFO     |    ✅ Selected Commodity Name: Soyabean
14:20:25 | INFO     |    Required Sales Order Quantity: 3.120 MT
14:20:26 | INFO     |    Found 15 rows in the lot table.
14:20:27 | INFO     |    ✅ Found a single row (Row 2) with 38.604 MT >= required 3.120 MT
14:20:29 | INFO     |    ✅ Checkbox selected for Row 2
14:20:32 | INFO     |    ✅ Allocation Quantity set to 3.12 MT
14:20:33 | INFO     | 📤 Submitting Lot Creation...
14:20:36 | INFO     | 🚀 Lot Creation for Soyabean Completed Successfully!
14:20:38 | INFO     | 
📦 --- Processing Lot for Item 2: Tur-Red ---
14:20:40 | INFO     |    🔄 Navigating back to the Create Lot form...
...
14:21:15 | INFO     | 🏁 All Lot Creations completed successfully!
```

## Usage Example

```python
from privateb2b.lot_section import fill_lot_creation
from data.test_data import sales_order_data   # contains customer_name and items array

def test_lot_creation(driver, wait):
    fill_lot_creation(driver, wait, sales_order_data)
```

## Maintenance Notes

- **Add Button on List Page**: The XPath `//button[contains(translate(., 'ADD', 'add'), 'add')...]` is case‑insensitive. Update it if the button text changes.
- **Sales Order Selection**: Assumes the first option in the dropdown is the correct one. If multiple SOs exist, you may need to filter by customer or date.
- **Commodity Selection**: Uses partial text match (`contains(normalize-space(), ...)`). Ensure test data item names are unique enough.
- **FIFO Allocation**: The script processes rows in DOM order. It assumes the table is already sorted by transaction date (oldest first). If the UI does not guarantee this, the allocation may not be true FIFO.
- **Quantity Formatting**: Allocation quantity is formatted to 3 decimal places, trailing zeros removed. This matches typical ERP precision requirements.
```