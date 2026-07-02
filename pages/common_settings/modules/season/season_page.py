import os
from pages.base_playwright_page import BasePlaywrightPage


class SeasonPage(BasePlaywrightPage):
    URL = "https://rhythmerp.algorhythms.in/#/dynamic-screens/Season"
    ADD_BTN = "button:has-text('Add Season')"
    NAME_INPUT = "mat-form-field:has(mat-label:has-text('Name')) input"
    DESC_INPUT = "mat-form-field:has(mat-label:has-text('Description')) input"
    SUBMIT = ".popup-footer button:has-text('Submit')"
    UPDATE = ".popup-footer button:has-text('Update')"
    CANCEL = ".popup-footer button:has-text('Cancel')"
    CHANGE_LOG = "app-dynamic-history table#excel-table tbody tr"

    def navigate_to_page(self):
        try:
            if "Season" in self.page.url:
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
        self.page.click(self.ADD_BTN)
        self.page.wait_for_selector(self.NAME_INPUT, timeout=5000)

    def fill_form(self, data):
        self.page.fill(self.NAME_INPUT, data["Name"])
        if data.get("Description"):
            self.page.fill(self.DESC_INPUT, data["Description"])

    def _clear_overlays(self):
        self.page.evaluate(
            "document.querySelectorAll('.cdk-overlay-backdrop').forEach(el => el.remove())"
        )

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

    def search_season(self, name):
        self.page.evaluate("""
            var btn = document.querySelector('button[mattooltip="Search"]');
            if (btn) { btn.scrollIntoView({block:'center'}); btn.click(); }
        """)
        self.page.wait_for_timeout(1500)
        self.page.evaluate("""
            var inp = document.getElementById('erpSearchInput');
            if (inp) { inp.style.display='block'; inp.style.visibility='visible'; inp.style.opacity='1'; }
        """)
        self.page.locator("input#erpSearchInput").fill(name)
        self.page.evaluate("""
            var inp = document.getElementById('erpSearchInput');
            if (inp) {
                var nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype,'value').set;
                nativeSetter.call(inp, inp.value);
                inp.dispatchEvent(new Event('input', {bubbles:true}));
                inp.dispatchEvent(new KeyboardEvent('keydown', {key:'Enter',code:'Enter',bubbles:true}));
                inp.dispatchEvent(new KeyboardEvent('keyup', {key:'Enter',code:'Enter',bubbles:true}));
            }
        """)
        self.page.wait_for_timeout(1000)

    def is_season_in_table(self, name):
        return self.page.locator(
            f"table#excel-table td.cdk-column-name:has-text('{name}')"
        ).count() > 0

    def verify_season_exists(self, name):
        assert self.is_season_in_table(name), f"Season '{name}' not found in table"

    def _find_row_index(self, name):
        cells = self.page.locator("td.cdk-column-name")
        for i in range(cells.count()):
            if cells.nth(i).inner_text().strip() == name:
                return i
        raise AssertionError(f"Season '{name}' not found in table")

    def click_view_button(self, name):
        self.click_row_action(self._find_row_index(name), "View")

    def click_edit_button(self, name):
        self.click_row_action(self._find_row_index(name), "Edit")

    def click_history_button(self, name):
        self.click_row_action(self._find_row_index(name), "History")
        self.page.wait_for_selector("app-dynamic-history", timeout=5000)

    def update_name(self, new_name):
        self.page.fill(self.NAME_INPUT, new_name)

    def verify_view_popup_read_only(self):
        buttons = self.page.locator(".popup-footer button")
        texts = [buttons.nth(i).text_content().strip() for i in range(buttons.count())]
        assert "Submit" not in texts and "Update" not in texts, \
            "View popup must not have Submit or Update"
