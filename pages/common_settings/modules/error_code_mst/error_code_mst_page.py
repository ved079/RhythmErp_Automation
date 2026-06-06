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
        """Check if form popup is open — JS offsetParent (instant).
        Checks div.edit_pop_up (the actual form container used by the ERP)."""
        return bool(self.driver.execute_script("""
            var el = document.querySelector('div.edit_pop_up');
            if (el && el.offsetParent !== null) return true;
            var bigModel = document.querySelector('div.big-model');
            if (bigModel && bigModel.offsetParent !== null) return true;
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
        """Set input value via JS native setter + Angular change events.
        Scoped to form popup (div.edit_pop_up) when popup is open."""
        self.driver.execute_script("""
            var input = null;
            var form = document.querySelector('div.edit_pop_up');
            if (form && form.offsetParent !== null) {
                input = form.querySelector('input[name="' + arguments[0] + '"]');
            }
            if (!input) {
                input = document.querySelector('input[name="' + arguments[0] + '"]');
            }
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

            # Find and click the matching option via JS (pointerdown → pointerup → click for Angular)
            clicked = self.driver.execute_script("""
                var options = document.querySelectorAll(
                    'div.mat-mdc-select-panel mat-option'
                );
                for (var i = 0; i < options.length; i++) {
                    if (options[i].offsetParent !== null &&
                        options[i].textContent.indexOf(arguments[0]) !== -1) {
                        options[i].scrollIntoView({block:'center'});
                        options[i].dispatchEvent(new PointerEvent('pointerdown', {bubbles: true}));
                        options[i].dispatchEvent(new PointerEvent('pointerup', {bubbles: true}));
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
                        allOpts[i].dispatchEvent(new PointerEvent('pointerdown', {bubbles: true}));
                        allOpts[i].dispatchEvent(new PointerEvent('pointerup', {bubbles: true}));
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
                var form = document.querySelector('div.edit_pop_up') || document.querySelector('div.big-model');
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
        """Check if Update button is present (Edit mode) — JS.
        Scoped to div.edit_pop_up to avoid matching buttons outside the form."""
        return bool(self.driver.execute_script("""
            var form = document.querySelector('div.edit_pop_up');
            if (!form || form.offsetParent === null) return false;
            var btns = form.querySelectorAll('.popup-footer button');
            for (var i = 0; i < btns.length; i++) {
                if (btns[i].textContent.indexOf('Update') !== -1 && btns[i].offsetParent !== null)
                    return true;
            }
            return false;
        """))

    def is_view_mode(self):
        """Check if form is open and no Submit/Update button (View mode) — JS.
        Also checks that Cancel button is present (form IS open, just read-only)."""
        if not self.is_form_open():
            return False
        has_submit = self._is_submit_visible()
        has_update = self.is_edit_mode()
        has_cancel = self._is_cancel_visible()
        return has_cancel and not has_submit and not has_update

    def _is_submit_visible(self):
        """Check if Submit button is visible — scoped to form popup."""
        return bool(self.driver.execute_script("""
            var form = document.querySelector('div.edit_pop_up');
            if (!form || form.offsetParent === null) return false;
            var btns = form.querySelectorAll('.popup-footer button');
            for (var i = 0; i < btns.length; i++) {
                if (btns[i].textContent.indexOf('Submit') !== -1 && btns[i].offsetParent !== null)
                    return true;
            }
            return false;
        """))

    def _is_cancel_visible(self):
        """Check if Cancel button is visible — scoped to form popup."""
        return bool(self.driver.execute_script("""
            var form = document.querySelector('div.edit_pop_up');
            if (!form || form.offsetParent === null) return false;
            var btns = form.querySelectorAll('.popup-footer button');
            for (var i = 0; i < btns.length; i++) {
                if (btns[i].textContent.indexOf('Cancel') !== -1 && btns[i].offsetParent !== null)
                    return true;
            }
            return false;
        """))

    def get_form_heading(self):
        """Read popup heading text — JS. Scoped to form popup."""
        try:
            return self.driver.execute_script(
                "var form = document.querySelector('div.edit_pop_up'); "
                "if (!form) form = document.querySelector('div.big-model'); "
                "if (!form) return ''; "
                "var el = form.querySelector('h3'); "
                "return el ? el.textContent.trim() : '';"
            )
        except Exception:
            return ""

    # ═══════════════════════════════════════════════════════════════════════════
    # Read Form Field Values
    # ═══════════════════════════════════════════════════════════════════════════

    def get_form_field_values(self):
        """Read all form field values — JS. Scoped to form popup to avoid
        picking up mat-select/input elements from the table or other areas."""
        values = self.driver.execute_script("""
            var result = {};
            var form = document.querySelector('div.edit_pop_up');
            if (!form || form.offsetParent === null) {
                return {error_code_type: '', code: '', description: '', is_qty_amt: 'Amount'};
            }
            var selectTrigger = form.querySelector('mat-select .mat-mdc-select-value-text');
            if (selectTrigger) {
                result.error_code_type = selectTrigger.textContent.trim();
            } else {
                var select = form.querySelector('mat-select');
                result.error_code_type = select ? (select.textContent || '').trim().split('\n')[0].trim() : '';
            }
            var code = form.querySelector('input[name="Code"]');
            result.code = code ? code.value : '';
            var desc = form.querySelector('input[name="Description"]');
            result.description = desc ? desc.value : '';
            var cb = form.querySelector('.switch-container.vertical input[type="checkbox"]');
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
    # Row Action Buttons — View / Edit / History (3-dot menu from UOM pattern)
    # ═══════════════════════════════════════════════════════════════════════════

    def click_view_on_row(self, row_index=0):
        """Click View action via 3-dot menu on specified row."""
        return self._click_action_menu_item(row_index, "View")

    def click_edit_on_row(self, row_index=0):
        """Click Edit action via 3-dot menu on specified row."""
        return self._click_action_menu_item(row_index, "Edit")

    def click_history_on_row(self, row_index=0):
        """Click History action via 3-dot menu on specified row."""
        return self._click_action_menu_item(row_index, "History")

    def _click_action_menu_item(self, row_index, action_name):
        """Click an action menu item (View/Edit/History) for a specific row.
        Uses the 3-dot (⋮) menu button (button.erp-row-trigger) in the Actions column,
        then selects the action from the dropdown overlay — UOM gold standard pattern."""
        # Step 1: Click the 3-dot menu trigger for the given row
        menu_opened = self.driver.execute_script("""
            var rows = document.querySelectorAll('table#excel-table tbody tr');
            if (arguments[0] >= rows.length) return false;
            var menuBtn = rows[arguments[0]].querySelector('td.cdk-column-actions button.erp-row-trigger');
            if (!menuBtn) return false;
            menuBtn.scrollIntoView({block:'center'});
            menuBtn.click();
            return true;
        """, row_index)

        if not menu_opened:
            return False

        # Step 2: Wait for the dropdown overlay to appear
        end = time.monotonic() + 3
        while time.monotonic() < end:
            overlay_visible = self.driver.execute_script("""
                var panels = document.querySelectorAll('.mat-mdc-menu-panel.erp-action-menu');
                for (var i = 0; i < panels.length; i++) {
                    if (panels[i].offsetParent !== null) return true;
                }
                return false;
            """)
            if overlay_visible:
                break
            time.sleep(0.1)

        # Step 3: Click the specific menu item from the dropdown overlay
        clicked = self.driver.execute_script("""
            var overlay = document.querySelector('.mat-mdc-menu-panel.erp-action-menu');
            if (!overlay) return false;
            // Try exact match on menu title first
            var titles = overlay.querySelectorAll('.erp-menu-title');
            for (var i = 0; i < titles.length; i++) {
                if (titles[i].textContent.trim() === arguments[0]) {
                    var item = titles[i].closest('.erp-menu-item');
                    if (item) { item.click(); return true; }
                    titles[i].click(); return true;
                }
            }
            // Fallback: try matching on any button/span text in the overlay
            var items = overlay.querySelectorAll('button, span, div');
            for (var i = 0; i < items.length; i++) {
                var text = items[i].textContent.trim();
                if (text === arguments[0]) {
                    items[i].click();
                    return true;
                }
            }
            // Fallback: partial match
            for (var i = 0; i < items.length; i++) {
                var text = items[i].textContent.trim().toLowerCase();
                if (text.indexOf(arguments[0].toLowerCase()) !== -1) {
                    items[i].click();
                    return true;
                }
            }
            return false;
        """, action_name)

        # Step 4: Wait for form or history popup to open
        if clicked:
            end_action = time.monotonic() + 5
            while time.monotonic() < end_action:
                if action_name == "History":
                    if self.is_history_popup_open():
                        break
                else:
                    if self.is_form_open():
                        break
                time.sleep(0.1)
            # Small settle for Angular to render form fields
            time.sleep(0.2)

        # Clean up any lingering overlays
        self._force_close_panels()
        return bool(clicked)

    # ═══════════════════════════════════════════════════════════════════════════
    # History Popup
    # ═══════════════════════════════════════════════════════════════════════════

    def is_history_popup_open(self):
        """Check if History popup is visible — JS offsetParent.
        History popup uses div.popup-overlay > .popup-content > .popup-header > h3.popup-title."""
        return bool(self.driver.execute_script("""
            // Primary: Check div.popup-overlay with popup-title containing 'History'
            var overlay = document.querySelector('div.popup-overlay');
            if (overlay) {
                var title = overlay.querySelector('h3.popup-title');
                if (title && title.textContent.indexOf('History') !== -1 && title.offsetParent !== null)
                    return true;
            }
            // Fallback: Check app-dynamic-history component (like UOM uses)
            var histComp = document.querySelector('app-dynamic-history');
            if (histComp && histComp.offsetParent !== null) return true;
            return false;
        """))

    def get_history_row_count(self):
        """Count rows in history table — JS. Checks popup-overlay first, then fallbacks."""
        return self.driver.execute_script("""
            var rows = document.querySelectorAll('div.popup-overlay app-dynamic-history table tbody tr');
            if (rows.length > 0) return rows.length;
            rows = document.querySelectorAll('.edit_pop_up table tbody tr');
            if (rows.length > 0) return rows.length;
            rows = document.querySelectorAll('app-dynamic-history table tbody tr');
            return rows.length;
        """) or 0

    def is_history_empty(self):
        """Check if history shows 'No Data Available' — JS.
        Checks popup-overlay first, then fallbacks."""
        return bool(self.driver.execute_script("""
            var overlay = document.querySelector('div.popup-overlay');
            if (overlay) {
                var img = overlay.querySelector('img[alt="No Data Available"]');
                if (img && img.offsetParent !== null) return true;
                var text = overlay.textContent || '';
                if (text.indexOf('No data available') !== -1 || text.indexOf('No Data Available') !== -1 || text.indexOf('No results found') !== -1) return true;
            }
            // Fallbacks
            var img = document.querySelector('.edit_pop_up img[alt="No Data Available"]');
            if (img && img.offsetParent !== null) return true;
            img = document.querySelector('app-dynamic-history img[alt="No Data Available"]');
            if (img && img.offsetParent !== null) return true;
            var allEls = document.querySelectorAll('.no-data, .noData');
            for (var i = 0; i < allEls.length; i++) {
                if (allEls[i].offsetParent !== null) return true;
            }
            return false;
        """))

    def close_history_popup(self):
        """Close History popup — pure JS Cancel click.
        Targets div.popup-overlay first, then fallback to any popup-footer."""
        self.driver.execute_script("""
            var overlay = document.querySelector('div.popup-overlay');
            if (overlay) {
                var footers = overlay.querySelectorAll('.popup-footer');
                for (var i = 0; i < footers.length; i++) {
                    var buttons = footers[i].querySelectorAll('button');
                    for (var j = 0; j < buttons.length; j++) {
                        if (buttons[j].textContent.indexOf('Cancel') !== -1) {
                            buttons[j].click(); return;
                        }
                    }
                }
                // Fallback: try close button (X) in popup-actions
                var closeBtn = overlay.querySelector('.popup-actions button[mat-icon-button]');
                if (closeBtn) { closeBtn.click(); return; }
            }
            // Ultimate fallback: any Cancel in any popup-footer
            var allFooters = document.querySelectorAll('.popup-footer');
            for (var i = 0; i < allFooters.length; i++) {
                var buttons = allFooters[i].querySelectorAll('button');
                for (var j = 0; j < buttons.length; j++) {
                    if (buttons[j].textContent.indexOf('Cancel') !== -1) {
                        buttons[j].click(); return;
                    }
                }
            }
        """)

    def search_in_history(self, search_text):
        """Search inside history popup — JS.
        Checks popup-overlay first, then fallbacks."""
        try:
            self.driver.execute_script("""
                var inp = null;
                var overlay = document.querySelector('div.popup-overlay');
                if (overlay) {
                    inp = overlay.querySelector('input[placeholder="Search box"], input#erpSearchInput');
                }
                if (!inp) inp = document.querySelector('.edit_pop_up input[placeholder="Search box"]');
                if (!inp) inp = document.querySelector('app-dynamic-history input');
                if (!inp) inp = document.querySelector('.edit_pop_up input[placeholder="Search"]');
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
        One-call record edit: click edit → wait for edit mode → fill changed fields → update.
        Returns dict: {status, error, message}
        """
        result = {"status": "failed", "error": "", "message": ""}
        try:
            self.click_edit_on_row(row_index)

            # Wait for edit mode to be ready (Update button visible)
            end_edit = time.monotonic() + 5
            while time.monotonic() < end_edit:
                if self.is_edit_mode():
                    break
                time.sleep(0.1)

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
        """One-call view: click view → wait for form → read values → close."""
        try:
            self.click_view_on_row(row_index)
            # Wait for form to fully open (view mode)
            end_view = time.monotonic() + 5
            while time.monotonic() < end_view:
                if self.is_form_open():
                    break
                time.sleep(0.1)
            # Small settle for Angular to populate fields
            time.sleep(0.3)
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

            # Wait for history popup to open with extended timeout
            end_hist = time.monotonic() + 5
            while time.monotonic() < end_hist:
                if self.is_history_popup_open():
                    break
                time.sleep(0.1)

            if not self.is_history_popup_open():
                result["error"] = "History popup did not open"
                return result

            result["row_count"] = self.get_history_row_count()
            result["is_empty"] = self.is_history_empty()

        except Exception as e:
            result["error"] = str(e)
        finally:
            try:
                self.close_history_popup()
            except Exception:
                pass

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
