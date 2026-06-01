"""
Page Object for UOM Conversion module.
Extends BasePage with pure-JS helpers for Angular Material MDC components.
"""

import time
import random

from common.base_page import BasePage
from common.logger import log


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
        """
        Poll until the 'add' icon appears in app-custom-header.
        Timeout extended to 30s. After expiry, waits an extra 3s as a
        last-ditch buffer so Angular can finish rendering before callers
        proceed.
        """
        waited = 0
        while waited < 30:
            try:
                has_add = self.driver.execute_script("""
                    // Try .erp-add-btn first (most reliable), then fallback to icon search
                    var addBtn = document.querySelector('app-custom-header .erp-add-btn');
                    if (addBtn) return true;
                    var icons = document.querySelectorAll('app-custom-header mat-icon, app-custom-header i.material-icons');
                    for (var i = 0; i < icons.length; i++) {
                        if (icons[i].textContent.trim() === 'add') return true;
                    }
                    return false;
                """)
                if has_add:
                    log.info("Page ready after " + str(waited) + "s")
                    return
            except Exception:
                pass
            time.sleep(1)
            waited += 1
        log.warning("Page may not be fully ready after 30s")
        # Last-ditch buffer: give Angular a few more seconds
        time.sleep(3)

    def hard_refresh(self):
        """Hard refresh the current page to clear stale overlays/state."""
        log.info("Hard refreshing page...")
        try:
            self.driver.execute_script("location.reload(true)")
            time.sleep(2)
            log.info("Hard refresh complete")
        except Exception as e:
            log.warning("Hard refresh failed: " + str(e))
            time.sleep(2)

    def open_add_form(self):
        """
        Click the ADD button to open the form popup.
        Retries up to 3 times. Between retries, attempts to close stale
        overlays and hard refresh the page.
        """
        js = """
        // Try .erp-add-btn first (most reliable), then fallback to icon click
        var addBtn = document.querySelector('app-custom-header .erp-add-btn');
        if (addBtn) { addBtn.click(); return 'clicked erp-add-btn'; }
        var icons = document.querySelectorAll('app-custom-header mat-icon, app-custom-header i.material-icons');
        for (var i = 0; i < icons.length; i++) {
            if (icons[i].textContent.trim() === 'add') {
                icons[i].click();
                return 'clicked add icon';
            }
        }
        throw new Error('ADD button not found');
        """
        last_exc = None
        for attempt in range(1, 4):
            try:
                result = self.driver.execute_script(js)
                log.info(f"Open add form: {result}")
                time.sleep(1)
                return result
            except Exception as e:
                last_exc = e
                log.warning(f"open_add_form attempt {attempt}/3 failed: {e}")
                if attempt < 3:
                    try:
                        self._force_close_panels()
                    except Exception:
                        pass
                    try:
                        self.force_close_form_popup()
                    except Exception:
                        pass
                    self.hard_refresh()
                else:
                    time.sleep(2)
        raise last_exc

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
        """Click the Submit or Update button on the form popup via JS."""
        js = """
        var footer = document.querySelector('div.popup-footer');
        if (!footer) throw new Error('Popup footer not found');
        var buttons = footer.querySelectorAll('button');
        for (var i = 0; i < buttons.length; i++) {
            var txt = buttons[i].textContent.trim();
            if (txt === 'Submit' || txt === 'Update') {
                buttons[i].click();
                return 'clicked ' + txt;
            }
        }
        throw new Error('Submit/Update button not found in popup footer');
        """
        result = self.driver.execute_script(js)
        log.info(f"Clicked save button: {result}")
        time.sleep(0.3)

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
                    var icon = buttons[i].querySelector('mat-icon, i.material-icons');
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
        time.sleep(0.3)
        try:
            msg = self.driver.execute_script("""
                var title = document.querySelector('.swal2-title');
                var content = document.querySelector('.swal2-html-container');
                return (title ? title.textContent.trim() : '') +
                       (content ? ' - ' + content.textContent.trim() : '');
            """)
            log.info(f"Validation warning: {msg}")
            # Pattern A uses .swal2-confirm ("OK") to dismiss
            self.driver.execute_script("""
                var btn = document.querySelector('.swal2-confirm');
                if (btn) btn.click();
            """)
            time.sleep(0.3)
            return msg
        except Exception:
            return ""

    def handle_validation_download(self):
        """SweetAlert Pattern B: dialog with Download Errors + Cancel."""
        time.sleep(0.3)
        try:
            msg = self.driver.execute_script("""
                var title = document.querySelector('.swal2-title');
                var content = document.querySelector('.swal2-html-container');
                return (title ? title.textContent.trim() : '') +
                       (content ? ' - ' + content.textContent.trim() : '');
            """)
            log.info(f"Validation download: {msg}")
            # Pattern B: click Cancel (.swal2-cancel) to dismiss WITHOUT downloading
            self.driver.execute_script("""
                var btn = document.querySelector('.swal2-cancel');
                if (btn) { btn.click(); return 'cancelled'; }
                // Fallback: deny button ("No")
                btn = document.querySelector('.swal2-deny');
                if (btn) { btn.click(); return 'denied'; }
                return 'no cancel/deny button';
            """)
            time.sleep(0.3)
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
                document.querySelectorAll('.cdk-overlay-backdrop:not(.cdk-overlay-dark-backdrop)').forEach(function(b) { b.remove(); });
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
        var icons = document.querySelectorAll('app-custom-header mat-icon, app-custom-header i.material-icons');
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

    # ================================================================
    #  ALIASES (methods called by tests with different names)
    # ================================================================

    CONVERSION_FACTOR_INPUT = "Conversion Factor"

    def enter_conversion_factor(self, value):
        """Alias for type_conversion_factor."""
        self.type_conversion_factor(value)

    def submit(self):
        """Alias for click_save_button."""
        self.click_save_button()

    def click_update(self):
        """Alias for submit (used in edit flow)."""
        self.click_save_button()

    def is_add_form_open(self):
        """Alias for is_form_open."""
        return self.is_form_open()

    def click_row_edit(self, source, target):
        """Alias for click_edit_button."""
        return self.click_edit_button(source, target)

    def click_row_view(self, source, target):
        """Alias for click_view_button."""
        return self.click_view_button(source, target)

    def click_row_history(self, source, target):
        """Alias for click_history_button."""
        return self.click_history_button(source, target)

    def cleanup(self):
        """General cleanup: close form, close popups, force close panels."""
        try:
            self.force_close_form_popup()
        except Exception:
            pass
        try:
            self.close_popup()
        except Exception:
            pass
        self._force_close_panels()

    # ================================================================
    #  SUCCESS / VALIDATION ALERT HELPERS
    # ================================================================

    def is_success_alert_present(self, timeout=3):
        """Check if SweetAlert success popup appeared."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                visible = self.driver.execute_script("""
                    var el = document.querySelector('.swal2-popup');
                    if (!el) return false;
                    if (el.offsetParent === null) return false;
                    var title = el.querySelector('.swal2-title');
                    if (title && title.textContent.toLowerCase().indexOf('success') !== -1) return true;
                    var icon = el.querySelector('.swal2-icon.swal2-success');
                    if (icon) return true;
                    return false;
                """)
                if visible:
                    return True
            except Exception:
                pass
            time.sleep(0.3)
        return False

    def is_validation_alert_present(self, timeout=3):
        """Check if SweetAlert validation/warning popup appeared."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                visible = self.driver.execute_script("""
                    var el = document.querySelector('.swal2-popup');
                    if (!el) return false;
                    if (el.offsetParent === null) return false;
                    return true;
                """)
                if visible:
                    return True
            except Exception:
                pass
            time.sleep(0.3)
        return False

    def handle_success_alert(self):
        """Click OK on success SweetAlert."""
        time.sleep(0.3)
        try:
            self.driver.execute_script("""
                var btn = document.querySelector('.swal2-confirm');
                if (btn) { btn.click(); return 'clicked'; }
            """)
            time.sleep(0.3)
        except Exception:
            pass

    def get_swal_title(self):
        """Get the SweetAlert popup title text."""
        try:
            return self.driver.execute_script("""
                var el = document.querySelector('.swal2-title');
                return el ? el.textContent.trim() : '';
            """) or ""
        except Exception:
            return ""

    # ================================================================
    #  FORM FIELD HELPERS
    # ================================================================

    def is_dropdown_error(self, label_text):
        """Check if a mat-select dropdown has error state."""
        js = """
        var fields = document.querySelectorAll('mat-form-field');
        for (var i = 0; i < fields.length; i++) {
            var label = fields[i].querySelector('mat-label');
            if (label && label.textContent.trim().indexOf(arguments[0]) !== -1) {
                var select = fields[i].querySelector('mat-select');
                if (select) {
                    return select.classList.contains('mat-mdc-select-invalid') ||
                           select.classList.contains('ng-invalid');
                }
            }
        }
        return false;
        """
        return self.driver.execute_script(js, label_text)

    def clear_conversion_factor_via_js(self):
        """Clear the Conversion Factor input field via JS."""
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
                    setter.call(input, '');
                    input.dispatchEvent(new Event('input', {bubbles: true}));
                    input.dispatchEvent(new Event('change', {bubbles: true}));
                    return 'cleared';
                }
            }
        }
        throw new Error('Conversion Factor input not found');
        """
        self.driver.execute_script(js)
        time.sleep(0.3)

    # ================================================================
    #  TABLE HELPERS
    # ================================================================

    def get_table_rows(self):
        """Get table rows as a list of row indices [0, 1, 2, ...]."""
        count = self.get_table_row_count()
        return list(range(count))

    def find_table_row(self, source_uom, target_uom):
        """Find row index for a record. Returns -1 if not found."""
        js = """
        var rows = document.querySelectorAll('table#excel-table tbody tr.mat-mdc-row');
        for (var i = 0; i < rows.length; i++) {
            var src = rows[i].querySelector('.cdk-column-source_uom_code');
            var tgt = rows[i].querySelector('.cdk-column-target_uom_code');
            if (src && tgt &&
                src.textContent.trim() === arguments[0] &&
                tgt.textContent.trim() === arguments[1]) {
                return i;
            }
        }
        return -1;
        """
        return self.driver.execute_script(js, source_uom, target_uom)

    def is_record_in_table(self, source_uom, target_uom):
        """Alias for is_record_present."""
        return self.is_record_present(source_uom, target_uom)

    def get_conversion_factor_from_row(self, row_index):
        """Get conversion factor value from a table row."""
        return self.get_table_cell_value(row_index, "conversion_factor")

    # ================================================================
    #  DYNAMIC PAIR FINDER
    # ================================================================

    def get_available_uoms(self):
        """
        Read all available UOM codes from the Source UOM dropdown.
        Opens the Add form popup temporarily to access the dropdown,
        then closes it. Returns a list of UOM code strings.
        """
        log.info("Reading available UOMs from dropdown")

        # Must open popup first � dropdown only exists inside the form
        self.open_add_form()
        time.sleep(1.5)

        # Read all mat-option texts from the Source UOM dropdown
        js_read = """
        var trigger = document.querySelector(
            "div.edit_pop_up mat-form-field mat-select .mat-mdc-select-trigger"
        );
        if (!trigger) throw new Error('Source UOM dropdown not found inside popup');
        trigger.click();

        // Wait a moment for options to render
        var start = Date.now();
        while (Date.now() - start < 2000) {
            var opts = document.querySelectorAll('.cdk-overlay-pane mat-option');
            if (opts.length > 0) break;
        }

        var options = document.querySelectorAll('.cdk-overlay-pane mat-option');
        var uoms = [];
        for (var i = 0; i < options.length; i++) {
            var text = options[i].textContent.trim();
            if (text) uoms.push(text);
        }

        // Close the dropdown panel
        var backdrop = document.querySelector('.cdk-overlay-backdrop');
        if (backdrop) backdrop.click();
        else {
            var panels = document.querySelectorAll('.cdk-overlay-pane');
            for (var j = 0; j < panels.length; j++) panels[j].remove();
        }

        return uoms;
        """
        uoms = self.driver.execute_script(js_read)
        log.info("Found " + str(len(uoms) if uoms else 0) + " available UOMs")

        # Close the Add form popup
        time.sleep(0.5)
        self.force_close_form_popup()
        time.sleep(0.5)
        self._force_close_panels()

        if not uoms:
            raise RuntimeError("No UOM options found in dropdown")
        return uoms

    def get_existing_pairs(self):
        """
        Read all existing Source?Target UOM pairs from the main table.
        No popup needed � reads directly from the visible table.
        Returns a set of tuples: {('KG', 'ML'), ('NOS', 'PCS'), ...}
        """
        log.info("Reading existing pairs from table")
        js_read = """
        var table = document.querySelector('table#excel-table');
        if (!table) throw new Error('Table not found on page');
        var rows = table.querySelectorAll('tbody tr');
        var pairs = [];
        for (var i = 0; i < rows.length; i++) {
            var source = '', target = '';
            var cells = rows[i].querySelectorAll('td');
            for (var j = 0; j < cells.length; j++) {
                var cls = cells[j].getAttribute('class') || '';
                if (cls.indexOf('cdk-column-source_uom_code') !== -1)
                    source = cells[j].textContent.trim();
                if (cls.indexOf('cdk-column-target_uom_code') !== -1)
                    target = cells[j].textContent.trim();
            }
            if (source && target) pairs.push([source, target]);
        }
        return pairs;
        """
        raw_pairs = self.driver.execute_script(js_read)
        pair_set = set()
        if raw_pairs:
            for pair in raw_pairs:
                pair_set.add((pair[0], pair[1]))
        log.info("Found " + str(len(pair_set)) + " existing pairs in table")
        return pair_set


    # ================================================================
    #  SELECT PANEL CLEANUP (Company Onboarding pattern)
    # ================================================================

    def _close_select_panel(self):
        """Close select dropdown panel by pressing Escape. Safe for Angular state."""
        try:
            self.driver.execute_script("""
                var esc = new KeyboardEvent('keydown', {key:'Escape',code:'Escape',bubbles:true});
                document.activeElement.dispatchEvent(esc);
                document.body.dispatchEvent(esc);
            """)
            time.sleep(0.3)
        except Exception:
            pass

    def _read_dropdown_uoms(self):
        """Open Source UOM dropdown and read all options. Leaves dropdown OPEN."""
        log.info("Opening Source UOM dropdown to read options")
        js = """
        var fields = document.querySelectorAll('div.edit_pop_up mat-form-field');
        for (var i = 0; i < fields.length; i++) {
            var label = fields[i].querySelector('mat-label');
            if (label && label.textContent.trim().indexOf('Source UOM') !== -1) {
                var trigger = fields[i].querySelector('.mat-mdc-select-trigger');
                if (trigger) { trigger.click(); return 'opened'; }
            }
        }
        throw new Error('Source UOM dropdown not found in form');
        """
        self.driver.execute_script(js)
        time.sleep(1.5)
        js_read = """
        var start = Date.now();
        while (Date.now() - start < 3000) {
            var opts = document.querySelectorAll('.cdk-overlay-pane mat-option .mdc-list-item__primary-text');
            if (opts.length > 0) break;
        }
        var options = document.querySelectorAll('.cdk-overlay-pane mat-option .mdc-list-item__primary-text');
        var uoms = [];
        for (var i = 0; i < options.length; i++) {
            var text = options[i].textContent.trim();
            if (text) uoms.push(text);
        }
        return uoms;
        """
        uoms = self.driver.execute_script(js_read)
        log.info("Found " + str(len(uoms) if uoms else 0) + " UOM options")
        if not uoms:
            raise RuntimeError("No UOM options found in dropdown")
        return uoms

    def _select_from_open_panel(self, uom_code):
        """Click an option in the ALREADY OPEN dropdown panel. Does NOT reopen."""
        log.info("Selecting from open panel: " + uom_code)
        js = """
        var options = document.querySelectorAll('.cdk-overlay-pane mat-option');
        for (var i = 0; i < options.length; i++) {
            var text = options[i].querySelector('.mdc-list-item__primary-text');
            if (text && text.textContent.trim() === arguments[0]) {
                options[i].click();
                return 'selected: ' + arguments[0];
            }
        }
        var needle = arguments[0].toUpperCase();
        for (var i = 0; i < options.length; i++) {
            var text = options[i].querySelector('.mdc-list-item__primary-text');
            if (text && text.textContent.trim().toUpperCase().indexOf(needle) !== -1) {
                options[i].click();
                return 'selected (partial): ' + text.textContent.trim();
            }
        }
        throw new Error('Option not found in open panel: ' + arguments[0]);
        """
        result = self.driver.execute_script(js, uom_code)
        log.info(result)
        time.sleep(0.5)

    def _dismiss_sweetalert(self):
        """Dismiss any visible SweetAlert popup using the correct handler.
        Pattern A (Validation Failed - Please correct...): .swal2-confirm = OK
        Pattern B (Validation Failed - Fields validation failed...Download): .swal2-cancel = Cancel
        """
        try:
            content = self.driver.execute_script("""
                var content = document.querySelector('.swal2-html-container');
                return content ? content.textContent.trim() : '';
            """) or ""
            if 'download' in content.lower():
                # Pattern B — click Cancel to avoid downloading
                self.handle_validation_download()
            else:
                # Pattern A — click OK
                self.handle_validation_warning()
        except Exception:
            # Fallback: try any dismiss button
            try:
                self.close_popup()
            except Exception:
                pass

    def create_fresh_record(self, factor=None, max_retries=5, raise_on_error=True):
        """
        Creates a new UOM conversion record with a fresh (non-duplicate) pair.
        Uses try-submit-catch-duplicate pattern - does NOT pre-read the table.

        IMPORTANT: On success, the ERP closes the form silently (NO success popup).
        We detect success by checking if the form closed after submit.

        Args:
            factor: If None, generates random integer 1-1000.
                    If provided, uses the given factor string/value.
            max_retries: Retry count on validation error (default 5).
            raise_on_error: If True (default), retries on error, raises on exhaustion.
                            If False, returns dict with success=False on first error.
        Returns: dict with source_uom, target_uom, conversion_factor,
                 success (bool), error (str, only if success=False).
        """
        log.info("Creating fresh UOM conversion record")
        last_error = None

        for attempt in range(max_retries):
            log.info("Attempt " + str(attempt + 1) + "/" + str(max_retries))

            self.open_add_form()
            time.sleep(1)

            uoms = self._read_dropdown_uoms()
            source, target = random.sample(uoms, 2)

            actual_factor = str(factor) if factor is not None else str(random.randint(1, 1000))
            log.info("Trying: " + source + " -> " + target + " = " + actual_factor)

            self._select_from_open_panel(source)
            time.sleep(0.5)
            self.select_target_uom(target)
            self.enter_conversion_factor(actual_factor)
            self.submit()

            # Wait briefly for ERP to process
            time.sleep(1)

            # --- Success path: form closed silently (no success popup) ---
            if not self.is_form_open() and not self.is_sweetalert_visible():
                log.info("Record created successfully (form closed silently): " + source + " -> " + target)
                return {
                    "source_uom": source, "target_uom": target,
                    "conversion_factor": actual_factor, "success": True
                }

            # --- Check for success alert (rare, but handle it) ---
            if self.is_success_alert_present(timeout=2):
                self.handle_success_alert()
                log.info("Record created successfully (success alert): " + source + " -> " + target)
                return {
                    "source_uom": source, "target_uom": target,
                    "conversion_factor": actual_factor, "success": True
                }

            # --- Validation / duplicate path ---
            if self.is_validation_alert_present(timeout=2):
                last_error = self.get_swal_title()
                log.warning("Validation alert on attempt " + str(attempt + 1) + ": " + str(last_error))
                # Dismiss using the correct handler based on alert pattern
                self._dismiss_sweetalert()
                time.sleep(0.3)

                if not raise_on_error:
                    # Caller wants to observe the error (Tests 10, 11, 13)
                    self.force_close_form_popup()
                    return {
                        "source_uom": source, "target_uom": target,
                        "conversion_factor": actual_factor,
                        "success": False, "error": last_error
                    }

                # Retry with a completely new random pair
                log.info("Duplicate/error detected - closing form and retrying with new pair...")
                self.force_close_form_popup()
                time.sleep(0.3)
                self.hard_refresh()
                time.sleep(1)
                continue

            # --- No alert and form still open (unexpected) ---
            last_error = "No alert and form still open after submit"
            log.warning(last_error)
            self.force_close_form_popup()
            if not raise_on_error:
                return {
                    "source_uom": source, "target_uom": target,
                    "conversion_factor": actual_factor,
                    "success": False, "error": last_error
                }

        # All retries exhausted
        if raise_on_error:
            raise RuntimeError("Failed to create record after " + str(max_retries) +
                             " attempts. Last error: " + str(last_error))
        return {
            "source_uom": source or "?", "target_uom": target or "?",
            "conversion_factor": str(factor) if factor is not None else "?",
            "success": False, "error": last_error or "max retries exhausted"
        }

    def get_available_uoms_from_form(self):
        """Read all UOM options from Source dropdown of currently open form.
        Closes dropdown after reading. Form stays open."""
        uoms = self._read_dropdown_uoms()
        self._close_select_panel()
        time.sleep(0.3)
        log.info("Available UOMs from form: " + str(len(uoms)) + " options")
        return uoms

    # ================================================================

    #  TABLE SEARCH
    # ================================================================

    def search_table(self, text):
        """Click search button, type text, press Enter to filter table."""
        log.info("Searching table: " + text)
        self.driver.execute_script("""
            var btn = document.querySelector('.search-btn');
            if (btn) btn.click();
        """)
        time.sleep(0.8)
        self.driver.execute_script("""
            var inp = document.getElementById('erpSearchInput');
            if (inp) {
                inp.value = '';
                inp.dispatchEvent(new Event('input', {bubbles:true}));
            }
        """)
        time.sleep(0.3)
        self.driver.execute_script("""
            var inp = document.getElementById('erpSearchInput');
            if (inp) {
                inp.value = arguments[0];
                inp.dispatchEvent(new Event('input', {bubbles:true}));
            }
        """, text)
        time.sleep(0.3)
        self.driver.execute_script("""
            var inp = document.getElementById('erpSearchInput');
            if (inp) {
                inp.dispatchEvent(new KeyboardEvent('keydown', {key:'Enter',code:'Enter',bubbles:true}));
                inp.dispatchEvent(new KeyboardEvent('keyup', {key:'Enter',code:'Enter',bubbles:true}));
            }
        """)
        time.sleep(1.5)
        log.info("Search applied: " + text)

    def clear_search(self):
        """Clear search input and press Enter to reset table."""
        try:
            self.driver.execute_script("""
                var inp = document.getElementById('erpSearchInput');
                if (inp) {
                    inp.value = '';
                    inp.dispatchEvent(new Event('input', {bubbles:true}));
                    inp.dispatchEvent(new KeyboardEvent('keydown', {key:'Enter',code:'Enter',bubbles:true}));
                }
            """)
            time.sleep(1)
            log.info("Search cleared")
        except Exception:
            pass

    # ================================================================

    #  HISTORY POPUP HELPERS
    # ================================================================

    def get_history_row_count(self):
        """Count rows in the history popup table."""
        try:
            return self.driver.execute_script("""
                var rows = document.querySelectorAll('table tbody tr');
                if (rows.length === 0) {
                    rows = document.querySelectorAll('.mat-mdc-row');
                }
                return rows.length;
            """) or 0
        except Exception:
            return 0

    def get_history_data(self):
        """Get all history table data as a list of row strings."""
        try:
            return self.driver.execute_script("""
                var rows = document.querySelectorAll('table tbody tr.mat-mdc-row');
                var data = [];
                for (var i = 0; i < rows.length; i++) {
                    data.push(rows[i].textContent.trim());
                }
                return data;
            """) or []
        except Exception:
            return []

    def close_history_popup(self):
        """Close the history popup by clicking Cancel button in footer."""
        try:
            self.driver.execute_script("""
                // Try Cancel button in popup footer
                var footer = document.querySelector('div.overflow_model .popup-footer button');
                if (footer) { footer.click(); return 'footer cancel'; }
                // Try close icon in popup header
                var popup = document.querySelector('div.overflow_model');
                if (popup) {
                    var actions = popup.querySelector('.popup-actions');
                    if (actions) {
                        var buttons = actions.querySelectorAll('button');
                        for (var i = buttons.length - 1; i >= 0; i--) {
                            var icon = buttons[i].querySelector('mat-icon');
                            if (icon && icon.textContent.trim() === 'close') {
                                buttons[i].click();
                                return 'close icon';
                            }
                        }
                    }
                }
                return 'none';
            """)
            time.sleep(0.5)
        except Exception:
            pass
        self._force_close_panels()

    def verify_view_popup_read_only(self):
        """Check if the view popup fields are disabled/read-only.
        Checks both input elements AND mat-select dropdowns."""
        try:
            return self.driver.execute_script("""
                var fields = document.querySelectorAll('mat-form-field');
                for (var i = 0; i < fields.length; i++) {
                    // Check input elements (Conversion Factor)
                    var input = fields[i].querySelector('input');
                    if (input && !input.disabled && !input.readOnly) {
                        return false;
                    }
                    // Check mat-select dropdowns (Source UOM, Target UOM)
                    var select = fields[i].querySelector('mat-select');
                    if (select) {
                        var ariaDisabled = select.getAttribute('aria-disabled');
                        var classDisabled = select.classList.contains('mat-mdc-select-disabled');
                        if (ariaDisabled !== 'true' && !classDisabled) {
                            return false;
                        }
                    }
                }
                return true;
            """)
        except Exception:
            return False