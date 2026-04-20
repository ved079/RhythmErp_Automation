# Farmer Registration Edge Cases Test (`test_registration_edge_cases.py`)

This module contains **negative and boundary tests** for the Farmer Registration form. It validates UI behavior such as preventing double submission and (in commented‑out tests) mandatory field checks, phone/email/pincode validation.

## Purpose

- Ensure the submit button becomes disabled or an overlay appears after clicking submit, preventing duplicate submissions.
- Provide a framework for additional validation tests (currently commented out) covering required fields, phone length, email format, and pincode numeric enforcement.

## Class: `TestRegistrationEdgeCases`

### Fixture

#### `setup_and_navigate(driver, wait)`

Automatically executed before each test method.

| Step | Action |
|------|--------|
| 1 | Navigates to the application URL (`config.URL`). |
| 2 | Performs login via `auth_section.perform_login`. |
| 3 | Navigates to the Farmer Registration page using `nav_section.go_to_farmer_page`. |
| 4 | Waits 2 seconds for Angular to settle. |

### Active Test Method

#### `test_prevent_double_submission_on_save(driver, wait)`

**Purpose:** Verify that after clicking the **Submit** button on a valid form, the UI enters a "locked" state (button disabled or overlay present) to prevent accidental double clicks.

**Steps:**
1. Fills all mandatory Farmer fields with valid data (name, email, phone, password, DOB, gender, caste, address details, pincode).
2. Clicks the **Submit** button.
3. Waits up to 5 seconds for either:
   - The submit button to become `disabled`.
   - A blocking overlay (spinner, SweetAlert, or CDK backdrop) to appear.
4. Asserts that the UI is locked; fails if it remains interactive.

### Commented‑Out Tests (Framework for Future Use)

The following tests are fully implemented but commented out. They can be uncommented and adjusted as needed.

| Test Method | Purpose |
|-------------|---------|
| `test_required_field_errors_on_submit` | Submits an empty form and asserts that specific error messages appear for Name, Phone, DOB, State, and District. |
| `test_invalid_phone_number_length` | Enters a 5‑digit phone number, submits, and verifies a validation error containing "phone", "mobile", or "valid". |
| `test_invalid_email_format` | Enters an email without `@` or domain, submits, and checks for an "email" or "valid" error. |
| `test_pincode_rejects_letters` | Expands the Address accordion, enters letters into the pincode field, submits, and asserts a pincode/number/invalid error. |

## Logging

The module uses a module‑level logger. Example output from the active test:

```
10:15:00 | INFO     | 
[DEBUG] Filling mandatory fields to enable valid submission...
10:15:05 | INFO     | [DEBUG] Form valid. Clicking Submit Button...
10:15:06 | INFO     | [DEBUG] ✅ UI successfully locked down after click.
```

## Usage

Run the active test with pytest:

```bash
pytest test_registration_edge_cases.py::TestRegistrationEdgeCases::test_prevent_double_submission_on_save -v
```

To run all tests (including commented ones after uncommenting):

```bash
pytest test_registration_edge_cases.py -v
```

## Maintenance Notes

- **UI Lock Detection**: The `ui_locked` function checks both the submit button's `disabled` attribute and the presence of overlay elements. If the application uses a different locking mechanism, update this logic.
- **Field Selectors**: The test uses a mix of `formcontrolname`, `id`, and `name` selectors. Adjust if the Farmer form HTML changes.
- **Commented Tests**: These rely on specific error message text. If the application's validation messages change, update the expected substrings in the assertions.
```