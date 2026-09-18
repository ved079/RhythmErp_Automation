import random
from pages.base_playwright_page import BasePlaywrightPage


class FarmerPage(BasePlaywrightPage):
    URL = "https://rhythmerp.algorhythms.in/#/dynamic-screens/Farmer/Farmer"

    SUBMIT_BTN  = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Submit')]"
    UPDATE_BTN  = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Update')]"
    CANCEL_BTN  = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Cancel')]"
    SEARCH_INPUT = "#erpSearchInput"

    # Basic
    FARMER_NAME     = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Farmer Name']]//input"
    EMAIL           = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Email']]//input"
    PHONE_NUMBER    = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Phone Number']]//input"
    FARMER_CATEGORY = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Farmer Category']]//mat-select"

    # Address row fields (use nth for row index)
    ADDR_TYPE     = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Address Type']]//mat-select"
    ADDR_STATE    = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='State']]//mat-select"
    ADDR_DISTRICT = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='District']]//mat-select"
    ADDR_TALUKA   = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Taluka']]//mat-select"
    ADDR_VILLAGE  = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Village']]//mat-select"
    ADDR_PIN_CODE = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Pin Code']]//mat-select"
    ADDR_ADDRESS  = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Address']]//input"
    SAME_AS_ABOVE = "mat-checkbox:has-text('Same as Above') .mdc-label"

    # Additional Details
    GENDER   = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Gender']]//mat-select"
    CATEGORY = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Category']]//mat-select"
    RELIGION = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Religion']]//mat-select"

    # Family Details
    MEMBER_NAME = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Member Name']]//input"

    # Other Details
    EDUCATION_QUAL    = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Education Qualification']]//mat-select"
    ELECTRICITY_AVAIL = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Electricity Availability']]//mat-select"

    # Land & Crop
    FARM_NAME   = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Farm Name']]//input"
    NO_OF_OWNER = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='No Of Owner']]//input"

    # KYC
    KYC_DOCUMENT = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='KYC Document']]//mat-select"
    KYC_NUMBER   = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='KYC Number']]//input"

    # Vehicle / Income / Irrigation
    VEHICLE_TYPE         = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Vehicle Type']]//mat-select"
    SOURCE_OF_INCOME     = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Source of Income']]//mat-select"
    INCOME_BRACKET       = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Income Bracket']]//mat-select"
    SOURCE_OF_IRRIGATION = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Source of Irrigation']]//mat-select"

    # Bank
    BANK_NAME        = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Bank Name']]//input"
    BANK_BRANCH      = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Branch']]//input"
    BANK_IFSC        = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='IFSC Code']]//input"
    BANK_ACCOUNT_TYPE= "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Account Type']]//mat-select"
    BANK_HOLDER_NAME = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Account Holder Name']]//input"
    BANK_ACCOUNT_NO  = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Account Number']]//input"
    BANK_PROOF       = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Bank Proof']]//mat-select"

    # ── mat-select helpers (proven pattern) ──────────────────────────────────
    def _select_mat_option_by_text(self, selector, text, nth=0):
        self.page.locator(selector).nth(nth).click(force=True)
        self.page.wait_for_selector(".mat-mdc-select-panel", timeout=5000)
        options = self.page.locator(
            ".mat-mdc-select-panel mat-option span.mdc-list-item__primary-text"
        ).filter(has_text=text)
        matched = None
        for opt in options.all():
            if opt.inner_text().strip() == text:
                matched = opt
                break
        if matched:
            matched.click(force=True)
        else:
            self.page.locator(".mat-mdc-select-panel mat-option").filter(has_text=text).first.click(force=True)
        try:
            self.page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=3000)
        except Exception:
            pass
        self.page.wait_for_timeout(100)

    def _select_random_mat_option(self, selector, nth=0):
        self.page.locator(selector).nth(nth).click(force=True)
        self.page.wait_for_selector(".mat-mdc-select-panel", timeout=5000)
        options = self.page.locator(".mat-mdc-select-panel mat-option:not(.dd-clear-option)").all()
        if options:
            random.choice(options).click(force=True)
        try:
            self.page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=3000)
        except Exception:
            pass
        self.page.wait_for_timeout(200)

    def _try_select_random_mat_option(self, selector, nth=0):
        self.page.locator(selector).nth(nth).click(force=True)
        try:
            self.page.wait_for_selector(".mat-mdc-select-panel", timeout=3000)
        except Exception:
            return
        options = self.page.locator(".mat-mdc-select-panel mat-option:not(.dd-clear-option)").all()
        if options:
            random.choice(options).click(force=True)
        try:
            self.page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=3000)
        except Exception:
            pass
        self.page.wait_for_timeout(200)

    def _fill_text(self, selector, value, nth=0):
        loc = self.page.locator(selector).nth(nth)
        loc.click(force=True)
        loc.fill(str(value))
        loc.press("Tab")

    def _click_next(self):
        self.page.evaluate("""
            const btns = document.querySelectorAll('button[matsteppernext]');
            for (const btn of btns) {
                if (btn.offsetParent !== null && getComputedStyle(btn).display !== 'none') {
                    btn.scrollIntoView({block: 'center'});
                    btn.click();
                    break;
                }
            }
        """)
        self.page.wait_for_timeout(500)

    def _clear_overlays(self):
        self.page.evaluate("document.querySelectorAll('.cdk-overlay-backdrop').forEach(el => el.remove())")

    def _add_row(self):
        self.page.locator("button.add-row-btn:visible").last.click()
        self.page.wait_for_timeout(800)

    # ── Section fill helpers ──────────────────────────────────────────────────

    def _fill_address_row_0(self, data):
        """Fill first address row: Permanent Address, State cascade, Address field."""
        self._select_mat_option_by_text(self.ADDR_TYPE, "Permanent Address", nth=0)
        self._select_mat_option_by_text(self.ADDR_STATE, data.get("state", "Maharashtra"), nth=0)
        self.page.locator(self.ADDR_DISTRICT).nth(0).wait_for(state="visible", timeout=10000)
        self._select_random_mat_option(self.ADDR_DISTRICT, nth=0)
        self.page.locator(self.ADDR_TALUKA).nth(0).wait_for(state="visible", timeout=10000)
        self._select_random_mat_option(self.ADDR_TALUKA, nth=0)
        self._try_select_random_mat_option(self.ADDR_VILLAGE, nth=0)
        self._try_select_random_mat_option(self.ADDR_PIN_CODE, nth=0)
        self._fill_text(self.ADDR_ADDRESS, data.get("address", "101 MG Road, Pune"), nth=0)

    def _add_current_address_same_as_above(self):
        """Add 2nd address row, set type to Current, click Same as Above."""
        self._add_row()
        self.page.locator(self.ADDR_TYPE).nth(1).wait_for(state="visible", timeout=10000)
        self._select_mat_option_by_text(self.ADDR_TYPE, "Current Address", nth=1)
        self.page.wait_for_timeout(500)
        self.page.locator(self.SAME_AS_ABOVE).nth(1).click()
        self.page.wait_for_timeout(300)

    def _fill_bank_section(self, data):
        self._fill_text(self.BANK_NAME, data.get("bank_name", "HDFC Bank"))
        self._fill_text(self.BANK_BRANCH, data.get("bank_branch", "Pune Branch"))
        self._fill_text(self.BANK_IFSC, data.get("bank_ifsc", "SBIN0807508"))
        self._select_mat_option_by_text(self.BANK_ACCOUNT_TYPE, data.get("account_type", "Current"))
        self._fill_text(self.BANK_HOLDER_NAME, data.get("bank_holder", "Account Holder"))
        self._fill_text(self.BANK_ACCOUNT_NO, data.get("bank_account", "100000000498"))
        self._select_mat_option_by_text(self.BANK_PROOF, data.get("bank_proof", "Cancelled Cheque"))
        self._clear_overlays()

    def _fill_additional_details_section(self, gender_nth=0):
        self._select_random_mat_option(self.GENDER, nth=gender_nth)
        self.page.locator(self.CATEGORY).nth(0).wait_for(state="visible", timeout=5000)
        self._select_random_mat_option(self.CATEGORY, nth=0)
        self.page.locator(self.RELIGION).nth(0).wait_for(state="visible", timeout=5000)
        self._select_random_mat_option(self.RELIGION, nth=0)

    def _fill_family_section(self):
        self._fill_text(self.MEMBER_NAME, "Family Member")
        self._select_random_mat_option(self.GENDER, nth=0)

    def _fill_other_details_section(self):
        self._select_random_mat_option(self.EDUCATION_QUAL)
        self.page.locator(self.ELECTRICITY_AVAIL).wait_for(state="visible", timeout=5000)
        self._select_random_mat_option(self.ELECTRICITY_AVAIL)

    def _fill_land_section(self):
        self._fill_text(self.FARM_NAME, "Soyabean Farm", nth=0)
        self._fill_text(self.NO_OF_OWNER, "1")

    def _fill_crop_section(self):
        # Farm Name nth(1) — Land's Farm Name is still in DOM at nth(0)
        self._fill_text(self.FARM_NAME, "Soyabean Farm", nth=1)

    def _fill_kyc_section(self, data):
        from pages.registration.modules.farmer.data.farmer_data import generate_kyc_number
        pan = generate_kyc_number("PAN")
        aadhar = generate_kyc_number("AADHAR")
        self._select_mat_option_by_text(self.KYC_DOCUMENT, "PAN", nth=0)
        self._fill_text(self.KYC_NUMBER, pan, nth=0)
        self._add_row()
        self._select_mat_option_by_text(self.KYC_DOCUMENT, "AADHAR", nth=1)
        self._fill_text(self.KYC_NUMBER, aadhar, nth=1)

    def _fill_vehicle_section(self):
        self._select_random_mat_option(self.VEHICLE_TYPE)

    def _fill_income_section(self):
        self._select_random_mat_option(self.SOURCE_OF_INCOME)
        self._select_random_mat_option(self.INCOME_BRACKET)

    def _fill_irrigation_section(self):
        self._select_random_mat_option(self.SOURCE_OF_IRRIGATION)

    # ── Main fill_form ────────────────────────────────────────────────────────

    def fill_form(self, data, category=None):
        category = category or data.get("farmer_category", "Walk-in Farmer")

        # Basic fields
        self._fill_text(self.FARMER_NAME, data.get("farmer_name", "Test Farmer"))
        self._fill_text(self.EMAIL, data.get("email", "test@testmail.com"))
        self._fill_text(self.PHONE_NUMBER, data.get("phone_number", "9876543210"))
        self._select_mat_option_by_text(self.FARMER_CATEGORY, category)
        self.page.wait_for_timeout(300)

        # Address (step 1 for all categories)
        self._fill_address_row_0(data)
        self._add_current_address_same_as_above()

        if category == "Walk-in Farmer":
            # Next → Bank → Submit
            self._click_next()
            self._fill_bank_section(data)

        elif category == "FPC Member":
            # Next → Additional → Land → Crop → KYC → Bank → Submit
            self._click_next()
            self._fill_additional_details_section(gender_nth=0)
            self._click_next()
            self._fill_land_section()
            self._click_next()
            self._fill_crop_section()
            self._click_next()
            self._fill_kyc_section(data)
            self._click_next()
            self._fill_bank_section(data)

        elif category == "Borrower Farmer":
            # Next → Family → Additional → Other → Land → Crop → KYC → Vehicle → Income → Bank → Irrigation → Award → Loan → Submit
            self._click_next()
            self._fill_family_section()
            self._click_next()
            # Gender nth(1) because Family's Gender is still in DOM at nth(0)
            self._fill_additional_details_section(gender_nth=1)
            self._click_next()
            self._fill_other_details_section()
            self._click_next()
            self._fill_land_section()
            self._click_next()
            self._fill_crop_section()
            self._click_next()
            self._fill_kyc_section(data)
            self._click_next()
            self._fill_vehicle_section()
            self._click_next()
            self._fill_income_section()
            self._click_next()
            self._fill_bank_section(data)
            self._click_next()
            self._fill_irrigation_section()
            self._click_next()
            # Award Details — leave empty
            self._click_next()
            # Loan Details — leave empty

    def submit(self):
        self._clear_overlays()
        self.page.click(self.SUBMIT_BTN)

    def close_popup(self):
        self._clear_overlays()
        try:
            self.page.locator(self.CANCEL_BTN).click()
        except Exception:
            self.page.get_by_role("button", name="close").click()

    def handle_success_alert(self):
        try:
            self.page.wait_for_selector(".swal2-container", timeout=5000)
            title = (self.page.locator("#swal2-title").text_content() or "").strip().lower()
            body  = (self.page.locator("#swal2-html-container").text_content() or "").strip()
            self.page.evaluate("document.querySelector('.swal2-confirm')?.click()")
            self.page.wait_for_selector(".swal2-container", state="hidden", timeout=3000)
            if "validation" in title or "failed" in title or "error" in title:
                labels = self.page.locator("mat-form-field.ng-invalid mat-label").all_text_contents()
                raise AssertionError(f"Validation failed — invalid fields: {labels} — body: '{body}'")
        except AssertionError:
            raise
        except Exception:
            pass

    def create_record(self, data, category=None):
        self.open_add_form()
        self.fill_form(data, category=category)
        self.submit()
        self.handle_success_alert()

    # ── Navigation ────────────────────────────────────────────────────────────

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
        self.page.locator("button.erp-add-btn").click()
        self.page.wait_for_selector(self.FARMER_NAME, timeout=8000)

    # ── Search / table helpers ────────────────────────────────────────────────

    def search_farmer(self, farmer_name):
        inp = self.page.locator(self.SEARCH_INPUT)
        if not inp.is_visible():
            self.page.evaluate("""
                var btn = document.querySelector('button[mattooltip="Search"]');
                if (btn) { btn.scrollIntoView({block:'center'}); btn.click(); }
            """)
            self.page.wait_for_timeout(500)
        inp.wait_for(state="visible", timeout=5000)
        inp.fill(farmer_name)
        self.page.keyboard.press("Enter")
        self.page.wait_for_timeout(1500)

    def verify_farmer_exists(self, farmer_name):
        rows = self.page.locator("table#excel-table tbody tr")
        for i in range(rows.count()):
            if farmer_name in rows.nth(i).inner_text():
                return
        raise AssertionError(f"Farmer '{farmer_name}' not found in table")

    def _find_row_index(self, farmer_name):
        rows = self.page.locator("table#excel-table tbody tr")
        for i in range(rows.count()):
            if farmer_name in rows.nth(i).inner_text():
                return i
        raise AssertionError(f"Farmer '{farmer_name}' not found in table")

    def click_view_button(self, farmer_name):
        self.search_farmer(farmer_name)
        self.click_row_action(self._find_row_index(farmer_name), "View")

    def click_edit_button(self, farmer_name):
        self.search_farmer(farmer_name)
        self.click_row_action(self._find_row_index(farmer_name), "Edit")
        self.page.wait_for_selector(self.FARMER_NAME, timeout=5000)

    def get_view_field_value(self, farmer_name, field_label):
        self.click_view_button(farmer_name)
        self.page.wait_for_selector(
            f"xpath=//mat-label[contains(.,'{field_label}')]/ancestor::mat-form-field//input",
            timeout=8000,
        )
        value = self.page.locator(
            f"xpath=//mat-label[contains(.,'{field_label}')]/ancestor::mat-form-field//input"
        ).first.input_value()
        self.force_close_popup()
        self.page.wait_for_timeout(300)
        return value

    def get_first_farmer_name(self):
        self.click_row_action(0, "View")
        self.page.wait_for_selector(self.FARMER_NAME, timeout=8000)
        name = self.page.locator(self.FARMER_NAME).input_value()
        self.force_close_popup()
        self.page.wait_for_timeout(300)
        return name

    def get_history_entry_count(self, farmer_name):
        self.search_farmer(farmer_name)
        idx = self._find_row_index(farmer_name)
        self.page.locator("button.erp-row-trigger").nth(idx).click()
        self.page.wait_for_selector(".mat-mdc-menu-panel", timeout=8000)
        self.page.locator(
            ".mat-mdc-menu-panel button.mat-mdc-menu-item:has(.erp-menu-title:text-is('History'))"
        ).click()
        self.page.wait_for_timeout(1000)
        if self.page.locator(".empty-state").is_visible():
            count = 0
        else:
            count = self.page.locator("table#excel-table").nth(1).locator("tbody tr").count()
        self.force_close_popup()
        self.page.wait_for_timeout(300)
        return count

    def click_edit_button(self, farmer_name):
        self.search_farmer(farmer_name)
        idx = self._find_row_index(farmer_name)
        self.page.locator("button.erp-row-trigger").nth(idx).click()
        self.page.wait_for_selector(".mat-mdc-menu-panel", timeout=8000)
        self.page.locator(
            ".mat-mdc-menu-panel button.mat-mdc-menu-item:has(.erp-menu-title:text-is('Edit'))"
        ).click()
        self.page.wait_for_selector(self.FARMER_NAME, timeout=8000)

    def click_update(self):
        self.page.locator(self.UPDATE_BTN).click()

    def export_master(self):
        self.page.locator("button.mat-mdc-menu-trigger.erp-outline-btn").click()
        self.page.wait_for_selector(".mat-mdc-menu-panel", timeout=5000)
        with self.page.expect_download() as dl:
            self.page.locator(
                ".mat-mdc-menu-panel button.mat-mdc-menu-item:has(.erp-menu-title:text-is('Export Master'))"
            ).click()
        return dl.value

    def set_page_size(self, size):
        self.page.evaluate(f"""
            var sel = document.querySelector('mat-select[aria-label="Items per page:"]');
            if (!sel) sel = document.querySelector('.mat-mdc-paginator mat-select');
            if (sel) sel.dispatchEvent(new MouseEvent('click', {{bubbles: true}}));
        """)
        try:
            self.page.wait_for_selector(".mat-mdc-select-panel", timeout=3000)
            opts = self.page.locator(".mat-mdc-select-panel mat-option").all()
            for opt in opts:
                if opt.inner_text().strip() == size:
                    opt.click(force=True)
                    break
            else:
                if opts:
                    opts[-1].click(force=True)
        except Exception:
            pass
        self.page.wait_for_timeout(800)

    def read_table_data(self, cols):
        rows = self.page.locator("table#excel-table tbody tr")
        data = []
        for i in range(rows.count()):
            row = rows.nth(i)
            cells = row.locator("td")
            row_data = tuple(
                cells.nth(c).inner_text().strip() if cells.count() > c else ""
                for c in cols
            )
            if any(row_data):
                data.append(row_data)
        return data
