# Receipt Module Reference (`receipt_section.py`)

This module automates the **Receipt** creation process in the FPC ERP system. It fills transaction date, selects customer, payment details, optional bank information, and submits the receipt.

## Main Function

### `fill_receipt_registration(driver, wait, data)`

Creates a receipt against an invoice.

| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | `dict` | Dictionary containing receipt details. Matches `test_data.receipt_data`. |

**Steps Performed:**

1. **Transaction Date** – Fills the date, presses ENTER to confirm, TAB to move focus, and ESCAPE to close the calendar overlay. Waits for the datepicker backdrop to disappear.
2. **Receipt Type** – Selects from dropdown (`payment_type_ref_id`).
3. **Department, Division, Location, Type of Sale** – Selects each from dropdowns, pressing ESCAPE after each to clear overlays.
4. **Customer Name** – Selects using a searchable dropdown.
5. **Payment Method** – Selects from dropdown.
6. **Company Account Number (optional)** – If `"First Option"` is specified, picks the first available account; otherwise selects by value.
7. **Customer Bank Name (optional)** – Same logic as Company Account Number.
8. **Submit** – Clicks the submit button and waits for redirect to the list page (or logs validation errors).

## Logging

All actions are logged with timestamps and severity levels (`INFO`, `WARNING`, `ERROR`).

**Example Console Output:**
```
14:30:15 | INFO     | ⚡ Starting Receipt Registration...
14:30:16 | INFO     | ✅ Filled Transaction Date: 14/04/2026
14:30:20 | INFO     |    Selected first Company Account Number
14:30:21 | INFO     |    Selected first Customer Bank Name
14:30:22 | INFO     | 📤 Submitting Receipt...
14:30:23 | INFO     |    ✅ Submit button clicked
14:30:26 | INFO     | 🚀 Receipt Registration Completed Successfully!
```

## Usage Example

```python
from privateb2b.receipt_section import fill_receipt_registration
from data.test_data import receipt_data

def test_receipt(driver, wait):
    fill_receipt_registration(driver, wait, receipt_data)
```

## Maintenance Notes

- **Datepicker Handling**: The function uses a specific sequence (ENTER → TAB → ESCAPE) to reliably close the Angular Material datepicker. If the UI changes, this sequence may need adjustment.
- **Overlay Cleanup**: `driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)` is called after each dropdown to ensure no overlay lingers and blocks subsequent clicks.
- **First Option Selection**: For Company Account and Customer Bank, the function uses `overlay.find_elements(By.TAG_NAME, "mat-option")[0]` instead of `:first-child` CSS selector, which is more reliable in Angular applications.
- **Optional Fields**: Company Account Number and Customer Bank Name are optional; if not provided or set to `"First Option"`, the function handles them gracefully.
```