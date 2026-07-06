from pages.base_playwright_page import BasePlaywrightPage


class ConstituentDocumentsPage(BasePlaywrightPage):
    URL = "https://rhythmerp.algorhythms.in/#/dynamic-screens/Constituent%20Documents/Constituent%20Documents"

    CIN_NO   = "xpath=//mat-form-field[.//mat-label[contains(.,'CIN No')]]//input"
    CIN_DATE = "xpath=//mat-form-field[.//mat-label[contains(.,'CIN Date')]]//input"

    ADD_ROW_BTN      = "xpath=//button[contains(.,'Add Row')]"
    DOCUMENTS_ROW    = "xpath=//app-dynamic-details//tbody/tr[contains(@mattooltip,'Click to edit row details')]"
    DOC_NAME_SELECT  = "xpath=//mat-form-field[.//mat-label[contains(.,'Document Name')]]//mat-select"

    NEXT_BTN   = "xpath=//div[contains(@class,'step-shell-footer')]//button[contains(.,'Next')]"
    SUBMIT_BTN = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Submit')]"
    CANCEL_BTN = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Cancel')]"
    SAVE_BTN   = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Save')]"
    SEARCH_INPUT = "#erpSearchInput"

    def _clear_overlays(self):
        self.page.evaluate(
            "document.querySelectorAll('.cdk-overlay-backdrop').forEach(el => el.remove())"
        )

    def _select_mat_option(self, selector):
        sel = self.page.locator(selector)
        sel.wait_for(state="visible", timeout=5000)
        sel.click(force=True)
        self.page.wait_for_selector(".mat-mdc-select-panel", timeout=5000)
        self.page.locator(".mat-mdc-select-panel mat-option").first.wait_for(state="visible", timeout=3000)
        self.page.evaluate("document.querySelector('.mat-mdc-select-panel mat-option')?.click()")
        self.page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=5000)
        self.page.wait_for_timeout(300)

    def _fill_date(self, selector, value):
        self.page.locator(selector).first.click(force=True, click_count=3)
        self.page.locator(selector).first.fill(value)
        self.page.keyboard.press("Tab")
        self.page.wait_for_timeout(200)

    def navigate_to_page(self):
        try:
            if "Constituent%20Documents" in self.page.url or "Constituent Documents" in self.page.url:
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
            self.page.click("button.erp-add-btn")
        except Exception:
            self.page.evaluate("""
                var btn = document.querySelector('button.erp-add-btn');
                if (btn) { btn.scrollIntoView({block:'center'}); btn.click(); }
            """)
        self.page.wait_for_selector(self.CIN_NO, timeout=5000)

    def _fill_one_row(self):
        row = self.page.locator("app-dynamic-details tbody tr.preview-row").first
        row.wait_for(state="visible", timeout=5000)
        self.page.wait_for_timeout(300)
        self._select_mat_option(self.DOC_NAME_SELECT)
        self._clear_overlays()

    def fill_document_row(self):
        self._fill_one_row()

    def fill_form(self, data):
        if data.get("cin_no"):
            self.page.locator(self.CIN_NO).first.click(force=True)
            self.page.locator(self.CIN_NO).first.fill(data["cin_no"])
            self.page.locator(self.CIN_NO).first.press("Tab")

        if data.get("cin_date"):
            self._fill_date(self.CIN_DATE, data["cin_date"])

        # Advance to Documents step
        next_btn = self.page.locator(self.NEXT_BTN)
        if next_btn.is_visible():
            next_btn.click()
            self.page.wait_for_timeout(800)

        self.fill_document_row()
        self._clear_overlays()

    def submit(self):
        self._clear_overlays()
        self.page.click(self.SUBMIT_BTN)

    def close_popup(self):
        self._clear_overlays()
        self.page.click(self.CANCEL_BTN)

    def handle_success_alert(self):
        try:
            self.page.wait_for_selector(".swal2-container", timeout=5000)
            title = (self.page.locator("#swal2-title").text_content() or "").strip().lower()
            body = (self.page.locator("#swal2-html-container").text_content() or "").strip()
            self.page.evaluate("document.querySelector('.swal2-confirm')?.click()")
            self.page.wait_for_selector(".swal2-container", state="hidden", timeout=3000)
            if "validation" in title or "failed" in title or "error" in title:
                labels = self.page.locator("mat-form-field.ng-invalid mat-label").all_text_contents()
                raise AssertionError(f"Validation failed — invalid fields: {labels} — body: '{body}'")
        except AssertionError:
            raise
        except Exception:
            pass
        try:
            if self.page.locator(self.CANCEL_BTN).is_visible():
                self._clear_overlays()
                self.page.locator(self.CANCEL_BTN).click()
                self.page.wait_for_timeout(500)
        except Exception:
            pass
        self.page.wait_for_selector("table#excel-table", timeout=8000)

    def handle_validation_alert(self):
        try:
            self.page.wait_for_selector(".swal2-container", timeout=5000)
            self.page.evaluate("document.querySelector('.swal2-confirm')?.click()")
            self.page.wait_for_selector(".swal2-container", state="hidden", timeout=3000)
        except Exception:
            pass
        self.page.wait_for_selector("table#excel-table", timeout=5000)

    def create_record(self, data):
        self.open_add_form()
        self.fill_form(data)
        self.submit()
        self.handle_success_alert()
        self.navigate_to_page()

    def search_document(self, cin_no):
        inp = self.page.locator(self.SEARCH_INPUT)
        if not inp.is_visible():
            self.page.evaluate("""
                var btn = document.querySelector('button[mattooltip="Search"]');
                if (btn) { btn.scrollIntoView({block:'center'}); btn.click(); }
            """)
            self.page.wait_for_timeout(800)
        inp.wait_for(state="visible", timeout=5000)
        inp.fill(cin_no)
        self.page.keyboard.press("Enter")
        self.page.wait_for_timeout(1500)

    def is_document_in_table(self, cin_no):
        for _ in range(10):
            rows = self.page.locator("table#excel-table tbody tr")
            for i in range(rows.count()):
                if cin_no in rows.nth(i).inner_text():
                    return True
            self.page.wait_for_timeout(300)
        return False

    def verify_document_exists(self, cin_no):
        assert self.is_document_in_table(cin_no), f"CIN '{cin_no}' not found in table"

    def _find_row_index(self, cin_no):
        rows = self.page.locator("table#excel-table tbody tr")
        for i in range(rows.count()):
            if cin_no in rows.nth(i).inner_text():
                return i
        raise AssertionError(f"CIN '{cin_no}' not found in table")

    def click_view_button(self, cin_no):
        self.click_row_action(self._find_row_index(cin_no), "View")

    def click_edit_button(self, cin_no):
        self.click_row_action(self._find_row_index(cin_no), "Edit")
        self.page.wait_for_selector(self.CIN_NO, timeout=5000)

    def update_cin_no(self, new_value):
        self.page.locator(self.CIN_NO).first.click(click_count=3)
        self.page.locator(self.CIN_NO).first.fill(new_value)

    def click_update(self):
        self.page.locator("xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Update')]").click()

    def click_history_button(self, cin_no):
        self.click_row_action(self._find_row_index(cin_no), "History")
        self.page.wait_for_timeout(1000)

    def verify_view_popup_read_only(self):
        buttons = self.page.locator(".popup-footer button")
        texts = [buttons.nth(i).text_content().strip() for i in range(buttons.count())]
        assert "Submit" not in texts and "Update" not in texts, \
            "View popup must not have Submit or Update"
