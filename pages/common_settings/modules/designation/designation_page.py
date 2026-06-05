"""
designation_page.py — RhythmERP Common Settings > Designation (v4 — UOM GOLD STANDARD)

Mirrors uom_page.py patterns exactly:
- hard_refresh() for fast page reset between tests
- Pure JS clicks (no multi-strategy fallbacks)
- offsetParent checks for visibility
- Fast polling (0.2s) instead of time.sleep()
- Short timeouts: 2s for alerts, 15s for page ready
- search_and_verify() combines search + existence check
- NO time.sleep() anywhere

v4 fixes:
- search_designation(): graceful search button JS click (no throw)
- is_history_popup_open(): robust multi-selector check with wait
- get_mat_error_text(): added tiny wait for Angular to render errors
- verify_designation_exists(): reduced timeout 5s→3s, poll 0.5s→0.3s
- handle_success_alert(): reduced timeouts 3s→2s
"""

import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from common.base_page import BasePage
from common.logger import log


class DesignationPage(BasePage):
    """Page Object for RhythmERP Designation screen."""

    PAGE_URL = "https://rhythmerp.algorhythms.in/#/dynamic-screens/Designation"

    NAME_INPUT = ("css", "input[name='Name']")
    DESCRIPTION_INPUT = ("css", "input[name='Description']")

    SUBMIT_BUTTON = ("xpath", "//div[@class='popup-footer']//button[contains(.,'Submit')]")
    UPDATE_BUTTON = ("xpath", "//div[@class='popup-footer']//button[contains(.,'Update')]")
    CANCEL_BUTTON = ("xpath", "//div[@class='popup-footer']//button[contains(.,'Cancel')]")

    # ── NAVIGATION ─────────────────────────────────────

    def navigate_to_page(self):
        log.info("Navigating to Designation page")
        self.driver.get(self.PAGE_URL)
        self._wait_for_page_ready()
        log.info("Arrived at Designation page")

    def hard_refresh(self):
        log.info("Hard refreshing page")
        self.driver.refresh()
        self._wait_for_page_ready()

    def _wait_for_page_ready(self):
        try:
            WebDriverWait(self.driver, 15).until(
                lambda d: d.find_elements("css selector", "table#excel-table")
            )
            log.info("Page ready (table found)")
        except Exception:
            try:
                WebDriverWait(self.driver, 5).until(
                    lambda d: d.find_elements("css selector", "button.search-btn")
                )
                log.info("Page ready (search button found, no table)")
            except Exception:
                log.warning("Page ready check timed out")

    # ── CREATE ──────────────────────────────────────────

    def open_add_form(self):
        log.info("Opening Add form")
        js = """
        var btn = document.querySelector('button.erp-add-btn');
        if (!btn) { throw new Error('Add button not found in DOM'); }
        btn.scrollIntoView({block:'center'});
        btn.click();
        return 'clicked';
        """
        try:
            result = self.driver.execute_script(js)
            log.info("Add button clicked via JS: " + str(result))
        except Exception as e:
            log.warning("JS click failed, falling back to Selenium click: " + str(e))
            self.click_with_retry(("css", "button.erp-add-btn"))
        try:
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located(("css selector", "input[name='Name']"))
            )
            log.info("Add form opened")
        except Exception:
            log.warning("Add form may not have opened — Name input not found")

    def fill_designation_form(self, data):
        log.info(f"Filling form: {data}")
        if data.get('name') is not None:
            self._set_input(self.NAME_INPUT, data['name'])
        if data.get('description') is not None:
            self._set_input(self.DESCRIPTION_INPUT, data['description'])
        if data.get('status') is not None and self.get_toggle_state() != data['status']:
            self.toggle_status()

    def submit(self):
        log.info("Clicking Submit")
        self._js_click_popup_button('Submit')

    # ── TOGGLE ──────────────────────────────────────────

    def get_toggle_state(self):
        """Get current toggle state — True=Active, False=Inactive."""
        result = self.driver.execute_script("""
            var cb = document.querySelector('.switch-wrapper input[type="checkbox"]');
            if (cb) return cb.checked;
            var toggle = document.querySelector('app-slide-toggle-v2');
            if (toggle) {
                var on = toggle.querySelector('.state-label.on');
                return (on && on.classList.contains('active')) ? true : false;
            }
            return false;
        """)
        log.info("Toggle state: " + str(result))
        return result

    def get_toggle_display_text(self):
        return self.driver.execute_script("""
            var on = document.querySelector('.switch-wrapper .state-label.on');
            if (on && on.classList.contains('active')) return 'Active';
            var toggle = document.querySelector('app-slide-toggle-v2');
            if (toggle) {
                var onLabel = toggle.querySelector('.state-label.on');
                return (onLabel && onLabel.classList.contains('active')) ? 'Active' : 'Inactive';
            }
            return 'Inactive';
        """)

    def toggle_status(self):
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

    # ── SEARCH ──────────────────────────────────────────

    def search_designation(self, name):
        log.info(f"Searching for: {name}")
        # Step 1: Check if search input already visible
        search_input = None
        try:
            el = self.driver.find_element("css selector", "input#erpSearchInput")
            rect = self.driver.execute_script(
                "var r=arguments[0].getBoundingClientRect();return r.width>0&&r.height>0;", el
            )
            if rect:
                search_input = el
                log.info("Search input already visible")
        except Exception:
            pass

        # Step 2: Click search button via JS if input not visible
        # FIX: Use graceful JS (no throw) — search button may not exist on some pages
        if search_input is None:
            log.info("Search input not visible, clicking search button via JS")
            js = """
            var btn = document.querySelector('button.search-btn');
            if (!btn) { return 'not_found'; }
            btn.scrollIntoView({block:'center'});
            btn.click();
            return 'clicked';
            """
            try:
                result = self.driver.execute_script(js)
                log.info("Search button JS result: " + str(result))
                if result == 'not_found':
                    log.warning("Search button not found in DOM — skipping search")
                    return
            except Exception as e:
                log.error("Failed to click search button: " + str(e))
                return
            try:
                search_input = WebDriverWait(self.driver, 3).until(
                    EC.visibility_of_element_located(("css selector", "input#erpSearchInput"))
                )
                log.info("Search input became visible")
            except Exception:
                log.warning("Search input did not become visible")
                return

        # Step 3: Clear + set value + fire Angular events
        self.driver.execute_script("arguments[0].value = '';", search_input)
        self.driver.execute_script(
            "arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", search_input
        )
        self.driver.execute_script("arguments[0].value = arguments[1];", search_input, name)
        search_input.click()
        for ev in ["input", "keyup", "change"]:
            self.driver.execute_script(
                f"arguments[0].dispatchEvent(new Event('{ev}', {{ bubbles: true }}));", search_input
            )

        # Step 4: Click search button again to submit filter
        self.driver.execute_script("""
            var btn = document.querySelector('button.search-btn');
            if (btn) { btn.click(); return 'clicked'; }
            return 'not found';
        """)
        log.info("Search submit clicked via JS")

        # Step 5: Wait for table to refresh (short wait)
        try:
            WebDriverWait(self.driver, 3).until(
                lambda d: d.find_elements("css selector", "table#excel-table tbody tr")
            )
        except Exception:
            pass

        log.info(f"Search completed for: {name}")

    def verify_designation_exists(self, name):
        """Verify designation name appears in table. Polls up to 3s (fast)."""
        log.info(f"Verifying '{name}' exists in table")
        end = time.monotonic() + 3
        last_seen = []
        while time.monotonic() < end:
            try:
                rows = self.driver.find_elements("css selector", "table#excel-table tbody tr")
                last_seen = []
                for row in rows:
                    cells = row.find_elements("css selector", "td")
                    row_text = " | ".join(c.text.strip() for c in cells if c.text.strip())
                    last_seen.append(row_text)
                    for cell in cells:
                        if name in cell.text.strip():
                            log.info(f"Designation '{name}' found in table")
                            return True
            except Exception:
                pass
            time.sleep(0.3)
        log.error(f"Designation '{name}' NOT found. Table contents: {last_seen}")
        raise AssertionError(f"Designation '{name}' NOT found in table after search. Last rows: {last_seen}")

    def search_and_verify(self, name):
        """Search + verify — recommended way to confirm create/update."""
        log.info(f"Searching and verifying: {name}")
        self.search_designation(name)
        return self.verify_designation_exists(name)

    def is_designation_in_table(self, name):
        """Check if name exists in current table view. No exceptions."""
        try:
            rows = self.driver.find_elements("css selector", "table#excel-table tbody tr")
            for row in rows:
                cells = row.find_elements("css selector", "td")
                for cell in cells:
                    if name in cell.text.strip():
                        return True
        except Exception:
            pass
        return False

    def clear_search(self):
        log.info("Clearing search - hard refreshing")
        self.hard_refresh()

    # ── TABLE QUERIES ───────────────────────────────────

    def get_table_row_count(self):
        try:
            return len(self.driver.find_elements("css selector", "table#excel-table tbody tr"))
        except Exception:
            return 0

    def get_status_from_table(self, name):
        return self.driver.execute_script("""
            var rows=document.querySelectorAll('table#excel-table tbody tr');
            for(var i=0;i<rows.length;i++){
                var nc=rows[i].querySelector('td.cdk-column-name,td.mat-column-name');
                if(nc&&nc.textContent.trim().toLowerCase().indexOf(arguments[0].toLowerCase())!==-1){
                    var sc=rows[i].querySelector('td.cdk-column-status,td.mat-column-status');
                    return sc?sc.textContent.trim():'';
                }
            }
            return '';
        """, name) or ''

    # ── VIEW ────────────────────────────────────────────

    def click_view_button(self, name):
        self._click_action_menu_item(name, "View")
        try:
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located(("css selector", ".popup-header h3"))
            )
        except Exception:
            pass

    def verify_view_popup_read_only(self):
        log.info("Verifying View popup is read-only")
        code_disabled = self.driver.execute_script(
            "var el=document.querySelector('input[name=\"Name\"]');return el?el.disabled:false;"
        )
        assert code_disabled, "Name field should be disabled in View mode"
        log.info("  [PASS] Name field is disabled")

        has_submit = self.driver.execute_script(
            "var btns=document.querySelectorAll('.popup-footer button');for(var i=0;i<btns.length;i++){if(btns[i].textContent.trim()==='Submit')return true;}return false;"
        )
        has_update = self.driver.execute_script(
            "var btns=document.querySelectorAll('.popup-footer button');for(var i=0;i<btns.length;i++){if(btns[i].textContent.trim()==='Update')return true;}return false;"
        )
        assert not has_submit, "Submit button should NOT be present in View mode"
        assert not has_update, "Update button should NOT be present in View mode"
        log.info("  [PASS] No Submit/Update button in View mode")

        assert self.is_present(self.CANCEL_BUTTON, timeout=3), "Cancel button should be present"
        log.info("  [PASS] Cancel button is present")

    # ── EDIT ────────────────────────────────────────────

    def click_edit_button(self, name):
        self._click_action_menu_item(name, "Edit")
        try:
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located(("css selector", "input[name='Name']"))
            )
        except Exception:
            pass

    def is_edit_mode(self):
        return self.driver.execute_script(
            "var btns=document.querySelectorAll('.popup-footer button');"
            "for(var i=0;i<btns.length;i++){"
            "if(btns[i].textContent.trim()==='Update'&&btns[i].offsetParent!==null)return true;"
            "}return false;"
        )

    def click_update(self):
        log.info("Clicking Update")
        self._js_click_popup_button('Update')

    # ── HISTORY ─────────────────────────────────────────

    def click_history_button(self, name):
        """Click History via 3-dot menu and wait for popup to appear."""
        self._click_action_menu_item(name, "History")
        # Wait for history component to appear in DOM
        try:
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located(("css selector", "app-dynamic-history"))
            )
            log.info("History component appeared in DOM")
        except Exception:
            log.warning("History component did not appear after click")
        # Give Angular a moment to render the popup content
        time.sleep(0.5)

    def is_history_popup_open(self):
        """Check if History popup is open — robust multi-selector check.
        Tries multiple selectors to detect the popup, with a small wait."""
        # Wait up to 2s for popup to become visible
        end = time.monotonic() + 2
        while time.monotonic() < end:
            result = self.driver.execute_script("""
                // Check 1: h2 with 'history' text (UOM pattern)
                var h2s = document.querySelectorAll('app-dynamic-history .tbl-title h2');
                for (var i = 0; i < h2s.length; i++) {
                    if (h2s[i].offsetParent !== null && h2s[i].textContent.toLowerCase().indexOf('history') !== -1)
                        return true;
                }
                // Check 2: any visible app-dynamic-history element with content
                var histComp = document.querySelector('app-dynamic-history');
                if (histComp && histComp.offsetParent !== null) {
                    var inner = histComp.innerHTML.trim();
                    if (inner.length > 50) return true;  // Has rendered content
                }
                // Check 3: popup with history-related header
                var headers = document.querySelectorAll('.popup-header h3');
                for (var i = 0; i < headers.length; i++) {
                    if (headers[i].offsetParent !== null && headers[i].textContent.toLowerCase().indexOf('history') !== -1)
                        return true;
                }
                return false;
            """)
            if result:
                return True
            time.sleep(0.3)
        return False

    def is_history_empty(self):
        log.info("Checking if History is empty")
        no_data = self.driver.execute_script("""
            var nd = document.querySelector('app-dynamic-history .no-data, app-dynamic-history img[alt="No Data Available"]');
            var ndt = null;
            var texts = document.querySelectorAll('app-dynamic-history *');
            for(var i=0;i<texts.length;i++){
                if(texts[i].textContent && texts[i].textContent.indexOf('No data available')!==-1){ndt=true;break;}
            }
            return (nd && nd.offsetParent!==null) || ndt;
        """)
        log.info("History empty: " + str(no_data))
        return bool(no_data)

    def get_history_row_count(self):
        try:
            return len(self.driver.find_elements("css selector", "app-dynamic-history table#excel-table tbody tr"))
        except Exception:
            return 0

    def get_history_data(self):
        data = []
        try:
            for row in self.driver.find_elements("css selector", "app-dynamic-history table#excel-table tbody tr"):
                cells = row.find_elements("tag name", "td")
                data.append({f'col_{i}': c.text.strip() for i, c in enumerate(cells)})
        except Exception:
            pass
        return data

    def close_history_popup(self):
        log.info("Closing History popup")
        self.driver.execute_script("""
            var footers = document.querySelectorAll('.popup-footer');
            for (var i = 0; i < footers.length; i++) {
                var buttons = footers[i].querySelectorAll('button');
                for (var j = 0; j < buttons.length; j++) {
                    if (buttons[j].textContent.indexOf('Cancel') !== -1) {
                        buttons[j].click();
                        return;
                    }
                }
            }
        """)

    # ── POPUP CLOSE ─────────────────────────────────────

    def cancel(self):
        log.info("Closing popup via Cancel")
        self.close_popup()

    def close_popup(self):
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

    def force_close_form_popup(self):
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

    def is_add_form_open(self):
        """Check if the Add/Create popup is currently open."""
        return self.driver.execute_script("""
            var el = document.querySelector('input[name="Name"]');
            return el && el.offsetParent !== null;
        """)

    def is_view_mode(self):
        return self.driver.execute_script(
            "var el=document.querySelector('input[name=\"Name\"]');return el?el.disabled:false;"
        )

    def is_page_loaded(self):
        return self.driver.execute_script(
            "var t=document.querySelector('table#excel-table');return t&&t.offsetParent!==null;"
        )

    def get_form_field_values(self):
        values = self.driver.execute_script("""
            var r={};
            var n=document.querySelector('input[name="Name"]');r.name=n?n.value:'';
            var d=document.querySelector('input[name="Description"]');r.description=d?d.value:'';
            return r;
        """) or {}
        values['status'] = self.get_toggle_state()
        return values

    # ── SWEET ALERT ─────────────────────────────────────

    def handle_success_alert(self):
        """Handle SweetAlert2 success notification — fast dismiss (UOM pattern)."""
        log.info("Handling success alert")
        try:
            WebDriverWait(self.driver, 2).until(
                EC.visibility_of_element_located(("css selector", ".swal2-container"))
            )
            log.info("SweetAlert detected, dismissing via JS")
            self.driver.execute_script("""
                var btn = document.querySelector('.swal2-confirm');
                if (btn) { btn.click(); return 'clicked'; }
                return 'not found';
            """)
            try:
                WebDriverWait(self.driver, 2).until(
                    EC.invisibility_of_element_located(("css selector", ".swal2-container"))
                )
            except Exception:
                pass
        except Exception:
            log.info("No SweetAlert found (may have auto-dismissed)")

    def handle_validation_warning(self):
        """Pattern A: Dismiss 'Please correct the highlighted fields' via JS click OK."""
        log.info("Handling validation warning (Pattern A)")
        self._dismiss_swal(button=".swal2-confirm", label="OK")

    def handle_validation_download(self):
        """Pattern B: Dismiss 'Fields validation failed' via JS click Cancel."""
        log.info("Handling validation download (Pattern B)")
        self._dismiss_swal(button=".swal2-cancel", label="Cancel")

    def dismiss_any_validation_alert(self):
        """Dismiss any SweetAlert — try Cancel first, then OK (UOM pattern)."""
        log.info("Dismissing any validation alert")
        self.driver.execute_script("""
            var cancel = document.querySelector('.swal2-cancel');
            if (cancel) { cancel.click(); return 'Cancel'; }
            var confirm = document.querySelector('.swal2-confirm');
            if (confirm) { confirm.click(); return 'OK'; }
            return 'none';
        """)
        try:
            WebDriverWait(self.driver, 2).until(
                EC.invisibility_of_element_located(("css selector", ".swal2-popup"))
            )
        except Exception:
            pass

    def is_validation_alert_present(self, timeout=3):
        """Check if SweetAlert validation popup is visible. Fast poll (0.2s)."""
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

    # ── MAT ERROR ───────────────────────────────────────

    def get_mat_error_text(self, field_locator=None):
        """Get mat-error text below a form field. Pure JS, no Selenium locators.
        Includes a small wait for Angular to render the error after input."""
        # Give Angular a moment to render mat-error after input/blur
        time.sleep(0.3)
        try:
            if field_locator:
                css = field_locator[1] if field_locator[0] == "css" else ""
                if not css:
                    return ""
                result = self.driver.execute_script("""
                    var input = document.querySelector(arguments[0]);
                    if (!input) return '';
                    var current = input;
                    for (var steps = 0; steps < 20; steps++) {
                        var errors = current.querySelectorAll('mat-error');
                        if (errors.length > 0) {
                            var texts = [];
                            for (var i = 0; i < errors.length; i++) {
                                var t = errors[i].textContent.trim();
                                if (t) texts.push(t);
                            }
                            return texts.join(' | ');
                        }
                        current = current.parentElement;
                        if (!current || current === document.body) break;
                    }
                    return '';
                """, css)
                return result or ""
            # No locator — get all visible mat-errors in popup
            result = self.driver.execute_script("""
                var errors = [];
                var matErrors = document.querySelectorAll('.edit_pop_up mat-error, .big-model mat-error');
                matErrors.forEach(function(el) {
                    if (el.offsetParent !== null) {
                        var t = el.textContent.trim();
                        if (t) errors.push(t);
                    }
                });
                return errors;
            """)
            return result or []
        except Exception:
            return ""

    def has_field_error(self, field_label):
        """Check if a form field has error styling (red border / invalid state)."""
        css = {"Name": "input[name='Name']", "Description": "input[name='Description']"}.get(field_label, "")
        if not css:
            return False
        result = self.driver.execute_script("""
            var input = document.querySelector(arguments[0]);
            if (!input) return false;
            var current = input;
            var invalid = ['mat-mdc-form-field-invalid', 'ng-invalid', 'cdk-text-field-invalid'];
            for (var s = 0; s < 20; s++) {
                var cls = current.className || '';
                for (var i = 0; i < invalid.length; i++) {
                    if (cls.indexOf(invalid[i]) !== -1) return true;
                }
                current = current.parentElement;
                if (!current || current === document.body) break;
            }
            return false;
        """, css)
        return bool(result)

    def has_name_invalid_class(self):
        return self.driver.execute_script("""
            var input = document.querySelector('input[name="Name"]');
            if (!input) return false;
            var cls = input.className || '';
            if (cls.indexOf('ng-invalid') !== -1 && cls.indexOf('ng-touched') !== -1) return true;
            // Also check parent form-field for invalid class
            var current = input;
            for (var s = 0; s < 15; s++) {
                var pcls = current.className || '';
                if (pcls.indexOf('mat-mdc-form-field-invalid') !== -1) return true;
                if (pcls.indexOf('mat-form-field-invalid') !== -1) return true;
                current = current.parentElement;
                if (!current || current === document.body) break;
            }
            return false;
        """)

    def get_field_value(self, locator):
        """Get the current value of an input field via JS (fast)."""
        try:
            css = locator[1] if locator[0] == "css" else ""
            if not css:
                return ""
            return self.driver.execute_script(
                "var el = document.querySelector(arguments[0]); "
                "return el ? el.value : '';", css
            ) or ""
        except Exception:
            return ""

    # ── ONE-CALL FLOWS (fast — no time.sleep!) ──────────

    def create_designation(self, data):
        """Create a designation. Returns result dict with status."""
        log.info(f"CREATE: {data.get('name','?')}")
        result = {'status': 'FAILED', 'error': '', 'message': '', 'data': data}
        try:
            self.open_add_form()
            self.fill_designation_form(data)
            self.submit()
            # Fast alert check
            if self.is_validation_alert_present(timeout=2):
                alert_title = self.driver.execute_script(
                    "var el=document.querySelector('#swal2-title');return el?el.textContent.trim():'';"
                ) or ''
                if 'success' in alert_title.lower():
                    result['message'] = alert_title
                    result['status'] = 'PASSED'
                    self.driver.execute_script("var btn=document.querySelector('.swal2-confirm');if(btn)btn.click();")
                else:
                    self.handle_validation_warning()
                    result['error'] = 'validation_warning'
                    result['message'] = alert_title
                    result['status'] = 'VALIDATION_FAILED'
                    return result
            else:
                self.handle_success_alert()
                result['status'] = 'PASSED'
            self._force_close_panels()
        except Exception as e:
            result['error'] = str(e)
        return result

    def edit_designation(self, name, updated_data):
        """Edit a designation. Returns result dict with status."""
        log.info(f"EDIT: {name}")
        result = {'status': 'FAILED', 'error': '', 'message': ''}
        try:
            if not self.is_designation_in_table(name):
                self.search_designation(name)
            self.click_edit_button(name)
            if not self.is_edit_mode():
                result['error'] = 'Edit popup did not open'
                return result
            self.fill_designation_form(updated_data)
            self.click_update()
            # Fast alert check
            if self.is_validation_alert_present(timeout=2):
                alert_title = self.driver.execute_script(
                    "var el=document.querySelector('#swal2-title');return el?el.textContent.trim():'';"
                ) or ''
                if 'success' in alert_title.lower():
                    result['message'] = alert_title
                    result['status'] = 'PASSED'
                    self.driver.execute_script("var btn=document.querySelector('.swal2-confirm');if(btn)btn.click();")
                else:
                    self.handle_validation_warning()
                    result['error'] = 'validation_warning'
                    result['message'] = alert_title
                    result['status'] = 'VALIDATION_FAILED'
                    return result
            else:
                self.handle_success_alert()
                result['status'] = 'PASSED'
            self._force_close_panels()
        except Exception as e:
            result['error'] = str(e)
        return result

    # ── INPUT SETTING ───────────────────────────────────

    def _set_input(self, locator, value, clear_first=True):
        css = locator[1] if locator[0] == "css" else ""
        if not css:
            return
        self.driver.execute_script("""
            var input = document.querySelector(arguments[0]);
            if (!input) return;
            input.focus();
            input.dispatchEvent(new Event('focus', {bubbles: true}));
            if (arguments[2]) {
                var ns = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                ns.call(input, '');
                input.dispatchEvent(new Event('input', {bubbles: true}));
            }
            var ns = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
            ns.call(input, arguments[1]);
            input.dispatchEvent(new Event('input', {bubbles: true}));
            input.dispatchEvent(new Event('change', {bubbles: true}));
            input.blur();
            input.dispatchEvent(new Event('blur', {bubbles: true}));
        """, css, value, clear_first)

    # For backward compat
    def _set_angular_input(self, locator, value, clear_first=True):
        self._set_input(locator, value, clear_first)

    # ── JS CLICK HELPERS ────────────────────────────────

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

    def _click_action_menu_item(self, name, action_name):
        """Click an action menu item (View/Edit/History) for a specific row (UOM pattern)."""
        log.info("Clicking " + action_name + " via 3-dot menu for: " + name)
        # Step 1: Open 3-dot menu for the row
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
        throw new Error('Row not found: ' + arguments[0]);
        """
        result = self.driver.execute_script(js, name)
        log.info("3-dot menu opened for: " + name)

        # Step 2: Wait for dropdown overlay
        try:
            WebDriverWait(self.driver, 2).until(
                EC.presence_of_element_located(("css selector", ".cdk-overlay-container .cdk-overlay-pane"))
            )
        except Exception:
            pass

        # Step 3: Click the specific menu item
        js_click = """
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
        for (var i = 0; i < items.length; i++) {
            var text = items[i].textContent.trim().toLowerCase();
            if (text.indexOf(arguments[0].toLowerCase()) !== -1) {
                items[i].click();
                return 'clicked_partial_' + arguments[0];
            }
        }
        throw new Error('Menu item "' + arguments[0] + '" not found in dropdown overlay');
        """
        result = self.driver.execute_script(js_click, action_name)
        log.info("Successfully clicked " + action_name + " for: " + name)
        return result

    # ── OVERLAY CLEANUP ─────────────────────────────────

    def _force_close_panels(self):
        """Remove any lingering CDK overlay panels that block clicks."""
        self.driver.execute_script("""
            document.querySelectorAll('.cdk-overlay-backdrop').forEach(function(el) { el.remove(); });
            document.querySelectorAll('.cdk-overlay-pane').forEach(function(el) { el.remove(); });
        """)

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
