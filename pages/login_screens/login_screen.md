# Login Screens Module – Complete Documentation

This document covers the **Login Screens** module of the PACS Automation framework. The module provides page objects, test data, and a pytest‑based test suite for:

- **Login** – authentication with email, password, and facility dropdown.
- **Forgot Password** – 3‑screen flow (email → OTP + new password → success).

All code resides under `pages/login_screens/`.

---

## 1. Overview

The `login_screens` module is a self‑contained test module that:

- Models the Login page and the complete Forgot Password flow using the **Page Object Model** (inheriting from `common.base_page.BasePage`).
- Supplies centralised test data (valid/invalid emails, passwords, edge cases) in `login_data.py`.
- Provides a pytest test suite (`test_forgot_password.py`) with **15 tests** divided into three classes:
  - `TestForgotPasswordScreen1` – email entry screen (6 tests)
  - `TestForgotPasswordScreen2` – OTP + password screen (4 tests)
  - `TestForgotPasswordFullFlow` – end‑to‑end flows, including manual OTP entry (5 tests)
- Includes a **test runner** (`runner.py`) that supports filtering tests by markers (`--auto-only`, `--otp-only`, `--screen1`, `--full-flow`, etc.).
- Produces **Excel reports** and **failure screenshots** via common hooks (the root `conftest.py` or a parent fixture).

---

## 2. Directory Structure

```
pages/login_screens/
├── data/
│   ├── login_data.py          → all test data (credentials, error messages)
│   └── __init__.py            (empty)
├── Login_Screens_/
│   ├── login_page.py          → LoginPage (POM)
│   ├── forgot_password_page.py→ ForgotPasswordPage (POM)
│   └── __pycache__/
├── reports/                   → Generated Excel reports (ForgotPassword_*.xlsx)
├── screenshots/               → Failure screenshots (PNG)
├── Test_cases_login/
│   ├── runner.py              → CLI test runner
│   ├── test_forgot_password.py→ pytest test cases
│   └── __pycache__/
└── (no conftest.py – inherits from root or uses common report hooks)
```

---

## 3. Page Object Modules (`Login_Screens_/`)

Both page classes inherit from `common.base_page.BasePage`, which provides reusable methods like `click()`, `type_text()`, `is_displayed()`, `wait_for_visible()`, `take_screenshot()`, etc.

### 3.1 `LoginPage`

**File:** `login_page.py`

**Purpose:** Handle all interactions on the main login screen.

**Key locators (as tuples):**

| Element                   | Locator                                                 |
|---------------------------|---------------------------------------------------------|
| Email input               | `("css", "input[formcontrolname='email']")`             |
| Password input            | `("css", "input[formcontrolname='password']")`          |
| Facility dropdown trigger | `("css", "mat-select .mat-mdc-select-trigger")`         |
| Login button              | `("xpath", "//span[contains(.,'Login')]/ancestor::button")` |

**Important methods:**

- `load()` – navigate to `LOGIN_URL` and wait for page load.
- `login(email, password, facility)` – complete login flow (load → enter email → enter password → select facility → click login).
- `login_default()` – uses credentials from `config.py` (`PACS_EMAIL`, `PACS_PASSWORD`, `PACS_FACILITY`).
- `wait_for_login_complete(timeout)` – waits for URL to change away from `/signin`.
- `get_all_facilities()` – opens the dropdown and returns a list of available facilities.
- `clear_all_fields()`, `get_email_value()`, `get_password_value()` – utilities for negative tests.

**Usage example:**

```python
from pages.login_screens.Login_Screens_.login_page import LoginPage

login_page = LoginPage(driver)
login_page.login_default()   # uses config credentials
assert login_page.wait_for_login_complete()
```

### 3.2 `ForgotPasswordPage`

**File:** `forgot_password_page.py`

**Purpose:** Model the 3‑screen Forgot Password flow.

#### Screen 1 – Email entry

| Action                     | Method                        |
|----------------------------|-------------------------------|
| Enter email                | `enter_email(email)`          |
| Click “Send OTP”           | `click_send_otp()`            |
| Get email field error      | `get_email_error()`           |
| Click “Back to Login”      | `click_back_to_login()`       |

#### Screen 2 – OTP + new password

| Action                     | Method                          |
|----------------------------|---------------------------------|
| Enter OTP                  | `enter_otp(otp)`                |
| Enter new password         | `enter_new_password(pwd)`       |
| Enter confirm password     | `enter_confirm_password(pwd)`   |
| Click “Reset Password”     | `click_reset_password()`        |
| Click “Resend OTP”         | `click_resend_otp()`            |
| Check if OTP screen visible| `is_otp_screen_displayed()`     |

#### Screen 3 – Success

| Action                     | Method                          |
|----------------------------|---------------------------------|
| Check success screen       | `is_success_screen_displayed()` |
| Get success message        | `get_success_message_text()`    |
| Click login link           | `click_login_link_after_success()` |

**Error handling methods:**

- `get_toast_message()` – captures snack‑bar / toast notifications.
- `get_alert_danger_text()` – returns text of `.alert-danger` element (used for OTP / password errors).
- `get_all_error_messages()` – collects all `mat-error` texts.

**Navigation helpers:**

- `navigate_to_forgot_password()` – clicks the “Forgot Password” link on the login page.
- `navigate_directly()` – goes directly to `FORGOT_PASSWORD_URL`.

---

## 4. Test Data (`data/login_data.py`)

Centralised test data for both Login and Forgot Password tests.  
All constants are consumed by the test files – no hard‑coded credentials inside tests.

### 4.1 Login‑related data

| Constant                     | Description                                                                 |
|------------------------------|-----------------------------------------------------------------------------|
| `INVALID_EMAILS`             | List of dicts with malformed or empty email formats.                       |
| `WRONG_PASSWORDS`            | List of wrong password strings (including empty).                          |
| `NEGATIVE_LOGIN_COMBINATIONS`| Structured test cases for wrong email/password/facility combinations.      |
| `CASE_VARIATIONS`            | Email case variations (uppercase, lowercase, mixed).                       |
| `SPACE_VARIATIONS`           | Leading/trailing spaces in email or password.                              |
| `SPECIAL_CHAR_EMAILS`        | Emails with plus, dot, underscore, hyphen.                                 |
| `SPECIAL_CHAR_PASSWORDS`     | XSS, SQL injection, HTML tags, quotes.                                     |
| `UNICODE_EMAILS`             | Accented and Chinese characters.                                           |
| `BOUNDARY_TEST_DATA`         | Very long email / password.                                                |
| `EXPECTED_MESSAGES`          | Dictionary of expected error/success texts (may need adjustment).          |

### 4.2 Forgot Password data (class `ForgotPasswordData`)

All values are loaded from `config.py` (except hard‑coded test strings).

| Attribute                     | Source                                  |
|-------------------------------|-----------------------------------------|
| `VALID_EMAIL`                 | `FP_EMAIL`                              |
| `UNREGISTERED_EMAIL`          | Hard‑coded `"nobody@doesnotexist.com"`  |
| `INVALID_FORMAT_EMAILS`       | List of broken formats                  |
| `VALID_NEW_PASSWORD`          | `FP_NEW_PASSWORD`                       |
| `WEAK_PASSWORDS`              | Dict of 5 weak password examples        |
| `MISMATCH_PASSWORD`           | `FP_CURRENT_PASSWORD` (different from new) |
| `RECENTLY_USED_PASSWORDS`     | `FP_OLD_PASSWORDS` (list)               |
| `SUCCESS_MESSAGE`             | `"Password Reset Successful"`           |
| `PASSWORD_POLICY_LABELS`      | List of expected policy hint texts      |

**Note:** `FP_EMAIL`, `FP_NEW_PASSWORD`, `FP_CURRENT_PASSWORD`, `FP_OLD_PASSWORDS`, `FP_USERNAME`, `FP_TENANT` must be defined in `config.py`.

---

## 5. Test Suite (`Test_cases_login/test_forgot_password.py`)

### 5.1 Fixtures (defined inside the test file)

| Fixture          | Scope    | Description                                                                 |
|------------------|----------|-----------------------------------------------------------------------------|
| `fp_on_screen1`  | function | Navigates to login page, clicks “Forgot Password”, waits on Screen 1.       |
| `fp_on_screen2`  | function | Same, then enters `FP_EMAIL` and clicks “Send OTP” → reaches Screen 2.      |

> **Important:** `fp_on_screen2` requires a valid email (must exist in the system) and sends a real OTP. The test will **pause** for manual OTP entry.

### 5.2 Markers

| Marker          | Purpose                                                                 |
|-----------------|-------------------------------------------------------------------------|
| `@manual_otp`   | Marks tests that require manual OTP entry. Used by `runner.py` filtering. |

### 5.3 Test Classes

#### A. `TestForgotPasswordScreen1` (Screen 1 – Email entry)

| Test ID                     | Description                                                              |
|-----------------------------|--------------------------------------------------------------------------|
| `test_fp_s1_01_unregistered_email_proceeds` | Unregistered email still goes to OTP screen (by design).                 |
| `test_fp_s1_02_valid_email_sends_otp`       | Valid email → OTP screen appears. **(manual OTP)**                       |
| `test_fp_s1_03_blank_email_submission`      | No email → error alert or field validation.                              |
| `test_fp_s1_04_email_with_leading_trailing_spaces` | Spaces trimmed, still proceeds.                                    |
| `test_fp_s1_05_email_case_insensitive`      | Uppercase email works same as lowercase.                                 |
| `test_fp_s1_06_double_click_send_otp`       | Double‑click does not break the flow.                                    |

#### B. `TestForgotPasswordScreen2` (Screen 2 – OTP + password)

| Test ID                     | Description                                                              |
|-----------------------------|--------------------------------------------------------------------------|
| `test_fp_s2_01_invalid_otp_shows_alert`    | Wrong OTP → `.alert-danger` appears.                                     |
| `test_fp_s2_02_password_mismatch_shows_alert` | Mismatched passwords → alert appears.                                   |
| `test_fp_s2_03_password_policy_hints_visible`| Weak password → policy hints appear after blur.                         |
| `test_fp_s2_04_recently_used_password_shows_alert` | Using a recently used password → alert appears.                         |

#### C. `TestForgotPasswordFullFlow` (End‑to‑end)

| Test ID                     | Description                                                              |
|-----------------------------|--------------------------------------------------------------------------|
| `test_fp_ff_05_browser_back_from_otp_screen` | Back button returns to Screen 1 or login.                               |
| `test_fp_ff_04_grand_finale_reset_login_dashboard` | **Grand Finale** – generates a unique password, resets via OTP, logs in, verifies dashboard. Saves the generated password for the next two tests. |
| `test_fp_ff_01_recently_used_password_rejected` | Uses the password just set by ff_04 → must be rejected (recently used). |
| `test_fp_ff_02_navigate_back_to_login_from_screen1` | “Back to Login” link works.                                             |
| `test_fp_ff_03_current_password_rejected` | Uses the same password as current → must be rejected.                   |

> All `@manual_otp` tests include **retry logic** (3 attempts) – if the OTP is typed incorrectly, the test prompts again and automatically requests a new OTP.

---

## 6. Test Runner (`Test_cases_login/runner.py`)

The runner is a CLI wrapper that calls `pytest.main()` with the appropriate keyword filters.

### Usage

| Command                                       | Effect                                                       |
|-----------------------------------------------|--------------------------------------------------------------|
| `python runner.py`                            | Run **all** tests (manual OTP tests will pause for input).   |
| `python runner.py --auto-only`                | Skip manual OTP tests (uses `-m "not manual_otp"`).          |
| `python runner.py --otp-only`                 | **Only** manual OTP tests (requires email).                  |
| `python runner.py --screen1`                  | Run only `TestForgotPasswordScreen1` tests.                  |
| `python runner.py --screen2`                  | Run only `TestForgotPasswordScreen2` tests.                  |
| `python runner.py --full-flow`                | Run only `TestForgotPasswordFullFlow` tests.                 |
| `python runner.py --edge`                     | Run only edge case tests (none currently – placeholder).     |
| `python runner.py -k "fp_s1_03"`              | Run a single test by name (passes unknown args to pytest).   |

**Example – run all auto‑validated tests (no OTP):**

```bash
python runner.py --auto-only
```

---

## 7. Reporting and Screenshots

- **Excel reports** are generated in `reports/` with naming pattern `ForgotPassword_TestReport_YYYYMMDD_HHMMSS.xlsx`.  
  The report is produced by the common `report_generator` (likely invoked by a root `conftest.py` hook).  
- **Failure screenshots** are saved in `screenshots/` as `FAILED_<testname>_<timestamp>.png`.  
  These are captured automatically by the same hook.

If the root `conftest.py` is not present, the tests will still run but no Excel report will be generated. The runner does not rely on a local `conftest.py` – it uses the one from the project root (if any).

---

## 8. Configuration Dependencies (`config.py`)

The following variables **must** be defined in `config.py` (project root):

```python
# Login
LOGIN_URL = "https://.../signin"
PACS_EMAIL = "your_email"
PACS_PASSWORD = "your_password"
PACS_FACILITY = "your_facility"

# Forgot Password
FORGOT_PASSWORD_URL = "https://.../forgot-password"
FP_EMAIL = "user@example.com"          # must exist
FP_NEW_PASSWORD = "NewPass@123"
FP_CURRENT_PASSWORD = "OldPass@123"
FP_OLD_PASSWORDS = ["OldPass1", "OldPass2"]   # list of recently used
FP_USERNAME = "user@example.com"      # same as email or separate username
FP_TENANT = "your_tenant"

# Common
EXPLICIT_WAIT = 30
```

If any of these are missing, the corresponding tests will fail or be skipped.

---

## 9. How to Run Tests

### 9.1 Run all login‑related tests (including manual OTP)

```bash
cd pages/login_screens/Test_cases_login
python runner.py
```

### 9.2 Run only automated tests (no OTP)

```bash
python runner.py --auto-only
```

### 9.3 Run only Screen 2 tests (OTP + password)

```bash
python runner.py --screen2
```

### 9.4 Run the Grand Finale full flow (manual OTP)

```bash
python runner.py -k "test_fp_ff_04"
```

---

## 10. Notes and Tips

- **Manual OTP tests** include a retry loop: you have 3 chances to enter the OTP correctly. If you mistype, the test will automatically request a new OTP and restart the flow.
- The **Grand Finale** (`ff_04`) **must run before** `ff_01` and `ff_03` because it generates the new password that the later tests try to reuse. The runner executes tests in the order they appear in the file, so `ff_04` will run first within its class.
- The `get_alert_danger_text()` method is used heavily – it looks for a `<div class="alert alert-danger">` element. If your application uses a different error container, adjust the locator in `forgot_password_page.py`.
- The `LoginPage` method `get_all_facilities()` uses `ActionChains` to send `ESCAPE` key to close the dropdown – this may need adjustment if the dropdown behaviour differs.
- Screenshots are saved on **any test failure** (including assertion failures and exceptions) because the root `conftest.py` hooks into `pytest_runtest_makereport`.

---

## 11. Extending the Module

To add new test scenarios:

1. **Add test data** in `data/login_data.py` (new dictionaries or constants).
2. **Add a test method** in the appropriate class in `test_forgot_password.py`.
3. If the test requires manual OTP, decorate it with `@manual_otp`.
4. Run the runner with `--auto-only` to skip it, or leave it as is.

To test the **Login page** itself (not just Forgot Password), you can create a new test file `test_login.py` that uses `LoginPage` and the login‑related data from `login_data.py`.

---

*Documentation generated for `pages/login_screens` – covers all files as of April 2026.*
```