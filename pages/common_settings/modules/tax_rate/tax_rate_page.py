"""
tax_rate_page.py
----------------
Page Object Model for RhythmERP Tax Rate screen (Common Settings).
Extends BasePage with Tax Rate-specific locators and methods.

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

    # --- Form Container ---
    FORM_POPUP = ("css", "div.edit_pop_up")
    FORM_CONTENT = ("css", "div.edit_pop_up div.overflow_model")
    FORM_HEADER_TITLE = ("css", "div.edit_pop_up .popup-header h3")

    # --- Header Fields (6 fields) ---
    # 1. Tax Rate Name — text input
    TAX_RATE_NAME_INPUT = ("css", "input[name='Tax Rate Name']")

    # 2. Tax Type — mat-select (1 option: GST)
    TAX_TYPE_SELECT = ("xpath", "//mat-label[contains(.,'Tax Type')]/ancestor::mat-form-field//mat-select")

    # 3. Tax Authority — mat-select (6 options)
    TAX_AUTHORITY_SELECT = ("xpath", "//mat-label[contains(.,'Tax Authority')]/ancestor::mat-form-field//mat-select")

    # 4. From Date — date picker (name=null — TR-04)
    FROM_DATE_INPUT = ("xpath", "//mat-label[contains(.,'From Date')]/ancestor::mat-form-field//input")

    # 5. To Date — date picker (name=null — TR-04)
    TO_DATE_INPUT = ("xpath", "//mat-label[contains(.,'To Date')]/ancestor::mat-form-field//input")

    # 6. Revision Status — text input
    REVISION_STATUS_INPUT = ("css", "input[name='Revision Status']")

    # --- Form Buttons ---
    SUBMIT_BUTTON = ("xpath", "//div[contains(@class,'popup-footer')]//button[contains(.,'Submit')]")
    CREATE_VERSION_BUTTON = ("xpath", "//div[contains(@class,'popup-footer')]//button[contains(.,'Create Version')]")
    CANCEL_BUTTON = ("xpath", "//div[contains(@class,'popup-footer')]//button[contains(.,'Cancel')]")

    # --- Popup Header Buttons (fullscreen + close X) ---
    CLOSE_X_BUTTON = ("xpath", "//div[@class='popup-actions']//button[contains(.,'close')]")
    FULLSCREEN_BUTTON = ("xpath", "//div[@class='popup-actions']//button[contains(.,'fullscreen')]")

    # ================================================================
    # LOCATORS — SweetAlert2 Popups
    # ================================================================

    SWEET_ALERT_POPUP = ("css", ".swal2-popup")
    SWEET_ALERT_TITLE = ("css", ".swal2-title")
    SWEET_ALERT_MESSAGE = ("css", ".swal2-html-container")
    SWEET_ALERT_CONFIRM_BTN = ("css", "button.swal2-confirm")
    SWEET_ALERT_CANCEL_BTN = ("css", "button.swal2-cancel")

    # ================================================================
    # LOCATORS — List Page
    # ================================================================

    # Add button
    ADD_BUTTON = ("xpath", "//button[mat-icon[text()='add']]")

    # Data table
    TABLE = ("css", "table#excel-table")
    TABLE_BODY = ("css", "table#excel-table tbody")
    TABLE_ROWS = ("css", "table#excel-table tbody tr")
    TABLE_BODY_ROWS = ("css", "table#excel-table tbody tr")

    # Table column classes (for row data reading)
    COL_TAX_RATE_NAME = ("css", "td.mat-column-tax_rate_name")

    # Action buttons per row — accessed via 3-dot menu (more_vert)
    # The ERP uses a single ⋮ menu per row instead of separate action columns.
    # Use _click_action_button(row_index, action_name) to click View/Edit/History.

    # Tax Rate Name cell per row
    def _name_cell(self, row_index):
        return ("xpath", f"(//td[contains(@class,'mat-column-tax_rate_name')])[{row_index + 1}]")

    # Search toggle button
    SEARCH_BUTTON = ("css", "button.search-btn")

    # Pagination
    PAGER = ("css", "mat-paginator")
    NEXT_PAGE_BTN = ("css", "mat-paginator button[aria-label='Next page']")

    # ================================================================
    # LOCATORS — Sub-Table (inside form popup, "Define Tax Rate Details" tab)
    # ================================================================

    # Tab to switch to sub-table view
    SUB_TABLE_TAB = ("xpath", "//div[contains(@class,'big-model')]//div[contains(.,'Define Tax Rate Details')]")

    # Sub-table container
    SUB_TABLE = ("css", "div.edit_pop_up table.mat-table")
    SUB_TABLE_BODY_ROWS = ("css", "div.edit_pop_up table.mat-table tbody tr")

    # Add row button in sub-table
    ADD_SUB_TABLE_ROW_BUTTON = ("xpath", "//div[contains(@class,'big-model')]//button[contains(.,'Add')]")

    # Tax Rate input in sub-table (input[name='Tax Rate'])
    SUB_TABLE_TAX_RATE_INPUT = ("css", "div.edit_pop_up input[name='Tax Rate']")

    # ================================================================
    # LOCATORS — History Popup
    # ================================================================

    HISTORY_POPUP = ("css", ".popup-overlay")
    HISTORY_TITLE = ("xpath", "//h3[contains(.,'Tax Rate History')]")
    HISTORY_CANCEL_BTN = ("xpath", "//div[contains(@class,'popup')]//button[contains(.,'Cancel')]")
    HISTORY_TABLE = ("css", ".edit_pop_up table")
    HISTORY_TABLE_ROWS = ("css", ".edit_pop_up table tbody tr")
    HISTORY_NO_DATA = ("css", ".edit_pop_up img[alt='No Data Available']")
    HISTORY_POPUP_CONTENT = ("css", ".popup-content")
    HISTORY_DYNAMIC_CONTAINER = ("css", "app-dynamic-history")

    # ================================================================
    # NAVIGATION
    # ================================================================

    def navigate_to_page(self):
        """Navigate directly to the Tax Rate screen via URL."""
        log.info("Navigating to Tax Rate screen")
        self.driver.get("https://rhythmerp.algorhythms.in/#/dynamic-screens/Tax%20Rate")
        self._wait_for_page_ready()
        log.info("Arrived at Tax Rate page")

    def hard_refresh(self):
        """Hard refresh the current page and wait for it to be ready."""
        log.info("Hard refreshing Tax Rate page")
        self.driver.refresh()
        self._wait_for_page_ready()
        log.info("Page refreshed and ready")

    def _wait_for_page_ready(self):
        """Wait for the Tax Rate page table to appear."""
        try:
            WebDriverWait(self.driver, 15).until(
                lambda d: d.find_elements("css selector", "table#excel-table")
            )
            log.info("Page ready (table found)")
        except Exception:
            log.warning("Page ready check timed out")

    def _cleanup(self):
        """Hard refresh for test cleanup — single refresh resets all state."""
        self.hard_refresh()

    def wait_for_table_load(self, timeout=15):
        """Wait for the main listing table to load."""
        try:
            self.wait_for_visible(self.TABLE, timeout=timeout)
            log.info("Tax Rate table loaded")
        except Exception:
            log.warning("Tax Rate table did not load within timeout")
            self.take_screenshot("tax_rate_table_load_failed")

    def is_page_loaded(self, timeout=5):
        """Check if the Tax Rate page is loaded with table visible."""
        return self.is_displayed(self.TABLE, timeout=timeout)

    # ================================================================
    # CLEANUP — Force close all popups, overlays, alerts
    # ================================================================

    def force_cleanup_all(self):
        """Force-close any stuck SweetAlert, form popup, history popup, and overlays.

        CRITICAL: NEVER remove .cdk-overlay-container or all .cdk-overlay-pane.
        Only remove .cdk-overlay-backdrop (the dark sheet). Removing the
        container/pane kills Angular's overlay rendering engine permanently.
        """
        try:
            # 1. Dismiss any SweetAlert popup via JS
            try:
                self.driver.execute_script(
                    "var btn = document.querySelector('.swal2-confirm');"
                    "if (btn) btn.click();"
                )
            except Exception:
                pass

            # 2. Remove ONLY CDK overlay backdrops (NEVER containers or panes)
            try:
                self.driver.execute_script(
                    "document.querySelectorAll('.cdk-overlay-backdrop').forEach(function(el) { el.remove(); });"
                )
            except Exception:
                pass

            # 3. Close form popup if open (via Cancel JS click)
            try:
                self.driver.execute_script(
                    "var footers = document.querySelectorAll('.popup-footer');"
                    "for (var i = 0; i < footers.length; i++) {"
                    "  var buttons = footers[i].querySelectorAll('button');"
                    "  for (var j = 0; j < buttons.length; j++) {"
                    "    if (buttons[j].textContent.indexOf('Cancel') !== -1) {"
                    "      buttons[j].click(); break;"
                    "    }"
                    "  }"
                    "}"
                )
            except Exception:
                pass

            # 4. Send Escape to dismiss any remaining overlays
            try:
                from selenium.webdriver.common.action_chains import ActionChains
                ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
            except Exception:
                pass

        except Exception as e:
            log.warning(f"Cleanup completed with warning: {e}")

    def _force_close_panels(self):
        """Remove open CDK overlay panels/backdrops safely.

        CRITICAL: Only removes .erp-action-menu panels and non-SweetAlert/non-history .cdk-overlay-pane.
        NEVER removes all .cdk-overlay-pane — that kills the history popup.
        """
        try:
            self.driver.execute_script(
                "document.querySelectorAll('.erp-action-menu').forEach(function(el) { el.remove(); });"
                "document.querySelectorAll('.cdk-overlay-backdrop').forEach(function(el) { el.remove(); });"
                "document.querySelectorAll('.cdk-overlay-pane').forEach(function(el) {"
                "  if (!el.querySelector('.swal2-popup') && !el.querySelector('app-dynamic-history')) el.remove();"
                "});"
            )
        except Exception:
            pass

    # ================================================================
    # JS HELPERS
    # ================================================================

    def _js_click(self, locator):
        """Click an element using JavaScript — bypasses CDK overlay blocking."""
        element = self.find_element(locator)
        self.driver.execute_script("arguments[0].click();", element)

    def _js_click_element(self, element):
        """Click a WebElement using JavaScript."""
        self.driver.execute_script("arguments[0].click();", element)

    def _set_text_field(self, locator, value):
        """Set text field value using atomic JavaScript for Angular reactivity."""
        try:
            self.driver.execute_script(
                "var input = arguments[0];"
                "var nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;"
                "nativeSetter.call(input, arguments[1]);"
                "input.dispatchEvent(new Event('input', {bubbles: true}));"
                "input.dispatchEvent(new Event('change', {bubbles: true}));"
            , self.find_element(locator), value)
        except Exception:
            self.type_text(locator, value, clear_first=True)

    def _set_date_field(self, locator, value):
        """Set date picker value via JavaScript.

        Date fields have name=null (TR-04) and use mat-datepicker.
        We set the value via JS and dispatch change events for Angular.
        """
        try:
            self.driver.execute_script(
                "var input = arguments[0];"
                "var nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;"
                "nativeSetter.call(input, arguments[1]);"
                "input.dispatchEvent(new Event('input', {bubbles: true}));"
                "input.dispatchEvent(new Event('change', {bubbles: true}));"
                "input.dispatchEvent(new Event('blur', {bubbles: true}));"
            , self.find_element(locator), value)
            log.info(f"Set date field to: {value}")
        except Exception as e:
            log.warning(f"Date field JS set failed: {e}")
            try:
                element = self.find_element(locator)
                element.clear()
                element.send_keys(value)
            except Exception:
                pass

    def _blur_active_element(self):
        """Click on body to blur any active input (helps dropdown focus issues)."""
        try:
            self.driver.execute_script("document.body.click();")
        except Exception:
            pass

    def _log_overlay_state(self):
        """Diagnostic: log current CDK overlay state."""
        try:
            panes = self.driver.find_elements(By.CSS_SELECTOR, ".cdk-overlay-pane")
            log.info(f"[DIAG] {len(panes)} overlay pane(s) in DOM")
            backdrops = self.driver.find_elements(By.CSS_SELECTOR, ".cdk-overlay-backdrop")
            log.info(f"[DIAG] {len(backdrops)} overlay backdrop(s) in DOM")
        except Exception as diag_err:
            log.info(f"[DIAG] Overlay check failed: {diag_err}")

    # ================================================================
    # ADD FORM — Open / Close
    # ================================================================

    def open_add_form(self):
        """Click the Add (+) button to open the create form popup.

        Uses JS click because the button is often overlapped
        and never becomes Selenium-clickable.
        """
        log.info("Opening Add form")
        js_click_add = (
            "var btn = document.querySelector('button.erp-add-btn');"
            "if (!btn) {"
            "  var icons = document.querySelectorAll('app-custom-header mat-icon, app-custom-header i.material-icons');"
            "  for (var i = 0; i < icons.length; i++) {"
            "    if (icons[i].textContent.trim() === 'add') {"
            "      btn = icons[i].closest('button'); break;"
            "    }"
            "  }"
            "}"
            "if (!btn) { throw new Error('Add button not found in DOM'); }"
            "btn.scrollIntoView({block:'center'});"
            "btn.click();"
            "return 'clicked';"
        )
        try:
            result = self.driver.execute_script(js_click_add)
            log.info("Add button clicked via JS: " + str(result))
        except Exception as e:
            log.warning("JS click failed, falling back: " + str(e))
            try:
                self.click(self.ADD_BUTTON)
            except Exception:
                add_btn = ("xpath", "//button[mat-icon[text()='add']]")
                self.click(add_btn)
        self.wait_for_form_to_open()
        log.info("Add form opened")

    def close_form_via_cancel(self):
        """Click the Cancel button to close the form popup via JS."""
        log.info("Closing form via Cancel button")
        try:
            self.driver.execute_script(
                "var footers = document.querySelectorAll('.popup-footer');"
                "for (var i = 0; i < footers.length; i++) {"
                "  var buttons = footers[i].querySelectorAll('button');"
                "  for (var j = 0; j < buttons.length; j++) {"
                "    if (buttons[j].textContent.indexOf('Cancel') !== -1) {"
                "      buttons[j].click(); return 'clicked';"
                "    }"
                "  }"
                "}"
                "return 'not found';"
            )
        except Exception:
            self.click(self.CANCEL_BUTTON)
        self.wait_for_form_to_close()

    def cancel(self):
        """Alias for close_form_via_cancel."""
        self.close_form_via_cancel()

    # ================================================================
    # FORM — State Checks
    # ================================================================

    def is_form_open(self):
        """Check if the Tax Rate form popup is currently visible (fast JS check)."""
        try:
            return self.driver.execute_script(
                "var el = document.querySelector('div.edit_pop_up'); "
                "return el && el.offsetParent !== null;"
            )
        except Exception:
            return False

    def is_view_mode(self):
        """Check if the form is in View mode (no Submit/Update/Create Version button)."""
        try:
            has_submit = self.driver.execute_script(
                "var btns = document.querySelectorAll('.popup-footer button'); "
                "for (var i = 0; i < btns.length; i++) { "
                "  var t = btns[i].textContent.trim(); "
                "  if (t === 'Submit' || t === 'Update' || t === 'Create Version') return true; "
                "} "
                "return false;"
            )
            return not has_submit
        except Exception:
            return True

    def wait_for_form_to_open(self, timeout=10):
        """Wait until the form popup appears (fast JS poll)."""
        end_time = time.monotonic() + timeout
        while time.monotonic() < end_time:
            try:
                visible = self.driver.execute_script(
                    "var el = document.querySelector('div.edit_pop_up'); "
                    "return el && el.offsetParent !== null;"
                )
                if visible:
                    log.info("Form popup is now open")
                    return
            except Exception:
                pass
            time.sleep(0.2)
        log.error("Form popup did not open within timeout")
        self.take_screenshot("tax_rate_form_not_opened")
        raise Exception("Form popup did not open within " + str(timeout) + "s")

    def wait_for_form_to_close(self, timeout=10):
        """Wait until the form popup disappears (fast JS poll)."""
        end_time = time.monotonic() + timeout
        while time.monotonic() < end_time:
            try:
                visible = self.driver.execute_script(
                    "var el = document.querySelector('div.edit_pop_up'); "
                    "return el && el.offsetParent !== null;"
                )
                if not visible:
                    log.info("Form popup closed")
                    return
            except Exception:
                return
            time.sleep(0.2)
        log.warning("Form popup still visible after timeout")

    def get_form_title(self):
        """Get the form popup header title."""
        try:
            return self.get_text(self.FORM_HEADER_TITLE)
        except Exception:
            return ""

    # ================================================================
    # HEADER FIELD FILL — Individual methods
    # ================================================================

    def fill_tax_rate_name(self, name):
        """Type Tax Rate Name into the text input field."""
        if name:
            self._set_text_field(self.TAX_RATE_NAME_INPUT, name)
            log.info(f"Tax Rate Name set to: {name}")

    def select_tax_type(self, tax_type):
        """Select Tax Type from mat-select dropdown via JS clicks.

        Args:
            tax_type: The tax type to select (e.g., 'GST').

        Returns:
            True if selection succeeded, False otherwise.
        """
        if not tax_type:
            return True
        log.info(f"Selecting Tax Type: {tax_type}")
        try:
            self._force_close_panels()
            # JS click the mat-select trigger
            self.driver.execute_script(
                "var labels = document.querySelectorAll('mat-label');"
                "for (var i = 0; i < labels.length; i++) {"
                "  if (labels[i].textContent.indexOf('Tax Type') !== -1) {"
                "    var sel = labels[i].closest('mat-form-field').querySelector('mat-select');"
                "    if (sel) { sel.click(); return 'opened'; }"
                "  }"
                "}"
                "throw new Error('Tax Type mat-select not found');"
            )
            # Fast poll for option to appear
            end_time = time.monotonic() + 5
            while time.monotonic() < end_time:
                try:
                    clicked = self.driver.execute_script(
                        "var opts = document.querySelectorAll('mat-option span');"
                        "for (var i = 0; i < opts.length; i++) {"
                        "  if (opts[i].textContent.trim() === arguments[0]) {"
                        "    opts[i].closest('mat-option').click(); return 'clicked';"
                        "  }"
                        "}"
                        "return '';"
                    , tax_type)
                    if clicked:
                        break
                except Exception:
                    pass
                time.sleep(0.1)
            else:
                log.warning(f"Tax Type option '{tax_type}' not found in dropdown")
                self._force_close_panels()
                return False
            self._force_close_panels()
            log.info(f"Tax Type set to: {tax_type}")
            return True
        except Exception as e:
            log.warning(f"Tax Type selection failed: {e}")
            self._force_close_panels()
            return False

    def select_tax_authority(self, authority):
        """Select Tax Authority from mat-select dropdown via JS clicks."""
        if not authority:
            return True
        log.info(f"Selecting Tax Authority: {authority}")
        try:
            self._force_close_panels()
            # JS click the mat-select trigger
            self.driver.execute_script(
                "var labels = document.querySelectorAll('mat-label');"
                "for (var i = 0; i < labels.length; i++) {"
                "  if (labels[i].textContent.indexOf('Tax Authority') !== -1) {"
                "    var sel = labels[i].closest('mat-form-field').querySelector('mat-select');"
                "    if (sel) { sel.click(); return 'opened'; }"
                "  }"
                "}"
                "throw new Error('Tax Authority mat-select not found');"
            )
            # Fast poll for option to appear
            end_time = time.monotonic() + 5
            while time.monotonic() < end_time:
                try:
                    clicked = self.driver.execute_script(
                        "var opts = document.querySelectorAll('mat-option span');"
                        "for (var i = 0; i < opts.length; i++) {"
                        "  if (opts[i].textContent.trim().indexOf(arguments[0]) !== -1) {"
                        "    opts[i].closest('mat-option').click(); return 'clicked';"
                        "  }"
                        "}"
                        "return '';"
                    , authority)
                    if clicked:
                        break
                except Exception:
                    pass
                time.sleep(0.1)
            else:
                log.warning(f"Tax Authority option '{authority}' not found in dropdown")
                self._force_close_panels()
                return False
            self._force_close_panels()
            log.info(f"Tax Authority set to: {authority}")
            return True
        except Exception as e:
            log.warning(f"Tax Authority selection failed: {e}")
            self._force_close_panels()
            return False

    def fill_from_date(self, date_str):
        """Set From Date in the date picker.

        Args:
            date_str: Date in DD/MM/YYYY format (e.g., '14/05/2026').
        """
        if date_str:
            self._set_date_field(self.FROM_DATE_INPUT, date_str)
            log.info(f"From Date set to: {date_str}")

    def fill_to_date(self, date_str):
        """Set To Date in the date picker.

        Args:
            date_str: Date in DD/MM/YYYY format. Empty string = server default 2099-12-30.
        """
        if date_str:
            self._set_date_field(self.TO_DATE_INPUT, date_str)
            log.info(f"To Date set to: {date_str}")

    def fill_revision_status(self, status):
        """Type Revision Status into the text input field."""
        if status:
            self._set_text_field(self.REVISION_STATUS_INPUT, status)
            log.info(f"Revision Status set to: {status}")

    # ================================================================
    # HEADER FIELD FILL — Combined (fill_all_fields)
    # ================================================================

    def fill_all_fields(self, data):
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
        """Clear all header text input fields."""
        log.info("Clearing header fields")
        try:
            self.clear_field(self.TAX_RATE_NAME_INPUT)
        except Exception:
            pass
        try:
            self.clear_field(self.REVISION_STATUS_INPUT)
        except Exception:
            pass

    # ================================================================
    # SUB-TABLE — Row Operations
    # ================================================================

    def _switch_to_sub_table_tab(self):
        """Click 'Define Tax Rate Details' tab to reveal sub-table via JS.

        Uses targeted selectors — avoids clicking parent container divs that
        contain the text but are not the actual tab element.
        """
        try:
            result = self.driver.execute_script(
                "var tabs = document.querySelectorAll('.big-model .tab-name, .big-model .stepper-title, "
                ".big-model div[role=\"tab\"], .big-model .tab-title, .big-model .nav-link');"
                "for (var i = 0; i < tabs.length; i++) {"
                "  if (tabs[i].textContent.indexOf('Define Tax Rate Details') !== -1) {"
                "    tabs[i].click(); return 'clicked';"
                "  }"
                "}"
                "var spans = document.querySelectorAll('.big-model .stepper-title span, .big-model .tab-name span, .big-model .nav-link span');"
                "for (var i = 0; i < spans.length; i++) {"
                "  if (spans[i].textContent.trim() === 'Define Tax Rate Details') {"
                "    spans[i].click(); return 'clicked_span';"
                "  }"
                "}"
                "var navLinks = document.querySelectorAll('.big-model a.nav-link, .big-model .nav-item a');"
                "for (var i = 0; i < navLinks.length; i++) {"
                "  if (navLinks[i].textContent.indexOf('Define Tax Rate Details') !== -1) {"
                "    navLinks[i].click(); return 'clicked_navlink';"
                "  }"
                "}"
                "var all = document.querySelectorAll('.big-model .tab-name, .big-model .stepper-title, .big-model [role=\"tab\"], .big-model .nav-item, .big-model .nav-link, .big-model .tab-item');"
                "for (var i = 0; i < all.length; i++) {"
                "  if (all[i].textContent.trim() === 'Define Tax Rate Details') {"
                "    all[i].click(); return 'clicked_exact_fallback';"
                "  }"
                "}"
                "var tabBtns = document.querySelectorAll('.big-model .nav-item, .big-model .tab-item, .big-model button[role=\"tab\"]');"
                "if (tabBtns.length >= 2) { tabBtns[1].click(); return 'clicked_second_tab'; }"
                "return 'not_found';"
            )
            log.info("Sub-table tab switch: " + str(result))
            # Fast poll for sub-table to appear
            end = time.monotonic() + 5
            while time.monotonic() < end:
                try:
                    has_rows = self.driver.execute_script(
                        "var rows = document.querySelectorAll('.edit_pop_up table tbody tr, .big-model table tbody tr');"
                        "return rows.length > 0;"
                    )
                    if has_rows:
                        break
                except Exception:
                    pass
                time.sleep(0.1)
        except Exception as e:
            log.warning("Sub-table tab switch failed: " + str(e))

    def _get_sub_table_rows(self):
        """Get all sub-table row WebElements.

        Tries multiple CSS selectors to handle different sub-table DOM structures.
        """
        selectors = [
            "div.edit_pop_up table.mat-table tbody tr",
            "div.edit_pop_up table tbody tr",
            "div.big-model table tbody tr",
        ]
        for sel in selectors:
            try:
                rows = self.driver.find_elements(By.CSS_SELECTOR, sel)
                if rows:
                    return rows
            except Exception:
                pass
        return []

    def _get_sub_table_row_count(self):
        """Get the number of sub-table rows."""
        rows = self._get_sub_table_rows()
        count = len(rows)
        log.info(f"Sub-table has {count} row(s)")
        return count

    def add_sub_table_row(self):
        """Click the Add button to add a new empty row to the sub-table via JS.

        Tracks row count BEFORE click and waits for it to increase by 1.
        This avoids the false-positive where count > 0 is always true
        due to the pre-created empty row.
        """
        log.info("Adding new sub-table row")
        try:
            # Get current row count BEFORE clicking Add
            count_before = self.driver.execute_script(
                "var rows = document.querySelectorAll('.edit_pop_up table tbody tr, .big-model table tbody tr');"
                "return rows.length;"
            ) or 0
            log.info("Row count before Add: " + str(count_before))

            self.driver.execute_script(
                "var btns = document.querySelectorAll('.big-model button');"
                "for (var i = 0; i < btns.length; i++) {"
                "  if (btns[i].textContent.trim() === 'Add') {"
                "    btns[i].click(); return 'clicked';"
                "  }"
                "}"
                "var addBtn = document.querySelector('.big-model button.erp-add-btn, .big-model .add-row-btn');"
                "if (addBtn) { addBtn.click(); return 'clicked_fallback'; }"
                "return 'not_found';"
            )
            # Fast poll for the new row to appear (count must increase)
            end = time.monotonic() + 5
            while time.monotonic() < end:
                try:
                    count_now = self.driver.execute_script(
                        "var rows = document.querySelectorAll('.edit_pop_up table tbody tr, .big-model table tbody tr');"
                        "return rows.length;"
                    ) or 0
                    if count_now > count_before:
                        break
                except Exception:
                    pass
                time.sleep(0.1)
            else:
                log.warning("Row count did not increase after clicking Add")
            log.info("New sub-table row added")
        except Exception as e:
            log.warning(f"Failed to add sub-table row: {e}")
            self.take_screenshot("sub_table_add_row_failed")

    def delete_sub_table_row(self, row_index=-1):
        """Delete a sub-table row by clicking its ACTION delete button.

        Args:
            row_index: Row index to delete. Default -1 = last row (safest).
        """
        rows = self._get_sub_table_rows()
        if not rows:
            log.warning("No sub-table rows to delete")
            return

        if row_index == -1:
            row_index = len(rows) - 1

        try:
            row = rows[row_index]
            delete_btn = row.find_element(By.CSS_SELECTOR, "td.mat-column-action button")
            self._js_click_element(delete_btn)
            log.info(f"Deleted sub-table row {row_index}")
        except Exception as e:
            log.warning(f"Failed to delete sub-table row {row_index}: {e}")

    def select_hsn_number(self, hsn, row_index=0):
        """Select HSN Number from the mat-select dropdown in a sub-table row via pure JS.

        Uses pure JS for the entire operation — avoids stale Selenium WebElements
        that become invalid after the form popup DOM changes.

        Args:
            hsn: HSN Number string (e.g., '997212').
            row_index: 0-based row index in the sub-table.

        Returns:
            True if selection succeeded, False otherwise.
        """
        if not hsn:
            return True

        log.info(f"Selecting HSN Number '{hsn}' in row {row_index}")
        self._force_close_panels()

        # Fast poll for sub-table row to be available (pure JS)
        end_time = time.monotonic() + 5
        while time.monotonic() < end_time:
            try:
                row_count = self.driver.execute_script(
                    "var rows = document.querySelectorAll('.edit_pop_up table tbody tr, .big-model table tbody tr');"
                    "return rows.length;"
                )
                if row_count and row_count > row_index:
                    break
            except Exception:
                pass
            time.sleep(0.1)
        else:
            log.warning(f"Sub-table row {row_index} not available")
            return False

        try:
            # JS click the mat-select in the sub-table row (pure JS)
            result = self.driver.execute_script(
                "var rows = document.querySelectorAll('.edit_pop_up table tbody tr, .big-model table tbody tr');"
                "var idx = arguments[0];"
                "if (idx >= rows.length) { throw new Error('Row ' + idx + ' not found'); }"
                "var sel = rows[idx].querySelector('mat-select');"
                "if (!sel) { throw new Error('mat-select not found in row ' + idx); }"
                "sel.click();"
                "return 'opened';"
            , row_index)
            log.info("HSN select opened: " + str(result))

            # Fast poll for option to appear
            end_time = time.monotonic() + 5
            while time.monotonic() < end_time:
                try:
                    clicked = self.driver.execute_script(
                        "var opts = document.querySelectorAll('mat-option span');"
                        "for (var i = 0; i < opts.length; i++) {"
                        "  if (opts[i].textContent.trim() === arguments[0]) {"
                        "    opts[i].closest('mat-option').click(); return 'clicked';"
                        "  }"
                        "}"
                        "return '';"
                    , hsn)
                    if clicked:
                        break
                except Exception:
                    pass
                time.sleep(0.1)
            else:
                log.warning(f"HSN option '{hsn}' not found in dropdown")
                self._force_close_panels()
                return False

            self._force_close_panels()
            log.info(f"HSN Number set to: {hsn}")
            return True
        except Exception as e:
            log.warning(f"HSN Number selection failed: {e}")
            self._force_close_panels()
            return False

    def fill_sub_table_tax_rate(self, rate, row_index=0):
        """Set Tax Rate value in a sub-table row via pure JS.

        Uses pure JS for row finding — avoids stale Selenium WebElements.

        Args:
            rate: Numeric tax rate value (e.g., 18.0, -5.0, 0).
            row_index: 0-based row index in the sub-table.
        """
        log.info(f"Setting Tax Rate to {rate} in row {row_index}")
        # Wait briefly for the row to exist
        end = time.monotonic() + 3
        while time.monotonic() < end:
            row_count = self.driver.execute_script(
                "var rows = document.querySelectorAll('.edit_pop_up table tbody tr, .big-model table tbody tr');"
                "return rows.length;"
            ) or 0
            if row_count > row_index:
                break
            time.sleep(0.1)

        try:
            result = self.driver.execute_script(
                "var rows = document.querySelectorAll('.edit_pop_up table tbody tr, .big-model table tbody tr');"
                "var idx = arguments[0];"
                "if (idx >= rows.length) return 'row_not_found';"
                "var input = rows[idx].querySelector('input[name=\"Tax Rate\"]');"
                "if (!input) return 'input_not_found';"
                "var nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;"
                "nativeSetter.call(input, '');"
                "input.dispatchEvent(new Event('input', {bubbles: true}));"
                "nativeSetter.call(input, String(arguments[1]));"
                "input.dispatchEvent(new Event('input', {bubbles: true}));"
                "input.dispatchEvent(new Event('change', {bubbles: true}));"
                "return 'set';"
            , row_index, rate)
            log.info(f"Tax Rate set to: {rate} (result: {result})")
        except Exception as e:
            log.warning(f"Failed to set Tax Rate: {e}")

    def fill_sub_table_row(self, row_data, row_index=0):
        """Fill HSN Number and Tax Rate for a specific sub-table row.

        Args:
            row_data: Dict with keys 'hsn_number' and 'tax_rate'.
            row_index: 0-based row index in the sub-table.

        Returns:
            True if both fields were filled successfully.
        """
        hsn = row_data.get("hsn_number", "")
        rate = row_data.get("tax_rate", "")

        hsn_ok = self.select_hsn_number(hsn, row_index)
        if hsn_ok:
            self._force_close_panels()
            self.fill_sub_table_tax_rate(rate, row_index)

        return hsn_ok

    def fill_sub_table(self, sub_table_rows):
        """Fill multiple sub-table rows.

        Sub-table starts with 1 empty row. For additional rows,
        clicks Add first, then fills top-down (index 0 first).

        Uses pure JS for row counting — avoids stale Selenium WebElements.

        Args:
            sub_table_rows: List of dicts, each with 'hsn_number' and 'tax_rate'.

        Returns:
            True if all rows were filled successfully.
        """
        if not sub_table_rows:
            log.info("No sub-table rows to fill")
            return True

        # Switch to sub-table tab
        self._switch_to_sub_table_tab()

        # Get current row count via JS (avoid stale Selenium elements)
        current_rows = self.driver.execute_script(
            "var rows = document.querySelectorAll('.edit_pop_up table tbody tr, .big-model table tbody tr');"
            "return rows.length;"
        ) or 0
        needed = len(sub_table_rows)
        log.info(f"Sub-table: {current_rows} existing rows, need {needed}")

        for _ in range(max(0, needed - current_rows)):
            self.add_sub_table_row()

        # Fill rows top-down (index 0 first)
        all_ok = True
        for i in range(needed):
            ok = self.fill_sub_table_row(sub_table_rows[i], row_index=i)
            if not ok:
                all_ok = False
                log.warning(f"Sub-table row {i} fill failed")

        return all_ok

    # ================================================================
    # FORM — Submit / Create Version
    # ================================================================

    def submit(self):
        """Click the Submit button (Create mode) via JS click."""
        log.info("Clicking Submit button")
        self._force_close_panels()
        js = (
            "var footers = document.querySelectorAll('.popup-footer');"
            "for (var i = 0; i < footers.length; i++) {"
            "  var buttons = footers[i].querySelectorAll('button');"
            "  for (var j = 0; j < buttons.length; j++) {"
            "    if (buttons[j].textContent.trim().indexOf('Submit') !== -1) {"
            "      buttons[j].click(); return 'clicked_Submit';"
            "    }"
            "  }"
            "}"
            "throw new Error('Submit button not found in popup footer');"
        )
        try:
            result = self.driver.execute_script(js)
            log.info("JS click Submit: " + str(result))
        except Exception as e:
            log.warning("JS click Submit failed: " + str(e))
            self.click(self.SUBMIT_BUTTON)

    def click_create_version(self):
        """Click the Create Version button (Version mode)."""
        log.step(4, "Clicking Create Version button")
        self._force_close_panels()
        self.click(self.CREATE_VERSION_BUTTON)

    # ================================================================
    # CREATE RECORD — Full flow with retry logic
    # ================================================================

    def create_record(self, data, max_cycles=2):
        """Create a new Tax Rate record.

        Opens form, fills header + sub-table, clicks Submit, and handles
        the result (success or validation failure).

        IMPORTANT: No success SweetAlert2 (TR-03). Form closes silently on success.

        Args:
            data: Dict with keys:
                  "header" — dict of header fields
                  "sub_table_rows" — list of dicts with 'hsn_number' and 'tax_rate'
            max_cycles: Max retry cycles for dropdown failures.

        Returns:
            dict with keys:
                "status": "success" or "failed"
                "error": error message (empty on success)
        """
        header = data.get("header", {})
        sub_rows = data.get("sub_table_rows", [])
        name = header.get("tax_rate_name", "Unknown")

        for cycle in range(1, max_cycles + 1):
            log.info(f"Creating Tax Rate: {name} (cycle {cycle}/{max_cycles})")

            try:
                # Only refresh on retry (cycle > 1); first cycle uses fixture's navigation
                if cycle > 1:
                    self.hard_refresh()

                # Open Add form
                self.open_add_form()

                # Fill header fields (dropdowns first, then text, then dates)
                self.fill_all_fields(header)

                # Fill sub-table rows
                if sub_rows:
                    self.fill_sub_table(sub_rows)

                # Click Submit via JS
                self.submit()

                # Fast poll for result (form close = success)
                end_time = time.monotonic() + 6
                while time.monotonic() < end_time:
                    # Check for validation alert first (ultra-fast JS check)
                    try:
                        result = self.driver.execute_script(
                            "var warn = document.querySelector('.swal2-popup.swal2-icon-warning');"
                            "if (warn && warn.offsetParent !== null) {"
                            "  var title = document.querySelector('.swal2-title');"
                            "  var btn = document.querySelector('.swal2-confirm');"
                            "  if (btn) btn.click();"
                            "  return title ? title.textContent.trim() : 'Validation Failed';"
                            "}"
                            "var el = document.querySelector('div.edit_pop_up');"
                            "if (el && el.offsetParent !== null) return 'form_open';"
                            "return 'form_closed';"
                        )
                        if result == 'form_closed':
                            log.info(f"Record '{name}' created successfully (silent success)")
                            return {"status": "success", "error": ""}
                        elif result not in ('form_open', ''):
                            # Validation alert detected — result is the alert title
                            log.info("Validation Failed: " + str(result))
                            try:
                                self.cancel()
                            except Exception:
                                pass
                            return {"status": "failed", "error": result}
                    except Exception:
                        pass

                    time.sleep(0.2)

                # Form still open, no alert — dropdown may have failed
                log.warning(f"Cycle {cycle}: Form still open, no alert — retrying")

            except Exception as e:
                log.warning(f"Cycle {cycle} error: {e}")

            # Cleanup before retry
            try:
                self.cancel()
            except Exception:
                pass
            time.sleep(0.3)

        return {"status": "failed", "error": f"Could not create record after {max_cycles} cycles"}

    # ================================================================
    # SWEET ALERT — Detection & Handling
    # ================================================================

    def is_validation_alert_present(self, timeout=5):
        """Check if SweetAlert 'Validation Failed' popup is visible (fast JS poll)."""
        end_time = time.monotonic() + timeout
        while time.monotonic() < end_time:
            try:
                visible = self.driver.execute_script(
                    "var el = document.querySelector('.swal2-popup.swal2-icon-warning, .swal2-popup.swal2-icon-error');"
                    "return el && el.offsetParent !== null;"
                )
                if visible:
                    log.info("Validation Failed alert detected")
                    return True
            except Exception:
                pass
            time.sleep(0.2)
        return False

    def get_sweetalert_title(self):
        """Get the title text from the current SweetAlert popup via JS."""
        try:
            return self.driver.execute_script(
                "var el = document.querySelector('.swal2-title');"
                "return el ? el.textContent.trim() : '';"
            ) or ""
        except Exception:
            return ""

    def get_sweetalert_message(self):
        """Get the message text from the current SweetAlert popup."""
        try:
            return self.get_text(self.SWEET_ALERT_MESSAGE)
        except Exception:
            return ""

    def accept_sweetalert(self):
        """Click OK/Confirm on the current SweetAlert popup via JS click."""
        log.info("Accepting SweetAlert (clicking OK via JS)")
        try:
            self.driver.execute_script(
                "var btn = document.querySelector('.swal2-confirm');"
                "if (btn) { btn.click(); return 'clicked'; }"
                "return 'not found';"
            )
            # Fast poll for SweetAlert to disappear
            end = time.monotonic() + 3
            while time.monotonic() < end:
                try:
                    visible = self.driver.execute_script(
                        "var el = document.querySelector('.swal2-popup');"
                        "return el && el.offsetParent !== null;"
                    )
                    if not visible:
                        break
                except Exception:
                    break
                time.sleep(0.1)
        except Exception:
            log.warning("Could not click SweetAlert OK button")

    def dismiss_sweetalert(self):
        """Click Cancel on the current SweetAlert popup via JS."""
        try:
            self.driver.execute_script(
                "var btn = document.querySelector('.swal2-cancel');"
                "if (btn) { btn.click(); return 'clicked'; }"
                "return 'not found';"
            )
        except Exception:
            pass

    def is_any_alert_present(self, timeout=3):
        """Check if any SweetAlert popup is visible (fast JS poll)."""
        end_time = time.monotonic() + timeout
        while time.monotonic() < end_time:
            try:
                visible = self.driver.execute_script(
                    "var el = document.querySelector('.swal2-popup');"
                    "return el && el.offsetParent !== null;"
                )
                if visible:
                    return True
            except Exception:
                pass
            time.sleep(0.2)
        return False

    # ================================================================
    # TABLE — Read Data
    # ================================================================

    def get_table_row_count(self):
        """Get the number of data rows in the Tax Rate listing table."""
        try:
            rows = self.find_elements(self.TABLE_ROWS)
            count = len(rows)
            log.info(f"Table has {count} row(s)")
            return count
        except Exception:
            return 0

    def get_name_from_row(self, row_index):
        """Get the Tax Rate Name from a specific table row."""
        try:
            cell = self._name_cell(row_index)
            return self.get_text(cell).strip()
        except Exception:
            return ""

    def find_name_row_index(self, name):
        """Find a table row index by matching the Tax Rate Name column.

        Uses JS for fast scanning instead of iterating Selenium elements.

        Args:
            name: Tax Rate Name to search for.

        Returns:
            0-based row index, or -1 if not found.
        """
        # Fast JS scan first
        try:
            idx = self.driver.execute_script("""
                var table = document.querySelector('table#excel-table');
                if (!table) return -1;
                var rows = table.querySelectorAll('tbody tr');
                for (var i = 0; i < rows.length; i++) {
                    var cells = rows[i].querySelectorAll('td');
                    for (var j = 0; j < cells.length; j++) {
                        if (cells[j].textContent.trim() === arguments[0]) {
                            return i;
                        }
                    }
                }
                return -1;
            """, name.strip())
            if idx >= 0:
                log.info("Found '" + name + "' at row " + str(idx))
                return idx
        except Exception:
            pass

        # Fallback: Selenium scan
        row_count = self.get_table_row_count()
        for i in range(row_count):
            cell_name = self.get_name_from_row(i)
            if cell_name.strip().lower() == name.strip().lower():
                log.info("Found '" + name + "' at row " + str(i))
                return i
        log.warning("Record '" + name + "' not found in visible rows")
        return -1

    def is_name_in_table(self, name):
        """Check if a Tax Rate Name exists in the table.

        Searches current page. Does NOT paginate.

        Args:
            name: Tax Rate Name to search for.

        Returns:
            True if found, False otherwise.
        """
        return self.find_name_row_index(name) != -1

    def search_and_verify(self, name):
        """Search for a record and verify it exists.

        Combined search + verify for speed. Returns True if found.
        """
        log.info("Searching and verifying: " + name)
        self.search_record(name, exact=True)
        return self.is_name_in_table(name)

    def get_column_headers(self):
        """Get all column header texts from the Tax Rate table."""
        try:
            headers = self.driver.find_elements(
                By.CSS_SELECTOR, "table#excel-table thead th"
            )
            return [h.text.strip() for h in headers if h.text.strip()]
        except Exception:
            return []

    # ================================================================
    # TABLE — Action Buttons
    # ================================================================

    def _click_action_button(self, row_index, action_name):
        """Click an action button for a specific row via the 3-dot menu.

        Gold standard pattern (from UOM Conversion):
        Step 1: Click .erp-row-trigger on the target row.
        Step 2: Fast-poll for .mat-mdc-menu-panel.erp-action-menu to appear.
        Step 3: Click the menu item by .erp-menu-title label text.
        Step 4: Clean up ONLY the small menu overlay (not history/form popups).
        """
        action_label = action_name.capitalize()
        log.info("Clicking " + action_name + " via 3-dot menu for row " + str(row_index))

        # Step 1: Click ⋮ menu trigger on target row
        self.driver.execute_script(
            "var table = document.querySelector('table#excel-table');"
            "if (!table) { throw new Error('Table not found'); }"
            "var rows = table.querySelectorAll('tbody tr');"
            "var idx = arguments[0];"
            "if (idx >= rows.length) { throw new Error('Row ' + idx + ' out of range'); }"
            "var trigger = rows[idx].querySelector('.erp-row-trigger');"
            "if (trigger) { trigger.click(); return 'opened'; }"
            "throw new Error('.erp-row-trigger not found on row ' + idx);"
        , row_index)

        # Step 2: Fast-poll for CDK overlay menu (0.1s intervals, 3s timeout)
        end = time.monotonic() + 3
        while time.monotonic() < end:
            menu_open = self.driver.execute_script(
                "var panels = document.querySelectorAll('.mat-mdc-menu-panel.erp-action-menu');"
                "for (var i = 0; i < panels.length; i++) {"
                "  if (panels[i].offsetParent !== null) return true;"
                "}"
                "return false;"
            )
            if menu_open:
                break
            time.sleep(0.1)

        # Step 3: Click menu item by .erp-menu-title label text
        clicked = self.driver.execute_script(
            "var overlay = document.querySelector('.mat-mdc-menu-panel.erp-action-menu');"
            "if (!overlay) return false;"
            "var titles = overlay.querySelectorAll('.erp-menu-title');"
            "for (var i = 0; i < titles.length; i++) {"
            "  if (titles[i].textContent.trim() === arguments[0]) {"
            "    var item = titles[i].closest('.erp-menu-item');"
            "    if (item) { item.click(); return true; }"
            "    titles[i].click(); return true;"
            "  }"
            "}"
            "var allItems = overlay.querySelectorAll('button, span, div');"
            "for (var i = 0; i < allItems.length; i++) {"
            "  var text = allItems[i].textContent.trim();"
            "  if (text === arguments[0]) {"
            "    allItems[i].click(); return true;"
            "  }"
            "}"
            "var needle = arguments[0].toLowerCase();"
            "for (var i = 0; i < allItems.length; i++) {"
            "  var text = allItems[i].textContent.trim().toLowerCase();"
            "  if (text.indexOf(needle) !== -1) {"
            "    allItems[i].click(); return true;"
            "  }"
            "}"
            "return false;"
        , action_label)

        # Step 4: Wait for form or history popup to open
        if clicked:
            end_action = time.monotonic() + 5
            while time.monotonic() < end_action:
                if action_name.lower() == "history":
                    if self.is_history_popup_open(timeout=0):
                        break
                else:
                    if self.is_form_open():
                        break
                time.sleep(0.1)

        # Clean up lingering 3-dot menu overlay ONLY (not history/form popups)
        try:
            self.driver.execute_script(
                "var menus = document.querySelectorAll('.mat-mdc-menu-panel.erp-action-menu');"
                "for (var i = 0; i < menus.length; i++) {"
                "  var pane = menus[i].closest('.cdk-overlay-pane');"
                "  if (pane) pane.remove();"
                "}"
                "var backdrops = document.querySelectorAll('.cdk-overlay-backdrop');"
                "for (var i = 0; i < backdrops.length; i++) {"
                "  backdrops[i].remove();"
                "}"
            )
        except Exception:
            pass

        log.info("Action " + action_name + " click result: " + str(clicked))
        return clicked

    def click_view_on_row(self, row_index):
        """Click the View button on a specific table row via 3-dot menu."""
        log.info("Clicking View on row " + str(row_index))
        self._click_action_button(row_index, "View")
        self.wait_for_form_to_open()

    def click_version_on_row(self, row_index):
        """Click the Version button on a specific table row via 3-dot menu.

        Opens editable form with 'Create Version' button (TR-02).
        """
        log.info("Clicking Version on row " + str(row_index))
        self._click_action_button(row_index, "Version")
        self.wait_for_form_to_open()

    def click_history_on_row(self, row_index):
        """Click the History button on a specific table row via 3-dot menu."""
        log.info("Clicking History on row " + str(row_index))
        self._click_action_button(row_index, "History")
        self.wait_for_history_popup()

    def is_edit_button_disabled(self, row_index):
        """Check if the Edit menu item is disabled for a specific row via 3-dot menu.

        Opens the 3-dot menu, checks the Edit item's disabled state,
        then closes the menu without clicking Edit.

        Returns:
            True if Edit is disabled, False if enabled.
        """
        log.info("Checking if Edit is disabled on row " + str(row_index))

        # Open the 3-dot menu
        self.driver.execute_script(
            "var table = document.querySelector('table#excel-table');"
            "if (!table) { throw new Error('Table not found'); }"
            "var rows = table.querySelectorAll('tbody tr');"
            "var idx = arguments[0];"
            "if (idx >= rows.length) { throw new Error('Row index ' + idx + ' out of range'); }"
            "var trigger = rows[idx].querySelector('.erp-row-trigger');"
            "if (trigger) { trigger.click(); return 'opened'; }"
            "throw new Error('.erp-row-trigger not found on row ' + idx);"
        , row_index)

        # Fast-poll for menu to appear
        end = time.monotonic() + 3
        while time.monotonic() < end:
            menu_open = self.driver.execute_script(
                "var panels = document.querySelectorAll('.mat-mdc-menu-panel.erp-action-menu');"
                "for (var i = 0; i < panels.length; i++) {"
                "  if (panels[i].offsetParent !== null) return true;"
                "}"
                "return false;"
            )
            if menu_open:
                break
            time.sleep(0.1)

        # Check the Edit menu item disabled state via .erp-menu-title
        is_disabled = self.driver.execute_script(
            "var overlay = document.querySelector('.mat-mdc-menu-panel.erp-action-menu');"
            "if (!overlay) return true;"
            "var titles = overlay.querySelectorAll('.erp-menu-title');"
            "for (var i = 0; i < titles.length; i++) {"
            "  if (titles[i].textContent.trim() === 'Edit') {"
            "    var item = titles[i].closest('.erp-menu-item');"
            "    if (item) return item.disabled || item.classList.contains('disabled');"
            "    var btn = titles[i].closest('button');"
            "    if (btn) return btn.disabled;"
            "  }"
            "}"
            "return true;"
        )
        log.info("Edit button disabled: " + str(is_disabled))

        # Close the menu by removing the overlay
        try:
            self.driver.execute_script(
                "var menus = document.querySelectorAll('.mat-mdc-menu-panel.erp-action-menu');"
                "for (var i = 0; i < menus.length; i++) {"
                "  var pane = menus[i].closest('.cdk-overlay-pane');"
                "  if (pane) pane.remove();"
                "}"
                "var backdrops = document.querySelectorAll('.cdk-overlay-backdrop');"
                "for (var i = 0; i < backdrops.length; i++) {"
                "  backdrops[i].remove();"
                "}"
            )
        except Exception:
            pass

        return is_disabled

    # ================================================================
    # SEARCH
    # ================================================================

    def _do_js_search(self, text):
        """Execute search using atomic JavaScript — fast poll approach."""
        # Step 1: Click search button to toggle search input
        self.driver.execute_script(
            "var toggleBtn = document.querySelector('button.search-btn');"
            "if (toggleBtn) toggleBtn.click();"
        )
        # Step 2: Fast poll for search input to appear
        end_time = time.monotonic() + 3
        while time.monotonic() < end_time:
            try:
                found = self.driver.execute_script(
                    "var el = document.querySelector('input#erpSearchInput') || "
                    "document.querySelector('input[placeholder=\"Search\"]'); "
                    "return el && el.offsetParent !== null;"
                )
                if found:
                    break
            except Exception:
                pass
            time.sleep(0.1)

        # Step 3: Set search value and fire Angular events
        self.driver.execute_script(
            "var input = document.querySelector('input#erpSearchInput') || "
            "document.querySelector('input[placeholder=\"Search\"]');"
            "if (!input) { throw new Error('Search input not found'); }"
            "var nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;"
            "nativeSetter.call(input, '');"
            "input.dispatchEvent(new Event('input', {bubbles: true}));"
            "nativeSetter.call(input, arguments[0]);"
            "input.dispatchEvent(new Event('input', {bubbles: true}));"
            "input.dispatchEvent(new Event('change', {bubbles: true}));"
        , text)

        # Step 4: Click search button to submit
        self.driver.execute_script(
            "var btn = document.querySelector('button.search-btn');"
            "if (btn) btn.click();"
        )

        # Step 5: Fast poll for table to refresh
        end_time = time.monotonic() + 3
        while time.monotonic() < end_time:
            try:
                rows = self.driver.find_elements(By.CSS_SELECTOR, "table#excel-table tbody tr")
                if rows:
                    break
            except Exception:
                pass
            time.sleep(0.1)

    def search_record(self, name, exact=False):
        """Search for a record by Tax Rate Name.

        Args:
            name: Search text.
            exact: If True, verifies exact name match.

        Returns:
            True if matching results found, False otherwise.
        """
        log.info(f"Searching for: {name} (exact={exact})")
        try:
            self._do_js_search(name)
            row_count = self.get_table_row_count()

            if row_count == 0:
                log.info(f"Search returned 0 results for '{name}'")
                return False

            if not exact:
                log.info(f"Search found {row_count} result(s)")
                return True

            # Exact mode
            name_lower = name.strip().lower()
            for i in range(row_count):
                row_name = self.get_name_from_row(i).strip().lower()
                if row_name == name_lower:
                    log.info(f"Exact match at row {i}: '{row_name}'")
                    return True
            log.info(f"No exact match for '{name}'")
            return False

        except Exception as e:
            log.error(f"Search failed: {e}")
            return False

    def clear_search(self):
        """Clear the search filter — fast hard refresh."""
        log.info("Clearing search filter — hard refreshing")
        self.hard_refresh()

    # ================================================================
    # REFRESH
    # ================================================================

    def refresh_table(self):
        """Refresh the table — fast hard refresh."""
        log.info("Refreshing Tax Rate table...")
        self.hard_refresh()

    # ================================================================
    # HISTORY POPUP
    # ================================================================

    def wait_for_history_popup(self, timeout=10):
        """Wait for the history popup to open and load data (fast JS poll)."""
        end_time = time.monotonic() + timeout
        while time.monotonic() < end_time:
            try:
                visible = self.driver.execute_script(
                    "var el = document.querySelector('.popup-content') || "
                    "document.querySelector('app-dynamic-history'); "
                    "return el && el.offsetParent !== null;"
                )
                if visible:
                    log.info("History popup loaded")
                    return
            except Exception:
                pass
            time.sleep(0.2)
        log.warning("History popup did not load within timeout")
        self.take_screenshot("history_popup_not_loaded")

    def is_history_popup_open(self, timeout=5):
        """Check if the History popup is currently visible (fast JS poll)."""
        end_time = time.monotonic() + timeout
        while time.monotonic() < end_time:
            try:
                visible = self.driver.execute_script(
                    "var el = document.querySelector('app-dynamic-history') || "
                    "document.querySelector('.popup-content'); "
                    "return el && el.offsetParent !== null;"
                )
                if visible:
                    return True
            except Exception:
                pass
            if timeout <= 0:
                break
            time.sleep(0.2)
        return False

    def get_history_title(self):
        """Get the title text from the History popup header."""
        try:
            return self.get_text(self.HISTORY_TITLE)
        except Exception:
            return ""

    def get_history_row_count(self):
        """Get the number of rows in the history table."""
        try:
            rows = self.driver.find_elements(
                By.CSS_SELECTOR, ".edit_pop_up table tbody tr"
            )
            return len(rows)
        except Exception:
            return 0

    def close_history_popup(self):
        """Close the History popup via Cancel button using JS."""
        log.info("Closing History popup")
        try:
            self.driver.execute_script(
                "var footers = document.querySelectorAll('.popup-footer');"
                "for (var i = 0; i < footers.length; i++) {"
                "  var buttons = footers[i].querySelectorAll('button');"
                "  for (var j = 0; j < buttons.length; j++) {"
                "    if (buttons[j].textContent.indexOf('Cancel') !== -1) {"
                "      buttons[j].click(); return 'clicked';"
                "    }"
                "  }"
                "}"
                "return 'not found';"
            )
            # Fast poll for popup to close
            end = time.monotonic() + 3
            while time.monotonic() < end:
                try:
                    visible = self.driver.execute_script(
                        "var el = document.querySelector('app-dynamic-history') || "
                        "document.querySelector('.popup-content'); "
                        "return el && el.offsetParent !== null;"
                    )
                    if not visible:
                        break
                except Exception:
                    break
                time.sleep(0.1)
        except Exception:
            try:
                from selenium.webdriver.common.action_chains import ActionChains
                ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
            except Exception:
                pass
