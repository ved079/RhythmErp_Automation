# Forgot Password – Pytest Test Suite

This file contains the complete pytest test suite for the **Forgot Password** flow of the PACS application. It covers:

- **Screen 1** – email entry (6 tests)
- **Screen 2** – OTP + new password (4 tests)
- **Full Flow** – end‑to‑end scenarios (5 tests, including manual OTP entry)

The suite includes both automatic (no manual intervention) and manual OTP tests, with retry logic for OTP entry.

---

## File Location

`pages/login_screens/Test_cases_login/test_forgot_password.py`

---

## Dependencies

The test file imports:

- `pytest`
- `datetime` – for generating unique passwords
- Selenium `By`, `Keys`, `ActionChains`
- `ForgotPasswordPage` and `LoginPage` (page objects)
- `config` – various credentials (`LOGIN_URL`, `FP_EMAIL`, `FP_NEW_PASSWORD`, `FP_USERNAME`, `FP_TENANT`)
- `pages.login_screens.data.login_data.ForgotPasswordData` – test data container

---

## Fixtures

| Fixture           | Scope    | Description                                                                 |
|-------------------|----------|-----------------------------------------------------------------------------|
| `fp_on_screen1`   | function | Navigates to login page, clicks “Forgot Password”, waits on Screen 1 (email entry). Returns `ForgotPasswordPage`. |
| `fp_on_screen2`   | function | Same as above, then enters `FP_EMAIL` and clicks “Send OTP”. Waits for OTP screen. Returns `ForgotPasswordPage`. Fails if OTP screen not reached. |

Both fixtures assume a `driver` fixture is provided (usually from a root `conftest.py`).

---

## Markers

| Marker              | Purpose                                                                 |
|---------------------|-------------------------------------------------------------------------|
| `@pytest.mark.manual_otp` | Marks tests that require the user to type an OTP from their email. These tests will pause for input. |

---

## Test Classes

### 1. `TestForgotPasswordScreen1` – Email Entry Tests (6 tests)

| Test ID                                         | Description                                                                 | Marker       |
|-------------------------------------------------|-----------------------------------------------------------------------------|--------------|
| `test_fp_s1_01_unregistered_email_proceeds`     | Unregistered email still proceeds to OTP screen (by design).               | –            |
| `test_fp_s1_02_valid_email_sends_otp`           | Valid email → OTP screen appears.                                          | `manual_otp` |
| `test_fp_s1_03_blank_email_submission`          | Click Send OTP without email → error alert or field validation.            | –            |
| `test_fp_s1_04_email_with_leading_trailing_spaces` | Spaces are trimmed; app proceeds to OTP screen.                           | –            |
| `test_fp_s1_05_email_case_insensitive`          | Uppercase email works same as lowercase.                                   | –            |
| `test_fp_s1_06_double_click_send_otp`           | Double‑clicking Send OTP does not break the flow.                          | –            |

### 2. `TestForgotPasswordScreen2` – OTP + Password Tests (4 tests)

| Test ID                                         | Description                                                                 | Marker |
|-------------------------------------------------|-----------------------------------------------------------------------------|--------|
| `test_fp_s2_01_invalid_otp_shows_alert`        | Wrong OTP → `.alert-danger` appears.                                        | –      |
| `test_fp_s2_02_password_mismatch_shows_alert`  | Mismatched passwords → error alert appears.                                 | –      |
| `test_fp_s2_03_password_policy_hints_visible`  | Typing weak password and blurring shows policy hints.                       | –      |
| `test_fp_s2_04_recently_used_password_shows_alert` | Using a recently used password → alert appears.                            | –      |

### 3. `TestForgotPasswordFullFlow` – End‑to‑End Flows (5 tests)

| Test ID                                         | Description                                                                 | Marker       |
|-------------------------------------------------|-----------------------------------------------------------------------------|--------------|
| `test_fp_ff_05_browser_back_from_otp_screen`   | Browser back button on OTP screen returns to Screen 1 or login page.       | –            |
| `test_fp_ff_04_grand_finale_reset_login_dashboard` | **Grand Finale** – generates a unique password, resets via OTP, logs in, verifies dashboard. Saves the generated password for later tests. | `manual_otp` |
| `test_fp_ff_01_recently_used_password_rejected` | Uses the password just set by `ff_04` → must be rejected (recently used).  | `manual_otp` |
| `test_fp_ff_02_navigate_back_to_login_from_screen1` | Clicks “Back to Login” link on Screen 1 → returns to login page.           | –            |
| `test_fp_ff_03_current_password_rejected`      | Uses the current password (same as `ff_04` just set) → must be rejected.   | `manual_otp` |

> **Important:** The Grand Finale (`ff_04`) must run **first** among the full flow tests because it stores the generated password in a class variable (`TestForgotPasswordFullFlow.generated_password`). The test class runs tests in the order they appear in the file, so `ff_04` executes before `ff_01` and `ff_03`.

---

## Helper Methods (inside `TestForgotPasswordFullFlow`)

| Method                               | Description                                                                                  |
|--------------------------------------|----------------------------------------------------------------------------------------------|
| `_navigate_to_otp_screen(driver)`    | Navigates to the login page, clicks “Forgot Password”, enters `FP_EMAIL`, sends OTP, and asserts OTP screen is displayed. Returns the `ForgotPasswordPage`. |
| `_is_otp_error(alert_text)`          | Checks if an error message is OTP‑related (e.g., “invalid code”) vs password‑related. Used to distinguish a typo from an expected rejection. |
| `_wait_for_alert(fp, timeout_seconds=5)` | Polls for `.alert-danger` element and returns its text if found within the timeout.         |

---

## Manual OTP Retry Logic

All tests marked `@manual_otp` include a **retry loop** (max 3 attempts). If the tester enters an incorrect OTP:

1. The test detects an OTP‑related error using `_is_otp_error()`.
2. It prints a message and automatically navigates back to the OTP screen (requesting a new OTP).
3. The loop continues up to 3 times.

This makes the tests robust against mistyped OTPs and does not require restarting the test.

---

## Running the Tests

Use the `runner.py` script located in the same directory. Examples:

```bash
# Run all tests (manual OTP tests will pause for input)
python runner.py

# Run only automated tests (skip manual OTP)
python runner.py --auto-only

# Run only Screen 1 tests
python runner.py --screen1

# Run only full flow tests (requires OTP)
python runner.py --full-flow

# Run a single test by name
python runner.py -k "test_fp_s1_03"
```

See `runner.py` documentation for more details.

---

## Configuration Requirements

The following variables must be defined in `config.py`:

- `LOGIN_URL`
- `FP_EMAIL` – a valid email that exists in the system
- `FP_NEW_PASSWORD` – a valid new password (used in Screen 2 tests)
- `FP_USERNAME` – the username/email used for login after reset
- `FP_TENANT` – the facility name to select during login
- (Optional) `FP_ALT_PASSWORD`, `FP_CURRENT_PASSWORD`, `FP_OLD_PASSWORDS` – used in `ForgotPasswordData`

Also, a `driver` fixture must be available (usually from a root `conftest.py`).

---

## Notes

- The Grand Finale (`ff_04`) **changes the password** of the account (`FP_EMAIL`). After running this test, the account’s password is updated to the generated value. The subsequent tests (`ff_01` and `ff_03`) rely on that new password to verify rejection – they do **not** change it again.
- If you run `ff_04` alone, you will need to manually reset the password back to a known value for future test runs. The test suite does not automatically revert it.
- The test `fp_s1_03` (blank email submission) uses a loop to look for an error alert; it also checks for `mat-error` elements and custom field errors as fallbacks – this makes it robust across different UI implementations.
- All `manual_otp` tests print the OTP prompt using `input()`, which requires the `-s` flag (pytest capture disabled). The `runner.py` includes `-s` by default.

---

## Related Files

- `pages/login_screens/Login_Screens_/forgot_password_page.py` – page object used by the tests.
- `pages/login_screens/Login_Screens_/login_page.py` – used for login after password reset.
- `pages/login_screens/data/login_data.py` – provides test data (`ForgotPasswordData` class).
- `pages/login_screens/Test_cases_login/runner.py` – CLI runner for these tests.

---

*Documentation generated for `test_forgot_password.py` – April 2026.*
```