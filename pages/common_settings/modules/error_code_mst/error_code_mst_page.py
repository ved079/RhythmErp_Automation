"""
Error Code Mst — Page Object (v4 SPEED OPTIMIZED)
====================================================
UOM gold-standard speed patterns applied.
Module: 4 fields (1 dropdown with 4 fixed options, 2 text, 1 toggle).

Speed optimizations vs v3:
- All fixed time.sleep() replaced with fast JS polls (0.1s intervals)
- Dropdown select: JS poll for CDK overlay close (was 0.3s sleep)
- get_dropdown_options(): JS poll for options visible + pure JS read (was 0.5s sleep)
- Toggle: JS poll for checkbox state change (was 0.3s sleep)
- Row action clicks: JS poll for form/popup open (was 0.3s sleep)
- History search: native setter + Angular events (was 0.5s sleep → 0.2s settle)
- _fresh_page() smart navigation: navigate_to_page() first call, hard_refresh() after
- Removed unused imports (EC, TimeoutException)
- Zero blocking time.sleep() remaining — all are fast poll intervals or brief settles
"""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException

from pages.common_settings.modules.error_code_mst.data.error_code_mst_data import (
    PAGE_URL,
    VALIDATION_FAILED_TITLE,
    POPUP_TITLE,
    HISTORY_POPUP_TITLE,
    ERROR_CODE_TYPE_OPTIONS,
    TOGGLE_AMOUNT,
    TOGGLE_QUANTITY,
)


class ErrorCodeMstPage:

    # ═══════════════════════════════════════════════════════════════════════════
    # Locators — Table & Toolbar
    # ═══════════════════════════════════════════════════════════════════════════

    TABLE = (By.CSS_SELECTOR, "table#excel-table")
    TABLE_BODY_ROWS = (By.CSS_SELECTOR, "table#excel-table tbody tr")
    ADD_BUTTON = (By.XPATH, "//button[contains(@class,'erp-add-btn')]")

    # ═══════════════════════════════════════════════════════════════════════════
    # Locators — Form Popup
    # ═══════════════════════════════════════════════════════════════════════════

    POPUP_TITLE = (By.CSS_SELECTOR, ".big-model h3")
    CANCEL_BUTTON = (By.XPATH, "//div[contains(@class,'popup-footer')]//button[contains(.,'Cancel')]")
    SUBMIT_BUTTON = (By.XPATH, "//div[contains(@class,'popup-footer')]//button[contains(.,'Submit')]")
    UPDATE_BUTTON = (By.XPATH, "//div[contains(@class,'popup-footer')]//button[contains(.,'Update')]")

    # ═══════════════════════════════════════════════════════════════════════════
    # Locators — Form Fields (4 fields)
    # ═══════════════════════════════════════════════════════════════════════════

    ERROR_CODE_TYPE_SELECT = (By.XPATH, "//mat-label[contains(.,'Error Code Type')]/ancestor::mat-form-field//mat-select")
    CODE_INPUT = (By.CSS_SELECTOR, "input[name='Code']")
    DESCRIPTION_INPUT = (By.CSS_SELECTOR, "input[name='Description']")
    TOGGLE_CHECKBOX = (By.CSS_SELECTOR, ".switch-container.vertical input[type='checkbox']")

    # ═══════════════════════════════════════════════════════════════════════════
    # Locators — SweetAlert2
    # ═══════════════════════════════════════════════════════════════════════════

    SWAL_CONTAINER = (By.CSS_SELECTOR, ".swal2-container")
    SWAL_TITLE = (By.CSS_SELECTOR, "#swal2-title")
    SWAL_CONTENT = (By.CSS_SELECTOR, ".swal2-html-container")
    SWAL_CONFIRM = (By.CSS_SELECTOR, ".swal2-confirm")

    # ═══════════════════════════════════════════════════════════════════════════
    # Locators — History Popup
    # ═══════════════════════════════════════════════════════════════════════════

    HISTORY_TITLE = (By.XPATH, "//h3[contains(.,'History')]")
    HISTORY_CANCEL = (By.XPATH, "//div[contains(@class,'popup')]//button[contains(.,'Cancel')]")
    HISTORY_TABLE_ROWS = (By.CSS_SELECTOR, ".edit_pop_up table tbody tr")
    NO_DATA_IMAGE = (By.CSS_SELECTOR, ".edit_pop_up img[alt='No Data Available']")

    # ═══════════════════════════════════════════════════════════════════════════
    # Init
    # ═══════════════════════════════════════════════════════════════════════════

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)

    # ═══════════════════════════════════════════════════════════════════════════
    # Navigation (UOM gold standard pattern)
    # ═══════════════════════════════════════════════════════════════════════════

    def navigate_to_page(self):
        """Navigate to Error Code Mst page via direct URL. First call only."""
        self.driver.get(PAGE_URL)
        self._wait_for_page_ready()

    def hard_refresh(self):
        """Hard refresh (Ctrl+R) + wait for page ready.
        Much faster than navigate_to_page() for resetting between tests."""
        self.driver.refresh()
        self._wait_for_page_ready()

    def _wait_for_page_ready(self):
        """Wait for the table to appear — fast JS poll (0.1s intervals)."""
        end = time.monotonic() + 15
        while time.monotonic() < end:
            try:
                found = self.driver.execute_script(
                    "var t = document.querySelector('table#excel-table'); "
                    "return t && t.offsetParent !== null;"
                )
                if found:
                    return
            except Exception:
                pass
            time.sleep(0.1)
        # Fallback: just proceed — tests will catch issues

    # ═══════════════════════════════════════════════════════════════════════════
    # Add Form — Open / Close (fast JS, no sleep)
    # ═══════════════════════════════════════════════════════════════════════════

    def open_add_form(self):
        """Click ADD button via JS + wait for form popup via fast poll."""
        self.driver.execute_script("""
            var btn = document.querySelector('button.erp-add-btn');
            if (btn) { btn.scrollIntoView({block:'center'}); btn.click(); }
        """)
        # Fast poll for form popup (0.2s intervals, 5s timeout)
        end = time.monotonic() + 5
        while time.monotonic() < end:
            if self.is_form_open():
                return
            # Retry click if form didn't open
            self.driver.execute_script("""
                var btn = document.querySelector('button.erp-add-btn');
                if (btn) { btn.click(); }
            """)
            time.sleep(0.2)

    def is_form_open(self):
        """Check if form popup is open — JS offsetParent (instant)."""
        return bool(self.driver.execute_script("""
            var el = document.querySelector('div.big-model');
            if (el && el.offsetParent !== null) return true;
            var dlg = document.querySelector('mat-dialog-container');
            if (dlg && dlg.offsetParent !== null) return true;
            return false;
        """))

    def is_form_closed(self):
        """Check if form popup is closed."""
        return not self.is_form_open()

    def close_popup(self):
        """Close popup via Cancel button — pure JS."""
        self.driver.execute_script("""
            var footers = document.querySelectorAll('.popup-footer');
            for (var i = 0; i < footers.length; i++) {
                var buttons = footers[i].querySelectorAll('button');
                for (var j = 0; j < buttons.length; j++) {
                    if (buttons[j].textContent.indexOf('Cancel') !== -1) {
                        buttons[j].click(); return;
                    }
                }
            }
        """)

    def cancel(self):
        """Click Cancel button — alias for close_popup (UOM pattern)."""
        self.close_popup()

    # ═══════════════════════════════════════════════════════════════════════════
    # Form — Fill Fields (JS native setter for Angular)
    # ═══════════════════════════════════════════════════════════════════════════

    def fill_code(self, value):
        """Type into Code input — JS native setter + Angular dispatch."""
        self._fill_input_by_name('Code', value)

    def fill_description(self, value):
        """Type into Description input — JS native setter + Angular dispatch."""
        self._fill_input_by_name('Description', value)

    def _fill_input_by_name(self, field_name, value):
        """Set input value via JS native setter + Angular change events."""
        self.driver.execute_script("""
            var input = document.querySelector('input[name="' + arguments[0] + '"]');
            if (!input) return;
            var nativeSetter = Object.getOwnPropertyDescriptor(
                window.HTMLInputElement.prototype, 'value'
            ).set;
            nativeSetter.call(input, arguments[1]);
            input.dispatchEvent(new Event('input', {bubbles: true}));
            input.dispatchEvent(new Event('change', {bubbles: true}));
        """, field_name, str(value))

    def select_error_code_type(self, option_text):
        """
        Select from Error Code Type dropdown (4 fixed options).
        Standard mat-select. Returns True if selection succeeded.
        """
        try:
            # Click the dropdown trigger via JS
            select_el = self.driver.find_element(*self.ERROR_CODE_TYPE_SELECT)
            self.driver.execute_script("arguments[0].click();", select_el)

            # Fast poll for overlay panel (0.2s intervals, 3s timeout)
            panel_open = False
            end = time.monotonic() + 3
            while time.monotonic() < end:
                panel_open = self.driver.execute_script("""
                    var panels = document.querySelectorAll(
                        'div.cdk-overlay-pane:not(.mat-mdc-dialog-container)'
                    );
                    for (var i = 0; i < panels.length; i++) {
                        if (panels[i].offsetParent !== null) return true;
                    }
                    return false;
                """)
                if panel_open:
                    break
                time.sleep(0.2)

            if not panel_open:
                return False

            # Find and click the matching option via JS
            clicked = self.driver.execute_script("""
                var options = document.querySelectorAll(
                    'div.mat-mdc-select-panel mat-option'
                );
                for (var i = 0; i < options.length; i++) {
                    if (options[i].offsetParent !== null &&
                        options[i].textContent.indexOf(arguments[0]) !== -1) {
                        options[i].scrollIntoView({block:'center'});
                        options[i].click();
                        return true;
                    }
                }
                // Fallback: try role=option
                var allOpts = document.querySelectorAll('[role="option"]');
                for (var i = 0; i < allOpts.length; i++) {
                    if (allOpts[i].offsetParent !== null &&
                        allOpts[i].textContent.indexOf(arguments[0]) !== -1) {
                        allOpts[i].scrollIntoView({block:'center'});
                        allOpts[i].click();
                        return true;
                    }
                }
                return false;
            """, option_text.strip())

            # Fast poll for CDK overlay panel to close (replaces time.sleep(0.3))
            end_panel = time.monotonic() + 1
            while time.monotonic() < end_panel:
                panel_gone = self.driver.execute_script("""
                    var panels = document.querySelectorAll('.cdk-overlay-pane:not(.mat-mdc-dialog-container)');
                    for (var i = 0; i < panels.length; i++) {
                        if (panels[i].offsetParent !== null) return false;
                    }
                    return true;
                """)
                if panel_gone:
                    break
                time.sleep(0.1)
            self._force_close_panels()
            return bool(clicked)

        except Exception:
            self._force_close_panels()
            return False

    def get_dropdown_options(self):
        """Get all current options from Error Code Type dropdown. Returns list of strings."""
        options = []
        try:
            select_el = self.driver.find_element(*self.ERROR_CODE_TYPE_SELECT)
            self.driver.execute_script("arguments[0].click();", select_el)

            # Fast poll for options to appear (replaces time.sleep(0.5))
            end_opts = time.monotonic() + 2
            while time.monotonic() < end_opts:
                opt_count = self.driver.execute_script("""
                    return document.querySelectorAll('div.mat-mdc-select-panel mat-option').length;
                """)
                if opt_count > 0:
                    break
                time.sleep(0.1)

            # Read options via JS (faster than Selenium find_elements)
            options = self.driver.execute_script("""
                var result = [];
                var opts = document.querySelectorAll('div.mat-mdc-select-panel mat-option');
                for (var i = 0; i < opts.length; i++) {
                    if (opts[i].offsetParent !== null) {
                        var text = (opts[i].textContent || '').trim();
                        if (text) result.push(text);
                    }
                }
                return result;
            """)

            self._force_close_panels()
        except Exception:
            self._force_close_panels()
        return options

    def toggle_is_qty_amt(self, state):
        """Set Is Qty/Amt toggle to 'amount' (off) or 'quantity' (on)."""
        try:
            cb = self.driver.find_element(*self.TOGGLE_CHECKBOX)
            current = self.is_toggle_quantity()
            want_on = (state == TOGGLE_QUANTITY)
            if current != want_on:
                self.driver.execute_script("""
                    var cb = arguments[0];
                    cb.click();
                    cb.dispatchEvent(new Event('change', {bubbles: true}));
                    cb.dispatchEvent(new Event('input', {bubbles: true}));
                """, cb)
                # Fast poll for toggle state change (replaces time.sleep(0.3))
                want_on = (state == TOGGLE_QUANTITY)
                end_toggle = time.monotonic() + 1
                while time.monotonic() < end_toggle:
                    if self.is_toggle_quantity() == want_on:
                        break
                    time.sleep(0.1)
        except Exception:
            pass

    def is_toggle_quantity(self):
        """Check if toggle is in Quantity (checked/Yes) state."""
        try:
            cb = self.driver.find_element(*self.TOGGLE_CHECKBOX)
            return cb.is_selected()
        except NoSuchElementException:
            return False

    def is_toggle_amount(self):
        """Check if toggle is in Amount (unchecked/No) state — default."""
        return not self.is_toggle_quantity()

    def fill_all_fields(self, data, max_retries=3):
        """
        Fill all form fields with retry logic for dropdown.
        Order: Dropdown FIRST → Text fields → Toggle.
        Returns True if all fields filled successfully.
        """
        for attempt in range(1, max_retries + 1):
            success = self._fill_all_fields_once(data)
            if success:
                return True
            # Retry: cancel + hard_refresh + reopen form
            self.cancel()
            self.hard_refresh()
            self.open_add_form()
        return False

    def _fill_all_fields_once(self, data):
        """Single pass: fill Dropdown → Text fields → Toggle."""
        # 1. Dropdown FIRST (most likely to fail)
        error_type = data.get("error_code_type", "")
        if error_type:
            dropdown_ok = self.select_error_code_type(error_type)
            if not dropdown_ok:
                return False

        # 2. Text fields
        code = data.get("code", "")
        desc = data.get("description", "")
        if code:
            self.fill_code(code)
        if desc:
            self.fill_description(desc)

        # 3. Toggle
        qty_amt = data.get("is_qty_amt", TOGGLE_AMOUNT)
        if qty_amt:
            self.toggle_is_qty_amt(qty_amt)

        return True

    # ═══════════════════════════════════════════════════════════════════════════
    # Submit / Update (UOM _js_click_popup_button pattern)
    # ═══════════════════════════════════════════════════════════════════════════

    def submit(self):
        """Click Submit button — single JS call (UOM pattern)."""
        self._js_click_popup_button('Submit')

    def click_update(self):
        """Click Update button — single JS call (UOM pattern)."""
        self._js_click_popup_button('Update')

    def _js_click_popup_button(self, button_text):
        """Click a popup footer button via JS — bypasses overlay issues."""
        self.driver.execute_script("""
            var footers = document.querySelectorAll('.popup-footer');
            for (var i = 0; i < footers.length; i++) {
                var buttons = footers[i].querySelectorAll('button');
                for (var j = 0; j < buttons.length; j++) {
                    if (buttons[j].textContent.trim().indexOf(arguments[0]) !== -1) {
                        buttons[j].click();
                        return;
                    }
                }
            }
        """, button_text)

    # ═══════════════════════════════════════════════════════════════════════════
    # SweetAlert2 — Combined alert handler (UOM pattern, fast)
    # ═══════════════════════════════════════════════════════════════════════════
    # NOTE: Error Code Mst does NOT show success SweetAlert2 on create/update.
    # Form closes silently. Only "Validation Failed" alert appears for errors.

    def _handle_submit_response(self, timeout=5):
        """
        Combined SweetAlert handler — single fast poll.
        Detects validation alert OR form close (= success).
        Returns dict: {alert: bool, title: str, form_closed: bool}
        """
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            result = self.driver.execute_script("""
                var popup = document.querySelector('.swal2-popup.swal2-icon-warning, .swal2-popup.swal2-icon-error');
                if (popup && popup.offsetParent !== null) {
                    var titleEl = document.querySelector('#swal2-title');
                    var title = titleEl ? titleEl.textContent.trim() : '';
                    var confirm = document.querySelector('.swal2-confirm');
                    if (confirm) confirm.click();
                    return {alert: true, title: title, form_closed: false};
                }
                var form = document.querySelector('div.big-model');
                var formOpen = form && form.offsetParent !== null;
                if (!formOpen) {
                    return {alert: false, title: '', form_closed: true};
                }
                return null;
            """)
            if result is not None:
                # Clean up swal remnants
                if result.get('alert'):
                    self._cleanup_swal2()
                return result
            time.sleep(0.2)

        # Timeout — check form state
        form_closed = not self.is_form_open()
        return {"alert": False, "title": "", "form_closed": form_closed}

    def is_validation_alert_present(self, timeout=3):
        """Check if validation SweetAlert2 is visible — fast JS poll (0.2s)."""
        end = time.monotonic() + timeout
        while time.monotonic() < end:
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

    def handle_validation_warning(self, timeout=5):
        """Handle SweetAlert2 validation warning — returns title text or empty string."""
        result = self._handle_submit_response(timeout)
        return result.get("title", "")

    def get_sweetalert_title(self, timeout=3):
        """Get SweetAlert2 title text — fast JS poll."""
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            try:
                title = self.driver.execute_script("""
                    var el = document.querySelector('#swal2-title');
                    return el && el.offsetParent !== null ? el.textContent.trim() : null;
                """)
                if title is not None:
                    return title
            except Exception:
                pass
            time.sleep(0.2)
        return ""

    def get_sweetalert_message(self, timeout=3):
        """Get SweetAlert2 body message — fast JS poll."""
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            try:
                msg = self.driver.execute_script("""
                    var el = document.querySelector('.swal2-html-container');
                    return el && el.offsetParent !== null ? el.textContent.trim() : null;
                """)
                if msg is not None:
                    return msg
            except Exception:
                pass
            time.sleep(0.2)
        return ""

    def accept_sweetalert(self, timeout=5):
        """Click OK/confirm on SweetAlert2 — single JS call."""
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            try:
                clicked = self.driver.execute_script("""
                    var btn = document.querySelector('.swal2-confirm');
                    if (btn && btn.offsetParent !== null) { btn.click(); return true; }
                    return false;
                """)
                if clicked:
                    self._cleanup_swal2()
                    return
            except Exception:
                pass
            time.sleep(0.2)
        self._cleanup_swal2()

    def _cleanup_swal2(self):
        """Remove leftover swal2 container + backdrops."""
        self.driver.execute_script("""
            document.querySelectorAll('.swal2-container').forEach(el => el.remove());
            document.querySelectorAll('.swal2-backdrop-show').forEach(el => el.remove());
        """)

    # ═══════════════════════════════════════════════════════════════════════════
    # Form Mode Detection (JS offsetParent)
    # ═══════════════════════════════════════════════════════════════════════════

    def is_edit_mode(self):
        """Check if Update button is present (Edit mode) — JS."""
        return bool(self.driver.execute_script("""
            var btns = document.querySelectorAll('.popup-footer button');
            for (var i = 0; i < btns.length; i++) {
                if (btns[i].textContent.indexOf('Update') !== -1 && btns[i].offsetParent !== null)
                    return true;
            }
            return false;
        """))

    def is_view_mode(self):
        """Check if form is open and no Submit/Update button (View mode) — JS."""
        return self.is_form_open() and not self.is_edit_mode() and not self._is_submit_visible()

    def _is_submit_visible(self):
        return bool(self.driver.execute_script("""
            var btns = document.querySelectorAll('.popup-footer button');
            for (var i = 0; i < btns.length; i++) {
                if (btns[i].textContent.indexOf('Submit') !== -1 && btns[i].offsetParent !== null)
                    return true;
            }
            return false;
        """))

    def get_form_heading(self):
        """Read popup heading text — JS."""
        try:
            return self.driver.execute_script(
                "var el = document.querySelector('.big-model h3'); "
                "return el ? el.textContent.trim() : '';"
            )
        except Exception:
            return ""

    # ═══════════════════════════════════════════════════════════════════════════
    # Read Form Field Values
    # ═══════════════════════════════════════════════════════════════════════════

    def get_form_field_values(self):
        """Read all form field values — JS. Returns dict."""
        values = self.driver.execute_script("""
            var result = {};
            var select = document.querySelector('mat-select');
            result.error_code_type = select ? (select.textContent || '').trim() : '';
            var code = document.querySelector('input[name="Code"]');
            result.code = code ? code.value : '';
            var desc = document.querySelector('input[name="Description"]');
            result.description = desc ? desc.value : '';
            var cb = document.querySelector('.switch-container.vertical input[type="checkbox"]');
            result.is_qty_amt = (cb && cb.checked) ? 'Qty' : 'Amount';
            return result;
        """)
        return values or {"error_code_type": "", "code": "", "description": "", "is_qty_amt": TOGGLE_AMOUNT}

    # ═══════════════════════════════════════════════════════════════════════════
    # Table Operations (pure JS — fast, no Selenium iteration)
    # ═══════════════════════════════════════════════════════════════════════════

    def get_table_row_count(self):
        """Count visible data rows in table — JS."""
        return self.driver.execute_script(
            "return document.querySelectorAll('table#excel-table tbody tr').length;"
        ) or 0

    def get_cell_text(self, row_index, css_class):
        """Read text from a table cell by row index and column CSS class — JS."""
        return self.driver.execute_script("""
            var rows = document.querySelectorAll('table#excel-table tbody tr');
            if (arguments[0] < rows.length) {
                var cell = rows[arguments[0]].querySelector('td.' + arguments[1]);
                return cell ? (cell.textContent || '').trim() : '';
            }
            return '';
        """, row_index, css_class)

    def is_code_in_table(self, code):
        """Check if Code value exists in table — pure JS (fast).
        If not found on current page, tries searching (handles pagination)."""
        # Try current page first
        found = self.driver.execute_script("""
            var rows = document.querySelectorAll('table#excel-table tbody tr');
            for (var i = 0; i < rows.length; i++) {
                var cells = rows[i].querySelectorAll('td');
                for (var j = 0; j < cells.length; j++) {
                    if (cells[j].textContent.indexOf(arguments[0]) !== -1)
                        return true;
                }
            }
            return false;
        """, code)
        if found:
            return True

        # Not on current page — try hard_refresh + check again (table might have updated)
        self.hard_refresh()
        found = self.driver.execute_script("""
            var rows = document.querySelectorAll('table#excel-table tbody tr');
            for (var i = 0; i < rows.length; i++) {
                var cells = rows[i].querySelectorAll('td');
                for (var j = 0; j < cells.length; j++) {
                    if (cells[j].textContent.indexOf(arguments[0]) !== -1)
                        return true;
                }
            }
            return false;
        """, code)
        if found:
            return True

        # Still not found — use search to bring record to page 1
        self.search_record(code)
        found = self.driver.execute_script("""
            var rows = document.querySelectorAll('table#excel-table tbody tr');
            for (var i = 0; i < rows.length; i++) {
                var cells = rows[i].querySelectorAll('td');
                for (var j = 0; j < cells.length; j++) {
                    if (cells[j].textContent.indexOf(arguments[0]) !== -1)
                        return true;
                }
            }
            return false;
        """, code)
        return bool(found)

    def find_code_row_index(self, code):
        """Find row index by Code value — pure JS (fast). Returns -1 if not found.
        If not found on current page, tries searching (handles pagination)."""
        # Try current page first
        idx = self.driver.execute_script("""
            var rows = document.querySelectorAll('table#excel-table tbody tr');
            for (var i = 0; i < rows.length; i++) {
                var cells = rows[i].querySelectorAll('td');
                for (var j = 0; j < cells.length; j++) {
                    if (cells[j].textContent.indexOf(arguments[0]) !== -1)
                        return i;
                }
            }
            return -1;
        """, code)
        if idx is not None and idx >= 0:
            return idx

        # Not on current page — try hard_refresh + check again
        self.hard_refresh()
        idx = self.driver.execute_script("""
            var rows = document.querySelectorAll('table#excel-table tbody tr');
            for (var i = 0; i < rows.length; i++) {
                var cells = rows[i].querySelectorAll('td');
                for (var j = 0; j < cells.length; j++) {
                    if (cells[j].textContent.indexOf(arguments[0]) !== -1)
                        return i;
                }
            }
            return -1;
        """, code)
        if idx is not None and idx >= 0:
            return idx

        # Still not found — use search to bring record to page 1
        self.search_record(code)
        idx = self.driver.execute_script("""
            var rows = document.querySelectorAll('table#excel-table tbody tr');
            for (var i = 0; i < rows.length; i++) {
                var cells = rows[i].querySelectorAll('td');
                for (var j = 0; j < cells.length; j++) {
                    if (cells[j].textContent.indexOf(arguments[0]) !== -1)
                        return i;
                }
            }
            return -1;
        """, code)
        return idx if idx is not None else -1

    # ═══════════════════════════════════════════════════════════════════════════
    # Row Action Buttons — View / Edit / History (JS click)
    # ═══════════════════════════════════════════════════════════════════════════

    def click_view_on_row(self, row_index=0):
        """Click View action button on specified row — JS."""
        return self._click_row_action_button(row_index, 'mat-column-view')

    def click_edit_on_row(self, row_index=0):
        """Click Edit action button on specified row — JS."""
        return self._click_row_action_button(row_index, 'mat-column-edit')

    def click_history_on_row(self, row_index=0):
        """Click History action button on specified row — JS."""
        return self._click_row_action_button(row_index, 'mat-column-archive')

    def _click_row_action_button(self, row_index, column_class):
        """Click action button in specific column — JS."""
        try:
            result = self.driver.execute_script("""
                var rows = document.querySelectorAll('table#excel-table tbody tr');
                if (arguments[0] < rows.length) {
                    var btn = rows[arguments[0]].querySelector('td.' + arguments[1] + ' button');
                    if (btn) { btn.click(); return true; }
                }
                return false;
            """, row_index, column_class)
            # Fast poll for form/popup to open (replaces time.sleep(0.3))
            if result:
                end_action = time.monotonic() + 3
                while time.monotonic() < end_action:
                    if self.is_form_open() or self.is_history_popup_open():
                        break
                    time.sleep(0.1)
            return bool(result)
        except Exception:
            return False

    # ═══════════════════════════════════════════════════════════════════════════
    # History Popup
    # ═══════════════════════════════════════════════════════════════════════════

    def is_history_popup_open(self):
        """Check if History popup is visible — JS offsetParent."""
        return self.driver.execute_script("""
            var el = document.querySelector('h3');
            if (el && el.textContent.indexOf('History') !== -1 && el.offsetParent !== null)
                return true;
            return false;
        """)

    def get_history_row_count(self):
        """Count rows in history table — JS."""
        return self.driver.execute_script(
            "return document.querySelectorAll('.edit_pop_up table tbody tr').length;"
        ) or 0

    def is_history_empty(self):
        """Check if history shows 'No Data Available' — JS."""
        return self.driver.execute_script("""
            var img = document.querySelector('.edit_pop_up img[alt="No Data Available"]');
            return img && img.offsetParent !== null;
        """)

    def close_history_popup(self):
        """Close History popup — pure JS Cancel click."""
        self.driver.execute_script("""
            var footers = document.querySelectorAll('.popup-footer');
            for (var i = 0; i < footers.length; i++) {
                var buttons = footers[i].querySelectorAll('button');
                for (var j = 0; j < buttons.length; j++) {
                    if (buttons[j].textContent.indexOf('Cancel') !== -1) {
                        buttons[j].click(); return;
                    }
                }
            }
        """)

    def search_in_history(self, search_text):
        """Search inside history popup — JS."""
        try:
            self.driver.execute_script("""
                var inp = document.querySelector('.edit_pop_up input[placeholder="Search box"]');
                if (inp) {
                    var nativeSetter = Object.getOwnPropertyDescriptor(
                        window.HTMLInputElement.prototype, 'value'
                    ).set;
                    nativeSetter.call(inp, arguments[0]);
                    inp.dispatchEvent(new Event('input', {bubbles: true}));
                    inp.dispatchEvent(new Event('keyup', {bubbles: true}));
                    inp.dispatchEvent(new Event('change', {bubbles: true}));
                }
            """, str(search_text))
            # Brief settle for Angular change detection (replaces time.sleep(0.5))
            time.sleep(0.2)
            return True
        except Exception:
            return False

    # ═══════════════════════════════════════════════════════════════════════════
    # High-Level One-Call Methods (speed-optimized)
    # ═══════════════════════════════════════════════════════════════════════════

    def create_record(self, data):
        """
        One-call record creation: open form → fill all → submit.
        Uses _handle_submit_response() for fast alert detection.
        Returns dict: {status, error, message, data}
        """
        result = {"status": "failed", "error": "", "message": "", "data": data}
        try:
            self.open_add_form()

            fill_ok = self.fill_all_fields(data)
            if not fill_ok:
                result["error"] = "Dropdown failed to open after retries"
                return result

            self._force_close_panels()
            self.submit()

            # Combined alert handler — fast poll
            response = self._handle_submit_response(timeout=5)
            if response.get("alert"):
                result["error"] = f"Validation: {response['title']}"
                self.force_close_form_popup()
                return result

            if response.get("form_closed"):
                result["status"] = "success"
                result["message"] = "Record created (form closed silently)"
            else:
                result["error"] = "Form still open after submit — unknown error"

        except Exception as e:
            result["error"] = str(e)
            self._cleanup_swal2()
            self._force_close_panels()

        return result

    def edit_record(self, row_index, updated_data):
        """
        One-call record edit: click edit → fill changed fields → update.
        Returns dict: {status, error, message}
        """
        result = {"status": "failed", "error": "", "message": ""}
        try:
            self.click_edit_on_row(row_index)

            if not self.is_edit_mode():
                result["error"] = "Edit form did not open"
                return result

            # Fill changed fields
            if updated_data.get("code"):
                self.fill_code(updated_data["code"])
            if updated_data.get("description"):
                self.fill_description(updated_data["description"])
            if updated_data.get("error_code_type"):
                self.select_error_code_type(updated_data["error_code_type"])
            if updated_data.get("is_qty_amt"):
                self.toggle_is_qty_amt(updated_data["is_qty_amt"])

            self._force_close_panels()
            self.click_update()

            # Combined alert handler
            response = self._handle_submit_response(timeout=5)
            if response.get("alert"):
                result["error"] = f"Validation: {response['title']}"
                self.force_close_form_popup()
                return result

            if response.get("form_closed"):
                result["status"] = "success"
                result["message"] = "Record updated (form closed silently)"
            else:
                result["error"] = "Form still open after update — unknown error"

        except Exception as e:
            result["error"] = str(e)
            self._cleanup_swal2()
            self._force_close_panels()

        return result

    def view_record(self, row_index):
        """One-call view: click view → read values → close."""
        try:
            self.click_view_on_row(row_index)
            values = self.get_form_field_values()
            self.cancel()
            return values
        except Exception:
            self.cancel()
            return None

    def check_history(self, row_index):
        """One-call history check. Returns dict: {row_count, is_empty, error}"""
        result = {"row_count": 0, "is_empty": True, "error": ""}
        try:
            self.click_history_on_row(row_index)

            if not self.is_history_popup_open():
                result["error"] = "History popup did not open"
                return result

            result["row_count"] = self.get_history_row_count()
            result["is_empty"] = self.is_history_empty()

        except Exception as e:
            result["error"] = str(e)
        finally:
            self.close_history_popup()

        return result

    # ═══════════════════════════════════════════════════════════════════════════
    # Force Cleanup (single JS call)
    # ═══════════════════════════════════════════════════════════════════════════

    def force_close_form_popup(self):
        """Force-close any open form popup — single JS call."""
        self.driver.execute_script("""
            var popup = document.querySelector('div.edit_pop_up');
            if (!popup) return;
            var closeBtn = popup.querySelector('button[mat-icon-button] mat-icon');
            if (closeBtn) {
                var btn = closeBtn.closest('button');
                if (btn) { btn.click(); return; }
            }
            // Fallback: click Cancel
            var footers = document.querySelectorAll('.popup-footer');
            for (var i = 0; i < footers.length; i++) {
                var buttons = footers[i].querySelectorAll('button');
                for (var j = 0; j < buttons.length; j++) {
                    if (buttons[j].textContent.indexOf('Cancel') !== -1) {
                        buttons[j].click(); return;
                    }
                }
            }
        """)

    def force_cleanup_all(self):
        """One-call cleanup: SweetAlert + CDK overlays + form popups."""
        self.driver.execute_script("""
            document.querySelectorAll('.swal2-container').forEach(function(el) { el.remove(); });
            document.querySelectorAll('.swal2-backdrop-show').forEach(function(el) { el.remove(); });
            document.querySelectorAll('.cdk-overlay-backdrop').forEach(function(el) { el.remove(); });
            document.querySelectorAll('.cdk-overlay-pane:not(.mat-mdc-dialog-container)').forEach(function(el) { el.remove(); });
            var popup = document.querySelector('div.edit_pop_up');
            if (popup) {
                var closeBtn = popup.querySelector('button[mat-icon-button] mat-icon');
                if (closeBtn) {
                    var btn = closeBtn.closest('button');
                    if (btn) btn.click();
                }
            }
        """)

    def _force_close_panels(self):
        """Remove leftover CDK overlay panels (not dialogs) — single JS."""
        self.driver.execute_script("""
            document.querySelectorAll('.cdk-overlay-backdrop:not(.cdk-overlay-dark)').forEach(function(el) { el.remove(); });
            document.querySelectorAll('.cdk-overlay-pane:not(.mat-mdc-dialog-container)').forEach(function(el) { el.remove(); });
        """)

    # ═══════════════════════════════════════════════════════════════════════════
    # Search (handles pagination — like Tax Authority pattern)
    # ═══════════════════════════════════════════════════════════════════════════

    def search_record(self, code):
        """Search for a record by Code in the main table.
        Uses JS clicks to bypass overlay issues. Returns True if found."""
        try:
            # Toggle search input open
            self.driver.execute_script("""
                var toggleBtn = document.querySelector('button.search-btn');
                if (toggleBtn && toggleBtn.offsetParent !== null) toggleBtn.click();
            """)
            # Fast poll for search input
            end_search = time.monotonic() + 3
            while time.monotonic() < end_search:
                found = self.driver.execute_script("""
                    var inp = document.querySelector('input[placeholder="Search"]');
                    return inp && inp.offsetParent !== null;
                """)
                if found:
                    break
                time.sleep(0.1)

            # Set search value via JS native setter
            self.driver.execute_script("""
                var input = document.querySelector('input[placeholder="Search"]');
                if (input) {
                    var nativeSetter = Object.getOwnPropertyDescriptor(
                        window.HTMLInputElement.prototype, 'value'
                    ).set;
                    nativeSetter.call(input, arguments[0]);
                    input.dispatchEvent(new Event('input', {bubbles: true}));
                    input.dispatchEvent(new Event('keyup', {bubbles: true}));
                    input.dispatchEvent(new Event('change', {bubbles: true}));
                }
                var searchBtn = document.querySelector('button.search-btn');
                if (searchBtn) searchBtn.click();
            """, code)

            # Fast poll for table to update
            end_table = time.monotonic() + 5
            while time.monotonic() < end_table:
                row_count = self.get_table_row_count()
                if row_count > 0:
                    break
                time.sleep(0.2)

            return self.get_table_row_count() > 0

        except Exception:
            return False

    def clear_search(self):
        """Clear search filter — pure JS."""
        self.driver.execute_script("""
            var input = document.querySelector('input[placeholder="Search"]');
            if (input) {
                var nativeSetter = Object.getOwnPropertyDescriptor(
                    window.HTMLInputElement.prototype, 'value'
                ).set;
                nativeSetter.call(input, '');
                input.dispatchEvent(new Event('input', {bubbles: true}));
                input.dispatchEvent(new Event('keyup', {bubbles: true}));
                input.dispatchEvent(new Event('change', {bubbles: true}));
            }
            var btn = document.querySelector('button.search-btn');
            if (btn) btn.click();
        """)
