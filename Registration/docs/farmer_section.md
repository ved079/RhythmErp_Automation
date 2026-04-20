
# Farmer Registration Module Reference (`farmer_section.py`)

This module automates the **Farmer Registration** form in the FPC ERP system. It fills all required fields (personal details, address, bank information), handles the Angular Material datepicker, and submits the form with verification.

## Functions

### `fill_datepicker(driver, wait, value)`

Fills the Date of Birth field, which uses an Angular Material datepicker.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `value` | `str` | Date in `dd/mm/yyyy` format (e.g., `"07/09/2004"`). |

**Behavior:**
- Locates the datepicker input using the class `mat-datepicker-input`.
- Clicks to focus, clears existing content (`Ctrl+A` + `Backspace`).
- Types the date and presses `Tab` to close the picker and trigger validation.
- Logs success or error (screenshot saved on failure).

---

### `click_submit_and_verify(driver, wait)`

Clicks the **Submit** button and waits for confirmation that the form was successfully saved.

**Behavior:**
- Finds the submit button by XPath (`//button[contains(@class, 'submit') and contains(text(), 'Submit')]`).
- Clicks using JavaScript.
- Waits for a success indicator (list page table, toast, or SweetAlert success popup).
- If validation errors appear, they are logged and a screenshot is saved.
- Raises an exception if submission fails silently.

---

### `fill_registration(driver, wait, data)`

Main function that orchestrates the entire Farmer registration process.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `data` | `dict` | Dictionary containing all farmer fields (must match keys in `test_data.farmer_data`). |

**Steps Performed:**

1. Fills **Name**, **Email**, **Phone**.
2. Fills **Date of Birth** via `fill_datepicker()`.
3. Selects **Gender** and **Caste** from dropdowns.
4. Enters **Password**.
5. Selects **Farmer Category** (defaults to `"Walk-in Farmer"` if not provided).
6. Expands **Address** accordion and fills state, district, taluka, village, pincode, and address lines.
7. Expands **Bank** accordion and fills bank name, IFSC, account number, account holder name, branch code, account type, and bank proof.
8. Checks the confirmation checkbox (if present).
9. Calls `click_submit_and_verify()` to submit and confirm success.

## Logging

All actions are logged with timestamps and severity levels.

**Example Console Output:**
```
10:23:45 | INFO     | ⚡ Starting Farmer Registration...
10:23:46 | INFO     | ✅ Filled Date of Birth: 07/09/2004
10:23:47 | INFO     | 📍 Expanding Address...
10:23:52 | INFO     | 🏦 Expanding Bank...
10:23:58 | INFO     | 📤 Submitting form...
10:24:02 | INFO     | ✅ Submit button clicked
10:24:05 | INFO     | 🚀 Farmer Registration Completed Successfully!
```

## Usage Example

```python
from Registration.farmer_section import fill_registration
from data.test_data import farmer_data

def test_farmer(driver, wait):
    fill_registration(driver, wait, farmer_data)
```

## Maintenance Notes

- **Datepicker Locator**: The function uses `input.mat-datepicker-input`. If multiple datepickers exist on the page, this selector will pick the first one. If needed, make it more specific (e.g., by locating via a parent `mat-form-field`).
- **Accordion Headers**: The Address and Bank sections are expanded by clicking `<strong>` elements containing `"Address"` and `"Bank"`. Update these XPaths if the UI text changes.
- **Dropdowns**: All dropdowns use `control_id` with `searchable=False`. If any dropdown becomes searchable in the future, change `searchable=True`.
- **Checkbox**: The checkbox ID `mat-mdc-checkbox-1-input` is dynamic and may change. It is wrapped in a `try/except` so failure does not crash the test.
```