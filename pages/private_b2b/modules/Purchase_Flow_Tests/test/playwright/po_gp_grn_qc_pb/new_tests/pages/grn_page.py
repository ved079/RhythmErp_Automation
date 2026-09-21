from pages.base_playwright_page import BasePlaywrightPage

BASE_URL = "https://rhythmerp.algorhythms.in"


class GRNPage(BasePlaywrightPage):
    URL = f"{BASE_URL}/#/purchase/grn"

    # ── Header selectors ────────────────────────────────────────────────
    SUPPLIER_NAME  = "xpath=//mat-label[contains(.,'Supplier Name')]/ancestor::mat-form-field//mat-select"
    GATE_PASS_NO   = "xpath=//mat-label[contains(.,'Gate Pass No.')]/ancestor::mat-form-field//mat-select"
    SUPPLIER_TYPE  = "xpath=//mat-label[contains(.,'Supplier Type')]/ancestor::mat-form-field//mat-select"
    PURCHASE_ORDER = "xpath=//mat-label[contains(.,'Purchase Order')]/ancestor::mat-form-field//mat-select"
    LOCATION       = "xpath=//mat-label[contains(.,'Location')]/ancestor::mat-form-field//mat-select"

    # ── Item row selectors (auto-populated after Gate Pass selection) ───
    ITEM_NAME       = "xpath=//mat-label[contains(.,'Item Name')]/ancestor::mat-form-field//mat-select"
    HSN_SAC_NO      = "xpath=//mat-label[contains(.,'HSN SAC No.')]/ancestor::mat-form-field//mat-select"
    UOM             = "xpath=//mat-label[contains(.,'UOM')]/ancestor::mat-form-field//mat-select"
    PO_QUANTITY     = "xpath=//mat-label[contains(.,'PO Quantity')]/ancestor::mat-form-field//input"
    GRN_QUANTITY    = "xpath=//mat-label[contains(.,'GRN Quantity')]/ancestor::mat-form-field//input"
    RATE            = "xpath=//mat-label[contains(.,'Rate')]/ancestor::mat-form-field//input"
    RECEIVED_QTY    = "xpath=//mat-label[contains(.,'Received Quantity')]/ancestor::mat-form-field//input"

    # ── Read-only / verify ───────────────────────────────────────────────
    GRN_REF_NO = "xpath=//mat-label[contains(.,'GRN Ref. No.')]/ancestor::mat-form-field//input"

    # ── Buttons ──────────────────────────────────────────────────────────
    ADD_BTN      = "button.erp-add-btn"
    SUBMIT_BTN   = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Submit')]"
    SEARCH_BTN   = "button[mattooltip='Search']"
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
        # Fallback: verify the field actually shows the selected name
        actual = self.page.locator(self.SUPPLIER_NAME).first.text_content().strip()
        if actual != name:
            raise RuntimeError(f"GRN supplier mismatch — expected '{name}', got '{actual}'")

    def select_gate_pass(self, gp_ref_no):
        self._select_mat_by_text(self.GATE_PASS_NO, gp_ref_no)
        # Gate pass selection auto-populates all fields — wait for Supplier Type
        self.page.locator(self.SUPPLIER_TYPE).wait_for(state="visible", timeout=10000)
        self.page.wait_for_timeout(800)

    # ── Item row actions ──────────────────────────────────────────────────

    def fill_received_quantity(self, value):
        self.page.locator(self.RECEIVED_QTY).first.fill(str(value))

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

    def get_grn_ref_no(self):
        return self.page.locator(self.GRN_REF_NO).input_value()

    def get_gate_pass_no(self):
        return self.page.locator(self.GATE_PASS_NO).text_content().strip()

    def get_purchase_order(self):
        return self.page.locator(self.PURCHASE_ORDER).text_content().strip()

    def get_received_quantity(self):
        return self.page.locator(self.RECEIVED_QTY).first.input_value()

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
            raise RuntimeError(f"GRN submit failed — {title}: {message}")

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
