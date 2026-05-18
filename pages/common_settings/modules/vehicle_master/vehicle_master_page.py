"""
vehicle_master_page.py
----------------------
Page Object Model for RhythmERP Vehicle Master screen.

Location: Common Settings > Vehicle Master
URL:      /#/dynamic-screens/Vehicle%20Master

FORM LAYOUT (single-page, no stepper):
  - Name            (text input,   required)
  - Vehicle Price   (text input,   required, numeric)
  - Vehicle Type    (mat-select,   required, searchable dropdown)
  - Fuel Type       (mat-select,   required, searchable dropdown)
  - Description     (text input,   optional)

TABLE COLUMNS (visible):
  - View / Edit / History  (action buttons per row)
  - Name
  - Vehicle Price
  - Description

KEY RULES:
  - NEVER use Keys.ESCAPE (use backdrop click + JS overlay removal)
  - JS clicks for Angular Material overlays
  - Dropdown options read dynamically at runtime (never hardcode)
  - History search requires Enter key after typing
  - Stacked popups: History -> View (z-index 1001 over 1000)
"""

import os
import sys
import time
import random
import copy

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
VM_SUBMISSIONS = []


class VehicleMasterPage(BasePage):
    PAGE_URL = f"{RHYTHMERP_BASE_URL}/#/dynamic-screens/Vehicle%20Master"

    # ==============================================================
    #  LOCATORS — Toolbar
    # ==============================================================
    ADD_BUTTON = (
        "css",
        "button.erp-add-btn",
    )
    SEARCH_TOGGLE = ("css", "button.search-btn, button[aria-label='Search']")
    REFRESH_BUTTON = ("css", "button[mattooltip='Refresh']")

    # ==============================================================
    #  LOCATORS — Search bar
    # ==============================================================
    SEARCH_INPUT = ("css", "input#erpSearchInput, .erp-search-wrapper input")
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
        "table#excel-table tbody td:nth-child(4)",
    )
    TABLE_PRICE_CELLS = (
        "css",
        "table#excel-table tbody td.cdk-column-vehiclePrice, "
        "table#excel-table tbody td.mat-column-vehiclePrice, "
        "table#excel-table tbody td:nth-child(5)",
    )
    TABLE_DESC_CELLS = (
        "css",
        "table#excel-table tbody td.cdk-column-description, "
        "table#excel-table tbody td.mat-column-description, "
        "table#excel-table tbody td:nth-child(6)",
    )
    NO_DATA_ROW = (
        "css",
        "table#excel-table tbody tr td.no-data, "
        "table#excel-table tbody tr.mat-mdc-no-data-row",
    )

    # ==============================================================
    #  LOCATORS — Add / Edit Form popup
    # ==============================================================
    FORM_POPUP = ("css", ".big-model, mat-dialog-container")
    FORM_HEADING = (
        "css",
        ".big-model h3, mat-dialog-container h3, .mat-mdc-dialog-title",
    )

    NAME_INPUT = (
        "css",
        "input[name='Name'], input[formcontrolname='name']",
    )
    PRICE_INPUT = (
        "css",
        "input[name='Vehicle Price'], "
        "input[formcontrolname='vehiclePrice'], "
        "input[name='vehiclePrice']",
    )
    VEHICLE_TYPE_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Vehicle Type')]"
        "/ancestor::mat-form-field//mat-select",
    )
    FUEL_TYPE_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Fuel Type')]"
        "/ancestor::mat-form-field//mat-select",
    )
    DESCRIPTION_INPUT = (
        "css",
        "input[name='Description'], textarea[formcontrolname='description']",
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
    #  LOCATORS — Row action buttons (parametrised by vehicle name)
    # ==============================================================
    VIEW_BUTTON = (
        "xpath",
        "//td[contains(text(),'{vehicle_name}')]"
        "/ancestor::tr//td[contains(@class,'cdk-column-view')]"
        "//button",
    )
    EDIT_BUTTON = (
        "xpath",
        "//td[contains(text(),'{vehicle_name}')]"
        "/ancestor::tr//td[contains(@class,'cdk-column-edit')]"
        "//button",
    )
    HISTORY_BUTTON = (
        "xpath",
        "//td[contains(text(),'{vehicle_name}')]"
        "/ancestor::tr//td[contains(@class,'cdk-column-history')]"
        "//button",
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
        ".big-model table tbody tr, mat-dialog-container table tbody tr",
    )
    HISTORY_SEARCH_INPUT = (
        "xpath",
        "//div[contains(@class,'big-model')]"
        "//input[contains(@placeholder,'Search') or contains(@placeholder,'search')]",
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
        """Navigate to the Vehicle Master listing page.
        Force-refreshes to clear leftover Angular state from previous tests.
        """
        log.info("Navigating to Vehicle Master page...")
        
        # Navigate to the URL
        self.navigate_to(self.PAGE_URL)
        
        # Force a full page reload to clear any leftover
        # Angular overlays / popups from the previous test.
        # Without this, the SPA may keep stale state since the
        # hash URL doesn't trigger a full reload.
        self.driver.refresh()
        
        self._wait_for_page_ready()

    def _wait_for_page_ready(self):
        """Wait until the Vehicle Master page is fully loaded:
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
            log.info("Vehicle Master table loaded")
        except TimeoutException:
            log.warning("Vehicle Master table not found, page may be empty")

        # Step 2: Wait for toolbar to fully render (proves ADD button is ready)
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "ul.tbl-export-btn")
                )
            )
            # Extra wait for Angular to bind mattooltip attributes
            self.wait_seconds(1)
            log.info("Vehicle Master toolbar ready")
        except TimeoutException:
            log.warning("Toolbar not found, ADD button may be delayed")
            self.wait_seconds(3)

    def is_page_loaded(self):
        """Check if the Vehicle Master listing page has loaded."""
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
        """Click the ADD (+) button to open the create form.
        Uses multiple strategies with proper waits to handle
        intermittent rendering delays.
        """
        log.info("Clicking ADD button...")

        # Ensure toolbar is rendered
        self._wait_for_toolbar()

        # Strategy 1: button.erp-add-btn (matches actual HTML structure)
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
                            log.info("ADD form opened via mini-fab icon")
                            return
                except Exception:
                    continue
        except Exception:
            pass

        # Strategy 3: Click the button.erp-add-btn wrapper itself
        try:
            div = self.driver.find_element(
                By.CSS_SELECTOR, "button.erp-add-btn"
            )
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});"
                "arguments[0].click();",
                div,
            )
            self.wait_seconds(1.5)
            if self._is_form_popup_open():
                log.info("ADD form opened via mattooltip div wrapper")
                return
        except Exception:
            pass

        # Strategy 4: BasePage click_with_retry
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
        """Wait for the toolbar and ADD button to be present and visible.
        Retries with increasing waits to handle Angular rendering delays.
        """
        for attempt in range(3):
            try:
                # Check if ADD button container exists
                add_container = self.driver.find_elements(
                    By.CSS_SELECTOR, "button.erp-add-btn"
                )
                if add_container and add_container[0].is_displayed():
                    return  # Toolbar is ready
            except Exception:
                pass

            # Also try finding by icon
            try:
                mini_fabs = self.driver.find_elements(
                    By.CSS_SELECTOR, "button.mat-mdc-mini-fab"
                )
                for btn in mini_fabs:
                    try:
                        icon = btn.find_element(By.CSS_SELECTOR, "mat-icon")
                        if icon.text.strip().lower() == "add":
                            return  # ADD button found
                    except Exception:
                        continue
            except Exception:
                pass

            # Not found yet — wait and retry
            log.info(f"Waiting for toolbar... attempt {attempt + 1}/3")
            self.wait_seconds(2)

        log.warning("Toolbar wait exhausted, ADD button may not be ready")

    def _is_form_popup_open(self):
        """Quick check if any form popup (big-model or dialog) is visible."""
        try:
            popups = self.driver.find_elements(
                By.CSS_SELECTOR,
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

    def fill_vehicle_form(self, data):
        """Fill all fields on the Vehicle Master add/edit form.
        Dropdown values: if None/empty, picks a random option from the live UI.
        """
        log.info("Filling Vehicle Master form...")

        # Name
        if data.get("name"):
            self.type_text(self.NAME_INPUT, str(data["name"]), clear_first=True)

        # Price
        if data.get("price"):
            self.type_text(
                self.PRICE_INPUT, str(data["price"]), clear_first=True
            )

        # Vehicle Type dropdown (dynamic)
        if data.get("vehicle_type"):
            self._select_mat_option(
                self.VEHICLE_TYPE_SELECT, str(data["vehicle_type"])
            )
        else:
            self._select_random_from_dropdown(
                self.VEHICLE_TYPE_SELECT, "Vehicle Type"
            )

        # Fuel Type dropdown (dynamic)
        if data.get("fuel_type"):
            self._select_mat_option(
                self.FUEL_TYPE_SELECT, str(data["fuel_type"])
            )
        else:
            self._select_random_from_dropdown(
                self.FUEL_TYPE_SELECT, "Fuel Type"
            )

        # Description
        if data.get("description"):
            self.type_text(
                self.DESCRIPTION_INPUT, str(data["description"]),
                clear_first=True,
            )

        self._force_close_panels()
        log.info("Vehicle Master form filled")

    # ==============================================================
    #  Form submission & cancellation
    # ==============================================================

    def submit(self):
        """Click the Submit button on the Create form."""
        log.info("Submitting Vehicle Master form...")
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
                ".big-model button mat-icon, mat-dialog-container button mat-icon",
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

            # Click confirm — try multiple strategies
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
                # Last resort: JS click any swal2-confirm on the page
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
            log.info("No success alert appeared within timeout")
            return ""

    def handle_validation_warning(self, timeout=10):
        """Handle SweetAlert2 validation warning popup.
        Returns the warning message text, or ''.
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
            try:
                confirm = self.driver.find_element(
                    By.CSS_SELECTOR, ".swal2-confirm"
                )
                self.driver.execute_script(
                    "arguments[0].click();", confirm
                )
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
        Uses JS to walk up the parent chain from mat-label to mat-form-field.
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
        """Check if the Add form popup is currently visible."""
        return self.is_displayed(self.NAME_INPUT, timeout=5)

    def is_form_closed(self):
        """Check if the form popup is no longer visible."""
        return not self.is_displayed(self.NAME_INPUT, timeout=5)

    def get_form_heading(self):
        """Read the heading text of the current popup."""
        try:
            el = self.driver.find_element(
                By.CSS_SELECTOR,
                ".big-model h3, mat-dialog-container h3, "
                ".mat-mdc-dialog-title",
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
        Returns a dict with keys: name, price, vehicle_type,
        fuel_type, description.
        """
        values = {}

        try:
            values["name"] = (
                self.driver.find_element(
                    By.CSS_SELECTOR,
                    "input[name='Name'], input[formcontrolname='name']",
                ).get_attribute("value")
                or ""
            )
        except Exception:
            values["name"] = ""

        try:
            values["price"] = (
                self.driver.find_element(
                    By.CSS_SELECTOR,
                    "input[name='Vehicle Price'], "
                    "input[formcontrolname='vehiclePrice']",
                ).get_attribute("value")
                or ""
            )
        except Exception:
            values["price"] = ""

        try:
            vt = self.driver.find_element(
                By.XPATH,
                "//mat-label[contains(.,'Vehicle Type')]"
                "/ancestor::mat-form-field//mat-select",
            )
            values["vehicle_type"] = vt.text.strip()
        except Exception:
            values["vehicle_type"] = ""

        try:
            ft = self.driver.find_element(
                By.XPATH,
                "//mat-label[contains(.,'Fuel Type')]"
                "/ancestor::mat-form-field//mat-select",
            )
            values["fuel_type"] = ft.text.strip()
        except Exception:
            values["fuel_type"] = ""

        try:
            values["description"] = (
                self.driver.find_element(
                    By.CSS_SELECTOR,
                    "input[name='Description'], "
                    "textarea[formcontrolname='description']",
                ).get_attribute("value")
                or ""
            )
        except Exception:
            values["description"] = ""

        return values

    # ==============================================================
    #  Table interactions
    # ==============================================================

    def get_table_row_count(self):
        """Return the number of visible data rows in the table."""
        rows = self.driver.find_elements(
            By.CSS_SELECTOR, "table#excel-table tbody tr"
        )
        return len(rows)

    def get_all_vehicle_names(self):
        """Return a list of all vehicle names in the current table view."""
        cells = self.driver.find_elements(
            By.CSS_SELECTOR,
            "table#excel-table tbody td.cdk-column-name, "
            "table#excel-table tbody td.mat-column-name, "
            "table#excel-table tbody td:nth-child(4)",
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

    def is_vehicle_in_table(self, vehicle_name):
        """Check if a vehicle with the given name appears in the table."""
        names = self.get_all_vehicle_names()
        return any(
            vehicle_name.strip().lower() in n.lower() for n in names
        )

    def find_vehicle_row_index(self, vehicle_name):
        """Find the 0-based row index for a vehicle by name.
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
                        vehicle_name.strip().lower()
                        in cell.text.strip().lower()
                    ):
                        return i
            except StaleElementReferenceException:
                continue
        return -1

    def get_vehicle_details_from_row(self, row_index=0):
        """Read text from a table row. Returns dict with
        name, price, description.
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
        if len(data_cells) >= 2:
            result["price"] = data_cells[1].text.strip()
        if len(data_cells) >= 3:
            result["description"] = data_cells[2].text.strip()
        return result

    # ==============================================================
    #  Row action buttons — JS click via _click_action_button
    # ==============================================================

    def _click_action_button(self, vehicle_name, action_xpath_template):
        """Click a row action button (View/Edit/History) using
        parametrised XPath. Falls back to index-based button click.
        Pure JS click to avoid overlay interception.
        """
        self._force_close_panels()
        xpath = action_xpath_template.format(vehicle_name=vehicle_name)

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
        row_idx = self.find_vehicle_row_index(vehicle_name)
        if row_idx >= 0:
            return self._click_action_button_by_index(
                row_idx, action_xpath_template
            )

        log.warning(
            f"Action button not found for vehicle: {vehicle_name}"
        )
        return False

    def _click_action_button_by_index(self, row_index, action_xpath_template):
        """Fallback: click action button by row index position."""
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
        elif "cdk-column-history" in action_xpath_template:
            idx = 2
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

    def click_view_button(self, vehicle_name=None, row_index=0):
        """Click the View button for a vehicle row."""
        log.info(f"Clicking View button for: {vehicle_name or row_index}...")
        if vehicle_name:
            return self._click_action_button(
                vehicle_name, self.VIEW_BUTTON[1]
            )
        return self._click_action_button_by_index(
            row_index, self.VIEW_BUTTON[1]
        )

    def click_edit_button(self, vehicle_name=None, row_index=0):
        """Click the Edit button for a vehicle row."""
        log.info(f"Clicking Edit button for: {vehicle_name or row_index}...")
        if vehicle_name:
            return self._click_action_button(
                vehicle_name, self.EDIT_BUTTON[1]
            )
        return self._click_action_button_by_index(
            row_index, self.EDIT_BUTTON[1]
        )

    def click_history_button(self, vehicle_name=None, row_index=0):
        """Click the History button for a vehicle row."""
        log.info(
            f"Clicking History button for: {vehicle_name or row_index}..."
        )
        if vehicle_name:
            return self._click_action_button(
                vehicle_name, self.HISTORY_BUTTON[1]
            )
        return self._click_action_button_by_index(
            row_index, self.HISTORY_BUTTON[1]
        )

    # ==============================================================
    #  View & Edit specific verifications
    # ==============================================================

    def verify_view_popup_read_only(self):
        """Verify that the View popup fields are read-only / disabled.
        Returns True if all fields are non-editable.
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

        try:
            price_input = self.find_visible_element(
                self.PRICE_INPUT, timeout=5
            )
            if price_input.is_enabled():
                all_readonly = False
                log.warning("Price field is editable in View mode")
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

    def search_vehicle(self, vehicle_name):
        """Search for a vehicle by name in the table search bar.
        Returns True if the vehicle is found in the table results.
        """
        log.info(f"Searching for vehicle: {vehicle_name}")
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
                vehicle_name,
            )
            self.wait_seconds(3)

            # Check results — retry a few times for slow Angular filtering
            found = False
            for _ in range(3):
                found = self.is_vehicle_in_table(vehicle_name)
                if found:
                    break
                self.wait_seconds(2)
            if found:
                log.info(f"Vehicle found in table: {vehicle_name}")
            else:
                log.warning(f"Vehicle NOT found in table: {vehicle_name}")
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

    def verify_vehicle_exists(self, vehicle_name):
        """Navigate to page, search, and verify a vehicle exists."""
        self.navigate_to_page()
        found = self.search_vehicle(vehicle_name)
        self.clear_search()
        return found

    # ==============================================================
    #  History panel
    # ==============================================================

    def is_history_popup_open(self):
        """Check if the History popup is currently visible."""
        try:
            headings = self.driver.find_elements(
                By.CSS_SELECTOR,
                "h3.popup-title, .big-model h3, mat-dialog-container h3",
            )
            for h in headings:
                try:
                    if h.is_displayed() and "history" in h.text.lower():
                        return True
                except Exception:
                    continue
            return False
        except Exception:
            return False

    def is_history_empty(self):
        """Check if the history table has no data rows."""
        return self.get_history_row_count() == 0

    def get_history_row_count(self):
        """Return the number of rows in the history popup table."""
        rows = self.driver.find_elements(
            By.CSS_SELECTOR,
            ".big-model table tbody tr, "
            "mat-dialog-container table tbody tr",
        )
        return len(rows)

    def get_history_data(self):
        """Read all data from the history popup table.
        Returns a list of dicts, one per row.
        """
        rows = self.driver.find_elements(
            By.CSS_SELECTOR,
            ".big-model table tbody tr, "
            "mat-dialog-container table tbody tr",
        )
        data = []
        for row in rows:
            try:
                cells = row.find_elements(By.TAG_NAME, "td")
                row_data = {}
                for idx, cell in enumerate(cells):
                    row_data[f"col_{idx}"] = cell.text.strip()
                data.append(row_data)
            except StaleElementReferenceException:
                continue
        return data

    def search_in_history(self, search_text):
        """Search within the history popup. Requires Enter key press.
        Returns True if search was executed.
        """
        log.info(f"Searching in history for: {search_text}")
        try:
            # Find the search input inside the history popup
            search_inputs = self.driver.find_elements(
                By.CSS_SELECTOR,
                ".big-model input, mat-dialog-container input",
            )
            for inp in search_inputs:
                try:
                    if inp.is_displayed():
                        inp.clear()
                        inp.send_keys(search_text)
                        # History search REQUIRES Enter key
                        inp.send_keys(Keys.RETURN)
                        self.wait_seconds(1)
                        log.info("History search executed with Enter")
                        return True
                except Exception:
                    continue

            log.warning("No search input found in history panel")
            return False
        except Exception as e:
            log.error(f"History search failed: {e}")
            return False

    def close_history_popup(self):
        """Close the history popup via Cancel button, X icon, or JS force."""
        log.info("Closing history popup...")

        # Strategy 1: JS click the Cancel button in popup-footer
        try:
            self.driver.execute_script("""
                var btns = document.querySelectorAll(
                    '.popup-footer button'
                );
                for (var i = 0; i < btns.length; i++) {
                    if (btns[i].textContent.includes('Cancel') ||
                        btns[i].textContent.includes('Close')) {
                        btns[i].click();
                        break;
                    }
                }
            """)
            self.wait_seconds(1)
            if not self.is_history_popup_open():
                log.info("History popup closed via Cancel button (JS)")
                return
        except Exception:
            pass

        # Strategy 2: JS click the X icon in popup-header
        try:
            self.driver.execute_script("""
                var icons = document.querySelectorAll(
                    '.popup-header button mat-icon'
                );
                for (var i = 0; i < icons.length; i++) {
                    if (icons[i].textContent.trim().toLowerCase() === 'close') {
                        icons[i].closest('button').click();
                        break;
                    }
                }
            """)
            self.wait_seconds(1)
            if not self.is_history_popup_open():
                log.info("History popup closed via X icon (JS)")
                return
        except Exception:
            pass

        # Strategy 3: JS force remove all popup containers + overlays
        try:
            self.driver.execute_script("""
                document.querySelectorAll('.cdk-overlay-pane').forEach(function(el) { el.remove(); });
                document.querySelectorAll('.cdk-overlay-backdrop').forEach(function(el) { el.remove(); });
            """)
            self.wait_seconds(0.5)
        except Exception:
            pass

        if self.is_history_popup_open():
            log.warning("Could not close history popup")
        else:
            log.info("History popup closed")

        if self.is_history_popup_open():
            log.warning("Could not close history popup")
        else:
            log.info("History popup closed")

    # ==============================================================
    #  Dropdown helpers — dynamic option reading (NEVER hardcode)
    # ==============================================================

    def _select_mat_option(self, select_locator, option_text):
        """Open a mat-select dropdown and select a specific option by text.
        Handles internal search textbox if present.
        """
        log.info(f"Selecting '{option_text}' from dropdown...")

        # Click the mat-select trigger
        try:
            self.click(select_locator)
        except Exception:
            # Fallback: click the trigger div directly
            trigger_xpath = (
                f"{select_locator[1]}"
                f"//div[contains(@class,'mat-mdc-select-trigger')]"
            )
            self.driver.find_element(By.XPATH, trigger_xpath).click()
        self.wait_seconds(0.5)

        # If dropdown has a search textbox, type into it
        try:
            search_inputs = self.driver.find_elements(
                By.CSS_SELECTOR,
                "div[role='listbox'] input, "
                ".cdk-overlay-pane input[placeholder]",
            )
            for inp in search_inputs:
                try:
                    if inp.is_displayed():
                        inp.clear()
                        inp.send_keys(option_text)
                        self.wait_seconds(0.5)
                        break
                except Exception:
                    continue
        except Exception:
            pass

        # Click the matching option
        try:
            opt_locator = (
                "xpath",
                f"//div[@role='listbox']//mat-option"
                f"[contains(.,'{option_text}')]",
            )
            self.click_with_retry(opt_locator)
        except Exception:
            # Try role='option' fallback
            try:
                opt_locator2 = (
                    "xpath",
                    f"//div[@role='listbox']//div[@role='option']"
                    f"[contains(.,'{option_text}')]",
                )
                self.click_with_retry(opt_locator2)
            except Exception:
                # Last resort: scroll and JS click
                opts = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    "div[role='listbox'] mat-option, "
                    "div[role='listbox'] [role='option']",
                )
                for opt in opts:
                    try:
                        if option_text in opt.text:
                            self.driver.execute_script(
                                "arguments[0].scrollIntoView({block:'center'});"
                                "arguments[0].click();",
                                opt,
                            )
                            break
                    except Exception:
                        continue

        self.wait_seconds(0.3)
        self._force_close_panels()
        log.info(f"Selected '{option_text}'")

    def _select_random_from_dropdown(
        self, select_locator, label_name, exclude=None
    ):
        """Open a mat-select dropdown and pick a random option.
        Returns the selected option text.
        Never hardcodes options — reads from live UI.
        """
        log.info(f"Selecting random option from '{label_name}'...")

        # Click the mat-select trigger
        try:
            self.click(select_locator)
        except Exception:
            trigger_xpath = (
                f"{select_locator[1]}"
                f"//div[contains(@class,'mat-mdc-select-trigger')]"
            )
            try:
                self.driver.find_element(By.XPATH, trigger_xpath).click()
            except Exception:
                # JS click on the mat-select element itself
                el = self.driver.find_element(
                    By.XPATH, select_locator[1]
                )
                self.driver.execute_script("arguments[0].click();", el)
        self.wait_seconds(0.5)

        # Wait for options to appear
        try:
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located(
                    (
                        By.CSS_SELECTOR,
                        "div[role='listbox'] mat-option, "
                        "div[role='listbox'] [role='option']",
                    )
                )
            )
        except TimeoutException:
            raise Exception(
                f"No options loaded in '{label_name}' dropdown"
            )

        # Read all option texts
        options = self.driver.find_elements(
            By.CSS_SELECTOR,
            "div[role='listbox'] mat-option, "
            "div[role='listbox'] [role='option']",
        )
        option_texts = []
        for opt in options:
            try:
                t = opt.text.strip()
                if t and t != "No results found" and not t.startswith("Select"):
                    option_texts.append(t)
            except Exception:
                continue

        if not option_texts:
            raise Exception(
                f"No valid options found in '{label_name}' dropdown"
            )

        # Exclude specific options if requested
        if exclude:
            option_texts = [t for t in option_texts if t not in exclude]
            if not option_texts:
                raise Exception(
                    f"No remaining options in '{label_name}' "
                    f"after excluding {exclude}"
                )

        # Pick a random option
        selected = random.choice(option_texts)
        log.info(f"Random '{label_name}' selected: '{selected}'")

        # Click the chosen option
        for opt in options:
            try:
                if opt.text.strip() == selected:
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView({block:'center'});"
                        "arguments[0].click();",
                        opt,
                    )
                    break
            except Exception:
                continue

        self.wait_seconds(0.3)
        self._force_close_panels()
        return selected

    def get_dropdown_options(self, select_locator):
        """Open a dropdown, read all option texts, then close it."""
        log.info("Reading dropdown options...")

        # Close any leftover overlay panels first
        self._close_select_panel()
        self.wait_seconds(0.3)

        # Click the mat-select trigger
        try:
            self.click(select_locator)
        except Exception:
            trigger_xpath = (
                f"{select_locator[1]}"
                f"//div[contains(@class,'mat-mdc-select-trigger')]"
            )
            try:
                self.driver.find_element(By.XPATH, trigger_xpath).click()
            except Exception:
                el = self.driver.find_element(
                    By.XPATH, select_locator[1]
                )
                self.driver.execute_script("arguments[0].click();", el)
        self.wait_seconds(0.5)

        # Wait for the VISIBLE dropdown panel to appear with options
        try:
            WebDriverWait(self.driver, 8).until(
                EC.visibility_of_element_located(
                    (
                        By.CSS_SELECTOR,
                        "div.mat-mdc-select-panel mat-option",
                    )
                )
            )
            self.wait_seconds(0.3)
        except TimeoutException:
            log.warning("Timed out waiting for dropdown options to become visible")

        # Read only VISIBLE options
        options = self.driver.find_elements(
            By.CSS_SELECTOR,
            "div.mat-mdc-select-panel mat-option",
        )
        option_texts = []
        for opt in options:
            try:
                if not opt.is_displayed():
                    continue
                t = opt.text.strip()
                if t and t != "No results found":
                    option_texts.append(t)
            except Exception:
                continue

        # Close the dropdown
        self._close_select_panel()
        log.info(f"Dropdown options: {option_texts}")
        return option_texts
    # ==============================================================
    #  Force close form popup (cleanup)
    # ==============================================================

    def force_close_form_popup(self):
        """Force close any open form popup via JS.
        Use as last resort when Cancel/Close buttons don't work.
        """
        log.info("Force closing form popup via JS...")
        self.driver.execute_script("""
            document.querySelectorAll(
                'mat-dialog-container'
            ).forEach(function(el) { el.remove(); });
            document.querySelectorAll(
                '.cdk-overlay-backdrop'
            ).forEach(function(el) { el.remove(); });
            document.querySelectorAll(
                '.cdk-overlay-pane'
            ).forEach(function(el) { el.remove(); });
        """)
        self.wait_seconds(0.5)

    # ==============================================================
    #  One-call convenience methods
    # ==============================================================

    def create_vehicle(self, vehicle_data):
        """One-call vehicle creation.
        Returns result dict: status, error, message, data.
        """
        name = vehicle_data.get("name", "N/A")
        log.info(f"Creating vehicle: {name}")
        result = {
            "status": "FAILED",
            "error": "",
            "message": "",
            "data": copy.deepcopy(vehicle_data),
        }

        try:
            self.open_add_form()
            if not self.is_add_form_open():
                raise Exception("Add form did not open")

            self.fill_vehicle_form(vehicle_data)
            self.submit()

            msg = self.handle_success_alert(timeout=60)
            if msg:
                result["message"] = msg
                result["status"] = "PASSED"
            else:
                self.wait_seconds(3)
                if self.is_form_closed():
                    result["message"] = "Form closed (assumed success)"
                    result["status"] = "PASSED"
                else:
                    errors = self.get_mat_error_text()
                    if errors:
                        result["error"] = f"Validation errors: {errors}"
                    else:
                        result["error"] = (
                            "No success message and dialog did not close"
                        )
        except Exception as e:
            result["error"] = str(e)
            log.error(f"Failed to create vehicle '{name}': {e}")

        # Always clean up: remove any leftover overlays/swals
        try:
            self.driver.execute_script("""
                document.querySelectorAll('.swal2-container').forEach(function(el) { el.remove(); });
                document.querySelectorAll('.cdk-overlay-backdrop').forEach(function(el) { el.remove(); });
            """)
        except Exception:
            pass

        VM_SUBMISSIONS.append(result)
        return result

    def edit_vehicle(self, vehicle_name, updated_data, row_index=0):
        """One-call vehicle edit. Clicks Edit, fills changed fields,
        clicks Update.
        Returns result dict: status, error, message.
        """
        log.info(f"Editing vehicle: {vehicle_name}")
        result = {"status": "FAILED", "error": "", "message": ""}

        try:
            # First try to find the vehicle directly
            if not self.is_vehicle_in_table(vehicle_name):
                # Search for it — might be on another page
                self.search_vehicle(vehicle_name)
                self.wait_seconds(1)

            self.click_edit_button(
                vehicle_name=vehicle_name, row_index=row_index
            )
            self.wait_seconds(1)

            if not self.is_edit_mode():
                raise Exception("Edit form did not open (no Update button)")

            # Fill only provided fields
            if updated_data.get("name"):
                self.type_text(
                    self.NAME_INPUT, str(updated_data["name"]),
                    clear_first=True,
                )
            if updated_data.get("price"):
                self.type_text(
                    self.PRICE_INPUT, str(updated_data["price"]),
                    clear_first=True,
                )
            if updated_data.get("vehicle_type"):
                self._select_mat_option(
                    self.VEHICLE_TYPE_SELECT,
                    str(updated_data["vehicle_type"]),
                )
            if updated_data.get("fuel_type"):
                self._select_mat_option(
                    self.FUEL_TYPE_SELECT,
                    str(updated_data["fuel_type"]),
                )
            if updated_data.get("description"):
                self.type_text(
                    self.DESCRIPTION_INPUT,
                    str(updated_data["description"]),
                    clear_first=True,
                )

            self._force_close_panels()
            self.click_update()

            msg = self.handle_success_alert(timeout=60)
            if msg:
                result["message"] = msg
                result["status"] = "PASSED"
            else:
                self.wait_seconds(3)
                if self.is_form_closed():
                    result["message"] = "Form closed (assumed success)"
                    result["status"] = "PASSED"
                else:
                    result["error"] = "No success message after edit"
        except Exception as e:
            result["error"] = str(e)
            log.error(f"Failed to edit vehicle '{vehicle_name}': {e}")

        VM_SUBMISSIONS.append(result)
        return result

    def view_vehicle(self, vehicle_name=None, row_index=0):
        """One-call vehicle view. Clicks View, reads fields,
        closes popup. Returns dict of field values.
        """
        log.info(f"Viewing vehicle: {vehicle_name or row_index}")
        try:
            self.click_view_button(
                vehicle_name=vehicle_name, row_index=row_index
            )
            self.wait_seconds(1)
            values = self.get_form_field_values()
            log.info(f"Vehicle details: {values}")
            self.close_popup()
            self.wait_seconds(0.5)
            return values
        except Exception as e:
            log.error(f"Failed to view vehicle: {e}")
            return None

    def check_history(self, vehicle_name=None, row_index=0,
                      search_text=None):
        """One-call history check. Opens History, reads row count,
        optionally searches, then closes popup.
        """
        log.info(f"Checking history for: {vehicle_name or row_index}")
        result = {
            "row_count": 0,
            "search_found": None,
            "data": [],
            "error": "",
        }

        try:
            # First try to find the vehicle directly
            if vehicle_name and not self.is_vehicle_in_table(vehicle_name):
                self.search_vehicle(vehicle_name)
                self.wait_seconds(1)

            self.click_history_button(
                vehicle_name=vehicle_name, row_index=row_index
            )
            self.wait_seconds(1.5)

            result["row_count"] = self.get_history_row_count()
            result["data"] = self.get_history_data()

            if search_text:
                result["search_found"] = self.search_in_history(
                    search_text
                )

            self.close_history_popup()
            self.wait_seconds(0.5)

        except Exception as e:
            result["error"] = str(e)

        return result

    # ==============================================================
    #  Bulk creation
    # ==============================================================

    def create_bulk_vehicles(self, vehicles_list, on_progress=None):
        """Create multiple vehicles in sequence.
        Returns list of result dicts.
        """
        total = len(vehicles_list)
        results = []

        for i, vdata in enumerate(vehicles_list, 1):
            name = vdata.get("name", f"Vehicle_{i}")
            log.info(f"[{i}/{total}] Creating: {name}")
            start_time = time.time()
            result = self.create_vehicle(vdata)
            elapsed = time.time() - start_time
            result["index"] = i
            result["duration"] = round(elapsed, 1)
            results.append(result)

            # Cleanup between creations
            try:
                self.force_close_form_popup()
                self.click_refresh()
                self.wait_seconds(2)
            except Exception:
                try:
                    self.navigate_to_page()
                    self.wait_seconds(2)
                except Exception:
                    pass

            if on_progress:
                on_progress(i, total, name)

        passed = sum(1 for r in results if r["status"] == "PASSED")
        failed = sum(1 for r in results if r["status"] == "FAILED")
        log.separator()
        log.info(
            f" BULK COMPLETE: {passed}/{total} passed, {failed} failed"
        )
        log.separator()
        return results