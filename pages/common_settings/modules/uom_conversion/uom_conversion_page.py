"""
Page Object for UOM Conversion module.
Extends BasePage with pure-JS helpers for Angular Material MDC components.
"""

import time

from common.base_page import BasePage
from common.logger import log
from config import EXPLICIT_WAIT


class UOMConversionPage(BasePage):
    """Page Object for UOM Conversion (Common Settings)."""
    UOM_CONVERSION_PAGE_URL = "https://rhythmerp.algorhythms.in/#/dynamic-screens/UOM%20Conversion"
    # ================================================================
    #  NAVIGATION
    # ================================================================

    def navigate_to_page(self):
        log.info("Navigating to UOM Conversion page")
        self.driver.get(self.UOM_CONVERSION_PAGE_URL)
        self._wait_for_page_ready()
        self._force_close_panels()
        log.info("Arrived at UOM Conversion page")

    def _wait_for_page_ready(self):
        waited = 0
        while waited < 20:
            try:
                self.driver.find_element("css selector", "button.search-btn")
                log.info("Page ready after " + str(waited) + "s")
                return
            except Exception:
                pass
            try:
                self.driver.find_element("css selector", "table#excel-table")
                log.info("Page ready after " + str(waited) + "s")
                return
            except Exception:
                pass
            time.sleep(1)
            waited += 1

    def open_add_form(self):
        """Click the ADD button to open the form popup."""
        js = """
        var icons = document.querySelectorAll('app-custom-header mat-icon');
        for (var i = 0; i < icons.length; i++) {
            if (icons[i].textContent.trim() === 'add') {
                icons[i].click();
                return 'clicked add icon';
            }
        }
        throw new Error('ADD button not found');
        """
        result = self.driver.execute_script(js)
        log.info(f"Open add form: {result}")
        time.sleep(1)
        return result

    # ================================================================
    #  MAT-SELECT DROPDOWN (MDC)
    # ================================================================

    def select_uom(self, label_text, uom_code):
        """
        Select a UOM from a mat-select dropdown.
        Uses .mat-mdc-select-trigger and .mat-mdc-select-panel (MDC version).
        """
        # Step 1: Click the select trigger
        js_open = """
        var fields = document.querySelectorAll('mat-form-field');
        for (var i = 0; i < fields.length; i++) {
            var label = fields[i].querySelector('mat-label');
            if (label && label.textContent.trim().indexOf(arguments[0]) !== -1) {
                var trigger = fields[i].querySelector('.mat-mdc-select-trigger');
                if (trigger) {
                    trigger.click();
                    return 'opened: ' + label.textContent.trim();
                }
            }
        }
        throw new Error('mat-select trigger with label "' + arguments[0] + '" not found');
        """
        result = self.driver.execute_script(js_open, label_text)
        log.info(f"Selecting '{uom_code}' from '{label_text}' - {result}")

        # Step 2: Wait for panel to appear (retry loop)
        panel = None
        for _ in range(15):
            panel = self.driver.execute_script(
                "var p = document.querySelector('.mat-mdc-select-panel');"
                " return (p && p.offsetParent !== null) ? p : null;"
            )
            if panel:
                break
            time.sleep(0.4)

        if not panel:
            raise Exception(
                f".mat-mdc-select-panel did not appear for '{label_text}'"
            )

        # Step 3: Type in search input
        js_search = """
        var panel = document.querySelector('.mat-mdc-select-panel');
        if (!panel) throw new Error('Panel not found');
        var searchInput = panel.querySelector('.search-container input');
        if (!searchInput) throw new Error('Search input not found in panel');
        var nativeInputValueSetter = Object.getOwnPropertyDescriptor(
            window.HTMLInputElement.prototype, 'value'
        ).set;
        nativeInputValueSetter.call(searchInput, arguments[0]);
        searchInput.dispatchEvent(new Event('input', {bubbles: true}));
        return 'searched';
        """
        self.driver.execute_script(js_search, uom_code)
        time.sleep(1)

        # Step 4: Click matching option
        js_click = """
        var panel = document.querySelector('.mat-mdc-select-panel');
        if (!panel) throw new Error('Panel not found');
        var options = panel.querySelectorAll('mat-option');
        for (var i = 0; i < options.length; i++) {
            var t = options[i].querySelector('.mdc-list-item__primary-text');
            if (t && t.textContent.trim() === arguments[0]) {
                options[i].click();
                return 'selected (exact)';
            }
        }
        var needle = arguments[0].toUpperCase();
        for (var i = 0; i < options.length; i++) {
            var t = options[i].querySelector('.mdc-list-item__primary-text');
            if (t && t.textContent.trim().toUpperCase().indexOf(needle) !== -1) {
                options[i].click();
                return 'selected (partial): ' + t.textContent.trim();
            }
        }
        throw new Error('Option "' + arguments[0] + '" not found');
        """
        result = self.driver.execute_script(js_click, uom_code)
        log.info(f"Option click result: {result}")
        time.sleep(0.5)

        # Step 5: Cleanup leftover panels
        self._force_close_panels()

    def select_source_uom(self, uom_code):
        self.select_uom("Source UOM", uom_code)

    def select_target_uom(self, uom_code):
        self.select_uom("Target UOM", uom_code)

    # ================================================================
    #  FORM FIELDS
    # ================================================================

    def type_conversion_factor(self, value):
        """Type into the Conversion Factor input field."""
        js = """
        var fields = document.querySelectorAll('mat-form-field');
        for (var i = 0; i < fields.length; i++) {
            var label = fields[i].querySelector('mat-label');
            if (label && label.textContent.trim().indexOf('Conversion Factor') !== -1) {
                var input = fields[i].querySelector('input');
                if (input) {
                    input.focus();
                    var setter = Object.getOwnPropertyDescriptor(
                        window.HTMLInputElement.prototype, 'value'
                    ).set;
                    setter.call(input, arguments[0]);
                    input.dispatchEvent(new Event('input', {bubbles: true}));
                    input.dispatchEvent(new Event('change', {bubbles: true}));
                    return 'typed: ' + arguments[0];
                }
            }
        }
        throw new Error('Conversion Factor input not found');
        """
        result = self.driver.execute_script(js, str(value))
        log.info(f"Conversion factor typed: {result}")
        time.sleep(0.3)

    def get_mat_error_text(self, label_text):
        """Get the mat-error message for a field by its label."""
        js = """
        var fields = document.querySelectorAll('mat-form-field');
        for (var i = 0; i < fields.length; i++) {
            var label = fields[i].querySelector('mat-label');
            if (label && label.textContent.trim().indexOf(arguments[0]) !== -1) {
                var err = fields[i].querySelector('mat-error');
                return err ? err.textContent.trim() : '';
            }
        }
        return '';
        """
        return self.driver.execute_script(js, label_text) or ""

    # ================================================================
    #  FORM BUTTONS
    # ================================================================

    def click_save_button(self):
        """Click the Submit button on the form popup."""
        js = """
        var footer = document.querySelector('div.popup-footer');
        if (!footer) throw new Error('Popup footer not found');
        var btn = footer.querySelector('button[type="submit"]');
        if (!btn) throw new Error('Submit button not found');
        btn.click();
        return 'clicked submit';
        """
        self.driver.execute_script(js)
        log.info("Clicked Submit button")
        time.sleep(0.5)

    def click_cancel_button(self):
        """Click the Cancel button on the form popup."""
        js = """
        var footer = document.querySelector('div.popup-footer');
        if (!footer) throw new Error('Popup footer not found');
        var btn = footer.querySelector('.left button');
        if (btn) { btn.click(); return 'clicked cancel'; }
        var buttons = footer.querySelectorAll('button');
        for (var i = 0; i < buttons.length; i++) {
            if (buttons[i].textContent.trim().indexOf('Cancel') !== -1) {
                buttons[i].click();
                return 'clicked cancel (text)';
            }
        }
        throw new Error('Cancel button not found');
        """
        self.driver.execute_script(js)
        log.info("Clicked Cancel button")
        time.sleep(0.5)

    # ================================================================
    #  FORM POPUP STATE
    # ================================================================

    def is_form_open(self):
        """Return True if the overflow_model popup is visible."""
        try:
            return self.driver.execute_script("""
                var el = document.querySelector('div.overflow_model');
                if (!el) return false;
                var style = window.getComputedStyle(el);
                return style.display !== 'none' && style.visibility !== 'hidden';
            """)
        except Exception:
            return False

    def force_close_form_popup(self):
        """Force-close the form popup."""
        try:
            js = """
            var popup = document.querySelector('div.overflow_model');
            if (!popup) return 'no popup found';
            var actions = popup.querySelector('.popup-actions');
            if (actions) {
                var buttons = actions.querySelectorAll('button');
                for (var i = buttons.length - 1; i >= 0; i--) {
                    var icon = buttons[i].querySelector('mat-icon');
                    if (icon && icon.textContent.trim() === 'close') {
                        buttons[i].click();
                        return 'clicked close icon';
                    }
                }
            }
            var footer = popup.querySelector('div.popup-footer');
            if (footer) {
                var cancelBtn = footer.querySelector('.left button');
                if (cancelBtn) { cancelBtn.click(); return 'clicked cancel'; }
            }
            return 'popup found but no close button';
            """
            result = self.driver.execute_script(js)
            log.info(f"Force close form popup: {result}")
        except Exception as e:
            log.info(f"Force close popup exception: {e}")
        self._force_close_panels()
        time.sleep(0.5)

    def wait_for_form_to_close(self, timeout=5):
        """Poll until the form popup disappears."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            if not self.is_form_open():
                return True
            time.sleep(0.3)
        return False

    # ================================================================
    #  SWEET ALERT HANDLERS
    # ================================================================

    def close_popup(self):
        """Click the OK button on a SweetAlert popup."""
        try:
            js = """
            var btn = document.querySelector('.swal2-confirm');
            if (btn) { btn.click(); return 'swal2-confirm'; }
            btn = document.querySelector('.mat-dialog-actions button');
            if (btn) { btn.click(); return 'mat-dialog'; }
            return 'no popup button found';
            """
            result = self.driver.execute_script(js)
            log.info(f"Close popup: {result}")
            time.sleep(0.5)
        except Exception as e:
            log.info(f"Close popup error: {e}")

    def handle_validation_warning(self):
        """SweetAlert Pattern A: warning dialog with OK."""
        time.sleep(0.5)
        try:
            msg = self.driver.execute_script("""
                var title = document.querySelector('.swal2-title');
                var content = document.querySelector('.swal2-html-container');
                return (title ? title.textContent.trim() : '') +
                       (content ? ' - ' + content.textContent.trim() : '');
            """)
            log.info(f"Validation warning: {msg}")
            self.close_popup()
            return msg
        except Exception:
            return ""

    def handle_validation_download(self):
        """SweetAlert Pattern B: dialog with Download + Cancel."""
        time.sleep(0.5)
        try:
            msg = self.driver.execute_script("""
                var title = document.querySelector('.swal2-title');
                var content = document.querySelector('.swal2-html-container');
                return (title ? title.textContent.trim() : '') +
                       (content ? ' - ' + content.textContent.trim() : '');
            """)
            log.info(f"Validation download: {msg}")
            js_cancel = """
            var btn = document.querySelector('.swal2-cancel');
            if (btn) { btn.click(); return 'cancelled'; }
            return 'no cancel button';
            """
            self.driver.execute_script(js_cancel)
            time.sleep(0.5)
            return msg
        except Exception:
            return ""

    def handle_error_toast(self):
        """SweetAlert Pattern C: error toast (auto-dismisses)."""
        time.sleep(1)
        try:
            msg = self.driver.execute_script("""
                var toast = document.querySelector('.swal2-container.swal2-top-end .swal2-title')
                         || document.querySelector('.swal2-popup .swal2-title');
                if (toast) return toast.textContent.trim();
                var snackbar = document.querySelector('.mat-mdc-snack-bar-container .mdc-snackbar__label');
                if (snackbar) return snackbar.textContent.trim();
                return '';
            """)
            log.info(f"Error toast: {msg}")
            return msg
        except Exception:
            return ""

    def is_sweetalert_visible(self):
        """Check if any SweetAlert popup is visible."""
        try:
            return self.driver.execute_script("""
                var el = document.querySelector('.swal2-popup, .swal2-container');
                if (!el) return false;
                return el.offsetParent !== null ||
                       window.getComputedStyle(el).display !== 'none';
            """)
        except Exception:
            return False

    # ================================================================
    #  TABLE INTERACTIONS
    # ================================================================

    def wait_for_table_to_load(self, timeout=10):
        """Wait for at least one data row."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            rows = self.driver.execute_script("""
                return document.querySelectorAll('table#excel-table tbody tr.mat-mdc-row').length;
            """)
            if rows and rows > 0:
                return True
            time.sleep(0.5)
        return False

    def get_table_row_count(self):
        """Return number of data rows."""
        return self.driver.execute_script("""
            return document.querySelectorAll('table#excel-table tbody tr.mat-mdc-row').length;
        """) or 0

    def get_table_cell_value(self, row_index, column_name):
        """Get cell text from row index and column name."""
        js = f"""
        var rows = document.querySelectorAll('table#excel-table tbody tr.mat-mdc-row');
        if (rows.length <= {row_index}) return '';
        var cell = rows[{row_index}].querySelector('.cdk-column-{column_name}');
        return cell ? cell.textContent.trim() : '';
        """
        return self.driver.execute_script(js) or ""

    def is_record_present(self, source_uom, target_uom):
        """Check if a record exists in the table."""
        js = """
        var rows = document.querySelectorAll('table#excel-table tbody tr.mat-mdc-row');
        for (var i = 0; i < rows.length; i++) {
            var src = rows[i].querySelector('.cdk-column-source_uom_code');
            var tgt = rows[i].querySelector('.cdk-column-target_uom_code');
            if (src && tgt &&
                src.textContent.trim() === arguments[0] &&
                tgt.textContent.trim() === arguments[1]) {
                return true;
            }
        }
        return false;
        """
        return self.driver.execute_script(js, source_uom, target_uom)

    def _click_action_button(self, row_source, row_target, action_column):
        """Click an action button for a specific row."""
        js = f"""
        var rows = document.querySelectorAll('table#excel-table tbody tr.mat-mdc-row');
        for (var i = 0; i < rows.length; i++) {{
            var src = rows[i].querySelector('.cdk-column-source_uom_code');
            var tgt = rows[i].querySelector('.cdk-column-target_uom_code');
            if (src && tgt &&
                src.textContent.trim() === arguments[0] &&
                tgt.textContent.trim() === arguments[1]) {{
                var cell = rows[i].querySelector('.cdk-column-{action_column}');
                if (cell) {{
                    var btn = cell.querySelector('button');
                    if (btn) {{
                        btn.click();
                        return 'clicked {action_column} on row ' + i;
                    }}
                }}
            }}
        }}
        throw new Error('Row or {action_column} button not found');
        """
        result = self.driver.execute_script(js, row_source, row_target)
        log.info(f"Action button click: {result}")
        time.sleep(0.5)
        return result

    def click_edit_button(self, row_source, row_target):
        return self._click_action_button(row_source, row_target, "edit")

    def click_view_button(self, row_source, row_target):
        return self._click_action_button(row_source, row_target, "view")

    def click_history_button(self, row_source, row_target):
        return self._click_action_button(row_source, row_target, "archive")

    # ================================================================
    #  CDK OVERLAY CLEANUP
    # ================================================================

    def _force_close_panels(self):
        """Remove any open CDK overlay panels/backdrops."""
        try:
            self.driver.execute_script("""
                document.querySelectorAll('.cdk-overlay-backdrop').forEach(function(b) { b.remove(); });
                document.querySelectorAll('.cdk-overlay-pane').forEach(function(p) {
                    if (!p.querySelector('.swal2-popup')) p.remove();
                });
            """)
        except Exception:
            pass

    # ================================================================
    #  UTILITY
    # ================================================================

    def refresh_page(self):
        """Click the REFRESH button."""
        js = """
        var icons = document.querySelectorAll('app-custom-header mat-icon');
        for (var i = 0; i < icons.length; i++) {
            if (icons[i].textContent.trim() === 'refresh') {
                icons[i].click();
                return 'clicked refresh';
            }
        }
        throw new Error('Refresh button not found');
        """
        self.driver.execute_script(js)
        log.info("Refreshed page")
        time.sleep(1.5)

    def get_selected_uom_text(self, label_text):
        """Get currently selected value from a mat-select."""
        js = """
        var fields = document.querySelectorAll('mat-form-field');
        for (var i = 0; i < fields.length; i++) {
            var label = fields[i].querySelector('mat-label');
            if (label && label.textContent.trim().indexOf(arguments[0]) !== -1) {
                var val = fields[i].querySelector('.mat-mdc-select-value-text span');
                return val ? val.textContent.trim() : '';
            }
        }
        return '';
        """
        return self.driver.execute_script(js, label_text) or ""

    def get_conversion_factor_value(self):
        """Get current value of Conversion Factor input."""
        js = """
        var fields = document.querySelectorAll('mat-form-field');
        for (var i = 0; i < fields.length; i++) {
            var label = fields[i].querySelector('mat-label');
            if (label && label.textContent.trim().indexOf('Conversion Factor') !== -1) {
                var input = fields[i].querySelector('input');
                return input ? input.value : '';
            }
        }
        return '';
        """
        return self.driver.execute_script(js) or ""
