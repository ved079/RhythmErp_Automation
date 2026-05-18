"""
uom_conversion_page.py
----------------------
Page Object for RhythmERP -> Common Settings -> UOM Conversion.
Handles Create, View, Edit, and History operations.

Form Fields (Add / Edit):
  - Source UOM      (mat-select dropdown, required)
  - Target UOM      (mat-select dropdown, required)
  - Conversion Factor (text input, type="character", required)

Table Columns:
  View | Edit | History | Source UOM | Target UOM | Conversion Factor | Status
"""

import time
from common.base_page import BasePage
from common.logger import log


class UOMConversionPage(BasePage):
    """
    UOMConversionPage - Page Object for Common Settings > UOM Conversion.

    Covers:
    - Navigate to page
    - Create new UOM Conversion
    - Select UOMs from mat-select dropdowns
    - Enter / clear Conversion Factor
    - View (read-only), Edit, History
    - Validation alert handling (SweetAlert2)
    - CDK overlay / panel cleanup
    """

    # ================================================================
    # PAGE URL
    # ================================================================
    PAGE_URL = "https://rhythmerp.algorhythms.in/#/dynamic-screens/UOM%20Conversion"

    # ================================================================
    # HEADER BUTTONS
    # ================================================================
    ADD_BUTTON = ("css", "button.erp-add-btn")
    REFRESH_BUTTON = ("css", "div[mattooltip='REFRESH'] button")

    # ================================================================
    # MAIN TABLE
    # ================================================================
    TABLE_ROWS = ("css", "table#excel-table tbody tr")

    # ================================================================
    # FORM FIELDS
    # ================================================================
    CONVERSION_FACTOR_INPUT = ("css", "input[name='Conversion Factor']")

    # ================================================================
    # FORM FOOTER BUTTONS
    # ================================================================
    SUBMIT_BUTTON = ("xpath", "//div[@class='popup-footer']//button[contains(.,'Submit')]")
    UPDATE_BUTTON = ("xpath", "//div[@class='popup-footer']//button[contains(.,'Update')]")
    CANCEL_BUTTON = ("xpath", "//div[@class='popup-footer']//button[contains(.,'Cancel')]")

    # ================================================================
    # HISTORY POPUP
    # ================================================================
    HISTORY_HEADER = ("css", "app-dynamic-history .tbl-title h2")
    HISTORY_NO_DATA = ("css", "app-dynamic-history .no-data, app-dynamic-history img[alt='No Data Available']")
    HISTORY_NO_DATA_TEXT = ("xpath", "//app-dynamic-history//*[contains(text(),'No data available')]")
    HISTORY_TABLE_ROWS = ("css", "app-dynamic-history table#excel-table tbody tr")
    HISTORY_CANCEL_BUTTON = ("xpath", "//app-dynamic-history//div[@class='popup-footer']//button[contains(.,'Cancel')]")

    # ================================================================
    # NAVIGATION
    # ================================================================

    def navigate_to_page(self):
        """Navigate to UOM Conversion page via direct URL."""
        log.info("Navigating to UOM Conversion page")
        self.driver.get(self.PAGE_URL)
        self._wait_for_page_ready()
        self._force_close_panels()
        log.info("Arrived at UOM Conversion page")

    def _wait_for_page_ready(self):
        """Wait up to 20s for the page to load (table or search button)."""
        waited = 0
        while waited < 20:
            try:
                self.driver.find_element("css selector", "table#excel-table")
                log.info("Page ready (table found) after " + str(waited) + "s")
                return
            except Exception:
                pass
            time.sleep(1)
            waited += 1
        log.warning("Page ready check timed out after 20s")

    # ================================================================
    # ADD FORM
    # ================================================================

    def open_add_form(self):
        """Click the Add button to open the Create UOM Conversion form."""
        log.info("Opening Add UOM Conversion form")
        self._force_close_panels()
        self.click_with_retry(self.ADD_BUTTON)
        time.sleep(1)

    # ================================================================
    # MAT-SELECT DROPDOWN (Source UOM / Target UOM)
    # ================================================================

    def select_uom(self, label_text, uom_code):
        """
        Select a UOM from a mat-select dropdown by its label.
        Uses pure JS to:
          1. Find mat-select by mat-label text
          2. Click to open the dropdown panel
          3. Type in the search input
          4. Click the matching option
        """
        log.info("Selecting '" + uom_code + "' from '" + label_text + "' dropdown")

        # Step 1: Click mat-select to open panel
        js_open = """
        var fields = document.querySelectorAll('mat-form-field');
        for (var i = 0; i < fields.length; i++) {
            var label = fields[i].querySelector('mat-label');
            if (label && label.textContent.trim().indexOf(arguments[0]) !== -1) {
                var select = fields[i].querySelector('mat-select');
                if (select) {
                    select.click();
                    return 'opened';
                }
            }
        }
        throw new Error('mat-select with label containing "' + arguments[0] + '" not found');
        """
        self.driver.execute_script(js_open, label_text)
        time.sleep(1)

        # Step 2: Type in the search input inside the dropdown panel
        js_search = """
        var panel = document.querySelector('.mat-select-panel');
        if (!panel) throw new Error('mat-select panel not found');
        var searchInput = panel.querySelector('div.search-container input');
        if (!searchInput) throw new Error('Search input not found in dropdown');
        searchInput.value = '';
        searchInput.dispatchEvent(new Event('input', {bubbles: true}));
        searchInput.value = arguments[0];
        searchInput.dispatchEvent(new Event('input', {bubbles: true}));
        searchInput.dispatchEvent(new Event('keyup', {bubbles: true}));
        return 'typed: ' + arguments[0];
        """
        self.driver.execute_script(js_search, uom_code)
        time.sleep(1)

        # Step 3: Click the matching option
        js_select = """
        var options = document.querySelectorAll('mat-option');
        for (var i = 0; i < options.length; i++) {
            if (options[i].textContent.trim().indexOf(arguments[0]) !== -1) {
                options[i].click();
                return 'selected: ' + options[i].textContent.trim();
            }
        }
        throw new Error('Option "' + arguments[0] + '" not found in dropdown');
        """
        result = self.driver.execute_script(js_select, uom_code)
        log.info("  Dropdown selected: " + str(result))
        time.sleep(0.5)

    def select_source_uom(self, uom_code):
        """Select Source UOM from dropdown."""
        self.select_uom("Source UOM", uom_code)

    def select_target_uom(self, uom_code):
        """Select Target UOM from dropdown."""
        self.select_uom("Target UOM", uom_code)

    def is_dropdown_error(self, label_text):
        """Check if a mat-form-field (by label) has the invalid class."""
        js = """
        var fields = document.querySelectorAll('mat-form-field');
        for (var i = 0; i < fields.length; i++) {
            var label = fields[i].querySelector('mat-label');
            if (label && label.textContent.trim().indexOf(arguments[0]) !== -1) {
                var classes = fields[i].className || '';
                var invalidClasses = ['mat-mdc-form-field-invalid', 'mat-form-field-invalid', 'ng-invalid'];
                for (var j = 0; j < invalidClasses.length; j++) {
                    if (classes.indexOf(invalidClasses[j]) !== -1) {
                        return JSON.stringify({found: true, cls: invalidClasses[j]});
                    }
                }
                return JSON.stringify({found: false});
            }
        }
        return JSON.stringify({found: false, reason: 'label not found'});
        """
        result = self.driver.execute_script(js, label_text)
        log.info("is_dropdown_error('" + label_text + "'): " + str(result))
        import json
        data = json.loads(result) if result else {"found": False}
        return data.get("found", False)

    # ================================================================
    # CONVERSION FACTOR FIELD
    # ================================================================

    def enter_conversion_factor(self, value):
        """Clear and type a value into the Conversion Factor input."""
        log.info("Entering Conversion Factor: " + str(value))
        self.type_text(self.CONVERSION_FACTOR_INPUT, str(value))

    def get_conversion_factor_value(self):
        """Read the current value of the Conversion Factor input."""
        try:
            css = self.CONVERSION_FACTOR_INPUT[1]
            el = self.driver.find_element("css selector", css)
            return el.get_attribute("value") or ""
        except Exception:
            return ""

    def clear_conversion_factor_via_js(self):
        """Clear the Conversion Factor field using JS (for Angular model sync)."""
        log.info("Clearing Conversion Factor via JS")
        css = self.CONVERSION_FACTOR_INPUT[1]
        js = """
        var el = document.querySelector(arguments[0]);
        if (!el) throw new Error('Conversion Factor input not found');
        var nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
        nativeSetter.call(el, '');
        el.dispatchEvent(new Event('input', {bubbles: true}));
        el.dispatchEvent(new Event('change', {bubbles: true}));
        """
        self.driver.execute_script(js, css)

    # ================================================================
    # FORM ACTIONS
    # ================================================================

    def submit(self):
        """Click Submit on the Create form."""
        log.info("Clicking Submit")
        self.click_with_retry(self.SUBMIT_BUTTON)
        time.sleep(1)

    def click_update(self):
        """Click Update on the Edit form."""
        log.info("Clicking Update")
        self.click_with_retry(self.UPDATE_BUTTON)
        time.sleep(1)

    def close_popup(self):
        """Close any popup by clicking Cancel."""
        log.info("Closing popup")
        try:
            self.click_with_retry(self.CANCEL_BUTTON)
            time.sleep(1)
        except Exception:
            log.warning("Could not click Cancel, trying force close")
            self._force_close_panels()

    def force_close_form_popup(self):
        """Force-close any open form popup by clicking the X button via JS."""
        log.info("Force closing form popup")
        js = """
        var popup = document.querySelector('div.edit_pop_up');
        if (!popup) return 'no popup found';
        var closeBtn = popup.querySelector('button[mat-icon-button] mat-icon');
        if (!closeBtn) return 'no close button found';
        var btn = closeBtn.closest('button');
        if (btn) { btn.click(); return 'clicked close'; }
        return 'could not click';
        """
        result = self.driver.execute_script(js)
        log.info("Force close result: " + str(result))
        time.sleep(0.5)

    def is_add_form_open(self):
        """Check if the Add/Create form popup is currently open."""
        try:
            self.driver.find_element("css selector", "input[name='Conversion Factor']")
            return True
        except Exception:
            return False

    # ================================================================
    # TABLE OPERATIONS
    # ================================================================

    def get_table_rows(self):
        """Get all rows in the main table."""
        return self.find_elements(self.TABLE_ROWS)

    def is_record_in_table(self, source_uom, target_uom):
        """Check if a Source UOM + Target UOM pair exists in the table."""
        try:
            rows = self.get_table_rows()
            for row in rows:
                cells = row.find_elements("css selector", "td")
                # Columns: View | Edit | History | Source UOM | Target UOM | ConvFactor | Status
                if len(cells) >= 5:
                    src = cells[3].text.strip()
                    tgt = cells[4].text.strip()
                    if src == source_uom and tgt == target_uom:
                        return True
        except Exception:
            pass
        return False

    def find_table_row(self, source_uom, target_uom):
        """Find a table row by Source UOM + Target UOM. Returns WebElement or None."""
        try:
            rows = self.get_table_rows()
            for row in rows:
                cells = row.find_elements("css selector", "td")
                if len(cells) >= 5:
                    src = cells[3].text.strip()
                    tgt = cells[4].text.strip()
                    if src == source_uom and tgt == target_uom:
                        return row
        except Exception:
            pass
        return None

    def get_conversion_factor_from_row(self, row):
        """Read the Conversion Factor value from a table row."""
        try:
            cells = row.find_elements("css selector", "td")
            # Column index 5 = Conversion Factor
            if len(cells) >= 6:
                return cells[5].text.strip()
        except Exception:
            pass
        return ""

    # ================================================================
    # ROW ACTION BUTTONS (View / Edit / History) — pure JS
    # ================================================================

    def click_row_view(self, source_uom, target_uom):
        """Click the View button for a specific Source→Target row."""
        self._click_action_button(source_uom, target_uom, "cdk-column-view")
        time.sleep(1.5)

    def click_row_edit(self, source_uom, target_uom):
        """Click the Edit button for a specific Source→Target row."""
        self._click_action_button(source_uom, target_uom, "cdk-column-edit")
        time.sleep(1.5)

    def click_row_history(self, source_uom, target_uom):
        """Click the History button for a specific Source→Target row."""
        self._click_action_button(source_uom, target_uom, "cdk-column-archive")
        time.sleep(2)

    def _click_action_button(self, source_uom, target_uom, column_class):
        """Click an action button (View/Edit/History) for a row matching Source+Target UOM."""
        log.info("Clicking " + column_class + " for " + source_uom + " -> " + target_uom)
        js = """
        var table = document.querySelector('table#excel-table');
        if (!table) throw new Error('Table not found');
        var rows = table.querySelectorAll('tbody tr');
        for (var i = 0; i < rows.length; i++) {
            var cells = rows[i].querySelectorAll('td');
            // Source UOM = col 3, Target UOM = col 4
            if (cells.length >= 5) {
                var src = cells[3].textContent.trim();
                var tgt = cells[4].textContent.trim();
                if (src.indexOf(arguments[0]) !== -1 && tgt.indexOf(arguments[1]) !== -1) {
                    var btn = rows[i].querySelector('td.' + arguments[2] + ' button');
                    if (btn) {
                        btn.scrollIntoView({block:'center'});
                        btn.click();
                        return 'clicked';
                    }
                    throw new Error('Button column ' + arguments[2] + ' not found in row');
                }
            }
        }
        throw new Error('Row ' + arguments[0] + ' -> ' + arguments[1] + ' not found in table');
        """
        result = self.driver.execute_script(js, source_uom, target_uom, column_class)
        log.info("Successfully clicked " + column_class + ": " + str(result))
        return result

    # ================================================================
    # VIEW POPUP — read-only verification
    # ================================================================

    def verify_view_popup_read_only(self):
        """Verify the View popup has dropdowns disabled (read-only)."""
        log.info("Verifying View popup is read-only")

        # Check Source UOM mat-select is disabled
        src_disabled = self._is_mat_select_disabled("Source UOM")
        assert src_disabled, "Source UOM dropdown should be disabled in View mode"
        log.info("  [PASS] Source UOM dropdown is disabled")

        # Check Target UOM mat-select is disabled
        tgt_disabled = self._is_mat_select_disabled("Target UOM")
        assert tgt_disabled, "Target UOM dropdown should be disabled in View mode"
        log.info("  [PASS] Target UOM dropdown is disabled")

        # Check Conversion Factor input is disabled
        cf_disabled = self.get_attribute(self.CONVERSION_FACTOR_INPUT, "disabled")
        assert cf_disabled == "true", "Conversion Factor should be disabled in View mode"
        log.info("  [PASS] Conversion Factor field is disabled")

        # No Submit/Update button
        submit_present = self.is_present(self.SUBMIT_BUTTON, timeout=2)
        update_present = self.is_present(self.UPDATE_BUTTON, timeout=2)
        assert not submit_present, "Submit button should NOT be present in View mode"
        assert not update_present, "Update button should NOT be present in View mode"
        log.info("  [PASS] No Submit/Update button in View mode")

        assert self.is_present(self.CANCEL_BUTTON, timeout=3), "Cancel button should be present in View mode"
        log.info("  [PASS] Cancel button is present")

        log.info("View popup verified as read-only")

    def _is_mat_select_disabled(self, label_text):
        """Check if a mat-select (by label) is disabled."""
        js = """
        var fields = document.querySelectorAll('mat-form-field');
        for (var i = 0; i < fields.length; i++) {
            var label = fields[i].querySelector('mat-label');
            if (label && label.textContent.trim().indexOf(arguments[0]) !== -1) {
                var select = fields[i].querySelector('mat-select');
                if (select) return select.disabled ? 'true' : 'false';
            }
        }
        return 'not_found';
        """
        result = self.driver.execute_script(js, label_text)
        return result == "true"

    # ================================================================
    # HISTORY POPUP
    # ================================================================

    def is_history_empty(self):
        """Check if the History popup shows 'No data available'."""
        log.info("Checking if History is empty")
        no_data = self.is_present(self.HISTORY_NO_DATA, timeout=5)
        no_data_text = self.is_present(self.HISTORY_NO_DATA_TEXT, timeout=5)
        is_empty = no_data or no_data_text
        log.info("History empty: " + str(is_empty))
        return is_empty

    def get_history_row_count(self):
        """Get the number of rows in the History table."""
        try:
            rows = self.find_elements(self.HISTORY_TABLE_ROWS)
            return len(rows)
        except Exception:
            return 0

    def get_history_data(self):
        """Get all data from the History table as list of dicts."""
        log.info("Reading History table data")
        records = []
        try:
            rows = self.find_elements(self.HISTORY_TABLE_ROWS)
            for row in rows:
                cells = row.find_elements("css selector", "td")
                record = {}
                col_classes = [
                    "created_date_time", "updated_date_time",
                    "source_uom", "target_uom", "conversion_factor", "status"
                ]
                for idx, col in enumerate(col_classes):
                    try:
                        record[col] = cells[idx].text.strip()
                    except Exception:
                        record[col] = ""
                records.append(record)
        except Exception as e:
            log.warning("Could not read history data: " + str(e))
        log.info("Found " + str(len(records)) + " history record(s)")
        return records

    def close_history_popup(self):
        """Close the History popup by clicking Cancel via JS."""
        log.info("Closing History popup")
        js = """
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
        throw new Error('Cancel button not found in any popup-footer');
        """
        self.driver.execute_script(js)
        time.sleep(1)

    # ================================================================
    # SWEETALERT 2 HANDLERS (same patterns as UOM page)
    # ================================================================

    def handle_success_alert(self):
        """Handle SweetAlert2 success notification (click confirm or wait for auto-dismiss)."""
        log.info("Handling success alert")
        try:
            if self.is_displayed(("css", ".swal2-container"), timeout=5):
                log.info("SweetAlert detected")
                try:
                    confirm_btn = self.driver.find_element("css selector", ".swal2-confirm")
                    self.driver.execute_script("arguments[0].click();", confirm_btn)
                    log.info("Clicked SweetAlert confirm via JS")
                except Exception:
                    log.info("SweetAlert confirm not found, waiting for auto-dismiss")
                time.sleep(3)
            else:
                log.info("No SweetAlert found (may have auto-dismissed)")
        except Exception as e:
            log.warning("SweetAlert handling: " + str(e))

    def handle_validation_warning(self):
        """Pattern A: 'Please correct the highlighted fields' — click OK."""
        log.info("Handling validation warning (Pattern A)")
        try:
            self.driver.find_element("css selector", ".swal2-popup.swal2-icon-warning")
            log.info("Validation warning SweetAlert detected")
            confirm_btn = self.driver.find_element("css selector", ".swal2-confirm")
            self.driver.execute_script("arguments[0].click();", confirm_btn)
            log.info("Clicked OK to dismiss validation warning")
            time.sleep(1)
        except Exception as e:
            log.warning("No validation warning found: " + str(e))

    def handle_validation_download(self):
        """Pattern B: 'Do you want to download?' — click Cancel."""
        log.info("Handling validation download (Pattern B)")
        try:
            self.driver.find_element("css selector", ".swal2-popup.swal2-icon-warning")
            log.info("Validation download SweetAlert detected")
            cancel_btn = self.driver.find_element("css selector", ".swal2-cancel")
            self.driver.execute_script("arguments[0].click();", cancel_btn)
            log.info("Clicked Cancel to dismiss validation download popup")
            time.sleep(1)
        except Exception as e:
            log.warning("No validation download popup found: " + str(e))

    def handle_error_toast(self):
        """Handle 'Failed to save record' error toast (auto-dismiss, no buttons)."""
        log.info("Handling error toast (waiting for auto-dismiss)")
        time.sleep(3)
        try:
            self.driver.find_element("css selector", ".swal2-popup.swal2-icon-error")
            log.info("Error toast detected, waiting for dismiss")
            time.sleep(3)
        except Exception:
            log.info("Error toast already dismissed")

    def is_validation_alert_present(self, timeout=5):
        """Check if any SweetAlert validation popup or error toast is visible."""
        try:
            elements = self.driver.find_elements(
                "css selector",
                ".swal2-popup.swal2-icon-warning, .swal2-popup.swal2-icon-error"
            )
            for el in elements:
                if el.is_displayed():
                    return True
            return False
        except Exception:
            return False

    def get_swal_title(self):
        """Get the title text from a SweetAlert popup."""
        try:
            el = self.driver.find_element("css selector", "h2.swal2-title")
            return el.text.strip()
        except Exception:
            return None

    def is_success_alert_present(self, timeout=5):
        """Check if a success SweetAlert is present."""
        try:
            elements = self.driver.find_elements("css selector", ".swal2-popup.swal2-icon-success")
            for el in elements:
                if el.is_displayed():
                    return True
            # Also check for text "successfully" in title
            title = self.get_swal_title()
            return title is not None and "successfully" in title.lower()
        except Exception:
            return False

    # ================================================================
    # ERROR DETECTION (same patterns as UOM page)
    # ================================================================

    def get_mat_error_text(self, field_locator):
        """Get the mat-error text below a form field (walks up parent chain)."""
        try:
            css_selector = field_locator[1] if field_locator[0] == "css" else ""
            if not css_selector:
                return ""
            js = """
            var input = document.querySelector(arguments[0]);
            if (!input) return JSON.stringify({found: false, reason: 'input not found'});
            var current = input;
            for (var steps = 0; steps < 20; steps++) {
                var errors = current.querySelectorAll('mat-error');
                if (errors.length > 0) {
                    var texts = [];
                    for (var i = 0; i < errors.length; i++) {
                        var t = errors[i].textContent.trim();
                        if (t) texts.push(t);
                    }
                    return JSON.stringify({found: true, errorText: texts.join(' | ')});
                }
                current = current.parentElement;
                if (!current || current === document.body) break;
            }
            return JSON.stringify({found: false});
            """
            result = self.driver.execute_script(js, css_selector)
            if not result:
                return ""
            import json
            data = json.loads(result)
            if data.get("found"):
                return data.get("errorText", "")
            return ""
        except Exception as e:
            log.warning("get_mat_error_text error: " + str(e))
            return ""

    def has_field_error(self, field_locator):
        """Check if a form field has error styling (red border / invalid class)."""
        try:
            css_selector = field_locator[1] if field_locator[0] == "css" else ""
            if not css_selector:
                return False
            js = """
            var input = document.querySelector(arguments[0]);
            if (!input) return JSON.stringify({found: false, reason: 'input not found'});
            var current = input;
            var invalidClasses = ['mat-mdc-form-field-invalid', 'mat-form-field-invalid', 'ng-invalid', 'cdk-text-field-invalid'];
            for (var steps = 0; steps < 20; steps++) {
                var classes = current.className || '';
                for (var i = 0; i < invalidClasses.length; i++) {
                    if (classes.indexOf(invalidClasses[i]) !== -1) {
                        return JSON.stringify({found: true, cls: invalidClasses[i]});
                    }
                }
                current = current.parentElement;
                if (!current || current === document.body) break;
            }
            return JSON.stringify({found: false});
            """
            result = self.driver.execute_script(js, css_selector)
            if not result:
                return False
            import json
            data = json.loads(result)
            return data.get("found", False)
        except Exception as e:
            log.warning("has_field_error error: " + str(e))
            return False

    # ================================================================
    # UTILITY - CDK OVERLAY CLEANUP
    # ================================================================

    def _force_close_panels(self):
        """Remove any lingering CDK overlay panels that block clicks."""
        try:
            overlays = self.driver.find_elements("css selector", ".cdk-overlay-backdrop")
            for overlay in overlays:
                self.driver.execute_script("arguments[0].remove();", overlay)
            panels = self.driver.find_elements("css selector", ".cdk-overlay-pane")
            for panel in panels:
                self.driver.execute_script("arguments[0].remove();", panel)
        except Exception:
            pass

    # ================================================================
    # MASTER CLEANUP
    # ================================================================

    def cleanup(self):
        """Dismiss alerts, close forms, remove overlays — return to clean table."""
        self.handle_error_toast()
        try:
            self.driver.find_element("css selector", ".swal2-confirm")
            self.driver.execute_script(
                "document.querySelector('.swal2-confirm').click();"
            )
            time.sleep(0.5)
        except Exception:
            pass
        self.cancel_form_safely()
        self._force_close_panels()

    def cancel_form_safely(self):
        """Try to close any open form via Cancel or force close."""
        try:
            self.click_with_retry(self.CANCEL_BUTTON)
            time.sleep(1)
        except Exception:
            self.force_close_form_popup()
            time.sleep(0.5)