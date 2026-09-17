import random
from pages.base_playwright_page import BasePlaywrightPage


class AgentPage(BasePlaywrightPage):
    URL = "https://rhythmerp.algorhythms.in/#/dynamic-screens/Agent"

    # ── Selectors ─────────────────────────────────────────────────────────
    SUBMIT_BTN   = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Submit')]"
    UPDATE_BTN   = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Update')]"
    CANCEL_BTN   = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Cancel')]"
    SEARCH_INPUT = "#erpSearchInput"

    # Step 1 — Agent details + address (inline, no separate step)
    AGENT_NAME   = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Agent Name']]//input"
    PHONE_NUMBER = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Phone Number']]//input"
    EMAIL        = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Email']]//input"
    ADDR_STATE   = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='State']]//mat-select"
    ADDR_DISTRICT= "xpath=//mat-form-field[.//mat-label[normalize-space(.)='District']]//mat-select"
    ADDR_TALUKA  = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Taluka']]//mat-select"
    ADDR_VILLAGE = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Village']]//mat-select"
    ADDR_ADDRESS = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Address']]//input"
    ADDR_PIN_CODE= "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Pin Code']]//mat-select"

    # Step 2 — Payment
    PAYMENT_TERMS            = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Payment Terms']]//mat-select"
    PREFERRED_PAYMENT_METHOD = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Preferred Payment Method']]//mat-select"

    # Step 3 — Bank
    BANK_NAME        = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Bank Name']]//input"
    BANK_BRANCH      = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Branch']]//input"
    BANK_IFSC        = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='IFSC Code']]//input"
    BANK_ACCOUNT_TYPE= "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Account Type']]//mat-select"
    BANK_HOLDER_NAME = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Account Holder Name']]//input"
    BANK_ACCOUNT_NO  = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Account Number']]//input"
    BANK_PROOF       = "xpath=//mat-form-field[.//mat-label[normalize-space(.)='Bank Proof']]//mat-select"

    # ── mat-select helpers (proven pattern) ───────────────────────────────
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
        self.page.wait_for_timeout(300)

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

    # ── Navigation ────────────────────────────────────────────────────────
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
        self.page.locator("button.erp-add-btn").click()
        self.page.wait_for_selector(self.AGENT_NAME, timeout=8000)

    # ── Form fill ─────────────────────────────────────────────────────────
    def fill_form(self, data):
        # Step 1: Agent details + address
        self._fill_text(self.AGENT_NAME, data["agent_name"])
        self._fill_text(self.PHONE_NUMBER, data["phone_number"])
        self._fill_text(self.EMAIL, data.get("email", "agent@testmail.com"))

        # Address cascade: State → wait for District → District → Taluka → Village
        self._select_mat_option_by_text(self.ADDR_STATE, data.get("state", "Maharashtra"))
        self.page.locator(self.ADDR_DISTRICT).wait_for(state="visible", timeout=10000)
        self._select_random_mat_option(self.ADDR_DISTRICT)
        self._select_random_mat_option(self.ADDR_TALUKA)
        self._try_select_random_mat_option(self.ADDR_VILLAGE)

        self._fill_text(self.ADDR_ADDRESS, data.get("address", "101 MG Road, Pune"))
        self._try_select_random_mat_option(self.ADDR_PIN_CODE)

        # Step 2: Payment
        self._click_next()
        self._select_mat_option_by_text(self.PAYMENT_TERMS, data.get("payment_terms", "Immediate"))
        self.page.locator(self.PREFERRED_PAYMENT_METHOD).wait_for(state="visible", timeout=10000)
        self._select_mat_option_by_text(self.PREFERRED_PAYMENT_METHOD, data.get("preferred_payment_method", "Cash"))
        self.page.wait_for_timeout(500)

        # Step 3: Bank
        self._click_next()
        self._fill_text(self.BANK_NAME, data.get("bank_name", "HDFC Bank"))
        self._fill_text(self.BANK_BRANCH, data.get("bank_branch", "Pune Branch"))
        self._fill_text(self.BANK_IFSC, data.get("bank_ifsc", "SBIN0807508"))
        self._select_mat_option_by_text(self.BANK_ACCOUNT_TYPE, data.get("account_type", "Current"))
        self._fill_text(self.BANK_HOLDER_NAME, data.get("bank_holder", "Account Holder"))
        self._fill_text(self.BANK_ACCOUNT_NO, data.get("bank_account", "8450534030237207"))
        self._select_mat_option_by_text(self.BANK_PROOF, data.get("bank_proof", "Passbook"))
        self._clear_overlays()

    def submit(self):
        self._clear_overlays()
        self.page.click(self.SUBMIT_BTN)

    def close_popup(self):
        self._clear_overlays()
        try:
            self.page.locator(self.CANCEL_BTN).click()
        except Exception:
            self.page.get_by_role("button", name="close").click()

    def download_validation_error_excel(self, save_path=None):
        import tempfile, os
        self.page.wait_for_selector(".swal2-container", timeout=10000)
        with self.page.expect_download() as dl:
            self.page.evaluate("document.querySelector('.swal2-confirm')?.click()")
        download = dl.value
        path = save_path or os.path.join(tempfile.gettempdir(), download.suggested_filename)
        download.save_as(path)
        self.page.wait_for_selector(".swal2-container", state="hidden", timeout=5000)
        return path

    def handle_success_alert(self):
        try:
            self.page.wait_for_selector(".swal2-container", timeout=5000)
            title = (self.page.locator("#swal2-title").text_content() or "").strip().lower()
            body = (self.page.locator("#swal2-html-container").text_content() or "").strip()
            self.page.evaluate("document.querySelector('.swal2-confirm')?.click()")
            self.page.wait_for_selector(".swal2-container", state="hidden", timeout=3000)
            if "validation" in title or "failed" in title or "error" in title:
                labels = self.page.locator("mat-form-field.ng-invalid mat-label").all_text_contents()
                try:
                    import tempfile, openpyxl, xlrd as _xlrd
                    self.page.wait_for_selector(".swal2-container", timeout=5000)
                    with self.page.expect_download() as _dl:
                        self.page.evaluate("document.querySelector('.swal2-confirm')?.click()")
                    _d = _dl.value
                    _p = tempfile.mktemp(suffix="." + _d.suggested_filename.rsplit(".", 1)[-1])
                    _d.save_as(_p)
                    _ext = _p.rsplit(".", 1)[-1].lower()
                    _rows = []
                    if _ext == "xlsx":
                        _ws = openpyxl.load_workbook(_p).active
                        _rows = [r for r in _ws.iter_rows(values_only=True) if any(c for c in r)]
                    else:
                        _sh = _xlrd.open_workbook(_p).sheet_by_index(0)
                        _rows = [_sh.row_values(i) for i in range(_sh.nrows)]
                    print("\n=== VALIDATION ERROR EXCEL ===")
                    for _r in _rows: print(_r)
                    print("==============================\n")
                except Exception as _e:
                    print(f"[could not read error excel: {_e}]")
                raise AssertionError(f"Validation failed — invalid fields: {labels} — body: '{body}'")
        except AssertionError:
            raise
        except Exception:
            pass

    def create_record(self, data):
        self.open_add_form()
        self.fill_form(data)
        self.submit()
        self.handle_success_alert()

    # ── Search / table helpers ────────────────────────────────────────────
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

    def verify_agent_exists(self, agent_name):
        rows = self.page.locator("table#excel-table tbody tr")
        for i in range(rows.count()):
            if agent_name in rows.nth(i).inner_text():
                return
        raise AssertionError(f"Agent '{agent_name}' not found in table")

    def _find_row_index(self, agent_name):
        rows = self.page.locator("table#excel-table tbody tr")
        for i in range(rows.count()):
            if agent_name in rows.nth(i).inner_text():
                return i
        raise AssertionError(f"Agent '{agent_name}' not found in table")

    def click_view_button(self, agent_name):
        self.click_row_action(self._find_row_index(agent_name), "View")

    def click_edit_button(self, agent_name):
        self.click_row_action(self._find_row_index(agent_name), "Edit")
        self.page.wait_for_selector(self.AGENT_NAME, timeout=5000)

    def click_update(self):
        self.page.locator(self.UPDATE_BTN).click()

    def get_first_agent_name(self):
        self.click_row_action(0, "View")
        self.page.wait_for_selector(self.AGENT_NAME, timeout=8000)
        name = self.page.locator(self.AGENT_NAME).input_value()
        self.force_close_popup()
        self.page.wait_for_timeout(300)
        return name

    def get_first_agent_phone(self):
        self.click_row_action(0, "View")
        self.page.wait_for_selector(
            "xpath=//mat-label[contains(.,'Phone Number')]/ancestor::mat-form-field//input",
            timeout=8000,
        )
        phone = self.page.locator(
            "xpath=//mat-label[contains(.,'Phone Number')]/ancestor::mat-form-field//input"
        ).input_value()
        self.force_close_popup()
        self.page.wait_for_timeout(500)
        return phone

    def get_view_field_value(self, agent_name, field_label):
        self.search_agent(agent_name)
        self.click_row_action(self._find_row_index(agent_name), "View")
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

    def edit_field_and_update(self, agent_name, field_label, new_value):
        self.search_agent(agent_name)
        self.click_row_action(self._find_row_index(agent_name), "Edit")
        self.page.wait_for_selector(self.AGENT_NAME, timeout=8000)
        loc = self.page.locator(
            f"xpath=//mat-label[contains(.,'{field_label}')]/ancestor::mat-form-field//input"
        ).first
        loc.click(click_count=3)
        loc.fill(new_value)
        loc.press("Tab")
        self.page.locator(self.UPDATE_BTN).click()
        self.handle_success_alert()

    def export_master(self):
        self.page.locator("button.mat-mdc-menu-trigger.erp-outline-btn").click()
        self.page.wait_for_selector(".mat-mdc-menu-panel", timeout=5000)
        with self.page.expect_download() as dl:
            self.page.locator(
                ".mat-mdc-menu-panel button.mat-mdc-menu-item:has(.erp-menu-title:text-is('Export Master'))"
            ).click()
        return dl.value
