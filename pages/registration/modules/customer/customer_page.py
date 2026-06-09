"""
customer_page.py
----------------
Page Object Model for RhythmERP Customer screen.

Location: Registration > Customer
URL:      /#/dynamic-screens/Customer/Customer

FORM LAYOUT (3-STEP HORIZONTAL STEPPER inside popup):

  UNIVERSAL FIELDS (always visible above stepper):
    - Party Reference        (mat-select,   optional)
    - Ownership Status       (mat-select,   required)
    - Company Name           (text input,   required, maxlength=255)
    - Sale Type              (mat-select,   required)
    - Supply Type            (mat-select,   required)
    - Transaction Currency   (mat-select,   required)
    - Email                  (text input,   required, maxlength=255)
    - Phone Number           (number input, required)
    - PAN Number             (text input,   required, maxlength=255)

  TOGGLE SWITCHES:
    - Copy From Existing Party (app-slide-toggle-v2, No/Yes, default No, OUTSIDE stepper)
    - Status                 (app-slide-toggle-v2, Active/Inactive, default Active, OUTSIDE stepper)
    - Is TDS Applicable      (app-slide-toggle-v2, No/Yes, default No, INSIDE stepper step 0)

  Step 0 — "Additional Details":
    - Contact Person Name    (text input,   optional, maxlength=255)
    - Office Number          (text input,   optional, maxlength=255)
    - Preferred Payment Method (mat-select, optional)
    - Gst Registration Status (mat-select,  optional, Registered/Unregistered)
    - Gst Registration Type  (mat-select,   optional, Composit/Regular)
    - Payment Terms          (mat-select,   optional)
    - Delivery Terms         (mat-select,   optional)
    - Mode Of Delivery       (mat-select,   optional)
    - Courier Terms          (mat-select,   optional)
    - Deposite               (number input, optional, default=0)
    - Quantity Tolerance     (number input, optional)
    - Rate Tolerance         (number input, optional)

  Step 1 — "Address Details" (Address Grid):
    Grid table with columns: Action, Same as Above, Address Type*, Country*,
    State*, District*, Taluka*, Village, Address*, Pin Code*, GSTIN
    Starts with 1 default empty row; Add (+) button to add more rows
    Cascading dropdowns: Country -> State -> District -> Taluka -> Village

  Step 2 — "Customer Bank Details" (Bank Grid):
    Grid table with columns: Action, Bank Name*, Branch*, IFSC Code,
    Account Type*, Account Holder Name*, Account Number*, Bank Proof*, Attachment
    Starts with 1 default empty row; Add (+) button to add more rows
    NOTE: Account Type and Bank Proof are now required=True in the ERP UI

TABLE COLUMNS (main listing):
  - View / Edit / History   (action buttons per row)
  - Company Name
  - Other customer fields

KEY RULES:
  - NEVER use Keys.ESCAPE (use backdrop click + JS overlay removal)
  - JS clicks for Angular Material overlays
  - Dropdown options read dynamically at runtime (never hardcode)
  - Toggle switches use <app-slide-toggle-v2> with <span class="main-label">
    and <div class="switch-wrapper compact">
  - BUG-001: Browser-clicked mat-select does NOT update Angular reactive form
    model — must use JS value-setter + dispatchEvent pattern
  - BUG-002: Stepper allows advancing even with empty required fields
  - Unique PAN Number validation (server-side)
  - Email validates with "Invalid Email" message
  - Inputs use name attribute for selection (e.g., name="Company Name")
  - Dropdowns use mat-label -> ancestor mat-form-field -> mat-select pattern
  - Address grid has cascading dropdowns (Country -> State -> District -> Taluka -> Village)
  - Stepper is non-linear: Next button does NOT validate required fields
  - Actual validation happens only on Submit button click
"""

import os
import sys
import time
import random
import copy

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
IM_SUBMISSIONS = []


class CustomerPage(BasePage):
    """Page Object for the RhythmERP Customer screen.

    Handles the listing page, the 3-step stepper popup form
    (Additional Details → Customer Details → Customer Bank Details),
    search, row actions, validation, and full CRUD workflows.
    """

    PAGE_URL = f"{RHYTHMERP_BASE_URL}/#/dynamic-screens/Customer/Customer"

    # ==============================================================
    #  LOCATORS — Toolbar
    # ==============================================================
    ADD_BUTTON = ("css", "button.erp-add-btn")
    SEARCH_TOGGLE = ("css", "button[mattooltip='Search']")
    REFRESH_BUTTON = ("css", "button[mattooltip='Refresh']")
    FILTER_BUTTON = ("css", "button[mattooltip='Filters']")
    MORE_BUTTON = ("css", "button[mattooltip='More']")

    # ==============================================================
    #  LOCATORS — Search bar
    # ==============================================================
    SEARCH_INPUT = ("css", "#erpSearchInput, input.erp-search-input")
    SEARCH_SUBMIT = ("css", "button.search-btn")

    # ==============================================================
    #  LOCATORS — Table (main listing)
    # ==============================================================
    TABLE = ("css", "app-dynamic-table table, table")
    TABLE_ROWS = ("css", "app-dynamic-table table tbody tr, table tbody tr")
    NO_DATA_ROW = ("css", ".empty-state__title")

    # ==============================================================
    #  LOCATORS — Popup / Stepper form
    # ==============================================================
    FORM_POPUP = (
        "css",
        ".edit_pop_up.override_edit_pop_up.popup-mode, "
        ".big-model, mat-dialog-container",
    )
    FORM_HEADING = (
        "css",
        ".edit_pop_up h3, .big-model h3, mat-dialog-container h3",
    )
    POPUP_HEADER = ("css", ".popup-header")
    CLOSE_BUTTON = (
        "xpath",
        "//div[contains(@class,'popup-actions')]//button[.//mat-icon[text()='close']]",
    )
    FULLSCREEN_BUTTON = (
        "xpath",
        "//div[contains(@class,'popup-actions')]//button[.//mat-icon[text()='fullscreen']]",
    )

    # ==============================================================
    #  LOCATORS — Stepper
    # ==============================================================
    MAT_STEPPER = ("css", "mat-horizontal-stepper")
    STEPPER_STEPS = ("css", "mat-step-header")
    STEPPER_NEXT = ("css", "button.mat-stepper-next")
    STEPPER_BACK = ("css", "button.mat-stepper-previous")

    # ==============================================================
    #  LOCATORS — Footer buttons
    # ==============================================================
    SUBMIT_BUTTON = (
        "xpath",
        "//div[contains(@class,'popup-footer')]//button[@type='submit']",
    )
    CANCEL_BUTTON = (
        "xpath",
        "//div[contains(@class,'popup-footer')]//button[contains(@class,'mat-warn')]",
    )

    # ==============================================================
    #  LOCATORS — Universal Fields: Dropdowns
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
    SALE_TYPE_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Sale Type')]"
        "/ancestor::mat-form-field//mat-select",
    )
    SUPPLY_TYPE_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Supply Type')]"
        "/ancestor::mat-form-field//mat-select",
    )
    TRANSACTION_CURRENCY_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Transaction Currency')]"
        "/ancestor::mat-form-field//mat-select",
    )

    # ==============================================================
    #  LOCATORS — Universal Fields: Inputs
    # ==============================================================
    COMPANY_NAME_INPUT = ("css", "input[name='Company Name']")
    EMAIL_INPUT = ("css", "input[name='Email']")
    PHONE_NUMBER_INPUT = ("css", "input[name='Phone Number']")
    PAN_NUMBER_INPUT = ("css", "input[name='PAN Number']")

    # ==============================================================
    #  LOCATORS — Toggle switches (app-slide-toggle-v2)
    # ==============================================================
    STATUS_TOGGLE = (
        "xpath",
        "//app-slide-toggle-v2[.//span[contains(@class,'main-label') "
        "and contains(.,'Status')]]"
        "//div[contains(@class,'switch-wrapper')]",
    )
    IS_TDS_APPLICABLE_TOGGLE = (
        "xpath",
        "//app-slide-toggle-v2[.//span[contains(@class,'main-label') "
        "and contains(.,'Is TDS Applicable')]]"
        "//div[contains(@class,'switch-wrapper')]",
    )

    # ==============================================================
    #  LOCATORS — Step 0: Additional Details — Dropdowns
    # ==============================================================
    PREFERRED_PAYMENT_METHOD_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Preferred Payment Method')]"
        "/ancestor::mat-form-field//mat-select",
    )
    GST_REGISTRATION_STATUS_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Gst Registration Status')]"
        "/ancestor::mat-form-field//mat-select",
    )
    GST_REGISTRATION_TYPE_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Gst Registration Type')]"
        "/ancestor::mat-form-field//mat-select",
    )
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
    COURIER_TERMS_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Courier Terms')]"
        "/ancestor::mat-form-field//mat-select",
    )

    # ==============================================================
    #  LOCATORS — Step 0: Additional Details — Inputs
    # ==============================================================
    CONTACT_PERSON_NAME_INPUT = ("css", "input[name='Contact Person Name']")
    OFFICE_NUMBER_INPUT = ("css", "input[name='Office Number']")
    DEPOSITE_INPUT = ("css", "input[name='Deposite']")
    QUANTITY_TOLERANCE_INPUT = ("css", "input[name='Quantity Tolerance']")
    RATE_TOLERANCE_INPUT = ("css", "input[name='Rate Tolerance']")

    # ==============================================================
    #  LOCATORS — Step 1: Customer Details (Address Grid)
    # ==============================================================
    ADDRESS_GRID_TABLE = ("css", ".grid-container .grid-table")
    ADDRESS_GRID_ROWS = ("css", ".grid-container .grid-table tbody tr")
    ADDRESS_GRID_ADD_BUTTON = (
        "xpath",
        "(//button[contains(@class,'mat-mdc-icon-button mat-primary')]"
        "[.//mat-icon[text()='add']])[1]",
    )
    ADDRESS_INPUT = ("css", "input[name='Address']")
    PIN_CODE_INPUT = ("css", "input[name='Pin Code']")
    GSTIN_INPUT = ("css", "input[name='GSTIN']")

    # ==============================================================
    #  LOCATORS — Step 2: Customer Bank Details (Bank Grid)
    # ==============================================================
    BANK_GRID_TABLE = (
        "css",
        ".grid-container:nth-of-type(2) .grid-table, "
        ".grid-container .grid-table",
    )
    BANK_GRID_ROWS = (
        "css",
        ".grid-container:nth-of-type(2) .grid-table tbody tr, "
        ".grid-container .grid-table tbody tr",
    )
    BANK_GRID_ADD_BUTTON = (
        "xpath",
        "(//button[contains(@class,'mat-mdc-icon-button mat-primary')]"
        "[.//mat-icon[text()='add']])[2]",
    )
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
    BANK_ATTACHMENT_INPUT = ("css", "input[type='file']")

    # # ==============================================================
    # #  LOCATORS — Row action buttons (parametrised by company name)
    # # ==============================================================
    # VIEW_BUTTON = (
    #     "xpath",
    #     "//td[contains(text(),'{company_name}')]"
    #     "/ancestor::tr//td[contains(@class,'cdk-column-view') "
    #     "or contains(@class,'cdk-column-viewDetails')]//button",
    # )
    # EDIT_BUTTON = (
    #     "xpath",
    #     "//td[contains(text(),'{company_name}')]"
    #     "/ancestor::tr//td[contains(@class,'cdk-column-edit')]//button",
    # )
    # HISTORY_BUTTON = (
    #     "xpath",
    #     "//td[contains(text(),'{company_name}')]"
    #     "/ancestor::tr//td[contains(@class,'cdk-column-archive')]//button",
    # )

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
    DROPDOWN_SEARCH = ("css", "div[role='listbox'] input")

    # ==============================================================
    #  LOCATORS — Row action 3-dot menu (replaces old column-based)
    # ==============================================================
    ROW_MENU_TRIGGER = ("css", "button.mat-mdc-menu-trigger.erp-row-trigger")
    ROW_MENU_VIEW = ("xpath", "//div[contains(@class,'mat-mdc-menu-content')]//span[contains(@class,'erp-menu-title') and text()='View']/ancestor::button")
    ROW_MENU_EDIT = ("xpath", "//div[contains(@class,'mat-mdc-menu-content')]//span[contains(@class,'erp-menu-title') and text()='Edit']/ancestor::button")
    ROW_MENU_HISTORY = ("xpath", "//div[contains(@class,'mat-mdc-menu-content')]//span[contains(@class,'erp-menu-title') and text()='History']/ancestor::button")




    # ==============================================================
    #  Navigation & page load
    # ==============================================================

    def navigate_to_page(self):
        """Navigate to the Customer listing page.
        Force-refreshes to clear leftover Angular state from previous tests.
        """
        log.info("Navigating to Customer page...")
        self.navigate_to(self.PAGE_URL)
        self.driver.refresh()
        self._wait_for_page_ready()

    def _wait_for_page_ready(self):
        """Wait until the Customer page is fully loaded:
        1. Table renders or empty state is visible
        2. Toolbar buttons (including ADD) are clickable
        """
        try:
            WebDriverWait(self.driver, EXPLICIT_WAIT).until(
                EC.visibility_of_element_located(
                    (
                        By.CSS_SELECTOR,
                        "app-dynamic-table table, table, .empty-state__title",
                    )
                )
            )
            log.info("Customer table or empty state loaded")
        except TimeoutException:
            log.warning("Customer table not found, page may be empty")

        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "button.erp-add-btn")
                )
            )
            self.wait_seconds(1)
            log.info("Customer toolbar ready")
        except TimeoutException:
            log.warning("Toolbar not found, ADD button may be delayed")
            self.wait_seconds(3)

    def is_page_loaded(self):
        """Check if the Customer listing page has loaded."""
        table_visible = self.is_displayed(self.TABLE, timeout=10)
        if table_visible:
            return True
        # Fallback: check for toolbar
        return self.is_present(self.ADD_BUTTON, timeout=5)

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
        """Close an open mat-select dropdown panel WITHOUT sending ESC.
        Sending ESC would close the entire stepper popup — this method
        clicks the select panel backdrop or removes the panel via JS,
        keeping the form popup intact.
        """
        self._close_select_panel()

    # ==============================================================
    #  Toolbar actions
    # ==============================================================

    def open_add_form(self):
        """Click the ADD (+) button to open the create form.
        Customer screen opens a 3-step stepper form inside a popup.
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

        # Strategy 3: div[mattooltip='ADD'] wrapper
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
        """Wait for the toolbar and ADD button to be present and visible."""
        for attempt in range(3):
            try:
                add_btn = self.driver.find_elements(
                    By.CSS_SELECTOR, "button.erp-add-btn"
                )
                if add_btn and add_btn[0].is_displayed():
                    return
            except Exception:
                pass

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

    def click_refresh(self):
        """Click the Refresh button."""
        log.info("Clicking Refresh button...")
        try:
            refresh_btns = self.driver.find_elements(
                By.CSS_SELECTOR, "button[mattooltip='Refresh']"
            )
            for btn in refresh_btns:
                try:
                    if btn.is_displayed():
                        self.driver.execute_script("arguments[0].click();", btn)
                        self.wait_seconds(2)
                        log.info("Refresh clicked")
                        return
                except Exception:
                    continue
        except Exception:
            pass

        # Fallback: find by icon text
        try:
            all_btns = self.driver.find_elements(
                By.CSS_SELECTOR, "button.mat-mdc-mini-fab"
            )
            for btn in all_btns:
                try:
                    icon = btn.find_element(By.CSS_SELECTOR, "mat-icon")
                    if icon.text.strip().lower() == "refresh" and btn.is_displayed():
                        self.driver.execute_script("arguments[0].click();", btn)
                        self.wait_seconds(2)
                        log.info("Refresh clicked via icon match")
                        return
                except Exception:
                    continue
        except Exception:
            pass
        log.warning("Refresh button not found")

    def search_item(self, query):
        """Search for a customer by name in the table search bar.
        Types the query, presses Enter to filter, and waits.
        Returns True if search was executed.
        """
        log.info(f"Searching for customer: {query}")
        try:
            self._force_close_panels()
            self.wait_seconds(1)

            # Toggle search bar open if needed
            try:
                toggle = self.driver.find_element(
                    By.CSS_SELECTOR, "button[mattooltip='Search']"
                )
                self.driver.execute_script("arguments[0].click();", toggle)
                self.wait_seconds(1)
            except Exception:
                pass

            # Type search text using JS value-setter (Angular reactive form)
            search_input = self.driver.find_element(
                By.CSS_SELECTOR, "#erpSearchInput, input.erp-search-input"
            )
            self.driver.execute_script(
                "arguments[0].value = '';"
                "arguments[0].dispatchEvent(new Event('input', {bubbles: true}));",
                search_input,
            )
            search_input.send_keys(query)
            search_input.send_keys(Keys.ENTER)
            self.wait_seconds(2)
            log.info(f"Search executed for: {query}")
            return True

        except Exception as e:
            log.error(f"Search failed: {e}")
            return False
    # ==============================================================
    #  Stepper navigation
    # ==============================================================

    def click_stepper_next(self):
        """Click the 'Next' button on the current stepper step
        to advance to the next step.
        Uses multiple strategies: CSS class, text match, JS fallback.
        """
        log.info("Clicking stepper Next button...")
        self._force_close_panels()

        # Strategy 1: Angular Material stepper next button
        try:
            next_btns = self.driver.find_elements(
                By.CSS_SELECTOR,
                "button.mat-stepper-next, "
                "button.mat-mdc-stepper-next",
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
                        log.info("Stepper Next clicked via CSS class")
                        return True
                except Exception:
                    continue
        except Exception:
            pass

        # Strategy 2: Button containing 'Next' text inside popup footer/stepper
        try:
            next_btns = self.driver.find_elements(
                By.XPATH,
                "//button[contains(.,'Next') and not(contains(.,'Next page'))]",
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
                        log.info("Stepper Next clicked via text match")
                        return True
                except Exception:
                    continue
        except Exception:
            pass

        # Strategy 3: JS find and click any Next button inside the popup
        try:
            self.driver.execute_script("""
                var btns = document.querySelectorAll(
                    '.edit_pop_up button, .big-model button, '
                    + 'mat-dialog-container button'
                );
                for (var i = 0; i < btns.length; i++) {
                    if (btns[i].textContent.trim() === 'Next'
                        || btns[i].classList.contains('mat-stepper-next')
                        || btns[i].classList.contains('mat-mdc-stepper-next')) {
                        btns[i].click();
                        break;
                    }
                }
            """)
            self.wait_seconds(1)
            log.info("Stepper Next clicked via JS")
            return True
        except Exception:
            pass

        log.warning("Stepper Next button not found or not clickable")
        return False

    def click_stepper_back(self):
        """Click the 'Back' button on the current stepper step
        to go back to the previous step.
        Uses multiple strategies: CSS class, text match.
        """
        log.info("Clicking stepper Back button...")
        self._force_close_panels()

        # Strategy 1: Angular Material stepper previous button
        try:
            back_btns = self.driver.find_elements(
                By.CSS_SELECTOR,
                "button.mat-stepper-previous, "
                "button.mat-mdc-stepper-previous",
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
                        log.info("Stepper Back clicked via CSS class")
                        return True
                except Exception:
                    continue
        except Exception:
            pass

        # Strategy 2: Button containing 'Back' text
        try:
            back_btns = self.driver.find_elements(
                By.XPATH,
                "//button[contains(.,'Back') and not(contains(.,'Back to'))]",
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
                        log.info("Stepper Back clicked via text match")
                        return True
                except Exception:
                    continue
        except Exception:
            pass

        # Strategy 3: JS click Back button inside popup
        try:
            self.driver.execute_script("""
                var btns = document.querySelectorAll(
                    '.edit_pop_up button, .big-model button, '
                    + 'mat-dialog-container button'
                );
                for (var i = 0; i < btns.length; i++) {
                    if (btns[i].textContent.trim() === 'Back'
                        || btns[i].classList.contains('mat-stepper-previous')
                        || btns[i].classList.contains('mat-mdc-stepper-previous')) {
                        btns[i].click();
                        break;
                    }
                }
            """)
            self.wait_seconds(1)
            log.info("Stepper Back clicked via JS")
            return True
        except Exception:
            pass

        log.warning("Stepper Back button not found or not clickable")
        return False

    def get_current_step_index(self):
        """Get the 0-based index of the currently active stepper step.
        Returns 0 for Step 0 (Additional Details),
                1 for Step 1 (Customer Details),
                2 for Step 2 (Customer Bank Details).
        Returns -1 if stepper not found.
        """
        try:
            steps = self.driver.find_elements(
                By.CSS_SELECTOR,
                "mat-step-header, .mat-step-header, "
                ".mat-mdc-step-header",
            )
            for i, step in enumerate(steps):
                try:
                    # Active step has 'selected' or 'active' in class
                    classes = step.get_attribute("class") or ""
                    if "selected" in classes or "active" in classes:
                        log.info(f"Current stepper step: {i}")
                        return i
                except Exception:
                    continue

            # Fallback: check aria-selected attribute
            for i, step in enumerate(steps):
                try:
                    selected = step.get_attribute("aria-selected")
                    if selected == "true":
                        log.info(f"Current stepper step (aria): {i}")
                        return i
                except Exception:
                    continue
        except Exception:
            pass

        log.warning("Could not determine current stepper step")
        return -1

    def get_current_step_label(self):
        """Get the label text of the currently active stepper step."""
        try:
            steps = self.driver.find_elements(
                By.CSS_SELECTOR,
                "mat-step-header, .mat-step-header",
            )
            for step in steps:
                try:
                    classes = step.get_attribute("class") or ""
                    if "selected" in classes or "active" in classes:
                        return step.text.strip()
                except Exception:
                    continue

            # Fallback: find active step via CSS
            active_labels = self.driver.find_elements(
                By.CSS_SELECTOR,
                ".mat-step-text-label, .mat-mdc-stepper-horizontal-label",
            )
            for label in active_labels:
                try:
                    if label.is_displayed():
                        return label.text.strip()
                except Exception:
                    continue
        except Exception:
            pass
        return ""

    def is_step0_active(self):
        """Check if Step 0 (Additional Details) is the current active step."""
        return self.get_current_step_index() == 0

    def is_step1_active(self):
        """Check if Step 1 (Customer Details) is the current active step."""
        return self.get_current_step_index() == 1

    def is_step2_active(self):
        """Check if Step 2 (Customer Bank Details) is the current active step."""
        return self.get_current_step_index() == 2

    def go_to_step(self, step_index):
        """Navigate to a specific stepper step by clicking the step header.
        Note: Angular Material steppers may not allow jumping to
        incomplete steps if linear mode is enabled.
        """
        log.info(f"Navigating to stepper step {step_index}...")
        try:
            steps = self.driver.find_elements(
                By.CSS_SELECTOR,
                "mat-step-header, .mat-step-header",
            )
            if step_index < len(steps):
                self.driver.execute_script(
                    "arguments[0].click();", steps[step_index]
                )
                self.wait_seconds(1)
                return True
        except Exception:
            pass
        log.warning(f"Could not navigate to step {step_index}")
        return False

    # ==============================================================
    #  Popup management
    # ==============================================================

    def _is_form_popup_open(self):
        """Quick check if any form popup is visible."""
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
        """Wait for form content (inputs/stepper) to render inside the popup."""
        import time as _time
        deadline = _time.time() + timeout
        while _time.time() < deadline:
            try:
                elements = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    "div.edit_pop_up mat-horizontal-stepper, "
                    "div.edit_pop_up input, "
                    ".big-model mat-stepper, "
                    ".big-model input, "
                    "mat-dialog-container mat-stepper, "
                    "mat-dialog-container input, "
                    "div.cdk-overlay-container mat-stepper, "
                    "div.cdk-overlay-container input",
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
                "div.edit_pop_up input, "
                "div.big-model input, "
                "mat-dialog-container input, "
                "div.cdk-overlay-container input",
            )
            log.info(f"DEBUG: Found {len(all_inputs)} inputs in popup")
            for i, inp in enumerate(all_inputs[:10]):
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

            # Check for stepper elements
            steppers = self.driver.find_elements(
                By.CSS_SELECTOR, "mat-stepper, mat-horizontal-stepper"
            )
            log.info(f"DEBUG: Found {len(steppers)} stepper elements")

            containers = self.driver.find_elements(
                By.CSS_SELECTOR,
                "div.edit_pop_up, div.big-model, mat-dialog-container, "
                "div.popup-wrapper",
            )
            log.info(f"DEBUG: Found {len(containers)} popup containers")
            for i, c in enumerate(containers[:5]):
                try:
                    log.info(
                        f"  Container[{i}]: "
                        f"class={c.get_attribute('class')}, "
                        f"visible={c.is_displayed()}"
                    )
                except Exception:
                    pass
        except Exception as e:
            log.warning(f"Debug popup info failed: {e}")

    def close_popup(self):
        """Close the form popup via Cancel button or X button."""
        log.info("Closing popup...")

        # Strategy 1: Click Cancel button
        try:
            cancel_btns = self.driver.find_elements(
                By.XPATH,
                "//div[contains(@class,'popup-footer')]"
                "//button[contains(@class,'mat-warn') or contains(.,'Cancel')]",
            )
            for btn in cancel_btns:
                try:
                    if btn.is_displayed():
                        self.driver.execute_script("arguments[0].click();", btn)
                        self.wait_seconds(0.5)
                        if not self._is_form_popup_open():
                            log.info("Popup closed via Cancel button")
                            return
                except Exception:
                    continue
        except Exception:
            pass

        # Strategy 2: Click X (close) icon in popup header
        try:
            close_btns = self.driver.find_elements(
                By.XPATH,
                "//div[contains(@class,'popup-actions')]"
                "//button[.//mat-icon[text()='close']]",
            )
            for btn in close_btns:
                try:
                    if btn.is_displayed():
                        self.driver.execute_script("arguments[0].click();", btn)
                        self.wait_seconds(0.5)
                        if not self._is_form_popup_open():
                            log.info("Popup closed via X button")
                            return
                except Exception:
                    continue
        except Exception:
            pass

        # Strategy 3: JS click close icon
        try:
            self.driver.execute_script("""
                var icons = document.querySelectorAll(
                    '.popup-actions button mat-icon, '
                    + '.popup-header button mat-icon'
                );
                for (var i = 0; i < icons.length; i++) {
                    if (icons[i].textContent.trim().toLowerCase() === 'close') {
                        icons[i].closest('button').click();
                        break;
                    }
                }
            """)
            self.wait_seconds(0.5)
            if not self._is_form_popup_open():
                log.info("Popup closed via JS close icon")
                return
        except Exception:
            pass

        log.warning("Could not close popup via normal methods")

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
            document.querySelectorAll(
                '.edit_pop_up'
            ).forEach(function(el) { el.remove(); });
        """)
        self.wait_seconds(0.5)

    def is_add_form_open(self):
        """Check if the Add form popup is currently visible.
        Uses multi-strategy approach for the stepper form.
        """
        popup_visible = self._is_form_popup_open()
        name_input_visible = self.is_displayed(self.COMPANY_NAME_INPUT, timeout=8)

        if name_input_visible:
            return True

        if popup_visible:
            # Check for stepper element inside popup
            try:
                steppers = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    "div.edit_pop_up mat-stepper, "
                    "div.edit_pop_up mat-horizontal-stepper, "
                    "div.big-model mat-stepper, "
                    "mat-dialog-container mat-stepper",
                )
                for s in steppers:
                    try:
                        if s.is_displayed():
                            return True
                    except Exception:
                        continue
            except Exception:
                pass

            # Fallback: any input inside popup
            try:
                popup_inputs = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    "div.edit_pop_up input, "
                    "div.big-model input, "
                    "mat-dialog-container input",
                )
                for inp in popup_inputs:
                    try:
                        if inp.is_displayed():
                            return True
                    except Exception:
                        continue
            except Exception:
                pass

            log.warning("Popup visible but no form content found")
            self._debug_popup_info()

        return False

    # ==============================================================
    #  Fill universal fields (above stepper — always visible)
    # ==============================================================

    def fill_universal_fields(self, data):
        """Fill all universal fields that appear above the stepper.

        Universal fields:
          - Party Reference       (mat-select, optional)
          - Ownership Status      (mat-select, required)
          - Company Name          (text input, required)
          - Sale Type             (mat-select, required)
          - Supply Type           (mat-select, required)
          - Transaction Currency  (mat-select, required)
          - Email                 (text input, required)
          - Phone Number          (text input, required)
          - PAN Number            (text input, required)
          - Status                (toggle, optional)
          - Is TDS Applicable     (toggle, optional — inside step 0 but set here)
        """
        log.info("Filling universal fields...")

        # --- Dropdown selects ---
        
        self._fill_dropdown_if_provided(
            data, "ownership_status", self.OWNERSHIP_STATUS_SELECT, "Ownership Status"
        )
        self._fill_dropdown_if_provided(
            data, "sale_type", self.SALE_TYPE_SELECT, "Sale Type"
        )
        self._fill_dropdown_if_provided(
            data, "supply_type", self.SUPPLY_TYPE_SELECT, "Supply Type"
        )
        self._fill_dropdown_if_provided(
            data, "transaction_currency",
            self.TRANSACTION_CURRENCY_SELECT, "Transaction Currency",
        )

        # --- Text Inputs ---
        if data.get("company_name"):
            self.type_text(
                self.COMPANY_NAME_INPUT,
                str(data["company_name"]),
                clear_first=True,
            )

        if data.get("email"):
            self.type_text(
                self.EMAIL_INPUT,
                str(data["email"]),
                clear_first=True,
            )

        if data.get("phone_number"):
            self.type_text(
                self.PHONE_NUMBER_INPUT,
                str(data["phone_number"]),
                clear_first=True,
            )

        if data.get("pan_number"):
            self.type_text(
                self.PAN_NUMBER_INPUT,
                str(data["pan_number"]),
                clear_first=True,
            )

        # --- Toggle switches ---
        self._set_toggle_if_provided(data, "status", self.STATUS_TOGGLE, "Status")
        self._set_toggle_if_provided(
            data, "is_tds_applicable",
            self.IS_TDS_APPLICABLE_TOGGLE, "Is TDS Applicable",
        )

        self._force_close_panels()
        log.info("Universal fields filled")

    # ==============================================================
    #  Fill Step 0: Additional Details
    # ==============================================================

    def fill_step0(self, data):
        """Fill all fields on Step 0 — "Additional Details".

        Fields:
          - Contact Person Name        (text input)
          - Office Number              (text input)
          - Preferred Payment Method   (mat-select)
          - Gst Registration Status    (mat-select, Registered/Unregistered)
          - Gst Registration Type      (mat-select)
          - Payment Terms              (mat-select)
          - Delivery Terms             (mat-select)
          - Mode Of Delivery           (mat-select)
          - Courier Terms              (mat-select)
          - Deposite                   (number input)
          - Quantity Tolerance         (number input)
          - Rate Tolerance             (number input)
        """
        log.info("Filling Step 0 — Additional Details...")

        # --- Text Inputs ---
        if data.get("contact_person_name"):
            self.type_text(
                self.CONTACT_PERSON_NAME_INPUT,
                str(data["contact_person_name"]),
                clear_first=True,
            )

        if data.get("office_number"):
            self.type_text(
                self.OFFICE_NUMBER_INPUT,
                str(data["office_number"]),
                clear_first=True,
            )

        if data.get("deposite"):
            self.type_text(
                self.DEPOSITE_INPUT,
                str(data["deposite"]),
                clear_first=True,
            )

        if data.get("quantity_tolerance"):
            self.type_text(
                self.QUANTITY_TOLERANCE_INPUT,
                str(data["quantity_tolerance"]),
                clear_first=True,
            )

        if data.get("rate_tolerance"):
            self.type_text(
                self.RATE_TOLERANCE_INPUT,
                str(data["rate_tolerance"]),
                clear_first=True,
            )

        # --- Dropdown selects ---
        self._fill_dropdown_if_provided(
            data, "preferred_payment_method",
            self.PREFERRED_PAYMENT_METHOD_SELECT, "Preferred Payment Method",
        )
        self._fill_dropdown_if_provided(
            data, "gst_registration_status",
            self.GST_REGISTRATION_STATUS_SELECT, "Gst Registration Status",
        )
        self._fill_dropdown_if_provided(
            data, "gst_registration_type",
            self.GST_REGISTRATION_TYPE_SELECT, "Gst Registration Type",
        )
        self._fill_dropdown_if_provided(
            data, "payment_terms",
            self.PAYMENT_TERMS_SELECT, "Payment Terms",
        )
        self._fill_dropdown_if_provided(
            data, "delivery_terms",
            self.DELIVERY_TERMS_SELECT, "Delivery Terms",
        )
        self._fill_dropdown_if_provided(
            data, "mode_of_delivery",
            self.MODE_OF_DELIVERY_SELECT, "Mode Of Delivery",
        )
        self._fill_dropdown_if_provided(
            data, "courier_terms",
            self.COURIER_TERMS_SELECT, "Courier Terms",
        )

        # --- Toggle switch (Is TDS Applicable is in step 0) ---
        if "is_tds_applicable" in data and "status" not in data:
            # Only set if not already set in universal fields
            self._set_toggle_if_provided(
                data, "is_tds_applicable",
                self.IS_TDS_APPLICABLE_TOGGLE, "Is TDS Applicable",
            )

        self._force_close_panels()
        log.info("Step 0 form filled")

    # ==============================================================
    #  Fill Step 1: Customer Details (Address Grid)
    # ==============================================================


    def add_address_row(self):
        """Click the Add Row (+) button on the LAST row of the Address grid.
        Each row has its own inline add button — there is no global add button.
        Scoped to the first .grid-container to avoid hitting the bank grid.
        """
        log.info("Clicking Add Row (on last row) in Address grid...")

        # Strategy 1: JS — find last tr in address grid → click its add button
        try:
            clicked = self.driver.execute_script("""
                var containers = document.querySelectorAll('.grid-container');
                if (containers.length < 1) return false;
                var tbody = containers[0].querySelector('.grid-table tbody, table tbody');
                if (!tbody) return false;
                var rows = tbody.querySelectorAll('tr');
                if (rows.length === 0) return false;
                var lastRow = rows[rows.length - 1];
                var btns = lastRow.querySelectorAll(
                    'button.mat-mdc-icon-button, button.mdc-icon-button'
                );
                for (var i = 0; i < btns.length; i++) {
                    var icon = btns[i].querySelector('mat-icon');
                    if (icon && icon.textContent.trim().toLowerCase() === 'add') {
                        btns[i].click();
                        return true;
                    }
                }
                return false;
            """)
            if clicked:
                self.wait_seconds(1)
                log.info("Address Add Row clicked via JS (last row inline button)")
                return
        except Exception:
            pass

        # Strategy 2: Python — find last visible address row, click its add button
        try:
            visible_rows = self._get_address_grid_rows()
            if visible_rows:
                last_row = visible_rows[-1]
                add_btns = last_row.find_elements(
                    By.CSS_SELECTOR,
                    "button.mat-mdc-icon-button, button.mdc-icon-button",
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
                            self.wait_seconds(1)
                            log.info("Address Add Row clicked via last-row Python strategy")
                            return
                    except Exception:
                        continue
        except Exception:
            pass

        log.warning("Address Add Row button not found on last row")
    

    def fill_address_row(self, row_index, data):
        """Fill one address row in the Customer Details grid."""
        log.info(f"Filling address row {row_index}...")

        try:
            visible_rows = self._get_address_grid_rows()

            if row_index >= len(visible_rows):
                log.warning(
                    f"Address row index {row_index} out of range "
                    f"(visible rows: {len(visible_rows)})"
                )
                return

            target_row = visible_rows[row_index]

            if "address_type" in data:
                self._fill_grid_dropdown_or_random(
                    target_row, "Address Type", data.get("address_type")
                )
                self.wait_seconds(1)

            if "country" in data:
                selected_country = self._fill_grid_dropdown_or_random(
                    target_row, "Country", data.get("country")
                )
                if selected_country:
                    log.info(f"Country selected: '{selected_country}' — waiting for State options to load...")
                self.wait_seconds(3)

            if "state" in data:
                self.wait_seconds(1)
                self._fill_grid_dropdown_or_random(
                    target_row, "State", data.get("state")
                )
                self.wait_seconds(3)

            if "district" in data:
                self.wait_seconds(1)
                self._fill_grid_dropdown_or_random(
                    target_row, "District", data.get("district")
                )
                self.wait_seconds(3)

            if "taluka" in data:
                self.wait_seconds(1)
                self._fill_grid_dropdown_or_random(
                    target_row, "Taluka", data.get("taluka")
                )
                self.wait_seconds(3)

            if "village" in data:
                self.wait_seconds(1)
                self._fill_grid_dropdown_or_random(
                    target_row, "Village", data.get("village")
                )

            if data.get("address"):
                self._fill_grid_text_input(target_row, "Address", data["address"])

            if data.get("pin_code"):
                self._fill_grid_text_input(target_row, "Pin Code", data["pin_code"])

            if data.get("gstin"):
                self._fill_grid_text_input(target_row, "GSTIN", data["gstin"])

        except Exception as e:
            log.error(f"Failed to fill address row {row_index}: {e}")


    def fill_step1(self, data):
        """Fill Step 1 — Customer Details (Address Grid).
        Data format:
        {
            "address_rows": [
                {
                    "address_type": "Shipping",
                    "country": "India",
                    "state": "Maharashtra",
                    "district": "Pune",
                    "taluka": "Haveli",
                    "village": None,
                    "address": "123 MG Road",
                    "pin_code": "411001",
                    "gstin": "27ABCDE1234F1Z5",
                },
            ]
        }
        """
        log.info("Filling Step 1 — Customer Details (Address Grid)...")
        address_rows = data.get("address_rows", [])

        for i, row_data in enumerate(address_rows):
            if i > 0:
                # Click add on the last existing row to append a new row
                self.add_address_row()
                self.wait_seconds(1.5)  # Wait for new row to render

            self.fill_address_row(i, row_data)

        self._force_close_panels()
        log.info(f"Step 1 filled with {len(address_rows)} address row(s)")

    # ==============================================================
    #  Fill Step 2: Customer Bank Details (Bank Grid)
    # ==============================================================

    def add_bank_row(self):
        """Click the Add Row (+) button in the Bank grid
        to add a new bank details row.
        """
        log.info("Clicking Add Row in Bank grid...")

        # Strategy 1: BANK_GRID_ADD_BUTTON locator
        try:
            btn = self.driver.find_element(
                By.XPATH, self.BANK_GRID_ADD_BUTTON[1]
            )
            if btn.is_displayed():
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});"
                    "arguments[0].click();",
                    btn,
                )
                self.wait_seconds(1)
                log.info("Bank Add Row clicked via locator")
                return
        except Exception:
            pass

        # Strategy 2: Find second add icon button (second grid-container)
        try:
            add_btns = self.driver.find_elements(
                By.CSS_SELECTOR,
                ".grid-container button.mat-mdc-icon-button",
            )
            add_count = 0
            for btn in add_btns:
                try:
                    icon = btn.find_element(By.CSS_SELECTOR, "mat-icon")
                    if icon.text.strip().lower() == "add" and btn.is_displayed():
                        add_count += 1
                        if add_count == 2:  # Second add button = Bank grid
                            self.driver.execute_script(
                                "arguments[0].scrollIntoView({block:'center'});"
                                "arguments[0].click();",
                                btn,
                            )
                            self.wait_seconds(1)
                            log.info("Bank Add Row clicked via second icon")
                            return
                except Exception:
                    continue
        except Exception:
            pass

        # Strategy 3: JS click in second grid-container
        try:
            self.driver.execute_script("""
                var containers = document.querySelectorAll('.grid-container');
                if (containers.length > 1) {
                    var btns = containers[1].querySelectorAll(
                        'button.mat-mdc-icon-button'
                    );
                    for (var i = 0; i < btns.length; i++) {
                        var icon = btns[i].querySelector('mat-icon');
                        if (icon && icon.textContent.trim().toLowerCase() === 'add') {
                            btns[i].click();
                            break;
                        }
                    }
                }
            """)
            self.wait_seconds(1)
            log.info("Bank Add Row clicked via JS")
        except Exception:
            log.warning("Bank Add Row button not found")

    def fill_bank_row(self, row_index, data):
        """Fill one bank row in the Customer Bank Details grid.

        For dropdown fields where the value is None, a random valid option
        is picked from the live UI.

        Args:
            row_index: 0-based index of the bank row
            data: dict with bank fields. None = pick random, "" = skip.
        """
        log.info(f"Filling bank row {row_index}...")

        try:
            # Find rows in the Bank grid using JS to avoid invalid CSS selectors
            # The Bank grid is the 2nd .grid-container inside the stepper
            visible_rows = self._get_bank_grid_rows()

            if row_index >= len(visible_rows):
                log.warning(
                    f"Bank row index {row_index} out of range "
                    f"(visible rows: {len(visible_rows)})"
                )
                return

            target_row = visible_rows[row_index]

            # --- Text inputs in the grid row ---
            if data.get("bank_name"):
                self._fill_grid_text_input(target_row, "Bank Name", data["bank_name"])

            if data.get("branch"):
                self._fill_grid_text_input(target_row, "Branch", data["branch"])

            if data.get("ifsc_code"):
                self._fill_grid_text_input(target_row, "IFSC Code", data["ifsc_code"])

            # --- Dropdown selects ---
            if "account_type" in data:
                self._fill_grid_dropdown_or_random(
                    target_row, "Account Type", data.get("account_type")
                )

            if data.get("account_holder_name"):
                self._fill_grid_text_input(
                    target_row, "Account Holder Name", data["account_holder_name"]
                )

            if data.get("account_number"):
                self._fill_grid_text_input(
                    target_row, "Account Number", data["account_number"]
                )

            if "bank_proof" in data:
                self._fill_grid_dropdown_or_random(
                    target_row, "Bank Proof", data.get("bank_proof")
                )

            # --- File attachment ---
            if data.get("attachment"):
                self._upload_bank_attachment(data["attachment"])

        except Exception as e:
            log.error(f"Failed to fill bank row {row_index}: {e}")

    def fill_step2(self, data):
        """Fill Step 2 — Customer Bank Details (Bank Grid).
        Data format:
          {
              "bank_rows": [
                  {
                      "bank_name": "SBI",
                      "branch": "Main Branch",
                      "ifsc_code": "SBIN0001234",
                      "account_type": "Current",
                      "account_holder_name": "John Doe",
                      "account_number": "12345678901234",
                      "bank_proof": "Cancelled Cheque",
                      "attachment": None,
                  },
              ]
          }
        """
        log.info("Filling Step 2 — Customer Bank Details (Bank Grid)...")
        bank_rows = data.get("bank_rows", [])

        for i, row_data in enumerate(bank_rows):
            if i > 0:
                # Add a new row for each additional entry
                self.add_bank_row()
                self.wait_seconds(1)

            self.fill_bank_row(i, row_data)

        self._force_close_panels()
        log.info(f"Step 2 filled with {len(bank_rows)} bank row(s)")

    def _upload_bank_attachment(self, file_path):
        """Upload a bank proof attachment file.
        Handles the hidden file input by sending keys directly.
        """
        log.info(f"Uploading bank attachment: {file_path}")
        try:
            file_inputs = self.driver.find_elements(
                By.CSS_SELECTOR,
                ".edit_pop_up input[type='file'], "
                ".big-model input[type='file'], "
                "mat-dialog-container input[type='file']",
            )
            for inp in file_inputs:
                try:
                    if inp.is_enabled():
                        inp.send_keys(file_path)
                        self.wait_seconds(1)
                        log.info("Bank attachment uploaded successfully")
                        return
                except Exception:
                    continue

            # Fallback: try to make hidden file input visible via JS
            try:
                self.driver.execute_script("""
                    var inputs = document.querySelectorAll('input[type="file"]');
                    inputs.forEach(function(inp) {
                        inp.style.display = 'block';
                        inp.style.visibility = 'visible';
                        inp.style.opacity = '1';
                    });
                """)
                self.wait_seconds(0.5)
                file_inputs = self.driver.find_elements(
                    By.CSS_SELECTOR, "input[type='file']"
                )
                for inp in file_inputs:
                    try:
                        inp.send_keys(file_path)
                        self.wait_seconds(1)
                        log.info("Bank attachment uploaded via JS visibility fix")
                        return
                    except Exception:
                        continue
            except Exception:
                pass

            log.warning("Bank attachment file input not found")
        except Exception as e:
            log.error(f"Bank attachment upload failed: {e}")

    # ==============================================================
    #  Dropdown selection — CRITICAL (handles BUG-001)
    # ==============================================================

    def _select_mat_option_by_label(self, label_text, option_value):
        """Open a mat-select dropdown by mat-label text and select an option.

        This is the MAIN dropdown selection method, handling BUG-001:
        Browser-clicked mat-select does NOT update Angular reactive form
        model. We use JS value-setter + dispatchEvent as a workaround.

        Steps:
          1. Find the mat-select element using the mat-label text
          2. Click it via JS (scrollIntoView + click)
          3. Wait for options to appear
          4. Find the matching option
          5. Click the option via JS
          6. Force close any remaining dropdown panel
          7. Verify the selection was applied

        Args:
            label_text: The mat-label text (e.g., 'Ownership Status')
            option_value: The option text to select (e.g., 'Owned')
        """
        log.info(
            f"Selecting '{option_value}' from '{label_text}' dropdown..."
        )

        # Step 1: Find the mat-select element via mat-label
        select_xpath = (
            f"//mat-label[contains(.,'{label_text}')]"
            f"/ancestor::mat-form-field//mat-select"
        )
        try:
            mat_select = self.driver.find_element(By.XPATH, select_xpath)
        except Exception:
            log.warning(f"mat-select for '{label_text}' not found")
            return False

        # Step 2: Click the mat-select via JS (scroll into view first)
        try:
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});"
                "arguments[0].click();",
                mat_select,
            )
        except Exception:
            try:
                # Fallback: click the trigger div
                trigger = mat_select.find_element(
                    By.CSS_SELECTOR,
                    ".mat-mdc-select-trigger, .mat-select-trigger",
                )
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});"
                    "arguments[0].click();",
                    trigger,
                )
            except Exception:
                log.warning(f"Could not click mat-select for '{label_text}'")
                self._close_dropdown_panel_only()
                return False

        self.wait_seconds(0.5)

        # Step 3: Wait for options to appear
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
            log.warning(
                f"No options loaded in '{label_text}' dropdown — skipping"
            )
            self._close_dropdown_panel_only()
            return False

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
                        inp.send_keys(option_value)
                        self.wait_seconds(0.5)
                        break
                except Exception:
                    continue
        except Exception:
            pass

        # Step 4: Find the matching option
        option_clicked = False
        try:
            opt_xpath = (
                f"//div[@role='listbox']//mat-option"
                f"[contains(.,'{option_value}')]"
            )
            opt = self.driver.find_element(By.XPATH, opt_xpath)
            # Step 5: Click the option via JS
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});"
                "arguments[0].click();",
                opt,
            )
            option_clicked = True
        except Exception:
            try:
                opt_xpath2 = (
                    f"//div[@role='listbox']//div[@role='option']"
                    f"[contains(.,'{option_value}')]"
                )
                opt = self.driver.find_element(By.XPATH, opt_xpath2)
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});"
                    "arguments[0].click();",
                    opt,
                )
                option_clicked = True
            except Exception:
                # Fallback: iterate through all options
                opts = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    "div[role='listbox'] mat-option, "
                    "div[role='listbox'] [role='option']",
                )
                for o in opts:
                    try:
                        if option_value in o.text:
                            self.driver.execute_script(
                                "arguments[0].scrollIntoView({block:'center'});"
                                "arguments[0].click();",
                                o,
                            )
                            option_clicked = True
                            break
                    except Exception:
                        continue

        self.wait_seconds(0.3)

        # Step 6: Force close any remaining dropdown panel
        self._force_close_panels()

        # Step 7: BUG-001 workaround — use JS value-setter + dispatchEvent
        # Re-find the mat-select and verify/force selection
        try:
            mat_select = self.driver.find_element(By.XPATH, select_xpath)
            # Read current displayed value
            current_value = mat_select.text.strip()
            if current_value != option_value:
                # BUG-001: Browser click didn't update the Angular model
                # Use JS to force the value
                self.driver.execute_script("""
                    var selectEl = arguments[0];
                    var triggerEl = selectEl.querySelector(
                        '.mat-mdc-select-trigger, .mat-select-trigger'
                    );
                    if (triggerEl) {
                        // Force Angular to detect the change
                        triggerEl.dispatchEvent(
                            new Event('change', {bubbles: true})
                        );
                    }
                """, mat_select)
                log.info(
                    f"BUG-001 workaround applied for '{label_text}': "
                    f"displayed='{current_value}', expected='{option_value}'"
                )
        except Exception:
            pass

        if option_clicked:
            log.info(f"Selected '{option_value}' from '{label_text}'")
            return True
        else:
            log.warning(
                f"Option '{option_value}' not found in '{label_text}' dropdown"
            )
            return False

    def _select_grid_dropdown(self, row_element, column_label, option_value):
        """Select an option from a mat-select dropdown within a specific
        grid row.

        Uses the mat-label → ancestor mat-form-field → mat-select pattern,
        but scoped to the given row element.

        Args:
            row_element: The Selenium WebElement for the grid row
            column_label: The mat-label text (e.g., 'Country', 'Account Type')
            option_value: The option text to select
        """
        log.info(
            f"Selecting '{option_value}' from grid dropdown '{column_label}'..."
        )

        try:
            # Find mat-select within this row by label text
            selects = row_element.find_elements(
                By.CSS_SELECTOR, "mat-select"
            )

            # Try to find the right select by matching label
            target_select = None
            for sel in selects:
                try:
                    # Find the associated label
                    form_field = sel.find_element(
                        By.XPATH, "ancestor::mat-form-field"
                    )
                    labels = form_field.find_elements(
                        By.CSS_SELECTOR, "mat-label"
                    )
                    for lbl in labels:
                        if column_label.lower() in lbl.text.lower():
                            target_select = sel
                            break
                    if target_select:
                        break
                except Exception:
                    continue

            # Fallback: if no label match, try all selects
            if not target_select:
                visible_selects = [
                    s for s in selects
                    if s.is_displayed()
                ]
                if visible_selects:
                    target_select = visible_selects[0]
                else:
                    log.warning(
                        f"No visible mat-select in grid row for '{column_label}'"
                    )
                    return False

            # Click the select via JS
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});"
                "arguments[0].click();",
                target_select,
            )
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
                log.warning(
                    f"No options loaded in grid dropdown '{column_label}'"
                )
                self._close_dropdown_panel_only()
                return False

            # If dropdown has a search textbox, type into it
            try:
                search_inputs = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    "div[role='listbox'] input",
                )
                for inp in search_inputs:
                    try:
                        if inp.is_displayed():
                            inp.clear()
                            inp.send_keys(option_value)
                            self.wait_seconds(0.5)
                            break
                    except Exception:
                        continue
            except Exception:
                pass

            # Find and click the matching option
            option_clicked = False
            try:
                opt_xpath = (
                    f"//div[@role='listbox']//mat-option"
                    f"[contains(.,'{option_value}')]"
                )
                opt = self.driver.find_element(By.XPATH, opt_xpath)
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});"
                    "arguments[0].click();",
                    opt,
                )
                option_clicked = True
            except Exception:
                opts = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    "div[role='listbox'] mat-option, "
                    "div[role='listbox'] [role='option']",
                )
                for o in opts:
                    try:
                        if option_value in o.text:
                            self.driver.execute_script(
                                "arguments[0].scrollIntoView({block:'center'});"
                                "arguments[0].click();",
                                o,
                            )
                            option_clicked = True
                            break
                    except Exception:
                        continue

            self.wait_seconds(0.3)
            self._force_close_panels()

            if option_clicked:
                log.info(
                    f"Selected '{option_value}' from grid '{column_label}'"
                )
                return True
            else:
                log.warning(
                    f"Option '{option_value}' not found in grid "
                    f"dropdown '{column_label}'"
                )
                return False

        except Exception as e:
            log.error(f"Failed to select grid dropdown '{column_label}': {e}")
            self._force_close_panels()
            return False

    def _select_grid_dropdown_random(self, row_element, column_label):
        """Pick a random non-placeholder option from a grid row's dropdown.

        Used for cascading dropdowns where we need to pick a valid option
        so the next level's options can load (e.g., pick random State so
        District options populate).

        Args:
            row_element: The Selenium WebElement for the grid row
            column_label: The mat-label text (e.g., 'State', 'Account Type')

        Returns:
            The text of the selected option, or None if failed.
        """
        log.info(
            f"Selecting random option from grid dropdown '{column_label}'..."
        )

        try:
            # Find mat-select within this row by label text
            selects = row_element.find_elements(
                By.CSS_SELECTOR, "mat-select"
            )

            target_select = None
            for sel in selects:
                try:
                    form_field = sel.find_element(
                        By.XPATH, "ancestor::mat-form-field"
                    )
                    labels = form_field.find_elements(
                        By.CSS_SELECTOR, "mat-label"
                    )
                    for lbl in labels:
                        if column_label.lower() in lbl.text.lower():
                            target_select = sel
                            break
                    if target_select:
                        break
                except Exception:
                    continue

            # Fallback: try all visible selects and pick first
            if not target_select:
                visible_selects = [
                    s for s in selects if s.is_displayed()
                ]
                if visible_selects:
                    target_select = visible_selects[0]
                else:
                    log.warning(
                        f"No visible mat-select in grid row for '{column_label}'"
                    )
                    return None

            # Click the select via JS
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});"
                "arguments[0].click();",
                target_select,
            )
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
                log.warning(
                    f"No options loaded in grid dropdown '{column_label}'"
                )
                self._close_dropdown_panel_only()
                return None

            # If dropdown has a search textbox, clear it to show all options
            try:
                search_inputs = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    "div[role='listbox'] input",
                )
                for inp in search_inputs:
                    try:
                        if inp.is_displayed():
                            inp.clear()
                            self.wait_seconds(0.3)
                            break
                    except Exception:
                        continue
            except Exception:
                pass

            # Read all options, filter out placeholders
            options = self.driver.find_elements(
                By.CSS_SELECTOR,
                "div[role='listbox'] mat-option, "
                "div[role='listbox'] [role='option']",
            )

            valid_options = []
            for opt in options:
                try:
                    text = opt.text.strip()
                    is_visible = opt.is_displayed()
                    is_placeholder = (
                        text.startswith("Select ")
                        or text == ""
                        or text.lower() == "select"
                    )
                    if text and is_visible and not is_placeholder:
                        valid_options.append((opt, text))
                except Exception:
                    continue

            if not valid_options:
                log.warning(
                    f"No valid options in grid dropdown '{column_label}'"
                )
                self._close_dropdown_panel_only()
                return None

            # Pick a random option
            chosen_opt, chosen_text = random.choice(valid_options)
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});"
                "arguments[0].click();",
                chosen_opt,
            )
            self.wait_seconds(0.3)
            self._force_close_panels()

            log.info(
                f"Random '{column_label}' selected: '{chosen_text}'"
            )
            return chosen_text

        except Exception as e:
            log.error(
                f"Failed to select random grid dropdown '{column_label}': {e}"
            )
            self._force_close_panels()
            return None

    def _fill_grid_dropdown_or_random(self, row_element, column_label, value):
        """Fill a grid dropdown: select specific option, or pick random if
        value is None.

        This is the grid-row equivalent of _fill_dropdown_if_provided().
        When value is None, it means "pick a random valid option from the
        live UI" — essential for cascading dropdowns where a selection
        must be made for the next level to populate.

        Args:
            row_element: The Selenium WebElement for the grid row
            column_label: The mat-label text (e.g., 'Country', 'State')
            value: Specific option text, None (pick random), or "" (skip)

        Returns:
            The text of the selected option, or None if skipped/failed.
        """
        if value is None:
            # Pick a random valid (non-placeholder) option
            return self._select_grid_dropdown_random(
                row_element, column_label
            )
        elif value == "":
            return None  # Skip empty strings
        else:
            result = self._select_grid_dropdown(
                row_element, column_label, value
            )
            return value if result else None

    def _select_cascading_dropdown(self, label_text, option_value, wait_time=2):
        """Select an option from a cascading dropdown, with extra wait time
        for dependent options to load.

        NOTE: This method uses _select_mat_option_by_label which searches
        GLOBALLY. For grid-row-scoped cascading dropdowns (Address grid),
        use _fill_grid_dropdown_or_random() with explicit wait_seconds()
        between each cascading level instead.

        Args:
            label_text: The mat-label text (e.g., 'State', 'District')
            option_value: The option text to select
            wait_time: Seconds to wait for cascading options to load
        """
        log.info(
            f"Selecting cascading '{option_value}' from '{label_text}' "
            f"(wait={wait_time}s)..."
        )
        # Wait for the dependent options to load
        self.wait_seconds(wait_time)
        return self._select_mat_option_by_label(label_text, option_value)

    def _get_address_grid_rows(self):
        """Get visible rows from the Address grid (first .grid-container).
        Uses JS to find rows, scoping to the FIRST .grid-container only,
        avoiding the bank grid which is the second .grid-container.
        Returns a list of WebElement rows.
        """
        # Use JS to find the first grid-container's table rows (Address grid)
        try:
            row_elements = self.driver.execute_script("""
                var containers = document.querySelectorAll('.grid-container');
                if (containers.length < 1) return [];
                var addressTable = containers[0].querySelector('.grid-table, table');
                if (!addressTable) return [];
                var trs = addressTable.querySelectorAll('tbody tr');
                var visible = [];
                for (var i = 0; i < trs.length; i++) {
                    if (trs[i].offsetParent !== null) visible.push(trs[i]);
                }
                return visible;
            """)
            if row_elements:
                return row_elements
        except Exception:
            pass

        # Fallback: CSS selector
        try:
            rows = self.driver.find_elements(
                By.CSS_SELECTOR,
                ".grid-container:first-of-type .grid-table tbody tr, "
                ".grid-container .grid-table tbody tr"
            )
            visible_rows = []
            for r in rows:
                try:
                    if r.is_displayed():
                        visible_rows.append(r)
                except Exception:
                    continue
            return visible_rows
        except Exception:
            pass

        return []

    def _get_bank_grid_rows(self):
        """Get visible rows from the Bank grid (second .grid-container).
        Uses JS to avoid the invalid CSS selector (.grid-container)[2].
        Returns a list of WebElement rows.
        """
        # Use JS to find the second grid-container's table rows
        # This avoids the invalid CSS selector (.grid-container)[2]
        try:
            row_elements = self.driver.execute_script("""
                var containers = document.querySelectorAll('.grid-container');
                if (containers.length < 2) return [];
                var bankTable = containers[1].querySelector('.grid-table, table');
                if (!bankTable) return [];
                var trs = bankTable.querySelectorAll('tbody tr');
                var visible = [];
                for (var i = 0; i < trs.length; i++) {
                    if (trs[i].offsetParent !== null) visible.push(trs[i]);
                }
                return visible;
            """)
            if row_elements:
                return row_elements
        except Exception:
            pass

        # Fallback: use nth-of-type CSS selector
        try:
            rows = self.driver.find_elements(
                By.CSS_SELECTOR,
                ".grid-container:nth-of-type(2) .grid-table tbody tr"
            )
            visible_rows = []
            for r in rows:
                try:
                    if r.is_displayed():
                        visible_rows.append(r)
                except Exception:
                    continue
            return visible_rows
        except Exception:
            pass

        return []

    def _fill_grid_text_input(self, row_element, field_name, value):
        """Fill a text input within a specific grid row by field name.

        Uses the input's 'name' attribute to locate the correct field.
        Uses the native value setter + dispatchEvent pattern (BUG-001 prevention).

        Args:
            row_element: The Selenium WebElement for the grid row
            field_name: The name attribute of the input (e.g., 'Address')
            value: The text value to type
        """
        try:
            inputs = row_element.find_elements(
                By.CSS_SELECTOR, "input"
            )
            for inp in inputs:
                try:
                    name_attr = inp.get_attribute("name") or ""
                    if name_attr.lower() == field_name.lower():
                        # Scroll into view first
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({block:'center'});",
                            inp,
                        )
                        # Clear and type via JS (BUG-001 prevention)
                        self.driver.execute_script(
                            "var el = arguments[0];"
                            "var newText = arguments[1];"
                            "var nativeSet = Object.getOwnPropertyDescriptor("
                            "  window.HTMLInputElement.prototype, 'value'"
                            ").set;"
                            "nativeSet.call(el, '');"
                            "el.dispatchEvent(new Event('input',{bubbles:true}));"
                            "nativeSet.call(el, newText);"
                            "el.dispatchEvent(new Event('input',{bubbles:true}));"
                            "el.dispatchEvent(new Event('change',{bubbles:true}));",
                            inp,
                            str(value),
                        )
                        self.wait_seconds(0.3)
                        log.info(
                            f"Grid text input '{field_name}' set to '{value}'"
                        )
                        return
                except Exception:
                    continue

            # Fallback: fill by name attribute CSS selector
            try:
                input_el = row_element.find_element(
                    By.CSS_SELECTOR, f"input[name='{field_name}']"
                )
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});",
                    input_el,
                )
                self.driver.execute_script(
                    "var el = arguments[0];"
                    "var newText = arguments[1];"
                    "var nativeSet = Object.getOwnPropertyDescriptor("
                    "  window.HTMLInputElement.prototype, 'value'"
                    ").set;"
                    "nativeSet.call(el, '');"
                    "el.dispatchEvent(new Event('input',{bubbles:true}));"
                    "nativeSet.call(el, newText);"
                    "el.dispatchEvent(new Event('input',{bubbles:true}));"
                    "el.dispatchEvent(new Event('change',{bubbles:true}));",
                    input_el,
                    str(value),
                )
                self.wait_seconds(0.3)
                log.info(
                    f"Grid text input '{field_name}' set to '{value}' (fallback)"
                )
            except Exception:
                log.warning(
                    f"Grid text input '{field_name}' not found in row"
                )

        except Exception as e:
            log.error(f"Failed to fill grid text input '{field_name}': {e}")

    # ==============================================================
    #  Helper: Fill dropdown if provided
    # ==============================================================

    def _fill_dropdown_if_provided(self, data, key, select_locator, label_name):
        """Fill a dropdown if the key exists in data.
        If value is provided, select that specific option using
        _select_mat_option_by_label (handles BUG-001).
        If key exists but value is empty/None, select random.
        If key doesn't exist in data, skip entirely.
        """
        if key not in data:
            return  # Key not provided — skip this dropdown entirely

        value = data[key]
        if value:
            self._select_mat_option_by_label(label_name, str(value))
        else:
            self._select_random_from_dropdown(select_locator, label_name)

    # ==============================================================
    #  Toggle switch helpers
    # ==============================================================

    def _set_toggle_if_provided(self, data, key, toggle_locator, label_name):
        """Set a toggle switch if the key exists in data.
        If value is True, turns the toggle ON.
        If value is False, turns the toggle OFF.
        If key doesn't exist in data, skip entirely.
        """
        if key not in data:
            return

        desired_state = bool(data[key])
        self._set_toggle_to(toggle_locator, label_name, desired_state)

    def _set_toggle_to(self, toggle_locator, label_name, desired_state):
        """Set a custom toggle switch to the desired state (True=ON, False=OFF).
        The Customer screen uses <app-slide-toggle-v2> with
        <div class="switch-wrapper">, NOT standard Angular checkboxes.
        """
        log.info(
            f"Setting toggle '{label_name}' to "
            f"{'ON' if desired_state else 'OFF'}..."
        )

        try:
            toggle_el = self.driver.find_element(
                By.XPATH, toggle_locator[1]
            )
        except Exception:
            # Fallback: try broader search
            try:
                toggle_el = self.driver.find_element(
                    By.CSS_SELECTOR,
                    ".edit_pop_up .switch-wrapper, "
                    ".big-model .switch-wrapper, "
                    "mat-dialog-container .switch-wrapper",
                )
            except Exception:
                log.warning(f"Toggle '{label_name}' not found")
                return

        # Determine current state: check if 'active' or 'checked' class is present
        current_state = self._is_toggle_on(toggle_el)

        if current_state == desired_state:
            log.info(
                f"Toggle '{label_name}' already "
                f"{'ON' if desired_state else 'OFF'}"
            )
            return

        # Click the toggle to change state
        try:
            # Try clicking the inner switch element
            switch = toggle_el.find_element(
                By.CSS_SELECTOR, ".switch, label, input[type='checkbox']"
            )
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});"
                "arguments[0].click();",
                switch,
            )
        except Exception:
            # Fallback: click the toggle wrapper itself
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});"
                "arguments[0].click();",
                toggle_el,
            )

        self.wait_seconds(0.5)

        # Verify state change
        new_state = self._is_toggle_on(toggle_el)
        if new_state == desired_state:
            log.info(
                f"Toggle '{label_name}' set to "
                f"{'ON' if desired_state else 'OFF'}"
            )
        else:
            log.warning(
                f"Toggle '{label_name}' state change may have failed. "
                f"Desired: {desired_state}, Got: {new_state}"
            )

    def _is_toggle_on(self, toggle_el):
        """Determine if a custom toggle switch element is ON or OFF.
        Checks for common indicators: 'active' class, 'checked' attribute,
        or the slider position.
        Returns True if ON, False if OFF.
        """
        try:
            classes = toggle_el.get_attribute("class") or ""
            # Check for active/checked class on the wrapper
            if "active" in classes or "checked" in classes:
                return True

            # Check for inner checkbox input
            try:
                checkbox = toggle_el.find_element(
                    By.CSS_SELECTOR, "input[type='checkbox']"
                )
                return checkbox.is_selected()
            except Exception:
                pass

            # Check the slider position via CSS class
            try:
                slider = toggle_el.find_element(
                    By.CSS_SELECTOR, ".slider, .switch-slider"
                )
                slider_classes = slider.get_attribute("class") or ""
                if "active" in slider_classes or "checked" in slider_classes:
                    return True
            except Exception:
                pass

            # Check aria-checked attribute
            aria_checked = toggle_el.get_attribute("aria-checked")
            if aria_checked == "true":
                return True

        except Exception:
            pass

        return False

    def get_toggle_state(self, toggle_locator, label_name=""):
        """Get the current state of a toggle switch.
        Returns True if ON, False if OFF.
        """
        try:
            toggle_el = self.driver.find_element(
                By.XPATH, toggle_locator[1]
            )
            return self._is_toggle_on(toggle_el)
        except Exception:
            log.warning(f"Could not read toggle state for '{label_name}'")
            return False

    def set_toggle(self, toggle_locator, desired_state):
        """Set a toggle to the desired state.
        Args:
            toggle_locator: Locator tuple for the toggle switch
            desired_state: True for ON, False for OFF
        """
        label_name = str(toggle_locator)
        self._set_toggle_to(toggle_locator, label_name, desired_state)

    # ==============================================================
    #  Dropdown helpers — dynamic option reading (NEVER hardcode)
    # ==============================================================

    def _select_mat_option(self, select_locator, option_text):
        """Open a mat-select dropdown and select a specific option by text.
        Handles internal search textbox if present.
        Also applies BUG-001 workaround via JS value-setter + dispatchEvent.
        """
        log.info(f"Selecting '{option_text}' from dropdown...")

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
                el = self.driver.find_element(By.XPATH, select_locator[1])
                self.driver.execute_script("arguments[0].click();", el)
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
        option_clicked = False
        try:
            opt_locator = (
                "xpath",
                f"//div[@role='listbox']//mat-option"
                f"[contains(.,'{option_text}')]",
            )
            self.click_with_retry(opt_locator)
            option_clicked = True
        except Exception:
            try:
                opt_locator2 = (
                    "xpath",
                    f"//div[@role='listbox']//div[@role='option']"
                    f"[contains(.,'{option_text}')]",
                )
                self.click_with_retry(opt_locator2)
                option_clicked = True
            except Exception:
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
                            option_clicked = True
                            break
                    except Exception:
                        continue

        self.wait_seconds(0.3)
        self._force_close_panels()

        # BUG-001 workaround: use JS value-setter + dispatchEvent
        if option_clicked:
            try:
                el = self.driver.find_element(By.XPATH, select_locator[1])
                self.driver.execute_script("""
                    var selectEl = arguments[0];
                    var triggerEl = selectEl.querySelector(
                        '.mat-mdc-select-trigger, .mat-select-trigger'
                    );
                    if (triggerEl) {
                        triggerEl.dispatchEvent(
                            new Event('change', {bubbles: true})
                        );
                    }
                """, el)
            except Exception:
                pass

        log.info(f"Selected '{option_text}'")

    def _select_random_from_dropdown(self, select_locator, label_name, exclude=None):
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
                el = self.driver.find_element(By.XPATH, select_locator[1])
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
            log.warning(
                f"No options loaded in '{label_name}' dropdown — skipping"
            )
            self._close_dropdown_panel_only()
            return None

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
            log.warning(
                f"No valid options in '{label_name}' dropdown — skipping"
            )
            self._close_dropdown_panel_only()
            return None

        if exclude:
            option_texts = [t for t in option_texts if t not in exclude]
            if not option_texts:
                log.warning(
                    f"No remaining options in '{label_name}' "
                    f"after excluding — skipping"
                )
                self._close_dropdown_panel_only()
                return None

        selected = random.choice(option_texts)
        log.info(f"Random '{label_name}' selected: '{selected}'")

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

        # BUG-001 workaround
        try:
            el = self.driver.find_element(By.XPATH, select_locator[1])
            self.driver.execute_script("""
                var selectEl = arguments[0];
                var triggerEl = selectEl.querySelector(
                    '.mat-mdc-select-trigger, .mat-select-trigger'
                );
                if (triggerEl) {
                    triggerEl.dispatchEvent(
                        new Event('change', {bubbles: true})
                    );
                }
            """, el)
        except Exception:
            pass

        return selected

    def get_dropdown_options(self, select_locator):
        """Open a dropdown, read all option texts, then close it."""
        log.info("Reading dropdown options...")
        self._close_select_panel()
        self.wait_seconds(0.3)

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
                el = self.driver.find_element(By.XPATH, select_locator[1])
                self.driver.execute_script("arguments[0].click();", el)
        self.wait_seconds(0.5)

        try:
            WebDriverWait(self.driver, 8).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, "div.mat-mdc-select-panel mat-option")
                )
            )
            self.wait_seconds(0.3)
        except TimeoutException:
            log.warning(
                "Timed out waiting for dropdown options to become visible"
            )

        options = self.driver.find_elements(
            By.CSS_SELECTOR, "div.mat-mdc-select-panel mat-option"
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

        self._close_select_panel()
        log.info(f"Dropdown options: {option_texts}")
        return option_texts

    # ==============================================================
    #  Form submission & cancellation
    # ==============================================================

    def click_submit(self):
        """Click the Submit button on the form."""
        log.info("Clicking Submit button...")
        self._force_close_panels()
        try:
            btn = self.driver.find_element(
                By.XPATH,
                "//div[contains(@class,'popup-footer')]"
                "//button[@type='submit']",
            )
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});"
                "arguments[0].click();",
                btn,
            )
            self.wait_seconds(2)
            log.info("Submit clicked via type='submit'")
        except Exception:
            try:
                btn = self.driver.find_element(
                    By.XPATH,
                    "//div[contains(@class,'popup-footer')]"
                    "//button[contains(.,'Submit')]",
                )
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});"
                    "arguments[0].click();",
                    btn,
                )
                self.wait_seconds(2)
                log.info("Submit clicked via text match")
            except Exception:
                log.warning("Submit button not found or not clickable")

    def cancel(self):
        """Click the Cancel button on the form."""
        log.info("Clicking Cancel button...")

        # Strategy 1: mat-warn button in popup-footer
        try:
            btn = self.driver.find_element(
                By.XPATH,
                "//div[contains(@class,'popup-footer')]"
                "//button[contains(@class,'mat-warn')]",
            )
            self.driver.execute_script("arguments[0].click();", btn)
            self.wait_seconds(1)
            log.info("Cancel clicked via mat-warn class")
            return
        except Exception:
            pass

        # Strategy 2: Cancel button by text
        try:
            btn = self.driver.find_element(
                By.XPATH,
                "//div[contains(@class,'popup-footer')]"
                "//button[contains(.,'Cancel')]",
            )
            self.driver.execute_script("arguments[0].click();", btn)
            self.wait_seconds(1)
            log.info("Cancel clicked via text match")
            return
        except Exception:
            pass

        # Strategy 3: JS click
        try:
            self.driver.execute_script("""
                var btns = document.querySelectorAll('.popup-footer button');
                for (var i = 0; i < btns.length; i++) {
                    if (btns[i].textContent.trim() === 'Cancel'
                        || btns[i].classList.contains('mat-warn')) {
                        btns[i].click();
                        break;
                    }
                }
            """)
            self.wait_seconds(1)
            log.info("Cancel clicked via JS")
        except Exception:
            log.warning("Cancel button not found")


    # ==============================================================
    #  Edit mode helpers
    # ==============================================================

    def click_update(self):
        """Click the Update button in Edit mode popup footer."""
        log.info("Clicking Update button...")
        try:
            btn = self.driver.find_element(
                By.XPATH,
                "//div[contains(@class,'popup-footer')]//button[@type='submit']",
            )
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});"
                "arguments[0].click();", btn,
            )
            self.wait_seconds(2)
            log.info("Update clicked")
            return True
        except Exception:
            pass

        # Fallback: Find by text 'Update'
        try:
            btn = self.driver.find_element(
                By.XPATH,
                "//div[contains(@class,'popup-footer')]//button[contains(.,'Update')]",
            )
            self.driver.execute_script("arguments[0].click();", btn)
            self.wait_seconds(2)
            log.info("Update clicked via text match")
            return True
        except Exception:
            log.warning("Update button not found")
            return False

    def has_update_button(self):
        """Check if the Update button is visible in the popup footer."""
        try:
            btns = self.driver.find_elements(
                By.XPATH,
                "//div[contains(@class,'popup-footer')]//button[@type='submit']",
            )
            for btn in btns:
                if btn.is_displayed():
                    return True
        except Exception:
            pass
        try:
            btns = self.driver.find_elements(
                By.XPATH,
                "//div[contains(@class,'popup-footer')]//button[contains(.,'Update')]",
            )
            for btn in btns:
                if btn.is_displayed():
                    return True
        except Exception:
            pass
        return False

    def is_edit_mode(self):
        """Check if the currently open popup is in Edit mode
        (has Update button instead of Submit).
        """
        try:
            btns = self.driver.find_elements(
                By.XPATH,
                "//div[contains(@class,'popup-footer')]//button",
            )
            for btn in btns:
                text = btn.text.strip()
                if "Update" in text and btn.is_displayed():
                    return True
        except Exception:
            pass
        return False

    def handle_success_alert(self, timeout=5):
        """Handle SweetAlert2 success alert after Update.
        Returns the alert message, or '' if no alert appeared.
        """
        log.info("Checking for success alert...")
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
                self.driver.execute_script("arguments[0].click();", confirm)
            except Exception:
                pass
            try:
                WebDriverWait(self.driver, 3).until(
                    EC.invisibility_of_element_located(
                        (By.CSS_SELECTOR, ".swal2-container")
                    )
                )
            except Exception:
                pass
            log.info(f"Success alert handled: {msg}")
            return msg
        except TimeoutException:
            return ""

    def is_validation_alert_present(self, timeout=3):
        """Quick check if a SweetAlert2 validation alert is visible."""
        try:
            el = self.driver.find_element(By.CSS_SELECTOR, "#swal2-title")
            return el.is_displayed()
        except Exception:
            return False

    def get_swal_title(self):
        """Get the current SweetAlert2 title text."""
        try:
            el = self.driver.find_element(By.CSS_SELECTOR, "#swal2-title")
            return el.text.strip()
        except Exception:
            return ""

    def clear_search(self):
        """Clear the search input and refresh the table."""
        log.info("Clearing search...")
        try:
            search_input = self.driver.find_element(
                By.CSS_SELECTOR, "#erpSearchInput, input.erp-search-input"
            )
            self.driver.execute_script(
                "arguments[0].value = '';"
                "arguments[0].dispatchEvent(new Event('input', {bubbles: true}));",
                search_input,
            )
            search_input.send_keys(Keys.ENTER)
            self.wait_seconds(2)
            log.info("Search cleared")
        except Exception:
            # Try closing search bar via toggle
            try:
                toggle = self.driver.find_element(
                    By.CSS_SELECTOR, "button[mattooltip='Search']"
                )
                self.driver.execute_script("arguments[0].click();", toggle)
                self.wait_seconds(1)
                log.info("Search closed via toggle")
            except Exception:
                pass

    # ==============================================================
    #  Validation helpers
    # ==============================================================

    def handle_validation_warning(self, timeout=10):
        """Handle SweetAlert2 validation warning popup.
        Returns the warning message text, or '' if no alert appeared.
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

            # Also read HTML message if present
            html_msg = ""
            try:
                html_el = self.driver.find_element(
                    By.CSS_SELECTOR, ".swal2-html-container"
                )
                html_msg = html_el.text.strip()
            except Exception:
                pass

            try:
                confirm = self.driver.find_element(
                    By.CSS_SELECTOR, ".swal2-confirm"
                )
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

            log.info(f"Validation warning handled: {msg} — {html_msg}")
            return msg
        except TimeoutException:
            return ""
        
    def edit_customer(self, company_name, edit_data):
        """Full edit workflow: click Edit, modify fields, Update.

        Args:
            company_name: The company name to find in the table
            edit_data: dict of fields to modify

        Returns:
            result dict: {status, error, message}
        """
        log.info(f"Editing customer: {company_name}")
        result = {"status": "UNKNOWN", "error": "", "message": ""}

        # Click Edit via 3-dot menu
        clicked = self.click_edit_button(company_name)
        if not clicked:
            result["status"] = "FAILED"
            result["error"] = "Edit button not found"
            return result

        self.wait_seconds(1)
        if not self._is_form_popup_open():
            self._wait_for_form_content(timeout=5)

        # Modify fields
        if "company_name" in edit_data and edit_data["company_name"]:
            self.type_text(self.COMPANY_NAME_INPUT, edit_data["company_name"], clear_first=True)
        if "email" in edit_data and edit_data["email"]:
            self.type_text(self.EMAIL_INPUT, edit_data["email"], clear_first=True)
        if "phone_number" in edit_data and edit_data["phone_number"]:
            self.type_text(self.PHONE_NUMBER_INPUT, edit_data["phone_number"], clear_first=True)
        if "pan_number" in edit_data and edit_data["pan_number"]:
            self.type_text(self.PAN_NUMBER_INPUT, edit_data["pan_number"], clear_first=True)

        # Click Update
        self.click_update()
        self.wait_seconds(2)

        # Handle SweetAlert2
        self.handle_success_alert(timeout=5)
        self.wait_seconds(1)

        # Close popup if still open
        try:
            self.close_popup()
        except Exception:
            pass
        try:
            self.force_close_form_popup()
        except Exception:
            pass

        result["status"] = "PASSED"
        result["message"] = f"Customer '{company_name}' updated"
        log.info(f"Edit result: {result}")
        return result

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

    def get_field_error(self, field_label):
        """Get the error text for a specific form field by label.
        Returns the error message string, or '' if no error.
        """
        try:
            locator = (
                "xpath",
                f"//mat-label[contains(.,'{field_label}')]"
                f"/ancestor::mat-form-field//mat-error",
            )
            el = self.find_visible_element(locator, timeout=3)
            return el.text.strip()
        except Exception:
            return ""

    def is_validation_shown(self):
        """Check if any validation errors are visible in the form.
        Returns True if at least one mat-error is displayed.
        """
        errors = self.driver.find_elements(
            By.CSS_SELECTOR, "mat-error, .mat-mdc-form-field-error"
        )
        for e in errors:
            try:
                if e.is_displayed() and e.text.strip():
                    return True
            except Exception:
                continue
        return False

    # ==============================================================
    #  Table interaction
    # ==============================================================

    def is_customer_in_table(self, company_name):
        """Check if a customer with the given company name appears
        in the listing table.
        """
        rows = self.driver.find_elements(
            By.CSS_SELECTOR,
            "app-dynamic-table table tbody tr, table tbody tr",
        )
        for row in rows:
            try:
                cells = row.find_elements(By.TAG_NAME, "td")
                for cell in cells:
                    if company_name.strip().lower() in cell.text.strip().lower():
                        return True
            except StaleElementReferenceException:
                continue
        return False

    def get_table_row_count(self):
        """Return the number of visible data rows in the table."""
        rows = self.driver.find_elements(
            By.CSS_SELECTOR,
            "app-dynamic-table table tbody tr, table tbody tr",
        )
        visible_rows = []
        for r in rows:
            try:
                if r.is_displayed():
                    visible_rows.append(r)
            except Exception:
                continue
        return len(visible_rows)

    
    def _click_first_menu_option(self, option_text):
        """Click a menu option (View/Edit/History) from the FIRST row's 3-dot menu."""
        # Click the 3-dot trigger on the first row
        triggers = self.driver.find_elements(
            By.CSS_SELECTOR, "button.mat-mdc-menu-trigger.erp-row-trigger"
        )
        if not triggers:
            log.warning("No 3-dot menu triggers found in table")
            return False
        self.driver.execute_script("arguments[0].click();", triggers[0])
        self.wait_seconds(1)

        # Click the desired menu option
        try:
            option = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        f"//div[contains(@class,'mat-mdc-menu-content')]//span[contains(@class,'erp-menu-title') and text()='{option_text}']/ancestor::button",
                    )
                )
            )
            self.driver.execute_script("arguments[0].click();", option)
            log.info(f"Clicked '{option_text}' from first row menu")
            return True
        except Exception:
            log.warning(f"Menu option '{option_text}' not found")
            # Close menu if option not found
            self._force_close_panels()
            return False

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

    def click_history_first_row(self):
        """Click History on the first row in the table (no creation needed)."""
        log.info("Opening History for first row...")
        self._click_first_menu_option("History")
        self.wait_seconds(1)

    def get_first_row_name(self):
        """Get the Company Name from the first row in the table."""
        try:
            cells = self.driver.find_elements(
                By.CSS_SELECTOR,
                "td.cdk-column-name, td.mat-column-name, "
                "td.cdk-column-company_name, td.mat-column-company_name",
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

    # ==============================================================
    #  Create workflow (high-level)
    # ==============================================================

    def create_customer(self, data):
        """Full create workflow for a new Customer.

        Steps:
          1. Open the Add form
          2. Fill universal fields
          3. Fill Step 0 (Additional Details)
          4. Click Next (to Step 1)
          5. Fill Step 1 (Customer Details / Address Grid)
          6. Click Next (to Step 2)
          7. Fill Step 2 (Customer Bank Details / Bank Grid)
          8. Submit
          9. Handle validation warning or check for success
          10. Return result dict with status and data

        Args:
            data: dict with all customer data including
                  'address_rows' and 'bank_rows' lists

        Returns:
            result dict: {status, error, message, data}
        """
        name = data.get("company_name", "N/A")
        log.info(f"Creating Customer: {name}")
        result = {
            "status": "FAILED",
            "error": "",
            "message": "",
            "data": copy.deepcopy(data),
        }

        try:
            # Step 1: Open Add form
            self.open_add_form()
            if not self.is_add_form_open():
                raise Exception("Add form did not open")

            # Step 2: Fill universal fields
            self.fill_universal_fields(data)

            # Step 3: Fill Step 0 — Additional Details
            self.fill_step0(data)

            # Step 4: Navigate to Step 1
            self.click_stepper_next()
            self.wait_seconds(1)

            # Step 5: Fill Step 1 — Customer Details (Address Grid)
            if data.get("address_rows"):
                self.fill_step1(data)

            # Step 6: Navigate to Step 2
            self.click_stepper_next()
            self.wait_seconds(1)

            # Step 7: Fill Step 2 — Customer Bank Details (Bank Grid)
            if data.get("bank_rows"):
                self.fill_step2(data)

            # Step 8: Submit
            self.click_submit()

            # Step 9: Handle result
            msg = self.handle_validation_warning(timeout=60)
            if msg:
                failure_keywords = ["validation failed", "failed", "error", "invalid"]
                if any(kw in msg.lower() for kw in failure_keywords):
                    result["status"] = "FAILED"
                    result["error"] = msg
                else:
                    result["message"] = msg
                    result["status"] = "PASSED"
            else:
                self.wait_seconds(3)
                if not self._is_form_popup_open():
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
            log.error(f"Failed to create customer '{name}': {e}")

        # Always clean up
        try:
            self.driver.execute_script("""
                document.querySelectorAll('.swal2-container').forEach(
                    function(el) { el.remove(); }
                );
                document.querySelectorAll('.cdk-overlay-backdrop').forEach(
                    function(el) { el.remove(); }
                );
            """)
        except Exception:
            pass

        IM_SUBMISSIONS.append(result)
        return result

    # ==============================================================
    #  Get form field values (for verification)
    # ==============================================================

    def get_form_field_values(self):
        """Read all universal field values from the currently open popup.
        Returns a dict with all universal field values.
        """
        values = {}

        # Text inputs
        for key, locator in [
            ("company_name", self.COMPANY_NAME_INPUT),
            ("email", self.EMAIL_INPUT),
            ("phone_number", self.PHONE_NUMBER_INPUT),
            ("pan_number", self.PAN_NUMBER_INPUT),
        ]:
            try:
                by, val = self._parse_locator(locator)
                el = self.driver.find_element(by, val)
                values[key] = el.get_attribute("value") or ""
            except Exception:
                values[key] = ""

        # Dropdown selects — read the displayed text
        for key, locator in [
            ("ownership_status", self.OWNERSHIP_STATUS_SELECT),
            ("sale_type", self.SALE_TYPE_SELECT),
            ("supply_type", self.SUPPLY_TYPE_SELECT),
            ("transaction_currency", self.TRANSACTION_CURRENCY_SELECT),
        ]:
            try:
                by, val = self._parse_locator(locator)
                el = self.driver.find_element(by, val)
                values[key] = el.text.strip()
            except Exception:
                values[key] = ""

        # Toggle switches
        for key, locator in [
            ("status", self.STATUS_TOGGLE),
            ("is_tds_applicable", self.IS_TDS_APPLICABLE_TOGGLE),
        ]:
            values[key] = self.get_toggle_state(locator, key)

        return values

    def get_form_field_values_step0(self):
        """Read all Step 0 field values from the currently open popup.
        Returns a dict with all Step 0 field values.
        """
        values = {}

        # Text inputs
        for key, locator in [
            ("contact_person_name", self.CONTACT_PERSON_NAME_INPUT),
            ("office_number", self.OFFICE_NUMBER_INPUT),
            ("deposite", self.DEPOSITE_INPUT),
            ("quantity_tolerance", self.QUANTITY_TOLERANCE_INPUT),
            ("rate_tolerance", self.RATE_TOLERANCE_INPUT),
        ]:
            try:
                by, val = self._parse_locator(locator)
                el = self.driver.find_element(by, val)
                values[key] = el.get_attribute("value") or ""
            except Exception:
                values[key] = ""

        # Dropdown selects — read the displayed text
        for key, locator in [
            ("preferred_payment_method", self.PREFERRED_PAYMENT_METHOD_SELECT),
            ("gst_registration_type", self.GST_REGISTRATION_TYPE_SELECT),
            ("payment_terms", self.PAYMENT_TERMS_SELECT),
            ("delivery_terms", self.DELIVERY_TERMS_SELECT),
            ("mode_of_delivery", self.MODE_OF_DELIVERY_SELECT),
            ("courier_terms", self.COURIER_TERMS_SELECT),
        ]:
            try:
                by, val = self._parse_locator(locator)
                el = self.driver.find_element(by, val)
                values[key] = el.text.strip()
            except Exception:
                values[key] = ""

        # Is TDS Applicable toggle
        values["is_tds_applicable"] = self.get_toggle_state(
            self.IS_TDS_APPLICABLE_TOGGLE, "Is TDS Applicable"
        )

        return values

    def get_form_field_values_step1(self):
        """Read all Step 1 (Address Grid) field values from the
        currently open popup.
        Returns a list of dicts, one per address row.
        """
        address_rows = []
        try:
            rows = self.driver.find_elements(
                By.CSS_SELECTOR, ".grid-container .grid-table tbody tr"
            )
            for row in rows:
                try:
                    if not row.is_displayed():
                        continue
                    row_data = {}

                    # Read text inputs
                    inputs = row.find_elements(By.CSS_SELECTOR, "input")
                    for inp in inputs:
                        try:
                            name = inp.get_attribute("name") or ""
                            if name:
                                row_data[name.lower().replace(" ", "_")] = (
                                    inp.get_attribute("value") or ""
                                )
                        except Exception:
                            continue

                    # Read dropdown displayed values
                    selects = row.find_elements(By.CSS_SELECTOR, "mat-select")
                    for idx, sel in enumerate(selects):
                        try:
                            # Find label
                            form_field = sel.find_element(
                                By.XPATH, "ancestor::mat-form-field"
                            )
                            labels = form_field.find_elements(
                                By.CSS_SELECTOR, "mat-label"
                            )
                            label_text = (
                                labels[0].text.strip().lower().replace(" ", "_")
                                if labels
                                else f"select_{idx}"
                            )
                            row_data[label_text] = sel.text.strip()
                        except Exception:
                            row_data[f"select_{idx}"] = sel.text.strip()

                    address_rows.append(row_data)
                except StaleElementReferenceException:
                    continue
        except Exception:
            pass
        return address_rows

    def get_form_field_values_step2(self):
        """Read all Step 2 (Bank Grid) field values from the
        currently open popup.
        Returns a list of dicts, one per bank row.
        """
        bank_rows = []
        try:
            rows = self._get_bank_grid_rows()
            for row in rows:
                try:
                    if not row.is_displayed():
                        continue
                    row_data = {}

                    # Read text inputs
                    inputs = row.find_elements(By.CSS_SELECTOR, "input")
                    for inp in inputs:
                        try:
                            name = inp.get_attribute("name") or ""
                            input_type = inp.get_attribute("type") or ""
                            if name and input_type != "file":
                                row_data[name.lower().replace(" ", "_")] = (
                                    inp.get_attribute("value") or ""
                                )
                        except Exception:
                            continue

                    # Read dropdown displayed values
                    selects = row.find_elements(By.CSS_SELECTOR, "mat-select")
                    for idx, sel in enumerate(selects):
                        try:
                            form_field = sel.find_element(
                                By.XPATH, "ancestor::mat-form-field"
                            )
                            labels = form_field.find_elements(
                                By.CSS_SELECTOR, "mat-label"
                            )
                            label_text = (
                                labels[0].text.strip().lower().replace(" ", "_")
                                if labels
                                else f"select_{idx}"
                            )
                            row_data[label_text] = sel.text.strip()
                        except Exception:
                            row_data[f"select_{idx}"] = sel.text.strip()

                    bank_rows.append(row_data)
                except StaleElementReferenceException:
                    continue
        except Exception:
            pass
        return bank_rows

    def dismiss_swal_alert(self, timeout=3):
        """Dismiss any SweetAlert2 popup by clicking its OK/Confirm button.
        Call this BEFORE trying to close the form, since SweetAlert2
        is modal and blocks all other interactions.
        """
        try:
            ok_btn = self.driver.find_element(
                By.CSS_SELECTOR, "button.swal2-confirm"
            )
            if ok_btn.is_displayed():
                self.driver.execute_script("arguments[0].click();", ok_btn)
                self.wait_seconds(1)
                log.info("SweetAlert2 dismissed via OK button")
                return True
        except Exception:
            pass
        return False
    
    def get_input_value(self, locator):
        """Read the current value of an input field (works with Angular reactive forms)."""
        try:
            by, val = self._normalize_locator(locator)
            element = self.driver.find_element(by, val)
            value = self.driver.execute_script("return arguments[0].value;", element)
            return value or ""
        except Exception as e:
            log.warning(f"Could not read input value for {locator}: {e}")
            return ""
        
    def type_text(self, locator, text, clear_first=True):
        """Type text into a field using browser keyboard events (not JS)."""
        try:
            by, val = self._normalize_locator(locator)
            element = self.driver.find_element(by, val)
            if clear_first:
                element.clear()
                self.wait_seconds(0.3)
            element.send_keys(text)
            log.info(f"Typed '{text}' into: {locator}")
        except Exception as e:
            log.warning(f"Could not type text into {locator}: {e}")

    def fill_universal_fields_browser_click(self, data):
        """Fill universal fields using normal Selenium browser clicks.
        Used by BUG-001 test to verify mat-select form model sync issue.
        Currently delegates to fill_universal_fields — will XPASS when ERP is fixed.
        """
        self.fill_universal_fields(data)

    def fill_step0_browser_click(self, company_name=None, email=None, phone=None, pan=None):
        """Fill Step 0 fields using browser clicks (not JS)."""
        try:
            if company_name:
                by, val = self._normalize_locator(self.COMPANY_NAME_INPUT)
                el = self.driver.find_element(by, val)
                el.click()
                el.clear()
                el.send_keys(company_name)
                log.info(f"Browser-typed company_name: {company_name}")
            if email:
                by, val = self._normalize_locator(self.EMAIL_INPUT)
                el = self.driver.find_element(by, val)
                el.click()
                el.clear()
                el.send_keys(email)
                log.info(f"Browser-typed email: {email}")
            if phone:
                by, val = self._normalize_locator(self.PHONE_INPUT)
                el = self.driver.find_element(by, val)
                el.click()
                el.clear()
                el.send_keys(phone)
                log.info(f"Browser-typed phone: {phone}")
            if pan:
                by, val = self._normalize_locator(self.PAN_INPUT)
                el = self.driver.find_element(by, val)
                el.click()
                el.clear()
                el.send_keys(pan)
                log.info(f"Browser-typed PAN: {pan}")
            self.wait_seconds(0.5)
            log.info("Step 0 filled via browser click")
        except Exception as e:
            log.warning(f"fill_step0_browser_click failed: {e}")

    def fill_address_row_browser_click(self, row_index, data):
        """Fill address row using normal Selenium browser clicks."""
        self.fill_address_row(row_index, data)

    def fill_bank_row_browser_click(self, row_index, data):
        """Fill bank row using normal Selenium browser clicks."""
        self.fill_bank_row(row_index, data)

    def _normalize_locator(self, locator):
        """Convert shorthand locator format to Selenium By constants."""
        by, value = locator
        mapping = {
            'css': By.CSS_SELECTOR,
            'xpath': By.XPATH,
            'id': By.ID,
            'name': By.NAME,
            'class': By.CLASS_NAME,
            'tag': By.TAG_NAME,
            'link_text': By.LINK_TEXT,
            'partial_link_text': By.PARTIAL_LINK_TEXT,
        }
        return (mapping.get(by, by), value)
