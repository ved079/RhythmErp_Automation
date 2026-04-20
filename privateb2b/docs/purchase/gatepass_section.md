
# Gate Pass Module Reference (`gatepass_section.py`)

This module automates the **Gate Pass** creation process in the FPC ERP system. It fills supplier details, vehicle information, and multiple commodity rows (bags and quantity), then submits the form.

## Main Function

### `fill_gatepass_registration(driver, wait, data)`

Orchestrates the complete Gate Pass registration workflow.

| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | `dict` | Dictionary matching the structure of `test_data.gatepass_data`. |

**Steps Performed:**

1. **Transaction Date** – Fills the date using `fill_input`.
2. **Standard Dropdowns** – Supplier, Item Type, Department, Division, Location, Type of Sale, Delivery Terms.
3. **Vehicle & Driver Information** – Vehicle No, Driver Name, Driver Contact, In Time.
4. **Multi‑Item Loop** – For each commodity in `data['items']`:
   - Clicks the **"+" button** (except for the first row) to add a new row.
   - Locates the specific row by XPath.
   - Selects the **Item** from a searchable dropdown.
   - Fills **No. of Bags** and **Quantity**.
5. **Submission** – Clicks the submit button via `click_submit`.

## Logging

All actions are logged with timestamps and severity levels.

**Example Console Output:**

```
15:12:34 | INFO     | ⚡ Starting Gate Pass Registration...
15:12:35 | INFO     |    📅 Setting Transaction Date to: 14/04/2026
15:12:36 | INFO     |    ✅ Filled transaction_date: 14/04/2026
15:12:40 | INFO     |    ✅ Filled vehicle_no: MH12AB1234
15:12:41 | INFO     |    ✅ Filled driver_name: Ramesh
15:12:42 | INFO     |    ✅ Filled driver_contact_no: 9876543210
15:12:43 | INFO     |    ✅ Filled in_time: 10:30
15:12:44 | INFO     |    📦 Adding 1 items to Gate Pass...
15:12:45 | INFO     |       ➡️ Filling Row 1: Soyabean
15:12:48 | INFO     | 📤 Submitting the form...
15:12:49 | INFO     | ✅ Submit button clicked
15:12:52 | INFO     | 🚀 Gate Pass Registration Completed Successfully!
```

## Usage Example

```python
from privateb2b.gatepass_section import fill_gatepass_registration
from data.test_data import gatepass_data

def test_gatepass(driver, wait):
    fill_gatepass_registration(driver, wait, gatepass_data)
```

## Maintenance Notes

- **Row Identification**: The script uses `//tbody[contains(@class, 'main_tbody')]/tr[{index + 1}]` to target each row. If the table structure changes, update this XPath.
- **Item Dropdown**: The option is selected by exact match of the item name using `normalize-space()`. Ensure the test data item names exactly match the UI text.
- **Add Row Button**: The selector `button.apply-button i.fa-plus` relies on a Font Awesome plus icon inside the button. If the icon changes, adjust the selector accordingly.
- **Waits**: A 3‑second sleep after submit allows the list page to load. Consider replacing with an explicit wait for a list‑page element if the load time varies.
```