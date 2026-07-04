from pages.base_playwright_page import BasePlaywrightPage


class FarmerPage(BasePlaywrightPage):
    URL = "https://rhythmerp.algorhythms.in/#/dynamic-screens/Farmer/Farmer"

    # Universal fields
    FARMER_NAME     = "xpath=//mat-form-field[.//mat-label[contains(.,'Farmer Name')]]//input"
    EMAIL           = "xpath=//mat-form-field[.//mat-label[contains(.,'Email')]]//input"
    PHONE_NUMBER    = "xpath=//mat-form-field[.//mat-label[contains(.,'Phone Number')]]//input"
    FARMER_CATEGORY = "xpath=//mat-form-field[.//mat-label[contains(.,'Farmer Category')]]//mat-select"

    # Address fields (inline grid on step 1)
    ADDR_ADDRESS_TYPE = "xpath=//mat-form-field[.//mat-label[contains(.,'Address Type')]]//mat-select"
    ADDR_COUNTRY      = "xpath=//mat-form-field[.//mat-label[contains(.,'Country')]]//mat-select"
    ADDR_STATE        = "xpath=//mat-form-field[.//mat-label[contains(.,'State')]]//mat-select"
    ADDR_DISTRICT     = "xpath=//mat-form-field[.//mat-label[contains(.,'District')]]//mat-select"
    ADDR_TALUKA       = "xpath=//mat-form-field[.//mat-label[contains(.,'Taluka')]]//mat-select"
    ADDR_VILLAGE      = "xpath=//mat-form-field[.//mat-label[contains(.,'Village')]]//mat-select"
    ADDR_ADDRESS      = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Address']]//input"
    ADDR_PIN_CODE     = "xpath=//mat-form-field[.//mat-label[contains(.,'Pin Code')]]//mat-select"

    # Additional Details
    LAND_CLASSIFICATION = "xpath=//mat-form-field[.//mat-label[contains(.,'Land Classification')]]//mat-select"
    APP_PASSWORD        = "xpath=//mat-form-field[.//mat-label[contains(.,'App Password')]]//input"
    DATE_OF_BIRTH       = "xpath=//mat-form-field[.//mat-label[contains(.,'Date Of Birth')]]//input"
    AGE                 = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Age']]//input"
    GENDER              = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Gender']]//mat-select"
    CATEGORY            = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Category']]//mat-select"
    RELIGION            = "xpath=//mat-form-field[.//mat-label[contains(.,'Religion')]]//mat-select"

    # Other Details (Borrower only)
    EDUCATION_QUALIFICATION  = "xpath=//mat-form-field[.//mat-label[contains(.,'Education Qualification')]]//mat-select"
    ELECTRICITY_AVAILABILITY = "xpath=//mat-form-field[.//mat-label[contains(.,'Electricity Availability')]]//mat-select"

    # Land Details grid
    LAND_FARM_NAME     = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Farm Name']]//input"
    LAND_NO_OF_OWNER   = "xpath=//mat-form-field[.//mat-label[contains(.,'No Of Owner')]]//input"
    LAND_TOTAL_HECTARE = "xpath=//mat-form-field[.//mat-label[contains(.,'Total Land On Document')]]//input"
    LAND_GAT_NUMBER    = "xpath=//mat-form-field[.//mat-label[contains(.,'Gat Number')]]//input"
    LAND_OWNERSHIP     = "xpath=//mat-form-field[.//mat-label[contains(.,'Land ownership')]]//mat-select"

    # Crop Details grid
    CROP_CROP         = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Crop']]//mat-select"
    CROP_SEASON       = "xpath=//mat-form-field[.//mat-label[contains(.,'Season')]]//mat-select"
    CROP_CULT_HECTARE = "xpath=//mat-form-field[.//mat-label[contains(.,'Cultivation Land In hectare')]]//input"

    # KYC Details grid
    KYC_DOCUMENT = "xpath=//mat-form-field[.//mat-label[contains(.,'KYC Document')]]//mat-select"
    KYC_NUMBER   = "xpath=//mat-form-field[.//mat-label[contains(.,'KYC Number')]]//input"

    # Award Details grid
    AWARD_NAME = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Name']]//input"
    AWARD_YEAR = "xpath=//mat-form-field[.//mat-label[contains(.,'Year')]]//input"

    # Family Details grid (Borrower only)
    FAMILY_MEMBER_NAME  = "xpath=//mat-form-field[.//mat-label[contains(.,'Member Name')]]//input"
    FAMILY_GENDER       = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Gender']]//mat-select"
    FAMILY_RELATIONSHIP = "xpath=//mat-form-field[.//mat-label[contains(.,'Relationship')]]//mat-select"

    # Vehicle Details grid (Borrower only)
    VEHICLE_TYPE = "xpath=//mat-form-field[.//mat-label[contains(.,'Vehicle Type')]]//mat-select"
    VEHICLE_NAME = "xpath=//mat-form-field[.//mat-label[contains(.,'Vehicle Name')]]//mat-select"

    # Income Details grid (Borrower only)
    INCOME_SOURCE  = "xpath=//mat-form-field[.//mat-label[contains(.,'Source of Income')]]//mat-select"
    INCOME_BRACKET = "xpath=//mat-form-field[.//mat-label[contains(.,'Income Bracket')]]//mat-select"

    # Irrigation Details grid (Borrower only)
    IRRIGATION_SOURCE = "xpath=//mat-form-field[.//mat-label[contains(.,'Source of Irrigation')]]//mat-select"
    IRRIGATION_METHOD = "xpath=//mat-form-field[.//mat-label[contains(.,'Method Of Irrigation')]]//mat-select"

    # Loan Details grid (Borrower only)
    LOAN_NAME     = "xpath=//mat-form-field[.//mat-label[contains(.,'Loan Name')]]//input"
    LOAN_FACILITY = "xpath=//mat-form-field[.//mat-label[contains(.,'Facility Type')]]//mat-select"
    LOAN_PURPOSE  = "xpath=//mat-form-field[.//mat-label[contains(.,'Purpose Of Loan')]]//input"
    LOAN_AMOUNT   = "xpath=//mat-form-field[.//mat-label[contains(.,'Sanctioned Amount')]]//input"

    # Bank fields
    BANK_NAME_INPUT   = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Bank Name']]//input"
    BANK_BRANCH       = "xpath=//mat-form-field[.//mat-label[contains(.,'Branch')]]//input"
    BANK_IFSC         = "xpath=//mat-form-field[.//mat-label[contains(.,'IFSC Code')]]//input"
    BANK_ACCOUNT_TYPE = "xpath=//mat-form-field[.//mat-label[contains(.,'Account Type')]]//mat-select"
    BANK_HOLDER_NAME  = "xpath=//mat-form-field[.//mat-label[contains(.,'Account Holder Name')]]//input"
    BANK_ACCOUNT_NO   = "xpath=//mat-form-field[.//mat-label[contains(.,'Account Number')]]//input"
    BANK_PROOF        = "xpath=//mat-form-field[.//mat-label[contains(.,'Bank Proof')]]//mat-select"

    SUBMIT_BTN  = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Submit')]"
    CANCEL_BTN  = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Cancel')]"
    VERIFY_BTN  = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Verify')]"
    APPROVE_BTN = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Approve')]"
    SEARCH_INPUT = "#erpSearchInput"

    # ── helpers ──────────────────────────────────────────────────────────────

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
        try:
            self.page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=5000)
        except Exception:
            self.page.keyboard.press("Escape")
            self.page.wait_for_timeout(300)
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

    def _click_back(self):
        self.page.evaluate("""
            const btns = document.querySelectorAll('button.mat-stepper-previous');
            for (const btn of btns) {
                const content = btn.closest('.mat-horizontal-stepper-content, .step-shell');
                if (content && !content.classList.contains('mat-horizontal-stepper-content-inactive')
                    && getComputedStyle(content).display !== 'none') {
                    btn.click(); break;
                }
            }
        """)
        self.page.wait_for_timeout(1000)

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
        self.page.wait_for_timeout(800)
        if address_type:
            self._select_mat_option_by_text(self.ADDR_ADDRESS_TYPE, address_type, nth=row_index)
        else:
            self._select_mat_option(self.ADDR_ADDRESS_TYPE, nth=row_index)
        self.page.wait_for_timeout(800)
        self._select_mat_option_by_text(self.ADDR_COUNTRY, "India", nth=row_index)
        self.page.wait_for_timeout(800)
        for sel in [self.ADDR_STATE, self.ADDR_DISTRICT, self.ADDR_TALUKA]:
            self._select_mat_option(sel, nth=row_index)
            self.page.wait_for_timeout(800)
        try:
            self._select_mat_option(self.ADDR_VILLAGE, nth=row_index)
            self.page.wait_for_timeout(800)
        except Exception:
            pass
        addr = self.page.locator(self.ADDR_ADDRESS).nth(row_index)
        addr.click(force=True)
        addr.fill(address_text)
        addr.press("Tab")
        self.page.wait_for_timeout(800)
        self._select_mat_option(self.ADDR_PIN_CODE, nth=row_index)
        self.page.wait_for_timeout(800)

    def _delete_extra_address_rows(self):
        active = self.page.locator(
            "xpath=//div[contains(@class,'mat-horizontal-stepper-content') and not(contains(@class,'mat-horizontal-stepper-content-inactive'))]//tbody/tr[3]//button[.//mat-icon[text()='delete_outline']]"
        )
        while active.count() > 0:
            active.first.click(force=True)
            self.page.wait_for_timeout(600)

    # ── step-fill helpers ─────────────────────────────────────────────────────

    def _fill_address_rows(self, data):
        self._fill_address_row(0, data.get("address1", "101 Shivaji Path Pune"), address_type="Permanent Address")
        self.page.evaluate("""
            var btn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.trim().toLowerCase().includes('add row'));
            if (btn) { btn.scrollIntoView({block:'center'}); btn.click(); }
        """)
        self.page.wait_for_timeout(800)
        self._fill_address_row(1, data.get("address2", "202 MG Road Kolhapur"), address_type="Current Address")
        self.page.wait_for_timeout(500)

    def _fill_bank_details(self, data):
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

    def _fill_additional_details(self):
        for sel in [self.LAND_CLASSIFICATION, self.GENDER, self.CATEGORY, self.RELIGION]:
            try:
                self._select_mat_option(sel)
            except Exception:
                pass
        try:
            loc = self.page.locator(self.APP_PASSWORD).first
            loc.click(force=True)
            loc.fill("Password@123456")
            loc.press("Tab")
        except Exception:
            pass
        try:
            loc = self.page.locator(self.DATE_OF_BIRTH).first
            loc.click(force=True)
            loc.fill("01/01/1990")
            loc.press("Tab")
        except Exception:
            pass

    def _fill_other_details(self):
        for sel in [self.EDUCATION_QUALIFICATION, self.ELECTRICITY_AVAILABILITY]:
            try:
                self._select_mat_option(sel)
            except Exception:
                pass

    def _fill_land_details(self):
        self._add_row()
        for selector, default in [
            (self.LAND_FARM_NAME,     "Green Fields"),
            (self.LAND_NO_OF_OWNER,   "2"),
            (self.LAND_TOTAL_HECTARE, "5"),
            (self.LAND_GAT_NUMBER,    "GAT123"),
        ]:
            try:
                loc = self.page.locator(selector).first
                loc.click(force=True)
                loc.fill(default)
                loc.press("Tab")
            except Exception:
                pass
        try:
            self._select_mat_option(self.LAND_OWNERSHIP)
        except Exception:
            pass

    def _fill_crop_details(self):
        self._add_row()
        try:
            loc = self.page.locator(self.LAND_FARM_NAME).first
            loc.click(force=True)
            loc.fill("Green Fields")
            loc.press("Tab")
        except Exception:
            pass
        for sel in [self.CROP_CROP, self.CROP_SEASON]:
            try:
                self._select_mat_option(sel)
            except Exception:
                pass
        try:
            loc = self.page.locator(self.CROP_CULT_HECTARE).first
            loc.click(force=True)
            loc.fill("3")
            loc.press("Tab")
        except Exception:
            pass

    def _fill_kyc_details(self):
        self._add_row()
        try:
            self._select_mat_option(self.KYC_DOCUMENT)
        except Exception:
            pass
        # Check which KYC doc was selected; if Aadhaar, use valid 12-digit number
        try:
            selected = self.page.locator(self.KYC_DOCUMENT).first.inner_text().strip().lower()
        except Exception:
            selected = ""
        kyc_number = "234567891234" if "aadhar" in selected or "aadhaar" in selected else "KYC123456"
        try:
            loc = self.page.locator(self.KYC_NUMBER).first
            loc.click(force=True)
            loc.fill(kyc_number)
            loc.press("Tab")
        except Exception:
            pass

    def _fill_award_details(self):
        self._add_row()
        try:
            loc = self.page.locator(self.AWARD_NAME).first
            loc.click(force=True)
            loc.fill("Best Farmer Award")
            loc.press("Tab")
        except Exception:
            pass
        try:
            loc = self.page.locator(self.AWARD_YEAR).first
            loc.click(force=True)
            loc.fill("2023")
            loc.press("Tab")
        except Exception:
            pass

    def _fill_family_details(self):
        self._add_row()
        try:
            loc = self.page.locator(self.FAMILY_MEMBER_NAME).first
            loc.click(force=True)
            loc.fill("Sunita Patil")
            loc.press("Tab")
        except Exception:
            pass
        for sel in [self.FAMILY_GENDER, self.FAMILY_RELATIONSHIP]:
            try:
                self._select_mat_option(sel)
            except Exception:
                pass

    def _fill_vehicle_details(self):
        self._add_row()
        for sel in [self.VEHICLE_TYPE, self.VEHICLE_NAME]:
            try:
                self._select_mat_option(sel)
            except Exception:
                pass

    def _fill_income_details(self):
        self._add_row()
        for sel in [self.INCOME_SOURCE, self.INCOME_BRACKET]:
            try:
                self._select_mat_option(sel)
            except Exception:
                pass

    def _fill_irrigation_details(self):
        self._add_row()
        for sel in [self.IRRIGATION_SOURCE, self.IRRIGATION_METHOD]:
            try:
                self._select_mat_option(sel)
            except Exception:
                pass

    def _fill_loan_details(self):
        self._add_row()
        for selector, default in [
            (self.LOAN_NAME,    "Kisan Credit"),
            (self.LOAN_PURPOSE, "Crop production"),
            (self.LOAN_AMOUNT,  "50000"),
        ]:
            try:
                loc = self.page.locator(selector).first
                loc.click(force=True)
                loc.fill(default)
                loc.press("Tab")
            except Exception:
                pass
        try:
            self._select_mat_option(self.LOAN_FACILITY)
        except Exception:
            pass

    # ── navigation ────────────────────────────────────────────────────────────

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

    # ── form fill ─────────────────────────────────────────────────────────────

    def fill_form(self, data, category="Walk-in Farmer"):
        for selector, key, default in [
            (self.FARMER_NAME,  "farmer_name",  "Ramesh Patil"),
            (self.EMAIL,        "email",        "farmer@testmail.com"),
            (self.PHONE_NUMBER, "phone_number", "9876543210"),
        ]:
            loc = self.page.locator(selector).first
            loc.click(force=True)
            loc.fill(data.get(key, default))
            loc.press("Tab")

        self._select_mat_option_by_text(self.FARMER_CATEGORY, category)
        self.page.wait_for_timeout(500)

        # Address is on step 1 for all categories
        self._fill_address_rows(data)

        if category == "Walk-in Farmer":
            self._click_next()              # → Bank Details
            self._fill_bank_details(data)
            self._click_back()              # back to address for submit

        elif category == "FPC Member":
            self._click_next()              # → Additional Details
            self._fill_additional_details()
            self._click_next()              # → Land Details
            self._fill_land_details()
            self._click_next()              # → Crop Details
            self._fill_crop_details()
            self._click_next()              # → KYC Details
            self._fill_kyc_details()
            self._click_next()              # → Bank Details
            self._fill_bank_details(data)
            self._click_next()              # → Award Details
            self._fill_award_details()
            self._click_back()              # back to award for submit

        elif category == "Borrower Farmer":
            self._click_next()              # → Other Details
            self._fill_other_details()
            self._click_next()              # → Additional Details
            self._fill_additional_details()
            self._click_next()              # → Family Details
            self._fill_family_details()
            self._click_next()              # → Land Details
            self._fill_land_details()
            self._click_next()              # → Crop Details
            self._fill_crop_details()
            self._click_next()              # → KYC Details
            self._fill_kyc_details()
            self._click_next()              # → Vehicle Details
            self._fill_vehicle_details()
            self._click_next()              # → Income Details
            self._fill_income_details()
            self._click_next()              # → Bank Details
            self._fill_bank_details(data)
            self._click_next()              # → Irrigation Details
            self._fill_irrigation_details()
            self._click_next()              # → Award Details
            self._fill_award_details()
            self._click_next()              # → Loan Details
            self._fill_loan_details()
            self._click_back()              # back to loan for submit

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

    def create_record(self, data, category="Walk-in Farmer"):
        self.open_add_form()
        self.fill_form(data, category=category)
        self._clear_overlays()
        self.page.click(self.SUBMIT_BTN)
        # If 3rd address row caused validation: dismiss (confirm not escape), delete it, resubmit
        try:
            self.page.wait_for_selector(".swal2-container", timeout=5000)
            title = (self.page.locator("#swal2-title").text_content() or "").strip().lower()
            self.page.locator(".swal2-confirm").click()
            self.page.wait_for_selector(".swal2-container", state="hidden", timeout=3000)
            if "validation" in title or "failed" in title or "error" in title:
                self.page.wait_for_timeout(500)
                self._delete_extra_address_rows()
                self._clear_overlays()
                self.page.click(self.SUBMIT_BTN)
        except Exception:
            pass
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

    def click_edit_button(self, farmer_name):
        self.click_row_action(self._find_row_index(farmer_name), "Edit")

    def click_workflow_btn(self, btn_selector):
        self._clear_overlays()
        self.page.click(btn_selector)
        try:
            self.page.wait_for_selector(".swal2-container", timeout=5000)
            self.page.locator(".swal2-confirm").click()
            self.page.wait_for_selector(".swal2-container", state="hidden", timeout=3000)
        except Exception:
            pass
        self.page.wait_for_selector("table#excel-table", timeout=8000)

    def get_workflow_status(self, farmer_name):
        rows = self.page.locator("table#excel-table tbody tr")
        for i in range(rows.count()):
            row = rows.nth(i)
            if farmer_name in row.inner_text():
                cell = row.locator("td[class*='cdk-column-workflow_status']")
                return cell.text_content().strip() if cell.count() > 0 else ""
        return ""

    def verify_view_popup_read_only(self):
        buttons = self.page.locator(".popup-footer button")
        texts = [buttons.nth(i).text_content().strip() for i in range(buttons.count())]
        assert "Submit" not in texts and "Update" not in texts, \
            "View popup must not have Submit or Update"
