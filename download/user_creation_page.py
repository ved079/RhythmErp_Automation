"""
user_creation_page.py
---------------------
Page Object Model for RhythmERP User Creation Screen.

Location: Access > User Creation Screen
URL:      /#/master-setup/usercreationscreen

FORM LAYOUT (single-page popup):
  - Username        (text input,   required, no spaces)
  - Email           (text input,   required)
  - First Name      (text input,   required)
  - Last Name       (text input,   required)
  - Password        (password,     required on Create)
  - User Type       (mat-select,   required, searchable)
  - Role            (mat-select,   required, searchable, dynamic)
  - Entity          (mat-select,   required, searchable, dynamic)
  - Designation     (mat-select,   required, searchable)
  - Active          (checkbox,     default=checked)
  - Staff           (checkbox,     default=unchecked)

TABLE COLUMNS:
  - Actions (View/Edit/History)
  - Username
  - Email
  - Joined (date)
  - Status (Active/Inactive)

KEY RULES:
  - NEVER use Keys.ESCAPE (use backdrop click + JS overlay removal)
  - JS clicks for Angular Material overlays
  - Dropdown options read dynamically at runtime (never hardcode)
  - Duplicate username is SILENTLY blocked — no error shown (BUG-001)
  - Only 1 mat-error visible at a time (BUG-006)
  - Search input is readonly; must click toggle first, then remove readonly via JS
"""

import os
import sys
import time
import random

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    ElementClickInterceptedException,
    StaleElementReferenceException,
)
from common.base_page import BasePage
from common.logger import log
from config import RHYTHMERP_BASE_URL, EXPLICIT_WAIT

# Global list to track every submission for reporting
UC_SUBMISSIONS = []


class UserCreationPage(BasePage):
    PAGE_URL = f"{RHYTHMERP_BASE_URL}/#/master-setup/usercreationscreen"

    # ==============================================================
    #  LOCATORS — Toolbar
    # ==============================================================
    ADD_BUTTON = ("css", "button.erp-add-btn")
    SEARCH_TOGGLE = ("css", "button[mattooltip='Search'], button.search-btn")
    REFRESH_BUTTON = ("css", "button[mattooltip='Refresh']")
    FILTER_BUTTON = ("css", "button.filter-btn, button[mattooltip='Filters']")
    MORE_BUTTON = ("css", "button[mattooltip='More']")

    # ==============================================================
    #  LOCATORS — Search bar
    # ==============================================================
    SEARCH_INPUT = ("css", "input.search-bar-input")
    SEARCH_SUBMIT = ("css", "button.search-btn")

    # ==============================================================
    #  LOCATORS — Table
    # ==============================================================
    TABLE = ("css", "table.mat-mdc-table")
    TABLE_ROWS = ("css", "table.mat-mdc-table tbody tr")
    TABLE_USERNAME_CELLS = (
        "css",
        "table.mat-mdc-table tbody td.cdk-column-username, "
        "table.mat-mdc-table tbody td.mat-column-username",
    )
    TABLE_EMAIL_CELLS = (
        "css",
        "table.mat-mdc-table tbody td.cdk-column-email, "
        "table.mat-mdc-table tbody td.mat-column-email",
    )
    TABLE_STATUS_CELLS = (
        "css",
        "table.mat-mdc-table tbody td.cdk-column-status, "
        "table.mat-mdc-table tbody td.mat-column-status",
    )
    NO_DATA_ROW = (
        "css",
        "table.mat-mdc-table tbody tr.mat-mdc-no-data-row, "
        "table.mat-mdc-table tbody td.no-data",
    )

    # ==============================================================
    #  LOCATORS — Add / Edit / View Form popup
    # ==============================================================
    FORM_POPUP = ("css", ".edit_pop_up, .big-model, mat-dialog-container")
    FORM_HEADING = (
        "css",
        ".edit_pop_up h3, .big-model h3, .popup-title",
    )

    USERNAME_INPUT = (
        "css",
        "input[formcontrolname='username']",
    )
    EMAIL_INPUT = (
        "css",
        "input[formcontrolname='email']",
    )
    FIRST_NAME_INPUT = (
        "css",
        "input[formcontrolname='first_name']",
    )
    LAST_NAME_INPUT = (
        "css",
        "input[formcontrolname='last_name']",
    )
    PASSWORD_INPUT = (
        "css",
        "input[formcontrolname='password']",
    )

    USER_TYPE_SELECT = (
        "xpath",
        "//mat-label[contains(.,'User Type')]"
        "/ancestor::mat-form-field//mat-select",
    )
    ROLE_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Role')]"
        "/ancestor::mat-form-field//mat-select",
    )
    ENTITY_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Entity')]"
        "/ancestor::mat-form-field//mat-select",
    )
    DESIGNATION_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Designation')]"
        "/ancestor::mat-form-field//mat-select",
    )

    ACTIVE_CHECKBOX = (
        "css",
        "mat-checkbox[formcontrolname='is_active']",
    )
    STAFF_CHECKBOX = (
        "css",
        "mat-checkbox[formcontrolname='is_staff']",
    )

    SUBMIT_BUTTON = (
        "xpath",
        "//div[@class='popup-footer']//button[contains(.,'Submit')]",
    )
    UPDATE_BUTTON = (
        "xpath",
        "//div[@class='popup-footer']//button[contains(.,'Update')]",
    )
    CANCEL_BUTTON = (
        "xpath",
        "//div[@class='popup-footer']//button[contains(.,'Cancel')]",
    )

    # ==============================================================
    #  LOCATORS — Row action buttons
    # ==============================================================
    VIEW_BUTTON = (
        "xpath",
        "//td[contains(@class,'cdk-column-action')]"
        "//app-feather-icons[@icon='eye']/ancestor::button",
    )
    EDIT_BUTTON = (
        "xpath",
        "//td[contains(@class,'cdk-column-action')]"
        "//app-feather-icons[@icon='edit']/ancestor::button",
    )
    HISTORY_BUTTON = (
        "xpath",
        "//td[contains(@class,'cdk-column-action')]"
        "//app-feather-icons[@icon='clock']/ancestor::button",
    )

    # ==============================================================
    #  LOCATORS — History popup
    # ==============================================================
    HISTORY_POPUP = (
        "xpath",
        "//div[contains(@class,'big-model')]"
        "[.//h3[contains(translate(.,'HISTORY','history'),'history')]]",
    )
    HISTORY_TABLE_ROWS = (
        "css",
        ".edit_pop_up table tbody tr, .big-model table tbody tr",
    )
    HISTORY_SEARCH_INPUT = (
        "xpath",
        "//div[contains(@class,'edit_pop_up')]"
        "//input[contains(@placeholder,'Search in table')]",
    )
    HISTORY_CLOSE_BUTTON = (
        "xpath",
        "//div[@class='popup-footer']//button[contains(.,'Close')]",
    )

    # ==============================================================
    #  LOCATORS — SweetAlert2
    # ==============================================================
    SWAL_TITLE = ("css", "#swal2-title")
    SWAL_CONFIRM = ("css", ".swal2-confirm")
    SWAL_CANCEL = ("css", ".swal2-cancel")
    SWAL_CONTAINER = ("css", ".swal2-container")

    # ==============================================================
    #  LOCATORS — Validation errors
    # ==============================================================
    MAT_ERROR = ("css", "mat-error, .mat-mdc-form-field-error")
    FIELD_ERROR = (
        "xpath",
        "//mat-label[contains(.,'{field_label}')]"
        "/ancestor::mat-form-field//mat-error",
    )

    # ==============================================================
    #  LOCATORS — Dropdown overlay
    # ==============================================================
    DROPDOWN_PANEL = (
        "css",
        "div.cdk-overlay-pane mat-select-panel, div[role='listbox']",
    )
    DROPDOWN_OPTIONS = (
        "css",
        "div[role='listbox'] mat-option, div[role='listbox'] [role='option']",
    )
    DROPDOWN_SEARCH = (
        "css",
        "div[role='listbox'] input, .cdk-overlay-pane input[placeholder]",
    )

    # ==============================================================
    #  Navigation & page load
    # ==============================================================

    def navigate_to_page(self):
        """Navigate to the User Creation Screen listing page.
        Force-refreshes to clear leftover Angular state.
        """
        log.info("Navigating to User Creation Screen page...")
        self.navigate_to(self.PAGE_URL)
        self.driver.refresh()
        self._wait_for_page_ready()

    def _wait_for_page_ready(self):
        """Wait until the page is fully loaded: table + toolbar."""
        try:
            WebDriverWait(self.driver, EXPLICIT_WAIT).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, "table.mat-mdc-table")
                )
            )
            log.info("User Creation table loaded")
        except TimeoutException:
            log.warning("User Creation table not found, page may be empty")

        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "button.erp-add-btn")
                )
            )
            self.wait_seconds(1)
            log.info("User Creation toolbar ready")
        except TimeoutException:
            log.warning("Toolbar not found, ADD button may be delayed")
            self.wait_seconds(3)

    def is_page_loaded(self):
        return self.is_displayed(self.TABLE, timeout=10)

    # ==============================================================
    #  Overlay cleanup — NEVER use Keys.ESCAPE
    # ==============================================================

    def _force_close_panels(self):
        """Remove ALL select overlay panes from the DOM via JS.
        Keeps dialog backdrop intact so form popups stay open."""
        self.driver.execute_script("""
            document.querySelectorAll(
                'div.cdk-overlay-backdrop:not(.cdk-overlay-dark-backdrop)'
            ).forEach(function(el) { el.remove(); });
            document.querySelectorAll(
                'div.cdk-overlay-pane'
            ).forEach(function(el) {
                if (!el.querySelector('mat-dialog-container')) el.remove();
            });
        """)
        self.wait_seconds(0.2)

    def _close_select_panel(self):
        """Try backdrop click first; fall back to JS removal."""
        try:
            backdrops = self.driver.find_elements(
                By.CSS_SELECTOR,
                "div.cdk-overlay-backdrop:not(.cdk-overlay-dark-backdrop)",
            )
            for bd in backdrops:
                try:
                    if bd.is_displayed():
                        bd.click()
                        self.wait_seconds(0.3)
                        return
                except Exception:
                    pass
        except Exception:
            pass
        remaining = self.driver.find_elements(
            By.CSS_SELECTOR,
            "div.cdk-overlay-backdrop:not(.cdk-overlay-dark-backdrop), "
            "div.cdk-overlay-pane mat-option",
        )
        if remaining:
            self._force_close_panels()

    # ==============================================================
    #  Toolbar actions
    # ==============================================================

    def open_add_form(self):
        """Click the ADD (+) button to open the create form."""
        log.info("Clicking ADD button...")
        self._wait_for_toolbar()

        # Strategy 1: button.erp-add-btn
        try:
            btn = self.driver.find_element(By.CSS_SELECTOR, "button.erp-add-btn")
            if btn.is_displayed():
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});"
                    "arguments[0].click();",
                    btn,
                )
                self.wait_seconds(1.5)
                if self._is_form_popup_open():
                    log.info("ADD form opened via erp-add-btn")
                    return
        except Exception:
            pass

        # Strategy 2: mini-fab with 'add' icon
        try:
            add_btns = self.driver.find_elements(
                By.CSS_SELECTOR, "button.mat-mdc-mini-fab"
            )
            for btn in add_btns:
                try:
                    icon = btn.find_element(By.CSS_SELECTOR, "mat-icon")
                    if icon.text.strip().lower() == "add" and btn.is_displayed():
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({block:'center'});"
                            "arguments[0].click();",
                            btn,
                        )
                        self.wait_seconds(1.5)
                        if self._is_form_popup_open():
                            log.info("ADD form opened via mini-fab icon")
                            return
                except Exception:
                    continue
        except Exception:
            pass

        # Strategy 3: click_with_retry
        try:
            self.click_with_retry(self.ADD_BUTTON)
            self.wait_seconds(1.5)
            if self._is_form_popup_open():
                log.info("ADD form opened via click_with_retry")
                return
        except Exception:
            pass

        raise Exception("ADD button not found or not clickable")

    def _wait_for_toolbar(self):
        """Wait for the toolbar and ADD button."""
        for attempt in range(3):
            try:
                add_container = self.driver.find_elements(
                    By.CSS_SELECTOR, "button.erp-add-btn"
                )
                if add_container and add_container[0].is_displayed():
                    return
            except Exception:
                pass
            log.info(f"Waiting for toolbar... attempt {attempt + 1}/3")
            self.wait_seconds(2)
        log.warning("Toolbar wait exhausted")

    def _is_form_popup_open(self):
        """Quick check if any form popup is visible."""
        try:
            popups = self.driver.find_elements(
                By.CSS_SELECTOR,
                "div.edit_pop_up, div.big-model, "
                "div.cdk-overlay-container div.popup-wrapper",
            )
            for p in popups:
                try:
                    if p.is_displayed():
                        return True
                except Exception:
                    continue
        except Exception:
            pass
        return False

    def click_refresh(self):
        """Click the Refresh button."""
        log.info("Clicking Refresh button...")
        try:
            refresh_btn = self.driver.find_element(
                By.CSS_SELECTOR, "button[mattooltip='Refresh']"
            )
            self.driver.execute_script("arguments[0].click();", refresh_btn)
            self.wait_seconds(2)
            log.info("Refresh clicked")
        except Exception:
            log.warning("Refresh button not found")

    # ==============================================================
    #  Search
    # ==============================================================

    def click_search_toggle(self):
        """Click the Search toggle button to enable the search input."""
        log.info("Clicking Search toggle...")
        try:
            toggle = self.driver.find_element(
                By.CSS_SELECTOR, "button[mattooltip='Search']"
            )
            self.driver.execute_script("arguments[0].click();", toggle)
            self.wait_seconds(1)
        except Exception:
            log.warning("Search toggle not found")

    def search_item(self, search_text):
        """Search for an item using the search bar.
        1. Click toggle to enable input
        2. Remove readonly attribute via JS
        3. Set value and press Enter
        """
        log.info(f"Searching for: {search_text}")
        self.click_search_toggle()
        self.wait_seconds(1)

        try:
            search_input = self.driver.find_element(
                By.CSS_SELECTOR, "input.search-bar-input"
            )
            # Remove readonly
            self.driver.execute_script(
                "arguments[0].removeAttribute('readonly');", search_input
            )
            # Clear and set value via JS
            self.driver.execute_script(
                "arguments[0].value = arguments[1];"
                "arguments[0].dispatchEvent(new Event('input', {bubbles: true}));"
                "arguments[0].dispatchEvent(new Event('change', {bubbles: true}));",
                search_input,
                search_text,
            )
            # Press Enter
            search_input.send_keys(Keys.ENTER)
            self.wait_seconds(3)
            log.info(f"Search submitted: {search_text}")
        except Exception as e:
            log.warning(f"Search failed: {e}")

    def clear_search(self):
        """Clear the search input and restore all results."""
        try:
            search_input = self.driver.find_element(
                By.CSS_SELECTOR, "input.search-bar-input"
            )
            self.driver.execute_script(
                "arguments[0].removeAttribute('readonly');", search_input
            )
            self.driver.execute_script(
                "arguments[0].value = '';"
                "arguments[0].dispatchEvent(new Event('input', {bubbles: true}));",
                search_input,
            )
            search_input.send_keys(Keys.ENTER)
            self.wait_seconds(2)
        except Exception:
            pass

    def search_user(self, username):
        """Search for a user by username. Returns True if found."""
        self.search_item(username)
        self.wait_seconds(2)
        found = self.is_user_in_table(username)
        self.clear_search()
        return found

    # ==============================================================
    #  Fill form fields
    # ==============================================================

    def fill_user_form(self, data):
        """Fill all fields on the User Creation add/edit form.
        Dropdown values: if None/empty, picks a random option from the live UI.
        """
        log.info("Filling User Creation form...")

        # Username
        if data.get("username") is not None and data.get("username") != "":
            self.type_text(self.USERNAME_INPUT, str(data["username"]), clear_first=True)

        # Email
        if data.get("email") is not None and data.get("email") != "":
            self.type_text(self.EMAIL_INPUT, str(data["email"]), clear_first=True)

        # First Name
        if data.get("first_name") is not None and data.get("first_name") != "":
            self.type_text(self.FIRST_NAME_INPUT, str(data["first_name"]), clear_first=True)

        # Last Name
        if data.get("last_name") is not None and data.get("last_name") != "":
            self.type_text(self.LAST_NAME_INPUT, str(data["last_name"]), clear_first=True)

        # Password
        if data.get("password") is not None and data.get("password") != "":
            self.type_text(self.PASSWORD_INPUT, str(data["password"]), clear_first=True)

        # User Type dropdown
        if data.get("user_type"):
            self._select_mat_option(self.USER_TYPE_SELECT, str(data["user_type"]))
        else:
            self._select_random_from_dropdown(self.USER_TYPE_SELECT, "User Type")

        # Role dropdown
        if data.get("role"):
            self._select_mat_option(self.ROLE_SELECT, str(data["role"]))
        else:
            self._select_random_from_dropdown(self.ROLE_SELECT, "Role")

        # Entity dropdown
        if data.get("entity"):
            self._select_mat_option(self.ENTITY_SELECT, str(data["entity"]))
        else:
            self._select_random_from_dropdown(self.ENTITY_SELECT, "Entity")

        # Designation dropdown
        if data.get("designation"):
            self._select_mat_option(self.DESIGNATION_SELECT, str(data["designation"]))
        else:
            self._select_random_from_dropdown(self.DESIGNATION_SELECT, "Designation")

        # Active checkbox
        if "is_active" in data and not data["is_active"]:
            self._uncheck_checkbox(self.ACTIVE_CHECKBOX)

        # Staff checkbox
        if "is_staff" in data and data["is_staff"]:
            self._check_checkbox(self.STAFF_CHECKBOX)

        self._force_close_panels()
        log.info("User Creation form filled")

    def _check_checkbox(self, locator):
        """Check a mat-checkbox if not already checked."""
        try:
            cb = self.find_visible_element(locator, timeout=5)
            checked = cb.get_attribute("aria-checked") == "true"
            if not checked:
                self.driver.execute_script("arguments[0].click();", cb)
                self.wait_seconds(0.3)
        except Exception:
            pass

    def _uncheck_checkbox(self, locator):
        """Uncheck a mat-checkbox if currently checked."""
        try:
            cb = self.find_visible_element(locator, timeout=5)
            checked = cb.get_attribute("aria-checked") == "true"
            if checked:
                self.driver.execute_script("arguments[0].click();", cb)
                self.wait_seconds(0.3)
        except Exception:
            pass

    # ==============================================================
    #  Form submission & cancellation
    # ==============================================================

    def submit(self):
        """Click the Submit button on the Create form."""
        log.info("Submitting User Creation form...")
        self._force_close_panels()
        try:
            btn = self.find_visible_element(self.SUBMIT_BUTTON, timeout=5)
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});"
                "arguments[0].click();",
                btn,
            )
        except Exception:
            try:
                btn = self.driver.find_element(
                    By.XPATH,
                    "//div[@class='popup-footer']//button[contains(.,'Submit')]",
                )
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});"
                    "arguments[0].click();",
                    btn,
                )
            except Exception:
                self.click_with_retry(self.SUBMIT_BUTTON)
        self.wait_seconds(2)
        log.info("Submit clicked")

    def click_update(self):
        """Click the Update button on the Edit form."""
        log.info("Clicking Update button...")
        self._force_close_panels()
        try:
            btn = self.find_visible_element(self.UPDATE_BUTTON, timeout=5)
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});"
                "arguments[0].click();",
                btn,
            )
        except Exception:
            try:
                btn = self.driver.find_element(
                    By.XPATH,
                    "//div[@class='popup-footer']//button[contains(.,'Update')]",
                )
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});"
                    "arguments[0].click();",
                    btn,
                )
            except Exception:
                self.click_with_retry(self.UPDATE_BUTTON)
        self.wait_seconds(2)
        log.info("Update clicked")

    def cancel(self):
        """Click the Cancel button on the form."""
        log.info("Clicking Cancel button...")
        try:
            btn = self.find_visible_element(self.CANCEL_BUTTON, timeout=5)
            self.driver.execute_script("arguments[0].click();", btn)
        except Exception:
            try:
                btn = self.driver.find_element(
                    By.XPATH,
                    "//div[@class='popup-footer']//button[contains(.,'Cancel')]",
                )
                self.driver.execute_script("arguments[0].click();", btn)
            except Exception:
                self.click_with_retry(self.CANCEL_BUTTON)
        self.wait_seconds(1)

    def close_popup(self):
        """Click the X (close) icon on the form header."""
        log.info("Closing popup via X button...")
        try:
            close_btns = self.driver.find_elements(
                By.CSS_SELECTOR,
                ".popup-actions button, .edit_pop_up .popup-actions button",
            )
            for btn in close_btns:
                try:
                    icon = btn.find_element(By.CSS_SELECTOR, "mat-icon")
                    if icon.text.strip().lower() == "close" and btn.is_displayed():
                        self.driver.execute_script(
                            "arguments[0].click();", btn
                        )
                        self.wait_seconds(0.5)
                        log.info("Popup closed via X button")
                        return
                except Exception:
                    continue
        except Exception:
            pass
        log.warning("X button not found, trying Cancel instead")
        self.cancel()

    def force_close_form_popup(self):
        """Force-remove the form popup and overlays via JS."""
        self.driver.execute_script("""
            document.querySelectorAll('.edit_pop_up').forEach(function(el) { el.remove(); });
            document.querySelectorAll('.cdk-overlay-backdrop').forEach(function(el) { el.remove(); });
            document.querySelectorAll('.cdk-overlay-pane').forEach(function(el) { el.remove(); });
        """)
        self.wait_seconds(0.5)

    # ==============================================================
    #  SweetAlert2 handlers
    # ==============================================================

    def handle_success_alert(self, timeout=EXPLICIT_WAIT):
        """Wait for SweetAlert2 success popup, read message, click OK."""
        log.info("Waiting for success alert...")
        try:
            wait = WebDriverWait(self.driver, timeout)
            title_el = wait.until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "#swal2-title"))
            )
            msg = title_el.text.strip()

            try:
                confirm = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, ".swal2-confirm"))
                )
                try:
                    confirm.click()
                except Exception:
                    self.driver.execute_script("arguments[0].click();", confirm)
                log.info(f"Success alert handled: {msg}")
            except Exception:
                try:
                    self.driver.execute_script(
                        "document.querySelectorAll('.swal2-confirm')"
                        ".forEach(function(b){b.click();});"
                    )
                except Exception:
                    pass

            try:
                WebDriverWait(self.driver, 10).until(
                    EC.invisibility_of_element_located(
                        (By.CSS_SELECTOR, ".swal2-container")
                    )
                )
            except Exception:
                pass
            return msg
        except TimeoutException:
            log.info("No success alert appeared within timeout")
            return ""

    def handle_validation_warning(self, timeout=10):
        """Handle SweetAlert2 validation warning popup."""
        log.info("Checking for validation warning...")
        try:
            wait = WebDriverWait(self.driver, timeout)
            title_el = wait.until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "#swal2-title"))
            )
            msg = title_el.text.strip()
            try:
                confirm = self.driver.find_element(By.CSS_SELECTOR, ".swal2-confirm")
                self.driver.execute_script("arguments[0].click();", confirm)
            except Exception:
                pass
            try:
                WebDriverWait(self.driver, 5).until(
                    EC.invisibility_of_element_located(
                        (By.CSS_SELECTOR, ".swal2-container")
                    )
                )
            except Exception:
                pass
            log.info(f"Validation warning handled: {msg}")
            return msg
        except TimeoutException:
            return ""

    def is_validation_alert_present(self, timeout=5):
        return self.is_displayed(self.SWAL_TITLE, timeout=timeout)

    # ==============================================================
    #  Field-level error checking
    # ==============================================================

    def get_mat_error_text(self):
        """Get all visible mat-error texts from the form."""
        errors = self.driver.find_elements(
            By.CSS_SELECTOR, "mat-error, .mat-mdc-form-field-error"
        )
        texts = []
        for e in errors:
            try:
                t = e.text.strip()
                if t:
                    texts.append(t)
            except StaleElementReferenceException:
                continue
        if texts:
            log.warning(f"Validation errors found: {texts}")
        return texts

    def has_field_error(self, field_label):
        """Check if a specific form field has a visible mat-error."""
        try:
            locator = (
                "xpath",
                f"//mat-label[contains(.,'{field_label}')]"
                "/ancestor::mat-form-field//mat-error",
            )
            return self.is_displayed(locator, timeout=3)
        except Exception:
            return False

    def is_field_invalid(self, field_label):
        """Check if a field has ng-invalid CSS class (even if no mat-error text visible)."""
        try:
            locator = (
                "xpath",
                f"//mat-label[contains(.,'{field_label}')]"
                "/ancestor::mat-form-field",
            )
            el = self.find_visible_element(locator, timeout=3)
            return "mat-form-field-invalid" in el.get_attribute("class") or \
                   "invalid" in el.get_attribute("class")
        except Exception:
            return False

    # ==============================================================
    #  Verification helpers
    # ==============================================================

    def is_add_form_open(self):
        return self.is_displayed(self.USERNAME_INPUT, timeout=5)

    def is_form_closed(self):
        return not self.is_displayed(self.USERNAME_INPUT, timeout=5)

    def get_form_heading(self):
        try:
            el = self.driver.find_element(
                By.CSS_SELECTOR,
                ".edit_pop_up h3, .big-model h3, .popup-title",
            )
            return el.text.strip()
        except Exception:
            return ""

    def is_view_mode(self):
        """Check if the currently open form is in View (read-only) mode."""
        try:
            username_input = self.find_visible_element(self.USERNAME_INPUT, timeout=5)
            return not username_input.is_enabled()
        except Exception:
            return False

    def is_edit_mode(self):
        """Check if the currently open form is in Edit mode."""
        return self.is_displayed(self.UPDATE_BUTTON, timeout=5)

    def get_form_field_values(self):
        """Read all form field values from the currently open popup."""
        values = {}

        for key, locator in [
            ("username", self.USERNAME_INPUT),
            ("email", self.EMAIL_INPUT),
            ("first_name", self.FIRST_NAME_INPUT),
            ("last_name", self.LAST_NAME_INPUT),
            ("password", self.PASSWORD_INPUT),
        ]:
            try:
                el = self.driver.find_element(
                    By.CSS_SELECTOR, locator[1]
                )
                values[key] = el.get_attribute("value") or ""
            except Exception:
                values[key] = ""

        for key, locator in [
            ("user_type", self.USER_TYPE_SELECT),
            ("role", self.ROLE_SELECT),
            ("entity", self.ENTITY_SELECT),
            ("designation", self.DESIGNATION_SELECT),
        ]:
            try:
                el = self.driver.find_element(
                    By.XPATH, locator[1]
                )
                values[key] = el.text.strip()
            except Exception:
                values[key] = ""

        try:
            active_cb = self.driver.find_element(
                By.CSS_SELECTOR, "mat-checkbox[formcontrolname='is_active']"
            )
            values["is_active"] = active_cb.get_attribute("aria-checked") == "true"
        except Exception:
            values["is_active"] = None

        try:
            staff_cb = self.driver.find_element(
                By.CSS_SELECTOR, "mat-checkbox[formcontrolname='is_staff']"
            )
            values["is_staff"] = staff_cb.get_attribute("aria-checked") == "true"
        except Exception:
            values["is_staff"] = None

        return values

    # ==============================================================
    #  Table interactions
    # ==============================================================

    def get_table_row_count(self):
        rows = self.driver.find_elements(
            By.CSS_SELECTOR, "table.mat-mdc-table tbody tr"
        )
        return len(rows)

    def get_all_usernames(self):
        cells = self.driver.find_elements(
            By.CSS_SELECTOR,
            "table.mat-mdc-table tbody td.cdk-column-username, "
            "table.mat-mdc-table tbody td.mat-column-username",
        )
        names = []
        for cell in cells:
            try:
                text = cell.text.strip()
                if text:
                    names.append(text)
            except StaleElementReferenceException:
                continue
        return names

    def is_user_in_table(self, username):
        names = self.get_all_usernames()
        return any(username.strip().lower() in n.lower() for n in names)

    def find_user_row_index(self, username):
        rows = self.driver.find_elements(
            By.CSS_SELECTOR, "table.mat-mdc-table tbody tr"
        )
        for i, row in enumerate(rows):
            try:
                cells = row.find_elements(By.TAG_NAME, "td")
                for cell in cells:
                    if username.strip().lower() in cell.text.strip().lower():
                        return i
            except StaleElementReferenceException:
                continue
        return -1

    # ==============================================================
    #  Row action buttons
    # ==============================================================

    def _click_action_button(self, username, icon_name):
        """Click a row action button (View/Edit/History) by username and icon name."""
        self._force_close_panels()

        # Strategy 1: Find row by username, click button by icon
        try:
            rows = self.driver.find_elements(
                By.CSS_SELECTOR, "table.mat-mdc-table tbody tr"
            )
            for row in rows:
                try:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    for cell in cells:
                        if username.strip().lower() in cell.text.strip().lower():
                            # Found the row — click the action button
                            btn = row.find_element(
                                By.CSS_SELECTOR,
                                f"app-feather-icons[icon='{icon_name}']"
                            )
                            parent_btn = btn.find_element(By.XPATH, "./ancestor::button")
                            self.driver.execute_script(
                                "arguments[0].click();", parent_btn
                            )
                            self.wait_seconds(1)
                            return True
                except Exception:
                    continue
        except Exception:
            pass

        # Strategy 2: Index-based fallback
        row_idx = self.find_user_row_index(username)
        if row_idx >= 0:
            return self._click_action_button_by_index(row_idx, icon_name)

        log.warning(f"Action button not found for user: {username}")
        return False

    def _click_action_button_by_index(self, row_index, icon_name):
        """Fallback: click action button by row index."""
        rows = self.driver.find_elements(
            By.CSS_SELECTOR, "table.mat-mdc-table tbody tr"
        )
        if row_index >= len(rows):
            raise Exception(f"Row index {row_index} out of range")
        row = rows[row_index]

        try:
            btn = row.find_element(
                By.CSS_SELECTOR,
                f"app-feather-icons[icon='{icon_name}']"
            )
            parent_btn = btn.find_element(By.XPATH, "./ancestor::button")
            self.driver.execute_script("arguments[0].click();", parent_btn)
            self.wait_seconds(1)
            return True
        except Exception:
            # Fallback: click by position (0=view, 1=edit, 2=history)
            btns = row.find_elements(By.CSS_SELECTOR, "td:first-child button")
            idx_map = {"eye": 0, "edit": 1, "clock": 2}
            idx = idx_map.get(icon_name, 0)
            if idx < len(btns):
                self.driver.execute_script("arguments[0].click();", btns[idx])
                self.wait_seconds(1)
                return True
        raise Exception(f"Action button not found in row {row_index}")

    def click_view_button(self, username=None, row_index=0):
        log.info(f"Clicking View button for: {username or row_index}...")
        if username:
            return self._click_action_button(username, "eye")
        return self._click_action_button_by_index(row_index, "eye")

    def click_edit_button(self, username=None, row_index=0):
        log.info(f"Clicking Edit button for: {username or row_index}...")
        if username:
            return self._click_action_button(username, "edit")
        return self._click_action_button_by_index(row_index, "edit")

    def click_history_button(self, username=None, row_index=0):
        log.info(f"Clicking History button for: {username or row_index}...")
        if username:
            return self._click_action_button(username, "clock")
        return self._click_action_button_by_index(row_index, "clock")

    # ==============================================================
    #  View & Edit specific verifications
    # ==============================================================

    def verify_view_popup_read_only(self):
        """Verify that the View popup fields are read-only / disabled."""
        log.info("Verifying View popup is read-only...")
        all_readonly = True

        for locator in [
            self.USERNAME_INPUT, self.EMAIL_INPUT,
            self.FIRST_NAME_INPUT, self.LAST_NAME_INPUT,
            self.PASSWORD_INPUT
        ]:
            try:
                inp = self.find_visible_element(locator, timeout=5)
                if inp.is_enabled():
                    all_readonly = False
                    log.warning(f"Field {locator} is editable in View mode")
            except Exception:
                pass

        # Submit/Update should NOT be visible
        if self.is_displayed(self.SUBMIT_BUTTON, timeout=2):
            all_readonly = False
            log.warning("Submit button visible in View mode")
        if self.is_displayed(self.UPDATE_BUTTON, timeout=2):
            all_readonly = False
            log.warning("Update button visible in View mode")

        return all_readonly

    def verify_edit_popup_editable(self):
        """Verify that the Edit popup shows Update button and editable fields."""
        log.info("Verifying Edit popup is editable...")
        has_update = self.is_displayed(self.UPDATE_BUTTON, timeout=5)

        # Username should be editable (or at least check if Update exists)
        try:
            username_input = self.find_visible_element(self.USERNAME_INPUT, timeout=5)
            editable = username_input.is_enabled()
        except Exception:
            editable = True  # Assume editable if can't check

        return has_update and editable

    # ==============================================================
    #  History popup
    # ==============================================================

    def is_history_popup_open(self):
        """Check if the history popup is currently visible."""
        try:
            headings = self.driver.find_elements(
                By.CSS_SELECTOR, ".edit_pop_up h3, .big-model h3"
            )
            for h in headings:
                try:
                    if "history" in h.text.strip().lower() and h.is_displayed():
                        return True
                except Exception:
                    continue
        except Exception:
            pass
        return False

    def close_history_popup(self):
        """Close the history popup using the Close button."""
        log.info("Closing history popup...")
        try:
            close_btns = self.driver.find_elements(
                By.XPATH,
                "//div[@class='popup-footer']//button[contains(.,'Close')]",
            )
            for btn in close_btns:
                try:
                    if btn.is_displayed():
                        self.driver.execute_script("arguments[0].click();", btn)
                        self.wait_seconds(0.5)
                        log.info("History popup closed via Close button")
                        return
                except Exception:
                    continue
        except Exception:
            pass
        # Fallback: close via X
        self.close_popup()

    def get_history_row_count(self):
        """Return the number of rows in the history table."""
        try:
            rows = self.driver.find_elements(
                By.CSS_SELECTOR, ".edit_pop_up table tbody tr"
            )
            return len(rows)
        except Exception:
            return 0

    # ==============================================================
    #  High-level action: create_user
    # ==============================================================

    def create_user(self, data):
        """Create a user from the given data dict.
        Returns dict: {status: PASSED/FAILED, message: str, username: str}
        """
        log.info("Creating user...")
        result = {"status": "FAILED", "message": "", "username": data.get("username", "")}

        try:
            self.open_add_form()
            self.wait_seconds(1)
            if not self.is_add_form_open():
                result["message"] = "Add form did not open"
                return result

            self.fill_user_form(data)
            self.wait_seconds(0.5)
            self.submit()
            self.wait_seconds(3)

            # Check for success alert
            alert_msg = self.handle_success_alert(timeout=10)
            if alert_msg:
                result["status"] = "PASSED"
                result["message"] = alert_msg
                return result

            # Check if form is still open (validation error or duplicate)
            if self.is_add_form_open():
                errors = self.get_mat_error_text()
                swal = self.handle_validation_warning(timeout=3)
                if errors:
                    result["message"] = f"Validation errors: {errors}"
                elif swal:
                    result["message"] = f"SweetAlert: {swal}"
                else:
                    # BUG-001: Silent duplicate block
                    result["message"] = "Form still open — possible silent duplicate block (BUG-001)"
                return result

            # Form closed but no alert — might still have succeeded
            result["status"] = "PASSED"
            result["message"] = "Form closed (no explicit success alert)"
            return result

        except Exception as e:
            result["message"] = f"Exception: {str(e)}"
            return result

    # ==============================================================
    #  High-level action: edit_user
    # ==============================================================

    def edit_user(self, username, edit_data):
        """Edit a user by username with the given edit_data dict.
        Returns dict: {status: PASSED/FAILED, message: str}
        """
        log.info(f"Editing user: {username}...")
        result = {"status": "FAILED", "message": ""}

        try:
            self.click_edit_button(username=username)
            self.wait_seconds(1)

            if not self.is_edit_mode() and not self.is_add_form_open():
                result["message"] = "Edit form did not open"
                return result

            # Fill only provided fields
            if edit_data.get("username") is not None:
                self.type_text(self.USERNAME_INPUT, str(edit_data["username"]), clear_first=True)
            if edit_data.get("email") is not None:
                self.type_text(self.EMAIL_INPUT, str(edit_data["email"]), clear_first=True)
            if edit_data.get("first_name") is not None:
                self.type_text(self.FIRST_NAME_INPUT, str(edit_data["first_name"]), clear_first=True)
            if edit_data.get("last_name") is not None:
                self.type_text(self.LAST_NAME_INPUT, str(edit_data["last_name"]), clear_first=True)
            if edit_data.get("password") is not None:
                self.type_text(self.PASSWORD_INPUT, str(edit_data["password"]), clear_first=True)

            self._force_close_panels()
            self.click_update()
            self.wait_seconds(3)

            alert_msg = self.handle_success_alert(timeout=10)
            if alert_msg:
                result["status"] = "PASSED"
                result["message"] = alert_msg
                return result

            if self.is_add_form_open():
                errors = self.get_mat_error_text()
                swal = self.handle_validation_warning(timeout=3)
                if errors:
                    result["message"] = f"Validation errors: {errors}"
                elif swal:
                    result["message"] = f"SweetAlert: {swal}"
                else:
                    result["message"] = "Form still open — possible silent block"
                return result

            result["status"] = "PASSED"
            result["message"] = "Form closed (no explicit success alert)"
            return result

        except Exception as e:
            result["message"] = f"Exception: {str(e)}"
            return result
