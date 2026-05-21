"""
farmer_page.py
--------------
Page Object Model for RhythmERP Farmer screen.

Location: Registration > Farmer
URL:      /#/dynamic-screens/Farmer/Farmer

FORM LAYOUT (MULTI-STEP STEPPER — varies by Farmer Category):
  Step 0: Farmer Details (ALWAYS VISIBLE)
  Stepper tabs depend on Farmer Category selection:
    Borrower Farmer -> 13 tabs
    FPC Member -> 6 tabs
    Walk-in Farmer -> 3 tabs

UNIVERSAL FIELDS (Step 0 — fill these FIRST before scrolling):
  Farmer Name, Email, Phone Number, Date Of Birth, Age (readonly),
  Gender, Category, Religion, Password, Farmer Category, Land Classification

KEY RULES (from browser exploration 2026-05-21):
  - NEVER use Keys.ESCAPE (can trigger Angular SPA navigation)
  - JS clicks for Angular Material overlays
  - JS value-setter for ALL dropdown selections
  - Farmer Category is MULTI-SELECT mat-select
  - Address tabs use TABLE/GRID ROWS with cascading dropdowns
  - Country MUST ALWAYS be "India" (other countries lack cascading data)
  - Fill ALL upper/visible fields first, THEN scroll down for lower fields
  - Age is READONLY — auto-calculated from Date Of Birth
  - Toggle switch uses <app-slide-toggle-v2> component
  - popup-footer class is dynamic — use contains(@class,'popup-footer')
  - Login button REQUIRES JavaScript click
  - SweetAlert2 for success/validation popups
  - Angular Material renders ALL tab contents in the DOM; inactive panels
    have inert="" attribute and class mat-horizontal-stepper-content-previous;
    active panel has class mat-horizontal-stepper-content-current and NO inert.
    Dropdown search MUST be scoped to the ACTIVE panel only.

STEPPER TAB LAYOUT BY CATEGORY:
  Walk-in Farmer:  Current Address Details, Permanent Address Details, Bank Details
  FPC Member:      Current Address Details, Permanent Address Details, Land Details,
                    Crop Details, KYC Details, Bank Details
  Borrower Farmer: Current Address Details, Permanent Address Details, Family Details,
                    Other Details, Land Details, Crop Details, KYC Details,
                    Vehicle Details, Income Details, Bank Details,
                    Irrigation Details, Award Details, Loan Details

KNOWN BUGS:
  BUG-F01: No Of Owner required but no asterisk
  BUG-F02: Deselect+Reselect farmer category freezes Next/Back
  BUG-F03: Farmer Name accepts special characters
  BUG-F04: Email rejects uppercase letters
  BUG-F05: Farmer Category placeholder is selectable
  BUG-F06: Amount fields accept 0 and . prefix
  BUG-F08: Edit mode missing Land/Crop/KYC tabs
  BUG-F09: Character count indicator disappears on validation error
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
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    ElementClickInterceptedException,
    StaleElementReferenceException,
    InvalidSessionIdException,
)
from common.base_page import BasePage
from common.logger import log
from config import RHYTHMERP_BASE_URL, EXPLICIT_WAIT

# Global list to track every submission for reporting
FARMER_SUBMISSIONS = []


class FarmerPage(BasePage):
    PAGE_URL = f"{RHYTHMERP_BASE_URL}/#/dynamic-screens/Farmer/Farmer"

    # ==============================================================
    #  LOCATORS — Toolbar
    # ==============================================================
    ADD_BUTTON = ("css", "button.erp-add-btn")
    SEARCH_TOGGLE = ("css", "button.search-btn, button[aria-label='Search']")
    REFRESH_BUTTON = ("css", "button[mattooltip='Refresh']")
    FILTER_BUTTON = ("css", "button.filter-btn")

    # ==============================================================
    #  LOCATORS — Search bar
    # ==============================================================
    SEARCH_INPUT = ("css", "input#erpSearchInput, .erp-search-wrapper input")
    SEARCH_SUBMIT = ("css", "button.search-btn")

    # ==============================================================
    #  LOCATORS — Table (main listing)
    # ==============================================================
    TABLE = ("css", "table#excel-table")
    TABLE_ROWS = ("css", "table#excel-table tbody tr")
    TABLE_FARMER_NAME_CELLS = (
        "css",
        "table#excel-table tbody td.cdk-column-name, "
        "table#excel-table tbody td.mat-column-name",
    )
    TABLE_PHONE_CELLS = (
        "css",
        "table#excel-table tbody td.cdk-column-mobile_no",
    )
    NO_DATA_ROW = (
        "css",
        "table#excel-table tbody tr td.no-data, "
        "table#excel-table tbody tr.mat-mdc-no-data-row",
    )

    # ==============================================================
    #  LOCATORS — Stepper form popup
    # ==============================================================
    FORM_POPUP = (
        "css",
        ".big-model, mat-dialog-container, "
        ".edit_pop_up.override_edit_pop_up.popup-mode",
    )
    FORM_HEADING = (
        "css",
        ".big-model h3, mat-dialog-container h3",
    )
    MAT_STEPPER = ("css", "mat-horizontal-stepper, mat-stepper")
    STEPPER_STEPS = ("css", "mat-step-header, .mat-step-header")

    # ==============================================================
    #  LOCATORS — Stepper navigation buttons
    # ==============================================================
    STEPPER_NEXT = (
        "xpath",
        "//button[contains(@class,'mat-stepper-next') or contains(.,'Next')]",
    )
    STEPPER_BACK = (
        "xpath",
        "//button[contains(@class,'mat-stepper-previous') or contains(.,'Back')]",
    )
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
    CLOSE_BUTTON = (
        "xpath",
        "//div[contains(@class,'big-model')]//button[contains(@class,'close') or @aria-label='Close']",
    )

    # ==============================================================
    #  LOCATORS — Step 0: Farmer Details (UNIVERSAL FIELDS)
    #  Fill order: upper visible fields first, then scroll-down fields
    # ==============================================================
    PARTY_REFERENCE_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Party Reference')]"
        "/ancestor::mat-form-field//mat-select",
    )
    FARMER_NAME_INPUT = ("css", "input[name='Farmer Name']")
    EMAIL_INPUT = ("css", "input[name='Email']")
    PHONE_NUMBER_INPUT = ("css", "input[name='Phone Number']")
    DATE_OF_BIRTH_INPUT = ("css", "input[placeholder='DD/MM/YYYY']")
    DATE_OF_BIRTH_CALENDAR = ("css", "button[aria-label='Open calendar']")
    AGE_INPUT = ("css", "input[name='Age']")
    GENDER_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Gender')]"
        "/ancestor::mat-form-field//mat-select",
    )
    CATEGORY_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Category')]"
        "/ancestor::mat-form-field//mat-select",
    )
    RELIGION_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Religion')]"
        "/ancestor::mat-form-field//mat-select",
    )
    PASSWORD_INPUT = ("css", "input[name='Password']")
    PHOTO_UPLOAD_INPUT = ("css", "input[type='file']")
    FARMER_CATEGORY_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Farmer Category')]"
        "/ancestor::mat-form-field//mat-select",
    )
    LAND_CLASSIFICATION_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Land Classification')]"
        "/ancestor::mat-form-field//mat-select",
    )
    IS_MEMBER_TOGGLE = (
        "xpath",
        "//app-slide-toggle-v2[.//span[contains(.,'Is Member')]]"
        "//div[contains(@class,'switch-wrapper')]",
    )

    # ==============================================================
    #  LOCATORS — Address table (Current/Permanent Address tabs)
    #  NOTE: Address fields use TABLE/GRID layout — labels may be in
    #  separate cells, NOT inside mat-form-field as mat-label.
    #  Use _find_address_dropdown() for JS-based element discovery.
    # ==============================================================
    ADDRESS_TABLE = ("css", "app-dynamic-details table, .grid-table")
    PIN_CODE_INPUT = ("css", "input[name='Pin Code']")
    ADDRESS_INPUT = ("css", "input[name='Address']")
    ADDRESS2_INPUT = ("css", "input[name='Address2']")
    ADD_ROW_BUTTON = (
        "xpath",
        "//button[contains(.,'Add Row') or contains(@class,'add-row')]",
    )

    # ==============================================================
    #  LOCATORS — Bank Details
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

    # ==============================================================
    #  LOCATORS — Family Details (Borrower Farmer, tab 3)
    # ==============================================================
    FAMILY_MEMBER_NAME_INPUT = ("css", "input[name='Member Name']")
    FAMILY_PHONE_INPUT = ("css", "input[name='Phone Number']")
    FAMILY_DOB_INPUT = ("xpath", "(//input[placeholder='DD/MM/YYYY'])[2]")
    FAMILY_AGE_INPUT = ("css", "input[name='Age']")
    FAMILY_GENDER_SELECT = (
        "xpath",
        "(//mat-label[contains(.,'Gender')]"
        "/ancestor::mat-form-field//mat-select)[2]",
    )
    EDUCATION_OF_FARMER_FAMILY_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Education of Farmer Family')]"
        "/ancestor::mat-form-field//mat-select",
    )
    RELATIONSHIP_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Relationship')]"
        "/ancestor::mat-form-field//mat-select",
    )
    FAMILY_PINCODE_INPUT = ("css", "input[name='Pincode']")
    FAMILY_ADDRESS_INPUT = ("css", "input[name='Address']")
    MARITAL_STATUS_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Marital Status')]"
        "/ancestor::mat-form-field//mat-select",
    )
    NO_OF_CHILDRENS_INPUT = ("css", "input[name='No of Childrens']")
    MEMBER_ANNUAL_INCOME_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Member Annual Income')]"
        "/ancestor::mat-form-field//mat-select",
    )
    OFF_FARM_INCOME_INPUT = ("css", "input[name='Off Farm Income']")

    # ==============================================================
    #  LOCATORS — Other Details (Borrower Farmer, tab 4)
    # ==============================================================
    EDUCATION_QUALIFICATION_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Education Qualification')]"
        "/ancestor::mat-form-field//mat-select",
    )
    ELECTRICITY_AVAILABILITY_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Electricity Availability')]"
        "/ancestor::mat-form-field//mat-select",
    )

    # ==============================================================
    #  LOCATORS — Land Details (Borrower Farmer + FPC Member)
    # ==============================================================
    FARM_NAME_INPUT = ("css", "input[name='Farm Name']")
    NO_OF_OWNER_INPUT = ("css", "input[name='No Of Owner']")
    TOTAL_LAND_ON_DOCUMENT_INPUT = ("css", "input[name='Total Land On Document (hectare)']")
    INDIVIDUAL_LAND_HOLDING_INPUT = ("css", "input[name='Individual Land Holding (hectare)']")
    GAT_NUMBER_INPUT = ("css", "input[name='Gat Number']")
    LAND_COORDINATE_INPUT = ("css", "input[name='Land Coordinate']")
    TOTAL_LAND_IN_HECTARE_INPUT = ("css", "input[name='Total Land In hectare']")
    TOTAL_CULTIVATION_LAND_HECTARE_INPUT = ("css", "input[name='Total Cultivation Land In hectare']")
    TOTAL_CULTIVATION_LAND_ACREAGE_INPUT = ("css", "input[name='Total Cultivation Land in acreage']")
    LAND_OWNERSHIP_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Land ownership') or contains(.,'Land Ownership')]"
        "/ancestor::mat-form-field//mat-select",
    )
    LATITUDE_INPUT = ("css", "input[name='Latitude(Lat)']")
    LONGITUDE_INPUT = ("css", "input[name='Longitude(Log)']")

    # ==============================================================
    #  LOCATORS — Crop Details (Borrower Farmer + FPC Member)
    # ==============================================================
    CROP_FARM_NAME_INPUT = ("xpath", "(//input[name='Farm Name'])[2]")
    CROP_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Crop')]"
        "/ancestor::mat-form-field//mat-select",
    )
    SEASON_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Season')]"
        "/ancestor::mat-form-field//mat-select",
    )
    CULTIVATION_LAND_HECTARE_INPUT = ("css", "input[name='Cultivation Land In hectare']")
    EXPECTED_YIELD_INPUT = ("css", "input[name='Expected Yield projection(in Quintal)']")
    ACTUAL_PRODUCE_INPUT = ("css", "input[name='Actual Produce(in Quintal)']")
    CULTIVATION_LAND_ACREAGE_INPUT = ("css", "input[name='Cultivation Land In acreage']")

    # ==============================================================
    #  LOCATORS — KYC Details (Borrower Farmer + FPC Member)
    # ==============================================================
    KYC_DOCUMENT_SELECT = (
        "xpath",
        "//mat-label[contains(.,'KYC Document')]"
        "/ancestor::mat-form-field//mat-select",
    )
    KYC_NUMBER_INPUT = ("css", "input[name='KYC Number']")

    # ==============================================================
    #  LOCATORS — Vehicle Details (Borrower Farmer only)
    # ==============================================================
    VEHICLE_TYPE_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Vehicle Type')]"
        "/ancestor::mat-form-field//mat-select",
    )
    VEHICLE_NAME_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Vehicle Name')]"
        "/ancestor::mat-form-field//mat-select",
    )

    # ==============================================================
    #  LOCATORS — Income Details (Borrower Farmer only)
    # ==============================================================
    SOURCE_OF_INCOME_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Source of Income')]"
        "/ancestor::mat-form-field//mat-select",
    )
    INCOME_BRACKET_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Income Bracket')]"
        "/ancestor::mat-form-field//mat-select",
    )
    EXACT_AMOUNT_INPUT = ("css", "input[name='Exact Amount']")

    # ==============================================================
    #  LOCATORS — Irrigation Details (Borrower Farmer only)
    # ==============================================================
    SOURCE_OF_IRRIGATION_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Source of Irrigation')]"
        "/ancestor::mat-form-field//mat-select",
    )
    METHOD_OF_IRRIGATION_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Method Of Irrigation')]"
        "/ancestor::mat-form-field//mat-select",
    )

    # ==============================================================
    #  LOCATORS — Award Details (Borrower Farmer only)
    # ==============================================================
    AWARD_NAME_INPUT = ("css", "input[name='Name']")
    AWARD_YEAR_INPUT = ("css", "input[name='Year']")

    # ==============================================================
    #  LOCATORS — Loan Details (Borrower Farmer only)
    # ==============================================================
    LOAN_NAME_INPUT = ("css", "input[name='Loan Name']")
    FACILITY_TYPE_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Facility Type')]"
        "/ancestor::mat-form-field//mat-select",
    )
    PURPOSE_OF_LOAN_INPUT = ("css", "input[name='Purpose Of Loan']")
    AVAILED_FROM_INPUT = ("css", "input[name='Availed From']")
    SANCTIONED_AMOUNT_INPUT = ("css", "input[name='Sanctioned Amount']")
    PRESENT_OUTSTANDING_INPUT = ("css", "input[name='Present Outstanding Amount']")

    # ==============================================================
    #  LOCATORS — Row action buttons
    # ==============================================================
    VIEW_BUTTON = (
        "xpath",
        "//td[contains(text(),'{farmer_name}')]"
        "/ancestor::tr//td[contains(@class,'cdk-column-view')]"
        "//button",
    )
    EDIT_BUTTON = (
        "xpath",
        "//td[contains(text(),'{farmer_name}')]"
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
        """Navigate to the Farmer listing page."""
        log.info("Navigating to Farmer page...")
        self.navigate_to(self.PAGE_URL)
        self.driver.refresh()
        self._wait_for_page_ready()

    def _wait_for_page_ready(self):
        """Wait until the Farmer page is fully loaded."""
        try:
            WebDriverWait(self.driver, EXPLICIT_WAIT).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, "table#excel-table")
                )
            )
            log.info("Farmer table loaded")
        except TimeoutException:
            log.warning("Farmer table not found, page may be empty")

        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "ul.tbl-export-btn")
                )
            )
            self.wait_seconds(1)
            log.info("Farmer toolbar ready")
        except TimeoutException:
            log.warning("Toolbar not found")
            self.wait_seconds(3)

    def is_page_loaded(self):
        """Check if the Farmer listing page has loaded."""
        return self.is_displayed(self.TABLE, timeout=10)

    # ==============================================================
    #  Overlay cleanup — NEVER use Keys.ESCAPE
    #  FIX: Catch InvalidSessionIdException to prevent session death cascade
    # ==============================================================

    def _force_close_panels(self):
        """Remove ALL select overlay panes from the DOM via JS.

        FIX: Wrapped in try/except to catch InvalidSessionIdException.
        If the session is dead, there is no point trying to clean up overlays —
        re-raising would cause a cascade of failures in the calling code that
        tries to interact with the dead session.
        """
        try:
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
        except InvalidSessionIdException:
            log.warning("Session is dead in _force_close_panels() — cannot clean up overlays")
            raise
        except Exception as e:
            log.warning(f"_force_close_panels() failed: {e}")

    def _close_select_panel(self):
        """Try backdrop click first; fall back to JS removal.

        FIX: Catch InvalidSessionIdException to prevent session death cascade.
        If the session is already dead, we cannot interact with any elements.
        """
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
                except InvalidSessionIdException:
                    log.warning("Session dead while clicking backdrop in _close_select_panel()")
                    raise
                except Exception:
                    pass
        except InvalidSessionIdException:
            log.warning("Session dead in _close_select_panel() — re-raising")
            raise
        except Exception:
            pass

        try:
            self._force_close_panels()
        except InvalidSessionIdException:
            raise
        except Exception:
            pass

    # ==============================================================
    #  Toolbar actions
    # ==============================================================

    def open_add_form(self):
        """Click the ADD (+) button to open the create form."""
        log.info("Clicking ADD Farmer button...")
        self._wait_for_toolbar()

        # Strategy 1: button.erp-add-btn
        try:
            btn = self.driver.find_element(By.CSS_SELECTOR, "button.erp-add-btn")
            if btn.is_displayed():
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});"
                    "arguments[0].click();", btn,
                )
                self.wait_seconds(1.5)
                if self._is_form_popup_open():
                    self._wait_for_form_content(timeout=5)
                    log.info("ADD form opened via erp-add-btn")
                    return
        except Exception:
            pass

        # Strategy 2: mini-fab button with 'add' icon
        try:
            add_btns = self.driver.find_elements(By.CSS_SELECTOR, "button.mat-mdc-mini-fab")
            for btn in add_btns:
                try:
                    icon = btn.find_element(By.CSS_SELECTOR, "mat-icon")
                    if icon.text.strip().lower() == "add" and btn.is_displayed():
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({block:'center'});"
                            "arguments[0].click();", btn,
                        )
                        self.wait_seconds(1.5)
                        if self._is_form_popup_open():
                            log.info("ADD form opened via mini-fab icon")
                            return
                except Exception:
                    continue
        except Exception:
            pass

        raise Exception("ADD button not found or not clickable")

    def _wait_for_toolbar(self):
        """Wait for the toolbar and ADD button."""
        for attempt in range(3):
            try:
                add_container = self.driver.find_elements(By.CSS_SELECTOR, "button.erp-add-btn")
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

    def _wait_for_form_content(self, timeout=5):
        """Wait for form content to render inside the popup."""
        import time as _time
        deadline = _time.time() + timeout
        while _time.time() < deadline:
            try:
                elements = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    "div.big-model mat-stepper, div.big-model input, "
                    "mat-dialog-container mat-stepper, mat-dialog-container input",
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
        return False

    def is_add_form_open(self):
        """Check if the Add form popup is open."""
        return self._is_form_popup_open()

    def click_refresh(self):
        """Click the Refresh button."""
        log.info("Clicking Refresh button...")
        try:
            refresh_btns = self.driver.find_elements(By.CSS_SELECTOR, "button.mat-mdc-mini-fab")
            for btn in refresh_btns:
                try:
                    icon = btn.find_element(By.CSS_SELECTOR, "mat-icon")
                    if icon.text.strip().lower() == "refresh" and btn.is_displayed():
                        self.driver.execute_script("arguments[0].click();", btn)
                        self.wait_seconds(2)
                        return
                except Exception:
                    continue
        except Exception:
            pass

    # ==============================================================
    #  Stepper navigation
    # ==============================================================

    def click_stepper_next(self):
        """Click the 'Next' button to advance to the next stepper tab."""
        log.info("Clicking stepper Next...")
        self._force_close_panels()

        try:
            next_btns = self.driver.find_elements(
                By.CSS_SELECTOR, "button.mat-stepper-next, button.mat-mdc-stepper-next"
            )
            for btn in next_btns:
                try:
                    if btn.is_displayed() and btn.is_enabled():
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({block:'center'});"
                            "arguments[0].click();", btn,
                        )
                        self.wait_seconds(1)
                        log.info("Stepper Next clicked via CSS class")
                        return True
                except Exception:
                    continue
        except Exception:
            pass

        try:
            next_btns = self.driver.find_elements(By.XPATH, "//button[contains(.,'Next')]")
            for btn in next_btns:
                try:
                    if btn.is_displayed() and btn.is_enabled():
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({block:'center'});"
                            "arguments[0].click();", btn,
                        )
                        self.wait_seconds(1)
                        log.info("Stepper Next clicked via text")
                        return True
                except Exception:
                    continue
        except Exception:
            pass

        try:
            self.driver.execute_script("""
                var btns = document.querySelectorAll('.big-model button, mat-dialog-container button');
                for (var i = 0; i < btns.length; i++) {
                    if (btns[i].textContent.trim() === 'Next') { btns[i].click(); break; }
                }
            """)
            self.wait_seconds(1)
            return True
        except Exception:
            pass

        log.warning("Stepper Next not found")
        return False

    def click_stepper_back(self):
        """Click the 'Back' button to go to the previous stepper tab."""
        log.info("Clicking stepper Back...")
        self._force_close_panels()

        try:
            back_btns = self.driver.find_elements(
                By.CSS_SELECTOR, "button.mat-stepper-previous, button.mat-mdc-stepper-previous"
            )
            for btn in back_btns:
                try:
                    if btn.is_displayed() and btn.is_enabled():
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({block:'center'});"
                            "arguments[0].click();", btn,
                        )
                        self.wait_seconds(1)
                        return True
                except Exception:
                    continue
        except Exception:
            pass
        return False

    def get_current_step_index(self):
        """Get the 0-based index of the currently active stepper step.
        NOTE: This returns the index among ALL mat-step-header elements,
        which may include the Farmer Details step. Use get_active_tab_name()
        instead for reliable tab identification.
        """
        try:
            steps = self.driver.find_elements(By.CSS_SELECTOR, "mat-step-header")
            for i, step in enumerate(steps):
                try:
                    classes = step.get_attribute("class") or ""
                    if "selected" in classes or "active" in classes:
                        return i
                except Exception:
                    continue
            for i, step in enumerate(steps):
                try:
                    if step.get_attribute("aria-selected") == "true":
                        return i
                except Exception:
                    continue
        except Exception:
            pass
        return -1

    def get_active_tab_name(self):
        """Get the name of the currently active/selected stepper tab DIRECTLY.

        This bypasses the index-alignment bug where get_current_step_index()
        counts ALL headers (including Farmer Details) but get_stepper_tab_names()
        may skip some. Instead, this method reads the label text directly from
        the selected header element — no index lookup needed.

        FIX: Also check for 'mat-step-label-selected' CSS class, which Angular
        Material adds to the label span of the active step. This is more reliable
        than checking only 'selected'/'active' in the header's class list.
        """
        try:
            headers = self.driver.find_elements(By.CSS_SELECTOR, "mat-step-header")
            for header in headers:
                try:
                    classes = header.get_attribute("class") or ""
                    aria_selected = header.get_attribute("aria-selected") or ""

                    # FIX: Also check for mat-step-label-selected on inner label
                    has_selected_label = False
                    try:
                        selected_labels = header.find_elements(
                            By.CSS_SELECTOR, ".mat-step-label-selected, .mat-step-label-active"
                        )
                        has_selected_label = len(selected_labels) > 0
                    except Exception:
                        pass

                    is_active = (
                        "selected" in classes
                        or "active" in classes
                        or aria_selected == "true"
                        or has_selected_label  # FIX: check inner label class
                    )
                    if not is_active:
                        continue

                    # Try .mat-step-text-label first (standard Angular Material)
                    try:
                        label = header.find_element(
                            By.CSS_SELECTOR, ".mat-step-text-label"
                        )
                        name = label.text.strip()
                        if name:
                            return name
                    except Exception:
                        pass

                    # Fallback: .mat-step-label
                    try:
                        label = header.find_element(
                            By.CSS_SELECTOR, ".mat-step-label"
                        )
                        name = label.text.strip()
                        if name:
                            return name
                    except Exception:
                        pass

                    # Fallback: any span/div with text inside header
                    try:
                        children = header.find_elements(By.CSS_SELECTOR, "span, div")
                        for child in children:
                            text = child.text.strip()
                            if text and len(text) > 2:
                                return text
                    except Exception:
                        pass

                except Exception:
                    continue
        except Exception:
            pass
        return ""

    def get_stepper_tab_count(self):
        """Count the number of stepper tab headers visible."""
        try:
            steps = self.driver.find_elements(By.CSS_SELECTOR, "mat-step-header")
            return len(steps)
        except Exception:
            return 0

    def get_stepper_tab_names(self):
        """Get the names of all visible stepper tabs."""
        try:
            steps = self.driver.find_elements(By.CSS_SELECTOR, "mat-step-header")
            names = []
            for step in steps:
                try:
                    label = step.find_element(By.CSS_SELECTOR, ".mat-step-text-label")
                    names.append(label.text.strip())
                except Exception:
                    names.append("")
            return names
        except Exception:
            return []

    def click_stepper_header(self, index):
        """Click on a stepper tab header by index (workaround for BUG-F02)."""
        try:
            steps = self.driver.find_elements(By.CSS_SELECTOR, "mat-step-header")
            if index < len(steps):
                self.driver.execute_script("arguments[0].click();", steps[index])
                self.wait_seconds(1)
                return True
        except Exception:
            pass
        return False

    # ==============================================================
    #  Step 0: Fill Farmer Details (UNIVERSAL FIELDS)
    #  RULE: Fill upper/visible fields FIRST, then scroll-down fields
    #  Farmer Category MUST be filled LAST (triggers stepper tab creation)
    # ==============================================================

    def fill_step0(self, data):
        """Fill all fields on Step 0 — Farmer Details.

        FILL ORDER (business rule):
          1. Upper visible text inputs (no scroll needed)
          2. Upper visible dropdowns (may need scroll)
          3. Farmer Category LAST (triggers stepper tab creation)
        """
        log.info("Filling Step 0: Farmer Details...")

        # === 1. UPPER VISIBLE TEXT INPUTS (no scroll needed) ===
        if data.get("farmer_name"):
            self.type_text(self.FARMER_NAME_INPUT, data["farmer_name"], clear_first=True)
        if data.get("email"):
            self.type_text(self.EMAIL_INPUT, data["email"], clear_first=True)
        if data.get("phone_number"):
            self.type_text(self.PHONE_NUMBER_INPUT, data["phone_number"], clear_first=True)
        if data.get("password"):
            self.type_text(self.PASSWORD_INPUT, data["password"], clear_first=True)
        if data.get("date_of_birth"):
            self.type_text(self.DATE_OF_BIRTH_INPUT, data["date_of_birth"], clear_first=True)
            self.wait_seconds(0.5)

        # === 2. SCROLL-DOWN DROPDOWNS (may need scrolling into view) ===
        self._fill_dropdown_if_provided(self.GENDER_SELECT, data.get("gender"))
        self._fill_dropdown_if_provided(self.CATEGORY_SELECT, data.get("category"))
        self._fill_dropdown_if_provided(self.RELIGION_SELECT, data.get("religion"))
        self._fill_dropdown_if_provided(self.LAND_CLASSIFICATION_SELECT, data.get("land_classification"))

        # === 3. FARMER CATEGORY LAST — it triggers stepper tab creation ===
        if data.get("farmer_category"):
            self._select_farmer_category(data["farmer_category"])

        # Toggle switch (bottom of form)
        if data.get("is_member_of_fpc") is not None:
            self._set_toggle_to(self.IS_MEMBER_TOGGLE, data["is_member_of_fpc"])

        log.info("Step 0 filled successfully")

    def _fill_dropdown_if_provided(self, locator, value):
        """Fill a mat-select dropdown if a value is provided.
        If value is None, pick the first valid option (non-placeholder).
        If value is empty string, skip.
        """
        if value is None:
            # Pick a random non-placeholder option
            self._select_random_from_dropdown(locator)
        elif value == "":
            return  # Skip empty strings
        else:
            self._select_mat_option(locator, value)

    def _select_mat_option(self, dropdown_locator, option_text):
        """Select a specific option in a mat-select dropdown using JS click."""
        try:
            dropdown = self.find_clickable_element(dropdown_locator, timeout=5)
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", dropdown)
            self.wait_seconds(0.3)
            self.driver.execute_script("arguments[0].click();", dropdown)
            self.wait_seconds(0.8)

            # Find and click the option
            options = self.driver.find_elements(By.CSS_SELECTOR, "div[role='listbox'] mat-option")
            for opt in options:
                try:
                    if opt.text.strip() == option_text and opt.is_displayed():
                        self.driver.execute_script("arguments[0].click();", opt)
                        self.wait_seconds(0.5)
                        self._close_select_panel()
                        return
                except Exception:
                    continue

            # Fallback: close panel if option not found
            self._close_select_panel()
            log.warning(f"Option '{option_text}' not found in dropdown")
        except Exception as e:
            log.warning(f"Dropdown selection failed: {e}")
            self._close_select_panel()

    def _select_random_from_dropdown(self, dropdown_locator):
        """Select the first valid non-placeholder option from a dropdown."""
        try:
            dropdown = self.find_clickable_element(dropdown_locator, timeout=5)
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", dropdown)
            self.wait_seconds(0.3)
            self.driver.execute_script("arguments[0].click();", dropdown)
            self.wait_seconds(0.8)

            options = self.driver.find_elements(By.CSS_SELECTOR, "div[role='listbox'] mat-option")
            valid_options = []
            for opt in options:
                try:
                    text = opt.text.strip()
                    if text and not text.startswith("Select ") and opt.is_displayed():
                        valid_options.append(opt)
                except Exception:
                    continue

            if valid_options:
                chosen = valid_options[0]  # Pick first valid option for consistency
                self.driver.execute_script("arguments[0].click();", chosen)
                self.wait_seconds(0.5)

            self._close_select_panel()
        except Exception as e:
            log.warning(f"Random dropdown selection failed: {e}")
            self._close_select_panel()

    def _select_farmer_category(self, category_text):
        """Select a farmer category from the multi-select dropdown."""
        try:
            dropdown = self.find_clickable_element(self.FARMER_CATEGORY_SELECT, timeout=5)
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", dropdown)
            self.wait_seconds(0.3)
            self.driver.execute_script("arguments[0].click();", dropdown)
            self.wait_seconds(0.8)

            options = self.driver.find_elements(By.CSS_SELECTOR, "div[role='listbox'] mat-option")
            for opt in options:
                try:
                    if opt.text.strip() == category_text and opt.is_displayed():
                        self.driver.execute_script("arguments[0].click();", opt)
                        self.wait_seconds(0.5)
                        break
                except Exception:
                    continue

            self._close_select_panel()
            log.info(f"Farmer Category selected: {category_text}")
        except Exception as e:
            log.warning(f"Farmer Category selection failed: {e}")
            self._close_select_panel()

    def _set_toggle_to(self, toggle_locator, desired_state):
        """Set a toggle switch to the desired state (True=ON, False=OFF)."""
        try:
            toggle = self.find_visible_element(toggle_locator, timeout=5)
            checkbox = toggle.find_element(By.CSS_SELECTOR, "input[type='checkbox']")
            current_state = checkbox.is_selected()

            if current_state != desired_state:
                self.driver.execute_script("arguments[0].click();", toggle)
                self.wait_seconds(0.5)
                log.info(f"Toggle set to {'ON' if desired_state else 'OFF'}")
        except Exception as e:
            log.warning(f"Toggle switch failed: {e}")

    # ==============================================================
    #  Address Tabs: Fill Current/Permanent Address
    #  RULE: Fill upper visible fields first (Country, State, District),
    #  then scroll down for lower fields (Taluka, Village, Pin Code, Address)
    #  Country is ALWAYS "India" (other countries lack cascading data)
    # ==============================================================

    def fill_current_address(self, data):
        """Fill the Current Address Details tab."""
        log.info("Filling Current Address...")
        self._fill_address_row(data, is_permanent=False)

    def fill_permanent_address(self, data):
        """Fill the Permanent Address Details tab."""
        log.info("Filling Permanent Address...")
        self._fill_address_row(data, is_permanent=True)

    def _find_address_dropdown(self, label_text):
        """Find a mat-select dropdown in the currently active tab.

        Uses JavaScript-based multi-strategy search because address fields
        may use TABLE/GRID layout where labels are in separate cells,
        NOT inside mat-form-field as mat-label elements.

        FIX: Angular Material renders ALL tab contents in the DOM simultaneously.
        Inactive panels have `inert=""` attribute and class
        `mat-horizontal-stepper-content-previous`. Active panel has class
        `mat-horizontal-stepper-content-current` and NO `inert` attribute.
        The dropdown search MUST be scoped to the ACTIVE panel only, otherwise
        we find elements in inert panels that cannot be interacted with.

        Strategies (in order):
          1. JS: Find ACTIVE panel -> mat-label -> mat-form-field -> mat-select
          2. JS: Find ACTIVE panel -> table row with label -> mat-select
          3. JS: Find ACTIVE panel -> any leaf text -> closest container -> mat-select
          4. XPath: global search for mat-label -> mat-form-field -> mat-select
          5. Debug dump if all strategies fail
        """
        # ---- Strategy 1: JS - ACTIVE panel -> mat-label inside mat-form-field ----
        try:
            el = self.driver.execute_script("""
                var labelText = arguments[0];
                var popup = document.querySelector('.big-model, mat-dialog-container');
                if (!popup) return null;

                // FIX: Find the ACTIVE stepper panel only
                var activeContent = popup.querySelector('div.mat-horizontal-stepper-content-current');
                if (!activeContent) {
                    // Fallback: find any stepper content without inert
                    var allPanels = popup.querySelectorAll('div[role="tabpanel"].mat-horizontal-stepper-content');
                    for (var p = 0; p < allPanels.length; p++) {
                        if (!allPanels[p].hasAttribute('inert')) {
                            activeContent = allPanels[p];
                            break;
                        }
                    }
                }
                if (!activeContent) return null;

                // Search ONLY within the active panel
                var labels = activeContent.querySelectorAll('mat-label');
                for (var i = 0; i < labels.length; i++) {
                    if (labels[i].textContent.trim().includes(labelText)) {
                        var field = labels[i].closest('mat-form-field, .mat-mdc-form-field');
                        if (field) {
                            var select = field.querySelector('mat-select');
                            if (select && select.offsetParent !== null) return select;
                        }
                    }
                }
                return null;
            """, label_text)
            if el:
                log.info(f"Found address dropdown '{label_text}' via JS active-panel mat-label strategy")
                return el
        except Exception as e:
            log.warning(f"JS Strategy 1 (active-panel mat-label) failed for '{label_text}': {e}")

        # ---- Strategy 2: JS - ACTIVE panel -> table row with label text -> mat-select ----
        try:
            el = self.driver.execute_script("""
                var labelText = arguments[0];
                var popup = document.querySelector('.big-model, mat-dialog-container');
                if (!popup) return null;

                // FIX: Find the ACTIVE stepper panel only
                var activeContent = popup.querySelector('div.mat-horizontal-stepper-content-current');
                if (!activeContent) {
                    var allPanels = popup.querySelectorAll('div[role="tabpanel"].mat-horizontal-stepper-content');
                    for (var p = 0; p < allPanels.length; p++) {
                        if (!allPanels[p].hasAttribute('inert')) {
                            activeContent = allPanels[p];
                            break;
                        }
                    }
                }
                if (!activeContent) return null;

                var rows = activeContent.querySelectorAll('tr, .grid-row, .form-row');
                for (var i = 0; i < rows.length; i++) {
                    var cells = rows[i].querySelectorAll('td, th, .grid-cell, .form-cell');
                    for (var j = 0; j < cells.length; j++) {
                        var cellText = cells[j].textContent.trim();
                        if (cellText.includes(labelText) || cellText.replace(/\\s*\\*/g, '').includes(labelText)) {
                            var select = rows[i].querySelector('mat-select');
                            if (select && select.offsetParent !== null) return select;
                        }
                    }
                }
                return null;
            """, label_text)
            if el:
                log.info(f"Found address dropdown '{label_text}' via JS active-panel table-row strategy")
                return el
        except Exception as e:
            log.warning(f"JS Strategy 2 (active-panel table-row) failed for '{label_text}': {e}")

        # ---- Strategy 3: JS - ACTIVE panel -> any leaf text -> closest container -> mat-select ----
        try:
            el = self.driver.execute_script("""
                var labelText = arguments[0];
                var popup = document.querySelector('.big-model, mat-dialog-container');
                if (!popup) return null;

                // FIX: Find the ACTIVE stepper panel only
                var activeContent = popup.querySelector('div.mat-horizontal-stepper-content-current');
                if (!activeContent) {
                    var allPanels = popup.querySelectorAll('div[role="tabpanel"].mat-horizontal-stepper-content');
                    for (var p = 0; p < allPanels.length; p++) {
                        if (!allPanels[p].hasAttribute('inert')) {
                            activeContent = allPanels[p];
                            break;
                        }
                    }
                }
                if (!activeContent) return null;

                var allEls = activeContent.querySelectorAll('span, div, label, p, td, th');
                for (var i = 0; i < allEls.length; i++) {
                    var el = allEls[i];
                    // Only check leaf-ish elements (direct text, no child elements with same text)
                    if (el.children.length === 0 || el.tagName === 'TD' || el.tagName === 'TH' || el.tagName === 'LABEL') {
                        var text = el.textContent.trim().replace(/\\s*\\*/g, '').replace(/\\s*:/g, '');
                        if (text === labelText || text.startsWith(labelText)) {
                            // Found text match — look for mat-select in the same form-field or row
                            var container = el.closest('mat-form-field, .mat-mdc-form-field, tr, .grid-row, .form-row, .row');
                            if (container) {
                                var select = container.querySelector('mat-select');
                                if (select && select.offsetParent !== null) return select;
                            }
                            // Try parent's parent
                            if (el.parentElement) {
                                var parentContainer = el.parentElement.closest('mat-form-field, .mat-mdc-form-field, tr, .grid-row, .form-row');
                                if (parentContainer) {
                                    var select = parentContainer.querySelector('mat-select');
                                    if (select && select.offsetParent !== null) return select;
                                }
                            }
                        }
                    }
                }
                return null;
            """, label_text)
            if el:
                log.info(f"Found address dropdown '{label_text}' via JS active-panel leaf-text strategy")
                return el
        except Exception as e:
            log.warning(f"JS Strategy 3 (active-panel leaf-text) failed for '{label_text}': {e}")

        # ---- Strategy 4: XPath - global search within popup ----
        xpaths = [
            # Within big-model popup
            f"//div[contains(@class,'big-model')]//mat-label[contains(.,'{label_text}')]/ancestor::mat-form-field//mat-select",
            # Within mat-dialog-container
            f"//mat-dialog-container//mat-label[contains(.,'{label_text}')]/ancestor::mat-form-field//mat-select",
            # Global - first visible match
            f"(//mat-label[contains(.,'{label_text}')]/ancestor::mat-form-field//mat-select)[1]",
        ]
        for xpath in xpaths:
            try:
                by, value = self._parse_locator(("xpath", xpath))
                elements = self.driver.find_elements(by, value)
                for el in elements:
                    try:
                        if el.is_displayed():
                            log.info(f"Found address dropdown '{label_text}' via XPath strategy")
                            return el
                    except Exception:
                        continue
            except Exception:
                continue

        # ---- All strategies failed — dump DOM for debugging ----
        log.warning(f"Address dropdown '{label_text}' not found — dumping DOM for debug")
        self._debug_dump_address_dom()
        return None

    def _debug_dump_address_dom(self):
        """Dump the DOM structure of the popup for debugging address dropdown issues.

        This method is called when _find_address_dropdown() fails to help
        diagnose the actual DOM structure of the address form.
        """
        try:
            result = self.driver.execute_script("""
                var output = [];
                var popup = document.querySelector('.big-model, mat-dialog-container');
                if (!popup) return 'No popup found';

                // 0. Stepper panel info (FIX: show which panel is active)
                var allPanels = popup.querySelectorAll('div[role="tabpanel"].mat-horizontal-stepper-content');
                output.push('=== stepper panels: ' + allPanels.length + ' ===');
                for (var p = 0; p < allPanels.length; p++) {
                    var hasInert = allPanels[p].hasAttribute('inert');
                    var classes = allPanels[p].className;
                    var isActive = !hasInert && classes.indexOf('current') >= 0;
                    output.push('  panel[' + p + '] inert=' + hasInert + ' class="' + classes.substring(0, 80) + '" active=' + isActive);
                }

                // 1. All mat-select elements
                var selects = popup.querySelectorAll('mat-select');
                output.push('=== mat-select elements: ' + selects.length + ' ===');
                for (var i = 0; i < selects.length; i++) {
                    var field = selects[i].closest('mat-form-field, .mat-mdc-form-field');
                    var label = field ? field.querySelector('mat-label') : null;
                    var name = selects[i].getAttribute('name');
                    var visible = selects[i].offsetParent !== null;
                    var inInert = false;
                    var parent = selects[i].parentElement;
                    while (parent) {
                        if (parent.hasAttribute && parent.hasAttribute('inert')) { inInert = true; break; }
                        parent = parent.parentElement;
                    }
                    output.push('  [' + i + '] name=' + name + ' label=' + (label ? label.textContent.trim() : 'N/A') + ' visible=' + visible + ' inInertPanel=' + inInert);
                }

                // 2. All mat-label elements
                var labels = popup.querySelectorAll('mat-label');
                output.push('=== mat-label elements: ' + labels.length + ' ===');
                for (var i = 0; i < labels.length; i++) {
                    var field = labels[i].closest('mat-form-field, .mat-mdc-form-field');
                    var hasSelect = field ? field.querySelector('mat-select') : null;
                    var inInert = false;
                    var parent = labels[i].parentElement;
                    while (parent) {
                        if (parent.hasAttribute && parent.hasAttribute('inert')) { inInert = true; break; }
                        parent = parent.parentElement;
                    }
                    output.push('  [' + i + '] text="' + labels[i].textContent.trim() + '" hasMatSelect=' + (hasSelect ? 'yes' : 'no') + ' inInertPanel=' + inInert);
                }

                // 3. All input elements with name attribute
                var inputs = popup.querySelectorAll('input[name]');
                output.push('=== input[name] elements: ' + inputs.length + ' ===');
                for (var i = 0; i < inputs.length; i++) {
                    output.push('  [' + i + '] name="' + inputs[i].getAttribute('name') + '" visible=' + (inputs[i].offsetParent !== null));
                }

                // 4. Table/grid structure
                var tables = popup.querySelectorAll('table, .grid-table, app-dynamic-details');
                output.push('=== table/grid elements: ' + tables.length + ' ===');
                for (var t = 0; t < tables.length; t++) {
                    var rows = tables[t].querySelectorAll('tr');
                    output.push('  table[' + t + ']: ' + rows.length + ' rows');
                    for (var r = 0; r < Math.min(rows.length, 3); r++) {
                        var cells = rows[r].querySelectorAll('td, th');
                        var cellTexts = [];
                        for (var c = 0; c < cells.length; c++) {
                            cellTexts.push(cells[c].textContent.trim().substring(0, 30));
                        }
                        output.push('    row[' + r + ']: ' + cellTexts.join(' | '));
                    }
                }

                // 5. All visible select-like elements (mat-select, native select)
                var nativeSelects = popup.querySelectorAll('select');
                output.push('=== native select elements: ' + nativeSelects.length + ' ===');

                return output.join('\\n');
            """)
            log.info(f"ADDRESS DOM DUMP:\n{result}")
        except Exception as e:
            log.warning(f"Debug DOM dump failed: {e}")

    def _fill_address_row(self, data, is_permanent=False):
        """Fill an address table row with cascading dropdowns.

        FILL ORDER (business rule):
          1. Upper visible dropdowns: Country -> State -> District
          2. Scroll-down dropdowns: Taluka -> Village
          3. Scroll-down text inputs: Pin Code -> Address -> Address2

        Country is ALWAYS forced to 'India' since other countries
        lack cascading data.
        """
        addr_type = 'Permanent' if is_permanent else 'Current'
        log.info(f"Filling {addr_type} Address...")

        # Wait for the address form to load in the active tab
        self.wait_seconds(1.5)

        # Scroll the popup content to the top first
        self._scroll_popup_to_top()
        self.wait_seconds(0.3)

        # === 1. UPPER VISIBLE DROPDOWNS (no scroll needed initially) ===
        # Country — ALWAYS "India"
        self._fill_cascading_dropdown("Country", "India")

        # State, District — still in upper area
        self._fill_cascading_dropdown("State", data.get("state"))
        self._fill_cascading_dropdown("District", data.get("district"))

        # === 2. SCROLL-DOWN DROPDOWNS (may need scrolling) ===
        self._fill_cascading_dropdown("Taluka", data.get("taluka"))
        self._fill_cascading_dropdown("Village", data.get("village"))

        # === 3. SCROLL-DOWN TEXT INPUTS ===
        if data.get("pin_code"):
            self._scroll_popup_to_element(self.PIN_CODE_INPUT)
            self.type_text(self.PIN_CODE_INPUT, data["pin_code"], clear_first=True)
        if data.get("address"):
            self._scroll_popup_to_element(self.ADDRESS_INPUT)
            self.type_text(self.ADDRESS_INPUT, data["address"], clear_first=True)
        if data.get("address2"):
            self._scroll_popup_to_element(self.ADDRESS2_INPUT)
            self.type_text(self.ADDRESS2_INPUT, data["address2"], clear_first=True)

        log.info(f"{addr_type} Address filled")

    def _scroll_popup_to_top(self):
        """Scroll the popup/dialog container to the top."""
        self.driver.execute_script("""
            var popup = document.querySelector('.big-model, mat-dialog-container, .cdk-dialog-container');
            if (popup) {
                // Try scrolling the popup itself
                popup.scrollTop = 0;
                // Also try scrolling any inner scrollable containers
                var scrollables = popup.querySelectorAll('[style*="overflow"], .mat-stepper-content, .cdk-step-content');
                for (var i = 0; i < scrollables.length; i++) {
                    scrollables[i].scrollTop = 0;
                }
            }
        """)
        self.wait_seconds(0.3)

    def _scroll_popup_to_element(self, locator):
        """Scroll the popup container so that the target element is visible.

        Unlike scroll_to_element() which scrolls the page, this scrolls
        the popup/dialog container which has its own scroll context.
        """
        try:
            element = self.find_element(locator)
            self.driver.execute_script("""
                var el = arguments[0];
                // Find the scrollable parent (popup container)
                var parent = el.parentElement;
                while (parent) {
                    var style = window.getComputedStyle(parent);
                    if ((style.overflow === 'auto' || style.overflow === 'scroll' ||
                         style.overflowY === 'auto' || style.overflowY === 'scroll') &&
                        parent.scrollHeight > parent.clientHeight) {
                        // Found the scrollable parent
                        var elRect = el.getBoundingClientRect();
                        var parentRect = parent.getBoundingClientRect();
                        var scrollOffset = elRect.top - parentRect.top + parent.scrollTop - (parentRect.height / 3);
                        parent.scrollTop = scrollOffset;
                        break;
                    }
                    parent = parent.parentElement;
                }
                // Also scroll the element into view as a fallback
                el.scrollIntoView({block: 'center', behavior: 'smooth'});
            """, element)
            self.wait_seconds(0.3)
        except Exception as e:
            log.warning(f"Scroll to element failed: {e}")

    def _fill_cascading_dropdown(self, label_text, value):
        """Fill a cascading dropdown in the active address tab.

        Uses _find_address_dropdown() to locate the correct element
        using JS-based multi-strategy search. Handles both specific
        value selection and first-valid-option selection (when value is None).

        FIX: Added stale element retry — if StaleElementReferenceException
        occurs during option selection, re-find the dropdown and retry.
        FIX: Better option matching using .strip().lower() for case-insensitive
        and whitespace-tolerant comparison.
        FIX: Longer wait (2s) for dependent dropdowns to populate after
        parent selection.
        """
        if value == "":
            return

        max_retries = 3
        for attempt in range(max_retries):
            try:
                dropdown = self._find_address_dropdown(label_text)
                if dropdown is None:
                    log.warning(f"Address dropdown '{label_text}' not found in active tab")
                    return

                # Scroll the dropdown into view within the popup
                self.driver.execute_script("""
                    var el = arguments[0];
                    // Scroll within popup container
                    var parent = el.parentElement;
                    while (parent) {
                        var style = window.getComputedStyle(parent);
                        if ((style.overflow === 'auto' || style.overflow === 'scroll' ||
                             style.overflowY === 'auto' || style.overflowY === 'scroll') &&
                            parent.scrollHeight > parent.clientHeight) {
                            var elRect = el.getBoundingClientRect();
                            var parentRect = parent.getBoundingClientRect();
                            var scrollOffset = elRect.top - parentRect.top + parent.scrollTop - (parentRect.height / 3);
                            parent.scrollTop = scrollOffset;
                            break;
                        }
                        parent = parent.parentElement;
                    }
                    el.scrollIntoView({block: 'center'});
                """, dropdown)
                self.wait_seconds(0.3)

                # Click to open the dropdown
                self.driver.execute_script("arguments[0].click();", dropdown)
                self.wait_seconds(0.8)

                if value is None:
                    # Pick first valid (non-placeholder) option
                    options = self.driver.find_elements(By.CSS_SELECTOR, "div[role='listbox'] mat-option")
                    valid_options = []
                    for opt in options:
                        try:
                            text = opt.text.strip()
                            if text and not text.startswith("Select ") and opt.is_displayed():
                                valid_options.append(opt)
                        except StaleElementReferenceException:
                            log.warning(f"Stale element while scanning options for '{label_text}', retry {attempt + 1}")
                            break
                        except Exception:
                            continue
                    else:
                        # Only executed if the for-loop didn't break (no stale elements)
                        if valid_options:
                            self.driver.execute_script("arguments[0].click();", valid_options[0])
                            self.wait_seconds(0.5)
                            log.info(f"Address '{label_text}' selected: {valid_options[0].text.strip()}")
                        self._close_select_panel()
                        self.wait_seconds(2)  # FIX: longer wait for dependent dropdown
                        return

                    # If we broke out due to stale element, close and retry
                    self._close_select_panel()
                    self.wait_seconds(0.5)
                    continue  # retry

                else:
                    # Select specific option
                    # FIX: Use case-insensitive, whitespace-tolerant matching
                    value_lower = value.strip().lower()
                    options = self.driver.find_elements(By.CSS_SELECTOR, "div[role='listbox'] mat-option")
                    found = False
                    for opt in options:
                        try:
                            opt_text = opt.text.strip()
                            if opt_text.lower() == value_lower and opt.is_displayed():
                                self.driver.execute_script("arguments[0].click();", opt)
                                self.wait_seconds(0.5)
                                log.info(f"Address '{label_text}' selected: {value}")
                                self._close_select_panel()
                                self.wait_seconds(2)  # FIX: longer wait for dependent dropdown
                                return
                        except StaleElementReferenceException:
                            log.warning(f"Stale element while selecting '{value}' in '{label_text}', retry {attempt + 1}")
                            self._close_select_panel()
                            self.wait_seconds(0.5)
                            break  # break inner for-loop, retry outer loop
                        except Exception:
                            continue
                    else:
                        # For-loop completed without break (no stale exception)
                        if not found:
                            log.warning(f"Option '{value}' not found in address '{label_text}' dropdown")

                    self._close_select_panel()
                    self.wait_seconds(2)  # FIX: longer wait for dependent dropdown
                    return

            except StaleElementReferenceException:
                log.warning(f"StaleElementReferenceException in _fill_cascading_dropdown('{label_text}'), retry {attempt + 1}/{max_retries}")
                self._close_select_panel()
                self.wait_seconds(0.5)
                continue
            except Exception as e:
                log.warning(f"Address cascading dropdown '{label_text}' failed: {e}")
                self._close_select_panel()
                return

        log.warning(f"Address cascading dropdown '{label_text}' failed after {max_retries} retries")

    # ==============================================================
    #  Bank Details Tab
    # ==============================================================

    def fill_bank_details(self, data):
        """Fill the Bank Details tab.

        FILL ORDER: upper visible text inputs first, then scroll-down fields.
        NOTE: Account Type label has a trailing tab character: "Account Type\\t"
        so the XPath contains(.,'Account Type') still matches.
        """
        log.info("Filling Bank Details...")

        # Upper visible text inputs
        if data.get("bank_name"):
            self.type_text(self.BANK_NAME_INPUT, data["bank_name"], clear_first=True)
        if data.get("branch"):
            self.type_text(self.BRANCH_INPUT, data["branch"], clear_first=True)
        if data.get("ifsc_code"):
            self.type_text(self.IFSC_CODE_INPUT, data["ifsc_code"], clear_first=True)

        # Dropdowns (may need scroll)
        self._fill_dropdown_if_provided(self.ACCOUNT_TYPE_SELECT, data.get("account_type"))

        # Lower text inputs
        if data.get("account_holder_name"):
            self.type_text(self.ACCOUNT_HOLDER_NAME_INPUT, data["account_holder_name"], clear_first=True)
        if data.get("account_number"):
            self.type_text(self.ACCOUNT_NUMBER_INPUT, data["account_number"], clear_first=True)

        # More dropdowns
        self._fill_dropdown_if_provided(self.BANK_PROOF_SELECT, data.get("bank_proof"))

        log.info("Bank Details filled")

    # ==============================================================
    #  Family Details Tab (Borrower Farmer only)
    # ==============================================================

    def fill_family_details(self, data):
        """Fill the Family Details tab (table row — uses same pattern as Address)."""
        log.info("Filling Family Details...")

        if data.get("member_name"):
            self.type_text(self.FAMILY_MEMBER_NAME_INPUT, data["member_name"], clear_first=True)
        if data.get("phone_number"):
            self.type_text(self.FAMILY_PHONE_INPUT, data["phone_number"], clear_first=True)
        if data.get("date_of_birth"):
            try:
                dob_input = self.find_visible_element(self.FAMILY_DOB_INPUT, timeout=3)
                if dob_input:
                    dob_input.clear()
                    dob_input.send_keys(data["date_of_birth"])
                    self.wait_seconds(0.5)
            except Exception:
                log.warning("Family DOB input not found, skipping")
        self._fill_dropdown_if_provided(self.FAMILY_GENDER_SELECT, data.get("gender"))
        self._fill_dropdown_if_provided(self.EDUCATION_OF_FARMER_FAMILY_SELECT, data.get("education_of_farmer_family"))
        self._fill_dropdown_if_provided(self.RELATIONSHIP_SELECT, data.get("relationship"))
        if data.get("pincode"):
            self.type_text(self.FAMILY_PINCODE_INPUT, data["pincode"], clear_first=True)
        if data.get("address"):
            self.type_text(self.FAMILY_ADDRESS_INPUT, data["address"], clear_first=True)
        self._fill_dropdown_if_provided(self.MARITAL_STATUS_SELECT, data.get("marital_status"))
        if data.get("no_of_childrens"):
            self.type_text(self.NO_OF_CHILDRENS_INPUT, data["no_of_childrens"], clear_first=True)
        self._fill_dropdown_if_provided(self.MEMBER_ANNUAL_INCOME_SELECT, data.get("member_annual_income"))
        if data.get("off_farm_income"):
            self.type_text(self.OFF_FARM_INCOME_INPUT, data["off_farm_income"], clear_first=True)

        log.info("Family Details filled")

    # ==============================================================
    #  Other Details Tab (Borrower Farmer only)
    # ==============================================================

    def fill_other_details(self, data):
        """Fill the Other Details tab."""
        log.info("Filling Other Details...")

        self._fill_dropdown_if_provided(self.EDUCATION_QUALIFICATION_SELECT, data.get("education_qualification"))
        self._fill_dropdown_if_provided(self.ELECTRICITY_AVAILABILITY_SELECT, data.get("electricity_availability"))

        log.info("Other Details filled")

    # ==============================================================
    #  Land Details Tab (Borrower Farmer + FPC Member)
    # ==============================================================

    def fill_land_details(self, data):
        """Fill the Land Details tab.

        FILL ORDER: upper text inputs first, then scroll-down fields.
        NOTE: No Of Owner is REQUIRED but has no asterisk (BUG-F01).
        """
        log.info("Filling Land Details...")

        # Upper visible text inputs
        if data.get("farm_name"):
            self.type_text(self.FARM_NAME_INPUT, data["farm_name"], clear_first=True)
        if data.get("no_of_owner"):
            self.type_text(self.NO_OF_OWNER_INPUT, data["no_of_owner"], clear_first=True)
        if data.get("total_land_on_document_hectare"):
            self.type_text(self.TOTAL_LAND_ON_DOCUMENT_INPUT, data["total_land_on_document_hectare"], clear_first=True)
        if data.get("individual_land_holding_hectare"):
            self.type_text(self.INDIVIDUAL_LAND_HOLDING_INPUT, data["individual_land_holding_hectare"], clear_first=True)

        # Middle text inputs
        if data.get("gat_number"):
            self.type_text(self.GAT_NUMBER_INPUT, data["gat_number"], clear_first=True)
        if data.get("land_coordinate"):
            self.type_text(self.LAND_COORDINATE_INPUT, data["land_coordinate"], clear_first=True)

        # Scroll-down text inputs
        if data.get("total_land_in_hectare"):
            self.type_text(self.TOTAL_LAND_IN_HECTARE_INPUT, data["total_land_in_hectare"], clear_first=True)
        if data.get("total_cultivation_land_in_hectare"):
            self.type_text(self.TOTAL_CULTIVATION_LAND_HECTARE_INPUT, data["total_cultivation_land_in_hectare"], clear_first=True)
        if data.get("total_cultivation_land_in_acreage"):
            self.type_text(self.TOTAL_CULTIVATION_LAND_ACREAGE_INPUT, data["total_cultivation_land_in_acreage"], clear_first=True)

        # Dropdowns
        self._fill_dropdown_if_provided(self.LAND_OWNERSHIP_SELECT, data.get("land_ownership"))

        # Bottom text inputs
        if data.get("latitude"):
            self.type_text(self.LATITUDE_INPUT, data["latitude"], clear_first=True)
        if data.get("longitude"):
            self.type_text(self.LONGITUDE_INPUT, data["longitude"], clear_first=True)

        log.info("Land Details filled")

    # ==============================================================
    #  Crop Details Tab (Borrower Farmer + FPC Member)
    # ==============================================================

    def fill_crop_details(self, data):
        """Fill the Crop Details tab."""
        log.info("Filling Crop Details...")

        if data.get("farm_name"):
            try:
                crop_farm_input = self.find_visible_element(self.CROP_FARM_NAME_INPUT, timeout=3)
                if crop_farm_input:
                    crop_farm_input.clear()
                    crop_farm_input.send_keys(data["farm_name"])
            except Exception:
                log.warning("Crop Farm Name input not found")
        self._fill_dropdown_if_provided(self.CROP_SELECT, data.get("crop"))
        self._fill_dropdown_if_provided(self.SEASON_SELECT, data.get("season"))
        if data.get("cultivation_land_in_hectare"):
            self.type_text(self.CULTIVATION_LAND_HECTARE_INPUT, data["cultivation_land_in_hectare"], clear_first=True)
        if data.get("expected_yield_projection"):
            self.type_text(self.EXPECTED_YIELD_INPUT, data["expected_yield_projection"], clear_first=True)
        if data.get("actual_produce"):
            self.type_text(self.ACTUAL_PRODUCE_INPUT, data["actual_produce"], clear_first=True)
        if data.get("cultivation_land_in_acreage"):
            self.type_text(self.CULTIVATION_LAND_ACREAGE_INPUT, data["cultivation_land_in_acreage"], clear_first=True)

        log.info("Crop Details filled")

    # ==============================================================
    #  KYC Details Tab (Borrower Farmer + FPC Member)
    # ==============================================================

    def fill_kyc_details(self, data):
        """Fill the KYC Details tab."""
        log.info("Filling KYC Details...")

        self._fill_dropdown_if_provided(self.KYC_DOCUMENT_SELECT, data.get("kyc_document"))
        if data.get("kyc_number"):
            self.type_text(self.KYC_NUMBER_INPUT, data["kyc_number"], clear_first=True)

        log.info("KYC Details filled")

    # ==============================================================
    #  Vehicle Details Tab (Borrower Farmer only)
    # ==============================================================

    def fill_vehicle_details(self, data):
        """Fill the Vehicle Details tab."""
        log.info("Filling Vehicle Details...")

        self._fill_dropdown_if_provided(self.VEHICLE_TYPE_SELECT, data.get("vehicle_type"))
        self._fill_dropdown_if_provided(self.VEHICLE_NAME_SELECT, data.get("vehicle_name"))

        log.info("Vehicle Details filled")

    # ==============================================================
    #  Income Details Tab (Borrower Farmer only)
    # ==============================================================

    def fill_income_details(self, data):
        """Fill the Income Details tab.
        NOTE: Exact Amount accepts 0 and . prefix (BUG-F06).
        """
        log.info("Filling Income Details...")

        self._fill_dropdown_if_provided(self.SOURCE_OF_INCOME_SELECT, data.get("source_of_income"))
        self._fill_dropdown_if_provided(self.INCOME_BRACKET_SELECT, data.get("income_bracket"))
        if data.get("exact_amount"):
            self.type_text(self.EXACT_AMOUNT_INPUT, data["exact_amount"], clear_first=True)

        log.info("Income Details filled")

    # ==============================================================
    #  Irrigation Details Tab (Borrower Farmer only)
    # ==============================================================

    def fill_irrigation_details(self, data):
        """Fill the Irrigation Details tab."""
        log.info("Filling Irrigation Details...")

        self._fill_dropdown_if_provided(self.SOURCE_OF_IRRIGATION_SELECT, data.get("source_of_irrigation"))
        self._fill_dropdown_if_provided(self.METHOD_OF_IRRIGATION_SELECT, data.get("method_of_irrigation"))

        log.info("Irrigation Details filled")

    # ==============================================================
    #  Award Details Tab (Borrower Farmer only)
    # ==============================================================

    def fill_award_details(self, data):
        """Fill the Award Details tab."""
        log.info("Filling Award Details...")

        if data.get("name"):
            self.type_text(self.AWARD_NAME_INPUT, data["name"], clear_first=True)
        if data.get("year"):
            self.type_text(self.AWARD_YEAR_INPUT, data["year"], clear_first=True)

        log.info("Award Details filled")

    # ==============================================================
    #  Loan Details Tab (Borrower Farmer only)
    # ==============================================================

    def fill_loan_details(self, data):
        """Fill the Loan Details tab.
        NOTE: Sanctioned Amount & Present Outstanding Amount accept 0/. prefix (BUG-F06).
        """
        log.info("Filling Loan Details...")

        if data.get("loan_name"):
            self.type_text(self.LOAN_NAME_INPUT, data["loan_name"], clear_first=True)
        self._fill_dropdown_if_provided(self.FACILITY_TYPE_SELECT, data.get("facility_type"))
        if data.get("purpose_of_loan"):
            self.type_text(self.PURPOSE_OF_LOAN_INPUT, data["purpose_of_loan"], clear_first=True)
        if data.get("availed_from"):
            self.type_text(self.AVAILED_FROM_INPUT, data["availed_from"], clear_first=True)
        if data.get("sanctioned_amount"):
            self.type_text(self.SANCTIONED_AMOUNT_INPUT, data["sanctioned_amount"], clear_first=True)
        if data.get("present_outstanding_amount"):
            self.type_text(self.PRESENT_OUTSTANDING_INPUT, data["present_outstanding_amount"], clear_first=True)

        log.info("Loan Details filled")

    # ==============================================================
    #  Navigate-to-tab helper (tab name -> step index)
    # ==============================================================

    def navigate_to_tab_by_name(self, target_tab_name):
        """Navigate to a specific stepper tab. Tries direct header click first,
        falls back to Next-button stepping with max-retry guard.
        Returns True if reached, False otherwise.
        """
        target_lower = target_tab_name.strip().lower()
        log.info(f"Navigating to tab: {target_tab_name}")

        # Strategy 1: Find the tab index and click the header directly
        tab_names = self.get_stepper_tab_names()
        for idx, name in enumerate(tab_names):
            if target_lower in name.strip().lower():
                current_idx = self.get_current_step_index()
                if current_idx == idx:
                    log.info(f"Already on tab: {target_tab_name}")
                    return True
                # Click the header directly — works even when Next is frozen (BUG-F02)
                if self.click_stepper_header(idx):
                    self.wait_seconds(1)
                    # Verify we landed on the right tab using get_active_tab_name()
                    active_name = self.get_active_tab_name()
                    if target_lower in active_name.lower():
                        log.info(f"Reached tab via header click: {target_tab_name}")
                        return True

        # Strategy 2: Step forward with Next button (max = number of tabs)
        max_steps = len(tab_names) if tab_names else 5
        for attempt in range(max_steps):
            active_name = self.get_active_tab_name()
            if target_lower in active_name.lower():
                log.info(f"Reached tab via Next stepping: {target_tab_name}")
                return True
            # If we've gone past the target, break
            tab_names = self.get_stepper_tab_names()
            found_target_idx = -1
            for idx, name in enumerate(tab_names):
                if target_lower in name.strip().lower():
                    found_target_idx = idx
                    break
            current_idx = self.get_current_step_index()
            if found_target_idx >= 0 and current_idx > found_target_idx:
                log.warning(f"Overshot tab: {target_tab_name} (at idx {current_idx}, target idx {found_target_idx})")
                break
            if not self.click_stepper_next():
                break
            self.wait_seconds(1)

        # Strategy 3: Final attempt — direct header click with retry
        tab_names = self.get_stepper_tab_names()
        for idx, name in enumerate(tab_names):
            if target_lower in name.strip().lower():
                self.click_stepper_header(idx)
                self.wait_seconds(1)
                active_name = self.get_active_tab_name()
                if target_lower in active_name.lower():
                    log.info(f"Reached tab via final header click: {target_tab_name}")
                    return True

        log.warning(f"Could not navigate to tab: {target_tab_name}")
        return False

    def fill_tab_by_name(self, tab_name, data):
        """Fill the currently active tab based on its name. Delegates to
        the appropriate fill method.
        """
        tab_lower = tab_name.strip().lower()

        if "current address" in tab_lower:
            self.fill_current_address(data)
        elif "permanent address" in tab_lower:
            self.fill_permanent_address(data)
        elif "family" in tab_lower:
            self.fill_family_details(data)
        elif "other" in tab_lower:
            self.fill_other_details(data)
        elif "land" in tab_lower:
            self.fill_land_details(data)
        elif "crop" in tab_lower:
            self.fill_crop_details(data)
        elif "kyc" in tab_lower:
            self.fill_kyc_details(data)
        elif "vehicle" in tab_lower:
            self.fill_vehicle_details(data)
        elif "income" in tab_lower:
            self.fill_income_details(data)
        elif "bank" in tab_lower:
            self.fill_bank_details(data)
        elif "irrigation" in tab_lower:
            self.fill_irrigation_details(data)
        elif "award" in tab_lower:
            self.fill_award_details(data)
        elif "loan" in tab_lower:
            self.fill_loan_details(data)
        else:
            log.warning(f"Unknown tab name: {tab_name} — skipping fill")

    # ==============================================================
    #  Submit / Cancel / Close
    # ==============================================================

    def submit(self):
        """Click Submit button (Create mode)."""
        log.info("Clicking Submit...")
        self._force_close_panels()
        try:
            btn = self.find_clickable_element(self.SUBMIT_BUTTON, timeout=5)
            if btn:
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});"
                    "arguments[0].click();", btn,
                )
                self.wait_seconds(1)
                return True
        except Exception:
            pass
        return False

    def click_update(self):
        """Click Update button (Edit mode)."""
        log.info("Clicking Update...")
        self._force_close_panels()
        try:
            btn = self.find_clickable_element(self.UPDATE_BUTTON, timeout=5)
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});"
                "arguments[0].click();", btn,
            )
            self.wait_seconds(1)
            return True
        except Exception:
            pass
        return False

    def cancel(self):
        """Click Cancel button."""
        try:
            btn = self.find_clickable_element(self.CANCEL_BUTTON, timeout=5)
            if btn:
                self.driver.execute_script("arguments[0].click();", btn)
                self.wait_seconds(1)
        except Exception:
            pass

    def close_popup(self):
        """Close form popup via Cancel or backdrop click."""
        try:
            self.cancel()
        except Exception:
            pass
        self.wait_seconds(0.5)

    def force_close_form_popup(self):
        """Force close any open popup via JS."""
        self.driver.execute_script("""
            document.querySelectorAll('mat-dialog-container').forEach(function(el) { el.remove(); });
            document.querySelectorAll('.cdk-overlay-backdrop').forEach(function(el) { el.remove(); });
            document.querySelectorAll('.cdk-overlay-pane').forEach(function(el) { el.remove(); });
        """)
        self.wait_seconds(0.5)

    # ==============================================================
    #  SweetAlert2 handling
    # ==============================================================

    def handle_success_alert(self, timeout=60):
        """Handle SweetAlert2 success alert. Returns alert title text."""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, ".swal2-container"))
            )
            self.wait_seconds(1)
            title = self.driver.find_element(By.CSS_SELECTOR, "#swal2-title").text.strip()
            self._swal2_confirm_click()
            self.wait_seconds(1)
            return title
        except TimeoutException:
            log.warning("No SweetAlert2 success alert found")
            return ""

    def handle_validation_warning(self, timeout=5):
        """Handle SweetAlert2 validation warning. Returns alert title text."""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, ".swal2-container"))
            )
            title = self.driver.find_element(By.CSS_SELECTOR, "#swal2-title").text.strip()
            self._swal2_confirm_click()
            self.wait_seconds(0.5)
            return title
        except TimeoutException:
            return ""

    def _swal2_confirm_click(self):
        """Click the confirm button on SweetAlert2 (3-tier strategy)."""
        for attempt in range(3):
            try:
                btn = self.driver.find_element(By.CSS_SELECTOR, ".swal2-confirm")
                if btn.is_displayed():
                    self.driver.execute_script("arguments[0].click();", btn)
                    self.wait_seconds(0.5)
                    return
            except Exception:
                pass
            self.wait_seconds(0.5)

    def is_validation_alert_present(self):
        """Check if a SweetAlert2 validation alert is showing."""
        try:
            container = self.driver.find_element(By.CSS_SELECTOR, ".swal2-container")
            return container.is_displayed()
        except Exception:
            return False

    # ==============================================================
    #  Validation errors
    # ==============================================================

    def get_mat_error_text(self):
        """Get all visible mat-error texts."""
        errors = []
        try:
            error_elements = self.driver.find_elements(By.CSS_SELECTOR, "mat-error, .mat-mdc-form-field-error")
            for el in error_elements:
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
    #  Table operations
    # ==============================================================

    def is_farmer_in_table(self, farmer_name):
        """Check if a farmer with the given name exists in the listing table."""
        try:
            cells = self.driver.find_elements(By.CSS_SELECTOR, "td.cdk-column-name")
            for cell in cells:
                try:
                    if farmer_name.lower() in cell.text.strip().lower():
                        return True
                except Exception:
                    continue
        except Exception:
            pass
        return False

    def click_edit_button(self, farmer_name):
        """Click Edit button for a specific farmer row."""
        xpath = f"//td[contains(text(),'{farmer_name}')]/ancestor::tr//td[contains(@class,'cdk-column-edit')]//button"
        try:
            btn = self.driver.find_element(By.XPATH, xpath)
            self.driver.execute_script("arguments[0].click();", btn)
            self.wait_seconds(2)
        except Exception:
            log.warning(f"Edit button not found for farmer: {farmer_name}")

    def click_view_button(self, farmer_name):
        """Click View button for a specific farmer row."""
        xpath = f"//td[contains(text(),'{farmer_name}')]/ancestor::tr//td[contains(@class,'cdk-column-view')]//button"
        try:
            btn = self.driver.find_element(By.XPATH, xpath)
            self.driver.execute_script("arguments[0].click();", btn)
            self.wait_seconds(2)
        except Exception:
            log.warning(f"View button not found for farmer: {farmer_name}")

    def search_item(self, search_text):
        """Search for a farmer using the search input."""
        log.info(f"Searching for: {search_text}")
        try:
            search_toggle = self.driver.find_elements(By.CSS_SELECTOR, "button.search-btn")
            if search_toggle:
                self.driver.execute_script("arguments[0].click();", search_toggle[0])
                self.wait_seconds(0.5)

            search_input = self.driver.find_element(By.CSS_SELECTOR, "input#erpSearchInput, input[placeholder='Search']")
            search_input.clear()
            search_input.send_keys(search_text)
            search_input.send_keys(Keys.ENTER)
            self.wait_seconds(2)
        except Exception as e:
            log.warning(f"Search failed: {e}")

    def clear_search(self):
        """Clear the search input."""
        try:
            search_input = self.driver.find_element(By.CSS_SELECTOR, "input#erpSearchInput, input[placeholder='Search']")
            search_input.clear()
            search_input.send_keys(Keys.ENTER)
            self.wait_seconds(2)
        except Exception:
            pass

    # ==============================================================
    #  Edit mode detection
    # ==============================================================

    def is_edit_mode(self):
        """Check if the form is in Edit mode (Update button present)."""
        try:
            btns = self.driver.find_elements(
                By.XPATH, "//div[contains(@class,'popup-footer')]//button[contains(.,'Update')]"
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
    #  End-to-End: Create Farmer
    #  FIX: Use navigate_to_tab_by_name() for explicit navigation instead
    #  of blind Next clicks. Track filled tabs to avoid re-filling.
    # ==============================================================

    def create_farmer(self, data):
        """Create a farmer with the given data. Returns result dict.

        Handles ALL 3 farmer categories by navigating through the stepper
        tabs using the ACTUAL active tab name (not index-based lookup).

        FIX: After filling Step 0 and clicking Next, the stepper may land
        on the WRONG tab (offset by 1). Instead of blindly clicking Next
        and hoping we land on the right tab, we now:
          1. Fill Step 0
          2. Click Next ONCE to advance from Farmer Details
          3. Read which tab we actually landed on
          4. Use navigate_to_tab_by_name() to go to the CORRECT tab
          5. Fill it, then move to next tab via navigate_to_tab_by_name()
          6. Track filled tabs to avoid re-filling

        STEPPER TAB LAYOUT BY CATEGORY:
          Walk-in Farmer:  Current Address, Permanent Address, Bank Details
          FPC Member:      Current Address, Permanent Address, Land Details,
                           Crop Details, KYC Details, Bank Details
          Borrower Farmer: Current Address, Permanent Address, Family Details,
                           Other Details, Land Details, Crop Details, KYC Details,
                           Vehicle Details, Income Details, Bank Details,
                           Irrigation Details, Award Details, Loan Details

        Data dict structure (keys are tab names):
            data["farmer_category"]        — "Borrower Farmer" | "FPC Member" | "Walk-in Farmer"
            data["current_address"]        — dict for Current Address tab
            data["permanent_address"]      — dict for Permanent Address tab
            data["bank_details"]           — dict for Bank Details tab
            data["family_details"]         — dict for Family Details tab (Borrower only)
            data["other_details"]          — dict for Other Details tab (Borrower only)
            data["land_details"]           — dict for Land Details tab (Borrower/FPC)
            data["crop_details"]           — dict for Crop Details tab (Borrower/FPC)
            data["kyc_details"]            — dict for KYC Details tab (Borrower/FPC)
            data["vehicle_details"]        — dict for Vehicle Details tab (Borrower only)
            data["income_details"]         — dict for Income Details tab (Borrower only)
            data["irrigation_details"]     — dict for Irrigation Details tab (Borrower only)
            data["award_details"]          — dict for Award Details tab (Borrower only)
            data["loan_details"]           — dict for Loan Details tab (Borrower only)
        """
        log.info("Creating farmer...")
        self.open_add_form()
        self.wait_seconds(1)

        # Fill Step 0 (universal fields — upper first, then scroll-down)
        self.fill_step0(data)

        # Get visible tab names after category selection
        tab_names = self.get_stepper_tab_names()
        log.info(f"Stepper tabs visible: {tab_names}")

        # Tab-name to data-key mapping
        TAB_DATA_MAP = {
            "Current Address": "current_address",
            "Permanent Address": "permanent_address",
            "Family Details": "family_details",
            "Other Details": "other_details",
            "Land Details": "land_details",
            "Crop Details": "crop_details",
            "KYC Details": "kyc_details",
            "Vehicle Details": "vehicle_details",
            "Income Details": "income_details",
            "Bank Details": "bank_details",
            "Irrigation Details": "irrigation_details",
            "Award Details": "award_details",
            "Loan Details": "loan_details",
        }

        # FIX: Track filled tabs to avoid re-filling
        filled_tabs = set()

        # FIX: Click Next ONCE to advance from Farmer Details step.
        # After this, we navigate explicitly by tab name instead of
        # blindly clicking Next and hoping we land on the right tab.
        self.click_stepper_next()
        self.wait_seconds(1.5)

        # Build the ordered list of tabs that need filling
        # (skip empty tab names like Farmer Details header)
        fillable_tabs = []
        for tab_name in tab_names:
            if not tab_name.strip():
                continue
            tab_lower = tab_name.strip().lower()
            # Find matching data key
            data_key = None
            for ui_name, key in TAB_DATA_MAP.items():
                if ui_name.lower() in tab_lower:
                    data_key = key
                    break
            if data_key:
                fillable_tabs.append((tab_name, data_key))

        log.info(f"Fillable tabs: {[(t, k) for t, k in fillable_tabs]}")

        # FIX: Navigate to each tab EXPLICITLY by name, then fill it.
        # This avoids the off-by-one bug where clicking Next may land
        # on the wrong tab after the stepper re-indexes.
        for tab_name, data_key in fillable_tabs:
            tab_lower = tab_name.strip().lower()

            # Skip if already filled
            if tab_lower in filled_tabs:
                log.info(f"Tab already filled, skipping: {tab_name}")
                continue

            # Navigate explicitly to the correct tab
            if not self.navigate_to_tab_by_name(tab_name):
                log.warning(f"Could not navigate to tab: {tab_name} — skipping")
                continue

            # Verify we're on the right tab
            actual_tab = self.get_active_tab_name()
            log.info(f"Current tab: {actual_tab} (target: {tab_name})")

            # Use the ACTUAL tab name for filling — it may differ from expected
            fill_tab_name = actual_tab if actual_tab else tab_name

            # Fill the tab if data is provided
            if data.get(data_key):
                self.fill_tab_by_name(fill_tab_name, data[data_key])
                log.info(f"Filled tab: {fill_tab_name}")
            else:
                log.info(f"Skipping tab (no data provided): {fill_tab_name}")

            # Mark this tab as filled
            filled_tabs.add(tab_lower)

        # Submit
        self._force_close_panels()
        self.submit()
        self.wait_seconds(2)

        # Handle success alert
        alert_title = self.handle_success_alert(timeout=30)

        result = {
            "status": "PASSED" if "successfully" in alert_title.lower() else "FAILED",
            "alert_title": alert_title,
            "farmer_name": data.get("farmer_name", ""),
            "error": "" if "successfully" in alert_title.lower() else alert_title,
        }

        FARMER_SUBMISSIONS.append(result)
        return result

    # ==============================================================
    #  Get form field values (for verification)
    # ==============================================================

    def get_form_field_values_step0(self):
        """Read current values of Step 0 form fields."""
        values = {}
        try:
            name_input = self.driver.find_element(By.CSS_SELECTOR, "input[name='Farmer Name']")
            values["farmer_name"] = name_input.get_attribute("value") or ""
        except Exception:
            values["farmer_name"] = ""

        try:
            email_input = self.driver.find_element(By.CSS_SELECTOR, "input[name='Email']")
            values["email"] = email_input.get_attribute("value") or ""
        except Exception:
            values["email"] = ""

        try:
            phone_input = self.driver.find_element(By.CSS_SELECTOR, "input[name='Phone Number']")
            values["phone_number"] = phone_input.get_attribute("value") or ""
        except Exception:
            values["phone_number"] = ""

        try:
            password_input = self.driver.find_element(By.CSS_SELECTOR, "input[name='Password']")
            values["password"] = password_input.get_attribute("value") or ""
        except Exception:
            values["password"] = ""

        return values
