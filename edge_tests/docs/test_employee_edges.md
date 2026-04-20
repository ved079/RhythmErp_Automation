# Employee Edge Cases Test Module (`test_employee_edge_cases.py`)

This module contains **negative test scenarios** for the Employee Registration form. It validates that mandatory field checks work correctly and that the Employee Name field enforces alphabet‑only input.

## Overview

- Uses `pytest` with a fixture that logs in and navigates to the Employee page before each test.
- Verifies that submitting an empty form triggers validation errors for **Employee Name**, **Email**, **Phone**, and **Maker/Checker**.
- Verifies that entering numbers and special characters in the Employee Name field triggers a validation error.

## Fixture

### `setup_and_navigate(driver, wait)`

Automatically executed before each test method.

| Step | Action |
|------|--------|
| 1 | Navigates to the application URL from `config.URL`. |
| 2 | Performs login via `auth_section.perform_login`. |
| 3 | Navigates to the Employee Registration page using `nav_section.go_to_employee_page`. |
| 4 | Waits 2 seconds for Angular to settle. |

## Test Methods

### `test_employee_empty_form_errors(driver, wait)`

**Purpose:** Ensure that submitting a completely empty Employee form displays mandatory field validation errors.

**Steps:**
1. Locates and clicks the **Submit** button (using JavaScript to avoid interception).
2. Waits briefly for Angular to render error messages.
3. Collects all visible `<mat-error>` elements and extracts their text content.
4. Logs the list of error texts for debugging.
5. Asserts that the combined error string contains:
   - `"name"` (for Employee Name)
   - `"email"` (for Email)
   - `"phone"` or `"mobile"` (for Phone)
   - `"maker"` or `"checker"` (for Maker/Checker)

### `test_employee_name_alphabet_only_validation(driver, wait)`

**Purpose:** Confirm that the Employee Name field rejects numbers and special characters.

**Steps:**
1. Locates the **Employee Name** input (`formcontrolname='emp_name'`).
2. Clears it and enters an invalid string: `"John123!@#"`.
3. Clicks the **Submit** button.
4. Collects all visible error messages from `<mat-error>` elements.
5. Logs the error texts.
6. Asserts that at least one error message contains `"name"`, `"character"`, or `"invalid"`, indicating the bad input was caught.

## Logging

The module uses a module‑level logger with timestamps and severity levels.

**Example Console Output:**

```
10:15:32 | INFO     | 
[DEBUG] Empty Employee Form Errors Found: ['employee name is required', 'email is required', 'phone number is required', 'maker/checker is required']
10:15:34 | INFO     | 
[DEBUG] Invalid Employee Name Errors Found: ['name must contain only letters']
```

## Usage

Run the tests with pytest:

```bash
pytest test_employee_edge_cases.py -v
```

## Maintenance Notes

- **Employee Name Locator**: The name field is located by `//input[@formcontrolname='emp_name']`. Update if the `formcontrolname` changes.
- **Submit Button Selector**: Uses `button.submit`. Adjust if the button structure changes.
- **Error Extraction**: Errors are read from `<mat-error>` tags. This relies on Angular Material's standard validation display.
- **Assertions**: The tests check for substrings in the combined error text to avoid brittle exact‑match failures. If the application's error wording changes, update the expected substrings accordingly.
```