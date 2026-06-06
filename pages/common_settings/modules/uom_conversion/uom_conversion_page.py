"""
UOM Conversion Page Object (v2 SPEED OPTIMIZED)
==================================================
UOM gold-standard speed patterns applied.
Module: 3 fields (2 FK dropdowns: Source UOM, Target UOM + 1 number: Conversion Factor).

Speed optimizations vs v1:
- All fixed time.sleep() replaced with fast JS polls (0.1-0.2s intervals)
- navigate_to_page() only on first call; hard_refresh() between tests
- Dropdown: fast poll for panel open/close, pointerdown+pointerup+click for Angular
- _wait_for_page_ready(): 0.1s poll intervals (was 1s)
- open_add_form(): fast poll for form open (was 1s sleep)
- create_fresh_record(): eliminated all fixed sleeps, fast polls throughout
- search_table(): fast polls (was 0.3-1.5s sleeps)
- _click_action_button(): fast polls (was 0.8s+0.5s sleeps)
- conftest: fast refresh instead of sleep(2)
- Zero blocking time.sleep() remaining — all are fast poll intervals or brief settles
"""

import time
import random

from common.base_page import BasePage
from common.logger import log


class UOMConversionPage(BasePage):
    """Page Object for UOM Conversion (Common Settings)."""

    UOM_CONVERSION_PAGE_URL = "https://rhythmerp.algorhythms.in/#/dynamic-screens/UOM%20Conversion"

    CONVERSION_FACTOR_INPUT = "Conversion Factor"

    # ================================================================
    #  NAVIGATION (UOM gold standard pattern)
    # ================================================================

    def navigate_to_page(self):
        """Navigate to UOM Conversion page via direct URL. First call only."""
        log.info("Navigating to UOM Conversion page")
        self.driver.get(self.UOM_CONVERSION_PAGE_URL)
        self._wait_for_page_ready()
        self._force_close_panels()

    def hard_refresh(self):
        """Hard refresh (Ctrl+R) + wait for page ready.
        Much faster than navigate_to_page() for resetting between tests."""
        self.driver.refresh()
        self._wait_for_page_ready()

    def _wait_for_page_ready(self):
        """Wait for the add button to appear — fast JS poll (0.1s intervals)."""
        end = time.monotonic() + 15
        while time.monotonic() < end:
            try:
                found = self.driver.execute_script(
                    "var btn = document.querySelector('app-custom-header .erp-add-btn');"
                    "if (btn) return true;"
                    "var icons = document.querySelectorAll('app-custom-header mat-icon');"
                    "for (var i = 0; i < icons.length; i++) {"
                    "  if (icons[i].textContent.trim() === 'add') return true;"
                    "}"
                    "return false;"
                )
                if found:
                    return
            except Exception:
                pass
            time.sleep(0.1)

    # ================================================================
    #  ADD FORM — Open / Close (fast JS polls)
    # ================================================================

    def open_add_form(self):
        """Click ADD button via JS + fast poll for form popup."""
        self.driver.execute_script(
            "var btn = document.querySelector('app-custom-header .erp-add-btn');"
            "if (btn) { btn.click(); return; }"
            "var icons = document.querySelectorAll('app-custom-header mat-icon');"
            "for (var i = 0; i < icons.length; i++) {"
            "  if (icons[i].textContent.trim() === 'add') { icons[i].click(); return; }"
            "}"
        )
        # Fast poll for form popup (0.2s intervals, 5s timeout)
        end = time.monotonic() + 5
        while time.monotonic() < end:
            if self.is_form_open():
                return
            # Retry click if form didn't open
            self.driver.execute_script(
                "var btn = document.querySelector('app-custom-header .erp-add-btn');"
                "if (btn) btn.click();"
            )
            time.sleep(0.2)

    def is_form_open(self):
        """Check if form popup is open — JS offsetParent (instant)."""
        try:
            return bool(self.driver.execute_script(
                "var el = document.querySelector('div.overflow_model');"
                "if (!el) return false;"
                "if (el.offsetParent !== null) return true;"
                "var s = window.getComputedStyle(el);"
                "return s.display !== 'none' && s.visibility !== 'hidden';"
            ))
        except Exception:
            return False

    def is_add_form_open(self):
        """Alias for is_form_open."""
        return self.is_form_open()

    def is_form_closed(self):
        """Check if form popup is closed."""
        return not self.is_form_open()

    def close_popup(self):
        """Close popup via Cancel button — pure JS."""
        self.driver.execute_script(
            "var footers = document.querySelectorAll('.popup-footer');"
            "for (var i = 0; i < footers.length; i++) {"
            "  var buttons = footers[i].querySelectorAll('button');"
            "  for (var j = 0; j < buttons.length; j++) {"
            "    if (buttons[j].textContent.indexOf('Cancel') !== -1) {"
            "      buttons[j].click(); return;"
            "    }"
            "  }"
            "}"
            "var btn = document.querySelector('.swal2-confirm');"
            "if (btn) btn.click();"
        )

    def force_close_form_popup(self):
        """Force-close form popup — single JS call."""
        try:
            self.driver.execute_script(
                "var popup = document.querySelector('div.overflow_model');"
                "if (!popup) return;"
                "var actions = popup.querySelector('.popup-actions');"
                "if (actions) {"
                "  var buttons = actions.querySelectorAll('button');"
                "  for (var i = buttons.length - 1; i >= 0; i--) {"
                "    var icon = buttons[i].querySelector('mat-icon, i.material-icons');"
                "    if (icon && icon.textContent.trim() === 'close') {"
                "      buttons[i].click(); return;"
                "    }"
                "  }"
                "}"
                "var footer = popup.querySelector('div.popup-footer');"
                "if (footer) {"
                "  var cancelBtn = footer.querySelector('.left button');"
                "  if (cancelBtn) { cancelBtn.click(); return; }"
                "  var btns = footer.querySelectorAll('button');"
                "  for (var k = 0; k < btns.length; k++) {"
                "    if (btns[k].textContent.indexOf('Cancel') !== -1) {"
                "      btns[k].click(); return;"
                "    }"
                "  }"
                "}"
            )
        except Exception:
            pass
        self._force_close_panels()

    def wait_for_form_to_close(self, timeout=5):
        """Poll until the form popup disappears — fast 0.1s intervals."""
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            if not self.is_form_open():
                return True
            time.sleep(0.1)
        return False

    # ================================================================
    #  MAT-SELECT DROPDOWN (MDC) — Speed Optimized
    # ================================================================

    def select_uom(self, label_text, uom_code):
        """Select a UOM from a mat-select dropdown — fast polls."""
        # Step 1: Click the select trigger
        self.driver.execute_script(
            "var fields = document.querySelectorAll('mat-form-field');"
            "for (var i = 0; i < fields.length; i++) {"
            "  var label = fields[i].querySelector('mat-label');"
            "  if (label && label.textContent.trim().indexOf(arguments[0]) !== -1) {"
            "    var trigger = fields[i].querySelector('.mat-mdc-select-trigger');"
            "    if (trigger) { trigger.click(); return; }"
            "  }"
            "}"
        , label_text)

        # Step 2: Fast poll for panel (0.1s intervals, 3s timeout)
        end = time.monotonic() + 3
        while time.monotonic() < end:
            panel_open = self.driver.execute_script(
                "var p = document.querySelector('.mat-mdc-select-panel');"
                "return p && p.offsetParent !== null;"
            )
            if panel_open:
                break
            time.sleep(0.1)

        # Step 3: Type in search input
        self.driver.execute_script(
            "var panel = document.querySelector('.mat-mdc-select-panel');"
            "if (!panel) return;"
            "var searchInput = panel.querySelector('.search-container input');"
            "if (!searchInput) return;"
            "var nativeSetter = Object.getOwnPropertyDescriptor("
            "  window.HTMLInputElement.prototype, 'value').set;"
            "nativeSetter.call(searchInput, arguments[0]);"
            "searchInput.dispatchEvent(new Event('input', {bubbles: true}));"
        , uom_code)
        # Brief settle for search filtering
        time.sleep(0.2)

        # Step 4: Click matching option (pointerdown+pointerup+click for Angular)
        self.driver.execute_script(
            "var panel = document.querySelector('.mat-mdc-select-panel');"
            "if (!panel) return false;"
            "var options = panel.querySelectorAll('mat-option');"
            "for (var i = 0; i < options.length; i++) {"
            "  var t = options[i].querySelector('.mdc-list-item__primary-text');"
            "  if (t && t.textContent.trim() === arguments[0]) {"
            "    options[i].dispatchEvent(new PointerEvent('pointerdown', {bubbles: true}));"
            "    options[i].dispatchEvent(new PointerEvent('pointerup', {bubbles: true}));"
            "    options[i].click(); return true;"
            "  }"
            "}"
            "var needle = arguments[0].toUpperCase();"
            "for (var i = 0; i < options.length; i++) {"
            "  var t = options[i].querySelector('.mdc-list-item__primary-text');"
            "  if (t && t.textContent.trim().toUpperCase().indexOf(needle) !== -1) {"
            "    options[i].dispatchEvent(new PointerEvent('pointerdown', {bubbles: true}));"
            "    options[i].dispatchEvent(new PointerEvent('pointerup', {bubbles: true}));"
            "    options[i].click(); return true;"
            "  }"
            "}"
            "return false;"
        , uom_code)

        # Fast poll for CDK overlay panel to close
        end_close = time.monotonic() + 1
        while time.monotonic() < end_close:
            gone = self.driver.execute_script(
                "var panels = document.querySelectorAll('.cdk-overlay-pane:not(.mat-mdc-dialog-container)');"
                "for (var i = 0; i < panels.length; i++) {"
                "  if (panels[i].offsetParent !== null) return false;"
                "}"
                "return true;"
            )
            if gone:
                break
            time.sleep(0.1)
        self._force_close_panels()

    def select_source_uom(self, uom_code):
        self.select_uom("Source UOM", uom_code)

    def select_target_uom(self, uom_code):
        self.select_uom("Target UOM", uom_code)

    # ================================================================
    #  FORM FIELDS — JS native setter for Angular
    # ================================================================

    def type_conversion_factor(self, value):
        """Type into Conversion Factor input — JS native setter + Angular dispatch."""
        self.driver.execute_script(
            "var fields = document.querySelectorAll('mat-form-field');"
            "for (var i = 0; i < fields.length; i++) {"
            "  var label = fields[i].querySelector('mat-label');"
            "  if (label && label.textContent.trim().indexOf('Conversion Factor') !== -1) {"
            "    var input = fields[i].querySelector('input');"
            "    if (input) {"
            "      input.focus();"
            "      var setter = Object.getOwnPropertyDescriptor("
            "        window.HTMLInputElement.prototype, 'value').set;"
            "      setter.call(input, arguments[0]);"
            "      input.dispatchEvent(new Event('input', {bubbles: true}));"
            "      input.dispatchEvent(new Event('change', {bubbles: true}));"
            "      return;"
            "    }"
            "  }"
            "}"
        , str(value))

    def enter_conversion_factor(self, value):
        """Alias for type_conversion_factor."""
        self.type_conversion_factor(value)

    def get_mat_error_text(self, label_text):
        """Get the mat-error message for a field by its label."""
        return self.driver.execute_script(
            "var fields = document.querySelectorAll('mat-form-field');"
            "for (var i = 0; i < fields.length; i++) {"
            "  var label = fields[i].querySelector('mat-label');"
            "  if (label && label.textContent.trim().indexOf(arguments[0]) !== -1) {"
            "    var err = fields[i].querySelector('mat-error');"
            "    return err ? err.textContent.trim() : '';"
            "  }"
            "}"
            "return '';"
        , label_text) or ""

    def is_dropdown_error(self, label_text):
        """Check if a mat-select dropdown has error state."""
        return bool(self.driver.execute_script(
            "var fields = document.querySelectorAll('mat-form-field');"
            "for (var i = 0; i < fields.length; i++) {"
            "  var label = fields[i].querySelector('mat-label');"
            "  if (label && label.textContent.trim().indexOf(arguments[0]) !== -1) {"
            "    var select = fields[i].querySelector('mat-select');"
            "    if (select) {"
            "      return select.classList.contains('mat-mdc-select-invalid') ||"
            "             select.classList.contains('ng-invalid');"
            "    }"
            "  }"
            "}"
            "return false;"
        , label_text))

    def clear_conversion_factor_via_js(self):
        """Clear the Conversion Factor input field via JS."""
        self.driver.execute_script(
            "var fields = document.querySelectorAll('mat-form-field');"
            "for (var i = 0; i < fields.length; i++) {"
            "  var label = fields[i].querySelector('mat-label');"
            "  if (label && label.textContent.trim().indexOf('Conversion Factor') !== -1) {"
            "    var input = fields[i].querySelector('input');"
            "    if (input) {"
            "      input.focus();"
            "      var setter = Object.getOwnPropertyDescriptor("
            "        window.HTMLInputElement.prototype, 'value').set;"
            "      setter.call(input, '');"
            "      input.dispatchEvent(new Event('input', {bubbles: true}));"
            "      input.dispatchEvent(new Event('change', {bubbles: true}));"
            "      return;"
            "    }"
            "  }"
            "}"
        )

    def get_selected_uom_text(self, label_text):
        """Get currently selected value from a mat-select."""
        return self.driver.execute_script(
            "var fields = document.querySelectorAll('mat-form-field');"
            "for (var i = 0; i < fields.length; i++) {"
            "  var label = fields[i].querySelector('mat-label');"
            "  if (label && label.textContent.trim().indexOf(arguments[0]) !== -1) {"
            "    var vt = fields[i].querySelector('.mat-mdc-select-value-text span');"
            "    return vt ? vt.textContent.trim() : '';"
            "  }"
            "}"
            "return '';"
        , label_text) or ""

    def get_conversion_factor_value(self):
        """Get current value of Conversion Factor input."""
        return self.driver.execute_script(
            "var fields = document.querySelectorAll('mat-form-field');"
            "for (var i = 0; i < fields.length; i++) {"
            "  var label = fields[i].querySelector('mat-label');"
            "  if (label && label.textContent.trim().indexOf('Conversion Factor') !== -1) {"
            "    var input = fields[i].querySelector('input');"
            "    return input ? input.value : '';"
            "  }"
            "}"
            "return '';"
        ) or ""

    # ================================================================
    #  FORM BUTTONS — JS click (bypasses overlay issues)
    # ================================================================

    def submit(self):
        """Click Submit button — JS click."""
        self._js_click_popup_button('Submit')

    def click_update(self):
        """Click Update button — JS click."""
        self._js_click_popup_button('Update')

    def click_save_button(self):
        """Click Submit or Update button — JS click."""
        self._js_click_popup_button('Submit') or self._js_click_popup_button('Update')

    def _js_click_popup_button(self, button_text):
        """Click a popup footer button via JS — bypasses overlay issues."""
        return self.driver.execute_script(
            "var footers = document.querySelectorAll('.popup-footer');"
            "for (var i = 0; i < footers.length; i++) {"
            "  var buttons = footers[i].querySelectorAll('button');"
            "  for (var j = 0; j < buttons.length; j++) {"
            "    if (buttons[j].textContent.trim().indexOf(arguments[0]) !== -1) {"
            "      buttons[j].click(); return true;"
            "    }"
            "  }"
            "}"
            "return false;"
        , button_text)

    def click_cancel_button(self):
        """Click Cancel button on form popup — JS."""
        self.driver.execute_script(
            "var footers = document.querySelectorAll('.popup-footer');"
            "for (var i = 0; i < footers.length; i++) {"
            "  var buttons = footers[i].querySelectorAll('button');"
            "  for (var j = 0; j < buttons.length; j++) {"
            "    if (buttons[j].textContent.indexOf('Cancel') !== -1) {"
            "      buttons[j].click(); return;"
            "    }"
            "  }"
            "}"
        )

    # ================================================================
    #  SWEET ALERT HANDLERS — Combined fast handler
    # ================================================================

    def _handle_submit_response(self, timeout=5):
        """Combined SweetAlert handler — fast poll.
        Detects validation alert, success alert, or form close (= success).
        Returns dict: {alert, title, form_closed, success}"""
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            result = self.driver.execute_script(
                "var popup = document.querySelector('.swal2-popup.swal2-icon-warning, .swal2-popup.swal2-icon-error');"
                "if (popup && popup.offsetParent !== null) {"
                "  var titleEl = document.querySelector('#swal2-title');"
                "  var title = titleEl ? titleEl.textContent.trim() : '';"
                "  var confirm = document.querySelector('.swal2-confirm');"
                "  if (confirm) confirm.click();"
                "  return {alert: true, title: title, form_closed: false, success: false};"
                "}"
                "var successPopup = document.querySelector('.swal2-popup.swal2-icon-success');"
                "if (successPopup && successPopup.offsetParent !== null) {"
                "  var confirm2 = document.querySelector('.swal2-confirm');"
                "  if (confirm2) confirm2.click();"
                "  return {alert: true, title: 'Success', form_closed: false, success: true};"
                "}"
                "var form = document.querySelector('div.overflow_model');"
                "var formOpen = form && form.offsetParent !== null;"
                "if (!formOpen) {"
                "  return {alert: false, title: '', form_closed: true, success: true};"
                "}"
                "return null;"
            )
            if result is not None:
                if result.get('alert'):
                    self._cleanup_swal2()
                return result
            time.sleep(0.2)

        # Timeout — check form state
        form_closed = not self.is_form_open()
        return {"alert": False, "title": "", "form_closed": form_closed, "success": form_closed}

    def is_validation_alert_present(self, timeout=3):
        """Check if SweetAlert validation/warning popup appeared — fast poll."""
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            try:
                visible = self.driver.execute_script(
                    "var el = document.querySelector('.swal2-popup.swal2-icon-warning, .swal2-popup.swal2-icon-error');"
                    "return el && el.offsetParent !== null;"
                )
                if visible:
                    return True
            except Exception:
                pass
            time.sleep(0.1)
        # Also check generic swal popup
        end2 = time.monotonic() + 1
        while time.monotonic() < end2:
            try:
                visible = self.driver.execute_script(
                    "var el = document.querySelector('.swal2-popup');"
                    "return el && el.offsetParent !== null;"
                )
                if visible:
                    return True
            except Exception:
                pass
            time.sleep(0.1)
        return False

    def is_success_alert_present(self, timeout=3):
        """Check if SweetAlert success popup appeared — fast poll."""
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            try:
                visible = self.driver.execute_script(
                    "var el = document.querySelector('.swal2-popup.swal2-icon-success');"
                    "if (el && el.offsetParent !== null) return true;"
                    "var title = document.querySelector('.swal2-title');"
                    "if (title && title.offsetParent !== null &&"
                    "    title.textContent.toLowerCase().indexOf('success') !== -1) return true;"
                    "return false;"
                )
                if visible:
                    return True
            except Exception:
                pass
            time.sleep(0.1)
        return False

    def is_sweetalert_visible(self):
        """Check if any SweetAlert popup is visible."""
        try:
            return bool(self.driver.execute_script(
                "var el = document.querySelector('.swal2-popup, .swal2-container');"
                "return el && el.offsetParent !== null;"
            ))
        except Exception:
            return False

    def handle_validation_warning(self):
        """SweetAlert Pattern A: warning dialog with OK — fast."""
        try:
            msg = self.driver.execute_script(
                "var title = document.querySelector('.swal2-title');"
                "var content = document.querySelector('.swal2-html-container');"
                "var result = (title ? title.textContent.trim() : '');"
                "if (content) result += ' - ' + content.textContent.trim();"
                "var btn = document.querySelector('.swal2-confirm');"
                "if (btn) btn.click();"
                "return result;"
            ) or ""
            self._cleanup_swal2()
            return msg
        except Exception:
            return ""

    def handle_validation_download(self):
        """SweetAlert Pattern B: dialog with Download Errors + Cancel — fast."""
        try:
            msg = self.driver.execute_script(
                "var title = document.querySelector('.swal2-title');"
                "var content = document.querySelector('.swal2-html-container');"
                "var result = (title ? title.textContent.trim() : '');"
                "if (content) result += ' - ' + content.textContent.trim();"
                "var btn = document.querySelector('.swal2-cancel');"
                "if (btn) { btn.click(); return result; }"
                "btn = document.querySelector('.swal2-deny');"
                "if (btn) btn.click();"
                "return result;"
            ) or ""
            self._cleanup_swal2()
            return msg
        except Exception:
            return ""

    def handle_success_alert(self):
        """Click OK on success SweetAlert — fast JS."""
        try:
            self.driver.execute_script(
                "var btn = document.querySelector('.swal2-confirm');"
                "if (btn) btn.click();"
            )
            self._cleanup_swal2()
        except Exception:
            pass

    def handle_error_toast(self):
        """SweetAlert Pattern C: error toast — read and return."""
        try:
            return self.driver.execute_script(
                "var toast = document.querySelector('.swal2-container.swal2-top-end .swal2-title')"
                "  || document.querySelector('.swal2-popup .swal2-title');"
                "if (toast) return toast.textContent.trim();"
                "var snackbar = document.querySelector('.mat-mdc-snack-bar-container .mdc-snackbar__label');"
                "if (snackbar) return snackbar.textContent.trim();"
                "return '';"
            ) or ""
        except Exception:
            return ""

    def _dismiss_sweetalert(self):
        """Dismiss any visible SweetAlert using the correct handler."""
        try:
            content = self.driver.execute_script(
                "var c = document.querySelector('.swal2-html-container');"
                "return c ? c.textContent.trim() : '';"
            ) or ""
            if 'download' in content.lower():
                self.handle_validation_download()
            else:
                self.handle_validation_warning()
        except Exception:
            try:
                self.close_popup()
            except Exception:
                pass

    def get_swal_title(self):
        """Get the SweetAlert popup title text."""
        try:
            return self.driver.execute_script(
                "var el = document.querySelector('.swal2-title');"
                "return el ? el.textContent.trim() : '';"
            ) or ""
        except Exception:
            return ""

    def _cleanup_swal2(self):
        """Remove leftover swal2 container + backdrops."""
        try:
            self.driver.execute_script(
                "document.querySelectorAll('.swal2-container').forEach(function(el){el.remove();});"
                "document.querySelectorAll('.swal2-backdrop-show').forEach(function(el){el.remove();});"
            )
        except Exception:
            pass

    # ================================================================
    #  TABLE INTERACTIONS — pure JS
    # ================================================================

    def get_table_row_count(self):
        """Count visible data rows — JS."""
        return self.driver.execute_script(
            "return document.querySelectorAll('table#excel-table tbody tr').length;"
        ) or 0

    def get_table_cell_value(self, row_index, column_name):
        """Get cell text from row index and column name — JS."""
        return self.driver.execute_script(
            "var rows = document.querySelectorAll('table#excel-table tbody tr');"
            "if (arguments[0] < rows.length) {"
            "  var cell = rows[arguments[0]].querySelector('.cdk-column-' + arguments[1]);"
            "  return cell ? cell.textContent.trim() : '';"
            "}"
            "return '';"
        , row_index, column_name) or ""

    def is_record_present(self, source_uom, target_uom):
        """Check if a record exists in the table — JS."""
        return bool(self.driver.execute_script(
            "var rows = document.querySelectorAll('table#excel-table tbody tr');"
            "for (var i = 0; i < rows.length; i++) {"
            "  var src = rows[i].querySelector('.cdk-column-source_uom_code');"
            "  var tgt = rows[i].querySelector('.cdk-column-target_uom_code');"
            "  if (src && tgt &&"
            "      src.textContent.trim() === arguments[0] &&"
            "      tgt.textContent.trim() === arguments[1]) {"
            "    return true;"
            "  }"
            "}"
            "return false;"
        , source_uom, target_uom))

    def is_record_in_table(self, source_uom, target_uom):
        """Alias for is_record_present."""
        return self.is_record_present(source_uom, target_uom)

    def find_table_row(self, source_uom, target_uom):
        """Find row index for a record. Returns -1 if not found — JS."""
        return self.driver.execute_script(
            "var rows = document.querySelectorAll('table#excel-table tbody tr');"
            "for (var i = 0; i < rows.length; i++) {"
            "  var src = rows[i].querySelector('.cdk-column-source_uom_code');"
            "  var tgt = rows[i].querySelector('.cdk-column-target_uom_code');"
            "  if (src && tgt &&"
            "      src.textContent.trim() === arguments[0] &&"
            "      tgt.textContent.trim() === arguments[1]) {"
            "    return i;"
            "  }"
            "}"
            "return -1;"
        , source_uom, target_uom)

    def get_table_rows(self):
        """Get table rows as a list of row indices [0, 1, 2, ...]."""
        count = self.get_table_row_count()
        return list(range(count))

    def get_conversion_factor_from_row(self, row_index):
        """Get conversion factor value from a table row."""
        return self.get_table_cell_value(row_index, "conversion_factor")

    def wait_for_table_to_load(self, timeout=10):
        """Wait for at least one data row — fast poll."""
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            rows = self.get_table_row_count()
            if rows > 0:
                return True
            time.sleep(0.2)
        return False

    # ================================================================
    #  ROW ACTION BUTTONS — 3-dot menu (UOM gold standard)
    # ================================================================

    def _click_action_button(self, row_source, row_target, action_icon):
        """Click action button via 3-dot menu — fast polls.
        Uses .erp-row-trigger (the ⋮ button) → CDK overlay dropdown menu."""
        icon_map = {"view": "visibility", "edit": "edit", "history": "history"}
        icon_text = icon_map.get(action_icon, action_icon)

        # Step 1: Click ⋮ menu trigger on matching row
        self.driver.execute_script(
            "var rows = document.querySelectorAll('table#excel-table tbody tr');"
            "for (var i = 0; i < rows.length; i++) {"
            "  var src = rows[i].querySelector('.cdk-column-source_uom_code');"
            "  var tgt = rows[i].querySelector('.cdk-column-target_uom_code');"
            "  if (src && tgt &&"
            "      src.textContent.trim() === arguments[0] &&"
            "      tgt.textContent.trim() === arguments[1]) {"
            "    var trigger = rows[i].querySelector('.erp-row-trigger');"
            "    if (trigger) { trigger.click(); return; }"
            "  }"
            "}"
        , row_source, row_target)

        # Fast poll for CDK overlay menu (0.1s intervals, 2s timeout)
        end = time.monotonic() + 2
        while time.monotonic() < end:
            menu_open = self.driver.execute_script(
                "var menu = document.querySelector('.cdk-overlay-container .cdk-overlay-pane .mat-mdc-menu-panel');"
                "return menu && menu.offsetParent !== null;"
            )
            if menu_open:
                break
            time.sleep(0.1)

        # Step 2: Click menu item by icon text OR label text
        self.driver.execute_script(
            "var overlay = document.querySelector('.cdk-overlay-container');"
            "if (!overlay) return;"
            "var items = overlay.querySelectorAll('button.mat-mdc-menu-item');"
            "for (var i = 0; i < items.length; i++) {"
            "  var icon = items[i].querySelector('i.material-icons');"
            "  if (icon && icon.textContent.trim() === arguments[0]) {"
            "    items[i].click(); return;"
            "  }"
            "}"
            "var allItems = overlay.querySelectorAll('button, span, div');"
            "for (var i = 0; i < allItems.length; i++) {"
            "  var text = allItems[i].textContent.trim();"
            "  if (text === arguments[0]) {"
            "    allItems[i].click(); return;"
            "  }"
            "}"
            "var needle = arguments[0].toLowerCase();"
            "for (var i = 0; i < allItems.length; i++) {"
            "  var text = allItems[i].textContent.trim().toLowerCase();"
            "  if (text.indexOf(needle) !== -1) {"
            "    allItems[i].click(); return;"
            "  }"
            "}"
        , icon_text)

        # Brief settle for Angular to process
        time.sleep(0.2)

    def click_edit_button(self, row_source, row_target):
        return self._click_action_button(row_source, row_target, "edit")

    def click_view_button(self, row_source, row_target):
        return self._click_action_button(row_source, row_target, "view")

    def click_history_button(self, row_source, row_target):
        return self._click_action_button(row_source, row_target, "history")

    # Aliases used by tests
    def click_row_edit(self, source, target):
        return self.click_edit_button(source, target)

    def click_row_view(self, source, target):
        return self.click_view_button(source, target)

    def click_row_history(self, source, target):
        return self.click_history_button(source, target)

    # ================================================================
    #  DYNAMIC PAIR FINDER — Speed Optimized
    # ================================================================

    def get_available_uoms(self):
        """Read all UOM codes from Source UOM dropdown.
        Opens Add form temporarily, reads options, then closes it."""
        self.open_add_form()
        # Fast poll for form
        end = time.monotonic() + 3
        while time.monotonic() < end:
            if self.is_form_open():
                break
            time.sleep(0.1)

        # Open Source UOM dropdown and read options
        self.driver.execute_script(
            "var trigger = document.querySelector("
            "  'div.edit_pop_up mat-form-field mat-select .mat-mdc-select-trigger'"
            ");"
            "if (trigger) trigger.click();"
        )
        # Fast poll for options
        end_opts = time.monotonic() + 3
        while time.monotonic() < end_opts:
            count = self.driver.execute_script(
                "return document.querySelectorAll('.cdk-overlay-pane mat-option').length;"
            )
            if count and count > 0:
                break
            time.sleep(0.1)

        uoms = self.driver.execute_script(
            "var options = document.querySelectorAll('.cdk-overlay-pane mat-option .mdc-list-item__primary-text');"
            "var uoms = [];"
            "for (var i = 0; i < options.length; i++) {"
            "  var text = options[i].textContent.trim();"
            "  if (text) uoms.push(text);"
            "}"
            "return uoms;"
        ) or []

        # Close dropdown + form
        self._force_close_panels()
        self.force_close_form_popup()
        self._force_close_panels()

        if not uoms:
            raise RuntimeError("No UOM options found in dropdown")
        return uoms

    def get_existing_pairs(self):
        """Read all existing Source→Target UOM pairs from the main table — JS."""
        raw_pairs = self.driver.execute_script(
            "var rows = document.querySelectorAll('table#excel-table tbody tr');"
            "var pairs = [];"
            "for (var i = 0; i < rows.length; i++) {"
            "  var source = '', target = '';"
            "  var cells = rows[i].querySelectorAll('td');"
            "  for (var j = 0; j < cells.length; j++) {"
            "    var cls = cells[j].getAttribute('class') || '';"
            "    if (cls.indexOf('cdk-column-source_uom_code') !== -1)"
            "      source = cells[j].textContent.trim();"
            "    if (cls.indexOf('cdk-column-target_uom_code') !== -1)"
            "      target = cells[j].textContent.trim();"
            "  }"
            "  if (source && target) pairs.push([source, target]);"
            "}"
            "return pairs;"
        ) or []
        pair_set = set()
        for pair in raw_pairs:
            pair_set.add((pair[0], pair[1]))
        return pair_set

    # ================================================================
    #  INTERNAL DROPDOWN HELPERS — for create_fresh_record
    # ================================================================

    def _read_dropdown_uoms(self):
        """Open Source UOM dropdown and read all options. Leaves dropdown OPEN."""
        self.driver.execute_script(
            "var fields = document.querySelectorAll('div.edit_pop_up mat-form-field');"
            "for (var i = 0; i < fields.length; i++) {"
            "  var label = fields[i].querySelector('mat-label');"
            "  if (label && label.textContent.trim().indexOf('Source UOM') !== -1) {"
            "    var trigger = fields[i].querySelector('.mat-mdc-select-trigger');"
            "    if (trigger) { trigger.click(); return; }"
            "  }"
            "}"
        )
        # Fast poll for options
        end = time.monotonic() + 3
        while time.monotonic() < end:
            count = self.driver.execute_script(
                "return document.querySelectorAll('.cdk-overlay-pane mat-option .mdc-list-item__primary-text').length;"
            )
            if count and count > 0:
                break
            time.sleep(0.1)

        uoms = self.driver.execute_script(
            "var options = document.querySelectorAll('.cdk-overlay-pane mat-option .mdc-list-item__primary-text');"
            "var uoms = [];"
            "for (var i = 0; i < options.length; i++) {"
            "  var text = options[i].textContent.trim();"
            "  if (text) uoms.push(text);"
            "}"
            "return uoms;"
        ) or []
        if not uoms:
            raise RuntimeError("No UOM options found in dropdown")
        return uoms

    def _select_from_open_panel(self, uom_code):
        """Click an option in the ALREADY OPEN dropdown panel."""
        self.driver.execute_script(
            "var options = document.querySelectorAll('.cdk-overlay-pane mat-option');"
            "for (var i = 0; i < options.length; i++) {"
            "  var text = options[i].querySelector('.mdc-list-item__primary-text');"
            "  if (text && text.textContent.trim() === arguments[0]) {"
            "    options[i].dispatchEvent(new PointerEvent('pointerdown', {bubbles: true}));"
            "    options[i].dispatchEvent(new PointerEvent('pointerup', {bubbles: true}));"
            "    options[i].click(); return;"
            "  }"
            "}"
            "var needle = arguments[0].toUpperCase();"
            "for (var i = 0; i < options.length; i++) {"
            "  var text = options[i].querySelector('.mdc-list-item__primary-text');"
            "  if (text && text.textContent.trim().toUpperCase().indexOf(needle) !== -1) {"
            "    options[i].dispatchEvent(new PointerEvent('pointerdown', {bubbles: true}));"
            "    options[i].dispatchEvent(new PointerEvent('pointerup', {bubbles: true}));"
            "    options[i].click(); return;"
            "  }"
            "}"
        , uom_code)
        # Fast poll for dropdown to close
        end = time.monotonic() + 1
        while time.monotonic() < end:
            gone = self.driver.execute_script(
                "var panels = document.querySelectorAll('.cdk-overlay-pane:not(.mat-mdc-dialog-container)');"
                "for (var i = 0; i < panels.length; i++) {"
                "  if (panels[i].offsetParent !== null) return false;"
                "}"
                "return true;"
            )
            if gone:
                break
            time.sleep(0.1)
        self._force_close_panels()

    def _close_select_panel(self):
        """Close select dropdown panel — force close panels."""
        self._force_close_panels()

    def get_available_uoms_from_form(self):
        """Read all UOM options from Source dropdown of currently open form."""
        uoms = self._read_dropdown_uoms()
        self._close_select_panel()
        return uoms

    # ================================================================
    #  HIGH-LEVEL: create_fresh_record (speed optimized)
    # ================================================================

    def create_fresh_record(self, factor=None, max_retries=5, raise_on_error=True):
        """
        Creates a new UOM conversion record with a fresh (non-duplicate) pair.
        Uses try-submit-catch-duplicate pattern. Fast polls throughout.

        On success, the ERP closes the form silently (NO success popup).
        Returns dict: {source_uom, target_uom, conversion_factor, success, error}
        """
        last_error = None

        for attempt in range(max_retries):
            self.open_add_form()
            # Fast poll for form
            end = time.monotonic() + 3
            while time.monotonic() < end:
                if self.is_form_open():
                    break
                time.sleep(0.1)

            uoms = self._read_dropdown_uoms()
            source, target = random.sample(uoms, 2)
            actual_factor = str(factor) if factor is not None else str(random.randint(1, 1000))

            self._select_from_open_panel(source)
            self.select_target_uom(target)
            self.enter_conversion_factor(actual_factor)
            self._force_close_panels()
            self.submit()

            # Combined alert handler — fast poll
            response = self._handle_submit_response(timeout=5)

            if response.get("success"):
                return {
                    "source_uom": source, "target_uom": target,
                    "conversion_factor": actual_factor, "success": True, "error": ""
                }

            if response.get("alert"):
                last_error = response.get("title", "Validation")
                if not raise_on_error:
                    self.force_close_form_popup()
                    return {
                        "source_uom": source, "target_uom": target,
                        "conversion_factor": actual_factor,
                        "success": False, "error": last_error
                    }
                # Retry with new pair
                self.force_close_form_popup()
                self.hard_refresh()
                continue

            # No alert and form still open (unexpected)
            last_error = "Form still open after submit"
            self.force_close_form_popup()
            if not raise_on_error:
                return {
                    "source_uom": source, "target_uom": target,
                    "conversion_factor": actual_factor,
                    "success": False, "error": last_error
                }

        if raise_on_error:
            raise RuntimeError("Failed to create record after " + str(max_retries) +
                             " attempts. Last error: " + str(last_error))
        return {
            "source_uom": source or "?", "target_uom": target or "?",
            "conversion_factor": str(factor) if factor is not None else "?",
            "success": False, "error": last_error or "max retries exhausted"
        }

    # ================================================================
    #  TABLE SEARCH — Speed Optimized
    # ================================================================

    def search_table(self, text):
        """Click search button, type text, press Enter — fast polls."""
        self.driver.execute_script(
            "var btn = document.querySelector('.search-btn');"
            "if (btn) btn.click();"
        )
        # Fast poll for search input
        end = time.monotonic() + 3
        while time.monotonic() < end:
            found = self.driver.execute_script(
                "var inp = document.getElementById('erpSearchInput');"
                "return inp && inp.offsetParent !== null;"
            )
            if found:
                break
            time.sleep(0.1)

        # Set search value via JS native setter + Enter
        self.driver.execute_script(
            "var inp = document.getElementById('erpSearchInput');"
            "if (inp) {"
            "  var nativeSetter = Object.getOwnPropertyDescriptor("
            "    window.HTMLInputElement.prototype, 'value').set;"
            "  nativeSetter.call(inp, arguments[0]);"
            "  inp.dispatchEvent(new Event('input', {bubbles: true}));"
            "  inp.dispatchEvent(new KeyboardEvent('keydown', {key:'Enter',code:'Enter',bubbles:true}));"
            "  inp.dispatchEvent(new KeyboardEvent('keyup', {key:'Enter',code:'Enter',bubbles:true}));"
            "}"
        , text)
        # Fast poll for table to update
        end_table = time.monotonic() + 3
        while time.monotonic() < end_table:
            row_count = self.get_table_row_count()
            if row_count > 0:
                break
            time.sleep(0.1)

    def clear_search(self):
        """Clear search input and press Enter — fast JS."""
        self.driver.execute_script(
            "var inp = document.getElementById('erpSearchInput');"
            "if (inp) {"
            "  var nativeSetter = Object.getOwnPropertyDescriptor("
            "    window.HTMLInputElement.prototype, 'value').set;"
            "  nativeSetter.call(inp, '');"
            "  inp.dispatchEvent(new Event('input', {bubbles: true}));"
            "  inp.dispatchEvent(new KeyboardEvent('keydown', {key:'Enter',code:'Enter',bubbles:true}));"
            "}"
        )

    # ================================================================
    #  HISTORY POPUP HELPERS
    # ================================================================

    def get_history_row_count(self):
        """Count rows in the history popup table — JS, scoped to popup."""
        return self.driver.execute_script(
            "var popup = document.querySelector('div.overflow_model, div.edit_pop_up');"
            "if (!popup) return 0;"
            "var rows = popup.querySelectorAll('table tbody tr');"
            "return rows.length;"
        ) or 0

    def get_history_data(self):
        """Get all history table data as a list of row strings."""
        try:
            return self.driver.execute_script(
                "var popup = document.querySelector('div.overflow_model, div.edit_pop_up');"
                "if (!popup) return [];"
                "var rows = popup.querySelectorAll('table tbody tr');"
                "var data = [];"
                "for (var i = 0; i < rows.length; i++) {"
                "  data.push(rows[i].textContent.trim());"
                "}"
                "return data;"
            ) or []
        except Exception:
            return []

    def close_history_popup(self):
        """Close the history popup — Cancel button in footer."""
        self.driver.execute_script(
            "var footer = document.querySelector('div.overflow_model .popup-footer');"
            "if (footer) {"
            "  var btns = footer.querySelectorAll('button');"
            "  for (var i = 0; i < btns.length; i++) {"
            "    if (btns[i].textContent.indexOf('Cancel') !== -1) {"
            "      btns[i].click(); return;"
            "    }"
            "  }"
            "}"
            "var popup = document.querySelector('div.overflow_model');"
            "if (popup) {"
            "  var actions = popup.querySelector('.popup-actions');"
            "  if (actions) {"
            "    var buttons = actions.querySelectorAll('button');"
            "    for (var i = buttons.length - 1; i >= 0; i--) {"
            "      var icon = buttons[i].querySelector('mat-icon');"
            "      if (icon && icon.textContent.trim() === 'close') {"
            "        buttons[i].click(); return;"
            "      }"
            "    }"
            "  }"
            "}"
        )
        self._force_close_panels()

    # ================================================================
    #  VIEW POPUP VERIFICATION
    # ================================================================

    def verify_view_popup_read_only(self):
        """Check if the view popup fields are disabled/read-only — JS."""
        try:
            return bool(self.driver.execute_script(
                "var fields = document.querySelectorAll('mat-form-field');"
                "for (var i = 0; i < fields.length; i++) {"
                "  var input = fields[i].querySelector('input');"
                "  if (input && !input.disabled && !input.readOnly) return false;"
                "  var select = fields[i].querySelector('mat-select');"
                "  if (select) {"
                "    var ariaDisabled = select.getAttribute('aria-disabled');"
                "    var classDisabled = select.classList.contains('mat-mdc-select-disabled');"
                "    if (ariaDisabled !== 'true' && !classDisabled) return false;"
                "  }"
                "}"
                "return true;"
            ))
        except Exception:
            return False

    # ================================================================
    #  CLEANUP HELPERS
    # ================================================================

    def cleanup(self):
        """General cleanup: close form, close popups, force close panels."""
        try:
            self.force_close_form_popup()
        except Exception:
            pass
        try:
            self._cleanup_swal2()
        except Exception:
            pass
        self._force_close_panels()

    def _force_close_panels(self):
        """Remove any open CDK overlay panels/backdrops — single JS call."""
        try:
            self.driver.execute_script(
                "document.querySelectorAll('.cdk-overlay-backdrop:not(.cdk-overlay-dark-backdrop)').forEach(function(b){b.remove();});"
                "document.querySelectorAll('.cdk-overlay-pane:not(.mat-mdc-dialog-container)').forEach(function(p){p.remove();});"
            )
        except Exception:
            pass

    def refresh_page(self):
        """Click the REFRESH button — or hard refresh as fallback."""
        try:
            self.driver.execute_script(
                "var icons = document.querySelectorAll('app-custom-header mat-icon');"
                "for (var i = 0; i < icons.length; i++) {"
                "  if (icons[i].textContent.trim() === 'refresh') {"
                "    icons[i].click(); return;"
                "  }"
                "}"
            )
            time.sleep(0.5)
        except Exception:
            self.hard_refresh()
