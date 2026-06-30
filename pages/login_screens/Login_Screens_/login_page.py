"""
login_page.py
-------------
Page Object Model for PACS / RhythmERP Login Page.
"""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from common.base_page import BasePage
from common.logger import log
from config import LOGIN_URL, EXPLICIT_WAIT


class LoginPage(BasePage):
    """
    Page Object for the PACS / RhythmERP Login Page.
    """

    # ================================================================
    # LOCATORS
    # ================================================================

    # --- Input Fields ---
    EMAIL_INPUT = ("css", "input[name='Username']")
    PASSWORD_INPUT = ("css", "input[name='Password']")

    # --- Facility Dropdown ---
    # FACILITY_SELECT = ("css", "mat-select")
    # FACILITY_SELECT_TRIGGER = ("css", "mat-select .mat-mdc-select-trigger")

    # --- Login Button ---
    LOGIN_BUTTON = ("xpath", "//span[contains(@class,'mdc-button__label') and text()='Login']/ancestor::button")
    LOGIN_BUTTON_CSS = ("css", "button[type='submit'].mat-mdc-unelevated-button")
    LOGIN_BUTTON_GENERIC = ("xpath", "//button[@type='submit']")

    # --- Error Messages ---
    ERROR_MESSAGE = ("css", ".mat-mdc-snack-bar-container, [role='alert'], .error-message, div.alert.alert-danger")
    TOAST_NOTIFICATION = ("css", "snack-bar-container, .mat-mdc-snack-bar-container")

    # --- Labels ---
    EMAIL_LABEL = ("xpath", "//mat-label[contains(.,'Username') or contains(.,'Email')]")
    PASSWORD_LABEL = ("xpath", "//mat-label[contains(.,'Password')]")
    # FACILITY_LABEL = ("xpath", "//mat-label[contains(.,'Facility') or contains(.,'Tenant')]")

    # ================================================================
    # SPEED CONFIG
    # ================================================================
    _FAST_WAIT = 3        # default wait for most operations
    _OVERLAY_WAIT = 3     # wait for overlay open/close
    _CLICK_WAIT = 2       # button locators
    _INPUT_WAIT = 5       # email/password field visibility

    # ================================================================
    # PAGE ACTIONS
    # ================================================================

    def load(self):
        """Navigate to the login page."""
        log.info("Loading login page...")
        self.navigate_to(LOGIN_URL)
        self.wait_for_page_load()
        log.info("Login page loaded successfully")

    def load_url(self, url):
        """Navigate to a specific login URL (for multi-product support)."""
        log.info(f"Loading login page: {url}")
        self.navigate_to(url)
        self.wait_for_page_load()
        log.info("Login page loaded successfully")

    def wait_for_page_load(self):
        """Wait for login page elements to be fully loaded."""
        try:
            self.wait_for_visible(self.EMAIL_INPUT, timeout=self._INPUT_WAIT)
            self.wait_for_visible(self.PASSWORD_INPUT, timeout=self._INPUT_WAIT)
            log.info("Login page elements are visible")
        except Exception:
            log.error("Login page did not load properly")
            self.take_screenshot("login_page_load_failed")
            raise

    def enter_email(self, email):
        """Type email/username into the email field."""
        log.step(1, f"Entering email: {email}")
        self.type_text(self.EMAIL_INPUT, email, clear_first=True)

    def enter_password(self, password):
        """Type password into the password field."""
        log.step(2, "Entering password")
        self.type_text(self.PASSWORD_INPUT, password, clear_first=True)

    def _dismiss_tenant_dropdown(self):
        """Click on page background to dismiss tenant dropdown (backend bug workaround).

        When a user has only one tenant, the dropdown shouldn't appear but does
        due to a backend bug. Clicking outside the dropdown dismisses it so the
        login button becomes clickable.
        """
        try:
            body = self.driver.find_element(By.TAG_NAME, "body")
            self.driver.execute_script("arguments[0].click();", body)
            time.sleep(0.5)
            log.info("Clicked outside to dismiss tenant dropdown")
        except Exception:
            pass

    # def select_facility(self, facility_name):
    #     """Select a facility from the Angular Material mat-select dropdown by name."""
    #     log.step(3, f"Selecting facility: {facility_name}")
    #
    #     self.dismiss_open_overlays()
    #
    #     self.click(self.FACILITY_SELECT_TRIGGER)
    #
    #     WebDriverWait(self.driver, self._OVERLAY_WAIT).until(
    #         EC.presence_of_element_located(
    #             (By.CSS_SELECTOR, "mat-option")
    #         )
    #     )
    #
    #     option_locator = (
    #         "xpath",
    #         f"//mat-option[contains(.,'{facility_name}')]"
    #     )
    #
    #     try:
    #         self.wait_for_visible(option_locator, timeout=self._OVERLAY_WAIT)
    #         self.click(option_locator)
    #         log.info(f"Selected facility: {facility_name}")
    #     except Exception:
    #         log.warning("Primary option locator failed, trying fallback...")
    #         fallback_locator = (
    #             "xpath",
    #             f"//div[@role='option' and contains(.,'{facility_name}')]"
    #         )
    #         self.wait_for_visible(fallback_locator, timeout=2)
    #         self.click(fallback_locator)
    #         log.info(f"Selected facility (fallback): {facility_name}")
    #
    #     self.wait_for_overlay_gone(timeout=self._OVERLAY_WAIT)

    # def select_facility_by_index(self, index=0):
    #     """Select facility by index (for blank/invisible text dropdowns).
    #
    #     Used when mat-option text is empty or not visible due to UI bug.
    #     Options render inside cdk-overlay-pane (appended to body).
    #     Waits for the overlay to fully close before returning so the
    #     next action (e.g. click_login) is never blocked by the open panel.
    #     """
    #     log.step(3, f"Selecting facility by index: {index}")
    #
    #     self.dismiss_open_overlays()
    #
    #     self.click(self.FACILITY_SELECT_TRIGGER)
    #
    #     try:
    #         options = WebDriverWait(self.driver, self._OVERLAY_WAIT).until(
    #             EC.presence_of_all_elements_located(
    #                 (By.CSS_SELECTOR, "div.cdk-overlay-pane mat-option")
    #             )
    #         )
    #     except Exception:
    #         log.warning("cdk-overlay-pane mat-option not found, trying panel fallback...")
    #         options = WebDriverWait(self.driver, self._OVERLAY_WAIT).until(
    #             EC.presence_of_all_elements_located(
    #                 (By.CSS_SELECTOR, ".mat-mdc-select-panel mat-option")
    #             )
    #         )
    #
    #     if index >= len(options):
    #         raise Exception(
    #             f"Index {index} out of range — only {len(options)} option(s) found"
    #         )
    #
    #     self.driver.execute_script("arguments[0].click();", options[index])
    #     log.info(f"Selected facility option at index {index}")
    #
    #     self.wait_for_overlay_gone(timeout=self._OVERLAY_WAIT)



    def click_login(self):
        """Click the Login button twice to handle tenant dropdown backend bug."""
        from selenium.common.exceptions import ElementNotInteractableException
        login_btn = self.driver.find_element(*self.LOGIN_BUTTON)
        try:
            login_btn.click()
        except ElementNotInteractableException:
            # Overlay blocking click (headless/slow server) — use ActionChains which
            # moves mouse to element center and fires real events Angular responds to
            ActionChains(self.driver).move_to_element(login_btn).click().perform()
        self.wait_seconds(1)
        try:
            login_btn = self.driver.find_element(*self.LOGIN_BUTTON)
            login_btn.click()
        except Exception:
            pass  # If first click already logged in, second will fail — that's fine

    def login_default(self):
        """Login using default PACS credentials from config."""
        from config import PACS_EMAIL, PACS_PASSWORD
        self.login(PACS_EMAIL, PACS_PASSWORD)

    def login_rhythmerp(self):
        """Login using RhythmERP credentials from config."""
        from config import RHYTHMERP_EMAIL, RHYTHMERP_PASSWORD, RHYTHMERP_LOGIN_URL
        log.info("Starting RhythmERP login flow...")
        self.load_url(RHYTHMERP_LOGIN_URL)
        self.enter_email(RHYTHMERP_EMAIL)
        self.enter_password(RHYTHMERP_PASSWORD)
        self._dismiss_tenant_dropdown()
        self.click_login()

    # ================================================================
    # VERIFICATION METHODS
    # ================================================================

    def is_page_loaded(self):
        """Check if login page is fully loaded."""
        email_visible = self.is_displayed(self.EMAIL_INPUT, timeout=self._INPUT_WAIT)
        password_visible = self.is_displayed(self.PASSWORD_INPUT, timeout=3)
        is_loaded = email_visible and password_visible
        log.info(f"Login page loaded: {is_loaded}")
        return is_loaded

    def is_email_field_displayed(self):
        return self.is_displayed(self.EMAIL_INPUT)

    def is_password_field_displayed(self):
        return self.is_displayed(self.PASSWORD_INPUT)

    # def is_facility_dropdown_displayed(self):
    #     return self.is_displayed(self.FACILITY_SELECT)

    def is_login_button_enabled(self):
        try:
            return self.is_enabled(self.LOGIN_BUTTON)
        except Exception:
            return False

    def is_error_message_displayed(self, timeout=3):
        return self.is_displayed(self.ERROR_MESSAGE, timeout=timeout)

    def get_error_message_text(self):
        try:
            return self.get_text(self.ERROR_MESSAGE)
        except Exception:
            return ""

    def wait_for_login_complete(self, timeout=10, login_url=None):
        """Wait for login to complete (URL changes away from login page)."""
        log.info("Waiting for login to complete...")
        check_url = (login_url or LOGIN_URL).lower()
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda driver: check_url not in driver.current_url.lower()
            )
            log.info("Login completed successfully")
            log.info(f"Current URL: {self.driver.current_url}")
            return True
        except Exception:
            log.error("Login did not complete - still on login page")
            self.take_screenshot("login_not_completed")
            return False

    def is_dashboard_visible(self, timeout=8):
        """Check if redirected to dashboard/main page."""
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda driver: "signin" not in driver.current_url.lower()
            )
            return True
        except Exception:
            return False

    def is_still_on_login_page(self):
        return "signin" in self.driver.current_url.lower()

    # def get_selected_facility(self):
    #     try:
    #         selected_text = self.get_text(
    #             ("css", "mat-select .mat-mdc-select-value-text span")
    #         )
    #         return selected_text.strip()
    #     except Exception:
    #         return ""

    # def get_all_facilities(self):
    #     """Open dropdown and return all available options."""
    #     facilities = []
    #     self.dismiss_open_overlays()
    #     self.click(self.FACILITY_SELECT_TRIGGER)
    #     time.sleep(0.3)
    #     try:
    #         options = self.find_elements(("css", "mat-option"))
    #         for option in options:
    #             text = option.text.strip()
    #             if text:
    #                 facilities.append(text)
    #     except Exception:
    #         log.warning("Could not read facility options")
    #     ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
    #     self.wait_for_overlay_gone(timeout=3)
    #     return facilities

    def clear_all_fields(self):
        self.clear_field(self.EMAIL_INPUT)
        self.clear_field(self.PASSWORD_INPUT)
        log.info("All login fields cleared")

    def get_email_value(self):
        return self.get_value(self.EMAIL_INPUT)

    def get_password_value(self):
        return self.get_value(self.PASSWORD_INPUT)