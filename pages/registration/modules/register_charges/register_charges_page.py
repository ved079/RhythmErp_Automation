from pages.base_playwright_page import BasePlaywrightPage


class RegisterChargesPage(BasePlaywrightPage):
    URL = "https://rhythmerp.algorhythms.in/#/dynamic-screens/Register%20Charges/Register%20Charges"

    DATE_OF_CREATION               = "xpath=//mat-form-field[.//mat-label[contains(.,'Date of Creation')]]//input"
    DATE_OF_MODIFICATION           = "xpath=//mat-form-field[.//mat-label[contains(.,'Date of Modification')]]//input"
    CHARGE_ID_ROC                  = "xpath=//mat-form-field[.//mat-label[contains(.,'Charge ID (ROC)')]]//input"
    DESCRIPTION_OF_ASSETS_PROPERTY = "xpath=//mat-form-field[.//mat-label[contains(.,'Description of Assets/Property')]]//input"
    AMOUNT_SECURED                 = "xpath=//mat-form-field[.//mat-label[contains(.,'Amount Secured')]]//input"
    CHARGE_HOLDER_DETAILS          = "xpath=//mat-form-field[.//mat-label[contains(.,'Charge Holder Details')]]//input"
    DATE_OF_SATISFACTION           = "xpath=//mat-form-field[.//mat-label[contains(.,'Date of Satisfaction')]]//input"
    TYPE_OF_CHARGE_SELECT          = "xpath=//mat-form-field[.//mat-label[contains(.,'Type of Charge')]]//mat-select"
    SUBMIT_BTN                     = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Submit')]"
    CANCEL_BTN                     = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Cancel')]"
    SEARCH_INPUT                   = "#erpSearchInput"

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
            if "Register%20Charges" in self.page.url or "Register Charges" in self.page.url:
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
        self.page.wait_for_selector(self.DATE_OF_CREATION, timeout=5000)

    def fill_form(self, data):
        if data.get("date_of_creation"):
            self._fill_date(self.DATE_OF_CREATION, data["date_of_creation"])

        if data.get("date_of_modification"):
            self._fill_date(self.DATE_OF_MODIFICATION, data["date_of_modification"])

        if data.get("charge_id"):
            self.page.locator(self.CHARGE_ID_ROC).first.click(force=True)
            self.page.locator(self.CHARGE_ID_ROC).first.fill(data["charge_id"])
            self.page.locator(self.CHARGE_ID_ROC).first.press("Tab")

        self._select_mat_option(self.TYPE_OF_CHARGE_SELECT)
        self.page.wait_for_timeout(300)

        if data.get("description"):
            self.page.locator(self.DESCRIPTION_OF_ASSETS_PROPERTY).first.click(force=True)
            self.page.locator(self.DESCRIPTION_OF_ASSETS_PROPERTY).first.fill(data["description"])
            self.page.locator(self.DESCRIPTION_OF_ASSETS_PROPERTY).first.press("Tab")

        if data.get("amount_secured"):
            self.page.locator(self.AMOUNT_SECURED).first.click(force=True)
            self.page.locator(self.AMOUNT_SECURED).first.fill(data["amount_secured"])
            self.page.locator(self.AMOUNT_SECURED).first.press("Tab")

        if data.get("charge_holder"):
            self.page.locator(self.CHARGE_HOLDER_DETAILS).first.click(force=True)
            self.page.locator(self.CHARGE_HOLDER_DETAILS).first.fill(data["charge_holder"])
            self.page.locator(self.CHARGE_HOLDER_DETAILS).first.press("Tab")

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

    def search_charge(self, charge_id):
        inp = self.page.locator(self.SEARCH_INPUT)
        if not inp.is_visible():
            self.page.evaluate("""
                var btn = document.querySelector('button[mattooltip="Search"]');
                if (btn) { btn.scrollIntoView({block:'center'}); btn.click(); }
            """)
            self.page.wait_for_timeout(800)
        inp.wait_for(state="visible", timeout=5000)
        inp.fill(charge_id)
        self.page.keyboard.press("Enter")
        self.page.wait_for_timeout(1500)

    def is_charge_in_table(self, charge_id):
        for _ in range(10):
            rows = self.page.locator("table#excel-table tbody tr")
            for i in range(rows.count()):
                if charge_id in rows.nth(i).inner_text():
                    return True
            self.page.wait_for_timeout(300)
        return False

    def verify_charge_exists(self, charge_id):
        assert self.is_charge_in_table(charge_id), f"Charge ID '{charge_id}' not found in table"

    def _find_row_index(self, charge_id):
        rows = self.page.locator("table#excel-table tbody tr")
        for i in range(rows.count()):
            if charge_id in rows.nth(i).inner_text():
                return i
        raise AssertionError(f"Charge ID '{charge_id}' not found in table")

    def click_view_button(self, charge_id):
        self.click_row_action(self._find_row_index(charge_id), "View")

    def click_history_button(self, charge_id):
        self.click_row_action(self._find_row_index(charge_id), "History")
        self.page.wait_for_timeout(1000)

    def verify_view_popup_read_only(self):
        buttons = self.page.locator(".popup-footer button")
        texts = [buttons.nth(i).text_content().strip() for i in range(buttons.count())]
        assert "Submit" not in texts and "Update" not in texts, \
            "View popup must not have Submit or Update"
