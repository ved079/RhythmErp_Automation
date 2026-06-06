"""
Tax Authority — Page Object (v4 SPEED OPTIMIZED)
====================================================
UOM gold-standard speed patterns applied.
Module: 3 fields (2 mat-select dropdowns + 1 text input).

Speed optimizations vs v3 (BasePage):
- Standalone page object (no BasePage inheritance = no wait_seconds overhead)
- Session-scoped driver + navigate_to_page() / hard_refresh() per test
- All time.sleep() replaced with fast JS polls (0.1-0.2s intervals)
- is_form_open() uses JS offsetParent (instant, no WebDriverWait)
- is_record_present() / find_row_by_name() use pure JS
- _handle_submit_response() combines alert detect + dismiss in ONE call
- _js_click_popup_button() like UOM — single JS call
- Dropdown: fast poll for panel open, JS option click, fast poll for close
- No function-scoped page fixture — tests create page per test
"""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException

from pages.common_settings.modules.tax_authority.data.tax_authority_data import (
    TAX_AUTHORITY_PAGE_URL,
    VALIDATION_FAILED_TITLE,
    FIELD_TAX_NAME,
)
from common.logger import log


class TaxAuthorityPage:

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
        """Navigate to Tax Authority page via direct URL. First call only."""
        self.driver.get(TAX_AUTHORITY_PAGE_URL)
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

    # ═══════════════════════════════════════════════════════════════════════════
    # Add Form — Open / Close (fast JS, no sleep)
    # ═══════════════════════════════════════════════════════════════════════════

    def open_add_form(self):
        """Click ADD button via JS + wait for form popup via fast poll."""
        self.driver.execute_script("""
            var btn = document.querySelector('button[mattooltip="ADD"]')
                     || document.querySelector('button.erp-add-btn');
            if (!btn) {
                var icons = document.querySelectorAll('button mat-icon');
                for (var i = 0; i < icons.length; i++) {
                    if (icons[i].textContent.trim() === 'add') {
                        btn = icons[i].closest('button'); break;
                    }
                }
            }
            if (btn) { btn.scrollIntoView({block:'center'}); btn.click(); }
        """)
        # Fast poll for form popup (0.2s intervals, 5s timeout)
        end = time.monotonic() + 5
        while time.monotonic() < end:
            if self.is_form_open():
                return
            # Retry click if form didn't open
            self.driver.execute_script("""
                var btn = document.querySelector('button[mattooltip="ADD"]')
                         || document.querySelector('button.erp-add-btn');
                if (!btn) {
                    var icons = document.querySelectorAll('button mat-icon');
                    for (var i = 0; i < icons.length; i++) {
                        if (icons[i].textContent.trim() === 'add') {
                            btn = icons[i].closest('button'); break;
                        }
                    }
                }
                if (btn) btn.click();
            """)
            time.sleep(0.2)

    def is_form_open(self):
        """Check if form popup is open — JS offsetParent (instant)."""
        return self.driver.execute_script("""
            var el = document.querySelector('div.edit_pop_up');
            return el && el.offsetParent !== null;
        """)

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

    def fill_tax_name(self, value):
        """Type into Tax Name input — JS native setter + Angular dispatch."""
        self._fill_input_by_name('Tax Name', value)

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

    # ═══════════════════════════════════════════════════════════════════════════
    # Dropdown Selection (fast JS polls, UOM pattern)
    # ═══════════════════════════════════════════════════════════════════════════

    def select_tax_type(self, option_text):
        """Select from Tax Type dropdown (mat-select). Returns True if successful."""
        return self._select_mat_dropdown('Tax Type', option_text)

    def select_country(self, country_name):
        """Select Country from searchable dropdown. Returns True if successful."""
        # Open dropdown
        if not self._open_mat_dropdown('Country'):
            return False

        # Type search text (Country dropdown is searchable)
        self.driver.execute_script("""
            var searchInputs = document.querySelectorAll(
                '.cdk-overlay-pane input[type="text"], .cdk-overlay-pane input'
            );
            for (var i = 0; i < searchInputs.length; i++) {
                if (searchInputs[i].offsetParent !== null) {
                    var nativeSetter = Object.getOwnPropertyDescriptor(
                        window.HTMLInputElement.prototype, 'value'
                    ).set;
                    nativeSetter.call(searchInputs[i], arguments[0]);
                    searchInputs[i].dispatchEvent(new Event('input', {bubbles: true}));
                    searchInputs[i].dispatchEvent(new Event('keyup', {bubbles: true}));
                    searchInputs[i].dispatchEvent(new Event('change', {bubbles: true}));
                    return true;
                }
            }
            return false;
        """, country_name)

        # Fast poll for filtered options to appear
        end_opts = time.monotonic() + 3
        while time.monotonic() < end_opts:
            opt_count = self.driver.execute_script("""
                var opts = document.querySelectorAll('div.mat-mdc-select-panel mat-option');
                return opts.length;
            """)
            if opt_count > 0:
                break
            time.sleep(0.1)

        # Click the matching option
        return self._click_dropdown_option(country_name)

    def _select_mat_dropdown(self, label_text, option_text):
        """Generic mat-select dropdown selection. Returns True if successful."""
        if not self._open_mat_dropdown(label_text):
            return False
        return self._click_dropdown_option(option_text)

    def _open_mat_dropdown(self, label_text):
        """Open a mat-select dropdown by label text. Returns True if panel opens."""
        # JS click the mat-select trigger
        self.driver.execute_script("""
            var labels = document.querySelectorAll('mat-label');
            var target = null;
            for (var i = 0; i < labels.length; i++) {
                if (labels[i].textContent.trim() === arguments[0]) {
                    target = labels[i]; break;
                }
            }
            if (!target) return false;
            var field = target.closest('mat-form-field');
            if (!field) return false;
            var select = field.querySelector('mat-select');
            if (select) { select.click(); return true; }
            return false;
        """, label_text)

        # Fast poll for overlay panel (0.2s intervals, 3s timeout)
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
                return True
            time.sleep(0.2)
        return False

    def _click_dropdown_option(self, option_text):
        """Click a matching option in the open dropdown panel."""
        clicked = self.driver.execute_script("""
            var options = document.querySelectorAll(
                'div.mat-mdc-select-panel mat-option, [role="option"]'
            );
            for (var i = 0; i < options.length; i++) {
                if (options[i].offsetParent !== null &&
                    options[i].textContent.indexOf(arguments[0]) !== -1) {
                    options[i].scrollIntoView({block:'center'});
                    options[i].click();
                    return true;
                }
            }
            return false;
        """, option_text.strip())

        # Fast poll for CDK overlay panel to close
        end_panel = time.monotonic() + 2
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

    # ═══════════════════════════════════════════════════════════════════════════
    # Fill All Fields (with lightweight retry)
    # ═══════════════════════════════════════════════════════════════════════════

    def fill_all_fields(self, data, max_retries=3, is_edit=False):
        """Fill all form fields with retry logic for dropdowns.
        Order: Dropdowns FIRST → Text field.
        Returns True if all fields filled successfully."""
        for attempt in range(1, max_retries + 1):
            success = self._fill_all_fields_once(data)
            if success:
                return True
            if is_edit:
                return False
            # Retry: cancel + hard_refresh + reopen form
            self.cancel()
            self.hard_refresh()
            self.open_add_form()
        return False

    def _fill_all_fields_once(self, data):
        """Single pass: fill Dropdowns → Text field."""
        # 1. Dropdowns first (most likely to fail)
        tax_type = data.get("tax_type", "")
        country = data.get("country", "")
        if tax_type:
            type_ok = self.select_tax_type(tax_type)
            if not type_ok:
                return False
        if country:
            country_ok = self.select_country(country)
            if not country_ok:
                return False

        # 2. Text field
        tax_name = data.get(FIELD_TAX_NAME, "")
        if tax_name:
            self.fill_tax_name(tax_name)

        return True

    # ═══════════════════════════════════════════════════════════════════════════
    # Submit / Update (UOM _js_click_popup_button pattern)
    # ═══════════════════════════════════════════════════════════════════════════

    def submit(self):
        """Click Submit button — single JS call."""
        self._js_click_popup_button('Submit')

    def click_update(self):
        """Click Update button — single JS call."""
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
    # NOTE: Tax Authority does NOT show success SweetAlert2 on create/update.
    # Form closes silently. Only "Validation Failed" alert appears for errors.

    def _handle_submit_response(self, timeout=5):
        """Combined SweetAlert handler — single fast poll.
        Detects validation alert OR form close (= success).
        Returns dict: {alert: bool, title: str, form_closed: bool}"""
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
                var form = document.querySelector('div.edit_pop_up');
                var formOpen = form && form.offsetParent !== null;
                if (!formOpen) {
                    return {alert: false, title: '', form_closed: true};
                }
                return null;
            """)
            if result is not None:
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

    def get_alert_title(self):
        """Get SweetAlert2 title text — JS."""
        try:
            return self.driver.execute_script(
                "var el = document.querySelector('#swal2-title'); "
                "return el && el.offsetParent !== null ? el.textContent.trim() : '';"
            )
        except Exception:
            return ""

    def get_alert_message(self):
        """Get SweetAlert2 body message — JS."""
        try:
            return self.driver.execute_script(
                "var el = document.querySelector('.swal2-html-container'); "
                "return el && el.offsetParent !== null ? el.textContent.trim() : '';"
            )
        except Exception:
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
        return self.driver.execute_script("""
            var btns = document.querySelectorAll('.popup-footer button');
            for (var i = 0; i < btns.length; i++) {
                if (btns[i].textContent.indexOf('Update') !== -1 && btns[i].offsetParent !== null)
                    return true;
            }
            return false;
        """)

    def is_view_mode(self):
        """Check if no Submit/Update button (View mode) — JS."""
        return not self.is_edit_mode() and not self._is_submit_visible()

    def _is_submit_visible(self):
        return self.driver.execute_script("""
            var btns = document.querySelectorAll('.popup-footer button');
            for (var i = 0; i < btns.length; i++) {
                if (btns[i].textContent.indexOf('Submit') !== -1 && btns[i].offsetParent !== null)
                    return true;
            }
            return false;
        """)

    def is_field_disabled(self, locator_tuple=None, field_name=None):
        """Check if a form field is disabled — JS by name."""
        name = field_name or (locator_tuple[1].split("name='")[1].split("'")[0] if locator_tuple and "name=" in str(locator_tuple) else "")
        if not name:
            return False
        return self.driver.execute_script("""
            var input = document.querySelector('input[name="' + arguments[0] + '"]');
            return input && (input.disabled || input.getAttribute('aria-disabled') === 'true');
        """, name)

    # ═══════════════════════════════════════════════════════════════════════════
    # Read Form Field Values
    # ═══════════════════════════════════════════════════════════════════════════

    def get_form_field_values(self):
        """Read all form field values — JS. Returns dict."""
        values = self.driver.execute_script("""
            var result = {};
            var input = document.querySelector('input[name="Tax Name"]');
            result.tax_name = input ? input.value : '';
            var selects = document.querySelectorAll('mat-select');
            for (var i = 0; i < selects.length; i++) {
                var trigger = selects[i].querySelector('.mat-mdc-select-min-line, .mat-select-value-text');
                if (!trigger) trigger = selects[i];
                var label = selects[i].closest('mat-form-field');
                if (label) {
                    var labelEl = label.querySelector('mat-label');
                    if (labelEl && labelEl.textContent.trim() === 'Tax Type') {
                        result.tax_type = (selects[i].textContent || '').trim();
                    }
                    if (labelEl && labelEl.textContent.trim() === 'Country') {
                        result.country = (selects[i].textContent || '').trim();
                    }
                }
            }
            return result;
        """)
        return values or {"tax_name": "", "tax_type": "", "country": ""}

    # ═══════════════════════════════════════════════════════════════════════════
    # Table Operations (pure JS — fast, no Selenium iteration)
    # ═══════════════════════════════════════════════════════════════════════════

    def get_table_row_count(self):
        """Count visible data rows in table — JS."""
        return self.driver.execute_script(
            "return document.querySelectorAll('table#excel-table tbody tr').length;"
        ) or 0

    def get_cell_text(self, row_index, col_index):
        """Read text from a table cell by row index and column index — JS."""
        return self.driver.execute_script("""
            var rows = document.querySelectorAll('table#excel-table tbody tr');
            if (arguments[0] < rows.length) {
                var cells = rows[arguments[0]].querySelectorAll('td');
                if (arguments[1] < cells.length) {
                    return (cells[arguments[1]].textContent || '').trim();
                }
            }
            return '';
        """, row_index, col_index)

    def find_row_by_name(self, name):
        """Find row index by Tax Name column — pure JS (fast). Returns -1 if not found."""
        return self.driver.execute_script("""
            var rows = document.querySelectorAll('table#excel-table tbody tr');
            var searchLower = arguments[0].toLowerCase();
            for (var i = 0; i < rows.length; i++) {
                var cells = rows[i].querySelectorAll('td');
                // Tax Name is column 3 (0-indexed)
                if (cells.length > 3) {
                    var text = (cells[3].textContent || '').trim().toLowerCase();
                    if (text === searchLower) return i;
                }
            }
            return -1;
        """, name.strip())

    def is_record_present(self, name):
        """Check if a Tax Authority record exists in the table."""
        return self.find_row_by_name(name) != -1

    def get_name_from_row(self, row_index):
        """Get the Tax Name value from a specific row (column 3)."""
        return self.get_cell_text(row_index, 3)

    # ═══════════════════════════════════════════════════════════════════════════
    # Row Action Buttons — View / Edit / History (JS click)
    # ═══════════════════════════════════════════════════════════════════════════

    def click_view_button(self, row_index=0):
        """Click View action button on specified row — JS."""
        return self._click_row_action_button(row_index, 0)

    def click_edit_button(self, row_index=0):
        """Click Edit action button on specified row — JS."""
        return self._click_row_action_button(row_index, 1)

    def click_history_button(self, row_index=0):
        """Click History action button on specified row — JS."""
        return self._click_row_action_button(row_index, 2)

    def _click_row_action_button(self, row_index, action_index):
        """Click action button by row and action index (0=view,1=edit,2=history) — JS."""
        try:
            result = self.driver.execute_script("""
                var rows = document.querySelectorAll('table#excel-table tbody tr');
                if (arguments[0] < rows.length) {
                    var btns = rows[arguments[0]].querySelectorAll('button.tblActnBtn');
                    if (btns.length > arguments[1]) {
                        btns[arguments[1]].click();
                        return true;
                    }
                    // Fallback: try action columns
                    var cells = rows[arguments[0]].querySelectorAll('td');
                    for (var j = 0; j < cells.length; j++) {
                        var cellBtns = cells[j].querySelectorAll('button');
                        if (cellBtns.length > 0 && j < 6) {
                            if (j === arguments[1] + 0) {
                                cellBtns[0].click();
                                return true;
                            }
                        }
                    }
                }
                return false;
            """, row_index, action_index)
            # Fast poll for form/popup to open
            if result:
                end_action = time.monotonic() + 5
                while time.monotonic() < end_action:
                    if self.is_form_open() or self.is_history_popup_open():
                        break
                    time.sleep(0.1)
            return bool(result)
        except Exception:
            return False

    # ═══════════════════════════════════════════════════════════════════════════
    # Search (atomic JS, UOM pattern)
    # ═══════════════════════════════════════════════════════════════════════════

    def search_record(self, name, exact=False):
        """Search for a record by Tax Name. Returns True if found."""
        try:
            # Toggle search, set value, trigger events — all JS
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

            # Set search value via JS
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
            """, name)

            # Fast poll for table to update
            end_table = time.monotonic() + 5
            while time.monotonic() < end_table:
                row_count = self.get_table_row_count()
                if row_count > 0:
                    break
                time.sleep(0.2)

            if exact:
                return self.find_row_by_name(name) != -1
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
                input.dispatchEvent(new KeyboardEvent('keydown', {
                    key: 'Enter', code: 'Enter', keyCode: 13, bubbles: true
                }));
            }
            var btn = document.querySelector('button.search-btn');
            if (btn) btn.click();
        """)

    # ═══════════════════════════════════════════════════════════════════════════
    # History Popup
    # ═══════════════════════════════════════════════════════════════════════════

    def is_history_popup_open(self):
        """Check if History popup is visible — JS offsetParent."""
        return self.driver.execute_script("""
            var el = document.querySelector('.popup-overlay .popup-content');
            return el && el.offsetParent !== null;
        """)

    def get_history_title(self):
        """Get history popup title — JS."""
        try:
            return self.driver.execute_script(
                "var el = document.querySelector('.popup-overlay .popup-content .popup-title'); "
                "return el ? el.textContent.trim() : '';"
            )
        except Exception:
            return ""

    def get_history_row_count(self):
        """Count rows in history table — JS."""
        return self.driver.execute_script(
            "return document.querySelectorAll('.popup-overlay .popup-content table tbody tr').length;"
        ) or 0

    def close_history_popup(self):
        """Close History popup — pure JS Cancel click."""
        self.driver.execute_script("""
            var footers = document.querySelectorAll('.popup-overlay .popup-footer');
            for (var i = 0; i < footers.length; i++) {
                var buttons = footers[i].querySelectorAll('button');
                for (var j = 0; j < buttons.length; j++) {
                    if (buttons[j].textContent.indexOf('Cancel') !== -1) {
                        buttons[j].click(); return;
                    }
                }
            }
            // Fallback: click X button
            var closeIcons = document.querySelectorAll('.popup-overlay .popup-actions button .mat-icon');
            for (var k = 0; k < closeIcons.length; k++) {
                if (closeIcons[k].textContent.trim() === 'close') {
                    var btn = closeIcons[k].closest('button');
                    if (btn) btn.click();
                    return;
                }
            }
            // Nuclear: remove overlay
            var overlay = document.querySelector('.popup-overlay');
            if (overlay) overlay.remove();
        """)

    # ═══════════════════════════════════════════════════════════════════════════
    # High-Level One-Call Methods (speed-optimized)
    # ═══════════════════════════════════════════════════════════════════════════

    def create_record(self, data):
        """One-call record creation: open form → fill all → submit.
        Uses _handle_submit_response() for fast alert detection.
        Returns dict: {status, error, message, data}"""
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

    def edit_record(self, data, row_index=0):
        """One-call record edit: click edit → fill changed fields → update.
        Returns dict: {status, error, message}"""
        result = {"status": "failed", "error": "", "message": ""}
        try:
            self.click_edit_button(row_index)

            if not self.is_edit_mode():
                result["error"] = "Edit form did not open"
                return result

            # Fill changed fields
            tax_name = data.get(FIELD_TAX_NAME, "")
            if tax_name:
                self.fill_tax_name(tax_name)
            if data.get("tax_type"):
                self.select_tax_type(data["tax_type"])
            if data.get("country"):
                self.select_country(data["country"])

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
            self.click_view_button(row_index)
            values = self.get_form_field_values()
            self.cancel()
            return values
        except Exception:
            self.cancel()
            return None

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
            var overlay = document.querySelector('.popup-overlay');
            if (overlay) overlay.remove();
        """)

    def _force_close_panels(self):
        """Remove leftover CDK overlay panels (not dialogs) — single JS."""
        self.driver.execute_script("""
            document.querySelectorAll('.cdk-overlay-backdrop:not(.cdk-overlay-dark)').forEach(function(el) { el.remove(); });
            document.querySelectorAll('.cdk-overlay-pane:not(.mat-mdc-dialog-container)').forEach(function(el) { el.remove(); });
        """)
