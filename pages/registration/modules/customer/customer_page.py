import random
from pages.base_playwright_page import BasePlaywrightPage


class CustomerPage(BasePlaywrightPage):
    URL = "https://rhythmerp.algorhythms.in/#/dynamic-screens/Customer/Customer"

    # Universal fields (page 1)
    OWNERSHIP_STATUS     = "xpath=//mat-form-field[.//mat-label[contains(.,'Ownership Status')]]//mat-select"
    COMPANY_NAME         = "xpath=//mat-form-field[.//mat-label[contains(.,'Company Name')]]//input"
    SALE_TYPE            = "xpath=//mat-form-field[.//mat-label[contains(.,'Sale Type')]]//mat-select"
    SUPPLY_TYPE          = "xpath=//mat-form-field[.//mat-label[contains(.,'Supply Type')]]//mat-select"
    TRANSACTION_CURRENCY = "xpath=//mat-form-field[.//mat-label[contains(.,'Transaction Currency')]]//mat-select"
    EMAIL                = "xpath=//mat-form-field[.//mat-label[contains(.,'Email')]]//input"
    PHONE_NUMBER         = "xpath=//mat-form-field[.//mat-label[contains(.,'Phone Number')]]//input"
    PAN_NUMBER           = "xpath=//mat-form-field[.//mat-label[contains(.,'PAN Number')]]//input"

    # Address fields (page 2, inline grid — 2 rows)
    # Use normalize-space exact matches to avoid catching unrelated labels like "Tax Registration Status"
    ADDR_ADDRESS_TYPE = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Address Type']]//mat-select"
    ADDR_COUNTRY      = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Country']]//mat-select"
    ADDR_STATE        = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='State']]//mat-select"
    ADDR_DISTRICT     = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='District']]//mat-select"
    ADDR_TALUKA       = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Taluka']]//mat-select"
    ADDR_VILLAGE      = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Village']]//mat-select"
    ADDR_ADDRESS      = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Address']]//input"
    ADDR_PIN_CODE     = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Pin Code']]//mat-select"
    ADDR_REG_NUMBER   = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Registration Number']]//input"
    ADDR_GSTIN        = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='GSTIN']]//input"

    # Additional Details (page 2)
    CONTACT_PERSON_NAME      = "xpath=//mat-form-field[.//mat-label[contains(.,'Contact Person Name')]]//input"
    OFFICE_NUMBER            = "xpath=//mat-form-field[.//mat-label[contains(.,'Office Number')]]//input"
    PREFERRED_PAYMENT_METHOD = "xpath=//mat-form-field[.//mat-label[contains(.,'Preferred Payment Method')]]//mat-select"
    GST_REGISTRATION_STATUS  = "xpath=//mat-form-field[.//mat-label[contains(.,'Gst Registration Status')]]//mat-select"
    GST_REGISTRATION_TYPE    = "xpath=//mat-form-field[.//mat-label[contains(.,'Gst Registration Type')]]//mat-select"
    PAYMENT_TERMS            = "xpath=//mat-form-field[.//mat-label[contains(.,'Payment Terms')]]//mat-select"
    MODE_OF_DELIVERY         = "xpath=//mat-form-field[.//mat-label[contains(.,'Mode Of Delivery')]]//mat-select"
    DELIVERY_TERMS           = "xpath=//mat-form-field[.//mat-label[contains(.,'Delivery Terms')]]//mat-select"
    COURIER_TERMS            = "xpath=//mat-form-field[.//mat-label[contains(.,'Courier Terms')]]//mat-select"

    # Bank fields (page 3)
    BANK_NAME_INPUT    = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Bank Name']]//input"
    BANK_BRANCH        = "xpath=//mat-form-field[.//mat-label[contains(.,'Branch')]]//input"
    BANK_IFSC          = "xpath=//mat-form-field[.//mat-label[contains(.,'IFSC Code')]]//input"
    BANK_ACCOUNT_TYPE  = "xpath=//mat-form-field[.//mat-label[contains(.,'Account Type')]]//mat-select"
    BANK_HOLDER_NAME   = "xpath=//mat-form-field[.//mat-label[contains(.,'Account Holder Name')]]//input"
    BANK_ACCOUNT_NO    = "xpath=//mat-form-field[.//mat-label[contains(.,'Account Number')]]//input"
    BANK_PROOF         = "xpath=//mat-form-field[.//mat-label[contains(.,'Bank Proof')]]//mat-select"

    SUBMIT_BTN   = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Submit')]"
    CANCEL_BTN   = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Cancel')]"
    SEARCH_INPUT = "#erpSearchInput"

    def _clear_overlays(self):
        self.page.evaluate(
            "document.querySelectorAll('.cdk-overlay-backdrop').forEach(el => el.remove())"
        )

    def _select_mat_option_by_text(self, selector, text, nth=0):
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
        """Open the nth dropdown and pick a random non-clear option."""
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
        """Like _select_random_mat_option but silently skips if no panel appears."""
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
        self.page.wait_for_timeout(300)

    def _click_next(self):
        # button[matsteppernext] is the Angular directive attribute — matches the Next button
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
        self.page.wait_for_timeout(1000)

    def _fill_text(self, selector, value, nth=0):
        loc = self.page.locator(selector).nth(nth)
        loc.click(force=True)
        loc.fill(str(value))
        loc.press("Tab")

    def _fill_address_row(self, row_index, address_text, address_type=None):
        # Address Type
        if address_type:
            self._select_mat_option_by_text(self.ADDR_ADDRESS_TYPE, address_type, nth=row_index)
        else:
            self._select_random_mat_option(self.ADDR_ADDRESS_TYPE, nth=row_index)

        # Country (optional — not present in all customer forms)
        try:
            self.page.locator(self.ADDR_COUNTRY).nth(row_index).wait_for(state="visible", timeout=2000)
            self._select_mat_option_by_text(self.ADDR_COUNTRY, "India", nth=row_index)
        except Exception:
            pass

        # State — supplier pattern: select specific state, then wait for District cascade
        self._select_mat_option_by_text(self.ADDR_STATE, "Maharashtra", nth=row_index)

        # District — wait for cascade after State, then pick random
        self.page.locator(self.ADDR_DISTRICT).nth(row_index).wait_for(state="visible", timeout=10000)
        self._select_random_mat_option(self.ADDR_DISTRICT, nth=row_index)

        # Taluka — cascades from District
        self._select_random_mat_option(self.ADDR_TALUKA, nth=row_index)

        # Village (optional)
        self._try_select_random_mat_option(self.ADDR_VILLAGE, nth=row_index)

        # Address text
        self._fill_text(self.ADDR_ADDRESS, address_text, nth=row_index)

        # Pin Code (optional — depends on Taluka)
        self._try_select_random_mat_option(self.ADDR_PIN_CODE, nth=row_index)

        # Registration Number (appears per-row when Tax Reg Status = Registered)
        try:
            self.page.locator(self.ADDR_REG_NUMBER).nth(row_index).wait_for(state="visible", timeout=2000)
            self._fill_text(self.ADDR_REG_NUMBER, "29ABCDE1234F1Z5", nth=row_index)
        except Exception:
            pass

        # GSTIN (optional)
        try:
            self.page.locator(self.ADDR_GSTIN).nth(row_index).wait_for(state="visible", timeout=2000)
            self._fill_text(self.ADDR_GSTIN, "29ABCDE1234F1Z5", nth=row_index)
        except Exception:
            pass

    def navigate_to_page(self):
        try:
            if "Customer" in self.page.url:
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
        self.page.wait_for_selector(self.COMPANY_NAME, timeout=5000)

    # Selector for Tax Registration Status (distinct from Gst Registration Status)
    TAX_REGISTRATION_STATUS = "xpath=//mat-form-field[.//mat-label[contains(.,'Tax Registration Status')]]//mat-select"

    def fill_form(self, data):
        # ── Step 1: Universal + Additional Details ────────────────────────
        self._select_mat_option_by_text(self.OWNERSHIP_STATUS, data.get("ownership_status", "Proprietorship"))
        self.page.wait_for_timeout(200)

        self._fill_text(self.COMPANY_NAME, data["company_name"])

        self._select_mat_option_by_text(self.SALE_TYPE, data.get("sale_type", "Export"))
        self.page.wait_for_timeout(200)

        self.page.locator(self.SUPPLY_TYPE).wait_for(state="visible", timeout=10000)
        self._select_mat_option_by_text(self.SUPPLY_TYPE, data.get("supply_type", "Both"))
        self.page.wait_for_timeout(200)

        self._select_mat_option_by_text(self.TRANSACTION_CURRENCY, data.get("transaction_currency", "INR"))
        self.page.wait_for_timeout(200)

        self._fill_text(self.EMAIL, data.get("email", "test@testmail.com"))

        if data.get("phone_number"):
            self._fill_text(self.PHONE_NUMBER, data["phone_number"])

        self._fill_text(self.PAN_NUMBER, data.get("pan_number", "ABCDE1234F"))
        self._fill_text(self.CONTACT_PERSON_NAME, data.get("contact_person", "Contact Person"))

        try:
            self._select_mat_option_by_text(self.PREFERRED_PAYMENT_METHOD, data.get("preferred_payment_method", "Cash"))
        except Exception:
            pass

        # Tax Registration Status — triggers Gst Registration Type + Registration Number
        try:
            self.page.locator(self.TAX_REGISTRATION_STATUS).wait_for(state="visible", timeout=8000)
            self._select_mat_option_by_text(self.TAX_REGISTRATION_STATUS, data.get("tax_registration_status", "Registered"))
            self.page.wait_for_timeout(500)
        except Exception:
            pass

        try:
            self._select_mat_option_by_text(self.GST_REGISTRATION_TYPE, data.get("gst_registration_type", "Regular"))
            self.page.wait_for_timeout(300)
        except Exception:
            pass

        for sel, key, default in [
            (self.PAYMENT_TERMS,   "payment_terms",   "Immediate"),
            (self.MODE_OF_DELIVERY,"mode_of_delivery","Air"),
            (self.DELIVERY_TERMS,  "delivery_terms",  "Spot"),
            (self.COURIER_TERMS,   "courier_terms",   "Paid"),
        ]:
            try:
                self.page.locator(sel).wait_for(state="visible", timeout=5000)
                self._select_mat_option_by_text(sel, data.get(key, default))
                self.page.wait_for_timeout(200)
            except Exception:
                pass

        # ── Step 2: Address Details ───────────────────────────────────────
        self._click_next()
        self._fill_address_row(0, data.get("address1", "101 Shivaji Path Pune"), address_type="Shipping")

        # Add billing row
        self.page.locator("button.add-row-btn").first.click()
        self.page.wait_for_timeout(1000)

        # Billing row — set type then Same as Above
        self._select_mat_option_by_text(self.ADDR_ADDRESS_TYPE, "Billing", nth=1)
        self.page.wait_for_timeout(1500)
        self.page.evaluate("""
            const matches = [...document.querySelectorAll('mat-checkbox .mdc-label')]
                .filter(lbl => lbl.textContent.trim().includes('Same as Above'));
            const target = matches[1] || matches[0];
            if (target) target.click();
        """)
        self.page.wait_for_timeout(500)

        # ── Step 3: Bank Details ─────────────────────────────────────────
        self._click_next()
        for selector, key, default in [
            (self.BANK_NAME_INPUT, "bank_name",    "HDFC Bank"),
            (self.BANK_BRANCH,     "bank_branch",  "Pune Branch"),
            (self.BANK_IFSC,       "bank_ifsc",    "SBIN0138644"),
            (self.BANK_HOLDER_NAME,"bank_holder",  "Account Holder"),
            (self.BANK_ACCOUNT_NO, "bank_account", "164831834232"),
        ]:
            self._fill_text(selector, data.get(key, default))

        self._select_mat_option_by_text(self.BANK_ACCOUNT_TYPE, data.get("account_type", "Saving"))
        self._select_mat_option_by_text(self.BANK_PROOF, data.get("bank_proof", "Cancelled Cheque"))
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

    def search_customer(self, company_name):
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

    def is_customer_in_table(self, company_name):
        for _ in range(10):
            rows = self.page.locator("table#excel-table tbody tr")
            for i in range(rows.count()):
                if company_name in rows.nth(i).inner_text():
                    return True
            self.page.wait_for_timeout(300)
        return False

    def verify_customer_exists(self, company_name):
        assert self.is_customer_in_table(company_name), f"Customer '{company_name}' not found in table"

    def _find_row_index(self, company_name):
        rows = self.page.locator("table#excel-table tbody tr")
        for i in range(rows.count()):
            if company_name in rows.nth(i).inner_text():
                return i
        raise AssertionError(f"Customer '{company_name}' not found in table")

    def click_view_button(self, company_name):
        self.click_row_action(self._find_row_index(company_name), "View")

    def click_edit_button(self, company_name):
        self.click_row_action(self._find_row_index(company_name), "Edit")
        self.page.wait_for_selector(self.COMPANY_NAME, timeout=5000)

    def update_company_name(self, new_value):
        self.page.locator(self.COMPANY_NAME).first.click(click_count=3)
        self.page.locator(self.COMPANY_NAME).first.fill(new_value)

    UPDATE_BTN = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Update')]"

    def click_update(self):
        self.page.locator(self.UPDATE_BTN).click()

    def get_first_customer_pan(self):
        self.click_row_action(0, "View")
        self.page.wait_for_selector(
            "xpath=//mat-label[contains(.,'PAN Number')]/ancestor::mat-form-field//input",
            timeout=8000,
        )
        pan = self.page.locator(
            "xpath=//mat-label[contains(.,'PAN Number')]/ancestor::mat-form-field//input"
        ).input_value()
        self.page.locator(self.CANCEL_BTN).click()
        self.page.wait_for_timeout(500)
        return pan

    def get_view_field_value(self, company_name, field_label):
        self.click_row_action(self._find_row_index(company_name), "View")
        self.page.wait_for_selector(
            f"xpath=//mat-label[contains(.,'{field_label}')]/ancestor::mat-form-field//input",
            timeout=8000,
        )
        value = self.page.locator(
            f"xpath=//mat-label[contains(.,'{field_label}')]/ancestor::mat-form-field//input"
        ).input_value()
        self.force_close_popup()
        self.page.wait_for_timeout(500)
        return value

    def edit_field_and_update(self, company_name, field_label, new_value):
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

    def click_history_button(self, company_name):
        self.click_row_action(self._find_row_index(company_name), "History")
        self.page.wait_for_timeout(1000)

    def verify_view_popup_read_only(self):
        buttons = self.page.locator(".popup-footer button")
        texts = [buttons.nth(i).text_content().strip() for i in range(buttons.count())]
        assert "Submit" not in texts and "Update" not in texts, \
            "View popup must not have Submit or Update"

    def export_master(self):
        self.page.locator("button.mat-mdc-menu-trigger.erp-outline-btn").click()
        self.page.wait_for_selector(".mat-mdc-menu-panel", timeout=5000)
        with self.page.expect_download() as dl:
            self.page.locator(
                ".mat-mdc-menu-panel button.mat-mdc-menu-item:has(.erp-menu-title:text-is('Export Master'))"
            ).click()
        return dl.value
