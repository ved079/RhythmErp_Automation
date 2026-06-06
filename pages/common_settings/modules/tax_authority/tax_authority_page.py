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
from selenium.webdriver.support.ui import WebDriverWait

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
        """Click ADD button via JS + wait for form popup + wait for fields to render."""
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
                break
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
        # Wait for mat-select elements to fully render inside form
        self._wait_for_form_fields_ready()

    def is_form_open(self):
        """Check if form popup is open — JS offsetParent (instant)."""
        return bool(self.driver.execute_script("""
            var el = document.querySelector('div.edit_pop_up');
            return el && el.offsetParent !== null;
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
        """Select Country from dropdown. Returns True if successful.
        Uses same _select_mat_dropdown pattern as Tax Type — simpler and more reliable.
        Works for 'India' (always first in the list)."""
        return self._select_mat_dropdown('Country', country_name)

    def _select_mat_dropdown(self, label_text, option_text):
        """Generic mat-select dropdown selection. Returns True if successful."""
        if not self._open_mat_dropdown(label_text):
            return False
        return self._click_dropdown_option(option_text)

    def _open_mat_dropdown(self, label_text):
        """Open a mat-select dropdown by label text. Returns True if panel opens.
        Uses partial label match + multiple click strategies for robustness."""
        # Try opening with multiple click strategies
        for attempt in range(3):
            self.driver.execute_script("""
                var labels = document.querySelectorAll('mat-label');
                var target = null;
                for (var i = 0; i < labels.length; i++) {
                    var txt = labels[i].textContent.trim();
                    if (txt === arguments[0] || txt.indexOf(arguments[0]) !== -1) {
                        target = labels[i]; break;
                    }
                }
                if (!target) return false;
                var field = target.closest('mat-form-field');
                if (!field) return false;
                var select = field.querySelector('mat-select');
                if (select) {
                    select.scrollIntoView({block:'center'});
                    select.click();
                    return true;
                }
                return false;
            """, label_text)

            # Fast poll for overlay panel (0.15s intervals, 2s timeout per attempt)
            end = time.monotonic() + 2
            while time.monotonic() < end:
                panel_open = self.driver.execute_script("""
                    var panels = document.querySelectorAll('.cdk-overlay-pane');
                    for (var i = 0; i < panels.length; i++) {
                        if (panels[i].offsetParent !== null) {
                            var hasOptions = panels[i].querySelector('mat-option, [role="option"]');
                            if (hasOptions) return true;
                        }
                    }
                    return false;
                """)
                if panel_open:
                    return True
                # Retry with trigger click strategy
                self.driver.execute_script("""
                    var labels = document.querySelectorAll('mat-label');
                    for (var i = 0; i < labels.length; i++) {
                        var txt = labels[i].textContent.trim();
                        if (txt === arguments[0] || txt.indexOf(arguments[0]) !== -1) {
                            var field = labels[i].closest('mat-form-field');
                            if (field) {
                                var trigger = field.querySelector('.mat-mdc-select-trigger');
                                if (trigger) { trigger.click(); return; }
                                var select = field.querySelector('mat-select');
                                if (select) { select.click(); return; }
                            }
                        }
                    }
                """, label_text)
                time.sleep(0.15)
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
        """Check if form is open AND no Submit/Update button (View mode) — JS."""
        return self.is_form_open() and not self.is_edit_mode() and not self._is_submit_visible()

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
        """Check if a form field is disabled (input or mat-select) — JS by name.
        Returns True if disabled, False if enabled or not found."""
        name = field_name or (locator_tuple[1].split("name='")[1].split("'")[0] if locator_tuple and "name=" in str(locator_tuple) else "")
        if not name:
            return False
        return bool(self.driver.execute_script("""
            // Check input element
            var input = document.querySelector('input[name="' + arguments[0] + '"]');
            if (input) {
                if (input.disabled || input.getAttribute('aria-disabled') === 'true' ||
                    input.hasAttribute('readonly') || input.getAttribute('readonly') === 'true') {
                    return true;
                }
            }
            // Check mat-select element (disabled state on mat-select itself)
            var labels = document.querySelectorAll('mat-label');
            for (var i = 0; i < labels.length; i++) {
                var txt = labels[i].textContent.trim();
                if (txt === arguments[0] || txt.indexOf(arguments[0]) !== -1) {
                    var field = labels[i].closest('mat-form-field');
                    if (field) {
                        var select = field.querySelector('mat-select');
                        if (select) {
                            if (select.classList.contains('mat-mdc-select-disabled') ||
                                select.hasAttribute('disabled') ||
                                select.getAttribute('aria-disabled') === 'true') {
                                return true;
                            }
                        }
                    }
                }
            }
            return false;
        """, name))

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

    def _get_tax_name_column_index(self):
        """Find the column index for Tax Name dynamically from table header or cdk-column."""
        return self.driver.execute_script("""
            // Try table header first
            var headers = document.querySelectorAll('table#excel-table thead tr th');
            for (var i = 0; i < headers.length; i++) {
                var text = (headers[i].textContent || '').trim().toLowerCase();
                if (text.indexOf('tax name') !== -1 || text === 'tax_name') return i;
            }
            // Try cdk-column class names on first data row
            var firstRow = document.querySelector('table#excel-table tbody tr');
            if (firstRow) {
                var cells = firstRow.querySelectorAll('td');
                for (var i = 0; i < cells.length; i++) {
                    var cls = cells[i].className || '';
                    if (cls.indexOf('cdk-column-tax_name') !== -1) return i;
                }
            }
            // Fallback: scan all cells in first row for any that look like tax names
            if (firstRow) {
                var cells = firstRow.querySelectorAll('td');
                for (var i = 1; i < cells.length; i++) {
                    var txt = (cells[i].textContent || '').trim();
                    // Skip columns that are too short (Sr No, actions) or look like dropdowns
                    if (txt.length > 3 && txt.length < 100 && !/^\\d+$/.test(txt)) return i;
                }
            }
            return 2;  // default fallback
        """)

    def find_row_by_name(self, name):
        """Find row index by Tax Name column — dynamic column detection. Returns -1 if not found."""
        col_idx = self._get_tax_name_column_index()
        return self.driver.execute_script("""
            var rows = document.querySelectorAll('table#excel-table tbody tr');
            var searchLower = arguments[0].toLowerCase();
            var colIdx = arguments[1];
            for (var i = 0; i < rows.length; i++) {
                var cells = rows[i].querySelectorAll('td');
                if (colIdx < cells.length) {
                    var text = (cells[colIdx].textContent || '').trim().toLowerCase();
                    if (text === searchLower) return i;
                }
                // Fallback: scan all cells
                for (var j = 0; j < cells.length; j++) {
                    var text2 = (cells[j].textContent || '').trim().toLowerCase();
                    if (text2 === searchLower) return i;
                }
            }
            return -1;
        """, name.strip(), col_idx)

    def is_record_present(self, name):
        """Check if a Tax Authority record exists in the table."""
        return self.find_row_by_name(name) != -1

    def get_name_from_row(self, row_index):
        """Get the Tax Name value from a specific row (dynamic column)."""
        col_idx = self._get_tax_name_column_index()
        return self.get_cell_text(row_index, col_idx)

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
        """Click action button using 3-dot menu (like UOM pattern).
        action_index: 0=View, 1=Edit, 2=History"""
        action_names = {0: "View", 1: "Edit", 2: "History"}
        action_name = action_names.get(action_index, "View")
        return self._click_action_menu_item(row_index, action_name)

    def _click_action_menu_item(self, row_index, action_name):
        """Click an action menu item (View/Edit/History) for a specific row.
        Uses 3-dot menu approach like UOM — opens menu dropdown, then clicks item."""
        try:
            # Step 1: Click 3-dot menu button in the actions column
            menu_opened = self.driver.execute_script("""
                var rows = document.querySelectorAll('table#excel-table tbody tr');
                if (arguments[0] >= rows.length) return false;
                var row = rows[arguments[0]];

                // Try cdk-column-actions button (3-dot menu)
                var menuBtn = row.querySelector('td.cdk-column-actions button');
                if (!menuBtn) {
                    // Try any button with mat-icon in the actions area
                    var actionCells = row.querySelectorAll('td');
                    for (var i = 0; i < actionCells.length; i++) {
                        var btns = actionCells[i].querySelectorAll('button');
                        for (var j = 0; j < btns.length; j++) {
                            var icon = btns[j].querySelector('mat-icon');
                            if (icon && (icon.textContent.trim() === 'more_vert'
                                || icon.textContent.trim() === 'more_horiz'
                                || icon.textContent.trim() === '...')) {
                                menuBtn = btns[j]; break;
                            }
                        }
                        if (menuBtn) break;
                    }
                }
                if (menuBtn) {
                    menuBtn.scrollIntoView({block:'center'});
                    menuBtn.click();
                    return true;
                }
                return false;
            """, row_index)

            if not menu_opened:
                # Fallback: try direct tblActnBtn approach
                result = self.driver.execute_script("""
                    var rows = document.querySelectorAll('table#excel-table tbody tr');
                    if (arguments[0] < rows.length) {
                        var btns = rows[arguments[0]].querySelectorAll('button.tblActnBtn');
                        if (btns.length > arguments[1]) {
                            btns[arguments[1]].click(); return true;
                        }
                    }
                    return false;
                """, row_index, action_index)
                if result:
                    end_action = time.monotonic() + 5
                    while time.monotonic() < end_action:
                        if self.is_form_open() or self.is_history_popup_open():
                            break
                        time.sleep(0.1)
                return bool(result)

            # Step 2: Wait for CDK overlay dropdown to appear
            end_menu = time.monotonic() + 3
            while time.monotonic() < end_menu:
                overlay_visible = self.driver.execute_script("""
                    var overlay = document.querySelector('.cdk-overlay-container .cdk-overlay-pane');
                    return overlay && overlay.offsetParent !== null;
                """)
                if overlay_visible:
                    break
                time.sleep(0.1)

            # Step 3: Click the action item in the dropdown
            result = self.driver.execute_script("""
                var overlay = document.querySelector('.cdk-overlay-container');
                if (!overlay) return false;
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

            # Step 4: Wait for form/popup to open
            if result:
                end_action = time.monotonic() + 5
                while time.monotonic() < end_action:
                    if action_name == "History":
                        if self.is_history_popup_open():
                            break
                    else:
                        if self.is_form_open():
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
        """Check if History popup is visible — JS offsetParent.
        Checks both app-dynamic-history component (like UOM) and popup-overlay."""
        return bool(self.driver.execute_script("""
            // Check app-dynamic-history (like UOM pattern)
            var histEl = document.querySelector('app-dynamic-history');
            if (histEl && histEl.offsetParent !== null) return true;
            // Check popup-overlay
            var el = document.querySelector('.popup-overlay .popup-content');
            if (el && el.offsetParent !== null) return true;
            return false;
        """))

    def get_history_title(self):
        """Get history popup title — JS. Checks both app-dynamic-history and popup-overlay."""
        try:
            return self.driver.execute_script("""
                // Check app-dynamic-history (like UOM)
                var histHeader = document.querySelector('app-dynamic-history .tbl-title h2');
                if (histHeader) return histHeader.textContent.trim();
                // Check popup-overlay
                var el = document.querySelector('.popup-overlay .popup-content .popup-title');
                return el ? el.textContent.trim() : '';
            """)
        except Exception:
            return ""

    def get_history_row_count(self):
        """Count rows in history table — JS. Checks both app-dynamic-history and popup-overlay."""
        return self.driver.execute_script("""
            var rows = document.querySelectorAll('app-dynamic-history table#excel-table tbody tr');
            if (rows.length > 0) return rows.length;
            rows = document.querySelectorAll('.popup-overlay .popup-content table tbody tr');
            return rows.length;
        """) or 0

    def close_history_popup(self):
        """Close History popup — pure JS Cancel click. Checks both patterns."""
        self.driver.execute_script("""
            // Try Cancel in app-dynamic-history (like UOM)
            var histFooters = document.querySelectorAll('app-dynamic-history .popup-footer');
            for (var i = 0; i < histFooters.length; i++) {
                var buttons = histFooters[i].querySelectorAll('button');
                for (var j = 0; j < buttons.length; j++) {
                    if (buttons[j].textContent.indexOf('Cancel') !== -1) {
                        buttons[j].click(); return;
                    }
                }
            }
            // Try Cancel in popup-overlay
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
            var closeIcons = document.querySelectorAll(
                'app-dynamic-history button .mat-icon, .popup-overlay .popup-actions button .mat-icon'
            );
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
            var hist = document.querySelector('app-dynamic-history');
            if (hist) hist.remove();
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

    def _wait_for_form_fields_ready(self):
        """Wait for form fields (especially mat-select) to be fully rendered."""
        end = time.monotonic() + 5
        while time.monotonic() < end:
            ready = self.driver.execute_script("""
                var selects = document.querySelectorAll('div.edit_pop_up mat-select');
                return selects.length >= 2;
            """)
            if ready:
                return
            time.sleep(0.1)

    def _force_close_panels(self):
        """Remove leftover CDK overlay panels (not dialogs) — single JS."""
        self.driver.execute_script("""
            document.querySelectorAll('.cdk-overlay-backdrop:not(.cdk-overlay-dark)').forEach(function(el) { el.remove(); });
            document.querySelectorAll('.cdk-overlay-pane:not(.mat-mdc-dialog-container)').forEach(function(el) { el.remove(); });
        """)
