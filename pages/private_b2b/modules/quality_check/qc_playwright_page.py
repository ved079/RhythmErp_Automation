import random
from pages.base_playwright_page import BasePlaywrightPage

BASE_URL = "https://rhythmerp.algorhythms.in"

_JS_SET_VALUE = """
    ([placeholder, value]) => {
        const inputs = document.querySelectorAll(`input[placeholder="${placeholder}"]`);
        const el = inputs[inputs.length > 1 ? inputs.length - 1 : 0];
        if (!el) return;
        const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
        setter.call(el, value);
        el.dispatchEvent(new Event('input', {bubbles: true}));
        el.dispatchEvent(new Event('change', {bubbles: true}));
    }
"""

_JS_SET_VALUE_NTH = """
    ([placeholder, idx, value]) => {
        const inputs = document.querySelectorAll(`input[placeholder="${placeholder}"]`);
        const el = inputs[idx];
        if (!el) return;
        const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
        setter.call(el, value);
        el.dispatchEvent(new Event('input', {bubbles: true}));
        el.dispatchEvent(new Event('change', {bubbles: true}));
    }
"""


class QCPlaywrightPage(BasePlaywrightPage):
    URL = f"{BASE_URL}/#/purchase/qc"

    SUPPLIER_NAME = "xpath=//mat-form-field[.//mat-label[contains(.,'Supplier Name')]]//mat-select"
    ITEM_CATEGORY = "xpath=//mat-form-field[.//mat-label[contains(.,'Item category')]]//mat-select"
    GATE_PASS     = "xpath=//mat-form-field[.//mat-label[contains(.,'Gate Pass')]]//mat-select"

    CONVERSION_RATE  = "xpath=//mat-form-field[.//mat-label[contains(.,'Conversion Rate')]]//input"
    EMPTY_BAG_WEIGHT = "xpath=//mat-form-field[.//mat-label[contains(.,'Empty Bag Weight')]]//input"
    DISCOUNT_RATE    = "xpath=//mat-form-field[.//mat-label[contains(.,'Discount Rate')]]//input"
    ACCEPTED_QTY     = "xpath=//mat-form-field[.//mat-label[contains(.,'Accepted Quantity')]]//input"
    FINAL_RATE       = "xpath=//mat-form-field[.//mat-label[contains(.,'Final Rate')]]//input"

    # QC Parameter popup opener + Done
    QC_PARAM_BTN  = "button[data-sd-details-opener='qc_details[0].qc_parameter_details']"
    # Bags Parameter popup opener
    BAGS_PARAM_BTN = "button[data-sd-details-opener='qc_details[0].qc_bags_details']"

    # Shared Done button (inside whichever popup is open)
    POPUP_DONE_BTN = "xpath=//div[contains(@class,'popup-content')]//button[contains(@class,'btn-save')]"

    # Bags popup fields
    BAGS_TYPE_SELECT = "xpath=//div[contains(@class,'popup-content')]//mat-form-field[.//mat-label[contains(.,'Type of Bag')]]//mat-select"

    ADD_BTN    = "button.erp-add-btn"
    SUBMIT_BTN = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Submit')]"
    CANCEL_BTN = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Cancel')]"
    REF_NO_COL = "td.cdk-column-transaction_ref_no"

    def navigate_to_page(self):
        for attempt in range(3):
            try:
                if attempt == 0:
                    self.page.goto(self.URL)
                else:
                    self.page.reload()
                self.page.wait_for_selector("table.mat-mdc-table, div.empty-state", timeout=20000)
                return
            except Exception:
                if attempt == 2:
                    raise

    def open_add_form(self):
        self.page.wait_for_selector("table.mat-mdc-table, div.empty-state", timeout=15000)
        add_btn = self.page.locator(self.ADD_BTN)
        add_btn.wait_for(state="visible", timeout=10000)
        add_btn.scroll_into_view_if_needed()
        add_btn.click(force=True)
        self.page.wait_for_selector(self.SUPPLIER_NAME, timeout=25000)

    def _select_mat_by_text(self, selector, text):
        self.page.locator(selector).first.click(force=True)
        self.page.wait_for_selector(".mat-mdc-select-panel", timeout=8000)
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

    def _select_mat_by_partial_text(self, selector, text):
        self.page.locator(selector).first.click(force=True)
        self.page.wait_for_selector(".mat-mdc-select-panel", timeout=8000)
        search = self.page.locator(".mat-mdc-select-panel input.dd-search-input")
        if search.count() > 0:
            search.fill(text)
            self.page.wait_for_timeout(1200)
        for opt in self.page.locator(
            ".mat-mdc-select-panel mat-option span.mdc-list-item__primary-text"
        ).all():
            if text in opt.inner_text().strip():
                opt.click(force=True)
                break
        try:
            self.page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=3000)
        except Exception:
            pass

    def _fill_input(self, selector, value):
        """Fill a main-form input using Playwright fill + Tab."""
        field = self.page.locator(selector).first
        field.click(force=True)
        field.fill(str(value))
        field.press("Tab")
        self.page.wait_for_timeout(300)

    def _js_fill_by_placeholder(self, placeholder, value, nth=0):
        """Fill an input inside a field-click-guard via JS native setter."""
        self.page.evaluate(_JS_SET_VALUE_NTH, [placeholder, nth, str(value)])
        self.page.wait_for_timeout(200)

    def select_supplier(self, supplier_name):
        self._select_mat_by_text(self.SUPPLIER_NAME, supplier_name)

    def select_item_category(self, category="Raw Materia"):
        self._select_mat_by_partial_text(self.ITEM_CATEGORY, category)

    def select_gate_pass(self, gp_ref_no):
        self._select_mat_by_partial_text(self.GATE_PASS, gp_ref_no)
        self.page.wait_for_timeout(3000)

    def fill_conversion_rate(self, value=1):
        self._fill_input(self.CONVERSION_RATE, value)

    def fill_empty_bag_weight(self, value=1):
        self._fill_input(self.EMPTY_BAG_WEIGHT, value)

    def fill_discount_rate(self, value=1):
        self._fill_input(self.DISCOUNT_RATE, value)

    def fill_accepted_qty(self, value=1):
        self._fill_input(self.ACCEPTED_QTY, value)

    def fill_final_rate(self, value=1):
        self._fill_input(self.FINAL_RATE, value)

    def fill_quality_parameters(self, actual_value=1, row=0):
        """Open QC Parameter popup for row N, fill all Actual Value inputs via JS, click Done."""
        btn_sel = f"button[data-sd-details-opener='qc_details[{row}].qc_parameter_details']"
        section_sel = f"[data-sd-section-path='qc_details[{row}].qc_parameter_details']"
        self.page.locator(btn_sel).first.click(force=True)
        self.page.wait_for_selector(section_sel, timeout=10000)
        self.page.wait_for_timeout(500)

        count = self.page.locator("input[placeholder='Actual Value']").count()
        for i in range(count):
            self._js_fill_by_placeholder("Actual Value", actual_value, nth=i)

        self.page.locator(self.POPUP_DONE_BTN).click(force=True)
        self.page.wait_for_timeout(500)

    def fill_bags_parameter(self, no_of_bags=1, per_bag_weight=1, row=0):
        """Open Bags Parameter popup for row N, fill fields, click Done."""
        btn_sel = f"button[data-sd-details-opener='qc_details[{row}].qc_bags_details']"
        section_sel = f"[data-sd-section-path='qc_details[{row}].qc_bags_details']"
        self.page.locator(btn_sel).first.click(force=True)
        self.page.wait_for_selector(section_sel, timeout=10000)
        self.page.wait_for_timeout(500)

        self.page.locator(self.BAGS_TYPE_SELECT).first.click(force=True)
        self.page.wait_for_selector(".mat-mdc-select-panel", timeout=5000)
        self.page.locator(".mat-mdc-select-panel mat-option").first.click(force=True)
        try:
            self.page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=3000)
        except Exception:
            pass
        self.page.wait_for_timeout(300)

        self._js_fill_by_placeholder("No of  Bag", no_of_bags, nth=0)
        self._js_fill_by_placeholder("Per Bag Weight", per_bag_weight, nth=0)

        self.page.locator(self.POPUP_DONE_BTN).click(force=True)
        self.page.wait_for_timeout(500)

    def fill_accepted_qty_nth(self, n, value):
        """Fill the Nth accepted quantity field (for multi-item QC forms)."""
        fields = self.page.locator(self.ACCEPTED_QTY)
        el = fields.nth(n)
        el.click(force=True)
        el.fill(str(value))
        el.press("Tab")
        self.page.wait_for_timeout(300)

    def submit(self):
        self.page.locator(self.SUBMIT_BTN).click()
        try:
            self.page.wait_for_selector(".swal2-container", timeout=8000)
            title = self.page.locator("#swal2-title").inner_text().strip()
            if any(w in title for w in ("Validation", "Failed", "Error")):
                msg = self.page.locator("#swal2-html-container").inner_text().strip()
                self.page.evaluate("document.querySelector('.swal2-confirm')?.click()")
                raise RuntimeError(f"QC creation failed — {title}: {msg}")
            self.page.evaluate("document.querySelector('.swal2-confirm')?.click()")
            self.page.wait_for_selector(".swal2-container", state="hidden", timeout=10000)
        except RuntimeError:
            raise
        except Exception:
            pass
        self.navigate_to_page()
        return self.page.locator(self.REF_NO_COL).first.inner_text().strip()

    def _read_row_item_names(self):
        """Read item name from each QC row via the Item Name mat-select span."""
        return self.page.evaluate("""
            () => {
                const rows = document.querySelectorAll(
                    'mat-form-field mat-label'
                );
                const itemFields = [...document.querySelectorAll('mat-form-field')]
                    .filter(f => f.querySelector('mat-label')?.textContent.trim() === 'Item Name');
                return itemFields.map(f =>
                    f.querySelector('.mat-mdc-select-min-line')?.textContent.trim() ?? ''
                );
            }
        """)

    def create_for_integration(self, supplier_name, gp_ref_no, accepted_qty=1):
        """Full QC creation for the integration flow. Returns QC ref_no.

        accepted_qty: int for single-item GP, or dict {item_name: qty} / list[int] for multi-item.
        When a dict is passed, each row's accepted qty is looked up by item name so ERP row
        ordering doesn't matter.
        """
        final_rate = random.randint(100, 5000)
        self.open_add_form()
        self.select_supplier(supplier_name)
        self.select_item_category("Raw Materia")
        self.select_gate_pass(gp_ref_no)
        self.fill_conversion_rate(1)
        self.fill_empty_bag_weight(1)
        self.fill_discount_rate(1)
        self.fill_final_rate(final_rate)

        if isinstance(accepted_qty, dict):
            # Map by item name — safe against ERP row reordering
            row_names = self._read_row_item_names()
            qty_list  = [accepted_qty.get(name, 1) for name in row_names]
        else:
            qty_list = accepted_qty if isinstance(accepted_qty, (list, tuple)) else [accepted_qty]

        for i, qty in enumerate(qty_list):
            self.fill_accepted_qty_nth(i, qty)
            self.fill_quality_parameters(actual_value=1, row=i)
            self.fill_bags_parameter(no_of_bags=1, per_bag_weight=1, row=i)

        return self.submit()

    def is_closed(self, ref_no):
        self.navigate_to_page()
        search_btn = self.page.locator("button[mattooltip='Search']")
        search_input = self.page.locator("#erpSearchInput")
        if search_btn.count() > 0:
            search_btn.click()                   # toggle — reveals the input
            self.page.wait_for_timeout(400)
            search_input.fill(ref_no)
            search_btn.click()                   # submit the search
            self.page.wait_for_timeout(2000)
        for row in self.page.locator("tr.mat-mdc-row").all():
            ref_cell = row.locator("td.cdk-column-transaction_ref_no")
            if ref_cell.count() > 0 and ref_no in ref_cell.inner_text():
                status = row.locator("td.cdk-column-booking_status")
                return status.count() > 0 and "Closed" in status.inner_text()
        return False

    def close_popup(self):
        try:
            self.page.locator(self.CANCEL_BTN).click()
            self.page.wait_for_selector("table.mat-mdc-table, div.empty-state", timeout=5000)
        except Exception:
            pass
