"""
tax_authority_page.py
----------------------
Page Object Model for RhythmERP Tax Authority screen (Common Settings).
Extends BasePage with Tax Authority-specific locators and methods.

Fields: Tax Name (text input) + Tax Type (mat-select) + Country (mat-select).
Pattern: List view (table#excel-table) + popup form (Add / Edit / View) + popup history.
"""

import time

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from common.base_page import BasePage
from common.logger import log


class TaxAuthorityPage(BasePage):
    """
    Page Object for Common Settings > Tax Authority screen.
    """

    # ================================================================
    # LOCATORS — Form Popup
    # ================================================================

    # --- Form Container ---
    FORM_POPUP = ("css", "div.edit_pop_up")
    FORM_CONTENT = ("css", "div.edit_pop_up div.overflow_model")
    FORM_HEADER_TITLE = ("css", "div.edit_pop_up .popup-header h3")

    # --- Form Fields (1 text input via input[name=...]) ---
    TAX_NAME_INPUT = ("css", "input[name='Tax Name']")

    # --- Dropdowns (label-based XPath — standard mat-select, NOT app-dropdown-v2) ---
    TAX_TYPE_SELECT = ("xpath", "//mat-label[normalize-space()='Tax Type']/ancestor::mat-form-field//mat-select")
    COUNTRY_SELECT = ("xpath", "//mat-label[normalize-space()='Country']/ancestor::mat-form-field//mat-select")

    # --- Form Buttons ---
    SUBMIT_BUTTON = ("xpath", "//div[contains(@class,'popup-footer')]//button[contains(.,'Submit')]")
    UPDATE_BUTTON = ("xpath", "//div[contains(@class,'popup-footer')]//button[contains(.,'Update')]")
    CANCEL_BUTTON = ("xpath", "//div[contains(@class,'popup-footer')]//button[contains(.,'Cancel')]")

    # --- Popup Header Buttons (fullscreen + close X) ---
    CLOSE_X_BUTTON = ("xpath", "//div[@class='popup-actions']//button[contains(.,'close')]")
    FULLSCREEN_BUTTON = ("xpath", "//div[@class='popup-actions']//button[contains(.,'fullscreen')]")

    # ================================================================
    # LOCATORS — SweetAlert Popups
    # ================================================================

    SWEET_ALERT_POPUP = ("css", ".swal2-popup")
    SWEET_ALERT_TITLE = ("css", ".swal2-title")
    SWEET_ALERT_MESSAGE = ("css", ".swal2-html-container")
    SWEET_ALERT_CONFIRM_BTN = ("css", "button.swal2-confirm")
    SWEET_ALERT_CANCEL_BTN = ("css", "button.swal2-cancel")

    # ================================================================
    # LOCATORS — List Page
    # ================================================================

    # Add button (NO mattooltip — uses mat-icon text 'add')
    ADD_BUTTON = ("xpath", "//button[mat-icon[text()='add']]")

    # Data table (same as Season/Error Code Mst pattern)
    TABLE = ("css", "table#excel-table")
    TABLE_BODY = ("css", "table#excel-table tbody")
    TABLE_ROWS = ("css", "table#excel-table tbody tr")

    # Action buttons per row (View=1st, Edit=2nd, History=3rd) — tblActnBtn pattern
    def _view_button(self, row_index):
        return ("xpath", f"(//button[contains(@class,'tblActnBtn')])[{row_index * 3 + 1}]")

    def _edit_button(self, row_index):
        return ("xpath", f"(//button[contains(@class,'tblActnBtn')])[{row_index * 3 + 2}]")

    def _history_button(self, row_index):
        return ("xpath", f"(//button[contains(@class,'tblActnBtn')])[{row_index * 3 + 3}]")

    # Table cell text (row=0-based data row, col=0-based)
    # Columns: 0=View(btn), 1=Edit(btn), 2=History(btn), 3=Tax Name
    def _table_cell(self, row, col):
        return ("xpath", f"(//table[@id='excel-table']//tbody//tr)[{row + 1}]/td[{col + 1}]")

    # Search toggle button
    SEARCH_BUTTON = ("css", "button.search-btn")

    # Pagination
    PAGER = ("css", "mat-paginator")
    PAGER_RANGE_LABEL = ("css", "mat-paginator .mat-mdc-paginator-range-label")
    NEXT_PAGE_BTN = ("css", "mat-paginator button[aria-label='Next page']")
    PREV_PAGE_BTN = ("css", "mat-paginator button[aria-label='Previous page']")
    FIRST_PAGE_BTN = ("css", "mat-paginator button[aria-label='First page']")
    LAST_PAGE_BTN = ("css", "mat-paginator button[aria-label='Last page']")

    # ================================================================
    # LOCATORS — History Popup (Season-style popup-overlay)
    # ================================================================

    HISTORY_POPUP = ("css", ".popup-overlay")
    HISTORY_TABLE_ROWS = ("css", ".popup-overlay .popup-content table tbody tr")
    HISTORY_NO_DATA = ("css", ".popup-overlay .popup-content .no-data")
    HISTORY_TITLE = ("css", ".popup-overlay .popup-content .popup-title")
    HISTORY_CANCEL_BTN = ("css", ".popup-overlay .popup-footer button")

    # ================================================================
    # NAVIGATION
    # ================================================================

    def navigate_to_tax_authority(self):
        """Navigate directly to the Tax Authority screen via URL."""
        from tax_authority.data.tax_authority_data import TAX_AUTHORITY_PAGE_URL
        log.info("Navigating to Tax Authority screen...")
        self._recover_from_stuck_state()
        self.navigate_to(TAX_AUTHORITY_PAGE_URL)
        self.wait_seconds(2)
        try:
            self.wait_for_visible(self.TABLE, timeout=15)
            log.info("Tax Authority screen loaded successfully")
        except Exception:
            log.warning("Table not found — page may still be loading or empty")
            self.take_screenshot("tax_authority_page_load")

    # ================================================================
    # STUCK STATE RECOVERY
    # ================================================================

    def _recover_from_stuck_state(self):
        """Recover from any stuck popups, overlays, or alerts.

        Handles: SweetAlert popups, CDK overlay backdrops,
        form popup, history popup.
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
                            log.info("Recovered: Dismissed SweetAlert popup")
                            self.wait_seconds(0.5)
            except Exception:
                pass

            # 2. Remove CDK overlay backdrops via JavaScript
            try:
                self.driver.execute_script("""
                    document.querySelectorAll('.cdk-overlay-backdrop').forEach(el => el.remove());
                """)
            except Exception:
                pass

            # 3. Close form popup if open
            try:
                form = self.driver.find_element(By.CSS_SELECTOR, "div.edit_pop_up")
                if form.is_displayed():
                    cancel = form.find_element(
                        By.CSS_SELECTOR,
                        ".popup-footer button[type='button']"
                    )
                    if cancel.is_displayed():
                        cancel.click()
                        log.info("Recovered: Closed stuck form popup")
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
                        log.info("Recovered: Closed stuck history popup")
                        self.wait_seconds(0.5)
            except Exception:
                pass

        except Exception as e:
            log.warning(f"Recovery attempt completed with warning: {e}")

    # ================================================================
    # ADD FORM — Open / Close
    # ================================================================

    def open_add_form(self):
        """Click the Add (+) button to open the form popup."""
        log.step(1, "Opening Add form")
        self._recover_from_stuck_state()
        try:
            self.click(self.ADD_BUTTON)
        except Exception:
            # Fallback: try mat-icon text
            add_btn = ("xpath", "//button[mat-icon[text()='add']]")
            self.click(add_btn)
        self.wait_for_form_to_open()
        log.info("Add form opened")

    def close_form_via_cancel(self):
        """Click the Cancel button to close the form."""
        log.info("Closing form via Cancel button")
        self.click(self.CANCEL_BUTTON)
        self.wait_for_form_to_close()

    def close_form_via_x(self):
        """Click the X (close) button in the popup header."""
        log.info("Closing form via X button")
        self.click(self.CLOSE_X_BUTTON)
        self.wait_for_form_to_close()

    # ================================================================
    # FORM — Fill Fields (Atomic JS for Angular reactivity)
    # ================================================================

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

    def fill_tax_name(self, name):
        """Type tax authority name into the Tax Name field."""
        self.type_text(self.TAX_NAME_INPUT, name, clear_first=True)

    def clear_form(self):
        """Clear the Tax Name text field."""
        log.info("Clearing form fields")
        try:
            self.clear_field(self.TAX_NAME_INPUT)
        except Exception:
            pass

    # ================================================================
    # DROPDOWN SELECTION (robust with retry + refresh loop)
    # ================================================================

    def _js_click(self, locator):
        """Click an element using JavaScript — bypasses CDK overlay."""
        element = self.find_element(locator)
        self.driver.execute_script("arguments[0].click();", element)

    def _force_close_panels(self):
        """Remove leftover CDK overlay panels (not dialogs)."""
        self.driver.execute_script("""
            document.querySelectorAll('.cdk-overlay-backdrop:not(.cdk-overlay-dark)').forEach(el => el.remove());
            document.querySelectorAll('.cdk-overlay-pane:not(.mat-mdc-dialog-container)').forEach(el => el.remove());
        """)

    def _log_overlay_state(self):
        """Diagnostic: log current CDK overlay pane state."""
        try:
            panes = self.driver.find_elements(By.CSS_SELECTOR, ".cdk-overlay-pane")
            log.info(f"[DIAG] {len(panes)} overlay pane(s) in DOM")
            options = self.driver.find_elements(By.CSS_SELECTOR, "mat-option")
            log.info(f"[DIAG] {len(options)} mat-option element(s) in DOM")
        except Exception as diag_err:
            log.info(f"[DIAG] Overlay state check failed: {diag_err}")

    # ═══════════════════════════════════════════════════════════
    # ROBUST DROPDOWN OPENER
    # ═══════════════════════════════════════════════════════════
    def _open_dropdown(self, trigger_locator, label="dropdown"):
        """
        Open a mat‑select dropdown with 3 click strategies.
        Returns True if at least one mat-option appears.
        """
        for attempt in range(3):
            try:
                if attempt == 0:
                    self.click(trigger_locator)
                elif attempt == 1:
                    el = self.find_element(trigger_locator)
                    self.driver.execute_script("arguments[0].click();", el)
                else:
                    el = self.find_element(trigger_locator)
                    ActionChains(self.driver).move_to_element(el).click().perform()
                self.wait_seconds(1)
                if self.driver.find_elements(By.CSS_SELECTOR, "mat-option"):
                    log.info(f"  [{label}] Dropdown opened")
                    return True
            except Exception as e:
                log.warning(f"  [{label}] click attempt {attempt+1} failed: {e}")
        return False

    # ═══════════════════════════════════════════════════════════
    # DROPDOWN SELECTION METHODS (return True/False)
    # ═══════════════════════════════════════════════════════════
    def select_tax_type(self, tax_type):
        """Select Tax Type from dropdown. Returns True if successful."""
        if not self._open_dropdown(self.TAX_TYPE_SELECT, "Tax Type"):
            return False
        # Try clicking the option up to 3 times until Angular registers it
        for attempt in range(3):
            try:
                option = ("xpath", f"//mat-option//span[contains(text(),'{tax_type}')]")
                if attempt > 0:
                    # Re-open the panel if it was closed
                    if not self.driver.find_elements(By.CSS_SELECTOR, ".cdk-overlay-pane mat-option"):
                        self._open_dropdown(self.TAX_TYPE_SELECT, "Tax Type")
                opt_el = self.find_element(option)
                opt_el.click()          # real DOM click – not JS
                self.wait_seconds(0.5)
                # Verify the select shows the value
                trigger = self.find_element(self.TAX_TYPE_SELECT)
                if tax_type.lower() in (trigger.text or "").lower():
                    self._force_close_panels()
                    return True
                log.warning(f"Tax Type not registered (attempt {attempt+1})")
            except Exception as e:
                log.warning(f"Tax Type click failed (attempt {attempt+1}): {e}")
        self._force_close_panels()
        return False

    def select_country(self, country):
        """Select Country from searchable dropdown. Returns True if successful."""
        if not self._open_dropdown(self.COUNTRY_SELECT, "Country"):
            return False
        # Type search text first
        search_typed = False
        for sel in [".cdk-overlay-pane input[type='text']", ".cdk-overlay-pane input"]:
            try:
                search_input = self.driver.find_element(By.CSS_SELECTOR, sel)
                if search_input.is_displayed():
                    search_input.clear()
                    search_input.send_keys(country)
                    self.wait_seconds(1)
                    search_typed = True
                    break
            except Exception:
                continue
        if not search_typed:
            # If no search box found, just proceed
            pass

        # Try clicking the first option up to 3 times until Angular registers it
        for attempt in range(3):
            try:
                first_option = ("xpath", "(//mat-option)[1]")
                if attempt > 0:
                    if not self.driver.find_elements(By.CSS_SELECTOR, ".cdk-overlay-pane mat-option"):
                        self._open_dropdown(self.COUNTRY_SELECT, "Country")
                        if search_typed:
                            # Re-type search term
                            for sel in [".cdk-overlay-pane input[type='text']", ".cdk-overlay-pane input"]:
                                try:
                                    inp = self.driver.find_element(By.CSS_SELECTOR, sel)
                                    if inp.is_displayed():
                                        inp.clear()
                                        inp.send_keys(country)
                                        self.wait_seconds(1)
                                        break
                                except Exception:
                                    pass
                opt_el = self.find_element(first_option)
                opt_el.click()
                self.wait_seconds(0.5)
                trigger = self.find_element(self.COUNTRY_SELECT)
                if country.lower() in (trigger.text or "").lower():
                    self._force_close_panels()
                    return True
                log.warning(f"Country not registered (attempt {attempt+1})")
            except Exception as e:
                log.warning(f"Country click failed (attempt {attempt+1}): {e}")
        self._force_close_panels()
        return False

    # ═══════════════════════════════════════════════════════════
    # FILL ALL FIELDS WITH RETRY (The Core Fix)
    # ═══════════════════════════════════════════════════════════
    def fill_all_fields(self, data, max_cycles=3, is_edit=False):
        """
        Fill the form. If any dropdown fails, close the form,
        hard‑refresh the page, reopen and try again (up to 3 cycles).
        Returns True when all fields are filled.

        When is_edit=True, the Edit form is already open – no refresh/open.
        """
        from tax_authority.data.tax_authority_data import FIELD_TAX_NAME

        for cycle in range(1, max_cycles + 1):
            if not is_edit:
                log.info(f"  Fill cycle {cycle}/{max_cycles} — refreshing page")
                self.navigate_to_tax_authority()   # safe navigation, no driver.refresh()
                self.open_add_form()

            # Dropdowns first (they can fail)
            tax_type = data.get("tax_type", "")
            country = data.get("country", "")
            type_ok = self.select_tax_type(tax_type) if tax_type else True
            country_ok = self.select_country(country) if country else True

            if type_ok and country_ok:
                # Now fill Tax Name
                tax_name = data.get(FIELD_TAX_NAME, "")
                if tax_name:
                    self.fill_tax_name(tax_name)
                return True

            # Dropdown failed → close, loop will restart with fresh page
            if is_edit:
                # In Edit mode we cannot recover – raise to avoid infinite loop
                raise Exception("Dropdowns failed in Edit mode – cannot recover")

            log.warning(f"  Dropdowns failed (tax_type={type_ok}, country={country_ok}) — retrying")
            try:
                self.close_form_via_cancel()
            except Exception:
                pass
            self.wait_seconds(1)

        raise Exception("Could not fill Tax Authority form after multiple refresh cycles")

    # ================================================================
    # FORM — Submit / Update
    # ================================================================

    def click_submit(self):
        """Click the Submit button (Add mode)."""
        log.step(4, "Clicking Submit button")
        self.click(self.SUBMIT_BUTTON)

    def click_update(self):
        """Click the Update button (Edit mode)."""
        log.step(4, "Clicking Update button")
        self.click(self.UPDATE_BUTTON)

    # ================================================================
    # CREATE RECORD — Full flow with alert-first detection
    # ================================================================

    def create_record(self, data):
        """Create a new Tax Authority record.

        Opens form, fills all fields (with retry), clicks Submit, and handles
        the result (success or validation failure).

        IMPORTANT: Checks for validation alert FIRST (before checking
        if form closed) to avoid false positives on duplicates.

        Args:
            data: Dict with FIELD_TAX_NAME, "tax_type", "country".

        Returns:
            True if record was created successfully (form closed, no validation alert).
            False if validation failed (alert present).
        """
        log.step(1, "Creating new Tax Authority record")
        self.fill_all_fields(data)        # fills, refreshing if needed
        self.click_submit()
        self.wait_seconds(2)

        # Check validation alert FIRST (alert-first pattern)
        if self.is_validation_alert_present(timeout=5):
            log.info("Validation Failed — record NOT created")
            self.handle_validation_alert()
            return False

        # Check if form closed (success)
        if not self.is_form_open():
            # BUG: Tax Authority doesn't show success SweetAlert (TA-001)
            # Form closes silently on success
            log.info("Form closed — record created (no success alert shown — known bug)")
            self.wait_seconds(1)
            return True

        # Form still open, no alert — unexpected state
        log.warning("Unexpected: form still open, no alert")
        self.take_screenshot("tax_authority_create_unexpected")
        return False

    def edit_record(self, data, row_index=0):
        """Edit an existing Tax Authority record.

        Opens edit form on specified row, clears and fills all fields,
        clicks Update, and handles the result.

        Args:
            data: Dict with FIELD_TAX_NAME, "tax_type", "country".
            row_index: 0-based row index to edit.

        Returns:
            True if updated successfully.
            False if validation failed.
        """
        log.step(1, f"Editing Tax Authority record at row {row_index}")
        self.click_edit_button(row_index)
        self.wait_seconds(1)
        self.clear_form()
        self.fill_all_fields(data, is_edit=True)   # Edit mode – no refresh
        self.click_update()
        self.wait_seconds(2)

        # Check validation alert FIRST
        if self.is_validation_alert_present(timeout=5):
            log.info("Validation Failed — record NOT updated")
            self.handle_validation_alert()
            return False

        if not self.is_form_open():
            log.info("Form closed — record updated")
            self.wait_seconds(1)
            return True

        log.warning("Unexpected: form still open after update")
        self.take_screenshot("tax_authority_edit_unexpected")
        return False

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

    def is_success_alert_present(self, timeout=5):
        """Check if SweetAlert success popup is visible.

        NOTE: Tax Authority does NOT show success SweetAlert (BUG TA-001).
        This method is kept for consistency but will always return False
        unless the bug is fixed.
        """
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, ".swal2-popup"))
            )
            title = self.get_text(self.SWEET_ALERT_TITLE)
            if "successfully" in title.lower():
                log.info(f"Success alert detected: {title}")
                return True
        except Exception:
            pass
        return False

    def is_any_alert_present(self, timeout=3):
        """Check if any SweetAlert popup is visible."""
        return self.is_displayed(self.SWEET_ALERT_POPUP, timeout=timeout)

    def get_alert_title(self):
        """Get the title text from the current SweetAlert popup."""
        try:
            return self.get_text(self.SWEET_ALERT_TITLE)
        except Exception:
            return ""

    def get_alert_message(self):
        """Get the message text from the current SweetAlert popup."""
        try:
            return self.get_text(self.SWEET_ALERT_MESSAGE)
        except Exception:
            return ""

    def handle_validation_alert(self):
        """Click OK on the Validation Failed SweetAlert."""
        log.info("Handling Validation Failed alert — clicking OK")
        try:
            self.click(self.SWEET_ALERT_CONFIRM_BTN)
            self.wait_seconds(0.5)
        except Exception:
            log.warning("Could not click validation alert OK button")

    def handle_success_alert(self, timeout=10):
        """Handle success SweetAlert.

        NOTE: Tax Authority does NOT show success SweetAlert (BUG TA-001).
        This method attempts to handle it in case the bug is fixed later.
        """
        try:
            self.wait_for_visible(self.SWEET_ALERT_CONFIRM_BTN, timeout=timeout)
            self._force_close_panels()
            self.wait_seconds(0.3)
            self.click(self.SWEET_ALERT_CONFIRM_BTN)
            self.wait_seconds(0.5)
            self.wait_for_success_alert_to_dismiss(timeout=5)
            log.info("Success alert handled — record saved")
        except Exception as e:
            log.warning(f"handle_success_alert: {e}")
            self.wait_for_success_alert_to_dismiss()

    def wait_for_success_alert_to_dismiss(self, timeout=5):
        """Wait for the success toast to auto-dismiss."""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.invisibility_of_element_located((By.CSS_SELECTOR, ".swal2-popup"))
            )
        except Exception:
            log.warning("Success toast did not dismiss within timeout")

    # ================================================================
    # FORM — State Checks
    # ================================================================

    def is_form_open(self):
        """Check if the Tax Authority form popup is currently visible."""
        return self.is_displayed(self.FORM_POPUP, timeout=5)

    def wait_for_form_to_open(self, timeout=10):
        """Wait until the form popup appears."""
        try:
            self.wait_for_visible(self.FORM_POPUP, timeout=timeout)
            log.info("Form popup is now open")
        except Exception:
            log.error("Form popup did not open within timeout")
            self.take_screenshot("form_not_opened")
            raise

    def wait_for_form_to_close(self, timeout=10):
        """Wait until the form popup disappears."""
        try:
            self.wait_for_invisible(self.FORM_POPUP, timeout=timeout)
            log.info("Form popup closed")
            self.wait_seconds(0.5)
        except Exception:
            log.warning("Form popup still visible after timeout")

    def is_field_disabled(self, locator):
        """Check if a form field is disabled (for View mode)."""
        try:
            element = self.find_element(locator)
            disabled = element.get_attribute("disabled")
            aria_disabled = element.get_attribute("aria-disabled")
            return disabled == "true" or aria_disabled == "true"
        except Exception:
            return False

    def is_form_in_view_mode(self):
        """Check if the form is in View mode (no Submit/Update button)."""
        try:
            return not self.is_displayed(self.SUBMIT_BUTTON, timeout=3)
        except Exception:
            return True

    def get_form_title(self):
        """Get the form popup header title."""
        try:
            return self.get_text(self.FORM_HEADER_TITLE)
        except Exception:
            return ""

    # ================================================================
    # TABLE — Read Data
    # ================================================================

    def get_table_row_count(self):
        """Get the number of data rows in the Tax Authority list table."""
        try:
            rows = self.find_elements(self.TABLE_ROWS)
            count = len(rows)
            log.info(f"Table has {count} row(s)")
            return count
        except Exception:
            return 0

    def get_cell_text(self, row_index, col_index):
        """Get text from a specific table cell (0-based indices).

        Columns (0-indexed):
            0 = View (button)
            1 = Edit (button)
            2 = History (button)
            3 = Tax Name
        """
        cell_locator = self._table_cell(row_index, col_index)
        return self.get_text(cell_locator)

    def find_row_by_name(self, name):
        """Find a table row index by matching the Tax Name column.

        Returns:
            int: 0-based row index, or -1 if not found.
        """
        row_count = self.get_table_row_count()
        for i in range(row_count):
            cell_text = self.get_cell_text(i, 3)  # Tax Name is column 3
            if cell_text.strip().lower() == name.strip().lower():
                log.info(f"Found '{name}' at row {i}")
                return i
        log.warning(f"Record '{name}' not found in visible rows")
        return -1

    def is_record_present(self, name):
        """Check if a Tax Authority record exists in the table."""
        return self.find_row_by_name(name) != -1

    def get_name_from_row(self, row_index):
        """Get the Tax Name value from a specific row (column 3)."""
        return self.get_cell_text(row_index, 3)

    def get_column_headers(self):
        """Get all column header texts from the Tax Authority table."""
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

    def click_view_button(self, row_index=0):
        """Click the View button on a specific row."""
        log.info(f"Clicking View button on row {row_index}")
        self.click(self._view_button(row_index))
        self.wait_for_form_to_open()

    def click_edit_button(self, row_index=0):
        """Click the Edit button on a specific row."""
        log.info(f"Clicking Edit button on row {row_index}")
        self.click(self._edit_button(row_index))
        self.wait_for_form_to_open()

    def click_history_button(self, row_index=0):
        """Click the History button on a specific row."""
        log.info(f"Clicking History button on row {row_index}")
        self.click(self._history_button(row_index))
        self.wait_for_history_popup()

    # ================================================================
    # REFRESH / RELOAD TABLE (safe fallback – no driver.refresh())
    # ================================================================

    def refresh_table(self):
        """Click the Refresh button to reload the table data."""
        log.info("Refreshing Tax Authority table...")
        try:
            refresh_btn = ("xpath", "//button[mat-icon[text()='refresh']]")
            self.click(refresh_btn)
            self.wait_seconds(2)
            log.info("Table refreshed")
        except Exception:
            log.warning("Refresh button not found, navigating to Tax Authority page")
            self.navigate_to_tax_authority()
            self.wait_seconds(2)

    # ================================================================
    # SEARCH (Atomic JS)
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
        """Search for a record by Tax Name.

        Args:
            name: The search text.
            exact: If True, verifies at least one visible result has an
                   EXACT name match (case-insensitive).

        Returns:
            True if matching results found, False otherwise.
        """
        log.info(f"Searching for record: {name} (exact={exact})")
        try:
            self._do_js_search(name)
            row_count = self.get_table_row_count()

            if row_count == 0:
                log.info(f"Search returned 0 results for '{name}'")
                return False

            if not exact:
                first_name = ""
                try:
                    first_name = self.get_text(
                        ("xpath", "(//table[@id='excel-table']//tbody//tr)[1]/td[4]")
                    ).strip()
                except Exception:
                    first_name = "(could not read)"
                log.info(f"Search found {row_count} result(s), first: '{first_name}'")
                return True

            # Exact mode
            name_lower = name.strip().lower()
            for i in range(row_count):
                try:
                    row_name = self.get_text(
                        ("xpath", f"(//table[@id='excel-table']//tbody//tr)[{i + 1}]/td[4]")
                    ).strip()
                    if row_name.lower() == name_lower:
                        log.info(f"Exact match found at row {i}: '{row_name}'")
                        return True
                except Exception:
                    continue
            log.info(f"No exact match for '{name}' in {row_count} result(s)")
            return False

        except Exception as e:
            log.error(f"[ERROR] Search failed: {e}")
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
            log.info("Search cleared via JS")
        except Exception:
            log.warning("JS clear failed, navigating to Tax Authority page")
            self.navigate_to_tax_authority()
            self.wait_seconds(2)

    # ================================================================
    # HISTORY POPUP
    # ================================================================

    def wait_for_history_popup(self, timeout=10):
        """Wait for the history popup to open and load data."""
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: (
                    len(d.find_elements(
                        By.CSS_SELECTOR,
                        ".popup-overlay .popup-content table tbody tr"
                    )) > 0
                    or d.find_element(
                        By.CSS_SELECTOR, ".popup-overlay .popup-content"
                    ).is_displayed()
                )
            )
            log.info("History popup loaded")
        except Exception:
            log.warning("History popup did not load within timeout")
            self.take_screenshot("history_popup_not_loaded")

    def get_history_title(self):
        """Get the title text from the History popup header."""
        try:
            return self.get_text(self.HISTORY_TITLE)
        except Exception:
            return ""

    def get_history_row_count(self):
        """Get the total number of rows in the history table.

        Returns 0 if the popup is not open or table not found.
        """
        try:
            rows = self.driver.find_elements(
                By.CSS_SELECTOR,
                ".popup-overlay .popup-content table tbody tr"
            )
            count = len(rows)
            log.info(f"History table has {count} row(s)")
            return count
        except Exception:
            return 0

    def is_history_popup_open(self, timeout=5):
        """Check if the History popup is currently visible."""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, ".popup-overlay .popup-content")
                )
            )
            return True
        except Exception:
            return False

    def close_history_popup(self):
        """Close the History popup using any available method."""
        log.info("Closing History popup")

        # 1. Click the Cancel button (in popup-footer)
        try:
            if self.is_displayed(self.HISTORY_CANCEL_BTN, timeout=2):
                self.click(self.HISTORY_CANCEL_BTN)
                self.wait_seconds(1)
                if not self.is_history_popup_open(timeout=3):
                    return
        except Exception:
            pass

        # 2. Click the X (close) button in popup-actions
        try:
            close_btn = ("css", ".popup-overlay .popup-actions button .mat-icon")
            icons = self.driver.find_elements(*close_btn)
            for icon in icons:
                if "close" in (icon.text or "").lower():
                    btn = icon.find_element(By.XPATH, "./ancestor::button")
                    self.driver.execute_script("arguments[0].click();", btn)
                    self.wait_seconds(1)
                    if not self.is_history_popup_open(timeout=3):
                        return
        except Exception:
            pass

        # 3. Force-remove the overlay with JavaScript
        try:
            self.driver.execute_script("""
                document.querySelectorAll('.popup-overlay').forEach(el => el.remove());
                document.querySelectorAll('.cdk-overlay-backdrop').forEach(el => el.remove());
            """)
            self.wait_seconds(0.5)
        except Exception:
            pass

        # 4. Last resort: press Escape
        try:
            ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
            self.wait_seconds(1)
        except Exception:
            pass