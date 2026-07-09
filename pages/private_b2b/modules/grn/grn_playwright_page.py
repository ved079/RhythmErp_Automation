import random
from pages.base_playwright_page import BasePlaywrightPage

BASE_URL = "https://rhythmerp.algorhythms.in"


class GRNPlaywrightPage(BasePlaywrightPage):
    URL = f"{BASE_URL}/#/purchase/grn"

    # Header fields
    SUPPLIER_NAME   = "xpath=//mat-form-field[.//mat-label[contains(.,'Supplier Name')]]//mat-select"
    GATE_PASS_NO    = "xpath=//mat-form-field[.//mat-label[contains(.,'Gate Pass No.')]]//mat-select"

    # Row fields
    ACCEPTED_QTY    = "xpath=//mat-form-field[.//mat-label[contains(.,'Accepted Quantity')]]//input"
    REJECTED_QTY    = "xpath=//mat-form-field[.//mat-label[contains(.,'Rejected Quantity')]]//input"
    GP_QTY          = "xpath=//mat-form-field[.//mat-label[contains(.,'Gate Pass Quantity')]]//input"

    # Buttons
    ADD_BTN    = "button.erp-add-btn"
    SUBMIT_BTN = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Submit')]"
    CANCEL_BTN = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Cancel')]"

    # Table
    REF_NO_COL = "td.cdk-column-transaction_ref_no"

    # ── Navigation ───────────────────────────────────────────────────────

    def handle_success_alert(self):
        try:
            self.page.wait_for_selector(".swal2-container", timeout=8000)
            self.page.evaluate("document.querySelector('.swal2-confirm')?.click()")
            try:
                self.page.wait_for_selector(".swal2-container", state="hidden", timeout=10000)
            except Exception:
                pass
        except Exception:
            pass
        try:
            self.page.wait_for_selector("table.mat-mdc-table", timeout=8000)
        except Exception:
            pass

    def navigate_to_page(self):
        self.page.goto(self.URL)
        try:
            self.page.wait_for_selector("table.mat-mdc-table, div.empty-state", timeout=15000)
        except Exception:
            self.page.reload()
            self.page.wait_for_selector("table.mat-mdc-table, div.empty-state", timeout=20000)

    # ── Mat-select helpers ───────────────────────────────────────────────

    def _select_mat_by_text(self, selector, text):
        self.page.locator(selector).first.click(force=True)
        self.page.wait_for_selector(".mat-mdc-select-panel", timeout=8000)
        options = self.page.locator(".mat-mdc-select-panel mat-option span.mdc-list-item__primary-text")
        for opt in options.all():
            if opt.inner_text().strip() == text:
                opt.click(force=True)
                break
        try:
            self.page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=3000)
        except Exception:
            pass
        self.page.wait_for_timeout(300)

    def _select_last_mat_option(self, selector):
        """Open mat-select and click the last option. Returns False if dropdown shows 'No results found'."""
        loc = self.page.locator(selector).first
        loc.wait_for(state="visible", timeout=10000)
        loc.click(force=True)
        self.page.wait_for_selector(".mat-mdc-select-panel", timeout=12000)

        if self.page.locator(".dd-empty-state").count() > 0:
            self.page.keyboard.press("Escape")
            try:
                self.page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=3000)
            except Exception:
                pass
            return False

        self.page.locator(".mat-mdc-select-panel mat-option").last.click(force=True)
        try:
            self.page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=3000)
        except Exception:
            pass
        self.page.wait_for_timeout(300)
        return True

    # ── Number helpers ───────────────────────────────────────────────────

    def _fill_number_nth(self, selector, row_index, value):
        self.page.evaluate("""
            ([xpath, idx, val]) => {
                const result = document.evaluate(xpath, document, null,
                    XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
                const el = result.snapshotItem(idx);
                if (!el) return;
                const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                    window.HTMLInputElement.prototype, 'value').set;
                nativeInputValueSetter.call(el, val);
                el.dispatchEvent(new Event('input', {bubbles: true}));
                el.dispatchEvent(new Event('change', {bubbles: true}));
                el.blur();
            }
        """, [selector.replace("xpath=", ""), row_index, str(value)])
        self.page.wait_for_timeout(400)

    def _read_readonly_nth(self, selector, row_index):
        xpath = selector.replace("xpath=", "")
        val = self.page.evaluate("""
            ([xpath, idx]) => {
                const result = document.evaluate(xpath, document, null,
                    XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
                const visible = [];
                for (let i = 0; i < result.snapshotLength; i++) {
                    const el = result.snapshotItem(i);
                    if (el.offsetParent !== null) visible.push(el);
                }
                const el = visible[idx];
                return el ? el.value : '';
            }
        """, [xpath, row_index])
        return val.strip() if val else ""

    # ── Open Add Form ────────────────────────────────────────────────────

    def open_add_form(self):
        self.page.wait_for_selector("table.mat-mdc-table, div.empty-state", timeout=15000)
        self.page.wait_for_timeout(500)
        add_btn = self.page.locator(self.ADD_BTN)
        add_btn.wait_for(state="visible", timeout=10000)
        add_btn.scroll_into_view_if_needed()
        add_btn.click(force=True)
        self.page.wait_for_timeout(2000)
        if self.page.locator(self.SUPPLIER_NAME).count() == 0:
            add_btn.click(force=True)
            self.page.wait_for_timeout(2000)
        self.page.wait_for_selector(self.SUPPLIER_NAME, timeout=25000)
        self.page.wait_for_timeout(500)

    # ── Fill form ────────────────────────────────────────────────────────

    def select_supplier_and_gp(self, supplier_name, expected_rows=1):
        """Select supplier + last GP and wait for rows to auto-patch.
        If rows don't appear after the wait, hard-refreshes, reopens the form, and retries once.
        Returns the number of patched rows.
        """
        def _attempt():
            self._select_mat_by_text(self.SUPPLIER_NAME, supplier_name)
            self.page.wait_for_timeout(5000)
            gp_selected = self._select_last_mat_option(self.GATE_PASS_NO)
            if not gp_selected:
                return 0
            self.page.wait_for_timeout(5000)
            return self.count_row_inputs()

        row_count = _attempt()
        if row_count < expected_rows:
            self._retry_on_empty_gp()
            row_count = _attempt()

        return row_count

    def _wait_for_gp_patch(self, timeout_ms=20000, poll_ms=500):
        """Poll until GP Quantity field has a non-empty value (rows auto-patched)."""
        elapsed = 0
        while elapsed < timeout_ms:
            val = self._read_readonly_nth(self.GP_QTY, 0)
            if val:
                return
            self.page.wait_for_timeout(poll_ms)
            elapsed += poll_ms
        raise RuntimeError("GRN: GP Quantity field did not populate within timeout — GP may not have auto-patched")

    def _retry_on_empty_gp(self):
        """Hard refresh + reopen form when GP dropdown showed 'No results found'."""
        self.page.reload()
        self.page.wait_for_selector("table.mat-mdc-table, div.empty-state", timeout=20000)
        self.open_add_form()

    def _select_random_supplier(self):
        """Select any supplier option (used to wake up the GP dropdown)."""
        self.page.locator(self.SUPPLIER_NAME).first.click(force=True)
        self.page.wait_for_selector(".mat-mdc-select-panel", timeout=8000)
        options = self.page.locator(".mat-mdc-select-panel mat-option").all()
        if options:
            import random as _random
            _random.choice(options).click(force=True)
        try:
            self.page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=3000)
        except Exception:
            pass
        self.page.wait_for_timeout(2000)

    def fill_form(self, supplier_name, accepted_qty, row_index=0):
        self._select_mat_by_text(self.SUPPLIER_NAME, supplier_name)
        self.page.wait_for_timeout(5000)
        gp_selected = self._select_last_mat_option(self.GATE_PASS_NO)
        if not gp_selected:
            # Wake up the dropdown by selecting a random supplier, then reselect ours
            self._select_random_supplier()
            self._select_mat_by_text(self.SUPPLIER_NAME, supplier_name)
            self.page.wait_for_timeout(5000)
            self._select_last_mat_option(self.GATE_PASS_NO)
        self._wait_for_gp_patch()
        self._fill_number_nth(self.ACCEPTED_QTY, row_index, accepted_qty)
        self.page.wait_for_timeout(600)

    def count_row_inputs(self):
        """Return how many Accepted Quantity inputs are currently rendered."""
        xpath = self.ACCEPTED_QTY.replace("xpath=", "")
        return self.page.evaluate("""
            (xpath) => {
                const result = document.evaluate(xpath, document, null,
                    XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
                return result.snapshotLength;
            }
        """, xpath)

    def read_gp_qty(self, row_index=0):
        val = self._read_readonly_nth(self.GP_QTY, row_index)
        return float(val) if val else None

    def read_rejected_qty(self, row_index=0):
        val = self._read_readonly_nth(self.REJECTED_QTY, row_index)
        return float(val) if val else None

    # ── Create ───────────────────────────────────────────────────────────

    def create_record(self, supplier_name, accepted_qty):
        self.open_add_form()
        self.fill_form(supplier_name, accepted_qty)
        self.page.locator(self.SUBMIT_BTN).click()
        self.handle_success_alert()
        self.navigate_to_page()
        return self.get_ref_no_of_first_row()

    # ── Table reads ──────────────────────────────────────────────────────

    def get_ref_no_of_first_row(self):
        return self.page.locator(self.REF_NO_COL).first.inner_text().strip()

    def is_grn_in_table(self, ref_no):
        return self.page.locator(self.REF_NO_COL).filter(has_text=ref_no).count() > 0

    def get_table_row_count(self):
        return self.page.locator("table.mat-mdc-table tbody tr").count()

    def search_by_ref_no(self, ref_no):
        self.search_entry(ref_no)

    # ── Close popup ──────────────────────────────────────────────────────

    def close_popup(self):
        try:
            cancel = self.page.locator(self.CANCEL_BTN)
            cancel.wait_for(state="visible", timeout=3000)
            cancel.click()
            self.page.wait_for_selector("table.mat-mdc-table, div.empty-state", timeout=10000)
        except Exception:
            try:
                self.page.locator("//mat-icon[text()='close']/ancestor::button").first.click()
            except Exception:
                pass
