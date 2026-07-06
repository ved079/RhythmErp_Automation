from pages.base_playwright_page import BasePlaywrightPage


class RegisterOfLoanPage(BasePlaywrightPage):
    URL = "https://rhythmerp.algorhythms.in/#/dynamic-screens/Register%20of%20Loan/Register%20of%20Loan"

    SANCTION_DATE           = "xpath=//mat-form-field[.//mat-label[contains(.,'Sanction Date')]]//input"
    BANK_NAME               = "xpath=//mat-form-field[.//mat-label[contains(.,'Bank Name')]]//input"
    SANCTION_AMOUNT         = "xpath=//mat-form-field[.//mat-label[contains(.,'Sanction Amount')]]//input"
    DISBURSEMENT_AMOUNT     = "xpath=//mat-form-field[.//mat-label[contains(.,'Disbursement Amount')]]//input"
    EMI_SERVICING_DATE      = "xpath=//mat-form-field[.//mat-label[contains(.,'EMI/Servicing Date')]]//input"
    INSTALMENT_AMOUNT       = "xpath=//mat-form-field[.//mat-label[contains(.,'Instalment Amount')]]//input"
    REMINDER_PERIOD_IN_DAYS = "xpath=//mat-form-field[.//mat-label[contains(.,'Reminder period (in days)')]]//input"
    OUTSTANDING_DATE        = "xpath=//mat-form-field[.//mat-label[contains(.,'Outstanding Date')]]//input"
    OUTSTANDING_AMOUNT      = "xpath=//mat-form-field[.//mat-label[contains(.,'Outstanding Amount')]]//input"
    FACILITY_DETAILS_SELECT = "xpath=//mat-form-field[.//mat-label[contains(.,'Facility Details')]]//mat-select"
    EMI_PERIOD_SELECT       = "xpath=//mat-form-field[.//mat-label[contains(.,'EMI Period')]]//mat-select"
    SUBMIT_BTN              = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Submit')]"
    CANCEL_BTN              = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Cancel')]"
    SEARCH_INPUT            = "#erpSearchInput"

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
            if "Register%20of%20Loan" in self.page.url or "Register of Loan" in self.page.url:
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
        self.page.wait_for_selector(self.BANK_NAME, timeout=5000)

    def fill_form(self, data):
        if data.get("sanction_date"):
            self._fill_date(self.SANCTION_DATE, data["sanction_date"])

        if data.get("bank_name"):
            self.page.locator(self.BANK_NAME).first.click(force=True)
            self.page.locator(self.BANK_NAME).first.fill(data["bank_name"])
            self.page.locator(self.BANK_NAME).first.press("Tab")

        if data.get("sanction_amount"):
            self.page.locator(self.SANCTION_AMOUNT).first.click(force=True)
            self.page.locator(self.SANCTION_AMOUNT).first.fill(data["sanction_amount"])
            self.page.locator(self.SANCTION_AMOUNT).first.press("Tab")

        self._select_mat_option(self.FACILITY_DETAILS_SELECT)
        self.page.wait_for_timeout(300)

        if data.get("disbursement_amount"):
            self.page.locator(self.DISBURSEMENT_AMOUNT).first.click(force=True)
            self.page.locator(self.DISBURSEMENT_AMOUNT).first.fill(data["disbursement_amount"])
            self.page.locator(self.DISBURSEMENT_AMOUNT).first.press("Tab")

        if data.get("emi_servicing_date"):
            self._fill_date(self.EMI_SERVICING_DATE, data["emi_servicing_date"])

        if data.get("instalment_amount"):
            self.page.locator(self.INSTALMENT_AMOUNT).first.click(force=True)
            self.page.locator(self.INSTALMENT_AMOUNT).first.fill(data["instalment_amount"])
            self.page.locator(self.INSTALMENT_AMOUNT).first.press("Tab")

        if data.get("reminder_days"):
            self.page.locator(self.REMINDER_PERIOD_IN_DAYS).first.click(force=True)
            self.page.locator(self.REMINDER_PERIOD_IN_DAYS).first.fill(data["reminder_days"])
            self.page.locator(self.REMINDER_PERIOD_IN_DAYS).first.press("Tab")

        self._select_mat_option(self.EMI_PERIOD_SELECT)
        self.page.wait_for_timeout(300)

        if data.get("outstanding_date"):
            self._fill_date(self.OUTSTANDING_DATE, data["outstanding_date"])

        if data.get("outstanding_amount"):
            self.page.locator(self.OUTSTANDING_AMOUNT).first.click(force=True)
            self.page.locator(self.OUTSTANDING_AMOUNT).first.fill(data["outstanding_amount"])
            self.page.locator(self.OUTSTANDING_AMOUNT).first.press("Tab")

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

    def search_loan(self, bank_name):
        inp = self.page.locator(self.SEARCH_INPUT)
        if not inp.is_visible():
            self.page.evaluate("""
                var btn = document.querySelector('button[mattooltip="Search"]');
                if (btn) { btn.scrollIntoView({block:'center'}); btn.click(); }
            """)
            self.page.wait_for_timeout(800)
        inp.wait_for(state="visible", timeout=5000)
        inp.fill(bank_name)
        self.page.keyboard.press("Enter")
        self.page.wait_for_timeout(1500)

    def is_loan_in_table(self, bank_name):
        for _ in range(10):
            rows = self.page.locator("table#excel-table tbody tr")
            for i in range(rows.count()):
                if bank_name in rows.nth(i).inner_text():
                    return True
            self.page.wait_for_timeout(300)
        return False

    def verify_loan_exists(self, bank_name):
        assert self.is_loan_in_table(bank_name), f"Loan '{bank_name}' not found in table"

    def _find_row_index(self, bank_name):
        rows = self.page.locator("table#excel-table tbody tr")
        for i in range(rows.count()):
            if bank_name in rows.nth(i).inner_text():
                return i
        raise AssertionError(f"Loan '{bank_name}' not found in table")

    def click_view_button(self, bank_name):
        self.click_row_action(self._find_row_index(bank_name), "View")

    def click_edit_button(self, bank_name):
        self.click_row_action(self._find_row_index(bank_name), "Edit")
        self.page.wait_for_selector(self.BANK_NAME, timeout=5000)

    def update_bank_name(self, new_value):
        self.page.locator(self.BANK_NAME).first.click(click_count=3)
        self.page.locator(self.BANK_NAME).first.fill(new_value)

    def click_update(self):
        self.page.locator("xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Update')]").click()

    def click_history_button(self, bank_name):
        self.click_row_action(self._find_row_index(bank_name), "History")
        self.page.wait_for_timeout(1000)

    def verify_view_popup_read_only(self):
        buttons = self.page.locator(".popup-footer button")
        texts = [buttons.nth(i).text_content().strip() for i in range(buttons.count())]
        assert "Submit" not in texts and "Update" not in texts, \
            "View popup must not have Submit or Update"
