"""
supplier_page.py
----------------
Page Object Model for RhythmERP Supplier Screen (3-Step Stepper Form).

Location: Dynamic Screens > Supplier
URL:      /#/dynamic-screens/Supplier/Supplier

FORM LAYOUT (3-STEP STEPPER — verified 2026-05-22 on live app):

  STEP 1 — Additional Details (INCLUDES Universal fields at top + Additional sub-section below):
    Universal Fields (visible immediately):
      - Party Reference         (mat-select, optional, default placeholder)
      - Ownership Status        (mat-select, required)
      - Company Name            (text input, required, maxlength=255)
      - PO Type                 (mat-select, required)
      - Email                   (text input, optional, maxlength=255, NO format validation)
      - Phone Number            (number input, required, no maxlength, has spinner BUG-003)
      - Default Currency        (mat-select, required)
      - PAN Number              (text input, required, maxlength=255, NO format validation BUG-004)
      - Is MSME Registered?     (toggle switch, default=No)
      - Status                  (toggle switch, default=Active)

    Additional Details (must SCROLL DOWN within Step 1):
      - Is GST Set Off          (toggle switch, default=Yes)
      - Is TDS Applicable       (toggle switch, default=No)
      - Contact Person Name     (text input, optional, maxlength=255)
      - Office Number           (text input, optional, maxlength=255)
      - Payment Terms           (mat-select, optional)
      - Delivery Terms          (mat-select, optional)
      - Mode Of Delivery        (mat-select, optional)

  STEP 2 — Address Details (dynamic rows — add/remove):
    Per row:
      - Address Type            (mat-select, required) — Shipping/Billing
      - Country                 (mat-select, required) — cascading first
      - State                   (mat-select, required, depends on Country)
      - District                (mat-select, required, depends on State)
      - Taluka                  (mat-select, required, depends on District)
      - Village                 (mat-select, optional, depends on Taluka)
      - Address                 (text input, required, maxlength=255)
      - Pin Code                (text input, optional, maxlength=255)
      - GSTIN                   (text input, optional, maxlength=255)
      - Remove row button

  STEP 3 — Bank Details (dynamic rows — add/remove):
    Per row:
      - Bank Name               (text input, optional, maxlength=255)
      - Branch                  (text input, optional, maxlength=255)
      - IFSC Code               (text input, optional, maxlength=255)
      - Account Type            (mat-select, optional) — Current/Saving
      - Account Holder Name     (text input, optional, maxlength=255)
      - Account Number          (text input, optional, maxlength=255)
      - Bank Proof              (mat-select, required) — Cancelled Cheque/Passbook
      - Attachment              (file upload, optional) — .png/.jpg/.pdf
      - Remove row button

KEY RULES (V2 — updated 2026-06-06):
  - NEVER use Keys.ESCAPE (use backdrop click + JS overlay removal)
  - JS clicks for Angular Material overlays
  - Dropdown options read dynamically at runtime (never hardcode)
  - STEPPER form: Next/Back buttons navigate between steps
  - Step 1 has scrollable content — Additional Details below the fold
  - Address and Bank steps support ADD ROW / REMOVE ROW
  - **CRITICAL: ERP requires BOTH Shipping AND Billing address rows for Suppliers.
    A single address row (any type) will be rejected with 400:
      "Shipping address is required for Supplier roles"
      "Billing address is required for Supplier roles"
    create_supplier() now adds 2 address rows by default.**
  - fill_step2_address() uses row-scoped locators for row_index > 0
    so the correct Nth address row is targeted (not always the first).
  - Cascading dropdowns MUST be filled in order: Country → State → District → Taluka → Village
  - Party Reference is optional, has dynamic farmer list
  - BUG-001: Company Name accepts special characters
  - BUG-002: No email format validation
  - BUG-003: Phone Number has spinner controls (type=number)
  - BUG-004: No PAN format validation
  - BUG-005: No Update button in Edit mode — only Cancel visible
  - NO History button on Supplier screen
  - CRITICAL: Browser-clicked mat-select options do NOT update Angular reactive
    form model. Must use JS value-setter + dispatchEvent for all dropdown
    selections.

TABLE COLUMNS (main listing):
  - View / Edit  (action buttons per row — NO History button)
  - Name (Company Name)
  - Phone Number (mobile_no)
  - Status

LOGIN: Assistant@mail.com / Vedant@12345 / Facility: RuralLife Producer Company (index 0)
"""

import os
import sys
import time
import random

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
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
SP_SUBMISSIONS = []


class SupplierPage(BasePage):
    PAGE_URL = f"{RHYTHMERP_BASE_URL}/#/dynamic-screens/Supplier/Supplier"

    # ==============================================================
    #  LOCATORS — Toolbar
    # ==============================================================
    ADD_BUTTON = ("css", "button.erp-add-btn")
    SEARCH_TOGGLE = ("css", "button.search-btn, button[mattooltip='Search']")
    SEARCH_INPUT = ("css", "#erpSearchInput, input.erp-search-input")
    REFRESH_BUTTON = ("css", "button[mattooltip='Refresh']")
    FILTER_BUTTON = ("css", "button.erp-outline-btn")

    # ==============================================================
    #  LOCATORS — Table (main listing)
    # ==============================================================
    TABLE = ("css", "table#excel-table, table.mat-mdc-table, table[mat-table]")
    TABLE_ROWS = ("css", "table#excel-table tbody tr, table.mat-mdc-table tbody tr.mat-mdc-row")
    TABLE_NAME_CELLS = (
        "css",
        "td.cdk-column-name, td.mat-column-name",
    )
    TABLE_PHONE_CELLS = (
        "css",
        "td.cdk-column-mobile_no, td.mat-column-mobile_no",
    )
    TABLE_STATUS_CELLS = (
        "css",
        "td.cdk-column-status, td.mat-column-status",
    )
    NO_DATA_ROW = (
        "css",
        "table#excel-table tbody tr td.no-data, "
        "table.mat-mdc-table tbody tr.mat-mdc-no-data-row, "
        "table.mat-mdc-table tbody tr td.no-data",
    )

    # ==============================================================
    #  LOCATORS — Row action buttons (3-dot menu)
    # ==============================================================
    ROW_MENU_TRIGGER = (
        "css",
        "button.mat-mdc-menu-trigger.erp-row-trigger",
    )
    ROW_MENU_VIEW = (
        "xpath",
        "//div[contains(@class,'mat-mdc-menu-content')]"
        "//button[.//i[contains(@class,'material-icons') and text()='visibility']]"
        "| //div[contains(@class,'mat-mdc-menu-content')]"
        "//span[contains(@class,'erp-menu-title') and text()='View']"
        "/ancestor::button",
    )
    ROW_MENU_EDIT = (
        "xpath",
        "//div[contains(@class,'mat-mdc-menu-content')]"
        "//button[.//i[contains(@class,'material-icons') and text()='edit']]"
        "| //div[contains(@class,'mat-mdc-menu-content')]"
        "//span[contains(@class,'erp-menu-title') and text()='Edit']"
        "/ancestor::button",
    )
    ROW_MENU_HISTORY = (
        "xpath",
        "//div[contains(@class,'mat-mdc-menu-content')]"
        "//button[.//i[contains(@class,'material-icons') and text()='history']]"
        "| //div[contains(@class,'mat-mdc-menu-content')]"
        "//span[contains(@class,'erp-menu-title') and text()='History']"
        "/ancestor::button",
    )

    # ==============================================================
    #  LOCATORS — Form popup (STEPPER popup)
    # ==============================================================
    FORM_POPUP = (
        "css",
        ".big-model, .edit_pop_up, mat-dialog-container, "
        "div.cdk-overlay-container div.popup-wrapper",
    )
    FORM_HEADING = ("css", ".big-model h3, .edit_pop_up h3, mat-dialog-container h3")

    # ==============================================================
    #  LOCATORS — Mat Stepper
    # ==============================================================
    MAT_STEPPER = ("css", "mat-stepper, mat-horizontal-stepper")
    STEP_HEADERS = ("css", "mat-step-header, .mat-step-header")
    STEP_HEADER_1 = ("css", "mat-step-header:nth-of-type(1)")
    STEP_HEADER_2 = ("css", "mat-step-header:nth-of-type(2)")
    STEP_HEADER_3 = ("css", "mat-step-header:nth-of-type(3)")

    # ==============================================================
    #  LOCATORS — Step 1: Universal Fields
    # ==============================================================
    PARTY_REFERENCE_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Party Reference')]"
        "/ancestor::mat-form-field//mat-select",
    )
    OWNERSHIP_STATUS_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Ownership Status')]"
        "/ancestor::mat-form-field//mat-select",
    )
    COMPANY_NAME_INPUT = ("css", "input[name='Company Name']")
    PO_TYPE_SELECT = (
        "xpath",
        "//mat-label[contains(.,'PO Type')]"
        "/ancestor::mat-form-field//mat-select",
    )
    EMAIL_INPUT = ("css", "input[name='Email']")
    PHONE_NUMBER_INPUT = ("css", "input[name='Phone Number']")
    DEFAULT_CURRENCY_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Default Currency')]"
        "/ancestor::mat-form-field//mat-select",
    )
    PAN_NUMBER_INPUT = ("css", "input[name='PAN Number']")

    # ==============================================================
    #  LOCATORS — Step 1: Toggle Switches (Universal)
    # ==============================================================
    IS_MSME_TOGGLE = (
        "xpath",
        "//app-slide-toggle-v2[.//span[contains(.,'Is MSME Registered')]]"
        "//div[contains(@class,'switch-wrapper')]",
    )
    STATUS_TOGGLE = (
        "xpath",
        "//app-slide-toggle-v2[.//span[contains(.,'Status')]]"
        "//div[contains(@class,'switch-wrapper')]",
    )

    # ==============================================================
    #  LOCATORS — Step 1: Additional Details (scroll down)
    # ==============================================================
    IS_GST_SET_OFF_TOGGLE = (
        "xpath",
        "//app-slide-toggle-v2[.//span[contains(.,'Is GST Set Off')]]"
        "//div[contains(@class,'switch-wrapper')]",
    )
    IS_TDS_APPLICABLE_TOGGLE = (
        "xpath",
        "//app-slide-toggle-v2[.//span[contains(.,'Is TDS Applicable')]]"
        "//div[contains(@class,'switch-wrapper')]",
    )
    CONTACT_PERSON_INPUT = ("css", "input[name='Contact Person Name']")
    OFFICE_NUMBER_INPUT = ("css", "input[name='Office Number']")
    PAYMENT_TERMS_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Payment Terms')]"
        "/ancestor::mat-form-field//mat-select",
    )
    DELIVERY_TERMS_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Delivery Terms')]"
        "/ancestor::mat-form-field//mat-select",
    )
    MODE_OF_DELIVERY_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Mode Of Delivery')]"
        "/ancestor::mat-form-field//mat-select",
    )

    # ==============================================================
    #  LOCATORS — Step 2: Address Details
    # ==============================================================
    # These are within the address row container — use index-based locators
    ADDRESS_TYPE_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Address Type')]"
        "/ancestor::mat-form-field//mat-select",
    )
    COUNTRY_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Country')]"
        "/ancestor::mat-form-field//mat-select",
    )
    STATE_SELECT = (
        "xpath",
        "//mat-label[contains(.,'State')]"
        "/ancestor::mat-form-field//mat-select",
    )
    DISTRICT_SELECT = (
        "xpath",
        "//mat-label[contains(.,'District')]"
        "/ancestor::mat-form-field//mat-select",
    )
    TALUKA_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Taluka')]"
        "/ancestor::mat-form-field//mat-select",
    )
    VILLAGE_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Village')]"
        "/ancestor::mat-form-field//mat-select",
    )
    ADDRESS_INPUT = ("css", "input[name='Address']")
    PIN_CODE_INPUT = ("css", "input[name='Pin Code']")
    GSTIN_INPUT = ("css", "input[name='GSTIN']")
    ADD_ADDRESS_ROW_BUTTON = (
        "xpath",
        "//mat-step-content[2]//button[.//mat-icon[text()='add']]"
        " | //mat-step-content[2]//button[contains(@class,'add-row')]"
    )
    REMOVE_ADDRESS_ROW_BUTTON = (
        "xpath",
        "//mat-step-content[2]//button[.//mat-icon[text()='delete' or text()='remove' or text()='close']]"
    )

    # ==============================================================
    #  LOCATORS — Step 3: Bank Details
    # ==============================================================
    BANK_NAME_INPUT = ("css", "input[name='Bank Name']")
    BRANCH_INPUT = ("css", "input[name='Branch']")
    IFSC_CODE_INPUT = ("css", "input[name='IFSC Code']")
    ACCOUNT_TYPE_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Account Type')]"
        "/ancestor::mat-form-field//mat-select",
    )
    ACCOUNT_HOLDER_NAME_INPUT = ("css", "input[name='Account Holder Name']")
    ACCOUNT_NUMBER_INPUT = ("css", "input[name='Account Number']")
    BANK_PROOF_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Bank Proof')]"
        "/ancestor::mat-form-field//mat-select",
    )
    ATTACHMENT_INPUT = ("css", "input[type='file'][accept='.png, .jpg, .pdf'], input[type='file']")
    ADD_BANK_ROW_BUTTON = (
        "xpath",
        "//mat-step-content[3]//button[.//mat-icon[text()='add']]"
        " | //mat-step-content[3]//button[contains(@class,'add-row')]"
    )
    REMOVE_BANK_ROW_BUTTON = (
        "xpath",
        "//mat-step-content[3]//button[.//mat-icon[text()='delete' or text()='remove' or text()='close']]"
    )

    # ==============================================================
    #  LOCATORS — Stepper navigation buttons
    # ==============================================================
    NEXT_BUTTON = ("css", "button.mat-stepper-next, button[contains(@class,'mat-stepper-next')]")
    BACK_BUTTON = ("css", "button.mat-stepper-previous, button[contains(@class,'mat-stepper-previous')]")

    # ==============================================================
    #  LOCATORS — Form buttons (Submit/Cancel/Update)
    # ==============================================================
    SUBMIT_BUTTON = (
        "xpath",
        "//div[contains(@class,'popup-footer')]//button[contains(.,'Submit')]",
    )
    UPDATE_BUTTON = (
        "xpath",
        "//div[contains(@class,'popup-footer')]//button[contains(.,'Update')]",
    )
    CANCEL_BUTTON = (
        "xpath",
        "//div[contains(@class,'popup-footer')]//button[contains(.,'Cancel')]",
    )

    # ==============================================================
    #  LOCATORS — Popup actions
    # ==============================================================
    FULLSCREEN_BUTTON = (
        "xpath",
        "//div[contains(@class,'popup-actions')]/button[1]",
    )
    CLOSE_BUTTON = (
        "xpath",
        "//div[contains(@class,'popup-actions')]/button[last()]",
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
    NG_INVALID_FIELDS = ("css", ".ng-invalid")

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
    #  LOCATORS — Pagination
    # ==============================================================
    ITEMS_PER_PAGE = ("css", "mat-select.mat-mdc-paginator-page-size-select")
    NEXT_PAGE = ("css", "button.mat-mdc-paginator-navigation-next")
    PREV_PAGE = ("css", "button.mat-mdc-paginator-navigation-previous")

    # ==============================================================
    #  Navigation & page load
    # ==============================================================

    def navigate_to_page(self):
        """Navigate to the Supplier Screen listing page.
        Force-refreshes to clear leftover Angular state from previous tests.
        """
        log.info("Navigating to Supplier Screen page...")
        self.navigate_to(self.PAGE_URL)
        self.driver.refresh()
        self._wait_for_page_ready()

    def _wait_for_page_ready(self):
        """Wait until the Supplier Screen page is fully loaded:
        1. Table renders (or no-data row)
        2. Toolbar buttons (including ADD) are clickable
        """
        try:
            WebDriverWait(self.driver, EXPLICIT_WAIT).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR,
                     "table#excel-table, table.mat-mdc-table, table[mat-table]")
                )
            )
            log.info("Supplier table loaded")
        except TimeoutException:
            log.warning("Supplier table not found, page may be empty")

        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "ul.tbl-export-btn, button.erp-add-btn")
                )
            )
            self.wait_seconds(1)
            log.info("Supplier toolbar ready")
        except TimeoutException:
            log.warning("Toolbar not found, ADD button may be delayed")
            self.wait_seconds(3)

    def is_page_loaded(self):
        """Check if the Supplier listing page has loaded."""
        return self.is_displayed(self.TABLE, timeout=10)

    # ==============================================================
    #  Overlay cleanup — NEVER use Keys.ESCAPE
    # ==============================================================

    def _force_close_panels(self):
        """Remove ALL select overlay panes from the DOM via JS.
        Keeps dialog backdrop intact so form popups stay open.
        """
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

    def _close_dropdown_panel_only(self):
        """Close an open mat-select dropdown panel WITHOUT sending ESC."""
        self._close_select_panel()

    # ==============================================================
    #  Toolbar actions
    # ==============================================================

    def open_add_form(self):
        """Click the ADD (+) button to open the stepper form popup.
        Uses multiple strategies with proper waits.
        """
        log.info("Clicking ADD button...")
        self._wait_for_toolbar()

        # Strategy 1: button.erp-add-btn
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
                    self._wait_for_form_content(timeout=5)
                    log.info("ADD form opened via erp-add-btn")
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

        # Strategy 3: BasePage click_with_retry
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
        """Wait for the toolbar and ADD button to be present and visible."""
        for attempt in range(3):
            try:
                add_container = self.driver.find_elements(
                    By.CSS_SELECTOR, "button.erp-add-btn"
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
        """Quick check if any form popup is visible."""
        try:
            popups = self.driver.find_elements(
                By.CSS_SELECTOR,
                "div.big-model, mat-dialog-container, "
                "div.edit_pop_up.override_edit_pop_up.popup-mode, "
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

    def is_add_form_open(self):
        """Public alias for _is_form_popup_open."""
        return self._is_form_popup_open()

    def _wait_for_form_content(self, timeout=5):
        """Wait for form content (inputs) to render inside the popup."""
        import time as _time
        deadline = _time.time() + timeout
        while _time.time() < deadline:
            try:
                elements = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    "div.big-model input, "
                    "mat-dialog-container input, "
                    ".edit_pop_up input, "
                    "div.cdk-overlay-container input"
                )
                for el in elements:
                    try:
                        if el.is_displayed():
                            return True
                    except Exception:
                        continue
            except Exception:
                pass
            self.wait_seconds(0.5)

        log.warning(f"Form content did not render within {timeout}s")
        self._debug_popup_info()
        return False

    def _debug_popup_info(self):
        """Log debug information about the current popup state."""
        try:
            all_inputs = self.driver.find_elements(
                By.CSS_SELECTOR,
                "div.big-model input, "
                "mat-dialog-container input, "
                ".edit_pop_up input, "
                "div.cdk-overlay-container input"
            )
            log.info(f"DEBUG: Found {len(all_inputs)} inputs in popup")
            for i, inp in enumerate(all_inputs[:15]):
                try:
                    log.info(
                        f"  Input[{i}]: "
                        f"name={inp.get_attribute('name')}, "
                        f"formcontrolname={inp.get_attribute('formcontrolname')}, "
                        f"type={inp.get_attribute('type')}, "
                        f"placeholder={inp.get_attribute('placeholder')}, "
                        f"visible={inp.is_displayed()}"
                    )
                except Exception:
                    pass
        except Exception as e:
            log.warning(f"Debug popup info failed: {e}")

    def click_refresh(self):
        """Click the Refresh button."""
        log.info("Clicking Refresh button...")
        try:
            btns = self.driver.find_elements(
                By.CSS_SELECTOR, "button[mattooltip='Refresh']"
            )
            for btn in btns:
                try:
                    if btn.is_displayed():
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({block:'center'});"
                            "arguments[0].click();",
                            btn,
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
    #  Dropdown helper — JS value-setter for Angular form sync
    # ==============================================================

    def _select_mat_option(self, select_locator, value=None):
        """Select an option from a mat-select dropdown.
        Uses JS value-setter + dispatchEvent to ensure Angular reactive
        form model stays in sync.

        If value is None, picks a random non-empty, non-placeholder option
        from the live UI.
        Returns the selected option text, or None on failure.
        """
        self._force_close_panels()

        # Find and click the mat-select trigger
        select_el = self.find_visible_element(select_locator)
        if not select_el:
            log.warning(f"mat-select not found: {select_locator}")
            return None

        self.driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});"
            "arguments[0].click();",
            select_el,
        )
        self.wait_seconds(1)

        # Wait for dropdown panel to appear
        try:
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "div[role='listbox'] mat-option")
                )
            )
        except TimeoutException:
            log.warning("Dropdown options did not appear")
            self._close_dropdown_panel_only()
            return None

        # Get all options
        options = self.driver.find_elements(
            By.CSS_SELECTOR, "div[role='listbox'] mat-option"
        )
        if not options:
            log.warning("No options found in dropdown")
            self._close_dropdown_panel_only()
            return None

        # Pick option
        selected_option = None
        selected_text = None

        if value:
            # Find matching option by text
            for opt in options:
                try:
                    opt_text = opt.text.strip()
                    if opt_text.lower() == value.lower():
                        selected_option = opt
                        selected_text = opt_text
                        break
                except Exception:
                    continue

            if not selected_option:
                # Partial match
                for opt in options:
                    try:
                        opt_text = opt.text.strip()
                        if value.lower() in opt_text.lower():
                            selected_option = opt
                            selected_text = opt_text
                            break
                    except Exception:
                        continue

        if not selected_option:
            # Pick a random non-empty, non-placeholder option
            valid_options = []
            for opt in options:
                try:
                    opt_text = opt.text.strip()
                    # Skip placeholder/empty options like "Select Party Reference"
                    if opt_text and not opt_text.lower().startswith("select "):
                        valid_options.append((opt, opt_text))
                except Exception:
                    continue

            if not valid_options:
                # If all start with "Select", just pick any non-empty
                for opt in options:
                    try:
                        opt_text = opt.text.strip()
                        if opt_text:
                            valid_options.append((opt, opt_text))
                    except Exception:
                        continue

            if valid_options:
                selected_option, selected_text = random.choice(valid_options)
            else:
                log.warning("No valid options to select")
                self._close_dropdown_panel_only()
                return None

        # Click the option via JS
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});"
            "arguments[0].click();",
            selected_option,
        )
        self.wait_seconds(0.5)

        # Close any remaining dropdown panel
        self._close_dropdown_panel_only()

        # CRITICAL: Sync Angular reactive form model
        self._sync_dropdown_angular_model(select_el)

        log.info(f"Selected dropdown option: {selected_text}")
        return selected_text

    def _sync_dropdown_angular_model(self, select_el):
        """Force Angular reactive form to recognize the dropdown selection.
        Dispatches focus/change/blur events and marks the field as touched/valid.
        """
        try:
            self.driver.execute_script("""
                var select = arguments[0];
                if (!select) return 'no element';

                // Dispatch Angular Material events
                select.dispatchEvent(new Event('focusin', { bubbles: true }));
                select.dispatchEvent(new KeyboardEvent('keydown', {
                    key: 'Enter', code: 'Enter', keyCode: 13, bubbles: true
                }));
                select.dispatchEvent(new Event('change', { bubbles: true }));
                select.dispatchEvent(new Event('input', { bubbles: true }));
                select.dispatchEvent(new KeyboardEvent('keyup', {
                    key: 'Enter', code: 'Enter', keyCode: 13, bubbles: true
                }));
                select.dispatchEvent(new Event('focusout', { bubbles: true }));
                select.dispatchEvent(new Event('blur', { bubbles: true }));

                // Mark as touched and valid
                select.classList.remove('ng-untouched');
                select.classList.add('ng-touched');
                select.classList.remove('ng-pristine');
                select.classList.add('ng-dirty');

                // Check if value text is showing
                var valueText = select.querySelector('.mat-mdc-select-value-text');
                var hasValue = valueText && valueText.textContent.trim().length > 0;

                if (hasValue) {
                    select.classList.remove('ng-invalid');
                    select.classList.add('ng-valid');
                }

                return 'synced, hasValue=' + hasValue;
            """, select_el)
        except Exception as e:
            log.warning(f"Angular form model sync failed: {e}")

    # ==============================================================
    #  Toggle switch helper
    # ==============================================================

    def _toggle_switch(self, toggle_locator, target_state=True):
        """Set a toggle switch to the desired state (True=on, False=off).
        Reads the current state first and only clicks if state differs.
        """
        try:
            toggle_el = self.find_visible_element(toggle_locator)
            if not toggle_el:
                log.warning(f"Toggle switch not found: {toggle_locator}")
                return False

            # Scroll into view
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});",
                toggle_el,
            )
            self.wait_seconds(0.3)

            # Check current state — 'active' class on on/off label
            is_currently_on = self.driver.execute_script("""
                var wrapper = arguments[0];
                var onLabel = wrapper.querySelector('span.state-label.on');
                if (onLabel && onLabel.classList.contains('active')) return true;
                return false;
            """, toggle_el)

            if is_currently_on != target_state:
                # Click the slider to toggle
                slider = self.driver.execute_script("""
                    var wrapper = arguments[0];
                    var slider = wrapper.querySelector('.slider');
                    return slider || wrapper;
                """, toggle_el)
                self.driver.execute_script("arguments[0].click();", slider)
                self.wait_seconds(0.3)
                log.info(f"Toggle switched to {'ON' if target_state else 'OFF'}")
            else:
                log.info(f"Toggle already {'ON' if target_state else 'OFF'} — no click needed")

            return True
        except Exception as e:
            log.warning(f"Toggle switch operation failed: {e}")
            return False

    # ==============================================================
    #  Step 1: Fill Universal Fields
    # ==============================================================

    def fill_step1_universal(self, data):
        """Fill the Universal fields section of Step 1.
        data dict keys: party_reference, ownership_status, company_name,
        po_type, email, phone_number, default_currency, pan_number,
        is_msme, status
        """
        log.info("Filling Step 1 — Universal Fields...")

        # Party Reference (optional — skip if empty or not provided)
        party_ref = data.get("party_reference", "")
        if party_ref and party_ref != "":
            self._select_mat_option(self.PARTY_REFERENCE_SELECT, party_ref)
            self.wait_seconds(0.3)

        # Ownership Status (REQUIRED)
        ownership = data.get("ownership_status")
        if ownership is None:
            # Pick random from UI
            self._select_mat_option(self.OWNERSHIP_STATUS_SELECT)
        elif ownership != "":
            self._select_mat_option(self.OWNERSHIP_STATUS_SELECT, ownership)
        self.wait_seconds(0.3)

        # Company Name (REQUIRED)
        company_name = data.get("company_name", "")
        if company_name:
            self.type_text(self.COMPANY_NAME_INPUT, company_name, clear_first=True)
            self.wait_seconds(0.3)

        # PO Type (REQUIRED)
        po_type = data.get("po_type")
        if po_type is None:
            self._select_mat_option(self.PO_TYPE_SELECT)
        elif po_type != "":
            self._select_mat_option(self.PO_TYPE_SELECT, po_type)
        self.wait_seconds(0.3)

        # Email (optional)
        email = data.get("email", "")
        if email:
            self.type_text(self.EMAIL_INPUT, email, clear_first=True)
            self.wait_seconds(0.3)

        # Phone Number (REQUIRED)
        phone = data.get("phone_number", "")
        if phone:
            self.type_text(self.PHONE_NUMBER_INPUT, phone, clear_first=True)
            self.wait_seconds(0.3)

        # Default Currency (REQUIRED)
        currency = data.get("default_currency")
        if currency is None:
            self._select_mat_option(self.DEFAULT_CURRENCY_SELECT)
        elif currency != "":
            self._select_mat_option(self.DEFAULT_CURRENCY_SELECT, currency)
        self.wait_seconds(0.3)

        # PAN Number (REQUIRED)
        pan = data.get("pan_number", "")
        if pan:
            self.type_text(self.PAN_NUMBER_INPUT, pan, clear_first=True)
            self.wait_seconds(0.3)

        # Toggle: Is MSME Registered? (default=No)
        if "is_msme" in data:
            self._toggle_switch(self.IS_MSME_TOGGLE, data["is_msme"])

        # Toggle: Status (default=Active)
        if "status" in data:
            self._toggle_switch(self.STATUS_TOGGLE, data["status"])

        log.info("Step 1 Universal Fields filled")

    # ==============================================================
    #  Step 1: Scroll to Additional Details + Fill
    # ==============================================================

    def scroll_to_additional_details(self):
        """Scroll down within Step 1 to reveal the Additional Details section."""
        log.info("Scrolling to Additional Details section...")
        try:
            # Scroll the popup content down
            self.driver.execute_script("""
                // Find the popup content area and scroll down
                var popup = document.querySelector('.big-model, .edit_pop_up, mat-dialog-container');
                if (popup) {
                    var scrollable = popup.querySelector('.mat-stepper-content, .popup-body, .mat-dialog-content');
                    if (scrollable) {
                        scrollable.scrollTop = scrollable.scrollHeight;
                    } else {
                        // Try scrolling the popup itself
                        popup.scrollTop = popup.scrollHeight;
                    }
                }
                // Also try scrolling the stepper content for step 1
                var stepContent = document.querySelector('mat-step-content');
                if (stepContent) {
                    stepContent.scrollTop = stepContent.scrollHeight;
                }
            """)
            self.wait_seconds(0.5)

            # Also scroll the Contact Person Name field into view as a target
            try:
                contact_input = self.driver.find_element(
                    By.CSS_SELECTOR, "input[name='Contact Person Name']"
                )
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});",
                    contact_input,
                )
                self.wait_seconds(0.5)
            except Exception:
                pass

            log.info("Scrolled to Additional Details")
        except Exception as e:
            log.warning(f"Scroll to Additional Details failed: {e}")

    def fill_step1_additional(self, data):
        """Fill the Additional Details sub-section of Step 1.
        Call scroll_to_additional_details() first.
        data dict keys: is_gst_set_off, is_tds_applicable,
        contact_person, office_number, payment_terms, delivery_terms,
        mode_of_delivery
        """
        log.info("Filling Step 1 — Additional Details...")

        # Ensure Additional Details are visible
        self.scroll_to_additional_details()

        # Toggle: Is GST Set Off (default=Yes)
        if "is_gst_set_off" in data:
            self._toggle_switch(self.IS_GST_SET_OFF_TOGGLE, data["is_gst_set_off"])

        # Toggle: Is TDS Applicable (default=No)
        if "is_tds_applicable" in data:
            self._toggle_switch(self.IS_TDS_APPLICABLE_TOGGLE, data["is_tds_applicable"])

        # Contact Person Name (optional)
        contact = data.get("contact_person", "")
        if contact:
            self.type_text(self.CONTACT_PERSON_INPUT, contact, clear_first=True)
            self.wait_seconds(0.3)

        # Office Number (optional)
        office = data.get("office_number", "")
        if office:
            self.type_text(self.OFFICE_NUMBER_INPUT, office, clear_first=True)
            self.wait_seconds(0.3)

        # Payment Terms (optional)
        payment_terms = data.get("payment_terms")
        if payment_terms is None:
            self._select_mat_option(self.PAYMENT_TERMS_SELECT)
        elif payment_terms != "":
            self._select_mat_option(self.PAYMENT_TERMS_SELECT, payment_terms)
        self.wait_seconds(0.3)

        # Delivery Terms (optional)
        delivery_terms = data.get("delivery_terms")
        if delivery_terms is None:
            self._select_mat_option(self.DELIVERY_TERMS_SELECT)
        elif delivery_terms != "":
            self._select_mat_option(self.DELIVERY_TERMS_SELECT, delivery_terms)
        self.wait_seconds(0.3)

        # Mode Of Delivery (optional)
        mode = data.get("mode_of_delivery")
        if mode is None:
            self._select_mat_option(self.MODE_OF_DELIVERY_SELECT)
        elif mode != "":
            self._select_mat_option(self.MODE_OF_DELIVERY_SELECT, mode)
        self.wait_seconds(0.3)

        log.info("Step 1 Additional Details filled")

    # ==============================================================
    #  Stepper navigation
    # ==============================================================

    def click_stepper_next(self):
        """Click the Next button on the current stepper step."""
        log.info("Clicking stepper Next button...")
        self._force_close_panels()

        # Strategy 1: CSS locator
        try:
            next_btns = self.driver.find_elements(
                By.CSS_SELECTOR, "button.mat-stepper-next"
            )
            for btn in next_btns:
                try:
                    if btn.is_displayed() and btn.is_enabled():
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({block:'center'});"
                            "arguments[0].click();",
                            btn,
                        )
                        self.wait_seconds(1)
                        log.info("Next clicked via CSS")
                        return
                except Exception:
                    continue
        except Exception:
            pass

        # Strategy 2: Text search
        try:
            next_btns = self.driver.find_elements(
                By.XPATH,
                "//button[contains(@class,'mat-stepper-next') or contains(.,'Next')]"
            )
            for btn in next_btns:
                try:
                    if btn.is_displayed() and btn.is_enabled():
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({block:'center'});"
                            "arguments[0].click();",
                            btn,
                        )
                        self.wait_seconds(1)
                        log.info("Next clicked via text search")
                        return
                except Exception:
                    continue
        except Exception:
            pass

        # Strategy 3: JS click
        try:
            self.driver.execute_script("""
                var btns = document.querySelectorAll('button.mat-stepper-next');
                for (var i = 0; i < btns.length; i++) {
                    if (btns[i].offsetParent !== null) {
                        btns[i].click();
                        break;
                    }
                }
            """)
            self.wait_seconds(1)
            log.info("Next clicked via JS")
            return
        except Exception:
            pass

        log.warning("Next button not found or not clickable")

    def click_stepper_back(self):
        """Click the Back button on the current stepper step."""
        log.info("Clicking stepper Back button...")
        self._force_close_panels()

        try:
            back_btns = self.driver.find_elements(
                By.CSS_SELECTOR, "button.mat-stepper-previous"
            )
            for btn in back_btns:
                try:
                    if btn.is_displayed() and btn.is_enabled():
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({block:'center'});"
                            "arguments[0].click();",
                            btn,
                        )
                        self.wait_seconds(1)
                        log.info("Back clicked")
                        return
                except Exception:
                    continue
        except Exception:
            pass

        log.warning("Back button not found or not clickable")

    # ==============================================================
    #  Step 2: Fill Address Details
    # ==============================================================

    # ==============================================================
    #  Address row-scoped locator helpers
    # ==============================================================
    # When the ERP renders multiple address rows in Step 2, the
    # generic class-level locators (ADDRESS_TYPE_SELECT, etc.) always
    # match the FIRST row.  These helpers build row-scoped XPath/CSS
    # locators that target the Nth address-row container inside
    # mat-step-content[2] (0-indexed: step 2 = index 1 in DOM, but
    # mat-step-content uses 1-based indexing in XPath).
    #
    # RhythmERP renders each address row inside a container div under
    # <mat-step-content> (the 2nd one for Step 2).  We scope to the
    # Nth such container using position().
    # ==============================================================

    def _addr_row_select_locator(self, label, row_index=0):
        """Return a row-scoped mat-select locator for an address dropdown.

        Args:
            label: The mat-label text (e.g. 'Address Type', 'Country')
            row_index: 0-based address row index (0 = first row, 1 = second)

        Returns:
            ("xpath", scoped_xpath) tuple targeting the Nth row only.
        """
        pos = row_index + 1  # XPath position() is 1-based
        xpath = (
            f"(//mat-step-content[2]"
            f"//mat-label[contains(.,'{label}')]"
            f"/ancestor::mat-form-field//mat-select)[{pos}]"
        )
        return ("xpath", xpath)

    def _addr_row_input_locator(self, field_name, row_index=0):
        """Return a row-scoped input locator for an address text field.

        Args:
            field_name: The input[name] value (e.g. 'Address', 'Pin Code', 'GSTIN')
            row_index: 0-based address row index

        Returns:
            ("xpath", scoped_xpath) tuple targeting the Nth row only.
        """
        pos = row_index + 1
        xpath = (
            f"(//mat-step-content[2]"
            f"//input[@name='{field_name}'])[{pos}]"
        )
        return ("xpath", xpath)

    def fill_step2_address(self, data, row_index=0):
        """Fill the Address Details fields in Step 2.

        IMPORTANT (verified 2026-06-05): ERP now REQUIRES both Shipping
        AND Billing address rows for Supplier roles.  This method fills
        ONE row at a time.  Call it once per address row, using
        row_index=0 for Shipping and row_index=1 for Billing.

        When row_index > 0, row-scoped XPath locators are used so the
        correct address-row container is targeted (not the first row).

        Cascading dropdowns MUST be filled in order:
        Country → State → District → Taluka → Village

        data dict keys: address_type, country, state, district,
        taluka, village, address, pin_code, gstin
        """
        log.info(f"Filling Step 2 — Address Details (row {row_index})...")

        # Pick locators: row-scoped when row_index > 0, class-level for row 0
        if row_index == 0:
            addr_type_loc = self.ADDRESS_TYPE_SELECT
            country_loc = self.COUNTRY_SELECT
            state_loc = self.STATE_SELECT
            district_loc = self.DISTRICT_SELECT
            taluka_loc = self.TALUKA_SELECT
            village_loc = self.VILLAGE_SELECT
            address_loc = self.ADDRESS_INPUT
            pin_code_loc = self.PIN_CODE_INPUT
            gstin_loc = self.GSTIN_INPUT
        else:
            addr_type_loc = self._addr_row_select_locator("Address Type", row_index)
            country_loc = self._addr_row_select_locator("Country", row_index)
            state_loc = self._addr_row_select_locator("State", row_index)
            district_loc = self._addr_row_select_locator("District", row_index)
            taluka_loc = self._addr_row_select_locator("Taluka", row_index)
            village_loc = self._addr_row_select_locator("Village", row_index)
            address_loc = self._addr_row_input_locator("Address", row_index)
            pin_code_loc = self._addr_row_input_locator("Pin Code", row_index)
            gstin_loc = self._addr_row_input_locator("GSTIN", row_index)

        # Address Type (REQUIRED) — Shipping/Billing
        addr_type = data.get("address_type")
        if addr_type is None:
            self._select_mat_option(addr_type_loc)
        elif addr_type != "":
            self._select_mat_option(addr_type_loc, addr_type)
        self.wait_seconds(0.5)

        # Country (REQUIRED) — MUST be filled first for cascading
        country = data.get("country")
        if country is None:
            country_selected = self._select_mat_option(country_loc)
        elif country != "":
            country_selected = self._select_mat_option(country_loc, country)
        else:
            country_selected = None
        self.wait_seconds(1)  # Wait for State options to load

        # State (REQUIRED, depends on Country)
        state = data.get("state")
        if state is None:
            state_selected = self._select_mat_option(state_loc)
        elif state != "":
            state_selected = self._select_mat_option(state_loc, state)
        else:
            state_selected = None
        self.wait_seconds(1)  # Wait for District options to load

        # District (REQUIRED, depends on State)
        district = data.get("district")
        if district is None:
            district_selected = self._select_mat_option(district_loc)
        elif district != "":
            district_selected = self._select_mat_option(district_loc, district)
        else:
            district_selected = None
        self.wait_seconds(1)  # Wait for Taluka options to load

        # Taluka (REQUIRED, depends on District)
        taluka = data.get("taluka")
        if taluka is None:
            self._select_mat_option(taluka_loc)
        elif taluka != "":
            self._select_mat_option(taluka_loc, taluka)
        self.wait_seconds(1)  # Wait for Village options to load

        # Village (optional, depends on Taluka)
        village = data.get("village")
        if village is None:
            self._select_mat_option(village_loc)
        elif village != "":
            self._select_mat_option(village_loc, village)
        self.wait_seconds(0.3)

        # Address (REQUIRED)
        address = data.get("address", "")
        if address:
            self.type_text(address_loc, address, clear_first=True)
            self.wait_seconds(0.3)

        # Pin Code (optional)
        pin_code = data.get("pin_code", "")
        if pin_code:
            self.type_text(pin_code_loc, pin_code, clear_first=True)
            self.wait_seconds(0.3)

        # GSTIN (optional)
        gstin = data.get("gstin", "")
        if gstin:
            self.type_text(gstin_loc, gstin, clear_first=True)
            self.wait_seconds(0.3)

        log.info(f"Step 2 Address Details filled (row {row_index})")

    def add_address_row(self):
        """Click the Add button to add a new Address row in Step 2."""
        log.info("Adding new Address row...")
        try:
            btn = self.driver.find_element(
                By.XPATH,
                "//mat-step-content[2]//button[.//mat-icon[text()='add']]"
            )
            self.driver.execute_script("arguments[0].click();", btn)
            self.wait_seconds(1)
            log.info("Address row added")
        except Exception:
            # Fallback: try clicking any add button in step 2
            try:
                self.driver.execute_script("""
                    var step2 = document.querySelectorAll('mat-step-content')[1];
                    if (step2) {
                        var addBtn = step2.querySelector('button mat-icon');
                        if (addBtn && addBtn.textContent.trim() === 'add') {
                            addBtn.closest('button').click();
                        }
                    }
                """)
                self.wait_seconds(1)
                log.info("Address row added via JS fallback")
            except Exception as e:
                log.warning(f"Add Address row failed: {e}")

    def remove_address_row(self, row_index=0):
        """Click the Remove button on an Address row in Step 2."""
        log.info(f"Removing Address row {row_index}...")
        try:
            remove_btns = self.driver.find_elements(
                By.XPATH,
                "//mat-step-content[2]//button[.//mat-icon[text()='delete' or text()='remove' or text()='close']]"
            )
            if remove_btns and len(remove_btns) > row_index:
                self.driver.execute_script(
                    "arguments[0].click();", remove_btns[row_index]
                )
                self.wait_seconds(0.5)
                log.info(f"Address row {row_index} removed")
        except Exception as e:
            log.warning(f"Remove Address row failed: {e}")

    # ==============================================================
    #  Bank row-scoped locator helpers
    # ==============================================================
    # Same pattern as address rows — when multiple bank rows exist,
    # generic locators always match the first. These helpers build
    # row-scoped locators targeting the Nth bank row.
    # ==============================================================

    def _bank_row_select_locator(self, label, row_index=0):
        """Return a row-scoped mat-select locator for a bank dropdown.

        Args:
            label: The mat-label text (e.g. 'Account Type', 'Bank Proof')
            row_index: 0-based bank row index

        Returns:
            ("xpath", scoped_xpath) tuple targeting the Nth row only.
        """
        pos = row_index + 1
        xpath = (
            f"(//mat-step-content[3]"
            f"//mat-label[contains(.,'{label}')]"
            f"/ancestor::mat-form-field//mat-select)[{pos}]"
        )
        return ("xpath", xpath)

    def _bank_row_input_locator(self, field_name, row_index=0):
        """Return a row-scoped input locator for a bank text field.

        Args:
            field_name: The input[name] value (e.g. 'Bank Name', 'Branch')
            row_index: 0-based bank row index

        Returns:
            ("xpath", scoped_xpath) tuple targeting the Nth row only.
        """
        pos = row_index + 1
        xpath = (
            f"(//mat-step-content[3]"
            f"//input[@name='{field_name}'])[{pos}]"
        )
        return ("xpath", xpath)

    def fill_step3_bank(self, data, row_index=0):
        """Fill the Bank Details fields in Step 3.

        When row_index > 0, row-scoped XPath locators are used so the
        correct bank-row container is targeted (not the first row).

        data dict keys: bank_name, branch, ifsc_code, account_type,
        account_holder_name, account_number, bank_proof, attachment_path
        """
        log.info(f"Filling Step 3 — Bank Details (row {row_index})...")

        # Pick locators: row-scoped when row_index > 0, class-level for row 0
        if row_index == 0:
            bank_name_loc = self.BANK_NAME_INPUT
            branch_loc = self.BRANCH_INPUT
            ifsc_loc = self.IFSC_CODE_INPUT
            account_type_loc = self.ACCOUNT_TYPE_SELECT
            holder_loc = self.ACCOUNT_HOLDER_NAME_INPUT
            account_num_loc = self.ACCOUNT_NUMBER_INPUT
            bank_proof_loc = self.BANK_PROOF_SELECT
        else:
            bank_name_loc = self._bank_row_input_locator("Bank Name", row_index)
            branch_loc = self._bank_row_input_locator("Branch", row_index)
            ifsc_loc = self._bank_row_input_locator("IFSC Code", row_index)
            account_type_loc = self._bank_row_select_locator("Account Type", row_index)
            holder_loc = self._bank_row_input_locator("Account Holder Name", row_index)
            account_num_loc = self._bank_row_input_locator("Account Number", row_index)
            bank_proof_loc = self._bank_row_select_locator("Bank Proof", row_index)

        # Bank Name (optional)
        bank_name = data.get("bank_name", "")
        if bank_name:
            self.type_text(bank_name_loc, bank_name, clear_first=True)
            self.wait_seconds(0.3)

        # Branch (optional)
        branch = data.get("branch", "")
        if branch:
            self.type_text(branch_loc, branch, clear_first=True)
            self.wait_seconds(0.3)

        # IFSC Code (optional)
        ifsc = data.get("ifsc_code", "")
        if ifsc:
            self.type_text(ifsc_loc, ifsc, clear_first=True)
            self.wait_seconds(0.3)

        # Account Type (optional) — Current/Saving
        account_type = data.get("account_type")
        if account_type is None:
            self._select_mat_option(account_type_loc)
        elif account_type != "":
            self._select_mat_option(account_type_loc, account_type)
        self.wait_seconds(0.3)

        # Account Holder Name (optional)
        holder = data.get("account_holder_name", "")
        if holder:
            self.type_text(holder_loc, holder, clear_first=True)
            self.wait_seconds(0.3)

        # Account Number (optional)
        account_num = data.get("account_number", "")
        if account_num:
            self.type_text(account_num_loc, account_num, clear_first=True)
            self.wait_seconds(0.3)

        # Bank Proof (REQUIRED)
        bank_proof = data.get("bank_proof")
        if bank_proof is None:
            self._select_mat_option(bank_proof_loc)
        elif bank_proof != "":
            self._select_mat_option(bank_proof_loc, bank_proof)
        self.wait_seconds(0.3)

        # Attachment (optional file upload)
        attachment_path = data.get("attachment_path")
        if attachment_path:
            self._upload_file(attachment_path)

        log.info(f"Step 3 Bank Details filled (row {row_index})")

    def add_bank_row(self):
        """Click the Add button to add a new Bank row in Step 3."""
        log.info("Adding new Bank row...")
        try:
            btn = self.driver.find_element(
                By.XPATH,
                "//mat-step-content[3]//button[.//mat-icon[text()='add']]"
            )
            self.driver.execute_script("arguments[0].click();", btn)
            self.wait_seconds(1)
            log.info("Bank row added")
        except Exception:
            try:
                self.driver.execute_script("""
                    var step3 = document.querySelectorAll('mat-step-content')[2];
                    if (step3) {
                        var addBtn = step3.querySelector('button mat-icon');
                        if (addBtn && addBtn.textContent.trim() === 'add') {
                            addBtn.closest('button').click();
                        }
                    }
                """)
                self.wait_seconds(1)
                log.info("Bank row added via JS fallback")
            except Exception as e:
                log.warning(f"Add Bank row failed: {e}")

    def remove_bank_row(self, row_index=0):
        """Click the Remove button on a Bank row in Step 3."""
        log.info(f"Removing Bank row {row_index}...")
        try:
            remove_btns = self.driver.find_elements(
                By.XPATH,
                "//mat-step-content[3]//button[.//mat-icon[text()='delete' or text()='remove' or text()='close']]"
            )
            if remove_btns and len(remove_btns) > row_index:
                self.driver.execute_script(
                    "arguments[0].click();", remove_btns[row_index]
                )
                self.wait_seconds(0.5)
                log.info(f"Bank row {row_index} removed")
        except Exception as e:
            log.warning(f"Remove Bank row failed: {e}")

    def _upload_file(self, file_path):
        """Upload a file to the attachment input in Step 3."""
        try:
            file_input = self.driver.find_element(
                By.CSS_SELECTOR, "input[type='file'][accept='.png, .jpg, .pdf'], input[type='file']"
            )
            file_input.send_keys(file_path)
            self.wait_seconds(1)
            log.info(f"File uploaded: {file_path}")
        except Exception as e:
            log.warning(f"File upload failed: {e}")

    # ==============================================================
    #  High-level: Create Supplier (full 3-step flow)
    # ==============================================================

    def create_supplier(self, data):
        """Create a complete supplier through the 3-step stepper form.
        data dict should have keys: step1, step2, step3

        Returns dict: {"status": "PASSED"/"FAILED", "message": str}
        """
        log.info("Creating supplier (full 3-step flow)...")

        result = {"status": "FAILED", "message": ""}

        try:
            # Open Add form
            self.open_add_form()
            self.wait_seconds(1)
            if not self._is_form_popup_open():
                result["message"] = "Add form did not open"
                return result

            # Step 1: Fill Universal + Additional Details
            step1 = data.get("step1", {})
            self.fill_step1_universal(step1)
            self.fill_step1_additional(step1)

            # Click Next to go to Step 2
            self.click_stepper_next()
            self.wait_seconds(1)

            # Step 2: Fill Address Details
            # IMPORTANT (verified 2026-06-05): ERP now REQUIRES both Shipping
            # AND Billing address rows for Supplier roles. The data dict may
            # contain either a single step2 or a list step2_addresses.
            step2_addresses = data.get("step2_addresses", [])
            if not step2_addresses:
                # Fallback: single step2 dict → wrap in list
                step2 = data.get("step2", {})
                if step2:
                    # First row = Shipping, second row = Billing
                    step2_addresses = [
                        {**step2, "address_type": "Shipping"},
                        {**step2, "address_type": "Billing"},
                    ]

            for i, addr_data in enumerate(step2_addresses):
                if i > 0:
                    # Add a new row for Billing (and beyond)
                    self.add_address_row()
                    self.wait_seconds(1)
                self.fill_step2_address(addr_data, row_index=i)

            # Click Next to go to Step 3
            self.click_stepper_next()
            self.wait_seconds(1)

            # Step 3: Fill Bank Details
            step3 = data.get("step3", {})
            self.fill_step3_bank(step3)

            # Submit
            self.submit()
            self.wait_seconds(2)

            # Check for success
            success = self.handle_success_alert(timeout=5)
            if success:
                result["status"] = "PASSED"
                result["message"] = f"Supplier created: {success}"
                company_name = step1.get("company_name", "Unknown")
                SP_SUBMISSIONS.append(company_name)
                log.info(f"Supplier created successfully: {company_name}")
            else:
                # Check for validation failure
                validation = self.handle_validation_warning(timeout=3)
                if validation:
                    result["message"] = f"Validation failed: {validation}"
                    log.info(f"Supplier creation blocked by validation: {validation}")
                else:
                    result["message"] = "No success or validation response"
                    log.warning("No response after submit")

        except Exception as e:
            result["message"] = f"Exception: {str(e)}"
            log.error(f"Create supplier exception: {e}")

        return result

    # ==============================================================
    #  Submit / Update / Cancel
    # ==============================================================

    def submit(self):
        """Click the Submit button (Create mode)."""
        log.info("Clicking Submit button...")
        self._force_close_panels()

        # Strategy 1: XPath locator
        try:
            btn = self.find_visible_element(self.SUBMIT_BUTTON)
            if btn:
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});"
                    "arguments[0].click();",
                    btn,
                )
                self.wait_seconds(1)
                log.info("Submit clicked via locator")
                return
        except Exception:
            pass

        # Strategy 2: Find by text
        try:
            btns = self.driver.find_elements(
                By.XPATH,
                "//div[contains(@class,'popup-footer')]//button[contains(.,'Submit')]"
            )
            for btn in btns:
                try:
                    if btn.is_displayed() and btn.is_enabled():
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({block:'center'});"
                            "arguments[0].click();",
                            btn,
                        )
                        self.wait_seconds(1)
                        log.info("Submit clicked via text search")
                        return
                except Exception:
                    continue
        except Exception:
            pass

        # Strategy 3: JS click
        try:
            self.driver.execute_script("""
                var btns = document.querySelectorAll(
                    '.popup-footer button, .big-model button'
                );
                for (var i = 0; i < btns.length; i++) {
                    if (btns[i].textContent.trim() === 'Submit') {
                        btns[i].click();
                        break;
                    }
                }
            """)
            self.wait_seconds(1)
            log.info("Submit clicked via JS")
            return
        except Exception:
            pass

        log.warning("Submit button not found or not clickable")

    def click_update(self):
        """Click the Update button (Edit mode).
        BUG-005: May not exist in Edit mode.
        """
        log.info("Clicking Update button...")
        self._force_close_panels()

        try:
            btn = self.find_visible_element(self.UPDATE_BUTTON)
            if btn:
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});"
                    "arguments[0].click();",
                    btn,
                )
                self.wait_seconds(1)
                log.info("Update clicked")
                return
        except Exception:
            pass

        log.warning("Update button not found — BUG-005 confirmed?")

    def cancel(self):
        """Click the Cancel button to close the popup."""
        log.info("Clicking Cancel button...")
        self._force_close_panels()

        try:
            btn = self.find_visible_element(self.CANCEL_BUTTON)
            if btn:
                self.driver.execute_script("arguments[0].click();", btn)
                self.wait_seconds(1)
                return
        except Exception:
            pass

        # Fallback: Close via X button
        self.close_popup()

    def close_popup(self):
        """Close the form popup via X button or Cancel."""
        try:
            close_btns = self.driver.find_elements(
                By.CSS_SELECTOR,
                ".big-model .popup-actions button, "
                ".edit_pop_up .popup-actions button, "
                "mat-dialog-container .popup-actions button"
            )
            for btn in close_btns:
                try:
                    icon = btn.find_element(By.CSS_SELECTOR, "mat-icon")
                    if icon.text.strip().lower() == "close" and btn.is_displayed():
                        self.driver.execute_script("arguments[0].click();", btn)
                        self.wait_seconds(1)
                        return
                except Exception:
                    continue
        except Exception:
            pass
        self.cancel()

    def force_close_form_popup(self):
        """Force close any open popup via JS."""
        try:
            self.driver.execute_script("""
                var closeBtns = document.querySelectorAll(
                    '.big-model .popup-actions button mat-icon, '
                    + '.edit_pop_up .popup-actions button mat-icon, '
                    + 'mat-dialog-container .popup-actions button mat-icon'
                );
                for (var i = 0; i < closeBtns.length; i++) {
                    if (closeBtns[i].textContent.trim().toLowerCase() === 'close') {
                        closeBtns[i].closest('button').click();
                        break;
                    }
                }
            """)
            self.wait_seconds(0.5)
        except Exception:
            pass

    # ==============================================================
    #  SweetAlert2 handlers
    # ==============================================================

    def handle_validation_warning(self, timeout=5):
        """Handle SweetAlert2 'Validation Failed' warning.
        Returns the alert title text if found, None otherwise.
        """
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, ".swal2-container")
                )
            )
            title_el = self.driver.find_element(By.CSS_SELECTOR, "#swal2-title")
            title = title_el.text.strip() if title_el else ""

            # Click OK to dismiss
            try:
                confirm_btn = self.driver.find_element(
                    By.CSS_SELECTOR, ".swal2-confirm"
                )
                self.driver.execute_script("arguments[0].click();", confirm_btn)
                self.wait_seconds(0.5)
            except Exception:
                pass

            log.info(f"SweetAlert2 handled: {title}")
            return title
        except TimeoutException:
            return None
        except Exception:
            return None

    def handle_success_alert(self, timeout=5):
        """Handle SweetAlert2 success alert.
        Returns the alert title/text if found, None otherwise.
        """
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, ".swal2-icon.swal2-success")
                )
            )
            title_el = self.driver.find_element(By.CSS_SELECTOR, "#swal2-title")
            title = title_el.text.strip() if title_el else ""

            # Click OK to dismiss
            try:
                confirm_btn = self.driver.find_element(
                    By.CSS_SELECTOR, ".swal2-confirm"
                )
                self.driver.execute_script("arguments[0].click();", confirm_btn)
                self.wait_seconds(0.5)
            except Exception:
                pass

            log.info(f"SweetAlert2 success: {title}")
            return title
        except TimeoutException:
            return None
        except Exception:
            return None

    # ==============================================================
    #  Validation error helpers
    # ==============================================================

    def get_mat_error_text(self):
        """Get all visible mat-error texts on the current form."""
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

    def has_field_error(self, field_label):
        """Check if a specific field has a visible mat-error."""
        try:
            error = self.driver.find_element(
                By.XPATH,
                f"//mat-label[contains(.,'{field_label}')]"
                "/ancestor::mat-form-field//mat-error"
            )
            return error.is_displayed()
        except Exception:
            return False

    def get_ng_invalid_count(self):
        """Count ng-invalid fields in the current form."""
        try:
            invalids = self.driver.find_elements(
                By.CSS_SELECTOR, ".ng-invalid"
            )
            # Filter to only visible form elements
            count = 0
            for el in invalids:
                try:
                    tag = el.tag_name.lower()
                    if tag in ("input", "select", "mat-select", "textarea") and el.is_displayed():
                        count += 1
                except Exception:
                    continue
            return count
        except Exception:
            return 0

    # ==============================================================
    #  Table interactions
    # ==============================================================

    def get_table_row_count(self):
        """Get the number of data rows in the main table."""
        try:
            rows = self.driver.find_elements(
                By.CSS_SELECTOR,
                "table#excel-table tbody tr, table.mat-mdc-table tbody tr.mat-mdc-row"
            )
            # Filter out no-data rows
            data_rows = []
            for row in rows:
                try:
                    no_data = row.find_elements(
                        By.CSS_SELECTOR, "td.no-data, td.mat-mdc-no-data-cell"
                    )
                    if not no_data:
                        data_rows.append(row)
                except Exception:
                    data_rows.append(row)
            return len(data_rows)
        except Exception:
            return 0

    def get_all_company_names(self):
        """Get all Company Names from the table listing."""
        names = []
        try:
            cells = self.driver.find_elements(
                By.CSS_SELECTOR,
                "td.cdk-column-name, td.mat-column-name, "
                "td.cdk-column-company_name, td.mat-column-company_name"
            )
            for cell in cells:
                try:
                    text = cell.text.strip()
                    if text:
                        names.append(text)
                except Exception:
                    continue
        except Exception:
            pass
        return names

    # ==============================================================
    #  Row action buttons — View / Edit
    # ==============================================================

    def click_view_button_by_name(self, company_name):
        """Click the View option from 3-dot menu for a specific supplier."""
        log.info(f"Clicking View for: {company_name}")
        try:
            # Find the row, then click its 3-dot menu trigger
            row = self.driver.find_element(
                By.XPATH,
                f"//td[contains(text(),'{company_name}')]/ancestor::tr"
            )
            trigger = row.find_element(
                By.CSS_SELECTOR, "button.mat-mdc-menu-trigger.erp-row-trigger"
            )
            self.driver.execute_script("arguments[0].click();", trigger)
            self.wait_seconds(0.5)

            # Click View from the dropdown menu
            view_btn = self.driver.find_element(
                By.XPATH,
                "//div[contains(@class,'mat-mdc-menu-content')]"
                "//span[contains(@class,'erp-menu-title') and text()='View']"
                "/ancestor::button"
            )
            self.driver.execute_script("arguments[0].click();", view_btn)
            self.wait_seconds(0.5)
            log.info("View clicked from menu")
        except Exception:
            log.warning(f"View not found for {company_name}, trying first row")
            self._click_first_menu_option("view")

    def click_edit_button_by_name(self, company_name):
        """Click the Edit option from 3-dot menu for a specific supplier."""
        log.info(f"Clicking Edit for: {company_name}")
        try:
            # Find the row, then click its 3-dot menu trigger
            row = self.driver.find_element(
                By.XPATH,
                f"//td[contains(text(),'{company_name}')]/ancestor::tr"
            )
            trigger = row.find_element(
                By.CSS_SELECTOR, "button.mat-mdc-menu-trigger.erp-row-trigger"
            )
            self.driver.execute_script("arguments[0].click();", trigger)
            self.wait_seconds(0.5)

            # Click Edit from the dropdown menu
            edit_btn = self.driver.find_element(
                By.XPATH,
                "//div[contains(@class,'mat-mdc-menu-content')]"
                "//span[contains(@class,'erp-menu-title') and text()='Edit']"
                "/ancestor::button"
            )
            self.driver.execute_script("arguments[0].click();", edit_btn)
            self.wait_seconds(0.5)
            log.info("Edit clicked from menu")
        except Exception:
            log.warning(f"Edit not found for {company_name}, trying first row")
            self._click_first_menu_option("edit")

    def click_view_first_row(self):
        """Click View on the first row in the table (no creation needed)."""
        log.info("Opening View for first row...")
        self._click_first_menu_option("View")
        self.wait_seconds(1)
        if not self._is_form_popup_open():
            self._wait_for_form_content(timeout=5)

    def click_edit_first_row(self):
        """Click Edit on the first row in the table (no creation needed)."""
        log.info("Opening Edit for first row...")
        self._click_first_menu_option("Edit")
        self.wait_seconds(1)
        if not self._is_form_popup_open():
            self._wait_for_form_content(timeout=5)
    
    def get_first_row_name(self):
        """Get the Company Name from the first row in the table."""
        try:
            cells = self.driver.find_elements(
                By.CSS_SELECTOR,
                "td.cdk-column-name, td.mat-column-name, "
                "td.cdk-column-company_name, td.mat-column-company_name"
            )
            for cell in cells:
                try:
                    text = cell.text.strip()
                    if text:
                        return text
                except Exception:
                    continue
        except Exception:
            pass
        return None

    def click_history_first_row(self):
        """Click History on the first row in the table (no creation needed)."""
        log.info("Opening History for first row...")
        self._click_first_menu_option("History")
        self.wait_seconds(1)

    def _click_first_menu_option(self, option="view"):
        """Click the first 3-dot menu trigger, then select View/Edit/History."""
        try:
            triggers = self.driver.find_elements(
                By.CSS_SELECTOR, "button.mat-mdc-menu-trigger.erp-row-trigger"
            )
            for trigger in triggers:
                try:
                    if trigger.is_displayed():
                        self.driver.execute_script("arguments[0].click();", trigger)
                        self.wait_seconds(0.5)

                        # Click the desired option from the menu
                        option_btn = self.driver.find_element(
                            By.XPATH,
                            f"//div[contains(@class,'mat-mdc-menu-content')]"
                            f"//span[contains(@class,'erp-menu-title') and text()='{option.capitalize()}']"
                            f"/ancestor::button"
                        )
                        self.driver.execute_script("arguments[0].click();", option_btn)
                        self.wait_seconds(0.5)
                        return
                except Exception:
                    continue
        except Exception:
            pass

    # ==============================================================
    #  View / Edit popup verification
    # ==============================================================

    def verify_view_popup_read_only(self):
        """Verify that View popup shows all fields as disabled/read-only."""
        try:
            # Check if all inputs are disabled
            inputs = self.driver.find_elements(
                By.CSS_SELECTOR,
                ".big-model input, mat-dialog-container input, .edit_pop_up input"
            )
            all_disabled = True
            for inp in inputs:
                try:
                    if inp.is_displayed() and inp.is_enabled():
                        all_disabled = False
                        break
                except Exception:
                    continue

            # Check if all mat-selects are disabled
            selects = self.driver.find_elements(
                By.CSS_SELECTOR,
                ".big-model mat-select, mat-dialog-container mat-select, .edit_pop_up mat-select"
            )
            for sel in selects:
                try:
                    if sel.is_displayed():
                        aria_disabled = sel.get_attribute("aria-disabled")
                        if aria_disabled != "true":
                            class_list = sel.get_attribute("class") or ""
                            if "mat-mdc-select-disabled" not in class_list:
                                all_disabled = False
                                break
                except Exception:
                    continue

            return all_disabled
        except Exception:
            return False

    def verify_edit_popup_editable(self):
        """Verify that Edit popup has editable fields.
        BUG-005: May not have Update button.
        """
        try:
            # Check if any input is enabled
            inputs = self.driver.find_elements(
                By.CSS_SELECTOR,
                ".big-model input, mat-dialog-container input, .edit_pop_up input"
            )
            has_editable = False
            for inp in inputs:
                try:
                    if inp.is_displayed() and inp.is_enabled():
                        has_editable = True
                        break
                except Exception:
                    continue

            # Check for Update button
            has_update = False
            try:
                update_btns = self.driver.find_elements(
                    By.XPATH,
                    "//div[contains(@class,'popup-footer')]//button[contains(.,'Update')]"
                )
                for btn in update_btns:
                    try:
                        if btn.is_displayed():
                            has_update = True
                            break
                    except Exception:
                        continue
            except Exception:
                pass

            return has_editable and has_update
        except Exception:
            return False

    def has_update_button(self):
        """Check if the Update button is visible in the popup.
        BUG-005: Update button is NOT present in Edit mode.
        """
        try:
            btns = self.driver.find_elements(
                By.XPATH,
                "//div[contains(@class,'popup-footer')]//button[contains(.,'Update')]"
            )
            for btn in btns:
                try:
                    if btn.is_displayed():
                        return True
                except Exception:
                    continue
        except Exception:
            pass
        return False

    # ==============================================================
    #  Search
    # ==============================================================

    def search_item(self, search_text):
        """Search for a supplier in the listing.
        Returns True if results found, False if no-data shown.
        """
        log.info(f"Searching for: {search_text}")
        try:
            # Click search toggle to open the erp-search-container
            try:
                toggle = self.driver.find_element(
                    By.CSS_SELECTOR, "button.search-btn, button[mattooltip='Search']"
                )
                self.driver.execute_script("arguments[0].click();", toggle)
                self.wait_seconds(0.5)
            except Exception:
                pass

            # Clear and type in the erp search input
            try:
                search_input = self.driver.find_element(
                    By.CSS_SELECTOR, "#erpSearchInput, input.erp-search-input"
                )
                # Clear via JS + dispatch input event for Angular
                self.driver.execute_script(
                    "arguments[0].value = '';"
                    "arguments[0].dispatchEvent(new Event('input', {bubbles: true}));",
                    search_input,
                )
                search_input.send_keys(search_text)
                search_input.send_keys(Keys.ENTER)
                self.wait_seconds(2)
            except Exception:
                pass

            # Check for results
            no_data = self.driver.find_elements(
                By.CSS_SELECTOR,
                "table#excel-table tbody tr td.no-data, "
                "table.mat-mdc-table tbody tr td.no-data"
            )
            for nd in no_data:
                try:
                    if nd.is_displayed():
                        return False
                except Exception:
                    continue

            # Check if any rows exist
            rows = self.driver.find_elements(
                By.CSS_SELECTOR,
                "table#excel-table tbody tr, table.mat-mdc-table tbody tr.mat-mdc-row"
            )
            return len(rows) > 0

        except Exception as e:
            log.warning(f"Search failed: {e}")
            return False

    def search_supplier(self, company_name):
        """Public alias for search_item — search by company name."""
        return self.search_item(company_name)

    # ==============================================================
    #  Dropdown option list retrieval
    # ==============================================================

    def get_dropdown_options(self, select_locator):
        """Open a dropdown and return all option texts, then close it."""
        options_list = []
        self._force_close_panels()
        try:
            select_el = self.find_visible_element(select_locator)
            if not select_el:
                return options_list

            self.driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});"
                "arguments[0].click();",
                select_el,
            )
            # Wait for dropdown panel options to appear
            try:
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "div[role='listbox'] mat-option")
                    )
                )
            except TimeoutException:
                log.warning("Dropdown options did not appear in get_dropdown_options")

            options = self.driver.find_elements(
                By.CSS_SELECTOR, "div[role='listbox'] mat-option"
            )
            for opt in options:
                try:
                    text = opt.text.strip()
                    if text:
                        options_list.append(text)
                except Exception:
                    continue

            self._close_dropdown_panel_only()
        except Exception as e:
            log.warning(f"Get dropdown options failed: {e}")
            self._close_dropdown_panel_only()

        return options_list

    # ==============================================================
    #  Phone Number spinner check (BUG-003)
    # ==============================================================

    def has_phone_number_spinner(self):
        """Check if Phone Number input has spinner controls (type=number).
        BUG-003: Phone Number shows spinner arrows because type=number.
        """
        try:
            phone_input = self.driver.find_element(
                By.CSS_SELECTOR, "input[name='Phone Number']"
            )
            input_type = phone_input.get_attribute("type")
            return input_type == "number"
        except Exception:
            return False

    # ==============================================================
    #  Toggle switch default value check
    # ==============================================================

    def get_toggle_state(self, toggle_locator):
        """Get the current state of a toggle switch (True=on, False=off)."""
        try:
            toggle_el = self.find_visible_element(toggle_locator)
            if not toggle_el:
                return None

            return self.driver.execute_script("""
                var wrapper = arguments[0];
                var input = wrapper.querySelector('input[type="checkbox"]');
                if (input) return input.checked;

                var parent = wrapper.closest('app-slide-toggle-v2');
                if (parent) {
                    var cb = parent.querySelector('input[type="checkbox"]');
                    if (cb) return cb.checked;
                }
                return null;
            """, toggle_el)
        except Exception:
            return None

    # ==============================================================
    #  Stepper step verification
    # ==============================================================

    def get_current_step_index(self):
        """Get the current active step index (0-based) in the stepper."""
        try:
            headers = self.driver.find_elements(
                By.CSS_SELECTOR, "mat-step-header"
            )
            for i, header in enumerate(headers):
                try:
                    class_attr = header.get_attribute("class") or ""
                    if "mat-step-header-selected" in class_attr or "mat-step-selected" in class_attr:
                        return i
                    # Check aria-selected
                    aria = header.get_attribute("aria-selected")
                    if aria == "true":
                        return i
                except Exception:
                    continue
        except Exception:
            pass
        return 0

    def is_step_enabled(self, step_index):
        """Check if a stepper step is enabled (navigable)."""
        try:
            headers = self.driver.find_elements(
                By.CSS_SELECTOR, "mat-step-header"
            )
            if step_index < len(headers):
                class_attr = headers[step_index].get_attribute("class") or ""
                # If has 'mat-step-header-disabled' or 'cdk-program-disabled'
                return "disabled" not in class_attr.lower()
        except Exception:
            pass
        return False

    # ==============================================================
    #  Get form field values (for Edit pre-populated check)
    # ==============================================================

    def get_form_field_values(self):
        """Get current values of all form fields in the popup.
        Returns a dict with field names as keys.
        """
        values = {}
        try:
            # Text inputs
            input_names = [
                "Company Name", "Email", "Phone Number", "PAN Number",
                "Contact Person Name", "Office Number",
                "Address", "Pin Code", "GSTIN",
                "Bank Name", "Branch", "IFSC Code",
                "Account Holder Name", "Account Number",
            ]
            for name in input_names:
                try:
                    inp = self.driver.find_element(
                        By.CSS_SELECTOR, f"input[name='{name}']"
                    )
                    values[name] = self.driver.execute_script("return arguments[0].value;", inp) or ""
                except Exception:
                    pass

            # Mat-selects — check displayed value text
            select_labels = [
                "Ownership Status", "PO Type", "Default Currency",
                "Payment Terms", "Delivery Terms", "Mode Of Delivery",
                "Address Type", "Country", "State", "District", "Taluka", "Village",
                "Account Type", "Bank Proof",
            ]
            for label in select_labels:
                try:
                    select_el = self.driver.find_element(
                        By.XPATH,
                        f"//mat-label[contains(.,'{label}')]"
                        "/ancestor::mat-form-field//mat-select"
                    )
                    value_text = select_el.find_element(
                        By.CSS_SELECTOR, ".mat-mdc-select-value-text"
                    )
                    values[label] = value_text.text.strip()
                except Exception:
                    values[label] = ""

        except Exception as e:
            log.warning(f"Get form field values failed: {e}")

        return values
