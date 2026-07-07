import random
from pages.base_playwright_page import BasePlaywrightPage


class COPlaywrightPage(BasePlaywrightPage):
    URL = "https://rhythmerp.algorhythms.in/#/dynamic-screens/Company%20Onboarding"

    # ── Universal / Company Details (Step 1) ─────────────────────────────────
    COMPANY_NAME       = "xpath=//mat-form-field[.//mat-label[contains(.,'Company Name')]]//input"
    ENTITY_GROUP       = "xpath=//mat-form-field[.//mat-label[contains(.,'Entity Group')]]//mat-select"
    PARENT_NAME        = "xpath=//mat-form-field[.//mat-label[contains(.,'Parent Name')]]//mat-select"
    COMPANY_LINKED     = "xpath=//mat-form-field[.//mat-label[contains(.,'Company Linked')]]//mat-select"
    # LEVEL — skip (auto-patched by ERP)
    OWNERSHIP_STATUS   = "xpath=//mat-form-field[.//mat-label[contains(.,'Ownership Status')]]//mat-select"
    COMPANY_CODE       = "xpath=//mat-form-field[.//mat-label[contains(.,'Company Code')]]//input"
    COMPANY_SHORT_NAME = "xpath=//mat-form-field[.//mat-label[contains(.,'Company Short Name')]]//input"
    CONTACT_NAME       = "xpath=//mat-form-field[.//mat-label[contains(.,'Contact Name')]]//input"
    COMPANY_BACKGROUND = "xpath=//mat-form-field[.//mat-label[contains(.,'Company Background')]]//textarea"
    EMAIL              = "xpath=//mat-form-field[.//mat-label[contains(.,'Email')]]//input"
    MOBILE_NUMBER      = "xpath=//mat-form-field[.//mat-label[contains(.,'Mobile Number')]]//input"
    PAN                = "xpath=//mat-form-field[.//mat-label[contains(.,'PAN')]]//input"
    TAN                = "xpath=//mat-form-field[.//mat-label[contains(.,'TAN')]]//input"
    GSTIN              = "xpath=//mat-form-field[.//mat-label[contains(.,'GSTIN')]]//input"
    CIN                = "xpath=//mat-form-field[.//mat-label[contains(.,'CIN')]]//input"
    BASE_CURRENCY      = "xpath=//mat-form-field[.//mat-label[contains(.,'Base Currency')]]//mat-select"
    PLAN_TYPE          = "xpath=//mat-form-field[.//mat-label[contains(.,'Plan Type')]]//mat-select"
    NATIVE_LANGUAGE    = "xpath=//mat-form-field[.//mat-label[contains(.,'Native Language')]]//mat-select"

    # ── Promoters Details (Step 2) ────────────────────────────────────────────
    PROMOTER_NAME   = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Name']]//input"
    PROMOTER_REMARK = "xpath=//mat-form-field[.//mat-label[contains(.,'Remark')]]//textarea"

    # ── Address Details (Step 3) ──────────────────────────────────────────────
    ADDR_ADDRESS_TYPE = "xpath=//mat-form-field[.//mat-label[contains(.,'Address Type')]]//mat-select"
    ADDR_COUNTRY      = "xpath=//mat-form-field[.//mat-label[contains(.,'Country')]]//mat-select"
    ADDR_STATE        = "xpath=//mat-form-field[.//mat-label[contains(.,'State')]]//mat-select"
    ADDR_DISTRICT     = "xpath=//mat-form-field[.//mat-label[contains(.,'District')]]//mat-select"
    ADDR_TALUKA       = "xpath=//mat-form-field[.//mat-label[contains(.,'Taluka')]]//mat-select"
    ADDR_ADDRESS      = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Address']]//input"
    ADDR_PIN_CODE     = "xpath=//mat-form-field[.//mat-label[contains(.,'Pin Code')]]//mat-select"

    # ── Business Activities (Step 4) ──────────────────────────────────────────
    BIZ_MODEL  = "xpath=//mat-form-field[.//mat-label[contains(.,'Business Model')]]//input"
    BIZ_MARKET = "xpath=//mat-form-field[.//mat-label[contains(.,'Market Linkages')]]//input"
    BIZ_LINE   = "xpath=//mat-form-field[.//mat-label[contains(.,'Line of Business')]]//input"
    BIZ_ADDL   = "xpath=//mat-form-field[.//mat-label[contains(.,'Additional Business Activities')]]//input"

    # ── Infrastructure Details (Step 5) ───────────────────────────────────────
    INFRA_TYPE      = "xpath=//mat-form-field[.//mat-label[contains(.,'Infrastructure Type')]]//mat-select"
    INFRA_LOCATION  = "xpath=//mat-form-field[.//mat-label[contains(.,'Infrastructure Location')]]//input"
    INFRA_OWNERSHIP = "xpath=//mat-form-field[.//mat-label[contains(.,'Ownership Type')]]//mat-select"

    SUBMIT_BTN   = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Submit')]"
    CANCEL_BTN   = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Cancel')]"
    SEARCH_INPUT = "#erpSearchInput"

    # ── low-level helpers ─────────────────────────────────────────────────────

    def _clear_overlays(self):
        self.page.evaluate(
            "document.querySelectorAll('.cdk-overlay-backdrop').forEach(el => el.remove())"
        )

    def _select_mat_option(self, selector, nth=0):
        trigger = self.page.locator(selector).nth(nth)
        trigger.click(force=True)
        self.page.wait_for_selector(".mat-mdc-select-panel", timeout=5000)
        self.page.locator(".mat-mdc-select-panel mat-option").first.wait_for(state="visible", timeout=3000)
        self.page.evaluate("document.querySelector('.mat-mdc-select-panel mat-option')?.click()")
        try:
            self.page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=5000)
        except Exception:
            trigger.click(force=True)
            self.page.wait_for_timeout(300)
        self.page.wait_for_timeout(300)

    def _select_mat_option_by_text(self, selector, text, nth=0):
        trigger = self.page.locator(selector).nth(nth)
        trigger.click(force=True)
        self.page.wait_for_selector(".mat-mdc-select-panel", timeout=5000)
        opt = self.page.locator(f".mat-mdc-select-panel mat-option:has-text('{text}')")
        opt.first.wait_for(state="visible", timeout=3000)
        opt.first.click(force=True)
        try:
            self.page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=5000)
        except Exception:
            trigger.click(force=True)
            self.page.wait_for_timeout(300)
        self.page.wait_for_timeout(300)

    def _select_random_mat_option(self, selector, nth=0):
        trigger = self.page.locator(selector).nth(nth)
        trigger.click(force=True)
        self.page.wait_for_selector(".mat-mdc-select-panel", timeout=5000)
        options = self.page.locator(".mat-mdc-select-panel mat-option").all()
        if options:
            random.choice(options).click(force=True)
        try:
            self.page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=5000)
        except Exception:
            # click the trigger again to close the panel — never Escape (closes the form)
            trigger.click(force=True)
            self.page.wait_for_timeout(300)
        self.page.wait_for_timeout(300)

    def _add_row(self):
        # Click the first visible add-row-btn — inactive steps are display:none so
        # only the current step's button is visible
        btns = self.page.locator("button.add-row-btn")
        for i in range(btns.count()):
            btn = btns.nth(i)
            if btn.is_visible():
                btn.click(force=True)
                break
        self.page.wait_for_timeout(800)

    def _click_next(self):
        self.page.evaluate("""
            const btns = document.querySelectorAll('button.mat-stepper-next');
            for (const btn of btns) {
                if (btn.offsetParent !== null) {
                    btn.scrollIntoView({block:'center'}); btn.click(); break;
                }
            }
        """)
        self.page.wait_for_timeout(800)

    def _click_back(self):
        self.page.evaluate("""
            const btns = document.querySelectorAll('button.mat-stepper-previous');
            for (const btn of btns) {
                if (btn.offsetParent !== null) {
                    btn.scrollIntoView({block:'center'}); btn.click(); break;
                }
            }
        """)
        self.page.wait_for_timeout(600)

    def _delete_extra_address_rows(self):
        self.page.wait_for_timeout(500)
        while True:
            del_btns = self.page.locator("mat-icon:text('delete_outline')").all()
            visible = [b for b in del_btns if b.is_visible()]
            if len(visible) <= 2:
                break
            try:
                visible[-1].click(force=True)
                self.page.wait_for_timeout(400)
            except Exception:
                break

    # ── step fill helpers ─────────────────────────────────────────────────────

    def _fill_company_details(self, data):
        for selector, key, default in [
            (self.COMPANY_NAME,       "company_name",  "Test Company"),
            (self.COMPANY_CODE,       "company_code",  "TC01"),
            (self.COMPANY_SHORT_NAME, "short_name",    "TC"),
            (self.CONTACT_NAME,       "contact_name",  "Test Contact"),
            (self.EMAIL,              "email",         "test@testmail.com"),
            (self.MOBILE_NUMBER,      "mobile",        "9876543210"),
            (self.PAN,                "pan",           "ABCDE1234F"),
            (self.TAN,                "tan",           "ABCD12345E"),
            (self.GSTIN,              "gstin",         "29ABCDE1234F1Z5"),
            (self.CIN,                "cin",           "U12345MH2024PTC123456"),
        ]:
            try:
                loc = self.page.locator(selector).first
                loc.click(force=True)
                loc.fill(data.get(key, default))
                loc.press("Tab")
            except Exception:
                pass

        try:
            loc = self.page.locator(self.COMPANY_BACKGROUND).first
            loc.click(force=True)
            loc.fill(data.get("background", "Automated test company background."))
        except Exception:
            pass

        for selector in [self.ENTITY_GROUP, self.PARENT_NAME, self.COMPANY_LINKED]:
            try:
                self._select_random_mat_option(selector)
            except Exception:
                pass

        for selector in [self.OWNERSHIP_STATUS, self.PLAN_TYPE, self.NATIVE_LANGUAGE]:
            try:
                self._select_mat_option(selector)
            except Exception:
                pass

        # Base Currency always "India - INR"
        try:
            self._select_mat_option_by_text(self.BASE_CURRENCY, "India - INR")
        except Exception:
            pass

    def _fill_address_row(self, row_index, address_text, address_type):
        self.page.wait_for_timeout(800)
        self._select_mat_option_by_text(self.ADDR_ADDRESS_TYPE, address_type, nth=row_index)
        self.page.wait_for_timeout(800)
        try:
            self._select_mat_option_by_text(self.ADDR_COUNTRY, "India", nth=row_index)
        except Exception:
            pass
        self.page.wait_for_timeout(800)
        for sel in [self.ADDR_STATE, self.ADDR_DISTRICT, self.ADDR_TALUKA]:
            try:
                self._select_random_mat_option(sel, nth=row_index)
            except Exception:
                pass
            self.page.wait_for_timeout(800)
        try:
            loc = self.page.locator(self.ADDR_ADDRESS).nth(row_index)
            loc.click(force=True)
            loc.fill(address_text)
            loc.press("Tab")
        except Exception:
            pass
        self.page.wait_for_timeout(800)
        try:
            self._select_random_mat_option(self.ADDR_PIN_CODE, nth=row_index)
        except Exception:
            pass

    def _fill_address_rows(self, data):
        self._fill_address_row(0, data.get("address1", "101 Shivaji Path Pune"), "Registered Address")
        self._add_row()
        self._fill_address_row(1, data.get("address2", "202 MG Road Kolhapur"), "Corporate Address")

    def _fill_promoters(self, data):
        self._add_row()
        try:
            loc = self.page.locator(self.PROMOTER_NAME).first
            loc.click(force=True)
            loc.fill(data.get("company_name", "Test Promoter"))
            loc.press("Tab")
        except Exception:
            pass
        try:
            loc = self.page.locator(self.PROMOTER_REMARK).first
            loc.click(force=True)
            loc.fill("Founder")
        except Exception:
            pass

    def _fill_business_activities(self):
        self._add_row()
        for selector, default in [
            (self.BIZ_MODEL,  "Direct Sales"),
            (self.BIZ_MARKET, "Local Market"),
            (self.BIZ_LINE,   "Agro Products"),
            (self.BIZ_ADDL,   "Processing"),
        ]:
            try:
                loc = self.page.locator(selector).first
                loc.click(force=True)
                loc.fill(default)
                loc.press("Tab")
            except Exception:
                pass

    def _fill_infrastructure(self):
        self._add_row()
        for sel in [self.INFRA_TYPE, self.INFRA_OWNERSHIP]:
            try:
                self._select_mat_option(sel)
            except Exception:
                pass
        try:
            loc = self.page.locator(self.INFRA_LOCATION).first
            loc.click(force=True)
            loc.fill("Pune Industrial Area")
            loc.press("Tab")
        except Exception:
            pass

    # ── navigation ────────────────────────────────────────────────────────────

    def navigate_to_page(self):
        try:
            if "Company%20Onboarding" in self.page.url or "Company Onboarding" in self.page.url:
                self.page.reload()
            else:
                self.page.goto(self.URL)
        except Exception:
            self.page.goto(self.URL)
        try:
            self.page.wait_for_selector("table#excel-table, div.empty-state", timeout=10000)
        except Exception:
            self.page.reload()
            self.page.wait_for_selector("table#excel-table, div.empty-state", timeout=15000)

    def open_add_form(self):
        try:
            self.page.click("button.erp-add-btn")
        except Exception:
            self.page.evaluate("""
                var btn = document.querySelector('button.erp-add-btn');
                if (btn) { btn.scrollIntoView({block:'center'}); btn.click(); }
            """)
        self.page.wait_for_selector(self.COMPANY_NAME, timeout=8000)

    # ── form fill ─────────────────────────────────────────────────────────────

    def fill_form(self, data):
        self._fill_company_details(data)
        self._click_next()                   # → Promoters Details
        self._fill_promoters(data)
        self._click_next()                   # → Address Details
        self._fill_address_rows(data)
        self._click_next()                   # → Business Activities
        self._fill_business_activities()
        self._click_next()                   # → Infrastructure Details
        self._fill_infrastructure()
        self._click_back()                   # back to Infrastructure for submit

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
            self.page.evaluate("document.querySelector('.swal2-confirm')?.click()")
            self.page.wait_for_selector(".swal2-container", state="hidden", timeout=3000)
            if "validation" in title or "failed" in title or "error" in title:
                labels = self.page.locator("mat-form-field.ng-invalid mat-label").all_text_contents()
                raise AssertionError(f"Validation failed — invalid fields: {labels}")
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

    def create_record(self, data):
        self.open_add_form()
        self.fill_form(data)
        self._clear_overlays()
        self.page.click(self.SUBMIT_BTN)
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

    # ── search / table ────────────────────────────────────────────────────────

    def search_company(self, company_name):
        inp = self.page.locator(self.SEARCH_INPUT)
        if not inp.is_visible():
            self.page.evaluate("""
                var btn = document.querySelector('button[mattooltip="Search"]');
                if (btn) { btn.scrollIntoView({block:'center'}); btn.click(); }
            """)
            self.page.wait_for_timeout(800)
        inp.wait_for(state="visible", timeout=5000)
        inp.fill(company_name)
        self.page.keyboard.press("Enter")
        self.page.wait_for_timeout(1500)

    def is_company_in_table(self, company_name):
        for _ in range(10):
            rows = self.page.locator("table#excel-table tbody tr")
            for i in range(rows.count()):
                if company_name in rows.nth(i).inner_text():
                    return True
            self.page.wait_for_timeout(300)
        return False

    def verify_company_exists(self, company_name):
        assert self.is_company_in_table(company_name), \
            f"Company '{company_name}' not found in table"

    def _find_row_index(self, company_name):
        rows = self.page.locator("table#excel-table tbody tr")
        for i in range(rows.count()):
            if company_name in rows.nth(i).inner_text():
                return i
        raise AssertionError(f"Company '{company_name}' not found in table")

    def click_view_button(self, company_name):
        self.click_row_action(self._find_row_index(company_name), "View")

    def click_history_button(self, company_name):
        self.click_row_action(self._find_row_index(company_name), "History")
        self.page.wait_for_timeout(1000)

    def verify_view_popup_read_only(self):
        buttons = self.page.locator(".popup-footer button")
        texts = [buttons.nth(i).text_content().strip() for i in range(buttons.count())]
        assert "Submit" not in texts and "Update" not in texts, \
            "View popup must not have Submit or Update"
