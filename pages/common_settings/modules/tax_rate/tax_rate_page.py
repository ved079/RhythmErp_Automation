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

    # Action buttons per row — 4 buttons per row:
    #   View (eye), Edit (pencil), Version (folder), History (archive)
    def _view_button(self, row_index):
        return ("xpath", f"(//td[contains(@class,'mat-column-view')]//button)[{row_index + 1}]")

    def _edit_button(self, row_index):
        return ("xpath", f"(//td[contains(@class,'mat-column-edit')]//button)[{row_index + 1}]")

    def _version_button(self, row_index):
        return ("xpath", f"(//td[contains(@class,'mat-column-folder')]//button)[{row_index + 1}]")

    def _history_button(self, row_index):
        return ("xpath", f"(//td[contains(@class,'mat-column-archive')]//button)[{row_index + 1}]")

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

    # ================================================================
    # NAVIGATION
    # ================================================================

    def navigate_to_page(self):
        """Navigate directly to the Tax Rate screen via URL."""
        from pages.common_settings.modules.tax_rate.data.tax_rate_data import PAGE_URL
        log.info("Navigating to Tax Rate screen...")
        self.force_cleanup_all()
        self.navigate_to(PAGE_URL)
        self.wait_seconds(2)
        try:
            self.wait_for_visible(self.TABLE, timeout=15)
            log.info("Tax Rate screen loaded successfully")
        except Exception:
            log.warning("Table not found — page may still be loading or empty")
            self.take_screenshot("tax_rate_page_load")

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

        CRITICAL: NEVER remove .cdk-overlay-container or .cdk-overlay-pane.
        Only remove .cdk-overlay-backdrop (the dark sheet). Removing the
        container/pane kills Angular's overlay rendering engine permanently.
        """
        try:
            # 1. Dismiss any SweetAlert popup
            try:
                alerts = self.driver.find_elements(By.CSS_SELECTOR, ".swal2-popup")
                for alert in alerts:
                    if alert.is_displayed():
                        confirm = alert.find_element(By.CSS_SELECTOR, "button.swal2-confirm")
                        if confirm.is_displayed():
                            confirm.click()
                            log.info("Cleaned: Dismissed SweetAlert popup")
                            self.wait_seconds(0.5)
            except Exception:
                pass

            # 2. Remove ONLY CDK overlay backdrops (NEVER containers or panes)
            try:
                self.driver.execute_script("""
                    document.querySelectorAll('.cdk-overlay-backdrop').forEach(el => el.remove());
                """)
            except Exception:
                pass

            # 3. Close form popup if open (via Cancel or Escape)
            try:
                form = self.driver.find_element(By.CSS_SELECTOR, "div.edit_pop_up")
                if form.is_displayed():
                    cancel = form.find_element(
                        By.CSS_SELECTOR,
                        ".popup-footer button[type='button']"
                    )
                    if cancel.is_displayed():
                        cancel.click()
                        log.info("Cleaned: Closed stuck form popup")
                        self.wait_seconds(0.5)
                    else:
                        from selenium.webdriver.common.action_chains import ActionChains
                        ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
                        self.wait_seconds(0.5)
            except Exception:
                pass

            # 4. Close history popup if open
            try:
                hist = self.driver.find_element(By.CSS_SELECTOR, ".popup-overlay")
                if hist.is_displayed():
                    cancel = hist.find_element(
                        By.CSS_SELECTOR,
                        ".popup-footer button[type='button']"
                    )
                    if cancel.is_displayed():
                        cancel.click()
                        log.info("Cleaned: Closed stuck history popup")
                        self.wait_seconds(0.5)
            except Exception:
                pass

            # 5. Send Escape to dismiss any remaining lightweight overlays
            try:
                from selenium.webdriver.common.action_chains import ActionChains
                ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
            except Exception:
                pass

        except Exception as e:
            log.warning(f"Cleanup completed with warning: {e}")

    def _force_close_panels(self):
        """Close any open dropdown panels using Escape key.
        Only sends Escape if a CDK overlay backdrop actually exists.
        """
        try:
            has_overlay = self.driver.execute_script(
                "return document.querySelectorAll('.cdk-overlay-backdrop').length > 0;"
            )
            if has_overlay:
                from selenium.webdriver.common.action_chains import ActionChains
                ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
                self.wait_seconds(0.3)
                log.info("Force closed dropdown panel via Escape")
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
            self.driver.execute_script("""
                var input = arguments[0];
                var nativeSetter = Object.getOwnPropertyDescriptor(
                    window.HTMLInputElement.prototype, 'value'
                ).set;
                nativeSetter.call(input, arguments[1]);
                input.dispatchEvent(new Event('input', {bubbles: true}));
                input.dispatchEvent(new Event('change', {bubbles: true}));
            """, self.find_element(locator), value)
        except Exception:
            self.type_text(locator, value, clear_first=True)

    def _set_date_field(self, locator, value):
        """Set date picker value via JavaScript.

        Date fields have name=null (TR-04) and use mat-datepicker.
        We set the value via JS and dispatch change events for Angular.
        """
        try:
            self.driver.execute_script("""
                var input = arguments[0];
                var nativeSetter = Object.getOwnPropertyDescriptor(
                    window.HTMLInputElement.prototype, 'value'
                ).set;
                nativeSetter.call(input, arguments[1]);
                input.dispatchEvent(new Event('input', {bubbles: true}));
                input.dispatchEvent(new Event('change', {bubbles: true}));
                input.dispatchEvent(new Event('blur', {bubbles: true}));
            """, self.find_element(locator), value)
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
            self.wait_seconds(0.3)
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
        """Click the Add (+) button to open the create form popup."""
        log.step(1, "Opening Add form")
        self.force_cleanup_all()
        try:
            self.click(self.ADD_BUTTON)
        except Exception:
            add_btn = ("xpath", "//button[mat-icon[text()='add']]")
            self.click(add_btn)
        self.wait_for_form_to_open()
        log.info("Add form opened")

    def close_form_via_cancel(self):
        """Click the Cancel button to close the form popup."""
        log.info("Closing form via Cancel button")
        self.click(self.CANCEL_BUTTON)
        self.wait_for_form_to_close()

    def cancel(self):
        """Alias for close_form_via_cancel."""
        self.close_form_via_cancel()

    # ================================================================
    # FORM — State Checks
    # ================================================================

    def is_form_open(self):
        """Check if the Tax Rate form popup is currently visible."""
        return self.is_displayed(self.FORM_POPUP, timeout=5)

    def is_view_mode(self):
        """Check if the form is in View mode (no Submit/Update/Create Version button)."""
        try:
            submit_visible = self.is_displayed(self.SUBMIT_BUTTON, timeout=2)
            version_visible = self.is_displayed(self.CREATE_VERSION_BUTTON, timeout=2)
            return not submit_visible and not version_visible
        except Exception:
            return True

    def wait_for_form_to_open(self, timeout=10):
        """Wait until the form popup appears."""
        try:
            self.wait_for_visible(self.FORM_POPUP, timeout=timeout)
            log.info("Form popup is now open")
        except Exception:
            log.error("Form popup did not open within timeout")
            self.take_screenshot("tax_rate_form_not_opened")
            raise

    def wait_for_form_to_close(self, timeout=10):
        """Wait until the form popup disappears."""
        try:
            self.wait_for_invisible(self.FORM_POPUP, timeout=timeout)
            log.info("Form popup closed")
            self.wait_seconds(0.5)
        except Exception:
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
        """Select Tax Type from mat-select dropdown.

        Args:
            tax_type: The tax type to select (e.g., 'GST').

        Returns:
            True if selection succeeded, False otherwise.
        """
        if not tax_type:
            return True
        log.info(f"Selecting Tax Type: {tax_type}")
        try:
            self._blur_active_element()
            self.wait_seconds(0.3)
            self.click(self.TAX_TYPE_SELECT)
            self.wait_seconds(1)

            option = ("xpath", f"//mat-option//span[contains(text(),'{tax_type}')]")
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(option)
            )
            self.wait_seconds(0.3)
            self._js_click(option)
            self.wait_seconds(0.5)
            log.info(f"Tax Type set to: {tax_type}")
            return True
        except Exception as e:
            log.warning(f"Tax Type selection failed: {e}")
            self._log_overlay_state()
            return False

    def select_tax_authority(self, authority):
        if not authority:
            return True
        log.info(f"Selecting Tax Authority: {authority}")
        try:
            self._blur_active_element()
            self.wait_seconds(0.3)
            self.click(self.TAX_AUTHORITY_SELECT)
            # ... rest stays the same
            self.wait_seconds(1)

            option = ("xpath", f"//mat-option//span[contains(text(),'{authority}')]")
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(option)
            )
            self.wait_seconds(0.3)
            self._js_click(option)
            self.wait_seconds(0.5)
            log.info(f"Tax Authority set to: {authority}")
            return True
        except Exception as e:
            log.warning(f"Tax Authority selection failed: {e}")
            self._log_overlay_state()
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
        """Click 'Define Tax Rate Details' tab to reveal sub-table."""
        try:
            self.click(self.SUB_TABLE_TAB)
            self.wait_seconds(1)
            log.info("Switched to sub-table tab")
        except Exception:
            log.info("Sub-table tab not found (may already be visible)")

    def _get_sub_table_rows(self):
        """Get all sub-table row WebElements."""
        try:
            rows = self.driver.find_elements(By.CSS_SELECTOR,
                "div.edit_pop_up table.mat-table tbody tr")
            return rows
        except Exception:
            return []

    def _get_sub_table_row_count(self):
        """Get the number of sub-table rows."""
        rows = self._get_sub_table_rows()
        count = len(rows)
        log.info(f"Sub-table has {count} row(s)")
        return count

    def add_sub_table_row(self):
        """Click the Add button to add a new empty row to the sub-table."""
        log.info("Adding new sub-table row")
        try:
            self._js_click(self.ADD_SUB_TABLE_ROW_BUTTON)
            self.wait_seconds(1)
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
            self.wait_seconds(0.5)
            log.info(f"Deleted sub-table row {row_index}")
        except Exception as e:
            log.warning(f"Failed to delete sub-table row {row_index}: {e}")

    def select_hsn_number(self, hsn, row_index=0):
        """Select HSN Number from the mat-select dropdown in a sub-table row.

        Args:
            hsn: HSN Number string (e.g., '997212').
            row_index: 0-based row index in the sub-table.

        Returns:
            True if selection succeeded, False otherwise.
        """
        if not hsn:
            return True

        log.info(f"Selecting HSN Number '{hsn}' in row {row_index}")
        try:
            rows = self._get_sub_table_rows()
            if row_index >= len(rows):
                log.warning(f"Row {row_index} does not exist ({len(rows)} rows)")
                return False

            row = rows[row_index]
            hsn_select = row.find_element(By.CSS_SELECTOR, "mat-select")
            self._blur_active_element()
            self.wait_seconds(0.3)
            self._js_click_element(hsn_select)
            self.wait_seconds(1)

            option = ("xpath", f"//mat-option//span[contains(text(),'{hsn}')]")
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(option)
            )
            self.wait_seconds(0.3)
            self._js_click(option)
            self.wait_seconds(0.5)
            log.info(f"HSN Number set to: {hsn}")
            return True
        except Exception as e:
            log.warning(f"HSN Number selection failed: {e}")
            self._log_overlay_state()
            return False

    def fill_sub_table_tax_rate(self, rate, row_index=0):
        """Set Tax Rate value in a sub-table row.

        Args:
            rate: Numeric tax rate value (e.g., 18.0, -5.0, 0).
            row_index: 0-based row index in the sub-table.
        """
        log.info(f"Setting Tax Rate to {rate} in row {row_index}")
        try:
            rows = self._get_sub_table_rows()
            if row_index >= len(rows):
                log.warning(f"Row {row_index} does not exist ({len(rows)} rows)")
                return

            row = rows[row_index]
            tax_rate_input = row.find_element(By.CSS_SELECTOR, "input[name='Tax Rate']")
            tax_rate_input.clear()
            tax_rate_input.send_keys(str(rate))
            self.wait_seconds(0.3)
            log.info(f"Tax Rate set to: {rate}")
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
        clicks Add first, then fills from bottom-up.

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
        self.wait_seconds(0.5)

        # Add extra rows if needed (first row is pre-created)
        current_rows = self._get_sub_table_row_count()
        needed = len(sub_table_rows)
        for _ in range(max(0, needed - current_rows)):
            self.add_sub_table_row()

        # Fill rows from bottom-up (pattern #9)
        all_ok = True
        for i in range(needed - 1, -1, -1):
            ok = self.fill_sub_table_row(sub_table_rows[i], row_index=i)
            if not ok:
                all_ok = False
                log.warning(f"Sub-table row {i} fill failed")

        return all_ok

    # ================================================================
    # FORM — Submit / Create Version
    # ================================================================

    def submit(self):
        """Click the Submit button (Create mode)."""
        log.step(4, "Clicking Submit button")
        self._force_close_panels()
        self.click(self.SUBMIT_BUTTON)

    def click_create_version(self):
        """Click the Create Version button (Version mode)."""
        log.step(4, "Clicking Create Version button")
        self._force_close_panels()
        self.click(self.CREATE_VERSION_BUTTON)

    # ================================================================
    # CREATE RECORD — Full flow with retry logic
    # ================================================================

    def create_record(self, data, max_cycles=3):
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
            log.step(1, f"Creating Tax Rate record: {name} (cycle {cycle}/{max_cycles})")

            try:
                # Navigate fresh
                self.driver.refresh()
                self.wait_seconds(3)
                self.wait_for_visible(self.TABLE, timeout=15)

                # Open Add form
                self.open_add_form()

                # Fill header fields (dropdowns first, then text, then dates)
                self.fill_all_fields(header)

                # Fill sub-table rows
                if sub_rows:
                    self.fill_sub_table(sub_rows)

                # Click Submit
                self.submit()
                self.wait_seconds(2)

                # ALERT-FIRST: Check for validation alert before checking form close
                if self.is_validation_alert_present(timeout=5):
                    title = self.get_sweetalert_title()
                    log.info(f"Validation Failed: {title}")
                    self.accept_sweetalert()
                    self.wait_seconds(1)
                    self.cancel()
                    return {"status": "failed", "error": title}

                # Check if form closed (silent success — TR-03)
                if not self.is_form_open():
                    log.info(f"Record '{name}' created successfully (silent success)")
                    self.wait_seconds(1)
                    return {"status": "success", "error": ""}

                # Form still open, no alert — dropdown may have failed
                log.warning(f"Cycle {cycle}: Form still open, no alert — retrying")

            except Exception as e:
                log.warning(f"Cycle {cycle} error: {e}")

            # Cleanup before retry
            try:
                self.cancel()
            except Exception:
                pass
            self.wait_seconds(1)

        return {"status": "failed", "error": f"Could not create record after {max_cycles} cycles"}

    # ================================================================
    # SWEET ALERT — Detection & Handling
    # ================================================================

    def is_validation_alert_present(self, timeout=5):
        """Check if SweetAlert 'Validation Failed' popup is visible."""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, ".swal2-popup"))
            )
            title = self.get_text(self.SWEET_ALERT_TITLE)
            if "Validation Failed" in title:
                log.info("Validation Failed alert detected")
                return True
        except Exception:
            pass
        return False

    def get_sweetalert_title(self):
        """Get the title text from the current SweetAlert popup."""
        try:
            return self.get_text(self.SWEET_ALERT_TITLE)
        except Exception:
            return ""

    def get_sweetalert_message(self):
        """Get the message text from the current SweetAlert popup."""
        try:
            return self.get_text(self.SWEET_ALERT_MESSAGE)
        except Exception:
            return ""

    def accept_sweetalert(self):
        """Click OK/Confirm on the current SweetAlert popup."""
        log.info("Accepting SweetAlert (clicking OK)")
        try:
            self.click(self.SWEET_ALERT_CONFIRM_BTN)
            self.wait_seconds(0.5)
        except Exception:
            log.warning("Could not click SweetAlert OK button")

    def dismiss_sweetalert(self):
        """Click Cancel on the current SweetAlert popup."""
        try:
            self.click(self.SWEET_ALERT_CANCEL_BTN)
            self.wait_seconds(0.5)
        except Exception:
            pass

    def is_any_alert_present(self, timeout=3):
        """Check if any SweetAlert popup is visible."""
        return self.is_displayed(self.SWEET_ALERT_POPUP, timeout=timeout)

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

        Args:
            name: Tax Rate Name to search for.

        Returns:
            0-based row index, or -1 if not found.
        """
        row_count = self.get_table_row_count()
        for i in range(row_count):
            cell_name = self.get_name_from_row(i)
            if cell_name.strip().lower() == name.strip().lower():
                log.info(f"Found '{name}' at row {i}")
                return i
        log.warning(f"Record '{name}' not found in visible rows")
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

    def click_view_on_row(self, row_index):
        """Click the View (eye) button on a specific table row."""
        log.info(f"Clicking View button on row {row_index}")
        self.click(self._view_button(row_index))
        self.wait_for_form_to_open()

    def click_version_on_row(self, row_index):
        """Click the Version (folder) button on a specific table row.

        Opens editable form with 'Create Version' button (TR-02).
        """
        log.info(f"Clicking Version button on row {row_index}")
        self.click(self._version_button(row_index))
        self.wait_for_form_to_open()

    def click_history_on_row(self, row_index):
        """Click the History (archive) button on a specific table row."""
        log.info(f"Clicking History button on row {row_index}")
        self.click(self._history_button(row_index))
        self.wait_for_history_popup()

    # ================================================================
    # SEARCH
    # ================================================================

    def _do_js_search(self, text):
        """Execute search using atomic JavaScript."""
        self.driver.execute_script("""
            var toggleBtn = document.querySelector('button.search-btn');
            if (toggleBtn) toggleBtn.click();
        """)
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='Search']"))
        )
        self.wait_seconds(1)

        self.driver.execute_script("""
            var input = document.querySelector('input[placeholder="Search"]');
            var nativeSetter = Object.getOwnPropertyDescriptor(
                window.HTMLInputElement.prototype, 'value'
            ).set;
            nativeSetter.call(input, '');
            input.dispatchEvent(new Event('input', {bubbles: true}));
            nativeSetter.call(input, arguments[0]);
            input.dispatchEvent(new Event('input', {bubbles: true}));
            input.dispatchEvent(new KeyboardEvent('keydown', {
                key: 'Enter', code: 'Enter', keyCode: 13, bubbles: true
            }));
        """, text)
        self.wait_seconds(2)

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
        """Clear the search filter to show all records."""
        log.info("Clearing search filter...")
        try:
            self.driver.execute_script("""
                var input = document.querySelector('input[placeholder="Search"]');
                if (input) {
                    var nativeSetter = Object.getOwnPropertyDescriptor(
                        window.HTMLInputElement.prototype, 'value'
                    ).set;
                    nativeSetter.call(input, '');
                    input.dispatchEvent(new Event('input', {bubbles: true}));
                    input.dispatchEvent(new KeyboardEvent('keydown', {
                        key: 'Enter', code: 'Enter', keyCode: 13, bubbles: true
                    }));
                }
                var btn = document.querySelector('button.search-btn');
                if (btn) btn.click();
            """)
            self.wait_seconds(1)
        except Exception:
            self.navigate_to_page()

    # ================================================================
    # REFRESH
    # ================================================================

    def refresh_table(self):
        """Click the Refresh button to reload the table data."""
        log.info("Refreshing Tax Rate table...")
        try:
            refresh_btn = ("xpath", "//button[mat-icon[text()='refresh']]")
            self.click(refresh_btn)
            self.wait_seconds(2)
            log.info("Table refreshed")
        except Exception:
            log.warning("Refresh button not found, falling back to page refresh")
            self.navigate_to_page()

    # ================================================================
    # HISTORY POPUP
    # ================================================================

    def wait_for_history_popup(self, timeout=15):
        """Wait for the history popup to open and load data."""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, ".popup-content")
                )
            )
            # Wait for either table rows or "No Data" image
            WebDriverWait(self.driver, 5).until(
                lambda d: (
                    len(d.find_elements(By.CSS_SELECTOR, ".edit_pop_up table tbody tr")) > 0
                    or d.find_element(By.CSS_SELECTOR, ".edit_pop_up img[alt='No Data Available']")
                        .is_displayed()
                )
            )
            log.info("History popup loaded")
        except Exception:
            log.warning("History popup did not load within timeout")
            self.take_screenshot("history_popup_not_loaded")

    def is_history_popup_open(self, timeout=5):
        """Check if the History popup is currently visible."""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, ".popup-content")
                )
            )
            return True
        except Exception:
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
        """Close the History popup via Cancel button."""
        log.info("Closing History popup")
        try:
            self.click(self.HISTORY_CANCEL_BTN)
            self.wait_seconds(1)
        except Exception:
            from selenium.webdriver.common.action_chains import ActionChains
            ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
            self.wait_seconds(0.5)
