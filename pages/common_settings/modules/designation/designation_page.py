"""
designation_page.py — RhythmERP Common Settings > Designation (v2 OPTIMISED)

UOM Gold Standard patterns:
- hard_refresh() for fast page reset between tests
- Pure JS clicks (no multi-strategy fallbacks)
- offsetParent checks for visibility
- Fast polling (0.2s) instead of time.sleep()
- Short timeouts: 3s for alerts, 15s for page ready
- search_and_verify() combines search + existence check
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
        except Exception:
            log.warning("Page ready check timed out")

    # ── CREATE ──────────────────────────────────────────

    def open_add_form(self):
        log.info("Opening Add form")
        self.driver.execute_script("""
            var btn = document.querySelector('button.erp-add-btn');
            if (!btn) throw new Error('Add button not found');
            btn.scrollIntoView({block:'center'});
            btn.click();
        """)
        try:
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located(("css selector", "input[name='Name']"))
            )
        except Exception:
            pass

    def fill_designation_form(self, data):
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
        return self.driver.execute_script("""
            var cb = document.querySelector('.switch-wrapper input[type="checkbox"]');
            if (cb) return cb.checked;
            var toggle = document.querySelector('app-slide-toggle-v2');
            if (toggle) {
                var on = toggle.querySelector('.state-label.on');
                return (on && on.classList.contains('active')) ? true : false;
            }
            return false;
        """)

    def toggle_status(self):
        log.info("Toggling status")
        self.driver.execute_script("""
            var slider = document.querySelector('.switch-wrapper .slider');
            if (slider) { slider.click(); return; }
            var toggle = document.querySelector('app-slide-toggle-v2');
            if (toggle) {
                var s = toggle.querySelector('.slider');
                if (s) { s.click(); return; }
                toggle.click(); return;
            }
        """)

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

    # ── SEARCH ──────────────────────────────────────────

    def search_designation(self, name):
        log.info(f"Searching for: {name}")
        search_input = None
        try:
            el = self.driver.find_element("css selector", "input#erpSearchInput")
            if self.driver.execute_script("var r=arguments[0].getBoundingClientRect();return r.width>0&&r.height>0;", el):
                search_input = el
        except Exception:
            pass

        if search_input is None:
            try:
                self.driver.execute_script("""
                    var btn=document.querySelector('button.search-btn,button[mattooltip="Search"]');
                    if(btn){btn.scrollIntoView({block:'center'});btn.click();}
                """)
                search_input = WebDriverWait(self.driver, 5).until(
                    EC.visibility_of_element_located(("css selector", "input#erpSearchInput"))
                )
            except Exception:
                log.warning("Search input not visible")
                return False

        self.driver.execute_script("arguments[0].value='';", search_input)
        self.driver.execute_script("arguments[0].dispatchEvent(new Event('input',{bubbles:true}));", search_input)
        self.driver.execute_script("arguments[0].value=arguments[1];", search_input, name)
        search_input.click()
        for ev in ["input", "keyup", "change"]:
            self.driver.execute_script(f"arguments[0].dispatchEvent(new Event('{ev}',{{bubbles:true}}));", search_input)
        self.driver.execute_script("""
            var btn=document.querySelector('button.search-btn,button[mattooltip="Search"]');
            if(btn)btn.click();
        """)
        try:
            WebDriverWait(self.driver, 5).until(
                lambda d: d.find_elements("css selector", "table#excel-table tbody tr")
            )
        except Exception:
            pass
        return self.is_designation_in_table(name)

    def verify_designation_exists(self, name):
        log.info(f"Verifying '{name}' exists in table")
        end = time.monotonic() + 5
        while time.monotonic() < end:
            try:
                for row in self.driver.find_elements("css selector", "table#excel-table tbody tr"):
                    for cell in row.find_elements("css selector", "td"):
                        if name in cell.text.strip():
                            return True
            except Exception:
                pass
            time.sleep(0.3)
        raise AssertionError(f"Designation '{name}' NOT found in table")

    def search_and_verify(self, name):
        self.search_designation(name)
        return self.verify_designation_exists(name)

    def is_designation_in_table(self, name):
        try:
            for row in self.driver.find_elements("css selector", "table#excel-table tbody tr"):
                for cell in row.find_elements("css selector", "td"):
                    if name in cell.text.strip():
                        return True
        except Exception:
            pass
        return False

    def clear_search(self):
        self.hard_refresh()

    def click_refresh(self):
        self.driver.execute_script("""
            var btns=document.querySelectorAll('button[mattooltip="Refresh"]');
            for(var i=0;i<btns.length;i++){if(btns[i].offsetParent!==null){btns[i].click();return;}}
            var icons=document.querySelectorAll('button.mat-mdc-mini-fab mat-icon');
            for(var i=0;i<icons.length;i++){if(icons[i].textContent.trim().toLowerCase()==='refresh'){icons[i].closest('button').click();return;}}
        """)

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
        disabled = self.driver.execute_script(
            "var el=document.querySelector('input[name=\"Name\"]');return el?el.disabled:false;"
        )
        has_submit = self.driver.execute_script(
            "var btns=document.querySelectorAll('.popup-footer button');for(var i=0;i<btns.length;i++){if(btns[i].textContent.trim()==='Submit')return true;}return false;"
        )
        has_update = self.driver.execute_script(
            "var btns=document.querySelectorAll('.popup-footer button');for(var i=0;i<btns.length;i++){if(btns[i].textContent.trim()==='Update')return true;}return false;"
        )
        assert disabled, "Name should be disabled in View"
        assert not has_submit, "Submit should NOT be in View"
        assert not has_update, "Update should NOT be in View"

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
            "var btns=document.querySelectorAll('.popup-footer button');for(var i=0;i<btns.length;i++){if(btns[i].textContent.trim()==='Update'&&btns[i].offsetParent!==null)return true;}return false;"
        )

    def click_update(self):
        log.info("Clicking Update")
        self._js_click_popup_button('Update')

    # ── HISTORY ─────────────────────────────────────────

    def click_history_button(self, name):
        self._click_action_menu_item(name, "History")
        try:
            WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located(("css selector", "app-dynamic-history,.big-model table,.popup-content table"))
            )
        except Exception:
            pass

    def is_history_popup_open(self):
        return self.driver.execute_script("""
            var h3s=document.querySelectorAll('h3.popup-title,.big-model h3,.popup-content h3,app-dynamic-history .tbl-title h2');
            for(var i=0;i<h3s.length;i++){if(h3s[i].offsetParent!==null&&h3s[i].textContent.toLowerCase().indexOf('history')!==-1)return true;}
            return false;
        """)

    def get_history_row_count(self):
        try:
            return len(self.driver.find_elements("css selector",
                "app-dynamic-history table#excel-table tbody tr,.big-model table tbody tr,.popup-content table tbody tr"))
        except Exception:
            return 0

    def get_history_data(self):
        data = []
        try:
            for row in self.driver.find_elements("css selector",
                "app-dynamic-history table#excel-table tbody tr,.big-model table tbody tr,.popup-content table tbody tr"):
                cells = row.find_elements("tag name", "td")
                data.append({f'col_{i}': c.text.strip() for i, c in enumerate(cells)})
        except Exception:
            pass
        return data

    def close_history_popup(self):
        log.info("Closing History popup")
        self.driver.execute_script("""
            var footers=document.querySelectorAll('.popup-footer');
            for(var i=0;i<footers.length;i++){var btns=footers[i].querySelectorAll('button');
            for(var j=0;j<btns.length;j++){if(btns[j].textContent.indexOf('Cancel')!==-1){btns[j].click();return;}}}
        """)

    # ── POPUP CLOSE ─────────────────────────────────────

    def cancel(self):
        log.info("Closing popup via Cancel")
        self.driver.execute_script("""
            var footers=document.querySelectorAll('.popup-footer');
            for(var i=0;i<footers.length;i++){var btns=footers[i].querySelectorAll('button');
            for(var j=0;j<btns.length;j++){if(btns[j].textContent.indexOf('Cancel')!==-1){btns[j].click();return;}}}
        """)

    def close_popup(self):
        log.info("Closing popup")
        self.driver.execute_script("""
            var footers=document.querySelectorAll('.popup-footer');
            for(var i=0;i<footers.length;i++){var btns=footers[i].querySelectorAll('button');
            for(var j=0;j<btns.length;j++){if(btns[j].textContent.indexOf('Cancel')!==-1){btns[j].click();return;}}}
            var icons=document.querySelectorAll('.popup-header button mat-icon,.big-model button mat-icon');
            for(var i=0;i<icons.length;i++){if(icons[i].textContent.trim().toLowerCase()==='close'){var btn=icons[i].closest('button');if(btn){btn.click();return;}}}
        """)

    def _is_form_popup_open(self):
        return self.driver.execute_script(
            "var els=document.querySelectorAll('.big-model');for(var i=0;i<els.length;i++){if(els[i].offsetParent!==null)return true;}return false;"
        )

    def is_add_form_open(self):
        return self.driver.execute_script(
            "var el=document.querySelector('input[name=\"Name\"]');return el&&el.offsetParent!==null;"
        )

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
        log.info("Handling success alert")
        try:
            WebDriverWait(self.driver, 3).until(
                EC.visibility_of_element_located(("css selector", ".swal2-container"))
            )
            title = self.driver.execute_script(
                "var el=document.querySelector('#swal2-title');return el?el.textContent.trim():'';"
            ) or ''
            self.driver.execute_script("var btn=document.querySelector('.swal2-confirm');if(btn)btn.click();")
            try:
                WebDriverWait(self.driver, 2).until(
                    EC.invisibility_of_element_located(("css selector", ".swal2-container"))
                )
            except Exception:
                pass
            return title
        except Exception:
            return ''

    def handle_validation_warning(self):
        log.info("Handling validation warning")
        try:
            self.driver.find_element("css selector", ".swal2-popup")
            title = self.driver.execute_script(
                "var el=document.querySelector('#swal2-title');return el?el.textContent.trim():'';"
            ) or ''
            self.driver.execute_script("var btn=document.querySelector('.swal2-confirm');if(btn)btn.click();")
            try:
                WebDriverWait(self.driver, 2).until(
                    EC.invisibility_of_element_located(("css selector", ".swal2-popup"))
                )
            except Exception:
                pass
            return title
        except Exception:
            return ''

    def is_validation_alert_present(self, timeout=3):
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            try:
                if self.driver.execute_script(
                    "var el=document.querySelector('.swal2-popup.swal2-icon-warning,.swal2-popup.swal2-icon-error');"
                    "return el&&el.offsetParent!==null;"
                ):
                    return True
            except Exception:
                pass
            time.sleep(0.2)
        return False

    # ── MAT ERROR ───────────────────────────────────────

    def get_mat_error_text(self, field_locator=None):
        try:
            if field_locator:
                css = field_locator[1] if field_locator[0] == "css" else ""
                return self.driver.execute_script("""
                    var input=document.querySelector(arguments[0]);if(!input)return '';
                    var current=input;
                    for(var s=0;s<20;s++){var errors=current.querySelectorAll('mat-error');
                    if(errors.length>0){var t=[];for(var i=0;i<errors.length;i++){if(errors[i].textContent.trim())t.push(errors[i].textContent.trim());}return t.join(' | ');}
                    current=current.parentElement;if(!current||current===document.body)break;}return '';
                """, css) or ""
            return self.driver.execute_script("""
                var errors=[];var matErrors=document.querySelectorAll('.big-model mat-error,.edit_pop_up mat-error');
                matErrors.forEach(function(el){if(el.offsetParent!==null){var t=el.textContent.trim();if(t)errors.push(t);}});return errors;
            """) or []
        except Exception:
            return ""

    def has_field_error(self, field_label):
        css = {"Name": "input[name='Name']", "Description": "input[name='Description']"}.get(field_label, "")
        if not css:
            return False
        return self.driver.execute_script("""
            var input=document.querySelector(arguments[0]);if(!input)return false;
            var current=input;var invalid=['mat-mdc-form-field-invalid','ng-invalid','cdk-text-field-invalid'];
            for(var s=0;s<20;s++){var cls=current.className||'';
            for(var i=0;i<invalid.length;i++){if(cls.indexOf(invalid[i])!==-1)return true;}
            current=current.parentElement;if(!current||current===document.body)break;}return false;
        """, css)

    def has_name_invalid_class(self):
        return self.driver.execute_script("""
            var input=document.querySelector('input[name="Name"]');if(!input)return false;
            var cls=input.className||'';if(cls.indexOf('ng-invalid')!==-1&&cls.indexOf('ng-touched')!==-1)return true;
            var v=input.value||'';if(v&&cls.indexOf('ng-touched')!==-1){if(v.trim()==='')return true;
            if(!/^[a-zA-Z\\s\\.\\,\\-\\(\\)]+$/.test(v))return true;}return false;
        """)

    # ── ONE-CALL FLOWS ──────────────────────────────────

    def create_designation(self, data):
        log.info(f"CREATE: {data.get('name','?')}")
        result = {'status': 'FAILED', 'error': '', 'message': '', 'data': data}
        try:
            self.open_add_form()
            self.fill_designation_form(data)
            self.submit()
            time.sleep(1)
            if self.is_validation_alert_present(timeout=3):
                alert_text = self.driver.execute_script(
                    "var el=document.querySelector('#swal2-title');return el?el.textContent.trim():'';"
                ) or ''
                if 'success' in alert_text.lower():
                    result['message'] = alert_text
                    result['status'] = 'PASSED'
                    self.driver.execute_script("var btn=document.querySelector('.swal2-confirm');if(btn)btn.click();")
                else:
                    warning = self.handle_validation_warning()
                    result['error'] = 'validation_warning'
                    result['message'] = warning if isinstance(warning, str) else alert_text
                    result['status'] = 'VALIDATION_FAILED'
                    return result
            else:
                msg = self.handle_success_alert()
                result['message'] = msg
                result['status'] = 'PASSED' if msg else 'UNKNOWN'
            self._force_close_panels()
        except Exception as e:
            result['error'] = str(e)
        return result

    def edit_designation(self, name, updated_data):
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
            time.sleep(1)
            if self.is_validation_alert_present(timeout=3):
                alert_text = self.driver.execute_script(
                    "var el=document.querySelector('#swal2-title');return el?el.textContent.trim():'';"
                ) or ''
                if 'success' in alert_text.lower():
                    result['message'] = alert_text
                    result['status'] = 'PASSED'
                    self.driver.execute_script("var btn=document.querySelector('.swal2-confirm');if(btn)btn.click();")
                else:
                    warning = self.handle_validation_warning()
                    result['error'] = 'validation_warning'
                    result['message'] = warning if isinstance(warning, str) else alert_text
                    result['status'] = 'VALIDATION_FAILED'
                    return result
            else:
                msg = self.handle_success_alert()
                result['message'] = msg
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
            var input=document.querySelector(arguments[0]);if(!input)return;
            input.focus();input.dispatchEvent(new Event('focus',{bubbles:true}));
            if(arguments[2]){var ns=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;
            ns.call(input,'');input.dispatchEvent(new Event('input',{bubbles:true}));}
            var ns=Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;
            ns.call(input,arguments[1]);input.dispatchEvent(new Event('input',{bubbles:true}));
            input.dispatchEvent(new Event('change',{bubbles:true}));input.blur();
            input.dispatchEvent(new Event('blur',{bubbles:true}));
        """, css, value, clear_first)

    # For backward compat with test calls to _set_angular_input
    def _set_angular_input(self, locator, value, clear_first=True):
        self._set_input(locator, value, clear_first)

    # ── JS CLICK HELPERS ────────────────────────────────

    def _js_click_popup_button(self, button_text):
        try:
            self.driver.execute_script("""
                var footers=document.querySelectorAll('.popup-footer');
                for(var i=0;i<footers.length;i++){var btns=footers[i].querySelectorAll('button');
                for(var j=0;j<btns.length;j++){if(btns[j].textContent.trim().indexOf(arguments[0])!==-1){btns[j].click();return;}}}
            """, button_text)
        except Exception as e:
            log.warning(f"JS click {button_text} failed: {e}")

    def _click_action_menu_item(self, name, action_name):
        log.info(f"Clicking {action_name} for: {name}")
        self.driver.execute_script("""
            var table=document.querySelector('table#excel-table');if(!table)throw new Error('Table not found');
            var rows=table.querySelectorAll('tbody tr');
            for(var i=0;i<rows.length;i++){var nc=rows[i].querySelector('td.cdk-column-name,td.mat-column-name');
            if(nc&&nc.textContent.trim().toLowerCase().indexOf(arguments[0].toLowerCase())!==-1){
            var mb=rows[i].querySelector('td.cdk-column-actions button,.erp-row-trigger');
            if(mb){mb.scrollIntoView({block:'center'});mb.click();return;}}}
            throw new Error('Row not found: '+arguments[0]);
        """, name)
        try:
            WebDriverWait(self.driver, 2).until(
                EC.presence_of_element_located(("css selector", ".cdk-overlay-container .cdk-overlay-pane"))
            )
        except Exception:
            pass
        self.driver.execute_script("""
            var overlay=document.querySelector('.cdk-overlay-container');if(!overlay)throw new Error('No overlay');
            var items=overlay.querySelectorAll('button,span,div');
            for(var i=0;i<items.length;i++){if(items[i].textContent.trim()===arguments[0]){items[i].click();return;}}
            for(var i=0;i<items.length;i++){if(items[i].textContent.trim().toLowerCase().indexOf(arguments[0].toLowerCase())!==-1){items[i].click();return;}}
            throw new Error('Menu item not found: '+arguments[0]);
        """, action_name)

    # ── OVERLAY CLEANUP ─────────────────────────────────

    def _force_close_panels(self):
        self.driver.execute_script("""
            document.querySelectorAll('.swal2-container').forEach(function(el){el.remove();});
            document.querySelectorAll('.cdk-overlay-backdrop').forEach(function(el){el.remove();});
        """)

    def force_close_form_popup(self):
        self.driver.execute_script("""
            var p=document.querySelector('div.edit_pop_up');if(!p)return;
            var c=p.querySelector('button[mat-icon-button] mat-icon');if(!c)return;
            var btn=c.closest('button');if(btn)btn.click();
        """)
