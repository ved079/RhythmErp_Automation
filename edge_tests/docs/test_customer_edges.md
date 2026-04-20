# Customer Edge Cases Test Module (`test_customer_edge_cases.py`)

This module contains **negative test scenarios** for the Customer Registration form. It validates that mandatory field checks work correctly and that the Deposit field inside Additional Details enforces numeric‑only input.

## Overview

- Uses `pytest` with a fixture that logs in and navigates to the Customer page before each test.
- Verifies that submitting an empty form triggers validation errors for **Company Name**, **Mobile Number**, **PAN Number**, and **Supply/Customer Type**.
- Verifies that entering alphabetical letters in the **Deposit** field (inside the Additional Details accordion) triggers a validation error.

## Fixture

### `setup_and_navigate(driver, wait)`

Automatically executed before each test method.

| Step | Action |
|------|--------|
| 1 | Navigates to the application URL from `config.URL`. |
| 2 | Performs login via `auth_section.perform_login`. |
| 3 | Navigates to the Customer Registration page using `nav_section.go_to_customer_page`. |
| 4 | Waits 2 seconds for Angular to settle. |

## Test Methods

### `test_customer_empty_form_errors(driver, wait)`

**Purpose:** Ensure that submitting a completely empty Customer form displays mandatory field validation errors.

**Steps:**
1. Locates and clicks the **Submit** button (`div.right button.submit`) using JavaScript.
2. Waits briefly for Angular to render error messages.
3. Collects all visible `<mat-error>` elements and extracts their text content.
4. Logs the list of error texts for debugging.
5. Asserts that the combined error string contains:
   - `"company"` (for Company Name)
   - `"phone"` or `"mobile"` (for Mobile Number)
   - `"pan"` (for PAN Number)
   - `"supply"` or `"type"` (for Supply/Customer Type)

### `test_customer_deposit_numeric_only_validation(driver, wait)`

**Purpose:** Confirm that the Deposit field rejects non‑numeric input.

**Steps:**
1. Expands the **Additional Details** accordion so the Deposit field becomes visible.
2. Locates the **Deposit** input (`id="deposit"`), scrolls it into view.
3. Clears it and enters `"ABC"`.
4. Clicks the **Submit** button.
5. Collects all visible error messages from `<mat-error>` elements.
6. Logs the error texts.
7. Asserts that at least one error message contains `"deposit"`, indicating the letters were rejected.

## Logging

The module uses a module‑level logger with timestamps and severity levels.

**Example Console Output:**

```
10:25:00 | INFO     | 
[DEBUG] Empty Customer Form Errors Found: ['company name is required', 'mobile number is required', 'pan is required', 'supply type is required']
10:25:02 | INFO     | 
[DEBUG] Invalid Deposit Errors Found: ['deposit must be a number']
```

## Usage

Run the tests with pytest:

```bash
pytest test_customer_edge_cases.py -v
```

## Maintenance Notes

- **Submit Button Selector**: The Customer page uses `div.right button.submit`. If the footer structure changes, update this selector.
- **Deposit Input Locator**: The field is located by `id="deposit"`. Update if the HTML ID changes.
- **Accordion Expansion**: The Additional Details accordion is opened by clicking a header containing `"Additional Details"`. If the UI text changes, update the XPath.
- **Error Extraction**: Errors are read from `<mat-error>` tags. This relies on Angular Material's standard validation display.
- **Assertions**: The tests check for substrings in the combined error text to avoid brittle exact‑match failures. If the application's error wording changes, update the expected substrings accordingly.
```