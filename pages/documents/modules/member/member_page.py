from pages.base_playwright_page import BasePlaywrightPage


class MemberPage(BasePlaywrightPage):
    URL = "https://rhythmerp.algorhythms.in/#/dynamic-screens/Member/Member"

    NAME_INPUT                 = "xpath=//mat-form-field[.//mat-label[contains(.,'Member Name')]]//input"
    MEMBER_ADDRESS             = "xpath=//mat-form-field[.//mat-label[contains(.,'Member Address')]]//input"
    FOLIO_NUMBER               = "xpath=//mat-form-field[.//mat-label[contains(.,'Folio Number')]]//input"
    PAN_OTHER                  = "xpath=//mat-form-field[.//mat-label[contains(.,'PAN/Other')]]//input"
    REGISTRATION_DATE          = "xpath=//mat-form-field[.//mat-label[contains(.,'Registration Date')]]//input"
    NUMBER_AND_CLASS_OF_SHARES = "xpath=//mat-form-field[.//mat-label[contains(.,'Number and Class of Shares')]]//input"
    DISTINCTIVE_NUMBER         = "xpath=//mat-form-field[.//mat-label[contains(.,'Distintive Number')]]//input"
    AMOUNT_PAID_ON_SHARES      = "xpath=//mat-form-field[.//mat-label[contains(.,'Amount Paid on Shares')]]//input"
    DATE_OF_ALLOTMENT          = "xpath=//mat-form-field[.//mat-label[contains(.,'Date of Allotment')]]//input"
    DATE_OF_CESSATION          = "xpath=//mat-form-field[.//mat-label[contains(.,'Date of Cessation')]]//input"
    PERCENTAGE_OF_SHARES       = "xpath=//mat-form-field[.//mat-label[contains(.,'Percentage of Shares')]]//input"
    PHONE_NUMBER               = "xpath=//mat-form-field[.//mat-label[contains(.,'Phone Number')]]//input"
    PREFIX_SELECT              = "xpath=//mat-form-field[.//mat-label[contains(.,'Prefix')]]//mat-select"
    SUBMIT_BTN                 = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Submit')]"
    CANCEL_BTN                 = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Cancel')]"
    SEARCH_INPUT               = "#erpSearchInput"

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
        # Native JS click fires real DOM events that Angular's selection handler listens to
        self.page.evaluate("document.querySelector('.mat-mdc-select-panel mat-option')?.click()")
        self.page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=5000)
        self.page.wait_for_timeout(300)

    def navigate_to_page(self):
        try:
            if "Member" in self.page.url:
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
        self.page.wait_for_selector(self.NAME_INPUT, timeout=5000)

    def fill_form(self, data):
        self._select_mat_option(self.PREFIX_SELECT)
        self.page.wait_for_timeout(300)
        self._select_mat_option(self.PREFIX_SELECT)
        self.page.wait_for_timeout(500)

        if data.get("member_name"):
            self.page.locator(self.NAME_INPUT).first.click(force=True)
            self.page.locator(self.NAME_INPUT).first.fill(data["member_name"])
            self.page.locator(self.NAME_INPUT).first.press("Tab")

        if data.get("member_address"):
            self.page.locator(self.MEMBER_ADDRESS).first.click(force=True)
            self.page.locator(self.MEMBER_ADDRESS).first.fill(data["member_address"])
            self.page.locator(self.MEMBER_ADDRESS).first.press("Tab")

        if data.get("folio_number"):
            self.page.locator(self.FOLIO_NUMBER).first.click(force=True)
            self.page.locator(self.FOLIO_NUMBER).first.fill(data["folio_number"])
            self.page.locator(self.FOLIO_NUMBER).first.press("Tab")

        if data.get("pan_no"):
            self.page.locator(self.PAN_OTHER).first.click(force=True)
            self.page.locator(self.PAN_OTHER).first.fill(data["pan_no"])
            self.page.locator(self.PAN_OTHER).first.press("Tab")

        if data.get("registration_date"):
            self.page.locator(self.REGISTRATION_DATE).first.click(force=True, click_count=3)
            self.page.locator(self.REGISTRATION_DATE).first.fill(data["registration_date"])
            self.page.keyboard.press("Tab")
            self.page.wait_for_timeout(200)

        if data.get("no_class_shares"):
            self.page.locator(self.NUMBER_AND_CLASS_OF_SHARES).first.click(force=True)
            self.page.locator(self.NUMBER_AND_CLASS_OF_SHARES).first.fill(data["no_class_shares"])
            self.page.locator(self.NUMBER_AND_CLASS_OF_SHARES).first.press("Tab")

        if data.get("distinctive_number"):
            self.page.locator(self.DISTINCTIVE_NUMBER).first.click(force=True)
            self.page.locator(self.DISTINCTIVE_NUMBER).first.fill(data["distinctive_number"])
            self.page.locator(self.DISTINCTIVE_NUMBER).first.press("Tab")

        if data.get("amount_paid"):
            self.page.locator(self.AMOUNT_PAID_ON_SHARES).first.click(force=True)
            self.page.locator(self.AMOUNT_PAID_ON_SHARES).first.fill(data["amount_paid"])
            self.page.locator(self.AMOUNT_PAID_ON_SHARES).first.press("Tab")

        if data.get("date_of_allotment"):
            self.page.locator(self.DATE_OF_ALLOTMENT).first.click(force=True, click_count=3)
            self.page.locator(self.DATE_OF_ALLOTMENT).first.fill(data["date_of_allotment"])
            self.page.keyboard.press("Tab")
            self.page.wait_for_timeout(200)

        if data.get("percentage"):
            self.page.locator(self.PERCENTAGE_OF_SHARES).first.click(force=True)
            self.page.locator(self.PERCENTAGE_OF_SHARES).first.fill(data["percentage"])
            self.page.locator(self.PERCENTAGE_OF_SHARES).first.press("Tab")

        if data.get("phone"):
            self.page.locator(self.PHONE_NUMBER).first.click(force=True)
            self.page.locator(self.PHONE_NUMBER).first.fill(data["phone"])
            self.page.locator(self.PHONE_NUMBER).first.press("Tab")

        self.page.wait_for_timeout(300)
        self.fill_kyc_row(data.get("kyc_number", "234567890123"))
        self._clear_overlays()

    def fill_kyc_row(self, kyc_number="234567890123"):
        row = self.page.locator("app-dynamic-details tbody tr.preview-row").first
        row.wait_for(state="visible", timeout=5000)
        self.page.wait_for_timeout(300)

        kyc_doc_sel = self.page.locator(
            "xpath=//mat-form-field[.//mat-label[contains(.,'KYC Document')]]//mat-select"
        )
        kyc_doc_sel.wait_for(state="visible", timeout=5000)
        kyc_doc_sel.click(force=True)
        self.page.wait_for_selector(".mat-mdc-select-panel", timeout=5000)
        self.page.locator(".mat-mdc-select-panel mat-option").first.click(force=True)
        self.page.wait_for_timeout(400)
        self._clear_overlays()

        kyc_num = self.page.locator(
            "xpath=//mat-form-field[.//mat-label[contains(.,'KYC Number')]]//input[not(@readonly)]"
        )
        kyc_num.fill(kyc_number)
        self.page.wait_for_timeout(300)

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
                errors = self.page.locator("mat-error").all_text_contents()
                labels = self.page.locator("mat-form-field.ng-invalid mat-label").all_text_contents()
                raise AssertionError(
                    f"Validation failed — invalid fields: {labels} — errors: {errors}"
                )
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

    def search_member(self, name):
        inp = self.page.locator(self.SEARCH_INPUT)
        if not inp.is_visible():
            self.page.evaluate("""
                var btn = document.querySelector('button[mattooltip="Search"]');
                if (btn) { btn.scrollIntoView({block:'center'}); btn.click(); }
            """)
            self.page.wait_for_timeout(800)
        inp.wait_for(state="visible", timeout=5000)
        inp.fill(name)
        self.page.keyboard.press("Enter")
        self.page.wait_for_timeout(1500)

    def is_member_in_table(self, name):
        for _ in range(10):
            rows = self.page.locator("table#excel-table tbody tr")
            for i in range(rows.count()):
                if name in rows.nth(i).inner_text():
                    return True
            self.page.wait_for_timeout(300)
        return False

    def verify_member_exists(self, name):
        assert self.is_member_in_table(name), f"Member '{name}' not found in table"

    def _find_row_index(self, name):
        rows = self.page.locator("table#excel-table tbody tr")
        for i in range(rows.count()):
            if name in rows.nth(i).inner_text():
                return i
        raise AssertionError(f"Member '{name}' not found in table")

    def click_view_button(self, name):
        self.click_row_action(self._find_row_index(name), "View")

    def click_edit_button(self, name):
        self.click_row_action(self._find_row_index(name), "Edit")
        self.page.wait_for_selector(self.NAME_INPUT, timeout=5000)

    def update_name(self, new_name):
        self.page.locator(self.NAME_INPUT).first.click(click_count=3)
        self.page.locator(self.NAME_INPUT).first.fill(new_name)

    def click_update(self):
        self.page.locator("xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Update')]").click()

    def click_history_button(self, name):
        self.click_row_action(self._find_row_index(name), "History")
        self.page.wait_for_timeout(1000)

    def verify_view_popup_read_only(self):
        buttons = self.page.locator(".popup-footer button")
        texts = [buttons.nth(i).text_content().strip() for i in range(buttons.count())]
        assert "Submit" not in texts and "Update" not in texts, \
            "View popup must not have Submit or Update"
