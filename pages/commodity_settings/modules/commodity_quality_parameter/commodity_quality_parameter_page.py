"""
commodity_quality_parameter_page.py
-----------------------------------
Page Object Model for RhythmERP Commodity Quality Parameter screen.

Location: Commodity Settings > Commodity Master > Commodity Quality Parameter
URL:      /#/dynamic-screens/Commodity%20Quality%20Parameter

FORM LAYOUT (Popup with Header + Detail Grid):

  HEADER SECTION (5 fields):
    - Item Name            (mat-select,    required, searchable, 42+ options)
    - Transaction Type     (mat-select,    required, searchable, 8 options)
    - From Date            (datepicker,    required, default: current date, DD/MM/YYYY)
    - To Date              (datepicker,    required, auto-fills 30/12/2099 after Item selection)
    - Revision Status      (text input,    optional, free text)

  DETAIL GRID — "Define Item Quality Parameter Details" tab (5 fields per row):
    - Quality Parameter    (mat-select,    required, searchable, 65+ options)
    - Min Quality Value    (text input,    required, max 255 chars)
    - Max Quality Value    (text input,    required, max 255 chars)
    - Is Rate/Percentage   (slide toggle,  required, Yes/No, defaults "No")
    - Multiplier           (text input,    required, max 255 chars)

  [Cancel] [Submit]

TABLE COLUMNS (main listing):
  - View / Edit / Version / History   (action buttons per row)
  - Item Name / Transaction Type / From Date / To Date / Revision Status

TRANSACTION TYPE OPTIONS (8):
  'Return Stock Down', 'Stock Transfer Down', 'Stock Down',
  'Return Stock Up', 'Stock Transfer Up', 'Stock Up',
  Sales, Purchase

KNOWN BUGS (documented at time of inspection):
  BUG-001 (HIGH)  : Version & History buttons both use 'tbl-fav-edit' CSS class
  BUG-002 (HIGH)  : Duplicate Item Name entries in dropdown (no dedup)
  BUG-003 (MEDIUM): Dates displayed as raw ISO strings in table
  BUG-004 (MEDIUM): History popup always shows "No data available"
  BUG-005 (LOW)   : To Date auto-populates 30/12/2099 sentinel without explanation
  BUG-006 (LOW)   : Quality Parameter dropdown slow to load (2-3 sec)
  BUG-007 (LOW)   : Test/QA data in QP dropdown (no data cleanup)
  BUG-008 (HIGH)  : Detail grid input name attrs have TRAILING TAB chars
                    e.g. name="Min Quality Value\t" — CSS [name='...'] FAILS!
                    Must use [name^='...'] (starts-with) or XPath contains()

POPUP TYPES:
  Type A — "Validation Failed - Please correct the highlighted fields"
            Appears when required fields are empty (client-side).
            Has .swal2-confirm button.
  Type B — "Failed to save record"
            Appears when server-side validation rejects data.
            MUST use JS dismiss to avoid StaleElementReferenceException.

KEY RULES:
  - NEVER use Keys.ESCAPE (use backdrop click + JS overlay removal)
  - JS clicks for Angular Material overlays
  - ALL SweetAlert2 dismissals MUST use JS querySelector click
  - ADD button uses button.erp-add-btn (project-wide standard)
  - History column uses cdk-column-archive (NOT cdk-column-history)
  - History popup uses div.popup-overlay container
  - Toggle switch uses app-slide-toggle-v2 component
  - mat-select dropdowns need JS click + wait for options panel
  - Datepicker inputs need mat-datepicker-input selector
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
    StaleElementReferenceException,
    WebDriverException,
)
from common.base_page import BasePage
from common.logger import log
from config import RHYTHMERP_BASE_URL, EXPLICIT_WAIT

# Global list to track every submission for reporting
CQP_SUBMISSIONS = []


class CommodityQualityParameterPage(BasePage):
    """Page Object for Commodity Quality Parameter screen."""

    PAGE_URL = (
        f"{RHYTHMERP_BASE_URL}"
        "/#/dynamic-screens/Commodity%20Quality%20Parameter"
    )

    # ==============================================================
    #  LOCATORS — Toolbar
    # ==============================================================
    ADD_BUTTON = ("css", "button.erp-add-btn")
    SEARCH_TOGGLE = ("css", "button.search-btn, button[aria-label='Search']")
    REFRESH_BUTTON = ("css", "button[mattooltip='Refresh']")
    FILTER_BUTTON = ("css", "div[mattooltip='Filters'] button")
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

    # ==============================================================
    #  LOCATORS — Table (main listing)
    # ==============================================================
    TABLE = ("css", "table#excel-table")
    TABLE_ROWS = ("css", "table#excel-table tbody tr")
    TABLE_ITEM_NAME_CELLS = (
        "css",
        "table#excel-table tbody td.cdk-column-item_ref_id, "
        "table#excel-table tbody td.mat-column-item_ref_id",
    )
    TABLE_TXN_TYPE_CELLS = (
        "css",
        "table#excel-table tbody td.cdk-column-transaction_type, "
        "table#excel-table tbody td.mat-column-transaction_type",
    )
    TABLE_FROM_DATE_CELLS = (
        "css",
        "table#excel-table tbody td.cdk-column-from_date, "
        "table#excel-table tbody td.mat-column-from_date",
    )
    TABLE_TO_DATE_CELLS = (
        "css",
        "table#excel-table tbody td.cdk-column-to_date, "
        "table#excel-table tbody td.mat-column-to_date",
    )
    TABLE_REVISION_STATUS_CELLS = (
        "css",
        "table#excel-table tbody td.cdk-column-revision_status, "
        "table#excel-table tbody td.mat-column-revision_status",
    )
    NO_DATA_ROW = (
        "css",
        "table#excel-table tbody tr td.no-data, "
        "table#excel-table tbody tr.mat-mdc-no-data-row",
    )

    # ==============================================================
    #  LOCATORS — Popup form
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

    # Header section fields
    ITEM_NAME_SELECT = (
        "css",
        ".popup-body .form-field mat-select, "
        ".big-model .form-field mat-select",
    )
    TRANSACTION_TYPE_SELECT = (
        "css",
        ".popup-body .form-field mat-select:nth-child(1), "
        ".big-model .form-field mat-select:nth-child(1)",
    )
    FROM_DATE_INPUT = (
        "css",
        "input[placeholder='DD/MM/YYYY']",
    )
    TO_DATE_INPUT = (
        "css",
        "input[placeholder='DD/MM/YYYY']",
    )
    # NOTE: ERP uses custom dual-input date fields — a visible display input
    # with placeholder="DD/MM/YYYY" and a hidden mat-datepicker-input.
    # The visible input accepts typed date values; the hidden one is for
    # the calendar popup.  We type into the VISIBLE input.
    # NOTE: ERP may add trailing tab in name attr — use starts-with selector
    REVISION_STATUS_INPUT = (
        "css",
        "input[name^='Revision Status']",
    )

    # Detail grid fields
    DETAIL_TABLE = (
        "css",
        ".popup-body table, .big-model table",
    )
    DETAIL_QUALITY_PARAM_SELECT = (
        "css",
        ".popup-body mat-select, .big-model mat-select",
    )
    # NOTE: The ERP generates name attributes with trailing tab characters
    # e.g. name="Min Quality Value\t" — CSS [name='...'] won't match!
    # Use [name^='...'] (starts-with) and XPath contains() as fallback.
    DETAIL_MIN_VALUE_INPUT = (
        "css",
        "input[name^='Min Quality Value']",
    )
    DETAIL_MAX_VALUE_INPUT = (
        "css",
        "input[name^='Max Quality Value']",
    )
    DETAIL_MULTIPLIER_INPUT = (
        "css",
        "input[name^='Multiplier']",
    )
    DETAIL_TOGGLE = (
        "css",
        "app-slide-toggle-v2 .switch-container",
    )
    DETAIL_ADD_ROW_BUTTON = (
        "css",
        ".popup-body button.add-row-btn, .big-model button.add-row-btn, "
        "button[mattooltip='Add Row']",
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
    #  LOCATORS — Row action buttons
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
    #  LOCATORS — History popup
    # ==============================================================
    HISTORY_POPUP = (
        "xpath",
        "//div[contains(@class,'popup-overlay') or contains(@class,'big-model')]"
        "[.//h3[contains(translate(.,'HISTORY','history'),'history')]]",
    )
    HISTORY_TABLE_ROWS = (
        "css",
        ".popup-body table tbody tr, .big-model table tbody tr, "
        "div.popup-overlay table tbody tr",
    )
    HISTORY_CLOSE_BUTTON = (
        "xpath",
        "//div[contains(@class,'popup-overlay') or contains(@class,'big-model')]"
        "[.//h3[contains(translate(.,'HISTORY','history'),'history')]]"
        "//button[contains(.,'Cancel') or contains(.,'Close')]",
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
    #  LOCATORS — Filter panel
    # ==============================================================
    FILTER_TOGGLE = (
        "css",
        "div[mattooltip='Filters'] button, button[mattooltip='Filters']",
    )
    FILTER_PANEL = ("css", ".filter-panel, .cdk-overlay-pane filter-panel")

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
        """Navigate to the CQP listing page.
        Force-refreshes to clear leftover Angular state.
        """
        log.info("Navigating to Commodity Quality Parameter page...")
        self.navigate_to(self.PAGE_URL)
        self.driver.refresh()
        self._wait_for_page_ready()

    def _wait_for_page_ready(self):
        """Wait until the CQP page is fully loaded."""
        try:
            WebDriverWait(self.driver, EXPLICIT_WAIT).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, "table#excel-table")
                )
            )
            log.info("CQP table loaded")
        except TimeoutException:
            log.warning("CQP table not found, page may be empty")

        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "ul.tbl-export-btn")
                )
            )
            self.wait_seconds(1)
            log.info("CQP toolbar ready")
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
        """Click the ADD (+) button to open the create popup form.
        Uses button.erp-add-btn as primary selector (project-wide standard).
        """
        log.info("Clicking ADD button on CQP...")
        self._wait_for_toolbar()

        # Strategy 1: button.erp-add-btn (primary — project-wide standard)
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
                    self._wait_for_form_content(timeout=8)
                    log.info("ADD form opened via erp-add-btn")
                    return
        except Exception:
            pass

        # Strategy 2: mini-fab button with 'add' icon
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
                            self._wait_for_form_content(timeout=8)
                            log.info("ADD form opened via mini-fab icon")
                            return
                except Exception:
                    continue
        except Exception:
            pass

        # Strategy 3: Legacy mattooltip selector
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
                    self._wait_for_form_content(timeout=8)
                    log.info("ADD form opened via mattooltip legacy")
                    return
        except Exception:
            pass

        # Strategy 4: click_with_retry
        try:
            self.click_with_retry(self.ADD_BUTTON)
            self.wait_seconds(1.5)
            if self._is_form_popup_open():
                self._wait_for_form_content(timeout=8)
                log.info("ADD form opened via click_with_retry")
                return
        except Exception:
            pass

        raise Exception("ADD button not found or not clickable on CQP")

    def _wait_for_toolbar(self):
        """Wait for the toolbar and ADD button to be ready."""
        for attempt in range(3):
            # Check erp-add-btn (primary)
            try:
                btns = self.driver.find_elements(
                    By.CSS_SELECTOR, "button.erp-add-btn"
                )
                for btn in btns:
                    if btn.is_displayed():
                        return
            except Exception:
                pass

            # Check mini-fab with add icon (fallback)
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

    def _wait_for_form_content(self, timeout=8):
        """Wait for form content (inputs/selects) to render inside the popup."""
        import time as _time
        deadline = _time.time() + timeout
        while _time.time() < deadline:
            try:
                elements = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    "div.big-model input, "
                    "div.big-model mat-select, "
                    "div.edit_pop_up input, "
                    "div.edit_pop_up mat-select, "
                    "mat-dialog-container input, "
                    "mat-dialog-container mat-select"
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

        log.warning(
            f"Form content did not render within {timeout}s."
        )
        self._debug_popup_info()
        return False

    def _debug_popup_info(self):
        """Log debug information about the current popup state."""
        try:
            all_inputs = self.driver.find_elements(
                By.CSS_SELECTOR,
                "div.big-model input, "
                "div.edit_pop_up input, "
                "mat-dialog-container input"
            )
            log.info(f"DEBUG: Found {len(all_inputs)} inputs in popup")
            for i, inp in enumerate(all_inputs):
                try:
                    log.info(
                        f"  Input[{i}]: "
                        f"tag={inp.tag_name}, "
                        f"name={inp.get_attribute('name')}, "
                        f"type={inp.get_attribute('type')}, "
                        f"placeholder={inp.get_attribute('placeholder')}, "
                        f"visible={inp.is_displayed()}"
                    )
                except Exception:
                    pass

            all_selects = self.driver.find_elements(
                By.CSS_SELECTOR,
                "div.big-model mat-select, "
                "div.edit_pop_up mat-select, "
                "mat-dialog-container mat-select"
            )
            log.info(f"DEBUG: Found {len(all_selects)} mat-selects in popup")
            for i, sel in enumerate(all_selects):
                try:
                    log.info(
                        f"  Select[{i}]: "
                        f"visible={sel.is_displayed()}, "
                        f"text={sel.text[:80]}"
                    )
                except Exception:
                    pass
        except Exception as e:
            log.warning(f"Debug popup info failed: {e}")

    def click_refresh(self):
        """Click the Refresh button.
        Uses button[mattooltip='Refresh'] selector (project-wide pattern).
        """
        log.info("Clicking Refresh button...")

        # Strategy 1: mattooltip selector (primary)
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
                        log.info("Refresh clicked via mattooltip")
                        return
                except Exception:
                    continue
        except Exception:
            pass

        # Strategy 2: erp-outline-btn with refresh icon
        try:
            btns = self.driver.find_elements(
                By.CSS_SELECTOR, "button.erp-outline-btn"
            )
            for btn in btns:
                try:
                    icon = btn.find_element(
                        By.CSS_SELECTOR, "i.material-icons, mat-icon"
                    )
                    if (
                        icon.text.strip().lower() == "refresh"
                        and btn.is_displayed()
                    ):
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({block:'center'});"
                            "arguments[0].click();",
                            btn,
                        )
                        self.wait_seconds(2)
                        log.info("Refresh clicked via outline-btn")
                        return
                except Exception:
                    continue
        except Exception:
            pass

        # Strategy 3: Use the REFRESH_BUTTON locator
        try:
            self.click_with_retry(self.REFRESH_BUTTON)
            self.wait_seconds(2)
            log.info("Refresh clicked via locator")
            return
        except Exception:
            pass

        log.warning("Refresh button not found")

    # ==============================================================
    #  mat-select dropdown helpers
    # ==============================================================

    # Placeholder texts that are NOT real options — never select these
    _PLACEHOLDER_OPTIONS = {
        "no results found",
        "no data",
        "no data available",
        "loading...",
        "loading",
        "searching...",
        "searching",
        "type to search",
        "",
    }

    def _is_placeholder_option(self, text):
        """Check if an option text is a placeholder (not a real selectable value)."""
        return text.strip().lower() in self._PLACEHOLDER_OPTIONS

    def _select_mat_option(self, select_element, option_text=None):
        """Select an option from a mat-select dropdown.

        Args:
            select_element: The mat-select WebElement
            option_text: Text of the option to select. If None, selects a random option.

        Returns:
            The text of the selected option, or '' if failed.
        """
        log.info(f"Selecting mat-option: option_text={option_text}")

        # Click the mat-select to open the dropdown
        try:
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});"
                "arguments[0].click();",
                select_element,
            )
            self.wait_seconds(1)
        except Exception:
            # Fallback: click via JS directly on the select trigger
            try:
                trigger = select_element.find_element(
                    By.CSS_SELECTOR, ".mat-mdc-select-trigger"
                )
                self.driver.execute_script(
                    "arguments[0].click();", trigger
                )
                self.wait_seconds(1)
            except Exception:
                log.warning("Could not open mat-select dropdown")
                return ""

        # Wait for the option panel to appear
        try:
            WebDriverWait(self.driver, 8).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR,
                     "div.cdk-overlay-pane mat-option, "
                     "mat-option")
                )
            )
            self.wait_seconds(0.5)
        except TimeoutException:
            log.warning("mat-option panel did not appear")
            return ""

        # Try to trigger search in searchable dropdowns.
        # Many Angular Material searchable dropdowns start with
        # "No results found" until a search query is entered.
        # Typing a space or clearing the filter triggers option loading.
        self._trigger_dropdown_search()

        # Wait for real options to load (retry up to 3 times)
        real_options = []
        for attempt in range(3):
            all_options = self.driver.find_elements(
                By.CSS_SELECTOR, "mat-option"
            )
            real_options = []
            for opt in all_options:
                try:
                    text = opt.text.strip()
                    if text and not self._is_placeholder_option(text) and opt.is_displayed():
                        real_options.append((opt, text))
                except StaleElementReferenceException:
                    continue

            if real_options:
                break

            log.info(
                f"Waiting for real dropdown options... "
                f"attempt {attempt + 1}/3 "
                f"(found {len(all_options)} total, 0 real)"
            )
            self.wait_seconds(2)
            # Try triggering search again
            self._trigger_dropdown_search()

        if not real_options:
            # Close the dropdown if nothing selectable
            self._close_select_panel()
            log.warning("No real options found in mat-select after retries")
            return ""

        if option_text:
            # Find the specific option among REAL options
            for opt, text in real_options:
                if option_text.strip().lower() in text.lower():
                    self.driver.execute_script(
                        "arguments[0].click();", opt
                    )
                    self.wait_seconds(0.5)
                    log.info(f"Selected option: {text}")
                    return text

            # Option not found — select first real option
            log.warning(
                f"Option '{option_text}' not found, selecting first real option"
            )

        # Select a random/first real option
        import random
        chosen_opt, chosen_text = random.choice(real_options)
        self.driver.execute_script("arguments[0].click();", chosen_opt)
        self.wait_seconds(0.5)
        log.info(f"Selected option: {chosen_text}")
        return chosen_text

    def _trigger_dropdown_search(self):
        """Try to trigger option loading in a searchable mat-select dropdown.

        Many Angular Material searchable dropdowns start with "No results found"
        until the user interacts with the search input inside the dropdown panel.
        This method types a space and then backspaces it to trigger the search API.
        """
        try:
            # Look for search input inside the dropdown overlay panel
            search_inputs = self.driver.find_elements(
                By.CSS_SELECTOR,
                "div.cdk-overlay-pane input, "
                "mat-option input, "
                ".cdk-overlay-pane input[matinput], "
                ".cdk-overlay-pane input[placeholder]"
            )
            for inp in search_inputs:
                try:
                    if inp.is_displayed():
                        # Type space + backspace to trigger search without changing query
                        inp.click()
                        self.wait_seconds(0.2)
                        inp.send_keys(" ")
                        self.wait_seconds(0.5)
                        inp.send_keys(Keys.BACK_SPACE)
                        self.wait_seconds(1)
                        log.info("Triggered dropdown search input")
                        return
                except Exception:
                    continue
        except Exception:
            pass

    def _select_random_from_dropdown(self, select_element):
        """Select a random option from a mat-select dropdown.
        Returns the text of the selected option.
        """
        import random
        log.info("Selecting random option from dropdown...")

        # Click to open
        try:
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});"
                "arguments[0].click();",
                select_element,
            )
            self.wait_seconds(1.5)
        except Exception:
            try:
                trigger = select_element.find_element(
                    By.CSS_SELECTOR, ".mat-mdc-select-trigger"
                )
                self.driver.execute_script("arguments[0].click();", trigger)
                self.wait_seconds(1.5)
            except Exception:
                return ""

        # Wait for options
        try:
            WebDriverWait(self.driver, 8).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, "mat-option")
                )
            )
            self.wait_seconds(0.5)
        except TimeoutException:
            return ""

        # Trigger search for searchable dropdowns
        self._trigger_dropdown_search()

        # Get all REAL options (skip placeholders like "No results found")
        options = self.driver.find_elements(
            By.CSS_SELECTOR, "mat-option"
        )
        valid_options = []
        for opt in options:
            try:
                text = opt.text.strip()
                if text and not self._is_placeholder_option(text) and opt.is_displayed():
                    valid_options.append((opt, text))
            except StaleElementReferenceException:
                continue

        if valid_options:
            # Pick a random option
            chosen_opt, chosen_text = random.choice(valid_options)
            self.driver.execute_script("arguments[0].click();", chosen_opt)
            self.wait_seconds(0.5)
            log.info(f"Randomly selected: {chosen_text}")
            return chosen_text

        self._close_select_panel()
        return ""

    def get_dropdown_options(self, select_element):
        """Open a mat-select and return all option texts.
        Closes the dropdown after reading.
        """
        log.info("Reading dropdown options...")

        try:
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});"
                "arguments[0].click();",
                select_element,
            )
            self.wait_seconds(1.5)
        except Exception:
            return []

        try:
            WebDriverWait(self.driver, 8).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, "mat-option")
                )
            )
            self.wait_seconds(0.5)
        except TimeoutException:
            return []

        # Trigger search for searchable dropdowns
        self._trigger_dropdown_search()

        options = self.driver.find_elements(
            By.CSS_SELECTOR, "mat-option"
        )
        option_texts = []
        for opt in options:
            try:
                text = opt.text.strip()
                if text and not self._is_placeholder_option(text):
                    option_texts.append(text)
            except StaleElementReferenceException:
                continue

        self._close_select_panel()
        return option_texts

    def _close_select_panel(self):
        """Close any open mat-select dropdown panel."""
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

        # Fallback: remove overlay panes that don't contain dialogs
        remaining = self.driver.find_elements(
            By.CSS_SELECTOR,
            "div.cdk-overlay-backdrop:not(.cdk-overlay-dark-backdrop), "
            "div.cdk-overlay-pane mat-option",
        )
        if remaining:
            self._force_close_panels()

    # ==============================================================
    #  Fill form fields — Header section
    # ==============================================================

    def fill_form(self, data):
        """Fill the CQP add/edit form — header section only.

        Fill order: Item Name -> Transaction Type -> From Date -> To Date -> Revision Status

        data dict keys:
          - item_name          (str, required — will select from dropdown)
          - transaction_type   (str, required — will select from dropdown)
          - from_date          (str, optional — DD/MM/YYYY format)
          - to_date            (str, optional — DD/MM/YYYY format)
          - revision_status    (str, optional — free text)

        If item_name / transaction_type are None, selects a random option.
        """
        log.info("Filling CQP header form...")

        # 1. Item Name (mat-select, required)
        if data.get("item_name") is not None or data.get("select_item_name", True):
            self._fill_item_name(data.get("item_name"))

        # 2. Transaction Type (mat-select, required)
        if data.get("transaction_type") is not None or data.get("select_transaction_type", True):
            self._fill_transaction_type(data.get("transaction_type"))

        # 3. From Date (datepicker) — SKIP: auto-filled by ERP to today's date
        #    Only fill if explicitly requested (from_date is a non-empty string
        #    AND from_date_force is True).
        if data.get("from_date_force") and data.get("from_date"):
            self._fill_date_input("From Date", data["from_date"])
        else:
            log.info("From Date: skipped (auto-filled by ERP)")

        # 4. To Date (datepicker) — always fill; ERP defaults to 30/12/2099
        #    If no to_date provided, use the sentinel value.
        to_date_val = data.get("to_date") or "30/12/2099"
        if to_date_val:  # Fill unless explicitly set to empty string ""
            self._fill_date_input("To Date", to_date_val)

        # 5. Revision Status (text input, optional)
        if data.get("revision_status") is not None:
            self._type_in_input(
                self.REVISION_STATUS_INPUT,
                None,
                str(data["revision_status"]),
            )

        self._force_close_panels()
        log.info("CQP header form filled")

    def _fill_item_name(self, item_name=None):
        """Select an Item Name from the dropdown.
        If item_name is None, selects a random option.
        """
        log.info(f"Filling Item Name: {item_name or 'random'}")
        try:
            selects = self.driver.find_elements(
                By.CSS_SELECTOR,
                ".big-model .form-field mat-select, "
                ".popup-body .form-field mat-select, "
                "mat-dialog-container .form-field mat-select"
            )
            # Item Name is typically the first mat-select
            if selects:
                selected = self._select_mat_option(selects[0], item_name)
                if selected:
                    log.info(f"Item Name selected: {selected}")
                    return selected
        except Exception as e:
            log.warning(f"Failed to fill Item Name: {e}")
        return ""

    def _fill_transaction_type(self, transaction_type=None):
        """Select a Transaction Type from the dropdown.
        If transaction_type is None, selects a random option.
        """
        log.info(f"Filling Transaction Type: {transaction_type or 'random'}")
        try:
            selects = self.driver.find_elements(
                By.CSS_SELECTOR,
                ".big-model .form-field mat-select, "
                ".popup-body .form-field mat-select, "
                "mat-dialog-container .form-field mat-select"
            )
            # Transaction Type is typically the second mat-select
            if len(selects) >= 2:
                selected = self._select_mat_option(selects[1], transaction_type)
                if selected:
                    log.info(f"Transaction Type selected: {selected}")
                    return selected
        except Exception as e:
            log.warning(f"Failed to fill Transaction Type: {e}")
        return ""

    def _fill_date_input(self, field_label, date_value):
        """Fill a date input field by label.

        The ERP uses a custom dual-input pattern for date fields:
          - Visible input:  matinput + placeholder="DD/MM/YYYY"
          - Hidden input:   class="mat-datepicker-input" (for calendar popup)

        We type into the VISIBLE input.  From Date is auto-filled by the
        ERP, so this method is primarily used for To Date.

        Strategy 1: Find visible input by placeholder (primary)
        Strategy 2: Find by form-field label (XPath)
        Strategy 3: Find hidden mat-datepicker-input and trigger via JS
        """
        log.info(f"Filling {field_label}: {date_value}")

        # ---- Strategy 1: Find visible input by placeholder ----
        target = None
        try:
            date_inputs = self.driver.find_elements(
                By.CSS_SELECTOR,
                "input[placeholder='DD/MM/YYYY']"
            )
            if field_label == "From Date" and date_inputs:
                target = date_inputs[0]
            elif field_label == "To Date" and len(date_inputs) >= 2:
                target = date_inputs[1]
            elif date_inputs:
                target = date_inputs[-1]
        except Exception:
            pass

        # ---- Strategy 2: Find by form-field label (XPath) ----
        if target is None:
            try:
                label = field_label.strip()
                target = self.driver.find_element(
                    By.XPATH,
                    f"//mat-label[contains(.,'{label}')]"
                    "/ancestor::mat-form-field"
                    "//input[@placeholder='DD/MM/YYYY']"
                )
            except Exception:
                pass

        # ---- Strategy 3: Find hidden mat-datepicker-input ----
        if target is None:
            try:
                hidden_inputs = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    "input.mat-datepicker-input[aria-haspopup='dialog']"
                )
                if field_label == "From Date" and hidden_inputs:
                    target = hidden_inputs[0]
                elif field_label == "To Date" and len(hidden_inputs) >= 2:
                    target = hidden_inputs[1]
                elif hidden_inputs:
                    target = hidden_inputs[-1]
            except Exception:
                pass

        if target is None:
            log.warning(f"No datepicker found for {field_label}")
            return

        # Fill the found input
        try:
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});", target
            )
            self.wait_seconds(0.3)

            # Click to focus
            try:
                target.click()
                self.wait_seconds(0.3)
            except Exception:
                self.driver.execute_script("arguments[0].click();", target)
                self.wait_seconds(0.3)

            # Clear existing value via JS setter + dispatch events
            self.driver.execute_script(
                "var s = Object.getOwnPropertyDescriptor("
                "window.HTMLInputElement.prototype,'value').set;"
                "s.call(arguments[0], '');"
                "arguments[0].dispatchEvent(new Event('input',{bubbles:true}));"
                "arguments[0].dispatchEvent(new Event('change',{bubbles:true}));",
                target,
            )
            self.wait_seconds(0.2)

            # Type the date value
            target.send_keys(date_value)
            self.wait_seconds(0.3)

            # Tab out to trigger Angular change detection
            target.send_keys(Keys.TAB)
            self.wait_seconds(0.3)

            log.info(f"{field_label} filled: {date_value}")
        except Exception as e:
            log.warning(f"Failed to fill {field_label}: {e}")

    # ==============================================================
    #  Fill form fields — Detail grid section
    # ==============================================================

    def fill_detail_row(self, row_index=0, data=None):
        """Fill a detail row in the Quality Parameter Details grid.

        data dict keys:
          - quality_parameter  (str, required — will select from dropdown)
          - min_quality_value  (str, required)
          - max_quality_value  (str, required)
          - is_rate_percentage (bool, required — True="Yes", False="No")
          - multiplier         (str, required)

        If quality_parameter is None, selects a random option.
        """
        if data is None:
            data = {}

        log.info(f"Filling detail row {row_index}...")

        # 1. Quality Parameter (mat-select in detail grid)
        if data.get("quality_parameter") is not None or data.get("select_qp", True):
            self._fill_detail_quality_parameter(
                row_index, data.get("quality_parameter")
            )

        # 2. Min Quality Value
        if data.get("min_quality_value") is not None:
            self._fill_detail_text_input(
                "Min Quality Value", row_index, str(data["min_quality_value"])
            )

        # 3. Max Quality Value
        if data.get("max_quality_value") is not None:
            self._fill_detail_text_input(
                "Max Quality Value", row_index, str(data["max_quality_value"])
            )

        # 4. Is Rate/Percentage toggle
        if data.get("is_rate_percentage") is not None:
            self._set_detail_toggle(row_index, data["is_rate_percentage"])

        # 5. Multiplier
        if data.get("multiplier") is not None:
            self._fill_detail_text_input(
                "Multiplier", row_index, str(data["multiplier"])
            )

        self._force_close_panels()
        log.info(f"Detail row {row_index} filled")

    def _fill_detail_quality_parameter(self, row_index=0, quality_param=None):
        """Select a Quality Parameter in the detail grid."""
        log.info(f"Filling detail QP select (row {row_index}): {quality_param or 'random'}")
        try:
            # Find detail mat-selects (these are in the detail grid area, not header)
            # Detail selects appear after the header selects
            all_selects = self.driver.find_elements(
                By.CSS_SELECTOR,
                ".big-model mat-select, "
                ".popup-body mat-select, "
                "mat-dialog-container mat-select"
            )
            # Header has 2 selects (Item Name, Transaction Type)
            # Detail grid selects start from index 2+
            detail_selects = all_selects[2:] if len(all_selects) > 2 else all_selects

            if row_index < len(detail_selects):
                selected = self._select_mat_option(
                    detail_selects[row_index], quality_param
                )
                return selected

            # Fallback: try the last mat-select in the popup
            if all_selects:
                selected = self._select_mat_option(all_selects[-1], quality_param)
                return selected

        except Exception as e:
            log.warning(f"Failed to fill detail QP: {e}")
        return ""

    def _fill_detail_text_input(self, field_name, row_index=0, value=""):
        """Fill a text input in the detail grid by field name.

        Handles the ERP bug where name attributes have trailing tab
        characters (e.g. name="Min Quality Value\t").
        Strategy 1: CSS [name^='...'] (starts-with)
        Strategy 2: XPath contains(@name, '...')
        Strategy 3: Find by position in detail grid (last resort)
        """
        log.info(f"Filling detail {field_name} (row {row_index}): {value}")

        target = None

        # Strategy 1: CSS starts-with selector (handles trailing tabs)
        try:
            inputs = self.driver.find_elements(
                By.CSS_SELECTOR,
                f"input[name^='{field_name}']"
            )
            if row_index < len(inputs):
                target = inputs[row_index]
            elif inputs:
                target = inputs[-1]
        except Exception:
            pass

        # Strategy 2: XPath contains (more forgiving)
        if target is None:
            try:
                inputs = self.driver.find_elements(
                    By.XPATH,
                    f".//input[contains(@name, '{field_name}')]"
                )
                if row_index < len(inputs):
                    target = inputs[row_index]
                elif inputs:
                    target = inputs[-1]
            except Exception:
                pass

        # Strategy 3: Find by position in detail grid table
        if target is None:
            try:
                # Map field names to column positions in detail grid
                # Columns: QP | Min Value | Max Value | Toggle | Multiplier
                col_map = {
                    "Min Quality Value": 1,
                    "Max Quality Value": 2,
                    "Multiplier": 3,
                }
                col_idx = col_map.get(field_name, 0)
                if col_idx > 0:
                    # Find text inputs inside the detail table
                    detail_inputs = self.driver.find_elements(
                        By.CSS_SELECTOR,
                        ".popup-body table input[type='text'], "
                        ".big-model table input[type='text'], "
                        ".popup-body table input:not([matdatepicker]), "
                        ".big-model table input:not([matdatepicker])"
                    )
                    # Filter to inputs inside the detail grid (not header)
                    if len(detail_inputs) >= col_idx:
                        target = detail_inputs[col_idx - 1]
                        log.info(
                            f"Found {field_name} by position "
                            f"(col {col_idx}) in detail grid"
                        )
            except Exception:
                pass

        if target is None:
            log.warning(
                f"Could not find input for '{field_name}' — "
                f"field will be left empty!"
            )
            return

        # Fill the found input
        try:
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});", target
            )
            self.driver.execute_script(
                "var s = Object.getOwnPropertyDescriptor("
                "window.HTMLInputElement.prototype,'value').set;"
                "s.call(arguments[0], '');"
                "arguments[0].dispatchEvent(new Event('input',{bubbles:true}));",
                target,
            )
            target.send_keys(value)
            self.wait_seconds(0.3)
            log.info(f"Successfully filled {field_name}: {value}")
        except Exception as e:
            log.warning(f"Failed to fill detail {field_name}: {e}")

    def _set_detail_toggle(self, row_index=0, value=False):
        """Set the Is Rate/Percentage slide toggle.
        value=True means "Yes", value=False means "No".
        """
        log.info(f"Setting detail toggle (row {row_index}): {'Yes' if value else 'No'}")
        try:
            toggles = self.driver.find_elements(
                By.CSS_SELECTOR,
                "app-slide-toggle-v2 .switch-container"
            )
            if row_index < len(toggles):
                toggle = toggles[row_index]
            elif toggles:
                toggle = toggles[-1]
            else:
                log.warning("No toggle switch found in detail grid")
                return

            # Read current state
            current_state = self._read_toggle_state(toggle)

            # Only click if we need to change the state
            if current_state != value:
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});"
                    "arguments[0].click();",
                    toggle,
                )
                self.wait_seconds(0.5)
                log.info(f"Toggle switched to: {'Yes' if value else 'No'}")
            else:
                log.info(f"Toggle already set to: {'Yes' if value else 'No'}")

        except Exception as e:
            log.warning(f"Failed to set detail toggle: {e}")

    def _read_toggle_state(self, toggle_element):
        """Read the current state of a slide toggle.
        Returns True if "Yes"/"On", False if "No"/"Off".
        """
        try:
            # Check for 'active' or 'on' class
            classes = toggle_element.get_attribute("class") or ""
            if "active" in classes or "on" in classes:
                return True

            # Check the state label
            try:
                on_label = toggle_element.find_element(
                    By.CSS_SELECTOR, ".state-label.on"
                )
                if on_label.is_displayed():
                    return True
            except Exception:
                pass

            try:
                off_label = toggle_element.find_element(
                    By.CSS_SELECTOR, ".state-label.off"
                )
                if off_label.is_displayed():
                    return False
            except Exception:
                pass

            # Check the slider position
            try:
                slider = toggle_element.find_element(
                    By.CSS_SELECTOR, ".slider"
                )
                slider_classes = slider.get_attribute("class") or ""
                if "active" in slider_classes or "right" in slider_classes:
                    return True
            except Exception:
                pass

        except Exception:
            pass
        return False

    # ==============================================================
    #  Type text helper (with fallback)
    # ==============================================================

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
        if fallback_locator:
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
                "mat-dialog-container input[type='text']",
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

        log.warning(f"Could not type '{text}' - no suitable input found")

    # ==============================================================
    #  Read form field values
    # ==============================================================

    def get_form_values(self):
        """Read all header form field values from the currently open popup.
        Returns a dict with keys: item_name, transaction_type, from_date,
        to_date, revision_status.
        """
        values = {}

        # Item Name — read from mat-select trigger text
        try:
            selects = self.driver.find_elements(
                By.CSS_SELECTOR,
                ".big-model .form-field mat-select, "
                ".popup-body .form-field mat-select, "
                "mat-dialog-container .form-field mat-select"
            )
            if selects:
                values["item_name"] = selects[0].text.strip()
            if len(selects) >= 2:
                values["transaction_type"] = selects[1].text.strip()
        except Exception:
            pass

        # Date inputs — use placeholder selector (ERP uses custom dual-input)
        try:
            date_inputs = self.driver.find_elements(
                By.CSS_SELECTOR, "input[placeholder='DD/MM/YYYY']"
            )
            if date_inputs:
                values["from_date"] = date_inputs[0].get_attribute("value") or ""
            if len(date_inputs) >= 2:
                values["to_date"] = date_inputs[1].get_attribute("value") or ""
        except Exception:
            pass

        # Revision Status
        try:
            rev_input = self.driver.find_element(
                By.CSS_SELECTOR, "input[name='Revision Status']"
            )
            values["revision_status"] = rev_input.get_attribute("value") or ""
        except Exception:
            values["revision_status"] = ""

        return values

    # ==============================================================
    #  Submit / Update / Cancel
    # ==============================================================

    def submit(self):
        """Click the Submit button (Create mode)."""
        log.info("Submitting CQP form...")
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
                self.wait_seconds(2)
                return
        except Exception:
            pass

        # Fallback: find any Submit button in popup
        try:
            btns = self.driver.find_elements(
                By.CSS_SELECTOR, ".popup-footer button"
            )
            for b in btns:
                if b.text.strip() == "Submit" and b.is_displayed():
                    self.driver.execute_script("arguments[0].click();", b)
                    log.info("Submit clicked via fallback")
                    self.wait_seconds(2)
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
                self.wait_seconds(2)
                return
        except Exception:
            pass

        try:
            btns = self.driver.find_elements(
                By.CSS_SELECTOR, ".popup-footer button"
            )
            for b in btns:
                if b.text.strip() == "Update" and b.is_displayed():
                    self.driver.execute_script("arguments[0].click();", b)
                    log.info("Update clicked via fallback")
                    self.wait_seconds(2)
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

        try:
            btns = self.driver.find_elements(
                By.CSS_SELECTOR, ".popup-footer button"
            )
            for b in btns:
                if b.text.strip() == "Cancel" and b.is_displayed():
                    self.driver.execute_script("arguments[0].click();", b)
                    self.wait_seconds(0.5)
                    return
        except Exception:
            pass
        log.warning("Cancel button not found")

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
        """Handle 'Validation Failed' SweetAlert2 popup (Type A)."""
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
        """Handle 'Failed to save record' SweetAlert2 popup (Type B)."""
        log.info("Handling save failure alert...")
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, "#swal2-title")
                )
            )
            title = self.get_swal_title()
            log.info(f"Save failure alert: {title}")

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
    #  Mode detection
    # ==============================================================

    def is_add_form_open(self):
        """Check if the Add form is open."""
        # Check for form popup + any select/input visible
        popup_visible = self._is_form_popup_open()
        if popup_visible:
            try:
                inputs = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    "div.big-model input, "
                    "div.big-model mat-select, "
                    "div.edit_pop_up input, "
                    "div.edit_pop_up mat-select, "
                    "mat-dialog-container input, "
                    "mat-dialog-container mat-select"
                )
                for el in inputs:
                    try:
                        if el.is_displayed():
                            return True
                    except Exception:
                        continue
            except Exception:
                pass
        return False

    def is_form_closed(self):
        """Check if the form popup is closed."""
        return not self._is_form_popup_open()

    def is_edit_mode(self):
        """Check if the form is in Edit mode (has Update button)."""
        try:
            return self.is_displayed(self.UPDATE_BUTTON, timeout=5)
        except (InvalidSessionIdException, WebDriverException):
            raise
        except Exception:
            return False

    def is_view_mode(self):
        """Check if the form is in View mode (all fields disabled)."""
        try:
            has_submit = self.is_displayed(self.SUBMIT_BUTTON, timeout=2)
            has_update = self.is_displayed(self.UPDATE_BUTTON, timeout=2)
            if has_submit or has_update:
                return False

            # Check if any select is disabled
            try:
                selects = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    ".big-model mat-select, "
                    ".edit_pop_up mat-select, "
                    "mat-dialog-container mat-select"
                )
                for sel in selects:
                    if sel.is_displayed() and not sel.is_enabled():
                        return True
            except Exception:
                pass
        except (InvalidSessionIdException, WebDriverException):
            raise
        except Exception:
            pass
        return False

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

    def click_version_button(self, item_name=None, row_index=0):
        """Click the Version button on a table row.
        Note: Uses cdk-column-folder (NOT cdk-column-version).
        """
        log.info(f"Clicking Version button (name={item_name}, row={row_index})...")
        if item_name:
            try:
                locator = (
                    "xpath",
                    f"//td[contains(text(),'{item_name}')]"
                    "/ancestor::tr//td[contains(@class,'cdk-column-folder')]"
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

        return self._click_action_button_by_index(row_index, 3)

    def _click_action_button_by_index(self, row_index, btn_index):
        """Click an action button by row and button index."""
        try:
            rows = self.driver.find_elements(
                By.CSS_SELECTOR, "table#excel-table tbody tr"
            )
            if row_index < len(rows):
                btns = rows[row_index].find_elements(
                    By.CSS_SELECTOR, "button.tblActnBtn, button"
                )
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
    #  History popup
    # ==============================================================

    def is_history_popup_open(self):
        """Check if the History popup is visible."""
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
            raise
        except Exception:
            pass
        return False

    def close_history_popup(self):
        """Close the History popup."""
        log.info("Closing History popup...")
        try:
            close_btn = self.find_visible_element(
                self.HISTORY_CLOSE_BUTTON, timeout=5
            )
            if close_btn:
                self.driver.execute_script(
                    "arguments[0].click();", close_btn
                )
                self.wait_seconds(0.5)
                return
        except Exception:
            pass

        # Fallback: find any Cancel/Close in visible popup
        try:
            btns = self.driver.find_elements(
                By.XPATH,
                "//div[contains(@class,'popup-overlay') "
                "or contains(@class,'big-model')]"
                "//button[contains(.,'Cancel') or contains(.,'Close')]"
            )
            for btn in btns:
                try:
                    if btn.is_displayed():
                        self.driver.execute_script(
                            "arguments[0].click();", btn
                        )
                        self.wait_seconds(0.5)
                        return
                except Exception:
                    continue
        except Exception:
            pass

        # Fallback: click the close icon in history popup header
        try:
            close_icons = self.driver.find_elements(
                By.CSS_SELECTOR,
                "div.popup-overlay .popup-header .action-btn mat-icon, "
                "div.big-model .popup-header .action-btn mat-icon"
            )
            for icon in close_icons:
                try:
                    if icon.text.strip().lower() == "close" and icon.is_displayed():
                        self.driver.execute_script(
                            "arguments[0].closest('button').click();", icon
                        )
                        self.wait_seconds(0.5)
                        return
                except Exception:
                    continue
        except Exception:
            pass

        log.warning("Could not close History popup")

    def get_history_row_count(self):
        """Count rows in the History popup table.
        Includes div.popup-overlay container selectors.
        """
        try:
            rows = self.driver.find_elements(
                By.CSS_SELECTOR,
                "div.popup-overlay table tbody tr, "
                ".popup-body table tbody tr, "
                ".big-model table tbody tr"
            )
            count = len(rows)
            log.info(f"History row count: {count}")
            return count
        except Exception:
            return 0

    def search_in_history(self, search_text):
        """Search within the history popup."""
        log.info(f"Searching in history: {search_text}")
        try:
            search_input = self.driver.find_element(
                By.CSS_SELECTOR,
                "div.popup-overlay input[aria-label='Search box'], "
                ".popup-body input[aria-label='Search box'], "
                "app-dynamic-history input"
            )
            search_input.clear()
            search_input.send_keys(search_text)
            self.wait_seconds(1)
            return True
        except Exception:
            log.warning("Could not find history search input")
            return False

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

    def get_all_item_names(self):
        """List all Item Name values in the table."""
        names = []
        for css_selector in [
            "table#excel-table tbody td.cdk-column-item_ref_id",
            "table#excel-table tbody td.mat-column-item_ref_id",
        ]:
            try:
                cells = self.driver.find_elements(
                    By.CSS_SELECTOR, css_selector
                )
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

        # Fallback: get text from first data column of each row
        try:
            rows = self.driver.find_elements(
                By.CSS_SELECTOR, "table#excel-table tbody tr"
            )
            for row in rows:
                try:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    data_cells = [c for c in cells if c.text.strip()]
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

    def is_cqp_in_table(self, item_name):
        """Check if a CQP record with the given Item Name appears in the table."""
        names = self.get_all_item_names()
        return any(
            item_name.strip().lower() in n.lower() for n in names
        )

    def find_cqp_row_index(self, item_name):
        """Find the 0-based row index for a CQP by Item Name."""
        rows = self.driver.find_elements(
            By.CSS_SELECTOR, "table#excel-table tbody tr"
        )
        for i, row in enumerate(rows):
            try:
                cells = row.find_elements(By.TAG_NAME, "td")
                for cell in cells:
                    if (
                        item_name.strip().lower()
                        in cell.text.strip().lower()
                    ):
                        return i
            except StaleElementReferenceException:
                continue
        return -1

    # ==============================================================
    #  Search helpers
    # ==============================================================

    def search_cqp(self, search_text):
        """Search for a CQP record. Returns True if found.

        Workflow:
          1. Click the Search toggle button to reveal the input
          2. Type the search text
          3. Press Enter
          4. Check if any result matches
        """
        log.info(f"Searching CQP: {search_text}")

        # Step 1: Click the Search toggle button to reveal the input
        try:
            search_btns = self.driver.find_elements(
                By.CSS_SELECTOR,
                "button[aria-label='Search'], button.search-btn"
            )
            for btn in search_btns:
                try:
                    if btn.is_displayed():
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({block:'center'});"
                            "arguments[0].click();",
                            btn,
                        )
                        self.wait_seconds(1)
                        break
                except Exception:
                    continue
        except Exception:
            pass

        # Step 2: Find and fill the search input
        try:
            search_input = None
            for css in [
                "input#erpSearchInput",
                ".erp-search-wrapper input",
                "input[placeholder='Search...']",
                "input[placeholder='Search']",
            ]:
                try:
                    candidates = self.driver.find_elements(
                        By.CSS_SELECTOR, css
                    )
                    for inp in candidates:
                        try:
                            if inp.is_displayed():
                                search_input = inp
                                break
                        except Exception:
                            continue
                    if search_input:
                        break
                except Exception:
                    continue

            if search_input is None:
                log.warning("Search input not found after clicking Search button")
                return False

            search_input.clear()
            search_input.send_keys(search_text)
            self.wait_seconds(1)
            search_input.send_keys(Keys.ENTER)
            self.wait_seconds(2)

            # Check if any result contains the search text
            return self.is_cqp_in_table(search_text)
        except Exception as e:
            log.warning(f"Search failed: {e}")
            return False

    def clear_search(self):
        """Clear the search input and wait for table refresh."""
        log.info("Clearing search...")
        try:
            search_input = None
            for css in [
                "input#erpSearchInput",
                ".erp-search-wrapper input",
                "input[placeholder='Search...']",
                "input[placeholder='Search']",
            ]:
                try:
                    candidates = self.driver.find_elements(
                        By.CSS_SELECTOR, css
                    )
                    for inp in candidates:
                        try:
                            if inp.is_displayed():
                                search_input = inp
                                break
                        except Exception:
                            continue
                    if search_input:
                        break
                except Exception:
                    continue

            if search_input:
                search_input.clear()
                search_input.send_keys(Keys.ENTER)
                self.wait_seconds(2)
                log.info("Search cleared")
            else:
                log.info("Search input not visible — may already be closed")
        except Exception:
            pass

    # ==============================================================
    #  Filter helpers
    # ==============================================================

    def open_filter_panel(self):
        """Open the filter panel.
        Uses button[mattooltip='Filters'] / button.filter-btn selectors.
        """
        log.info("Opening filter panel...")

        # Strategy 1: mattooltip selector (primary)
        try:
            btns = self.driver.find_elements(
                By.CSS_SELECTOR,
                "button[mattooltip='Filters'], button.filter-btn"
            )
            for btn in btns:
                try:
                    if btn.is_displayed():
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({block:'center'});"
                            "arguments[0].click();",
                            btn,
                        )
                        self.wait_seconds(1)
                        log.info("Filter panel opened via mattooltip")
                        return True
                except Exception:
                    continue
        except Exception:
            pass

        # Strategy 2: erp-outline-btn with filter_list icon
        try:
            btns = self.driver.find_elements(
                By.CSS_SELECTOR, "button.erp-outline-btn"
            )
            for btn in btns:
                try:
                    icon = btn.find_element(
                        By.CSS_SELECTOR, "i.material-icons, mat-icon"
                    )
                    if (
                        icon.text.strip().lower() == "filter_list"
                        and btn.is_displayed()
                    ):
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({block:'center'});"
                            "arguments[0].click();",
                            btn,
                        )
                        self.wait_seconds(1)
                        log.info("Filter panel opened via outline-btn")
                        return True
                except Exception:
                    continue
        except Exception:
            pass

        # Strategy 3: Use the FILTER_TOGGLE locator
        try:
            self.click_with_retry(self.FILTER_TOGGLE)
            self.wait_seconds(1)
            log.info("Filter panel opened via locator")
            return True
        except Exception:
            pass

        log.warning("Filter button not found")
        return False

    def close_filter_panel(self):
        """Close the filter panel."""
        log.info("Closing filter panel...")
        try:
            close_btns = self.driver.find_elements(
                By.XPATH,
                "//div[contains(@class,'filter-panel')]"
                "//button[contains(.,'close')]"
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

    def apply_filters(self):
        """Click Apply Filters button in filter panel."""
        log.info("Applying filters...")
        try:
            apply_btns = self.driver.find_elements(
                By.XPATH,
                "//button[contains(.,'Apply Filters') or contains(.,'check')]"
            )
            for btn in apply_btns:
                try:
                    if btn.is_displayed():
                        self.driver.execute_script("arguments[0].click();", btn)
                        self.wait_seconds(2)
                        return True
                except Exception:
                    continue
        except Exception:
            pass
        return False

    def clear_all_filters(self):
        """Click Clear All in filter panel."""
        log.info("Clearing all filters...")
        try:
            clear_btns = self.driver.find_elements(
                By.XPATH,
                "//button[contains(.,'Clear All') or contains(.,'clear_all')]"
            )
            for btn in clear_btns:
                try:
                    if btn.is_displayed():
                        self.driver.execute_script("arguments[0].click();", btn)
                        self.wait_seconds(1)
                        return True
                except Exception:
                    continue
        except Exception:
            pass
        return False

    # ==============================================================
    #  Pagination helpers
    # ==============================================================

    def get_pagination_info(self):
        """Read the pagination range text (e.g., '1 - 10 of 15')."""
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
        """Click the next page button."""
        log.info("Clicking next page...")
        try:
            btn = self.driver.find_element(
                By.CSS_SELECTOR,
                "button.mat-paginator-navigation-next, "
                "button[aria-label='Next page']",
            )
            self.driver.execute_script("arguments[0].click();", btn)
            self.wait_seconds(2)
            return True
        except Exception:
            return False

    def click_previous_page(self):
        """Click the previous page button."""
        log.info("Clicking previous page...")
        try:
            btn = self.driver.find_element(
                By.CSS_SELECTOR,
                "button.mat-paginator-navigation-previous, "
                "button[aria-label='Previous page']",
            )
            self.driver.execute_script("arguments[0].click();", btn)
            self.wait_seconds(2)
            return True
        except Exception:
            return False

    # ==============================================================
    #  Sort helpers
    # ==============================================================

    def click_sort_column(self, column_name):
        """Click a sortable column header to sort."""
        log.info(f"Clicking sort on column: {column_name}")
        try:
            # Map column names to CSS classes
            column_map = {
                "Item Name": "cdk-column-item_ref_id",
                "Transaction Type": "cdk-column-transaction_type",
                "From Date": "cdk-column-from_date",
                "To Date": "cdk-column-to_date",
                "Revision Status": "cdk-column-revision_status",
            }
            col_class = column_map.get(column_name, "")
            if col_class:
                header = self.driver.find_element(
                    By.CSS_SELECTOR,
                    f"th.{col_class} mat-sort-header, "
                    f"th.{col_class} .mat-sort-header"
                )
                self.driver.execute_script("arguments[0].click();", header)
                self.wait_seconds(2)
                return True
        except Exception:
            pass
        return False

    # ==============================================================
    #  High-level workflow methods
    # ==============================================================

    def create_cqp(self, header_data, detail_data=None):
        """Create a complete CQP record with header + detail row.

        Args:
            header_data: dict with header fields
            detail_data: dict with detail row fields (if None, auto-generates)

        Returns:
            dict with keys:
              - item_name: str — the Item Name used
              - created: bool — True if creation succeeded
              - alert_title: str — SweetAlert title if any appeared
        """
        log.info("Creating CQP record...")

        self.open_add_form()
        self.wait_seconds(1)
        assert self.is_add_form_open(), "Add form did not open"

        # Fill header
        self.fill_form(header_data)
        self.wait_seconds(1)

        # Read what Item Name was selected
        item_name = ""
        try:
            selects = self.driver.find_elements(
                By.CSS_SELECTOR,
                ".big-model mat-select, .popup-body mat-select, "
                "mat-dialog-container mat-select"
            )
            if selects:
                item_name = selects[0].text.strip()
        except Exception:
            pass

        # Fill detail row
        if detail_data is None:
            detail_data = {}
        self.fill_detail_row(0, detail_data)
        self.wait_seconds(1)

        # Verify all required detail fields were actually filled
        self._verify_detail_fields_filled(detail_data)

        # Submit
        self.submit()
        self.wait_seconds(2)

        # Check for SweetAlert response
        alert_title = ""
        created = False
        if self.is_validation_alert_present(timeout=5):
            alert_title = self.get_swal_title() or ""
            log.info(f"SweetAlert after submit: {alert_title}")

            if "saved successfully" in alert_title.lower():
                created = True
                self._dismiss_swal_confirm()
                self._cleanup_swal_containers()
                log.info("CQP creation SUCCEEDED (success alert)")
            elif "validation" in alert_title.lower() or "failed" in alert_title.lower():
                self.handle_validation_warning(timeout=5)
                log.warning(f"CQP creation FAILED (alert: {alert_title})")
            else:
                self.handle_validation_warning(timeout=5)
                log.warning(f"CQP creation — unexpected alert: {alert_title}")
        else:
            # No alert appeared — check if form closed (older flow)
            if self.is_form_closed():
                created = True
                log.info("CQP creation SUCCEEDED (form closed, no alert)")
            else:
                log.warning("CQP creation — no alert and form still open")
                # Try to detect success by checking if success popup appeared
                try:
                    success_el = self.driver.find_element(
                        By.CSS_SELECTOR, "#swal2-title"
                    )
                    if success_el.is_displayed():
                        alert_title = success_el.text.strip()
                        if "saved successfully" in alert_title.lower():
                            created = True
                            self._dismiss_swal_confirm()
                            self._cleanup_swal_containers()
                except Exception:
                    pass

        # Track submission
        CQP_SUBMISSIONS.append({
            "item_name": item_name,
            "header_data": header_data,
            "detail_data": detail_data,
            "created": created,
            "alert_title": alert_title,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        })

        log.info(
            f"CQP creation {'SUCCEEDED' if created else 'FAILED'}: "
            f"{item_name} (alert: {alert_title})"
        )
        return {
            "item_name": item_name,
            "created": created,
            "alert_title": alert_title,
        }

    def verify_record_in_table(self, item_name):
        """Verify a CQP record exists in the listing table.

        Uses Refresh + Search to find the record.

        Returns:
            True if the record is found, False otherwise.
        """
        log.info(f"Verifying CQP record in table: {item_name}")

        # Refresh the table
        self.click_refresh()
        self.wait_seconds(2)

        # Search for the record
        found = self.search_cqp(item_name)
        if found:
            log.info(f"CQP record FOUND in table: {item_name}")
        else:
            log.warning(f"CQP record NOT found in table: {item_name}")

        # Clear search to restore full table
        self.clear_search()

        return found

    def _verify_detail_fields_filled(self, detail_data):
        """Verify that all required detail fields have values.
        Logs warnings for any field that appears empty.
        This catches cases where CSS selectors failed to find the input.
        """
        log.info("Verifying detail fields were filled...")

        # Check Min Quality Value
        try:
            min_inputs = self.driver.find_elements(
                By.CSS_SELECTOR, "input[name^='Min Quality Value']"
            )
            if min_inputs:
                val = min_inputs[0].get_attribute("value") or ""
                if not val.strip():
                    log.warning(
                        "Min Quality Value is EMPTY after fill attempt! "
                        "CSS selector may have missed the input."
                    )
                    # Try XPath fallback to fill it now
                    if detail_data.get("min_quality_value"):
                        self._fill_detail_text_input_fallback(
                            "Min Quality Value",
                            str(detail_data["min_quality_value"])
                        )
                else:
                    log.info(f"Min Quality Value filled: {val}")
            else:
                log.warning("No Min Quality Value input found during verification!")
        except Exception:
            pass

        # Check Max Quality Value
        try:
            max_inputs = self.driver.find_elements(
                By.CSS_SELECTOR, "input[name^='Max Quality Value']"
            )
            if max_inputs:
                val = max_inputs[0].get_attribute("value") or ""
                if not val.strip():
                    log.warning(
                        "Max Quality Value is EMPTY after fill attempt!"
                    )
                    if detail_data.get("max_quality_value"):
                        self._fill_detail_text_input_fallback(
                            "Max Quality Value",
                            str(detail_data["max_quality_value"])
                        )
                else:
                    log.info(f"Max Quality Value filled: {val}")
            else:
                log.warning("No Max Quality Value input found during verification!")
        except Exception:
            pass

        # Check Multiplier
        try:
            mult_inputs = self.driver.find_elements(
                By.CSS_SELECTOR, "input[name^='Multiplier']"
            )
            if mult_inputs:
                val = mult_inputs[0].get_attribute("value") or ""
                if not val.strip():
                    log.warning(
                        "Multiplier is EMPTY after fill attempt!"
                    )
                    if detail_data.get("multiplier"):
                        self._fill_detail_text_input_fallback(
                            "Multiplier",
                            str(detail_data["multiplier"])
                        )
                else:
                    log.info(f"Multiplier filled: {val}")
            else:
                log.warning("No Multiplier input found during verification!")
        except Exception:
            pass

    def _fill_detail_text_input_fallback(self, field_name, value):
        """Last-resort fallback to fill a detail text input using JS."""
        log.info(f"JS fallback fill for {field_name}: {value}")
        try:
            # Use XPath contains to find the input
            inputs = self.driver.find_elements(
                By.XPATH,
                f".//input[contains(@name, '{field_name}')]"
            )
            if inputs:
                target = inputs[0]
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});", target
                )
                self.driver.execute_script(
                    "var s = Object.getOwnPropertyDescriptor("
                    "window.HTMLInputElement.prototype,'value').set;"
                    "s.call(arguments[0], arguments[1]);"
                    "arguments[0].dispatchEvent(new Event('input',{bubbles:true}));"
                    "arguments[0].dispatchEvent(new Event('change',{bubbles:true}));",
                    target, value,
                )
                self.wait_seconds(0.3)
                log.info(f"JS fallback filled {field_name}: {value}")
            else:
                # Ultra-last-resort: find ALL text inputs in detail table
                log.warning(f"XPath fallback also failed for {field_name}")
                self._fill_by_position_fallback(field_name, value)
        except Exception as e:
            log.warning(f"JS fallback failed for {field_name}: {e}")

    def _fill_by_position_fallback(self, field_name, value):
        """Ultra-last-resort: fill input by its position in the detail grid."""
        log.info(f"Position fallback fill for {field_name}: {value}")
        try:
            # Find all text inputs inside the big-model/popup-body table
            # that are NOT datepickers and NOT in the header section
            all_inputs = self.driver.find_elements(
                By.CSS_SELECTOR,
                ".big-model table input:not([matdatepicker]), "
                ".popup-body table input:not([matdatepicker]), "
                "mat-dialog-container table input:not([matdatepicker])"
            )
            log.info(f"Found {len(all_inputs)} non-datepicker inputs in detail table")

            # Map field names to positions (0-based)
            # Detail grid columns: QP(select) | Min(0) | Max(1) | Toggle | Multiplier(2)
            pos_map = {
                "Min Quality Value": 0,
                "Max Quality Value": 1,
                "Multiplier": 2,
            }
            pos = pos_map.get(field_name)
            if pos is not None and pos < len(all_inputs):
                target = all_inputs[pos]
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});", target
                )
                self.driver.execute_script(
                    "var s = Object.getOwnPropertyDescriptor("
                    "window.HTMLInputElement.prototype,'value').set;"
                    "s.call(arguments[0], arguments[1]);"
                    "arguments[0].dispatchEvent(new Event('input',{bubbles:true}));"
                    "arguments[0].dispatchEvent(new Event('change',{bubbles:true}));",
                    target, value,
                )
                self.wait_seconds(0.3)
                log.info(f"Position fallback filled {field_name} at pos {pos}: {value}")
            else:
                log.warning(
                    f"Position fallback failed for {field_name}: "
                    f"pos={pos}, available inputs={len(all_inputs)}"
                )
        except Exception as e:
            log.warning(f"Position fallback failed for {field_name}: {e}")

    def view_cqp(self, item_name=None, row_index=0):
        """View a CQP record."""
        log.info(f"Viewing CQP: {item_name}")
        self.click_view_button(item_name=item_name, row_index=row_index)
        self.wait_seconds(1)
        return self.get_form_values()

    def edit_cqp(self, item_name=None, row_index=0, new_data=None):
        """Edit a CQP record."""
        log.info(f"Editing CQP: {item_name}")
        self.click_edit_button(item_name=item_name, row_index=row_index)
        self.wait_seconds(1)

        if new_data:
            self.fill_form(new_data)
            self.wait_seconds(1)

        self.click_update()
        self.wait_seconds(2)

        # Handle SweetAlert
        if self.is_validation_alert_present(timeout=3):
            self.handle_validation_warning(timeout=5)

    def check_history(self, item_name=None, row_index=0):
        """Open the History popup for a CQP record."""
        log.info(f"Checking history: {item_name}")
        self.click_history_button(item_name=item_name, row_index=row_index)
        self.wait_seconds(1)
        return self.is_history_popup_open()
