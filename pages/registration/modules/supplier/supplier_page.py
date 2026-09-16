import random
from pages.base_playwright_page import BasePlaywrightPage


class SupplierPage(BasePlaywrightPage):
    URL = "https://rhythmerp.algorhythms.in/#/dynamic-screens/Supplier/Supplier"

    # Step 1 — Universal fields
    OWNERSHIP_STATUS = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Ownership Status']]//mat-select"
    COMPANY_NAME     = "xpath=//mat-form-field[.//mat-label[contains(.,'Company Name')]]//input"
    PO_TYPE          = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='PO Type']]//mat-select"
    DEFAULT_CURRENCY = "xpath=//mat-form-field[.//mat-label[contains(.,'Default Currency')]]//mat-select"
    EMAIL            = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Email']]//input"
    PHONE_NUMBER     = "xpath=//mat-form-field[.//mat-label[contains(.,'Phone Number')]]//input"
    PAN_NUMBER       = "xpath=//mat-form-field[.//mat-label[contains(.,'PAN Number')]]//input"
    CONTACT_PERSON   = "xpath=//mat-form-field[.//mat-label[contains(.,'Contact Person Name')]]//input"

    # Step 1 — Additional Details
    TAX_REG_STATUS   = "xpath=//mat-form-field[.//mat-label[contains(.,'Tax Registration Status')]]//mat-select"
    GST_REG_TYPE     = "xpath=//mat-form-field[.//mat-label[contains(.,'Gst Registration Type')]]//mat-select"
    PAYMENT_TERMS    = "xpath=//mat-form-field[.//mat-label[contains(.,'Payment Terms')]]//mat-select"
    DELIVERY_TERMS   = "xpath=//mat-form-field[.//mat-label[contains(.,'Delivery Terms')]]//mat-select"
    MODE_OF_DELIVERY = "xpath=//mat-form-field[.//mat-label[contains(.,'Mode Of Delivery')]]//mat-select"

    # Step 2 — Address fields
    ADDR_ADDRESS_TYPE = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Address Type']]//mat-select"
    ADDR_STATE        = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='State']]//mat-select"
    ADDR_DISTRICT     = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='District']]//mat-select"
    ADDR_TALUKA       = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Taluka']]//mat-select"
    ADDR_VILLAGE      = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Village']]//mat-select"
    ADDR_ADDRESS      = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Address']]//input"
    ADDR_PIN_CODE     = "xpath=//mat-form-field[.//mat-label[contains(.,'Pin Code')]]//mat-select"
    ADDR_REG_NUMBER   = "xpath=//mat-form-field[.//mat-label[contains(.,'Registration Number')]]//input"

    # Step 3 — Bank fields
    BANK_NAME         = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Bank Name']]//input"
    BANK_BRANCH       = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Branch']]//input"
    BANK_IFSC         = "xpath=//mat-form-field[.//mat-label[contains(.,'IFSC Code')]]//input"
    BANK_ACCOUNT_TYPE = "xpath=//mat-form-field[.//mat-label[contains(.,'Account Type')]]//mat-select"
    BANK_HOLDER_NAME  = "xpath=//mat-form-field[.//mat-label[contains(.,'Account Holder Name')]]//input"
    BANK_ACCOUNT_NO   = "xpath=//mat-form-field[.//mat-label[contains(.,'Account Number')]]//input"
    BANK_PROOF        = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Bank Proof']]//mat-select"

    SUBMIT_BTN   = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Submit')]"
    UPDATE_BTN   = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Update')]"
    CANCEL_BTN   = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Cancel')]"
    NEXT_BTN     = "button[matsteppernext]"
    ADD_ROW_BTN  = "button.add-row-btn"
    SEARCH_INPUT = "input#erpSearchInput"

    # ── mat-select helpers ──────────────────────────────────────────────

    def _select_mat_by_text(self, selector, text, nth=0):
        """Open the nth dropdown and click the option whose text exactly matches."""
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
            self.page.locator(
                ".mat-mdc-select-panel mat-option"
            ).filter(has_text=text).first.click(force=True)
        try:
            self.page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=3000)
        except Exception:
            pass
        self.page.wait_for_timeout(300)

    def _select_random_mat_option(self, selector, nth=0):
        """Open the nth dropdown and pick a random option."""
        self.page.locator(selector).nth(nth).click(force=True)
        self.page.wait_for_selector(".mat-mdc-select-panel", timeout=5000)
        options = self.page.locator(
            ".mat-mdc-select-panel mat-option:not(.dd-clear-option)"
        ).all()
        if options:
            random.choice(options).click(force=True)
        try:
            self.page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=3000)
        except Exception:
            pass
        self.page.wait_for_timeout(500)

    def _try_select_random_mat_option(self, selector, nth=0):
        """Same as _select_random_mat_option but silently skips if no panel appears."""
        self.page.locator(selector).nth(nth).click(force=True)
        try:
            self.page.wait_for_selector(".mat-mdc-select-panel", timeout=3000)
        except Exception:
            return
        options = self.page.locator(
            ".mat-mdc-select-panel mat-option:not(.dd-clear-option)"
        ).all()
        if options:
            random.choice(options).click(force=True)
        try:
            self.page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=3000)
        except Exception:
            pass
        self.page.wait_for_timeout(500)

    def _fill_text(self, selector, value, nth=0):
        loc = self.page.locator(selector).nth(nth)
        loc.click(force=True)
        loc.fill(str(value))
        loc.press("Tab")

    def _click_next(self):
        # JS walk finds the next button whose stepper pane is currently active/visible.
        self.page.evaluate("""
            const btns = document.querySelectorAll('button[matsteppernext]');
            for (const btn of btns) {
                if (btn.offsetParent !== null &&
                        getComputedStyle(btn).display !== 'none') {
                    btn.scrollIntoView({block: 'center'});
                    btn.click();
                    break;
                }
            }
        """)
        self.page.wait_for_timeout(1000)

    # ── Navigation ──────────────────────────────────────────────────────

    def navigate_to_page(self):
        try:
            if "Supplier" in self.page.url:
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
        self.page.wait_for_selector(self.COMPANY_NAME, timeout=8000)

    # ── Step fillers ────────────────────────────────────────────────────

    def _fill_step1(self, data):
        self._select_mat_by_text(self.OWNERSHIP_STATUS, data.get("ownership_status", "Proprietorship"))
        self._fill_text(self.COMPANY_NAME, data["company_name"])
        self._select_mat_by_text(self.PO_TYPE, data.get("po_type", "Domestic"))
        self._fill_text(self.EMAIL, data.get("email", ""))
        self._fill_text(self.PHONE_NUMBER, data["phone_number"])
        self._select_mat_by_text(self.DEFAULT_CURRENCY, data.get("default_currency", "INR"))
        self._fill_text(self.PAN_NUMBER, data["pan_number"])
        self._fill_text(self.CONTACT_PERSON, data.get("contact_person", ""))
        self._select_mat_by_text(self.TAX_REG_STATUS, data.get("tax_reg_status", "Registered"))
        self._select_mat_by_text(self.GST_REG_TYPE, data.get("gst_reg_type", "Regular"))
        self._try_select_random_mat_option(self.PAYMENT_TERMS)
        self._try_select_random_mat_option(self.DELIVERY_TERMS)
        self._try_select_random_mat_option(self.MODE_OF_DELIVERY)

    def _fill_step2(self, data):
        # Row 0 — Shipping
        self._select_mat_by_text(self.ADDR_ADDRESS_TYPE, "Shipping", nth=0)
        self._select_mat_by_text(self.ADDR_STATE, data.get("state", "Maharashtra"), nth=0)
        self.page.locator(self.ADDR_DISTRICT).nth(0).wait_for(state="visible", timeout=10000)
        self._select_random_mat_option(self.ADDR_DISTRICT, nth=0)
        self._select_random_mat_option(self.ADDR_TALUKA, nth=0)
        self._try_select_random_mat_option(self.ADDR_VILLAGE, nth=0)
        self._fill_text(self.ADDR_ADDRESS, data.get("address", "101 Shivaji Path"), nth=0)
        self._try_select_random_mat_option(self.ADDR_PIN_CODE, nth=0)
        self._fill_text(self.ADDR_REG_NUMBER, data.get("registration_number", ""), nth=0)

        # Add billing row (first add-row-btn = Address; second = Bank Details)
        self.page.locator(self.ADD_ROW_BTN).first.click()
        self.page.wait_for_timeout(1000)

        # Row 1 — Billing: set type, then check Same as Above so billing copies shipping data.
        # Click the .mdc-label (not mat-checkbox itself) to bypass field-click-guard.
        # The label's `for` attribute points directly to the native input, so Angular's
        # checkbox CDK fires correctly without hitting the guard overlay.
        self._select_mat_by_text(self.ADDR_ADDRESS_TYPE, "Billing", nth=1)
        self.page.wait_for_timeout(1500)
        self.page.evaluate("""
            const matches = [...document.querySelectorAll('mat-checkbox .mdc-label')]
                .filter(lbl => lbl.textContent.trim().includes('Same as Above'));
            const target = matches[1] || matches[0];
            if (target) target.click();
        """)
        self.page.wait_for_timeout(500)

    def _fill_step3(self, data):
        self._fill_text(self.BANK_NAME, data.get("bank_name", "HDFC Bank"))
        self._fill_text(self.BANK_BRANCH, data.get("bank_branch", "Pune Branch"))
        self._fill_text(self.BANK_IFSC, data.get("bank_ifsc", "BARB0DHUKIS"))
        self._select_mat_by_text(self.BANK_ACCOUNT_TYPE, data.get("account_type", "Saving"))
        self._fill_text(self.BANK_HOLDER_NAME, data.get("bank_holder", "Holder Name"))
        self._fill_text(self.BANK_ACCOUNT_NO, data.get("bank_account", "9849892348734"))
        self._select_mat_by_text(self.BANK_PROOF, data.get("bank_proof", "Passbook"))

    # ── Public API ──────────────────────────────────────────────────────

    def fill_form(self, data):
        self._fill_step1(data)
        self._click_next()
        self._fill_step2(data)
        self._click_next()
        self._fill_step3(data)

    def submit(self):
        self.page.locator(self.SUBMIT_BTN).click()

    def close_popup(self):
        try:
            self.page.locator(self.CANCEL_BTN).click()
            self.page.wait_for_selector("table#excel-table", timeout=5000)
        except Exception:
            pass

    def handle_success_alert(self):
        self.page.wait_for_selector(".swal2-container", timeout=10000)
        self.page.evaluate("document.querySelector('.swal2-confirm')?.click()")
        try:
            self.page.wait_for_selector(".swal2-container", state="hidden", timeout=5000)
        except Exception:
            pass
        self.page.wait_for_selector("table#excel-table", timeout=10000)

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

    # ── Search & table helpers ───────────────────────────────────────────

    def search_supplier(self, company_name):
        if not self.page.locator(self.SEARCH_INPUT).is_visible():
            self.page.locator("button[mattooltip='Search']").click()
            self.page.wait_for_timeout(500)
        self.page.locator(self.SEARCH_INPUT).wait_for(state="visible", timeout=5000)
        self.page.locator(self.SEARCH_INPUT).fill(company_name)
        self.page.locator(self.SEARCH_INPUT).press("Enter")
        self.page.wait_for_timeout(1500)

    def is_supplier_in_table(self, company_name):
        for _ in range(10):
            rows = self.page.locator("table#excel-table tbody tr")
            for i in range(rows.count()):
                if company_name in rows.nth(i).inner_text():
                    return True
            self.page.wait_for_timeout(300)
        return False

    def verify_supplier_exists(self, company_name):
        assert self.is_supplier_in_table(company_name), \
            f"Supplier '{company_name}' not found in table"

    def _find_row_index(self, company_name):
        rows = self.page.locator("table#excel-table tbody tr")
        for i in range(rows.count()):
            if company_name in rows.nth(i).inner_text():
                return i
        raise AssertionError(f"Supplier '{company_name}' not found in table")

    # ── Row actions ──────────────────────────────────────────────────────

    def get_first_supplier_pan(self):
        """Open View on the first table row, read the PAN Number, close popup."""
        self.page.locator("button.erp-row-trigger").nth(0).click()
        self.page.wait_for_selector(".mat-mdc-menu-panel", timeout=8000)
        self.page.locator(
            ".mat-mdc-menu-panel button.mat-mdc-menu-item:has(.erp-menu-title:text-is('View'))"
        ).click()
        self.page.wait_for_selector(
            "xpath=//mat-label[contains(.,'PAN Number')]/ancestor::mat-form-field//input",
            timeout=8000
        )
        pan = self.page.locator(
            "xpath=//mat-label[contains(.,'PAN Number')]/ancestor::mat-form-field//input"
        ).input_value()
        self.page.locator(self.CANCEL_BTN).click()
        self.page.wait_for_timeout(500)
        return pan

    def get_history_entry_count(self, company_name):
        """Open History for company_name, return row count, then close."""
        self.click_row_action(self._find_row_index(company_name), "History")
        self.page.wait_for_timeout(1000)
        count = self.page.locator("table tbody tr").count()
        self.force_close_popup()
        self.page.wait_for_timeout(500)
        return count

    def get_view_field_value(self, company_name, field_label):
        """Open View for company_name, read field value, close popup."""
        self.click_row_action(self._find_row_index(company_name), "View")
        self.page.wait_for_selector(
            f"xpath=//mat-label[contains(.,'{field_label}')]/ancestor::mat-form-field//input",
            timeout=8000
        )
        value = self.page.locator(
            f"xpath=//mat-label[contains(.,'{field_label}')]/ancestor::mat-form-field//input"
        ).input_value()
        self.force_close_popup()
        self.page.wait_for_timeout(500)
        return value

    def edit_field_and_update(self, company_name, field_label, new_value):
        """Open Edit for company_name, update one text field, submit."""
        self.click_row_action(self._find_row_index(company_name), "Edit")
        self.page.wait_for_selector(self.COMPANY_NAME, timeout=8000)
        loc = self.page.locator(
            f"xpath=//mat-label[contains(.,'{field_label}')]/ancestor::mat-form-field//input"
        ).first
        loc.click(click_count=3)
        loc.fill(new_value)
        loc.press("Tab")
        self.page.locator(self.UPDATE_BTN).click()
        self.handle_success_alert()
        self.navigate_to_page()

    def click_view_button(self, company_name):
        self.click_row_action(self._find_row_index(company_name), "View")

    def click_edit_button(self, company_name):
        self.click_row_action(self._find_row_index(company_name), "Edit")
        self.page.wait_for_selector(self.COMPANY_NAME, timeout=5000)

    def update_company_name(self, new_value):
        loc = self.page.locator(self.COMPANY_NAME).first
        loc.click(click_count=3)
        loc.fill(new_value)

    def click_update(self):
        self.page.locator(self.UPDATE_BTN).click()

    def click_history_button(self, company_name):
        self.click_row_action(self._find_row_index(company_name), "History")
        self.page.wait_for_timeout(1000)

    def verify_view_popup_read_only(self):
        self.page.wait_for_selector(".popup-footer", timeout=5000)
        buttons = self.page.locator(".popup-footer button")
        texts = [buttons.nth(i).text_content().strip() for i in range(buttons.count())]
        assert "Submit" not in texts and "Update" not in texts, \
            "View popup must not have Submit or Update"
