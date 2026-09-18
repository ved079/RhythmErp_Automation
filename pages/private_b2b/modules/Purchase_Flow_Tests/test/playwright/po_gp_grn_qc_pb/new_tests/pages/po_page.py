from datetime import date
from pages.base_playwright_page import BasePlaywrightPage

BASE_URL = "https://rhythmerp.algorhythms.in"


class POPage(BasePlaywrightPage):
    URL = f"{BASE_URL}/#/purchase/purchase-order"

    # ── Header selectors ────────────────────────────────────────────────
    SUPPLIER_NAME   = "xpath=//mat-label[contains(.,'Supplier Name')]/ancestor::mat-form-field//mat-select"
    ITEM_CATEGORY   = "xpath=//mat-label[contains(.,'Item Category')]/ancestor::mat-form-field//mat-select"
    LOCATION        = "xpath=//mat-label[contains(.,'Location')]/ancestor::mat-form-field//mat-select"
    DEPARTMENT      = "xpath=//mat-label[contains(.,'Department')]/ancestor::mat-form-field//mat-select"
    DIVISION        = "xpath=//mat-label[contains(.,'Division')]/ancestor::mat-form-field//mat-select"
    TYPE_OF_SALE    = "xpath=//mat-label[contains(.,'Type of Sale')]/ancestor::mat-form-field//mat-select"
    DELIVERY_TERMS  = "xpath=//mat-label[contains(.,'Delivery Terms')]/ancestor::mat-form-field//mat-select"

    # ── Item row selectors ───────────────────────────────────────────────
    ITEM_NAME  = "xpath=//mat-label[contains(.,'Item Name')]/ancestor::mat-form-field//mat-select"
    HSN_SAC_NO = "xpath=//mat-label[contains(.,'HSN SAC No.')]/ancestor::mat-form-field//mat-select"
    UOM        = "xpath=//mat-label[contains(.,'UOM')]/ancestor::mat-form-field//mat-select"
    QUANTITY   = "xpath=//mat-label[contains(.,'Quantity')]/ancestor::mat-form-field//input"
    RATE       = "xpath=//mat-label[contains(.,'Rate')]/ancestor::mat-form-field//input"
    GST_TYPE   = "xpath=//mat-label[contains(.,'GST Type')]/ancestor::mat-form-field//mat-select"
    TAX_RATE   = "xpath=//mat-label[contains(.,'Tax Rate')]/ancestor::mat-form-field//mat-select"

    # ── Read-only / verify ───────────────────────────────────────────────
    TOTAL_PO_AMOUNT       = "xpath=//mat-label[contains(.,'Total PO Amount')]/ancestor::mat-form-field//input"
    TRANSACTION_CURRENCY  = "xpath=//mat-label[contains(.,'Transaction Currency')]/ancestor::mat-form-field//mat-select"
    SUPPLIER_REF_TYPE     = "xpath=//mat-label[contains(.,'Supplier Ref. Type')]/ancestor::mat-form-field//mat-select"

    # ── Date fields ──────────────────────────────────────────────────────
    EXPECTED_DELIVERY_DATE = "xpath=//mat-label[contains(.,'Expected Delivery Date')]/ancestor::mat-form-field//input[@matinput]"

    # ── Buttons ──────────────────────────────────────────────────────────
    ADD_BTN    = "button.erp-add-btn"
    SAVE_BTN   = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Save')]"
    SUBMIT_BTN = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Submit')]"
    SEARCH_BTN = "button[mattooltip='Search']"
    SEARCH_INPUT = "input#erpSearchInput"
    ROW_TRIGGER  = "button.erp-row-trigger"

    # ── Table ────────────────────────────────────────────────────────────
    REF_NO_COL = "td.cdk-column-transaction_ref_no"

    # ── Navigation ───────────────────────────────────────────────────────

    def navigate_to_page(self):
        self.page.goto(self.URL)
        self.page.wait_for_selector("mat-form-field, table.mat-mdc-table, .page-content", timeout=20000)

    def open_add_form(self):
        self.page.locator(self.ADD_BTN).click()
        self.page.wait_for_selector(self.SUPPLIER_NAME, timeout=15000)

    # ── Header actions ────────────────────────────────────────────────────

    def select_supplier(self, name):
        self._select_mat_by_text(self.SUPPLIER_NAME, name)

    def select_item_category(self, value):
        self._select_mat_by_text(self.ITEM_CATEGORY, value)
        self.page.locator(self.SUPPLIER_REF_TYPE).wait_for(state="visible", timeout=10000)

    def select_location(self, value):
        self._select_mat_by_text(self.LOCATION, value)
        self.page.locator(self.DEPARTMENT).wait_for(state="visible", timeout=10000)

    def select_department(self, value):
        self._select_mat_by_text(self.DEPARTMENT, value)
        self.page.locator(self.DIVISION).wait_for(state="visible", timeout=10000)

    def select_division(self, value):
        self._select_mat_by_text(self.DIVISION, value)
        self.page.locator(self.TYPE_OF_SALE).wait_for(state="visible", timeout=10000)

    def select_type_of_sale(self, value):
        self._select_mat_by_text(self.TYPE_OF_SALE, value)
        self.page.locator(self.DELIVERY_TERMS).wait_for(state="visible", timeout=10000)

    def select_delivery_terms(self, value):
        self._select_mat_by_text(self.DELIVERY_TERMS, value)

    def fill_expected_delivery_date(self):
        today = date.today().strftime("%d/%m/%Y")
        loc = self.page.locator(self.EXPECTED_DELIVERY_DATE)
        loc.click()
        loc.fill(today)
        self.page.keyboard.press("Tab")

    # ── Item row actions ──────────────────────────────────────────────────

    def select_item_name(self, value):
        self.page.locator(self.ITEM_NAME).wait_for(state="visible", timeout=10000)
        self._select_mat_by_text(self.ITEM_NAME, value)
        self.page.locator(self.HSN_SAC_NO).wait_for(state="visible", timeout=10000)

    def fill_quantity(self, value):
        self.page.locator(self.QUANTITY).first.fill(str(value))

    def fill_rate(self, value):
        self.page.locator(self.RATE).first.fill(str(value))

    def select_gst_type(self, value):
        self._select_mat_by_text(self.GST_TYPE, value)

    def select_tax_rate(self, value):
        self._select_mat_by_text(self.TAX_RATE, str(value))

    def select_random_tax_rate(self):
        """Open Tax Rate dropdown, pick a random available option, return the selected text."""
        import random
        self.page.locator(self.TAX_RATE).first.click(force=True)
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

    # ── Submit & search ───────────────────────────────────────────────────

    def submit(self):
        self.page.locator(self.SUBMIT_BTN).click()
        self.handle_success_alert()
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

    # ── Read values ───────────────────────────────────────────────────────

    def get_ref_no_of_first_row(self):
        self.page.wait_for_selector(self.REF_NO_COL, timeout=15000)
        return self.page.locator(self.REF_NO_COL).first.inner_text().strip()

    def get_transaction_amount(self):
        return self.page.locator("xpath=//mat-label[contains(.,'Transaction Amount')]/ancestor::mat-form-field//input").input_value()

    def get_total_amount(self):
        return self.page.locator("xpath=//mat-label[contains(.,'Total Amount')]/ancestor::mat-form-field//input").input_value()

    def get_total_po_amount(self):
        return self.page.locator(self.TOTAL_PO_AMOUNT).input_value()

    def get_supplier_name(self):
        return self.page.locator(self.SUPPLIER_NAME).text_content().strip()

    def get_item_name(self):
        return self.page.locator(self.ITEM_NAME).text_content().strip()

    def get_transaction_currency(self):
        return self.page.locator(self.TRANSACTION_CURRENCY).text_content().strip()

    def handle_success_alert(self):
        self.page.wait_for_selector(".swal2-container", timeout=8000)
        title = self.page.locator("#swal2-title").inner_text().strip()
        message = self.page.locator("#swal2-html-container").inner_text().strip()
        self.page.evaluate("document.querySelector('.swal2-confirm')?.click()")
        try:
            self.page.wait_for_selector(".swal2-container", state="hidden", timeout=15000)
        except Exception:
            pass
        if any(k in title for k in ("Validation", "Failed", "Error")):
            raise RuntimeError(f"PO submit failed — {title}: {message}")

    def _select_mat_by_text(self, selector, text):
        self.page.locator(selector).first.click(force=True)
        self.page.wait_for_selector(".mat-mdc-select-panel", timeout=8000)
        search = self.page.locator(".mat-mdc-select-panel input.dd-search-input")
        if search.count() > 0:
            search.fill(text)
            self.page.wait_for_timeout(800)
        for opt in self.page.locator(
            ".mat-mdc-select-panel mat-option span.mdc-list-item__primary-text"
        ).all():
            if opt.inner_text().strip() == text:
                opt.click(force=True)
                break
        try:
            self.page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=3000)
        except Exception:
            pass
