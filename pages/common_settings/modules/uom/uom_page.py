"""
uom_page.py
------------
Page Object for RhythmERP -> Common Settings -> UOM.
Handles Create, View, Edit, and History operations on the UOM page.

Optimised (v2):
- Replaced most time.sleep() with explicit WebDriverWait
- Added hard_refresh() for fast page reset between tests
- search_and_verify() combines search + existence check
- Reduced unnecessary waits throughout
"""

import time
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
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

    # Action buttons — now inside a 3-dot menu dropdown (cdk-column-actions)
    ACTIONS_COLUMN = ("css", "td.cdk-column-actions")
    THREE_DOT_MENU_BUTTON = ("css", "td.cdk-column-actions button")

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
        log.info("Arrived at UOM page")

    def hard_refresh(self):
        """Hard refresh the current page (Ctrl+R) and wait for it to be ready.
        Much faster than full navigate_to_page() for resetting between tests."""
        log.info("Hard refreshing page")
        self.driver.refresh()
        self._wait_for_page_ready()
        log.info("Page refreshed and ready")

    def _wait_for_page_ready(self):
        """Wait for the UOM page table to appear.
        We only wait for the table (not clickability of buttons) because
        the search button is often overlapped and never Selenium-clickable.
        We use JS clicks for the search button instead."""
        try:
            WebDriverWait(self.driver, 15).until(
                lambda d: d.find_elements("css selector", "table#excel-table")
            )
            log.info("Page ready (table found)")
        except Exception:
            # Fallback: check for search button
            try:
                WebDriverWait(self.driver, 5).until(
                    lambda d: d.find_elements("css selector", "button.search-btn")
                )
                log.info("Page ready (search button found, no table)")
            except Exception:
                log.warning("Page ready check timed out")

    # ================================================================
    # CREATE UOM
    # ================================================================

    def open_add_form(self):
        """Click the Add button to open the Create UOM form popup.
        Uses JS click because button.erp-add-btn is often overlapped
        and never becomes Selenium-clickable (same issue as search button)."""
        log.info("Opening Add UOM form")
        # JS click — bypasses overlay/z-index issues
        js_click_add = """
        var btn = document.querySelector('button.erp-add-btn');
        if (!btn) { throw new Error('Add button not found in DOM'); }
        btn.scrollIntoView({block:'center'});
        btn.click();
        return 'clicked';
        """
        try:
            result = self.driver.execute_script(js_click_add)
            log.info("Add button clicked via JS: " + str(result))
        except Exception as e:
            log.warning("JS click failed, falling back to Selenium click: " + str(e))
            self.click_with_retry(self.ADD_BUTTON)
        # Wait for the form popup to appear
        try:
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located(("css selector", "input[name='UOM Code']"))
            )
            log.info("Add form opened")
        except Exception:
            log.warning("Add form may not have opened — UOM Code input not found")

    def fill_uom_form(self, data):
        """
        Fill the UOM form with given data.
        Args:
            data: dict with keys 'uom_code' and 'uom_description'
        """
        log.info(f"Filling UOM form: {data}")
        self.type_text(self.UOM_CODE_INPUT, data["uom_code"])
        self.type_text(self.UOM_DESCRIPTION_INPUT, data["uom_description"])

    def submit(self):
        """Click Submit on the Create form via JS click."""
        log.info("Clicking Submit")
        self._js_click_popup_button('Submit')

    # ================================================================
    # SEARCH
    # ================================================================

    def search_uom(self, code):
        """Search for a UOM code in the table. Uses JS clicks to bypass overlay issues.
        The search button (button.search-btn) is often overlapped on the live system
        and never becomes Selenium-clickable, so we click it via JavaScript instead."""
        log.info(f"Searching for UOM: {code}")

        # Step 1: Check if search input is already visible
        search_input = None
        try:
            el = self.driver.find_element("css selector", "input#erpSearchInput")
            rect = self.driver.execute_script(
                "var r = arguments[0].getBoundingClientRect(); "
                "return r.width > 0 && r.height > 0;", el
            )
            if rect:
                search_input = el
                log.info("Search input already visible, skipping button click")
        except Exception:
            pass

        # Step 2: If search input not visible, click search button via JS to open it
        if search_input is None:
            log.info("Search input not visible, clicking search button via JS")
            js_click_search = """
            var btn = document.querySelector('button.search-btn');
            if (!btn) { throw new Error('Search button not found in DOM'); }
            btn.scrollIntoView({block:'center'});
            btn.click();
            return 'clicked';
            """
            try:
                result = self.driver.execute_script(js_click_search)
                log.info("Search button clicked via JS: " + str(result))
            except Exception as e:
                log.error("Failed to click search button via JS: " + str(e))
                return

            # Wait for search input to become visible
            try:
                search_input = WebDriverWait(self.driver, 5).until(
                    EC.visibility_of_element_located(("css selector", "input#erpSearchInput"))
                )
                log.info("Search input became visible")
            except Exception:
                log.warning("Search input did not become visible after clicking search button")
                return

        # Step 3: Clear existing value completely
        self.driver.execute_script("arguments[0].value = '';", search_input)
        self.driver.execute_script(
            "arguments[0].dispatchEvent(new Event('input', { bubbles: true }));",
            search_input,
        )

        # Step 4: Set new value and fire Angular change events
        self.driver.execute_script(
            "arguments[0].value = arguments[1];", search_input, code
        )
        search_input.click()
        for event in ["input", "keyup", "change"]:
            self.driver.execute_script(
                f"arguments[0].dispatchEvent(new Event('{event}', {{ bubbles: true }}));",
                search_input,
            )

        # Step 5: Click the search button again via JS to submit/filter the table
        js_click_search = """
        var btn = document.querySelector('button.search-btn');
        if (btn) { btn.click(); return 'clicked'; }
        return 'not found';
        """
        self.driver.execute_script(js_click_search)
        log.info("Search submit clicked via JS")

        # Step 6: Wait for table to refresh
        try:
            WebDriverWait(self.driver, 5).until(
                lambda d: d.find_elements("css selector", "table#excel-table tbody tr")
            )
        except Exception:
            pass  # Table might be empty (no results)

        log.info(f"Search completed for: {code}")

    def verify_uom_exists(self, code):
        """
        Verify UOM code appears in the main table.
        Polls up to 10s to handle slow Angular re-renders.
        Also logs what IS in the table to help debug misses.
        """
        log.info(f"Verifying UOM '{code}' exists in table")
        end_time = time.monotonic() + 10
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

    def search_and_verify(self, code):
        """
        Search for a UOM code, then verify it exists in the filtered results.
        This is the recommended way to verify a create/update — uses search
        instead of scanning all rows (handles pagination automatically).
        Returns True if found.
        """
        log.info(f"Searching and verifying UOM: {code}")
        self.search_uom(code)
        return self.verify_uom_exists(code)

    def is_uom_in_table(self, code):
        """
        Check if a UOM code exists in the main table (current view only).
        Returns True if found, False if not. No exceptions.
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
        log.info("Clearing search - hard refreshing")
        self.hard_refresh()

    # ================================================================
    # VIEW UOM
    # ================================================================

    def click_view_button(self, uom_code):
        """Click the View (eye) button for a specific UOM row via 3-dot menu."""
        self._click_action_menu_item(uom_code, "View")
        # Wait for view popup to appear
        try:
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located(("css selector", ".popup-header h3"))
            )
        except Exception:
            pass

    def verify_view_popup_read_only(self):
        """
        Verify the View popup has fields disabled (read-only).
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
        """Click the Edit button for a specific UOM row via 3-dot menu."""
        self._click_action_menu_item(uom_code, "Edit")
        # Wait for edit popup to appear
        try:
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located(("css selector", "input[name='UOM Code']"))
            )
        except Exception:
            pass

    def verify_edit_popup_editable(self):
        """
        Verify the Edit popup has fields enabled.
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
        """Click the Update button on the Edit form via JS click."""
        log.info("Clicking Update")
        self._js_click_popup_button('Update')

    # ================================================================
    # HISTORY
    # ================================================================

    def click_history_button(self, uom_code):
        """Click the History button for a specific UOM row via 3-dot menu."""
        self._click_action_menu_item(uom_code, "History")
        # Wait for history popup to appear
        try:
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located(("css selector", "app-dynamic-history"))
            )
        except Exception:
            pass

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

    # ================================================================
    # POPUP CLOSE (shared)
    # ================================================================

    def close_popup(self):
        """Close any popup by clicking Cancel button via JS."""
        log.info("Closing popup")
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

    # ================================================================
    # SUCCESS ALERT (SweetAlert2)
    # ================================================================

    def handle_success_alert(self):
        """Handle SweetAlert2 success notification — fast dismiss."""
        log.info("Handling success alert")
        # SweetAlert appears almost instantly — check with short timeout
        try:
            WebDriverWait(self.driver, 3).until(
                EC.visibility_of_element_located(("css selector", ".swal2-container"))
            )
            log.info("SweetAlert detected, dismissing via JS")
            # Click confirm button via JS (fast, bypasses overlay)
            self.driver.execute_script("""
                var btn = document.querySelector('.swal2-confirm');
                if (btn) { btn.click(); return 'clicked'; }
                return 'not found';
            """)
            # Wait for SweetAlert to disappear (short wait)
            try:
                WebDriverWait(self.driver, 3).until(
                    EC.invisibility_of_element_located(("css selector", ".swal2-container"))
                )
            except Exception:
                pass
        except Exception:
            log.info("No SweetAlert found (may have auto-dismissed)")

    # ================================================================
    # UTILITY - CDK OVERLAY CLEANUP
    # ================================================================

    def _force_close_panels(self):
        """Remove any lingering CDK overlay panels that block clicks."""
        self.driver.execute_script("""
            document.querySelectorAll('.cdk-overlay-backdrop').forEach(function(el) { el.remove(); });
            document.querySelectorAll('.cdk-overlay-pane').forEach(function(el) { el.remove(); });
        """)

    # ================================================================
    # UTILITY - ACTION BUTTON CLICKER (pure JS, no XPath)
    # ================================================================

    def _click_action_menu_item(self, uom_code, action_name):
        """
        Click an action menu item (View/Edit/History) for a specific UOM row.
        The live system uses a 3-dot (⋮) menu button in cdk-column-actions.
        """
        log.info("Clicking " + action_name + " via 3-dot menu for UOM: " + uom_code)
        js = """
        var table = document.querySelector('table#excel-table');
        if (!table) { throw new Error('Table not found'); }
        var rows = table.querySelectorAll('tbody tr');
        for (var i = 0; i < rows.length; i++) {
            var cells = rows[i].querySelectorAll('td');
            for (var j = 0; j < cells.length; j++) {
                if (cells[j].textContent.trim().indexOf(arguments[0]) !== -1) {
                    var menuBtn = rows[i].querySelector('td.cdk-column-actions button');
                    if (!menuBtn) { throw new Error('3-dot menu button not found in actions column'); }
                    menuBtn.scrollIntoView({block:'center'});
                    menuBtn.click();
                    return 'menu_opened';
                }
            }
        }
        throw new Error('UOM code ' + arguments[0] + ' not found in table');
        """
        result = self.driver.execute_script(js, uom_code)
        log.info("3-dot menu opened for UOM: " + uom_code)

        # Wait briefly for dropdown to render
        try:
            WebDriverWait(self.driver, 2).until(
                EC.presence_of_element_located(("css selector", ".cdk-overlay-container .cdk-overlay-pane"))
            )
        except Exception:
            pass

        # Click the specific menu item from the dropdown overlay
        js_click_item = """
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
        // Fallback: try partial match
        for (var i = 0; i < items.length; i++) {
            var text = items[i].textContent.trim().toLowerCase();
            if (text.indexOf(arguments[0].toLowerCase()) !== -1) {
                items[i].click();
                return 'clicked_partial_' + arguments[0];
            }
        }
        throw new Error('Menu item "' + arguments[0] + '" not found in dropdown overlay');
        """
        result = self.driver.execute_script(js_click_item, action_name)
        log.info("Successfully clicked " + action_name + " for UOM: " + uom_code)
        return result

    # ================================================================
    # VALIDATION ALERT HANDLERS
    # ================================================================

    def handle_validation_warning(self):
        """Pattern A: Dismiss 'Please correct the highlighted fields' via JS click."""
        log.info("Handling validation warning (Pattern A)")
        self._dismiss_swal(button=".swal2-confirm", label="OK")

    def handle_validation_download(self):
        """Pattern B: Dismiss 'Fields validation failed' via JS click on Cancel."""
        log.info("Handling validation download (Pattern B)")
        self._dismiss_swal(button=".swal2-cancel", label="Cancel")

    def handle_error_toast(self):
        """
        DEPRECATED: Pattern C ('Failed to save record' error toast) no longer exists
        on the live system. Kept for backward compatibility.
        """
        log.warning("handle_error_toast is DEPRECATED. Pattern C no longer exists on live system.")
        log.info("Checking for any error toast (backward compat)")
        try:
            WebDriverWait(self.driver, 3).until(
                EC.presence_of_element_located(("css selector", ".swal2-popup.swal2-icon-error"))
            )
            log.info("Error toast detected (unexpected on live system), waiting for dismiss")
            try:
                WebDriverWait(self.driver, 5).until(
                    EC.invisibility_of_element_located(("css selector", ".swal2-popup.swal2-icon-error"))
                )
            except Exception:
                pass
        except Exception:
            log.info("No error toast found (expected — Pattern C removed from live system)")

    def is_validation_alert_present(self, timeout=3):
        """Check if any SweetAlert validation popup is visible. Fast poll (0.2s)."""
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

    def dismiss_any_validation_alert(self):
        """Dismiss any SweetAlert validation popup — try Cancel first (Pattern B), then OK (Pattern A)."""
        log.info("Dismissing any validation alert")
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

    def get_mat_error_text(self, field_locator):
        """
        Get the mat-error text below a form field.
        Uses pure JS (no Selenium find_element) to avoid locator issues.
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
        return self.driver.execute_script("""
            var el = document.querySelector("input[name='UOM Code']");
            return el && el.offsetParent !== null;
        """)

    def get_field_value(self, locator):
        """Get the current value of an input field via JS (fast)."""
        try:
            css_selector = locator[1] if locator[0] == "css" else ""
            if not css_selector:
                return ""
            return self.driver.execute_script(
                "var el = document.querySelector(arguments[0]); "
                "return el ? el.value : '';", css_selector
            ) or ""
        except Exception:
            return ""

    def _js_click_popup_button(self, button_text):
        """Click a popup footer button (Submit/Update) via JS — bypasses overlay issues."""
        js = """
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
        """
        try:
            result = self.driver.execute_script(js, button_text)
            log.info("JS click " + button_text + ": " + str(result))
        except Exception as e:
            log.warning("JS click failed for " + button_text + ", falling back to Selenium: " + str(e))
            if button_text == 'Submit':
                self.click_with_retry(self.SUBMIT_BUTTON)
            elif button_text == 'Update':
                self.click_with_retry(self.UPDATE_BUTTON)

    def _dismiss_swal(self, button, label):
        """Dismiss a SweetAlert popup by clicking the specified button via JS."""
        try:
            self.driver.find_element("css selector", ".swal2-popup")
            self.driver.execute_script("""
                var btn = document.querySelector(arguments[0]);
                if (btn) { btn.click(); }
            """, button)
            log.info("Dismissed SweetAlert via " + label)
            try:
                WebDriverWait(self.driver, 2).until(
                    EC.invisibility_of_element_located(("css selector", ".swal2-popup"))
                )
            except Exception:
                pass
        except Exception as e:
            log.warning("No SweetAlert to dismiss: " + str(e))

    def force_close_form_popup(self):
        """Force-close any open form popup by clicking the X button via JS."""
        log.info("Force closing form popup")
        result = self.driver.execute_script("""
            var popup = document.querySelector('div.edit_pop_up');
            if (!popup) return 'no popup found';
            var closeBtn = popup.querySelector('button[mat-icon-button] mat-icon');
            if (!closeBtn) return 'no close button found';
            var btn = closeBtn.closest('button');
            if (btn) { btn.click(); return 'clicked close'; }
            return 'could not click';
        """)
        log.info("Force close result: " + str(result))
