# LoginPage – Page Object Model for PACS Login

This module provides a **Page Object Model (POM)** for the PACS Login page. It handles:

- Loading the login page
- Entering email/username and password
- Selecting a facility from the Material dropdown
- Clicking the Login button
- Verifying login success or error states
- Utility methods for negative test scenarios

All methods inherit from `common.base_page.BasePage`, which provides reusable WebDriver actions.

---

## File Location

`pages/login_screens/Login_Screens_/login_page.py`

---

## Dependencies

- `selenium.webdriver.common.by.By`
- `selenium.webdriver.support.ui.WebDriverWait`
- `common.base_page.BasePage`
- `common.logger.log` – structured logging with step numbers
- `config` – must define:
  - `LOGIN_URL` (string)
  - `EXPLICIT_WAIT` (int, default timeout)

---

## Class: `LoginPage(BasePage)`

### Locators (class attributes)

All locators are tuples `(strategy, selector)`.

| Name                       | Strategy | Selector                                                                 |
|----------------------------|----------|--------------------------------------------------------------------------|
| `EMAIL_INPUT`              | css      | `input[formcontrolname='email']`                                         |
| `PASSWORD_INPUT`           | css      | `input[formcontrolname='password']`                                      |
| `FACILITY_SELECT`          | css      | `mat-select`                                                             |
| `FACILITY_SELECT_TRIGGER`  | css      | `mat-select .mat-mdc-select-trigger`                                     |
| `LOGIN_BUTTON`             | xpath    | `//span[contains(@class,'mdc-button__label') and text()='Login']/ancestor::button` |
| `LOGIN_BUTTON_CSS`         | css      | `button[type='submit'].mat-mdc-unelevated-button`                        |
| `LOGIN_BUTTON_GENERIC`     | xpath    | `//button[@type='submit']`                                               |
| `ERROR_MESSAGE`            | css      | `.mat-mdc-snack-bar-container, [role='alert'], .error-message`           |
| `TOAST_NOTIFICATION`       | css      | `snack-bar-container, .mat-mdc-snack-bar-container`                      |
| `EMAIL_LABEL`              | xpath    | `//mat-label[contains(.,'Username') or contains(.,'Email')]`             |
| `PASSWORD_LABEL`           | xpath    | `//mat-label[contains(.,'Password')]`                                    |
| `FACILITY_LABEL`           | xpath    | `//mat-label[contains(.,'Facility') or contains(.,'Tenant')]`            |

---

### Page Actions (Main Flow)

#### `load()`
Navigates to `LOGIN_URL` and waits for the page to load (email and password fields visible). Logs each step.

#### `wait_for_page_load()`
Waits for `EMAIL_INPUT` and `PASSWORD_INPUT` to be visible (timeout = `EXPLICIT_WAIT`). Takes a screenshot if failed.

#### `enter_email(email)`
Clears and types the email/username into the email field.
- Logs step number 1 with the email value.

#### `enter_password(password)`
Clears and types the password.
- Logs step number 2 (password value not printed).

#### `select_facility(facility_name)`
Opens the Material dropdown, waits for the option, and clicks it.
- First tries `//mat-option[contains(.,'facility_name')]`.
- If that fails, falls back to `//div[@role='option' and contains(.,'facility_name')]`.
- Logs step number 3.
- Uses a short `time.sleep(0.5)` after clicking the trigger.

#### `click_login()`
Clicks the Login button.
- Tries three locators in order: `LOGIN_BUTTON` (precise), `LOGIN_BUTTON_CSS`, then `LOGIN_BUTTON_GENERIC`.
- Logs step number 4.
- Takes a screenshot if button not found or click fails.

#### `login(email, password, facility)`
Complete login flow: `load()` → `enter_email()` → `enter_password()` → `select_facility()` → `click_login()`.

#### `login_default()`
Convenience method that calls `login()` with credentials from `config.py`:
- `PACS_EMAIL`
- `PACS_PASSWORD`
- `PACS_FACILITY`

---

### Verification Methods

| Method | Description |
|--------|-------------|
| `is_page_loaded()` | Returns `True` if both email and password fields are visible within timeouts. |
| `is_email_field_displayed()` | Checks visibility of email input. |
| `is_password_field_displayed()` | Checks visibility of password input. |
| `is_facility_dropdown_displayed()` | Checks visibility of the mat‑select element. |
| `is_login_button_enabled()` | Returns `True` if the primary Login button is enabled, else `False`. |
| `is_error_message_displayed()` | Checks if any error message (snackbar/alert) is visible (timeout 5 sec). |
| `get_error_message_text()` | Returns text of the first error message, or empty string. |
| `wait_for_login_complete(timeout=20)` | Waits for URL to no longer contain the login page substring (case‑insensitive). Returns `True` on success, `False` otherwise. Takes screenshot on failure. |
| `is_dashboard_visible(timeout=15)` | Returns `True` if URL no longer contains `"signin"`. |
| `is_still_on_login_page()` | Returns `True` if current URL contains `"signin"`. |
| `get_selected_facility()` | Returns the text of the currently selected facility (from the dropdown trigger). |
| `get_all_facilities()` | Opens the dropdown, collects all option texts, closes dropdown with `ESC`, returns list. |
| `clear_all_fields()` | Clears email and password fields using `clear_field()`. |
| `get_email_value()` | Returns the current value of the email input. |
| `get_password_value()` | Returns the current value of the password input. |

---

## Usage Example

### Basic login with default credentials

```python
from pages.login_screens.Login_Screens_.login_page import LoginPage

# Assume driver is already initialized
login_page = LoginPage(driver)
login_page.login_default()
assert login_page.wait_for_login_complete()
assert login_page.is_dashboard_visible()
```

### Custom credentials

```python
login_page.login("user@example.com", "MyPass@123", "Main Facility")
```

### Negative test example (wrong password)

```python
login_page.load()
login_page.enter_email("user@example.com")
login_page.enter_password("wrongpassword")
login_page.select_facility("Main Facility")
login_page.click_login()
assert login_page.is_error_message_displayed()
error_text = login_page.get_error_message_text()
assert "Invalid credentials" in error_text
```

### Retrieve all facilities

```python
facilities = login_page.get_all_facilities()
print(f"Available facilities: {facilities}")
```

---

## Notes

- The `login_default()` method **imports** from `config` inside the function to avoid circular imports at module level.
- Facility selection uses two fallback locators – this makes the page object robust against changes in Angular Material version.
- The `select_facility()` method includes a hard‑coded `time.sleep(0.5)` after clicking the trigger. If your application is very fast, you may reduce this; if slow, increase it.
- The `get_all_facilities()` method sends the `ESCAPE` key to close the dropdown – this is a workaround because Material dropdowns do not auto‑close after reading options.
- All error and toast locators are generic – adjust them if your application uses different CSS classes.

---

## Related Files

- `common/base_page.py` – provides base methods like `click()`, `type_text()`, `is_displayed()`, `take_screenshot()`.
- `common/logger.py` – provides `log` with `step()` method.
- `config.py` – must define `LOGIN_URL`, `EXPLICIT_WAIT`, `PACS_EMAIL`, `PACS_PASSWORD`, `PACS_FACILITY`.
- `pages/login_screens/Login_Screens_/forgot_password_page.py` – for the Forgot Password flow.
- `pages/login_screens/Test_cases_login/test_forgot_password.py` – test examples using this page object.

---

*Documentation generated for `login_page.py` – April 2026.*
```