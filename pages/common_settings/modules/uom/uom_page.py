"""
uom_page.py
------------
Page Object for RhythmERP -> Common Settings -> UOM.
Handles Create, View, Edit, and History operations on the UOM page.
"""

import time
from common.base_page import BasePage
from common.logger import log
from config import EXPLICIT_WAIT


class UOMPage(BasePage):
    """
    UOMPage - Page Object for Common Settings > UOM.

    Covers:
    - Navigate to UOM page
    - Create new UOM
    - Search UOM in table
    - View UOM details (read-only)
    - Edit UOM (update description, toggle status)
    - View UOM History (check empty / check data)
    """

    # ================================================================
    # SIDEBAR NAVIGATION
    # ================================================================
    SIDEBAR_COMMON_SETTINGS = ("xpath", "//span[contains(text(),'Common Settings')]")
    SIDEBAR_UOM = ("xpath", "//span[contains(text(),'UOM')]")

    # ================================================================
    # MAIN TABLE
    # ================================================================
    ADD_BUTTON = ("css", "button.erp-add-btn")
    SEARCH_BUTTON = ("css", "button.search-btn")
    SEARCH_INPUT = ("css", "input#erpSearchInput")
    TABLE_UOM_CODES = ("css", "table#excel-table td.cdk-column-uom_code")
    TABLE_ROWS = ("css", "table#excel-table tbody tr")

    # Action buttons in a specific row (parametrized via XPath)
    VIEW_BUTTON = ("xpath", "//td[contains(text(),'{uom_code}')]/ancestor::tr//td.cdk-column-view//button")
    EDIT_BUTTON = ("xpath", "//td[contains(text(),'{uom_code}')]/ancestor::tr//td.cdk-column-edit//button")
    HISTORY_BUTTON = ("xpath", "//td[contains(text(),'{uom_code}')]/ancestor::tr//td.cdk-column-archive//button")

    # ================================================================
    # CREATE / EDIT FORM (shared form fields)
    # ================================================================
    UOM_CODE_INPUT = ("css", "input[name='UOM Code']")
    UOM_DESCRIPTION_INPUT = ("css", "input[name='UOM Description']")

    SUBMIT_BUTTON = ("xpath", "//div[@class='popup-footer']//button[contains(.,'Submit')]")
    UPDATE_BUTTON = ("xpath", "//div[@class='popup-footer']//button[contains(.,'Update')]")
    CANCEL_BUTTON = ("xpath", "//div[@class='popup-footer']//button[contains(.,'Cancel')]")

    # ================================================================
    # VIEW POPUP - read-only indicators
    # ================================================================
    VIEW_POPUP_HEADER = ("css", ".popup-header h3")
    VIEW_UOM_CODE_FIELD = ("css", ".popup-body input[name='UOM Code']")

    # ================================================================
    # HISTORY POPUP
    # ================================================================
    HISTORY_HEADER = ("css", "app-dynamic-history .tbl-title h2")
    HISTORY_NO_DATA = ("css", "app-dynamic-history .no-data, app-dynamic-history img[alt='No Data Available']")
    HISTORY_NO_DATA_TEXT = ("xpath", "//app-dynamic-history//*[contains(text(),'No data available')]")
    HISTORY_SEARCH_INPUT = ("css", "app-dynamic-history input#erpSearchInput")
    HISTORY_TABLE_ROWS = ("css", "app-dynamic-history table#excel-table tbody tr")
    HISTORY_CANCEL_BUTTON = ("xpath", "//app-dynamic-history//div[@class='popup-footer']//button[contains(.,'Cancel')]")

    # History table column cells
    HISTORY_COL_CREATED_TIME = ("css", "app-dynamic-history td.cdk-column-created_date_time")
    HISTORY_COL_UPDATED_TIME = ("css", "app-dynamic-history td.cdk-column-updated_date_time")
    HISTORY_COL_UOM_CODE = ("css", "app-dynamic-history td.cdk-column-uom_code")
    HISTORY_COL_DESCRIPTION = ("css", "app-dynamic-history td.cdk-column-uom_description")
    HISTORY_COL_STATUS = ("css", "app-dynamic-history td.cdk-column-status")

    # ================================================================
    # UOM PAGE URL
    # ================================================================
    UOM_PAGE_URL = "https://rhythmerp.algorhythms.in/#/dynamic-screens/UOM"

    # ================================================================
    # NAVIGATION
    # ================================================================

    def navigate_to_page(self):
        """Navigate to UOM page via direct URL (fast and reliable)."""
        log.info("Navigating to UOM page")
        self.driver.get(self.UOM_PAGE_URL)
        self._wait_for_page_ready()
        self._force_close_panels()
        log.info("Arrived at UOM page")

    def _wait_for_page_ready(self):
        """Wait up to 20s for the UOM page search button or table to appear."""
        waited = 0
        while waited < 20:
            try:
                self.driver.find_element("css selector", "button.search-btn")
                log.info("Page ready (search button found) after " + str(waited) + "s")
                return
            except Exception:
                pass
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
    # CREATE UOM
    # ================================================================

    def open_add_form(self):
        """Click the Add button to open the Create UOM form popup."""
        log.info("Opening Add UOM form")
        self._force_close_panels()
        self.click_with_retry(self.ADD_BUTTON)
        time.sleep(1)

    def fill_uom_form(self, data):
        """
        Fill the UOM form with given data.
        Args:
            data: dict with keys 'uom_code' and 'uom_description'
        """
        log.info(f"Filling UOM form: {data}")
        self.type_text(self.UOM_CODE_INPUT, data["uom_code"])
        self.type_text(self.UOM_DESCRIPTION_INPUT, data["uom_description"])
        time.sleep(0.5)

    def submit(self):
        """Click Submit on the Create form."""
        log.info("Clicking Submit")
        self.click_with_retry(self.SUBMIT_BUTTON)
        time.sleep(1)

    # ================================================================
    # SEARCH
    # ================================================================

    def search_uom(self, code):
    
        log.info(f"Searching for UOM: {code}")

        # Step 1: Check if search input is already visible; if not, click button to open it
        try:
            search_input = self.driver.find_element("css selector", "input#erpSearchInput")
            rect = self.driver.execute_script(
                "var r = arguments[0].getBoundingClientRect(); "
                "return r.width > 0 && r.height > 0;", search_input
            )
            if not rect:
                raise Exception("Not visible")
            log.info("Search input already visible, skipping button click")
        except Exception:
            log.info("Search input not visible, clicking search button to open")
            self.click_with_retry(self.SEARCH_BUTTON)
            time.sleep(0.5)
            search_input = self.find_visible_element(self.SEARCH_INPUT)

        # Step 2: Clear existing value completely
        self.driver.execute_script("arguments[0].value = '';", search_input)
        self.driver.execute_script(
            "arguments[0].dispatchEvent(new Event('input', { bubbles: true }));",
            search_input,
        )
        time.sleep(0.3)

        # Step 3: Set new value and fire Angular change events
        self.driver.execute_script(
            "arguments[0].value = arguments[1];", search_input, code
        )
        search_input.click()
        for event in ["input", "keyup", "change"]:
            self.driver.execute_script(
                f"arguments[0].dispatchEvent(new Event('{event}', {{ bubbles: true }}));",
                search_input,
            )
        time.sleep(0.3)

        # Step 4: Click the search button to actually submit/filter the table
        self.click_with_retry(self.SEARCH_BUTTON)
        time.sleep(2)

        log.info(f"Search triggered for: {code}")


    def verify_uom_exists(self, code):
        """
        Verify UOM code appears in the main table after search.
        Polls up to 15s to handle slow Angular re-renders.
        Also logs what IS in the table to help debug misses.
        """
        log.info(f"Verifying UOM '{code}' exists in table")
        end_time = time.monotonic() + 15
        last_seen = []
        while time.monotonic() < end_time:
            try:
                rows = self.find_elements(self.TABLE_ROWS)
                last_seen = []
                for row in rows:
                    cells = row.find_elements("css selector", "td")
                    row_text = " | ".join(c.text.strip() for c in cells if c.text.strip())
                    last_seen.append(row_text)
                    for cell in cells:
                        if code in cell.text.strip():
                            log.info(f"UOM '{code}' found in table")
                            return True
            except Exception:
                pass
            time.sleep(0.5)
        log.error(f"UOM '{code}' NOT found. Table contents were: {last_seen}")
        raise AssertionError(f"UOM '{code}' NOT found in table after search. Last table rows: {last_seen}")

    def is_uom_in_table(self, code):
        """
        Check if a UOM code exists in the main table (first page only).
        Returns True if found, False if not. No logging or exceptions.
        """
        try:
            rows = self.find_elements(self.TABLE_ROWS)
            for row in rows:
                cells = row.find_elements("css selector", "td")
                for cell in cells:
                    if code in cell.text.strip():
                        return True
        except Exception:
            pass
        return False
    

    def clear_search(self):
        """Clear the search input and refresh to get clean state."""
        log.info("Clearing search - navigating fresh")
        self.navigate_to_page()
        time.sleep(1)

    # ================================================================
    # VIEW UOM
    # ================================================================

    def click_view_button(self, uom_code):
        """Click the View (eye) button for a specific UOM row."""
        self._click_action_button(uom_code, "cdk-column-view")
        time.sleep(1.5)

    def verify_view_popup_read_only(self):
        """
        Verify the View popup has fields disabled (read-only).
        Checks:
        1. UOM Code input has 'disabled' attribute
        2. UOM Description input has 'disabled' attribute
        3. No Submit/Update button is present
        4. Cancel button IS present
        """
        log.info("Verifying View popup is read-only")

        code_disabled = self.get_attribute(self.UOM_CODE_INPUT, "disabled")
        assert code_disabled == "true", "UOM Code field should be disabled in View mode"
        log.info("  [PASS] UOM Code field is disabled")

        desc_disabled = self.get_attribute(self.UOM_DESCRIPTION_INPUT, "disabled")
        assert desc_disabled == "true", "UOM Description field should be disabled in View mode"
        log.info("  [PASS] UOM Description field is disabled")

        submit_present = self.is_present(self.SUBMIT_BUTTON, timeout=2)
        update_present = self.is_present(self.UPDATE_BUTTON, timeout=2)
        assert not submit_present, "Submit button should NOT be present in View mode"
        assert not update_present, "Update button should NOT be present in View mode"
        log.info("  [PASS] No Submit/Update button in View mode")

        assert self.is_present(self.CANCEL_BUTTON, timeout=3), "Cancel button should be present in View mode"
        log.info("  [PASS] Cancel button is present")

        log.info("View popup verified as read-only")

    def get_view_field_value(self, locator):
        """Get the value from a field in the View popup."""
        return self.get_attribute(locator, "value")

    # ================================================================
    # EDIT UOM
    # ================================================================

    def click_edit_button(self, uom_code):
        """Click the Edit button for a specific UOM row."""
        self._click_action_button(uom_code, "cdk-column-edit")
        time.sleep(1.5)

    def verify_edit_popup_editable(self):
        """
        Verify the Edit popup has fields enabled.
        Checks:
        1. Update button IS present
        2. Cancel button IS present
        """
        log.info("Verifying Edit popup is editable")

        assert self.is_present(self.UPDATE_BUTTON, timeout=3), "Update button should be present in Edit mode"
        log.info("  [PASS] Update button is present")

        assert self.is_present(self.CANCEL_BUTTON, timeout=3), "Cancel button should be present in Edit mode"
        log.info("  [PASS] Cancel button is present")

        log.info("Edit popup verified as editable")

    def update_uom_description(self, new_description):
        """Clear and type a new description in the Edit form."""
        log.info("Updating description to: " + str(new_description))
        self.type_text(self.UOM_DESCRIPTION_INPUT, new_description)
        time.sleep(0.5)

    def toggle_status(self):
        """Click the status toggle (Active <-> Inactive) via .slider."""
        log.info("Toggling status")
        js = """
        var toggle = document.querySelector('app-slide-toggle-v2');
        if (!toggle) { throw new Error('app-slide-toggle-v2 not found'); }
        var slider = toggle.querySelector('.slider');
        if (slider) {
            slider.scrollIntoView({block:'center'});
            slider.click();
            return 'clicked .slider';
        }
        var wrapper = toggle.querySelector('.switch-wrapper');
        if (wrapper) {
            wrapper.scrollIntoView({block:'center'});
            wrapper.click();
            return 'clicked .switch-wrapper';
        }
        toggle.scrollIntoView({block:'center'});
        toggle.click();
        return 'clicked host';
        """
        result = self.driver.execute_script(js)
        log.info("Toggle clicked: " + str(result))
        time.sleep(0.5)

    def get_toggle_status(self):
        """Get current toggle state - Active or Inactive."""
        js = """
        var toggle = document.querySelector('app-slide-toggle-v2');
        if (!toggle) { return 'unknown'; }
        var onLabel = toggle.querySelector('.state-label.on');
        return (onLabel && onLabel.classList.contains('active')) ? 'Active' : 'Inactive';
        """
        status = self.driver.execute_script(js)
        log.info("Toggle status: " + str(status))
        return status

    def click_update(self):
        """Click the Update button on the Edit form."""
        log.info("Clicking Update")
        self.click_with_retry(self.UPDATE_BUTTON)
        time.sleep(1)

    # ================================================================
    # HISTORY
    # ================================================================

    def click_history_button(self, uom_code):
        """Click the History (clock) button for a specific UOM row."""
        self._click_action_button(uom_code, "cdk-column-archive")
        time.sleep(2)

    def is_history_empty(self):
        """
        Check if the History popup shows 'No data available'.
        Returns True if empty, False if data exists.
        """
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
        """
        Get all data from the History table.
        Returns list of dicts with keys: created_time, updated_time,
        uom_code, description, status.
        """
        log.info("Reading History table data")
        history_records = []
        try:
            rows = self.find_elements(self.HISTORY_TABLE_ROWS)
            for row in rows:
                record = {}
                try:
                    record["created_time"] = row.find_element(
                        "css selector", "td.cdk-column-created_date_time"
                    ).text.strip()
                except Exception:
                    record["created_time"] = ""
                try:
                    record["updated_time"] = row.find_element(
                        "css selector", "td.cdk-column-updated_date_time"
                    ).text.strip()
                except Exception:
                    record["updated_time"] = ""
                try:
                    record["uom_code"] = row.find_element(
                        "css selector", "td.cdk-column-uom_code"
                    ).text.strip()
                except Exception:
                    record["uom_code"] = ""
                try:
                    record["description"] = row.find_element(
                        "css selector", "td.cdk-column-uom_description"
                    ).text.strip()
                except Exception:
                    record["description"] = ""
                try:
                    record["status"] = row.find_element(
                        "css selector", "td.cdk-column-status"
                    ).text.strip()
                except Exception:
                    record["status"] = ""
                history_records.append(record)
        except Exception as e:
            log.warning("Could not read history data: " + str(e))
        log.info("Found " + str(len(history_records)) + " history record(s)")
        return history_records

    def close_history_popup(self):
        """Close the History popup by clicking Cancel using pure JS."""
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
    # POPUP CLOSE (shared)
    # ================================================================

    def close_popup(self):
        """Close any popup by clicking Cancel button."""
        log.info("Closing popup")
        try:
            self.click_with_retry(self.CANCEL_BUTTON)
            time.sleep(1)
        except Exception:
            log.warning("Could not click Cancel, trying to force close panels")
            self._force_close_panels()

    # ================================================================
    # SUCCESS ALERT (SweetAlert2)
    # ================================================================

    def handle_success_alert(self):
        """
        Handle SweetAlert2 success notification.
        Waits briefly for SweetAlert, tries to dismiss it quickly.
        If confirm button not found, waits for auto-dismiss.
        """
        log.info("Handling success alert")
        try:
            swal = ("css", ".swal2-container")
            if self.is_displayed(swal, timeout=5):
                log.info("SweetAlert success detected")
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

    # ================================================================
    # UTILITY - CDK OVERLAY CLEANUP
    # ================================================================

    def _force_close_panels(self):
        """Remove any lingering CDK overlay panels that block clicks."""
        try:
            overlays = self.driver.find_elements(
                "css selector", ".cdk-overlay-backdrop"
            )
            for overlay in overlays:
                self.driver.execute_script("arguments[0].remove();", overlay)
            panels = self.driver.find_elements(
                "css selector", ".cdk-overlay-pane"
            )
            for panel in panels:
                self.driver.execute_script("arguments[0].remove();", panel)
        except Exception:
            pass

    # ================================================================
    # UTILITY - ACTION BUTTON CLICKER (pure JS, no XPath)
    # ================================================================

    def _click_action_button(self, uom_code, column_class):
        """
        Click an action button (View/Edit/History) for a specific UOM row.
        Uses pure JS to find the row by UOM code and click the button.
        This avoids XPath text() issues with Angular comment nodes.
        """
        log.info("Clicking " + column_class + " button for UOM: " + uom_code)
        js = """
        var table = document.querySelector('table#excel-table');
        if (!table) { throw new Error('Table not found'); }
        var rows = table.querySelectorAll('tbody tr');
        for (var i = 0; i < rows.length; i++) {
            var cells = rows[i].querySelectorAll('td');
            for (var j = 0; j < cells.length; j++) {
                if (cells[j].textContent.trim().indexOf(arguments[0]) !== -1) {
                    var btn = rows[i].querySelector('td.' + arguments[1] + ' button');
                    if (btn) {
                        btn.scrollIntoView({block:'center'});
                        btn.click();
                        return 'clicked';
                    }
                    throw new Error('Button column ' + arguments[1] + ' not found in row');
                }
            }
        }
        throw new Error('UOM code ' + arguments[0] + ' not found in table');
        """
        result = self.driver.execute_script(js, uom_code, column_class)
        log.info("Successfully clicked " + column_class + " button for UOM: " + uom_code)
        return result

    # ================================================================
    # VALIDATION ALERT HANDLERS
    # ================================================================

    def handle_validation_warning(self):
        """
        Pattern A: 'Please correct the highlighted fields'
        SweetAlert with only an OK button (.swal2-confirm).
        Clicks OK to dismiss.
        """
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
        """
        Pattern B: 'Fields validation failed. Do you want to download?'
        SweetAlert with Cancel (.swal2-cancel) + Download Errors (.swal2-confirm).
        Clicks Cancel to dismiss.
        """
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
        """
        Handle 'Failed to save record' error toast (swal2-icon-error).
        This is a toast notification with no buttons - just wait for auto-dismiss.
        """
        log.info("Handling error toast (waiting for auto-dismiss)")
        time.sleep(3)
        try:
            self.driver.find_element("css selector", ".swal2-popup.swal2-icon-error")
            log.info("Error toast detected, waiting for dismiss")
            time.sleep(3)
        except Exception:
            log.info("Error toast already dismissed")

    def is_validation_alert_present(self, timeout=5):
        """
        Check if any SweetAlert validation popup or error toast is visible.
        Polls up to `timeout` seconds (checks every 0.5s).
        Returns True if swal2-icon-warning (Pattern A/B) or
        swal2-icon-error ('Failed to save record' toast) is present.
        """
        end_time = time.monotonic() + timeout
        while time.monotonic() < end_time:
            try:
                elements = self.driver.find_elements(
                    "css selector",
                    ".swal2-popup.swal2-icon-warning, .swal2-popup.swal2-icon-error"
                )
                for el in elements:
                    if el.is_displayed():
                        return True
            except Exception:
                pass
            time.sleep(0.5)
        return False

    def dismiss_any_validation_alert(self):
        """
        Dismiss any SweetAlert validation popup (Pattern A or Pattern B).
        Pattern A: clicks OK (.swal2-confirm).
        Pattern B: clicks Cancel (.swal2-cancel).
        """
        try:
            self.driver.find_element("css selector", ".swal2-popup.swal2-icon-warning")
            log.info("Validation SweetAlert detected, attempting to dismiss")
            try:
                cancel_btn = self.driver.find_element("css selector", ".swal2-cancel")
                self.driver.execute_script("arguments[0].click();", cancel_btn)
                log.info("Dismissed via Cancel button (Pattern B)")
            except Exception:
                confirm_btn = self.driver.find_element("css selector", ".swal2-confirm")
                self.driver.execute_script("arguments[0].click();", confirm_btn)
                log.info("Dismissed via OK button (Pattern A)")
            time.sleep(1)
        except Exception as e:
            log.warning("No validation alert to dismiss: " + str(e))

    def get_mat_error_text(self, field_locator):
        """
        Get the mat-error text below a form field.
        Uses pure JS (no Selenium find_element) to avoid locator issues.
        Walks up parentElement chain to find mat-error at any ancestor level.
        Returns all error texts joined by ' | ', or empty string if none.
        """
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
            var chain = [];
            current = document.querySelector(arguments[0]);
            for (var d = 0; d < 15; d++) {
                if (!current || current === document.body) break;
                chain.push(current.tagName + '.' + (current.className || '').substring(0, 40).split(' ')[0]);
                current = current.parentElement;
            }
            return JSON.stringify({found: false, chain: chain.join(' > ')});
            """
            result = self.driver.execute_script(js, css_selector)
            log.info("get_mat_error_text raw: " + str(result))
            if not result:
                return ""
            import json
            data = json.loads(result)
            if data.get("found"):
                return data.get("errorText", "")
            else:
                log.warning("mat-error not found. Chain: " + data.get("chain", data.get("reason", "unknown")))
                return ""
        except Exception as e:
            log.warning("get_mat_error_text error: " + str(e))
            return ""

    def has_field_error(self, field_locator):
        """
        Check if a form field has error styling (red border / invalid state).
        Uses pure JS to walk up parentElement chain looking for invalid classes.
        """
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
                        return JSON.stringify({found: true, tag: current.tagName, cls: invalidClasses[i]});
                    }
                }
                current = current.parentElement;
                if (!current || current === document.body) break;
            }
            return JSON.stringify({found: false});
            """
            result = self.driver.execute_script(js, css_selector)
            log.info("has_field_error raw: " + str(result))
            if not result:
                return False
            import json
            data = json.loads(result)
            return data.get("found", False)
        except Exception as e:
            log.warning("has_field_error error: " + str(e))
            return False

    def is_add_form_open(self):
        """Check if the Add/Create UOM popup is currently open."""
        try:
            self.driver.find_element("css selector", "input[name='UOM Code']")
            return True
        except Exception:
            return False

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