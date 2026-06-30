from pages.base_playwright_page import BasePlaywrightPage


class ErrorCodeMstPage(BasePlaywrightPage):
    URL = "https://rhythmerp.algorhythms.in/#/dynamic-screens/Error%20Code%20Mst"
    ADD_BTN = "button:has-text('Add Error Code Mst')"
    TYPE_TRIGGER = "mat-form-field:has(mat-label:has-text('Error Code Type')) .mat-mdc-select-trigger"
    CODE_INPUT = "input[name='Code']"
    DESC_INPUT = "input[name='Description']"
    SUBMIT = ".popup-footer button:has-text('Submit')"
    UPDATE = ".popup-footer button:has-text('Update')"
    CANCEL = ".popup-footer button:has-text('Cancel')"

    def navigate_to_page(self):
        self.page.reload()
        try:
            self.page.wait_for_selector("table#excel-table", timeout=15000)
        except Exception:
            self.page.goto(self.URL)
            self.page.wait_for_selector("table#excel-table", timeout=15000)

    def open_add_form(self):
        try:
            self.page.click(self.ADD_BTN, force=True)
        except Exception:
            self.page.evaluate("""
                var btn = document.querySelector('button.erp-add-btn');
                if (btn) { btn.scrollIntoView({block:'center'}); btn.click(); }
            """)
        self.page.wait_for_selector(self.CODE_INPUT, timeout=5000)

    def select_error_code_type(self):
        self.page.locator(self.TYPE_TRIGGER).click()
        self.page.wait_for_selector(".cdk-overlay-pane", timeout=5000)
        self.page.wait_for_timeout(400)
        opts = self.page.locator(".cdk-overlay-pane mat-option")
        opts.first.wait_for(state="visible", timeout=3000)
        text = opts.first.text_content().strip()
        opts.first.click(force=True)
        self.page.wait_for_timeout(500)
        return text

    def fill_form(self, data):
        self.select_error_code_type()
        if data.get("code"):
            self.page.fill(self.CODE_INPUT, data["code"])
        if data.get("description"):
            self.page.fill(self.DESC_INPUT, data["description"])

    def submit(self):
        self.page.evaluate("""
            document.querySelectorAll('.cdk-overlay-backdrop').forEach(function(el){el.click();});
        """)
        self.page.wait_for_timeout(300)
        self.page.click(self.SUBMIT, force=True)

    def click_update(self):
        self.page.evaluate("""
            document.querySelectorAll('.cdk-overlay-backdrop').forEach(function(el){el.click();});
        """)
        self.page.wait_for_timeout(300)
        self.page.click(self.UPDATE, force=True)

    def close_popup(self):
        self.page.evaluate("""
            document.querySelectorAll('.cdk-overlay-backdrop').forEach(function(el){el.click();});
        """)
        self.page.wait_for_timeout(300)
        self.page.click(self.CANCEL, force=True)

    def handle_success_alert(self):
        try:
            self.page.wait_for_selector(".swal2-container", timeout=5000)
            title = self.page.evaluate("document.querySelector('#swal2-title')?.textContent")
            if title and "success" not in title.lower() and "added" not in title.lower() and "updated" not in title.lower():
                self.page.evaluate("document.querySelector('.swal2-confirm')?.click()")
                self.page.wait_for_timeout(1000)
                return
            self.page.evaluate("document.querySelector('.swal2-confirm')?.click()")
            self.page.wait_for_selector(".swal2-container", state="hidden", timeout=5000)
        except Exception:
            pass
        try:
            self.page.wait_for_selector("table#excel-table", timeout=3000)
        except Exception:
            self.force_close_popup()
            self.page.wait_for_selector("table#excel-table", timeout=5000)

    def search_record(self, text):
        btn = self.page.locator("button.search-btn")
        try:
            btn.wait_for(state="visible", timeout=3000)
            btn.scroll_into_view_if_needed()
            btn.click()
        except Exception:
            self.page.evaluate("""
                var b = document.querySelector('button.search-btn') ||
                    document.querySelector('button[mattooltip="Search"]');
                if (b) { b.scrollIntoView({block:'center'}); b.click(); }
            """)
        self.page.wait_for_timeout(2000)
        try:
            inp = self.page.locator("input#erpSearchInput")
            inp.wait_for(state="visible", timeout=5000)
            inp.fill(text)
        except Exception:
            self.page.evaluate(f"""
                var inp = document.getElementById('erpSearchInput');
                if (inp) {{
                    var ns = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;
                    ns.call(inp, '{text}');
                    inp.dispatchEvent(new Event('input', {{bubbles:true}}));
                }}
            """)
        try:
            btn.click()
        except Exception:
            self.page.evaluate("""
                var b = document.querySelector('button.search-btn') ||
                    document.querySelector('button[mattooltip="Search"]');
                if (b) { b.click(); }
            """)
        self.page.wait_for_timeout(1000)

    def is_code_in_table(self, code):
        for _ in range(10):
            found = self.page.evaluate(f"""
                (() => {{
                    var rows = document.querySelectorAll('table#excel-table tbody tr');
                    for (var i = 0; i < rows.length; i++) {{
                        var cells = rows[i].querySelectorAll('td');
                        for (var j = 0; j < cells.length; j++) {{
                            if (cells[j].textContent.trim().indexOf('{code}') !== -1)
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

    def _find_row_index(self, code):
        for col in ["cdk-column-code", "cdk-column-error_code", "cdk-column-name"]:
            cells = self.page.locator(f"td.{col}")
            for i in range(cells.count()):
                if cells.nth(i).inner_text().strip() == code:
                    return i
        raise AssertionError(f"Error code '{code}' not found in table")

    def click_view_button(self, code):
        self.click_row_action(self._find_row_index(code), "View")

    def click_edit_button(self, code):
        self.click_row_action(self._find_row_index(code), "Edit")

    def click_history_button(self, code):
        self.click_row_action(self._find_row_index(code), "History")

    def update_code(self, new_code):
        self.page.fill(self.CODE_INPUT, new_code)
