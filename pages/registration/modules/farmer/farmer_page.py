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
        """Click on a stepper tab header by index.

        Works even when Next button is frozen (BUG-F02).
        FIX: Added force-click that removes aria-disabled attribute
        before clicking, bypassing Angular Material's linear mode
        restriction that prevents navigating to incomplete steps.
        """
        try:
            # Force-click: remove aria-disabled and click via JS
            result = self.driver.execute_script("""
                var idx = arguments[0];
                var headers = document.querySelectorAll('mat-step-header');
                if (idx >= 0 && idx < headers.length) {
                    var header = headers[idx];
                    // Remove Angular Material's disabled state
                    header.removeAttribute('aria-disabled');
                    header.classList.remove('mat-step-header-optional');
                    // Click the header
                    header.click();
                    return true;
                }
                return false;
            """, index)
            self.wait_seconds(1)
            return bool(result)
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

        FIX: Upgraded to use _fill_input_by_name_js() for Angular-compatible
        text input filling and _fill_dropdown_if_provided() with label_text
        for more robust dropdown selection. Uses _set_toggle_if_provided()
        for data-key-driven toggle handling.
        """
        log.info("Filling Step 0: Farmer Details...")

        # === 1. UPPER VISIBLE TEXT INPUTS (no scroll needed) ===
        # FIX: Use _fill_input_by_name_js() for Angular form model sync
        if data.get("farmer_name"):
            self._fill_input_by_name_js("Farmer Name", data["farmer_name"])
        if data.get("email"):
            self._fill_input_by_name_js("Email", data["email"])
        if data.get("phone_number"):
            self._fill_input_by_name_js("Phone Number", data["phone_number"])
        if data.get("password"):
            self._fill_input_by_name_js("Password", data["password"])
        if data.get("date_of_birth"):
            self.type_text(self.DATE_OF_BIRTH_INPUT, data["date_of_birth"], clear_first=True)
            self.wait_seconds(0.5)

        # === 2. SCROLL-DOWN DROPDOWNS (may need scrolling into view) ===
        # FIX: Pass label_text for label-based selection fallback
        self._fill_dropdown_if_provided(self.GENDER_SELECT, data.get("gender"), label_text="Gender")
        self._fill_dropdown_if_provided(self.CATEGORY_SELECT, data.get("category"), label_text="Category")
        self._fill_dropdown_if_provided(self.RELIGION_SELECT, data.get("religion"), label_text="Religion")
        self._fill_dropdown_if_provided(self.LAND_CLASSIFICATION_SELECT, data.get("land_classification"), label_text="Land Classification")

        # === 3. FARMER CATEGORY LAST — it triggers stepper tab creation ===
        if data.get("farmer_category"):
            self._select_farmer_category(data["farmer_category"])

        # Toggle switch (bottom of form)
        # FIX: Use data-key-driven toggle helper
        self._set_toggle_if_provided(data, "is_member_of_fpc", self.IS_MEMBER_TOGGLE, "Is Member of FPC")

        log.info("Step 0 filled successfully")

    def _fill_dropdown_if_provided(self, locator, value, label_text=None, exclude=None):
        """Fill a mat-select dropdown if a value is provided.

        FIX: Extended to support data-key-driven pattern with optional
        label-based selection. When label_text is provided, uses
        _select_mat_option_by_label() for more robust element finding.

        If value is None, pick a random valid option (non-placeholder).
        If value is empty string, skip.
        If value is a string, select that specific option.

        Args:
            locator: Locator tuple for the mat-select element.
            value: Value from data dict (None=random, ''=skip, str=specific).
            label_text: Optional mat-label text for label-based selection.
            exclude: Optional list of option texts to exclude from random.
        """
        if value is None:
            # Pick a random non-placeholder option
            self._select_random_from_dropdown(locator, exclude=exclude)
        elif value == "":
            return  # Skip empty strings
        else:
            if label_text:
                # Use label-based selection (more robust)
                self._select_mat_option_by_label(label_text, value)
            else:
                self._select_mat_option(locator, value)

    def _select_mat_option(self, dropdown_locator, option_text):
        """Select a specific option in a mat-select dropdown using JS click.

        FIX (BUG-001 WORKAROUND): After clicking an option, re-find the
        mat-select trigger element and fire
        `dispatchEvent(new Event('change', {bubbles: true}))` to force
        Angular's reactive form model to register the selection. Without
        this, Angular may not detect the JS-clicked option and show
        silent validation errors on Submit.
        """
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
                        # BUG-001 WORKAROUND: Force Angular reactive form update
                        self._dispatch_change_event(dropdown_locator)
                        self._close_select_panel()
                        log.info(f"Selected option '{option_text}' (with BUG-001 workaround)")
                        return
                except Exception:
                    continue

            # Fallback: close panel if option not found
            self._close_select_panel()
            log.warning(f"Option '{option_text}' not found in dropdown")
        except Exception as e:
            log.warning(f"Dropdown selection failed: {e}")
            self._close_select_panel()

    def _dispatch_change_event(self, dropdown_locator):
        """BUG-001 WORKAROUND: Re-find the mat-select trigger and fire a
        `change` event with `bubbles: true` so Angular's reactive form
        model picks up the JS-clicked selection.

        This is the same pattern used in customer_page.py and agent_page.py.
        Without it, Angular may not register the selection, causing
        silent validation failures on Submit even though the dropdown
        appears visually selected.
        """
        try:
            # Re-find the dropdown element (may have gone stale)
            trigger = self.find_clickable_element(dropdown_locator, timeout=3)
            if trigger:
                self.driver.execute_script("""
                    var el = arguments[0];
                    // Find the mat-select trigger inside the form field
                    var trigger = el.tagName === 'MAT-SELECT' ? el : el.querySelector('mat-select');
                    if (trigger) {
                        trigger.dispatchEvent(new Event('change', {bubbles: true}));
                    }
                    // Also dispatch on the value accessor
                    el.dispatchEvent(new Event('change', {bubbles: true}));
                """, trigger)
        except Exception as e:
            log.debug(f"BUG-001 dispatchEvent failed (non-critical): {e}")

    def _select_random_from_dropdown(self, dropdown_locator, exclude=None):
        """Select a random valid non-placeholder option from a dropdown.

        FIX: Changed from picking the first option to random.choice() for
        better test coverage. Added `exclude` parameter to skip specific
        options (e.g., duplicates like BUG-F07 Dairy). Added comprehensive
        placeholder filtering and BUG-001 dispatchEvent workaround.

        Args:
            dropdown_locator: Locator tuple for the mat-select element.
            exclude: Optional list of option texts to skip (e.g., ['Dairy']).
        """
        import random as _random
        if exclude is None:
            exclude = []

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
                    # Filter out placeholders, empty options, "No results found", and excluded items
                    if not text:
                        continue
                    if text.startswith("Select ") or text.startswith("Choose "):
                        continue
                    if text.lower() in ("no results found", "no data found"):
                        continue
                    if text in exclude:
                        continue
                    if opt.is_displayed():
                        valid_options.append((opt, text))
                except Exception:
                    continue

            if valid_options:
                chosen_opt, chosen_text = _random.choice(valid_options)
                self.driver.execute_script("arguments[0].click();", chosen_opt)
                self.wait_seconds(0.5)
                # BUG-001 WORKAROUND: Force Angular reactive form update
                self._dispatch_change_event(dropdown_locator)
                log.info(f"Random dropdown option selected: '{chosen_text}'")
            else:
                log.warning("No valid options found in dropdown for random selection")

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

    def _is_toggle_on(self, toggle_element):
        """Multi-strategy check if a toggle switch is currently ON.

        FIX: Upgraded from single-strategy (checkbox.is_selected) to
        multi-strategy detection matching the customer_page.py pattern.
        Angular Material toggle switches may use different internal
        representations depending on the component library version.

        Strategies (in order):
          1. Inner checkbox input — is_selected()
          2. CSS class 'active' on the switch wrapper
          3. CSS class 'checked' or 'mat-checked' on the slide-toggle
          4. aria-checked='true' attribute
          5. Slider position class (e.g., 'mat-slide-toggle-checked')
        """
        try:
            # Strategy 1: Inner checkbox
            try:
                checkbox = toggle_element.find_element(By.CSS_SELECTOR, "input[type='checkbox']")
                if checkbox.is_selected():
                    return True
            except Exception:
                pass

            # Strategy 2: 'active' class on switch wrapper
            classes = toggle_element.get_attribute("class") or ""
            if "active" in classes.split():
                return True

            # Strategy 3: 'checked' / 'mat-checked' on slide-toggle
            try:
                slide_toggle = toggle_element.find_element(
                    By.CSS_SELECTOR, "mat-slide-toggle, .mat-slide-toggle"
                )
                slide_classes = slide_toggle.get_attribute("class") or ""
                if "mat-checked" in slide_classes or "mat-slide-toggle-checked" in slide_classes:
                    return True
            except Exception:
                pass

            # Strategy 4: aria-checked
            try:
                aria = toggle_element.get_attribute("aria-checked")
                if aria == "true":
                    return True
            except Exception:
                pass

            # Strategy 5: Check parent element for checked class
            try:
                parent = toggle_element.find_element(By.XPATH, "..")
                parent_classes = parent.get_attribute("class") or ""
                if "checked" in parent_classes.split():
                    return True
            except Exception:
                pass

        except Exception:
            pass
        return False

    def _set_toggle_to(self, toggle_locator, desired_state):
        """Set a toggle switch to the desired state (True=ON, False=OFF).

        FIX: Now uses multi-strategy _is_toggle_on() for reliable state
        detection instead of only checkbox.is_selected(). This handles
        Angular Material toggle variants that may not have a visible
        checkbox input.
        """
        try:
            toggle = self.find_visible_element(toggle_locator, timeout=5)
            current_state = self._is_toggle_on(toggle)

            if current_state != desired_state:
                self.driver.execute_script("arguments[0].click();", toggle)
                self.wait_seconds(0.5)
                # Verify the toggle changed
                new_state = self._is_toggle_on(toggle)
                if new_state != desired_state:
                    # Retry with JS direct click on the switch element
                    try:
                        switch = toggle.find_element(By.CSS_SELECTOR, ".switch, .slide-toggle, .mat-slide-toggle-bar")
                        self.driver.execute_script("arguments[0].click();", switch)
                        self.wait_seconds(0.3)
                    except Exception:
                        pass
                log.info(f"Toggle set to {'ON' if desired_state else 'OFF'}")
        except Exception as e:
            log.warning(f"Toggle switch failed: {e}")

    def _set_toggle_if_provided(self, data, key, toggle_locator, label_name="Toggle"):
        """Data-key-driven toggle helper — only sets if key exists in data dict.

        FIX: New method following customer_page.py pattern. Uses
        _is_toggle_on() for reliable state detection.

        Args:
            data: Data dict containing the toggle key.
            key: Key name in data dict (e.g., 'is_member_of_fpc').
            toggle_locator: Locator tuple for the toggle element.
            label_name: Human-readable name for logging.
        """
        if key not in data:
            return  # Key not provided — skip
        desired_state = data[key]
        try:
            self._set_toggle_to(toggle_locator, desired_state)
            log.info(f"{label_name} set to {'ON' if desired_state else 'OFF'}")
        except Exception as e:
            log.warning(f"{label_name} toggle failed: {e}")

    # ==============================================================
    #  Label-Based Dropdown Selection
    #  FIX: New method following customer_page.py pattern — finds dropdown
    #  by mat-label text instead of relying on hardcoded XPath locators.
    # ==============================================================

    def _select_mat_option_by_label(self, label_text, option_text, scope="popup"):
        """Select a mat-select dropdown option by its mat-label text.

        FIX: New method following customer_page.py pattern. Finds the
        dropdown by searching for a mat-label containing `label_text`,
        then clicks the associated mat-select and selects `option_text`.

        This is more robust than hardcoded XPath locators because:
        - It works even when Angular reorders DOM elements
        - It scopes to the active panel when scope='panel'
        - It applies BUG-001 dispatchEvent workaround

        Args:
            label_text: Text to search for in mat-label (e.g., 'Gender').
            option_text: Option text to select (e.g., 'Male').
            scope: 'popup' = search whole popup, 'panel' = active panel only.
        """
        log.info(f"Label-based select: label='{label_text}', option='{option_text}'")
        try:
            # Step 1: Find the mat-select by label text
            select_el = self.driver.execute_script("""
                var labelText = arguments[0];
                var scopeMode = arguments[1];
                var popup = document.querySelector('.big-model, mat-dialog-container');
                if (!popup) return null;

                var searchRoot = popup;
                if (scopeMode === 'panel') {
                    var activeContent = popup.querySelector(
                        'div.mat-horizontal-stepper-content-current'
                    );
                    if (!activeContent) {
                        var allPanels = popup.querySelectorAll(
                            'div[role="tabpanel"].mat-horizontal-stepper-content'
                        );
                        for (var p = 0; p < allPanels.length; p++) {
                            if (!allPanels[p].hasAttribute('inert')) {
                                activeContent = allPanels[p];
                                break;
                            }
                        }
                    }
                    if (activeContent) searchRoot = activeContent;
                }

                var labels = searchRoot.querySelectorAll('mat-label');
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
            """, label_text, scope)

            if not select_el:
                log.warning(f"Label-based dropdown not found: '{label_text}'")
                return

            # Step 2: Click to open
            self.driver.execute_script("""
                arguments[0].scrollIntoView({block:'center'});
                arguments[0].click();
            """, select_el)
            self.wait_seconds(0.8)

            # Step 3: Find and click the option
            options = self.driver.find_elements(By.CSS_SELECTOR, "div[role='listbox'] mat-option")
            for opt in options:
                try:
                    if opt.text.strip() == option_text and opt.is_displayed():
                        self.driver.execute_script("arguments[0].click();", opt)
                        self.wait_seconds(0.5)
                        # BUG-001 WORKAROUND
                        self.driver.execute_script("""
                            arguments[0].dispatchEvent(new Event('change', {bubbles: true}));
                        """, select_el)
                        self._close_select_panel()
                        log.info(f"Label-based select succeeded: '{label_text}' -> '{option_text}'")
                        return
                except Exception:
                    continue

            self._close_select_panel()
            log.warning(f"Option '{option_text}' not found for label '{label_text}'")
        except Exception as e:
            log.warning(f"Label-based dropdown selection failed: {e}")
            self._close_select_panel()

    def _fill_input_by_name_js(self, field_name, value, scope="popup"):
        """Fill a text input using JS nativeInputValueSetter + dispatchEvent.

        FIX: New method following agent_page.py pattern. Uses
        `Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set`
        to set the value, then fires `input` and `change` events with
        `bubbles: true` so Angular's reactive form model detects the change.

        This is more reliable than `send_keys()` for Angular Material forms
        because it bypasses the browser's input event buffering and directly
        notifies Angular's change detection.

        Args:
            field_name: HTML name attribute of the input (e.g., 'Farmer Name').
            value: Value to set.
            scope: 'popup' = search whole popup, 'panel' = active panel only.
        """
        if not value:
            return
        log.info(f"JS fill input: name='{field_name}', value='{str(value)[:50]}...'")
        try:
            result = self.driver.execute_script("""
                var fieldName = arguments[0];
                var val = arguments[1];
                var scopeMode = arguments[2];
                var popup = document.querySelector('.big-model, mat-dialog-container');
                if (!popup) return false;

                var searchRoot = popup;
                if (scopeMode === 'panel') {
                    var activeContent = popup.querySelector(
                        'div.mat-horizontal-stepper-content-current'
                    );
                    if (!activeContent) {
                        var allPanels = popup.querySelectorAll(
                            'div[role="tabpanel"].mat-horizontal-stepper-content'
                        );
                        for (var p = 0; p < allPanels.length; p++) {
                            if (!allPanels[p].hasAttribute('inert')) {
                                activeContent = allPanels[p];
                                break;
                            }
                        }
                    }
                    if (activeContent) searchRoot = activeContent;
                }

                // Try exact name match first, then contains (for TAB char fields)
                var inputs = searchRoot.querySelectorAll('input[name="' + fieldName + '"]');
                if (inputs.length === 0) {
                    // Fallback: search by contains (handles trailing TAB chars)
                    var allInputs = searchRoot.querySelectorAll('input[name]');
                    for (var i = 0; i < allInputs.length; i++) {
                        var name = allInputs[i].getAttribute('name') || '';
                        if (name.indexOf(fieldName) === 0 && allInputs[i].offsetParent !== null) {
                            inputs = [allInputs[i]];
                            break;
                        }
                    }
                }

                if (inputs.length === 0) return false;

                // Find the visible input (not in inert panel)
                var targetInput = null;
                for (var j = 0; j < inputs.length; j++) {
                    if (inputs[j].offsetParent !== null) {
                        targetInput = inputs[j];
                        break;
                    }
                }
                if (!targetInput && inputs.length > 0) {
                    targetInput = inputs[0];
                }
                if (!targetInput) return false;

                // Use nativeInputValueSetter for Angular compatibility
                var nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                    window.HTMLInputElement.prototype, 'value'
                ).set;
                nativeInputValueSetter.call(targetInput, val);
                targetInput.dispatchEvent(new Event('input', {bubbles: true}));
                targetInput.dispatchEvent(new Event('change', {bubbles: true}));

                return true;
            """, field_name, str(value), scope)

            if result:
                log.info(f"JS fill succeeded: '{field_name}'")
            else:
                log.warning(f"JS fill failed: input '{field_name}' not found")
        except Exception as e:
            log.warning(f"JS fill input failed: {e}")

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

    def _debug_dump_active_panel_inputs(self, target_field_name=""):
        """Dump input elements in the active stepper panel for debugging.

        Called when _fill_address_text_input fails to help diagnose
        why the input wasn't found or the value didn't stick.
        """
        try:
            result = self.driver.execute_script("""
                var targetField = arguments[0] || '';
                var output = [];
                var popup = document.querySelector('.big-model, mat-dialog-container');
                if (!popup) return 'No popup found';

                // Find active panel
                var activeContent = popup.querySelector(
                    'div.mat-horizontal-stepper-content-current'
                );
                if (!activeContent) {
                    var allPanels = popup.querySelectorAll(
                        'div[role="tabpanel"].mat-horizontal-stepper-content'
                    );
                    for (var p = 0; p < allPanels.length; p++) {
                        if (!allPanels[p].hasAttribute('inert')) {
                            activeContent = allPanels[p];
                            break;
                        }
                    }
                }
                if (!activeContent) return 'No active panel found';

                output.push('Active panel class: ' + activeContent.className.substring(0, 100));
                output.push('Active panel inert: ' + activeContent.hasAttribute('inert'));

                // List all inputs in the active panel
                var inputs = activeContent.querySelectorAll('input[name]');
                output.push('Inputs in active panel: ' + inputs.length);
                for (var i = 0; i < inputs.length; i++) {
                    var name = inputs[i].getAttribute('name');
                    var val = inputs[i].value;
                    var visible = inputs[i].offsetParent !== null;
                    var isTarget = (name === targetField || name === targetField + '\\t');
                    output.push(
                        '  [' + i + '] name="' + name + '" value="' + val.substring(0, 30) +
                        '" visible=' + visible + (isTarget ? ' <-- TARGET' : '')
                    );
                }

                // Also check ALL panels for the target field
                if (targetField) {
                    var allPanels = popup.querySelectorAll(
                        'div[role="tabpanel"].mat-horizontal-stepper-content'
                    );
                    output.push('\\nAll panels with "' + targetField + '" input:');
                    for (var p = 0; p < allPanels.length; p++) {
                        var input = allPanels[p].querySelector(
                            'input[name="' + targetField + '"], input[name="' + targetField + '\\t"]'
                        );
                        if (input) {
                            output.push(
                                '  panel[' + p + '] has it: inert=' +
                                allPanels[p].hasAttribute('inert') +
                                ' class=' + allPanels[p].className.includes('current') +
                                ' input.value="' + input.value.substring(0, 30) + '"'
                            );
                        }
                    }
                }

                return output.join('\\n');
            """, target_field_name)
            log.info(f"ACTIVE PANEL INPUT DUMP:\n{result}")
        except Exception as e:
            log.warning(f"Active panel input dump failed: {e}")

    def _fill_address_row(self, data, is_permanent=False):
        """Fill an address table row with cascading dropdowns.

        FILL ORDER (business rule):
          1. Upper visible dropdowns: Country -> State -> District
          2. Scroll-down dropdowns: Taluka -> Village
          3. Scroll-down text inputs: Pin Code -> Address -> Address2

        Country is ALWAYS forced to 'India' since other countries
        lack cascading data.

        FIX: Added Angular stability wait after Country selection.
        After selecting Country, Angular fetches State data via HTTP.
        We must wait for Angular's change detection to complete and
        the State dropdown to be fully populated before proceeding.
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

        # CRITICAL: Wait for Angular to fetch states after Country selection.
        # Angular makes an async HTTP call after Country changes. The State
        # dropdown component is destroyed and recreated with new options.
        # We must wait for this process to complete before interacting
        # with State, otherwise the dropdown won't have options yet.
        log.info(f"Waiting for Angular to stabilize after Country selection...")
        self._wait_for_angular_stable(timeout=8)
        self.wait_seconds(1)

        # State — depends on Country (pick first valid if data is None)
                # FIX: Permanent address data uses "perm_" prefixed keys
        state_val = data.get("perm_state") if is_permanent else None
        if not state_val:
            state_val = data.get("state")
        self._fill_cascading_dropdown("State", state_val)

        self._wait_for_angular_stable(timeout=5)
        self.wait_seconds(0.5)

        district_val = data.get("perm_district") if is_permanent else None
        if not district_val:
            district_val = data.get("district")
        self._fill_cascading_dropdown("District", district_val)

        self._wait_for_angular_stable(timeout=5)
        self.wait_seconds(0.5)

        taluka_val = data.get("perm_taluka") if is_permanent else None
        if not taluka_val:
            taluka_val = data.get("taluka")
        self._fill_cascading_dropdown("Taluka", taluka_val)

        self._wait_for_angular_stable(timeout=5)
        self.wait_seconds(0.5)

        village_val = data.get("perm_village") if is_permanent else None
        if not village_val:
            village_val = data.get("village")
        self._fill_cascading_dropdown("Village", village_val)

        # === 3. SCROLL-DOWN TEXT INPUTS ===
        # FIX: Use JS-scoped element finding instead of global CSS selectors.
        # After force-navigate, the Permanent Address panel is active but
        # global CSS selectors like input[name='Pin Code'] may find the
        # element in the inert Current Address panel (which isn't visible),
        # causing TimeoutException. Scoping to the active panel ensures we
        # find the correct input regardless of navigation state.

        # CRITICAL: Force-close any leftover mat-select overlay panels before
        # typing text inputs. After cascading dropdown selection, the mat-select
        # overlay panel may still be open (or fading out), which intercepts
        # clicks and blocks text input focus. This is the #1 cause of
        # Permanent Address Pin Code / Address not being filled.
        self._force_close_panels()
        self.wait_seconds(0.5)

        # Scroll popup to bottom to make text inputs visible
        self._scroll_popup_to_bottom()
        self.wait_seconds(0.3)

                # FIX: Permanent address data uses "perm_" prefixed keys.
        # When is_permanent=True, check perm_ keys first, then fall back
        # to unprefixed keys for backward compatibility.
        pin_code_val = data.get("perm_pin_code") if is_permanent else data.get("pin_code")
        if not pin_code_val:
            pin_code_val = data.get("pin_code")
        if pin_code_val:
            self._fill_address_text_input("Pin Code", pin_code_val)

        address_val = data.get("perm_address") if is_permanent else data.get("address")
        if not address_val:
            address_val = data.get("address")
        if address_val:
            self._fill_address_text_input("Address", address_val)

        address2_val = data.get("perm_address2") if is_permanent else data.get("address2")
        if not address2_val:
            address2_val = data.get("address2")
        if address2_val:
            self._fill_address_text_input("Address2", address2_val)

        log.info(f"{addr_type} Address filled")

    def _fill_address_text_input(self, field_name, value):
        """Fill a text input in the ACTIVE address panel using JavaScript.

        FIX: After force-navigate, global CSS selectors like
        input[name='Pin Code'] may find the element in the inert
        Current Address panel instead of the active Permanent Address
        panel. This method scopes the search to the active panel only,
        just like _js_open_cascading_dropdown() does for dropdowns.

        Uses the native input value setter (same as base_page.js_type_text)
        to properly trigger Angular's reactive form change detection.

        V2 FIX: Added value VERIFICATION after setting. In some cases,
        the native setter succeeds but Angular's change detection resets
        the value (especially after force-navigate when Angular's form
        state is out of sync with the DOM). This method now:
          1. Sets the value via native setter
          2. Reads it back to verify it stuck
          3. If not, tries focus+click+type simulation
          4. Logs diagnostics if all approaches fail

        Args:
            field_name: The input's name attribute (e.g. "Pin Code", "Address")
            value: The text to type into the input
        """
        if not value:
            return

        # Close any leftover overlay panels that might block input focus
        self._force_close_panels()
        self.wait_seconds(0.3)

        max_retries = 3
        for attempt in range(max_retries):
            # --- Strategy A: Native setter (fast, works for most cases) ---
            try:
                result = self.driver.execute_script("""
                    var fieldName = arguments[0];
                    var textValue = arguments[1];

                    // 1. Find the popup container
                    var popup = document.querySelector('.big-model, mat-dialog-container');
                    if (!popup) return {success: false, error: 'No popup found'};

                    // 2. Find the ACTIVE stepper panel
                    var activeContent = popup.querySelector(
                        'div.mat-horizontal-stepper-content-current'
                    );
                    if (!activeContent) {
                        var allPanels = popup.querySelectorAll(
                            'div[role="tabpanel"].mat-horizontal-stepper-content'
                        );
                        for (var p = 0; p < allPanels.length; p++) {
                            if (!allPanels[p].hasAttribute('inert')) {
                                activeContent = allPanels[p];
                                break;
                            }
                        }
                    }
                    if (!activeContent) return {success: false, error: 'No active panel'};

                    // 3. Find the input by name attribute within the active panel
                    var input = activeContent.querySelector('input[name="' + fieldName + '"]');
                    if (!input) return {success: false, error: 'Input not found: ' + fieldName};

                    // 4. Scroll into view and focus
                    input.scrollIntoView({block: 'center'});
                    input.focus();

                    // 5. Clear and set value using Angular-compatible native setter
                    var nativeSet = Object.getOwnPropertyDescriptor(
                        window.HTMLInputElement.prototype, 'value'
                    ).set;

                    // Clear first
                    nativeSet.call(input, '');
                    input.dispatchEvent(new Event('input', {bubbles: true}));
                    input.dispatchEvent(new Event('change', {bubbles: true}));

                    // Set new value
                    nativeSet.call(input, textValue);
                    input.dispatchEvent(new Event('input', {bubbles: true}));
                    input.dispatchEvent(new Event('change', {bubbles: true}));
                    input.dispatchEvent(new Event('blur', {bubbles: true}));

                    // 6. VERIFY: Read back the value to confirm it stuck
                    var actualValue = input.value;
                    return {
                        success: actualValue === textValue,
                        value: actualValue,
                        expected: textValue,
                        verified: actualValue === textValue
                    };
                """, field_name, value)

                if result and result.get('success'):
                    log.info(f"Address '{field_name}' typed: {value}")
                    return
                elif result and not result.get('verified'):
                    # Value was set but didn't stick — Angular may have reset it
                    log.warning(
                        f"Address '{field_name}' value verification FAILED: "
                        f"expected='{result.get('expected')}', "
                        f"actual='{result.get('value')}' "
                        f"(attempt {attempt + 1}/{max_retries})"
                    )
                else:
                    error = result.get('error', 'Unknown') if result else 'JS returned null'
                    log.warning(
                        f"Address text input '{field_name}' failed: {error}, "
                        f"retry {attempt + 1}/{max_retries}"
                    )
            except Exception as e:
                log.warning(
                    f"Address text input '{field_name}' exception: {e}, "
                    f"retry {attempt + 1}/{max_retries}"
                )

            self.wait_seconds(1)

            # --- Strategy B: Focus + click + character-by-character simulation ---
            # If native setter doesn't stick, try Selenium send_keys on the
            # JS-found element. This triggers Angular's full event pipeline.
            if attempt == max_retries - 1:
                try:
                    log.info(f"Trying send_keys strategy for '{field_name}'...")
                    element = self.driver.execute_script("""
                        var fieldName = arguments[0];
                        var popup = document.querySelector('.big-model, mat-dialog-container');
                        if (!popup) return null;
                        var activeContent = popup.querySelector(
                            'div.mat-horizontal-stepper-content-current'
                        );
                        if (!activeContent) {
                            var allPanels = popup.querySelectorAll(
                                'div[role="tabpanel"].mat-horizontal-stepper-content'
                            );
                            for (var p = 0; p < allPanels.length; p++) {
                                if (!allPanels[p].hasAttribute('inert')) {
                                    activeContent = allPanels[p];
                                    break;
                                }
                            }
                        }
                        if (!activeContent) return null;
                        var input = activeContent.querySelector('input[name="' + fieldName + '"]');
                        if (input) {
                            input.scrollIntoView({block: 'center'});
                            input.focus();
                        }
                        return input;
                    """, field_name)
                    if element:
                        element.clear()
                        element.send_keys(value)
                        self.wait_seconds(0.3)
                        # Verify
                        actual = element.get_attribute('value')
                        if actual == value:
                            log.info(f"Address '{field_name}' typed via send_keys: {value}")
                            return
                        else:
                            log.warning(
                                f"Address '{field_name}' send_keys verification failed: "
                                f"expected='{value}', actual='{actual}'"
                            )
                except Exception as e:
                    log.warning(f"Address '{field_name}' send_keys strategy failed: {e}")

        # Final fallback: try the global Selenium approach as last resort
        log.warning(f"All strategies failed for '{field_name}', trying global Selenium fallback")
        try:
            locator = ("css", f"input[name='{field_name}']")
            self._scroll_popup_to_element(locator)
            self.type_text(locator, value, clear_first=True)
            log.info(f"Address '{field_name}' typed via fallback: {value}")
        except Exception as e:
            log.warning(f"Global Selenium fallback also failed for '{field_name}': {e}")
            # Diagnostic: dump what inputs exist in the active panel
            self._debug_dump_active_panel_inputs(field_name)

    def _fill_active_panel_text_input(self, field_name, value):
        """Fill a text input in the ACTIVE stepper panel using JavaScript.

        This is a generalized version of _fill_address_text_input() that works
        for ANY tab's text inputs, not just address tabs. It scopes the search
        to the currently active stepper panel, avoiding the common bug where
        global CSS selectors find elements in inert/inactive panels.

        Works for fields where the input's name attribute matches exactly:
          - input[name='Member Name'], input[name='Pincode'], etc.

        For fields with trailing TAB chars in name attr (like 'No of Childrens\\t'),
        use _fill_active_panel_text_input_contains() instead.

        V2 FIX: Added value verification and send_keys fallback, same as
        _fill_address_text_input().

        Args:
            field_name: The input's name attribute (e.g. "Member Name", "Pincode")
            value: The text to type into the input
        """
        if not value:
            return

        # Close any leftover overlay panels
        self._force_close_panels()
        self.wait_seconds(0.2)

        max_retries = 3
        for attempt in range(max_retries):
            try:
                result = self.driver.execute_script("""
                    var fieldName = arguments[0];
                    var textValue = arguments[1];

                    // 1. Find the popup container
                    var popup = document.querySelector('.big-model, mat-dialog-container');
                    if (!popup) return {success: false, error: 'No popup found'};

                    // 2. Find the ACTIVE stepper panel
                    var activeContent = popup.querySelector(
                        'div.mat-horizontal-stepper-content-current'
                    );
                    if (!activeContent) {
                        var allPanels = popup.querySelectorAll(
                            'div[role="tabpanel"].mat-horizontal-stepper-content'
                        );
                        for (var p = 0; p < allPanels.length; p++) {
                            if (!allPanels[p].hasAttribute('inert')) {
                                activeContent = allPanels[p];
                                break;
                            }
                        }
                    }
                    if (!activeContent) return {success: false, error: 'No active panel'};

                    // 3. Find the input by name attribute within the active panel
                    var input = activeContent.querySelector('input[name="' + fieldName + '"]');
                    if (!input) return {success: false, error: 'Input not found: ' + fieldName};

                    // 4. Scroll into view and focus
                    input.scrollIntoView({block: 'center'});
                    input.focus();

                    // 5. Clear and set value using Angular-compatible native setter
                    var nativeSet = Object.getOwnPropertyDescriptor(
                        window.HTMLInputElement.prototype, 'value'
                    ).set;

                    // Clear first
                    nativeSet.call(input, '');
                    input.dispatchEvent(new Event('input', {bubbles: true}));
                    input.dispatchEvent(new Event('change', {bubbles: true}));

                    // Set new value
                    nativeSet.call(input, textValue);
                    input.dispatchEvent(new Event('input', {bubbles: true}));
                    input.dispatchEvent(new Event('change', {bubbles: true}));
                    input.dispatchEvent(new Event('blur', {bubbles: true}));

                    // 6. VERIFY: Read back the value to confirm it stuck
                    var actualValue = input.value;
                    return {
                        success: actualValue === textValue,
                        value: actualValue,
                        expected: textValue
                    };
                """, field_name, str(value))

                if result and result.get('success'):
                    log.info(f"Panel text '{field_name}' typed: {value}")
                    return
                elif result and result.get('value') != result.get('expected'):
                    log.warning(
                        f"Panel text '{field_name}' verification failed: "
                        f"expected='{result.get('expected')}', "
                        f"actual='{result.get('value')}' "
                        f"(attempt {attempt + 1}/{max_retries})"
                    )
                else:
                    error = result.get('error', 'Unknown') if result else 'JS returned null'
                    log.warning(
                        f"Panel text input '{field_name}' failed: {error}, "
                        f"retry {attempt + 1}/{max_retries}"
                    )
            except Exception as e:
                log.warning(
                    f"Panel text input '{field_name}' exception: {e}, "
                    f"retry {attempt + 1}/{max_retries}"
                )

            self.wait_seconds(1)

            # --- Strategy B: send_keys fallback on last retry ---
            if attempt == max_retries - 1:
                try:
                    log.info(f"Trying send_keys strategy for panel text '{field_name}'...")
                    element = self.driver.execute_script("""
                        var fieldName = arguments[0];
                        var popup = document.querySelector('.big-model, mat-dialog-container');
                        if (!popup) return null;
                        var activeContent = popup.querySelector(
                            'div.mat-horizontal-stepper-content-current'
                        );
                        if (!activeContent) {
                            var allPanels = popup.querySelectorAll(
                                'div[role="tabpanel"].mat-horizontal-stepper-content'
                            );
                            for (var p = 0; p < allPanels.length; p++) {
                                if (!allPanels[p].hasAttribute('inert')) {
                                    activeContent = allPanels[p];
                                    break;
                                }
                            }
                        }
                        if (!activeContent) return null;
                        var input = activeContent.querySelector('input[name="' + fieldName + '"]');
                        if (input) {
                            input.scrollIntoView({block: 'center'});
                            input.focus();
                        }
                        return input;
                    """, field_name)
                    if element:
                        element.clear()
                        element.send_keys(str(value))
                        self.wait_seconds(0.3)
                        actual = element.get_attribute('value')
                        if actual == str(value):
                            log.info(f"Panel text '{field_name}' typed via send_keys: {value}")
                            return
                except Exception as e:
                    log.warning(f"Panel text '{field_name}' send_keys strategy failed: {e}")

        # Final fallback: try the global Selenium approach
        log.warning(f"JS panel text input failed for '{field_name}', trying global fallback")
        try:
            locator = ("css", f"input[name='{field_name}']")
            self.type_text(locator, value, clear_first=True)
        except Exception as e:
            log.warning(f"Global fallback also failed for '{field_name}': {e}")

    def _fill_active_panel_text_input_contains(self, field_name_partial, value):
        """Fill a text input in the ACTIVE panel where the name attribute
        contains the given substring. Used for fields with trailing TAB
        characters in their name attribute (e.g. 'No of Childrens\\t').

        Args:
            field_name_partial: Substring to match in the name attribute
            value: The text to type into the input
        """
        if not value:
            return

        max_retries = 3
        for attempt in range(max_retries):
            try:
                result = self.driver.execute_script("""
                    var fieldNamePartial = arguments[0];
                    var textValue = arguments[1];

                    var popup = document.querySelector('.big-model, mat-dialog-container');
                    if (!popup) return {success: false, error: 'No popup found'};

                    var activeContent = popup.querySelector(
                        'div.mat-horizontal-stepper-content-current'
                    );
                    if (!activeContent) {
                        var allPanels = popup.querySelectorAll(
                            'div[role="tabpanel"].mat-horizontal-stepper-content'
                        );
                        for (var p = 0; p < allPanels.length; p++) {
                            if (!allPanels[p].hasAttribute('inert')) {
                                activeContent = allPanels[p];
                                break;
                            }
                        }
                    }
                    if (!activeContent) return {success: false, error: 'No active panel'};

                    // Find input whose name CONTAINS the partial string
                    var inputs = activeContent.querySelectorAll('input[name]');
                    var input = null;
                    for (var i = 0; i < inputs.length; i++) {
                        var n = inputs[i].getAttribute('name') || '';
                        if (n.indexOf(fieldNamePartial) >= 0) {
                            input = inputs[i];
                            break;
                        }
                    }
                    if (!input) return {success: false, error: 'Input not found containing: ' + fieldNamePartial};

                    input.scrollIntoView({block: 'center'});

                    var nativeSet = Object.getOwnPropertyDescriptor(
                        window.HTMLInputElement.prototype, 'value'
                    ).set;
                    nativeSet.call(input, '');
                    input.dispatchEvent(new Event('input', {bubbles: true}));
                    input.dispatchEvent(new Event('change', {bubbles: true}));

                    nativeSet.call(input, textValue);
                    input.dispatchEvent(new Event('input', {bubbles: true}));
                    input.dispatchEvent(new Event('change', {bubbles: true}));
                    input.dispatchEvent(new Event('blur', {bubbles: true}));

                    return {success: true, value: textValue};
                """, field_name_partial, str(value))

                if result and result.get('success'):
                    log.info(f"Panel text '{field_name_partial}' typed: {value}")
                    return
                else:
                    error = result.get('error', 'Unknown') if result else 'JS returned null'
                    log.warning(
                        f"Panel text input contains '{field_name_partial}' failed: {error}, "
                        f"retry {attempt + 1}/{max_retries}"
                    )
            except Exception as e:
                log.warning(
                    f"Panel text input contains '{field_name_partial}' exception: {e}, "
                    f"retry {attempt + 1}/{max_retries}"
                )

            self.wait_seconds(1)

        log.warning(f"All retries failed for '{field_name_partial}'")

    def _fill_active_panel_date_input(self, date_value):
        """Fill a datepicker input in the ACTIVE stepper panel.

        Scopes to the active panel to avoid matching the Step 0 DOB input.
        The datepicker input has placeholder='DD/MM/YYYY' but NO name attribute,
        so we find it by placeholder within the active panel.

        Args:
            date_value: Date string in DD/MM/YYYY format
        """
        if not date_value:
            return

        try:
            result = self.driver.execute_script("""
                var dateValue = arguments[0];

                var popup = document.querySelector('.big-model, mat-dialog-container');
                if (!popup) return {success: false, error: 'No popup found'};

                var activeContent = popup.querySelector(
                    'div.mat-horizontal-stepper-content-current'
                );
                if (!activeContent) {
                    var allPanels = popup.querySelectorAll(
                        'div[role="tabpanel"].mat-horizontal-stepper-content'
                    );
                    for (var p = 0; p < allPanels.length; p++) {
                        if (!allPanels[p].hasAttribute('inert')) {
                            activeContent = allPanels[p];
                            break;
                        }
                    }
                }
                if (!activeContent) return {success: false, error: 'No active panel'};

                // Find datepicker input by placeholder within active panel
                var dateInput = activeContent.querySelector(
                    'input[placeholder="DD/MM/YYYY"]'
                );
                if (!dateInput) return {success: false, error: 'Date input not found in active panel'};

                dateInput.scrollIntoView({block: 'center'});

                var nativeSet = Object.getOwnPropertyDescriptor(
                    window.HTMLInputElement.prototype, 'value'
                ).set;
                nativeSet.call(dateInput, '');
                dateInput.dispatchEvent(new Event('input', {bubbles: true}));
                dateInput.dispatchEvent(new Event('change', {bubbles: true}));

                nativeSet.call(dateInput, dateValue);
                dateInput.dispatchEvent(new Event('input', {bubbles: true}));
                dateInput.dispatchEvent(new Event('change', {bubbles: true}));
                dateInput.dispatchEvent(new Event('blur', {bubbles: true}));

                return {success: true, value: dateValue};
            """, date_value)

            if result and result.get('success'):
                log.info(f"Panel date input typed: {date_value}")
            else:
                error = result.get('error', 'Unknown') if result else 'JS returned null'
                log.warning(f"Panel date input failed: {error}")
        except Exception as e:
            log.warning(f"Panel date input exception: {e}")

    def _wait_for_angular_stable(self, timeout=10):
        """Wait for Angular to finish rendering and HTTP requests to complete.

        Uses a polling approach: checks for loading indicators in mat-select
        elements. If any dropdown is still loading, waits and checks again.
        Falls back to a simple fixed wait if the JS check fails.

        FIX: Uses synchronous execute_script (not async) for compatibility
        with all Selenium drivers.
        """
        deadline = time.time() + timeout
        stable_count = 0
        required_stable = 2  # Must be stable for 2 consecutive checks

        while time.time() < deadline:
            try:
                is_stable = self.driver.execute_script("""
                    // Check if any mat-select in the active panel is still loading
                    var popup = document.querySelector('.big-model, mat-dialog-container');
                    if (!popup) return true;  // No popup = nothing to wait for

                    var activeContent = popup.querySelector(
                        'div.mat-horizontal-stepper-content-current'
                    );
                    if (!activeContent) {
                        var allPanels = popup.querySelectorAll(
                            'div[role="tabpanel"].mat-horizontal-stepper-content'
                        );
                        for (var p = 0; p < allPanels.length; p++) {
                            if (!allPanels[p].hasAttribute('inert')) {
                                activeContent = allPanels[p];
                                break;
                            }
                        }
                    }

                    // Check for loading indicators
                    if (activeContent) {
                        var triggers = activeContent.querySelectorAll(
                            'mat-select .mat-select-trigger, ' +
                            'mat-select .mat-mdc-select-trigger'
                        );
                        for (var i = 0; i < triggers.length; i++) {
                            var text = triggers[i].textContent.trim();
                            if (text === 'Loading...' || text === 'loading...') {
                                return false;
                            }
                        }

                        // Also check if any mat-select has no trigger at all
                        // (component still initializing)
                        var selects = activeContent.querySelectorAll('mat-select');
                        for (var i = 0; i < selects.length; i++) {
                            if (selects[i].offsetParent === null) {
                                // Hidden select, skip
                                continue;
                            }
                            var trigger = selects[i].querySelector(
                                '.mat-select-trigger, .mat-mdc-select-trigger'
                            );
                            if (!trigger) {
                                // Select exists but no trigger yet = still loading
                                return false;
                            }
                        }
                    }

                    return true;
                """)

                if is_stable:
                    stable_count += 1
                    if stable_count >= required_stable:
                        return
                else:
                    stable_count = 0

            except Exception:
                # JS check failed, just do a fixed wait
                self.wait_seconds(2)
                return

            self.wait_seconds(0.5)

        # Timeout reached — proceed anyway
        log.debug("Angular stability wait timed out, proceeding anyway")

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

    def _scroll_popup_to_bottom(self):
        """Scroll the popup/dialog container to the bottom.

        Used before filling text inputs (Pin Code, Address) that are
        at the bottom of the address form and may not be visible in
        the popup's scrollable area.
        """
        self.driver.execute_script("""
            var popup = document.querySelector('.big-model, mat-dialog-container, .cdk-dialog-container');
            if (popup) {
                // Scroll the popup itself to bottom
                popup.scrollTop = popup.scrollHeight;
                // Also scroll any inner scrollable containers to bottom
                var scrollables = popup.querySelectorAll('[style*="overflow"], .mat-stepper-content, .cdk-step-content');
                for (var i = 0; i < scrollables.length; i++) {
                    scrollables[i].scrollTop = scrollables[i].scrollHeight;
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

    # ==============================================================
    #  PURE JAVASCRIPT cascading dropdown methods
    #  --------------------------------------------------------------
    #  ROOT CAUSE of StaleElementReferenceException:
    #    After selecting a parent dropdown (e.g. Country "India"),
    #    Angular re-renders dependent dropdown components (State,
    #    District, Taluka, Village). The mat-select DOM elements
    #    are DESTROYED and RECREATED. Any Python-side WebElement
    #    reference to the old element becomes stale.
    #
    #  FIX: Use a 2-phase pure-JavaScript approach that NEVER holds
    #    Python-side WebElement references across Angular re-renders:
    #      Phase 1: Pure JS finds and clicks the mat-select (atomic)
    #      Python-side wait for the overlay panel to appear
    #      Phase 2: Pure JS finds and clicks the option in the overlay
    #
    #  The overlay panel (div[role='listbox']) lives in the CDK
    #  overlay container, which is OUTSIDE Angular's component tree.
    #  Overlay options are stable and never stale.
    # ==============================================================

    def _fill_cascading_dropdown(self, label_text, value):
        """Fill a cascading dropdown using pure JavaScript (2-phase).

        This method COMPLETELY avoids StaleElementReferenceException by
        never holding Python-side WebElement references. Each phase does
        a fresh DOM query within a single atomic JS execution.

        Phase 1: JS finds the mat-select in the active panel and clicks it
        Phase 2: After Python-side wait, JS finds and clicks the option

        Args:
            label_text: The dropdown label (e.g. "Country", "State")
            value: The option text to select. None = pick first valid option.
                   Empty string = skip this dropdown entirely.
        """
        if value == "":
            return

        max_retries = 5
        for attempt in range(max_retries):
            # Phase 1: Find and click the dropdown (pure JS, atomic)
            open_result = self._js_open_cascading_dropdown(label_text)
            if not open_result:
                log.warning(
                    f"Could not open cascading dropdown '{label_text}', "
                    f"retry {attempt + 1}/{max_retries}"
                )
                self._close_select_panel()
                self.wait_seconds(1)
                continue

            # Wait for the overlay panel to appear and populate with options
            self.wait_seconds(1.5)

            # Phase 2: Find and click the option (pure JS, atomic)
            select_result = self._js_select_cascading_option(label_text, value)
            if select_result and select_result.get('success'):
                selected_text = select_result.get('selectedText', '?')
                log.info(f"Address '{label_text}' selected: {selected_text}")
                # Wait for Angular to re-render dependent dropdowns
                wait_after = 3.0 if label_text == "Country" else 2.5
                self.wait_seconds(wait_after)
                return

            error_msg = select_result.get('error', 'Unknown') if select_result else 'JS returned null'
            log.warning(
                f"Option selection failed for '{label_text}': {error_msg}, "
                f"retry {attempt + 1}/{max_retries}"
            )
            self._close_select_panel()
            self.wait_seconds(0.5)

        log.warning(f"Cascading dropdown '{label_text}' failed after {max_retries} retries")

    def _js_open_cascading_dropdown(self, label_text):
        """Phase 1: Find and click a cascading dropdown using pure JavaScript.

        Runs entirely within a single JS execution context, so there is
        NO window for Angular to re-render the element between finding
        it and clicking it. The click event is dispatched atomically
        right after the element is found.

        Returns True if the dropdown was found and clicked, False otherwise.
        """
        try:
            result = self.driver.execute_script("""
                var labelText = arguments[0];

                // 1. Find the popup container
                var popup = document.querySelector('.big-model, mat-dialog-container');
                if (!popup) return {success: false, error: 'No popup found'};

                // 2. Find the ACTIVE stepper panel only
                var activeContent = popup.querySelector(
                    'div.mat-horizontal-stepper-content-current'
                );
                if (!activeContent) {
                    var allPanels = popup.querySelectorAll(
                        'div[role="tabpanel"].mat-horizontal-stepper-content'
                    );
                    for (var p = 0; p < allPanels.length; p++) {
                        if (!allPanels[p].hasAttribute('inert')) {
                            activeContent = allPanels[p];
                            break;
                        }
                    }
                }
                if (!activeContent) return {success: false, error: 'No active panel'};

                // 3. Find the mat-select matching the label
                var select = null;

                // Strategy A: mat-label inside mat-form-field
                var labels = activeContent.querySelectorAll('mat-label');
                for (var i = 0; i < labels.length; i++) {
                    if (labels[i].textContent.trim().includes(labelText)) {
                        var field = labels[i].closest(
                            'mat-form-field, .mat-mdc-form-field'
                        );
                        if (field) {
                            var s = field.querySelector('mat-select');
                            if (s && s.offsetParent !== null) {
                                select = s;
                                break;
                            }
                        }
                    }
                }

                // Strategy B: table row with label text -> mat-select
                if (!select) {
                    var rows = activeContent.querySelectorAll('tr, .grid-row');
                    for (var i = 0; i < rows.length; i++) {
                        var cells = rows[i].querySelectorAll('td, th');
                        for (var j = 0; j < cells.length; j++) {
                            var cellText = cells[j].textContent.trim()
                                .replace(/\\s*\\*/g, '');
                            if (cellText.includes(labelText)) {
                                var s = rows[i].querySelector('mat-select');
                                if (s && s.offsetParent !== null) {
                                    select = s;
                                    break;
                                }
                            }
                        }
                        if (select) break;
                    }
                }

                // Strategy C: any leaf text -> closest container -> mat-select
                if (!select) {
                    var allEls = activeContent.querySelectorAll(
                        'span, div, label, p, td, th'
                    );
                    for (var i = 0; i < allEls.length; i++) {
                        var el = allEls[i];
                        if (el.children.length === 0 ||
                            el.tagName === 'TD' ||
                            el.tagName === 'TH' ||
                            el.tagName === 'LABEL') {
                            var text = el.textContent.trim()
                                .replace(/\\s*\\*/g, '').replace(/\\s*:/g, '');
                            if (text === labelText || text.startsWith(labelText)) {
                                var container = el.closest(
                                    'mat-form-field, .mat-mdc-form-field, ' +
                                    'tr, .grid-row, .form-row, .row'
                                );
                                if (container) {
                                    var s = container.querySelector('mat-select');
                                    if (s && s.offsetParent !== null) {
                                        select = s;
                                        break;
                                    }
                                }
                            }
                        }
                    }
                }

                if (!select) {
                    return {
                        success: false,
                        error: 'Dropdown not found for label: ' + labelText
                    };
                }

                // 4. Scroll into view within popup
                select.scrollIntoView({block: 'center'});

                // 5. Click to open the dropdown panel
                select.click();

                return {success: true};
            """, label_text)
            return result and result.get('success')
        except Exception as e:
            log.warning(f"JS open cascading dropdown failed for '{label_text}': {e}")
            return False

    def _js_select_cascading_option(self, label_text, value):
        """Phase 2: Find and click an option in the open overlay panel via pure JS.

        The overlay panel (div[role='listbox']) lives in the CDK overlay
        container which is OUTSIDE Angular's component tree. Options in
        the overlay are stable and never stale.

        Args:
            label_text: The dropdown label (for logging/error messages)
            value: The option text to select. None = pick first valid option.

        Returns:
            Dict with 'success' and 'selectedText' or 'error'.
        """
        try:
            result = self.driver.execute_script("""
                var labelText = arguments[0];
                var optionValue = arguments[1];
                var pickFirst = (optionValue === null);
                if (!pickFirst) optionValue = optionValue.trim().toLowerCase();

                // 1. Find the VISIBLE overlay panel (may be multiple if
                //    page has other dropdowns open)
                var overlayPanel = null;
                var panels = document.querySelectorAll('div[role="listbox"]');
                for (var i = 0; i < panels.length; i++) {
                    if (panels[i].offsetParent !== null) {
                        overlayPanel = panels[i];
                        break;
                    }
                }
                if (!overlayPanel) {
                    return {
                        success: false,
                        error: 'No overlay panel visible for: ' + labelText
                    };
                }

                // 2. Find matching option
                var options = overlayPanel.querySelectorAll(
                    'mat-option, [role="option"]'
                );
                var selectedOption = null;
                var firstValidOption = null;

                for (var i = 0; i < options.length; i++) {
                    var optText = options[i].textContent.trim();
                    var isVisible = options[i].offsetParent !== null;
                    var isPlaceholder = optText.startsWith('Select ')
                        || optText === '';

                    if (isVisible && !isPlaceholder && optText) {
                        if (!firstValidOption) {
                            firstValidOption = options[i];
                        }
                        if (!pickFirst &&
                            optText.trim().toLowerCase() === optionValue) {
                            selectedOption = options[i];
                            break;
                        }
                    }
                }

                if (pickFirst) selectedOption = firstValidOption;

                if (!selectedOption) {
                    // Close the overlay before returning error
                    var backdrops = document.querySelectorAll(
                        '.cdk-overlay-backdrop:not(.cdk-overlay-dark-backdrop)'
                    );
                    for (var b = 0; b < backdrops.length; b++) {
                        try { backdrops[b].click(); } catch(e) {}
                    }
                    return {
                        success: false,
                        error: 'Option not found for: ' + labelText +
                            (pickFirst ? '' : ' value=' + arguments[1])
                    };
                }

                // 3. Click the option
                selectedOption.click();

                return {
                    success: true,
                    selectedText: selectedOption.textContent.trim()
                };
            """, label_text, value)
            return result
        except Exception as e:
            log.warning(f"JS select cascading option failed for '{label_text}': {e}")
            return None

    # ==============================================================
    #  Bank Details Tab
    # ==============================================================

    def fill_bank_details(self, data):
        """Fill the Bank Details tab.

        FILL ORDER: upper visible text inputs first, then scroll-down fields.
        NOTE: Account Type label has a trailing tab character: "Account Type\\t"
        so the XPath contains(.,'Account Type') still matches.

        FIX: Uses _fill_active_panel_text_input() for ALL text inputs instead
        of global type_text(). After force-navigate, global CSS selectors like
        input[name='Bank Name'] may find elements in inert address panels,
        AND send_keys() doesn't trigger Angular's reactive form change detection.
        The panel-scoped JS method uses nativeInputValueSetter + dispatchEvent
        to properly register values with Angular's form model.
        """
        log.info("Filling Bank Details...")

        # Wait for panel content to render after navigation
        self.wait_seconds(1)

        # Upper visible text inputs — FIX: panel-scoped + Angular-synced
        if data.get("bank_name"):
            self._fill_active_panel_text_input("Bank Name", data["bank_name"])
        if data.get("branch"):
            self._fill_active_panel_text_input("Branch", data["branch"])
        if data.get("ifsc_code"):
            self._fill_active_panel_text_input("IFSC Code", data["ifsc_code"])

        # Dropdowns (may need scroll)
        self._fill_dropdown_if_provided(self.ACCOUNT_TYPE_SELECT, data.get("account_type"))

        # Lower text inputs — FIX: panel-scoped + Angular-synced
        if data.get("account_holder_name"):
            self._fill_active_panel_text_input("Account Holder Name", data["account_holder_name"])
        if data.get("account_number"):
            self._fill_active_panel_text_input("Account Number", data["account_number"])

        # More dropdowns
        self._fill_dropdown_if_provided(self.BANK_PROOF_SELECT, data.get("bank_proof"))

        log.info("Bank Details filled")

    # ==============================================================
    #  Family Details Tab (Borrower Farmer only)
    # ==============================================================

    def fill_family_details(self, data):
        """Fill the Family Details tab (table row — uses JS-scoped element finding).

        FIX: All text inputs and dropdowns in Family Details must be scoped
        to the ACTIVE panel because Angular Material renders ALL tab contents
        in the DOM simultaneously. Global CSS selectors like input[name='Address']
        find elements in inert address panels, causing TimeoutException.

        Uses _fill_active_panel_text_input() for text inputs (same JS-scoping
        pattern as _fill_address_text_input() for address tabs) and
        _fill_cascading_dropdown() for dropdowns (already panel-scoped via JS).

        Key field name differences from address tabs:
          - Pincode (not 'Pin Code') — input[name='Pincode']
          - Address — same name as address tabs but in different panel
          - No of Childrens — name attr has trailing TAB char, use contains()
          - Date Of Birth — 2nd datepicker in the form, must scope to panel
        """
        log.info("Filling Family Details...")

        # Text inputs — use JS-scoped finding to avoid matching inactive panels
        # FIX: Data keys now match generate_valid_family_data() output:
        #   'family_phone_number' (not 'phone_number')
        #   'family_dob' (not 'date_of_birth')
        #   'family_gender' (not 'gender')
        #   'family_pincode' (not 'pincode')
        #   'family_address' (not 'address')
        if data.get("member_name"):
            self._fill_active_panel_text_input("Member Name", data["member_name"])
        if data.get("family_phone_number"):
            self._fill_active_panel_text_input("Phone Number", data["family_phone_number"])

        # Date Of Birth — must scope to active panel's datepicker
        if data.get("family_dob"):
            self._fill_active_panel_date_input(data["family_dob"])

        # Age is READONLY — auto-calculated from DOB, skip

        # Dropdowns — _fill_cascading_dropdown() already scopes to active panel
        # FIX: Use 'family_gender' key (not 'gender')
        self._fill_dropdown_if_provided(self.FAMILY_GENDER_SELECT, data.get("family_gender"))
        self._fill_dropdown_if_provided(self.EDUCATION_OF_FARMER_FAMILY_SELECT, data.get("education_of_farmer_family"))
        self._fill_dropdown_if_provided(self.RELATIONSHIP_SELECT, data.get("relationship"))

        # Is Member Staying With Farmer toggle
        # (skip unless data explicitly requests it)

        # Pincode — note: name='Pincode' (not 'Pin Code' like address tabs)
        # FIX: Use 'family_pincode' key (not 'pincode')
        if data.get("family_pincode"):
            self._fill_active_panel_text_input("Pincode", data["family_pincode"])

        # Address — same name as address tab fields but in Family Details panel
        # FIX: Use 'family_address' key (not 'address')
        if data.get("family_address"):
            self._fill_active_panel_text_input("Address", data["family_address"])

        # More dropdowns
        self._fill_dropdown_if_provided(self.MARITAL_STATUS_SELECT, data.get("marital_status"))

        # No of Childrens — name attr has trailing TAB char
        if data.get("no_of_childrens"):
            self._fill_active_panel_text_input_contains("No of Childrens", data["no_of_childrens"])

        self._fill_dropdown_if_provided(self.MEMBER_ANNUAL_INCOME_SELECT, data.get("member_annual_income"))

        # Off Farm Income
        if data.get("off_farm_income"):
            self._fill_active_panel_text_input("Off Farm Income", data["off_farm_income"])

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

        FIX: Uses _fill_active_panel_text_input_contains() for ALL fields because
        Land/Crop number field name attributes have trailing TAB chars (\t).
        This avoids the global CSS selector matching wrong panels.
        """
        log.info("Filling Land Details...")

        # Upper visible text inputs
        # NOTE: Farm Name also exists in Crop Details — use contains() to scope
        if data.get("farm_name"):
            self._fill_active_panel_text_input("Farm Name", data["farm_name"])
        # No Of Owner — name has trailing TAB, BUG-F01: required but no asterisk
        if data.get("no_of_owner"):
            self._fill_active_panel_text_input_contains("No Of Owner", data["no_of_owner"])
        # FIX: Data key names now match generate_valid_land_data() output:
        #   data key 'total_land_on_document' (not 'total_land_on_document_hectare')
        #   data key 'individual_land_holding' (not 'individual_land_holding_hectare')
        if data.get("total_land_on_document"):
            self._fill_active_panel_text_input_contains("Total Land On Document", data["total_land_on_document"])
        if data.get("individual_land_holding"):
            self._fill_active_panel_text_input_contains("Individual Land Holding", data["individual_land_holding"])

        # Middle text inputs — name attrs have trailing TAB chars
        if data.get("gat_number"):
            self._fill_active_panel_text_input_contains("Gat Number", data["gat_number"])
        if data.get("land_coordinate"):
            self._fill_active_panel_text_input_contains("Land Coordinate", data["land_coordinate"])

        # Scroll-down text inputs — name attrs have trailing TAB chars
        # FIX: Data keys now match generate_valid_land_data() output:
        #   'total_cultivation_land_hectare' (not 'total_cultivation_land_in_hectare')
        #   'total_cultivation_land_acreage' (not 'total_cultivation_land_in_acreage')
        if data.get("total_land_in_hectare"):
            self._fill_active_panel_text_input_contains("Total Land In hectare", data["total_land_in_hectare"])
        if data.get("total_cultivation_land_hectare"):
            self._fill_active_panel_text_input_contains("Total Cultivation Land In hectare", data["total_cultivation_land_hectare"])
        if data.get("total_cultivation_land_acreage"):
            self._fill_active_panel_text_input_contains("Total Cultivation Land in acreage", data["total_cultivation_land_acreage"])

        # Dropdowns
        self._fill_dropdown_if_provided(self.LAND_OWNERSHIP_SELECT, data.get("land_ownership"))

        # Bottom text inputs
        if data.get("latitude"):
            self._fill_active_panel_text_input("Latitude(Lat)", data["latitude"])
        if data.get("longitude"):
            self._fill_active_panel_text_input("Longitude(Log)", data["longitude"])

        log.info("Land Details filled")

    # ==============================================================
    #  Crop Details Tab (Borrower Farmer + FPC Member)
    # ==============================================================

    def fill_crop_details(self, data):
        """Fill the Crop Details tab.

        FIX: Uses panel-scoped methods for all fields. Farm Name also exists
        in Land Details tab, and number field name attrs have trailing TAB chars.
        """
        log.info("Filling Crop Details...")

        # Farm Name — also exists in Land Details, must scope to active panel
        if data.get("crop_farm_name"):
            self._fill_active_panel_text_input("Farm Name", data["crop_farm_name"])
        self._fill_dropdown_if_provided(self.CROP_SELECT, data.get("crop"))
        self._fill_dropdown_if_provided(self.SEASON_SELECT, data.get("season"))
        # Number fields — name attrs have trailing TAB chars
        # FIX: Data keys now match generate_valid_crop_data() output:
        #   'cultivation_land_hectare' (not 'cultivation_land_in_hectare')
        #   'cultivation_land_acreage' (not 'cultivation_land_in_acreage')
        if data.get("cultivation_land_hectare"):
            self._fill_active_panel_text_input_contains("Cultivation Land In hectare", data["cultivation_land_hectare"])
        if data.get("expected_yield_projection"):
            self._fill_active_panel_text_input_contains("Expected Yield projection", data["expected_yield_projection"])
        if data.get("actual_produce"):
            self._fill_active_panel_text_input_contains("Actual Produce", data["actual_produce"])
        if data.get("cultivation_land_acreage"):
            self._fill_active_panel_text_input_contains("Cultivation Land In acreage", data["cultivation_land_acreage"])

        log.info("Crop Details filled")

    # ==============================================================
    #  KYC Details Tab (Borrower Farmer + FPC Member)
    # ==============================================================

    def fill_kyc_details(self, data):
        """Fill the KYC Details tab.

        FIX: Uses _fill_active_panel_text_input() for KYC Number instead
        of global type_text() for Angular form model sync.
        """
        log.info("Filling KYC Details...")

        self._fill_dropdown_if_provided(self.KYC_DOCUMENT_SELECT, data.get("kyc_document"))
        if data.get("kyc_number"):
            self._fill_active_panel_text_input("KYC Number", data["kyc_number"])

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

        FIX: Uses _fill_active_panel_text_input() for Exact Amount instead
        of global type_text() for Angular form model sync.
        """
        log.info("Filling Income Details...")

        self._fill_dropdown_if_provided(self.SOURCE_OF_INCOME_SELECT, data.get("source_of_income"))
        self._fill_dropdown_if_provided(self.INCOME_BRACKET_SELECT, data.get("income_bracket"))
        if data.get("exact_amount"):
            self._fill_active_panel_text_input("Exact Amount", data["exact_amount"])

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
        """Fill the Award Details tab.

        FIX: Uses _fill_active_panel_text_input() for Name and Year instead
        of global type_text() for Angular form model sync.
        NOTE: 'Name' is a common field name — panel-scoping prevents matching
        the wrong element in an inert panel.
        """
        log.info("Filling Award Details...")

        # FIX: Data keys match generate_valid_award_data() output
        if data.get("award_name"):
            self._fill_active_panel_text_input("Name", data["award_name"])
        if data.get("award_year"):
            self._fill_active_panel_text_input("Year", data["award_year"])

        log.info("Award Details filled")

    # ==============================================================
    #  Loan Details Tab (Borrower Farmer only)
    # ==============================================================

    def fill_loan_details(self, data):
        """Fill the Loan Details tab.
        NOTE: Sanctioned Amount & Present Outstanding Amount accept 0/. prefix (BUG-F06).

        FIX: Uses _fill_active_panel_text_input() for ALL text inputs instead
        of global type_text() for Angular form model sync. 'Purpose Of Loan'
        and other fields have name attrs with trailing TAB chars, so use
        _fill_active_panel_text_input_contains() for those.
        """
        log.info("Filling Loan Details...")

        if data.get("loan_name"):
            self._fill_active_panel_text_input("Loan Name", data["loan_name"])
        self._fill_dropdown_if_provided(self.FACILITY_TYPE_SELECT, data.get("facility_type"))
        if data.get("purpose_of_loan"):
            self._fill_active_panel_text_input_contains("Purpose Of Loan", data["purpose_of_loan"])
        # FIX: Data key 'availed_from_date' to match generator
        if data.get("availed_from_date"):
            # 'Availed From' is a datepicker — use panel-scoped date input
            self._fill_active_panel_date_input(data["availed_from_date"])
        if data.get("sanctioned_amount"):
            self._fill_active_panel_text_input_contains("Sanctioned Amount", data["sanctioned_amount"])
        if data.get("present_outstanding_amount"):
            self._fill_active_panel_text_input_contains("Present Outstanding Amount", data["present_outstanding_amount"])

        log.info("Loan Details filled")

    # ==============================================================
    #  Navigate-to-tab helper (tab name -> step index)
    # ==============================================================

    def navigate_to_tab_by_name(self, target_tab_name):
        """Navigate to a specific stepper tab. Returns True if reached.

        SPEED FIX: Angular Material's linear stepper blocks header clicks and
        Next-button navigation when required fields on previous tabs aren't
        filled. Strategies 1-3 (header click, Next stepping, retry) all fail
        in this case, wasting 60+ seconds before reaching Strategy 4
        (force-navigate) which always works.

        New approach: Try quick header click first (fast path for adjacent
        tabs that Angular allows). If that fails, skip straight to
        force-navigate instead of wasting time on Next-button stepping.
        """
        target_lower = target_tab_name.strip().lower()
        log.info(f"Navigating to tab: {target_tab_name}")

        # Find the target tab index
        tab_names = self.get_stepper_tab_names()
        target_idx = -1
        for idx, name in enumerate(tab_names):
            if target_lower in name.strip().lower():
                target_idx = idx
                break

        if target_idx < 0:
            log.warning(f"Tab not found in stepper headers: {target_tab_name}")
            return False

        # Fast path: Check if already on this tab
        current_idx = self.get_current_step_index()
        if current_idx == target_idx:
            log.info(f"Already on tab: {target_tab_name}")
            return True

        # Quick attempt: Direct header click (works for adjacent tabs
        # that Angular's linear mode allows, takes ~1 second)
        if self.click_stepper_header(target_idx):
            self.wait_seconds(0.8)
            active_name = self.get_active_tab_name()
            if target_lower in active_name.lower():
                log.info(f"Reached tab via header click: {target_tab_name}")
                return True

        # FAST PATH: Skip Next-button stepping and go straight to
        # force-navigate. After filling a tab with required fields,
        # Angular blocks normal navigation to subsequent tabs. The
        # Next-button stepping wastes 30-60 seconds per tab before
        # failing. Force-navigate always works and takes ~2 seconds.
        log.info(f"Quick header click failed, force-navigating to tab: {target_tab_name}")
        if self._force_navigate_to_step(target_idx):
            self.wait_seconds(1.5)
            # Verify via active tab name
            active_name = self.get_active_tab_name()
            if target_lower in active_name.lower():
                log.info(f"Force-navigated to tab: {target_tab_name}")
                return True
            # Even if tab name doesn't match, check if the DOM
            # panel is now active (sometimes get_active_tab_name
            # fails but the panel IS active)
            try:
                is_active = self.driver.execute_script("""
                    var popup = document.querySelector(
                        '.big-model, mat-dialog-container'
                    );
                    if (!popup) return false;
                    var active = popup.querySelector(
                        'div.mat-horizontal-stepper-content-current'
                    );
                    if (!active) return false;
                    return !active.hasAttribute('inert');
                """)
                if is_active:
                    log.info(f"Force-navigate succeeded (panel is active): {target_tab_name}")
                    return True
            except Exception:
                pass

        log.warning(f"Could not navigate to tab: {target_tab_name}")
        return False

    def _force_navigate_to_step(self, target_index):
        """Force-navigate to a stepper step by directly manipulating
        Angular Material's internal DOM state via JavaScript.

        This bypasses:
        - Linear mode restrictions (aria-disabled)
        - Validation-based navigation blocking
        - Step completion requirements

        Works by:
        1. Removing 'inert' from target panel
        2. Adding 'inert' to all other panels
        3. Updating CSS classes for active/previous states
        4. Updating step header aria-selected attributes
        5. Dispatching click event on the target header
        """
        try:
            result = self.driver.execute_script("""
                var targetIdx = arguments[0];
                var popup = document.querySelector(
                    '.big-model, mat-dialog-container'
                );
                if (!popup) return false;

                var stepper = popup.querySelector(
                    'mat-horizontal-stepper, mat-stepper'
                );
                if (!stepper) return false;

                // 1. Get all step content panels
                var panels = stepper.querySelectorAll(
                    'div[role="tabpanel"].mat-horizontal-stepper-content'
                );
                if (targetIdx < 0 || targetIdx >= panels.length) return false;

                // 2. Update panel states
                for (var i = 0; i < panels.length; i++) {
                    if (i === targetIdx) {
                        // Make this panel active
                        panels[i].removeAttribute('inert');
                        panels[i].classList.add(
                            'mat-horizontal-stepper-content-current'
                        );
                        panels[i].classList.remove(
                            'mat-horizontal-stepper-content-previous'
                        );
                    } else {
                        // Make other panels inactive
                        panels[i].setAttribute('inert', '');
                        panels[i].classList.remove(
                            'mat-horizontal-stepper-content-current'
                        );
                        panels[i].classList.add(
                            'mat-horizontal-stepper-content-previous'
                        );
                    }
                }

                // 3. Update step header states
                // FIX: Also remove 'mat-step-selected' class from non-target
                // headers so that get_active_tab_name() doesn't pick up stale
                // CSS classes from the previously-active tab.
                var headers = stepper.querySelectorAll('mat-step-header');
                for (var i = 0; i < headers.length; i++) {
                    if (i === targetIdx) {
                        headers[i].setAttribute('aria-selected', 'true');
                        headers[i].removeAttribute('aria-disabled');
                        // Add selected class if Angular uses it
                        if (!headers[i].classList.contains('mat-step-selected')) {
                            headers[i].classList.add('mat-step-selected');
                        }
                        // Also ensure inner label has selected class
                        var innerLabels = headers[i].querySelectorAll(
                            '.mat-step-label, .mat-step-text-label'
                        );
                        for (var l = 0; l < innerLabels.length; l++) {
                            if (!innerLabels[l].classList.contains('mat-step-label-selected')) {
                                innerLabels[l].classList.add('mat-step-label-selected');
                                innerLabels[l].classList.add('mat-step-label-active');
                            }
                        }
                    } else {
                        headers[i].setAttribute('aria-selected', 'false');
                        // FIX: Remove ALL selected/active indicators
                        headers[i].classList.remove('mat-step-selected');
                        // Remove inner label selected classes too
                        var innerLabels = headers[i].querySelectorAll(
                            '.mat-step-label, .mat-step-text-label'
                        );
                        for (var l = 0; l < innerLabels.length; l++) {
                            innerLabels[l].classList.remove('mat-step-label-selected');
                            innerLabels[l].classList.remove('mat-step-label-active');
                        }
                    }
                }

                // 4. Also update the icon states
                var icons = stepper.querySelectorAll(
                    '.mat-step-icon, .mat-mdc-step-icon'
                );
                for (var i = 0; i < icons.length; i++) {
                    if (i === targetIdx) {
                        icons[i].classList.add('mat-step-icon-selected');
                    } else {
                        icons[i].classList.remove('mat-step-icon-selected');
                    }
                }

                // 5. Click the target header to trigger Angular's state update
                if (targetIdx < headers.length) {
                    headers[targetIdx].click();
                }

                return true;
            """, target_index)
            return bool(result)
        except Exception as e:
            log.warning(f"Force navigate to step {target_index} failed: {e}")
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
        """Handle SweetAlert2 success alert. Returns alert title text.

        FIX: After Submit, the browser session may die (InvalidSessionIdException)
        if the form submission triggers a page navigation. Also, SweetAlert2
        may auto-dismiss or have a different DOM structure. This method now
        handles both cases gracefully instead of crashing.

        V2 FIX: Reduced default timeout from 60s to 30s for create_farmer
        calls. When validation fails with inline mat-error (not SweetAlert),
        the old 60s wait was wasting time. Now also checks for inline
        validation errors when no SweetAlert appears.
        """
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, ".swal2-container"))
            )
            self.wait_seconds(1)
        except (TimeoutException, InvalidSessionIdException):
            # No SweetAlert appeared — check for inline validation errors
            inline_errors = self.get_mat_error_text()
            if inline_errors:
                error_summary = "; ".join(inline_errors[:5])
                log.warning(f"No SweetAlert, but inline validation errors found: {error_summary}")
                return f"VALIDATION_ERRORS: {error_summary}"
            log.warning("No SweetAlert2 alert appeared (timeout or session died)")
            return ""

        # Try to read the title — may fail if alert auto-dismissed or session died
        try:
            title = self.driver.find_element(By.CSS_SELECTOR, "#swal2-title").text.strip()
        except Exception as e:
            log.warning(f"Could not read swal2-title: {e}")
            # Try alternative selectors
            try:
                container = self.driver.find_element(By.CSS_SELECTOR, ".swal2-container")
                title = container.text.strip()
            except Exception:
                title = ""

        # Try to click confirm button
        try:
            self._swal2_confirm_click()
            self.wait_seconds(1)
        except (InvalidSessionIdException, Exception) as e:
            log.warning(f"Could not click swal2 confirm: {e}")

        return title

    def handle_validation_warning(self, timeout=5):
        """Handle SweetAlert2 validation warning. Returns alert title text."""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, ".swal2-container"))
            )
            try:
                title = self.driver.find_element(By.CSS_SELECTOR, "#swal2-title").text.strip()
            except Exception:
                try:
                    title = self.driver.find_element(By.CSS_SELECTOR, ".swal2-container").text.strip()
                except Exception:
                    title = ""
            try:
                self._swal2_confirm_click()
                self.wait_seconds(0.5)
            except Exception:
                pass
            return title
        except (TimeoutException, InvalidSessionIdException):
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
        """Search for a farmer using the search input.

        FIX: Multiple search input strategies because the ERP's search
        input CSS varies between screens. Try each selector in order.
        """
        log.info(f"Searching for: {search_text}")
        try:
            # Try opening search panel first
            search_toggle = self.driver.find_elements(By.CSS_SELECTOR, "button.search-btn")
            if search_toggle:
                try:
                    self.driver.execute_script("arguments[0].click();", search_toggle[0])
                    self.wait_seconds(0.5)
                except Exception:
                    pass

            # FIX: Try multiple search input selectors
            search_selectors = [
                "input#erpSearchInput",
                "input[placeholder='Search']",
                "input[formcontrolname='search']",
                ".erp-search-wrapper input",
                "input[type='search']",
                "input[aria-label='Search']",
            ]

            search_input = None
            for selector in search_selectors:
                try:
                    els = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for el in els:
                        if el.is_displayed():
                            search_input = el
                            break
                    if search_input:
                        break
                except Exception:
                    continue

            if not search_input:
                # Last resort: find ANY visible input on the page that looks like search
                try:
                    all_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='text'], input[type='search']")
                    for inp in all_inputs:
                        try:
                            placeholder = inp.get_attribute("placeholder") or ""
                            aria_label = inp.get_attribute("aria-label") or ""
                            if ("search" in placeholder.lower() or
                                "search" in aria_label.lower() or
                                "erpSearchInput" in (inp.get_attribute("id") or "")):
                                search_input = inp
                                break
                        except Exception:
                            continue
                except Exception:
                    pass

            if search_input:
                search_input.clear()
                search_input.send_keys(search_text)
                search_input.send_keys(Keys.ENTER)
                self.wait_seconds(2)
                log.info(f"Search executed for: {search_text}")
            else:
                log.warning("Search input not found with any selector — skipping search")

        except Exception as e:
            log.warning(f"Search failed: {e}")

    def clear_search(self):
        """Clear the search input."""
        try:
            search_selectors = [
                "input#erpSearchInput",
                "input[placeholder='Search']",
                "input[formcontrolname='search']",
                ".erp-search-wrapper input",
                "input[type='search']",
                "input[aria-label='Search']",
            ]
            search_input = None
            for selector in search_selectors:
                try:
                    els = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for el in els:
                        if el.is_displayed():
                            search_input = el
                            break
                    if search_input:
                        break
                except Exception:
                    continue
            if search_input:
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

        # Wait for stepper tabs to appear after Farmer Category selection.
        # Angular creates the stepper tabs dynamically after category is chosen.
        # FIX: Wait up to 5 seconds for tabs to render before proceeding.
        for wait_attempt in range(5):
            tab_names = self.get_stepper_tab_names()
            non_empty = [n for n in tab_names if n.strip()]
            if non_empty:
                break
            log.info(f"Waiting for stepper tabs to appear... attempt {wait_attempt + 1}/5")
            self.wait_seconds(1)

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
        next_clicked = self.click_stepper_next()
        if not next_clicked:
            log.warning("Stepper Next click failed after Step 0 — trying force navigate")
        self.wait_seconds(1.5)

        # Verify we actually moved past Step 0
        active_tab = self.get_active_tab_name()
        log.info(f"After Step 0 Next click, active tab: {active_tab}")

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

            # Verify we're on the right tab (for logging only)
            actual_tab = self.get_active_tab_name()
            log.info(f"Current tab: {actual_tab} (target: {tab_name})")

            # FIX: Always use the TARGET tab name for fill routing, NOT the
            # DETECTED active tab name. After force-navigate, get_active_tab_name()
            # may return a stale/wrong value because Angular's stepper header
            # state isn't fully updated. The target tab name is authoritative
            # because navigate_to_tab_by_name() already succeeded.
            fill_tab_name = tab_name

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

        # FIX: Before submitting, check for validation errors
        # and log them for debugging
        validation_errors = self.get_mat_error_text()
        if validation_errors:
            log.warning(f"Validation errors before submit: {validation_errors}")

        self.submit()
        self.wait_seconds(2)

        # Handle success or validation alert
        # V2 FIX: Reduced timeout from 30s to 15s. If SweetAlert doesn't appear
        # in 15s, it's almost certainly a validation failure. The old 30s wait
        # was wasting time on every failed submission.
        alert_title = self.handle_success_alert(timeout=15)

        # If submission failed, check for validation warning
        if "successfully" not in alert_title.lower():
            validation_warning = self.handle_validation_warning(timeout=3)
            if validation_warning:
                log.warning(f"Validation warning: {validation_warning}")
                alert_title = validation_warning

            # V2 FIX: If STILL no useful error message, check for inline
            # mat-error again (Angular may show them after Submit click)
            if not alert_title or alert_title == "":
                post_submit_errors = self.get_mat_error_text()
                if post_submit_errors:
                    error_summary = "; ".join(post_submit_errors[:5])
                    log.warning(f"Post-submit validation errors: {error_summary}")
                    alert_title = f"VALIDATION_ERRORS: {error_summary}"

        result = {
            "status": "PASSED" if "successfully" in alert_title.lower() else "FAILED",
            "alert_title": alert_title,
            "farmer_name": data.get("farmer_name", ""),
            "error": "" if "successfully" in alert_title.lower() else alert_title,
            "validation_errors": validation_errors,
        }

        # V2 FIX: Log the result clearly for debugging
        if result["status"] == "FAILED":
            log.warning(
                f"Create FAILED for '{data.get('farmer_name', '?')}': "
                f"alert='{alert_title}', "
                f"pre-submit_errors={validation_errors}"
            )

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
