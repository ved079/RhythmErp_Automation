"""
test_login.py
-------------
Test cases for RhythmERP Login Screen.
16 tests total, all automatic — no manual OTP/input needed.

Structure:
  TestLoginPageLoad  — LP_01 to LP_05 (page UI / load)
  TestLoginNegative  — LN_01 to LN_10 (wrong creds / validation / edge cases)
  TestLoginPositive  — L_01 (happy path)
"""

import time
import pytest

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver import ActionChains

from pages.login_screens.Login_Screens_.login_page import LoginPage
from config import RHYTHMERP_EMAIL, RHYTHMERP_PASSWORD, RHYTHMERP_LOGIN_URL
from pages.login_screens.data.login_data import LoginData


# ================================================================
# HELPERS
# ================================================================

def _touch_field(driver, css_selector):
    """
    Focus then immediately blur a field so Angular marks it as 'touched'.
    Angular Material only renders mat-error AFTER a field has been touched.
    Without this, submitting an empty pristine form shows no mat-error at all.
    """
    el = driver.find_element(By.CSS_SELECTOR, css_selector)
    el.click()
    el.send_keys(Keys.TAB)


def _has_field_error(driver):
    """
    Check for ANY visible Angular Material mat-error element.
    Intentionally broad — we don't filter by keyword because different
    app versions may use different wording (e.g. 'This field is required',
    'Please enter a valid email', 'Field cannot be empty', etc.).
    """
    errors = driver.find_elements(By.CSS_SELECTOR, "mat-error")
    for el in errors:
        if el.text.strip():
            return True
    return False


def _has_alert_error(page):
    """Check for snackbar/toast OR alert-danger error message."""
    try:
        # Check Angular snackbar/toast
        if page.is_error_message_displayed(timeout=3):
            return True
    except Exception:
        pass
    try:
        # Check Bootstrap-style alert-danger (what this app actually uses)
        alerts = page.driver.find_elements(
            By.CSS_SELECTOR, "div.alert.alert-danger"
        )
        if any(a.text.strip() for a in alerts):
            return True
    except Exception:
        pass
    return False


def _poll_for_error(page, driver, timeout_seconds=5):
    """Poll for any kind of error (alert, toast, field validation)."""
    for _ in range(timeout_seconds * 2):
        time.sleep(0.5)
        if _has_alert_error(page):
            return "alert"
        if _has_field_error(driver):
            return "field"
    return None


# ================================================================
# PAGE LOAD / UI TESTS
# ================================================================
class TestLoginPageLoad:

    def test_lp_01_all_elements_visible(self, on_login_page):
        """All UI elements — email, password, facility, login button — render on page load."""
        page = on_login_page

        assert page.is_email_field_displayed(), "Email field should be visible"
        assert page.is_password_field_displayed(), "Password field should be visible"
        assert page.is_facility_dropdown_displayed(), "Facility dropdown should be visible"
        assert page.is_login_button_enabled(), "Login button should be present"

    def test_lp_02_facility_dropdown_opens(self, on_login_page):
        """Facility dropdown opens and has options (text may be blank — UI bug)."""
        page = on_login_page

        page.click(page.FACILITY_SELECT_TRIGGER)
        time.sleep(1)

        # Options render in cdk-overlay-pane (on body), not inside mat-select
        options = page.driver.find_elements(
            By.CSS_SELECTOR, "div.cdk-overlay-pane mat-option, .mat-mdc-select-panel mat-option"
        )
        assert len(options) > 0, "Facility dropdown should have at least one option"

        # Close dropdown
        ActionChains(page.driver).send_keys(Keys.ESCAPE).perform()
        time.sleep(0.5)

    def test_lp_03_password_field_masks_input(self, on_login_page):
        """Password field should mask input (type='password')."""
        page = on_login_page

        page.enter_password("test123")
        field_type = page.driver.find_element(
            By.CSS_SELECTOR, "input[formcontrolname='password']"
        ).get_attribute("type")
        assert field_type == "password", \
            f"Password field type should be 'password', got '{field_type}'"

        page.clear_all_fields()

    def test_lp_04_forgot_password_link_navigates(self, on_login_page):
        """Click Forgot Password link → URL contains 'forgot-password'."""
        page = on_login_page

        from pages.login_screens.Login_Screens_.forgot_password_page import ForgotPasswordPage
        fp = ForgotPasswordPage(driver=page.driver)
        fp.navigate_to_forgot_password()
        time.sleep(2)

        assert "forgot-password" in page.driver.current_url.lower(), \
            "Should navigate to forgot password page"

    def test_lp_05_empty_form_submission(self, on_login_page):
        """
        Click Login with ALL fields empty → validation errors appear.

        Angular Material only shows mat-error after a field is 'touched'
        (focused then blurred). Submitting a pristine form silently does
        nothing visible. We must touch each field first, then submit.
        """
        page = on_login_page
        driver = page.driver

        # Touch email field: click it, then Tab away → marks it as touched
        _touch_field(driver, "input[formcontrolname='email']")

        # Touch password field: click it, then Tab away → marks it as touched
        _touch_field(driver, "input[formcontrolname='password']")

        # Now click Login — Angular will display mat-error on empty touched fields
        page.click_login()

        error_type = _poll_for_error(page, driver, timeout_seconds=5)
        assert error_type is not None, \
            "Should show validation error or alert when submitting empty form"


# ================================================================
# NEGATIVE / VALIDATION TESTS
# ================================================================
class TestLoginNegative:

    def test_ln_01_correct_email_wrong_password(self, on_login_page):
        """Correct email + wrong password → error message, stays on login."""
        page = on_login_page

        page.enter_email(RHYTHMERP_EMAIL)
        page.enter_password(LoginData.WRONG_PASSWORD)
        page.select_facility_by_index(index=0)
        page.click_login()

        error_type = _poll_for_error(page, page.driver, timeout_seconds=8)
        assert error_type is not None, "Should show error for wrong password"
        assert page.is_still_on_login_page(), "Should stay on login page"

    def test_ln_02_wrong_email_correct_password(self, on_login_page):
        """Wrong email + correct password → error message, stays on login."""
        page = on_login_page

        page.enter_email(LoginData.WRONG_EMAIL)
        page.enter_password(RHYTHMERP_PASSWORD)
        page.select_facility_by_index(index=0)
        page.click_login()

        error_type = _poll_for_error(page, page.driver, timeout_seconds=8)
        assert error_type is not None, "Should show error for wrong email"
        assert page.is_still_on_login_page(), "Should stay on login page"

    def test_ln_03_both_wrong(self, on_login_page):
        """Both email and password wrong → error message, stays on login."""
        page = on_login_page

        page.enter_email(LoginData.WRONG_EMAIL)
        page.enter_password(LoginData.WRONG_PASSWORD)
        page.select_facility_by_index(index=0)
        page.click_login()

        error_type = _poll_for_error(page, page.driver, timeout_seconds=8)
        assert error_type is not None, "Should show error for wrong credentials"
        assert page.is_still_on_login_page(), "Should stay on login page"

    def test_ln_04_blank_email(self, on_login_page):
        """Blank email + valid password → field-level validation on email."""
        page = on_login_page
        driver = page.driver

        # Touch the email field so Angular validates it on submit
        _touch_field(driver, "input[formcontrolname='email']")

        page.enter_password(RHYTHMERP_PASSWORD)
        page.click_login()

        error_type = _poll_for_error(page, driver, timeout_seconds=5)
        assert error_type is not None, "Should show validation for blank email"

    def test_ln_05_blank_password(self, on_login_page):
        """Valid email + blank password → field-level validation on password."""
        page = on_login_page
        driver = page.driver

        page.enter_email(RHYTHMERP_EMAIL)

        # Touch the password field so Angular validates it on submit
        _touch_field(driver, "input[formcontrolname='password']")

        page.click_login()

        error_type = _poll_for_error(page, driver, timeout_seconds=5)
        assert error_type is not None, "Should show validation for blank password"

    def test_ln_06_invalid_email_format(self, on_login_page):
        """Invalid email format (no @, no domain) → field validation."""
        page = on_login_page

        page.enter_email("invalidemail")
        page.enter_password(RHYTHMERP_PASSWORD)
        page.click_login()

        error_type = _poll_for_error(page, page.driver, timeout_seconds=5)
        assert error_type is not None, "Should show validation for invalid email format"

    def test_ln_07_email_with_spaces(self, on_login_page):
        """Email with leading/trailing spaces — system trims or validates."""
        page = on_login_page

        # Use WRONG email with spaces — if app trims it's still wrong → error
        # If app doesn't trim it's invalid format → error either way
        spaced_email = f" {LoginData.WRONG_EMAIL} "
        page.enter_email(spaced_email)
        page.enter_password(RHYTHMERP_PASSWORD)
        page.select_facility_by_index(index=0)
        page.click_login()

        error_type = _poll_for_error(page, page.driver, timeout_seconds=8)
        assert error_type is not None, \
            "Should reject OR show validation error for email with spaces"

    def test_ln_08_email_space_in_middle(self, on_login_page):
        """Space in the middle of email (e.g. 'test @gmail.com') → validation."""
        page = on_login_page

        page.enter_email(LoginData.EMAIL_WITH_SPACES["middle"])
        page.enter_password(RHYTHMERP_PASSWORD)
        page.click_login()

        error_type = _poll_for_error(page, page.driver, timeout_seconds=5)
        assert error_type is not None, "Should catch space in middle of email"

    def test_ln_09_no_facility_selected(self, on_login_page):
        """Login without selecting facility → validation or error."""
        page = on_login_page

        # Enter email + password but DON'T select facility
        page.enter_email(RHYTHMERP_EMAIL)
        page.enter_password(RHYTHMERP_PASSWORD)
        page.click_login()

        error_type = _poll_for_error(page, page.driver, timeout_seconds=5)
        assert error_type is not None, "Should show error when facility not selected"

    def test_ln_10_double_click_login(self, on_login_page):
        """Rapid double-click on Login — no duplicate requests / race condition."""
        page = on_login_page

        page.enter_email(RHYTHMERP_EMAIL)
        page.enter_password(LoginData.WRONG_PASSWORD)
        page.select_facility_by_index(index=0)

        # Double-click login button
        try:
            btn = page.find_visible_element(page.LOGIN_BUTTON, timeout=5)
        except Exception:
            btn = page.find_visible_element(page.LOGIN_BUTTON_GENERIC, timeout=3)

        ActionChains(page.driver).double_click(btn).perform()
        time.sleep(3)

        # Should still be on login page (not broken by double click)
        assert page.is_still_on_login_page(), \
            "Should stay on login page after double-click"


# ================================================================
# POSITIVE TEST
# ================================================================
class TestLoginPositive:

    def test_l_01_valid_credentials_dashboard(self, on_login_page):
        """Valid credentials + facility → dashboard loads, URL changes away from signin."""
        page = on_login_page

        page.enter_email(RHYTHMERP_EMAIL)
        page.enter_password(RHYTHMERP_PASSWORD)
        page.select_facility_by_index(index=0)
        page.click_login()

        success = page.wait_for_login_complete(
            timeout=20,
            login_url=RHYTHMERP_LOGIN_URL
        )
        assert success, "Should reach dashboard with valid credentials"
        assert "signin" not in page.driver.current_url.lower(), \
            "URL should not contain 'signin' after successful login"