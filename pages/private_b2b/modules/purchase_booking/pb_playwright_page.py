import random
from pages.base_playwright_page import BasePlaywrightPage

BASE_URL = "https://rhythmerp.algorhythms.in"

# JS native setter — targets the nth mat-form-field whose mat-label exactly matches labelText,
# then fills its input. Used for all field-click-guard row inputs.
_JS_FILL_ROW_FIELD = """
    ([labelText, rowIdx, value]) => {
        const fields = [...document.querySelectorAll('mat-form-field')].filter(f =>
            f.querySelector('mat-label')?.textContent.trim() === labelText
        );
        const el = fields[rowIdx]?.querySelector('input');
        if (!el) return false;
        const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
        setter.call(el, String(value));
        el.dispatchEvent(new Event('input', {bubbles: true}));
        el.dispatchEvent(new Event('change', {bubbles: true}));
        return true;
    }
"""

# Fills the nth input matched by placeholder attribute.
_JS_FILL_BY_PLACEHOLDER = """
    ([placeholder, rowIdx, value]) => {
        const els = [...document.querySelectorAll(`input[placeholder="${placeholder}"]`)];
        const el = els[rowIdx];
        if (!el) return false;
        const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
        setter.call(el, String(value));
        el.dispatchEvent(new Event('input', {bubbles: true}));
        el.dispatchEvent(new Event('change', {bubbles: true}));
        return true;
    }
"""

# Row-level fields and their random value generators.
# Labels use capital 'Off' which differs from header-level 'off' labels — no index offset needed.
_ROW_FIELDS = [
    ("Empty Bag Weight (KG)",      lambda: round(random.uniform(0.5, 10), 1)),
    ("Rate",                        lambda: random.randint(100, 5000)),
    ("Labour Charges",              lambda: random.randint(1, 500)),
    ("Discount Percentage",         lambda: random.randint(1, 10)),
    ("Round Off Credit Amount(-)",  lambda: round(random.uniform(0, 1), 1)),
    ("Round Off Debit Amount(+)",   lambda: round(random.uniform(0, 1), 1)),
]

_GST_TYPES = ["IGST", "CGST + SGST"]


class PBPlaywrightPage(BasePlaywrightPage):
    URL = f"{BASE_URL}/#/purchase/purchase-booking"

    SUPPLIER_NAME   = "xpath=//mat-form-field[.//mat-label[contains(.,'Supplier Name')]]//mat-select"
    QC_SELECT       = "xpath=//mat-form-field[.//mat-label[contains(.,'QC')]]//mat-select"
    CONVERSION_RATE = "xpath=//mat-form-field[.//mat-label[contains(.,'Conversion Rate')]]//input"

    GST_TOGGLE_SLIDER = "app-slide-toggle-v2 div.slider"
    TAX_RATE_SELECT   = "xpath=//mat-select[.//span[contains(@class,'mat-mdc-select-placeholder') and contains(.,'Select tax rate')]]"
    GST_TYPE_SELECT   = "xpath=//mat-form-field[.//mat-label[text()='GST Type']]//mat-select"

    ADD_BTN    = "button.erp-add-btn"
    SUBMIT_BTN = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Submit')]"
    CANCEL_BTN = "xpath=//div[contains(@class,'popup-footer')]//button[contains(.,'Cancel')]"
    REF_NO_COL = "td.cdk-column-transaction_ref_no"

    def navigate_to_page(self):
        self.page.goto(self.URL)
        self.page.wait_for_selector("table.mat-mdc-table, div.empty-state", timeout=20000)

    def open_add_form(self):
        self.page.wait_for_selector("table.mat-mdc-table, div.empty-state", timeout=15000)
        btn = self.page.locator(self.ADD_BTN)
        btn.wait_for(state="visible", timeout=10000)
        btn.scroll_into_view_if_needed()
        btn.click(force=True)
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

    def select_supplier(self, supplier_name):
        self._select_mat_by_text(self.SUPPLIER_NAME, supplier_name)

    def select_qc(self, qc_ref_no):
        qc_locator = self.page.locator(self.QC_SELECT).first

        for attempt in range(3):
            # Open the panel
            qc_locator.click(force=True)
            try:
                self.page.wait_for_selector(".mat-mdc-select-panel", timeout=8000)
            except Exception:
                self.page.wait_for_timeout(500)
                continue

            # Type into search to narrow options — panel has placeholder "Search QC..."
            search = self.page.locator(".mat-mdc-select-panel input.dd-search-input")
            if search.count() > 0:
                search.fill(qc_ref_no)
                self.page.wait_for_timeout(1200)

            # Find and click the exact matching option (skip the "Select Options" clear entry)
            clicked = False
            for opt in self.page.locator(
                ".mat-mdc-select-panel mat-option:not(.dd-clear-option) span.mdc-list-item__primary-text"
            ).all():
                if opt.inner_text().strip() == qc_ref_no:
                    opt.click(force=True)
                    clicked = True
                    break

            if not clicked:
                self.page.keyboard.press("Escape")
                self.page.wait_for_timeout(600)
                continue

            try:
                self.page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=4000)
            except Exception:
                pass

            # Confirm the value landed in the QC select specifically (not the first select on page)
            panel_id = qc_locator.get_attribute("aria-controls") or ""
            selected_text = self.page.evaluate(
                """
                ([ref]) => {
                    // Walk up from mat-select to mat-form-field, then read the selected text
                    const selects = [...document.querySelectorAll('mat-select')];
                    for (const s of selects) {
                        const label = s.closest('mat-form-field')
                            ?.querySelector('mat-label')?.textContent.trim() ?? '';
                        if (label.toLowerCase().includes('qc')) {
                            return s.querySelector('.mat-mdc-select-min-line')?.textContent.trim() ?? '';
                        }
                    }
                    return '';
                }
                """,
                [qc_ref_no],
            )
            if qc_ref_no in selected_text:
                break

            self.page.wait_for_timeout(600)
        else:
            raise RuntimeError(f"Failed to select QC '{qc_ref_no}' after 3 attempts")

        # Wait for rows to auto-populate from QC selection
        self.page.wait_for_selector(
            "xpath=//mat-form-field[.//mat-label[text()='Labour Charges']]//input",
            timeout=15000,
        )
        self.page.wait_for_timeout(1000)

    def fill_conversion_rate(self, value=1):
        field = self.page.locator(self.CONVERSION_RATE).first
        field.click(force=True)
        field.fill(str(value))
        field.press("Tab")
        self.page.wait_for_timeout(300)

    def read_row_item_names(self):
        """Return list of item names from each PB row via the Item Name mat-select."""
        return self.page.evaluate("""
            () => {
                const itemFields = [...document.querySelectorAll('mat-form-field')]
                    .filter(f => f.querySelector('mat-label')?.textContent.trim() === 'Item Name');
                return itemFields.map(f =>
                    f.querySelector('.mat-mdc-select-min-line')?.textContent.trim() ?? ''
                );
            }
        """)

    def count_pb_rows(self):
        return self.page.locator(
            "xpath=//mat-form-field[.//mat-label[text()='Labour Charges']]//input"
        ).count()

    _GST_TYPES = ["IGST", "CGST + SGST"]

    def _fill_row_gst(self, row_index):
        """Toggle IS GST Off ON, pick a random tax rate, pick a random GST type."""
        sliders = self.page.locator(self.GST_TOGGLE_SLIDER)
        if sliders.count() == 0:
            return
        slider = sliders.nth(row_index)
        slider.scroll_into_view_if_needed()
        slider.click(force=True)
        self.page.wait_for_timeout(1200)

        # Tax rate
        tax_selects = self.page.locator(self.TAX_RATE_SELECT)
        if tax_selects.count() > 0:
            tax_selects.nth(row_index).click(force=True)
            self.page.wait_for_selector(".mat-mdc-select-panel", timeout=6000)
            opts = self.page.locator(
                ".mat-mdc-select-panel mat-option span.mdc-list-item__primary-text"
            ).all()
            if opts:
                import random as _r
                _r.choice(opts).click(force=True)
            try:
                self.page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=3000)
            except Exception:
                pass
            self.page.wait_for_timeout(500)

        # GST type
        gst_selects = self.page.locator(self.GST_TYPE_SELECT)
        if gst_selects.count() > 0:
            import random as _r
            chosen = _r.choice(self._GST_TYPES)
            gst_selects.nth(row_index).click(force=True)
            self.page.wait_for_selector(".mat-mdc-select-panel", timeout=6000)
            search = self.page.locator(".mat-mdc-select-panel input.dd-search-input")
            if search.count() > 0:
                search.fill(chosen)
                self.page.wait_for_timeout(600)
            for opt in self.page.locator(
                ".mat-mdc-select-panel mat-option span.mdc-list-item__primary-text"
            ).all():
                if opt.inner_text().strip() == chosen:
                    opt.click(force=True)
                    break
            try:
                self.page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=3000)
            except Exception:
                pass
            self.page.wait_for_timeout(400)

    def _fill_row_tax(self, row_idx):
        """Pick a random tax rate, then pick a random GST type (IGST or CGST+SGST)."""
        tax_selects = self.page.locator(self.TAX_RATE_SELECT)
        if tax_selects.count() > row_idx:
            tax_selects.nth(row_idx).click(force=True)
            self.page.wait_for_selector(".mat-mdc-select-panel", timeout=6000)
            opts = self.page.locator(
                ".mat-mdc-select-panel mat-option:not(.dd-clear-option) span.mdc-list-item__primary-text"
            ).all()
            if opts:
                random.choice(opts).click(force=True)
            try:
                self.page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=3000)
            except Exception:
                pass
            self.page.wait_for_timeout(500)

        gst_selects = self.page.locator(self.GST_TYPE_SELECT)
        if gst_selects.count() > row_idx:
            chosen = random.choice(_GST_TYPES)
            gst_selects.nth(row_idx).click(force=True)
            self.page.wait_for_selector(".mat-mdc-select-panel", timeout=6000)
            for opt in self.page.locator(
                ".mat-mdc-select-panel mat-option span.mdc-list-item__primary-text"
            ).all():
                if opt.inner_text().strip() == chosen:
                    opt.click(force=True)
                    break
            try:
                self.page.wait_for_selector(".mat-mdc-select-panel", state="hidden", timeout=3000)
            except Exception:
                pass
            self.page.wait_for_timeout(400)

    def fill_row(self, row_idx):
        for label, value_fn in _ROW_FIELDS:
            self.page.evaluate(_JS_FILL_ROW_FIELD, [label, row_idx, value_fn()])
            self.page.wait_for_timeout(150)
        # Transport charges uses placeholder= not mat-label
        self.page.evaluate(_JS_FILL_BY_PLACEHOLDER, ["Transport charges", row_idx, random.randint(1, 500)])
        self.page.wait_for_timeout(150)
        self._fill_row_tax(row_idx)

    def submit(self):
        self.page.locator(self.SUBMIT_BTN).click()
        try:
            self.page.wait_for_selector(".swal2-container", timeout=8000)
            title = self.page.locator("#swal2-title").inner_text().strip()
            if any(w in title for w in ("Validation", "Failed", "Error")):
                msg = self.page.locator("#swal2-html-container").inner_text().strip()
                self.page.evaluate("document.querySelector('.swal2-confirm')?.click()")
                raise RuntimeError(f"PB creation failed — {title}: {msg}")
            self.page.evaluate("document.querySelector('.swal2-confirm')?.click()")
            self.page.wait_for_selector(".swal2-container", state="hidden", timeout=10000)
        except RuntimeError:
            raise
        except Exception:
            pass
        self.navigate_to_page()
        return self.page.locator(self.REF_NO_COL).first.inner_text().strip()

    def create_for_integration(self, supplier_name, qc_ref_no):
        """Open PB form, select supplier + QC, fill all row fields randomly, submit."""
        self.open_add_form()
        self.select_supplier(supplier_name)
        self.select_qc(qc_ref_no)
        self.fill_conversion_rate(1)
        n_rows = self.count_pb_rows()
        for i in range(n_rows):
            self.fill_row(i)

        return self.submit()

    def _search_ref(self, ref_no):
        search = self.page.locator("#erpSearchInput")
        if search.count() > 0:
            search.fill(ref_no)
            self.page.locator("button[mattooltip='Search']").click()
            self.page.wait_for_timeout(2000)

    def _check_status_closed(self, ref_no):
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
