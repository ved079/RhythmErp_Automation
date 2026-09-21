import random
from pages.base_playwright_page import BasePlaywrightPage

BASE_URL = "https://rhythmerp.algorhythms.in"


class PBPage(BasePlaywrightPage):
    URL = f"{BASE_URL}/#/purchase/purchase-booking"

    SUPPLIER_NAME   = "xpath=//mat-label[contains(.,'Supplier Name')]/ancestor::mat-form-field//mat-select"
    QC_SELECT       = "xpath=//mat-form-field[.//mat-label[contains(.,'QC')]]//mat-select"
    GST_TYPE_SELECT = "xpath=//mat-form-field[.//mat-label[text()='GST Type']]//mat-select"
    GST_RATE_SELECT = "xpath=//mat-form-field[.//mat-label[contains(.,'GST Rate')]]//mat-select"
    GRN_FIELD       = "xpath=//mat-label[contains(.,'GRN')]/ancestor::mat-form-field//mat-select"

    SUBMIT_BTN  = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Submit')]"
    ADD_BTN     = "button.erp-add-btn"
    SEARCH_BTN  = "button[mattooltip='Search']"
    SEARCH_INPUT = "input#erpSearchInput"
    ROW_TRIGGER  = "button.erp-row-trigger"
    REF_NO_COL   = "td.cdk-column-transaction_ref_no"

    NET_PAYABLE       = "xpath=//mat-label[contains(.,'Net Payable Amount')]/ancestor::mat-form-field//input"
    NET_PURCHASE_RATE = "xpath=//mat-label[contains(.,'Net Purchase Rate')]/ancestor::mat-form-field//input"
    CANCEL_BTN        = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Cancel')]"

    def navigate_to_page(self):
        self.page.goto(self.URL)
        self.page.wait_for_selector("mat-form-field, table.mat-mdc-table, .page-content", timeout=20000)

    def open_add_form(self):
        self.page.locator(self.ADD_BTN).click()
        self.page.locator(self.SUPPLIER_NAME).wait_for(state="visible", timeout=15000)

    def select_supplier(self, name):
        self._select_mat_by_text(self.SUPPLIER_NAME, name)

    def select_qc(self, qc_ref_no):
        loc = self.page.locator(self.QC_SELECT).first
        loc.click(force=True)
        self.page.wait_for_selector(".mat-mdc-select-panel", timeout=8000)
        search = self.page.locator(".mat-mdc-select-panel input.dd-search-input")
        if search.count() > 0:
            search.fill(qc_ref_no)
            self.page.wait_for_timeout(800)
        for opt in self.page.locator(
            ".mat-mdc-select-panel mat-option span.mdc-list-item__primary-text"
        ).all():
            txt = opt.inner_text().strip()
            if qc_ref_no in txt or txt in qc_ref_no:
                opt.click(force=True)
                break
        try:
            self.page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=3000)
        except Exception:
            pass
        self.page.wait_for_timeout(500)

    def select_gst_type(self, value="IGST"):
        self._select_mat_by_text(self.GST_TYPE_SELECT, value)
        # GST Type selection triggers auto-patch of GRN, PO, GST Rate, etc.
        try:
            self.page.locator(self.GRN_FIELD).wait_for(state="visible", timeout=10000)
        except Exception:
            pass
        self.page.wait_for_timeout(800)

    def select_gst_rate_any(self):
        """Pick the first available GST Rate option."""
        try:
            self.page.locator(self.GST_RATE_SELECT).first.wait_for(state="visible", timeout=8000)
        except Exception:
            return None
        self.page.locator(self.GST_RATE_SELECT).first.click(force=True)
        self.page.wait_for_selector(".mat-mdc-select-panel", timeout=8000)
        opts = self.page.locator(
            ".mat-mdc-select-panel mat-option:not(.dd-clear-option) span.mdc-list-item__primary-text"
        ).all()
        if not opts:
            self.page.keyboard.press("Escape")
            return None
        choice = random.choice(opts)
        text = choice.inner_text().strip()
        choice.click(force=True)
        try:
            self.page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=3000)
        except Exception:
            pass
        return text

    def submit(self):
        self.page.locator(self.SUBMIT_BTN).click()
        # PB uses a tracking card (not swal2) — wait for it to appear then disappear
        try:
            self.page.wait_for_selector(".tracking-card", timeout=8000)
        except Exception:
            pass
        # Check for swal2 validation error before tracking card
        try:
            self.page.wait_for_selector(".swal2-container", timeout=2000)
            title = self.page.locator("#swal2-title").inner_text().strip()
            msg   = self.page.locator("#swal2-html-container").inner_text().strip()
            self.page.evaluate("document.querySelector('.swal2-confirm')?.click()")
            raise RuntimeError(f"PB submit failed — {title}: {msg}")
        except RuntimeError:
            raise
        except Exception:
            pass
        try:
            self.page.wait_for_selector(".tracking-card", state="hidden", timeout=60000)
        except Exception:
            pass
        self.navigate_to_page()

    def search(self, ref_no):
        if not self.page.locator(self.SEARCH_INPUT).is_visible():
            self.page.locator(self.SEARCH_BTN).click()
        self.page.locator(self.SEARCH_INPUT).fill(ref_no)
        self.page.locator(self.SEARCH_INPUT).press("Enter")
        self.page.wait_for_timeout(1000)

    def open_view(self, ref_no):
        self.page.locator(f"tr:has-text('{ref_no}')").first.locator(self.ROW_TRIGGER).click(force=True)
        self.page.wait_for_selector(".mat-mdc-menu-panel", timeout=8000)
        self.page.locator(".mat-mdc-menu-panel button.mat-mdc-menu-item:has(.erp-menu-title:text-is('View'))").click()
        self.page.wait_for_timeout(1000)

    def close_view(self):
        self.force_close_popup()

    def get_ref_no_of_first_row(self):
        self.page.wait_for_selector(self.REF_NO_COL, timeout=15000)
        return self.page.locator(self.REF_NO_COL).first.inner_text().strip()

    def get_net_payable_amount(self):
        return self.page.locator(self.NET_PAYABLE).first.input_value()

    def get_net_purchase_rate(self):
        return self.page.locator(self.NET_PURCHASE_RATE).first.input_value()

    def computed_fields_ready(self) -> bool:
        """Return True if Net Payable Amount and Net Purchase Rate are both non-empty."""
        try:
            payable = self.page.locator(self.NET_PAYABLE).first.input_value()
            rate    = self.page.locator(self.NET_PURCHASE_RATE).first.input_value()
            return bool(payable and payable.strip() and rate and rate.strip())
        except Exception:
            return False

    def cancel_form(self):
        """Cancel / close the add form without saving."""
        try:
            self.page.locator(self.CANCEL_BTN).click()
            self.page.wait_for_timeout(500)
        except Exception:
            self.force_close_popup()

    def _select_mat_by_text(self, selector, text):
        self.page.locator(selector).first.click(force=True)
        self.page.wait_for_selector(".mat-mdc-select-panel", timeout=8000)
        search = self.page.locator(".mat-mdc-select-panel input.dd-search-input")
        if search.count() > 0:
            search.fill(text)
            # Wait for options to filter before iterating
            self.page.wait_for_timeout(1000)
        opts_loc = self.page.locator(
            ".mat-mdc-select-panel mat-option:not(.dd-clear-option) span.mdc-list-item__primary-text"
        )
        opts_loc.first.wait_for(state="visible", timeout=5000)
        for opt in opts_loc.all():
            if opt.inner_text().strip() == text:
                opt.scroll_into_view_if_needed()
                opt.click(force=True)
                break
        try:
            self.page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=3000)
        except Exception:
            pass
