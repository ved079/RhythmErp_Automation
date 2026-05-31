"""
item_group_page.py
------------------
Page Object Model for RhythmERP Item Group screen.

Location: Commodity Settings > Commodity Master > Item Group
URL:      /#/dynamic-screens/Item%20Group

FORM LAYOUT (Simple popup — NOT a stepper):

  - Code            (text input,   required, name="Code")
  - Description     (text input,   required, name="Description")
  [Cancel] [Submit]

TABLE COLUMNS (main listing):
  - View / Edit / History   (action buttons per row)
  - Code / Description

KNOWN BEHAVIORS (confirmed via ERP exploration):
  BEH-001 : No dropdowns — both fields are text inputs (type="character")
  BEH-002 : No Status toggle on this screen
  BEH-003 : No Delete button — only View, Edit, History
  BEH-004 : Duplicate Codes ALLOWED — no uniqueness constraint
  BEH-005 : Both Code and Description are required
  BEH-006 : History button present and functional
  BEH-007 : Fields use name="Code" / name="Description" (NO formcontrolname)

POPUP TYPES:
  Type A — "Validation Failed - Please correct the highlighted fields"
            Appears when required fields are empty (client-side).
            Has .swal2-confirm button.
  Type B — "Failed to save record"
            Appears when server-side validation rejects data.
            MUST use JS dismiss to avoid StaleElementReferenceException.

KEY RULES:
  - NEVER use Keys.ESCAPE (closes entire popup form!)
  - JS clicks for Angular Material overlays
  - ALL SweetAlert2 dismissals MUST use JS querySelector click
  - No toggle switches on this screen
  - No dropdown selections needed
  - Edit mode: all fields editable, button says "Update"
  - View mode: all fields disabled, only Cancel button
  - History column uses cdk-column-archive (NOT cdk-column-history)
  - History popup uses div.popup-overlay container (NOT mat-dialog-container)
"""

import os
import sys
import time

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
sys.path.insert(0, PROJECT_ROOT)

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    ElementClickInterceptedException,
    NoSuchElementException,
    InvalidSessionIdException,
    WebDriverException,
)
from common.base_page import BasePage
from common.logger import log
from config import RHYTHMERP_BASE_URL, EXPLICIT_WAIT

# Global list to track every submission for reporting
IG_SUBMISSIONS = []


class ItemGroupPage(BasePage):
    """Page Object for Item Group screen."""

    PAGE_URL = f"{RHYTHMERP_BASE_URL}/#/dynamic-screens/Item%20Group"

    # ==============================================================
    #  LOCATORS - Toolbar
    # ==============================================================
    ADD_BUTTON = ("css", "button.erp-add-btn")
    SEARCH_TOGGLE = ("css", "button.search-btn, button[aria-label='Search']")
    REFRESH_BUTTON = ("css", "button[mattooltip='Refresh']")
    FILTER_BUTTON = ("css", "div[mattooltip='Filters'] button")

    # ==============================================================
    #  LOCATORS - Search bar
    # ==============================================================
    SEARCH_INPUT = ("css", "input#erpSearchInput, .erp-search-wrapper input")

    # ==============================================================
    #  LOCATORS - Table (main listing)
    # ==============================================================
    TABLE = ("css", "table#excel-table")
    TABLE_ROWS = ("css", "table#excel-table tbody tr")

    TABLE_CODE_CELLS = (
        "css",
        "table#excel-table tbody td.cdk-column-code, "
        "table#excel-table tbody td.mat-column-code",
    )
    TABLE_DESCRIPTION_CELLS = (
        "css",
        "table#excel-table tbody td.cdk-column-description, "
        "table#excel-table tbody td.mat-column-description",
    )
    NO_DATA_ROW = (
        "css",
        "table#excel-table tbody tr td.no-data, "
        "table#excel-table tbody tr.mat-mdc-no-data-row",
    )

    # ==============================================================
    #  LOCATORS - Popup form
    # ==============================================================
    FORM_POPUP = (
        "css",
        ".edit_pop_up.override_edit_pop_up.popup-mode, "
        ".big-model, mat-dialog-container",
    )

    # Text inputs — using name attribute (matching ERP dynamic-screens pattern)
    CODE_INPUT = (
        "css",
        "input[name='Code']",
    )
    DESCRIPTION_INPUT = (
        "css",
        "input[name='Description']",
    )

    # Fallback locators using formcontrolname (just in case)
    CODE_INPUT_ALT = (
        "css",
        "input[formcontrolname='code'], "
        "input[formcontrolname='Code']",
    )
    DESCRIPTION_INPUT_ALT = (
        "css",
        "input[formcontrolname='description'], "
        "input[formcontrolname='Description']",
    )

    # Popup buttons
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
    #  LOCATORS - Row action buttons
    # ==============================================================
    VIEW_BUTTON_BY_NAME = (
        "xpath",
        "//td[contains(text(),'{item_name}')]"
        "/ancestor::tr//td[contains(@class,'cdk-column-view')]"
        "//button",
    )
    EDIT_BUTTON_BY_NAME = (
        "xpath",
        "//td[contains(text(),'{item_name}')]"
        "/ancestor::tr//td[contains(@class,'cdk-column-edit')]"
        "//button",
    )
    HISTORY_BUTTON_BY_NAME = (
        "xpath",
        "//td[contains(text(),'{item_name}')]"
        "/ancestor::tr//td[contains(@class,'cdk-column-archive')]"
        "//button",
    )

    # ==============================================================
    #  LOCATORS - History popup
    # ==============================================================
    HISTORY_POPUP = (
        "xpath",
        "//div[contains(@class,'popup-overlay') or contains(@class,'big-model')]"
        "[.//h3[contains(translate(.,'HISTORY','history'),'history')]]",
    )
    HISTORY_TABLE_ROWS = (
        "css",
        ".popup-body table tbody tr, .big-model table tbody tr",
    )
    HISTORY_CLOSE_BUTTON = (
        "xpath",
        "//div[@class='popup-footer']//button[contains(.,'Cancel') or contains(.,'Close')]",
    )

    # ==============================================================
    #  LOCATORS - SweetAlert2
    # ==============================================================
    SWAL_TITLE = ("css", "#swal2-title")
    SWAL_HTML = ("css", ".swal2-html-container")
    SWAL_CONFIRM = ("css", ".swal2-confirm")
    SWAL_CANCEL = ("css", ".swal2-cancel")

    # ==============================================================
    #  LOCATORS - Validation errors
    # ==============================================================
    MAT_ERROR = ("css", "mat-error, .mat-mdc-form-field-error")
    FIELD_ERROR = (
        "xpath",
        "//mat-label[contains(.,'{field_label}')]"
        "/ancestor::mat-form-field//mat-error",
    )

    # ==============================================================
    #  Navigation & page load
    # ==============================================================

    def navigate_to_page(self):
        """Navigate to the Item Group listing page.
        Force-refreshes to clear leftover Angular state.
        """
        log.info("Navigating to Item Group page...")
        self.navigate_to(self.PAGE_URL)
        self.driver.refresh()
        self._wait_for_page_ready()

    def _wait_for_page_ready(self):
        """Wait until the page is fully loaded."""
        try:
            WebDriverWait(self.driver, EXPLICIT_WAIT).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, "table#excel-table")
                )
            )
            log.info("Item Group table loaded")
        except TimeoutException:
            log.warning("Item Group table not found, page may be empty")

        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "ul.tbl-export-btn")
                )
            )
            self.wait_seconds(1)
            log.info("Item Group toolbar ready")
        except TimeoutException:
            log.warning("Toolbar not found, ADD button may be delayed")
            self.wait_seconds(3)

    def is_page_loaded(self):
        """Check if the listing page has loaded."""
        return self.is_displayed(self.TABLE, timeout=10)

    # ==============================================================
    #  Overlay cleanup — NEVER use Keys.ESCAPE
    # ==============================================================

    def _force_close_panels(self):
        """Remove ALL select overlay panes from the DOM via JS."""
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

    def force_close_form_popup(self):
        """Force close any form popup via JS."""
        self.driver.execute_script("""
            document.querySelectorAll('.swal2-container').forEach(function(el) {
                el.remove();
            });
        """)
        self._force_close_panels()

    # ==============================================================
    #  Toolbar actions
    # ==============================================================

    def open_add_form(self):
        """Click the ADD button to open the create popup form."""
        log.info("Clicking ADD button on Item Group...")
        self._wait_for_toolbar()

        # Strategy 1: button.erp-add-btn (confirmed HTML class)
        try:
            btn = self.driver.find_element(
                By.CSS_SELECTOR, "button.erp-add-btn"
            )
            if btn.is_displayed():
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});"
                    "arguments[0].click();",
                    btn,
                )
                self.wait_seconds(1.5)
                if self._is_form_popup_open():
                    log.info("ADD form opened on Item Group")
                    return
        except Exception:
            pass

        # Strategy 2: button containing text "Add Item Group"
        try:
            btns = self.driver.find_elements(
                By.CSS_SELECTOR, "button"
            )
            for btn in btns:
                try:
                    btn_text = btn.text.strip().lower()
                    if ("add" in btn_text and "item" in btn_text 
                            and btn.is_displayed()):
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({block:'center'});"
                            "arguments[0].click();",
                            btn,
                        )
                        self.wait_seconds(1.5)
                        if self._is_form_popup_open():
                            log.info("ADD form opened via text match on Item Group")
                            return
                except Exception:
                    continue
        except Exception:
            pass

        # Strategy 3: mini-fab button with 'add' icon
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
                            log.info("ADD form opened via mini-fab on Item Group")
                            return
                except Exception:
                    continue
        except Exception:
            pass

        # Strategy 4: button.erp-add-btn (legacy fallback)
        try:
            btn = self.driver.find_element(
                By.CSS_SELECTOR, "button.erp-add-btn"
            )
            if btn.is_displayed():
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});"
                    "arguments[0].click();",
                    btn,
                )
                self.wait_seconds(1.5)
                if self._is_form_popup_open():
                    log.info("ADD form opened via mattooltip on Item Group")
                    return
        except Exception:
            pass

        # Strategy 5: click_with_retry
        try:
            self.click_with_retry(self.ADD_BUTTON)
            self.wait_seconds(1.5)
            if self._is_form_popup_open():
                log.info("ADD form opened via click_with_retry on Item Group")
                return
        except Exception:
            pass

        raise Exception("ADD button not found or not clickable on Item Group")

    def _wait_for_toolbar(self):
        """Wait for the toolbar and ADD button to be ready."""
        for attempt in range(3):
            # Check button.erp-add-btn (confirmed class)
            try:
                btn = self.driver.find_element(
                    By.CSS_SELECTOR, "button.erp-add-btn"
                )
                if btn.is_displayed():
                    return
            except Exception:
                pass

            # Check button with text containing "Add Item Group"
            try:
                btns = self.driver.find_elements(By.CSS_SELECTOR, "button")
                for btn in btns:
                    try:
                        btn_text = btn.text.strip().lower()
                        if ("add" in btn_text and "item" in btn_text 
                                and btn.is_displayed()):
                            return
                    except Exception:
                        continue
            except Exception:
                pass

            # Check mini-fab with add icon
            try:
                mini_fabs = self.driver.find_elements(
                    By.CSS_SELECTOR, "button.mat-mdc-mini-fab"
                )
                for btn in mini_fabs:
                    try:
                        icon = btn.find_element(By.CSS_SELECTOR, "mat-icon")
                        if icon.text.strip().lower() == "add":
                            return
                    except Exception:
                        continue
            except Exception:
                pass

            # Check legacy mattooltip
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

    def _is_form_popup_open(self):
        """Quick check if any form popup is visible."""
        try:
            popups = self.driver.find_elements(
                By.CSS_SELECTOR,
                "div.big-model, mat-dialog-container, "
                "div.edit_pop_up.override_edit_pop_up.popup-mode",
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

    def is_add_form_open(self):
        """Check if the Add form is open by looking for Code input."""
        # Try primary locator, then fallback
        if self.is_displayed(self.CODE_INPUT, timeout=5):
            return True
        return self.is_displayed(self.CODE_INPUT_ALT, timeout=3)

    def is_form_closed(self):
        """Check if the form popup is closed."""
        return not self._is_form_popup_open()

    def click_refresh(self):
        """Click the Refresh button."""
        log.info("Clicking Refresh button...")
        try:
            refresh_btns = self.driver.find_elements(
                By.CSS_SELECTOR, "button.mat-mdc-mini-fab"
            )
            for btn in refresh_btns:
                try:
                    icon = btn.find_element(By.CSS_SELECTOR, "mat-icon")
                    if icon.text.strip().lower() == "refresh" and btn.is_displayed():
                        self.driver.execute_script("arguments[0].click();", btn)
                        self.wait_seconds(2)
                        log.info("Refresh clicked")
                        return
                except Exception:
                    continue
        except Exception:
            pass
        log.warning("Refresh button not found")

    # ==============================================================
    #  Fill form fields
    # ==============================================================

    def fill_form(self, data):
        """Fill all fields on the Item Group popup form.

        Fill order: Code -> Description

        data dict keys:
          - code          (str, required)
          - description   (str, required)
        """
        log.info("Filling Item Group form...")

        # 1. Code (required)
        if data.get("code") is not None:
            self._type_in_input(
                self.CODE_INPUT,
                self.CODE_INPUT_ALT,
                str(data["code"]),
            )

        # 2. Description (required)
        if data.get("description") is not None:
            self._type_in_input(
                self.DESCRIPTION_INPUT,
                self.DESCRIPTION_INPUT_ALT,
                str(data["description"]),
            )

        self._force_close_panels()
        log.info("Item Group form filled")

    def _type_in_input(self, primary_locator, fallback_locator, text):
        """Type text into a text input, trying primary then fallback locator."""
        # Try primary
        try:
            el = self.find_visible_element(primary_locator, timeout=5)
            if el:
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});", el
                )
                self.driver.execute_script(
                    "var s = Object.getOwnPropertyDescriptor("
                    "window.HTMLInputElement.prototype,'value').set;"
                    "s.call(arguments[0], '');"
                    "arguments[0].dispatchEvent(new Event('input',{bubbles:true}));",
                    el,
                )
                el.send_keys(text)
                log.info(f"Typed '{text}' via primary locator")
                return
        except Exception:
            pass

        # Try fallback
        try:
            el = self.find_visible_element(fallback_locator, timeout=5)
            if el:
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});", el
                )
                self.driver.execute_script(
                    "var s = Object.getOwnPropertyDescriptor("
                    "window.HTMLInputElement.prototype,'value').set;"
                    "s.call(arguments[0], '');"
                    "arguments[0].dispatchEvent(new Event('input',{bubbles:true}));",
                    el,
                )
                el.send_keys(text)
                log.info(f"Typed '{text}' via fallback locator")
                return
        except Exception:
            pass

        # Last resort: find any visible text input in the popup
        try:
            inputs = self.driver.find_elements(
                By.CSS_SELECTOR,
                ".big-model input[type='text'], "
                ".edit_pop_up input[type='text'], "
                "mat-dialog-container input[type='text'], "
                ".big-model input[type='character'], "
                ".edit_pop_up input[type='character']",
            )
            for inp in inputs:
                try:
                    if inp.is_displayed() and inp.is_enabled():
                        inp.clear()
                        inp.send_keys(text)
                        log.info(f"Typed '{text}' via generic text input")
                        return
                except Exception:
                    continue
        except Exception:
            pass

        log.warning(f"Could not type '{text}' — no suitable input found")

    # ==============================================================
    #  Read form field values
    # ==============================================================

    def get_code_value(self):
        """Read the current value of the Code input."""
        return self._read_input_value(self.CODE_INPUT, self.CODE_INPUT_ALT)

    def get_description_value(self):
        """Read the current value of the Description input."""
        return self._read_input_value(
            self.DESCRIPTION_INPUT, self.DESCRIPTION_INPUT_ALT
        )

    def _read_input_value(self, primary_locator, fallback_locator):
        """Read the value of an input field, trying primary then fallback."""
        for locator in [primary_locator, fallback_locator]:
            try:
                el = self.find_visible_element(locator, timeout=3)
                if el:
                    val = el.get_attribute("value") or ""
                    if val is not None:
                        return val.strip()
            except Exception:
                continue
        return ""

    def get_form_values(self):
        """Read all form field values as a dict."""
        return {
            "code": self.get_code_value(),
            "description": self.get_description_value(),
        }

    def is_input_disabled(self, primary_locator, fallback_locator):
        """Check if an input field is disabled (read-only)."""
        for locator in [primary_locator, fallback_locator]:
            try:
                el = self.find_visible_element(locator, timeout=3)
                if el:
                    return not el.is_enabled()
            except Exception:
                continue
        return False

    # ==============================================================
    #  Submit / Update / Cancel
    # ==============================================================

    def submit(self):
        """Click the Submit button (Create mode)."""
        log.info("Submitting Item Group form...")
        self._force_close_panels()
        try:
            btn = self.find_visible_element(self.SUBMIT_BUTTON, timeout=5)
            if btn:
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});"
                    "arguments[0].click();",
                    btn,
                )
                log.info("Submit clicked")
                return
        except Exception:
            pass

        # Fallback: find any Submit button in popup
        try:
            btns = self.driver.find_elements(By.CSS_SELECTOR, ".popup-footer button")
            for b in btns:
                if b.text.strip() == "Submit" and b.is_displayed():
                    self.driver.execute_script("arguments[0].click();", b)
                    log.info("Submit clicked via fallback")
                    return
        except Exception:
            pass

        log.warning("Submit button not found")

    def click_update(self):
        """Click the Update button (Edit mode)."""
        log.info("Clicking Update button...")
        self._force_close_panels()
        try:
            btn = self.find_visible_element(self.UPDATE_BUTTON, timeout=5)
            if btn:
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});"
                    "arguments[0].click();",
                    btn,
                )
                log.info("Update clicked")
                return
        except Exception:
            pass

        # Fallback
        try:
            btns = self.driver.find_elements(By.CSS_SELECTOR, ".popup-footer button")
            for b in btns:
                if b.text.strip() == "Update" and b.is_displayed():
                    self.driver.execute_script("arguments[0].click();", b)
                    log.info("Update clicked via fallback")
                    return
        except Exception:
            pass

        log.warning("Update button not found")

    def cancel(self):
        """Click the Cancel button."""
        log.info("Clicking Cancel button...")
        try:
            btn = self.find_visible_element(self.CANCEL_BUTTON, timeout=5)
            if btn:
                self.driver.execute_script("arguments[0].click();", btn)
                self.wait_seconds(0.5)
                return
        except Exception:
            pass

        # Fallback
        try:
            btns = self.driver.find_elements(By.CSS_SELECTOR, ".popup-footer button")
            for b in btns:
                if b.text.strip() == "Cancel" and b.is_displayed():
                    self.driver.execute_script("arguments[0].click();", b)
                    self.wait_seconds(0.5)
                    return
        except Exception:
            pass
        log.warning("Cancel button not found")

    # ==============================================================
    #  SweetAlert2 handlers — JS-only dismissals
    # ==============================================================

    def handle_success_alert(self, timeout=15):
        """Handle success SweetAlert2 popup.
        Returns the alert title text, or '' if no alert appeared.
        """
        log.info("Handling success alert...")
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, "#swal2-title")
                )
            )
            title = self.get_swal_title()
            log.info(f"Success alert: {title}")

            self._dismiss_swal_confirm()
            self._cleanup_swal_containers()

            return title or ""
        except TimeoutException:
            log.info("No success alert appeared")
            return ""

    def handle_validation_warning(self, timeout=10):
        """Handle 'Validation Failed' SweetAlert2 popup (Type A).
        Appears when required fields are empty (client-side).
        Returns the alert title text, or '' if no alert appeared.
        """
        log.info("Handling validation warning...")
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, "#swal2-title")
                )
            )
            title = self.get_swal_title()
            log.info(f"Validation warning: {title}")

            self._dismiss_swal_confirm()
            self._cleanup_swal_containers()

            return title or ""
        except TimeoutException:
            log.info("No validation warning appeared")
            return ""

    def handle_save_failure_alert(self, timeout=10):
        """Handle 'Failed to save record' SweetAlert2 popup (Type B).
        This popup appears when server-side validation rejects the data.
        Uses JS click to avoid StaleElementReferenceException.
        Returns the alert title text, or '' if no alert appeared.
        """
        log.info("Handling save failure alert...")
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, "#swal2-title")
                )
            )
            title = self.get_swal_title()
            log.info(f"Save failure alert: {title}")

            # Read the HTML message if available
            try:
                html_el = self.driver.find_element(
                    By.CSS_SELECTOR, ".swal2-html-container"
                )
                html_msg = html_el.text.strip()
                if html_msg:
                    log.info(f"Save failure detail: {html_msg}")
            except Exception:
                pass

            self._dismiss_swal_confirm()
            self._cleanup_swal_containers()

            return title or ""
        except TimeoutException:
            log.info("No save failure alert appeared")
            return ""

    # ==============================================================
    #  SweetAlert2 — internal helpers (JS-only, no Selenium .click())
    # ==============================================================

    def _dismiss_swal_confirm(self):
        """Dismiss a SweetAlert2 popup via JS querySelector."""
        self.wait_seconds(0.5)
        self.driver.execute_script(
            "document.querySelector('.swal2-confirm')?.click();"
        )
        self.wait_seconds(0.3)

        # Fallback: click ALL swal2-confirm buttons
        try:
            remaining = self.driver.find_elements(
                By.CSS_SELECTOR, ".swal2-confirm"
            )
            if remaining:
                self.driver.execute_script("""
                    document.querySelectorAll('.swal2-confirm').forEach(
                        function(b) { b.click(); }
                    );
                """)
                self.wait_seconds(0.3)
        except Exception:
            pass

    def _cleanup_swal_containers(self):
        """Remove all leftover .swal2-container elements from the DOM."""
        try:
            WebDriverWait(self.driver, 3).until(
                EC.invisibility_of_element_located(
                    (By.CSS_SELECTOR, ".swal2-container")
                )
            )
        except Exception:
            pass

        self.driver.execute_script("""
            document.querySelectorAll('.swal2-container')
            .forEach(function(el) { el.remove(); });
        """)
        self.wait_seconds(0.2)

    def get_swal_title(self):
        """Read the SweetAlert2 title text."""
        try:
            el = self.driver.find_element(By.CSS_SELECTOR, "#swal2-title")
            return el.text.strip()
        except Exception:
            return ""

    def is_validation_alert_present(self, timeout=5):
        """Check if SweetAlert2 is visible."""
        return self.is_displayed(self.SWAL_TITLE, timeout=timeout)

    # ==============================================================
    #  Validation error helpers
    # ==============================================================

    def has_field_error(self, field_label):
        """Check if a specific field has a validation error."""
        try:
            locator = (
                "xpath",
                f"//mat-label[contains(.,'{field_label}')]"
                "/ancestor::mat-form-field//mat-error",
            )
            return self.is_displayed(locator, timeout=3)
        except Exception:
            return False

    def get_mat_error_text(self):
        """Get all mat-error text messages on the form."""
        errors = []
        try:
            error_els = self.driver.find_elements(
                By.CSS_SELECTOR, "mat-error, .mat-mdc-form-field-error"
            )
            for el in error_els:
                try:
                    text = el.text.strip()
                    if text and el.is_displayed():
                        errors.append(text)
                except Exception:
                    continue
        except Exception:
            pass
        return errors

    # ==============================================================
    #  Row action buttons
    # ==============================================================

    def click_view_button(self, item_name=None, row_index=0):
        """Click the View button on a table row."""
        log.info(f"Clicking View button (name={item_name}, row={row_index})...")
        if item_name:
            try:
                locator = (
                    "xpath",
                    f"//td[contains(text(),'{item_name}')]"
                    "/ancestor::tr//td[contains(@class,'cdk-column-view')]"
                    "//button",
                )
                btn = self.find_visible_element(locator, timeout=5)
                if btn:
                    self.driver.execute_script("arguments[0].click();", btn)
                    self.wait_seconds(1)
                    return True
            except Exception:
                pass

        return self._click_action_button_by_index(row_index, 0)

    def click_edit_button(self, item_name=None, row_index=0):
        """Click the Edit button on a table row."""
        log.info(f"Clicking Edit button (name={item_name}, row={row_index})...")
        if item_name:
            try:
                locator = (
                    "xpath",
                    f"//td[contains(text(),'{item_name}')]"
                    "/ancestor::tr//td[contains(@class,'cdk-column-edit')]"
                    "//button",
                )
                btn = self.find_visible_element(locator, timeout=5)
                if btn:
                    self.driver.execute_script("arguments[0].click();", btn)
                    self.wait_seconds(1)
                    return True
            except Exception:
                pass

        return self._click_action_button_by_index(row_index, 1)

    def click_history_button(self, item_name=None, row_index=0):
        """Click the History button on a table row.
        Note: Uses cdk-column-archive (NOT cdk-column-history).
        """
        log.info(f"Clicking History button (name={item_name}, row={row_index})...")
        if item_name:
            try:
                locator = (
                    "xpath",
                    f"//td[contains(text(),'{item_name}')]"
                    "/ancestor::tr//td[contains(@class,'cdk-column-archive')]"
                    "//button",
                )
                btn = self.find_visible_element(locator, timeout=5)
                if btn:
                    self.driver.execute_script("arguments[0].click();", btn)
                    self.wait_seconds(1)
                    return True
            except Exception:
                pass

        return self._click_action_button_by_index(row_index, 2)

    def _click_action_button_by_index(self, row_index, btn_index):
        """Click an action button by row and button index."""
        try:
            rows = self.driver.find_elements(
                By.CSS_SELECTOR, "table#excel-table tbody tr"
            )
            if row_index < len(rows):
                btns = rows[row_index].find_elements(By.CSS_SELECTOR, "button")
                if btn_index < len(btns):
                    self.driver.execute_script(
                        "arguments[0].click();", btns[btn_index]
                    )
                    self.wait_seconds(1)
                    return True
        except (InvalidSessionIdException, WebDriverException):
            log.error("Browser session lost during action button click")
            raise
        except Exception as e:
            log.warning(f"Failed to click action button: {e}")
        return False

    # ==============================================================
    #  Mode detection
    # ==============================================================

    def is_edit_mode(self):
        """Check if the form is in Edit mode (has Update button)."""
        try:
            return self.is_displayed(self.UPDATE_BUTTON, timeout=5)
        except (InvalidSessionIdException, WebDriverException):
            raise
        except Exception:
            return False

    def is_view_mode(self):
        """Check if the form is in View mode (all fields disabled, no Submit/Update)."""
        try:
            has_submit = self.is_displayed(self.SUBMIT_BUTTON, timeout=2)
            has_update = self.is_displayed(self.UPDATE_BUTTON, timeout=2)
            if has_submit or has_update:
                return False

            # Check if Code input is disabled
            try:
                inp = self.driver.find_element(
                    By.CSS_SELECTOR, "input[name='Code']"
                )
                if not inp.is_enabled():
                    return True
            except Exception:
                pass

            # Try fallback locator
            try:
                inp = self.driver.find_element(
                    By.CSS_SELECTOR,
                    "input[formcontrolname='code'], "
                    "input[formcontrolname='Code']"
                )
                if not inp.is_enabled():
                    return True
            except Exception:
                pass
        except (InvalidSessionIdException, WebDriverException):
            log.error("Browser session lost during view mode check")
            raise
        except Exception:
            pass
        return False

    # ==============================================================
    #  History popup
    # ==============================================================

    def is_history_popup_open(self):
        """Check if the History popup is visible.
        Uses div.popup-overlay + h3 containing 'history' text,
        with fallback to div.big-model.
        """
        try:
            popups = self.driver.find_elements(
                By.CSS_SELECTOR,
                "div.popup-overlay, div.big-model, div.edit_pop_up"
            )
            for p in popups:
                try:
                    h3s = p.find_elements(By.CSS_SELECTOR, "h3")
                    for h in h3s:
                        if "history" in h.text.lower() and p.is_displayed():
                            return True
                except Exception:
                    continue
        except (InvalidSessionIdException, WebDriverException):
            log.error("Browser session lost during history popup check")
            raise
        except Exception:
            pass
        return False

    def close_history_popup(self):
        """Close the History popup."""
        log.info("Closing History popup...")
        try:
            close_btn = self.find_visible_element(self.HISTORY_CLOSE_BUTTON, timeout=5)
            if close_btn:
                self.driver.execute_script("arguments[0].click();", close_btn)
                self.wait_seconds(0.5)
                return
        except Exception:
            pass

        # Fallback: find any Cancel/Close in visible popup
        try:
            btns = self.driver.find_elements(
                By.XPATH,
                "//div[contains(@class,'popup-overlay') or contains(@class,'big-model')]"
                "//button[contains(.,'Cancel') or contains(.,'Close')]"
            )
            for btn in btns:
                try:
                    if btn.is_displayed():
                        self.driver.execute_script("arguments[0].click();", btn)
                        self.wait_seconds(0.5)
                        return
                except Exception:
                    continue
        except Exception:
            pass

        log.warning("Could not close History popup")

    def get_history_row_count(self):
        """Count rows in the History popup table."""
        # Strategy 1: Look inside popup-overlay (confirmed container)
        try:
            rows = self.driver.find_elements(
                By.CSS_SELECTOR,
                "div.popup-overlay table tbody tr, "
                "div.popup-overlay .popup-body table tbody tr"
            )
            if rows:
                return len(rows)
        except Exception:
            pass

        # Strategy 2: Original selectors
        try:
            rows = self.driver.find_elements(
                By.CSS_SELECTOR,
                ".popup-body table tbody tr, .big-model table tbody tr"
            )
            if rows:
                return len(rows)
        except Exception:
            pass

        # Strategy 3: Any table rows inside any visible popup
        try:
            popups = self.driver.find_elements(
                By.CSS_SELECTOR,
                "div.popup-overlay, div.big-model, div.edit_pop_up"
            )
            for popup in popups:
                try:
                    if popup.is_displayed():
                        rows = popup.find_elements(
                            By.CSS_SELECTOR, "table tbody tr"
                        )
                        visible_rows = [
                            r for r in rows
                            if r.is_displayed() and r.text.strip()
                        ]
                        if visible_rows:
                            return len(visible_rows)
                except Exception:
                    continue
        except Exception:
            pass

        # Strategy 4: Generic — any table rows on the page inside an overlay
        try:
            rows = self.driver.find_elements(
                By.CSS_SELECTOR, "table tbody tr"
            )
            visible = [r for r in rows if r.is_displayed() and r.text.strip()]
            if visible:
                return len(visible)
        except Exception:
            pass

        return 0


    # ==============================================================
    #  Table data helpers
    # ==============================================================

    def get_table_row_count(self):
        """Count visible data rows in the table."""
        try:
            rows = self.driver.find_elements(
                By.CSS_SELECTOR, "table#excel-table tbody tr"
            )
            return len(rows)
        except Exception:
            return 0

    def get_all_codes(self):
        """List all Code values in the table."""
        names = []
        for css_selector in [
            "table#excel-table tbody td.cdk-column-code",
            "table#excel-table tbody td.mat-column-code",
        ]:
            try:
                cells = self.driver.find_elements(By.CSS_SELECTOR, css_selector)
                for cell in cells:
                    try:
                        text = cell.text.strip()
                        if text:
                            names.append(text)
                    except Exception:
                        continue
                if names:
                    return names
            except Exception:
                continue

        # Fallback: get first data cell from each row
        try:
            rows = self.driver.find_elements(
                By.CSS_SELECTOR, "table#excel-table tbody tr"
            )
            for row in rows:
                try:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    data_cells = [c for c in cells if c.text.strip()]
                    # Skip action button columns — code is the first data column
                    for cell in data_cells:
                        text = cell.text.strip()
                        if text:
                            names.append(text)
                            break
                except Exception:
                    continue
        except Exception:
            pass
        return names

    def is_item_group_in_table(self, code):
        """Check if an Item Group with the given code appears in the table."""
        codes = self.get_all_codes()
        return any(code.strip().lower() in c.lower() for c in codes)

    def find_row_index_by_code(self, code):
        """Find the 0-based row index for an Item Group by code.
        Returns -1 if not found.
        """
        rows = self.driver.find_elements(
            By.CSS_SELECTOR, "table#excel-table tbody tr"
        )
        for i, row in enumerate(rows):
            try:
                cells = row.find_elements(By.TAG_NAME, "td")
                for cell in cells:
                    if code.strip().lower() in cell.text.strip().lower():
                        return i
            except Exception:
                continue
        return -1

    # ==============================================================
    #  Search
    # ==============================================================

    def search_item_group(self, search_text):
        """Search for an Item Group by text in the search bar.
        Returns True if a matching result appears in the table.
        """
        log.info(f"Searching for: {search_text}")
        try:
            # Click search toggle to open search bar
            try:
                search_btns = self.driver.find_elements(
                    By.CSS_SELECTOR, "button.search-btn"
                )
                for btn in search_btns:
                    try:
                        if btn.is_displayed():
                            self.driver.execute_script("arguments[0].click();", btn)
                            self.wait_seconds(1)
                            break
                    except Exception:
                        continue
            except Exception:
                pass

            # Type in search input
            try:
                search_input = self.driver.find_element(
                    By.CSS_SELECTOR,
                    "input#erpSearchInput, .erp-search-wrapper input",
                )
                # Clear using JS native setter
                self.driver.execute_script(
                    "var s = Object.getOwnPropertyDescriptor("
                    "window.HTMLInputElement.prototype,'value').set;"
                    "s.call(arguments[0], '');"
                    "arguments[0].dispatchEvent(new Event('input',{bubbles:true}));",
                    search_input,
                )
                search_input.send_keys(search_text)
                search_input.send_keys(Keys.ENTER)
                self.wait_seconds(2)
            except Exception:
                log.warning("Search input not found")
                return False

            # Check if the search text appears in the table
            return self.is_item_group_in_table(search_text)

        except Exception:
            log.warning("Search failed")
            return False

    def clear_search(self):
        """Clear the search bar and refresh the table."""
        log.info("Clearing search...")
        try:
            search_input = self.driver.find_element(
                By.CSS_SELECTOR,
                "input#erpSearchInput, .erp-search-wrapper input",
            )
            self.driver.execute_script(
                "var s = Object.getOwnPropertyDescriptor("
                "window.HTMLInputElement.prototype,'value').set;"
                "s.call(arguments[0], '');"
                "arguments[0].dispatchEvent(new Event('input',{bubbles:true}));",
                search_input,
            )
            search_input.send_keys(Keys.ENTER)
            self.wait_seconds(1)
        except Exception:
            pass
        self.click_refresh()
        self.wait_seconds(2)

    # ==============================================================
    #  Filter panel
    # ==============================================================

    def open_filter_panel(self):
        """Open the filter panel."""
        log.info("Opening filter panel...")
        try:
            self.click_with_retry(self.FILTER_BUTTON)
            self.wait_seconds(1)
        except Exception:
            log.warning("Filter button not found")

    def is_filter_panel_open(self):
        """Check if the filter panel is visible."""
        try:
            panels = self.driver.find_elements(
                By.CSS_SELECTOR,
                ".filter-panel, .cdk-overlay-pane filter-panel, "
                "div.cdk-overlay-pane [role='listbox']",
            )
            for p in panels:
                try:
                    if p.is_displayed():
                        return True
                except Exception:
                    continue
        except Exception:
            pass
        return False

    def close_filter_panel(self):
        """Close the filter panel."""
        log.info("Closing filter panel...")
        self._force_close_panels()
        self.wait_seconds(0.5)

    # ==============================================================
    #  High-level convenience methods
    # ==============================================================

    def create_item_group(self, data):
        """Create an Item Group using the provided data dict.
        Returns the code used for the new Item Group.

        data dict keys:
          - code          (str, required)
          - description   (str, required)
        """
        log.info(f"Creating Item Group: code={data.get('code', '')}")
        code = data.get("code", "")

        self.open_add_form()
        self.wait_seconds(1)

        if not self.is_add_form_open():
            raise Exception("Add form did not open for Item Group creation")

        self.fill_form(data)
        self.submit()
        self.wait_seconds(2)

        # Handle SweetAlert2 (success or validation)
        if self.is_validation_alert_present(timeout=5):
            title = self.get_swal_title()
            if "Validation Failed" in title or "Failed" in title:
                log.warning(f"Validation during create: {title}")
                self._dismiss_swal_confirm()
                self._cleanup_swal_containers()
            else:
                self._dismiss_swal_confirm()
                self._cleanup_swal_containers()
        else:
            # Check for success alert
            self.handle_success_alert(timeout=5)

        IG_SUBMISSIONS.append({
            "action": "create",
            "code": code,
            "data": data,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        })

        return code

    def edit_item_group(self, existing_code, new_data):
        """Edit an existing Item Group.
        Returns the new code from new_data.

        Args:
            existing_code: code of the Item Group row to edit
            new_data: dict with code and/or description to update
        """
        log.info(f"Editing Item Group: {existing_code}")

        self.click_edit_button(item_name=existing_code)
        self.wait_seconds(1)

        if not self.is_edit_mode():
            log.warning("Edit form not detected, trying to proceed anyway")

        self.fill_form(new_data)
        self.click_update()
        self.wait_seconds(2)

        # Handle SweetAlert2
        if self.is_validation_alert_present(timeout=5):
            title = self.get_swal_title()
            self._dismiss_swal_confirm()
            self._cleanup_swal_containers()
        else:
            self.handle_success_alert(timeout=5)

        IG_SUBMISSIONS.append({
            "action": "edit",
            "original_code": existing_code,
            "new_data": new_data,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        })

        return new_data.get("code", existing_code)

    def view_item_group(self, code):
        """Open the View popup for an Item Group.

        Args:
            code: code of the Item Group row to view
        """
        log.info(f"Viewing Item Group: {code}")
        self.click_view_button(item_name=code)
        self.wait_seconds(1)

    def open_history(self, code):
        """Open the History popup for an Item Group.

        Args:
            code: code of the Item Group row to view history
        """
        log.info(f"Opening History for Item Group: {code}")
        self.click_history_button(item_name=code)
        self.wait_seconds(1)

    def get_form_heading(self):
        """Read the heading text of the current popup."""
        try:
            el = self.driver.find_element(
                By.CSS_SELECTOR,
                ".edit_pop_up h3, .big-model h3, "
                "mat-dialog-container h3, .mat-mdc-dialog-title",
            )
            return el.text.strip()
        except Exception:
            return ""
