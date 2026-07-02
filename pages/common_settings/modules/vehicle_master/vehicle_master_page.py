from pages.base_playwright_page import BasePlaywrightPage


class VehicleMasterPage(BasePlaywrightPage):
    URL = "https://rhythmerp.algorhythms.in/#/dynamic-screens/Vehicle%20Master"
    ADD_BTN = "button:has-text('Add Vehicle Master')"
    NAME_INPUT = "input[name='Name']"
    PRICE_INPUT = "input[name='Vehicle Price']"
    DESC_INPUT = "input[name='Description']"
    TYPE_SELECT = "mat-form-field:has(mat-label:has-text('Vehicle Type')) mat-select"
    FUEL_SELECT = "mat-form-field:has(mat-label:has-text('Fuel Type')) mat-select"
    SUBMIT = ".popup-footer button:has-text('Submit')"
    UPDATE = ".popup-footer button:has-text('Update')"
    CANCEL = ".popup-footer button:has-text('Cancel')"
    CHANGE_LOG = "app-dynamic-history table#excel-table tbody tr"

    def _clear_overlays(self):
        self.page.evaluate(
            "document.querySelectorAll('.cdk-overlay-backdrop').forEach(el => el.remove())"
        )

    def navigate_to_page(self):
        try:
            if self.URL.split("#")[1] in self.page.url:
                self.page.reload()
            else:
                self.page.goto(self.URL)
        except Exception:
            self.page.goto(self.URL)
        try:
            self.page.wait_for_selector("table#excel-table", timeout=10000)
        except Exception:
            self.page.reload()
            self.page.wait_for_selector("table#excel-table", timeout=15000)

    def open_add_form(self):
        try:
            self.page.click(self.ADD_BTN)
        except Exception:
            self.page.evaluate("""
                var btn = document.querySelector('button.erp-add-btn');
                if (btn) { btn.scrollIntoView({block:'center'}); btn.click(); }
            """)
        self.page.wait_for_selector(self.NAME_INPUT, timeout=5000)

    def _select_mat_option(self, select_selector):
        sel = self.page.locator(select_selector)
        sel.wait_for(state="visible", timeout=5000)
        sel.click()
        self.page.wait_for_selector(".mat-mdc-select-panel", timeout=5000)
        self.page.wait_for_selector(
            ".mat-mdc-select-panel mat-option",
            timeout=10000
        )
        self.page.wait_for_timeout(300)
        opts = self.page.locator(".mat-mdc-select-panel mat-option")
        text = opts.first.text_content().strip()
        opts.first.click(force=True)
        self.page.wait_for_timeout(500)
        self._clear_overlays()
        return text

    def fill_form(self, data):
        self.page.fill(self.NAME_INPUT, data["name"])
        price_input = self.page.locator(self.PRICE_INPUT)
        price_input.fill("")
        price_input.fill(str(data["price"]))
        if data.get("description"):
            self.page.fill(self.DESC_INPUT, data["description"])
        vehicle_type = self._select_mat_option(self.TYPE_SELECT)
        fuel_type = self._select_mat_option(self.FUEL_SELECT)
        return vehicle_type, fuel_type

    def submit(self):
        self._clear_overlays()
        self.page.click(self.SUBMIT)

    def click_update(self):
        self._clear_overlays()
        self.page.click(self.UPDATE)

    def close_popup(self):
        self._clear_overlays()
        self.page.click(self.CANCEL)

    def handle_success_alert(self):
        try:
            self.page.wait_for_selector(".swal2-container", timeout=4000)
            swal_text = (self.page.locator(".swal2-title").text_content() or "").strip().lower()
            if swal_text and any(w in swal_text for w in ("validation", "error", "failed", "warn")):
                self.page.evaluate("document.querySelector('.swal2-confirm')?.click()")
                self.page.wait_for_selector(".swal2-container", state="hidden", timeout=3000)
                return
            self.page.evaluate("document.querySelector('.swal2-confirm')?.click()")
            self.page.wait_for_selector(".swal2-container", state="hidden", timeout=3000)
        except Exception:
            pass
        try:
            if self.page.locator(self.CANCEL).is_visible():
                self._clear_overlays()
                self.page.click(self.CANCEL)
                self.page.wait_for_timeout(500)
        except Exception:
            pass
        self.page.wait_for_selector("table#excel-table", timeout=5000)

    def search_vehicle(self, name):
        self.page.evaluate("""
            var btn = document.querySelector('button[mattooltip="Search"]');
            if (btn) { btn.scrollIntoView({block:'center'}); btn.click(); }
        """)
        self.page.wait_for_timeout(1500)
        self.page.evaluate(f"""
            var inp = document.getElementById('erpSearchInput');
            if (inp) {{
                inp.style.display='block';
                inp.style.visibility='visible';
                inp.style.opacity='1';
                var nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;
                nativeSetter.call(inp, '{name}');
                inp.dispatchEvent(new Event('input', {{bubbles:true}}));
                inp.dispatchEvent(new KeyboardEvent('keydown', {{key:'Enter',code:'Enter',bubbles:true}}));
                inp.dispatchEvent(new KeyboardEvent('keyup', {{key:'Enter',code:'Enter',bubbles:true}}));
            }}
        """)
        self.page.wait_for_timeout(1000)

    def is_vehicle_in_table(self, name):
        for _ in range(10):
            found = self.page.evaluate(f"""
                (() => {{
                    var rows = document.querySelectorAll('table#excel-table tbody tr');
                    for (var i = 0; i < rows.length; i++) {{
                        var cells = rows[i].querySelectorAll('td');
                        for (var j = 0; j < cells.length; j++) {{
                            if (cells[j].textContent.trim().indexOf('{name}') !== -1)
                                return true;
                        }}
                    }}
                    return false;
                }})()
            """)
            if found:
                return True
            self.page.wait_for_timeout(300)
        return False

    def verify_vehicle_exists(self, name):
        assert self.is_vehicle_in_table(name), f"Vehicle '{name}' not found in table"

    def _find_row_index(self, name):
        for col in ["cdk-column-name", "cdk-column-vehicle_name"]:
            cells = self.page.locator(f"td.{col}")
            for i in range(cells.count()):
                if cells.nth(i).inner_text().strip() == name:
                    return i
        raise AssertionError(f"Vehicle '{name}' not found in table")

    def click_view_button(self, name):
        self.click_row_action(self._find_row_index(name), "View")

    def click_edit_button(self, name):
        self.click_row_action(self._find_row_index(name), "Edit")

    def click_history_button(self, name):
        self.click_row_action(self._find_row_index(name), "History")
        self.page.wait_for_selector("app-dynamic-history", timeout=5000)

    def update_name(self, new_name):
        name_input = self.page.locator(self.NAME_INPUT)
        name_input.click(click_count=3)
        name_input.fill(new_name)

    def verify_view_popup_read_only(self):
        buttons = self.page.locator(".popup-footer button")
        texts = [buttons.nth(i).text_content().strip() for i in range(buttons.count())]
        assert "Submit" not in texts and "Update" not in texts, \
            "View popup must not have Submit or Update"
