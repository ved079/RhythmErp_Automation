"""
season_page.py
--------------
Page Object Model for RhythmERP Season screen (Common Settings).
Extends BasePage with Season-specific locators and methods.

Optimised (v3) — UOM-pattern speed improvements:
- hard_refresh() for fast page reset (Ctrl+R instead of full URL load)
- Pure JS for ALL interactions (no Selenium click chain overhead)
- is_form_open() uses JS offsetParent check (instant, no WebDriverWait)
- search_and_verify() combines search + existence check (handles pagination)
- Eliminated most wait_seconds() calls
- clear_search() uses hard_refresh() instead of navigate_to_season()
- refresh_table() uses hard_refresh() instead of clicking Refresh button
- _click_action_menu_item() is pure JS (find row → click kebab → click menu item)

Fields: Name (required), Description (optional), Status (checkbox).
Pattern: List view + popup form (Add / Edit / View).
"""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    StaleElementReferenceException,
    ElementClickInterceptedException,
    TimeoutException,
)
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

from common.base_page import BasePage
from common.logger import log


class SeasonPage(BasePage):
    """
    Page Object for Common Settings > Season screen.
    """

    # ================================================================
    # COLUMN INDICES — 1-based for XPath td[N]
    # Live DOM: Actions=td[1], Name=td[2], Description=td[3], Status=td[4]
    # ================================================================
    COL_ACTIONS = 1
    COL_NAME = 2
    COL_DESCRIPTION = 3
    COL_STATUS = 4

    # ================================================================
    # LOCATORS — Form Popup
    # ================================================================
    FORM_POPUP = ("css", "div.edit_pop_up")
    NAME_INPUT = ("css", "input[name='Name']")
    DESCRIPTION_INPUT = ("css", "input[name='Description']")
    STATUS_CHECKBOX = ("css", "div.edit_pop_up input[type='checkbox']")
    SUBMIT_BUTTON = ("css", "div.popup-footer button[type='submit']")
    CANCEL_BUTTON = ("css", "div.popup-footer button[type='button']")
    CLOSE_X_BUTTON = ("xpath", "//div[contains(@class,'popup-actions')]//button[mat-icon[text()='close']]")

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
    ADD_BUTTON = ("css", "button.erp-add-btn")
    REFRESH_BUTTON = ("xpath", "//button[i[text()='refresh']]")
    TABLE = ("css", "table#excel-table")
    TABLE_ROWS = ("css", "table#excel-table tbody tr")

    # Search
    SEARCH_BUTTON = ("css", "button[aria-label='Search']")
    SEARCH_INPUT = ("css", "input#erpSearchInput")

    # ================================================================
    # LOCATORS - History Popup
    # ================================================================
    HISTORY_POPUP_TITLE = ("xpath", "//h3[contains(text(),'History')]")
    HISTORY_CANCEL_BUTTON = (
        "xpath",
        "//div[contains(@class,'popup-overlay')]"
        "//div[contains(@class,'popup-footer')]"
        "//span[contains(@class,'mdc-button__label') and normalize-space(text())='Cancel']/.."
    )

    # ================================================================
    # PAGE URL
    # ================================================================
    SEASON_PAGE_URL = "https://rhythmerp.algorhythms.in/#/dynamic-screens/Season"

    # ================================================================
    # NAVIGATION
    # ================================================================

    def navigate_to_season(self):
        """Navigate to Season page via direct URL."""
        log.info("Navigating to Season page")
        self.driver.get(self.SEASON_PAGE_URL)
        self._wait_for_page_ready()
        log.info("Arrived at Season page")

    def hard_refresh(self):
        """Hard refresh (Ctrl+R) — much faster than full navigate_to_season().
        Use this for resetting between operations within a test."""
        log.info("Hard refreshing page")
        self.driver.refresh()
        self._wait_for_page_ready()
        log.info("Page refreshed and ready")

    def _wait_for_page_ready(self):
        """Wait for Season page table to appear. Fast — only checks DOM presence."""
        try:
            WebDriverWait(self.driver, 15).until(
                lambda d: d.find_elements("css selector", "table#excel-table")
            )
            log.info("Page ready (table found)")
        except Exception:
            log.warning("Page ready check timed out")

    # ================================================================
    # ADD FORM — Open / Close
    # ================================================================

    def open_add_form(self):
        """Click Add button via JS — bypasses overlay/z-index issues."""
        log.info("Opening Add form")
        self.driver.execute_script("""
            var btn = document.querySelector('button.erp-add-btn');
            if (!btn) { throw new Error('Add button not found'); }
            btn.scrollIntoView({block:'center'});
            btn.click();
        """)
        # Wait for form popup to appear
        try:
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located(("css selector", "input[name='Name']"))
            )
            log.info("Add form opened")
        except Exception:
            log.warning("Add form may not have opened — Name input not found")

    def close_popup(self):
        """Close any popup by clicking Cancel button via pure JS."""
        log.info("Closing popup via Cancel")
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

    def close_form_via_cancel(self):
        """Close form via Cancel button (alias for close_popup)."""
        self.close_popup()

    def close_form_via_x(self):
        """Close form via X button using JS."""
        log.info("Closing form via X button")
        self.driver.execute_script("""
            var closeBtn = document.querySelector('div.popup-actions button mat-icon');
            if (closeBtn && closeBtn.textContent.trim() === 'close') {
                closeBtn.closest('button').click();
                return 'clicked';
            }
            // Fallback: try second button in popup-actions
            var actions = document.querySelector('div.popup-actions');
            if (actions) {
                var btns = actions.querySelectorAll('button');
                if (btns.length > 1) { btns[1].click(); return 'clicked_fallback'; }
            }
            return 'not found';
        """)

    # ================================================================
    # FORM — Fill Fields
    # ================================================================

    def enter_name(self, name):
        """Type season name into the Name field.
        Uses JS native setter to set value in one step (no intermediate empty state)
        which avoids Angular's required-field validation firing on clear.
        Works for both Add (empty field) and Edit (pre-filled field)."""
        log.info(f"Entering Name: {name}")
        self.driver.execute_script("""
            var el = document.querySelector("input[name='Name']");
            if (!el) { throw new Error('Name input not found'); }
            var nativeSet = Object.getOwnPropertyDescriptor(
                window.HTMLInputElement.prototype, 'value'
            ).set;
            nativeSet.call(el, arguments[0]);
            el.dispatchEvent(new Event('input', {bubbles: true}));
            el.dispatchEvent(new Event('change', {bubbles: true}));
            el.dispatchEvent(new Event('blur', {bubbles: true}));
        """, name)
        log.info(f"JS-set '{name}' into: {self.NAME_INPUT}")

    def enter_description(self, description):
        """Type description into the Description field.
        Uses JS native setter to set value in one step (no intermediate empty state).
        Works for both Add (empty field) and Edit (pre-filled field)."""
        if description:
            log.info(f"Entering Description: {description}")
            self.driver.execute_script("""
                var el = document.querySelector("input[name='Description']");
                if (!el) { throw new Error('Description input not found'); }
                var nativeSet = Object.getOwnPropertyDescriptor(
                    window.HTMLInputElement.prototype, 'value'
                ).set;
                nativeSet.call(el, arguments[0]);
                el.dispatchEvent(new Event('input', {bubbles: true}));
                el.dispatchEvent(new Event('change', {bubbles: true}));
                el.dispatchEvent(new Event('blur', {bubbles: true}));
            """, description)
            log.info(f"JS-set '{description}' into: {self.DESCRIPTION_INPUT}")
        else:
            log.info("Description left blank (optional field)")

    def fill_form(self, name, description=""):
        """Fill all form fields at once."""
        self.enter_name(name)
        if description:
            self.enter_description(description)

    def clear_form(self):
        """Clear all text fields in the form via JS."""
        log.info("Clearing form fields")
        self.driver.execute_script("""
            var nameInput = document.querySelector("input[name='Name']");
            var descInput = document.querySelector("input[name='Description']");
            var nativeSet = Object.getOwnPropertyDescriptor(
                window.HTMLInputElement.prototype, 'value'
            ).set;
            if (nameInput) {
                nativeSet.call(nameInput, '');
                nameInput.dispatchEvent(new Event('input', {bubbles: true}));
                nameInput.dispatchEvent(new Event('change', {bubbles: true}));
            }
            if (descInput) {
                nativeSet.call(descInput, '');
                descInput.dispatchEvent(new Event('input', {bubbles: true}));
                descInput.dispatchEvent(new Event('change', {bubbles: true}));
            }
        """)

    # ================================================================
    # FORM — Submit / Update (pure JS, fast)
    # ================================================================

    def _js_click_popup_button(self, button_text):
        """Click a popup footer button (Submit/Update) via pure JS."""
        self.driver.execute_script("""
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
            throw new Error('Button "' + arguments[0] + '" not found in popup footer');
        """, button_text)
        log.info(f"JS-clicked {button_text}")

    def click_submit(self):
        """Click Submit button via JS. Returns 'success', 'validation', or 'unknown'."""
        log.info("Clicking Submit")
        self._js_click_popup_button('Submit')
        return self._handle_post_submit()

    def click_update(self):
        """Click Update button via JS. Returns 'success', 'validation', or 'unknown'."""
        log.info("Clicking Update")
        self._js_click_popup_button('Update')
        return self._handle_post_submit()

    def _handle_post_submit(self):
        """Handle post-submit state: check for validation alert or form close.

        Fast: checks SweetAlert via JS offsetParent (no WebDriverWait), then
        checks form popup visibility via JS.
        """
        # Brief pause for Angular to process
        time.sleep(0.5)

        # Check for validation alert via JS (instant, no WebDriverWait)
        if self.is_validation_alert_present(timeout=3):
            alert_title = self.get_alert_title()
            alert_msg = self.get_alert_message()
            log.info(f"Validation alert detected after submit — Title: '{alert_title}', Msg: '{alert_msg}'")
            # Debug: deep Angular state inspection
            debug_info = self.driver.execute_script("""
                var result = {};
                // DOM values
                var nameEl = document.querySelector("input[name='Name']");
                var descEl = document.querySelector("input[name='Description']");
                result.dom_name = nameEl ? nameEl.value : 'NOT_FOUND';
                result.dom_desc = descEl ? descEl.value : 'NOT_FOUND';

                // mat-error elements
                var errors = document.querySelectorAll('mat-error, .mat-mdc-form-field-error');
                result.mat_errors = [];
                for (var i = 0; i < errors.length; i++) {
                    result.mat_errors.push(errors[i].textContent.trim());
                }

                // ng-invalid classes
                var invalids = document.querySelectorAll('.ng-invalid, .ng-touched');
                result.ng_invalid_count = invalids.length;
                result.ng_invalid_details = [];
                for (var i = 0; i < invalids.length; i++) {
                    var el = invalids[i];
                    var tag = el.tagName + (el.getAttribute('name') ? '[name=' + el.getAttribute('name') + ']' : '');
                    var classes = el.className;
                    if (typeof classes === 'string' && (classes.indexOf('ng-invalid') !== -1 || classes.indexOf('ng-touched') !== -1)) {
                        result.ng_invalid_details.push(tag + ' -> ' + classes.substring(0, 200));
                    }
                }

                // Angular FormControl state (if accessible)
                try {
                    var formEl = document.querySelector('form');
                    if (formEl) {
                        var ngControl = formEl.__ngContext__;
                        result.has_ng_context = !!ngControl;
                    }
                } catch(e) { result.ng_context_error = e.message; }

                // Check all form inputs
                var allInputs = document.querySelectorAll('.edit_pop_up input, .edit_pop_up textarea, .edit_pop_up select');
                result.all_inputs = [];
                for (var i = 0; i < allInputs.length; i++) {
                    var inp = allInputs[i];
                    result.all_inputs.push({
                        name: inp.getAttribute('name') || inp.getAttribute('formcontrolname') || 'unnamed',
                        type: inp.type || inp.tagName,
                        value: inp.value,
                        required: inp.required,
                        disabled: inp.disabled,
                        readOnly: inp.readOnly,
                        classes: (inp.className || '').substring(0, 150)
                    });
                }

                return result;
            """)
            log.info(f"DEBUG DOM values: Name='{debug_info.get('dom_name')}', Desc='{debug_info.get('dom_desc')}'")
            log.info(f"DEBUG mat_errors: {debug_info.get('mat_errors')}")
            log.info(f"DEBUG ng_invalid: count={debug_info.get('ng_invalid_count')}, details={debug_info.get('ng_invalid_details')}")
            log.info(f"DEBUG all_inputs: {debug_info.get('all_inputs')}")
            return "validation"

        # Wait for form to close (success path) — poll via JS
        if self._wait_for_form_close_js(timeout=8):
            self._dismiss_any_sweet_alert()
            log.info("Submit successful — form closed")
            return "success"

        # Double-check for delayed validation alert
        if self.is_validation_alert_present(timeout=2):
            return "validation"

        log.warning("Form did not close and no validation alert after submit")
        return "unknown"

    def _wait_for_form_close_js(self, timeout=8):
        """Wait for form popup to close using JS check (faster than WebDriverWait)."""
        end_time = time.monotonic() + timeout
        while time.monotonic() < end_time:
            visible = self.driver.execute_script("""
                var popup = document.querySelector('div.edit_pop_up');
                return popup && popup.offsetParent !== null;
            """)
            if not visible:
                return True
            time.sleep(0.3)
        return False

    # ================================================================
    # SWEET ALERT — Detection & Handling (JS-first, fast)
    # ================================================================

    def is_validation_alert_present(self, timeout=3):
        """Check for SweetAlert validation popup via JS (fast poll)."""
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
            time.sleep(0.2)
        return False

    def is_success_alert_present(self, timeout=3):
        """Check for SweetAlert success popup via JS."""
        end_time = time.monotonic() + timeout
        while time.monotonic() < end_time:
            try:
                visible = self.driver.execute_script("""
                    var el = document.querySelector('.swal2-popup');
                    if (!el || el.offsetParent === null) return false;
                    var title = el.querySelector('.swal2-title');
                    if (!title) return false;
                    var t = title.textContent.toLowerCase();
                    return t.indexOf('success') !== -1 || t.indexOf('successfully') !== -1;
                """)
                if visible:
                    return True
            except Exception:
                pass
            time.sleep(0.2)
        return False

    def get_alert_title(self):
        """Get SweetAlert title text via JS."""
        return self.driver.execute_script("""
            var el = document.querySelector('.swal2-title');
            return el ? el.textContent.trim() : '';
        """)

    def get_alert_message(self):
        """Get SweetAlert message text via JS."""
        return self.driver.execute_script("""
            var el = document.querySelector('.swal2-html-container');
            return el ? el.textContent.trim() : '';
        """)

    def handle_validation_alert(self):
        """Dismiss Validation Failed alert via JS."""
        log.info("Dismissing validation alert")
        self.driver.execute_script("""
            var cancel = document.querySelector('.swal2-cancel');
            if (cancel) { cancel.click(); return 'Cancel'; }
            var confirm = document.querySelector('.swal2-confirm');
            if (confirm) { confirm.click(); return 'OK'; }
            return 'none';
        """)
        # Wait for SweetAlert to disappear
        try:
            WebDriverWait(self.driver, 2).until(
                EC.invisibility_of_element_located(("css selector", ".swal2-popup"))
            )
        except Exception:
            pass

    def handle_success_alert(self):
        """Handle SweetAlert success notification — fast dismiss."""
        log.info("Handling success alert")
        try:
            WebDriverWait(self.driver, 3).until(
                EC.visibility_of_element_located(("css selector", ".swal2-container"))
            )
            self.driver.execute_script("""
                var btn = document.querySelector('.swal2-confirm');
                if (btn) btn.click();
            """)
            try:
                WebDriverWait(self.driver, 3).until(
                    EC.invisibility_of_element_located(("css selector", ".swal2-container"))
                )
            except Exception:
                pass
        except Exception:
            pass  # SweetAlert may have auto-dismissed

    def _dismiss_any_sweet_alert(self):
        """Dismiss any SweetAlert popup via JS."""
        self.driver.execute_script("""
            var cancel = document.querySelector('.swal2-cancel');
            if (cancel) { cancel.click(); return 'Cancel'; }
            var confirm = document.querySelector('.swal2-confirm');
            if (confirm) { confirm.click(); return 'OK'; }
            return 'none';
        """)

    # ================================================================
    # FORM — State Checks (JS-first, instant)
    # ================================================================

    def is_form_open(self):
        """Check if form popup is open via JS (instant, no WebDriverWait)."""
        return self.driver.execute_script("""
            var el = document.querySelector("input[name='Name']");
            return el && el.offsetParent !== null;
        """)

    def wait_for_form_to_open(self, timeout=5):
        """Wait until the form popup appears (JS poll)."""
        end_time = time.monotonic() + timeout
        while time.monotonic() < end_time:
            if self.is_form_open():
                return
            time.sleep(0.2)
        raise TimeoutException("Form popup did not open within timeout")

    def wait_for_form_to_close(self, timeout=8):
        """Wait until the form popup disappears (JS poll)."""
        self._wait_for_form_close_js(timeout)

    def is_field_disabled(self, locator):
        """Check if a form field is disabled (for View mode)."""
        css = locator[1] if locator[0] == "css" else ""
        if not css:
            return False
        return self.driver.execute_script("""
            var el = document.querySelector(arguments[0]);
            if (!el) return false;
            return el.disabled || el.getAttribute('aria-disabled') === 'true'
                || el.getAttribute('readonly') === 'true';
        """, css)

    def is_form_in_view_mode(self):
        """Check if form is in View mode (no Submit/Update button visible)."""
        return self.driver.execute_script("""
            var btn = document.querySelector("div.popup-footer button[type='submit']");
            return !btn || btn.offsetParent === null;
        """)

    # ================================================================
    # TABLE — Read Data
    # ================================================================

    def get_table_row_count(self):
        """Get row count via JS (instant)."""
        rows = self.driver.find_elements("css selector", "table#excel-table tbody tr")
        return len(rows)

    def get_cell_text(self, row_index, col_index):
        """Get cell text via JS (avoids StaleElementReferenceException)."""
        return self.driver.execute_script("""
            var rows = document.querySelectorAll('table#excel-table tbody tr');
            if (arguments[0] >= rows.length) return '';
            var cells = rows[arguments[0]].querySelectorAll('td');
            if (arguments[1] - 1 >= cells.length) return '';
            return cells[arguments[1] - 1].textContent.trim();
        """, row_index, col_index)

    def find_row_by_name(self, name):
        """Find row index by Name column via JS (instant, no per-row Selenium calls)."""
        return self.driver.execute_script("""
            var rows = document.querySelectorAll('table#excel-table tbody tr');
            var searchName = arguments[0].trim().toLowerCase();
            for (var i = 0; i < rows.length; i++) {
                var cells = rows[i].querySelectorAll('td');
                if (cells.length >= 2) {
                    var cellText = cells[1].textContent.trim().toLowerCase();
                    if (cellText === searchName) return i;
                }
            }
            return -1;
        """, name)

    def is_record_present(self, name):
        """Check if a season record exists by Name."""
        return self.find_row_by_name(name) != -1

    def get_name_from_row(self, row_index):
        return self.get_cell_text(row_index, self.COL_NAME)

    def get_description_from_row(self, row_index):
        return self.get_cell_text(row_index, self.COL_DESCRIPTION)

    def get_status_from_row(self, row_index):
        return self.get_cell_text(row_index, self.COL_STATUS)

    # ================================================================
    # TABLE — Row Actions via Kebab Menu (pure JS, fast)
    # ================================================================

    def _click_action_menu_item(self, name, action_name):
        """Click a kebab menu item (View/Edit/History) for a row found by Name.
        Pure JS — finds row, clicks kebab, then clicks menu item. No Selenium."""
        log.info(f"Clicking {action_name} via kebab menu for: {name}")

        # Step 1: Find the row and click the kebab menu button
        result = self.driver.execute_script("""
            var table = document.querySelector('table#excel-table');
            if (!table) { throw new Error('Table not found'); }
            var rows = table.querySelectorAll('tbody tr');
            var searchName = arguments[0].trim().toLowerCase();
            for (var i = 0; i < rows.length; i++) {
                var cells = rows[i].querySelectorAll('td');
                for (var j = 0; j < cells.length; j++) {
                    if (cells[j].textContent.trim().toLowerCase() === searchName) {
                        var menuBtn = rows[i].querySelector('button.erp-row-trigger');
                        if (!menuBtn) { throw new Error('Kebab button not found in row'); }
                        menuBtn.scrollIntoView({block:'center'});
                        menuBtn.click();
                        return 'menu_opened';
                    }
                }
            }
            throw new Error('Row with name "' + arguments[0] + '" not found in table');
        """, name)

        # Step 2: Wait for CDK overlay dropdown to render
        try:
            WebDriverWait(self.driver, 2).until(
                EC.presence_of_element_located(("css selector", ".cdk-overlay-pane .mat-mdc-menu-item"))
            )
        except Exception:
            pass

        # Step 3: Click the specific menu item from the overlay
        result = self.driver.execute_script("""
            var overlay = document.querySelector('.cdk-overlay-container');
            if (!overlay) { throw new Error('CDK overlay not found after menu click'); }
            var items = overlay.querySelectorAll('button, span, div');
            for (var i = 0; i < items.length; i++) {
                var text = items[i].textContent.trim();
                if (text === arguments[0]) {
                    items[i].click();
                    return 'clicked_' + arguments[0];
                }
            }
            // Fallback: partial match
            for (var i = 0; i < items.length; i++) {
                var text = items[i].textContent.trim().toLowerCase();
                if (text.indexOf(arguments[0].toLowerCase()) !== -1) {
                    items[i].click();
                    return 'clicked_partial_' + arguments[0];
                }
            }
            throw new Error('Menu item "' + arguments[0] + '" not found in dropdown');
        """, action_name)
        log.info(f"Clicked {action_name} for {name}")

    def click_view_button(self, name):
        """Click View on a row found by Name."""
        self._click_action_menu_item(name, "View")
        self.wait_for_form_to_open()

    def click_edit_button(self, name):
        """Click Edit on a row found by Name."""
        self._click_action_menu_item(name, "Edit")
        self.wait_for_form_to_open()

    def click_history_button(self, name):
        """Click History on a row found by Name."""
        self._click_action_menu_item(name, "History")
        self.wait_for_history_popup()

    # Legacy row_index-based methods (kept for backward compat)
    def click_view_button_by_index(self, row_index=0):
        """Click View on row by index (legacy)."""
        name = self.get_name_from_row(row_index)
        self.click_view_button(name)

    def click_edit_button_by_index(self, row_index=0):
        """Click Edit on row by index (legacy)."""
        name = self.get_name_from_row(row_index)
        self.click_edit_button(name)

    def click_history_button_by_index(self, row_index=0):
        """Click History on row by index (legacy)."""
        name = self.get_name_from_row(row_index)
        self.click_history_button(name)

    # ================================================================
    # HISTORY POPUP
    # ================================================================

    def is_history_popup_open(self, timeout=5):
        """Check if History popup is open via JS."""
        end_time = time.monotonic() + timeout
        while time.monotonic() < end_time:
            visible = self.driver.execute_script("""
                var el = document.querySelector('app-dynamic-history h3, div.popup-overlay h3');
                if (!el) return false;
                return el.textContent.indexOf('History') !== -1 && el.offsetParent !== null;
            """)
            if visible:
                return True
            time.sleep(0.2)
        return False

    def wait_for_history_popup(self, timeout=10):
        """Wait for History popup to open and content to settle."""
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda d: d.execute_script("""
                    var el = document.querySelector('app-dynamic-history h3, div.popup-overlay h3');
                    if (!el) return false;
                    return el.textContent.indexOf('History') !== -1 && el.offsetParent !== null;
                """)
            )
            log.info("History popup opened")
        except Exception:
            log.error("History popup did not open")
            raise

    def get_history_title(self):
        """Get History popup title via JS."""
        return self.driver.execute_script("""
            var el = document.querySelector('app-dynamic-history h3, div.popup-overlay h3');
            return el ? el.textContent.trim() : '';
        """)

    def get_history_row_count(self):
        """Get number of rows in the history table via JS."""
        rows = self.driver.find_elements("css selector", "div.popup-overlay .scrollable-table-container tr")
        return len(rows)

    def get_history_cell_text(self, row_index, col_index):
        """Get cell text from history table."""
        try:
            rows = self.driver.find_elements("css selector", "div.popup-overlay .scrollable-table-container tr")
            if row_index < len(rows):
                cells = rows[row_index].find_elements("css selector", "td, th")
                if col_index < len(cells):
                    return cells[col_index].text.strip()
            return "ROW_NOT_FOUND"
        except Exception:
            return "ROW_NOT_FOUND"

    def close_history_popup(self):
        """Close History popup via JS."""
        log.info("Closing History popup")
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
        """)

    def close_history_via_cancel(self):
        """Close History popup via Cancel button (alias)."""
        self.close_history_popup()

    def search_in_history(self, text):
        """Search within History popup via JS."""
        log.info(f"Searching in history for: {text}")
        self.driver.execute_script("""
            var input = document.querySelector('div.popup-overlay #erpSearchInput');
            if (!input) {
                var btn = document.querySelector('div.popup-overlay button[aria-label="Search"]');
                if (btn) btn.click();
            }
        """)
        time.sleep(0.5)

        self.driver.execute_script("""
            var input = document.querySelector('div.popup-overlay #erpSearchInput');
            if (!input) input = document.querySelector('div.popup-overlay input[type="text"]');
            if (input) {
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
            }
        """, text)
        time.sleep(1)

    # ================================================================
    # REFRESH / RELOAD (fast)
    # ================================================================

    def refresh_table(self):
        """Refresh table via hard_refresh (fast — Ctrl+R instead of clicking Refresh button)."""
        self.hard_refresh()

    # ================================================================
    # SEARCH (pure JS, fast)
    # ================================================================

    def search_record(self, text, exact=False):
        """Search for a record. Uses JS for all interactions.
        Returns True if found."""
        log.info(f"Searching for: {text} (exact={exact})")

        # Open search bar if needed
        self.driver.execute_script("""
            var input = document.querySelector('#erpSearchInput');
            if (!input || input.offsetParent === null) {
                var btn = document.querySelector('button[aria-label="Search"]');
                if (btn) btn.click();
            }
        """)

        # Wait for search input to appear
        try:
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located(("css selector", "#erpSearchInput"))
            )
        except Exception:
            pass

        time.sleep(0.3)

        # Clear + Type + Enter via JS
        self.driver.execute_script("""
            var input = document.querySelector('#erpSearchInput');
            if (!input) return;
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

        time.sleep(1)

        # Check results
        row_count = self.get_table_row_count()
        if row_count == 0:
            log.info(f"Search returned 0 results for '{text}'")
            return False

        if not exact:
            log.info(f"Search found {row_count} result(s)")
            return True

        # Exact mode: scan rows for exact name match (via JS)
        return self.driver.execute_script("""
            var rows = document.querySelectorAll('table#excel-table tbody tr');
            var searchName = arguments[0].trim().toLowerCase();
            for (var i = 0; i < rows.length; i++) {
                var cells = rows[i].querySelectorAll('td');
                if (cells.length >= 2) {
                    if (cells[1].textContent.trim().toLowerCase() === searchName) return true;
                }
            }
            return false;
        """, text)

    def search_and_verify(self, name):
        """Search + verify a record exists. Polls up to 10s for slow renders.
        Returns True if found."""
        log.info(f"Searching and verifying: {name}")
        self.search_record(name)
        return self.verify_record_exists(name)

    def verify_record_exists(self, name):
        """Verify a record exists in the current table view. Polls up to 10s."""
        end_time = time.monotonic() + 10
        while time.monotonic() < end_time:
            try:
                found = self.driver.execute_script("""
                    var rows = document.querySelectorAll('table#excel-table tbody tr');
                    var searchName = arguments[0].trim().toLowerCase();
                    for (var i = 0; i < rows.length; i++) {
                        var cells = rows[i].querySelectorAll('td');
                        for (var j = 0; j < cells.length; j++) {
                            if (cells[j].textContent.trim().toLowerCase().indexOf(searchName) !== -1) return true;
                        }
                    }
                    return false;
                """, name)
                if found:
                    log.info(f"Record '{name}' found in table")
                    return True
            except Exception:
                pass
            time.sleep(0.5)
        log.error(f"Record '{name}' NOT found after 10s polling")
        return False

    # ================================================================
    # OVERLAY CLEANUP (non-destructive)
    # ================================================================

    def _dismiss_overlays_and_popups(self):
        """Dismiss any open overlays/popups using Escape key."""
        # Dismiss SweetAlert first
        self._dismiss_any_sweet_alert()
        # Close any open CDK overlay or popup
        ActionChains(self.driver).send_keys(Keys.ESCAPE).perform()
        time.sleep(0.2)

    def _dismiss_any_sweet_alert(self):
        """Dismiss any SweetAlert via JS."""
        self.driver.execute_script("""
            var cancel = document.querySelector('.swal2-cancel');
            if (cancel) { cancel.click(); return; }
            var confirm = document.querySelector('.swal2-confirm');
            if (confirm) { confirm.click(); return; }
        """)

    def clear_search(self):
        """Clear search filter via hard_refresh (fast)."""
        log.info("Clearing search - hard refreshing")
        self.hard_refresh()
