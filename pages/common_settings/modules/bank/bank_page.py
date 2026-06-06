"""
bank_page.py
------------
Page Object Model for RhythmERP Bank screen.

Location: Common Settings > Bank
URL:      /#/dynamic-screens/Bank

FORM LAYOUT (simple popup — NOT a stepper form):

  Single-page popup with heading "Bank":

    Text Inputs (10):
    - Bank Name              (text input,   required, maxlength=255)
    - Bank Code              (text input,   required, maxlength=255)
    - Branch Name            (text input,   required, maxlength=255)
    - Branch Code            (text input,   required, maxlength=255)
    - Account Number         (text input,   required, maxlength=255)
    - Swift Number           (text input,   optional, maxlength=255)
    - IBAN Number            (text input,   optional, maxlength=255)
    - IFSC Code              (text input,   required, maxlength=255)
    - Cash Credit Limit      (text input,   required, maxlength=255)
    - Bank Address           (text input,   required, maxlength=255)

    Dropdowns (2):
    - Account Type           (mat-select,   required, searchable)
                              Options: "Current", "Saving"
    - GL Account             (mat-select,   required, searchable, 116+ options)

    Toggles (2):
    - Is Default Bank?       (app-slide-toggle-v2, default No)
    - Status                 (app-slide-toggle-v2, default Active)

TABLE COLUMNS (main listing):
  - View / Edit / History   (action buttons per row)
  - Bank Name
  - Account Number
  - IFSC Code
  - Status

KEY RULES (verified from live application 2026-05-19):
  - Simple popup (NO stepper, NO Next/Back buttons)
  - NO formcontrolname attributes — only name attributes (exact case, e.g. name="Bank Name")
  - Bank Name: ALL UPPERCASE letters only, appears to require >= 10 chars
  - IFSC Code: Exactly 11 chars
  - BUG-004 (CRITICAL): Browser-clicked mat-select options do NOT reliably
    update Angular reactive form model. Must use JS value-setter + dispatchEvent
    for ALL dropdown selections.
  - SweetAlert2 for success/validation popups
  - Character counters visible in View mode only
  - Edit mode button says "Update" not "Submit"
  - View mode: all fields disabled, only "Cancel" button
  - History button opens View popup (BUG-006)
  - No Delete functionality (BUG-005)
  - Global search does not filter Bank table (BUG-003)

Optimised (v3 — UOM gold standard + BUG-004 fix):
- ActionChains click for mat-select dropdowns (FIX BUG-004 — JS clicks don't update Angular model)
- _handle_submit_response(): combined alert handler — single poll for success/validation
- Ultra-fast _dismiss_swal() — no wait for SweetAlert to disappear
- Fast polling (0.1s) throughout instead of 0.2-0.3s
- hard_refresh() for fast page reset between tests
- search_and_verify() combines search + existence check
- JS clicks for Add/Submit/Update/Cancel bypass overlay issues
- Reduced is_bank_in_table() timeout from 8s to 3s
- JS-based get_field_validation_state() and get_input_value() for speed
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


class BankPage(BasePage):
    PAGE_URL = f"{RHYTHMERP_BASE_URL}/#/dynamic-screens/Bank"

    # ==============================================================
    #  LOCATORS — Toolbar
    # ==============================================================
    ADD_BUTTON = (
        "css",
        "button.erp-add-btn",
    )
    SEARCH_TOGGLE = ("css", "button.search-btn, button[aria-label='Search']")
    REFRESH_BUTTON = ("css", "button[mattooltip='Refresh']")
    MORE_BUTTON = ("css", "button[mattooltip='More']")

    # ==============================================================
    #  LOCATORS — Search bar
    # ==============================================================
    SEARCH_INPUT = ("css", ".erp-search-wrapper input, input#erpSearchInput")
    SEARCH_SUBMIT = ("css", "button.search-btn")

    # ==============================================================
    #  LOCATORS — Table (main listing)
    # ==============================================================
    TABLE = ("css", "table#excel-table")
    TABLE_ROWS = ("css", "table#excel-table tbody tr")
    TABLE_BANK_NAME_CELLS = (
        "css",
        "table#excel-table tbody td.cdk-column-bank_name, table#excel-table tbody td:nth-child(2)",
    )
    TABLE_ACCOUNT_CELLS = (
        "css",
        "table#excel-table tbody td.cdk-column-account_number, table#excel-table tbody td:nth-child(3)",
    )
    TABLE_IFSC_CELLS = (
        "css",
        "table#excel-table tbody td.cdk-column-ifsc_code, table#excel-table tbody td:nth-child(4)",
    )
    TABLE_STATUS_CELLS = (
        "css",
        "table#excel-table tbody td.cdk-column-status, table#excel-table tbody td:nth-child(5)",
    )
    NO_DATA_ROW = (
        "css",
        "table#excel-table tbody tr td.no-data, "
        "table#excel-table tbody tr.mat-mdc-no-data-row",
    )

    # ==============================================================
    #  LOCATORS — Form popup
    # ==============================================================
    FORM_POPUP = (
        "css",
        ".edit_pop_up.override_edit_pop_up.popup-mode",
    )
    FORM_HEADING = (
        "css",
        ".edit_pop_up h3, .edit_pop_up.override_edit_pop_up.popup-mode h3",
    )

    # ==============================================================
    #  LOCATORS — Text inputs (by name attribute)
    # ==============================================================
    BANK_NAME_INPUT = ("css", "input[name='Bank Name']")
    BANK_CODE_INPUT = ("css", "input[name='Bank Code']")
    BRANCH_NAME_INPUT = ("css", "input[name='Branch Name']")
    BRANCH_CODE_INPUT = ("css", "input[name='Branch Code']")
    ACCOUNT_NUMBER_INPUT = ("css", "input[name='Account Number']")
    SWIFT_NUMBER_INPUT = ("css", "input[name='Swift Number']")
    IBAN_NUMBER_INPUT = ("css", "input[name='IBAN Number']")
    IFSC_CODE_INPUT = ("css", "input[name='IFSC Code']")
    CASH_CREDIT_LIMIT_INPUT = ("css", "input[name='Cash Credit Limit']")
    BANK_ADDRESS_INPUT = ("css", "input[name='Bank Address']")

    # ==============================================================
    #  LOCATORS — Dropdowns (mat-select, by mat-label XPath)
    # ==============================================================
    ACCOUNT_TYPE_SELECT = (
        "xpath",
        "//mat-label[contains(.,'Account Type')]"
        "/ancestor::mat-form-field//mat-select",
    )
    GL_ACCOUNT_SELECT = (
        "xpath",
        "//mat-label[contains(.,'GL Account')]"
        "/ancestor::mat-form-field//mat-select",
    )

    # ==============================================================
    #  LOCATORS — Toggles (app-slide-toggle-v2)
    # ==============================================================
    IS_DEFAULT_BANK_TOGGLE = (
        "xpath",
        "//app-slide-toggle-v2[.//span[contains(@class,'main-label') "
        "and contains(.,'Is Default Bank?')]]"
        "//div[contains(@class,'switch-wrapper')]",
    )
    STATUS_TOGGLE = (
        "xpath",
        "//app-slide-toggle-v2[.//span[contains(@class,'main-label') "
        "and contains(.,'Status')]]"
        "//div[contains(@class,'switch-wrapper')]",
    )

    # ==============================================================
    #  LOCATORS — Footer buttons
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
    #  LOCATORS — Row action buttons (now via 3-dot menu, see _click_action_button)
    # ==============================================================

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
    #  LOCATORS — Pagination
    # ==============================================================
    PAGINATION_NEXT = ("css", "button[aria-label='Next page'], button.mat-mdc-paginator-navigation-next")
    PAGINATION_PREV = ("css", "button[aria-label='Previous page'], button.mat-mdc-paginator-navigation-previous")
    ITEMS_PER_PAGE_SELECT = ("css", "mat-paginator-page-size select, .mat-mdc-paginator-page-size select")

    # ==============================================================
    #  LOCATORS — More menu
    # ==============================================================
    EXPORT_EXCEL_OPTION = (
        "xpath",
        "//button[contains(.,'Export to Excel') or contains(.,'Download as')]",
    )

    # ==============================================================
    #  Navigation & page load
    # ==============================================================

    def navigate_to_page(self):
        """Navigate to the Bank listing page via direct URL (fast and reliable).
        No double-load — just driver.get + wait for page ready.
        """
        log.info("Navigating to Bank page...")
        self.driver.get(self.PAGE_URL)
        self._wait_for_page_ready()
        log.info("Arrived at Bank page")

    def hard_refresh(self):
        """Hard refresh the current page and wait for it to be ready.
        Much faster than full navigate_to_page() for resetting between tests."""
        log.info("Hard refreshing page")
        self.driver.refresh()
        self._wait_for_page_ready()
        log.info("Page refreshed and ready")

    def _wait_for_page_ready(self):
        """Wait for the Bank page table to appear.
        Pure WebDriverWait — no sleep fallbacks."""
        try:
            WebDriverWait(self.driver, 15).until(
                lambda d: d.find_elements("css selector", "table#excel-table")
            )
            log.info("Page ready (table found)")
        except Exception:
            # Fallback: check for search button
            try:
                WebDriverWait(self.driver, 5).until(
                    lambda d: d.find_elements("css selector", "button.search-btn")
                )
                log.info("Page ready (search button found, no table)")
            except Exception:
                log.warning("Page ready check timed out")

    def is_page_loaded(self):
        """Check if the Bank listing page has loaded."""
        return self.is_displayed(self.TABLE, timeout=10)

    # ==============================================================
    #  Overlay cleanup — NEVER use Keys.ESCAPE
    # ==============================================================

    def _force_close_panels(self):
        """Remove ALL select overlay panes from the DOM via JS.
        Keeps dialog backdrop intact so form popups stay open.
        No wait_seconds — pure JS cleanup.
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
        """Click the ADD (+) button to open the create form.
        Bank opens a simple single-page popup (not stepper).
        Uses JS click — bypasses overlay/z-index issues.
        """
        log.info("Opening Add Bank form")
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
                EC.presence_of_element_located(("css selector", "input[name='Bank Name']"))
            )
            log.info("Add form opened")
        except Exception:
            log.warning("Add form may not have opened — Bank Name input not found")

    def _is_form_popup_open(self):
        """Quick check if the Bank form popup is visible using fast JS offsetParent check."""
        try:
            return self.driver.execute_script("""
                var popup = document.querySelector('.edit_pop_up.override_edit_pop_up.popup-mode');
                return popup && popup.offsetParent !== null;
            """)
        except Exception:
            pass
        # Fallback: check for any visible popup container
        try:
            popups = self.driver.find_elements(
                By.CSS_SELECTOR,
                ".edit_pop_up.override_edit_pop_up.popup-mode, "
                "mat-dialog-container, "
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
        """Check if the Add Bank form popup is open (fast JS check)."""
        return self.driver.execute_script("""
            var el = document.querySelector("input[name='Bank Name']");
            return el && el.offsetParent !== null;
        """)

    def is_form_popup_open(self):
        """Check if any form popup is visible (fast JS check)."""
        return self.driver.execute_script("""
            var popup = document.querySelector('.edit_pop_up.override_edit_pop_up.popup-mode');
            return popup && popup.offsetParent !== null;
        """)

    def click_refresh(self):
        """Click the Refresh button — just use hard_refresh() for speed."""
        log.info("Refreshing via hard_refresh...")
        self.hard_refresh()

    # ==============================================================
    #  Form filling — JS value-setter for Angular compatibility
    # ==============================================================

    def _fill_input_by_name(self, name_attr, value):
        """Fill an input field by its name attribute using JS value-setter.

        Uses the native input value setter + dispatchEvent pattern to
        ensure Angular reactive form model is properly updated.
        This is critical because simple send_keys may not trigger Angular
        change detection (BUG-004 applies to inputs too in some cases).
        """
        js = f"""
            var popup = document.querySelector(
                '.edit_pop_up.override_edit_pop_up.popup-mode'
            );
            if (!popup) return 'No popup';
            var input = popup.querySelector('input[name="{name_attr}"]');
            if (input) {{
                var nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                    window.HTMLInputElement.prototype, 'value'
                ).set;
                nativeInputValueSetter.call(input, arguments[0]);
                input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                return 'OK';
            }}
            return 'Not found: {name_attr}';
        """
        result = self.driver.execute_script(js, str(value))
        if "OK" not in str(result):
            log.warning(f"Input not filled: {name_attr} — {result}")

    def _fill_input_via_locator(self, locator, value):
        """Fill an input field using a locator tuple (type, value)."""
        try:
            el = self.find_element(locator)
            if el:
                js = """
                    var nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                        window.HTMLInputElement.prototype, 'value'
                    ).set;
                    nativeInputValueSetter.call(arguments[0], arguments[1]);
                    arguments[0].dispatchEvent(new Event('input', {bubbles: true}));
                    arguments[0].dispatchEvent(new Event('change', {bubbles: true}));
                """
                self.driver.execute_script(js, el, str(value))
                return True
        except Exception as e:
            log.warning(f"Failed to fill input via locator: {e}")
        return False

    def _clear_input_by_name(self, name_attr):
        """Clear an input field by its name attribute using JS value-setter."""
        self._fill_input_by_name(name_attr, "")

    # ==============================================================
    #  Dropdown selection — JS approach (BUG-004)
    # ==============================================================

    def _open_dropdown_by_label(self, label_text):
        """Open a mat-select dropdown by finding its form-field label.
        Uses Selenium ActionChains click — JS click does NOT reliably open
        Angular Material mat-select dropdowns (BUG-004).

        Step 1: Find the mat-select element via Selenium XPath.
        Step 2: Click using ActionChains (properly triggers Angular's event handlers).
        Step 3: Wait for dropdown panel to appear via WebDriverWait.
        """
        try:
            # Step 1: Find mat-select via Selenium
            select_el = self.driver.find_element(
                By.XPATH,
                f"//mat-label[contains(.,'{label_text}')]/"
                f"ancestor::mat-form-field//mat-select"
            )
            # Step 2: ActionChains click — triggers Angular change detection
            ActionChains(self.driver).move_to_element(select_el).click().perform()
        except Exception as e:
            # Fallback: JS dispatch mouse events
            log.warning(f"ActionChains click failed for '{label_text}': {e}")
            self.driver.execute_script("""
                var popup = document.querySelector(
                    '.edit_pop_up.override_edit_pop_up.popup-mode'
                );
                if (!popup) return;
                var formFields = popup.querySelectorAll('mat-form-field');
                for (var i = 0; i < formFields.length; i++) {
                    var label = formFields[i].querySelector('mat-label');
                    if (label && label.textContent.trim() === arguments[0]) {
                        var select = formFields[i].querySelector('mat-select');
                        if (select) {
                            select.dispatchEvent(new MouseEvent('mousedown', {bubbles: true}));
                            select.dispatchEvent(new MouseEvent('mouseup', {bubbles: true}));
                            select.dispatchEvent(new MouseEvent('click', {bubbles: true}));
                        }
                    }
                }
            """, label_text)

        # Step 3: Wait for dropdown options to appear
        try:
            WebDriverWait(self.driver, 3).until(
                EC.presence_of_element_located((
                    "css selector",
                    ".cdk-overlay-pane mat-option, .cdk-overlay-pane [role='option']"
                ))
            )
            return True
        except Exception:
            pass
        log.warning(f"Dropdown panel not appeared for: {label_text}")
        return False

    def _select_option_by_text(self, option_text):
        """Select a mat-option from the currently open dropdown panel.
        Uses Selenium ActionChains click on the option element.
        JS click on mat-option does NOT update Angular's form model (BUG-004),
        but Selenium ActionChains click DOES because it triggers real browser events.
        """
        # Try Selenium click on matching option first (most reliable for Angular)
        try:
            options = self.driver.find_elements(
                By.CSS_SELECTOR,
                ".cdk-overlay-pane mat-option, .cdk-overlay-pane [role='option']"
            )
            for opt in options:
                text = opt.text.strip()
                if text == option_text or option_text in text:
                    ActionChains(self.driver).move_to_element(opt).click().perform()
                    return True
        except Exception:
            pass

        # Fallback: JS click with partial matching
        js = """
            var options = document.querySelectorAll(
                '.cdk-overlay-pane mat-option'
            );
            // Exact match first
            for (var i = 0; i < options.length; i++) {
                if (options[i].textContent.trim() === arguments[0]) {
                    options[i].click();
                    return 'Selected';
                }
            }
            // Partial match (indexOf)
            for (var i = 0; i < options.length; i++) {
                if (options[i].textContent.trim().indexOf(arguments[0]) !== -1) {
                    options[i].click();
                    return 'Selected_partial';
                }
            }
            // Role=option fallback
            var allOpts = document.querySelectorAll(
                '.cdk-overlay-pane [role="option"]'
            );
            for (var i = 0; i < allOpts.length; i++) {
                if (allOpts[i].textContent.trim().indexOf(arguments[0]) !== -1) {
                    allOpts[i].click();
                    return 'Selected_role';
                }
            }
            return 'Not found: ' + arguments[0];
        """
        result = self.driver.execute_script(js, option_text)
        if "Selected" in str(result):
            return True
        log.warning(f"Option not selected: {option_text} — {result}")
        return False

    def _close_dropdown_panel(self):
        """Close any open dropdown overlay panel — just JS cleanup, no sleep."""
        self._force_close_panels()

    def select_account_type(self, value):
        """Select an Account Type dropdown option ('Current' or 'Saving')."""
        log.info(f"Selecting Account Type: {value}")
        self._open_dropdown_by_label("Account Type")
        self._select_option_by_text(value)
        self._close_dropdown_panel()

    def select_gl_account(self, value):
        """Select a GL Account dropdown option."""
        log.info(f"Selecting GL Account: {value}")
        self._open_dropdown_by_label("GL Account")
        self._select_option_by_text(value)
        self._close_dropdown_panel()

    def select_random_account_type(self):
        """Select a random Account Type option from the live UI.
        Returns the selected option text.
        """
        log.info("Selecting random Account Type...")
        self._open_dropdown_by_label("Account Type")

        # Read available options
        options = self._get_dropdown_options()
        if not options:
            self._close_dropdown_panel()
            return None

        # Filter out placeholder text
        valid_opts = [o for o in options if o.strip()]
        if not valid_opts:
            self._close_dropdown_panel()
            return None

        chosen = random.choice(valid_opts)
        self._select_option_by_text(chosen)
        self._close_dropdown_panel()
        log.info(f"Selected Account Type: {chosen}")
        return chosen

    def select_random_gl_account(self):
        """Select a random GL Account option from the live UI.
        Returns the selected option text.
        """
        log.info("Selecting random GL Account...")
        self._open_dropdown_by_label("GL Account")

        # Read available options
        options = self._get_dropdown_options()
        if not options:
            self._close_dropdown_panel()
            return None

        valid_opts = [o for o in options if o.strip()]
        if not valid_opts:
            self._close_dropdown_panel()
            return None

        chosen = random.choice(valid_opts)
        self._select_option_by_text(chosen)
        self._close_dropdown_panel()
        log.info(f"Selected GL Account: {chosen}")
        return chosen

    def _get_dropdown_options(self):
        """Get all option texts from the currently open dropdown panel."""
        js = """
            var options = document.querySelectorAll(
                '.cdk-overlay-pane mat-option'
            );
            var texts = [];
            for (var i = 0; i < options.length; i++) {
                texts.push(options[i].textContent.trim());
            }
            return texts;
        """
        return self.driver.execute_script(js) or []

    def get_account_type_options(self):
        """Get all Account Type dropdown options by opening and reading."""
        self._open_dropdown_by_label("Account Type")
        opts = self._get_dropdown_options()
        self._close_dropdown_panel()
        return opts

    def get_gl_account_options(self):
        """Get all GL Account dropdown options by opening and reading."""
        self._open_dropdown_by_label("GL Account")
        opts = self._get_dropdown_options()
        self._close_dropdown_panel()
        return opts

    # ==============================================================
    #  Toggle handling
    # ==============================================================

    def _set_toggle(self, label_text, value):
        """Set a toggle switch by its label text.

        Args:
            label_text: Part of the label to match (e.g., 'Is Default Bank?')
            value: True to toggle ON, False to toggle OFF
        """
        js = f"""
            var toggles = document.querySelectorAll('app-slide-toggle-v2');
            for (var i = 0; i < toggles.length; i++) {{
                var mainLabel = toggles[i].querySelector('.main-label');
                if (mainLabel && mainLabel.textContent.trim().indexOf('{label_text}') > -1) {{
                    var sw = toggles[i].querySelector(
                        '.switch-wrapper input[type="checkbox"]'
                    );
                    if (sw && sw.checked !== {str(value).lower()}) {{
                        sw.click();
                        return 'Toggled to ' + {str(value).lower()};
                    }}
                    return 'Already ' + {str(value).lower()};
                }}
            }}
            return 'Toggle not found: {label_text}';
        """
        result = self.driver.execute_script(js)
        log.info(f"Toggle '{label_text}': {result}")

    def set_is_default_bank(self, value):
        """Set the 'Is Default Bank?' toggle."""
        self._set_toggle("Is Default Bank?", value)

    def set_status(self, value):
        """Set the 'Status' toggle."""
        self._set_toggle("Status", value)

    def get_toggle_state(self, label_text):
        """Get the current state of a toggle by its label text.
        Returns True if checked (ON), False if unchecked (OFF).
        """
        js = f"""
            var toggles = document.querySelectorAll('app-slide-toggle-v2');
            for (var i = 0; i < toggles.length; i++) {{
                var mainLabel = toggles[i].querySelector('.main-label');
                if (mainLabel && mainLabel.textContent.trim().indexOf('{label_text}') > -1) {{
                    var sw = toggles[i].querySelector(
                        '.switch-wrapper input[type="checkbox"]'
                    );
                    return sw ? sw.checked : null;
                }}
            }}
            return null;
        """
        return self.driver.execute_script(js)

    # ==============================================================
    #  Form fill — complete
    # ==============================================================

    def fill_bank_form(self, data):
        """Fill all fields on the Bank form with provided data dict.

        Args:
            data: Dict with keys matching field names.
                   None values for dropdowns → select random from live UI.
        """
        log.info("Filling Bank form...")

        # Text inputs — fill using JS value-setter
        text_field_map = [
            ("bank_name", "Bank Name"),
            ("bank_code", "Bank Code"),
            ("branch_name", "Branch Name"),
            ("branch_code", "Branch Code"),
            ("account_number", "Account Number"),
            ("swift_number", "Swift Number"),
            ("iban_number", "IBAN Number"),
            ("ifsc_code", "IFSC Code"),
            ("cash_credit_limit", "Cash Credit Limit"),
            ("bank_address", "Bank Address"),
        ]

        for key, name_attr in text_field_map:
            value = data.get(key)
            if value is not None:
                self._fill_input_by_name(name_attr, str(value))

        # Dropdowns — select specified or random
        if data.get("account_type"):
            self.select_account_type(data["account_type"])
        else:
            random_type = self.select_random_account_type()
            if random_type:
                data["account_type"] = random_type

        if data.get("gl_account"):
            self.select_gl_account(data["gl_account"])
        else:
            random_gl = self.select_random_gl_account()
            if random_gl:
                data["gl_account"] = random_gl

        # Toggles
        if "is_default_bank" in data:
            self.set_is_default_bank(data["is_default_bank"])
        if "status" in data:
            self.set_status(data["status"])

    # ==============================================================
    #  Create / Edit / Submit / Cancel
    # ==============================================================

    def create_bank(self, data):
        """Open Add form, fill all fields, and submit.

        Returns dict with:
            status: "PASSED" or "FAILED"
            bank_name: the bank name used
            error: error message if any
        """
        log.info("Creating Bank record...")
        self.open_add_form()
        assert self._is_form_popup_open(), "Add form did not open"
        self.fill_bank_form(data)
        return self._submit_and_handle_result(data)

    def _submit_and_handle_result(self, data):
        """Click Submit/Update and handle the result using fast SweetAlert polling.
        v3: Uses _handle_submit_response() for combined alert detection.

        Returns dict with status, bank_name, error.
        """
        result = {"status": "FAILED", "bank_name": "", "error": ""}

        # Click Submit via JS
        self._force_close_panels()
        self._js_click_popup_button('Submit')

        # Combined response handler — single poll cycle
        response = self._handle_submit_response()
        if response == 'success':
            result["status"] = "PASSED"
            result["bank_name"] = data.get("bank_name", "")
            log.info(f"Bank created successfully: {result['bank_name']}")
        elif response == 'validation':
            result["error"] = "Validation Failed"
            result["bank_name"] = data.get("bank_name", "")
        else:
            # No alert appeared — check if popup closed (success without alert)
            if not self._is_form_popup_open():
                result["status"] = "PASSED"
                result["bank_name"] = data.get("bank_name", "")
                log.info(f"Bank created (no alert): {result['bank_name']}")
            else:
                result["error"] = "Submit clicked but no SweetAlert appeared"
                log.warning(result["error"])

        return result

    def _handle_submit_response(self):
        """Handle the response after submit/update — combines success and validation
        alert detection into ONE wait cycle instead of two.

        OLD WAY (4-5s per create):
          is_validation_alert_present(timeout=2) -> handle_success_alert(timeout=2)

        NEW WAY (1-2s per create):
          Single poll for ANY SweetAlert -> read title -> click appropriate button

        Returns: 'success', 'validation', or 'none'
        """
        log.info("Waiting for submit response")
        end = time.monotonic() + 3
        while time.monotonic() < end:
            info = self.driver.execute_script("""
                var popup = document.querySelector('.swal2-popup');
                if (!popup || popup.offsetParent === null) return JSON.stringify({found: false});
                var title = document.querySelector('#swal2-title');
                var titleText = title ? title.textContent.trim() : '';
                var icon = document.querySelector('.swal2-popup .swal2-icon');
                var iconType = '';
                if (icon) {
                    if (icon.classList.contains('swal2-icon-success')) iconType = 'success';
                    else if (icon.classList.contains('swal2-icon-warning')) iconType = 'warning';
                    else if (icon.classList.contains('swal2-icon-error')) iconType = 'error';
                }
                return JSON.stringify({
                    found: true,
                    title: titleText,
                    icon: iconType
                });
            """)
            try:
                import json
                d = json.loads(info)
                if d.get('found'):
                    title = d.get('title', '')
                    icon = d.get('icon', '')
                    if icon == 'success' or 'success' in title.lower():
                        self.driver.execute_script("""
                            var btn = document.querySelector('.swal2-confirm');
                            if (btn) btn.click();
                        """)
                        log.info("Submit response: SUCCESS — " + title)
                        return 'success'
                    else:
                        self.driver.execute_script("""
                            var cancel = document.querySelector('.swal2-cancel');
                            if (cancel) { cancel.click(); return; }
                            var confirm = document.querySelector('.swal2-confirm');
                            if (confirm) confirm.click();
                        """)
                        log.info("Submit response: VALIDATION — " + title)
                        return 'validation'
            except Exception:
                pass
            # Also check if popup closed (success without SweetAlert)
            if not self._is_form_popup_open():
                log.info("Submit response: popup closed (success)")
                return 'success'
            time.sleep(0.1)
        log.info("No SweetAlert appeared after submit")
        return 'none'

    def submit(self):
        """Click the Submit button on the form via JS click."""
        log.info("Clicking Submit")
        self._force_close_panels()
        self._js_click_popup_button('Submit')

    def update(self):
        """Click the Update button on the edit form via JS click."""
        log.info("Clicking Update")
        self._force_close_panels()
        self._js_click_popup_button('Update')

    def _js_click_popup_button(self, button_text):
        """Click a popup footer button (Submit/Update) via JS — bypasses overlay issues."""
        js = """
        var footers = document.querySelectorAll('.popup-footer');
        for (var i = 0; i < footers.length; i++) {
            var buttons = footers[i].querySelectorAll('button');
            for (var j = 0; j < buttons.length; j++) {
                if (buttons[j].textContent.trim().indexOf(arguments[0]) !== -1) {
                    buttons[j].click();
                    return 'clicked_' + arguments[0];
                }
            }
        }
        throw new Error('Button "' + arguments[0] + '" not found');
        """
        try:
            result = self.driver.execute_script(js, button_text)
            log.info("JS click " + button_text + ": " + str(result))
        except Exception as e:
            log.warning("JS click failed for " + button_text + ", falling back to Selenium: " + str(e))
            if button_text == 'Submit':
                self.click_with_retry(self.SUBMIT_BUTTON)
            elif button_text == 'Update':
                self.click_with_retry(self.UPDATE_BUTTON)

    def cancel(self):
        """Click the Cancel button on the form popup via JS."""
        log.info("Clicking Cancel")
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

    def close_popup(self):
        """Close the form popup via Cancel button or JS removal."""
        try:
            self.cancel()
        except Exception:
            pass
        try:
            self.force_close_form_popup()
        except Exception:
            pass

    def force_close_form_popup(self):
        """Force close the form popup by clicking the X button via JS."""
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
    #  SweetAlert2 handling
    # ==============================================================

    def get_swal_title(self):
        """Get the SweetAlert2 title text."""
        try:
            el = self.driver.find_element(By.CSS_SELECTOR, "#swal2-title")
            if el.is_displayed():
                return el.text.strip()
        except Exception:
            pass
        return ""

    def get_swal_content(self):
        """Get the SweetAlert2 content text."""
        try:
            el = self.driver.find_element(
                By.CSS_SELECTOR, ".swal2-html-container"
            )
            if el.is_displayed():
                return el.text.strip()
        except Exception:
            pass
        return ""

    def _dismiss_swal(self):
        """Dismiss the SweetAlert2 popup — try Cancel first, then OK.
        Ultra-fast — no wait for SweetAlert to disappear (saves 2-3s per call)."""
        self.driver.execute_script("""
            var cancel = document.querySelector('.swal2-cancel');
            if (cancel) { cancel.click(); return 'Cancel'; }
            var confirm = document.querySelector('.swal2-confirm');
            if (confirm) { confirm.click(); return 'OK'; }
            return 'none';
        """)

    def is_swal_visible(self):
        """Check if a SweetAlert2 popup is visible."""
        try:
            container = self.driver.find_element(
                By.CSS_SELECTOR, ".swal2-container"
            )
            return container.is_displayed()
        except Exception:
            return False

    def handle_validation_warning(self, timeout=2):
        """Handle the 'Validation Failed' SweetAlert2 popup.
        Fast poll for validation alert, then dismiss.

        Returns the SweetAlert title if visible, or empty string.
        Automatically dismisses the alert.
        """
        log.info("Handling validation warning")
        end_time = time.monotonic() + timeout
        while time.monotonic() < end_time:
            try:
                visible = self.driver.execute_script("""
                    var el = document.querySelector('.swal2-popup.swal2-icon-warning, .swal2-popup.swal2-icon-error');
                    return el && el.offsetParent !== null;
                """)
                if visible:
                    title = self.get_swal_title()
                    self._dismiss_swal()
                    return title
            except Exception:
                pass
            time.sleep(0.1)
        return ""

    def handle_success_alert(self):
        """Handle the success SweetAlert2 popup — ULTRA FAST dismiss.
        Clicks confirm via JS and does NOT wait for SweetAlert to disappear.
        The popup will auto-close — waiting wastes 4-6s per call."""
        log.info("Handling success alert")
        # Click confirm immediately — don't wait for visibility first
        result = self.driver.execute_script("""
            var btn = document.querySelector('.swal2-confirm');
            if (btn) { btn.click(); return 'clicked'; }
            return 'not found';
        """)
        if result == 'clicked':
            log.info("SweetAlert confirm clicked")
            return
        # Brief poll — SweetAlert may take 1s to appear after submit
        end = time.monotonic() + 3
        while time.monotonic() < end:
            result = self.driver.execute_script("""
                var btn = document.querySelector('.swal2-confirm');
                if (btn) { btn.click(); return 'clicked'; }
                return 'not found';
            """)
            if result == 'clicked':
                log.info("SweetAlert confirm clicked (after poll)")
                return
            time.sleep(0.1)
        log.info("No SweetAlert found (may have auto-dismissed)")

    # ==============================================================
    #  Validation alert handlers (like UOM)
    # ==============================================================

    def is_validation_alert_present(self, timeout=2):
        """Check if any SweetAlert validation popup is visible. Fast poll (0.1s)."""
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
            time.sleep(0.1)
        return False

    def dismiss_any_validation_alert(self):
        """Dismiss any SweetAlert validation popup — try Cancel first, then OK.
        Ultra-fast — no wait for SweetAlert to disappear."""
        log.info("Dismissing any validation alert")
        self.driver.execute_script("""
            var cancel = document.querySelector('.swal2-cancel');
            if (cancel) { cancel.click(); return 'Cancel'; }
            var confirm = document.querySelector('.swal2-confirm');
            if (confirm) { confirm.click(); return 'OK'; }
            return 'none';
        """)

    # ==============================================================
    #  Validation error reading
    # ==============================================================

    def get_mat_error_text(self, field_name=None):
        """Get mat-error text from the form popup.
        If field_name is provided, looks up error by input name attribute (JS-based).
        Otherwise, returns all mat-error texts.
        """
        if field_name:
            # JS-based lookup for a specific field
            try:
                js = """
                var input = document.querySelector('input[name="' + arguments[0] + '"]');
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
                return JSON.stringify({found: false, reason: 'mat-error not found in ancestor chain'});
                """
                result = self.driver.execute_script(js, field_name)
                if result:
                    import json
                    data = json.loads(result)
                    if data.get("found"):
                        return data.get("errorText", "")
                    else:
                        log.warning("mat-error not found for field '" + field_name + "': " + data.get("reason", ""))
                return ""
            except Exception as e:
                log.warning(f"get_mat_error_text error for field '{field_name}': {e}")
                return ""

        # Original behavior: return all mat-error texts
        errors = []
        try:
            popup = self.driver.find_element(
                By.CSS_SELECTOR,
                ".edit_pop_up.override_edit_pop_up.popup-mode",
            )
            error_els = popup.find_elements(By.CSS_SELECTOR, "mat-error")
            for el in error_els:
                text = el.text.strip()
                if text and text not in errors:
                    errors.append(text)
        except Exception:
            pass
        return errors

    def get_field_error(self, field_label):
        """Get mat-error text for a specific field by its label."""
        try:
            popup = self.driver.find_element(
                By.CSS_SELECTOR,
                ".edit_pop_up.override_edit_pop_up.popup-mode",
            )
            form_fields = popup.find_elements(
                By.CSS_SELECTOR, "mat-form-field"
            )
            for ff in form_fields:
                label = ff.find_element(By.CSS_SELECTOR, "mat-label")
                if label and field_label in label.text:
                    error_el = ff.find_elements(By.CSS_SELECTOR, "mat-error")
                    if error_el:
                        return error_el[0].text.strip()
        except Exception:
            pass
        return ""

    def get_field_validation_state(self, field_label):
        """Check if a specific field is currently invalid.
        Uses fast JS-based DOM walk-up instead of Selenium find_elements for ~3x speed.

        Returns dict with: invalid (bool), error (str), touched (bool).
        """
        js = """
            var popup = document.querySelector(
                '.edit_pop_up.override_edit_pop_up.popup-mode'
            );
            if (!popup) return JSON.stringify({invalid: false, touched: false, error: ''});
            var formFields = popup.querySelectorAll('mat-form-field');
            for (var i = 0; i < formFields.length; i++) {
                var label = formFields[i].querySelector('mat-label');
                if (label && label.textContent.trim().indexOf(arguments[0]) !== -1) {
                    var classes = formFields[i].className || '';
                    var errorEl = formFields[i].querySelector('mat-error');
                    return JSON.stringify({
                        invalid: classes.indexOf('ng-invalid') !== -1,
                        touched: classes.indexOf('ng-touched') !== -1,
                        error: errorEl ? errorEl.textContent.trim() : ''
                    });
                }
            }
            return JSON.stringify({invalid: false, touched: false, error: ''});
        """
        try:
            import json
            result = self.driver.execute_script(js, field_label)
            return json.loads(result)
        except Exception:
            pass
        return {"invalid": False, "touched": False, "error": ""}

    def get_all_field_states(self):
        """Get validation state for ALL form fields.

        Returns list of dicts: {field, invalid, error, touched}.
        """
        result = []
        try:
            popup = self.driver.find_element(
                By.CSS_SELECTOR,
                ".edit_pop_up.override_edit_pop_up.popup-mode",
            )
            form_fields = popup.find_elements(
                By.CSS_SELECTOR, "mat-form-field"
            )
            for ff in form_fields:
                label = ff.find_element(By.CSS_SELECTOR, "mat-label")
                classes = ff.get_attribute("class") or ""
                error_el = ff.find_elements(By.CSS_SELECTOR, "mat-error")
                result.append({
                    "field": label.text.strip() if label else "?",
                    "invalid": "ng-invalid" in classes,
                    "touched": "ng-touched" in classes,
                    "error": error_el[0].text.strip() if error_el else "",
                })
        except Exception as e:
            log.warning(f"get_all_field_states error: {e}")
        return result

    # ==============================================================
    #  Form field value reading
    # ==============================================================

    def get_form_field_values(self):
        """Read all form field values from the popup.

        Returns dict with field names as keys and current values.
        """
        values = {}
        try:
            popup = self.driver.find_element(
                By.CSS_SELECTOR,
                ".edit_pop_up.override_edit_pop_up.popup-mode",
            )

            # Text inputs — use JS to reliably read Angular Material values
            # (Selenium find_elements can miss Angular-rendered inputs)
            js = """
                var popup = document.querySelector('.edit_pop_up.override_edit_pop_up.popup-mode');
                if (!popup) return {};
                var result = {};
                var inputs = popup.querySelectorAll('input');
                for (var i = 0; i < inputs.length; i++) {
                    var inp = inputs[i];
                    var name = inp.getAttribute('name');
                    if (name && inp.type === 'text') {
                        result[name] = inp.value || '';
                    }
                }
                return result;
            """
            input_values = self.driver.execute_script(js)
            if input_values:
                values.update(input_values)

            # Dropdowns (mat-select trigger text)
            form_fields = popup.find_elements(By.CSS_SELECTOR, "mat-form-field")
            for ff in form_fields:
                label = ff.find_elements(By.CSS_SELECTOR, "mat-label")
                if not label:
                    continue
                select = ff.find_elements(By.CSS_SELECTOR, "mat-select")
                if select:
                    label_text = label[0].text.strip()
                    trigger = select[0].find_elements(
                        By.CSS_SELECTOR, ".mat-select-trigger, .mat-mdc-select-trigger"
                    )
                    if trigger:
                        values[label_text] = trigger[0].text.strip()

            # Toggles
            toggles = popup.find_elements(By.CSS_SELECTOR, "app-slide-toggle-v2")
            for tc in toggles:
                main_label = tc.find_elements(By.CSS_SELECTOR, ".main-label")
                sw = tc.find_elements(By.CSS_SELECTOR, ".switch-wrapper input[type='checkbox']")
                if main_label:
                    values[main_label[0].text.strip()] = (
                        sw[0].is_selected() if sw else None
                    )

        except Exception as e:
            log.warning(f"get_form_field_values error: {e}")
        return values

    def get_input_value(self, name_attr):
        """Get the current value of an input field by name attribute.
        Uses fast JS instead of Selenium find_element for speed."""
        try:
            return self.driver.execute_script("""
                var popup = document.querySelector(
                    '.edit_pop_up.override_edit_pop_up.popup-mode'
                );
                if (!popup) return '';
                var input = popup.querySelector('input[name="' + arguments[0] + '"]');
                return input ? (input.value || '') : '';
            """, name_attr)
        except Exception:
            return ""

    # ==============================================================
    #  Table operations
    # ==============================================================

    def get_table_row_count(self):
        """Get the number of data rows in the table."""
        try:
            rows = self.driver.find_elements(
                By.CSS_SELECTOR, "table#excel-table tbody tr"
            )
            return len(rows)
        except Exception:
            return 0

    def is_bank_in_table(self, bank_name, timeout=3):
        """Check if a bank with the given name exists in the table.
        Fast polling (0.1s) with reduced timeout (3s, was 8s)."""
        end_time = time.monotonic() + timeout
        while time.monotonic() < end_time:
            try:
                rows = self.find_elements(self.TABLE_ROWS)
                for row in rows:
                    cells = row.find_elements("css selector", "td")
                    for cell in cells:
                        if bank_name in cell.text.strip():
                            return True
            except Exception:
                pass
            time.sleep(0.1)
        return False

    def get_all_bank_names(self):
        """Get all bank names from the current table page."""
        names = []
        try:
            cells = self.driver.find_elements(
                By.CSS_SELECTOR,
                "table#excel-table tbody td.cdk-column-bank_name, "
                "table#excel-table tbody td:nth-child(2)"
            )
            for cell in cells:
                try:
                    name = cell.text.strip()
                    if name:
                        names.append(name)
                except Exception:
                    continue
        except Exception:
            pass
        return names

    def get_row_count_text(self):
        """Get the pagination text (e.g., '1 – 10 of 40')."""
        try:
            el = self.driver.find_element(
                By.CSS_SELECTOR, "mat-paginator"
            )
            return el.text.strip()
        except Exception:
            return ""

    # ==============================================================
    #  Row action buttons
    # ==============================================================

    def _click_action_button(self, bank_name, action_icon):
        """Click an action button for a specific row via the 3-dot (more_vert) menu.
        Uses JS approach like UOM's _click_action_menu_item() for speed.

        The ERP uses a single ⋮ menu per row instead of separate action columns.
        """
        # Map friendly action names to the actual icon text in the ERP menu
        icon_map = {
            "view": "visibility",
            "edit": "edit",
            "history": "history",
        }
        icon_text = icon_map.get(action_icon, action_icon)

        # Step 1 & 2: Find the row and click its menu trigger
        js_trigger = """
        var table = document.querySelector('table#excel-table');
        if (!table) { throw new Error('Table not found'); }
        var rows = table.querySelectorAll('tbody tr');
        for (var i = 0; i < rows.length; i++) {
            var cells = rows[i].querySelectorAll('td');
            for (var j = 0; j < cells.length; j++) {
                if (cells[j].textContent.trim().indexOf(arguments[0]) !== -1) {
                    // Try .erp-row-trigger first (3-dot menu button)
                    var trigger = rows[i].querySelector('.erp-row-trigger');
                    if (trigger) {
                        trigger.click();
                        return 'menu_opened';
                    }
                    // Fallback: cdk-column-actions button
                    var menuBtn = rows[i].querySelector('td.cdk-column-actions button');
                    if (menuBtn) {
                        menuBtn.scrollIntoView({block:'center'});
                        menuBtn.click();
                        return 'menu_opened';
                    }
                }
            }
        }
        throw new Error('Row or action trigger not found for bank: ' + arguments[0]);
        """
        result = self.driver.execute_script(js_trigger, bank_name)
        log.info("Action trigger click: " + str(result))

        # Wait briefly for dropdown to render
        try:
            WebDriverWait(self.driver, 2).until(
                EC.presence_of_element_located(("css selector", ".cdk-overlay-container .cdk-overlay-pane"))
            )
        except Exception:
            pass

        # Step 3 & 4: Click the correct menu item by its icon text
        js_menu_item = """
        var overlay = document.querySelector('.cdk-overlay-container');
        if (!overlay) {
            // Fallback: try mat-menu panel
            overlay = document.querySelector('.mat-mdc-menu-panel');
        }
        if (!overlay) throw new Error('CDK overlay not found after menu click');
        var items = overlay.querySelectorAll('button.mat-mdc-menu-item, button');
        for (var i = 0; i < items.length; i++) {
            var icon = items[i].querySelector('i.material-icons');
            if (icon && icon.textContent.trim() === arguments[0]) {
                items[i].click();
                return 'clicked menu item: ' + arguments[0];
            }
        }
        // Fallback: try text match
        for (var i = 0; i < items.length; i++) {
            var text = items[i].textContent.trim().toLowerCase();
            if (text.indexOf(arguments[0].toLowerCase()) !== -1) {
                items[i].click();
                return 'clicked_partial_' + arguments[0];
            }
        }
        throw new Error('Menu item with icon "' + arguments[0] + '" not found');
        """
        result = self.driver.execute_script(js_menu_item, icon_text)
        log.info("Menu item click: " + str(result))

    def click_view_button(self, bank_name):
        """Click the View button for a specific bank row via 3-dot menu."""
        log.info(f"Clicking View for: {bank_name}")
        self._force_close_panels()
        try:
            self._click_action_button(bank_name, 'view')
        except Exception as e:
            log.error(f"View button not found for '{bank_name}': {e}")

    def click_edit_button(self, bank_name):
        """Click the Edit button for a specific bank row via 3-dot menu."""
        log.info(f"Clicking Edit for: {bank_name}")
        self._force_close_panels()
        try:
            self._click_action_button(bank_name, 'edit')
        except Exception as e:
            log.error(f"Edit button not found for '{bank_name}': {e}")

    def click_history_button(self, bank_name):
        """Click the History button for a specific bank row via 3-dot menu."""
        log.info(f"Clicking History for: {bank_name}")
        self._force_close_panels()
        try:
            self._click_action_button(bank_name, 'history')
        except Exception as e:
            log.error(f"History button not found for '{bank_name}': {e}")

    # ==============================================================
    #  Search functionality
    # ==============================================================

    def open_search(self):
        """Click the search toggle button to show the search input via JS."""
        log.info("Opening search bar...")
        try:
            self.driver.execute_script("""
                var btn = document.querySelector('button.search-btn');
                if (btn) { btn.click(); return 'clicked'; }
                return 'not found';
            """)
            return True
        except Exception:
            pass
        log.warning("Search button not found")
        return False

    def search(self, text):
        """Type text into the search input and click search via JS.
        Fast approach like UOM with JS event dispatching."""
        log.info(f"Searching for: {text}")

        # Step 1: Check if search input is already visible
        search_input = None
        try:
            el = self.driver.find_element("css selector", "input#erpSearchInput")
            rect = self.driver.execute_script(
                "var r = arguments[0].getBoundingClientRect(); "
                "return r.width > 0 && r.height > 0;", el
            )
            if rect:
                search_input = el
                log.info("Search input already visible, skipping button click")
        except Exception:
            pass

        # Step 2: If search input not visible, click search button via JS to open it
        if search_input is None:
            log.info("Search input not visible, clicking search button via JS")
            try:
                self.driver.execute_script("""
                    var btn = document.querySelector('button.search-btn');
                    if (!btn) { throw new Error('Search button not found in DOM'); }
                    btn.scrollIntoView({block:'center'});
                    btn.click();
                    return 'clicked';
                """)
            except Exception as e:
                log.error("Failed to click search button via JS: " + str(e))
                return

            # Wait for search input to become visible
            try:
                search_input = WebDriverWait(self.driver, 3).until(
                    EC.visibility_of_element_located(("css selector", "input#erpSearchInput"))
                )
                log.info("Search input became visible")
            except Exception:
                log.warning("Search input did not become visible after clicking search button")
                return

        # Step 3: Clear existing value completely
        self.driver.execute_script("arguments[0].value = '';", search_input)
        self.driver.execute_script(
            "arguments[0].dispatchEvent(new Event('input', { bubbles: true }));",
            search_input,
        )

        # Step 4: Set new value and fire Angular change events
        self.driver.execute_script(
            "arguments[0].value = arguments[1];", search_input, str(text)
        )
        search_input.click()
        for event in ["input", "keyup", "change"]:
            self.driver.execute_script(
                f"arguments[0].dispatchEvent(new Event('{event}', {{ bubbles: true }}));",
                search_input,
            )

        # Step 5: Click the search button again via JS to submit/filter the table
        self.driver.execute_script("""
            var btn = document.querySelector('button.search-btn');
            if (btn) { btn.click(); return 'clicked'; }
            return 'not found';
        """)
        log.info("Search submit clicked via JS")

        # Step 6: Wait for table to refresh
        try:
            WebDriverWait(self.driver, 5).until(
                lambda d: d.find_elements("css selector", "table#excel-table tbody tr")
            )
        except Exception:
            pass  # Table might be empty (no results)

        log.info(f"Search completed for: {text}")

    def search_and_verify(self, bank_name):
        """Search for a bank name, then verify it exists in the filtered results.
        This is the recommended way to verify a create/update — uses search
        instead of scanning all rows (handles pagination automatically).
        Returns True if found.
        """
        log.info(f"Searching and verifying Bank: {bank_name}")
        self.search(bank_name)
        return self.is_bank_in_table(bank_name, timeout=3)

    def clear_search(self):
        """Clear the search input and refresh to get clean state."""
        log.info("Clearing search - hard refreshing")
        self.hard_refresh()

    # ==============================================================
    #  Pagination
    # ==============================================================

    def go_to_next_page(self):
        """Navigate to the next page in the table."""
        try:
            btns = self.driver.find_elements(
                By.CSS_SELECTOR,
                "button.mat-mdc-paginator-navigation-next"
            )
            for btn in btns:
                if btn.is_enabled():
                    self.driver.execute_script(
                        "arguments[0].click();", btn
                    )
                    return True
        except Exception:
            pass
        log.info("Next page button not available")
        return False

    def go_to_previous_page(self):
        """Navigate to the previous page in the table."""
        try:
            btns = self.driver.find_elements(
                By.CSS_SELECTOR,
                "button.mat-mdc-paginator-navigation-previous"
            )
            for btn in btns:
                if btn.is_enabled():
                    self.driver.execute_script(
                        "arguments[0].click();", btn
                    )
                    return True
        except Exception:
            pass
        log.info("Previous page button not available")
        return False

    def get_current_page_info(self):
        """Get current pagination info (range text)."""
        return self.get_row_count_text()

    # ==============================================================
    #  More menu
    # ==============================================================

    def open_more_menu(self):
        """Open the more_vert menu."""
        try:
            btn = self.driver.find_element(
                By.CSS_SELECTOR, "button[mattooltip='More']"
            )
            if btn.is_displayed():
                btn.click()
                return True
        except Exception:
            pass
        return False

    def click_export_excel(self):
        """Click Export to Excel from the more menu."""
        log.info("Clicking Export to Excel...")
        self.open_more_menu()
        try:
            option = self.driver.find_element(
                By.XPATH,
                "//button[contains(.,'Export to Excel') or "
                "contains(.,'Download as')]"
            )
            option.click()
            return True
        except Exception as e:
            log.warning(f"Export option not found: {e}")
            return False

    # ==============================================================
    #  Utility methods
    # ==============================================================

    def is_edit_mode(self):
        """Check if the popup is in edit mode (Update button instead of Submit)."""
        try:
            popup = self.driver.find_element(
                By.CSS_SELECTOR,
                ".edit_pop_up.override_edit_pop_up.popup-mode",
            )
            btns = popup.find_elements(
                By.CSS_SELECTOR, ".popup-footer button"
            )
            for btn in btns:
                if "Update" in btn.text:
                    return True
        except Exception:
            pass
        return False

    def is_view_mode(self):
        """Check if the popup is in view mode (only Cancel button)."""
        try:
            popup = self.driver.find_element(
                By.CSS_SELECTOR,
                ".edit_pop_up.override_edit_pop_up.popup-mode",
            )
            btns = popup.find_elements(
                By.CSS_SELECTOR, ".popup-footer button"
            )
            # View mode has only Cancel, no Submit/Update
            return len(btns) == 1
        except Exception:
            pass
        return False

    def is_field_disabled(self, name_attr):
        """Check if a specific input field is disabled."""
        try:
            popup = self.driver.find_element(
                By.CSS_SELECTOR,
                ".edit_pop_up.override_edit_pop_up.popup-mode",
            )
            input_el = popup.find_element(
                By.CSS_SELECTOR, f"input[name='{name_attr}']"
            )
            return input_el.is_enabled() is False
        except Exception:
            return False

    def is_dropdown_disabled(self, label_text):
        """Check if a dropdown is disabled."""
        try:
            popup = self.driver.find_element(
                By.CSS_SELECTOR,
                ".edit_pop_up.override_edit_pop_up.popup-mode",
            )
            form_fields = popup.find_elements(By.CSS_SELECTOR, "mat-form-field")
            for ff in form_fields:
                label = ff.find_element(By.CSS_SELECTOR, "mat-label")
                if label and label_text in label.text:
                    select = ff.find_element(By.CSS_SELECTOR, "mat-select")
                    return select.get_attribute("disabled") is not None
        except Exception:
            pass
        return False

    def _cleanup(self):
        """Fast cleanup: close any open popup, then hard refresh."""
        if self.is_add_form_open() or self.is_form_popup_open():
            self.force_close_form_popup()
        self.hard_refresh()

    def _debug_form_state(self):
        """Log debug information about the current form state."""
        try:
            popup = self.driver.find_element(
                By.CSS_SELECTOR,
                ".edit_pop_up.override_edit_pop_up.popup-mode",
            )
            log.info(f"Popup visible: {popup.is_displayed()}")

            heading = popup.find_element(By.CSS_SELECTOR, "h3")
            log.info(f"Heading: {heading.text.strip() if heading else 'N/A'}")

            inputs = popup.find_elements(By.CSS_SELECTOR, "input[type='text']")
            log.info(f"Text inputs: {len(inputs)}")
            for inp in inputs[:15]:
                name = inp.get_attribute("name")
                value = inp.get_attribute("value")
                disabled = inp.get_attribute("disabled")
                readonly = inp.get_attribute("readonly")
                log.info(
                    f"  [{name}] value='{value}' "
                    f"disabled={disabled} readonly={readonly}"
                )

            selects = popup.find_elements(By.CSS_SELECTOR, "mat-select")
            log.info(f"Mat-selects: {len(selects)}")

            btns = popup.find_elements(
                By.CSS_SELECTOR, ".popup-footer button"
            )
            btn_texts = [b.text.strip() for b in btns]
            log.info(f"Footer buttons: {btn_texts}")
        except Exception as e:
            log.warning(f"Debug form state failed: {e}")
