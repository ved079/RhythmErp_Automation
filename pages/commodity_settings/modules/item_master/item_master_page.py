"""
item_master_page.py  (V3 — Optimised)
--------------------------------------
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
    - Item Sourcing          (mat-select,   required, searchable) ← NEW V3 field
    - UOM                    (mat-select,   required, searchable)
    - HSN SAC Code           (mat-select,   required, searchable)
    - Base Uom               (mat-select,   required, searchable)
    - Base Uom Conversion    (text input,   required, numeric)
    *** PLUS 4 TOGGLE SWITCHES (visible on Step 1): ***
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
  - Actions                (3-dot menu ⋮ in cdk-column-actions — NOT separate View/Edit/History columns)
  - Item Name
  - UOM
  - Status

V3 OPTIMISATIONS (aligned with UOM golden code patterns):
  - ACTION BUTTONS: 3-dot menu (more_vert icon) replaces separate View/Edit/History columns
  - JS-first clicks for ALL buttons — bypasses overlay/z-index issues
  - hard_refresh() for fast page reset between tests (instead of navigate_to_page)
  - search_and_verify() combines search + existence check (UOM pattern)
  - _click_action_menu_item() for 3-dot menu actions (UOM pattern)
  - _js_click_popup_button() for Submit/Update (UOM pattern)
  - handle_success_alert() with short timeout (3s) and JS confirm click (UOM pattern)
  - handle_validation_warning() / handle_validation_download() (UOM patterns A & B)
  - is_validation_alert_present() with fast polling (0.2s intervals)
  - dismiss_any_validation_alert() — try Cancel first, then OK
  - get_field_value() via JS (UOM pattern)
  - get_mat_error_text() with field_locator parameter (UOM pattern)
  - has_field_error() via JS (UOM pattern)
  - is_add_form_open() via JS-only check (UOM pattern)
  - force_close_form_popup() via JS (UOM pattern)
  - close_popup() via JS (UOM pattern)
  - _cleanup() helper — close form if open, then hard refresh
  - Replaced most time.sleep() with WebDriverWait where possible

KEY RULES (V3 — carried forward from V2):
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
  - CRITICAL: Browser-clicked mat-select options do NOT update Angular reactive form model.
    Must use JS value-setter + dispatchEvent for all dropdown selections.
    The _select_mat_option method must trigger Angular change detection.
"""

import os
import sys
import time
import random
import copy
import json

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
    SEARCH_INPUT = ("css", "input.search-bar-input, input#erpSearchInput, .erp-search-wrapper input")
    SEARCH_SUBMIT = ("css", "button.erp-outline-btn, button.search-btn")

    # ==============================================================
    #  LOCATORS — Table (main listing)
    # ==============================================================
    TABLE = ("css", "table#excel-table")
    TABLE_ROWS = ("css", "table#excel-table tbody tr")
    TABLE_NAME_CELLS = (
        "css",
        "table#excel-table tbody td.cdk-column-name, "
        "table#excel-table tbody td.mat-column-name, "
        "table#excel-table tbody td.cdk-column-itemName, "
        "table#excel-table tbody td.mat-column-itemName, "
        "table#excel-table tbody td.cdk-column-item_name, "
        "table#excel-table tbody td.mat-column-item_name, "
        "table#excel-table tbody td:nth-child(2)",
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

    # V3: Action column — 3-dot menu (same pattern as UOM)
    ACTIONS_COLUMN = ("css", "td.cdk-column-actions")
    THREE_DOT_MENU_BUTTON = ("css", "td.cdk-column-actions button")

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
    )
    ITEM_CODE_INPUT = (
        "css",
        "input[formcontrolname='code'], input[name='Item Code'], "
        "input[name='itemCode']",
    )
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

    # V3: Item Sourcing — NEW required field in Step 1
    ITEM_SOURCING_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Item Sourcing')]"
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
    #  LOCATORS — Row action buttons
    #  V3: Now uses 3-dot menu in cdk-column-actions (same as UOM)
    #  The old separate VIEW/EDIT/HISTORY button locators are kept
    #  for backward compat but the click methods now delegate to
    #  _click_action_menu_item()
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

    def hard_refresh(self):
        """Hard refresh the current page (Ctrl+R) and wait for it to be ready.
        Much faster than full navigate_to_page() for resetting between tests.
        UOM golden pattern.
        """
        log.info("Hard refreshing Item Master page")
        self.driver.refresh()
        self._wait_for_page_ready()
        log.info("Page refreshed and ready")

    def _wait_for_page_ready(self):
        """Wait until the Item Master page is fully loaded.
        V4: Check for table first, then fallback to search input (new or old selector).
        """
        try:
            WebDriverWait(self.driver, 15).until(
                lambda d: d.find_elements("css selector", "table#excel-table")
            )
            log.info("Item Master page ready (table found)")
        except Exception:
            # Fallback: check for search input (new UI)
            try:
                WebDriverWait(self.driver, 5).until(
                    lambda d: d.find_elements("css selector", "input.search-bar-input, button.search-btn, button.erp-outline-btn")
                )
                log.info("Item Master page ready (search element found, no table)")
            except Exception:
                log.warning("Item Master page ready check timed out")

    def is_page_loaded(self):
        """Check if the Item Master listing page has loaded."""
        return self.is_displayed(self.TABLE, timeout=10)

    # ==============================================================
    #  Overlay cleanup — NEVER use Keys.ESCAPE
    # ==============================================================

    def _force_close_panels(self):
        """Remove ALL select overlay panes from the DOM via JS.
        UOM golden pattern: removes all CDK overlay panes and backdrops.
        """
        self.driver.execute_script("""
            document.querySelectorAll('.cdk-overlay-backdrop').forEach(function(el) { el.remove(); });
            document.querySelectorAll('.cdk-overlay-pane').forEach(function(el) { el.remove(); });
        """)

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
                        time.sleep(0.3)
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
        V3: UOM golden pattern — JS-first click, Selenium fallback.
        """
        log.info("Opening Add Item Master form")
        # JS click — bypasses overlay/z-index issues
        js_click_add = """
        var btn = document.querySelector('button.erp-add-btn');
        if (!btn) { throw new Error('Add button not found in DOM'); }
        btn.scrollIntoView({block:'center'});
        btn.click();
        return 'clicked';
        """
        try:
            result = self.driver.execute_script(js_click_add)
            log.info("Add button clicked via JS: " + str(result))
        except Exception as e:
            log.warning("JS click failed, falling back to Selenium click: " + str(e))
            self.click_with_retry(self.ADD_BUTTON)
        # Wait for the form popup to appear
        try:
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located(("css selector", "input[formcontrolname='name']"))
            )
            log.info("Add form opened")
        except Exception:
            log.warning("Add form may not have opened — Item Name input not found")

    def click_refresh(self):
        """Click the Refresh button via JS."""
        log.info("Clicking Refresh button...")
        try:
            self.driver.execute_script("""
                var btns = document.querySelectorAll('button.mat-mdc-mini-fab');
                for (var i = 0; i < btns.length; i++) {
                    var icon = btns[i].querySelector('mat-icon');
                    if (icon && icon.textContent.trim().toLowerCase() === 'refresh') {
                        btns[i].click();
                        return 'clicked';
                    }
                }
                return 'not found';
            """)
            log.info("Refresh clicked via JS")
        except Exception:
            log.warning("Refresh button not found")

    # ==============================================================
    #  Stepper navigation
    # ==============================================================

    def click_stepper_next(self):
        """Click the 'Next' button on the current stepper step
        to advance to the next step. JS-first approach.
        """
        log.info("Clicking stepper Next button...")
        self._force_close_panels()

        # JS-first: find and click any Next button inside the popup
        try:
            result = self.driver.execute_script("""
                var btns = document.querySelectorAll(
                    '.big-model button, mat-dialog-container button, '
                    + '.edit_pop_up button'
                );
                for (var i = 0; i < btns.length; i++) {
                    if (btns[i].textContent.trim() === 'Next'
                        || btns[i].classList.contains('mat-stepper-next')
                        || btns[i].classList.contains('mat-mdc-stepper-next')) {
                        btns[i].scrollIntoView({block:'center'});
                        btns[i].click();
                        return 'clicked';
                    }
                }
                return 'not found';
            """)
            if result == 'clicked':
                time.sleep(0.5)
                log.info("Stepper Next clicked via JS")
                return True
        except Exception:
            pass

        # Fallback: Selenium CSS class search
        try:
            next_btns = self.driver.find_elements(
                By.CSS_SELECTOR,
                "button.mat-stepper-next, button.mat-mdc-stepper-next"
            )
            for btn in next_btns:
                try:
                    if btn.is_displayed() and btn.is_enabled():
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({block:'center'});"
                            "arguments[0].click();",
                            btn,
                        )
                        time.sleep(0.5)
                        log.info("Stepper Next clicked via CSS class fallback")
                        return True
                except Exception:
                    continue
        except Exception:
            pass

        log.warning("Stepper Next button not found or not clickable")
        return False

    def click_stepper_back(self):
        """Click the 'Back' button on the current stepper step
        to go back to the previous step. JS-first approach.
        """
        log.info("Clicking stepper Back button...")
        self._force_close_panels()

        # JS-first
        try:
            result = self.driver.execute_script("""
                var btns = document.querySelectorAll(
                    '.big-model button, mat-dialog-container button, '
                    + '.edit_pop_up button'
                );
                for (var i = 0; i < btns.length; i++) {
                    if (btns[i].textContent.trim() === 'Back'
                        || btns[i].classList.contains('mat-stepper-previous')
                        || btns[i].classList.contains('mat-mdc-stepper-previous')) {
                        btns[i].scrollIntoView({block:'center'});
                        btns[i].click();
                        return 'clicked';
                    }
                }
                return 'not found';
            """)
            if result == 'clicked':
                time.sleep(0.5)
                log.info("Stepper Back clicked via JS")
                return True
        except Exception:
            pass

        # Fallback: Selenium CSS class search
        try:
            back_btns = self.driver.find_elements(
                By.CSS_SELECTOR,
                "button.mat-stepper-previous, button.mat-mdc-stepper-previous"
            )
            for btn in back_btns:
                try:
                    if btn.is_displayed() and btn.is_enabled():
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({block:'center'});"
                            "arguments[0].click();",
                            btn,
                        )
                        time.sleep(0.5)
                        log.info("Stepper Back clicked via CSS class fallback")
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
                time.sleep(1)
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
        V3: Added Item Sourcing field (required combobox in Step 1).
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
            # Base Uom Conversion may be readonly initially — remove readonly via JS first
            self.driver.execute_script("""
                var el = document.querySelector(
                    "input[name='Base Uom Conversion'], " +
                    "input[formcontrolname='baseUomConversion'], " +
                    "input[name='baseUomConversion']"
                );
                if (el && el.hasAttribute('readonly')) {
                    el.removeAttribute('readonly');
                }
            """)
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

        # V3: Item Sourcing — NEW required field, added after HSN SAC Code
        self._fill_dropdown_if_provided(
            data, "item_sourcing", self.ITEM_SOURCING_SELECT, "Item Sourcing"
        )

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

        time.sleep(0.5)

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
                        time.sleep(1)
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
                time.sleep(0.5)
                file_inputs = self.driver.find_elements(
                    By.CSS_SELECTOR, "input[type='file']"
                )
                for inp in file_inputs:
                    try:
                        inp.send_keys(file_path)
                        time.sleep(1)
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

        # JS-first approach
        try:
            result = self.driver.execute_script("""
                var btns = document.querySelectorAll(
                    'app-dynamic-details button[mat-icon-button], '
                    + 'app-dynamic-details button.mat-mdc-icon-button'
                );
                for (var i = 0; i < btns.length; i++) {
                    var icon = btns[i].querySelector('mat-icon');
                    if (icon && icon.textContent.trim().toLowerCase() === 'add') {
                        btns[i].scrollIntoView({block:'center'});
                        btns[i].click();
                        return 'clicked';
                    }
                }
                return 'not found';
            """)
            if result == 'clicked':
                time.sleep(1)
                log.info("Add Row clicked via JS")
                return
        except Exception:
            pass

        # Fallback: Button with 'Add Row' text
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
                        time.sleep(1)
                        log.info("Add Row clicked via text match")
                        return
                except Exception:
                    continue
        except Exception:
            pass

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
                        time.sleep(0.5)

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
                            time.sleep(0.3)
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
                        time.sleep(0.5)

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

                        time.sleep(0.3)
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
                        time.sleep(0.3)
                        return
                except Exception:
                    continue

            # Fallback: if we know the position, fill by index
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
                time.sleep(0.3)

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
                 item_attribute1-5, item_sourcing, uom, hsn_sac_code, base_uom,
                 base_uom_conversion, status, is_critical, include_wip,
                 is_packing_material (toggles)
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
        time.sleep(0.5)

        # Step 2: Define Item Master Details (Attachment Type + File Upload only — NO toggles)
        step2_data = data.get("step2", {})
        self.fill_step2(step2_data)

        # Navigate to Step 3
        self.click_stepper_next()
        time.sleep(0.5)

        # Step 3: Product Order Packaging Details
        step3_data = data.get("step3", {})
        if step3_data:
            self.fill_step3(step3_data)

        log.info("Full 3-step form filled")
        return auto_name

    # ==============================================================
    #  Form submission & cancellation — V3: UOM golden patterns
    # ==============================================================

    def submit(self):
        """Click the Submit button on the final step of the stepper form.
        V3: Uses _js_click_popup_button() from UOM pattern.
        """
        log.info("Submitting Item Master form...")
        self._force_close_panels()
        self._js_click_popup_button('Submit')

    def click_update(self):
        """Click the Update button on the Edit form.
        V3: Uses _js_click_popup_button() from UOM pattern.
        """
        log.info("Clicking Update button...")
        self._force_close_panels()
        self._js_click_popup_button('Update')

    def cancel(self):
        """Click the Cancel button on the form via JS."""
        log.info("Clicking Cancel button...")
        self.driver.execute_script("""
            var footers = document.querySelectorAll('.popup-footer');
            for (var i = 0; i < footers.length; i++) {
                var buttons = footers[i].querySelectorAll('button');
                for (var j = 0; j < buttons.length; j++) {
                    if (buttons[j].textContent.indexOf('Cancel') !== -1) {
                        buttons[j].click();
                        return 'clicked';
                    }
                }
            }
            return 'not found';
        """)
        time.sleep(1)

    def close_popup(self):
        """Close any popup by clicking Cancel button via JS.
        V3: UOM golden pattern — pure JS click on popup-footer Cancel.
        """
        log.info("Closing popup")
        self.driver.execute_script("""
            var footers = document.querySelectorAll('.popup-footer');
            for (var i = 0; i < footers.length; i++) {
                var buttons = footers[i].querySelectorAll('button');
                for (var j = 0; j < buttons.length; j++) {
                    if (buttons[j].textContent.indexOf('Cancel') !== -1) {
                        buttons[j].click();
                        return 'clicked';
                    }
                }
            }
            return 'not found';
        """)

    def _js_click_popup_button(self, button_text):
        """Click a popup footer button (Submit/Update) via JS — bypasses overlay issues.
        UOM golden pattern.
        """
        js = """
        var footers = document.querySelectorAll('.popup-footer');
        for (var i = 0; i < footers.length; i++) {
            var buttons = footers[i].querySelectorAll('button');
            for (var j = 0; j < buttons.length; j++) {
                if (buttons[j].textContent.trim().indexOf(arguments[0]) !== -1) {
                    buttons[j].scrollIntoView({block:'center'});
                    buttons[j].click();
                    return 'clicked_' + arguments[0];
                }
            }
        }
        throw new Error('Button "' + arguments[0] + '" not found in popup footer');
        """
        try:
            result = self.driver.execute_script(js, button_text)
            log.info("JS click " + button_text + ": " + str(result))
            time.sleep(0.5)
        except Exception as e:
            log.warning("JS click failed for " + button_text + ", falling back to Selenium: " + str(e))
            if button_text == 'Submit':
                self.click_with_retry(self.SUBMIT_BUTTON)
            elif button_text == 'Update':
                self.click_with_retry(self.UPDATE_BUTTON)

    # ==============================================================
    #  SweetAlert2 handlers — V3: UOM golden patterns
    # ==============================================================

    def handle_success_alert(self, timeout=3):
        """Handle SweetAlert2 success notification — fast dismiss.
        V3: UOM golden pattern — short timeout (3s), JS click confirm,
        wait for disappear.
        Returns the alert message text, or '' if no alert appeared.
        """
        log.info("Handling success alert")
        # SweetAlert appears almost instantly — check with short timeout
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(("css selector", ".swal2-container"))
            )
            # Read the title
            msg = ""
            try:
                title_el = self.driver.find_element(
                    By.CSS_SELECTOR, "#swal2-title"
                )
                msg = title_el.text.strip()
            except Exception:
                pass

            log.info("SweetAlert detected, dismissing via JS")
            # Click confirm button via JS (fast, bypasses overlay)
            self.driver.execute_script("""
                var btn = document.querySelector('.swal2-confirm');
                if (btn) { btn.click(); return 'clicked'; }
                return 'not found';
            """)
            # Wait for SweetAlert to disappear (short wait)
            try:
                WebDriverWait(self.driver, 3).until(
                    EC.invisibility_of_element_located(("css selector", ".swal2-container"))
                )
            except Exception:
                pass
            log.info(f"Success alert handled: {msg}")
            return msg
        except Exception:
            log.info("No SweetAlert found (may have auto-dismissed)")
            return ""

    def handle_validation_warning(self):
        """Pattern A: Dismiss 'Please correct the highlighted fields' via JS click OK.
        UOM golden pattern.
        """
        log.info("Handling validation warning (Pattern A)")
        self._dismiss_swal(button=".swal2-confirm", label="OK")

    def handle_validation_download(self):
        """Pattern B: Dismiss 'Fields validation failed' via JS click Cancel.
        UOM golden pattern.
        """
        log.info("Handling validation download (Pattern B)")
        self._dismiss_swal(button=".swal2-cancel", label="Cancel")

    def handle_error_toast(self, timeout=3):
        """Check for error toast notification.
        DEPRECATED — kept for backward compatibility.
        """
        log.warning("handle_error_toast is DEPRECATED. Pattern C no longer exists on live system.")
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(("css selector", ".swal2-popup.swal2-icon-error"))
            )
            try:
                WebDriverWait(self.driver, 5).until(
                    EC.invisibility_of_element_located(("css selector", ".swal2-popup.swal2-icon-error"))
                )
            except Exception:
                pass
        except Exception:
            pass

    def is_validation_alert_present(self, timeout=3):
        """Check if any SweetAlert validation popup is visible.
        V3: UOM golden pattern — fast poll (0.2s intervals).
        """
        end_time = time.monotonic() + timeout
        while time.monotonic() < end_time:
            try:
                visible = self.driver.execute_script("""
                    var el = document.querySelector('.swal2-popup.swal2-icon-warning, .swal2-popup.swal2-icon-error');
                    return el && el.offsetParent !== null;
                """)
                if visible:
                    return True
            except Exception:
                pass
            time.sleep(0.2)
        return False

    def dismiss_any_validation_alert(self):
        """Dismiss any SweetAlert validation popup — try Cancel first (Pattern B), then OK (Pattern A).
        UOM golden pattern.
        """
        log.info("Dismissing any validation alert")
        self.driver.execute_script("""
            var cancel = document.querySelector('.swal2-cancel');
            if (cancel) { cancel.click(); return 'Cancel'; }
            var confirm = document.querySelector('.swal2-confirm');
            if (confirm) { confirm.click(); return 'OK'; }
            return 'none';
        """)
        # Wait for SweetAlert to disappear
        try:
            WebDriverWait(self.driver, 2).until(
                EC.invisibility_of_element_located(("css selector", ".swal2-popup"))
            )
        except Exception:
            pass

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

    def _dismiss_swal(self, button, label):
        """Dismiss a SweetAlert popup by clicking the specified button via JS.
        UOM golden pattern.
        """
        try:
            self.driver.find_element("css selector", ".swal2-popup")
            self.driver.execute_script("""
                var btn = document.querySelector(arguments[0]);
                if (btn) { btn.click(); }
            """, button)
            log.info("Dismissed SweetAlert via " + label)
            try:
                WebDriverWait(self.driver, 2).until(
                    EC.invisibility_of_element_located(("css selector", ".swal2-popup"))
                )
            except Exception:
                pass
        except Exception as e:
            log.warning("No SweetAlert to dismiss: " + str(e))

    # ==============================================================
    #  Field-level error checking — V3: UOM golden patterns
    # ==============================================================

    def get_mat_error_text(self, field_locator=None):
        """Get the mat-error text below a form field.
        V3: UOM golden pattern — uses pure JS (no Selenium find_element)
        to avoid locator issues. Accepts optional field_locator parameter.
        If field_locator is None, returns all visible mat-error texts.
        """
        if field_locator is None:
            # Original V2 behavior: return all visible mat-error texts
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

        # V3: UOM pattern with field_locator parameter
        try:
            css_selector = field_locator[1] if field_locator[0] == "css" else ""
            if not css_selector:
                return ""
            js = """
            var input = document.querySelector(arguments[0]);
            if (!input) return JSON.stringify({found: false, reason: 'input not found'});
            var current = input;
            for (var steps = 0; steps < 20; steps++) {
                var errors = current.querySelectorAll('mat-error');
                if (errors.length > 0) {
                    var texts = [];
                    for (var i = 0; i < errors.length; i++) {
                        var t = errors[i].textContent.trim();
                        if (t) texts.push(t);
                    }
                    return JSON.stringify({found: true, errorText: texts.join(' | ')});
                }
                current = current.parentElement;
                if (!current || current === document.body) break;
            }
            var chain = [];
            current = document.querySelector(arguments[0]);
            for (var d = 0; d < 15; d++) {
                if (!current || current === document.body) break;
                chain.push(current.tagName + '.' + (current.className || '').substring(0, 40).split(' ')[0]);
                current = current.parentElement;
            }
            return JSON.stringify({found: false, chain: chain.join(' > ')});
            """
            result = self.driver.execute_script(js, css_selector)
            log.info("get_mat_error_text raw: " + str(result))
            if not result:
                return ""
            data = json.loads(result)
            if data.get("found"):
                return data.get("errorText", "")
            else:
                log.warning("mat-error not found. Chain: " + data.get("chain", data.get("reason", "unknown")))
                return ""
        except Exception as e:
            log.warning("get_mat_error_text error: " + str(e))
            return ""

    def has_field_error(self, field_locator=None):
        """Check if a form field has error styling (red border / invalid state).
        V3: UOM golden pattern — uses pure JS to walk up parentElement chain
        looking for invalid classes.
        If field_locator is None, checks if any mat-error is visible.
        """
        if field_locator is None:
            # Original V2 behavior: check by field label
            return len(self.get_mat_error_text()) > 0

        # V3: UOM pattern with field_locator parameter
        try:
            css_selector = field_locator[1] if field_locator[0] == "css" else ""
            if not css_selector:
                return False
            js = """
            var input = document.querySelector(arguments[0]);
            if (!input) return JSON.stringify({found: false, reason: 'input not found'});
            var current = input;
            var invalidClasses = ['mat-mdc-form-field-invalid', 'mat-form-field-invalid', 'ng-invalid', 'cdk-text-field-invalid'];
            for (var steps = 0; steps < 20; steps++) {
                var classes = current.className || '';
                for (var i = 0; i < invalidClasses.length; i++) {
                    if (classes.indexOf(invalidClasses[i]) !== -1) {
                        return JSON.stringify({found: true, tag: current.tagName, cls: invalidClasses[i]});
                    }
                }
                current = current.parentElement;
                if (!current || current === document.body) break;
            }
            return JSON.stringify({found: false});
            """
            result = self.driver.execute_script(js, css_selector)
            log.info("has_field_error raw: " + str(result))
            if not result:
                return False
            data = json.loads(result)
            return data.get("found", False)
        except Exception as e:
            log.warning("has_field_error error: " + str(e))
            return False

    # ==============================================================
    #  Verification helpers — V3: UOM golden patterns
    # ==============================================================

    def is_popup_open(self):
        """Check if any popup/form is currently open.
        Used by conftest for state checks.
        """
        return self.driver.execute_script("""
            var popup = document.querySelector(
                '.big-model, mat-dialog-container, ' +
                '.edit_pop_up.override_edit_pop_up.popup-mode'
            );
            return popup && popup.offsetParent !== null;
        """)

    def is_add_form_open(self):
        """Check if the Add/Create form popup is currently open.
        V3: UOM golden pattern — JS-only check, no Selenium find_element.
        """
        return self.driver.execute_script("""
            var el = document.querySelector("input[formcontrolname='name']");
            return el && el.offsetParent !== null;
        """)

    def is_form_closed(self):
        """Check if the form popup is no longer visible.
        V3: JS-only check.
        """
        result = self.driver.execute_script("""
            var el = document.querySelector("input[formcontrolname='name']");
            return !el || el.offsetParent === null;
        """)
        return bool(result)

    def get_field_value(self, locator):
        """Get the current value of an input field via JS (fast).
        UOM golden pattern.
        """
        try:
            css_selector = locator[1] if locator[0] == "css" else ""
            if not css_selector:
                return ""
            return self.driver.execute_script(
                "var el = document.querySelector(arguments[0]); "
                "return el ? el.value : '';",
                css_selector
            ) or ""
        except Exception:
            return ""

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
            ("item_sourcing", self.ITEM_SOURCING_SELECT),
            ("base_uom", self.BASE_UOM_SELECT),
        ]:
            try:
                el = self.driver.find_element(By.XPATH, locator[1])
                values[key] = el.text.strip()
            except Exception:
                values[key] = ""

        # Toggle switches (ALL on Step 1 — verified 2026-05-18)
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
    #  Row action buttons — V3: 3-dot menu (UOM golden pattern)
    # ==============================================================

    def _click_action_menu_item(self, item_name, action_name):
        """Click an action menu item (View/Edit/History) for a specific Item Master row.
        V3: The live ERP uses a 3-dot (⋮) menu button in cdk-column-actions.
        UOM golden pattern — pure JS, no XPath.
        """
        log.info("Clicking " + action_name + " via 3-dot menu for: " + item_name)
        # Step 1: Open the 3-dot menu for the row containing the item name
        js = """
        var table = document.querySelector('table#excel-table');
        if (!table) { throw new Error('Table not found'); }
        var rows = table.querySelectorAll('tbody tr');
        for (var i = 0; i < rows.length; i++) {
            var cells = rows[i].querySelectorAll('td');
            for (var j = 0; j < cells.length; j++) {
                if (cells[j].textContent.trim().indexOf(arguments[0]) !== -1) {
                    var menuBtn = rows[i].querySelector('td.cdk-column-actions button');
                    if (!menuBtn) { throw new Error('3-dot menu button not found in actions column'); }
                    menuBtn.scrollIntoView({block:'center'});
                    menuBtn.click();
                    return 'menu_opened';
                }
            }
        }
        throw new Error('Item ' + arguments[0] + ' not found in table');
        """
        self.driver.execute_script(js, item_name)
        log.info("3-dot menu opened for: " + item_name)

        # Step 2: Wait briefly for dropdown to render
        try:
            WebDriverWait(self.driver, 2).until(
                EC.presence_of_element_located(("css selector", ".cdk-overlay-container .cdk-overlay-pane"))
            )
        except Exception:
            pass

        # Step 3: Click the specific menu item from the dropdown overlay
        js_click = """
        var overlay = document.querySelector('.cdk-overlay-container');
        if (!overlay) { throw new Error('CDK overlay not found after menu click'); }
        var items = overlay.querySelectorAll('button, span, div');
        for (var i = 0; i < items.length; i++) {
            var text = items[i].textContent.trim();
            if (text === arguments[0]) {
                items[i].click();
                return 'clicked_' + arguments[0];
            }
        }
        // Fallback: partial match
        for (var i = 0; i < items.length; i++) {
            if (items[i].textContent.trim().toLowerCase().indexOf(arguments[0].toLowerCase()) !== -1) {
                items[i].click();
                return 'clicked_partial_' + arguments[0];
            }
        }
        throw new Error('Menu item "' + arguments[0] + '" not found in dropdown overlay');
        """
        result = self.driver.execute_script(js_click, action_name)
        log.info("Successfully clicked " + action_name + " for: " + item_name)
        return result

    def click_view_button(self, item_name=None, row_index=0):
        """Click the View button for an item row.
        V3: Uses 3-dot menu pattern from UOM.
        """
        log.info("Clicking View button for: " + str(item_name or row_index))
        if item_name:
            self._click_action_menu_item(item_name, "View")
            # Wait for view popup to appear
            try:
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located(("css selector", ".big-model, mat-dialog-container, .edit_pop_up"))
                )
            except Exception:
                pass
        else:
            # Fallback for row_index-based access (backward compat)
            self._click_action_button_by_index(row_index, "view")

    def click_edit_button(self, item_name=None, row_index=0):
        """Click the Edit button for an item row.
        V3: Uses 3-dot menu pattern from UOM.
        """
        log.info("Clicking Edit button for: " + str(item_name or row_index))
        if item_name:
            self._click_action_menu_item(item_name, "Edit")
            # Wait for edit popup to appear
            try:
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located(("css selector", "input[formcontrolname='name']"))
                )
            except Exception:
                pass
        else:
            # Fallback for row_index-based access (backward compat)
            self._click_action_button_by_index(row_index, "edit")

    def click_history_button(self, item_name=None, row_index=0):
        """Click the History button for an item row.
        V3: Uses 3-dot menu pattern from UOM.
        """
        log.info("Clicking History button for: " + str(item_name or row_index))
        if item_name:
            self._click_action_menu_item(item_name, "History")
            # Wait for history popup to appear
            try:
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located(("css selector", ".big-model, mat-dialog-container"))
                )
            except Exception:
                pass
        else:
            # Fallback for row_index-based access (backward compat)
            self._click_action_button_by_index(row_index, "archive")

    def _click_action_button_by_index(self, row_index, action_type="view"):
        """Fallback: click action button by row index position.
        Used when item_name is not available (backward compat).
        """
        rows = self.driver.find_elements(
            By.CSS_SELECTOR, "table#excel-table tbody tr"
        )
        if row_index >= len(rows):
            raise Exception(
                f"Row index {row_index} out of range (total rows: {len(rows)})"
            )
        row = rows[row_index]
        btns = row.find_elements(By.CSS_SELECTOR, "td.cdk-column-actions button")

        if btns:
            # 3-dot menu approach
            self.driver.execute_script("arguments[0].click();", btns[0])
            time.sleep(0.5)
            # Click the menu item
            action_map = {
                "view": "View",
                "edit": "Edit",
                "archive": "History",
                "history": "History",
            }
            action_label = action_map.get(action_type.lower(), "View")
            try:
                js_click = """
                var overlay = document.querySelector('.cdk-overlay-container');
                if (!overlay) { throw new Error('CDK overlay not found'); }
                var items = overlay.querySelectorAll('button, span, div');
                for (var i = 0; i < items.length; i++) {
                    var text = items[i].textContent.trim();
                    if (text === arguments[0]) {
                        items[i].click();
                        return 'clicked';
                    }
                }
                // Fallback: partial match
                for (var i = 0; i < items.length; i++) {
                    if (items[i].textContent.trim().toLowerCase().indexOf(arguments[0].toLowerCase()) !== -1) {
                        items[i].click();
                        return 'clicked_partial';
                    }
                }
                throw new Error('Menu item not found');
                """
                self.driver.execute_script(js_click, action_label)
            except Exception:
                # Last resort: click all row buttons
                all_btns = row.find_elements(By.CSS_SELECTOR, "button")
                action_btn_map = {"view": 0, "edit": 1, "archive": 2, "history": 2}
                idx = action_btn_map.get(action_type.lower(), 0)
                if idx < len(all_btns):
                    self.driver.execute_script("arguments[0].click();", all_btns[idx])
        else:
            # Very old fallback: click buttons directly in row
            all_btns = row.find_elements(By.CSS_SELECTOR, "button")
            action_btn_map = {"view": 0, "edit": 1, "archive": 2, "history": 2}
            idx = action_btn_map.get(action_type.lower(), 0)
            if idx < len(all_btns):
                self.driver.execute_script("arguments[0].click();", all_btns[idx])

        time.sleep(1)

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
    #  Search functionality — V3: UOM golden pattern (JS-based)
    # ==============================================================

    def search_item(self, item_name):
        """Search for an item by name in the table search bar.
        V4: Updated for new ERP search UI — input.search-bar-input is always visible,
        button.erp-outline-btn submits the search.
        Returns True if the item is found in the table results.
        """
        log.info(f"Searching for item: {item_name}")
        try:
            self._force_close_panels()

            # Step 1: Find the search input — new UI uses input.search-bar-input (always visible)
            search_input = None
            try:
                el = self.driver.find_element("css selector", "input.search-bar-input")
                rect = self.driver.execute_script(
                    "var r = arguments[0].getBoundingClientRect(); "
                    "return r.width > 0 && r.height > 0;", el
                )
                if rect:
                    search_input = el
                    log.info("Search input found (input.search-bar-input)")
            except Exception:
                pass

            # Fallback: try old selector
            if search_input is None:
                try:
                    el = self.driver.find_element("css selector", "input#erpSearchInput")
                    rect = self.driver.execute_script(
                        "var r = arguments[0].getBoundingClientRect(); "
                        "return r.width > 0 && r.height > 0;", el
                    )
                    if rect:
                        search_input = el
                        log.info("Search input found (input#erpSearchInput fallback)")
                except Exception:
                    pass

            # If still not found, try clicking the search toggle button
            if search_input is None:
                log.info("Search input not visible, clicking search button via JS")
                js_click_search = """
                var btn = document.querySelector('button.erp-outline-btn, button.search-btn');
                if (!btn) { throw new Error('Search button not found in DOM'); }
                btn.scrollIntoView({block:'center'});
                btn.click();
                return 'clicked';
                """
                try:
                    self.driver.execute_script(js_click_search)
                except Exception as e:
                    log.error("Failed to click search button via JS: " + str(e))
                    return False

                # Wait for search input to become visible
                try:
                    search_input = WebDriverWait(self.driver, 5).until(
                        EC.visibility_of_element_located(("css selector", "input.search-bar-input, input#erpSearchInput"))
                    )
                except Exception:
                    log.warning("Search input did not become visible after clicking search button")
                    return False

            # Step 2: Clear existing value and set new value via JS
            self.driver.execute_script("""
                var el = arguments[0];
                var s = Object.getOwnPropertyDescriptor(
                    window.HTMLInputElement.prototype, 'value').set;
                s.call(el, '');
                el.dispatchEvent(new Event('input', { bubbles: true }));
                s.call(el, arguments[1]);
                el.dispatchEvent(new Event('input', { bubbles: true }));
                el.dispatchEvent(new Event('keyup', { bubbles: true }));
                el.dispatchEvent(new Event('change', { bubbles: true }));
            """, search_input, item_name)

            # Step 3: Click the search submit button via JS
            js_click_search = """
            var btn = document.querySelector('button.erp-outline-btn, button.search-btn');
            if (btn) { btn.click(); return 'clicked'; }
            return 'not found';
            """
            self.driver.execute_script(js_click_search)
            log.info("Search submit clicked via JS")

            # Step 4: Wait for table to refresh
            try:
                WebDriverWait(self.driver, 5).until(
                    lambda d: d.find_elements("css selector", "table#excel-table tbody tr")
                )
            except Exception:
                pass  # Table might be empty (no results)

            # Step 5: Verify the item is in the results
            found = self.is_item_in_table(item_name)
            if found:
                log.info(f"Item found in table: {item_name}")
            else:
                log.warning(f"Item NOT found in table: {item_name}")
            return found

        except Exception as e:
            log.error(f"Search failed: {e}")
            return False

    def verify_item_exists(self, item_name):
        """Navigate to page, search, and verify an item exists.
        Polls up to 10s to handle slow Angular re-renders.
        """
        log.info(f"Verifying item '{item_name}' exists in table")
        end_time = time.monotonic() + 10
        last_seen = []
        while time.monotonic() < end_time:
            try:
                rows = self.find_elements(self.TABLE_ROWS)
                last_seen = []
                for row in rows:
                    cells = row.find_elements("css selector", "td")
                    row_text = " | ".join(c.text.strip() for c in cells if c.text.strip())
                    last_seen.append(row_text)
                    for cell in cells:
                        if item_name in cell.text.strip():
                            log.info(f"Item '{item_name}' found in table")
                            return True
            except Exception:
                pass
            time.sleep(0.5)
        log.error(f"Item '{item_name}' NOT found. Table contents were: {last_seen}")
        raise AssertionError(
            f"Item '{item_name}' NOT found in table after search. "
            f"Last table rows: {last_seen}"
        )

    def search_and_verify(self, item_name):
        """Search for an item name, then verify it exists in the filtered results.
        V3: UOM golden pattern — combines search + existence check.
        Returns True if found.
        """
        log.info(f"Searching and verifying item: {item_name}")
        self.search_item(item_name)
        return self.verify_item_exists(item_name)

    def clear_search(self):
        """Clear the search input and reset the table.
        V3: Uses hard_refresh() instead of manual clear (UOM pattern).
        """
        log.info("Clearing search - hard refreshing")
        self.hard_refresh()

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
        """Search within the history popup.
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
                        time.sleep(1)
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
        """Close the history popup via Cancel button, X icon, or JS force.
        V3: UOM golden pattern — JS click Cancel first.
        """
        log.info("Closing history popup...")

        # Strategy 1: JS click the Cancel/Close button (UOM pattern)
        try:
            self.driver.execute_script("""
                var footers = document.querySelectorAll('.popup-footer');
                for (var i = 0; i < footers.length; i++) {
                    var buttons = footers[i].querySelectorAll('button');
                    for (var j = 0; j < buttons.length; j++) {
                        if (buttons[j].textContent.includes('Cancel') ||
                            buttons[j].textContent.includes('Close')) {
                            buttons[j].click();
                            return 'clicked';
                        }
                    }
                }
                return 'not found';
            """)
            time.sleep(1)
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
            time.sleep(1)
            if not self.is_history_popup_open():
                log.info("History popup closed via X icon (JS)")
                return
        except Exception:
            pass

        # Strategy 3: JS force remove overlays
        try:
            self.driver.execute_script("""
                document.querySelectorAll('.cdk-overlay-pane').forEach(
                    function(el) { el.remove(); }
                );
                document.querySelectorAll('.cdk-overlay-backdrop').forEach(
                    function(el) { el.remove(); }
                );
            """)
            time.sleep(0.5)
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
        V4: Uses JS value-setter + dispatchEvent pattern to ensure Angular
        reactive form model is properly synced (BUG-007 fix).
        Browser clicks on mat-option do NOT update Angular form — must use JS.
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
        time.sleep(0.5)

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
                        time.sleep(0.3)
                        break
                except Exception:
                    continue
        except Exception:
            pass

        # Click the matching option — use JS click + Angular form sync
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

        time.sleep(0.2)
        self._force_close_panels()

        # BUG-007 FIX: Force Angular change detection after mat-select selection.
        # Browser clicks don't always update Angular reactive form model.
        # Trigger change detection on the mat-select element.
        try:
            self.driver.execute_script("""
                var selects = document.querySelectorAll('mat-select');
                for (var i = 0; i < selects.length; i++) {
                    var trigger = selects[i].querySelector('.mat-mdc-select-trigger');
                    if (trigger) {
                        trigger.dispatchEvent(new Event('change', { bubbles: true }));
                        trigger.dispatchEvent(new Event('blur', { bubbles: true }));
                    }
                    // Also try the underlying select element
                    var value = selects[i].getAttribute('ng-reflect-value');
                    if (!value) {
                        // Force Angular to pick up the selection
                        var evt = new Event('selectionChange', { bubbles: true });
                        selects[i].dispatchEvent(evt);
                    }
                }
            """)
        except Exception:
            pass

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
        time.sleep(0.5)

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

        time.sleep(0.3)
        self._force_close_panels()
        return selected

    def get_dropdown_options(self, select_locator):
        """Open a dropdown, read all option texts, then close it."""
        log.info("Reading dropdown options...")
        self._close_select_panel()
        time.sleep(0.3)

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
        time.sleep(0.5)

        try:
            WebDriverWait(self.driver, 8).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, "div.mat-mdc-select-panel mat-option")
                )
            )
            time.sleep(0.3)
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
    #  Force close form popup (cleanup) — V3: UOM golden pattern
    # ==============================================================

    def force_close_form_popup(self):
        """Force-close any open form popup by clicking the X button via JS.
        UOM golden pattern.
        """
        log.info("Force closing form popup")
        result = self.driver.execute_script("""
            var popup = document.querySelector('div.edit_pop_up');
            if (!popup) return 'no popup found';
            var closeBtn = popup.querySelector('button[mat-icon-button] mat-icon');
            if (!closeBtn) return 'no close button found';
            var btn = closeBtn.closest('button');
            if (btn) { btn.click(); return 'clicked close'; }
            return 'could not click';
        """)
        log.info("Force close result: " + str(result))

    # ==============================================================
    #  Cleanup helper — V3: new method
    # ==============================================================

    def _cleanup(self):
        """Smart cleanup — close form if open, then hard refresh.
        UOM golden pattern for reliable state reset between tests.
        """
        if self.is_add_form_open():
            self.force_close_form_popup()
        self.hard_refresh()

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

            msg = self.handle_success_alert(timeout=5)
            if msg:
                result["message"] = msg
                result["status"] = "PASSED"
            else:
                time.sleep(2)
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
                time.sleep(1)

            self.click_edit_button(item_name=item_name, row_index=row_index)
            time.sleep(1)

            if not self.is_edit_mode():
                raise Exception("Edit form did not open (no Update button)")

            # Fill the updated data through the stepper
            self.fill_full_form(updated_data)

            self._force_close_panels()
            self.click_update()

            msg = self.handle_success_alert(timeout=5)
            if msg:
                result["message"] = msg
                result["status"] = "PASSED"
            else:
                time.sleep(2)
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
            time.sleep(1)
            values = self.get_form_field_values_step1()
            log.info(f"Item details: {values}")
            self.close_popup()
            time.sleep(0.5)
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
                time.sleep(1)

            self.click_history_button(
                item_name=item_name, row_index=row_index
            )
            time.sleep(1.5)

            result["row_count"] = self.get_history_row_count()
            result["data"] = self.get_history_data()

            if search_text:
                result["search_found"] = self.search_in_history(search_text)

            self.close_history_popup()
            time.sleep(0.5)

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

            # V3: Cleanup between creations — use _cleanup() (UOM pattern)
            try:
                self._cleanup()
            except Exception:
                try:
                    self.navigate_to_page()
                    time.sleep(2)
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
