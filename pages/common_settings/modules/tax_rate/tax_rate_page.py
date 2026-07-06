from pages.base_playwright_page import BasePlaywrightPage


class TaxRatePage(BasePlaywrightPage):
    URL = "https://rhythmerp.algorhythms.in/#/dynamic-screens/Tax%20Rate"
    ADD_BTN = "button.erp-add-btn"
    NAME_INPUT = "input[name='Revision Status']"
    TYPE_SELECT = "mat-form-field:has(mat-label:has-text('Tax Type')) mat-select"
    AUTHORITY_SELECT = "mat-form-field:has(mat-label:has-text('Tax Authority')) mat-select"
    FROM_DATE = "mat-form-field:has(mat-label:has-text('From Date')) input.mat-mdc-input-element"
    TO_DATE = "mat-form-field:has(mat-label:has-text('To Date')) input.mat-mdc-input-element"
    SUBMIT = ".popup-footer button:has-text('Submit')"
    CANCEL = ".popup-footer button:has-text('Cancel')"
    CHANGE_LOG = "app-dynamic-history table#excel-table tbody tr"

    def _clear_overlays(self):
        self.page.evaluate(
            "document.querySelectorAll('.cdk-overlay-backdrop').forEach(el => el.remove())"
        )

    def navigate_to_page(self):
        try:
            if "Tax%20Rate" in self.page.url or "Tax Rate" in self.page.url:
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
        self.page.evaluate("""
            var btn = document.querySelector('button.erp-add-btn');
            if (!btn) {
                var icons = document.querySelectorAll('app-custom-header mat-icon, app-custom-header i.material-icons');
                for (var i = 0; i < icons.length; i++) {
                    if (icons[i].textContent.trim() === 'add') {
                        btn = icons[i].closest('button'); break;
                    }
                }
            }
            if (btn) { btn.scrollIntoView({block:'center'}); btn.click(); }
        """)
        self.page.wait_for_selector("div.edit_pop_up", timeout=10000)

    def _select_mat_option(self, select_selector):
        sel = self.page.locator(select_selector)
        sel.wait_for(state="visible", timeout=5000)
        sel.click()
        self.page.wait_for_selector(".mat-mdc-select-panel", timeout=5000)
        opts = self.page.locator(".mat-mdc-select-panel mat-option")
        opts.first.wait_for(state="visible", timeout=3000)
        text = opts.first.text_content().strip()
        opts.first.click(force=True)
        self.page.wait_for_timeout(300)
        self._clear_overlays()
        return text

    def fill_date(self, selector, value):
        inp = self.page.locator(selector)
        inp.click(click_count=3)
        inp.fill(value)
        self.page.keyboard.press("Tab")

    def fill_header(self, data):
        self._select_mat_option(self.TYPE_SELECT)
        self._select_mat_option(self.AUTHORITY_SELECT)
        self.fill_date(self.FROM_DATE, data.get("from_date", "01/04/2025"))
        self.fill_date(self.TO_DATE, data.get("to_date", "31/03/2026"))
        name = data.get("tax_rate_name", "Active")
        self.page.fill(self.NAME_INPUT, name)

    def submit(self):
        self._clear_overlays()
        self.page.evaluate("""
            var btns = document.querySelectorAll('.popup-footer button');
            var found = false;
            for (var i = 0; i < btns.length; i++) {
                if (btns[i].textContent.trim() === 'Submit') {
                    btns[i].click(); found = true; break;
                }
            }
            if (!found && btns.length > 0) {
                btns[btns.length - 1].click();
            }
        """)

    def close_popup(self):
        self._clear_overlays()
        self.page.evaluate("""
            var btns = document.querySelectorAll('.popup-footer button');
            for (var i = 0; i < btns.length; i++) {
                var t = btns[i].textContent.trim();
                if (t === 'Cancel' || t.indexOf('Cancel') >= 0) {
                    btns[i].click(); break;
                }
            }
        """)

    def handle_success_alert(self):
        try:
            self.page.wait_for_selector(".swal2-container", timeout=5000)
            title = (self.page.locator("#swal2-title").text_content() or "").strip().lower()
            body = (self.page.locator("#swal2-html-container").text_content() or "").strip()
            self.page.evaluate("document.querySelector('.swal2-confirm')?.click()")
            self.page.wait_for_selector(".swal2-container", state="hidden", timeout=3000)
            if "validation" in title or "failed" in title or "error" in title:
                body = (self.page.locator("#swal2-html-container").text_content() or "").strip()
                raise AssertionError(f"Expected success but got alert: '{title}' — body: '{body}'")
        except AssertionError:
            raise
        except Exception:
            pass
        try:
            if self.page.locator(self.CANCEL).is_visible():
                self._clear_overlays()
                self.page.click(self.CANCEL)
                self.page.wait_for_timeout(500)
        except Exception:
            pass
        self.page.wait_for_selector("table#excel-table", timeout=8000)

    def fill_sub_table_row(self):
        """Fill HSN Number + Tax Rate inline in the preview row (no sub-popup)."""
        row = self.page.locator("tr.preview-row, tr.cdk-drag").first
        row.wait_for(state="visible", timeout=8000)
        # Click the HSN mat-select inside the row
        hsn_sel = row.locator("mat-select").first
        hsn_sel.click(force=True)
        try:
            self.page.wait_for_selector(".mat-mdc-select-panel", timeout=3000)
        except Exception:
            self._clear_overlays()
            hsn_sel.click(force=True)
            self.page.wait_for_selector(".mat-mdc-select-panel", timeout=5000)
        self.page.locator(".mat-mdc-select-panel mat-option").first.click(force=True)
        self.page.wait_for_timeout(400)
        self._clear_overlays()
        # Fill Tax Rate input inline
        tax_input = row.locator("input").first
        tax_input.click()
        tax_input.fill("18")
        self.page.wait_for_timeout(300)

    def create_record(self, data):
        self.open_add_form()
        self.fill_header(data)
        self.page.wait_for_timeout(1500)
        self.fill_sub_table_row()
        self.submit()
        self.handle_success_alert()
        self.navigate_to_page()

    def go_to_first_page(self):
        try:
            first_btn = self.page.locator("xpath=//button[.//i[contains(@class,'material-icons')][normalize-space()='first_page']]")
            if first_btn.count() > 0 and first_btn.is_enabled():
                first_btn.click()
                self.page.wait_for_timeout(800)
        except Exception:
            pass

    def refresh_table(self):
        try:
            self.page.locator("xpath=//button[@mattooltip='Refresh']").click()
            self.page.wait_for_selector("table#excel-table", timeout=8000)
            self.page.wait_for_timeout(500)
        except Exception:
            pass

    def search_tax_rate(self, name):
        inp = self.page.locator("input.erp-search-input, input[placeholder='Search']").first
        if not inp.is_visible():
            self.page.evaluate("""
                var btn = document.querySelector('button[mattooltip="Search"]');
                if (btn) { btn.scrollIntoView({block:'center'}); btn.click(); }
            """)
            self.page.wait_for_timeout(800)
        inp.wait_for(state="visible", timeout=5000)
        inp.click()
        inp.fill("")
        inp.fill(name)
        self.page.keyboard.press("Enter")
        self.page.wait_for_timeout(1500)

    def is_tax_rate_in_table(self, name):
        for _ in range(10):
            rows = self.page.locator("table#excel-table tbody tr")
            for i in range(rows.count()):
                if name in rows.nth(i).inner_text():
                    return True
            self.page.wait_for_timeout(300)
        return False

    def verify_tax_rate_exists(self, name):
        assert self.is_tax_rate_in_table(name), f"Tax Rate '{name}' not found in table"

    def _find_row_index(self, name):
        rows = self.page.locator("table#excel-table tbody tr")
        for i in range(rows.count()):
            row_text = rows.nth(i).inner_text()
            if name in row_text:
                return i
        raise AssertionError(f"Tax Rate '{name}' not found in table")

    def click_view_button(self, name):
        self.click_row_action(self._find_row_index(name), "View")

    def click_history_button(self, name):
        self.click_row_action(self._find_row_index(name), "History")
        self.page.wait_for_selector("app-dynamic-history", timeout=5000)

    def verify_view_popup_read_only(self):
        buttons = self.page.locator(".popup-footer button")
        texts = [buttons.nth(i).text_content().strip() for i in range(buttons.count())]
        assert "Submit" not in texts and "Update" not in texts, \
            "View popup must not have Submit or Update"
