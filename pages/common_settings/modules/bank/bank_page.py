from pages.base_playwright_page import BasePlaywrightPage


class BankPage(BasePlaywrightPage):
    URL = "https://rhythmerp.algorhythms.in/#/dynamic-screens/Bank"
    ADD_BTN = "button:has-text('Add Bank')"
    NAME_INPUT = "mat-form-field:has(mat-label:has-text('Bank Name')) input"
    CODE_INPUT = "mat-form-field:has(mat-label:has-text('Bank Code')) input"
    BRANCH_NAME_INPUT = "mat-form-field:has(mat-label:has-text('Branch Name')) input"
    BRANCH_CODE_INPUT = "mat-form-field:has(mat-label:has-text('Branch Code')) input"
    ACCOUNT_NUMBER_INPUT = "mat-form-field:has(mat-label:has-text('Account Number')) input"
    ACCOUNT_TYPE_SELECT = "mat-form-field:has(mat-label:has-text('Account Type')) mat-select"
    GL_ACCOUNT_SELECT = "mat-form-field:has(mat-label:has-text('GL Account')) mat-select"
    IFSC_INPUT = "mat-form-field:has(mat-label:has-text('IFSC Code')) input"
    SWIFT_INPUT = "mat-form-field:has(mat-label:has-text('Swift Number')) input"
    IBAN_INPUT = "mat-form-field:has(mat-label:has-text('IBAN Number')) input"
    BALANCE_CREDIT_LIMIT_INPUT = "//mat-label[contains(.,'Balance Cash Credit Limit')]/ancestor::mat-form-field//input"
    CASH_CREDIT_LIMIT_INPUT = "//mat-label[contains(.,'Cash Credit Limit') and not(contains(.,'Balance'))]/ancestor::mat-form-field//input"
    ADDRESS_INPUT = "mat-form-field:has(mat-label:has-text('Bank Address')) input"
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
            if "/Bank" in self.page.url or "%2FBank" in self.page.url:
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
        """Open mat-select via CDP click and pick first available option."""
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

    def _try_fill(self, selector, value):
        try:
            loc = f"xpath={selector}" if selector.startswith("//") else selector
            inp = self.page.locator(loc)
            if inp.count() > 0 and value:
                inp.first.fill(str(value))
        except Exception:
            pass

    def fill_form(self, data):
        self.page.fill(self.NAME_INPUT, data["bank_name"])
        self._try_fill(self.CODE_INPUT, data.get("bank_code"))
        self._try_fill(self.BRANCH_NAME_INPUT, data.get("branch_name"))
        self._try_fill(self.BRANCH_CODE_INPUT, data.get("branch_code"))
        self._try_fill(self.ACCOUNT_NUMBER_INPUT, data.get("account_number"))
        self._select_mat_option(self.ACCOUNT_TYPE_SELECT)
        self._select_mat_option(self.GL_ACCOUNT_SELECT)
        self._try_fill(self.IFSC_INPUT, data.get("ifsc_code"))
        self._try_fill(self.SWIFT_INPUT, data.get("swift_number"))
        self._try_fill(self.IBAN_INPUT, data.get("iban_number"))
        self._try_fill(self.BALANCE_CREDIT_LIMIT_INPUT, data.get("cash_credit_limit"))
        self._try_fill(self.CASH_CREDIT_LIMIT_INPUT, data.get("cash_credit_limit"))
        self._try_fill(self.ADDRESS_INPUT, data.get("bank_address"))

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
            self.page.wait_for_selector(".swal2-container", timeout=5000)
            title = (self.page.locator("#swal2-title").text_content() or "").strip().lower()
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

    def go_to_first_page(self):
        """Go to page 1 — AUTO... names sort alphabetically to the start."""
        try:
            first_btn = self.page.locator("xpath=//button[.//i[contains(@class,'material-icons')][normalize-space()='first_page']]")
            if first_btn.count() > 0 and first_btn.is_enabled():
                first_btn.click()
                self.page.wait_for_timeout(800)
        except Exception:
            pass

    def is_bank_in_table(self, name):
        # BUG-003: search doesn't filter — scan all visible rows
        for _ in range(10):
            rows = self.page.locator("table#excel-table tbody tr")
            for i in range(rows.count()):
                if name in rows.nth(i).inner_text():
                    return True
            self.page.wait_for_timeout(300)
        return False

    def verify_bank_exists(self, name):
        assert self.is_bank_in_table(name), f"Bank '{name}' not found in table"

    def _find_row_index(self, name):
        rows = self.page.locator("table#excel-table tbody tr")
        for i in range(rows.count()):
            if name in rows.nth(i).inner_text():
                return i
        raise AssertionError(f"Bank '{name}' not found in table")

    def click_view_button(self, name):
        self.click_row_action(self._find_row_index(name), "View")

    def click_edit_button(self, name):
        self.click_row_action(self._find_row_index(name), "Edit")

    def click_history_button(self, name):
        # BUG-006: History opens View popup instead of audit trail
        self.click_row_action(self._find_row_index(name), "History")
        self.page.wait_for_timeout(1000)

    def update_name(self, new_name):
        name_input = self.page.locator(self.NAME_INPUT)
        name_input.click(click_count=3)
        name_input.fill(new_name)

    def verify_view_popup_read_only(self):
        buttons = self.page.locator(".popup-footer button")
        texts = [buttons.nth(i).text_content().strip() for i in range(buttons.count())]
        assert "Submit" not in texts and "Update" not in texts, \
            "View popup must not have Submit or Update"
