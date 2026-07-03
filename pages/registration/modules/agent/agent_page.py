from pages.base_playwright_page import BasePlaywrightPage


class AgentPage(BasePlaywrightPage):
    URL = "https://rhythmerp.algorhythms.in/#/dynamic-screens/Agent/Agent"

    # Step 1 — basic info
    AGENT_NAME   = "xpath=//mat-form-field[.//mat-label[contains(.,'Agent Name')]]//input"
    PHONE_NUMBER = "xpath=//mat-form-field[.//mat-label[contains(.,'Phone Number')]]//input"
    EMAIL        = "xpath=//mat-form-field[.//mat-label[contains(.,'Email')]]//input"

    # Step 3 — payment details
    PAYMENT_TERMS            = "xpath=//mat-form-field[.//mat-label[contains(.,'Payment Terms')]]//mat-select"
    PREFERRED_PAYMENT_METHOD = "xpath=//mat-form-field[.//mat-label[contains(.,'Preferred Payment Method')]]//mat-select"

    # Grid row selector (pre-existing clickable rows)
    GRID_ROW = "xpath=//tbody/tr[contains(@mattooltip,'Click to edit row details')]"

    # Address popup fields (open by clicking address grid row)
    ADDR_COUNTRY      = "xpath=//mat-form-field[.//mat-label[contains(.,'Country')]]//mat-select"
    ADDR_STATE        = "xpath=//mat-form-field[.//mat-label[contains(.,'State')]]//mat-select"
    ADDR_DISTRICT     = "xpath=//mat-form-field[.//mat-label[contains(.,'District')]]//mat-select"
    ADDR_TALUKA       = "xpath=//mat-form-field[.//mat-label[contains(.,'Taluka')]]//mat-select"
    ADDR_VILLAGE      = "xpath=//mat-form-field[.//mat-label[contains(.,'Village')]]//mat-select"
    ADDR_ADDRESS      = "xpath=//mat-form-field[.//mat-label[contains(.,'Address')]]//input"
    ADDR_PIN_CODE     = "xpath=//mat-form-field[.//mat-label[contains(.,'Pin Code')]]//mat-select"
    SAME_AS_ABOVE     = "xpath=//mat-checkbox[.//*[contains(.,'Same as Above')]]"

    # Bank popup fields (open by clicking bank grid row)
    BANK_NAME_INPUT    = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Bank Name']]//input"
    BANK_BRANCH        = "xpath=//mat-form-field[.//mat-label[contains(.,'Branch')]]//input"
    BANK_IFSC          = "xpath=//mat-form-field[.//mat-label[contains(.,'IFSC Code')]]//input"
    BANK_ACCOUNT_TYPE  = "xpath=//mat-form-field[.//mat-label[contains(.,'Account Type')]]//mat-select"
    BANK_HOLDER_NAME   = "xpath=//mat-form-field[.//mat-label[contains(.,'Account Holder Name')]]//input"
    BANK_ACCOUNT_NO    = "xpath=//mat-form-field[.//mat-label[contains(.,'Account Number')]]//input"
    BANK_PROOF         = "xpath=//mat-form-field[.//mat-label[contains(.,'Bank Proof')]]//mat-select"

    SAVE_BTN   = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Save')]"
    SUBMIT_BTN = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Submit')]"
    CANCEL_BTN = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Cancel')]"
    NEXT_BTN   = "xpath=//div[contains(@class,'step-shell-footer')]//button[contains(.,'Next')]"
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

    def _click_next(self):
        # Click the Next button inside the currently active (visible) stepper step
        self.page.evaluate("""
            const btns = document.querySelectorAll('button.mat-stepper-next');
            for (const btn of btns) {
                const content = btn.closest('.mat-horizontal-stepper-content, .step-shell');
                if (content && !content.classList.contains('mat-horizontal-stepper-content-inactive')
                    && getComputedStyle(content).display !== 'none') {
                    btn.click();
                    break;
                }
            }
            // fallback: click first visible Next button
            if (!document.querySelector('.mat-horizontal-stepper-content:not(.mat-horizontal-stepper-content-inactive) button.mat-stepper-next')) {
                const allBtns = document.querySelectorAll('button.mat-stepper-next');
                if (allBtns.length) allBtns[0].click();
            }
        """)
        self.page.wait_for_timeout(1000)

    def _save_row_popup(self):
        self._clear_overlays()
        save = self.page.locator(self.SAVE_BTN).first
        save.wait_for(state="visible", timeout=5000)
        save.click()
        save.wait_for(state="hidden", timeout=8000)
        self.page.wait_for_timeout(500)

    def _select_mat_option_by_text(self, selector, text):
        sel = self.page.locator(selector)
        sel.wait_for(state="visible", timeout=5000)
        sel.click(force=True)
        self.page.wait_for_selector(".mat-mdc-select-panel", timeout=5000)
        opt = self.page.locator(f".mat-mdc-select-panel mat-option:has-text('{text}')")
        opt.first.wait_for(state="visible", timeout=3000)
        opt.first.click(force=True)
        self.page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=5000)
        self.page.wait_for_timeout(300)

    def _fill_address_row1(self, data):
        # Country always India
        self._select_mat_option_by_text(self.ADDR_COUNTRY, "India")
        # Remaining cascading selects — pick first available option
        for sel in [self.ADDR_STATE, self.ADDR_DISTRICT, self.ADDR_TALUKA]:
            self._select_mat_option(sel)
        # Village is optional
        try:
            self._select_mat_option(self.ADDR_VILLAGE)
        except Exception:
            pass
        # Address text
        addr = self.page.locator(self.ADDR_ADDRESS).first
        addr.wait_for(state="visible", timeout=5000)
        addr.click(force=True)
        addr.fill(data.get("address", "405 MG Road Solapur"))
        addr.press("Tab")
        # Pin Code is a mat-select
        self._select_mat_option(self.ADDR_PIN_CODE)

    def _fill_address_row2(self):
        # Second row — tick "Same as Above"
        cb = self.page.locator(self.SAME_AS_ABOVE).first
        cb.wait_for(state="visible", timeout=5000)
        cb.click(force=True)
        self.page.wait_for_timeout(300)

    def _fill_bank_row(self, data):
        for selector, key, default in [
            (self.BANK_NAME_INPUT,  "bank_name",    "HDFC Bank"),
            (self.BANK_BRANCH,      "bank_branch",  "Mumbai Main Branch"),
            (self.BANK_IFSC,        "bank_ifsc",    "SBIN0179242"),
            (self.BANK_HOLDER_NAME, "bank_holder",  "Meera Desai"),
            (self.BANK_ACCOUNT_NO,  "bank_account", "398177224327"),
        ]:
            loc = self.page.locator(selector).first
            loc.click(force=True)
            loc.fill(data.get(key, default))
            loc.press("Tab")
        self._select_mat_option(self.BANK_ACCOUNT_TYPE)
        self._select_mat_option(self.BANK_PROOF)

    def navigate_to_page(self):
        try:
            if "Agent" in self.page.url:
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
        self.page.wait_for_selector(self.AGENT_NAME, timeout=5000)

    def fill_form(self, data):
        # Page 1 — universal fields + address (no Next needed)
        if data.get("agent_name"):
            self.page.locator(self.AGENT_NAME).first.click(force=True)
            self.page.locator(self.AGENT_NAME).first.fill(data["agent_name"])
            self.page.locator(self.AGENT_NAME).first.press("Tab")
        if data.get("phone_number"):
            self.page.locator(self.PHONE_NUMBER).first.click(force=True)
            self.page.locator(self.PHONE_NUMBER).first.fill(data["phone_number"])
            self.page.locator(self.PHONE_NUMBER).first.press("Tab")
        if data.get("email"):
            self.page.locator(self.EMAIL).first.click(force=True)
            self.page.locator(self.EMAIL).first.fill(data["email"])
            self.page.locator(self.EMAIL).first.press("Tab")
        # Address rows are on the same page — inline editable
        self._fill_address_row1(data)
        self._fill_address_row2()

        # Page 2 — Payment Details
        self._click_next()
        self._select_mat_option(self.PAYMENT_TERMS)
        self.page.wait_for_timeout(300)
        self._select_mat_option(self.PREFERRED_PAYMENT_METHOD)
        self.page.wait_for_timeout(300)

        # Page 3 — Bank Details — inline editable
        self._click_next()
        self._fill_bank_row(data)
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

    def search_agent(self, agent_name):
        inp = self.page.locator(self.SEARCH_INPUT)
        if not inp.is_visible():
            self.page.evaluate("""
                var btn = document.querySelector('button[mattooltip="Search"]');
                if (btn) { btn.scrollIntoView({block:'center'}); btn.click(); }
            """)
            self.page.wait_for_timeout(800)
        inp.wait_for(state="visible", timeout=5000)
        inp.fill(agent_name)
        self.page.keyboard.press("Enter")
        self.page.wait_for_timeout(1500)

    def is_agent_in_table(self, agent_name):
        for _ in range(10):
            rows = self.page.locator("table#excel-table tbody tr")
            for i in range(rows.count()):
                if agent_name in rows.nth(i).inner_text():
                    return True
            self.page.wait_for_timeout(300)
        return False

    def verify_agent_exists(self, agent_name):
        assert self.is_agent_in_table(agent_name), f"Agent '{agent_name}' not found in table"

    def _find_row_index(self, agent_name):
        rows = self.page.locator("table#excel-table tbody tr")
        for i in range(rows.count()):
            if agent_name in rows.nth(i).inner_text():
                return i
        raise AssertionError(f"Agent '{agent_name}' not found in table")

    def click_view_button(self, agent_name):
        self.click_row_action(self._find_row_index(agent_name), "View")

    def click_history_button(self, agent_name):
        self.click_row_action(self._find_row_index(agent_name), "History")
        self.page.wait_for_timeout(1000)

    def verify_view_popup_read_only(self):
        buttons = self.page.locator(".popup-footer button")
        texts = [buttons.nth(i).text_content().strip() for i in range(buttons.count())]
        assert "Submit" not in texts and "Update" not in texts, \
            "View popup must not have Submit or Update"
