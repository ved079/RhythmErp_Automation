"""
commodity_base_rate_page.py
--------------------------
Page Object for RhythmERP -> Commodity Settings -> Commodity Base Rate.

Optimised (v2) — UOM golden standard:
- hard_refresh() for fast page reset between tests
- _cleanup() smart cleanup: close form if open, then refresh
- search_and_verify() combines search + existence check
- _click_action_menu_item() replaces broken cdk-column-* locators
- _js_click_popup_button() for Submit/Update (pure JS, no overlay issues)
- Simplified handle_success_alert() (3s timeout, JS dismiss)
- Removed _debug_popup_info() and excessive fallback chains
- Kept label-based mat-select helpers (CBR has 4 dropdowns)

FORM LAYOUT (two-step stepper):
  Step 1: Pricing Type (mat-select), From Date (datepicker),
          To Date (datepicker), Location (mat-select)
  Step 2: Grid with Item Name (mat-select), Item Rate (input), UOM (mat-select)

TABLE COLUMNS (visible):
  - Actions (3-dot menu): View / Edit / Version / History
  - Pricing Type, From Date, To Date, Location

KNOWN BUGS:
  BUG-001 (HIGH)  : Item Rate accepts non-numeric input
  BUG-002 (MEDIUM): Item Rate accepts zero value
  BUG-003 (MEDIUM): Listing shows raw ISO timestamps
  BUG-004 (HIGH)  : To Date overridden to 30/12/2099 on submit
  BUG-005 (LOW)   : Edit disabled for new records
  BUG-006 (MEDIUM): Version creation fails with same From Date

KEY RULES:
  - NEVER use Keys.ESCAPE (use backdrop click + JS overlay removal)
  - JS clicks for Angular Material overlays (mat-select, datepicker)
  - _force_close_panels() uses JS removal, NOT Escape key
  - SweetAlert2 for success/error popups
  - LABEL-BASED XPath for form fields (NOT name/formcontrolname CSS)
"""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from common.base_page import BasePage
from common.logger import log
from config import RHYTHMERP_BASE_URL, EXPLICIT_WAIT


class CommodityBaseRatePage(BasePage):

    PAGE_URL = f"{RHYTHMERP_BASE_URL}/#/dynamic-screens/Commodity%20Base%20Rate"

    # ================================================================
    # TABLE
    # ================================================================
    ADD_BUTTON = ("css", "button.erp-add-btn")
    SEARCH_BUTTON = ("css", "button.search-btn")
    SEARCH_INPUT = ("css", "input#erpSearchInput")
    TABLE_ROWS = ("css", "table#excel-table tbody tr")

    # Action buttons — 3-dot menu in cdk-column-actions (same as UOM)
    ACTIONS_COLUMN = ("css", "td.cdk-column-actions")
    THREE_DOT_MENU_BUTTON = ("css", "td.cdk-column-actions button")

    # ================================================================
    # CREATE / EDIT FORM (label-based locators)
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

    # ================================================================
    # VALIDATION ERRORS
    # ================================================================
    MAT_ERROR = ("css", "mat-error, .mat-mdc-form-field-error")

    # ================================================================
    # NAVIGATION
    # ================================================================

    def navigate_to_page(self):
        """Navigate to CBR page via direct URL (fast and reliable)."""
        log.info("Navigating to Commodity Base Rate page")
        self.driver.get(self.PAGE_URL)
        self._wait_for_page_ready()
        log.info("Arrived at CBR page")

    def hard_refresh(self):
        """Hard refresh (Ctrl+R) and wait for page ready.
        Much faster than full navigate_to_page() for resetting between tests."""
        log.info("Hard refreshing CBR page")
        self.driver.refresh()
        self._wait_for_page_ready()
        log.info("CBR page refreshed and ready")

    def _wait_for_page_ready(self):
        """Wait for the CBR table to appear. Single lambda wait."""
        try:
            WebDriverWait(self.driver, 15).until(
                lambda d: d.find_elements("css selector", "table#excel-table")
            )
            log.info("CBR page ready (table found)")
        except Exception:
            try:
                WebDriverWait(self.driver, 5).until(
                    lambda d: d.find_elements("css selector", "button.search-btn")
                )
                log.info("CBR page ready (search button found)")
            except Exception:
                log.warning("CBR page ready check timed out")

    # ================================================================
    # CLEANUP
    # ================================================================

    def _cleanup(self):
        """Smart cleanup — close form if open, then hard refresh."""
        if self._is_form_popup_open():
            self.force_close_form_popup()
        self.hard_refresh()

    # ================================================================
    # OVERLAY CLEANUP — NEVER use Keys.ESCAPE
    # ================================================================

    def _force_close_panels(self):
        """Remove lingering CDK overlay panels that block clicks."""
        try:
            self.driver.execute_script("""
                document.querySelectorAll('.cdk-overlay-backdrop').forEach(function(el) { el.remove(); });
                document.querySelectorAll('.cdk-overlay-pane').forEach(function(el) { el.remove(); });
            """)
        except Exception as e:
            log.warning(f"_force_close_panels failed: {e}")

    # ================================================================
    # CREATE CBR
    # ================================================================

    def open_add_form(self):
        """Click Add button to open the Create CBR form popup.
        Uses JS click first (bypasses overlay/z-index issues)."""
        log.info("Opening Add CBR form")
        js_click_add = """
        var btn = document.querySelector('button.erp-add-btn');
        if (!btn) { throw new Error('Add button not found in DOM'); }
        btn.scrollIntoView({block:'center'});
        btn.click();
        return 'clicked';
        """
        try:
            self.driver.execute_script(js_click_add)
            log.info("Add button clicked via JS")
        except Exception as e:
            log.warning("JS click failed, falling back to Selenium: " + str(e))
            self.click_with_retry(self.ADD_BUTTON)
        # Wait for the form popup to appear
        try:
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located(("css selector", ".edit_pop_up input, .edit_pop_up mat-select"))
            )
            log.info("Add form opened")
        except Exception:
            log.warning("Add form may not have opened — no inputs found")

    def fill_form(self, data):
        """Fill the CBR add/edit form with provided data dict.
        Uses LABEL-BASED locators for reliable element finding.
        Supports both single-row and multi-row grid data."""
        log.info("Filling CBR form...")

        # Pricing Type (mat-select)
        if data.get("pricing_type"):
            self._open_mat_select_and_choose("Pricing Type", data["pricing_type"])

        # From Date (datepicker input)
        if data.get("from_date"):
            self._set_datepicker_by_label("From Date", data["from_date"])

        # To Date (datepicker input)
        if data.get("to_date"):
            self._set_datepicker_by_label("To Date", data["to_date"])

        # Location (mat-select)
        if data.get("location"):
            self._open_mat_select_and_choose("Location", data["location"])

        # Grid rows
        if data.get("grid_rows"):
            self._fill_grid_rows(data["grid_rows"])
        elif "item_name" in data or data.get("item_rate") is not None or "uom" in data:
            self._fill_single_grid_row(data)

        self._force_close_panels()
        log.info("CBR form filled")

    def submit(self):
        """Click Submit on the Create form via JS click."""
        log.info("Clicking Submit")
        self._js_click_popup_button('Submit')

    # ================================================================
    # SEARCH
    # ================================================================

    def search_cbr(self, search_text):
        """Search for text in the CBR table. Uses JS clicks to bypass overlay issues."""
        log.info(f"Searching CBR for: {search_text}")

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
        except Exception:
            pass

        # Step 2: If search input not visible, click search button via JS
        if search_input is None:
            log.info("Search input not visible, clicking search button via JS")
            try:
                self.driver.execute_script("""
                    var btn = document.querySelector('button.search-btn');
                    if (!btn) { throw new Error('Search button not found'); }
                    btn.scrollIntoView({block:'center'});
                    btn.click();
                """)
            except Exception as e:
                log.error("Failed to click search button: " + str(e))
                return

            try:
                search_input = WebDriverWait(self.driver, 5).until(
                    EC.visibility_of_element_located(("css selector", "input#erpSearchInput"))
                )
            except Exception:
                log.warning("Search input did not become visible")
                return

        # Step 3: Clear and set value
        self.driver.execute_script("arguments[0].value = '';", search_input)
        self.driver.execute_script(
            "arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", search_input
        )
        self.driver.execute_script("arguments[0].value = arguments[1];", search_input, search_text)
        search_input.click()
        for event in ["input", "keyup", "change"]:
            self.driver.execute_script(
                f"arguments[0].dispatchEvent(new Event('{event}', {{ bubbles: true }}));", search_input
            )

        # Step 4: Click search button again to submit
        self.driver.execute_script("""
            var btn = document.querySelector('button.search-btn');
            if (btn) { btn.click(); }
        """)

        # Step 5: Wait for table to refresh
        try:
            WebDriverWait(self.driver, 5).until(
                lambda d: d.find_elements("css selector", "table#excel-table tbody tr")
            )
        except Exception:
            pass

        log.info(f"Search completed for: {search_text}")

    def verify_record_exists(self, search_text, timeout=10):
        """Verify a record exists in the table by searching for text.
        Polls up to timeout seconds to handle slow Angular re-renders."""
        log.info(f"Verifying record '{search_text}' exists in table")
        end_time = time.monotonic() + timeout
        while time.monotonic() < end_time:
            try:
                rows = self.find_elements(self.TABLE_ROWS)
                for row in rows:
                    cells = row.find_elements("css selector", "td")
                    for cell in cells:
                        if search_text in cell.text.strip():
                            log.info(f"Record '{search_text}' found in table")
                            return True
            except Exception:
                pass
            time.sleep(0.5)
        log.error(f"Record '{search_text}' NOT found in table after search")
        return False

    def search_and_verify(self, search_text):
        """Search for text, then verify it exists in filtered results.
        Recommended way to verify a create/update — handles pagination."""
        log.info(f"Searching and verifying: {search_text}")
        self.search_cbr(search_text)
        return self.verify_record_exists(search_text)

    def clear_search(self):
        """Clear search — hard refresh for clean state."""
        log.info("Clearing search - hard refreshing")
        self.hard_refresh()

    # ================================================================
    # VIEW CBR
    # ================================================================

    def click_view_button(self, row_text):
        """Click View button for a row matching row_text via 3-dot menu."""
        self._click_action_menu_item(row_text, "View")

    def is_view_mode(self):
        """Check if the currently open form is in View (read-only) mode."""
        try:
            selects = self.driver.find_elements(
                "css selector",
                "div.edit_pop_up mat-select, .big-model mat-select, mat-dialog-container mat-select"
            )
            for sel in selects:
                try:
                    if sel.is_displayed() and sel.get_attribute("aria-disabled") == "true":
                        return True
                except Exception:
                    continue
            inputs = self.driver.find_elements(
                "css selector",
                "div.edit_pop_up input, .big-model input, mat-dialog-container input"
            )
            for inp in inputs:
                try:
                    if inp.is_displayed() and inp.get_attribute("disabled") is not None:
                        return True
                except Exception:
                    continue
        except Exception:
            pass
        return False

    # ================================================================
    # EDIT CBR
    # ================================================================

    def click_edit_button(self, row_text):
        """Click Edit button for a row matching row_text via 3-dot menu."""
        self._click_action_menu_item(row_text, "Edit")

    def click_update(self):
        """Click Update on the Edit form via JS click."""
        log.info("Clicking Update")
        self._js_click_popup_button('Update')

    def is_edit_enabled(self, row_text=None):
        """Check if Edit is available for a row.
        BUG-005: Edit may be disabled for newly created records."""
        # Try to click edit — if it opens the form, edit is enabled
        # Just check if Edit menu item exists and is not disabled
        try:
            self._open_action_menu(row_text)
            js = """
            var overlay = document.querySelector('.cdk-overlay-container');
            if (!overlay) return false;
            var items = overlay.querySelectorAll('button, span, div');
            for (var i = 0; i < items.length; i++) {
                var text = items[i].textContent.trim();
                if (text === 'Edit') {
                    return !items[i].disabled && items[i].offsetParent !== null;
                }
            }
            return false;
            """
            result = self.driver.execute_script(js)
            self._force_close_panels()
            return result
        except Exception:
            self._force_close_panels()
            return False

    # ================================================================
    # VERSION
    # ================================================================

    def click_version_button(self, row_text):
        """Click Version button for a row matching row_text via 3-dot menu."""
        self._click_action_menu_item(row_text, "Version")

    # ================================================================
    # HISTORY
    # ================================================================

    def click_history_button(self, row_text):
        """Click History button for a row matching row_text via 3-dot menu."""
        self._click_action_menu_item(row_text, "History")

    def is_history_empty(self):
        """Check if History popup shows 'No data available'."""
        try:
            no_data = self.is_present(self.HISTORY_NO_DATA, timeout=5)
            no_data_text = self.is_present(self.HISTORY_NO_DATA_TEXT, timeout=5)
            return no_data or no_data_text
        except Exception:
            return True

    def close_history_popup(self):
        """Close History popup by clicking Cancel via JS."""
        log.info("Closing History popup")
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

    # ================================================================
    # POPUP CLOSE
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
                        buttons[j].click(); return;
                    }
                }
            }
        """)

    def force_close_form_popup(self):
        """Force-close any open form popup by clicking X button via JS."""
        log.info("Force closing form popup")
        self.driver.execute_script("""
            var popup = document.querySelector('div.edit_pop_up');
            if (!popup) return 'no popup';
            var closeBtn = popup.querySelector('button[mat-icon-button] mat-icon');
            if (!closeBtn) return 'no close button';
            var btn = closeBtn.closest('button');
            if (btn) { btn.click(); return 'clicked close'; }
            return 'could not click';
        """)

    # ================================================================
    # SUCCESS ALERT (SweetAlert2)
    # ================================================================

    def handle_success_alert(self):
        """Handle SweetAlert2 success notification — fast dismiss (3s timeout)."""
        log.info("Handling success alert")
        try:
            WebDriverWait(self.driver, 3).until(
                EC.visibility_of_element_located(("css selector", ".swal2-container"))
            )
            self.driver.execute_script("""
                var btn = document.querySelector('.swal2-confirm');
                if (btn) { btn.click(); }
            """)
            try:
                WebDriverWait(self.driver, 3).until(
                    EC.invisibility_of_element_located(("css selector", ".swal2-container"))
                )
            except Exception:
                pass
            log.info("Success alert dismissed")
        except Exception:
            log.info("No SweetAlert found (may have auto-dismissed)")

    # ================================================================
    # VALIDATION ALERT HANDLERS
    # ================================================================

    def handle_validation_warning(self):
        """Pattern A: Dismiss 'Please correct highlighted fields' via JS click."""
        log.info("Handling validation warning (Pattern A)")
        self._dismiss_swal(button=".swal2-confirm", label="OK")

    def handle_validation_download(self):
        """Pattern B: Dismiss 'Fields validation failed' via JS click on Cancel."""
        log.info("Handling validation download (Pattern B)")
        self._dismiss_swal(button=".swal2-cancel", label="Cancel")

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
        """Dismiss any SweetAlert — try Cancel first (Pattern B), then OK (Pattern A)."""
        log.info("Dismissing any validation alert")
        self.driver.execute_script("""
            var cancel = document.querySelector('.swal2-cancel');
            if (cancel) { cancel.click(); return; }
            var confirm = document.querySelector('.swal2-confirm');
            if (confirm) { confirm.click(); }
        """)
        try:
            WebDriverWait(self.driver, 2).until(
                EC.invisibility_of_element_located(("css selector", ".swal2-popup"))
            )
        except Exception:
            pass

    # ================================================================
    # FIELD HELPERS
    # ================================================================

    def get_mat_error_text(self):
        """Get all visible mat-error texts from the form."""
        errors = self.driver.find_elements("css selector", "mat-error, .mat-mdc-form-field-error")
        texts = []
        for e in errors:
            try:
                t = e.text.strip()
                if t:
                    texts.append(t)
            except Exception:
                continue
        return texts

    def is_add_form_open(self):
        """Check if the Add/Create CBR popup is currently open."""
        return self._is_form_popup_open()

    def is_form_closed(self):
        """Check if the form popup is no longer visible."""
        return not self._is_form_popup_open()

    # ================================================================
    # TABLE HELPERS
    # ================================================================

    def get_table_row_count(self):
        """Return the number of visible data rows in the table."""
        rows = self.driver.find_elements("css selector", "table#excel-table tbody tr")
        return len(rows)

    def get_table_data(self):
        """Get all visible data from the listing table.
        Returns list of dicts with column headers as keys."""
        try:
            headers = [
                h.text.strip()
                for h in self.driver.find_elements("css selector", "table#excel-table thead th")
            ]
            rows = self.driver.find_elements("css selector", "table#excel-table tbody tr")
            data = []
            for row in rows:
                try:
                    cells = row.find_elements("tag name", "td")
                    row_data = {}
                    for idx, cell in enumerate(cells):
                        if idx < len(headers):
                            row_data[headers[idx]] = cell.text.strip()
                    data.append(row_data)
                except Exception:
                    continue
            return data
        except Exception:
            return []

    def is_record_in_table(self, pricing_type=None, location=None):
        """Check if a matching record exists in the listing table."""
        data = self.get_table_data()
        for row in data:
            match = True
            if pricing_type and row.get("Pricing Type", "").strip() != pricing_type:
                match = False
            if location and row.get("Location", "").strip() != location:
                match = False
            if match:
                return True
        return False

    def has_iso_dates_in_listing(self):
        """Check if any dates in the listing are in raw ISO format (BUG-003)."""
        data = self.get_table_data()
        for row in data:
            for key in ["From Date", "To Date"]:
                val = row.get(key, "")
                if "T" in val and ":" in val and len(val) > 15:
                    return True
        return False

    # ================================================================
    # COMPLETE WORKFLOW
    # ================================================================

    def create_cbr_record(self, data):
        """Complete workflow: Add -> Fill -> Submit -> Return success status."""
        self.open_add_form()
        self.fill_form(data)
        self.submit()

        success_msg = self.handle_success_alert()
        if self.is_form_closed():
            log.info("Form closed after submit (success)")
            return True

        if self.is_validation_alert_present(timeout=3):
            self.dismiss_any_validation_alert()
            log.warning("Validation alert on submit")
            return False

        return False

    # ================================================================
    # MAT-SELECT HELPERS — LABEL-BASED approach
    # ================================================================

    def _find_mat_select_by_label(self, label_text, timeout=8):
        """Find a mat-select by its mat-label text. Primary method for dropdowns."""
        xpath = (
            f"//mat-form-field[.//mat-label[contains(text(),'{label_text}')]]"
            f"//mat-select"
        )
        log.info(f"Finding mat-select by label: '{label_text}'")
        try:
            el = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            return el
        except Exception:
            # Fallback: <label> instead of <mat-label>
            xpath2 = (
                f"//mat-form-field[.//label[contains(text(),'{label_text}')]]"
                f"//mat-select"
            )
            try:
                el = WebDriverWait(self.driver, 3).until(
                    EC.presence_of_element_located((By.XPATH, xpath2))
                )
                return el
            except Exception:
                raise NoSuchElementException(
                    f"mat-select with label '{label_text}' not found"
                )

    def _find_input_by_label(self, label_text, timeout=8):
        """Find an input by its mat-label text."""
        xpath = (
            f"//mat-form-field[.//mat-label[contains(text(),'{label_text}')]]"
            f"//input"
        )
        log.info(f"Finding input by label: '{label_text}'")
        try:
            el = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            return el
        except Exception:
            xpath2 = (
                f"//mat-form-field[.//label[contains(text(),'{label_text}')]]"
                f"//input"
            )
            try:
                el = WebDriverWait(self.driver, 3).until(
                    EC.presence_of_element_located((By.XPATH, xpath2))
                )
                return el
            except Exception:
                raise NoSuchElementException(
                    f"input with label '{label_text}' not found"
                )

    def _open_mat_select_and_choose(self, label_text, option_text):
        """Complete workflow: find mat-select by label, click, select option.
        If option_text is None or empty, selects FIRST available option."""
        select_first = option_text is None or option_text == ""
        log.info(
            f"Opening mat-select '{label_text}' to select "
            f"{'[FIRST]' if select_first else repr(option_text)}"
        )
        self._force_close_panels()

        # Find the mat-select
        select_el = self._find_mat_select_by_label(label_text)

        # Click to open
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block:'center'}); arguments[0].click();",
            select_el,
        )

        # Wait for overlay options
        try:
            WebDriverWait(self.driver, 8).until(
                EC.presence_of_element_located(
                    ("css selector", ".cdk-overlay-pane mat-option")
                )
            )
        except Exception:
            # Retry click
            self.driver.execute_script("arguments[0].click();", select_el)
            try:
                WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located(
                        ("css selector", ".cdk-overlay-pane mat-option")
                    )
                )
            except Exception:
                self._force_close_panels()
                raise ValueError(f"Dropdown overlay did not appear for '{label_text}'")

        # Collect options
        available_options = []
        for opt in self.driver.find_elements("css selector", "mat-option"):
            try:
                txt = opt.text.strip()
                if txt:
                    available_options.append((txt, opt))
            except Exception:
                continue

        if not available_options:
            self._force_close_panels()
            raise ValueError(f"No options found in '{label_text}' dropdown")

        # Select the option
        selected_text = None

        if select_first:
            first_text, first_el = available_options[0]
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block:'center'}); arguments[0].click();", first_el
            )
            selected_text = first_text
        else:
            for opt_text, opt_el in available_options:
                if opt_text == option_text or option_text.lower() in opt_text.lower():
                    self.driver.execute_script(
                        "arguments[0].scrollIntoView({block:'center'}); arguments[0].click();", opt_el
                    )
                    selected_text = opt_text
                    break
            if selected_text is None:
                # Fallback to first option
                first_text, first_el = available_options[0]
                log.warning(
                    f"Option '{option_text}' not found, falling back to FIRST: '{first_text}'"
                )
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'}); arguments[0].click();", first_el
                )
                selected_text = first_text

        self._force_close_panels()
        log.info(f"Selected '{selected_text}' from '{label_text}'")
        return selected_text

    # ================================================================
    # DATEPICKER HELPERS
    # ================================================================

    def _set_datepicker_by_label(self, label_text, date_str):
        """Set a date value in an Angular Material datepicker by label.
        date_str format: DD/MM/YYYY"""
        log.info(f"Setting date '{date_str}' for label '{label_text}'")
        try:
            el = self._find_input_by_label(label_text)

            # Clear via JS
            self.driver.execute_script(
                "var s = Object.getOwnPropertyDescriptor("
                "  window.HTMLInputElement.prototype,'value').set;"
                "s.call(arguments[0], '');"
                "arguments[0].dispatchEvent(new Event('input',{bubbles:true}));"
                "arguments[0].dispatchEvent(new Event('change',{bubbles:true}));",
                el,
            )
            # Remove readonly
            self.driver.execute_script("arguments[0].removeAttribute('readonly');", el)
            # Type the date
            el.send_keys(date_str)
            # Tab to confirm
            el.send_keys(Keys.TAB)
            log.info(f"Date '{date_str}' set for '{label_text}'")
        except Exception as e:
            log.warning(f"Could not set date '{date_str}' for '{label_text}': {e}")

    # ================================================================
    # GRID ROW HELPERS
    # ================================================================

    def _fill_single_grid_row(self, data):
        """Fill a single grid row with Item Name, Rate, UOM.
        Use None/"" for item_name/uom to select FIRST available option."""
        if "item_name" in data:
            self._open_mat_select_and_choose("Item Name", data["item_name"])

        if data.get("item_rate") is not None:
            try:
                rate_el = self._find_input_by_label("Item Rate")
                self.driver.execute_script(
                    "var s = Object.getOwnPropertyDescriptor("
                    "  window.HTMLInputElement.prototype,'value').set;"
                    "s.call(arguments[0], '');"
                    "arguments[0].dispatchEvent(new Event('input',{bubbles:true}));"
                    "arguments[0].dispatchEvent(new Event('change',{bubbles:true}));",
                    rate_el,
                )
                rate_el.send_keys(str(data["item_rate"]))
            except Exception:
                log.warning("Could not fill Item Rate")

        if "uom" in data:
            self._open_mat_select_and_choose("UOM", data["uom"])

    def _fill_grid_rows(self, grid_rows):
        """Fill multiple grid rows."""
        for idx, row_data in enumerate(grid_rows):
            if idx > 0:
                # Click "Add Row" for subsequent rows
                try:
                    self.driver.execute_script("""
                        var btn = document.querySelector('button.add-row, button[mattooltip="Add Row"]');
                        if (btn) { btn.click(); }
                    """)
                except Exception:
                    pass
            self._fill_single_grid_row(row_data)

    # ================================================================
    # UTILITY - ACTION BUTTON CLICKER (pure JS, 3-dot menu)
    # ================================================================

    def _open_action_menu(self, row_text):
        """Open the 3-dot menu for a row containing row_text."""
        js = """
        var table = document.querySelector('table#excel-table');
        if (!table) { throw new Error('Table not found'); }
        var rows = table.querySelectorAll('tbody tr');
        for (var i = 0; i < rows.length; i++) {
            var cells = rows[i].querySelectorAll('td');
            for (var j = 0; j < cells.length; j++) {
                if (cells[j].textContent.trim().indexOf(arguments[0]) !== -1) {
                    var menuBtn = rows[i].querySelector('td.cdk-column-actions button');
                    if (!menuBtn) { throw new Error('3-dot menu button not found'); }
                    menuBtn.scrollIntoView({block:'center'});
                    menuBtn.click();
                    return 'menu_opened';
                }
            }
        }
        throw new Error('Row with text "' + arguments[0] + '" not found');
        """
        result = self.driver.execute_script(js, row_text)

        # Wait briefly for dropdown to render
        try:
            WebDriverWait(self.driver, 2).until(
                EC.presence_of_element_located(
                    ("css selector", ".cdk-overlay-container .cdk-overlay-pane")
                )
            )
        except Exception:
            pass
        return result

    def _click_action_menu_item(self, row_text, action_name):
        """Click an action menu item (View/Edit/Version/History) for a specific row.
        Uses 3-dot (⋮) menu in cdk-column-actions."""
        log.info(f"Clicking {action_name} via 3-dot menu for row: {row_text}")

        # Open the 3-dot menu
        self._open_action_menu(row_text)

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
        // Fallback: partial match
        for (var i = 0; i < items.length; i++) {
            var text = items[i].textContent.trim().toLowerCase();
            if (text.indexOf(arguments[0].toLowerCase()) !== -1) {
                items[i].click();
                return 'clicked_partial_' + arguments[0];
            }
        }
        throw new Error('Menu item "' + arguments[0] + '" not found in dropdown');
        """
        result = self.driver.execute_script(js_click_item, action_name)
        log.info(f"Successfully clicked {action_name} for row: {row_text}")
        return result

    # ================================================================
    # UTILITY - JS CLICK POPUP BUTTON
    # ================================================================

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
            log.info(f"JS click {button_text}: {result}")
        except Exception as e:
            log.warning(f"JS click failed for {button_text}: {e}, falling back to Selenium")
            if button_text == 'Submit':
                self.click_with_retry(self.SUBMIT_BUTTON)
            elif button_text == 'Update':
                self.click_with_retry(self.UPDATE_BUTTON)

    # ================================================================
    # UTILITY - DISMISS SWAL
    # ================================================================

    def _dismiss_swal(self, button, label):
        """Dismiss a SweetAlert popup by clicking the specified button via JS."""
        try:
            self.driver.find_element("css selector", ".swal2-popup")
            self.driver.execute_script("""
                var btn = document.querySelector(arguments[0]);
                if (btn) { btn.click(); }
            """, button)
            log.info(f"Dismissed SweetAlert via {label}")
            try:
                WebDriverWait(self.driver, 2).until(
                    EC.invisibility_of_element_located(("css selector", ".swal2-popup"))
                )
            except Exception:
                pass
        except Exception:
            log.warning("No SweetAlert to dismiss")

    # ================================================================
    # UTILITY - FORM POPUP CHECK
    # ================================================================

    def _is_form_popup_open(self):
        """Check if any form popup is visible."""
        try:
            popups = self.driver.find_elements(
                "css selector",
                "div.edit_pop_up.override_edit_pop_up.popup-mode, "
                "div.big-model, mat-dialog-container"
            )
            for p in popups:
                try:
                    if p.is_displayed():
                        return True
                except Exception:
                    continue
        except Exception:
            pass
        return False
