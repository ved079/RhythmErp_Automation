import os
from pages.base_playwright_page import BasePlaywrightPage

BASE_URL = "https://rhythmerp.algorhythms.in"


class GRNPlaywrightPage(BasePlaywrightPage):
    URL = f"{BASE_URL}/#/purchase/grn"

    # Header fields
    SUPPLIER_NAME = "xpath=//mat-select[.//span[contains(@class,'mat-mdc-select-placeholder') and contains(.,'Select supplier name')]]"
    GATE_PASS_REF = "xpath=//mat-select[.//span[contains(@class,'mat-mdc-select-placeholder') and contains(.,'Select gate pass no.')]]"
    PO_REF        = "xpath=//mat-select[.//span[contains(@class,'mat-mdc-select-placeholder') and contains(.,'Select purchase order')]]"

    # Item grid — all readonly except Accepted Quantity
    GATE_PASS_QTY_INPUT = "xpath=//mat-form-field[.//mat-label[contains(.,'Gate Pass Quantity')]]//input"
    PO_QTY_INPUT        = "xpath=//mat-form-field[.//mat-label[contains(.,'PO Quantity')]]//input"
    RATE_INPUT          = "xpath=//mat-form-field[.//input[@placeholder='Rate']]//input"
    ACCEPTED_QTY_INPUT  = "xpath=//mat-form-field[.//input[@placeholder='Accepted Quantity']]//input"

    # Buttons
    ADD_BTN    = "button.erp-add-btn"
    SUBMIT_BTN = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Submit')]"
    CANCEL_BTN = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Cancel')]"

    # Table
    REF_NO_COL = "td.cdk-column-transaction_ref_no"

    def handle_success_alert(self):
        self.page.wait_for_selector(".swal2-container", timeout=8000)
        self.page.evaluate("document.querySelector('.swal2-confirm')?.click()")
        try:
            self.page.wait_for_selector(".swal2-container", state="hidden", timeout=10000)
        except Exception:
            pass
        try:
            self.page.wait_for_selector("table.mat-mdc-table", timeout=10000)
        except Exception:
            pass

    def navigate_to_page(self):
        for attempt in range(4):
            try:
                if attempt == 0:
                    self.page.goto(self.URL)
                else:
                    self.page.reload()
                self.page.wait_for_selector("table.mat-mdc-table, div.empty-state", timeout=20000)
                return
            except Exception:
                if attempt == 3:
                    raise

    def _select_mat_by_partial_text(self, selector, text):
        """Open mat-select, type in search box if present, then click the matching option."""
        self.page.locator(selector).first.click(force=True)
        self.page.wait_for_selector(".mat-mdc-select-panel", timeout=8000)

        # Many GRN dropdowns have an inline search box (dd-search-input)
        search_input = self.page.locator(".mat-mdc-select-panel input.dd-search-input")
        if search_input.count() > 0:
            search_input.fill(text)
            self.page.wait_for_timeout(1500)  # wait for options to filter

        options = self.page.locator(
            ".mat-mdc-select-panel mat-option span.mdc-list-item__primary-text"
        ).all()
        for opt in options:
            if text in opt.inner_text().strip():
                opt.click(force=True)
                break
        try:
            self.page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=3000)
        except Exception:
            pass

    def open_add_form(self):
        for attempt in range(4):
            try:
                self.page.wait_for_selector("table.mat-mdc-table, div.empty-state", timeout=15000)
                add_btn = self.page.locator(self.ADD_BTN)
                add_btn.wait_for(state="visible", timeout=10000)
                add_btn.scroll_into_view_if_needed()
                add_btn.click(force=True)
                self.page.wait_for_selector(self.SUPPLIER_NAME, timeout=25000)
                return
            except Exception:
                if attempt == 3:
                    raise
                self.navigate_to_page()

    def select_supplier(self, supplier_name):
        """Select supplier — must be done first so the Gate Pass dropdown gets populated."""
        self._select_mat_by_partial_text(self.SUPPLIER_NAME, supplier_name)

    def select_gate_pass(self, gp_ref_no):
        """Select a Gate Pass by its reference number and wait for rows to auto-populate."""
        self._select_mat_by_partial_text(self.GATE_PASS_REF, gp_ref_no)
        # ERP takes 5-7 seconds to populate item rows after GP selection
        self.page.wait_for_timeout(7000)

    def select_po(self, po_ref_no):
        """Select a PO by its reference number; rows auto-enrich with rate and PO qty."""
        self._select_mat_by_partial_text(self.PO_REF, po_ref_no)
        self.page.wait_for_timeout(7000)

    def _read_input_nth(self, selector, row_index):
        val = self.page.evaluate("""
            ([xpath, idx]) => {
                const result = document.evaluate(xpath, document, null,
                    XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
                const el = result.snapshotItem(idx);
                return el ? el.value : '';
            }
        """, [selector.replace("xpath=", ""), row_index])
        return float(val) if val and val.strip() else 0.0

    def count_grn_rows(self):
        """Count auto-filled item rows in the GRN form."""
        return self.page.locator(self.GATE_PASS_QTY_INPUT).count()

    def read_gate_pass_qty_nth(self, row_index=0):
        return self._read_input_nth(self.GATE_PASS_QTY_INPUT, row_index)

    def read_po_qty_nth(self, row_index=0):
        """Read remaining PO balance for this item at time of GRN creation."""
        return self._read_input_nth(self.PO_QTY_INPUT, row_index)

    def read_rate_nth(self, row_index=0):
        return self._read_input_nth(self.RATE_INPUT, row_index)

    def fill_accepted_qty_nth(self, row_index, qty):
        """Fill the Accepted Quantity field (the only editable field in GRN rows)."""
        self.page.evaluate("""
            ([xpath, idx, val]) => {
                const result = document.evaluate(xpath, document, null,
                    XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
                const el = result.snapshotItem(idx);
                if (!el) return;
                const setter = Object.getOwnPropertyDescriptor(
                    window.HTMLInputElement.prototype, 'value').set;
                setter.call(el, val);
                el.dispatchEvent(new Event('input', {bubbles: true}));
                el.dispatchEvent(new Event('change', {bubbles: true}));
                el.blur();
            }
        """, [self.ACCEPTED_QTY_INPUT.replace("xpath=", ""), row_index, str(qty)])
        self.page.wait_for_timeout(400)

    def submit(self):
        """Submit the GRN form, dismiss success alert, and return the new GRN ref number."""
        self.page.locator(self.SUBMIT_BTN).click()
        self.handle_success_alert()
        self.navigate_to_page()
        return self.page.locator(self.REF_NO_COL).first.inner_text().strip()

    def close_popup(self):
        try:
            self.page.locator(self.CANCEL_BTN).click()
            self.page.wait_for_selector("table.mat-mdc-table, div.empty-state", timeout=5000)
        except Exception:
            pass
