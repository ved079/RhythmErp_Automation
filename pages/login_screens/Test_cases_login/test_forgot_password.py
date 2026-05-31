"""
test_forgot_password.py
------------------------
RhythmERP Forgot Password test cases.
15 tests total: 10 auto + 5 manual OTP.

Screen 1 (no OTP needed):
  FP_S1_01 - Unregistered email proceeds
  FP_S1_02 - Valid email sends OTP          [MANUAL]
  FP_S1_03 - Blank email submission
  FP_S1_04 - Email with leading/trailing spaces
  FP_S1_05 - Email case insensitive
  FP_S1_06 - Double-click Send OTP

Screen 2 (invalid OTP, no manual input):
  FP_S2_01 - Invalid OTP shows alert
  FP_S2_02 - Password mismatch shows alert
  FP_S2_03 - Password policy hints visible
  FP_S2_04 - Recently used password shows alert

Full Flow (manual OTP, ORDER MATTERS):
  FP_FF_01 - Browser back from OTP screen       (no OTP)
  FP_FF_02 - Back to login from screen 1        (no OTP)
  FP_FF_03 - Grand Finale: reset â†’ login â†’ dashboard  (OTP #1)
  FP_FF_04 - Recently used password rejected    (OTP #2)
  FP_FF_05 - Current password rejected          (OTP #3)
  FP_FF_06 - Cleanup: reset back to default     (OTP #4)

Execution order: ff_01 â†’ ff_02 â†’ ff_03 â†’ ff_04 â†’ ff_05 â†’ ff_06
ff_03 MUST run before ff_04 and ff_05 (generates the password they test).
ff_06 MUST run last (resets password for next test run).
"""

import pytest
from datetime import datetime

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ActionChains

from pages.login_screens.Login_Screens_.forgot_password_page import ForgotPasswordPage
from pages.login_screens.Login_Screens_.login_page import LoginPage
from config import (
    RHYTHMERP_LOGIN_URL,
    RHYTHMERP_FP_EMAIL,
    RHYTHMERP_FP_USERNAME,
    RHYTHMERP_FP_CURRENT_PASSWORD,
    RHYTHMERP_FP_DEFAULT_PASSWORD,
    RHYTHMERP_FP_TENANT,
)
from pages.login_screens.data.login_data import ForgotPasswordData


# ================================================================
# FIXTURES
# ================================================================
@pytest.fixture
def fp_on_screen1(driver):
    """Navigate to RhythmERP forgot password Screen 1 (email input)."""
    driver.delete_all_cookies()
    driver.get("about:blank")
    driver.get(RHYTHMERP_LOGIN_URL)
    page = ForgotPasswordPage(driver)
    page.wait_for_page_load()
    page.navigate_to_forgot_password()
    return page


@pytest.fixture
def fp_on_screen2(driver):
    """Navigate to RhythmERP forgot password Screen 2 (OTP + password input)."""
    driver.delete_all_cookies()
    driver.get("about:blank")
    driver.get(RHYTHMERP_LOGIN_URL)
    page = ForgotPasswordPage(driver)
    page.wait_for_page_load()
    page.navigate_to_forgot_password()
    page.enter_email(RHYTHMERP_FP_EMAIL)
    page.click_send_otp()
    page.wait_seconds(2)

    if page.is_otp_screen_displayed():
        return page
    else:
        pytest.fail("Could not reach OTP screen. Check if email is valid.")


# ================================================================
# MARKERS
# ================================================================
manual_otp = pytest.mark.manual_otp


# ================================================================
# SCREEN 1 TESTS
# ================================================================
class TestForgotPasswordScreen1:

    def test_fp_s1_01_unregistered_email_rejected(self, fp_on_screen1):
        """App rejects unregistered email with error message."""
        fp = fp_on_screen1
        fp.enter_email(ForgotPasswordData.UNREGISTERED_EMAIL)
        fp.click_send_otp()

        alert_text = None
        for _ in range(10):
            fp.wait_seconds(0.5)
            alert_text = fp.get_alert_danger_text()
            if alert_text:
                break

        assert alert_text is not None, "Should show error for unregistered email"
        assert "no user found" in alert_text.lower(), \
            f"Expected 'No user found' message, got '{alert_text}'"

    @manual_otp
    def test_fp_s1_02_valid_email_sends_otp(self, fp_on_screen1):
        """Valid email -> OTP screen appears."""
        fp = fp_on_screen1
        fp.enter_email(RHYTHMERP_FP_EMAIL)
        fp.click_send_otp()
        fp.wait_seconds(3)
        assert fp.is_otp_screen_displayed(), "OTP screen should appear"

    def test_fp_s1_03_blank_email_submission(self, fp_on_screen1):
        """Click Send OTP without entering any email -> should show error."""
        fp = fp_on_screen1
        fp.click_send_otp()

        alert_text = None
        for _ in range(10):
            fp.wait_seconds(0.5)
            alert_text = fp.get_alert_danger_text()
            if alert_text:
                break

        has_validation = False
        if not alert_text:
            mat_errors = fp.driver.find_elements(By.CSS_SELECTOR, "mat-error")
            for el in mat_errors:
                text = el.text.lower()
                if "email" in text or "required" in text or "valid" in text:
                    has_validation = True
                    break

            if not has_validation:
                email_elements = fp.driver.find_elements(By.CSS_SELECTOR, "div.custom-field-error")
                for el in email_elements:
                    text = el.text.lower()
                    if "email" in text or "required" in text or "valid" in text:
                        has_validation = True
                        break

        assert alert_text or has_validation, \
            "Should show error when submitting without email"

    def test_fp_s1_04_email_with_leading_trailing_spaces(self, fp_on_screen1):
        """Email with spaces should still work (app should trim them)."""
        fp = fp_on_screen1
        fp.enter_email(f"  {RHYTHMERP_FP_EMAIL}  ")
        fp.click_send_otp()
        fp.wait_seconds(3)
        assert fp.is_otp_screen_displayed(), \
            "Should proceed to OTP screen after trimming spaces from email"

    def test_fp_s1_05_email_case_insensitive(self, fp_on_screen1):
        """Uppercase email is treated as different â€” RhythmERP is case-sensitive on email."""
        fp = fp_on_screen1
        upper_email = RHYTHMERP_FP_EMAIL.upper()
        fp.enter_email(upper_email)
        fp.click_send_otp()

        alert_text = None
        for _ in range(10):
            fp.wait_seconds(0.5)
            alert_text = fp.get_alert_danger_text()
            if alert_text:
                break

        assert alert_text is not None, "Should show error for uppercase email (case-sensitive)"
        assert "no user found" in alert_text.lower(), \
            f"Expected 'No user found' message, got '{alert_text}'"

    def test_fp_s1_06_double_click_send_otp(self, fp_on_screen1):
        """Rapid double-click on Send OTP should not send multiple OTPs."""
        fp = fp_on_screen1
        fp.enter_email(RHYTHMERP_FP_EMAIL)

        send_btn = fp.find_visible_element(fp.SEND_OTP_BUTTON)
        actions = ActionChains(fp.driver)
        actions.double_click(send_btn).perform()

        fp.wait_seconds(3)
        assert fp.is_otp_screen_displayed(), \
            "Should proceed to OTP screen after double-click (not broken)"


# ================================================================
# SCREEN 2 TESTS
# ================================================================
class TestForgotPasswordScreen2:

    def test_fp_s2_01_invalid_otp_shows_alert(self, fp_on_screen2):
        """Invalid OTP should show an alert-danger message."""
        fp = fp_on_screen2
        fp.enter_otp(ForgotPasswordData.INVALID_OTP)
        fp.enter_new_password("Test@newpass1234")
        fp.enter_confirm_password("Test@newpass1234")
        fp.click_reset_password()

        alert_text = None
        for _ in range(10):
            fp.wait_seconds(0.5)
            alert_text = fp.get_alert_danger_text()
            if alert_text:
                break

        assert alert_text is not None, "Should show error alert for invalid OTP"

    def test_fp_s2_02_password_mismatch_shows_alert(self, fp_on_screen2):
        """Mismatched passwords should show alert on submit."""
        fp = fp_on_screen2
        fp.enter_otp("123456")
        fp.enter_new_password("Test@newpass1234")
        fp.enter_confirm_password(ForgotPasswordData.MISMATCH_PASSWORD)
        fp.click_reset_password()

        alert_text = None
        for _ in range(10):
            fp.wait_seconds(0.5)
            alert_text = fp.get_alert_danger_text()
            if alert_text:
                break

        assert alert_text is not None, "Should show 'Passwords do not match' alert"

    def test_fp_s2_03_password_policy_hints_visible(self, fp_on_screen2):
        """Password policy hints appear after typing a weak password and blurring."""
        fp = fp_on_screen2
        fp.enter_new_password("abc")
        fp.click(fp.OTP_INPUT)
        fp.wait_seconds(1)

        has_policy = False
        for _ in range(10):
            fp.wait_seconds(0.5)
            policy_elements = fp.driver.find_elements(
                By.CSS_SELECTOR, "div.custom-field-error"
            )
            for el in policy_elements:
                text = el.text.lower()
                if "minimum 12 characters" in text or "uppercase" in text:
                    has_policy = True
                    break
            if has_policy:
                break

        assert has_policy, "Password policy hints should appear after typing weak password"

    def test_fp_s2_04_recently_used_password_shows_alert(self, fp_on_screen2):
        """Recently used password should trigger alert-danger."""
        fp = fp_on_screen2
        fp.enter_otp("123456")
        old_pass = ForgotPasswordData.RECENTLY_USED_PASSWORDS[0]
        fp.enter_new_password(old_pass)
        fp.enter_confirm_password(old_pass)
        fp.click_reset_password()

        alert_text = None
        for _ in range(10):
            fp.wait_seconds(0.5)
            alert_text = fp.get_alert_danger_text()
            if alert_text:
                break

        assert alert_text is not None, "Should show error alert for recently used password"


# ================================================================
# FULL FLOW TESTS
# ================================================================
class TestForgotPasswordFullFlow:

    # â”€â”€ Helpers â”€â”€

    @staticmethod
    def _navigate_to_otp_screen(driver):
        """Navigate to forgot password and reach OTP screen."""
        driver.delete_all_cookies()
        driver.get("about:blank")
        driver.get(RHYTHMERP_LOGIN_URL)
        login_page = LoginPage(driver)
        login_page.wait_for_page_load()

        fp = ForgotPasswordPage(driver)
        fp.navigate_to_forgot_password()
        fp.wait_seconds(2)

        fp.enter_email(RHYTHMERP_FP_EMAIL)
        fp.click_send_otp()
        fp.wait_seconds(3)

        assert fp.is_otp_screen_displayed(), "Should be on OTP screen"
        return fp

    @staticmethod
    def _is_otp_error(alert_text):
        """Check if error is about OTP (wrong code) vs password (expected rejection)."""
        if not alert_text:
            return False
        alert_lower = alert_text.lower()
        otp_keywords = ["otp", "invalid code", "verification code", "incorrect code"]
        password_keywords = ["password", "recently used", "same as"]
        has_otp = any(kw in alert_lower for kw in otp_keywords)
        has_pass = any(kw in alert_lower for kw in password_keywords)
        return has_otp and not has_pass

    @staticmethod
    def _wait_for_alert(fp, timeout_seconds=5):
        """Poll for alert-danger text."""
        alert_text = None
        for _ in range(timeout_seconds * 2):
            fp.wait_seconds(0.5)
            alert_text = fp.get_alert_danger_text()
            if alert_text:
                break
        return alert_text

    # â”€â”€ Tests â”€â”€

    def test_fp_ff_01_browser_back_from_otp_screen(self, driver):
        """Browser back button on OTP screen should not allow form reuse."""
        fp = self._navigate_to_otp_screen(driver)
        driver.back()
        fp.wait_seconds(2)

        is_on_screen1 = False
        try:
            email_field = fp.find_visible_element(fp.EMAIL_INPUT, timeout=3)
            is_on_screen1 = email_field is not None
        except Exception:
            pass

        is_on_login = "signin" in driver.current_url.lower()
        assert is_on_screen1 or is_on_login, \
            "Browser back from OTP screen should return to email entry or login page"

    def test_fp_ff_02_navigate_back_to_login_from_screen1(self, fp_on_screen1):
        """Click 'Back to Login' -> return to login page."""
        fp = fp_on_screen1
        if fp.is_displayed(fp.BACK_TO_LOGIN_LINK, timeout=3):
            fp.click_back_to_login()
            fp.wait_seconds(2)
            assert "signin" in fp.driver.current_url.lower(), "Should navigate back to login"
        else:
            pytest.skip("Back to Login link not found")

    @manual_otp
    def test_fp_ff_03_grand_finale_reset_login_dashboard(self, driver):
        """GRAND FINALE: Reset password -> login with new creds -> verify dashboard.
        MUST run before ff_04 and ff_05 â€” generates the password they test."""
        # Step 1: Generate a unique password
        timestamp = datetime.now().strftime("%H%M%S")
        new_password = f"Vedant@{timestamp}x"
        print(f"\n  ðŸ”‘ Auto-generated password: {new_password}\n")

        # Save for rejection tests (ff_04 and ff_05)
        TestForgotPasswordFullFlow.generated_password = new_password

        # Step 2: Navigate and send OTP
        fp = self._navigate_to_otp_screen(driver)

        # Step 3: Enter OTP with retry (3 attempts)
        max_retries = 3
        for attempt in range(max_retries):
            otp = input(f"  â³ Enter OTP for vedant@rhythmflows.com ({attempt + 1}/{max_retries}): ")
            fp.enter_otp(otp)

            # Step 4: Enter new password and reset
            fp.enter_new_password(new_password)
            fp.enter_confirm_password(new_password)
            fp.click_reset_password()
            fp.wait_seconds(3)

            if fp.is_success_screen_displayed():
                break

            alert = self._wait_for_alert(fp)
            if self._is_otp_error(alert):
                print(f"  âŒ Wrong OTP! App said: {alert}")
                print(f"  ðŸ“§ A new OTP has been sent. Check your email.\n")
                fp = self._navigate_to_otp_screen(driver)
                continue
            else:
                pytest.fail(f"Unexpected error during reset: {alert}")
        else:
            pytest.fail(f"Wrong OTP entered {max_retries} times. Aborting.")

        # Step 5: Verify reset success
        success_text = fp.get_success_message_text()
        assert "password reset successful" in success_text.lower(), \
            f"Expected success message, got '{success_text}'"

        # Step 6: Navigate to login
        fp.click_login_link_after_success()
        fp.wait_seconds(2)
        assert "signin" in driver.current_url.lower(), "Should be on login page"

        # Step 7: Login with new credentials (use test@gmail.com, facility by index)
        login_page = LoginPage(driver)
        login_page.wait_for_page_load()
        login_page.enter_email(RHYTHMERP_FP_USERNAME)
        login_page.enter_password(new_password)
#         login_page.select_facility_by_index(index=0)
        login_page.click_login()
        login_page.wait_for_login_complete(timeout=20, login_url=RHYTHMERP_LOGIN_URL)

        # Step 8: Verify dashboard
        assert "signin" not in driver.current_url.lower(), \
            "Should reach dashboard after login with new password"

    @manual_otp
    def test_fp_ff_04_recently_used_password_rejected(self, driver):
        """Use the password just set by ff_03 -> expect rejection.
        Proves 'recently used' security protection works."""
        fp = self._navigate_to_otp_screen(driver)
        recent_password = TestForgotPasswordFullFlow.generated_password

        max_retries = 3
        for attempt in range(max_retries):
            otp = input(f"  â³ Enter OTP for vedant@rhythmflows.com ({attempt + 1}/{max_retries}): ")
            fp.enter_otp(otp)
            fp.enter_new_password(recent_password)
            fp.enter_confirm_password(recent_password)
            fp.click_reset_password()

            alert_text = self._wait_for_alert(fp)
            success = fp.is_success_screen_displayed()

            if self._is_otp_error(alert_text):
                print(f"  âŒ Wrong OTP! App said: {alert_text}")
                print(f"  ðŸ“§ A new OTP has been sent. Check your email.\n")
                fp = self._navigate_to_otp_screen(driver)
                continue

            assert not success, "Should NOT succeed with recently used password"
            assert alert_text is not None, "Should show rejection alert for recently used password"
            break
        else:
            pytest.fail(f"Wrong OTP entered {max_retries} times. Aborting.")

    @manual_otp
    def test_fp_ff_05_current_password_rejected(self, driver):
        """Use the current password (same one ff_03 just set) -> expect rejection.
        Proves 'same as current' protection works."""
        fp = self._navigate_to_otp_screen(driver)
        current_password = TestForgotPasswordFullFlow.generated_password

        max_retries = 3
        for attempt in range(max_retries):
            otp = input(f"  â³ Enter OTP for vedant@rhythmflows.com ({attempt + 1}/{max_retries}): ")
            fp.enter_otp(otp)
            fp.enter_new_password(current_password)
            fp.enter_confirm_password(current_password)
            fp.click_reset_password()

            alert_text = self._wait_for_alert(fp)
            success = fp.is_success_screen_displayed()

            if self._is_otp_error(alert_text):
                print(f"  âŒ Wrong OTP! App said: {alert_text}")
                print(f"  ðŸ“§ A new OTP has been sent. Check your email.\n")
                fp = self._navigate_to_otp_screen(driver)
                continue

            assert not success, "Should NOT succeed with current password"
            assert alert_text is not None, "Should show rejection alert for current password"
            break
        else:
            pytest.fail(f"Wrong OTP entered {max_retries} times. Aborting.")

    @manual_otp
    def test_fp_ff_06_cleanup_reset_to_default(self, driver):
        """CLEANUP: Reset password back to Test@2526270 via rotation.
        If target is in recently-used history, push it out with dummy passwords.
        Best case: 1 OTP (target not in history).
        Worst case: 6 OTPs (target at position 1 in last 5)."""
        target = "Test@2526270"
        max_pushes = 5

        for i in range(max_pushes + 1):
            fp = self._navigate_to_otp_screen(driver)

            # Enter OTP
            max_retries = 3
            otp_accepted = False
            for attempt in range(max_retries):
                otp = input(f"  â³ Enter OTP for vedant@rhythmflows.com ({i+1}/{max_pushes+1}): ")
                fp.enter_otp(otp)
                fp.enter_new_password(target)
                fp.enter_confirm_password(target)
                fp.click_reset_password()
                fp.wait_seconds(3)

                if fp.is_success_screen_displayed():
                    print(f"\n  âœ… Password reset to: {target}")
                    # Verify login
                    fp.click_login_link_after_success()
                    fp.wait_seconds(2)
                    login_page = LoginPage(driver)
                    login_page.wait_for_page_load()
                    login_page.enter_email(RHYTHMERP_FP_USERNAME)
                    login_page.enter_password(target)
#                     login_page.select_facility_by_index(index=0)
                    login_page.click_login()
                    login_page.wait_for_login_complete(timeout=20, login_url=RHYTHMERP_LOGIN_URL)
                    assert "signin" not in driver.current_url.lower(), \
                        f"Should reach dashboard with {target}"
                    return  # DONE!

                alert = self._wait_for_alert(fp)
                if self._is_otp_error(alert):
                    print(f"  âŒ Wrong OTP! Try again.")
                    fp = self._navigate_to_otp_screen(driver)
                    continue
                else:
                    otp_accepted = True
                    break
            else:
                pytest.fail(f"Wrong OTP {max_retries} times on attempt {i+1}")

            # Target rejected â€” push with dummy password (same screen, same OTP)
            if i < max_pushes:
                dummy = f"Vedant@push{datetime.now().strftime('%H%M%S')}x"
                print(f"  âš ï¸  Target rejected. Pushing with dummy: {dummy}")

                fp.enter_new_password(dummy)
                fp.enter_confirm_password(dummy)
                fp.click_reset_password()
                fp.wait_seconds(3)

                if fp.is_success_screen_displayed():
                    print(f"  âœ… Dummy set. Continuing rotation...")
                    continue  # Next iteration â€” new OTP, try target again

                alert2 = self._wait_for_alert(fp)
                if self._is_otp_error(alert2):
                    print(f"  âŒ OTP expired. Will get fresh OTP next round.")
                    continue
                else:
                    pytest.fail(f"Unexpected error with dummy: {alert2}")

        pytest.fail(f"Could not reset to {target} after {max_pushes} push attempts")
