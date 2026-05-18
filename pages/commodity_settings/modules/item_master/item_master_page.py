"""
item_master_page.py
-------------------
Page Object Model for RhythmERP Item Master screen.

Location: Commodity Settings > Commodity Master > Item Master
URL:      /#/dynamic-screens/Item%20Master

FORM LAYOUT (3-STEP STEPPER FORM — NOT a simple popup):

  Step 1 — "Additional Details":
    - Item Name              (AUTO-GENERATED, READONLY — space-separated concat of Attr 1-5)
    - Item Code              (AUTO-GENERATED, editable — dash-separated concat of Attr 1-5)
    - Description            (text input,   optional)
    - Item Category          (mat-select,   required, searchable) ← FILL FIRST
    - Item Group             (mat-select,   NOT required, searchable) ← NOT required in Create/Edit
    - Item Type              (mat-select,   required, searchable)
    - Item Attribute 1-5     (mat-select,   optional, searchable)
    - UOM                    (mat-select,   required, searchable)
    - HSN SAC Code           (mat-select,   required, searchable)
    - Base Uom               (mat-select,   required, searchable)
    - Base Uom Conversion    (text input,   required, numeric)
    *** PLUS 3 TOGGLE SWITCHES (visible on Step 1 — NOT 4!): ***
    - Status                 (toggle switch,  Active/Inactive, default Active)
      → Located in .big-model parent (always visible regardless of step)
    - Is Critical            (toggle switch,  Yes/No, default No)
    - Include Wip Stock Cal  (toggle switch,  Yes/No, default No)
    - Is Packing Material    (toggle switch,  Yes/No, default No)
      → These 3 are in Step 0's mat-horizontal-stepper-content (visible only on Step 1)
    - NOTE: "Allow Negative Stock" toggle DOES NOT EXIST in Item Master
      (was incorrectly listed in V1 spec — confirmed absent 2026-05-18)

  Step 2 — "Define Item Master Details" (ATTACHMENT ONLY — NO toggles!):
    - Attachment Type        (mat-select/combobox, optional, placeholder "Select Attachment Type")
    - File Upload            (file upload widget, optional, shows "cloud_upload No File Uploaded")

  Step 3 — "Product Order Packeging Details" (note: typo is on actual page):
    - Table inside <app-dynamic-details> component
    - Columns: Action (add/delete), Packaging (mat-select),
               Packaging Capacity (number input), Base Packaging Capacity (number input)
    - Starts with 1 default empty row; Add (+) button to add more rows

TABLE COLUMNS (main listing):
  - View / Edit / History   (action buttons per row)
  - Item Name
  - UOM
  - Status

KEY RULES (V2 — updated from browser exploration 2026-05-18):
  - NEVER use Keys.ESCAPE (use backdrop click + JS overlay removal)
  - JS clicks for Angular Material overlays
  - Dropdown options read dynamically at runtime (never hardcode)
  - Toggle switches use <app-slide-toggle-v2> with <span class="main-label">
    and <div class="switch-wrapper compact"> (NOT standard Angular)
  - Item Name is AUTO-GENERATED and READONLY: space-separated concat of Attr 1-5
    Cannot be typed into — CANNOT test spaces-only, long strings, or special chars in name
    formcontrolname="name" (NOT "itemName") — confirmed via browser exploration
  - Item Code is AUTO-GENERATED but EDITABLE: dash-separated concat of Attr 1-5
    CAN be manually overridden after auto-generation
    formcontrolname="code" (NOT "itemCode") — confirmed via browser exploration
  - ONLY 3 toggles on Step 1 (NOT 4): Status, Is Critical, Include Wip Stock Cal,
    Is Packing Material. "Allow Negative Stock" DOES NOT EXIST (verified 2026-05-18)
  - Item Group is NOT required in Create OR Edit mode (confirmed 2026-05-18)
  - Base Uom does NOT auto-sync with UOM — they are independent fields (confirmed 2026-05-18)
  - DROPDOWN FILL ORDER IS CRITICAL: Category → Group → Type → Attr1 → Attr2 → Attr3 → Attr4 → Attr5
    Category/Group/Type are INDEPENDENT of each other, but Attributes cascade:
    Attr1 depends on Category+Group+Type combo, Attr2 depends on Attr1, etc.
  - Duplicate Item Names are ALLOWED — no uniqueness validation (confirmed 2026-05-18)
  - Step 2 & 3 tabs are DISABLED in Edit mode — only Step 1 is editable
  - Edit mode button says "Update" not "Submit"
  - Validation error: "This field is required" (generic) + SweetAlert2 "Validation Failed"
  - Step 2 has ONLY Attachment Type + File Upload
  - Stepper navigation: Next/Back buttons between steps, Submit on final step
  - After completing Step 1, tab label changes to "Editable Additional Details"
  - History column uses mat-column-archive (NOT mat-column-history)
  - Stacked popups: History -> View (z-index 1001 over 1000)
  - Step 3 grid table uses <table class="grid-table"> with <tr>/<td>
  - CRITICAL: Browser-clicked mat-select options do NOT update Angular reactive form model.
    Must use JS value-setter + dispatchEvent for all dropdown selections.
    The _select_mat_option method must trigger Angular change detection.
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


class ItemMasterPage(BasePage):
    PAGE_URL = f"{RHYTHMERP_BASE_URL}/#/dynamic-screens/Item%20Master"

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
    #  LOCATORS — Table (main listing)
    # ==============================================================
    TABLE = ("css", "table#excel-table")
    TABLE_ROWS = ("css", "table#excel-table tbody tr")
    TABLE_NAME_CELLS = (
        "css",
        "table#excel-table tbody td.cdk-column-itemName, "
        "table#excel-table tbody td.mat-column-itemName, "
        "table#excel-table tbody td.cdk-column-item_name, "
        "table#excel-table tbody td.mat-column-item_name, "
        "table#excel-table tbody td:nth-child(4)",
    )
    TABLE_UOM_CELLS = (
        "css",
        "table#excel-table tbody td.cdk-column-uom, "
        "table#excel-table tbody td.mat-column-uom, "
        "table#excel-table tbody td:nth-child(5)",
    )
    TABLE_STATUS_CELLS = (
        "css",
        "table#excel-table tbody td.cdk-column-status, "
        "table#excel-table tbody td.mat-column-status, "
        "table#excel-table tbody td:nth-child(6)",
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
        ".big-model h3, mat-dialog-container h3, "
        ".mat-mdc-dialog-title, .edit_pop_up h3",
    )
    MAT_STEPPER = ("css", "mat-stepper, mat-horizontal-stepper, mat-vertical-stepper")
    STEPPER_STEPS = ("css", "mat-step, .mat-step")

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
    #  LOCATORS — Step 1: "Additional Details"
    # ==============================================================
    # Text inputs
    ITEM_NAME_INPUT = (
        "css",
        "input[formcontrolname='name'], input[name='Item Name'], "
        "input[name='itemName']",
    )  # V2: formcontrolname='name' confirmed via browser exploration (was 'itemName' in V1)
    ITEM_CODE_INPUT = (
        "css",
        "input[formcontrolname='code'], input[name='Item Code'], "
        "input[name='itemCode']",
    )  # V2: formcontrolname='code' confirmed via browser exploration (was 'itemCode' in V1)
    DESCRIPTION_INPUT = (
        "css",
        "input[name='Description'], textarea[formcontrolname='description'], "
        "input[name='description']",
    )
    BASE_UOM_CONVERSION_INPUT = (
        "css",
        "input[name='Base Uom Conversion'], "
        "input[formcontrolname='baseUomConversion'], "
        "input[name='baseUomConversion']",
    )

    # Dropdowns (mat-select) — using XPath by label for reliability
    # V2: Fill order is Category → Group → Type (Category FIRST, confirmed 2026-05-18)
    # Item Group is NOT required in Create or Edit mode
    ITEM_CATEGORY_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Item Category')]"
        "/ancestor::mat-form-field//mat-select",
    )
    ITEM_GROUP_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Item Group')]"
        "/ancestor::mat-form-field//mat-select",
    )
    ITEM_TYPE_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Item Type')]"
        "/ancestor::mat-form-field//mat-select",
    )
    ITEM_ATTRIBUTE1_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Item Attribute 1') or contains(.,'Item Attribute1')]"
        "/ancestor::mat-form-field//mat-select",
    )
    ITEM_ATTRIBUTE2_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Item Attribute 2') or contains(.,'Item Attribute2')]"
        "/ancestor::mat-form-field//mat-select",
    )
    ITEM_ATTRIBUTE3_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Item Attribute 3') or contains(.,'Item Attribute3')]"
        "/ancestor::mat-form-field//mat-select",
    )
    ITEM_ATTRIBUTE4_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Item Attribute 4') or contains(.,'Item Attribute4')]"
        "/ancestor::mat-form-field//mat-select",
    )
    ITEM_ATTRIBUTE5_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Item Attribute 5') or contains(.,'Item Attribute5')]"
        "/ancestor::mat-form-field//mat-select",
    )
    UOM_SELECT = (
        "xpath",
        "//mat-label[(contains(.,'UOM') or contains(.,'Uom') or contains(.,'uom'))"
        " and not(contains(.,'Base'))]"
        "/ancestor::mat-form-field//mat-select",
    )
    HSN_SAC_CODE_SELECT = (
        "xpath",
        "//mat-label[contains(.,'HSN') or contains(.,'hsn')]"
        "/ancestor::mat-form-field//mat-select",
    )
    BASE_UOM_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Base Uom') and not(contains(.,'Conversion'))]"
        "/ancestor::mat-form-field//mat-select",
    )

    # Toggle switches — Step 1 uses <span class="main-label"> + <div class="switch-wrapper compact">
    #   inside <app-slide-toggle-v2> component (NOT mat-label/mat-form-field)
    #   NOTE: ONLY 3 toggles on Step 1 (NOT 4! Verified 2026-05-18).
    #   "Allow Negative Stock" DOES NOT EXIST in Item Master.
    #   Status toggle is in .big-model parent (always visible regardless of step).
    #   Is Critical, Include Wip Stock Cal, Is Packing Material are in
    #   Step 0's mat-horizontal-stepper-content (visible only when Step 1 is active).
    STATUS_TOGGLE = (
        "xpath",
        "//app-slide-toggle-v2[.//span[contains(@class,'main-label') and contains(.,'Status')]]"
        "//div[contains(@class,'switch-wrapper')]",
    )
    IS_CRITICAL_TOGGLE = (
        "xpath",
        "//app-slide-toggle-v2[.//span[contains(@class,'main-label') and contains(.,'Is Critical')]]"
        "//div[contains(@class,'switch-wrapper')]",
    )
    INCLUDE_WIP_TOGGLE = (
        "xpath",
        "//app-slide-toggle-v2[.//span[contains(@class,'main-label') and contains(.,'Include Wip')]]"
        "//div[contains(@class,'switch-wrapper')]",
    )
    IS_PACKING_MATERIAL_TOGGLE = (
        "xpath",
        "//app-slide-toggle-v2[.//span[contains(@class,'main-label') and contains(.,'Is Packing Material')]]"
        "//div[contains(@class,'switch-wrapper')]",
    )

    # ==============================================================
    #  LOCATORS — Step 2: "Define Item Master Details"
    #  (Attachment Type + File Upload — NO toggles!)
    # ==============================================================
    ATTACHMENT_TYPE_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Attachment Type')]"
        "/ancestor::mat-form-field//mat-select",
    )
    FILE_UPLOAD_INPUT = (
        "css",
        "input[type='file'], input[formcontrolname='fileUpload']",
    )
    FILE_UPLOAD_WIDGET = (
        "xpath",
        "//*[contains(.,'cloud_upload') and contains(.,'No File Uploaded')]",
    )

    # ==============================================================
    #  LOCATORS — Step 3: "Product Order Packaging Details"
    #  Uses <table class="grid-table"> with <tr>/<td> rows
    #  inside <app-dynamic-details> component
    # ==============================================================
    STEP3_ADD_ROW_BUTTON = (
        "xpath",
        "//button[contains(.,'Add Row') or contains(.,'Add') "
        "and contains(@class,'add-row')]",
    )
    STEP3_TABLE = (
        "css",
        "app-dynamic-details table.grid-table",
    )
    STEP3_ROWS = (
        "css",
        "app-dynamic-details table.grid-table tbody tr",
    )

    # ==============================================================
    #  LOCATORS — Row action buttons (parametrised by item name)
    # ==============================================================
    VIEW_BUTTON = (
        "xpath",
        "//td[contains(text(),'{item_name}')]"
        "/ancestor::tr//td[contains(@class,'cdk-column-view')]"
        "//button",
    )
    EDIT_BUTTON = (
        "xpath",
        "//td[contains(text(),'{item_name}')]"
        "/ancestor::tr//td[contains(@class,'cdk-column-edit')]"
        "//button",
    )
    HISTORY_BUTTON = (
        "xpath",
        "//td[contains(text(),'{item_name}')]"
        "/ancestor::tr//td[contains(@class,'cdk-column-archive')]"
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
        "//div[@class='popup-footer']//button[contains(.,'Cancel') or contains(.,'Close')]",
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
        """Navigate to the Item Master listing page.
        Force-refreshes to clear leftover Angular state from previous tests.
        """
        log.info("Navigating to Item Master page...")
        self.navigate_to(self.PAGE_URL)
        self.driver.refresh()
        self._wait_for_page_ready()

    def _wait_for_page_ready(self):
        """Wait until the Item Master page is fully loaded:
        1. Table renders
        2. Toolbar buttons (including ADD) are clickable
        """
        try:
            WebDriverWait(self.driver, EXPLICIT_WAIT).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, "table#excel-table")
                )
            )
            log.info("Item Master table loaded")
        except TimeoutException:
            log.warning("Item Master table not found, page may be empty")

        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "ul.tbl-export-btn")
                )
            )
            self.wait_seconds(1)
            log.info("Item Master toolbar ready")
        except TimeoutException:
            log.warning("Toolbar not found, ADD button may be delayed")
            self.wait_seconds(3)

    def is_page_loaded(self):
        """Check if the Item Master listing page has loaded."""
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
        Item Master opens a 3-step stepper form.
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

    def _wait_for_form_content(self, timeout=5):
        """Wait for form content (inputs/stepper) to render inside the popup."""
        import time as _time
        deadline = _time.time() + timeout
        while _time.time() < deadline:
            try:
                # Check for stepper or any input inside popup
                elements = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    "div.big-model mat-stepper, "
                    "div.big-model input, "
                    "mat-dialog-container mat-stepper, "
                    "mat-dialog-container input, "
                    ".edit_pop_up mat-stepper, "
                    ".edit_pop_up input, "
                    "div.cdk-overlay-container mat-stepper"
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
                "div.big-model, mat-dialog-container, "
                ".edit_pop_up, div.popup-wrapper"
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
    #  Stepper navigation
    # ==============================================================

    def click_stepper_next(self):
        """Click the 'Next' button on the current stepper step
        to advance to the next step.
        """
        log.info("Clicking stepper Next button...")
        self._force_close_panels()

        # Strategy 1: Angular Material stepper next button
        try:
            next_btns = self.driver.find_elements(
                By.CSS_SELECTOR,
                "button.mat-stepper-next, "
                "button.mat-mdc-stepper-next"
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
                "//button[contains(.,'Next') and not(contains(.,'Next page'))]"
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
                    '.big-model button, mat-dialog-container button, '
                    + '.edit_pop_up button'
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
        """
        log.info("Clicking stepper Back button...")
        self._force_close_panels()

        # Strategy 1: Angular Material stepper previous button
        try:
            back_btns = self.driver.find_elements(
                By.CSS_SELECTOR,
                "button.mat-stepper-previous, "
                "button.mat-mdc-stepper-previous"
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
                "//button[contains(.,'Back') and not(contains(.,'Back to'))]"
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

        log.warning("Stepper Back button not found or not clickable")
        return False

    def get_current_step_index(self):
        """Get the 0-based index of the currently active stepper step.
        Returns 0 for Step 1, 1 for Step 2, 2 for Step 3.
        Returns -1 if stepper not found.
        """
        try:
            steps = self.driver.find_elements(
                By.CSS_SELECTOR,
                "mat-step-header, .mat-step-header, "
                ".mat-mdc-step-header"
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
            # Find active step header and read its label
            steps = self.driver.find_elements(
                By.CSS_SELECTOR,
                "mat-step-header, .mat-step-header"
            )
            for step in steps:
                try:
                    classes = step.get_attribute("class") or ""
                    if "selected" in classes or "active" in classes:
                        return step.text.strip()
                except Exception:
                    continue

            # Fallback: find active step via CSS
            active_label = self.driver.find_elements(
                By.CSS_SELECTOR,
                ".mat-step-text-label, .mat-mdc-stepper-horizontal-label"
            )
            for label in active_label:
                try:
                    if label.is_displayed():
                        return label.text.strip()
                except Exception:
                    continue
        except Exception:
            pass
        return ""

    def is_step1_active(self):
        """Check if Step 1 (Additional Details) is the current active step."""
        return self.get_current_step_index() == 0

    def is_step2_active(self):
        """Check if Step 2 (Define Item Master Details) is the current active step."""
        return self.get_current_step_index() == 1

    def is_step3_active(self):
        """Check if Step 3 (Product Order Packaging Details) is the current active step."""
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
                "mat-step-header, .mat-step-header"
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
    #  Step 1: Fill "Additional Details" fields
    # ==============================================================

    def fill_step1(self, data):
        """Fill all fields on Step 1 — "Additional Details".
        Dropdown values: if None/empty, picks a random option from the live UI.
        Item Name is AUTO-GENERATED from Item Attribute 1-5 concatenation,
        so we do NOT type into the Item Name field.
        Toggle switches are on Step 1 (verified on live app).
        Returns the auto-generated item name (concatenation of attribute values).
        """
        log.info("Filling Step 1 — Additional Details...")

        # --- Text Inputs (Item Name is auto-generated, do NOT type it) ---
        if data.get("item_name"):
            log.info(
                "Item Name is auto-generated from attributes — "
                "skipping manual input"
            )

        if data.get("item_code"):
            self.type_text(
                self.ITEM_CODE_INPUT, str(data["item_code"]), clear_first=True
            )

        if data.get("description"):
            self.type_text(
                self.DESCRIPTION_INPUT, str(data["description"]), clear_first=True
            )

        if data.get("base_uom_conversion"):
            self.type_text(
                self.BASE_UOM_CONVERSION_INPUT,
                str(data["base_uom_conversion"]),
                clear_first=True,
            )

        # --- Dropdown selects ---
        # Capture selected attribute values for auto-generated item name
        attr_values = []

        # V2: Fill order is CRITICAL: Category → Group → Type → Attr1 → Attr2 → Attr3 → Attr4 → Attr5
        # Category/Group/Type are INDEPENDENT of each other, but Attributes cascade:
        # Attr1 depends on Category+Group+Type combo, Attr2 depends on Attr1, etc.
        self._fill_dropdown_if_provided(
            data, "item_category", self.ITEM_CATEGORY_SELECT, "Item Category"
        )  # FILL FIRST — options: Pulses, Oilseeds, Grains
        self._fill_dropdown_if_provided(
            data, "item_group", self.ITEM_GROUP_SELECT, "Item Group"
        )  # NOT required — options: Raw Material, Finished Goods, Semi Finished
        self._fill_dropdown_if_provided(
            data, "item_type", self.ITEM_TYPE_SELECT, "Item Type"
        )  # options: Non Farm, Farm

        # Item Attributes 1-5 — capture selected values for name prediction
        attr1 = self._fill_dropdown_if_provided(
            data, "item_attribute1", self.ITEM_ATTRIBUTE1_SELECT, "Item Attribute 1"
        )
        if attr1:
            attr_values.append(attr1)

        attr2 = self._fill_dropdown_if_provided(
            data, "item_attribute2", self.ITEM_ATTRIBUTE2_SELECT, "Item Attribute 2"
        )
        if attr2:
            attr_values.append(attr2)

        attr3 = self._fill_dropdown_if_provided(
            data, "item_attribute3", self.ITEM_ATTRIBUTE3_SELECT, "Item Attribute 3"
        )
        if attr3:
            attr_values.append(attr3)

        attr4 = self._fill_dropdown_if_provided(
            data, "item_attribute4", self.ITEM_ATTRIBUTE4_SELECT, "Item Attribute 4"
        )
        if attr4:
            attr_values.append(attr4)

        attr5 = self._fill_dropdown_if_provided(
            data, "item_attribute5", self.ITEM_ATTRIBUTE5_SELECT, "Item Attribute 5"
        )
        if attr5:
            attr_values.append(attr5)

        # Build the auto-generated item name from attribute values
        auto_name = " ".join(attr_values)
        if auto_name:
            log.info(f"Auto-generated Item Name (from attributes): '{auto_name}'")
            data["_auto_item_name"] = auto_name
        else:
            # Fallback: read the Item Name field value after all selections
            try:
                name_el = self.driver.find_element(
                    By.CSS_SELECTOR,
                    "input[name='Item Name'], input[formcontrolname='itemName']"
                )
                auto_name = name_el.get_attribute("value") or ""
                if auto_name:
                    log.info(f"Read auto-generated Item Name from field: '{auto_name}'")
                    data["_auto_item_name"] = auto_name
            except Exception:
                pass

        # V2: Base Uom does NOT auto-sync with UOM — must fill independently
        self._fill_dropdown_if_provided(
            data, "uom", self.UOM_SELECT, "UOM"
        )  # Use KG for automation. Does NOT auto-fill Base Uom.
        self._fill_dropdown_if_provided(
            data, "hsn_sac_code", self.HSN_SAC_CODE_SELECT, "HSN SAC Code"
        )  # e.g., 8537
        self._fill_dropdown_if_provided(
            data, "base_uom", self.BASE_UOM_SELECT, "Base Uom"
        )  # INDEPENDENT of UOM. Same lookup data. Use KG.

        # --- Toggle switches (3 toggles on Step 1 — NOT 4! Verified 2026-05-18) ---
        # "Allow Negative Stock" toggle DOES NOT EXIST in Item Master
        self._set_toggle_if_provided(data, "status", self.STATUS_TOGGLE, "Status")
        self._set_toggle_if_provided(data, "is_critical", self.IS_CRITICAL_TOGGLE, "Is Critical")
        self._set_toggle_if_provided(data, "include_wip", self.INCLUDE_WIP_TOGGLE, "Include Wip Stock Cal")
        self._set_toggle_if_provided(
            data, "is_packing_material", self.IS_PACKING_MATERIAL_TOGGLE, "Is Packing Material"
        )

        self._force_close_panels()
        log.info("Step 1 form filled")
        return auto_name

    def _fill_dropdown_if_provided(self, data, key, select_locator, label_name):
        """Fill a dropdown if the key exists in data.
        If value is provided, select that specific option.
        If key exists but value is empty/None, select random.
        If key doesn't exist in data, skip entirely.
        Returns the selected option text (or None if skipped/failed).
        """
        if key not in data:
            return None  # Key not provided — skip this dropdown entirely

        value = data[key]
        if value:
            self._select_mat_option(select_locator, str(value))
            return str(value)
        else:
            return self._select_random_from_dropdown(select_locator, label_name)

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
        The Item Master uses <app-slide-toggle-v2> with:
          - <span class="main-label">Label Text</span>
          - <div class="switch-wrapper compact">
              <span class="state-label off active"> No </span>
              <input type="checkbox">
              <div class="slider"><div class="circle"></div></div>
              <span class="state-label on"> Yes </span>
            </div>
        Locator XPath targets the label text to find the right toggle.
        """
        log.info(f"Setting toggle '{label_name}' to {'ON' if desired_state else 'OFF'}...")

        toggle_el = None

        # Strategy 1: Primary XPath locator (app-slide-toggle-v2 based)
        try:
            toggle_el = self.driver.find_element(
                By.XPATH, toggle_locator[1]
            )
        except Exception:
            pass

        # Strategy 2: Broader label-based search using span.main-label
        if not toggle_el:
            try:
                # Map common label variations
                label_map = {
                    "Status": "Status",
                    "Is Critical": "Is Critical",
                    "Include Wip": "Include Wip",
                    "Include Wip Stock Cal": "Include Wip",
                    "Is Packing Material": "Is Packing Material",
                }
                search_label = label_map.get(label_name, label_name)
                toggle_el = self.driver.find_element(
                    By.XPATH,
                    f"//span[contains(@class,'main-label') and contains(.,'{search_label}')]"
                    "/ancestor::app-slide-toggle-v2"
                    "//div[contains(@class,'switch-wrapper')]"
                )
            except Exception:
                pass

        # Strategy 3: Any switch-wrapper with matching label nearby
        if not toggle_el:
            try:
                containers = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    "app-slide-toggle-v2"
                )
                for container in containers:
                    try:
                        label = container.find_element(
                            By.CSS_SELECTOR, "span.main-label"
                        )
                        if label_name.lower() in label.text.lower():
                            toggle_el = container.find_element(
                                By.CSS_SELECTOR,
                                "div.switch-wrapper"
                            )
                            break
                    except Exception:
                        continue
            except Exception:
                pass

        if not toggle_el:
            log.warning(f"Toggle '{label_name}' not found")
            return

        # Determine current state from the 'off active' / 'on active' spans
        current_state = self._is_toggle_on(toggle_el)

        if current_state == desired_state:
            log.info(f"Toggle '{label_name}' already {'ON' if desired_state else 'OFF'}")
            return

        # Click the toggle to change state
        try:
            # Try clicking the inner checkbox input
            checkbox = toggle_el.find_element(
                By.CSS_SELECTOR, "input[type='checkbox']"
            )
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});"
                "arguments[0].click();",
                checkbox,
            )
        except Exception:
            # Fallback: click the slider div
            try:
                slider = toggle_el.find_element(
                    By.CSS_SELECTOR, ".slider"
                )
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});"
                    "arguments[0].click();",
                    slider,
                )
            except Exception:
                # Last fallback: click the toggle wrapper itself
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});"
                    "arguments[0].click();",
                    toggle_el,
                )

        self.wait_seconds(0.5)

        # Verify state change
        new_state = self._is_toggle_on(toggle_el)
        if new_state == desired_state:
            log.info(f"Toggle '{label_name}' set to {'ON' if desired_state else 'OFF'}")
        else:
            log.warning(
                f"Toggle '{label_name}' state change may have failed. "
                f"Desired: {desired_state}, Got: {new_state}"
            )

    def _is_toggle_on(self, toggle_el):
        """Determine if a custom toggle switch element is ON or OFF.
        For <app-slide-toggle-v2>, the state is indicated by:
          - <span class="state-label off active"> No </span>  → OFF
          - <span class="state-label on active"> Yes </span>  → ON
        Also checks the checkbox input's selected state as fallback.
        Returns True if ON, False if OFF.
        """
        try:
            # Strategy 1: Check "on" state-label has "active" class
            try:
                on_labels = toggle_el.find_elements(
                    By.CSS_SELECTOR, "span.state-label.on"
                )
                for on_label in on_labels:
                    classes = on_label.get_attribute("class") or ""
                    if "active" in classes:
                        return True
            except Exception:
                pass

            # Strategy 2: Check "off" state-label has "active" class → means OFF
            try:
                off_labels = toggle_el.find_elements(
                    By.CSS_SELECTOR, "span.state-label.off"
                )
                for off_label in off_labels:
                    classes = off_label.get_attribute("class") or ""
                    if "active" in classes:
                        return False
            except Exception:
                pass

            # Strategy 3: Check inner checkbox input
            try:
                checkbox = toggle_el.find_element(
                    By.CSS_SELECTOR, "input[type='checkbox']"
                )
                return checkbox.is_selected()
            except Exception:
                pass

            # Strategy 4: Check wrapper class for active/checked
            classes = toggle_el.get_attribute("class") or ""
            if "active" in classes or "checked" in classes:
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

    # ==============================================================
    #  Step 2: Fill "Define Item Master Details"
    # ==============================================================

    def fill_step2(self, data):
        """Fill all fields on Step 2 — "Define Item Master Details".
        Step 2 contains ONLY:
          - Attachment Type (mat-select, optional)
          - File Upload (optional)
        There are NO toggle switches in Step 2 — all toggles are on Step 1.
        """
        log.info("Filling Step 2 — Define Item Master Details (attachment)...")

        # --- Attachment Type dropdown (optional) ---
        if data.get("attachment_type"):
            self._select_mat_option(self.ATTACHMENT_TYPE_SELECT, str(data["attachment_type"]))
        elif "attachment_type" in data and not data["attachment_type"]:
            # attachment_type key exists but empty — select random
            self._select_random_from_dropdown(self.ATTACHMENT_TYPE_SELECT, "Attachment Type")

        # --- File Upload (optional) ---
        if data.get("file_path"):
            self._upload_file(data["file_path"])

        self._force_close_panels()
        log.info("Step 2 form filled")

    def _upload_file(self, file_path):
        """Upload a file using the file input element.
        Handles the hidden file input by sending keys directly.
        """
        log.info(f"Uploading file: {file_path}")
        try:
            file_inputs = self.driver.find_elements(
                By.CSS_SELECTOR,
                ".big-model input[type='file'], "
                "mat-dialog-container input[type='file'], "
                ".edit_pop_up input[type='file']"
            )
            for inp in file_inputs:
                try:
                    if inp.is_displayed() or inp.is_enabled():
                        inp.send_keys(file_path)
                        self.wait_seconds(1)
                        log.info("File uploaded successfully")
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
                        log.info("File uploaded via JS visibility fix")
                        return
                    except Exception:
                        continue
            except Exception:
                pass

            log.warning("File upload input not found")
        except Exception as e:
            log.error(f"File upload failed: {e}")

    # ==============================================================
    #  Step 3: "Product Order Packaging Details" — Dynamic table
    # ==============================================================

    def fill_step3(self, data):
        """Fill Step 3 — "Product Order Packaging Details".
        This step has a dynamic table inside <app-dynamic-details>.
        Table uses <table class="grid-table"> with <tr>/<td> rows.
        Each row has: Packaging (mat-select), Packaging Capacity (input),
        Base Packaging Capacity (input), and an Add (+) button.

        Data format (supports both "rows" and "packaging_rows" keys):
          {
              "rows": [
                  {"packaging": "Box", "capacity": "10", "base_capacity": "5"},
              ]
          }
        or:
          {
              "packaging_rows": [
                  {"packaging": None, "capacity": "10", "base_capacity": "5"},
              ]
          }
        If rows list is empty or not provided, skips filling (default row exists).
        """
        log.info("Filling Step 3 — Product Order Packaging Details...")
        rows = data.get("rows", data.get("packaging_rows", []))

        for i, row_data in enumerate(rows):
            if i > 0:
                # Add a new row for each additional entry
                self._click_add_row_step3()

            self._fill_step3_row(i, row_data)

        self._force_close_panels()
        log.info(f"Step 3 filled with {len(rows)} row(s)")

    def _click_add_row_step3(self):
        """Click the Add (+) button in Step 3 to add a new table row.
        The button is a mat-icon-button with a 'add' mat-icon inside
        the grid table's Action column.
        """
        log.info("Clicking Add Row in Step 3...")

        # Strategy 1: mat-icon-button with add icon inside app-dynamic-details
        try:
            add_btns = self.driver.find_elements(
                By.CSS_SELECTOR,
                "app-dynamic-details button.mat-mdc-icon-button"
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
                        log.info("Add Row clicked via icon button in grid table")
                        return
                except Exception:
                    continue
        except Exception:
            pass

        # Strategy 2: Button with 'Add Row' text
        try:
            add_btns = self.driver.find_elements(
                By.XPATH,
                "//button[contains(.,'Add Row') or contains(.,'Add row')]"
            )
            for btn in add_btns:
                try:
                    if btn.is_displayed():
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({block:'center'});"
                            "arguments[0].click();",
                            btn,
                        )
                        self.wait_seconds(1)
                        log.info("Add Row clicked via text match")
                        return
                except Exception:
                    continue
        except Exception:
            pass

        # Strategy 3: JS click add button in app-dynamic-details
        try:
            self.driver.execute_script("""
                var btns = document.querySelectorAll(
                    'app-dynamic-details button[mat-icon-button]'
                );
                for (var i = 0; i < btns.length; i++) {
                    var icon = btns[i].querySelector('mat-icon');
                    if (icon && icon.textContent.trim().toLowerCase() === 'add') {
                        btns[i].click();
                        break;
                    }
                }
            """)
            self.wait_seconds(1)
            log.info("Add Row clicked via JS")
        except Exception:
            log.warning("Add Row button not found in Step 3")

    def _fill_step3_row(self, row_index, row_data):
        """Fill a single row in the Step 3 dynamic table.
        Uses <app-dynamic-details> > <table class="grid-table"> > <tbody> > <tr>.
        row_data: {"packaging": "Box", "capacity": "10", "base_capacity": "5"}
        If packaging is None/empty, selects random from dropdown.
        """
        log.info(f"Filling Step 3 row {row_index}...")

        try:
            # Find rows in the Step 3 grid table
            rows = self.driver.find_elements(
                By.CSS_SELECTOR,
                "app-dynamic-details table.grid-table tbody tr"
            )

            # Filter to visible rows only
            visible_rows = []
            for r in rows:
                try:
                    if r.is_displayed():
                        visible_rows.append(r)
                except Exception:
                    continue

            if row_index >= len(visible_rows):
                log.warning(
                    f"Row index {row_index} out of range "
                    f"(visible rows: {len(visible_rows)})"
                )
                return

            target_row = visible_rows[row_index]

            # Fill Packaging dropdown in this row
            packaging_val = row_data.get("packaging")
            if packaging_val:
                self._fill_row_dropdown(target_row, str(packaging_val))
            elif "packaging" in row_data and not packaging_val:
                # packaging key exists but empty — select random
                self._fill_row_dropdown_random(target_row, "Packaging")

            # Fill Packaging Capacity text input in this row
            if row_data.get("capacity"):
                self._fill_row_text_input(
                    target_row, "Packaging Capacity", row_data["capacity"]
                )

            # Fill Base Packaging Capacity text input in this row
            if row_data.get("base_capacity"):
                self._fill_row_text_input(
                    target_row, "Base Packaging Capacity", row_data["base_capacity"]
                )

        except Exception as e:
            log.error(f"Failed to fill Step 3 row {row_index}: {e}")

    def _fill_row_dropdown(self, row_element, option_text):
        """Fill a mat-select dropdown within a specific table row."""
        try:
            selects = row_element.find_elements(
                By.CSS_SELECTOR, "mat-select"
            )
            for sel in selects:
                try:
                    if sel.is_displayed():
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({block:'center'});"
                            "arguments[0].click();",
                            sel,
                        )
                        self.wait_seconds(0.5)

                        # Try to find and click the option
                        try:
                            opt = self.driver.find_element(
                                By.XPATH,
                                f"//div[@role='listbox']//mat-option"
                                f"[contains(.,'{option_text}')]"
                            )
                            self.driver.execute_script(
                                "arguments[0].scrollIntoView({block:'center'});"
                                "arguments[0].click();",
                                opt,
                            )
                            self.wait_seconds(0.3)
                        except Exception:
                            # Try scrolling to find the option
                            opts = self.driver.find_elements(
                                By.CSS_SELECTOR,
                                "div[role='listbox'] mat-option"
                            )
                            for o in opts:
                                try:
                                    if option_text in o.text:
                                        self.driver.execute_script(
                                            "arguments[0].scrollIntoView({block:'center'});"
                                            "arguments[0].click();",
                                            o,
                                        )
                                        break
                                except Exception:
                                    continue

                        self._close_select_panel()
                        return
                except Exception:
                    continue
        except Exception as e:
            log.error(f"Failed to fill row dropdown: {e}")

    def _fill_row_dropdown_random(self, row_element, label_name):
        """Fill a mat-select dropdown within a specific table row with a random option.
        Returns the selected option text, or None if no options available.
        """
        try:
            selects = row_element.find_elements(
                By.CSS_SELECTOR, "mat-select"
            )
            for sel in selects:
                try:
                    if sel.is_displayed():
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({block:'center'});"
                            "arguments[0].click();",
                            sel,
                        )
                        self.wait_seconds(0.5)

                        # Read all options
                        opts = self.driver.find_elements(
                            By.CSS_SELECTOR,
                            "div[role='listbox'] mat-option, "
                            "div[role='listbox'] [role='option']",
                        )
                        option_texts = []
                        for opt in opts:
                            try:
                                t = opt.text.strip()
                                if t and t != "No results found" and not t.startswith("Select"):
                                    option_texts.append(t)
                            except Exception:
                                continue

                        if not option_texts:
                            log.warning(
                                f"No options in row '{label_name}' dropdown — skipping"
                            )
                            self._close_dropdown_panel_only()
                            return None

                        selected = random.choice(option_texts)
                        log.info(f"Random '{label_name}' selected in row: '{selected}'")

                        for opt in opts:
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
                        self._close_dropdown_panel_only()
                        return selected
                except Exception:
                    continue
        except Exception as e:
            log.error(f"Failed to fill row dropdown random: {e}")
        return None

    def _fill_row_text_input(self, row_element, field_name, value):
        """Fill a text input within a specific table row by field name.
        Uses JS fallback for Angular reactive form inputs.
        Field name matching uses the input's 'name' or 'placeholder' attribute.
        """
        try:
            inputs = row_element.find_elements(
                By.CSS_SELECTOR, "input"
            )
            for inp in inputs:
                try:
                    name_attr = inp.get_attribute("name") or ""
                    placeholder = inp.get_attribute("placeholder") or ""
                    if (
                        field_name.lower() in name_attr.lower()
                        or field_name.lower() in placeholder.lower()
                    ):
                        # Use JS fallback for Angular reactive form inputs
                        try:
                            inp.clear()
                            inp.send_keys(str(value))
                        except Exception:
                            self.driver.execute_script("""
                                var el = arguments[0];
                                var val = arguments[1];
                                el.focus();
                                var setter = Object.getOwnPropertyDescriptor(
                                    window.HTMLInputElement.prototype, 'value'
                                ).set;
                                setter.call(el, val);
                                el.dispatchEvent(new Event('input', {bubbles: true}));
                                el.dispatchEvent(new Event('change', {bubbles: true}));
                            """, inp, str(value))
                        self.wait_seconds(0.3)
                        return
                except Exception:
                    continue

            # Fallback: if we know the position, fill by index
            # Row structure: Packaging(dropdown), Packaging Capacity(input), Base Packaging Capacity(input)
            # But dropdowns are mat-select, not input, so inputs are: Capacity=0, Base Capacity=1
            visible_inputs = []
            for inp in inputs:
                try:
                    if inp.is_displayed() and inp.get_attribute("type") not in ("file", "checkbox"):
                        visible_inputs.append(inp)
                except Exception:
                    continue

            field_map = {
                "Packaging Capacity": 0,
                "Base Packaging Capacity": 1,
                "Capacity": 0,
                "Base Capacity": 1,
            }
            if field_name in field_map and field_map[field_name] < len(visible_inputs):
                idx = field_map[field_name]
                try:
                    visible_inputs[idx].clear()
                    visible_inputs[idx].send_keys(str(value))
                except Exception:
                    self.driver.execute_script("""
                        var el = arguments[0];
                        var val = arguments[1];
                        el.focus();
                        var setter = Object.getOwnPropertyDescriptor(
                            window.HTMLInputElement.prototype, 'value'
                        ).set;
                        setter.call(el, val);
                        el.dispatchEvent(new Event('input', {bubbles: true}));
                        el.dispatchEvent(new Event('change', {bubbles: true}));
                    """, visible_inputs[idx], str(value))
                self.wait_seconds(0.3)

        except Exception as e:
            log.error(f"Failed to fill row text input '{field_name}': {e}")

    def get_step3_row_count(self):
        """Get the number of rows in the Step 3 dynamic table."""
        try:
            rows = self.driver.find_elements(
                By.CSS_SELECTOR,
                "app-dynamic-details table.grid-table tbody tr"
            )
            visible_rows = [r for r in rows if r.is_displayed()]
            return len(visible_rows)
        except Exception:
            return 0

    # ==============================================================
    #  Full 3-step form fill
    # ==============================================================

    def fill_full_form(self, data):
        """Fill the entire 3-step Item Master form.
        data should have keys for all steps:
          step1: item_code, description, item_group, item_category, item_type,
                 item_attribute1-5, uom, hsn_sac_code, base_uom, base_uom_conversion,
                 status, is_critical, include_wip, is_packing_material (toggles)
          step2: attachment_type, file_path
          step3: rows/packaging_rows list
        Item Name is auto-generated from attributes — NOT typed manually.
        ONLY 3 toggles are filled in Step 1 (NOT 4! Verified 2026-05-18).
        "Allow Negative Stock" toggle DOES NOT EXIST in Item Master.
        Returns the auto-generated item name.
        """
        log.info("Filling full Item Master 3-step form...")

        # Step 1: Additional Details + ALL toggle switches
        step1_data = data.get("step1", data)
        auto_name = self.fill_step1(step1_data)

        # Navigate to Step 2
        self.click_stepper_next()
        self.wait_seconds(1)

        # Step 2: Define Item Master Details (Attachment Type + File Upload only — NO toggles)
        step2_data = data.get("step2", {})
        self.fill_step2(step2_data)

        # Navigate to Step 3
        self.click_stepper_next()
        self.wait_seconds(1)

        # Step 3: Product Order Packaging Details
        step3_data = data.get("step3", {})
        if step3_data:
            self.fill_step3(step3_data)

        log.info("Full 3-step form filled")
        return auto_name

    # ==============================================================
    #  Form submission & cancellation
    # ==============================================================

    def submit(self):
        """Click the Submit button on the final step of the stepper form."""
        log.info("Submitting Item Master form...")
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
                ".big-model button mat-icon, "
                "mat-dialog-container button mat-icon, "
                ".edit_pop_up button mat-icon",
            )
            for icon in close_btns:
                try:
                    if icon.text.strip().lower() == "close" and icon.is_displayed():
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

            try:
                confirm = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, ".swal2-confirm")
                    )
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
                    log.info(f"Success alert handled via JS: {msg}")
                except Exception:
                    log.warning("Could not click swal2-confirm")

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

    def handle_error_toast(self, timeout=10):
        """Check for error toast notification."""
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
            el = self.driver.find_element(By.CSS_SELECTOR, ".swal2-html-container")
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

    # ==============================================================
    #  Verification helpers
    # ==============================================================

    def is_add_form_open(self):
        """Check if the Add form popup is currently visible.
        Uses multi-strategy approach for the stepper form.
        """
        popup_visible = self._is_form_popup_open()
        name_input_visible = self.is_displayed(self.ITEM_NAME_INPUT, timeout=8)

        if name_input_visible:
            return True

        if popup_visible:
            # Check for stepper element inside popup
            try:
                steppers = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    "div.big-model mat-stepper, "
                    "mat-dialog-container mat-stepper, "
                    ".edit_pop_up mat-stepper"
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
                    "div.big-model input, "
                    "mat-dialog-container input, "
                    ".edit_pop_up input"
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

    def is_form_closed(self):
        """Check if the form popup is no longer visible."""
        popup_gone = not self._is_form_popup_open()
        if popup_gone:
            return True
        return not self.is_displayed(self.ITEM_NAME_INPUT, timeout=3)

    def get_form_heading(self):
        """Read the heading text of the current popup."""
        try:
            el = self.driver.find_element(
                By.CSS_SELECTOR,
                ".big-model h3, mat-dialog-container h3, "
                ".mat-mdc-dialog-title, .edit_pop_up h3",
            )
            return el.text.strip()
        except Exception:
            return ""

    def is_view_mode(self):
        """Check if the currently open form is in View (read-only) mode.
        View mode: all inputs disabled, no Submit/Update buttons.
        """
        try:
            name_input = self.find_visible_element(self.ITEM_NAME_INPUT, timeout=5)
            return not name_input.is_enabled()
        except Exception:
            return False

    def is_edit_mode(self):
        """Check if the currently open form is in Edit mode
        (Update button visible).
        """
        return self.is_displayed(self.UPDATE_BUTTON, timeout=5)

    def get_form_field_values_step1(self):
        """Read all Step 1 form field values from the currently open popup.
        Returns a dict with all Step 1 field values.
        """
        values = {}

        # Text inputs
        for key, locator in [
            ("item_name", self.ITEM_NAME_INPUT),
            ("item_code", self.ITEM_CODE_INPUT),
            ("description", self.DESCRIPTION_INPUT),
            ("base_uom_conversion", self.BASE_UOM_CONVERSION_INPUT),
        ]:
            try:
                el = self.driver.find_element(By.CSS_SELECTOR, locator[1])
                values[key] = el.get_attribute("value") or ""
            except Exception:
                values[key] = ""

        # Dropdown selects — read the displayed text (V2: Category before Group per fill order)
        for key, locator in [
            ("item_category", self.ITEM_CATEGORY_SELECT),
            ("item_group", self.ITEM_GROUP_SELECT),
            ("item_type", self.ITEM_TYPE_SELECT),
            ("item_attribute1", self.ITEM_ATTRIBUTE1_SELECT),
            ("item_attribute2", self.ITEM_ATTRIBUTE2_SELECT),
            ("item_attribute3", self.ITEM_ATTRIBUTE3_SELECT),
            ("item_attribute4", self.ITEM_ATTRIBUTE4_SELECT),
            ("item_attribute5", self.ITEM_ATTRIBUTE5_SELECT),
            ("uom", self.UOM_SELECT),
            ("hsn_sac_code", self.HSN_SAC_CODE_SELECT),
            ("base_uom", self.BASE_UOM_SELECT),
        ]:
            try:
                el = self.driver.find_element(By.XPATH, locator[1])
                values[key] = el.text.strip()
            except Exception:
                values[key] = ""

        # Toggle switches (ALL on Step 1 — verified 2026-05-15)
        for key, locator in [
            ("status", self.STATUS_TOGGLE),
            ("is_critical", self.IS_CRITICAL_TOGGLE),
            ("include_wip", self.INCLUDE_WIP_TOGGLE),
            ("is_packing_material", self.IS_PACKING_MATERIAL_TOGGLE),
        ]:
            values[key] = self.get_toggle_state(locator, key)

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

    def get_all_item_names(self):
        """Return a list of all item names in the current table view."""
        cells = self.driver.find_elements(
            By.CSS_SELECTOR,
            "table#excel-table tbody td.cdk-column-itemName, "
            "table#excel-table tbody td.mat-column-itemName, "
            "table#excel-table tbody td.cdk-column-item_name, "
            "table#excel-table tbody td.mat-column-item_name, "
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

    def is_item_in_table(self, item_name):
        """Check if an item with the given name appears in the table."""
        names = self.get_all_item_names()
        return any(item_name.strip().lower() in n.lower() for n in names)

    def find_item_row_index(self, item_name):
        """Find the 0-based row index for an item by name.
        Returns -1 if not found.
        """
        rows = self.driver.find_elements(
            By.CSS_SELECTOR, "table#excel-table tbody tr"
        )
        for i, row in enumerate(rows):
            try:
                cells = row.find_elements(By.TAG_NAME, "td")
                for cell in cells:
                    if item_name.strip().lower() in cell.text.strip().lower():
                        return i
            except StaleElementReferenceException:
                continue
        return -1

    def get_item_details_from_row(self, row_index=0):
        """Read text from a table row. Returns dict with
        item_name, uom, status.
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
            result["item_name"] = data_cells[0].text.strip()
        if len(data_cells) >= 2:
            result["uom"] = data_cells[1].text.strip()
        if len(data_cells) >= 3:
            result["status"] = data_cells[2].text.strip()
        return result

    # ==============================================================
    #  Row action buttons — JS click via _click_action_button
    # ==============================================================

    def _click_action_button(self, item_name, action_xpath_template):
        """Click a row action button (View/Edit/History) using
        parametrised XPath. Falls back to index-based button click.
        Pure JS click to avoid overlay interception.
        """
        self._force_close_panels()
        xpath = action_xpath_template.format(item_name=item_name)

        # Strategy 1: Parametrised XPath
        try:
            btns = self.driver.find_elements(By.XPATH, xpath)
            for btn in btns:
                try:
                    if btn.is_displayed():
                        self.driver.execute_script("arguments[0].click();", btn)
                        self.wait_seconds(1)
                        return True
                except Exception:
                    continue
        except Exception:
            pass

        # Strategy 2: Find row by name, click button by index
        row_idx = self.find_item_row_index(item_name)
        if row_idx >= 0:
            return self._click_action_button_by_index(
                row_idx, action_xpath_template
            )

        log.warning(f"Action button not found for item: {item_name}")
        return False

    def _click_action_button_by_index(self, row_index, action_xpath_template):
        """Fallback: click action button by row index position."""
        rows = self.driver.find_elements(
            By.CSS_SELECTOR, "table#excel-table tbody tr"
        )
        if row_index >= len(rows):
            raise Exception(
                f"Row index {row_index} out of range (total rows: {len(rows)})"
            )
        row = rows[row_index]
        btns = row.find_elements(By.CSS_SELECTOR, "button")

        # Determine which button based on the template keyword
        # Order: View(0), Edit(1), History/Archive(2)
        if "cdk-column-view" in action_xpath_template:
            idx = 0
        elif "cdk-column-edit" in action_xpath_template:
            idx = 1
        elif "cdk-column-archive" in action_xpath_template:
            idx = 2
        else:
            idx = 0

        if idx < len(btns):
            self.driver.execute_script("arguments[0].click();", btns[idx])
            self.wait_seconds(1)
            return True
        raise Exception(
            f"Action button index {idx} not found in row {row_index}"
        )

    def click_view_button(self, item_name=None, row_index=0):
        """Click the View button for an item row."""
        log.info(f"Clicking View button for: {item_name or row_index}...")
        if item_name:
            return self._click_action_button(item_name, self.VIEW_BUTTON[1])
        return self._click_action_button_by_index(
            row_index, self.VIEW_BUTTON[1]
        )

    def click_edit_button(self, item_name=None, row_index=0):
        """Click the Edit button for an item row."""
        log.info(f"Clicking Edit button for: {item_name or row_index}...")
        if item_name:
            return self._click_action_button(item_name, self.EDIT_BUTTON[1])
        return self._click_action_button_by_index(
            row_index, self.EDIT_BUTTON[1]
        )

    def click_history_button(self, item_name=None, row_index=0):
        """Click the History button for an item row.
        NOTE: Item Master uses 'archive' column class, not 'history'.
        """
        log.info(f"Clicking History button for: {item_name or row_index}...")
        if item_name:
            return self._click_action_button(item_name, self.HISTORY_BUTTON[1])
        return self._click_action_button_by_index(
            row_index, self.HISTORY_BUTTON[1]
        )

    # ==============================================================
    #  View & Edit specific verifications
    # ==============================================================

    def verify_view_popup_read_only(self):
        """Verify that the View popup fields are read-only / disabled.
        For the stepper form, checks Step 1 fields.
        Returns True if all checked fields are non-editable.
        """
        log.info("Verifying View popup is read-only...")
        all_readonly = True

        try:
            name_input = self.find_visible_element(self.ITEM_NAME_INPUT, timeout=5)
            if name_input.is_enabled():
                all_readonly = False
                log.warning("Item Name field is editable in View mode")
        except Exception:
            pass

        try:
            code_input = self.find_visible_element(self.ITEM_CODE_INPUT, timeout=5)
            if code_input.is_enabled():
                all_readonly = False
                log.warning("Item Code field is editable in View mode")
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

    def search_item(self, item_name):
        """Search for an item by name in the table search bar.
        Returns True if the item is found in the table results.
        """
        log.info(f"Searching for item: {item_name}")
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
                item_name,
            )
            self.wait_seconds(3)

            # Check results — retry a few times
            found = False
            for _ in range(3):
                found = self.is_item_in_table(item_name)
                if found:
                    break
                self.wait_seconds(2)
            if found:
                log.info(f"Item found in table: {item_name}")
            else:
                log.warning(f"Item NOT found in table: {item_name}")
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
                search_input.send_keys(Keys.RETURN)
                self.wait_seconds(1)
        except Exception:
            pass

    def verify_item_exists(self, item_name):
        """Navigate to page, search, and verify an item exists."""
        self.navigate_to_page()
        found = self.search_item(item_name)
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
            ".big-model table tbody tr, mat-dialog-container table tbody tr",
        )
        return len(rows)

    def get_history_data(self):
        """Read all data from the history popup table.
        Returns a list of dicts, one per row.
        """
        rows = self.driver.find_elements(
            By.CSS_SELECTOR,
            ".big-model table tbody tr, mat-dialog-container table tbody tr",
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
            search_inputs = self.driver.find_elements(
                By.CSS_SELECTOR,
                ".big-model input, mat-dialog-container input",
            )
            for inp in search_inputs:
                try:
                    if inp.is_displayed():
                        inp.clear()
                        inp.send_keys(search_text)
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

        # Strategy 1: JS click the Cancel/Close button
        try:
            self.driver.execute_script("""
                var btns = document.querySelectorAll('.popup-footer button');
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

        # Strategy 2: JS click the X icon
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

        # Strategy 3: JS force remove
        try:
            self.driver.execute_script("""
                document.querySelectorAll('.cdk-overlay-pane').forEach(
                    function(el) { el.remove(); }
                );
                document.querySelectorAll('.cdk-overlay-backdrop').forEach(
                    function(el) { el.remove(); }
                );
            """)
            self.wait_seconds(0.5)
        except Exception:
            pass

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
        try:
            opt_locator = (
                "xpath",
                f"//div[@role='listbox']//mat-option"
                f"[contains(.,'{option_text}')]",
            )
            self.click_with_retry(opt_locator)
        except Exception:
            try:
                opt_locator2 = (
                    "xpath",
                    f"//div[@role='listbox']//div[@role='option']"
                    f"[contains(.,'{option_text}')]",
                )
                self.click_with_retry(opt_locator2)
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
            log.warning(f"No options loaded in '{label_name}' dropdown — skipping")
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
            log.warning(f"No valid options in '{label_name}' dropdown — skipping")
            self._close_dropdown_panel_only()
            return None

        if exclude:
            option_texts = [t for t in option_texts if t not in exclude]
            if not option_texts:
                log.warning(
                    f"No remaining options in '{label_name}' after excluding — skipping"
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
            log.warning("Timed out waiting for dropdown options to become visible")

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

    def create_item(self, item_data):
        """One-call item creation through the 3-step stepper form.
        item_data can be:
          - Flat dict with all keys (step1 fields at top level)
          - Nested dict with 'step1', 'step2', 'step3' keys
        Item Name is auto-generated from attribute values — stored in
        item_data['_auto_item_name'] and result['item_name'].
        Returns result dict: status, error, message, data, item_name.
        """
        log.info(f"Creating Item Master...")
        result = {
            "status": "FAILED",
            "error": "",
            "message": "",
            "data": copy.deepcopy(item_data),
            "item_name": "",  # Will be set to auto-generated name
        }

        try:
            self.open_add_form()
            if not self.is_add_form_open():
                raise Exception("Add form did not open")

            # Fill the full 3-step form — returns auto-generated name
            auto_name = self.fill_full_form(item_data)
            result["item_name"] = auto_name or item_data.get("_auto_item_name", "")
            log.info(f"Auto-generated Item Name: '{result['item_name']}'")

            # Submit on the final step
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
                        result["error"] = "No success message and dialog did not close"
        except Exception as e:
            result["error"] = str(e)
            log.error(f"Failed to create item: {e}")

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

    def edit_item(self, item_name, updated_data, row_index=0):
        """One-call item edit. Clicks Edit, fills changed fields,
        clicks Update.
        Returns result dict: status, error, message.
        """
        log.info(f"Editing Item Master: {item_name}")
        result = {"status": "FAILED", "error": "", "message": ""}

        try:
            if not self.is_item_in_table(item_name):
                self.search_item(item_name)
                self.wait_seconds(1)

            self.click_edit_button(item_name=item_name, row_index=row_index)
            self.wait_seconds(1)

            if not self.is_edit_mode():
                raise Exception("Edit form did not open (no Update button)")

            # Fill the updated data through the stepper
            self.fill_full_form(updated_data)

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
            log.error(f"Failed to edit item '{item_name}': {e}")

        IM_SUBMISSIONS.append(result)
        return result

    def view_item(self, item_name=None, row_index=0):
        """One-call item view. Clicks View, reads fields,
        closes popup. Returns dict of field values.
        """
        log.info(f"Viewing item: {item_name or row_index}")
        try:
            self.click_view_button(item_name=item_name, row_index=row_index)
            self.wait_seconds(1)
            values = self.get_form_field_values_step1()
            log.info(f"Item details: {values}")
            self.close_popup()
            self.wait_seconds(0.5)
            return values
        except Exception as e:
            log.error(f"Failed to view item: {e}")
            return None

    def check_history(self, item_name=None, row_index=0, search_text=None):
        """One-call history check. Opens History, reads row count,
        optionally searches, then closes popup.
        """
        log.info(f"Checking history for: {item_name or row_index}")
        result = {
            "row_count": 0,
            "search_found": None,
            "data": [],
            "error": "",
        }

        try:
            if item_name and not self.is_item_in_table(item_name):
                self.search_item(item_name)
                self.wait_seconds(1)

            self.click_history_button(
                item_name=item_name, row_index=row_index
            )
            self.wait_seconds(1.5)

            result["row_count"] = self.get_history_row_count()
            result["data"] = self.get_history_data()

            if search_text:
                result["search_found"] = self.search_in_history(search_text)

            self.close_history_popup()
            self.wait_seconds(0.5)

        except Exception as e:
            result["error"] = str(e)

        return result

    # ==============================================================
    #  Bulk creation
    # ==============================================================

    def create_bulk_items(self, items_list, on_progress=None):
        """Create multiple items in sequence.
        Returns list of result dicts.
        """
        total = len(items_list)
        results = []

        for i, idata in enumerate(items_list, 1):
            name = idata.get("item_name", idata.get("step1", {}).get("item_name", f"Item_{i}"))
            log.info(f"[{i}/{total}] Creating: {name}")
            start_time = time.time()
            result = self.create_item(idata)
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
        log.info(f" BULK COMPLETE: {passed}/{total} passed, {failed} failed")
        log.separator()
        return results

    # ==============================================================
    #  Screenshot helper
    # ==============================================================

    def take_screenshot(self, filename):
        """Take a screenshot and save to the screenshots directory."""
        screenshots_dir = os.path.join(os.path.dirname(__file__), "screenshots")
        os.makedirs(screenshots_dir, exist_ok=True)
        filepath = os.path.join(screenshots_dir, filename)
        self.driver.save_screenshot(filepath)
        log.info(f"Screenshot saved: {filepath}")
        return filepath