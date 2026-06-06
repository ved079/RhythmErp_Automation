"""
tax_rate_page.py
----------------
Page Object Model for RhythmERP Tax Rate screen (Common Settings).
Extends BasePage with Tax Rate-specific locators and methods.

Optimised (v2) — following UOM gold standard patterns:
- All button clicks via JS (bypasses CDK overlay blocking)
- All visibility checks via offsetParent (instant, no Selenium timeout)
- Fast polling (0.2s) instead of time.sleep()
- Single hard_refresh() for page reset
- Ultra-fast SweetAlert handler
- Single-line JS strings (no triple-quote Unicode issues)

Complexity: HIGHEST in Common Settings (nested sub-table).
Fields: 6 header fields + nested sub-table (HSN Number + Tax Rate).
Pattern: List view (table#excel-table) + popup form + sub-table tab + version flow.

Key quirks:
  - Edit button is DISABLED for all rows (use Version instead)
  - No success SweetAlert2 on create/version (silent close)
  - Date fields have name=null (must use mat-label traversal)
  - From Date auto-fills on open, To Date defaults to 2099-12-30
  - Sub-table starts with 1 empty row pre-created
  - Generic "Validation Failed" for ALL errors
"""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from common.base_page import BasePage
from common.logger import log


class TaxRatePage(BasePage):
    """
    Page Object for Common Settings > Tax Rate screen.
    """

    # ================================================================
    # LOCATORS — Form Popup
    # ================================================================

    FORM_POPUP = ("css", "div.edit_pop_up")
    FORM_HEADER_TITLE = ("css", "div.edit_pop_up .popup-header h3")

    # --- Header Fields (6 fields) ---
    TAX_RATE_NAME_INPUT = ("css", "input[name='Tax Rate Name']")
    TAX_TYPE_SELECT = ("xpath", "//mat-label[contains(.,'Tax Type')]/ancestor::mat-form-field//mat-select")
    TAX_AUTHORITY_SELECT = ("xpath", "//mat-label[contains(.,'Tax Authority')]/ancestor::mat-form-field//mat-select")
    FROM_DATE_INPUT = ("xpath", "//mat-label[contains(.,'From Date')]/ancestor::mat-form-field//input")
    TO_DATE_INPUT = ("xpath", "//mat-label[contains(.,'To Date')]/ancestor::mat-form-field//input")
    REVISION_STATUS_INPUT = ("css", "input[name='Revision Status']")

    # --- Form Buttons ---
    SUBMIT_BUTTON = ("xpath", "//div[contains(@class,'popup-footer')]//button[contains(.,'Submit')]")
    CREATE_VERSION_BUTTON = ("xpath", "//div[contains(@class,'popup-footer')]//button[contains(.,'Create Version')]")
    CANCEL_BUTTON = ("xpath", "//div[contains(@class,'popup-footer')]//button[contains(.,'Cancel')]")

    # ================================================================
    # LOCATORS — List Page
    # ================================================================

    TABLE = ("css", "table#excel-table")
    TABLE_ROWS = ("css", "table#excel-table tbody tr")

    # Search
    SEARCH_BUTTON = ("css", "button.search-btn")
    SEARCH_INPUT = ("css", "input#erpSearchInput")

    # ================================================================
    # LOCATORS — Sub-Table (inside form popup)
    # ================================================================

    SUB_TABLE_TAB = ("xpath", "//div[contains(@class,'big-model')]//div[contains(.,'Define Tax Rate Details')]")
    ADD_SUB_TABLE_ROW_BUTTON = ("xpath", "//div[contains(@class,'big-model')]//button[contains(.,'Add')]")

    # ================================================================
    # LOCATORS — History Popup
    # ================================================================

    HISTORY_POPUP = ("css", "div.popup-overlay")
    HISTORY_TITLE = ("xpath", "//h3[contains(.,'Tax Rate History')]")
    HISTORY_CANCEL_BTN = ("xpath", "//div[contains(@class,'popup')]//button[contains(.,'Cancel')]")

    # ================================================================
    # NAVIGATION
    # ================================================================

    PAGE_URL = "https://rhythmerp.algorhythms.in/#/dynamic-screens/Tax%20Rate"

    def navigate_to_page(self):
        """Navigate directly to the Tax Rate screen via URL."""
        log.info("Navigating to Tax Rate screen")
        self.driver.get(self.PAGE_URL)
        self._wait_for_page_ready()
        log.info("Arrived at Tax Rate page")

    def hard_refresh(self):
        """Hard refresh the current page and wait for it to be ready."""
        log.info("Hard refreshing Tax Rate page")
        self.driver.refresh()
        self._wait_for_page_ready()
        log.info("Page refreshed and ready")

    def _wait_for_page_ready(self, timeout=15):
        """Wait for the Tax Rate page table to appear."""
        end_time = time.monotonic() + timeout
        while time.monotonic() < end_time:
            try:
                tables = self.driver.find_elements("css selector", "table#excel-table")
                if tables:
                    log.info("Page ready (table found)")
                    return
            except Exception:
                pass
            time.sleep(0.3)
        log.warning("Page ready check timed out")

    def wait_for_table_load(self, timeout=15):
        """Wait for the main listing table to load."""
        self._wait_for_page_ready(timeout)

    def is_page_loaded(self, timeout=5):
        """Check if the Tax Rate page is loaded with table visible."""
        return self.driver.execute_script(
            "var t = document.querySelector('table#excel-table'); "
            "return t && t.offsetParent !== null;"
        )

    # ================================================================
    # CLEANUP — Force close all popups, overlays, alerts
    # ================================================================

    def _cleanup(self):
        """Fast cleanup: dismiss SweetAlert, close form/history popups, remove backdrops."""
        # 1. Dismiss SweetAlert via JS (instant)
        self.driver.execute_script(
            "var btn = document.querySelector('.swal2-confirm'); "
            "if (btn) btn.click();"
        )
        # 2. Close form popup Cancel via JS
        self.driver.execute_script(
            "var footers = document.querySelectorAll('.popup-footer'); "
            "for (var i = 0; i < footers.length; i++) { "
            "  var buttons = footers[i].querySelectorAll('button'); "
            "  for (var j = 0; j < buttons.length; j++) { "
            "    if (buttons[j].textContent.indexOf('Cancel') !== -1) { "
            "      buttons[j].click(); return; "
            "    } "
            "  } "
            "}"
        )
        # 3. Remove only CDK overlay backdrops (NEVER containers or panes)
        self.driver.execute_script(
            "document.querySelectorAll('.cdk-overlay-backdrop').forEach(function(el) { el.remove(); });"
        )

    def force_cleanup_all(self):
        """Force-close any stuck popups, overlays, alerts. Full version with waits."""
        try:
            # 1. Dismiss SweetAlert via JS
            self.driver.execute_script(
                "var btn = document.querySelector('.swal2-confirm'); "
                "if (btn) btn.click();"
            )
            time.sleep(0.2)
            # 2. Close form popup via JS Cancel
            self.driver.execute_script(
                "var footers = document.querySelectorAll('.popup-footer'); "
                "for (var i = 0; i < footers.length; i++) { "
                "  var buttons = footers[i].querySelectorAll('button'); "
                "  for (var j = 0; j < buttons.length; j++) { "
                "    if (buttons[j].textContent.indexOf('Cancel') !== -1) { "
                "      buttons[j].click(); return; "
                "    } "
                "  } "
                "}"
            )
            time.sleep(0.2)
            # 3. Remove only CDK backdrops
            self.driver.execute_script(
                "document.querySelectorAll('.cdk-overlay-backdrop').forEach(function(el) { el.remove(); });"
            )
            # 4. Escape key for any remaining overlays
            try:
                from selenium.webdriver.common.action_chains import ActionChains
                ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
            except Exception:
                pass
        except Exception as e:
            log.warning("Cleanup completed with warning: " + str(e))

    def _force_close_panels(self):
        """Close any open dropdown panels. Only removes .erp-action-menu panels and backdrops.
        CRITICAL: Never remove all CDK overlay panes — that kills history popups too."""
        try:
            has_overlay = self.driver.execute_script(
                "return document.querySelectorAll('.cdk-overlay-backdrop').length > 0;"
            )
            if has_overlay:
                from selenium.webdriver.common.action_chains import ActionChains
                ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
                time.sleep(0.2)
        except Exception:
            pass

    # ================================================================
    # JS HELPERS — Gold standard patterns
    # ================================================================

    def _js_click_popup_button(self, button_text):
        """Click a popup footer button (Submit/Update/Cancel/Create Version) via JS."""
        js = "var footers = document.querySelectorAll('.popup-footer'); " \
             "for (var i = 0; i < footers.length; i++) { " \
             "  var buttons = footers[i].querySelectorAll('button'); " \
             "  for (var j = 0; j < buttons.length; j++) { " \
             "    if (buttons[j].textContent.trim().indexOf(arguments[0]) !== -1) { " \
             "      buttons[j].click(); return 'clicked_' + arguments[0]; " \
             "    } " \
             "  } " \
             "} " \
             "throw new Error('Button not found: ' + arguments[0]);"
        try:
            result = self.driver.execute_script(js, button_text)
            log.info("JS click " + button_text + ": " + str(result))
        except Exception as e:
            log.warning("JS click failed for " + button_text + ": " + str(e))

    def _js_click(self, locator):
        """Click an element via JavaScript — bypasses CDK overlay blocking."""
        element = self.find_element(locator)
        self.driver.execute_script("arguments[0].click();", element)

    def _js_click_element(self, element):
        """Click a WebElement via JavaScript."""
        self.driver.execute_script("arguments[0].click();", element)

    def _set_text_field(self, locator, value):
        """Set text field value using atomic JavaScript for Angular reactivity."""
        try:
            self.driver.execute_script(
                "var input = arguments[0]; "
                "var nativeSetter = Object.getOwnPropertyDescriptor("
                "window.HTMLInputElement.prototype, 'value').set; "
                "nativeSetter.call(input, arguments[1]); "
                "input.dispatchEvent(new Event('input', {bubbles: true})); "
                "input.dispatchEvent(new Event('change', {bubbles: true}));",
                self.find_element(locator), value
            )
        except Exception:
            self.type_text(locator, value, clear_first=True)

    def _set_date_field(self, locator, value):
        """Set date picker value via JavaScript with blur event."""
        try:
            self.driver.execute_script(
                "var input = arguments[0]; "
                "var nativeSetter = Object.getOwnPropertyDescriptor("
                "window.HTMLInputElement.prototype, 'value').set; "
                "nativeSetter.call(input, arguments[1]); "
                "input.dispatchEvent(new Event('input', {bubbles: true})); "
                "input.dispatchEvent(new Event('change', {bubbles: true})); "
                "input.dispatchEvent(new Event('blur', {bubbles: true}));",
                self.find_element(locator), value
            )
            log.info("Set date field to: " + str(value))
        except Exception as e:
            log.warning("Date field JS set failed: " + str(e))
            try:
                element = self.find_element(locator)
                element.clear()
                element.send_keys(value)
            except Exception:
                pass

    def _blur_active_element(self):
        """Blur any active input by clicking body via JS."""
        self.driver.execute_script("document.body.click();")

    # ================================================================
    # ADD FORM — Open / Close
    # ================================================================

    def open_add_form(self):
        """Click the Add (+) button to open the create form popup via JS."""
        log.info("Opening Add form")
        js_click_add = "var btn = document.querySelector('button.erp-add-btn'); " \
                       "if (!btn) { var icons = document.querySelectorAll('button[mat-icon-button]'); " \
                       "  for (var i = 0; i < icons.length; i++) { " \
                       "    var icon = icons[i].querySelector('mat-icon'); " \
                       "    if (icon && icon.textContent.trim() === 'add') { btn = icons[i]; break; } " \
                       "  } " \
                       "} " \
                       "if (!btn) { throw new Error('Add button not found'); } " \
                       "btn.scrollIntoView({block:'center'}); btn.click(); return 'clicked';"
        try:
            result = self.driver.execute_script(js_click_add)
            log.info("Add button clicked via JS: " + str(result))
        except Exception as e:
            log.warning("JS click failed, falling back: " + str(e))
            try:
                self.click(self.ADD_BUTTON)
            except Exception:
                pass
        # Wait for form popup to appear
        try:
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located(("css selector", "div.edit_pop_up"))
            )
            log.info("Add form opened")
        except Exception:
            log.warning("Add form may not have opened")

    def close_form_via_cancel(self):
        """Close the form popup via Cancel button using JS click."""
        log.info("Closing form via Cancel button")
        self._js_click_popup_button('Cancel')

    def cancel(self):
        """Alias for close_form_via_cancel."""
        self.close_form_via_cancel()

    # ================================================================
    # FORM — State Checks (fast offsetParent-based)
    # ================================================================

    def is_form_open(self):
        """Check if the Tax Rate form popup is currently visible via offsetParent."""
        return self.driver.execute_script(
            "var el = document.querySelector('div.edit_pop_up'); "
            "return el && el.offsetParent !== null;"
        )

    def is_view_mode(self):
        """Check if the form is in View mode (no Submit/Version button visible)."""
        try:
            has_submit = self.driver.execute_script(
                "var btns = document.querySelectorAll('.popup-footer button'); "
                "for (var i = 0; i < btns.length; i++) { "
                "  if (btns[i].textContent.indexOf('Submit') !== -1 && btns[i].offsetParent !== null) return true; "
                "} return false;"
            )
            has_version = self.driver.execute_script(
                "var btns = document.querySelectorAll('.popup-footer button'); "
                "for (var i = 0; i < btns.length; i++) { "
                "  if (btns[i].textContent.indexOf('Create Version') !== -1 && btns[i].offsetParent !== null) return true; "
                "} return false;"
            )
            return not has_submit and not has_version
        except Exception:
            return True

    def wait_for_form_to_open(self, timeout=10):
        """Wait until the form popup appears using fast poll."""
        end_time = time.monotonic() + timeout
        while time.monotonic() < end_time:
            if self.is_form_open():
                log.info("Form popup is now open")
                return
            time.sleep(0.2)
        log.error("Form popup did not open within timeout")
        self.take_screenshot("tax_rate_form_not_opened")
        raise Exception("Form popup did not open within " + str(timeout) + "s")

    def wait_for_form_to_close(self, timeout=10):
        """Wait until the form popup disappears using fast poll."""
        end_time = time.monotonic() + timeout
        while time.monotonic() < end_time:
            if not self.is_form_open():
                log.info("Form popup closed")
                return
            time.sleep(0.2)
        log.warning("Form popup still visible after timeout")

    def get_form_title(self):
        """Get the form popup header title."""
        try:
            return self.driver.execute_script(
                "var h = document.querySelector('div.edit_pop_up .popup-header h3'); "
                "return h ? h.textContent.trim() : '';"
            )
        except Exception:
            return ""

    # ================================================================
    # HEADER FIELD FILL — Individual methods
    # ================================================================

    def fill_tax_rate_name(self, name):
        """Type Tax Rate Name into the text input field."""
        if name:
            self._set_text_field(self.TAX_RATE_NAME_INPUT, name)
            log.info("Tax Rate Name set to: " + name)

    def select_tax_type(self, tax_type):
        """Select Tax Type from mat-select dropdown via JS click."""
        if not tax_type:
            return True
        log.info("Selecting Tax Type: " + tax_type)
        try:
            self._blur_active_element()
            time.sleep(0.2)
            # Click mat-select via JS
            self.driver.execute_script(
                "var sel = document.evaluate("
                "\"//mat-label[contains(.,'Tax Type')]/ancestor::mat-form-field//mat-select\", "
                "document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue; "
                "if (sel) { sel.scrollIntoView({block:'center'}); sel.click(); return 'clicked'; } "
                "throw new Error('Tax Type select not found');"
            )
            # Wait for options
            option = ("xpath", "//mat-option//span[contains(text(),'" + tax_type + "')]")
            WebDriverWait(self.driver, 8).until(EC.presence_of_element_located(option))
            time.sleep(0.2)
            self._js_click(option)
            time.sleep(0.3)
            log.info("Tax Type set to: " + tax_type)
            return True
        except Exception as e:
            log.warning("Tax Type selection failed: " + str(e))
            return False

    def select_tax_authority(self, authority):
        """Select Tax Authority from mat-select dropdown via JS click."""
        if not authority:
            return True
        log.info("Selecting Tax Authority: " + authority)
        try:
            self._blur_active_element()
            time.sleep(0.2)
            self.driver.execute_script(
                "var sel = document.evaluate("
                "\"//mat-label[contains(.,'Tax Authority')]/ancestor::mat-form-field//mat-select\", "
                "document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue; "
                "if (sel) { sel.scrollIntoView({block:'center'}); sel.click(); return 'clicked'; } "
                "throw new Error('Tax Authority select not found');"
            )
            option = ("xpath", "//mat-option//span[contains(text(),'" + authority + "')]")
            WebDriverWait(self.driver, 8).until(EC.presence_of_element_located(option))
            time.sleep(0.2)
            self._js_click(option)
            time.sleep(0.3)
            log.info("Tax Authority set to: " + authority)
            return True
        except Exception as e:
            log.warning("Tax Authority selection failed: " + str(e))
            return False

    def fill_from_date(self, date_str):
        """Set From Date in the date picker."""
        if date_str:
            self._set_date_field(self.FROM_DATE_INPUT, date_str)
            log.info("From Date set to: " + str(date_str))

    def fill_to_date(self, date_str):
        """Set To Date in the date picker."""
        if date_str:
            self._set_date_field(self.TO_DATE_INPUT, date_str)
            log.info("To Date set to: " + str(date_str))

    def fill_revision_status(self, status):
        """Type Revision Status into the text input field."""
        if status:
            self._set_text_field(self.REVISION_STATUS_INPUT, status)
            log.info("Revision Status set to: " + status)

    # ================================================================
    # HEADER FIELD FILL — Combined
    # ================================================================

    def fill_all_fields(self, data):
        """Fill all header fields. Order: dropdowns first, then text, then dates."""
        tax_type = data.get("tax_type", "")
        tax_authority = data.get("tax_authority", "")
        if tax_type:
            self.select_tax_type(tax_type)
        if tax_authority:
            self.select_tax_authority(tax_authority)

        tax_rate_name = data.get("tax_rate_name", "")
        revision_status = data.get("revision_status", "")
        if tax_rate_name:
            self.fill_tax_rate_name(tax_rate_name)
        if revision_status:
            self.fill_revision_status(revision_status)

        from_date = data.get("from_date", "")
        to_date = data.get("to_date", "")
        if from_date:
            self.fill_from_date(from_date)
        if to_date:
            self.fill_to_date(to_date)

    def clear_header_fields(self):
        """Clear all header text input fields via JS."""
        log.info("Clearing header fields")
        self.driver.execute_script(
            "var nameInput = document.querySelector('input[name=\"Tax Rate Name\"]'); "
            "if (nameInput) { nameInput.value = ''; nameInput.dispatchEvent(new Event('input', {bubbles: true})); } "
            "var revInput = document.querySelector('input[name=\"Revision Status\"]'); "
            "if (revInput) { revInput.value = ''; revInput.dispatchEvent(new Event('input', {bubbles: true})); }"
        )

    # ================================================================
    # SUB-TABLE — Row Operations
    # ================================================================

    def _switch_to_sub_table_tab(self):
        """Click 'Define Tax Rate Details' tab to reveal sub-table via JS."""
        try:
            self.driver.execute_script(
                "var tabs = document.querySelectorAll('.big-model div'); "
                "for (var i = 0; i < tabs.length; i++) { "
                "  if (tabs[i].textContent.indexOf('Define Tax Rate Details') !== -1) { "
                "    tabs[i].click(); return; "
                "  } "
                "}"
            )
            time.sleep(0.5)
            log.info("Switched to sub-table tab")
        except Exception:
            log.info("Sub-table tab not found (may already be visible)")

    def _get_sub_table_rows(self):
        """Get all sub-table row WebElements."""
        try:
            return self.driver.find_elements(By.CSS_SELECTOR, "div.edit_pop_up table.mat-table tbody tr")
        except Exception:
            return []

    def _get_sub_table_row_count(self):
        """Get the number of sub-table rows."""
        return len(self._get_sub_table_rows())

    def add_sub_table_row(self):
        """Click the Add button to add a new empty row to the sub-table via JS."""
        log.info("Adding new sub-table row")
        try:
            self.driver.execute_script(
                "var btns = document.querySelectorAll('.big-model button'); "
                "for (var i = 0; i < btns.length; i++) { "
                "  if (btns[i].textContent.indexOf('Add') !== -1) { btns[i].click(); return; } "
                "}"
            )
            time.sleep(0.5)
            log.info("New sub-table row added")
        except Exception as e:
            log.warning("Failed to add sub-table row: " + str(e))

    def delete_sub_table_row(self, row_index=-1):
        """Delete a sub-table row by clicking its delete button via JS."""
        rows = self._get_sub_table_rows()
        if not rows:
            return
        if row_index == -1:
            row_index = len(rows) - 1
        try:
            row = rows[row_index]
            delete_btn = row.find_element(By.CSS_SELECTOR, "td.mat-column-action button")
            self._js_click_element(delete_btn)
            time.sleep(0.3)
        except Exception as e:
            log.warning("Failed to delete sub-table row: " + str(e))

    def select_hsn_number(self, hsn, row_index=0):
        """Select HSN Number from mat-select dropdown in a sub-table row."""
        if not hsn:
            return True
        log.info("Selecting HSN Number '" + hsn + "' in row " + str(row_index))
        try:
            rows = self._get_sub_table_rows()
            if row_index >= len(rows):
                log.warning("Row " + str(row_index) + " does not exist")
                return False
            row = rows[row_index]
            hsn_select = row.find_element(By.CSS_SELECTOR, "mat-select")
            self._blur_active_element()
            time.sleep(0.2)
            self._js_click_element(hsn_select)
            # Wait for options
            option = ("xpath", "//mat-option//span[contains(text(),'" + hsn + "')]")
            WebDriverWait(self.driver, 8).until(EC.presence_of_element_located(option))
            time.sleep(0.2)
            self._js_click(option)
            time.sleep(0.3)
            log.info("HSN Number set to: " + hsn)
            return True
        except Exception as e:
            log.warning("HSN Number selection failed: " + str(e))
            return False

    def fill_sub_table_tax_rate(self, rate, row_index=0):
        """Set Tax Rate value in a sub-table row via JS."""
        log.info("Setting Tax Rate to " + str(rate) + " in row " + str(row_index))
        try:
            rows = self._get_sub_table_rows()
            if row_index >= len(rows):
                return
            row = rows[row_index]
            tax_rate_input = row.find_element(By.CSS_SELECTOR, "input[name='Tax Rate']")
            self.driver.execute_script(
                "var input = arguments[0]; "
                "var nativeSetter = Object.getOwnPropertyDescriptor("
                "window.HTMLInputElement.prototype, 'value').set; "
                "nativeSetter.call(input, arguments[1]); "
                "input.dispatchEvent(new Event('input', {bubbles: true})); "
                "input.dispatchEvent(new Event('change', {bubbles: true}));",
                tax_rate_input, str(rate)
            )
            log.info("Tax Rate set to: " + str(rate))
        except Exception as e:
            log.warning("Failed to set Tax Rate: " + str(e))

    def fill_sub_table_row(self, row_data, row_index=0):
        """Fill HSN Number and Tax Rate for a specific sub-table row."""
        hsn = row_data.get("hsn_number", "")
        rate = row_data.get("tax_rate", "")
        hsn_ok = self.select_hsn_number(hsn, row_index)
        if hsn_ok:
            self._force_close_panels()
            self.fill_sub_table_tax_rate(rate, row_index)
        return hsn_ok

    def fill_sub_table(self, sub_table_rows):
        """Fill multiple sub-table rows. First row is pre-created."""
        if not sub_table_rows:
            return True
        self._switch_to_sub_table_tab()
        time.sleep(0.3)
        # Add extra rows if needed
        current_rows = self._get_sub_table_row_count()
        needed = len(sub_table_rows)
        for _ in range(max(0, needed - current_rows)):
            self.add_sub_table_row()
        # Fill rows from bottom-up
        all_ok = True
        for i in range(needed - 1, -1, -1):
            ok = self.fill_sub_table_row(sub_table_rows[i], row_index=i)
            if not ok:
                all_ok = False
        return all_ok

    # ================================================================
    # FORM — Submit / Create Version (JS clicks)
    # ================================================================

    def submit(self):
        """Click the Submit button via JS."""
        log.info("Clicking Submit button")
        self._force_close_panels()
        self._js_click_popup_button('Submit')

    def click_create_version(self):
        """Click the Create Version button via JS."""
        log.info("Clicking Create Version button")
        self._force_close_panels()
        self._js_click_popup_button('Create Version')

    # ================================================================
    # CREATE RECORD — Full flow (optimized, no driver.refresh per cycle)
    # ================================================================

    def create_record(self, data, max_cycles=3):
        """Create a new Tax Rate record. No success SweetAlert2 — form closes silently.

        Args:
            data: Dict with "header" and "sub_table_rows"
            max_cycles: Max retry cycles

        Returns:
            dict with "status" and "error"
        """
        header = data.get("header", {})
        sub_rows = data.get("sub_table_rows", [])
        name = header.get("tax_rate_name", "Unknown")

        for cycle in range(1, max_cycles + 1):
            log.info("Creating Tax Rate: " + name + " (cycle " + str(cycle) + "/" + str(max_cycles) + ")")
            try:
                # Hard refresh for clean state
                self.hard_refresh()

                # Open Add form
                self.open_add_form()

                # Fill header fields
                self.fill_all_fields(header)

                # Fill sub-table rows
                if sub_rows:
                    self.fill_sub_table(sub_rows)

                # Click Submit
                self.submit()

                # ALERT-FIRST: Check for validation alert
                if self.is_validation_alert_present(timeout=5):
                    title = self.get_sweetalert_title()
                    log.info("Validation Failed: " + title)
                    self.accept_sweetalert()
                    time.sleep(0.3)
                    self.cancel()
                    return {"status": "failed", "error": title}

                # Check if form closed (silent success)
                time.sleep(1)
                if not self.is_form_open():
                    log.info("Record '" + name + "' created successfully (silent success)")
                    return {"status": "success", "error": ""}

                # Form still open, no alert — retry
                log.warning("Cycle " + str(cycle) + ": Form still open, no alert — retrying")

            except Exception as e:
                log.warning("Cycle " + str(cycle) + " error: " + str(e))

            # Cleanup before retry
            try:
                self.cancel()
            except Exception:
                pass
            time.sleep(0.5)

        return {"status": "failed", "error": "Could not create record after " + str(max_cycles) + " cycles"}

    # ================================================================
    # SWEET ALERT — Fast detection & handling
    # ================================================================

    def is_validation_alert_present(self, timeout=5):
        """Check if SweetAlert 'Validation Failed' popup is visible. Fast poll."""
        end_time = time.monotonic() + timeout
        while time.monotonic() < end_time:
            try:
                visible = self.driver.execute_script(
                    "var el = document.querySelector('.swal2-popup.swal2-icon-warning, .swal2-popup.swal2-icon-error'); "
                    "return el && el.offsetParent !== null;"
                )
                if visible:
                    return True
            except Exception:
                pass
            time.sleep(0.2)
        return False

    def get_sweetalert_title(self):
        """Get the title text from the current SweetAlert popup."""
        try:
            return self.driver.execute_script(
                "var el = document.querySelector('.swal2-title'); "
                "return el ? el.textContent.trim() : '';"
            )
        except Exception:
            return ""

    def get_sweetalert_message(self):
        """Get the message text from the current SweetAlert popup."""
        try:
            return self.driver.execute_script(
                "var el = document.querySelector('.swal2-html-container'); "
                "return el ? el.textContent.trim() : '';"
            )
        except Exception:
            return ""

    def accept_sweetalert(self):
        """Click OK/Confirm on the current SweetAlert popup via JS."""
        log.info("Accepting SweetAlert (clicking OK)")
        self.driver.execute_script(
            "var btn = document.querySelector('.swal2-confirm'); "
            "if (btn) btn.click();"
        )
        # Wait for SweetAlert to disappear
        try:
            WebDriverWait(self.driver, 3).until(
                EC.invisibility_of_element_located(("css selector", ".swal2-popup"))
            )
        except Exception:
            pass

    def dismiss_sweetalert(self):
        """Click Cancel on the current SweetAlert popup via JS."""
        self.driver.execute_script(
            "var btn = document.querySelector('.swal2-cancel'); "
            "if (btn) btn.click();"
        )

    def is_any_alert_present(self, timeout=3):
        """Check if any SweetAlert popup is visible. Fast poll."""
        end_time = time.monotonic() + timeout
        while time.monotonic() < end_time:
            try:
                visible = self.driver.execute_script(
                    "var el = document.querySelector('.swal2-popup'); "
                    "return el && el.offsetParent !== null;"
                )
                if visible:
                    return True
            except Exception:
                pass
            time.sleep(0.2)
        return False

    # ================================================================
    # TABLE — Read Data (fast JS-based)
    # ================================================================

    def get_table_row_count(self):
        """Get the number of data rows in the Tax Rate listing table."""
        try:
            rows = self.driver.find_elements(By.CSS_SELECTOR, "table#excel-table tbody tr")
            return len(rows)
        except Exception:
            return 0

    def get_name_from_row(self, row_index):
        """Get the Tax Rate Name from a specific table row."""
        try:
            cells = self.driver.find_elements(By.CSS_SELECTOR, "td.mat-column-tax_rate_name")
            if row_index < len(cells):
                return cells[row_index].text.strip()
            return ""
        except Exception:
            return ""

    def find_name_row_index(self, name):
        """Find a table row index by matching the Tax Rate Name column."""
        row_count = self.get_table_row_count()
        name_lower = name.strip().lower()
        for i in range(row_count):
            cell_name = self.get_name_from_row(i)
            if cell_name.strip().lower() == name_lower:
                log.info("Found '" + name + "' at row " + str(i))
                return i
        log.warning("Record '" + name + "' not found in visible rows")
        return -1

    def is_name_in_table(self, name):
        """Check if a Tax Rate Name exists in the table."""
        return self.find_name_row_index(name) != -1

    def get_column_headers(self):
        """Get all column header texts from the Tax Rate table."""
        try:
            headers = self.driver.find_elements(By.CSS_SELECTOR, "table#excel-table thead th")
            return [h.text.strip() for h in headers if h.text.strip()]
        except Exception:
            return []

    # ================================================================
    # TABLE — Action Buttons (JS clicks for each row)
    # ================================================================

    def _click_action_button(self, row_index, action_name):
        """Click View/Edit/Version/History button on a specific row via JS.

        The Tax Rate screen has 4 button columns per row:
          View (mat-column-view), Edit (mat-column-edit),
          Version (mat-column-folder), History (mat-column-archive)
        """
        log.info("Clicking " + action_name + " on row " + str(row_index))
        # Map action name to column class
        col_map = {
            "View": "mat-column-view",
            "Edit": "mat-column-edit",
            "Version": "mat-column-folder",
            "History": "mat-column-archive",
        }
        col_class = col_map.get(action_name, "mat-column-view")
        js = "var rows = document.querySelectorAll('table#excel-table tbody tr'); " \
             "if (arguments[0] >= rows.length) throw new Error('Row not found'); " \
             "var row = rows[arguments[0]]; " \
             "var btn = row.querySelector('td." + col_class + " button'); " \
             "if (!btn) throw new Error('Button not found in " + col_class + "'); " \
             "btn.click(); return 'clicked';"
        try:
            result = self.driver.execute_script(js, row_index)
            log.info(action_name + " clicked: " + str(result))
        except Exception as e:
            log.warning("JS click " + action_name + " failed: " + str(e))
            # Fallback: try Selenium click
            try:
                if action_name == "View":
                    self.click(("xpath", "(//td[contains(@class,'mat-column-view')]//button)[" + str(row_index + 1) + "]"))
                elif action_name == "Edit":
                    self.click(("xpath", "(//td[contains(@class,'mat-column-edit')]//button)[" + str(row_index + 1) + "]"))
                elif action_name == "Version":
                    self.click(("xpath", "(//td[contains(@class,'mat-column-folder')]//button)[" + str(row_index + 1) + "]"))
                elif action_name == "History":
                    self.click(("xpath", "(//td[contains(@class,'mat-column-archive')]//button)[" + str(row_index + 1) + "]"))
            except Exception:
                pass

    def click_view_on_row(self, row_index):
        """Click the View (eye) button on a specific table row."""
        self._click_action_button(row_index, "View")
        self.wait_for_form_to_open()

    def click_version_on_row(self, row_index):
        """Click the Version (folder) button on a specific table row."""
        self._click_action_button(row_index, "Version")
        self.wait_for_form_to_open()

    def click_history_on_row(self, row_index):
        """Click the History (archive) button on a specific table row."""
        self._click_action_button(row_index, "History")
        self.wait_for_history_popup()

    # ================================================================
    # SEARCH (fast JS-based)
    # ================================================================

    def search_record(self, name, exact=False):
        """Search for a record by Tax Rate Name using JS search."""
        log.info("Searching for: " + name + " (exact=" + str(exact) + ")")
        try:
            self._do_js_search(name)
            row_count = self.get_table_row_count()
            if row_count == 0:
                return False
            if not exact:
                return True
            # Exact mode
            name_lower = name.strip().lower()
            for i in range(row_count):
                row_name = self.get_name_from_row(i).strip().lower()
                if row_name == name_lower:
                    return True
            return False
        except Exception as e:
            log.error("Search failed: " + str(e))
            return False

    def _do_js_search(self, text):
        """Execute search using atomic JavaScript (fast)."""
        # Toggle search input
        self.driver.execute_script(
            "var toggleBtn = document.querySelector('button.search-btn'); "
            "if (toggleBtn) toggleBtn.click();"
        )
        # Wait for search input
        try:
            WebDriverWait(self.driver, 5).until(
                EC.visibility_of_element_located(("css selector", "input#erpSearchInput"))
            )
        except Exception:
            # Try placeholder-based search input
            try:
                WebDriverWait(self.driver, 3).until(
                    EC.presence_of_element_located(("css selector", "input[placeholder='Search']"))
                )
            except Exception:
                pass
        time.sleep(0.3)

        # Set value and fire events
        self.driver.execute_script(
            "var input = document.querySelector('input#erpSearchInput') || document.querySelector('input[placeholder=\"Search\"]'); "
            "if (!input) return; "
            "var nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set; "
            "nativeSetter.call(input, ''); "
            "input.dispatchEvent(new Event('input', {bubbles: true})); "
            "nativeSetter.call(input, arguments[0]); "
            "input.dispatchEvent(new Event('input', {bubbles: true})); "
            "input.dispatchEvent(new KeyboardEvent('keydown', {key:'Enter',code:'Enter',keyCode:13,bubbles:true}));",
            text
        )
        # Wait for table to refresh
        time.sleep(1)

    def clear_search(self):
        """Clear the search filter to show all records."""
        log.info("Clearing search filter")
        self.hard_refresh()

    # ================================================================
    # REFRESH
    # ================================================================

    def refresh_table(self):
        """Refresh the table data."""
        self.hard_refresh()

    # ================================================================
    # HISTORY POPUP
    # ================================================================

    def wait_for_history_popup(self, timeout=15):
        """Wait for the history popup to open and load data."""
        end_time = time.monotonic() + timeout
        while time.monotonic() < end_time:
            if self.is_history_popup_open():
                log.info("History popup loaded")
                return
            time.sleep(0.3)
        log.warning("History popup did not load within timeout")

    def is_history_popup_open(self, timeout=5):
        """Check if the History popup is currently visible via offsetParent."""
        try:
            return self.driver.execute_script(
                "var el = document.querySelector('div.popup-overlay'); "
                "return el && el.offsetParent !== null;"
            )
        except Exception:
            return False

    def get_history_title(self):
        """Get the title text from the History popup header."""
        try:
            return self.driver.execute_script(
                "var h = document.querySelector('div.popup-overlay h3'); "
                "return h ? h.textContent.trim() : '';"
            )
        except Exception:
            return ""

    def get_history_row_count(self):
        """Get the number of rows in the history table."""
        try:
            rows = self.driver.find_elements(By.CSS_SELECTOR, "div.popup-overlay table tbody tr")
            return len(rows)
        except Exception:
            return 0

    def close_history_popup(self):
        """Close the History popup via Cancel button using JS."""
        log.info("Closing History popup")
        self.driver.execute_script(
            "var footers = document.querySelectorAll('.popup-overlay .popup-footer, div.popup-overlay .popup-footer'); "
            "for (var i = 0; i < footers.length; i++) { "
            "  var buttons = footers[i].querySelectorAll('button'); "
            "  for (var j = 0; j < buttons.length; j++) { "
            "    if (buttons[j].textContent.indexOf('Cancel') !== -1) { "
            "      buttons[j].click(); return; "
            "    } "
            "  } "
            "}"
        )
        time.sleep(0.3)
