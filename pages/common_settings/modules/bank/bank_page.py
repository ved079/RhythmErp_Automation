"""
bank_page.py
------------
Page Object Model for RhythmERP Bank screen (Common Settings).
Extends BasePage with Bank-specific locators and methods.

Fields: 10 text inputs + 2 dropdowns + 2 custom toggles = 14 fields.
Pattern: List view + popup form (Add / Edit / View).
History: Side panel (NOT popup) — different DOM from Add/Edit.
"""

import time

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from common.base_page import BasePage
from common.logger import log


class BankPage(BasePage):
    """
    Page Object for Common Settings > Bank screen.
    """

    # ================================================================
    # LOCATORS — Form Popup (shared by Add/Edit/View)
    # ================================================================

    # --- Container ---
    FORM_POPUP = ("css", "div.edit_pop_up")
    FORM_CONTENT = ("css", "div.edit_pop_up div.overflow_model")
    FORM_HEADER_TITLE = ("css", "div.edit_pop_up .popup-header h3")

    # --- 10 Text Input Fields ---
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

    # --- 2 Dropdown Fields (mat-select) ---
    ACCOUNT_TYPE_SELECT = ("xpath", "//mat-label[normalize-space()='Account Type']/ancestor::mat-form-field//mat-select")
    GL_ACCOUNT_SELECT = ("xpath", "//mat-label[normalize-space()='GL Account']/ancestor::mat-form-field//mat-select")

    # --- 2 Custom Toggle Switches (NOT Angular Material) ---
    IS_DEFAULT_BANK_TOGGLE = ("xpath", "//span[contains(@class,'main-label') and normalize-space()='Is Default Bank?']/ancestor::app-slide-toggle-v2")
    STATUS_TOGGLE = ("xpath", "//span[contains(@class,'main-label') and normalize-space()='Status']/ancestor::app-slide-toggle-v2")

    # --- Form Buttons ---
    SUBMIT_BUTTON = ("css", "div.popup-footer button[type='submit']")
    CANCEL_BUTTON = ("css", "div.popup-footer button[type='button']")

    # --- Popup Header Buttons ---
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
    # LOCATORS — List Page (Table & Toolbar)
    # ================================================================

    TABLE = ("css", "table.mat-mdc-table")
    TABLE_ROWS = ("css", "table.mat-mdc-table tbody tr.mat-mdc-row")

    # Column headers (for verification)
    COL_VIEW = ("css", "th.mat-column-view")
    COL_EDIT = ("css", "th.mat-column-edit")
    COL_HISTORY = ("css", "th.mat-column-archive")
    COL_BANK_NAME = ("css", "th.mat-column-bank_name")
    COL_ACCOUNT_NUMBER = ("css", "th.mat-column-account_number")
    COL_IFSC_CODE = ("css", "th.mat-column-ifsc_code")
    COL_STATUS = ("css", "th.mat-column-status")

    # Data cells
    CELL_BANK_NAME = ("css", "td.mat-column-bank_name")
    CELL_ACCOUNT_NUMBER = ("css", "td.mat-column-account_number")
    CELL_IFSC_CODE = ("css", "td.mat-column-ifsc_code")
    CELL_STATUS = ("css", "td.mat-column-status")

    # Row action buttons per row (View=1st, Edit=2nd, History=3rd)
    def _view_button(self, row_index):
        return ("xpath", f"(//button[contains(@class,'tblActnBtn')])[{row_index * 3 + 1}]")

    def _edit_button(self, row_index):
        return ("xpath", f"(//button[contains(@class,'tblActnBtn')])[{row_index * 3 + 2}]")

    def _history_button(self, row_index):
        return ("xpath", f"(//button[contains(@class,'tblActnBtn')])[{row_index * 3 + 3}]")

    # Table cell by row/col (0-based)
    def _table_cell(self, row, col):
        return ("xpath", f"(//table[contains(@class,'mat-mdc-table')]//tbody//tr)[{row + 1}]/td[{col + 1}]")

    # ================================================================
    # LOCATORS — History SIDE PANEL (NOT popup!)
    # ================================================================

    HISTORY_PANEL = ("css", ".popup-content")
    HISTORY_TITLE = ("css", ".popup-content .popup-title")
    HISTORY_CANCEL_BTN = ("css", ".popup-content .popup-footer button")
    HISTORY_TABLE_ROWS = ("css", ".popup-content table.mat-mdc-table tbody tr.mat-mdc-row")
    HISTORY_NO_DATA = ("css", ".popup-content .no-data")

    # ================================================================
    # LOCATORS — Dropdown Overlay (CDK)
    # ================================================================

    CDK_OVERLAY = ("css", ".cdk-overlay-container")
    CDK_OPTIONS = ("css", ".cdk-overlay-container mat-option")
    CDK_SEARCH_INPUT = ("css", ".cdk-overlay-container input[placeholder='Search...']")
    CDK_NO_RESULTS = ("css", ".cdk-overlay-container mat-option[disabled]")

    # ================================================================
    # NAVIGATION
    # ================================================================

    def navigate_to_bank(self):
        """Navigate directly to the Bank screen via URL."""
        from bank.data.bank_data import BANK_PAGE_URL
        log.info("Navigating to Bank screen...")
        self.navigate_to(BANK_PAGE_URL)
        self.wait_seconds(2)
        # Recovery: dismiss any stuck popups/overlays after navigation
        self._recover_from_stuck_state()
        self.wait_seconds(1)
        try:
            self.wait_for_visible(self.TABLE, timeout=15)
            log.info("Bank screen loaded successfully")
        except Exception:
            log.warning("Table not found — page may still be loading or empty")
            self.take_screenshot("bank_page_load")

    # ================================================================
    # RECOVERY — Dismiss stuck popups/overlays between tests
    # ================================================================

    def _recover_from_stuck_state(self):
        """Dismiss any stuck SweetAlert, form popup, overlay backdrop, or side panel.

        Called before actions (open_add_form, navigate) to recover from
        state left by a previous test.
        """
        try:
            # 1. Dismiss SweetAlert if present
            try:
                popup = self.driver.find_element(By.CSS_SELECTOR, ".swal2-popup")
                if popup.is_displayed():
                    log.warning("Stuck SweetAlert detected — dismissing")
                    try:
                        self.driver.find_element(By.CSS_SELECTOR, "button.swal2-confirm").click()
                        self.wait_seconds(1)
                    except Exception:
                        pass
            except Exception:
                pass

            # 2. Remove CDK overlay backdrops (block all clicks)
            self.driver.execute_script("""
                document.querySelectorAll('.cdk-overlay-backdrop').forEach(
                    function(el) { el.remove(); }
                );
            """)

            # 3. Close form popup if visible
            try:
                popup = self.driver.find_element(By.CSS_SELECTOR, "div.edit_pop_up")
                if popup.is_displayed():
                    log.warning("Stuck form popup detected — closing via Cancel")
                    try:
                        self.driver.find_element(By.CSS_SELECTOR, "div.popup-footer button[type='button']").click()
                        self.wait_seconds(1)
                    except Exception:
                        pass
            except Exception:
                pass

            # 4. Close history side panel if visible
            try:
                panel = self.driver.find_element(By.CSS_SELECTOR, ".popup-content")
                if panel.is_displayed():
                    log.warning("Stuck history panel detected — closing")
                    try:
                        self.driver.find_element(By.CSS_SELECTOR, ".popup-content .popup-footer button").click()
                        self.wait_seconds(1)
                    except Exception:
                        pass
            except Exception:
                pass

        except Exception:
            pass


    # ================================================================
    # ADD FORM — Open / Close
    # ================================================================

    def open_add_form(self):
        """Click the Add button to open the form popup."""
        log.step(1, "Opening Add form")
        # Recovery: clear any stuck state before clicking ADD
        self._recover_from_stuck_state()
        try:
            add_btn = ("xpath", "//div[@mattooltip='ADD']//button")
            self.click(add_btn)
        except Exception:
            log.warning("Primary add button not found, trying fallback...")
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
        """Click the X button to close the form."""
        log.info("Closing form via X button")
        self.click(self.CLOSE_X_BUTTON)
        self.wait_for_form_to_close()

    # ================================================================
    # FORM — Fill Text Input Fields
    # ================================================================

    def enter_bank_name(self, name):
        """Type into the Bank Name field using nativeInputValueSetter for Angular reactivity."""
        log.step(2, f"Entering Bank Name: {name}")
        self._fill_text_field(self.BANK_NAME_INPUT, name)

    def enter_bank_code(self, code):
        """Type into the Bank Code field."""
        log.step(3, f"Entering Bank Code: {code}")
        self._fill_text_field(self.BANK_CODE_INPUT, code)

    def enter_branch_name(self, name):
        """Type into the Branch Name field."""
        log.step(4, f"Entering Branch Name: {name}")
        self._fill_text_field(self.BRANCH_NAME_INPUT, name)

    def enter_branch_code(self, code):
        """Type into the Branch Code field."""
        log.step(5, f"Entering Branch Code: {code}")
        self._fill_text_field(self.BRANCH_CODE_INPUT, code)

    def enter_account_number(self, number):
        """Type into the Account Number field."""
        log.step(6, f"Entering Account Number: {number}")
        self._fill_text_field(self.ACCOUNT_NUMBER_INPUT, number)

    def enter_swift_number(self, number):
        """Type into the Swift Number field (optional)."""
        log.step(7, f"Entering Swift Number: {number}")
        self._fill_text_field(self.SWIFT_NUMBER_INPUT, number)

    def enter_iban_number(self, number):
        """Type into the IBAN Number field (optional)."""
        log.step(8, f"Entering IBAN Number: {number}")
        self._fill_text_field(self.IBAN_NUMBER_INPUT, number)

    def enter_ifsc_code(self, code):
        """Type into the IFSC Code field."""
        log.step(9, f"Entering IFSC Code: {code}")
        self._fill_text_field(self.IFSC_CODE_INPUT, code)

    def enter_cash_credit_limit(self, limit):
        """Type into the Cash Credit Limit field."""
        log.step(10, f"Entering Cash Credit Limit: {limit}")
        self._fill_text_field(self.CASH_CREDIT_LIMIT_INPUT, limit)

    def enter_bank_address(self, address):
        """Type into the Bank Address field."""
        log.step(11, f"Entering Bank Address: {address}")
        self._fill_text_field(self.BANK_ADDRESS_INPUT, address)

    def _fill_text_field(self, locator, value):
        """Fill a text input using nativeInputValueSetter for Angular reactivity."""
        if not value:
            log.info("Value is empty — skipping field")
            return
        self.driver.execute_script("""
            var input = arguments[0];
            var nativeSetter = Object.getOwnPropertyDescriptor(
                window.HTMLInputElement.prototype, 'value'
            ).set;
            nativeSetter.call(input, arguments[1]);
            input.dispatchEvent(new Event('input', {bubbles: true}));
            input.dispatchEvent(new Event('change', {bubbles: true}));
        """, self.find_element(locator), value)

    # ================================================================
    # FORM — Dropdown Fields
    # ================================================================

    def select_account_type(self, option_text):
        """Select an option from the Account Type dropdown (2 fixed options: Current/Saving)."""
        log.step(12, f"Selecting Account Type: {option_text}")
        try:
            self.click(self.ACCOUNT_TYPE_SELECT)
            self.wait_seconds(1)
            # Click the matching mat-option
            option = ("xpath", f"//mat-option//span[contains(text(),'{option_text}')]")
            self.click(option)
            self.wait_seconds(0.5)
            log.info(f"Account Type '{option_text}' selected")
        except Exception as e:
            log.error(f"Failed to select Account Type '{option_text}': {e}")
            raise

    def select_gl_account(self, search_text):
        """Select a GL Account by searching in the dropdown (115+ options).

        Opens the dropdown, types a search term, then clicks the first
        matching option.
        """
        log.step(13, f"Selecting GL Account matching: {search_text}")
        try:
            self.click(self.GL_ACCOUNT_SELECT)
            self.wait_seconds(1)

            # Type in the search input inside the dropdown panel
            search_input = self.CDK_SEARCH_INPUT
            self.wait_for_visible(search_input, timeout=5)
            self._fill_text_field(search_input, search_text)
            self.wait_seconds(1)

            # Click the first visible mat-option
            self.click(self.CDK_OPTIONS)
            self.wait_seconds(0.5)
            log.info(f"GL Account selected for search term '{search_text}'")
        except Exception as e:
            log.error(f"Failed to select GL Account '{search_text}': {e}")
            raise

    # ================================================================
    # FORM — Toggle Switch Fields (Custom, NOT Angular Material)
    # ================================================================

    def set_is_default_bank(self, enabled=True):
        """Set the 'Is Default Bank?' toggle.

        Args:
            enabled: True = Yes (click .on label), False = No (click .off label).
        """
        log.step(14, f"Setting Is Default Bank: {'Yes' if enabled else 'No'}")
        try:
            toggle = self.find_element(self.IS_DEFAULT_BANK_TOGGLE)
            if enabled:
                toggle.find_element(By.CSS_SELECTOR, "span.state-label.on").click()
            else:
                toggle.find_element(By.CSS_SELECTOR, "span.state-label.off").click()
            self.wait_seconds(0.3)
        except Exception as e:
            log.warning(f"Could not set Is Default Bank toggle: {e}")

    def set_status(self, active=True):
        """Set the Status toggle.

        Args:
            active: True = Active (click .on label), False = Inactive (click .off label).
        """
        log.step(15, f"Setting Status: {'Active' if active else 'Inactive'}")
        try:
            toggle = self.find_element(self.STATUS_TOGGLE)
            if active:
                toggle.find_element(By.CSS_SELECTOR, "span.state-label.on").click()
            else:
                toggle.find_element(By.CSS_SELECTOR, "span.state-label.off").click()
            self.wait_seconds(0.3)
        except Exception as e:
            log.warning(f"Could not set Status toggle: {e}")

    # ================================================================
    # FORM — Fill All Fields (Convenience)
    # ================================================================

    def fill_all_required_fields(self, data):
        """Fill all 12 required fields at once from a data dict.

        Expected keys: Bank Name, Bank Code, Branch Name, Branch Code,
        Account Number, IFSC Code, Cash Credit Limit, Bank Address,
        Account Type, GL Account.
        """
        self.enter_bank_name(data.get("Bank Name", ""))
        self.enter_bank_code(data.get("Bank Code", ""))
        self.enter_branch_name(data.get("Branch Name", ""))
        self.enter_branch_code(data.get("Branch Code", ""))
        self.enter_account_number(data.get("Account Number", ""))
        self.enter_ifsc_code(data.get("IFSC Code", ""))
        self.enter_cash_credit_limit(data.get("Cash Credit Limit", ""))
        self.enter_bank_address(data.get("Bank Address", ""))

        # Optional fields
        if data.get("Swift Number"):
            self.enter_swift_number(data["Swift Number"])
        if data.get("IBAN Number"):
            self.enter_iban_number(data["IBAN Number"])

        # Dropdowns
        if data.get("Account Type"):
            self.select_account_type(data["Account Type"])
        if data.get("GL Account"):
            self.select_gl_account(data["GL Account"])

        # Toggles
        if "Is Default Bank" in data:
            self.set_is_default_bank(data["Is Default Bank"])
        if "Status" in data:
            self.set_status(data["Status"])

    def clear_form(self):
        """Clear all 10 text input fields in the form."""
        log.info("Clearing form text fields")
        for locator in [
            self.BANK_NAME_INPUT, self.BANK_CODE_INPUT,
            self.BRANCH_NAME_INPUT, self.BRANCH_CODE_INPUT,
            self.ACCOUNT_NUMBER_INPUT, self.SWIFT_NUMBER_INPUT,
            self.IBAN_NUMBER_INPUT, self.IFSC_CODE_INPUT,
            self.CASH_CREDIT_LIMIT_INPUT, self.BANK_ADDRESS_INPUT,
        ]:
            try:
                self.clear_field(locator)
            except Exception:
                pass

    # ================================================================
    # FORM — Submit / Update
    # ================================================================

    def click_submit(self):
        """Click the Submit button (Add mode)."""
        log.step(16, "Clicking Submit button")
        self.click(self.SUBMIT_BUTTON)

    def click_update(self):
        """Click the Update button (Edit mode). Same element, different text."""
        log.step(16, "Clicking Update button")
        self.click(self.SUBMIT_BUTTON)

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
        """Check if SweetAlert success popup is visible."""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, ".swal2-popup"))
            )
            title = self.get_text(self.SWEET_ALERT_TITLE)
            if "successfully" in title.lower() or "success" in title.lower():
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

    def handle_success_alert(self):
        """Handle success SweetAlert — click OK or wait for auto-dismiss."""
        try:
            self.click(self.SWEET_ALERT_CONFIRM_BTN)
            self.wait_seconds(0.5)
        except Exception:
            # Button may auto-dismiss — wait briefly
            self.wait_seconds(3)

    def wait_for_success_alert_to_dismiss(self, timeout=5):
        """Wait for the success toast to auto-dismiss."""
        log.info("Waiting for success toast to dismiss...")
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.invisibility_of_element_located((By.CSS_SELECTOR, ".swal2-popup"))
            )
            log.info("Success toast dismissed")
        except Exception:
            log.warning("Success toast did not dismiss within timeout")

    # ================================================================
    # FORM — State Checks
    # ================================================================

    def is_form_open(self):
        """Check if the Bank form popup is currently visible."""
        return self.is_displayed(self.FORM_POPUP, timeout=5)

    def wait_for_form_to_open(self, timeout=10):
        """Wait until the form popup appears."""
        try:
            self.wait_for_visible(self.FORM_POPUP, timeout=timeout)
            log.info("Form popup is now open")
        except Exception:
            log.error("Form popup did not open within timeout")
            self.take_screenshot("bank_form_not_opened")
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
        """Check if a form field is disabled (used for View mode)."""
        try:
            element = self.find_element(locator)
            disabled = element.get_attribute("disabled")
            aria_disabled = element.get_attribute("aria-disabled")
            return disabled == "true" or disabled == "" or aria_disabled == "true"
        except Exception:
            return False

    def is_form_in_view_mode(self):
        """Check if the form is in View mode (no Submit/Update button visible)."""
        try:
            return not self.is_displayed(self.SUBMIT_BUTTON, timeout=3)
        except Exception:
            return True

    # ================================================================
    # TABLE — Read Data
    # ================================================================

    def get_table_row_count(self):
        """Get the number of data rows in the Bank list table."""
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
            3 = Bank Name
            4 = Account Number
            5 = IFSC Code
            6 = Status
        """
        cell_locator = self._table_cell(row_index, col_index)
        return self.get_text(cell_locator)

    def find_row_by_name(self, name):
        """Find a table row index by matching the Bank Name column.

        Returns: 0-based row index, or -1 if not found.
        """
        row_count = self.get_table_row_count()
        for i in range(row_count):
            cell_text = self.get_cell_text(i, 3)  # Bank Name is column 3
            if cell_text.strip().lower() == name.strip().lower():
                log.info(f"Found '{name}' at row {i}")
                return i
        log.warning(f"Record '{name}' not found in visible rows")
        return -1

    def is_record_present(self, name):
        """Check if a bank record exists in the table by name."""
        return self.find_row_by_name(name) != -1

    def get_bank_name_from_row(self, row_index):
        """Get the Bank Name value from a specific row (column 3)."""
        return self.get_cell_text(row_index, 3)

    def get_account_number_from_row(self, row_index):
        """Get the Account Number value from a specific row (column 4)."""
        return self.get_cell_text(row_index, 4)

    def get_ifsc_code_from_row(self, row_index):
        """Get the IFSC Code value from a specific row (column 5)."""
        return self.get_cell_text(row_index, 5)

    def get_status_from_row(self, row_index):
        """Get the Status value from a specific row (column 6)."""
        return self.get_cell_text(row_index, 6)

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
        """Click the History button on a specific row (opens side panel)."""
        log.info(f"Clicking History button on row {row_index}")
        self.click(self._history_button(row_index))
        self.wait_for_history_panel()

    # ================================================================
    # REFRESH / RELOAD TABLE
    # ================================================================

    def refresh_table(self):
        """Click the Refresh button to reload the table data."""
        log.info("Refreshing Bank table...")
        try:
            refresh_btn = ("xpath", "//div[@mattooltip='REFRESH']//button")
            self.click(refresh_btn)
            self.wait_seconds(2)
            log.info("Table refreshed")
        except Exception:
            log.warning("Refresh button not found, falling back to page refresh")
            self.navigate_to_bank()
            self.wait_seconds(2)

    # ================================================================
    # SEARCH (Atomic JS — input destroyed/recreated on toggle)
    # ================================================================

    def _do_js_search(self, text):
        """Execute search using atomic JavaScript.

        Bank search input (input[placeholder='Search']) is destroyed and
        recreated each time the search toggle is clicked. Uses atomic JS
        to avoid stale element issues.
        """
        # Open search bar if not visible
        self.driver.execute_script("""
            var btn = document.querySelector('button.search-btn');
            if (btn) btn.click();
        """)
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='Search']"))
        )
        self.wait_seconds(1)

        # Atomic JS: clear + type + Enter all in one call
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
        """Search for a bank record by name.

        Args:
            name: Search text.
            exact: If True, verifies EXACT name match in results.
                   If False, returns True if ANY results found (contains match).

        Returns: True if matching results found, False otherwise.
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
                        ("xpath", "(//table[contains(@class,'mat-mdc-table')]//tbody//tr)[1]/td[4]")
                    ).strip()
                except Exception:
                    first_name = "(could not read)"
                log.info(f"Search found {row_count} result(s), first: '{first_name}'")
                return True

            # Exact mode: scan ALL visible rows
            name_lower = name.strip().lower()
            for i in range(row_count):
                try:
                    row_name = self.get_text(
                        ("xpath", f"(//table[contains(@class,'mat-mdc-table')]//tbody//tr)[{i + 1}]/td[4]")
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
            log.warning("JS clear failed, navigating to bank page")
            self.navigate_to_bank()

    # ================================================================
    # HISTORY SIDE PANEL (NOT popup!)
    # ================================================================

    def wait_for_history_panel(self, timeout=10):
        """Wait for the History side panel to open and load."""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, ".popup-content"))
            )
            self.wait_seconds(1)
            log.info("History side panel opened")
        except Exception:
            log.warning("History panel did not open within timeout")
            self.take_screenshot("bank_history_panel_not_opened")

    def get_history_title(self):
        """Get the title text from the History side panel."""
        try:
            return self.get_text(self.HISTORY_TITLE)
        except Exception:
            return ""

    def get_history_row_count(self):
        """Get the number of data rows in the history table."""
        try:
            rows = self.find_elements(self.HISTORY_TABLE_ROWS)
            count = len(rows)
            log.info(f"History table has {count} data row(s)")
            return count
        except Exception:
            return 0

    def is_history_panel_open(self, timeout=5):
        """Check if the History side panel is currently visible."""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, ".popup-content"))
            )
            return True
        except Exception:
            return False

    def is_history_empty(self):
        """Check if the History panel shows 'No data available'."""
        try:
            return self.is_displayed(self.HISTORY_NO_DATA, timeout=3)
        except Exception:
            return False

    def close_history_panel(self):
        """Close the History side panel via Cancel button."""
        log.info("Closing History side panel")
        try:
            self.click(self.HISTORY_CANCEL_BTN)
            self.wait_seconds(1)
            log.info("History panel closed")
        except Exception:
            log.warning("Could not click history Cancel button")

    # ================================================================
    # SERVER-SIDE VALIDATION CHECK
    # ================================================================

    def check_server_error_alert(self, timeout=5):
        """Check if a server-side validation error alert appeared (e.g., 'Invalid IFSC').

        Returns: Alert title string, or empty string if no alert.
        """
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, ".swal2-popup"))
            )
            title = self.get_text(self.SWEET_ALERT_TITLE)
            if title and "Validation Failed" not in title:
                log.info(f"Server validation alert: {title}")
                return title
        except Exception:
            pass
        return ""