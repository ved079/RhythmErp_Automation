"""
quality_parameter_master_page.py
--------------------------------
Page Object Model for RhythmERP Quality Parameter Master screen.

Location: Commodity Settings > Quality Parameter Master
URL:      /#/dynamic-screens/Quality%20Parameter%20Master

FORM LAYOUT (single-page, no stepper):
  - Name            (text input,   required)
  [QPM has ONLY one form field — no dropdowns, no price, no description]

TABLE COLUMNS (visible):
  - View / Edit     (action buttons per row)
  - Name            (only data column)

KNOWN BUGS (documented at time of inspection):
  BUG-001 (HIGH)  : Spaces-only name creates empty record (no trim)
  BUG-002 (HIGH)  : Duplicate names allowed (no uniqueness check)
  BUG-003 (MEDIUM): No maxlength on input, 300+ char names accepted
  BUG-004 (LOW)   : No success SweetAlert after create/update
  BUG-005 (LOW)   : No Delete option anywhere on screen
  BUG-006 (LOW)   : No History / Audit trail feature

KEY RULES:
  - NEVER use Keys.ESCAPE (use backdrop click + JS overlay removal)
  - JS clicks for Angular Material overlays
  - No dropdowns on this screen — no mat-select logic needed
  - No History feature — no history popup methods needed
  - Popup mode uses .edit_pop_up.override_edit_pop_up.popup-mode
  - SweetAlert2 only appears on validation failure (not on success)
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
    StaleElementReferenceException,
)
from common.base_page import BasePage
from common.logger import log
from config import RHYTHMERP_BASE_URL, EXPLICIT_WAIT

# Global list to track every submission for reporting
QPM_SUBMISSIONS = []


class QualityParameterMasterPage(BasePage):
    PAGE_URL = (
        f"{RHYTHMERP_BASE_URL}"
        "/#/dynamic-screens/Quality%20Parameter%20Master"
    )

    # ==============================================================
    #  LOCATORS — Toolbar
    # ==============================================================
    ADD_BUTTON = (
        "css",
        "div[mattooltip='ADD'] button",
    )
    SEARCH_TOGGLE = ("css", "button.search-btn, button[aria-label='Search']")
    REFRESH_BUTTON = ("css", "button[mattooltip='Refresh']")
    MORE_BUTTON = (
        "css",
        "div[mattooltip='More'] button, button[mattooltip='More']",
    )

    # ==============================================================
    #  LOCATORS — Search bar
    # ==============================================================
    SEARCH_INPUT = (
        "css",
        "input#erpSearchInput, .erp-search-wrapper input",
    )
    SEARCH_SUBMIT = ("css", "button.search-btn")

    # ==============================================================
    #  LOCATORS — Table
    # ==============================================================
    TABLE = ("css", "table#excel-table")
    TABLE_ROWS = ("css", "table#excel-table tbody tr")
    TABLE_NAME_CELLS = (
        "css",
        "table#excel-table tbody td.cdk-column-name, "
        "table#excel-table tbody td.mat-column-name, "
        "table#excel-table tbody td:nth-child(3)",
    )
    NO_DATA_ROW = (
        "css",
        "table#excel-table tbody tr td.no-data, "
        "table#excel-table tbody tr.mat-mdc-no-data-row",
    )

    # ==============================================================
    #  LOCATORS — Add / Edit Form popup
    # ==============================================================
    FORM_POPUP = (
        "css",
        ".edit_pop_up.override_edit_pop_up.popup-mode, "
        ".big-model, mat-dialog-container",
    )
    FORM_HEADING = (
        "css",
        ".edit_pop_up h3, .big-model h3, "
        "mat-dialog-container h3, .mat-mdc-dialog-title",
    )

    NAME_INPUT = (
        "css",
        "input[name='Name'], input[name='name'], input[formcontrolname='name']",
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
    #  LOCATORS — Row action buttons (parametrised by name)
    # ==============================================================
    VIEW_BUTTON = (
        "xpath",
        "//td[contains(text(),'{qp_name}')]"
        "/ancestor::tr//td[contains(@class,'cdk-column-view')]"
        "//button",
    )
    EDIT_BUTTON = (
        "xpath",
        "//td[contains(text(),'{qp_name}')]"
        "/ancestor::tr//td[contains(@class,'cdk-column-edit')]"
        "//button",
    )

    # ==============================================================
    #  LOCATORS — SweetAlert2
    # ==============================================================
    SWAL_TITLE = ("css", "#swal2-title")
    SWAL_HTML = ("css", ".swal2-html-container")
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
    #  LOCATORS — Fullscreen toggle
    # ==============================================================
    FULLSCREEN_BUTTON = (
        "css",
        ".edit_pop_up .popup-header button[mattooltip='Fullscreen'], "
        ".big-model .popup-header button[mattooltip='Fullscreen']",
    )
    FULLSCREEN_CONTAINER = ("css", ".big-model.fullscreen")

    # ==============================================================
    #  LOCATORS — Filter panel
    # ==============================================================
    FILTER_TOGGLE = (
        "css",
        "div[mattooltip='Filters'] button, button[mattooltip='Filters']",
    )
    FILTER_PANEL = ("css", ".filter-panel, .cdk-overlay-pane filter-panel")
    FILTER_CHECKBOX = (
        "xpath",
        "//mat-checkbox[contains(.,'{filter_text}')]"
        "//label/div[contains(@class,'mat-mdc-checkbox')]",
    )

    # ==============================================================
    #  LOCATORS — Pagination
    # ==============================================================
    PAGINATION_NEXT = (
        "css",
        "button.mat-paginator-navigation-next, "
        "button[aria-label='Next page']",
    )
    PAGINATION_PREVIOUS = (
        "css",
        "button.mat-paginator-navigation-previous, "
        "button[aria-label='Previous page']",
    )
    PAGINATION_INFO = (
        "css",
        ".mat-mdc-paginator-range-label, "
        ".mat-paginator-range-label",
    )

    # ==============================================================
    #  Navigation & page load
    # ==============================================================

    def navigate_to_page(self):
        """Navigate to the Quality Parameter Master listing page.
        Force-refreshes to clear leftover Angular state from previous tests.
        """
        log.info("Navigating to Quality Parameter Master page...")

        # Navigate to the URL
        self.navigate_to(self.PAGE_URL)

        # Force a full page reload to clear any leftover
        # Angular overlays / popups from the previous test.
        # Without this, the SPA may keep stale state since the
        # hash URL doesn't trigger a full reload.
        self.driver.refresh()

        self._wait_for_page_ready()

    def _wait_for_page_ready(self):
        """Wait until the QPM page is fully loaded:
        1. Table renders
        2. Toolbar buttons (including ADD) are clickable
        """
        # Step 1: Wait for table
        try:
            WebDriverWait(self.driver, EXPLICIT_WAIT).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, "table#excel-table")
                )
            )
            log.info("Quality Parameter Master table loaded")
        except TimeoutException:
            log.warning("QPM table not found, page may be empty")

        # Step 2: Wait for toolbar to fully render (proves ADD button is ready)
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "ul.tbl-export-btn")
                )
            )
            # Extra wait for Angular to bind mattooltip attributes
            self.wait_seconds(1)
            log.info("Quality Parameter Master toolbar ready")
        except TimeoutException:
            log.warning("Toolbar not found, ADD button may be delayed")
            self.wait_seconds(3)

    def is_page_loaded(self):
        """Check if the QPM listing page has loaded."""
        return self.is_displayed(self.TABLE, timeout=10)

    # ==============================================================
    #  Overlay cleanup — NEVER use Keys.ESCAPE
    # ==============================================================

    def _force_close_panels(self):
        """Remove ALL select overlay panes from the DOM via JS.
        Keeps dialog backdrop intact so form popups stay open.
        QPM has no dropdowns, but overlay cleanup is still needed
        for filter panels and other CDK overlays."""
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
        """Try backdrop click first; fall back to JS removal.
        Kept for consistency with Vehicle Master pattern,
        even though QPM has no dropdowns."""
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
        """Click the ADD (+) button to open the create form.
        Uses multiple strategies with proper waits to handle
        intermittent rendering delays.
        """
        log.info("Clicking ADD button...")

        # Ensure toolbar is rendered
        self._wait_for_toolbar()

        # Strategy 1: div[mattooltip='ADD'] button
        try:
            btn = self.driver.find_element(
                By.CSS_SELECTOR, "div[mattooltip='ADD'] button"
            )
            if btn.is_displayed():
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});"
                    "arguments[0].click();",
                    btn,
                )
                self.wait_seconds(1.5)
                if self._is_form_popup_open():
                    # Wait for form content to render inside popup
                    self._wait_for_form_content(timeout=5)
                    log.info("ADD form opened via mattooltip div button")
                    return
        except Exception:
            pass

        # Strategy 2: Find mini-fab button with 'add' icon
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
                            self._wait_for_form_content(timeout=5)
                            log.info("ADD form opened via mini-fab icon")
                            return
                except Exception:
                    continue
        except Exception:
            pass

        # Strategy 3: Click the div[mattooltip='ADD'] wrapper itself
        try:
            div = self.driver.find_element(
                By.CSS_SELECTOR, "div[mattooltip='ADD']"
            )
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});"
                "arguments[0].click();",
                div,
            )
            self.wait_seconds(1.5)
            if self._is_form_popup_open():
                self._wait_for_form_content(timeout=5)
                log.info("ADD form opened via mattooltip div wrapper")
                return
        except Exception:
            pass

        # Strategy 4: BasePage click_with_retry
        try:
            self.click_with_retry(self.ADD_BUTTON)
            self.wait_seconds(1.5)
            if self._is_form_popup_open():
                self._wait_for_form_content(timeout=5)
                log.info("ADD form opened via click_with_retry")
                return
        except Exception:
            pass

        raise Exception("ADD button not found or not clickable")

    def _wait_for_toolbar(self):
        """Wait for the toolbar and ADD button to be present and visible.
        Retries with increasing waits to handle Angular rendering delays.
        """
        for attempt in range(3):
            try:
                add_container = self.driver.find_elements(
                    By.CSS_SELECTOR, "div[mattooltip='ADD']"
                )
                if add_container and add_container[0].is_displayed():
                    return
            except Exception:
                pass

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

            log.info(f"Waiting for toolbar... attempt {attempt + 1}/3")
            self.wait_seconds(2)

        log.warning("Toolbar wait exhausted, ADD button may not be ready")

    def _is_form_popup_open(self):
        """Quick check if any form popup is visible.
        QPM uses .edit_pop_up.override_edit_pop_up.popup-mode by default,
        but may also use .big-model for fullscreen mode.
        """
        try:
            popups = self.driver.find_elements(
                By.CSS_SELECTOR,
                "div.edit_pop_up.override_edit_pop_up.popup-mode, "
                "div.big-model, mat-dialog-container, "
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

    def _wait_for_form_content(self, timeout=5):
        """Wait for form content (inputs) to render inside the popup.
        The popup container may appear before the Angular form renders.
        Polls for any visible input inside the popup.
        """
        import time as _time
        deadline = _time.time() + timeout
        while _time.time() < deadline:
            try:
                # Check for any input inside known popup containers
                inputs = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    "div.edit_pop_up input, "
                    "div.big-model input, "
                    "mat-dialog-container input, "
                    "div.cdk-overlay-container input"
                )
                for inp in inputs:
                    try:
                        if inp.is_displayed():
                            return True
                    except Exception:
                        continue
            except Exception:
                pass
            self.wait_seconds(0.5)

        # Content didn't appear — log debug info
        log.warning(
            f"Form content did not render within {timeout}s. "
            "Running debug diagnostics..."
        )
        self._debug_popup_info()
        return False

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
                    if (
                        icon.text.strip().lower() == "refresh"
                        and btn.is_displayed()
                    ):
                        self.driver.execute_script(
                            "arguments[0].click();", btn
                        )
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
        """Fill the Quality Parameter Master add/edit form.
        QPM has only ONE field: Name (text input, required).
        """
        log.info("Filling Quality Parameter Master form...")

        # Name — the only form field
        if data.get("name") is not None:
            self.type_text(
                self.NAME_INPUT, str(data["name"]), clear_first=True
            )

        self._force_close_panels()
        log.info("Quality Parameter Master form filled")

    # ==============================================================
    #  Form submission & cancellation
    # ==============================================================

    def submit(self):
        """Click the Submit button on the Create form."""
        log.info("Submitting Quality Parameter Master form...")
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
                ".edit_pop_up button mat-icon, "
                ".big-model button mat-icon, "
                "mat-dialog-container button mat-icon",
            )
            for icon in close_btns:
                try:
                    if (
                        icon.text.strip().lower() == "close"
                        and icon.is_displayed()
                    ):
                        self.driver.execute_script(
                            "arguments[0].closest('button').click();", icon
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

    # ==============================================================
    #  SweetAlert2 handlers
    # ==============================================================

    def handle_success_alert(self, timeout=EXPLICIT_WAIT):
        """Wait for SweetAlert2 success popup, read message, click OK.
        Returns the alert message text, or '' if no alert appeared.

        NOTE (BUG-004): QPM does NOT show a success SweetAlert after
        create or update. The popup simply closes. This method is kept
        for API compatibility with Vehicle Master pattern, but will
        typically return '' for QPM.
        """
        log.info("Waiting for success alert...")
        try:
            wait = WebDriverWait(self.driver, timeout)
            title_el = wait.until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, "#swal2-title")
                )
            )
            msg = title_el.text.strip()

            # Click confirm
            try:
                confirm = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, ".swal2-confirm")
                    )
                )
                try:
                    confirm.click()
                except Exception:
                    self.driver.execute_script(
                        "arguments[0].click();", confirm
                    )
                log.info(f"Success alert handled: {msg}")
            except Exception:
                try:
                    self.driver.execute_script(
                        "document.querySelectorAll('.swal2-confirm')"
                        ".forEach(function(b){b.click();});"
                    )
                    log.info(f"Success alert handled via JS: {msg}")
                except Exception:
                    log.warning("Could not click swal2-confirm")

            # Wait for alert to disappear
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
            log.info("No success alert appeared within timeout (expected for QPM)")
            return ""

    def handle_validation_warning(self, timeout=10):
        """Handle SweetAlert2 validation warning popup.
        QPM shows this when submitting with empty Name field:
        Title: "Validation Failed"
        Message: "Please correct the highlighted fields"
        Returns the warning title text, or ''.
        """
        log.info("Checking for validation warning...")
        try:
            wait = WebDriverWait(self.driver, timeout)
            title_el = wait.until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, "#swal2-title")
                )
            )
            msg = title_el.text.strip()

            # Also read the HTML message if present
            html_msg = ""
            try:
                html_el = self.driver.find_element(
                    By.CSS_SELECTOR, ".swal2-html-container"
                )
                html_msg = html_el.text.strip()
            except Exception:
                pass

            # Click confirm to dismiss
            try:
                confirm = self.driver.find_element(
                    By.CSS_SELECTOR, ".swal2-confirm"
                )
                self.driver.execute_script(
                    "arguments[0].click();", confirm
                )
            except Exception:
                pass

            # Wait for alert to disappear
            try:
                WebDriverWait(self.driver, 5).until(
                    EC.invisibility_of_element_located(
                        (By.CSS_SELECTOR, ".swal2-container")
                    )
                )
            except Exception:
                pass

            log.info(f"Validation warning handled: {msg} — {html_msg}")
            return msg
        except TimeoutException:
            return ""

    def handle_error_toast(self, timeout=10):
        """Check for error toast notification.
        Returns the toast message text, or ''.
        """
        log.info("Checking for error toast...")
        toast_loc = (
            "css",
            "snack-bar-container .mat-mdc-snack-bar-label, "
            "[role='alert'], .mat-mdc-snack-bar .mdc-snackbar__label",
        )
        if self.is_displayed(toast_loc, timeout=timeout):
            text = self.get_text(toast_loc)
            log.info(f"Error toast found: {text}")
            return text
        return ""

    def is_validation_alert_present(self, timeout=5):
        """Check if any SweetAlert2 popup is currently visible."""
        return self.is_displayed(self.SWAL_TITLE, timeout=timeout)

    def get_swal_title(self):
        """Read the SweetAlert2 title text if visible."""
        try:
            el = self.driver.find_element(By.CSS_SELECTOR, "#swal2-title")
            if el.is_displayed():
                return el.text.strip()
        except Exception:
            pass
        return ""

    def get_swal_html_message(self):
        """Read the SweetAlert2 HTML container message if visible."""
        try:
            el = self.driver.find_element(
                By.CSS_SELECTOR, ".swal2-html-container"
            )
            if el.is_displayed():
                return el.text.strip()
        except Exception:
            pass
        return ""

    # ==============================================================
    #  Field-level error checking
    # ==============================================================

    def get_mat_error_text(self):
        """Get all visible mat-error texts from the form.
        Returns a list of error strings.
        """
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
        """Check if a specific form field has a visible mat-error.
        For QPM, field_label would be 'Name'.
        """
        try:
            locator = (
                "xpath",
                f"//mat-label[contains(.,'{field_label}')]"
                "/ancestor::mat-form-field//mat-error",
            )
            return self.is_displayed(locator, timeout=3)
        except Exception:
            return False

    # ==============================================================
    #  Verification helpers
    # ==============================================================

    def is_add_form_open(self):
        """Check if the Add form popup is currently visible.
        Uses a multi-strategy approach:
          1. Check the popup container is visible
          2. Check the NAME_INPUT is visible (primary)
          3. Fallback: check for ANY input inside the popup
        """
        # Strategy 1: Check popup container is visible
        popup_visible = self._is_form_popup_open()

        # Strategy 2: Check NAME_INPUT directly
        name_input_visible = self.is_displayed(self.NAME_INPUT, timeout=8)

        if name_input_visible:
            return True

        # Strategy 3: If popup is open but NAME_INPUT not found,
        # try broader selectors — QPM input may have different attrs
        if popup_visible:
            try:
                # Try any input inside the popup container
                popup_inputs = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    "div.edit_pop_up input, "
                    "div.big-model input, "
                    "mat-dialog-container input, "
                    "div.cdk-overlay-container input"
                )
                for inp in popup_inputs:
                    try:
                        if inp.is_displayed():
                            log.info(
                                "Form input found via broad selector: "
                                f"name={inp.get_attribute('name')}, "
                                f"formcontrolname={inp.get_attribute('formcontrolname')}, "
                                f"placeholder={inp.get_attribute('placeholder')}"
                            )
                            return True
                    except Exception:
                        continue
            except Exception:
                pass

            # Popup is open but no input found — log debug info
            log.warning(
                "Popup container is visible but no input found. "
                "Taking debug screenshot..."
            )
            self._debug_popup_info()

        return False

    def is_form_closed(self):
        """Check if the form popup is no longer visible."""
        # Check both popup container AND input
        popup_gone = not self._is_form_popup_open()
        if popup_gone:
            return True
        # Fallback: check NAME_INPUT
        return not self.is_displayed(self.NAME_INPUT, timeout=3)

    def _debug_popup_info(self):
        """Log debug information about the current popup state.
        Helps diagnose selector mismatches when forms don't open."""
        try:
            # Check what inputs exist in the popup
            all_inputs = self.driver.find_elements(
                By.CSS_SELECTOR,
                "div.edit_pop_up input, "
                "div.big-model input, "
                "mat-dialog-container input, "
                "div.cdk-overlay-container input"
            )
            log.info(f"DEBUG: Found {len(all_inputs)} inputs in popup")
            for i, inp in enumerate(all_inputs):
                try:
                    log.info(
                        f"  Input[{i}]: "
                        f"tag={inp.tag_name}, "
                        f"name={inp.get_attribute('name')}, "
                        f"formcontrolname={inp.get_attribute('formcontrolname')}, "
                        f"type={inp.get_attribute('type')}, "
                        f"placeholder={inp.get_attribute('placeholder')}, "
                        f"visible={inp.is_displayed()}"
                    )
                except Exception:
                    pass

            # Check what popup containers exist
            containers = self.driver.find_elements(
                By.CSS_SELECTOR,
                "div.edit_pop_up, div.big-model, "
                "mat-dialog-container, div.popup-wrapper"
            )
            log.info(f"DEBUG: Found {len(containers)} popup containers")
            for i, c in enumerate(containers):
                try:
                    log.info(
                        f"  Container[{i}]: "
                        f"class={c.get_attribute('class')}, "
                        f"visible={c.is_displayed()}, "
                        f"text_preview={c.text[:100]}"
                    )
                except Exception:
                    pass
        except Exception as e:
            log.warning(f"Debug popup info failed: {e}")

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

    def is_view_mode(self):
        """Check if the currently open form is in View (read-only) mode."""
        try:
            name_input = self.find_visible_element(self.NAME_INPUT, timeout=5)
            return not name_input.is_enabled()
        except Exception:
            return False

    def is_edit_mode(self):
        """Check if the currently open form is in Edit mode
        (Update button visible)."""
        return self.is_displayed(self.UPDATE_BUTTON, timeout=5)

    def get_form_field_values(self):
        """Read all form field values from the currently open popup.
        QPM has only one field: name.
        Returns a dict with key: name.
        """
        values = {}

        try:
            name_input = self.driver.find_element(
                By.CSS_SELECTOR,
                "input[name='Name'], input[name='name'], "
                "input[formcontrolname='name']",
            )
            val = name_input.get_attribute("value") or ""
            if not val:
                try:
                    val = self.driver.execute_script(
                        "return arguments[0].value;", name_input
                    ) or ""
                except Exception:
                    pass
            values["name"] = val
        except Exception:
            values["name"] = ""

        return values

    def get_name_input_maxlength(self):
        """Read the maxlength attribute of the Name input field.
        BUG-003: No maxlength is set on the QPM Name input.
        Returns the maxlength value or None if not set.
        """
        try:
            name_input = self.driver.find_element(
                By.CSS_SELECTOR,
            "input[name='Name'], input[name='name'], "
            "input[formcontrolname='name']",
            )
            maxlength = name_input.get_attribute("maxlength")
            return maxlength
        except Exception:
            return None

    # ==============================================================
    #  Table interactions
    # ==============================================================

    def get_table_row_count(self):
        """Return the number of visible data rows in the table."""
        rows = self.driver.find_elements(
            By.CSS_SELECTOR, "table#excel-table tbody tr"
        )
        return len(rows)

    def get_all_qp_names(self):
        """Return a list of all Quality Parameter names in the
        current table view."""
        cells = self.driver.find_elements(
            By.CSS_SELECTOR,
            "table#excel-table tbody td.cdk-column-name, "
            "table#excel-table tbody td.mat-column-name, "
            "table#excel-table tbody td:nth-child(3)",
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

    def is_qp_in_table(self, qp_name):
        """Check if a Quality Parameter with the given name
        appears in the table."""
        names = self.get_all_qp_names()
        return any(qp_name.strip().lower() in n.lower() for n in names)

    def find_qp_row_index(self, qp_name):
        """Find the 0-based row index for a QP by name.
        Returns -1 if not found.
        """
        rows = self.driver.find_elements(
            By.CSS_SELECTOR, "table#excel-table tbody tr"
        )
        for i, row in enumerate(rows):
            try:
                cells = row.find_elements(By.TAG_NAME, "td")
                for cell in cells:
                    if (
                        qp_name.strip().lower()
                        in cell.text.strip().lower()
                    ):
                        return i
            except StaleElementReferenceException:
                continue
        return -1

    def get_qp_details_from_row(self, row_index=0):
        """Read text from a table row. QPM has only Name column.
        Returns dict with key: name.
        """
        rows = self.driver.find_elements(
            By.CSS_SELECTOR, "table#excel-table tbody tr"
        )
        if row_index >= len(rows):
            return {}
        row = rows[row_index]
        cells = row.find_elements(By.TAG_NAME, "td")
        data_cells = [c for c in cells if c.text.strip()]
        result = {}
        if len(data_cells) >= 1:
            result["name"] = data_cells[0].text.strip()
        return result

    # ==============================================================
    #  Row action buttons — JS click via _click_action_button
    # ==============================================================

    def _click_action_button(self, qp_name, action_xpath_template):
        """Click a row action button (View/Edit) using parametrised
        XPath. Falls back to index-based button click.
        Pure JS click to avoid overlay interception.
        """
        self._force_close_panels()
        xpath = action_xpath_template.format(qp_name=qp_name)

        # Strategy 1: Parametrised XPath
        try:
            btns = self.driver.find_elements(By.XPATH, xpath)
            for btn in btns:
                try:
                    if btn.is_displayed():
                        self.driver.execute_script(
                            "arguments[0].click();", btn
                        )
                        self.wait_seconds(1)
                        return True
                except Exception:
                    continue
        except Exception:
            pass

        # Strategy 2: Find row by name, click button by index
        row_idx = self.find_qp_row_index(qp_name)
        if row_idx >= 0:
            return self._click_action_button_by_index(
                row_idx, action_xpath_template
            )

        log.warning(
            f"Action button not found for QP: {qp_name}"
        )
        return False

    def _click_action_button_by_index(self, row_index, action_xpath_template):
        """Fallback: click action button by row index position.
        QPM has only View (idx 0) and Edit (idx 1) — no History.
        """
        rows = self.driver.find_elements(
            By.CSS_SELECTOR, "table#excel-table tbody tr"
        )
        if row_index >= len(rows):
            raise Exception(
                f"Row index {row_index} out of range "
                f"(total rows: {len(rows)})"
            )
        row = rows[row_index]
        btns = row.find_elements(By.CSS_SELECTOR, "button")

        # Determine which button based on the template keyword
        if "cdk-column-view" in action_xpath_template:
            idx = 0
        elif "cdk-column-edit" in action_xpath_template:
            idx = 1
        else:
            idx = 0

        if idx < len(btns):
            self.driver.execute_script(
                "arguments[0].click();", btns[idx]
            )
            self.wait_seconds(1)
            return True
        raise Exception(
            f"Action button index {idx} not found in row {row_index}"
        )

    def click_view_button(self, qp_name=None, row_index=0):
        """Click the View button for a QP row."""
        log.info(f"Clicking View button for: {qp_name or row_index}...")
        if qp_name:
            return self._click_action_button(qp_name, self.VIEW_BUTTON[1])
        return self._click_action_button_by_index(
            row_index, self.VIEW_BUTTON[1]
        )

    def click_edit_button(self, qp_name=None, row_index=0):
        """Click the Edit button for a QP row."""
        log.info(f"Clicking Edit button for: {qp_name or row_index}...")
        if qp_name:
            return self._click_action_button(qp_name, self.EDIT_BUTTON[1])
        return self._click_action_button_by_index(
            row_index, self.EDIT_BUTTON[1]
        )

    # ==============================================================
    #  View & Edit specific verifications
    # ==============================================================

    def verify_view_popup_read_only(self):
        """Verify that the View popup fields are read-only / disabled.
        QPM has only one field (Name) to check.
        Returns True if the Name field is non-editable.
        """
        log.info("Verifying View popup is read-only...")
        all_readonly = True

        try:
            name_input = self.find_visible_element(
                self.NAME_INPUT, timeout=5
            )
            if name_input.is_enabled():
                all_readonly = False
                log.warning("Name field is editable in View mode")
        except Exception:
            pass

        # Submit should NOT be visible, Update should NOT be visible
        if self.is_displayed(self.SUBMIT_BUTTON, timeout=2):
            all_readonly = False
            log.warning("Submit button visible in View mode")
        if self.is_displayed(self.UPDATE_BUTTON, timeout=2):
            all_readonly = False
            log.warning("Update button visible in View mode")

        return all_readonly

    def verify_edit_popup_editable(self):
        """Verify that the Edit popup fields are editable.
        Returns True if the Update button is visible (edit mode).
        """
        log.info("Verifying Edit popup is editable...")
        return self.is_displayed(self.UPDATE_BUTTON, timeout=5)

    # ==============================================================
    #  Search functionality
    # ==============================================================

    def search_qp(self, qp_name):
        """Search for a Quality Parameter by name in the table
        search bar. Returns True if found in the table results.
        """
        log.info(f"Searching for QP: {qp_name}")
        try:
            self._force_close_panels()
            self.wait_seconds(1)

            # Toggle search bar open
            self.driver.execute_script(
                "var b = document.querySelector("
                "'button.search-btn'); if(b) b.click();"
            )
            self.wait_seconds(1)

            # Type search text via JS (Angular reactive form)
            self.driver.execute_script(
                "var i = document.querySelector("
                "'.erp-search-wrapper input, "
                "input#erpSearchInput');"
                "if(i){"
                "  i.focus();"
                "  var s = Object.getOwnPropertyDescriptor("
                "    window.HTMLInputElement.prototype,'value').set;"
                "  s.call(i, arguments[0]);"
                "  i.dispatchEvent(new Event('input',{bubbles:true}));"
                "  i.dispatchEvent(new KeyboardEvent('keydown',"
                "    {key:'Enter',keyCode:13,bubbles:true}));"
                "}",
                qp_name,
            )
            self.wait_seconds(3)

            # Check results — retry a few times for slow Angular filtering
            found = False
            for _ in range(3):
                found = self.is_qp_in_table(qp_name)
                if found:
                    break
                self.wait_seconds(2)
            if found:
                log.info(f"QP found in table: {qp_name}")
            else:
                log.warning(f"QP NOT found in table: {qp_name}")
            return found

        except Exception as e:
            log.error(f"Search failed: {e}")
            return False

    def clear_search(self):
        """Clear the search input and reset the table."""
        try:
            search_input = self.driver.find_element(
                By.CSS_SELECTOR,
                ".erp-search-wrapper input, input#erpSearchInput",
            )
            if search_input.is_displayed():
                search_input.clear()
                # Press Enter to refresh results
                search_input.send_keys(Keys.RETURN)
                self.wait_seconds(1)
        except Exception:
            pass

    def verify_qp_exists(self, qp_name):
        """Navigate to page, search, and verify a QP exists."""
        self.navigate_to_page()
        found = self.search_qp(qp_name)
        self.clear_search()
        return found

    # ==============================================================
    #  Fullscreen toggle
    # ==============================================================

    def toggle_fullscreen(self):
        """Click the fullscreen toggle button on the popup header.
        QPM popup starts in normal mode (.edit_pop_up.popup-mode).
        Clicking fullscreen adds the .big-model.fullscreen class.
        """
        log.info("Toggling fullscreen mode...")
        try:
            fullscreen_btns = self.driver.find_elements(
                By.CSS_SELECTOR,
                ".popup-header button mat-icon, "
                ".edit_pop_up button mat-icon, "
                ".big-model button mat-icon",
            )
            for icon in fullscreen_btns:
                try:
                    tooltip = icon.find_element(
                        By.XPATH, "./ancestor::button"
                    ).get_attribute("mattooltip")
                    if tooltip and "fullscreen" in tooltip.lower():
                        self.driver.execute_script(
                            "arguments[0].closest('button').click();", icon
                        )
                        self.wait_seconds(1)
                        log.info("Fullscreen toggled")
                        return True
                except Exception:
                    continue
        except Exception:
            pass

        # Fallback: try direct button click
        try:
            self.click_with_retry(self.FULLSCREEN_BUTTON)
            self.wait_seconds(1)
            log.info("Fullscreen toggled via fallback")
            return True
        except Exception:
            pass

        log.warning("Fullscreen button not found")
        return False

    def is_fullscreen_mode(self):
        """Check if the popup is currently in fullscreen mode."""
        try:
            fullscreen_el = self.driver.find_element(
                By.CSS_SELECTOR, ".big-model.fullscreen"
            )
            return fullscreen_el.is_displayed()
        except Exception:
            return False

    # ==============================================================
    #  Filter panel
    # ==============================================================

    def open_filter_panel(self):
        """Click the Filters button to open the filter panel."""
        log.info("Opening filter panel...")
        try:
            self.driver.execute_script(
                "var b = document.querySelector("
                "\"div[mattooltip='Filters'] button, "
                "button[mattooltip='Filters']\");"
                "if(b) b.click();"
            )
            self.wait_seconds(1)
            log.info("Filter panel opened")
        except Exception:
            log.warning("Filter button not found")

    def is_filter_panel_open(self):
        """Check if the filter panel is currently visible."""
        try:
            filter_els = self.driver.find_elements(
                By.CSS_SELECTOR,
                ".filter-panel, .cdk-overlay-pane filter-panel, "
                ".cdk-overlay-pane .filter-content",
            )
            for f in filter_els:
                try:
                    if f.is_displayed():
                        return True
                except Exception:
                    continue
        except Exception:
            pass
        return False

    def close_filter_panel(self):
        """Close the filter panel by clicking backdrop or Close button."""
        try:
            # Try backdrop click
            backdrops = self.driver.find_elements(
                By.CSS_SELECTOR,
                "div.cdk-overlay-backdrop",
            )
            for bd in backdrops:
                try:
                    if bd.is_displayed():
                        bd.click()
                        self.wait_seconds(0.5)
                        return
                except Exception:
                    pass
        except Exception:
            pass

        # Fallback: JS close
        self._force_close_panels()

    # ==============================================================
    #  Pagination
    # ==============================================================

    def get_pagination_info(self):
        """Read the paginator range label text.
        E.g. '1 - 10 of 25'
        """
        try:
            el = self.driver.find_element(
                By.CSS_SELECTOR,
                ".mat-mdc-paginator-range-label, "
                ".mat-paginator-range-label",
            )
            return el.text.strip()
        except Exception:
            return ""

    def click_next_page(self):
        """Click the Next Page button in paginator."""
        log.info("Clicking Next Page...")
        try:
            next_btn = self.driver.find_element(
                By.CSS_SELECTOR,
                "button.mat-paginator-navigation-next, "
                "button[aria-label='Next page']",
            )
            self.driver.execute_script("arguments[0].click();", next_btn)
            self.wait_seconds(2)
            log.info("Next page clicked")
        except Exception:
            log.warning("Next Page button not found or disabled")

    def click_previous_page(self):
        """Click the Previous Page button in paginator."""
        log.info("Clicking Previous Page...")
        try:
            prev_btn = self.driver.find_element(
                By.CSS_SELECTOR,
                "button.mat-paginator-navigation-previous, "
                "button[aria-label='Previous page']",
            )
            self.driver.execute_script("arguments[0].click();", prev_btn)
            self.wait_seconds(2)
            log.info("Previous page clicked")
        except Exception:
            log.warning("Previous Page button not found or disabled")

    # ==============================================================
    #  Column sort
    # ==============================================================

    def click_name_column_header(self):
        """Click the Name column header to toggle sort order."""
        log.info("Clicking Name column header for sort...")
        try:
            header = self.driver.find_element(
                By.CSS_SELECTOR,
                "table#excel-table th.cdk-column-name, "
                "table#excel-table th.mat-column-name",
            )
            self.driver.execute_script("arguments[0].click();", header)
            self.wait_seconds(1)
            log.info("Name column header clicked")
        except Exception:
            # Fallback: find any th containing "Name"
            try:
                headers = self.driver.find_elements(
                    By.CSS_SELECTOR, "table#excel-table th"
                )
                for h in headers:
                    if "name" in h.text.strip().lower():
                        self.driver.execute_script(
                            "arguments[0].click();", h
                        )
                        self.wait_seconds(1)
                        log.info("Name column header clicked via fallback")
                        return
            except Exception:
                pass
            log.warning("Name column header not found")

    # ==============================================================
    #  Convenience: full CRUD workflow in one method
    # ==============================================================

    def create_quality_parameter(self, data):
        """Full create workflow: open add form → fill → submit.
        Returns the name that was submitted.
        Tracks submission in QPM_SUBMISSIONS for reporting.
        """
        name = data.get("name", "")
        log.info(f"Creating Quality Parameter: {name}")

        self.open_add_form()
        assert self.is_add_form_open(), "Add form did not open"

        self.fill_form(data)
        self.submit()

        # BUG-004: No success alert in QPM, just check popup closed
        self.wait_seconds(1)

        # Check if validation alert appeared instead
        if self.is_validation_alert_present(timeout=3):
            warning = self.get_swal_title()
            log.warning(f"Validation alert after submit: {warning}")

        # Track submission
        QPM_SUBMISSIONS.append({
            "name": name,
            "action": "CREATE",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        })

        return name

    def edit_quality_parameter(self, qp_name, new_data):
        """Full edit workflow: search → click edit → fill → update.
        Returns the new name that was submitted.
        """
        new_name = new_data.get("name", "")
        log.info(f"Editing QP '{qp_name}' → '{new_name}'")

        # Search for the record first
        self.navigate_to_page()
        self.search_qp(qp_name)

        # Click Edit on the row
        self.click_edit_button(qp_name=qp_name)
        self.wait_seconds(1)

        # Should be in edit mode
        assert self.is_edit_mode(), "Edit mode not activated"

        # Fill new data and update
        self.fill_form(new_data)
        self.click_update()

        # BUG-004: No success alert in QPM
        self.wait_seconds(1)

        # Track submission
        QPM_SUBMISSIONS.append({
            "name": new_name,
            "old_name": qp_name,
            "action": "EDIT",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        })

        return new_name

    def view_quality_parameter(self, qp_name):
        """Full view workflow: search → click view → verify read-only → close.
        Returns the form field values dict.
        """
        log.info(f"Viewing QP: {qp_name}")

        # Search for the record
        self.navigate_to_page()
        self.search_qp(qp_name)

        # Click View on the row
        self.click_view_button(qp_name=qp_name)
        self.wait_seconds(1)

        # Read values and verify read-only
        values = self.get_form_field_values()
        self.verify_view_popup_read_only()

        # Close the view popup
        self.close_popup()

        return values

    # ==============================================================
    #  Screenshot helper
    # ==============================================================

    def take_screenshot(self, filename):
        """Take a screenshot and save to the screenshots directory."""
        import os
        screenshots_dir = os.path.join(
            os.path.dirname(__file__), "screenshots"
        )
        os.makedirs(screenshots_dir, exist_ok=True)
        filepath = os.path.join(screenshots_dir, filename)
        self.driver.save_screenshot(filepath)
        log.info(f"Screenshot saved: {filepath}")
        return filepath
