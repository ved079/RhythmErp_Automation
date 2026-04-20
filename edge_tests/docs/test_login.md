# Login Test Module (`test_login.py`)

This module contains **pytest**‑based tests for the login functionality of the FPC ERP system. It covers both invalid login scenarios (wrong credentials, empty fields, whitespace handling) and a valid login flow including tenant selection.

## Purpose

- Validate that the login form correctly rejects invalid credentials with appropriate error messages.
- Ensure that leading/trailing whitespace in the username field is handled gracefully.
- Confirm that a successful login followed by tenant selection lands the user on the main dashboard.

## Class: `TestLogin`

All test methods are contained within this class.

### Helper Methods

#### `safe_type(wait, css_selectors, text)`

Reliably clears and types text into a field, character by character, to avoid Angular’s `.clear()` pitfalls.

| Parameter | Type | Description |
|-----------|------|-------------|
| `wait` | `WebDriverWait` | WebDriverWait instance. |
| `css_selectors` | `list` | List of CSS selectors to try (first clickable wins). |
| `text` | `str` | Text to type into the field. |

**Behavior:**
- Tries each selector until a clickable element is found.
- Clears the field with `Ctrl+A` + `Backspace`.
- Types each character individually with a 0.1s delay (visual verification).
- Returns the element.

#### `click_password_visibility(wait)`

Clicks the password visibility toggle (`mat-icon` containing `"visibility_off"`) to unmask the password field. Includes a 1.5‑second pause so the tester can see the unmasked password.

#### `fill_login_initial(wait, username, password)`

Fills the username and password fields, optionally toggles password visibility, and clicks the login button.

| Parameter | Type | Description |
|-----------|------|-------------|
| `username` | `str` | Username to enter. |
| `password` | `str` | Password to enter. |

#### `select_tenant(wait, tenant_name)`

Selects a tenant from the Angular Material dropdown after the initial login step, and clicks the final login button.

| Parameter | Type | Description |
|-----------|------|-------------|
| `tenant_name` | `str` | Exact tenant name to select. |

### Test Methods

#### `@pytest.mark.parametrize` – `test_invalid_login(driver, wait, username, password, reason)`

Tests various invalid login attempts and asserts that an error message appears.

**Parameters (parametrized):**

| `username` | `password` | `reason` |
|------------|------------|----------|
| `"invalid_user@example.com"` | `config.PASS` | Invalid Username |
| `config.USER` | `"wrong_password"` | Invalid Password |
| `""` | `config.PASS` | Empty Username |
| `config.USER` | `""` | Empty Password |
| `f"   {config.USER}   "` | `config.PASS` | Username With Whitespace |

**Steps:**
1. Navigates to the login URL.
2. Calls `fill_login_initial` with the parametrized credentials.
3. Waits for an error element (e.g., `mat-error`, toast, alert) to appear.
4. Asserts that the error text is non‑empty.
5. Saves a screenshot on failure.

#### `test_valid_login(driver, wait)`

Performs a successful login and tenant selection, then verifies that the dashboard is reached.

**Steps:**
1. Navigates to the login URL.
2. Calls `fill_login_initial` with valid credentials from `config`.
3. Waits for the tenant dropdown to appear; fails if it does not.
4. Calls `select_tenant` with `config.TENANT_NAME`.
5. Waits for a dashboard indicator (e.g., profile icon, navigation menu) to be visible.

## Logging

The module uses a module‑level logger. Warnings are logged if the password visibility icon is not found.

**Example Console Output (Valid Login):**

```
10:00:00 | INFO     | (login steps are logged by auth_section, not this module)
10:00:05 | INFO     | ✅ Login Successful
```

## Usage

Run all login tests with pytest:

```bash
pytest test_login.py -v
```

Run only the valid login test:

```bash
pytest test_login.py::TestLogin::test_valid_login -v
```

## Maintenance Notes

- **Username/Password Selectors**: The `safe_type` method tries `[formcontrolname='username']` and `#mat-input-0`. Update these if the login page HTML changes.
- **Tenant Dropdown**: The tenant selection expects `mat-select[formcontrolname='tenant_name']`. Adjust if the `formcontrolname` differs.
- **Dashboard Indicator**: The success check looks for `.profile-icon, .logout-btn, #user-menu, nav`. Modify this list if the dashboard layout changes.
- **Screenshots**: On failure, screenshots are saved with descriptive names (e.g., `invalid_login_fail_Invalid_Username.png`). Ensure the test has write permissions.
```