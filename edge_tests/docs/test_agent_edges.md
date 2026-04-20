# Agent Edge Cases Test Module (`test_agent_edge_cases.py`)

This module contains **negative test scenarios** for the Agent Registration form. It validates that mandatory field checks work correctly and that the Commission field enforces numeric‑only input.

## Overview

- Uses `pytest` with a fixture that logs in and navigates to the Agent page before each test.
- Verifies that submitting an empty form triggers validation errors for **Agent Name**, **Phone**, **Basis Type**, and **Bank Name**.
- Verifies that entering alphabetical letters in the **Commission** field triggers a validation error.

## Fixture

### `setup_and_navigate(driver, wait)`

Automatically executed before each test method.

| Step | Action |
|------|--------|
| 1 | Navigates to the application URL from `config.URL`. |
| 2 | Performs login via `auth_section.perform_login`. |
| 3 | Navigates to the Agent Registration page using `nav_section.go_to_agent_page`. |
| 4 | Waits 2 seconds for Angular to settle. |

## Test Methods

### `test_agent_empty_form_errors(driver, wait)`

**Purpose:** Ensure that submitting a completely empty Agent form displays mandatory field validation errors.

**Steps:**
1. Locates and clicks the **Submit** button (`div.right button.submit`) using JavaScript.
2. Waits briefly for Angular to render error messages.
3. Collects all visible `<mat-error>` elements and extracts their text content.
4. Logs the list of error texts for debugging.
5. Asserts that the combined error string contains:
   - `"name"` (for Agent Name)
   - `"phone"` or `"mobile"` (for Phone)
   - `"basis"` (for Basis Type)
   - `"bank"` (for Bank Name)

### `test_agent_commission_numeric_only_validation(driver, wait)`

**Purpose:** Confirm that the Commission field rejects non‑numeric input.

**Steps:**
1. Locates the **Commission** input (`id="commission"`), scrolls it into view.
2. Clears it and enters `"ABC"`.
3. Clicks the **Submit** button.
4. Collects all visible error messages from `<mat-error>` elements.
5. Logs the error texts.
6. Asserts that at least one error message contains `"commission"`, indicating the letters were rejected.

## Logging

The module uses a module‑level logger with timestamps and severity levels.

**Example Console Output:**

```
10:20:00 | INFO     | 
[DEBUG] Empty Agent Form Errors Found: ['agent name is required', 'phone number is required', 'basis type is required', 'bank name is required']
10:20:02 | INFO     | 
[DEBUG] Invalid Commission Errors Found: ['commission must be a number']
```

## Usage

Run the tests with pytest:

```bash
pytest test_agent_edge_cases.py -v
```

## Maintenance Notes

- **Submit Button Selector**: The Agent page uses `div.right button.submit`. If the footer structure changes, update this selector.
- **Commission Input Locator**: The field is located by `id="commission"`. Update if the HTML ID changes.
- **Error Extraction**: Errors are read from `<mat-error>` tags. This relies on Angular Material's standard validation display.
- **Assertions**: The tests check for substrings in the combined error text to avoid brittle exact‑match failures. If the application's error wording changes, update the expected substrings accordingly.
```