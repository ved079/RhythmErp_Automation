"""
farmer_page.py
--------------
Page Object Model for RhythmERP Farmer screen.

Location: Registration > Farmer
URL:      /#/dynamic-screens/Farmer/Farmer

FORM LAYOUT (verified 2026-06-12):

  Step 0 — Farmer Details (ALWAYS VISIBLE, top-level):
    1.  Copy From Existing Party   — toggle, key=copy_from_party, optional
    2.  Party Reference            — mat-select, key=party_ref_id, conditional on copy_from_party
    3.  Farmer Name                — text input, key=name, REQUIRED, name='Farmer Name'
    4.  Email                      — text input, key=email_id, optional, name='Email'
    5.  Phone Number               — number input, key=mobile_no, REQUIRED, name='Phone Number'
    6.  Farmer Category            — MULTI-SELECT mat-select, key=farmer_category, REQUIRED
                                      Options: Walk-in Farmer(1592), FPC Member(1593), Borrower Farmer(1594)
    7.  Land Classification        — mat-select, key=land_classification, READONLY
    8.  Password                   — text input, key=password, REQUIRED, name='Password'
    9.  Is Member of This FPC      — toggle, key=is_member_this_fpc
    10. Other FPC Name             — text input, conditional on is_member_this_fpc
    11. Member Id                  — text input, conditional on is_member_this_fpc

  13 Stepper Tabs (appear after Farmer Category is selected):
    Tab 1:  Address Details    — grid rows + cascade + same_as_above
    Tab 2:  Other Details      — Education Qualification, Electricity Availability
    Tab 3:  Family Details     — 14 fields, grid rows
    Tab 4:  Additional Details — DOB/Age/Gender/Religion/Category/Photo (MOVED from Step 0)
    Tab 5:  Land Details       — 11 fields, grid rows
    Tab 6:  Crop Details       — 8 fields, grid rows
    Tab 7:  KYC Details        — 3 fields, grid rows
    Tab 8:  Vehicle Details    — 2 fields, grid rows
    Tab 9:  Income Details     — 3 fields, grid rows
    Tab 10: Bank Details       — 8 fields, grid rows
    Tab 11: Irrigation Details — 2 fields, grid rows
    Tab 12: Award Details      — 2 fields, grid rows
    Tab 13: Loan Details       — 6 fields, grid rows

  Farmer Category determines which stepper tabs are visible:
    Walk-in Farmer  -> subset of tabs (Address, Bank at minimum)
    FPC Member      -> more tabs (Address, Land, Crop, KYC, Bank, etc.)
    Borrower Farmer -> all 13 tabs

KEY RULES (from browser exploration 2026-06-12):
  - NEVER use Keys.ESCAPE (can trigger Angular SPA navigation)
  - JS clicks for Angular Material overlays
  - JS value-setter for ALL dropdown selections
  - Farmer Category is MULTI-SELECT mat-select
  - Address tab uses TABLE/GRID ROWS with cascading dropdowns
  - Both Permanent Address and Current Address rows required
  - Country→State→District→Taluka→Village cascade
  - "Same as Above" checkbox copies Permanent to Current
  - Country MUST ALWAYS be "India" (other countries lack cascading data)
  - Fill ALL upper/visible fields first, THEN scroll down for lower fields
  - Age is READONLY — auto-calculated from Date Of Birth (in Additional Details tab now)
  - Land Classification is READONLY — don't try to fill it
  - Toggle switch uses <app-slide-toggle-v2> component
  - popup-footer class is dynamic — use contains(@class,'popup-footer')
  - SweetAlert2 for success/validation popups
  - Angular Material renders ALL tab contents in DOM; inactive panels have inert="" attribute
  - Dropdown search MUST be scoped to the ACTIVE panel only
  - force_close_form_popup() — 4-step cascade (Cancel → Close(X) → backdrop → nuclear JS)

KNOWN BUGS:
  BUG-F01: No Of Owner required but no asterisk (Land Details)
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
    #  STEPPER TAB INDEX CONSTANTS
    #  (0-based index among stepper tab headers, NOT including Step 0)
    # ==============================================================
    TAB_ADDRESS = 0
    TAB_OTHER = 1
    TAB_FAMILY = 2
    TAB_ADDITIONAL = 3
    TAB_LAND = 4
    TAB_CROP = 5
    TAB_KYC = 6
    TAB_VEHICLE = 7
    TAB_INCOME = 8
    TAB_BANK = 9
    TAB_IRRIGATION = 10
    TAB_AWARD = 11
    TAB_LOAN = 12

    # Maps category names to which tab indices appear
    CATEGORY_TAB_MAP = {
        "Walk-in Farmer": [0, 9],           # Address, Bank
        "FPC Member":     [0, 1, 4, 5, 6, 9],  # Address, Other, Land, Crop, KYC, Bank
        "Borrower Farmer": list(range(13)),  # All 13 tabs
    }

    # Tab display name -> data dict key
    TAB_DATA_MAP = {
        "Address Details":    "address_details",
        "Other Details":      "other_details",
        "Family Details":     "family_details",
        "Additional Details": "additional_details",
        "Land Details":       "land_details",
        "Crop Details":       "crop_details",
        "KYC Details":        "kyc_details",
        "Vehicle Details":    "vehicle_details",
        "Income Details":     "income_details",
        "Bank Details":       "bank_details",
        "Irrigation Details": "irrigation_details",
        "Award Details":      "award_details",
        "Loan Details":       "loan_details",
    }

    # Ordered tab names for Borrower Farmer (all tabs)
    ALL_TAB_NAMES = [
        "Address Details",
        "Other Details",
        "Family Details",
        "Additional Details",
        "Land Details",
        "Crop Details",
        "KYC Details",
        "Vehicle Details",
        "Income Details",
        "Bank Details",
        "Irrigation Details",
        "Award Details",
        "Loan Details",
    ]

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
    #  LOCATORS — Step 0: Farmer Details
    #  Fill order: upper visible fields first, then scroll-down fields
    # ==============================================================
    COPY_FROM_PARTY_TOGGLE = (
        "xpath",
        "//app-slide-toggle-v2[.//span[contains(.,'Copy From Existing Party')]]"
        "//div[contains(@class,'switch-wrapper')]",
    )
    PARTY_REFERENCE_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Party Reference')]"
        "/ancestor::mat-form-field//mat-select",
    )
    FARMER_NAME_INPUT = ("css", "input[name='Farmer Name']")
    EMAIL_INPUT = ("css", "input[name='Email']")
    PHONE_NUMBER_INPUT = ("css", "input[name='Phone Number']")
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
    PASSWORD_INPUT = ("css", "input[name='Password']")
    IS_MEMBER_TOGGLE = (
        "xpath",
        "//app-slide-toggle-v2[.//span[contains(.,'Is Member of This FPC')]]"
        "//div[contains(@class,'switch-wrapper')]",
    )
    OTHER_FPC_NAME_INPUT = ("css", "input[name='Other FPC Name']")
    MEMBER_ID_INPUT = ("css", "input[name='Member Id']")

    # ==============================================================
    #  LOCATORS — Address Details (Tab 1: grid rows + cascade)
    # ==============================================================
    ADDRESS_TABLE = ("css", "app-dynamic-details table, .grid-table")
    PIN_CODE_INPUT = ("css", "input[name='Pin Code']")
    ADDRESS_INPUT = ("css", "input[name='Address']")
    ADDRESS2_INPUT = ("css", "input[name='Address2']")
    SAME_AS_ABOVE_CHECKBOX = (
        "xpath",
        "//mat-checkbox[.//span[contains(.,'Same as Above') or contains(.,'Same as above')]]"
        "//input[@type='checkbox']",
    )
    ADD_ROW_BUTTON = (
        "xpath",
        "//button[contains(.,'Add Row') or contains(@class,'add-row')]",
    )

    # ==============================================================
    #  LOCATORS — Other Details (Tab 2)
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
    #  LOCATORS — Family Details (Tab 3: grid rows)
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
    #  LOCATORS — Additional Details (Tab 4: DOB/Age/Gender/Religion/Category/Photo)
    # ==============================================================
    ADDITIONAL_DOB_INPUT = ("css", "input[placeholder='DD/MM/YYYY']")
    ADDITIONAL_AGE_INPUT = ("css", "input[name='Age']")
    ADDITIONAL_GENDER_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Gender')]"
        "/ancestor::mat-form-field//mat-select",
    )
    ADDITIONAL_RELIGION_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Religion')]"
        "/ancestor::mat-form-field//mat-select",
    )
    ADDITIONAL_CATEGORY_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Category')]"
        "/ancestor::mat-form-field//mat-select",
    )
    ADDITIONAL_PHOTO_UPLOAD_INPUT = ("css", "input[type='file']")

    # ==============================================================
    #  LOCATORS — Land Details (Tab 5: grid rows)
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
    #  LOCATORS — Crop Details (Tab 6: grid rows)
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
    #  LOCATORS — KYC Details (Tab 7: grid rows)
    # ==============================================================
    KYC_DOCUMENT_SELECT = (
        "xpath",
        "//mat-label[contains(.,'KYC Document')]"
        "/ancestor::mat-form-field//mat-select",
    )
    KYC_NUMBER_INPUT = ("css", "input[name='KYC Number']")

    # ==============================================================
    #  LOCATORS — Vehicle Details (Tab 8: grid rows)
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
    #  LOCATORS — Income Details (Tab 9: grid rows)
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
    #  LOCATORS — Bank Details (Tab 10: grid rows)
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
    #  LOCATORS — Irrigation Details (Tab 11: grid rows)
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
    #  LOCATORS — Award Details (Tab 12: grid rows)
    # ==============================================================
    AWARD_NAME_INPUT = ("css", "input[name='Name']")
    AWARD_YEAR_INPUT = ("css", "input[name='Year']")

    # ==============================================================
    #  LOCATORS — Loan Details (Tab 13: grid rows)
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

    def get_page_title(self):
        """Get the browser page title."""
        return self.driver.title

    # ==============================================================
    #  Overlay cleanup — NEVER use Keys.ESCAPE
    # ==============================================================

    def _force_close_panels(self):
        """Remove ALL select overlay panes from the DOM via JS."""
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

    # ==============================================================
    #  Stepper navigation
    # ==============================================================

    def navigate_to_stepper(self, tab_name):
        """Navigate to a specific stepper tab by name. Returns True if reached.

        SPEED FIX: Try quick header click first (fast path for adjacent
        tabs that Angular allows). If that fails, skip straight to
        force-navigate instead of wasting time on Next-button stepping.
        """
        target_lower = tab_name.strip().lower()
        log.info(f"Navigating to stepper tab: {tab_name}")

        # Find the target tab index
        tab_names = self.get_stepper_names()
        target_idx = -1
        for idx, name in enumerate(tab_names):
            if target_lower in name.strip().lower():
                target_idx = idx
                break

        if target_idx < 0:
            log.warning(f"Tab not found in stepper headers: {tab_name}")
            return False

        # Fast path: Check if already on this tab
        current_tab = self.get_current_stepper_name()
        if target_lower in current_tab.lower():
            log.info(f"Already on tab: {tab_name}")
            return True

        # Quick attempt: Direct header click
        if self._click_stepper_header(target_idx):
            self.wait_seconds(0.8)
            active_name = self.get_current_stepper_name()
            if target_lower in active_name.lower():
                log.info(f"Reached tab via header click: {tab_name}")
                return True

        # Force-navigate (always works, ~2 seconds)
        log.info(f"Quick header click failed, force-navigating to tab: {tab_name}")
        if self._force_navigate_to_step(target_idx):
            self.wait_seconds(1.5)
            active_name = self.get_current_stepper_name()
            if target_lower in active_name.lower():
                log.info(f"Force-navigated to tab: {tab_name}")
                return True
            # Even if tab name doesn't match, check if the DOM panel is now active
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
                    log.info(f"Force-navigate succeeded (panel is active): {tab_name}")
                    return True
            except Exception:
                pass

        log.warning(f"Could not navigate to tab: {tab_name}")
        return False

    def navigate_to_stepper_by_index(self, index):
        """Navigate to a stepper tab by 0-based index. Returns True if reached."""
        log.info(f"Navigating to stepper tab index: {index}")

        # Quick attempt: Direct header click
        if self._click_stepper_header(index):
            self.wait_seconds(0.8)
            return True

        # Force-navigate
        if self._force_navigate_to_step(index):
            self.wait_seconds(1.5)
            return True

        return False

    def get_current_stepper_name(self):
        """Get the name of the currently active/selected stepper tab.

        Reads the label text directly from the selected header element
        — no index lookup needed, bypasses the index-alignment bug.
        """
        try:
            headers = self.driver.find_elements(By.CSS_SELECTOR, "mat-step-header")
            for header in headers:
                try:
                    classes = header.get_attribute("class") or ""
                    aria_selected = header.get_attribute("aria-selected") or ""

                    # Check for mat-step-label-selected on inner label
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
                        or has_selected_label
                    )
                    if not is_active:
                        continue

                    # Try .mat-step-text-label first
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

    def get_stepper_names(self):
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

    def _click_stepper_header(self, index):
        """Click on a stepper tab header by index.

        Works even when Next button is frozen (BUG-F02).
        Force-click removes aria-disabled attribute before clicking.
        """
        try:
            result = self.driver.execute_script("""
                var idx = arguments[0];
                var headers = document.querySelectorAll('mat-step-header');
                if (idx >= 0 && idx < headers.length) {
                    var header = headers[idx];
                    header.removeAttribute('aria-disabled');
                    header.classList.remove('mat-step-header-optional');
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

    def _force_navigate_to_step(self, target_index):
        """Force-navigate to a stepper step by directly manipulating
        Angular Material's internal DOM state via JavaScript.

        Bypasses linear mode restrictions, validation blocking,
        and step completion requirements.
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

                var panels = stepper.querySelectorAll(
                    'div[role="tabpanel"].mat-horizontal-stepper-content'
                );
                if (targetIdx < 0 || targetIdx >= panels.length) return false;

                // Update panel states
                for (var i = 0; i < panels.length; i++) {
                    if (i === targetIdx) {
                        panels[i].removeAttribute('inert');
                        panels[i].classList.add(
                            'mat-horizontal-stepper-content-current'
                        );
                        panels[i].classList.remove(
                            'mat-horizontal-stepper-content-previous'
                        );
                    } else {
                        panels[i].setAttribute('inert', '');
                        panels[i].classList.remove(
                            'mat-horizontal-stepper-content-current'
                        );
                        panels[i].classList.add(
                            'mat-horizontal-stepper-content-previous'
                        );
                    }
                }

                // Update step header states
                var headers = stepper.querySelectorAll('mat-step-header');
                for (var i = 0; i < headers.length; i++) {
                    if (i === targetIdx) {
                        headers[i].setAttribute('aria-selected', 'true');
                        headers[i].removeAttribute('aria-disabled');
                        if (!headers[i].classList.contains('mat-step-selected')) {
                            headers[i].classList.add('mat-step-selected');
                        }
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
                        headers[i].classList.remove('mat-step-selected');
                        var innerLabels = headers[i].querySelectorAll(
                            '.mat-step-label, .mat-step-text-label'
                        );
                        for (var l = 0; l < innerLabels.length; l++) {
                            innerLabels[l].classList.remove('mat-step-label-selected');
                            innerLabels[l].classList.remove('mat-step-label-active');
                        }
                    }
                }

                // Update icon states
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

                // Click the target header to trigger Angular's state update
                if (targetIdx < headers.length) {
                    headers[targetIdx].click();
                }

                return true;
            """, target_index)
            return bool(result)
        except Exception as e:
            log.warning(f"Force navigate to step {target_index} failed: {e}")
            return False

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

    # ==============================================================
    #  Step 0: Fill Farmer Details
    #  RULE: Fill upper/visible fields FIRST, then scroll-down fields
    #  Farmer Category MUST be filled LAST (triggers stepper tab creation)
    # ==============================================================

    # Key mapping: API field keys → UI field names used by fill_step0()
    # This allows fill_step0() to accept both API-format keys (name, email_id, mobile_no)
    # and UI-format keys (farmer_name, email, phone_number).
    _STEP0_KEY_MAP = {
        "name":            "farmer_name",
        "email_id":        "email",
        "mobile_no":       "phone_number",
        "party_ref_id":    "party_reference",
    }

    def fill_step0(self, data):
        """Fill all fields on Step 0 — Farmer Details.

        FILL ORDER (business rule):
          1. Copy From Existing Party toggle (if needed)
          2. Party Reference (if copy_from_party is on)
          3. Upper visible text inputs (Farmer Name, Email, Phone Number)
          4. Farmer Category LAST (triggers stepper tab creation)
          5. Password
          6. Is Member of This FPC toggle + conditional fields
        """
        log.info("Filling Step 0: Farmer Details...")

        # Normalize API keys → UI keys so both formats work
        d = {}
        for k, v in data.items():
            d[self._STEP0_KEY_MAP.get(k, k)] = v

        # === 1. Copy From Existing Party toggle ===
        if d.get("copy_from_party"):
            self._toggle_switch(self.COPY_FROM_PARTY_TOGGLE, True)
            self.wait_seconds(0.5)
            # Party Reference — conditional on copy_from_party
            if d.get("party_reference"):
                self._fill_dropdown_if_provided(
                    self.PARTY_REFERENCE_SELECT,
                    d["party_reference"],
                    label_text="Party Reference",
                )

        # === 2. UPPER VISIBLE TEXT INPUTS ===
        if d.get("farmer_name"):
            self._fill_input_by_name_js("Farmer Name", d["farmer_name"])
        if d.get("email"):
            self._fill_input_by_name_js("Email", d["email"])
        if d.get("phone_number"):
            self._fill_input_by_name_js("Phone Number", d["phone_number"])

        # === 3. FARMER CATEGORY — MUST be filled LAST (triggers stepper tab creation) ===
        if d.get("farmer_category"):
            self._select_farmer_category(d["farmer_category"])

        # === 4. Land Classification — READONLY, skip ===
        # (Land Classification is auto-populated, do not attempt to fill)

        # === 5. Password ===
        if d.get("password"):
            self._fill_input_by_name_js("Password", d["password"])

        # === 6. Is Member of This FPC toggle + conditional fields ===
        if "is_member_this_fpc" in d:
            self._toggle_switch(self.IS_MEMBER_TOGGLE, d["is_member_this_fpc"])
            if d["is_member_this_fpc"]:
                self.wait_seconds(0.5)
                if d.get("other_fpc_name"):
                    self._fill_input_by_name_js("Other FPC Name", d["other_fpc_name"])
                if d.get("member_id"):
                    self._fill_input_by_name_js("Member Id", d["member_id"])

        log.info("Step 0 filled successfully")

    # ==============================================================
    #  Internal helpers — Input, Dropdown, Toggle
    # ==============================================================

    def _fill_input_by_name_js(self, field_name, value, scope="popup"):
        """Fill a text input using JS nativeInputValueSetter + dispatchEvent.

        Uses Object.getOwnPropertyDescriptor to set the value, then fires
        'input' and 'change' events with bubbles: true so Angular's
        reactive form model detects the change.

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

                // Try exact name match first, then contains
                var inputs = searchRoot.querySelectorAll('input[name="' + fieldName + '"]');
                if (inputs.length === 0) {
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

    def _fill_dropdown_if_provided(self, locator, value, label_text=None, exclude=None):
        """Fill a mat-select dropdown if a value is provided.

        If value is None, pick a random valid option.
        If value is empty string, skip.
        If value is a string, select that specific option.

        Args:
            locator: Locator tuple for the mat-select element.
            value: Value from data dict (None=random, ''=skip, str=specific).
            label_text: Optional mat-label text for label-based selection.
            exclude: Optional list of option texts to exclude from random.
        """
        if value is None:
            self._select_random_from_dropdown(locator, exclude=exclude)
        elif value == "":
            return
        else:
            if label_text:
                self._select_mat_option_by_label(label_text, value)
            else:
                self._select_mat_option(locator, value)

    def _select_mat_option(self, dropdown_locator, option_text):
        """Select a specific option in a mat-select dropdown using JS click.

        BUG-001 WORKAROUND: After clicking an option, re-find the mat-select
        trigger and dispatch a 'change' event to force Angular's reactive
        form model to register the selection.
        """
        try:
            dropdown = self.find_clickable_element(dropdown_locator, timeout=5)
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", dropdown)
            self.wait_seconds(0.3)
            self.driver.execute_script("arguments[0].click();", dropdown)
            self.wait_seconds(0.8)

            options = self.driver.find_elements(By.CSS_SELECTOR, "div[role='listbox'] mat-option")
            for opt in options:
                try:
                    if opt.text.strip() == option_text and opt.is_displayed():
                        self.driver.execute_script("arguments[0].click();", opt)
                        self.wait_seconds(0.5)
                        self._dispatch_change_event(dropdown_locator)
                        self._close_select_panel()
                        log.info(f"Selected option '{option_text}' (with BUG-001 workaround)")
                        return
                except Exception:
                    continue

            self._close_select_panel()
            log.warning(f"Option '{option_text}' not found in dropdown")
        except Exception as e:
            log.warning(f"Dropdown selection failed: {e}")
            self._close_select_panel()

    def _dispatch_change_event(self, dropdown_locator):
        """BUG-001 WORKAROUND: Re-find the mat-select trigger and fire a
        'change' event with bubbles: true so Angular's reactive form
        model picks up the JS-clicked selection.
        """
        try:
            trigger = self.find_clickable_element(dropdown_locator, timeout=3)
            if trigger:
                self.driver.execute_script("""
                    var el = arguments[0];
                    var trigger = el.tagName === 'MAT-SELECT' ? el : el.querySelector('mat-select');
                    if (trigger) {
                        trigger.dispatchEvent(new Event('change', {bubbles: true}));
                    }
                    el.dispatchEvent(new Event('change', {bubbles: true}));
                """, trigger)
        except Exception as e:
            log.debug(f"BUG-001 dispatchEvent failed (non-critical): {e}")

    def _select_random_from_dropdown(self, dropdown_locator, exclude=None):
        """Select a random valid non-placeholder option from a dropdown.

        Args:
            dropdown_locator: Locator tuple for the mat-select element.
            exclude: Optional list of option texts to skip.
        """
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
                chosen_opt, chosen_text = random.choice(valid_options)
                self.driver.execute_script("arguments[0].click();", chosen_opt)
                self.wait_seconds(0.5)
                self._dispatch_change_event(dropdown_locator)
                log.info(f"Random dropdown option selected: '{chosen_text}'")
            else:
                log.warning("No valid options found in dropdown for random selection")

            self._close_select_panel()
        except Exception as e:
            log.warning(f"Random dropdown selection failed: {e}")
            self._close_select_panel()

    def _select_farmer_category(self, categories):
        """Select farmer category/categories from the MULTI-SELECT dropdown.

        Args:
            categories: A single category string (e.g., "Walk-in Farmer") or
                        a list of category strings for multi-select.
        """
        if isinstance(categories, str):
            categories = [categories]

        try:
            dropdown = self.find_clickable_element(self.FARMER_CATEGORY_SELECT, timeout=5)
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", dropdown)
            self.wait_seconds(0.3)
            self.driver.execute_script("arguments[0].click();", dropdown)
            self.wait_seconds(0.8)

            for cat_text in categories:
                options = self.driver.find_elements(By.CSS_SELECTOR, "div[role='listbox'] mat-option")
                for opt in options:
                    try:
                        if opt.text.strip() == cat_text and opt.is_displayed():
                            self.driver.execute_script("arguments[0].click();", opt)
                            self.wait_seconds(0.5)
                            break
                    except Exception:
                        continue

            self._close_select_panel()
            log.info(f"Farmer Category selected: {categories}")
        except Exception as e:
            log.warning(f"Farmer Category selection failed: {e}")
            self._close_select_panel()

    def _toggle_switch(self, locator, desired_state):
        """Set a toggle switch to the desired state (True=ON, False=OFF).

        Uses multi-strategy _is_toggle_on() for reliable state detection.
        """
        try:
            toggle = self.find_visible_element(locator, timeout=5)
            current_state = self._is_toggle_on(toggle)

            if current_state != desired_state:
                self.driver.execute_script("arguments[0].click();", toggle)
                self.wait_seconds(0.5)
                # Verify the toggle changed
                new_state = self._is_toggle_on(toggle)
                if new_state != desired_state:
                    # Retry with JS direct click on the switch element
                    try:
                        switch = toggle.find_element(
                            By.CSS_SELECTOR, ".switch, .slide-toggle, .mat-slide-toggle-bar"
                        )
                        self.driver.execute_script("arguments[0].click();", switch)
                        self.wait_seconds(0.3)
                    except Exception:
                        pass
                log.info(f"Toggle set to {'ON' if desired_state else 'OFF'}")
        except Exception as e:
            log.warning(f"Toggle switch failed: {e}")

    def _is_toggle_on(self, toggle_element):
        """Multi-strategy check if a toggle switch is currently ON.

        Strategies (in order):
          1. Inner checkbox input — is_selected()
          2. CSS class 'active' on the switch wrapper
          3. CSS class 'checked' or 'mat-checked' on the slide-toggle
          4. aria-checked='true' attribute
          5. Slider position class
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

    def _select_mat_option_by_label(self, label_text, option_text, scope="popup"):
        """Select a mat-select dropdown option by its mat-label text.

        Finds the dropdown by searching for a mat-label containing label_text,
        then clicks the associated mat-select and selects option_text.

        Args:
            label_text: Text to search for in mat-label (e.g., 'Gender').
            option_text: Option text to select (e.g., 'Male').
            scope: 'popup' = search whole popup, 'panel' = active panel only.
        """
        log.info(f"Label-based select: label='{label_text}', option='{option_text}'")
        try:
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

            # Click to open
            self.driver.execute_script("""
                arguments[0].scrollIntoView({block:'center'});
                arguments[0].click();
            """, select_el)
            self.wait_seconds(0.8)

            # Find and click the option
            options = self.driver.find_elements(By.CSS_SELECTOR, "div[role='listbox'] mat-option")
            for opt in options:
                try:
                    if opt.text.strip() == option_text and opt.is_displayed():
                        self.driver.execute_script("arguments[0].click();", opt)
                        self.wait_seconds(0.5)
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

    # ==============================================================
    #  Active panel text input helpers
    # ==============================================================

    def _fill_active_panel_text_input(self, field_name, value):
        """Fill a text input in the ACTIVE stepper panel using JavaScript.

        Scopes to the active panel to avoid matching elements in inert panels.
        Uses nativeInputValueSetter + dispatchEvent for Angular compatibility.
        Includes value verification and send_keys fallback.

        Args:
            field_name: The input's name attribute (e.g., "Member Name", "Pincode")
            value: The text to type into the input
        """
        if not value:
            return

        self._force_close_panels()
        self.wait_seconds(0.2)

        max_retries = 3
        for attempt in range(max_retries):
            try:
                result = self.driver.execute_script("""
                    var fieldName = arguments[0];
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

                    var input = activeContent.querySelector('input[name="' + fieldName + '"]');
                    if (!input) return {success: false, error: 'Input not found: ' + fieldName};

                    input.scrollIntoView({block: 'center'});
                    input.focus();

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

            # send_keys fallback on last retry
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
        characters in their name attribute (e.g., 'No of Childrens\\t').

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

        Scopes to the active panel to avoid matching the Step 0 or other
        datepickers. Finds by placeholder='DD/MM/YYYY' within active panel.

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

    # ==============================================================
    #  Cascading dropdown helpers (Address Details)
    #  PURE JAVASCRIPT — avoids StaleElementReferenceException
    # ==============================================================

    def _fill_cascading_dropdown(self, label_text, value):
        """Fill a cascading dropdown using pure JavaScript (2-phase).

        Phase 1: JS finds the mat-select in the active panel and clicks it
        Phase 2: After Python-side wait, JS finds and clicks the option

        Args:
            label_text: The dropdown label (e.g., "Country", "State")
            value: The option text to select. None = pick first valid option.
                   Empty string = skip this dropdown entirely.
        """
        if value == "":
            return

        max_retries = 5
        for attempt in range(max_retries):
            # Phase 1: Find and click the dropdown
            open_result = self._js_open_cascading_dropdown(label_text)
            if not open_result:
                log.warning(
                    f"Could not open cascading dropdown '{label_text}', "
                    f"retry {attempt + 1}/{max_retries}"
                )
                self._close_select_panel()
                self.wait_seconds(1)
                continue

            self.wait_seconds(1.5)

            # Phase 2: Find and click the option
            select_result = self._js_select_cascading_option(label_text, value)
            if select_result and select_result.get('success'):
                selected_text = select_result.get('selectedText', '?')
                log.info(f"Address '{label_text}' selected: {selected_text}")
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

        Runs entirely within a single JS execution context — NO window for
        Angular to re-render the element between finding and clicking.
        """
        try:
            result = self.driver.execute_script("""
                var labelText = arguments[0];

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

                select.scrollIntoView({block: 'center'});
                select.click();

                return {success: true};
            """, label_text)
            return result and result.get('success')
        except Exception as e:
            log.warning(f"JS open cascading dropdown failed for '{label_text}': {e}")
            return False

    def _js_select_cascading_option(self, label_text, value):
        """Phase 2: Find and click an option in the open overlay panel via pure JS.

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
                    var backdrops = document.querySelectorAll(
                        '.cdk-overlay-backdrop:not(.cdk-overlay-dark-backdrop)'
                    );
                    for (var b = 0; b < backdrops.length; b++) {
                        try { backdrops[b].click(); } catch(e) {}
                    }
                    return {
                        success: false,
                        error: 'Option not found for: ' + labelText
                    };
                }

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
    #  Angular stability & scrolling helpers
    # ==============================================================

    def _wait_for_angular_stable(self, timeout=10):
        """Wait for Angular to finish rendering and HTTP requests to complete.

        Uses a polling approach: checks for loading indicators in mat-select
        elements. Falls back to a simple fixed wait if JS check fails.
        """
        deadline = time.time() + timeout
        stable_count = 0
        required_stable = 2

        while time.time() < deadline:
            try:
                is_stable = self.driver.execute_script("""
                    var popup = document.querySelector('.big-model, mat-dialog-container');
                    if (!popup) return true;

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

                        var selects = activeContent.querySelectorAll('mat-select');
                        for (var i = 0; i < selects.length; i++) {
                            if (selects[i].offsetParent === null) {
                                continue;
                            }
                            var trigger = selects[i].querySelector(
                                '.mat-select-trigger, .mat-mdc-select-trigger'
                            );
                            if (!trigger) {
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
                self.wait_seconds(2)
                return

            self.wait_seconds(0.5)

        log.debug("Angular stability wait timed out, proceeding anyway")

    def _scroll_popup_to_top(self):
        """Scroll the popup/dialog container to the top."""
        self.driver.execute_script("""
            var popup = document.querySelector('.big-model, mat-dialog-container, .cdk-dialog-container');
            if (popup) {
                popup.scrollTop = 0;
                var scrollables = popup.querySelectorAll('[style*="overflow"], .mat-stepper-content, .cdk-step-content');
                for (var i = 0; i < scrollables.length; i++) {
                    scrollables[i].scrollTop = 0;
                }
            }
        """)
        self.wait_seconds(0.3)

    def _scroll_popup_to_bottom(self):
        """Scroll the popup/dialog container to the bottom."""
        self.driver.execute_script("""
            var popup = document.querySelector('.big-model, mat-dialog-container, .cdk-dialog-container');
            if (popup) {
                popup.scrollTop = popup.scrollHeight;
                var scrollables = popup.querySelectorAll('[style*="overflow"], .mat-stepper-content, .cdk-step-content');
                for (var i = 0; i < scrollables.length; i++) {
                    scrollables[i].scrollTop = scrollables[i].scrollHeight;
                }
            }
        """)
        self.wait_seconds(0.3)

    def _scroll_popup_to_element(self, locator):
        """Scroll the popup container so that the target element is visible."""
        try:
            element = self.find_element(locator)
            self.driver.execute_script("""
                var el = arguments[0];
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
                el.scrollIntoView({block: 'center', behavior: 'smooth'});
            """, element)
            self.wait_seconds(0.3)
        except Exception as e:
            log.warning(f"Scroll to element failed: {e}")

    # ==============================================================
    #  Tab 1: Address Details — grid rows + cascade + same_as_above
    #  Both Permanent Address and Current Address rows required.
    #  Country→State→District→Taluka→Village cascade.
    #  "Same as Above" checkbox copies Permanent to Current.
    # ==============================================================

    def fill_address_details(self, data):
        """Fill the Address Details stepper tab.

        The Address tab has a grid with two rows:
          - Row 0: Permanent Address
          - Row 1: Current Address

        Both rows require Country→State→District→Taluka→Village cascade.
        Country is ALWAYS forced to "India".
        If data contains "same_as_above" = True, check the "Same as Above"
        checkbox to auto-copy Permanent Address to Current Address.

        FILL ORDER:
          1. Fill Permanent Address row (row 0)
          2. Check "Same as Above" if requested (skips Current Address)
          3. Fill Current Address row (row 1) if not same-as-above
        """
        log.info("Filling Address Details tab...")

        self.wait_seconds(1.5)
        self._scroll_popup_to_top()
        self.wait_seconds(0.3)

        # Fill Permanent Address (row 0)
        perm_data = data.get("permanent_address", data)
        self._fill_address_row(perm_data, row_index=0, is_permanent=True)

        # Check "Same as Above" if requested
        same_as_above = data.get("same_as_above", False)
        if same_as_above:
            self._check_same_as_above()
            log.info("Same as Above checked — skipping Current Address fill")
            log.info("Address Details filled")
            return

        # Add row for Current Address if it doesn't exist
        # (The grid may auto-create both rows, or we may need to add)
        current_row_count = self.get_grid_row_count("Address Details")
        if current_row_count < 2:
            self.add_grid_row("Address Details")
            self.wait_seconds(1)

        # Fill Current Address (row 1)
        curr_data = data.get("current_address", data)
        self._fill_address_row(curr_data, row_index=1, is_permanent=False)

        log.info("Address Details filled")

    def _fill_address_row(self, data, row_index=0, is_permanent=True):
        """Fill a single address grid row with cascading dropdowns.

        FILL ORDER:
          1. Upper visible dropdowns: Country -> State -> District
          2. Scroll-down dropdowns: Taluka -> Village
          3. Scroll-down text inputs: Pin Code -> Address -> Address2

        Country is ALWAYS forced to "India".
        """
        addr_type = 'Permanent' if is_permanent else 'Current'
        log.info(f"Filling {addr_type} Address (row {row_index})...")

        self.wait_seconds(1)

        # === 1. UPPER VISIBLE DROPDOWNS ===
        # Country — ALWAYS "India"
        self.select_country("India", row_index=row_index)

        # Wait for Angular to fetch states after Country selection
        log.info("Waiting for Angular to stabilize after Country selection...")
        self._wait_for_angular_stable(timeout=8)
        self.wait_seconds(1)

        # State
        state_val = data.get("perm_state") if is_permanent else data.get("state")
        if not state_val:
            state_val = data.get("state")
        self.select_state(state_val, row_index=row_index)

        self._wait_for_angular_stable(timeout=5)
        self.wait_seconds(0.5)

        # District
        district_val = data.get("perm_district") if is_permanent else data.get("district")
        if not district_val:
            district_val = data.get("district")
        self.select_district(district_val, row_index=row_index)

        self._wait_for_angular_stable(timeout=5)
        self.wait_seconds(0.5)

        # === 2. SCROLL-DOWN DROPDOWNS ===
        taluka_val = data.get("perm_taluka") if is_permanent else data.get("taluka")
        if not taluka_val:
            taluka_val = data.get("taluka")
        self.select_taluka(taluka_val, row_index=row_index)

        self._wait_for_angular_stable(timeout=5)
        self.wait_seconds(0.5)

        village_val = data.get("perm_village") if is_permanent else data.get("village")
        if not village_val:
            village_val = data.get("village")
        self.select_village(village_val, row_index=row_index)

        # === 3. SCROLL-DOWN TEXT INPUTS ===
        self._force_close_panels()
        self.wait_seconds(0.5)
        self._scroll_popup_to_bottom()
        self.wait_seconds(0.3)

        pin_code_val = data.get("perm_pin_code") if is_permanent else data.get("pin_code")
        if not pin_code_val:
            pin_code_val = data.get("pin_code")
        if pin_code_val:
            self._fill_active_panel_text_input("Pin Code", pin_code_val)

        address_val = data.get("perm_address") if is_permanent else data.get("address")
        if not address_val:
            address_val = data.get("address")
        if address_val:
            self._fill_active_panel_text_input("Address", address_val)

        address2_val = data.get("perm_address2") if is_permanent else data.get("address2")
        if not address2_val:
            address2_val = data.get("address2")
        if address2_val:
            self._fill_active_panel_text_input("Address2", address2_val)

        log.info(f"{addr_type} Address filled (row {row_index})")

    def _check_same_as_above(self):
        """Check the 'Same as Above' checkbox to copy Permanent to Current."""
        try:
            checkbox = self.driver.find_element(By.CSS_SELECTOR, "mat-checkbox")
            # Find the right checkbox
            checkboxes = self.driver.find_elements(
                By.XPATH,
                "//mat-checkbox[.//span[contains(.,'Same as Above') or contains(.,'Same as above')]]"
            )
            for cb in checkboxes:
                try:
                    if cb.is_displayed():
                        inner_input = cb.find_element(By.CSS_SELECTOR, "input[type='checkbox']")
                        if not inner_input.is_selected():
                            self.driver.execute_script("arguments[0].click();", inner_input)
                            self.wait_seconds(0.5)
                            log.info("'Same as Above' checkbox checked")
                            return
                except Exception:
                    continue
        except Exception as e:
            log.warning(f"Could not check 'Same as Above' checkbox: {e}")

    # ==============================================================
    #  Dropdown Cascade (Address) — public API
    # ==============================================================

    def select_country(self, value="India", row_index=0):
        """Select Country in the address row. Default is always "India"."""
        self._fill_cascading_dropdown("Country", value or "India")

    def select_state(self, value=None, row_index=0):
        """Select State in the address row. None = pick first valid option."""
        self._fill_cascading_dropdown("State", value)

    def select_district(self, value=None, row_index=0):
        """Select District in the address row. None = pick first valid option."""
        self._fill_cascading_dropdown("District", value)

    def select_taluka(self, value=None, row_index=0):
        """Select Taluka in the address row. None = pick first valid option."""
        self._fill_cascading_dropdown("Taluka", value)

    def select_village(self, value=None, row_index=0):
        """Select Village in the address row. None = pick first valid option."""
        self._fill_cascading_dropdown("Village", value)

    # ==============================================================
    #  Tab 2: Other Details
    # ==============================================================

    def fill_other_details(self, data):
        """Fill the Other Details tab (Education Qualification, Electricity Availability)."""
        log.info("Filling Other Details...")

        self._fill_dropdown_if_provided(
            self.EDUCATION_QUALIFICATION_SELECT,
            data.get("education_qualification"),
            label_text="Education Qualification",
        )
        self._fill_dropdown_if_provided(
            self.ELECTRICITY_AVAILABILITY_SELECT,
            data.get("electricity_availability"),
            label_text="Electricity Availability",
        )

        log.info("Other Details filled")

    # ==============================================================
    #  Tab 3: Family Details — grid rows (14 fields)
    # ==============================================================

    def fill_family_details(self, data):
        """Fill the Family Details tab (grid rows).

        14 fields: Member Name, Phone Number, Date Of Birth, Age,
        Gender, Education, Relationship, Is Staying, Pincode, Address,
        Marital Status, No of Children, Annual Income, Off Farm Income.
        """
        log.info("Filling Family Details...")

        if data.get("member_name"):
            self._fill_active_panel_text_input("Member Name", data["member_name"])
        if data.get("family_phone_number"):
            self._fill_active_panel_text_input("Phone Number", data["family_phone_number"])

        # Date Of Birth — must scope to active panel's datepicker
        if data.get("family_dob"):
            self._fill_active_panel_date_input(data["family_dob"])

        # Age is READONLY — auto-calculated from DOB, skip

        # Dropdowns
        self._fill_dropdown_if_provided(self.FAMILY_GENDER_SELECT, data.get("family_gender"))
        self._fill_dropdown_if_provided(
            self.EDUCATION_OF_FARMER_FAMILY_SELECT,
            data.get("education_of_farmer_family"),
        )
        self._fill_dropdown_if_provided(self.RELATIONSHIP_SELECT, data.get("relationship"))

        # Pincode — name='Pincode' (not 'Pin Code' like address tabs)
        if data.get("family_pincode"):
            self._fill_active_panel_text_input("Pincode", data["family_pincode"])

        # Address
        if data.get("family_address"):
            self._fill_active_panel_text_input("Address", data["family_address"])

        # More dropdowns
        self._fill_dropdown_if_provided(self.MARITAL_STATUS_SELECT, data.get("marital_status"))

        # No of Childrens — name attr has trailing TAB char
        if data.get("no_of_childrens"):
            self._fill_active_panel_text_input_contains("No of Childrens", data["no_of_childrens"])

        self._fill_dropdown_if_provided(
            self.MEMBER_ANNUAL_INCOME_SELECT,
            data.get("member_annual_income"),
        )

        # Off Farm Income
        if data.get("off_farm_income"):
            self._fill_active_panel_text_input("Off Farm Income", data["off_farm_income"])

        log.info("Family Details filled")

    # ==============================================================
    #  Tab 4: Additional Details — DOB/Age/Gender/Religion/Category/Photo
    #  (MOVED from Step 0 to this tab)
    # ==============================================================

    def fill_additional_details(self, data):
        """Fill the Additional Details tab.

        Fields: Date Of Birth (datepicker), Age (readonly from DOB),
        Gender (dropdown), Religion (dropdown), Category (dropdown),
        Profile Photo (file upload).

        Age is READONLY — auto-calculated from Date Of Birth.
        """
        log.info("Filling Additional Details...")

        # Date Of Birth — datepicker in this tab
        if data.get("date_of_birth"):
            self._fill_active_panel_date_input(data["date_of_birth"])

        # Age is READONLY — auto-calculated from DOB, do not fill

        # Dropdowns
        if data.get("gender"):
            self._fill_dropdown_if_provided(
                self.ADDITIONAL_GENDER_SELECT,
                data["gender"],
                label_text="Gender",
            )
        if data.get("religion"):
            self._fill_dropdown_if_provided(
                self.ADDITIONAL_RELIGION_SELECT,
                data["religion"],
                label_text="Religion",
            )
        if data.get("category"):
            self._fill_dropdown_if_provided(
                self.ADDITIONAL_CATEGORY_SELECT,
                data["category"],
                label_text="Category",
            )

        # Profile Photo — file upload
        if data.get("profile_photo"):
            try:
                file_input = self.driver.find_element(By.CSS_SELECTOR, "input[type='file']")
                file_input.send_keys(data["profile_photo"])
                self.wait_seconds(0.5)
                log.info("Profile photo uploaded")
            except Exception as e:
                log.warning(f"Profile photo upload failed: {e}")

        log.info("Additional Details filled")

    # ==============================================================
    #  Tab 5: Land Details — grid rows (11 fields)
    # ==============================================================

    def fill_land_details(self, data):
        """Fill the Land Details tab.

        Fields: Farm Name, Land Attachment, No Of Owner (REQUIRED but no
        asterisk — BUG-F01), Total Land, Individual Land, Gat Number,
        Cultivation Land, Land ownership, Latitude, Longitude.

        NOTE: Number field name attrs may have trailing TAB chars.
        """
        log.info("Filling Land Details...")

        if data.get("farm_name"):
            self._fill_active_panel_text_input("Farm Name", data["farm_name"])
        # No Of Owner — BUG-F01: required but no asterisk
        if data.get("no_of_owner"):
            self._fill_active_panel_text_input_contains("No Of Owner", data["no_of_owner"])
        if data.get("total_land_on_document"):
            self._fill_active_panel_text_input_contains(
                "Total Land On Document", data["total_land_on_document"]
            )
        if data.get("individual_land_holding"):
            self._fill_active_panel_text_input_contains(
                "Individual Land Holding", data["individual_land_holding"]
            )
        if data.get("gat_number"):
            self._fill_active_panel_text_input_contains("Gat Number", data["gat_number"])

        # Land Attachment — file upload (skip for now, complex)
        if data.get("land_attachment"):
            try:
                file_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
                if file_inputs:
                    file_inputs[0].send_keys(data["land_attachment"])
            except Exception as e:
                log.warning(f"Land attachment upload failed: {e}")

        if data.get("total_land_in_hectare"):
            self._fill_active_panel_text_input_contains(
                "Total Land In hectare", data["total_land_in_hectare"]
            )
        if data.get("total_cultivation_land_hectare"):
            self._fill_active_panel_text_input_contains(
                "Total Cultivation Land In hectare", data["total_cultivation_land_hectare"]
            )

        # Dropdown
        self._fill_dropdown_if_provided(
            self.LAND_OWNERSHIP_SELECT, data.get("land_ownership")
        )

        # Bottom text inputs
        if data.get("latitude"):
            self._fill_active_panel_text_input("Latitude(Lat)", data["latitude"])
        if data.get("longitude"):
            self._fill_active_panel_text_input("Longitude(Log)", data["longitude"])

        log.info("Land Details filled")

    # ==============================================================
    #  Tab 6: Crop Details — grid rows (8 fields)
    # ==============================================================

    def fill_crop_details(self, data):
        """Fill the Crop Details tab.

        Fields: Farm Name, Crop (150 options), Season, Cultivation Land,
        Expected Yield, Actual Produce, Document Attachment.
        """
        log.info("Filling Crop Details...")

        if data.get("crop_farm_name"):
            self._fill_active_panel_text_input("Farm Name", data["crop_farm_name"])
        self._fill_dropdown_if_provided(self.CROP_SELECT, data.get("crop"))
        self._fill_dropdown_if_provided(self.SEASON_SELECT, data.get("season"))
        if data.get("cultivation_land_hectare"):
            self._fill_active_panel_text_input_contains(
                "Cultivation Land In hectare", data["cultivation_land_hectare"]
            )
        if data.get("expected_yield_projection"):
            self._fill_active_panel_text_input_contains(
                "Expected Yield projection", data["expected_yield_projection"]
            )
        if data.get("actual_produce"):
            self._fill_active_panel_text_input_contains(
                "Actual Produce", data["actual_produce"]
            )

        # Document Attachment — file upload (skip for now)
        if data.get("document_attachment"):
            try:
                file_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
                if file_inputs:
                    file_inputs[0].send_keys(data["document_attachment"])
            except Exception as e:
                log.warning(f"Document attachment upload failed: {e}")

        log.info("Crop Details filled")

    # ==============================================================
    #  Tab 7: KYC Details — grid rows (3 fields)
    # ==============================================================

    def fill_kyc_details(self, data):
        """Fill the KYC Details tab.

        Fields: KYC Document (AADHAR/PAN), KYC Number, KYC Attachment.
        """
        log.info("Filling KYC Details...")

        self._fill_dropdown_if_provided(self.KYC_DOCUMENT_SELECT, data.get("kyc_document"))
        if data.get("kyc_number"):
            self._fill_active_panel_text_input("KYC Number", data["kyc_number"])

        # KYC Attachment — file upload
        if data.get("kyc_attachment"):
            try:
                file_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
                if file_inputs:
                    file_inputs[0].send_keys(data["kyc_attachment"])
            except Exception as e:
                log.warning(f"KYC attachment upload failed: {e}")

        log.info("KYC Details filled")

    # ==============================================================
    #  Tab 8: Vehicle Details — grid rows (2 fields)
    # ==============================================================

    def fill_vehicle_details(self, data):
        """Fill the Vehicle Details tab.

        Fields: Vehicle Type, Vehicle Name (no options).
        """
        log.info("Filling Vehicle Details...")

        self._fill_dropdown_if_provided(self.VEHICLE_TYPE_SELECT, data.get("vehicle_type"))
        self._fill_dropdown_if_provided(self.VEHICLE_NAME_SELECT, data.get("vehicle_name"))

        log.info("Vehicle Details filled")

    # ==============================================================
    #  Tab 9: Income Details — grid rows (3 fields)
    # ==============================================================

    def fill_income_details(self, data):
        """Fill the Income Details tab.

        Fields: Source of Income, Income Bracket, Exact Amount.
        NOTE: Exact Amount accepts 0 and . prefix (BUG-F06).
        """
        log.info("Filling Income Details...")

        self._fill_dropdown_if_provided(self.SOURCE_OF_INCOME_SELECT, data.get("source_of_income"))
        self._fill_dropdown_if_provided(self.INCOME_BRACKET_SELECT, data.get("income_bracket"))
        if data.get("exact_amount"):
            self._fill_active_panel_text_input("Exact Amount", data["exact_amount"])

        log.info("Income Details filled")

    # ==============================================================
    #  Tab 10: Bank Details — grid rows (8 fields)
    # ==============================================================

    def fill_bank_details(self, data):
        """Fill the Bank Details tab.

        Fields: Bank Name, Branch, IFSC Code, Account Type,
        Account Holder Name, Account Number, Bank Proof, Attachment.
        """
        log.info("Filling Bank Details...")

        self.wait_seconds(1)

        # Upper visible text inputs
        if data.get("bank_name"):
            self._fill_active_panel_text_input("Bank Name", data["bank_name"])
        if data.get("branch"):
            self._fill_active_panel_text_input("Branch", data["branch"])
        if data.get("ifsc_code"):
            self._fill_active_panel_text_input("IFSC Code", data["ifsc_code"])

        # Dropdowns
        self._fill_dropdown_if_provided(self.ACCOUNT_TYPE_SELECT, data.get("account_type"))

        # Lower text inputs
        if data.get("account_holder_name"):
            self._fill_active_panel_text_input(
                "Account Holder Name", data["account_holder_name"]
            )
        if data.get("account_number"):
            self._fill_active_panel_text_input("Account Number", data["account_number"])

        # More dropdowns
        self._fill_dropdown_if_provided(self.BANK_PROOF_SELECT, data.get("bank_proof"))

        # Attachment — file upload
        if data.get("bank_attachment"):
            try:
                file_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
                if file_inputs:
                    file_inputs[0].send_keys(data["bank_attachment"])
            except Exception as e:
                log.warning(f"Bank attachment upload failed: {e}")

        log.info("Bank Details filled")

    # ==============================================================
    #  Tab 11: Irrigation Details — grid rows (2 fields)
    # ==============================================================

    def fill_irrigation_details(self, data):
        """Fill the Irrigation Details tab.

        Fields: Source of Irrigation, Method of Irrigation.
        """
        log.info("Filling Irrigation Details...")

        self._fill_dropdown_if_provided(
            self.SOURCE_OF_IRRIGATION_SELECT, data.get("source_of_irrigation")
        )
        self._fill_dropdown_if_provided(
            self.METHOD_OF_IRRIGATION_SELECT, data.get("method_of_irrigation")
        )

        log.info("Irrigation Details filled")

    # ==============================================================
    #  Tab 12: Award Details — grid rows (2 fields)
    # ==============================================================

    def fill_award_details(self, data):
        """Fill the Award Details tab.

        Fields: Name, Year.
        NOTE: 'Name' is a common field name — panel-scoping prevents
        matching the wrong element in an inert panel.
        """
        log.info("Filling Award Details...")

        if data.get("award_name"):
            self._fill_active_panel_text_input("Name", data["award_name"])
        if data.get("award_year"):
            self._fill_active_panel_text_input("Year", data["award_year"])

        log.info("Award Details filled")

    # ==============================================================
    #  Tab 13: Loan Details — grid rows (6 fields)
    # ==============================================================

    def fill_loan_details(self, data):
        """Fill the Loan Details tab.

        Fields: Loan Name, Facility Type, Purpose, Availed From (date),
        Sanctioned Amount, Present Outstanding.
        NOTE: Sanctioned Amount & Present Outstanding accept 0/. prefix (BUG-F06).
        """
        log.info("Filling Loan Details...")

        if data.get("loan_name"):
            self._fill_active_panel_text_input("Loan Name", data["loan_name"])
        self._fill_dropdown_if_provided(self.FACILITY_TYPE_SELECT, data.get("facility_type"))
        if data.get("purpose_of_loan"):
            self._fill_active_panel_text_input_contains("Purpose Of Loan", data["purpose_of_loan"])
        if data.get("availed_from_date"):
            self._fill_active_panel_date_input(data["availed_from_date"])
        if data.get("sanctioned_amount"):
            self._fill_active_panel_text_input_contains(
                "Sanctioned Amount", data["sanctioned_amount"]
            )
        if data.get("present_outstanding_amount"):
            self._fill_active_panel_text_input_contains(
                "Present Outstanding Amount", data["present_outstanding_amount"]
            )

        log.info("Loan Details filled")

    # ==============================================================
    #  Fill routing — tab name -> fill method
    # ==============================================================

    def fill_tab_by_name(self, tab_name, data):
        """Fill the currently active tab based on its name.
        Delegates to the appropriate fill method.
        """
        tab_lower = tab_name.strip().lower()

        if "address" in tab_lower:
            self.fill_address_details(data)
        elif "other" in tab_lower:
            self.fill_other_details(data)
        elif "family" in tab_lower:
            self.fill_family_details(data)
        elif "additional" in tab_lower:
            self.fill_additional_details(data)
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
    #  Grid Row Management
    # ==============================================================

    def add_grid_row(self, stepper_name):
        """Add a new row in the grid of the specified stepper tab.

        Navigates to the tab first, then clicks the 'Add Row' button.
        """
        log.info(f"Adding grid row in: {stepper_name}")
        # Ensure we're on the correct tab
        self.navigate_to_stepper(stepper_name)
        self.wait_seconds(0.5)

        try:
            add_btns = self.driver.find_elements(
                By.XPATH,
                "//button[contains(.,'Add Row') or contains(@class,'add-row')]"
            )
            for btn in add_btns:
                try:
                    if btn.is_displayed():
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({block:'center'});"
                            "arguments[0].click();", btn
                        )
                        self.wait_seconds(1)
                        log.info(f"Grid row added in: {stepper_name}")
                        return
                except Exception:
                    continue
        except Exception:
            pass

        # Fallback: JS click
        try:
            self.driver.execute_script("""
                var popup = document.querySelector('.big-model, mat-dialog-container');
                if (!popup) return;
                var activeContent = popup.querySelector(
                    'div.mat-horizontal-stepper-content-current'
                );
                if (!activeContent) return;
                var btns = activeContent.querySelectorAll('button');
                for (var i = 0; i < btns.length; i++) {
                    if (btns[i].textContent.trim() === 'Add Row') {
                        btns[i].click();
                        break;
                    }
                }
            """)
            self.wait_seconds(1)
        except Exception as e:
            log.warning(f"Add grid row failed: {e}")

    def remove_grid_row(self, stepper_name, row_index=0):
        """Remove a grid row in the specified stepper tab.

        Args:
            stepper_name: Name of the stepper tab
            row_index: 0-based index of the row to remove
        """
        log.info(f"Removing grid row {row_index} in: {stepper_name}")
        self.navigate_to_stepper(stepper_name)
        self.wait_seconds(0.5)

        try:
            # Find delete/remove buttons in the active panel
            result = self.driver.execute_script("""
                var targetRow = arguments[0];
                var popup = document.querySelector('.big-model, mat-dialog-container');
                if (!popup) return false;
                var activeContent = popup.querySelector(
                    'div.mat-horizontal-stepper-content-current'
                );
                if (!activeContent) return false;
                var rows = activeContent.querySelectorAll('tr, .grid-row');
                if (targetRow >= 0 && targetRow < rows.length) {
                    var deleteBtn = rows[targetRow].querySelector(
                        'button[title="Delete"], button[title="Remove"], ' +
                        'button.delete-btn, button.remove-btn, ' +
                        'button[mattooltip="Delete"], button[mattooltip="Remove"]'
                    );
                    if (deleteBtn) {
                        deleteBtn.click();
                        return true;
                    }
                }
                return false;
            """, row_index)
            if result:
                self.wait_seconds(0.5)
                log.info(f"Grid row {row_index} removed in: {stepper_name}")
        except Exception as e:
            log.warning(f"Remove grid row failed: {e}")

    def get_grid_row_count(self, stepper_name):
        """Get the number of grid rows in the specified stepper tab.

        Args:
            stepper_name: Name of the stepper tab

        Returns:
            Number of data rows (excluding header rows)
        """
        try:
            result = self.driver.execute_script("""
                var popup = document.querySelector('.big-model, mat-dialog-container');
                if (!popup) return 0;
                var activeContent = popup.querySelector(
                    'div.mat-horizontal-stepper-content-current'
                );
                if (!activeContent) return 0;
                var tables = activeContent.querySelectorAll('table, .grid-table');
                if (tables.length === 0) return 0;
                // Count tbody rows (data rows), excluding header
                var rows = tables[0].querySelectorAll('tbody tr');
                return rows.length;
            """)
            return result or 0
        except Exception:
            return 0

    # ==============================================================
    #  Submit / Cancel / Close
    # ==============================================================

    def submit_form(self):
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

    def cancel(self):
        """Click Cancel button."""
        try:
            btn = self.find_clickable_element(self.CANCEL_BUTTON, timeout=5)
            if btn:
                self.driver.execute_script("arguments[0].click();", btn)
                self.wait_seconds(1)
        except Exception:
            pass

    def force_close_form_popup(self):
        """Force close any open popup via 4-step cascade:
        1. Cancel button
        2. Close(X) button
        3. Backdrop click
        4. Nuclear JS removal
        """
        # Step 1: Cancel
        try:
            btns = self.driver.find_elements(
                By.XPATH,
                "//div[contains(@class,'popup-footer')]//button[contains(.,'Cancel')]"
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

        # Step 2: Close(X) button
        try:
            close_btns = self.driver.find_elements(
                By.CSS_SELECTOR,
                ".big-model button.close, .big-model button[aria-label='Close']"
            )
            for btn in close_btns:
                try:
                    if btn.is_displayed():
                        self.driver.execute_script("arguments[0].click();", btn)
                        self.wait_seconds(0.5)
                        return
                except Exception:
                    continue
        except Exception:
            pass

        # Step 3: Backdrop click
        try:
            backdrops = self.driver.find_elements(
                By.CSS_SELECTOR, ".cdk-overlay-backdrop.cdk-overlay-dark-backdrop"
            )
            for bd in backdrops:
                try:
                    if bd.is_displayed():
                        bd.click()
                        self.wait_seconds(0.5)
                        return
                except Exception:
                    continue
        except Exception:
            pass

        # Step 4: Nuclear JS removal
        try:
            self.driver.execute_script("""
                document.querySelectorAll('mat-dialog-container').forEach(function(el) { el.remove(); });
                document.querySelectorAll('.cdk-overlay-backdrop').forEach(function(el) { el.remove(); });
                document.querySelectorAll('.cdk-overlay-pane').forEach(function(el) { el.remove(); });
            """)
            self.wait_seconds(0.5)
        except Exception:
            pass

    # ==============================================================
    #  SweetAlert2 handling
    # ==============================================================

    def is_success_alert_visible(self):
        """Check if a SweetAlert2 success alert is showing."""
        try:
            container = self.driver.find_element(By.CSS_SELECTOR, ".swal2-container")
            title = self.driver.find_element(By.CSS_SELECTOR, "#swal2-title")
            return container.is_displayed() and "success" in (title.text or "").lower()
        except Exception:
            return False

    def is_validation_alert_visible(self):
        """Check if a SweetAlert2 validation alert is showing."""
        try:
            container = self.driver.find_element(By.CSS_SELECTOR, ".swal2-container")
            return container.is_displayed()
        except Exception:
            return False

    def get_alert_title(self):
        """Get the title text of the SweetAlert2 alert."""
        try:
            title = self.driver.find_element(By.CSS_SELECTOR, "#swal2-title")
            return title.text.strip()
        except Exception:
            try:
                container = self.driver.find_element(By.CSS_SELECTOR, ".swal2-container")
                return container.text.strip()
            except Exception:
                return ""

    def dismiss_alert(self):
        """Dismiss a SweetAlert2 alert by clicking the confirm button."""
        try:
            self._swal2_confirm_click()
            self.wait_seconds(0.5)
        except Exception:
            pass

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

    def handle_success_alert(self, timeout=30):
        """Handle SweetAlert2 success alert. Returns alert title text.

        Also checks for inline validation errors when no SweetAlert appears.
        """
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, ".swal2-container"))
            )
            self.wait_seconds(1)
        except (TimeoutException, InvalidSessionIdException):
            # No SweetAlert — check for inline validation errors
            inline_errors = self.get_mat_error_text()
            if inline_errors:
                error_summary = "; ".join(inline_errors[:5])
                log.warning(f"No SweetAlert, but inline validation errors found: {error_summary}")
                return f"VALIDATION_ERRORS: {error_summary}"
            log.warning("No SweetAlert2 alert appeared (timeout or session died)")
            return ""

        # Try to read the title
        try:
            title = self.driver.find_element(By.CSS_SELECTOR, "#swal2-title").text.strip()
        except Exception:
            try:
                container = self.driver.find_element(By.CSS_SELECTOR, ".swal2-container")
                title = container.text.strip()
            except Exception:
                title = ""

        # Try to click confirm button
        try:
            self._swal2_confirm_click()
            self.wait_seconds(1)
        except Exception:
            pass

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

    # ==============================================================
    #  Validation errors
    # ==============================================================

    def get_mat_error_text(self):
        """Get all visible mat-error texts."""
        errors = []
        try:
            error_elements = self.driver.find_elements(
                By.CSS_SELECTOR, "mat-error, .mat-mdc-form-field-error"
            )
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

    def get_table_row_count(self):
        """Get the number of data rows in the main listing table."""
        try:
            rows = self.driver.find_elements(
                By.CSS_SELECTOR, "table#excel-table tbody tr"
            )
            # Filter out no-data rows
            count = 0
            for row in rows:
                try:
                    cells = row.find_elements(By.CSS_SELECTOR, "td")
                    has_data = any(cell.text.strip() for cell in cells)
                    no_data_classes = row.get_attribute("class") or ""
                    if has_data and "no-data" not in no_data_classes and "mat-mdc-no-data-row" not in no_data_classes:
                        count += 1
                except Exception:
                    continue
            return count
        except Exception:
            return 0

    def get_table_row_data(self, row_index):
        """Get cell data from a specific table row.

        Args:
            row_index: 0-based index of the row

        Returns:
            Dict mapping column names to cell values, or empty dict.
        """
        try:
            rows = self.driver.find_elements(
                By.CSS_SELECTOR, "table#excel-table tbody tr"
            )
            if row_index >= len(rows):
                log.warning(f"Row index {row_index} out of range ({len(rows)} rows)")
                return {}

            row = rows[row_index]
            cells = row.find_elements(By.CSS_SELECTOR, "td")

            # Get header column names
            headers = self.driver.find_elements(
                By.CSS_SELECTOR, "table#excel-table thead th"
            )
            col_names = [h.text.strip() for h in headers]

            data = {}
            for i, cell in enumerate(cells):
                try:
                    col_name = col_names[i] if i < len(col_names) else f"col_{i}"
                    data[col_name] = cell.text.strip()
                except Exception:
                    continue
            return data
        except Exception:
            return {}

    def search_farmer(self, search_text):
        """Search for a farmer using the search input."""
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

            # Try multiple search input selectors
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
                try:
                    all_inputs = self.driver.find_elements(
                        By.CSS_SELECTOR, "input[type='text'], input[type='search']"
                    )
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
                log.warning("Search input not found — skipping search")

        except Exception as e:
            log.warning(f"Search failed: {e}")

    def click_table_row(self, row_index):
        """Click on a specific table row to select it.

        Args:
            row_index: 0-based index of the row
        """
        try:
            rows = self.driver.find_elements(
                By.CSS_SELECTOR, "table#excel-table tbody tr"
            )
            if row_index < len(rows):
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});"
                    "arguments[0].click();", rows[row_index]
                )
                self.wait_seconds(1)
        except Exception as e:
            log.warning(f"Click table row failed: {e}")

    # ==============================================================
    #  View/Edit by row
    # ==============================================================

    def view_farmer(self, entry_id=None, row_index=0):
        """Open the View form for a farmer.

        Args:
            entry_id: Optional farmer name/ID to search for
            row_index: Row index to click if not searching
        """
        log.info(f"Viewing farmer: entry_id={entry_id}, row_index={row_index}")
        if entry_id:
            self.search_farmer(entry_id)
            self.wait_seconds(2)

        # Click the view button for the specified row
        try:
            rows = self.driver.find_elements(
                By.CSS_SELECTOR, "table#excel-table tbody tr"
            )
            if row_index < len(rows):
                view_btn = rows[row_index].find_element(
                    By.CSS_SELECTOR, "td.cdk-column-view button, td.mat-column-view button"
                )
                self.driver.execute_script("arguments[0].click();", view_btn)
                self.wait_seconds(2)
                return True
        except Exception as e:
            log.warning(f"View button not found: {e}")
        return False

    def edit_farmer(self, entry_id=None, row_index=0):
        """Open the Edit form for a farmer.

        Args:
            entry_id: Optional farmer name/ID to search for
            row_index: Row index to click if not searching
        """
        log.info(f"Editing farmer: entry_id={entry_id}, row_index={row_index}")
        if entry_id:
            self.search_farmer(entry_id)
            self.wait_seconds(2)

        # Click the edit button for the specified row
        try:
            rows = self.driver.find_elements(
                By.CSS_SELECTOR, "table#excel-table tbody tr"
            )
            if row_index < len(rows):
                edit_btn = rows[row_index].find_element(
                    By.CSS_SELECTOR, "td.cdk-column-edit button, td.mat-column-edit button"
                )
                self.driver.execute_script("arguments[0].click();", edit_btn)
                self.wait_seconds(2)
                return True
        except Exception as e:
            log.warning(f"Edit button not found: {e}")
        return False

    # ==============================================================
    #  Get form field values (for verification)
    # ==============================================================

    def get_form_field_values(self):
        """Read current values of ALL form fields (Step 0 + active tab).

        Returns a dict with field names as keys and current values.
        """
        values = {}

        # Step 0 fields
        step0_fields = {
            "farmer_name": "Farmer Name",
            "email": "Email",
            "phone_number": "Phone Number",
            "password": "Password",
        }
        for key, name_attr in step0_fields.items():
            try:
                inp = self.driver.find_element(By.CSS_SELECTOR, f"input[name='{name_attr}']")
                values[key] = inp.get_attribute("value") or ""
            except Exception:
                values[key] = ""

        # Check toggle states
        try:
            toggle = self.driver.find_element(
                By.XPATH,
                "//app-slide-toggle-v2[.//span[contains(.,'Is Member of This FPC')]]"
                "//div[contains(@class,'switch-wrapper')]"
            )
            values["is_member_this_fpc"] = self._is_toggle_on(toggle)
        except Exception:
            values["is_member_this_fpc"] = False

        # Farmer Category — read selected text
        try:
            cat_trigger = self.driver.find_element(
                By.XPATH,
                "//mat-label[contains(.,'Farmer Category')]"
                "/ancestor::mat-form-field//mat-select"
            )
            cat_text = cat_trigger.text.strip()
            values["farmer_category"] = cat_text
        except Exception:
            values["farmer_category"] = ""

        # Active tab fields — read visible inputs in active panel
        try:
            active_inputs = self.driver.execute_script("""
                var popup = document.querySelector('.big-model, mat-dialog-container');
                if (!popup) return {};
                var activeContent = popup.querySelector(
                    'div.mat-horizontal-stepper-content-current'
                );
                if (!activeContent) return {};
                var inputs = activeContent.querySelectorAll('input[name]');
                var result = {};
                for (var i = 0; i < inputs.length; i++) {
                    var name = inputs[i].getAttribute('name');
                    if (name) {
                        result[name] = inputs[i].value || '';
                    }
                }
                return result;
            """)
            if active_inputs:
                values["active_tab_fields"] = active_inputs
        except Exception:
            pass

        return values

    # ==============================================================
    #  High-Level: Create Farmer
    #  Fills Step 0 + required stepper tabs + submits.
    #  Address Details is now REQUIRED for all categories.
    # ==============================================================

    def create_farmer(self, data, category="Walk-in Farmer"):
        """Create a farmer with the given data. Returns result dict.

        Handles ALL 3 farmer categories by navigating through the stepper
        tabs using the ACTUAL active tab name.

        Address Details tab is REQUIRED for all categories.

        Args:
            data: Data dict with all form fields. Expected structure:
                data["farmer_name"]          — Farmer Name (REQUIRED)
                data["email"]                — Email
                data["phone_number"]         — Phone Number (REQUIRED)
                data["password"]             — Password (REQUIRED)
                data["farmer_category"]      — category string or list
                data["address_details"]      — dict for Address Details (REQUIRED)
                data["other_details"]        — dict for Other Details
                data["family_details"]       — dict for Family Details
                data["additional_details"]   — dict for Additional Details
                data["land_details"]         — dict for Land Details
                data["crop_details"]         — dict for Crop Details
                data["kyc_details"]          — dict for KYC Details
                data["vehicle_details"]      — dict for Vehicle Details
                data["income_details"]       — dict for Income Details
                data["bank_details"]         — dict for Bank Details
                data["irrigation_details"]   — dict for Irrigation Details
                data["award_details"]        — dict for Award Details
                data["loan_details"]         — dict for Loan Details
            category: Default category to use if not specified in data.
        """
        log.info(f"Creating farmer (category={category})...")
        self.open_add_form()
        self.wait_seconds(1)

        # Ensure farmer_category is set
        if not data.get("farmer_category"):
            data["farmer_category"] = category

        # Fill Step 0
        self.fill_step0(data)

        # Wait for stepper tabs to appear after Farmer Category selection
        for wait_attempt in range(5):
            tab_names = self.get_stepper_names()
            non_empty = [n for n in tab_names if n.strip()]
            if non_empty:
                break
            log.info(f"Waiting for stepper tabs to appear... attempt {wait_attempt + 1}/5")
            self.wait_seconds(1)

        tab_names = self.get_stepper_names()
        log.info(f"Stepper tabs visible: {tab_names}")

        # Build the ordered list of tabs that need filling
        fillable_tabs = []
        for tab_name in tab_names:
            if not tab_name.strip():
                continue
            tab_lower = tab_name.strip().lower()
            # Find matching data key
            data_key = None
            for ui_name, key in self.TAB_DATA_MAP.items():
                if ui_name.lower() in tab_lower:
                    data_key = key
                    break
            if data_key:
                fillable_tabs.append((tab_name, data_key))

        log.info(f"Fillable tabs: {[(t, k) for t, k in fillable_tabs]}")

        # Click Next ONCE to advance from Farmer Details step
        next_clicked = self.click_stepper_next()
        if not next_clicked:
            log.warning("Stepper Next click failed after Step 0 — trying force navigate")
        self.wait_seconds(1.5)

        # Verify we actually moved past Step 0
        active_tab = self.get_current_stepper_name()
        log.info(f"After Step 0 Next click, active tab: {active_tab}")

        # Track filled tabs to avoid re-filling
        filled_tabs = set()

        # Navigate to each tab EXPLICITLY by name, then fill it
        for tab_name, data_key in fillable_tabs:
            tab_lower = tab_name.strip().lower()

            if tab_lower in filled_tabs:
                log.info(f"Tab already filled, skipping: {tab_name}")
                continue

            # Navigate explicitly to the correct tab
            if not self.navigate_to_stepper(tab_name):
                log.warning(f"Could not navigate to tab: {tab_name} — skipping")
                continue

            actual_tab = self.get_current_stepper_name()
            log.info(f"Current tab: {actual_tab} (target: {tab_name})")

            # Fill the tab if data is provided
            if data.get(data_key):
                self.fill_tab_by_name(tab_name, data[data_key])
                log.info(f"Filled tab: {tab_name}")
            else:
                log.info(f"Skipping tab (no data provided): {tab_name}")

            filled_tabs.add(tab_lower)

        # Submit
        self._force_close_panels()

        # Check for validation errors before submitting
        validation_errors = self.get_mat_error_text()
        if validation_errors:
            log.warning(f"Validation errors before submit: {validation_errors}")

        self.submit_form()
        self.wait_seconds(2)

        # Handle success or validation alert
        alert_title = self.handle_success_alert(timeout=15)

        if "successfully" not in alert_title.lower():
            validation_warning = self.handle_validation_warning(timeout=3)
            if validation_warning:
                log.warning(f"Validation warning: {validation_warning}")
                alert_title = validation_warning

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

        if result["status"] == "FAILED":
            log.warning(
                f"Create FAILED for '{data.get('farmer_name', '?')}': "
                f"alert='{alert_title}', "
                f"pre-submit_errors={validation_errors}"
            )

        FARMER_SUBMISSIONS.append(result)
        return result

    # ==============================================================
    #  Legacy compatibility aliases
    # ==============================================================

    def submit(self):
        """Alias for submit_form()."""
        return self.submit_form()

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

    def close_popup(self):
        """Close form popup via Cancel or backdrop click."""
        try:
            self.cancel()
        except Exception:
            pass
        self.wait_seconds(0.5)

    def is_edit_mode(self):
        """Check if the form is in Edit mode (Update button present)."""
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
                        return
                except Exception:
                    continue
        except Exception:
            pass

    def search_item(self, search_text):
        """Alias for search_farmer()."""
        return self.search_farmer(search_text)

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

    # Legacy tab navigation alias
    def navigate_to_tab_by_name(self, target_tab_name):
        """Alias for navigate_to_stepper()."""
        return self.navigate_to_stepper(target_tab_name)

    def get_active_tab_name(self):
        """Alias for get_current_stepper_name()."""
        return self.get_current_stepper_name()

    def get_stepper_tab_names(self):
        """Alias for get_stepper_names()."""
        return self.get_stepper_names()

    # Legacy fill methods for backward compatibility
    def fill_current_address(self, data):
        """Legacy: Fill address with 'Current Address' context."""
        self.fill_address_details({"current_address": data, "permanent_address": data})

    def fill_permanent_address(self, data):
        """Legacy: Fill address with 'Permanent Address' context."""
        self.fill_address_details({"permanent_address": data, "same_as_above": True})
