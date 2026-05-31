# ForgotPasswordPage – Page Object Model

This module provides a **Page Object Model (POM)** for the **Forgot Password** flow of the PACS application. The flow consists of three screens:

1. **Screen 1** – Enter email and request an OTP.
2. **Screen 2** – Enter OTP, new password, and confirm password.
3. **Screen 3** – Success message and link back to login.

All methods inherit from `common.base_page.BasePage`, which provides reusable WebDriver actions (click, type, wait, etc.).

---

## File Location

`pages/login_screens/Login_Screens_/forgot_password_page.py`

---

## Dependencies

- `selenium.webdriver.support.ui.WebDriverWait`
- `common.base_page.BasePage`
- `config` – must define:
  - `EXPLICIT_WAIT` (int, default timeout)
  - `FORGOT_PASSWORD_URL` (string, direct URL)
  - `LOGIN_URL` (string, used for back navigation)

---

## Class: `ForgotPasswordPage(BasePage)`

### Locators (class attributes)

All locators are tuples `(strategy, selector)` as expected by `BasePage` methods.

| Name                     | Strategy | Selector                                                       | Screen |
|--------------------------|----------|----------------------------------------------------------------|--------|
| `EMAIL_INPUT`            | css      | `input[formcontrolname='email']`                               | 1      |
| `SEND_OTP_BUTTON`        | xpath    | `//span[text()='Send OTP']/ancestor::button`                   | 1      |
| `FORGOT_PASSWORD_LINK`   | css      | `a[href='#/authentication/forgot-password']`                   | Login  |
| `BACK_TO_LOGIN_LINK`     | css      | `a[href='#/authentication/signin']`                            | 1 / 3  |
| `OTP_INPUT`              | css      | `input[formcontrolname='otp']`                                 | 2      |
| `NEW_PASSWORD_INPUT`     | css      | `input[formcontrolname='new_password']`                        | 2      |
| `CONFIRM_PASSWORD_INPUT` | css      | `input[formcontrolname='confirm_password']`                    | 2      |
| `RESET_PASSWORD_BUTTON`  | xpath    | `//span[text()='Reset Password']/ancestor::button`             | 2      |
| `RESEND_OTP_LINK`        | xpath    | `//span[contains(text(),'Resend')]/ancestor::a`                | 2      |
| `SUCCESS_MESSAGE`        | tag      | `h3`                                                           | 3      |
| `ERROR_MESSAGE`          | css      | `mat-error, div.custom-field-error, .mat-mdc-form-field-error` | 1,2    |
| `TOAST_MESSAGE`          | css      | `snack-bar-container, .mat-snack-bar-container, [role='alert']`| Any    |
| `ALERT_DANGER`           | css      | `div.alert.alert-danger`                                       | Any    |

---

### Navigation Methods

#### `navigate_to_forgot_password()`
Clicks the “Forgot Password” link on the login page and waits for the URL to contain `"forgot-password"`.

#### `navigate_directly()`
Navigates directly to `FORGOT_PASSWORD_URL` (no login page intermediate).

#### `wait_for_page_load()`
Waits for the email input field to be visible (timeout 10 seconds). Assumes Screen 1 is loaded.

---

### Screen 1 – Email Input

| Method | Description |
|--------|-------------|
| `enter_email(email)` | Clears and types the email into the email field. |
| `click_send_otp()` | Clicks the “Send OTP” button. |
| `get_email_error()` | Returns text of the first visible error message under the email field, or `None`. |
| `is_send_otp_button_enabled()` | Checks if the Send OTP button is enabled (clickable). |

---

### Screen 2 – OTP + New Password

| Method | Description |
|--------|-------------|
| `enter_otp(otp)` | Clears and types the OTP. |
| `enter_new_password(password)` | Clears and types the new password. |
| `enter_confirm_password(password)` | Clears and types the confirm password. |
| `click_reset_password()` | Clicks the “Reset Password” button. |
| `get_otp_error()` | Returns error message below the OTP field, or `None`. |
| `is_otp_screen_displayed()` | Returns `True` if the OTP input is visible (timeout 10 sec). |
| `is_reset_button_enabled()` | Checks if the Reset Password button is enabled. |

#### Resend OTP

| Method | Description |
|--------|-------------|
| `is_resend_otp_visible()` | Checks if the “Resend OTP” link is visible (timeout 5 sec). |
| `click_resend_otp()` | Clicks the “Resend OTP” link. |

---

### Screen 3 – Success

| Method | Description |
|--------|-------------|
| `is_success_screen_displayed()` | Returns `True` if the success `h3` is visible (timeout 10 sec). |
| `get_success_message_text()` | Returns the text of the success `h3` element. |
| `click_login_link_after_success()` | Clicks the “Back to Login” link on the success screen and waits for URL to contain `"signin"`. |

---

### Back to Login from Screen 1

#### `click_back_to_login()`
Clicks the “Back to Login” link on Screen 1 (email entry screen) and waits for URL to contain `"signin"`.

---

### Utility Methods

| Method | Description |
|--------|-------------|
| `get_toast_message()` | Returns the text of a toast/snackbar notification (timeout 8 sec), or `None`. |
| `get_all_error_messages()` | Returns a list of all visible error message texts (from `ERROR_MESSAGE` locator). |
| `get_alert_danger_text()` | Returns the text of a visible `.alert.alert-danger` element (timeout 5 sec), or `None`. |
| `_get_text_if_visible(locator, timeout=5)` | Internal helper. Returns element text if visible within timeout, else `None`. |
| `_wait_for_url_contains(partial_url)` | Internal helper. Waits until the current URL contains the given substring (uses `EXPLICIT_WAIT`). |

---

## Usage Example

```python
from pages.login_screens.Login_Screens_.forgot_password_page import ForgotPasswordPage
from config import FP_EMAIL, FP_NEW_PASSWORD

# Assume driver is already launched
fp = ForgotPasswordPage(driver)

# Navigate to Screen 1
fp.navigate_to_forgot_password()
fp.wait_for_page_load()

# Screen 1
fp.enter_email(FP_EMAIL)
fp.click_send_otp()

# Wait for Screen 2
if fp.is_otp_screen_displayed():
    # Manual OTP entry
    otp = input("Enter OTP: ")
    fp.enter_otp(otp)
    fp.enter_new_password(FP_NEW_PASSWORD)
    fp.enter_confirm_password(FP_NEW_PASSWORD)
    fp.click_reset_password()

    # Check success
    if fp.is_success_screen_displayed():
        print("Password reset succeeded!")
        fp.click_login_link_after_success()
    else:
        error = fp.get_alert_danger_text()
        print(f"Reset failed: {error}")
```

---

## Notes

- The class does **not** handle the initial login page – use `LoginPage` for that.
- `get_alert_danger_text()` is particularly useful for OTP and password validation errors (often returned as `.alert-danger`).
- All timeouts are configurable via `EXPLICIT_WAIT` (from `config.py`) and method‑specific overrides.
- The `_get_text_if_visible` helper prevents `NoSuchElementException` when an error element is absent.
- The locators assume Angular Material form controls (`formcontrolname` attributes). If your app uses different selectors, adjust accordingly.

---

## Related Files

- `common/base_page.py` – provides the base class and reusable actions.
- `pages/login_screens/Login_Screens_/login_page.py` – for the main login page.
- `pages/login_screens/data/login_data.py` – test data for Forgot Password.
- `pages/login_screens/Test_cases_login/test_forgot_password.py` – pytest test cases using this page object.

---

*Documentation generated for `forgot_password_page.py` – April 2026.*
```