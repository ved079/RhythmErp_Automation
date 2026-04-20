# Supplier Edge Cases Test Module (`test_supplier_edge_cases.py`)

This module contains **negative test scenarios** for the Supplier Registration form. It validates that mandatory field checks and PAN format enforcement work correctly.

## Overview

- Uses `pytest` with a fixture that logs in and navigates to the Supplier page before each test.
- Verifies that submitting an empty form triggers validation errors for **Company Name**, **Phone Number**, and **PAN Number**.
- Verifies that an invalid PAN format (e.g., all digits) is rejected with an appropriate error message.

## Fixture

### `setup_and_navigate(driver, wait)`

Automatically executed before each test method.

| Step | Action |
|------|--------|
| 1 | Navigates to the application URL from `config.URL`. |
| 2 | Performs login via `auth_section.perform_login`. |
| 3 | Navigates to the Supplier Registration page using `nav_section.go_to_supplier_page`. |
| 4 | Waits 2 seconds for Angular to settle. |

## Test Methods

### `test_supplier_empty_form_errors(driver, wait)`

**Purpose:** Ensure that submitting a completely empty Supplier form displays mandatory field validation errors.

**Steps:**
1. Locates and clicks the **Submit** button (using JavaScript to avoid interception).
2. Waits briefly for Angular to render error messages.
3. Collects all visible `<mat-error>` elements and extracts their text content.
4. Logs the list of error texts for debugging.
5. Asserts that the combined error string contains:
   - `"company"` (for Company Name)
   - `"phone"` (for Phone Number)
   - `"pan"` (for PAN Number)

### `test_supplier_invalid_pan_format(driver, wait)`

**Purpose:** Confirm that an improperly formatted PAN (e.g., `"1234567890"`) is rejected by the UI.

**Steps:**
1. Locates the **PAN Number** input field (`id="pan_no"`).
2. Clears it and enters a purely numeric string (`"1234567890"`).
3. Clicks the **Submit** button.
4. Collects all visible error messages from `<mat-error>` elements.
5. Logs the error texts.
6. Asserts that at least one error message contains `"pan"`, `"valid"`, or `"format"`, indicating the bad PAN was caught.

## Logging

The module uses a module‑level logger with timestamps and severity levels.

**Example Console Output:**

```
10:15:32 | INFO     | 
[DEBUG] Empty Supplier Form Errors Found: ['company name is required', 'phone number is required', 'pan is required']
10:15:34 | INFO     | 
[DEBUG] Invalid PAN Errors Found: ['enter a valid pan']
```

## Usage

Run the tests with pytest:

```bash
pytest test_supplier_edge_cases.py -v
```

## Maintenance Notes

- **PAN Input Locator**: The PAN field is located by `id="pan_no"`. Update if the HTML ID changes.
- **Submit Button Selector**: Uses `div.right button.submit`. Adjust if the button structure changes.
- **Error Extraction**: Errors are read from `<mat-error>` tags. This relies on Angular Material's standard validation display.
- **Assertions**: The tests check for substrings in the combined error text to avoid brittle exact‑match failures. If the application's error wording changes, update the expected substrings accordingly.
```