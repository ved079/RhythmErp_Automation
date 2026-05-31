"""
forgot_password_page.py
------------------------
Page Object Model for Forgot Password flow (3 screens).
Screen 1: Enter Email -> Send OTP
Screen 2: Enter OTP + New Password -> Reset Password
Screen 3: Success -> Back to Login

Inherits all helper methods from BasePage.
Supports multiple products (PACS, RhythmERP) via config overrides.
"""

from selenium.webdriver.support.ui import WebDriverWait

from common.base_page import BasePage
from config import EXPLICIT_WAIT
import config


class ForgotPasswordPage(BasePage):

    # ================================================================
    # LOCATORS — SCREEN 1: Email Input
    # ================================================================
    EMAIL_INPUT = ("css", "input[formcontrolname='email']")
    SEND_OTP_BUTTON = ("xpath", "//span[text()='Send OTP']/ancestor::button")
    FORGOT_PASSWORD_LINK = ("css", "a[href='#/authentication/forgot-password']")
    BACK_TO_LOGIN_LINK = ("css", "a[href='#/authentication/signin']")

    # ================================================================
    # LOCATORS — SCREEN 2: OTP + New Password
    # ================================================================
    OTP_INPUT = ("css", "input[formcontrolname='otp']")
    NEW_PASSWORD_INPUT = ("css", "input[formcontrolname='new_password']")
    CONFIRM_PASSWORD_INPUT = ("css", "input[formcontrolname='confirm_password']")
    RESET_PASSWORD_BUTTON = ("xpath", "//span[text()='Reset Password']/ancestor::button")
    RESEND_OTP_LINK = ("xpath", "//span[contains(text(),'Resend')]/ancestor::a")

    # ================================================================
    # LOCATORS — SCREEN 3: Success
    # ================================================================
    SUCCESS_MESSAGE = ("tag", "h3")

    # ================================================================
    # LOCATORS — ERROR MESSAGES
    # ================================================================
    ERROR_MESSAGE = ("css", "mat-error, div.custom-field-error, .mat-mdc-form-field-error")
    TOAST_MESSAGE = ("css", "snack-bar-container, .mat-snack-bar-container, [role='alert']")
    ALERT_DANGER = ("css", "div.alert.alert-danger")

    # ================================================================
    # NAVIGATION
    # ================================================================
    def navigate_to_forgot_password(self):
        """Click 'Forgot Password' link on the login page to reach Screen 1."""
        self.click(self.FORGOT_PASSWORD_LINK)
        self._wait_for_url_contains("forgot-password")

    def navigate_directly(self):
        """Go directly to forgot password URL."""
        self.driver.get(config.FORGOT_PASSWORD_URL)

    def wait_for_page_load(self):
        """Wait for forgot password page elements to load."""
        self.wait_for_visible(self.EMAIL_INPUT, timeout=10)

    # ================================================================
    # SCREEN 1: EMAIL INPUT
    # ================================================================
    def enter_email(self, email):
        """Clear and type email into the email field."""
        self.type_text(self.EMAIL_INPUT, email)

    def click_send_otp(self):
        """Click the 'Send OTP' button."""
        self.click(self.SEND_OTP_BUTTON)

    def get_email_error(self):
        """Get error message below email field, returns None if no error."""
        return self._get_text_if_visible(self.ERROR_MESSAGE)

    def is_send_otp_button_enabled(self):
        """Check if Send OTP button is clickable/enabled."""
        return self.is_enabled(self.SEND_OTP_BUTTON)

    # ================================================================
    # SCREEN 2: OTP + NEW PASSWORD
    # ================================================================
    def enter_otp(self, otp):
        """Clear and type OTP into the OTP field."""
        self.type_text(self.OTP_INPUT, otp)

    def enter_new_password(self, password):
        """Clear and type new password."""
        self.type_text(self.NEW_PASSWORD_INPUT, password)

    def enter_confirm_password(self, password):
        """Clear and type confirm password."""
        self.type_text(self.CONFIRM_PASSWORD_INPUT, password)

    def click_reset_password(self):
        """Click the 'Reset Password' button."""
        self.click(self.RESET_PASSWORD_BUTTON)

    def get_otp_error(self):
        """Get error message below OTP field."""
        return self._get_text_if_visible(self.ERROR_MESSAGE)

    def is_otp_screen_displayed(self):
        """Check if Screen 2 (OTP + Password) is visible."""
        return self.is_displayed(self.OTP_INPUT, timeout=10)

    def is_reset_button_enabled(self):
        """Check if Reset Password button is clickable/enabled."""
        return self.is_enabled(self.RESET_PASSWORD_BUTTON)

    # ================================================================
    # RESEND OTP
    # ================================================================
    def is_resend_otp_visible(self):
        """Check if Resend OTP link is visible."""
        return self.is_displayed(self.RESEND_OTP_LINK, timeout=5)

    def click_resend_otp(self):
        """Click the 'Resend OTP' link."""
        self.click(self.RESEND_OTP_LINK)

    # ================================================================
    # SCREEN 3: SUCCESS
    # ================================================================
    def is_success_screen_displayed(self):
        """Check if success screen is shown (h3 element visible)."""
        return self.is_displayed(self.SUCCESS_MESSAGE, timeout=10)

    def get_success_message_text(self):
        """Get the text from the success message h3 element."""
        return self.get_text(self.SUCCESS_MESSAGE)

    def click_login_link_after_success(self):
        """Click the login link on the success screen to go back to login."""
        self.click(self.BACK_TO_LOGIN_LINK)
        self._wait_for_url_contains("signin")

    # ================================================================
    # BACK TO LOGIN (from Screen 1)
    # ================================================================
    def click_back_to_login(self):
        """Click 'Back to Login' link on Screen 1."""
        self.click(self.BACK_TO_LOGIN_LINK)
        self._wait_for_url_contains("signin")

    # ================================================================
    # UTILITY METHODS
    # ================================================================
    def get_toast_message(self):
        """Get toast/snackbar notification text, returns None if not visible."""
        return self._get_text_if_visible(self.TOAST_MESSAGE, timeout=8)

    def get_all_error_messages(self):
        """Get all visible error messages on the page."""
        try:
            errors = self.find_elements(self.ERROR_MESSAGE)
            return [e.text.strip() for e in errors if e.text.strip()]
        except Exception:
            return []

    def get_alert_danger_text(self):
        """Return text of alert-danger element if visible, else None."""
        if self.is_displayed(self.ALERT_DANGER, timeout=5):
            return self.get_text(self.ALERT_DANGER)
        return None

    def _get_text_if_visible(self, locator, timeout=5):
        """Get text if element is visible, otherwise return None."""
        if self.is_displayed(locator, timeout=timeout):
            try:
                return self.get_text(locator)
            except Exception:
                return None
        return None

    def _wait_for_url_contains(self, partial_url):
        """Wait until URL contains the given string."""
        WebDriverWait(self.driver, EXPLICIT_WAIT).until(
            lambda d: partial_url in d.current_url
        )