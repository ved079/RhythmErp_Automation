from pages.base_playwright_page import BasePlaywrightPage


class FarmerPage(BasePlaywrightPage):
    URL = "https://rhythmerp.algorhythms.in/#/dynamic-screens/Farmer/Farmer"

    # Universal fields
    FARMER_NAME     = "xpath=//mat-form-field[.//mat-label[contains(.,'Farmer Name')]]//input"
    EMAIL           = "xpath=//mat-form-field[.//mat-label[contains(.,'Email')]]//input"
    PHONE_NUMBER    = "xpath=//mat-form-field[.//mat-label[contains(.,'Phone Number')]]//input"
    FARMER_CATEGORY = "xpath=//mat-form-field[.//mat-label[contains(.,'Farmer Category')]]//mat-select"

    # Address fields (page 2 grid — inline)
    ADDR_ADDRESS_TYPE = "xpath=//mat-form-field[.//mat-label[contains(.,'Address Type')]]//mat-select"
    ADDR_COUNTRY      = "xpath=//mat-form-field[.//mat-label[contains(.,'Country')]]//mat-select"
    ADDR_STATE        = "xpath=//mat-form-field[.//mat-label[contains(.,'State')]]//mat-select"
    ADDR_DISTRICT     = "xpath=//mat-form-field[.//mat-label[contains(.,'District')]]//mat-select"
    ADDR_TALUKA       = "xpath=//mat-form-field[.//mat-label[contains(.,'Taluka')]]//mat-select"
    ADDR_VILLAGE      = "xpath=//mat-form-field[.//mat-label[contains(.,'Village')]]//mat-select"
    ADDR_ADDRESS      = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Address']]//input"
    ADDR_PIN_CODE     = "xpath=//mat-form-field[.//mat-label[contains(.,'Pin Code')]]//mat-select"

    # Bank fields (page 3 grid — inline)
    BANK_NAME_INPUT   = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Bank Name']]//input"
    BANK_BRANCH       = "xpath=//mat-form-field[.//mat-label[contains(.,'Branch')]]//input"
    BANK_IFSC         = "xpath=//mat-form-field[.//mat-label[contains(.,'IFSC Code')]]//input"
    BANK_ACCOUNT_TYPE = "xpath=//mat-form-field[.//mat-label[contains(.,'Account Type')]]//mat-select"
    BANK_HOLDER_NAME  = "xpath=//mat-form-field[.//mat-label[contains(.,'Account Holder Name')]]//input"
    BANK_ACCOUNT_NO   = "xpath=//mat-form-field[.//mat-label[contains(.,'Account Number')]]//input"
    BANK_PROOF        = "xpath=//mat-form-field[.//mat-label[contains(.,'Bank Proof')]]//mat-select"

    SUBMIT_BTN   = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Submit')]"
    CANCEL_BTN   = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Cancel')]"
    SEARCH_INPUT = "#erpSearchInput"

    def _clear_overlays(self):
        self.page.evaluate(
            "document.querySelectorAll('.cdk-overlay-backdrop').forEach(el => el.remove())"
        )

    def _select_mat_option(self, selector, nth=0):
        sel = self.page.locator(selector).nth(nth)
        sel.click(force=True)
        self.page.wait_for_selector(".mat-mdc-select-panel", timeout=5000)
        self.page.locator(".mat-mdc-select-panel mat-option").first.wait_for(state="visible", timeout=3000)
        self.page.evaluate("document.querySelector('.mat-mdc-select-panel mat-option')?.click()")
        self.page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=5000)
        self.page.wait_for_timeout(300)

    def _select_mat_option_by_text(self, selector, text, nth=0):
        sel = self.page.locator(selector).nth(nth)
        sel.click(force=True)
        self.page.wait_for_selector(".mat-mdc-select-panel", timeout=5000)
        opt = self.page.locator(f".mat-mdc-select-panel mat-option:has-text('{text}')")
        opt.first.wait_for(state="visible", timeout=3000)
        opt.first.click(force=True)
        self.page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=5000)
        self.page.wait_for_timeout(300)

    def _click_next(self):
        self.page.evaluate("""
            const btns = document.querySelectorAll('button.mat-stepper-next');
            for (const btn of btns) {
                const content = btn.closest('.mat-horizontal-stepper-content, .step-shell');
                if (content && !content.classList.contains('mat-horizontal-stepper-content-inactive')
                    && getComputedStyle(content).display !== 'none') {
                    btn.click(); break;
                }
            }
        """)
        self.page.wait_for_timeout(1000)

    def _add_row(self):
        self.page.evaluate("""
            var btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim().toLowerCase().includes('add row'));
            if (btn) { btn.scrollIntoView({block:'center'}); btn.click(); }
        """)
        self.page.wait_for_timeout(800)

    def _fill_address_row(self, row_index, address_text, address_type=None):
        if address_type:
            self._select_mat_option_by_text(self.ADDR_ADDRESS_TYPE, address_type, nth=row_index)
        else:
            self._select_mat_option(self.ADDR_ADDRESS_TYPE, nth=row_index)
        self._select_mat_option_by_text(self.ADDR_COUNTRY, "India", nth=row_index)
        for sel in [self.ADDR_STATE, self.ADDR_DISTRICT, self.ADDR_TALUKA]:
            self._select_mat_option(sel, nth=row_index)
        try:
            self._select_mat_option(self.ADDR_VILLAGE, nth=row_index)
        except Exception:
            pass
        addr = self.page.locator(self.ADDR_ADDRESS).nth(row_index)
        addr.click(force=True)
        addr.fill(address_text)
        addr.press("Tab")
        self._select_mat_option(self.ADDR_PIN_CODE, nth=row_index)

    def navigate_to_page(self):
        try:
            if "Farmer" in self.page.url:
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
        self.page.wait_for_selector(self.FARMER_NAME, timeout=5000)

    def fill_form(self, data):
        # Page 1 — universal fields (Walk-in Farmer)
        for selector, key, default in [
            (self.FARMER_NAME,  "farmer_name",  "Ramesh Patil"),
            (self.EMAIL,        "email",        "farmer@testmail.com"),
            (self.PHONE_NUMBER, "phone_number", "9876543210"),
        ]:
            loc = self.page.locator(selector).first
            loc.click(force=True)
            loc.fill(data.get(key, default))
            loc.press("Tab")

        self._select_mat_option_by_text(self.FARMER_CATEGORY, "Walk-in Farmer")
        self.page.wait_for_timeout(500)

        # Address Details — 1 pre-existing row (Permanent), add 1 more (Current)
        self._fill_address_row(0, data.get("address1", "101 Shivaji Path Pune"), address_type="Permanent Address")
        self._add_row()
        self._fill_address_row(1, data.get("address2", "202 MG Road Kolhapur"), address_type="Current Address")

        # Bank Details
        self._click_next()
        self._add_row()
        for selector, key, default in [
            (self.BANK_NAME_INPUT, "bank_name",    "HDFC Bank"),
            (self.BANK_BRANCH,     "bank_branch",  "Pune Branch"),
            (self.BANK_IFSC,       "bank_ifsc",    "BARB0696379"),
            (self.BANK_HOLDER_NAME,"bank_holder",  "Ramesh Patil"),
            (self.BANK_ACCOUNT_NO, "bank_account", "964770974496"),
        ]:
            loc = self.page.locator(selector).first
            loc.click(force=True)
            loc.fill(data.get(key, default))
            loc.press("Tab")
        self._select_mat_option(self.BANK_ACCOUNT_TYPE)
        self._select_mat_option(self.BANK_PROOF)
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

    def search_farmer(self, farmer_name):
        inp = self.page.locator(self.SEARCH_INPUT)
        if not inp.is_visible():
            self.page.evaluate("""
                var btn = document.querySelector('button[mattooltip="Search"]');
                if (btn) { btn.scrollIntoView({block:'center'}); btn.click(); }
            """)
            self.page.wait_for_timeout(800)
        inp.wait_for(state="visible", timeout=5000)
        inp.fill(farmer_name)
        self.page.keyboard.press("Enter")
        self.page.wait_for_timeout(1500)

    def is_farmer_in_table(self, farmer_name):
        for _ in range(10):
            rows = self.page.locator("table#excel-table tbody tr")
            for i in range(rows.count()):
                if farmer_name in rows.nth(i).inner_text():
                    return True
            self.page.wait_for_timeout(300)
        return False

    def verify_farmer_exists(self, farmer_name):
        assert self.is_farmer_in_table(farmer_name), f"Farmer '{farmer_name}' not found in table"

    def _find_row_index(self, farmer_name):
        rows = self.page.locator("table#excel-table tbody tr")
        for i in range(rows.count()):
            if farmer_name in rows.nth(i).inner_text():
                return i
        raise AssertionError(f"Farmer '{farmer_name}' not found in table")

    def click_view_button(self, farmer_name):
        self.click_row_action(self._find_row_index(farmer_name), "View")

    def click_history_button(self, farmer_name):
        self.click_row_action(self._find_row_index(farmer_name), "History")
        self.page.wait_for_timeout(1000)

    def verify_view_popup_read_only(self):
        buttons = self.page.locator(".popup-footer button")
        texts = [buttons.nth(i).text_content().strip() for i in range(buttons.count())]
        assert "Submit" not in texts and "Update" not in texts, \
            "View popup must not have Submit or Update"
