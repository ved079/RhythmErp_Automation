"""
bank_page.py
-------------
Page Object Model for RhythmERP Bank screen (Common Settings).
Extends BasePage with Bank-specific locators and methods.

Fields: 10 text inputs + 2 dropdowns (Account Type, GL Account) + 2 toggles (Is Default Bank, Status).
Pattern: List view (mat-mdc-table) + popup form (Add / Edit / View) + side panel (History).
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
    # LOCATORS — Form Popup
    # ================================================================

    # --- Form Container ---
    FORM_POPUP = ("css", "div.edit_pop_up")
    FORM_CONTENT = ("css", "div.edit_pop_up div.overflow_model")
    FORM_HEADER_TITLE = ("css", "div.edit_pop_up .popup-header h3")

    # --- Form Fields (10 text inputs via input[name=...]) ---
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

    # --- Dropdowns (label-based XPath — nth-child fails because each
    #     dropdown is wrapped in its own app-dropdown-v2 component) ---
    ACCOUNT_TYPE_SELECT = ("xpath", "//mat-label[normalize-space()='Account Type']/ancestor::mat-form-field//mat-select")
    GL_ACCOUNT_SELECT = ("xpath", "//mat-label[normalize-space()='GL Account']/ancestor::mat-form-field//mat-select")

    # --- Toggles (label-based XPath — nth-child fails because each toggle
    #     is wrapped in its own app-slide-toggle-v2 component) ---
    IS_DEFAULT_BANK_TOGGLE = ("xpath", "//span[contains(@class,'main-label') and normalize-space()='Is Default Bank?']/ancestor::app-slide-toggle-v2")
    STATUS_TOGGLE = ("xpath", "//span[contains(@class,'main-label') and normalize-space()='Status']/ancestor::app-slide-toggle-v2")

    # --- Form Buttons ---
    SUBMIT_BUTTON = ("css", "div.popup-footer button[type='submit']")
    CANCEL_BUTTON = ("css", "div.popup-footer button[type='button']")

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

    # Add button (plus icon in page header / toolbar)
    ADD_BUTTON = ("xpath", "//*[@mattooltip='ADD']")

    # Data table (Angular MDC migration: mat-mdc-table, mat-mdc-row)
    TABLE = ("css", "table.mat-mdc-table")
    TABLE_BODY = ("css", "table.mat-mdc-table tbody")
    TABLE_ROWS = ("css", "table.mat-mdc-table tbody tr.mat-mdc-row")

    # Action buttons per row (View, Edit, History)
    # Column names: mat-column-view, mat-column-edit, mat-column-archive
    def _view_button(self, row_index):
        return ("xpath", f"(//table.mat-mdc-table//td[@class='mat-column-view']//button)[{row_index + 1}]")

    def _edit_button(self, row_index):
        return ("xpath", f"(//table.mat-mdc-table//td[@class='mat-column-edit']//button)[{row_index + 1}]")

    def _history_button(self, row_index):
        return ("xpath", f"(//table.mat-mdc-table//td[@class='mat-column-archive']//button)[{row_index + 1}]")

    # Table cell text (row=0-based data row, col=0-based)
    # Columns: 0=View(btn), 1=Edit(btn), 2=History(btn), 3=Bank Name, 4=Account Number, 5=IFSC Code, 6=Status
    def _table_cell(self, row, col):
        return ("xpath", f"(//table.mat-mdc-table//tbody//tr[@class='mat-mdc-row'])[{row + 1}]/td[{col + 1}]")

    # Search toggle button
    SEARCH_TOGGLE = ("css", "button.search-btn")

    # Pagination
    PAGER = ("css", "mat-paginator")
    PAGER_RANGE_LABEL = ("css", "mat-paginator .mat-mdc-paginator-range-label")
    NEXT_PAGE_BTN = ("css", "mat-paginator button[aria-label='Next page']")
    PREV_PAGE_BTN = ("css", "mat-paginator button[aria-label='Previous page']")
    FIRST_PAGE_BTN = ("css", "mat-paginator button[aria-label='First page']")
    LAST_PAGE_BTN = ("css", "mat-paginator button[aria-label='Last page']")

    # ================================================================
    # LOCATORS — History Side Panel
    # ================================================================

    # History is a SIDE PANEL (.popup-content), NOT a popup overlay
    HISTORY_PANEL = ("css", ".popup-content")
    HISTORY_TITLE = ("css", ".popup-content .popup-title")
    HISTORY_TABLE_ROWS = ("css", ".popup-content table.mat-mdc-table tbody tr")
    HISTORY_CANCEL_BTN = ("css", ".popup-content .popup-footer button[type='button']")
    HISTORY_REFRESH_BTN = ("css", ".popup-content button[mattooltip='Refresh']")
    HISTORY_SEARCH_INPUT = ("css", ".popup-content input[placeholder='Search in table']")

    # History table columns:
    # 0=View(btn), 1=Creation Time, 2=Updated Time, 3=Bank Name, 4=Account Number, 5=IFSC Code, 6=Status
    def _history_table_cell(self, row, col):
        return ("xpath", f"(.popup-content table.mat-mdc-table//tbody//tr)[{row + 1}]/td[{col + 1}]")

    # History paginator
    HISTORY_PAGER = ("css", ".popup-content mat-paginator")
    HISTORY_PAGER_RANGE_LABEL = ("css", ".popup-content mat-paginator .mat-mdc-paginator-range-label")
    HISTORY_NEXT_PAGE_BTN = ("css", ".popup-content mat-paginator button[aria-label='Next page']")

    # ================================================================
    # NAVIGATION
    # ================================================================

    def navigate_to_bank(self):
        """Navigate directly to the Bank screen via URL."""
        from data.bank_data import BANK_PAGE_URL
        log.info("Navigating to Bank screen...")
        self._recover_from_stuck_state()
        self.navigate_to(BANK_PAGE_URL)
        self.wait_seconds(2)
        try:
            self.wait_for_visible(self.TABLE, timeout=15)
            log.info("Bank screen loaded successfully")
        except Exception:
            log.warning("Table not found — page may still be loading or empty")
            self.take_screenshot("bank_page_load")

    # ================================================================
    # STUCK STATE RECOVERY
    # ================================================================

    def _recover_from_stuck_state(self):
        """Recover from any stuck popups, overlays, or alerts.

        This is called before navigation and before opening forms to
        ensure a clean state. Handles:
        - SweetAlert popups (validation/success still visible)
        - CDK overlay backdrops blocking clicks
        - Form popup still open from previous test
        - History side panel still open
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
                    document.querySelectorAll('.cdk-overlay-container').forEach(el => el.remove());
                """)
            except Exception:
                pass

            # 3. Close form popup if open
            try:
                form = self.driver.find_element(By.CSS_SELECTOR, "div.edit_pop_up")
                if form.is_displayed():
                    cancel = form.find_element(By.CSS_SELECTOR, "div.popup-footer button[type='button']")
                    if cancel.is_displayed():
                        cancel.click()
                        log.info("Recovered: Closed stuck form popup")
                        self.wait_seconds(0.5)
            except Exception:
                pass

            # 4. Close history panel if open
            try:
                panel = self.driver.find_element(By.CSS_SELECTOR, ".popup-content")
                if panel.is_displayed():
                    cancel = panel.find_element(By.CSS_SELECTOR, ".popup-footer button[type='button']")
                    if cancel.is_displayed():
                        cancel.click()
                        log.info("Recovered: Closed stuck history panel")
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

    def close_form_via_escape(self):
        """Press Escape to close the form."""
        log.info("Closing form via Escape key")
        from selenium.webdriver.common.action_chains import ActionChains
        ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
        self.wait_for_form_to_close()

    # ================================================================
    # FORM — Fill Fields (Atomic JS for Angular reactivity)
    # ================================================================

    def _set_text_field(self, locator, value):
        """Set text field value using atomic JavaScript for Angular reactivity.

        Uses nativeInputValueSetter to ensure Angular change detection fires.
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
            """, self.find_element(locator), value)
        except Exception:
            # Fallback to regular type_text
            self.type_text(locator, value, clear_first=True)

    def fill_bank_name(self, name):
        """Type bank name into the Bank Name field."""
        self._set_text_field(self.BANK_NAME_INPUT, name)

    def fill_bank_code(self, code):
        """Type bank code into the Bank Code field."""
        self._set_text_field(self.BANK_CODE_INPUT, code)

    def fill_branch_name(self, name):
        """Type branch name into the Branch Name field."""
        self._set_text_field(self.BRANCH_NAME_INPUT, name)

    def fill_branch_code(self, code):
        """Type branch code into the Branch Code field."""
        self._set_text_field(self.BRANCH_CODE_INPUT, code)

    def fill_account_number(self, number):
        """Type account number into the Account Number field."""
        self._set_text_field(self.ACCOUNT_NUMBER_INPUT, number)

    def fill_swift_number(self, swift):
        """Type SWIFT number (optional field)."""
        self._set_text_field(self.SWIFT_NUMBER_INPUT, swift)

    def fill_iban_number(self, iban):
        """Type IBAN number (optional field)."""
        self._set_text_field(self.IBAN_NUMBER_INPUT, iban)

    def fill_ifsc_code(self, ifsc):
        """Type IFSC code into the IFSC Code field."""
        self._set_text_field(self.IFSC_CODE_INPUT, ifsc)

    def fill_cash_credit_limit(self, ccl):
        """Type cash credit limit into the CCL field."""
        self._set_text_field(self.CASH_CREDIT_LIMIT_INPUT, ccl)

    def fill_bank_address(self, address):
        """Type bank address into the Bank Address field."""
        self._set_text_field(self.BANK_ADDRESS_INPUT, address)

    def fill_all_fields(self, data):
        """Fill all form fields from a data dictionary.

        Expected keys: FIELD_* constants from bank_data.py
        (Bank Name, Bank Code, Branch Name, Branch Code,
         Account Number, IFSC Code, Cash Credit Limit, Bank Address,
         Account Type, GL Account, Is Default Bank, Status).
        Optional keys: Swift Number, IBAN Number.

        Toggle values accept both boolean and string:
          bool True/False  →  auto-converted to "Yes"/"No" or "Active"/"Inactive"
        """
        from data.bank_data import (
            FIELD_BANK_NAME, FIELD_BANK_CODE, FIELD_BRANCH_NAME,
            FIELD_BRANCH_CODE, FIELD_ACCOUNT_NUMBER, FIELD_IFSC_CODE,
            FIELD_CASH_CREDIT_LIMIT, FIELD_BANK_ADDRESS,
            FIELD_SWIFT_NUMBER, FIELD_IBAN_NUMBER,
            FIELD_ACCOUNT_TYPE, FIELD_GL_ACCOUNT,
            FIELD_IS_DEFAULT_BANK, FIELD_STATUS,
        )

        # Text fields
        if FIELD_BANK_NAME in data:
            self.fill_bank_name(data[FIELD_BANK_NAME])
        if FIELD_BANK_CODE in data:
            self.fill_bank_code(data[FIELD_BANK_CODE])
        if FIELD_BRANCH_NAME in data:
            self.fill_branch_name(data[FIELD_BRANCH_NAME])
        if FIELD_BRANCH_CODE in data:
            self.fill_branch_code(data[FIELD_BRANCH_CODE])
        if FIELD_ACCOUNT_NUMBER in data:
            self.fill_account_number(data[FIELD_ACCOUNT_NUMBER])
        if FIELD_SWIFT_NUMBER in data:
            self.fill_swift_number(data[FIELD_SWIFT_NUMBER])
        if FIELD_IBAN_NUMBER in data:
            self.fill_iban_number(data[FIELD_IBAN_NUMBER])
        if FIELD_IFSC_CODE in data:
            self.fill_ifsc_code(data[FIELD_IFSC_CODE])
        if FIELD_CASH_CREDIT_LIMIT in data:
            self.fill_cash_credit_limit(data[FIELD_CASH_CREDIT_LIMIT])
        if FIELD_BANK_ADDRESS in data:
            self.fill_bank_address(data[FIELD_BANK_ADDRESS])

        # Dropdowns
        if FIELD_ACCOUNT_TYPE in data:
            self.select_account_type(data[FIELD_ACCOUNT_TYPE])
        if FIELD_GL_ACCOUNT in data:
            self.select_gl_account(data[FIELD_GL_ACCOUNT])

        # Toggles — handle both boolean and string values
        if FIELD_IS_DEFAULT_BANK in data:
            val = data[FIELD_IS_DEFAULT_BANK]
            if isinstance(val, bool):
                val = "Yes" if val else "No"
            self.set_is_default_bank(val)
        if FIELD_STATUS in data:
            val = data[FIELD_STATUS]
            if isinstance(val, bool):
                val = "Active" if val else "Inactive"
            self.set_status(val)

    def clear_form(self):
        """Clear all text fields in the form."""
        log.info("Clearing form fields")
        for field in [self.BANK_NAME_INPUT, self.BANK_CODE_INPUT,
                      self.BRANCH_NAME_INPUT, self.BRANCH_CODE_INPUT,
                      self.ACCOUNT_NUMBER_INPUT, self.SWIFT_NUMBER_INPUT,
                      self.IBAN_NUMBER_INPUT, self.IFSC_CODE_INPUT,
                      self.CASH_CREDIT_LIMIT_INPUT, self.BANK_ADDRESS_INPUT]:
            try:
                self.clear_field(field)
            except Exception:
                pass

    # ================================================================
    # DROPDOWN SELECTION
    # ================================================================
    # NOTE: Angular Material places a .cdk-overlay-backdrop over the page
    # when a dropdown opens. REMOVING this backdrop via el.remove() causes
    # Angular to close the dropdown. Instead, we use JavaScript .click()
    # on options, which fires the click event directly on the element and
    # completely bypasses the overlay interception.
    # ================================================================

    def _js_click(self, locator):
        """Click an element using JavaScript.

        Unlike Selenium's physical click (which checks if another element
        would receive the click), JS .click() fires the event directly on
        the target element — bypassing CDK overlay interception.
        """
        element = self.find_element(locator)
        self.driver.execute_script("arguments[0].click();", element)

    def _log_overlay_state(self):
        """Diagnostic: log current CDK overlay pane state.

        Call this in except blocks to understand what's in the DOM
        when dropdown selection fails.
        """
        try:
            panes = self.driver.find_elements(By.CSS_SELECTOR, ".cdk-overlay-pane")
            log.info(f"[DIAG] {len(panes)} overlay pane(s) in DOM")
            for i, pane in enumerate(panes):
                inner = pane.get_attribute('innerHTML')[:500]
                log.info(f"[DIAG] Pane {i}: {inner}")
            backdrops = self.driver.find_elements(By.CSS_SELECTOR, ".cdk-overlay-backdrop")
            log.info(f"[DIAG] {len(backdrops)} backdrop(s) in DOM")
            options = self.driver.find_elements(By.CSS_SELECTOR, "mat-option")
            log.info(f"[DIAG] {len(options)} mat-option element(s) in DOM")
        except Exception as diag_err:
            log.info(f"[DIAG] Overlay state check failed: {diag_err}")

    def select_account_type(self, account_type):
        """Select Account Type from dropdown (Current or Saving).

        Args:
            account_type: 'Current' or 'Saving'
        """
        log.step(2, f"Selecting Account Type: {account_type}")
        try:
            # Step 1: Click the dropdown trigger to open it (Selenium click)
            self.click(self.ACCOUNT_TYPE_SELECT)
            self.wait_seconds(1)

            # Step 2: Wait for the option to appear in the DOM
            #         Use PRESENCE (not visibility) — the CDK overlay does
            #         not prevent the option from being in the DOM.
            option = ("xpath", f"//mat-option//span[contains(text(),'{account_type}')]")
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(option)
            )
            self.wait_seconds(0.3)

            # Step 3: Click option via JavaScript — bypasses CDK overlay
            #         completely (no need to remove the backdrop)
            self._js_click(option)
            self.wait_seconds(0.5)
            log.info(f"Account Type set to: {account_type}")
        except Exception as e:
            log.warning(f"Account Type selection failed: {e}")
            self._log_overlay_state()

    def select_gl_account(self, search_text):
        """Select GL Account from searchable dropdown.

        Opens the dropdown, types a search term, and clicks the first
        matching option from 115+ available GL accounts.

        Args:
            search_text: Text to search for (e.g., 'Cash')
        """
        log.step(3, f"Selecting GL Account with search: {search_text}")
        try:
            # Step 1: Click the dropdown trigger to open it (Selenium click)
            self.click(self.GL_ACCOUNT_SELECT)
            self.wait_seconds(1)

            # Step 2: Wait for the dropdown panel to appear (mat-option elements)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, ".cdk-overlay-pane mat-option")
                )
            )
            self.wait_seconds(0.5)

            # Step 3: Find and type in the search input
            #         Try multiple selectors — the exact structure varies
            search_typed = False
            search_selectors = [
                ".cdk-overlay-pane mat-form-field input",
                ".cdk-overlay-pane input[type='text']",
                ".cdk-overlay-pane input",
                "mat-option input",
                ".cdk-overlay-pane input[placeholder]",
            ]
            for sel in search_selectors:
                try:
                    input_el = self.driver.find_element(By.CSS_SELECTOR, sel)
                    if input_el.is_displayed():
                        input_el.clear()
                        input_el.send_keys(search_text)
                        search_typed = True
                        log.info(f"Typed '{search_text}' in search input: {sel}")
                        break
                except Exception:
                    continue

            if not search_typed:
                # Fallback: send keys to the currently focused element
                from selenium.webdriver.common.action_chains import ActionChains
                ActionChains(self.driver).send_keys(search_text).perform()
                log.info(f"Sent '{search_text}' via ActionChains (fallback)")

            self.wait_seconds(1.5)

            # Step 4: Wait for filtered option to appear, then click via JS
            first_option = ("xpath", "(//mat-option[contains(@class,'mat-mdc-option')])[1]")
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(first_option)
            )
            self.wait_seconds(0.3)
            self._js_click(first_option)
            self.wait_seconds(0.5)
            log.info(f"GL Account set to: {search_text}")
        except Exception as e:
            log.warning(f"GL Account selection failed: {e}")
            self._log_overlay_state()

    # ================================================================
    # TOGGLE SELECTION
    # ================================================================

    def set_is_default_bank(self, value):
        """Set Is Default Bank toggle to Yes or No.

        Args:
            value: 'Yes' or 'No'
        """
        log.step(4, f"Setting Is Default Bank: {value}")
        try:
            toggle = self.find_element(self.IS_DEFAULT_BANK_TOGGLE)
            # Find the appropriate label: .state-label.on for Yes, .state-label.off for No
            if value == "Yes":
                label = toggle.find_element(By.CSS_SELECTOR, "span.state-label.on")
            else:
                label = toggle.find_element(By.CSS_SELECTOR, "span.state-label.off")
            label.click()
            self.wait_seconds(0.3)
        except Exception as e:
            log.warning(f"Is Default Bank toggle failed: {e}")

    def set_status(self, value):
        """Set Status toggle to Active or Inactive.

        Args:
            value: 'Active' or 'Inactive'
        """
        log.step(5, f"Setting Status: {value}")
        try:
            toggle = self.find_element(self.STATUS_TOGGLE)
            if value == "Active":
                label = toggle.find_element(By.CSS_SELECTOR, "span.state-label.on")
            else:
                label = toggle.find_element(By.CSS_SELECTOR, "span.state-label.off")
            label.click()
            self.wait_seconds(0.3)
        except Exception as e:
            log.warning(f"Status toggle failed: {e}")

    # ================================================================
    # FORM — Submit / Update
    # ================================================================

    def click_submit(self):
        """Click the Submit button (Add mode)."""
        log.step(6, "Clicking Submit button")
        self.click(self.SUBMIT_BUTTON)

    def click_update(self):
        """Click the Update button (Edit mode). Same element as Submit."""
        log.step(6, "Clicking Update button")
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
        """Handle success SweetAlert — click OK with CDK removal."""
        try:
            self.wait_for_visible(self.SWEET_ALERT_CONFIRM_BTN, timeout=timeout)

            # Diagnostic: log which alert we're handling
            try:
                title = self.get_text(("css", ".swal2-title"))
                log.info(f"ALERT TITLE: '{title}'")
            except Exception:
                pass

            # Remove CDK overlay backdrops that can block the confirm button
            try:
                self._remove_cdk_overlay()
                self.wait_seconds(0.3)
            except Exception:
                pass

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
        """Check if the Bank form popup is currently visible."""
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

        Bank table columns (0-indexed):
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

    def get_column_headers(self):
        """Get all column header texts from the Bank table."""
        try:
            headers = self.driver.find_elements(
                By.CSS_SELECTOR, "table.mat-mdc-table thead th"
            )
            return [h.text.strip() for h in headers if h.text.strip()]
        except Exception:
            return []

    def get_pager_range_text(self):
        """Get the paginator range label text (e.g., '1 – 10 of 65')."""
        try:
            return self.get_text(self.PAGER_RANGE_LABEL)
        except Exception:
            return ""

    def is_next_page_enabled(self):
        """Check if Next page button is enabled."""
        try:
            btn = self.find_element(self.NEXT_PAGE_BTN)
            aria_disabled = btn.get_attribute("aria-disabled")
            return aria_disabled != "true"
        except Exception:
            return False

    def is_prev_page_enabled(self):
        """Check if Previous page button is enabled."""
        try:
            btn = self.find_element(self.PREV_PAGE_BTN)
            aria_disabled = btn.get_attribute("aria-disabled")
            return aria_disabled != "true"
        except Exception:
            return False

    def is_first_page_enabled(self):
        """Check if First page button is enabled."""
        try:
            btn = self.find_element(self.FIRST_PAGE_BTN)
            aria_disabled = btn.get_attribute("aria-disabled")
            return aria_disabled != "true"
        except Exception:
            return False

    def is_last_page_enabled(self):
        """Check if Last page button is enabled."""
        try:
            btn = self.find_element(self.LAST_PAGE_BTN)
            aria_disabled = btn.get_attribute("aria-disabled")
            return aria_disabled != "true"
        except Exception:
            return False

    def click_next_page(self):
        """Click the Next page button."""
        self.click(self.NEXT_PAGE_BTN)
        self.wait_seconds(1)

    def click_prev_page(self):
        """Click the Previous page button."""
        self.click(self.PREV_PAGE_BTN)
        self.wait_seconds(1)

    def click_first_page(self):
        """Click the First page button."""
        self.click(self.FIRST_PAGE_BTN)
        self.wait_seconds(1)

    def click_last_page(self):
        """Click the Last page button."""
        self.click(self.LAST_PAGE_BTN)
        self.wait_seconds(1)

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
        self.wait_for_history_panel()

    # ================================================================
    # REFRESH / RELOAD TABLE
    # ================================================================

    def refresh_table(self):
        """Click the Refresh button to reload the table data."""
        log.info("Refreshing Bank table...")
        try:
            refresh_btn = ("xpath", "//button[mat-icon[text()='refresh']]")
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

        The search input is completely removed from DOM when closed and
        freshly injected when opened. Uses nativeInputValueSetter for
        Angular change detection.
        """
        # Toggle search bar ON
        self.driver.execute_script("""
            var toggleBtn = document.querySelector('button.search-btn');
            if (toggleBtn) toggleBtn.click();
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
        """Search for a record by bank name.

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
                        ("xpath", "(//table.mat-mdc-table//tbody//tr[@class='mat-mdc-row'])[1]/td[4]")
                    ).strip()
                except Exception:
                    first_name = "(could not read)"
                log.info(f"Search found {row_count} result(s), first: '{first_name}'")
                return True

            # Exact mode: scan all visible rows
            name_lower = name.strip().lower()
            for i in range(row_count):
                try:
                    row_name = self.get_text(
                        ("xpath", f"(//table.mat-mdc-table//tbody//tr[@class='mat-mdc-row'])[{i + 1}]/td[4]")
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
                var toggleBtn = document.querySelector('button.search-btn');
                if (toggleBtn) toggleBtn.click();
            """)
            self.wait_seconds(1)
            log.info("Search cleared via JS")
        except Exception:
            log.warning("JS clear failed, navigating to bank page")
            self.navigate_to_bank()

    # ================================================================
    # HISTORY SIDE PANEL
    # ================================================================

    def wait_for_history_panel(self, timeout=10):
        """Wait for the history side panel to open and load data."""
        try:
            self.wait_for_visible(self.HISTORY_PANEL, timeout=timeout)
            self.wait_seconds(1)
            log.info("History panel opened")
        except Exception:
            log.warning("History panel did not open within timeout")
            self.take_screenshot("history_panel_not_opened")

    def is_history_panel_open(self, timeout=5):
        """Check if the History side panel is currently visible."""
        return self.is_displayed(self.HISTORY_PANEL, timeout=timeout)

    def get_history_title(self):
        """Get the title text from the History panel."""
        try:
            return self.get_text(self.HISTORY_TITLE)
        except Exception:
            return ""

    def get_history_row_count(self):
        """Get the number of data rows in the history table.

        Note: Row 0 is the header row. Data rows start at index 1.
        """
        try:
            rows = self.find_elements(self.HISTORY_TABLE_ROWS)
            count = len(rows)
            log.info(f"History table has {count} data row(s)")
            return count
        except Exception:
            return 0

    def get_history_cell_text(self, row_index, col_index):
        """Get text from a specific history table cell.

        History columns (0-indexed):
            0 = View (button)
            1 = Creation Time
            2 = Updated Time
            3 = Bank Name
            4 = Account Number
            5 = IFSC Code
            6 = Status
        """
        cell_locator = self._history_table_cell(row_index, col_index)
        try:
            return self.get_text(cell_locator)
        except Exception:
            return "CELL_NOT_FOUND"

    def close_history_panel(self):
        """Close the History side panel."""
        log.info("Closing History panel")
        try:
            self.click(self.HISTORY_CANCEL_BTN)
            self.wait_seconds(0.5)
        except Exception:
            from selenium.webdriver.common.action_chains import ActionChains
            ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()

    def search_in_history(self, text):
        """Search within the History panel using atomic JS."""
        log.info(f"Searching in history for: {text}")
        try:
            self.driver.execute_script("""
                var panel = document.querySelector('.popup-content');
                var input = panel.querySelector('input[placeholder="Search in table"]');
                if (input) {
                    var nativeSetter = Object.getOwnPropertyDescriptor(
                        window.HTMLInputElement.prototype, 'value'
                    ).set;
                    nativeSetter.call(input, arguments[0]);
                    input.dispatchEvent(new Event('input', {bubbles: true}));
                    input.dispatchEvent(new KeyboardEvent('keydown', {
                        key: 'Enter', code: 'Enter', keyCode: 13, bubbles: true
                    }));
                }
            """, text)
            self.wait_seconds(2)
        except Exception as e:
            log.error(f"History search failed: {e}")

    def refresh_history(self):
        """Click the Refresh button inside the History panel."""
        log.info("Refreshing history panel...")
        try:
            self.click(self.HISTORY_REFRESH_BTN)
            self.wait_seconds(2)
            log.info("History panel refreshed")
        except Exception as e:
            log.warning(f"History refresh failed: {e}")

    def get_history_pager_range(self):
        """Get the history paginator range label text."""
        try:
            return self.get_text(self.HISTORY_PAGER_RANGE_LABEL)
        except Exception:
            return ""

    def is_history_next_page_enabled(self):
        """Check if history Next page button is enabled."""
        try:
            btn = self.find_element(self.HISTORY_NEXT_PAGE_BTN)
            aria_disabled = btn.get_attribute("aria-disabled")
            return aria_disabled != "true"
        except Exception:
            return False

    def click_history_next_page(self):
        """Click the Next page button inside the History panel."""
        self.click(self.HISTORY_NEXT_PAGE_BTN)
        self.wait_seconds(1)

    # ================================================================
    # FULLSCREEN
    # ================================================================

    def click_fullscreen_button(self):
        """Click the Fullscreen button in the popup header."""
        log.info("Clicking Fullscreen button")
        self.click(self.FULLSCREEN_BUTTON)
        self.wait_seconds(0.5)

    def is_fullscreen_active(self):
        """Check if the form popup is in fullscreen mode."""
        try:
            popup = self.driver.find_element(By.CSS_SELECTOR, "div.edit_pop_up")
            classes = popup.get_attribute("class") or ""
            return "fullscreen" in classes.lower() or "maximize" in classes.lower()
        except Exception:
            return False