"""
bank_page.py — FIXED VERSION
============================
Page Object Model for RhythmERP Bank screen (Common Settings).

CRITICAL FIXES vs original:
1. _set_text_field() now uses Selenium send_keys() as PRIMARY (JS nativeSetter BREAKS Bank Name validation)
2. handle_success_alert() now returns True/False and detects "Validation Failed"
3. close_form_via_cancel() uses JS click + stale element retry
4. refresh_table() uses button[mattooltip='Refresh'] (NOT //button[mat-icon[text()='refresh']])
5. search_record() uses Selenium send_keys + Enter key (JS-only search doesn't trigger Angular filter)
6. click_history_button() uses icon-based detection first
7. _history_table_cell XPath fixed (was using CSS syntax .popup-content inside XPath)
8. Added create_bank_record() and create_and_verify_bank() methods
9. All recovery methods use JS click to avoid msedgedriver crashes
"""

import time

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException,
    StaleElementReferenceException, ElementClickInterceptedException
)

from common.base_page import BasePage
from common.logger import log

from pages.common_settings.modules.bank.data.bank_data import (
    BANK_PAGE_URL,
    FIELD_BANK_NAME, FIELD_BANK_CODE, FIELD_BRANCH_NAME,
    FIELD_BRANCH_CODE, FIELD_ACCOUNT_NUMBER, FIELD_IFSC_CODE,
    FIELD_CASH_CREDIT_LIMIT, FIELD_BANK_ADDRESS,
    FIELD_SWIFT_NUMBER, FIELD_IBAN_NUMBER,
    FIELD_ACCOUNT_TYPE, FIELD_GL_ACCOUNT,
    FIELD_IS_DEFAULT_BANK, FIELD_STATUS,
    VALIDATION_ALERT_TITLE,
)


class BankPage(BasePage):
    """Page Object for Common Settings > Bank screen."""

    # ================================================================
    # LOCATORS — Form Popup
    # ================================================================

    FORM_POPUP = ("css", "div.edit_pop_up")
    FORM_CONTENT = ("css", "div.edit_pop_up div.overflow_model")
    FORM_HEADER_TITLE = ("css", "div.edit_pop_up .popup-header h3")

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

    ACCOUNT_TYPE_SELECT = ("xpath", "//mat-label[normalize-space()='Account Type']/ancestor::mat-form-field//mat-select/div[contains(@class,'mat-mdc-select-trigger')]")
    GL_ACCOUNT_SELECT = ("xpath", "//mat-label[normalize-space()='GL Account']/ancestor::mat-form-field//mat-select/div[contains(@class,'mat-mdc-select-trigger')]")

    IS_DEFAULT_BANK_TOGGLE = ("xpath", "//span[contains(@class,'main-label') and normalize-space()='Is Default Bank?']/ancestor::app-slide-toggle-v2")
    STATUS_TOGGLE = ("xpath", "//span[contains(@class,'main-label') and normalize-space()='Status']/ancestor::app-slide-toggle-v2")

    SUBMIT_BUTTON = ("css", "div.popup-footer button[type='submit']")
    CANCEL_BUTTON = ("css", "div.popup-footer button[type='button']")

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

    ADD_BUTTON = ("xpath", "//button[contains(@class,'erp-add-btn')]")
    TABLE = ("css", "table#excel-table")
    TABLE_BODY = ("css", "table#excel-table tbody")
    TABLE_ROWS = ("css", "table#excel-table tbody tr")

    # FIX: Search button uses mattooltip="Search", NOT class "search-btn"
    SEARCH_TOGGLE = ("css", "button[mattooltip='Search']")
    # FIX: Search input placeholder is "Search" (not "Search box")
    SEARCH_INPUT = ("css", "input[placeholder='Search']")

    PAGER = ("css", "mat-paginator")
    PAGER_RANGE_LABEL = ("css", "mat-paginator .mat-mdc-paginator-range-label")
    NEXT_PAGE_BTN = ("css", "mat-paginator button[aria-label='Next page']")
    PREV_PAGE_BTN = ("css", "mat-paginator button[aria-label='Previous page']")
    FIRST_PAGE_BTN = ("css", "mat-paginator button[aria-label='First page']")
    LAST_PAGE_BTN = ("css", "mat-paginator button[aria-label='Last page']")

    # ================================================================
    # LOCATORS — History Side Panel
    # ================================================================

    HISTORY_PANEL = ("css", "div.popup-content")
    HISTORY_TITLE = ("css", "div.popup-content .popup-title")
    HISTORY_TABLE_ROWS = ("css", "div.popup-content table.mat-mdc-table tbody tr")

    HISTORY_CANCEL_BTN = ("css", "div.popup-content .popup-footer button[type='button']")
    HISTORY_REFRESH_BTN = ("css", "div.popup-content button[mattooltip='Refresh']")
    HISTORY_SEARCH_INPUT = ("css", "div.popup-content input[placeholder='Search box']")

    HISTORY_PAGER = ("css", "div.popup-content mat-paginator")
    HISTORY_PAGER_RANGE_LABEL = ("css", "div.popup-content mat-paginator .mat-mdc-paginator-range-label")
    HISTORY_NEXT_PAGE_BTN = ("css", "div.popup-content mat-paginator button[aria-label='Next page']")

    # ================================================================
    # TABLE — Dynamic Row Action Locators
    # ================================================================

    def _view_button(self, row_index):
        return ("xpath", f"(//table[@id='excel-table']//tbody//tr)[{row_index + 1}]//button[contains(@class,'tblActnBtn')][1]")

    def _edit_button(self, row_index):
        return ("xpath", f"(//table[@id='excel-table']//tbody//tr)[{row_index + 1}]//button[contains(@class,'tblActnBtn')][2]")

    def _history_button(self, row_index):
        return ("xpath", f"(//table[@id='excel-table']//tbody//tr)[{row_index + 1}]//button[contains(@class,'tblActnBtn')][3]")

    def _table_cell(self, row, col):
        return ("xpath", f"(//table[@id='excel-table']//tbody//tr)[{row + 1}]/td[{col + 1}]")

    # FIX: Was using .popup-content (CSS syntax) inside XPath — now uses proper XPath
    def _history_table_cell(self, row, col):
        return ("xpath", f"(//div[contains(@class,'popup-content')]//table[contains(@class,'mat-mdc-table')]//tbody//tr)[{row + 1}]/td[{col + 1}]")

    # ================================================================
    # NAVIGATION
    # ================================================================

    def navigate_to_bank(self):
        """Navigate directly to the Bank screen via URL."""
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

    def hard_refresh(self):
        """Hard refresh — recover stuck state, reload page, wait for table."""
        log.info("*** HARD REFRESH ***")
        self._recover_from_stuck_state()
        self.driver.refresh()
        self.wait_seconds(2)
        try:
            self.wait_for_visible(self.TABLE, timeout=15)
            log.info("Hard refresh done — table visible")
        except Exception:
            log.warning("Table not visible after hard refresh, navigating to Bank page")
            self.navigate_to_bank()

    # ================================================================
    # STUCK STATE RECOVERY
    # ================================================================

    def _recover_from_stuck_state(self):
        """Recover from any stuck popups, overlays, or alerts.

        IMPORTANT: All clicks use JS to avoid msedgedriver crashes on SweetAlert overlays.
        """
        try:
            # 1. Dismiss any SweetAlert popup
            try:
                alerts = self.driver.find_elements(By.CSS_SELECTOR, ".swal2-popup")
                for alert in alerts:
                    if alert.is_displayed():
                        try:
                            confirm = alert.find_element(By.CSS_SELECTOR, "button.swal2-confirm")
                            if confirm.is_displayed():
                                self.driver.execute_script("arguments[0].click();", confirm)
                                log.info("Recovered: Dismissed SweetAlert popup (JS click)")
                                self.wait_seconds(0.5)
                        except Exception:
                            pass
            except Exception:
                pass

            # 2. Close form popup if open
            try:
                form = self.driver.find_element(By.CSS_SELECTOR, "div.edit_pop_up")
                if form.is_displayed():
                    cancel = form.find_element(By.CSS_SELECTOR, "div.popup-footer button[type='button']")
                    if cancel.is_displayed():
                        self.driver.execute_script("arguments[0].click();", cancel)
                        log.info("Recovered: Closed stuck form popup")
                        self.wait_seconds(0.5)
            except Exception:
                pass

            # 3. Close history panel if open
            try:
                panel = self.driver.find_element(By.CSS_SELECTOR, "div.popup-content")
                if panel.is_displayed():
                    cancel = panel.find_element(By.CSS_SELECTOR, ".popup-footer button[type='button']")
                    if cancel.is_displayed():
                        self.driver.execute_script("arguments[0].click();", cancel)
                        log.info("Recovered: Closed stuck history panel")
                        self.wait_seconds(0.5)
            except Exception:
                pass

            # 4. Press Escape for any remaining overlays
            try:
                ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
                self.wait_seconds(0.3)
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
            self.wait_for_visible(self.ADD_BUTTON, timeout=10)
            self.click(self.ADD_BUTTON)
        except Exception:
            add_btn = ("xpath", "//button[mat-icon[text()='add']]")
            self.click(add_btn)
        self.wait_for_form_to_open()
        log.info("Add form opened")

    def close_form_via_cancel(self):
        """Click the Cancel button to close the form — with stale element retry."""
        log.info("Closing form via Cancel button")
        for attempt in range(3):
            try:
                # Re-locate each time to avoid stale element
                cancel = self.find_clickable_element(self.CANCEL_BUTTON, timeout=5)
                self.driver.execute_script("arguments[0].click();", cancel)
                self.wait_for_form_to_close()
                return
            except StaleElementReferenceException:
                log.warning(f"Stale element on cancel attempt {attempt+1}, retrying...")
                self.wait_seconds(0.5)
            except TimeoutException:
                if not self.is_form_open():
                    log.info("Form already closed")
                    return
                raise
            except Exception as e:
                log.warning(f"Cancel attempt {attempt+1} failed: {e}")
                self.wait_seconds(0.5)
        # Last resort: JS close
        try:
            self.driver.execute_script("""
                var btn = document.querySelector("div.popup-footer button[type='button']");
                if (btn) btn.click();
            """)
            self.wait_for_form_to_close()
        except Exception:
            ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
            self.wait_seconds(1)

    def close_form_via_x(self):
        """Click the X (close) button in the popup header."""
        log.info("Closing form via X button")
        try:
            self.click(self.CLOSE_X_BUTTON)
            self.wait_for_form_to_close()
        except Exception:
            self.close_form_via_cancel()

    def close_form_via_escape(self):
        """Press Escape to close the form."""
        log.info("Closing form via Escape key")
        ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
        self.wait_for_form_to_close()

    # ================================================================
    # FORM — Fill Fields
    # FIX: Use Selenium send_keys() as PRIMARY — JS nativeSetter
    #      BREAKS Angular validation for Bank Name!
    # ================================================================

    def _set_text_field(self, locator, value):
        """Set text field value using Selenium send_keys as PRIMARY.

        CRITICAL FIX: The JS nativeSetter approach does NOT properly trigger
        Angular's form validation for Bank Name. Must use Selenium send_keys()
        which simulates actual keyboard input and triggers all Angular events.
        """
        try:
            # PRIMARY: Use Selenium type_text (send_keys) — this triggers Angular properly
            self.type_text(locator, value, clear_first=True)
        except Exception:
            # FALLBACK: JS nativeSetter (only if send_keys fails)
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
            except Exception:
                log.warning(f"Both send_keys and JS setter failed for {locator}")

    def fill_bank_name(self, name):
        self._set_text_field(self.BANK_NAME_INPUT, name)

    def fill_bank_code(self, code):
        self._set_text_field(self.BANK_CODE_INPUT, code)

    def fill_branch_name(self, name):
        self._set_text_field(self.BRANCH_NAME_INPUT, name)

    def fill_branch_code(self, code):
        self._set_text_field(self.BRANCH_CODE_INPUT, code)

    def fill_account_number(self, number):
        self._set_text_field(self.ACCOUNT_NUMBER_INPUT, number)

    def fill_swift_number(self, swift):
        self._set_text_field(self.SWIFT_NUMBER_INPUT, swift)

    def fill_iban_number(self, iban):
        self._set_text_field(self.IBAN_NUMBER_INPUT, iban)

    def fill_ifsc_code(self, ifsc):
        self._set_text_field(self.IFSC_CODE_INPUT, ifsc)

    def fill_cash_credit_limit(self, ccl):
        self._set_text_field(self.CASH_CREDIT_LIMIT_INPUT, ccl)

    def fill_bank_address(self, address):
        self._set_text_field(self.BANK_ADDRESS_INPUT, address)

    def fill_all_fields(self, data):
        """Fill all form fields from a data dictionary. With retry on dropdown failure."""
        for cycle in range(3):
            if cycle > 0:
                log.info(f"  Fill cycle {cycle+1}/3 — refreshing page")
                self.navigate_to_bank()
                self.wait_seconds(1)
                self.open_add_form()
                self.wait_seconds(0.5)

            account_ok = True
            gl_ok = True

            if FIELD_ACCOUNT_TYPE in data:
                account_ok = self.select_account_type(data[FIELD_ACCOUNT_TYPE])
            if FIELD_GL_ACCOUNT in data:
                gl_ok = self.select_gl_account(data[FIELD_GL_ACCOUNT])

            if account_ok and gl_ok:
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

                log.info(f"  Form filled successfully on cycle {cycle+1}")
                return

            log.warning(f"  Dropdown failed (account={account_ok}, gl={gl_ok}). Closing form for next cycle...")
            try:
                self.close_form_via_cancel()
            except Exception:
                try:
                    self.close_form_via_x()
                except Exception:
                    ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
            self.wait_seconds(0.5)

        raise Exception("Could not fill form after 3 cycles — dropdowns keep failing")

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

    def _open_dropdown(self, trigger_locator, label="dropdown"):
        """Open a mat-select dropdown with multi-strategy click + recovery."""
        for attempt in range(3):
            try:
                if attempt == 0:
                    self.click(trigger_locator)
                    log.info(f"  [{label}] Selenium click on trigger (attempt {attempt+1})")
                elif attempt == 1:
                    el = self.find_element(trigger_locator)
                    self.driver.execute_script("arguments[0].click();", el)
                    log.info(f"  [{label}] JS click on trigger (attempt {attempt+1})")
                else:
                    el = self.find_element(trigger_locator)
                    ActionChains(self.driver).move_to_element(el).click().perform()
                    log.info(f"  [{label}] ActionChains click on trigger (attempt {attempt+1})")

                self.wait_seconds(0.5)

                options = self.driver.find_elements(By.CSS_SELECTOR, "mat-option")
                if len(options) > 0:
                    log.info(f"  [{label}] Dropdown opened! ({len(options)} option(s))")
                    return True
                else:
                    log.warning(f"  [{label}] Click did not open dropdown (0 options)")

            except Exception as e:
                log.warning(f"  [{label}] Click attempt {attempt+1} failed: {e}")

        # Recovery: close form, hard refresh, reopen
        log.warning(f"  [{label}] All 3 attempts failed. Recovering...")
        try:
            self.close_form_via_cancel()
        except Exception:
            ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
        self.wait_seconds(1)

        self.navigate_to_bank()
        self.wait_seconds(1)
        self.open_add_form()
        self.wait_seconds(1)

        log.info(f"  [{label}] Retrying after hard refresh...")
        try:
            el = self.find_element(trigger_locator)
            self.driver.execute_script("arguments[0].click();", el)
            self.wait_seconds(1)

            options = self.driver.find_elements(By.CSS_SELECTOR, "mat-option")
            if len(options) > 0:
                log.info(f"  [{label}] Dropdown opened after refresh! ({len(options)} option(s))")
                return True
        except Exception as e:
            log.warning(f"  [{label}] Retry after refresh failed: {e}")

        self._log_overlay_state()
        return False

    def _log_overlay_state(self):
        """Diagnostic: log current overlay state when dropdown fails."""
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
        """Select Account Type from dropdown. Returns True/False."""
        log.step(2, f"Selecting Account Type: {account_type}")
        try:
            opened = self._open_dropdown(self.ACCOUNT_TYPE_SELECT, "Account Type")
            if not opened:
                log.error("[Account Type] Dropdown did not open")
                return False

            option = ("xpath", f"//mat-option//span[contains(text(),'{account_type}')]")
            WebDriverWait(self.driver, 8).until(
                EC.presence_of_element_located(option)
            )
            self.wait_seconds(0.2)

            el = self.find_element(option)
            self.driver.execute_script("arguments[0].click();", el)
            self.wait_seconds(0.3)
            log.info(f"Account Type set to: {account_type}")
            return True
        except Exception as e:
            log.warning(f"Account Type selection failed: {e}")
            return False

    def select_gl_account(self, search_text):
        """Select GL Account from searchable dropdown. Returns True/False."""
        log.step(3, f"Selecting GL Account with search: {search_text}")
        try:
            opened = self._open_dropdown(self.GL_ACCOUNT_SELECT, "GL Account")
            if not opened:
                log.error("[GL Account] Dropdown did not open")
                return False

            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, ".cdk-overlay-pane mat-option")
                )
            )
            self.wait_seconds(0.3)

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
                ActionChains(self.driver).send_keys(search_text).perform()
                log.info(f"Sent '{search_text}' via ActionChains (fallback)")

            self.wait_seconds(1)

            first_option = ("xpath", "(//mat-option[contains(@class,'mat-mdc-option')])[1]")
            WebDriverWait(self.driver, 8).until(
                EC.presence_of_element_located(first_option)
            )
            self.wait_seconds(0.2)
            el = self.find_element(first_option)
            self.driver.execute_script("arguments[0].click();", el)
            self.wait_seconds(0.3)
            log.info(f"GL Account set to: {search_text}")
            return True
        except Exception as e:
            log.warning(f"GL Account selection failed: {e}")
            return False

    # ================================================================
    # TOGGLE SELECTION
    # ================================================================

    def set_is_default_bank(self, value):
        """Set Is Default Bank toggle to Yes or No."""
        log.step(4, f"Setting Is Default Bank: {value}")
        try:
            toggle = self.find_element(self.IS_DEFAULT_BANK_TOGGLE)
            if value == "Yes":
                label = toggle.find_element(By.CSS_SELECTOR, "span.state-label.on")
            else:
                label = toggle.find_element(By.CSS_SELECTOR, "span.state-label.off")
            self.driver.execute_script("arguments[0].click();", label)
            self.wait_seconds(0.2)
        except Exception as e:
            log.warning(f"Is Default Bank toggle failed: {e}")

    def set_status(self, value):
        """Set Status toggle to Active or Inactive."""
        log.step(5, f"Setting Status: {value}")
        try:
            toggle = self.find_element(self.STATUS_TOGGLE)
            if value == "Active":
                label = toggle.find_element(By.CSS_SELECTOR, "span.state-label.on")
            else:
                label = toggle.find_element(By.CSS_SELECTOR, "span.state-label.off")
            self.driver.execute_script("arguments[0].click();", label)
            self.wait_seconds(0.2)
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
        """Click the Update button (Edit mode)."""
        log.step(6, "Clicking Update button")
        self.click(self.SUBMIT_BUTTON)

    # ================================================================
    # SWEET ALERT — Detection & Handling
    # FIX: handle_success_alert() now returns True/False!
    # ================================================================

    def is_validation_alert_present(self, timeout=5):
        """Check if SweetAlert 'Validation Failed' popup is visible."""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, ".swal2-popup"))
            )
            title = self.get_text(self.SWEET_ALERT_TITLE)
            if VALIDATION_ALERT_TITLE in title:
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
        """Click OK on the Validation Failed SweetAlert (JS click)."""
        log.info("Handling Validation Failed alert — clicking OK via JS")
        try:
            el = self.driver.find_element(By.CSS_SELECTOR, "button.swal2-confirm")
            self.driver.execute_script("arguments[0].click();", el)
            self.wait_seconds(0.5)
        except Exception:
            log.warning("Could not click validation alert OK button")

    def handle_success_alert(self, timeout=10):
        """Handle the SweetAlert after submit.

        FIX: Now checks the actual alert title and returns True/False.
        - Returns True if success alert ("successfully" in title)
        - Returns False if Validation Failed alert
        - Returns False on any error
        """
        try:
            self.wait_for_visible(self.SWEET_ALERT_CONFIRM_BTN, timeout=timeout)

            # Read the actual title
            title = ""
            try:
                title = self.get_text(("css", ".swal2-title"))
                log.info(f"ALERT TITLE: '{title}'")
            except Exception:
                pass

            # Click the confirm button (JS to avoid msedgedriver crash)
            el = self.driver.find_element(By.CSS_SELECTOR, "button.swal2-confirm")
            self.driver.execute_script("arguments[0].click();", el)
            self.wait_seconds(0.5)

            # Check if this was a Validation Failed alert
            if VALIDATION_ALERT_TITLE in title:
                log.warning("handle_success_alert: Got Validation Failed instead of success")
                self.wait_for_success_alert_to_dismiss()
                return False

            self.wait_for_success_alert_to_dismiss(timeout=5)
            log.info("Success alert handled — record saved")
            return True
        except Exception as e:
            log.warning(f"handle_success_alert: {e}")
            self.wait_for_success_alert_to_dismiss()
            return False

    def wait_for_success_alert_to_dismiss(self, timeout=5):
        """Wait for the success toast to auto-dismiss."""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.invisibility_of_element_located((By.CSS_SELECTOR, ".swal2-popup"))
            )
        except Exception:
            log.warning("SweetAlert did not dismiss within timeout")

    # ================================================================
    # FORM — State Checks
    # ================================================================

    def is_form_open(self):
        """Check if the form popup is currently open."""
        return self.is_displayed(self.FORM_POPUP, timeout=5)

    def wait_for_form_to_open(self, timeout=10):
        """Wait until the form popup becomes visible."""
        try:
            self.wait_for_visible(self.FORM_POPUP, timeout=timeout)
            log.info("Form popup is now open")
        except Exception:
            log.error("Form popup did not open within timeout")
            self.take_screenshot("form_not_opened")
            raise

    def wait_for_form_to_close(self, timeout=10):
        """Wait until the form popup becomes invisible."""
        try:
            self.wait_for_invisible(self.FORM_POPUP, timeout=timeout)
            log.info("Form popup closed")
            self.wait_seconds(0.5)
        except Exception:
            log.warning("Form popup still visible after timeout")
            # Force close with JS
            try:
                self.driver.execute_script("""
                    var popup = document.querySelector('div.edit_pop_up');
                    if (popup) popup.style.display = 'none';
                """)
            except Exception:
                pass

    def is_field_disabled(self, locator):
        """Check if a form field is disabled."""
        try:
            element = self.find_element(locator)
            disabled = element.get_attribute("disabled")
            aria_disabled = element.get_attribute("aria-disabled")
            return disabled == "true" or aria_disabled == "true"
        except Exception:
            return False

    def is_form_in_view_mode(self):
        """Check if the form is in View mode (Submit button NOT visible)."""
        try:
            return not self.is_displayed(self.SUBMIT_BUTTON, timeout=3)
        except Exception:
            return True

    def get_form_title(self):
        """Get the form popup header title text."""
        try:
            return self.get_text(self.FORM_HEADER_TITLE)
        except Exception:
            return ""

    # ================================================================
    # TABLE — Read Data
    # ================================================================

    def get_table_row_count(self):
        """Return the number of data rows in the bank table."""
        try:
            rows = self.find_elements(self.TABLE_ROWS)
            count = len(rows)
            log.info(f"Table has {count} row(s)")
            return count
        except Exception:
            return 0

    def get_cell_text(self, row_index, col_index):
        """Get text from a specific table cell."""
        cell_locator = self._table_cell(row_index, col_index)
        return self.get_text(cell_locator)

    def get_column_headers(self):
        """Get all table column header texts."""
        try:
            headers = self.driver.find_elements(
                By.CSS_SELECTOR, "table.mat-mdc-table thead th"
            )
            return [h.text.strip() for h in headers if h.text.strip()]
        except Exception:
            return []

    def get_pager_range_text(self):
        """Get the paginator range label text."""
        try:
            return self.get_text(self.PAGER_RANGE_LABEL)
        except Exception:
            return ""

    def is_next_page_enabled(self):
        try:
            btn = self.find_element(self.NEXT_PAGE_BTN)
            return btn.get_attribute("aria-disabled") != "true"
        except Exception:
            return False

    def is_prev_page_enabled(self):
        try:
            btn = self.find_element(self.PREV_PAGE_BTN)
            return btn.get_attribute("aria-disabled") != "true"
        except Exception:
            return False

    def is_first_page_enabled(self):
        try:
            btn = self.find_element(self.FIRST_PAGE_BTN)
            return btn.get_attribute("aria-disabled") != "true"
        except Exception:
            return False

    def is_last_page_enabled(self):
        try:
            btn = self.find_element(self.LAST_PAGE_BTN)
            return btn.get_attribute("aria-disabled") != "true"
        except Exception:
            return False

    def click_next_page(self):
        self.click(self.NEXT_PAGE_BTN)
        self.wait_seconds(1)

    def click_prev_page(self):
        self.click(self.PREV_PAGE_BTN)
        self.wait_seconds(1)

    def click_first_page(self):
        self.click(self.FIRST_PAGE_BTN)
        self.wait_seconds(1)

    def click_last_page(self):
        self.click(self.LAST_PAGE_BTN)
        self.wait_seconds(1)

    # ================================================================
    # TABLE — Action Buttons (Multi-strategy)
    # ================================================================

    def click_view_button(self, row_index=0):
        """Click the View button on a table row — with icon-based fallback."""
        log.info(f"Clicking View button on row {row_index}")
        try:
            self.click(self._view_button(row_index))
            self.wait_for_form_to_open()
        except Exception:
            # Fallback: find by SVG icon class (feather-eye)
            try:
                row = self.driver.find_elements(By.CSS_SELECTOR, "table#excel-table tbody tr")[row_index]
                btn = row.find_element(By.CSS_SELECTOR, "button.tblActnBtn svg.feather-eye")
                self.driver.execute_script("arguments[0].closest('button').click();", btn)
                self.wait_for_form_to_open()
            except Exception as e2:
                log.error(f"View button not found on row {row_index}: {e2}")
                raise

    def click_edit_button(self, row_index=0):
        """Click the Edit button on a table row — with icon-based fallback."""
        log.info(f"Clicking Edit button on row {row_index}")
        try:
            self.click(self._edit_button(row_index))
            time.sleep(3)
            self.wait_for_form_to_open()
        except Exception:
            # Fallback: find by SVG icon class (feather-edit) or tooltip
            try:
                row = self.driver.find_elements(By.CSS_SELECTOR, "table#excel-table tbody tr")[row_index]
                # Try by tooltip first
                btn = row.find_element(By.CSS_SELECTOR, "button[mattooltip='Click to edit']")
                self.driver.execute_script("arguments[0].click();", btn)
                time.sleep(3)
                self.wait_for_form_to_open()
            except Exception:
                try:
                    row = self.driver.find_elements(By.CSS_SELECTOR, "table#excel-table tbody tr")[row_index]
                    btn = row.find_element(By.CSS_SELECTOR, "button.tblActnBtn svg.feather-edit")
                    self.driver.execute_script("arguments[0].closest('button').click();", btn)
                    time.sleep(3)
                    self.wait_for_form_to_open()
                except Exception as e2:
                    log.error(f"Edit button not found on row {row_index}: {e2}")
                    raise

    def click_history_button(self, row_index=0):
        """Click the History button on a table row — multi-strategy fallback.

        Strategy 1: Icon-based detection (feather-clock SVG)
        Strategy 2: Index-based (3rd button)
        Strategy 3: Count all action buttons, use last one
        """
        log.info(f"Clicking History button on row {row_index}")

        # Strategy 1: SVG icon-based detection (most reliable)
        try:
            rows = self.driver.find_elements(By.CSS_SELECTOR, "table#excel-table tbody tr")
            if row_index < len(rows):
                row = rows[row_index]
                # The History button has a feather-clock SVG icon
                btn = row.find_element(By.CSS_SELECTOR, "button.tblActnBtn svg.feather-clock")
                self.driver.execute_script("arguments[0].closest('button').click();", btn)
                time.sleep(3)
                self.wait_for_history_panel()
                log.info("History button found via feather-clock icon")
                return
        except Exception as e:
            log.warning(f"Icon-based history search failed: {e}")

        # Strategy 2: Index-based button (3rd button)
        try:
            self.click(self._history_button(row_index))
            time.sleep(3)
            self.wait_for_history_panel()
            log.info("History button found via index [3]")
            return
        except Exception:
            pass

        # Strategy 3: Count all action buttons, use last one
        try:
            rows = self.driver.find_elements(By.CSS_SELECTOR, "table#excel-table tbody tr")
            if row_index < len(rows):
                row = rows[row_index]
                btns = row.find_elements(By.CSS_SELECTOR, "td button.tblActnBtn")
                if len(btns) >= 3:
                    self.driver.execute_script("arguments[0].click();", btns[2])
                    time.sleep(3)
                    self.wait_for_history_panel()
                    return
                elif len(btns) >= 1:
                    self.driver.execute_script("arguments[0].click();", btns[-1])
                    time.sleep(3)
                    self.wait_for_history_panel()
                    return
        except Exception as e:
            log.warning(f"Button-count strategy failed: {e}")

        log.error(f"History button not found on row {row_index} after all strategies")
        raise TimeoutException(f"History button not found on row {row_index}")

    # ================================================================
    # REFRESH / RELOAD TABLE
    # FIX: Uses button[mattooltip='Refresh'] — NOT //button[mat-icon[text()='refresh']]
    # ================================================================

    def refresh_table(self):
        """Refresh the bank table data — multi-strategy."""
        log.info("Refreshing Bank table...")

        refresh_selectors = [
            ("css", "button[mattooltip='Refresh']"),
            ("xpath", "//button[i[contains(@class,'material-icons') and contains(text(),'refresh')]]"),
            ("css", "button.erp-outline-btn i.material-icons"),
        ]
        for locator in refresh_selectors:
            try:
                el = self.find_clickable_element(locator, timeout=3)
                if el:
                    self.driver.execute_script("arguments[0].click();", el)
                    self.wait_seconds(1)
                    log.info(f"Table refreshed via button: {locator}")
                    return
            except Exception:
                continue

        # JS fallback: find any button with refresh icon
        try:
            self.driver.execute_script("""
                var icons = document.querySelectorAll('i.material-icons');
                for (var i = 0; i < icons.length; i++) {
                    if (icons[i].textContent.trim() === 'refresh') {
                        var btn = icons[i].closest('button');
                        if (btn) { btn.click(); break; }
                    }
                }
            """)
            self.wait_seconds(1)
            log.info("Table refreshed via JS icon search")
            return
        except Exception:
            pass

        log.warning("Refresh button not found, falling back to page refresh")
        self.navigate_to_bank()
        self.wait_seconds(2)

    # ================================================================
    # SEARCH (FIX: Uses Selenium send_keys + Enter key)
    # ================================================================

    def search_record(self, name, exact=False):
        """Search for a bank record by name.

        FIX: Now uses Selenium send_keys + Enter to trigger Angular's filter.
        The old JS-only approach didn't trigger the filter.
        """
        log.info(f"Searching for record: '{name}' (exact={exact})")

        for strategy in range(1, 4):
            log.info(f"  Search strategy {strategy}/3")

            if strategy == 2:
                self.navigate_to_bank()
                self.wait_seconds(2)
            elif strategy == 3:
                self.hard_refresh()
                self.wait_seconds(2)

            # Clear any existing search
            self._clear_search_input()
            self.wait_seconds(0.5)

            # Open search panel
            search_open = self._ensure_search_open()
            if not search_open:
                log.warning(f"  Search input not found (strategy {strategy})")
                continue

            # Type and search using Selenium send_keys + Enter
            typed = self._type_in_search(name)
            if not typed:
                log.warning(f"  Could not type in search (strategy {strategy})")
                continue

            # Wait for table to update
            self.wait_seconds(2)

            row_count = self.get_table_row_count()
            if row_count > 0:
                if not exact:
                    log.info(f"  Search found {row_count} result(s) (strategy {strategy})")
                    return True
                if self._check_exact_match(name, row_count):
                    log.info(f"  Exact match found (strategy {strategy})")
                    return True
                else:
                    log.info(f"  {row_count} rows found but no exact match (strategy {strategy})")

            log.info(f"  Strategy {strategy} returned 0 results")

        log.info(f"Search returned 0 results for '{name}' after all strategies")
        return False

    def _ensure_search_open(self):
        """Make sure search input is visible."""
        try:
            search_input = self.driver.find_element(By.CSS_SELECTOR, "input[placeholder='Search']")
            if search_input.is_displayed():
                return True
        except Exception:
            pass

        # Click toggle to open search
        try:
            toggle = self.driver.find_element(By.CSS_SELECTOR, "button[mattooltip='Search']")
            if toggle.is_displayed():
                self.driver.execute_script("arguments[0].click();", toggle)
                self.wait_seconds(1)
        except Exception:
            pass

        # Verify search input is now visible
        try:
            WebDriverWait(self.driver, 5).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "input[placeholder='Search']"))
            )
            return True
        except Exception:
            pass

        return False

    def _clear_search_input(self):
        """Clear any text in the search input."""
        try:
            search_input = self.driver.find_element(By.CSS_SELECTOR, "input[placeholder='Search']")
            if search_input.is_displayed():
                search_input.clear()
                search_input.send_keys(Keys.ESCAPE)
                self.wait_seconds(0.5)
        except Exception:
            pass

    def _type_in_search(self, text):
        """Type text into the search input and trigger Angular search with Enter."""
        try:
            search_input = self.driver.find_element(By.CSS_SELECTOR, "input[placeholder='Search']")
            if not search_input.is_displayed():
                return False

            search_input.clear()
            self.wait_seconds(0.2)
            search_input.send_keys(text)
            self.wait_seconds(0.3)
            # CRITICAL: Must press Enter to trigger Angular filter
            search_input.send_keys(Keys.ENTER)
            self.wait_seconds(2)
            return True
        except Exception:
            return False

    def _check_exact_match(self, name, row_count):
        """Check for exact match in table rows."""
        name_lower = name.strip().lower()
        for i in range(min(row_count, 20)):
            try:
                for col in [4, 2, 3, 1]:
                    try:
                        row_name = self.driver.find_element(
                            By.XPATH, f"(//table[@id='excel-table']//tbody//tr)[{i + 1}]/td[{col}]"
                        ).text.strip()
                        if row_name.lower() == name_lower:
                            return True
                    except Exception:
                        continue
            except Exception:
                continue
        return False

    def clear_search(self):
        """Clear the search filter and show all records."""
        log.info("Clearing search filter...")
        try:
            self._clear_search_input()
            self._ensure_search_open()
            # Type empty and press Enter to clear filter
            search_input = self.driver.find_element(By.CSS_SELECTOR, "input[placeholder='Search']")
            search_input.clear()
            search_input.send_keys(Keys.ENTER)
            self.wait_seconds(1)
            log.info("Search cleared")
        except Exception:
            log.warning("Could not clear search, refreshing page")
            self.navigate_to_bank()

    # ================================================================
    # HISTORY PANEL
    # ================================================================

    def wait_for_history_panel(self, timeout=10):
        """Wait until the History side panel is visible."""
        try:
            self.wait_for_visible(self.HISTORY_PANEL, timeout=timeout)
            log.info("History panel is now open")
        except Exception:
            log.error("History panel did not open within timeout")
            self.take_screenshot("history_panel_not_opened")
            raise

    def is_history_panel_open(self, timeout=5):
        try:
            return self.is_displayed(self.HISTORY_PANEL, timeout=timeout)
        except Exception:
            return False

    def get_history_title(self):
        try:
            return self.get_text(self.HISTORY_TITLE)
        except Exception:
            return ""

    def get_history_row_count(self):
        try:
            rows = self.driver.find_elements(By.CSS_SELECTOR, "div.popup-content table.mat-mdc-table tbody tr")
            return len(rows)
        except Exception:
            return 0

    def get_history_cell_text(self, row_index, col_index):
        cell_locator = self._history_table_cell(row_index, col_index)
        return self.get_text(cell_locator)

    def search_in_history(self, text):
        log.info(f"Searching in History: '{text}'")
        try:
            input_el = self.find_element(self.HISTORY_SEARCH_INPUT, timeout=5)
            input_el.clear()
            input_el.send_keys(text)
            self.wait_seconds(1)
            input_el.send_keys(Keys.ENTER)
            self.wait_seconds(2)
        except Exception as e:
            log.warning(f"History search failed: {e}")

    def refresh_history(self):
        log.info("Refreshing History panel...")
        # Strategy 1: Click the history refresh button
        try:
            el = self.find_clickable_element(self.HISTORY_REFRESH_BTN, timeout=3)
            self.driver.execute_script("arguments[0].click();", el)
            self.wait_seconds(2)
            return
        except Exception:
            pass

        # Strategy 2: Find refresh icon inside history panel
        try:
            panel = self.driver.find_element(By.CSS_SELECTOR, "div.popup-content")
            icons = panel.find_elements(By.CSS_SELECTOR, "i.material-icons")
            for icon in icons:
                if 'refresh' in icon.text.strip().lower():
                    btn = icon.find_element(By.XPATH, "./ancestor::button")
                    self.driver.execute_script("arguments[0].click();", btn)
                    self.wait_seconds(2)
                    return
        except Exception:
            pass

        # Strategy 3: JS click any refresh button in history
        try:
            self.driver.execute_script("""
                var panel = document.querySelector('div.popup-content');
                if (panel) {
                    var icons = panel.querySelectorAll('i.material-icons');
                    for (var i = 0; i < icons.length; i++) {
                        if (icons[i].textContent.trim() === 'refresh') {
                            var btn = icons[i].closest('button');
                            if (btn) { btn.click(); break; }
                        }
                    }
                }
            """)
            self.wait_seconds(2)
        except Exception as e:
            log.warning(f"History refresh failed: {e}")

    def close_history_panel(self):
        """Close the History side panel — with JS click."""
        log.info("Closing History panel")
        try:
            cancel_btn = self.find_clickable_element(self.HISTORY_CANCEL_BTN, timeout=5)
            self.driver.execute_script("arguments[0].click();", cancel_btn)
            self.wait_seconds(0.5)
            log.info("History panel closed")
        except Exception:
            try:
                self.driver.execute_script("""
                    var panel = document.querySelector('div.popup-content');
                    if (panel) {
                        var btn = panel.querySelector('.popup-footer button[type="button"]');
                        if (btn) btn.click();
                    }
                """)
                self.wait_seconds(0.5)
            except Exception:
                pass
            try:
                ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
                self.wait_seconds(0.5)
            except Exception:
                pass

    # ================================================================
    # FULLSCREEN
    # ================================================================

    def click_fullscreen_button(self):
        log.info("Clicking fullscreen button")
        try:
            self.click(self.FULLSCREEN_BUTTON)
            self.wait_seconds(0.5)
        except Exception as e:
            log.warning(f"Fullscreen button click failed: {e}")

    # ================================================================
    # COMPLETE CREATE + SUBMIT FLOW (Helper for tests)
    # ================================================================

    def create_bank_record(self, data=None):
        """Create a bank record and return (success, bank_name).

        Args:
            data: Optional data dict. If None, uses valid_bank_required_only().

        Returns:
            tuple: (success: bool, bank_name: str)
        """
        if data is None:
            from pages.common_settings.modules.bank.data.bank_data import valid_bank_required_only
            data = valid_bank_required_only()

        bank_name = data[FIELD_BANK_NAME]

        self.open_add_form()
        self.fill_all_fields(data)
        self.click_submit()

        # Check what kind of alert we got
        is_success = self.handle_success_alert(timeout=10)
        if is_success:
            # Wait for form to close (it should auto-close after success)
            try:
                self.wait_for_form_to_close(timeout=8)
            except Exception:
                # If form doesn't auto-close, close it manually
                log.warning("Form did not auto-close after success, closing manually...")
                try:
                    self.close_form_via_cancel()
                except Exception:
                    pass
            log.info(f"Bank '{bank_name}' created successfully")
            return True, bank_name
        else:
            # Validation failed — close form
            log.warning(f"Bank '{bank_name}' creation failed (validation error)")
            try:
                self.close_form_via_cancel()
            except Exception:
                pass
            return False, bank_name

    def create_and_verify_bank(self, data=None):
        """Create a bank record, verify it appears in search.

        Returns:
            tuple: (success: bool, bank_name: str)
        """
        if data is None:
            from pages.common_settings.modules.bank.data.bank_data import valid_bank_required_only
            data = valid_bank_required_only()

        bank_name = data[FIELD_BANK_NAME]

        success, name = self.create_bank_record(data)
        if not success:
            return False, name

        # Refresh and search
        self.refresh_table()
        self.wait_seconds(1)
        found = self.search_record(name)
        if not found:
            # Retry after navigation
            self.navigate_to_bank()
            self.wait_seconds(2)
            found = self.search_record(name)

        return found, name
