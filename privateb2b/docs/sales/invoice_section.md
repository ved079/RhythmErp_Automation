# Invoice Module Reference (`invoice_section.py`)

This module automates the **Invoice** creation process in the FPC ERP system. It selects a customer, sales type, supply type, picks the first available Dispatch Note, and submits the invoice.

## Main Function

### `fill_invoice_registration(driver, wait, data)`

Creates an invoice based on a Dispatch Note.

| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | `dict` | Dictionary containing `customer_name`, `sales_type`, `supply_type`. Matches `test_data.invoice_data`. |

**Steps Performed:**

1. Selects **Customer** (searchable dropdown).
2. Selects **Sales Type** and **Supply Type** (simple dropdowns).
3. Opens the **Dispatch Note** dropdown and selects the first available option (most recent).
4. Clicks the **Submit** button.
5. Waits for redirect to the invoice list page (or logs validation errors).

## Logging

All actions are logged with timestamps and severity levels (`INFO`, `WARNING`, `ERROR`).

**Example Console Output:**
```
10:15:32 | INFO     | ⚡ Starting Invoice Registration...
10:15:34 | INFO     |    Opened Dispatch Note dropdown
10:15:35 | INFO     |    Selected first Dispatch Note
10:15:36 | INFO     | 📤 Submitting Invoice...
10:15:37 | INFO     |    ✅ Submit button clicked
10:15:40 | INFO     | 🚀 Invoice Registration Completed Successfully!
```

## Usage Example

```python
from privateb2b.invoice_section import fill_invoice_registration
from data.test_data import invoice_data

def test_invoice(driver, wait):
    fill_invoice_registration(driver, wait, invoice_data)
```

## Maintenance Notes

- **Dispatch Note Selection**: The function always selects the **first** option in the dropdown. If multiple Dispatch Notes exist and a specific one is required, the selection logic will need to be updated (e.g., filter by date or customer).
- **Form Submission**: The submit button is located using `div.footer button.submit`. Update the selector if the UI changes.
- **Error Handling**: If the form fails to submit, the function checks for Angular Material validation errors (`mat-error`) and logs them before raising an exception.
```