"""
commodity_base_rate_page.py
--------------------------
Page Object Model for RhythmERP Commodity Base Rate screen.

Location: Commodity Settings > Commodity Base Rate
URL:      /#/dynamic-screens/Commodity%20Base%20Rate

FORM LAYOUT (two-step stepper):
  Step 1: Pricing Type (mat-select), From Date (datepicker),
          To Date (datepicker), Location (mat-select)
  Step 2: Grid with Item Name (mat-select), Item Rate (input), UOM (mat-select)

TABLE COLUMNS (visible):
  - View / Edit / Version / History (action buttons per row)
  - Pricing Type, From Date, To Date, Location

KNOWN BUGS:
  BUG-001 (HIGH)  : Item Rate accepts non-numeric input
  BUG-002 (MEDIUM): Item Rate accepts zero value
  BUG-003 (MEDIUM): Listing shows raw ISO timestamps
  BUG-004 (HIGH)  : To Date overridden to 30/12/2099 on submit
  BUG-005 (LOW)   : Edit disabled for new records
  BUG-006 (MEDIUM): Version creation fails with same From Date

KEY RULES:
  - NEVER use Keys.ESCAPE (use backdrop click + JS overlay removal)
  - JS clicks for Angular Material overlays (mat-select, datepicker)
  - _force_close_panels() uses JS removal, NOT Escape key
  - SweetAlert2 for success/error popups
  - LABEL-BASED XPath for form fields (NOT name/formcontrolname CSS)
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
    NoSuchElementException,
    ElementClickInterceptedException,
    StaleElementReferenceException,
)
from common.base_page import BasePage
from common.logger import log
from config import RHYTHMERP_BASE_URL, EXPLICIT_WAIT


class CommodityBaseRatePage(BasePage):
    PAGE_URL = (
        f"{RHYTHMERP_BASE_URL}"
        "/#/dynamic-screens/Commodity%20Base%20Rate"
    )

    # ==============================================================
    #  LOCATORS — Toolbar
    # ==============================================================
    ADD_BUTTON = (
        "css",
        "button.erp-add-btn",
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
    NO_DATA_ROW = (
        "css",
        "table#excel-table tbody tr td.no-data, "
        "table#excel-table tbody tr.mat-mdc-no-data-row",
    )

    # ==============================================================
    #  LOCATORS — Add / Edit Form (popup or inline)
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

    # ── LABEL-BASED XPath locators for form fields ───────────────
    # These find mat-select/input inside the mat-form-field
    # that contains a mat-label with the given text.
    # This is the ONLY reliable way to locate dynamic screen fields
    # in RhythmERP since name/formcontrolname attributes vary.

    PRICING_TYPE_SELECT = (
        "xpath",
        "//mat-form-field[.//mat-label[contains(text(),'Pricing Type')]]//mat-select",
    )
    FROM_DATE_INPUT = (
        "xpath",
        "//mat-form-field[.//mat-label[contains(text(),'From Date')]]//input",
    )
    TO_DATE_INPUT = (
        "xpath",
        "//mat-form-field[.//mat-label[contains(text(),'To Date')]]//input",
    )
    LOCATION_SELECT = (
        "xpath",
        "//mat-form-field[.//mat-label[contains(text(),'Location')]]//mat-select",
    )

    # Grid / Stepper fields
    ITEM_NAME_SELECT = (
        "xpath",
        "//mat-form-field[.//mat-label[contains(text(),'Item Name')]]//mat-select",
    )
    ITEM_RATE_INPUT = (
        "xpath",
        "//mat-form-field[.//mat-label[contains(text(),'Item Rate')]]//input",
    )
    UOM_SELECT = (
        "xpath",
        "//mat-form-field[.//mat-label[contains(text(),'UOM')]]//mat-select",
    )

    # Form buttons
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

    # Grid add row button
    ADD_GRID_ROW_BUTTON = (
        "css",
        "button.add-row, button[mattooltip='Add Row']",
    )

    # ==============================================================
    #  LOCATORS — Row action buttons
    # ==============================================================
    VIEW_BUTTON = (
        "xpath",
        "//td[contains(@class,'cdk-column-view')]"
        "//button",
    )
    EDIT_BUTTON = (
        "xpath",
        "//td[contains(@class,'cdk-column-edit')]"
        "//button",
    )
    VERSION_BUTTON = (
        "xpath",
        "//td[contains(@class,'cdk-column-version')]"
        "//button",
    )
    HISTORY_BUTTON = (
        "xpath",
        "//td[contains(@class,'cdk-column-history')]"
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
    #  LOCATORS — Stepper
    # ==============================================================
    STEPPER_TABS = ("css", "mat-step-header")

    # ==============================================================
    #  LOCATORS — Pagination
    # ==============================================================
    PAGINATION_NEXT = (
        "css",
        "button.mat-paginator-navigation-next, "
        "button[aria-label='Next page']",
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
        """Navigate to Commodity Base Rate listing page.
        Force-refreshes to clear leftover Angular state.
        """
        log.info("Navigating to Commodity Base Rate page...")
        self.navigate_to(self.PAGE_URL)
        self.driver.refresh()
        self._wait_for_page_ready()

    def _wait_for_page_ready(self):
        """Wait until the CBR page is fully loaded."""
        # Step 1: Wait for table or action buttons
        try:
            WebDriverWait(self.driver, EXPLICIT_WAIT).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, "table#excel-table, button.erp-add-btn")
                )
            )
            log.info("Commodity Base Rate page loaded")
        except TimeoutException:
            log.warning("CBR table not found, page may be loading")

        # Step 2: Wait for toolbar
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "ul.tbl-export-btn, button.erp-add-btn")
                )
            )
            self.wait_seconds(1)
            log.info("CBR toolbar ready")
        except TimeoutException:
            log.warning("Toolbar not found, ADD button may be delayed")
            self.wait_seconds(3)

    def is_page_loaded(self):
        """Check if the CBR listing page has loaded."""
        return self.is_displayed(self.TABLE, timeout=10)

    # ==============================================================
    #  Overlay cleanup — NEVER use Keys.ESCAPE
    # ==============================================================

    def _force_close_panels(self):
        """Remove ALL select overlay panes from the DOM via JS.
        Keeps dialog backdrop intact so form popups stay open.
        Wrapped in try-except to prevent browser crash cascade.
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
        except Exception as e:
            log.warning(f"_force_close_panels failed (browser may be dead): {e}")

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
        self._force_close_panels()

    # ==============================================================
    #  Toolbar actions
    # ==============================================================

    def open_add_form(self):
        """Click the ADD (+) button to open the create form."""
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

        # Strategy 2: mini-fab with 'add' icon
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
                            log.info("ADD form opened via mini-fab")
                            return
                except Exception:
                    continue
        except Exception:
            pass

        # Strategy 3: click_with_retry
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
        """Wait for toolbar and ADD button to be present."""
        for attempt in range(3):
            try:
                btns = self.driver.find_elements(
                    By.CSS_SELECTOR, "button.erp-add-btn"
                )
                if btns and btns[0].is_displayed():
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

    def _is_form_popup_open(self):
        """Check if any form popup is visible."""
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
        """Wait for form content (inputs) to render inside the popup."""
        import time as _time
        deadline = _time.time() + timeout
        while _time.time() < deadline:
            try:
                inputs = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    "div.edit_pop_up input, div.edit_pop_up mat-select, "
                    "div.big-model input, mat-dialog-container input, "
                    "div.cdk-overlay-container input, "
                    "div.cdk-overlay-container mat-select"
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
        log.warning(f"Form content did not render within {timeout}s")
        self._debug_popup_info()
        return False

    def _debug_popup_info(self):
        """Log debug info about popup state for diagnosing locator issues."""
        try:
            # Check what form fields exist in the popup
            all_selects = self.driver.find_elements(
                By.CSS_SELECTOR,
                "div.edit_pop_up mat-select, div.big-model mat-select, "
                "mat-dialog-container mat-select, "
                "div.cdk-overlay-container mat-select"
            )
            all_inputs = self.driver.find_elements(
                By.CSS_SELECTOR,
                "div.edit_pop_up input, div.big-model input, "
                "mat-dialog-container input, "
                "div.cdk-overlay-container input"
            )
            log.info(f"DEBUG: Found {len(all_selects)} mat-select, {len(all_inputs)} inputs in popup")

            for i, sel in enumerate(all_selects):
                try:
                    # Try to find the label for this select
                    label_text = ""
                    try:
                        parent = sel.find_element(By.XPATH, "ancestor::mat-form-field")
                        label_els = parent.find_elements(By.CSS_SELECTOR, "mat-label, label")
                        label_text = ", ".join([l.text.strip() for l in label_els if l.text.strip()])
                    except Exception:
                        pass
                    log.info(
                        f"  Select[{i}]: name={sel.get_attribute('name')}, "
                        f"formcontrolname={sel.get_attribute('formcontrolname')}, "
                        f"aria-label={sel.get_attribute('aria-label')}, "
                        f"visible={sel.is_displayed()}, label={label_text}"
                    )
                except Exception:
                    pass

            for i, inp in enumerate(all_inputs):
                try:
                    label_text = ""
                    try:
                        parent = inp.find_element(By.XPATH, "ancestor::mat-form-field")
                        label_els = parent.find_elements(By.CSS_SELECTOR, "mat-label, label")
                        label_text = ", ".join([l.text.strip() for l in label_els if l.text.strip()])
                    except Exception:
                        pass
                    log.info(
                        f"  Input[{i}]: name={inp.get_attribute('name')}, "
                        f"formcontrolname={inp.get_attribute('formcontrolname')}, "
                        f"type={inp.get_attribute('type')}, "
                        f"placeholder={inp.get_attribute('placeholder')}, "
                        f"visible={inp.is_displayed()}, label={label_text}"
                    )
                except Exception:
                    pass

            # Check mat-labels in popup
            all_labels = self.driver.find_elements(
                By.CSS_SELECTOR,
                "div.edit_pop_up mat-label, div.big-model mat-label, "
                "mat-dialog-container mat-label"
            )
            log.info(f"DEBUG: Found {len(all_labels)} mat-labels in popup")
            for i, lbl in enumerate(all_labels):
                try:
                    log.info(f"  Label[{i}]: text='{lbl.text.strip()}', visible={lbl.is_displayed()}")
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
    #  Mat-Select helpers — LABEL-BASED approach
    # ==============================================================

    def _find_mat_select_by_label(self, label_text, timeout=8):
        """Find a mat-select element by its mat-label text.
        Uses XPath to locate the mat-form-field containing a mat-label
        with the given text, then finds the mat-select inside it.

        This is the PRIMARY method for finding dropdowns in
        RhythmERP dynamic screens, where name/formcontrolname
        attributes are unreliable.
        """
        xpath = (
            f"//mat-form-field[.//mat-label[contains(text(),'{label_text}')]]"
            f"//mat-select"
        )
        log.info(f"Finding mat-select by label: '{label_text}'")
        try:
            el = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            log.info(f"Found mat-select for label: '{label_text}'")
            return el
        except TimeoutException:
            # Fallback: try with <label> instead of <mat-label>
            xpath2 = (
                f"//mat-form-field[.//label[contains(text(),'{label_text}')]]"
                f"//mat-select"
            )
            try:
                el = WebDriverWait(self.driver, 3).until(
                    EC.presence_of_element_located((By.XPATH, xpath2))
                )
                log.info(f"Found mat-select for label (via <label>): '{label_text}'")
                return el
            except TimeoutException:
                pass

            # Fallback: broad search for any mat-select in popup
            log.warning(f"Label-based XPath failed for '{label_text}'. Running debug...")
            self._debug_popup_info()

            # Try finding by CSS with broader selectors
            try:
                selects = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    "div.edit_pop_up mat-select, div.big-model mat-select, "
                    "mat-dialog-container mat-select"
                )
                for sel in selects:
                    try:
                        if sel.is_displayed():
                            # Check if parent has matching label
                            try:
                                parent = sel.find_element(By.XPATH, "ancestor::mat-form-field")
                                labels = parent.find_elements(By.CSS_SELECTOR, "mat-label, label")
                                for lbl in labels:
                                    if label_text.lower() in lbl.text.strip().lower():
                                        log.info(f"Found mat-select via broad CSS + label match: '{label_text}'")
                                        return sel
                            except Exception:
                                pass
                    except Exception:
                        continue
            except Exception:
                pass

            raise NoSuchElementException(
                f"mat-select with label '{label_text}' not found. "
                f"Run debug to see available labels."
            )

    def _find_input_by_label(self, label_text, timeout=8):
        """Find an input element by its mat-label text.
        Uses XPath to locate the mat-form-field containing a mat-label
        with the given text, then finds the input inside it.
        """
        xpath = (
            f"//mat-form-field[.//mat-label[contains(text(),'{label_text}')]]"
            f"//input"
        )
        log.info(f"Finding input by label: '{label_text}'")
        try:
            el = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            log.info(f"Found input for label: '{label_text}'")
            return el
        except TimeoutException:
            # Fallback: try with <label> instead of <mat-label>
            xpath2 = (
                f"//mat-form-field[.//label[contains(text(),'{label_text}')]]"
                f"//input"
            )
            try:
                el = WebDriverWait(self.driver, 3).until(
                    EC.presence_of_element_located((By.XPATH, xpath2))
                )
                log.info(f"Found input for label (via <label>): '{label_text}'")
                return el
            except TimeoutException:
                pass

            log.warning(f"Label-based XPath failed for input '{label_text}'. Running debug...")
            self._debug_popup_info()
            raise NoSuchElementException(
                f"input with label '{label_text}' not found."
            )

    def _open_mat_select_and_choose(self, label_text, option_text):
        """Complete workflow: find mat-select by label, click it, select option.
        This is the PRIMARY method for interacting with dropdowns.
        
        If option_text is None or empty string, selects the FIRST available option.
        If the exact option_text is not found, falls back to the first available option.
        """
        select_first = option_text is None or option_text == ""
        log.info(
            f"Opening mat-select '{label_text}' to select "
            f"{'[FIRST AVAILABLE]' if select_first else repr(option_text)}"
        )
        self._force_close_panels()

        # Step 1: Find the mat-select element by label
        select_el = self._find_mat_select_by_label(label_text)

        # Step 2: Scroll into view and click to open
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'});",
            select_el,
        )
        self.wait_seconds(0.3)

        # Click the select trigger
        try:
            self.driver.execute_script("arguments[0].click();", select_el)
        except Exception:
            # Fallback: click the trigger div inside the select
            try:
                trigger = select_el.find_element(
                    By.CSS_SELECTOR, ".mat-mdc-select-trigger"
                )
                self.driver.execute_script("arguments[0].click();", trigger)
            except Exception:
                select_el.click()

        self.wait_seconds(0.5)

        # Step 3: Wait for overlay options to appear
        try:
            WebDriverWait(self.driver, 8).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, ".cdk-overlay-pane mat-option")
                )
            )
            self.wait_seconds(0.3)
        except TimeoutException:
            log.warning(f"Dropdown overlay did not appear for '{label_text}'. Retrying click...")
            # Retry click
            try:
                self.driver.execute_script("arguments[0].click();", select_el)
                self.wait_seconds(0.8)
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, ".cdk-overlay-pane mat-option")
                    )
                )
            except TimeoutException:
                log.error(f"Dropdown overlay STILL did not appear for '{label_text}'")
                self._force_close_panels()
                raise ValueError(f"Dropdown overlay did not appear for '{label_text}'")

        # Step 4: Collect all available options
        available_options = []
        try:
            option_elements = self.driver.find_elements(
                By.CSS_SELECTOR, "mat-option"
            )
            for opt in option_elements:
                try:
                    txt = opt.text.strip()
                    if txt:
                        available_options.append((txt, opt))
                except StaleElementReferenceException:
                    continue
        except Exception:
            pass

        if not available_options:
            self._force_close_panels()
            raise ValueError(f"No options found in '{label_text}' dropdown")

        # Step 5: Select the option
        selected_text = None

        if select_first:
            # Select first available option
            first_text, first_el = available_options[0]
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});",
                first_el,
            )
            self.wait_seconds(0.2)
            try:
                first_el.click()
            except Exception:
                self.driver.execute_script("arguments[0].click();", first_el)
            self.wait_seconds(0.3)
            selected_text = first_text
            log.info(f"Selected FIRST option '{first_text}' from '{label_text}' dropdown")

        else:
            # Try exact/partial match on option_text
            for opt_text, opt_el in available_options:
                if opt_text == option_text or option_text.lower() in opt_text.lower():
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView({block:'center'});",
                        opt_el,
                    )
                    self.wait_seconds(0.2)
                    try:
                        opt_el.click()
                    except Exception:
                        self.driver.execute_script("arguments[0].click();", opt_el)
                    self.wait_seconds(0.3)
                    selected_text = opt_text
                    log.info(f"Selected '{opt_text}' from '{label_text}' dropdown")
                    break

            if selected_text is None:
                # Fallback: select first available option instead of crashing
                first_text, first_el = available_options[0]
                log.warning(
                    f"Option '{option_text}' not found in '{label_text}' dropdown. "
                    f"Available: {[t for t, _ in available_options]}. "
                    f"Falling back to FIRST option: '{first_text}'"
                )
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});",
                    first_el,
                )
                self.wait_seconds(0.2)
                try:
                    first_el.click()
                except Exception:
                    self.driver.execute_script("arguments[0].click();", first_el)
                self.wait_seconds(0.3)
                selected_text = first_text

        # Close any leftover overlay
        self.wait_seconds(0.2)
        self._force_close_panels()
        return selected_text

    def _select_mat_option(self, option_text):
        """Select an option from an already-open mat-select overlay.
        MUST be called after clicking the mat-select trigger.
        Kept for backward compatibility with code that opens selects manually.
        """
        log.info(f"Selecting mat-option: {option_text}")
        try:
            # Wait for overlay to appear
            WebDriverWait(self.driver, EXPLICIT_WAIT).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, ".cdk-overlay-pane mat-option")
                )
            )
            self.wait_seconds(0.3)

            # Find option by text
            options = self.driver.find_elements(
                By.CSS_SELECTOR, "mat-option"
            )
            for opt in options:
                try:
                    opt_text = opt.text.strip()
                    if opt_text == option_text or option_text.lower() in opt_text.lower():
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({block:'center'});",
                            opt,
                        )
                        self.wait_seconds(0.2)
                        try:
                            opt.click()
                        except Exception:
                            self.driver.execute_script("arguments[0].click();", opt)
                        self.wait_seconds(0.3)
                        log.info(f"Selected option: {option_text}")
                        return True
                except StaleElementReferenceException:
                    continue

            # Fallback: partial match via XPath
            xpath = f"//mat-option[contains(.,'{option_text}')]"
            try:
                el = self.driver.find_element(By.XPATH, xpath)
                self.driver.execute_script("arguments[0].click();", el)
                self.wait_seconds(0.3)
                log.info(f"Selected option via XPath: {option_text}")
                return True
            except Exception:
                pass

            raise ValueError(f"Option '{option_text}' not found in dropdown")
        except TimeoutException:
            raise ValueError(f"Dropdown overlay did not appear for '{option_text}'")

    def _open_mat_select(self, locator):
        """Open a mat-select dropdown using a locator tuple.
        Kept for backward compatibility. Prefer _open_mat_select_and_choose().
        """
        self._force_close_panels()
        try:
            if locator[0] == "xpath":
                el = WebDriverWait(self.driver, 8).until(
                    EC.presence_of_element_located((By.XPATH, locator[1]))
                )
            else:
                el = self.find_visible_element(locator, timeout=8)
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'});"
                "arguments[0].click();",
                el,
            )
            self.wait_seconds(0.5)
        except Exception:
            try:
                self.click_with_retry(locator)
                self.wait_seconds(0.5)
            except Exception:
                log.warning(f"Could not open mat-select with locator: {locator}")

    # ==============================================================
    #  Fill form fields — LABEL-BASED approach
    # ==============================================================

    def fill_form(self, data):
        """Fill the CBR add/edit form with provided data dict.
        Uses LABEL-BASED locators for reliable element finding.

        Supports both single-row and multi-row grid data.
        """
        log.info("Filling CBR form...")

        # Pricing Type (mat-select)
        if data.get("pricing_type"):
            self._open_mat_select_and_choose("Pricing Type", data["pricing_type"])
            self.wait_seconds(0.3)

        # From Date (datepicker input)
        if data.get("from_date"):
            self._set_datepicker_by_label("From Date", data["from_date"])

        # To Date (datepicker input)
        if data.get("to_date"):
            self._set_datepicker_by_label("To Date", data["to_date"])

        # Location (mat-select)
        if data.get("location"):
            self._open_mat_select_and_choose("Location", data["location"])
            self.wait_seconds(0.3)

        # Grid rows
        if data.get("grid_rows"):
            self._fill_grid_rows(data["grid_rows"])
        elif "item_name" in data or data.get("item_rate") is not None or "uom" in data:
            # Single row data — use "key" in data checks because None is falsy
            # but means "select first available option" for dropdowns
            self._fill_single_grid_row(data)

        self._force_close_panels()
        log.info("CBR form filled")

    def _set_datepicker_by_label(self, label_text, date_str):
        """Set a date value in an Angular Material datepicker by label.
        date_str format: DD/MM/YYYY
        """
        log.info(f"Setting date '{date_str}' for label '{label_text}'")
        try:
            el = self._find_input_by_label(label_text)

            # Clear via JS (Angular inputs resist normal clear)
            self.driver.execute_script(
                "var s = Object.getOwnPropertyDescriptor("
                "  window.HTMLInputElement.prototype,'value').set;"
                "s.call(arguments[0], '');"
                "arguments[0].dispatchEvent(new Event('input',{bubbles:true}));"
                "arguments[0].dispatchEvent(new Event('change',{bubbles:true}));",
                el,
            )
            self.wait_seconds(0.2)

            # Remove readonly if present
            self.driver.execute_script(
                "arguments[0].removeAttribute('readonly');", el
            )

            # Type the date
            el.send_keys(date_str)
            self.wait_seconds(0.3)

            # Tab to confirm
            el.send_keys(Keys.TAB)
            self.wait_seconds(0.3)
            log.info(f"Date '{date_str}' set for '{label_text}'")
        except Exception as e:
            log.warning(f"Could not set date '{date_str}' for '{label_text}': {e}")
            # Fallback: try using the old locator approach
            try:
                if label_text == "From Date":
                    self._set_datepicker(self.FROM_DATE_INPUT, date_str)
                elif label_text == "To Date":
                    self._set_datepicker(self.TO_DATE_INPUT, date_str)
            except Exception:
                log.error(f"All datepicker methods failed for '{label_text}'")

    def _set_datepicker(self, locator, date_str):
        """Set a date value in an Angular Material datepicker using a locator.
        Kept as fallback for backward compatibility.
        """
        log.info(f"Setting date (fallback): {date_str}")
        try:
            el = self.find_visible_element(locator, timeout=5)
            # Clear via JS
            self.driver.execute_script(
                "var s = Object.getOwnPropertyDescriptor("
                "  window.HTMLInputElement.prototype,'value').set;"
                "s.call(arguments[0], '');"
                "arguments[0].dispatchEvent(new Event('input',{bubbles:true}));"
                "arguments[0].dispatchEvent(new Event('change',{bubbles:true}));",
                el,
            )
            self.wait_seconds(0.2)
            # Remove readonly
            self.driver.execute_script(
                "arguments[0].removeAttribute('readonly');", el
            )
            el.send_keys(date_str)
            self.wait_seconds(0.3)
            el.send_keys(Keys.TAB)
            self.wait_seconds(0.3)
        except Exception:
            # Fallback: JS value set
            try:
                if isinstance(locator, tuple) and locator[0] == "xpath":
                    el = self.driver.find_element(By.XPATH, locator[1])
                elif isinstance(locator, tuple) and locator[0] == "css":
                    el = self.driver.find_element(By.CSS_SELECTOR, locator[1])
                else:
                    el = self.driver.find_element(By.CSS_SELECTOR, locator[1] if isinstance(locator, tuple) else locator)
                self.driver.execute_script(
                    "arguments[0].removeAttribute('readonly');"
                    "var s = Object.getOwnPropertyDescriptor("
                    "  window.HTMLInputElement.prototype,'value').set;"
                    "s.call(arguments[0], arguments[1]);"
                    "arguments[0].dispatchEvent(new Event('input',{bubbles:true}));"
                    "arguments[0].dispatchEvent(new Event('change',{bubbles:true}));",
                    el, date_str,
                )
                self.wait_seconds(0.3)
            except Exception:
                log.warning(f"Could not set date: {date_str}")

    def _fill_single_grid_row(self, data):
        """Fill a single grid row with item name, rate, UOM.
        Uses label-based approach for dropdowns.

        IMPORTANT: Use None or "" for item_name/uom to select the FIRST
        available option from the dropdown. The key must be PRESENT in the
        data dict — omitting the key skips the field entirely.

        Guard conditions use `"key" in data` instead of `data.get("key")`
        because None (meaning "select first available") is falsy in Python.
        """
        # Item Name — None/"" means "select first available option"
        if "item_name" in data:
            log.info(f"Filling Item Name: {repr(data['item_name'])} (None/''=first available)")
            self._open_mat_select_and_choose("Item Name", data["item_name"])
            self.wait_seconds(0.5)  # Extra wait: Angular may update UOM options based on Item Name

        # Item Rate
        if data.get("item_rate") is not None:
            try:
                rate_el = self._find_input_by_label("Item Rate")
                # Clear via JS
                self.driver.execute_script(
                    "var s = Object.getOwnPropertyDescriptor("
                    "  window.HTMLInputElement.prototype,'value').set;"
                    "s.call(arguments[0], '');"
                    "arguments[0].dispatchEvent(new Event('input',{bubbles:true}));"
                    "arguments[0].dispatchEvent(new Event('change',{bubbles:true}));",
                    rate_el,
                )
                self.wait_seconds(0.1)
                rate_el.send_keys(str(data["item_rate"]))
                self.wait_seconds(0.3)
                log.info(f"Item Rate set to: {data['item_rate']}")
            except Exception:
                log.warning("Could not fill Item Rate via label, trying locator fallback")
                try:
                    self.type_text(
                        self.ITEM_RATE_INPUT, str(data["item_rate"]), clear_first=True
                    )
                except Exception:
                    log.error("Item Rate input not found by any method")

        # UOM — None/"" means "select first available option"
        if "uom" in data:
            log.info(f"Filling UOM: {repr(data['uom'])} (None/''=first available)")
            self._open_mat_select_and_choose("UOM", data["uom"])
            self.wait_seconds(0.5)  # Extra wait for Angular to process selection

    def _fill_grid_rows(self, grid_rows):
        """Fill multiple grid rows."""
        for idx, row_data in enumerate(grid_rows):
            if idx > 0:
                # Click "Add Row" for subsequent rows
                # The add-row button is a mat-icon-button with mat-icon "add"
                # inside the grid table's Action column
                add_clicked = False

                # Strategy 1: Find by CSS class or mattooltip
                try:
                    add_btn = self.driver.find_element(
                        By.CSS_SELECTOR,
                        "button.add-row, button[mattooltip='Add Row']"
                    )
                    self.driver.execute_script("arguments[0].click();", add_btn)
                    add_clicked = True
                except Exception:
                    pass

                # Strategy 2: Find the add icon button in the grid table
                if not add_clicked:
                    try:
                        # The grid uses mat-icon-button with "add" mat-icon
                        grid_table = self.driver.find_element(
                            By.CSS_SELECTOR, ".grid-table, table.mat-elevation-z2"
                        )
                        add_btns = grid_table.find_elements(
                            By.CSS_SELECTOR, "button.mat-mdc-icon-button"
                        )
                        for btn in add_btns:
                            try:
                                icon = btn.find_element(By.CSS_SELECTOR, "mat-icon")
                                if icon.text.strip().lower() == "add" and btn.is_displayed():
                                    self.driver.execute_script("arguments[0].click();", btn)
                                    add_clicked = True
                                    break
                            except Exception:
                                continue
                    except Exception:
                        pass

                # Strategy 3: Find the last row's add button
                if not add_clicked:
                    try:
                        rows = self.driver.find_elements(
                            By.CSS_SELECTOR, ".grid-table tbody tr, table.mat-elevation-z2 tbody tr"
                        )
                        if rows:
                            last_row = rows[-1]
                            add_btns = last_row.find_elements(
                                By.CSS_SELECTOR, "button.mat-mdc-icon-button"
                            )
                            for btn in add_btns:
                                try:
                                    icon = btn.find_element(By.CSS_SELECTOR, "mat-icon")
                                    if icon.text.strip().lower() == "add":
                                        self.driver.execute_script("arguments[0].click();", btn)
                                        add_clicked = True
                                        break
                                except Exception:
                                    continue
                    except Exception:
                        pass

                if not add_clicked:
                    log.warning("Add Row button not found for multi-row grid")
                self.wait_seconds(0.5)

            self._fill_single_grid_row(row_data)

    # ==============================================================
    #  Form submission & cancellation
    # ==============================================================

    def submit(self):
        """Click the Submit button on the Create form."""
        log.info("Submitting CBR form...")
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
                    "//div[@class='popup-footer']//button[contains(.,'Submit')]"
                )
                self.driver.execute_script("arguments[0].click();", btn)
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
                    "//div[@class='popup-footer']//button[contains(.,'Update')]"
                )
                self.driver.execute_script("arguments[0].click();", btn)
            except Exception:
                self.click_with_retry(self.UPDATE_BUTTON)
        self.wait_seconds(2)
        log.info("Update clicked")

    def cancel(self):
        """Click the Cancel button."""
        log.info("Clicking Cancel button...")
        try:
            btn = self.find_visible_element(self.CANCEL_BUTTON, timeout=5)
            self.driver.execute_script("arguments[0].click();", btn)
        except Exception:
            try:
                btn = self.driver.find_element(
                    By.XPATH,
                    "//div[@class='popup-footer']//button[contains(.,'Cancel')]"
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
        """Wait for SweetAlert2 success popup, read message, click OK."""
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
                self.driver.execute_script(
                    "document.querySelectorAll('.swal2-confirm')"
                    ".forEach(function(b){b.click();});"
                )

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
        """Handle SweetAlert2 validation warning popup."""
        log.info("Checking for validation warning...")
        try:
            wait = WebDriverWait(self.driver, timeout)
            title_el = wait.until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, "#swal2-title")
                )
            )
            msg = title_el.text.strip()

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

    # ==============================================================
    #  Field-level error checking
    # ==============================================================

    def get_mat_error_text(self):
        """Get all visible mat-error texts from the form."""
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

    # ==============================================================
    #  Verification helpers
    # ==============================================================

    def is_add_form_open(self):
        """Check if the Add form popup is currently visible."""
        # Check for any mat-select or input inside the popup
        try:
            selects = self.driver.find_elements(
                By.CSS_SELECTOR,
                "div.edit_pop_up mat-select, div.big-model mat-select, "
                "mat-dialog-container mat-select"
            )
            for sel in selects:
                try:
                    if sel.is_displayed():
                        return True
                except Exception:
                    continue
        except Exception:
            pass

        try:
            inputs = self.driver.find_elements(
                By.CSS_SELECTOR,
                "div.edit_pop_up input, div.big-model input, "
                "mat-dialog-container input"
            )
            for inp in inputs:
                try:
                    if inp.is_displayed():
                        return True
                except Exception:
                    continue
        except Exception:
            pass

        return self._is_form_popup_open()

    def is_form_closed(self):
        """Check if the form popup is no longer visible."""
        return not self._is_form_popup_open()

    def is_view_mode(self):
        """Check if the currently open form is in View (read-only) mode."""
        try:
            # Check if any mat-select in the popup has aria-disabled="true"
            selects = self.driver.find_elements(
                By.CSS_SELECTOR,
                "div.edit_pop_up mat-select, div.big-model mat-select, "
                "mat-dialog-container mat-select"
            )
            for sel in selects:
                try:
                    if sel.is_displayed() and sel.get_attribute("aria-disabled") == "true":
                        return True
                except Exception:
                    continue

            # Check if inputs are disabled
            inputs = self.driver.find_elements(
                By.CSS_SELECTOR,
                "div.edit_pop_up input, div.big-model input, "
                "mat-dialog-container input"
            )
            for inp in inputs:
                try:
                    if inp.is_displayed() and inp.get_attribute("disabled") is not None:
                        return True
                except Exception:
                    continue
        except Exception:
            pass
        return False

    def is_edit_mode(self):
        """Check if currently in Edit mode (Update button visible)."""
        return self.is_displayed(self.UPDATE_BUTTON, timeout=5)

    # ==============================================================
    #  Table interactions
    # ==============================================================

    def get_table_row_count(self):
        """Return the number of visible data rows in the table."""
        rows = self.driver.find_elements(
            By.CSS_SELECTOR, "table#excel-table tbody tr"
        )
        return len(rows)

    def get_table_data(self):
        """Get all visible data from the listing table.
        Returns list of dicts with column headers as keys.
        """
        try:
            headers = [
                h.text.strip()
                for h in self.driver.find_elements(
                    By.CSS_SELECTOR, "table#excel-table thead th"
                )
            ]
            rows = self.driver.find_elements(
                By.CSS_SELECTOR, "table#excel-table tbody tr"
            )
            data = []
            for row in rows:
                try:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    row_data = {}
                    for idx, cell in enumerate(cells):
                        if idx < len(headers):
                            row_data[headers[idx]] = cell.text.strip()
                    data.append(row_data)
                except StaleElementReferenceException:
                    continue
            return data
        except Exception:
            return []

    def get_cell_value(self, row_idx, col_idx):
        """Get the text value of a specific cell."""
        try:
            rows = self.driver.find_elements(
                By.CSS_SELECTOR, "table#excel-table tbody tr"
            )
            if row_idx < len(rows):
                cells = rows[row_idx].find_elements(By.TAG_NAME, "td")
                if col_idx < len(cells):
                    return cells[col_idx].text.strip()
        except Exception:
            pass
        return ""

    def has_iso_dates_in_listing(self):
        """Check if any dates in the listing are in raw ISO format (BUG-003)."""
        data = self.get_table_data()
        for row in data:
            for key in ["From Date", "To Date"]:
                val = row.get(key, "")
                if "T" in val and ":" in val and len(val) > 15:
                    return True
        return False

    def is_record_in_table(self, pricing_type=None, location=None):
        """Check if a matching record exists in the listing table."""
        data = self.get_table_data()
        for row in data:
            match = True
            if pricing_type and row.get("Pricing Type", "").strip() != pricing_type:
                match = False
            if location and row.get("Location", "").strip() != location:
                match = False
            if match:
                return True
        return False

    # ==============================================================
    #  Row actions (View, Edit, Version, History)
    # ==============================================================

    def click_row_action(self, row_idx, action):
        """Click an action button for a specific row.
        action: 'view', 'edit', 'version', 'history'
        """
        self._force_close_panels()
        log.info(f"Clicking {action} on row {row_idx}")
        try:
            rows = self.driver.find_elements(
                By.CSS_SELECTOR, "table#excel-table tbody tr"
            )
            if row_idx < len(rows):
                row = rows[row_idx]
                # Find the action button by column class
                btn = row.find_element(
                    By.CSS_SELECTOR,
                    f"td.cdk-column-{action} button, "
                    f"td.mat-column-{action} button"
                )
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});"
                    "arguments[0].click();",
                    btn,
                )
                self.wait_seconds(1)
                log.info(f"{action.capitalize()} clicked on row {row_idx}")
                return
        except Exception:
            pass

        # Fallback: try mattooltip-based button
        try:
            rows = self.driver.find_elements(
                By.CSS_SELECTOR, "table#excel-table tbody tr"
            )
            if row_idx < len(rows):
                row = rows[row_idx]
                btn = row.find_element(
                    By.CSS_SELECTOR,
                    f"button[mattooltip='{action.capitalize()}']"
                )
                self.driver.execute_script("arguments[0].click();", btn)
                self.wait_seconds(1)
                return
        except Exception:
            pass

        # Fallback: click action icon by tooltip text in the row
        try:
            rows = self.driver.find_elements(
                By.CSS_SELECTOR, "table#excel-table tbody tr"
            )
            if row_idx < len(rows):
                row = rows[row_idx]
                icons = row.find_elements(By.CSS_SELECTOR, "button mat-icon")
                for icon in icons:
                    try:
                        tooltip = icon.find_element(By.XPATH, "..").get_attribute("mattooltip") or ""
                        if action.lower() in tooltip.lower():
                            self.driver.execute_script("arguments[0].click();", icon.find_element(By.XPATH, ".."))
                            self.wait_seconds(1)
                            return
                    except Exception:
                        continue
        except Exception:
            pass

        log.warning(f"Could not click {action} on row {row_idx}")

    def is_edit_enabled(self, row_idx=0):
        """Check if Edit button is enabled for a row."""
        try:
            rows = self.driver.find_elements(
                By.CSS_SELECTOR, "table#excel-table tbody tr"
            )
            if row_idx < len(rows):
                row = rows[row_idx]
                btn = row.find_element(
                    By.CSS_SELECTOR,
                    "td.cdk-column-edit button, td.mat-column-edit button"
                )
                return btn.is_enabled() and "disabled" not in (btn.get_attribute("class") or "")
        except Exception:
            return False

    # ==============================================================
    #  Search
    # ==============================================================

    def search_record(self, search_text):
        """Search for a record using the search bar."""
        log.info(f"Searching for: {search_text}")
        try:
            self.click_with_retry(self.SEARCH_TOGGLE)
            self.wait_seconds(1)
        except Exception:
            pass

        try:
            search_input = self.find_visible_element(self.SEARCH_INPUT, timeout=5)
            search_input.clear()
            search_input.send_keys(search_text)
            self.wait_seconds(0.5)
            self.click_with_retry(self.SEARCH_SUBMIT)
            self.wait_seconds(2)
            return True
        except Exception:
            log.warning("Search input not found")
            return False

    def clear_search(self):
        """Clear search and refresh listing."""
        try:
            search_input = self.driver.find_element(
                By.CSS_SELECTOR,
                "input#erpSearchInput, .erp-search-wrapper input"
            )
            search_input.clear()
            search_input.send_keys(Keys.BACKSPACE)
        except Exception:
            pass
        self.click_refresh()

    # ==============================================================
    #  Column sorting
    # ==============================================================

    def sort_by_column(self, column_header_text):
        """Click a column header to sort."""
        log.info(f"Sorting by column: {column_header_text}")
        try:
            headers = self.driver.find_elements(
                By.CSS_SELECTOR,
                "table#excel-table thead th"
            )
            for header in headers:
                try:
                    if column_header_text.lower() in header.text.strip().lower():
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({block:'center'});"
                            "arguments[0].click();",
                            header,
                        )
                        self.wait_seconds(1)
                        log.info(f"Sorted by: {column_header_text}")
                        return
                except Exception:
                    continue
        except Exception:
            pass
        log.warning(f"Column header '{column_header_text}' not found")

    # ==============================================================
    #  Complete workflow: create record
    # ==============================================================

    def create_cbr_record(self, data):
        """Complete workflow: Click Add -> Fill form -> Submit -> Return success status.
        Returns True if success popup appeared, False otherwise.
        """
        self.open_add_form()
        self.wait_seconds(1)
        self.fill_form(data)
        self.wait_seconds(0.5)
        self.submit()
        self.wait_seconds(2)

        # Check for success alert
        success_msg = self.handle_success_alert(timeout=5)
        if success_msg:
            log.info(f"Record created successfully: {success_msg}")
            return True

        # Check if popup just closed (no alert)
        if self.is_form_closed():
            log.info("Form closed after submit (no success alert)")
            return True

        # Check for validation alert
        validation_msg = self.handle_validation_warning(timeout=3)
        if validation_msg:
            log.warning(f"Validation alert: {validation_msg}")
            return False

        return False
