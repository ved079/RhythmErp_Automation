import os
from pages.base_playwright_page import BasePlaywrightPage


class HsnSacPage(BasePlaywrightPage):
    URL = "https://rhythmerp.algorhythms.in/#/dynamic-screens/HSN%20SAC"
    ADD_BTN = "button:has-text('Add HSN SAC')"

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
        # Close any open popup if table not immediately visible
        try:
            self.page.wait_for_selector("table#excel-table", timeout=3000)
        except Exception:
            self.force_close_popup()
            self.page.wait_for_selector("table#excel-table", timeout=5000)
    NUMBER_INPUT = "mat-form-field:has(mat-label:has-text('HSN SAC Number')) input"
    DESC_INPUT = "mat-form-field:has(mat-label:has-text('HSN SAC Description')) input"
    SUBMIT = ".popup-footer button:has-text('Submit')"
    UPDATE = ".popup-footer button:has-text('Update')"
    CANCEL = ".popup-footer button:has-text('Cancel')"
    CHANGE_LOG = "app-dynamic-history table#excel-table tbody tr"

    def navigate_to_page(self):
        self.page.goto(self.URL)
        try:
            self.page.wait_for_selector("table#excel-table", timeout=10000)
        except Exception:
            self.page.reload()
            self.page.wait_for_selector("table#excel-table", timeout=15000)

    def open_add_form(self):
        try:
            self.page.click(self.ADD_BTN, force=True)
        except Exception:
            self.page.evaluate("""
                var btn = document.querySelector('button.erp-add-btn');
                if (btn) { btn.scrollIntoView({block:'center'}); btn.click(); }
            """)
        self.page.wait_for_selector(self.NUMBER_INPUT, timeout=5000)

    def select_hsn_sac_type(self, option_text):
        self.page.evaluate("""
            (() => {
                var backdrops = document.querySelectorAll('.cdk-overlay-backdrop');
                for (var i = 0; i < backdrops.length; i++) {
                    backdrops[i].click();
                }
            })()
        """)
        self.page.wait_for_timeout(300)
        trigger_sel = "mat-form-field:has(mat-label:has-text('HSN SAC Type')) .mat-mdc-select-trigger"
        self.page.locator(trigger_sel).click()
        self.page.wait_for_selector(".cdk-overlay-pane", timeout=5000)
        self.page.wait_for_timeout(400)
        option_sel = ".cdk-overlay-pane mat-option:has-text('" + option_text + "')"
        self.page.locator(option_sel).last.click()
        self.page.wait_for_timeout(500)
        return option_text

    def fill_form(self, data):
        if data.get("hsn_sac_number"):
            self.page.fill(self.NUMBER_INPUT, data["hsn_sac_number"])
        if data.get("hsn_sac_type"):
            self.select_hsn_sac_type(data["hsn_sac_type"])
        if data.get("hsn_sac_description"):
            self.page.fill(self.DESC_INPUT, data["hsn_sac_description"])

    def submit(self):
        self.page.click(self.SUBMIT, force=True)

    def click_update(self):
        self.page.click(self.UPDATE, force=True)

    def close_popup(self):
        self.page.click(self.CANCEL, force=True)

    def search_hsn_sac(self, text):
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
        self.page.wait_for_timeout(2000)

    def is_hsn_in_table(self, hsn_no):
        for _ in range(10):
            found = self.page.evaluate(f"""
                (() => {{
                    var rows = document.querySelectorAll('table#excel-table tbody tr');
                    for (var i = 0; i < rows.length; i++) {{
                        var cells = rows[i].querySelectorAll('td');
                        for (var j = 0; j < cells.length; j++) {{
                            if (cells[j].textContent.trim().indexOf('{hsn_no}') !== -1)
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

    def verify_hsn_exists(self, hsn_no):
        assert self.is_hsn_in_table(hsn_no), f"HSN SAC '{hsn_no}' not found in table"

    def _find_row_index(self, hsn_no):
        for col in ["cdk-column-hsn_sac_no", "cdk-column-hsn_sac_number", "cdk-column-name"]:
            cells = self.page.locator(f"td.{col}")
            for i in range(cells.count()):
                if cells.nth(i).inner_text().strip() == hsn_no:
                    return i
        raise AssertionError(f"HSN SAC '{hsn_no}' not found in table")

    def click_view_button(self, hsn_no):
        self.click_row_action(self._find_row_index(hsn_no), "View")

    def click_edit_button(self, hsn_no):
        self.click_row_action(self._find_row_index(hsn_no), "Edit")

    def click_history_button(self, hsn_no):
        self.click_row_action(self._find_row_index(hsn_no), "History")
        self.page.wait_for_selector("app-dynamic-history", timeout=5000)

    def update_number(self, new_number):
        self.page.fill(self.NUMBER_INPUT, new_number)

    def verify_view_popup_read_only(self):
        buttons = self.page.locator(".popup-footer button")
        texts = [buttons.nth(i).text_content().strip() for i in range(buttons.count())]
        assert "Submit" not in texts and "Update" not in texts, \
            "View popup must not have Submit or Update"
